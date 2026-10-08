---
title: "Day 40 posts"
parent: "Day 40: agents, and why the token bill explodes"
grand_parent: "Week 6: AI systems"
nav_order: 3
---

# Day 40 posts: LinkedIn and X

The scoreboard makes a good screenshot: a 20-step agent processing 8x the tokens you would have budgeted, doubling the steps costing 3.1x not 2x, and context trimming saving half. Swap in your own numbers and voice.

## LinkedIn

Day 40 of 60 days of system design. Today I finally understood why agents are so expensive, by simulating the token accounting on my own laptop. No model, no API, just the maths every agent framework pays.

An agent loops: think, call a tool, read the result, repeat. The catch nobody tells you up front is that the model keeps no memory between calls. So the harness re-sends the WHOLE conversation so far on every single step. Step 1 sends a small prompt. Step 20 re-sends everything from steps 1 through 19 plus the fixed system prompt and tool schemas.

I ran a 20-step task:

    the first call:                2,157 tokens
    if all 20 calls stayed that small:   43,140 tokens
    what the run actually processed:    343,824 tokens

That is 8 times the budget you would naively write down. And because the input to each step keeps growing, the total grows roughly with the square of the number of steps. I doubled the steps from 10 to 20 and the cost went up 3.1x, not 2x.

Then I added the single biggest fix: cap the context. Keep the last 4 steps verbatim, collapse the older ones into one short summary. Same task, same 20 steps:

    naive total tokens:    343,824
    trimmed total tokens:  159,472

A 54% cut, and the saving gets bigger the longer the task runs, because trimming turns that quadratic curve back into a straight line. This one lever, what you keep in the context, is the biggest knob on an agent's bill.

The last part brought back two earlier weeks. One request is now 20 sequential model calls, so latency is 20 round trips (week 1). And a 5% slow-call tail (week 1, day 4) gets 20 chances to fire, so 64% of runs hit at least one slow step. More steps means more cost, more latency, and more ways to go wrong.

The lesson I am taking: a tight tool loop beats a sprawling one, and context management is not a nice-to-have, it is the cost model.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #llm #aiagents #learninginpublic

## X thread

**1/**

Day 40 of 60 days of system design. I simulated the token cost of an AI agent (no model, no API, just the accounting) and the bill is worse than it looks.

A 20-step agent processed 343,824 tokens. I would have budgeted 43,140.

8x. Here is why.

**2/**

An agent loops: think, call a tool, read the result, repeat.

The model keeps NO memory between calls. So the harness re-sends the whole conversation so far, every single step.

Step 1 is tiny. Step 20 re-sends steps 1 through 19. The input grows every step.

**3/**

Summing a growing input over K steps goes as K squared, not K.

I doubled the steps (10 to 20) and the cost went up 3.1x, not 2x.

Cost-per-step RISES as you add steps. That is the signature of a quadratic. The context you re-send is the tax.

**4/**

The single biggest fix: cap the context.

Keep the last 4 steps verbatim, summarise the rest into ~300 tokens.

Same 20-step task:
naive:   343,824 tokens
trimmed: 159,472 tokens

54% off, and the saving grows with task length. Quadratic turns back into a line.

**5/**

Fan-out brings back week 1.

One request is now 20 sequential model calls, so latency is 20 round trips.

And a 5% slow-call tail (day 4) gets 20 chances to fire. 64% of runs hit at least one slow step. One slow step stalls the whole request.

**6/**

So: more steps means more cost, more latency, and more ways to go wrong.

A tight tool loop beats a sprawling one, and context management is the cost model, not a nice-to-have.

Code: github.com/anurag629/system-design-60-days
