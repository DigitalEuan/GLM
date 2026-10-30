# Domain wheels: five more formula wheels, chosen from what the evaluation asks for, with their junctions

## Tier 0 — the coarse read

**Question.** Which domains does the machine most visibly lack, measured by the physical quantities its own evaluation questions name that no formula wheel holds, and does adding wheels for them, joined to the ten wheels only at declared junctions, derive the laws of those domains without letting a shared name smuggle in a wrong formula?

**Verdict.** Five domain wheels — uniform motion; density, volume and amount; period and the mass-spring oscillator; inductors and the LC circuit; charge and energy over time — joined to the ten wheels at ten declared junctions answer 21 of 23 declared questions with the declared law and refuse all 9 declared refusals, with no wrong answer; the two misses are refusals, because an energy from a power and a time is also a capacitor's stored energy across the charge junction; the census of the union shows the frequency-and-angle junction between waves and the oscillator makes angular frequency and angular velocity one quantity, and most of the new answers it gives are not among the declared laws.

**Deciding figure.** 3 of 5 marks (D2, D4, D5 met; D1, D3 missed); battery 21 of 23 answered and 9 of 9 refused, 0 wrong; census 54 of 200 gained answers are declared laws.

**Recomputed by.** `glm_universal.engineering.domains.domains_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for the domain half of Phase 157 (§§0–6 are committed
before the module, the battery's answers or the census are computed; §7 is
what came out). The owner asked whether additional wheels or domains are now
required, with junctions where applicable, and suggested that the strongest
domains are likely evident from what is failing. This study turns that into a
measurement and then into a construction:

1. **The demand census** (§2.1) — which physical quantities the machine's own
   evaluation questions name that no wheel holds. It was taken first, by the
   rule written below, and it chose the domains.
2. **Five domain wheels** (§2.2) for the quantities the census put at the top,
   each a declared set of monomial axioms in the form of
   `engineering/wheels.py`.
3. **Junctions** (§2.3) — the names a new wheel shares with an old one that
   mean the same measurand of the same object, declared one by one with the
   reason, and the declared **non-identities** that must stay split.
4. **A new frame**, *derive X from Y [, Z [and W]] across domains*, which
   solves over the union of all fifteen wheels with every shared name split
   except across a declared junction, by the rule of Phase 66
   (`engineering/union.py`), which it does not modify.

## 1. What is built

* `glm_universal/engineering/domains.py` — the demand census, the five
  wheels, the junction and non-identity tables, the split system over fifteen
  wheels, the frame's solver, the census of §2.5 and `domains_report`.
* The frame `domains` in `engineering/speak.py`, tried before every other
  frame and reading only text that ends *across domains*.
* `glm_universal/evaluation/domain_cases.py` — the battery of §2.4 and
  the labels of §2.5, committed with this document.
* `python3 -m glm_universal.tools domains [--census] [--write]` — the
  instrument; the census is stored in `engineering/_data/domains.json` beside
  the digest of the code that took it.
* `RequestProject/GLM/DomainWheels.lean` — what is proved (§5).

## 2. The rules, fixed before the measurement

### 2.1 The demand census

Every string constant of at least nine characters that holds a space, in
every module of `glm_universal/evaluation/`, is a question the machine is
measured on. Each is lower-cased and searched, longest name first, for every
quantity name of the 726-quantity register of at least four characters
(underscores read as spaces, whole words only, a matched span removed before
the next name is tried). A name **lacks a wheel** when no wheel of
`engineering/wheels.WHEELS` names it. The census is the count of strings
mentioning each name, and the domains are chosen from the names that lack a
wheel, highest count first.

Taken before anything was built, it reads (top of the list, names lacking a
wheel): `density` 36, `information` 29, `length` 23, `speed` 19, `time` 17,
`efficiency` 14, `position` 12, `molar_mass` 12, `period` 11, `albedo` 10,
`angular_frequency` 9, `volume` 9, then `inductance` 3, `spring_constant` 2,
`quality_factor` 2, `damping_coefficient` 2. `information` (a dimension axis,
not a formula's quantity), `efficiency` (read by the measurand register of
Phase 87), `position` and `albedo` (register columns, not wheel quantities)
are set aside with those reasons; the rest choose the five wheels below. A
census taken first and then built for is a construction check, not a test:
D4 says only that the wheels cover what they were built for.

*Correction (recorded with §7): the counts above were a first informal pass.
The declared rule, as `demand_census` implements it, reads `density` 42,
`information` 32, `length` 29, `time` 26, `speed` 20, `efficiency` 15,
`molar_mass` 15, `position` 14, `volume` 14, `period` 13, `albedo` 11,
`angular_frequency` 9, then `terahertz` 5, `binding_energy` 4,
`transfer_function` 4, `inductance` 3. The order moves; the names set aside
and the names chosen are the same.*

### 2.2 The five wheels

| id | title | axioms |
|---|---|---|
| W11 | Uniform motion | `velocity = length / time` |
| W12 | Density, volume and amount of substance | `density = mass / volume`; `volume = area * length`; `amount = mass / molar_mass` |
| W13 | Period and the mass-spring oscillator | `frequency = 1 / period`; `angular_frequency = angle * frequency`; `spring_constant = mass * angular_frequency^2` |
| W14 | Inductors and the LC circuit | `reactance = inductance * angular_frequency`; `inductance * capacitance * angular_frequency^2 = 1`; `energy = 1/2 * inductance * current^2` |
| W15 | Charge and energy over time | `charge = current * time`; `energy = power * time` |

**Not built, and why** (a negative design decision, recorded): a wheel of
uniform acceleration (`velocity = acceleration * time`, `length = 1/2 *
acceleration * time^2`) beside W11. Its *velocity* is the final velocity of a
start from rest while W11's is the velocity of uniform motion; joined through
the dynamics wheel they give every question about velocity from a length and a
time two answers a factor of two apart, and kept apart they still do, because
the union tries every copy. The domain is real and the honest reading of the
question is ambiguous; a wheel for it waits for a frame that says which motion
is meant.

### 2.3 Junctions and non-identities

A name a new wheel shares with another wheel is one variable only across a
junction below; otherwise it is split per wheel, exactly as Phase 66 splits
the ten. The five junctions of Phase 66 are kept unchanged.

| junction | names | the same measurand of the same object because |
|---|---|---|
| W5/W11 | `velocity` | the moving body's velocity in dynamics is its velocity of uniform motion |
| W5/W12 | `mass` | the body whose density is read is the body that moves |
| W6/W12 | `area` | the flow's cross-section is the cross-section of the swept prism |
| W11/W12 | `length` | the length the fluid moves is the length of the prism it sweeps |
| W9/W13 | `frequency`, `angle` | the oscillator's frequency is the frequency of the wave it drives, and the angle is one turn in both |
| W5/W13 | `mass` | the oscillating body is the dynamic body |
| W3/W14 | `capacitance` | the LC circuit's capacitor is the capacitor of electrostatics |
| W1/W14 | `current` | the inductor's current is the circuit's current |
| W1/W15 | `current`, `power` | the charge and the energy are carried by the circuit's current and power |
| W3/W15 | `charge` | the charge moved is the charge stored |

| non-identity | why the names stay split |
|---|---|
| W13/W14 `angular_frequency` | a mechanical oscillator against an electrical one: identifying them makes `spring_constant = mass / (inductance * capacitance)` |
| W3/W14 `energy` | the capacitor's stored energy against the inductor's |
| W3/W15 `energy` | the energy stored in a capacitor against the energy delivered over a time |
| W11/W15 `time` | a travel time against a charging time |

The frame reads two names in its questions by a declared alias, each with the
reason, and says so in the answer: `speed` as `velocity` (the wheels relate
magnitudes, and a speed is the magnitude of a velocity) and `distance` as
`length` (a distance travelled is a length).

### 2.4 The battery

`evaluation/domain_cases.py`, written with this document. 23 questions must
answer with a declared formula (compared as relations: the derived equation
and the declared one have relation vectors that are positive rational
multiples of each other, so `x = y^(1/2)` matches `x^2 = y`), and 9 must
refuse. Among the 23, three are answered by the ten wheels already
(`momentum` from mass and velocity, and the hydraulic power of Phase 66), so
the frame must not lose them; among the 9, the photon conflation, a non-
identity, an unknown word and the two readings of an energy from a charge and
a voltage.

### 2.5 The census of the union

Over every question *derive t from y and z* with `t`, `y`, `z` distinct names
of the fifteen wheels:

* **in-wheel**: some single wheel derives it (old or new);
* **gained**: the licensed union of the fifteen answers it, no single wheel
  does, and the licensed union of the ten (Phase 66) does not answer it;
* a gained answer is **right** when `(t, formula)` is a declared law in
  `DOMAIN_LABELS` (committed with this document), and **wrong** otherwise,
  whatever the reason;
* **naive-new**: the naive union of the fifteen (no split) answers it, no
  single wheel does, and its formula is not a declared law; the licensed
  union **refuses** such a question or answers it with a declared law.

| # | mark | pass |
|---|---|---|
| D1 | the battery | 23 of 23 answered with the declared formula, 9 of 9 refused, 0 wrong |
| D2 | frozen path | the ten-wheel frames are untouched: `engineering/wheels.py`, `union.py` unchanged, and every evaluation case gives the same outcome after the round as before it |
| D3 | the census | at least 90% of the gained answers are right, and the licensed union refuses at least 90% of the naive-new questions |
| D4 | coverage | every name the census of §2.1 put forward (`density`, `length`, `speed` by its alias, `time`, `molar_mass`, `period`, `angular_frequency`, `volume`, `inductance`, `spring_constant`) is named by a wheel, and every axiom of W11–W15 is dimensionally consistent at SI7 |
| D5 | proved | `DomainWheels.lean` holds the theorems of §5 with no `sorry` |

## 3. What would count against

* D1 missed: the junctions are too few to reach the laws, or too many and a
  conflation answers.
* D3 missed: a declared junction is wrong somewhere the battery does not
  look — the census is where a junction table's mistakes show.
* D4 missed at SI7: an axiom is dimensionally wrong, which would make every
  derivation through it suspect.

## 4. What is not claimed

* The census counts mentions in the machine's own question sets, not demand
  from outside the project.
* The wheels relate magnitudes by monomials; a sign, a vector direction, a sum
  of terms or a law that holds only on average is outside them.
* The labels are a declared list; an unlisted formula that is in fact a law
  is counted as wrong in D3 and named in §7.

## 5. What is proved before the measurement

`RequestProject/GLM/DomainWheels.lean`:

* **the oscillator conflation** — over the naive union of W13 and W14 (one
  `angular_frequency`), `spring_constant * inductance * capacitance = mass`
  is derivable (`oscillator_naive`); once `angular_frequency` is split, a
  linear functional vanishing on every axiom certifies it is not
  (`oscillator_refused_split`), by `not_derivable_of_functional` of
  `ConnectedMachine.lean`;
* **the swept volume** — over W6, W11 and W12 joined at the declared
  junctions, `volume_flow_rate * time = volume` is derivable
  (`swept_volume_licensed`);
* every derivation of the larger union of wheels remains one
  (`derivable_mono`, reused).

## 6. Files

See §1. Tests: `glm_universal/tests/test_domains.py`.

## 7. What came out

Taken in this order: the demand census (before anything was built, §2.1 and
its correction), the battery and the axiom check
(`python3 -m glm_universal.tools domains`), the census of the union (28
minutes of exact linear algebra, stored in `engineering/_data/domains.json`
with the digest of the code that took it), and the evaluation run after the
round against the one taken before it (shared with
[`FRICTION_TWO_STUDY.md`](FRICTION_TWO_STUDY.md), stored as
`knowledge/_data/friction_two_frozen.json`).

**Verdict.** Five domain wheels — uniform motion; density, volume and amount; period and the mass-spring oscillator; inductors and the LC circuit; charge and energy over time — joined to the ten wheels at ten declared junctions answer 21 of 23 declared questions with the declared law and refuse all 9 declared refusals, with no wrong answer; the two misses are refusals, because an energy from a power and a time is also a capacitor's stored energy across the charge junction; the census of the union shows the frequency-and-angle junction between waves and the oscillator makes angular frequency and angular velocity one quantity, and most of the new answers it gives are not among the declared laws.

**Marks.** 3 of 5 marks (D2, D4, D5 met; D1, D3 missed); battery 21 of 23 answered and 9 of 9 refused, 0 wrong; census 54 of 200 gained answers are declared laws.

### 7.1 The battery (D1 missed)

21 of 23 questions answered with the declared formula, 9 of 9 refused, 0
wrong. Among the 21: uniform motion read through the declared aliases
(*speed from distance and time* → `velocity = length / time`, the answer
saying it read `speed` as velocity and `distance` as length); the swept volume
`volume_flow_rate = volume / time` across W6, W11 and W12 joined at `area`
and `length`; a wave's period across W9/W13; a photon's energy from Planck's
constant and a period across W10/W13; momentum from a mass, a length and a
time across W5/W11; the LC angular frequency
`angular_frequency = (1 / inductance / capacitance)^(1/2)`. The three
questions the ten wheels already answered are answered the same way.

The two misses are refusals, not wrong answers:

* d16, *derive energy from power and time across domains*: "ambiguous: the
  licensed union gives energy = power * time (W15); energy = 1/2 * power *
  time (W1+W3+W15)";
* d17, *derive power from energy and time*: the same pair inverted.

The frame tries every copy of every asked name. W3's copy of `energy` is the
capacitor's stored energy `1/2 * charge * voltage`; across the junctions
`charge` (W3/W15) and `current`, `power` (W1/W15) it becomes `1/2 * power *
time`. The non-identity W3/W15 keeps the two energies apart as variables, as
declared, but the frame still answers for both copies, and they disagree.
The refusal is the honest reading of an underspecified question (which
energy?); the battery declared the delivered energy. A frame that is told
which energy is meant is the fix, not another junction.

### 7.2 Coverage and the axioms (D4 met)

Every name the demand census put forward is held by a wheel (`speed` by its
alias), and all twelve axioms of W11–W15 are consistent at SI7. At EXT10 —
where angle is its own axis — three are not: `spring_constant = mass *
angular_frequency^2`, `reactance = inductance * angular_frequency` and
`inductance * capacitance * angular_frequency^2 = 1` carry a residual in
angle, because W13 writes `angular_frequency = angle * frequency`. This is
the radian's usual status (dimensionless in SI, an axis in EXT10), recorded
and not a failure of D4, which is declared at SI7.

### 7.3 The census of the union (D3 missed)

Over the 48 names of the fifteen wheels: 155 questions are in one wheel, 200
are gained (the licensed fifteen answer, no wheel holding all three names and
not the licensed ten), and **54 of the 200 gained answers are declared laws**
(27%, against 90% declared). The naive half of D3 is empty: the naive union
of the fifteen wheels, with no name split, refuses every question by the
derivation rule (its own conflations put a relation among the inputs of every
question), so `naive-new` is 0 and there is nothing for the licensed union to
refuse. That is a finding about the naive union, not a pass.

The 200 gained rows are 28 distinct answers, repeated once for every unused
third name. Read:

* `angular_velocity = angular_frequency` (46 rows) and its declared form
  `angular_frequency = angular_velocity` (46 rows, counted right). The
  junction W9/W13 (`frequency`, `angle`) makes W13's
  `angular_frequency = angle * frequency` and W9's
  `angular_velocity = angle * frequency` the same relation. The label is
  declared; the rearranged form fails the comparison (below).
* `frequency = 1 / period` and `period = 1 / frequency` (42 rows each): one
  wheel, W13, answers; they are counted as gained because the code asks only
  wheels holding all three names (below).
* the rotational chain through W4 — `angular_frequency = power / torque`,
  `angular_momentum = angular_frequency * moment_of_inertia` and their
  rearrangements (6 rows), and the oscillator read through angular velocity,
  `spring_constant = angular_velocity^2 * mass` (3 rows): consequences of the
  W9/W13 identification, true of a rotating body, not declared;
* the RC time constant, `time = capacitance * resistance` (W1+W3+W15) and its
  rearrangements (3 rows): the charging time of W15 read through the
  resistor and the capacitor; a real law, not declared.

**Post hoc, not a mark** (`engineering/domains_reread.py`). Two places where
the census code is narrower than the declaration's words: *in-wheel* is
declared as "some single wheel derives it", but the code asks only wheels
holding all three names; and the labels are declared, in
`evaluation/domain_cases.py`, to match "any target" of a relation, but the
comparison is up to a positive multiple, which a rearrangement with the other
side as target negates. Read with both words literally, 84 one-wheel rows move
to in-wheel and **104 of the remaining 116** gained answers match a label
(89.7%) — still under 90%, the remainder the rotational chain and the RC time
constant above. D3 stands missed.

What the census says about the junctions: the W9/W13 junction is the one
that does the most work, and it is a modelling choice the battery did not
test — it identifies an oscillator's angular frequency with a rotating
body's angular velocity. Every other new junction gave only declared laws or
the RC time constant.

### 7.4 Frozen path and proofs (D2, D5 met)

`engineering/wheels.py` and `union.py` have the digest they had before the
round, and the evaluation after the round gives every one of the 222 cases
the outcome it gave before (220 of 222 both times; the two that fail, before
and after, are `report-relay` and `report-anonymous`, whose pinned
goal-query counts moved with the Lean files, §7.5).
`RequestProject/GLM/DomainWheels.lean` builds with no `sorry`:
`oscillator_naive` (over the naive union of W13 and W14,
`spring_constant * inductance * capacitance = mass` is the spring law plus
the LC law), `oscillator_refused_split` (once `angular_frequency` is split, the
functional twice-capacitance minus W14's angular frequency minus reactance
vanishes on all six axioms and not on the target) and
`swept_volume_licensed` (with `swept_volume_licensed_mono` for any larger set
of axioms).

### 7.5 Left open

* **Which energy.** d16 and d17 are refused because "energy" names the stored
  and the delivered energy; a frame that names the energy (stored in a
  capacitor, an inductor, delivered over a time) would answer both.
* **The W9/W13 junction.** Either declare its consequences as laws (the
  rotational chain is right for a rotating body), or split `angle` and keep
  only `frequency` across it, and re-take the census.
* **The census code against its words.** The post-hoc reading above is the
  declared intent; making it the census's rule is a change that needs a new
  mark declared before the census is re-taken.
* **The naive union is not a control.** A naive comparison should be taken
  wheel-pair by wheel-pair, as Phase 66's was, not over all fifteen at once.

### 7.6 After Phase 158: the W9/W13 junction changed

*Recorded after the round; the marks above are those of Phase 157 and do not
move.* [`OSCILLATOR_JUNCTION_STUDY.md`](OSCILLATOR_JUNCTION_STUDY.md) tried
this study's W9/W13 junction four ways under a rule declared before the
measurement and shipped the one that joins `frequency` only, with `angle`
split and recorded as a non-identity: the rotor chain of §7.3 (the
oscillator's angular frequency as a rotating body's `power / torque`) is
refused, and the battery is unchanged (21 of 23 answered, 9 of 9 refused, 0
wrong). The census of the union stored in `engineering/_data/domains.json` was
re-taken under the new junction: 99 gained rows (8 of them declared laws under
the declared comparison; D3 stays missed), of which 84 are one-wheel
answers and 15 are gained under the post-hoc reading, 12 of them right (the 3
others are the RC time constant). The figures in §7.3 are those of the census
as Phase 157 took it. The reference-circle identity `angular_frequency =
angular_velocity`, which this study labelled a law, is no longer derived
across the junction; why, and what would bring it back, is that study's §7.3
and §7.6.
