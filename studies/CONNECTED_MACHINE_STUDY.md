# The connected machine: one question path, every tool on it, and derivation across wheels

## Tier 0 — the coarse read

**Question.** Can one question path reach every working surface of the GLM without a flag, and can the engineering surface derive across a union of formula wheels without the wrong answers that naive composition gives?

**Verdict.** Yes, on every declared mark: one path now can route to the toolbox, the Python dialect, the engineering surface and the planner without a flag, and all 177 contract cases stay with the planner; the eight unreached modules are reachable as tools; and the union mode answers the 3 physically correct cross-wheel derivations and refuses the other 158 that naive composition gets wrong.

**Deciding figure.** 136 more declared questions answered correctly on the default path (53 engineering, 83 Python) with 0 wrong added; 0 of 96 reasoning modules unreached; naive union 3 right and 158 wrong against the licensed union's 3 right and 0 wrong.

**Recomputed by.** `glm_universal.runtime.router.connected_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

The owner, opening the round:

> *My input at this stage is to experiment with the concepts and find if there
> is a way to obtain increased GLM capability and to ensure the working parts
> are connected and available to the GLM as needed.*

Two things in the tree stand in the way of *connected and available*:

* **The surfaces are reached by flag, not by the question.** `GLM.py -q`
  reads through the typed planner and the grammar. The engineering surface
  needs `--eng`, the Python dialect (and through it the carried fork of
  Phase 65) needs `--python`. A question the machine can answer is refused
  when the caller picks the wrong flag: the default path answers none of the
  53 answerable engineering questions and none of the 83 Python programs.
* **Eight tested reasoning modules are reached by nothing.** The wiring audit
  (`python3 studies/scripts/wiring_audit.py`, candidate 3 of
  [`STATUS.md`](../STATUS.md) §3.4) finds `deep_dive`, `llvq`, `moonshine`,
  `pcgs`, `salvage`, `salvage_second`, `stability` and `tie_break` outside
  the import closure of every entry point. Each has a test file, a study and a
  Lean specification.

And one thing stands in the way of *increased capability* that the last
engineering round named itself (candidate E): the surface derives inside one
wheel at a time, so it refuses *derive power from pressure and volume flow
rate* although the union of the linear-dynamics and fluid wheels licenses it.

## 1. The objects

**The router.** Surfaces are tried in a declared order; each either *reads*
the text (and then answers or refuses, and that is the verdict) or does not
read it (and the next surface is tried). The order:

| order | surface | reads the text when |
|---|---|---|
| 1 | **toolbox** | it starts with `tool` or is `tools` |
| 2 | **Python dialect** | it parses as Python and every name it loads is bound — assigned in the program, a dialect builtin, or a name the dialect refuses by name (`float`, `hash`, `random`, …) |
| 3 | **engineering** | one of its frames reads it |
| 4 | **planner** (then the grammar) | always — it is the old default path |

The rule that makes this safe is stated rather than hoped: a surface placed
before the planner changes an answer only for text it reads. So the
measurement that matters is which declared questions each early surface
reads.

**The toolbox.** A declared catalogue of every surface and tool: its name,
what it answers, the faculty (D15), its Lean specification and its study.
The eight unreached modules each get one entry, reached by `tool <name>`.

**The union mode.** *Derive X from Y and Z across wheels*: the axioms of all
ten wheels are taken together, but a quantity name shared by two wheels is
the same variable only where a **junction** declares the two wheels to mean
the same measurand of the same object. Every other shared name is split into
one copy per wheel (`energy@W5`, `energy@W10`), so it cannot be eliminated
against itself. The answer names the wheels whose axioms it used and the
junctions it crossed. The in-wheel `derive` frame is unchanged.

## 2. Declarations — written before any router, toolbox or union code

### 2.1 The junction table (argued, not looked up)

A junction identifies a shared name between two wheels when both wheels'
axioms are about the same physical object in the same domain. A shared name
that crosses domains — electrical to mechanical, kinetic to thermal, massive
to massless — names a *conversion*, which is a process with its own law, not
an identity. Declared identities:

| wheels | shared name identified | why |
|---|---|---|
| W5, W6 | `force`, `velocity` | the force on and the velocity of the same fluid column or piston |
| W5, W8 | `mass` | one body's mass |
| W1, W3 | `voltage` | the same terminal voltage across a capacitor in a DC circuit |
| W4, W9 | `angular_velocity` | the same rotating phasor |
| W9, W10 | `frequency` | the same wave's frequency |

Declared *not* identified, with the reason, because each is where naive
composition goes wrong: W1/W2 `current`, `voltage`, `power` (DC values against
sinusoidal amplitudes: identifying them makes resistance equal impedance);
W5/W8 `energy` (kinetic against thermal energy); W5/W10 `energy`, `momentum`
(a massive, non-relativistic body against a photon). Every shared name not in
the first table is split.

### 2.2 Marks

**Router (C).**

* **C1 — no regression.** Through the router, each of the 177 contract cases
  has the same verdict (answered or refused) and the same pass/fail under the
  evaluation's scoring as through the planner: 177 of 177.
* **C2 — reach without a flag.** Through the router: the 63 engineering
  questions get what `--eng` gives (53 answered correctly, 10 refused, 0
  wrong); the 83 Python value programs are answered equal to CPython and the
  26 refusal programs refused under their declared names; the 33 round-two
  cognition questions get what the planner gives.
* **C3 — gain on the default path.** Over the union of those four sets, the
  router answers strictly more correctly than the planner alone, and adds no
  wrong answer.
* **C4 — wiring.** After the round the wiring audit reports **0** of the
  reasoning modules outside the entry-point closure; each of the eight has a
  toolbox entry naming its Lean specification and its study, and each entry
  runs (the census-sized ones on a declared single input) inside 60 seconds.

**Union (U).**

* **U1 — what naive composition gets wrong.** Over the union of all ten
  wheels with no junction discipline, list every two-input derivation that no
  single wheel licenses, and label each by physics (the labels are in §2.3).
  This is a measurement, not a mark: it says how often naive composition is
  wrong.
* **U2 — the licensed union.** Over the same list, the union mode answers
  exactly the physically correct derivations and refuses the rest: **0
  wrong**.
* **U3 — no damage in-wheel.** For every two-input derivation some single
  wheel licenses, the union mode gives the same formula; and the 63
  engineering questions (whose `derive` frame is unchanged) still score 53
  answered, 10 refused, 0 wrong. In particular *derive power from pressure
  and volume flow rate* is still refused in-wheel, as the formula study's
  protocol requires, and is answered *across wheels*.
* **U4 — proved, not measured.** Lean: a licensed derivation is a derivation
  of the naive union (soundness of splitting), a derivation in a sub-union is
  one in any larger union, the naive union derives `energy = 2 * mass *
  speed_of_light^2` from W5 and W10, and the licensed union does not (a
  linear functional certifies it).

### 2.3 The physics labels for U1

Written from standard physics, family by family, before the union mode
existed. A formula is *correct* if it is a law of the stated wheels' domain,
not merely dimensionally consistent.

| family | correct? | reason |
|---|---|---|
| `power = pressure * volume_flow_rate` and its two rearrangements | yes | hydraulic power |
| `impedance = resistance` (and the converse), with any second input | no | holds only for a purely resistive load |
| `velocity = 2 * speed_of_light`, `speed_of_light = 1/2 * velocity` | no | a massive body's speed is not tied to `c` |
| `energy = 2 * mass * speed_of_light^2` and its rearrangements (`mass`, `momentum`, `force`, `power` against `c`) | no | photon relations applied to a massive body |
| `velocity = (2 * specific_heat_capacity * temperature)^(1/2)` and rearrangements | no | kinetic energy identified with stored heat |
| any family that goes through W5/W10 to W6 or W8 | no | inherits the photon conflation |

## 3. Results

Every figure below is re-taken by `python3 -m glm_universal.tools connected`
(add `--quick` to skip the union census, which is two and a half minutes of
exact linear algebra); the suite holds them in
`tests/test_connected_machine.py`, the census as an exhaustive case.

### 3.1 C1 — no regression: met

The reads census puts each declared question with the surface that reads it:

| set | toolbox | python | engineering | planner |
|---|---:|---:|---:|---:|
| contract (177) | 0 | 0 | 0 | 177 |
| engineering (63) | 0 | 0 | 63 | 0 |
| cognition (33) | 0 | 0 | 0 | 33 |
| Python (109) | 0 | 109 | 0 | 0 |

No contract case is read by a surface in front of the planner, so by
`route_prefix_none` every one of the 177 gets exactly the planner's verdict.
Two contract questions do parse as Python — *what is energy* and *what is 2 +
2* are comparisons of a name `what` with something — and are not read,
because `what` is bound nowhere. That collision was found by an exploratory
parse check before the declarations of §1 were written, and it is why the
Python reader asks for bound names rather than a successful parse.

### 3.2 C2 — reach without a flag: met

* **Engineering:** through the router the 63 questions score 53 correct, 10
  correct refusals, 0 wrong — what `--eng` gives.
* **Python:** 83 of 83 value programs agree with CPython in type and value;
  26 of 26 refusal programs are refused under their declared names.
* **Cognition:** all 33 go to the planner, so they get the planner's 26
  answers and 7 refusals.

### 3.3 C3 — gain on the default path: met

Over the four sets (382 questions), the planner alone answers none of the 53
answerable engineering questions and none of the 83 Python programs. On the
engineering set it answers two (`w-rot-alpha`, `p-ohm-p-vr`) with its
dimensional frame, only up to an undetermined dimensionless constant
(`power = k * voltage^2 * resistance^-1`), which the engineering scorer counts
as not the formula; on the Python set it answers two refusal programs,
`1.5 + 2` and `7 / 2`, as the exact rational `7/2`, where the dialect's
declared verdict is `FLOAT`. The router gives the declared verdict on all
four. Net: **136** more correct answers on the default path and no wrong
answer added.

### 3.4 C4 — wiring: met

`python3 studies/scripts/wiring_audit.py` now reads **96 of 96** reasoning
modules reached from an entry point, 0 not. The decision for each of the
eight was *reachable*, because each answers a question a caller can ask and
none is superseded outright:

| tool | answers | Lean specification |
|---|---|---|
| `tool moonshine` | the graded dimensions of V♮ (1, 0, 196884, …) | `Foundations.lean` |
| `tool llvq` | the Leech shells without a codebook | `Foundations.lean`, `LLVQTable.lean` |
| `tool pcgs` | 6 of 6 generative systems admitted, 3 by proof | `PCGS.lean` |
| `tool salvage` | the first eleven archive results, recomputed | `Lightspeed.lean`, `GolayWeightEnum.lean` |
| `tool salvage second` | eight more archive results | `Cube/Surface.lean`, `GrayJump.lean` |
| `tool deep dive` | 44 balanced octads against 37,800 of 735,471 by chance | `TriadChance.lean`, `Relaxation.lean` |
| `tool tie break NAME` | the tie class of one declaration's Leech address | `TieBreak.lean` |
| `tool stability NAME` | how far one declaration's address may move | `Stability.lean` |

All eight declared tool questions are answered with their declared fragment
inside the 60-second budget (the slowest, `stability`, about ten seconds on
first call). `tie break` and `stability` answer for one named declaration,
not for the whole book: their censuses stay in their studies.

### 3.5 U1 — what naive composition gets wrong

Over the union of all ten wheels with every shared name one variable, there
are **161** two-input derivations that no single wheel licenses. By the labels
of §2.3, **3** are laws (hydraulic power and its two rearrangements) and
**158** are wrong. The wrong ones fall into five families, and every one goes
through a conflation §2.1 names:

| wheels the certificate uses | derivations | example |
|---|---:|---|
| W5 + W10 | 79 | `energy = 2 * mass * speed_of_light^2`, `velocity = 2 * speed_of_light` |
| W1 + W2 | 70 | `impedance = resistance` (with any second input) |
| W5 + W8 | 3 | `velocity = (2 * specific_heat_capacity * temperature)^(1/2)` |
| W5 + W6 + W10 | 3 | `volume_flow_rate = 2 * area * speed_of_light` |
| W5 + W8 + W10 | 3 | `speed_of_light = (1/2 * specific_heat_capacity * temperature)^(1/2)` |
| W5 + W6 | 3 | `power = pressure * volume_flow_rate` — the only laws |

140 of the 161 formulas use only one of the two named inputs: the second
input is carried by a wheel that the certificate never touches. The algebra
is exact in every case; what is wrong is the identification.

### 3.6 U2 — the licensed union: met

With the junction table of §2.1, the union mode answers exactly the **3**
laws and refuses all **158** others: **0 wrong**. Each refusal says what the
naive union would have given and which identification it needs — for
example *the naive union of W5+W10 gives energy = 2 \* mass \*
speed_of_light^2, but only by identifying W5/W10 (a massive,
non-relativistic body against a photon)*. All 12 declared phrased questions
are answered or refused as declared, including *derive momentum from planck
constant and wavelength across wheels*, which is refused because the de
Broglie relation needs `wave_speed = speed_of_light`, and no wheel says so.

### 3.7 U3 — no damage in-wheel: met

For all **105** two-input derivations a single wheel licenses, the union
mode gives the same formula. The in-wheel `derive` frame is unchanged, so
*derive power from pressure and volume flow rate* is still refused there, as
the formula study's protocol requires, and the 63 engineering questions still
score 53, 10, 0.

### 3.8 U4 — proved: met

`RequestProject/GLM/ConnectedMachine.lean` builds with no `sorry` and only
the standard axioms:

* `route_cons_none`, `route_prefix_none`, `route_cons_some`,
  `route_append_of_some`, `route_total` — the router's rule;
* `derivable_mono`, `licensed_sound`, `not_derivable_of_functional` — the
  union's rule, over any rational vector space;
* `emc2_naive` — the naive union of W5 and W10 derives `energy = 2 * mass *
  speed_of_light^2`, with the combination `-1`, `2`, `2`;
* `emc2_refused_split`, `emc2_refused_split_photon` — after splitting
  `energy` and `momentum`, neither copy of energy is derivable so, certified
  by the functional *speed of light + photon energy + Planck's constant*;
* `hydraulic_licensed` — across the declared junction,
  `power = pressure * volume_flow_rate` is derivable.

## 4. What is wired

* `GLM.py --ask TEXT` (repeatable, short form `-a`): the connected path. It
  prints `SURFACE <name>` and then the surface's own rendering, so an answer
  looks the same whether it came by its flag or by this path.
* `GLM.py --ask tools` lists every surface and tool; `--ask "tool <name>"`
  runs one.
* `derive X from Y and Z across wheels` (and *express X in terms of Y and Z
  across wheels*) is the eighth engineering frame, reachable through `--ask`
  and `--eng`.
* `glm_universal.runtime.router` (`route`, `ask_routed`, `reader_of`),
  `glm_universal.runtime.toolbox` (`SURFACES`, `TOOLS`, `run_tool`),
  `glm_universal.engineering.union` (`derive_across`, `union_census`).
* `python3 -m glm_universal.tools connected` re-takes every figure here.

`-q` is unchanged: it still reads through the planner and the grammar. The
census says switching `-q` to the router would change no contract answer;
that switch is left to the owner, because `-q` is the interface every
earlier document describes.

## 5. D15, said plainly

This round moved **derivation** (hydraulic power across two wheels, which no
wheel holds and the system computes, with a certificate) and **refusal**
(158 wrong cross-wheel formulas refused, each with the identification it
would need). The router is not a new faculty: it is **reach** — 136 answers
the machine could already give are now given on the default path. The eight
tools are wiring, and are recorded as that.

## 6. What would earn the next round

1. **Switch `-q` to the router**, after the owner agrees, and re-run the
   contract set through the command line rather than by census.
2. **Junctions as a register**, not a table: the five identities and three
   non-identities of §2.1 are the first declared *measurands* in the system
   (candidate 1 of `STATUS.md` §3.4 asked for exactly this). A register of
   measurands would let a conversion — electrical to mechanical power through
   a stated efficiency — be a law of its own rather than a refusal.
3. **A router over a conversation**: the conversation layer binds follow-ups
   on the planner's path only; a follow-up to a Python or engineering answer
   is not yet bound.
4. **The Python dialect asking the engineering surface**: a builtin
   `derive(target, y, z)` would make a derivation a value a program can use.
