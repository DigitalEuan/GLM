# Typed material contracts

`cent_compiler/material_contracts.py` is the typed seam between the compact
material tables and the graph/proof work. It covers all **73** declared rows:

- **38** `DELTA_SUBSTRATE` rows;
- **35** `EXPANSIONS` rows;
- **19** distinct ¢ primitives.

Each row exposes a `cent-material-contract/1` contract through its `.contract`
property. The legacy row fields remain compact indexes for discovery and
backward compatibility; the contract is the graph-facing representation.

## Contract fields

| Field | Meaning |
|---|---|
| `key` | Stable key: `kind:primitive:domain:component` |
| `kind` | `substrate` or `expansion` |
| `primitive` | The ¢ primitive implemented |
| `component` | Declared physical component or expansion name |
| `domain` | Electrical, mechanical, fluidic, optical, thermal, digital, etc. |
| `carrier` | Temporal, spatial, phase-wrap or static |
| `ports` | Typed input/output ports with kind and domain |
| `parameters` | Declared parameters and allowed ranges |
| `law` | Governing law for a substrate; declared behavior for an expansion |
| `operating_range` | Declared model range, not a measured datasheet range |
| `failure_modes` | Declared failure modes; measurement gaps remain gaps |
| `description` | The row's declared description |
| `source` | `DELTA_SUBSTRATE` or `EXPANSIONS` |
| `expands_to` | Expansion subgraph, empty for substrates |
| `delta_sigma` | Whether the expansion carries the declared loop signature |

The interfaces are typed per primitive, so a `log` material has `x` and `y`
ports, a `quantize` material has `signal` and `level`, and a `delay` material
has `x` and `y` with `ticks` and `initial` parameters. Material-specific
domain failures are added without claiming measured values.

## Discovery payload

Every method produced from an expansion or substrate row now carries:

```json
{
  "material_contract": {
    "schema": "cent-material-contract/1",
    "key": "substrate:sum:electrical:kcl-node",
    "kind": "substrate",
    "primitive": "sum",
    "ports": [
      {"name": "a", "direction": "input", "kind": "numeric or interval"},
      {"name": "b", "direction": "input", "kind": "numeric or interval"},
      {"name": "sum", "direction": "output", "kind": "numeric or interval"}
    ],
    "law": "ΣI_in = ΣI_out (Kirchhoff's Current Law)",
    "operating_range": "...",
    "failure_modes": ["..."]
  }
}
```

Contract-level methods that do not come from a material row carry
`"material_contract": null`.

## Provenance and limits

- The contract is derived from the same declared row that discovery already
  exposes; it does not add a new physical claim.
- Ranges and failure modes are declared or explicitly uncharacterised. No
  measured transfer function, tolerance distribution or datasheet value is
  invented.
- Duplicate component names are disambiguated by domain, so `sum`'s mechanical
  and rotational rigid-body rows have distinct keys.
- The compact tables have not been deleted. Replacing their storage with
  contract-first definitions is a separate migration; this layer is the typed
  view that graph and proof work can consume now.

## Tests

```bash
python3 tests/test_discovery.py  # 133/133, including all 73 contracts
python3 tests/run_all.py         # 824/824 across the seventeen-suite gate
```

The discovery suite checks that every substrate and expansion row resolves to
a contract with matching primitive/component/law/domain/carrier, that all keys
are unique, that every contract carries ports, an operating range, failures and
provenance, and that a substrate method exposes its contract in the discovery
payload.
