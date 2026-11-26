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
| `n ≤ 225` (`p+q ≤ 21`, sides `< 15.5`) | 213,150 | 225 | 129 | **24** | **0** | 48 proved rows, silent |
| block **position** spent (`carrier_offset.py`) | 421,713 | 7 open tie rows | — | — | **0 nominations** | proved rows refused |

**Nothing was promoted.** No candidate reached a side below a delivered row, so C1–C4 was never
entered; `submission.csv` and root `WHITEBOARD.md` are untouched and the delivered total stands at
**22.217428576** (554 beats, 446 grid ties).

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

* **98 of 100 counts reached.** n = 1 and n = 2 are the two the family cannot make at all (its least
  count with `K = 2` and a block is above them).
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

* **129 of 225 counts reached**; **96 are not** — their counts are never attained at any side below
  `15.5`, a statement about the family, not about the cap (a count the family cannot make it cannot
  make anywhere, since `n` fixes the parameter box).
* **24 rows tied exactly**: `20, 30, 40, 42, 56, 57, 58, 65, 72, 73, 74, 89, 91, 92, 93, 94, 101,
  111, 112, 113, 114, 116, 117, 124`.
* **0 rows beaten**, with the falsifier silent on 48 proved rows.
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
`p + q ≤ 14` (or `21`), sides below the cap, counts below 130. The offset probe is a *probe*: 7×7
offsets at 40 sides, `p, q ≤ 19`, floats only to nominate and the exact gate on every nomination. The
directions that remain outside both are: `r ≥ 3` **with** an offset (two parameters the family has never
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

`carrier_offset.py --selftest` (5): (1) the float scan equals the exact bed rule at the centred offset on
12 declarations; (2) sliding the block moves the count and the reachable set on the offset grid is
`{8, 10, 12}` — not contiguous, which is why offsets are enumerated; (3) proved rows 13 and 22 are in the
refuse list; (4) offset 0 reproduces the centred family's count law exactly; (5) the `n = 20` scan is run
and reported either way (it reports 2,346 declarations, 0 nominations).

## 7. Reproduce

```
python3 scripts/carrier_ceil.py --selftest        # 7 controls
python3 scripts/carrier_ceil.py                   # the map at n <= 100   (21 s)
python3 scripts/carrier_ceil.py --wide            # the map at n <= 225   (~14 min)
python3 scripts/carrier_ceil.py --row 20          # every declaration that reaches 20
python3 scripts/carrier_offset.py --selftest      # 5 controls
python3 scripts/carrier_offset.py                 # the seven open tie rows (45 s)
```

Ledgers: `workspace/push/carrier_ceil.json` (the map, per row: the least side, the interval, the
declaration, the built pose's own side and count, the gate verdict), `workspace/push/carrier_offset.json`
(per row: declarations scanned, the least bed seen, nominations, verdict).

**Checks.** `sqscore.guard` green (22.217428576, 554/446) at the start of both runs; no row changed; no
candidate, so C1–C4 not entered; `submission.csv` and root `WHITEBOARD.md` untouched.
