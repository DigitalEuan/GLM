# 45 — The band anchors' empty square, certified (Run 82)

Instrument `scripts/space_around.py` (extended, 8 controls); ledgers
`workspace/push/space_around.json` (now carrying certificates) and
`workspace/push/space_around_blocks.json`. Read-only: **no row changed**, no
score claimed, `submission.csv` untouched.

**What this run adds to run 81.** Run 81 *achieved* a side for the largest empty
square in each band anchor. This run turns each number into an interval with a
proof on both ends, and then attacks the lower end with a different initial
placing — which found that one anchor (k = 29) had been under-searched by 0.024.

**Headline.** For every anchor and every box, the largest empty square is
bracketed as **0.695–0.807 achieved, 0.788–0.886 certified upper**, with a
**certified gap of 0.071–0.098** per anchor. Since the largest upper side over
all 42 states is **0.8869 < 1**, no unit square fits at *any* orientation in *any*
of them — that is now a proof, not a measurement, with at least **0.113** of
side to spare. Separately, the axis-aligned maximum `M(0)` is certified to
**1e-4** at every anchor, so the run-81 value at 0° is now a theorem.

---

## 1. Two independent upper bounds

**(a) The disk bound.** A square of side s that fits contains its inscribed disk
of radius s/2 at the same centre, and that disk is in the free space. So
`s <= 2 c(p)` for every placement, with `c` the distance to the nearest packed
square or wall, and therefore

    s_max(any orientation) <= 2 max_p c(p).

`c` is 1-Lipschitz, so a cell of half-diagonal r has `max c <= c(centre) + r`;
branch and bound over a covering grid of the box certifies `max c` from above to
a chosen tolerance, pruned against the achieved side. The bound is
orientation-free: one certificate covers the whole circle.

**(b) The inscription bound.** A square of side s at angle θ contains an
axis-aligned square of side `s/(cos θ + sin θ)` (at 45° it is `s/√2`), so

    s(theta) <= (cos theta + sin theta) M(0) <= sqrt(2) M(0),

where `M(0)` is the axis-aligned maximum. `s(p, 0)` is 2-Lipschitz in p, so a
quadtree of cells with `max s <= s(centre) + sqrt(2)·cell` certifies `M(0)` from
above; at every anchor it converges in under a second to **1e-4** of the
achieved 0° value.

The reported upper side is `min(2 c_max, sqrt(2) M(0))`. In this run the disk
bound was the smaller one in all 42 states — the inscription bound runs 0.98 to
1.14 here, so it never binds, but it is the bound that would matter if a tilted
angle ever *beat* the axis one.

**Why the gap is not zero, stated plainly.** The disk bound is attained only in
a strip. At a *corner* pocket — two free directions meeting an obstacle corner —
the largest empty disk is bigger than the largest empty square, and 2c overstates
s by up to 69%. Control 6 pins this exactly: on a 0.4 strip the disk bound is
0.4686 against a true 0.4. Every anchor's free space is corner-like, which is why
the gap is 0.07–0.10 rather than 1e-3. The gap is bound looseness, not search
error: the search error at 0° is certified at 1e-4, and dense re-checks in run 81
agreed to 2e-5.

## 2. The certified table (own box)

| k | n | achieved s_max | M(0) certified | s_ub | certified gap | 1−s_max | 1−s_ub | s(45°) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 18 | 344 | 0.70222 | 0.70231 | 0.78802 | 0.0858 | 0.2978 | 0.2120 | 0.56929 |
| 19 | 382 | 0.69481 | 0.69490 | 0.79293 | 0.0981 | 0.3052 | 0.2071 | 0.57978 |
| 20 | 423 | 0.73208 | 0.73218 | 0.82497 | 0.0929 | 0.2679 | 0.1750 | 0.59773 |
| 21 | 465 | 0.75062 | 0.75071 | 0.84148 | 0.0909 | 0.2494 | 0.1585 | 0.60638 |
| 22 | 509 | 0.75889 | 0.75897 | 0.84698 | 0.0881 | 0.2411 | 0.1530 | 0.61018 |
| 23 | 556 | 0.75290 | 0.75300 | 0.84217 | 0.0893 | 0.2471 | 0.1578 | 0.60743 |
| 24 | 604 | 0.76064 | 0.76116 | 0.84922 | 0.0886 | 0.2394 | 0.1508 | 0.61097 |
| 25 | 655 | 0.76133 | 0.76205 | 0.85061 | 0.0893 | 0.2387 | 0.1494 | 0.61145 |
| 26 | 707 | 0.80721 | 0.80729 | 0.88557 | 0.0784 | 0.1928 | 0.1144 | 0.63167 |
| 27 | 761 | 0.76037 | 0.76047 | 0.84906 | 0.0887 | 0.2396 | 0.1509 | 0.61085 |
| 28 | 818 | 0.76066 | 0.76075 | 0.84843 | 0.0878 | 0.2393 | 0.1516 | 0.61098 |
| 29 | 876 | **0.73611** | 0.73619 | 0.80755 | 0.0714 | 0.2639 | 0.1925 | 0.58824 |
| 30 | 936 | 0.75080 | 0.75088 | 0.84063 | 0.0898 | 0.2492 | 0.1594 | 0.60649 |
| 31 | 998 | 0.76550 | 0.76559 | 0.85281 | 0.0873 | 0.2345 | 0.1472 | 0.61319 |

The other two boxes agree: run 78's box gives achieved 0.7022–0.8093 with gaps
0.078–0.099; the centred placement gives 0.6995–0.8082 with gaps 0.078–0.099.
Across all 42 states the largest upper side is **0.8869**, the smallest margin
below 1 is **0.1144**, and **no certificate hit its split cap**.

Note what is and is not proven about the *value*: `M(0)` (the axis-aligned
maximum) is proven at every anchor to 1e-4, and the achieved global number
equals it at all 14. But the certificate does not prove that no orientation
beats 0°; it proves that none exceeds the `s_ub` column. Proving
`s_max = M(0)` needs a monotonicity argument in θ that neither bound supplies.

## 3. Alternative initial placing: sub-blocks

`--blocks b` cuts the box into `b × b` smaller squares and runs the same
coarse-grid-plus-climb search inside each one, independently, at θ = 0. With a
fixed total point budget this gives each region a *finer* seed grid — the effect
is exactly resolution, and it shows up clearly (`side`, and the block that won):

| k | b = 1 | b = 2 | b = 4 | run 81 |
| ---: | ---: | ---: | ---: | ---: |
| 18 | 0.70221 | 0.70222 (0,0) | 0.70222 (0,1) | 0.70222 |
| 19 | 0.69481 | 0.69481 (0,1) | 0.69481 (0,3) | 0.69481 |
| 20 | 0.73208 | 0.73208 (0,0) | 0.73208 (0,1) | 0.73208 |
| 21 | 0.75062 | 0.75062 (0,1) | 0.75062 (0,3) | 0.75062 |
| 22 | 0.75889 | 0.75889 (0,1) | 0.75889 (0,3) | 0.75889 |
| 23 | 0.75290 | 0.75290 (0,0) | 0.75268 (0,0) | 0.75290 |
| 24 | 0.70535 | 0.76064 (0,1) | 0.76064 (0,3) | 0.76064 |
| 25 | 0.75046 | 0.76132 (0,1) | 0.76133 (0,3) | 0.76133 |
| 26 | 0.80721 | 0.80721 (0,1) | 0.80721 (0,3) | 0.80721 |
| 27 | 0.62845 | 0.76037 (0,1) | 0.76037 (0,3) | 0.76037 |
| 28 | 0.76066 | 0.76066 (0,1) | 0.76066 (0,3) | 0.76066 |
| 29 | 0.73611 | 0.73611 (0,1) | 0.73611 (0,2) | 0.71218 → **0.73611** |
| 30 | 0.75080 | 0.75080 (0,0) | 0.75080 (0,0) | 0.75080 |
| 31 | 0.62066 | 0.76550 (0,1) | 0.76550 (0,3) | 0.76550 |

Three effects, each worth naming:

* **A single coarse grid is not enough.** b = 1 (0.6 spacing here) loses 0.13 at
  k = 27 and k = 31 and 0.055 at k = 24. Those pockets are ~0.7 wide and sharply
  peaked, so a grid point beside the peak reports half its value — the same
  failure mode run 81 had to fix with its subgrid stage.
* **Decomposition recovers it.** b = 2 and b = 4, with the same total budget,
  match run 81 at every anchor except one, and the winning block is always in
  the upper half of the container (rows 1 or 3 of the partition) — the pocket
  sits on the boundary layer, not in the middle.
* **It corrected an anchor.** At k = 29 the decomposed search finds
  **0.736113**, verified exactly, against run 81's 0.712176. `M(0)` for that
  anchor is 0.736186, so run 81 was 0.024 short of the axis maximum there. The
  ledger entry is revised and the certificate recomputed (gap 0.0714): the
  certified statement is unchanged, the achieved side improves, and the deficit
  to fitting one more square at k = 29 falls from 0.288 to 0.264.

A small counter-effect, for honesty: at k = 23, b = 4 gives 0.75268 against
0.75290 — a 2e-4 loss, because each block climbs independently and a pocket that
straddles a block boundary is split. The block search is a resolution lever, not
a free improvement.

## 4. Controls (8)

1. Hand geometry: two unit squares in a 2-box give `s_max = 1` exactly.
2. A rigid 10×10 grid gives 0 and the gate refuses a duplicate.
3. A holed 8×8 grid gives exactly 1 and gates at `L = 8 + 1e-6`.
4. Anisotropy is detected: 0.4 at 0°, `0.4/√2` at 45°.
5. The closed form agrees with an independent vertex-projection SAT on 729
   placements of a mixed-angle state.
6. The disk bound is valid **and loose exactly at a corner**: on the 0.4 strip it
   certifies 0.4686 against a true 0.4 — the 0.069 is the same mechanism as the
   per-anchor gaps.
7. The disk certificate is two-sided: 1.000129 on the holed grid (achieved 1),
   and 0.057 on the full grid, where a zero clearance needs every cell and the
   split cap is what stops it (flagged `capped`).
8. The position bound is exact at one orientation: `1.000005` on the holed grid,
   `5.2e-3` on the full one.

## 5. What is proven, and what is not

Proven, for all 14 anchors and all three boxes:

* **No unit square fits in the free space at any orientation.** The largest
  certified upper side is 0.8869, so every orientation is short of 1 by at least
  0.113 — for an *arbitrary* angle, not just the 17 sampled.
* **The axis-aligned maximum `M(0)` is exact to 1e-4** at every anchor
  (0.69481–0.80721), and it equals the achieved global maximum in all 14.
* The achieved sides are attained by placements checked by the closed form and
  by vertex SAT; no certificate hit its cap.

Not proven, named:

* **That the maximum is at 0°.** The certificate brackets the global maximum in
  `[achieved, s_ub]` but does not exclude a tilted orientation reaching up to
  `s_ub`. The disk bound has no orientation in it, so it cannot see the tilt
  penalty the measurements show.
* **A tight value.** The gap is 0.07–0.10 and it is the corner looseness of the
  disk bound. A tighter certificate needs an orientation-aware bound (a
  contact-structure enumeration or an interval version of `s(p, θ)`); that is the
  next instrument, not this one.
* **Constructions that move the squares.** Everything here freezes the record.
  The achieved deficits say what a rearranged layer must buy (0.19–0.31 of side),
  which remains a target, not a route.

## 6. Re-running

```bash
cd source_material/ToDo/squares_in_squares
python3 scripts/space_around.py --selftest          # 8 controls (~7 s)
python3 scripts/space_around.py                     # 14 anchors x 3 boxes, certified (~6 min)
python3 scripts/space_around.py --blocks            # the b = 1, 2, 4 comparison (~4 min)
```
