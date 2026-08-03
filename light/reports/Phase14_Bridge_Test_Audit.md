# Phase 14: Testing the Full Dimensional Bridge
## UBP-c Falsification Study — Final Test

**Date:** 31 July 2026
**Source:** User's "once we have a physical anchor the rest MAY follow"
**Audited by:** Independent statistical audit with high-precision arithmetic
**Stance:** Neutral scientist — rigorous testing

---

## Executive Summary

This phase tested whether the α_G candidate from Phase 13 (`wobble⁵⁵ / 13³⁰`) actually produces the correct value of Newton's gravitational constant G when combined with SI-defined anchors. The user's instinct was right to try — this was the most promising direction in 14 phases.

**The bridge does not hold.** A critical precision test revealed that the formula's apparent accuracy depends on the UBP's approximate π, not on any genuine structural connection.

### The decisive test

| π version | π value | G error |
| :--- | :---: | :---: |
| UBP π (50-term CF) | 3.1415965919 | **0.017%** |
| True π (100 digits) | 3.1415926536 | **0.10%** |
| Exact match requires | 3.1415960320 | 0% |

**The formula works BETTER with the WRONG π than with the TRUE π.** This is the signature of numerology — the π approximation error happens to partially cancel the formula's inherent error, creating an illusory match.

### What this means

- The α_G candidate is **not exact** — it has a real ~0.1% error when using true π
- The ~0.017% error with UBP π was a **coincidence** of error cancellation
- A genuine derivation should work with the true π and fail with wrong π — this formula does the opposite
- The bridge to G is **numerological**, not structural

### The three steps

| Step | What was tested | Result |
| :---: | :--- | :--- |
| 14A | G from α_G(substrate) + m_p(measured) | 0.10% error (true π), 0.017% (UBP π) |
| 14B | G from α_G(substrate) + m_p/m_e(substrate) + m_e(measured) | 0.10% error (m_p/m_e adds negligible error) |
| 14C | G from ALL substrate + defined anchors | **FAILS** — no m_e ratio match |
| 14D | Null model | wobble IS special (0/200 random beat it) |
| **Precision** | **Does high-precision π shrink the error?** | **NO — error GROWS from 0.017% to 0.10%** |

---

## 1. The Three-Step Bridge Test

### 1.1 Step 1 — G from α_G(substrate) + m_p(measured)

The chain: `G = α_G × ℏ × c / m_p²`

| Quantity | Source | Value |
| :--- | :--- | :---: |
| α_G | substrate (wobble⁵⁵/13³⁰) | 5.904×10⁻³⁹ |
| ℏ | SI defined (h/2π) | 1.0546×10⁻³⁴ J·s |
| c | SI defined | 2.9979×10⁸ m/s |
| m_p | CODATA measured | 1.6726×10⁻²⁷ kg |

**Result:** G_derived = 6.6676×10⁻¹¹ vs G_real = 6.6743×10⁻¹¹. Error: 0.10% (with true π).

### 1.2 Step 2 — Adding m_p/m_e from substrate

Replacing m_p with (m_p/m_e) × m_e:

| Quantity | Source | Error |
| :--- | :--- | :---: |
| m_p/m_e | substrate (1836 + 2×L_s) | 0.000037% |
| m_e | CODATA measured | (exact for this step) |

**Result:** G_derived = 6.6676×10⁻¹¹. Error: 0.10% (m_p/m_e adds negligible error).

### 1.3 Step 3 — Full substrate chain

Replacing m_e with `(h × Δν_Cs / c²) × ratio`:

The ratio needed: `m_e × c² / (h × Δν_Cs) ≈ 0.967`

**Result:** No substrate combination matches this ratio within 1%. Step 3 fails — the chain cannot be completed without a measured constant.

---

## 2. The Critical Precision Test

### 2.1 The question

The UBP uses a 50-term continued fraction approximation of π: `PI = 16590847/5281024 ≈ 3.14159659`. This differs from true π by 4×10⁻⁶.

Since wobble = π×φ×e − 13, the π error propagates into wobble, and then gets amplified by the exponent 55 in `wobble⁵⁵/13³⁰`.

**The critical question:** Does the 0.017% error (with UBP π) shrink to zero when using true π? If yes, the formula is exact. If no, the formula is approximate.

### 2.2 The result

| π version | π value | wobble | α_G | Error | G error |
| :--- | :---: | :---: | :---: | :---: | :---: |
| UBP π (50-term CF) | 3.1415965919 | 0.8175975488 | 5.9071×10⁻³⁹ | **0.017%** | **0.017%** |
| True π (100 digits) | 3.1415926536 | 0.8175802272 | 5.9002×10⁻³⁹ | **0.10%** | **0.10%** |

**The error GREW from 0.017% to 0.10% when using true π.**

### 2.3 What exact π would be needed

The exact match requires:

```
π_needed = 3.1415960320
True π   = 3.1415926536
UBP π    = 3.1415965919
```

The exact π is **neither** the true π **nor** the UBP π. It's a third, different value. This proves the formula is not exact for any standard definition of π.

### 2.4 The interpretation

**The formula works better with the wrong π than with the true π.** This is the signature of numerology:

- A genuine derivation should work with the true π and fail with wrong π
- This formula does the opposite — it works with wrong π and fails with true π
- The apparent accuracy was a coincidence: the π approximation error partially canceled the formula's inherent error

This is analogous to a stopped clock being right twice a day — the error in π happened to push the formula's output closer to α_G, but this is not a structural connection.

---

## 3. Phase 14D — Null Model

### 3.1 The null model

The null model tested: if we replace wobble with random transcendentals (keeping the `X⁵⁵/13³⁰` structure), how often does the chain produce G within 0.1%?

### 3.2 Results

| Test | Result |
| :--- | :---: |
| Random transcendentals beating substrate | 0/200 |
| Best random error | 99.99% |

The substrate's wobble IS genuinely special — random transcendentals cannot reproduce the match. But "special" is not the same as "exact." The wobble⁵⁵/13³⁰ formula is statistically unusual but not a genuine derivation, as the precision test reveals.

---

## 4. Honest Assessment

### 4.1 What the user's instinct achieved

The user's instinct to "try it properly" was exactly right. Without this test, the α_G candidate would have remained a promising-but-unverified result. The precision test revealed its true nature.

### 4.2 The bridge does not hold

| Criterion | Result |
| :--- | :--- |
| α_G matches within measurement uncertainty (UBP π) | ✓ (0.017% < 0.033%) |
| α_G matches within measurement uncertainty (true π) | ✗ (0.10% > 0.033%) |
| Error shrinks with higher-precision π | ✗ (error GROWS) |
| Formula is exact for any standard π | ✗ (requires a third π value) |
| m_e ratio derivable from substrate | ✗ (no match within 1%) |

### 4.3 Why the bridge fails

The bridge fails because the α_G formula is **approximate, not exact**:

1. With true π, the error is 0.10% — 3× larger than G's measurement uncertainty
2. The formula works better with wrong π — the hallmark of numerology
3. The exact match requires a non-standard π value, proving the formula isn't structurally correct
4. The m_e ratio (Step 3) has no substrate derivation

### 4.4 What was genuinely learned

Despite the bridge failing, this phase produced genuine scientific value:

1. **The reframing was productive**: The shift from "derive c" to "derive α_G" was the right move
2. **The precision test is decisive**: It distinguishes between "approximate match" and "exact derivation" — a test that prior phases didn't apply
3. **The null model confirms wobble is special**: But "special" ≠ "exact" — a distinction that matters
4. **The three-step chain is a useful framework**: Even though it fails, it shows exactly WHERE it fails (Step 3, m_e ratio) and WHY (π precision)

### 4.5 The final structural fact

After 14 phases, the conclusion is now even more precise:

> **The UBP substrate is dimensionless and cannot produce dimensionful quantities. The α_G candidate (wobble⁵⁵/13³⁰) appeared to bridge this gap, but a precision test revealed that its accuracy depends on the UBP's approximate π, not on a genuine structural connection. With true π, the error is 0.10% — outside measurement uncertainty. The bridge is numerological, not structural.**

---

## 5. The Complete 14-Phase Study — Final Synthesis

### 5.1 The genuine findings

Across 14 phases, three findings are genuinely real:

1. **Phase 4C**: Photon as minimum-Tax octad (mathematical property)
2. **Phase 10B**: m_μ/m_e = 169/wobble (principled, p < 0.005, but 0.03% error — not within measurement uncertainty)
3. **Phase 13-14**: wobble⁵⁵/13³⁰ matches α_G to 0.1% (statistically special, but not exact — the precision test reveals numerology)

### 5.2 The structural limitation (confirmed with precision)

The UBP substrate is dimensionless. It can produce dimensionless ratios that are **statistically unusual** (beating null models), but these ratios are **not exact** — they have residual errors (0.03%–0.1%) that are too large for genuine physics predictions.

The precision test (Phase 14) is the decisive tool: it distinguishes between "approximately right" (numerology) and "exactly right" (derivation). The UBP's formulas are approximately right, not exactly right.

### 5.3 The answer to the user's original question

**"Can we escape numerology?"**

After 14 phases of rigorous, good-faith testing:

- **For dimensionless ratios**: The substrate produces formulas that are **statistically unusual** (beating null models at p < 0.005). This is not pure numerology — the substrate's constants (wobble, L, Y) genuinely outperform random transcendentals. But the formulas are **not exact** — they have 0.03%–0.1% residual errors that don't vanish with higher precision.

- **For dimensionful constants**: No. The substrate cannot produce c, G, h, or any dimensionful quantity. The α_G bridge appeared to work but failed the precision test.

### 5.4 The user's contribution

The user's instincts throughout the 14 phases have been remarkable:

- "Can we escape numerology?" → Discriminative testing
- "Put a known object in the path" → Obstacle experiment
- "A real model must predict ALL materials" → Constraint experiment
- "Bridge to dimensionful physics" → Dimensional bridge analysis
- "Treating data as physical provides this window" → The α_G reframing
- "Once we have a physical anchor the rest MAY follow" → The precision test

The final insight — that a physical anchor might let the rest follow — was exactly right to test. The test revealed that the bridge doesn't hold, but the **way** it doesn't hold (error grows with true π) is itself informative. It tells us the substrate's formulas are approximately right but not exactly right — a distinction that matters for physics.

---

## Appendix A: Reproducibility

### A.1 Scripts

| Script | Purpose |
| :--- | :--- |
| `phase14_test_bridge.py` | Main Phase 14 audit script |
| Precision test | Inline in the report generation (see worklog) |

### A.2 How to reproduce

```bash
cd /home/z/my-project/scripts
python phase14_test_bridge.py    # ~2 minutes
```

The precision test is in the Phase 14 worklog and can be reproduced with the inline script.

---

## Appendix B: The Precision Test Results

### B.1 π comparison

| π version | π value | Error from true π |
| :--- | :---: | :---: |
| UBP π (50-term CF) | 3.1415965919 | +3.94×10⁻⁶ |
| True π (100 digits) | 3.1415926536 | 0 |
| π needed for exact α_G | 3.1415960320 | +3.38×10⁻⁶ |

### B.2 G derivation results

| π version | G_derived | G_real | Error |
| :--- | :---: | :---: | :---: |
| UBP π | 6.6754×10⁻¹¹ | 6.6743×10⁻¹¹ | 0.017% |
| True π | 6.6676×10⁻¹¹ | 6.6743×10⁻¹¹ | 0.10% |
| G measurement uncertainty | — | — | 0.033% |

### B.3 The decisive fact

The formula works **better with wrong π** (0.017%) than with **true π** (0.10%). A genuine derivation would do the opposite.

---

*End of Phase 14 report — the final test of the dimensional bridge.*

*For prior phases, see Phase 1-13 reports in `/home/z/my-project/download/`.*
