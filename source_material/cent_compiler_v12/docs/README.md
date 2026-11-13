# Documentation

For a question, start with the addressed-part map in
[`KNOWLEDGE_ATLAS.md`](KNOWLEDGE_ATLAS.md); it finds the owning section without
creating another copy. For authority, start with
[`../DIRECTIVE.md`](../DIRECTIVE.md) for the binding objective, rules, work
order and scoreboard, then [`../WORKFLOW.md`](../WORKFLOW.md) for execution state
and the D1–D7 task board. For the current capability boundary and open gaps,
read [`CURRENT_SCOPE.md`](CURRENT_SCOPE.md). The design rationale and historical
phase record are in
[`TRANSFER_COMPILER_OBJECTIVE.md`](TRANSFER_COMPILER_OBJECTIVE.md); the
completed workstream ledger and blocked-item register is
[`../PHYSICAL_COMPILER_ROADMAP.md`](../PHYSICAL_COMPILER_ROADMAP.md); it is
historical and is not an active roadmap. Start with
the root [`README.md`](../README.md) for installation, quick-start commands and
the current test baseline. The
previous local product roadmap is archived at
[`archive/PHYSICAL_COMPILER_ROADMAP_PRODUCT_COMPLETE.md`](archive/PHYSICAL_COMPILER_ROADMAP_PRODUCT_COMPLETE.md);
the older full build record is at
[`archive/PHYSICAL_COMPILER_ROADMAP_COMPLETED.md`](archive/PHYSICAL_COMPILER_ROADMAP_COMPLETED.md).
The historical expansion blueprints and Hypothesis Engine reference are under
[`archive/expansion/`](archive/expansion/).

## Authority chain

Use these documents for current state; use the ledgers and archives for history,
not for a second opinion on what is current.

| Question | Owner |
|---|---|
| Why the project exists and what may be started next | [`../DIRECTIVE.md`](../DIRECTIVE.md) |
| What is being executed now | [`../WORKFLOW.md`](../WORKFLOW.md) |
| What works, what is declared, what is blocked | [`CURRENT_SCOPE.md`](CURRENT_SCOPE.md) |
| Install, commands and the live gate count | [`../README.md`](../README.md) |
| Where a claim lives and how to stitch a reading path | [`KNOWLEDGE_ATLAS.md`](KNOWLEDGE_ATLAS.md) |
| Completed workstream and phase history | [`../PHYSICAL_COMPILER_ROADMAP.md`](../PHYSICAL_COMPILER_ROADMAP.md), [`TRANSFER_COMPILER_OBJECTIVE.md`](TRANSFER_COMPILER_OBJECTIVE.md), [`archive/`](archive/) |
| Detailed evidence claims | [`RESULTS.md`](RESULTS.md) |

`DEVELOPMENT_AUDIT.md` and `VALIDATION_REPORT.md` are dated audits, not current
status pages. The 22 `applications/` notes are legacy show-work; current
transfer bundles are in `examples/transfer/`.

## Guides

- [`CURRENT_SCOPE.md`](CURRENT_SCOPE.md) — current
  capability boundary, known loose ends and proposal examples; it does not set
  priority.
- [`RESULTS.md`](RESULTS.md) — detailed evidence summary moved out of the root
  README; an evidence index, not a status page.
- [`KNOWLEDGE_ATLAS.md`](KNOWLEDGE_ATLAS.md) — addressed document parts,
duplicate detection and stitching; the file-keeping method.
- [`../DIRECTIVE.md`](../DIRECTIVE.md) — binding objective, rules, D1–D7 work
  order and scoreboard.
- [`../WORKFLOW.md`](../WORKFLOW.md) — execution tracker, task board and D1
  checklist.
- [`GUIDE.md`](GUIDE.md) — how to enter a £, accepted syntax, examples and the
  cross-domain ¢ → ∆ path.
- [`CENT_FRAMEWORK.md`](CENT_FRAMEWORK.md) — canonical architecture of the
  £ → ¢ → ∆ compiler.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — where to add a wheel, contract, route,
  substrate row and test.
- [`TRANSFER_COMPILER_OBJECTIVE.md`](TRANSFER_COMPILER_OBJECTIVE.md) — design
  rationale, mechanism/transfer contracts and historical phase record.
- [`TRANSFER_PROPOSALS.md`](TRANSFER_PROPOSALS.md) — `cent propose` bundles,
  readiness states and the review-to-validation handoff.
- [`MACHINES.md`](MACHINES.md) — the experimental whole-machine side-arm:
  complete function trees, compiler-selected parts and the executable
  `sigma-delta-sqrt` concept.
- [`../examples/transfer/README.md`](../examples/transfer/README.md) — current
  transfer proposal bundles; the 22 legacy `.cir` files are physical show-work.
- [`../applications/README.md`](../applications/README.md) — shared pipeline,
  parameters, run commands and W1↔W6 table for the 22 legacy proposals.
- [`../examples/holdout/README.md`](../examples/holdout/README.md) — D6 frozen
  retrodictive corpus, dated labels and measured report.

## Architecture and contracts

- [`TYPED_GRAPHS.md`](TYPED_GRAPHS.md) — typed route graphs and lowerings.
- [`MATERIAL_CONTRACTS.md`](MATERIAL_CONTRACTS.md) — the 73 declared material
  contracts.
- [`WHEEL_MAPPING.md`](WHEEL_MAPPING.md) — graph proofs, declared bridges and
  text-only candidates.
- [`ASTRO_COSMO_WHEELS.md`](ASTRO_COSMO_WHEELS.md) — sourced W26/W27
  astrophysics and cosmology equations, dimensions and conventions.
- [`DESIGN_SOLVER.md`](DESIGN_SOLVER.md) — constrained design spaces and
  verification plans.
- [`METHOD_COMPARISON.md`](METHOD_COMPARISON.md) — independent route comparison.
- [`OPERATION_MATRIX.md`](OPERATION_MATRIX.md) — operation × method evidence
  matrix and explicit gaps.
- [`ORIENTATION_ENVELOPE.md`](ORIENTATION_ENVELOPE.md) — exact finite-direction
  minimum-area envelope and its optional interpretation.
- [`PIPELINES.md`](PIPELINES.md) — exact route micro-pipelines, stage contracts
  and feedback handoffs.
- [`HYPOTHESES.md`](HYPOTHESES.md) — pre-admission structural leads, knowledge
  states and the explicit card/contract/target-test/review promotion gate.
- [`semantics.md`](semantics.md) — exact-core conventions.
- [`extensions.md`](extensions.md) — vocabulary reconciliation and limits.

## Routes and physical artifacts

- [`DELTA_SIGMA_DEMO.md`](DELTA_SIGMA_DEMO.md) — delta-sigma carry route.
- [`LOG_DOMAIN_SQRT.md`](LOG_DOMAIN_SQRT.md) — log-domain compute route.
- [`OPAMP_MULTIPLIER_SQRT.md`](OPAMP_MULTIPLIER_SQRT.md) — feedback compute
  route.
- [`OPAMP_SUM.md`](OPAMP_SUM.md) — ideal op-amp summing/difference route and
  its physical gaps.
- [`DEVICE_BINDING.md`](DEVICE_BINDING.md) — declared device quantities and
  error budgets.
- [`PHYSICAL_NETLIST.md`](PHYSICAL_NETLIST.md) — reference netlist and
  floorplan.
- [`FABRICATION.md`](FABRICATION.md) — declared geometry, DRC and parasitics.
- [`DYNAMICS.md`](DYNAMICS.md) — sampled-data and nonlinear transients.

## Validation and studies

- [`DEVELOPMENT_AUDIT.md`](DEVELOPMENT_AUDIT.md) — observed operation coverage
  and concrete gaps; it is a ledger, not a work order.
- [`evidence/`](evidence/) — runnable decision records, including the current
  live-GLM breadth refusal.
- [`QUESTION_CORPUS.md`](QUESTION_CORPUS.md) — fixed GLM/cent CLI questions
  with exact answers, refusals and explicit gaps.
- [`VALIDATION_REPORT.md`](VALIDATION_REPORT.md) — validation history.
- [`MOVE_CORPUS.md`](MOVE_CORPUS.md) — declared move-corpus audit.
- [`LEECH_STUDY_AUDIT.md`](LEECH_STUDY_AUDIT.md) — external study audit.
- [`LEECH_ISOMORPHISM.md`](LEECH_ISOMORPHISM.md) — move-class isomorphism.
- [`GLM_LEAN_REVIEW.md`](GLM_LEAN_REVIEW.md) — source-level Lean review; no
  Lean build was run.
- [`GLM_CENT_APPLICATION_AUDIT.md`](GLM_CENT_APPLICATION_AUDIT.md) — GLM gaps
  mapped to cent primitives, scalar application probes and false-match findings.
- [`GLM_DIRECT_QUESTIONS_AUDIT.md`](GLM_DIRECT_QUESTIONS_AUDIT.md) — direct
  Leech/path/XOR/packing/Rule30 questions, narrow utilities and method gaps.
- [`PACKING_PRESSURE_SETTLING.md`](PACKING_PRESSURE_SETTLING.md) — W36/W37
  pressure-settling packing analogy and its optimality gap.
- [`archive/PHYSICAL_COMPILER_ROADMAP_COMPLETED.md`](archive/PHYSICAL_COMPILER_ROADMAP_COMPLETED.md)
  — older completed build record.
- [`archive/PHYSICAL_COMPILER_ROADMAP_PRODUCT_COMPLETE.md`](archive/PHYSICAL_COMPILER_ROADMAP_PRODUCT_COMPLETE.md)
  — product roadmap archive; local work complete, external evidence blocked.

## Conventions

- Every accepted capability names its exact contract, declared material or
  explicit gap.
- A text match is not a graph proof.
- A declared bridge is not an axiom proof.
- A proposal is not a fabricated device.
- Test counts in the README refer to the canonical `tests/run_all.py` gate.
