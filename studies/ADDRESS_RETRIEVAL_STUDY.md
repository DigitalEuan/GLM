# The address layer, made to do work: retrieval, measured against its controls

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
   **51.5 %** of queries against **6.9 %** for chance — **7.4×** — and it beats
   the digest control (3.5 %), the seeded reshuffle (6.9 %), the random ranking
   (5.9 %) and name-substring search (34.2 %).
2. **And it is beaten decisively by plain text.** Jaccard overlap of identifier
   tokens between the query and the candidate statements finds a relative for
   **85.6 %** of the same queries, at **57.7 %** precision against the address's
   **15.5 %**.
3. **The lattice is not what carries the signal.** Ranking on the raw feature
   vectors, with no quantisation at all, scores **51.0 %** — within half a point
   of the address's 51.5 %, and *better* on precision@5 (16.2 % against
   15.5 %). The geometry transports the features faithfully; it does not add to
   them.
4. **Giving the geometry the words helps, and is still not enough.** A second
   address scheme built from the statement's *identifiers* rather than its
   syntax — counted by initial letter into the same 24 coordinates and
   quantised the same way — reaches **64.9 %**. Better than the structural
   address by thirteen points, worse than the text control by twenty one. The
   limit is the projection to 24 capped integers, not the choice of what to put
   in them.
5. **An address shortlist does not even make the text search cheaper for free.**
   Pruning to the nearest 800 by address (28.3 % of the corpus) and then ranking
   by text gives 85.1 %; at 1.8 % of the corpus it gives 69.8 %. Every
   shortlist costs accuracy. There is no free filter here.
6. **What the lattice does earn is exactness.** The completeness bound of
   `GLM/Retrieval.lean` holds on **144,075** measured pairs with **zero**
   violations, and at feature radius 2 the guaranteed-complete shortlist is
   **70.9** declarations — **2.5 %** of the corpus — containing all **16.8**
   feature-close declarations on average. An empty shortlist is a *proof* of
   absence. That is a functional role, and it is a different one from
   "the geometry knows what a theorem is about".

The formal half is
[`RequestProject/GLM/Retrieval.lean`](../RequestProject/GLM/Retrieval.lean),
the computational half is `glm_universal.reasoning.retrieval`, the test that
pins the two against each other is
`overlay/glm_universal/tests/test_retrieval.py` (42 tests, 439 subtests), and
the report prints with

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report retrieval" --verify-tct
```

whose third column re-derives every figure below in a fresh interpreter.

---

## 1. The experiment

**The corpus.** All **2,826** declarations of the Lean development, addressed
in `reasoning/_data/lean_addresses.json` (structural) and
`reasoning/_data/lean_lexical_addresses.json` (lexical). Both files carry the
SHA-256 digest of the Lean tree they were computed from; a single changed byte
makes them `stale` and the report says so rather than answering from them.

**The queries.** Every 14th declaration in the address book's order — a stated
stride, not a seeded sample — giving **202** queries, each with at least one
relative. The goal-query experiment uses a coarser stride and **101** queries,
because it decodes a fresh Leech point per query.

**What counts as a hit.** A retrieved declaration is *relevant* when it is a
**relative** of the query: same source file, or joined to it by a citation in
either direction. Neither relation appears anywhere in either feature map — the
address knows no file names and no citation directions — so "the neighbours are
relatives" is a prediction that can fail. The mean query has **40.5**
relatives among 2,825 candidates.

**Chance** is computed in closed form, not simulated:
`1 − C(m−r, k)/C(m, k)` per query, averaged exactly over the queries.

---

## 2. Declaration queries: the eight schemes side by side

The query is a declaration; the scheme ranks the other 2,825; a hit is a
relative in the top `k`.

| scheme | hit@1 | hit@3 | hit@5 | hit@10 | precision@5 | MRR@10 |
| --- | --- | --- | --- | --- | --- | --- |
| **address** — Leech address of the structural feature vector | 61 (30.2 %) | 91 (45.0 %) | **104 (51.5 %)** | 123 (60.9 %) | 15.5 % | 0.389 |
| *features* — the same vector, no lattice (ablation) | 58 (28.7 %) | 84 (41.6 %) | 103 (51.0 %) | 124 (61.4 %) | 16.2 % | 0.379 |
| *lexical* — Leech address of the identifier-letter vector | 84 (41.6 %) | 113 (55.9 %) | 131 (64.9 %) | 151 (74.8 %) | 27.8 % | 0.508 |
| *text* — Jaccard overlap of identifier tokens (**the strong control**) | 142 (70.3 %) | 164 (81.2 %) | **173 (85.6 %)** | 180 (89.1 %) | 57.7 % | 0.767 |
| *name* — name-substring search | 42 (20.8 %) | 60 (29.7 %) | 69 (34.2 %) | 91 (45.0 %) | 15.4 % | 0.269 |
| *digest* — SHA-256 address (D3 control) | 1 (0.5 %) | 3 (1.5 %) | 7 (3.5 %) | 20 (9.9 %) | 0.7 % | 0.022 |
| *shuffled* — the feature addresses re-paired by a seeded permutation | 3 (1.5 %) | 10 (5.0 %) | 14 (6.9 %) | 28 (13.9 %) | 1.6 % | 0.043 |
| *random* — a seeded permutation of the corpus | 2 (1.0 %) | 6 (3.0 %) | 12 (5.9 %) | 20 (9.9 %) | 1.2 % | 0.031 |
| **chance**, in closed form | 1.4 % | 4.2 % | 6.9 % | 13.3 % | — | — |

Four readings, in the order of how much they matter.

**The address carries information.** Three controls — digest, reshuffle,
random — sit at chance, exactly as they should: the digest knows the name and
nothing else, the reshuffle has the same geometry with the pairing destroyed,
the random ranking never looks at the query. The address is 7.4 times chance.
So the twenty four counts are not noise, and the address book is not a
decoration.

**The lattice is not the reason.** `features` is the same experiment with the
quantiser removed. It scores 51.0 % against 51.5 % at `k = 5` — half a point,
one query — is *higher* at `k = 10` (61.4 % against 60.9 %) and *higher* on
precision@5 (16.2 % against 15.5 %). Whatever separation there is belongs to
the feature map. This is exactly what `GLM.Address.address_congr`
predicts and what `GLM.Retrieval.retrieve_congr` restates for retrieval: the
address can make no distinction the feature map has not already made. The
measurement agrees with the theorem, which is the point of having both.

**A lexical search beats all of it.** The `text` control is not sophisticated —
it is the set of identifiers in the query against the set of identifiers in each
candidate, scored by exact Jaccard, which is what `grep` would do with better
book-keeping. It finds a relative first time for 70.3 % of queries. The
structural address does that for 30.2 %. On this task, the identifiers are what
locate a declaration, and the structural feature map throws them away by
design.

**So we gave the geometry the identifiers.** The `lexical` scheme is a genuine
second address book: each statement's distinct identifiers are counted by
initial letter into 24 buckets (a *stated, readable* projection — coordinate 7
is "how many identifiers begin with h" — not a digest, so directive D3 is
respected), capped at 12 as the structural vector is, and quantised to the
lattice by the same decoder. It scores 64.9 % — a large gain over the
structural address, and still 21 points behind the raw token sets it was built
from. Twenty four capped integers cannot hold what a set of identifiers holds.
That is a **capacity** result about the projection, not about the choice of
features, and it is the most useful thing this study learned.

---

## 3. Goal queries: the case the system will actually meet

A declaration query has an unfair advantage: its address is already in the book.
A *goal* query is a bare statement, and two of its coordinates — how many
results cite it, how deep its namespace sits — cannot be known. They are set to
zero. **None** of the 101 goal queries reproduces its own stored feature
vector, so this is a genuinely held-out address every time.

| scheme | hit@1 | hit@3 | hit@5 | hit@10 | precision@5 |
| --- | --- | --- | --- | --- | --- |
| address | 15 (14.9 %) | 24 (23.8 %) | 29 (28.7 %) | 44 (43.6 %) | 9.3 % |
| lexical | 36 (35.6 %) | 51 (50.5 %) | 57 (56.4 %) | 61 (60.4 %) | 19.2 % |
| text | 71 (70.3 %) | 86 (85.1 %) | 89 (88.1 %) | 93 (92.1 %) | 57.4 % |
| name | 22 (21.8 %) | 28 (27.7 %) | 33 (32.7 %) | 43 (42.6 %) | 16.6 % |
| digest | 1 (1.0 %) | 2 (2.0 %) | 6 (5.9 %) | 8 (7.9 %) | 1.2 % |
| random | 1 (1.0 %) | 3 (3.0 %) | 5 (5.0 %) | 8 (7.9 %) | 1.0 % |

The goal set is a coarser stride, so the rates are not paired with §2's
query-for-query; but read as two populations of the same corpus, the two
unknowable coordinates cost the structural address 22.8 points of hit@5
(51.5 % → 28.7 %) and the lexical scheme 8.5 (64.9 % → 56.4 %), while the text
control loses nothing at all (85.6 % → 88.1 %), because a goal *is* its
identifiers. The ordering of the schemes is unchanged, and the address still
beats its digest and random controls by a wide margin — but it now falls behind
name-substring search, and the gap it has to close is wider in the case that
matters.

---

## 4. Is the address at least a cheap filter?

If the text search is the better ranker, the address could still earn its place
by *pruning*: address-shortlist first, text-rank the survivors. That is the
standard architecture, and it is worth measuring rather than assuming.

| shortlist | fraction of corpus | hit@5 | precision@5 |
| --- | --- | --- | --- |
| 50 | 1.8 % | 69.8 % | 28.8 % |
| 100 | 3.5 % | 77.7 % | 35.4 % |
| 200 | 7.1 % | 78.7 % | 39.2 % |
| 400 | 14.2 % | 82.7 % | 43.9 % |
| 800 | 28.3 % | 85.1 % | 49.6 % |
| **no shortlist** | 100 % | **85.6 %** | **57.7 %** |

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

| what was checked | result |
| --- | --- |
| pairs checked against `sqrt(address²) ≤ 9·sqrt(features²) + 2ρ`, ρ = 4 | **144,075** |
| violations | **0** |
| tightest observed slack | 64 (squared units) |
| guaranteed-complete shortlist at feature radius 2 | mean **70.9** declarations = **2.5 %** of the corpus |
| feature-close declarations it must contain | mean **16.8** |

So the address book is an exact spatial index with a proved recall guarantee:
it reduces a 2,826-declaration scan to 71 candidates while provably keeping
every declaration within the stated feature radius, and when it returns nothing
that emptiness is a theorem rather than a shrug. That is what the substrate is
contributing here — *addressing and exactness*, which is what it has always
been good at — and it is not semantic ranking.

---

## 6. Two worked queries

**`GLM.Address.address_congr`, by address.** The four nearest are
`GLM.ModeAlgebra.definitionOk_is_a_function_of_dominant_role` (d² = 608),
`GLM.Shell.shSum_eq` (608), `GLM.Info.namedResolution_of_injective` (704) and
`GLM.TieBreak.dist_eq_of_mem_nearest` (704) — four theorems of the same
*shape*: a congruence or an equality with a similar quantifier profile and a
similar citation degree, drawn from four different files. The address is doing
precisely what it was built to do, and none of them is a relative.

**The same query, by text.** `GLM.Address.ne_of_address_ne` (11/13),
`GLM.Address.conflates_symm` (5/7), `GLM.Address.address` (2/3),
`GLM.Address.Conflates` (9/14) — its four file mates, in order. Four hits out
of four.

The two answers are both correct answers to different questions. The address
answers "what else looks like this?"; the text answers "what else is about
this?". A proof-search wants the second.

---

## 7. What would falsify this

* **The negative result.** If a feature map exists that is a projection into
  24 capped integers and matches the text control on these queries, the
  capacity reading in §2 is wrong. The two tried here (syntactic, lexical) both
  fall short, one by 34 points and one by 21; a third that closes the gap would
  overturn the conclusion, and the harness scores any scheme that supplies a
  vector.
* **The positive result.** If the digest control or the seeded reshuffle ever
  rises to the address's rate, the experiment is measuring corpus structure
  rather than the feature map, and `test_retrieval.py` fails when it does.
* **The guarantee.** One pair violating `complete_shortlist` would mean the
  quantiser is not the quantiser the Lean file assumes; 144,075 pairs are
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
