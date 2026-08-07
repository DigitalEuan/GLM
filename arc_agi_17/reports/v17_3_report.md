# ARC-AGI v17.3 — Growth Layer Results

**Date:** 2026-08-06
**Run number:** 1
**Approach:** GROWTH (extends v17.2, doesn't replace it)

---

## Summary

- **Tasks tested:** 10
- **Solved:** 5/10
- **New solves:** 1
- **Run number:** 1 (the system has run 1 times)

## GLM Growth

- **Total concepts:** 65 (+39 this run)
- **Total CRG edges:** 98 (+68 this run)

### New concepts added this run:

- **cause** (ADJECTIVE): CAUSAL_LINK
- **effect** (ADJECTIVE): CONSEQUENCE
- **enable** (OPERATOR): ENABLEMENT
- **prevent** (ADJECTIVE): INHIBITION
- **require** (NOUN): PREREQUISITE
- **before** (OPERATOR): PRECEDES
- **after** (ADJECTIVE): FOLLOWS
- **sequence** (NOUN): ORDERED_SERIES
- **repeat** (NOUN): PERIODIC_ITERATION
- **cycle** (OPERATOR): CLOSED_LOOP
- **region** (VERB): SPATIAL_DOMAIN
- **boundary** (ADJECTIVE): FRONTIER
- **center** (NOUN): CENTROID
- **edge** (NOUN): PERIMETER
- **corner** (ADJECTIVE): VERTEX_POINT
- **measure** (ADJECTIVE): QUANTIFICATION
- **label** (VERB): IDENTIFIER_TAG
- **threshold** (NOUN): DECISION_BOUNDARY
- **ratio** (NOUN): PROPORTIONALITY
- **count_value** (ADJECTIVE): INTEGER_RESULT
- ... and 19 more

### New CRG edges added this run:

- cause --produces--> effect
- enable --permits--> effect
- prevent --blocks--> effect
- require --precedes--> enable
- condition --gates--> effect
- before --precedes--> after
- sequence --contains--> before
- repeat --generates--> sequence
- cycle --contains--> sequence
- repeat --implies--> cycle
- region --contains--> cell
- region --bounded_by--> boundary
- boundary --surrounds--> region
- center --inside--> region
- edge --part_of--> boundary
- corner --part_of--> boundary
- grid --composed_of--> region
- measure --produces--> count_value
- measure --uses--> rule
- label --identifies--> object
- ... and 48 more

## Learning Analysis (HOW the GLM learns)

Per user: 'the Long Term Memory will eventually show us how the GLM learns so we can bypass a pile of training by designing training routines that specifically grow it where needed.'

- **Total experiences:** 205
- **Total successes:** 30

### Fastest task types (fewest attempts to first success)

| Task type | Attempts to first success |
|---|---|
| high_overlap | 1 |

This tells us which task types the GLM learns fastest. These need less training.

### Best strategies (most successes)

| Strategy | Successes |
|---|---|
| conditional_solver | 2 |
| colour_map_via_AND | 2 |
| settlement_gravity | 1 |

These are the GLM's strengths. Build on them.

### Most useful concepts (activated in successful reasoning)

| Concept | Successes when activated |
|---|---|
| shape | 5 |
| colour | 5 |
| size | 5 |

These concepts should be EXPANDED — they correlate with success.

## Per-task results

| Task | Task type (simple) | Task type (BW-1024) | Solved? | Strategy | New? | Activated concepts |
|---|---|---|---|---|---|---|
| 00dbd492 | high_overlap | high_overlap_low_nrci | ✗ | None |  | shape, colour, size |
| 1e0a9b12 | high_overlap | high_overlap_low_nrci | ✓ | settlement_gravity |  | shape, colour, size |
| 396d80d7 | high_overlap | high_overlap_high_nrci | ✓ | conditional_solver |  | shape, colour, size |
| 45737921 | high_overlap | high_overlap_low_nrci | ✗ | None |  | shape, colour, size |
| 50846271 | high_overlap | high_overlap_low_nrci | ✓ | colour_map_via_AND | NEW! | shape, colour, size |
| 54d82841 | high_overlap | high_overlap_low_nrci | ✓ | colour_map_via_AND |  | shape, colour, size |
| 575b1a71 | high_overlap | high_overlap_low_nrci | ✗ | None |  | shape, colour, size |
| a85d4709 | size_change | size_change_low_nrci | ✗ | None |  | shape, colour, size |
| ae58858e | high_overlap | high_overlap_low_nrci | ✓ | conditional_solver |  | shape, colour, size |
| e48d4e1a | medium_overlap | medium_overlap_high_nrci | ✗ | None |  | shape, colour, size |

## Comparison across versions

| Metric | v17 | v17.1 | v17.2 | v17.3 |
|---|---|---|---|---|
| Solvers | 8 | 11 | 8 | 10 |
| Solved | 4/10 | 5/10 | 5/10 | 5/10 |
| New solves | 1 | 1 | 1 | 1 |
| GLM concepts | — | — | 26 | 65 |
| CRG edges | — | — | 30 | 98 |
| Persistent LTM | ❌ | ❌ | ❌ | ✅ |
| Learning analysis | ❌ | ❌ | ❌ | ✅ |
| BW-1024 classifier | ❌ | ❌ | ❌ | ✅ |

## What grew this run

- **39 new concepts** added (general-purpose, not just ARC)
- **68 new CRG edges** added (broad semantic relations)
- **5 new successes** recorded to LTM
- **BW-1024 NRCI** used for finer task classification
- **Parity sign recolor** and **column rank** solvers re-added (were missing in v17.2)

## The growth mechanism

Per user: 'growth not rebuild each Time.'

The v17.3 pipeline:
1. **Loads** the previous GLM state (concepts + CRG edges) from `glm_state.json`
2. **Adds** new concepts and edges (broad, general-purpose)
3. **Runs** the pipeline with the grown system
4. **Saves** the grown state for the next run
5. **Analyzes** how the GLM is learning (which concepts correlate with success)

Each run adds to the previous state. The system gets smarter over time, not rebuilt.

## Next steps (growth-oriented)

1. **Run v17.3 multiple times** — each run grows the GLM. Watch the learning analysis change.
2. **Expand the most useful concepts** — the learning analysis shows which concepts correlate with success. Add more concepts related to those.
3. **Design targeted training routines** — use the learning analysis to identify which task types need more training, and design routines that grow the GLM in those areas.
4. **Integrate the full GLM** (from glm_machine/) — the current 50+ concepts are a proof of concept. The full GLM has 2,550 concepts and 989 CRG edges.
5. **Use the CRG for reasoning** — the 80+ edges are currently transparent (for debugging). Next step: use them to COMPUTE new strategies, not just classify tasks.
