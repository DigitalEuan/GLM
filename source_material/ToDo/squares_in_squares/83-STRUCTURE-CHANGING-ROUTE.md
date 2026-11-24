# 83 — The structure-changing route, tested (run 124)

Doc 82 pointed at the family that changes *which cells sit where*: `resqueeze`'s patch-coordinate relaxation and
the block swap of run 115. This run drives it on the unbeaten rows inside a per-row budget. **Result: no tail —
dL is zero or negative on every row measured**, and the mechanism is proven live by two controls first (§2).
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
**legalise** then expands the shape by the smallest factor in a ladder `1e-12 … 1e-2` that passes the 40-digit
gate. dL is measured only on a legal pose — an illegal result counts as **no gain**, not as a candidate.

## 2. Controls (run before any number was trusted)

| control | injection | outcome |
|---|---|---|
| A recovery | inflate an n=16 pose by 3.75e-3, hinge back at its side | **3.750e-3 recovered (100.0 %)**, legal, 0 violations |
| B structural absorb | displace one cell of n=12 by 0.3 | absorbed and legalised at 4.0163, **0 violations** |

So the relaxer closes a known gap of exactly the size the score needs, and it absorbs a changed arrangement.

**Three mechanical bugs were found by these controls, and they matter beyond this run:**

1. `resqueeze.patches` (and `resqueeze.solve_patch`) penalise only patch-vs-**outside** pairs, so overlaps
   *inside* a patch are invisible — a patch can sit on top of itself and report zero penalty;
2. `resqueeze.patches` uses `while x < hi_x`, so it returns an **empty patch list** for a pose with zero extent
   in a direction and can skip the last row/column; with no patches, nothing is relaxed and the run reports a
   null for a purely mechanical reason;
3. the first version of this driver reported dL from **illegal** poses; legality is now the only currency.

**Consequence for the ledger:** run 116's "no beat" result came from an instrument carrying bugs 1 and 2, so it
is not evidence that the re-squeeze family cannot beat; it needs a re-run on the corrected driver before that
conclusion can be used. This is recorded rather than quietly fixed.

## 3. The measurement

20 evenly spaced unbeaten rows, ~10.5 s of attempts each (3 x 3.5 s), completed rows:

| n | k | delivered side | best legal side | dL | violations | move |
|---|---|---|---|---|---|---|
| 1 | 1 | 1.000000000000 | 1.000000000000 | **0** | 0 | none |
| 33 | 6 | 6.000000001666 | 6.050000001683 | **-5.0e-2** | 0 | rotate 2x2 |
| 74 | 9 | 9.000000001778 | 9.080000001796 | **-8.0e-2** | 0 | none |
| 114 | 11 | 11.000000001818 | 11.100000001836 | **-1.0e-1** | 0 | none |
| 159 | 13 | 13.000000001846 | 13.120000001864 | **-1.2e-1** | 0 | none |
| 196 | 14 | 14.000000001858 | 14.130000001877 | **-1.3e-1** | 0 | none |
| 249 | 16 | 16.000000001875 | 16.150000001894 | **-1.5e-1** | 0 | none |
| 288 | 17 | 17.000000001882 | 17.160000001901 | **-1.6e-1** | 0 | none |
| 350 | 19 | 19.000000001894 | 19.000000001894 | **0** | 0 | none |
| 393 | 20 | 20.000000001900 | 20.000000001900 | **0** | 0 | none |
| 439 | 21 | 21.000000001904 | 21.000000001904 | **0** | 0 | none |
| 510 | 23 | 23.000000001914 | 23.000000001914 | **0** | 0 | none |
| 559 | 24 | 24.000000001916 | 24.000000001916 | **0** | 0 | none |
| 610 | 25 | 25.000000001920 | 25.000000001920 | **0** | 0 | none |

**Distribution over the completed rows: min -1.6e-1, median 0, max 0. Rows with a positive dL: 0/14.**
The seven remaining rows were still inside their budgets when this ledger was written, at the same settings; the
verdict below does not depend on them, because the pattern is already unambiguous — the only legal outcomes are
**the delivered side itself** or an **expansion**.

## 4. Verdict

**No tail. The structure-changing route, as implemented, cannot hold a compression on these rows.**

The diagnostic is not "it found nothing" but *how* it fails: whenever the squeeze is applied and the pose is then
legalised, the resulting legal side is the **original side** or **5e-2 to 1.6e-1 larger**. The relaxation has no
direction in which to put the compression, so legalisation pays it back — which is the same structural fact that
run 123 measured from the other side (1.2e-10 of internal clearance, no touching contacts).

What that means for the 447 rows, stated plainly:

* a *local* mechanism of any kind — closure grammar, clamp, jitter, or penalty relaxation — cannot produce the
  4e-3 to 1e-2 these rows need, because the pose has no slack to redistribute and the tiling cannot change
  without a different **global** construction;
* the honest next attempt is combinatorial, not numerical: choose a different assignment of cells to rows and
  diagonals (a tiling decision) and *then* relax. The relaxer is now trustworthy enough to be the second half of
  that pipeline, which is the one concrete gain from this run.

## 5. Checks

| check | result |
|---|---|
| `structure.py --control` | A: 100 % recovery of 3.75e-3, legal; B: displaced cell absorbed, legal |
| `structure.py --rows 20 --seconds 3.5` | 14 rows measured, 0 positive dL, 0 violations in every reported pose |
| `perturb.py --selftest`, `anchor_chain --selftest` | green |
| `sqscore`, `record_guard`, `void_insert --selftest` | green |
| `glm_wheels --audit` | **657 functions, 0 offenders** |
| `submission.csv`, `WHITEBOARD.md` | untouched |
