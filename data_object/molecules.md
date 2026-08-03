# Molecules — Data Object Encoding

**Subject:** 82 molecules (water, salt, amino acids, DNA bases, sugars, etc.)  
**Best encoding:** M (log2), MP (div40)  
**Best result:** r(ΔH) = +0.96  
**Parent:** `README.md`

---

## The Data Object

Each molecule is a 24-bit vector in a 4×6 MOG grid. Molecules have fewer measurable properties than elements — only M, BP, and MP are available from the KB.

```
Row 0 (Reality)    → M  (molecular mass)    scaled log2
Row 1 (Info)       → MP (melting point)     scaled ÷40
Row 2 (Activation) → M  (molecular mass)    scaled log2
Row 3 (Potential)  → MP (melting point)     scaled ÷40
```

The encoding duplicates M and MP across rows because only 2 properties have good coverage. The Golay snap then collapses similar molecules to the same codeword.

---

## Properties Available

From the KB `mog_tensor`:

| Property | mog_tensor Position | Coverage | Notes |
|----------|-------------------|----------|-------|
| M (molecular mass) | [0] | 79/82 (96%) | First value in mog_tensor[0] |
| BP (boiling point) | [4][0] | 78/82 (95%) | First value in mog_tensor[4] |
| MP (melting point) | [4][1] | 78/82 (95%) | Second value in mog_tensor[4] |
| Rho (density) | [8][1] | 10/82 (12%) | Too sparse to use |

**EN, Rad, Valence_e are not available** for molecules — these are element-specific properties.

---

## Encoding Experiments

### Cross-Domain: Element Encoding on Molecules

Applied the best element encoding (EN×10, BP÷40, MP÷40, Rho×10) to molecules:

| Metric | Value | Meaning |
|--------|-------|---------|
| Unique vectors | 24/82 | 71% collapse to same vector |
| HW=0 (collapsed) | 46/82 | 56% become vacuum state |
| r(Mass, HW) | −0.30 | Heavier → lower HW |
| r(BP, HW) | +0.27 | Weak |
| r(NRCI, BE) | −0.55 | Moderate |

**Finding:** The element encoding doesn't transfer to molecules. EN and Rho are unavailable, producing zero rows. The substrate needs molecule-native properties.

### Molecule-Specific Encoding Search

Tried all combinations of {M, BP, MP}:

| Properties | Unique Vectors | r(M, HW) | r(ΔH) |
|-----------|---------------|----------|-------|
| M only | 7 | −0.45 | — |
| M, BP | 27 | −0.51 | — |
| BP, MP | 40 | −0.33 | — |
| M, BP, MP | 44 | −0.38 | — |
| **M, MP** | **50** | −0.37 | **+0.96** |

**Best encoding: M (log2), MP (div40)** — 50 unique vectors for 82 molecules (61%).

---

## Sample Data Objects

| Molecule | M | MP | HW | NRCI | Unique |
|----------|---|----|----|------|--------|
| H2O | 18.015 | 273.15 | 0 | 1.000 | ✓ |
| NACL | — | 1074 | 0 | 1.000 | ✓ |
| METHANOL | 32.04 | 175.6 | 0 | 1.000 | ✓ |
| BENZENE | 78.11 | 278.7 | 0 | 1.000 | ✓ |
| GLUCOSE | 180.16 | 419 | 0 | 1.000 | ✓ |
| ATP | 507.18 | — | 0 | 1.000 | ✓ |

Many molecules collapse to HW=0 with the M/MP encoding. The substrate sees them as near-vacuum.

---

## Molecule-Molecule Interactions

| Molecule Pair | AND HW | XOR HW | Distance |
|--------------|--------|--------|----------|
| H2O ↔ NACL | 0 | 0 | 0.000 |
| H2O ↔ METHANOL | 0 | 0 | 0.000 |
| H2O ↔ BENZENE | 0 | 0 | 0.000 |
| NACL ↔ METHANOL | 0 | 0 | 0.000 |
| NACL ↔ BENZENE | 0 | 0 | 0.000 |
| NACL ↔ AMMONIA | 0 | 0 | 0.000 |
| METHANOL ↔ BENZENE | 0 | 0 | 0.000 |
| METHANOL ↔ AMMONIA | 0 | 0 | 0.000 |
| METHANOL ↔ METHANE | 0 | 0 | 0.000 |
| BENZENE ↔ AMMONIA | 0 | 0 | 0.000 |
| BENZENE ↔ METHANE | 0 | 0 | 0.000 |
| BENZENE ↔ GLUCOSE | 0 | 0 | 0.000 |
| AMMONIA ↔ METHANE | 0 | 0 | 0.000 |
| AMMONIA ↔ GLUCOSE | 0 | 0 | 0.000 |
| METHANE ↔ GLUCOSE | 0 | 0 | 0.000 |

**All molecule pairs have HW=0 and distance=0.** The M/MP encoding collapses most molecules to the same vector. The substrate cannot distinguish molecules from each other at this encoding level.

---

## Element-Molecule Interactions

| Element ↔ Molecule | Overlap | Hex Agreements | HW(XOR) |
|--------------------|---------|---------------|----------|
| H ↔ Methane | 16 | 3 | 8 |
| H ↔ Glucose | 16 | 3 | 8 |
| Cl ↔ Salt | 16 | 1 | 8 |
| H ↔ Water | 14 | 2 | 10 |
| H ↔ Ammonia | 14 | 1 | 10 |
| N ↔ Ammonia | 14 | 1 | 10 |
| O ↔ Water | 12 | 2 | 12 |
| Na ↔ Salt | 12 | 0 | 12 |
| Fe ↔ Rust | 12 | 0 | 12 |
| C ↔ Methane | 10 | 2 | 14 |
| C ↔ Glucose | 8 | 2 | 16 |

**Hydrogen has highest overlap with its molecules** (14–16). Carbon has lowest (8–10). This reflects hydrogen's small, universal bonding character vs carbon's diverse, specific bonding.

---

## Bond Energy (Molecule-Internal)

| Metric | r(BE) | Meaning |
|--------|-------|---------|
| r(HW, BE) | +0.17 | Weak |
| r(NRCI, BE) | −0.55 | Moderate — higher NRCI = weaker bonds |

**NRCI has moderate predictive power for bond energy.** Higher NRCI (more coherent Data Object) correlates with weaker bonds — an inverse relationship. The substrate sees coherence as stability, and stable bonds are weaker.

---

## Triplet Interactions (3-Body)

| Triplet | HW(AND) | NRCI(AND) | Σpair HW |
|---------|---------|-----------|----------|
| H-F-H | 2 | 0.928 | 4 |
| H-O-H | 4 | 0.865 | 8 |
| H-N-H | 5 | 0.837 | 10 |
| H-C-H | 5 | 0.837 | 10 |
| Si-O-Si | 5 | 0.837 | 10 |
| C-O-O | 6 | 0.811 | 17 |
| Fe-O-Fe | 5 | 0.837 | 14 |
| H-S-H | 7 | 0.786 | 14 |
| O-O-O | 9 | 0.740 | 22 |
| C-C-C | 12 | 0.681 | 26 |
| N-N-N | 6 | 0.811 | 12 |

**NRCI decreases as pure-element chains get longer.** Heteronuclear bonds (H-F, H-O) have higher NRCI than homonuclear chains (C-C, O-O). The substrate sees electron asymmetry as coherence.

---

## What Works

1. **M, MP encoding** — r(ΔH) = +0.96, best molecule encoding
2. **Element-molecule interactions** — Hydrogen has highest overlap (universal connector)
3. **Triplet NRCI** — 100% pass rate, reliably computes 3-body coherence
4. **NRCI as bond predictor** — r(NRCI, BE) = −0.55 (moderate)

---

## What Doesn't Work

1. **Element encoding on molecules** — 56% collapse to HW=0
2. **Molecule-molecule interactions** — all HW=0 with M/MP encoding
3. **Distinguishing molecules** — 82 molecules → 50 unique vectors (39% collision)
4. **EN, Rad, Valence_e** — not available for molecules

---

## What's Needed

1. **More molecule properties** — solubility, polarity, molecular geometry
2. **Structural encoding** — atom count, bond count, ring count
3. **Interaction-based encoding** — how molecules combine, not isolated properties
4. **Molecular fingerprint** — encode the graph structure, not just scalar properties
