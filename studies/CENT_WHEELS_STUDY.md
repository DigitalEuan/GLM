# The cent compiler's wheels — which of the 31 supplied wheels are sound, and do the sound ones let the GLM answer derivability questions in new domains, with nothing wrong?

## Tier 0 — the coarse read

**Question.** Of the 31 formula wheels supplied with `cent_compiler_v12`, which are sound — every axiom dimensionally balanced on its own table, every case's stated derivability equal to exact span membership, every negative control refused — and do the sound ones, absorbed, let the GLM's exact engine answer derivability questions in the new domains that it refuses without them, with no answer wrong?

**Verdict.** Yes, with one pre-registered mark not met. After rule R, 15 of the 16 new wheels are sound and pass the absorption rule (W35 loses both axioms and does not), and with them the GLM's exact engine licenses 63 of the 64 law questions of the pre-registered battery and 0 of its 51 not-a-law questions, where the fifteen wheels alone license 1 law; every negative control is refused and every verdict on the 15 has a Lean proof written, whose build is the owner's to confirm; until it is, the 15 wheels are in the package provisionally, and say so. Mark E2 is not met: besides its two additions, the supplied W4 omits the repository's case W4-M1.

**Deciding figure.** 63 of 64 laws licensed and 0 of 51 not-a-laws licensed with the cent wheels (bars: at least 56, at most 0), against 1 of 64 laws with the fifteen wheels alone (bar: at most 4); 26 of 26 supplied negative controls refused; 10 supplied axioms failing at SI7, 0 absorbed.

**Recomputed by.** `glm_universal.wheels.cent_wheels_study.cent_wheels_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026 by `python3 -m glm_universal.intake scaffold cent_compiler_v12 --study CENT_WHEELS_STUDY` (directive D22) and written the same day. §§0–7 were written on 31 October 2026 before any module of the round existed and before any question of §4 was put to an engine; §8 is what came out.  Last altered 31 October 2026: the wheels installed provisionally by the owner's decision, awaiting the owner's Lean build (§7, §8.2); the verdict says so.*

## 0. What this document is

A **pre-registration** for the intake of the wheels of one supplied item,
[`source_material/ToDo/cent_compiler_v12`](../source_material/ToDo/cent_compiler_v12)
(record `cent_compiler_v12` in
[`source_material/INTAKE.yaml`](../source_material/INTAKE.yaml)), followed by
its measurement in §8 (taken 31 October 2026). The item is a full study: a cross-domain physical
compiler (pound → cent → delta) with 31 JSON formula wheels (72 axioms, 119
cases), 22 application proposals, SPICE netlists, a framework and a validation
report. This round takes only the **wheels**; §1 says what is left.

The order of work, so the reader can weigh it:

1. *Read first.* The triage record (its wheel survey: seven axioms failing the
   dimension check, W22-03 disputed, 18 cases the GLM's engine could not parse
   because of fractional powers), the item's `README.md`, the 31 wheel files
   listed by hand (axioms, cases, flags and dimension tables), and the
   repository's conventions: `engineering/wheels.py` (relation vectors,
   exact span membership, the explicit-angle reference registry) and
   `DOMAIN_WHEELS_STUDY.md` §7.2 (the angle). The item's own tests were run on
   scratch copies, as at triage. Reading the tables by hand flagged more than
   the record lists: the root in W29's spin diffusion length, the missing
   permeability in W25's Alfvén speed, the table entry of W21's stress
   intensity factor (three axioms the record's engine could not parse), the
   literal `314159265` standing for π in W21, the two W33 axioms that together
   force the Nusselt number to 1, and two axioms that equate two different
   names (W24, W28). That is why marks S3 and S5 exist and why rule R (§3) is
   written as it is: the reader should know the rule was written by someone who
   had seen what it would correct. No code of the round had run, and no
   question of §4 had been put to an engine.
2. *Then this document*, with the marks, rule R, the absorption rule and the
   battery of §4 — the battery as data in
   `glm_universal/wheels/cent_wheels_study.py` (`MEASURE_BATTERY`, with the
   bars `BAR_WRONG_MAX`, `BAR_LAWS_LICENSED_MIN`, `BAR_BASELINE_LAWS_MAX`),
   written before the engine or the absorbed wheels existed.
3. *Then the code*: the rational-power engine and the absorbed wheels
   (`glm_universal/wheels/cent_wheels.py`), the Lean file
   (`Wheels/CentWheels.lean`), the tests (`tests/test_cent_wheels.py`) and the
   measurement functions below the battery.
4. *Then the measurement* of §8.

## 1. What the item offers, and what is taken from it

The item offers `cent_compiler` v2.0: it decomposes an abstract operation £
into atomic steps ¢, enumerates physical implementations ∆, escalates them
through five fidelity layers and emits a SPICE netlist; its data substrate is
31 JSON wheels (`wheels/W1.json` … `W35.json`, no W26, W27, W30, W31):

* **W1–W10**, the ten engineering wheels — W1–W3, W5, W7–W10 as in
  `engineering/wheels.py`; W4 adds the axiom
  `energy = 1/2 * moment_of_inertia * angular_velocity^2` and the case W4-04;
  W6 adds the axiom `power = pressure * volume_flow_rate` (which makes W6-03
  derivable);
* **W11–W15**, the five domain wheels of `DOMAIN_WHEELS_STUDY.md`, with the
  axioms of `src/glm_universal/wheels/w11.py`–`w15.py` and 14 cases (the
  package's wheels have none);
* **W16–W35**, sixteen wheels in domains no existing wheel covers: induction,
  gravitation, the ideal gas, EM waves, elasticity, fracture, kinetics,
  electrochemistry, semiconductors, plasma, Josephson junctions, spintronics,
  capillarity, heat transfer, haemodynamics, electrophysiology (34 axioms,
  64 cases).

**Taken in this round** (subject to the marks): the sound wheels among
W16–W35, with the axioms rule R corrects and without the axioms it drops,
as a third wheel family in `src/glm_universal/wheels/` beside the fifteen
monomial-law wheels and the provision wheels; the W4 and W6 additions and the
14 W11–W15 cases, as data with their Lean evidence, **without** changing the
W4 and W6 of `engineering/wheels.py` or the cases of `wheels/w11.py`–`w15.py`
(the registry of the fifteen wheels is untouched; attaching them is a
separate decision, listed in §8).

**Left open** (not evaluated in this round): the compiler itself (`cent`,
`cent_compiler/*.py`: grammar, pattern matcher, substrate library, cost
function, isomorphism gate, hypothesis bridge, simulators, delta-sigma), the
SPICE emission and the 22 `.cir` files, the 22 application proposals, the
expansion notes, `CENT_FRAMEWORK.md` and `VALIDATION_REPORT.md`.

## 2. The objects

**A relation vector**, as `engineering/wheels.py` writes it: an equation
`cL * Π l = cR * Π r` is the exponent of every quantity (left minus right) and
the prime exponents of `cL / cR`. Exponents are **rational**: a fractional
power `(…)^(1/2)` multiplies every exponent inside it, the coefficient's prime
exponents included, so `(2 * x)^(1/2)` has exponent 1/2 on the prime 2. The
integer engine of `engineering/wheels.py` refuses such powers (“a power must
be an integer literal”); the engine of this round reads them and is otherwise
the same (mark E1).

**Derivability**: a formula follows from a wheel when its relation vector lies
in the rational span of the wheel's axiom vectors (`ConnectedMachine.Derivable`
in Lean), decided by exact row reduction over `Fraction`; a *certificate* is
the rational combination, and a refusal is certified by a *separating
functional* — a rational vector orthogonal to every axiom and not to the
formula (`ConnectedMachine.not_derivable_of_functional`).

**A dimension verdict**: each wheel carries its own table, an exponent vector
over the eight axes L, M, T, I, H, N, J, A for each quantity. An equation's
residual is the table's image of its relation vector (prime coordinates map to
0): the two sides have equal exponent vectors exactly when the residual is 0.
Exponents are rational here too.

**The angle convention** — the repository's, fixed before anything is measured:
**SI7 decides, the angle axis is recorded.** An axiom is dimensionally sound
when its residual vanishes on the first seven axes (L M T I H N J, angle
dimensionless), as D4 of `DOMAIN_WHEELS_STUDY.md` is declared at SI7 and as
`expected_dimensional` of `engineering/wheels.py` is the SI verdict; the
residual on A (the explicit-angle policy, `expected_dimensional_explicit`) is
computed and stated, never hidden. The cent tables use the explicit-angle
registry of `engineering.wheels.REFERENCE_DIMENSIONS` (angular velocity
`T^-1 A`, torque `L^2 M T^-2 A^-1`, moment of inertia `L^2 M A^-2`; spring
constant and reactance without A), so `spring_constant = mass *
angular_frequency^2`, `reactance = inductance * angular_frequency` and
`inductance * capacitance * angular_frequency^2 = 1` balance at SI7 and carry
an A residual — the radian's usual status, as §7.2 of the domain-wheels study
records it.

## 3. The marks, declared before the code

| Mark | What is measured | Met when |
|---|---|---|
| I1 | the item's named tests | `cent test` and the item's `show_work.py` pass in place, on scratch copies (`intake advance cent_compiler_v12 tested`); the one failure of the item's `cent_compiler_v12/tests/test_all.py` (14 of 15 at triage) is explained |
| D1 | a dimension verdict for every axiom | all 72 supplied axioms get an SI7 verdict and an A residual from their own wheel's table, fractional powers included: 0 unknown |
| D2 | the tables against the repository registry | every quantity of a cent table that `engineering.wheels.REFERENCE_DIMENSIONS` also holds has the same eight exponents there; every disagreement listed |
| E1 | the exact engine | on every axiom and case of the 31 wheels that the integer engine of `engineering/wheels.py` can read, the rational-power engine gives the same relation vector and, case by case in its wheel, the same derivability verdict: 0 disagreements |
| E2 | what is new in W1–W15 | W1–W3, W5, W7–W10 identical to `engineering/wheels.py` (axioms, cases, flags); W4 and W6 differ exactly by the two additions of §1; W11–W15 axioms identical to `wheels/w11.py`–`w15.py` |
| S1 | the supplied flags | every supplied case's `expected_derivable` compared with span membership over its supplied axioms; every disagreement listed and settled in §8 with its reason |
| S2 | the negative controls | every `-N` case of the 31 wheels refused, over the supplied axioms and over the corrected ones |
| S3 | the failing axioms | every axiom that fails at SI7 — the seven of the record and any the record could not read — is corrected under rule R or dropped; afterwards 0 absorbed axiom fails at SI7 |
| S4 | W22-03 | settled: its span verdict over W22's axioms, with a Lean certificate |
| S5 | no hidden numbers | no absorbed wheel's span holds a nonzero relation among its SI7-dimensionless quantities and numbers alone (a hidden `nusselt_number = 1` or `2 = 1`); a wheel whose span does is corrected (by dropping the axiom that creates it) or not absorbed; axioms equating two different names are listed |
| A1 | the angle | every axiom whose only residual is on A is listed, and its SI7 balance and its A residual are stated in Lean |
| L1 | the Lean file | `Wheels/CentWheels.lean` proves, for every absorbed wheel, the W4/W6 additions and the W11–W15 cases: the axioms balance at SI7 (and on A where they do); every case, control and §4 question of the wheel has the verdict §8 reports, by an explicit rational combination or a separating functional; and every supplied axiom that fails at SI7 does, on its supplied table; no `sorry`, no `axiom`, no `native_decide`; imported by `AxiomAuditAll.lean`; `python3 -m glm_universal.lean_check` passes; `tests/test_cent_wheels.py` reads the file and agrees with the Python on every vector, certificate and verdict |
| M1 | wrong answers | with the absorbed cent wheels, at most `BAR_WRONG_MAX` = 0 of the 51 not-a-law questions of §4 licensed |
| M2 | the help | with the absorbed cent wheels, at least `BAR_LAWS_LICENSED_MIN` = 56 of the 64 law questions of §4 licensed |
| M3 | against the baseline | the GLM's fifteen wheels W01–W15 alone license at most `BAR_BASELINE_LAWS_MAX` = 4 of the 64 law questions, so at least 52 are new; their wrong answers are counted too |
| M4 | the naive union (reported, no bar) | the §4 battery read over the pooled axioms of the fifteen wheels and the absorbed cent wheels: laws licensed and wrong answers counted, and each conflation named |
| I4 | no regression | `test_wheels`, `test_integer_wheel`, `test_intake`, `test_combiner`, `test_exactness` and `test_constants` pass as before the round |

**How a question is answered** (M1–M3). The GLM licenses a formula when one of
its wheels derives it — span membership over that wheel's axioms, as
`engineering.wheels.case_table` reads a case in its wheel. *With the cent
wheels* means the fifteen wheels (through the integer engine) and the absorbed
cent wheels (through the rational-power engine); *the baseline* is the fifteen
wheels alone, where a formula the integer engine cannot parse is refused. A
licensed law is *right*; a licensed not-a-law is *wrong*; a refused law is a
*miss*; a refused not-a-law is *right*.

**Rule R** (a failing axiom is corrected only so). A correction is one of:

* **(a)** a standard factor missing from the law the wheel names, its other
  quantities as supplied (the factor and its dimension are the textbook's);
* **(b)** a root or power applied to the wrong group;
* **(c)** a wrong entry in the wheel's own dimension table, the axiom being the
  textbook law;
* **(d)** an integer literal standing for an irrational number dropped, as the
  wheels' convention drops 4π² in W17-03 and notes 2π in W4-M1.

A correction never replaces a supplied quantity by another and never needs a
function that is not a monomial; an axiom that cannot be corrected so is
**dropped** — correcting it would be guessing which law was meant. Every
correction and drop is recorded with the supplied text and the reason. A case
that is a rearrangement of a corrected axiom is corrected the same way, and its
supplied text becomes a question of §4 whose gold answer is *not a law*. A
case whose flag disagrees with span membership over the corrected axioms has
its flag settled by the span, with the reason.

**What the hand reading expects rule R to do** (the measurement confirms or
refutes each line):

| Wheel | Supplied | Defect | Expected decision |
|---|---|---|---|
| W21 | `fracture_toughness = (2 * youngs_modulus * surface_energy / (314159265 * crack_length))^(1/2)` | `314159265` stands for π (it is π × 10^8); the item's own case W21-01 drops it | corrected, (d): `fracture_toughness = (2 * youngs_modulus * surface_energy / crack_length)^(1/2)` |
| W21 | `stress_intensity_factor = dimensionless_factor * stress * crack_length^(1/2)` | the table gives `L^-1 M T^-2`; the law makes it `L^-1/2 M T^-2` (Pa·m^1/2) | table corrected, (c) |
| W22 | `rate_constant = pre_exponential_factor * concentration / rate_constant` | self-referential; Arrhenius `k = A exp(-Ea/RT)` is not a monomial | dropped |
| W25 | `cyclotron_frequency = magnetic_field / mass` | the charge is missing (`ω_c = qB/m`) | corrected, (a): `cyclotron_frequency = charge * magnetic_field / mass`, table gains `charge = T I` |
| W25 | `alfven_velocity = magnetic_field / mass_density^(1/2)` | the permeability is missing (`v_A = B/√(μ0 ρ)`) | corrected, (a): `alfven_velocity = magnetic_field / (permeability * mass_density)^(1/2)`, table gains `permeability = L M T^-2 I^-2` |
| W29 | `spin_diffusion_length = diffusion_coefficient * time^(1/2)` | the root binds τ only (`λ = √(Dτ)`) | corrected, (b): `spin_diffusion_length = (diffusion_coefficient * time)^(1/2)` |
| W32 | `capillary_height = surface_tension * wetting_coefficient / (viscosity * capillary_radius)` | Jurin's law has ρg and no viscosity; Washburn's has a viscosity and a time: which was meant is a guess | dropped |
| W34 | `vascular_resistance = viscosity * length / pipe_radius^4`; `volume_flow_rate = pressure / vascular_resistance` | the table gives resistance `L^-4 M T^+1`; the law makes it `L^-4 M T^-1` | table corrected, (c); 8/π dropped as declared |
| W35 | `membrane_voltage = temperature / valence` | `k_B/e` missing and Nernst has a logarithm | dropped |
| W35 | `ion_flux = diffusion_coefficient * ion_concentration` | a 1/length is missing: a gradient or a membrane thickness — which is a guess | dropped |
| W33 | `heat_transfer_coefficient = thermal_conductivity / characteristic_length` | balances, but with `nusselt_number = heat_transfer_coefficient * characteristic_length / thermal_conductivity` it forces the Nusselt number to 1 (mark S5) | dropped if S5 finds the relation |

So W35, with no axiom left, would not be absorbed, and the cases W25-01,
W25-02, W25-03 and W29-03 would be corrected with their axioms.

**The absorption rule.** A wheel of W16–W35 is absorbed when, after rule R,
it has at least one axiom; every axiom balances at SI7 on its (corrected)
table; S2 and S5 hold for it; and every one of its cases has a settled flag
equal to span membership — each proved in Lean (L1).

## 4. The battery, fixed before the wiring

115 derivability questions in the domains of W16–W35, as data in
`glm_universal.wheels.cent_wheels_study.MEASURE_BATTERY`: **64 laws** and **51
not-a-laws**. Each is attributed to the wheel whose domain it is in. The gold
answer comes from the physics, under these declared model conventions: magnitudes
only (the wheels relate positive magnitudes); numeric factors standing for π
dropped (4π² in Kepler's law, π in Griffith's, 8/π in Poiseuille's); W23's
Faraday law at valence 1; W28's flux one flux quantum. *Not a law* means
dimensionally wrong, a wrong coefficient, two quantities confused, or true only
in a special case.

* **Supplied cases (48)**: every case of W16–W35, the four W25/W29 cases rule R
  corrects in their corrected text. Their gold is *law*, except W24-03 (the
  Debye length without the elementary charge), W32-03 (built on the dropped
  W32 axiom), W33-01 and W33-02 (true only at Nusselt number 1) and W35-01 …
  W35-03 (built on the dropped W35 axioms): *not a law*. W22-03 (Fick's first
  law) is a *law* — whether W22 derives it is S4.
* **Negative controls (16)**: the `-N` case of each new wheel; *not a law*.
* **Supplied forms (13)**: the supplied text of every axiom and case rule R is
  expected to correct or drop (W21's π axiom; W22's, W32's, W33's and W35's
  dropped axioms; W25's two axioms and three cases; W29's axiom and case);
  *not a law*.
* **Held-out questions (38)**: written for this study, two or three per wheel
  where the wheel admits them — 23 laws, rearrangements or two-axiom
  consequences of the textbook laws (for example `emf = magnetic_field * area
  / time`, `period^2 = distance / surface_gravity`, `pressure = viscosity *
  length * volume_flow_rate / pipe_radius^4`), and 15 not-a-laws, five of them
  dimensionally consistent: a wrong coefficient (`flux = 2 * magnetic_field *
  area`, `period^2 = 2 * distance / surface_gravity`, `pressure * volume = 2 *
  amount * gas_constant * temperature`, `mass = 2 * charge * molar_mass /
  faraday_constant`), two quantities of one dimension confused
  (`stress = youngs_modulus`, `fracture_toughness = youngs_modulus`), or a
  special case (`nusselt_number = 1`).

The table of all 115, with their gold answers and reasons, is the constant
itself; §8 lists the outcome of every question.

## 5. Lean obligations

`RequestProject/GLM/Wheels/CentWheels.lean` (namespace `GLM.CentWheels`,
importing `RequestProject.GLM.ConnectedMachine` for `Derivable` and
`not_derivable_of_functional`), written in this round from the numbers:

* for each absorbed wheel: its axiom vectors over its own coordinates, its
  dimension table, and that every axiom's residual vanishes at SI7 — and on A
  too where it does — which is the statement that the two sides have equal
  exponent vectors;
* for each case, control and §4 question of the wheel: `Derivable` with an
  explicit rational combination checked coordinate by coordinate, or
  `¬ Derivable` with an explicit functional vanishing on every axiom and not on
  the question;
* the W4 addition balances (on all eight axes) and W4-04 follows from the W4
  axioms; the W6 addition balances, W6-03 follows once it is added, and W6-01,
  W6-02 and W6-N1 keep their verdicts;
* the W11–W15 axioms balance at SI7, the three angle axioms carry the A
  residuals §2 names, and each of the 14 supplied W11–W15 cases follows;
* every supplied axiom that fails at SI7 has a nonzero residual on its supplied
  table.

The build itself is the owner's (`scripts/rebuild_lean.sh`); this round checks
the file with its own type-check and with `python3 -m glm_universal.lean_check`
(static), and `tests/test_cent_wheels.py` re-verifies every certificate of the
file in exact arithmetic and compares every vector with the Python.

From the triage record, for the wheels this round takes:

* cent W1–W10: W4's new axiom balances over Z^8 and the new case is derivable;
  W6's new axiom balances and every existing W6 case keeps its derivability;
  the rest is unchanged from `engineering/wheels.py`.
* cent W11–W15 and W16–W35: per axiom, equal exponent vectors of the two sides
  from the wheel's own table (after the angle convention of §2); per case, the
  flag equals span membership over Q; per negative control, not in the span;
  the failing axioms corrected or dropped first; fractional powers with
  Q-valued exponents; W22-03 settled.

## 6. What this round does not do

* It does not evaluate, absorb or close the compiler, the SPICE emission, the
  applications, the expansion notes or the framework documents; they stay open
  parts of the record and the item stays in `ToDo/`.
* It does not change `engineering/wheels.py` (W1–W10), `wheels/w11.py`–`w15.py`,
  `ALL_WHEELS` or any junction table; the W4/W6 additions and the W11–W15
  cases are absorbed as data beside them.
* It does not join the cent wheels to the fifteen at junctions or license
  answers across wheels (the split-name answering of `engineering/domains.py`);
  M4 only reports what a naive union would do.
* It does not add axioms the item does not supply (Fick's law for W22,
  Jurin's law for W32): a dropped axiom is dropped, not replaced.

## 7. Files

* The item, `source_material/ToDo/cent_compiler_v12`, unchanged; its wheels are
  `wheels/W*.json` and `wheels/index.json`.
* The battery and the measurement: `wheels/cent_wheels_study.py`.
* The wheels that pass the absorption rule, and the rational-power engine:
  `wheels/cent_wheels.py` (the family `CENT_WHEEL_IDS`, `cent_family`,
  `answer_derivability`), with `wheels/lean_cent_data.py`.
* These three modules and `tests/test_cent_wheels.py` are in the package
  provisionally, by the owner's decision, until the owner's build confirms the
  Lean file (directive D22; §8.2).
* The Lean file: `src/lean/RequestProject/GLM/Wheels/CentWheels.lean`, imported
  by `AxiomAuditAll.lean`.
* The tests: `tests/test_cent_wheels.py`.
* The intake record: `source_material/INTAKE.yaml`, id `cent_compiler_v12`.

## 8. The measurement

*Taken 31 October 2026, after §§0–7, by
`glm_universal.wheels.cent_wheels_study.cent_wheels_report`; every figure below
is that function's, and `tests/test_cent_wheels.py` pins them.*

**In one sentence.** Yes, with one pre-registered mark not met. After rule R, 15 of the 16 new wheels are sound and pass the absorption rule (W35 loses both axioms and does not), and with them the GLM's exact engine licenses 63 of the 64 law questions of the pre-registered battery and 0 of its 51 not-a-law questions, where the fifteen wheels alone license 1 law; every negative control is refused and every verdict on the 15 has a Lean proof written, whose build is the owner's to confirm; until it is, the 15 wheels are in the package provisionally, and say so. Mark E2 is not met: besides its two additions, the supplied W4 omits the repository's case W4-M1.

### 8.1 The marks, pre-registered against measured

| Mark | Met when (§3) | Measured | Verdict |
|---|---|---|---|
| I1 | the two named item tests pass in place; the item's one `test_all` failure explained | `cent test`: exit 0, 7/7 simulations passed; the item's `cent_compiler_v12/tests/show_work.py`: exit 0 (it prints its original suite as 6/7). The item's `cent_compiler_v12/tests/test_all.py`: 14 of 15, as at triage. The fifteenth is application proposal 07 ("Quantum-Classical Bridge"): `test_07` of the item's `cent_compiler_v12/tests/test_applications.py` compares `E / c` with the same `E / c`, its own comment calls the check a tautology, it files the result as `DIMENSIONAL CHECK` rather than `PASS` and returns `False` on purpose, and the item's `test_all` counts only `PASS`. That is the item's honest self-classification, not a plain bug, so nothing was fixed and the item is unchanged | met |
| D1 | 72 verdicts, 0 unknown | 72 verdicts, 0 unknown. 62 axioms balance at SI7 and 10 fail: the seven of the triage record and three it could not parse (W21 axiom 2, W25 axiom 2, W29 axiom 2). 3 balance at SI7 and carry an A residual (A1) | met |
| D2 | every shared entry equal to the registry | 99 table entries shared with `REFERENCE_DIMENSIONS`, 0 disagreements; no quantity carries two dimensions across the 31 tables | met |
| E1 | 0 disagreements | 184 axioms and cases read by both engines, 0 disagreements in vector or verdict; 7 more read only by the rational-power engine (fractional powers) | met |
| E2 | W1–W3, W5, W7–W10 identical; W4 and W6 differ exactly by the two additions; W11–W15 axioms identical | W1–W3, W5, W7–W10 identical; W6 differs exactly by its addition; W11–W15 axioms identical as relations (three written as products: `mass * angular_frequency * angular_frequency` for `mass * angular_frequency^2`, and two like it in W14). **W4 differs by one more thing: the supplied W4 omits the repository's case W4-M1** (`angular_velocity = frequency`, a model-convention case, not derivable). The absorbed W4 data keeps W4-M1 (`extended_wheel("W4")` takes the repository's cases) and the Lean file proves it still refused (`W4Ext.q_W4_M1`) | **not met** |
| S1 | every flag compared and settled | 119 cases, 116 agree with span membership over their supplied axioms. W21-01 (flag derivable, span no: the supplied axiom carries the literal `314159265`, the case drops it) is settled by correcting the axiom, (d); W22-03 (flag derivable, span no) is settled not derivable (S4); W34-02 (flag not derivable, span yes over rational exponents: one quarter of the resistance axiom) is settled derivable. After rule R three more flags are settled by the span: W32-03 (it rearranges the dropped W32 axiom; also fails at SI7), W33-01 and W33-02 (true only at Nusselt number 1). Over the absorbed wheels: 60 cases, 0 disagreements. The supplied *dimension* flags disagree with the tables on 20 cases (W2-02, W8-N1, W10-03, W22-03, W24-03, W24-N1 name a quantity their table lacks; the rest fail on the uncorrected tables); after rule R two dimension flags of absorbed wheels are corrected (W17-03 explicit, W20-N1), both recorded in `CORRECTIONS` | met |
| S2 | every control refused | 26 of 26 supplied controls refused over the supplied axioms; 15 of 15 controls of the absorbed wheels refused over the corrected ones | met |
| S3 | the failing axioms corrected or dropped; 0 absorbed axiom failing | the ten, as §3's table expected: W21 axiom 2 by a table correction (c); W25 axioms 1 and 2 corrected (a); W29 axiom 2 corrected (b); both W34 axioms by a table correction (c); W22 axiom 2, W32 axiom 2 and both W35 axioms dropped. 0 absorbed axioms fail at SI7, and none carries an angle residual | met |
| S4 | W22-03 settled, with a Lean certificate | not derivable, over the supplied and over the absorbed W22 axioms: no W22 axiom names `diffusion_flux`, `diffusion_coefficient` or `concentration_gradient`; the separating functional is the `concentration_gradient` coordinate (`W22.q_W22_03`). The flag is corrected from derivable to not derivable; Fick's law is not added (§6) | met |
| S5 | no hidden number in an absorbed span; aliases listed | the supplied W33 span holds `nusselt_number = 1`, so W33 axiom 1 is dropped (as §3 expected); no absorbed span holds a dimensionless relation. Two axioms equate two names: W24 `saturation_current = current` and W28 `flux_quantum = magnetic_flux`, both kept (they balance and hide no number; W28's is the declared one-flux-quantum convention, W24's makes every current law a saturation-current law — listed here as a caveat on W24) | met |
| A1 | listed and stated in Lean | 3: W13 axiom 3 (A residual −2), W14 axiom 1 (−1), W14 axiom 2 (+2); in Lean `W13Dom.axiom_2_residual`, `W14Dom.axiom_0_residual`, `W14Dom.axiom_1_residual` (numbered from 0) | reported (no bar) |
| L1 | the Lean file proves every absorbed verdict and every SI7 failure, and is audited | `Wheels/CentWheels.lean`: 183 theorems over 22 sections (the 15 absorbed wheels, W4 and W6 with their additions, W11–W15) — 48 axioms balanced or with their stated residual, 84 derivations by explicit rational combination, 50 refusals by separating functional (W6-03 without the addition among them), and the 10 supplied SI7 failures with their exact residuals. `lean_cent_data.agreement` finds 0 problems against the Python; the file is imported by `AxiomAuditAll.lean`; `python3 -m glm_universal.lean_check` passes. The round type-checked every theorem of the file, in sections, under Lean 4 with Mathlib, against a stand-in for `ConnectedMachine.Derivable` and `not_derivable_of_functional` identical to them; the build in the repository's own toolchain is the owner's rebuild | met (the build pending the owner's rebuild log) |
| M1 | at most 0 of 51 not-a-laws licensed | 0 | met |
| M2 | at least 56 of 64 laws licensed | 63; the one miss is W22-03 (Fick's law, which no absorbed W22 axiom supports) | met |
| M3 | the fifteen wheels license at most 4 laws | 1 (W23-03, `current = charge / time`, by W15); 0 wrong; so 62 laws are new | met |
| M4 | the naive union reported | the pooled axioms of the fifteen and the absorbed wheels license 63 laws and 4 not-a-laws: H16-F, H17-F, H18-F, H23-F, each a wrong factor 2. All four use W1, W3 and W15: the fifteen wheels' pooled axioms already put the bare number 2 in the span — W3's `energy = 1/2 * capacitance * voltage^2` against W1's `power = voltage * current`, W3's `charge = capacitance * voltage` and W15's `charge = current * time`, `energy = power * time`, which give `energy = capacitance * voltage^2` (the energy a capacitor stores and the energy delivered at constant voltage share one name). The conflation is the fifteen wheels', not the cent wheels'; the answering surface asks one wheel at a time and licenses none of the four | reported (no bar) |
| I4 | the six named test files pass as before | `test_wheels` 34, `test_integer_wheel` 46, `test_intake` 19, `test_combiner` 24, `test_exactness` 27, `test_constants` 20 passed, 0 failed; the new `tests/test_cent_wheels.py` 36 passed | met |

### 8.2 What was absorbed, corrected and dropped

**Status, 31 October 2026: installed provisionally, awaiting the owner's Lean
build.** In this section *absorbed* means admitted by the absorption rule of
§3. The modules that hold the admitted wheels (`wheels/cent_wheels.py`,
`wheels/cent_wheels_study.py`, `wheels/lean_cent_data.py`) and their test are
in `src/glm_universal/wheels/` and `src/glm_universal/tests/`, but
`Wheels/CentWheels.lean` has not yet been built, so under the owner's decision
("keep them in the wheels folder now, clearly marked provisional until my Lean
build log confirms them") they are installed provisionally: the item's wheel
parts are recorded `provisional`, the item stands at *Lean written* in
`source_material/ToDo/`, the register
`src/glm_universal/wheels/_data/provisional.json` names it, and
`glm_universal.wheels.answer_derivability` adds the provisional note to every
answer a cent wheel gives. When `scripts/rebuild_lean.sh` passes, `python3 -m
glm_universal.intake advance cent_compiler_v12 measured` and `python3 -m
glm_universal.intake absorb-staged cent_compiler_v12` confirm them (the parts
become absorbed and the register entry goes); the compiler parts stay open.

* **Absorbed** (15 wheels, `src/glm_universal/wheels/cent_wheels.py`, the
  family `CENT_WHEEL_IDS` of `wheels/__init__.py`; provisional, as above): W16 induction, W17
  gravitation, W18 the ideal gas, W19 EM waves, W20 beams, W21 fracture, W22
  kinetics, W23 electrochemistry, W24 semiconductors, W25 plasma, W28
  Josephson, W29 spin diffusion, W32 capillarity, W33 heat transfer, W34
  haemodynamics — 25 axioms, 60 cases.
* **Corrected** under rule R, each recorded in `CORRECTIONS` with the supplied
  text and the reason: W21 axiom 1 (d, the literal `314159265` for π dropped);
  the W21 table entry of `stress_intensity_factor` (c, `L^-1/2 M T^-2`); W25
  axiom 1 (a, the charge) and axiom 2 (a, the permeability), with the cases
  W25-01, W25-02, W25-03; W29 axiom 2 (b, `(diffusion_coefficient *
  time)^(1/2)`) with W29-03; the W34 table entry of `vascular_resistance` (c,
  `L^-4 M T^-1`); and the flags W17-03 (explicit dimension), W20-N1
  (dimension), W22-03, W32-03, W33-01, W33-02 (derivability, to not
  derivable) and W34-02 (derivability, to derivable).
* **Dropped** (correcting would be a guess), in `DROPPED`: W22 axiom 2
  (self-referential; Arrhenius is not a monomial), W32 axiom 2 (Jurin or
  Washburn?), W33 axiom 1 (forces the Nusselt number to 1), both W35 axioms
  (Nernst needs a logarithm; Fick a 1/length). **Not absorbed:** W35, which
  has no axiom left.
* **The W4 and W6 additions and the 14 W11–W15 cases** are absorbed as data
  beside the registry (`ENGINEERING_ADDITIONS`, `ADDITION_TABLES`,
  `DOMAIN_CASES`, `DOMAIN_TABLES`, `extended_wheel`) with their Lean evidence
  (`W4Ext`, `W6Ext`, `W11Dom` … `W15Dom`); `engineering/wheels.py`,
  `wheels/w11.py`–`w15.py` and `ALL_WHEELS` are unchanged. Attaching them to
  the registry's W4, W6 and W11–W15 is a separate decision (it would change
  the registry's own measurements).

The query surface is `answer_derivability(equation, wheel_id=None)` of
`glm_universal.wheels.cent_wheels`, re-exported by the package `glm_universal.wheels` (which adds the provisional note): the fifteen wheels first (integer engine), then the absorbed
cent wheels (rational-power engine), one wheel at a time; a derivation comes
with its rational certificate, a refusal by a named wheel with its separating
functional.

### 8.3 Every question of §4

| Question | Wheel | Source | Gold | Fifteen wheels | With the cent wheels | Outcome | Naive union |
|---|---|---|---|---|---|---|---|
| W16-01 | W16 | case | law | refused | W16 | right | right |
| W16-02 | W16 | case | law | refused | W16 | right | right |
| W16-03 | W16 | case | law | refused | W16 | right | right |
| W16-N1 | W16 | control | not a law | refused | refused | right | right |
| H16-1 | W16 | held-out | law | refused | W16 | right | right |
| H16-2 | W16 | held-out | law | refused | W16 | right | right |
| H16-3 | W16 | held-out | law | refused | W16 | right | right |
| H16-F | W16 | held-out | not a law | refused | refused | right | wrong |
| W17-01 | W17 | case | law | refused | W17 | right | right |
| W17-02 | W17 | case | law | refused | W17 | right | right |
| W17-03 | W17 | case | law | refused | W17 | right | right |
| W17-N1 | W17 | control | not a law | refused | refused | right | right |
| H17-1 | W17 | held-out | law | refused | W17 | right | right |
| H17-2 | W17 | held-out | law | refused | W17 | right | right |
| H17-F | W17 | held-out | not a law | refused | refused | right | wrong |
| W18-01 | W18 | case | law | refused | W18 | right | right |
| W18-02 | W18 | case | law | refused | W18 | right | right |
| W18-03 | W18 | case | law | refused | W18 | right | right |
| W18-N1 | W18 | control | not a law | refused | refused | right | right |
| H18-1 | W18 | held-out | law | refused | W18 | right | right |
| H18-2 | W18 | held-out | law | refused | W18 | right | right |
| H18-F | W18 | held-out | not a law | refused | refused | right | wrong |
| W19-01 | W19 | case | law | refused | W19 | right | right |
| W19-02 | W19 | case | law | refused | W19 | right | right |
| W19-03 | W19 | case | law | refused | W19 | right | right |
| W19-N1 | W19 | control | not a law | refused | refused | right | right |
| H19-1 | W19 | held-out | law | refused | W19 | right | right |
| H19-2 | W19 | held-out | law | refused | W19 | right | right |
| H19-F | W19 | held-out | not a law | refused | refused | right | right |
| W20-01 | W20 | case | law | refused | W20 | right | right |
| W20-02 | W20 | case | law | refused | W20 | right | right |
| W20-03 | W20 | case | law | refused | W20 | right | right |
| W20-N1 | W20 | control | not a law | refused | refused | right | right |
| H20-1 | W20 | held-out | law | refused | W20 | right | right |
| H20-2 | W20 | held-out | law | refused | W20 | right | right |
| H20-F | W20 | held-out | not a law | refused | refused | right | right |
| W21-01 | W21 | case | law | refused | W21 | right | right |
| W21-02 | W21 | case | law | refused | W21 | right | right |
| W21-03 | W21 | case | law | refused | W21 | right | right |
| W21-N1 | W21 | control | not a law | refused | refused | right | right |
| F21-ax1 | W21 | supplied form | not a law | refused | refused | right | right |
| H21-1 | W21 | held-out | law | refused | W21 | right | right |
| H21-2 | W21 | held-out | law | refused | W21 | right | right |
| H21-F | W21 | held-out | not a law | refused | refused | right | right |
| W22-01 | W22 | case | law | refused | W22 | right | right |
| W22-02 | W22 | case | law | refused | W22 | right | right |
| W22-03 | W22 | case | law | refused | refused | miss | miss |
| W22-N1 | W22 | control | not a law | refused | refused | right | right |
| F22-ax2 | W22 | supplied form | not a law | refused | refused | right | right |
| H22-F | W22 | held-out | not a law | refused | refused | right | right |
| W23-01 | W23 | case | law | refused | W23 | right | right |
| W23-02 | W23 | case | law | refused | W23 | right | right |
| W23-03 | W23 | case | law | W15 | W15 | right | right |
| W23-N1 | W23 | control | not a law | refused | refused | right | right |
| H23-1 | W23 | held-out | law | refused | W23 | right | right |
| H23-2 | W23 | held-out | law | refused | W23 | right | right |
| H23-F | W23 | held-out | not a law | refused | refused | right | wrong |
| W24-01 | W24 | case | law | refused | W24 | right | right |
| W24-02 | W24 | case | law | refused | W24 | right | right |
| W24-03 | W24 | case | not a law | refused | refused | right | right |
| W24-N1 | W24 | control | not a law | refused | refused | right | right |
| H24-F | W24 | held-out | not a law | refused | refused | right | right |
| W25-01 | W25 | case | law | refused | W25 | right | right |
| W25-02 | W25 | case | law | refused | W25 | right | right |
| W25-03 | W25 | case | law | refused | W25 | right | right |
| W25-N1 | W25 | control | not a law | refused | refused | right | right |
| F25-01 | W25 | supplied form | not a law | refused | refused | right | right |
| F25-02 | W25 | supplied form | not a law | refused | refused | right | right |
| F25-03 | W25 | supplied form | not a law | refused | refused | right | right |
| F25-ax1 | W25 | supplied form | not a law | refused | refused | right | right |
| F25-ax2 | W25 | supplied form | not a law | refused | refused | right | right |
| H25-1 | W25 | held-out | law | refused | W25 | right | right |
| H25-2 | W25 | held-out | law | refused | W25 | right | right |
| H25-F | W25 | held-out | not a law | refused | refused | right | right |
| W28-01 | W28 | case | law | refused | W28 | right | right |
| W28-02 | W28 | case | law | refused | W28 | right | right |
| W28-03 | W28 | case | law | refused | W28 | right | right |
| W28-N1 | W28 | control | not a law | refused | refused | right | right |
| H28-1 | W28 | held-out | law | refused | W28 | right | right |
| H28-2 | W28 | held-out | law | refused | W28 | right | right |
| H28-F | W28 | held-out | not a law | refused | refused | right | right |
| W29-01 | W29 | case | law | refused | W29 | right | right |
| W29-02 | W29 | case | law | refused | W29 | right | right |
| W29-03 | W29 | case | law | refused | W29 | right | right |
| W29-N1 | W29 | control | not a law | refused | refused | right | right |
| F29-03 | W29 | supplied form | not a law | refused | refused | right | right |
| F29-ax2 | W29 | supplied form | not a law | refused | refused | right | right |
| H29-1 | W29 | held-out | law | refused | W29 | right | right |
| H29-F | W29 | held-out | not a law | refused | refused | right | right |
| W32-01 | W32 | case | law | refused | W32 | right | right |
| W32-02 | W32 | case | law | refused | W32 | right | right |
| W32-03 | W32 | case | not a law | refused | refused | right | right |
| W32-N1 | W32 | control | not a law | refused | refused | right | right |
| F32-ax2 | W32 | supplied form | not a law | refused | refused | right | right |
| H32-F | W32 | held-out | not a law | refused | refused | right | right |
| W33-01 | W33 | case | not a law | refused | refused | right | right |
| W33-02 | W33 | case | not a law | refused | refused | right | right |
| W33-03 | W33 | case | law | refused | W33 | right | right |
| W33-N1 | W33 | control | not a law | refused | refused | right | right |
| F33-ax1 | W33 | supplied form | not a law | refused | refused | right | right |
| H33-1 | W33 | held-out | law | refused | W33 | right | right |
| H33-F | W33 | held-out | not a law | refused | refused | right | right |
| W34-01 | W34 | case | law | refused | W34 | right | right |
| W34-02 | W34 | case | law | refused | W34 | right | right |
| W34-03 | W34 | case | law | refused | W34 | right | right |
| W34-N1 | W34 | control | not a law | refused | refused | right | right |
| H34-1 | W34 | held-out | law | refused | W34 | right | right |
| H34-2 | W34 | held-out | law | refused | W34 | right | right |
| H34-F | W34 | held-out | not a law | refused | refused | right | right |
| W35-01 | W35 | case | not a law | refused | refused | right | right |
| W35-02 | W35 | case | not a law | refused | refused | right | right |
| W35-03 | W35 | case | not a law | refused | refused | right | right |
| W35-N1 | W35 | control | not a law | refused | refused | right | right |
| F35-ax1 | W35 | supplied form | not a law | refused | refused | right | right |
| F35-ax2 | W35 | supplied form | not a law | refused | refused | right | right |

### 8.4 What is left

* The item's other parts — the compiler (`cent`, `cent_compiler/*.py`), the
  SPICE emission and the 22 `.cir` files, the 22 application proposals, the
  expansion notes, `CENT_FRAMEWORK.md` and `VALIDATION_REPORT.md` — were not
  evaluated; they stay open parts of the record and the item stays in
  `ToDo/`. Proposals 13, 15, 17, 18 and 19 rest on axioms this round corrected
  or dropped.
* W22 derives nothing about diffusion (W22-03 is a miss) and W32 keeps one
  axiom: adding Fick's or Jurin's law is a decision for a later round, not a
  correction.
* The Lean build of `Wheels/CentWheels.lean` is confirmed only by the owner's
  rebuild log (`scripts/rebuild_lean.sh`); until it is, the 15 wheels are
  installed provisionally and say so (§8.2).
