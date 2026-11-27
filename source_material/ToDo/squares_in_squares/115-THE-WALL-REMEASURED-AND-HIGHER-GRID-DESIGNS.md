# 115 — The wall, remeasured: what the delivered poses actually are, and the higher-grid designs that follow

**Run 160 · 2026-11-27 · status: investigation complete; no candidate submitted.**
**Instruments:** `scripts/frontier_census.py` (new), `scripts/low_angle_grain.py` (new),
`scripts/sqscore.py`, `scripts/packlib.py`, `scripts/void_insert.py`.
**Ledgers:** `workspace/push/frontier_census.json`, `workspace/push/low_angle_grain.json`,
`workspace/push/target_audit.json`.
**Truth:** `workspace/submission/submission.csv` is the delivered geometry. `table.json` is not.

---

## 0. The answer in one paragraph

The deliverable is sound: 1000/1000 rows pass `packlib.verify`, the guard reproduces
**22.217428576459…**, with **554** beats and **446** grid ties. The wall is real, but the project has
been describing the wrong wall. For the ten bands `k = 21, 22, 24…31`, the pose the wall studies
measured — `table.json`'s `state` — is the **unclosed `k × k` margin grid**, not the delivered pose:
`reconcile_table.py` rewrote `L` to the 40-digit side but left `state` alone, so those rows still hold
`k² − j` axis-aligned cells at side `k`, with `j` unit holes. That is why the measured free square was
`0.9994–0.9999`: it was literally a unit hole in a grid that had not yet been compressed. The delivered
CSV poses for those rows are mixed, with 144–321 cells tilted (up to 24°), and the two pockets measured
are **0.733 and 0.762 of a cell**, not 0.9997 (the coarse scan finds nothing above 0.74 in the
other ten). The operative deficit is therefore **at least 24–27 % of a cell where measured**, not
0.03 %; the seating and block-substitution refutations in run 75 were run on the unclosed grid (or an
older mixed state) and do not apply to the delivered pose; and the two rows run 75 already singled out as genuine *notches* — `k = 23`
and `k = 32` — are the right targets. The designs below are local 4–20-cell pocket modules at those
measured pockets, plus the provenance repair that has to come first so the next measurement is of the
right object.

---

## 1. Reality check: the deliverable and the score

`python3 scripts/frontier_census.py` (no arguments; fast, no free-space scan):

```
delivered: score 22.217428576, beats 554, grid 446, rows 1000; illegal 0
split: beats 15.076155 + ties 7.141273 = 22.217429;
       locked 2.500830, open 4.602930, import 1.023011
```

* **Legality.** All 1000 rows pass the project's own SAT gate. The worst penetration over the whole
  file is negative; the tightest row is `n = 998` at `−5.69e-6`, which is the delivered tolerance, not a
  violation.
* **Score.** `sqscore.guard()` still expects `22.217428576459…`, 554 beats, 446 ties, and it passes.
  The score is reproducible from the CSV alone; `table.json` is not needed to score.
* **What the score is made of.** The 554 beats carry **15.076155**: 525 rows classified `beaten` plus
  29 of the 30 imports. The 446 ties carry **7.141273**: **2.500830** is locked (152 rows where the
  project's own grid/construction is already at or ahead of the record), **4.602930** is open (293 rows
  where a better packing would score), and **0.037513** is the one import tie (`n = 157`) — the three sum
  to 7.141273 exactly. The 30 catalogue imports carry **1.023011** of row score, but only **+0.008891**
  of it is *gain over what the project already had* — the rest was already matched.
* **Consequence.** The single largest accessible pool is still the 293 open ties (4.60), but the
  cheapest certain gain is the 30 imports (+0.0089). The 30-row seating ledger in run 75 is +0.23251, i.e.
  one beat per band is worth ~0.012–0.020 each, not a score-changing jackpot on its own.
  The score is a check on reality, not the reason the frontier matters: the frontier is where the
  *architecture* changes.

---

## 2. The provenance defect: 358 states are not the delivered poses

`frontier_census.py` compares every `table.json` state with its CSV row by a rounded coordinate key.
**358 of 1000 states differ.** The frontier rows affected are `k = 10` and **all of `k = 19…32`**.
The high-band breakdown is decisive:

| k | m* | stale state | state extent | true `L` | state kind |
| --- | --- | --- | --- | --- | --- |
| 21 | 423 | 423 cells | 21.000000 | 20.993728 | axis grid, 18 holes |
| 22 | 465 | 465 | 22.000000 | 21.990850 | axis grid, 19 holes |
| 23 | 509 | 509 | 22.993589 | 22.989777 | older mixed pose |
| 24 | 556 | 556 | 24.000000 | 23.995962 | axis grid, 20 holes |
| 25 | 604 | 604 | 25.000000 | 24.993299 | axis grid, 21 holes |
| 26 | 655 | 655 | 26.000000 | 25.999711 | axis grid, 21 holes |
| 27 | 707 | 707 | 27.000000 | 26.997433 | axis grid, 22 holes |
| 28 | 761 | 761 | 28.000000 | 27.993283 | axis grid, 23 holes |
| 29 | 818 | 818 | 29.000000 | 28.998653 | axis grid, 23 holes |
| 30 | 876 | 876 | 30.000000 | 29.997572 | axis grid, 24 holes |
| 31 | 936 | 936 | 31.000000 | 30.997708 | axis grid, 25 holes |
| 32 | 998 | 998 | 31.996876 | 31.986239 | older mixed pose |

For `k = 21, 22, 24…31` the stale state is **all-axis, exactly `k` distinct x and y values, own extent
exactly `k`** — the pre-compression margin sheet. It has `j` holes of side 1, so its largest free square is
a unit cell: `void_insert` reports `0.9994–0.9999`, with the missing few `1e-4` being scan resolution.
For `k = 23` and `k = 32` the stale state is a different *mixed* pose (509: 244 x-values, 227 y-values;
998: 444 x-values, 451 y-values, angles from 0.0038 rad up), so those two measurements were of a real
pose — just not the delivered one.

**Root cause.** `reconcile_table.py` rewrote `L` from the CSV and deliberately did not touch `state`.
Its own diff reports only `L`. The state column has therefore been a mixture ever since: 642 rows match
the CSV, 358 do not. There is no `state_src` field, so a reader cannot tell which is which.

**Instruments that read the stale geometry.** `void_insert.load_pose()` reads `table[str(n)]["state"]`;
`block_swap.py`, `resqueeze.py` and `notch32.py` import `load_pose` from it; `legal_slide.py` has its own
loader with the same read; `p1p_insert31.py` does the same. Every one of them is measuring a pose that is
not in the submission for the affected rows. `frontier_census.py` is the first instrument in the tree
that reads the CSV for geometry.

**What this invalidates, precisely.**

* **Run 75 §3, the ten “compressed-lattice sliver” bands.** The measured `0.9994–0.9999` is the unclosed
  grid's unit hole, and the `1 − (k−L)/k` fit is a coincidence of that grid's pitch: at side `k` every
  hole is exactly 1, and the scan's small shortfall is numerical. On the delivered pose at `k = 26` the
  same field gives **0.761940** (below). The ten bands are not slivers.
* **Run 75 §4, the eleven-band seating attempt.** It took the grid state, put a container of side
  `k − 1e-3` around it, and asked the optimizer to seat a cell. But the grid state's own extent is `k`,
  so the state *started outside the container* by `1e-3`; the optimizer's first job was to compress the
  full grid by `1e-3`, which is exactly the thing the delivered pose had already done differently. The
  reported “side grows to `k + 1.1e-4…2.4e-4`” is the signature of pushing a grid, not of a failed
  pocket. **The experiment does not test seating in the delivered pose.**
* **Run 75 §5, block substitution.** The `3 × 3` block with six cells and three holes is a block of the
  unclosed grid. The theorem `s(7) = 3` is true and remains true, but its application here only says
  that *that grid block* cannot take a seventh cell. The delivered pose's cells are tilted; it need not
  contain that block, and the theorem does not rule out a different local module.

**What survives the correction.**

* The **area ledger** is computed from `L` and `m*`, both of which are true in `table.json`; §4 of run 75
  stands.
* The **identification of `k = 23` and `k = 32` as notch rows** stands, and is strengthened: their stale
  states were mixed poses, and the true `k = 32` pose has a 0.7328 pocket.
* The **30-row / +0.23251 seating ledger** in run 75 §7 is the right target. It was never wrong; it was
  pointed at the wrong pose.
* `s(7) = 3`, the catalogue imports, the grid/Block45/Friedman reproductions and the exact-word machinery
  are independent of the state column.

---

## 3. The corrected geometry of the high bands

### 3.1 Count identity

For every frontier row, `m* = k(k−1) + r` with `r = k − j`:

| k | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 | 32 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| r | 3 | 3 | 3 | 4 | 4 | 5 | 5 | 5 | 6 | 6 | 6 | 6 |

That is not a deep theorem — it is `k² − j = k(k−1) + (k−j)` — but it is the right way to read the pose:
the count decomposes as a **`(k−1)`-wide, `k`-tall array plus `r` cells in the last column**. The row
census (24–26 cells per band at `k = 26`) is consistent with this, not a proof of it. The next row asks
for `r + 1` cells in that last column, at side `< k`. The last column's width is
`δ = k − L`, between `2.9e-4` and `1.4e-2`. This is why a global “compress by 0.03 %” story felt right and
why it is the wrong unit: the ask is **one cell in a 0.0003–0.014-wide column**, not a uniform squeeze.

### 3.2 Band table (true CSV geometry)

`V = L² − m*` is the pose's actual void. `V−1` is what remains at `n = m*+1` if the side is held — always
positive, so one added cell is **always area-feasible**. `tilt>1e-4` counts genuinely rotated cells.

| k | m* | L | δ | V | V−1 | tilt>1e-4 | stale? |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 21 | 423 | 20.993728478 | 0.006272 | 17.74 | 16.74 | 144/423 | grid |
| 22 | 465 | 21.990849853 | 0.009150 | 18.60 | 17.60 | 171/465 | grid |
| 23 | 509 | 22.989777095 | 0.010223 | 19.53 | 18.53 | 169/509 | mixed |
| 24 | 556 | 23.995962392 | 0.004038 | 19.81 | 18.81 | 196/556 | grid |
| 25 | 604 | 24.993298935 | 0.006701 | 20.66 | 19.66 | 203/604 | grid |
| 26 | 655 | 25.999711088 | 0.000289 | 20.98 | 19.98 | 235/655 | grid |
| 27 | 707 | 26.997433262 | 0.002567 | 21.86 | 20.86 | 227/707 | grid |
| 28 | 761 | 27.993283306 | 0.006717 | 22.62 | 21.62 | 233/761 | grid |
| 29 | 818 | 28.998652868 | 0.001347 | 22.92 | 21.92 | 248/818 | grid |
| 30 | 876 | 29.997571908 | 0.002428 | 23.85 | 22.85 | 321/876 | grid |
| 31 | 936 | 30.997707704 | 0.002292 | 24.86 | 23.86 | 317/936 | grid |
| 32 | 998 | 31.986238620 | 0.013761 | 25.12 | 24.12 | 317/998 | mixed |

Two consequences.

1. **Area is never the obstacle.** At `n = m*+1` and the same side, 16.7–24.1 area remains. The extra cell
   costs 1.0. Even after seating it, 15.7–23.1 remains for the cells that must be moved. The frontier is
   not area-tight; it is *shape*-tight.
2. **The pose is not a compressed grid.** 144–321 cells per band are tilted by more than `1e-4`. At
   `k = 26`: 420 cells within `1e-4` of an axis (362 within `1e-9`), **235 above `1e-4`, 214 above
   `1e-2`, max 23.86°**; 228 angle classes at `1e-9`, and the largest non-axis class is only 8 cells. At
   `k = 32`: 681 within `1e-4` (only one exactly on an axis), 317 above `1e-4`, 303 above `1e-2`, max
   20.81°, and **945 classes at `1e-9`** — the tilted cells are continuously varied, not a small grain
   vocabulary. These are **mixed poses**: an axis-like scaffold plus independently oriented cells, not a
   uniformly sheared lattice.

### 3.3 The real pocket

`frontier_census.py --at` evaluates a stated centre exactly with the same SAT field as `void_insert`:

```
k=26, n=655, at (2.38108, 8.38097), angle 0:
    free side 0.761940, deficit 0.238060
    binds cell 51 (2.5000, 7.5000) tilt  0.00°  allows 0.761940
    binds cell 64 (2.5381, 9.3557) tilt 17.35°  allows 0.762001
    binds cell 29 (1.5000, 8.5000) tilt  0.00°  allows 0.762160
    binds cell 26 (1.5000, 7.5000) tilt  0.00°  allows 0.762160

k=32, n=998, at (27.59, 0.40), angle 0:
    free side 0.732771, deficit 0.267229
    binds cell 848 (27.4374, 1.3548) tilt 17.03°  allows 0.732771
    binds cell 881 (28.4862, 0.5000) tilt  0.00°  allows 0.792404
```

Both pockets are bounded by **one tilted grain cell and an axis corner**. The `k = 26` pocket area is
`0.761940² = 0.5806`; a unit cell needs 1.0, so **0.4194 of area** must be found by moving the four binding
cells, or 0.2381 of side. The pose has 20.98 of void; the problem is not the amount, it is that the void is
fragmented into slivers that individually cannot hold a cell. The four binding cells are the ones whose
`allows` equals the pocket; two nearby cells (5 and 23) allow 1.38 and 1.76, so they are not binding and
need not move.

The automatic scan (`--pocket 26`, 84×13 grid, 5 refine rounds) settles on a *smaller* wall pocket
(0.621278 at `(2.4991, 0.5000)`) because the coarse grid misses the U-pocket's centre; the direct `--at`
value is the reproducible one. This is a property of the scan, not of the pose, and it is worth recording:
**every published pocket number should carry its centre**, or it cannot be rechecked.

### 3.4 What the stale grid's free space is

For `k = 26` the state is 655 axis cells at 26 distinct x and y values, extent 26.0000000019. It has
`676 − 655 = 21` unit holes. `void_insert` finds 0.9995 of a cell, i.e. one of those holes. The same is
true at `k = 21, 22, 24…31`. The delivered pose closes those 21 holes into a 0.762 pocket at a side
0.000289 smaller — a real, substantial rearrangement, not a 0.03 % squeeze. The scan was measuring the
*starting* object. This also explains why the “sliver” values fit `1 − δ/k` so well: *if* a `k × k` grid
were uniformly compressed to side `L`, its pitch would be `L/k` and every hole would be `1 − δ/k` wide.
The stale state is the uncompressed sheet at side `k` (holes of 1.0); the scan's 0.9995 is that unit hole.

---

## 4. What works

**Deliverable and gate.**
* 1000/1000 legal; guard exact; score 22.217428576459.
* `packlib.verify` (SAT, exact predicates), `true_geom` at 40 digits, and the C1–C4 promotion gate are
  consistent and cheap enough to run on every candidate.
* `sqscore.py` scores from the CSV alone; it cannot be fooled by a stale state.

**Constructions that reproduce rows.**
* The plain grid and the `k² − j` margin family.
* **Block45 / Block45Half / ridge** exact laws, which reproduce **369** beaten rows.
* **Friedman inflation + cascade**, which reproduces **425** rows.
* Exact 45° products (`2×2 → 3×3`, `3×3 → 4×4`) and chain-3 inheritance.
* **30 catalogue imports**, exact, +0.008891, already listed with sources in
  `workspace/push/target_audit.json`.

**Solver.**
* The analytic gradient is **86×** faster than finite differences on the real objective.
* Calibration at `n = 5, 10` meets the published values; the target regime reaches `n = 39` at
  `6.9999` in **5.3 s**, and `n = 118` with defect `2.07e-5`.
* The genuine C1–C4 discipline: a candidate that is not gate-legal never becomes a document claim.

**Instruments and analysis.**
* `void_insert`'s closed-form free-square field and its `refine` are the right local probe; with a stated
  centre they are exact and fast.
* `target_audit.py` gives the only complete score decomposition in the tree.
* `exact_words.py` (550 exact bases) and `scale_motifs.py` (36,043 comparisons) are well-built negative
  instruments: they answer their questions decisively.
* **Run 75's own structure** — price in area, then ask the local question, then the notch rows — is
  correct. Its §3 table, §4 machinery and §7 ledger are reusable once pointed at the CSV.

---

## 5. What does not work — and what is now unproven

**Refuted or exhausted (independent of the state bug).**

* **Polish / compression of a nearly-tight pose.** The measured legal gap is `1e-5…3e-4`; polish captures
  ~1 % of it, so reaching a cell needs 12–30× more than the method produces. Ceiling ≈ +0.01. This is a
  tool limit, not a wall.
* **45° families on unbeaten rows.** 0/444, best +0.071. A family whose exact law is at its own optimum
  cannot donate a cell to a different regime.
* **Carriers / branch-and-bound.** 0 survivors to `n ≤ 100`; the surviving carrier is the grid. Closed.
* **Scalable motifs.** 0 beats over 36,043 tests; every motif's `n < k²`, so it cannot reach the row.
  Closed as a family.
* **The annealer at 83 % density.** `n = 39` at +2.5e-2 and `n = 118` at `2.07e-5` are the measured
  frontier of that method; it is not a frontier tool at `k ≥ 21`.
* **The row-anchor settler.** 203 days/row at `n ≈ 100`, and it reproduces the lattice; not a route.
* **Catalogue imports in `n ≤ 324`.** Nothing left behind; the 30 rows are the only imports.

**Now unproven, because the experiment used the stale state.**

* **“Uniform compression makes the hole 0.9997 and the deficit 0.03 %.”** The delivered hole is
  0.733–0.762 where measured, and the deficit at least 24 %. The uniform-compression picture is the
  *unclosed grid's* picture.
* **“Seating a cell fails in all eleven bands.”** It fails on the grid state, for the trivial reason that
  the grid is already at side `k` and the container is `k − 1e-3`. It has not been tried on the delivered
  mixed pose.
* **“Block substitution is refuted by `s(7) = 3`.”** The theorem is true; its application assumed a `3 × 3`
  six-cell block that the delivered pose need not contain. A different 4–20-cell module is not covered.
* **Run 75's claim that the wall is “the compression itself.”** It is the pocket's shape.

**Also negative, from this run.**

* **Low-angle corner grain + rigid integer fill.** `low_angle_grain.py` tested the family: a `b × b` grain
  at `atan(1/q)`, plus every free integer slot of a `k × k` lattice at side `k − 1e-6`. Over `k = 21…32`,
  `q = 2…7`, `b = 3…12`: **0/12 bands reach the next row**. Best at `k = 26` is 618 cells (`q = 3`,
  `b = 3`) at side 25.0 (need 656 at side < 26); the shortfall is 31–45 cells across the bands. The reason is structural and worth keeping: a
  full-width row of `k` axis cells needs `L ≥ k`, so at `L < k` an integer fill loses a whole row. The
  grain angle is the right vocabulary; the **fill** must be compressed, which is exactly what the
  delivered pose does. Do not build a corner grain and expect a rigid axis fill to finish it.

---

## 6. The wall, restated

1. **Not area.** `V − 1 > 0` in every band (16.7–24.1). One cell is always affordable.
2. **Not a uniform compression.** `δ` is 0.0003–0.014; the pose is mixed, with 144–321 tilted cells and
   228–945 angle classes at `1e-9` resolution. A uniform squeeze is the wrong model.
3. **A single contiguous pocket, 0.733–0.762 where measured**, bounded by one tilted corner and an axis
   corner. The deficit is 0.238–0.267 of side; the pocket's area deficit is 0.42–0.46.
4. **The frontier's count is `(k−1) × k` plus `r = 3…6` cells in the last column.** The next row is
   `r + 1` cells there. The last column is `δ` wide. This is why the ask is local, not global.
5. **The unit of progress is a 4–20-cell module**, not a new global packing. The rest of the pose is a
   working scaffold; replacing it is the mistake the last campaigns kept making.

The wall is therefore *larger* than the documents said (24 % of a cell, not 0.03 %) and *more tractable*
(the deficit is one pocket with four binding cells, and the area to pay for it is already in the pose).

---

## 7. Designs for higher grids

Each design is stated as: target, move, first experiment, acceptance, refutation, cost. A design is a
test, not a claim.

### D0 — Repair provenance first (prerequisite, not optional)

**Target:** make “the pose” mean the CSV pose in every instrument.
**Move:** add `state_src` to `table.json` and repoint `load_pose` to the CSV (or rewrite `state` from the
CSV behind an explicit `--from-csv` flag); add a guard that for every row `extent(state) == L` to `1e-9`
and the state passes `packlib.verify`. Mark the affected run-75 numbers as *grid-state* numbers in their
headers.
**First experiment:** run the guard over all 1000; re-run `frontier_census.py`; diff.
**Acceptance:** 0 rows with `|extent(state) − L| > 1e-9`; the 358-row diff becomes 0; `sqscore.guard()`
unchanged.
**Refutation:** none — this is a correctness fix.
**Cost:** hours. **Do this before any new measurement.**

### D1 — The 5-cell pocket module (primary)

**Target:** `k = 26` first (pocket 0.761940, four binding cells), then `k = 32` (0.732771, two binding
cells). These are the two measured pockets; in run 75's table the area price is +0.120 at `k = 32` and
+0.985 at `k = 26`, while the full 30-row seating ledger is +0.23251.
**Move:** freeze the other 651 cells. Remove the four binding cells `{26, 29, 51, 64}` (at `k = 26`), insert
one cell at the pocket centre, and re-place the four somewhere in the remaining 19.98 of void. Net +1
cell, 5 cells moving, 15 degrees of freedom (11 if the tilts are held). This is the smallest move that can
beat the row; it is a *relocation*, not a re-pack.
**First experiment:** multi-start SLSQP/L-BFGS on the 5 cells, objective = maximize the minimum clearance
(or maximize the free square at the pocket centre), with the rest frozen; 20 restarts; gate every result.
Seed the new cell at `(2.38108, 8.38097, 0)` and the four at their current positions. At `k = 32`, seed at
`(27.59, 0.40, 0)`.
**Acceptance:** 656 cells, `true_geom` side `< 26`, `packlib.verify` legal, C1–C4; for `k = 32`, 999 cells
at side `< 32`. A gate-legal state that beats the row is a score gain; a near-miss with penetration
`< 1e-6` is a D2 seed, not a failure.
**Refutation:** if all 20 restarts end with a negative minimum clearance and the four cells cannot find
homes in the 19.98 void, the 5-cell module is too small; escalate to D2/D3. Do not conclude “the wall is
impossible” from this — conclude “this module is too small”.
**Cost:** minutes per restart; under an hour for both bands.

### D2 — Exact rational pocket module (2→2 or 3→3)

**Target:** the same pockets, but with an exact base, so the result can be certified in `Q(√2)`/`Q(√10)`
rather than at 40 digits.
**Move:** replace the four binding cells by a 4-cell module whose angles are exact words (0°, 45°,
`atan(1/3)`), in the same neighbourhood, leaving a unit hole; or a 3→4 module if the pocket's corner can
host one extra. Enumerate small modules by their exact footprints, gate each, and only then
optimize.
**First experiment:** enumerate 4-cell modules with one hole inside a `2.5 × 2.5` box, exact words only,
and test which fit the k=26 binding footprint (cells 26/29/51/64 span roughly `1.5…3.0 × 7.0…9.9`).
**Acceptance:** exact coordinates, gate-legal, side `< 26`; no floating-point tolerance in the claim.
**Refutation:** if no exact 4-cell module fits the footprint, the pocket is irreducibly numeric; D1's
numeric result (if any) stands but cannot enter the exact catalogue.
**Cost:** hours to a day; combinatorial but small.

### D3 — Direct band construction from the count identity (the higher-grid design)

**Target:** a *constructive* family for `m* = k(k−1) + r`, not a repair.
**Move:** build a `(k−1)`-wide, `k`-tall staggered lattice with row pitch `< 1`, plus `r` cells in a
`δ`-wide last column; the last column is a strip of low-angle cells at the measured 10–24° vocabulary,
and the pocket is the seam between the strip and the axis scaffold. Parameters: row pitch, the strip's
angle schedule (one exact word per grain), the offset of the strip, and the seam shape. The low-angle grain
screen says the strip cannot be an integer fill; the delivered pose says the scaffold can be axis-aligned
in its interior.
**First experiment:** fit the *delivered* k=26 pose to this template: cluster its 655 cells into axis rows
and tilted grains, extract the row pitches and grain angles, and check whether the template reproduces
`L = 25.999711` to `1e-6` with a small set of grain angles; then test whether those angles are within
`1e-3` of exact words. If the fit works, you have the generative rule for the band; if it does not, the
pose has a second independent mechanism and D1 is the only route.
**Acceptance:** a template that reproduces a delivered frontier pose to `1e-6` and, with `r+1` strip cells,
produces a gate-legal `m*+1` at side `< k`.
**Refutation:** if the fit needs more than two grain angles or non-constant row pitch, the template is
not predictive; fall back to D1/D2.
**Cost:** days. This is the design that would generalize to `k > 32`; D1 buys rows, D3 buys the method.

### D4 — Bank the 30 catalogue imports (certain)

**Target:** +0.008891, no geometry risk.
**Move:** replay the 30 rows from `workspace/push/target_audit.json`, `snap_certify`, C1–C4, update the
`sqscore` beat constants so the guard moves once and only once.
**Acceptance:** guard's new score equals old + 0.008891 to 12 digits; the 30 rows are legal; the import
list is recorded with sources.
**Refutation:** none; it is already verified in the audit.
**Cost:** hours. Do it while D1 runs.

### D5 — Small-`k` records (high value per row, high risk)

**Target:** `n = 20` (≈0.046) and `n = 30` (≈0.083) — a small-`n` row is worth several frontier rows.
**Move:** a two-domain pose at the record side, exact certification. These are world records; the project's
machinery has never produced one at these `n`, and the catalogue is at the record there.
**Acceptance:** a published exact packing at side below the record, or nothing.
**Refutation:** no constructive two-domain candidate after a bounded search; leave it.
**Cost:** open-ended; only after D1/D3, and only with an exact construction, not an anneal.

### Do not reopen

Carriers, scalable motifs, global polish, and the row-anchor settler are closed by measurement (§5). The
45° families are closed on unbeaten rows. The block-swap campaign can be reopened *only* on CSV poses and
*only* for a block that actually exists there — which is D1/D2 by another name.

---

## 8. Ranked plan

| # | action | why | cost | expected |
| --- | --- | --- | --- | --- |
| 1 | **D0** provenance repair + guard | every later measurement depends on it | hours | 0, but makes the rest trustworthy |
| 2 | **D4** 30 imports | certain score | hours | **+0.008891** |
| 3 | **D1 at k=32**, then k=26 | largest measured pockets; k=32 is the cheapest; smallest possible move | 1–2 days | one band beat = +0.012–0.020; validates the method |
| 4 | **D2** exact module | certifiable version of a D1 success | 1–3 days | turns a numeric row into an exact base |
| 5 | **D3** template fit | the only route that generalizes past k=32 | ~1 week | a generative rule, or a decisive negative |
| 6 | **D5** small-k records | largest per-row value | open | only with an exact two-domain pose |

**Decision gates.** After D1: if a gate-legal beat exists at either band, the “pocket module” thesis is
confirmed and D2/D3 are funded. If both fail with the four cells homeless, the thesis is that the void is
too fragmented for a 5-cell move; go to a 15–20-cell module before doubting the pocket. If D3's fit fails
to `1e-6`, the high-band pose has a second mechanism and the project should stop trying to derive it and
keep D1 as a per-band repair.

**What not to do.** Do not run another global anneal on a frontier row; do not re-run block swap on
`table.json`; do not quote a pocket without its centre; do not promote a candidate whose state is not the
CSV's.

---

## 9. Reproduction and guards

```
python3 scripts/frontier_census.py --selftest
python3 scripts/frontier_census.py                      # score, split, 358 stale, band table
python3 scripts/frontier_census.py --at 655 2.38108 8.38097 --write
python3 scripts/frontier_census.py --at 998 27.59 0.40
python3 scripts/low_angle_grain.py --selftest
python3 scripts/low_angle_grain.py --write               # the 0/12 screen
```

Guards: `frontier_census` asserts the extent of `n = 1`, the score identity
`(1/1 − 1) + (3/2 − 1) + (5/3 − 1) = 7/6` at 40 digits, and that the provenance scan finds stale rows. `low_angle_grain`
asserts the low-angle limit, the 45° corner count (13 at `k = 4`), the waste identity, and a planted
overlap. `sqscore.guard()` is unchanged.

**Limitations.** The free-square field is a local maximum; `--at` values are exact, `--pocket` values are
lower bounds. The `k = 26` pocket has been measured at one centre; the global maximum could be larger
(the scan's wall pocket is smaller, so the centre matters). The `k = 32` pocket is measured at 0.7328, not
optimized. The tilt census is exact over the CSV; the “axis vs mixed” classification of the stale states
uses `|angle| < 1e-12`, which is the right test for those grid states. No candidate was promoted; no
submission file was touched; nothing was committed.

---

## Appendix — full band table (true CSV)

```
k  m*   j  L             delta      V      V/j   tilt>1e-4  stale
21 423  18 20.993728478 0.006272  17.74  0.985   144       grid
22 465  19 21.990849853 0.009150  18.60  0.979   171       grid
23 509  20 22.989777095 0.010223  19.53  0.976   169       mixed
24 556  20 23.995962392 0.004038  19.81  0.990   196       grid
25 604  21 24.993298935 0.006701  20.66  0.984   203       grid
26 655  21 25.999711088 0.000289  20.98  0.999   235       grid
27 707  22 26.997433262 0.002567  21.86  0.994   227       grid
28 761  23 27.993283306 0.006717  22.62  0.984   233       grid
29 818  23 28.998652868 0.001347  22.92  0.997   248       grid
30 876  24 29.997571908 0.002428  23.85  0.994   321       grid
31 936  25 30.997707704 0.002292  24.86  0.994   317       grid
32 998  26 31.986238620 0.013761  25.12  0.966   317       mixed
```

`V/j` is the fraction of the “one void per missing cell” budget the pose actually spends; it is not a
deficit. The frozen `table.json` states for the “grid” rows hold the `j` unit holes of the pre-compression
sheet, which is why their free square is 0.999; `V` in this table is computed from the true `L`, not from
those states.
