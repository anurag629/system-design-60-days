---
title: "Day 53 mock briefs"
parent: "Day 53: mock, a rate limiter and a news feed"
grand_parent: "Week 8: putting it all together"
nav_order: 1
---

# Mock 3: two designs, 20 minutes each

Copy this into your fork. Run the rate limiter first, hard stop at 20 minutes, short break, then the news feed. The skill today is getting to the hinge decision fast. Spend about 4 minutes on requirements and scale, then go straight to the one decision that matters.

---

## Mock 3a: design a distributed rate limiter (20 min)

### Brief
Limit each user to N requests per minute across a fleet of many gateway servers. Reject the excess politely. The limit should be close to exact, and the limiter must never take down the service it protects.

1. Requirements + scale (4 min):

2. The hinge: where does the limit state live across many gateways? (central, local, hybrid, and the tradeoff):

3. Algorithm and the reject response (429 + Retry-After):

4. It falls over: the central store is down. Fail open or closed?

Self-grade (out of 10): reached distributed-state decision by minute 8? named the tradeoff? handled store-down? ______

---

## Mock 3b: design a news feed (20 min)

### Brief
A user follows others, posts, and sees a feed of recent posts from people they follow. Feed open must be fast. Some users have 100 million followers.

1. Requirements + scale (4 min):

2. The hinge: fan-out on write or on read? (and the cost that kills each at the extreme):

3. The hybrid: who gets which, and how is one follower's feed assembled from both?

4. It falls over: a celebrity with 100M followers posts. What do you do?

Self-grade (out of 10): reached the fan-out decision by minute 8? named the hybrid? handled the celebrity? ______

---

The one I ran cleaner, and why: ______
