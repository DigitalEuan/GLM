# ARC AGI × UBP/GLM — Experiment Tracker

**Date:** 29 July 2026
**Author:** E.R.A. Craig + AI Assistant

## Score: 5/50 (10%)

| # | Task | Solver | Module | Discovery |
|---|------|--------|--------|-----------|
| 1 | `1e0a9b12` | dsl_GRAVITY_DOWN | v029 | DSL ops |
| 2 | `45737921` | free_k_arm | v029 | Similarity matching |
| 3 | `396d80d7` | Minkowski p=1.5 | v033 | **Automated** sweep |
| 4 | `575b1a71` | Column-rank fill | v044 | **Disruption** lens |
| 5 | `ae58858e` | Component size ≥ 4 | v044 | **Disruption** lens |

## Modules Built (16 total)

| # | Module | Approach | Solves | Verdict |
|---|--------|----------|--------|---------|
| 1 | v030 recolour | Consistent/conditional recolour | 0 | No consistent mapping |
| 2 | v030 pattern | Flood fill, spread, grow | 0 | ARC fills aren't simple |
| 3 | v031 rules | General rule discovery | 0 | Rules too complex |
| 4 | v032 distance | Manhattan + diagonal filter | **1** | **WORKS** |
| 5 | v033 Minkowski | Vectorized p-norm sweep | 0 | Rediscovers v032 |
| 6 | v034 totient | Geometric number theory | 0 | Feature enrichment |
| 7 | v035 combined | Unified pipeline | 0 | Integration layer |
| 8 | v036 Cayley-Menger | Object identity, containment | 0 | ARC uses spatial relations |
| 9 | v037 Lucas-Lehmer | Trajectory fingerprint | 0 | Dynamic features unused |
| 10 | v038 per-colour | Colour-specific distances | 0 | No colour-specific rules |
| 11 | v039 compositional | Multi-step DSL composition | 0 | BLOCKED by conditional gap |
| 12 | v040 MOG conditional | MOG-encoded conditional recolour | 0 | Overfitting |
| 13 | v041 neighbourhood | Bitmask rules | 0 | Conditions too complex |
| 14 | v042 object level | Object segmentation | 0 | ARC uses spatial relations |
| 15 | v043 composition | Occam's razor grammar | 0 | No single rule works |
| 16 | v044 disruption | **Disruption lens** | **2** | **WORKS** |

## Synthetic Tests: 10/10 Pass

All primitives work correctly:
- ✓ Distance-1 fill from objects
- ✓ Distance-2 + diagonal filter
- ✓ Neighbour-conditional recolour
- ✓ Count-based neighbour rule
- ✓ Fingerprint: symmetric positions match
- ✓ Fingerprint: different contexts differ
- ✓ Gravity down
- ✓ Rotate 90
- ✓ Connected components
- ✓ Frame detection

## What Worked

### 1. Minkowski p=1.5 (v032/v033)
- **Task:** 396d80d7
- **Rule:** bg cells at Minkowski p=1.5 distance ≈ 1.59 from objects → minority colour
- **Discovery:** Automated by sweep (not hardcoded)
- **Key insight:** Fractional Minkowski norms can express composite metric intersections

### 2. Column-Rank Fill (v044)
- **Task:** 575b1a71
- **Rule:** Fill = rank of column among columns with zeros
- **Discovery:** Disruption lens (global pattern)
- **Key insight:** The fill colour depends on the *entire grid structure*, not local context

### 3. Component-Size Recolour (v044)
- **Task:** ae58858e
- **Rule:** Connected components of colour 2 with size ≥ 4 become 6
- **Discovery:** Disruption lens (object-level rule)
- **Key insight:** The transformation depends on the *size of connected components*

## What Didn't Work

| Approach | Why it failed |
|----------|---------------|
| Consistent recolour | No task has consistent global mapping |
| Conditional recolour | Conditions more complex than neighbour-based |
| Pattern matching | ARC fills aren't simple enclosed regions |
| Rule learning | Rules are context-dependent |
| DSL compositions | BLOCKED by conditional gap |
| Totient/Cayley-Menger/Lucas-Lehmer | Feature enrichment only |
| Per-colour Minkowski | No colour-specific distance rules |
| MOG conditional | Overfitting to train addresses |

## The Fundamental Finding

**Every ARC task needs conditional recolouring.** No task has a consistent global colour mapping. The conditions are more complex than single-cell neighbourhood rules.

The disruption lens reveals **global patterns** that local approaches miss:
- Column-rank fill (575b1a71) — depends on entire grid structure
- Component-size recolour (ae58858e) — depends on connected component size

## UBP Laws Applied

| Law | Application | Status |
|-----|-------------|--------|
| LAW_PATTERN_001 | "Visual puzzles are coherence maps" | Disruption lens works |
| LAW_OPTICAL_TOGGLE_001 | "Neighbour-dependent toggle" | Tested, conditions too complex |
| LAW_TGIC_369_GENESIS | "3-Axis, 6-Face, 9-Neighbour" | Spatial constraints |
| LAW_TOPOLOGICAL_ERASURE_001 | "Geometric stability over magnitude" | Erasure patterns |

## Key Insights

1. **The disruption lens works** — found 2 new solves that 14 modules missed
2. **Minkowski p=1.5** expresses composite metrics as single fractional norms
3. **ARC tasks are perturbation responses** — input disrupts substrate, output is equilibrium
4. **Global rules exist** — column-rank, component-size depend on entire grid
5. **The tools work** — 10/10 synthetic tests; gap is in composition, not capability
6. **The UBP/GLM is a substrate for capability** — can encode any relationship, doesn't know which to use

## Next Steps

1. **Per-colour distance layers** — `dist_to_colour_X` for each non-bg colour
2. **Arrangement topology classifier** — scattered/frame/dense mode detection
3. **Compositional search with disruption classification** — use disruption type to select tools
4. **Weighted Minkowski** — row/column bias for anisotropic patterns
5. **Multi-sensor fusion** — combine all feature layers

## Files

```
v030_recolour_enhanced.py
v030_pattern_learner.py
v031_rule_learner.py
v032_distance_rule.py        ← SOLVES 396d80d7
v033_minkowski_sweep.py
v034_totient_kinetics.py
v035_combined_pipeline.py
v036_cayley_menger.py
v037_lucas_lehmer.py
v038_per_colour_minkowski.py
v039_compositional_search.py
v040_conditional_recolour.py
v041_neighbourhood_bitmask.py
v042_object_level.py
v043_composition_grammar.py
v044_disruption.py           ← SOLVES 575b1a71, ae58858e
v045_disruption_fisher.py
mog_leech.py
spatial_totient_kinetics.py
EXPERIMENT_TRACKER.md
EXPERIMENT_LOG.md
DISRUPTION_ANALYSIS.md
```
