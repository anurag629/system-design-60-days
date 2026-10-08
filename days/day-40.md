---
title: "Day 40: agents, and why the token bill explodes"
parent: "Week 6: AI systems"
nav_order: 5
has_children: true
---

# Day 40
## Agents, and why the token bill explodes 🤖💸

Today's one idea: an agent is just a loop. Think, call a tool, read the result, repeat until done. Simple. The expensive part is hidden one level down: the model keeps no memory between calls, so on every single step the whole conversation so far gets re-sent. The context grows each step, the cost of each step grows with it, and the total is a sum over a growing thing, which climbs roughly with the square of the number of steps. One user request quietly becomes twenty model calls, and each one is bigger than the last. Once you see that shape, the whole cost model of agents makes sense, and so does every trick people use to tame it.

This is week 6, the AI week, and today is the one where the bill arrives. Yesterday RAG was retrieval plus a cache. Today the request fans out into many calls, so the token cost and the tail latency you met in weeks 1 and 4 come back together.

---

## Before you start ⏪

You want three earlier days fresh. Day 1, because latency is round trips, and an agent is many round trips back to back. Day 4, because the slow-call tail is about to get many chances to fire. Day 2 and Day 6, batching and amortising, because the reason prefill is cheap per token is that you pay it once on a big prompt, and an agent pays it again and again on a prompt that keeps growing. You do not need Day 36's inference internals for the lab, but if you have them, the quadratic will feel even more physical: every re-sent token is prefill you pay for twice, three times, twenty times.

The lab is pure Python, standard library only. No model, no API, no network. We are not calling an LLM today, we are modelling the accounting that sits around one, because that accounting is the part you can actually design.

---

## Words you will meet today 📖

An agent is a loop around a model: the model picks a tool, the tool runs, the result goes back to the model, and it picks again, until it decides it is done. The model drives; your code just runs the tools and carries the messages.

A tool is a function the model is allowed to call, described to it in the prompt (its name, what it does, its arguments). Every tool you offer costs tokens on every call, because the whole list of tool descriptions rides along in the context.

The context, or context window, is everything sent to the model on one call: the system prompt, the tool descriptions, the user's task, and the full back-and-forth so far. The model is stateless between calls, so this bundle is rebuilt and re-sent every step.

Prefill is the model reading that whole input before it writes anything. It scales with the size of the context, so a long context is slow and costly to prefill, and an agent re-prefills a growing context on every step.

Context management is the set of tricks for keeping that bundle small: trim old steps, summarise them, keep only the last few verbatim, drop tool outputs you no longer need. It is the single biggest lever on an agent's cost.

Prompt caching is the provider caching the stable front of your context (system prompt, tool schemas) so re-sending it is heavily discounted. It lowers the price of the re-sent prefix; it does not change the fact that you re-send.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) by Anthropic. The clearest statement of what an agent actually is: a model in a loop with tools, and the honest advice that you should reach for the simplest thing that works and add autonomy only when it earns its keep. Read it for the loop and for the workflows-versus-agents distinction.
- [Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) by Anthropic. This is today's Part 2, written up properly: what to keep in the context, what to throw away, and why the context is a budget you spend, not a bucket you fill.
- [Prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) in the Anthropic docs. Read the constraints, because the constraints are the design: the cached part has to be a stable prefix, which tells you exactly how to lay out an agent's prompt.

If you want the origin of the loop, skim [ReAct: synergizing reasoning and acting](https://arxiv.org/abs/2210.03629). It is the paper that framed "reason, act, observe" as one loop, and every agent framework is a descendant.

Watch, after the lab:
- [How We Build Effective Agents](https://www.youtube.com/watch?v=D7_ipDqhtwk) by Barry Zhang of Anthropic, about 15 minutes. A grounded talk on when to build an agent at all, and why simpler and tighter usually wins. It lands better once you have felt the cost in the lab.

### The loop, and the one fact that makes it expensive (16 min)

Strip away the mystique and an agent is embarrassingly simple. You send the model a task and a list of tools. It replies, "call search with this query." Your code runs search, gets a result, and sends it back. The model replies, "now call read_file on this path." You run it, send the result back. Round and round until the model says, "here is the answer, I am done." That is the whole thing. ReAct named it reason-act-observe, and LangChain, the OpenAI and Anthropic SDKs, and every framework since are variations on that loop.

Here is the fact that turns this tidy loop into a budget problem: the model has no memory between calls. None. Each call is a fresh start. So for the model to know what happened on steps 1 through 7 when it is deciding step 8, your harness has to send all of it again: the system prompt, the tool descriptions, the original task, and every single prior step's reply and tool result. The provider's API is stateless, and the "conversation" is an illusion your code maintains by re-sending the transcript every time.

Think of a clerk at a government office who refuses to remember anything between questions. Every time you ask one more thing, he re-reads the entire file from page one before he answers, and he charges you by the page he reads. Your first question, thin file, cheap. Your tenth question, the file now holds all nine previous questions and his nine previous answers, and he reads the whole fat thing again to answer the tenth. That is an agent. The clerk is the model, the file is the context, and the per-page charge is the token price.

This is also why an agent is really a distributed-systems problem wearing a prompt. One user request has fanned out into many model calls. We saw fan-out hurt latency in week 1. Here it hurts cost too, and in a particularly nasty shape.

### Why the bill is quadratic, not linear (14 min)

Let me make the shape concrete, because this is the part people get wrong when they estimate a feature's cost.

Say the fixed overhead (system prompt plus tool schemas plus the task) is about 1,700 tokens, and each step adds about 1,600 tokens to the context (the model's own reply plus the tool result it triggered). Now count the input tokens the model reads across a 10-step task:

- Step 1 reads 1,700.
- Step 2 reads 1,700 + 1,600.
- Step 3 reads 1,700 + 3,200.
- ...
- Step 10 reads 1,700 + 14,400.

Each step is fine on its own. The problem is the sum. You are adding up a quantity that grows by a fixed chunk every step, and the sum of 1, 2, 3, up to K is K times (K+1) over 2, which is a K-squared shape. Double the number of steps and you roughly quadruple the total cost, not double it. In the lab you will measure a 10-step task, then a 20-step version of the same task, and watch the cost go up about 3x, not 2x. The reason it is 3x and not a clean 4x is the fixed overhead, which adds a linear term that softens the curve a little. The dominant term is still the square.

The cleanest way to feel it: the cost-per-step rises as the task gets longer. The twentieth step is far more expensive than the first, because the twentieth step re-reads nineteen steps of history. A naive estimate ("one call is 2,000 tokens, twenty calls is 40,000 tokens") can be off by 8x or more. In the lab, the real 20-step run processes about 344,000 tokens against a naive budget of 43,000. That gap is the single most common way AI feature costs blow past their estimate.

### The fix: manage the context, and cache the prefix (12 min)

If the cost comes from re-sending a growing context, the fix is to stop the context from growing. That is context management, and it is the most important cost lever you have.

The simplest version, and the one you build today, is a sliding window with a summary. Keep the last few steps verbatim, because the recent steps hold most of what the model needs to pick the next action. Collapse everything older into one short summary, a few hundred tokens, and send that instead of the full history. Now the input per step stops growing once you are past the window: it is the fixed overhead, plus the summary, plus the last few steps, and that is a constant. A constant per step summed over K steps is linear in K, not quadratic. In the lab, trimming the 20-step task cuts the tokens by about half, and the saving gets bigger the longer the task runs, because you are bending a quadratic curve back down to a line.

Trimming is not free, and I want you to respect the trade. A summary can quietly drop a specific detail the agent needed later: an ID, a path, a constraint it was told once. Then the agent re-fetches it, or repeats a step, or loops. You manage that by keeping the recent window generous, pinning the handful of facts that must survive, and summarising carefully rather than crudely truncating. But the alternative, letting the context grow without bound, is both ruinously expensive and bad for quality, because the model's attention gets diluted as the window fills. Trimming usually wins.

The other lever is prompt caching, which you read about today. The front of an agent's context, the system prompt and the tool schemas, is identical on every call. Caching lets the provider skip re-processing that stable prefix and bills it at a steep discount. This is cache-aside from week 3, applied to the prompt itself: the key is the prefix, the value is its processed form, and you get a hit every step because the prefix does not change. Notice what caching does and does not do. It lowers the price of the bytes you re-send. It does not stop you re-sending them, so the quadratic shape is still there, just with a smaller constant in front. Context management attacks the shape; caching attacks the constant. You want both, and context management first.

### Fan-out, round trips, and the tail come back (8 min)

The last thing to see is that cost is not the only thing that scaled with steps. Latency did too, and in the way week 1 warned you about.

One user request is now twenty sequential model calls. You cannot start step 2 until step 1's tool result is back, so the calls run back to back, and the user's wait is the sum of twenty round trips. In the lab that is a request that takes ten to seventeen seconds of wall clock where a single call was a third of a second. And because the context grows, each round trip is a little slower to prefill than the one before, so the latency curve bends upward too.

Then the tail (Day 4) walks back in. Suppose any single call hits a slow path 5% of the time, a queue wait, a provider hiccup, a retry. Over one call, you shrug, 5%. Over twenty sequential calls, the chance that at least one of them is slow is 1 minus (every call being fast), which is 1 minus 0.95 to the twentieth, about 64%. So nearly two out of three runs of this agent hit at least one slow step, and because the steps are sequential, that one slow step stalls the entire request. You have taken a 5% per-call problem and turned it into a 64% per-request problem, purely by having many steps.

Put the three together and the design advice writes itself. More steps means more cost (quadratically), more latency (K round trips, each one bigger), and more chances to go wrong (the tail fires somewhere). A tight loop with good tools and few steps beats a sprawling one that wanders for twenty. The best token is the one you never send, and the best step is the one you never take.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. Write your answers into [`notes/day-40-drills.md`](../notes/day-40-drills.md). About 8 minutes each.

D1. The loop costs a sum, not a single call. An agent runs 12 steps. The model keeps no memory between calls, so each call re-sends everything so far. Each step adds about 1,600 tokens of context (the model's turn plus the tool result), on top of 1,700 fixed tokens of system prompt and tools. Roughly how many input tokens does step 12 send, and roughly how many input tokens does the whole 12-step run process? Why is the total much more than 12 times the first call?

D2. Quadratic, in your own words. If every step adds a fixed chunk to the context, the input to step i grows linearly in i, so the total over K steps grows as K squared over 2. A 10-step task costs X. Without doing the full sum, estimate what a 30-step version of the same task costs relative to X, and say why tripling the steps hurts so much more than it looks.

D3. The context lever. You cap the context: keep the last 4 steps verbatim and replace everything older with one 300-token summary. For a long task, what shape does the total cost curve become, linear or quadratic, and why? Name one thing a summary can quietly drop that then makes the agent repeat work or loop, and say why trimming is still usually worth it.

D4. Fan-out and the tail, back from weeks 1 and 4. One user request becomes 20 sequential model calls. A single call has a p99 of 3 seconds and a p50 of 0.3 seconds, and each call independently hits the slow path 5% of the time. What is the chance that at least one of the 20 steps is slow, and what does that do to the p99 of the whole request compared to a single call? Which earlier day is this exactly?

D5. Design judgement. A teammate's agent takes 25 steps and re-sends the full history every time, and the token bill is eating the feature's margin. Give three concrete levers to cut the bill, in the order you would reach for them, and say what each one trades. At least one must be about the number of steps, and one about what rides in the context on every call.

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-40-agents/agent_loop.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-40-agents/agent_loop.py).

It is a pure cost simulation, standard library only. No model, no API, no network. We generate a deterministic task of K steps (each step's token sizes come from a seeded RNG) and then run the accounting two ways. Part 1 runs the loop naively, re-sending the whole context every step, and measures how the total tokens and dollars grow as the task gets longer. Part 2 caps the context (keep the last few steps, summarise the rest) and measures the saving. Part 3 turns one request into K sequential calls and measures the wall-clock latency and the chance the tail fires at least once.

The full working version is `solution.py` in the same folder, if you get stuck.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything.

- P1. A naive agent, going from a 10-step task to a 20-step task. By what factor does the total token cost grow? Linear would say 2x. What does "re-send everything" say?
- P2. The naive 20-step run. Its total tokens, as a multiple of "20 times the first call" (what you would budget if every call stayed the size of the first one). How many times bigger?
- P3. Context trimming (keep the last 4 steps, summarise the rest) on the same 20-step task. What percent of the naive total tokens does it save?
- P4. Each model call independently hits a slow tail 5% of the time. Over a 20-step run, what is the chance at least one step is slow?

P1 is the one to feel in your gut first. Most people say 2x, because they are thinking "twice the steps." Write a number down before you run it.

### Fill in the TODOs

1. TODO 1 is the naive input: the whole conversation re-sent every step. This one line is the entire reason agents are expensive.
2. TODO 2 is the trimmed input: keep the last few steps, add one fixed summary for the rest. This one line turns the quadratic into a line.
3. TODO 3 is the billing: input tokens and output tokens charged at their different rates.
4. TODO 4 is the tail over a loop: the chance at least one of K calls is slow, which is 1 minus the chance every call is fast.

```bash
cd labs/day-40-agents
python3 agent_loop.py
```

### What you're going to discover

Part 1 is the shock. The same task, costed honestly. A single call is about 2,000 tokens, so twenty calls "should" be about 40,000. The real run processes about 344,000, roughly 8x the naive budget, because every step after the first re-reads all the steps before it. Then you double the steps from 10 to 20 and the cost goes up about 3x, not 2x. The cost-per-step is rising, which is the fingerprint of a quadratic.

Part 2 is the relief. Keep the last 4 steps and summarise the rest, and the 20-step task drops from about 344,000 tokens to about 159,000, a bit over half off. Better still, run the naive-versus-trimmed comparison across task lengths and watch the ratio widen: the longer the task, the more trimming saves, because you are bending a quadratic back to a line. This is the lever to reach for first.

Part 3 is the sting in the tail. One request is twenty sequential calls, so the wall clock is ten to seventeen seconds where a single call was a third of a second, and trimming helps here too because a smaller context prefills faster. Then the tail: a 5% per-call slow chance, over twenty calls, hits at least once in about 64% of runs. You will see the measured number land right on the analytic 1 minus 0.95 to the twentieth.

### Traps ⚠️

- Do not mistake the output tokens for the problem. Output (the model's own replies) is a small, roughly fixed cost per step. The explosion is all in the re-sent input. That is also why trimming saves fewer dollars than tokens: output is untouched and billed at the higher rate.
- The quadratic is about the re-sent context, not the per-step size. If you made each step tiny, the shape would be the same, just scaled down. The fix is fewer steps or a capped context, not smaller steps.
- Trimming is lossy. In this lab the summary is a fixed token count with no content, so it never "forgets" anything that matters. In real life a summary drops detail, and that can make an agent loop or repeat work. The lab shows you the cost win; respect that the quality cost is real and lives off-screen here.
- Prompt caching is not in the lab on purpose. It changes the price of the re-sent prefix, not the fact that you re-send. Context management changes the shape, which is the bigger win, so that is what we measure.

### Deliverable

[`labs/day-40-agents/RESULTS.md`](../labs/day-40-agents/RESULTS.md) has a skeleton. Paste the output, and write two lines: how many times more tokens the naive 20-step run processed than you would have budgeted, and how much trimming saved, in your own words.

---

## Block 4: write (30 min) 📣

Your angle today is the measured surprise: "I simulated an AI agent's token cost, no model, just the accounting. A 20-step run processed 8x the tokens I would have budgeted, and doubling the steps cost 3x, not 2x, because the model re-sends the whole conversation every step. Capping the context cut it in half." The scoreboard is the screenshot: 344,000 tokens, 3x on double steps, 54% saved by trimming, 64% of runs hitting the tail.

Example posts are on the [Day 40 posts](../shares/day-40-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the naive-versus-trimmed token numbers you measured, and one thing you still cannot explain.

Day 41 is the serving layer around all of this: semantic caching so repeated questions do not re-run the model, token-based rate limiting so one user cannot burn your whole budget, and a fallback for when your primary model is slow or down. Today you felt where the cost comes from. Tomorrow you put the guards in front of it.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. Step 12 re-sends the fixed overhead plus the 11 steps before it: 1,700 + 11 times 1,600 = 1,700 + 17,600 = about 19,300 input tokens on that one step. The whole run is the sum over all 12 steps: 12 times 1,700 for the overhead, plus 1,600 times (0 + 1 + ... + 11) = 1,600 times 66 = 105,600 for the accumulating history, so about 126,000 input tokens, plus a small amount of output. Twelve times the first call (about 2,150 tokens) would be only about 25,800. The total is roughly 5x that, because every step after the first re-reads all the accumulated history, and that re-reading, not the 12 calls themselves, is where the tokens go.

D2. The quadratic term scales with the square of the step count, so going from 10 steps to 30 steps scales the dominant term by (30/10) squared, which is 9x. The fixed overhead adds a linear term that softens it a little, so in practice a 30-step version costs somewhere around 7x to 9x the 10-step one, not 3x. Tripling the steps hurts far more than 3x because the cost is a triangular sum: each new step adds a call that re-sends all the steps before it, and the last steps of a long task are the most expensive calls in the whole run.

D3. With a cap, the input per step stops growing once the history passes the kept window: it becomes the fixed overhead, plus the summary, plus the last 4 steps, which is a constant. A constant per step summed over K steps is linear in K, so the total cost curve becomes a straight line instead of a parabola. The thing a summary can quietly drop is a specific detail the agent needs later: an ID, a file path, a constraint it was told once, an earlier decision. Lose that and the agent re-fetches it, repeats a step, or loops. Trimming is still usually worth it because unbounded growth is both ruinously expensive (quadratic) and bad for quality (attention dilutes as the window fills); you manage the risk by keeping the recent window generous and pinning the few facts that must survive.

D4. The chance at least one of 20 calls is slow is 1 minus the chance all 20 are fast, which is 1 minus 0.95 to the twentieth, about 1 minus 0.358, so roughly 64%. That means the whole request is slow far more often than any single call is: a 5% per-call tail becomes a 64% per-request tail. Because the steps are sequential, one slow call stalls the entire request, so the request's p99 is dominated by the tail and sits several seconds above a single call's p99 (it is the sum of 20 calls with at least one, usually more, landing on the 3-second path). This is exactly Day 4: tail latency amplified by fan-out, where touching many components makes the slow case of the whole far worse than the slow case of a part.

D5. In order:
First, cut the number of steps, because cost is quadratic in steps so this is the biggest lever. Give the agent better tools so it needs fewer round trips, add clear stopping conditions, and do not let it wander. The trade is some flexibility and autonomy for a large cut in cost, latency, and failure odds.
Second, manage the context on every call: trim and summarise old steps, keep only the last few verbatim, and stop sending tool schemas or documents the current step does not need. The trade is a small risk of dropping a needed detail in the summary, in exchange for turning the quadratic into a line.
Third, turn on prompt caching for the stable prefix (system prompt and tool schemas) so re-sending it is cheap. The trade is living with the cache's constraints (a stable prefix, a short time to live) for a steep discount on the re-sent front of the context. A fourth, if steps are independent, is to run them in parallel, which cuts latency but not total cost.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-40-agents/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-40-agents/solution.py).

TODO 1, the naive input, the whole conversation re-sent every step. This one line is the reason agents are expensive:

```python
return system + user + sum(a + o for (a, o) in history)
```

TODO 2, the trimmed input, keep the last few steps and add one fixed summary for the rest. This one line turns the quadratic into a line:

```python
recent = history[-keep:]
summary = summary_tokens if len(history) > keep else 0
return system + user + summary + sum(a + o for (a, o) in recent)
```

TODO 3, the billing, input and output at their different rates:

```python
return input_tokens * price_in + output_tokens * price_out
```

TODO 4, the tail over a loop, the chance at least one of K calls is slow:

```python
return 1 - (1 - p_slow) ** steps
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3. Deterministic, seed 40, so your numbers should match these.

```
==============================================================================
Part 1: the loop re-sends everything, so cost grows ~ quadratically
==============================================================================
  A 20-step task. The model keeps no memory between calls, so
  every call re-sends the whole conversation so far as input.
  Fixed overhead re-sent each call: 1,700 tokens (system + tools + task).

  Watch the INPUT to each call climb as the context piles up:
     step   input tokens    this call $     running $
        1          1,700        0.0120$       0.0120$
        2          3,247        0.0187$       0.0306$
        3          4,799        0.0209$       0.0515$
        5          8,094        0.0313$       0.1099$
       10         15,807        0.0520$       0.3283$
       15         24,233        0.0776$       0.6692$
       20         32,079        0.1026$       1.1369$

  the first call was 2,157 tokens. If every call stayed
  that small, 20 calls would be 43,140 tokens.
  the run ACTUALLY processed 343,824 tokens, 8.0x that budget,
  and cost $1.1369 for ONE user request.

  Now double the steps and watch the cost more than double:
     steps    total tokens      cost $    cost / steps
         5          26,336     0.1047$        0.02094$
        10         101,973     0.3632$        0.03632$
        15         203,964     0.6899$        0.04600$
        20         343,824     1.1369$        0.05684$

  10 steps cost $0.3632, 20 steps cost $1.1369: a 3.13x jump
  for only 2x the steps. Cost-per-step RISES as you add steps, which is
  the signature of a quadratic. The context you re-send is the tax.

==============================================================================
Part 2: cap the context, and the quadratic collapses to a line
==============================================================================
  Same 20-step task. Keep the last 4 steps verbatim, collapse the
  rest into one 300-token summary. The input per step stops growing.

    approach           input tok   output tok    total tok     cost $
    naive                335,042        8,782      343,824    1.1369$
    trimmed              150,690        8,782      159,472    0.5838$

  trimming saved 53.6% of the tokens and 48.6% of the dollars
  (dollars save a touch less, because output tokens are untouched and
  billed higher). Output is the same; all the saving is on re-sent input.

  The real win shows up as the task gets longer. Naive vs trimmed total
  tokens, by task length:
     steps     naive tok   trimmed tok   naive/trim
         5        26,336        26,336        1.00x
        10       101,973        76,183        1.34x
        15       203,964       118,452        1.72x
        20       343,824       159,472        2.16x

  Naive climbs quadratically, trimmed climbs linearly, so the gap widens
  with every step. This one lever, what you keep in the context, is the
  biggest knob on an agent's bill. Prompt caching is the other one: it
  cuts the price of the re-sent prefix, but the SHAPE stays the same.

==============================================================================
Part 3: one request, K round trips, and the tail fires K times
==============================================================================
  A single model call here is about 0.29s. But one user
  request becomes 20 of them, run one after another (Day 1: latency
  is round trips). You pay the trips back to back, and the context keeps
  growing, so each trip is a little slower than the last.

    naive 20-step request, mean wall clock:    16.65s
    trimmed 20-step request, mean wall clock:  11.12s
    (trimming is faster too: a smaller context prefills quicker.)

  Now the tail (Day 4). Each call is slow 5% of the time. Over one
  call that is a 5% worry. Over 20 sequential calls, the chance that
  AT LEAST ONE is slow is 1 minus (every call fast):
    measured over 20,000 runs: 64.3% of runs hit a slow step
    analytic 1 - (1 - 0.05)^20:      64.2%

  So a long loop is almost guaranteed to stub its toe on the tail at
  least once, and that one slow step stalls the whole request. More
  steps means more cost, more latency, and more chances to go wrong.
  That is the case for a tight tool loop over a sprawling one.

==============================================================================
Scoreboard
==============================================================================
  P1 double-steps cost factor        you =    3.2   actual =     3.1 x       close enough
  P2 total vs 20 first-calls         you =    8.0   actual =     8.0 x       close enough
  P3 trim saving                     you =   55.0   actual =    53.6 %       close enough
  P4 any step slow                   you =   64.0   actual =    64.3 %       close enough

==============================================================================
The number to carry
==============================================================================
  A naive 20-step agent re-sent the whole context every step and
  processed 343,824 tokens, 8.0x what you would have budgeted for
  20 plain calls. Double the steps and the bill went up 3.1x, not 2x:
  that is the quadratic. Trimming the context (keep the last few,
  summarise the rest) saved 54% of the tokens and turned the curve
  back into a line. And because one request is K sequential calls, the
  5% slow tail got 20 chances and hit 64% of runs. Fewer, tighter
  steps win on all three: cost, latency, and the odds of going wrong.
```

Part 1 is the day. The twenty steps each look reasonable on their own, but the input to each one keeps climbing, from 1,700 tokens on step 1 to 32,000 on step 20, because every step re-sends all the steps before it. The sum is about 344,000 tokens for one request, 8x the 43,000 you would have budgeted by multiplying one call by twenty. Doubling the steps took the cost from $0.36 to $1.14, a 3.1x jump, and the cost-per-step rose the whole way. That rising per-step cost is the quadratic showing its face.

Part 2 is the lever. Keeping the last 4 steps and summarising the rest cut the 20-step task from 344,000 tokens to 159,000, about 54% off, and the naive-versus-trimmed ratio widened from 1.0x at 5 steps to 2.16x at 20. The longer the task, the more trimming saves, because trimming is the thing that turns the quadratic curve back into a straight line. Dollars saved a little less than tokens (48.6% versus 53.6%), because the output tokens are untouched and billed at the higher rate, and all the saving lands on the re-sent input.

Part 3 is cost's twin, latency. One request became twenty sequential calls, about 17 seconds of wall clock where a single call was 0.29s, and trimming brought that to 11 seconds because a smaller context prefills faster. Then the tail: a 5% per-call slow chance, given twenty chances, hit at least once in 64% of runs, measured and analytic agreeing to the digit. That is Day 4 amplified by fan-out, and it is why a loop that wanders for twenty steps is both expensive and unreliable.

The one line to carry out of today: an agent re-sends its whole growing context on every step, so cost and latency climb with the square of the number of steps, and the two fixes that matter are taking fewer steps and keeping the context small.

</details>
