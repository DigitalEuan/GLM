# 75 — The grid wall, priced

**Run 114.** Request: *"The Kaggle score can be moved ... I want to stop looking at the rows already good and
focus on the more difficult but actually likely to have some movement possible — can we just focus on the
un-optimised grids for a good run? ... see what is logical and what you can achieve."*

Short answer: **the grid rows are not un-optimised, they are the wall** — and this run measured the wall
instead of arguing about it. Three results, in order of how much they change the picture:

1. The delivered table is **not behind the published record anywhere** in `n <= 324`: 0 rows behind,
   21 ahead. There is no score sitting in the catalogue.
2. The grid campaign **can** pay for the whole 0.163635 gap — beating each band's next row by inheriting
   that band's own frontier side is worth **+0.23207** — so the instinct is right, and the money is at the
   band tops.
3. What actually blocks it is **0.03 %**: at `k >= 21` the largest square that fits in a frontier pose's free
   space is **0.9994–0.9999** of a cell, not 1. It is `1 - (k - L)/k` to within `6e-4` in ten of eleven
   bands — these poses are *uniformly compressed lattices*, and every "hole" is a squashed unit cell.

Instrument: `scripts/published_census.py` (benchmark + void budget), `scripts/void_insert.py`
(free-space measurement and seating attempt, 2 controls). Neither is in the float audit — they are
discovery instruments, like `relax_angles.py` and `pattern_seeds.py`. **No row changed, no score claimed.**

---

## 1. Is the table behind the published record?

The reference is the Squares Project best-known list of 2026-10-20 (`jlevy.github.io/squares`, all 324 cases,
exact where the source writes `=`, upper bound where it writes `<=`), transcribed to 5 dp in
`published_census.py`. Tolerance `2e-5` is that transcription floor, not a geometric tolerance.

| verdict | rows | note |
| --- | --- | --- |
| equal to the published record | 303 | |
| **delivered is better** | **21** | worth `0.006414` over the record |
| behind the record | **0** | |

So for `n <= 324` the table *is* the record. `s(12) = 4` is conjectured (floor 3.9715, so nothing to be
had there), `s(k^2 - 3) = k` is proved for `k >= 6`, and the recent 2026 improvements (Hosono, Xu, Ostashev,
Chaoweeraprasit, Daniel, Couzo — cited in the source) are already in our rows: `n = 29` at `5.93384`,
`n = 86` at `9.82054`, `n = 232` at `15.76418`, `n = 261` at `16.67878`, `n = 183` at `13.99959`.

**Consequence.** A better score cannot come from importing the literature. Every remaining point is either
a new packing or a re-polish, and the two campaigns are priced in §4.

## 2. What an unbeaten row actually costs

Exact, no density needed. Write `n = k^2 - j`; `j` is the number of cells missing from the `k x k` grid and
any packing has void `V = L^2 - n`. It beats the grid exactly when `L < k`, i.e. **when `V < j`**. The band's
frontier row `m*` already spends most of its budget, and the next row up must fit inside `V < j* - 1`:

    price of the next row  d(k) = V(m*) - (j* - 1)      [unit^2 of void still to save]

| k | frontier m* | j* | L(m*) | V | V/j* | next | price d |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 5 | 4 | 2.707106782 | 2.328 | 0.582 | 6 | -0.672 |
| 4 | 11 | 5 | 3.877083592 | 4.032 | 0.806 | 12 | +0.032 |
| 5 | 19 | 6 | 4.885618085 | 4.869 | 0.812 | 20 | -0.131 |
| 6 | 29 | 7 | 5.933833464 | 6.210 | 0.887 | 30 | +0.210 |
| 7 | 41 | 8 | 6.926693096 | 6.979 | 0.872 | 42 | -0.021 |
| 8 | 55 | 9 | 7.945771009 | 8.135 | 0.904 | 56 | +0.135 |
| 9 | 71 | 10 | 8.944071559 | 8.996 | 0.900 | 72 | -0.004 |
| 10 | 89 | 11 | 9.949747470 | 9.998 | 0.909 | 90 | -0.003 |
| 11 | 110 | 11 | 10.996783398 | 10.929 | 0.994 | 111 | +0.929 |
| 12 | 132 | 12 | 11.985680201 | 11.657 | 0.971 | 133 | +0.657 |
| 13 | 156 | 13 | 12.979165856 | 12.459 | 0.958 | 157 | +0.459 |
| 14 | 183 | 13 | 13.999580181 | 12.988 | **0.999** | 184 | +0.988 |
| 15 | 211 | 14 | 14.993549628 | 13.807 | 0.986 | 212 | +0.807 |
| 16 | 241 | 15 | 15.987117097 | 14.588 | 0.973 | 242 | +0.588 |
| 17 | 273 | 16 | 16.983925965 | 15.454 | 0.966 | 274 | +0.454 |
| 18 | 308 | 16 | 17.997149123 | 15.897 | 0.994 | 309 | +0.897 |
| 19 | 344 | 17 | 18.992567547 | 16.718 | 0.983 | 345 | +0.718 |
| 20 | 382 | 18 | 19.986581715 | 17.463 | 0.970 | 383 | +0.463 |
| 21 | 423 | 18 | 20.993728478 | 17.737 | 0.985 | 424 | +0.737 |
| 22 | 465 | 19 | 21.990849853 | 18.598 | 0.979 | 466 | +0.598 |
| 23 | 509 | 20 | 22.989777095 | 19.530 | 0.977 | 510 | +0.530 |
| 24 | 556 | 20 | 23.995962392 | 19.806 | 0.990 | 557 | +0.806 |
| 25 | 604 | 21 | 24.993298935 | 20.665 | 0.984 | 605 | +0.665 |
| 26 | 655 | 21 | 25.999711088 | 20.985 | **0.999** | 656 | +0.985 |
| 27 | 707 | 22 | 26.997433262 | 21.861 | 0.994 | 708 | +0.861 |
| 28 | 761 | 23 | 27.993283306 | 22.624 | 0.984 | 762 | +0.624 |
| 29 | 818 | 23 | 28.998652868 | 22.922 | 0.997 | 819 | +0.922 |
| 30 | 876 | 24 | 29.997571908 | 23.854 | 0.994 | 877 | +0.854 |
| 31 | 936 | 25 | 30.997707704 | 24.858 | 0.994 | 937 | +0.858 |

The frontier rows spend **87–99.9 % of their void budget**; the median next row has to give up **0.72 unit^2**
of empty area. A beat is not "more search" — it is one cell's worth of void.

## 3. Where the last 0.03 % lives

§2 prices the row in *area*. The operative question is *local*: does the frontier pose contain room for one
more cell **as it stands**? If it does, that is an immediate beat — the frontier pose has side `L(m*) < k`,
so any legal unit cell inside its bounding box makes `n = m*+1` beat `k`.

`void_insert.py` answers it exactly. Two convex squares are disjoint iff one of their four edge normals
separates them, so for a candidate at `(c, t)` the feasible half-size is
`h = min_cells max_axes ((|(c-p).q| - h_u(q)) / g(t,q))`, capped by the wall distance over
`|cos t| + |sin t|`; a centre/angle scan then a local refinement finds the global maximum. Controls: 8 cells
of a `3 x 3` grid with one corner emptied must read `1.0000` (reads 1.0000), the full `3 x 3` must read
`0.0000` (reads 0.0000).

Largest square that fits in each band's frontier pose:

| k | m* | free square | k | m* | free square | k | m* | free square |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 3 | 5 | 0.6464 | 13 | 156 | 0.7593 | 23 | 509 | **0.7534** |
| 4 | 11 | 0.8317 | 14 | 183 | 0.6450 | 24 | 556 | 0.9997 |
| 5 | 19 | 0.5571 | 15 | 211 | 0.6681 | 25 | 604 | 0.9997 |
| 6 | 29 | 0.8001 | 16 | 241 | 0.6896 | 26 | 655 | 0.9995 |
| 7 | 41 | 0.6193 | 17 | 273 | 0.7561 | 27 | 707 | 0.9997 |
| 8 | 55 | 0.7561 | 18 | 308 | 0.7559 | 28 | 761 | 0.9994 |
| 9 | 71 | 0.5621 | 19 | 344 | 0.7592 | 29 | 818 | 0.9994 |
| 10 | 89 | 0.4502 | 20 | 382 | 0.7578 | 30 | 876 | 0.9996 |
| 11 | 110 | 0.6711 | 21 | 423 | 0.9997 | 31 | 936 | 0.9999 |
| 12 | 132 | 0.6726 | 22 | 465 | 0.9997 | | | |

Two modes, and they mean different things.

* **`k >= 21` (and 22): a compressed-lattice sliver.** The measured free square is `1 - (k - L)/k` to within
  `6e-4` in ten of eleven bands (`k = 21` 0.999726 vs 0.999701; `k = 25` 0.999665 vs 0.999732; `k = 31`
  0.999883 vs 0.999926). That is the signature of a `k x k` lattice compressed uniformly by `delta = k - L`:
  every gap shrinks to `1 - delta/k`, so *every* hole in the pose is a squashed unit cell and none of them
  is a cell. **`k = 23` is the exception** (`delta = 0.010223`, largest of the group, free square 0.7534):
  there the void is a genuine three-quarter notch, not a sliver.
* **`k <= 20`: real voids, 0.45–0.76.** These are the hand-polished mixed lattices of runs 62–113; no cell
  fits, and the shortfall (0.24–0.55) is large enough that seating one is a rearrangement, not a nudge.

## 4. Can it be done? The seating attempt

`--seat` takes the frontier pose, inserts a cell at the best free-space point, frees the cells it penetrates
(1–6 of them), adds the container as a hard hinge (a box of side `k - 1e-3` centred on the pose, so anything
legal inside is automatically a beat), asks for `1e-9` clearance rather than mere touching, and runs
L-BFGS-B on `3 (freed + 1)` variables. Verdict by `true_geom` at 40 digits.

**Eleven bands attempted (k = 21…31), zero beats.** Every run lands at side `k + 2e-9` with 2–11 violations
left and the container penalty unsatisfied by ~`4e-3`: the optimiser has to *push cells out* of the box to
make room for the cell, and it always loses. Without the container hinge the cell seats perfectly (penalty
`2e-16`) but the side grows to `k + 1.1e-4 … 2.4e-4` — i.e. the pose's own tight cells sit on the wall and
there is nowhere for the extra cell to go *inward*.

Read with §3, that is the whole story of the wall: the hole is 0.9997 of a cell, the deficit is 0.03 %, and
freeing six cells does not create 0.03 % because the compression is uniform — taking room from one hole
gives it back to the next. Beating these rows needs a pose that is *not* a compressed lattice, which is
exactly what the world record table also fails to have.

## 5. What each campaign is worth

| campaign | size | value | price |
| --- | --- | --- | --- |
| beat the next grid row in every band, **inheriting** the frontier's own side (no new construction) | 31 rows | **+0.23207** | seat one cell in a 0.9997 hole |
| the same, but a genuinely better construction | up to 447 rows | up to `2.9` | a world record per row |
| shave the **553 beaten rows** by 1 % of their unclaimed room | 553 rows | **+0.15023** | 0.005 of a cell per row on average |
| the same by 5 % | 553 rows | **+0.75113** | |

The unclaimed room below the 553 beaten rows is **15.02 score**. The reported leader's gap is 0.163635 — that
is **1.1 % of the room the beaten rows are still leaving on the table**, or three quarters of the inheritance
bound of the whole grid campaign.

So the logical answer to the request is uncomfortable but clean:

* The **grid rows are the right target in principle** — `+0.232` is more than the gap, and it is the only
  large gain that does not require improving a row that is already at the record.
* But **each one is a 0.03 % density record at `k >= 21`**, and a rearrangement at `k <= 20`; the search
  instruments here (single insertion + local freed cells) are the wrong shape for it, since the compression
  is uniform and local freedom does not redistribute it.
* The **beaten rows are where the arithmetic is easy**: 1 % of what they leave is 0.150, and it needs no new
  construction — just a tighter polish than the one that produced the record.

The honest recommendation: if the score is the measure, the next run should attack the **11 compressed-lattice
rows** with a *global* instrument that can redistribute compression (a lattice-doubling / block-substitution
move on the `k x k` compressed pose: replace a `p x q` block of the lattice by a rotated block of `p q + 1`
cells at a slightly larger pitch, then re-run the squeeze) — and keep the beaten-row polish as the fallback
that is guaranteed to pay. The 0.9997 measurement is the target: seat one cell in a hole that is 3e-4 short.

## 6. Instruments and checks

* `scripts/published_census.py` — §1 benchmark (324 published values, tolerance `2e-5`), §2 void budget,
  §5 pricing. Writes `workspace/published_census114.json`.
* `scripts/void_insert.py` — §3 free-space scan (`hfield`, exact separating axis), `--selftest` (2 controls
  with known answers), `--seat k...` (§4). Writes `workspace/push/void_insert114.json` and
  `workspace/push/seat114.json`.
* Delivered state unchanged: `sqscore` guard OK `22.218056945` / 553 beats; `record_guard.py` OK;
  README/STATUS run-history line byte-identical. `submission.csv` untouched.

## 7. Two corrections to earlier documents

* **Doc 73 §4 / run 113's "packing waste"** was already corrected; §2 here supersedes the earlier
  *density* framing of the grid rows (density is useless as an invariant because `n = k^2` has density 1 —
  a first version of this census reported a wall of 100 % because of exactly that). The void budget is the
  right currency: `V < j`.
* The earlier impression that the frontier is "effort-limited" (gains decaying to `0.0004`) is now
  **retired**: the frontier is a geometric wall in void terms, and the published record agrees with it on
  every row it covers.
