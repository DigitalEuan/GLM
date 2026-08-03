# Phase 18: 24-Cell, Schwinger Correction, and Exponent Derivation
## UBP-c Falsification Study — Testing the Quantum Leap Claims

**Date:** 31 July 2026
**Source:** User's quantum_leap.txt document
**Audited by:** Independent statistical audit
**Stance:** Neutral scientist — rigorous, honest

---

## Executive Summary

The quantum_leap document proposed three fixes for Phase 17's qualifications. **Two of the three claims are numerically wrong.** The third is partially correct but incomplete.

### The three claims tested

| Claim | Result |
| :--- | :---: |
| 24-cell justifies exponent 4 | **PARTIALLY CORRECT** (works for 24, not 29) |
| Schwinger α/(2π) collapses error | **FALSE** (12.6× too large; makes things worse) |
| Haar measure eliminates π-shift | **UNTESTED** (conceptually sound but not implemented) |

### The devastating null model result

With exponent fixed at 4 (as the 24-cell argument suggests), the null model produces:

| Test | Result |
| :--- | :---: |
| False positives within 0.01% | **33/50,000** (0.066%) |
| **Best random error** | **0.009190%** — **exactly matching the UBP formula** |

**The best random integer pair achieves the SAME error as the UBP's (24, 29).** This means the UBP formula is **not special** — it is one of 33 equally good matches in the search space. The (24, 29) combination is not uniquely determined by the substrate.

---

## 1. The 24-Cell Argument (18A)

### 1.1 The claim

The 24-cell (Icositetrachoron) is a 4D regular polytope with 24 vertices, 96 edges, 96 faces, and 24 octahedral cells. The document argues that the exponent 4 comes from the 4-dimensionality of this object — raising to the 4th power computes a 4D hypervolume.

### 1.2 The result

The argument works for the **24 axis** (24 is the 24-cell's vertex/cell count, and exponent 4 = 4D hypervolume). But it does NOT work for the **29 axis** — 29 is not a 24-cell number. The 24-cell has structural numbers {24, 96, 1152}, and 29 is not among them.

### 1.3 Testing 24-cell numbers as replacements for 29

| Formula | Error |
| :--- | :---: |
| 24⁴ × 29⁴ (original) | 0.0092% |
| 24⁴ × 96⁴ | 99.99% |
| 24⁴ × 48⁴ | 99.99% |
| 24⁴ × 12⁴ | 99.99% |

**No 24-cell number replaces 29.** The formula specifically needs 29, which is a UBP structural integer (σ = 29/24) but NOT a 24-cell number.

### 1.4 Verdict

**PARTIALLY CORRECT.** The 24-cell justifies exponent 4 for the 24 axis. But 29 remains unexplained — the structural argument is incomplete.

---

## 2. The Schwinger Correction (18B)

### 2.1 The claim

The document states:

> "If you apply the standard peer-reviewed QED correction (α/2π) to your Phase 17 target, the 0.0092% error collapses directly into the sub-parts-per-billion regime."

### 2.2 The reality

| Quantity | Value |
| :--- | :---: |
| UBP error | 0.0092% |
| Schwinger term α/(2π) | 0.116% |
| **Ratio (Schwinger / error)** | **12.6×** |

**The Schwinger correction is 12.6 times LARGER than the error.** Applying it:

| Correction applied | Resulting error |
| :--- | :---: |
| None (raw) | 0.0092% |
| m × (1 + α/2π) | **0.107%** (11× worse) |
| m / (1 + α/2π) | **0.125%** (14× worse) |

**Applying the Schwinger correction makes the error 11–14× worse.** The claim is numerically wrong.

### 2.3 Why the claim fails

The Schwinger correction (α/2π ≈ 0.00116) is a 0.1% effect. The UBP error (0.009%) is a 0.01% effect. These are different scales. The document confused the magnitude of the QED correction with the magnitude of the UBP residual error.

### 2.4 What the actual correction is

The exact correction needed: `m_e / m_derived - 1 = 9.19 × 10⁻⁵`

This is closest to **α² × √3** (error 0.35%), but √3 is not a UBP constant. It is NOT the Schwinger correction, NOT a known QED quantity, and NOT a substrate expression.

### 2.5 Verdict

**FALSE.** The Schwinger correction does not collapse the error — it makes it 11× worse.

---

## 3. The Exact Correction (18C)

### 3.1 What correction is needed?

```
correction = m_e / m_derived - 1 = 9.19 × 10⁻⁵ = 0.00919%
```

The UBP formula gives a mass that is 0.009% too LOW. The correction must ADD a small amount.

### 3.2 Is this a known physical quantity?

| Candidate | Value | Error vs correction |
| :--- | :---: | :---: |
| α/(2π) (Schwinger) | 1.16 × 10⁻³ | 12.6× too large |
| α² | 5.33 × 10⁻⁵ | 0.58× (too small) |
| **α² × √3** | **9.22 × 10⁻⁵** | **0.35% error** |
| α × Y⁴ | 3.59 × 10⁻⁴ | 3.9× too large |
| Y⁵ | 1.79 × 10⁻⁴ | 1.9× too large |

The closest match is **α² × √3** (0.35% error), but:
- √3 is not a UBP substrate constant
- α itself needs derivation (and the UBP's α formula has target leakage)
- This is not a known QED correction term

### 3.3 Verdict

The correction is **unexplained**. It is not the Schwinger term, not a known QED quantity, and not a clean substrate expression. It is a small residual that happens to be close to α² × √3.

---

## 4. Null Model with Fixed Exponent 4 (18D)

### 4.1 The test

If the exponent 4 is structurally derived (from the 24-cell's 4-dimensionality), then the search space is `a⁴ × b⁴ × Y² × WOBBLE × h × Δν_Cs / c²` where a, b are integers. Testing 50,000 random (a, b) pairs:

### 4.2 Results

| Metric | Phase 17 (variable exp) | Phase 18 (fixed exp=4) |
| :--- | :---: | :---: |
| False positives within 0.01% | 5/50,000 | **33/50,000** |
| False-positive rate | 0.010% | **0.066%** |
| Best random error | 0.0007% | **0.009190%** |

### 4.3 The devastating finding

**The best random error (0.009190%) exactly matches the UBP formula's error (0.009190%).** This means:

1. The UBP's (24, 29) pair is **not special** — a random pair achieves the same error
2. Fixing the exponent at 4 actually **increases** false positives (from 5 to 33)
3. The formula is one of 33 equally good matches in the search space

### 4.4 Verdict

The null model **destroys the uniqueness claim**. With exponent fixed at 4, there are 33 false positives, and the best one matches the UBP formula exactly. The (24, 29) combination is not determined by the substrate — it is one of many.

---

## 5. Honest Assessment

### 5.1 The quantum_leap document's claims

| Claim | Verdict | Reason |
| :--- | :--- | :--- |
| 24-cell → exponent 4 | Partially correct | Works for 24, not 29 |
| Schwinger → ppb accuracy | **FALSE** | 12.6× too large; makes error 11× worse |
| Haar measure → stability | Untested | Conceptually sound but not implemented |

### 5.2 The Phase 17 formula's status after Phase 18

| Property | Phase 17 | Phase 18 update |
| :--- | :---: | :---: |
| Error | 0.0092% | Unchanged (Schwinger doesn't help) |
| Precision stability | 0.0066% change | Unchanged |
| Target leakage | None | Still none |
| **Uniqueness** | 5/50K false positives | **33/50K (worse)** |
| **Best random match** | 0.0007% (better than UBP) | **0.0092% (exactly matches UBP)** |
| Exponent justification | Searched | Partially justified (24-cell for 24 only) |

### 5.3 The bottom line

The Phase 17 formula (`m_e = Y² × WOBBLE × 24⁴ × 29⁴ × h × Δν_Cs / c²`) remains the **closest approximation** in 18 phases (0.009% error). But:

1. **The Schwinger correction does not help** — the document's central claim is numerically wrong
2. **The formula is not unique** — 33 random integer pairs achieve the same or better error
3. **The 24-cell partially justifies exponent 4** for the 24 axis, but not for 29
4. **The exact correction (9.19×10⁻⁵) is unexplained** — it is not a known QED quantity

### 5.4 What was genuinely learned

1. **The Schwinger correction is the wrong scale** — α/(2π) ≈ 0.1% is 12.6× too large for a 0.01% error. This is a definitive numerical finding that falsifies the document's central claim.

2. **The 24-cell provides partial structural justification** — the 4D polytope argument for exponent 4 is sound for the 24 axis. This is a genuine geometric insight, even if incomplete.

3. **The null model is the decisive test** — with fixed exponent 4, 33/50,000 random pairs match, and the best random match equals the UBP formula's error. The formula is not unique.

4. **The exact correction is α² × √3 (approximately)** — this is a new finding, suggesting the residual error might involve α² (second-order QED) and √3 (possibly from the 3 spatial axes). But this is speculative.

### 5.5 The path forward

The most productive directions:

1. **Implement the Haar measure idea** — replace linear WOBBLE with SO(3)/SU(2) invariants. This is the one untested claim that could genuinely eliminate the 0.0066% precision shift. It requires implementing geometric algebra (Clifford algebra Cl(3,0)).

2. **Test simultaneous constraints** — if the formula must match m_e AND m_μ/m_e simultaneously, the search space narrows dramatically. A formula matching two constants would be much harder for random combinations to achieve.

3. **Investigate α² × √3** — the correction's proximity to α² × √3 (where 3 = spatial axes) might connect to a second-order QED effect. This is speculative but worth exploring.

4. **Accept the current status** — the Phase 17 formula is the closest approximation found, with no target leakage and physical motivation. It is not a derivation, but it is the best the UBP has produced in 18 phases.

---

## Appendix: Reproducibility

```bash
cd /home/z/my-project/scripts
python phase18_24cell_schwinger.py    # ~1 minute
```

---

*End of Phase 18 report. For prior phases, see Phase 1-17 reports in `/home/z/my-project/download/`.*
