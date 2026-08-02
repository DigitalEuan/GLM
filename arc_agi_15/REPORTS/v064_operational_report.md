# v064 Operational UBP/GLM Report

## Score

**9/50 (18.0%)** on `data/training`.

## What this system can solve

| Task | Solver | Physics category |
|---|---|---|
| `00dbd492` | `multi_interior_fill` | expand |
| `1e0a9b12` | `gravity_down` | enrich |
| `396d80d7` | `minkowski_distance` | preserve |
| `45737921` | `local_swap` | preserve |
| `54d82841` | `colour_center_fill` | enrich |
| `575b1a71` | `column_rank_fill` | expand |
| `a85d4709` | `marker_fill_85` | enrich |
| `ae58858e` | `cond_recolour` | preserve |
| `e48d4e1a` | `cross_shift_by_markers` | simplify |

## Solver capability ledger

| Solver | What it can do | Why it stops |
|---|---|---|
| `multi_interior_fill` | fills enclosed zero-regions using region-size→colour mappings learned from train pairs | cannot infer new fill logic when enclosed-region size alone is insufficient |
| `gravity_down` | compacts non-zero cells downward column-wise while preserving order | does not handle lateral motion, object interaction, or shape rewriting |
| `minkowski_distance` | fills background cells selected by a learned distance/adjacency rule | covers only a narrow distance-selected fill family |
| `local_swap` | swaps the two colours inside a connected non-zero component | requires exactly two colours within a connected component |
| `colour_center_fill` | projects object-group centres into the bottom row | depends on a bottom-row projection target; no support for arbitrary projection axes |
| `column_rank_fill` | fills zero-columns by their left-to-right rank among zero-bearing columns | assumes a global column-order rule, not arbitrary recolour/fill layouts |
| `marker_fill_85` | replaces rows marked by colour-5 sentinels with learned fill colours | works only for the learned row-marker family |
| `cond_recolour` | recolours objects when a learned component-size threshold is met | supports only single-threshold object recolouring, not chained conditions |
| `cross_shift_by_markers` | translates a cross by the count of marker cells | handles only marker-count-driven cross translation, not general object motion |

## Why the remaining tasks fail

| Reason | Tasks |
|---|---|
| has no consistent global colour mapping across train pairs | 41 |
| needs conditional recolouring or object-specific selection rather than one uniform rule | 41 |
| needs relational object selection or object ranking before transformation | 21 |
| needs a size-changing transform such as crop, selection, extraction, or downsampling | 17 |
| introduces a derived fill colour that must be inferred from structure, not copied directly | 10 |
| needs a multi-step composition that both erases and synthesises cells | 6 |
| covered by solver 'colour_center_fill' because its train pairs match that solver's rule family | 1 |
| covered by solver 'column_rank_fill' because its train pairs match that solver's rule family | 1 |
| covered by solver 'cond_recolour' because its train pairs match that solver's rule family | 1 |
| covered by solver 'cross_shift_by_markers' because its train pairs match that solver's rule family | 1 |
| covered by solver 'gravity_down' because its train pairs match that solver's rule family | 1 |
| covered by solver 'local_swap' because its train pairs match that solver's rule family | 1 |
| covered by solver 'marker_fill_85' because its train pairs match that solver's rule family | 1 |
| covered by solver 'minkowski_distance' because its train pairs match that solver's rule family | 1 |
| covered by solver 'multi_interior_fill' because its train pairs match that solver's rule family | 1 |

## Category breakdown

| Physics category | Tasks | Unsolved |
|---|---|---|
| compress | 4 | 4 |
| enrich | 21 | 18 |
| expand | 3 | 1 |
| preserve | 12 | 9 |
| simplify | 10 | 9 |

## Unsolved task snapshot

| Task | Category | Primary blocker |
|---|---|---|
| `1f642eb9` | enrich | has no consistent global colour mapping across train pairs |
| `2697da3f` | preserve | needs a size-changing transform such as crop, selection, extraction, or downsampling |
| `2753e76c` | compress | needs a size-changing transform such as crop, selection, extraction, or downsampling |
| `2bcee788` | enrich | has no consistent global colour mapping across train pairs |
| `3345333e` | simplify | has no consistent global colour mapping across train pairs |
| `36d67576` | enrich | has no consistent global colour mapping across train pairs |
| `3979b1a8` | enrich | needs a size-changing transform such as crop, selection, extraction, or downsampling |
| `46c35fc7` | simplify | has no consistent global colour mapping across train pairs |
| `484b58aa` | preserve | has no consistent global colour mapping across train pairs |
| `50846271` | enrich | has no consistent global colour mapping across train pairs |
| `5289ad53` | compress | needs a size-changing transform such as crop, selection, extraction, or downsampling |
| `538b439f` | preserve | has no consistent global colour mapping across train pairs |
| `5521c0d9` | preserve | has no consistent global colour mapping across train pairs |
| `5587a8d0` | simplify | needs a size-changing transform such as crop, selection, extraction, or downsampling |
| `5e6bbc0b` | enrich | has no consistent global colour mapping across train pairs |
| `662c240a` | compress | needs a size-changing transform such as crop, selection, extraction, or downsampling |
| `6ecd11f4` | compress | needs a size-changing transform such as crop, selection, extraction, or downsampling |
| `6f473927` | enrich | needs a size-changing transform such as crop, selection, extraction, or downsampling |
| `712bf12e` | enrich | has no consistent global colour mapping across train pairs |
| `782b5218` | preserve | has no consistent global colour mapping across train pairs |

## Interpretation

The current stack is strong when a task can be expressed as a **single interpretable rule family**: one distance law, one component-size rule, one fill rule, one marker-driven move, or one global ranking rule. It breaks when the task demands **chained decisions**: select an object class, erase part of it, derive a new colour, then reconstruct a new geometry.
