# GLM — Geometric Language Machine v3.7.7

A modular, deterministic semantic reasoning engine grounded in the 24-bit Golay/Leech lattice substrate of the Universal Binary Principle (UBP). Runs live in the browser via Pyodide.

**Current state**: 12/12 self-tests pass · Deployed live on [Google AI Studio](https://ai.studio/apps/6d78d479-2a4e-4e34-89b3-4b87b85d5b9a)

---

## Quick Start

### Prerequisites
- Python 3.10+ (requires `int.bit_count()`)
- SymPy (`pip install sympy`)
- `ubp_system_kb.json` and `ubp_lang_kb_combined_v4.json` in the workspace root

### Run Self-Tests
```bash
python GLM12_cli_entry.py --test
```
Expected: `12/12 tests passed`

### Chat Query
```bash
python GLM12_cli_entry.py --chat "What is gcd(54, 24)?"
python GLM12_cli_entry.py --chat "is 5 prime?"
python GLM12_cli_entry.py --chat "Find all positive integers n for which 2^n - 1 is divisible by 7."
```

### Interactive Python
```python
from GLM11_runtime import GLMRuntimeV37
rt = GLMRuntimeV37()
print(rt.chat("what is time?"))        # KB lookup + alias map
print(rt.chat("differentiate x^2"))     # SymPy symbolic
print(rt.chat("is 97 prime?"))          # Primality detection
```

---

## Modular Architecture

The system is split into 14 self-contained Python modules. Each can be tested independently.

| Module | Purpose |
|--------|---------|
| `GLM00_config.py` | Configuration, path setup, KB file verification |
| `GLM01_substrate.py` | BLA, MOG categories, CRG, lexer, KB loading, vocabulary builder, alias map |
| `GLM02_constants.py` | Thresholds, function words, pronouns, tunables |
| `GLM03_crg.py` | Extended CRG (contradictions, auto-expand, lattice linking, query-type) |
| `GLM04_number_vocab.py` | Derived number-word lattice points (55 numbers) |
| `GLM05_idea_evidence.py` | Source-tagged evidence dataclass |
| `GLM06_idea_zone.py` | IdeaZone: decay, ticks, crystallisation, adversarial testing |
| `GLM07_idea_manager.py` | Multi-zone routing, cross-zone synthesis, contradiction pivot |
| `GLM08_idea_meta_graph.py` | Persistence, warm-start, deterministic IDs |
| `GLM09_tools.py` | SymPy: arithmetic, GCD, LCM, factorial, primality, symbolic ops |
| `GLM10_response_composer.py` | Confidence-tagged, multi-zone, synthesis-aware response |
| `GLM11_runtime.py` | GLMRuntimeV37: wires everything, reflexive recall, gap derivation |
| `GLM12_cli_entry.py` | Self-test suite (12 tests A–L), CLI interface |
| `GLM13_deliberative_reasoning.py` | UBP-native arithmetic, 7 problem pattern detectors |

### Test Files
| File | Purpose |
|------|---------|
| `test_full_stack.py` | Integration test: chat + calculus + deliberative reasoning |
| `test_zone.py` | IdeaZone unit tests |
| `test_manager.py` | IdeaManager unit tests |
| `test_meta.py` | Meta-graph unit tests |
| `reset_cache.py` | Clear idea_meta_graph.json and caches |
| `golden_cases.json` | 28-case gold set for benchmark runs |

### Other Files
| Path | Purpose |
|------|---------|
| `dev/` | Legacy monolithic builds (glm_v37_grown.py, glm_v37_unified.py) |
| `doc/` | Academic paper (PDF + LaTeX source) |

---

## How It Works

### The Substrate
Every concept is a 24-bit binary vector — mathematically identical to a hex colour code. Hamming distance uses native CPU XOR + `bit_count()` (~100× faster than Python list iteration). The 24 bits are partitioned into 4 quadrants (Matter, Information, Activation, Potential) with 6 MOG categories each.

### The Pipeline
Each query flows through 15 traceable stages:

```
Import → Config → Boot → Preprocess → Detect compute/symbolic
→ Tokenize → Gap-fill → Filter → Recall KB → Route to zone
→ Update zone → Adversarial test → Deliberative reasoning → Compose → Return
```

### Key Capabilities

**Computation (GLM09_tools.py)**
- GCD/LCM (both `gcd(N,M)` and natural-language "greatest common divisor of N and M")
- Factorial, square root, power, combinations
- Primality testing ("is 5 prime?" → True)
- Symbolic differentiation, integration, solving, simplification (via SymPy)
- Results snap to lattice number-words ("18" → "eighteen")

**Deliberative Reasoning (GLM13)**
When direct detection fails, 7 problem patterns fire:
1. Divisibility sequences → modular period detection
2. GCD/irreducibility proofs → Euclidean algorithm
3. Bounded search → LCM candidate testing
4. Stars and bars → combinatorics formula
5. Subset sum divisibility → brute force (N ≤ 20)
6. Tetrahedron inradius → geometric formula
7. Median inequality → triangle inequality

**Knowledge Base Lookup (GLM01 + GLM10)**
- Alias map (1,935 entries): word → ubp_id → KB entry
- 30+ hardcoded aliases (monster→moonshine, golay→LAW_GOLAY, etc.)
- Auto-extracted from KB names/descriptions
- Example: "what is time?" → "The Law of Relativistic Coherence: Time is the emergent rhythm of substrate toggles..."

**Idea Zones (GLM06 + GLM07)**
- Multi-zone routing: distant concepts spawn separate zones
- Crystallisation: ideas form when coherence ≥ 0.70 (evidence + backbone + NRCI)
- Contradiction detection: boson↔fermion, classical↔quantum, etc.
- Cross-zone synthesis: "both zones relate to symmetry"
- Warm-start: meta-graph persists crystallised ideas across sessions
- Autonomous maturation: tick cycles discover inferred nouns via CRG edges

**Concept Relation Graph (GLM03)**
- 82 curated physics edges across 8 relation types
- 8 contradiction edges (symmetric)
- Auto-expansion: lattice-adjacent nouns get `auto_proposed` edges
- Lattice auto-linking: same-zone nouns within Hamming distance 4 get linked

---

## Self-Tests (A–L)

| Test | Capability | Result |
|------|-----------|--------|
| A | Crystallisation (hamiltonian + time → thesis) | PASS |
| B | Calculation + lattice grounding (gcd → six) | PASS |
| C | Symbolic differentiation (x² → 2x) | PASS |
| D | Symbolic solve (x²−4 → [−2, 2]) | PASS |
| E | Multi-zone routing (2 zones spawned) | PASS |
| F | Contradiction detection (boson ↔ fermion) | PASS |
| G | Autonomous maturation (20 inferred nouns) | PASS |
| H | Warm-start (meta-graph matching) | PASS |
| I | Determinism (byte-identical across runs) | PASS |
| J | CRG auto-expansion (2 auto-proposed edges) | PASS |
| K | Contradiction-driven pivot (zone spawn) | PASS |
| L | Cross-zone synthesis ("both zones relate to symmetry") | PASS |

---

## Live Query Examples

| Query | Response |
|-------|----------|
| `what is time?` | [KB] The Law of Relativistic Coherence: Time is the emergent rhythm of substrate toggles... |
| `what is energy?` | [KB] Computational Mana Coherence: Mana is modeled as the energy flux of local lattice alignment. |
| `how does hydrogen and oxygen become water?` | [Recall] Element: Oxygen, Element: Hydrogen, Molecule: Water |
| `Find all positive integers n for which 2^n - 1 is divisible by 7.` | [Deliberated:divisibility] Period 3 detected. [Conclusion] n divisible by 3 |
| `Find the greatest common divisor of 252 and 198.` | [Computed] gcd(252,198) = 18 → Snapped to 'eighteen' |
| `is 5 prime?` | [Computed] isprime(5) = True. [KB] Law of Prime Resonance: The G24 substrate is tuned to the first Riemann Zeta Zero. |

---

## API Summary (`GLMRuntimeV37`)

```python
from GLM11_runtime import GLMRuntimeV37

rt = GLMRuntimeV37()

# Chat
rt.chat("Tell me about the hamiltonian and time.")
rt.chat("What about symmetry?")           # 'it' → hamiltonian (anaphora)

# Autonomous maturation
rt.mature(5)                               # 5 autonomous ticks
print(rt.idea_state())                     # full multi-zone state

# Computation
rt.chat("What is gcd(54, 24)?")            # → six (grounded)
rt.chat("differentiate x^2 with respect to x")  # → 2*x

# Deliberative reasoning
rt.chat("Find all positive integers n for which 2^n - 1 is divisible by 7.")
# → [Deliberated:divisibility] n divisible by 3

# Cross-zone synthesis
mt = rt.synthesise()
if mt: print(mt.thesis)

# Reset
rt.reset_idea()
```

---

## Required Files

Only 2 KB files needed on disk:

| File | Size | Source |
|------|------|--------|
| `ubp_system_kb.json` | 1.7MB | `system_kb/ubp_system_kb.json` |
| `ubp_lang_kb_combined_v4.json` | 11.0MB | `core/ubp_lang_kb_combined_v4.json` |

No external `.py` substrate files required — all substrate code is absorbed inline in `GLM01_substrate.py`.

---

## Boot Characteristics

- **Boot time**: ~2 seconds (1,374-word vocab + 82 CRG edges + 55 numbers)
- **Per-turn latency**: <50ms for chat; <200ms for deliberative reasoning
- **Determinism**: byte-identical output across runs (verified by self-test I)
- **Memory**: ~12.7MB of KB data loaded into RAM
- **Persistence**: `idea_meta_graph.json` accumulates crystallised ideas across sessions

---

## Version History

| Version | Key Change |
|---------|-----------|
| v3.7.7 | Modular architecture (14 files), alias map KB lookup, priority vocab, full CRG, NRCI fix, thesis filter |
| v3.7.6 | Initial modular split from monolith, Pyodide deployment |
| v3.7.5 | Self-contained substrate (no external .py deps) |
| v3.7.4 | Hex colour optimization, catastrophic regex fix, algorithmic hang prevention |
| v3.7.3 | Deliberative reasoning layer (§13), MathNet 100%, detect fixes |
| v3.7.2 | Legacy absorption: lattice CRG, reflexive recall, gap-derivation, query-type |
| v3.7.1 | User-friendly fallback, chat_with_effort() |
| v3.7 | Cross-zone synthesis, CRG auto-expansion, symbolic tools, contradiction pivot |

---

## Related Links

- **Live App**: [Google AI Studio](https://ai.studio/apps/6d78d479-2a4e-4e34-89b3-4b87b85d5b9a)
- **Core Studio App Repo**: [github.com/DigitalEuan/ubp_core_studio_app](https://github.com/DigitalEuan/ubp_core_studio_app)
- **UBP Repository**: [github.com/DigitalEuan/UBP_Repo](https://github.com/DigitalEuan/UBP_Repo)
- **Academic Paper**: `doc/Geometric_Language_Machine.pdf`

---

## Author

E R A Craig, New Zealand

## License

This work is part of the Universal Binary Principle (UBP) research project. All UBP repositories are public access.
