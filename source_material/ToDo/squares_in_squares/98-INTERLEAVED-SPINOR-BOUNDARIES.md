# 98 — The interleaved spinor boundary: built, gated, and priced out (Run 141)

**Run 141, 2026-11-25.** Instruments `scripts/interleaved_boundary.py` (new: the
interleaved two/three-domain constructor, the exact integer gate and the tilt
price); ledger `workspace/push/interleaved_boundary.json`. Doc 97's §4 asked for
this: the butted twin family is capped at `L >= ceil(sqrt n)` because a straight
interface *adds* two extents, so the next family has to let the two bounding
boxes overlap. That family is built here. It beats the straight-line bound — and
still cannot beat the grid, for a reason that is now an exact inequality.

**Nothing promoted.** No candidate reached C2, so `submission.csv` and root
`WHITEBOARD.md` are untouched and the delivered total stands at
**`22.217428576`** / 554 beats / 446 grid ties.

## 1. What was built

`interleaved_boundary.py` assembles two or three square-crystal domains in one box:

| piece | what it is |
| --- | --- |
| substrate `A` | axis-aligned unit cells: an `a1 x a2` rectangle, a **staircase** whose column heights step down, or a rectangle with a `u x v` **corner notch** |
| grain `B_k` | a `b1 x b2` square-lattice block rotated by a rational spinor `tan(theta/2) = p/q`, so `cos = (q^2-p^2)/(p^2+q^2)` and `sin = 2pq/(p^2+q^2)` are exact rationals |
| interface | `B_k` is translated by `(dx, dy)` **into `A`'s bounding box**, and the collision is resolved by deleting from one side only |
| control | every surviving pose is re-decided from scratch by `import_n090`'s independent exact SAT (`verify`) before it may count |

Two yield rules, because they are genuinely different geometries:

- `give="block"` — the tilted grain gives way. `A` keeps every cell; every cell of
  `B` that collides with `A` (or with an earlier `B_j`) is deleted. What is left is
  the tilted grain's *far side* wedged against the axis grain's corner.
- `give="sub"` — the substrate gives way. Every axis cell a tilted cell touches is
  deleted, so the whole grain survives and `A` grows a **notch exactly where the
  grain lands**. This is the stepped/sawtooth boundary in its purest form: the
  interface is the grain's own footprint.

Cells lost either way are made up by enlarging `A`, and the pose is then
**thinned** back to exactly `n` (drop the top-right axis cells; removing cells
can never create an overlap, and the pose is re-verified anyway).

## 2. Exact arithmetic on a fixed grid

Every coordinate this constructor can emit is a rational whose denominator
divides `G = 22 100 = 2 x 2 x 5^2 x 13 x 17` (the spinor denominators times 2 for
half-integer centres times 2 for half-integer offsets). So after one exact
conversion the whole search runs in **integers**:

- `pair_slack2` returns **twice the exact separating slack scaled by `G`** — same
  four axes as `import_n090.pair_slack`, denominators cleared; its sign is the
  sign of the rational slack, so no decision changes.
- `extent` uses the identity that a unit square rotated by `(c, s)` has coordinate
  extent exactly `|c| + |s|`, which is 8x cheaper than enumerating corners and is
  pinned equal to the corner bbox by control 8.
- the winning pose is converted back to `Fraction` (`as_frac`) and re-decided by
  the independent SAT; the promotion render uses `inflate(1e-9)` and the 4d
  perturbation bound exactly as `promote_n090.py` does.

No float appears in any decision path: counts and heights are `int`, coordinates,
slacks and sides are `int` or `Fraction`, and the only `float` in the file is a
`float(...)` inside a print statement. (`glm_wheels --audit` is clean.)

The first version did the hot loop in `Fraction` and took **15 ms per placement**;
the integer rewrite is **~110 us**, which is what made the full space affordable:
**270,000 placements in 30 s**.

## 3. Controls (9, all exact)

1. all six spinors satisfy `c^2 + s^2 = 1` exactly and land on the `1/22 100` grid;
2. a raw `4x4 + 3x3@(1,3)` placement collides in **4 pairs** under the independent
   `Fraction` SAT; after pruning **3 cells**, SAT finds **0** overlaps in 22 cells;
3. **POSITIVE CONTROL — interleaving beats the straight-line bound:** the same two
   blocks give interleaved side **7.2000** against doc 97's butted bound **8.2000**,
   a saving of exactly **1.0000** (the whole stack offset). This is the instance that
   falsifies "a two-grain family is capped at the sum of its extents";
4. a stepped top edge `[4,4,4,3]` deletes **2** cells where the solid `4x4` deletes
   **3** — the step absorbs a cell that would otherwise be sacrificed;
5. `give="block"` keeps 4 of 9 tilted cells; `give="sub"` deletes **2 substrate
   cells** and keeps all **9**, still 0 overlaps;
6. edge cases: a `2x2` twin buried in the substrate loses all 4 cells (refused); a
   distant `3x3` loses 0 and its side (24.20) exceeds the bound (8.20);
7. bookkeeping identity across three domains `20 + 9 + 9 - 5 = 33` exactly, 0
   overlaps over 528 pairs; thinning drops 5 to reach 15 and stays legal;
8. `extent` equals the corner bbox exactly on five poses;
9. **the price of a tilt** (below) is the inequality it claims to be, checked
   exactly for every spinor and three block shapes.

## 4. The positive control, and what it does *not* settle

Interleaving breaks doc 97's cap: at 22 cells the family reaches 7.2 where the
butted arrangement of the same blocks needs 8.2. That is a real falsification and
it is why this experiment was worth running.

It does not follow that the family can beat the **grid**. `ceil(sqrt n)` is not the
butted bound; it is the area bound rounded up, and the grid attains it. Every
interleaved assembly found below sits at or above `ceil(sqrt n)`, and the reason
is §6.

## 5. Search coverage and results

Sweep: 6 spinors (`q <= 4`) x 5x5 corner-anchored offsets per axis x both yield
rules x every near-square block size that can fill the gap x every substrate shape
and family (`near` window 60 cells), capped at 3,000,000 placements.

| n | placements | assemblies with exactly n cells | best side | grid | delivered | butted bound | gain | promotable |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 18 | 53 700 | 47 786 | **5.000000** | 5 | 4.822876 | 6.0 | `-4.1749e-2` | no |
| 19 | 50 400 | 44 711 | **5.000000** | 5 | 4.885618 | 6.0 | `-2.6241e-2` | no |
| 51 | 165 900 | 157 724 | **8.000000** | 8 | 7.690356 | 9.0 | `-4.3359e-2` | no |

**270,000 placements, 250,221 exact-count assemblies, 0 promotable.**

Two findings in that table matter more than the null itself:

- **the winner is the grid itself.** Every best pose is `2x2 rect + (n-4)-cell
  block` at spinor **`1/1`** — 90 degrees, the identity rotation — with 2, 1, 2
  cells deleted at the seam, 0 thinned, exact SAT **0 overlaps** and minimum slack
  **exactly 0** (touching). The optimiser does not find a tilted grain and lose on
  margin; it declines every tilted grain.
- **the interleaved family does beat the butted bound on all three rows** (5.0 <
  6.0, 5.0 < 6.0, 8.0 < 9.0), so the constructor works — it is competing against
  the grid, not against doc 97's cap, and the grid wins.

Three-dimensional pass (two tilted grains over one substrate, both pruned together):
best 5.000 at `n = 18` (432 placements, 134 exact-count assemblies) and 5.000 at
`n = 19` (720 / 132), again `1/1 + 1/1`. At `n = 51` no three-domain assembly
reached exactly 51 cells inside the 20,000-placement cap, so that row has no
three-grain reading — recorded as searched-and-empty rather than as a result.

## 6. Why it collapses: the price of a tilt

A `b1 x b2` grain rotated by the spinor angle `theta` has bbox
`W = b1 c + b2 s`, `H = b1 s + b2 c`, so

    W H = b1 b2 (c^2 + s^2) + (b1^2 + b2^2) c s
        = b1 b2 + (b1^2 + b2^2) c s
        >= b1 b2 (1 + sin 2theta).

The grain's own side is therefore at least `sqrt(b1 b2) * sqrt(1 + sin 2theta)`,
while an **axis** grain of the same cell count needs only `sqrt(b1 b2)`. The seam
can buy back at most one unit — one cell row of overlap between the two boxes —
so a grain of `m` cells can only profit if

    sqrt(m (1 + x)) - sqrt(m) < 1,   x = sin 2theta = 4pq(q^2-p^2)/(p^2+q^2)^2,

which is the exact rational test `(m x - 1)^2 < 4m` for `m x > 1` (and always true
for `m x <= 1`). `tilt_price` computes it in `Fraction`, and control 9 pins both the
test and the identity above.

| spinor | `sin 2theta` | grain must be at most |
| --- | --- | --- |
| `1/2`, `1/3` | `24/25` (0.9600) | 6 cells |
| `2/3` | `120/169` (0.7101) | 10 cells |
| `1/4` | `240/289` (0.8304) | 8 cells |
| `3/4` | `336/625` (0.5376) | 17 cells |
| `1/1` | `0` | any — this rotation *is* the axis grain |

This is exactly what the sweep shows. At `n = 51` the winning grain is `7x7 = 49`
cells — above every threshold in the table — so **every available non-degenerate
spinor is priced out**, and `theta = 90` degrees is the only survivor: the grid.
At `n = 18, 19` the substrate is 16 cells, which leaves the grain 4-8 cells: the
one size band where a tilt is *not* priced out, and the search does explore every
such configuration (47,786 and 44,711 exact-count assemblies) without finding one
that beats the grid.

Doc 97 said butted blocks cannot help. The sharper statement is this: **a
two-grain interface cannot help at these counts either, because the seam is worth
at most one cell row and a tilt costs `sqrt(1 + sin 2theta)` 21-40 % of the
grain's own side.** The escape is not a *better* interface; it is more grains —
which is what the delivered rows are (§7 of doc 97: 2-9 orientation classes per
row, 6-35 grain contacts), not two.

## 7. The gate: nothing promoted

- **C1 (proof):** every candidate is decided by the independent exact SAT; the
  best poses carry 0 overlaps and a minimum slack of exactly 0 (touching is legal
  in this repository's convention).
- **C2 (margin):** no candidate is strictly smaller than the delivered side. The
  three best sides are **above** the delivered rows by `4.17e-2`, `2.62e-2` and
  `4.34e-2` of score — not close, and negative.
- **C3/C4:** `sqscore` **22.217428576** (554/446), `record_guard` OK,
  `glm_wheels --audit` 0 offenders; this doc records the null and the refusals.

`submission.csv` and root `WHITEBOARD.md` are untouched: the gate is closed to
anything that does not pass C1-C4 with a strictly positive verified gain, and
nothing did.

## 8. What would have to be true for this family to win

1. The grain must be **small** (<= 6-17 cells depending on spinor) — which means
   the substrate carries the box, and the substrate is an axis rectangle whose
   side is already `>= ceil(sqrt(a1 a2))`, i.e. the grid.
2. Or the tilt must be **smaller** than the `q <= 4` alphabet allows: at
   `q = 4` the cheapest word is `3/4` at `sin 2theta = 0.5376`; a word with
   `sin 2theta < 4/49 ~ 0.082` would be needed to make a 49-cell grain
   competitive, and such a word is nearly axis-aligned (a lattice at
   `theta < 2.4` degrees), which the grid already dominates.
3. Or the interface must be worth **more than one row** — which requires the two
   lattices to interlock over a band (cells of each owning area on both sides),
   not merely to overlap their boxes. That is a genuinely different object, and
   the delivered rows suggest where it comes from: they are not two-grain
   assemblies at all, they are 2-9-class polycrystals with many short grain
   contacts.

## 9. Instruments and guards

`scripts/interleaved_boundary.py` — `spinor`, `SPIN`, `G`, `substrate`, `block`,
`variants`, `extent`, `side`, `as_frac`, `pair_slack2`, `prune(give=...)`, `thin`,
`verify`, `straight_bound`, `tilt_price`, `sweep`, `sweep_three`, `gate`,
`render_bound`, `--targets/--near/--cap`, `--selftest` (9 controls).

Checked this run, each exit 0: `interleaved_boundary --selftest` 9 ·
`twin_boundary --selftest` 5 · `notch136` · `glm_plan` 5 · `pure_slide` ·
`beaten_leverage` · `band5` · `ext_census` · `range_leverage` · `construct_seam` ·
`p_screen` · `legal_slide` · `structure --control` and `--check-solver` ·
`perturb` · `anchor_chain` · `void_insert` · `true_geom` · `row_census` ·
`motif_wheels` 13 · `crystal_domains` 4 · `import_n090` 5 · `pub_bounds_check` 4 ·
`witt_octad` 5 · `leech_audit_fix` · `verify_certificates` · `sqscore`
**22.217428576** (554/446) · `record_guard` OK · `glm_wheels --audit` 0 offenders ·
`py_compile`.

**Not claimed.** No row moved. The sweep covers one axis substrate plus one or two
lattice grains with near-square blocks and `q <= 4`; it does not cover interlocking
bands, non-lattice grains, or substrates that are themselves polycrystalline. The
`n = 51` three-domain pass is incomplete by cap. And the tilt-price inequality is
a statement about a *single* grain in an axis substrate — it does not bound a
polycrystal, which is precisely why the delivered rows live there.
