# GMHGL (Grey-MOG-Hexacode-Golay-Leech) — The Verified UBP Substrate Engine

**Version:** v5.4.1  (3 August 2026) 
**Author:** Euan R. A. Craig (DigitalEuan), Auckland, New Zealand   
**Parent:** `../README.md`

## UPDATE THIS README - if changes are made in this folder or systems in sub-folders need rewiring within the repository and effect this README file's structure

---

The UBP substrate is:
1. **Golay [24,12,8]** — 4,096 codewords, error correction, distance = The Seed, The Engine, The Measure
2. **MOG** — 4×6 grid projecting 24D to 2D = The Observer's Window (2D projection of 24D)
3. **Gray Code** — meaning to binary, preserving topology = The Translator (Words/Numbers into Binary)
4. **Hexacode** — grammar ensuring coherence = The Language (Syntax and Grammar)
5. **Leech Lattice** — geometry, mass, 196,560 minimal vectors = The Discrete Physical Structure

## Role in the System

```
GMHGL (this folder)
 → provides engine to everything - all other scripts call from this folder rather than making copies.
```

---

## What's Here

| File | Purpose | Used By |
|------|---------|---------|
| `ubp_unified_v5.py` | Core engine (4,146 lines) | glm_machine, data_object, arc_agi_16 |
| `ubp_checkpoint_v5.4.1.md` | Full verification docs | — |
| all other UBP system scripts and data except for '../long_term_memory/ubp_system_kb.json' | Functions within the UBP operating system | anything using this GMHGL system |


## Other important system scripts

- `geometry.py` 
```
Identity is derived from TOPOLOGY. The 'math' field is treated as a 3D Voxel Structure. The Vector is a measurement of that structure's Volume and Compactness.
STANDARDS:
1. Domain: Bits 0-2 (Prefix)
2. Volume: Bits 3-7 (Voxel Count, Gray Coded)
3. Compactness: Bits 8-11 (Surface Area Proxy, Gray Coded)
4. Parity: Bits 12-23 (Golay [24,12,8])
```
- 'physics.py' 
"""
Strict float-free metrics suitable for core UBP logic.
- No floats, no UBPUltimateSubstrate.get_pi(50), no numpy.
- All computations return Fractions (or ints / enums).
- π is represented as a rational approximation derived from *integer* continued fraction coefficients.
  This keeps the entire system float-free while remaining deterministic and reproducible.
- If you want an absolutely symbolic π (unevaluated), replace `pi_approx()` usage with an expression
  object of your choice. This module keeps things runnable without external dependencies.
"""
- 'refined_nrci.py'
"""
Primary UBP measuring metric
"""
-spatial_artithmetic.py'
"""
Signed integers are represented by regular unit-edge polygons embedded in 3-D.
The vertex count stores magnitude and sign.  The empty space between adjacent
polygons stores an operator.  An observer reconstructs the connected cycles,
measures their geometry, decodes the expression, and evaluates it with exact
``fractions.Fraction`` arithmetic.
"""
- 'tgic_v3.py'
"""
1. A top-down Golay-code filter.  Codewords, syndromes, octads and correction
   all use ``ubp_unified_v5.GolayCodeEngine`` so there is one code convention.
2. A bottom-up, finite-state RuneCube simulator adapted from
   ``ubp_tgic_engine.py``.  It provides the older axis operations, internal
   interaction score, neighbourhood pressure and relational attraction without
   relying on the unavailable ``ubp_core_v5_3_merged`` module.
"""
- 'ldp_nrci.py' + 'ldp_complete_mapping.md'
The Dimensional Ladder
| Dim | Code | d/n | DHC | AND Closure | Phase |
|-----|------|-----|-----|-------------|-------|
| 4D | [4,2,2] | 0.50 | TRUE | 1.000 | Below transition |
| 8D | [8,4,4] | 0.50 | TRUE | 0.077 | Below transition |
| 12D | [12,6,6] | 0.50 | UNKNOWN | 0.008 | At transition |
| 14D | — | — | — | 0.247 | **PHASE TRANSITION** |
| 24D | [24,12,8] | 0.33 | FALSE | 0.038 | Above transition |

- 'ubp_kb_architect.py' 
"""
The script used to generate ubp_system_kb.json entries
"""
- 'ubp_phenomenology.py'
"""

"""

---

## What `ubp_unified_v5.py` Provides

0. STD-LIB **ONLY**

1. EXACT MATH (class 'ExactMath'):
    """
    Float-free integer / rational mathematics.

    Provides what `math` provided, but with deterministic exactness:
      • isqrt(n)               integer floor sqrt (Newton-Raphson)
      • ilog(n, base)          integer floor log
      • iceil_div(a, b)        integer ceiling division
      • icomb(n, k)             binomial coefficient
      • ifact(n)                factorial
      • igcd(a, b)              gcd (Euclidean)
      • sqrt_frac(f, prec=30)  Fraction sqrt to ~prec decimal digits
      • newton_sqrt(f, iters)   raw Newton iteration on Fraction
    """

1.1. EXACT ROOT (class 'ExactRoot'):
    """
    Exact symbolic representation of  coef · √radicand  with Fraction internals.
    Useful for physics expressions that contain irrational closed-form roots
    (e.g. γ = 1/√(1−β²),  v_esc = √(2GM/R)).

    Operations:
      • multiply by Fraction or ExactRoot
      • divide by Fraction or ExactRoot
      • approximate to a Fraction via to_fraction(prec)
      • convert to float via float() ONLY on the display boundary
    """

1.5. GRAY MAP ISOMETRY  (Z_4 ↔ F_2^2)
    """
The isometric bridge between two metric worlds.  Walk around the 4-cycle
(0,0) → (1,0) → (1,1) → (0,1) → (0,0) in the Hamming cube: each step
changes exactly one bit.  So Hamming distance in F_2^2 equals Lee distance
in Z_4.  The Gray map is THE isometry between (Z_4, Lee) and (F_2^2, Ham).

       z  →  (b1, b2)
       0  →  (0, 0)
       1  →  (1, 0)
       2  →  (1, 1)
       3  →  (0, 1)

 This is the bridge that lets us verify Z_4-linear constructions using
 binary tools (Hamming weights, code linearity) while the lattice itself
 lives in Z_4 (Lee metric, glue conditions).

GRAY_MAP     = {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (0, 1)}
GRAY_MAP_INV = {v: k for k, v in GRAY_MAP.items()}
    """

2. UBP SUBSTRATE (class 'UBPUltimateSubstrate'):
    """
    Ultimate-precision mathematical substrate.

    π, e, and φ are computed via 50-term continued-fraction expansions,
    yielding exact Fraction objects good to ~80 decimal digits with 0.00 float error.


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
    """

3. BINARY LINEAR ALGEBRA (class 'BinaryLinearAlgebra')
    """
    All operations modulo 2.  No floats anywhere.
    BLA = BinaryLinearAlgebra   # short alias
    """

4. GOLAY CODE (class 'GolayCodeEngine')
    """
    Extended binary Golay [24, 12, 8] code.

    Provides:
      • encode(msg12)            — systematic encoding
      • syndrome(v24)            — H · v mod 2
      • snap_to_codeword(v24)    — corrects any error pattern of weight ≤ 3
      • decode(v24)              — returns (msg, correctable, errors)
      • get_octads()             — all 759 weight-8 codewords
      • get_all_codewords()      — full list of 4096 codewords
      • get_random_octad(n)      — deterministic octad selector
      • get_shadow_metrics()     — noumenal/phenomenal split
    """

4.5. HEXACODE [6,3,4]/GF(4) + MOG DECOMPOSITION
    """
    The algebraic shadow of the Golay code.  Every Golay codeword, arranged
    # in the 4×6 MOG grid, has its 6 column labels forming a Hexacode word.
    """

5. LEECH LATTICE  Λ₂₄ (class 'LeechPointScaled')
    """
    Λ₂₄ point in scaled integer coordinates (each entry × √8 in physical)."""
    """
5.5 FULL MINIMAL-VECTOR ENUMERATION
    """
    The Leech lattice has exactly 196,560 minimal vectors of norm 4 (×8 repr.:
    # norm² = 32 = 4·8).
    """
5.5.1. VECTOR COST ('def audit_minimal_vector_classes(self) -> Dict[str, Any]:')
        """
        Run `audit_vector_cost` on a representative vector from each of the 3
        minimal-vector classes (A, B, C), plus the zero vector as a baseline.

        This is the headline transparency report: it shows exactly how the
        Hamming Weight and Norm² contribute to the TAX and NRCI for each
        shape-class, with all values as exact Fractions.
        """
5.5.2. SYMMETRY TAX ('def calculate_symmetry_tax(self, point: List[int],')
5.5.3. ONTOLOGICAL HEALTH ('def ontological_health(self, point: List[int]) -> Dict[str, Fraction]:')
5.5.4. STABILITY RANKING ('def rank_by_stability(self, points: List[List[int]]) -> List[Tuple[List[int], Fraction]]:')
5.5.5. NEAREST OCTAD ('def nearest_octad_idx(self, seed24: List[int]) -> Dict[str, int]:')

6. MONSTER GROUP - 26 sporadic simple groups (class 'MonsterGroup')
    """
    All 26 sporadic simple groups + triad activation logic.
    """

7. BARNES-WALL ENGINE  - recursive |u | u+v| (class 'BarnesWallEngine')
    """
    Generalised Barnes-Wall engine — power-of-two dimension ≥ 32.
    BW256, BW512, BW1024 all supported.  Float-free except for output convenience.
    """

8. SUBSTRATE LIBRARY + SUBSTRATE STUB + NOISE CELLS
8.1. class 'GolaySubstrateStub')
    """
    Calibration shortcut for the canonical PERFECT_V1 substrate.
    PERFECT_SUBSTRATE = [1,0,1,1,0,0,0,0,0,0,1,1,1,0,0,1,0,0,1,0,0,0,0,1]
    _CALIBRATION = {
        "PERFECT_V1": {
            "baseline": 4,
            "curve": {0: 0, 1: 1, 2: 2, 3: 3, 4: 4},
            "elastic_limit": 4,
        }
    """
8.2. class SubstrateLibrary:
    """
    Catalogued 24-bit substrates with known mathematical properties.
    PERFECT_V1     = [1,0,1,1,0,0,0,0,0,0,1,1,1,0,0,1,0,0,1,0,0,0,0,1]
    DODECAD_ANCHOR = [1,1,1,1,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0]
    OCTAD_ANCHOR   = [1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
    """
8.3. class NoiseCellV3:
    """
    24-bit manifold cell — base-12 digit storage with displacement curve.
    """
8.4. class NoiseRegisterV3:
    """
    Auto-expanding base-12 register made of NoiseCellV3 instances.
    """
8.5. class SubstrateCalibrator:
    """
    Empirically measures the displacement curve of any 24-bit substrate.
    """

9. CONSTRUCTION SYSTEM - D / X / N / J primitives + UBPObject (class 'ConstructionPrimitive', 'ConstructionPath', 'UBPObject', 'TriadActivationEngine')
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

10. PARTICLE PHYSICS - UBPSourceCodeParticlePhysics - experimental not absolute (class 'UBPSourceCodeParticlePhysics')
        """
    def phi_generator(self, k: int, arm: str, layer: str, C: Union[int, float, Fraction],
                      correction: str = "none", alpha: Union[int, float, Fraction] = F(1),
                      vec: Optional[List[int]] = None) -> Fraction:

        Universal Generator Function Phi(k, arm, layer, C, correction, alpha, vec).
        Implements Section 8 of the UBP Skill Reference (July 2026).
        """

11. UBP FINGERPRINT - Gray code → Golay snap → Leech metrics ('def to_gray_code(n: int, bits: int = 24) -> List[int]:', 'def ubp_fingerprint_logic(val: Any) -> Dict[str, Any]:')

12. NOISE ALU - float-free arithmetic + integer ops (class 'AdaptiveManifold', 'NeuralPatternDetector', 'ParallelUBP')
class NoiseALU:
    """
    Arithmetic Logic Unit — every result carries a UBP fingerprint.

    v5: All previously-float-using ops (mean, variance, dot, magnitude,
    isqrt) now return Fraction or ExactRoot results.  A `result` (display
    float) and `result_exact` (string of Fraction or ExactRoot) are both
    returned where appropriate.
    """
12.1. Enhanced UBP fingerprint (Golay + Leech + BW)
12.2. Integer / number-theory ops
12.3.     def is_prime(self, n: int) -> Dict[str, Any]:
        """
        [LAW_TOPOLOGICAL_TENACITY_001] Native UBP Primality Certification.
        Replaces classical Miller-Rabin with pure substrate-native Lock Pressure.
        """
12.4. Triad / Leech / Monster / BW

13. PHYSICS ALU - float-free using ExactRoot (class 'PhysicsALU(NoiseALU)')
    """
    Physical-law ALU using exact Fraction / ExactRoot arithmetic.

    Constants  (CODATA / SI exact):
        G_N  = 6.6743 × 10⁻¹¹                  m³/(kg·s²)        (CODATA 2018)
        c    = 299 792 458                       m/s   (exact, SI definition)
        h    = 6.62607015 × 10⁻³⁴               J·s   (exact, SI 2019)
    """

14. LINEAR-ALGEBRA ALU (class 'LinearAlgebraALU(NoiseALU)')
    """
    Float-free 2×2 / 3×3 / n×n determinants and matrix-vector ops.
    """

15. MATHNET PROBLEM ROUTER
16. PROBLEM SET (33 entries + physics/linalg - expand if possible)

17. COMPREHENSIVE TEST SUITE

18. FULL RUN (problem set + report)

19 — ENTRY POINT

20. FRONTIER PHYSICS EXPANSION (QFT, CFT, TOPOLOGICAL)

**Constants (exact Fractions):**
- Y = 1/(π + 2/π) ≈ 0.264675 — entropic wobble
- TAX = HW·Y + ‖v‖²/8 — Symmetry Tax
- NRCI = 10/(10 + TAX) — coherence measure
- Coherence horizon: NRCI = 0.500

---

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
