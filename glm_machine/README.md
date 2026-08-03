# GLM README — Geometric Language Machine

**Version:** 4.0.0  (3 August 2026) 
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand  
**Parent:** `../README.md`

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure

- A deterministic, geometry-grounded language engine built on the 24-bit Golay/Leech substrate. Every word has a 24-bit Golay codeword. Every relationship is a labeled edge in a knowledge graph. Every response is structured as Three Column Thinking — language, math, and code aligned at each step.

This is NOT an LLM. It has no neural weights, no training on internet-scale data, no sampling. It's a different kind of intelligence — based on error-correcting codes and geometric algebra.

---

## Quick Start

```python
from GLM import GLM

rt = GLM()

# Ask a question
print(rt.chat("What is gravity?"))

# See all three columns (language + math + script)
print(rt.chat_verbose("What is a quark?"))

# Learn from text
rt.learn("Photosynthesis is the process by which plants convert light into energy.")
print(rt.chat("What is photosynthesis?"))

# Multi-turn conversation
print(rt.chat("What is the hamiltonian?"))
print(rt.chat("How does it relate to symmetry?"))  # context-aware
```

### CLI

```bash
python3 GLM.py --chat "What is gravity?"
python3 GLM.py --verbose "What is a quark?"
python3 GLM.py --learn "Photosynthesis is the process by which plants convert light into energy."
python3 GLM.py --interactive
python3 GLM.py --status
```

---

## How It Works

### The Substrate

Every word in the GLM vocabulary has a 24-bit vector derived from SVD co-occurrence statistics, snapped to the nearest Golay codeword. The Golay code is a perfect error-correcting code — it can correct up to 3 errors in 24 bits. This means:

- **Hamming distance = semantic distance** (words close in Hamming space are semantically related)
- **NRCI = stability** (words at stable lattice positions have high NRCI)
- **Quadrant weights = grammatical role** (Reality→NOUN, Information→ADJECTIVE, Activation→VERB, Potential→OPERATOR)
- **HexColour** every concept in the Geometric Language Machine is a 24-bit vector — which IS an RGB colour

### The Knowledge Graph (CRG)

The Concept Relation Graph has 930+ curated semantic edges connecting physics, math, and UBP concepts. Each edge is a labeled relationship like `("hamiltonian", "generates", "time")` or `("entropy", "measures", "dimension")`.

### Three Column Thinking

Every response is structured as aligned thought steps:

```
Step 1: DEFINITION
  Language: Gravity is a fundamental force arising from spacetime curvature.
  Math:     NRCI(gravity) = 0.6814, HW = 12
  Script:   entry = vocab['gravity']; nrci = float(entry.nrci)

Step 2: RELATIONSHIPS
  Language: Gravity curves spacetime. Gravity attracts mass.
  Math:     gravity --curves--> spacetime ∧ gravity --attracts--> mass
  Script:   edges = crg.out.get('gravity', [])

Step 3: GEOMETRY
  Language: Gravity occupies the Potential layer with 4 bits.
  Math:     v(gravity) = 0x4C68BD, Q = [3,2,2,5]
  Script:   v = vocab['gravity'].vector

Step 4: IMPLICATIONS
  Language: Gravity curves spacetime. Spacetime contains event.
  Math:     chain: gravity → spacetime → event

Step 5: RESOLUTION
  All columns align: gravity is well-defined and coherent.
```

The `chat()` method shows only the Language column. The `chat_verbose()` method shows all three.

### On-the-Fly Learning

Feed the GLM any text and it grows:

```python
rt.learn("The Standard Model describes three of the four known fundamental forces.")
# → Learns vocabulary, definitions, CRG edges, and co-occurrence patterns
```

Every text is training data. Every conversation makes it smarter.

### Geometric Realignment

The GLM's knowledge graph is a physical system. Concepts have positions in 3D space (quadrant weights). Edges are springs connecting related concepts. Coherence is physical stability.

At boot, the GLM runs geometric realignment — moving semantically close concepts to be geometrically close in the substrate. This improves coherence.

---

## Current Architecture

* **NOTE:** this repository is part of developing this GLM system, the current work generating 'arc_agi_(version_number)' attempts is building on the system in this 'glm_machine/' folder.

* The current ARC AGI method uses:
| File | Purpose | Lines |
|---|---|---|
| `reasoning_loop.py` | Complete cognitive cycle | ~600 |
| `substrate_mind.py` | Settlement dynamics | ~700 |
| `conditional_lobe.py` | Conditional reasoning | ~500 |
| `semantic_layer.py` | Lingo descriptions | ~400 |
| `geometric_perception.py` | Spatial arithmetic integration | ~400 |
| `ubp_calibration_engine.py` | Lightspeed calibration | ~500 |
| `substrate_test.py` | Synthetic validation | ~200 |
| `consolidated_mind.py` | All styles + toolkit | ~1300 |

The older files (`mog_mind.py`, `mog_attention.py`, `mog_transformer.py`, `v065_ubp_glm.py`) are superseded but kept for reference.

```
GLM.py
├── ThreeColumnEngine    — Three Column Thinking (language + math + script)
├── TextMiner            — On-the-fly learning from text
├── ContextAccumulator   — Multi-turn conversation tracking
├── GeometricRealigner   — Makes geometry match semantics
├── GLM                  — Main class (orchestrates everything)
│
├── Dependencies:
│   ├── GLM01_substrate.py    — Golay/Leech engine, vocabulary, BLA
│   ├── GLM02_constants.py    — Function words, edge labels
│   ├── GLM03_crg.py          — Concept Relation Graph
│   ├── GLM04_number_vocab.py — Number vocabulary
│   ├── GLM07_idea_manager.py — Idea zone management
│   ├── GLM08_idea_meta_graph.py — Long-term idea graph
│   ├── GLM09_tools.py        — Math/symbolic computation
│   ├── GLM14_lexer.py        — Multi-word tokenization
│   ├── GLM38_corpus_vocab.py — SVD vocabulary from corpus
│   ├── GLM_CRG_EXPANDED.py   — 597 curated semantic edges
│   ├── ubp_unified_v5.py     — Core UBP engine (Golay/Leech)
│   └── corpus.txt            — 71K-word physics corpus
│
└── Data:
    ├── glm_unified_resource.json — Unified resource (15MB)
    └── golden_cases.json         — Golden test cases
```

---

## File Inventory

### Core Files (keep)

| File | Description |
|------|-------------|
| `GLM.py` | **Main entry point** — polished runtime with all features |
| `GLM00_config.py` | Paths and configuration |
| `GLM01_substrate.py` | Golay/Leech engine, vocabulary, BLA |
| `GLM02_constants.py` | Function words, edge labels |
| `GLM03_crg.py` | Concept Relation Graph |
| `GLM04_number_vocab.py` | Number vocabulary |
| `GLM05_idea_evidence.py` | Evidence dataclass |
| `GLM06_idea_zone.py` | Idea zone |
| `GLM07_idea_manager.py` | Idea zone management |
| `GLM08_idea_meta_graph.py` | Long-term idea graph |
| `GLM09_tools.py` | Math/symbolic computation |
| `GLM10_response_composer.py` | Terse response composer |
| `GLM11_runtime.py` | Original runtime (dependency) |
| `GLM13_deliberative_reasoning.py` | Pattern-based reasoning |
| `GLM14_lexer.py` | Multi-word tokenization |
| `GLM15_physics_pack.py` | Physics vocabulary |
| `GLM16_master_resource.py` | Resource loading |
| `GLM17_semantic_frames.py` | Backbone verbalization |
| `GLM18_hex_colour.py` | Visualization |
| `GLM19_prose_composer.py` | Prose composer |
| `GLM20_svd_vocab.py` | SVD vocabulary builder |
| `GLM21_generator.py` | Word-chain generator |
| `GLM22_ontological_grammar.py` | Computed SVO grammar |
| `GLM23_grammar_vectors.py` | Grammar vector builder |
| `GLM24_continuous_learner.py` | Continuous learning |
| `GLM25_native_alu.py` | Native ALU |
| `GLM26_crg_alu.py` | CRG traversal ALU |
| `GLM27_crg_expander.py` | CRG auto-expansion |
| `GLM28_native_poly.py` | Polynomial operations |
| `GLM29_answer_extractor.py` | Answer extraction |
| `GLM30_domain_filter.py` | Domain filtering |
| `GLM31_verification.py` | Verification |
| `GLM32_mode_algebra.py` | Kracht mode algebra |
| `GLM33_considered_response.py` | Multi-paragraph composer |
| `GLM34_simplicial_crg.py` | Simplicial CRG |
| `GLM35_paragraph_composer.py` | Paragraph composer |
| `GLM38_corpus_vocab.py` | SVD vocabulary from corpus |
| `GLM_CRG_EXPANDED.py` | 597 curated semantic edges |
| `refined_nrci.py` | 5-shell sign-sensitive NRCI |
| `ubp_unified_v5.py` | Core UBP engine |
| `ubp_tgic_engine.py` | TGIC engine |
| `ubp_genesis_boot.py` | Genesis boot |
| `corpus.txt` | 71K-word physics corpus |

### Data Files (keep)

| File | Description |
|------|-------------|
| `glm_unified_resource.json` | Unified resource (15MB) |
| `golden_cases.json` | Golden test cases |
| `research_notes.txt` | Research notes |

### Archive (not needed for operation)

| Directory | Contents |
|-----------|----------|
| `archive/experimental/` | Intermediate runtimes (GLM36-52) |
| `archive/intermediate_reports/` | Development reports |
| `archive/intermediate_runtimes/` | Intermediate CLI and tests |

---

## Benchmark Results

```
definition_quality        [██████████████████░░] 0.92
relation_quality          [███████████████░░░░░] 0.75
math_accuracy             [████████████████████] 1.00
coherence                 [████████████░░░░░░░░] 0.64
length                    [████████████████████] 1.00
learning                  [████████████████████] 1.00
context                   [████████████████████] 1.00
response_time             [███████████████████░] 0.99
OVERALL:                  [███████████████░░░░░] 0.79
```

---

## What Makes This Novel

1. **Deterministic** — Same input always produces same output. No sampling, no temperature.
2. **Geometry-grounded** — Every word has a 24-bit Golay codeword. Hamming distance = semantic distance.
3. **Three Column Thinking** — Language, math, and code must align at every step.
4. **Learns in real-time** — Feed it text and it grows vocabulary, definitions, edges.
5. **Physical knowledge graph** — Concepts have positions, edges are springs, coherence is stability.
6. **Real math** — SymPy evaluation, native ALU, Golay error correction.

---

## Dependencies

- Python ≥ 3.10 
- NumPy (for SVD) - not for computation or calculation, only to be used where absolutely necessary 
- SymPy (for symbolic math, optional) - not for computation or calculation, only to be used for validation or where absolutely necessary 
- No pip installs required for core functionality 

---

## License

Part of the UBP research initiative by Euan R. A. Craig. Experimental — please verify results independently.

---

## Advanced Features (v4.0)

### 3D Visualization
```python
rt.visualize("graph3d.html")
# → Opens an interactive 3D view of the knowledge graph
# → 2,550 concepts, 702 edges
# → Drag to rotate, scroll to zoom, hover for details
# → Color-coded by ontological layer (Reality/Information/Activation/Potential)
```

### Geometric Realignment
```python
rt.realign_advanced(iterations=5)
# → Pulls semantically close concepts to be geometrically close
# → Energy decreases as the system settles
# → Respects Golay codeword constraints
```

### Time-Based Dynamics
```python
rt.time_drift(steps=5)
# → Concepts drift toward their semantic neighbors
# → Like atoms settling into a crystal lattice
# → Snaps to Golay codewords after each drift step
```

### Expanded Corpus
- **148K words** from Einstein, Russell, Poincaré, and physics texts
- **989 CRG edges** (250 new curated edges)
- **2,550 vocabulary entries**

### Knowledge Graph as Physics
The GLM's knowledge graph is a physical system:
- **Concepts** have positions in 3D space (quadrant weights)
- **Edges** are springs connecting related concepts
- **Coherence** is physical stability
- **Realignment** is energy minimization
- **Time drift** is atoms settling into a lattice

---

## What's New Since v4.0

| Feature | Before | After |
|---------|--------|-------|
| CRG edges | 930 | **989** (+59) |
| Corpus size | 71K words | **148K words** (2×) |
| 3D visualization | ❌ | **Interactive HTML** |
| Force-directed realignment | ❌ | **Pull-only, Golay-safe** |
| Time-based dynamics | ❌ | **Drift toward neighbors** |
| Coherence | 0.64 | **0.673** (improving) |

---

## Sandbox & Persistence (v4.1)

### Virtual Thinking Environment
The GLM has a sandbox where it can execute code safely:

```python
result = rt.sandbox_think("""
v = vocab['gravity'].vector
q = [sum(v[0:6]), sum(v[6:12]), sum(v[12:18]), sum(v[18:24])]
observe('gravity_quadrants', str(q))
print(f'Quadrants: {q}')
""")
```

**Loop prevention:**
- Max 20 iterations per thought
- Max 50 operations per query
- 5-second timeout per operation
- Recursion depth limit: 5

### Persistent Memory
Everything persists across sessions:

```python
rt.sandbox_observe("key", "value")  # Store
rt.sandbox_recall("key")            # Recall
rt.sandbox_recall()                  # Get all context
```

**What persists:**
- Learned vocabulary (words, definitions, vectors)
- Learned CRG edges
- Observations and insights
- Session history
- Growth log

### Growth Tracking
The GLM tracks its own growth:

```python
status = rt.status()
# → {vocab_size, crg_edges, sandbox: {observations, thoughts}, persistence: {learned_vocab, ...}}
```

---

## UBP Tools Available

The GLM has access to UBP core scripts as tools:

| Tool | Source | What It Does |
|------|--------|-------------|
| GOLAY_SNAP | ubp_unified_v5.py | Snap to nearest Golay codeword |
| NRCI_COMPUTE | ubp_unified_v5.py | Compute NRCI stability |
| HAMMING_DIST | ubp_unified_v5.py | Distance between vectors |
| CRG_WALK | GLM03_crg.py | Walk the knowledge graph |
| MATH_EVAL | GLM09_tools.py | Evaluate expressions |
| VECTOR_ANALYZE | geometry.py | Full geometric analysis |
| PRIMALITY | GLM09_tools.py | Primality test |
| GRAY_CODE | hash_all_1.py | Gray code conversion |
| SUBSTRATE_MAP | ubp_mog_mapper.py | Map to ontological layer |
| GOLAY_ANALYZE | Sandbox | Deep Golay analysis |
| CRG_NEIGHBORS | Sandbox | Find all neighbors |
| SEMANTIC_DISTANCE | Sandbox | Distance between concepts |
| LAYER_ANALYSIS | Sandbox | Layer distribution |
| KNOWLEDGE_GAP | Sandbox | Find sparse connections |
