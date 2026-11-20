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

The spin over `k = 1..9` at the same word never beats a delivered row: `k = 1` behind by 0.8229,
`k = 3` by 0.1158, `k = 5` by 0.1158, `k = 6` by 0.0447, while `k = 2, 4, 7, 8, 9` have no
delivered row at those counts and are recorded as uncalibrated — every comparison exact in
`Decimal` through `DecimalWitness.scalar`. The staircase is a *reading* of the census's row, not
a better packing.

## 5. The pocket, decided exactly

The corner pocket is decided by an exact cage (`staircase_cage`) — no scan, no tolerance, no
float anywhere in the decision.

A centre `p` of a unit square of word `w` is feasible iff it clears every sentence square on one
of the four declared axes — i.e. iff it lies outside every square's **no-fit octagon**, the
intersection of four exact slabs. The cage covers the whole `L`-box with exact `Quad` boxes in
the candidate word's own frame and prunes a box only when that is **provable**: the box lies
wholly inside one square's octagon, or wholly outside the `L`-box. Every surviving box is
therefore a superset of feasible centres, and every quantity below is exact `Quad`/`Fraction`
arithmetic — the slab itself is `23/4`, a rational, because `L/2 = 23/4 + √7/4` and the word's
half-extent is `√7/4`.

For the census word against the 149 squares:

```
capacity = 1          cover = 24 exact boxes at side 1/8
cover extent          u: 5/8 = 0.625        v: 3/4 = 0.75
witness centre        (u, v) = (97/16, 31/16)
```

Two word-aligned unit squares that do not overlap have centres at least `1` apart along one of
that word's axes, so a cover narrower than `1` in **both** axes holds at most one centre: the
pocket's word-aligned capacity is exactly **1**, not `≥ 2`. The square it holds is the **cap
brick** — the last column's `A` brick repeated one column out (`u + 12`, `v = (17 + √7)/8`),
exactly tangent along `u` to its twin (`Δu = 1`, `Δv = 0`).

```
N = 150 = 149 + 1 cap brick      L = 23/2 + ½√7
clearance = 0     contacts = 449     violations = 0
```

And with that brick in place the cage is **empty for the census word itself** — the pocket is
closed, so 150 is the word-aligned ceiling at this side, not merely a bound.

## 6. The word spin: the closure law is one line

The two brick layers are `v_A − v_B = 2c(c + s) − (1 + s)` apart, so the residual is

```
v_A − v_B − 1 = 2c(c + s) − (1 + s) − 1 = s·(2(c − s) − 1)
```

which vanishes iff `s = 0` (the degenerate axis word) or `c − s = 1/2` — and `c − s = 1/2` on
the unit circle pins `(c, s) = ((1 + √7)/4, (−1 + √7)/4)` up to signs. The staircase is
**field-rigid**: it closes at one word and refuses every other by `staircase_layer_gap`.

Spun over **62 declared unit words** (the wheel's 45° word in Q(√2), the Slope 2:1 word in
Q(√5), the Seventh and every other unit word of Q(√7) at height ≤ 8, and every Pythagorean word
with denominator ≤ 13), the constructor is actually run, and it closes at exactly one:

| word | field | residual `v_A − v_B − 1` | verdict |
|---|---|---|---|
| 45° | Q(√2) | `−½√2` | `staircase_layer_gap` |
| Slope 2:1 | Q(√5) | `2/5 − 1/5√5` | `staircase_layer_gap` |
| Seventh `(√7/4, 3/4)` | Q(√7) | `−15/8 + 3/8√7` | `staircase_layer_gap` |
| `t = 1/2` | Q | `−28/25` | `staircase_layer_gap` |
| `t = 1/3` | Q | `−9/25` | `staircase_layer_gap` |
| `t = 1/5` | Q | `5/169` | `staircase_layer_gap` |
| **census** | Q(√7) | **0** | **closed** |

## 7. The second word: no field-compatible word places the 151st square

The 150-square sentence has a closed pocket for the census word. Could a *second* exact word
place the 151st square at `L = 23/2 + ½√7`? The same exact cage answers it against the 150
squares, for **78 field-compatible words**: all 22 unit words of Q(√7) at height ≤ 8 (the
census word and its mirrors, the Seventh, the Pell-type words such as `(5 + √7)/8`, the rational
words) and every Pythagorean word with denominator ≤ 13, which embeds in Q(√7) as a rational
pair — so the whole test stays in one field and every comparison in it is exact.

**Every cage is empty: 78 of 78.** No second word places the 151st square inside the `L`-box,
so the obstruction is not this one word's arithmetic — the pocket is closed for
`Q(√7) ∪ Q_Pyth`, and the table's escape is precisely a rotation that lies in neither.

The sweep is **66 cages, not 78**: a quarter turn of a word (`(c, s) → (−s, c)`) leaves the
square unchanged, so a cage answers for a whole rotation class at once and one representative
per class decides every word in it. Two loss-free changes took the sweep from 40.0 s to 19.5 s:
the class reduction, and a rational pre-filter that skips a cell when its own coordinate is
further from the whole box than that cell's largest separation need (a cell that skips cannot
cover the box, so nothing is proved less). No verdict moved: all 66 cages are empty, the 149
cage still has capacity 1 with cover `5/8` × `3/4`, and the cap brick is still tangent `Δu = 1`.

### 7.1 Mixing the census word with the table's own rotation

The census's own row does not use a second field word: it spends two squares on a **rotation of
0.614761828896 rad**, exactly `19211307153/31250000000`. That angle is rational, but its cosine
is not a field element — so this test is *measured* wherever it cannot be caged, and is labelled
as measured here.

* Rounded **up** at `1e−25` into Q(√7) (so `cos² + sin² ≥ 1` and the caged square is the table's
  square grown by `1e−25`), the rotation still finds a placement against the exact 149, and the
  exact gate certifies **N = 150 at `23/2 + ½√7`, clearance 0, 449 contacts**. The table's own
  rotation *does* close a 150th square at the census side.
* It does not close the 151st. Two such squares side by side along the word's own `v` are one
  rectangle of sides `(1, 2)` in that frame; the cage for the rectangle against the 149
  **collapses to a single box of width `1e−3` with no witness in it** — a degenerate tangency —
  and an exact `17 × 17` point scan inside that box finds no feasible pair either. With the cap
  brick in place the cage is *empty* for the rotation too, so the pocket admits one extra square
  and no more.
* With the **census** word the same rectangle cage is **empty**: an exact proof, and the same
  fact as capacity 1 read another way.

So the honest answer to "does 151 close at the census side" is **no, not as a sentence**: at most
one extra square fits, and that is the certified 150. The delivered row reaches 151 the other way
— by tolerance. Replaying its own two rotation squares against our exact 149 gives worst pair
slack `−2.365e−9` (an odd square against a wall brick), i.e. an overlap: the table's n = 151 is a
12-decimal pose held at ~`1e−9`, not a packing at the exact side. No row changes.

## 8. Verification

* `glm_wheels.py --selftest` — **27 controls**, exit 0 (about 2 min). Control 25 is the staircase: the
  125 = 55 + 66 + 4 split, the twelve-column walk with its three repeats, all 24 named-axis
  tangencies exact, the gate at `N = 149`, `L = 23/2 + ½√7`, clearance 0, the 9.0e-8 census
  agreement, the thirteenth column's exact pinch, the odd word's non-membership in Q(√7), the
  exact cage (capacity 1, cover `5/8` × `3/4`, witness centre), the certified **150**, the cap
  brick's `Δu = 1` tangency, the empty cage against the 150, and the `k = 1..9` calibration
  spin. Control 26 is the word spin (62 words, one closed, the residual identity
  `2c(c+s) − (1+s) − 1 = s(2(c−s) − 1)`) and the second-word test (78 field-compatible words,
  66 rotation-class cages, all empty). Control 27 is the mixed word: the table's own
  `19211307153/31250000000` rad rounded up at `1e−25` into Q(√7) closes a certified **150**
  (clearance 0), refuses the 151st (the `(1, 2)` rectangle cage degenerates, no witness, and an
  exact `17 × 17` point scan finds no pair), and the census word's `(1, 2)` rectangle cage is
  empty; the control also replays the delivered rotation pair against the exact 149 and reports
  the measured overlap `−2.365e−9`. Control 5 exercises `staircase_layer_gap` on the 45° word;
  control 24 records the k = 2, 3, 4, 5 ring verdicts (see doc 57 §5).
* `glm_wheels.py` — spin: spatial **48/48 certified**, 0 refused (`Ring k=1`, `Staircase k=5`);
  sequences 6/7; lattice 24/28.
* `glm_wheels.py --audit` — bytecode float audit of every decision function.
* `grammar_induction.py --selftest`, `qsqrt2.py --selftest`, `field_triage.py --selftest`,
  `scripts/record_guard.py` — all OK.

Nothing touches `submission.csv` or `WHITEBOARD.md`; no row changed and no score is claimed.
