# 44 — Space around the band anchors, over all orientations (Run 81)

Instrument `scripts/space_around.py` (5 controls); ledger
`workspace/push/space_around.json`. Read-only: **no row changed**, no score
claimed, `submission.csv` untouched.

**The question.** Take the last record of each of the 14 band blocks and look at
the space *around* its squares, not at a placement: what is the largest square,
at any orientation, that the free space can hold? Run 78 answered a narrower
version with six angles and a 1/16 raster; this answers it over the whole
orientation circle, and asks whether the deficit to fitting one more unit square
is uniform in orientation or only an artefact of looking at right angles.

**The answer, in two parts.**

1. **The largest empty square is 0.695 to 0.807 of a unit, and it is always at
   0°.** Every one of the 14 anchors peaks at zero tilt; at 45° the space holds
   only 0.569 to 0.632. The deficit to one more unit square is **0.193 to 0.305**
   (mean 0.252), not the ~0.1 that run 78's margins implied.
2. **It is therefore not a right-angle artefact, and it is not uniform either:**
   tilting *loses* 0.115 to 0.176 of side (mean 0.144). The free space is a
   rectangle, and a rotated square needs more room to fit in it, not less.

No orientation reaches 1, so there is nothing for the gate to judge: 0 of 42
candidate states gated, and the table is unchanged.

---

## 1. What "space around" means here, exactly

For a frozen state and a box of side L, let `s(p, theta)` be the largest square
that is centred at p, rotated by theta, inside the box, and interior-disjoint
from every packed square. Both constraints are closed-form:

    containment       s <= 2 min(p_x, L-p_x, p_y, L-p_y) / (|cos th| + |sin th|)
    inserted axes     s <= 2 (|d . u_new| - h_obs)
    packed axes       s <= (2 |d . u_old| - 1) / k

with `h_obs = (|cos dphi| + |sin dphi|)/2`, `k = |cos dphi| + |sin dphi|` in
[1, √2], and `d = p - q_old`; a packed square separates if *any* of the four
axes separates, so each gives an upper bound and the pair contributes the
largest of them. Then

    s_max(theta) = max over p of s(p, theta),      s_max = max over theta.

The position maximum is the only searched part: a covering grid seeds it, a
local subgrid resolves the peak, and a pattern search finishes to ~1e-10. Every
reported value is **attained** by a placement that the instrument re-checks with
the same closed form and with an independent vertex-projection SAT; it is a
verified achievable side, not a proof that no larger square exists.

## 2. A correction to run 78, found while building this

Run 78's `scan` required a separation of `1.0` on the *packed* square's axes.
That is the requirement for a unit square at zero tilt: on those axes the
candidate's own support is `0.5 k`, not `0.5`, so the requirement is
`0.5 k + 0.5`, up to `1.207`. At zero tilt the two agree; at a tilt the recorded
overlap is too small. So "largest empty square = 1 − margin" (0.86–0.91) is an
over-estimate, and the exact value is 0.69–0.81.

This does not weaken run 78's verdict — its scan was *optimistic* and still
found no placement, so there is none — but its number is wrong, and doc 41's
sentence about it now carries a pointer here. The error is instructive: a
penetration is not a gap, because shrinking the candidate reduces the required
separation by `(1-s)·k/2`, so the two differ by a factor between 1 and √2.

## 3. The measurement

Fourteen anchors, `n = k² + M(k)`, three boxes each (the record's own bounding
box; run 78's box `k+1−1e-6` with the record flush in a corner; the same box
with the record centred). Own box, 17 orientations from 0° to 45°:

| k | n | L₀ | s_max | at | deficit 1−s_max | s(45°) | spread over the arc |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 18 | 344 | 18.99257 | **0.70222** | 0° | 0.2978 | 0.56929 | 0.1329 |
| 19 | 382 | 19.98658 | 0.69481 | 0° | 0.3052 | 0.57978 | 0.1150 |
| 20 | 423 | 20.99373 | 0.73208 | 0° | 0.2679 | 0.59773 | 0.1344 |
| 21 | 465 | 21.99085 | 0.75062 | 0° | 0.2494 | 0.60638 | 0.1442 |
| 22 | 509 | 22.98978 | 0.75889 | 0° | 0.2411 | 0.61018 | 0.1487 |
| 23 | 556 | 23.99596 | 0.75290 | 0° | 0.2471 | 0.60743 | 0.1509 |
| 24 | 604 | 24.99330 | 0.76064 | 0° | 0.2394 | 0.61097 | 0.1552 |
| 25 | 655 | 25.99971 | 0.76133 | 0° | 0.2387 | 0.61145 | 0.1555 |
| 26 | 707 | 26.99743 | **0.80721** | 0° | 0.1928 | 0.63167 | 0.1755 |
| 27 | 761 | 27.99328 | 0.76037 | 0° | 0.2396 | 0.61085 | 0.1547 |
| 28 | 818 | 28.99865 | 0.76066 | 0° | 0.2393 | 0.61098 | 0.1552 |
| 29 | 876 | 29.99757 | 0.71218 | 0° | 0.2878 | 0.58824 | 0.1239 |
| 30 | 936 | 30.99771 | 0.75080 | 0° | 0.2492 | 0.60649 | 0.1484 |
| 31 | 998 | 31.98624 | 0.76550 | 0° | 0.2345 | 0.61319 | 0.1523 |

Summary over the 14 own-box measurements: mean `s_max = 0.74787`, deficit mean
**0.2521** (range 0.1928–0.3052); `s(45°)` mean 0.6039, so tilt costs 0.1440 of
side on average and 0.1755 at most. The box barely matters: run 78's box gives
mean 0.75023 and the centred placement 0.74976, all within 0.003 of the own-box
reading, and the argmax is at 0° in all 42 states. So the bottleneck is the
interior of the layer, not where the record sits in the container.

*Corrected and certified in run 82 (doc 45): the k = 29 row was
under-searched -- its largest empty square is **0.736113**, not 0.71218
(deficit 0.264, not 0.288); the other thirteen rows stand. Every value in
this table now carries a certified upper side, and the strongest statement
here -- that no unit square fits at any orientation -- is proved there.*

The curve is not perfectly monotone — 13 of 14 have interior wiggles at the
1e-3 scale, as the tracked pocket changes — but its maximum is at 0° in every
case and its minimum is at or near 45°.

## 4. Controls

1. Hand geometry: one unit square in a 2-box, `s_max = 1` exactly, at the
   placement that puts the second square beside it.
2. A rigid 10×10 grid at L = 10: `s_max = 0` and the gate refuses a duplicate.
3. A holed 8×8 grid: `s_max = 1` exactly, and the insertion gates at
   `L = 8 + 1e-6`.
4. Anisotropy is detected: a 0.4 strip gives 0.4 at 0° and 0.353553 = 0.4/√2 at
   45°.
5. The closed form agrees with an independent **vertex-projection** SAT on 729
   placements of a mixed-angle state (this is the control that caught run 78's
   axis shortfall — and an earlier version of this instrument's own containment
   bug, 4× too generous).

A dense re-check with a 0.05 grid at k = 18, 24, 31 and 0°, 22.5°, 45° agrees
with the ledger to ≤ 2e-5 and never beats it (the one 2e-5 difference is at an
intermediate angle, where the ledger's continuation is the better value).

## 5. What this settles, and what it does not

Settled, by measurement over all orientations:

* **No band anchor is one square from a record, in any orientation.** The
  largest empty square is at most 0.807 of a unit; one more square needs 1.0.
  The gap is 0.19–0.31, roughly a third of a unit side, not the ~0.1 that the
  six-angle raster suggested.
* **The free space is rectangular, not diamond-shaped, and tilting hurts.**
  Run 78 said "box-shaped, not diamond-shaped" from six samples; this is the
  same statement measured over the circle, with the tilt penalty quantified:
  the best tilted placement is 0.115–0.176 worse than the best axis placement.
* **The bottleneck is interior.** Moving the record inside the larger beating
  box (corner or centred) changes the largest empty square by ≤ 0.003. Freeing
  the boundary strip does not create a pocket.

Not settled, named:

* **Optimality of the measurement itself.** `s_max` is a verified achievable
  side, not a proven maximum: a placement better by more than the grid and
  pattern-search tolerance was not found, but no exhaustive arrangement argument
  is offered. The margin of error is bounded by the dense re-check (2e-5 at the
  sampled points), not by a theorem.
* **Constructions that move the squares.** Everything here freezes the record.
  The measured deficit says what a *rearranged* layer would have to buy: 0.19 to
  0.31 of side, against a band that needs `m ≥ 21` squares from a layer whose
  clean builds top out at 13 (run 79). That is a target, not a route.
* **Rows past the anchor.** The measurement is the block's last record; the
  band rows above it are strictly harder at the same side, so a negative here
  transfers to them only through the nesting argument run 78 already made.

## 6. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/space_around.py --selftest          # 5 controls (~2 s)
python3 scripts/space_around.py                     # 14 anchors × 3 boxes (~10 min)
python3 scripts/space_around.py --k 26 --step 0.05  # one anchor, finer arc
```
