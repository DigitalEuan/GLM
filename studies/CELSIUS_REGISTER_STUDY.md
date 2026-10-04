# The Celsius register: the ITS-90 fixed points, and the scale table's first offset row

## Tier 0 — the coarse read

**Question.** Can the system hold a register whose readings are in degrees Celsius, carry them through the scale table's first offset row, and use them — ordered against the element register's kelvins and fed to the stepwise planner as levels — without answering anything wrongly?

**Verdict.** Yes: the ITS-90 fixed-point register holds its fourteen temperatures in degrees Celsius, the scale table's first offset row carries them onto the ITS-90 kelvin column exactly, and the ordering operation, the extremum operation and the stepwise planner read them with every declared case as declared and 0 wrong.

**Deciding figure.** 14 of 14 points carried onto the ITS-90 kelvin column; 10 of 10 ordering, 3 of 3 column and 9 of 9 planner cases as declared, 0 wrong; through `GLM.py --ask` the machine answered 0 of the 9 planner questions before the round and 6 after; with the offset dropped, 3 ordering verdicts flip and 6 of 6 planner answers are wrong; 6 of 6 chain scripts verified (25 of 25 steps aligned) with every mutation and every offset lie rejected; 8 of 8 marks met.

**Recomputed by.** `glm_universal.runtime.celsius_register_report.celsius_register_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

The owner asked for a register that holds a Celsius reading, because more
wheels, registers and junctions will be wanted along the recorded
development directions. It is the one item of the order of work that has
waited on a register rather than on code: round 1's item 1a
([`MEASURAND_REGISTER_STUDY.md`](MEASURAND_REGISTER_STUDY.md) §6) and
candidate 1's first half ([`SCALE_CONVERSION_STUDY.md`](SCALE_CONVERSION_STUDY.md)
§9). The scale table admits an affine conversion `value -> factor * value +
offset`, and `GLM.ScaleConversion.cmpQ_apply` is proved for any offset, but
every declared row has offset 0, and `quantity_units.scale_into_si` refuses an
offset row as `OFFSET_UNIT` with the line marked unreachable. Phase 86 reads a
*given* in degrees Celsius; no *register* held one.

## 1. The register

The fourteen fixed points of the International Temperature Scale of 1990
that have an assigned temperature: the triple points of equilibrium hydrogen,
neon, oxygen, argon, mercury and water, the melting point of gallium, and the
freezing points of indium, tin, zinc, aluminium, silver, gold and copper. The
helium and hydrogen vapour-pressure points are temperature ranges defined by
a vapour-pressure relation, not points, and are not held.

Why this register: its values are *assigned* (ITS-90 Table 1), so nothing in
it is a measurement this system could get wrong, and they are stated there in
both kelvin and degrees Celsius, so the offset row can be checked against a
column the register does not hold. The register holds the Celsius column
only, `temperature_C`: the kelvin value is what the offset row must derive.
And it overlaps the element register — thirteen of the fourteen substances are
elements whose melting point the element register holds in kelvin — so for
the first time a comparison across registers needs an offset.

## 2. Declarations — written before any code of the round

The corpus is [`evaluation/celsius_register_cases.py`](../overlay/glm_universal/evaluation/celsius_register_cases.py):
the register (14 rows), 10 ordering cases, 3 column cases and 9 planner
questions, with expected verdicts worked by hand in exact fractions.

| mark | what it requires |
|---|---|
| C1 | the register: 14 rows, every reading an exact rational; the offset row carries every Celsius reading onto exactly the ITS-90 T90 in kelvin that the corpus states beside it; every point above absolute zero; strictly increasing in the listed order |
| C2 | every ordering case as declared, 0 wrong |
| C3 | every column case as declared |
| C4 | every planner case as declared, 0 wrong |
| C5 | the controls: with the offset dropped (a Celsius reading taken as kelvins) the ordering verdicts of `o03` and `o04` flip, and each of the six answered planner cases is answered wrongly; with the register absent, none of the nine planner questions is answered |
| C6 | nothing earlier moves: the scale table's 12 declared questions, the ordering and extremum operations' declared sets, the measurand register's 30 questions and Phase 86's corpus as they were |
| C7 | every answered planner chain's column-3 script verifies in a fresh interpreter, and every mutation of each is rejected |
| C8 | the facts the round rests on proved in Lean, without `sorry` |

One reading is reported and not scored, because it was looked at while the
register was being chosen: the agreement, point by point, between the
ITS-90 assigned temperatures carried into kelvin and the element register's
melting points.

## 3. What was built

* [`data_objects/fixed_points.py`](../overlay/glm_universal/data_objects/fixed_points.py):
  the register — 14 rows keyed by the point (`"zinc freezing point"`), each
  with the substance, the kind of point and `temperature_C`, an exact
  rational parsed from the decimal ITS-90 prints. No row carries a `name` or
  `symbol`, so no row answers to `zinc`: the element register keeps the
  element and this register keeps the point. A switch `ACTIVE` removes it
  from the field surface for the register-absent control.
* In [`runtime/fields.py`](../overlay/glm_universal/runtime/fields.py): the
  field surface's third source table, `fixed_point`.
* In [`reasoning/scale_conversion.py`](../overlay/glm_universal/reasoning/scale_conversion.py):
  the row `fixed_point:temperature_C`, quantity `temperature`, unit `K`,
  factor `1`, offset `CELSIUS_ZERO_IN_K = 273.15`, sourced to the SI
  Brochure; the switch `OFFSETS` (off: the offset dropped, the control);
  `carry_text`, which names the offset in an answer.
* In `reasoning/coordinate_order.py`: an ordering across an offset row names
  the two carried values (`... x1 + 5463/20 ..., which carry the two readings
  to 6829/25 (= 273.16) and 5858/25 (= 234.32) K`), because the raw readings
  alone (`0.01` against `234.32`) do not show the order.
* In `runtime/quantity_units.py`: `scale_into_si_affine`, the one reader of a
  register scale that may carry an offset. `scale_into_si`, which takes a
  factor alone, now refuses an offset row `OFFSET_UNIT` with the reason
  (before, the line was marked unreachable).
* In `runtime/stepwise.py`: a register value on an offset scale is read as a
  level, `value * factor + offset`, and its chain step records both numbers;
  in `reasoning/stepwise_script.py` the column-3 script recomputes that step
  from the declared row (`scale_affine`).
* In `runtime/measurand_register.py`: the register's measurand row
  (`ITS-90 fixed-point temperature`, a thermodynamic temperature, read by name
  as `temperature`) and an `offset` field on every measurand row (zero for
  the nine earlier ones).
* In `runtime/semantic_plan.py`: the field words `temperature` and `celsius
  temperature` name `temperature_C` on a row that holds it (and nothing on a
  row that does not), so *the temperature of the zinc freezing point* is a
  register phrase.
* The measurement `runtime/celsius_register_report.py`, the command
  `tools celsius-register`, `tests/test_celsius_register.py` and
  `RequestProject/GLM/CelsiusRegister.lean`.

## 4. Results

Recomputed by `PYTHONPATH=. python3 -m glm_universal.tools celsius-register`.
Yes on every mark: all eight are met.

| mark | result |
|---|---|
| C1 | met: 14 rows, every reading exact and as declared; the offset row carries 14 of 14 onto the ITS-90 kelvin column; all above absolute zero; strictly increasing |
| C2 | met: 10 of 10 ordering cases as declared, 0 wrong (8 answered, 6 of them across the offset row; `o09` refused `different-scale`, `o10` `unreadable`) |
| C3 | met: 3 of 3 — the largest is the copper point and the smallest the hydrogen point (14 rows read); gathered by quantity over every table, `temperature` is still `incomplete` |
| C4 | met: 9 of 9 planner cases as declared, 0 wrong (6 answered, `p05` and `p06` refused `LEVEL_AS_DIFFERENCE`, `p08` refused `UNKNOWN_STEP`); through `GLM.py --ask` the machine answered 0 of the 9 before and 6 after |
| C5 | met: with the offset dropped the verdicts of `o02`, `o03` and `o04` flip (two declared, `o02` as well), and the six answered planner cases are all answered wrongly (`p01` as 273160000 where the answer is 10000; `p07` as a negative entropy); with the register absent none of the 9 is answered |
| C6 | met: the scale table's 12 of 12 declared questions, the ordering operation's 7 of 7 and the extremum operation's 8 of 8, the measurand register's 30 of 30 and Phase 86's 36 of 36, as before |
| C7 | met: 6 of 6 chain scripts verified, 25 of 25 steps aligned; every one of the 36 mutations rejected, and the round's own lie — the offset conversion with its offset set to 0 and every column re-rendered to agree — rejected in 6 of 6 |
| C8 | met: `RequestProject/GLM/CelsiusRegister.lean`, no `sorry`, standard axioms only |

Two answers worth reading in full. *Given the temperature of the water
triple point and energy = 2731600, what is the entropy* is `10000`, by a
chain that reads `fixed_point[water triple point].temperature_C = 1/100`,
carries it `s1 * 1 + 5463/20 [fixed_point:temperature_C -> SI, level] =
6829/25` (273.16 K) and divides on wheel W8; with the offset dropped the
same chain says 273160000. *Order melting_point_K of aluminum and
temperature_C of aluminium freezing point* is `lt`, by an exact `9/250` K:
933.437 K against 933.473 K.

The typed planner's stored reading of the whole evaluation set was re-taken
after the register went in (`tools plans --write`): no plan moved, only the
digest of the code it was taken over.

The comparability census of the measurand register now reads 8 of 8 related
pairs of one kind, 0 withdrawn, 10 of 10 scales registered (it read 6, 6 and
9 before the row).

**The agreement between the two registers** (reported, not scored: it was
looked at while the register was chosen). Of the thirteen fixed points whose
substance is an element, 10 lie within 0.005 K of the element register's
melting point — inside the rounding of a value given to 0.01 K. Three do not:

| point | ITS-90, carried | element register | gap |
|---|---|---|---|
| hydrogen triple point | 13.8033 K | 13.81 K | +0.0067 K |
| argon triple point | 83.8058 K | 83.8 K | −0.0058 K |
| aluminium freezing point | 933.473 K | 933.437 K | −0.036 K |

The hydrogen value is the triple point as IPTS-68 assigned it (13.81 K), and
the argon value is given to 0.1 K, so both are a precision or an older scale.
The aluminium value is not: `933.437` and `933.473` differ by a transposition
of the last two digits, and 0.036 K is seven times the rounding of a
three-decimal value. The element register is left as it was — it is a frozen
ingest of its source, and amending it is the owner's decision — and
`GLM.CelsiusRegister.aluminium_gap` states the gap.

## 5. What this moved

**Derive** — a register value in degrees Celsius now feeds derivations (an
entropy from an ITS-90 point), and two registers on two temperature scales
are ordered against each other. **Refuse** — a Celsius level fed to a law
that reads a difference is refused `LEVEL_AS_DIFFERENCE` as a kelvin level is,
and a reader that takes a factor alone refuses an offset row by name rather
than silently reading the level from zero. The offset-dropped control shows
what that refusal guards: three wrong verdicts and six wrong answers.

## 6. How the next register goes in

The owner expects more registers, wheels and junctions. This round is the
shape a register takes, and each touch point is one declaration:

1. **The register** — a module in `data_objects/` holding exact rows, with
   its source written beside them, and a `fields()` per row. Key the rows by
   what they are, and do not give a row a `name` or `symbol` that another
   register already answers to unless it is meant to be the same row.
2. **The field surface** — one `FieldTable` in `runtime/fields.py`.
3. **The scale table** — one row per numeric field in
   `reasoning/scale_conversion.py`: quantity, canonical unit, exact factor and
   offset, source. A field without a row is refused by every cross-scale
   operation, which is the intended default.
4. **The measurand register** — one row per scale in
   `runtime/measurand_register.py`: what the value *is*, its kind, and the
   wheel quantity it is read as by name, with the argument.
5. **The words** — a `FIELD_SYNONYMS` entry in `runtime/semantic_plan.py` when
   the field name is not how a question says it.
6. **The declarations and the proof** — a cases file in `evaluation/`, the
   marks in a study, then a report, a `tools` command, a test file and a Lean
   file for the facts the round rests on.

A **wheel** (a formula family) is a `WHEELS` entry in
`engineering/wheels.py`, and a **junction** (which wheel quantities are one
quantity, and which are related only by a conversion) is an entry of
`JUNCTIONS` in `engineering/union.py`, with a conversion law in
`runtime/measurand_register.py` when the relation is not an identity.

## 7. What this leaves

* **Fahrenheit and other offset scales in a register.** The offset row is a
  declaration like any other; a register in degrees Fahrenheit would take
  factor 5/9 and offset 45967/180, which
  `GLM.MeasurandKinds.fahrenheit_kelvin` already states.
* **The element register's aluminium melting point**, 0.036 K from the ITS-90
  value — a question for the owner, not an amendment this round makes.
* **The ITS-90 vapour-pressure points** (helium 3–5 K, equilibrium hydrogen
  near 17 K and 20.3 K) are ranges defined by a relation, not points; a
  register of them would need a value with an interval, which the held
  precision of Phase 76 could carry.
* **A Celsius target.** The planner answers in kelvins or a declared unit; it
  does not yet *state* an answer in degrees Celsius (a level out through the
  offset). Phase 86's offset readings are the inverse that would be needed.
