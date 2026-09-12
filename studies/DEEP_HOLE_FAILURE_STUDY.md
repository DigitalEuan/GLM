# The four failures, and the spread that gates the certificate

## Tier 0 — the coarse read

**Question.** The escalated deep-hole reading names 40 of 44 and certifies
nothing. Which of four pre-registered mechanisms accounts for the four it does
not name, and is that mechanism the same one that holds the separation ratio
`ρ = 2W/B` above 1?

**Verdict.** All four failures are near misses at rank 2, and the type whose within-type spread stalls the separation ratio is the type the failures belong to, so the two open questions are one mechanism and not two. The global ratio stays above 1 and the pre-registered negative stands; read type by type, three of the ten types do satisfy the criterion.

**Deciding figure.** The rank the correct label takes in each of the four: 2, 2, 2, 2. The worst within-type spread `W = 0.0659` against the closest separation `B = 0.0358`, giving `ρ = 2.5943` on the seed reading, and 3 of 10 types certified.

**Recomputed by.** `glm_universal.reasoning.deep_hole_failures.deep_hole_failure_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0a. The reading in one paragraph

All four failures are near misses at rank 2, and the type whose within-type spread stalls the separation ratio is the type the failures belong to, so the two open questions are one mechanism and not two. The global ratio stays above 1 and the pre-registered negative stands; read type by type, three of the ten types do satisfy the criterion. The rank the correct label takes in each of the four is 2, 2, 2 and 2; the worst within-type spread is `W = 0.0659` against a closest separation of `B = 0.0358`, which is a ratio of `ρ = 2.5943` on the seed reading; and 3 of 10 types are certified.

The same reading, recomputed rather than written:

<!-- generated: deepholefail-tier -->
All 4 failures are opened at the one declared cell.  Of them, 4 have their truth and their winner among the five closest reference pairs, 4 split their ensemble halves onto different labels, 0 are ties, and 0 have the correct answer outside the first three ranks; 0 match none of the four.  The four are D_8^3 named as D_10 E_7^2, D_10 E_7^2 named as D_8^3, D_6^4 named as E_6^4, D_6^4 named as E_6^4.

The spread that stalls the ratio is `D_6^4`'s, at `W = 0.0659` against a separation of `B = 0.0358`, and the failing queries belong to that same type — so the failures and the stalled ratio are one mechanism.  Over the 55 declared deletions the smallest ratio reached is `1.4784`, and `rho < 1` over the full ten-type set — the only reading that earns the certificate — is not reached.
<!-- end generated -->

---

## 0. What this document is

A **pre-registration**. §§1–11 were committed before the module that takes the
measurement had ever been run, and §12 is whatever came out.

It is the third round on one question. The first
([`DEEP_HOLE_STUDY.md`](DEEP_HOLE_STUDY.md)) classified a hole's type from the
distribution of walk arrivals and stopped at its own sanity check, 3 of 10. The
second ([`DEEP_HOLE_ESCALATION_STUDY.md`](DEEP_HOLE_ESCALATION_STUDY.md)) asked
whether that was the geometry or the layer it was read at, escalated the
reading along a declared ladder, and reached the gate at the joint reading with
1920 starts — 10 of 10 on the sanity check, **40 of 44** on the full query set.

That round left two things on the record and examined neither:

* the **four** queries it does not name correctly, which were counted and never
  opened; and
* the ratio `ρ = 2W/B`, which falls from 3.90 to **2.59** along the ladder and
  stops well short of the `ρ < 1` that `GLM.DeepHoleLadder.nearest_correct`
  needs. So the classifier that names 40 of 44 cannot certify a single
  *absence*: at the passing cell faithfulness needs `r ≥ 0.0659` where
  separation permits only `r < 0.0179`.

Both are governed by the **worst-case within-type spread** `W`. That is the
whole reason this round takes them as one item: if the four failures identify a
specific mechanism inflating `W`, and it can be removed or read around, the
failures and the certificate move together. If they do not, the round says so
and both stay open.

**What this round is not.** It is not another rung. Escalation is not free, and
re-reading a negative at layer after layer until one passes is an unbounded
multiple-comparison search whose pass means less than the original negative
did. This round is therefore allowed **no search on the layer axis at all**:
every number in it is taken at one cell, fixed in §2 before the module existed.

---

## 1. What is used rather than re-derived

The centres, the certification, the transforms, the seeds, the reference table
and the query set are the escalation round's, unchanged, and are taken from
`glm_universal.reasoning.deep_hole_escalation` rather than rebuilt. Nothing
about the geometry is re-derived here; only the reading of what it returned is
opened up.

The stopping rule of §9 exists to enforce that: if this round's re-reading does
not return exactly the escalation round's 40 of 44, the two disagree about the
same measurement and nothing else here is read.

---

## 2. The cell, declared before anything is measured

**One cell: `(L₄, 1920)`** — the joint reading (arrival shares, the stray
spectrum and the exact rational measure of emission distances) at 1920 starts.

That is the escalation round's passing cell. It is named here, in advance,
because it is the *only* cell this round may read at. No other layer, no other
ensemble size, no other metric, and no re-selection after the numbers are seen.
The multiplicity of this round on the layer axis is therefore exactly **1**.

---

## 3. The descriptive object

For each of the 44 used queries, the round records the exact distance to
**every one of the ten references**, not merely to the winner:

* the ranked list of all ten `(type, distance)` pairs, as exact rationals;
* the winner, and whether the verdict was a strict name or a tie;
* the rank of the correct answer, and the exact margin `d(truth) − d(winner)`;
* the same margin as a fraction of the reference separation `B`.

This is the first step precisely because *second by a hair* and *absent from
the shortlist* are opposite diagnoses that the escalation round's summary
cannot tell apart.

---

## 4. The four diagnoses, and the rule that decides each

Four mechanisms are live for the failures, and each is given a rule now, so
that none of them can be fitted to the numbers afterwards.

| tag | the hypothesis | the rule that decides it |
|---|---|---|
| **A** | the references were never separated: the query's type and the type it was named as are the closest pair under the separation measure | the `(truth, winner)` pair is among the **5 closest** of the 45 reference pairs |
| **B** | the ensemble's arrival distribution is genuinely bimodal, so a single profile is the wrong summary object | the two declared halves of the ensemble — starts 0–959 and 960–1919 — name **different** types, each against the reference table read on the corresponding half |
| **C** | it is the nearest-reference rule's tie behaviour, not the geometry | the verdict is `ambiguous`, or the margin is exactly 0 |
| **D** | the wobble crossed into another hole's basin: the correct answer is not merely beaten, it is nowhere near | the correct answer's rank is **greater than 3** |

Two further readings are recorded because they are what distinguishes D from
its opposite:

* **near miss** — the correct answer is rank 2 and the margin is less than
  `B/10`;
* **none of the four** — no rule above fires. This is a live outcome and is
  reported as one: it would refute all four hypotheses at once, and the round
  does not force the four to be exhaustive.

The four are readings of the same 44 queries and are **not independent tests**;
no bit score is computed from them and none is claimed as a discovery.

---

## 5. The spread, opened up type by type

For each reference type `T`:

* `W_T^seed` — the distance from `f_T` to the same centre read under the sanity
  seed. This is the escalation round's spread, per type.
* `W_T` — the largest distance from `f_T` to *any* query of type `T` in the
  declared query set (the seed change, the translation, the negation, the
  permutation and the sibling centres). This is the spread the classifier
  actually has to survive, and it is at least `W_T^seed`.
* `B_T` — the distance from `f_T` to its nearest other reference.
* `ρ_T = 2W_T / B_T`, and `ρ_T^seed = 2W_T^seed / B_T`.

Reported alongside: which type attains the global `W`, which pair attains the
global `B`, and whether the type that inflates `W` is one of the types the four
failures belong to. That last is the question of whether the failures and the
stalled ratio are one mechanism or two, and it is answered yes or no.

---

## 6. What would count as the ratio being fixed, and what would not

`ρ < 1` over the full ten-type reference set is the only thing that earns the
certificate. Nothing short of it is reported as earning anything.

In particular, a **deletion** that takes `ρ` below 1 certifies only over the
types that remain. A classifier that cannot be asked about a type it has
deleted has not earned a certificate about that type, and the round states that
wherever the deletion table is read.

---

## 7. The deletion sweep, declared and reported in full

To locate the spread rather than to pass a gate, the round computes `ρ` over
every reference set obtained by deleting one type (**10** subsets) and every
set obtained by deleting two (**45** subsets): **55** in all, every one printed
whatever it says, sorted by ratio.

The count is declared here because it is an enumeration and enumerations are
where multiplicity hides. It is not a search for a passing cell: the cell is
fixed in §2, all 55 rows are reported, and the smallest ratio among them is
read as a *description of where the spread lives*, never as a certificate.

---

## 8. The original negative, kept beside whatever this returns

The escalation round's negative stands, and is restated in the report object
itself rather than in prose that can drift from it:

> at the passing cell `ρ = 2.5943` against a criterion of 1, faithfulness needs
> `r ≥ 0.0659` where separation permits `r < 0.0179`, and no absence is
> certified.

Nothing in this round repairs that. If the round ends with the negative intact,
that is the result: a negative that has survived being read at a finer
resolution is a stronger statement than the negative was.

---

## 9. The stopping rule

Before anything in §§3–7 is read, the round re-classifies all 44 used queries
at the declared cell and must return **40 correct of 44**, the escalation
round's own numbers. If it does not, the two rounds disagree about the same
measurement, and the round stops and reconciles rather than reporting.

---

## 10. The Lean half: what is proved rather than measured

The measurements above are measurements. Five statements about them are
theorems, in `RequestProject/GLM/DeepHoleFailure.lean`:

1. **A rank-1 reading is a correct reading**
   (`GLM.DeepHoleFailure.rank_one_correct`). If a query's own reference is
   strictly nearest then the nearest-reference rule names it correctly — the
   rank language of §3 and the verdict language of the classifier agree.
2. **A failure puts two references close together**
   (`GLM.DeepHoleFailure.failure_pair_close`), and its contrapositive
   (`GLM.DeepHoleFailure.no_failure_of_separated`): a query mis-named in favour
   of `q` while lying within `w` of its own reference `p` forces
   `d(p, q) ≤ 2w`. This is what licences reading the four failures as a
   statement about the closest pairs rather than about basins.
3. **Deleting a reference can only lower the ratio's denominator, never raise
   it** (`GLM.DeepHoleFailure.separation_mono`, with
   `GLM.DeepHoleFailure.resolves_of_subset`). The separation of a
   sub-collection is at least the separation of the whole, so a deletion cannot
   make `ρ` worse — which is why a deletion passing the criterion is evidence
   about *where* the spread lives and not evidence that the spread is gone.
4. **A per-type criterion suffices where the global one fails**
   (`GLM.DeepHoleFailure.per_type_correct`, stated through
   `GLM.DeepHoleFailure.ResolvesAt`, with
   `GLM.DeepHoleFailure.resolvesAt_of_resolves` relating it to the global
   reading). If `2W_T < B_T` for a particular type, every query of that type
   within `W_T` of `f_T` is named correctly, whatever the other types do. This
   is the exact sense in which one type's spread can gate the whole table.
5. **A per-type certificate also refuses**
   (`GLM.DeepHoleFailure.per_type_absent`): under the same hypothesis a profile
   further than `W_T` from `f_T` is not of type `T`, so for a certified type
   the negative answer is a proof and not a shrug.

---

## 11. Exactness, and how to re-take every number

Integers and `Fraction` throughout: distances, shares, Wasserstein integrals,
margins, ratios and radii. No float, no RNG, and no digest except the cache
guard.

```
python3 -m glm_universal.tools failures --write   # re-take (about ten minutes)
python3 -m glm_universal.tools failures           # read the stored measurement
```

The measurement cache is guarded by a digest of the modules it is taken from,
so if any of them moves the tables below say so instead of printing a stale
number.

---

## 12. The measurement

*Written by the measurement, not by hand: every table below is a generated
block emitted from a cache guarded by a digest of the modules that produced
it, so when a source moves the block says so and the corpus check fails.*

### 12.1 The stopping rule

<!-- generated: deepholefail-reproduction -->
Re-reading all 44 used queries at the declared cell returns **40 correct**, against the **40 of 44** the escalation round reported: reproduces = `True`.  The two rounds agree about the same measurement, and the rest of the study is read.
<!-- end generated -->

### 12.2 The four failures, exactly

<!-- generated: deepholefail-failures -->
| query | truth | named as | rank of the truth | margin | margin / `B` | the first three references, with distances |
|---|---|---|---|---|---|---|
| hole 5 · translation | D_8^3 | D_10 E_7^2 | 2 | 0.0050 | 0.1392 | D_10 E_7^2 0.0509, D_8^3 0.0559, E_8^3 0.0828 |
| hole 7 · translation | D_10 E_7^2 | D_8^3 | 2 | 0.0093 | 0.2586 | D_8^3 0.0461, D_10 E_7^2 0.0553, E_8^3 0.0624 |
| hole 9 · negation | D_6^4 | E_6^4 | 2 | 0.0159 | 0.4434 | E_6^4 0.0418, D_6^4 0.0577, D_10 E_7^2 0.1194 |
| hole 9 · permutation | D_6^4 | E_6^4 | 2 | 0.0025 | 0.0703 | E_6^4 0.0325, D_6^4 0.0350, D_10 E_7^2 0.1098 |

The whole ranked list of all ten references is in the measurement cache for every one of the 44 queries; the first three are shown because the diagnosis that matters — second by a hair against absent from the shortlist — is decided there.
<!-- end generated -->

### 12.3 The diagnoses

<!-- generated: deepholefail-diagnoses -->
| query | A closest pair | B bimodal | C tie | D absent from the shortlist | near miss | halves name |
|---|---|---|---|---|---|---|
| hole 5 · translation | yes (pair rank 2) | yes | no | no | no | E_8^3 / D_8^3 |
| hole 7 · translation | yes (pair rank 2) | yes | no | no | no | D_10 E_7^2 / D_8^3 |
| hole 9 · negation | yes (pair rank 1) | yes | no | no | no | E_6^4 / D_6^4 |
| hole 9 · permutation | yes (pair rank 1) | yes | no | no | yes | E_6^4 / D_6^4 |

Totals over the 4 failures: A 4, B 4, C 0, D 0, near miss 1, none of the four 0.  The four rules are readings of the same queries and are not independent tests; no bit score is computed from them.

**The control on rule B, added after the four were read.**  The same half-split rule fires for 7 of the 40 queries the reading names *correctly*, against 4 of the 4 it does not.  Rule B therefore reads as a statement about margin rather than about modality: the halves come apart wherever the margin is smaller than what half the budget resolves, which is what a near-miss is.  It is reported as a control and is not counted among the pre-registered four.
<!-- end generated -->

### 12.4 The spread, type by type

<!-- generated: deepholefail-spread -->
| type | `W_T` (all perturbations) | attained by | `W_T` (seed only) | nearest other reference | `B_T` | `rho_T` |
|---|---|---|---|---|---|---|
| D_6^4 | 0.0659 | hole 9 · translation | 0.0243 | E_6^4 | 0.0358 | 3.6799 |
| D_24 | 0.0600 | hole 3 · translation | 0.0465 | D_16 E_8 | 0.1089 | 1.1023 |
| D_8^3 | 0.0559 | hole 5 · translation | 0.0379 | D_10 E_7^2 | 0.0519 | 2.1555 |
| D_10 E_7^2 | 0.0553 | hole 7 · translation | 0.0461 | D_8^3 | 0.0519 | 2.1336 |
| E_8^3 | 0.0546 | walk 7 · sibling centre | 0.0277 | D_8^3 | 0.0764 | 1.4298 |
| D_16 E_8 | 0.0517 | hole 8 · negation | 0.0269 | E_8^3 | 0.0844 | 1.2243 |
| E_6^4 | 0.0516 | walk 10 · sibling centre | 0.0265 | D_6^4 | 0.0358 | 2.8829 |
| A_2^12 | 0.0365 | hole 1 · negation | 0.0313 | A_1^24 | 0.3656 | 0.1994 |
| A_12^2 | 0.0342 | hole 4 · translation | 0.0273 | D_8^3 | 0.0860 | 0.7956 |
| A_1^24 | 0.0302 | the sanity seed | 0.0302 | A_2^12 | 0.3656 | 0.1652 |

The global separation is `B = 0.0358`, attained by the pair `E_6^4 / D_6^4`.  Read over the sanity seed alone the ratio is `rho = 2.5943`, which is the escalation round's number; read over every perturbation the query set contains it is `3.6799`.  Faithfulness needs `r >= 0.0659` where separation permits only `r < 0.0179`, so the two are compatible: `False`.

The global ratio is a worst case over all ten types, and it hides that the criterion already holds for **3 of 10** of them: `A_2^12`, `A_12^2`, `A_1^24`.  For those, `2W_T < B_T`, and `GLM.DeepHoleFailure.per_type_correct` turns that into a certificate — every query of the type within `W_T` of its reference is named correctly whatever the other types do.  That is the first certification this line of rounds has earned, and it covers 3 types, not ten.
<!-- end generated -->

### 12.5 The deletion sweep

<!-- generated: deepholefail-leaveout -->
| deleted | separation `B` | worst spread `W` | `rho` | `rho < 1` |
|---|---|---|---|---|
| nothing (all ten types) | 0.0358 | 0.0659 | 3.6799 | no |
| D_6^4 | 0.0519 | 0.0600 | 2.3154 | no |
| E_6^4 | 0.0519 | 0.0659 | 2.5414 | no |
| A_1^24 | 0.0358 | 0.0659 | 3.6799 | no |
| A_2^12 | 0.0358 | 0.0659 | 3.6799 | no |
| E_8^3 | 0.0358 | 0.0659 | 3.6799 | no |
| D_24 | 0.0358 | 0.0659 | 3.6799 | no |
| A_12^2 | 0.0358 | 0.0659 | 3.6799 | no |
| D_8^3 | 0.0358 | 0.0659 | 3.6799 | no |
| D_10 E_7^2 | 0.0358 | 0.0659 | 3.6799 | no |
| D_16 E_8 | 0.0358 | 0.0659 | 3.6799 | no |
| D_8^3, D_6^4 | 0.0812 | 0.0600 | 1.4784 | no |
| D_10 E_7^2, D_6^4 | 0.0764 | 0.0600 | 1.5723 | no |
| D_8^3, E_6^4 | 0.0812 | 0.0659 | 1.6227 | no |
| E_6^4, D_10 E_7^2 | 0.0764 | 0.0659 | 1.7257 | no |
| D_24, D_6^4 | 0.0519 | 0.0559 | 2.1555 | no |
| A_1^24, D_6^4 | 0.0519 | 0.0600 | 2.3154 | no |
| A_2^12, D_6^4 | 0.0519 | 0.0600 | 2.3154 | no |
| E_8^3, D_6^4 | 0.0519 | 0.0600 | 2.3154 | no |
| A_12^2, D_6^4 | 0.0519 | 0.0600 | 2.3154 | no |
| E_6^4, D_6^4 | 0.0519 | 0.0600 | 2.3154 | no |

All 55 declared deletions were computed — the ten one-type deletions in full above, and the ten best of the forty-five two-type deletions, the rest being in the measurement cache.  The smallest ratio any deletion reaches is `1.4784`, deleting `D_8^3, D_6^4`.  A deletion certifies only over the types that remain: a classifier that cannot be asked about a type it has deleted has earned nothing about that type, so this table locates the spread and does not license a certificate.
<!-- end generated -->

### 12.6 What the round establishes

<!-- generated: deepholefail-establishes -->
**The failures are described rather than hypothesised.**  Each of the 4 carries its rank and its exact margin to every reference.  1 of them are second by less than a tenth of the separation and 0 have the correct answer outside the first three ranks — the two diagnoses that point in opposite directions, now separated by measurement.

**The spread is localised.**  The worst within-type spread belongs to `D_6^4` at `0.0659`, and the closest reference pair is `E_6^4 / D_6^4` at `0.0358`.  Whether the two are the same object is the question the round was taken to answer, and the answer is `True`.

**The certificate is not earned.**  Over the full ten-type reference set the ratio is `2.5943` on the seed reading and `3.6799` over every perturbation, against a criterion of 1.  The best of the 55 deletions reaches `1.4784`, and a deletion certifies only over what remains.  The escalation round's negative therefore stands: `True`.

**Three types are certified, and seven are not.**  The criterion holds type by type for `A_2^12`, `A_12^2`, `A_1^24`, so for those the naming is a certificate rather than a faculty.  The remaining seven include both members of each of the two closest pairs, which is exactly where the four failures are.

**A negative that survives a finer reading is a stronger statement than the negative was.**  That is the result this round is entitled to, and it is the one it reports.
<!-- end generated -->

---

## 13. What this study does not do

* It does **not** read at any cell but `(L₄, 1920)`.
* It does **not** enlarge the hole set, the transform set or the ensemble.
* It does **not** promote the deletion sweep to a certificate.
* It does **not** claim a bit score: no new classification is proposed here, so
  there is nothing for a multiplicity correction to be applied to. The 55
  subsets are reported in full precisely so that no row of them can be quoted
  as a finding on its own.

---

## 14. What was added after the numbers were seen

Two things in this document were not in the version committed before the
measurement was taken, and both are labelled as post-hoc wherever they are
quoted:

1. **The control on diagnosis B.** Rule B — "the two halves of the ensemble
   disagree" — fires for all four failures, which on its own says nothing,
   because a rule that fires everywhere separates nothing. The control counts
   how often it fires among the forty *correct* queries: 7 of 40. B is
   therefore reported as a margin statement (the failures sit where the
   ensemble is least settled) and not as a diagnosis that picks the failures
   out.
2. **The per-type criterion.** The pre-registered question was the global
   ratio, and the global ratio is `> 1`; splitting the criterion type by type
   was decided after seeing that the spread is localised in `D_6^4`. Three
   types pass. That is a genuine positive, but it is an unregistered reading of
   a registered measurement, so it is reported as one: it earns a certificate
   for three named types, and it does not touch the pre-registered negative,
   which stands unchanged in §8.

No cell of the layer × budget ladder was tried other than the declared
`(L₄, 1920)`, so nothing here is a multiple-comparison search over layers. The
two additions above are the entire post-hoc content of the round.
