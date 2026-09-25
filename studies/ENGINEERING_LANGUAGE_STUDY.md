# Engineering languages — formula wheels, the Smith chart, analogies and delta-sigma

## Tier 0 — the coarse read

**Question.** The formula-wheel session record built three standalone engineering studies and named, as its first priority, running them against the GLM's own substrate. Can the GLM be asked electrical and mechanical questions in words — derive a formula-wheel spoke, check a formula at two dimensional layers, move a load onto the Smith chart, carry a problem between a spring and a circuit, say what a delta-sigma loop does — and answer them exactly, or refuse with a reason, without a wrong answer?

**Verdict.** Through the engineering surface the GLM answers every preregistered engineering question it was asked and refuses every one whose right outcome is a refusal, with no wrong answer, where both existing paths refused all of them; the register agrees with the corrected formula study on all 41 cases at both layers, and the rules that license the answers are proved.

**Deciding figure.** Of 63 preregistered questions the surface answers 53 correctly and refuses 10 correctly with 0 wrong, against 0 correct and 53 refused through both existing paths; the stress set written after the first run scored 27 correct, 10 correct refusals and 1 scored wrong on its first run.

**Recomputed by.** `glm_universal.engineering.study.engineering_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. What this round took, and from where

Not a candidate of [`STATUS.md`](../STATUS.md) §3.4. The round took the
supplied session record,
`source_material/formula_wheel/GLM_formula_wheel_study_session_record.md`,
with the three scripts and the candidate table supplied beside it
(`02_glm_formula_wheel_study_v2.py`, `06_glm_formula_wheel_suite.py`,
`08_glm_multidomain_evidence_suite.py`, `glm_smith_matching_candidates.csv`).
The record's own Priority 1 is *integrate the real GLM substrate*: run the
same cases through the register, read-only, with the same labels. Its
figures — 41/41, 16/16, 6/6 — measure standalone scripts against their own
expectations, and none of them measures a question put to the machine.

The Smith-chart and delta-sigma scripts the record names
(`glm_smith_chart_study.py`, `glm_smith_chart_extensions.py`,
`glm_delta_sigma_audio_study.py`) were not supplied. They were not needed:
the record describes each protocol closely enough to rebuild it exactly, and
the rebuilt versions are exact (`Fraction`) where the originals used floats.
The originals would be needed only to reproduce the record's float figures
byte for byte, which is not a goal of this round.

Before any engineering code existed the question set was committed on its
own (`evaluation/engineering_heldout.py`, 63 questions, labels written from
textbook physics), and both existing paths were run against it:
`GeometricSession.ask` and `ask_planned` each scored **0 correct, 0 wrong,
53 refused, 10 correct refusals**. The machine could not be asked any of it.

## 2. What was built

`overlay/glm_universal/engineering/`, standard library only, exact
throughout:

| module | what it does |
|---|---|
| `wheels.py` | formula wheels as rational spans of relation vectors, with a certificate for every derivation; the ten wheels and 41 cases of the corrected study verbatim; dimensions read at three layers |
| `smith.py` | the Smith chart over Gaussian rationals; 16 checks; an exact L-section match over a rational band with a bypass candidate and ±5 % corners |
| `analogy.py` | the force-voltage and force-current analogies as maps on laws, a structure check, a scrambled control and a degeneracy guard |
| `delta_sigma.py` | periodicity by theorem; first-order, second-order and memoryless one-bit loops measured exactly through a `sinc^3` decimator; six checks declared before they were computed |
| `speak.py` | the question surface: seven frames, refusal with a reason, fall-through to the typed planner |
| `study.py` | the whole measurement, evidence envelopes in the record's recommended shape |

It is opt-in: `python3 GLM.py --eng -q "…"`, or
`GeometricSession.ask_engineering`. A question no engineering frame reads is
answered exactly as `ask_planned` answers it, so the surface only adds. The
default command line and the 177-case evaluation are unchanged.
`python3 -m glm_universal.tools engineering` prints every figure below.

## 3. Formula wheels — the register against the corrected study

A formula `cL·∏l = cR·∏r` is read as its relation vector (quantity
exponents, left minus right, plus the prime factorisation of `cL/cR`). It
follows from a wheel exactly when that vector is in the rational span of the
axioms' vectors, and the combination found is the certificate.

| layer | agrees with the preregistered expectation |
|---|---:|
| reference registry, SI policy | 41 / 41 |
| reference registry, explicit-angle policy | 41 / 41 |
| GLM register, SI7 | 41 / 41 |
| GLM register, EXT10 | 41 / 41 |
| derivability from the wheel's axioms | 41 / 41 |

All 41 cases are held by the register (six names through declared synonyms:
`volume_flow_rate` is `volumetric_flow`, `acoustic_pressure` is
`sound_pressure`, and so on). EXT10 plays the part of the corrected study's
experimental explicit-angle policy exactly: `angular_velocity = frequency` is
consistent at SI7 and inconsistent at EXT10 with residual `A^1`, as the study
expected. One register difference was found outside the cases: the register
gives `reduced_planck_constant` no plane-angle exponent where the reference
gives it `A^-1`; no case uses it, and it is recorded rather than changed.

**Generating wheels.** Solving for the combination that leaves only a target
and two named inputs produces the wheel rather than looking it up. The Ohm
wheel's two axioms generate all **12** textbook spokes, including the two
square-root ones (`voltage = (resistance * power)^(1/2)`,
`current = (power / resistance)^(1/2)`); the ten wheels generate **108**
spokes. Some are less familiar and still right —
`power = angular_acceleration * angular_momentum` for a rigid body on a fixed
axis, `power = acceleration * momentum` — because they are rational
consequences of the declared axioms and nothing else.

**Across wheels.** Asked of the union of all ten wheels' axioms, one case
changes: **W6-03**, `power = pressure * volume_flow_rate`, which the study
marks *not derivable* inside W6 (no hydraulic-power axiom), follows from W5's
`power = force * velocity` with W6's `force = pressure * area` and
`volume_flow_rate = area * velocity`. That is hydraulic power, derived by
composing two domains. The question surface keeps the study's per-wheel
protocol (the preregistered label is a refusal), and the cross-wheel reading
is reported here as a finding, not used to answer.

## 4. The Smith chart

`Z` and `Z0` are checked to share a dimension against the register before
`z = Z/Z0` is formed — a farad reference is refused, not normalised. Then
`Γ = (z − 1)/(z + 1)` over Gaussian rationals: **16 / 16** checks hold
(matched, short, real and complex loads, inverse, two round trips, admittance
duality, passive, lossless and active loads, reflected power, one resistance
and one reactance circle, and an exact VSWR). A VSWR is exact where `|Γ|` is
rational and is given as a closed radical otherwise; `|Γ| ≥ 1` is refused.

The exact L-section search (a series R-L-C load, 25 Ω, 20 nH, 2 pF, eleven
rational angular frequencies from 4.5 to 5.5 × 10^9 rad/s, 50 Ω, a 20-value
grid per component kind, 1601 candidates with the bypass) selects series L
5 nH, shunt C 3 pF, taking the worst `|Γ|²` from 3469/19669 (bypass) to
42365/290173; the ±5 % corners give 4788226353409/29569026353409. These are
ideal lumped components on a synthetic load, exactly as the record's own
limits say of its float version.

## 5. Electro-mechanical analogies

Each analogy is a map on quantity names with an exponent (spring constant ↦
capacitance⁻¹ under force-voltage), extended multiplicatively to formulas.
Structure is checked, not assumed: every axiom of one lumped wheel is
translated and tested for derivability in the other.

| dictionary | electrical → mechanical | mechanical → electrical |
|---|---:|---:|
| force-voltage | 9 / 9 | 9 / 9 |
| force-current | 8 / 9 | 8 / 9 |
| scrambled control (mass and damping images exchanged) | 4 / 9 | 4 / 9 |

Seven of the fifteen name pairs change dimension, so the check is about laws,
not a dimensional identity in disguise. The force-current failures are both
the quality factor: the electrical wheel's `Q = ω0 L / R` is the *series*
R-L-C one, and the mobility analogy maps a mass-spring-damper onto a
*parallel* circuit, whose `Q` is the reciprocal. The structure check found
the topology dependence by itself.

**A negative result, kept.** The first version of both wheels wrote the two
stored energies as one quantity, `energy`. With `voltage = current *
resistance` that forces `inductance = capacitance * resistance^2` — every
circuit critically tuned at `Q = 1` — and the surface's uniqueness check
refused to derive `Q` from `R, L, C` because the inputs had become dependent.
The energies were named apart (`magnetic_energy`, `electric_energy`,
`kinetic_energy`, `potential_energy`) and `analogy.degeneracy` now guards the
wheels against implying any relation between element parameters.

**Cross-domain answers.** A resonance, quality-factor or damping-ratio
question is derived twice: in the components' own wheel, and again after the
components are carried through the force-voltage analogy into the other
wheel. It is answered only when both routes give the same exact value
(`omega0 = 5 rad/s` for 4 kg on 100 N/m; `(1/2)^(1/2) rad/s` for 2 kg on
1 N/m). The two routes agree by `translate_derivable`; the check is kept
because a wrong dictionary entry would make them disagree.

An analogy left unnamed is ambiguous where the two dictionaries disagree —
*what is the electrical analogue of mass?* is refused with both readings
named — and answered where they agree (power is power).

## 6. Delta-sigma

Periodicity is decided by theorem rather than by looking:
`ds_bits_periodic_iff` proves that `P` is a period of the first-order
bitstream of `t ∈ [0,1)` exactly when `P·t` is an integer. So a rational
`p/q` in lowest terms has least period `q`, and an irrational input is never
periodic. The surface answers both from the theorem; `detect_period` is the
executable control.

The six checks declared in `delta_sigma.CHECKS` all hold (**6 / 6**): rational
DC 1/16 has period 16; triangular dither breaks it within the window;
`sqrt(2) − 1`, run with integer arithmetic only, shows no period; the
second-order loop's in-band error is below the first-order loop's; both
beat the memoryless baseline; and every second-order state stays within
`|x| ≤ 8`. In whole decibels by exact comparison, the second-order loop gains
at least 21 dB over the first on both tones, and the first gains at least
56 dB over the memoryless baseline.

**Two failed runs, recorded.** The fourth check failed on its first two runs,
both times for an implementation reason: the second integrator read the
*updated* first state (the wrong noise transfer), and then the in-band error
compared the output with the undelayed input (a loop's signal transfer is
`z^-1` or `z^-2`, and a pure delay was being scored as error). After both
corrections the check holds by a wide margin. The checks were not changed.

## 7. The language measurement

| set | questions | correct | wrong | refused | correct refusals |
|---|---:|---:|---:|---:|---:|
| wheels | 12 | 12 | 0 | 0 | 0 |
| checks | 6 | 6 | 0 | 0 | 0 |
| smith | 11 | 11 | 0 | 0 | 0 |
| analogy | 11 | 11 | 0 | 0 | 0 |
| delta-sigma | 5 | 5 | 0 | 0 | 0 |
| tricks | 10 | 0 | 0 | 0 | 10 |
| paraphrases | 8 | 8 | 0 | 0 | 0 |
| **all 63** | 63 | **53** | **0** | 0 | **10** |
| both existing paths, before | 63 | 0 | 0 | 53 | 10 |

The scoring rule is stricter than the earlier held-out sets': every group of
a label must appear, so a wheel answer that names one spoke of three is
wrong.

**The caveat that matters.** The 63 were committed before the code, but by
the same author, and the code was then written knowing them. The stress set
is the control for that: 38 hostile questions written after the first run
and committed before being run once. Its first run is frozen in
`STRESS_FIRST_RUN`: **27 correct, 10 correct refusals, 1 scored wrong, 0
refused**. The one scored wrong, `x-smith-cap`, is a scoring artifact: the
answer `Gamma = 1/5 - 2/5j` is right and the label's fragment `-2/5` does not
match the rendering `- 2/5j`. Neither the label nor the renderer was changed.

**It only adds.** Every question the machine already answers — the 177
contract cases, the frozen probe in both phrasings, the earlier held-out
sets, 374 in all — was offered to the engineering frames; none was read.

**D15.** Of the 53 correct answers, 48 are `derive` (a spoke solved from
axioms, a check at two layers, a reflection coefficient, a resonance through
two wheels, a period by theorem — no register holds any of them) and 5 are
`address` (a counterpart read off a declared dictionary). None is `table`.
On the stress set: 23 derive and 4 address.

## 8. What is proved

`RequestProject/GLM/EngineeringWheels.lean`, 11 theorems, no `sorry`, only the
standard axioms:

* `derivable_consistent` — a formula derived from dimensionally consistent
  axioms is consistent (so consistency is necessary for derivability);
* `ohm_power_derivable`, `ohm_negative_control_not_derivable` — `P = V²/R` is
  in the span of the Ohm axioms and `P = V·R` is not;
* `translate_derivable` — a linear translation sending every axiom into the
  target span sends every derivation there;
* `smith_round_trip`, `smith_admittance_dual`, `smith_passive`,
  `smith_lossless_iff` — the Möbius map, its inverse, duality, and the
  passive disc with its lossless boundary;
* `ds_bits_periodic_iff`, `ds_rational_period_iff`, `ds_irrational_aperiodic`
  — the periods of the first-order bitstream.

## 9. What is not claimed

* No Golay–Leech advantage. The surface reads the register's exact
  dimension vectors — the EXT10 and SI7 coordinates of the 24-coordinate
  physics carrier — and does its own exact algebra. Whether the Golay or
  Leech layers add anything to engineering reasoning is not measured here;
  the record's blind-ranking protocol (a `glm_score` column over the 3,370
  candidate table) is the way to measure it, and it needs the load model of
  the unsupplied extensions script.
* Monomial laws only. Sums, signs, phase, conjugation, dot and cross
  products and tensor contraction are outside the wheels, exactly as the
  record's Priority 5 says; `W2-03`'s *P, Q, S* ambiguity is untouched.
* Dimensional consistency is not physical truth, and derivability is relative
  to the declared axioms: the surface refuses what the axioms do not reach.
* The RF and delta-sigma models are idealised, as the record states of its
  own.

## 10. Verdict

Through the engineering surface the GLM answers every preregistered
engineering question it was asked and refuses every one whose right outcome
is a refusal, with no wrong answer, where both existing paths refused all of
them; the register agrees with the corrected formula study on all 41 cases
at both layers, and the rules that license the answers are proved.

## 11. Next

* The cross-wheel derivation of W6-03 suggests a second mode — derive across
  a *declared* union of wheels, with the union named in the answer — and a
  preregistered set to measure what it gains and what it gets wrong.
* Typed operators (the record's Priority 5): complex power with conjugation
  would let W2 separate *P*, *Q* and *S* instead of refusing.
* The blind ranking of the record's candidate table, once the load model is
  supplied.
