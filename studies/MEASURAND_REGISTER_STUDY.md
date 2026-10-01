# The measurand register: register values read through what they measure, conversions through a stated efficiency, and the elementary charge

## Tier 0 — the coarse read

**Question.** Can the stepwise planner read a register value through the measurand it is — a first ionization energy as the energy of the photon that ionizes the atom — and carry a power across a conversion only through a stated efficiency, without answering anything wrongly?

**Verdict.** Yes: the stepwise planner now reads a register value through a declared register of measurands, carries a power across a motor, generator, pump or turbine only through a stated efficiency in (0, 1], and reads the elementary charge as an exact unit, with every declared case as declared and 0 wrong.

**Deciding figure.** 30 of 30 declared questions as declared (12 register, 14 conversion, 4 charge), 0 wrong; through `GLM.py --ask` the machine answered 2 of the 30 before the round and 18 after; the naive control answers 7 conversion cases, all 7 wrongly; 18 of 18 chain scripts verified (123 of 123 steps aligned) with every mutation rejected; 8 of 8 marks met.

**Recomputed by.** `glm_universal.runtime.measurand_register_report.measurand_register_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 1 of the order of work in [`ROADMAP_STUDY.md`](ROADMAP_STUDY.md): the
measurand register, which is candidate K2 of [`STATUS.md`](../STATUS.md) §3.4
(the junction table as a register of measurands, so a conversion through a
stated efficiency is a law), the remainder of O5 (a declared map from register
measurands to wheel quantities, and the elementary charge), and the second
half of candidate 1 (measurands rather than units, and which pairs are
comparable). Phase 86 ([`MEASURANDS_STUDY.md`](MEASURANDS_STUDY.md)) gave the
planner kinds of quantity on *units*; this round gives them to *register
values* and to *conversions*.

Three things the planner could not do before this round:

* A register value fed the wheels by the **unit** of its declared scale.
  The scale table holds a first ionization energy as a *molar energy*
  (electronvolts per atom carried into kilojoules per mole), so *given energy
  = the ionization energy of hydrogen* was refused `UNIT_MISMATCH`, and a
  bare *given the ionization energy of hydrogen* was refused because no wheel
  names a molar energy. What the value *is* — the least energy one photon must
  carry to ionize the free atom — was written nowhere.
* The junction table (Phase 66,
  [`CONNECTED_MACHINE_STUDY.md`](CONNECTED_MACHINE_STUDY.md) §2.1) keeps
  electrical and mechanical power apart, rightly: they are related by a
  conversion, not an identity. But with no conversion law, a motor question
  was simply refused.
* The elementary charge, exact since 2019, was not a unit the planner read.

## 1. The objects

* **Register measurands.** For each declared register scale, the measurand
  it holds: a name, a kind of quantity, the entity it is per, the exact
  reading into the coherent SI unit *per entity*, and the wheel quantity — and
  which wheel's copy of it — that the measurand is read as **by name** (when
  the question gives the register phrase bare). Argued, not looked up:
  * the first ionization energy and the electron affinity are energies per
    atom, read by name as the energy of a photon (wheel W10): the
    photoionization and photodetachment thresholds;
  * a melting or boiling point is a thermodynamic temperature (a level),
    read by name as `temperature`, as before;
  * an atomic or covalent radius is a length with no wheel quantity by name:
    a radius is not a wavelength, so a bare radius is refused, and *wavelength
    = the atomic radius of iron* is answered because the question makes the
    identification (both are of the kind *length*, ISO 80000-3);
  * the scales whose unit has no exact SI factor stay refused as before.
* **Conversion laws.** A named efficiency `eta`, `0 < eta <= 1`, relating the
  power out of a declared conversion to the power in, `P_out = eta * P_in`,
  across one of the junction table's declared non-identities: motor (W1
  electrical in, W4 shaft out), generator (W4 in, W1 out), pump (W4 in, the
  hydraulic power of the joined W5/W6 fluid column out), turbine (that
  hydraulic power in, W4 out). Given in a question as *motor efficiency =
  9/10* (or *90 percent*); it may also be asked for. An efficiency that is
  not in `(0, 1]`, stated or derived, is refused `EFFICIENCY_OUT_OF_RANGE`
  (above 1 the conversion would create energy); a bare *efficiency* that
  names no declared conversion is refused `EFFICIENCY_UNDECLARED`.
* **The elementary charge** as an exact unit of charge,
  `1.602176634e-19 C`.

## 2. Declarations — written before any code of the round

The corpus is [`evaluation/measurand_register_cases.py`](../overlay/glm_universal/evaluation/measurand_register_cases.py),
30 questions: 12 register, 14 conversion and 4 charge, with expected verdicts
worked by hand in exact fractions from the register's values, the SI's exact
defining constants, the wheels' axioms and the declared conversion laws.

| mark | what it requires |
|---|---|
| R1 | every register case as declared, 0 wrong |
| R2 | every conversion case as declared, 0 wrong |
| R3 | every charge case as declared, 0 wrong |
| R4 | the controls: the naive control (the conversion read as an identity, the efficiency dropped) answers at least 6 of the answered conversion cases, each wrongly; the unrestricted control (a register energy fed to every wheel's `energy`) answers the declared case `r09` that the measurand's restriction refuses |
| R5 | nothing earlier moves: Phase 86's corpus (kinds, temperatures, constants, amendments) and rounds one to four of the stepwise planner as they were |
| R6 | every answered chain's column-3 script verifies in a fresh interpreter, and every mutation of each is rejected |
| R7 | the comparability census: every pair of scales the unit table relates is a pair of one kind of quantity under the register, so the register withdraws no comparison the table licensed |
| R8 | the facts the round rests on proved in Lean, without `sorry` |

## 3. What was built

* [`runtime/measurand_register.py`](../overlay/glm_universal/runtime/measurand_register.py):
  the register of measurands (9 rows, one per declared register scale), the
  4 conversion laws `C1`–`C4`, the elementary charge and the percent as
  units, the comparability census, and the three switches the controls use
  (`ACTIVE`, `RESTRICT`, `NAIVE`).
* In [`runtime/stepwise.py`](../overlay/glm_universal/runtime/stepwise.py):
  `goal_two` reads an efficiency named in the question, refuses
  `EFFICIENCY_UNDECLARED` and `EFFICIENCY_OUT_OF_RANGE`, and brings only the
  named laws into scope (`_LAWS_IN_SCOPE`, empty for every earlier question);
  `_register_reading` reads a register value through its measurand where the
  register's per-entity reading differs from the unit table's; `_goal_core`
  restricts a measurand read by name to its declared wheels' copy.
* In `runtime/quantity_units.py`: the elementary charge and the percent read
  as units; an efficiency has dimension one.
* In `reasoning/stepwise_script.py`: a conversion law is a pseudo-wheel the
  column-3 script checks against the declaration, and a measurand reading is
  a conversion into SI the script recomputes from the register.
* The measurement `runtime/measurand_register_report.py`, the command
  `tools measurand-register`, `tests/test_measurand_register.py`, and
  `RequestProject/GLM/MeasurandRegister.lean`.

## 4. Results

Recomputed by `PYTHONPATH=. python3 -m glm_universal.tools measurand-register`.
Yes on every mark: all eight are met.

| mark | result |
|---|---|
| R1 | met: 12 of 12 register cases as declared, 0 wrong; through `GLM.py --ask` the machine answered 2 before the round and 7 after |
| R2 | met: 14 of 14 conversion cases as declared, 0 wrong; the machine answered 0 before and 8 after |
| R3 | met: 4 of 4 charge cases as declared, 0 wrong; the machine answered 0 before and 3 after |
| R4 | met: the naive control answers 7 conversion cases, all 7 wrongly (e01 as 23/5 where the answer is 207/50; e03, e04, e05, e12, e13, e14), and none rightly; the unrestricted control answers `r09`, feeding the ionization energy of hydrogen to the heat law as if it were heat given to 2 kg |
| R5 | met: Phase 86's corpus (kinds, temperatures, constants, the 5 amendments) and rounds one to four of the planner held |
| R6 | met: 18 of 18 chain scripts verified, 123 of 123 steps aligned; every mutation of each rejected |
| R7 | met: 6 of 6 pairs the unit table relates are pairs of one kind under the register; 0 withdrawn; 9 of 9 scales registered |
| R8 | met: `RequestProject/GLM/MeasurandRegister.lean`, no `sorry`, standard axioms only |

In all, through `GLM.py --ask` the machine answered 2 of the 30 before the
round and 18 after, and carries the stated efficiency, the measurand and the
exact unit through every answered chain.

Two answers worth reading in full. *Given the ionization energy of hydrogen
and wave speed = 299792458, what is the wavelength in nanometres* is answered
as `6621486190496429/72621326230440`, about 91.18 nm — the Lyman limit — by
a chain that reads 13.598 eV per atom, supplies the exact Planck constant,
derives the threshold frequency on wheel W10, crosses the W9/W10 junction on
frequency, and carries the register's stated precision to the answer. *Given
voltage = 230 volts, current = 2 amperes, motor efficiency = 9/10 and angular
velocity = 100, what is the torque* is `207/50`, through `C1: shaft_power =
motor_efficiency * electrical_power`; the naive identity says `23/5`.

The declared case `e02` (*given torque, angular velocity and generator
efficiency, what is the power*) is answered `AMBIGUOUS` as declared: the
shaft power and the electrical power are both *power*, and the question does
not say which it asks for.

## 5. What this round moved

**Derive** — register values now feed derivations they could not feed before
(a photon threshold from an ionization energy or an electron affinity), and a
conversion through a stated efficiency is a law rather than a refusal.
**Refuse** — an efficiency outside (0, 1], stated or derived, and an
efficiency that names no declared conversion, are refused by name; a register
measurand read by name is kept to the wheel it is.

## 6. What this leaves

* **The scale table's offset row** (candidate 1's first half) is still not
  shipped: no register holds a reading in degrees Celsius, so there is no row
  to declare. Phase 86 reads offsets for givens; the register would take an
  offset row the day such a register arrives.
* **More measurands by name.** The bond dissociation energy is declared
  (a molar energy, no wheel by name) but the planner has no phrase that
  reaches it; a photodissociation threshold per molecule would follow from the
  same argument as the two photon thresholds.
* **More conversions**: heat engines (a conversion with a sign and a Carnot
  bound), electrical heating into wheel W8 (which has no power), and
  conversions chained in one question (proved to compose,
  `conversion_compose`, and not yet exercised by a declared case).
* **Typed operators** (candidate F) — real, reactive and apparent power as
  three measurands of one dimension — are the next round on this track
  ([`ROADMAP_STUDY.md`](ROADMAP_STUDY.md) §4).
