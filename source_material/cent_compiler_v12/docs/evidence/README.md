# Evidence records

Runnable evidence used to resolve pre-admission leads and scope decisions.
These are decision records, not mechanism cards or supported operations.

| Record | Evidence | Result |
|---|---|---|
| `nematic-q-tensor-bounding-box` | [Q-tensor audit](nematic-q-tensor/README.md), [check](nematic-q-tensor/check.py) | No map from scalar Q-tensor invariants alone; orientation is an additional input. The original lead is retired. |
| `bresenham-quantized-carry` | [Bresenham audit](bresenham/README.md), [check](bresenham/check.py) | Exact one-tick floor delta-sigma equivalence over the declared range; the existing two-tick target is not equivalent. The lead is retained only as the narrowed one-tick variant. |
| `live-glm-breadth` | [Live GLM audit](live-glm-breadth/README.md), [check](live-glm-breadth/check.py) | The live GLM CLI refuses `sqrt`/`exp`; its exact `mult`/`div` results have no production mechanism cards. T3 records a refusal for the current interface. |

Run from the project root:

```bash
python3 docs/evidence/nematic-q-tensor/check.py
python3 docs/evidence/bresenham/check.py
python3 docs/evidence/live-glm-breadth/check.py
```

The scripts use exact rational arithmetic and declared external results. They do
not claim a physical liquid-crystal state, a hardware implementation, a GLM
model score or a performance result.
