# R-calculus v2 — Implementation Report

## Self-contained, with the integer oscillator and the catalogue

---

## 1. What v2 fixes and adds

The original `r_calculus.py` depended on `geometric_corpus_prototype` for the Golay code — a dependency the user didn't have. **v2 is fully self-contained**: the Golay code is implemented inline (Python stdlib only, no external imports). The module generates all 4096 codewords from the generator polynomial, provides nearest-codeword decoding, and codeword testing.

### v2 also adds four things the original doc mentioned but didn't build:

1. **The integer oscillator** (V drives ρ) — the "next step" the original doc's section 11 described as a feedback loop where V feeds back into the drive ρ. Three variants: linear, threshold, quadratic.

2. **The codeword catalogue sweep** — residual fingerprints for all 4096 Golay codewords, revealing the distribution of cycle lengths. The original doc tested 6 codewords; v2 tests all 4095 non-zero codewords in 15 seconds.

3. **The coupling of two pipelines** (interlocking blocks) — two R-calculus systems with different targets, where each system's rotation is driven by the other's residual. Cross-correlation measures synchronization.

4. **GLM guard integration** — the layer-aware identity guard from the v15/v16 engine, applied to the R-calculus operators. Four algebraic identities tested on up to 98,304 cases each. All pass.

### v2 also improves the arithmetic:

- **Exact Fractions** for mean, variance, and autocorrelation (v1 used floats).
- **Exact integer cycle detection** with configurable min_repeat.
- **The DFT extractor** is present but uses a scaled-integer approach (the exact cyclotomic-field computation is left as a future improvement).

---

## 2. The self-contained Golay code

The `GolayCode` class generates all 4096 codewords from the generator polynomial `g(x) = x¹¹ + x¹⁰ + x⁶ + x⁵ + x⁴ + x² + 1` (the standard Golay polynomial). The 12 generator rows are built from the cyclic shifts of g(x), with a parity bit at position 23 to make the code doubly-even (every codeword has weight divisible by 4). All 2¹² = 4096 codewords are enumerated by XOR combinations of the rows.

`is_codeword(x)` tests membership in O(1) (set lookup). `nearest_codeword(x)` decodes by brute force over all 4096 codewords — O(4096) per call, exact. For production use, one would implement syndrome decoding (O(1) for the Golay code), but brute force is fine for the R-calculus demonstration.

---

## 3. The five demonstrations

### Demo 1: the canonical pipeline (reproduces v1's finding)

T = 0x00149f (weight-8 Golay codeword), S₀ = T ⊕ 0x00000F, ρ = 1-bit rotation, C = greedy 1-flip, R = Hamming weight, 200 steps.

**Result**: V has a **38-step cycle from step 0**, mean = 469/50 = 9.38, range [4, 15]. The autocorrelation at lag 19 is **−0.91** (anti-correlated at the half-period), at lag 38 is **+0.96** (correlated at the full period). This exactly reproduces v1's finding, confirming the self-contained Golay code is correct.

### Demo 2: the integer oscillator (v2 NEW)

Three feedback variants, compared to the fixed-rotation baseline:

| Variant | Mean | Std | Range | Cycle |
|---------|------|-----|-------|-------|
| baseline (fixed ρ=1) | 9.38 | 2.58 | [4,15] | (0, 38) |
| linear: shift = V[n-1] mod 24 | 11.83 | 1.24 | [4,14] | (13, 4) |
| threshold: shift = 1 if V<10 else 3 | 12.15 | 1.89 | [4,15] | (18, 14) |
| quadratic: shift = (V[n-1]²) mod 24 | 12.09 | 2.20 | [4,18] | (43, 2) |

**Finding**: the oscillator produces **different dynamics** from the fixed rotation. The linear variant collapses to a short 4-cycle (the feedback drives the system into a tight orbit). The threshold variant produces a 14-cycle. The quadratic variant produces a 2-cycle after a 43-step transient. The feedback loop (V → ρ) creates self-modulated periods — the original doc's prediction confirmed.

### Demo 3: the codeword catalogue (v2 NEW)

All 4095 non-zero Golay codewords swept in 15 seconds. Each codeword produces a residual fingerprint: (cycle_length, mean, std, range).

**Cycle length distribution** (selected):
- **L=46**: 1890 codewords (the most common — the "typical" fingerprint)
- **L=2**: many codewords (degenerate — the correction dominates)
- **L=38, 40, 42, 44**: the "rich dynamics" codewords (including the original demo's T=0x00149f at L=38)
- **L=34**: rare (e.g., T=0x02877f)

**Mean residual distribution** (binned to integers):
- mean=11: 2844 codewords (the peak)
- mean=10: 996 codewords
- mean=9: 192 codewords
- mean=8: 48 codewords
- mean=0: 1 codeword (the zero codeword, skipped)

**Finding**: the cycle length is a **fingerprint of the target** — different codewords produce different cycle lengths, and the distribution is structured (not uniform). The 46-step cycle is the "typical" Golay codeword's residual; the 38-step cycle (the original demo) is an outlier.

### Demo 4: coupling two pipelines (v2 NEW)

Two R-calculus systems with different targets (T₁ = 0x00149f, T₂ = 0x003da1), each system's rotation driven by the other's residual. 200 steps.

**Result**:
- System 1: mean=13.90, std=1.96, range=[4,18], cycle=(73, 2)
- System 2: mean=10.82, std=2.34, range=[4,19], cycle=(177, 2)
- **Cross-correlation (lag 0): +0.0288** — the two systems are **INDEPENDENT**

**Finding**: the coupling as currently implemented (each system's shift = other's V mod 24) does NOT synchronize the two systems. The cross-correlation is near zero. This is an honest negative result — the coupling needs to be stronger (e.g., shared correction, or a common drive) to produce synchronization. The original doc's "interlocking blocks" prediction is not confirmed by this simple coupling; a more sophisticated coupling mechanism is needed.

### Demo 5: GLM guard integration (v2 NEW)

Four algebraic identities tested by the layer-aware identity guard:

| Identity | Cases tested | Result |
|----------|-------------|--------|
| Hamming distance = popcount(a ⊕ b) | 65,536 | **PASS** |
| rotate(rotate(S, k), 24−k) = S (involution) | 98,304 | **PASS** |
| greedy correction: dist(C(S,T), T) ≤ dist(S, T) | 65,536 | **PASS** |
| magnetization = 24 − 2·popcount | 4,096 | **PASS** |

**Overall: ALL GUARDS PASS**. The R-calculus operators are algebraically correct on every test case. This confirms the engine's substrate (the bit-vector arithmetic) is sound — the same conclusion the v16 engine reached for the TAX and wobble domains.

---

## 4. What v2 proves

v2 proves four things:

**1. The R-calculus is self-contained.** No external dependencies. The Golay code, all operators, all extractors, and the guard integration work from a single file. The module can be dropped into any environment with Python 3.8+.

**2. The integer oscillator computes.** The feedback loop (V → ρ) produces self-modulated periods, confirming the original doc's "next step" prediction. The linear, threshold, and quadratic variants each produce different dynamics — the oscillator is tunable.

**3. The codeword catalogue is structured.** The 4095 non-zero Golay codewords produce a structured distribution of cycle lengths (not uniform). The 46-step cycle is the "typical" fingerprint; the 38-step cycle (the original demo) is an outlier. The cycle length is a genuine fingerprint of the target.

**4. The guards pass.** The R-calculus operators are algebraically correct on every test case. The engine's guard architecture (developed in v15/v16 for the hypothesis engine) applies cleanly to the R-calculus — the same identity guard that caught the TAX criterion error confirms the R-calculus operators are sound.

---

## 5. What v2 does NOT confirm

**The coupling does not synchronize.** The simple coupling (each system's shift = other's V mod 24) produces independent systems (cross-correlation +0.03). The original doc's "interlocking blocks" prediction is not confirmed by this coupling mechanism. A stronger coupling (shared correction, common drive, or phase-locking) would be needed to produce synchronization. This is an honest negative result — the coupling is a research direction, not a settled finding.

---

## 6. Files

- **`r_calculus_v2.py`** (~700 lines) — the self-contained module, including the Golay code, all operators, the oscillator, the catalogue sweep, the coupling, and the guard integration. Run with `python3 r_calculus_v2.py` (full) or `python3 r_calculus_v2.py --quick` (200 codewords).
- **`r_calculus_v2_output.json`** — the structured output (basic run stats, catalogue summary, guard results).

The original `r_calculus.py` and `R_Calculus_Does_It_Compute.md` are preserved in the upload directory; v2 is a drop-in replacement that needs no external dependencies.
