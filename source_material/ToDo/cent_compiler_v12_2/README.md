# cent_compiler v2.0 — The £ → ¢ → ∆ Transfer Compiler

> **Objective reset (2026-11-11).** The primary objective is cross-domain computational method transfer, not selection among pre-declared physical routes. A mechanism from one domain — for example, error-feedback noise shaping from audio delta-sigma — must be retrievable, mapped into a target context, and validated there. The full objective, contracts and phased plan are in [`docs/TRANSFER_COMPILER_OBJECTIVE.md`](docs/TRANSFER_COMPILER_OBJECTIVE.md).

The target system takes a computational operation contract, finds mechanisms across physical and information domains that can realize it, constructs an explicit transfer mapping, and validates a target artifact. The existing £ → ¢ → ∆ and SPICE path remains the **physical backend**: it is used when the target is a physical realization, not as the definition of the compiler. The current capability boundary, loose ends and post-G5b development track are in [`docs/CURRENT_SCOPE_AND_NEXT_TRACK.md`](docs/CURRENT_SCOPE_AND_NEXT_TRACK.md).

For that physical backend, the five-layer trace is now part of `cent compile`. Electrical candidates run the existing reference cascade; mechanical, fluidic, thermal, optical and digital candidates keep all five layer slots but report explicit “no declared layer model” gaps. The trace is a screening record, not a device simulation or a measured result.

**Delta-sigma is one benchmark mechanism, not the objective** — an error-feedback/noise-shaping loop from audio electronics that can be transferred into quantized information representation. The compiler must find and validate such transfers, not merely label delta-sigma as a carrier.

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
```

Use `cent compile "<£>" --json` for the same result as a tooling payload. The
JSON proposals include each rank's domain, carrier, components and six-axis
cost breakdown. `--top N` is a ranking view, not a domain quota: a non-electrical
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
python3 cent review proposals --list                      # durable review ledger
python3 cent review proposals proposal-sqrt-to-glm-reference-via-log-domain-sqrt \
  --state accepted --reviewer alice --note "Handoff reviewed"
python3 cent transfer "sum" --mechanism "kcl-conservation" --validate --json
python3 cent transfer "sum" --mechanism "fluid-continuity" --validate --json
python3 cent transfer "sum" --mechanism "opamp-summing" --validate --json
python3 cent transfer "difference" --mechanism "opamp-summing" --validate --json
python3 cent evaluate --json                     # G5b retrieval metrics

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
python3 cent hypothesis                       # list pre-admission leads
python3 cent hypothesis bounding_box         # structural matches, no promotion
python3 cent hypothesis quantized_carry --json
python3 cent hypothesis --resolve nematic-q-tensor-bounding-box  # ask needs, then keep/retire
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

# Run the current seventeen-suite gate (824 checks)
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
| Python modules | 57 |
| Package exports | 62 |
| Tests passing | 824/824 across the assembly, discovery, transfer-contract/mechanism/engine/evaluation/proposal/target, move-corpus/class-word, browser, core, console, device-binding, constrained-design, reference-netlist, declared-fabrication, sampled-data-dynamics, proposal-regression, question-corpus, GLM-application-audit, GLM-direct-question and pressure-settling-packing suites |

---

## Key Results

- **39 wheels** loaded from JSON (single source of truth in `wheels/` folder), with **366 derived two-input spokes**
- **4 transducer wheels added**: gears/transmissions, magnetic circuits, piezoelectric transducers, thermoelectric transducers
- **Astrophysics and cosmology coverage**: W26 declares four sourced stellar/compact-object relations (blackbody luminosity, Schwarzschild radius, circular orbital speed and Hawking temperature); W27 declares four sourced expansion relations (Hubble law, critical density, Hubble time and Hubble horizon). Ten reviewed junctions connect them to the thermal, power, motion, density, gravity and EM wheels. W26's multi-input laws produce no two-input spoke; W27 contributes 30
- **22 ¢ primitives** (v1.0's 12 + v2.0's 10 new: exp, log, sat, hysteresis, grad, div_spatial, curl, delay, translinear, state_space)
- **22 legacy physical show-work proposals** with full 8-step pipeline trace (7 original + 3 v2.0 primitives + 12 expanded wheels)
- **22 legacy physical .cir files** written to disk (one per proposal, 9 SPICE templates); current transfer proposal bundles are under `examples/transfer/`
- **7 TIER 3 transducers** (Paynter, rotational-linear, C-L duality, electromechanical, thermoelectric, optoelectronic, electro-hydrodynamic)
- **Delta-sigma flagship**: √2 carried as bitstream, 36.9 dB noise suppression, NTF slope 28.0 dB/dec
- **Nine exact typed route modes across four operation families**: delta-sigma carries a value; the log-domain route computes a certified rational enclosure of √x; the op-amp + multiplier route solves a finite-gain algebraic feedback equilibrium; the KCL route computes an exact normalized sum or difference from two inputs; the fluid route computes an independent exact normalized sum or reversed-port difference at a declared pipe junction; the op-amp route computes an exact normalized sum or inverting-buffer difference from a matched summing amplifier
- **Three physical device bindings plus normalized KCL, fluid and op-amp sum/difference routes**: an exact RC/clock design for delta-sigma, a diode log/antilog reference design for √x, and an op-amp + multiplier feedback design with an independent loop-closure check, each with a conservative static error budget and an independent exact audit of derived quantities; the KCL binding preserves two exact inputs and audits the normalized sum or difference without claiming physical units; the fluid route declares normalized flow conservation but no device binding or netlist; the op-amp route declares an ideal matched-resistor summing block but no device values or reference netlist
- **Structural route audits**: every assembled route carries a `topology_audit` that checks unique component roles, contract port arity, declared parameters and exact-program wire coverage; malformed or unsupported compositions return an explicit `gap`
- **Typed wheel bridge**: the log-domain route’s ports map to W24 semiconductor quantities through a declared diode law, with an exact zero dimensional residual; unmatched text candidates remain explicit gaps
- **Method status and wheel navigation**: discovery carries each contract’s capability status and display label, method cards render it, and wheel-candidate pills open the selected wheel in the wheel browser; every vocabulary primitive is checked for contract, capability, dispatch and wire-kind coverage
- **Reviewed capability index**: all 41 exact contracts have capability tags and a provenance basis; canonical contract names and reviewed aliases are discoverable, and the tags describe exact operation semantics rather than claiming a physical route
- **Ordered multi-step goals**: `cent discover` splits sequencing words and punctuation into ordered `GoalStep` records, matches each step independently, exposes per-step candidate counts, and keeps the missing step-to-step handoff explicit instead of claiming a composed `¢` graph
- **Operation × method matrix**: `cent matrix` reports the declared operation-first catalogue without inventing methods. Every row names one evidence class — exact route, exact algorithm, structural template, declared bridge, inherited wheel candidate or gap — plus its role, domain, carrier, route and first missing physical model. Compute, carry and grounding rows are separate, so delta-sigma remains a carrier rather than an operation algorithm. The envelope appears as the matrix's `exact-algorithm` row, not as a physical route
- **Ten-operation transfer corpus**: `cent transfer` now declares ten operation contracts; `mult`, `div`, `exp`, `log`, `reciprocal` and `sign` join the original four. Each new contract names an exact or certified reference and a fixed test. None has a production mechanism or target adapter, so retrieval returns zero candidates with an explicit adapter gap instead of a fabricated match. This is G5a corpus intake, not a recall claim.
- **Declared retrieval evaluation**: `cent evaluate` measures the ten-operation corpus against four known-valid cases (10 expected mechanism candidates), five negative controls, six zero-mechanism operations and three refused names. The declared result is 10/10 candidate recall, 4/4 case recall, 0/5 negative-control false positives, 8/8 reference target pairs, 8 artifacts, 2 supported-but-unadapted candidates with recorded T1 refusal conditions and 10/10 retrieval plus 8/8 target evidence completeness. Known-valid means declared card support, not independent external ground truth; the six zero-mechanism operations are valid contracts with no declared transfer, and no live or measured target is claimed.
- **Exact orientation envelopes**: `cent envelope` computes minimum-area bounding rectangles over a declared finite set of rational directions, with exact projections, exact corners and an explicit finite-direction/global-optimum gap. `cent discover "compute a minimum-area bounding box for points"` resolves it as the declared `Orientation Envelope — finite-direction minimax` method, and `cent matrix --operation bounding_box` carries that evidence. The method is purely computational; an orientation or liquid-crystal analogy is optional interpretation, not a validation requirement
- **Micro-pipeline decomposition**: `cent pipeline` derives every stage and named-wire handoff from an assembled route's actual `cent-program/1` instructions. `sqrt` becomes `log → scale → exp`, `difference` becomes `neg → sum`, and `quantized_carry` becomes `neg → sum → accum → quantize → sat → delay`, with the delay-to-neg feedback edge labelled instead of hidden. Stage laws come from typed route contracts, or explicit exact-program glue laws where the route has no separate component contract
- **Pre-admission hypotheses**: `cent hypothesis` is a separate discovery surface for structural matches that are not yet mechanism cards. It reuses the `CentWheel` knowledge states, requires a declared primitive-chain overlap and score for card matches, and carries review leads such as a nematic Q-tensor for `bounding_box` and Bresenham for `quantized_carry`. The 2026-11-11 audit proves that scalar Q-tensor invariants are orientation-blind, so the Q-tensor lead is retired; it finds an exact one-tick Bresenham/delta-sigma correspondence, so Bresenham is retained only as that narrowed variant, not as an equivalence claim about the existing two-tick target. Their pre-admission wheel state remains `DOESN'T-KNOW` as provenance, and neither lead is deleted. Current records are in `docs/hypothesis-resolutions/`; the earlier absence-based records are under `history/`. No mechanism's `supported_operations`, transfer candidate or matrix row changes automatically. The resolver turns each need into a question, retries until all needs are answered, and records keep or retire; retirement requires a reason, and neither decision promotes the lead
- **Operation-level discovery queries**: `cent discover` resolves reviewed verbs and nouns such as multiply/product/times, divide/quotient/ratio, exponentiate/antilog, logarithm/ln and add/sum to their declared contracts. Queries are scoped to that contract, and the returned methods do not gain route or template status merely because the query is operation-first
- **Constrained design solver**: searches 4 declared delta-sigma grades, 4 log-domain precisions and 3 feedback gains, rejects over-budget, over-accuracy or under-bandwidth candidates with exact reasons, and emits a verification plan with measurement and dynamic gaps explicit; the same solver powers the browser Design tab and is linked from bound method cards
- **Declared-pole bandwidth**: `--min-bandwidth` checks every declared small-signal pole at each probe with a certified rational enclosure of π; it accepts only a certified lower bound, rejects only a certified upper-bound miss, and reports the narrow undecided interval as an explicit gap
- **Reference physical emission**: `cent physical` turns the selected binding into three topology-derived part lists, connected nets, SPICE-shaped reference decks and non-overlapping schematic stage floorplans; exact rationals remain in JSON, and every fabrication claim stays an explicit gap
- **Advisory post-solve fabrication audit**: every solved `cent-design/1` result carries a `cent-fabrication-audit/1` block with the existing exact DRC, thermal and parasitic checks, failed-check names, unrouted nets and gaps. It is explicitly advisory: it does not change candidate selection and is not a fabrication sign-off
- **Declared fabrication geometry**: `cent fabricate` derives generic footprints, a four-layer stackup, an orthogonal escape/bus route, exact lumped R/C/L parasitics, a single-node junction thermal model and an independent DRC from that reference topology; every check carries exact compared values, single-pin behavioral control labels are declared unrouted rather than invented, and prototyping, DFM and measured-device limits stay explicit
- **Exact Pareto design ranking**: the solver applies the hard constraints first, then sorts the feasible candidates into exact Pareto layers over cost and worst-probe error; a bandwidth request switches to a `dynamic-aware` profile that adds only the certified slowest-pole lower bound, never an invented noise term. Selection is the cheapest front point with an exact tie-break, and every payload carries the profile, front, layers, ranks and dominators
- **Cross-route method comparison**: `cent compare` solves any chosen subset of the declared routes independently under shared requests, keeps each route's exact Pareto rank, and exports JSON or Markdown. A blank input leaves each route on its declared default; costs remain declared complexity units, and no cross-route scalar winner or measured preference is invented
- **Typed material contracts**: every one of the 73 declared `EXPANSIONS`/`DELTA_SUBSTRATE` rows resolves through a `cent-material-contract/1` view with typed ports, parameters, law/behavior, operating range, failure modes and provenance; discovery carries the contract, giving graph and proof layers typed material nodes without inventing measured ranges
- **Typed route graphs and lowerings**: all three selected routes expand into `cent-typed-graph/1` nodes with named wires, typed ports, exact-core glue and `cent-component-contract/1` lowerings. Delta-sigma has six nodes and a stateful feedback edge; log-domain has three component nodes; the feedback route has four nodes and an explicitly labeled algebraic loop. `cent graph` emits the same graph, and route JSON carries it automatically
- **Global axiom graph and exact derivation**: `cent axioms` projects all 39 wheels, 98 axioms, 230 wheel-local quantity nodes and 65 exact dimension nodes into `cent-axiom-graph/1`. Wheel membership, exact axiom exponents, quantities, dimensions, 54/57 declared junctions and 5/9 declared non-identities are explicit graph edges. Shared names stay wheel-local unless a junction declares identity; seven endpoint records that do not resolve to a quantity node remain gaps, never invented edges. `cent derive` accepts any number of wheel-qualified inputs over a bounded target/input plus one-junction-hop slice, enumerates exact sparse support, and returns the formula, exact coefficient and exponents, used axioms with rational weights, only the junction paths that actually bridge labels, and an explicit `gap` when the target and inputs are disconnected or the support bound is exhausted. `--strategy substitution` adds a bounded backward-substitution search over the requested wheel scope and records each exact substitution step; `auto` keeps the direct path first and falls back to substitutions. `ground_primitive` now calls that proof layer for discovery: graph-derived wheel relations are `graph-proof`, W24's diode law remains a separate `declared-bridge`, and keyword matches are retained only as non-scoring `text_only` candidates
- **k-best exact derivations**: `cent derive --k N` returns up to eight distinct exact paths in the bounded target/input plus one-junction-hop scope, with proof steps, assumptions and structured missing-bridge reports. A W5/W38 example returns both the W38 torque × angular-velocity path through the declared junction and the W5 force × velocity alternative. `cent derive --strategy substitution` additionally returns a bounded cross-wheel substitution path with exact per-step equations and dependencies.
- **Structural SPICE template selection**: the console, CLI and emitter share one declared matcher. A template is chosen only when the complete ¢ operation set fits its required operations and allowed envelope; a DAG that merely contains `sqrt` or `mult` no longer inherits a template by first-op priority. Unmatched or ambiguous sets return an explicit gap with the present operations, and no netlist is invented. The bundle records the template status and detail alongside the netlist
- **Uniform output certificates**: every public compiler JSON payload and saved `cent-material/1` bundle carries `cent-output-certificate/1`. The certificate summarizes only the payload's declared exact/structural checks and gaps; it is `certified` only when every listed check passes and no gap remains, otherwise `partial` or `gap`. CLI envelopes and browser responses inherit the certificate, including assemble, graph, axioms, derive, solve, compare, physical, fabricate and dynamics outputs
- **Executable target certificates, reference and live**: `cent transfer "quantized_carry" --validate`, `cent transfer "sqrt" --validate`, `cent transfer "sum" --mechanism "kcl-conservation" --validate`, `cent transfer "sum" --mechanism "fluid-continuity" --validate`, `cent transfer "difference" --mechanism "kcl-conservation" --validate` and `cent transfer "difference" --mechanism "fluid-continuity" --validate` run eight pure-Python exact-rational reference adapters over twenty-four fixed vectors. The delta-sigma adapter reproduces source code and mean, checks bounded state and a plain uniform-quantizer baseline; the log-domain sqrt adapter checks its certified `exp((1/2) log x)` enclosure against the source route and an independent `sqrt_q` baseline; the KCL sum and difference adapters check exact source parity and commutativity/anti-commutativity; the normalized fluid-continuity sum and reversed-port difference adapters check exact source parity, commutativity/antisymmetry and the declared flow-conservation domain; the op-amp sum and difference adapters check the matched summing block and inverting-buffer route. All emit `cent-transfer-certificate/1` and declare reference-operation latency and bit budgets; these reference certificates are `target-simulated`. A separate `glm-live` target executes the real external `GLM.py` CLI (or `GLM_CLI`) for exact KCL sum and difference, parses its exact witness, and reports `target-integrated`. It covers only those two operations and makes no latency, bit-budget, model or performance claim. The T3 breadth decision and its reproducible CLI probe are in [`docs/evidence/live-glm-breadth/README.md`](docs/evidence/live-glm-breadth/README.md).
- **Explicit relaxation records**: every `cent-transfer/1` candidate carries a `cent-relaxation/1` record with `exact`, `asymptotic`, `parameter-dependent` or `unclassified`, a basis and an evidence level. Retrieval defaults to `unclassified`; target-validated exact KCL, fluid-continuity and op-amp sum/difference routes are recorded `exact`, while delta-sigma and sqrt stay unclassified. A non-`unclassified` class requires a matching target, target-level evidence, an artifact and at least one target test.
- **Reviewable cross-domain proposals**: `cent propose "sqrt" --target glm-reference --json` turns ranked analogies into `cent-proposal/1` records with operation, mechanism, mapping, source tests, target adapter, readiness and a handoff command. `--out DIR` writes one JSON per proposal plus `index.json` and `index.md`, and every proposal starts with an `unreviewed` review block. `cent review DIR ID --state accepted|rejected|tested --reviewer ... --note ...` appends to `reviews.json` and updates the proposal/index review state without changing `status: unvalidated`. A `tested` review requires a passing `cent-transfer-certificate/1`, copied into `evidence/` with its SHA-256; `--list` renders the audit trail. `ready-for-execution` names the exact `cent transfer ... --validate` command; missing adapters remain `needs-target-adapter`. No proposal claims an isomorphism or a validation.
- **366-spoke graph regression**: `axiom_graph.regress_legacy_spokes()` re-derives all 366 legacy two-input formulas over the global axiom graph with exact formula matching. Forty-eight entries carry an extra input the formula never uses; those are reported explicitly, while the graph continues to reject disconnected inputs.
- **153-case corpus reconciliation**: `wheels.regress_declared_cases()` re-runs every declared formula case after the JSON/global-graph migration. The corrected dimensions and axioms now give 153/153 dimensional agreement and 153/153 derivability agreement with no mismatches: W21 uses the squared fracture-toughness law, W22/W24 have the missing dimension rows, W29 uses the exact spin-diffusion law, W32 declares its wetting-coefficient dimension, W34 uses hydraulic resistance T^-1, and W37's quotient/product cases match its axioms. W25/W35 remain explicit non-SI model conventions, not silently relabelled.
- **Declared move-corpus audit**: `cent moves` reads a `cent-move-corpus/1` document and reports exact in-sample bigram top-1 with a deterministic lexical tie-break, plus optional exact integer-vector return/displacement statistics. It labels the missing held-out split and does not claim a Leech heat kernel, a Griess product, a Lean certificate or a codebook optimizer. The compiler audit was also run against the separate `DigitalEuan/Leech-lattice` study's reconstructed 442-file corpus: 80,361 moves and 1,487,183 occurrences. The study-protocol leave-one-file-out score is 681,926/1,486,741 = 45.8672%, reproducing the reported 45.8%; a strict file holdout gives 46.3422%. The move classes admit an explicit group isomorphism to `F₂²⁴`: 63,257 distinct bit words, rank 24, XOR composition. `cent leech-class` now re-derives that result compiler-side from a declared row-HNF basis: 80,361 moves, 63,257 class words, rank 24, one zero-class move and 5,000/5,000 sampled XOR compositions. See [MOVE_CORPUS.md](docs/MOVE_CORPUS.md), [LEECH_STUDY_AUDIT.md](docs/LEECH_STUDY_AUDIT.md) and [LEECH_ISOMORPHISM.md](docs/LEECH_ISOMORPHISM.md)
- **GLM-aligned class-word audit**: `cent leech-class` uses only the standard library and exact integer arithmetic, with no float, NumPy or GLM import. It accepts a declared row-HNF basis and a `cent-move-corpus/1` document, and emits `cent-leech-class/1` with sampled XOR-composition evidence. It is a class index only; the lattice metric/q-form, Griess product and Monster action remain explicit gaps
- **Graph-coverage and GLM Lean audit**: the study's lattice graph covers all 20,458 structural token parts, with 105,282 exact joinings, one connected component and no isolated structural nodes. Its 19,534 codebook remainder is 10,421 bigrams, 8,935 comments, 63 frames, 86 tactics and 29 whitespace parts; all bigrams already encode an existing token edge, so adding them as nodes adds no structural transition. A source-level review of the adjacent 434-file GLM Lean tree found `CentWheels`, `Derivability` and `ConnectedMachine` directly relevant to the wheel/derivation layer, while `Shortcut/Leech` and the Golay files belong to the Leech bridge; no Lean build was run. See [LEECH_STUDY_AUDIT.md](docs/LEECH_STUDY_AUDIT.md) and [GLM_LEAN_REVIEW.md](docs/GLM_LEAN_REVIEW.md)
- **Sampled-data and nonlinear dynamics**: `cent dynamics` runs the delta-sigma RC/clock loop as an exact 64-tick trace; the first step gain is `1 − e⁻¹ = 0.6321`, not the static `1`, so the result is `partial` rather than hidden. Delta-sigma also runs a continuous-time four-substep clocked-comparator/RC transient, and the three physical routes expose a `nonlinear_transient` coverage block. The log-domain route integrates a two-node nonlinear diode/load transient, and the feedback route a slope-normalized quadratic closed-loop transient; both use adaptive step doubling with an exact local budget, carry passing continuous bounded-state and monotone-stability certificates, expose the too-small-box failure through `--certificate-box` and the dynamics API, and separately report a certified local-truncation global bound that still exceeds the 1e-3 V target
- **Hypothesis bridge**: Cent Wheel knowledge state management, 5-layer escalation, conjecture loop, parametric ledger
- **6 of 7** original application proposals pass validation (1 honestly classified as DIMENSIONAL CHECK)
- **22 of 22** show-work proposals pass the full pipeline (decompose → enumerate → escalate → emit .cir); the canonical proposal regression regenerates all 22 netlists and preserves the separate **6/7** original comparison
- **Fixed GLM/cent question corpus**: 13 stable CLI questions with pinned JSON fields, exact arithmetic results, two refusals and explicit gaps. `tests/test_question_corpus.py` runs 16 canonical checks; this is evidence/reproducibility coverage, not a benchmark or GLM score. See [QUESTION_CORPUS.md](docs/QUESTION_CORPUS.md)
- **GLM application audit**: eight sourced GLM gaps, six scalar application probes through the exact core, one exact KCL residual route, five explicit gaps and two recorded discovery false matches. `tests/test_glm_application_audit.py` runs 19 checks, including the GLM-facing computational addition evidence; it does not run a GLM or claim physical implementation. See [GLM_CENT_APPLICATION_AUDIT.md](docs/GLM_CENT_APPLICATION_AUDIT.md)
- **Direct GLM question audit**: the packing query now proposes the **Pressure Settling Engine** from W36/W37: a squared penetration/wall-energy objective plus a viscous relaxation step. The method scans all 39 wheel documents, selects W36/W37, and keeps adjacent pressure/elasticity candidates unpromoted. The exact fixed-container probe resolves overlap but sets `optimal=false` and keeps the global optimality gap explicit. The other four direct queries — Leech tie resolution, efficient lattice-path travel, 24D XOR and Rule 30 — remain gaps or narrow utilities. `tests/test_glm_direct_questions.py` runs 12 checks. See [GLM_DIRECT_QUESTIONS_AUDIT.md](docs/GLM_DIRECT_QUESTIONS_AUDIT.md) and [PACKING_PRESSURE_SETTLING.md](docs/PACKING_PRESSURE_SETTLING.md)
- **7 of 7** core simulations pass

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
python3 tests/run_all.py      # canonical seventeen-suite gate, 824 checks, fails on any suite
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
├── PHYSICAL_COMPILER_ROADMAP.md # forward-looking workstreams
├── docs/                        # documentation index and reference notes
│   ├── README.md                # start here: all documentation links
│   ├── GUIDE.md                 # £ syntax, examples and cross-domain pipeline
│   ├── CONTRIBUTING.md          # where to add wheels, contracts and routes
│   ├── TRANSFER_COMPILER_OBJECTIVE.md # transfer objective, contracts and action plan
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
│   ├── HYPOTHESES.md            # pre-admission structural leads and knowledge states
│   ├── DEVELOPMENT_AUDIT.md     # operation coverage and next gaps
│   ├── REFINEMENT_DIVE.md       # input-review triage, decisions and backlog
│   ├── CURRENT_SCOPE_AND_NEXT_TRACK.md # current abilities, loose ends and next track
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
│   └── archive/                 # completed and product-complete roadmap archives
├── cent                         # CLI tool
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
│   ├── mechanisms.py            # cent-mechanism/1 mechanism cards
│   ├── transfer.py              # cent-transfer/1 candidates and target profiles
│   ├── transfer_engine.py       # operation contracts, behavior retrieval and candidates
│   ├── transfer_validation.py   # executable target validation and certificates
│   ├── transfer_evaluation.py   # G5b retrieval evaluation corpus and metrics
│   ├── proposals.py             # cent-proposal/1 bundles and handoffs
│   └── targets/                 # declared target adapters
│       ├── __init__.py          # target package
│       ├── glm.py               # glm-reference adapter and fixed vectors
│       └── glm_live.py          # live external GLM CLI target
├── applications/                # 7 application proposals
├── expansion/                   # roadmap + Hypothesis Engine reference
├── tests/                       # validation tests + wheel generators
├── wheels/                      # 40 JSON files (39 wheels + index) — single source of truth
└── examples/                    # 22 legacy physical .cir proposals, demo output and current transfer bundles
    └── transfer/                # current G5b proposal bundles and evaluation.json
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
├── addition_lab.py     # isolated ideal-law lab for alternative adder/subtractor methods
├── port_contracts.py   # declared 0/1-junction port contracts and exact coverage audit
├── hypotheses.py       # pre-admission leads with knowledge states
├── wheel_mapping.py    # declared typed wheel bridges and dimensional residuals
└── webui.py            # stdlib HTTP server for the browser UI

tools/
└── export_capabilities.py

tests/
├── run_all.py         # canonical seventeen-suite gate
├── test_core.py        # 75 core checks
├── check_docs_consistency.py  # README tree/count preflight
├── test_ui.py          # 24 console UI checks
├── test_webui.py       # 93 browser/API checks
├── test_discovery.py   # 133 method-discovery checks
├── test_transfer_contracts.py # 93 transfer-contract/engine/proposal/review/target checks
├── test_transfer_evaluation.py # 14 retrieval-evaluation checks
├── test_moves.py       # 11 move-corpus and class-word checks
├── test_proposals.py   # 8 proposal-pipeline regression checks
├── test_question_corpus.py # 16 fixed question-corpus checks
├── test_glm_application_audit.py # 19 GLM application-audit checks
├── test_glm_direct_questions.py # 12 direct-question checks
├── test_assembly.py    # 71 typed-route and graph checks
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
The ordered build plan is in
[`PHYSICAL_COMPILER_ROADMAP.md`](PHYSICAL_COMPILER_ROADMAP.md).

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

## Expansion Roadmap

The `expansion/` folder contains three roadmap documents:

1. **01_Expanding_Computational_Depth.md** — new ¢ primitives, ∆ substrates, TIER 3 transducers (IMPLEMENTED in v2.0)
2. **02_Expanding_Wheels.md** — W20-W35 new domain wheels (IMPLEMENTED in v2.0)
3. **03_Expanding_Beyond.md** — 10-axis cost engine, multi-format output, native solver integration, algorithmic £ synthesis (deferred to v3)

Plus Hypothesis Engine reference files for the knowledge state management architecture.

---

## License

Open source. Built on the GLM wheel system (github.com/DigitalEuan/GLM).
