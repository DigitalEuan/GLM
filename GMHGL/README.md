# 'GMHGL/' - (Grey-MOG-Hexacode-Golay-Leech) — The Verified UBP Substrate Engine

**Version:** v5.4.2 (7 August 2026)  
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand  
**Parent:** `../README.md`

> **⚠️ UPDATE THIS README:** If changes are made in this folder, or if systems in sub-folders need rewiring within the repository and affect this README file's structure.

---

## The UBP Substrate

The UBP substrate consists of five core components:
1. **Golay [24,12,8]** — 4,096 codewords, error correction, distance = *The Seed, The Engine, The Measure*
2. **MOG** — 4×6 grid projecting 24D to 2D = *The Observer's Window* (2D projection of 24D)
3. **Gray Code** — meaning to binary, preserving topology = *The Translator* (Words/Numbers into Binary)
4. **Hexacode** — grammar ensuring coherence = *The Language* (Syntax and Grammar)
5. **Leech Lattice** — geometry, mass, 196,560 minimal vectors = *The Discrete Physical Structure*

## Role in the System

```text
GMHGL (this folder)
 → provides engine to everything - all other scripts call from this folder rather than making copies.
```

---

## What's Here

| File | Purpose | Used By |
|------|---------|---------|
| `ubp_unified_v5.py` | Core engine (4,146 lines) | `glm_machine`, `data_object`, `arc_agi_16` |
| `ubp_checkpoint_v5.4.1.md` | Full verification docs | — |
| All other UBP system scripts & data | Functions within the UBP operating system | Anything using this GMHGL system *(except `../long_term_memory/ubp_system_kb.json`)* |

### Important System Scripts

#### `spatial_arithmetic.py`
```text
Signed integers are represented by regular unit-edge polygons embedded in 3-D.
The vertex count stores magnitude and sign. The empty space between adjacent
polygons stores an operator. An observer reconstructs the connected cycles,
measures their geometry, decodes the expression, and evaluates it with exact
`fractions.Fraction` arithmetic.
```

#### `tgic_v3.py`
```text
1. A top-down Golay-code filter. Codewords, syndromes, octads and correction
   all use `ubp_unified_v5.GolayCodeEngine` so there is one code convention.
2. A bottom-up, finite-state RuneCube simulator adapted from
   `ubp_tgic_engine.py`. It provides the older axis operations, internal
   interaction score, neighbourhood pressure and relational attraction without
   relying on the unavailable `ubp_core_v5_3_merged` module.
```

#### `refined_nrci.py`
Primary UBP measuring metric:
* **1.0000 (OnBit):** Pure Mathematical/Noumenal Truth.
* **0.98–1.00 (Capture Zone):** Within 3-bit radius; substrate exerts Restorative Pressure; universe "Snaps" to coherent state.
* **0.7000 – 0.9800 (Stable):** Manifested Physical Matter (the "Conscious Zone").
* **0.60–0.70 (Subliminal / Zombie State):** High SOC Energy but fails the `0.70` `CONSCIOUS_THRESHOLD`. Stays in the Potential buffer; cannot transfer to the Reality register. (Top Quark example.)
* **0.4200 (Noise Floor):** Limit of random informational noise; anomaly detection threshold.
* **~0.005 (Redline, Gap 7):** Super-heavy elements ($Z > 118$); one bit from Deep Hole.
* **0.0000 (Deep Hole):** Geometric collapse; the object cannot exist.

**Islands of Stability:** The system identifies local NRCI peaks where stability "bounces" upward despite high complexity. Applying a `RESONATE` pulse to super-heavy isotopes like `U114_N170` reduces their Gap from 7 to 3, increasing stability into a peaked state (see §14.2).

#### `ldp_nrci.py` + `ldp_complete_mapping.md`
The Dimensional Ladder:

| Dim | Code | d/n | DHC | AND Closure | Phase |
|-----|------|-----|-----|-------------|-------|
| 4D  | [4,2,2] | 0.50 | TRUE | 1.000 | Below transition |
| 8D  | [8,4,4] | 0.50 | TRUE | 0.077 | Below transition |
| 12D | [12,6,6]| 0.50 | UNKNOWN | 0.008 | At transition |
| 14D | — | — | — | 0.247 | **PHASE TRANSITION** |
| 24D | [24,12,8]| 0.33 | FALSE | 0.038 | Above transition |

---

## Layered Architecture Summary

### Layer 1 — Mathematical Substrate

| File | Role |
|:---|:---|
| **`ubp_unified_v5.py`** | The core engine of the UBP. |
| **`ubp_eml_alu_sovereign.py`** | Derives the Triadic Monad and exact particle masses purely from the transcendental projection $\text{eml}(x,y) = e^x - \ln(y)$. Includes `Dual` (automatic differentiation) and `GrandUnifiedEmlALU`. |
| **`ubp_tgic_v3.py`** | Golay filter plus optional 3-6-9 RuneCube simulator. |
| **`ubp_tgic_engine.py`** | Implements 3-6-9 Genesis Logic (Axis Orthogonality, Face Coherence, Neighborhood Limits), RuneCube AND/XOR/OR ops, and Relational Gravity. |
| **`ubp_genesis_boot.py`** | Seeds 24 base geometries + 26 sporadic groups, slides unstable objects along the Gray manifold until they resonate at a stable Λ₂₄ coordinate, exports `genesis_atlas.json`. |
| **`geometry.py`** | Condensed geometry module. `HexDictionaryV4Exact` (symbolic-hash memory), `MathAtlasConstants`, `ConstructionPath`, `MathObjectV4`, `ExactRationalEncoder`. Self-contained subset of `math_atlas.py`. |
| **`math_atlas.py`** | The Voxel Engine. Treats `math` fields as instructions for a 3-D Voxel Walker using the four primitives D / X / N / J. |
| **`physics.py`** | Coherence, holographic NRCI, and observer cost. |
| **`ubp_electromagnetic_analog_compute_engine.py`** | Comprehensive validation that UBP arithmetic can be performed via orthogonal electromagnetic field interactions. |

### Layer 2 — Semantic & Phenomenological Senses (used before GLM)

| File | Role |
|:---|:---|
| **`ubp_semantic_engine.py`** | The system's memory and dictionary. Uses weighted Cosine Resonance to map natural language queries to 24-bit vectors. Trigrams carry 9× the weight of unigrams. Outputs Lexical Gap traces. |
| **`ubp_semantic_sovereign.py`** | The cognitive bridge. `SovereignSemanticAuditor` performs Lattice-Snaps to verify if a concept is "Phase-Locked" (NRCI ≥ 0.70) in reality; `TripleDeltaProjector` generates deterministic symbolic formulas from physical signatures. |
| **`ubp_phenomenology.py`** | The external data bridge. `PhenomenologyEngine` (Scanner): translates real-world data (RGB, sensors, text) into stable 24-bit vectors. `NoumenalProjector`: inverse direction — translates Shadow Intent into the matter/info required to sustain it. |
| **`ubp_observer_dynamics.py`** | Observer Dynamics Engine. Calculates SOC Energy against the 1 THz Wall of Reality, splits ontology layers, and performs the **0.70 Conscious READ gate**. |
| **`ubp_internal_dialogue_semantic_description.py`** | Deep semantic mirror. `find_word_for_concept(law_vec)` searches the Language KB for the closest semantic match to a physical vector. `deepest_internal_dialogue(query, max_depth, gap_threshold)` recursively probes the lattice and emits the full reasoning trace including Lexical Gaps. |
| **`auto_trigger.py`** | Real-time interface between the chat/user and the system's memory. Loads the v9.9 columnar KB, performs reflexive recall, and synthesizes a three-part context (Primary Resonance + Reasoning Chain + Synthesis Hint) for injection into the LLM prompt. |

### Layer 3 — Translation & Execution (used before GLM)

| File | Role |
|:---|:---|
| **`ubp_python_engine.py`** | Maps Python keywords to 24-bit physical laws (`LAW_PY_DEF`, etc.) to synthesize code based on geometric stability. |
| **`ubp_sovereign_evolver.py`** | Parses the AST of standard Python scripts, strips floating-point dependencies (`math.sin`, etc.), and rewires them to the native `GrandUnifiedEmlALU`. |
| **`ubp_py_runtime.py`** | `CortexAtom` is the fundamental unit (label, value as `Fraction`, vector 24-bit, NRCI, tax, tilt, tier, category, hierarchy, parent_lineage). `MOGOntology.calculate_health` implements LAW_SUBSTRATE_005 Tetradic MOG partition health. `UBPPyVM.to_scene_3d()` projects 24-bit atoms into 3-D space for visualization. |
| **`ubp_py_lang.py`** | The UBP-Py language parser (v2.0). Translates `.ubp` text commands into VM operations. |
| **`ubppy.py`** | CLI entry point (v2.3). `python ubppy.py --program myprog.ubp --trace trace.json --scene scene.json`. |

### Layer 4 — Cognitive Orchestration (used before GLM)

| File | Role |
|:---|:---|
| **`ubp_brain_consolidated.py`** | Deterministic recall engine. Enforces Domain Gating (prevents `OP_LIGHT` from intercepting "Speed of Light"), Identity Lock (prioritizes `PARTICLE_`/`ELEM_` prefixes), N-Gram Weighting (trigrams 9×), and Robust Loader (auto-hydrates v9.9 columnar KB). |
| **`ubp_swarm_tct_v25.py`** | Multi-agent loop that extracts mathematical kernels, solves them via the Oracle Bridge, audits their physical reality, and utilizes **Lexical Genesis** to mathematically invent new formulas for unresolved concepts. |
| **`ubp_v28_oracle.py`** | The logical calculator. Implements the **Two-Track Parallel Solve** (UBP Native via `TopologicalALU` + `NativeMathEngine` + `UBPPolynomial`, vs. SymPy Oracle). Contains `MathNetKernelExtractor` to strip English fluff from Olympiad problems, plus a battery of specialized MathNet kernel solvers. |
| **`ubp_moe_cortex_v2.py`** | Mixture-of-Experts router. Selects which expert (Brain / Swarm / Oracle / Semantic Engine) to invoke for a given query. |
| **`ubp_integrated_engine_v1.py`** | Integrated Engine v3.4 — Composite Scene Edition. High-level executive layer. Bridges the Semantic Brain, the 24-D Micro-Core, and the 256-D Macro-Bulk. `analyze_query` performs a Penta-Audit (semantic, geometric, particle-physics, MOG, thermo). `hex_to_bw256(hex_str)` maps SHA-256 fingerprints directly into 256-D Barnes-Wall coordinates. `VitEyesEngine` is the Visual Cortex. |

### Support Tier — Visualization, Bridges, KB Tooling

| File | Role |
|:---|:---|
| **`ubp_viz.py`** | Visual Bridge v2.0. Converts Python geometric data into `scene_3d.json` for the React/Three.js frontend. Handles Fraction-to-Float conversion. Provides `point`, `sphere`, `line` helpers and `save_scene_3d(data)`. |
| **`ubp_rgdl.py`** | Resonance Geometry Definition Language v5.1. Maps 3-D voxel coordinates (x,y,z) to 24-bit vectors, snaps them to the Leech Lattice, and colors them by true NRCI stability (Cyan for stable, Magenta/Blue for unstable). Generates voxelized spheres (The Monad) and cubes (The Matrix). |
| **`viz_loader.py`** | Loads and renders specific JSON files from the Workspace. |
| **`viz_spatial_simplification.py`** | Simplifies complex 3-D manifolds into stable geometric Faces with the Origin to prevent visual clutter. Reveals underlying Pyramid structures (stable triadic relationships). |
| **`ubp_kb_architect.py`** | KB Architect v2.2 (SOP_002 + Gray Code). Factory for new KB entries. `create_entry(ubp_id, lexicon_name, definition, math_dna, hierarchy)` returns a fully hardened entry. Includes the 24 MOG categories list. |

---

## What `ubp_unified_v5.py` Provides

### 0. Standard Library Only
This module operates using **STD-LIB ONLY**.

### 1. Exact Math (`class ExactMath`)
Float-free integer / rational mathematics. Provides what `math` provided, but with deterministic exactness:
* `isqrt(n)`: integer floor sqrt (Newton-Raphson)
* `ilog(n, base)`: integer floor log
* `iceil_div(a, b)`: integer ceiling division
* `icomb(n, k)`: binomial coefficient
* `ifact(n)`: factorial
* `igcd(a, b)`: gcd (Euclidean)
* `sqrt_frac(f, prec=30)`: Fraction sqrt to ~prec decimal digits
* `newton_sqrt(f, iters)`: raw Newton iteration on Fraction

### 1.1. Exact Root (`class ExactRoot`)
Exact symbolic representation of `coef · √radicand` with `Fraction` internals. Useful for physics expressions that contain irrational closed-form roots (e.g. γ = 1/√(1−β²), v_esc = √(2GM/R)).
* Operations: multiply/divide by `Fraction` or `ExactRoot`
* `to_fraction(prec)`: approximate to a `Fraction`
* `float()`: convert to float ONLY on the display boundary

### 1.5. Gray Map Isometry (Z_4 ↔ F_2^2)
The isometric bridge between two metric worlds. Walk around the 4-cycle `(0,0) → (1,0) → (1,1) → (0,1) → (0,0)` in the Hamming cube: each step changes exactly one bit. So Hamming distance in F_2^2 equals Lee distance in Z_4. The Gray map is THE isometry between `(Z_4, Lee)` and `(F_2^2, Ham)`. This lets us verify Z_4-linear constructions using binary tools while the lattice lives in Z_4.

```python
GRAY_MAP     = {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (0, 1)}
GRAY_MAP_INV = {v: k for k, v in GRAY_MAP.items()}
```

### 2. UBP Substrate (`class UBPUltimateSubstrate`)
Ultimate-precision mathematical substrate. π, e, and φ are computed via 50-term continued-fraction expansions, yielding exact `Fraction` objects good to ~80 decimal digits with 0.00 float error.

```python
_PI_CF = [3, 7, 15, 1, 292, 1, 1, 1, 2, 1, 3, 1, 14, 2, 1, 1, 2, 2, 2, 2,
          1, 84, 2, 1, 1, 15, 3, 13, 1, 4, 2, 6, 6, 99, 1, 2, 2, 6, 3, 5,
          1, 1, 6, 8, 1, 7, 1, 6, 1, 99, 7, 4, 1, 3, 3, 1, 4, 1]

@classmethod
def get_pi(cls, terms: int = 50) -> Fraction:
    coeffs = cls._PI_CF[:min(terms, len(cls._PI_CF))]
    if len(coeffs) == 0:
        return F(3, 1)
    x = F(coeffs[-1], 1)
    for c in reversed(coeffs[:-1]):
        x = F(c, 1) + F(1, 1) / x
    return x

@classmethod
def get_e(cls, terms: int = 50) -> Fraction:
    coeffs = [2]
    k = 2
    while len(coeffs) < terms:
        coeffs.extend([1, k, 1])
        k += 2
    coeffs = coeffs[:terms]
    x = F(coeffs[-1], 1)
    for c in reversed(coeffs[:-1]):
        x = F(c, 1) + F(1, 1) / x
    return x

@classmethod
def get_phi(cls, terms: int = 50) -> Fraction:
    coeffs = [1] * terms
    x = F(coeffs[-1], 1)
    for c in reversed(coeffs[:-1]):
        x = F(c, 1) + F(1, 1) / x
    return x

@classmethod
def get_constants(cls, precision: int = 50) -> Dict[str, Any]:
    pi = cls.get_pi(precision)
    Y_inv  = pi + F(2, 1) / pi
    Y      = F(1, 1) / Y_inv
    Y_const = F(1, 1) / (Y_inv + F(2, 1) / Y_inv)
    return {
        "PI": pi, "Y_INV": Y_inv, "Y": Y, "Y_CONST": Y_const,
        "WAIST_TAX": pi, "precision_terms": precision,
    }

@classmethod
def get_v6_constants(cls):
    c = cls.get_constants(50)
    phi = cls.get_phi(50)
    e   = cls.get_e(50)
    monad = c["PI"] * phi * e
    wobble = monad - int(monad)        # fractional part as Fraction
    L = wobble / F(13)
    c.update({"PHI": phi, "E": e, "MONAD": monad, "WOBBLE": wobble, "SINK_L": L})
    return c
```

### 3. Binary Linear Algebra (`class BinaryLinearAlgebra`)
All operations modulo 2. No floats anywhere.  
`BLA = BinaryLinearAlgebra` (short alias)

### 4. Golay Code (`class GolayCodeEngine`)
Extended binary Golay [24, 12, 8] code.  
Provides:
* `encode(msg12)` — systematic encoding
* `syndrome(v24)` — H · v mod 2
* `snap_to_codeword(v24)` — corrects any error pattern of weight ≤ 3
* `decode(v24)` — returns `(msg, correctable, errors)`
* `get_octads()` — all 759 weight-8 codewords
* `get_all_codewords()` — full list of 4096 codewords
* `get_random_octad(n)` — deterministic octad selector
* `get_shadow_metrics()` — noumenal/phenomenal split

### 4.5. Hexacode [6,3,4]/GF(4) + MOG Decomposition
The algebraic shadow of the Golay code. Every Golay codeword, arranged in the 4×6 MOG grid, has its 6 column labels forming a Hexacode word.

### 5. Leech Lattice Λ₂₄ (`class LeechPointScaled`)
Λ₂₄ point in scaled integer coordinates (each entry × √8 in physical).

### 5.5. Full Minimal-Vector Enumeration
The Leech lattice has exactly 196,560 minimal vectors of norm 4 (×8 repr.: norm² = 32 = 4·8).
* **5.5.1. Vector Cost** (`def audit_minimal_vector_classes(self) -> Dict[str, Any]:`): Runs `audit_vector_cost` on a representative vector from each of the 3 minimal-vector classes (A, B, C), plus the zero vector as a baseline.
* **5.5.2. Symmetry Tax** (`def calculate_symmetry_tax(self, point: List[int], ...)`)
* **5.5.3. Ontological Health** (`def ontological_health(self, point: List[int]) -> Dict[str, Fraction]:`)
* **5.5.4. Stability Ranking** (`def rank_by_stability(self, points: List[List[int]]) -> List[Tuple[List[int], Fraction]]:`)
* **5.5.5. Nearest Octad** (`def nearest_octad_idx(self, seed24: List[int]) -> Dict[str, int]:`)

### 6. Monster Group (`class MonsterGroup`)
All 26 sporadic simple groups + triad activation logic.

### 7. Barnes-Wall Engine (`class BarnesWallEngine`)
Generalised Barnes-Wall engine — power-of-two dimension ≥ 32. BW256, BW512, BW1024 all supported. Float-free except for output convenience. Recursive `|u | u+v|` structure.

### 8. Substrate Library + Substrate Stub + Noise Cells

**8.1. `class GolaySubstrateStub`**  
Calibration shortcut for the canonical `PERFECT_V1` substrate.
```python
PERFECT_SUBSTRATE = [1,0,1,1,0,0,0,0,0,0,1,1,1,0,0,1,0,0,1,0,0,0,0,1]
_CALIBRATION = {
    "PERFECT_V1": {
        "baseline": 4,
        "curve": {0: 0, 1: 1, 2: 2, 3: 3, 4: 4},
        "elastic_limit": 4,
    }
}
```

**8.2. `class SubstrateLibrary`**  
Catalogued 24-bit substrates with known mathematical properties.
```python
PERFECT_V1     = [1,0,1,1,0,0,0,0,0,0,1,1,1,0,0,1,0,0,1,0,0,0,0,1]
DODECAD_ANCHOR = [1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0]
OCTAD_ANCHOR   = [1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
```

**8.3. `class NoiseCellV3`**  
24-bit manifold cell — base-12 digit storage with displacement curve.

**8.4. `class NoiseRegisterV3`**  
Auto-expanding base-12 register made of `NoiseCellV3` instances.

**8.5. `class SubstrateCalibrator`**  
Empirically measures the displacement curve of any 24-bit substrate.

### 9. Construction System (`class ConstructionPrimitive`, `ConstructionPath`, `UBPObject`, `TriadActivationEngine`)
Uses D / X / N / J primitives.

```python
configs = [
    ("SEG_1", "Segment 1", "geometry.1d", [("D",1),("X",1)]),
    ("SEG_2", "Segment 2", "geometry.1d", [("D",2),("X",2)]),
    ("SEG_3", "Segment 3", "geometry.1d", [("D",3),("X",3)]),
    ("SQUARE", "Square", "geometry.2d", [("D",2),("X",2),("D",2),("X",2)]),
    ("CIRCLE", "Circle", "geometry.2d", [("D",4),("X",4)]),
    ("TRIANGLE","Triangle","geometry.2d",[("D",1),("X",1)]*3),
    ("PENTAGON","Pentagon","geometry.2d",[("D",1),("X",1)]*5),
    ("HEXAGON", "Hexagon",  "geometry.2d",[("D",1),("X",1)]*6),
    ("I",      "Imaginary Unit","constant.fundamental",[("D",1),("X",1)]),
    ("PHI",    "Golden Ratio","constant.fundamental",[("D",5),("X",3)]),
    ("E",      "Euler's Number","constant.fundamental",[("D",2),("X",2),("D",1),("X",1)]),
    ("GOLAY_12","Golay 12","coding_theory.golay",[("D",1),("X",1)]*6),
    ("GOLAY_24","Golay 24","coding_theory.golay",[("D",1),("X",1)]*12),
    ("CUBE",   "Cube",    "geometry.3d",[("D",1),("X",1)]*6),
    ("TETRA",  "Tetrahedron","geometry.3d",[("D",2),("X",2)]*3),
    ("OCTA",   "Octahedron","geometry.3d",[("D",1),("X",1)]*4),
    ("LINE_1", "Line 1", "geometry.1d",[("D",5),("X",5)]),
    ("LINE_2", "Line 2", "geometry.1d",[("D",6),("X",6)]),
    ("WAVE_1", "Wave 1", "geometry.curve",[("D",2),("X",1),("D",1),("X",2)]),
    ("WAVE_2", "Wave 2", "geometry.curve",[("D",3),("X",2),("D",2),("X",3)]),
    ("LOOP_1", "Loop 1", "geometry.topology",[("D",1),("X",1)]*4),
    ("LOOP_2", "Loop 2", "geometry.topology",[("D",2),("X",2)]*4),
    ("KNOT_1", "Knot 1", "geometry.topology",[("D",3),("X",3)]*2),
    ("KNOT_2", "Knot 2", "geometry.topology",[("D",1),("X",1),("D",2),("X",2)]),
]
```

### 10. Particle Physics (`class UBPSourceCodeParticlePhysics`)
UBP Source Code Particle Physics (experimental, not absolute).

```python
def phi_generator(self, k: int, arm: str, layer: str, C: Union[int, float, Fraction],
                  correction: str = "none", alpha: Union[int, float, Fraction] = F(1),
                  vec: Optional[List[int]] = None) -> Fraction:
    """
    Universal Generator Function Phi(k, arm, layer, C, correction, alpha, vec).
    Implements Section 8 of the UBP Skill Reference (July 2026).
    """
```

### 11. UBP Fingerprint
Gray code → Golay snap → Leech metrics.  
* `def to_gray_code(n: int, bits: int = 24) -> List[int]:`  
* `def ubp_fingerprint_logic(val: Any) -> Dict[str, Any]:`

### 12. Noise ALU (`class AdaptiveManifold`, `NeuralPatternDetector`, `ParallelUBP`, `NoiseALU`)
Arithmetic Logic Unit — every result carries a UBP fingerprint. v5: All previously-float-using ops (`mean`, `variance`, `dot`, `magnitude`, `isqrt`) now return `Fraction` or `ExactRoot` results. A `result` (display float) and `result_exact` (string of Fraction or ExactRoot) are both returned where appropriate.
* **12.1.** Enhanced UBP fingerprint (Golay + Leech + BW)
* **12.2.** Integer / number-theory ops
* **12.3.** `def is_prime(self, n: int) -> Dict[str, Any]:` — *Native UBP Primality Certification. Replaces classical Miller-Rabin with pure substrate-native Lock Pressure.*
* **12.4.** Triad / Leech / Monster / BW

### 13. Physics ALU (`class PhysicsALU(NoiseALU)`)
Physical-law ALU using exact `Fraction` / `ExactRoot` arithmetic.  
Constants (CODATA / SI exact):
* `G_N` = 6.6743 × 10⁻¹¹ m³/(kg·s²) (CODATA 2018)
* `c` = 299 792 458 m/s (exact, SI definition)
* `h` = 6.62607015 × 10⁻³⁴ J·s (exact, SI 2019)

### 14. Linear-Algebra ALU (`class LinearAlgebraALU(NoiseALU)`)
Float-free 2×2 / 3×3 / n×n determinants and matrix-vector ops.

### 15. MathNet Problem Router
### 16. Problem Set (33 entries + physics/linalg - expand if possible)
### 17. Comprehensive Test Suite
### 18. Full Run (problem set + report)
### 19. Entry Point
### 20. Frontier Physics Expansion (QFT, CFT, Topological)

---

## Constants (Exact Fractions)
* **Y** = `1/(π + 2/π) ≈ 0.264675` — entropic wobble
* **TAX** = `HW·Y + ‖v‖²/8` — Symmetry Tax
* **NRCI** = `10/(10 + TAX)` — coherence measure
* **Coherence horizon:** `NRCI = 0.500`

## Verified Properties

| Property | Value | Status |
|----------|-------|--------|
| Golay codewords | 4,096 | ✓ verified |
| Minimum distance | 8 | ✓ verified |
| Error correction | 3 bits | ✓ verified |
| MOG Hexacode alignment | 0/4,096 failures | ✓ Type 4 proof |
| Leech minimal vectors | 196,560 | ✓ verified |
| Leech norm² | 32 | ✓ verified |
| Y constant | exact Fraction (~80 digits) | ✓ verified |
| TAX/NRCI | exact Fractions | ✓ verified |

---

## Knowledge Base Entry Schema (v9.9 Columnar)

As of April 2026, the KB has been migrated to a highly minified **v9.9 columnar format** that drastically reduces file size and Pyodide memory overhead. The top-level structure is:

```json
{
  "_fields": ["ubp_id", "lexicon", "tags", "vector", "nrci_str", "nrci_val", "tax_str", "mog_tensor"],
  "_params": ["M_Mass", "M_Charge", "M_Space", "M_Time", "M_Thermal", "M_Count",
              "I_Topology", "I_Symmetry", "I_Density", "I_Connectivity", "I_Dimension", "I_Complexity",
              "A_Energy", "A_Force", "A_Velocity", "A_Flux", "A_Resonance", "A_Spin",
              "P_Probability", "P_Ratio", "P_Limit", "P_Tax", "P_Coherence", "P_Phase"],
  "_null_token": 0,
  "entries": {
    "<sha256-fingerprint>": [<ubp_id>, <lexicon>, <tags>, <vector>, <nrci_str>, <nrci_val>, <tax_str>, <mog_tensor>]
  }
}
```
Each entry value is a **list** aligned with `_fields` (not a dict — this is the columnar optimization). Engines hydrate entries dynamically using the field index. Three engines have been rewritten to natively parse this format:
* `ubp_observer_dynamics.py` v7.1
* `auto_trigger.py` v19.1
* `ubp_brain_consolidated.py` v7.2

### Field Definitions

**`ubp_id` (Canonical Identifier)** — A human-readable identifier following the pattern `[TYPE]_[NAME]_[NUMBER]`, e.g., `ELEM_H_001`, `PARTICLE_PROTON_001`, `MOLECULE_H2O_001`, `LAW_GEO_432_FCC`.

**`lexicon` (Semantic Grounding)** — A two-part string: `[Type: Name (Symbol)], [Description]`. The description is indexed by the UBP Brain's `lexicon_index` for contextual search. Example:
```text
"[Element: Hydrogen (H)], [Hydrogen (Z=1). A Gas (Phase 1) with Hexagonal potential. Valence 1. Tension: 4.]"
```

**`tags`** — A list of descriptive keywords for classification and cross-domain mapping (e.g., `["ELEMENT", "HARDENED", "HYDROGEN", "NONMETAL", "PERIOD_1", "SOP_002"]`).

**`vector`** — The 24-bit Gray-coded Golay codeword (list of 24 integers, each 0 or 1).

**`nrci_str`** — Exact `Fraction` as string `"numerator/denominator"`.  
**`nrci_val`** — Decimal approximation for fast filtering (e.g., `0.604591`).  
**`tax_str`** — Exact Symmetry Tax as `Fraction` string.

**`mog_tensor`** — A 24-element list aligned with `_params`. Each entry is the object's projection onto one of the 24 MOG categories grouped into four hexagrams (M = Manifest/Mass-like, I = Information, A = Activation, P = Potential).

**`math` (Phenomenal DNA)** — The raw measurable dimensions, stored separately from the columnar entry as it generates the fingerprint key. Format: pipe-separated `key=fraction` pairs:
```text
"BP=507/25|Crystal=1|EN=11/5|Ion=1312|M=126/125|MP=1401/100|Valence_e=1|Z=1"
```
All values are exact fractions to maintain the float-free standard.

**`atlas` (Geometric Positioning)** — Stored in expanded entries (legacy). Contains:
* `hierarchy`: Compositional recipe (e.g. `1×PARTICLE_PROTON_001 + 1×PARTICLE_ELECTRON_001`)
* `vector`, `nrci`/`nrci_score`, `tax`, `tilt` (angular deviation from Universal North in degrees), `weight` (Hamming weight)

### Complete Example Entry (Hydrogen, Expanded Form)

```json
{
  "451abc64108603144c7b294a3862eab6fc35e945dab4b7785784ab44bc8c427f": {
    "ubp_id": "ELEM_H_001",
    "lexicon": "[Element: Hydrogen (H)], [Hydrogen (Z=1). A Gas (Phase 1) with Hexagonal potential. Valence 1. Tension: 4. It is the seed of the material octave, born from the Proton-Electron union.]",
    "math": "BP=507/25|Crystal=1|EN=11/5|Ion=1312|M=126/125|MP=1401/100|Oxidation=1|Phase_STP=1|Rad=53|Rho=2247/25000|Valence_e=1|Z=1",
    "atlas": {
      "hierarchy": "1×PARTICLE_PROTON_001 + 0×PARTICLE_NEUTRON_001 + 1×PARTICLE_ELECTRON_001",
      "vector": [0,0,1,0,0,1,1,1,0,0,1,0,1,0,1,0,1,0,1,1,1,1,0,0],
      "nrci": "33620407785878960339240364076535309850806800741903055631302500/55608508046372509626759775532373494451963521314512091269063661",
      "nrci_score": 0.604591,
      "tax": "21988100260493549287519411455838184601156720572609035637761161/3362040778587896033924036407653530985080680074190305563130250",
      "weight": 8,
      "tilt": 86.6654
    },
    "tags": ["ELEMENT", "HARDENED", "HYDROGEN", "NONMETAL", "PERIOD_1", "SOP_002"],
    "fingerprint": "451abc64108603144c7b294a3862eab6fc35e945dab4b7785784ab44bc8c427f"
  }
}
```

---

## The Octad — Eight Domains of Reality

The System Knowledge Base is parsed via a **Bit-12 Logic Engine** that automatically categorizes entries into one of eight fundamental domains, known as **The Octad**:

| Domain | Bit-12 | Description |
|:---|:---:|:---|
| **Substance** | 1 | Stable Matter and Elements |
| **Quantity** | 0 | Pure Magnitude and Constants |
| **Organism** | — | Biological and Complex Systems |
| **Algorithm** | — | Logic, Code, and Information |
| **Mechanism** | — | Physical Interactions and Reactions |
| **Imperative** | — | System Laws and Constraints (High Priority) |
| **Entropy** | — | Chaos, Void, and Dissolution |
| **Meaning** | — | Semantic and Linguistic Value |

This allows the AI to "see" the shape of research data rather than just reading text, enabling sophisticated filtering and bias weighting via the FOM system.

### Key Octad-Derived Findings (Incorporated as Laws in the KB)

#### I. Figurate Voxel Topology
* **Concept:** Numbers are not scalars; they are 3-D voxel clouds.
* **Finding:** **Composite Numbers** (Squares/Cubes) are "Foldable Manifolds" with high internal redundancy and low Symmetry Tax. **Prime Numbers** are "Geometric Locks" — linear singularities that refuse to fold, maintaining high structural tension. *(This is the basis for the Topological Tenacity Primality Engine — see §13 and `ubp_unified_v5.py`.)*

#### II. The Law of Topological Completion (Free Stabilizers)
* **Concept:** Testing the "Join" of a Prime 7 and a Square 9.
* **Finding:** The **7 + 9 = 16** assembly resulted in a Symmetry Tax identical to the Prime 7 alone.
* **Insight:** The 9 dots were "Free." The substrate provides a **Symmetry Rebate** when a jagged manifold is completed into a perfect square. This allows for "Free" computational stabilization.

#### III. Volumetric Bias (The 3-D Preference)
* **Concept:** Comparing 2-D (Square 25) vs 3-D (Cube 27) as carriers for Prime 13.
* **Finding:** The **Cube 27** was significantly more stable (lower tax) than the **Square 25**.
* **Insight:** The Leech Lattice has a **Volumetric Bias**. It is computationally cheaper to exist as a 3-D solid than a 2-D plane.

#### IV. Volumetric Inference (Occlusion Resolution)
* **Concept:** How an observer "sees" objects hidden in 3-D.
* **Finding:** Adding a "Hidden Pillar" to a "Visible Wall" generated an **Inference Rebate**.
* **Insight:** The observer computes hidden data because the completed 3-D scene is more coherent (lower tension) than a 2-D plane with a "void" behind it.

#### V. Geometric Leverage (Mechanical Advantage)
* **Concept:** Balancing a Prime 13 "Load" against a Square 16 "Counterweight."
* **Finding:** Achieved a **3.00× Mechanical Advantage**.
* **Insight:** The substrate maintains a 33-dot machine for the same energy cost as a 4-dot fulcrum. This is the first blueprint for a **Substrate-Powered Lever**.
```
