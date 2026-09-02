# A coordinate for the name — attacking the resolution ceiling where it lives

*What `reasoning/name_coordinate.py`, `RequestProject/GLM/NameCoordinate.lean`
and `report names` are for, and what they measured.*

Every figure below is recomputed by the code that reports it. Run

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report names" --verify-tct
```

and the third column re-derives the whole study in a fresh interpreter and
checks it key by key (`VERIFIED True`).

---

## 1. The question this answers

[`ESCALATION_STUDY.md`](ESCALATION_STUDY.md) ran the five-layer stack on the
machine's own data — one carrier per named object of every shipped register,
1,040 in all — and found a hard stop:

| | |
|---|---|
| named entries | 1,040 |
| distinct carriers | 757 |
| entries sharing a carrier with another | **283** |
| collision classes | 104 |
| classes crossing a register boundary | 0 |
| largest class | 78 dimensionless physics quantities |

No layer can separate those 283, and the reason is structural rather than a
defect: a layer's view is a function of the carrier, and the carrier is the
same. `GLM.Info.entryResolution_le_distinct` is that as a theorem. The study
ended by naming the cause — *what is missing is a coordinate for the name, not
a finer layer* — and stopped there.

That diagnosis is a claim about coordinates, and it was untested. Supplying
the coordinate and *measuring* what it buys is a different question from
asserting that it would help, and the difference is the whole content of this
round. The register-scale ceiling is the sharpest statement the project has
about where meaning runs out; growing the semantic register while it stands
would mean adding entries that provably cannot be told apart from ones already
there. So the ceiling is attacked first, and the bulk waits on the result.

## 2. The admission rule, applied to a coordinate

The rule the project applies before admitting any new data is that **every
coordinate must be computable from the entry, exactly, with no float** —
nothing stored beside the entry. A name coordinate has to pass the same test,
and the one used here does:

```python
def name_code(name: str) -> int:
    return int.from_bytes(b"\x01" + name.encode("utf-8"), "big")
```

The UTF-8 bytes of the name behind a leading `0x01`, read as a big-endian
integer. Integer arithmetic, no hash library, no float, and nothing consulted
but the entry's own name. The leading byte puts a name of `L` bytes in
`[256**L, 2·256**L)`, so names of different lengths land in disjoint bands and
names of the same length differ in some byte: the map is injective. That is an
argument, so the report also *measures* it — 1,019 distinct codes for 1,019
distinct names on the shipped corpus.

Two reductions of that integer to `b` bits are studied, both still exact:

| scheme | definition | what it keeps |
|---|---|---|
| `low_bits` | `code mod 2**b` | the tail of the name |
| `prime_mod` | `code mod p`, `p` the largest prime below `2**b` | the whole name, mixed |

## 3. The headline is the least interesting number

Read an entry as the pair `(carrier, code)` with the exact code:

| | before | after |
|---|---|---|
| entries resolved | 757 | **1,040** |
| unreachable | 283 | **0** |
| recovered | — | **283** |

and from the *coarsest* layer in the stack, not the finest:

| | entries resolved |
|---|---|
| 24-bit substrate alone | 415 |
| 24-bit substrate with the name beside it | **1,040** |

Neither number is a discovery. `GLM.Info.namedResolution_of_injective` proves
that an injective coordinate resolves every entry of a register whatever layer
it sits on, so 1,040 was forced before it was computed. Its worth is that it
fixes what the coordinate *is*: an **address**, in the sense of directive D3,
and not a measurement. Nothing about any quantity's meaning has been added.

## 4. The measurement is the sweep

Reduce the code to `b` bits and the ceiling comes back — and only inside the
collision classes, because two entries with different carriers are already
separated and a name collision between them costs nothing.

| bits | `prime_mod` unreachable | `low_bits` unreachable |
|---|---|---|
| 0 | 283 | 283 |
| 4 | 96 | 177 |
| 7 | 20 | 173 |
| 8 | 10 | 173 |
| 10 | 3 | 152 |
| 12 | **1** | 148 |
| 14 | 2 | 146 |
| 16 | **0** | 146 |
| 20 | 0 | 138 |
| 24 | 0 | 138 |

Three things in that table are worth more than the zero above it.

**The reduction is a choice, and it is a measured one.** Same name, same
width, same exactness — only the arithmetic differs, and `low_bits` never
clears the ceiling at any width. It saturates at 138 unreachable, because the
corpus is full of suffix families (`abbe_dispersion_number`,
`reynolds_number`, `prandtl_number`, …) that agree in their last bytes however
many of those bytes are kept. A coordinate can be exact, computed from the
entry, and still be the wrong coordinate.

**The sweep is not monotone.** 12 bits leaves one entry unreachable and 14
leaves two. Nothing is wrong: the modulus is a different prime at each width,
so a wider code is not a refinement of a narrower one. Reporting the
non-monotonicity is cheaper than explaining it away later.

**There is a floor, and it is a theorem.** A class of 78 entries at one
carrier cannot be separated by fewer than 78 codes — `GLM.Info.card_le_of_codeInjOn`
— so at least ⌈log₂ 78⌉ = **7** bits are necessary whatever the reduction
does. 16 were sufficient. The gap between 7 and 16 is a fact about this
corpus, not about the bound; `GLM.Info.namedResolution_le_mul` is the general
form, that a coordinate taking at most `m` values multiplies a layer's
resolution by at most `m`.

## 5. The control decides what is doing the work

A coordinate is not informative merely by being exact. Three other quantities
computed from the entry, by the same rule, measured the same way:

| coordinate | codes used | recovered of 283 |
|---|---|---|
| constant | 1 | **0** |
| register label | 6 | **0** |
| first letter | 48 | 174 |
| name length | 32 | 177 |
| **exact name** | 1,019 | **283** |

The register label is the control that matters, and it recovers nothing at
all. That is not an accident of this data either: all 104 collision classes
lie inside a single register, so the register coordinate is constant on every
class it would have to split, and `GLM.Info.namedResolution_eq_of_constant_on_classes`
proves that a coordinate of that shape leaves the resolution exactly where it
found it.

The first letter and the length are the interesting controls, because they
*do* recover part — 174 and 177 of 283, from 48 and 32 values respectively.
Their existence is what stops the finding being "one more coordinate helps".
The name recovers all 283 with 1,019 values; a cheap fragment of the name
recovers about three fifths of them; and a coordinate that is not the name at
all recovers none.

## 6. What is checked, and what would be vacuous to check

Pairing the carrier with a code can split a class and can never merge two, so
the named reading refines the layer's — `GLM.Info.namedLayer_refines_entryLayer`,
and `GLM.Info.entryResolution_le_namedResolution` for the consequence. Counting
merges in the instrument would be counting a structural zero, because the
carrier is literally part of the key, and a zero that cannot be anything else
is worth nothing.

What is counted instead is the admission rule itself. Every coordinate is
evaluated twice, the second time with the entries visited in the opposite
order, and a disagreement means the coordinate read something other than its
entry — a counter, a cursor, a position in a file. All 25 rows of this study
(two sweeps of ten widths, four controls, the exact code) are checked, and all
25 pass. `test_name_coordinate.py` also runs a deliberately bad coordinate
that reads the traversal instead of the entry, and confirms the counter
reports it, so the zero is not vacuous.

## 7. What this changes, and what it does not

**Changed.** The ceiling is no longer a limit of the design; it is a limit of
a choice, and the choice is now measured. The registers can grow, and the
question "can two new entries be told apart?" now has an answer that does not
depend on their carriers being different.

**Not changed.** The coordinate is an address. It separates `reynolds_number`
from `prandtl_number` and says nothing whatever about how they differ. An
entry that is *only* distinguished by its name is still an entry the machine
has nothing to say about, and the honest reading of §3 is that the 283 were
never a shortage of resolution — they were 283 places where the registers hold
a label and no measurement. Lifting the ceiling makes them addressable; it
does not make them meaningful. That work is the measure-word layer's, and it
is measured separately in [`RELATIVE_MEASURE_STUDY.md`](RELATIVE_MEASURE_STUDY.md).

## 8. Surface and counts

| | |
|---|---|
| module | `overlay/glm_universal/reasoning/name_coordinate.py` |
| report subject | `report names` (aliases: `name`, `name coordinate`, `naming`) |
| column-3 template | `report_names` |
| tests | `overlay/glm_universal/tests/test_name_coordinate.py`, 30 cases |
| evaluation case | `report-names` |
| Lean | `RequestProject/GLM/NameCoordinate.lean` — 3 definitions, 8 theorems, no `sorry` |
