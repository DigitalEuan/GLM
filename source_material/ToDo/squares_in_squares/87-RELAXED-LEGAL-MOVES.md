# 87 — The legal move set on the relaxed poses: no squeeze becomes convertible, and the cost is `p · L` (run 128)

Run 127 closed the legal move set on **delivered** poses: every wall cell there has `3.3e-10` of legal room, the
move ladder's smallest rung is `1/512`, so no slide can fire, and the only move that does (a swap into a void)
is side-neutral. It named one place left to look: the poses the **projection stage** produces, where the pose is
inside the delivered side and the clearance is not zero.

This run looks there. The answer has three parts, all measured:

1. **The moves fire.** After the relaxed pose is made legal, its walls have `2.8e-3 … 6.1e-2` of legal room —
   five to seven orders of magnitude more than a delivered pose — and **7 legal moves** are accepted on every
   row (4 on the run-127 ladder, 3 at a side-minimising bisected step).
2. **No squeeze becomes convertible.** Making the relaxed pose legal costs more than the squeeze banked, on
   **6/6** rows: payback `1.80e-2 … 1.59` against a gain of `3.9e-3`, i.e. **4.6× to 401×** the gain.
3. **The cost is a law, not an accident**: `payback = p · L`, the residual penetration depth times the side,
   which reproduces the measured payback to **1 % for n ≥ 439**. Convertibility therefore needs
   `p < gain / L` — `6.5e-4` at n = 33 down to `1.3e-4` at n = 942 — and the projection stage leaves `p` **5×
   to 407× too large**.

Nothing here changes a row. `submission.csv`, the table and the score (`22.218056945`, 553 beats, 447 grid) are
untouched.

## 1. The pipeline, and where the arithmetic changes hands

```
structure.attempt(n, kind=0)            # run 126's squeeze + projection, unchanged
  relax(want = L0 - 4e-3)               #   wall_w = 1e5   (float, discovery)
  project(want)                         #   wall_w = 1e2   (float, discovery)
  pose -> repr(float) strings           # the exact float64 the relaxer produced
legal_relaxed.as_decimal                # Decimal, no float named
  check_pose                            # exact: is this pose legal at 40 digits?
  legal_scale                           # minimum uniform scale f* that is legal
  swap_into_void / tighten / tighten_exact   # legal moves only, slack >= 0 at the destination
```

`scripts/legal_relaxed.py` is the driver (a discovery harness: it calls `structure.py`). Everything after the
hand-over is `legal_slide.py`'s `Decimal` at `true_geom.DPS = 40`, and every number in §4 is taken there — the
squeeze side, the penetration, `f*`, the legal side, the dL. The hand-over is exact rather than approximate:
`repr(float)` is the shortest decimal that round-trips to that float64, so no second rounding is introduced.

Budget: 20 s per row for the squeeze and projection (run 126's `--split 0.6`, `--iters 10`, `--proj-iters 40`
with a 20 s budget), plus the exact analysis afterwards. Squeeze/projection is stochastic (the patch order is
shuffled), so the penetration depth differs run to run at the same budget; the exact stage is deterministic
given the pose.

## 2. What had to be added, and the two bugs the controls caught

| addition | why the run needs it | control |
|---|---|---|
| `check_pose(state, dirs)` | an exact verdict on a *whole* pose, not one move: `(worst slack, violation count, witness)`. The `REACH` sweep is **complete** — two unit squares more than 2 apart in either coordinate cannot overlap at any angles — so it is the O(n²) pass with fewer pairs, not a weaker one | **S** |
| `legal_scale(state, dirs)` | the cheapest legalisation the pipeline's own family admits: the **minimum** uniform scale about the box centre, bisected. A pair's slack is `f·|d·q| − (h_a+h_b)`, non-decreasing in `f`, so the legal `f` form an upper interval and the bisection is exact to `1e-15` | **F** |
| `min_side_step(...)` | the **largest legal step is not the useful step**: a 1e-3 gap with a row free to slide 2 units has 2 units of legal room and 1e-3 of useful step. The side is convex in the step (`max` of `max`/`min` of linear functions), so a ternary search over the legal range minimises it | **E** |
| `tighten_exact(...)` | the ladder's granularity, and the wall as a **set**: each wall is tried as the band through its first cell, that cell alone, and the whole wall set (a lattice-like wall is defined by several cells in different bands; moving one band redefines nothing) | **E**, **P** |
| `void_seats(..., idx=)` | it scanned a unit lattice × n cells (964k Decimal subtractions on a 942-cell row); the sorted-x index gives the same seat set | **V** |

**Bug 1 — clearances of exactly zero were the lookup, not the geometry.** The first smoke test reported
`clearance = 0` on all four walls and **0 moves**. The cause was `wall_cells`, which required the wall cells'
edges to be *bit-identical* to the extreme. That is true of a delivered pose and false of a scaled one: after
`scale_pose` the equality breaks in the last digits of the 40 used, the wall set comes back **empty**, every
per-wall loop skips, and the driver prints zeros for its own missing input. The exact consequence-orientation of
this project makes that failure look like a *finding* — "no room to fire" — which is exactly why it is recorded
here. Fixed with `WALL_TOL = 1e-18` (twenty orders above the 40-digit rounding, far below any length that
decides anything); the measured room is `1.7e-4 … 6.1e-2`, and the moves fire.

**Bug 2 — my own claim that the ladder cannot take a small gap was wrong.** Control E was first written to
assert that a 1e-3 gap is below the ladder's smallest rung (1/512 = 1.95e-3) and therefore refused. It is not:
the ladder overshoots, and the side gate accepts the overshoot because sliding a displaced row *past* its
neighbours reduces the bounding box by more than the overshoot in the other direction. The ladder took the move
(side `4.001 → 4.00095`) and the exact step did better (`→ 4.0000007`). What decides a slide is the **side
gate**, not the step size — run 127's zeros were about `1e-10` of clearance, where *no* positive step is legal
at any size.

## 3. Controls (`python3 scripts/legal_slide.py --selftest`)

The five run-127 controls are unchanged and still green; three are new.

| control | what it shows | result |
|---|---|---|
| **P** positive, tighten | a 4×4 grid with one row displaced by 0.25 tightens by a legal move | side **4.25 → 4.00**, 1 move, resulting pose re-checked pair by pair |
| **N** negative, 3 refusals | overlaps are refused with exact slack | **−1** at pair (5,6); **−1/2** at (5,6); **−1** at (5,1) |
| **N3** negative, regression | a long slide onto a **distant** occupied cell is refused | 4 units onto cell 6 → **−1** at (8,6) |
| **N2** non-vacuity | the accepting branch is alive | a free cell slides 1/2 into empty space and is accepted |
| **V** positive, block swap | a swap into a void fires and tightens | 3×3 with its centre removed: **7 seats**, swap at slack **0**, side **5.00 → 3.00** |
| **E** step search (new) | the largest legal step is not the useful one | largest legal step **2** gives side **5.999**; the side-minimising step **0.000999997** gives **4.000000003**; ladder **4.00095**, exact **4.0000007** |
| **F** minimal legal scale (new) | `legal_scale` returns the analytic minimum and the payback law | 4×4 at spacing `1−1e-3` both ways, 42 violations: `f* = 1.00100100100100153355…` against the analytic `1/(1−1e-3)`, legal at side **4.0000000000000016** with 0 violations, payback **exactly 3d** = `(f*−1) ×` the 3-unit spread (not `(f*−1) ×` the side) |
| **S** sweep vs pair pass (new) | the `REACH` scan is a substitute for the O(n²) pass, not an approximation | delivered n=33: **0 vs 0**; the same pose compressed by 0.999: **99 vs 99** violations, worst slack **−9.999997e-4 vs −9.999997e-4** |

## 4. The six rows

`python3 scripts/legal_relaxed.py --rows 33,159,439,662,883,942 --seconds 20`
(record `workspace/push/legal_relaxed128.json`, logs `.log` in the same directory)

| n | L0 (delivered) | squeeze gain | residual depth `p` | `f*` | payback | payback/gain | clearance after legalising | slides (ladder+exact) | swaps | dL | convertible |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 33 | 6.0000000017 | −3.9266e−3 | **3.5893e−3** | 1.003598 | +1.7976e−2 | **4.6×** | 2.829e−3 | 0+3 | 0 | −1.4037e−2 | no |
| 159 | 13.0000000018 | −3.9493e−3 | **5.2797e−3** | 1.005307 | +6.3662e−2 | **16.1×** | 5.714e−3 | 4+3 | 0 | −5.9682e−2 | no |
| 439 | 21.0000000019 | −3.9339e−3 | **1.3787e−2** | 1.013979 | +2.7951e−1 | **71.1×** | 1.448e−2 | 4+3 | 0 | −2.7542e−1 | no |
| 662 | 26.0000000019 | −3.9703e−3 | **1.6307e−2** | 1.016567 | +4.1410e−1 | **104.3×** | 1.591e−2 | 4+3 | 0 | −4.1005e−1 | no |
| 883 | 30.0000000019 | −3.9728e−3 | **3.7130e−2** | 1.038398 | +1.1133e+0 | **280.2×** | 3.835e−2 | 4+3 | 0 | −1.1093e+0 | no |
| 942 | 31.0000000019 | −3.9721e−3 | **5.2148e−2** | 1.053112 | +1.5931e+0 | **401.1×** | 6.075e−2 | 4+3 | 0 | −1.5888e+0 | no |

Column by column: the squeeze is the run-126 result reproduced (`−3.93e-3` on 6/6, target `4e-3`); `p` is the
**deepest violating pair**, measured by the exact scan; `f*` is the minimum uniform scale that makes the pose
legal; payback is `legal side − squeeze side`, measured, not derived; clearance is the largest legal inward slide
of a wall cell on the loosest wall; dL is `L0 − final side` after the legal moves, both sides exact.
`swap_into_void` found **no seat** on any row (see §6). The whole-pose 40-digit pass certifies the final poses on
n = 33 and 159 (`TG.check`: the side above, **0 violations**); the larger rows are certified by `check_pose`,
which is the same test over the `REACH`-bounded pair list that control S pins to `TG.check`.

## 5. The cost law: `payback = p · L`

| n | `p · L0` | measured payback | ratio | `p` allowed (`gain/L0`) | how far over |
|---|---|---|---|---|---|
| 33 | 2.154e−2 | 1.7976e−2 | 0.83 | 6.544e−4 | **5.5×** |
| 159 | 6.864e−2 | 6.3662e−2 | 0.93 | 3.038e−4 | **17×** |
| 439 | 2.895e−1 | 2.7951e−1 | 0.97 | 1.873e−4 | **74×** |
| 662 | 4.240e−1 | 4.1410e−1 | 0.98 | 1.527e−4 | **107×** |
| 883 | 1.114e+0 | 1.1133e+0 | 1.00 | 1.324e−4 | **280×** |
| 942 | 1.617e+0 | 1.5931e+0 | 0.99 | 1.281e−4 | **407×** |

Why the law has that form: a pair at centre distance `d` with penetration `p` is separated when the scale
satisfies `f·|d·q| ≥ h_a + h_b`, so `f* − 1 ≈ p / |d·q| ≈ p` for a contact at distance ~1; and the side grows by
`(f* − 1)` times the **spread** of the binding axis, which is within a few percent of `L`. So the payback is
`p · L` and it is *not* `(f* − 1) · L` alone — half-extents do not scale, which is what control F pins: the
payback there is exactly `3d`, the spread, not `d` times the side.

The consequence is the one this run exists to state. The squeeze banked `gain = 3.9e-3`. A legalisation paying
`p · L` leaves a net gain only when `p < gain / L`: **6.5e-4** at n = 33 falling to **1.3e-4** at n = 942. The
projection stage leaves `p = 3.6e-3 … 5.2e-2` — over the bar by 5.5× on the smallest row and 407× on the
largest, and the factor grows with `n` because `L` grows while the achievable `p` does not shrink as fast.

## 6. What the legal moves did, on the one pose with room

After legalisation the clearance is `1.7e-4 … 6.1e-2` — the run-127 measurement was `3.3e-10 … 6.5e-11` on
delivered poses, so the promise was met: this **is** a pose a slide can work on. And the moves do fire:

* **7 accepted moves per row** (4 on the ladder, 3 at the bisected side-minimising step; n = 33 takes 0 on the
  ladder and 3 at the exact step, because its ladder rung overshoots into a neighbour).
* They recover **1.3e-5 … 2.6e-4** of side — **0.005 % to 0.07 %** of the payback. dL stays negative on 6/6.
* No void swap fires: `void_seats` (exact, per candidate cell's angle, at unit lattice step) finds **no free
  seat** in a pose that is `4e-3` inside the delivered side — every unit cell of the bounding box is taken.
  That is a stronger version of run 127's result, where a seat existed but the swap was side-neutral.

**Why the moves cannot refund the payback.** At the minimum legal scale the pose sits **on** the boundary: the
deepest pair has slack `0` and the wall it belongs to is in contact. The only slack available to a legal move is
the slack legalisation itself created, and the wall-set move has to spend it against the same contacts that set
`f*`. So the legal move set can at best refund a fraction of the payback, never more, and it measurably refunds
under 0.1 % of it. The composite pipeline `squeeze → project → legalise → move` therefore lands at
`L0 + payback − refund`, which is `1.40e-2 … 1.59` **behind** the delivered side on every row tested.

## 7. One figure corrected

Docs 85 and 86 quote the projection stage's residual as `1.1e-4` (n = 33) to `1.6e-2` (n = 942) and call it a
penetration. The field is `post_project_pen`, which `structure.attempt` sets from `total_pen(...)[0]` — the
**sum of squared penetrations** over the pairs the penalty sees, i.e. an area, not a depth. Measured exactly here,
the depth of the deepest violating pair on these poses is **3.59e-3 … 5.21e-2**: the clearance promise was real
(it is what lets the moves fire at all) but the pose is **more** penetrated than the quoted number implies, and
the legalisation cost is correspondingly larger. The old `4.6e-2 … 3.0` payback figures stand as the **ladder's**
cost (`f = 1 %` up to n = 393, `10 %` beyond); the minimum scale replaces them with `1.80e-2 … 1.59`, a 2.5× to
2.6× reduction that still loses on every row.

## 8. What this says about global restructuring plus local tightening

The request's reading — a global/combinatorial restructuring with local continuous tightening — is the right
shape, and this run prices the two halves separately:

* **The local continuous half must not be the one that pays for legality.** Every local route measured so far
  (polish, face squeeze, penalty walk, minimum uniform scale) buys legality at `p · L`, and `p` after a penalty
  walk is `1e-3 … 5e-2` because the walk is *encouraged* to overlap. That is why every local route loses by
  4.6× to 401×: the payback is the penetration, and the penetration is the mechanism.
* **The target the combinatorial half has to hit is now a number.** A tiling whose projection leaves
  `p ≤ gain / L` — `1.3e-4` at n ≈ 1000, `6.5e-4` at n = 33 — is convertible, and nothing else is. The current
  relaxation converges to `p` two to three orders above that, so an arrangement change must do the work *before*
  the continuous stage runs, and the continuous stage then needs only to be **legal at every step** (the move set
  here) rather than to squeeze and be repaired.
* **The negative half of that is worth stating too**: on a delivered pose the legal move set has `1e-10` of room
  (run 127), and on a legally relaxed pose the room is exactly the payback it just paid. Both ends are measured,
  so a future run can test a candidate arrangement by measuring `p` at the target side and stopping immediately
  if it is above the bar — no long budget is needed to know it will lose.

## 9. Files, records, checks

* `scripts/legal_slide.py` — extended: `extents`, `check_pose`, `scale_pose`, `legal_scale`, `min_side_step`,
  `tighten_exact`, a `moved`-group `max_legal_step`, an indexed `void_seats`, and `wall_cells`' `WALL_TOL`;
  **inside** the float audit, now **27 decision functions** (21 + 6).
* `scripts/legal_relaxed.py` — new driver (discovery, outside the audit by the same rule as `structure.py`):
  `as_decimal`, `clearance`, `swap_into_void`, `analyse`, `main`.
* `scripts/structure.py` — `attempt(..., pose_out=...)` appends the relaxed pose (as `repr(float)` strings) so
  the exact stage can consume it; the record is unchanged.
* `workspace/push/legal_relaxed128.json` / `legal_relaxed128a.log`, `legal_relaxed128b.log` — the six rows:
  per row `L0`, `squeeze_side`, `residual_penetration`, `violations_at_projection`, `f_star`, `legal_side`,
  `payback`, `payback_over_gain`, `clearance_legal`, `moves_ladder`, `moves_exact`, `swaps`, `side_final`, `dL`,
  `recovered_by_moves`, `certified`.
* Guards green: `legal_slide --selftest` (**8 controls**: P, N, N3, N2, V, E, F, S), `structure --control`
  (A 100.0 %, B absorbed at 4.0030358954), `structure --check-solver` (86.0× / 57.9×, |df| 3.78e-22),
  `perturb`, `anchor_chain`, `void_insert`, `true_geom` selftests, `sqscore` **22.218056945** (553 beats,
  447 grid), `record_guard` OK, `glm_wheels --audit` **684 functions, 0 offenders**, `py_compile` OK.
  `submission.csv` and `WHITEBOARD.md` untouched; no row, no table entry and no score changed.
