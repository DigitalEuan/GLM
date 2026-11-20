# Run 90 — one seam law, a malformed declaration that cannot certify, and the ridge rungs

Two items: finish the unification started in run 89 (Strip and Pocket laws, plus a control
for a genuinely malformed declaration), and give the field census's remaining algebraic
rungs — Q(√5), Q(√7), rational-t — wheel cells that the *same* exact gate verifies.

No row of the table moved. `submission.csv` and the root whiteboard are untouched.

## 1. Strip and Pocket now differ only in family and parameters

`_assemble_field` already sets the `diamonds` law, so `p_strip`'s second assignment was
dead weight and `p_pocket` had no `seam` law at all. Now:

```python
p_strip  → _assemble_field(... family="Strip",  params={"k": k, "m": m}) + laws["seam"]
p_pocket → _assemble_field(... family="Pocket", params={"k": k})         + laws["seam"]
```

Both carry `diamonds` (once, from the assembler) and `seam` (from the builder), so **the
two claims differ only in `family` and `params`** — which is the statement that a pocket
is the strip at m = 1, made in the claim rather than in a comment. Control 19 already
pins state, words, L and N; it now keeps passing with the claims equal up to those two
fields.

## 2. A malformed declaration is refused by `declaration_overlaps`, not absorbed

Run 88's control 5 exercised the law with `drop_colliding=False` — a *flag*, not a
malformed declaration. Control 20 is the real thing, three ways:

| malformation | who catches it |
|---|---|
| two **coincident** slots | the gate: `declaration_overlaps`, `violations` in the detail |
| two slots **1/10 apart** | the gate — no tolerance, so "nearly on top of each other" is an overlap like any other |
| a slot over an axis cell with the insertion rule **off** | the carrier rule: `declaration_overlaps` |

The first two matter because the insertion rule *cannot* see them: it compares axis cells
to slots, and two slots overlapping each other leaves every axis cell untouched. Before
this run the only defence against that was "the author would not do that"; now the gate
refuses it, which is why `_assemble_field` runs the gate on the *assembled* sentence
rather than trusting the declaration.

## 3. The ridge: one sentence, every quadratic rung

The strip's 45° diamond nests in a seam of width √2/2 because that is exactly where the
tilted square touches the four corner blocks. Generalise the word and the same contact
condition gives the width in closed form. With the tilted square centred in the seam and
the nearest block cell centred at `(k − 1/2, k − 1/2)`, the centre difference is
`d = −(1+w)/2 · (1, 1)`, and the two binding slacks are

```
along the tilted square's own axis u = (c, s):   (1+w)(c+s)/2 = (1 + c + s)/2   ⟹ w = 1/(c+s)
along the block's axis x:                        (1+w)/2     = (1 + c + s)/2   ⟹ w = c + s
```

so `w* = min(1/(c+s), c+s)` and `L = 2k + w*`, both exact field elements. No ladder, no
scan, no tolerance: the width is derived from the contact condition and the sentence is
built at clearance **exactly 0**.

The 45° member is the strip: `1/(√2) = √2/2`, so `L = 2k + ½√2` = `S(k,1)` cell for cell
(control 21 asserts it). The other members are new rungs:

| family | word | field | L (k) | gain over grid | witnesses | verdict |
|---|---|---|---|---|---|---|
| `Slope` 2:1 | `(2, 1)/√5` | Q(√5) | `2k + ⅓√5` | `1 − ⅓√5 ≈ 0.2546` | 4 | certified |
| `Seventh` | `(√7/4, 3/4)` | Q(√7) | `2k + 6 − 2√7` | `2√7 − 5 ≈ 0.2915` | 4 | certified |
| `Tilt` t=1/2 | `(3/5, 4/5)` | Q (in Q(√2)) | `2k + 5/7` | `2/7 ≈ 0.2857` | 4 | certified |
| `Ridge` 45° | `(½√2, ½√2)` | Q(√2) | `2k + ½√2` | `1 − ½√2` | 4 | = the Strip |

With k = 1, 2, 3 that is **nine new certified cells and spatial 40/40, 0 refused**. The
word is checked on the circle exactly (`cos² + sin² = 1` in the field, a refusal if not),
so nothing is normalised numerically: the Q(√7) member's `(√7/4)² + (3/4)² = 7/16 + 9/16`
is an identity the class verifies, not a rounding.

## 4. The gate is now one procedure over any `Quad(d)`

`exact_field.Quad` already carries exact sign, floor, abs and order for any square-free
`d`, so `qgate(cls, state, words)` is a *port* of `qsqrt2.gate` — same axes, same
`|dx| ≥ 2` prune, same return keys — parameterised by the field class. The witnesses
became field-aware rather than field-specific:

- `PackingGateWitness` → `gate_of(claim)`, which uses `qsqrt2.gate` for `d = 2` (the path
  every existing cell passes, untouched) and the port otherwise;
- `ContactGraphWitness` → `pairs_of(claim, i, j)`, same rule;
- `ConservationWitness` → the integer `N` is rebuilt in the *claim's* field (`type(L)(n)`);
- `spatial_decimal` → the same 70-digit recomputation with `half = type(L)(1/2)`;
- `_tag` → the grid side `⌈√n⌉` is rebuilt in the claim's field, so a Q(√5) side and a
  rational grid can be compared (this was the type error that first said "cannot mix
  Q(sqrt 2) with Q(sqrt 5)").

Control 21 proves the port agrees with the original **exactly** — ok, L, clearance,
contacts, violations — on the three diamond atoms, and that the 45° ridge reproduces the
Strip's state and side.

## 5. Calibration against the delivered table

Each new cell records `meta["table_side"]` (the delivered side, taken from the exact
Q(√2) lift of that row — no decimal) and `meta["beats_table"]`, a Decimal comparison of
two exact values. At n = 5 the delivered row's side is `2 + ½√2 = 2.707107`, and every
rung loses:

| rung | L | gap to the delivered side |
|---|---|---|
| `Seventh` k=1 | `8 − 2√7 = 2.708497` | `1.39e−3` |
| `Tilt` t=1/2 k=1 | `19/7 = 2.714286` | `7.18e−3` |
| `Slope` 2:1 k=1 | `2 + ⅓√5 = 2.745360` | `3.83e−2` |

The ordering is the expected one: 45° is the best angle for this construction, and
Q(√7) is the nearest competitor at 1.4 thousandths. **None of them beats the table**, and
none of them is claimed to.

For n = 17 and n = 37 the calibration is *not available*: those delivered rows contain an
orientation outside the axis/45° alphabet (`_word_of` returns None), so they do not lift
into Q(√2) and have no exact side to compare against. The cells are recorded as
**uncalibrated**, not as wins — the distinction is in the data
(`meta["table_side"] = None`) and in control 21's printed line.

## 6. Refusal laws recorded

- `word_off_circle` — a declared `(c, s)` with `c² + s² ≠ 1`; the control asks for
  `(0, 0)` in Q(√5) and is refused.
- `ridge_cuts_corner` — should the derived width still leave an overlap, the builder
  refuses with the exact violation count instead of assembling a bad sentence. It did
  fire during development: at the *half-extent* width `(c+s)/2` the 2:1 tilt overlaps one
  pair, which is exactly why the width is derived from the contact condition rather than
  assumed from the 45° picture.
- `degenerate_cell`, `t_out_of_range` — the existing family guards, unchanged.

## 7. What this run does not claim

- **The ridge reaches N = 4k² + 1 only.** The census's n = 18 row with side `7/2 + √7/2`
  is not in this family (18 ≠ 4k²+1 for any k), so that specific rung remains uncaptured;
  the Q(√7) member reaches n = 5, 17, 37 at `8 − 2√7 + 2(k−1)` instead.
- **The rational-t member's side is rational** (`2k + 5/7`): the angle is Pythagorean, the
  side is not new arithmetic. Only the Q(√5) and Q(√7) members have irrational sides.
- **`qgate` is a port, not a new theory.** It is verified equal to `qsqrt2.gate` on the
  three atoms and used by nothing in the Q(√2) path.
- **No row changed, no score claimed.** Every new cell is dominated by the delivered table
  or uncalibrated.

## 8. Verification

| check | result |
|---|---|
| `glm_wheels --selftest` | **21 controls** (derived count), exit 0 |
| `glm_wheels` spin | spatial **40/40**, sequences 6/7, lattice 24/28 |
| `glm_wheels --audit` | **197 functions, 0 offenders** |
| `grammar_induction` acceptance | 10/10, 19/19, 40/40 exact |
| `qsqrt2 --selftest` | 11/11 |
| `field_triage --selftest` | 4/4 |
| `record_guard.py` | OK |

Entries `53-RIDGE-AND-RUNGS.md`; records `31`–`53`.
