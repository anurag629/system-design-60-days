---
title: "Day 21: designing a news feed"
parent: "Week 3: caching and the CDN"
nav_order: 7
has_children: true
---

# Day 21
## Designing a news feed, where caching stops being a trick and becomes the architecture 📰

Today's one idea: a news feed is not a database problem with a cache bolted on. It is a caching problem with a database underneath. Every hard decision, whether to precompute each feed, what to do about the user with ten million followers, how to keep it all in memory, is a week 3 lesson. Today you put them together into one design.

This is the week 3 finale, a design day. No coding lab. You design the home feed for a social app, on paper, against the clock, then measure how differently you think about caching now than you did on Day 15.

---

## Before you start ⏪

Bring all of week 3. Day 15 (cache-aside, the hit-rate math), Day 16 (the working set, why a cache far smaller than the data still wins), Day 17 (the stampede), Day 18 (the celebrity hot key), Day 19 (round trips and why fewer, richer operations win), Day 20 (TTLs and serving stale on purpose). Today pulls on every one.

---

## Words you will meet today 📖

A home feed, or timeline, is the merged, reverse-chronological list of posts from everyone you follow. It is what you see when you open the app.

Fan-out on write, also called push, means doing the work when a post is created: the moment you post, the system copies that post into the precomputed feed of every one of your followers. Reads are then instant.

Fan-out on read, also called pull, means doing the work when a feed is requested: at read time the system gathers recent posts from everyone you follow and merges them. Writes are cheap, reads are expensive.

A feed cache is the precomputed per-user timeline, usually a capped list of recent post ids held in memory (a Redis list per user), so opening the app is one fast read.

Hydration is turning a list of post ids into the full posts, by looking each one up, ideally from a cache (Day 15), not the database.

The hybrid, or fan-out with a celebrity exception, is the real answer: push for normal users, pull for the few accounts with enormous followings.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Design a news feed](https://www.hellointerview.com/learn/system-design/problem-breakdowns/fb-news-feed) from Hello Interview. The exact problem, worked, with the fan-out decision front and centre. Skim before you try, read properly after.
- [Design the Twitter timeline and search](https://github.com/donnemartin/system-design-primer/blob/master/solutions/system_design/twitter/README.md) from the System Design Primer. A second worked take with the back of the envelope numbers for fan-out written out.
- Re-skim your own Day 18 notes on the celebrity hot key. The feed's worst problem is that exact problem, and you already measured it.

Watch, after you have done your own design:
- [News feed system design, fan-out to a million followers](https://www.youtube.com/watch?v=4v3T_bQKz5s) by Kuluru Vineeth, about 32 minutes. A full walkthrough of the push/pull/hybrid decision.
- Optional: [Twitter's timeline journey, from join queries to fan-out to home mixer](https://www.youtube.com/watch?v=dut0HC2RwR0), 19 minutes, for how the real system evolved.

### Push, pull, and why you end up doing both (15 min)

There are two honest ways to build a feed, and they are opposites.

Push, or fan-out on write, does the work when you post. The instant you publish, the system appends your post id to the precomputed feed list of every follower you have. Now when any of them opens the app, their feed is already sitting there in memory: one read, instant. This is wonderful for reads, which is most of what a feed does. The catch is the write. If you have 500 followers, one post is 500 small cache writes, fine. If you have ten million followers, one post is ten million cache writes, and that is the Day 18 celebrity problem wearing a new hat.

Pull, or fan-out on read, does the work when someone opens the app. Nothing happens at post time beyond saving the post. At read time, the system gathers the recent posts of everyone you follow and merges them into a timeline. Writes are now trivial, even for a celebrity. But reads are expensive: following 500 people means merging 500 little timelines every single time you refresh, and reads vastly outnumber posts.

So neither pure approach survives. Push dies on the celebrity's write. Pull dies on everyone's read. The real systems do both: push for normal accounts, so almost everyone gets instant feeds cheaply, and pull for the handful of mega-accounts, so one celebrity post does not trigger ten million writes. When you open the app, your feed is your precomputed push feed, with the few celebrities you follow pulled in and merged at read time. That hybrid is the whole design, and it exists entirely because of the hot-key lesson from Day 18.

### The rest of the feed is also week 3 (10 min)

Once the fan-out decision is made, the other pieces are the days you just did.

The feed cache is the working set from Day 16. You do not keep a hot precomputed feed for all two billion users, only the ones active lately. An inactive user's feed can be dropped and rebuilt when they return, because the hot set is a small fraction of all users and that fraction gets almost all the reads.

Hydration is cache-aside from Day 15. The feed is a list of post ids; turning them into real posts is a batch of lookups that should hit a post cache, not the database. And you fetch them in as few round trips as possible, which is the Day 19 pipelining lesson: one request for a hundred posts, not a hundred requests.

The celebrity post everyone loads at once is the Day 17 stampede and the Day 18 hot key together. That single post is one hot object read by millions, so it lives in cache, gets replicated or absorbed in a local cache, and its recompute is single-flighted so a cache miss does not send millions of reads at the database.

And the images and videos in the feed are Day 20: static, heavy, and served from a CDN with long TTLs, never from your origin on every scroll.

Notice the pattern. You are not inventing anything today. You are assembling six days of caching into one system, and the feed is just the place they all meet.

---

## Block 2: drill (40 min) ✍️

Paper first, with numbers. Write your answers into [`notes/day-21-drills.md`](../notes/day-21-drills.md). About 8 minutes each.

D1. Estimate the scale. 100 million daily users, each posts twice a day, each follows 200 people on average, each opens the feed 10 times a day. Posts per second (and peak at 3x)? Feed reads per second? Under fan-out on write, how many timeline writes per day does the average case cause (posts times average followers)?

D2. Push versus pull on one post. A normal user has 500 followers; a celebrity has 10 million. Under fan-out on write, how many cache writes does one post cause for each? Why does push break for the celebrity, and what do you do about that one account instead?

D3. The hybrid read path. You follow 199 normal people and 1 celebrity. When you open the app, where does each part of your feed come from: the 199, and the 1? Why is the celebrity handled differently?

D4. The feed cache in memory. You keep each active user's feed as a capped list of the last 800 post ids, 8 bytes each. For 100 million active users, how much memory is that? Does it fit across a Redis cluster, and which Day 16 idea lets you store far fewer feeds than you have users?

D5. A celebrity posts and 10 million followers refresh within a few seconds. Which two week 3 problems is this, by name, and what three things keep that one post from taking down the database?

---

## Block 3: build (100 min) 🔧

Today you build a design, not code. The template is [`labs/day-21-news-feed/DESIGN.md`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-21-news-feed/DESIGN.md). Copy it into your fork and fill it in.

Do it against the clock. Give yourself 45 minutes for a first full pass: requirements, scale estimate, the push/pull/hybrid decision, the write path, the read path, the feed cache, and the celebrity and failure cases. Do not open the Solutions or the worked breakdowns until your 45 minutes are up.

Then improve it with the readings open, marking in a different colour what you added. That delta is week 3 landing.

### What a strong feed design has

A weak one says "cache the feed." A strong one estimates the read-to-write ratio and the fan-out cost first, then chooses push for the many and pull for the few, and can say the exact follower count where it flips. It names where the feed cache lives, how big it is, and why it holds far fewer feeds than there are users. And it has a specific answer for the celebrity post that every lesson this week was building toward. Aim for that.

### Deliverable

Your filled-in `DESIGN.md`, and one honest paragraph: which week 3 day did the feed lean on hardest, and where did you have to guess?

---

## Block 4: write (30 min) 📣

Your angle is the reframe: "I used to think a news feed was a database query. It is really a caching problem. Here is why Twitter pushes your friends' posts to you when they write them, but pulls a celebrity's post only when you read, and the follower count where it switches." The push versus pull tradeoff is the whole post.

Example posts are on the [Day 21 posts](../shares/day-21-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it, and look back 📝

Log the three: what you completed, the fan-out write cost you estimated, and one thing you still cannot explain.

Then the week 3 retrospective. Think back to Day 15, when a cache was a dict in front of a slow function. Write down the three things you now know about caching that you did not a week ago. That gap is week 3.

Week 4 is async, queues and the log. So far every request did its work while you waited. Next week you learn to hand the work to someone else and walk away, which is how that celebrity fan-out of ten million writes actually gets done without anyone standing still.

---

## Solutions 🔑

Open these only after your own 45-minute design pass.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. 100 million users times 2 posts is 200 million posts a day, about 2,000 per second, roughly 6,000 at a 3x peak. Feed reads: 100 million times 10 opens is 1 billion a day, about 10,000 per second, roughly 30,000 at peak, so reads outnumber posts around 5 to 1 even before counting that each open shows many posts. Fan-out on write: 200 million posts times 200 average followers is 40 billion timeline writes a day, about 400,000 per second. That number is the whole reason the write path needs care: a post is cheap, but fanning it out to every follower is not.

D2. A normal post is 500 cache writes, nothing. A celebrity post is 10 million cache writes, for one tweet. If that celebrity posts ten times a day, that is 100 million timeline writes from one account, and it arrives in bursts. Push breaks because the write amplification is unbounded in the follower count. So you do not push for that account at all: you leave their posts in their own timeline and pull them in at read time, when their followers actually open the app. One account, handled the opposite way, because of its shape.

D3. The 199 normal people were pushed: their posts were copied into your precomputed feed when they posted, so they are already sitting in your feed cache, read in one shot. The 1 celebrity was not pushed; at read time the system fetches that celebrity's recent posts (one cheap read of their own timeline, cached and hot because millions want it) and merges them into your feed before returning it. The celebrity is different because pushing to their millions of followers at write time is the cost you are avoiding, and pulling their one timeline at read time is cheap and shared across everyone who follows them.

D4. 100 million users times 800 ids times 8 bytes is 640 GB. That fits across a Redis cluster of, say, 15 to 20 nodes, comfortably. And the Day 16 working set is what makes it even easier: you do not need a hot feed for every user who ever signed up, only for users active recently, which is a fraction of the total. Inactive users' feeds are evicted and rebuilt on their next visit, so the memory you actually hold is smaller than the raw number suggests.

D5. This is the thundering herd (Day 17) and the celebrity hot key (Day 18) at the same time: one post, read by ten million people in a few seconds. Three things keep it safe. First, the post lives in cache and is replicated or absorbed in a local in-process cache on each server, so the reads spread instead of hammering one node. Second, its recompute is single-flighted, so a cache miss triggers one database read, not ten million. Third, the media in the post is served from a CDN (Day 20), so the heavy bytes never touch your origin at all. The feed cache means most of those ten million never reach the database in the first place.

</details>

<details markdown="1">
<summary>A worked reference design</summary>

One good answer, not the only one. Yours will differ; what matters is that the numbers and the week 3 lessons drive it.

Requirements. Functional: post, and see a reverse-chronological home feed of posts from everyone you follow. Non-functional: the feed opens fast (it is the thing users do constantly), the system is heavily read-skewed, and it must survive one account having tens of millions of followers.

Scale, from D1: about 2,000 posts per second, about 10,000 feed reads per second, and a fan-out cost of roughly 400,000 timeline writes per second if you push naively. Reads dominate, so the design optimises the read path and pays carefully on writes.

The core decision, from D2 and D3: hybrid fan-out. Push each normal post into followers' precomputed feed caches at write time, so the common read is one fast cache lookup. Do not push for mega-accounts; pull their posts at read time and merge. Pick a follower threshold (tens of thousands, say) above which an account switches from push to pull.

Write path: save the post, then enqueue a fan-out job (this is where week 4's queues come in) that appends the post id to each follower's feed list, skipping accounts above the pull threshold. The post content goes into a post cache.

Read path: read the user's precomputed feed list from the feed cache (Day 16 working set keeps active users hot), pull in recent posts from the few celebrities they follow, merge by time, then hydrate the post ids into full posts from the post cache in as few round trips as possible (Day 15 cache-aside, Day 19 pipelining). Media is served from a CDN (Day 20).

The celebrity and failure cases, from D5: a celebrity's post is one hot object, cached and replicated or locally absorbed, with single-flight recompute so a miss does not stampede the database (Days 17 and 18). The feed cache going cold is the scary case, because the database would suddenly take the full read load, so you warm it carefully and size the database to survive a partial cold cache.

The sentence that makes this sound senior: "feeds are push for the many and pull for the few, because fan-out on write is cheap at 500 followers and ruinous at 10 million, and the follower count is the dial between them."

</details>

<details markdown="1">
<summary>Week 3 in one page</summary>

Seven days, one idea underneath: the fastest, cheapest read is the one that never reaches the database, and a cache is a second copy of the truth that you now have to manage.

Day 15, cache-aside. Check the cache, miss to the source, populate. A hit is orders of magnitude faster than the source, and hit rate is non-linear: 90 to 80 percent roughly doubles database load.

Day 16, eviction and the working set. A cache far smaller than the data still wins, because a few hot keys get most of the reads. LRU keeps the hot set; the hit-rate curve has a knee.

Day 17, the thundering herd. A popular key expires and the whole crowd misses at once. A per-key lock or early recompute turns a flood of source calls back into one.

Day 18, the celebrity hot key. One key gets a huge share of reads and melts the one node it lives on. You cannot shard around it; you replicate it or absorb it locally.

Day 19, round trips. The network, not the server, is usually the wall. Pipelining and rich operations turn many round trips into one, which is why Redis is single-threaded and fast.

Day 20, the CDN. Serve from the edge with TTLs, revalidate cheaply with conditional requests, and serve stale on purpose while refreshing in the background so no user waits.

Day 21, today. All six, assembled into a feed, where push versus pull is really the celebrity hot key, hydration is really cache-aside, and the whole thing is really the working set in memory.

If your feed design estimated the fan-out cost, chose push for the many and pull for the few, and had a specific answer for the celebrity post, you did not learn six caching tricks this week. You learned that caching, past a certain scale, is the architecture. Week 4 teaches you how the expensive work, like that fan-out, gets done without anyone waiting.

</details>
