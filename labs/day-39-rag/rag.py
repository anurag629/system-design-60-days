"""
Day 39 lab: RAG in pure Python, and the thing nobody demos. The generation step
is a stub. The lesson is that RAG lives or dies on RETRIEVAL, so this whole lab
measures retrieval quality and nothing else.

Run it:      python3 rag.py

First fill in PREDICTIONS below (your guess is the point, so make it before you
run anything). Then fill in the four numbered TODOs. If you get stuck, the full
working version is solution.py in this folder.

Standard library only. No model, no API, no network, no numpy. Everything is a
tiny deterministic TF-IDF retriever over a small corpus of animal facts. There
is no randomness at all, so the run is reproducible to the digit.

The pipeline, the same four steps every RAG system runs at retrieval time:
  1. chunk the corpus into pieces,
  2. turn each chunk into a TF-IDF vector (term frequency times inverse document
     frequency, so rare words count and common words fade),
  3. turn the query into a vector the same way,
  4. rank chunks by cosine similarity and keep the best few above a threshold.

We measure recall@k: for a set of test questions, each with a known answer
sentence sitting somewhere in the corpus, did the chunk holding that answer make
the retrieved shortlist? If it did not, generation never had a chance, no matter
how clever the model.

The big ideas, which you will watch happen:
  - Chunk size is a real tuning knob. Too SMALL and the answer is split across
    chunks, so no single chunk carries enough of it. Too LARGE and the answer is
    diluted among unrelated text, so its similarity drops below the threshold.
    Recall peaks in the middle and falls off both ends. An inverted U.
  - TF-IDF matches WORDS, not MEANING. Ask with synonyms the document does not
    use (swift instead of fast, beast instead of animal) and recall collapses,
    because a word the corpus never saw has nothing to match. This is exactly the
    gap semantic embeddings (Day 38) are built to close, and why rerankers exist.
  - So most "RAG is bad" is really "retrieval is bad". The model is downstream of
    a ranked list it did not choose.
"""

import math
import sys
from collections import Counter

PREDICTIONS = {
    # P1: at a sensible chunk size, over the 10 test questions whose wording
    #     matches the documents, what percent land the answer chunk in the
    #     retrieved shortlist (top 3 above the threshold)?
    "good_recall_pct": None,

    # P2: re-chunk far too LARGE (answer diluted among unrelated text, so its
    #     similarity drops below the threshold). Recall over the same questions.
    "large_recall_pct": None,

    # P3: re-chunk far too SMALL (answer split across chunks, so no one chunk is
    #     similar enough). Recall over the same questions.
    "small_recall_pct": None,

    # P4: keep the good chunk size, but ask the SAME 10 questions reworded with
    #     synonyms the documents never use. Recall over the same questions.
    "synonym_recall_pct": None,
}

K = 3                 # retrieve at most the top K chunks
TAU = 0.30            # relevance threshold: a match below this cosine is noise,
                      # so the retriever throws it away. Real vector search does
                      # exactly this, a minimum score, not a blind top K.
SMALL_CHUNK = 6       # words per chunk, far too small
GOOD_CHUNK = 28       # words per chunk, a sensible size
LARGE_CHUNK = 200     # words per chunk, far too large
SWEEP = [3, 6, 12, 20, 28, 40, 60, 90, 140, 200]

# A short stop list. Real TF-IDF drops these so common glue words do not drown
# out the words that carry meaning. Nothing security-sensitive, just noise.
STOP = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "for",
    "by", "with", "from", "as", "is", "are", "was", "were", "be", "been", "it",
    "its", "this", "that", "these", "those", "their", "they", "them", "there",
    "he", "she", "his", "her", "him", "i", "you", "we", "us", "our", "your",
    "which", "what", "who", "when", "where", "why", "how", "does", "do", "did",
    "has", "have", "had", "can", "could", "will", "would", "should", "may",
    "not", "no", "than", "then", "up", "out", "into", "each", "some", "any",
    "all", "many", "most", "more", "single", "very", "just", "so", "also",
    "about", "other", "only", "one", "two", "three",
}


# ---------------------------------------------------------------------------
# The corpus: 16 short animal facts. The documents share a lot of vocabulary
# (large, lives, eats, hunts, water, young), which is what makes retrieval a
# real contest rather than a lookup.
# ---------------------------------------------------------------------------

CORPUS = [
    "The African elephant is the largest land animal alive today. An adult bull "
    "can weigh over six thousand kilograms. Elephants live in family herds led by "
    "the oldest female, called the matriarch. They eat grass, leaves, bark, and "
    "fruit for many hours each day. An elephant uses its long trunk to drink water "
    "and to pick up food. Elephants can live for about seventy years in the wild.",

    "The lion is a large cat that lives in the grasslands of Africa. A group of "
    "lions living together is called a pride. Male lions grow a thick mane of hair "
    "around the head. Lions hunt zebra, antelope, and other animals, and the "
    "females do most of the hunting. A lion can sleep for up to twenty hours in a "
    "day. Lions roar to warn other prides to stay away from their territory.",

    "The blue whale is the largest animal that has ever lived on Earth. It can grow "
    "longer than thirty meters and weigh more than one hundred thousand kilograms. "
    "The blue whale eats tiny shrimp-like creatures called krill, swallowing "
    "millions of them each day. It swims across great distances to feed and breed. "
    "Its call is louder than a jet engine and travels for kilometers underwater.",

    "Penguins are birds that cannot fly, but they swim very well using their stiff "
    "flippers. Most penguins live in the cold southern half of the world. They eat "
    "fish, squid, and krill caught in the ocean. A thick layer of fat and tightly "
    "packed feathers keep the penguin warm in freezing water. Emperor penguin "
    "fathers hold the egg on their feet and keep it warm through the long winter.",

    "The kangaroo is a marsupial that lives in Australia and carries its young in a "
    "pouch. A baby kangaroo is called a joey and stays in the pouch for months "
    "after birth. Kangaroos move by hopping on their strong back legs and cover "
    "large distances quickly. They eat grass and other plants in the early morning "
    "and evening. Kangaroos use their thick tail for balance while hopping.",

    "The cheetah is the fastest land animal, able to run at great speed over short "
    "distances. It can reach speeds over one hundred kilometers per hour in a few "
    "seconds. The cheetah hunts in the daytime, chasing gazelle on the open plains "
    "of Africa. Its slim body, long legs, and flexible spine are built for the "
    "chase. A cheetah cannot roar like a lion, but it can purr like a house cat.",

    "The octopus is a sea animal with a soft body and eight long arms covered in "
    "suckers. It has three hearts and blue blood, and it can change the color of "
    "its skin to hide from danger. The octopus is clever and can open jars and "
    "escape through tiny gaps. It eats crabs and small fish, using a hard beak to "
    "break open shells. When threatened, the octopus squirts a cloud of dark ink.",

    "The eagle is a large bird of prey with powerful wings and very sharp eyesight. "
    "It can spot a small animal on the ground from high in the sky. Eagles build "
    "huge nests on tall cliffs and trees and use them for years. They hunt fish and "
    "rabbits, catching them with strong curved claws called talons. Eagles can "
    "glide for hours on rising warm air without flapping their wings.",

    "The honey bee lives in a large colony with a queen, thousands of workers, and "
    "some males called drones. Worker bees gather nectar from flowers and turn it "
    "into honey stored inside the hive. As a bee moves from flower to flower it "
    "spreads pollen. A worker bee tells the others where to find flowers by "
    "performing a special waggle dance. A worker bee dies after it stings.",

    "The polar bear is a large white bear that lives on the sea ice of the Arctic. "
    "It hunts seals, waiting beside holes in the ice for a seal to come up for air. "
    "A thick layer of fat and dense fur keep the polar bear warm in the cold. Its "
    "white coat helps it blend into the snow while hunting. A mother polar bear "
    "digs a den in the snow where she gives birth to her cubs in winter.",

    "The crocodile is a large reptile that lives in rivers, lakes, and swamps in "
    "warm parts of the world. It has a long snout full of sharp teeth and a "
    "powerful tail. The crocodile lies still at the surface and waits to ambush "
    "animals that come to drink. A female crocodile guards her eggs and carries the "
    "newly hatched young to the water in her mouth.",

    "The bat is the only mammal that can truly fly, using wings made of thin skin "
    "stretched over long finger bones. Most bats are active at night and rest "
    "upside down during the day. Many bats find their way and catch insects in the "
    "dark by making high sounds and listening for the echo. Some bats feed on fruit "
    "and help spread the seeds of many plants.",

    "The great white shark is a large fish that lives in the open ocean. It has "
    "rows of sharp teeth that are replaced throughout its life. The shark can sense "
    "a few drops of blood in the water from far away. It hunts seals and fish near "
    "the surface. Unlike most fish, the shark must keep swimming to push water over "
    "its gills and breathe.",

    "The owl is a bird of prey that hunts mostly at night. It can turn its head "
    "almost the whole way around to look behind itself. Soft feathers let the owl "
    "fly silently so that its prey does not hear it coming. It catches mice with "
    "sharp claws. The owl has large eyes that gather light and give it keen vision "
    "in the dark.",

    "The dolphin is a clever sea mammal that lives in groups called pods. It "
    "breathes air through a blowhole on the top of its head. Dolphins find fish by "
    "sending out clicks and listening for the signals that bounce back. They often "
    "leap out of the water and play in the waves. A dolphin sleeps with only half "
    "of its brain at a time so it can keep coming up to breathe.",

    "The camel is a large animal that lives in hot, dry deserts. It stores fat in "
    "its hump, which lets it go for days without food or water. Wide feet keep the "
    "camel from sinking into the soft desert sand. Long eyelashes and closable "
    "nostrils protect it from blowing sand. People in desert lands have used camels "
    "to carry heavy loads for thousands of years.",

    # More short animal facts. These share the same everyday vocabulary (large,
    # lives, eats, hunts, water, young, warm) as the entries above. They do not
    # hold any test answer; they are there so that at a large chunk size there are
    # many chunks competing for the query's common words. That competition is what
    # makes a too-large chunk lose: a diluted answer chunk has real rivals.
    "The giraffe is the tallest animal in the world and lives on the grasslands of "
    "Africa. It uses its very long neck to reach leaves high in the trees that "
    "other animals cannot eat.",
    "The tiger is a large cat that lives in the forests of Asia and hunts alone at "
    "night. Its orange coat with black stripes helps it hide among the tall grass "
    "while it waits for prey.",
    "The wolf hunts in a group called a pack and can travel long distances in a "
    "day. Wolves live in forests and cold northern lands and talk to each other by "
    "howling.",
    "The gorilla is a large ape that lives in the forests of central Africa. It "
    "eats mostly leaves and stems and lives in a family group led by a big male "
    "called a silverback.",
    "The hippopotamus is a large animal that spends its days in rivers and lakes to "
    "keep its skin cool. It comes out at night to eat grass on the land near the "
    "water.",
    "The rhinoceros is a heavy animal with thick grey skin and one or two horns on "
    "its nose. It eats grass and leaves and lives on the plains and in the forests "
    "of Africa and Asia.",
    "The zebra is a wild horse with black and white stripes that lives in large "
    "herds on the African plains. The stripes make it hard for a hunting lion to "
    "pick out one animal.",
    "The giant panda lives in the mountain forests of China and eats almost nothing "
    "but bamboo. It spends many hours each day feeding because bamboo gives it so "
    "little energy.",
    "The koala lives in the trees of Australia and eats the leaves of the "
    "eucalyptus. It sleeps for most of the day and carries its young in a pouch "
    "like a kangaroo.",
    "The red fox is a small clever hunter that lives in forests, fields, and even "
    "cities. It eats mice, birds, fruit, and whatever food it can find at night.",
    "The brown bear is a large animal that eats fish, berries, and plants. It "
    "sleeps through the cold winter in a den and comes out hungry in the spring.",
    "The raccoon is a small animal with a black mask of fur around its eyes. It "
    "comes out at night and uses its clever front paws to open bins and find food.",
    "The deer is a gentle animal that eats grass and leaves in forests and fields. "
    "The males grow branching antlers each year and lose them again in the winter.",
    "The rabbit is a small animal with long ears and strong back legs for hopping. "
    "It lives in a burrow in the ground and eats grass and other plants.",
    "The squirrel lives in trees and eats nuts and seeds. It buries food in the "
    "ground in the autumn and digs it up again during the cold winter.",
    "The frog is a small animal that lives near ponds and streams and starts life "
    "as a tadpole in the water. It catches insects with its long sticky tongue.",
    "The sea turtle swims across whole oceans and comes back to the same beach to "
    "lay its eggs in the warm sand. It can live for many tens of years.",
    "The jellyfish drifts in the ocean with the current and has a soft body and no "
    "bones at all. Long trailing arms carry a sting it uses to catch small fish.",
    "The seahorse is a tiny fish that swims upright and holds onto seaweed with its "
    "curling tail. The father seahorse carries the eggs in a pouch until they "
    "hatch.",
    "The salmon is a fish that is born in rivers, swims out to the sea to grow, and "
    "then fights its way back upriver to lay its eggs where it began.",
    "The ostrich is the largest bird in the world and cannot fly, but it can run "
    "very fast across the dry African plains on its strong legs.",
    "The parrot is a colorful bird of warm forests that can copy sounds and even "
    "human words. It uses its strong curved beak to crack open hard nuts and seeds.",
    "The hummingbird is a tiny bird that can hover in the air and even fly "
    "backwards. It beats its wings so fast they hum, and it feeds on the sweet "
    "nectar of flowers.",
    "The flamingo is a tall pink bird that wades in shallow water on long thin "
    "legs. Its color comes from the tiny shrimp and other small creatures it eats.",
    "The woodpecker is a bird that hammers its strong beak into tree bark to find "
    "insects. Its stiff tail props it up against the trunk while it works.",
    "The swan is a large white water bird with a long graceful neck. It glides "
    "across lakes and rivers and defends its young fiercely from any danger.",
    "The ant lives in a huge colony in the ground and each one has a job to do. "
    "Together they carry food many times their own weight back to the nest.",
    "The butterfly begins life as a caterpillar, wraps itself in a case, and comes "
    "out with wide colorful wings. It feeds on the nectar of flowers through a long "
    "tube.",
    "The spider spins a web of silk to trap insects for food. It has eight legs and "
    "most spiders have a bite they use to hold their prey still.",
    "The snake is a long reptile with no legs that moves by sliding over the "
    "ground. Some snakes squeeze their prey and others have a bite full of venom.",
    "The turtle carries a hard shell on its back and can pull its head and legs "
    "inside to hide from danger. It moves slowly on land and can live a very long "
    "time.",
    "The earthworm lives in the soil and eats dead leaves and bits of plant. As it "
    "tunnels it mixes the earth and helps plants grow.",
    "The snail carries a spiral shell on its back and moves slowly on a trail of "
    "slime. It eats leaves and comes out mostly in the damp cool of the night.",
    "The horse is a large animal that people have kept for thousands of years to "
    "ride and to pull heavy loads. It eats grass and hay and can sleep standing up.",
    "The cow is a large farm animal that eats grass and gives milk. It has a "
    "special stomach that lets it bring food back up and chew it again.",
    "The pig is a clever farm animal that eats almost anything. It cannot sweat, so "
    "it rolls in cool mud to keep from getting too hot in the sun.",
    "The sheep is a farm animal kept for its thick wool and its meat. It lives in a "
    "flock and follows the others closely wherever they go.",
    "The goat is a hardy farm animal that can climb steep rocky hills. It eats "
    "grass, leaves, and almost any plant it can reach.",
    "The chicken is a farm bird kept for its eggs and its meat. It cannot fly far, "
    "and it scratches at the ground all day looking for seeds and insects.",
    "The duck is a water bird with webbed feet for paddling and feathers that keep "
    "the water out. It dips its head under the surface to feed on plants and small "
    "creatures.",
    "The mouse is a tiny animal that can squeeze through the smallest gaps. It comes "
    "out at night to look for seeds and crumbs and hides from owls and cats.",
]


# ---------------------------------------------------------------------------
# The test set. Each question has an answer sentence that sits verbatim in the
# corpus (so the gold chunk is wherever that sentence lands), a "matched" query
# phrased in the documents' own words, and a "synonym" query that asks the same
# thing with words the corpus never uses.
# ---------------------------------------------------------------------------

QUESTIONS = [
    {
        "answer": "It comes out at night to eat grass on the land near the water.",
        "matched": "which animal comes out at night to eat grass near the water",
        "synonym": "which beast emerges after dusk to munch turf beside the lagoon",
    },
    {
        "answer": "It sleeps through the cold winter in a den and comes out hungry "
                  "in the spring.",
        "matched": "which animal sleeps through the cold winter in a den",
        "synonym": "which beast slumbers through the frosty months inside a lair",
    },
    {
        "answer": "It buries food in the ground in the autumn and digs it up again "
                  "during the cold winter.",
        "matched": "which animal buries food in the ground and digs it up in winter",
        "synonym": "which beast stashes snacks underground and unearths them in the chilly spell",
    },
    {
        "answer": "It sleeps for most of the day and carries its young in a pouch "
                  "like a kangaroo.",
        "matched": "which animal sleeps most of the day and carries its young in a pouch",
        "synonym": "which beast dozes through the daylight and totes its infant in a pocket",
    },
    {
        "answer": "The salmon is a fish that is born in rivers, swims out to the sea "
                  "to grow, and then fights its way back upriver to lay its eggs "
                  "where it began.",
        "matched": "which fish is born in rivers and swims out to the sea to lay its eggs",
        "synonym": "which creature hatches in brooks and voyages to the ocean to deposit its roe",
    },
    {
        "answer": "The woodpecker is a bird that hammers its strong beak into tree "
                  "bark to find insects.",
        "matched": "which bird uses its strong beak on tree bark to find insects",
        "synonym": "which flier drills its bill into timber rind to locate bugs",
    },
    {
        "answer": "It beats its wings so fast they hum, and it feeds on the sweet "
                  "nectar of flowers.",
        "matched": "which bird beats its wings fast and feeds on the nectar of flowers",
        "synonym": "which flier flaps its pinions rapidly and sips the syrup of blossoms",
    },
    {
        "answer": "The flamingo is a tall pink bird that wades in shallow water on "
                  "long thin legs.",
        "matched": "which tall bird stands in water on long thin legs",
        "synonym": "which lofty flier perches in liquid on lengthy slender limbs",
    },
    {
        "answer": "The swan is a large white water bird with a long graceful neck.",
        "matched": "which large white water bird has a long neck",
        "synonym": "which sizable pale aquatic flier sports a lengthy elegant throat",
    },
    {
        "answer": "The ostrich is the largest bird in the world and cannot fly, but "
                  "it can run very fast across the dry African plains on its strong "
                  "legs.",
        "matched": "which large bird cannot fly but can run fast across the plains",
        "synonym": "which enormous flier cannot soar yet dashes rapidly over the arid savanna",
    },
]


# ---------------------------------------------------------------------------
# The four TODOs: the whole retrieval pipeline, one load-bearing line each.
# ---------------------------------------------------------------------------

def term_frequencies(tokens):
    """Step 1 of a vector. Count how often each term appears in a piece of text.
    A chunk (or a query) becomes a bag of word counts."""
    # TODO 1 ------------------------------------------------------------------
    # A Counter does exactly this: it maps each token to how many times it
    # appears. One line:
    #     return Counter(tokens)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def idf(doc_freq, n_chunks):
    """The weight that makes TF-IDF work. A term in FEW chunks is rare and
    informative, so it gets a big weight; a term in every chunk tells you
    nothing, so its weight falls to zero."""
    # TODO 2 ------------------------------------------------------------------
    # doc_freq is how many chunks contain the term, out of n_chunks. The inverse
    # document frequency is the log of the ratio:
    #     return math.log(n_chunks / doc_freq)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def cosine(vec_a, vec_b, norm_a, norm_b):
    """How we compare a query to a chunk. Not by counting shared words, but by
    the ANGLE between the two vectors: the dot product over the product of their
    lengths. 1.0 means same direction, 0.0 means nothing in common."""
    if norm_a == 0 or norm_b == 0:
        return 0.0
    # TODO 3 ------------------------------------------------------------------
    # dot(vec_a, vec_b) is the overlap; divide it by the two vector lengths to
    # get the cosine of the angle between them:
    #     return dot(vec_a, vec_b) / (norm_a * norm_b)
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def found(shortlist, gold_index):
    """The measurement. Retrieval handed back a shortlist: the top chunks whose
    score cleared the relevance threshold. Did the chunk that actually holds the
    answer make that shortlist? That is the whole game: if it did not, the model
    downstream cannot answer, however clever it is."""
    # TODO 4 ------------------------------------------------------------------
    # The shortlist is a list of chunk indices. The answer chunk was found if
    # its index is one of them:
    #     return gold_index in shortlist
    # -------------------------------------------------------------------------
    return None  # <-- replace this


def first_blank_todo():
    """Probe each TODO with a trivial call. Returns the number of the first one
    still blank (returning None), or 0 if all four are filled in."""
    if term_frequencies(["x", "x", "y"]) is None:
        return 1
    if idf(2, 8) is None:
        return 2
    if cosine({"x": 1.0}, {"x": 1.0}, 1.0, 1.0) is None:
        return 3
    if found([0, 1, 2], 1) is None:
        return 4
    return 0


# ---------------------------------------------------------------------------
# Plumbing around the four TODOs. None of this is secret; it is the ordinary
# work of turning text into vectors and ranking them.
# ---------------------------------------------------------------------------

def tokenize(text):
    """Lowercase, keep only letters and digits as words. Stop words stay in here
    so chunk sizes are counted in real words; they are dropped later, when we
    build vectors."""
    out, word = [], []
    for ch in text.lower():
        if ch.isalnum():
            word.append(ch)
        elif word:
            out.append("".join(word))
            word = []
    if word:
        out.append("".join(word))
    return out


def content(tokens):
    """The meaning-bearing tokens: everything that is not a stop word."""
    return [t for t in tokens if t not in STOP]


def dot(a, b):
    """Dot product of two sparse vectors held as dicts."""
    if len(b) < len(a):
        a, b = b, a
    return sum(w * b.get(t, 0.0) for t, w in a.items())


def vlen(vec):
    """Euclidean length of a sparse vector."""
    return math.sqrt(sum(w * w for w in vec.values()))


STREAM = tokenize(" ".join(CORPUS))   # the whole corpus as one token stream


def make_chunks(stream, size):
    """Naive fixed-size chunking: cut the token stream into pieces of `size`
    words. This ignores sentence and document boundaries on purpose; it is the
    simplest thing a RAG tutorial does, and it is exactly what the chunk-size
    knob acts on."""
    return [stream[i:i + size] for i in range(0, len(stream), size)]


def answer_tokens(answer):
    """The meaning-bearing tokens of an answer sentence."""
    return content(tokenize(answer))


class Index:
    """A built TF-IDF index over the corpus at one chunk size. Holds the chunk
    vectors and their lengths so queries are cheap."""

    def __init__(self, size):
        self.size = size
        self.chunks = make_chunks(STREAM, size)
        self.n = len(self.chunks)
        tfs = [term_frequencies(content(ch)) for ch in self.chunks]   # TODO 1
        df = Counter()
        for tf in tfs:
            for term in tf:
                df[term] += 1
        self.idf = {term: idf(df[term], self.n) for term in df}       # TODO 2
        self.vecs = [{t: tf[t] * self.idf[t] for t in tf} for tf in tfs]
        self.norms = [vlen(v) for v in self.vecs]

    def query_vector(self, text):
        """Vectorise a query with the SAME idf weights. A query word the corpus
        never saw is simply absent from self.idf, so it adds nothing. That one
        line is the whole vocabulary-mismatch problem in Part 3."""
        tf = term_frequencies(content(tokenize(text)))               # TODO 1
        return {t: tf[t] * self.idf[t] for t in tf if t in self.idf}

    def similarities(self, text):
        """Cosine of the query against every chunk."""
        q = self.query_vector(text)
        nq = vlen(q)
        return [cosine(q, self.vecs[i], nq, self.norms[i])          # TODO 3
                for i in range(self.n)]

    def rank(self, text):
        """Chunk indices ordered by similarity, best first, ties broken by chunk
        order so the run is deterministic. Returns (order, scores)."""
        sims = self.similarities(text)
        order = sorted(range(self.n), key=lambda i: (sims[i], -i), reverse=True)
        return order, sims

    def retrieve(self, text, k, tau):
        """What a real retriever hands the model: the top k chunks, but only the
        ones whose similarity clears the relevance threshold tau. A match below
        tau is noise, so it is dropped. This one rule drives all three parts: a
        diluted chunk, a split fragment, or a synonym query all score too low to
        survive it."""
        order, sims = self.rank(text)
        return [i for i in order[:k] if sims[i] >= tau]

    def gold_chunk(self, answer):
        """The chunk that holds the most of the answer sentence. At a good size
        that is the chunk with the whole answer in it; chop the chunks too small
        and the answer scatters, so even its best chunk carries only a fragment."""
        want = Counter(answer_tokens(answer))
        best_i, best_overlap = 0, -1
        for i, ch in enumerate(self.chunks):
            have = Counter(content(ch))
            overlap = sum(min(want[t], have[t]) for t in want)
            if overlap > best_overlap:
                best_overlap, best_i = overlap, i
        return best_i


def recall_at_k(index, questions, field, k, tau):
    """Fraction of questions whose gold chunk survives into the retrieved
    shortlist (top k above threshold tau), using the query given by `field`
    ("matched" or "synonym")."""
    hits = 0
    for q in questions:
        shortlist = index.retrieve(q[field], k, tau)
        gold = index.gold_chunk(q["answer"])
        if found(shortlist, gold):                                   # TODO 4
            hits += 1
    return hits / len(questions) * 100


# ---------------------------------------------------------------------------
# The three parts.
# ---------------------------------------------------------------------------

def part1():
    print("=" * 78)
    print("Part 1: a tiny RAG retriever, and how often it finds the answer chunk")
    print("=" * 78)
    idx = Index(GOOD_CHUNK)
    print(f"  corpus: {len(CORPUS)} short documents, {len(STREAM)} words total.")
    print(f"  chunk size: {GOOD_CHUNK} words  ->  {idx.n} chunks on the shelf.")
    print(f"  test set: {len(QUESTIONS)} questions, each with a known answer sentence.")
    print(f"  retrieval: TF-IDF vectors, cosine similarity, keep the top {K} chunks")
    print(f"             whose score clears the relevance threshold tau = {TAU}.")
    print()
    good = recall_at_k(idx, QUESTIONS, "matched", K, TAU)
    print(f"  recall@{K} with sensibly sized chunks = {good:.0f}%")
    print("  Read that as: in that share of the questions, the chunk that actually")
    print(f"  holds the answer survived into the top {K} we would hand to the model.")
    print("  When it does not, the smartest LLM alive still answers from wrong text.")
    print()
    print("  A couple of retrievals, so you can see it working:")
    for q in QUESTIONS[:2]:
        order, sims = idx.rank(q["matched"])
        gold = idx.gold_chunk(q["answer"])
        pos = order.index(gold) + 1
        snippet = " ".join(idx.chunks[order[0]])[:58]
        print(f"    q: {q['matched'][:52]!r}")
        print(f"       gold ranked #{pos} at cosine {sims[gold]:.2f}; "
              f"top hit \"...{snippet}...\"")
    return good


def part2():
    print("\n" + "=" * 78)
    print("Part 2: break it with chunk size. Too small splits the answer, too")
    print("        large dilutes it, and recall peaks in the middle")
    print("=" * 78)
    print(f"  Same corpus, same {len(QUESTIONS)} questions, same top {K} above tau. Only")
    print("  the chunk size changes. Watch recall climb then fall: an inverted U.")
    print()
    print(f"  {'chunk size':>12}{'chunks':>9}{'recall@'+str(K):>12}")
    peak_size, peak_recall = None, -1.0
    for size in SWEEP:
        idx = Index(size)
        r = recall_at_k(idx, QUESTIONS, "matched", K, TAU)
        bar = "#" * int(round(r / 5))
        print(f"  {size:>12}{idx.n:>9}{r:>11.0f}%  {bar}")
        if r > peak_recall:
            peak_recall, peak_size = r, size
    print()
    small = recall_at_k(Index(SMALL_CHUNK), QUESTIONS, "matched", K, TAU)
    large = recall_at_k(Index(LARGE_CHUNK), QUESTIONS, "matched", K, TAU)
    print(f"  too small ({SMALL_CHUNK} words):  recall@{K} = {small:.0f}%")
    print("    The answer sentence is cut across several tiny chunks, so the one")
    print("    that holds the most of it carries only a word or two of the query.")
    print("    Its similarity is weak and it sinks below the other scraps, or below")
    print("    tau, so the retriever never hands it over.")
    print(f"  too large ({LARGE_CHUNK} words): recall@{K} = {large:.0f}%")
    print("    Now the answer is one sentence buried in a wall of unrelated text. Its")
    print("    few matching words are averaged over the whole chunk, the cosine of")
    print("    the right chunk drops below tau, and the retriever discards it as")
    print("    noise even though the answer is sitting right there inside it.")
    print(f"  best in the sweep: {peak_size} words at {peak_recall:.0f}%. Chunk size is a")
    print("  knob you tune, not a default you ignore.")
    return small, large


def part3():
    print("\n" + "=" * 78)
    print("Part 3: break it with vocabulary. TF-IDF matches words, not meaning")
    print("=" * 78)
    idx = Index(GOOD_CHUNK)
    print(f"  Good chunk size ({GOOD_CHUNK} words), the same {len(QUESTIONS)} questions, but")
    print("  reworded with synonyms the documents never use: 'swift' for 'fast',")
    print("  'beast' for 'animal', 'dwells' for 'lives', and so on.")
    print()
    matched = recall_at_k(idx, QUESTIONS, "matched", K, TAU)
    synonym = recall_at_k(idx, QUESTIONS, "synonym", K, TAU)
    print(f"  recall@{K}, matched wording:  {matched:.0f}%")
    print(f"  recall@{K}, synonym wording:  {synonym:.0f}%")
    print()
    print("  Why it falls off a cliff: a query word the corpus never saw is not in")
    print("  the vocabulary, so it has no idf weight and contributes nothing to the")
    print("  score. Look at how many query words even survive to be matched:")
    print()
    print(f"  {'question':>9}{'matched hits vocab':>22}{'synonym hits vocab':>22}")
    for i, q in enumerate(QUESTIONS, 1):
        mt = content(tokenize(q["matched"]))
        st = content(tokenize(q["synonym"]))
        m_in = sum(1 for t in mt if t in idx.idf)
        s_in = sum(1 for t in st if t in idx.idf)
        print(f"  {i:>9}{f'{m_in}/{len(mt)}':>22}{f'{s_in}/{len(st)}':>22}")
    print()
    print("  Same questions, same answers sitting right there in the corpus. Only")
    print("  the words changed, and retrieval went blind. This is the exact gap")
    print("  semantic embeddings (Day 38) close: they put 'swift' and 'fast' near")
    print("  each other in vector space, so meaning matches even when words do not.")
    print("  A reranker on top then reorders the shortlist by a deeper read.")
    return matched, synonym


def verdict(name, predicted, actual, unit="%"):
    if predicted is None:
        print(f"  {name:<34} actual = {actual:>6.0f} {unit}  (no prediction)")
        return
    diff = abs(actual - predicted)
    note = "     close enough" if diff <= max(10.0, 0.15 * abs(predicted)) \
        else f"  off by {diff:.0f}"
    print(f"  {name:<34} you = {predicted:>4.0f}   actual = {actual:>6.0f} {unit}  {note}")


def main():
    if all(v is None for v in PREDICTIONS.values()):
        print("\n  !! No predictions yet. Open this file, fill in PREDICTIONS,")
        print("     then run again. The guess is the point, so make it first.\n")
        sys.exit(1)

    blank = first_blank_todo()
    if blank:
        print(f"\n  !! TODO {blank} is still blank. Fill in the four numbered TODOs,")
        print("     then run again. Nothing below works until each one returns a")
        print(f"     real value. Start with TODO {blank}.\n")
        sys.exit(0)

    good = part1()
    small, large = part2()
    matched, synonym = part3()

    print("\n" + "=" * 78)
    print("Scoreboard")
    print("=" * 78)
    verdict("P1 good chunk recall@3", PREDICTIONS["good_recall_pct"], good)
    verdict("P2 too-large recall@3", PREDICTIONS["large_recall_pct"], large)
    verdict("P3 too-small recall@3", PREDICTIONS["small_recall_pct"], small)
    verdict("P4 synonym recall@3", PREDICTIONS["synonym_recall_pct"], synonym)

    print("\n" + "=" * 78)
    print("The number to carry")
    print("=" * 78)
    print(f"  At a sensible chunk size, retrieval found the answer chunk {good:.0f}% of the")
    print(f"  time. Chunk too large and it fell to {large:.0f}%; too small, {small:.0f}%. Keep the")
    print(f"  good size but ask with synonyms and it crashed to {synonym:.0f}%, because")
    print("  TF-IDF matches words, not meaning. Every one of those failures happens")
    print("  BEFORE the model sees anything. That is why RAG is a retrieval problem")
    print("  wearing a generation costume, and why 'the LLM got it wrong' is usually")
    print("  'we handed it the wrong three chunks'.")
    print()


if __name__ == "__main__":
    main()
