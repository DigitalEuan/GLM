# 90 — Band 5 by theorem, the 11 certified rows, and what the stored poses are (run 131)

**Run 131, 2026-11-25.** Instruments `scripts/band5.py` and `scripts/ext_census.py`; records
`workspace/push/band5_131.json`, `workspace/push/ext_census131.json` and `json/extended_table_5000_certified.json`.
`submission.csv` and root `WHITEBOARD.md` are untouched; `json/extended_table_5000.json` is untouched.

**The brief.** Run 130's ranking put `n = 20..23` at the top of the open, area-affordable, high-leverage rows
(band `k = 5`, `d = -0.131`, leverage `0.209–0.224`), and asked for a construction that reaches them; it also
left 11 extension rows improved but only *compared*, not certified, and a `-22` to `-28` void price unexplained.
This run does all three.

---

## 1. What the target actually is

The delivered rows 20–24 are **the plain 5×5 grid, trimmed**: `src = grid`, side `5.0000000016` (the `finalize`
pad), and **one angle class, `0.0`** — no cell is tilted. The band's frontier is `n = 19` at
`L = 4.8856180847` (45° cells), whose largest free square is `0.5571` (doc 75 §3). So the ladder inside band 5
is

```
n = 19  ->  4.8856180847  (beaten, a 45-degree construction)
n = 20  ->  5.0000000016  (the grid)          <- the target
```

and the target is *only sub-5*: 20 squares fit in 5 trivially. **Area is not the obstacle** — 20 cells in
`5 - eps` leaves `25 - 20 = 4.9` unit^2 of void, 19.6 % of the box, which is exactly the density the 19-cell
pose already achieves (19 / 4.8856^2 = 79.6 %).

## 2. The pocket bound: the mechanism caps at 17 cells below L = 5

Take an arrangement of four upright rectangular corner blocks `a_i x b_i` (each in two walls) and one unit cell
tilted 45° anywhere in the gap, every block in exact contact with one edge of that cell. Write the tilted cell's
centre as `(cx, cy)`. Its four edges are `x + y = cx + cy ± sqrt2/2` and `x - y = cx - cy ± sqrt2/2`, so the four
contact conditions are

```
a1 + b1           = cx + cy - sqrt2/2          (bottom-left block, lower-left edge)
2L - a4 - b4      = cx + cy + sqrt2/2          (top-right block, upper-right edge)
L - a2 - b2       = cx - cy + sqrt2/2          (bottom-right block, lower-right edge)
a3 - (L - b3)     = cx - cy - sqrt2/2          (top-left block, upper-left edge)
```

Adding each diagonal pair eliminates the centre:

```
(a1+b1) + (a4+b4) = 2L - sqrt2        and        (a2+b2) + (a3+b3) = 2L - sqrt2 ,
```

i.e. **both diagonal sums equal `s = 2L - sqrt2`, and `L = (s + sqrt2)/2`**. For `L < 5` we need `s <= 8`
(`s = 8` gives `L = 4.7071067811…`; `s = 9` gives `5.2071067811…`). On one diagonal two blocks with
`t1 + t2 = s` hold at most `t1^2/4 + t2^2/4 <= s^2/8` cells, so the four corners hold at most `s^2/4 = 16` and

> **n <= 17 for every arrangement of this shape with L < 5** — 3, 4, 5 and 6 cells short of rows 20, 21, 22, 23.

The enumeration is run too, not only argued: `pocket_bound(kmax=4)` lists the 604 admissible block tuples
(wall sums and all four vertices checked) below `L = 5` and finds maximum **17**, at the four `2 x 2` blocks.
That bound is **tight**: `windmill(2)` really is 17 cells at `4.7071067811 < 5`, and `exact_gate` reports
penetration exactly `0`. The same enumeration finds `n = 5` at `2.7071` (`a = 1`), so it is not blind to beats.

Two consequences worth naming:

* The mechanism *is* the 19-cell frontier's mechanism generalised — a central tilted cell with blocks in the
  corners — and band 5's frontier is the last row where it pays. `n = 17` is its largest beat below 5.
* **A pure tilted block cannot help either.** A `p x q` block of 45° cells has bounding box `(p+q)/sqrt2`, and
  `(p+q)^2 >= 4pq` gives `(p+q)/sqrt2 >= sqrt(2pq) > sqrt(pq)`: a tilted block always needs more side than the
  area floor of its own count, so 20 cells in one would need `L >= sqrt(40) = 6.3246`. Checked exactly on all
  64 `(p,q)` with `p,q <= 8`.

**Scope, stated plainly.** The bound covers *corner blocks + one 45° cell*, with no restriction on the block
sizes or on the cell's position — but it is not a lower bound for arbitrary arrangements. The run's attempt at
the general question is a budget measurement, not a proof: the repo's exact anchor-closure builder at
`L = k - 1/100` places **6 of 20** cells at a 6-node cap (3.0 s; the same parameters place 6 of 6 at `L = 3`,
so the machinery works). A capped search says nothing about the row's geometry.

**Verdict for band 5: no arrangement found, and the one mechanism that has ever beaten this band is provably
3 cells short. Nothing to promote** — C1–C4 are not met because there is no candidate.

## 3. The 11 extension rows, certified

Run 130 compared the pocket net's algebraic side `2a + sqrt2/2` with the extension table and found it smaller on
11 rows above 1000. A comparison is not a certificate, so each pose is now **gated exactly**: containment
against the exact side, and every pair that could possibly overlap, in `Q(sqrt 2)`. The pruning is sound — two
unit squares overlap only if `|dx| < sqrt2` and `|dy| < sqrt2` (the largest half-extent of either orientation is
`sqrt2/2`), and both tests are exact — so the pair list is complete, not a sample.

| n | a | k | L before | **L certified** | gain | status |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1157 | 17 | 35 | 34.970562750420 | **34.707106781187** | 0.263456 | beaten → beaten |
| 1601 | 20 | 41 | 40.798989875174 | **40.707106781187** | 0.091883 | beaten → beaten |
| 1937 | 22 | 45 | 44.920310218739 | **44.707106781187** | 0.213203 | beaten → beaten |
| 2305 | 24 | 49 | 49.0 | **48.707106781187** | 0.292893 | **tie → beaten** |
| 2501 | 25 | 51 | 50.748737343489 | **50.707106781187** | 0.041631 | beaten → beaten |
| 2705 | 26 | 53 | 53.0 | **52.707106781187** | 0.292893 | **tie → beaten** |
| 2917 | 27 | 55 | 54.870057687053 | **54.707106781187** | 0.162951 | beaten → beaten |
| 3365 | 29 | 59 | 58.991378030615 | **58.707106781187** | 0.284271 | beaten → beaten |
| 3845 | 31 | 63 | 63.0 | **62.707106781187** | 0.292893 | **tie → beaten** |
| 4097 | 32 | 65 | 64.819805155364 | **64.707106781187** | 0.112698 | beaten → beaten |
| 4625 | 34 | 69 | 68.941125498925 | **68.707106781187** | 0.234019 | beaten → beaten |

Every gate returns **`ok`, 0 violations, worst penetration exactly `0`** (no pair, no wall, is over). Controls:
`windmill(1)` gates clean at penetration `0`, and a duplicated cell is refused with penetration exactly `1.0`.

**Effect on the extension census.** Three rows leave the unbeaten set (`n = 2305, 2705, 3845` were tied to
`L = k` and are now strictly below it): the extension's unbeaten count goes **3,195 → 3,192**, and the whole
measured range **3,642 → 3,639**. The scored range is unchanged at 553 / 447, because none of these rows has
`n <= 1000`.

**Where it is recorded.** The certified sides are written as a patch,
`json/extended_table_5000_certified.json` — 11 rows, each with `L_before`, `L_after`, the source label and the
gate that licenses it. `json/extended_table_5000.json` (the run-41 measurement) stays byte-identical, so every
number quoted from it in docs 08 and 89 still reproduces. `submission.csv` is not touched.

## 4. The 33 stored poses: what the `-22` to `-28` void price actually is

The extension stores a pose for 33 rows. Read them as measured, not as guessed:

| n | L | k | tilted / cells | angle classes | +cells over `floor(L)^2` | void `V` | contact pairs | non-contact gap |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1028 | 32.5563 | 32 | 484 / 1028 | **2** | 4 | 31.92 | 2470 | 0.0607 (8 pairs) |
| 1188 | 34.9706 | 34 | 576 / 1188 | **2** | 32 | 34.94 | 2826 | 0.0251 / 0.0398 |
| 1765 | 42.4880 | 42 | 562 / 1765 | 2 | 1 | 40.23 | 6071 | **0.1011 (942 pairs)** |
| 2036 | 45.6274 | 45 | 1024 / 2036 | **2** | 11 | 45.86 | 4964 | 0.0607 |
| 2043 | 45.6964 | 45 | 666 / 2043 | 57 | 18 | 45.16 | 7244 | 0.1019 / 0.1230 |
| 2425 | 49.7487 | 49 | 1225 / 2425 | **2** | 24 | 49.94 | 5988 | 0.0251 / 0.0459 |
| 3305 | 57.9914 | 57 | 1681 / 3305 | **2** | 56 | 58.00 | 8324 | 0.0251 / 0.0459 |
| 4009 | 63.8198 | 63 | 2025 / 4009 | **2** | 40 | 63.97 | 10328 | 0.0398 / 0.0546 |
| 4921 | 70.6482 | 70 | 2401 / 4921 | **2** | 21 | 70.17 | 13338 | 0.0251 / 0.0546 |

(the record has all 33; the table above is the > 2000 subset plus `n = 1028`.)

Four measurements, and they agree on the same story.

* **Two angle classes.** 28 of the 33 poses use exactly `{0, pi/4}` — they are Göbel's 45° constructions, with
  **47–51 % of cells tilted**. The other five (`catalogue:kingbird`) use 5–57 angle classes.
* **They are jammed, not sloppy.** Every pose has thousands of pairs at *exactly* zero slack (2,470 … 13,338),
  and no pair overlaps. These are contact structures.
* **The loose part is one uniform gap, in one family of pairs.** Every non-contact pair in a pose has the *same*
  clearance: 8 pairs at `0.0607` for `n = 1028`, 8 at `0.0251` and 8 at `0.0546` for `n = 4921`, and 942 pairs at
  `0.1011` for `n = 1765`. The five distinct values across all 33 poses are
  `0.0251, 0.0398, 0.0459, 0.0607, 0.1011`. So each pose is a jammed contact core plus a sheet separated from it
  by a constant `delta`.
* **No free cell anywhere.** Probing the largest free square of either orientation on a `0.5` grid of centres
  (the same quantity doc 75 §3 reports for the scored frontiers: 0.9995 for a compressed lattice, 0.7171 for the
  `k = 32` notch) gives **negative** values on every pose above 2000 — the best centres found are `-0.0208` to
  `-0.2433`, i.e. every sampled centre sits inside some cell. At that resolution these poses are locally jammed.

**So where does the `-28` come from?** Not from a defective pose. The price is `d(k) = V(m*) - (j*-1)`, and for
the extension bands `j*` is enormous: `k = 33` has frontier `m* = 1028`, `j* = 61`, so the *next* row's budget is
`j*-1 = 60` unit^2 of void while the frontier pose uses `31.9`. In the scored bands the frontier sits `18–26`
cells below `k^2`; above 1000 it sits **36–61** cells below. The frontier is simply far from the `k^2` row, so
the band's area budget dwarfs the pose's void. `n` exceeds `floor(L)^2` by only 1–60 cells: these are *dense*
constructions (97 % occupancy), not loose ones.

**Does repairing the loose sheet generalise?** No, and the reason is geometric rather than budgetary: the sheet's
`delta` is a clearance along **one** direction, while the container side is the **maximum of two extents**. Closing
`delta` shrinks one axis; the square side is set by the other one and does not move. Recovering the gain would
mean re-tilting the sheet (changing its angles off 45°, leaving `Q(sqrt 2)`), which is a rearrangement, not a
repair. And the one exact-contact family that *does* beat the grid — the pocket net — gains a fixed
`1 - sqrt2/2 = 0.2929` at `n ≡ 1 (mod 4)` and nothing anywhere else (run 130 §5). A density-gaining construction
would have to be full at the row's own count; nothing in this run produces one, above 1000 or below it.

## 5. Verdict

**Nothing promoted.** `submission.csv` and root `WHITEBOARD.md` are untouched; the score is `22.218056945` with *(historical: at that time.)*
553 beats and 447 unbeaten rows, exactly as delivered. The extension gain is recorded in the unscored range only
(11 certified sides; 3 rows move tie → beaten), which is C4 material, not C2.

## 6. Files, records, checks

* `scripts/band5.py` (new, exact `Q(sqrt 2)`/`Fraction`/`Decimal`, no float named): `pocket_bound`,
  `bound_argument`, `tilted_block_bound`, `probe`, `selftest`, `main`.
* `scripts/ext_census.py` (new; exact `Q(sqrt 2)` gate, floats only in the labelled discovery probes):
  `gate_pose`, `pocket_rows`, `apply_certified`, `snap_q2`, `lattice_residual`, `occupancy`, `contact_census`,
  `diagnose`, `selftest`, `main`.
* `json/extended_table_5000_certified.json` — the 11-row certified patch (source table untouched).
* `workspace/push/band5_131.json`, `workspace/push/ext_census131.json` — the band-5 theorem/enumeration/probe,
  the 35 gated pocket rows, the patch, and the 33-pose diagnosis.
* **Controls.** `band5 --selftest` **4**: the bound is 17 and is attained by `windmill(2)` (gate 0); `s = 8` vs
  `s = 9` (`4.7071` vs `5.2071`); `(p+q)/sqrt2 >= sqrt(2pq)` on all 64 `(p,q)`; the 5×5 grid holds 25 at `L = 5`.
  `ext_census --selftest` **4**: the windmill gates clean; a duplicate cell is refused with penetration exactly
  `1.0`; the pocket pose reproduces the scored row 5 to the pad and the 11 certified rows are all above 1000;
  the diagnosis finds 33 stored poses with a 0.50 tilted share at `n = 2036`.
* Guards green: `range_leverage --selftest` **5**, `construct_seam --selftest` **4**, `p_screen` **4**,
  `legal_slide` **8**, `structure --control` and `--check-solver`, `perturb`, `anchor_chain`, `void_insert`,
  `true_geom`, `sqscore` **22.218056945** (553 / 447), `record_guard` OK, `glm_wheels --audit` **684 functions,
  0 offenders** (unchanged: both new files are discovery instruments, not audited decision modules),
  `py_compile` OK.
