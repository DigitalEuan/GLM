# Documentation

For the current capability boundary and open gaps, start with
[`CURRENT_SCOPE_AND_NEXT_TRACK.md`](CURRENT_SCOPE_AND_NEXT_TRACK.md). The
primary objective and historical phase record are defined in
[`TRANSFER_COMPILER_OBJECTIVE.md`](TRANSFER_COMPILER_OBJECTIVE.md). The
forward plan and priority order are in
[`../PHYSICAL_COMPILER_ROADMAP.md`](../PHYSICAL_COMPILER_ROADMAP.md); use it,
not this index, for “what comes next.” Start with the root
[`README.md`](../README.md) for installation, quick-start commands and the
current test baseline. The
previous local product roadmap is archived at
[`archive/PHYSICAL_COMPILER_ROADMAP_PRODUCT_COMPLETE.md`](archive/PHYSICAL_COMPILER_ROADMAP_PRODUCT_COMPLETE.md);
the older full build record is at
[`archive/PHYSICAL_COMPILER_ROADMAP_COMPLETED.md`](archive/PHYSICAL_COMPILER_ROADMAP_COMPLETED.md).

## Guides

- [`CURRENT_SCOPE_AND_NEXT_TRACK.md`](CURRENT_SCOPE_AND_NEXT_TRACK.md) — current
  capability boundary, known loose ends, current proposal examples and the
  post-G5b development track.
- [`GUIDE.md`](GUIDE.md) — how to enter a £, accepted syntax, examples and the
  cross-domain ¢ → ∆ path.
- [`CENT_FRAMEWORK.md`](CENT_FRAMEWORK.md) — canonical architecture of the
  £ → ¢ → ∆ compiler.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — where to add a wheel, contract, route,
  substrate row and test.
- [`TRANSFER_COMPILER_OBJECTIVE.md`](TRANSFER_COMPILER_OBJECTIVE.md) — primary
  objective, mechanism/transfer contracts and phased action plan.
- [`TRANSFER_PROPOSALS.md`](TRANSFER_PROPOSALS.md) — `cent propose` bundles,
  readiness states and the review-to-validation handoff.
- [`../examples/transfer/README.md`](../examples/transfer/README.md) — current
  transfer proposal bundles; the 22 legacy `.cir` files are physical show-work.

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
  states and the no-automatic-promotion boundary.
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

- [`DEVELOPMENT_AUDIT.md`](DEVELOPMENT_AUDIT.md) — observed operation coverage,
  concrete gaps and the next development areas.
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
