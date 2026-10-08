---
title: "Day 58 posts"
parent: "Day 58: capstone writeup"
grand_parent: "Week 8: putting it all together"
nav_order: 3
---

# Day 58 posts: LinkedIn and X

The angle is that the writeup is the real deliverable, and numbers are what make it credible. Swap in your own voice.

## LinkedIn

Day 58 of 60 days of system design. I turned four days of designing, building and breaking into one architecture document.

Here is what surprised me. The code took a day. Writing it up so a staff engineer would trust it took longer and taught me more.

A staff engineer reading your doc checks three things, and none of them is whether the diagram is pretty. Do you know why you made each choice, or did you copy a pattern? Can you state what you deliberately did not do, or did you try to do everything and finish nothing? And are your claims backed by numbers or by hope?

That last one is where the load test earns its keep. "Writes peak at about 4,200 per second and the bottleneck is the single database writer" is a sentence hope cannot fake. I measured it, so I can defend it.

The shape of a doc that holds up: a one-paragraph summary a stranger understands, the requirements and the non-goals, the design in words with one diagram, the two or three hard decisions written as records of what I chose and what I rejected and why, then the measured results with the knee and bottleneck named, then the failure modes each with how I detect and degrade, then the rough cost. Four tight pages, not twenty vague ones.

The move that makes a doc trustworthy is admitting its own weaknesses. A doc that lists its failure modes is far more credible than one that pretends there are none. Honesty is the credibility.

The code gets rewritten. The ability to explain a system clearly, in writing, backed by numbers, compounds for a whole career.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #softwarearchitecture #writing #learninginpublic

## X thread

**1/**

Day 58 of 60 days of system design. Four days of design, build, break, turned into one architecture doc.

The surprise: the code took a day. Writing it up so a staff engineer would trust it took longer and taught me more.

**2/**

A staff engineer checks three things, none of them the diagram:

- Do you know WHY each choice, or did you copy a pattern?
- Can you state what you did NOT do?
- Claims backed by numbers or by hope?

**3/**

That last one is where the load test earns its keep.

"Writes peak ~4,200/s and the bottleneck is the single DB writer" is a sentence hope can't fake. I measured it, so I can defend it.

**4/**

Shape that holds up: summary a stranger gets, requirements + non-goals, design in words, 2-3 decisions (chosen/rejected/why), measured results with the knee named, failure modes with detect + degrade, rough cost.

Four tight pages, not twenty vague ones.

**5/**

The move that makes a doc trustworthy: admit its weaknesses. A doc that lists its failure modes beats one that pretends there are none.

Code gets rewritten. Explaining a system clearly, backed by numbers, compounds for a career.

Code: github.com/anurag629/system-design-60-days
