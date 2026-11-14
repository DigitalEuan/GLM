# cent_compiler v2.0 — The £ → ¢ → ∆ Transfer Compiler

> **Binding directive (2026-11-12).** [`DIRECTIVE.md`](DIRECTIVE.md) owns the objective, rules, work order and scoreboard: **originate → bound → benefit**. [`WORKFLOW.md`](WORKFLOW.md) tracks execution. The live gate count is in the statistics row below; this page does not restate the directive's phase status.

The target system takes a computational operation contract, finds mechanisms across physical and information domains that can realize it, constructs an explicit transfer mapping, and validates a target artifact. The existing £ → ¢ → ∆ and SPICE path remains the **physical backend**: it is used when the target is a physical realization, not as the definition of the compiler. The current capability boundary is in [`docs/CURRENT_SCOPE.md`](docs/CURRENT_SCOPE.md); the completed workstream ledger and blocked-item register is [`PHYSICAL_COMPILER_ROADMAP.md`](PHYSICAL_COMPILER_ROADMAP.md) (historical, not an active roadmap).

For that physical backend, the five-layer trace is now part of `cent compile`. Electrical candidates run the existing reference cascade; mechanical, fluidic, thermal, optical and digital candidates keep all five layer slots but report explicit “no declared layer model” gaps. The trace is a screening record, not a device simulation or a measured result.

**Delta-sigma is one benchmark mechanism, not the objective** — an error-feedback/noise-shaping loop from audio electronics that can be transferred into quantized information representation. The compiler must find and validate such transfers, not merely label delta-sigma as a carrier.

---

## Install

Python 3.10 or newer is required. The transfer and exact-core paths use only
the standard library; the legacy delta-sigma simulator and its tests use
`numpy`.

```bash
cd cent_compiler_v12
python3 -m pip install -r requirements.txt
```

---

## Start here

```bash
python3 cent guide
python3 cent compile "velocity = (2 * energy / mass)^(1/2)"
```

`cent guide` is the canonical syntax reference for a £ and the full
¢ → ∆ → proposal path. The compiled output lists the ¢ DAG, every ∆ candidate
count, the ranked proposals and the first explicit gap. Compilation is not
filtered to electrical implementations: mechanical, fluidic, thermal and mixed
domains are ranked by the same declared ¢_cost, and the selected domain and
carrier stay visible.

### Entering a £

A £ is one target relation, quoted as a shell argument:

```text
target = expression
```

Supported forms include `+`, `-`, `*`, `/`, `^`, `**`, parentheses,
`sqrt(x)` (or `x^(1/2)`), `exp(x)`, `log(x)`/`ln(x)` and `tanh(x)`. Unsupported
functions fail explicitly; the compiler does not guess a method.

The full syntax, worked examples and troubleshooting are in
[`docs/GUIDE.md`](docs/GUIDE.md). The documentation index is
[`docs/README.md`](docs/README.md); the extension map is
[`docs/CONTRIBUTING.md`](docs/CONTRIBUTING.md). The current operation-coverage
audit and development gaps are in
[`docs/DEVELOPMENT_AUDIT.md`](docs/DEVELOPMENT_AUDIT.md).

### Your first two £s

```bash
# A compute relation; read the domain and carrier columns in the ranking.
python3 cent compile "y = sqrt(5)"

# A thermal relation; the ranking must still expose its mechanical candidate.
python3 cent compile "heat_rate = thermal_conductivity * area * temperature_gradient"

# A single arithmetic operation also gets its validated transfer handoff.
python3 cent compile "y = 1/x"
python3 cent compile "y = exp(x)" --json
```

Use `cent compile "<£>" --json` for the same result as a tooling payload. The
JSON proposals include each rank's domain, carrier, components and six-axis
cost breakdown. A single `exp`, `log`, `mult`, `div` or reciprocal formula also
carries a `cent-compile-transfer/1` block with the `log-domain-arithmetic`
mechanism, its `glm-reference` fixed-vector result, certificate and handoff
command. A formula with several primitives gets one handoff per executable
stage plus typed stage-interface boundaries: each boundary declares the
producer kind/domain and the consumer port, then checks domain and interface
compatibility. Those boundaries are contract-checked, not target-executed. The
declared `mult -> div` chain `(a*b)/c`, `mult -> reciprocal` chain `1/(a*b)` and
`div -> mult` chain `(a/b)*c` are certified end to end by composed
`glm-reference` adapters over three fixed vectors each, and carry composition
certificates that include the boundary checks. Other compositions remain
`staged` or `partial` with `validated: false` and no composition certificate;
`partial` records the unsupported stages explicitly. `--top N` is a ranking view, not a domain quota: a non-electrical
candidate is not suppressed merely because the first N rows are electrical.

Both relations are exercised by `tests/test_ui.py`; the thermal one also has
the explicit domain-diversity regression. Every ranked row is marked
`not-fabricated`: the text output prints the boundary and the JSON payload
repeats it on each proposal. A proposal is not a fabricated or measured device.

The SPICE template is a separate structural decision over the complete ¢ DAG,
not a domain filter. A missing template is a gap; it does not remove or demote
any ranked ∆ proposal, including non-electrical ones. The JSON `spice.decision`
records `structural: true` and `proposal_effect: none`. The output certificate
requires that contract for both `cent-compile/1` and `cent-material/1`; a
missing or contradictory decision is a certificate check failure that tooling
can reject.

---

## Quick Start

```bash
cd cent_compiler_v12

# Show the £ syntax and the cross-domain pipeline
python3 cent guide

# Compile a £ through the full pipeline
python3 cent compile "velocity = (2 * energy / mass)^(1/2)"
python3 cent compile "y = sqrt(5)" --json

# Discover physical methods for a problem statement
python3 cent discover "compute an irrational value with an analog method"

# Inspect the declared operation × method evidence matrix
python3 cent matrix
python3 cent matrix --operation mult --json

# Inspect the seeded cross-domain mechanism registry
python3 cent mechanism list
python3 cent mechanism delta-sigma-error-feedback --json

# Retrieve transfer candidates for a production operation contract
python3 cent transfer "sqrt" --target glm-reference --json
python3 cent transfer "quantized_carry" --validate --json
cent propose "sqrt" --target glm-reference --json  # portable proposal bundle
python3 cent propose "sqrt" --target glm-reference --out proposals  # write reviewable files
python3 cent propose "sqrt" --trial                       # run ready proposals over fixed vectors
python3 cent trial proposals                              # trial a saved proposal bundle
python3 cent trial proposals proposal-sqrt-to-glm-reference-via-log-domain-sqrt
python3 cent trial --wheel                                # trial every declared operation
python3 cent trial --wheel --json
python3 cent machine list                       # hand-authored concepts and route wrappers
python3 cent machine sigma-delta-sqrt          # compose and run the first machine
python3 cent machine sigma-delta-sqrt --json
python3 cent knowledge atlas                              # address document parts
python3 cent knowledge stitch "operation trial wheel" --full
python3 cent review proposals --list                      # durable review ledger
python3 cent refute --json                                # D5 Tier-D negatives with witnesses
python3 cent holdout --json                               # D6 frozen retrodictive holdout
python3 cent holdout --write examples/holdout/ledger.json
python3 cent originate --json                              # D8 origination search over declared TIER-3 analogies
python3 cent originate --search scale --json                # D9/D10 declared-data origination at scale
python3 cent review proposals proposal-sqrt-to-glm-reference-via-log-domain-sqrt \
  --state accepted --reviewer alice --note "Handoff reviewed"
python3 cent self --json                          # D4 measured self-transfer ledger
python3 cent-self --revert junction-runtime-invariants --json  # exercised rollback
python3 cent-self --write examples/self/utility.json
python3 cent transfer "sum" --mechanism "kcl-conservation" --validate --json
python3 cent transfer "sum" --mechanism "fluid-continuity" --validate --json
python3 cent transfer "sum" --mechanism "opamp-summing" --validate --json
python3 cent transfer "difference" --mechanism "opamp-summing" --validate --json
python3 cent evaluate --json                     # D1 baseline; uncertified

# Assemble and simulate the exact typed routes
python3 cent assemble delta-sigma --input 1/2 --samples 12
python3 cent assemble sqrt-log --input 2 --precision 20
python3 cent assemble sqrt-feedback --input 2 --precision 64
python3 cent assemble sum-kcl --input 1/2 --input-b 1/3
python3 cent assemble sum-kcl --input 1/2 --input-b 1/3 --operation difference
python3 cent assemble sum-fluid --input 1/2 --input-b 1/3
python3 cent assemble sum-opamp --input 1/2 --input-b 1/3
python3 cent assemble sum-opamp --input 1/2 --input-b 1/3 --operation difference
python3 cent envelope --point 0,1 --point 1,0 --point 0,-1 --point=-1,0
python3 cent envelope --point 0,1 --point 1,0 --point 0,-1 --point=-1,0 --json
python3 cent pipeline sqrt
python3 cent pipeline difference --json
python3 cent pipeline quantized_carry --json

# Chain discovery/compile through proposals, trials, pipeline and a machine wrapper
python3 cent workflow "compute a square root" --out workflow-out
python3 cent workflow --formula "y = 1/x" --json
python3 cent hypothesis                       # list pre-admission leads
python3 cent hypothesis bounding_box         # structural matches, no promotion
python3 cent hypothesis quantized_carry --json
python3 cent hypothesis --resolve nematic-q-tensor-bounding-box  # ask needs, then keep/retire
python3 cent hypothesis --promote bresenham-quantized-carry --mechanism delta-sigma-error-feedback \
  --certificate certificate.json --review promotion-review.json --out promotion-out
python3 cent bind sum-kcl --input 1/2 --input-b 1/3
python3 cent bind sum-kcl --input 1/2 --input-b 1/3 --operation difference --json

# Flatten the declared wheel axioms into one typed graph
python3 cent axioms --json

# Derive a target from any number of wheel inputs over that graph
python3 cent derive W8.energy W8.mass W8.specific_heat_capacity W8.temperature
python3 cent derive W5.power W38.input_torque W38.input_angular_velocity --json
python3 cent derive W5.power W5.force W5.velocity W38.input_torque W38.input_angular_velocity --k 2

# Audit a declared move corpus; no corpus is bundled with the repository
python3 cent moves path/to/move-corpus.json --holdout study

# Exact class-word audit for a declared row-HNF basis and move corpus
python3 cent leech-class --basis path/to/basis.json --corpus path/to/move-corpus.json

# Bind the three physical routes to declared device quantities and an error budget
python3 cent bind delta-sigma
python3 cent bind sqrt-log --input 1/2
python3 cent bind sqrt-feedback --input 2
python3 cent bind sum-kcl --input 1/2 --input-b 1/3

# Select a declared design point under exact accuracy, range, cost and bandwidth constraints
python3 cent solve delta-sigma --accuracy 1/500
python3 cent solve sqrt-log --range 1/2:1
python3 cent solve sqrt-feedback --max-cost 2
python3 cent solve sqrt-feedback --min-bandwidth 100000
python3 cent solve sqrt-feedback --min-bandwidth 100000 --ranking dynamic-aware

# Compare independently solved routes; export JSON or Markdown
python3 cent compare --range 1/2:1
python3 cent compare sqrt-log delta-sigma --json
python3 cent compare --markdown

# Emit a topology-derived reference netlist and schematic stage floorplan
python3 cent physical sqrt-log --range 1/2:1

# Emit declared footprints, stackup, DRC, parasitics and thermal placement
python3 cent fabricate sqrt-log --range 1/2:1

# Run the exact sampled-data RC/clock check for the delta-sigma route
python3 cent dynamics delta-sigma --samples 64
python3 cent dynamics sqrt-log

# Interactive console: enter a £, read ¢ primitives, ∆ ranking and material
python3 cent ui

# One-shot report; --save writes the material bundle, netlist and report
python3 cent report "velocity = (2 * energy / mass)^(1/2)" --save cent_out

# Run the generated exact-core program
python3 cent eval cent_out/velocity.material.json --set energy=8 --set mass=1

# Run the delta-sigma flagship showcase
python3 cent showcase

# Run the current twenty-six-suite gate
python3 tests/run_all.py

# Run the legacy v2.0 seven-simulation suite
python3 cent test

# Emit a SPICE netlist (writes .cir to disk)
python3 cent spice "y = sqrt(5)"

# Enumerate all ∆ for a £
python3 cent enumerate "y = sqrt(5)"
```

---

## System Statistics (v2.0)

| Metric | Value |
|--------|-------|
| Wheels | 39 (loaded from JSON) |
| Axioms | 98 |
| Cases | 153 |
| Derived wheel spokes | 366 two-input formulas |
| ¢ primitives | 16 atomic + 6 composite = 22 |
| ∆ substrate expansions | ~38 |
| TIER 3 transducers | 7 |
| Cross-domain junctions | 57 |
| Escalation layers | 5 (ideal → parasitic → thermal → quantum → fabricated) |
| Knowledge states | 5 (KNOWS / THINKS-TRUE / DOESN'T-KNOW / NEEDS / LANGUAGE) |
| Python modules | 72 |
| Package exports | 62 |
| Tests passing | 1061/1061 across the assembly, discovery, hypothesis-promotion, transfer-contract/mechanism/engine/evaluation/sabotage/ablation/log-domain/self-target/refutation/retrodictive-holdout/origination (D8+D9+D10), proposal/proposal-trial/target, move-corpus/class-word, browser, core, console/knowledge-atlas, device-binding, constrained-design, reference-netlist, declared-fabrication, sampled-data-dynamics, machine-composer, proposal-regression, question-corpus, GLM-application-audit, GLM-direct-question and pressure-settling-packing suites |

---

## Key Results

The detailed evidence summary is in [`docs/RESULTS.md`](docs/RESULTS.md). It
is a reading index, not a second status page; the live gate count remains in
the statistics row above.

---

## Exact core (v2.1) — `CentCalculus2`

The v2.0 compiler above is a floating-point pipeline: it decomposes, enumerates, escalates and emits SPICE. The exact core is a second, independent execution layer in the same package. It has no binary floating point at all.

```bash
# 75 checks over exact arithmetic, enclosures, ports, fields, programs
python3 tests/test_core.py

# machine-readable capability registry (29 atomic + 12 composite)
python3 tools/export_capabilities.py --out capabilities.json
```

| Metric | Value |
|--------|-------|
| Atomic ¢ primitives | 29 across 4 tiers |
| Composite macros | 12 |
| Contracts in the registry | 41 |
| Core verification | 75/75 checks |
| Documentation | `docs/semantics.md`, `docs/extensions.md` |

What the exact core adds:

- **Exact scalars** — every numeric wire is a `fractions.Fraction`; floats are rejected unless converted explicitly (`from_float_exact`), and failures are structured `CentError` codes rather than sentinel values.
- **Certified enclosures** — `√2`, `e`, `log 2` and `π` are bracketed by exact rational endpoints proved by construction (integer square root, Taylor with Lagrange remainder, `atanh` series, Machin's formula).
- **Conservative ports** — effort/flow pairs, power-conserving 0/1 junctions, gyrator, transformer, and dissipation with entropy production.
- **Spatial carriers** — exact central stencils on the 24-D carrier, a 276-component 2-form curl, and Dirichlet/Neumann/Robin boundaries.
- **A transactional tick evaluator** — a single-assignment ¢ program IR with static arity, parameter, kind and cycle checking; state is committed only on success.
- **Layered resolution** — `ideal → parasitic → thermal → quantum → fabricated` with every failure preserved in the trace.

---

## Console and browser UI

Two front ends sit over the same report pipeline. Both take a target relation (£), show the ¢ DAG and primitive census, the ranked ∆ implementations, the SPICE netlist and — when the formula maps exactly — the generated `cent-material/1` program.

```bash
# line console: type a £, read the report
python3 cent ui

# one-shot: report + material files
python3 cent report "velocity = (2 * energy / mass)^(1/2)" --save cent_out

# browser UI on http://127.0.0.1:8000
python3 cent web
```

The browser UI adds buttons for the example queries, an exact runner (set the numeric inputs and tick count), and download links for the material JSON, the SPICE netlist, the text report and a zip bundle. **Design solver** exposes the three declared design spaces: set an exact input, optional range endpoints, accuracy, cost ceiling, bandwidth and ranking profile, then inspect every candidate, the exact Pareto front, the selected design and its verification plan. A **Method comparison** card below solves any chosen subset of the three routes independently under shared requests and downloads JSON or Markdown without inventing a cross-route scalar winner. A solved card can emit its reference netlist and schematic floorplan, with the SPICE deck and physical gaps shown in place, derive declared footprints, stackup, exact lumped parasitics, thermal placement and a DRC report with **Fabricate geometry**, and run **Run dynamic check** for the exact sampled-data result. Bound method cards link directly to their matching design space. Two further tabs expose the substrate: **Wheels** lists all 39 built wheels spanning W1–W41 (W30 and W31 are reserved) with their axioms, derived spokes, cases, dimensions and junctions; **Concept map** searches the 41 exact contracts and draws the exact path and the physical path, marking the first missing simulation, application note or fabrication step. Method cards also show declared typed wheel bridges and their zero-residual port mappings. Wheel search covers ids, titles, axioms, cases and quantities, and every wheel detail includes all two-input formulas the exact algebra derives. Unknown concepts return suggestions rather than invented methods. `--port` and `--host` choose where it listens (localhost by default); `--out DIR` chooses where saved material goes (default `cent_out/web`). `--save`/the “save material” box are the only writes the compile panel makes.

The preview panel is only as live as the Python process. If the cloud workspace has been asleep, that process is gone and the panel returns 404; start it again with:

```bash
python3 cent web --host 0.0.0.0 --port 3000
```

```bash
python3 tests/run_all.py      # canonical twenty-six-suite gate, fails on any suite
python3 tests/test_ui.py      # console, report and material checks
python3 tests/test_webui.py   # HTTP, wheels, concepts, downloads and exact eval
python3 tests/test_discovery.py  # problem-to-method discovery
python3 tests/test_question_corpus.py  # fixed GLM/cent question corpus
python3 tests/test_glm_application_audit.py  # GLM gap and application audit
python3 tests/test_glm_direct_questions.py  # direct Leech/path/XOR/packing/Rule30 audit
python3 cent packing --n 2 --side 3           # exact W36/W37 pressure-settling probe
python3 tests/test_assembly.py   # typed route contracts, graphs, carry and compute routes
python3 tests/test_binding.py    # declared device quantities and error budgets
python3 tests/test_design.py     # constrained design selection and verification plans
python3 tests/test_physical.py   # reference netlists, nets and schematic floorplans
python3 tests/test_fabrication.py  # declared geometry, DRC, parasitics and thermal placement
python3 tests/test_dynamics.py   # exact sampled-data RC/clock checks
```

---

## Package Layout

```
cent_compiler_v12/
├── README.md                    # this file
├── requirements.txt             # numpy for the legacy simulator and its tests
├── DIRECTIVE.md                 # binding objective, rules, work order, scoreboard
├── WORKFLOW.md                  # execution tracker and D1–D7 task board
├── PHYSICAL_COMPILER_ROADMAP.md # completed workstream ledger; blocked-item register
├── docs/                        # documentation index and reference notes
│   ├── README.md                # start here: all documentation links
│   ├── KNOWLEDGE_ATLAS.md       # addressed parts, duplicate detection and stitches
│   ├── RESULTS.md               # detailed evidence summary moved from the README
│   ├── GUIDE.md                 # £ syntax, examples and cross-domain pipeline
│   ├── CONTRIBUTING.md          # where to add wheels, contracts and routes
│   ├── TRANSFER_COMPILER_OBJECTIVE.md # design rationale, contracts and phase history
│   ├── CENT_FRAMEWORK.md        # physical-backend architecture
│   ├── TYPED_GRAPHS.md          # typed route graphs and lowerings
│   ├── MATERIAL_CONTRACTS.md    # 73 declared material contracts
│   ├── WHEEL_MAPPING.md         # graph proofs, declared bridges and text-only gaps
│   ├── ASTRO_COSMO_WHEELS.md    # sourced W26/W27 equations and conventions
│   ├── DELTA_SIGMA_DEMO.md      # benchmark carry route
│   ├── LOG_DOMAIN_SQRT.md       # log-domain compute route
│   ├── OPAMP_MULTIPLIER_SQRT.md # feedback compute route
│   ├── DEVICE_BINDING.md        # declared device quantities and error budgets
│   ├── FLUID_SUM.md             # fluid pipe-junction sum/difference route and audit
│   ├── OPAMP_SUM.md             # ideal op-amp sum/difference route and audit
│   ├── PHYSICAL_NETLIST.md      # reference netlist and floorplan
│   ├── FABRICATION.md           # declared geometry, DRC and parasitics
│   ├── DYNAMICS.md              # sampled-data and nonlinear transients
│   ├── DESIGN_SOLVER.md         # constrained design and verification plans
│   ├── METHOD_COMPARISON.md     # independent route comparison
│   ├── OPERATION_MATRIX.md      # declared operation × method evidence matrix
│   ├── ORIENTATION_ENVELOPE.md  # exact finite-direction envelope method
│   ├── PIPELINES.md             # exact route micro-pipelines and handoffs
│   ├── MACHINES.md              # complete computational machine side-arm
│   ├── HYPOTHESES.md            # pre-admission structural leads and knowledge states
│   ├── DEVELOPMENT_AUDIT.md     # operation coverage and gap ledger
│   ├── REFINEMENT_DIVE.md       # input-review triage, decisions and backlog
│   ├── CURRENT_SCOPE.md # current capability boundary and gap ledger
│   ├── QUESTION_CORPUS.md       # fixed GLM/cent CLI questions and gaps
│   ├── VALIDATION_REPORT.md     # historical validation record
│   ├── MOVE_CORPUS.md           # declared move-corpus audit
│   ├── LEECH_STUDY_AUDIT.md     # study audit
│   ├── LEECH_ISOMORPHISM.md     # move-class isomorphism
│   ├── GLM_LEAN_REVIEW.md       # source-level Lean review
│   ├── GLM_CENT_APPLICATION_AUDIT.md # GLM gaps and scalar cent applications
│   ├── GLM_DIRECT_QUESTIONS_AUDIT.md # direct Leech/path/XOR/packing/Rule30 audit
│   ├── PACKING_PRESSURE_SETTLING.md # W36/W37 pressure-settling packing analogy
│   ├── semantics.md             # exact-core conventions
│   ├── extensions.md            # vocabulary reconciliation and limits
│   └── archive/                 # completed roadmaps and archived design material
│       └── expansion/           # historical expansion blueprints
├── cent                         # CLI tool
├── cent-self                    # D4 self-transfer CLI alias
├── review/                      # D5 console-free working specifications
│   └── refuter_demo.py          # Tier-D refutation demonstration
├── cent_compiler/               # Python package
│   ├── grammar.py               # 22 ¢ primitives + AST decomposer
│   ├── wheels.py                # 39 wheels loaded from JSON
│   ├── substrate_library.py     # ~38 ∆ expansion rules
│   ├── pattern_matcher.py       # 3-pattern clustering
│   ├── cost_function.py         # 6-axis ¢_cost + pruning
│   ├── isomorphism_gate.py      # 3-tier gate + ∆Σ classifier + 7 transducers
│   ├── simulator.py             # 7 verified simulations
│   ├── spice_emitter.py         # SPICE netlist + .cir file output
│   ├── delta_sigma.py           # ∆Σ engine + flagship demonstration
│   ├── pound_suite.py           # 8 £ test cases
│   ├── hypothesis_bridge.py     # Cent Wheel + escalation + conjecture loop + ledger
│   ├── operation_contract.py    # cent-operation/1 schema and validation
│   ├── machine.py               # whole-machine composition and executable first concept
│   ├── mechanisms.py            # cent-mechanism/1 cards; principles plus generated Δ interpretations
│   ├── mapping.py               # executable Τ operators with check/apply
│   ├── transfer.py              # cent-transfer/1 candidates and target profiles
│   ├── transfer_engine.py       # operation contracts, behavior retrieval and candidates
│   ├── transfer_validation.py   # executable target validation and certificates
│   ├── composition_validation.py # chains, typed boundaries and certificates
│   ├── transfer_evaluation.py   # D1 provenance-labelled top-three evaluation
│   ├── proposals.py             # cent-proposal/1 bundles and handoffs
│   ├── proposal_trial.py        # computational trial side-loop for saved proposals
│   ├── knowledge.py             # part addresses, duplicate detection and stitches
│   ├── quantized_carry_floor.py # one-tick floor-carry contract from the Bresenham proof
│   ├── runtime_invariants.py    # exact cent-program/1 junction invariant checks
│   ├── refutation.py            # D5 Tier-D witness search and derived obligations
│   ├── holdout.py               # D6 frozen retrodictive holdout and dated corpus
│   ├── origination.py            # D8 search over declared TIER-3 analogies
│   ├── origination_scale.py       # D9 declared-data search with computed family acceptance
│   ├── self_oracle.py           # independent R5 utility oracle and certificate issuer
│   ├── self_target.py           # D4 cent-utility/1 records, adoption and rollback
│   └── targets/                 # declared target adapters
│       ├── __init__.py          # target package
│       ├── glm.py               # glm-reference adapter and fixed vectors
│       └── glm_live.py          # live external GLM CLI target
├── applications/                # 22 legacy show-work proposals
│   └── README.md                # shared pipeline, parameters and run commands
├── tests/                       # validation tests + wheel generators
├── wheels/                      # 40 JSON files (39 wheels + index) — single source of truth
└── examples/                    # 22 legacy physical .cir proposals, demo output and current ledgers
    ├── transfer/                # current G5b proposal bundles and evaluation.json
    ├── machines/                # whole-machine bundles and the sigma-delta sqrt concept
    ├── self/                    # D4 cent-utility/1 ledger and rollback notes
    ├── refutation/              # D5 Tier-D generated negatives and witness pairs
    ├── holdout/                 # D6 frozen retrodictive holdout ledger
    └── origination/              # D8 origination-search ledger
```

### Exact-core additions

```
cent_compiler/
├── guide.py            # shared £ syntax and cross-domain guidance
├── exact.py            # exact rationals, structured error taxonomy
├── interval.py         # certified sqrt/exp/log/pi enclosures
├── port.py             # conjugate ports, junctions, two-ports
├── density.py          # unit-density channel policies
├── geometry.py         # carrier, fields, stencils, boundaries
├── state.py            # machine state, transactional context, PRNG
├── vocabulary.py       # 29 atomic + 12 composite contracts
├── program.py          # program IR, static checker, feedback analysis
├── evaluator.py        # exact tick evaluator
├── resolution.py       # layered fallback with a preserved failure trace
├── ui.py               # report renderer, material bundles, console shell
├── output_certificate.py # uniform certificate-or-gap block for public outputs
├── parse_diagnostics.py # accepted-symbol parse diagnostics
├── concepts.py         # concept explorer over contracts, evidence and wheels
├── discovery.py        # problem → exact contracts → declared physical routes
├── assembly.py         # typed component contracts + exact route simulation
├── device.py           # declared device quantities, laws and error budgets
├── design.py           # constrained selection over declared design alternatives
├── physical.py         # topology-derived reference netlist and schematic floorplan
├── fabrication.py      # declared footprints, stackup, DRC, parasitics and thermal placement
├── dynamics.py         # exact sampled-data RC/clock model and explicit gaps
├── typed_graph.py      # typed route graphs and component lowerings
├── axiom_graph.py      # flattened global graph of wheel axioms and dimensions
├── move_corpus.py      # declared move-bigram and integer-vector corpus audit
├── leech_class.py      # exact class-word audit for a declared row-HNF basis
├── packing.py          # exact W36/W37 pressure-settling probe
├── envelope.py         # exact finite-direction orientation envelope
├── pipeline.py         # exact route stage/handoff decomposition
├── workflow.py         # discovery/compile → hypotheses → proposal → trial → pipeline/machine
├── promotion.py        # gated hypothesis → mechanism/card → proposal handoff
├── addition_lab.py     # isolated ideal-law lab for alternative adder/subtractor methods
├── port_contracts.py   # declared 0/1-junction port contracts and exact coverage audit
├── hypotheses.py       # pre-admission leads with knowledge states
├── wheel_mapping.py    # declared typed wheel bridges and dimensional residuals
└── webui.py            # stdlib HTTP server for the browser UI

tools/
└── export_capabilities.py

tests/
├── run_all.py         # canonical twenty-six-suite gate
├── test_core.py        # 75 core checks
├── check_docs_consistency.py  # README tree/count preflight
├── test_ui.py          # 29 console UI checks
├── test_webui.py       # 93 browser/API checks
├── test_discovery.py   # 136 method-discovery checks
├── test_workflow.py    # 17 workflow handoff checks
├── test_hypothesis_promotion.py # 14 promotion-gate checks
├── test_transfer_contracts.py # 106 transfer-contract/engine/proposal/review/target checks
├── test_transfer_evaluation.py # 16 D1 retrieval-evaluation checks
├── test_ablation.py          # 11 D2 generated-card and certificate-parity checks
├── test_log_domain.py        # 25 D3 log-domain arithmetic and tolerance checks
├── test_self_target.py       # 21 D4 self-target utility, oracle and rollback checks
├── test_refutation.py        # 19 D5 Tier-D witness and derived-obligation checks
├── test_holdout.py           # 27 D6 retrodictive-holdout checks
├── test_origination.py        # 56 D8+D9+D10 origination checks (analogies, declared-data scale, sign-family unblock)
├── test_evaluation_sabotage.py # 9 constant-score sabotage checks
├── test_moves.py       # 11 move-corpus and class-word checks
├── test_proposals.py   # 8 proposal-pipeline regression checks
├── test_machine.py     # 23 whole-machine composition checks
├── test_question_corpus.py # 16 fixed question-corpus checks
├── test_glm_application_audit.py # 19 GLM application-audit checks
├── test_glm_direct_questions.py # 12 direct-question checks
├── test_assembly.py    # 73 typed-route and graph checks
├── test_binding.py     # 54 declared device-binding checks
├── test_design.py      # 60 constrained-design checks
├── test_physical.py    # 36 reference-netlist checks
├── test_fabrication.py # 53 declared-fabrication checks
├── fixtures/
│   └── glm_cent_questions.json # fixed GLM/cent question corpus
└── test_dynamics.py    # 41 sampled-data checks
```

---

## The Delta-Sigma Benchmark

> Delta-Sigma modulation is the physical process that carries irrational numbers without storing them.

```bash
python3 cent showcase
```

Output: √2 carried as a 100,000-sample bitstream at OSR=64×. Running average converges to 1.414213562373095 (exact). FFT shows 36.9 dB in-band noise suppression vs unshaped quantizer. NTF slope = 28.0 dB/decade (first-order high-pass).

---

## Method discovery

`cent discover` is the first problem-level front end above the relation compiler. `cent matrix` is the operation-first view: it lists declared methods and evidence for each operation without pretending that a structural template or text candidate is an assembled route.

```bash
python3 cent discover "compute an irrational value with an analog method"
python3 cent discover "carry an irrational value as a physical signal" --json
python3 cent discover "compute a square root" --domain mechanical
python3 cent discover "compute a square root, then carry the result as a bitstream"
python3 cent discover "how do I multiply two signals"
python3 cent discover "compute a ratio"
python3 cent discover "exponentiate a signal"
python3 cent discover "compute a reciprocal"
python3 cent discover "sum two signals"
python3 cent discover "compute a minimum-area bounding box for points"
```

It interprets the problem as a behaviour plus an object, finds exact contracts
with that capability, expands their declared `EXPANSIONS`/`DELTA_SUBSTRATE`
materials across domains, and reports typed wheel grounding in three evidence
classes: exact `graph-proof` relations, explicit `declared-bridge` laws, and
non-scoring `text-only` candidates. A text match is never promoted to a proof.
A declared bridge with an explicit law and a zero dimensional residual is
exposed as a typed port/quantity mapping; every other text match stays a gap. It
separates **compute** (for example a square-root circuit) from **carry** (for
example a delta-sigma bitstream), and reports missing physical models instead
of inventing them. Every exact contract has a reviewed capability record and
basis; those tags describe the operation, not a built route. A query with
`then`, `;`, `->` or `→` is parsed into ordered
steps; each step keeps its own behaviour, object, goals and constraints, and the
payload exposes the ordered steps and their returned candidate counts. This is
a grammar and discovery boundary, not composition: no declared handoff maps the
computed result into the carrier, and the missing handoff is reported as a gap.
The binding work order is in [`DIRECTIVE.md`](DIRECTIVE.md); execution state
and the completed D1–D7 record are in [`WORKFLOW.md`](WORKFLOW.md).

`cent axioms` flattens the declared wheel data into a single
`cent-axiom-graph/1` payload: wheel-to-axiom containment, exact axiom relation
exponents, wheel-local quantity nodes, shared exact dimension nodes, declared
junctions and declared non-identities. It reports 39 wheels, 98 axioms, 230
quantities and 65 dimensions. Of 57 declared junctions, 54 become edges; the
other three records (two of them pointing at the absent `W1.charge`) remain
explicit endpoint gaps. Four of nine declared non-identities likewise have no
endpoint node. The graph is a typed projection with declared identities only:
shared names are never merged without a junction, and no missing endpoint is
invented.
`cent derive` consumes that graph without widening the proof claim: it accepts
N wheel-qualified inputs, merges only declared junction identities, limits the
axiom slice to the target/input wheels plus one junction hop, and searches exact
support up to `--max-axioms`. The result names every used axiom and weight, the
junction paths that bridge the requested labels, and a `gap` when no exact
combination exists. It does not search arbitrary cross-wheel paths.

Six exact routes are now assembled across four operation families. Delta-sigma is the **carry** route: typed
`accum`, `quantize` and `delay` contracts, an exact-core program and an exact
bitstream simulation. The log-domain route is an explicit **compute** route:
typed `log`, `scale` and `exp` stages that evaluate `exp((1/2) ln x)` and return
a certified rational enclosure of `sqrt(x)`. The op-amp + analog-multiplier
route is an implicit **compute** route: it solves the finite-gain algebraic
feedback equilibrium `A·(x − k·y²) − y = 0` and independently checks it with
the quadratic formula. The KCL route computes an exact normalized electrical
sum or difference, and the fluid route computes an independent exact normalized
sum or reversed-port difference from the declared pipe-junction continuity row.
The fluid route has no
device binding, physical flow scaling or netlist yet.

The three physical routes also have declared device bindings with exact device-law
checks and static error budgets; the KCL route has a normalized binding only.
A selected physical binding can now emit a reference
netlist and schematic stage floorplan through `cent physical`, and all three
routes can be run over time through `cent dynamics`; neither is a fabrication
netlist. The delta-sigma result is `partial` because the declared
`tau = T_clock` gives a 0.632 first-tick gain, not the static unit increment.
The log-domain route declares `C_j`, `C_out` and a 10 us output pole; its
transient keeps the full Shockley diode law and the half-gain antilog stage.
The feedback route declares a 100 ns small-signal closed-loop pole and a 10 ns
load pole; its nonlinear loop is normalized by the local residual slope so
that declared pole remains meaningful. Both compute routes use exact interval
step-doubling with a declared local budget, a continuous bounded-state
certificate, a monotone large-signal stability certificate, and a certified
local-truncation global bound. The bound is valid but still far above the
declared 1e-3 V target, so that target remains an explicit gap. Measured device models, full dynamic
nonidealities, a manufactured board and manufacturing evidence remain open. See
[`PHYSICAL_NETLIST.md`](docs/PHYSICAL_NETLIST.md) and [`DYNAMICS.md`](docs/DYNAMICS.md).

Wheel grounding now has a typed layer: the log-domain route maps its `x` and
`root` ports through `I_in` and `I_out` to W24 `current`, and maps `V_T` and
`I_s` to W24 `thermal_voltage` and `saturation_current`. The declared diode law
and exact SI dimension vectors are checked, so a mismatch is reported as a gap.
W21, W25 and W29 carry exact graph proofs; W24's log-domain diode law is a
declared bridge, and remaining text-only candidates never score. See
[`WHEEL_MAPPING.md`](docs/WHEEL_MAPPING.md).

## Computational machines (experimental side-arm)

`cent machine` builds a complete function tree for a concept, fills its core stages from the existing transfer rankings, and executes the stages it can actually test. It is a side-arm: it does not change `cent compile` or the transfer scoreboard.

```bash
python3 cent machine list
python3 cent machine sigma-delta-sqrt
python3 cent machine sigma-delta-sqrt --json
python3 cent machine sqrt-log                         # wrap an assembled exact route
python3 cent machine sum-kcl --load mechanical        # declared TIER 3 load branch
python3 cent machine sum-fluid --load fluid
python3 cent machine sigma-delta-sqrt --out examples/machines/sigma-delta-sqrt
```

The first concept is a one-bit delta-sigma √2 carrier: input conditioning, a first-order error-feedback loop, a one-bit quantizer and DAC, digital decimation, and a declared analog reconstruction branch. It reports 12/12 required roles, three compiler-selected core parts and a decimated output error of `4.573e-06`. Its node 1.3 records the input scale `0.700035713374682` and reconstruction factor; the 28.02 dB/dec NTF figure is marked as a finite-window fit, not an asymptotic filter order. The analog branch, clock jitter and supply rejection remain explicit gaps. `machine.cir` is the behavioral electrical core only; it is not a fabrication netlist. The same side-arm wraps any assembled route and accepts a declared `analog`, `mechanical` or `fluid` load from the TIER 3 transducer set; see [`docs/MACHINES.md`](docs/MACHINES.md) and the generated [`machine.md`](examples/machines/sigma-delta-sqrt/machine.md).

## Exact route assembly

`cent assemble` turns a declared route into a checked exact-core program and
runs it on exact rationals. Each route payload carries a structural
`topology_audit` and a typed `¢` graph with explicit ports and lowerings; these
check the declared composition, not physical placement:

```bash
python3 cent assemble delta-sigma --input 1/2 --samples 12
python3 cent assemble sqrt-log --input 2 --precision 20
python3 cent assemble sqrt-log --input 1/2 --precision 24 --json
python3 cent assemble sqrt-feedback --input 2 --precision 64
python3 cent assemble sqrt-feedback --input 2 --precision 64 --json
python3 cent graph sqrt-log --json
python3 cent bind delta-sigma
python3 cent bind sqrt-log --input 1/2
python3 cent bind sqrt-feedback --input 2
```

The delta-sigma route is a first-order loop with a two-level quantizer:

```text
error = x - feedback
integrator = accum(error)
level = clamp(quantize(integrator, quantum), 0, full_scale)
feedback = delay(level, 1)
```

The compute route is a log-domain pipeline with no hidden `sqrt` instruction:

```text
ln_x = log(x)
half_ln = scale(ln_x, 1/2)
root = exp(half_ln)   # certified enclosure of sqrt(x)
```

The feedback compute route is an algebraic loop rather than a program:

```text
residual = A * (x - k * y^2) - y
solve residual = 0 for y > 0 by exact monotone bisection
check the root with the independent quadratic formula
```

It has no hidden `sqrt` instruction. At the default `A = 1,000,000` and
`k = 1`, the finite-gain result at `x = 2` is approximately `1.4142130624`,
which is below the ideal `1.4142135624` by about `5e-7`. That bias is reported
as `finite-gain error`, not corrected by a hidden ideal square root.

The plans record typed ports, laws, parameters, material sources and failure
modes for the physical ingredients. The delta-sigma trace shows the exact
level, error and integrator at every tick. The log-domain result is checked
against an independently constructed `sqrt_q` bracket and must overlap it
within its declared tolerance. The feedback route is checked against its
quadratic equilibrium enclosure, and its finite-gain deviation from the ideal
`sqrt(x/k)` target is bounded explicitly rather than hidden.

`cent bind` maps the three physical routes to declared device quantities: voltages,
currents, resistors, capacitance, clock, temperature, gain and junction
parameters. The delta-sigma binding checks `R_in * C_int * f_clock = 1` exactly;
the log-domain binding checks the squared full-scale relation and evaluates the
diode law independently of the route program; the feedback binding evaluates
`V_fb = k·V_out²/V_ref` and the error-amplifier fixed point independently. Each
reports a conservative static error budget and keeps the netlist, measurement
and dynamic-model gaps explicit. The separate KCL binding preserves both
normalized inputs and audits `a + b` or `a - b`; it declares no physical error
budget or netlist. The physical bindings are reference specifications, not
datasheet values. Standalone notes are in
[`DELTA_SIGMA_DEMO.md`](docs/DELTA_SIGMA_DEMO.md),
[`LOG_DOMAIN_SQRT.md`](docs/LOG_DOMAIN_SQRT.md),
[`OPAMP_MULTIPLIER_SQRT.md`](docs/OPAMP_MULTIPLIER_SQRT.md),
[`DEVICE_BINDING.md`](docs/DEVICE_BINDING.md) and [`DYNAMICS.md`](docs/DYNAMICS.md).

`cent solve` searches a finite, declared design space on top of those bindings.
It can tighten the delta-sigma comparator grade, raise the log-domain enclosure
precision or raise the feedback amplifier gain when the requested accuracy or
range requires it. A candidate that passes its device checks but exceeds the
declared cost ceiling is reported as a gap with the exact cost violation. The result includes an executed verification plan and explicit measurement,
dynamic and fabrication gaps. A solved design points at both `cent physical`,
which emits the reference netlist and schematic stage floorplan, and
`cent dynamics`, which runs the declared sampled-data model. All three dynamic
checks currently return `partial`: delta-sigma exposes the sampled RC/clock
gain mismatch, while the compute routes expose declared reference parasitics
and local-only adaptive error control. See [`DESIGN_SOLVER.md`](docs/DESIGN_SOLVER.md),
[`METHOD_COMPARISON.md`](docs/METHOD_COMPARISON.md),
[`MATERIAL_CONTRACTS.md`](docs/MATERIAL_CONTRACTS.md),
[`TYPED_GRAPHS.md`](docs/TYPED_GRAPHS.md),
[`PHYSICAL_NETLIST.md`](docs/PHYSICAL_NETLIST.md) and [`DYNAMICS.md`](docs/DYNAMICS.md).

---

## Archived expansion blueprints

The pre-v2/v3 design blueprints are retained under
[`docs/archive/expansion/`](docs/archive/expansion/) and are not part of the
active work order:

1. [01_Expanding_Computational_Depth.md](docs/archive/expansion/01_Expanding_Computational_Depth.md) — v2.0 primitives, substrates and transducers; implemented where the live code and docs record it.
2. [02_Expanding_Wheels.md](docs/archive/expansion/02_Expanding_Wheels.md) — v2.0 wheel blueprint; declared wheels are in the live wheel data.
3. [03_Expanding_Beyond.md](docs/archive/expansion/03_Expanding_Beyond.md) — deferred v3 design, not an authorized work item.

The [Hypothesis Engine reference](docs/archive/expansion/hypothesis_engine_README.md)
and its reference tests are archived there. The standalone engine file described
by that note is not part of this package.

---

## License

Open source. Built on the GLM wheel system (github.com/DigitalEuan/GLM).
