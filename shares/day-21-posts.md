---
title: "Day 21 posts"
parent: "Day 21: designing a news feed"
grand_parent: "Week 3: caching and the CDN"
nav_order: 3
---

# Day 21 posts: LinkedIn and X

The angle is the reframe: a feed is a caching problem, not a query. The push vs pull tradeoff is the whole post. Swap in your own voice.

## LinkedIn

Day 21 of 60 days of system design, end of week 3. I designed a news feed, and the big realisation was this: a feed is not a database query with a cache in front. It is a caching problem with a database underneath.

The one decision that is the whole design is how you fan out a post.

Push (fan-out on write): the moment you post, copy it into the precomputed feed of every follower. Reads are then instant, one cache lookup. Perfect, until a celebrity with 10 million followers posts, and that one tweet becomes 10 million cache writes.

Pull (fan-out on read): do nothing at post time; at read time, gather recent posts from everyone you follow and merge. Writes are cheap even for a celebrity, but now every refresh does a pile of work, and reads outnumber posts many times over.

So you do both. Push for normal accounts, so almost everyone gets instant feeds cheaply. Pull for the handful of mega-accounts, so one celebrity post does not trigger 10 million writes. When you open the app, your feed is your precomputed push feed with the few celebrities you follow merged in at read time. The follower count is the dial between the two.

And every other piece was a day from this week. The feed cache is the working set (you keep hot feeds only for active users). Turning post ids into posts is cache-aside. The celebrity post that millions load at once is the thundering herd and the hot key together. The images come from a CDN.

A week ago a cache was a dict in front of a slow function. Now I can see that past a certain scale, caching is the architecture.

Code and notes: github.com/anurag629/system-design-60-days

#systemdesign #caching #learninginpublic

## X thread

**1/**

Day 21, end of week 3 of 60 days of system design. I designed a news feed, and the lesson is: a feed is a caching problem, not a database query.

**2/**

The whole design is one decision: how to fan out a post.

Push: copy each post into every follower's precomputed feed at write time. Reads instant. Breaks when a celebrity with 10M followers posts = 10M writes per tweet.

**3/**

Pull: do nothing at post time, merge everyone's recent posts at read time. Writes cheap even for a celebrity. But reads outnumber posts many times over, so now every refresh is expensive.

**4/**

So you do both. Push for the many (instant feeds, cheap). Pull for the few mega-accounts (no 10M-write storm). Your feed = your push feed + celebrities merged in at read time. The follower count is the dial.

**5/**

Everything else was a day from this week:

feed cache = working set (hot feeds for active users only)
id -> post = cache-aside
celebrity post, 10M readers = thundering herd + hot key
images = CDN

Week 3 done. Past a certain scale, caching IS the architecture.

Code: github.com/anurag629/system-design-60-days
