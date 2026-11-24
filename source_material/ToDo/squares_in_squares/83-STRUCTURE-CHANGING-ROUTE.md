# 83 — The structure-changing route, tested (run 124, completed in run 125)

Doc 82 pointed at the family that changes *which cells sit where*: `resqueeze`'s patch-coordinate relaxation and
the block swap of run 115. This run drives it on the unbeaten rows inside a per-row budget, with controls first.
**Result: dL is zero on 20/20 rows — but the measurement shows *why*, and it is not what the first pass claimed:
one relaxation sweep costs 5–163 s against a 3 s attempt budget, so on the large rows the sweep never completed.**
Read-only: no row changed, no score moved.

## 1. Why this family is different, and what was run

The earlier local routes refused a move the moment it overlapped a cell. This one is a **penalty** method, so it
may pass *through* illegal states — which is the only way a different tiling can be reached from a packed grid.
Per row, inside the budget, three attempts:

| attempt | structural move | then |
|---|---|---|
| 0 | none | squeeze (container hinged at `L0 - 4e-3`), project, legalise |
| 1 | one cell teleported into a void (or displaced 0.4 if there is none) | same |
| 2 | a 2x2 block rotated 90° about its centroid | same |

**squeeze** pays for the box and accepts overlap; **project** removes overlap under a weak wall term;
**legalise** then expands the shape by the smallest factor that passes the 40-digit gate. dL is measured only on
a certified legal pose — an illegal result counts as **no gain**, not as a candidate.

Two instrument facts, both established here, govern how the numbers below may be read:

* the 40-digit pair pass is O(n²) — 12 s at n = 655, 85 s at n = 999, measured this run — so the driver takes the
  exact side from `true_geom.side` (O(n), same digits) and spends the pair pass only where it can change a verdict;
* a pose whose exact side is already at or above the delivered side cannot be a gain, because expansion is
  monotone in the factor. The driver stops there, which is an exact early exit, not a truncation.

## 2. Controls (run before any number was trusted)

| control | injection | outcome |
|---|---|---|
| A recovery | inflate an n=16 pose by 3.75e-3, hinge back at its side | **3.750e-3 recovered (100.0 %)**, legal, 0 violations |
| B structural absorb | displace one cell of n=12 by 0.3 | absorbed and legalised at 4.0163, **0 violations** |

So the relaxer closes a known gap of exactly the size the score needs, and it absorbs a changed arrangement.
The controls were re-run at the start and end of the pass and gave the same answers.

**Three mechanical bugs were found by these controls, and they matter beyond this run:**

1. `resqueeze.patches` (and `resqueeze.solve_patch`) penalise only patch-vs-**outside** pairs, so overlaps
   *inside* a patch are invisible — a patch can sit on top of itself and report zero penalty;
2. `resqueeze.patches` uses `while x < hi_x`, so it returns an **empty patch list** for a pose with zero extent
   in a direction and can skip the last row/column; with no patches, nothing is relaxed and the run reports a
   null for a purely mechanical reason;
3. the first version of this driver reported dL from **illegal** poses; legality is now the only currency.

**Consequence for the ledger:** run 116's "no beat" result came from an instrument carrying bugs 1 and 2. It was
re-run on the corrected driver — doc 84 — and its conclusion stands while its violation counts do not.

## 3. The measurement

20 evenly spaced unbeaten rows, three attempts each, **3 s per attempt** (9 s of budget per row):

| n | k | delivered side | squeeze side | dL | attempt outcome |
|---|---|---|---|---|---|
| 1 | 1 | 1.000000000000 | 1.000000000000 | **0** | pose at the bar |
| 33 | 6 | 6.000000001666 | 6.000000001666 | **0** | pose at the bar |
| 74 | 9 | 9.000000001778 | 9.000000001778 | **0** | pose at the bar |
| 114 | 11 | 11.000000001818 | 11.000000001818 | **0** | pose at the bar |
| 159 | 13 | 13.000000001846 | 13.000000001846 | **0** | pose at the bar |
| 196 | 14 | 14.000000001858 | 14.000000001858 | **0** | pose at the bar |
| 249 | 16 | 16.000000001875 | 16.000000001875 | **0** | pose at the bar |
| 288 | 17 | 17.000000001882 | 17.000000001882 | **0** | pose at the bar |
| 350 | 19 | 19.000000001894 | 19.000000001894 | **0** | pose at the bar |
| 393 | 20 | 20.000000001900 | 20.000000001900 | **0** | pose at the bar |
| 439 | 21 | 21.000000001904 | 21.000000001904 | **0** | pose at the bar |
| 510 | 23 | 23.000000001914 | 23.000000001914 | **0** | pose at the bar |
| 559 | 24 | 24.000000001916 | 24.000000001916 | **0** | pose at the bar |
| 610 | 25 | 25.000000001920 | 25.000000001920 | **0** | pose at the bar |
| 662 | 26 | 26.000000001924 | 26.000000001924 | **0** | pose at the bar |
| 715 | 27 | 27.000000001926 | 27.000000001926 | **0** | pose at the bar |
| 770 | 28 | 28.000000001928 | 28.000000001928 | **0** | pose at the bar |
| 826 | 29 | 29.000000001932 | 29.000000001932 | **0** | pose at the bar |
| 883 | 30 | 30.000000001934 | 30.000000001934 | **0** | pose at the bar |
| 942 | 31 | 31.000000001936 | 31.000000001936 | **0** | pose at the bar |

**Distribution: min 0, median 0, max 0; rows with any positive dL: 0/20; rows reaching 4e-3: 0/20.**
The squeeze column is the exact 40-digit side the squeeze stage reached on its own, and it equals the delivered
side on every row — so no attempt was ever in a position where legality could matter.

### Why every row is zero

Measured cost of the relaxation, one sweep = one pass over the patch list, each patch an L-BFGS solve on 27
variables with 120 iterations:

| n | patches | per patch solve | one sweep | attempt budget |
|---|---|---|---|---|
| 33 | 13 | 410 ms | **5.3 s** | 3 s |
| 439 | 194 | 374 ms | **72.6 s** | 3 s |
| 942 | 426 | 383 ms | **163.3 s** | 3 s |

A sweep is 1.8× to 54× the whole per-attempt budget. The deadline check sits between patches, so a sweep is cut
after a few dozen patches and the pose's bounding box is untouched: the squeeze returns the delivered side, the
early exit fires, and dL is 0 by construction rather than by geometry.

Where the mechanism *did* get enough time, it behaves exactly as the earlier partial pass saw. n = 33 with a 10 s
deadline (two sweeps): the squeeze reaches **5.998000642275**, i.e. 2.0e-3 below the delivered side and illegal;
legalisation then pays it back to **6.497795892793** — a **net loss of 4.98e-1**, and the ladder's first rung that
is near-legal is `f = 0.1` (a ten-percent expansion). That is the same pay-back that produced the 5e-2–1.6e-1
expansions in the earlier partial-sweep pass.

## 4. Verdict

**No positive dL on 20/20 rows — and the honest reading is narrower than "the route cannot compress".**

* Where the relaxation completed a sweep (small n, or a longer deadline), the squeeze does reach below the
  delivered side and legalisation gives back more than it gained: **n = 33, 2.0e-3 gained, 4.98e-1 returned.**
  In that regime the route is a net loss by one to two orders of magnitude more than the 4e-3 it needs.
* On the rows the score actually needs (n ≥ 250) the sweep never completed inside the budget, so **this run
  does not test the mechanism there at all**. The zeros are a throughput result, not a refusal.

So the route is **not closed by this measurement**. What is closed is the hope that a 3 s budget is enough: at
0.38 s per patch solve and 194–426 patches per sweep, the relaxation is ~20–50× too slow to run one sweep per
attempt on a real row. The named next step is therefore throughput, not geometry: cheaper patch solves (fewer
iterations, smaller patches, or an analytic slide instead of L-BFGS), then re-run this same 20-row table with a
budget that lets at least one full sweep finish. Only then is a zero informative.

The relaxer itself remains trustworthy — the 40-digit gate decides legality, the exact side is O(n), and the
early exits are monotone and exact — which is what makes it usable as the second half of a combinatorial tiling
search, the one concrete gain from this line.

## 5. Checks

| check | result |
|---|---|
| `structure.py --control` | A: 100 % recovery of 3.75e-3, legal; B: displaced cell absorbed, legal |
| `structure.py --rows 20 --seconds 3` | 20 rows, 0 positive dL, 0 candidates below the delivered side |
| relaxation cost | 5.3 s / 72.6 s / 163.3 s per sweep at n = 33 / 439 / 942 (410, 374, 383 ms per patch) |
| `perturb.py --selftest`, `anchor_chain --selftest` | green |
| `sqscore`, `record_guard`, `void_insert --selftest` | green |
| `glm_wheels --audit` | **657 functions, 0 offenders** |
| `submission.csv`, `WHITEBOARD.md` | untouched |
