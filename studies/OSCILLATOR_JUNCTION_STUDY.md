# The oscillator junction: which angular quantity an oscillator shares, tried four ways

## Tier 0 — the coarse read

**Question.** The junction between wave kinematics (W9) and the mass-spring oscillator (W13) joins `frequency` and `angle`, and through the older junction between rotational mechanics and waves (W4/W9) it makes an oscillator's angular frequency the angular velocity of any rotating body; tried four ways under one declared rule, which junction keeps every declared answer and gives no answer that ties an oscillator to a rotating body it was never said to be coupled to?

**Verdict.** Of four junctions between wave kinematics and the mass-spring oscillator, the one that joins `frequency` only and splits `angle` (B, rate only) is chosen by the declared rule and now ships: it keeps all 21 declared answers and 9 refusals and every one of the 249 answers the shipped frame gave on the preservation set, and its census has no answer tying the oscillator to a rotating body, where the Phase 157 junction (A) gave 6; the reference circle read literally (D) also removes them but loses 8 shaft-power answers of Phase 66, and keeping the wheels apart (C) loses 4 declared answers; the price of B is the reference-circle identity itself, which it no longer derives.

**Deciding figure.** B chosen: O1, O2, O3 met (O4 met); not-entailed oscillator answers A 6, B 0, C 0, D 0; preservation lost A 0, B 0, C 0, D 8 of 249; battery answered A 21, B 21, C 17, D 21 of 23.

**Recomputed by.** `glm_universal.engineering.oscillator_junction.report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 158 (§§0–6 are committed before the variant
module is written and before any variant is measured; §7 is what came out).
It takes the second half of `STATUS.md` To-Do item 5, left by Phase 157
([`DOMAIN_WHEELS_STUDY.md`](DOMAIN_WHEELS_STUDY.md) §7.3, §7.5): the census of
the fifteen-wheel union showed that the W9/W13 junction does the most work of
any new junction, and that much of that work is not among the declared laws.
The owner's note for this round: *the junction will likely just take some
experimentation to see what works best*. So this round does not argue for one
junction; it declares four, one rule for choosing among them, and measures.

**The method, by analogy.** This round uses the technique the owner set out
with the friction study (see [`FRICTION_STUDY.md`](FRICTION_STUDY.md) §8): take
a well-established mathematical system, and apply it in the way that works for
the GLM. The established system here is the **reference circle** of classical
mechanics: simple harmonic motion is the projection of uniform circular motion,
so an oscillator's angular frequency *is* an angular velocity — the angular
velocity of its own reference phasor, turning once per period. The analogy
says what may be shared across the junction (the rate of the phasor, the turn
it makes, the frequency it drives a wave at) and what may not (the angular
velocity of some other rotating body, a flywheel or a shaft, which the
oscillator turns with only if something couples them). The four variants are
four ways of writing that boundary into the junction table.

## 1. What is built

* `overlay/glm_universal/engineering/oscillator_junction.py` — the four
  variant junction tables, the split system for each (the rule of
  `engineering/domains.py`, which it reads and does not modify), the battery,
  the preservation set and the census for each variant, the grading of §2.3
  and the choice of §2.4.
* `python3 -m glm_universal.tools oscjunction [--census] [--write]` — the
  instrument; the per-variant censuses are stored in
  `engineering/_data/oscillator_junction.json` beside the digest of the code.
* `RequestProject/GLM/OscillatorJunction.lean` — what is proved (§5).

## 2. The rules, fixed before the measurement

### 2.1 The four variants

Every variant keeps the fifteen wheels, the Phase 66 junctions and the other
nine junctions of Phase 157 exactly as they are, and changes only what is
listed.

| variant | change | reading |
|---|---|---|
| **A** `turn_and_rate` | none: W9/W13 joins `frequency` and `angle` | as shipped by Phase 157 — the control |
| **B** `rate_only` | W9/W13 joins `frequency` only; `angle` is split | the oscillator drives the wave at its frequency; the turn it is measured against is its own |
| **C** `apart` | no W9/W13 junction | the oscillator and the wave share nothing |
| **D** `reference_circle` | W9/W13 joins `frequency` and `angle`, and the W4/W9 junction of Phase 66 is not used in the fifteen-wheel union | the reference circle read literally: the oscillator's angular frequency is the wave's phase rate, and a rotating body reaches neither |

The frame (*derive X from Y … across domains*) and the census are computed
for each variant with that junction table; nothing else moves.

### 2.2 The three sets each variant is measured on

1. **The battery**: the 32 declared questions of `evaluation/domain_cases.py`
   (23 to answer, 9 to refuse), read by the frame's own parser, compared as
   Phase 157 compares them (relations up to a positive rational multiple).
2. **The preservation set**: every question that the shipped frame (variant A)
   answers among (i) every two-input question over the names of the ten
   wheels of Phase 66, and (ii) every three-input question over the names of
   W4 and W9. A variant **keeps** such a question when it answers it with the
   same relation.
3. **The census**: the census of the union of
   [`DOMAIN_WHEELS_STUDY.md`](DOMAIN_WHEELS_STUDY.md) §2.5, every two-input
   question over the names of the fifteen wheels, taken with the variant's
   junction table. Its gained rows are read as in that study's post-hoc
   reading (`engineering/domains_reread.py`): a one-wheel answer is in-wheel,
   and a label matches up to any non-zero multiple.

### 2.3 The grading of an oscillator answer

A gained census answer is **oscillator-attributable** when W13 is among the
wheels it uses. Each distinct oscillator-attributable answer is graded:

* **not entailed** when it also uses W4 (rotational mechanics): it then
  relates the oscillator to a rotating body's torque, moment of inertia,
  angular momentum or shaft power, and nothing in the question says the body
  and the oscillator are coupled. The reference circle licenses the phasor's
  angular velocity, not a flywheel's;
* **entailed** otherwise: it uses only the oscillator, the wave it drives (W9),
  the photon at that frequency (W10) or the dynamic body (W5), which are the
  objects the declared junction reasons name.

Of the entailed answers, those that match a declared label are counted
separately. Labels are not added in this round: declaring the rotational chain
as laws (the other option `STATUS.md` named) would make the chain right by
fiat, and the grading above is the reason it is not taken.

### 2.4 The marks and the choice

| # | mark | pass |
|---|---|---|
| O1 | battery | the variant answers the same 21 questions with the declared formula as A, refuses all 9 declared refusals, and gives no wrong answer |
| O2 | preservation | the variant keeps every question of the preservation set |
| O3 | no rotor | the variant's census has no not-entailed oscillator answer |
| O4 | proved | `OscillatorJunction.lean` holds the theorems of §5 with no `sorry` |

**The choice.** Among the variants that meet O1 and O2, the one with the
fewest not-entailed oscillator answers; a tie is broken by more distinct
entailed oscillator answers that match a label, then by fewer junction names.
If the chosen variant is not A, the frame ships it: `DOMAIN_JUNCTIONS` (or the
fifteen-wheel union's use of Phase 66's table) is changed to it, the Phase 157
census is re-taken under it and stored, and the evaluation is run before and
after. If no variant meets O1 and O2, A stays and the finding is recorded.

## 3. What would count against

* Every variant that removes the rotor chain also loses a declared answer (O1)
  or a shipped answer (O2): the junction cannot be cut where the analogy says
  without a cost the frame's users would see.
* B or D gives a new kind of undeclared answer the census of A did not show.

## 4. What is not claimed

* The grading of §2.3 is a declared rule about which objects the junctions
  speak of, not a theorem of physics; a crank-driven oscillator does turn with
  its flywheel, and a frame that says so could license the chain.
* The census is over two-input questions, as in Phase 157; the preservation
  set adds three-input questions only around W4 and W9.
* The labels are those of Phase 157, unchanged.

## 5. What is proved before the measurement

`RequestProject/GLM/OscillatorJunction.lean`, over W4 (rotational mechanics),
W9 (wave kinematics) and W13 (the oscillator):

* **the rotor chain** — with W4/W9 joining `angular_velocity` and W9/W13
  joining `frequency` and `angle` (variant A), `angular_frequency * torque =
  power` is derivable (`rotor_chain_turn_and_rate`);
* **cut by splitting the angle** — with `angle` split across W9/W13 (variant
  B), a linear functional vanishing on every axiom certifies that it is not
  (`rotor_chain_refused_rate_only`);
* **the wave's period survives** — under B, `wave_speed * period = wavelength`
  is still derivable (`wave_period_rate_only`);
* **cut by leaving the rotor out** — with W4/W9 not used (variant D), the
  chain is refused (`rotor_chain_refused_reference_circle`) while
  `angular_frequency = angular_velocity` (the reference circle) is derivable
  (`reference_circle_identity`).

## 6. Files

See §1. Tests: `overlay/glm_universal/tests/test_oscillator_junction.py`.

## 7. What came out

Taken in this order, all after the commit of §§0–6: the battery of each
variant (seconds), the preservation set (24150 questions, 249 of them answered
by the shipped frame; minutes), and the four censuses side by side (about half
an hour each). Variant A's census reproduces the stored Phase 157 census
exactly under the post-hoc reading (116 gained, 104 right), which checks that
the variant system is the shipped one. Then B was shipped, the four
measurements were re-taken and stored with the digest of the shipped code
(`python3 -m glm_universal.tools oscjunction --write`), the Phase 157 census
was re-taken under B (`python3 -m glm_universal.tools domains --write`), and
the evaluation was run before and after the change.

**Verdict.** Of four junctions between wave kinematics and the mass-spring oscillator, the one that joins `frequency` only and splits `angle` (B, rate only) is chosen by the declared rule and now ships: it keeps all 21 declared answers and 9 refusals and every one of the 249 answers the shipped frame gave on the preservation set, and its census has no answer tying the oscillator to a rotating body, where the Phase 157 junction (A) gave 6; the reference circle read literally (D) also removes them but loses 8 shaft-power answers of Phase 66, and keeping the wheels apart (C) loses 4 declared answers; the price of B is the reference-circle identity itself, which it no longer derives.

### 7.1 The four variants

| variant | battery (of 23 / of 9) | preservation lost (of 249) | gained, re-read | right | not-entailed oscillator answers | entailed, labelled | entailed, other | O1 | O2 | O3 |
|---|---|---|---|---|---|---|---|---|---|---|
| A `turn_and_rate` | 21 / 9 | 0 | 116 | 104 | 6 | 11 | 3 | met | met | missed |
| B `rate_only` | 21 / 9 | 0 | 15 | 12 | 0 | 9 | 0 | met | met | met |
| C `apart` | 17 / 9 | 0 | 6 | 3 | 0 | 0 | 0 | missed | met | met |
| D `reference_circle` | 21 / 9 | 8 | 110 | 104 | 0 | 11 | 3 | met | missed | met |

No variant gives a wrong battery answer; d16 and d17 (which energy) are
refused as ambiguous by all four, as in Phase 157.

* **A, as shipped by Phase 157.** The 6 not-entailed answers are the rotor
  chain: `angular_frequency = power / torque`, `angular_frequency =
  angular_momentum / moment_of_inertia` and their rearrangements, each across
  W4+W9+W13. The 3 entailed but unlabelled answers are the spring law read
  through the wave's angular velocity (`spring_constant = angular_velocity^2 *
  mass` and two rearrangements).
* **B, rate only.** The rotor chain is gone and so is every other answer
  through `angular_velocity`'s link to the oscillator; the 9 entailed answers
  that remain all match a label — the wave's period (`wavelength = period *
  wave_speed` and its rearrangements), the photon's period (`energy =
  planck_constant / period` and its rearrangements) and one turn per period
  (`angular_velocity = angle / period` and its rearrangements, through W9's
  own angle and W13's period across the frequency junction). The 3 rows that
  are still wrong under the labels are the RC time constant (`time =
  capacitance * resistance`, W1+W3+W15), which does not touch the oscillator.
* **C, apart.** The wave's period, a photon's period and one turn per period
  are refused: d09, d18, d19 and d23 of the battery.
* **D, reference circle.** The rotor chain is gone and the identity
  `angular_frequency = angular_velocity` survives, but the eight three-input
  answers of Phase 66 that run a rotating body through a wave's angle and
  frequency (`power = angle * frequency * torque`, `angular_momentum = angle *
  frequency * moment_of_inertia` and their rearrangements, across W4+W9) are
  refused.

### 7.2 The choice (§2.4)

O1 and O2 are met by A and B; of the two, B has 0 not-entailed oscillator
answers against A's 6. **B is chosen** and ships: `DOMAIN_JUNCTIONS` joins
W9/W13 at `frequency` only, and `DOMAIN_NON_IDENTITIES` holds the split angle
with its reason (the oscillator's own reference turn against the wave's phase
turn, which W4/W9 makes a rotating body's). O1, O2, O3 and O4 are met by B.

### 7.3 What B costs, read through the analogy

The reference circle says the oscillator's angular frequency is an angular
velocity — of its own phasor. B does not derive that identity any more: asked
*derive angular frequency from angular velocity across domains*, the frame
refuses, and the spring law read through the wave's angular velocity is gone
with it. Those answers are entailed by the analogy (D keeps them), so B is the
safer of the two junctions that pass the marks, not the more complete.

The measurement also says what the defect in A actually is. Phase 66's
W4/W9 junction reads a wave's angular velocity as that of the rotating body
that drives it; Phase 157's W9/W13 junction reads the wave's frequency and
turn as those of the oscillator that drives it. Both junctions name *the
wave's source*, and the union's junctions are transitive, so with both in
place the rotating body and the oscillator become one source — which is the
rotor chain. D keeps the oscillator as the source and drops the rotating
body; B keeps the rotating body's link and lets the oscillator share only the
frequency. Neither can keep both readings, because which body drives the wave
is a fact about the question, not about the wheels (§7.6).

### 7.4 Frozen path, the Phase 157 census re-taken, proofs (O4 met)

The evaluation after the change gives every one of the 222 cases the same
outcome and the same answer line as before it (222 of 222 both times; stored
as `engineering/_data/oscillator_junction_frozen.json`). The Phase 157 census
of the union, re-taken under B and stored in `engineering/_data/domains.json`,
reads 99 gained rows (84 of them one-wheel answers and 15 gained under the
post-hoc reading, 12 of them right); its D3 stays missed, as declared by that
study's rule. `RequestProject/GLM/OscillatorJunction.lean` builds with no
`sorry` and uses only the standard axioms: `rotor_chain_turn_and_rate`,
`rotor_chain_refused_rate_only` (the functional angular frequency plus W13's
angle plus twice the spring constant vanishes on every axiom of B),
`wave_period_rate_only`, `rotor_chain_refused_reference_circle` and
`reference_circle_identity`.

### 7.5 The method

This round used the analogy method of
[`FRICTION_STUDY.md`](FRICTION_STUDY.md) §8 deliberately: a well-established
system (the reference circle) was mapped part by part onto the junction table,
each mapping became a variant, and the analogy's own boundary (a phasor is not
a flywheel) became the grading rule of §2.3, written before the measurement.
The analogy picked out the defect (A's rotor chain) and both repairs (B and
D); the measurement, not the analogy, decided between them.

### 7.6 Left open

* **Which body drives the wave.** A frame that says which body is the
  wave's source (a rotating body, or the oscillator) would let the union use
  W4/W9 or the full W9/W13 junction for that question alone, keeping the
  reference circle identity and Phase 66's shaft-power answers without the
  rotor chain — the same shape of fix as *which energy* in Phase 157. It
  needs a question form the battery and the census do not have.
* **A coupled oscillator.** A frame that says the oscillator is driven by (or
  drives) a rotating body would license the rotor chain for that question;
  the census has no such question form.
* **Which energy**, the RC time constant and the census code against its
  words stay as [`DOMAIN_WHEELS_STUDY.md`](DOMAIN_WHEELS_STUDY.md) §7.5 left
  them.
