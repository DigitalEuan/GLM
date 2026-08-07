# ARC-AGI v27 — Diverse Training + Improved Perception

**Date:** 2026-08-07
**Iterations:** 5
**Tasks:** 25 ARC + 50 diverse (10 types) + 2 variants

## What's New (v27)

### 1. Diverse Puzzle Types
10 new puzzle generators that exercise different cognitive abilities:
- Colour Cascade (modular arithmetic mapping)
- Symmetry Complete (mirror detection and completion)
- Border Frame (boundary extraction)
- Object Gravity (object-aware gravity)
- Pattern Tile (periodicity detection)
- Diagonal Transform (diagonal operations)
- Conditional Region (region-dependent rules)
- Connected Component (flood fill, component labelling)
- Noise Clean (noise removal, structure preservation)
- Count Encode (object counting and encoding)

### 2. Object Detection
Connected component analysis extracts objects with properties:
colour, size, bounding box, centroid. Used by perception pipeline.

### 3. Symmetry Detection
Detects horizontal, vertical, rotational (180°), and diagonal symmetry.
Reports symmetry type to the reasoning pipeline.

### 4. Fixed Import Paths
All hardcoded `/home/z/my-project/scripts` replaced with relative repo paths.
Engine loaded from `../GMHGL/ubp_unified_v5.py`.

### 5. Improved Error Handling
No bare `except: pass`. All exceptions caught specifically with logging.
Pipeline continues on individual task failures.

## Growth Summary

| Metric | Start | End | Growth |
|---|---|---|---|
| CRG edges | 3123 | 3203 | +80 |
| HexColour addresses | 46 | 48 | +2 |
| Best score | 23/78 | 24/78 | +1 |
| Edges to 5000 | 1877 | 1797 | -80 |

## Results Per Run

| Run | Solved | Edges | +Edges | →5000 |
|---|---|---|---|---|
| 142 | 23/78 | 3123 | +0 | 1877 |
| 143 | 24/78 | 3143 | +0 | 1857 |
| 144 | 23/78 | 3163 | +0 | 1837 |
| 145 | 24/78 | 3183 | +0 | 1817 |
| 146 | 23/77 | 3203 | +0 | 1797 |

## Aggregate Per-Type Scores

| Type | Solved | Total | Rate |
|---|---|---|---|
| arc | 15 | 125 | 12% |
| arc_variant | 2 | 14 | 14% |
| border | 23 | 25 | 92% |
| colour_cascade | 22 | 25 | 88% |
| conditional_region | 0 | 25 | 0% |
| connected_component | 5 | 25 | 20% |
| count_encode | 0 | 25 | 0% |
| diagonal | 0 | 25 | 0% |
| noise_clean | 0 | 25 | 0% |
| object_gravity | 25 | 25 | 100% |
| pattern_tile | 0 | 25 | 0% |
| symmetry | 25 | 25 | 100% |

## Stubs & Simplifications Addressed

1. **Import paths**: All 19 pipeline files fixed from hardcoded `/home/z/...` to relative paths
2. **Missing files**: Reconstructed `arc_v17_2_pipeline.py`, created `arc_v19_pipeline.py` symlink
3. **Error handling**: Replaced bare `except: pass` with specific exception catching + logging
4. **Perception gaps**: Added object detection (connected components) and symmetry detection
5. **Task diversity**: Added 10 puzzle generators (50 tasks) alongside 25 ARC tasks

## What's Next

1. More ARC tasks (full 400-task set when available)
2. Deeper object detection (shape classification, spatial relations)
3. Compositional proposals from object+symmetry analysis
4. Cross-task pattern transfer via CRG
5. Continue growing toward 5000 CRG edges
