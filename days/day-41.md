---
title: "Day 41: serving concerns, caching, limiting and fallback"
parent: "Week 6: AI systems"
nav_order: 6
has_children: true
---

# Day 41
## Serving concerns, or the three cheap tricks that make an AI feature affordable and keep it up 🛡️

Today's one idea: the model is the expensive, glamorous part, but whether your AI feature is affordable and whether it stays up is decided almost entirely by three unglamorous layers wrapped around it. A semantic cache that answers repeat questions without calling the model. A rate limiter that meters tokens instead of requests, because tokens are what you pay for. And a gateway that retries, and when the primary provider falls over, fails across to a backup. You have met all three before, in weeks 3, 4 and 5. Today you point them at a GPU.

Yesterday the agent made one user request fan out into twenty model calls, and you watched the token bill climb. Today you learn to push that bill back down and to keep serving when the provider has a bad afternoon.

---

## Before you start ⏪

You want three earlier ideas fresh. Caching from week 3, especially cache-aside (Day 15) and the hot-key skew of Day 18, because a semantic cache is cache-aside with a cleverer key. Rate limiting and backpressure from week 4 (Day 27), because a token bucket is the same shape you already know. And failover from week 5, the quorums and read-repair of Day 31, because fallback is just "ask someone else when the first one does not answer". If you did Day 38 this week, the toy embedding today is the same idea in miniature. No GPU, no API key, no network. Everything runs on your laptop in well under a minute.

---

## Words you will meet today 📖

A semantic cache is a cache whose key is the meaning of a query, not its exact text. You embed the query into a vector, and a new query is a hit if it is close enough (by cosine similarity) to one you already answered. Paraphrases of the same question collapse onto a single stored answer.

An embedding is a vector that stands in for a piece of text, built so that texts with similar meaning land near each other in the vector space. Today's is a hand-rolled toy, a bag of content words, but the shape is exactly the real thing from Day 38.

Cosine similarity is the standard way to measure how close two embeddings point. It runs from 1 (same direction, same meaning) down through 0 (unrelated). You pick a threshold, and at or above it you call two queries "the same".

A token bucket is a rate limiter that holds a budget of tokens, refilled at a steady rate, and admits a request only while the budget can still cover its cost. It is the right meter for an LLM because the bill is counted in tokens.

A model gateway is the service that sits between your app and the model providers. It does the caching, the rate limiting, the retries and the fallback, so your application code just asks for an answer.

Fallback is serving a request from a secondary model (or a cache) when the primary fails or is too slow. It is what turns a provider outage from "feature down" into "feature slightly worse".

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these, one per layer, plus the cost framing:
- [Prompt caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching) in the Anthropic docs. The production cousin of today's Part 1: cache the expensive prefix so you stop paying to re-read the same context. Read it for the cost framing, that caching an LLM is first and foremost a money decision.
- [GPTCache](https://github.com/zilliztech/GPTCache) on GitHub. The open-source semantic cache that popularised the idea. Skim the README: embed the query, nearest-neighbour search, a similarity threshold, return the stored answer. That is exactly your Part 1.
- [Rate limits](https://platform.openai.com/docs/guides/rate-limits) in the OpenAI docs. Note that the limits are quoted in tokens per minute (TPM), not just requests per minute. That one word, tokens, is the whole of Part 2.
- [LiteLLM routing and fallbacks](https://docs.litellm.ai/docs/routing). A real model gateway. Read the fallbacks and retry sections, which is Part 3 as a shipping product: a list of models, try the first, fall through to the next.

Watch, after the lab:
- [Semantic Caching Explained: Reduce AI API Costs with Redis](https://www.youtube.com/watch?v=NrqvtsnjIHU) by Nariman Codes, a short, concrete walk through the embed, match and serve loop you will build.
- [API Rate Limiting Algorithms](https://www.youtube.com/watch?v=i8Rt18MU-EE) by Code with GD, the token bucket set beside the leaky bucket and the window counters, so you know where the token bucket fits.

### The three cheap tricks, and why they are old friends (12 min)

Here is the mental picture for the whole day. Your application does not talk to the model directly. It talks to a gateway, and the gateway has three jobs that happen in order on every request.

First, check the cache. If someone already asked this, in these words or in different words that mean the same thing, hand back the stored answer and do not call the model at all. Second, if it is not cached and we do have to spend money, make sure we can afford it: meter the tokens so one greedy feature cannot drain the whole budget. Third, actually call the model, and if the call fails or hangs, retry, and if it keeps failing, call a different model so the user still gets something.

Notice that not one of these is new. Checking a cache before doing expensive work is cache-aside, straight out of Day 15. Metering spend so one tenant cannot starve the rest is the rate limiting and load shedding of Day 27. Falling across to a backup when the primary is down is failover, the same instinct behind the quorums of Day 31. The reason week 6 feels learnable is that you already did the hard part. An LLM is just a very expensive, occasionally flaky backend, and you know how to wrap one of those.

What is genuinely new is the shape of the cost. A normal backend charges you roughly per request. An LLM charges per token, and the number of tokens per request varies wildly, from a one-line "thanks" to a 50-page document pasted into the prompt. That single fact bends two of today's three tricks. It is why the cache wants to match by meaning (so a hundred phrasings of one question cost you one answer) and it is why the limiter must count tokens (so a handful of giant requests cannot quietly cost more than a flood of tiny ones).

### A cache that understands paraphrases (14 min)

Think about a support chatbot. Over a day, thousands of people ask, in their own words, the same small set of questions. "How do I reset my password." "I forgot my password, how do I reset it." "Steps to reset my password." To a human these are obviously one question. To an ordinary cache, which keys on the exact string, they are three completely different keys, three misses, three calls to the model, three times the cost. The exact cache only ever helps when someone types a previous question character for character, which almost nobody does.

A semantic cache fixes this by changing the key. Instead of keying on the text, you embed the query into a vector, a list of numbers chosen so that queries meaning the same thing point in nearly the same direction. Then a new query is a hit when its vector is close to a stored one, close meaning cosine similarity at or above some threshold you pick. Now all three password questions land in the same neighbourhood, so the first one calls the model and the other two are free.

Today's embedding is deliberately a toy, so you can see every moving part. You lowercase the query, drop the filler words (how, do, I, my, to), and keep the content words (reset, password). That little bag of words, normalised to a unit vector, is the embedding. Two queries built from the same content words point the same way and score a high cosine. A real embedding from a trained model is far richer, it can tell that "cancel" and "unsubscribe" are cousins even though they share no letters, but the mechanic is identical: text goes in, a vector comes out, and close vectors mean close meaning.

The threshold is the interesting knob, and it is a genuine tradeoff, not a free lunch. Set it too high, say 0.95, and you only catch near-identical phrasings, so you miss most paraphrases and leave savings on the table. That is a false miss, and it only costs you money. Set it too low, say 0.3, and you start serving the cached password answer to someone asking about billing, because the vectors were vaguely close. That is a false hit, and it is far worse, because the user gets a confidently wrong answer. So you tune the threshold on the cautious side and accept a slightly lower hit rate, the same way you would rather a search engine miss a result than show you the wrong one. In the lab you will measure a semantic hit rate near 68% against an exact cache's 7% on the same traffic, and that gap is the entire argument for the technique.

### Meter the token, not the request (12 min)

Now the limiter. On an ordinary backend you cap requests per minute, because every request costs roughly the same, so counting requests is a fine proxy for counting work. On an LLM that proxy breaks, and it breaks expensively.

Here is the trap. You know your budget is, say, ten thousand tokens a minute, so you reach for the limiter you have always used and set it to a hundred requests a minute, quietly assuming each request is about a hundred tokens. For a while it is fine. Then someone ships a feature that summarises long documents, and its requests are two thousand tokens each. Your hundred-requests-a-minute limiter cheerfully waves through a hundred of them, which is two hundred thousand tokens, twenty times your budget, and you find out when the invoice arrives. The limiter did its job perfectly. It was just counting the wrong thing.

A token bucket counts the right thing. You give it a budget of tokens, and each request, when it arrives, tries to draw its own token cost from the bucket. A small request draws fifty, a big one draws two thousand. Admit the request only while the bucket still holds enough, otherwise reject or queue it. The beautiful part is that the same bucket does the right thing for both shapes of traffic: it will admit two hundred tiny requests or five huge ones, whichever shows up, and in both cases the total it admits is one budget's worth of tokens. The request cap could not do that, because it never knew what a request weighed. In the lab you will watch a request cap under-spend on small traffic and overshoot the budget twentyfold on large traffic, while the token bucket sits exactly on the line in both. This is the same backpressure instinct as Day 27, only the unit of pressure is the token.

### The gateway: retries for blips, fallback for outages (12 min)

The last layer is about staying up. Model providers fail. A call times out, or comes back with a 503, or the whole provider has a bad hour. Your feature should not simply fall over every time.

There are two different failures hiding here, and they need two different fixes. The first is the independent blip: a single call fails for no deep reason, and a retry a moment later succeeds. Retries handle this beautifully, because an independent 30% failure almost never repeats three times in a row (0.3 cubed is under 3%), so three tries turns a 70% success rate into about 97%. If failures were always independent, retries alone would be enough and you could stop there.

The second failure is the one that bites: the provider is actually down. Now every attempt fails, not independently but together, and retrying is useless. You can retry a dead endpoint a thousand times and get a thousand failures. This is where fallback earns its keep. Past a threshold of failed attempts on the primary, the gateway gives up on it and calls a second provider, a different model, ideally on different infrastructure. In the lab you will simulate a full primary outage and watch success with no fallback sit at a flat 0%, while the same gateway with a fallback holds it at basically 100%. Retries did nothing there, because the thing they protect against was not what went wrong.

And here is where today's three tricks join hands. During that outage, your semantic cache is still sitting there full of yesterday's answers. The most common questions, the head of the distribution, can be served straight from the cache with no model call at all, primary or secondary. So the real production answer to "what happens when my provider goes down" is: the cache covers the common questions, the fallback model covers the rest, and the user barely notices. That is the same defence in depth you have been building all along, caching plus failover, now protecting an AI feature. Fallback is cheap insurance. You pay a little complexity every day, and most days it does nothing, and then on the one bad afternoon it is the only reason you still have a product.

---

## Block 2: drill (40 min) ✍️

Paper first. Then copy your answers into [`notes/day-41-drills.md`](../notes/day-41-drills.md).

D1. A semantic cache runs over 10,000 support queries in a day. 60% are paraphrases of the 200 most common questions, and you measure a 55% hit rate. At $0.01 per model call, what do you save versus no cache? Then: a too-low threshold (0.3) causes false hits, a too-high one (0.95) causes false misses. Which error is worse, and why?

D2. Your token budget is 1,000,000 tokens per minute. You set a request limiter at 10,000 requests per minute, assuming 100 tokens each. A new summarisation feature sends 5,000-token requests. How many does the request limiter admit, how many tokens is that, and what multiple of the budget? How many would a token bucket have admitted?

D3. The primary model fails 20% of attempts, independently. (a) Success on one attempt. (b) Success with up to 3 attempts. (c) During a full outage the primary fails 100% of the time: success with 3 retries and no fallback. (d) Add a secondary that fails 5% per attempt, up to 3 tries: outage success with fallback.

D4. Describe the order a request should flow through a gateway that has a semantic cache, a primary model and a secondary model. Explain how the cache plus fallback together let you survive a primary provider outage, and name the main risk of leaning on the cache during that outage.

D5. The PM maths. 100,000 users, 20 messages a day each, average request 800 input tokens and 200 output tokens, priced at $3 per million input and $15 per million output. Daily cost with no cache? With a semantic cache at a 40% hit rate? Roughly what is the monthly saving?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-41-serving/serving.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-41-serving/serving.py).

It is in three parts. Part 1 runs a support-chat workload, mostly paraphrases of five questions, through an exact-match cache and a semantic cache, and measures the hit rate and the model calls each one saves. Part 2 feeds a stream of small requests and a stream of large ones through a request cap and a token bucket on the same budget, and shows which limiter actually respects the budget. Part 3 simulates a flaky primary model and measures the end-user success rate with retries alone, then with fallback, on a normal day and during a full outage.

Standard library only. No model, no embedding API, no network, no numpy. Everything is a deterministic toy with made-up vectors, token counts and failure coins, seeded so your run matches the reference to the digit. It finishes in under a second and leaves no files behind.

### Predict first

Fill in `PREDICTIONS` at the top.

- P1. The semantic cache runs over a workload that is mostly paraphrases of a handful of questions. What percent of queries are a cache hit?
- P2. The same workload through a plain exact-match cache. What percent are a hit? (It only catches literal repeats.)
- P3. A workload of big requests through a limiter that caps requests, not tokens. How many times over the token budget does it let spend go?
- P4. The primary model is in a full outage. With a gateway that falls back to a healthy secondary, what percent of users still get an answer?

P2 is the one to feel first. Write a number. Most people guess the exact cache catches "a fair few" of the paraphrases. It catches almost none, because a paraphrase is a different string.

### Fill in the TODOs

1. TODO 1 is `cosine`, the meaning-distance. For two unit vectors it is just their dot product, the sum over the dimensions they share. This is the heart of the semantic cache.
2. TODO 2 is `is_cache_hit`, the decision: the best match counts as the same meaning when its similarity reaches the threshold.
3. TODO 3 is `can_admit`, the token bucket: admit a request only if the budget still holds at least its token cost. This one line is the whole difference from a request cap.
4. TODO 4 is `gateway_ok`, the fallback: the user is served if the primary succeeded, or if the secondary did.

```bash
cd labs/day-41-serving
python3 serving.py
```

### What you're going to discover

Part 1 is the headline. Same workload, two caches. The exact-match cache catches only the three word-for-word repeats, a 7% hit rate, because every paraphrase is a new string to it. The semantic cache reads the meaning under the wording and hits 68%, cutting model calls from 41 down to 13. That gap, 7% against 68%, is the entire case for keying a cache by meaning.

Part 2 is the trap sprung in slow motion. On the small-request workload the request cap stops at 100 requests and spends barely half the budget, turning away requests that would have fit. On the large-request workload the same cap waves through 100 big requests and spends twenty times the budget. The token bucket, metering the token, lands exactly on the budget in both cases. One limiter counts requests and is wrong twice. The other counts the thing you pay for and is right both times.

Part 3 is the two-failures lesson. On a normal day, retries alone lift success from 70% to 97%, and fallback just tops it off to 100%, so you might think fallback is barely worth it. Then the primary goes fully down, and retries collapse to a flat 0%, because retrying a dead model just fails faster. Fallback holds success at 99.9%. The trick that looked redundant on the good day is the only thing standing on the bad one.

### Traps ⚠️

- A semantic cache lives or dies by its threshold. In the lab a threshold of 0.6 cleanly separates paraphrases from genuinely different questions, because the toy embedding makes same-meaning queries score well above it and different ones well below. Drop the threshold toward 0 and you will start serving confident nonsense (false hits). That failure, a wrong answer, is worse than a miss, so real systems tune the threshold high and give up some hit rate to protect correctness.
- The token bucket admits in arrival order and stops at the first request that does not fit, so its spend sits at or just under the budget, never over. If you see it go over, you deducted the cost before checking it fits. Check first, then deduct.
- In Part 3, do not read the normal-day numbers and conclude fallback is pointless. The whole argument is the outage row, where retries give 0% and fallback gives 99.9%. Retries and fallback defend against different failures. You want both.
- The embedding here is a toy bag of words. Do not mistake it for the real thing. A trained embedding would catch synonyms the bag of words misses ("cancel" and "unsubscribe"). The mechanic you are learning, embed then threshold on cosine, is identical.

### Deliverable

[`labs/day-41-serving/RESULTS.md`](../labs/day-41-serving/RESULTS.md) has a skeleton. Paste the output, and write one line each: why the exact cache saved almost nothing, why a request cap is the wrong meter for an LLM, and why retries alone did not survive the outage.

---

## Block 4: write (30 min) 📣

Your angle today is the measured surprise: "most of the engineering that makes an AI feature affordable and reliable has nothing to do with the model. It is a cache keyed by meaning (68% hits vs 7%), a limiter that counts tokens not requests (a request cap overspent the budget 20x), and a fallback that turned a total outage from 0% served into basically 100%." The scoreboard is the screenshot.

Example posts are on the [Day 41 posts](../shares/day-41-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the semantic-versus-exact hit rate you measured, and one thing you still cannot explain.

Day 42 is the week's design day: you take all of week 6, prefill and decode, the KV cache, vector search, RAG, agents, and today's serving layer, and design a production AI chat product or a RAG system at real scale, timed, then a retro. Today you learned the layer that sits between your app and the model. Tomorrow you put the whole stack together.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. A 55% hit rate on 10,000 queries is 5,500 queries served from cache, so 5,500 model calls avoided, which at $0.01 each is $55 saved that day against calling the model every time. The two threshold errors are not equal. Too high (0.95) causes false misses: paraphrases look like new questions, so you call the model when you did not have to. That only costs money. Too low (0.3) causes false hits: a query that is merely vaguely close to a stored one gets the stored answer, so a billing question might be served the password answer. That is a wrong answer in front of a user, a correctness bug, which is much worse than paying for a call you could have saved. So you tune the threshold on the cautious side and accept a lower hit rate.

D2. The request limiter admits its cap of 10,000 requests. At 5,000 tokens each that is 50,000,000 tokens, which is 50 times the 1,000,000-token budget. The overspend is 50x, and it is exactly the ratio between the real request size (5,000) and the size the cap silently assumed (100). A token bucket on the same budget would admit 1,000,000 / 5,000 = 200 requests, landing exactly on the budget. The limiter was not broken. It was metering requests when the budget is denominated in tokens.

D3. (a) One attempt, 20% failure, so 80% success. (b) Three attempts fail only if all three fail: 1 minus 0.2 cubed = 1 minus 0.008 = 99.2%. (c) In a full outage the primary fails 100% of the time, so all three retries fail and success is 0%. Retries do nothing against an outage, because the failures are not independent, they are the same dead endpoint every time. (d) A secondary failing 5% per attempt over three tries fails only 0.05 cubed = 0.000125 of the time, so success with fallback is about 99.99%. The lesson: retries kill independent blips, fallback kills outages, and you need both because they defend against different things.

D4. The flow is cache, then primary, then secondary. Embed the incoming query and check the semantic cache first; on a hit, return the stored answer with no model call. On a miss, call the primary with a couple of retries; if it is still failing, fall back to the secondary; then store the fresh answer back in the cache. During a full primary outage the cache serves the common head of the question distribution with no model at all, and the secondary serves the long tail, so most users still get answered. The main risk of leaning on the cache is staleness: a cached answer that was correct when stored may now be out of date, and a loose similarity threshold can serve a confidently wrong answer to a slightly different question. Mitigate with TTLs, per-tenant scoping, and a conservative threshold.

D5. Per message, input is 800 tokens at $3 per million = $0.0024, output is 200 tokens at $15 per million = $0.003, so $0.0054 a message. Traffic is 100,000 users times 20 messages = 2,000,000 messages a day. With no cache that is 2,000,000 times $0.0054 = $10,800 a day. A 40% hit rate means only 60% reach the model, so $10,800 times 0.6 = $6,480 a day. The daily saving is $4,320, and over a month roughly $130,000. The embedding you run on every query to check the cache costs a tiny fraction of a cent and is noise next to a generation, so ignore it in the estimate. The real point of this drill is that you can now hand a PM a monthly dollar figure for an AI feature, which almost nobody can do.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-41-serving/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-41-serving/solution.py).

TODO 1, cosine similarity, the meaning-distance. The embeddings are already unit vectors, so the cosine is just the dot product over the dimensions they share:

```python
return sum(a[k] * b[k] for k in a if k in b)
```

TODO 2, the semantic-cache decision. The nearest stored query counts as the same meaning when its similarity reaches the threshold:

```python
return best_sim >= threshold
```

TODO 3, the token bucket, the whole difference from a request cap in one line. Admit only if the budget still covers the token cost:

```python
return available_tokens >= cost
```

TODO 4, the fallback. The user is served if the primary succeeded, or if the secondary did:

```python
return primary_ok or secondary_ok
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3, seeded run.

```
==============================================================================
Part 1: the semantic cache. Key by meaning, and the paraphrases
        collapse onto one model call
==============================================================================
  workload: 41 queries, mostly paraphrases of 5 questions,
  a handful of one-offs, and 3 word-for-word repeats.
  cosine threshold for 'same meaning': 0.6

  cache                 hits   model calls    hit rate
  no cache                 0            41        0.0%
  exact-match              3            38        7.3%
  semantic                28            13       68.3%

  The exact-match cache caught only the 3 literal repeats. Every
  paraphrase looked like a brand new string to it, so it called the
  model 38 times. The semantic cache saw the meaning behind the
  wording and called the model just 13 times.
  model calls saved vs exact-match: 25  ($0.25 at $0.01/call)
  Same workload. One cache keys by string and saves almost nothing,
  the other keys by meaning and cuts calls by more than half.

==============================================================================
Part 2: token-based rate limiting. Meter tokens, not requests, because
        the bill is per token
==============================================================================
  budget: 10,000 tokens per window.
  the naive limiter instead caps requests at 100 per window,
  which quietly assumes every request is about 100 tokens.

  workload              limiter           admitted   tokens spent
  many small (~50 tok)  token bucket           201          9,988
                        request cap            100          4,890
  few large (~2000 tok) token bucket             5          9,821
                        request cap            100        197,909

  On the small workload the request cap stopped at 100 requests and
  spent only about half the budget, turning away requests that would
  have fit fine. On the large workload it waved through 100 big
  requests and blew the budget by about 20x.
  The token bucket held spend at the budget in BOTH cases, because it
  meters the token, which is what the invoice is counted in.

==============================================================================
Part 3: the model gateway. Retries for blips, fallback for outages
==============================================================================
  primary fails 30% of attempts, secondary 10%, up to 3 tries each.

  Normal day (failures are independent blips):
    primary, 1 try, no fallback:         70.06%
    primary, 3 tries, no fallback:        97.32%
    primary 3 tries + fallback:          100.00%
  Retries alone do most of the work when failures are independent:
  one bad roll rarely repeats three times. Fallback just tops it off.

  Outage day (the primary is fully down, every attempt fails):
    primary 3 tries, no fallback:         0.00%
    primary 3 tries + fallback:           99.90%
  Now retries are useless: three failures out of three every time.
  Only the fallback keeps users served. This is the day the second
  provider, and a semantic cache serving yesterday's answers, earn
  their keep. Fallback is cheap insurance you are glad to have paid.

==============================================================================
Scoreboard
==============================================================================
  P1 semantic cache hit rate         you =   68.0   actual =    68.3 %       close enough
  P2 exact-match hit rate            you =    7.0   actual =     7.3 %       close enough
  P3 request-cap overspend           you =   20.0   actual =    19.8 x       close enough
  P4 outage success w/ fallback      you =   99.0   actual =    99.9 %       close enough

==============================================================================
The number to carry
==============================================================================
  Same support-chat workload, two caches. Keyed by string, the cache
  hit 7% of the time and saved almost nothing. Keyed by meaning,
  it hit 68% and cut model calls by more than half. That gap is the
  whole case for a semantic cache.
  A request cap let 20x the token budget through on big requests,
  because it meters the wrong thing. A token bucket meters tokens and
  holds the line. And when the primary went fully down, success without
  fallback collapsed to 0% while the gateway's fallback held it
  at 100%.
  None of this is AI magic. It is caching, rate limiting and failover,
  the same three moves from weeks 3, 4 and 5, pointed at a GPU.
```

Part 1 is the day. Same 41 queries, mostly paraphrases of five support questions. The exact-match cache caught only the three word-for-word repeats, a 7.3% hit rate, and called the model 38 times. The semantic cache read the meaning under the wording, hit 68.3%, and called the model 13 times. Keying by string saved almost nothing; keying by meaning cut the calls by more than half.

Part 2 is the trap. On small requests the request cap under-spent, stopping at 100 requests and 4,890 tokens, turning away requests that fit. On large requests the same cap spent 197,909 tokens, about 20 times the 10,000 budget. The token bucket landed on the budget both times, because it meters the token, which is what the bill counts.

Part 3 is the two-failures lesson. On a normal day retries lifted success from 70% to 97% and fallback finished it at 100%. Then the primary went fully down, retries collapsed to 0%, and only fallback held success, at 99.9%. The trick that looked redundant on the good day was the only one that worked on the bad day.

The one line to carry: AI serving is distributed systems with a GPU in the middle. A semantic cache is caching, a token bucket is rate limiting, a fallback is failover, the same three moves from weeks 3, 4 and 5, pointed at a very expensive backend.

</details>
