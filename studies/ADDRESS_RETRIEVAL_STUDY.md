# The address layer, made to do work: retrieval, measured against its controls


## Tier 0 — the coarse read

**Question.** Can the Leech address book retrieve the declarations relevant to a question, and does it beat its controls?

**Verdict.** The address is a real index, and it is beaten decisively by plain text.

**Deciding figure.** Hit@5 of 40.0 % against 5.9 % for chance, with the text control at 85.7 %.

**Recomputed by.** `glm_universal.reasoning.retrieval.retrieval_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**What this document is.**
[`LEAN_ADDRESS_STUDY.md`](LEAN_ADDRESS_STUDY.md) built an address book: every
declaration of the Lean development reduced to twenty four integer counts,
scaled by nine, sent to its nearest Leech point, and read back exactly. It
measured that *nearest by address* shares a source file many times more often
than chance. That is a fact about a table. It is not yet a faculty: nothing in
the system used the address to answer anything.

This study closes that gap and then asks the only question that decides whether
the substrate has earned a functional role:

> Given a question — a declaration, or a bare Lean goal — can the address book
> **retrieve** the declarations relevant to it, and does it beat the controls
> the house style requires: a name search, a digest, a reshuffle, chance, and
> the one control that matters most, *a plain lexical search over the statement
> text*?

The answer, stated before the tables so that nothing here reads as a defence of
a preferred result:

1. **The address is a real index.** At `k = 5` it finds a relative for
   **40.0 %** of queries against **5.9 %** for chance — **6.8×** — and it beats
   the digest control (4.8 %), the seeded reshuffle (5.7 %), the random ranking
   (5.7 %) and name-substring search (34.8 %).
2. **And it is beaten decisively by plain text.** Jaccard overlap of identifier
   tokens between the query and the candidate statements finds a relative for
   **85.7 %** of the same queries, at **58.7 %** precision against the address's
   **12.7 %**.
3. **The lattice is not what carries the signal.** Ranking on the raw feature
   vectors, with no quantisation at all, scores **40.5 %** against the address's
   40.0 %. The two differ only where the quantiser rounds near-equal distances
   apart: the address is behind by one query at `k = 1` (43 against 44) and at
   `k = 5` (84 against 85), ahead by one at `k = 10` (110 against 109), and
   precision@5 differs by a tenth of a point (12.7 % against 12.8 %). The
   geometry transports the features faithfully; it does not add to them, and on
   the present stride it is a query behind them rather than a query ahead.
4. **Giving the geometry the words helps, and is still not enough.** A second
   address scheme built from the statement's *identifiers* rather than its
   syntax — counted by initial letter into the same 24 coordinates and
   quantised the same way — reaches **62.4 %**. Better than the structural
   address by twenty points, worse than the text control by twenty.
   The limit is the projection to 24 capped integers, not the choice of what to
   put in them.
5. **An address shortlist does not even make the text search cheaper for free.**
   Pruning to the nearest 800 by address (23.9 % of the corpus) and then ranking
   by text gives 84.3 %; at 1.5 % of the corpus it gives 64.8 %. Every
   shortlist costs accuracy. There is no free filter here.
6. **What the lattice does earn is exactness.** The completeness bound of
   `GLM/Retrieval.lean` holds on **170,850** measured pairs with **zero**
   violations, and at feature radius 2 the guaranteed-complete shortlist is
   **94.4** declarations — **2.8 %** of the corpus — containing all **20.9**
   feature-close declarations on average. An empty shortlist is a *proof* of
   absence. That is a functional role, and it is a different one from
   "the geometry knows what a theorem is about".

Every table below is a **generated block**: it is emitted from the measurement
cache that `python3 -m glm_universal.corpus --remeasure` fills, guarded by the
digest of the Lean sources it was taken from. When the development moves, a
block reports staleness rather than printing a figure from a tree that has
changed.

The formal half is
[`RequestProject/GLM/Retrieval.lean`](../RequestProject/GLM/Retrieval.lean),
the computational half is `glm_universal.reasoning.retrieval`, the test that
pins the two against each other is
`overlay/glm_universal/tests/test_retrieval.py` (42 tests, 399 subtests), and
the report prints with

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report retrieval" --verify-tct
```

whose third column re-derives every figure below in a fresh interpreter.

---

## 1. The experiment

**The corpus and the queries.** The declarations are addressed in
`reasoning/_data/lean_addresses.json` (structural) and
`reasoning/_data/lean_lexical_addresses.json` (lexical). Both files carry the
SHA-256 digest of the Lean tree they were computed from; a single changed byte
makes them `stale` and the report says so rather than answering from them. The
queries are taken by a stated stride through the address book's order — not a
seeded sample — and the goal experiment uses a coarser stride, because it
decodes a fresh Leech point per query.

<!-- generated: retrieval-setup -->
All **3,383** declarations of the Lean development are the corpus.  The declaration experiment uses **212** queries and the goal experiment **103**, each with at least one relative; the mean query has **40.5** relatives among the 3,382 other declarations.  None of the 103 goal queries reproduces its own stored feature vector (0 of 103), so a goal address is held out every time.
<!-- end generated -->

**What counts as a hit.** A retrieved declaration is *relevant* when it is a
**relative** of the query: same source file, or joined to it by a citation in
either direction. Neither relation appears anywhere in either feature map — the
address knows no file names and no citation directions — so "the neighbours are
relatives" is a prediction that can fail. The mean query has **39.9**
relatives among the other 3,186 candidates.

**Chance** is computed in closed form, not simulated:
`1 − C(m−r, k)/C(m, k)` per query, averaged exactly over the queries.

---

## 2. Declaration queries: the eight schemes side by side

The query is a declaration; the scheme ranks the other 3,186; a hit is a
relative in the top `k`.

<!-- generated: retrieval-declarations -->
| scheme | hit@1 | hit@3 | hit@5 | hit@10 | precision@5 | MRR@10 |
|---|---|---|---|---|---|---|
| **address** — Leech address of the structural feature vector | 43 (20.3 %) | 70 (33.0 %) | 86 (40.6 %) | 110 (51.9 %) | 12.6 % | 0.289 |
| *features* — the same vector, no lattice (ablation) | 43 (20.3 %) | 73 (34.4 %) | 87 (41.0 %) | 109 (51.4 %) | 12.5 % | 0.292 |
| *lexical* — Leech address of the identifier-letter vector | 87 (41.0 %) | 120 (56.6 %) | 133 (62.7 %) | 155 (73.1 %) | 25.2 % | 0.503 |
| *text* — Jaccard overlap of identifier tokens (**the strong control**) | 152 (71.7 %) | 173 (81.6 %) | **182 (85.8 %)** | 188 (88.7 %) | 59.1 % | 0.774 |
| *name* — name-substring search | 41 (19.3 %) | 61 (28.8 %) | 75 (35.4 %) | 91 (42.9 %) | 13.8 % | 0.255 |
| *digest* — SHA-256 address (D3 control) | 3 (1.4 %) | 8 (3.8 %) | 10 (4.7 %) | 22 (10.4 %) | 0.9 % | 0.033 |
| *shuffled* — the feature addresses re-paired by a seeded permutation | 3 (1.4 %) | 8 (3.8 %) | 14 (6.6 %) | 23 (10.8 %) | 1.3 % | 0.037 |
| *random* — a seeded permutation of the corpus | 0 (0.0 %) | 5 (2.4 %) | 9 (4.2 %) | 21 (9.9 %) | 0.8 % | 0.021 |
| **chance**, in closed form | 1.2 % | 3.5 % | 5.8 % | 11.2 % | — | — |

212 queries of the 3,383-declaration corpus.  At k = 5 the structural address runs 6.99× closed-form chance; the text control beats the address: yes; the lattice matches the raw features: no.
<!-- end generated -->

Four readings, in the order of how much they matter.

**The address carries information.** Three controls — digest, reshuffle,
random — sit at chance or within a point or two of it, exactly as they should:
the digest knows the name and nothing else, the reshuffle has the same geometry
with the pairing destroyed, the random ranking never looks at the query. The
address is 6.8 times chance.
So the twenty four counts are not noise, and the address book is not a
decoration.

**The lattice is not the reason.** `features` is the same experiment with the
quantiser removed. It scores 40.5 % against the address's 40.0 % at `k = 5` — one
query ahead — is one query behind at `k = 10` (51.9 % against 52.4 %) and within
a tenth of a point on precision@5 (12.8 % against 12.7 %). Whatever separation
there is belongs to the feature map. This is exactly what `GLM.Address.address_congr`
predicts and what `GLM.Retrieval.retrieve_congr` restates for retrieval: the
address can make no distinction the feature map has not already made. The
measurement agrees with the theorem, which is the point of having both.

**A lexical search beats all of it.** The `text` control is not sophisticated —
it is the set of identifiers in the query against the set of identifiers in each
candidate, scored by exact Jaccard, which is what `grep` would do with better
book-keeping. It finds a relative first time for 72.2 % of queries. The
structural address does that for 24.4 %. On this task, the identifiers are what
locate a declaration, and the structural feature map throws them away by
design.

**So we gave the geometry the identifiers.** The `lexical` scheme is a genuine
second address book: each statement's distinct identifiers are counted by
initial letter into 24 buckets (a *stated, readable* projection — coordinate 7
is "how many identifiers begin with h" — not a digest, so directive D3 is
respected), capped at 12 as the structural vector is, and quantised to the
lattice by the same decoder. It scores 67.9 % — a large gain over the
structural address, and still 17 points behind the raw token sets it was built
from. Twenty four capped integers cannot hold what a set of identifiers holds.
That is a **capacity** result about the projection, not about the choice of
features, and it is the most useful thing this study learned.

---

## 3. Goal queries: the case the system will actually meet

A declaration query has an unfair advantage: its address is already in the book.
A *goal* query is a bare statement, and two of its coordinates — how many
results cite it, how deep its namespace sits — cannot be known. They are set to
zero. **None** of the goal queries reproduces its own stored feature vector, so
this is a genuinely held-out address every time.

<!-- generated: retrieval-goals -->
| scheme | hit@1 | hit@3 | hit@5 | hit@10 | precision@5 |
|---|---|---|---|---|---|
| address | 16 (15.5 %) | 23 (22.3 %) | 28 (27.2 %) | 34 (33.0 %) | 7.8 % |
| lexical | 32 (31.1 %) | 38 (36.9 %) | 53 (51.5 %) | 68 (66.0 %) | 19.6 % |
| text | 78 (75.7 %) | 89 (86.4 %) | 92 (89.3 %) | 93 (90.3 %) | 59.4 % |
| name | 18 (17.5 %) | 26 (25.2 %) | 32 (31.1 %) | 40 (38.8 %) | 12.6 % |
| digest | 0 (0.0 %) | 1 (1.0 %) | 5 (4.9 %) | 13 (12.6 %) | 1.0 % |
| random | 0 (0.0 %) | 2 (1.9 %) | 3 (2.9 %) | 6 (5.8 %) | 0.6 % |

103 goal queries, the two coordinates a goal cannot know set to zero.
<!-- end generated -->

The goal set is a coarser stride, so the rates are not paired with §2's
query-for-query; but read as two populations of the same corpus, the two
unknowable coordinates cost the structural address 12.5 points of hit@5
(40.0 % → 27.5 %) and the lexical scheme 13.4 (62.4 % → 49.0 %), while the text
control loses four tenths of a point (85.7 % → 85.3 %), because a goal *is* its
identifiers. The address still beats its digest and random controls — but on
goals it is now *behind* name-substring search at `k = 5` (27.5 % against
33.3 %), so the gap it has to close is wider in the case that matters.

---

## 4. Is the address at least a cheap filter?

If the text search is the better ranker, the address could still earn its place
by *pruning*: address-shortlist first, text-rank the survivors. That is the
standard architecture, and it is worth measuring rather than assuming.

<!-- generated: retrieval-hybrid -->
| shortlist | fraction of corpus | hit@5 | precision@5 |
|---|---|---|---|
| 50 | 1.5 % | 63.7 % | 25.4 % |
| 100 | 3.0 % | 70.3 % | 30.9 % |
| 200 | 5.9 % | 77.8 % | 37.3 % |
| 400 | 11.8 % | 79.7 % | 42.6 % |
| 800 | 23.6 % | 84.4 % | 49.0 % |
| **no shortlist** | 100 % | **85.8 %** | **59.1 %** |

Any shortlist beats the text control: no.
<!-- end generated -->

**No shortlist beats the text control, at any size.** The curve is monotone and
approaches the unpruned rate from below: the address ordering is positively
correlated with relevance — it is not throwing relatives away at random — but it
throws enough of them away that the pruning is never free. Recorded as a
negative result, in the same register as the 44 balanced octads and the
economic register's undecoded control.

---

## 5. What the lattice does earn: an exact, complete, certifiable shortlist

The theorems of
[`RequestProject/GLM/Retrieval.lean`](../RequestProject/GLM/Retrieval.lean)
survive every number above, because none of them is about hit rates.

| statement | what it says | Lean |
| --- | --- | --- |
| order independence | ranking a permuted corpus gives the same list; ties are broken by name, never by arrival | `ranked_eq_of_perm`, `topk_eq_of_perm` |
| prefix monotonicity | the top `k` is a prefix of the top `k'`; a hit at `k` is a hit at `k'` | `topk_prefix`, `hit_mono` |
| no invention | every returned candidate is in the corpus | `mem_topk` |
| certified absence | an empty radius shortlist *proves* nothing lies within the radius | `filterRadius_eq_nil_certifies_absence` |
| completeness | feature distance ≤ `r` implies address distance ≤ `r + 2ρ`, so a radius search over addresses never misses what a search over features would find | `complete_shortlist`, `address_dist_le` |
| congruence | equal features are answered identically — the index sees the features and nothing else | `retrieve_congr` |

The completeness bound is the one with teeth, and it is measured:

<!-- generated: retrieval-guarantee -->
| what was checked | result |
|---|---|
| pairs checked against `sqrt(address²) ≤ 9·sqrt(features²) + 2ρ`, ρ = 4 | **172,482** |
| violations | **0** |
| tightest observed slack | 64 (squared units) |
| guaranteed-complete shortlist at feature radius 2 | mean **109.9** declarations = **3.2 %** of the corpus |
| feature-close declarations it must contain | mean **25.6** |

Over 51 queries of the 3,383-declaration corpus.  The bound holds: yes.
<!-- end generated -->

So the address book is an exact spatial index with a proved recall guarantee:
it reduces a 3,186-declaration scan to 70.5 candidates while provably keeping
every declaration within the stated feature radius, and when it returns nothing
that emptiness is a theorem rather than a shrug. That is what the substrate is
contributing here — *addressing and exactness*, which is what it has always
been good at — and it is not semantic ranking.

---

## 6. Two worked queries

**`GLM.Address.address_congr`, by address.** The four nearest are
`GLM.Conjugate.rel_injective` (d² = 384),
`GLM.Completion.estimated_of_empty` (608),
`GLM.ModeAlgebra.definitionOk_is_a_function_of_dominant_role` (608) and
`GLM.Shell.shSum_eq` (608) — four theorems of the same *shape*: an injectivity
or an equality with a similar quantifier profile and a similar citation
degree, drawn from four different files. The address is doing precisely what
it was built to do, and none of them is a relative.

**The same query, by text.** `GLM.Address.ne_of_address_ne` (6/7),
`GLM.Address.conflates_symm` (11/15), `GLM.Retrieval.retrieve_congr` (11/17)
and `GLM.Address.injective_features_of_injective_address` (5/8) — three file
mates and the retrieval restatement that cites it. Four hits out of four.

The two answers are both correct answers to different questions. The address
answers "what else looks like this?"; the text answers "what else is about
this?". A proof-search wants the second.

---

## 7. What would falsify this

* **The negative result.** If a feature map exists that is a projection into
  24 capped integers and matches the text control on these queries, the
  capacity reading in §2 is wrong. The two tried here (syntactic, lexical) both
  fall short, one by 34 points and one by 17; a third that closes the gap would
  overturn the conclusion, and the harness scores any scheme that supplies a
  vector.
* **The positive result.** If the digest control or the seeded reshuffle ever
  rises to the address's rate, the experiment is measuring corpus structure
  rather than the feature map, and `test_retrieval.py` fails when it does.
* **The guarantee.** One pair violating `complete_shortlist` would mean the
  quantiser is not the quantiser the Lean file assumes; 162,486 pairs are
  checked on every run.
* **The hybrid.** If any shortlist size beat the text control, §4's conclusion
  reverses; the report computes that comparison itself and the test asserts the
  answer it finds.

---

## 8. What this says about the founding question

The project asks whether the Golay–Leech substrate can provide what is needed
to build a deterministic reasoning language machine. On the one experiment that
was in reach of deciding it — *does the geometry do the retrieval work* — the
answer measured here is:

**No, and precisely no.** The geometry supplies an exact, deterministic,
order-independent, provably complete index with a certified refusal, and it
transports whatever the feature map gives it without loss. It does not supply
the relevance. On this corpus the relevance lives in the identifiers, a
lexical search reads them directly, and a 24-coordinate projection of them —
however it is built, and however faithfully the lattice then carries it —
loses too much to compete.

That is worth having as a result rather than an impression. It says where to
spend the next effort: not on a better decoder, but on what is *put into* the
coordinates, and on the parts of the machine where exactness and certified
absence are the scarce commodity rather than ranking accuracy.

**What a later round did with this result.** Every number above was measured
with each faculty answering *alone* — which is the right way to ask whether the
geometry is an index, and the wrong way to ask whether it is worth having in a
machine that holds more than one faculty.
[`STACK_RELAY_STUDY.md`](STACK_RELAY_STUDY.md) asks the second question: it
lets each faculty declare how much evidence it has for the query at hand, and
hands the query to the geometry only where the lexical leader has none. The
negative result above is not overturned — the lexical search is still the
better single faculty, by a wide margin, and the relay *is* the lexical
ranking wherever the lexical search is confident (`relay_confident`). What
changes is the margin at the bottom: on the queries the leader cannot read, the
geometry carries 14 and loses 1, against 4 for a digest-and-reshuffle control
and 0 for a name search, and the stack finishes ahead of the leader on a tuning
stride, a disjoint held-out stride and a goal-query set alike.
