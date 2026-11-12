# Current scope and next development track

**Last reviewed:** 2026-11-12  
**Canonical gate:** 17/17 suites, **824/824 checks**, README consistency **OK**

> **Document role:** this is the capability boundary and open-gap ledger. It
> answers *what works now, what is only declared, and what is blocked*. The
> [`PHYSICAL_COMPILER_ROADMAP`](../PHYSICAL_COMPILER_ROADMAP.md) owns priority and
> sequencing; [`TRANSFER_COMPILER_OBJECTIVE`](TRANSFER_COMPILER_OBJECTIVE.md)
> owns the objective, schemas and historical phase record.

This is the current capability audit. It is deliberately narrower than the
project vision: it records what the code and fixed tests support now, what is
only declared, and what would close each remaining gap. It does not promote a
mechanism, proposal or example above its evidence level.

## 1. Current capability boundary

| Layer | Implemented now | Evidence / limit |
|---|---|---|
| Physical backend | £ parsing, ¢ DAG decomposition, declared ∆ enumeration and ranking, 39 wheels, nine exact route modes, three physical bindings, reference netlists and dynamic checks | Exact or declared structural results; no fabricated or measured device |
| Operation contracts | Ten contracts: `sqrt`, `sum`, `difference`, `quantized_carry`, `mult`, `div`, `exp`, `log`, `reciprocal`, `sign` | Each has semantics, a reference and a fixed test; six have no mechanism |
| Mechanism registry | Eight cards: delta-sigma, log-domain sqrt, KCL, fluid continuity, op-amp summing, cam profile, orifice pressure/flow, PLL phase tracking | Five cards support at least one production operation; three sqrt routes are declared, two structural |
| Retrieval | Four operations retrieve candidates: `sqrt` 3, `sum` 3, `difference` 3, `quantized_carry` 1 | Declared mechanism support, not independent ground truth |
| Evaluation | `cent evaluate`: 4 known-valid cases, 5 negative controls, 6 zero-mechanism operations, 3 refused names | 10/10 candidate recall, 4/4 cases, 0/5 false positives, 8/8 target pairs, 2 unadapted candidates with T1 refusal records |
| Reference target | Eight executable `glm-reference` pairs over 24 fixed vectors | `target-simulated`; no real GLM, measured-device or external budget |
| Live target | `glm-live` exact KCL sum and difference through the external CLI | `target-integrated` for those two operations only; no latency or bit-budget measurement |
| Proposal handoff | `cent propose` bundles, readiness, review ledger and executable handoffs | Current bundles below; a proposal remains unvalidated until target tests run |

### Usable now

- Exact rational arithmetic, certified interval sqrt/exp/log, exact route
  assembly and fixed-vector target validation.
- `cent transfer` for the four mechanism-backed operations, with explicit
  candidate-only gaps.
- `cent evaluate` for the declared corpus and its negative controls.
- `cent propose` for the four backed operations, including a review ledger.
- `target-simulated` reference adapters for eight pairs and `target-integrated`
  live KCL sum/difference.

### Declared but not target-validated

- `cam-profile` and `orifice-pressure-flow` for `sqrt`: structural mechanisms
  with no exact model, adapter or fixed target vectors. T1 records both as
  refusals until those laws and vectors exist.
- The physical KCL artifact: the normalized route and binding exist; component
  values, source/load and a reference netlist do not.
- The 22 `.cir` examples and physical routes: useful declared/reference
  artifacts, not measured devices.

### Not usable as a transfer claim

- The six zero-mechanism operations (`mult`, `div`, `exp`, `log`,
  `reciprocal`, `sign`) have no declared mechanism transfer.
- PLL phase tracking has a source-simulated mechanism card but no production
  operation contract, so `cent transfer track_phase` refuses.
- Bresenham is a retained one-tick hypothesis lead, not a mechanism card; the
  existing two-tick target is not equivalent.
- Q-tensor is retired; scalar invariants cannot select a director.
- No external held-out corpus, physical measurement, fabrication result or
  benchmark score is claimed.

## 2. Loose ends

These are the known open gaps. “Closed here” means this tidy-up added a concrete
artifact or statement, not that the underlying evidence exists.

| ID | Loose end | Status now | What would close it |
|---|---|---|---|
| L1 | Six operation contracts have no mechanism or target adapter | Open; `cent transfer` returns zero with an explicit gap | A mechanism card with a real source law, provenance, fixed test and adapter, or continued explicit refusal |
| L2 | Two supported candidates are unadapted (`cam-profile`, `orifice-pressure-flow`) | Closed for T1 by recorded refusal; still counted as unadapted with required evidence in G5b | Declared model, fixed vectors and target adapter, or a stated refusal |
| L3 | G5b known-valid means declared card support | Open; documented in `cent evaluate` and this audit | Independent/held-out corpus with provenance and negative controls |
| L4 | Live target covers only exact KCL sum/difference | Closed for T3 by recorded refusal; reference-only for sqrt/carry | Additional live operation with reproducible vectors and declared budgets |
| L5 | Physical KCL artifact is missing | Blocked | Declared component values, source/load, compliance and error budget |
| L6 | PLL supports `track_phase`/`synthesize_frequency` but no operation contract exists | Open | Contract with semantics, reference, fixed test, then adapter |
| L7 | Cam and orifice are structural only | Open | Exact profile/restriction law and an adapter with vectors |
| L8 | Bresenham is a lead, not a card | Retained narrowly | Separate card and target evidence for the one-tick variant only |
| L9 | 22 legacy `.cir` examples and current transfer proposals were not separated | Closed here: current bundles are under `examples/transfer/`; the 22 `.cir` files remain pinned physical show-work | Keep both classes labelled |
| L10 | External math evidence (D5, D10b–e, Lean) and Rule30/ARC adapters are absent | Blocked | Declared structure, tensor/action data, build or benchmark adapter with scoring |
| L11 | Documentation counts are automated, but semantic claims are not | Mitigated here; counts/tree are checked by the gate | Review this file and the roadmap whenever evidence changes |
| L12 | Discovery has overbroad matches for “Griess product” and “matrix-vector product” | Known; generic multiplier methods are not accepted as those operations | Narrow the match or retain the refusal; do not count a text match as a proof |
| L13 | No measured-device or fabrication evidence | Blocked | Fabrication and measurement, not a netlist or simulation |
| L14 | W30/W31 have no declared domain content | Blocked | Reviewed wheels with axioms and tests; do not guess a table |

## 3. Updated examples and proposals

The current proposal bundles are in
[`../examples/transfer/`](../examples/transfer/). They were generated from the
current CLI on 2026-11-12:

| Operation | Proposals | `ready-for-execution` | `needs-target-adapter` |
|---|---:|---:|---:|
| `sqrt` | 3 | 1 (`log-domain-sqrt`) | 2 (`cam-profile`, `orifice-pressure-flow`) |
| `sum` | 3 | 3 (`kcl-conservation`, `fluid-continuity`, `opamp-summing`) | 0 |
| `difference` | 3 | 3 (`kcl-conservation`, `fluid-continuity`, `opamp-summing`) | 0 |
| `quantized_carry` | 1 | 1 (`delta-sigma-error-feedback`) | 0 |
| **Total** | **10** | **8** | **2** |

`examples/transfer/evaluation.json` is the current `cent evaluate --json`
payload. Its certificate is `partial`, correctly, because the evaluation has
declared gaps.

These proposals are different from the 22 `examples/proposal_*.cir` files:

- the `.cir` files are physical-backend show-work examples, pinned by
  `tests/test_proposals.py`;
- the `examples/transfer/` bundles are transfer handoffs with mechanism,
  mapping, readiness, review state, target vectors and handoff commands;
- neither class is a validation result without its declared target tests.

### Can any proposed method be used with benefit?

| Method | Current evidence | Can it be used now? | Benefit / limitation |
|---|---|---|---|
| Delta-sigma error feedback → `quantized_carry` | `source-simulated`; `target-simulated` reference certificate | **Yes**, reference target | Exact carry/mean test, bounded-state and baseline checks; no live GLM or measured hardware |
| Log-domain sqrt → `sqrt` | `source-simulated`; `target-simulated` reference certificate | **Yes**, reference target | Certified rational enclosure with independent `sqrt_q`; no measured junction |
| KCL conservation → `sum` / `difference` | `source-simulated`; `target-simulated` reference; live exact KCL | **Yes**, reference and live KCL | Exact normalized arithmetic; no physical units or measured junction |
| Fluid continuity → `sum` / `difference` | `source-simulated`; `target-simulated` reference certificates | **Yes**, reference target | Exact normalized-flow parity, commutativity and reversed-port difference; no pressure/flow scaling or measured junction |
| Op-amp summing → `sum` / `difference` | `source-simulated`; `target-simulated` reference certificates | **Yes**, reference target | Ideal matched-resistor summing block and inverting-buffer difference; no device values or measured amplifier |
| Cam profile → `sqrt` | `structural` | **No target use** | Design lead; no exact cam solver or adapter |
| Orifice pressure/flow → `sqrt` | `structural` | **No target use** | Design lead; no calibrated law or adapter |
| PLL → phase/frequency | `source-simulated` card | **No transfer use** | No production operation contract; numerical, not exact |
| Bresenham one-tick carry | Hypothesis evidence only | **No** | Narrow lead; not a card and not equivalent to the two-tick target |
| Orientation envelope | Exact finite-direction algorithm | **Yes, separately** | Useful exact geometry method via `cent envelope`; not a mechanism transfer |
| Q-tensor | Retired by invariant proof | **No** | Scalar invariants are orientation-blind |

The only methods that can be used with target benefit today are the eight
reference-backed pairs above. The structural methods are useful as design leads
only; the fluid route is now an independent normalized-flow reference check, not
a measured physical transfer.

## 4. Next development track

**State at a glance:** T0 complete; T1 and T3 closed for the current scope by
recorded refusal; **T2 is the active priority**; T4 is blocked on physical
values; T5 is later; T6 remains blocked. Nothing in this table authorizes a
label-only promotion. Existing roadmap IDs are kept where they already exist.

| Phase | Track | Why now | Acceptance / refusal |
|---|---|---|---|
| **T0** | Documentation and examples maintenance | This review reconciled the three overlapping status documents and refreshed counts | README/gate counts synchronized; examples regenerated; the three documents have distinct roles |
| **T1** | Close the remaining supported-but-unadapted candidates (**G7**) | Closed by recorded refusal for `cam-profile` and `orifice-pressure-flow`; the fluid and op-amp additions are separate promoted routes, not T1 adaptations | Each remaining candidate gets a declared model, fixed vectors and an executable reference adapter, or a recorded refusal |
| **T2** | External/held-out evaluation (**G6**) | G5b is a declared-support regression suite, not independent external truth | A declared corpus with provenance, held-out labels and negative controls; otherwise remains open |
| **T3** | Current-interface live boundary (**G4b**) | Closed by recorded refusal; live coverage remains KCL sum/difference | Reopen only with a reproducible exact interface and a declared mechanism |
| **T4** | Physical KCL artifact (**C1**) | The normalized route has no physical artifact | Declared values, source/load, compliance and error budget; no invented component values |
| **T5** | Operation/mechanism expansion (**G8**) | Six zero-mechanism operations and PLL are the next breadth candidates | Each new card/contract has a source law, provenance, fixed test and adapter/gap; no card added just to fill a row |
| **T6** | Blocked external layers (**D5/E1/F1**) | These need data or tooling, not a label | Reproducible artifact or explicit refusal; no cross-layer substitution |

### Recommended order

1. **T2 — active priority.** Source an independent held-out corpus with
   provenance, labels and negative controls. This is the only way to move recall
   beyond “the cards agree with themselves.” If no corpus can be sourced, keep
   it an explicit gap; do not relabel G5b.
2. **T4 only with physical values.** A normalized exact route is not a physical
   KCL artifact. Work starts only when component values, source/load, compliance
   and an error budget are declared.
3. **T5 last.** Adding another operation or mechanism before T2/T4 would repeat
   the label-count problem G5a/G5b were meant to stop.
4. **T1 and T3 are closed by refusal, not by adaptation.** Cam/orifice and the
   current live interface have recorded refusal conditions; reopen only with the
   named evidence.
5. **T6 remains blocked** until its declared data, build or adapter exists.

### Non-goals for this track

- Do not call a reference adapter live.
- Do not call a structural card target-validated.
- Do not treat G5b declared support as external ground truth.
- Do not invent calibration, component values, latency or bit budgets.
- Do not add a mechanism card merely to make a zero-mechanism operation look
  supported.

## 5. Review history

### 2026-11-12 — documentation reconciliation

- Assigned the three documents distinct jobs: capability boundary here,
  priority/sequence in the roadmap, objective/schema/history in the transfer
  document.
- Updated the capability tables to eight mechanism cards, 32 matrix rows,
  nine exact route modes, eight reference adapters over 24 fixed vectors, and
  the 10/10 evaluation result.
- Recorded the op-amp sum/difference promotion and the separate computational
  addition laboratory.
- Clarified that T1 is closed by refusal for cam/orifice and T3 is closed for
  the current live interface. “Closed” means the refusal condition is recorded;
  it does not mean the missing evidence now exists.
- Removed the implication that the whole roadmap was complete through G5b while
  G4b and T2 were still being described as open in different places.

### 2026-11-11 — previous tidy-up

- Added the first current-scope, loose-end and next-track record.
- Generated transfer proposal bundles and the evaluation payload under
  `examples/transfer/`.
- Separated the 22 legacy physical `.cir` examples from current transfer
  proposals.
- Added T1 refusal records for cam and orifice to `cent evaluate`.
- Added the T3 live-breadth probe and refusal record under `docs/evidence/`.
- Linked this audit from the documentation index, README and roadmap.
