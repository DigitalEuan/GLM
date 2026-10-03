# Typed operators: real, reactive and apparent power, and the dot against the cross product

## Tier 0 — the coarse read

**Question.** Can the machine keep apart quantities that share one dimension but are different products — real, reactive and apparent power from one pair of phasors, and the work (a dot product) against the torque (a cross product) of one pair of vectors — answering each exactly and refusing a unit of the wrong kind?

**Verdict.** Yes: real, reactive and apparent power, the power factor, the work and the torque are now separate typed operators, computed exactly from phasors, the power triangle or vectors, with each unit read as the kind it names, every declared case as declared and 0 wrong.

**Deciding figure.** 43 of 43 declared questions as declared (22 phasor, 9 kind, 12 vector), 0 wrong; through the router 0 before the round and 43 after; the naive monomial control answers 19 cases and 15 of them wrongly; 0 of 2971 earlier questions read; 43 of 43 scripts verified and 29 of 29 mutations rejected; 8 of 8 marks met.

**Recomputed by.** `glm_universal.runtime.typed_operators_report.typed_operators_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 3 of the order of work in [`ROADMAP_STUDY.md`](ROADMAP_STUDY.md):
candidate F of [`STATUS.md`](../STATUS.md) §3.4, *typed physical operators*,
named by Phase 59 ([`ENGINEERING_LANGUAGE_STUDY.md`](ENGINEERING_LANGUAGE_STUDY.md)):
monomial wheels cannot separate real, reactive and apparent power (the
record's `W2-03`), nor dot from cross product; complex power with
conjugation, over the Gaussian rationals the Smith chart already uses, is the
smallest step. Phase 86 ([`MEASURANDS_STUDY.md`](MEASURANDS_STUDY.md)) and
Phase 87 ([`MEASURAND_REGISTER_STUDY.md`](MEASURAND_REGISTER_STUDY.md)) gave
the machine kinds of quantity — the hertz is not for angular velocity, the
joule is not for torque — and this round extends the same reading to the
three powers: the watt, the var and the volt-ampere are one dimension and
three kinds.

Before this round, the stepwise planner answers *given voltage = 230 volts and
current = 2 amperes, what is the power* as 460 — right for direct current and
for nothing else — and reads no question with a phasor or a vector in it.

## 1. The objects

* **Complex power** from RMS phasors `V` and `I` (Gaussian rationals):
  `S = V * conj(I)`, with `P = Re S` (real power, watts), `Q = Im S`
  (reactive power, vars), `|S| = sqrt(P^2 + Q^2)` (apparent power,
  volt-amperes) and the power factor `P / |S|`, *lagging* when `Q > 0`,
  *leading* when `Q < 0`. Through an impedance: `S = |V|^2 / conj(Z) =
  |I|^2 Z`. The apparent power and the power factor are exact surds where
  `P^2 + Q^2` is not a rational square.
* **The power triangle**: two of `P`, `Q`, `|S|` and the power factor give
  the rest, except the *sign* of `Q`, which only *lagging* or *leading*
  fixes (refused `PF_SENSE_UNDECLARED` otherwise); a side longer than the
  hypotenuse is `POWER_TRIANGLE_VIOLATED`, a power factor outside `[-1, 1]`
  `POWER_FACTOR_OUT_OF_RANGE`.
* **Kind-restricted units**: the watt for real power only, the var for
  reactive power only, the volt-ampere for apparent and complex power only,
  each with its SI prefixes; anything else is `KIND_MISMATCH`, the code
  Phase 86 already uses.
* **Vector operators** on rational components: work `F · d` and mechanical
  power `F · v` are dot products (scalars); the torque `r × F` is a cross
  product (a vector in newton metres), its magnitude an exact surd. The
  joule–torque and newton-metre–energy restrictions are Phase 86's own.
  A cross product of vectors of unequal length is `VECTOR_LENGTH_MISMATCH`.
* A bare *power* asked of phasors is `AMBIGUOUS`: it could be any of three.

## 2. Declarations — written before any code of the round

The corpus is [`evaluation/typed_operator_cases.py`](../overlay/glm_universal/evaluation/typed_operator_cases.py),
43 questions: 22 phasor, 9 kind and 12 vector, with expected verdicts worked
by hand in exact fractions from the two conventions written at its head.

| mark | what it requires |
|---|---|
| T1 | every phasor case as declared, 0 wrong |
| T2 | every kind case as declared, 0 wrong |
| T3 | every vector case as declared, 0 wrong |
| T4 | the controls: the naive monomial control (magnitudes multiplied: `|V||I|` for every power, `|F||d|` for work, `|r||F|` for torque) answers at least 12 of the answered phasor and vector cases wrongly; with the typed reader off, the machine (through the router) answers none of the 43 as declared |
| T5 | nothing earlier moves: the typed reader recognises none of the questions of any earlier declared corpus, so no earlier routing can change |
| T6 | every answered reading's column-3 script verifies in a fresh interpreter, and a mutation of each (the asserted value moved by one) is rejected |
| T7 | the census: over every Gaussian integer `V`, `I` with parts in `[-3, 3]`, `P^2 + Q^2 = |V|^2 |I|^2` exactly and `|P| ≤ |S|`; over a grid of integer vectors, Lagrange's identity `|r × F|^2 + (r · F)^2 = |r|^2 |F|^2` and `r · (r × F) = 0` |
| T8 | the facts the round rests on proved in Lean, without `sorry` |

## 3. What was built

* [`runtime/typed_operators.py`](../overlay/glm_universal/runtime/typed_operators.py):
  the reader. Phasors are the Smith chart's own Gaussian rationals
  (`engineering.smith.GaussQ`); `complex_power` is `V * conj(I)`,
  `power_factor` returns an exact surd and its sense, `dot` and `cross` work
  on tuples of `Fraction`. `POWER_UNITS` declares the watt, the var and the
  volt-ampere (with kilo and mega) as kind-restricted names; the joule and
  the newton metre keep the restrictions of `runtime/measurands.py`, which
  this module reads rather than repeats. The power triangle is solved from
  any two of `P`, `Q`, `|S|` and the power factor, refusing the sign of `Q`
  when no sense is stated. `ACTIVE` switches the reader off for the control.
* Each reading carries Three Column Thinking. The column-3 script recomputes
  the answer from the givens by the textbook formula, component by component
  and with the standard library only, and asserts the claimed value. Because
  the claim is a parameter of `script_for`, a mutated claim yields a script
  that fails.
* In [`runtime/question_frames.py`](../overlay/glm_universal/runtime/question_frames.py):
  the frame `typed_operator`, tried before the planner's *given* phrasing is
  set aside — the planner reads no phasor, vector or typed power, so a
  question such as *given apparent power = 500 VA and power factor = 3/5
  lagging, what is the reactive power* reaches the frame through the router
  and `GLM.py -q`, gated like every other frame.
* The measurement `runtime/typed_operators_report.py`, the command
  `tools typed-operators`, `tests/test_typed_operators.py` and
  `RequestProject/GLM/TypedOperators.lean`. The non-interference test of
  `tests/test_question_frames.py` now skips this round's corpus, as it
  already skipped Phase 89's: these are the frames' own questions.

## 4. Results

Recomputed by `PYTHONPATH=. python3 -m glm_universal.tools typed-operators`.
Yes: real, reactive and apparent power, the power factor, the work and the
torque are now separate typed operators, computed exactly from phasors, the
power triangle or vectors, with each unit read as the kind it names, every
declared case as declared and 0 wrong. All eight marks are met.

| mark | result |
|---|---|
| T1 | met: 22 of 22 phasor cases as declared, 0 wrong |
| T2 | met: 9 of 9 kind cases as declared, 0 wrong |
| T3 | met: 12 of 12 vector cases as declared, 0 wrong |
| T4 | met: the naive monomial control answers 19 cases, 15 of them wrongly (a01, a02 and a03 all as 600; a06 as 20 where the reactive power is 0; a09 as 1058; a11 as 20 where the answer is -16; k05; v01, v03 and v04 as `7*sqrt(22)`; v02; v08 as 6 where the work is 0; v09 as 15 where the power is 11; v10 as 28 where the torque is 0; v12), against the declared floor of 12. The 4 it gets right are the apparent powers and the one perpendicular torque, which is where a product of magnitudes is the answer. With the typed reader off, the router sends all 43 to the planner and answers 0 of them as declared, and in fact answers none at all |
| T5 | met: 0 of 2971 questions read by the typed reader, drawn from 24 earlier corpora (every module of `evaluation/` but this round's, plus Set B and Outside O1), so no earlier routing can change |
| T6 | met: 43 of 43 column-3 scripts verified in a fresh interpreter; 29 of 29 answered readings' mutated claims rejected |
| T7 | met: 2401 phasor pairs with 0 violations of `P^2 + Q^2 = |V|^2 |I|^2` or `|P| ≤ |S|`; 7569 vector pairs with 0 violations of Lagrange's identity or of `r · (r × F) = F · (r × F) = 0` |
| T8 | met: `RequestProject/GLM/TypedOperators.lean`, no `sorry`, standard axioms only |

Through the router, the machine answered 0 of the 43 as declared before the
round and 43 after.

Three answers worth reading in full. *With phasor voltage V = 50 + 0j V and
phasor current I = 1 + 2j A, what is the power factor?* is `sqrt(5)/5`
leading, exactly: `S = 50 - 100j`, `|S| = 50 sqrt(5)`. *Given apparent power
= 500 VA and power factor = 3/5, what is the reactive power?* is refused
`PF_SENSE_UNDECLARED`. Both `+400` and `-400` var solve the triangle, and
only *lagging* or *leading* chooses between them. The same givens asked for
the real power give 300 W, because the sense does not matter there. *A force
F = (4, 5, 6) N acts at position r = (1, 2, 3) m; what is the magnitude of
the torque?* is `3*sqrt(6)` N m, where the monomial answer `|r||F|` is
`7*sqrt(22)`.

The Lean file proves what the round rests on:

* `power_triangle`: the triangle identity.
* `power_factor_mem`: a power factor lies in `[-1, 1]`, which is why the two
  range refusals are right.
* `complex_power_impedance` and `complex_power_admittance`: `S` through an
  impedance.
* `reactive_sign_undetermined`: why the sense is needed.
* `naive_real_power_wrong`: the monomial real power is wrong whenever
  `Q ≠ 0`.
* `lagrange_identity` and `naive_torque_wrong`: the monomial torque is right
  exactly when `r · F = 0`.
* `case_a01`: the corpus's first case.

## 5. What this round moved

**Derive.** Questions with a phasor, an impedance, a power triangle or a
vector in them are now read and answered exactly, where before every one fell
to the planner and was refused. **Refuse.** A unit of the wrong kind of power
is refused `KIND_MISMATCH`, the code Phase 86 introduced for torque and
energy. So are a reactive power whose sign the question leaves open, a side
longer than the hypotenuse, a power factor outside `[-1, 1]` and a cross
product of unequal lengths, each by name. A bare *power* of phasors is
`AMBIGUOUS`.

## 6. What this leaves

* **Phasors in polar form** (`230∠30°`) need an exact cosine. The reader takes
  rectangular phasors only. A polar phasor with a rational-cosine angle (0°,
  60°, 90°, ...) would be a small extension.
* **Three-phase power** (`S = 3 V_ph conj(I_ph)`, or `sqrt(3) V_L I_L` with
  a surd) and **power-factor correction** (the capacitor that brings a
  lagging load to a target power factor) are the next widenings of the same
  algebra.
* **The planner's own power**: *given voltage = 230 volts and current = 2
  amperes, what is the power* is still answered 460 by the planner, correct
  for direct current. A question that says *alternating* with magnitudes only
  could be refused for an undeclared phase angle. That would change an earlier
  verdict, so it is the owner's call and is not taken here.
* **The verifier's rank algebra** (`reasoning/verifier.py`) already separates
  `dot` from `moment` by tensor rank on the dimension side. Joining it to the
  value side, so that a relation's rank audit and its typed value come from
  one declaration, is open.
* Track 1 continues with **C + H1**, the register against the world
  ([`ROADMAP_STUDY.md`](ROADMAP_STUDY.md) §4, round 6). The next round in the
  order is round 4, the planner widenings.
