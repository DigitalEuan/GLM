# Current transfer proposal examples

Generated with the current `cent` CLI on 2026-11-12. These bundles are
reviewable transfer handoffs, not validated transfers. Every proposal remains
`status: unvalidated` until its target handoff runs.

| Operation | Proposals | `ready-for-execution` | `needs-target-adapter` |
|---|---:|---:|---:|
| `sqrt` | 3 | 1 (`log-domain-sqrt`) | 2 (`cam-profile`, `orifice-pressure-flow`) |
| `sum` | 3 | 3 (`kcl-conservation`, `fluid-continuity`, `opamp-summing`) | 0 |
| `difference` | 3 | 3 (`kcl-conservation`, `fluid-continuity`, `opamp-summing`) | 0 |
| `quantized_carry` | 1 | 1 (`delta-sigma-error-feedback`) | 0 |
| **Total** | **10** | **8** | **2** |

All three `sum` and all three `difference` mechanisms are executable and expose
mechanism-specific handoff commands; `sqrt` keeps two adapter gaps for cam and
orifice, both with recorded T1 refusal conditions.

## Files

- `sqrt/`, `sum/`, `difference/`, `quantized_carry/` — one bundle each, with
  `index.json`, `index.md` and one JSON proposal per candidate.
- `evaluation.json` — the current `cent evaluate --json` payload, including its
  `partial` output certificate for the declared gaps.

## Regenerate

```bash
for op in sqrt sum difference quantized_carry; do
  python3 cent propose "$op" --target glm-reference --out "examples/transfer/$op"
done
python3 cent evaluate --json > examples/transfer/evaluation.json
```

Do not overwrite a bundle that has a review ledger (`reviews.json`) without
preserving its review history.

## Relationship to the other examples

The 22 `examples/proposal_*.cir` files are physical-backend show-work examples,
pinned by `tests/test_proposals.py`. They are still current for that backend.
They are not the same artifact class as these transfer proposals.

See [`../../docs/CURRENT_SCOPE_AND_NEXT_TRACK.md`](../../docs/CURRENT_SCOPE_AND_NEXT_TRACK.md)
for the capability boundary, loose ends and next development track.
