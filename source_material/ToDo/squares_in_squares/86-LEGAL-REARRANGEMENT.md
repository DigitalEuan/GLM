# 86 — A legal rearrangement move: slide, block swap, and what the 447 rows do with it (run 127)

Every route since run 123 has had the same shape: compress the pose until it overlaps, then try to repair the
overlap. The squeeze is real (doc 85: 19/20 rows reach `L0 − 4e-3`) and legalising it costs 4.6e-2 to 3.0, so
the repair always refuses. This run builds the other kind of move — one that is **legal at every accepted
step** — and asks whether it can shrink a delivered row. It cannot, and the reason is measurable.

## 1. The test: exact separating-axis slack, at the destination

`scripts/legal_slide.py` (float-free; `Decimal` at `true_geom.DPS = 40`, directions from `TG.axes`):

* `slack(a, b)` — the separating-axis test on the four edge normals of both cells:
  `max over axes of (extent_a + extent_b − |projection difference|)`. `≥ 0` is legal, `< 0` is penetration.
  Every term is a finite `Decimal` and every comparison is exact.
* `check_move(state, dirs, idx, moved, dx, dy)` — translate `moved` by `(dx, dy)` and return
  `(worst_slack, witness)`. It tests **only moved-vs-unmoved pairs, and at the moved cell's new position**
  (`near_at` looks the pairs up from a sorted-x index at the destination, within `REACH = 2`).
* Completeness, stated rather than assumed: a common translation preserves the relative offset of every pair
  inside the moved group **exactly** (Decimal addition of finite decimals is exact), so moved-moved slacks
  cannot change; unmoved-unmoved cannot change either. The destination test is therefore the whole test, not a
  sample of it. `None` means no unmoved pair is within `REACH` of the destination — legal vacuously.

## 2. The move set

1. **Band slide.** `slab(i, along=0)` is the row (cells with the same `v`), `slab(i, along=1)` the column;
   the band is translated along the wall it is parallel to. In a grid this move is always legal (the wall is
   periodic), which is exactly why it is useless as a negative control (§3).
2. **Single-cell slide** in one direction, same acceptance test.
3. **Block swap into a void.** `void_seats` scans a unit lattice over the pose's bounding box for centres where
   a unit cell *of the moving cell's own angle* fits (exact slack against every other cell), and the cell is
   moved there. Seats are computed per candidate cell, because the fit depends on its angle.

Acceptance is `legal` **and** strictly smaller side for slides; for a swap, `legal` and not-larger side (a swap
may legitimately be side-neutral). Nothing is ever squeezed and repaired.

## 3. Controls (`python3 scripts/legal_slide.py --selftest`)

| control | what it shows | result |
|---|---|---|
| **P** positive, tighten | a 4×4 grid with one row displaced by 0.25 in `u` can be tightened by a legal move | side **4.25 → 4.00**, 1 move accepted; every pair of the *resulting* pose re-checked `≥ 0`, so the accepted move is certified, not assumed |
| **N** negative, 3 refusals | illegal overlaps are refused with exact slack | cell onto its neighbour by 1 → **−1** at pair (5, 6); half way → **−1/2** at (5, 6); into the row in front → **−1** at (5, 1) |
| **N3** negative, regression | a **long** slide onto a *distant* occupied cell is refused | cell moved 4 units onto cell 6 → **−1** at (8, 6) (the first version accepted this; §5) |
| **N2** non-vacuity | the accepting branch is not dead | a free cell slides 1/2 into empty space and is accepted (no pair in reach) |
| **V** positive, block swap | a swap into a void both fires and tightens | 3×3 with the centre removed: **7 seats**, the outside cell swaps in at slack **0**, side **5.00 → 3.00** |

The three N refusals are *single-cell* on purpose: in a grid a band slide along its own wall is legal by
construction, so a band is not a valid negative control (an earlier version of this test tried exactly that and
was wrong — the "illegal" band move was legal).

## 4. The sample: 6 unbeaten rows, 20 s each

`python3 scripts/legal_slide.py --rows 33,159,439,662,883,942 --seconds 20`
(record `workspace/push/legal_slide127.json`, log `.log`)

| n | L0 (delivered) | slides accepted | void swaps | dL | wall clearance | seats | whole-pose verdict |
|---|---|---|---|---|---|---|---|
| 33 | 6.0000000016660000 | 0 | 1 | 0 | 3.33e-10 | 1 | `TG.check`: same side, **0 violations** |
| 159 | 13.0000000018460000 | 0 | 1 | 0 | 1.54e-10 | 1 | `TG.check`: same side, **0 violations** |
| 439 | 21.0000000019040000 | 0 | 1 | 0 | 9.50e-11 | 1 | not verified (pair pass ≈ 20 s > budget) |
| 662 | 26.0000000019240000 | 0 | 1 | 0 | 7.70e-11 | 1 | not verified |
| 883 | 30.0000000019340000 | 0 | 1 | 0 | 6.70e-11 | 1 | not verified |
| 942 | 31.0000000019360000 | 0 | 1 | 0 | 6.50e-11 | 1 | not verified |

**dL = 0 on 6/6, 0 rows beat their delivered side.** "Wall clearance" is the largest legal inward slide of any
wall cell, by 48-step bisection with tolerance 1e-15 capped at `REACH = 2` — a **measurement**.

**Why zero slides.** The delivered poses are jammed: every wall cell has at most 3.3e-10 of legal room before it
touches its neighbour, and the move ladder's smallest step is 1/512 ≈ 2e-3, seven orders of magnitude larger. No
slide can fire. This is not a budget artefact: rows 33 and 159 finished the whole analysis in 1.7 s and 6.4 s and
still accepted 0 moves, and the clearance measurement itself finished on all six rows.

**Why one swap each.** Every pose does contain at least one seat where a unit cell fits exactly (`void_seats`),
and one wall cell can move there legally — so the move set *is* live on real rows. The side does not shrink
because the vacated cell is one of a full column on that wall, which redefines the wall rather than moving it.
On the two rows the independent 40-digit pass could afford, the swapped pose is the delivered side with 0
violations: a real, certified, **side-neutral** rearrangement.

## 5. The bug the sample found

The first version of `check_move` tested the mover's **old** neighbour list (an x-sweep with `REACH = 2`). That
is sound for a small step and quietly wrong for a long one: a cell slid 9.5 units passes *over* its old
neighbours and lands on a cell that was never in its list, and the move is accepted. The symptom was the first
sample run, which reported wall clearances of **3.3, 9.5, 7.7, 6.7, 6.5 units** on poses that are jammed at
1e-10 — physically impossible, and identical across all four walls because the scan returns the first step it is
offered.

The fix is to look the pairs up at the destination (`near_at`), and **N3** is the regression test: a 4-unit slide
onto a distant occupied cell, accepted before, refused now at exact slack −1.

This is the failure mode this whole line of work exists to avoid — "compress into overlap and hope legalisation
recovers it" — except the *checker* was the one hoping. A legality test that is only locally sound is the most
dangerous bug in this code: it makes every downstream number (dL, certificates, "no overlaps") look better, never
worse.

## 6. What it says about the 447 rows

Three instruments now agree, from opposite directions:

* runs 123/117: polish finds **1.2e-10** internal clearance and closes nothing (ceiling 0.00000);
* runs 124–126: the squeeze is real, and legalising it costs **4.6e-2 to 3.0** per row;
* run 127: a **legal** move never shrinks the side, because a delivered pose has ~1e-10 of legal room, and the
  move set that works (the swap) is side-neutral.

The reading is that these poses sit *on* the feasibility boundary with the side set by a full wall. A move that
removes one cell from that wall cannot lower it, and a move that pushes the wall inward is exactly the illegal
one. So the blocker is structural, and it is now stated as a measurement rather than an inference.

**Named next step (not done here).** Apply this move set to the **relaxed** poses the projection stage produces
(doc 85: residual penetration 1.1e-4 at n = 33 to 1.6e-2 at n = 942), where the clearance is not zero. That is
the only place in the current pipeline where a legal slide has room to fire and could decide whether a squeeze is
convertible. On the delivered poses there is nothing to convert.

**Done in doc 87 (run 128).** The moves do fire there — clearance `2.8e-3 … 6.1e-2` after legalising, **7 accepted
moves per row** — and **no squeeze becomes convertible on 6/6 rows**: the minimum uniform legalisation pays
`p · L` (`1.80e-2 … 1.59` against the `3.9e-3` banked, **4.6× to 401×** the gain), and the legal moves recover under 0.1 % of that payback. Doc 87 also corrects this document's `1.1e-4 … 1.6e-2` figures: they are
`post_project_pen`, a sum of squared penetrations, and the depth itself is `3.59e-3 … 5.21e-2`.

## 7. Files and checks

* `scripts/legal_slide.py` — new, 21 functions, **inside** the float audit (`glm_wheels.py --audit`):
  **678 functions checked, 0 offenders** (657 + 21; the budget is parsed as an `int` so the module names no
  float even in `main`).
* `workspace/push/legal_slide127.json` / `.log` — the sample, per row: `cells`, `L0`, `dL`, `moves_accepted`,
  `swaps`, `void_seats`, per-wall `max_inward_step`, `certified*`.
* Guards green: `structure.py --control`, `--check-solver`, `perturb` / `anchor_chain` / `void_insert` /
  `true_geom` selftests, `sqscore` **22.218056945** (553 beats, 447 grid), `record_guard`, audit 678/0,
  `py_compile`. `submission.csv` and root `WHITEBOARD.md` untouched.
