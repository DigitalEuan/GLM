# The cell guard — a ladder answer certified to be the nearest carrier

## Tier 0 — the coarse read

**Question.** Can each rung of the escalation ladder be made to answer only when its answer is provably the nearest carrier to the query — using two distances it already has, not a search over every carrier — and does that remove the wrong answers the ladder gives on held-out perturbations, at what cost in answers?

**Verdict.** Safe but nearly silent. The cell guard answers no query wrongly on any of the three sets, every guarded answer is the strictly nearest carrier as the Lean file proves, and the guarded ladder is order-independent; but it keeps only 30 of the ladder's 467 correct answers on the standard set and 12 of 435 and 12 of 426 on the held-out and third sets, because most carriers sit outside the inscribed ball of their own cell. The retirement rule read on the standard and held-out sets together keeps only the five coarse rungs, and that ladder answers 388 of the third set's queries correctly and none wrongly, where the ladder Phase 123 left answers one wrongly.

**Deciding figure.** 8 of 9 marks (L1, Q1, N1, N2, S1, S2, S3, U1; K1 missed); guarded ladder 30, 12 and 12 correct with 0 wrong on the three sets; unguarded ladder 467/0, 435/8 and 426/1 (middle-out order); union-retired ladder 388 correct, 0 wrong on the third set.

**Recomputed by.** `glm_universal.reasoning.cell_guard.cell_guard_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 128, committed with its Lean file and before
the module that takes the measurement exists. §§0–6 are as they were
committed; §7 is what came out.

It takes item 1 of [`STATUS.md`](../STATUS.md) §2.1, *the ladder on held-out
perturbations*, left by Phase 127
([`NORM_256_HEX_STUDY.md`](NORM_256_HEX_STUDY.md) §7.3, §7.5): on 568 held-out
queries the ladder Phase 123 left answers 8 wrongly in the middle-out order,
from three carrier pairs that sit across cell walls at `C`, `A`, `A/2`, `2D`
and `Z`. Its retirement rule had only ever been read on the original 568. The
To-Do line asks for a margin guard, or a retirement read on both sets, under a
new pre-registration with a third, unseen set. This round declares one of
each, and the third set.

**Order of work, stated plainly.**

1. *What was known before this was written.* Phase 127's record: the ladder
   (`8C 8A 4C 2C 2A C A 2D A/2 D12^2 Z`) is 467 correct, 0 wrong on the 568
   standard queries and 440 correct (oracle), 8 wrong on the 568 held-out
   ones; the three carrier pairs and rungs of §7.3 of that study. Nothing
   below had been run.
2. *The Lean file before this was committed.*
   `RequestProject/GLM/CellGuard.lean` was written and built first (§1).
3. **No guarded reading, no union retirement and no query of the third set
   had been computed when this was committed.**

## 1. What is proved before any code

`RequestProject/GLM/CellGuard.lean`, no `sorry`, `#print axioms` showing
`propext`, `Classical.choice` and `Quot.sound` only. In any metric space, for
a point set `L` whose points are at least `2r` apart and a quantiser `Q`
returning a nearest point of `L`:

* `quantise_eq_of_dist_lt` — a point within `r` of `p ∈ L` is quantised to
  `p`;
* `guarded_strict_nearest` — if the cell `Q q` holds only carrier `i` and
  `dist(q, c_i) + dist(q, Q q) < r`, then `c_i` is **strictly nearer to `q`
  than every other carrier**: every other carrier lies in another cell, so at
  least `r` from `Q q`, so at least `r − dist(q, Q q) > dist(q, c_i)` from
  `q`;
* `guarded_agree`, `firstNamed_agree` — two guarded rungs never name
  different carriers, so the first guarded answer is the same along every
  visiting order;
* `guarded_correct_of_close` — a guarded answer is right whenever the query is
  the true carrier moved by less than half its distance to every other
  carrier;
* `sqrt_add_lt_sqrt_iff` — `√A + √B < √R ↔ A + B < R ∧ 4AB < (R − A − B)²`
  for non-negative `A, B, R`: the guard is decided exactly, in rationals, with
  `A = ‖q − c_i‖²`, `B = ‖q − Q q‖²` and `R = m/4` for a rung of minimum norm
  `m`.

What the theorems do **not** say: that a guarded answer is right. A guarded
answer is the nearest carrier; when the nearest carrier is not the true one,
the guarded answer is wrong, and so is every reading that names the nearest
carrier. That is the floor the guard is measured against (§3, mark N2).

## 2. The two candidates

| key | rule | what it reads |
|---|---|---|
| `G` (the cell guard) | at every rung, answer the cell's single carrier `i` only if `‖q − c_i‖ + ‖q − Q q‖ < √m / 2`, decided by `sqrt_add_lt_sqrt_iff`; otherwise the rung refuses | two squared distances per answering rung |
| `U` (union retirement) | apply `norm_escalation.retirement` to the audit of the ladder over the standard and held-out queries together (1,136), drop every retired rung (no substitution), read the rest unguarded | the rung audit over 1,136 queries |

`G` changes no rung and no order; `U` changes the ladder and no rung's
reading. Both are read on all three query sets; only `G`'s marks decide
anything about adoption, and **nothing is put into the answering path** (§5).

## 3. The marks, declared before the code

| mark | statement |
|---|---|
| **L1** | `RequestProject/GLM/CellGuard.lean` builds with no `sorry` and the standard axioms only, with the theorems of §1. |
| **Q1** | *The hypothesis the theorems need, checked.* For every rung of the ladder, on 200 declared test vectors (a rung point, read as the quantised image of a declared sweep vector, plus a declared offset of squared length below `m/4`), the quantiser returns that point. |
| **N1** | *The theorem, checked.* On all three query sets, every guarded rung answer is the strictly nearest carrier (exact squared distances over all 142 carriers). |
| **N2** | *The floor.* On all three query sets, every wrong guarded ladder answer is a query whose nearest carrier is not its true carrier. |
| **S1** | On the 568 standard queries, the guarded ladder answers 0 wrongly and is order-independent. |
| **S2** | On the 568 held-out queries of Phase 127, the guarded ladder answers 0 wrongly. |
| **S3** | *Blind.* On the third set (§4), the guarded ladder answers 0 wrongly. |
| **K1** | On each of the three sets, the guarded ladder keeps at least half of the correct answers the unguarded ladder gives. |
| **U1** | *Blind, comparison.* On the third set, the union-retired ladder `U` answers 0 wrongly. |

**Predictions.** L1 and N1 hold (theorem). Q1 is predicted to hold: every
quantiser is an exact nearest-point decoder by its construction. S1 is
predicted to hold, since the unguarded ladder is already safe there. S2 and S3
are predicted to hold with moderate confidence: a wrong guarded answer needs
the nearest carrier to be the wrong one, which for these perturbation lengths
(squared length at most 9) and the carriers' spacing is expected to be rare
but is not ruled out. K1 is the most uncertain: the guard asks the query to be
inside the inscribed ball of its cell by the length of its own displacement,
and the coarse rungs' cells are large but the fine ones' are small. U1 is
predicted to fail more likely than hold: a rule read on two sets is still a
rule read on the sets it was read on.

## 4. The third query set, declared here

The same 142 carriers; four perturbations used by no earlier round, applied
with `ladder_escalation.perturb` to the carrier of index `i` with the codeword
index `i + 3072`:

| support | magnitude | squared length |
|---|---|---|
| 16 coordinates | 1/2 | 4 |
| 8 coordinates | 1 | 8 |
| 4 coordinates | 3/2 | 9 |
| 20 coordinates | 1/4 | 5/4 |

568 queries, generated and read once, after this document is committed.

## 5. What this round does not do

* It does not put the guard into the answering path, the deep-hole reports or
  the evaluation: that changes pinned answers and needs a frozen-path
  comparison of its own.
* It does not tune the guard. The radius is the packing radius `√m/2`, fixed
  by the rung, and the displacement is the query's own; there is no margin
  parameter to choose.
* It does not claim the guard is cheaper than a nearest-carrier search in
  general; it reports the distances it computed.

## 6. Files

| file | what |
|---|---|
| `RequestProject/GLM/CellGuard.lean` | §1 |
| `glm_universal/reasoning/cell_guard.py` | the guard, the union retirement, the third set, the marks, `cell_guard_report` |
| `glm_universal/tests/test_cell_guard.py` | the marks |
| `python3 -m glm_universal.tools cell-guard` | the measurement |

## 7. The measurement

*Written after the measurement. §§0–6 above are as they were committed.*

`python3 -m glm_universal.tools cell-guard --write` takes it and stores it
beside the digest of its sources (`reasoning/_data/cell_guard.json`);
`tools cell-guard` reads it back.

### 7.1 The verdict

Safe but nearly silent. The cell guard answers no query wrongly on any of the three sets, every guarded answer is the strictly nearest carrier as the Lean file proves, and the guarded ladder is order-independent; but it keeps only 30 of the ladder's 467 correct answers on the standard set and 12 of 435 and 12 of 426 on the held-out and third sets, because most carriers sit outside the inscribed ball of their own cell. The retirement rule read on the standard and held-out sets together keeps only the five coarse rungs, and that ladder answers 388 of the third set's queries correctly and none wrongly, where the ladder Phase 123 left answers one wrongly.

### 7.2 The marks

| mark | statement | result |
|---|---|---|
| L1 | the Lean file | **met**: `RequestProject/GLM/CellGuard.lean`, 8 named theorems, no `sorry`, `#print axioms` showing `propext`, `Classical.choice`, `Quot.sound` only |
| Q1 | the quantiser hypothesis | **met**: 0 failures in 200 vectors on each of the 11 rungs |
| N1 | every guarded answer is the strictly nearest carrier | **met**: 0 violations on all three sets |
| N2 | every wrong guarded answer is below the floor | **met**, vacuously: there is no wrong guarded answer |
| S1 | standard set: 0 wrong, order-independent | **met**: 30 correct, 0 wrong, the same in all three orders |
| S2 | held-out set: 0 wrong | **met**: 12 correct, 0 wrong; all 8 of the unguarded ladder's wrong answers are refused |
| S3 | blind, third set: 0 wrong | **met**: 12 correct, 0 wrong; the one wrong unguarded answer is refused |
| K1 | the guard keeps half the correct answers | **missed**: it keeps 30 of 467, 12 of 435 and 12 of 426 (6.4 %, 2.7 %, 2.8 %) |
| U1 | blind, third set: the union-retired ladder 0 wrong | **met**: 388 correct, 0 wrong, 180 refused, the same in all three orders |

**Scored as declared: 8 of 9.** The predictions: L1, Q1, N1 and S1 held as
predicted; S2 and S3 held; K1, declared the most uncertain, failed by a wide
margin; U1, predicted more likely to fail, held.

**The third set read unguarded.** The ladder Phase 123 left answers 426 of
the third set correctly and **1 wrongly** (`high_denominator_2x3` read as
`axis_root_e0` at `Z`, the same pair as one of the held-out wrong answers).
So the finding of Phase 127 reproduces on a set nobody had seen: the ladder's
retirement rule, read on the 568 standard queries, does not make it safe on
new perturbations.

### 7.3 Post hoc: why the guard is nearly silent

*Read after the marks, labelled post hoc.* The guard asks
`‖q − c_i‖ + ‖q − Q q‖ < r`; at `q = c_i` that is `‖c_i − Q c_i‖ < r`, so a
carrier outside the inscribed ball of its own cell can **never** be named
under the guard, however small the perturbation. The `placement` figures of
the report count how many carriers are inside that ball at each rung: from 11
(`A/2`) to 66 (`Z`) of 142, and fewer still are both inside it and alone in
their cell (1 at `8A`, 2 to 6 at the other rungs from `8C` to `A/2`, 25 at
`D12^2`, 58 at `Z`). The guard is therefore a statement about where the carriers sit
in the lattice, not about the perturbation: the carriers were placed by the
registers, not by the ladder, and most of them sit near a cell wall at every
rung. That is the price of a certificate that needs nothing but two distances.

Two further readings, description only:

* **The nearest carrier is not the floor it was declared to be.** Read on its
  own, the nearest-carrier reading (exact `ℓ²` over all 142 carriers) answers
  506, 489 and 499 correctly and **1, 13 and 7 wrongly** on the three sets,
  with 61, 66 and 62 ties. So the ladder unguarded is *safer* than the nearest
  carrier on the held-out and third sets: wrong answers there are not all
  below a floor every reading shares. No guarded answer is one of those
  wrong nearest-carrier answers on these sets.
* **The union retirement retires every fine rung.** Read on 1,136 queries,
  clause 1 retires `C` (4 wrong), `2D` (2), `A`, `A/2` and `Z` (1 each), and
  clause 2 retires `D12^2`. What is left, `8C 8A 4C 2C 2A`, is safe on the
  third set at 388 correct against the full ladder's 426: 38 correct answers
  given up to remove one wrong one.

### 7.4 What the round settles, and what it leaves

* **Settled.** A two-distance certificate that a ladder answer is the nearest
  carrier exists, is proved, and holds on every query read; it never answers
  wrongly here; and it is far too conservative to replace the ladder.
* **Settled, on one unseen set.** The coarse-only ladder that the retirement
  rule leaves when read on two sets is safe on the third.
* **Left.** (i) Putting either into the answering path needs a frozen-path
  comparison. (ii) A guard that uses the carriers' own placement — certify
  against the nearest *other* carrier's distance to the cell centre, stored
  once per rung, instead of the packing radius — would keep the theorem's
  shape with a larger radius per cell; it is a new pre-registration, not a
  re-tuning. (iii) A fourth set, to see whether the coarse-only ladder stays
  safe. *Both taken by Phase 129*
  ([`PLACEMENT_GUARD_STUDY.md`](PLACEMENT_GUARD_STUDY.md)): the placement
  guard keeps 445 of the 467 on the standard set and answers nothing wrongly
  on four sets, and the coarse-only ladder is safe on the fourth.
