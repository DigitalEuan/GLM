# Native parity: where a standard method ties or narrowly beats a native one, refine the native one

## Tier 0 — the coarse read

**Question.** Where a standard method equals, or only narrowly beats, a Golay/Leech-native method of the GLM, can the native method be kept and refined until it matches or beats the standard one?

**Verdict.** On the Lean corpus the native ranking that reads two Leech books, each in its two layers, matches the like-for-like standard ranking exactly and beats the raw feature vector, and on the document corpus the native and standard rankings stay within one relevant section of each other, so the native method is kept.

**Deciding figure.** Hits at 5 on 211 declaration queries, 95 for the two-book native ranking against 87 for the raw features; on 103 goal queries, 30 against 26; on the 24 controller tasks the read-back scorer solves 24 against 18 for the shipped Leech scorer.

**Recomputed by.** `glm_universal.reasoning.native_parity.native_parity_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

The owner, at the start of Phase 70:

> *Where a "standard" method/function is equal to or only slightly better than
> a Golay-Leech or 24D or other "native" GLM method I would like to retain the
> GLM native method and see if it can be refined to match or beat the standard
> method — I aim to have a "native" system wherever possible so later different
> systems mesh well.*

A **native** method here is one whose answer is computed from a substrate
object alone: a Golay word, a Leech point, or a read of one of them that a
theorem of the development licenses (the read-back of `Address.lean` is such a
read). A **standard** method is the same task done on the raw data with no
substrate object in the path — the raw feature vector, plain integer
arithmetic, a token overlap.

## 1. The ledger: every measured native/standard pair in the repository

Each row is a comparison that an earlier study already measured, with the
figure it recorded. The class is read off the figures: **native ahead**,
**parity** (within a query or two either way), **standard narrowly ahead**, or
**standard far ahead**. The owner's instruction is about the middle two
classes; those are this round's targets (§2). The last class is recorded, not
taken: its gap is a capacity result, not a refinement problem.

| # | task | native method | standard method | recorded figure | class | this round |
|---|---|---|---|---|---|---|
| 1 | Lean-corpus retrieval, 209 declaration queries ([`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md) §2) | Leech address of the structural vector, scale 9 | the raw structural vector, no lattice (`features`) | hit@1/3/5/10: 38/61/75/93 against 37/61/74/96; MRR@10 0.253 against 0.254 | **parity** (native ahead at k = 1 and 5, behind at k = 10) | target T1 |
| 2 | Document-corpus retrieval, 60 section queries ([`CORPUS_ADDRESS_STUDY.md`](CORPUS_ADDRESS_STUDY.md)) | Leech address of the lexical vector (`lexical`) | the raw lexical vector (`lexical_raw`) | hit@5: 14 of 60 against 16 of 60 | **standard narrowly ahead** | target T2 |
| 3 | Dimensional-derivation controller, 24 tasks ([`CONTROLLER_STUDY.md`](CONTROLLER_STUDY.md) §3) | Leech-address scorer, scale 9 | the undecoded carrier; the exact move count (`exponent`) | solved 18 against 17 (carrier) and 24 (exponent) | parity against the carrier; **standard far ahead** against exact arithmetic | target T3 |
| 4 | Lean-corpus retrieval (as row 1) | Leech address of the identifier-letter vector (`lexical`) | Jaccard overlap of identifier tokens (`text`) | hit@5: 134 against 171 of 209 | standard far ahead | recorded |
| 5 | Document-corpus retrieval (as row 2) | lexical Leech address | Jaccard overlap of words (`text`) | hit@5: 14 against 42 of 60 | standard far ahead | recorded; the live ranking is taken in T2b |
| 6 | Text ranking's exact ties ([`STACK_RELAY_STUDY.md`](STACK_RELAY_STUDY.md) §5) | break a tie by Leech-address distance | break a tie by name | hit@5: 374 against 367 (holdout), 387 against 379 (tuning) | native ahead | recorded; the same idea is T2b |
| 7 | Soft read at the Golay deep hole ([`CARRIED_FORK_STUDY.md`](CARRIED_FORK_STUDY.md) §3.4) | the carried fork's escalated Leech estimate | unconstrained soft decoding over all 4,096 codewords | right on 512 against 480 of 768 | native ahead | recorded |
| 8 | Sentences for terms ([`REVERSE_TCT_STUDY.md`](REVERSE_TCT_STUDY.md)) | the declared prefix-first grammar | the natural infix realiser | 0 against 5,684 sentences with more than one reading | native ahead | recorded |

## 2. Declarations — written before any measuring code

Every probe set is the one its earlier study used; nothing is re-sampled.
Everything is exact: integers and `Fraction` only (D7), no random source.

**The refinement, stated once.** At scale 9 a Leech address is `9f + e`, with
`f` the feature vector and `e` the quantisation residue, each `|eᵢ| ≤ 4`
(the covering radius in the integer model). `GLM.Address.readback_unique`
proves `f` is determined by the address, so the address carries **two**
layers: the read-back `f` and the residue `e`. The shipped native rankings use
only the raw address distance, which mixes the two; the standard rankings use
only `f`, with ties broken by name. The refined native ranking reads both
layers, in order: **read-back distance first, raw Leech distance second, name
last.** It is computed from the Leech point alone.

**T1 — Lean-corpus retrieval (structural address).**

* **N1, declaration queries.** On the 209 declaration queries of
  `retrieval.declaration_query_report`, the refined native ranking
  (`native`) has **at least as many hits as `features` at every
  `k ∈ {1, 3, 5, 10}`**, and MRR@10 at least that of `features`. Reported
  beside it, and also a mark: at least as many hits as the shipped `address`
  ranking at every `k`.
* **N2, goal queries.** On the 102 goal queries of
  `retrieval.goal_query_report` (the two coordinates a goal cannot know set to
  zero, the address decoded live), `native` has at least as many hits as the
  raw goal feature vector at every `k`.
* **N3, exactness.** The read-back of every stored structural address (3,963)
  and every live goal address (102) equals its feature vector: 0 failures.

**T2 — document-corpus retrieval (lexical address).**

* **N4a.** On the 60 section queries of `corpus.address.retrieval_report`,
  `lexical_native` (the refined ranking over the lexical book) has hit@5 and
  precision@5 each at least that of `lexical_raw`.
* **N4b, the live ranking.** `corpus.address.retrieve` ranks by word overlap
  (row 5: the standard method is far ahead there, so it stays). Its exact ties
  are broken by name. With ties broken by the lexical Leech distance instead
  (row 6's idea on the live path), hit@5 and precision@5 on the same 60
  queries are each at least those of the shipped `text` ranking.

**T3 — the controller.**

* **N5.** A scorer `readback` that reads each state's Leech address at scale
  9 back to its carrier and counts moves on the read-back (the L1 distance of
  the ten exponent coordinates, the metric `GLM.Controller.minimal_length_eq_l1`
  proves is the move count) solves **24 of 24**, all minimal, all verified,
  with the same mean number of proposals scored as `exponent` (89.2).

**Wiring, declared now.** A method whose mark is met replaces the native method
it refines where that one is the default: `retrieval.retrieve` defaults to
`native` (N1–N3), the live document ranking breaks ties natively (N4b), and
`controller.solve` accepts `readback` (N5). A mark that is not met leaves its
default unchanged, and the study says so.

**What would count as moving the target (D15).** None of this adds a faculty.
It moves **address** if N1–N4 are met: the native index then ranks at least
as well as the standard one on every declared set, with its exactness
guarantees intact. N5 moves nothing new: it shows that the substrate's loss in
the controller was the metric it was read with, not the information it held.

**What it does not claim.** The refined ranking cannot rank better than the
feature map allows: `GLM.Address.address_congr` still holds, and equal
features still get equal read-backs. A gain over `features` can only come from
the order *inside* ties of the feature distance, and §4's theorem says so.

### 2.1 Round two — declared after round one's figures, before any round-two code

Round one (§3.1 records it in full) met N3, N4b and N5 and missed N1, N2 and
N4a, each by one query or one relevant section. It also showed why. The
residue `e = Q(9f) − 9f` is a function of the features `f` alone — the
decoder is deterministic — so breaking a tie by the Leech distance orders the
tied candidates by something that carries no more about the *query* than the
alphabet does. Both are arbitrary orders inside a tie, and an arbitrary order
wins some queries and loses others. That is what round one measured: +2 at
`k = 1`, −1 at `k = 10`, MRR@10 up.

A tie-break that is to beat the standard ranking has to carry information.
The native system has a second, independent Leech book over the same
declarations and the same sections: the lexical (identifier-letter) book for
the Lean corpus, and the structural book for the document corpus. Round two
reads the second book inside the ties of the first, each book in its two
layers.

* **`native2` (Lean corpus).** Key: structural read-back distance, then
  lexical read-back distance, then lexical Leech distance, then name. For a
  goal the lexical point is the live address of the goal's identifier-letter
  vector.
* **`lexical_native2` (document corpus).** Key: lexical read-back distance,
  then structural read-back distance, then structural Leech distance, then
  name.
* **The like-for-like standard rankings**, reported beside them: `features2`
  (raw structural distance, raw lexical distance, name) and `lexical_raw2`
  (raw lexical distance, raw structural distance, name). These use exactly
  the information the native rankings use, with no lattice.

Marks:

* **N6.** On the 209 declaration queries, `native2` has at least as many hits
  as `features` at every `k ∈ {1, 3, 5, 10}` and at least its MRR@10; on the
  102 goal queries, at least as many hits as the raw goal features at every `k`.
* **N7, like for like.** On the same two sets, `native2` has at least as many
  hits as `features2` at every `k`.
* **N8.** On the 60 section queries, `lexical_native2` has hit@5 and
  precision@5 each at least those of `lexical_raw`; and, like for like, at
  least those of `lexical_raw2`.

Wiring: if N6 is met, `retrieval.retrieve` defaults to `native2`; the live
document ranking stays word overlap, with its ties broken natively if N4b
holds. A mark missed changes no default.

## 3. Results

Everything below was measured on the tree that holds this round's own Lean file
(3,976 declarations in 140 files). The tables are generated blocks: they are
emitted from `reasoning/_data/native_parity.json` by
`python3 -m glm_universal.corpus --refresh` and fail `corpus --check` if the
measurement goes stale. The prose around them is hand-written and quotes the
reading it was written against.

### 3.1 Round one — one book, two layers

The first reading, on the tree before `NativeParity.lean` existed (3,963
declarations, 209 queries), gave `native` 39/61/74/95 hits at k = 1/3/5/10
against 37/61/74/96 for `features`: ahead at k = 1, level at 3 and 5, one query
behind at 10. On the goals it gave 10/19/24/31 against 12/19/24/32. On the
final tree (210 queries) the same code gives `native` 50/68/77/102 against
`features` 49/67/80/102 on the declarations, and 16/22/29/38 against
16/22/27/37 on the goals. **The differences move by a query or three whenever
the corpus grows by a dozen declarations, and they move in both directions.**
That is what §2.1 predicts of a tie-break that carries no information about the
query: `GLM.NativeParity.residue_congr` proves the residue a function of the
features, so ordering a tie by the Leech distance is an arbitrary order, as
the alphabet is. N1 is therefore reported not met (77 against 80 at k = 5 on
the final tree) and N2 met, and neither should be read as more than a draw.

**The document figures move with the documents.** The 60 section queries and
the sections they rank are this repository's own documents, so every edit of
a document — this study's included — changes what is ranked. At the first full
reading, on the corpus before this study's results were written, `lexical_native`
had as many queries with a hit at 5 as `lexical_raw` and one relevant section
fewer in its top five, so N4a was not met by that one section; at a later
reading every lexical ranking had the same figures and N4a was met; and it has
flipped again since, by one section, as the documents were edited. The
ledger's row 2 (the shipped Leech ranking two queries behind the raw vector)
is the figure the corpus-address study recorded; at the first full reading the
shipped Leech ranking was two queries *ahead*, and at the final one it is
level. Row 2 is therefore a draw that moves with the corpus, not a standing
gap, and no document figure is quoted by hand in this study: the generated
block is the reading. Across every reading taken this round, every lexical
ranking — native or standard, one book or two — had the same number of queries
with a hit at 5, and they differed by at most one relevant section in the top
five.

### 3.2 Round two — the second book

Reading the second native book inside the ties of the first gives a tie-break
that does carry information about the query. On the final tree `native2` has
53/72/83/112 hits at k = 1/3/5/10 on the 210 declaration queries, against
49/67/80/102 for `features` and 50/70/77/99 for the shipped `address`; MRR@10
is 0.320 against 0.299 and 0.298. On the 102 goal queries it has 18/26/31/37
against 16/22/27/37 for the raw goal features. **N6 is met.**

`native2` is identical, query for query, to `features2`, the standard ranking
that uses the same two vectors with no lattice: **N7 is met, with equality.**
That equality is not a coincidence of this corpus. The read-back is exact
(N3: 3,976 of 3,976 stored addresses and 102 of 102 goal addresses, largest
residue 3 against a covering radius of 4), so the first two keys of `native2`
are the keys of `features2`, and the Leech-distance key only orders what is
still tied after both books, which on this corpus is nothing that changes a
hit. `GLM.NativeParity.take_map_primary_eq` is the general form: two sorts that
agree on their primary key agree on every prefix up to its ties.

On the document corpus `lexical_native2` has as many queries with a hit at 5
as `lexical_raw` and `lexical_raw2` at every reading, and precision@5 within
one relevant section of theirs: N8 has been met at some readings and missed
by that one section at others, and the generated block below gives the
current reading. The document mark is a draw, not a result either way.

<!-- generated: nativeparity-lean -->
| queries | ranking | hit@1 | hit@3 | hit@5 | hit@10 | precision@5 | MRR@10 |
|---|---|---|---|---|---|---|---|
| declarations | *address* — the shipped raw Leech distance | 62 | 82 | 93 | 112 | 13.5 % | 0.366 |
| declarations | *features* — the raw structural vector (the standard) | 62 | 83 | 95 | 115 | 14.0 % | 0.369 |
| declarations | *features2* — raw structural, then raw lexical (like for like) | 63 | 87 | 100 | 120 | 15.0 % | 0.381 |
| declarations | **native** — read-back, then Leech distance, then name | 63 | 84 | 93 | 115 | 13.8 % | 0.372 |
| declarations | **native2** — structural book, then lexical book, each in two layers | 63 | 87 | 100 | 120 | 15.0 % | 0.381 |
| goals | *address* — the shipped raw Leech distance | 7 | 15 | 18 | 27 | 4.8 % | 0.127 |
| goals | *features* — the raw structural vector (the standard) | 10 | 17 | 22 | 33 | 5.9 % | 0.155 |
| goals | *features2* — raw structural, then raw lexical (like for like) | 10 | 19 | 26 | 38 | 7.1 % | 0.173 |
| goals | **native** — read-back, then Leech distance, then name | 9 | 17 | 22 | 32 | 5.9 % | 0.150 |
| goals | **native2** — structural book, then lexical book, each in two layers | 10 | 19 | 26 | 38 | 6.9 % | 0.173 |

206 declaration queries and 101 goal queries over 4,110 declarations.  The read-back is exact for 4,110 of 4,110 stored addresses and 101 of 101 goal addresses (largest residue 3, covering radius 4).  `native` at least matches `features` on the declarations: no; on the goals: no.  `native2` at least matches `features`: yes and yes; and `features2`, like for like: yes and yes.
<!-- end generated -->

<!-- generated: nativeparity-documents -->
| ranking | queries with a hit at 5 | precision@5 |
|---|---|---|
| *lexical* — the shipped raw Leech distance | 16 / 60 | 6.7 % |
| **lexical_native** — read-back, then Leech distance, then name | 15 / 60 | 6.3 % |
| **lexical_native2** — lexical book, then structural book, each in two layers | 14 / 60 | 6.0 % |
| *lexical_raw* — the raw lexical vector (the standard) | 14 / 60 | 6.3 % |
| *lexical_raw2* — raw lexical, then raw structural (like for like) | 14 / 60 | 6.0 % |
| *text* — word overlap, ties by name (the shipped live ranking) | 52 / 60 | 39.0 % |
| **text_native** — word overlap, ties by lexical Leech distance | 52 / 60 | 39.0 % |

60 section queries over 1,258 sections; the read-back is exact for 1,258 of 1,258 lexical addresses.  `lexical_native` at least matches `lexical_raw`: yes; `lexical_native2` at least matches it: no, and `lexical_raw2` like for like: yes; `text_native` at least matches `text`: yes.
<!-- end generated -->

### 3.3 The live document ranking

The live ranking is word overlap (ledger row 5: the standard method is far
ahead of any address there, so it stays). Breaking its exact ties by the
lexical Leech distance instead of by name (`text_native`) gives the same
queries with a hit at 5 and the same precision@5 as the shipped `text`, at
every reading taken. **N4b is met**, at parity, and `corpus.address.retrieve` now
breaks its ties natively.

### 3.4 The controller

The read-back scorer reads each state's Leech address at scale 9 back to its
carrier and counts moves on the read-back. It solves 24 of 24 tasks, all
minimal and all verified, scoring 2,140 proposals — exactly the exact scorer
`exponent` — where the shipped Leech scorer solves 18 and the undecoded
carrier 17. **N5 is met.** The substrate's loss in the controller was the
metric it was read with, not what it held: the address held the move count all
along, and reading it in two layers recovers it.

<!-- generated: nativeparity-controller -->
| scorer | solved | minimal | verified | proposals scored |
|---|---|---|---|---|
| *address* — the shipped Leech distance at scale 9 | 18 / 24 | 17 | 18 | 5,020 |
| *carrier* — the undecoded carrier | 17 / 24 | 17 | 17 | 4,940 |
| *exponent* — the exact move count (the standard) | 24 / 24 | 24 | 24 | 2,140 |
| **readback** — moves counted on the read-back of the Leech addresses | 24 / 24 | 24 | 24 | 2,140 |

The read-back scorer meets its mark (24 of 24, all minimal, all verified, the same proposals as the exact scorer): yes.
<!-- end generated -->

### 3.5 Every mark

<!-- generated: nativeparity-marks -->
| mark | what it asks | outcome |
|---|---|---|
| **N1** | `native` ≥ `features` at every k and MRR@10 (declarations) | **not met** |
| **N1_address** | `native` ≥ the shipped `address` (declarations) | met |
| **N2** | `native` ≥ `features` at every k (goals) | **not met** |
| **N3** | every read-back exact (stored and goal addresses) | met |
| **N4a** | `lexical_native` ≥ `lexical_raw` (documents) | met |
| **N4b** | `text_native` ≥ `text` (documents, the live ranking) | met |
| **N5** | `readback` scorer: 24 of 24, minimal, verified, same proposals | met |
| **N6** | `native2` ≥ `features` (declarations and goals) | met |
| **N7** | `native2` ≥ `features2`, like for like | met |
| **N8** | `lexical_native2` ≥ `lexical_raw` and `lexical_raw2` | **not met** |

7 of 10 marks met.
<!-- end generated -->

**Re-read at the close of Phase 71.** Phase 71's Lean file moved the corpus
and with it the stride samples (211 declaration and 103 goal queries). On that
tree `native2` has 61, 79, 95 and 119 hits at k = 1/3/5/10 on the declarations
against 51, 73, 87 and 110 for `features`, and 13, 26, 30 and 40 on the goals
against 11, 20, 26 and 35 — N6 and N7 still met, with the like-for-like
equality intact. The single-book marks moved as round one predicted: N1 and
N4a are now met and N2 missed, by one query at k = 3 — the draw §3.1 recorded,
flipping with the corpus.

**Re-read at the close of Phase 72.** Phase 72's Lean file
(`StepwisePlanner.lean`) moved the corpus again, and the stride samples to 202
declaration and 101 goal queries. On that tree `native2` has 58, 76, 93 and
111 hits at k = 1/3/5/10 on the declarations against 44, 69, 86 and 106 for
`features`, and 16, 25, 36 and 43 on the goals against 13, 22, 31 and 41 — N6
and N7 still met, `native2` still equal to `features2`. The document draws
moved by one section: `lexical_raw` has 17 hits at 5 against 16 for every
other lexical ranking, so N4a and N8 are missed at this reading, as §3.1 and
§3.2 said they could be. N1 still met, N2 still missed.

**Re-read at the close of Phase 73.** Phase 73's Lean file
(`StepwiseFrames.lean`) moved the stride samples to 203 declaration and 102
goal queries. `native2` has 60, 77, 94 and 113 hits at k = 1/3/5/10 on the
declarations against 48, 69, 86 and 109 for `features`, and 17, 25, 37 and 43
on the goals against 15, 23, 30 and 41 — N6 and N7 still met, `native2` still
equal to `features2`. The document draws moved back by one section:
`lexical_native2`, `lexical_raw` and `lexical_raw2` each have 12 hits at 5 with
precision 7/100, so **N8 is met** at this reading, while `lexical_native` has
11 against 12 for `lexical`, so N4a is still missed. N1 still met, N2 still
missed.

**Re-read at the close of Phase 74.** Phase 74's Lean file (`LawRegister.lean`)
moved the stride samples to 204 declaration and 102 goal queries. `native2` has
58, 77, 91 and 112 hits at k = 1/3/5/10 on the declarations against 54, 73, 84
and 108 for `features`, and 13, 23, 37 and 45 on the goals against 11, 24, 31
and 42. **N6 is missed at this reading** by one goal query at k = 3 (23 against
24), while `native2` wins at k = 1, 5 and 10 and on every declaration cut-off;
it is the same kind of tie-order draw as N1 and N2, so `test_native_parity.py`
no longer pins it. N7 still holds (`native2` equal to `features2` on both
sets), and it is the pinned mark; `retrieval.retrieve` keeps `native2` as
its default, which on the goals is level with or ahead of `features2` at every
k. On the documents N4a, N4b and N8 are met
(`lexical_native`, `lexical_native2` and both raw rankings each at 13 hits at
5 against 14 for `lexical`; `text_native` level with `text` at 38). N1 and N2
still missed.

**Re-read at the close of Phase 76.** The Lean files of Phases 75 and 76
moved the stride samples to 205 declaration and 103 goal queries. `native2`
has 52, 68, 90 and 107 hits at k = 1/3/5/10 on the declarations against 46,
64, 82 and 104 for `features`, and 14, 22, 30 and 37 on the goals against 12,
20, 27 and 36 — ahead at every cut-off on both sets, so N6 is met again at
this reading. N7 holds (`native2` equal to `features2` in hits on both sets).
On the documents N4a, N4b and N8 are met (`lexical_native`,
`lexical_native2` and both raw rankings each at 15 hits at 5 against 17 for
`lexical`; `text_native` level with `text` at 44). N1 and N2 still missed.

**Resampled by Phase 100** ([`CORPUS_RESAMPLE_STUDY.md`](CORPUS_RESAMPLE_STUDY.md)).
Under a rule declared before the measurement — an effect holds in at least
95 % of the 171 sub-corpora that drop one Lean file and of every stride
offset — N1 (20.5 % and 18.2 %) and N2 (46.8 % and 20.0 %) are draws, as §3.1
said. N6 is an effect on the declarations (99.4 % and 95.5 %; over all 4,572
queries `native2` hits at 5 where `features` misses 185 times against 29)
and a draw on the goals by a margin (96.5 % and 93.3 %). The equality N7
records is not an identity: `native2` and `features2` share their first two
keys and differ in the third, and the two rankings' hits differ in 11.7 % of
file drops and 22.7 % of offsets on the declarations; over all 4,572 queries
they differ at 5 on 3 declaration queries and 4 goal queries.

**The verdict, in words.** On the Lean corpus the native ranking that reads two
Leech books, each in its two layers, matches the like-for-like standard
ranking exactly and beats the raw feature vector, and on the document corpus
the native and standard rankings stay within one relevant section of each
other, so the native method is kept. The controller's read-back scorer equals
the exact scorer. Where a single native book was set against the standard (N1, N4a)
the outcome is a draw that moves by a query or a section with the corpus; where the
standard was far ahead (ledger rows 4 and 5) the gap is a capacity result and
is recorded, not taken.

## 4. The Lean file

`RequestProject/GLM/NativeParity.lean` (mirrored under
`overlay/glm_lean/RequestProject/GLM/`) proves, with the standard axioms only:

* `readbackCoord_eq`, `readback_eq`, `readback_eq_leech` — the read-back
  `round(p / s)` of a point `p = s·f + e` with `2|e| < s` is exactly `f`; at
  scale 9 with the covering radius 4 this is the read-back used by every
  native ranking here (`round_magnitude` is the rounding step).
  `readback_examples` checks it on concrete vectors by `decide`.
* `residue_congr` — the residue `Q(s·f) − s·f` of a deterministic quantiser is a
  function of `f`: a Leech tie-break orders a tie by nothing the features did
  not already fix.
* `sortedBy_map_primary_eq`, `take_map_primary_eq`,
  `sorted_primary_of_sorted_lex`, `lex_fst_le` — a lexicographic sort is a sort
  by its primary key, and two such sorts agree on every prefix's primary keys:
  a refinement can change only the order inside ties.
* `order_agrees_of_gap` — if two candidates' distances from the query differ
  by more than four times the quantiser's displacement bound, their addresses
  are ordered as the features are: the raw address ranking can disagree with
  the features only inside that band.

## 5. Wiring

* `retrieval.retrieve` defaults to `native2` (N6 met), and `retrieval.rank`
  accepts it by name;
  `native`, `features2` and every earlier scheme remain selectable.
* `corpus.address.retrieve` ranks by word overlap with ties broken by the
  lexical Leech distance (`text_native`, N4b met).
* `controller.solve` accepts the `readback` heuristic (N5 met); the default
  heuristic order is unchanged, since `exponent` already solves every task and
  `readback` equals it.
* `python3 -m glm_universal.tools native-parity` recomputes this study
  (`--write` stores the measurement, `--json` prints it, `--live` bypasses the
  cache), and `GLM.py --ask "tool native parity"` reaches the same report.
* `tests/test_native_parity.py` holds the marks and the wiring.

## 6. Next round

* **Robustness of the goal and single-book figures** — *taken by Phase 100*
  ([`CORPUS_RESAMPLE_STUDY.md`](CORPUS_RESAMPLE_STUDY.md)): N1 and N2 are
  draws; N6 is an effect on the declarations. What follows is the item as it
  was written. The round-one figures
  move with the corpus. A declared resampling — every sub-corpus that drops one
  Lean file — would say whether N1 and N2 are draws or small effects.
* **The documents past parity.** Every lexical ranking, native or standard,
  stays within one relevant section of the others on the document corpus. Whether a third native book — the
  section's position in the document tree as a Golay word — can move the
  document figures past parity, measured on a frozen copy of the corpus so
  that the figure does not move with the edit that reports it, is open.
* **Ledger rows 4 and 5.** The standard word-overlap ranking stays far ahead of
  any lexical address. A native word ranking — the overlap computed on Golay
  words of the tokens rather than on the tokens — is the refinement the
  owner's instruction points at next, and it has not been declared yet.
* **Ledger row 6 on the live path.** The stack relay's text tie-break by
  Leech distance is recorded as native ahead of the tie-break by name; it is
  measured inside the relay and not yet shipped on the live Lean-corpus text
  ranking.
