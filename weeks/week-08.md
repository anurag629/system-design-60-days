# Week 8: putting it all together 🎯

Days 50 to 60, Tue 2026-11-10 to Fri 2026-11-20.

This is it, the last stretch. Seven weeks of building small broken systems and measuring them has quietly turned into something. You do not "know facts about system design" any more. You have judgement. This week you prove it to yourself.

The plan is simple. First a couple of days learning how to actually run a design conversation, because a 45-minute interview is a performance with a structure, and knowing the structure frees your brain to think. Then four timed mock designs across the topics you have covered, each one written up and critiqued. Then a real capstone: you pick one system, design it properly, build a slice of it, load test it until it breaks, and write the architecture document you would be proud to hand a staff engineer.

No new theory this week. Everything you need, you already have. This week is about fluency and nerve.

## What you will be able to do by day 60

Walk into any system design interview and run it calmly: clarify the problem, estimate the scale on a napkin, sketch the high level, go deep where it matters, and talk honestly about failure, cost and tradeoffs. And more importantly, actually build and reason about real systems at work, which is the point that outlasts any interview.

## The days 🗓️

Day 50: the framework. How to run a 45-minute design cleanly: requirements, scale estimate, API, high-level design, deep dives, then bottlenecks and failure. We practise the shape with no pressure.

Day 51: mock 1, design a URL shortener, end to end and timed. The classic. You have already built pieces of this, now assemble the whole thing under the clock.

Day 52: mock 2, design a chat system like WhatsApp. Fan-out, delivery, presence, and the scale of a billion users. 💬

Day 53: mock 3, design a rate limiter and a news feed. Two smaller ones, back to back, to build speed.

Day 54: mock 4, design an AI system, a production RAG or chat product. This ties week 6 into everything else and is exactly the kind of question showing up in real interviews now.

Day 55: capstone kickoff. Pick one system you genuinely care about. Write the requirements and the architecture doc first, before any code.

Day 56: capstone build. Implement one real slice of it, the interesting part, not a toy.

Day 57: capstone load test. Point k6 or your own load generator at it, push until it breaks, and find the true bottleneck. Break your own thing before the world does.

Day 58: capstone writeup. Turn what you learned into a clean architecture document: the design, the tradeoffs, the numbers, the failure modes, the cost.

Day 59: review and gaps. Look honestly at what is still shaky across all eight weeks and spend the day on targeted revision. You will know exactly where the weak spots are by now.

Day 60: the finish. Present the capstone to yourself out loud as if to an interviewer, then a proper retrospective on the whole 60 days, and a plan for what comes next. 🏁

## Core resources for the week 📚

Read and use:
- [Hello Interview](https://www.hellointerview.com/), the most honest free interview prep, for the mock structure and common designs.
- Your own repo. Seriously, re-read your `RESULTS.md` files and progress log. Sixty days of your own measured numbers is a better revision guide than any book.

Watch:
- [Exponent](https://www.tryexponent.com/) mock interview recordings, to see how a strong candidate structures 45 minutes under pressure.

## What trips people up at the finish ⚠️

They think day 60 is a finish line. It is a base camp. You will not have "mastered" every corner of distributed systems in two months, and anyone who claims they did is selling something. What you will have is a method: measure before you guess, know the numbers, reason from the data, and design the failure path on purpose. That method compounds for the rest of your career. The certificate is not the repo or a score. It is that you now think like someone who builds real systems. Keep building. Keep measuring. Keep sharing what you learn. 🚀
