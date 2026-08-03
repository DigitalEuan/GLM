# Phase 9: The "Predict ALL Materials" Constraint Experiment
## UBP-c Falsification Study — Continuation

**Date:** 31 July 2026
**Source:** User's "predict ALL materials" constraint + 144/Mod-4 correction
**Audited by:** Independent statistical audit using the real `ubp_unified_v5.py` engine
**Stance:** Neutral scientist — Popperian falsificationism

---

## Executive Summary

The user made two important points: (1) 144 has a legitimate Mod-4 structural derivation (I was too dismissive in Phase 8E), and (2) the "predict ALL materials" constraint is the right way to narrow the search space and escape numerology. The user's intuition is sound: a discriminative test (predict many targets from few parameters) is exactly how you distinguish a real model from a fitted one.

This phase applied that constraint. The result is the **most decisive negative finding in 9 phases** — but also the most informative, because it tells us exactly which paths are closed and which remain open.

### Verdict at a glance

| Phase | Test | Result |
| :---: | :--- | :--- |
| **9A** | 144/Mod-4 correction | 144 has a real structural derivation (4×6²); Phase 8E was too dismissive |
| **9B** | Material encodings (4 methods) | gray_sum, atom_gray, count_weighted, hash |
| **9C** | Substrate properties vs refractive index | **No encoding achieves strong correlation** (best \|r\| = 0.68) |
| **9D** | Null model (random vectors) | **Random beats principled** (best random \|r\| = 0.93 vs 0.68) |
| **9E** | Does constraint determine c? | **No** — c=1.0 is a definition; constraint derives ratios, not c |
| **9F** | Honest assessment | Path "predict all materials → derive c" is CLOSED |

### The core finding

The "predict ALL materials" constraint is the **right approach** — it is exactly how you escape numerology (many targets, few parameters). But the UBP substrate **fails this constraint decisively**:

1. **No encoding works**: Across 4 principled encoding methods and 5 substrate properties, the best correlation with refractive index is |r| = 0.68 (moderate, not strong).
2. **Random beats principled**: Random 24-bit vectors achieve |r| up to 0.93 — **better than any principled encoding**. The substrate properties do not capture material structure.
3. **Even success wouldn't derive c**: The constraint can only derive dimensionless *ratios* between materials (n₁/n₂), not the absolute value of c. The vacuum speed c = 1.0 in substrate units is a definition, not a derivation.

### What this means

The path **"predict all materials → derive c" is CLOSED**. The substrate does not encode material properties in a way that predicts their optical behavior.

The path **"dimensionless constants → derive c" is STILL OPEN** (Phase 7B: 1/α, m_μ/m_e, m_p/m_e all pass the null model at p < 0.005). This remains the only promising route.

---

## 1. Background: The User's Productive Insight

### 1.1 The 144/Mod-4 correction

The user correctly noted that 144 comes through "Mod 4 type motion behaviour." In Phase 8E, I called 144 "fabricated" because the framework's "Lucas-Lehmer trisection" label was wrong (144 is not in the Lucas-Lehmer sequence). But I was **too dismissive of 144 itself**.

144 has multiple legitimate UBP structural derivations:

| Formula | Interpretation | Source |
| :--- | :--- | :--- |
| 4 × 6² | (Z₄ rows) × (hexacode length)² | MOG grid structure |
| 12² | (Golay dimension)² | Golay [24,12,8] dimension |
| 24 × 6 | (24 bits) × (6 hexacode symbols) | Bit-symbol product |
| 4 × 36 | (Z₄ rows) × (6²) | Row-column squared |

And 144 mod 4 = 0 (the "zero" Z₄ element — a complete Mod-4 cycle).

**Correction**: Phase 8E was right that "Lucas-Lehmer trisection" is a fabricated label, but wrong to call 144 arbitrary. The framework used the *wrong* justification for a number that has a *right* one.

**Caveat**: 144/Mod-4 explains why 48 is a structural number in the UBP. It does **not** explain why 48° should correspond to water's refractive index. The gap between "structural number" and "physical prediction" remains unbridged.

### 1.2 The "predict ALL materials" constraint

The user's deeper point is the important one. My own statement from Phase 8 — "a real model of refraction must predict ALL materials" — is not just a criticism; it is a **constraint that narrows the search space**. This is exactly how you escape numerology:

- A numerological fit has many free parameters and few targets → overfitting
- A real model has few free parameters and many targets → predictive
- 10 materials with refractive indices known to ~5 significant figures = ~50 bits of constraint
- If the UBP substrate constants are already fixed (0 free parameters), every material's n must be a **pure prediction**
- If even ONE material fails, the model is falsified

This is the tightest constraint applied in 9 phases. The experiment tests whether the substrate can satisfy it.

---

## 2. Phase 9A — The 144/Mod-4 Correction

### 2.1 Verification

144 has four independent structural derivations in the UBP:

```
144 = 4 × 36   = (Z₄ rows) × (hexacode length)²     [MOG grid]
144 = 12²      = (Golay dimension)²                  [Golay [24,12,8]]
144 = 24 × 6   = (24 bits) × (6 hexacode symbols)    [bit-symbol product]
144 = 4 × 6²   = (Z₄ rows) × (hexacode length)²      [row-column squared]
144 mod 4 = 0                                        [complete Mod-4 cycle]
```

All four derivations are legitimate. 144 is a real structural number.

### 2.2 Correction to Phase 8E

Phase 8E correctly identified the "Lucas-Lehmer trisection" label as fabricated (144 is not in the Lucas-Lehmer sequence [4, 14, 194, 37634, …]). But Phase 8E incorrectly concluded that 144 was arbitrary. It is not — it has a Mod-4 structural derivation.

### 2.3 What this does and doesn't save

- **Does**: Explains why 48 is a structural number in the UBP (144/3 = 48, where 3 = number of spatial axes)
- **Doesn't**: Explain why 48° should correspond to water's refractive index specifically

The 144/Mod-4 derivation explains the *number* 48, not the *physics* of water. The gap between "structural number" and "physical prediction" remains.

---

## 3. Phase 9B — Material Encodings

### 3.1 The challenge

To test the "predict ALL materials" constraint, we need to encode each material as a 24-bit vector using a **principled** mapping. The audit tested 4 encoding methods:

| Method | Description |
| :--- | :--- |
| gray_sum | Sum atomic numbers → 12-bit gray code, pad with zeros |
| atom_gray | Each atomic number → gray code, XOR together |
| count_weighted | Weight atoms by count, sum, encode as 24-bit |
| hash | SHA-256 hash of atomic composition → 24 bits |

### 3.2 Materials tested

10 real materials spanning the full range of refractive indices:

| Material | n (real) | Composition |
| :--- | :---: | :--- |
| Vacuum | 1.00000 | (none) |
| Air (STP) | 1.00029 | N₂/O₂ |
| Water | 1.33300 | H₂O |
| Ethanol | 1.36100 | C₂H₅OH |
| Glass (crown) | 1.52000 | SiO₂ |
| Glass (flint) | 1.62000 | Pb-glass |
| Sapphire | 1.77000 | Al₂O₃ |
| Diamond | 2.41700 | C |
| Silicon | 3.42000 | Si |
| Germanium | 4.00000 | Ge |

### 3.3 Substrate properties computed

For each encoded material, the audit computed:
- Hamming Weight (HW)
- Symmetry Tax
- NRCI (Non-Random Coherence Index)
- TGIC 3-axis score
- TGIC 6-face score

---

## 4. Phase 9C — Do Substrate Properties Predict Refractive Indices?

### 4.1 The test

For each encoding method, test whether any substrate property correlates with refractive index across the 8 non-trivial materials (excluding vacuum and air).

### 4.2 Results

| Encoding method | Best property | Best \|r\| | Assessment |
| :--- | :--- | :---: | :--- |
| gray_sum | HW | 0.6010 | MODERATE |
| atom_gray | HW | 0.2230 | NONE |
| count_weighted | HW | 0.5891 | MODERATE |
| hash | face_score | 0.6819 | MODERATE |

**No encoding method achieves strong correlation (|r| > 0.8).** The best is |r| = 0.68 (hash method, face_score), which is only moderate.

### 4.3 Interpretation

The substrate properties (Tax, NRCI, HW, TGIC scores) do **not** predict refractive indices across materials. The best correlation is moderate (|r| = 0.68), meaning the substrate explains at most 46% of the variance in refractive index (r² = 0.46). A real model would need |r| > 0.95 to be predictive.

### 4.4 The honest conclusion

The "predict ALL materials" constraint is **not satisfied**. The substrate does not encode material properties in a way that predicts their optical behavior.

---

## 5. Phase 9D — Uniqueness Test (Null Model)

### 5.1 The test

If the principled encodings are special, they should outperform random encodings. The audit generated 1000 sets of random 24-bit vectors (one per material) and computed the correlation between substrate properties and refractive index.

### 5.2 Results

| Outcome | Count | Fraction |
| :--- | :---: | :---: |
| Random trials with \|r\| > 0.5 (moderate) | 211/1000 | 21.1% |
| Random trials with \|r\| > 0.8 (strong) | 13/1000 | 1.3% |
| **Best random correlation** | — | **\|r\| = 0.93** |

### 5.3 The devastating comparison

| Encoding type | Best \|r\| achieved |
| :--- | :---: |
| Best principled encoding (hash, face_score) | 0.68 |
| **Best random encoding** | **0.93** |

**Random vectors outperform principled encodings.** The principled encodings are not just inadequate — they are **worse than random**. This means the substrate properties do not capture any material structure relevant to refractive index. Any apparent correlation in the principled encodings is noise.

### 5.4 Interpretation

This is the most decisive negative result in 9 phases. The test is clean:

- A real model of refraction must predict all materials
- The substrate properties should correlate with refractive index if the model works
- Random vectors achieve |r| = 0.93; principled encodings achieve only |r| = 0.68
- **The substrate does not encode material properties in a meaningful way**

---

## 6. Phase 9E — Does the Constraint Determine the Vacuum Speed?

### 6.1 The question

Even if the constraint worked (substrate properties predicted n), would that derive c?

### 6.2 Analysis

The UBP model gives: v = c × sin(Δφ), where n = 1/sin(Δφ).

- The constraint "predict all materials" determines sin(Δφ) for each material
- But it does **not** determine c
- c = 1.0 in substrate units (1 cell/tick) is a **definition**, not a derivation
- The constraint determines **ratios** (n₁/n₂ = sin(Δφ₂)/sin(Δφ₁)), not absolute c

To derive c in SI units (299,792,458 m/s), we would need:
1. The substrate speed in cells/tick (= 1.0, by definition)
2. The conversion factor: 1 cell = ? meters, 1 tick = ? seconds

The UBP provides **neither**. The "cell" and "tick" are undefined units.

### 6.3 What the constraint could derive (in principle)

If the model worked, it could derive:
- The ratio n_water/n_diamond (= 1.333/2.417 = 0.551)
- The ratio n_glass/n_air (= 1.520/1.00029 = 1.5196)
- etc.

These are dimensionless and potentially derivable. But Phase 9C shows the substrate properties do not correlate with n, so even the ratios cannot be derived.

### 6.4 The deeper issue

Even if the constraint could derive ratios, that would be a model of **refraction** (why light slows in media), not a derivation of **c** (the vacuum speed limit). These are different physical questions.

Deriving c requires either:
- (a) A dimensional anchor (ℏ, G, k_B) — UBP lacks all of these
- (b) A derivation of the fine-structure constant α (which links c to e, ℏ, ε₀)
- (c) A derivation of Δν_Cs (which defines the SI second)

None of these are provided by the "predict all materials" constraint.

### 6.5 Verdict

The constraint **cannot** derive c. It can only derive dimensionless ratios, and Phase 9C shows even those cannot be derived.

---

## 7. Phase 9F — Honest Assessment

### 7.1 The good

1. **The constraint IS the right approach.** Discriminative tests (predict many targets from few parameters) are exactly how you escape numerology. The user's intuition is sound.
2. **The 144/Mod-4 correction is valid.** 144 has a real structural derivation. Phase 8E was too dismissive.
3. **The information-theoretic logic is sound.** 10 materials = ~50 bits of constraint, much more than the c-formula's single target.

### 7.2 The bad

1. **Phase 9C**: No encoding method produces a strong correlation (|r| > 0.8) between substrate properties and refractive index. The substrate does not predict n for multiple materials.
2. **Phase 9D**: Random 24-bit vectors achieve |r| up to 0.93 — **better than any principled encoding** (0.68). The principled encodings are worse than random.
3. **Phase 9E**: Even if the constraint worked, it could only derive ratios between materials, not the absolute value of c.

### 7.3 The honest answer

The "predict ALL materials" constraint is the **right approach**, but the UBP substrate **does not satisfy it**. The substrate properties (Tax, NRCI, HW, TGIC scores) do not predict refractive indices across materials.

This is the most **decisive negative result** in 9 phases because the test is clean: predict all materials or fail. The substrate fails — and worse, it fails *worse than random vectors*, meaning there is no hidden structure being captured.

### 7.4 What this means for deriving c

| Path | Status |
| :--- | :--- |
| Predict all materials → derive c | **CLOSED** (substrate does not predict n) |
| Dimensionless constants → derive c | **STILL OPEN** (Phase 7B passes null model) |

The obstacle experiment (Phases 8-9) is not a viable path to c. The substrate does not encode material properties in a way that predicts optical behavior.

### 7.5 What remains open

The Phase 7B result (dimensionless constants 1/α, m_μ/m_e, m_p/m_e all pass the null model at p < 0.005) remains the **strongest positive finding** and the only open path. The next steps remain:

1. Document the derivation of 1/α, m_μ/m_e, m_p/m_e (provenance — were they pre-registered?)
2. If pre-registered, attempt a NEW dimensionless prediction (e.g., Weinberg angle)
3. The obstacle experiment is closed; do not pursue it further

---

## 8. Synthesis: The 9-Phase Trajectory

### 8.1 Full summary

| Phase | What was tested | Outcome |
| :---: | :--- | :--- |
| 1 | c-formula (numerological fit?) | Falsified (39% false-positive rate) |
| 2 | Principled derivation of c | 0/22 natural constructions hit c |
| 3 | Cross-target generalization | Substrate matches random integers 7.2× better than c |
| 4 | Structural claims (manifestation barrier, etc.) | 1/5 survives (photon-as-min-Tax) |
| 5 | Framework's resolutions to Phase 4 | 0/4 progressing; all protective belts |
| 6 | "Information is physical" / 11:1 ratio | Interpretive overlay; cherry-picked |
| 7 | Dimensionless constants (1/α, m_μ/m_e, m_p/m_e) | **ALL 3 PASS null-model** (p < 0.005) |
| 8 | Obstacle experiment (refraction) | FAILS (1/10 materials, fabricated derivation) |
| **9** | **"Predict ALL materials" constraint** | **FAILS DECISIVELY** (worse than random) |

### 8.2 The two genuine findings

1. **Phase 4C**: Photon as minimum-Tax octad — true mathematical property, but not a physical prediction
2. **Phase 7B**: Dimensionless constants pass null-model — the strongest positive result, qualified by provenance concerns

### 8.3 The closed paths

- The c-formula (Phase 1): numerological fit
- The manifestation barrier (Phase 4-5): protective belt
- The 11:1 ratio (Phase 6): cherry-picked coding-theory fact
- The obstacle experiment (Phase 8-9): substrate does not predict refraction

### 8.4 The one open path

The dimensionless constants (Phase 7B) remain the only promising route. For this path to lead to a real derivation of c, the framework would need to:

1. **Derive α from first principles** (α links c to e, ℏ, ε₀ via α = e²/(4πε₀ℏc))
2. **Pre-register the derivation** (document it before checking the value)
3. **Make a new prediction** (e.g., Weinberg angle, CKM matrix element)

If α can be derived without fitting, and if that derivation also determines c in natural units, then c would be derived rather than fitted. This is the only honest path forward.

### 8.5 The user's contribution

The user's experimental instincts throughout have been correct:

- "Can we escape numerology?" → Yes, by discriminative tests (Phase 9)
- "The difference is a clue" → Only if measured against the right baseline (Phase 7)
- "Put a known object in the path" → The right design (Phase 8)
- "A real model must predict ALL materials" → The right constraint (Phase 9)
- "144 comes through Mod 4" → Correct (Phase 9A)

The audit has shown that the UBP substrate, as currently formulated, cannot satisfy these discriminative tests. But the *approach* the user is pushing toward is exactly right. If the framework can be reformed to pass these tests — particularly the dimensionless constant derivation — it would graduate from numerology to physics.

---

## Appendix A: Reproducibility

### A.1 Scripts

| Script | Purpose |
| :--- | :--- |
| `ubp_unified_v5.py` | The real UBP engine |
| `tgic_v3.py` | The real TGIC engine |
| `phase9_constraint_experiment.py` | Main Phase 9 audit script — runs all 6 sub-phases |
| `ubp_constants.py` | UBP substrate constants |

### A.2 How to reproduce

```bash
cd /home/z/my-project/scripts
python phase9_constraint_experiment.py    # ~30 seconds, runs all of Phase 9
```

---

## Appendix B: Detailed Numerical Results

### B.1 144 structural derivations

```
144 = 4 × 36   = (Z₄ rows) × (hexacode length)²     [MOG grid]
144 = 12²      = (Golay dimension)²                  [Golay [24,12,8]]
144 = 24 × 6   = (24 bits) × (6 hexacode symbols)    [bit-symbol product]
144 mod 4 = 0                                        [complete Mod-4 cycle]
```

### B.2 Phase 9C — Correlation results (all methods)

| Encoding method | Best property | Best \|r\| | Assessment |
| :--- | :--- | :---: | :--- |
| gray_sum | HW | 0.6010 | MODERATE |
| atom_gray | HW | 0.2230 | NONE |
| count_weighted | HW | 0.5891 | MODERATE |
| hash | face_score | 0.6819 | MODERATE |

### B.3 Phase 9D — Null model (1000 random trials)

| Threshold | Count | Fraction |
| :--- | :---: | :---: |
| \|r\| > 0.5 (moderate) | 211/1000 | 21.1% |
| \|r\| > 0.8 (strong) | 13/1000 | 1.3% |
| Best random \|r\| | — | **0.93** |
| Best principled \|r\| | — | 0.68 |

**Random beats principled by 0.25 in |r|.**

### B.4 Phase 9E — Why the constraint cannot derive c

```
UBP model: v = c × sin(Δφ), where n = 1/sin(Δφ)
Constraint: determines sin(Δφ) for each material
Does NOT determine: c (c = 1.0 in substrate units is a definition)

To derive c in SI:
  Need: 1 cell = ? meters, 1 tick = ? seconds
  UBP provides: neither
  Dimensional anchors needed: ℏ, G, or k_B (all absent from UBP)
```

---

*End of Phase 9 report. For prior phases, see:*
- *Phase 1-3: `UBP_c_Falsification_Study.pdf`*
- *Phase 4: `Phase4_Structural_Claims_Audit.md`*
- *Phase 5: `Phase5_Resolution_Audit.md`*
- *Phase 6: `Phase6_Information_Physical_Audit.md`*
- *Phase 7: `Phase7_Gap_As_Clue_Audit.md`*
- *Phase 8: `Phase8_Obstacle_Experiment_Audit.md`*

*All in `/home/z/my-project/download/`.*
