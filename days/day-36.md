---
title: "Day 36: how LLM inference actually works"
parent: "Week 6: AI systems"
nav_order: 1
has_children: true
---

# Day 36
## How an LLM actually serves a request, and why it is memory-bound not compute-bound 🤖

Today's one idea: an LLM answers in two very different phases. It reads your whole prompt in one fast parallel pass (prefill), then writes the answer one token at a time (decode), and each of those output tokens is a full trip through the entire model. That asymmetry is the whole economics of serving an LLM. Output is far more expensive than input, your latency is a straight line in the length of the answer, and the bottleneck is not the GPU's maths, it is how fast it can read the model's weights out of memory. Get this one fact and the rest of the week falls into place.

Welcome to week 6. Here is the reassuring part: serving a model is not a new discipline, it is distributed systems with a very hungry component in the middle. The batching you met in week 1, the tail latency from Day 4, the caching from week 3, they all point straight at the GPU now. We start with the component itself, because everything else this week is architecture wrapped around the behaviour you measure today.

---

## Before you start ⏪

You do not need any code from a previous day. You need one mental shift: a GPU is a machine with two separate speeds, how fast it can do arithmetic and how fast it can read from its memory, and those two speeds are wildly different. All of today is about which of the two you are waiting on.

One idea from earlier weeks does the heavy lifting. Batching (Day 2, and again in Day 6) was the trick of amortising a fixed cost across many items. Today you will see that an LLM's fixed cost is reading 14 GB of weights, and batching is how you make that one read pay for many tokens at once. If that clicks, Day 37 is already half done.

The lab is a cost model in pure Python. No GPU, no API, no downloads. You give the toy machine a memory bandwidth and a compute rate, give the toy model a size, and the latencies fall out of arithmetic you can check by hand.

---

## Words you will meet today 📖

A token is the unit an LLM reads and writes, roughly three quarters of a word. You are billed per token, and both the prompt (input tokens) and the answer (output tokens) are counted, usually at different prices.

Prefill is the first phase: the model reads the entire prompt in one parallel pass and produces the first output token. All the prompt tokens go through together, so prefill is cheap per token. Its duration is the time-to-first-token.

Decode is the second phase: the model generates the rest of the answer one token at a time. Each new token needs a full pass over the model, and it depends on every token before it, so decode is strictly sequential.

Time-to-first-token (TTFT) is how long you wait before the first word appears. It is dominated by prefilling the prompt, so a longer prompt means a longer wait, but only once.

Time-per-output-token (TPOT) is how long each decode step takes after the first token. Total latency is TTFT plus TPOT times the number of output tokens, a straight line in the length of the answer.

Memory-bound versus compute-bound is the question of which speed you are waiting on. A step is memory-bound if the time to read its data from memory is longer than the time to do its arithmetic. Decode is memory-bound. Prefill, on a long enough prompt, is compute-bound.

Arithmetic intensity is how many FLOPs of maths you do for each byte you read from memory. It is the single number that tells you which side of that line you are on.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these:
- [LLM Inference Performance Engineering: Best Practices](https://www.databricks.com/blog/llm-inference-performance-engineering-best-practices) by the Databricks and Mosaic team. The spine for today. It names the prefill and decode phases, defines TTFT and TPOT exactly as the lab does, and says plainly that generation is bounded by memory bandwidth. If you read one thing, read this.
- [Transformer Inference Arithmetic](https://kipp.ly/transformer-inference-arithmetic/) by kipply. This is where today's numbers come from. It walks the actual bytes and FLOPs of a forward pass and shows why decoding sits on the memory-bandwidth side of the roofline. A little mathy, worth it.
- [Making Deep Learning Go Brrrr From First Principles](https://horace.io/brrr_intro.html) by Horace He. The clearest explanation anywhere of compute-bound versus memory-bound versus overhead-bound. Read it for Part 2, and the whole memory wall will feel obvious.

Optional, and it is tomorrow's paper:
- [Efficient Memory Management for LLM Serving with PagedAttention](https://arxiv.org/abs/2309.06180), the vLLM paper. Skim the abstract and the intro today to see the problem batching is about to solve. We go deep on Day 37.

Watch, after the lab:
- [LLM Inference Explained: Prefill, Decode, KV Cache](https://www.youtube.com/watch?v=6QgLJLmNJGg) by Micro Learning, about 9 minutes. A clean visual pass over the two phases and why the first token lags.
- [Why LLM Inference Is Memory-Bound, Not Compute-Bound](https://www.youtube.com/watch?v=ADVRuiJSxWw) by Liquid AI, about 5 minutes. Short and sharp, and it is exactly Part 2 of today.

### Two phases, and why the first token is the slow one (16 min)

Picture asking a model a question. From the outside it feels like one thing: you send text, you get text back. Inside, it is two jobs with completely different shapes, and the difference is the most useful thing you will learn this week.

The first job is prefill. The model takes your entire prompt and pushes all of it through in one pass. Every prompt token is processed at the same time, in parallel, because they are all already known. Think of a teacher collecting a whole class's answer sheets in one go, rather than one at a time. At the end of this pass the model emits the first token of its answer. The time this takes is the time-to-first-token, and it grows with how long your prompt is, because there is more to read. But it is a one-off cost. You pay it once, up front, no matter how long the answer turns out to be.

The second job is decode, and this is where the surprise lives. To produce the second token, the model has to run again, over the whole model, using the first token it just made. To produce the third, it runs again over the whole model using the first two. Each new token is a fresh, full pass, and it cannot start until the previous token exists, because the next word depends on the words so far. There is no parallelising this. It is a person writing a sentence word by word, where each word depends on the one before. The time for one such step is the time-per-output-token.

So the total time to answer is the first-token wait plus one per-token cost for every token in the answer. Written out, total latency is TTFT plus M times TPOT, where M is the number of output tokens. That is a straight line in the length of the answer, and the lab draws it for you by sweeping the output length and fitting the line. The slope it recovers is TPOT, the intercept is TTFT.

Here is the consequence that reframes everything. Put 500 tokens in the prompt and it is one prefill pass. Ask for 500 tokens of output and it is 500 separate decode passes. Same token count, wildly different cost. On the lab's toy machine, 500 input tokens take about 23 ms and 500 output tokens take about 3,500 ms, which is 150 times longer. Input tokens carpool through one pass. Output tokens each need their own car.

### Why decode is waiting on memory, not maths (16 min)

Now the deeper why, the fact that the whole week leans on. When the model runs once to produce a single token, what is it actually doing, and what is it waiting on?

To run the model once, the GPU has to read every one of the model's weights out of its memory. For a 7 billion parameter model stored in fp16, that is 7 billion numbers at 2 bytes each, so 14 GB, read for every single token. The arithmetic it does with those weights, for one token, is about 14 billion FLOPs. That sounds like a lot until you compare it to what the GPU can do. A data-centre GPU does hundreds of trillions of FLOPs per second but reads memory at only a couple of terabytes per second. Those two numbers are not close.

Divide them and you get the balance point, the arithmetic intensity at which a GPU switches from waiting on memory to waiting on maths. On the lab's machine it is 300 TFLOP/s divided by 2 TB/s, which is 150 FLOPs per byte. To keep the compute units busy, you need to do 150 FLOPs for every byte you read. A decode step does 14 billion FLOPs for 14 billion bytes, which is 1 FLOP per byte. One, against a needed 150. The maths finishes almost instantly and then the GPU sits there, 99 percent idle, waiting for the weights to finish streaming in. That is what memory-bound means, and it is why decode is slow.

Sit with how strange this is. The expensive supercomputer part of the GPU, the thing you are paying for, is doing nothing for most of every token. The bottleneck is a pipe, not a brain. And a faster brain does not widen a pipe. This is why the whole field chases memory tricks (quantisation to shrink the bytes, the KV cache to avoid recomputing, paged attention to pack memory) rather than just buying more FLOPs.

So how do you ever use that idle compute? Batching, the same amortisation idea from Day 2. The 14 GB read is a fixed cost. If you have many requests in flight at once, you can run them together: read the weights once, and apply them to a token from every request in the batch. One read, many tokens. The arithmetic intensity climbs with the batch size, 1 FLOP per byte at batch 1, 16 at batch 16, and at batch 150 you finally hit the balance point and the compute units are full. In the lab, going from batch 1 to batch 150 keeps the step time essentially flat while throughput multiplies by 150. The read was going to happen anyway, so every extra request in the batch is nearly free until the maths saturates. That is the entire reason an LLM server batches, and it is Day 37.

### What this does to your latency and your bill (10 min)

Step back to the product. You are a PM or an engineer shipping an AI feature, and someone asks what it will cost and how fast it will be. Today's two facts answer both.

Latency first. Because total time is TTFT plus M times TPOT, and TPOT dominates for any real answer, latency tracks the length of the output almost one for one. A reply of 500 tokens takes roughly ten times as long as a reply of 50 tokens from the same prompt, because the fixed prefill is tiny next to the decode. If your chatbot feels slow, the usual culprit is not the model being dumb, it is the answer being long. The cheapest latency win available to you is to ask for a shorter answer: a tighter system prompt, a lower max-tokens, a format that does not ramble.

Cost next. You pay per token, and output tokens are almost always priced higher than input tokens, often three times as much, precisely because they are the sequential, memory-bound, expensive-to-produce part. So output hits you twice: there is more of it per second of latency, and each one costs more. In the lab, the same 200-token prompt answered with 50 tokens versus 500 tokens is about 10 times the latency and about 5 times the cost. Scale that to a hundred thousand replies a day and it is the difference between a few hundred dollars a month and a few thousand, for the identical prompt and model.

The habit to build: when you estimate an AI feature, estimate the output tokens first, because that is the number that moves both the clock and the invoice. Input length matters far less than it feels like it should. This is the maths almost nobody on a product team can do, and after today you can.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. Use the lab's toy machine throughout: a 7B model in fp16 (14 GB of weights per pass, about 14 GFLOPs per token), a GPU with 2 TB/s of memory bandwidth and 300 TFLOP/s of compute. Then copy your answers into [`notes/day-36-drills.md`](../notes/day-36-drills.md). About 8 minutes each.

D1. Prefill and TTFT. Prefilling a 1,000-token prompt is one parallel pass: the FLOPs are 1,000 tokens' worth, the bytes read are the 14 GB of weights once. Work out the compute time and the memory time, say which wins, and give the TTFT.

D2. Decode and total latency. A decode step is memory-bound at about 7 ms (TPOT), and the TTFT from D1 is the start-up cost. Give the total latency for a 300-token reply, and what fraction of it is decode.

D3. The memory wall. A batch-1 decode step reads 14 GB and does 14 GFLOPs. Compute its arithmetic intensity in FLOP/byte and the machine's balance point. Is the step memory-bound or compute-bound, and by what factor do the compute units sit idle?

D4. Batching. One 14 GB weight read can serve a whole batch at once. Roughly what batch size makes the step compute-bound, and what is the throughput in tokens per second at batch 1 versus batch 64? Why does batching lift throughput but not the latency of a single lonely request?

D5. The token bill. Same 1,000-token prompt, two replies: 100 output tokens and 1,000 output tokens, with TPOT 7 ms and the TTFT from D1. Give the latency ratio. If output tokens are priced at 3x input tokens, give the cost ratio. In one line, why do you trim the output before anything else?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-36-inference/inference.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-36-inference/inference.py).

It is a cost model in three parts, pure standard library, and it runs in a fraction of a second. Part 1 measures TTFT and TPOT, sweeps the output length, and fits the straight line that is total latency. Part 2 computes the arithmetic intensity of a decode step, shows it is memory-bound, and sweeps the batch size to show throughput climbing while step time stays flat. Part 3 turns it into latency and dollars: a short reply versus a long one from the same prompt.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything.

- P1. TPOT, the time for one decode step (one output token), in milliseconds. A step reads all 14 GB of weights at 2 TB/s.
- P2. One output token versus one prompt token. How many times more wall time does generating one output token cost than feeding in one prompt token?
- P3. The arithmetic intensity of a batch-1 decode step, in FLOPs per byte.
- P4. Same 200-token prompt, a 50-token reply versus a 500-token reply. How many times longer does the 500-token one take?

P2 is the one to feel in your gut first. Most people guess 2 or 3. Write a number down before you see it.

### Fill in the TODOs

1. TODO 1 is the roofline: a step's time is the max of its memory time and its compute time. This one line is the whole physics of the day.
2. TODO 2 is prefill as one parallel pass: the FLOPs for all the prompt tokens together.
3. TODO 3 is total latency: the first-token wait plus one TPOT per output token, the straight line.
4. TODO 4 is arithmetic intensity: FLOPs done per byte moved, the number that says memory-bound.

```bash
cd labs/day-36-inference
python3 inference.py
```

### What you're going to discover

Part 1 is the asymmetry. The same 500 tokens cost about 23 ms as a prompt and about 3,500 ms as an answer, 150 times more, purely because input is one shared pass and output is 500 separate ones. The fitted line confirms total latency is TTFT plus M times TPOT, a slope of 7 ms per output token sitting on a 23 ms intercept.

Part 2 is the why. A decode step does 1 FLOP for every byte it reads, against a machine that wants 150, so the compute units are idle 99 percent of the time and the weights are the bottleneck. Then batching: one 14 GB read feeds the whole batch, so from batch 1 to batch 150 the step time barely moves but throughput goes up 150 times. That flat step time next to the climbing throughput is the setup for tomorrow.

Part 3 is the bill. The same prompt answered in 500 tokens instead of 50 is about 10 times the latency and 5 times the cost, which at a hundred thousand replies a day is hundreds of dollars a month versus thousands. Output is where the time and the money both live.

### Traps ⚠️

- The lab is deterministic. Your numbers should match the reference almost to the digit, because it is arithmetic, not a benchmark. If they do not, a constant drifted, not your machine.
- Do not confuse the two speeds. Compute time is FLOPs divided by the compute rate, memory time is bytes divided by the bandwidth, and the step takes the larger of the two. Mixing them up is the one way to get Part 2 wrong.
- Batching raises throughput, not single-request latency. One user's answer still comes out one token at a time at the same TPOT. Batching helps the server serve more users at once, it does not make any one reply appear faster. Keep those two apart.
- The pricing in Part 3 is illustrative, made up to show the shape. The real ratios shift by provider, but output being pricier than input is near universal.

### Deliverable

[`labs/day-36-inference/RESULTS.md`](../labs/day-36-inference/RESULTS.md) has a skeleton. Paste the output, and write one line: one output token cost how many prompt tokens, and why is decode waiting on memory rather than maths?

---

## Block 4: write (30 min) 📣

Your angle today is the reframe: "I built a cost model of how an LLM serves one request, and learned that output tokens are about 150 times more expensive than input tokens, because the GPU reads the entire model from memory to produce each one. The bottleneck is bandwidth, not brains." The scoreboard, output 150x input and a decode step 99 percent idle on compute, is the screenshot.

Example posts are on the [Day 36 posts](../shares/day-36-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the number you measured for one output token versus one input token, and one thing you still cannot explain.

Day 37 is the payoff: the KV cache and continuous batching, the vLLM insight. Today you saw that decode is memory-bound and that batching is the way out. Tomorrow you see the two tricks that make batching actually work in production, and why a paper about virtual memory ended up running every LLM server on earth.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Prefill 1,000 tokens is one pass. Compute time is 1,000 times 14 GFLOPs divided by 300 TFLOP/s, which is 1.4e13 / 3e14 = 46.7 ms. Memory time is 14 GB divided by 2 TB/s = 7 ms. Compute is the larger, so prefill here is compute-bound, and the TTFT is about 46.7 ms. Note the shape: a long prompt pushes prefill into compute-bound territory because the maths scales with the number of prompt tokens while the weight read does not.

D2. Total latency is TTFT plus M times TPOT = 46.7 + 300 times 7 = 46.7 + 2,100 = 2,146.7 ms, about 2.1 seconds. Decode is 2,100 of that, so about 97.8 percent. The first-token wait is real but tiny next to the per-token stream once the answer is a few hundred tokens long.

D3. Arithmetic intensity is 14 GFLOPs divided by 14 GB = 1 FLOP per byte. The machine balance is 300 TFLOP/s divided by 2 TB/s = 150 FLOP per byte. Since 1 is far below 150, the step is memory-bound. The compute units are busy 1/150 of the time, so they sit idle about 99.3 percent of every decode step. The step waits on the 7 ms weight read, not the 0.05 ms of maths, a factor of 150.

D4. The step turns compute-bound when the batch pushes arithmetic intensity up to the balance point, so at a batch of about 150 (150 FLOP/byte). Throughput at batch 1 is one token per 7 ms step, about 143 tokens per second. At batch 64 the one read still takes about 7 ms but produces 64 tokens, so about 9,143 tokens per second, 64 times more. Batching does not help a single request's latency because that request's own tokens are still produced one at a time, each waiting the full TPOT. Batching shares the weight read across different requests running together, so it raises total tokens per second across everyone, not the speed of any one stream.

D5. With TTFT 46.7 ms and TPOT 7 ms: 100 tokens is 46.7 + 700 = 746.7 ms, 1,000 tokens is 46.7 + 7,000 = 7,046.7 ms, a ratio of about 9.4x, close to the 10x ratio of the outputs because decode dominates. Cost in token-equivalents with output at 3x input: 100-token reply is 1,000 + 3 times 100 = 1,300 units, 1,000-token reply is 1,000 + 3 times 1,000 = 4,000 units, a ratio of about 3.1x. You trim the output first because it is both the slow part (each token a full memory-bound pass) and the pricey part (priced higher and there is more of it), while the input rides one shared pass.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-36-inference/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-36-inference/solution.py).

TODO 1, the roofline, the whole physics of the day in one line. A step must both move its bytes and do its maths, and finishes no sooner than the slower of the two:

```python
return max(bytes_moved / MEM_BANDWIDTH, flops / COMPUTE)
```

TODO 2, prefill as one parallel pass. All the prompt tokens go through together, so the FLOPs are the token count times the per-token cost:

```python
return n_prompt * FLOPS_PER_TOKEN
```

TODO 3, total latency, the straight line. A flat first-token wait, then one TPOT per output token:

```python
return ttft_s + n_output * tpot_s
```

TODO 4, arithmetic intensity, the number that says memory-bound. FLOPs done per byte moved:

```python
return flops / bytes_moved
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Deterministic cost model, Python 3, 7B fp16 model on a 2 TB/s, 300 TFLOP/s toy GPU. Your run should match this closely, because it is arithmetic.

```
==============================================================================
Part 1: prefill vs decode. One parallel pass, then a token at a time
==============================================================================
  model: 7B params, fp16, so 14 GB of weights to read per pass
  gpu:   2 TB/s memory bandwidth, 300 TFLOP/s compute

  TTFT (prefill a 500-token prompt, one pass):   23.33 ms
  TPOT (one decode step, one output token):           7.00 ms

  Serving the same 500-token prompt with growing output:
     output tokens   total latency
                 1         30.2 ms
                25        200.3 ms
                50        371.8 ms
               100        724.3 ms
               200       1424.8 ms
               400       2827.8 ms
               800       5621.7 ms

  Fit total = intercept + slope * (output tokens):
    measured TPOT (slope)     =  6.999 ms per output token
    measured TTFT (intercept) =  24.31 ms
  A straight line. Total latency is TTFT + M * TPOT, linear in OUTPUT
  tokens. The prompt sets a one-off start cost; every output token
  after that adds a fixed TPOT, because the model runs once per token.

  Now the punchline. 500 tokens as INPUT vs 500 tokens as OUTPUT:
    500 prompt tokens  (prefill, one pass) :    23.33 ms
    500 output tokens  (decode, 500 passes):  3500.00 ms
    output is 150x slower, for the SAME number of tokens
  Input tokens share one pass. Output tokens each need their own. That
  asymmetry is the whole economics of serving an LLM.

==============================================================================
Part 2: memory-bound, not compute-bound. Why batching is the whole game
==============================================================================
  A single decode step, batch of 1:
    reads 14 GB of weights, does 14 GFLOPs of math
    time if memory-bound  =   7.000 ms   (bytes / bandwidth)
    time if compute-bound =   0.047 ms   (flops / compute)
    memory loses by 150x, so the step waits on MEMORY.

    arithmetic intensity = 1.0 FLOP/byte  (math done per byte read)
    machine balance      = 150 FLOP/byte  (compute / bandwidth)
    1 is far below 150, so the math units are idle 99.3% of the time.
  The GPU reads 14 GB to do the arithmetic of ONE token. That is the
  memory wall: the weights, not the maths, set the clock.

  So reuse the read. Batch B requests, and one 14 GB read feeds all B
  tokens. Intensity becomes B FLOP/byte, and throughput climbs until
  the step finally turns compute-bound (at B = machine balance).

     batch   intensity    step time      throughput    bound by
         1         1       7.000 ms         143 tok/s      memory
         8         8       7.000 ms       1,143 tok/s      memory
        16        16       7.000 ms       2,286 tok/s      memory
        64        64       7.000 ms       9,143 tok/s      memory
       150       150       7.000 ms      21,429 tok/s      memory
       300       300      14.000 ms      21,429 tok/s     compute

  From batch 1 to batch 150 the step time barely moves, but throughput
  goes up 150x, because the one expensive read now pays for 150 tokens.
  Past 150 the math units are full, so throughput plateaus and latency
  starts to climb. THIS is why an LLM server batches: Day 37.

==============================================================================
Part 3: your token bill. Output is the part that costs
==============================================================================
  Same 200-token prompt, two replies. TTFT is a flat 9.3 ms,
  then every output token adds 7.0 ms.

           reply       latency          cost
       50 tokens      361.5 ms     $0.000175
      500 tokens     3514.9 ms     $0.000850

  10x the output tokens -> 9.7x the latency and 4.9x the cost.
  Latency scales almost 1:1 with output because decode dwarfs the fixed
  prefill. Cost scales with output because output tokens are priced
  higher AND there are more of them. A chatbot that streams 500 tokens
  is a different animal from one that returns 50, on both the clock and
  the invoice. Trim the output before you trim anything else.

  At 100,000 replies a day: the 50-token answer costs $525 a
  month, the 500-token answer $2,550. Same prompt, same model.

==============================================================================
Scoreboard
==============================================================================
  P1 TPOT per output token           you =     7.0   actual =     7.00 ms       close enough
  P2 output vs input token           you =   150.0   actual =   150.00 x       close enough
  P3 decode arithmetic intensity     you =     1.0   actual =     1.00 FLOP/byte       close enough
  P4 500-token vs 50-token reply     you =    10.0   actual =     9.72 x       close enough

==============================================================================
The number to carry
==============================================================================
  One decode step reads all 14 GB of weights to make a single
  token: 7 ms, set by memory bandwidth, not by the 300 TFLOP/s of
  compute that sits 150x idle. So an output token costs about
  150x a prompt token, total latency is TTFT + M * TPOT (a line in
  M), and the same 150 is the batch size you need to put the compute
  to work. Memory-bound decode is the one fact that explains prefill vs
  decode, your latency, your bill, and why Day 37 is all about batching.
```

Part 1 is the day. Five hundred tokens cost about 23 ms as a prompt and about 3,500 ms as an answer, 150 times more, for the identical token count. The fitted line confirms the law underneath it: total latency is a flat TTFT plus a fixed TPOT for every output token. Nothing about the tokens changed, only whether they rode through one shared pass (input) or needed a pass each (output).

Part 2 is why. A decode step does 1 FLOP for each byte of weights it reads, against a machine that needs 150 to stay busy, so the compute units are idle 99 percent of every token and the bottleneck is the 14 GB read, not the maths. Batching is the escape: one read feeds the whole batch, so throughput climbs 150-fold from batch 1 to batch 150 while the step time holds flat. That is the hinge the whole of Day 37 turns on.

Part 3 is the bill. The same prompt answered in 500 tokens rather than 50 is about 10 times the latency and 5 times the cost, which at scale is the gap between a few hundred and a few thousand dollars a month. Output is the expensive, sequential, memory-bound part, so output is the number you manage first.

The one line to carry out of today: an LLM reads its entire self from memory to produce each single output token, so decode is memory-bound, output costs far more than input, and batching (Day 37) is how you win the memory back.

</details>
