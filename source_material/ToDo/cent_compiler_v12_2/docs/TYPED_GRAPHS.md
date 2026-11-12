# Typed ¢ graphs

`cent_compiler/typed_graph.py` turns each selected exact route into a
`cent-typed-graph/1` view. The graph is derived from the existing route
program or declared algebraic composition; it is not a second simulator and it
does not add a physical claim.

```bash
python3 cent graph delta-sigma
python3 cent graph sqrt-log --json
python3 cent graph sqrt-feedback --precision 64
python3 cent graph sum-kcl
python3 cent graph sum-kcl --operation difference
```

Route JSON also carries the graph under `route.typed_graph`, so
`cent assemble ... --json` and discovery route payloads expose it without a
separate request.

## Schema

| Field | Meaning |
|---|---|
| `schema` | `cent-typed-graph/1` |
| `route` | Selected route id |
| `nodes` | Primitive nodes with named input/output wires |
| `ports` | Route-level typed ports and their wires |
| `edges` | Producer-to-consumer edges with a `feedback` marker |
| `feedback_edges` | The subset of edges that close a loop |
| `summary` | Node/component/glue/port/feedback counts and loop kind |
| `gaps` | Lowering aliases, exact-core disclaimers and route gaps |

Each node has:

- `id`, `op`, `parameters` and optional physical `role`;
- input and output bindings, each with `port`, `wire`, `kind` and `domain`;
- a `lowering` with `kind` `component` or `exact-core`;
- an explicit contract port map.

## Lowerings

Physical nodes lower to their existing `ComponentContract` under
`cent-component-contract/1`. The contract supplies the declared ports, law,
parameters, operating range, material description and failure modes. The
lowering adds a contract-port-to-wire map and keeps any alias visible. For
example, the delta-sigma quantizer's contract output is named `level` while the
program node produces `raw_level` before the exact saturation guard; the graph
records that alias instead of silently renaming it.

Arithmetic and control glue (`neg`, `sum`, `sat`) lowers to `exact-core` with a
law and port map but no material key. This is deliberate: glue is not counted as
a physical component.

The 73 material contracts from [`MATERIAL_CONTRACTS.md`](MATERIAL_CONTRACTS.md)
are the material-row library. Route components are not one-to-one with those
rows—there is no distinct `amp` material row—so the graph does not fabricate a
material reference for every component. It uses the typed component contract
where that is the honest boundary.

## The three graphs

| Route | Nodes | Component nodes | Exact-core nodes | Loop |
|---|---:|---:|---:|---|
| `delta-sigma-first-order` | 6 | 3 | 3 | stateful, one feedback edge |
| `sqrt-log-domain` | 3 | 3 | 0 | none |
| `sqrt-opamp-multiplier` | 4 | 2 | 2 | algebraic |
| `sum-kcl` | 1 or 2 | 1 | 0 or 1 | none |

- Delta-sigma: `neg`, `sum`, `accum`, `quantize`, `sat`, `delay`; the delay
  output closes the stateful feedback edge.
- Log-domain: `log`, `scale`, `exp`; all three nodes lower directly to
  component contracts, with no hidden `sqrt`.
- Feedback: `neg`, `sum`, `amp`, `mult`; `neg`/`sum` are residual glue and the
  `amp`/`mult` nodes lower to their component contracts. The loop is
  algebraic, not a sampled-data state loop.
- KCL sum: `sum` for addition, or `neg`, `sum` for difference. The KCL junction
  is the declared component; negation is exact-core glue. This route has an
  exact two-input simulation but no device binding or fabrication evidence.

## Global axiom graph and exact derivation

`cent_compiler/axiom_graph.py` projects the declared wheel data into
`cent-axiom-graph/1`; `cent axioms` emits it. The same graph now supports
`cent-derivation/1` through `cent derive`:

```bash
python3 cent derive W8.energy W8.mass W8.specific_heat_capacity W8.temperature
python3 cent derive W5.energy W5.mass W5.velocity --json
python3 cent derive W5.power W38.input_torque W38.input_angular_velocity
python3 cent derive W1.power W1.voltage W15.charge W15.time --strategy substitution
python3 cent derive W9.wavelength W8.energy W8.temperature --json
```

The derivation is exact and deliberately bounded:

- any number of wheel-qualified inputs is accepted;
- declared junction identities are merged transitively, while declared
  non-identities are barriers and unresolved endpoints are errors;
- `strategy="direct"` (the default direct search) takes candidate axioms from
  the target/input wheels plus one declared-junction hop,  not a search over all
  39 wheels;
- `strategy="substitution"` searches backward over the declared axiom scope
  (all wheels unless `--wheel` narrows it), solving one quantity per step from
  already-derived quantities; `strategy="auto"` tries direct first and then
  this bounded substitution search;
- exact support is enumerated from one axiom up to `--max-axioms` (default 4);
- the formula, rational coefficient and input exponents come from the selected
  axiom relation vectors, not from names or keyword matches;
- `used_junctions` contains only the declared paths that bridge an axiom label
  to a requested target/input label.

A successful payload carries `status: derived`, `used_axioms` with exact
rational weights, `used_junctions`, `input_exponents` and `unused_inputs`.
Substitution results additionally carry `strategy: substitution`, ordered
`proof_steps`, `proof_depth` and `intermediate_quantities`; every selected
axiom is rechecked by the exact relation-vector solver. Disconnected
components, a target with no candidate axiom, a support bound that is too
small, and missing/ambiguous quantities return `status: gap` or a
`DerivationLookupError`. The command does not claim exhaustive or arbitrary
cross-wheel search, physical proof or a fabricated device.

## Discovery grounding

`axiom_graph.ground_primitive(op)` applies the same exact solver to a declared
monomial relation query. For `sqrt`, W21/W25/W29 are accepted only when
`derive_from` re-derives each target from its axiom's inputs with support one.
Discovery stores these under `wheel_grounding.candidates` as `graph-proof`.
W24's non-monomial diode law is a separate `declared-bridge`; text matches are
`text_only` and do not contribute to the grounding score. Unsupported
primitives return an explicit graph-grounding gap.

## Limits

- The graph is a typed view of the selected route, not a new physical netlist.
- Component contracts are specifications with declared ranges and failure
  modes; they are not measured device models.
- `exact-core` glue has no material mapping and no fabrication geometry.
- The feedback graph is a four-node algebraic composition; it is not a
  transient model and does not add slew, stability or settling evidence.
- The delta-sigma quantizer alias and the feedback residual composition are
  reported as gaps/loop metadata rather than hidden.

## Tests

```bash
python3 tests/test_assembly.py  # 71/71, including six graph checks
python3 tests/run_all.py        # 824/824 across the seventeen-suite gate
```

The focused checks cover node order, component/glue counts, the stateful and
algebraic loop markers, every node's port map, contract schema selection and the
`cent graph --json` payload.
