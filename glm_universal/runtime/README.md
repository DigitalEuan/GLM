# `glm_universal/runtime` — the interactive geometric language runtime

**Parent:** `../README.md`

Three modules turn the substrate, the carriers and the reasoning kernel
into something a person can hold a conversation with:

```
runtime/
├── parser.py      deterministic semantic query parser (13 query kinds)
├── session.py     GeometricSession: 13 solvers, registers, history
├── tct_engine.py  Three Column Thinking trace generation + verification
└── __init__.py    public API exports
```

## The 13 query kinds (v0.6.0)

| Kind | Surface | What it does | Wired in |
|---|---|---|---|
| `verify` | `force = mass * acceleration` | multi-plane equation audit | v0.4.0 |
| `analogy` | `A : B :: C : ?` | proportional analogy in a named subspace | v0.4.0 |
| `describe` | `describe carbon` | the dossier of one carrier (now with lattice projection) | v0.4.0, augmented v0.5.3 |
| `nearest` | `nearest 5 to pressure` | ranking under the Griess metric | v0.4.0 |
| `product` | `sakuma product` | the Norton-Sakuma 2A algebra | v0.4.0 |
| `cluster` | `cluster C, N, O into 2` | exact agglomerative clustering | v0.4.0 |
| `spatial` | `mog grid of oxygen` | the MOG presentation of a carrier | v0.4.0 |
| `project` | `project carbon oxygen` | walk all 5 dimension-projection layers | v0.5.3 |
| `trilinear` | `trilinear 127 432 463` | the invariant form ⟨A·B, C⟩ | v0.5.3 |
| `coherence` | `coherence carbon` | the five-shell NRCI breakdown | v0.5.3 |
| `report` | `report leech distribution` | on-demand recomputation of facts | v0.5.4 |
| `angle` | `angle carbon oxygen` | exact cosine comparison | v0.5.4 |
| `unknown` | (fallback) | diagnostics + suggestions | v0.4.0 |

## The `GLM.py` CLI

The CLI entry point lives at the **repo root** (`../GLM.py`), not in
this folder.  It is a thin shell over this package.  See the root
README's "Quick Start" for usage.

## Design invariants

- **No float anywhere**, in the runtime sources *or* in the scripts
  they generate.  `script_is_exact` checks generated source by AST.
- **No RNG and no wall clock.** A trace must be byte-identical between
  runs.
- **XOR only where it is addition.** On the F_2 module Lambda/2Lambda.
- **Failures are results.** An unsolved query returns a Solution with
  `ok=False` and is recorded in the history.
