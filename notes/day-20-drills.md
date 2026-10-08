---
title: "Day 20 drills"
parent: "Day 20: the CDN and cache invalidation"
grand_parent: "Week 3: caching and the CDN"
nav_order: 2
---

# Day 20 drills

Written on paper first. TTLs, conditional requests, 304s, purges, and serving stale on purpose.

D1 (a resource is requested 1,000 times/sec. You put a CDN in front with Cache-Control max-age=10s. Treating one edge as a single shared cache, how many requests per second reach the origin? Now the CDN has 50 edge locations (POPs) that do NOT share a cache. How many origin requests per second now, and what does that tell you about long-tail content on a big CDN?):

D2 (a 500 KB image with max-age=60 is requested again 5 minutes after it was stored, and the content has not changed. Compare a plain re-fetch against a conditional request with If-None-Match. What does the resulting 304 save you, in bytes and in origin work, and what does it NOT save?):

D3 (a response carries Cache-Control: max-age=60, stale-while-revalidate=600. For a request that arrives when the stored copy is 30s old, 120s old, and 700s old: in each case, is the copy served from the edge or does someone wait for the origin, and is a background refresh triggered?):

D4 (you shipped a broken app.css with max-age=86400 and users are stuck with it for a day. Compare two fixes: purge the file at the CDN, versus serve it from a new fingerprinted URL like app.9f3c2a.css. Which is more reliable and why? And why is the common rule "fingerprint your static assets with max-age=1 year, but serve index.html with no-cache"?):

D5 (one very hot page expires at the edge at the exact moment 10,000 requests/sec are hitting it. Under blocking revalidation with no coalescing, what does the origin feel? Explain how (a) request coalescing and (b) stale-while-revalidate each prevent that, and which one keeps user latency flat):
