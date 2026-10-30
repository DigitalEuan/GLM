# Contextual domain frames — the question says which energy, and which body drives the wave

## Tier 0 — the coarse read

**Question.** Can a question say the context a shared name is meant in — whether an energy is stored or delivered, which oscillator is meant, whether a rotating body drives the wave — so that the domain wheels recover the relationship the union refuses, without identifying the quantities globally and without changing any answer given without a context?

**Verdict.** Yes. A question can now say which energy is meant, which oscillator, and whether a rotating body drives the wave. Energy from power and time is answered as `energy = power * time` when the energy is delivered over a time and as half of that when it is stored in a capacitor; the source's energy `charge * voltage` and the capacitor's `1/2 * charge * voltage` are told apart the same way; with a rotating body driving the wave, the reference-circle identity and the rotor chain come back. No answer given without a context moved, and over 16,215 questions no pin changed an answer — as Lean proves it cannot. One mark was missed on a mis-written expectation, not on an answer.

**Deciding figure.** 8 of 9 marks (X5 missed as written, X5′ met); 10 of 10 theorems, 0 `sorry`; battery 21 of 23 and 9 of 9 with and without the rotating-body join, 0 wrong; census 16,215 questions, 0 answers changed by a pin, 12 ambiguities resolved by each of the two energy pins; 4 of 4 declared refusals; evaluation 223 of 223.

**Recomputed by.** `glm_universal.reasoning.frame_plane_study.frame_plane_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 20 October 2026 (pre-registered 20 October 2026: §§0–6 were committed before the measurement of §7 was taken; measured 20 October 2026).*

## 0. What this document is

A pre-registration for Phase 170. It takes Part II.3 of the owner's plan of
19 October 2026 ([`source_material/GLM_19OCT26_1.md`](../source_material/GLM_19OCT26_1.md),
*add contextual domain frames*) and with it To-Do item 5 of `STATUS.md` §2.1
(*the domain wheels, the rest*): *which energy*
([`DOMAIN_WHEELS_STUDY.md`](DOMAIN_WHEELS_STUDY.md) §7.5) and *which body
drives the wave* ([`OSCILLATOR_JUNCTION_STUDY.md`](OSCILLATOR_JUNCTION_STUDY.md)
§7.6). The plan asks that the question be able to specify which object is
measured, which body drives a wave, whether an oscillator is coupled to a
rotating body, whether energy is stored or delivered, and which physical
interpretation of a shared name is intended — recovering useful relationships
without globally identifying quantities that are only conditionally related.

**What was known when this was written.** The module and the frame were
written first and tried on the questions they were written for, to see that
they ran: with *the energy is delivered over a time*, energy from power and
time answers `energy = power * time` and power from energy and time
`power = energy / time`; with *the energy is stored in a capacitor* they
answer `energy = 1/2 * power * time` and `power = 2 * energy / time` through
W1, W3 and W15; with *the energy is stored in an inductor* energy from power
and time is refused; with *a rotating body drives the wave* angular frequency
from angular velocity answers `angular_frequency = angular_velocity`. Those
six outcomes were seen. Nothing else of §4 was run: not the battery under
either reading, not the rotor chain, not the refusal probes other than the
inductor, and not the census of X6.

## 1. The contexts

`glm_universal/engineering/context_frames.py`. A question may end
*across domains where* followed by one or more declared context phrases
(joined by *and* or a comma). Six contexts are declared, each with its
phrasings and its reason (`CONTEXTS`):

| context | phrasing (one of) | what it does |
|---|---|---|
| `energy-delivered` | *the energy is delivered over a time* | pins `energy` to W15 |
| `energy-stored-capacitor` | *the energy is stored in a capacitor* | pins `energy` to W3 |
| `energy-stored-inductor` | *the energy is stored in an inductor* | pins `energy` to W14 |
| `oscillator-spring` | *the oscillator is a mass on a spring* | pins `angular_frequency` to W13 |
| `oscillator-lc` | *the oscillator is an lc circuit* | pins `angular_frequency` to W14 |
| `rotating-drive` | *a rotating body drives the wave* | joins `angle` across W9/W13 for this question |

A **pin** keeps only the copies of the named quantity whose junction class
holds the named wheel; a **join** adds one junction to the union for this
question only. The fifteen-wheel union is never modified, and a question
without a `where` clause is answered by `domains.derive_domains` as before.
The rule that decides is the domains frame's: every remaining copy is tried,
and the answer is given only when every derivation found agrees.

The declared refusals: a phrase that is not declared is refused, never
guessed; a pin on a quantity the question does not ask about is refused; two
pins that say different things about one quantity are refused; a frame in
which no derivation remains is refused.

## 2. The formal half

`glm_lean/RequestProject/GLM/ContextFrames.lean`:
`pin_never_changes`, `pin_answer_mem`, `pin_same_answer` (a pin only removes
candidates, so it never changes an answer); `delivered_energy`,
`stored_energy_half`, `stored_energy_not_full` (the two readings of the
energy are both derivable in their frames and are different relations);
`reference_circle_joined`, `reference_circle_split` (the identity derivable
with the join, refused without it), with the two witnesses' vanishing lemmas.

## 3. Faculties

**Derivation — moved.** Questions the union refused as ambiguous, or could
not derive, are answered in a declared frame. **Refusal — kept**, and
sharpened: an undeclared context is refused by name. **Not addressing.**

## 4. The marks

| mark | met when |
|---|---|
| **X1** | `ContextFrames.lean` declares the ten theorems of §2 with no `sorry` and builds |
| **X2** | without a context nothing moves: the domain battery gives 21 of 23 declared laws, refuses 9 of 9, 0 wrong, as before; and the end-to-end evaluation has no failure (223 of 223) |
| **X3** | with *the energy is delivered over a time*, energy from power and time and power from energy and time give the declared laws (`energy = power * time`, `power = energy / time`) |
| **X4** | with *the energy is stored in a capacitor* both answer, through W3, with a relation different from X3's; with *the energy is stored in an inductor* energy from power and time is refused |
| **X5** | with *a rotating body drives the wave*, angular frequency from angular velocity and its reverse give `angular_frequency = angular_velocity`, and angular frequency from power and torque gives `angular_frequency = power / torque` (the rotor chain, right for a body that drives the wave); without the context both are refused |
| **X6** | over every two-input question on the fifteen wheels' names that a pinned name enters (as target or input), under each pin context: no question answered without the context is answered differently with it |
| **X7** | the domain battery with *a rotating body drives the wave* appended to every question grades exactly as without it: the join moves nothing the battery asks |
| **X8** | four probes are refused with a reason: an undeclared phrase (*the energy is warm*); a pin on a quantity not asked (density from mass and volume, *delivered over a time*); two pins that disagree (*delivered over a time* and *stored in a capacitor*); a frame with no derivation (spring constant from mass and angular frequency, *the oscillator is an lc circuit*) |

## 5. What would count against

X6 missed would mean a pin changed an answer, which `pin_same_answer` says
cannot happen if the code does what the theorem describes: the code would be
wrong. X7 missed would mean the rotating-body join reaches questions that do
not ask about a rotating body. X4's inductor refusal missed would mean a
frame invents a route.

## 6. What is not claimed

The contexts are declared, not read from free text: a context said in other
words is refused. The stored-energy answer is the energy after a steady
current has charged the capacitor, with `power` the power at the final
voltage; the frame names its reading and its certificate but does not say
that in words. The join is one junction; other couplings (a wave driving an
oscillator, an LC circuit driven by a generator) are not declared. The
contexts are read by the engineering surface only; the planner's other
surfaces do not offer them.

## 7. What came out

`PYTHONPATH=. python3 -m glm_universal.tools context-frames` (stored in
`engineering/_data/context_frames_study.json`, digest-guarded over the Lean
file, the module, the domain wheels, the engineering surface and the domain
battery; `--write` re-takes it in about four minutes on eight processes).

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **X1** | 10 of 10 theorems, 0 `sorry`; `lake build RequestProject.GLM.ContextFrames` passes; standard axioms | yes |
| **X2** | battery 21 correct, 9 correct refusals, 2 refused (d16, d17, as before), 0 wrong; evaluation no failures (223 of 223) | yes |
| **X3** | `energy = power * time`; `power = energy / time` (both W15) | yes |
| **X4** | `energy = 1/2 * power * time`, `power = 2 * energy / time` (W1+W3+W15), a different relation from X3's; the inductor's energy from power and time refused | yes |
| **X5** | x5a `angular_frequency = angular_velocity`, x5c `angular_frequency = power / torque`, x5d and x5e refused without the context; x5b answered `angular_velocity = angular_frequency` and graded **wrong** against the declared `angular_frequency = angular_velocity` | **missed** |
| **X5′** | the same, with x5b's law written for its own target (amendment) | yes |
| **X6** | 16,215 questions; 0 answered questions answered differently under a pin | yes |
| **X7** | the battery with *a rotating body drives the wave* appended grades exactly as without it (0 moved) | yes |
| **X8** | 4 of 4 refused, each with its reason | yes |

**X5, and its amendment.** The domains frame compares a relation with the
declared law up to a *positive* multiple, so the law must be written with the
question's target on the left; x5b asks for the angular velocity, and the
pre-registration gave it x5a's equation. The answer is the identity, read the
other way. X5 is reported missed as written; X5′, written after the first
take and named here as such, grades x5b against
`angular_velocity = angular_frequency` and is met.

### 7.2 What the pins do over the census

Every two-input question on the fifteen wheels' names that a pinned name
enters, under each of the five pin contexts:

| context | ambiguous → answered | answered → same answer | answered → refused | ambiguous → refused | refused → refused |
|---|---|---|---|---|---|
| `energy-delivered` | 12 | 2 | 24 | 0 | 3,205 |
| `energy-stored-capacitor` | 12 | 2 | 24 | 0 | 3,205 |
| `energy-stored-inductor` | 0 | 5 | 21 | 12 | 3,205 |
| `oscillator-spring` | 0 | 11 | 9 | 0 | 3,223 |
| `oscillator-lc` | 0 | 11 | 9 | 0 | 3,223 |

No row has an answer that changed, which is `pin_same_answer` seen in the
code. The two energy pins resolve the same twelve ambiguities, in opposite
ways, and every pair is the distinction the context names: energy from
charge and voltage is `charge * voltage` delivered (W1+W15, the source's work,
one of Phase 157's declared laws) and `1/2 * charge * voltage` stored (W3);
from capacitance and voltage, `capacitance * voltage^2` against
`1/2 * capacitance * voltage^2`; time from energy and power, `energy / power`
against `2 * energy / power`. The *answered → refused* rows are questions
answered through another wheel's energy (a moving body's, a photon's, a
heated body's) that the pin says is not the energy meant: a pin removes
readings, and an answer that rested on a removed reading is withdrawn, not
replaced. The inductor pin resolves nothing from a power and a time and says
so.

### 7.3 What the join does

With *a rotating body drives the wave* the angle is one quantity across
W9/W13 for that question only, and the identities Phase 158 removed from the
union come back where they are asked for: `angular_frequency =
angular_velocity` both ways and the rotor chain `angular_frequency = power /
torque`. Appended to every question of the battery, the join moves none of
them: a question that does not involve the angle is not reached. The union
itself is untouched, and without the clause both identities are refused, as
`reference_circle_split` proves they must be.

### 7.4 Faculties

**Derivation — moved**: 12 questions refused as ambiguous now answer, each
in two named frames, and the two identities the oscillator junction gave up are
derivable where the question licenses them. **Refusal — kept and sharpened**:
an undeclared context, a context about a quantity not asked, and two contexts
that disagree are refused by name. **Not addressing.**

### 7.5 What is left

* The contexts are six declared phrases; a context said in other words is
  refused. Reading them through the language descriptions' slot shapes would
  let the parser carry them.
* The stored energy's reading (a steady current, `power` at the final
  voltage) is in the certificate but not said in words.
* Other couplings are not declared: a wave driving an oscillator, a generator
  driving an LC circuit, a heated body's energy against a moving body's.
* The census's own code still reads its declaration more narrowly than its
  words, and the naive control is still taken over all fifteen wheels at once
  (To-Do item 5's last line, untouched here).
* The contexts reach the engineering surface only: the planner and the
  conversation do not offer them, and a `nearest` tie does not yet ask which
  energy is meant.

## In one paragraph

Yes. A question can now say which energy is meant, which oscillator, and whether a rotating body drives the wave. Energy from power and time is answered as `energy = power * time` when the energy is delivered over a time and as half of that when it is stored in a capacitor; the source's energy `charge * voltage` and the capacitor's `1/2 * charge * voltage` are told apart the same way; with a rotating body driving the wave, the reference-circle identity and the rotor chain come back. No answer given without a context moved, and over 16,215 questions no pin changed an answer — as Lean proves it cannot. One mark was missed on a mis-written expectation, not on an answer.

The figures: 8 of 9 marks (X5 missed as written, X5′ met); 10 of 10 theorems, 0 `sorry`; battery 21 of 23 and 9 of 9 with and without the rotating-body join, 0 wrong; census 16,215 questions, 0 answers changed by a pin, 12 ambiguities resolved by each of the two energy pins; 4 of 4 declared refusals; evaluation 223 of 223.
