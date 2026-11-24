# 75 — The grid wall, priced

**Runs 114–115.** Request: *"The Kaggle score can be moved ... I want to stop looking at the rows already
good and focus on the more difficult but actually likely to have some movement possible — can we just focus
on the un-optimised grids for a good run? ... see what is logical and what you can achieve."*

Short answer: **the grid rows are not un-optimised, they are the wall** — and these runs measured the wall
instead of arguing about it. Five results:

1. The delivered table is **not behind the published record anywhere** in `n <= 324`: 0 rows behind,
   21 ahead. There is no score sitting in the catalogue.
2. **30 bands** carry a frontier row (k = 3…32, the k = 32 band clamped at n = 1000, frontier 998 → next row
   999). Beating each band's next row by *inheriting* that band's own frontier side is worth **+0.23251** —
   more than the whole 0.163635 gap — so the instinct is right, and the money is at the band tops.
3. What blocks it is **0.03 %**: at `k >= 21` the largest square that fits a frontier pose's free space is
   **0.9994–0.9999** of a cell, not 1, and it is `1 - (k - L)/k` to within `6e-4` in ten of eleven bands —
   these poses are *uniformly compressed lattices*, and every hole is a squashed unit cell.
4. **Block substitution is refuted**, not merely tried: in all twelve `k >= 21` bands the best near-full block
   is the same **3 x 3 holding 6 cells (3 holes), needing 7 cells in 2.9994–3.0000** — short by
   `2.2e-5…8.9e-5`, which is exactly the compression, and impossible because **`s(7) = 3` is proved**.
5. **No family gives even a "slightly better than base" on an unsolved row.** Block45, Block45Half and the
   ridge cover 444 of the 446 unbeaten rows (n >= 2) and beat the base grid on **none**: closest `+0.0711`
   (n = 212, 242, 243, 244), median `+0.6066`. They beat the base only at the 369 counts where the table
   already beats it.

Instruments: `scripts/published_census.py` (benchmark + void budget), `scripts/void_insert.py` (free-space
measurement and seating, 2 controls), `scripts/block_swap.py` (block substitution), `scripts/grid_families.py`
(family coverage). None is in the float audit — they are discovery instruments, like `relax_angles.py` and
`pattern_seeds.py`. **No row changed, no score claimed.**

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

So for `n <= 324` the table *is* the record. `s(12) = 4` is conjectured (floor 3.9715), `s(k^2 - 3) = k` is
proved for `k >= 6`, and the recent 2026 improvements (Hosono, Xu, Ostashev, Chaoweeraprasit, Daniel, Couzo)
are already in our rows: n = 29 `5.93384`, n = 86 `9.82054`, n = 183 `13.99959`, n = 232 `15.76418`.

**Consequence.** A better score cannot come from importing the literature. Every remaining point is either a
new packing or a re-polish, and both campaigns are priced in §5.

## 2. What an unbeaten row actually costs

Exact, no density needed. Write `n = k^2 - j`; `j` is the number of cells missing from the `k x k` grid and
any packing has void `V = L^2 - n`. It beats the grid exactly when `L < k`, i.e. **when `V < j`**. The band's
frontier row `m*` already spends most of its budget, and the next row up must fit inside `V < j* - 1`:

    price of the next row  d(k) = V(m*) - (j* - 1)      [unit^2 of void still to save]

All **30** bands that carry a frontier row are listed (k = 3…32; band k = 32 is clamped at n = 1000, so its
frontier is 998 and its next row 999).

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
| 32 | 998 | 26 | 31.986238620 | 25.120 | 0.966 | 999 | **+0.120** |

The frontier rows spend **87–99.9 % of their void budget**; the median next row has to give up **0.72 unit^2**
of empty area. A beat is not "more search" — it is one cell's worth of void. (Band k = 32 is the cheapest
large-band price in the table at `+0.120`, and it is also *not* a compressed lattice: see §3.)

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
| 12 | 132 | 0.6726 | 22 | 465 | 0.9997 | 32 | 998 | **0.7171** |

Three modes, and they mean different things.

* **The compressed-lattice sliver: k = 21, 22, 24, 25, 26, 27, 28, 29, 30, 31 (ten bands).** The measured free
  square equals `1 - (k - L)/k` to within `6e-4` (`k = 21` 0.999726 vs 0.999701; `k = 25` 0.999665 vs
  0.999732; `k = 31` 0.999883 vs 0.999926). That is the signature of a `k x k` lattice compressed uniformly
  by `delta = k - L`: every gap shrinks to `1 - delta/k`, so *every* hole is a squashed unit cell and none of
  them is a cell.
* **Notches: k = 23 (0.7534) and k = 32 (0.7171).** These two are *not* slivers — k = 23 has the largest
  compression of the group (`delta = 0.010223`) and k = 32 sits at the top of the table; both leave a genuine
  three-quarter notch. They are the cheapest prices in the large bands (+0.530 and +0.120) and the only two
  large-band rows where a cell-sized hole is even conceivable.
* **`k <= 20`: real voids, 0.45–0.83.** These are the hand-polished mixed lattices of runs 62–113; no cell
  fits, and the shortfall (0.17–0.55) is large enough that seating one is a rearrangement, not a nudge.

## 4. Can it be done? The seating attempt

`--seat` takes the frontier pose, inserts a cell at the best free-space point, frees the cells it penetrates
(1–6 of them), adds the container as a hard hinge (a box of side `k - 1e-3` centred on the pose, so anything
legal inside is automatically a beat), asks for `1e-9` clearance rather than mere touching, and runs
L-BFGS-B on `3 (freed + 1)` variables. Verdict by `true_geom` at 40 digits.

**Eleven bands attempted (k = 21…31), zero beats.** Every run lands at side `k + 2e-9` with 2–11 violations
left and the container penalty unsatisfied by ~`4e-3`: the optimiser has to *push cells out* of the box to
make room for the cell, and it always loses. Without the container hinge the cell seats perfectly (penalty
`2e-16`) but the side grows to `k + 1.1e-4 … 2.4e-4` — the pose's own tight cells sit on the wall and there
is nowhere for the extra cell to go *inward*.

Read with §3, that is the whole story of the wall: the hole is 0.9997 of a cell, the deficit is 0.03 %, and
freeing six cells does not create 0.03 % because the compression is uniform — taking room from one hole
gives it back to the next.

## 5. Block substitution — the campaign, and why it is refuted

The move: pick a `p x q` block of the compressed lattice, count the `c` cells it holds (`h = pq - c` holes),
and try to place `c + 1` cells in the same block box. If that works the whole pose gains a cell at (nearly)
unchanged side and row `m* + 1` is beaten.

`block_swap.py` runs it on all twelve `k >= 21` band tops (the eleven sliver/notch bands k = 21…31 plus
k = 32), enumerating every block with `3 <= p <= q <= 7`, **1–3 holes and at least 4 cells** — a full block
can never gain a cell by area, and a nearly empty block proves nothing (an earlier unrestricted run "won"
trivially by repacking a 7 x 7 block holding one lonely cell; that is why the filter exists). For each block
`W = (q-1)·pitch + 1`, `T = min(W, H)`, and the fast test is
`shortfall = L_best(c + 1) - T`, with `L_best` our own table's side (at or ahead of the record, §1).

| k | blocks | fit now | best block | c → c+1 | box T | record | shortfall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 21 | 247 | 0 | 3 x 3 | 6 → 7 | 2.999403 | 3 | +0.000597 |
| 22 | 259 | 0 | 3 x 3 | 6 → 7 | 2.999168 | 3 | +0.000832 |
| 23 | 2579 | 0 | 3 x 3 | 6 → 7 | 2.999111 | 3 | +0.000889 |
| 24 | 289 | 0 | 3 x 3 | 6 → 7 | 2.999664 | 3 | +0.000336 |
| 25 | 301 | 0 | 3 x 3 | 6 → 7 | 2.999464 | 3 | +0.000536 |
| 26 | 316 | 0 | 3 x 3 | 6 → 7 | 2.999978 | 3 | **+0.000022** |
| 27 | 328 | 0 | 3 x 3 | 6 → 7 | 2.999810 | 3 | +0.000190 |
| 28 | 340 | 0 | 3 x 3 | 6 → 7 | 2.999520 | 3 | +0.000480 |
| 29 | 353 | 0 | 3 x 3 | 6 → 7 | 2.999907 | 3 | +0.000093 |
| 30 | 365 | 0 | 3 x 3 | 6 → 7 | 2.999838 | 3 | +0.000162 |
| 31 | 377 | 0 | 3 x 3 | 6 → 7 | 2.999852 | 3 | +0.000148 |
| 32 | 4193 | 0 | 3 x 3 | 6 → 7 | 2.999140 | 3 | +0.000860 |

**Not one block in any band fits, and the same block is best everywhere**: a `3 x 3` holding six cells, asked
to take a seventh in a box of 2.9991–3.0000. Three consequences, in increasing strength:

* The shortfall is the compression itself: `3·delta/k` predicts 3.3e-5 at k = 26 against the measured 2.2e-5,
  1.4e-4 at k = 29 against 9.3e-5.
* The optimiser cannot close it: packing 7 cells into those boxes stalls at penetration `1.8e-8`, `2.3e-8`,
  `7.2e-8` (k = 26, 29, 31) after 2500 iterations and four restarts — no legal state.
* It is **impossible, not hard**: `s(7) = 3` is proved (Göbel/Stromquist lineage), so seven unit squares never
  fit a box below 3. The block substitution the eleven sliver bands invite is refuted by a published
  theorem — the residual `2.2e-5…8.9e-5` is not a search target, it is a wall.

Block substitution is therefore closed as a route on the compressed-lattice rows. What survives is the
*notch* rows (§3: k = 23, 32) where the free square is a real 0.72–0.75 and the price is the smallest in the
large bands — and those need a rearrangement, not a substitution.

## 6. Do the 45° families give even "slightly better than base" on the unsolved rows?

The premise worth testing: Block45, Block45Half and the Staircase beat the plain grid at most of their own
counts, so might they give the 447 unsolved rows a hair below base? A packing of `N` cells at side `L` also
packs every `n <= N` at side `<= L` (delete cells), so a member covers a row whenever `N >= n`.

`grid_families.py` writes the three exact laws of docs 61/62/96 and evaluates them over all `N <= 1000`
(660 members), then takes, for each unbeaten row, the best member that covers it:

| family | count law | side law |
| --- | --- | --- |
| Block45 | `N = s^2 + 2k(k+1)` | `L = max(s/√2 + k + 1, s√2)`, feasible `k <= floor(s/√2) + 1` |
| Block45Half | `N = s^2 + 2k(k-1)` | `L = max(s/√2 + k + ½, s√2)`, feasible `L >= 2k - 2` |
| ridge | `N = m^2 + 1`, `m >= 2` | `L = m + ½√2` |

Result over the 444 uncovered-or-covered unbeaten rows (`n >= 2`, `n <= 999`):

* **0 beaten, 0 at parity, 444 behind.**
* Deficit `L_family - ceil(√n)`: min **+0.0711**, median **+0.6066**, max **+0.7071** (= ½√2, the ridge's
  own floor). 17 rows are within 0.15 and 43 within 0.25.
* The closest calls are all Block45: `+0.0711` at n = 212, 242, 243, 244; `+0.1213` at n = 20, 21, 30, 31,
  32, 33; `+0.1421` at n = 184, 819, 820, 877, 878 and 15 other counts.
* The families do beat the base grid — at **369** counts, and every one of them is a row the table already
  beats by other means (n = 5, 10, 17, 26, 28, 37, ...). Not one of those counts is an unsolved row, and
  that is structural: an unbeaten row is by definition a row where no member beats the grid.

So the honest answer to "do we have at least a slightly better than base for the unsolved grids?" is **no,
not one**, and the families are not merely silent there — they are 0.07–0.71 *behind*. The premise that a
45° arrangement almost always beats the standard base is true only over the counts where the grid is not
already beaten; on the unsolved set the 45° cost (`w >= ½√2` at the seam) is exactly what keeps every member
above the grid.

The "beginnings of the way" that the data does support are the two notch rows (§3, k = 23 and 32, price 0.530
and 0.120 with a real 0.72–0.75 hole) and the four Block45 near-misses at `+0.0711` (n = 212, 242, 243, 244):
those are the only places where any construction is within 5 % of a beat.

## 7. What each campaign is worth

| campaign | size | value | price |
| --- | --- | --- | --- |
| beat the next grid row in every band, **inheriting** the frontier's own side (no new construction) | 30 rows | **+0.23251** | seat one cell in a 0.9997 hole (slivers) or a 0.72 notch |
| the same, but a genuinely better construction | up to 447 rows | up to `2.9` | a world record per row |
| shave the **553 beaten rows** by 1 % of their unclaimed room | 553 rows | **+0.15023** | 0.005 of a cell per row on average |
| the same by 5 % | 553 rows | **+0.75113** | |

The unclaimed room below the 553 beaten rows is **15.02 score**. The reported leader's gap is 0.163635 — that
is **1.1 % of the room the beaten rows are still leaving on the table**, or three quarters of the inheritance
bound of the whole grid campaign.

So the logical answer to the request is uncomfortable but clean:

* The **grid rows are the right target in principle** — `+0.23251` is more than the gap, and it is the only
  large gain that does not require improving a row that is already at the record.
* But the sliver bands are refuted (§5, `s(7) = 3`), the families give nothing (§6), and the only openings
  left are the two notch rows and four Block45 near-misses — all of which need a **rearrangement**, not a
  local move or a substitution.
* The **beaten rows are where the arithmetic is easy**: 1 % of what they leave is 0.150, and it needs no new
  construction — just a tighter polish than the one that produced the record.

## 8. Instruments and checks

* `scripts/published_census.py` — §1 benchmark (324 published values, tolerance `2e-5`), §2 void budget,
  §7 pricing. Writes `workspace/published_census114.json`.
* `scripts/void_insert.py` — §3 free-space scan (`hfield`, exact separating axis), `--selftest` (2 controls
  with known answers), `--seat k...` (§4). Writes `workspace/push/void_insert114.json`, `seat114.json`.
* `scripts/block_swap.py` — §5. Writes `workspace/push/block_swap115.json` (census) and
  `block_swap115_attempt.json` (the three box-packing attempts).
* `scripts/grid_families.py` — §6. Writes `workspace/push/grid_families115.json`.
* Delivered state unchanged: `sqscore` guard OK `22.218056945` / 553 beats; `record_guard.py` OK;
  README/STATUS run-history line byte-identical. `submission.csv` untouched.

## 10. Run 116 — the standing card is placed, and the re-squeeze lead is opened and controlled

**The card.** `DIRECTORS-NOTE.md` now sits at the project top level and is pointed to from `README.md`,
`STATUS.md` and `00-OVERVIEW.md` ("Start here every run"). It carries the orientation, the "no floats"
operating definition (discovery vs proof), the proved leverage, the open leads and the C1–C4 promotion gate,
plus a review table recording that every number in it was checked against the repository. **One factual error
was corrected:** the compressed-lattice statement is about the band's *frontier pose* (`m* = k² − j*`,
`j* = 18…26` at `k >= 21`), not about `n = k² − 1`, which is a frontier row nowhere in the table.

**The lead: dynamic re-squeeze block substitution.** `resqueeze.py` inserts one cell at the exact free-space
point (`void_insert`'s scan), then runs patch-coordinate relaxation — overlapping 4.5-wide patches, each solved
on its own `3c` variables against every contact, sweeps in random order, and a **monotone acceptance test** (a
patch move is kept only if the whole-pose penalty falls). The container is placed at `k` itself.

* **Control first** (the pose alone, no insertion, k = 26) — and it earned its keep twice. A first version
  hinged the container at `k − 1e-3` and **destroyed a legal pose** (pen `0.59`, 234 violations): the wall
  penalty outweighed the overlaps, which is why the target is `k`, not `k − 1e-3`. With that fixed the control
  reads pen `2.4e-14` (max contact `7e-8`), side `26.0000000013`, 76 violations: the instrument is stable, its
  floor is ~`1e-8`, and — the substantive point — **penalty descent inflates the pose to `k`**, i.e. it spends
  the frontier's own `delta` instead of gaining room.
* **k = 26 (sliver):** n = 656, side `26.00000000132585758710…`, 79 violations, max penetration `4.6e-6`.
  Not a beat: the re-squeeze reaches `k` to `1.3e-9`, which is the sliver statement again.
* **k = 32 (notch):** n = 999, side **`31.99687596003605622186…`** — `3.1e-3` *inside* `k`, which would be
  worth `9.9e-5` — but 17 violations with max penetration `9.4e-2`, and only `1/168` then `0/168` patch moves
  accepted before it jammed. So the notch is **real room** (the side genuinely goes below `k`) and the failure
  is combinatorial, 17 pairs deep, not a lack of space.

**Verdict of the development step.** No beat, and the lead is now an instrument with a control rather than a
paragraph. Two things are established: a soft-wall penalty descent cannot gain a cell (it spends `delta`), and
the k = 32 notch can be entered — the pose reaches side below `k` — but not resolved by this descent. The named
next fix is **hard side projection** (exact container, no penalty) plus contact-graph repair on the 17 jamming
pairs rather than more descent.

## 11. Run 117 — the k = 32 notch under a hard side constraint, and the contact-graph repair

The card's first fix, implemented exactly as written. **The container is never a penalty:** after every move
each cell is clamped into the box (`x in [lo + h_x, hi - h_x]`), so every state reported here satisfies the
side constraint *exactly*, and penetration is the only objective. **The repair is a descent on the contact
graph:** for the deepest violating pair, the exact separating slide
`sign(proj) * (h_a(q) + h_b(q) + eps - |proj|)` along that pair's best axis, kept only if the whole pose's
`(pairs, sum of squared depth, deepest)` strictly improves, deepest 12 pairs per pass.

* **The notch is bigger than run 114 said.** The finer scan (140 x 33, six refine rounds) finds a free square
  of side **0.8394** at the k = 32 frontier pose, not 0.7171 — the earlier figure was a coarse-grid
  underestimate. The cell is therefore **0.1606** short of fitting, and it is placed at the hole's centre.
* **Start:** frontier 998 at side 31.986238620 plus the inserted cell → **3 violating pairs, deepest
  0.0939**.
* **Repair:** 23 passes of exact slides move the deepest bite from `9.392e-2` to `9.389e-2` — `2.0e-6` of
  total progress — and then **no single slide helps**. The fallback constrained sweep accepts **0/168**
  patches: the monotone test refuses every one, so this is a genuine local minimum of the move set, not a
  stalled loop.
* **Verdict at 40 digits (`true_geom`):** n = 999 reaches side
  **`31.99687592223010338076867830301645689164`** — `3.124e-3` inside `k = 32`, which would be worth
  `9.9e-5` — but with **6 violations**. So **no: n = 999 does not go below 32 with zero overlap.** The three
  SAT pairs are mutually blocking (closing one by an exact slide opens another), and the pose has `1.4e-2` of
  side slack against a `9.4e-2` bite.
* No candidate passes C1/C2; nothing is written to `submission.csv`, no score is claimed.

**What this settles.** The notch is real room but not a cell: 0.8394 of the 1.0 needed. The re-squeeze
recovers `3.1e-3` of side and `1.9e-4` of the bite. Closing the remaining `9.4e-2` on three mutually
blocking pairs is not a projection problem — it needs a different packing of the notch's neighbourhood.

## 12. What a 1 % capture on the 553 beaten rows really costs

The card's arithmetic is right: 1 % of the 15.02 unclaimed room is **0.15023**, and one percentage point of
capture (`e -> e + 0.01`, `e = (k - L)/(k - sqrt(n))`) is **0.21742** — both the order of the 0.163635 gap.
What the score arithmetic hides is the **price**: per row the side must fall by `dL = 0.01 (k - sqrt(n))`.

| quantity | value |
|---|---|
| beaten rows | 553 |
| `dL` needed per row for +1 pp of capture | **0.00399 – 0.00984**, median **0.00708** |
| capture `e` already taken | 0.001 – 0.495, median 0.287 |
| measured legal-gap band (run 111, doc 72 §6) | **6.2e-5 – 3.3e-4** |
| rows needing `dL <= 3.3e-4` (the whole band) | **0 / 553** |
| rows needing `dL <= 3e-3` | **0 / 553** |
| best-case polish: every row moves by the band top `3.3e-4` | **+0.00999** |
| conservative polish: band floor `6.2e-5` | +0.00188 |
| face-squeeze campaign (run 108) | 2.7e-8 |

The required move is **12x to 30x the largest local slide this project has ever measured as available**, and
**no row at all** is below `3e-3`. A 1 % capture therefore costs **21.8x the entire best-case polish
ceiling**. It is not a polish: it is **553 new constructions**, each of which must beat a certified-tight or
near-tight pose rather than nudge one. The honest value of the whole polish campaign is about **+0.01** —
one sixteenth of the gap — and the face-squeeze is `2.7e-8`.

Where the money sits, if any polish is worth doing at all: the low-capture rows are cheapest per row
(`e in [0, 0.1)`: 80 rows, 0.0202 worth, `dL` median 0.0047), the high-capture rows carry most of the value
(`e in [0.4, 0.5)`: 132 rows, 0.0622 worth, `dL` median 0.0092) — but even the cheapest row needs `0.0047`,
**fourteen times** the band's top.

## 9. Corrections to earlier documents and to run 114

* **The band count is 30, not 29 or 31.** Run 114's table looped `k = 2..31` and so silently dropped band
  k = 32, whose frontier is n = 998 and whose next row is 999 — a real target. The table above adds it, and
  the inheritance bound moves from 0.23207 to **0.23251**. The run-114 prose's "31 rows" was the same
  off-by-one.
* **Density is the wrong invariant for these rows** (perfect squares have density 1) — the void budget
  `V < j` in §2 is the right currency. A first version of the census reported a 100 % wall for that reason.
* **The "effort-limited frontier" reading is retired**: the frontier is a geometric wall in void terms, and
  the published record agrees with it on every row it covers.
* **The ridge law's validity floor is `m >= 2`**: `m = 1` reads N = 2 at L = 1.7071, which `s(2) = 2` refutes.
  The first family run reported one "beat" (n = 2) from exactly that artifact.
