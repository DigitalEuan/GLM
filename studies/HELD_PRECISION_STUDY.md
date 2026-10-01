# Held precision — a register value's stated precision carried through a derivation

## Tier 0 — the coarse read

**Question.** When a register value feeds a formula-wheel derivation, what does its stated precision do to the answer, and can the GLM say so exactly?

**Verdict.** Every answered derivation that reads a register value now states the exact interval its answer lies in, carried from the precision the register wrote the value at; two chains are exact because the held value cancels, which step-by-step interval arithmetic would have missed. No verdict or value moved. From Phase 86 the two cancelling chains are refused, because they read a temperature level as a difference, and mark H3 is no longer met (§4).

**Deciding figure.** 8 of 39 goal and narrative chains read a register value and carry an exact interval; 2 exact because a held value cancels; 2 where step-by-step interval arithmetic is strictly wider; 5 of 5 marks met.

**Recomputed by.** `glm_universal.reasoning.held_precision.held_precision_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Candidate O of [`STATUS.md`](../STATUS.md) §3.4, item **O6**, named by
[`STEPWISE_TWO_STUDY.md`](STEPWISE_TWO_STUDY.md) §6: *a register value enters
the derivation as the exact rational the register holds; its stated precision
(the ordering frame's interval) is not carried through the wheels. An answer
derived from 77.36 K is exact for 77.36 and says nothing about 77.355.* The
stepwise planner answers *given mass = 2, specific heat capacity = 450 and
temperature = the melting point of iron, what is the energy* with `1629900`,
stated as if exact, when the register holds the melting point as `1811` — a
reading at the unit, which stands for anything in `[1810.5, 1811.5]`.

The precision reading already exists: `reasoning.intervals.Interval.as_held`
reads a held decimal at the places it was written to (half a unit of the last
place either side), and the ordering frame refuses a comparison when two such
intervals overlap (`GLM.CognitionRoundTwo.closed_overlap_iff`). What is
missing is carrying it through a chain of wheel steps.

## 1. Declarations — written before any code of this round

**The object.** Every wheel step is a monomial in its inputs (an axiom
`c₁ Π xᵢ^aᵢ = c₂ Π yⱼ^bⱼ` solved for a variable of power ±1), a step carried
into or out of SI multiplies by an exact positive factor, and a leaf is a
given, a measured amount or a register lookup. So the answer of a goal or
narrative chain is a single monomial `C · Π leafₖ^eₖ` in its leaves, with
integer exponents. Its range over a box of positive leaf intervals is exact
and attained at two corners (each leaf at its low or high end according to
the sign of its exponent). A leaf whose exponent is 0 has cancelled: its
precision does not reach the answer.

A register lookup is read at its stated precision (`Interval.as_held`); a
given or a measured amount is the number the question states, and is exact.

**H1.** Every answered goal or narrative chain of the stepwise corpora
(round one and round two) that reads a register value carries a precision
note stating the interval of its answer; a chain that reads none carries no
note.

**H2.** The interval is exact: the composite monomial at the held values
equals the chain's answer; both endpoints are values of the chain at a corner
of the held box (recomputed through the chain's own steps); and on the grid of
every leaf at its low end, middle and high end the chain's value never leaves
the interval.

**H3.** Dependency is handled, not ignored: the count of chains in which a
held value cancels (the answer is exact whatever the held value's precision),
and the count in which step-by-step interval arithmetic (each step's interval
from its inputs' intervals alone) is strictly wider than the exact interval.
Declared: at least one of each — `given mass = 2, specific heat capacity =
450 and temperature = the melting point of iron, what is the entropy` reads
the melting point twice, once into the energy and once dividing it out.

**H4.** Nothing else moves: every verdict and every value of the stepwise
corpora is unchanged; only a note is added.

**H5.** In Lean (`RequestProject/GLM/HeldPrecision.lean`): a monomial with
integer exponents over a box of positive intervals is bounded by, and attains,
its two corners; and there is a chain (`x · y / x`) on which step-by-step
interval arithmetic gives a strictly wider interval than the exact one. Builds
with no `sorry` and only the standard axioms.

## 2. Results

`glm_universal.reasoning.held_precision.held_precision_report` (and
`python -m glm_universal.tools held-precision`) recomputes everything below;
all arithmetic is exact rational.

**Summary.** Every answered derivation that reads a register value now states the exact interval its answer lies in, carried from the precision the register wrote the value at; two chains are exact because the held value cancels, which step-by-step interval arithmetic would have missed. No verdict or value moved.

| mark | declared | result |
|---|---|---|
| H1 | every register-reading chain carries a note, no other chain does | **met** — 8 of 39 goal and narrative chains read a register value; all 8 carry the note, the other 31 carry none |
| H2 | composite equals the answer, endpoints are corner values, the grid never leaves the interval | **met** on all 8 |
| H3 | at least one cancelled chain and at least one strictly-wider stepwise chain | **met** — 2 exact because a held value cancels; 2 where step-by-step interval arithmetic is strictly wider |
| H4 | nothing else moves | **met** — every verdict and value of both stepwise corpora unchanged (112 corpus questions); the stepwise test suites pass |
| H5 | Lean corner bound and a strictly-wider witness | **met** — `RequestProject/GLM/HeldPrecision.lean` builds with no `sorry`, standard axioms only |

5 of 5 marks met.

**The eight chains.**

| answer | exact interval | step-by-step interval |
|---|---|---|
| 1629900 (energy, melting point of iron) | [1629450, 1630350] | same |
| 2 | [7244/3623, 7244/3621] | same |
| 900 (entropy, melting point of iron) | [900, 900] — exact | [3258900/3623, 1086900/1207] |
| 97/100000000000 | [0.0000000009675, 0.0000000009725] | same |
| 3868/25 | [154.71, 154.73] | same |
| 12177/100 (energy in kilojoules, boiling point of oxygen) | [121.7025, 121.8375] | same |
| 3622 | [3621, 3623] | same |
| 900 (entropy, narrative form) | [900, 900] — exact | [3258900/3623, 1086900/1207] |

The entropy question reads the melting point of iron twice — once into the
energy, once dividing it out. Its composite monomial is `mass · specific heat`
with the looked-up temperature at exponent 0, so the answer is exact whatever
the register's precision; interval arithmetic step by step (each step from
its inputs' intervals alone) forgets that the two readings are the same
number and reports a spread of about half a unit. The chain's note now says
*exact: the melting point of iron cancels*.

**In Lean.** `monomial_corner_bounds` and `scaled_corner_bounds`: a monomial
`c · Π xᵢ^eᵢ` (c > 0, integer exponents) over a box of positive intervals lies
between its low and high corners, each of which is a point of the box
(`corner_mem`); `cancelled_leaf`: an exponent-0 leaf contributes 1;
`stepwise_strictly_wider`: on `x · y / x` with `x ∈ [1, 2]` and `y = 1`, the
chain is `1` everywhere, while step-by-step interval arithmetic gives
`[1/2, 2]`.

## 3. What this round moved

Against the standing target: **honesty of a derived answer**. An answer that
rests on a register value was stated as if exact; it now says how far the
register's own precision lets it move, and says *exact* only when that is
true. Nothing else the GLM answers changed.

**Not done.** Givens and measured amounts are still read as exact — the
question states them without a precision. A chain with a sum step (a
composition) is not a monomial and is not given a note; none of the 39
chains has one, but a future wheel might.

## 4. Addendum (Phase 86): H3 is no longer met

From Phase 86 the two cancelling chains are refused, because they read a temperature level as a difference, and mark H3 is no longer met.
The measurands round ([`MEASURANDS_STUDY.md`](MEASURANDS_STUDY.md)) gave the
stepwise planner kinds of quantity. `energy = mass * specific_heat_capacity *
temperature` reads a temperature *difference*; the melting point of iron is a
temperature *level*, which is a difference only from absolute zero. The four
goal and narrative chains that fed a register melting or boiling point to that
law (stepwise round two's g01, g03, g11 and m02) are now refused
`LEVEL_AS_DIFFERENCE`, and the corpus records each as an amended verdict with
its reason.

Both H3 witnesses were among them: the entropy question (g03, and its
narrative form m02) read the melting point of iron once as a difference into
the energy and once as a level dividing it out. The cancellation that made the
answer exact was the cancellation of a conflation — the answer 900 was the
entropy of heating from absolute zero at constant specific heat, which
diverges. The held-precision engine was right about the arithmetic; the chain
it was reading was wrong in kind.

Recomputed now (`tools held-precision`): 35 goal and narrative chains, 4 read
a register value, every one carries its note and its interval (H1, H2 met),
0 exact because a held value cancels and 0 where step-by-step intervals are
wider (H3 **not met**), H4 and H5 met. The Lean witness
`stepwise_strictly_wider` still stands as mathematics; the corpus no longer
holds a chain that exhibits it.

