# Hypothesis resolution records

These are the resolver's recorded decisions. The static pre-admission registry
still shows `doesnt_know` as provenance; these records are the decision layer,
not a mechanism-card admission.

## Current decisions

| Lead | Decision | Evidence |
|---|---|---|
| `nematic-q-tensor-bounding-box` | `retired` | Scalar Q-tensor invariants are orientation-blind; the invariant-only projection map cannot exist. See [evidence](../evidence/nematic-q-tensor/README.md) and [record](nematic-q-tensor-bounding-box.json). |
| `bresenham-quantized-carry` | `retained` (narrowed) | Exact one-tick floor equivalence, range test and negative control; the existing two-tick target is not equivalent. See [evidence](../evidence/bresenham/README.md) and [record](bresenham-quantized-carry.json). |

The Q-tensor retirement is for the lead as worded. A separate
orientation-only eigenframe lead may be declared, but it must not inherit the
invariant claim. The Bresenham retention is only for the one-tick variant; it
does not promote the lead or claim equivalence with the existing two-tick route.

## History

The first pass recorded both leads as retired because no evidence artifact
existed. Those records are preserved as the initial absence audit:

- [Q-tensor initial record](history/nematic-q-tensor-bounding-box-initial-retired.json)
- [Bresenham initial record](history/bresenham-quantized-carry-initial-retired.json)

They were superseded on 2026-11-11 after the evidence scripts in
`docs/evidence/` were written and run. The history is retained so a later
decision can see what changed.
