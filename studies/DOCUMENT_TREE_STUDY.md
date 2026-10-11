# The document tree as a third native book, on a frozen corpus

## Tier 0 — the coarse read

**Question.** Can a third native book for the documents — a section's position in the document tree, held as a Golay word — move the document rankings past parity with the raw lexical vector, when it is measured on a frozen copy of the corpus?

**Verdict.** No: the document tree cannot move the document rankings past parity. The literal book — the section's document as a Golay word — reads the relevance relation and scores a hit at 1 on every query, which is a leak and not a refinement; the leak-free part of the tree, where in its document a section sits, changes no hit, because the two earlier books leave a tie across the top-five boundary on only 30 of 1,506 queries, and even the leaking book in that layer gains one query. N2 is closed in the negative by its ceiling.

**Deciding figure.** On the 1,506-query census of the frozen corpus, hit@5 / relatives in the top five: `lexical_native3` 324 / 413 against `lexical_raw` 323 / 414 (discordance 7 : 6, sign test 1); `lexical_native3` identical to `lexical_native2` on every query's hit (0 : 0); the oracle third layer `path3` 325 / 414; `path_first` 1,506 hits at 1; marks F1, F3 and F5 met, F2, F4 and F6 not met.

**Recomputed by.** `glm_universal.reasoning.document_tree.document_tree_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 9 of the order of work in [`STATUS.md`](../STATUS.md) §3.4, retrieval,
continued after Phase 101: **N2**. Phase 70
([`NATIVE_PARITY_STUDY.md`](NATIVE_PARITY_STUDY.md) §6) left it as:

> Every lexical ranking, native or standard, stays within one relevant section
> of the others on the document corpus. Whether a third native book — the
> section's position in the document tree as a Golay word — can move the
> document figures past parity, measured on a frozen copy of the corpus so
> that the figure does not move with the edit that reports it, is open.

Two facts about the document benchmark decide how the question has to be
asked, and both were read before anything was declared:

* **Relevance is the tree.** `corpus.address.relative_table` counts a section
  relevant to a query exactly when it is another section *of the same
  document*. Its docstring says why that relation was chosen: it "is nowhere
  in either feature map -- no coordinate sees a path". A book that holds a
  section's full position in the tree holds its document, and so holds the
  relevance relation itself.
* **Every section is a query.** All 1,502 units of the written corpus belong
  to a document with at least two sections, so every unit has a relative and
  the whole corpus can be used as the query set (a *census*), rather than the
  60-query spread that every earlier document figure was read on.

So the item, taken literally, has an answer that needs no measurement — a book
that names the document finds the document — and that answer is a leak, not a
refinement. This round therefore declares the literal book as the **leak
control**, proves in Lean why it must score perfectly, and asks N2's question
of the part of the tree that does *not* name the document.

## 1. The objects

**The frozen corpus.** One snapshot of the written corpus, taken once, after
§0–§2 of this study were written and before any measuring code existed:
every unit's name, document, folder, its ordinal among its document's
sections, its document's section count, both Leech addresses (lexical and
structural, as `corpus.address.addresses` holds them) and both raw feature
vectors. It is stored in `reasoning/_data/document_tree_frozen.json` beside
the SHA-256 of its own canonical content. Every figure in this study is read
off the snapshot; the live documents are never consulted by the measurement,
so writing the results into this file cannot move them.

**Three tree words.** Each is a codeword of the extended binary Golay code
(`substrate.mog.GOLAY.encode_mask` of a 12-bit message), compared by Hamming
distance — 0 for the same position, at least 8 for any other.

| book | 12-bit message | what it names |
|---|---|---|
| `path` | the index of the section's document among the snapshot's documents | the document — the relevance relation |
| `folder` | the index of the document's folder | a coarse part of the path; 104 of the 135 documents share the folder `studies` |
| `place` | `min(i, 7) + 8 · min(n − 1 − i, 7)` for the section's ordinal `i` among the document's `n` sections | where in its document a section sits, counted from both ends, capped at 7 — no document identity |

**The rankings.** Each is a lexicographic key over a candidate section, the
query excluded, as in Phase 70.

* `lexical_raw` — the raw lexical vector (the standard Phase 70 measured
  parity against), ties by name.
* `lexical_native2` — Phase 70's two-book native ranking: lexical read-back
  distance, structural read-back distance, structural Leech distance, name.
* `lexical_native3` — **the subject**: lexical read-back distance, structural
  read-back distance, `place` Hamming distance, structural Leech distance,
  name. The tree book decides only what both earlier books leave tied.
* `lexical_raw3` — like for like, no lattice and no code: raw lexical, raw
  structural, `|Δ min(i,7)| + |Δ min(n−1−i,7)|`, name.
* `lexical_place2` — the tree book one layer higher: lexical read-back,
  `place` Hamming, structural read-back, structural Leech, name.
* `path_first` — the leak control: `path` Hamming distance first, then
  `lexical_native2`'s key.
* `path3` and `folder3` — `path` and `folder` in the third layer, where
  `place` sits in `lexical_native3`.

## 2. Declarations — written before any measuring code

The query sets are the census (every unit of the snapshot, 1,502 queries) and,
for continuity with Phase 70, the 60-query spread of
`corpus.address.query_sample` read on the snapshot. A *hit* at `k` is a
relative among the first `k`; precision@5 is relatives in the first five over
five. The discordance of two rankings is the pair (queries where only the
first has a hit at 5, queries where only the second does), and its two-sided
sign test is `GLM.CorpusResample.signTest`. Everything is exact (D7): integers,
masks and `Fraction`, no random source.

* **F1 — frozen.** The snapshot's stored digest matches its content; its
  addresses read back exactly to its stored vectors (0 failures); and the
  measurement re-taken from the snapshot after this study's results are
  written equals the stored measurement.
* **F2 — the books are what they say.** Every tree word that occurs is a
  Golay codeword (zero syndrome); `path` takes a different word on every
  document; and **every `place` word that occurs is shared by sections of at
  least two documents** — no place word identifies a document.
* **F3 — the leak, declared.** `path_first` has a hit at 1 on every census
  query, as `GLM.DocumentTree.separating_key_head` says it must. This is
  recorded as the reason the literal book cannot be a retrieval book under
  this relevance: it reads the answer. `path3` is reported beside it, and any
  gain it shows is labelled a leak.
* **F4 — N2, the leak-free book (the question).** On the census,
  `lexical_native3` has hit@5 and precision@5 each at least those of
  `lexical_raw`, and its discordance against `lexical_raw` at `k = 5` runs its
  way with a sign test at most 0.05. Met, the book is past parity. Not
  significant but not behind, the outcome is a **draw** and is recorded as
  such. Behind on either figure, **not met**.
* **F5 — like for like.** On the census, `lexical_native3` has hit@5 and
  precision@5 each at least those of `lexical_raw3`.
* **F6 — the higher layer.** On the census, `lexical_place2` has hit@5 at
  least that of `lexical_raw`.

`folder3` and the 60-query spread are reported, with no mark.

**Wiring, declared now.** If F4 is met, `corpus.address.rank` gains the scheme
`lexical_native3`. No live default changes in any case: the live document
ranking is the native word overlap (`words_native`, Phase 71), which is far
ahead of every vector ranking, and this round does not touch it. A mark
missed changes nothing and the study says so.

**What would count as moving the target (D15).** F4 met moves **address**:
a native book would rank the documents past the standard vector it was level
with. F3 moves nothing; it is a control, and its value is that it says, with
a proof, why the item as first written could only ever have scored by leaking.

**What it does not claim.** The `place` book can only reorder candidates that
the two earlier books leave exactly tied (`GLM.NativeParity.take_map_primary_eq`
is the general form), so F4's ceiling is set by how many ties the first two
books leave inside the first five.

## 3. Results

Everything below is read off the snapshot
`reasoning/_data/document_tree_frozen.json` (digest `5fefdc91…`), taken after
§0–§2 were written: **1,506 units in 136 documents**. That is four units more
than §0 counted, because the snapshot holds this study's own declaration —
the one edit that was allowed into it. Every unit has a relative, so the census
is 1,506 queries. `python3 -m glm_universal.tools document-tree` prints the
table; the stored measurement is `reasoning/_data/document_tree.json`.

### 3.1 The census

| ranking | hit@1 | hit@5 | relatives in the top five | precision@5 |
|---|---|---|---|---|
| `lexical_raw` — the raw lexical vector (the standard) | 107 | 323 | 414 | 5.50 % |
| `lexical_native2` — lexical book, then structural book (Phase 70) | 113 | 324 | 413 | 5.48 % |
| **`lexical_native3`** — then the place word | 113 | 324 | 413 | 5.48 % |
| `lexical_raw3` — raw lexical, raw structural, raw place | 113 | 324 | 413 | 5.48 % |
| `lexical_place2` — the place word one layer higher | 112 | 319 | 410 | 5.44 % |
| `folder3` — the folder word in the third layer | 113 | 324 | 413 | 5.48 % |
| `path3` — the path word in the third layer | 113 | 325 | 414 | 5.50 % |
| `path_first` — the path word first (the leak control) | 1,506 | 1,506 | 7,462 | 99.1 % |

Discordances at `k = 5` (queries where only the first / only the second has a
hit), with the two-sided sign test (`GLM.DocumentTree.census_signs`):
`lexical_native3` against `lexical_raw` **7 : 6**, sign test 1;
`lexical_native2` against `lexical_raw` 7 : 6; `lexical_native3` against
`lexical_native2` **0 : 0**; `lexical_place2` against `lexical_raw` 3 : 7, sign
test 11/32; `path3` against `lexical_native2` 1 : 0; `folder3` against
`lexical_native2` 0 : 0.

On the 60-query spread of Phase 70, read on the same snapshot, every ranking
but the control has 15 queries with a hit at 5 and 21 relatives in its top
five; `path_first` has 60 and 297.

### 3.2 The ceiling, and why it decides the question

A third layer orders only what the first two leave exactly tied, and it can
change the first five only when the first two tie *across* the boundary
between rank five and rank six (`GLM.DocumentTree.take_perm_of_gap`: with no
tie at the boundary, every ranking sorted by the same first two keys has the
same top five as a set). On the census that happens on **30 of 1,506
queries**. The place word changed the top-five set on 7 of them and changed
no hit: the discordance against `lexical_native2` is 0 : 0.

The ceiling can be read exactly, because `path3` is the oracle for that layer:
inside every tie of the first two books it puts the query's own document
first, which is the best any third layer could do for the count of relatives
in the top five. It gains **one query** and one relevant section over
`lexical_native2` (325 / 414 against 324 / 413). So no book in the third layer
— native or standard, leak-free or leaking — can move the census by more than
one query, and "past parity" with `lexical_raw` (323 / 414) is out of reach
for the layer N2 named. That is the negative result, and it is a property of
the first two books, not of the tree.

### 3.3 The leak

`path_first` has a hit at 1 on all 1,506 queries and 99.1 % precision@5 (its
only misses are documents with fewer than six sections). That is what
`GLM.DocumentTree.separating_key_head` proves it must do: its key, the
Hamming distance between Golay words of document indices, is zero exactly on
the relevant candidates (`injective_word_separates`), and a ranking sorted by
such a key puts a relevant candidate first whenever there is one. It is also
not a book a reader could use: a question asked from outside has no position
in the tree, so the key cannot be computed for it. The literal form of N2
therefore had a perfect score available that would have meant nothing.

### 3.4 The books

Every tree word is a Golay codeword (136 words, 0 with a nonzero syndrome);
`path` takes a different word on each of the 136 documents; distinct place
words are at least 8 apart. **F2 asked that no place word name a single
document, and 3 of the 61 place words do**: the only document with exactly
three sections (`overlay/glm_universal/sandbox/README.md`) has three positions
no other document has. The leak is real but has no effect, since the place
word changes no hit.

### 3.5 Every mark

| mark | what it asks | outcome |
|---|---|---|
| **F1** | snapshot intact, read-back exact, the figures re-taken from the snapshot equal the stored ones | **met** — 3,012 of 3,012 addresses read back exactly; the measurement re-taken after these results were written is the stored one, and the test suite re-takes the 60-query spread on every run |
| **F2** | every tree word a codeword, `path` injective, no place word naming one document | **not met** — 3 of 61 place words name the one three-section document |
| **F3** | `path_first` has a hit at 1 on every census query | **met** — 1,506 of 1,506 (the leak, as declared) |
| **F4** | `lexical_native3` at least `lexical_raw` on hit@5 and precision@5, its discordance its way at sign test ≤ 0.05 | **not met** — one query ahead on hit@5 (324 against 323), one relevant section behind on precision@5 (413 against 414), discordance 7 : 6 |
| **F5** | `lexical_native3` at least `lexical_raw3`, like for like | **met** — identical on every figure |
| **F6** | `lexical_place2` hit@5 at least `lexical_raw` | **not met** — 319 against 323 |

F4 is the question, and its outcome is the same draw Phase 70 recorded, now on
a census of 1,506 queries rather than 60 and on a corpus that cannot move:
the native two-book ranking and the raw lexical vector are level within one
query and one relevant section. The place word moves neither.

So N2 is closed in the negative by its ceiling: even the literal book, which
scores a hit at 1 on every query when it is read first, gains one query when
it is read in the third layer, where the item placed the tree.

**The verdict, in one paragraph.** No: the document tree cannot move the document rankings past parity. The literal book — the section's document as a Golay word — reads the relevance relation and scores a hit at 1 on every query, which is a leak and not a refinement; the leak-free part of the tree, where in its document a section sits, changes no hit, because the two earlier books leave a tie across the top-five boundary on only 30 of 1,506 queries, and even the leaking book in that layer gains one query. N2 is closed in the negative by its ceiling.

## 4. The Lean file

`RequestProject/GLM/DocumentTree.lean` builds with no `sorry` and the standard
axioms only.

* `separating_key_head` — a ranking sorted by a key that is zero exactly on
  the relevant candidates puts a relevant candidate first, whenever there is
  one (F3).
* `injective_word_separates` — under an injective word map, two documents'
  words are at Hamming distance zero exactly when they are the same document:
  the `path` book is such a key.
* `map_eq_of_perm_sorted` and `take_perm_of_gap` — two rankings that are
  permutations of each other and sorted by the same cost have the same top `k`
  as a set unless the cost ties across the boundary (§3.2's ceiling), for any
  linearly ordered cost, so for the pair of the first two layers.
* `census_signs` — the sign-test values of §3.1, checked by the kernel.

## 5. Wiring

F4 is not met, so, as declared, `corpus.address.rank` gains no scheme and no
default changes. What the round adds to the system is the instrument:
`reasoning/document_tree.py`, the command
`python3 -m glm_universal.tools document-tree` (`--freeze` takes a snapshot,
`--write` re-takes the measurement from it), and
`tests/test_document_tree.py`. The frozen snapshot is the first document
benchmark in the repository whose figures do not move with the documents, and
it can carry any later document-ranking question.

By the standing target (`ITERATE.md` §5) the round moves nothing: it adds no
derivation, no addressing and no refusal. It closes an open item with a
reason: the document tree is either the answer (the leak) or below the
ceiling of the layer it could occupy.

## 6. Next round

* **The documents past parity, re-posed.** If the owner still wants the
  document vector rankings past the raw vector, the ceiling says where the
  room is: in the first two layers, not a third. Two candidates, neither
  declared: a structural book with fewer ties at the boundary (finer
  coordinates), or a relevance relation that is not the tree, so that a tree
  book stops being the answer — for example a held-out set of
  owner-judged related sections.
* **N5 and I3** remain round 9's next items: the native word ranking with the
  part letter words as its first layer, and the Python AST address indexed
  beside the Lean corpus.
* **The snapshot as a fixture.** `tools document-tree --freeze` is cheap
  (about a second); a later document-ranking round can freeze its own corpus
  the same way before it declares.
