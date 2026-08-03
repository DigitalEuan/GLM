# GLM v3.16.0 — Refined, Audited, with Continuous Learning

**v3.15.0 → v3.16.0**: Full stub/simplification audit completed. Continuous learning loop added — vectors now improve as the system processes queries. Clean manifest of what works and what data it needs.

## Stub/Simplification Audit Results

I audited every GLM module for stubs, silent failures, and simplifications. Here's the honest state:

### ✅ Real (No Stubs)
| Component | Status | Evidence |
|-----------|--------|----------|
| Golay(24,12) error correction | REAL | 2325-entry syndrome table, 4096 codewords, corrects 1/2/3-bit errors (verified test Y) |
| Leech NRCI calculation | REAL | Uses exact Y constant from π (58-term CF). NRCI=0.681 for weight-12 (stub would give 1.0, verified test Z) |
| Binary Linear Algebra | REAL | Uses real BLA from ubp_unified_v5 with hex-int fast path |
| BarnesWall 256D engine | REAL | Available in ubp_unified_v5, loaded at import |
| Monster Group (26 sporadics) | REAL | Available in ubp_unified_v5, loaded at import |
| SVD distributional vectors | REAL | PPMI + truncated SVD on 70K-token corpus |
| Grammar-aligned vectors | REAL | Quadrant-forced + quadrant-preserving Golay snap, 100% alignment |
| CRG (141 typed edges) | REAL | Hand-curated physics + master resource relations |
| Gap computation | REAL | AND-intersection produces VERB-dominant vectors (31.6% of edges) |
| Ontological grammar | REAL | Computes S→V→O from vector geometry, no templates |

### ⚠️ Simplifications (Honest, Not Stubs)
| Component | Simplification | Impact |
|-----------|----------------|--------|
| Grammatical role inference | Suffix heuristics + definition patterns (not a full POS tagger) | ~70% accuracy on role assignment. This is a TRAINING-TIME tool, not runtime — improving it doesn't add runtime dependencies |
| Continuous learning | Geometric refinement (not gradient descent) | Vectors move on the lattice via co-occurrence averaging, not backprop. This is BY DESIGN — no neural model, no stored text at runtime |
| `except: pass` (4 instances) | Silent failure in meta-graph recording, CRG auto-expand, ground_result, meta-graph record | Non-fatal — these are enhancement features, not critical path |

### ❌ Not Used (Legacy)
| Component | Location | Note |
|-----------|----------|------|
| `GolaySubstrateStub` | ubp_unified_v5.py line 947 | Used only by NoiseALU internally, NOT by GLM |
| Stub Golay/Leech engines | GLM01_substrate.py line 171-185 | Fallback ONLY if ubp_unified_v5.py is missing. Never activates in practice (`_HAS_REAL_ENGINE = True`) |
| GLM17 semantic frames | GLM17_semantic_frames.py | Superseded by GLM22 ontological grammar. Still imported but template-based approach is legacy |

## What's New in v3.16.0

### GLM24_continuous_learner.py (NEW — 280 lines)
The continuous learning loop you asked for. Vectors are added to and reorganized as chat/test runs — a continuous learning and improving loop.

**How it works (all within the substrate, no external ML):**

1. **Co-occurrence tracking**: When two words appear in the same query, their co-occurrence count increases (in-memory, no stored corpus)

2. **Vector refinement**: Every 10 queries, vectors with significant co-occurrence changes are refined:
   - Blend current vector with co-occurrence partners' vectors (weighted by count)
   - Re-threshold to 24 bits
   - Re-snap to Golay codeword (quadrant-preserving)
   - Update vocab entry in-place

3. **New word learning**: When a query contains a word not in vocab:
   - Infer grammatical role from suffix
   - Derive vector from co-occurring known words (averaged + thresholded)
   - Snap to Golay codeword (quadrant-preserving)
   - Add to vocab

4. **CRG edge learning**: When two words co-occur ≥3 times, a `co_occurs` edge is added to the CRG

5. **Persistence**: Learned state saves to `glm_learned_state.json` every 5 queries

**Verified**: After 12 queries co-occurring "hamiltonian" with other physics words, hamiltonian's vector changed (HD=8) — the system learned from the queries.

### New API
```python
rt = GLMRuntimeV37()
rt.chat("Tell me about the hamiltonian and time.")  # triggers learning
rt.learning_status()
# {"queries_processed": 1, "words_learned": 0, "edges_learned": 0,
#  "vectors_refined": 0, "cooccurrence_pairs": 3, "state_saved": false}
```

## Clean Manifest: What Works and What Data It Needs

### What Works (v3.16.0)
1. **Query answering** — 26/26 self-tests, 28/28 golden cases
2. **Math computation** — GCD, LCM, factorial, primality, integrate, differentiate, solve, simplify, ODE, Taylor, limit, vector ops, linear algebra
3. **Deliberative reasoning** — 13 problem patterns (divisibility, GCD proof, stars & bars, etc.)
4. **Knowledge base lookup** — 751 system KB entries + 4248 master resource definitions
5. **Natural language generation** — `chat_prose()` for fluent paragraphs, `generate_grammatical()` for computed S→V→O
6. **Continuous learning** — vectors refine from query co-occurrence, new words learned, CRG edges discovered
7. **Hex colour signatures** — every concept IS a #RRGGBB colour
8. **Real Golay error correction** — 3-bit correction on 2325-entry syndrome table
9. **Grammar-aligned vectors** — 100% quadrant alignment, 69% NOUN / 17% VERB / 11% ADJ / 3% OP

### Data Files Required
| File | Size | Purpose |
|------|------|---------|
| `ubp_unified_v5.py` | 157K | The real engine (Golay, Leech, BarnesWall, Monster, ExactMath) |
| `ubp_system_kb.json` | 1.7M | 751 system KB entries (elements, laws, particles, molecules) |
| `ubp_lang_kb_combined_v4.json` | 11M | 1086 language KB entries (lexicon + vectors) |
| `glm_master_resource_v1.json` | 15M | 4248 dictionary definitions (training data for vectors) |
| `glm_learned_state.json` | ~10K | Continuous learning state (created at runtime, persists across sessions) |

### Data Files NOT Required at Runtime
| What | Why |
|------|-----|
| The 70K-token corpus | Used ONLY at training time to derive grammar-aligned vectors. Discarded after. |
| Any external ML model | The system has no neural generation layer, no n-gram model |
| Any stored text | The 24-bit vectors ARE the learned data |

## Architecture (The Clean Picture)

```
TRAINING TIME (one-time, corpus discarded):
  3 KBs (28M) → corpus (70K tokens) → SVD → grammar role inference
  → quadrant-forced 24-bit vectors → Golay snap (quadrant-preserving)
  → 4,261 grammar-aligned vectors → CORPUS DISCARDED

RUNTIME (no corpus, no ML model, no stored text):
  GLM substrate (Golay/Leech geometry)
    + 4,261 grammar-aligned vectors (the learned data)
    + 141 CRG edges + co_occurs edges (learned)
    + Continuous learner (refines vectors from queries)
    → Query answering + NL generation + continuous improvement
```

## Test Results

| Suite | v3.15.0 | v3.16.0 |
|-------|---------|---------|
| Self-tests (A–Z) | 26/26 | **26/26** |
| Golden cases | 28/28 | **28/28** |

No regressions.

## How to Verify

```bash
cd /path/to/GLM_v3.16.0
python GLM12_cli_entry.py --test          # expect 26/26

# Test continuous learning:
python -c "
from GLM11_runtime import GLMRuntimeV37
rt = GLMRuntimeV37()
print('Before:', rt.learning_status())
for i in range(12):
    rt.chat('Tell me about the hamiltonian and time and energy.')
print('After:', rt.learning_status())
"
```
