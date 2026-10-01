# Measurands: kinds of quantity, temperature levels and differences, and the SI's defining constants in the stepwise planner

## Tier 0 — the coarse read

**Question.** Can the stepwise planner tell apart quantities that share a dimension but not a kind — a torque from an energy, a frequency from an angular velocity, a temperature level from a temperature difference — and supply the SI's exactly defined constants where the givens alone derive nothing, without answering anything wrongly?

**Verdict.** Yes: the stepwise planner now refuses `KIND_MISMATCH` where a unit has the right dimension but the wrong kind, reads a temperature in degrees Celsius or Fahrenheit as a level or as a difference by the quantity it feeds and refuses the three conflations by name, and supplies the Planck constant and the speed of light when the givens alone derive nothing, with every declared case as declared and 0 wrong.

**Deciding figure.** 31 of 31 declared questions as declared (10 kind, 15 temperature, 6 constant), 0 wrong; the kinds-off control answers 5 of the 5 declared `KIND_MISMATCH` refusals, each with a number; 5 of 5 amended earlier verdicts as amended; rounds one to four held; 17 of 17 chain scripts verified (80 of 80 steps aligned) with every mutation rejected.

**Recomputed by.** `glm_universal.runtime.measurand_report.measurand_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Candidate O5 of [`STATUS.md`](../STATUS.md) §3.4 (named by Phase 72, and
candidate K2 / the second half of candidate 1 before it): *measurands rather
than units — the unit check compares dimensions, so it cannot tell a torque
from an energy*. The unit check of
[`STEPWISE_TWO_STUDY.md`](STEPWISE_TWO_STUDY.md) compares the seven SI base
exponents. That is necessary and not sufficient: the SI Brochure (9th
edition, 2019, §2.3.4 and Table 4) says a unit does not identify a quantity,
and restricts some special unit names to one kind of quantity — the hertz
only for periodic frequency (not angular velocity, which is in radians per
second), the newton metre for torque (not the joule). A temperature in
degrees Celsius is a further case: a Celsius *level* is `T/K − 273.15`, a
Celsius *interval* equals a kelvin. Treating a level as a difference is only
right when the other end is absolute zero, which no question says.

This is established metrology, not something the GLM discovers: the round
writes the Brochure's rules down as declarations and holds the planner to
them.

## 1. The objects

Declared in [`runtime/measurands.py`](../overlay/glm_universal/runtime/measurands.py);
exact rational throughout (D7).

* **Unit kinds.** A unit name may carry a kind; a quantity of a different
  kind with the same dimension may not take it (`UNIT_FORBIDS`): the hertz
  is not an angular velocity, the radian per second is not a frequency, the
  joule and the electronvolt are not a torque, the newton metre is not an
  energy. Given in one, asked in the other: `KIND_MISMATCH`.
* **Slot kinds.** A wheel law may read a temperature as a **difference** or
  as a **level** (`SLOT_KINDS`): `energy = mass * specific_heat_capacity *
  temperature` reads a difference; `entropy = energy / temperature` reads a
  level. Names that say *difference* — *temperature change*, *temperature
  rise*, *temperature difference* — are differences
  (`DIFFERENCE_NAMES`); a register temperature (a melting or boiling point)
  is a level.
* **Offset readings.** Degrees Celsius and Fahrenheit are read as a level
  (`t + 273.15`, `(t + 459.67)·5/9`) or as a difference (`×1`, `×5/9`)
  according to what the quantity is (`OFFSET_READINGS`). A level below 0 K
  is refused `BELOW_ABSOLUTE_ZERO`.
* **The three conflations.** A level fed to a difference slot:
  `LEVEL_AS_DIFFERENCE`. A difference fed to a level slot:
  `DIFFERENCE_AS_LEVEL`. One bare temperature read by one law as a
  difference and by another as a level in the same chain: `KIND_CONFLATION`.
* **Defined constants.** The SI's exact defining constants `h =
  6.62607015e-34 J s` and `c = 299792458 m/s` (`DEFINED_CONSTANTS`) are
  offered to the planner **only** when every attempt with the givens alone
  fails with `NO_DERIVATION`; each appears in the chain as a `constant` step
  with its exact value in column 1.

## 2. Declarations — written before any code of the round

The corpus is
[`evaluation/measurand_cases.py`](../overlay/glm_universal/evaluation/measurand_cases.py),
every expected answer worked from the Brochure: 10 kind questions (5 refused
`KIND_MISMATCH`, 5 answered in the unit of the right kind), 15 temperature
questions (8 answered, 7 refused by one of the new names), 6 constant
questions (4 answered, 2 refused). `AMENDED` lists the 5 earlier declared
cases whose verdict the round changes, with reasons (§4).

| mark | claim | measured by |
|---|---|---|
| **M1** | every kind case gets its declared verdict; 0 wrong | `kinds` |
| **M2** | every temperature case gets its declared verdict; 0 wrong | `temperatures` |
| **M3** | every constant case gets its declared verdict; 0 wrong; a constant is never used where the givens derive the goal | `constants` |
| **M4** | control: with the kinds switched off (the dimension check alone), at least 4 of the 5 `KIND_MISMATCH` refusals are answered with a number | `control` |
| **M5** | every answered chain's column-3 script prints `VERIFIED True` in a fresh `python3 -I`, one `ALIGNED` line per step, every applicable mutation rejected | `scripts` |
| **M6** | non-interference: rounds one to four keep every verdict except the 5 declared amendments, which take the amended verdict with the kinds on and the original with them off; on the router's declared sets no declared refusal becomes an answer | `amendments`, `interference` |
| **M7** | `RequestProject/GLM/MeasurandKinds.lean` builds with no `sorry` and standard axioms, and proves the offset and kind facts the refusals rest on | Lean |

## 3. What was built

* [`runtime/measurands.py`](../overlay/glm_universal/runtime/measurands.py) —
  the declarations of §1, behind the switch `ACTIVE`.
* [`runtime/stepwise.py`](../overlay/glm_universal/runtime/stepwise.py) —
  `_kind_check` and `_kind_failure`; the offset reading and register kinds in
  `goal_two`; the kind filter and the constants fallback in `_goal_core`;
  the five new refusals.
* [`reasoning/stepwise_script.py`](../overlay/glm_universal/reasoning/stepwise_script.py)
  — a `constant` step, and a unit step with an offset, in both columns, the
  readers and the generated script; [`reasoning/held_precision.py`](../overlay/glm_universal/reasoning/held_precision.py)
  reads a constant as a leaf.
* [`runtime/measurand_report.py`](../overlay/glm_universal/runtime/measurand_report.py)
  — the measurement and the kinds-off control; `tools measurands`;
  `tests/test_measurands.py`.

## 4. Results

`python -m glm_universal.tools measurands` recomputes everything below.

**Summary.** Yes: the stepwise planner now refuses `KIND_MISMATCH` where a unit has the right dimension but the wrong kind, reads a temperature in degrees Celsius or Fahrenheit as a level or as a difference by the quantity it feeds and refuses the three conflations by name, and supplies the Planck constant and the speed of light when the givens alone derive nothing, with every declared case as declared and 0 wrong. In all, 31 of 31 declared questions as declared.

| mark | result |
|---|---|
| M1 | **met** — 10 of 10 as declared, 0 wrong |
| M2 | **met** — 15 of 15 as declared, 0 wrong |
| M3 | **met** — 6 of 6 as declared, 0 wrong |
| M4 | **met** — kinds off answers 5 of the 5 `KIND_MISMATCH` refusals (k01 as 100, k02 as 100, k03 as 10, k04 as 2, k08 as 5); 8 of the round's refusals answered in all |
| M5 | **met** — 17 of 17 verified, 80 of 80 steps aligned; value-lie, column-1, reorder, answer and read-lie caught 17 of 17, unit-lie 16 of 16 |
| M6 | **met** — 5 of 5 amendments; rounds one, two, three and four held; 11 of 273 router questions read by the planner, 0 turned into answers |
| M7 | **met** — builds, no `sorry`, standard axioms |

7 of 7 marks met.

**Through the whole machine** (`GLM.py --ask`, before and after): kind
questions 10 answered before, 5 now — the five that are gone are the five
wrong-kind answers; temperature questions 5 before, 8 now; constant
questions 0 before, 4 now.

**The amendments.** Five earlier declared verdicts of
[`STEPWISE_TWO_STUDY.md`](STEPWISE_TWO_STUDY.md) change to
`LEVEL_AS_DIFFERENCE`: u13 (25 °C into the heat law, which round two
refused as an offset unit), and g01, g03, g11, m02, which answered by feeding
a register melting or boiling point to `energy = mass · specific heat ·
temperature`. That law reads a temperature *difference*; a melting point is
a *level*, a difference only from absolute zero. g03 and m02 were worse:
their answer 900 was the entropy of heating from absolute zero at constant
specific heat, a quantity that diverges. They were wrong answers the
dimension check could not see.

**A consequence for held precision.** Both witnesses of mark H3 of
[`HELD_PRECISION_STUDY.md`](HELD_PRECISION_STUDY.md) — the chain whose held
value cancels and the chain where step-by-step intervals are wider — were
g03 and m02. They are now refused, so H3 is no longer met (§4 of that
study).

**In Lean.** `offset_difference_free`: a difference of two offset readings
does not depend on the offset. `level_as_difference_depends_on_zero`:
reading a level as a difference changes `m·c·T` by any non-zero choice of
zero. `difference_law_zero_free`: the difference law is the same for every
zero. `fahrenheit_kelvin`: the Fahrenheit level equals the Celsius level of
the converted reading. `absolute_zero_celsius`: −273.15 °C is 0 K, and
below it is negative. `hertz_as_angular_velocity_wrong`: reading `f` hertz
as `f` radians per second is wrong by the factor `2π` for every non-zero
`f`.

## 5. What this round moved

Against the standing target: **fewer wrong answers**. Five answers the
machine gave were wrong in kind, and five more (the amendments) were wrong
in the physics; each is now a named refusal, and the questions that were
refused because a constant was missing are answered exactly.

## 6. What this leaves

* **Measurands by name into the wheels** — the other half of O5: a declared
  map from register measurands to wheel quantities (the register's *atomic
  radius* as a *length* feeding a *wavelength*). Not built.
* **Conversions with an efficiency or a sign** (heat engines, a signed
  temperature change): not declared.
* **The elementary charge** is declared in the corpus text but not yet
  offered as a constant; no wheel reads a charge.
* **Kinds beyond the Brochure's named restrictions** (a length as a radius
  versus a wavelength) would need the map above.
