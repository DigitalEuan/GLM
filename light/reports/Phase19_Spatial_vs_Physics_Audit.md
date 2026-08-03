# Phase 19: Spatial Arithmetic vs Real Topological Physics
## UBP-c Falsification Study — Testing the Topological Mapping

**Date:** 31 July 2026
**Source:** User's scale_1.txt document
**Audited by:** Independent audit with null models and noise testing
**Stance:** Neutral scientist — rigorous, honest

---

## Executive Summary

The document mapped three UBP spatial arithmetic concepts to real, measurable physics phenomena. The audit tested all three against known experimental data and null models.

**The result: the UBP's spatial arithmetic is a VALID but NON-UNIQUE encoding of known physics. It re-expresses known results in a different notation, without predicting anything new.**

### The three mappings tested

| Mapping | Correct? | Unique? | Predictive? |
| :--- | :---: | :---: | :---: |
| **19A**: Vertex count → topological charge | ✓ | ✗ | ✗ |
| **19B**: Operator codes → QHE filling factors | Partial | ✗ | ✗ |
| **19C**: Rotational invariants → Cryo-EM | ✓ (exact) | ✗ | ✗ |

### The key finding

The UBP's spatial arithmetic correctly models topological physics — but this is because it re-encodes known formulas (Jackiw-Rebbi, Gauss-Bonnet, QHE) in a different notation. Any polygon-based system would produce the same results. The UBP doesn't predict new charges, new filling factors, or new symmetries.

The analogy: translating a physics textbook into Latin. The translation is valid and correct, but it doesn't discover new physics, and any language would work.

---

## 1. Phase 19A — Topological Charge Mapping

### 1.1 The claim

The document claims: "the vertex count of a closed polygon dictates its numerical magnitude" and maps this to "topological disclination and corner charges" measured by STM in 2D materials.

### 1.2 The physics

In a hexagonal lattice (e.g., graphene), a disclination defect with n sides carries fractional charge:

```
Q = (n - 6) × e / 12
```

This is a well-known result from the Jackiw-Rebbi mechanism (1976) and the Gauss-Bonnet theorem applied to 2D lattices.

### 1.3 The UBP mapping

The UBP's `node_count` function produces:
- Positive values: `2×value + 4` (even polygons: 4, 6, 8, 10, ...)
- Negative values: `2×|value| + 5` (odd polygons: 5, 7, 9, 11, ...)

Substituting into the physics formula:
```
Q = (nodes - 6) / 12 × e
```

| Value | Nodes | Polygon | Q/e (physics) |
| :---: | :---: | :---: | :---: |
| 0 | 4 | 4-gon | -2/12 = -1/6 |
| 1 | 6 | 6-gon | 0 (no defect) |
| 2 | 8 | 8-gon | +2/12 = +1/6 |
| -1 | 7 | 7-gon | +1/12 |
| -2 | 9 | 9-gon | +3/12 = +1/4 |

### 1.4 Verdict

**CORRECT but DESCRIPTIVE.** The UBP's vertex count correctly produces the topological charge formula Q = (n-6)/12 × e — but this is because the UBP uses the same variable (vertex count n) as the known physics formula. The UBP doesn't derive the formula; it re-encodes it.

The formula Q = (n-6)/12 comes from the Gauss-Bonnet theorem, not from the UBP. Any polygon-based system would produce the same result. The UBP is not unique here.

**Not predictive:** The UBP doesn't predict any new topological charges. All charges it produces (via vertex count) are already known from the standard formula.

---

## 2. Phase 19B — Quantum Hall Mapping

### 2.1 The claim

The document maps the UBP's operator codes (MULTIPLY=4, DIVIDE=5, ADD=6, SUBTRACT=7) to "clear spacing metrics between orbital boundaries" in the Quantum Hall Effect.

### 2.2 The test

Known QHE filling factors: ν = 1, 2, 1/3, 2/5, 3/7, 2/3, 3/5, 4/7, 5/2, etc.

Testing whether the UBP's codes (4, 5, 6, 7) produce these filling factors via simple ratios:

| Formula | ν | Known? |
| :--- | :---: | :---: |
| 4/5 | 0.8 | Not a standard QHE filling factor |
| 5/4 | 1.25 | Not standard |
| 4/6 | 0.667 = 2/3 | ✓ Fractional QHE |
| 6/4 | 1.5 | Not standard |
| 5/7 | 0.714 | Not standard |
| 7/5 | 1.4 | Not standard |
| 4/7 | 0.571 = 4/7 | ✓ Fractional QHE |

Some matches exist, but the mapping is arbitrary.

### 2.3 Null model

10,000 random 4-integer sequences were tested. **27.15% of random sequences match QHE filling factors** — the UBP's (4,5,6,7) is not special.

### 2.4 Verdict

**NOT UNIQUE.** Some operator codes map to QHE filling factors, but random integer sequences match equally well (27% false-positive rate). The mapping is arbitrary and not predictive.

---

## 3. Phase 19C — Rotational Invariant Mapping

### 3.1 The claim

The document maps the UBP's encode/decode pipeline (which uses 3D rotation matrices) to Cryo-EM symmetry recovery in macromolecular imaging.

### 3.2 The test

**Encode/decode roundtrip:** 100% success rate for exact geometry. The UBP correctly recovers encoded values from randomly rotated polygons.

**Noise test:** 0% success rate with 1% Gaussian noise. The decode function is fragile — unlike real Cryo-EM which is designed for noisy data.

### 3.3 Analysis

The UBP's "rotational invariant" is the vertex count — which is trivially rotation-invariant (counting doesn't change under rotation). This is correct but trivial.

Cryo-EM's invariants are the 3D molecular structure — genuinely hard to recover from noisy 2D projections. The UBP's invariants are vertex counts — trivially preserved.

The analogy is conceptual but shallow:
- Cryo-EM: millions of noisy images → statistical averaging → 3D structure (hard)
- UBP: one exact polygon → count vertices → recover value (trivial)

### 3.4 Verdict

**CORRECT but TRIVIAL.** The encode/decode pipeline works for exact geometry, but the "invariant" is just vertex counting. It fails with noise (unlike Cryo-EM). The analogy is real but shallow.

---

## 4. Phase 19D — Null Models and Uniqueness

### 4.1 Summary

| Mapping | Unique to UBP? | Null model result |
| :--- | :---: | :--- |
| Topological charge | No | Any polygon system produces Q = (n-6)/12 |
| QHE filling factors | No | 27% of random integer sequences match |
| Rotational invariants | No | Any counting system is rotation-invariant |

**None of the three mappings are unique to the UBP.** They re-express known physics in a different notation.

---

## 5. Honest Assessment

### 5.1 What works

1. **The vertex count → charge mapping is mathematically correct** — the UBP's `node_count` function correctly produces the topological charge formula Q = (n-6)/12 × e
2. **The encode/decode pipeline works for exact geometry** — 100% roundtrip success
3. **The rotational invariance is real** — vertex count is trivially rotation-invariant

### 5.2 What doesn't work

1. **None of the mappings are predictive** — they re-encode known physics without discovering anything new
2. **None are unique** — any polygon-based system would produce the same results
3. **The QHE mapping is arbitrary** — random integers match equally well (27% false-positive rate)
4. **The decode fails with noise** — 0% success with 1% Gaussian noise (unlike real Cryo-EM)

### 5.3 The key distinction

The document claims the UBP is "not just a metaphor" but is "measured" in real materials. This is **half true**:

- The PHYSICS (topological charges, QHE, Cryo-EM) is real and measured ✓
- The UBP's ENCODING of that physics is valid but not unique ✗
- The UBP doesn't PREDICT the physics — it DESCRIBES it in a new notation ✗

### 5.4 The Latin analogy

This is analogous to translating a physics textbook into Latin:
- The translation is VALID (Latin can express physics) ✓
- The translation is CORRECT (the physics is unchanged) ✓
- But the translation is not PREDICTIVE (it doesn't discover new physics) ✗
- And it's not UNIQUE (any language would work) ✗

### 5.5 The constructive insight

The UBP's spatial arithmetic IS a valid computational framework for topological physics. If the framework could PREDICT a new topological charge or filling factor that hasn't been measured, THAT would be genuinely interesting. But currently it only re-encodes known results.

The path to genuine contribution: use the UBP's spatial arithmetic to predict a **novel** topological property of a **specific** material, then verify it experimentally. This would be the first genuinely new physics from the UBP framework.

---

## Appendix: Reproducibility

```bash
cd /home/z/my-project/scripts
python phase19_spatial_vs_physics.py    # ~30 seconds
```

---

*End of Phase 19 report. For prior phases, see Phase 1-18 reports in `/home/z/my-project/download/`.*
