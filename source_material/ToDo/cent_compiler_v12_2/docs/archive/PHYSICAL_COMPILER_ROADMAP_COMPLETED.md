# Physical Compiler — Completed Roadmap Archive

> **Archive snapshot.** This is the completed build record through D4, kept for
> traceability. External-only items remain listed as open. The forward plan is
> [`../../PHYSICAL_COMPILER_ROADMAP.md`](../../PHYSICAL_COMPILER_ROADMAP.md).

Status: **method discovery with capability-status visibility, a flattened global
axiom graph with exact multi-input graph derivation, graph-backed wheel
grounding, k-best paths and a
336/336 spoke regression, uniform output certificates, a declared move-corpus audit, reviewed capability records for all 41 contracts, ordered multi-step goal parsing and wheel navigation, three exact typed routes with structural topology audits, declared device bindings with independent derived-quantity audits, one declared typed wheel bridge, a constrained design solver with exact declared-pole bandwidth checks, topology-derived reference netlists/floorplans, a declared fabrication-geometry layer with an independent DRC, exact Pareto design ranking, exact sampled-data and continuous-time clocked delta-sigma transients, adaptive step-doubling compute-route transients, and continuous bounded-state certificates for both compute routes implemented in the CLI and browser; multi-step composition, a global transient bound within the 1e-3 V target, and measured-device evidence are not done.**

This document is the ordered build list. A checked item has code and a test; it
does not mean the whole physical compiler is complete. The invariant is:

> Curate knowledge, not answers. Every route is traceable to an exact contract,
> a declared material row, a documented simulation/demo, or a wheel candidate.

## Problem the compiler must accept

A user problem is not just a formula. The requested problem IR is:

```text
problem text
  -> ordered goal steps (then, ;, ->, →)
  -> behaviour: compute | carry | solve | track
  -> object: irrational | root | equilibrium | power | phase | explicit primitive
  -> constraints: analog/physical, exact, domain, bandwidth, accuracy
  -> candidate methods across domains
  -> coverage and missing-material report
  -> (next) a selected path with a port graph, parameters and netlist
```

The example

```text
"compute an irrational value with an analog method"
```

is interpreted as two related but distinct goals:

1. **compute** a specified irrational relation, such as `sqrt(x)`;
2. **carry/represent** a known irrational value as a physical signal.

Delta-sigma is evidence for (2), not a square-root algorithm. The compiler must
keep those claims separate.

## Running list

### D0 — Semantic invariants

- [x] Exact `Fraction` arithmetic remains the execution authority.
- [x] No binary floating point in the exact core.
- [x] No invented methods, materials, simulations or wheel proofs.
- [x] Every candidate labels its evidence and its gaps.
- [x] Wheel texts are candidate grounding, not proofs.

### D1 — Problem IR and query interpretation

- [x] Recognise behaviour (`compute`, `carry`, `solve`, `track`).
- [x] Recognise object (`irrational`, `root`, `equilibrium`, `power`, `phase`,
  explicit primitive).
- [x] Parse constraints (`analog/physical`, `exact/certified`, domain).
- [x] Separate “compute” from “carry”.
- [x] Return a clarification state for unknown goals.
- [x] Add explicit accuracy, range and cost constraints to the design solver.
- [x] Add bandwidth constraints over the declared small-signal poles; compute-route monotone large-signal stability is certified separately.
- [x] Add a grammar for multi-step goals (for example “compute sqrt, then carry
  the result as a bitstream”); steps are parsed and discovered independently,
  while composition remains an explicit gap.

### D2 — Capability index

- [x] Map exact contracts to capability tags.
- [x] Include provenance/basis for every capability entry.
- [x] Keep the index separate from route selection.
- [x] Add a reviewed capability record for every one of the 41 contracts;
  every record has tags and an explicit contract-semantics basis, without
  claiming a physical route.
- [x] Distinguish `implemented_verified`, `implemented_tested`, proof-pending
  and unsupported at selection time; discovery carries the contract status and
  display label, and method cards render it.
- [x] Add automated coverage checks against `vocabulary.ALL_PRIMITIVES`:
  contracts, capability report, evaluator handlers and wire-kind tables.


### D3 — Material expansion across domains

- [x] Use `EXPANSIONS` for composite primitives.
- [x] Use `DELTA_SUBSTRATE` for atomic and composite routes.
- [x] Merge overlapping expansion/substrate rows instead of double-counting.
- [x] Report the domains and carriers of each candidate.
- [x] Report ingredient coverage for composites.
- [x] Add a declared electrical quantizer material (flash ADC / comparator bank)
  and register `quantize` with the ∆ enumerator.
- [x] Add a declared clocked-register material for `delay`.
- [x] Add typed contracts for `accum`, `quantize` and `delay` with ports, laws,
  parameters, operating ranges and failure modes (`assembly.py`).
- [x] Add typed contracts for `log`, `scale` and `exp`, including certified
  interval ports and declared gain (`assembly.py`).
- [x] Add a route-level exact program and port graph for the delta-sigma loop.
- [x] Add a route-level exact program and certified-enclosure graph for the
  log-domain square-root extractor.
- [x] Add a steady-state algebraic-feedback route for the op-amp + multiplier
  square root, with an exact bisection solver and an independent quadratic
  check.
- [x] Add declared device bindings for all three routes: exact device-law
  checks and conservative static error budgets (`device.py`).
- [x] Replace the remaining flat material rows with typed component contracts.
  All 38 substrate and 35 expansion rows resolve through a
  `cent-material-contract/1` view with typed ports, parameters, law/behavior,
  operating range, failure modes and provenance; the compact rows remain
  indexes, not the graph-facing representation.
- [x] Add a topology feasibility check for arbitrary assembled compositions (`assembly.audit_route_topology`); malformed roles, port arity, parameters and program wires return `gap`.
- [x] Add parameter selection and exact constraint propagation over declared
  design alternatives (`design.py`).
- [x] Add topology-derived reference netlist and schematic stage floorplan
  emission from a selected binding (`physical.py`).
- [x] Add an exact sampled-data RC/clock model for delta-sigma, with explicit
  settling gaps (`dynamics.py`).
- [x] Add declared junction/load/closed-loop parameters and nonlinear
  large-signal backward-Euler transients for the log-domain and feedback routes.
- [x] Add adaptive step-doubling control with exact local-budget acceptance for
  those compute-route transients.
- [x] Add continuous forward-invariance bounded-state certificates for both
  compute routes, with an explicit too-small-box failure result exposed through
  the CLI and HTTP API.
- [x] Add certified local-truncation global ODE bounds for those transients. The bounds are valid but still exceed the 1e-3 V target, so target closure remains open.
- [x] Add continuous-range certificates from declared monotone error/bandwidth directions and endpoint stress; undeclared non-monotone ranges remain gaps.
- [x] Add monotone large-signal stability certificates for both compute routes.
- [x] Add fabrication geometry: footprints, stackup, DRC, parasitics and thermal
  placement from the reference topology. `cent fabricate` emits generic land
  patterns, a four-layer stackup, an orthogonal escape/bus route, exact lumped
  R/C/L parasitics, a single-node junction thermal model and an independent DRC;
  single-pin behavioral control labels are declared unrouted rather than
  invented.

### D4 — Wheel grounding

- [x] Find wheels whose axioms/cases/quantities mention the primitive.
- [x] Find component/material words in wheel text.
- [x] Expose the matching wheel and the matched terms.
- [x] Attach declared analogies when a wheel pair has one.
- [x] Turn text matches into typed quantity/port mappings where a declared
  bridge exists (`wheel_mapping.py`).
- [x] Require a dimensional residual and a declared bridge law before claiming
  a cross-domain mapping; unmatched matches remain explicit gaps.
- [x] Register the first bridge: log-domain square root ↔ W24 diode quantities,
  with exact SI dimensions and a zero residual.
- [x] Use the global axiom graph and proof search rather than keyword hits.
  `axiom_graph.ground_primitive` uses declared monomial relation queries and
  accepts a wheel only when `derive_from` proves the target from the other
  quantities with exactly one declared axiom. Discovery attaches the result as
  `wheel_grounding`; text matches remain `text_only` candidates and earn no
  grounding score. The W24 log-domain bridge remains a separate
  `declared-bridge`, not a fabricated graph proof of the Shockley law. The
  first graph queries cover square-root and product relations; unsupported
  primitives return an explicit gap rather than falling back to keywords.

### D5 — Evidence and coverage

- [x] Report exact-contract, simulation and application evidence separately.
- [x] Detect a declared evidence file that is missing.
- [x] Report missing ingredient substrates. Delta-sigma now has typed
  contracts, an exact route model and a declared device binding; a reference
  netlist/floorplan and a declared fabrication geometry are also available,
  while measured device models and a manufactured board remain open.
- [x] Report route-level model coverage; three routes are exact, the others
  are not yet assembled.
- [x] Add the first exact route-level simulation (delta-sigma carry loop).
- [x] Add the first exact compute route with an independent `sqrt_q` bracket
  check (log-domain square root).
- [x] Report device-binding coverage; all three exact routes have declared
  reference designs and reference netlist/floorplan emission, while fabrication
  geometry and measured evidence remain open.
- [x] Report sampled-data coverage: all three routes return finite traces with
  explicit nonlinear-transient or sampled-data limits.
- [x] Add route-level nonlinear transient simulation for every selected path.
  `DynamicResult.nonlinear_transient` now carries a finite coverage block on
  all three selected routes. Delta-sigma runs a continuous-time, four-substep
  RC transient with a clocked comparator and feedback held per clock; the two
  compute routes expose their existing adaptive nonlinear transients as a
  coverage block. The delta-sigma substeps use the exact exponential enclosure
  with outward 12-place state rounding, and the comparator decision remains
  explicit. This is a bounded route model, not a smooth-device or SPICE run.
- [x] Add an independent exact checker for generated device parameters (`device.audit_device_parameters`); every binding payload carries its audit and tampered quantities fail explicitly.
- [x] Add a Pareto/constraint-based ranking instead of one scalar score. Hard
  constraints filter first, exact non-dominated sorting exposes the Pareto
  layers, `exact-static` uses cost and worst-probe error, `dynamic-aware` adds
  only the certified slowest-pole lower bound, and the cheapest front point is
  selected with an exact tie-break; no weighted score or noise term is invented.
- [ ] Add fabricated-device evidence only when a real device exists.

### D6 — Method selection and planning

- [x] Rank candidates by goal fit, exactness, evidence, wheel grounding and gaps.
- [x] Group results by compute/carry/solve role.
- [x] Support a domain filter.
- [x] Expose declared device bindings in discovery and the CLI.
- [x] Assemble one contract into a typed route graph and exact simulation
  (`delta-sigma-first-order`).
- [x] Assemble a compute contract into a typed route graph and certified
  enclosure check (`sqrt-log-domain`).
- [x] Assemble the op-amp + multiplier feedback compute route with an exact
  algebraic solver and independent checker.
- [x] Select a bound route’s declared design point under explicit accuracy,
  range and cost constraints (`design.py`).
- [x] Expand every selected method into a typed `¢` graph.
  All three selected routes now emit `cent-typed-graph/1`: delta-sigma has six
  nodes, log-domain three and the feedback route four. Named wires, primitive
  nodes, parameters and feedback edges are preserved from the exact route or
  its declared algebraic composition.
- [x] Lower every graph to components and ports.
  Physical nodes lower to `cent-component-contract/1` with explicit contract
  port-to-wire maps; arithmetic/control glue lowers to exact-core with no
  physical-device claim. The feedback route keeps its algebraic loop explicit.
  Route JSON carries the graph, and `cent graph` emits it directly.
- [x] Emit a parameterized design and an executed/gapped verification plan
  (`cent solve`).
- [x] Emit a reference netlist, connected nets and schematic stage floorplan
  from the selected binding (`cent physical`).
- [x] Run the selected route's declared sampled-data model when timing
  quantities exist (`cent dynamics`).
- [x] Attach an advisory post-solve fabrication audit to a solved design.
  `cent-design/1` carries `cent-fabrication-audit/1` with exact DRC/thermal
  checks, failed-check names, unrouted nets and gaps. It never changes
  candidate selection, and the full geometry remains a separate
  `cent fabricate` command.

### D7 — Global path compiler

- [x] Flatten the 90 wheel axioms into one typed graph.
  `cent_compiler/axiom_graph.py` emits `cent-axiom-graph/1` with 37 wheel
  nodes, 90 axiom nodes, 209 wheel-local quantity nodes, 64 exact dimension
  nodes, 90 containment edges and 279 quantity mentions. `cent axioms` exposes
  it in text or JSON. The 44 resolvable junction edges and 5 resolvable
  non-identity edges are declared edges; the other seven declared endpoint
  records are explicit gaps. Shared names remain wheel-local without a
  declared junction, so this is a typed projection, not proof search.
- [x] Generalize `derive_from` beyond one wheel and two inputs.
  `axiom_graph.derive_from` accepts any number of wheel-qualified inputs and
  uses declared junction identities transitively over a bounded slice: the
  target/input wheels plus one junction hop. It enumerates exact sparse support
  up to `--max-axioms` (default 4), and returns the exact formula, coefficient,
  input exponents, used axioms with rational weights and the junction paths
  that actually bridge requested labels. Disconnected components, exhausted
  support and missing endpoints are explicit gaps; bounded cross-wheel path
  search is now available, while exhaustive search is not claimed. The legacy
  two-input `wheels.derive_from` remains the 336-spoke corpus generator.
- [x] Search cross-wheel paths with substitutions and proof steps.
  `derive_from(..., strategy="substitution")` performs bounded backward
  substitution over the declared axiom scope, solves each equation for one
  quantity from already-derived quantities, and records exact substitution
  steps with rational exponents and coefficients. The selected axioms are
  rechecked by the same exact relation-vector solver; a path that does not
  reproduce an exact combination is discarded. `strategy="auto"` keeps the
  direct one-junction-hop path first and falls back to this bounded search;
  `strategy="direct"` preserves the original behavior. The W1/W15 regression
  returns `W1.power = W1.voltage * W15.charge / W15.time` through two exact
  substitutions.
- [x] Re-derive the 336 existing spokes as a regression corpus.
  `axiom_graph.regress_legacy_spokes()` re-derives every formula over the
  global graph: 336/336 exact formula matches. Thirty-six legacy entries carry
  an extra input that their formula never uses; the graph correctly rejects a
  disconnected extra input, so the regression asks for the used inputs and
  reports those 36 redundant entries explicitly. See
  `test_discovery.py`.
- [x] Expose k-best paths, assumptions and missing-bridge reports.
  `derive_from(..., k=N)` collects up to eight distinct exact derivations in
  the bounded target/input plus one-junction-hop scope. It returns the best
  path plus alternatives, proof steps (axiom and junction records), explicit
  assumptions, and structured missing-bridge records when components are
  disconnected. The W5/W38 check returns two paths: W38 torque × angular
  velocity through the declared junction, and W5 force × velocity.

### D8 — Front-end integration

- [x] `cent discover "<problem>"` CLI command.
- [x] `GET /api/discover?q=...` endpoint.
- [x] Browser “Find methods” panel.
- [x] `cent assemble delta-sigma` CLI command.
- [x] `cent assemble sqrt-log` CLI command with precision and tolerance.
- [x] `cent assemble sqrt-feedback` CLI command with gain, iteration and
  tolerance controls.
- [x] `cent bind delta-sigma`, `cent bind sqrt-log` and `cent bind sqrt-feedback`
  CLI commands.
- [x] `cent solve` CLI command with accuracy, range, cost and declared-pole bandwidth constraints.
- [x] `GET /api/design` and `GET`/`POST /api/solve` browser endpoints.
- [x] Browser **Design solver** tab with exact inputs, candidate results and
  verification plans.
- [x] Let a chosen method open the corresponding declared design space.
- [x] `cent physical` CLI command for all three selected routes.
- [x] `GET`/`POST /api/physical` browser endpoint and a solved-card emission
  action in the Design solver tab.
- [x] `cent dynamics` CLI command for the delta-sigma loop and the two compute
  certificate reports, including optional caller-supplied certificate boxes.
- [x] `GET`/`POST /api/dynamics` browser endpoint and a solved-card dynamic
  action in the Design solver tab, including caller-supplied certificate boxes.
- [x] Expose all three exact route models and simulations in discovery.
- [x] Let a chosen method open the corresponding wheel/material view; wheel
  candidate pills switch to the wheel panel and open the selected wheel.
- [x] Show the pipeline trace (interpret → seed → expand → ground → rank → simulate → bind → netlist).
- [x] Add method comparison and export. `cent compare` solves selected declared
  routes independently under shared constraints, preserves per-route Pareto
  ranks, exposes `GET`/`POST /api/compare` and a Design-tab comparison card, and
  exports JSON or Markdown with no cross-route scalar winner.

### D9 — Verification and deprecation

- [x] Focused discovery tests for interpretation, domains, evidence and gaps.
- [x] Focused typed-route and exact-simulation tests.
- [x] Focused device-binding tests.
- [x] Focused constrained-design tests (`test_design.py`).
- [x] Browser/API tests for the design catalog, solve paths, cross-route
  comparison, invalid constraints and reference-netlist emission.
- [x] Focused reference-netlist and floorplan tests (`test_physical.py`).
- [x] Focused sampled-data tests (`test_dynamics.py`).
- [x] API regression test.
- [x] Add one canonical command for the eleven-suite gate (`tests/run_all.py`),
  with a non-zero exit on any failing suite.
- [x] Move all `EXPANSIONS`/`DELTA_SUBSTRATE` rows behind component contracts.
  Discovery resolves each expanded method through its typed material contract
  and carries the contract in the discovery payload.
- [x] Remove template-by-first-op selection from the compile path.
  `spice_emitter.select_spice_template` matches the complete `¢` operation set
  against declared required/allowed envelopes. The console, `cent compile`,
  `cent spice` and `emit_for_cent_dag` share it; unmatched or ambiguous sets
  return an explicit gap with no netlist, and the material bundle records the
  template status and detail. `test_ui.py` covers a DAG containing `sqrt` plus
  `mult` that must not inherit the sqrt template.
- [x] Make every compiler output carry a certificate or an explicit gap.
  Public CLI/API JSON payloads and saved `cent-material/1` bundles now carry
  `cent-output-certificate/1` with the subject schema, declared checks, gaps,
  status and an explicit non-physical claim. The shared helper is
  `cent_compiler/output_certificate.py`; a payload is `certified` only when all
  listed checks pass and no gap remains, otherwise `partial` or `gap`. CLI and
  browser transports attach the certificate to assemble, graph, axioms, derive,
  solve, compare, physical, fabricate, dynamics, discovery and report outputs.
- [x] Re-run the 336-spoke and 143-case corpora after the global graph migration.
  The 336/336 spoke regression is exact. The 143-case re-run now gives 143/143
  dimensional agreement and 143/143 derivability agreement after correcting the
  underlying data: W21's squared fracture-toughness law, W22/W24 dimension rows,
  W29's spin-diffusion law, W32's wetting dimension, W34's hydraulic-resistance
  exponent, and W37's quotient/product cases. W25/W35 are retained as explicit
  non-SI model conventions. `wheels.regress_declared_cases()` returns `ok` with
  no mismatches. See the 143-case reconciliation bullet in `README.md`.
- [x] Reconcile the 21 declared case-expectation mismatches by correcting the
  dimensions and axioms, not by changing the report status. The W21 correction
  adds three valid spokes, so the regression is now 336/336, not 333/333.

### D10 — External corpus adapters

- [x] Add a declared move-corpus loader and exact audit (`cent moves`).
  `cent-move-corpus/1` carries move ids, optional exact weights, optional
  integer vectors and ordered sequences. The audit reports sequence, move and
  transition counts, exact in-sample bigram top-1 with deterministic lexical
  tie-break, and optional exact net-displacement/squared-norm statistics. It
  labels the absent held-out split and does not claim a Leech heat kernel,
  Griess product, Lean certificate or codebook optimizer.
- [x] Reconstruct the 442-file GLM corpus and reproduce the separate study's
  45.8% move result. The study protocol subtracts only the held-out file's
  count of the evaluated pair: 681,926/1,486,741 = 45.8672% (45.8% rounded). A
  strict file holdout gives 46.3422%; `--holdout study|strict` keeps the two
  protocols explicit. See `LEECH_STUDY_AUDIT.md`.
- [ ] Add 24-dimensional Leech generator/weight data and an exact finite-walk
  Green's-function solver with an explicit finite quotient or boundary.
- [ ] Add Griess algebra multiplication, the Parker-loop cocycle and the Monster
  action; no multiplication tensor is currently declared.
- [ ] Add Lean project/elaborator integration for dependent-type certificates;
  all current theorem labels remain Lean-pending. A source-level review of the
  adjacent GLM Lean tree found `Wheels/CentWheels.lean`,
  `IntakeChecks/Derivability.lean` and `ConnectedMachine.lean` directly relevant
  to the wheel/derivation layer, and `Shortcut/Leech.lean` plus the Golay files
  relevant to the Leech bridge. No Lean build was run. See
  `GLM_LEAN_REVIEW.md`.
- [ ] Add Viazovska/modular-form codebook optimization; no codebook corpus or
  packing objective is currently declared.

## Current slice: what is actually implemented

The `cent discover` path performs:

```text
problem text
  -> parse_problem() and ordered GoalStep parsing
  -> capability match over vocabulary.CONTRACTS
  -> typed material contracts over EXPANSIONS + DELTA_SUBSTRATE
  -> primitive/component text search over wheels/*.json
  -> evidence, route and declared device-binding report
  -> ranked, grouped JSON / terminal output
```

The `cent assemble delta-sigma` path performs:

```text
typed component contracts
  -> exact-core Program (sum, neg, accum, quantize, sat, delay)
  -> static analysis and feedback check
  -> exact rational simulation with a per-tick trace
  -> route plan + explicit device/fabrication gaps
```

The `cent assemble sqrt-log` path performs:

```text
typed component contracts
  -> exact-core Program (log, scale, exp); no hidden sqrt instruction
  -> certified rational enclosures at a declared precision
  -> independent sqrt_q bracket comparison
  -> route plan + explicit device/fabrication gaps
```

The `cent assemble sqrt-feedback` path performs:

```text
typed multiplier and amplifier contracts, plus exact sum glue
  -> steady-state residual A*(x - k*y^2) - y
  -> exact bisection on a rational bracket
  -> independent quadratic checker + ideal sqrt_q comparison
  -> route plan + explicit device/fabrication gaps
```

The `cent graph` path performs:

```text
selected exact route (or declared algebraic feedback composition)
  -> typed ¢ nodes over named wires and parameters
  -> component lowerings with contract port maps
  -> exact-core lowerings for sum/neg/sat glue
  -> stateful or algebraic feedback-edge markers
  -> explicit gaps for any lowering alias
```

The `cent bind` path performs:

```text
selected exact route
  -> declared reference quantities (voltage, current, R, C, clock, T, I_s)
  -> exact device-law checks and one independent device-law evaluation
  -> conservative static error budget with named terms
  -> explicit netlist, measurement and dynamic-model gaps
```

The `cent solve` path performs:

```text
exact accuracy, input-range and cost constraints
  -> finite declared design alternatives for the selected route
  -> exact binding evaluation at the input and range endpoints
  -> exact Pareto layers over cost, error and (with a bandwidth target) certified bandwidth
  -> cheapest front point satisfying every check and the cost ceiling
  -> parameterized design + executed/gapped verification plan
```

The `cent compare` path performs:

```text
shared requested constraints
  -> independent exact solve for each selected declared route
  -> per-route Pareto front, selected design and explicit gaps
  -> JSON / Markdown export; no cross-route scalar winner
```

The `cent physical` path performs:

```text
selected exact binding
  -> declared route roles and exact component values
  -> connected reference part list
  -> SPICE-shaped behavioral deck
  -> non-overlapping schematic stage floorplan
  -> structural checks + fabrication gaps
```

It does **not** yet:

- generate a fabrication netlist, bias network, manufacturing layout or geometry;
- solve arbitrary component values, prove an arbitrary non-monotone range or model
  dynamic nonidealities;
- prove that a wheel match is a valid physical analogy;
- simulate every candidate route end to end (three routes are exact; the
  others remain candidates);
- execute a multi-step goal as one typed `¢` graph; each selected route now has
  a typed graph, but the parser still exposes per-step candidates without a
  step-to-step handoff;
- guarantee that every possible method is found (the declared tables bound the
  search).

These limits are visible in the result, not hidden.

## Immediate next three tasks

1. **Close the remaining global-error target gap.** Certified local truncation
   and route contraction are implemented, but the conservative bounds are about
   `5.46e8 V` (log) and `1.80e19 V` (feedback), above the `1e-3 V` target. Improve
   the state-local bounds or integrator without relabeling a step-doubling
   estimate as a proof.
2. **Extend continuous range/stability beyond declared monotone routes.** The
   current certificates cover the three declared spaces; arbitrary non-monotone
   terms and undeclared dynamics still return `gap`.
3. **Begin manufacturing evidence.** Simulate the current reference deck and
   add a parasitic/footprint/DRC schema, while keeping measured-device evidence
   external and explicit.

Measured-device evidence and the global axiom-graph proof search remain later
milestones; they need external data/tooling and should not be mixed into the
certification pass above.

## Verification

```bash
cd cent_compiler_v12

# Canonical gate: streams all ten suites and exits non-zero on failure.
python3 tests/run_all.py

# Legacy v2.0 seven-simulation runner
python3 cent test

# Focused runs
python3 tests/test_assembly.py
python3 tests/test_discovery.py
python3 tests/test_moves.py
python3 tests/test_webui.py
python3 tests/test_core.py
python3 tests/test_ui.py
python3 tests/test_binding.py
python3 tests/test_design.py
python3 tests/test_physical.py
python3 tests/test_fabrication.py
python3 tests/test_dynamics.py
```

The route, discovery, browser, device-binding, constrained-design,
material-contract, typed-graph, Pareto-ranking, cross-route-comparison,
reference-netlist, fabrication-geometry and sampled-data tests are expected to
pass (588/588 checks); a manufactured board, measured device
evidence and cross-wheel path search remain later milestones.
