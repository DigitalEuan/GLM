# 35 — Cubes in a cube: is the 3D optimum the extrusion of the 2D row? (Run 72)

> **Superseded in part by `36`.** Run 73 proves `L(n) = ⌈n^{1/3}⌉` for *every* n, by a sub-box
> counting argument on the centres. So the values below are exact optima, not constructions: the
> "n >= 5 are constructions, not optima" caveat in §3, §5 and §7 is withdrawn, and `L(9)`, left open
> in `(2, 3]` here, is exactly 3. The instrument and its controls stand.

`SQUARES.md` in `dimension_ladder` left one concrete question open: the dimension ladder cannot
touch this project through the plane — it can only touch it one dimension up. So the 3D analogue of
`declp` was built (`scripts/declp3.py`), judged by its own exact gate, and asked the question
directly: **is the 3D optimum the extrusion of the delivered 2D row, or strictly better?**

Answer: **the extrusion is optimal for n = 2, 3, 4 and is strictly beaten for every row from n = 5
to 8 — where the 3D optimum is exactly 2, proved — and again at n = 10, 12, 16, 20.** At n = 9 the
two tie at 3, and the true value is left open in `(2, 3]`.

No row of the 2D table changed. The delivered total is still `22.218056945`, 553 beats, and
`sqscore.guard()` holds: this run adds a dimension, not a score.

## 1. The model, and why it is the honest one dimension up

`declp` decides, for unit squares with frozen angles, whether a *declared* separating axis per pair
survives a shrink. The 3D analogue keeps every part of that discipline and drops only what cubes do
not have — rotation:

    state      centres c_i in R^3, container [-L/2, L/2]^3, cubes axis-parallel, side 1
    branch     one (axis, sign) per pair:   s * (c_j - c_i).e_q >= 1
    variables  a translation d_i in R^3 per cube, and t = L
    objective  minimise t

The LP is a *relaxation*: it enforces only each pair's declared axis, so its state can be invalid on
the axes it did not declare. `declp3.gate` is therefore the only judge, and it is exact — stronger
than the 2D gate. Coordinates are rounded to 12 dp and then read as `Fraction`s, so pairwise
penetration and the container side are **rational arithmetic on the recorded numbers**; there is no
tolerance constant in the verdict. `worst_pen <= 0` is an exact statement about the state as written.

## 2. The one theorem this hinges on

Two axis-parallel unit cubes in a box of side `L < 2` must intersect: in each axis their intervals
have length 1 inside an interval of length `< 2`, so they overlap in every axis. Hence

    L(n) >= 2 for every n >= 2,      and the 2x2x2 grid gives L = 2 for n <= 8,

so **L(n) = 2 exactly for 2 <= n <= 8**. That is what makes the comparison with the 2D row sharp
rather than suggestive: at n = 5 the 2D table needs 2.7071 and 3D provably needs 2.

## 3. The run

12 rows, `python3 scripts/declp3.py` (71 s, dominated by the exhaustive part in §5). `algn` says
whether the delivered 2D row is axis-aligned — a rotated square is not a unit cube, so on the two
non-aligned rows the "extrusion" is only *the cubes at those centres*.

| n | algn | L2 (2D) | extr | grid3 | desc(extr) | desc(grid) | verdict |
|---:|---|---:|---:|---:|---:|---:|---|
| 2 | yes | 2.0000 | 2.0000 | 2.0000 | 2.0000 | 2.0000 | tie — extrusion optimal (= 2, proved) |
| 3 | yes | 2.0000 | 2.0000 | 2.0000 | 2.0000 | 2.0000 | tie — extrusion optimal (= 2, proved) |
| 4 | yes | 2.0000 | 2.0000 | 2.0000 | 2.0000 | 2.0000 | tie — extrusion optimal (= 2, proved) |
| 5 | no | 2.7071 | 2.7071 | 2.0000 | 2.7071 | 2.0000 | **3D strictly better** (2, proved) |
| 6 | yes | 3.0000 | 3.0000 | 2.0000 | 3.0000 | 2.0000 | **3D strictly better** (2, proved) |
| 7 | yes | 3.0000 | 3.0000 | 2.0000 | 3.0000 | 2.0000 | **3D strictly better** (2, proved) |
| 8 | yes | 3.0000 | 3.0000 | 2.0000 | 3.0000 | 2.0000 | **3D strictly better** (2, proved) |
| 9 | yes | 3.0000 | 3.0000 | 3.0000 | 3.0000 | 3.0000 | tie at 3; L(9) in (2, 3] open |
| 10 | no | 3.7071 | 3.7071 | 3.0000 | 3.7071 | 3.0000 | **3D strictly better** |
| 12 | yes | 4.0000 | 4.0000 | 3.0000 | 4.0000 | 3.0000 | **3D strictly better** |
| 16 | yes | 4.0000 | 4.0000 | 3.0000 | 4.0000 | 3.0000 | **3D strictly better** |
| 20 | yes | 5.0000 | 5.0000 | 3.0000 | 5.0000 | 3.0000 | **3D strictly better** |

Two things in that table matter more than the verdict column.

* **`desc(extr) = L2` on every row.** The extrusion is not merely *a* packing — it is rigid under its
  own declared axes. The LP cannot shrink it at all, in 3D, for any of the twelve rows. So the
  improvement at n = 5–8 is not "the same structure, polished"; it is a **different structure**.
  Extrusion is a local optimum of the declared-axis system and not the global one.
* **The 2D row's whole interest does not survive the increase in dimension, in this sample.** For
  n <= 8 the cube grid meets the two-cube bound exactly, so no improvement is possible; the first row
  with any room at all is n = 9 (volume `9 > 8`). In the same range the 2D table beats its own grid
  at 553 rows out of 1000. Nothing here found a 3D grid beat — which is *not* a theorem, only the
  absence of one in twelve rows by two descent paths.

## 4. Two defects, both caught by the degradation control

The gates and the descent were written after the control, and the control earned its place twice.
Control 1 asks the 3D instrument, with `z` pinned and only `x`/`y` declared, to reproduce `declp`'s
own minimum side on an axis-aligned row. It refused three times:

1. the containment rows had `0.5 - c` and `0.5 + c` where the algebra gives `-0.5 - c` and
   `-0.5 + c`, so the LP was shrinking boxes the state could not occupy (`3D 2.0` against `2D 3.707`);
2. after that, states were not centred, so the per-cube move bound blocked the free translation and
   the LP reported a *larger* side than the 2D one (`2.8` against `2.0`) — centring is free, and the
   model must do it;
3. the reference value itself was taken from `declp.max_shrink`, whose window stops at 1e−2, so it
   saturated and compared the wrong number.

This is run 67's lesson in a new place: a copy of a constraint system drifts by a constant and still
looks like a certificate. The control is the reason these are recorded as defects rather than as
results.

## 5. Exhaustive branch bounds (n <= 4)

Enumerating all `6^C(n,2)` declared structures and taking the minimum LP side is a valid lower bound
(the optimum has *some* branch; the LP relaxes everything else):

| n | branches | best LP side |
|---:|---:|---:|
| 2 | 6 | 2.000000 |
| 3 | 216 | 2.000000 |
| 4 | 46,656 | 2.000000 |

All three agree with Lemma §2, which is the point: the LP is the instrument the lemma predicts, and
the lemma is what closes n = 2–8 without any enumeration at all. Above n = 4 the enumeration is
`6^10 ≈ 6.0e7` at n = 5 and hopeless thereafter, so **no LP lower bound is claimed above n = 4** —
the values in §3 for n >= 5 are constructions (upper bounds), not optima.

## 6. Controls

```
python3 scripts/declp3.py --control
```

* **degradation** — n = 4, 12, 22, 35 with `z` pinned: 3D 2.000000000 / 4.000000000 / 5.000000000 /
  6.000000000 against 2D 1.9999999 / 3.9999999 / 4.9999999 / 5.9999999 (difference +1.0e−7, the
  1e−9 floor of the 2D bisection). The 3D instrument reduces to the 2D one.
* **two cubes** — all six declared axes return `t = 2` exactly; the gate passes the state at 2 and
  refuses 0.9999 apart with penetration exactly `1/10000`.
* **the gate is exact and unsigned** — a deliberately overlapping triple is refused with
  penetration exactly `2/5`; grid knowns 8 → 2, 9 → 3, 16 → 3, 27 → 3, 28 → 4 all gate.

## 7. What this does not say

* It does not improve `22.218056945`. No 2D row, angle or coordinate was touched.
* It does not give `L(n)` for any n >= 5. Those are constructions; the LP lower bound is only
  computed for n <= 4, and n = 9 in particular sits in `(2, 3]` with nothing said about where.
* It does not say the cube grid is never beaten in 3D. It says two descent paths from twelve rows
  did not beat it, and that for n <= 8 it cannot be beaten.
* It does not transfer to rotated solids. A rotated square is not a cube, which is why `algn` is a
  column and not an assumption.

## 8. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/declp3.py --control     # 3 controls, exact gate
python3 scripts/declp3.py               # 12 rows + exhaustive n <= 4 (71 s)
python3 scripts/declp3.py --exhaustive 4 2000   # a bounded sample of the 46,656
```

Ledger: `workspace/push/declp3.json` (per-row verdicts, both descent traces, exhaustive bounds).
