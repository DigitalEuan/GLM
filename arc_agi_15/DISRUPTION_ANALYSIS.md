# Disruption Analysis — ARC AGI × UBP/GLM

**Date:** 29 July 2026
**Score:** 5/50 (10%)

## The Disruption Lens

Instead of asking "what rule transforms A→B?", we ask:
**"How does A perturb the substrate, and what does the perturbed state look like?"**

- **P** = the substrate (background grid)
- **A** = the input (perturbation)
- **B** = the output (equilibrium after perturbation propagates)

This connects to:
- LAW_PATTERN_001: "Visual puzzles are coherence maps"
- LAW_TOPOLOGICAL_ERASURE_001: "The substrate prioritizes geometric stability"
- LAW_OPTICAL_TOGGLE_001: "Light propagates via neighbour-dependent toggle"

## Solves Found by Disruption Lens

### 575b1a71 — Column-Rank Fill
**Rule:** Fill = rank of the cell's column among all columns that contain at least one zero.

**Why it was invisible to other approaches:**
- Distance-based: no distance pattern
- Neighbourhood: no local pattern
- DSL: no geometric operation
- Object segmentation: not an object-level rule

**Why the disruption lens found it:**
The rule depends on the *global structure* of the grid — which columns have zeros. The disruption lens sees this as: "the substrate responds to perturbation by filling zeros with the rank of their column among all columns that have zeros."

### ae58858e — Component-Size Recolour
**Rule:** Connected components of colour 2 with size ≥ 4 become 6.

**Why it was invisible to other approaches:**
- Distance-based: no distance pattern
- Neighbourhood: no local pattern
- DSL: no geometric operation
- Recolour: not all 2s change (only large components)

**Why the disruption lens found it:**
The rule depends on the *size of connected components* — an object-level property. The disruption lens sees this as: "the substrate responds to perturbation by recolouring large components but preserving small ones."

## Disruption Types

| Type | Description | Tasks | Solves |
|------|-------------|-------|--------|
| SIZE_CHANGE | Grid dimensions transform | 17 | 0 |
| PURE_FILL | Only zeros become non-zero | 11 | 1 (575b1a71) |
| FILL+RECOLOUR | Both fill and colour change | 11 | 1 (1e0a9b12) |
| PURE_RECOLOUR | Only non-zero cells change colour | 11 | 3 (396d80d7, 45737921, ae58858e) |

## PURE_FILL Analysis (11 tasks)

| Task | Pattern | Status |
|------|---------|--------|
| 575b1a71 | Column-rank fill | **SOLVED** |
| 00dbd492 | Row-based fill (rows 1-7→3, 11-13→8) | Complex |
| d43fd935 | Column-based fill (cols 4,5→7, cols 6-8→8) | Partial |
| 712bf12e | Uniform fill (all→2, partial) | Doesn't cover all zeros |
| d4f3cd78 | Uniform fill (all→8, partial) | Doesn't cover all zeros |
| fcc82909 | Uniform fill (all→3, partial) | Doesn't cover all zeros |
| 36d67576 | Mixed fills (1 and 3) | No pattern found |
| 484b58aa | Many fill colours | Complex |
| 54d82841 | Single fill at (4,2)→4 | Too few data points |
| 9f27f097 | Mixed fills (1 and 4) | No pattern found |
| e048c9ed | Single fill at (2,2)→1 | Too few data points |

## PURE_RECOLOUR Analysis (11 tasks)

| Task | Mapping | Status |
|------|---------|--------|
| 396d80d7 | {7: 2} consistent | **SOLVED** (Minkowski) |
| 45737921 | {5: 8, 8: 5} consistent | **SOLVED** (k-arm) |
| ae58858e | {2: 6} component-size | **SOLVED** (disruption) |
| 50846271 | {5: 8} consistent | Conditional (unknown rule) |
| 7acdf6d3 | {7: 9, 9: 7} swap | Conditional |
| f8f52ecc | {1: 2} consistent | Conditional |
| Others | Inconsistent | Complex |

## FILL+RECOLOUR Analysis (11 tasks)

| Task | Recolour | Fill | Status |
|------|----------|------|--------|
| 1e0a9b12 | Inconsistent | Mixed | **SOLVED** (gravity) |
| 5521c0d9 | Consistent (4,2,1→0) | Positional | Complex |
| c62e2108 | Consistent | Uniform (8) | Partial |
| d255d7a7 | Consistent (7→0, 9→7) | Mostly 7 | Partial |
| Others | Inconsistent | Mixed | Complex |

## The Disruption Map

```
SOLVED (5/50 = 10%)
┌────────────────────────────────────────────────────┐
│ 1e0a9b12   DSL gravity                            │
│ 45737921   k-arm similarity                       │
│ 396d80d7   Minkowski p=1.5 distance               │
│ 575b1a71   Column-rank fill (DISRUPTION)          │
│ ae58858e   Component-size recolour (DISRUPTION)    │
└────────────────────────────────────────────────────┘

THE WALL (45/50 = 90%)
┌────────────────────────────────────────────────────┐
│ SIZE-CHANGE (17)    PURE_FILL (9 remaining)        │
│ FILL+RECOLOUR (10)  PURE_RECOLOUR (8 remaining)    │
└────────────────────────────────────────────────────┘
```

## Key Insight

The disruption lens reveals **global patterns** that local approaches miss:
- **Column-rank fill** — depends on which columns have zeros
- **Component-size recolour** — depends on the size of connected components

These are **structural properties of the perturbation field**, not local cell-level rules. The disruption lens is the right tool for finding global rules.

## What the Disruption Lens Adds

The disruption lens is a **new category of tool** — it sees global patterns that distance, neighbourhood, DSL, and object segmentation all miss. The two new solves prove it works.

The lens is most effective for tasks where the rule depends on the **global configuration** of the grid, not just local cell properties.

## Files

```
v044_disruption.py — Disruption analysis implementation
v045_disruption_fisher.py — Systematic pattern search
DISRUPTION_ANALYSIS.md — This file
```
