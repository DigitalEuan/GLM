# GLM v3.16.0 — Geometric Language Machine

## Quick Start

```bash
# 1. Place these files alongside the GLM modules (you already have them):
#    - ubp_unified_v5.py       (the real engine: Golay, Leech, BarnesWall, Monster)
#    - ubp_system_kb.json      (751 system KB entries)
#    - ubp_lang_kb_combined_v4.json (1086 language KB entries)
#    - glm_master_resource_v1.json  (4248 dictionary definitions — training data for vectors)

# 2. Run self-tests:
python GLM12_cli_entry.py --test          # expect 26/26

# 3. Chat:
python GLM12_cli_entry.py --chat "What is gcd(54, 24)?"
python GLM12_cli_entry.py --chat "What is the weyl anomaly?"
```

## What This Package Contains

This zip contains the **31 GLM Python modules** (7,454 lines) + golden_cases.json + test scripts developed across sessions v3.7.7 → v3.16.0.

### Files Included in This Zip

| File | Lines | Purpose |
|------|-------|---------|
| `GLM00_config.py` | 56 | Configuration, path setup, KB file verification |
| `GLM01_substrate.py` | 700 | Substrate: real Golay/Leech engines, CRG, vocabulary builder |
| `GLM02_constants.py` | 100 | Thresholds, function words, pronouns, tunables |
| `GLM03_crg.py` | 180 | Extended CRG (contradictions, auto-expand, lattice linking) |
| `GLM04_number_vocab.py` | 154 | Number-word lattice points (55 numbers) |
| `GLM05_idea_evidence.py` | 41 | Source-tagged evidence dataclass |
| `GLM06_idea_zone.py` | 222 | IdeaZone: decay, ticks, crystallisation, adversarial testing |
| `GLM07_idea_manager.py` | 211 | Multi-zone routing, cross-zone synthesis, contradiction pivot |
| `GLM08_idea_meta_graph.py` | 113 | Persistence, warm-start, deterministic IDs |
| `GLM09_tools.py` | 680 | SymPy tools: arithmetic, GCD, LCM, integrate, ODE, linear algebra |
| `GLM10_response_composer.py` | 200 | Confidence-tagged, multi-zone, synthesis-aware response |
| `GLM11_runtime.py` | 560 | GLMRuntimeV37: wires everything, chat/chat_prose/generate |
| `GLM12_cli_entry.py` | 330 | Self-test suite (26 tests A–Z), CLI interface |
| `GLM13_deliberative_reasoning.py` | 280 | 13 problem pattern detectors (GCD proof, stars & bars, etc.) |
| `GLM14_lexer.py` | 290 | Multi-token lexer with LaTeX scrubbing, lemmatisation |
| `GLM15_physics_pack.py` | 360 | 197-term physics vocabulary pack with definitions |
| `GLM16_master_resource.py` | 230 | Loads 4248 dictionary entries + 70 relations + 55 spatial nodes |
| `GLM17_semantic_frames.py` | 270 | Frame-based NL generation (legacy, superseded by GLM22) |
| `GLM18_hex_colour.py` | 230 | Hex colour signatures — every concept IS a #RRGGBB colour |
| `GLM19_prose_composer.py` | 290 | Fluent NL paragraphs (~3-4x longer than terse output) |
| `GLM20_svd_vocab.py` | 180 | SVD+Golay-snapped distributional vectors |
| `GLM21_generator.py` | 250 | Zone-centroid-state generation loop (addresses pigeonhole cycling) |
| `GLM22_ontological_grammar.py` | 330 | Computed grammar: S→V→O from vector geometry (no templates) |
| `GLM23_grammar_vectors.py` | 380 | Grammar-aligned vectors: quadrant = grammatical role |
| `GLM24_continuous_learner.py` | 280 | Continuous learning: vectors refine from query co-occurrence |
| `golden_cases.json` | 280 | 28-case gold-set benchmark |
| `reset_cache.py` | 25 | Clear idea_meta_graph.json and caches |
| `test_full_stack.py` | 17 | Integration test |
| `test_manager.py` | 27 | IdeaManager unit tests |
| `test_meta.py` | 29 | Meta-graph unit tests |
| `test_zone.py` | 47 | IdeaZone unit tests |

### Files NOT Included (You Already Have Them)

| File | Size | Source | Why Excluded |
|------|------|--------|--------------|
| `ubp_unified_v5.py` | 157K | `core_studio_v4.0/core/` | UNCHANGED from repo — verified byte-identical |
| `ubp_system_kb.json` | 1.7M | `core_studio_v4.0/system_kb/` | UNCHANGED from repo — verified byte-identical |
| `ubp_lang_kb_combined_v4.json` | 11M | `core_studio_v4.0/core/` | UNCHANGED from repo — verified byte-identical |
| `glm_master_resource_v1.json` | 15M | `core_studio_v4.0/GLM/` | UNCHANGED from repo — already present |

**Total excluded: ~28MB** (you already have these files)

### Files Created at Runtime (Not in Zip)

| File | When Created | Purpose |
|------|--------------|---------|
| `glm_learned_state.json` | Continuous learner saves every 5 queries | Persistent learning state (co-occurrence, learned words, learned edges) |
| `idea_meta_graph.json` | When ideas crystallise | Long-term memory of crystallised ideas |
| `v37_test_results.json` | After `--test` runs | Self-test results |

## Architecture (v3.16.0)

```
TRAINING TIME (one-time, corpus discarded):
  3 KBs (28M) → corpus (70K tokens) → SVD → grammar role inference
  → quadrant-forced 24-bit vectors → Golay snap (quadrant-preserving)
  → 4,261 grammar-aligned vectors → CORPUS DISCARDED

RUNTIME (no corpus, no ML model, no stored text):
  GLM substrate (Golay/Leech geometry)
    + 4,261 grammar-aligned vectors (the learned data)
    + 141 CRG edges + co_occurs edges (learned at runtime)
    + Continuous learner (refines vectors from queries)
    → Query answering + NL generation + continuous improvement
```

## API Summary

```python
from GLM11_runtime import GLMRuntimeV37

rt = GLMRuntimeV37()

# Query answering
rt.chat("What is gcd(54, 24)?")                    # terse bracket-tag output
rt.chat_prose("What is the weyl anomaly?")         # fluent NL paragraph

# Generation (computed, not templated)
rt.generate("hamiltonian")                          # word-chain generation
rt.generate_grammatical("hamiltonian")              # computed S→V→O
rt.compute_sentence("hamiltonian", "time")          # inspect geometric computation

# Continuous learning
rt.learning_status()                                # queries processed, vectors refined

# Substrate diagnostics
rt.engine_status()                                  # Golay syndrome table, codewords, Y constant
rt.master_status()                                  # master resource loaded?
rt.idea_colour()                                    # hex colour signature of current zone
rt.word_colour("hamiltonian")                       # hex colour of a word
rt.snap_query("test query")                         # snap query to Golay codeword

# State
rt.idea_state()                                     # full zone + meta-graph + colour + master status
rt.mature(5)                                        # 5 autonomous ticks
rt.synthesise()                                     # cross-zone synthesis
rt.reset_idea()                                     # reset zone state
```

## Test Results

| Suite | Result |
|-------|--------|
| Self-tests (A–Z) | **26/26** |
| Golden cases | **28/28** |

## Stub/Simplification Audit (v3.16.0)

### ✅ Real (No Stubs)
- **Golay(24,12) error correction** — 2325-entry syndrome table, corrects 1/2/3-bit errors (verified test Y)
- **Leech NRCI** — exact Y constant from π, NRCI=0.681 for weight-12 (verified test Z, stub would give 1.0)
- **SVD distributional vectors** — PPMI + truncated SVD on 70K-token corpus
- **Grammar-aligned vectors** — 100% quadrant alignment, quadrant-preserving Golay snap
- **CRG** — 141 typed edges + co_occurs edges learned at runtime
- **Gap computation** — AND-intersection produces VERB-dominant vectors (31.6% of edges)
- **Ontological grammar** — computes S→V→O from vector geometry, no templates
- **Continuous learning** — vectors refine from query co-occurrence, geometric (not gradient)

### ⚠️ Simplifications (Honest, Not Stubs)
- **Grammatical role inference** — suffix heuristics + definition patterns (~70% accuracy). Training-time tool, not runtime dependency.
- **Continuous learning** — geometric refinement (co-occurrence averaging + Golay snap), not gradient descent. BY DESIGN — no neural model.

### Legacy (Not Used at Runtime)
- Stub Golay/Leech engines in GLM01 — only activate if ubp_unified_v5.py is missing (never happens)
- GLM17 semantic frames — superseded by GLM22 ontological grammar

## Version History

| Version | Key Change |
|---------|-----------|
| v3.16.0 | Continuous learning loop (GLM24). Full stub audit. Clean manifest. |
| v3.15.0 | Grammar-aligned vectors (GLM23): quadrant = grammatical role, 100% alignment |
| v3.14.0 | Ontological grammar (GLM22): computed S→V→O from gap geometry, no templates |
| v3.13.0 | Generation loop (GLM21): zone-centroid state, addresses pigeonhole cycling |
| v3.12.0 | SVD+Golay-snapped distributional vectors (GLM20) |
| v3.11.0 | Prose composer (GLM19), Experiment L (engineered features), G-followup |
| v3.10.0 | Real ubp_unified_v5.py engine integration (replaced stub) |
| v3.9.0 | Master resource integration (GLM16), semantic frames (GLM17), hex colours (GLM18) |
| v3.8.0 | Multi-token lexer (GLM14), physics vocab pack (GLM15), 141 CRG edges |
| v3.7.7 | Modular architecture (14 files), alias map KB lookup, priority vocab |
