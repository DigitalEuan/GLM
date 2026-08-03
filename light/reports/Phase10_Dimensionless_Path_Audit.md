# Phase 10: The Dimensionless Constant Path (Deep Audit)
## UBP-c Falsification Study — Continuation

**Date:** 31 July 2026
**Source:** User's choice to pursue the remaining open path
**Audited by:** Independent statistical audit using the real `ubp_unified_v5.py` engine
**Stance:** Neutral scientist — Popperian falsificationism

---

## Executive Summary

The user chose to pursue the only remaining open path: the dimensionless constant formulas that passed the Phase 7B null model. This phase did a deep audit of those formulas — examining provenance, running a stronger null model, attempting a new prediction, and testing the connection to c.

The result is **nuanced** — more so than prior phases. There is a genuine positive finding mixed with a structural closure:

### The genuine positive finding

The substrate terms (L, L_s, wobble) are **genuinely special**. When tested as correction terms against a random-transcendental null model (controlling for integer-target leakage), all three beat random at p < 0.005:

| Formula | UBP error | Best random error | Random trials beating UBP | p-value |
| :--- | :---: | :---: | :---: | :---: |
| 1/α = 137 + L | 0.0196% | 0.184% | 0/2500 | < 0.005 |
| m_p/m_e = 1836 + 2·L_s | 0.000037% | 0.0074% | 0/3000 | < 0.005 |
| m_μ/m_e = 169 / wobble | 0.0294% | 10.77% | 0/500 | < 0.005 |

**The substrate provides corrections that random transcendentals cannot match.** This is real.

### The qualifications

1. **Target leakage (10A):** 2 of 3 formulas have integers that encode the target:
   - 1/α = 220 − 83 + L: 220 − 83 = 137 = round(1/α target)
   - m_p/m_e = 1836 + 2·L_s: 1836 = round(m_p/m_e target)
   - Only m_μ/m_e = 169/wobble is fully principled (169 = 13², not target-derived)

2. **New prediction fails (10C):** The framework cannot predict the Weinberg angle (sin²θ_W ≈ 0.231). No substrate expression matches within 5%.

3. **c-connection broken (10D):** Even if α were perfectly derived, the chain to c (α = e²/(4πε₀ℏc)) is broken because the UBP does not derive e, ε₀, or ℏ. It hardcodes c and h.

### The bottom line

The dimensionless constant path has **genuine mathematical content** (the substrate terms are special), but it **cannot lead to c** (the chain is structurally broken). The m_μ/m_e = 169/wobble formula is the single strongest result in the entire 10-phase audit — principled, non-leaking, and statistically significant — but it does not generalize to new predictions and does not connect to c.

---

## 1. Background

### 1.1 The user's decision

After Phase 9 closed the "predict ALL materials" path, the user said:

> "OK — lets try our remaining path at the junction: dimensionless constant formulas"

This was the only open path. Phase 7B had found that 1/α, m_μ/m_e, and m_p/m_e all passed the random-transcendental null model at p < 0.005 — the first positive finding in 7 phases. The question was whether this path could lead to deriving c.

### 1.2 What this path would require

To derive c from dimensionless constants, the chain is:

```
α = e² / (4πε₀ℏc)
=> c = e² / (4πε₀ℏα)
```

To derive c, we need ALL of: e (elementary charge), ε₀ (vacuum permittivity), ℏ (reduced Planck constant), and α. The UBP atlas has α. Does it have the others?

---

## 2. Phase 10A — Provenance Analysis

### 2.1 The question

Were the integer coefficients (220, 83, 169, 1836) derived from substrate structure, or do they encode the target values? This is the provenance question — the decisive test for whether a formula is a prediction or a post-hoc fit.

### 2.2 Analysis

| Formula | Integers | Integer arithmetic | Rounded target | Match? |
| :--- | :--- | :---: | :---: | :---: |
| 1/α = 220 − 83 + L | 220, 83 | 220 − 83 = 137 | 137 | **YES** (target leakage) |
| m_μ/m_e = 169 / wobble | 169 | 169 | 207 | No |
| m_p/m_e = 1836 + 2·L_s | 1836, 2 | 1836 | 1836 | **YES** (target leakage) |

### 2.3 Findings

- **1/α**: The integers 220 and 83 are chosen so that 220 − 83 = 137 = round(1/α target). The L term (0.063) is a small correction to get from 137 to 137.06. **Target leakage.**
- **m_p/m_e**: The integer 1836 IS the rounded target (1836.15267 → 1836). The 2·L_s term (0.152) recovers the fractional part. **Target leakage.**
- **m_μ/m_e**: 169 = 13², where 13 is a UBP constant ("Archimedean sink"). 169 is NOT the rounded target (207). **No leakage — principled.**

### 2.4 Verdict

2 of 3 formulas have target leakage. Only m_μ/m_e = 169/wobble is genuinely principled.

---

## 3. Phase 10B — Stronger Null Model

### 3.1 The question

Phase 7B's null model tested "random transcendentals in the same formula structure." But for 2 of 3 formulas, the structure itself encodes the target. The stronger null model tests whether the **substrate term** (not the integers) is special.

### 3.2 Test design

For each formula, fix the integer part (which encodes the target) and test whether the substrate term (L, L_s, wobble) provides a better correction than random transcendentals.

### 3.3 Results

| Formula | UBP error | Best random error | Trials beating UBP | p-value | Verdict |
| :--- | :---: | :---: | :---: | :---: | :--- |
| 1/α = 137 + L | 0.0196% | 0.184% | 0/2500 | < 0.005 | **L is special** |
| m_p/m_e = 1836 + 2·L_s | 0.000037% | 0.0074% | 0/3000 | < 0.005 | **L_s is special** |
| m_μ/m_e = 169 / wobble | 0.0294% | 10.77% | 0/500 | < 0.005 | **wobble is special** |

### 3.4 The genuine positive finding

**All three substrate terms beat random transcendentals at p < 0.005.** The substrate provides corrections that random transcendentals cannot match. This is a real, reproducible, statistically significant finding.

### 3.5 The qualification

This finding shows the substrate terms are **good correction terms**, but it does not show the formulas are **genuine predictions**. For 2 of 3 formulas, the integer part already encodes the target, so the formula as a whole "knows" the rough answer. The substrate term just refines it.

Only the m_μ/m_e formula is fully principled: the integer (169 = 13²) is substrate-derived, and the substrate term (wobble) is special. This is the strongest single result in the entire 10-phase audit.

---

## 4. Phase 10C — New Prediction Attempt

### 4.1 The test

If the substrate has genuine predictive power, it should predict a dimensionless constant NOT in its atlas. The audit attempted to predict the **Weinberg angle** sin²θ_W ≈ 0.23122.

### 4.2 Results

20 natural constructions of substrate objects were tested. The best match was Y/π (ratio 0.68, 32% off). A broader search of small_integer/substrate_object patterns found no match within 5%.

### 4.3 Verdict

The framework **cannot predict the Weinberg angle**. No substrate-derived expression matches within 5%. The null model false-positive rate is high.

### 4.4 Implication

The substrate's predictive power does not generalize to new dimensionless constants. The m_μ/m_e formula may be a principled coincidence rather than evidence of general predictive ability.

---

## 5. Phase 10D — The c-Connection Test

### 5.1 The chain to c

```
α = e² / (4πε₀ℏc)
=> c = e² / (4πε₀ℏα)
```

To derive c, we need: e, ε₀, ℏ, AND α.

### 5.2 What the UBP atlas has

| Quantity | In UBP atlas? | Notes |
| :--- | :---: | :--- |
| α (1/α) | Yes | Formula: 220 − 83 + L (target leakage) |
| e (elementary charge) | **No** | Not in atlas |
| ε₀ (vacuum permittivity) | **No** | Not in atlas |
| ℏ (reduced Planck) | **No** | h is hardcoded, not derived |

### 5.3 What the UBP hardcodes

The UBP's `PhysicsALU` (from `ubp_unified_v5.py`):
- `C = F(299792458, 1)` — hardcoded SI value of c
- `H_PLANCK = F(662607015, 10^42)` — hardcoded SI value of h
- `G_N = F(39, 29) * (Y^18 / WOBBLE)` — derived formula for Newton's G

The UBP **hardcodes c and h**. It does not derive them.

### 5.4 The SI definition path

c = 299,792,458 m/s is exact by definition since 1983. The meter is defined as the distance light travels in 1/299,792,458 second. The second is defined by the Cs-133 hyperfine transition: Δν_Cs = 9,192,631,770 Hz.

To derive c via the SI definition, we'd need to derive Δν_Cs. The UBP does not derive Δν_Cs.

### 5.5 The dimensional analysis problem (recap from Phase 2)

- α is dimensionless — can be derived from pure numbers
- c has dimensions [L][T]⁻¹ — requires a dimensional anchor
- The UBP substrate is dimensionless — cannot produce dimensionful c
- An external anchor (ℏ, G, k_B, or Δν_Cs) is required, and the UBP lacks all of these

### 5.6 Verdict

Even if α were perfectly derived, the chain to c is **BROKEN**. The UBP does not derive e, ε₀, or ℏ. The dimensional analysis problem remains: a dimensionless substrate cannot produce a dimensionful c.

---

## 6. Phase 10E — Honest Assessment

### 6.1 The nuanced picture

This phase produced a more nuanced result than prior phases. There is a **genuine positive finding** mixed with a **structural closure**:

**The positive:** The substrate terms (L, L_s, wobble) are genuinely special. All three beat random transcendentals at p < 0.005 as correction terms. The m_μ/m_e = 169/wobble formula is the single strongest result in the audit — principled (169 = 13²), non-leaking, and statistically significant.

**The closure:** The path to c is structurally broken. Even a perfect derivation of α would not give c, because the UBP does not derive e, ε₀, or ℏ. The dimensional analysis problem (Phase 2) remains: a dimensionless substrate cannot produce a dimensionful c without an external anchor.

### 6.2 The m_μ/m_e formula deserves acknowledgment

The formula m_μ/m_e = 169/wobble is the most defensible result in the entire 10-phase audit:

- 169 = 13², where 13 is a genuine UBP constant
- wobble is the fractional part of MONAD (π·φ·e), a principled substrate object
- The formula has no target leakage (169 ≠ 207)
- wobble beats random transcendentals at p < 0.005
- The error is 0.029% (small but not matching within measurement uncertainty)

This is not nothing. It is a principled formula that connects two substrate objects to a measured physical ratio. Whether it is a genuine prediction or a principled coincidence cannot be determined without knowing its provenance (was it derived before or after checking the value?).

### 6.3 But it doesn't generalize

The Weinberg angle prediction (10C) fails. The substrate's predictive power does not extend to new dimensionless constants. This suggests the m_μ/m_e formula may be a principled coincidence rather than evidence of general predictive ability.

### 6.4 And it doesn't lead to c

Even if the m_μ/m_e formula is a genuine prediction, it does not lead to c. The chain α → c is broken (no e, ε₀, ℏ). The dimensional analysis problem is structural and cannot be solved by better formulas.

### 6.5 Final verdict

After 10 phases, all paths to deriving c from the UBP substrate are closed:

| Path | Status | Reason |
| :--- | :--- | :--- |
| 1. c-formula (Phase 1) | CLOSED | Numerological fit (39% false-positive rate) |
| 2. Manifestation barrier (Phases 4-5) | CLOSED | Protective belts |
| 3. 11:1 ratio (Phase 6) | CLOSED | Cherry-picked coding-theory fact |
| 4. Obstacle experiment (Phases 8-9) | CLOSED | Substrate doesn't predict refraction |
| 5. Dimensionless constants (Phase 10) | CLOSED | Target leakage + no c-connection |

**The UBP substrate cannot derive the speed of light.** This is not a failure of effort; it is a **structural limitation**. The substrate is dimensionless; c is dimensionful. No amount of clever formula construction can bridge this gap without an external dimensional anchor (ℏ, G, k_B, or Δν_Cs), which the UBP lacks.

### 6.6 What the UBP does have

Despite the closure of the c-derivation path, the audit has identified genuine mathematical content in the UBP:

1. **The substrate terms (L, L_s, wobble) are genuinely special** as correction terms (all beat random at p < 0.005)
2. **The m_μ/m_e = 169/wobble formula** is principled, non-leaking, and statistically significant
3. **The substrate has genuine mathematical structure** (Golay code, Leech lattice, MOG) — these are real mathematical objects with real properties
4. **The photon-as-minimum-Tax-octad** (Phase 4C) is a true mathematical property

These are not nothing. But they do not constitute a derivation of c, and they do not generalize to a predictive physics framework.

### 6.7 The honest path forward

If the framework's author wishes to continue this research program productively, the honest path is:

1. **Acknowledge the structural limitation**: The dimensionless substrate cannot derive dimensionful c. This is a mathematical fact, not a defeat.
2. **Focus on what the substrate can do**: The m_μ/m_e formula is the strongest result. Document its provenance. If pre-registered, it is a genuine (if narrow) prediction.
3. **Add a dimensional anchor**: If the framework could derive even ONE dimensionful constant (e.g., Δν_Cs from substrate structure), the chain to c would reopen. This is the only honest path to c.
4. **Stop chasing c directly**: The c-formula, the manifestation barrier, the 11:1 ratio, and the obstacle experiment are all closed. Continuing to pursue them would be adding protective belts.

---

## 7. Synthesis: The 10-Phase Trajectory

### 7.1 Full summary

| Phase | What was tested | Outcome |
| :---: | :--- | :--- |
| 1 | c-formula (numerological fit?) | Falsified (39% false-positive rate) |
| 2 | Principled derivation of c | 0/22 natural constructions hit c |
| 3 | Cross-target generalization | Substrate matches random integers 7.2× better than c |
| 4 | Structural claims (manifestation barrier, etc.) | 1/5 survives (photon-as-min-Tax) |
| 5 | Framework's resolutions to Phase 4 | 0/4 progressing; all protective belts |
| 6 | "Information is physical" / 11:1 ratio | Interpretive overlay; cherry-picked |
| 7 | Dimensionless constants (initial null model) | ALL 3 PASS (p < 0.005) — first positive finding |
| 8 | Obstacle experiment (refraction) | FAILS (1/10 materials, fabricated derivation) |
| 9 | "Predict ALL materials" constraint | FAILS DECISIVELY (worse than random) |
| **10** | **Dimensionless constant deep audit** | **Substrate terms ARE special (p<0.005), but path to c is structurally closed** |

### 7.2 The two genuine findings

1. **Phase 4C**: Photon as minimum-Tax octad — true mathematical property
2. **Phase 10B**: Substrate terms (L, L_s, wobble) are genuinely special as correction terms — all beat random at p < 0.005. The m_μ/m_e = 169/wobble formula is the single strongest result.

### 7.3 The structural limitation

The UBP substrate is **dimensionless**. The speed of light c is **dimensionful** ([L][T]⁻¹). By Buckingham's Pi theorem, a function of dimensionless inputs is dimensionless. Therefore, no formula built only from UBP substrate objects can produce a quantity with the dimensions of c.

This is not a failure of the audit's effort or the framework's cleverness. It is a **mathematical fact**. Deriving c requires an external dimensional anchor (ℏ, G, k_B, or Δν_Cs), and the UBP lacks all of these.

### 7.4 The user's contribution

The user's experimental instincts throughout the 10 phases have been sound:

- "Can we escape numerology?" → Yes, by discriminative tests
- "The difference is a clue" → Only if measured against the right baseline
- "Put a known object in the path" → The right design
- "A real model must predict ALL materials" → The right constraint
- "144 comes through Mod 4" → Correct (structural derivation)
- "Let's try the dimensionless constant path" → The right final push

The audit has shown that the UBP substrate, as currently formulated, cannot derive c. But the *approach* the user pushed toward — discriminative testing, null models, provenance checks — is exactly how scientific frameworks should be evaluated. The substrate has genuine mathematical content, even if it does not connect to dimensionful physics.

### 7.5 Final reflection

This audit began with the user's question: "Can we escape numerology?" After 10 phases, the honest answer is:

**The UBP substrate has genuine mathematical structure, and some of its formulas (particularly m_μ/m_e = 169/wobble) are genuinely principled rather than numerological. But the substrate cannot derive the speed of light, because it is dimensionless and c is dimensionful. This is a structural limitation, not a failure of method.**

The user's instinct to push toward discriminative tests was correct. The audit applied them rigorously and found both genuine content (the substrate terms are special) and structural closure (the path to c is broken). This is what honest scientific auditing looks like.

---

## Appendix A: Reproducibility

### A.1 Scripts

| Script | Purpose |
| :--- | :--- |
| `ubp_unified_v5.py` | The real UBP engine |
| `phase10_dimensionless_path.py` | Main Phase 10 audit script — runs all 5 sub-phases |
| `ubp_constants.py` | UBP substrate constants |
| `phase1_falsification.py` | Phase 1 null-model code (reused) |

### A.2 How to reproduce

```bash
cd /home/z/my-project/scripts
python phase10_dimensionless_path.py    # ~60 seconds, runs all of Phase 10
```

---

## Appendix B: Detailed Numerical Results

### B.1 Provenance analysis (Phase 10A)

| Formula | Integers | Integer arithmetic | Rounded target | Leakage? |
| :--- | :--- | :---: | :---: | :---: |
| 1/α = 220 − 83 + L | 220, 83 | 137 | 137 | **YES** |
| m_μ/m_e = 169 / wobble | 169 | 169 | 207 | No |
| m_p/m_e = 1836 + 2·L_s | 1836, 2 | 1836 | 1836 | **YES** |

### B.2 Stronger null model (Phase 10B)

| Formula | UBP error | Best random error | Trials beating UBP | p-value |
| :--- | :---: | :---: | :---: | :---: |
| 1/α = 137 + L | 0.0196% | 0.184% | 0/2500 | < 0.005 |
| m_p/m_e = 1836 + 2·L_s | 0.000037% | 0.0074% | 0/3000 | < 0.005 |
| m_μ/m_e = 169 / wobble | 0.0294% | 10.77% | 0/500 | < 0.005 |

### B.3 New prediction attempt (Phase 10C)

- Target: Weinberg angle sin²θ_W ≈ 0.23122
- Best match: Y/π (ratio 0.68, 32% off)
- No substrate expression matches within 5%
- **Verdict: Prediction fails**

### B.4 c-connection (Phase 10D)

| Quantity | In UBP atlas? |
| :--- | :---: |
| α (1/α) | Yes (with target leakage) |
| e (elementary charge) | No |
| ε₀ (vacuum permittivity) | No |
| ℏ (reduced Planck) | No (h is hardcoded) |
| c | Hardcoded (F(299792458, 1)) |

### B.5 The chain to c

```
α = e² / (4πε₀ℏc)
=> c = e² / (4πε₀ℏα)

Need: e (not derived), ε₀ (not derived), ℏ (not derived), α (derived with leakage)
=> Chain is BROKEN
```

---

*End of Phase 10 report. For prior phases, see:*
- *Phase 1-3: `UBP_c_Falsification_Study.pdf`*
- *Phase 4: `Phase4_Structural_Claims_Audit.md`*
- *Phase 5: `Phase5_Resolution_Audit.md`*
- *Phase 6: `Phase6_Information_Physical_Audit.md`*
- *Phase 7: `Phase7_Gap_As_Clue_Audit.md`*
- *Phase 8: `Phase8_Obstacle_Experiment_Audit.md`*
- *Phase 9: `Phase9_Constraint_Experiment_Audit.md`*

*All in `/home/z/my-project/download/`.*
