# Cent Transfer Compiler — Objective and Action Plan

> **Document role:** this file owns the objective, schemas and the historical
> phase plan. It is **not** the current status page: use
> [`CURRENT_SCOPE_AND_NEXT_TRACK`](CURRENT_SCOPE_AND_NEXT_TRACK.md) for the
> capability boundary and the [`PHYSICAL_COMPILER_ROADMAP`](../PHYSICAL_COMPILER_ROADMAP.md)
> for priority and sequencing.

**Status:** canonical objective, adopted 2026-11-11; implementation snapshot refreshed 2026-11-12  
**Implementation state:** Phase 3.5 eight executable `glm-reference` certificates implemented for delta-sigma quantized carry, log-domain square root, KCL exact sum/difference, normalized fluid-continuity sum/difference and ideal op-amp sum/difference, plus a separate live `glm-live` target for exact KCL sum/difference through the real GLM CLI and a reviewable `cent-proposal/1` handoff with an append-only review ledger; no GLM performance or external-budget claim is made
**Supersedes:** the “physical method selector” framing as the primary objective

**Current snapshot (2026-11-12):** eight mechanism cards; eight `glm-reference`
adapters over 24 fixed vectors; 32 matrix rows and nine exact route modes; G5b
reports 10/10 expected candidates, 8/8 target pairs, eight artifacts and 10/10
retrieval plus 8/8 target evidence. The T1 cam/orifice refusals and the current
live interface (T3) are closed by recorded refusal; T2 independent held-out
evaluation is the next evidence priority; physical KCL values (T4) remain
blocked.

## 1. One-sentence objective

Given a computational operation and a target context, find mechanisms from any
domain whose causal structure can realize that operation, construct an explicit
transfer mapping into the target, and produce a validated artifact with evidence
and gaps.

“Physical implementation” is one possible artifact. It is not the definition of
the compiler. A software adapter, a numerical model, or an information-processing
encoding can be a valid transfer target.

## 2. What changes

The old framing asked:

> Which declared physical ∆ implementations exist for this £?

The new framing asks:

> Which mechanisms, from any domain, can realize this operation; what exactly
> survives the move into the target; and what test shows that it works there?

| Old framing | New framing |
|---|---|
| Operation is a formula | Operation is a typed contract plus reference semantics and tests |
| Method is a declared physical route | Method is a mechanism plus a domain interpretation |
| Domain is a substrate label | Domain is a semantic and quantitative context with laws, constraints and costs |
| Transfer is a “declared analogy” label | Transfer is equations, invariants, a validity envelope and target tests |
| Evidence is “a route exists” | Evidence is source validation plus target validation and a certificate |
| Success is a SPICE netlist | Success is a validated target artifact; a netlist is one backend |
| Delta-sigma is the flagship answer | Delta-sigma is one benchmark transfer candidate |

The existing `£ → ¢ → ∆` path is not discarded. It becomes the **physical
realization backend** for a transfer candidate whose target is physical. The
new layer is the transfer compiler above it.

### 2.1 Why the current system cannot do this

- `discovery` indexes declared contracts, expansions, substrate rows, routes and
  wheel material. It can rank what is already declared; it cannot retrieve a
  mechanism that is absent from those tables.
- `compile` decomposes a formula and enumerates pre-declared physical
  implementations. It does not ask whether the same mechanism appears in another
  domain or what it would mean in a computational target.
- The five fidelity layers test physical effects (parasitics, noise, fabrication).
  They do not test whether the target operation is computed correctly.
- The cost function ranks component count and consistency, not transfer validity,
  semantic coverage or target utility.
- The GLM work is an application audit. Reference adapters remain
  `target-simulated`; a separate `glm-live` target runs the real GLM CLI for
  exact KCL sum/difference only, without a model or performance claim.
- Packing is a hand-declared analogy. It proves that the data model can host an
  analogy once someone writes it; it does not show that the compiler can find one.

Delta-sigma makes the gap concrete. The useful claim is not “delta-sigma is a
carrier.” The useful claim is:

> Error-feedback noise shaping, a mechanism used in audio analog-to-digital
> conversion, can be transferred into a quantized information representation and
> validated against a target operation.

That is a different object of study, with a different search space and a
different test obligation.

## 3. Definitions

| Term | Meaning | Example |
|---|---|---|
| **Operation contract** `£` | Typed signature, reference semantics, input/output domains, tolerances and tests | `sqrt: x ≥ 0 → y`, within a declared error bound |
| **Primitive chain** `¢` | The operation decomposed into the existing atomic/composite primitives | `scale → sqrt → output` |
| **Mechanism** `Μ` | A causal or structural principle that realizes an operation, independent of one substrate | Error-feedback noise shaping; feedback equilibrium; conservation at a junction |
| **Domain interpretation** `∆` | A realization of a mechanism in a domain, with quantities, laws, constraints and costs | A switched-capacitor integrator in electronics; a cam profile in mechanics |
| **Carrier / encoding** | How values are represented in the source or target | Voltage, pressure, position, phase, bitstream, spikes, fixed-point words |
| **Transfer mapping** `Τ` | Explicit correspondence from source quantities and laws to target quantities and laws, including what is preserved and what is lost | Accumulator state → numerical state; comparator output → ±1 code; mean code → scalar estimate |
| **Artifact** `Α` | Executable model, software adapter, simulation deck, netlist or documented procedure produced for the target | Python GLM adapter with test vectors; SPICE deck; mechanical profile |
| **Evidence level** | How strongly a claim is supported | proposed, structural, admissible, source-simulated, target-simulated, target-integrated |

A mechanism is not a substrate. “Capacitor” is a substrate. “Integrate charge and
compare it to a threshold in a feedback loop” is a mechanism. A transfer maps the
mechanism, not just the component name.

## 4. The transfer pipeline

1. **Accept the operation contract.**
   Parse a formula when possible; otherwise accept a typed operation descriptor
   with a reference implementation and tests. Refuse an operation with no
   declared semantics instead of guessing.

2. **Derive a behavior signature.**
   Record the primitive chain, statefulness, feedback topology, conserved
   quantities, nonlinearities, monotonicity, required precision, encoding and
   composition boundaries.

3. **Retrieve mechanisms across domains.**
   Search mechanism cards by behavior signature, not by operation name. A card
   may match because it has the same feedback topology, the same conserved
   quantity, the same nonlinear law, or the same state/encoding role.

4. **Propose transfer mappings.**
   Apply declared mapping operators: variable and unit mapping, scaling/offset,
   effort–flow duality, state transformation, time/sample scaling, amplitude
   quantization, linearization, feedback equivalence or composition. Every
   operator declares its preconditions.

5. **Check admissibility.**
   Verify topology, dimensions, units, conserved quantities and the declared
   validity envelope. The existing three-tier isomorphism gate is the starting
   point, but dimensional consistency alone is not semantic equivalence.

6. **Check behavioral validity.**
   Compare the source model and the target reference operation on declared test
   vectors and properties. Include edge cases, negative controls and a stated
   tolerance. A source mechanism that cannot reproduce the source claim fails.

7. **Emit the target artifact.**
   For a physical target, use the existing `compile`/`physical`/`fabricate`
   backend. For a software or information target, emit a target adapter and test
   harness. Do not emit a SPICE deck for a GLM target and call that a transfer.

8. **Certify, rank and expose gaps.**
   Each candidate carries its evidence level, passed tests, failed tests, first
   missing step and validity limits. Rank by target utility and evidence, not by
   component count alone.

## 5. Worked example: delta-sigma as a transfer, not a mascot

This is an illustrative target shape. The exact source loop law stays in the
declared implementation in `cent_compiler/assembly.py`; the transfer card points
to it rather than duplicating an approximate equation.

**Operation:** `quantized_carry(x)` — represent a scalar as a bounded code from
which the scalar can be reconstructed within a declared tolerance.

**Source mechanism:** error-feedback noise shaping in a first-order delta-sigma
modulator. The source domain is audio/electronics.

**Source structure:** an accumulator, a quantizer, and a feedback path that
subtracts the quantized output from the accumulated error.

**Target context:** GLM information processing, using a numerical encoding and a
reference reconstruction operation.

**Transfer mapping, at the card level:**

- normalized scalar input ↔ declared input range;
- comparator/code output ↔ ±1 (or declared multi-level) code;
- loop state ↔ numerical accumulator state;
- reconstruction ↔ declared decoder/average operation.

**Preserved:** bounded loop state, error feedback, first-moment reconstruction,
the declared oversampling relationship.

**Relaxed or lost:** analog voltage range, clock jitter, thermal noise, physical
power, and any claim that the numerical state is a fabricated circuit.

**Required tests:** loop stability, bounded state, reconstruction error against a
uniform quantizer, edge inputs, and a negative control where a plain quantizer
should not be promoted to the delta-sigma mechanism.

**Artifact:** a software adapter and test vectors. Not a SPICE netlist. If a
physical target is requested later, the physical backend may compile a circuit,
but that is a separate artifact and a separate evidence claim.

**Gaps:** the reference target has operation-local budgets; the live target has
no latency or bit-budget measurement and covers only exact KCL sum/difference.
The T3 probe records why the current GLM interface adds no honest live transfer:
`sqrt`/`exp` are refused, and exact `mult`/`div` have no mechanism cards. No GLM
performance score or external numeric contract is present. Those are explicit,
not implied by the mechanism name.

The point of this example is the template: operation → mechanism → mapping →
target tests → artifact → certificate. Delta-sigma is one benchmark, not the goal.

## 6. Target architecture

The transfer layer is additive. It should not turn `discovery` into another pile
of operation-specific branches.

| Component | Proposed responsibility |
|---|---|
| `cent_compiler/operation_contract.py` | Parse/normalize `£`; formula adapter; typed operation descriptors; reference evaluation and tests |
| `cent_compiler/mechanisms.py` | `MechanismCard` registry; source laws, invariants, failure modes, evidence and links back to existing routes/materials |
| `cent_compiler/transfer.py` / `transfer_engine.py` | Transfer schema, operation contracts, structural retrieval, mapping operators, candidates and ranking |
| `cent_compiler/targets/glm.py` / `transfer_validation.py` | Declared target profile, executable adapter, fixed vectors and pass/fail certificates |
| `cent_compiler/targets/glm.py` | GLM target profile, reference operations, adapter emission and test-vector format |
| `cent_compiler/transfer_validation.py` | Source/target model checks, property tests, evidence levels and certificates |
| `cent_compiler/discovery.py` | Remains a source catalogue; gains a mechanism-card projection rather than being the transfer engine |
| `cent_compiler/isomorphism_gate.py` | Extend the gate from dimensional admissibility to behavioral and target validation |
| `cent_compiler/wheel_mapping.py` | Reusable model for declared mappings; each mapping still needs a law, validity envelope and test |
| `cent` | New `operation`, `mechanism` and `transfer` commands; existing `compile` remains the physical backend |
| `tests/test_transfer_*.py` | Contract, mechanism, transfer, target and negative-control suites |

### 6.1 Proposed schemas

`cent-operation/1`:

```json
{
  "id": "sqrt",
  "signature": {"inputs": {"x": "nonnegative-real"}, "outputs": {"y": "real"}},
  "reference": "declared evaluator or executable",
  "tolerance": "exact or declared interval",
  "tests": [],
  "target_constraints": {}
}
```

`cent-mechanism/1`:

```json
{
  "id": "delta-sigma-error-feedback",
  "principle": "quantize the accumulated error and feed the code back",
  "source_domains": ["audio", "electronics"],
  "primitive_chain": ["accum", "quantize", "feedback"],
  "invariants": ["bounded state", "first-moment reconstruction"],
  "validity": ["declared input range", "stable loop"],
  "failure_modes": ["overload", "limit cycle"],
  "provenance": ["assembly.py", "DELTA_SIGMA_DEMO.md"]
}
```

`cent-transfer/1`:

```json
{
  "operation": "quantized_carry",
  "mechanism": "delta-sigma-error-feedback",
  "source": "audio ADC",
  "target": "glm",
  "mapping": [],
  "preserved": [],
  "relaxed": [],
  "relaxation": {
    "schema": "cent-relaxation/1",
    "classification": "unclassified",
    "basis": "no target-level relaxation evidence; candidate-only",
    "evidence_level": "none",
    "target": ""
  },
  "validity": [],
  "tests": [],
  "artifact": null,
  "evidence": "source-simulated",
  "gaps": []
}
```

### 6.2 Implemented command surface

```bash
python3 cent mechanism list
python3 cent mechanism delta-sigma-error-feedback --json
python3 cent transfer "quantized_carry" --target glm-reference --json
python3 cent transfer "sqrt" --target glm-reference --top 6
python3 cent transfer "quantized_carry" --target glm-reference --validate --json
python3 cent propose "sqrt" --target glm-reference --json
python3 cent propose "sqrt" --target glm-reference --out proposals
```

The `mechanism`, `transfer` and `propose` commands are implemented. There is no
separate `cent operation` command yet; operation contracts are exposed in
`cent transfer ... --json` and in the discovery/matrix views. `cent compile`
keeps its existing physical-backend role. The transfer `--validate` flag runs
the declared target adapter; `--emit` is not a transfer command. Reviewable
proposal files are written with `cent propose --out DIR`.

## 7. Action plan (historical phase record)

The ordering was deliberate: contracts and mechanism cards first, transfer
retrieval second, target validation third. The phases below record how the
current scope was reached; they are not a second current-status page. The
checked items are implemented, the open items are either future evidence work or
blocked. See the roadmap for the active order.

Do not start by adding more operation-specific branches to `discovery`.

### Phase 0 — Freeze the objective and contracts (1–2 days)

- [x] Publish this objective and link it from the README, roadmap and docs index.
- [x] Define `cent-operation/1`, `cent-mechanism/1`, `cent-transfer/1` and a
  target-profile record as dataclasses with JSON round-trip tests.
- [x] Add schema fixtures for delta-sigma, KCL sum and mechanical cam.
- [x] Add a negative-control fixture: a generic multiplier must not be accepted
  as a Griess or matrix-vector transfer.

**Acceptance:** every fixture round-trips; every field has provenance or an
explicit gap; the schema tests do not claim that transfer works yet.

**Implemented:** `cent_compiler/operation_contract.py`,
`cent_compiler/mechanisms.py`, `cent_compiler/transfer.py` and
`tests/test_transfer_contracts.py`; the shared suite passes **102/102** (16 contract checks, 11 registry checks, 10 engine checks, 20 proposal checks and 45 target checks), and the separate G5b evaluation suite passes **14/14**. The canonical gate is now seventeen suites and **824 checks**.

**G5a operation intake (2026-11-11):** ten operation contracts are declared —
`sqrt`, `sum`, `difference`, `quantized_carry`, `mult`, `div`, `exp`, `log`,
`reciprocal` and `sign`. The six additions each name an exact or certified
reference function and a fixed test; none has a production mechanism or target
adapter, so retrieval returns zero candidates with an explicit gap.

**G5b retrieval evaluation (2026-11-11):** `cent evaluate` declares four
known-valid cases, five negative controls, six unadapted operations and three
refused names. It measures 10/10 expected-candidate recall, 4/4 case recall, 0/5
negative-control false positives, 8/8 reference target pairs, 8 artifacts and
2 supported-but-unadapted candidates, with 10/10 retrieval and 8/8 target evidence
completeness. The two remaining supported candidates, cam and orifice, carry
T1 refusal records with the evidence required to reopen them. Known-valid means
declared card support, not independent external ground truth; no live or
measured target is claimed.

### Phase 1 — Seed the mechanism library (3–5 days)

- [x] Normalize existing route/expansion/substrate evidence into mechanism cards.
  Start with six; the current registry adds fluid continuity and op-amp summing
  as the seventh and eighth cards:
  - delta-sigma error-feedback noise shaping (audio/electronics → information);
  - log-domain exponential/logarithm (electronics → arithmetic);
  - KCL conservation (electronics → sum/difference);
  - fluid pipe-junction continuity (fluidics → sum/difference);
  - op-amp summing/difference (electronics → sum/difference);
  - cam profile (mechanics → function generation);
  - orifice pressure/flow law (fluidics → square root);
  - phase-locked loop (electronics → phase/frequency tracking).
- [x] Each card cites its existing source, law, invariants, carrier, validity
  envelope, failure modes and first gap.
- [x] Add `cent mechanism list` and `cent mechanism <id> --json`.
- [x] Link method-matrix rows to mechanism ids where a mapping is declared.

**Acceptance:** eight cards load and validate; no card exists without a provenance
link; a card with no target evidence is marked `proposed` or `gap`, not
`validated`.

**Implemented:** `MECHANISM_CARDS`, `MECHANISM_BY_ID` and `get_mechanism` in
`cent_compiler/mechanisms.py`; the registry loads at import, and its 11 checks
cover uniqueness, validation, provenance, first gaps, evidence levels, the
source laws and JSON round-trips. Six cards are `source-simulated` (delta-sigma,
log-domain, KCL, fluid, op-amp and PLL); cam and orifice remain `structural`.
The read-only `cent mechanism list` and `cent mechanism <id> --json` commands are
implemented. Matrix rows now carry explicit mechanism ids for the KCL, fluid,
op-amp, log-domain, delta-sigma and W24 bridge mappings; unlinked rows keep
`mechanism: null`.

### Phase 2 — Transfer engine v0 (1–2 weeks)

- [x] Implement the operation-contract adapter for existing formulas, plus one
  non-formula typed operation fixture.
- [x] Implement behavior signatures: primitive chain, state, feedback, conserved
  quantities, nonlinearity, encoding and precision.
- [x] Implement structural retrieval over mechanism cards.
- [x] Implement a small set of mapping operators with declared preconditions:
  identity, scale/offset, effort–flow duality, state transform, sampling/
  quantization, feedback equivalence and composition.
- [x] Emit `cent-transfer/1` candidates with preserved/relaxed properties,
  evidence level, first gap and test plan.
- [x] Add `cent transfer "<operation>" [--target ...] [--json]`.
- [x] Add negative controls: no generic multiplier match for Griess or
  matrix-vector; no text match promoted to a transfer.

**Acceptance (v0):** the four mechanism-backed operation contracts retrieve
candidates — `sqrt` 3, `sum` 3, `difference` 3, `quantized_carry` 1; every
candidate has a mapping, an evidence level and a first gap; delta-sigma is
retrieved by primitive/state/feedback features, not a name branch. Target
validation and multi-domain breadth for every operation remain separate
evidence steps.

### Phase 3 — GLM target adapter and validation (1–2 weeks)

- [x] Define the GLM target profile: input/output schema, reference operations,
  precision, invocation and reference-operation latency/bit budgets. External
  values remain gaps, not invented values.
- [x] Implement `cent_compiler/targets/glm.py` with pure reference operations and
  fixed test vectors. This is an adapter experiment, not a GLM score.
- [x] Emit executable adapters plus tests for the accepted transfers.
- [x] Implement the delta-sigma → GLM quantized-carry benchmark, including
  reconstruction error against a uniform quantizer and a bounded-state check.
- [x] Add non-delta-sigma transfers: the log-domain sqrt, KCL exact-sum and
  KCL exact-difference adapters. A log-domain multiplication artifact remains
  future work.
- [x] Add a separate live `glm-live` target for exact KCL sum/difference through
  the real GLM CLI; keep latency and bit-budget measurements out.

**Acceptance:** eight reference artifacts run against the reference target
profile; each has a pass/fail certificate with exact or declared numerical
results; the delta-sigma case has a baseline comparison. A separate `glm-live`
target runs exact KCL sum/difference through the real GLM CLI. No performance
improvement or external-budget claim is made.

**Status (eight reference; live KCL):** the delta-sigma quantized-carry,
log-domain square-root, KCL exact-sum/difference, normalized fluid-continuity
sum/difference and ideal op-amp sum/difference reference artifacts execute and
certify, and reference-operation latency/bit budgets are declared. A separate `glm-live` target executes the real external GLM CLI for
exact KCL sum/difference and certifies `target-integrated`. It makes no
performance, latency or bit-budget claim; broader live operations and external
budgets remain open.

### Phase 3.5 — Reviewable proposal handoff (implemented)

- [x] Emit a `cent-proposal/1` record per ranked analogy with operation, target,
  mechanism, mapping, analogy basis, source tests, target adapter and handoff.
- [x] Classify readiness as `ready-for-execution`, `needs-target-adapter`,
  `needs-target-vectors` or `needs-environment`.
- [x] Export `cent propose "<operation>" --out DIR` as one JSON per proposal,
  `index.json` and `index.md`.
- [x] Add persistent reviewer states (`accepted`, `rejected`, `tested`), notes
  and certificate-backed evidence in an append-only review ledger.

**Acceptance:** a proposal can be handed to a reviewer without re-deriving the
candidate; executable proposals name the exact validation command; missing
adapters are explicit; review decisions preserve prior state and never become a
validation claim; no proposal claims an isomorphism or a validation.

### Phase 4 — Evaluation and expansion (ongoing)

- [x] Build the ten-operation, eight-mechanism intake corpus with a reference
  and a fixed test per operation, using proposal bundles as the intake records;
  six new operations carry explicit target-adapter gaps.
- [x] Add known-valid and known-invalid transfers to the intake corpus.
- [x] Measure recall of known valid transfers, false positives on negative
  controls, target-test pass rate, artifact count and evidence completeness.
- [ ] Extend the evaluation beyond the declared corpus and reference adapters.
- [ ] Add mechanisms and domains only with provenance and target tests.
- [x] Integrate a live GLM CLI target for exact KCL sum/difference after the
  reference target contract became reproducible.
- [ ] Keep the physical backend gate green; a transfer candidate that selects a
  physical target should hand off to `compile` without redefining it.

**Acceptance:** at least one validated transfer that was not directly listed in
`DECLARED_ANALOGIES` or the operation’s expansion table; zero unlabelled false
positives on the five declared negative controls; all accepted artifacts carry
evidence and gaps. The current G5b metrics meet the declared corpus, but do not
establish external recall or a live target result.

## 8. First milestone

The first meaningful milestone is not “the GLM is solved.” It is:

```text
cent transfer "quantized_carry" --target glm --json
```

returning:

1. at least three mechanisms from at least two domains;
2. delta-sigma selected by its feedback/quantization structure, not by a name
   check;
3. one mapping with explicit preserved and relaxed properties;
4. one executable target artifact and test vector set;
5. a certificate with passed tests, a baseline comparison and remaining gaps.

A second command should return a non-delta-sigma arithmetic transfer, proving the
engine is not a renamed delta-sigma showcase.

## 9. Success criteria

For the first transfer milestone:

- ten operation contracts accepted, with at least one non-formula operation
  and explicit adapter gaps for the six new contracts;
- eight mechanism cards with provenance and failure modes (the six initial
  cards plus fluid continuity and op-amp summing);
- eight target adapters;
- at least ten ranked transfer candidates, of which at least three pass
  target tests;
- zero false positives on the declared negative controls;
- every candidate names its evidence level and first missing step;
- the existing physical gate remains green;
- no claim that a mechanism card, mapping or candidate is a measured device or a
  GLM result.

“Novel transfer” means a candidate not directly listed in the operation’s
expansion table or `DECLARED_ANALOGIES`, retrieved by behavior signature and
validated on the target. A renamed pre-declared route does not count.

## 10. Guardrails

- **No invented mechanisms, mappings, parameters or evidence.** A missing law is
  a gap.
- **A text match is not a mechanism.** A wheel keyword, shared symbol or domain
  word is a candidate only.
- **A dimensional match is not semantic equivalence.** Dimensions are necessary,
  not sufficient.
- **Physical and computational validity are separate.** A transfer can be
  computationally valid but physically unbuildable, or physically buildable but
  useless for the target.
- **Every accepted transfer needs target-specific tests.** Source simulation
  alone is not target validation.
- **Do not overfit to delta-sigma.** It is the first benchmark because its
  structure is known, not because it is the answer.
- **Keep existing claims honest.** The current physical routes, fidelities,
  fabrication limits and GLM audit boundaries remain as documented.
- **Do not call a reference adapter a GLM integration.** Only `glm-live` is a
  real interface, and it covers exact KCL sum/difference with a reproducible
  test.

## 11. Open decisions

1. What is the minimal stable GLM target API: a Python function, a JSON schema,
   or a message-level adapter?
2. Which operation contracts are in the first corpus? Candidate: sqrt, multiply,
   sum/difference, quantized carry, normalize, threshold/compare.
3. Is the first target purely software, or must one candidate also pass the
   physical backend?
4. How much of the existing `EXPANSIONS`/`DELTA_SUBSTRATE` data can be normalized
   automatically into mechanism cards without inventing fields?
5. What is the acceptance tolerance for the delta-sigma reconstruction benchmark,
   and against which uniform quantizer baseline?
6. Which negative controls are mandatory in the first gate?

## 12. Milestone checklist (historical)

These were the actions that built the current scope. The **current** next action
is T2/G6 independent held-out evaluation; T4 physical KCL remains blocked.

1. [x] Publish this document as the canonical objective.
2. [x] Add the three schema dataclasses and their round-trip tests.
3. [x] Seed the six mechanism cards from existing sources.
4. [x] Add a `cent transfer` skeleton that returns cards and explicit gaps, with
   no execution claim.
5. [x] Current live interface closed by T3 refusal: only exact KCL
   sum/difference are live. Reopen only with a new reproducible interface and a
   declared mechanism; external latency/bit budgets remain absent.
6. [x] Add the first delta-sigma transfer fixture and its negative control.
7. [x] Add reviewable proposal bundles and explicit validation handoffs.

**Implemented (Phase 3.5, reviewable proposals):** `cent_compiler/proposals.py`
builds `cent-proposal/1` records from the ranked candidates and writes a portable
bundle with `index.json`, `index.md` and one JSON per proposal. Readiness is
explicit: `ready-for-execution`, `needs-target-adapter`, `needs-target-vectors`
or `needs-environment`. The proposal layer never claims an isomorphism or a
validation. The focused suite is **102/102**, the evaluation suite is **14/14**,
and the full gate is **824 checks**.
The eight reference certificates and the live KCL target remain as documented;
the live target covers only exact KCL sum/difference and makes no latency,
bit-budget, model or performance claim.

This document is a design commitment. The historical phase plan above is
complete for its declared scope: contracts, cards, retrieval, reference
adapters, proposals and G5b evaluation all exist. The next evidence priority is
**T2/G6** independent held-out evaluation, followed by **T4** physical KCL only
when declared values exist. **T5** breadth comes last. T1 and T3 are closed by
recorded refusal, not by a broader claim. See the sequenced priorities in
[`../PHYSICAL_COMPILER_ROADMAP.md`](../PHYSICAL_COMPILER_ROADMAP.md) and the
capability ledger in [`CURRENT_SCOPE_AND_NEXT_TRACK.md`](CURRENT_SCOPE_AND_NEXT_TRACK.md).
Physical KCL values and the external layers remain blocked on their own
evidence.
