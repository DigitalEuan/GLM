# Live GLM breadth refusal

This is the T3 decision record for the current external GLM CLI. It is a scope
refusal, not a claim that additional live operations are impossible.

## Probe

Run from the project root:

```bash
python3 docs/evidence/live-glm-breadth/check.py
```

The probe resolves the same CLI as the `glm-live` target: `GLM_CLI` when set,
otherwise the sibling `glm-study/src/GLM.py`. It sends five exact queries and
records the result rows:

| Query | Observed result | Consequence |
|---|---|---|
| `what is sqrt(2)` | refused; no carrier in an enabled domain | No exact live sqrt interface |
| `what is sqrt(9)` | refused; no carrier in an enabled domain | Not even a perfect-square shortcut is declared |
| `what is exp(0)` | refused; no carrier in an enabled domain | No exact live exp interface |
| `what is (1/2) * (1/3)` | answered exactly as `1/6` | Arithmetic exists, but `mult` has no mechanism card |
| `what is (1/2) / (1/3)` | answered exactly as `3/2` | Arithmetic exists, but `div` has no mechanism card |

The probe also checks that the declared live adapter map remains exactly:

```text
sum/kcl-conservation
difference/kcl-conservation
```

## Decision

T3 does **not** add a live adapter for this interface. The additional exact
operations (`mult`, `div`) are operation contracts without a production
mechanism card, so a live arithmetic check would not be a transfer validation.
`sqrt` and `exp` are refused by the CLI. The existing live target therefore
remains KCL `sum`/`difference` only, with no latency or bit-budget claim.

## Reopen conditions

T3 can reopen when at least one of these exists:

- a declared mechanism card with a source law, fixed vectors and an adapter for
  `mult` or `div`;
- an exact, reproducible live `sqrt` or `exp` result with fixed vectors;
- a broader live target with a declared external interface and any measured
  latency/bit budgets.

Until then, the refusal is the evidence boundary, not a hidden capability.
