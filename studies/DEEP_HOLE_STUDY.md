# The Niemeier deep holes, classified from trajectories

## Tier 0 — the coarse read

**Question.** Can the distribution of trajectories that arrive at a deep hole of the Leech lattice name the hole's Coxeter–Dynkin type, and does it beat the plain vertex count?

**Verdict.** The trajectory statistic beats every control, including the vertex-count baseline that was fixed in advance as the real competitor, and the round still stops: the pre-registered sanity query fails, because the same hole under a different declared ensemble is often named as a different hole.

**Deciding figure.** One primary statistic against a digest control, a seeded reshuffle and the vertex-count baseline, corrected for the 4 statistics tried, read against the gate of 3 bits.

**Recomputed by.** `glm_universal.reasoning.deep_hole_classifier.deep_hole_classifier_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration**, committed before the module that takes the
measurement — §§1–11 are as they were committed, and §12 is what came out.
The trajectory statistic beats every control, including the vertex-count
baseline that was fixed in advance as the real competitor, and the round still
stops: the pre-registered sanity query fails, because the same hole under a
different declared ensemble is often named as a different hole.
The order is the point: §§1–11 were written and committed first, the module was
written against them, and §12 reports whatever came out. A weak result under a
stated gate is a result worth writing down, and this project has nine of them
already.

The question is *not* "what are the deep holes of a Niemeier lattice" — that is
tabulated, and
[`RequestProject/GLM/Golay/Census.lean`](../RequestProject/GLM/Golay/Census.lean)
already carries a census for one lattice. The question is whether the
**distribution of trajectories that reach a hole** carries enough structure to
*name* the hole, so that the classification is a measurement of the substrate
rather than a lookup.

There is a specific reason to doubt it, and the doubt is what makes the test
worth taking: the number of vertices of a deep hole is `24 + k` where `k` is the
number of components of its extended diagram, so the **plain vertex count**
already names some of the types by itself. Any trajectory statistic that merely
reproduces the vertex count has measured nothing. The cheap baseline is
therefore fixed here, before the measurement, and it is the competitor that
matters — exactly as the retrieval round's text control was the one that
mattered.

---

## 1. What is already known, and is used rather than re-derived

Three things are inputs, not findings.

* **The 23 root systems.** `glm_universal.reasoning.niemeier` enumerates them
  from the ADE component formulas — same rank 24, one shared Coxeter number per
  system — so the catalogue is derived rather than stored.
* **The walk that reaches a hole.**
  `glm_universal.reasoning.voronoi_walk` slides from a lattice point along
  directions orthogonal to the active constraints, solving exactly for each
  crossing, to a vertex of the Voronoi diagram; a hill climb on the 1-skeleton
  raises the radius to the covering radius. That is
  `glm_universal.reasoning.deep_holes.walked_hole`, and **it is the starting
  point of the ensemble below**.
* **The certified reading of a hole.** `deep_holes.hole_diagram` reads the
  vertex set's distance graph, matches each component against an extended
  Dynkin shape, solves for the marks as the null vector of the affine Cartan
  matrix, and checks the barycentre identity `∑ nᵢ vᵢ = h·c`. A vertex set that
  passes cannot be extended. **This is the ground truth for this study, and it
  is not the thing being tested.** The classifier under test never sees a
  pairwise distance between two vertices.

**The declared change to the existing walk.** None to `walked_hole`,
`voronoi_walk` or `hole_diagram`: they are frozen as they stand, and the new
module imports them. What is new is a *recording* ensemble — `probe_hole`
returns the set of vertices reached and discards how often each was reached,
and the statistic below needs the counts. The new module therefore runs its own
ensemble loop with the same mechanics (same decoder, same sweep, same offsets)
and keeps the arrival tally. The old path stays in place so the new one has
something to agree with: §12 reports the vertex *sets* of both and requires
them to be equal wherever the old path saturates.

---

## 2. The trajectory ensemble, stated exactly

A walk is a **start**, a **step rule**, a **stopping rule** and a **record**.
All four are fixed here.

**Start.** For a hole centre `c` (24 exact rationals) and a declared seed `s`,
the deterministic sweep `fwht_decode._Sweep(s)` produces start `i` as the
24-vector of offsets `Fraction(sweep.below(2001) - 1000, 4000)`, i.e. each
coordinate an exact rational in `[-1/4, 1/4]` with denominator 4000. Start 0 is
the **zero accumulator** — the undithered modulator — and is kept, and counted,
like any other.

**Step.** One tick of the delta–sigma loop: the driven vector `a + c` is
quantised by the exact nearest-Leech-point decoder
`fwht_decode.nearest_lattice_point_fwht`, and the emitted point is recorded.

**Stop.** After exactly **one tick**. There is no patience rule, no early stop
and no certificate-driven exit: every start contributes exactly one emission, so
the arrival counts are commensurable across holes and across ensembles. (The
existing `probe_hole` stops early on a certificate; that is right for finding a
vertex set and wrong for measuring a distribution, and it is why the ensemble is
run here rather than reused.)

**Record.** For each start, the emitted lattice point and its raw squared
distance to `c`. An emission at the minimum distance seen is a **vertex
arrival**; an emission further away is a **stray** and is counted separately,
reported, and excluded from the profile.

**Size.** `N = 240` starts. The stability re-measurement is at `N = 120`,
declared secondary.

**Why 240 and not an enumeration.** *This is the compromise, declared here
rather than discovered mid-measurement.* The set of start offsets is not
enumerable: it is `2001²⁴` points, about `10⁷⁹`. The ensemble is therefore **the
declared finite deterministic sweep of exactly 240 starts**, not a sample from a
distribution — there is no randomness, no float and no seed-dependent
re-running; a different seed is a *different declared ensemble*, and the study
measures whether the statistic survives changing it. Everything else in this
study is enumerated: the reference table, the query set, the transforms, the
controls and the tails are exhaustive.

---

## 3. The statistic

**Primary — the arrival-share profile `S₁`.** Over the declared ensemble, let
`a(v)` be the number of starts whose emission is the vertex `v`, and
`A = ∑ᵥ a(v)` the number of non-stray arrivals. The shares `q(v) = a(v)/A` are
exact rationals summing to 1. The profile is the tuple of shares **sorted
descending and zero-padded to length 48** (48 is the largest possible vertex
count, that of the `A₁²⁴` hole). Distance between profiles is the **L1 metric**
on `ℚ⁴⁸`.

*Why this one.* It is a statistic of the trajectory and not of the diagram: no
pairwise vertex distance, no shape matching, no marks. It is invariant under
relabelling the vertices, which is the only freedom the walk has in naming them
(§9). Its support size is exactly the vertex count, so the cheap baseline is
*inside* it — which means any margin over the baseline comes from the shape of
the distribution and nothing else, and the ablation in §5 makes that explicit.
And it measures something the static address cannot see: the share `q(v)` is the
fraction of the offset box that quantises to `v`, i.e. a solid angle of the
Voronoi cone at the hole, and cones of the same size can have very different
angular distributions.

**Secondaries, named now so that they cannot be promoted later.**

* `S₂` — the same sorted share profile under the **L∞** metric.
* `S₃` — the **unnormalised arrival counts**, sorted descending, L1.
* `S₄` — the **distance profile of the strays**: the multiset of raw squared
  distances of all emissions, as shares.

`m = 4` statistics tried, and the multiplicity correction of §7 uses that number
whatever the outcome.

**Not a statistic here, and why.** The component sizes of the induced diagram
are the *label source*, not a competitor: they are how the ground truth is
computed. Reporting them as a rival statistic would be reporting the answer key
as a method. They are also, for two of the types this study is most interested
in, useless: `E₈³` and `D₈³` both have three components of nine nodes each, so
component sizes cannot tell them apart and neither can the vertex count.

---

## 4. The label, and the map from statistic to it

**The label** is the hole's Coxeter–Dynkin type as the certified reader names it
— `E_8^3`, `D_24`, `A_1^24` and so on — and the known census is ground truth.

**The map is a stated rule, not a hypothesis-free clustering.**

1. **Reference table.** For each distinct type reached (§6), the *first* centre
   certified of that type becomes the type's reference centre, and its profile
   under the reference ensemble (seed `20260825`) is the reference profile
   `f_T`.
2. **Query.** A query is a centre `c'` with a known ground-truth type, measured
   under a *different* ensemble and, in all but the sanity case, at a
   *different* centre (§6).
3. **Verdict.** With `d_T = L1(S₁(c'), f_T)` over the reference table, and the
   operating radius `r = 1/2`:
   * `named T` if `T` is the **unique** minimiser and `d_T ≤ r`;
   * `ambiguous` if the minimum is attained twice or more within `r`;
   * `absent` if `d_T > r` for every `T`.
   A query is **correct** only when the verdict is `named T` with `T` its
   ground-truth type. `ambiguous` and `absent` are refusals and count as not
   correct; they never count as errors of the other kind, because the whole
   point of a stated refusal is that it is not a guess.
4. **The certified radius.** `r* = ½ · min_{T≠U} L1(f_T, f_U)` is measured, not
   chosen. Under `r*` at most one reference can be within range of any profile,
   so a `named` verdict at `r*` is provably unique and an `absent` verdict at
   `r*` is a certified absence (§9). Both radii are reported. `r = 1/2` is the
   operating radius fixed in advance; `r*` is a measured consequence of the
   table.

---

## 5. The nulls, and the cheap baseline that is the real competitor

Four controls, all run on the same query set, all reported whatever they say.

* **N1 — the digest control (D3).** Each hole's profile is replaced by a
  48-vector of exact rationals derived from the SHA-256 of the hole's *name*.
  A digest addresses integrity and never meaning, so this must score at chance.
  If it does not, the pipeline is leaking the label and the round is void.
* **N2 — the seeded reshuffle.** The reference table's statistic-to-label
  pairing is permuted by a declared seeded permutation (the sweep at seed
  `20260825`, rejecting the identity). Chance again, by construction; it catches
  an accounting error that N1 would not.
* **N3 — the cheap baseline, and the one that matters: the plain vertex
  count.** Classify a query by the number of distinct vertices its ensemble
  reaches: `named T` if exactly one reference type has that vertex count,
  `ambiguous` otherwise. This is not a straw man. Vertex count is `24 + k` with
  `k` the number of components, it costs nothing to compute, and it is exactly
  what the trajectory statistic would collapse to if the arrival distribution
  carried no information. **The method must beat N3, not merely N1 and N2.**
* **N4 — the uniform-profile ablation.** The measured shares are replaced by the
  uniform profile `(1/|V|, …, 1/|V|, 0, …)` on the same support size, and the
  same nearest-reference rule is run. This is N3 expressed inside the method's
  own metric, and the gap between N4 and the method is precisely the value of
  the *shape* of the arrival distribution.

**Chance** is `1/K` per query with `K` the number of types in the reference
table, and the tail probability of a correct count is computed by exact rational
binomial enumeration — no sampling anywhere.

---

## 6. What is attempted, in what order, and what stops the round

**The hole set, in this order.**

1. The two holes the substrate constructs from its own codewords: the
   octad-pair midpoint and the dodecad-triangle centroid
   (`deep_holes.octad_pair_hole`, `deep_holes.dodecad_triangle_hole`). They are
   deterministic and cheap, and they are first for that reason.
2. **Twelve walks**, seeds `20260825 + 977·i` for `i = 0 … 11`, in index order.

Whatever distinct certified types that budget produces is the attempted set, of
size `K`. There is no cherry-picking: the list of seeds is fixed here, a walk
that stalls at a shallow hole is reported as a stall, and the types **not**
reached are reported as not reached with no claim made about them. Of the 23
Niemeier root systems, this study attempts however many of them `K` turns out to
be, and says so in tier 0. Reaching a named type on demand would need its
centre, which is the stored table the exercise exists to avoid.

**The query set** — every query has a known ground-truth type, re-certified at
the query centre, and any transform whose certified type differs from the
source's is dropped with a stated reason rather than quietly used.

* **Q0, the sanity query.** The same centre, a *different* ensemble seed
  (`20260826`). If the statistic does not survive changing the seed at a fixed
  centre, nothing downstream is worth measuring — see the stopping rule below.
* **Q1, translation.** `c + λ` with `λ` the first vector of
  `deep_holes._trio_vectors()`, a minimal vector of the lattice; ensemble seed
  `20260827`.
* **Q2, negation.** `−c`; ensemble seed `20260828`.
* **Q3, a coordinate permutation.** The first **non-identity** permutation of a
  declared finite family that
  `substrate.isomorphism.is_golay_automorphism` accepts: the 24
  cyclic rotations `x ↦ x + k mod 24`, then the maps fixing coordinate 23 and
  acting as `x ↦ a·x + b mod 23` for `a` a quadratic residue mod 23 and
  `b = 0 … 22`, in that order. If no member is accepted, or the accepted one
  fails to map a sample of lattice points into the lattice, **Q3 is dropped and
  the study says so**; ensemble seed `20260829`.
* **Q4, sibling centres.** Any later centre certified with a type already in the
  reference table is a genuine second centre of that type and is added as a
  query under seed `20260830`. There may be none; that is reported.

**The gate, fixed before the measurement.**

*Recovering the census for one lattice* means: **every** query centre carrying
that type is `named`, with the correct type, with no refusal and no error.

| outcome | reading | what happens next |
|---|---|---|
| Q0 fails — the statistic does not survive a seed change at a fixed centre | the ensemble is measuring the sweep, not the hole | **stop**; report it; the transform ensembles are not run |
| method accuracy `≤` N3's | the trajectory adds nothing over the static vertex count | stop; tier 0 says so; no classification faculty is claimed |
| method beats N3 but `B < 3` bits | weak | record as weak; the module ships as a measurement, and no faculty is claimed |
| method beats N3, `B ≥ 3`, and it recovers **exactly one** type that N3 cannot | a coincidence, and reported as one | recorded; not called a method |
| method beats N3, `B ≥ 3`, and it recovers **two or more** types that N3 cannot | a method | claim the faculty; instantiate the certified-absence theorem at `r*` |

The falsifiable form, said plainly: recovering the census for one lattice is a
method only if it recovers it for others. Recovering it for exactly one is a
coincidence.

---

## 7. The score

```
B = log2(1 / p_tail) - log2(m),    m = 4
```

`p_tail` is the exact probability that a uniform labeller — each query assigned
one of the `K` reference labels independently and uniformly — gets at least as
many correct as the method did:

```
p_tail = ∑_{j ≥ correct} C(n, j) · (1/K)^j · (1 - 1/K)^(n-j)
```

an exact `Fraction` over `n` queries. `log2` is an exact rational bracket from
`glm_universal.reasoning.transcendental`, never a float. The correction is
applied whatever the outcome, and the gate is `B ≥ 3`.

---

## 8. What this round has to produce, in the shape D5 requires

* a reasoning module, `glm_universal/reasoning/deep_hole_classifier.py`, with a
  `deep_hole_classifier_report` function;
* a report subject wired into the query runtime and into the evaluation set;
* a test file, `tests/test_deep_hole_classifier.py`, including a test that
  **fails if any control ever rises to the method's rate**;
* this document, with every table a generated block emitted from a measurement
  cache guarded by a digest of its sources (D4/D6), not typed;
* a Lean file, `RequestProject/GLM/DeepHoleClassifier.lean`, in both copies;
* exactness throughout: integers and `Fraction`, no float, and enumeration
  wherever enumeration is possible (D7), with the one non-enumerable part
  declared in §2.

---

## 9. The Lean half: what can actually be proved

Not the census. The theorems worth having are about the **classifier**, in the
register the retrieval round's completeness bound established.

1. **Invariance.** The statistic is a multiset of arrival shares, and the sorted
   profile is a function of that multiset. So relabelling the vertices — the
   only arbitrary choice the walk makes in naming what it reached — cannot move
   the profile: `profile_of_perm`. The label is therefore a function of the hole
   and not of the walk's bookkeeping.
2. **Totality and single-valuedness, with a stated refusal.** The classifier is
   a total function into `named T | ambiguous | absent`; it returns at most one
   label; and it returns `named T` only when `T` is the unique reference within
   the radius. A refusal is a value, not a failure.
3. **The one with teeth — certified absence.** Under the separation hypothesis
   `L1(f_T, f_U) > 2r` for `T ≠ U`, which the measurement supplies as the
   radius `r*`:
   * any profile within `r` of some `f_T` is named `T`, and `ambiguous` cannot
     occur;
   * if the verdict is `absent`, then no profile within `r` of any reference
     equals the query — so, given faithfulness (every hole of type `T` has a
     profile within `r` of `f_T`), **no hole of any tabulated type has this
     statistic**. A negative answer is a proof, which is the property that made
     the retrieval shortlist worth having.

Faithfulness is an empirical hypothesis, is stated as a hypothesis in the Lean
file rather than assumed silently, and is what §12 measures.

---

## 10. What the GLM gains — three claims, to be argued or refuted by the numbers

1. **A classification faculty over a geometric object.** The substrate currently
   addresses and retrieves; it does not classify. If the method beats N3, the
   GLM gains a faculty it did not have.
2. **A second, independent test of whether a trajectory distribution carries
   structure the static address does not.** The address book measured statics;
   this measures dynamics. N4 is the instrument: the gap between the measured
   profile and the uniform profile on the same support is exactly the dynamics'
   contribution.
3. **A hole detector whose negative answers are proofs**, if the certified-
   absence theorem lands with a usable `r*`.

If none of the three survives contact with the controls, that is the finding and
tier 0 says so.

---

## 11. Exactness, and how to re-take every number

No float is constructed anywhere in the module, the cache or the tables. Start
offsets, shares, distances, radii and tails are exact `Fraction`s; logarithms
are exact rational brackets; rendering is integer arithmetic. The one place a
sample could have crept in is the trajectory ensemble, and §2 declares what is
used instead of an enumeration and why.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools deepholes --write
PYTHONPATH=. python3 GLM.py -q "report hole classifier" -c 1
PYTHONPATH=. python3 -m glm_universal.corpus --write
```

---

## 12. The measurement

Every table below is a generated block emitted from a measurement cache that is
guarded by a digest of the modules that produced it: when a source moves, the
cache reports itself stale, the blocks say so, and
`glm_universal.corpus.checks.corpus_checks` fails. No number here is typed.

<!-- generated: deephole-verdict -->
**The verdict is `stopped at the sanity query`.**  The declared budget reached 10 of the 23 Niemeier types, giving 44 queries at a chance rate of `1/10`.  The arrival-share profile named 15 of them correctly (34.1 %), against 11 (25.0 %) for the plain vertex count, 4 (9.1 %) for the digest control and 3 (6.8 %) for the seeded reshuffle.  So the method beats every control, including the one that mattered — and it still fails, because the pre-registered decision tree stops the round earlier than that.

**What stops it is the sanity query.**  Q0 changes only the ensemble seed and leaves the hole where it is; the study fixed in advance that if the statistic does not survive that, nothing downstream is worth reading.  It survives it for 3 of 10 holes.  The statistic does not survive a seed change at a fixed centre, so the ensemble is measuring the sweep and not the hole.

The score against the uniform-label null is 14.18 bits after correcting for 4 statistics tried, which clears the gate of 3 bits — and is reported here as what it is: a bit score computed on a statistic that the round's own stopping rule has already disqualified.  A score is not a licence to ignore the tree it was gated by.

The types the method recovers completely — every query of that type named correctly — are `A_1^24`, `A_2^12`; the vertex count recovers `A_2^12`, `D_24`.  That is 1 type(s) beyond the baseline, and the study fixed in advance that one is a coincidence.
<!-- end generated -->

### 12.1 The holes reached, and their certified types

<!-- generated: deephole-holes -->
| hole | how it was reached | certified type | certified | vertices |
|---|---|---|---|---|
| octad-pair midpoint | midpoint of two orthogonal octads of a MOG trio | A_1^24 | yes | 48 |
| dodecad-triangle centroid | centroid of an equilateral triangle of lattice points | A_2^12 | yes | 36 |
| walk 0 | walk + climb | E_8^3 | yes | 27 |
| walk 1 | walk + climb | D_24 | yes | 25 |
| walk 2 | walk + climb | A_12^2 | yes | 26 |
| walk 3 | walk + climb | D_8^3 | yes | 27 |
| walk 4 | walk + climb | E_6^4 | yes | 28 |
| walk 5 | walk + climb | D_10 E_7^2 | yes | 27 |
| walk 6 | walk + climb | E_8^3 | yes | 27 |
| walk 7 | walk + climb | E_8^3 | yes | 27 |
| walk 8 | walk + climb | D_16 E_8 | yes | 26 |
| walk 9 | walk + climb | D_6^4 | yes | 28 |
| walk 10 | walk + climb | E_6^4 | yes | 28 |
| walk 11 | walk + climb | D_16 E_8 | yes | 26 |

10 distinct types from 14 attempts.  The 13 types the budget did not reach are reported as not reached and nothing is claimed about them: `A_3^8`, `A_4^6`, `A_5^4 D_4`, `D_4^6`, `A_6^4`, `A_7^2 D_5^2`, `A_8^3`, `A_9^2 D_6`, `A_11 D_7 E_6`, `A_15 D_9`, `A_17 E_7`, `D_12^2`, `A_24`.  Reaching a named type on demand would need its centre, which is the stored table the exercise exists to avoid.
<!-- end generated -->

### 12.2 The reference table, its separation, and the two radii

<!-- generated: deephole-references -->
| type | reference centre | certified vertices | vertices the ensemble reached | arrivals | strays | coverage |
|---|---|---|---|---|---|---|
| `A_1^24` | octad-pair midpoint | 48 | 48 | 240 | 0 | 48/48 |
| `A_2^12` | dodecad-triangle centroid | 36 | 36 | 240 | 0 | 36/36 |
| `E_8^3` | walk 0 | 27 | 27 | 235 | 5 | 27/27 |
| `D_24` | walk 1 | 25 | 25 | 221 | 19 | 25/25 |
| `A_12^2` | walk 2 | 26 | 26 | 227 | 13 | 26/26 |
| `D_8^3` | walk 3 | 27 | 27 | 232 | 8 | 27/27 |
| `E_6^4` | walk 4 | 28 | 28 | 236 | 4 | 28/28 |
| `D_10 E_7^2` | walk 5 | 27 | 27 | 234 | 6 | 27/27 |
| `D_16 E_8` | walk 8 | 26 | 26 | 223 | 17 | 26/26 |
| `D_6^4` | walk 9 | 28 | 28 | 234 | 6 | 28/28 |

The 45 pairwise L1 separations of the reference profiles have minimum `2/39` (0.0513), attained by `D_10 E_7^2` and `D_6^4`, so the **certified radius** is `r* = 1/39` (0.0256) against an operating radius of `r = 1/2`.

**And that is the sentence the certified-absence theorem turns on.**  Faithfulness — every hole of type `T` within `r` of `T`'s reference — needs `r` at least 0.1659 on this query set, while separation needs `r` below 0.0256. The two are compatible: `False`.  At `r*` the classifier returns `absent` for 44 of 44 queries, every one of which is a hole that is present and tabulated.  So the theorem holds and the detector does not: `GLM.DeepHole.absent_certifies` is exactly as strong as its faithfulness hypothesis, and this measurement refutes the hypothesis rather than the theorem.
<!-- end generated -->

### 12.3 The query set, query by query

<!-- generated: deephole-queries -->
| query | truth | verdict | named | correct | distance to it | distance to its own reference | rank of its own | vertex count correct |
|---|---|---|---|---|---|---|---|---|
| hole 0 · seed | `A_1^24` | named | `A_1^24` | yes | 0.1000 | 0.1000 | 1 | yes |
| hole 0 · translation | `A_1^24` | named | `A_1^24` | yes | 0.0750 | 0.0750 | 1 | no |
| hole 0 · negation | `A_1^24` | named | `A_1^24` | yes | 0.0833 | 0.0833 | 1 | yes |
| hole 0 · permutation | `A_1^24` | named | `A_1^24` | yes | 0.1250 | 0.1250 | 1 | yes |
| hole 1 · seed | `A_2^12` | named | `A_2^12` | yes | 0.0667 | 0.0667 | 1 | yes |
| hole 1 · translation | `A_2^12` | named | `A_2^12` | yes | 0.0583 | 0.0583 | 1 | yes |
| hole 1 · negation | `A_2^12` | named | `A_2^12` | yes | 0.0917 | 0.0917 | 1 | yes |
| hole 1 · permutation | `A_2^12` | named | `A_2^12` | yes | 0.0750 | 0.0750 | 1 | yes |
| hole 2 · seed | `E_8^3` | named | `D_10 E_7^2` | no | 0.0412 | 0.0851 | 4 | no |
| hole 2 · translation | `E_8^3` | named | `E_6^4` | no | 0.0476 | 0.0498 | 2 | no |
| hole 2 · negation | `E_8^3` | named | `E_6^4` | no | 0.0796 | 0.0837 | 2 | no |
| hole 2 · permutation | `E_8^3` | named | `D_10 E_7^2` | no | 0.0513 | 0.0993 | 4 | no |
| hole 3 · seed | `D_24` | named | `D_24` | yes | 0.0797 | 0.0797 | 1 | yes |
| hole 3 · translation | `D_24` | named | `D_16 E_8` | no | 0.0892 | 0.1062 | 2 | yes |
| hole 3 · negation | `D_24` | named | `E_8^3` | no | 0.1264 | 0.1273 | 2 | yes |
| hole 3 · permutation | `D_24` | named | `D_16 E_8` | no | 0.0800 | 0.0837 | 2 | yes |
| hole 4 · seed | `A_12^2` | named | `D_16 E_8` | no | 0.0711 | 0.0879 | 4 | no |
| hole 4 · translation | `A_12^2` | named | `A_12^2` | yes | 0.0645 | 0.0645 | 1 | no |
| hole 4 · negation | `A_12^2` | named | `E_8^3` | no | 0.0834 | 0.1066 | 3 | no |
| hole 4 · permutation | `A_12^2` | named | `D_10 E_7^2` | no | 0.0678 | 0.0804 | 3 | no |
| hole 5 · seed | `D_8^3` | named | `E_8^3` | no | 0.0583 | 0.0726 | 2 | no |
| hole 5 · translation | `D_8^3` | named | `D_8^3` | yes | 0.0706 | 0.0706 | 1 | no |
| hole 5 · negation | `D_8^3` | named | `D_8^3` | yes | 0.0523 | 0.0523 | 1 | no |
| hole 5 · permutation | `D_8^3` | named | `D_10 E_7^2` | no | 0.0561 | 0.0745 | 3 | no |
| hole 6 · seed | `E_6^4` | named | `E_8^3` | no | 0.0553 | 0.0567 | 2 | no |
| hole 6 · translation | `E_6^4` | named | `E_8^3` | no | 0.0643 | 0.0871 | 2 | no |
| hole 6 · negation | `E_6^4` | named | `E_8^3` | no | 0.0681 | 0.0902 | 4 | no |
| hole 6 · permutation | `E_6^4` | named | `E_8^3` | no | 0.0692 | 0.1105 | 3 | no |
| hole 7 · seed | `D_10 E_7^2` | named | `E_8^3` | no | 0.0548 | 0.0782 | 6 | no |
| hole 7 · translation | `D_10 E_7^2` | named | `D_10 E_7^2` | yes | 0.0640 | 0.0640 | 1 | no |
| hole 7 · negation | `D_10 E_7^2` | named | `E_8^3` | no | 0.0603 | 0.0746 | 3 | no |
| hole 7 · permutation | `D_10 E_7^2` | named | `E_8^3` | no | 0.0951 | 0.1659 | 7 | no |
| hole 8 · seed | `D_16 E_8` | named | `A_12^2` | no | 0.0704 | 0.0912 | 4 | no |
| hole 8 · translation | `D_16 E_8` | named | `D_16 E_8` | yes | 0.0359 | 0.0359 | 1 | no |
| hole 8 · negation | `D_16 E_8` | named | `A_12^2` | no | 0.0495 | 0.0918 | 5 | no |
| hole 8 · permutation | `D_16 E_8` | named | `E_8^3` | no | 0.0650 | 0.0741 | 3 | no |
| hole 9 · seed | `D_6^4` | named | `D_8^3` | no | 0.0572 | 0.0657 | 2 | no |
| hole 9 · translation | `D_6^4` | named | `E_8^3` | no | 0.0711 | 0.0965 | 3 | no |
| hole 9 · negation | `D_6^4` | named | `E_8^3` | no | 0.0727 | 0.0817 | 2 | no |
| hole 9 · permutation | `D_6^4` | named | `D_8^3` | no | 0.0924 | 0.1009 | 3 | no |
| walk 6 · sibling centre | `E_8^3` | named | `E_6^4` | no | 0.0664 | 0.0946 | 6 | no |
| walk 7 · sibling centre | `E_8^3` | named | `D_10 E_7^2` | no | 0.0659 | 0.1277 | 6 | no |
| walk 10 · sibling centre | `E_6^4` | named | `E_8^3` | no | 0.0879 | 0.1253 | 4 | no |
| walk 11 · sibling centre | `D_16 E_8` | named | `D_16 E_8` | yes | 0.0658 | 0.0658 | 1 | no |

The `own rank` column is the diagnostic that says what went wrong: the query's own reference is the nearest one for 15 of 44 queries, so for the rest a *different* type's profile is closer than the profile of the very hole the query is a transform of.  The statistic is not measuring the hole strongly enough to survive its own ensemble.
<!-- end generated -->

### 12.4 The controls, and the baseline that matters

<!-- generated: deephole-controls -->
| classifier | correct | queries | accuracy | refusals | tail | bits |
|---|---|---|---|---|---|---|
| **the arrival-share profile** — the method | 15 | 44 | 34.1 % | 0 | `33718380255258728697013412887588538071/2500000000000000000000000000000000000000000` | 14.18 |
| digest control (D3) | 4 | 44 | 9.1 % | 0 | `65344889664341869165234446618221578427767141/100000000000000000000000000000000000000000000` | -1.39 |
| seeded reshuffle of the pairing | 3 | 44 | 6.8 % | 0 | `82963110895214245840818300941981641968615937/100000000000000000000000000000000000000000000` | -1.73 |
| the plain vertex count | 11 | 44 | 25.0 % | 33 | `335454185621601291664345895423303435248537/100000000000000000000000000000000000000000000` | 6.22 |
| uniform-profile ablation | 12 | 44 | 27.3 % | 32 | `98447414412639696497680970560943419851709/100000000000000000000000000000000000000000000` | 7.99 |

Chance is `1/10` per query.  The digest control sits where D3 says it must, and the reshuffle with it.  The competitor that was fixed in advance is the vertex count, and the method does beat it — by 4 queries of 44 — with the uniform-profile ablation, which is the vertex count expressed in the method's own metric, landing between the two.

The declared stability re-measurement at 120 starts gives 31.8 % against 34.1 % at the full ensemble (agrees: `False`), which is the same finding from the other side: halving the declared ensemble moves the answer.
<!-- end generated -->

### 12.5 The three claims of §10, answered

<!-- generated: deephole-claims -->
| claim | verdict | the number that decides it |
|---|---|---|
| (i) a classification faculty over a geometric object | refuted for now | 15/44 against 11/44 for the vertex count, but the sanity query fails and the tree stops the round |
| (ii) a trajectory distribution carries structure the static address does not | partly upheld | the shape of the distribution is worth 3 queries over the uniform profile on the same support, which is real and small |
| (iii) a hole detector whose negative answers are proofs | refuted on this data | faithfulness needs r >= 0.1659 and separation needs r < 0.0256; compatible: `False`, and 44 of 44 present holes are called absent at r* |

| type | queries | named correctly | recovered by the method | recovered by the vertex count |
|---|---|---|---|---|
| `A_1^24` | 4 | 4 | yes | no |
| `A_2^12` | 4 | 4 | yes | yes |
| `E_8^3` | 6 | 0 | no | no |
| `D_24` | 4 | 1 | no | yes |
| `A_12^2` | 4 | 1 | no | no |
| `D_8^3` | 4 | 2 | no | no |
| `E_6^4` | 5 | 0 | no | no |
| `D_10 E_7^2` | 4 | 1 | no | no |
| `D_16 E_8` | 5 | 2 | no | no |
| `D_6^4` | 4 | 0 | no | no |

So the answer to the round is tier 0's: two of the three claims do not survive contact with the controls, the third survives only as a small margin, and the pre-registered stopping rule fires before any of them can be claimed.
<!-- end generated -->

### 12.6 What the round actually establishes

Three things, and the third is the one worth keeping.

**The arrival distribution is not empty.** It beats the digest control, the
reshuffle, the vertex count and the uniform-profile ablation, in that order,
and the ordering is the one the pre-registration predicted a real signal would
produce. Whatever the shape of the arrival distribution carries, it is not
nothing.

**It is not enough to name a hole.** The stopping rule was fixed for exactly
this case and it fires: change the ensemble seed and leave the hole where it
is, and the profile moves further than the profiles of *different* types are
apart — the two radii in §12.2 are the measurement of that, and they are a
factor of several the wrong way round. The `own rank` column of §12.3 is the
same fact query by query, and the stability row of §12.4 is it again from the
side of the ensemble size. The honest reading is that 240 starts over 25 to 48
vertices does not resolve the arrival distribution finely enough to separate
types whose reference profiles are as close as this table's closest pair. That
is a statement about the declared ensemble as much as about the geometry, and
§2 declared the ensemble before the measurement precisely so that this sentence
could be written rather than argued about.

**The certified-absence theorem is fine and its hypothesis is not.**
`GLM.DeepHole.absent_certifies` says a refusal is a proof *given* faithfulness,
and the measurement supplies the two radii that decide whether faithfulness and
separation can hold at once. They cannot, on this data, by a wide margin. The
theorem is not weakened by that; it is doing its job, which is to make the
empirical hypothesis visible instead of letting a detector quietly assume it.

What a next round would have to change is the ensemble, not the theory: a
statistic whose resolution is coarser than the separation it must detect cannot
detect it, however the classifier is written. The two candidate fixes — many
more starts, or a statistic that is exact per start rather than a frequency —
are both stateable in advance, which is where they should be stated.

---

## 13. What this study does not do

* It does **not** formalise the census, and it does not re-derive the 23 root
  systems: they are `reasoning.niemeier`'s, and they are inputs.
* It does **not** claim to reach all 23 types. It reaches what the declared
  budget reaches and reports the rest as not reached.
* It does **not** solve the nearest-hole problem for a carrier in general
  position. A carrier that is not at the covering radius has no type, and the
  classifier refuses it.
* It does **not** promote a secondary statistic to primary after seeing the
  numbers. `S₁` is fixed in §3, and this document was committed before the
  module existed.
