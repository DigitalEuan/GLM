# Run 92 — the bar, and the word the table actually uses

Run 90 built a ridge by hand: one tilted square in the seam, its width found from the
binding contact conditions in closed form. Run 91 opened that construction to three more
fields but left it single-seeded. This run lets the ridge hold **m** tilted squares, derives
w\*(m) exactly in the field, checks the 45° member against the Strip cell for cell, and
then answers the question the run was given: does any member reach the census's n = 18 row
at `7/2 + √7/2`? It does not — and reading the row says why, and says which word it uses.

## 1. The bar

A ridge is four `k×k` blocks flush in the corners of a box `[0, 2k+w]²` plus a **bar** of
tilted unit squares sitting in the seam. The bar is edge to edge along the square's own
edge direction `−v = (s, −c)`, centred in the seam:

```python
def _bar_offsets(cls, c, s, m):
    return [(cls(F(2 * i - (m - 1), 2)) * s, -cls(F(2 * i - (m - 1), 2)) * c)
            for i in range(m)]
```

so slot `i` sits at `centre + (i − (m−1)/2)(s, −c)` and consecutive slots share an edge for
every `m`. `N = 4k² + m`; `m = 0` is the plain grid.

## 2. The seam width is linear, so it is exact

Both the blocks and the bar move with `w` — the far blocks by `+w`, the bar's centre by
`+w/2` — so every pair's four axis slacks are **linear** in `w`:

```
d(w) = block − slot = (A_x + B_x w, A_y + B_y w),
d(w)·q              = P + Q w,        |d(w)·q| = need  ⇔  w = (±need − P)/Q,
```

with `need = 1/2 + (|c|+|s|)/2` on every axis (the block's extent along `u` or `v` and the
slot's extent along `x` or `y` are the same expression). Feasibility can only change at
those roots, so `ridge_widths` collects them — one closed-form root per pair, per axis, per
sign, in the field — sorts them, and `ridge_width` returns the **smallest root at which the
exact gate passes**. No scan, no tolerance, no measured threshold: the number is a contact
width by construction, and the gate is the arbiter.

`m = 1, k = None` still returns run 90's closed form `min(1/(c+s), c+s)`; the m-general path
reproduces it exactly (control 22 asserts the equality of the two call forms through the
cells).

## 3. At 45° the bar *is* the Strip

For `k = 1..3` and `m = 1..3` the ridge's state, its slots and its side equal
`strip_field(k, m)` exactly — same cell coordinates, same slot coordinates,
`L = 2k + m√2/2`, `N = 4k² + m`, all nine `(k, m)` cells. So the strip is the ridge's
45° member for every `m`, the same way it was its `m = 1` member in run 90. Beyond the
checked range the law is arithmetic: at 45° `w*(m) = m√2/2` through `m = 4`.

## 4. w\*(2) = 2w\*(1), and beyond that the binding pair may re-bind

| rung | w\*(1) | w\*(2) | w\*(3) | w\*(4) |
|---|---|---|---|---|
| 45° | ½√2 | √2 | 3/2√2 | 2√2 |
| Slope 2:1, Q(√5) | ⅓√5 | ⅔√5 | √5 | 6/5√5 |
| Seventh, Q(√7), census word | 2/7√7 | 4/7√7 | −1/2 + √7 | −3/4 + 5/4√7 |
| Tilt t = 1/2 | 5/7 | 10/7 | 15/7 | 20/7 |

`w*(2) = 2 w*(1)` holds exactly on every rung, and it is a theorem of the construction: the
two-slot bar is symmetric about the seam centre, so each slot is one half-seam closer to its
block than the single slot was. Past `m = 2` the same pair can stop binding. The 45° rung
stays linear through `m = 4` because its bar's ends reach the corner void symmetrically; the
oblique rungs re-bind, and the Q(√7) rung gives a **smaller** width at `m = 3`
(`−1/2 + √7 = 2.1458`, against `3·2/7√7 = 2.2678`) because the third square's corner slips
past the contact line into the void that the single-seed ridge's seam leaves at the box
corners. Control 22 therefore asserts `w*(2) = 2w*(1)` and the monotonicity of `w*(3)`,
`w*(4)`, and **reports** the wider widths rather than claiming a linear law it does not hold.

## 5. The Q(√7) rung was using an invented word

Run 90's `Seventh` rung chose `(√7/4, 3/4)` — the smallest-height unit word in Q(√7).
Nothing tied that choice to the table. Reading the census's n = 18 row does:

```
tilt = 424031039491/1000000000000 rad,  cos_sin at 70 digits →
cos = 0.911437827766… , sin = 0.411437827766… ,
recover_scalar in Q(√7) → cos = 1/4 + 1/4√7 , sin = −1/4 + 1/4√7 .
```

and `cos² + sin² = 1/2 + √7/8 + 1/2 − √7/8 = 1` exactly. So the word the delivered row
uses is **`((1+√7)/4, (√7−1)/4)`**: cosine and sine differ by exactly `1/2`, and their sum
is `√7/2`. `_sqrt7_word` now returns that word, so the rung is the table's rung and its
single-seed side is `2k + 2/7√7` (it was `2k + 6 − 2√7`). Control 22 re-runs the recovery on
every run and refuses if the word moves.

## 6. n = 18 is not a ridge, and the numbers say so once

`N = 18 = 4·2² + 2`, so the only candidate is `(k, m) = (2, 2)`. Every rung's `L(2,2)`:

| rung | w\*(2) | L(2, 2) | decimal |
|---|---|---|---|
| 45° | √2 | 4 + √2 | 5.414214 |
| Slope 2:1 | ⅔√5 | 4 + ⅔√5 | 5.490712 |
| Seventh (census word) | 4/7√7 | 4 + 4/7√7 | 5.511858 |
| Tilt 1/2 | 10/7 | 38/7 | 5.428571 |

The row's side is `7/2 + √7/2 = 4.822876`. To reach it at `(2,2)` a rung would need seam
width `(√7−1)/2 = 0.822876`; the closest rung's `w*(2)` is `4/7√7 = 1.511858`, and at
`m = 1` the same rung gives `4 + 2/7√7 = 4.755944`, still 0.067 away. **No member of the
family captures n = 18** — asserted exactly, per rung, in control 22. The pose differs too:
the ridge at `(2,2)` is 16 axis squares plus 2 tilted; the row is 10 axis plus 8 tilted, so
the mismatch is not a near miss that a shifted width could repair.

## 7. What the row *is*

All 36 coordinates of the row's 18 centres recover exactly in Q(√7) (denominators ≤ 16). Its
ten axis squares have centres on the square `±(5/4 + √7/4)²` — the extremes recover as
`(5/4, 1/4)` and `(−5/4, −1/4)` — and its eight tilted squares carry the word above. So

```
L = 2·(5/4 + √7/4) + 1 = 7/2 + √7/2,          and, since cos = (1+√7)/4,
L = 3 + 2 cos .
```

That is the grammatical answer to the question. The row is a **ring** sentence: its side is
an odd rational part — `3 = 2·1 + 1` — plus **twice a cosine**. The ridge's side is
`2k + w`: an *even* rational part `2k`, flush blocks (their offsets are `0` and `L − k`,
with no half-square shift available), plus a seam width. `7/2` is not of the form `2k`, and
`(√7−1)/2` is not a sum `(c+s)` — the equality `L = 3 + 2cos` also shows the row's free
length is tied to the word's **cosine**, where the ridge's is tied to `1/(c+s)` or `c+s`.
A half-square offset and a cosine law put the row outside the ridge's grammar, which is why
no `(k, m)` reaches it: not a failure of the width, a different sentence.

## 8. Registration, controls, status

- `p_ridge(d, c, s, k, family, params, m=1)`, `_ridge_blocks`, `_bar_offsets`,
  `_ridge_affine`, `ridge_widths`, `ridge_width(cls, c, s, k=None, m=1)`;
  `p_slope`/`p_seventh`/`p_tilt` take `m`.
- Refusals stay declared: `word_off_circle`, `no_contact_width`, `ridge_cuts_corner`,
  `degenerate_cell`, `negative_seam`.
- Cells: `m = 1` at `k = 1..3` as before, plus `m = 2` at `k = 2, 3` on the three non-45
  rungs. `m = 2, k = 1` is refused by the contact-graph witness (`contact_graph_thin`:
  the two-square bar touches only itself, min degree 0) — the same floppiness that keeps
  `S(1, 2)` out of the strip wheel, so the wheel registers the same `k` range.
- **Control 22** asserts the nine-cell 45° identity, the `w*(2) = 2w*(1)` law on four rungs,
  the n = 18 negative per rung, and the row's reading (word, unit circle, 10 + 8, extremes,
  `L = 3 + 2cos = 7/2 + √7/2`).

**Verification.** `glm_wheels --selftest` **22 controls**, exit 0; spin spatial **46/46**
certified, 0 refused, sequences 6/7, lattice 24/28; float audit **195 decision functions,
0 offenders**; `grammar_induction --selftest` 3/3; `qsqrt2 --selftest` 11/11;
`field_triage --selftest` 4/4; `record_guard.py` OK. No row changed; `WHITEBOARD.md` and
`submission.csv` untouched.

Records `31`–`55`.
