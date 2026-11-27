# 105 — The carrier's ceiling: the whole surface swept instead of probed (Run 148)

**Headline.** Runs 145–147 measured the block-bedded carrier by *visiting* rows: an entry test on 110
delivered pairs (19 reproduced), a beat probe on those 110 (949,243 trials, 0 beats), and a probe of 19
reach rows at `r = 2..6` (124,176 trials, 0 beats). This run asks the family's question the other way
round. The family's count is a **step function of the side**, so the whole `(side, count)` surface is a
finite union of open intervals and can be *swept*, exactly, in `Q(√2)`, with integer-only comparisons.

Three measurements, all exact, all in the declared family:

| sweep | declarations | rows | reached | tied | **beaten** | falsifier |
| --- | --- | --- | --- | --- | --- | --- |
| `n ≤ 100` (`p+q ≤ 14`, sides `< 10.5`) | 25,935 | 100 | 98 | **16** | **0** | 49 proved rows, silent |
| `n ≤ 225` (`p+q ≤ 21`, sides `< 15.5`), **every count to 225** | 213,150 | 225 | **223** | **58** | **0** | 69 proved rows, silent |
| block **position** *decided* (`carrier_offset.py`, exact — doc 106) | 7,381 | 17 open rows (`n ≤ 100`) | — | — | **0** | every declaration's box list emptied |

**Nothing was promoted.** No candidate reached a side below a delivered row, so C1–C4 was never
entered; `submission.csv` and root `WHITEBOARD.md` are untouched and the delivered total stands at
**22.217428576** (554 beats, 446 grid ties).

---

## 0. Correction (Run 149): three claims in this document were wrong

Run 149 re-ran the sweep to build on it and found three defects. All are fixed here and in the code;
the table above already carries the corrected numbers, and the wide ledger was regenerated
(`workspace/push/carrier_ceil_wide.json`).

* **`counts_max` filtered the wide map at 130.** `family_map` defaults to `counts_max = 130` and the
  wide run did not override it, so every count from 131 to 225 was dropped before a row was compared
  with it. Run 148's "129 of 225 counts reached, 96 never attained" was that filter, not the family.
  With `counts_max = up_to` the same 213,150 declarations reach **223 of 225** and tie **58** rows.
  The demonstration is inside the old figure: `n = 131`, listed as never attained, is attained on
  `L ∈ (12, 12.292893218814]` by `(K, kx, ky, p, q) = (12, 1, 1, 1, 9)` — inside this very box.
* **an unattained count is not unattained everywhere.** §3's parenthetical ("a count the family
  cannot make it cannot make anywhere, since `n` fixes the parameter box") is false: the box itself
  is the bound (`K ≤ 15`, `p + q ≤ 21`, `L < 15.5`), and a count outside it may be made at a larger
  side. The correct statement is the one the sweep can support: *not attained in the declared box*.
* **§2's two missing counts are not 1 and 2.** The `n ≤ 100` map does not attain `n = 3` and `n = 99`;
  `n = 1` *is* reached, at side 2. (`n = 3` is a real gap: `pq ≤ 3` and `D = K² + pq − 3` needs a bed
  larger than a 3-cell block can cut.)

---

## 1. What was probed before, and what is swept now

A probe answers "is there a declaration at a side below this row's side" for a declared list of rows and
sides, by building and gating each one. A sweep answers "for **every** count the family can make, what
is the least side at which it makes it" — once — and then every row is a lookup. The first is a
measurement on a set of rows; the second is a measurement on the family.

The sweep is possible because the bed rule is affine in the side. A carrier cell's interior meets the
block exactly when four strict SAT inequalities hold, and with the cell's centre
`(c_x/4 + s_x·L, c_y/4 + s_y·L)` and the block centred at `(L/2, L/2)` all four are intervals in `L`:

```
|dx + dy| < 1 + p√2/2        |dy − dx| < 1 + q√2/2        |dx| < C        |dy| < C
C = 1/2 + (p+q)√2/4                                    dx = x − L/2,  dy = y − L/2
```

so each cell is bedded on **one open interval** `(lo, hi)` of sides, and `D(L)` — the number of bedded
cells — is the number of those intervals covering `L`: a step function whose steps are a finite,
computable set. Sorting the endpoints and walking them gives the count `n(L) = K² − D(L) + p·q` on every
interval, and therefore the least side at which each count is attained (`carrier_ceil.py`).

**Exactness.** Every endpoint is `(m + n√2)/4` with `m, n` integers — `Ap = (4 + 2p√2)/4`,
`Aq = (4 + 2q√2)/4`, `C = (2 + (p+q)√2)/4`, and a division by `±1` or `±1/2`. Ordering is the integer
sign test `sign(m + n√2)` (`m²` against `2n²`), so the sweep, its ordering and every count claim are
exact; only the *ratio* comparisons at the end are decimal, and only against the CSV's own 12-dp sides.

## 2. The map at `n ≤ 100`

25,935 declarations: every `K = 2..10`, every split `(kx, ky)`, every shape with `p+q ≤ 14` whose block
fits the box, every side below `10.5`.

* **98 of 100 counts reached.** `n = 3` and `n = 99` are the two this box does not attain (§0); `n = 1`
  is reached, at side 2.
* **16 rows tied exactly** at their delivered side: `20, 30, 40, 42, 56, 57, 58, 65, 72, 73, 74, 89,
  91, 92, 93, 94`. (Run 145's 19/110 was measured on the 110 two-class beats only; on the whole block
  `n ≤ 100` the family reproduces these 16, which is the same statement from the other side: the family
  reproduces the table **exactly where the table is a symmetric grid pose or a two-lattice pose of its
  own shape**, and nowhere else.)
* **0 rows beaten.** Not one declaration reaches a row's count at a side below the row's side — and this
  is now a statement about the whole surface, not about 110 rows.
* **57 rows sit above** their delivered side with a measured deficit, and three of them are near misses
  worth naming: `n = 28` above by `0.003983`, `n = 90` above by `0.005961`, `n = 12` above by
  `0.414214 = √2 − 1`. The rest are far.

**The falsifier.** The published frontier marks 48 of the rows in scope *proved optimal*. A proved
optimum cannot be beaten by any legal pose, so a sweep that reports one is wrong. The sweep reports
none, on all 48 — the control that costs nothing and would catch any interval, ordering or count error
in the instrument.

## 3. The same map at `n ≤ 225`

213,150 declarations (`K ≤ 15`, `p+q ≤ 21`, sides `< 15.5`), which covers every band `k ≤ 15`:

* **223 of 225 counts reached**; **`n = 3` and `n = 223` are not** — both statements about this box
  (`K ≤ 15`, `p + q ≤ 21`, sides `< 15.5`), never about the family anywhere (§0). `n = 223` is a
  proved-optimal row, so the family failing to make its count is the falsifier's own direction.
* **58 rows tied exactly**: `20, 30, 40, 42, 56, 57, 58, 65, 72, 73, 74, 89, 91, 92, 93, 94, 101,
  111, 112, 113, 114, 116, 117, 124, 133, 134, 135, 136, 137, 138, 145, 148, 157, 158, 159, 160,
  161, 162, 164, 165, 184, 185, 186, 187, 188, 189, 190, 197, 200, 212, 213, 214, 215, 216, 217,
  218, 220, 221`.
* **0 rows beaten**, with the falsifier silent on the 69 proved rows in scope.
* the near misses are again arithmetic, not search: `n = 28` by `0.003983`, `n = 90` by `0.005961`,
  `n = 130` by `0.097570`, `n = 110` by `0.003217`.

The band-5 question is answered inside this map, in the family's own terms. With `L < 5` the block must
fit, so `(p+q)/√2 < 5` gives `p + q ≤ 7`; with `K = 4` the count law needs `p·q − D = 4`, and the only
shapes that fit are `1×4, 2×2, 2×3, 3×3, 3×4` (`p+q ≤ 7`), demanding `D = 0, 0, 2, 5, 8`. The sweep
reports the least side the family reaches at 20 as **`5.000000000000`** — the tie — with the declaration
`(K, kx, ky, p, q) = (5, 1, 1, 1, 2)`. So the carrier reproduces band 5's tie and cannot lower it, which
is what run 131 proved for the corner-pocket mechanism and run 135 for sixteen from-scratch patterns;
it is now also a statement about every declaration of the carrier.

## 4. The one free parameter: where the block sits

> **Run 149 replaced this section's sample with a decision** (`carrier_offset.py`, doc 106: a certified
> branch and bound over `(L, cx, cy)`; run 150 then made it 7,381 declarations on every open row up to
> 100, every one emptied).
> The probe below is kept as the record of run 148, and its structural reading — that a beat needs
> `K ≤ k−1` and `L < k`, so the seam gap is under one unit and the block always beds cells — is the
> reason the decision finds nothing to keep.

All three earlier runs declared the block **centred**. Its position is the family's last unused parameter,
and it moves exactly one thing — `D`. For a row `n` and a declaration `(K, p, q)` the block must bed

```
D* = K² + p·q − n
```

cells, so the design question is arithmetic: *does any declaration admit `D*` at a side below the row's
side?* `carrier_offset.py` asks it on the **open, non-proved** tie rows — the rows whose side is the
plain grid and where the literature has not proved the grid optimal — and refuses every proved row
before looking at geometry:

| n | k | declarations over 40 sides × 7×7 offsets | least bed seen at any offset | the count law's cheapest demand | verdict |
| --- | --- | --- | --- | --- | --- |
| 12 | 4 | 1,024 | **2** | `D* = 0` at `(3, 1, 3)` | refused |
| 20 | 5 | 3,848 | **3** | `D* = 0` at `(4, 1, 4)` | refused |
| 30 | 6 | 11,934 | **4** | `D* = 0` at `(5, 1, 5)` | refused |
| 42 | 7 | 28,560 | **5** | `D* = 0` at `(6, 1, 6)` | refused |
| 56 | 8 | 60,310 | **7** | `D* = 0` at `(6, 4, 5)` | refused |
| 72 | 9 | 122,040 | **7** | `D* = 0` at `(6, 6, 6)` | refused |
| 91 | 10 | 193,997 | **10** | `D* = 0` at `(7, 6, 7)` | refused |

**421,713 declarations, 0 nominations.** The reason is structural and visible in the third column: a
beat needs `K ≤ k − 1` and `L < k`, so the seam gap `g = L − K` is **under one unit** and the carrier's
runs sit within a cell of the block's own bounding box; the block therefore always beds cells, and the
least bed it can be made to bed — sliding it anywhere in its free play — grows with `k` (2, 3, 4, 5, 7,
7, 10) while the count law, at its cheapest declaration, asks for **0**. The offset changes *which* cells
are bedded, never *how few*: the bed is a band around the block's perimeter and the perimeter is fixed by
the block's own size, which the row's count fixes.

Two further measured facts from the same probe, both of which forbid a shortcut:

* **the reachable bed is not an interval.** For a symmetric carrier with a square block the bed takes only
  even values (`{8, 10, 12}` on a 31×31 offset grid at `L = 4.9`), so "the bed sweeps every integer
  between its extremes" is false and the offsets must be enumerated, not interpolated;
* **the bed steps by more than one.** Sliding along one axis moves `D` by up to 4 at a time (four cells
  leave together by symmetry), so no bisection on `D` is sound either.

## 5. What this closes, and what it leaves

**Closed.** (i) The carrier family cannot beat any row of the table: 0 beats over 213,150 declarations
covering every band `k ≤ 15`, and 0 on the position parameter over 421,713 more. (ii) Its reach is
exactly the table's own symmetric rows — 24 ties out of 225 — which is the *positive* content of the
family and the reason it is kept as an explanatory instrument rather than a search. (iii) Band 5 in the
carrier's terms: `D = 5` at `p+q = 6` is the smallest shape that could pay, and the bed cannot be made
that small at a side below 5. (iv) `r ≥ 3` runs (run 147) and every split (this run) are both spent.

**Left, and honestly declared.** The sweep's declared box is: `r = 2` runs per axis, a **centred** block,
`p + q ≤ 14` (or `21`), sides below the cap, and every count up to the row count (§0). Run 148's
offset measurement was a 7×7-offset *sample* at 40 sides with floats nominating; run 149 (doc 106)
replaced it with an exact decision over the whole legal domain, so the position is no longer a gap.
The directions that remain outside both are: `r ≥ 3` **with** an offset (two parameters the family has never
spent together — but run 147 priced the extra translates at zero reach on their own), a **notched** block
(run 148's list, item 2), and the interleaved interface (doc 98) — none of which this family's count law
can express, because all three change the bed's *perimeter* rather than its position.

## 6. Controls

`carrier_ceil.py --selftest` (7): (1) `cell_window` agrees with `block_bed.in_bed` on 847 (cell, side)
pairs; (2) the sweep's count equals `in_bed`'s count at 92 sides over four declarations, and every
reported interval rebuilds as a gated pose of that count above the area floor; (3) the family map itself;
(4) the falsifier over the 49 proved rows in scope; (5) the four run-145 tie rows in scope are all reached
at or below their delivered side; (6) band 5: the least side the family reaches at 20 is `5.000000000000`;
(7) the bytecode audit — 14 decision functions, 0 naming float.

`carrier_offset.py --selftest` (8, after run 149 rewrote the module): (1) the pair test, the strip form
and `block_bed.in_bed` agree on 12 declaration x side pairs; (2) the rectangle's thresholds equal
`block_bed.beds`; (3) `forced <= D(point) <= possible` on 250 sampled points of 2 boxes; (4) a planted
configuration is never pruned on 70 declaration x position triples — the search has **no false zero**;
(5) the notched L is exactly the union of its two rectangles and its kept cells never leave the full
block; (6) band 5 — `(5,1,1,1,2)` builds count 20 at `L = 5` exactly, and the count law's cheapest
demand for 20 (`D* = 0`) is emptied strictly below 5; (7) the reflection identity that lets the
declarations take `p ≤ q`; (8) the bytecode audit, 23 decision functions, 0 naming float.

## 7. Reproduce

```
python3 scripts/carrier_ceil.py --selftest        # 7 controls
python3 scripts/carrier_ceil.py                   # the map at n <= 100   (21 s)
python3 scripts/carrier_ceil.py --wide            # the map at n <= 225   (~14 min)
python3 scripts/carrier_ceil.py --row 20          # every declaration that reaches 20
python3 scripts/carrier_offset.py --selftest      # 9 controls
python3 scripts/carrier_offset.py                 # every open row to 100, plain block (~13 min)
python3 scripts/carrier_offset.py --notched        # the seven rows, notched block (~25 min)
python3 scripts/carrier_offset.py --minima         # the exact least bed where it is cheap
```

Ledgers: `workspace/push/carrier_ceil.json` (the map over `n ≤ 100`; the wide map is
`workspace/push/carrier_ceil_wide.json`, written by `--wide` — this run regenerated both with the
defect of §0 fixed; per row: the least side, the interval, the declaration, the built pose's own side
and count, the gate verdict), `workspace/push/carrier_offset.json` (per row and per family: the
declarations decided, the boxes visited, the verdict).

**Checks.** `sqscore.guard` green (22.217428576, 554/446) at the start of both runs; no row changed; no
candidate, so C1–C4 not entered; `submission.csv` and root `WHITEBOARD.md` untouched.
