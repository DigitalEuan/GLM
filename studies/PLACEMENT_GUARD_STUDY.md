# The placement guard — the cell guard with a radius read from the carriers

## Tier 0 — the coarse read

**Question.** If the cell guard's packing radius is replaced by the radius that is actually true of the carriers — the distance from the cell's centre to the nearest other carrier, stored once per cell — does the certified-nearest ladder keep enough of its correct answers to be worth having, and does it stay safe on four query sets?

**Verdict.** Yes, on every set read. The placement guard answers no query wrongly on any of the four sets — the standard set, Phase 127's held-out set, Phase 128's third set and a fourth set generated after the pre-registration — while the unguarded ladder answers 0, 8, 1 and 2 wrongly on them; and it keeps 445 of the ladder's 467 correct answers on the standard set and between 91 and 93 per cent on the other three. Every guarded answer is the strictly nearest carrier, as the Lean file proves without any hypothesis on the quantiser, and the guarded ladder is order-independent. The coarse-only ladder the retirement rule leaves is also safe on the fourth set, with 386 correct against the placement guard's 402.

**Deciding figure.** 9 of 9 marks (L1, P1, N1, S1, S2, S3, S4, K1, U2); placement-guarded ladder 445, 402, 393 and 402 correct with 0 wrong on the four sets, against the unguarded ladder's 467/0, 435/8, 426/1 and 441/2 in the middle-out order; union-retired ladder 386 correct, 0 wrong on the fourth set.

**Recomputed by.** `glm_universal.reasoning.placement_guard.placement_guard_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 129, committed with its Lean file and before
the module that takes the measurement exists. §§0–6 are as they were
committed; §7 is what came out.

It takes the follow-up Phase 128 left
([`CELL_GUARD_STUDY.md`](CELL_GUARD_STUDY.md) §7.4 (ii) and (iii)): the cell
guard was safe on all three query sets but kept only 30, 12 and 12 of the
ladder's correct answers, because most carriers sit outside the inscribed
ball of their own cell; and the coarse-only ladder the retirement rule leaves
when read on two sets was safe on the third, which one unseen set does not
settle.

**Order of work, stated plainly.**

1. *What was known before this was written.* Everything in
   [`CELL_GUARD_STUDY.md`](CELL_GUARD_STUDY.md) §7, in particular: the
   nearest-carrier reading answers 1, 13 and 7 queries wrongly on the
   standard, held-out and third sets, and the placement counts of §7.3.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/PlacementGuard.lean` was written and built first (§1).
3. **The placement guard has not been computed on any query, and the fourth
   set (§4) has not been generated, when this was committed.**

## 1. What is proved before any code

`RequestProject/GLM/PlacementGuard.lean`, no `sorry`, standard axioms only,
on top of `RequestProject/GLM/CellGuard.lean`:

* `placed_strict_nearest` — if every carrier other than `i` is at least `ρ`
  from a point `p`, and `dist(q, c_i) + dist(q, p) < ρ`, then `c_i` is the
  strictly nearest carrier to `q`. **No property of the quantiser is used**:
  the radius is a fact about the carriers, so the theorem holds for any rung.
* `placement_radius_ge` — for a nearest-point quantiser of a `2r`-separated
  set, a cell holding only `i` has every other carrier at least `r` from its
  centre; so the stored radius is at least the packing radius, and
  `cellGuard_imp_placed` — every cell-guard answer is a placement-guard answer.
* `placed_firstNamed_agree` — a placement-guarded ladder is order-independent.

As in Phase 128, the theorems do not say a guarded answer is right: it is the
nearest carrier, and the nearest carrier was wrong 1, 13 and 7 times on the
three earlier sets. A placement-guarded wrong answer is always one of those.

## 2. The rule

At every rung of the ladder Phase 123 left, for every cell `p` that holds
exactly one carrier `i`, store `ρ²_p = min_{k ≠ i} ‖c_k − p‖²` (exact, once
per cell, over all 142 carriers). A query `q` quantised to `p` is answered `i`
only if `‖q − c_i‖ + ‖q − p‖ < ρ_p`, decided by `sqrt_add_lt_sqrt_iff` with
`R = ρ²_p`; otherwise the rung refuses. Nothing is tuned: the radius is the
carriers'.

## 3. The marks, declared before the code

| mark | statement |
|---|---|
| **L1** | `RequestProject/GLM/PlacementGuard.lean` builds with no `sorry` and the standard axioms only, with the theorems of §1. |
| **P1** | *The theorems, checked.* Every stored radius is at least the packing radius (`ρ²_p ≥ m/4`), and on all four sets every cell-guard answer is a placement-guard answer. |
| **N1** | On all four sets, every placement-guarded rung answer is the strictly nearest carrier. |
| **S1** | On the 568 standard queries, the placement-guarded ladder answers 0 wrongly. |
| **S2** | On the 568 held-out queries of Phase 127, it answers 0 wrongly. |
| **S3** | On the 568 queries of Phase 128's third set, it answers 0 wrongly. |
| **S4** | *Blind.* On the fourth set (§4), it answers 0 wrongly. |
| **K1** | On each of the four sets, it keeps at least half of the correct answers the unguarded ladder gives. |
| **U2** | *Blind, comparison.* On the fourth set, the union-retired ladder of Phase 128 (`8C 8A 4C 2C 2A`) answers 0 wrongly. |

**Predictions.** L1, P1 and N1 hold (theorem). S1 is predicted to hold (the
nearest carrier is wrong once there, and that query need not pass the
guard). S2 and S3 are uncertain: the nearest carrier is wrong 13 and 7 times
there, and the guard passes more queries than the cell guard did. K1 is
uncertain in the other direction; it is predicted to hold on the standard set
at least. U2 is predicted to hold, with low confidence.

## 4. The fourth query set, declared here

The same 142 carriers; four perturbations used by no earlier round, applied
with `ladder_escalation.perturb` to the carrier of index `i` with the codeword
index `i + 1024`:

| support | magnitude | squared length |
|---|---|---|
| 24 coordinates | 1/4 | 3/2 |
| 12 coordinates | 1/2 | 3 |
| 10 coordinates | 3/4 | 45/8 |
| 2 coordinates | 2 | 8 |

568 queries, generated and read once, after this document is committed.

## 5. What this round does not do

* It does not put the guard into the answering path: that needs a frozen-path
  comparison of its own.
* It does not choose between the guard and the union retirement; it measures
  both on a set neither has seen.

## 6. Files

| file | what |
|---|---|
| `RequestProject/GLM/PlacementGuard.lean` | §1 |
| `glm_universal/reasoning/placement_guard.py` | the radii, the guard, the fourth set, the marks, `placement_guard_report` |
| `glm_universal/tests/test_placement_guard.py` | the marks |
| `python3 -m glm_universal.tools placement-guard` | the measurement |

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

`python3 -m glm_universal.tools placement-guard --write` takes it and stores
it beside the digest of its sources (`reasoning/_data/placement_guard.json`);
`tools placement-guard` reads it back.

### 7.1 The verdict

Yes, on every set read. The placement guard answers no query wrongly on any of the four sets — the standard set, Phase 127's held-out set, Phase 128's third set and a fourth set generated after the pre-registration — while the unguarded ladder answers 0, 8, 1 and 2 wrongly on them; and it keeps 445 of the ladder's 467 correct answers on the standard set and between 91 and 93 per cent on the other three. Every guarded answer is the strictly nearest carrier, as the Lean file proves without any hypothesis on the quantiser, and the guarded ladder is order-independent. The coarse-only ladder the retirement rule leaves is also safe on the fourth set, with 386 correct against the placement guard's 402.

### 7.2 The marks

| mark | statement | result |
|---|---|---|
| L1 | the Lean file | **met**: `RequestProject/GLM/PlacementGuard.lean`, 4 named theorems on top of `CellGuard.lean`, no `sorry`, standard axioms only |
| P1 | radii at least the packing radius; cell guard ⊆ placement guard | **met**: 0 of the 1,166 single-carrier cells over the 11 rungs has `ρ²_p < m/4`; 0 cell-guard answers refused by the placement guard on any set |
| N1 | every guarded answer is the strictly nearest carrier | **met**: 0 violations on all four sets |
| S1 | standard set: 0 wrong | **met**: 445 correct, 0 wrong, 123 refused |
| S2 | held-out set: 0 wrong | **met**: 402 correct, 0 wrong, 166 refused |
| S3 | third set: 0 wrong | **met**: 393 correct, 0 wrong, 175 refused |
| S4 | blind, fourth set: 0 wrong | **met**: 402 correct, 0 wrong, 166 refused |
| K1 | keeps half the ladder's correct answers on each set | **met**: 445 of 467, 402 of 435, 393 of 426 and 402 of 441 in the middle-out order (95, 92, 92 and 91 per cent) |
| U2 | blind, fourth set: the union-retired ladder 0 wrong | **met**: 386 correct, 0 wrong, 182 refused |

**Scored as declared: 9 of 9.** The predictions: L1, P1, N1 and S1 held as
predicted; S2 and S3, declared uncertain, held; K1 held on every set, not only
the standard one; U2, predicted to hold with low confidence, held.

**The fourth set read unguarded.** The ladder Phase 123 left answers 441 of
the fourth set correctly and 2 wrongly in the middle-out order (1 in the
fine-to-coarse order), so the finding of Phase 127 reproduces a second time on
a set nobody had seen.

**Every set, side by side** (middle-out order; correct / wrong):

| set | unguarded ladder | cell guard (Phase 128) | placement guard | nearest carrier alone |
|---|---|---|---|---|
| standard | 467 / 0 | 30 / 0 | 445 / 0 | 506 / 1 (61 ties) |
| held-out | 435 / 8 | 12 / 0 | 402 / 0 | 489 / 13 (66 ties) |
| third | 426 / 1 | 12 / 0 | 393 / 0 | 499 / 7 (62 ties) |
| fourth | 441 / 2 | 13 / 0 | 402 / 0 | 497 / 14 (57 ties) |

### 7.3 Post hoc: what the radius is doing

*Read after the marks, labelled post hoc.*

* **The guard and the nearest carrier.** Every placement-guarded answer is
  the nearest carrier (N1), yet the nearest carrier read alone answers 1, 13,
  7 and 14 queries wrongly on the four sets. None of those queries passes the
  guard at any rung (a pass would have been a wrong guarded answer). The guard
  does not know the truth; it refuses wherever the triangle inequality does
  not certify the nearest carrier from two distances and the stored radius.
* **Where the answers come from.** Rung by rung, the placement guard passes
  most of what each rung answers: on the standard set from 299 of 302 at `8C`
  to 126 of 127 at `D12^2`; on the held-out set from 281 of 284 at `8C` to
  14 of 20 at `A/2`.
* **The radii.** The smallest stored radius at each rung is at least the
  packing radius (P1), and at several rungs above it: the least `ρ²_p` is 10
  against `m/4 = 8` at `C`, 9 against 4 at `A`, 38 against 16 at `2A` and 64
  against 32 at `2C`. The margin between each cell's radius and the packing
  radius is what the cell guard threw away.
* **Against the union retirement.** On the fourth set the coarse-only ladder
  answers 386 correctly and the placement guard 402, both with none wrong; the
  guard keeps the fine rungs and refuses only where a fine rung is not sure.

### 7.4 What the round settles, and what it leaves

* **Settled, on four sets.** A per-cell radius read from the carriers turns
  every rung's answer into a certified-nearest answer at the cost of two
  distances; it removed every wrong answer the ladder gave on three sets it
  had not been chosen on, and kept 91–95 per cent of the correct ones.
* **Not settled.** The guard is certified-nearest, not certified-correct: a
  perturbation that carries a query nearer to another carrier and deep into
  that carrier's cell would be answered wrongly, and nothing in four sets
  rules it out for larger perturbations. The theorem
  `guarded_correct_of_close` says when that cannot happen: when the
  perturbation is shorter than half the distance from the true carrier to
  every other.
* **Left.** (i) **The guard in the answering path**: the ladder's readings in
  the escalation reports and the evaluation are unguarded; putting the
  placement guard in changes pinned answers and needs a frozen-path
  comparison. (ii) The stored radii are a per-cell table beside the carriers;
  a register that grows must re-take them, and the table should be kept beside
  the digest of the carriers it came from (D4) once it is in the answering
  path.
