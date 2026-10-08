---
title: "Day 20 posts"
parent: "Day 20: the CDN and cache invalidation"
grand_parent: "Week 3: caching and the CDN"
nav_order: 3
---

# Day 20 posts: LinkedIn and X

The scoreboard makes a good screenshot: origin hits falling from 120 to 12, and the stale-while-revalidate worst case staying at 1 ms while blocking revalidation spikes to 38 ms. Swap in your own numbers and voice.

## LinkedIn

Day 20 of 60 days of system design. Today I built a tiny CDN on my laptop to finally understand cache invalidation, which is supposed to be one of the two hard problems in computing.

I wrote a small origin server that does real work on every request (about 60 ms), and put a tiny edge cache in front of it, the way your browser sits in front of a CDN that sits in front of your server. Then I sent the same 120 requests for the same 3 resources through it.

With no cache, all 120 reached the origin. Average latency 66 ms, because every read paid the full cost.

    no cache:   120 origin hits,  66 ms average
    TTL cache:   12 origin hits,   4 ms average

The cache cut origin load by about 10x. The part that clicked for me: when a cached copy went stale, the edge did not just re-download it. It sent a conditional request (If-None-Match, with the ETag it already had), and because nothing had changed the origin replied 304 Not Modified, with no body. 9 of those 12 origin trips were cheap 304s. The conditional request saves the body and the regeneration work, though you still pay the round trip.

Then the best bit, stale-while-revalidate. When a copy is just past fresh, instead of making the unlucky request wait for the origin, the edge hands over the slightly old copy instantly and refreshes it in the background.

    blocking revalidation:   worst request  38 ms
    stale-while-revalidate:  worst request   1 ms

Both hit the origin the same number of times. The difference is who waits. Under blocking, the one request that arrives the moment the copy expires eats the whole origin trip while everyone else is served from the edge. Under stale-while-revalidate, nobody waits. That is why CDNs serve slightly stale content on purpose.

Caching is not free. Every cache is a second copy of the truth, and now you own keeping them in agreement. But measured like this, you can see exactly what you are buying.

Code is public: github.com/anurag629/system-design-60-days

#systemdesign #caching #cdn #learninginpublic

## X thread

**1/**

Day 20 of 60 days of system design. I built a tiny CDN on my laptop to understand cache invalidation.

Same 120 requests for 3 resources:

    no cache:  120 origin hits, 66 ms avg
    TTL cache:  12 origin hits,  4 ms avg

A ~10x cut in origin load. Here is what actually happens.

**2/**

A CDN keeps a copy at the edge and serves it while it is fresh (max-age). When it goes stale, it does NOT blindly re-download.

It sends a conditional request: "If-None-Match: <etag>". If nothing changed, the origin replies 304 Not Modified, no body.

9 of my 12 origin trips were cheap 304s.

**3/**

A 304 saves the body and the work of regenerating it. It does NOT save the round trip. You still had to go ask the origin "did this change?"

So the big win is really that MOST requests never leave the edge at all. The few that do are cheap.

**4/**

Now the nice trick: stale-while-revalidate.

When a copy is just past fresh, serve the slightly old copy INSTANTLY and refresh it in the background.

    blocking:               worst request 38 ms
    stale-while-revalidate: worst request  1 ms

Same number of origin hits. Different victim.

**5/**

Under blocking revalidation, the one request that arrives the instant the copy expires is stuck waiting for the origin. Everyone else is served from the edge in ~1 ms. That is a latency spike for one unlucky user.

SWR makes nobody wait. The refresh happens behind the scenes.

**6/**

So the whole day in one line:

A CDN is just a cache at the edge. max-age decides freshness, the conditional request makes revalidation cheap, and serving stale on purpose keeps the unlucky request from paying for everyone else's refresh.

Code: github.com/anurag629/system-design-60-days
