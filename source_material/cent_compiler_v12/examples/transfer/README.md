# Current transfer proposal examples

Generated with the current `cent` CLI on 2026-11-12. These bundles are
reviewable transfer handoffs, not validated transfers. Every proposal remains
`status: unvalidated` until its target handoff runs. `cent trial <bundle>` is a
computational side-loop over declared fixed vectors; `cent trial --wheel`
spins through the declared operation registry and runs every executable
proposal. Neither changes review state or marks a proposal validated.

| Operation | Proposals | `ready-for-execution` | `needs-target-adapter` |
|---|---:|---:|---:|
| `sqrt` | 3 | 1 (`log-domain-sqrt`) | 2 (`cam-profile`, `fluid-continuity`) |
| `sum` | 3 | 3 (`kcl-conservation`, `fluid-continuity`, `opamp-summing`) | 0 |
| `difference` | 3 | 3 (`kcl-conservation`, `fluid-continuity`, `opamp-summing`) | 0 |
| `quantized_carry` | 3 | 1 (`delta-sigma-error-feedback`) | 2 (`pll-phase-tracking`, `orifice-pressure-flow`) |
| `exp` | 3 | 1 (`log-domain-arithmetic`) | 2 (`log-domain-sqrt`, `fluid-continuity`) |
| `log` | 3 | 1 (`log-domain-arithmetic`) | 2 (`log-domain-sqrt`, `fluid-continuity`) |
| `mult` | 3 | 1 (`log-domain-arithmetic`) | 2 (`fluid-continuity`, `kcl-conservation`) |
| `div` | 3 | 1 (`log-domain-arithmetic`) | 2 (`fluid-continuity`, `kcl-conservation`) |
| `reciprocal` | 3 | 1 (`log-domain-arithmetic`) | 2 (`fluid-continuity`, `kcl-conservation`) |
| `sign` | 3 | 1 (`threshold-comparator`) | 2 (`fluid-continuity`, `kcl-conservation`) |
| **Total** | **30** | **14** | **16** |

These bundles follow D1's top-three structural ranking. Candidates that do not
have an executable target adapter remain reviewable gaps; they are not
validated transfers. Under D2/D3, `fluid-continuity` and `opamp-summing`
proposals carry `mechanism.principle_id = "kcl-conservation"`, and
`log-domain-arithmetic` carries `transcendental-identity`, plus the executable
operator chain that generated each card; the other proposals carry empty
generation metadata. The orifice T1 refusal record remains in the evaluation
corpus even though the current top-three ranking does not return it for `sqrt`.

## Files

- `sqrt/`, `sum/`, `difference/`, `quantized_carry/`, `exp/`, `log/`, `mult/`,
  `div/`, `reciprocal/`, `sign/` — one bundle each, with `index.json`,
  `index.md` and one JSON proposal per candidate.
- `evaluation.json` — the current `cent evaluate --json` payload, including its
  `partial` output certificate for the declared gaps. The evaluation is
`certified: false` with 15/16 candidate recall, 9/10 case recall, 14/14
reference target pairs and 2/6 negative-control failures; the unlabelled
candidates are in triage, not counted as false positives.

## Regenerate

```bash
for op in sqrt sum difference quantized_carry exp log mult div reciprocal sign; do
  python3 cent propose "$op" --target glm-reference --out "examples/transfer/$op"
done
python3 cent evaluate --json > examples/transfer/evaluation.json
```

Do not overwrite a bundle that has a review ledger (`reviews.json`) without
preserving its review history.

## Relationship to the other examples

The 22 `examples/proposal_*.cir` files are physical-backend show-work examples,
pinned by `tests/test_proposals.py`. They are still current for that backend.
They are not the same artifact class as these transfer proposals. The D4
self-transfer utility ledger is a separate artifact under
[`../self/`](../self/README.md), and the D5 generated negatives are under
[`../refutation/`](../refutation/README.md).

See [`../../docs/CURRENT_SCOPE.md`](../../docs/CURRENT_SCOPE.md)
for the capability boundary and gap ledger, and [`../../DIRECTIVE.md`](../../DIRECTIVE.md)
for the work order.
