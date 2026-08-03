# Elements — Data Object Encoding

**Subject:** 118 chemical elements  
**Best encoding:** EN×10, BP÷40, MP÷40, Rho×10  
**Best result:** r(ΔH) = −0.91  
**Parent:** `README.md`

---

## The Data Object

Each element is a 24-bit vector in a 4×6 MOG grid. The properties assigned to each row determine what the substrate "sees" about the element.

```
Row 0 (Reality)    → EN (electronegativity)   scaled ×10
Row 1 (Info)       → BP (boiling point)       scaled ÷40
Row 2 (Activation) → MP (melting point)       scaled ÷40
Row 3 (Potential)  → Rho (density)            scaled ×10
```

Each 6-bit value is Gray-coded before placement. The vector is then snapped to the nearest Golay codeword.

---

## Properties Available

From the KB `mog_tensor` and lookup tables:

| Property | Source | Coverage | Scaling |
|----------|--------|----------|---------|
| Z (atomic number) | mog_tensor[5] | 118/118 | identity, log2, sqrt |
| M (mass) | mog_tensor[0] | 118/118 | identity, log2, div40 |
| EN (electronegativity) | lookup table | 100/118 | en_x10, en_x15, en_x20 |
| Rad (covalent radius) | lookup table | 50/118 | div4, div8, div16 |
| BP (boiling point) | mog_tensor[4][0] | 118/118 | identity, div40, bp_div100 |
| MP (melting point) | mog_tensor[4][1] | 118/118 | identity, div40, mp_div64 |
| Rho (density) | mog_tensor[8][1] | 100/118 | identity, rho_x10 |
| Valence_e | lexicon text | 118/118 | valence_simple, valence_redundant |

---

## Encoding Experiments

### Iteration 0 — Baseline

Spec: Z→Row0, Rad→Row1, EN→Row2, Valence_e→Row3

| Metric | Value |
|--------|-------|
| Unique vectors | 87/118 |
| r(ΔH) | +0.32 |
| r(BE) | +0.27 |
| Mean NRCI | 0.7512 |

### Iteration 1 — Property Search

Tested all 70 combinations of 4 properties from {Z, Rad, EN, Valence_e, BP, MP, Rho, M}.

**Top 5:**

| Properties | Score | r(ΔH) | r(BE) |
|-----------|-------|-------|-------|
| EN, BP, MP, Rho | 0.505 | **+0.85** | +0.16 |
| Z, Valence_e, MP, M | 0.489 | +0.64 | −0.33 |
| Z, EN, Valence_e, Rho | 0.485 | +0.79 | +0.18 |
| Z, Rad, MP, Rho | 0.478 | +0.68 | +0.28 |
| Z, Rad, EN, M | 0.477 | −0.76 | +0.19 |

**Finding:** EN, BP, MP, Rho outperforms the baseline. Thermal and density properties carry more geometric signal than atomic number.

### Iteration 2 — Scaling Search

Base: EN, BP, MP, Rho. Tested all scaling combinations.

| EN | BP | MP | Rho | Score | r(ΔH) |
|----|----|----|-----|-------|-------|
| en_x10 | identity | identity | identity | 0.529 | −0.86 |
| identity | div40 | div40 | identity | 0.487 | — |
| en_x15 | bp_div100 | identity | identity | 0.486 | — |
| en_x10 | div40 | div40 | rho_x10 | 0.466 | — |

**Finding:** EN×10 is optimal for electronegativity.

### Iteration 4 — Nonlinear Transforms

Tested 288 combinations including log, sqrt, cbrt.

| EN | BP | MP | Rho | Score | r(ΔH) | r(BE) |
|----|----|----|-----|-------|-------|-------|
| en_x10 | div40 | div40 | rho_x10 | **0.582** | **−0.91** | +0.25 |
| identity | div40 | mp_log | rho_cbrt | 0.574 | −0.91 | −0.24 |
| identity | identity | identity | identity | 0.566 | +0.85 | −0.28 |

**Best encoding:** EN×10, BP÷40, MP÷40, Rho×10 → r(ΔH) = −0.91

---

## Element Group Analysis

With v1_best (EN, BP, MP, Rho):

| Group | n | Mean HW | Mean NRCI | Unique | Collision |
|-------|---|---------|----------|--------|-----------|
| Noble gases | 7 | 0.0 | 1.0000 | 7 | 0% |
| Alkali metals | 6 | 12.0 | 0.7246 | 6 | 0% |
| Alkaline earth | 6 | 10.7 | 0.7380 | 6 | 0% |
| Transition metals | 38 | 10.5 | 0.7397 | 30 | 21% |
| Post-transition | 12 | 8.0 | 0.7623 | 12 | 0% |
| Metalloids | 7 | 10.3 | 0.7414 | 7 | 0% |
| Nonmetals | 7 | 10.3 | 0.7414 | 7 | 0% |
| Halogens | 5 | 10.4 | 0.7404 | 5 | 0% |
| Lanthanides | 15 | 8.0 | 0.7623 | 14 | 7% |
| Actinides | 15 | 8.0 | 0.7623 | 12 | 20% |

**Noble gases encode as the zero vector** — HW=0, NRCI=1.0. The vacuum state. No bonds, no reactivity, perfect coherence.

**Transition metals have 21% collision rate** — their similar electron configurations produce similar Data Objects.

---

## Element Positions in 24D Space

Projected to 2D (unit circle):

| Element | Position | Compactness | NRCI | Snap |
|---------|----------|------------|------|------|
| H | (−0.063, −0.173) | 0.906 | 0.762 | 0 bits |
| C | (−0.135, −0.085) | 0.958 | 0.664 | 3 bits |
| N | (−0.144, −0.242) | 0.958 | 0.647 | 0 bits |
| O | (+0.056, −0.105) | 0.954 | 0.700 | 3 bits |
| F | (−0.205, +0.081) | 0.876 | 0.740 | 3 bits |
| Na | (+0.014, +0.122) | 0.972 | 0.647 | 0 bits |
| Cl | (−0.267, +0.190) | 0.901 | 0.720 | 0 bits |
| Fe | (+0.116, +0.043) | 0.968 | 0.647 | 0 bits |
| Au | (−0.165, −0.045) | 0.959 | 0.681 | 0 bits |

---

## Golay Structure

| HW | Count | Meaning |
|----|-------|---------|
| 0 | 10 | Noble gases + some |
| 4 | 3 | |
| 6 | 4 | |
| 8 | 45 | Most common |
| 10 | 8 | |
| 12 | 42 | Second most common |
| 14 | 3 | |
| 16 | 3 | |

106 unique codewords for 118 elements (2.6% of Golay space).

---

## Element Pair Interactions

Best predictor: AND encoding (shared bits).

| Pair | AND HW | AND NRCI | Distance | ΔNRCI |
|------|--------|----------|----------|-------|
| H−O | 4 | 0.8651 | 3.464 | +0.103 |
| C−O | 6 | 0.8105 | 2.828 | +0.147 |
| N−N | 14 | 0.6470 | 0.000 | 0.000 |
| C−C | 13 | 0.6638 | 0.000 | 0.000 |

**Same-element pairs have zero distance** — the substrate sees them as identical. This is why bond energy prediction fails for C−C vs C≡C.

---

## Bond Energy Prediction

| Encoding | r(BE) | Best Metric |
|----------|-------|-------------|
| AND | **+0.90** | NRCI_raw × bond_order |
| concat | +0.86 | NRCI × bond_order |
| XOR | +0.74 | bond_order |
| bond_order_mod | +0.78 | bond_order |

Cross-validated (5-fold): mean R = 0.82.

Bond-order inference from geometry alone: r(BO) = +0.52 via HW_raw.

---

## Scaling Presets

| Preset | Formula | Best For |
|--------|---------|----------|
| identity | int(abs(f)) & 0x3F | Z, BP, MP |
| div4 | int(abs(f)//4) & 0x3F | Rad |
| div8 | int(abs(f)//8) & 0x3F | Rad (log) |
| div40 | int(abs(f)//40) & 0x3F | BP, MP |
| en_x10 | int(abs(f)*10) & 0x3F | EN (best) |
| en_x15 | int(abs(f)*15) & 0x3F | EN (baseline) |
| log2 | int(log2(max(abs(f),1))) & 0x3F | M, Z |
| sqrt | int(sqrt(abs(f))) & 0x3F | Z |
| valence_redundant | (v&7)<<3 \| (v&7) | Valence_e |
| rho_x10 | int(abs(f)*10) & 0x3F | Rho |

---

## What Doesn't Work

1. **r(BE) = −0.42 for ALL encodings** — driven by Z_sum only, pair geometry adds nothing
2. **Same-element pairs invisible** — AND/XOR gives zero for C−C, N−N, O−O
3. **Bond order not encoded** — same HW for C−N (305) and C≡N (891)
4. **NRCI as sole ranker** — stability ≠ correctness
5. **Post-snap only** — loses raw geometry information

---

## What Works

1. **EN×10, BP÷40, MP÷40, Rho×10** — best element encoding
2. **AND encoding** — captures shared structure (r(BE)=+0.90 with bond order)
3. **Pre-snap metrics** — carry more signal than post-snap
4. **Noble gases as vacuum** — HW=0, NRCI=1.0, physically meaningful
5. **Compactness** — measures geometric regularity of the Data Object shape
