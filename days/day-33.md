---
title: "Day 33: logical clocks"
parent: "Week 5: distributed systems"
nav_order: 5
has_children: true
---

# Day 33
## How to order events when not one clock can be trusted 🕰️

Today's one idea: on Day 29 you watched two machines disagree about the time and silently corrupt data because of it. Today you get the fix. We stop asking "what time did this happen?" and start asking "did this happen before that?". It turns out you can answer the second question perfectly without any clock at all, just by counting. Lamport timestamps give you one honest number per event and a clean total order. Vector clocks go one better and tell you, for any two events, whether one truly came before the other or whether they were genuinely independent. That second thing, detecting concurrency, is the piece a wall clock can never give you, and it is exactly what keeps a distributed store from eating your writes.

This is the hard week, and today bends the brain a little more than most. Take it slow. The lab is tiny and deterministic on purpose, so you can hold the whole thing in your head and watch the idea click.

---

## Before you start ⏪

Keep Day 29 close. That was the day you accepted that wall clocks on different machines drift, jump backwards when NTP corrects them, and cannot be compared safely. Today is the answer to "so what do we order events with instead?". It also helps to have Day 31 fresh, the Dynamo day, where two copies of a value were allowed to disagree and heal later. The "sibling" conflict you met there is the same thing we detect with vector clocks today, so Part 3 of the lab ties the two days together.

Day 2's comfort with Python is plenty for the lab. There is no database, no network, no threads. Just counting.

---

## Words you will meet today 📖

The happened-before relation, written a to b with an arrow, means a could have influenced b. It holds in exactly three cases: a and b are on the same process and a came first, or a is a send and b is its matching receive, or there is a chain of those linking them. It is the real, clock-free notion of "before".

A partial order is an ordering where some pairs are simply not comparable. Happened-before is a partial order: plenty of event pairs have no arrow either way. Those pairs are the interesting ones.

Concurrent events are a pair with no happened-before arrow in either direction. Neither could have known about the other. Concurrent does not mean "at the same wall-clock instant", it means causally independent.

A Lamport timestamp is a single integer per event. Each process keeps a counter, bumps it on every event, and on receiving a message jumps to max(its own, the message's) plus one. It gives a total order consistent with causality.

A total order puts every pair in some order, even pairs that are really concurrent. Handy for picking a single winner, but it invents orderings that were never real.

A vector clock is a whole array of counters, one slot per process, carried on every message. Comparing two vectors tells you before, after, or concurrent, with no false ordering invented.

A sibling, in Dynamo terms, is one of two concurrent versions of the same key. Vector clocks are how the store notices it has siblings and must reconcile them instead of silently dropping one.

---

## Block 1: read (50 min)

### What to read and watch today 📚

Read these three:
- [Time, Clocks, and the Ordering of Events in a Distributed System](https://lamport.azurewebsites.net/pubs/time-clocks.pdf) by Leslie Lamport, 1978. The paper that started all of this, and a Turing Award sits partly on it. It is short and far more readable than its reputation. The first few pages, up to and including the "happened before" definition, are the whole of today.
- [Martin Kleppmann's distributed systems notes](https://www.cl.cam.ac.uk/teaching/2122/ConcDisSys/dist-sys-notes.pdf), the sections on physical time, causality, and logical time (roughly pages 42 to 54). This is the clearest modern treatment, and the notes pair with the two videos below.
- [Vector Clocks](https://sookocheff.com/post/time/vector-clocks/) by Kevin Sookocheff. A short, concrete walk through the vector clock rules with a worked example. Read it right before the lab.

Watch, they are the perfect warm-up:
- [Distributed Systems 3.3: Causality and happens-before](https://www.youtube.com/watch?v=OKHIdpOAxto) by Martin Kleppmann, about 10 minutes. The happened-before relation, drawn out properly. Watch this first.
- [Distributed Systems 4.1: Logical time](https://www.youtube.com/watch?v=x-D8iFU1d-o) by Martin Kleppmann, about 14 minutes. Lamport clocks and vector clocks, back to back. This is today in one sitting.

### Why a wall clock cannot order your events (14 min)

Picture a big family WhatsApp group. Someone posts "reached the station", and a minute later someone else posts "come fast, train is here". You know the second message came after the first, not because you trust everyone's phone clock, but because the content follows: the second is a reply to the first. Now picture two cousins, one in Delhi and one in Chennai, both posting "booked!" in the same second about two completely different things. Their phone clocks might say 10:00:00.3 and 09:59:58.9. Which came first? The question has no useful answer. They did not influence each other. They are concurrent.

That is the whole mindset shift. On Day 29 you saw that machine clocks drift and jump, so comparing two timestamps from two machines is a coin toss dressed up as a fact. Lamport's move in 1978 was to stop trying. Instead of "when", he defined a clean relation called happened-before, written with an arrow. a to b holds in exactly three situations. First, a and b happen on the same process and a comes first in that process's own order. Second, a is the sending of a message and b is the receiving of that same message, so obviously the send came first. Third, transitivity: if a to b and b to c, then a to c.

Everything that is not linked by such a chain is concurrent. And here is the key point for the whole day: happened-before is a partial order, not a total one. Many pairs of events have no arrow between them in either direction. A wall clock would happily slap an order on those pairs anyway, and that order would be fiction. Our job today is to track the real relation with counters, and to know when we are inventing order that was never there.

### Lamport timestamps: one honest number, one blind spot (18 min)

Lamport's clock is almost insultingly simple, and that is the beauty of it. Each process keeps a single integer counter, starting at zero. Three rules:

Before any event (internal step, or sending a message), the process adds one to its counter, and that new value is the event's timestamp. When a process sends a message, it attaches its current counter value to the message. When a process receives a message, it sets its counter to the maximum of its own value and the value riding on the message, and then adds one. That "max then plus one" is the entire trick. It means a receiver can never look earlier than the sender it just heard from.

Out of those three rules falls a lovely guarantee. If a really happened before b, then Lamport(a) is strictly less than Lamport(b). A reply always carries a bigger number than the message it answers, across any number of machines, with nobody's wall clock involved. That is enough to build a single consistent total order of all events in a distributed system, which is genuinely useful: it is how you can make every node agree on "process these requests in this one order" without a shared clock.

Now the catch, and it is the thing to really feel today. The guarantee runs one way only. Lamport(a) less than Lamport(b) does not mean a happened before b. The two events might be completely concurrent, and Lamport will still hand you two different numbers and imply one came first. In the lab you will see it put a confident strict order on 11 pairs of events that never spoke to each other. The total order is real and consistent, but it is partly made up. Lamport simply cannot see concurrency. Ask it "did a influence b, or were they independent?" and it shrugs. For a lot of jobs that is fine. For detecting conflicting writes, it is a disaster, because it will cheerfully tell you one write came "after" another when in truth they were simultaneous and both matter.

### Vector clocks: now you can actually see concurrency (16 min)

Vector clocks fix the blind spot by keeping more state. Instead of one integer, each process keeps a whole vector of integers, one slot per process in the system. Think of it as "here is my best knowledge of how many events every process has done". The rules rhyme with Lamport's. On a local event, a process bumps only its own slot. When it sends, it attaches the whole vector. When it receives, it takes the elementwise maximum of its own vector and the one on the message (learning the sender's knowledge), then bumps its own slot by one.

The payoff is in the comparison. Take two events with vectors V and W. If V is less than or equal to W in every single slot, then V happened before W. If it is greater than or equal in every slot, W happened before V. And if neither dominates, if V is ahead in some slot while W is ahead in another, then the two events are concurrent, provably, with no guessing. That is the thing Lamport could not do. In the lab you will classify all 45 pairs of events purely from their vectors and watch the answer match the true causal relation on every single pair.

Why does this matter beyond being elegant? Because a pair of concurrent writes to the same key is exactly the Dynamo sibling you met on Day 31. When two clients both update a shopping cart without seeing each other's write, their vector clocks come out concurrent. A system that tracks vector clocks notices this and keeps both versions, so it can reconcile them later (for a cart, take the union, so nothing falls out). A system that trusts a wall clock just compares two timestamps, keeps the bigger one, and throws the other write away. No error, no log line, no page. Your item is simply gone. Part 3 of the lab puts these two side by side and counts the damage.

There is a cost, and you should know it. A vector clock grows with the number of processes, so in a thousand node cluster each clock is a thousand numbers riding on every message. Real systems trim this hard: Dynamo attaches a version entry per coordinator rather than per client and prunes old ones, and newer designs use dotted version vectors. The idea is exactly today's. The engineering is in keeping it small.

---

## Block 2: drill (40 min) ✍️

Paper first, honestly, this is a day where drawing the little message diagrams by hand is what makes it stick. Then copy your answers into [`notes/day-33-drills.md`](../notes/day-33-drills.md).

D1. State the one-way guarantee of Lamport timestamps precisely: what does a happened-before b tell you about their stamps? Then give a concrete two-process example where Lamport(a) is less than Lamport(b) but a and b are actually concurrent. Why can Lamport never rule this out?

D2. Two processes, P and Q. P does p1 (internal), then p2 (sends m1 to Q), then later p3 (receives m2 from Q). Q does q1 (internal), then q2 (receives m1), then q3 (sends m2). Compute the Lamport timestamp of every event, showing the max-plus-one step at each receive.

D3. Same scenario as D2. Now compute the vector clock of every event as [P, Q]. Then use the vectors to classify two pairs: p2 versus q1, and p2 versus q2. Which is concurrent and which is ordered, and how do the vectors tell you?

D4. A cluster has N nodes, each carrying a vector clock. How many integers is each clock, and what happens to that cost as N grows into the thousands? Name one real technique a production system uses to keep vector clocks from blowing up.

D5. Two clients both read the same cart (version with vector clock [1,0,0]) and, without seeing each other, each add one item and write back. Write down the two resulting vector clocks and show they are concurrent. What does a Dynamo-style store do with them, and what would a last-write-wins store using wall-clock timestamps do instead? Which one loses data?

---

## Block 3: build (100 min) 🔧

Today's lab is [`labs/day-33-logical-clocks/vector_clocks.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-33-logical-clocks/vector_clocks.py).

It is a deterministic simulation of three processes passing three messages, ten events in all. No clock, no network, no randomness, so it prints the same numbers for you as it does for me. Part 1 assigns Lamport timestamps and shows you both the guarantee that holds and the 11 pairs it mis-orders. Part 2 assigns vector clocks and classifies all 45 event pairs as ordered or concurrent, matching the true causal relation exactly. Part 3 replays four writes to one shopping cart and pits vector clocks against last-write-wins, counting the items each approach keeps.

Standard library only, and it finishes in well under a second.

### Predict first

Fill in `PREDICTIONS` at the top before you run anything. The run refuses to start until you do.

- P1. Ten events give 45 unordered pairs in total. How many of those are causally ordered (one truly happened before the other)?
- P2. The headline. How many pairs are genuinely concurrent? This is the number vector clocks recover and Lamport throws away.
- P3. Of the concurrent pairs, how many does Lamport mis-order with a strict less-than, pretending one came first?
- P4. In the cart run, how many concurrent write conflicts (siblings) do vector clocks flag?

P2 is the one to sit with. Draw the three processes, draw the three message arrows, and try to spot the independent pairs by eye before the code tells you.

### Fill in the TODOs

1. TODO 1 is the Lamport receive rule, max of the two clocks plus one. The one line that keeps a receiver from ever looking earlier than its sender.
2. TODO 2 is the vector clock local step: bump only your own slot. A local event is nobody else's business.
3. TODO 3 is the vector clock receive rule: elementwise max to absorb the sender's knowledge, then bump your own slot. This is the heart of the whole idea.
4. TODO 4 is the comparison: decide before, after, equal, or concurrent from two vectors. This is the thing Lamport could not do, so it is the thing the whole day is about.

```bash
cd labs/day-33-logical-clocks
python3 vector_clocks.py
```

### What you're going to discover

Part 1 is the quiet trap. Lamport's guarantee really does hold: on all 31 ordered pairs, the earlier event has the smaller stamp, every time. It feels airtight. Then you look at the concurrent pairs and find Lamport has slapped a confident "less than" on 11 of them, ordering events that never influenced each other, plus 3 more it leaves as ties it cannot break. The total order is consistent and it is also partly fiction.

Part 2 is the relief. The same ten events, now with vectors, and suddenly every pair is classified correctly: 31 ordered, 14 concurrent, matching the ground truth on all 45. Read one off by hand, like a3 = [3,0,0] against b2 = [2,2,0], and you can see with your own eyes why neither dominates and so neither could have known about the other.

Part 3 is the gut punch. Four writes to one cart. Vector clocks flag 2 concurrent conflicts, keep every live sibling, and the cart reconciles to all 4 items with nothing lost. Last-write-wins, trusting a skewed wall clock, keeps the single write with the biggest timestamp and silently drops 3 items. Same writes, same order, and one approach quietly loses three quarters of your cart.

### Traps ⚠️

- On a receive, the order is elementwise max first, then bump your own slot. If you bump first and then max, you can get the wrong vector. Do the max, then the plus one.
- Comparison is not "is V bigger overall". It is per slot. V is before W only if it is less-than-or-equal in every slot. The moment one slot goes the other way, they are concurrent. That single rule is the whole point of vector clocks.
- Do not read Lamport's guarantee backwards. a to b implies smaller stamp, yes. Smaller stamp does not imply a to b. The lab prints 11 counterexamples so you cannot talk yourself out of it.
- Concurrent does not mean "same wall-clock time". c1 and a2 in the run are concurrent because no message links them, not because they happened at the same instant. Causality, not clocks.

### Deliverable

[`labs/day-33-logical-clocks/RESULTS.md`](../labs/day-33-logical-clocks/RESULTS.md) has a skeleton. Paste the output and answer the one question that matters: how many event pairs were genuinely concurrent, and why could Lamport not flag them while vector clocks could?

---

## Block 4: write (30 min) 📣

Your angle today is the quiet data loss. "Two people edited the same cart at the same moment. One system kept both items and merged them. The other threw one away and never told anyone. The difference is whether you track causality with a vector clock or trust a wall clock that lies." The Part 3 scoreboard, 4 items kept versus 1, is your screenshot.

Example posts are on the [Day 33 posts](../shares/day-33-posts.md) page. Write yours in your own voice. Drafts go in `shares/`.

---

## End of day: log it 📝

Log the three: what you completed, the number of genuinely concurrent pairs you measured, and one thing you still cannot explain. If your head hurts, that is the week working as intended, not you failing it.

Day 34 is paper day, the one where it all clicks. You read Dynamo properly, skim Bigtable and Spanner, and write a plain-language page on each. Today you built the tool that detects the conflicts Dynamo is designed around, so tomorrow the paper will read like a description of something you already understand.

---

## Solutions 🔑

Open these only after you've done the day.

<details markdown="1">
<summary>Drill answers, D1 to D5</summary>

D1. The guarantee is one-directional: if a happened before b, then Lamport(a) is strictly less than Lamport(b). The converse fails. Take two processes P and Q that never exchange a message before these events: P's first event p1 has stamp 1, and Q's first event q1 also has stamp 1, and if Q then does q2 it has stamp 2. Now Lamport(p1) = 1 is less than Lamport(q2) = 2, yet p1 and q2 are concurrent, since no chain of program-order or message edges links them. Lamport can never rule this out because a single integer cannot record which process's knowledge it reflects. Two events can reach the same or ordered numbers by coincidence of counting, with no causal link between them.

D2. Walk it event by event, tracking each process's counter.
- p1 (internal on P): P goes 0 to 1. p1 = 1.
- p2 (send m1, carries stamp 2): P goes 1 to 2. p2 = 2.
- q1 (internal on Q): Q goes 0 to 1. q1 = 1.
- q2 (receive m1, message carried 2): Q takes max(1, 2) + 1 = 3. q2 = 3.
- q3 (send m2, carries stamp 4): Q goes 3 to 4. q3 = 4.
- p3 (receive m2, message carried 4): P takes max(2, 4) + 1 = 5. p3 = 5.
So p1=1, p2=2, p3=5, q1=1, q2=3, q3=4.

D3. Vectors as [P, Q], same walk.
- p1 = [1,0]. p2 = [2,0] (and m1 carries [2,0]).
- q1 = [0,1]. q2 receives m1: max([0,1],[2,0]) = [2,1], then bump Q to [2,2]. q2 = [2,2].
- q3 sends m2: bump Q, [2,3], carries [2,3].
- p3 receives m2: max([2,0],[2,3]) = [2,3], then bump P to [3,3]. p3 = [3,3].
Now classify. p2 = [2,0] versus q1 = [0,1]: p2 is ahead in slot P (2 > 0), q1 is ahead in slot Q (1 > 0), neither dominates, so they are concurrent. p2 = [2,0] versus q2 = [2,2]: p2 is less-than-or-equal in every slot (2 ≤ 2, 0 ≤ 2) and strictly smaller in one, so p2 happened before q2. That matches the causal story, p2 is the send and q2 is its receive.

D4. Each clock is N integers, one slot per node. The cost rides on every message and every stored version, so at N in the thousands you are attaching a thousand-number array to traffic that might otherwise be a few bytes, and comparison gets linear in N too. Production systems keep it small in a few ways. Dynamo attaches a version entry per coordinator node that handled the write, not per client, and prunes the oldest entries past a cap. Dotted version vectors are a tighter encoding that avoids false conflicts while staying compact. The pragmatic answer in many systems is to keep the number of "writers" that share a clock deliberately small.

D5. Client one writes and gets vector [2,0,0] (it bumped its own slot from the base [1,0,0]); client two, not having seen client one, also starts from [1,0,0] and its write lands as [1,1,0]. Compare [2,0,0] and [1,1,0]: the first is ahead in slot 0, the second is ahead in slot 1, neither dominates, so they are concurrent. A Dynamo-style store sees this and keeps both as siblings, then reconciles on the next read (for a cart, union the items, so both survive). A last-write-wins store compares wall-clock timestamps and keeps whichever write had the larger one, dropping the other write and its item silently. Last-write-wins loses data, and because clocks are skewed (Day 29) it can even keep the write that truly happened earlier.

</details>

<details markdown="1">
<summary>Lab solution: the four TODOs</summary>

The full working file is [`labs/day-33-logical-clocks/solution.py`](https://github.com/anurag629/system-design-60-days/blob/main/labs/day-33-logical-clocks/solution.py).

TODO 1, the Lamport receive rule. Never look earlier than the sender, then step once more:

```python
return max(local, received) + 1
```

TODO 2, the vector clock local step. A local event advances only your own slot:

```python
out[pid] += 1
```

TODO 3, the vector clock receive rule. Absorb the sender's knowledge with an elementwise max, then step your own slot:

```python
merged = [max(a, b) for a, b in zip(local_vc, msg_vc)]
merged[pid] += 1
return merged
```

TODO 4, the comparison. One vector dominates another only if it is greater-or-equal in every slot. If neither dominates, they are concurrent:

```python
le = all(x <= y for x, y in zip(a, b))
ge = all(x >= y for x, y in zip(a, b))
if le and ge:
    return "equal"
if le:
    return "before"
if ge:
    return "after"
return "concurrent"
```

</details>

<details markdown="1">
<summary>Reference run, and what each number means</summary>

Apple Silicon laptop, macOS, Python 3.10. The simulation is deterministic, so your numbers should match these exactly.

```
==============================================================================
Part 1: Lamport timestamps. One counter per process.
==============================================================================
  Event Lamport stamps (one integer each):
    a1=1  a2=2  a3=3  c1=1  b1=3  b2=4  b3=5  c2=5  c3=6  a4=7  

  The good news. For every pair where a really happened before b,
  we check that Lamport(a) < Lamport(b). Holds on all 31 ordered pairs: True.
  So Lamport stamps never contradict real causality. A reply always
  outranks the message it answers. That alone is enough to build a
  single consistent total order out of a distributed mess.

  The catch. Lamport(a) < Lamport(b) does NOT mean a happened before b.
  Of the concurrent pairs, Lamport puts a strict order on 11 of
  them anyway, inventing a 'first' between events that never spoke:
    c1(L=1) < a2(L=2)   but c1 and a2 are concurrent
    c1(L=1) < a3(L=3)   but c1 and a3 are concurrent
    a3(L=3) < b2(L=4)   but a3 and b2 are concurrent
    a3(L=3) < b3(L=5)   but a3 and b3 are concurrent
    a3(L=3) < c2(L=5)   but a3 and c2 are concurrent
    a3(L=3) < c3(L=6)   but a3 and c3 are concurrent
    c1(L=1) < b1(L=3)   but c1 and b1 are concurrent
    c1(L=1) < b2(L=4)   but c1 and b2 are concurrent
    c1(L=1) < b3(L=5)   but c1 and b3 are concurrent
    b3(L=5) < c3(L=6)   but b3 and c3 are concurrent
    b3(L=5) < a4(L=7)   but b3 and a4 are concurrent
  Another 3 come out as ties Lamport cannot separate: a1~c1, a3~b1, b3~c2.
  A total order is handy, but Lamport has quietly lied about who
  influenced whom. It cannot see concurrency. That is the gap.

==============================================================================
Part 2: vector clocks. One counter per process, carried by everyone.
==============================================================================
  Event vector clocks [P0, P1, P2]:
    a1 = [1, 0, 0]
    a2 = [2, 0, 0]
    a3 = [3, 0, 0]
    c1 = [0, 0, 1]
    b1 = [2, 1, 0]
    b2 = [2, 2, 0]
    b3 = [2, 3, 0]
    c2 = [2, 2, 2]
    c3 = [2, 2, 3]
    a4 = [4, 2, 3]

  Vector clocks classify all 45 pairs. They match the
  ground-truth causal relation on every single pair: True.

  Ordered pairs (one happened before the other): 31
  Concurrent pairs (neither did):                 14
  These are the concurrent pairs, each one invisible to Lamport:
    a1|c1, a2|c1, a3|c1, a3|b1, a3|b2, a3|b3, a3|c2, a3|c3, c1|b1, c1|b2, c1|b3, b3|c2, b3|c3, b3|a4

  Read one off to feel it. a3 = [3,0,0] and b2 = [2,2,0]. a3 is ahead
  on P0 (3 > 2), b2 is ahead on P1 (2 > 0). Neither vector dominates,
  so neither event could have known about the other. Concurrent, and
  the vectors prove it. Lamport had them as 3 < 4 and called it order.

==============================================================================
Part 3: why it matters. Concurrent writes are Dynamo siblings.
==============================================================================
  Key cart:42, written by three clients with SKEWED wall clocks.
  Vector clocks decide, for each new write, whether it supersedes what
  is stored or conflicts with it (a concurrent sibling kept alongside).

  write A  {milk} supersedes the stored version(s)
  write B  {eggs} is CONCURRENT with [A] -> keep both as siblings
  write C  {bread,eggs,milk} supersedes the stored version(s)
  write A2 {butter,milk} is CONCURRENT with [C] -> keep both as siblings

  Vector clocks flagged 2 concurrent conflict(s). The cart keeps every
  live sibling, so a read reconciles to their union: ['bread', 'butter', 'eggs', 'milk']
  Items preserved: 4. Nothing lost.

  Last-write-wins (trust the wall clock) instead:
    highest timestamp is client B at t=500, so the cart becomes
    just ['eggs']. Silently lost: ['bread', 'butter', 'milk'].
  Same writes, same order. Vector clocks keep 4 items, the wall
  clock keeps 1 and drops 3 with nobody the wiser.

==============================================================================
Scoreboard
==============================================================================
  P1 ordered pairs                   you =   30   actual =     31        close enough
  P2 concurrent pairs (the number)   you =   12   actual =     14        close enough
  P3 Lamport mis-orderings           you =   10   actual =     11        close enough
  P4 Dynamo sibling conflicts        you =    2   actual =      2        close enough

==============================================================================
The number to carry
==============================================================================
  Of 45 event pairs, 14 are genuinely concurrent: neither event
  influenced the other. Vector clocks flag every one of them, because
  neither vector dominates. Lamport timestamps cannot, they hand back a
  tidy total order and mis-order 11 of those pairs as if one came first.
  That gap is not academic. A concurrent pair writing the same key is a
  Dynamo sibling. Vector clocks see the conflict and keep both versions.
  A wall clock picks the bigger timestamp and loses your data in silence.
```

The shape of the day is Part 1 giving you false confidence and Part 2 taking it away in the best possible way. Lamport's total order is real and it never contradicts causality, which is exactly why it is so easy to trust too much. The moment you ask it about concurrency it falls silent, and it quietly ordered 11 pairs that had no business being ordered. Vector clocks pay for more state, one counter per process on every message, and in return they answer the question Lamport dodges: for all 45 pairs, before, after, or concurrent, matching the truth every time.

Part 3 is why any of this earns its keep. Fourteen concurrent pairs in a toy run sounds academic until one of those pairs is two writes to the same shopping cart. Vector clocks see the conflict and keep both items. The wall clock compares two timestamps, keeps one, and drops three items without a single error. That is the Day 29 bug and the Day 31 sibling in one picture, and the fix is counting, not clocks.

</details>
