# ARC-AGI v17.7 — Full GLM Vocabulary Integration

**Date:** 2026-08-06
**Key integration:** Full 4,256-word GLM vocabulary with REAL vectors
**Tasks:** 36
**Iterations:** 10

---

## What's new in v17.7

1. **4,256-word vocabulary** from glm_unified_resource.json — REAL corpus-derived 24-bit vectors (not hash-derived)
2. **250 MASSIVE CRG edges** from GLM_CRG_MASSIVE.py
3. **67 unified relations** from glm_unified_resource.json
4. **Total concepts:** 4620 (up from 527 in v17.6)
5. **Total CRG edges:** 1103 (up from 814 in v17.6)

### Why the real vectors matter

v17.6 used hash-derived vectors (deterministic but arbitrary — `hash(word) & 0xFFF`).
v17.7 uses the REAL GLM vectors from glm_unified_resource.json, which are:
- Derived from corpus co-occurrence statistics (SVD)
- Snapped to Golay codewords
- Grammar-aligned (dominant quadrant = grammatical role)

This means **Hamming distance = REAL semantic distance**. Two words that are
semantically related (like 'gravity' and 'mass') are close in Hamming space,
not just arbitrarily close.

## Multi-run results

| Run | Solved | New | Concepts | Edges |
|---|---|---|---|---|
| 32 | 15/36 | 11 | 4620 | 923 |
| 33 | 15/36 | 11 | 4620 | 943 |
| 34 | 15/36 | 11 | 4620 | 963 |
| 35 | 15/36 | 11 | 4620 | 983 |
| 36 | 15/36 | 11 | 4620 | 1003 |
| 37 | 15/36 | 11 | 4620 | 1023 |
| 38 | 15/36 | 11 | 4620 | 1043 |
| 39 | 15/36 | 11 | 4620 | 1063 |
| 40 | 15/36 | 11 | 4620 | 1083 |
| 41 | 15/36 | 11 | 4620 | 1103 |

### Summary

- **First run:** 15/36 solved
- **Best run:** Run 32 — 15/36 solved
- **Final run:** 15/36 solved
- **Vocabulary:** 4620 concepts
- **CRG:** 1103 edges

## Learning Analysis

- **Total experiences:** 215
- **Total successes:** 40

### Best strategies

| Strategy | Successes |
|---|---|
| colour_map_via_AND | 325 |
| conditional_solver | 98 |
| settlement_gravity | 39 |
| flip_solver | 23 |

### Most useful concepts

| Concept | Successes when activated |
|---|---|
| p | 1395 |
| a | 495 |
| i | 495 |
| shape | 485 |
| colour | 485 |
| substrate | 465 |
| form | 465 |
| rate | 465 |

## Comparison across all versions

| Metric | v17.4 | v17.5 | v17.6 | v17.7 |
|---|---|---|---|---|
| Tasks | 10 | 25 | 36 | 36 |
| Iterations | 3 | 10 | 10 | 10 |
| GLM concepts | 65 | 527 | 527 | 4620 |
| CRG edges | 110 | 763 | 814 | 1103 |
| Real vectors | ❌ | ❌ | ❌ | ✅ |
| Sandbox | ❌ | ❌ | ✅ | ✅ |
| Best solved | 5/10 | 10/25 | 15/36 | 15/36 |

## Resources integrated

| Resource | Source | Size | Status |
|---|---|---|---|
| Vocabulary | glm_unified_resource.json | 4,256 words | ✅ |
| CRG EXPANDED edges | GLM_CRG_EXPANDED.py | 597 edges | ✅ |
| CRG MASSIVE edges | GLM_CRG_MASSIVE.py | 250 edges | ✅ |
| Unified relations | glm_unified_resource.json | 67 relations | ✅ |
| Broad CRG edges | v17.3 BROAD_CRG_EDGES | 68 edges | ✅ |
| Lingo vocabulary | semantic_layer.py | 26 concepts | ✅ |
| Expanded concepts | v17.3 EXPANDED_CONCEPTS | 39 concepts | ✅ |
| Language KB | ubp_lang_kb_combined_v4.json | 1,086 entries | available |
| Sandbox | GLM_sandbox.py | verification | ✅ |
| Bit-Ops layer | v10/v11 | throughout | ✅ |

## Next steps

1. **Load the full GLM.py runtime** — the 4,256 vocabulary is loaded, but the full GLM.py runtime (with chat(), three_column thinking, text mining) is not yet integrated. This would give natural language reasoning.
2. **Use the language KB definitions** — the 1,086 entries have definitions that could ground the GLM's reasoning in natural language.
3. **Run 50-100 iterations** — the growth is cumulative. More runs = smarter GLM.
4. **Analyze the unsolved tasks** — which need natural language reasoning?
5. **Integrate the GLM's chat() method** — let the GLM 'talk' about each task in English before solving.
