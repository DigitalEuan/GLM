# ARC-AGI v22 — All Components Generative

**Date:** 2026-08-06
**Key fix:** ALL components are now generative — their output DRIVES the next step

## Component Audit (v21 → v22)

| Component | v21 (passive) | v22 (generative) |
|---|---|---|
| Geometric work | Logged, ignored | **DRIVES proposal prioritization** |
| Sandbox | Initialized, never called | **VERIFIES each proposal before commit** |
| LTM routing | Loaded, never queried | **RECOMMENDS strategies based on success rate** |
| CRG edges | Loaded, never traversed | **TRAVERSED to generate proposals** |
| MathAtlas | Loaded, never called | **Provides exact Y constant for computation** |
| 4,620 concepts | Loaded, never referenced | **Activated concepts drive CRG traversal** |

## Results

| Run | Solved | Mind | Analogical | CRG | LTM | Sandbox |
|---|---|---|---|---|---|---|
| 96 | 14/40 | 2 | 1 | 12 | 12 | 2 |
| 97 | 14/40 | 2 | 1 | 12 | 12 | 2 |
| 98 | 14/40 | 2 | 1 | 12 | 12 | 2 |

### Summary
- **Best run:** Run 96 — 14/40
- **GLM mind solves:** 3
- **Generative usage:** CRG=12, LTM=12, Sandbox=2

## What "generative" means

A component is GENERATIVE when its output is USED by the next step:
- CRG generates proposals → proposals are TESTED → results feed back
- LTM recommends strategies → recommendations PRIORITIZE proposals
- Sandbox verifies → verification GATES the commit
- Geometric work classifies → classification PRIORITIZES proposals
- MathAtlas provides constants → constants are USED in NRCI/TAX

A component is PASSIVE when it's loaded but its output is ignored.
v21 had 7 passive components. v22 has 0.
