# 93 — The two notches, measured and priced: closed by rigidity (Run 136)

**Run 136, 2026-11-25.** Instrument `scripts/notch136.py` (`--diagnose`, `--room`, `--strips`,
`--insert`, `--selftest`); ledger `workspace/push/notch136.json`.
**No row changed, no score claimed, `submission.csv` and root `WHITEBOARD.md` untouched.**

Doc 75 left two structural openings and this was the run that went at both: `k = 23` (frontier
`n = 509`, hole `0.7534`) and `k = 32` (frontier `n = 998`, hole `0.7171`, `0.8394` on the finer
scan). Both are real square holes, not squashed cells. The answer, in one paragraph: **both holes
are real, both are 0.24–0.27 short of a cell, and neither can be opened — every cell in either
neighbourhood, and every facing slab of cells, is locked to at most `1.3e-5` of motion, against the
`0.24` needed.** A beat here would have to *replace* cells (a re-tiling), not move them; and the
whole prize for doing it is **`8.9e-4` of score**.

---

## 0. A frame correction, found by measuring first

`workspace/submission/table.json` stores each pose at its **construction** orientation; the scored
`submission.csv` stores it rotated to the orientation with the smallest axis-aligned box, which is
the container `sqscore.extent` measures. For the two frontier rows the difference is not small:

| n | `table.json` state, extent | delivered CSV pose, extent | `sqscore` / table `L` | Δ |
| --- | --- | --- | --- | --- |
| 509 | `22.9935885033` | `22.9897770950` | `22.9897770950` | `3.81e-3` |
| 998 | `31.9968759222` | `31.9862386204` | `31.9862386204` | `1.06e-2` |

Consequences, both load-bearing:

1. **Every geometric statement about a notch has to be made in the delivered frame.** The old
   instruments (`void_insert.load_pose`, `legal_slide.load_pose`, `structure.load_pose`) read
   `table.json`, so their holes were measured on a pose the scorer never sees. Doc 75's `0.7534`
   and run 117's `0.7171 / 0.8394` are construction-frame numbers; §1 gives the delivered-frame
   ones. (Calibration: this run's scan on the *table* pose reproduces `0.7151`, doc 75's coarse
   `0.7171` — so the instrument is the same and the frame is the only difference.)
2. **Run 117's "reached `31.996876`" was not a near-miss at the frontier.** The frontier's delivered
   side is `31.986239`, so the repaired pose was `1.06e-2` *worse* than the row it was trying to
   beat — it would still have beaten the grid (row 999 sits at `32.0000000019`), but for `9.9e-5`
   instead of `4.35e-4`. Three quarters of the prize was lost to the frame, not to the geometry.

## 1. The holes, in the delivered frame

`hmax_scan(100x17) + refine(6)`; `hfield` returns the *half*-size, so the side is `2h`.

| k | n | L | hole side | centre | θ | short of a cell | doc 75 / 117 (construction frame) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 23 | 509 | `22.9897770950` | **`0.7328`** | `(-6.9514, -4.0482)` | `0.2543` | **`0.2672`** | `0.7534` |
| 32 | 998 | `31.9862386204` | **`0.7612`** | `(27.5951, 0.3916)` | `0.0292` | **`0.2388`** | `0.7171` / `0.8394` |

The two holes are not the same kind of object:

* **k = 23 is an interior void.** Its centre is 0.45 inside the bottom wall and it is bounded above
  and below by axis-aligned cells at `y = -4.9949` and `-3.9949` — a genuine hole in the lattice.
* **k = 32 is a wall notch.** Its bottom edge is at `y = 0.0098`, i.e. 0.01 above the box floor,
  which is set by cells 594 at `(18.5129, 0.5)` and 881 at `(28.4862, 0.5)` (both exactly on
  `y = 0.0`). The notch is a corner: floor below, cells at `x = 26.52` left and `x = 28.49` right,
  tilted cells (`0.2974`, `0.2627`) above at `y ≈ 0.73`.

## 2. Rigidity: nothing in either neighbourhood can move

Two measurements, both discovery-float with the exact numbers reported separately in §3.

**Single cells.** For the twelve cells nearest each hole, the largest translation along ±x / ±y with
no penetration (`pen_vec` on the local neighbourhood, bisected to 1e-12):

| k | n | max room over 6 nearest cells × 4 directions | verdict |
| --- | --- | --- | --- |
| 23 | 509 | **`3.213e-10`** (cell 83) | locked |
| 32 | 998 | `2.500e-1` (cell 881, straight down) — every other cell `<= 5.0e-3`, most `<= 5e-5` | locked, one outlier |

**Slabs** (the group case a per-cell measurement cannot see: a row locked cell-by-cell can still be
free as a body if the freedom is shared). The slab facing each wall of the hole, `1.6` cells deep
and `2.6` cells wide, migrated *away* from the hole against the whole complement:

| k | slab `x+` | slab `x-` | slab `y+` | slab `y-` |
| --- | --- | --- | --- | --- |
| 23 | `8.7e-11` (9 cells) | `8.7e-11` (4) | `8.7e-11` (6) | `8.7e-11` (10) |
| 32 | `1.16e-5` (6) | `1.32e-5` (3) | `1.20e-5` (5) | *0 cells — the hole is on the floor* |

**The one loose cell is loose out of the box.** Cell 881 can drop `0.25` because nothing is below it
— and it is itself part of the floor: its own bottom edge *is* the bounding box at `y = 0.0`. Using
the room takes the extent from `31.986239` to `32.236` and costs `0.25/√999 = 7.9e-3` of score, i.e.
**18× the entire k = 32 prize**, for a cell that still would not fit the notch.

This is the same rigidity run 134 measured on the 551 delivered beats (`dL <= 5.517e-13`, free-axis
slack `<= 1.575e-10`): the frontier poses are square-tied, and the two notches are no exception.

## 3. What a beat would have to be, and what it costs exactly

A unit cell placed at the hole's best centre, gated exactly at 40 digits (`p_screen.measure`):

| k | n | placement | axis-aligned cell | 45° cell |
| --- | --- | --- | --- | --- |
| 23 | 509 | `(-6.936177, -4.063849)` | 4 violations, depth **`0.2229`** | 4 violations, `0.2761` |
| 32 | 998 | `(27.596035, 0.389907)` | 2 violations, depth **`0.1555`**, side grows to `32.0963` | 3 violations, `0.3169`, side `32.3034` |

So the void is 2–4 contacts deep: no placement, at any exact word, fits. A beat is therefore a
**re-tiling** — replace `r` cells of the notch's neighbourhood by `r + 1` — and doc 75 prices it:
`+0.530` unit² of void to save at `k = 23`, `+0.119` at `k = 32`. The cheaper of the two is the
cheapest large band in the whole table, and it still needs a 26-cell obligation on a 998-cell pose
with 147 distinct angle classes (doc 94 refuses it under R1/R2).

## 4. The prize, exactly

`row_score(n+1, L) - row_score(n+1, k)` with `sqscore`'s `L/√n - 1`, in `Decimal` at 40 digits:

| k | row | delivered | at the frontier side | gain |
| --- | --- | --- | --- | --- |
| 23 | 510 | `0.018554...` at `23.0000000019` | `0.018270...` at `22.9897770950` | **`4.527e-4`** |
| 32 | 999 | `0.0124351955` at `32.0000000019` | `0.0119998047` at `31.9862386204` | **`4.354e-4`** |

**Total `8.881e-4`** — that is `0.38 %` of the `0.23251` band-inheritance programme (doc 75 §2) and
`0.004 %` of the `22.218056945` score. For scale: the *median* band prize in the table is `4.4e-4`,
so these two famous openings are worth exactly a typical band, not more. The largest single prize in
the table is `k = 3`, worth **`0.1196` — 269× the k = 23 notch** (doc 94).

## 5. Verdict

**Both notches are closed by rigidity, not by failed search.** The frontier pose cannot be
rearranged into `n + 1` cells by any legal motion of one cell or of any facing slab; the only loose
cell has its freedom outside the container; and a re-tiling is an undecidable obligation at
`n = 509 / 998`. Nothing is promoted, and the honest budget statement is that **no further run here
can succeed**: this was the last structural opening in the table, and it is worth `8.9e-4`.

**Controls.** `notch136 --selftest` **3**: the prize arithmetic against `sqscore` (agrees to 1e-15);
both frontier poses legal at their delivered sides with 0 violations at 40 digits (`509` cells at
`22.9897770950`, `998` at `31.9862386204`); the scan finds a hole strictly between `0.5` and `1.0`.
Plus the frame calibration of §0 (`0.7151` vs doc 75's `0.7171` on the table pose) and the agreement
of the single-cell and slab measurements.
