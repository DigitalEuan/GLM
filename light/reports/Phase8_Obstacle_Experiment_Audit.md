# Phase 8: The "Put a Known Object in the Path" Experiment
## UBP-c Falsification Study — Continuation

**Date:** 31 July 2026
**Source:** User's "put a known object in the path" framing + UBP light-obstacle simulation
**Audited by:** Independent statistical audit using the real `ubp_unified_v5.py` engine
**Stance:** Neutral scientist — Popperian falsificationism

---

## Executive Summary

The user proposed the most productive experimental design of the entire 8-phase audit: **"put a known object in the path of light and see which model does the correct thing."** This is exactly how you discriminate between models — test them against a known physical phenomenon (refraction) rather than fitting formulas to constants.

The UBP framework's document proposed a light-obstacle simulation where a 48° phase shift in a medium gives n = 1/sin(48°) ≈ 1.3456, matching water's refractive index (1.333) within 0.95%. The framework called this a derivation from the "Lucas-Lehmer trisection angle (144°/3)."

The audit reproduced the 48° → 1.3456 → water match, but found that **the UBP model fails the discriminative test**:

1. **Cherry-picked coincidence (8C):** 22 of 89 integer angles (24.7%) match *some* real material within 2%. The UBP's 48° → water match is one of 22 coincidences. 49° matches water even better (0.60% vs 0.95%).
2. **Only 1 of 10 materials predicted (8B):** The UBP model provides one angle (48°) for one material (water). It does not predict diamond (n=2.417), glass (n=1.520), silicon (n=3.420), or any other material.
3. **Snell's law is assumed, not derived (8D):** The UBP model gives v = c·sin(Δφ) where sin(Δφ) = 1/n. This is *identical* to standard optics v = c/n — just a coordinate change. No new physics is added.
4. **"Lucas-Lehmer" label is fabricated (8E):** 144 is NOT in the Lucas-Lehmer sequence (which is 4, 14, 194, 37634, …). 144 is the 12th Fibonacci number. The label was invented post-hoc to justify the chosen angle.

### Verdict at a glance

| Phase | Test | Result |
| :---: | :--- | :--- |
| **8A** | Reproduce 48° → n=1.3456 → water | **VERIFIED** (0.95% error) |
| **8B** | Predict 10 real materials | **FAILS** (1/10 — water only, by coincidence) |
| **8C** | Null model: random angles vs materials | 24.7% of integer angles match some material |
| **8D** | Derive Snell's law | **FAILS** — UBP is a relabeling of v = c/n |
| **8E** | "Lucas-Lehmer trisection" derivation | **FABRICATED** — 144 is not in the LL sequence |
| **8F** | Overall assessment | Model fails the discriminative test |

### The core finding

The user's experimental design is exactly right: put a known object in the path and see if the model predicts the correct behavior. The UBP model fails this test because:

- It matches **one** material (water) by coincidence
- It does **not** predict the other 9 materials tested
- It does **not** derive Snell's law (it relabels n as Δφ)
- It uses a **fabricated** mathematical label for the chosen angle

The model is a **relabeling of standard optics** (v = c/n becomes v = c·sin(Δφ) where sin(Δφ) = 1/n) with one cherry-picked match to water.

---

## 1. Background and Methodology

### 1.1 The user's productive framing

The user proposed moving away from particle physics and testing the UBP model against a known physical phenomenon:

> "I don't want to get stuck on Particle Physics — can we push another level or further with this attached concept of putting a known object in the path of light and finding our correct model that way?"

This is the **right experimental design**. Instead of fitting formulas to constants (which any flexible formula space can do), test whether the model can reproduce a known physical behavior across multiple cases. Refraction is ideal because:

- It has a simple, well-tested law (Snell's law)
- It varies across many real materials (water, glass, diamond, etc.)
- The refractive index is measured to high precision
- A real model must explain ALL materials, not just one

### 1.2 The UBP framework's proposal

The framework's document proposed:

- Light in vacuum propagates at c = 1.0 (substrate speed limit, 1 cell per tick)
- In a medium, the E and M fields lose orthogonality: Δφ < 90°
- Speed drops to v = c·sin(Δφ)
- Refractive index: n = 1/sin(Δφ)
- For water: Δφ = 48°, giving n ≈ 1.3456 (water's real n = 1.333, error 0.95%)
- The 48° is claimed to be the "Lucas-Lehmer trisection angle (144°/3)"

### 1.3 Methodology

- **8A:** Reproduced the UBP simulation using the real engine
- **8B:** Tested against 10 real materials (vacuum, air, water, ethanol, crown glass, flint glass, sapphire, diamond, silicon, germanium)
- **8C:** Computed a null model: for each integer angle 1°–89°, checked if 1/sin(θ) matches some real material within 2%
- **8D:** Tested whether the UBP model derives Snell's law or assumes it
- **8E:** Verified the "Lucas-Lehmer trisection" claim against the actual Lucas-Lehmer sequence
- **8F:** Constructive assessment

---

## 2. Phase 8A — Reproduction of the UBP Simulation

### 2.1 The 48° claim

| Quantity | Value |
| :--- | :---: |
| Phase angle Δφ | 48° |
| v = sin(48°) | 0.7431 |
| n = 1/sin(48°) | 1.3456 |
| Water (real) | 1.333 |
| Error | 0.95% |

The 48° → n=1.3456 → water (0.95% error) claim is **reproduced exactly**.

### 2.2 The "instant speed restoration" claim

The framework presents the photon's speed snapping back to c=1.0 upon exiting the medium as a UBP discovery. This is **standard wave mechanics**: phase velocity in a medium is c/n, and when the wave exits, it returns to c. This is not a discovery; it is a restatement of how refraction works in any wave model.

### 2.3 Verdict

The simulation reproduces one data point (water) within 0.95%. But one data point is not a model — it is a coincidence unless the framework can predict the other materials too.

---

## 3. Phase 8B — Testing Against 10 Real Materials

### 3.1 The test

If the UBP model genuinely predicts refractive indices, it should work for ALL materials, not just water. The audit tested 10 real materials:

| Material | n (real) | θ required = arcsin(1/n) | UBP predicts? |
| :--- | :---: | :---: | :---: |
| Vacuum | 1.00000 | 90.00° | ✓ (trivially) |
| Air (STP) | 1.00029 | 88.62° | ✗ |
| Water (20°C) | 1.33300 | 48.61° | ~ (48° is close) |
| Ethanol | 1.36100 | 47.29° | ✗ |
| Glass (crown) | 1.52000 | 41.14° | ✗ |
| Glass (flint) | 1.62000 | 38.12° | ✗ |
| Sapphire | 1.77000 | 34.40° | ✗ |
| Diamond | 2.41700 | 24.44° | ✗ |
| Silicon | 3.42000 | 17.00° | ✗ |
| Germanium | 4.00000 | 14.48° | ✗ |

### 3.2 Findings

- Different materials require angles from 14° to 90°
- The UBP model provides **one** angle (48°) for **one** material (water)
- It does not predict the refractive indices of the other 9 materials
- A real model of refraction must explain ALL materials, not just one

### 3.3 Verdict

The UBP model is not a model of refraction; it is a single data point cherry-picked to match water.

---

## 4. Phase 8C — Null-Model Test

### 4.1 The test

If you pick a random integer angle θ, n = 1/sin(θ) will match SOME real material within 2% a certain fraction of the time. This is the null model. If the UBP's 48° → water match is a real prediction, it should be rare. If it's a coincidence, it should be common.

### 4.2 Results

For all 89 integer angles (1° to 89°):

| Match threshold | Count | Fraction |
| :--- | :---: | :---: |
| Within 2.0% of some material | 22/89 | **24.7%** |
| Within 1.0% of some material | 12/89 | 13.5% |
| Within 0.5% of some material | 5/89 | 5.6% |

### 4.3 All 22 matches within 2%

| Angle | n = 1/sin(θ) | Closest material | Error % |
| :---: | :---: | :--- | :---: |
| 17° | 3.4203 | Silicon | 0.01% |
| 24° | 2.4586 | Diamond | 1.72% |
| 34° | 1.7883 | Sapphire | 1.03% |
| 35° | 1.7434 | Sapphire | 1.50% |
| 38° | 1.6243 | Glass (flint) | 0.26% |
| 39° | 1.5890 | Glass (flint) | 1.91% |
| 41° | 1.5243 | Glass (crown) | 0.28% |
| 42° | 1.4945 | Glass (crown) | 1.68% |
| 47° | 1.3673 | Ethanol | 0.46% |
| **48°** | **1.3456** | **Water (20°C)** | **0.95%** |
| 49° | 1.3250 | Water (20°C) | 0.60% |
| 79°–89° | 1.0002–1.0187 | Air (STP) | 0.01%–1.84% |

### 4.4 The UBP's 48° in context

- The UBP's 48° → water match (0.95% error) is **one of 22** such matches
- **49° matches water even better** (0.60% error) — the UBP chose the wrong angle!
- 47° matches ethanol even better (0.46% error)
- 17° matches silicon almost perfectly (0.01% error)
- 41° matches crown glass almost perfectly (0.28% error)

### 4.5 Verdict

**24.7% of integer angles match some real material within 2%.** The UBP's 48° → water match is a coincidence, not a prediction. Any of the 22 angles listed above would give a comparable "match" to some real material.

---

## 5. Phase 8D — Snell's Law Test

### 5.1 The question

Does the UBP model *derive* Snell's law from substrate principles, or does it *assume* Snell's law and relabel it?

### 5.2 The UBP model's optics

| Framework | Formula | Notes |
| :--- | :--- | :--- |
| Standard optics | v = c/n | n is the refractive index |
| UBP | v = c·sin(Δφ) | Δφ is the "phase angle" |

The UBP defines sin(Δφ) = 1/n, so:

```
v_UBP = c · sin(Δφ) = c · (1/n) = c/n = v_standard
```

**The two formulas are identical.** The UBP model adds the variable Δφ = arcsin(1/n), but this is just a coordinate change. It does not add any new physics.

### 5.3 Snell's law derivation test

Snell's law: sin(θ₁)/sin(θ₂) = n₂/n₁ = v₁/v₂

For the UBP model to derive Snell's law, it would need to show that the phase angle transforms as sin(Δφ) at the interface. But the UBP model only gives v = c·sin(Δφ) — it does not give a refraction angle. To get θ₂, you must **use Snell's law directly**.

| Scenario | θ₁ | n₁ | n₂ | θ₂ (Snell) | UBP Δφ₂ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Air → Water | 30° | 1.0003 | 1.333 | 22.04° | 48.61° |
| Air → Glass | 45° | 1.0003 | 1.520 | 27.73° | 41.14° |
| Water → Air | 30° | 1.333 | 1.0003 | 41.78° | 88.62° |
| Glass → Diamond | 20° | 1.520 | 2.417 | 12.42° | 24.44° |

The UBP model computes θ₂ by **applying Snell's law**, not deriving it. The Δφ₂ column is just arcsin(1/n₂), which is a relabeling of n₂.

### 5.4 Verdict

The UBP model does not derive Snell's law; it assumes it. The variable Δφ is just a relabeling of n. No new physics is added.

---

## 6. Phase 8E — The "Lucas-Lehmer Trisection" Audit

### 6.1 The claim

The document states:

> "This 48° phase shift is not arbitrary. In `value_geometry.py`, 48° is the Lucas-Lehmer trisection angle (144°/3)."

This is presented as the mathematical derivation of why 48° is special.

### 6.2 Is 144 in the Lucas-Lehmer sequence?

The Lucas-Lehmer sequence (used to test Mersenne primes) is defined by s(0) = 4, s(n+1) = s(n)² − 2:

```
s(0) = 4
s(1) = 14
s(2) = 194
s(3) = 37634
s(4) = 1416317954
...
```

**144 is NOT in the Lucas-Lehmer sequence.** The "Lucas-Lehmer" label is **fabricated**.

### 6.3 What is 144 actually?

144 has several legitimate mathematical identities, none of which are "Lucas-Lehmer":

- 144 = 12²
- 144 = Fibonacci number F(12)
- 144 = 2⁴ × 3²
- 144 = "one gross" (12 dozen)

### 6.4 Why 144°/3 = 48°?

The document does not explain:
- Why 144° is special (beyond the fabricated label)
- Why divide by 3 (the "trisection" label suggests angle trisection, but 144°/3 is just division)

### 6.5 Is 48° derived from any UBP substrate object?

The audit checked whether 48 or 48° can be derived from substrate objects (Y, Y_inv, MONAD, wobble, L, U_e, sigma, pi, phi, e) under simple operations. The closest match was:

- (1/Y_inv) × 180 = 47.64 ≈ 48

This is a coincidence (within 0.36 of 48), but:
- The operation (1/Y_inv × 180) has no physical motivation
- Y_inv = π + 2/π ≈ 3.778, so 1/Y_inv ≈ 0.2647, and 0.2647 × 180 = 47.64
- This is just "convert Y to degrees" — arbitrary

### 6.6 The real source of 48°

The exact angle that would match water is:

```
arcsin(1/1.333) = 48.61°
```

The UBP uses 48° (off by 0.61°). If they used 48.61°, the match would be exact. Why didn't they? Because:

- 48.61° doesn't have a "nice" label like "Lucas-Lehmer trisection"
- 48° can be labeled as "144°/3" and 144 can be (falsely) called "Lucas-Lehmer"
- 48° was chosen for **marketability**, not accuracy

### 6.7 Verdict

The 48° "Lucas-Lehmer trisection" derivation is **fabricated**. 144 is not in the Lucas-Lehmer sequence. 48° was chosen because sin(48°) ≈ 1/n_water, and a mathematical label was invented to justify it post-hoc.

---

## 7. Phase 8F — Constructive Assessment

### 7.1 The user's experimental design is right

The user's framing — "put a known object in the path of light and see which model does the correct thing" — is the **most productive experimental design** in the entire 8-phase audit. It is a discriminative test: rather than fitting formulas to constants, test whether the model can reproduce a known physical phenomenon across multiple cases.

### 7.2 The UBP model fails this test

| Criterion | Result |
| :--- | :--- |
| Predicts water's refractive index | ✓ (within 0.95%, by coincidence) |
| Predicts other materials' refractive indices | ✗ (0 of 9 other materials) |
| Derives Snell's law from substrate | ✗ (assumes it, relabels n as Δφ) |
| Uses valid mathematical derivation for 48° | ✗ (fabricated "Lucas-Lehmer" label) |
| Adds new physics beyond standard optics | ✗ (v = c·sin(Δφ) is identical to v = c/n) |

### 7.3 Why this is the most clear-cut failure yet

Unlike the c-formula (Phase 1) or the dimensionless constants (Phase 7), the obstacle experiment has a **clean discriminative test**: a real model of refraction must predict ALL materials, not just one. The UBP model:

- Predicts 1 of 10 materials (water only)
- The 1 match is a coincidence (24.7% of angles match some material)
- Does not derive the governing law (Snell's law)
- Uses a fabricated derivation

This is the clearest failure in the audit because the test is unambiguous: either the model predicts all materials, or it doesn't. It doesn't.

### 7.4 What would make this a real prediction

For the UBP model to genuinely predict refractive indices, it would need to:

1. **Derive the phase angle Δφ for EACH material from the material's substrate representation** (e.g., from the bit pattern of the medium's codeword)
2. **Predict n = 1/sin(Δφ) for each material BEFORE measuring it**
3. **Match all 10 materials within measurement uncertainty** (not just water within 0.95%)
4. **Derive Snell's law from substrate principles** (not assume it and relabel it)

None of these are met. The UBP model is a relabeling of standard optics with one cherry-picked match to water.

### 7.5 The constructive path

If the framework's author wants to pursue this direction productively:

1. **Map each material to a substrate representation.** For example, encode water's molecular structure (H₂O) as a 24-bit vector and derive Δφ from its Tax/NRCI properties.
2. **Pre-register predictions for 5-10 materials** before checking their refractive indices.
3. **Test whether the derived Δφ values match the required arcsin(1/n) values.**
4. **If they match, you have a real model of refraction.** If they don't, the framework cannot predict refractive indices.

This is the only honest path forward for the obstacle experiment.

---

## 8. Synthesis: Where the 8-Phase Audit Stands

### 8.1 The full trajectory

| Phase | What was tested | Outcome |
| :---: | :--- | :--- |
| 1 | c-formula (numerological fit?) | Falsified (39% false-positive rate) |
| 2 | Principled derivation of c | 0/22 natural constructions hit c |
| 3 | Cross-target generalization | Substrate matches random integers 7.2× better than c |
| 4 | Structural claims (manifestation barrier, etc.) | 1/5 survives (photon-as-min-Tax) |
| 5 | Framework's resolutions to Phase 4 | 0/4 progressing; all protective belts |
| 6 | "Information is physical" / 11:1 ratio | Interpretive overlay; cherry-picked |
| 7 | Dimensionless constants (1/α, m_μ/m_e, m_p/m_e) | **ALL 3 PASS null-model** (first positive finding) |
| **8** | **Obstacle experiment (refraction)** | **FAILS discriminative test** (1/10 materials, fabricated derivation) |

### 8.2 The two genuine findings

Across 8 phases, two findings stand out as genuine:

1. **Phase 4C: Photon as minimum-Tax octad** — true mathematical property, but not a physical prediction
2. **Phase 7B: Dimensionless constants pass null-model** — the 3 dimensionless targets (1/α, m_μ/m_e, m_p/m_e) all beat random transcendentals at p < 0.005. This is the strongest positive result, though qualified by measurement-uncertainty and provenance concerns.

### 8.3 The pattern of failures

The failures follow a consistent pattern:

- **Cherry-picking**: selecting the most favorable comparison (Phase 6: bit 0 vs bit 12; Phase 8: 48° vs water)
- **Relabeling**: renaming known physics in UBP terminology (Phase 6: syndrome weight → "radiation"; Phase 8: n → Δφ)
- **Fabricated derivations**: inventing mathematical labels post-hoc (Phase 8: "Lucas-Lehmer trisection")
- **Single data points**: matching one target and ignoring others (Phase 8: water only, not the other 9 materials)

### 8.4 The user's intuition was right

The user's intuition throughout has been sound:

- "Can we escape numerology?" — Yes, by using discriminative tests (Phase 8)
- "The difference is a clue" — Only if measured against the right baseline (Phase 7)
- "Put a known object in the path" — The right experimental design (Phase 8)

The audit has shown that the UBP framework, as currently formulated, cannot pass these discriminative tests. But the *approach* the user is pushing toward — test against known physical phenomena across multiple cases — is exactly the right way to evaluate any physics model.

### 8.5 The path forward

The most productive directions, in order of promise:

1. **Phase 7 dimensionless constants (strongest positive finding):** If the formulas for 1/α, m_μ/m_e, m_p/m_e were pre-registered (derived before checking the target), this is a real result. The framework's author should document the derivation and attempt a new prediction (e.g., Weinberg angle).

2. **Phase 8 obstacle experiment (right design, wrong execution):** If the framework can map each material to a substrate representation and derive Δφ for each, it could predict all 10 refractive indices. This would be a real model of refraction.

3. **Honest acknowledgment of limitations:** The c-formula, the manifestation barrier, the 11:1 ratio, and the 48° "Lucas-Lehmer" claim should be retracted or clearly labeled as interpretive rather than predictive.

### 8.6 Final assessment

The "put a known object in the path" experiment is the **right approach** for evaluating physics models. The UBP model **fails** this test: it matches one material (water) by coincidence, does not predict the other nine, does not derive Snell's law, and uses a fabricated mathematical derivation.

But the *experimental design itself* is sound. If the framework can be extended to genuinely derive refractive indices for multiple materials from their substrate representations — pre-registered and tested against measurement — that would be the first real physics to emerge from the UBP program.

---

## Appendix A: Reproducibility

### A.1 Scripts

| Script | Purpose |
| :--- | :--- |
| `ubp_unified_v5.py` | The real UBP engine |
| `phase8_obstacle_experiment.py` | Main Phase 8 audit script — runs all 6 sub-phases |
| `ubp_constants.py` | UBP substrate constants |

### A.2 How to reproduce

```bash
cd /home/z/my-project/scripts
python phase8_obstacle_experiment.py    # ~15 seconds, runs all of Phase 8
```

---

## Appendix B: Detailed Numerical Results

### B.1 The 10 real materials tested

| Material | n (real) | θ = arcsin(1/n) | Category |
| :--- | :---: | :---: | :--- |
| Vacuum | 1.00000 | 90.00° | Reference |
| Air (STP) | 1.00029 | 88.62° | Atmospheric |
| Water (20°C) | 1.33300 | 48.61° | Common liquid |
| Ethanol | 1.36100 | 47.29° | Common liquid |
| Glass (crown) | 1.52000 | 41.14° | Optical glass |
| Glass (flint) | 1.62000 | 38.12° | Optical glass |
| Sapphire | 1.77000 | 34.40° | Crystal |
| Diamond | 2.41700 | 24.44° | Crystal |
| Silicon | 3.42000 | 17.00° | Semiconductor (IR) |
| Germanium | 4.00000 | 14.48° | Semiconductor (IR) |

### B.2 Null-model matches (integer angles 1°–89°)

22 of 89 integer angles (24.7%) match some real material within 2%. See Section 4.3 for the full table.

### B.3 Lucas-Lehmer sequence verification

```
Lucas-Lehmer sequence: [4, 14, 194, 37634, 1416317954, ...]
144 in sequence? False
```

144 is the 12th Fibonacci number, not a Lucas-Lehmer number.

### B.4 The UBP model vs standard optics

| Framework | Formula | Equivalent? |
| :--- | :--- | :---: |
| Standard optics | v = c/n | — |
| UBP | v = c·sin(Δφ) where sin(Δφ) = 1/n | **Yes** (identical) |

The UBP model is a coordinate change (n → Δφ = arcsin(1/n)), not new physics.

---

*End of Phase 8 report. For prior phases, see:*
- *Phase 1-3: `UBP_c_Falsification_Study.pdf`*
- *Phase 4: `Phase4_Structural_Claims_Audit.md`*
- *Phase 5: `Phase5_Resolution_Audit.md`*
- *Phase 6: `Phase6_Information_Physical_Audit.md`*
- *Phase 7: `Phase7_Gap_As_Clue_Audit.md`*

*All in `/home/z/my-project/download/`.*
