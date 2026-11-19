# Run 87 — one contract, a cage without monkeypatching, and the diamond primitive

Run 86 ended with four named friction points and one deferred primitive. This run
answers both, and in doing so corrects a number it published: the 173 placements in
n = 126's cage were counted under two rules that were too generous. What survives is
stronger than what was claimed, because it is now derived instead of hand-set.

Nothing in the table moved. `submission.csv` and the root whiteboard are untouched;
this is an engine run.

## 1. The friction, restated as a test

Doc 49 listed the friction it had hit:

1. `Wheel.spin` wrote `n`, `extent`, `gain` — packing words. A lattice shell has no
   extent, a Sturmian word has no side.
2. A witness that knew about 45° squares could not be reused by a sequence.
3. `DecimalWitness` recomputed separations from `Quad` centres, so it only existed
   for the packing domain.
4. Witness suites were a fixed list of four, one of which (`KissingWitness`) applies
   only to two families.

The test for fixing them is not "does it still pass" — all three domains already
passed. The test is that **one report, one suite mechanism and one Decimal witness
serve all three domains, with no domain-shaped branch inside them**.

## 2. The neutral contract

`Claim` now carries, and `Wheel.spin` writes:

| column | meaning |
|---|---|
| `size` | the domain's own count — squares, ones, lattice points |
| `measure` | the domain's own primary quantity, as `(name, value)` |
| `invariant` | the domain's declared law quantity, as `(name, value)` |
| `witness_count` | how many witnesses this row's suite actually ran |

`Claim.n` survives as a read-only property aliasing `size`, so all 31 spatial cells,
the sequence builders and the lattice builders kept their literals and no control had
to change for the rename. `claim.meta["gain"]` is still where a packing puts its
gain; a sequence leaves it `None` and the column simply empties.

Witness suites are now declared, not listed:

```python
class Witness:
    families = None          # None = every family; else a set of family names

class Domain:
    def suite(self, claim):  # declared `families` filtered by this claim's family
```

`KissingWitness` is the only witness that scopes itself (`families = {"Frame",
"Atom"}`), which is exactly the statement it was making before — now made by the
witness instead of by the wheel's ordering. The other three apply everywhere.

One `DecimalWitness` replaces the packing-only one. It asks the domain for a scalar
projection:

```python
Domain.decimal_model = spatial_decimal | sequence_decimal | lattice_decimal
```

and compares 70-digit `Decimal` values. `spatial_decimal` projects a `Quad` centre
onto an axis; `sequence_decimal` reads the word's letter; `lattice_decimal` reads a
doubled-integer lattice point. Each is ~10 lines and none of them is consulted by the
wheel.

The visible result is one table for everything:

```
spatial: 28/31 certified, 3 refused {'strip_needs_diamond': 3}
sequences: 6/7 certified, 1 refused {'not_sturmian': 1}
lattice: 24/28 certified, 4 refused {'empty_shell': 2, 'rank_budget': 2}
```

with the same six columns, `w` = 4 for packing and sequence rows, `w` = 3 for lattice
`Tile` rows (the kissing witness scopes itself out of them) — the witness count is now
visible evidence rather than an assumption. `glm_wheels --selftest`: **17 controls**,
including control 17, which is a wrong kissing number refused by its own declared law.

One real bug surfaced during the refactor and is worth recording because it had the
signature of a mathematical failure: `Q2(1, 2)` is `1 + 2√2`, not `½`. A helper written
as `Q2(F(1,2))` in one place and `Q2(1,2)` in another produced `declaration_overlaps:
n10 … 10 violations` — a correct refusal of a wrong field element.

## 3. The cage, as a mode rather than a probe

Run 86 solved n = 126's last square with a script that monkeypatched `lift_sentence`,
captured the pre-recovery state, and typed two bounds by hand. That is a measurement,
not an instrument. It is now:

```python
cage_segment(state, words, pos, L, j, dens=(8, 16, 32), bmax=8, tol=None, legacy=False)
```

Given only the state, the words, the placement vector and the free square's index, it

1. reduces the squared contact system `|d·q| = need` to its row space (the rank is
   data, not a guess — n = 126 gives rank 1 from two contacts that share an axis),
2. proves the free square's corner is constrained to a line, with the line's
   coefficients as exact `Q(√2)` elements,
3. bisects the feasible interval **in `Decimal`**, from a point known to be feasible,
   so the segment is measured rather than assumed,
4. enumerates `Q(√2)` points of that line at denominators `dens`, heights `|b| ≤ bmax`,
   and keeps those whose full value lies in the segment *and* whose 45°-rotated box
   stays inside the container, each checked against the exact gate at clearance 0,
5. returns the law, the segment, its width, the placements and the nearest.

`lift_sentence` now returns `pos` (the placed centres) and `lo` (the frame origin)
instead of hiding them, which is what made step 1 possible without a spy.

`qsqrt2 --selftest` gains control 11: it lifts n = 126, finds the unplaced square
(`j = 120`), runs the mode with no bounds supplied, and asserts the rank, the law
`y − x = 11/2 + (5/2)√2`, the placement count, the nearest `x = 43/32`, and that the
nearest passes `gate` at clearance exactly 0. **11 controls, all passing.**

### The correction: 173 was not the cage

Control 11 asserts `count == 4` and, separately, `legacy=True → count == 173`. The
173 is reproducible, and reproducing it showed what it was counting:

- run 86 filtered candidates on `x.a` — the *rational part* of a `Q(√2)` value —
  so a placement whose full value is far outside the segment still entered;
- run 86's box test checked `y` containment but not `x`, so squares parked outside
  the container were admitted, and the exact gate happily passes them because it
  only asks for pairwise separation and containment of the *bounding box it computes*.

Under both flaws the count is 173. With the field value doing the filtering and both
coordinates tested for containment, the cage holds **4** `Q(√2)` placements at
clearance 0, at denominators ≤ 32 and heights ≤ 8: `43/32`, `21/16 + (1/32)√2`,
and two neighbours. The nearest is unchanged — `x = 43/32`, L1 distance 8.2e-3 — so
n = 126's conclusion is unchanged: **off-lattice pose, on-lattice topology**. Only the
size of the cage's field content changes, and it changes downward.

`legacy=True` exists so this correction can never be quietly forgotten: the mode can
still produce the old number, and the control asserts both, side by side, forever.

## 4. The diamond primitive

Doc 49's deferred item: a diamond insertion that *derives* its geometry instead of
hardcoding rows. `DiamondField` is a declaration, not a construction:

```python
DiamondField("n10", cells=("bent", origin, steps_x, steps_y), slots=[(p, q, py), ...])
```

- `cells` is either a **bent grid** `(origin, steps_x, steps_y)` — all `sx × sy`
  products of the two step vectors — or an explicit list of axis-square centres
  `(p, q, py)` (a `Q(√2)` point written as three rationals, `p + q√2` in x,
  `py + q√2` in y).
- `slots` declares where diamonds go, each slot naming the pair of axis squares its
  two corners sit in.
- The **insertion rule** then drops every axis cell that collides with a declared
  diamond, and derives L (the bbox side), the void `V = L² − N`, the gain against the
  grid, and the contact graph. Nothing about L or the contacts is written down.

A declaration that fails the gate raises `Refusal("declaration_overlaps")` — the field
refuses, it does not repair.

Acceptance (the induction test doc 49 named), from `grammar_induction --selftest`
control 3 and the `--diamond` ledger `workspace/push/diamond_fields.json`:

| field | axis | diamonds | dropped axis cells | size | L | void | gain | covered |
|---|---|---|---|---|---|---|---|---|
| n10 | 8 | 2 | 8 of 16 | 10 | `3 + ½√2` | `−½ + 3√2` | `1 − ½√2` | 10/10 |
| n19 | 11 | 8 | 0 | 19 | `3 + 4/3√2` | `−58/9 + 8√2` | `2 − 4/3√2` | 19/19 |
| n40 | 24 | 16 | 0 | 40 | `4 + 2√2` | `−16 + 16√2` | `3 − 2√2` | 40/40 |

Every field is `identical_to_atom` and `L_matches_atom`, i.e. the derived side and the
derived contacts reproduce the delivered atom exactly, and the decomposition is
**100 % exact** in all three cases. That is the primitive doc 49 said was missing: the
induction search failed 44 of 45 states because no template could place a diamond;
with `DiamondField` declared, all three atoms are decomposed by 8+2, 11+8 and 24+16
copies of `Tile1` and the diamond.

Registered on the spatial wheel as three cells (`DiamondField name=n10|n19|n40`), all
certified by the same four witnesses as everything else — the diamond cells are
ordinary cells, which is the point of the contract work in §2.

## 5. What this run does not claim

- **n = 19 and n = 40 declare their axis cells explicitly.** Their axis sets are not
  product grids, so the bent-grid form does not generate them; the declaration lists
  them. The derivation of L, void and contacts is still from the declaration, but the
  declaration is longer than n = 10's. A cell-algebra that generates those sets is a
  later run's job, and pretending otherwise would be the kind of "hardcoded row" the
  item was meant to remove.
- **`strip_needs_diamond` still fires three times.** `S(k, 0)` refuses because a strip
  with no diamonds cannot be a strip; the primitive now exists, but the Strip builder
  is not yet rewritten to consume a `DiamondField`. That is a wiring job, not a
  mathematical one, and it was not in scope.
- **The 173 is corrected, not defended.** See §3.
- The cage mode is exact and permanent but still bounded by `dens` and `bmax`; it
  reports what it enumerated, never "all".

## 6. Ledger

- `scripts/glm_wheels.py` — neutral `Claim` fields, `Witness.families`,
  `Domain.suite`, one `DecimalWitness`, `p_diamond_field`, `DIAMOND_FIELDS`;
  17 controls, one uniform report for three domains.
- `scripts/qsqrt2.py` — `cage_segment` (+ `_dec`, `_affine_project`, local `Refusal`),
  `lift_sentence` returns `pos`/`lo`; control 11; 11 controls.
- `scripts/grammar_induction.py` — `diamond1()`, `acceptance()`, `--diamond` ledger;
  control 3; 3 controls.
- `scripts/lattice_shells.py` — witnesses adapted to the neutral signature; lattice
  cells now fill `measure`/`invariant`.
- Float audit: **174 decision functions, 0 offenders** (`glm_wheels --audit`).
- Not touched: `submission.csv`, root `WHITEBOARD.md`, any row of the table.

Entries `50-ENGINE-CONTRACT-AND-DIAMOND.md`; records `31`–`50`.
