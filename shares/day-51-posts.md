---
title: "Day 51 posts"
parent: "Day 51: mock, a URL shortener"
grand_parent: "Week 8: putting it all together"
nav_order: 3
---

# Day 51 posts: LinkedIn and X

The angle is that knowing a design and performing it under the clock are two different skills. Swap in your own voice.

## LinkedIn

Day 51 of 60 days of system design. First timed mock: design a URL shortener in 45 minutes, out loud, no pausing.

I have "known" this design for weeks. I could draw it on a napkin. So I expected the mock to be easy. It was not, and that gap taught me more than any reading this week.

Knowing a design is passive. You recognise the pieces when you see them. Performing it is active: you have to produce the pieces, in order, while a clock runs and you narrate your reasoning. Completely different muscle.

What the clock exposed for me:

The whole system is really a cache design. It is read heavy by about 100 to 1, a link is created once and visited thousands of times, so almost every request is a read you have already seen. Get that fact out early and the rest of the design follows from it.

The write path and the read path should share nothing. If the component that generates short codes dies, writes pause but every existing redirect keeps working, because resolving a code is a cache or database read that never touches the generator. Saying that out loud is the move that sounds senior.

Analytics does not belong on the redirect path. Use a 302 so clicks come back through you, then drop each click on a queue and count it offline. The redirect returns instantly and never waits for the counter.

The lesson of the day: practise performing, not just knowing. Run the mock, grade yourself honestly, find the step that ate your clock, and do it again.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #interviewprep #learninginpublic

## X thread

**1/**

Day 51 of 60 days of system design. First timed mock: design a URL shortener, 45 min, out loud, no pausing.

I have "known" this for weeks. The mock was still hard. That gap was the lesson.

**2/**

Knowing a design is passive, you recognise the pieces. Performing it is active, you produce them in order while a clock runs and you narrate.

Different muscle entirely.

**3/**

What the clock exposed:

It is a cache design. Read heavy ~100:1. A link is made once, visited thousands of times. Say that early and the whole design follows.

**4/**

Read path and write path share nothing. If the code generator dies, writes pause but every redirect still works, because resolving a code never touches the generator.

That sentence sounds senior.

**5/**

Analytics is not on the redirect path. 302 so clicks return to you, then queue each click and count offline. Redirect never waits.

Practise performing, not just knowing.

Code: github.com/anurag629/system-design-60-days
