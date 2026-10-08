---
title: "Day 40 drills"
parent: "Day 40: agents, and why the token bill explodes"
grand_parent: "Week 6: AI systems"
nav_order: 2
---

# Day 40 drills

Written on paper first, with numbers. The agent loop, the growing context, and the bill that follows from it.

D1 (the loop costs a sum, not a single call. An agent runs 12 steps. The model keeps no memory between calls, so each call re-sends everything so far. Each step adds about 1,600 tokens of context (the model's turn plus the tool result), on top of 1,700 fixed tokens of system prompt and tools. Roughly how many INPUT tokens does step 12 send, and roughly how many input tokens does the whole 12-step run process? Why is the total much more than 12 times the first call?):

D2 (quadratic, in your own words. If every step adds a fixed chunk to the context, the input to step i grows linearly in i, so the total over K steps grows as K squared over 2. A 10-step task costs X. Without doing the full sum, estimate what a 30-step version of the same task costs relative to X, and say why doubling or tripling the steps hurts so much more than it looks):

D3 (the context lever. You cap the context: keep the last 4 steps verbatim and replace everything older with one 300-token summary. For a long task, what shape does the total cost curve become, linear or quadratic, and why? Name one thing a summary can quietly drop that then makes the agent repeat work or loop, and say why trimming is still usually worth it):

D4 (fan-out and the tail, back from weeks 1 and 4. One user request becomes 20 sequential model calls. A single call has a p99 of 3 seconds and a p50 of 0.3 seconds. Each call independently hits the slow path 5% of the time. What is the chance that at least one of the 20 steps is slow, and what does that do to the p99 of the WHOLE request compared to a single call? Which earlier day is this exactly?):

D5 (design judgement. A teammate's agent takes 25 steps and re-sends the full history every time, and the token bill is eating the feature's margin. Give three concrete levers to cut the bill, in the order you would reach for them, and say what each one trades. At least one must be about the number of steps, and one about what rides in the context on every call):
