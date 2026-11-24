# 82 — The non-closure perturbation test, and its verdict (run 123)

Doc 81 named the cheapest honest next test: let cells at **free positions** (~1e-6 slack) and ask whether a
local rearrangement shrinks the container on the unbeaten rows. It was run on **20 of the 447**, 10 s each.
**The route has no tail: dL is exactly 0 on all 20 rows**, and that null is meaningful because the same search
recovers injected slack down to ~1e-5 (controls in §2). Read-only: no row changed, no score moved.

Instrument: `scripts/perturb.py` (new). Arithmetic: `Decimal` at 40 digits with `true_geom`'s Taylor
`cos`/`sin` — no binary float touches a coordinate; `time.monotonic` only spends the budget, and the single
`float(dL)` is the *reporting* conversion.

## 1. What was searched

Take the delivered pose, hold the angles, and try three move families, each accepted only if every nearby pair
keeps slack >= 0:

| family | move |
|---|---|
| jitter | one cell displaced by delta in one of 8 directions |
| pull | a container-extreme cell displaced **inward** by delta |
| slide | two cells displaced together by delta |

deltas `1e-6, 1e-5, 1e-4, 1e-3`; a move that leaves the side unchanged is a **plateau** and is kept (drift cap
0.02) so the search can reorganise rather than stall; pairs are tested through a frozen sorted-by-x neighbour
window, so a node costs O(k) pair tests, not O(n^2).

## 2. Controls — the null only means something because these pass

| control | injected slack | recovered | verdict |
|---|---|---|---|
| inflate n = 16 grid by 0.2 % | 6.0e-3 | **5.0e-3** | route is live |
| inflate by 0.001 % | 3.0e-5 | 8.0e-6 | partial, near the floor |
| inflate by 0.00001 % | 3.0e-7 | **0** | below sensitivity |
| unit selftest | — | — | touching pair slack 0; 1e-6 slack positive; 1e-6 overlap negative |

So the search **can** close slack, and its **sensitivity floor is ~1e-5** — already below the legal-gap band's
own floor of 6.2e-5 (run 111).

## 3. The measurement: 20 unbeaten rows

Rows evenly spaced across the 447, 10 s each, seed 7, positions only:

| n | k | delivered side | dL | moves | gains | violations |
|---|---|---|---|---|---|---|
| 159 | 13 | 13.000000001846 | **0** | 3 671 | 0 | 0 |
| 196 | 14 | 14.000000001858 | **0** | 3 771 | 0 | 0 |
| 249 | 16 | 16.000000001875 | **0** | 2 994 | 0 | 0 |
| 288 | 17 | 17.000000001882 | **0** | 781 | 0 | 0 |
| 350 | 19 | 19.000000001894 | **0** | 1 545 | 0 | 0 |
| 393 | 20 | 20.000000001900 | **0** | 1 621 | 0 | 0 |
| 439 | 21 | 21.000000001904 | **0** | 462 | 0 | 0 |
| 510 | 23 | 23.000000001914 | **0** | 1 561 | 0 | 0 |
| 559 | 24 | 24.000000001916 | **0** | 1 352 | 0 | 0 |
| 610 | 25 | 25.000000001920 | **0** | 1 647 | 0 | 0 |
| 662 | 26 | 26.000000001924 | **0** | 339 | 0 | 0 |
| 715 | 27 | 27.000000001926 | **0** | 1 553 | 0 | 0 |
| 770 | 28 | 28.000000001928 | **0** | 1 379 | 0 | 0 |
| 826 | 29 | 29.000000001932 | **0** | 1 261 | 0 | 0 |
| 942 | 31 | 31.000000001936 | **0** | 533 | 0 | 0 |

(all 20 rows in `workspace/push/perturb123.json`; the rest are n = 1, 281, 617, 79, 121 — same dL = 0)

**Distribution: min 0, median 0, max 0. Rows with any gain: 0/20. Rows at or above the legal-gap floor:
0/20. Score value if applied: 0.000e+00.**

Pushing the delta ladder down to `1e-10, 1e-9, 1e-8, 1e-7` on n = 159, 249, 393 leaves dL at **0** as well
(5 053 / 5 771 / 4 287 moves). The rows are not merely tight against a coarse step; there is nothing to take.

## 4. Why: the look-ahead is already spent, not the budget

The delivered poses are not contact-touching grids — measured at 40 digits:

| n | cells | zero-slack contacts | positive-slack pairs | **min pair gap** |
|---|---|---|---|---|
| 159 | 159 | 0 | 12 561 | **1.53e-10** |
| 196 | 196 | 0 | 19 110 | **1.42e-10** |
| 249 | 249 | 0 | 30 876 | **1.24e-10** |
| 288 | 288 | 0 | 41 328 | **1.17e-10** |

Every cell is separated from every other by at least ~1e-10, so the pose is a grid inflated by **rounding
noise**: the entire geometric headroom it contains is ~1e-10. Harvesting all of it is worth ~1e-10/sqrt(n) per
row, i.e. **1e-11 of score**.

Two independent reasons therefore close this route:

1. **There is no slack to harvest.** The delivered side sits 1.8e-9 above the grid, and the pose's internal
   clearance is 1.2e-10; a local perturbation can only redistribute what exists.
2. **A real gain needs the topology to change.** Improving one of these rows by 4e-3 to 1e-2 means a different
   *packing*, not a jiggle: contacts have to be broken and rebuilt. That is a global combinatorial search, and
   the move set tested here — like the clamps of run 117 (ceiling 0.00000 on 12/12) and the closure grammar of
   runs 118–120 — cannot express it.

## 5. Verdict

**No tail. Do not scale this route.** The measured dL distribution on the 447-row target set is a point mass at
zero, and it is zero for a structural reason that no larger budget or wider move set will change: the rows are
already at their grid side with 1e-10 of internal clearance.

What the three campaigns now say together, honestly:

| route | cost per row | measured outcome |
|---|---|---|
| anchor closure settler (runs 118–122) | 8 s at n = 6 to > 150 s at n = 23 | settles at the grid side; 203-day floor at 990 cells |
| polish clamps + pricing (run 117) | < 1 s | ceiling 0.00000 on 12/12 |
| non-closure perturbation (this run) | 10 s | **dL = 0 on 20/20** |

All three are *local* in the same sense: they refine a pose that is already near the grid. The evidence now
points at one conclusion rather than another local refinement: **the 447 rows need a different packing
structure, not a better polish.** Any next effort should start from a construction that changes how many cells
sit on which diagonals (the `resqueeze`/block-swap family of run 115), and be scored by measured dL per row
before it is scaled — the same discipline that killed this route in four minutes.

## 6. Checks

| check | result |
|---|---|
| `perturb.py --selftest` | touching pair slack 0; 1e-6 slack > 0; 1e-6 overlap < 0; side exact |
| `perturb.py --control 1.002` | recovers 5.0e-3 of 6.0e-3, 0 violations |
| `perturb.py --rows 20 --seconds 10` | dL = 0 on 20/20, 0 violations everywhere |
| delta ladder to 1e-10 | still 0 on 3 rows |
| tightness measurement | min pair gap 1.17e-10 .. 1.53e-10, zero touching contacts |
| `sqscore`, `record_guard`, `void_insert --selftest`, `anchor_chain --selftest` | green |
| `glm_wheels --audit` | **657 functions, 0 offenders** |
| `submission.csv`, `WHITEBOARD.md` | untouched |
