# Run 95 — the staircase: n = 151 extracted, and why it stops at 149

Run 94 ended with a split: the Q(√7) family's side law generalises across all five census rows,
but the ring sentence is `k = 1` only, and n = 151 is "a 151-square staircase" with no grammar.
This run supplies the grammar for the axis layer, builds the seam brick wall from declared
tangency, certifies **149 squares at `L = 23/2 + ½√7` with clearance exactly 0**, and shows
*exactly* why the last two squares of the row cannot join them in Q(√7).

Nothing here changes a row: at n = 149 the family's table side is `12 + ½√2`, so it does not
beat the table, and the 151st pair is a measured refusal, not a failure.

## 1. What n = 151 actually is

The row's 151 squares split 125 axis + 26 tilted. Every axis coordinate, recovered exactly at
70 digits, is of the form `m ± c` with `c = 1/4 + 1/4√7`; the two families are **not** independent
(`j + (1 − c)` is the `−c` family), so the whole axis layer lives on the two lattices
`(a − c, b + c)` and `(a + c, b − c)`.

Read as a grid of integer pairs `(a, b) ∈ [−k, k]²` with `k = 5`, the occupancy is exact and
simple (control 25 pins it):

| block | rule | count at k = 5 |
|---|---|---|
| `A` | `(a − c, b + c)` for `−k ≤ a < b ≤ k` | 55 |
| `B` | `(a + c, b − c)` for `−k ≤ b ≤ a ≤ k` | 66 |
| caps | `(−k − c, −k − c)`, `(−k − c, −k + 1 − c)`, `(k − 1 + c, k + c)`, `(k + c, k + c)` | 4 |

**125 = 55 + 66 + 4.** The two blocks never touch: block `A` sits at `x − y ≤ −1 − 2c` on its
seam edge and block `B` at `x − y ≥ 2c`, and a block-A/block-B pair would need an integer shift
of `1 ± 2c` on one axis — impossible for irrational `c`. The diagonal seam between them is
therefore a real gap, and the gap is where the 24 tilted squares live.

The axis layer is `staircase_frame(cls, c, s, k)`, count `4k² + 4k + 5`, side
`L = 2k + 1 + 2c = 2k + 3/2 + (c + s)` (`staircase_side`) — the same one side law as the ring.

## 2. The seam wall

In the word's own frame `u = (c, s)`, `v = (−s, c)`, the 24 census bricks have **exactly
consecutive integer `u`** — `u_j = u + j` for twelve columns — and two `v`-values per column
differing by exactly 1. Each brick is tangent **along its own `v` axis** to one named seam
square of the frame, and the walk is exact:

| column | frame square | brick `v` |
|---|---|---|
| `a` | `B(a, a)` | `a(c − s) − c(c + s) + need` |
| `a` | `A(a, a + 1)` | `a(c − s) + c(1 + c + s) − need` |

with `need = 1/2 + (|c| + |s|)/2`, and the columns run `a = −k … k − 2` with the column
**repeated whenever `a % 3 == 0`** — at `k = 5` the twelve labels are
`[−5, −4, −3, −3, −2, −1, 0, 0, 1, 2, 3, 3]`. All 24 declarations hold exactly (control 25).

**The two layers close only at one word.** The two bricks of a column are
`v_A − v_B = 2c(c + s) − (1 + s)` apart, so they are edge-to-edge along `v` iff that is 1,
i.e. iff `c − s = 1/2`. With `c² + s² = 1` this forces `c + s = √7/2`, so the closed wall is the
Q(√7) word's own and no other word's: the combinator is field-general in its *argument* and the
Q(√7) word is its only closure. Control 5 refuses the 45° word by `staircase_layer_gap`.

`u` is the wall's one free transverse parameter. Every declaration is along `v`, and `u ⊥ v`,
so sliding the wall preserves all of them; only the non-overlap against the frame constrains
`u`, and the census row fixes the value (`−1357/128 + 211/128√7`). The combinator takes `u`
as an argument — the 149 centres are computed, not replayed.

## 3. The certificate

`staircase_field(7, c, s, 5, u)` → `p_staircase(5)`:

```
N = 149 = 125 axis + 24 bricks        L = 23/2 + ½√7
clearance = 0     contacts = 449     violations = 0
24 declared brick–frame tangencies, all exact
```

Every one of the 149 constructed centres matches a delivered centre of n = 151 to **9.0e-8**,
the scale of the table's own numerical polish. The `Staircase k=5` cell is registered on the
spatial wheel: **48/48 certified**, all four witnesses.

## 4. The last two squares, and the exact reason they stay out

The wall's thirteenth column (`a = k − 1 = 4`) does not fit. At the row's own gauge it
overlaps the top-right cap `(k − 1 + c, k + c)` by

```
clearance = −163/128 + 61/128√7 = −0.0125716...
```

one violation, measured exactly. Sliding the wall does not open the corner: the slide that
removes this pinch by construction (`−d`, `d = 163/128 − 61/128√7`) immediately produces another
pair at `−0.005557` — the wall is jammed between two constraints, and no gauge admits 26 bricks.

That is why the table rotates those two squares. Their angle is `0.614761828896` rad
(`cos = 0.8169108386…`); recovering `cos` and `sin` in Q(√7) at heights up to 4096 gives a pair
whose norm is `868927/1024 − 656073/2048√7 ≠ 1`, so it is not a unit word of the field, and it is
not Pythagorean either (no `t` with denominator ≤ 1024). A field-general Q(√7) staircase
therefore **cannot reach n = 151**: the 24.3° word pinches by `163/128 − 61/128√7`, and the
table's escape is a rotation outside the field.

So the honest count is **149 constructed of 151**, with the 151st pair refused by an exact law
rather than left unexplained. The family's own law is `N(k) = 4k² + 4k + 5 + 2|columns(k)|` —
the `4k² + 4k + 5` axis layer plus two bricks per wall column — at `L = 2k + 3/2 + (c + s)`,
which gives 15, 37, 67, 103, 149, 203 at `k = 1..6`.

Two further measurements, both honest negatives. **(i)** A scan of the corner pocket in the
wall's own frame (120×120 in `(u, v)`, every point gated against the 149) finds the feasible set
is one diagonal strip spanning `0.53` in `u` and `0.63` in `v`, and any two word-aligned squares
need one coordinate at least `1` apart — so at most **one** more word-aligned square fits there
(for instance `(u + 12, m = 17)`, exactly tangent along `u` to its twin), and the word-aligned
ceiling at this side is 150, not 151. This is a measurement, not a certificate, and a single
dilated brick carries no grammar, so the family stays at 149. **(ii)** The spin over `k = 1..9`
at the same word never beats a delivered row: `k = 1` behind by 0.8229, `k = 3` by 0.1158,
`k = 5` by 0.1158, `k = 6` by 0.0447, while `k = 2, 4, 7, 8, 9` have no delivered row at those
counts and are recorded as uncalibrated — every comparison exact in `Decimal` through
`DecimalWitness.scalar`. The staircase is a *reading* of the census's row, not a better packing.

## 5. Verification

* `glm_wheels.py --selftest` — **25 controls**, exit 0. Control 25 is the staircase: the
  125 = 55 + 66 + 4 split, the twelve-column walk with its three repeats, all 24 named-axis
  tangencies exact, the gate at `N = 149`, `L = 23/2 + ½√7`, clearance 0, the 9.0e-8 census
  agreement, the thirteenth column's exact pinch, and the odd word's non-membership in Q(√7),
  plus the `k = 1..9` spin: the count law `4k² + 4k + 5 + 2|columns(k)|` and the assertion that
  no member beats its delivered row (exact `Decimal` differences).
  Control 5 exercises `staircase_layer_gap` on the 45° word; control 24 now records the
  k = 2, 3, 4, 5 ring verdicts (see doc 57 §5).
* `glm_wheels.py` — spin: spatial **48/48 certified**, 0 refused (`Ring k=1`, `Staircase k=5`);
  sequences 6/7; lattice 24/28.
* `glm_wheels.py --audit` — bytecode float audit of every decision function.
* `grammar_induction.py --selftest`, `qsqrt2.py --selftest`, `field_triage.py --selftest`,
  `scripts/record_guard.py` — all OK.

Nothing touches `submission.csv` or `WHITEBOARD.md`; no row changed and no score is claimed.
