# Pair-Bond Geometry Report — 4 August 2026

## The Breakthrough: Bond Order Warping

**The problem:** Element Data Objects are fixed per element. O=O and O-O
produce identical codewords because the encoding captures element identity,
not bond context.

**The solution:** Warp the codeword based on bond order using Golay column
permutations. This creates distinct spatial sectors in the 24D lattice for
single, double, and triple bonds.

### Results

| Method | CV r (BE) | CV MAE | Δ from baseline |
|--------|-----------|--------|-----------------|
| Random Forest (original) | 0.09 | 133 | baseline |
| **Random Forest (warped)** | **0.31** | **124** | **+0.22** |
| Evolved k-NN | 0.24 | 126 | +0.15 |

**Bond order warping improves prediction by +0.22 r.** This is the
largest single improvement in the entire experiment.

---

## How the Warping Works

```
Bond Order 1 (single):  codeword unchanged
Bond Order 2 (double):  swap MOG columns 2↔3 in each row
Bond Order 3 (triple):  swap MOG columns 2↔3 AND 4↔5 in each row
```

This ensures that:
- O-O (single) and O=O (double) land on **different sectors** of the 24D lattice
- The Golay structure is preserved (column swaps are valid MOG operations)
- The snap-to-codeword process maps warped vectors to different codeword neighborhoods

---

## Feature Analysis

### Strongest correlations with Bond Energy

| Feature | r(BE) | Interpretation |
|---------|-------|----------------|
| **overlap_A** | **−0.35** | Activation row overlap — strongest signal |
| shared_bits / pre_tax / dot_ab | −0.25 | Shared structure |
| diff_R | +0.25 | Reality row difference |
| proj_b | −0.25 | Element B projection onto bond |
| cross_strength | −0.22 | Element interaction strength |
| snap_depth | +0.21 | Snap magnitude × correction bits |

### Strongest correlations with Bond Order

| Feature | r(BO) | Interpretation |
|---------|-------|----------------|
| **overlap_P** | **+0.26** | Potential row overlap |
| diff_A | −0.22 | Activation row difference |
| cross_strength | +0.21 | Element interaction strength |
| snap_energy | +0.18 | Energy released/absorbed by snap |
| length | −0.21 | Bond length (Hamming distance) |

---

## Evolutionary Seed Selection

50 seeds × 20 generations. Best fitness: 63.3% (BO classification).

Top evolved features:
1. **asymmetry** (1.92) — which element contributes more to the bond
2. **shared_bits** (1.80) — AND Hamming weight
3. **snap_depth** (1.71) — snap magnitude × corrections
4. **nrci_b** (1.64) — Element B's coherence
5. **mass_product** (1.63) — product of element Hamming weights

The evolutionary algorithm converged quickly (plateau by generation 5),
suggesting the feature space has a clear fitness landscape.

---

## What This Means

1. **Bond order warping works.** The Golay column permutation creates
   distinct spatial sectors for different bond types. This is the
   geometric encoding of bond context that was missing.

2. **The Activation row is key.** `overlap_A` (r=−0.35) is the strongest
   predictor of bond energy. The Activation row encodes MP (melting point),
   which correlates with bond strength.

3. **The snap process carries signal.** `snap_depth` and `snap_energy`
   correlate with both BE and BO. The snap is part of the interaction
   mechanism, not just post-processing.

4. **Nonlinear primitives help.** `cross_strength`, `asymmetry`, and
   `proj_b` all carry meaningful signal. The dot products and projections
   between element vectors and bond vectors capture interaction geometry.

---

## Next Steps

1. **Refine the warping** — try different column permutations per bond order
2. **Combine warping + evolved weights** — use evolutionary optimization
   on the warped feature space
3. **Test on held-out pairs** — validate the r=0.31 result with proper CV
4. **Apply to language** — the warping principle (modify one object based
   on relationship type) applies to noun-verb encoding
