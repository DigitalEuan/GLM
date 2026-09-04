# The archive, read a second time

*The first pass over `source_material/GLM-main.zip` retrieved eleven results
([`SOURCE_SALVAGE_AUDIT.md`](SOURCE_SALVAGE_AUDIT.md)) and left two questions
open ([`ARCHIVE_DEEP_DIVE_STUDY.md`](ARCHIVE_DEEP_DIVE_STUDY.md)). Read a second
time, with the first pass's Lean development in hand, **eight more results came
back**. This is their runtime half: each section recomputes what its Lean file
proves, from the substrate this package already carries.*

Module: [`overlay/glm_universal/reasoning/salvage_second.py`](../overlay/glm_universal/reasoning/salvage_second.py)
— one call, `second_pass_report()`.
Tests: `overlay/glm_universal/tests/test_salvage_second.py` — 39 test methods.
Arithmetic: exact `int` and `Fraction` (D7). `π` enters only as a rational
enclosure computed from Machin's formula, never as a float.

```bash
cd overlay
PYTHONPATH=. python3 -c "from glm_universal.reasoning.salvage_second import second_pass_report as r; print(r())"
```

| Lean file | archive source | what it settles |
|---|---|---|
| `Cube/Surface.lean` | `data_object/mog_cube_1` | the cube's surface **is** the MOG grid, and the code on it factors into three layers |
| `ReadQuantum.lean` | `data_object/FirstPrinciples` | the read quantum as an operator: `Y` is a stipulation, not an extremum |
| `GrayJump.lean` | `leech_lattice` | the shortcut's jump norm is one instruction, and its "100 % even" is a parity law |
| `GridTension.lean` | `arc_agi_15` | the grid metrics as exact bounds, and what they cannot separate |
| `ConditionalInduction.lean` | `arc_agi_15` | the conditional lobe: sound, incomplete, and committed to a tie-break |
| `ModeAlgebra.lean` | `GMHGL/ubp_eml_alu_sovereign.py` | Kracht signs: what the argmax collapse costs, and a mode that can never fire |
| `Cube/Stabiliser.lean` | `data_object/mog_cube_1` | which of the cube's 48 surface symmetries are free |
| `Golay/CubeMirror.lean` | `data_object/mog_cube_1` | and why no placement frees a diagonal mirror |

---

## 1. The cube's surface is the MOG grid

Six faces of four cells is 24 cells, and the Golay code carried on them is the
substrate's own: weight enumerator `1 + 759x⁸ + 2576x¹² + 759x¹⁶ + x²⁴`,
minimum non-zero weight 8, all 4,096 codewords accounted for.

The code **factors into three layers**: 64 hexacode words (minimum distance 4),
a free top row of 2¹⁸ = 262,144 grids per hexacode word, and a parity factor of
64. Every grid the parametrisation produces is a codeword.

What this buys is an error statement about faces rather than about bits:

* **one bad face heals** — no non-zero codeword is supported on a single face
  (`single_face_codewords == 0`), so a single corrupt face is always correctable;
* **two do not** — for all 15 pairs of faces there *are* codewords supported on
  the pair, each of weight 8, so two corrupt faces can be a legal word.

A second presentation of the hexacode, taken from the archive's own generator,
shares only 4 words with this one and yet agrees on every invariant — same word
count, same minimum distance, same enumerator. The layer is a property of the
code, not of the presentation.

## 2. The read quantum is a stipulation

Written as an operator, `readCost d t = 1/(t + d/t)`. The archive fixes
`Y = 1/(π + 2/π)` and treats it as an extremum. It is not: at `d = 2` the
maximum of the operator sits at `t = √2`, where the cost squared is exactly
`1/8`, and `Y² < 1/8` strictly. `π` is a choice of loop-check, not a maximiser.

The exact brackets, computed from Machin's formula:

| quantity | bracket |
|---|---|
| `Q` | `[38967543/10⁸, 4870943/1.25·10⁷]` |
| `Y` | `[26467543/10⁸, 3308443/1.25·10⁷]` |

The package's own stored `Y` lies inside its bracket. The cost has **no positive
lower bound** — `readCost` at `t = 10, 100, 1000` is `1/10, 1/100, 1/1000` — so
"the cost of a read" can be driven below any positive number by raising the
loop-check, which is what makes it a stipulation.

On 24 signed coordinates only two of the four coherence regimes can occur,
`OnBit` and `Coherent`: the octad tax interval is
`[38967543/1.25·10⁷, 4870943/1562500]` and the maximum tax on 24 signed
coordinates is `[116902629/1.25·10⁷, 14612829/1562500]`, both below the budget
that would reach the other two. The octad is coherent rather than on-bit, and
the boundary sits between `6Q` and `7Q`.

## 3. The Leech shortcut's jump norm

The archive's "Leech lattice shortcut" is a walk. It is one machine instruction:

```
d2(a, b) = popcount(gray(a xor b))
```

Checked over a sample of 64, the formula holds every time, and on a walk of 17
consecutive integers from 1000033 the norm is **1 at every step** — adjacent
integers are always at distance one, which is what the Gray code is for.

The archive's "100 % even" result is a parity law and not a fact about the
lattice: the parity of the jump norm is the parity of `a + b`. Over the sample
2,048 of the jump norms are odd, and the published directory values `8, 10, 12,
14` are even because the pairs behind them happen to have even sums.

## 4. The ARC grid metrics

Of the three metrics the ARC generation used, only the mass is arithmetic. The
other two are smooth functions of the cell count alone:

* the **tension** is below `10/N²` for every `N ≥ 7`, and the bound decays;
* the **circumradius** is the perimeter over `2π` to within `1/N`; the bracket
  width falls below `1/N` from `N = 7` — the smallest `N` with `2π/N ≤ 1`.

Both are computed against a rational enclosure of `π`, and `π² < 10` is proved
rather than assumed. A metric that depends only on the cell count ranks objects
by size and cannot separate two objects of the same size, which is exactly what
the generation needed it to do.

## 5. The conditional lobe

Over all 6,561 observations, with 8 descriptions and 6 conditions:

| property | value |
|---|---|
| unsound answers | **0** |
| gave up though a rule of its own family fits | **56** |
| ambiguous observations | 136 |
| answered anyway, from the order of its tests | **119** |

The survivor distribution is `0: 5193, 1: 1232, 2: 111, 3: 20, 4: 4, 5: 0, 6: 1`. So
the lobe is **sound** — it never returns a rule the data refutes — **incomplete**
on 56 observations, and **committed**: in 119 of the 136 ambiguous cases it
answers from the order in which its tests happen to run rather than from the
data. Soundness is the property worth keeping; the commitment is the one to
report, because it is invisible from the outside.

## 6. Mode algebra, and a mode that never fires

2,401 categories over 18 labels, two of them indefinite. The complaint the
archive records — that the argmax collapse loses information — is **exact for
one mode and empty for another**: the DEFINITION test reads only the argmax and
licenses all 614,656 category pairs, while the SVO verb slot does not, and
**1,185** licensed categories share their argmax with an unlicensed one. The
smallest witness is the pair `(0,0,2,3)` and `(0,0,0,1)`.

The dominance census is `NOUN 784, ADJECTIVE 644, VERB 532, OPERATOR 441`;
1,724 categories are subject-licensed and 1,717 verb-licensed, giving
5,103,226,192 licensed SVO triples. The fibres total `2²⁴` exactly. The
CONTRADICTION mode fires on **0** definite pairs: it can never fire, and the
PROPERTY role is unreachable.

## 7. Which cube symmetries are free

The cube's surface has 48 symmetries, 24 of them rotations. Under the canonical
placement of the code on the surface, **12** are free — the tetrahedral group —
and the quarter turn is a rotation that is *not* free.

A second placement, found by search, frees **all 24 rotations** while carrying
the same code: 4,096 codewords, minimum weight 8, the same enumerator. So the
canonical placement's 12 is a property of the placement, not of the code.

No placement frees a reflection: the second placement prices every one of them.

## 8. Why 24 is the ceiling: the mirror argument

The last result is the reason §7 stops at 24, and it is pure counting.

A diagonal mirror of the surface fixes 4 cells and transposes 10 pairs. It is an
involution and lies in `T_d`. An invariant five-set is therefore built from
fixed cells and whole pairs, and there are exactly **220** of them.

Each invariant five-set lies in exactly one octad — `S(5,8,24)` — and that octad
must be invariant too, since the mirror sends the octad containing a five-set to
the octad containing its image, which is the same five-set. So the 220 invariant
five-sets map into the invariant octads, and each invariant octad holds
**0, 6 or 12** of them: every fibre is a multiple of six.

But `220 = 6 × 36 + 4` is not a multiple of six. The map cannot exist, so **no
Golay code on the cube's surface is invariant under a diagonal mirror** — the
rotation group of order 24 is the ceiling, and the 48 is out of reach for a
reason, not by accident.

---

## 9. What the second pass changes

Three of the eight are corrections to first-pass readings, and they are the
reason a second pass was worth making:

1. `Y` is not an extremum. The first pass carried `Y` as *the* read quantum;
   the operator form shows it is one loop-check among many.
2. The Gray-jump "100 % even" is a parity law, not a lattice fact.
3. The cube's 12 free symmetries are a property of the placement; a different
   placement frees 24, and a counting argument shows 24 is the most any
   placement can free.

The other five add structure the first pass could not see without the Lean it
had by then built: the three-layer factorisation, the one-face/two-face error
statement, the lobe's commitment census, the mode algebra's collapse witnesses,
and the grid metrics' exact bounds.

---

## 10. Where this sits

* First pass: [`SOURCE_SALVAGE_AUDIT.md`](SOURCE_SALVAGE_AUDIT.md).
* The two open questions: [`ARCHIVE_DEEP_DIVE_STUDY.md`](ARCHIVE_DEEP_DIVE_STUDY.md).
* Lean half of the archive round: [`RETRIEVED_LEAN_STUDY.md`](RETRIEVED_LEAN_STUDY.md).
