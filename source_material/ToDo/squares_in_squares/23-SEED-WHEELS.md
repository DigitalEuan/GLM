# 23 — construction grammars: the n = 10 seed wheel and the two-frame motif (run 55)

Instrument `scripts/seed_wheels.py` (selftest 7/7), ledger
`workspace/push/seed_wheels.json`. Read-only: no row changed, no score moved.

Answers the run-55 review. Its premise is the right one: three runs of polishing
(`21` §5, `22` §5) moved 0.76–0.92 of side and produced no new word, because they
were optimising arrangements inside a family. This run builds two **new families**
as wheels, and reports their boundaries rather than a global negative.

## 1. The wheel contract, and the expressiveness ladder

Every wheel here has six parts and declares its scope up front, so a refusal says
**what was excluded**, not merely that nothing was found:

| part | here |
| --- | --- |
| grammar | 2 tilt classes × 10×10 wall frames × 2 fills, or 1 centred fill × 9 offsets |
| count law | 2 tilted + 8 upright = 10, checked per cell |
| builder | exact, in ℚ(√2), no fitting |
| gate | `seam_wheels.exact_gate`, all separating axes, no floats |
| scorer | `packlib.finalize` then `sqscore.row_gain` (never the unpadded side) |
| ledger | survivors **and** refusals, with the rule that produced each |

    SCOPE: field Q(√2); frames 1–2; masks {full, strip, two-tilt, two-frame union};
    placement wall-anchored on the √2/2 grid or centred with a Q(√2) offset;
    angles {0, π/4}; translations a declared finite set.
    EXCLUDED: angles outside {0, π/4} (rational-t fields are certifiable but out of
    scope here), three or more lattices, non-wall-anchored fills.

## 2. PART A — the two-tilt seed wheel at n = 10

Two tilted 45° squares have exactly **two** relations up to the square's own
symmetry, and the first draft of this grammar got that wrong: it listed
`(0,0)-(1,1)` and `(0,1)-(1,0)` as different shapes when they are the same shape
rotated. The two classes are

    edge    centres 1 apart along a 45° normal   → the squares share an edge
    corner  centres √2 apart along an axis       → they touch at a corner

Both are now tested (`pair shapes are 2 distinct classes`).

**Wall-anchored grammar** — 2 pair classes × 10×10 frames on the √2/2 + ½ grid ×
2 declared 8-square fills (a 3×3 block minus a corner, a 2×4 bar), all anchored
at the near corner:

    400 cells, 44 certified, 0 gains, best certified side 4.000000000

Four is exactly the grid at n = 10, so this grammar buys **nothing at all**: the
tilted pair is not worth a single unit of side when the block is pinned to a wall
and the fill is one of those two shapes.

**Centred grammar** — the delivered 8-square fill with the two-tilt block centred
(`κ = L/2 + κ₀`, `κ₀` on the √2/2 + ½ grid, 9 offsets per axis, both classes):
36 cells, and the best is

    3.707106791  (centred/edge, offset (−1+½, −1+½))   vs delivered 3.707106783

a difference of 8e-9, which is the instrument's 1e-8 nomination resolution and not
a real separation (the finalizer's pad is 1.9e-9): the seed certifies **at** the
delivered side. That cell is the delivered row's own construction, so the wheel
contains the known row and certifies it; nothing in the 36 certifies below
delivered minus the 4e-8 gain threshold.

Totals: **436 cells, 80 certified, 0 `feasible_gain`.**

**Correction (run 56, `24-N10-OPTIMAL.md`): the 0-gain result was forced, not
informative about room.** `s(10) = 3 + 1/√2` is **proved optimal** (Stromquist,
Electron. J. Combin. 10 (2003) #R8, Theorem 1), so the Karakuş floor 3.192582 is
0.514524 *below* the true optimum: that 0.51 is bound looseness, not unclaimed
side. The wheel therefore **recovered a proved optimum**, which is a positive
control for the builder, gate and mask. The earlier phrasing of this section
("0.51 of theoretically admissible side that this grammar never reaches") is
withdrawn. Two things still follow, and they are the useful part:

* the **fill** is the binding component, not the tilt pair. The pair is worth
  exactly zero when the fill is a corner block (best = grid), and the delivered
  row's advantage over the grid comes entirely from its 8-anchor fill placed
  *centred*, with the tilted pair dropped into the gap;
* there is nothing to cascade. A seed pays along r = 1 only if its slack
  `δ = L − 3` is below the delivered 0.707107. Nothing here is: the best is
  0.707107 exactly. So the payoff of this grammar is zero by **absence**, not by
  ranking — which is the distinction the review asked the ladder to make.

This is a boundary on a declared grammar of 436 cells. It is **not** a claim that
n = 10 or the r = 1 column is exhausted: the gap is 3.1926…3.7071 and closing it
needs a fill that is neither of the two wall shapes nor the delivered 8 anchors.

## 3. PART B — the two-frame motif, acceptance test on n = 290

`22` §3 refused n = 290 because its tilted squares do not lie on one lattice.
Representing the tilted part as a **union of two (frame, mask) pairs** now
reconstructs it exactly, before any perturbation:

| n | frames | mask shapes | upright | non-lattice offset | exact gate | rebuild error |
| ---: | ---: | --- | ---: | ---: | --- | ---: |
| 290 | 2 | 5×5 + 5×5 (25 + 25) | 240 | 0.2721·√2 = 0.384808 | pen 0 | 1.7e-9 |
| 226 | 1 | 5×5 (25) | 201 | — | pen 0 | 1.0e-9 |

Two frames, two masks, one shared fill, one exact gate. The n = 226 control walks
the same code path and reports one frame, which is the check that the split is
not simply always returning 2.

**A bug worth recording**, because it would have published a false structural
claim: the first version of the split put a site with residual −1e-9 at
`frac = 0.999999999` instead of `0.0`, so n = 226 split into groups of 24 + 1 and
n = 290 into three. Rounding the residue and taking it mod 1 again folds that
back. The earlier "two lattices, offset 0.384808" statement was right in
conclusion and reached by a coarser route; the split now proves it.

## 4. Repairs to the instruments

* **Orientation matching** in `diamond_mask` compared sorted position sequences.
  On the dense 10-square row a tilted and an upright square can sit at almost the
  same coordinate and swap order, so the check failed on a correct rebuild. It is
  now a greedy distance-sorted **bijection** with orientations compared per pair.
* **Pair classes**: 3 declared shapes → 2 classes (above), which also cut the
  wall grammar from 600 to 400 cells.
* The delivered n = 10 row is *centred*, so it was never in the wall-anchored
  grammar's image; adding the centred variant is what turned the wheel from
  "cannot express the row" into "contains the row and nothing better".

## 5. What this does not show

* Both grammars are **bounded and declared**: 436 cells at n = 10 only. No other
  row was searched.
* **No composition**: each cell is one pair plus one fill. The review's "compose
  several moves" is not implemented.
* **Two-frame atoms are reconstructed, not perturbed.** The acceptance test
  passed; changing the second frame's offset is the next step and is not done.
* **Fill is not a grammar.** Only three fills are declared (two wall, one
  delivered). A fill grammar can still test coverage (e.g. Göbel's alternative
  n = 10 packing) but cannot produce score there: n = 10 is optimal.
* No rational-t angles, no non-45° tilts, no three-lattice atoms (all excluded by
  `SCOPE`).

## 6. Files

* `scripts/seed_wheels.py` — `Seed`, `PAIR_SHAPES` (2 classes), `seed_wheel`
  (wall, 400 cells), `centred_wheel` (36), `_cell`, `split_lattices`,
  `describe_two`, `SCOPE`; `--selftest` 7/7.
* `scripts/diamond_mask.py` — `match_states` (bijection) replacing the sorted
  orientation comparison.
* `workspace/push/seed_wheels.json` — 436 seed cells, 2 two-frame rows, the scope.
* follows `22-DIAMOND-MASK.md`; the n = 10 start it tests is the top of the
  optimistic r = 1 column re-ranked there in §6.
