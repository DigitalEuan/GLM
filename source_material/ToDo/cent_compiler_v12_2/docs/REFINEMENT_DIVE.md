# Input 1 refinement dive

Source: `input1.txt` (attached review, 2026-11-11). This is a triage and working
backlog, not a second specification. Each claim below was checked against the
current code before being accepted.

**Acceptance policy:** computational correctness is the gate. A geometric,
physical or biological story can be attached as optional interpretation; it does
not need a physical-realization proof before a computational method can be built.
Physical claims remain out of scope.

## Verdict on the attachment

| Attachment claim | Current system | Decision |
|---|---|---|
| Mechanisms are indexed only by domain nouns. | Partly true. `BehaviorSignature`, `MECHANISM_BEHAVIORS`, `primitive_chain`, `stateful`, `feedback`, `conserved_quantities`, `nonlinearity`, `encoding` and `precision` already exist. Candidate eligibility is still gated by `supported_operations`; that is a deliberate guardrail, not a keyword parser. | Keep the admission gate. Do not turn shared words into candidates. Add declared cards where a real source route exists. |
| Add an `invariant_signature` field. | The substance already exists as `MechanismCard.invariants` plus the behavior signature table. There is no field with that exact name. | Do not duplicate the schema just to rename it. Add a field only when an external consumer needs a stable serialized form. |
| Add behavior-signature tags. | Already implemented in `MECHANISM_BEHAVIORS`; the card JSON exposes `primitive_chain`, `stateful`, `invariants` and the free-text law. | Use the existing signatures; do not add a second tagging system. |
| Decompose operations into micro-pipelines. | Implemented structurally. `cent pipeline` derives stages from each route's actual `cent-program/1` instructions; typed route components supply laws, and declared exact-program glue covers `neg`, `sum` and `sat`. | Keep deriving from declared programs, not operation names. The current output is a decomposition, not a new execution engine or arbitrary sub-operation composition. |
| Classify discrete/continuous relaxation. | Implemented. `cent-relaxation/1` defaults to `unclassified`; a non-`unclassified` class needs a basis, matching target, target-level evidence, artifact and target tests. Target-backed exact KCL, fluid and op-amp sum/difference routes are `exact`; delta-sigma and sqrt remain `unclassified`. | Keep the target-evidence guard; do not classify the RC/clock `0.632` behavior as an exact discrete step. |
| Build the ten-operation, at-least-six-mechanism corpus. | Complete for the declared corpus. The registry has ten operation contracts and eight mechanism cards; the six new contracts have no production mechanism or target adapter. `cent evaluate` reports 10/10 expected-candidate recall, 4/4 cases, 0/5 negative-control false positives, 8/8 reference target pairs, 8 artifacts and 2 unadapted candidates. | P1. G5b is complete for the declared corpus. External recall, held-out ground truth and live target evidence remain open; known-valid means declared card support, not independent truth. |
| Add an exact packing certificate. | Gap for global optimality. `packing.py` is an exact axis-aligned feasibility probe with no rotation, exhaustive search or global certificate. | P2 exact separating-axis witness for axis-aligned states; global/rotated packing remains out of scope. |
| Bresenham is exactly first-order delta-sigma. | The one-tick floor variant is exact by induction over `1 <= dx <= 32, 0 <= dy <= dx`; the existing two-tick nearest-level target is a different timing and mismatches. | Retained narrowly as the one-tick variant in `docs/evidence/bresenham/`; no equivalence claim for the existing route, and no promotion without a separate mechanism card. |
| Hybrid SAT/nematic/pressure packing pipeline. | No pipeline. The `nematic-q-tensor-bounding-box` audit proves scalar invariants are orientation-blind; a full eigenframe bridge is orientation-only. The existing W36/W37 route still has no rotating-square, spin-state or nematic model. | Q-tensor retired in `docs/evidence/nematic-q-tensor/`; a separate orientation-only lead may be declared, but it must not claim invariant content. |

## Completed in this pass

- [x] Added the `fluid-continuity` mechanism card and behavior signature.
- [x] `cent transfer sum` now retrieves both `kcl-conservation` and
  `fluid-continuity` across electrical and fluidic domains.
- [x] Kept `supported_operations` as the admission gate; unsupported cards are
  not silently promoted.
- [x] All three `sum` and all three `difference` mechanisms now have
  independent executable adapters; the explicit `--mechanism` selector keeps
  KCL, fluid and op-amp handoffs distinct.
- [x] Linked `sum-fluid` to `fluid-continuity` and `sum-opamp` to
  `opamp-summing` for both operations in the operation matrix.
- [x] Synchronized the matrix audit: 32 rows, 9 exact routes, 1 exact algorithm, 9 mechanism links.
- [x] Added the ideal op-amp summing/difference route, its mechanism card and
  independent fixed-vector target adapters; device values and measured
  amplifier evidence remain explicit gaps.
- [x] Added the normalized-flow `fluid-continuity` target adapter and fixed
  vectors; device binding, pressure/flow scaling and measured evidence remain
  explicit gaps.
- [x] Added `cent envelope`, an exact finite-direction minimum-area envelope
  over rational points, with exact corners and an explicit finite-direction
  limitation. Its physical/liquid-crystal interpretation is optional.
- [x] Made the envelope discoverable as `bounding_box`: `cent discover` returns
  it as an `exact-algorithm` method, and `cent matrix` carries one
  `orientation-envelope` row without counting it as a physical route.
- [x] Added `cent pipeline` and `docs/PIPELINES.md`. Stages and named-wire
  handoffs come from route programs; the delta-sigma feedback edge is explicit.
- [x] Added `cent hypothesis`, a pre-admission structural view over declared
  cards and review leads. It uses `CentWheel`/`KnowledgeState`, requires a
  primitive-chain overlap for card matches, and never changes
  `supported_operations`.
- [x] Recorded the Q-tensor and Bresenham examples as `DOESNT-KNOW` leads with
  explicit proof, test and definition needs, not as mechanisms or transfers.
- [x] Ran H1 on 2026-11-11. The Q-tensor lead was retired after an exact
  invariant obstruction proof; Bresenham was retained narrowly after an exact
  one-tick proof, range test and negative control. Records are in
  `docs/hypothesis-resolutions/`; initial absence-based records are preserved
  under `history/`, and the pre-admission state is unchanged.

## P1 — next work

### 1. Relaxation classification — complete

- [x] Add one declared relaxation record to `cent-transfer/1`, with `exact`,
  `asymptotic`, `parameter-dependent` or `unclassified` and a basis.
- [x] Require a basis and target-level evidence for any non-`unclassified`
  value; require a matching target, artifact and target tests.
- [x] Default retrieved candidates to `unclassified`; a candidate-only transfer
  has no target relaxation evidence.
- [x] Add negative tests for a missing basis, missing target, source-only
  evidence, missing artifact/tests and an unsupported class.
- [x] Do not classify the RC/clock `0.632` behavior as an exact discrete step.

The exact KCL and fluid sum targets and the KCL difference target are recorded
`exact`. Delta-sigma and sqrt remain `unclassified` because their fixed-vector
certificates do not establish a general relaxation class. The free-text `relaxed` list remains separate from the
new classified record.

### 2. Ten-operation corpus

- [ ] Add operations only with a declared signature, semantics, reference and at
  least one fixed test.
- [ ] Name a target adapter for each operation, or record the exact missing
  adapter.
- [ ] Add positive and negative controls for every new operation.
- [ ] Keep the existing `sqrt`, `sum`, `difference` and `quantized_carry`
  contracts unchanged unless their tests change.

### 3. Exact axis-aligned packing witness

- [ ] Add an exact separating-axis check for the existing axis-aligned square
  states, with rational projection intervals.
- [ ] Emit a `cent-packing-certificate/1`-style witness or an explicit overlap
  gap.
- [ ] Keep the global optimality gap: a feasible witness is not a smallest-box
  proof.
- [ ] Treat the finite direction set as a declared computational limit, not a
  physical gate; add rotations when the algorithm declares them.

## P2 — deferred design work

- [x] Structural micro-pipeline decomposition from declared route programs,
  including typed stage data and explicit feedback handoffs.
- [ ] Execution or composition of arbitrary sub-operation contracts remains
  deferred; the current pipeline does not invent a handoff between separately
  discovered methods.
- [ ] Cross-domain benchmark for `sum-fluid` to information routing, only after
  a target contract and target tests exist.
- [ ] Existing two-tick graphics-to-quantized-arithmetic transfer remains open;
  the one-tick proof is evidence, not a promoted route.
- [ ] Global or rotated square packing, which needs a separate search and
  certificate design.

## Guardrails

- A shared invariant is not an isomorphism.
- A pre-admission lead is not a supported operation or mechanism card.
- A structural score is not an equivalence proof.
- A mapping step is not an executable composition.
- A candidate is not a validation.
- A feasible packing is not a global optimum.
- No mechanism, parameter, target adapter or measured result is invented to
  fill a row.

## Verification

```bash
python3 tests/test_transfer_contracts.py
python3 tests/test_discovery.py
python3 tests/test_assembly.py
python3 tests/test_discovery.py
python3 tests/run_all.py
python3 cent transfer sum --json
python3 cent matrix --operation sum --json
python3 cent envelope --point 0,1 --point 1,0 --point 0,-1 --point=-1,0 --json
python3 cent discover "compute a minimum-area bounding box for points" --json
python3 cent matrix --operation bounding_box --json
python3 cent pipeline quantized_carry --json
python3 cent hypothesis
python3 cent hypothesis bounding_box --json
python3 cent hypothesis quantized_carry --json
```
