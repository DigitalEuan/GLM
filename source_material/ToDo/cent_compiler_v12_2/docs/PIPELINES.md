# Micro-pipelines

`cent pipeline` decomposes a declared exact route into the individual
instructions that actually execute it. A broad operation label such as
`quantized_carry` is not treated as one opaque step: the command exposes the
arithmetic, accumulation, quantization, saturation and delay stages, plus every
named-wire handoff between them.

The source of truth is `route.program.instructions`, not a hand-written stage
list. If a route constructor changes, the pipeline changes with it.

## Commands

```bash
python3 cent pipeline sqrt
python3 cent pipeline difference --json
python3 cent pipeline sum --mechanism fluid-continuity
python3 cent pipeline quantized_carry --json
```

The text view prints each stage's operation, inputs, output and law, then lists
all handoffs and gaps. `--json` emits the full `cent-pipeline/1` payload with an
output certificate.

## Declared operations

| Pipeline | Route | Default mechanism |
|---|---|---|
| `sqrt` | `sqrt-log-domain` | `log-domain-sqrt` |
| `sum` | `sum-kcl`, `sum-fluid` or `sum-opamp` | `kcl-conservation`; use `--mechanism fluid-continuity` or `opamp-summing` for the other routes |
| `difference` | `sum-kcl`, `sum-fluid` or `sum-opamp` | `kcl-conservation`; use `--mechanism fluid-continuity` or `opamp-summing` for the other routes |
| `quantized_carry` | `delta-sigma-first-order` | `delta-sigma-error-feedback` |

## Stages

Each stage is derived from one `Instruction`:

| Field | Source |
|---|---|
| `index` | instruction position in the route program |
| `op` | instruction operation |
| `inputs` / `output` | named wires |
| `parameters` | exact instruction parameters |
| `law`, `domain`, `carrier`, `material`, `source` | the matching typed route component contract |
| `role` | the route component role; `exact-core` for declared glue |

The delta-sigma program has three glue operations (`neg`, `sum`, `sat`) without
separate typed route components. Their exact program laws are declared in
`pipeline.py` and their domain/carrier values are inherited from the route's
first typed component. No device or physical parameter is invented.

## Handoffs

Every input wire becomes an edge:

- `route-input` — supplied by the route's declared input;
- `stage` — produced by an earlier stage;
- `feedback` — produced by a later stage and fed back to an earlier one.

For `quantized_carry`, the delay output `feedback` is produced by stage 6 and
consumed by stage 1. The edge is labelled `feedback`; it is not hidden inside a
single “delta-sigma” node.

Example:

```text
sqrt             quantized_carry
0 -> 1 x         6 -> 1 feedback   [feedback]
1 -> 2 ln_x      0 -> 2 x          [route-input]
2 -> 3 half_ln   1 -> 2 neg_feedback [stage]
                 2 -> 3 error      [stage]
                 3 -> 4 integrator [stage]
                 4 -> 5 raw_level  [stage]
                 5 -> 6 level      [stage]
```

## Contract

- Schema: `cent-pipeline/1`
- Input: a declared operation and optional mechanism
- Output: stages, handoffs, route inputs/outputs, checks, summary and gaps
- `passed` is true only when the program has stages and every input wire
  resolves to a route input, an earlier stage or a feedback edge
- The payload carries `cent-output-certificate/1`

## Limits

- This is a structural decomposition of an already-declared route, not a new
  execution engine or a target adapter.
- It does not compose two independently discovered methods or invent a handoff
  between them.
- It does not add device nonidealities, fabrication geometry or measured
  evidence.
- The stage count is not a cost, latency or area estimate.

The point is to make the internal steps workable: each stage has an operation,
typed wire contract and law, so a later tool can address, replace or validate
one step without treating the whole operation as a single black box.

## Tests

```bash
python3 tests/test_discovery.py  # 133/133, including pipeline stages, feedback and CLI
python3 tests/run_all.py         # 824/824 across the seventeen-suite gate
```
