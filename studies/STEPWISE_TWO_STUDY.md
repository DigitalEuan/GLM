# The stepwise planner, round two: the frames the leaves lacked, givens with units, and the register in the wheels

## Tier 0 — the coarse read

**Question.** Can the stepwise planner read the four kinds of question round one could not — *how many more*, parity, averages, givens written with units — and let a register value feed a wheel derivation, without answering anything wrongly?

**Verdict.** Yes: the stepwise planner now reads *how many more*, parity and averages over register values, converts givens and targets written with units through a declared exact unit table, and feeds register values into wheel derivations through the declared scale table, answering every declared case as declared with 0 wrong answers and refusing by name wherever a unit, a scale or an order is not what the question needs.

**Deciding figure.** 53 of 53 declared questions, 2 of 2 narratives and 2 of 2 follow-ups as declared, 0 wrong, where round one's reader answers 0 of the 53; 39 of 39 chain scripts verified (178 of 178 steps aligned) and every mutation rejected, 22 of 22 unit lies included; 8 of 8 marks met.

**Recomputed by.** `glm_universal.runtime.stepwise_two.stepwise_two_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round one ([`STEPWISE_PLANNER_STUDY.md`](STEPWISE_PLANNER_STUDY.md), Phase
72) made the typed planner the executive of a chain of steps. Its §4.1 ran
nineteen questions written after the module and found four it could not read:
*how many more protons does iron have than carbon*, *is the atomic number of
gold odd*, *the average of …*, and givens written with units (*voltage = 12
volts*), which the goal reader refused rather than guess a unit. Its §6 named
those, and one more: a register value (*the melting point of iron*) feeding a
wheel derivation. Those are items two and four of candidate O of
[`STATUS.md`](../STATUS.md) §3.4, and this round takes them.

Item one of candidate O, a question set written by someone outside the
project, is not something this round can supply; item three, the reverse
relay into the chain, is left named (§6).

## 1. The objects

Exact throughout (D7), no digest decides a meaning (D3).

* **Three frames over the leaves.** *How many more X does A have than B*
  reads the count noun through a declared table (`protons` is the atomic
  number, by definition) and is a subtraction of two leaves; *how much
  larger / higher / lower is A than B* is the same subtraction, the right way
  round. A difference that comes out negative is refused
  `DIFFERENCE_REVERSED` rather than answered with a negative number: the
  question presupposed the opposite order. *Is A odd / even* is a parity step
  over an integer, refused `NOT_AN_INTEGER` otherwise. *The average (mean) of
  A, B and C*, and the distributive plural *the average of the Xs of A, B and
  C*, is one step with every item as an input.
* **Givens with units.** A given may be written `name = amount unit`. The
  unit is read through a declared table: the SI coherent units by name, the
  exact SI prefixes, the planner's own exact table of length, mass and time
  units, and products, quotients (`per`) and powers (`square`, `cubic`) of
  them. Each unit carries a dimension over the seven SI axes and an exact
  factor into the coherent SI unit; the dimension must equal the wheel
  quantity's dimension (the formula study's reference registry, read under
  the SI policy, angle dropped), and the amount is converted into SI before
  any wheel is read. A target may be asked `in unit`, and the answer is
  converted out. A bare number is read in the coherent SI unit, as round one
  read every given. Unit names are spelled out: a lower-cased symbol is
  ambiguous (`mw` is a milliwatt or a megawatt), so symbols are not read.
  Four named refusals: `UNKNOWN_UNIT`; `UNIT_MISMATCH` (a unit of another
  dimension, on a given or a target); `UNIT_INEXACT` (a unit whose SI factor
  is not an exact rational: the revolution and the degree of angle carry π,
  the dalton is measured rather than defined); `OFFSET_UNIT` (degrees Celsius
  or Fahrenheit: the conversion depends on whether the wheel's temperature is
  a level or a difference, and the wheel does not say).
* **The register in the wheels.** A given may be written `name = <phrase>`,
  the phrase a question the planner answers from the register (*temperature =
  the melting point of iron*), or as the bare phrase (*given the melting point
  of iron and …*), when the name is the quantity the scale table declares for
  that field. The value is read from the register and carried into SI through
  the declared scale table of Phase 55
  ([`SCALE_CONVERSION_STUDY.md`](SCALE_CONVERSION_STUDY.md)) and an exact
  factor from the scale's canonical unit into SI (kelvin is SI; a picometre is
  10⁻¹² m). A field on no declared scale is refused `SCALE_UNDECLARED`; a
  scale whose canonical unit has no exact SI factor (the unified atomic mass
  unit) is refused `UNIT_INEXACT`; a scale of another dimension
  `UNIT_MISMATCH`; a bare phrase whose declared quantity names no wheel
  quantity (*the atomic radius of iron* is a length, and no wheel has a
  quantity called length) `UNKNOWN_QUANTITY`, rather than a guess at which
  length is meant.
* **Three columns.** Every new step has a declared column-1 template and a
  column-2 equation that the chain's column-3 script reads back with its own
  readers. A given written with a unit is two steps — the amount as written,
  then its conversion into SI — and a register-fed given is two steps — the
  register entry, then its conversion. The script re-reads the unit or the
  scale from the declared tables and re-derives the factor and the dimension
  check itself; it does not trust the recorded factor.

## 2. Declarations — written before any code of the round

The corpus is
[`evaluation/stepwise_two_cases.py`](../overlay/glm_universal/evaluation/stepwise_two_cases.py),
committed with this section and before any code: 21 frame questions (16 to be
answered, 5 refused by name), 18 unit questions (12 answered, 6 refused), 14
register questions (7 answered, 7 refused), 2 narratives and 2 follow-ups.
Every expected answer was worked by hand.

| mark | claim | measured by |
|---|---|---|
| **T1** | every frame case gets its declared verdict; 0 wrong. Control: round one's reader (the new frames switched off) answers 0 of the 21 | `frames` |
| **T2** | every unit case gets its declared verdict, and every answered one stitches exactly the declared quantities; 0 wrong | `units` |
| **T3** | every register case gets its declared verdict, and every answered one stitches exactly the declared quantities; 0 wrong | `register` |
| **T4** | the unit table matters: a *strip the units* control (every amount read as SI, every target unit ignored, every register value taken as held) answers wrongly at least 5 of the answered unit and register cases, and answers at least 4 of the declared unit refusals | `controls` |
| **T5** | every answered chain's column-3 script prints `VERIFIED True` in a fresh `python3 -I`, with one `ALIGNED` line per step; round one's five mutation kinds are all rejected, and so is a sixth, `unit-lie` (a conversion step's factor altered, both columns re-rendered to agree) | `scripts` |
| **T6** | non-interference: round one's corpus keeps every verdict (marks S1–S7 of the round-one study still met), and on the router's declared sets no answered verdict changes and no declared refusal becomes an answer | `interference` |
| **T7** | both narratives get their declared values (in the unit asked), order taken and stitched quantities; both follow-ups their declared verdict | `narratives`, `follow_ups` |
| **T8** | `RequestProject/GLM/StepwiseFrames.lean` builds with no `sorry` and standard axioms, and proves: the mean is order-free and lies between the least and the greatest item; the parity witness decides parity; the difference is refused exactly when it is negative; a monomial law is invariant under a change of base units exactly when it is dimensionally homogeneous (so the unit check is what licenses the conversion); an offset conversion does not commute with differences (so `OFFSET_UNIT` withholds a real ambiguity); a positive conversion leaves the consistency veto unchanged | Lean |

The measurement is `glm_universal.runtime.stepwise_two.stepwise_two_report`.

**One amendment, before any measurement.** None to the corpus or the marks.
While writing the module one defect of round one was found and fixed (§4.2):
round one's column-3 script re-read a decimal given (`voltage = 1.5`) as `1`
and so rejected a right chain.

## 3. What was built

* [`runtime/quantity_units.py`](../overlay/glm_universal/runtime/quantity_units.py)
  — the declared unit table: spelled-out unit names with an exact SI factor
  and a symbol whose dimension is *derived* by
  `reasoning.units.dimension_of_symbol` (so the volt's dimension comes from
  the register's own `V = W/A`, never from a stored vector); the exact SI
  prefixes; the planner's length, mass and time table read as it stands;
  `per`, `square`, `cubic`, `squared`, `cubed` and products; the named
  inexact units (revolution, degree, dalton) and offset units (Celsius,
  Fahrenheit); and `scale_into_si`, which carries a Phase 55 scale into SI (a
  kelvin is SI, a picometre is 10⁻¹² m, the unified atomic mass unit has no
  exact factor).
* [`runtime/stepwise.py`](../overlay/glm_universal/runtime/stepwise.py) —
  the three frames (`_difference_readings`, the parity predicate,
  `_mean_readings`) with the steps `mean`, `parity` and the guarded
  difference; `parse_goal_two` and `goal_two`, which read givens written
  `name = amount unit`, `name = <register phrase>` or as a bare register
  phrase, and targets written `T in unit`, convert them, and hand the SI
  values to round one's derivation, vetoes and narrative, unchanged
  (`_goal_core`). A question takes the round-two goal path only when it uses
  a round-two feature; every round-one question takes round one's path
  (`ROUND_TWO` switches the round off for the control).
* [`reasoning/stepwise_script.py`](../overlay/glm_universal/reasoning/stepwise_script.py)
  — the column-1 templates, column-2 equations and readers of the five new
  step kinds (`measured`, `si`, `unit_out`, `parity`, `mean`); the chain's
  script re-reads each unit or scale from the declared tables, re-derives
  the factor and the dimension check itself, re-reads the question for every
  amount and unit, and checks that a conversion is of the unit (or register
  entry) it claims; the sixth mutation `unit-lie`.
* [`runtime/stepwise_two.py`](../overlay/glm_universal/runtime/stepwise_two.py)
  — the measurement (`stepwise_two_report`) and both controls; `tools
  stepwise-two`; `tests/test_stepwise_two.py`.
* **Wiring.** Nothing new: the router already hands a planner refusal to the
  stepwise planner, so every new question is reachable from `GLM.py --ask`
  and `GLM.py --steps`, with its three columns and `--verify-tct`.
* [`RequestProject/GLM/StepwiseFrames.lean`](../RequestProject/GLM/StepwiseFrames.lean)
  — §5.

## 4. Results

Measured by `tools stepwise-two` at the close of the round.

**Can it?** Yes: the stepwise planner now reads *how many more*, parity and averages over register values, converts givens and targets written with units through a declared exact unit table, and feeds register values into wheel derivations through the declared scale table, answering every declared case as declared with 0 wrong answers and refusing by name wherever a unit, a scale or an order is not what the question needs.

| mark | result | figure |
|---|---|---|
| **T1** | met | 21 of 21 frame cases as declared: 16 answered, 5 refused by the declared name (`DIFFERENCE_REVERSED` twice, `NOT_AN_INTEGER`, `UNKNOWN_STEP` twice); 0 wrong. Round one's reader answers 0 of the 21 |
| **T2** | met | 18 of 18 unit cases as declared, every answered one stitching exactly the declared quantities: 12 answered, 6 refused (`UNIT_MISMATCH` twice, `UNKNOWN_UNIT`, `UNIT_INEXACT`, `OFFSET_UNIT`, `INCONSISTENT_GIVENS`); 0 wrong. Round one answers 0 of the 18 |
| **T3** | met | 14 of 14 register cases as declared: 7 answered, 7 refused (`UNIT_INEXACT`, `UNKNOWN_QUANTITY` twice, `UNKNOWN_STEP`, `SCALE_UNDECLARED`, `NO_DERIVATION`, `INCONSISTENT_GIVENS`); 0 wrong. Round one answers 0 of the 14 |
| **T4** | met | strip-the-units answers 6 of the answered unit and register cases wrongly (`u05`, `u06`, `u07`, `u09`, `g04`, `g11`; at least 5 declared) and answers 7 of the declared unit refusals (at least 4 declared) |
| **T5** | met | 39 of 39 answered chains verified in a fresh `python3 -I`, 178 of 178 steps `ALIGNED`; value lie, column 1 alone, reordering, answer and read lie each 39 of 39 rejected, unit lie 22 of 22 |
| **T6** | met | round one's corpus through the round-two module: 30 of 30 composition, 21 of 21 goal, 6 of 6 narrative, 4 of 4 follow-up cases as declared, its controls unchanged (3 and 1), its 43 scripts still verified; on the router's 273 declared questions the stepwise layer still reads 11, every one answered by the planner first, and turns none into an answer |
| **T7** | met | 2 of 2 narratives (values in the unit asked, order taken, stitched quantities) and 2 of 2 follow-ups as declared |
| **T8** | met | §5 |

**In all.** 53 of 53 declared questions (21 frames, 18 unit, 14 register), 2
of 2 narratives and 2 of 2 follow-ups as declared, with 0 wrong answers;
every declared case was met on the first measurement. As in round one, the
corpus and the module share an author, so this is the reach of the declared
set, not an independent test (§6).

**What the unit table buys, case by case.** The strip-the-units reading is
the one a reader that ignores units would give. It is wrong wherever the
prefixes do not cancel: *500 grams at 36 kilometres per hour* has energy 25 J,
not 324,000; *12 newtons on 3 square metres* is 1/250 kPa, not 4; *2 kilowatts
at 250 volts* is 125/4 Ω, not 31,250; two pounds is not two kilograms; the
atomic radius of iron is 194 pm, so the wave speed is 97/10¹¹ m/s, not 970;
121.77 kJ is not 121,770. It answers seven questions the table refuses: a
voltage in metres, a unit it cannot read, revolutions per minute (π), degrees
Celsius, a power asked in metres, an atomic weight fed in as a mass in
kilograms, and an atomic number fed in as a temperature. Twelve of the
eighteen answered cases it gets *right* by coincidence — *12 kilovolts and 2
milliamperes* is 24 W either way, because kilo and milli cancel — which is
why agreement with a unit-blind reading is no evidence that units were read.

**What the register feed buys.** *Given mass = 2, specific heat capacity =
450 and temperature = the melting point of iron, what is the entropy?* reads
1811 K from the element table, carries it into SI through the declared scale
(kelvin, factor 1), stitches the stored heat (1,629,900 J) that nobody asked
for, and divides: 900 J/K. *Given temperature = the melting point of iron,
energy = 3622 and entropy = 3* is refused `INCONSISTENT_GIVENS` because the
register value re-derives the entropy as 2. *Given the atomic radius of iron
and frequency = 5* is refused `UNKNOWN_QUANTITY`: the scale table says the
radius is a length, and the reader does not guess which of the wheels'
lengths (a wavelength) is meant.

**Faculty (D15).** Derive: every answered chain computes a value no register
holds — a difference, a mean, a parity verdict, or a wheel quantity from
converted givens and register values — with every step shown and re-checked
in all three columns. Refuse: the six new named refusals withhold the seven
answers the strip-the-units reading gives to questions whose units or scales
do not license them, and `DIFFERENCE_REVERSED` withholds the negative
difference a question with the order reversed would otherwise get.

### 4.1 Beyond the declaration — not counted

Seventeen further questions, written after the module worked and so **not** a
held-out test, were run once through `GLM.py --ask`'s router. Fourteen were
answered and each was checked by hand, and each chain's script verified: 0
wrong (among them *the average of the atomic numbers of helium, neon and
argon* = 10, *1.2 kilowatts at 5 amperes* = 240 V, *1500 kilograms at 72
kilometres per hour* = 30,000 kg m/s, *3 tonnes at 2 metres per second
squared* = 6 kN, *5 kilojoules at the melting point of gold* = 500000/133733
J/K, and a question written with a capital and a question mark). Three were
refused: *600 terahertz* (the prefix table stops at giga), *how much heavier
is …* (*heavier* is not a comparative of the difference frame; the question
went to another reader, which refused it), and an average over an element
the register does not hold.

### 4.2 A defect of round one, found and fixed

Round one's column-3 script re-read every given from the question with the
pattern `-?\d+(?:/\d+)?`, so a decimal given (`voltage = 1.5`) was re-read as
`1`, and the script printed `VERIFIED False` for a chain whose answer (9/2)
was right. The round-one corpus has no decimal given, so no round-one mark
exercised it. The script now re-reads the question item by item, with the
amount, its decimal part and its unit; the case is pinned in
`tests/test_stepwise_two.py`.

## 5. Lean

`RequestProject/GLM/StepwiseFrames.lean` builds with no `sorry` and the
standard axioms only (`propext`, `Classical.choice`, `Quot.sound`).

* `mean_perm`, `le_mean`, `mean_le` — the mean is independent of the order of
  the items and lies between any lower and upper bound of them.
* `parity_witness`, `odd_iff_emod` — the column-2 witness `n = 2 × q + r`,
  `r ∈ {0, 1}`, decides parity, and `r = 1` exactly when `n` is odd.
* `more_eq_none_iff`, `more_eq_some_iff` — the difference is refused exactly
  when the first is smaller, and an answer is the difference and never
  negative.
* `monomial_rescale`, `invariant_iff_homogeneous` — a change of base units
  multiplies a monomial by the powers of its degrees, so a (non-zero)
  monomial law holds in every system of base units exactly when it is
  dimensionally homogeneous: the reason a given is converted only through a
  unit of its quantity's own dimension.
* `offset_not_multiplicative`, `offset_changes_product` — a conversion with
  an offset is no multiplication, and reading a temperature as a level or a
  difference changes a product law by `m c o`: `OFFSET_UNIT` withholds a real
  ambiguity.
* `unit_round_trip`, `veto_unit_free` — a conversion out and back is exact,
  and the consistency veto does not depend on the unit a given was written
  in.
* `register_feed_sound` — a derivation in which a register value, carried
  into SI, stands for a given evaluates to the true value in every model of
  the rules in which the register is right; round one's `eval_eq_model` with
  the register's correctness as the stated hypothesis. (`IsModel` in
  `StepwisePlanner.lean` is now `@[expose]`, so this file can build a model
  of it.)

## 6. What this leaves

* **A held-out set nobody on the project wrote** — still the sharpest item,
  and still not something the project can write for itself. Every mark of
  both rounds was met on the first reading; §4.1 is the honest size of the
  reach beyond the declared sets.
* **The reverse relay into the chain** — let `relay:` hand a column-2 value
  to the stepwise planner, so its multi-step answer chooses the next reverse
  operation (candidate M's last item). Untouched by this round.
* **Measurands, not units.** The unit check compares dimensions, so it
  cannot tell a torque from an energy (both `L² M T⁻²` under the SI policy)
  or a frequency from an angular velocity; the scale table's quantity names
  (`length`) are not the wheels' (`wavelength`). A declared map from register
  measurands to wheel quantities is candidate K2 and candidate 1's second
  half, and it is what would let *the atomic radius of iron* feed a
  wavelength by name rather than only by `wavelength = …`.
* **Precision.** A register value enters the derivation as the exact
  rational the register holds; its stated precision (the ordering frame's
  interval) is not carried through the wheels. An answer derived from 77.36 K
  is exact for 77.36 and says nothing about 77.355.
* **Widening.** The tera- and pico- prefixes, *heavier / lighter / older* as
  comparatives with a declared field, parity and averages over a whole
  column (candidate 2's folds), and *how many more* over further count nouns
  (electrons need a charge state; neutrons need a nuclide register).
