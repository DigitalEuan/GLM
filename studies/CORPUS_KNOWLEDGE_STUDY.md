# The corpus as what the GLM knows — counting instead of training

## Tier 0 — the coarse read

**Question.** Can the project's own corpus — every study, state document, Lean file, Python module, JSON and CSV the GLM has accumulated, read as folder, document, paragraph, sentence and token — be used directly as the GLM's knowledge, giving it the surrounding-word context an LLM gets from training, without letting chance or a float into the system?

**Verdict.** Yes, for the uses that reduce to counting: the corpus, counted rather than trained, predicts held-out text three times better than word frequency and eight times better than its own words without their order, grows more accurate as it grows, is exactly additive and order-free, and reads word use and definitions with a witness sentence for every answer; it does not yet know when its prediction is right at a useful coverage, and no rule tried for choosing terms gave 80% definitions.

**Deciding figure.** 7 of 9 marks, both amended marks missed; next token 21.5% against 6.9% (most frequent token) and 2.7% (order control) on 25,435 novel held-out sentences; counts equal after halving and after reversing 2,187 documents.

**Recomputed by.** `glm_universal.knowledge.study.corpus_knowledge_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 154 (§§0–6, committed before the stored
measurement; §7 is what came out). The owner asked whether everything the
GLM has written down — the studies, the Lean development, the scripts, the
data files, and the supplied material in `source_material/` — can be used as
the GLM's corpus *directly*: what an LLM gets from training (the words a word
keeps company with, the way a phrase goes on, what a term is said to be),
obtained without randomness and without probability being let into the
system.

The design answer is that an LLM's training reduces, for every one of those
uses, to statistics of co-occurrence, and that co-occurrence can be *counted*
exactly instead of being estimated by gradient descent. Counting has three
properties that training does not:

1. **It is deterministic.** The same bytes give the same counts; nothing is
   initialised at random and nothing depends on a batch order.
2. **It is additive.** The counts of two disjoint collections are the sum of
   their counts, so adding a document is adding its counts and the result is
   *equal* to recounting from nothing. That is what makes it safe for the
   corpus to keep growing: the model "learns as it collects", and the order
   documents arrive in cannot change it.
3. **Every figure has a witness.** A count is a number of sentences, and each
   one has an address (`document#paragraph.sentence`), so anything said from
   the counts can be traced back to what said it.

None of those is true of a trained network, and each is checkable here.

## 1. What is built

A new package, `glm_universal/knowledge/`:

| module | what it holds |
|---|---|
| `reader.py` | the corpus walk, by rule: `.md`/`.txt` prose (no fenced code; a heading is a sentence; a table row is one sentence), Python docstrings and comments, Lean doc and line comments, JSON strings and CSV cells of at least five words with more words than numbers, and the members of `source_material/*.zip`. Every sentence carries its address and whether it sits in its document's tier-0 block. |
| `model.py` | the counts: tokens, the one- and two-token continuation tables, document and folder frequency, and content-word co-occurrence inside a four-token window; the integer association rule; and the cache, re-read per file digest so a changed file is the only file re-read. |
| `answer.py` | five readings: `define` (what the corpus says X is), `context` (the words over-represented around X at sentence, paragraph or document scale), `similar` (words used like X), `related` (words found with the same company as X), `continue_text` (the corpus's own continuation of a phrase), and `spread` (how far X reaches through the hierarchy). |
| `study.py` | this measurement. |

Every rate is a `Fraction`, every comparison is between integers, and a tie
is reported rather than broken: `continue_text` stops at a tie and names it,
and `predict` returns no word when two continuations are equally frequent.

## 2. What is proved before the measurement

`RequestProject/GLM/CorpusKnowledge.lean` states the three properties above
for a count model over lists of sentences (as delivered; the pre-registration
named two of these `predict_some_max` and `predict_some_unique`, and the
second was proved as the stronger `predict_some_iff`):

* the counts of a concatenated corpus are the sum of the counts (`count_append`),
  so incremental counting equals recounting (`train_append`, `train_snoc`);
* the counts are invariant under any reordering of the documents (`train_perm`);
* a count is positive exactly when a sentence carries the feature
  (`count_pos_iff`, `train_pos_iff`) — every figure has a witness;
* the guarded prediction returns a word exactly when it is the unique strict
  maximum (`predict_some_iff`), its count is then at least every other
  continuation's (`predict_some_max`), and a tie at the top gives no
  prediction (`predict_eq_none_of_tie`);
* the squared-cosine similarity of two finite feature sets lies in `[0, 1]`
  and is `1` exactly when the sets are equal (`sqcos_nonneg`, `sqcos_le_one`,
  `sqcos_eq_one_iff`).

`lake build` compiles it with no `sorry`; the axioms are `propext`,
`Classical.choice` and `Quot.sound`.

## 3. The marks, declared before the measurement

The held-out split is a rule on the sorted list of corpus documents: the
document at index `i` is held out when `i mod 5 = 4`. A held-out sentence is
**novel** when its token sequence occurs nowhere in the training documents
(the corpus carries copies — the supplied zip holds earlier versions of some
studies — and a copied sentence is recall, not prediction). Next-token
positions are every token of every novel held-out sentence, the end-of-sentence
marker included.

| # | mark | pass |
|---|---|---|
| K1 | next-token accuracy of the counted model (two-token context, backing off to one, then to the most frequent token), on novel held-out sentences | at least twice the accuracy of always answering the most frequent token |
| K2 | the same, against the **order control** — the same training documents with every sentence's tokens sorted, which keeps every count of the bag and destroys word order | at least 10 percentage points above the control |
| K3 | the **guarded** reading — answer only from a two-token context seen at least twice whose maximum is unique — against the unguarded accuracy | precision at least 1.5 times the unguarded accuracy, at a coverage of at least 20% |
| K4 | learning as it collects: accuracy trained on the first 25%, 50%, 75% and 100% of the training documents | the 100% accuracy is at least the 25% accuracy |
| K5 | additivity on the real corpus: the model of the training documents equals the sum of the models of its two halves, and equals the model of the documents taken in reverse order | equal count signatures, both |
| K6 | `similar` on the twelve number words *one* … *twelve* | at least half of the ten neighbours of each are other number words, on average |
| K7 | singular and plural (`w`, `w+s`, both read and compared) — spelling never enters the similarity, so the plural is a fair blind target | the plural is among the ten neighbours of the singular for at least 20% of pairs, under `similar` or `related`, and at least ten times chance |
| K8 | `define` on the term list (the 40 content words of at least four letters with the largest document frequency, and the 40 content-word pairs with the largest sentence count) | at least 80% of the terms answered with a definitional sentence |
| K9 | refusal: each term of K8 spelled backwards (`golay` → `yalog`) | refused every time |

### 3a. Two amended marks, declared after the first measurement and before the second

The first measurement (§7) missed K3 and K8. Both misses are kept as
misses. Two amended marks are declared here, before they are measured, and
are reported beside the originals, never in place of them:

| # | mark | pass |
|---|---|---|
| K3′ | the **majority guard** — answer only from a two-token context seen at least three times whose winning continuation is more than half of what followed it | precision at least 1.5 times the unguarded accuracy, at a coverage of at least 20% |
| K8′ | `define` with the **label rule** (a glossary separator followed by a path, a file name or nothing is a label, not a definition; a comma is a gloss only before *the*, *a* or *an*) on the corpus's **own marked terms**: the 60 phrases of one to three alphabetic words set in bold (`**…**`) most often across the written Markdown documents, outside the archive and the supplied material | at least 80% answered, and the backwards spellings refused every time |

K8's term rule picked function words (*rather*, *never*, *itself*) and code
fragments (*usr bin*, *type ignore*), which no corpus defines and no reader
would ask about; the bold terms are the phrases the documents themselves mark
as terms. The label rule is a repair to `define` that the first audit (§7.2)
asked for, and it is applied to K8's list too so that both lists are read by
the same rule.

## 4. What would count against

* K1 or K2 missed: the counts carry no more about what comes next than word
  frequency, or than the bag of words without its order — the "surrounding
  word context" would be a frequency table and nothing more.
* K3 missed: the refusal rule buys no precision, so the counted model cannot
  tell when it knows.
* K5 missed: the model is not additive on the real corpus, so an incremental
  model could not be trusted to equal a recount.
* K6/K7 missed: the context sets do not carry word use.

## 5. What is not claimed

* **Not an LLM.** Nothing here generates fluent text about something no
  sentence of the corpus says. `continue_text` reproduces the corpus's own most
  frequent continuation, and stops — naming the tie — as soon as the corpus is
  undecided. It is recall with a witness, and is classed `table` under
  [`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md) §1, not derivation.
* **Not a judge of truth.** `define` returns what the corpus *says* X is, with
  the sentence's address and the rank of its source (tier 0 first, then the
  state documents, the Lean doc comments, docstrings, the archive and the
  supplied material, and data files). An archived sentence can be out of
  date; its rank says so.
* **Not a substitute for the registers.** The corpus readings are a new query
  kind, `corpus`, beside the others; nothing that the registers answer is
  rerouted through them.
* **No probability.** A count, a ratio of counts as a `Fraction`, and an
  integer comparison are the whole of it; no score is a probability estimate
  and nothing is sampled.

## 6. Files

* `glm_universal/knowledge/` — the package (`reader.py`, `model.py`,
  `answer.py`, `ask.py`, `study.py`, `README.md`).
* the `corpus` query kind: `python3 GLM.py -q "corpus define golay code"`,
  with column 3 recounting the answer by brute force.
* `glm_universal/knowledge/_data/corpus_knowledge.json` — the stored
  measurement, beside the digest of the code that took it.
* `glm_universal/tests/test_corpus_knowledge.py` — the tests.
* `glm_lean/RequestProject/GLM/CorpusKnowledge.lean` — §2.
* `python3 -m glm_universal.tools corpus-knowledge [--write]` — the instrument.

## 7. What came out

Two measurements were taken. The first (kept as
`_data/corpus_knowledge_first.json`) met 7 of 9 marks and missed K3 and K8;
§3a was then declared and committed, the label rule was added to `define`,
and the second measurement (`_data/corpus_knowledge.json`, the stored one,
`tools corpus-knowledge`) took all nine marks again together with K3′ and
K8′. Between the two, two ranking repairs were also made to `define` (a
sentence copied into several documents is kept at its best-ranked copy, not
its first; a table row of more than two cells is never ranked as a
glossary entry); they change which definition comes first, never whether a
term is answered, so no mark depends on them. The corpus itself moved
between the measurements (this round's own files are part of it), so the
held-out split moved with it.

### 7.1 The corpus

2,187 documents (1,268 Python, 375 Markdown, 310 Lean, 173 JSON, 53 text, 8
CSV), 184,118 sentences, 2,655,147 tokens and 49,603 distinct words; 1,031
documents come from `source_material/` (most of them the members of the
supplied zip archive), 981 from ``, 160 from `studies/`. Reading it
from nothing takes under a minute; after one file changes, only that file is
read again. The held-out fifth of the documents holds 47,070 sentences, of
which 25,435 are novel (said nowhere in the training documents); K1–K4 are
scored on every token of those 25,435.

### 7.2 The marks

| # | first | second (stored) | mark |
|---|---|---|---|
| K1 | 22.4% against 7.2% | **21.5% against 6.9%** (94,028 of 438,119 positions; the most frequent token is *the*) | met |
| K2 | control 2.5% | **control 2.7%** | met |
| K3 | 24.2% precision at 63% coverage, against 22.4% | **23.8% at 62.3%**, against 21.5% | **missed** |
| K4 | 17.4 → 18.8 → 20.3 → 22.4% | **16.8 → 18.4 → 19.4 → 21.5%** | met |
| K5 | equal, equal | **equal, equal** (2,187 documents) | met |
| K6 | 61/120 | **61/120** of the neighbours are number words, against a chance of 11 in 11,309 | met (narrowly) |
| K7 | related 283/1,098 | **related 285/1,099 (25.9%)**, similar 143/1,099 (13.0%), against chances of 1 in 1,113 and 10 in 11,309 | met |
| K8 | 56/80 | **52/80 (65%)** | **missed** |
| K9 | 80/80 | **80/80** | met |
| K3′ | — | precision **54.0%** (2.5 times the unguarded accuracy) at coverage **10.7%** | **missed** (coverage) |
| K8′ | — | **45/60 (75%)**; backwards spellings refused **58/60** | **missed** (both halves) |

**7 of 9 marks; both amended marks missed.** In one sentence: Yes, for the uses that reduce to counting: the corpus, counted rather than trained, predicts held-out text three times better than word frequency and eight times better than its own words without their order, grows more accurate as it grows, is exactly additive and order-free, and reads word use and definitions with a witness sentence for every answer; it does not yet know when its prediction is right at a useful coverage, and no rule tried for choosing terms gave 80% definitions.

### 7.3 What this answers

**The corpus can be used directly, and counting is enough for what an LLM's
corpus gives it locally.** The surrounding-word context is real and it is in
the order of the words, not only in their frequencies: the counted model
predicts the next token of sentences it has never seen three times as often as
word frequency does (K1), and the same counts with each sentence's words
sorted — every frequency kept, only the order lost — fall to 2.7%, below
even the frequency baseline (K2). The accuracy rises at every quarter of
added training documents (K4): the model learns as the corpus collects, and
it does so by addition, which K5 checks on the real corpus and
`train_append` / `train_perm` prove in general.

**Word use comes out of the contexts.** Asked for the words used like *seven*,
the positional reading returns *eight, ten, four, nine, five, six, twelve,
fourteen, three, fifteen* — it knows nothing of spelling or arithmetic, only
that these words fill the same slots. Half of all number-word neighbours are
number words (K6, narrowly: *one*, *eleven* and *twelve* are pulled to
determiners and to rare company), and a quarter of singular nouns find their
own plural among the ten words sharing their company (K7), two hundred times
chance. *decoder* is used like *decoding, quantiser, generator, reader*;
*compute* like *evaluate, encode, reproduce, infer, certify*.

**Two negative results, kept.**

* **The counted model does not yet know when it is right at a useful
  coverage** (K3, K3′). The declared guard — a two-token context seen twice
  with a unique maximum — buys almost no precision. The majority guard buys a
  great deal (54% precision, 2.5 times the unguarded rate) but at 10.7%
  coverage, under the declared 20%. Between the two lies a coverage/precision
  curve that this round did not declare a point on; the next round may, but
  only before measuring it.
* **No rule tried for choosing terms produced 80% definitions** (K8, K8′).
  K8's rule chose high-frequency words, a third of which are not terms at
  all (*rather*, *never*, *itself*, *usr bin*, *type ignore*); the label rule
  removed four label lines it had counted as definitions, so K8 fell from 70%
  to 65%, which is the rule working. K8′'s bold-term rule chose the
  documents' structural labels (*verdict*, *deciding figure*, *recomputed
  by*, *met*), and its refusal half failed on two backwards spellings that are
  real words of the corpus: *no* → *on*, and *is* → *si*, which the corpus
  defines as the sine integral. Both misses are failures of the term rule as
  much as of `define`, and the answered rate is a weak proxy for a correct
  definition in either case. A term list that is what a reader asks, with a
  graded answer, is the open item (§7.5).

### 7.4 Faculties (D15)

* **refuse — moved.** A term the corpus never mentions, a term it mentions
  but never defines, a continuation at a tie, and a word with too little
  company to compare are each refused with the reason (K9: 80/80; the
  `corpus-unmentioned` evaluation case).
* **table — the rest.** `define`, `context`, `similar`, `related`,
  `continue` and `spread` make what the corpus holds reachable as answers; a
  corpus answer is a sentence or a count of the corpus, so none of it is
  derivation, and it is not geometric addressing either: the readings are
  exact counts, not positions on the lattice.
* **derive — not moved.**

### 7.5 What is left

* **A graded term list.** Hold out the glossary of
  [`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md) (Appendix E) from the
  corpus, ask `define` for each of its terms, and grade the answer against the
  held-out gloss by shared content words, against a control that answers with
  a random-free but uninformed sentence (the term's first mention). That
  measures the definitions themselves rather than whether one was found.
* **A declared point on the guard curve** (K3′ at a coverage of 20%), declared
  before it is measured.
* **The corpus as the planner's vocabulary.** The `similar` reading could
  offer the parser's `did you mean` list words *used like* the unknown one
  rather than words spelled like it; it needs a frozen-path comparison,
  because it changes refusals the evaluation pins.
* **A Leech address for a word.** The associated-context sets are finite
  sets, and the corpus package already quantises 24-count vectors onto the
  lattice; a word's 24 counts against 24 declared anchor words would give it
  a point on the same lattice as a carrier, a declaration and a document
  section, with the completeness guarantee of `GLM.Retrieval`.
