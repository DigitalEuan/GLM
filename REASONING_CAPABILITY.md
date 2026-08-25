# Can the GLM function as a reasoning machine yet?

**Short answer: yes, within a bounded but non-trivial competence, and with an
unusually strong guarantee attached to every answer it does give.**

It is a *deductive* reasoning machine over exact structured knowledge — a
726-quantity dimensional register, a 118-element chemical register, a
mathematical register, a substrate of the Golay code and the Leech lattice,
and (new in this pass) a 4,680-concept relational graph recovered by the
literal data migration. It is **not** a language model, not a numeric
calculator, and not an open-domain question answerer. Asked something outside
its competence it refuses and names what is missing, rather than guessing.

Everything in this document is generated, not narrated. The transcript is
produced by

```
cd overlay
PYTHONPATH=. python3 glm_universal/examples/reasoning_showcase.py
```

and the full verbatim output is checked in at
[`glm_universal/examples/reasoning_showcase_transcript.md`](glm_universal/examples/reasoning_showcase_transcript.md).

---

## 1. What "reasoning" is taken to mean here

A GLM answer is not a string. It is a `Solution` carrying four separable
things, and the separation is the point:

| part | what it is | who checks it |
|---|---|---|
| `steps` (column 1) | the chain of reasoning in plain English | a human |
| `steps` (column 2) | *the same steps* as exact statements over ℚ, ℤ or 𝔽₂ | a human |
| `expected` | the falsifiable core: claim name → exact canonical string | column 3 |
| `payload` | rankings, diagnostics, provenance — explicitly **not** verified | nobody |

Columns 1 and 2 are two renderings of one list of steps, so they cannot drift
apart. Column 3 is a Python script *generated from the solution*, run in a
**fresh interpreter** with no shared state, whose printed claims are compared
key by key against column 2. A solution is reported `verified` only when the
independent re-derivation agrees on every claim.

This is why the honest answer to "can it reason?" is stronger than a pass
rate: **of the 25 answered probes in the showcase, 25 were verified by
independent re-derivation, and every generated script was float-free.** The
four remaining probes are refusals, which is the intended behaviour.

## 2. The competence, stated plainly

### It can

1. **Decide dimensional relations** — multiplication, division, rational
   exponents, parentheses, and a stricter "tensor" mode that also compares
   tensor rank and parity. It decides both directions: it accepts true laws
   and rejects near-miss false ones.
2. **Answer questions about physical constants** dimensionally, including
   `speed_of_light`, `fine_structure_constant`, `rydberg_constant`,
   `neutron_mass`, `atomic_mass_constant` and `impedance_of_free_space`,
   added in this pass precisely because their absence blocked ordinary
   questions.
3. **Compute coherence** — the exact TAX / NRCI law, with its regime band,
   for any carrier in any register.
4. **Retrieve and rank** — nearest neighbours, exact angles, clustering, and
   four-term analogies, all by exact rational distance, and it says when the
   answer is *not unique* instead of picking one silently.
5. **Escalate through layers** — compare two concepts at the substrate,
   integer, rational, Griess and universal layers, and report which layer
   first separates them. This is the information-loss study made
   operational.
6. **Reason over the migrated state** — query the recovered concept graph,
   and, crucially, *adjudicate* what it retrieves against the dimensional
   register rather than merely repeating it.
7. **Induce a rule from examples** on ARC-style grids and apply it.

### It cannot

1. **Evaluate numerically or convert units.** The registers are dimensional;
   they carry exponent vectors and an exact decimal scale, not measured
   magnitudes. `how many joules is one electronvolt` is refused.
2. **Absorb an arbitrary numeric factor.** `energy = 3 * mass * c^2` is
   refused: only exact powers of ten are representable in the scale
   coordinate, and approximating would break exactness.
3. **Handle open-ended natural language.** There are thirteen query kinds;
   anything else is reported as unrecognised, with the list of kinds.
4. **Infer new physics.** Dimensional consistency is necessary, not
   sufficient: the system will certify `energy = entropy * temperature` and
   equally certify any other relation with the same exponents. It says so —
   see §4.

## 3. Worked examples

Excerpts below are verbatim from the transcript.

### 3.1 Mass–energy equivalence, decided both ways

```
ASK  verify energy = mass * speed_of_light^2
     energy = mass * speed_of_light^2 holds under scalar semantics

ASK  verify energy = mass * speed_of_light
     energy = mass * speed_of_light does not hold under scalar semantics
```

with column 2 for the first:

```
1. [parse]     lhs = energy ; rhs = mass * speed_of_light^2
2. [dimension] dim(lhs) = L^2 M T^-2 ; dim(rhs) = L^2 M T^-2
3. [rank]      rank(lhs) = 0, rank(rhs) = 0
4. [semantics] compared coordinates = 18 of the 24 relation coordinates
5. [stack]     depth = 3, offset = 2 ; planes compared = 0..2
6. [verdict]   for all planes p: lhs_p - rhs_p = 0
```

Column 3 re-derived all 7 claims in a fresh interpreter: **verified**.

The same question typed in ordinary English —
`verify energy = mass * speed of light^2` — now also works: the equation
parser glues adjacent words back into the longest register name it
recognises, and only accepts a join that actually resolves, so a genuinely
missing `*` is still an error.

### 3.2 The stricter semantics

```
ASK  check tensor force = mass * acceleration
     force = mass * acceleration holds under full semantics
```

`full` semantics compares all 24 relation coordinates, including tensor rank
and parity, not just the 18 dimensional ones.

### 3.3 A constant identified with its quantity

```
ASK  verify impedance_of_free_space = resistance
     impedance_of_free_space = resistance holds under scalar semantics
```

### 3.4 Coherence, exactly

```
ASK  coherence of planck_constant
     coherence planck_constant: NRCI = 0.1870 (Subcoherent)

ASK  coherence of electron
     coherence electron: NRCI = 0.0004 (Subcoherent)
```

The printed NRCI is a rounded display; the verified claims are exact
rationals in `B / (B + TAX)` form, and column 3 recomputes them as fractions.
The same law applies across registers — the second probe is a chemical
element, not a physical quantity.

### 3.5 Analogy that admits it is not unique

```
ASK  force : energy :: pressure : ?
     force : energy :: pressure : adhesion_energy
```

with claims

```
answer     = adhesion_energy
distance2  = 0/1
exact_hit  = True
unique     = False
tied       = ['adhesion_energy', 'flux_density_jansky', 'fracture_energy',
              'radiant_exposure', 'spring_constant', 'surface_energy',
              'surface_tension']
```

This is the honest behaviour: the translation `C + (B − A)` lands exactly on
a register point, and *seven* quantities occupy it, because they share a
dimension. The system reports the tie rather than hiding it.

### 3.6 Layer escalation — where a truth stops holding

```
ASK  project energy torque
     project energy torque: walked 5 layers, final = universal
```

The layer-by-layer readout is the concrete form of the information-loss
study:

| layer | what it sees | separation |
|---|---|---|
| substrate | energy HW=3 (decodes, `corrected`), torque HW=4 (`ambiguous`, 6 nearest codewords) | 3 |
| integer | SI7 exponents `(2,1,−2,0,0,0,0)` for **both** | **0** |
| rational | Leech `d² = 15/8` vs `3/2`, distinct classes | 3/8 |
| griess | same classes | 3/8 |
| universal | all layers at once | 3/8 |

The integer layer is *blind* to a distinction the layers on either side of it
can see: energy and torque are the same quantity in SI7 and different in
EXT10. Note also the substrate line — torque's carrier sits at Hamming
distance 4 from the Golay code, exactly the weight at which nearest-codeword
reading stops being unique, and the system reports `ambiguous` with all six
equidistant codewords rather than picking one. That boundary is the one
proved in Lean as `snap_boundary_at_three`.

`task physics` states the same finding as a worked task:

```
task physics: energy and torque are the same quantity in SI7 (L^2 M T^-2)
and different in EXT10; the carriers first differ at digit plane 0, and the
difference is carried by the dimension, tensor_rank, nominal_kind facets
```

The facet attribution is exact, not heuristic, because the six facet
projections are orthogonal and complete — proved in Lean as
`GLM.Facets.pythagoras`.

### 3.7 Reasoning over the migrated data

```
ASK  report state migration
     4282 concepts and 4014 edges migrated in the canonical frame,
     398 carriers minted, 1828 carriers ambiguous under complete decoding,
     no float written

ASK  task concepts
     the migrated CRG relates entropy to energy in 2 asserted steps, and the
     dimensional register confirms entropy * temperature = energy while
     rejecting entropy * temperature = force; the substrate contributes
     nothing to either, since the carriers were assigned by digest
```

This probe is the most informative one in the set, because it is the only
place where retrieved knowledge is *adjudicated*:

* the graph supplies a chain `entropy → dissipation → energy`, and the chain
  survives excluding the growth loop's auto-proposed edges, so it is asserted
  knowledge rather than machine speculation;
* both endpoints cross-link into the physics register, which is where the
  claim can be tested rather than repeated;
* the test is discriminating: the law passes **and** a control with the same
  shape fails. A check that passed both would be checking nothing;
* the substrate contributed **nothing**, and the system says so: entropy's
  three nearest carriers are `amiability`, `cacodyl`, `shot`, which share no
  edge with it. Those vectors were assigned by digest in the original data,
  so Hamming distance between concepts is not a semantic distance. This is
  recorded as a negative result, not quietly dropped.

### 3.8 A non-physics task

```
ASK  task grid
     task grid: the rule is rotate180; the test grid maps to
     [[0, 0, 7], [0, 5, 0], [3, 0, 2]]
```

### 3.9 The refusals, verbatim

```
ASK  verify energy = mass * zzzz_nope
     unsolved: verify: unknown concept 'zzzz_nope'; did you mean ['z_p']?

ASK  verify energy = 3 * mass * speed_of_light^2
     unsolved: verify: numeric factor 3 is not a power of ten; the register
     tracks the decimal scale exactly and refuses to absorb other constants

ASK  how many joules is one electronvolt
     The query was not recognised as any of ['verify', 'analogy', 'describe',
     'nearest', 'product', 'cluster', 'spatial', 'project', 'trilinear',
     'coherence', 'report', 'angle', 'task'].
```

## 4. What the verification does *not* claim

Column 3 checks that the answer is *correctly derived from the registers*. It
does not check that the registers are right about the world, and it does not
turn a dimensional check into a physical one. Concretely:

* `verify X = Y` establishes dimensional consistency. It is necessary for a
  physical law and nowhere near sufficient — torque and energy pass every
  SI7 test against each other and are not the same thing, which is exactly
  the case §3.6 dissects.
* The new constants are dimensional records only. No numerical value is
  stored for any of them, and `test_physics_constants.py` asserts that none
  is smuggled in. The electronvolt was deliberately **not** added, because
  its magnitude is not an exact power of ten of the joule and its `scale`
  coordinate could therefore only be recorded approximately.
* Concept-to-concept Hamming distance in the migrated data is meaningless,
  as §3.7 states. Only the register cross-links carry semantics.

## 5. Reproducing this

```
cd overlay

# the transcript in this document (about 4 minutes, spawns one subprocess
# per probe for column 3)
PYTHONPATH=. python3 glm_universal/examples/reasoning_showcase.py

# fast version, no column 3
PYTHONPATH=. python3 glm_universal/examples/reasoning_showcase.py --no-verify

# regenerate the checked-in transcript
PYTHONPATH=. python3 glm_universal/examples/reasoning_showcase.py --markdown \
    > glm_universal/examples/reasoning_showcase_transcript.md

# one section only
PYTHONPATH=. python3 glm_universal/examples/reasoning_showcase.py --only "layered"
```

The showcase is also a test: `glm_universal/tests/test_reasoning_showcase.py`
runs every probe and asserts that each answered probe is solved, each refused
probe is refused, and — for a representative sample — that column 3 verifies.
