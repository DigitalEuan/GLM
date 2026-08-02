# UBP Data Object Encoding Specification v1.0

**Produced:** 2026
**Study basis:** Tests E0–E7 (see `/data_object/test_ledger.md`)
**Status:** Baseline for GLM learning — the GLM should attempt to comprehend an element/element pair by exploring variations of this specification and scoring them against reality using the harness in `/data_object/scripts/encoding_spec.py` - what configuration makes the most reality-aligned model of a Subject and why?
**Edited by:** UBP and GLM systems engineer E R A Craig 01 August 2026 - answers some questions and elaborates on some points.

---

## Purpose

This document specifies how to encode the "Subject" - whatever concept is being encoded, as a measurable "Data Object" - as an example and for testing/development these are currently: chemical elements; after that is: words, numbers then all inputs possible including visual, robotic sensors, various technical/mechanical plug-in sensory modules. A UBP "Data Object" is to be suitable for Spatial Arithmetic processing in the mog-mind. A Data Objects is to provide "meaning" by being a representation of a Subject that has actual alignment with reality through calculation - Elements provide a good known and verifiable starting point, numbers will be interesting and words may have meaning when compared relative to other words and known Subjects, not many things works well in isolation - generally speaking the strongest results occur through interaction, comparison, reflection and other relationship calculations.

The encoding is **layered**. Each layer exposes different geometric signals. The GLM should learn to read all layers.

---

## The Data Object (24-bit vector)

A Data Object is a 24-bit vector arranged as a 4×6 MOG (Miracle Octad Generator) grid:

```
            col 0   col 1   col 2   col 3   col 4   col 5
row 0       b0      b1      b2      b3      b4      b5      ← Reality
row 1       b6      b7      b8      b9      b10     b11     ← Info
row 2       b12     b13     b14     b15     b16     b17     ← Activation
row 3       b18     b19     b20     b21     b22     b23     ← Potential
```

Each row is a 6-bit Gray-coded value in [0, 63].

---

## Layer 1 — KB-Hardened Vector (UBP v5.4.1 native encoding)

**Source:** `ubp_system_kb.json` — the 118 element entries are pre-hardened by UBP v5.4.1.

**Property:** Each element's 24-bit `atlas.vector` field is a perfect Golay [24,12,8] codeword (syndrome weight = 0). Distribution across elements:
- 80 Dodecad (HW=12)
- 23 Hexadecad (HW=16)
- 15 Octad (HW=8)

**Signals carried (verified in E5, E6):**
- `sa_b_scene_max_3d_dist` ↔ ΔH: r = −0.47 (n=30)
- `aa_normal_dot` ↔ ΔH: r = +0.48 (n=30)
- `aa_normal_dot` ↔ BE: r = −0.37 (n=37)

**Usage:** Read directly from KB. Do not modify unless the entire used dataset is verifiable, completely, all encoded the same way and calibrated - this is worth running through the pipeline to investigate how different sets of data about Subjects produce different results and why, and to refine the pipeline itself.

---

## Layer 2 — D_geometric Re-encoding (property-based)

**Source:** Computed from the element's KB `math` field.

**Property-to-row assignment (BEST permutation from E7):**

| Row | Name        | Property      | Scaling preset     | Formula                          |
|-----|-------------|---------------|--------------------|----------------------------------|
| 0   | Reality     | `Z`           | `identity`         | `int(Z) & 0x3F`                  |
| 1   | Info        | `Valence_e`   | `valence_redundant`| `(v & 0x07) << 3 \| (v & 0x07)`  |
| 2   | Activation  | `EN`          | `en_x15`           | `int(EN × 15) & 0x3F`            |
| 3   | Potential   | `Rad`         | `div4`             | `int(Rad / 4) & 0x3F`            |

Each 6-bit value is Gray-coded before placement.

**Signals carried (verified in E4, E7):**
- `scn_overlap_count` ↔ BE: r = +0.56 (n=37) with this permutation
- `scn_overlap_count` ↔ ΔH: r = +0.29 (n=30)

**Usage:** Compute from KB `math` field using `encoding_spec.encode_element(symbol, spec)`.

---

## Per-bit Leech Geometry

Each of the 24 bits is assigned a 24D Leech point using the **A_basis scheme** (standard basis vector, magnitude = bit value). This is the control scheme that won for spatial-arithmetic integration.

- bit i (value v) → vector with v at position i, 0 elsewhere
- Norm² = bit_value² ∈ {0, 1}
- NOT a Leech minimal vector (control case)

**Signals carried:**
- Per-bit Leech points → spatial arithmetic polygons → scene metrics
- Best: `sa_b_scene_max_3d_dist` (see Layer 1 signals above)

### To be tested:
Can this per-bit 24D assignment provide additional dataspace/geometry to encode actual information about a Subject past the 6-bit capacity of grid-level grey coded encoding.

---

## Stacked MOG Grid Configuration

When two Data Objects interact, their 4×6 grids are stacked in 3D virtual space:

| Parameter         | Value  | Notes                                                |
|-------------------|--------|------------------------------------------------------|
| `cell_w`          | 4.0    | Horizontal spacing between grid columns              |
| `cell_h`          | 4.0    | Vertical spacing between grid rows                   |
| `z_offset`        | 7.0    | Z-axis distance between the two grids                |
| `seed_offset_a`   | 0      | Grid A polygon rotation seed offset                  |
| `seed_offset_b`   | 10     | Grid B polygon rotation seed offset (TUNED in E6)    |

**Why seed_offset_b = 10:** Sweep over 0–500 found seed_b=10 maximises the normal-vector alignment signal (r ≈ ±0.48 vs ΔH). Different seeds give B's polygons different 3D orientations, and seed_b=10 aligns best with chemistry - this 'Seed' aspect of the system needs experimentation, investigation and clarification.

**Operator-code encoding (structural, not signal-carrying):**
- With z=7, cell=4: same-position (1,1) bit pairs → DIVIDE operator (clearance = 5)
- Diagonal (Δr=1, Δc=1) bit pairs → SUBTRACT operator (clearance = 7)
- The operator COUNT is a weak signal (|r| < 0.24) — documented for completeness.

---

## Composite Metric

The three signals from the dual-encoding layers combine via multiple linear regression:

```
predicted_BE = β0 + β1·scn_overlap_d + β2·sa_b_max_3d_kb + β3·aa_normal_dot_kb
predicted_ΔH = γ0 + γ1·scn_overlap_d + γ2·sa_b_max_3d_kb + γ3·aa_normal_dot_kb
```

**Regression coefficients (fit on 37 pairs, best permutation `[Z, Valence_e, EN, Rad]`):**

| Target | Intercept | scn_overlap_d | sa_b_max_3d_kb | aa_normal_dot_kb |
|--------|-----------|---------------|----------------|-------------------|
| BE     | +350.31   | +49.01        | ~0 (degenerate) | −1497.35          |
| ΔH     | −941.03   | +40.00        | ~0 (degenerate) | +4213.55          |

Note: `sa_b_max_3d_kb` coefficient is effectively zero because KB-hardened vectors all have the same norm² distribution (quantized), making this metric nearly constant across pairs. The composite R is driven primarily by `scn_overlap_d` and `aa_normal_dot_kb` - verifiable data is required wherever possible.

**Performance (best permutation `[Z, Valence_e, EN, Rad]`):**

| Metric                        | Full sample | 5-fold CV |
|-------------------------------|-------------|-----------|
| Multiple R (BE), n=37         | 0.68        | 0.22      |
| Multiple R (ΔH), n=30         | 0.50        | 0.45      |
| R² (BE)                       | 0.46        | —         |
| R² (ΔH)                       | 0.25        | —         |

**Overfitting warning:** The BE signal has a large train/CV gap (0.68 → 0.22), suggesting the 37-pair sample is too small for stable BE prediction. The ΔH signal generalises better (0.50 → 0.45). Expanding to 60+ pairs would help - we are exploring the space and recording findings not expecting, but accepting results.

---

## Per-bit Attribution (from E7 ablation)

The 5 most critical bits in the KB-hardened Layer 1 (flipping these hurts the score most):

| Bit | Row         | Col | Score change when flipped |
|-----|-------------|-----|---------------------------|
| 1   | Reality     | 1   | −0.19                     |
| 23  | Potential   | 5   | −0.18                     |
| 11  | Info        | 5   | −0.16                     |
| 9   | Info        | 3   | −0.15                     |
| 12  | Activation  | 0   | −0.14                     |

The 5 least critical bits (safe to perturb):

| Bit | Row         | Col | Score change when flipped |
|-----|-------------|-----|---------------------------|
| 5   | Reality     | 5   | +0.003                    |
| 7   | Info        | 1   | +0.006                    |
| 21  | Potential   | 3   | −0.010                    |
| 14  | Activation  | 2   | −0.012                    |
| 19  | Potential   | 1   | −0.013                    |

**Interpretation:** Reality-row (Z) and Info-row (mass/shells) bits are most diagnostic. Potential-row low bits are least diagnostic. The GLM should focus comprehension effort on the high-impact bits - what measure in reality aligns with this?

---

## How the GLM Should Use This Specification

The GLM learning loop:

1. **Load the baseline** from this document.
2. **For each element or element pair**, compute:
   - Layer 1 metrics (from KB-hardened vector in this example but use verified data where available)
   - Layer 2 metrics (from D_geometric re-encoding)
   - Stacked-grid metrics (from the configuration above)
3. **Predict** bond energy and ΔH using the composite metric.
4. **Compare** predictions to actual chemistry (from `KNOWN_PAIRS` in `e1_e2_e3_kb_sweep.py` - expand where possible).
5. **Try variations** of the encoding:
   - Different property subsets (try `['Z', 'Ion', 'EN', 'Rad']`, etc.)
   - Different row permutations (24 options for any 4 properties)
   - Different scaling presets (see `SCALING_PRESETS` in `encoding_spec.py` - expand where possible)
   - Different Leech schemes (A_basis, B_classA, C_classC, D_classB)
   - Different stacked-grid configs (cell_w, cell_h, z_offset, seed_b)
6. **Score** each variation using `score_dual_encoding(spec)`.
7. **Learn** which variations improve the overall score.
8. **Comprehend** the element when the GLM can reliably predict its chemistry across held-out pairs.

---

## Files:

| File | Purpose |
|------|---------|
| `/scripts/encoding_spec.py` | EncodingSpec dataclass, scaling presets, `encode_element()`, `score_encoding()` |
| `/scripts/experiment/e7_encoding_spec_study.py` | Dual-encoding scoring, per-bit ablation, row permutation study |
| `vis/e7_visualize.py` | Visualizations of ablation + permutation results |
| `/scripts/ubp_kb_loader.py` | KB parser (118 elements, 22 reactions, etc.) |
| `/scripts/stacked_mog_grids.py` | Stacked MOG grid engine with operator detection |
| `/scripts/per_bit_leech.py` | Per-bit Leech address encoder (4 schemes) |

---

## Known Limitations (areas for immediate expansion)

1. **Small sample size (n=37 pairs).** Cross-validation R for BE drops sharply (0.68 → 0.22), indicating overfitting. Need 60+ pairs for stable BE prediction.
NOTE - Once a mapping is defined we can optimise the required data.

2. **KB-hardened encoding is opaque.** We use the UBP v5.4.1 KB vectors directly without fully understanding how they're produced. The GLM cannot easily vary Layer 1. 
NOTE - The script used for this is 'ubp_architect.py'. Vectors were produced from the 'math' data of the encoded subject (Element).

3. **No molecules yet.** The encoding is calibrated for elements only. Extending to KB MOLECULE entries (82 available) is the next milestone. 
NOTE - some 'MOLECULE' entries already exist.

4. **Best achievable R ≈ 0.68 (BE), 0.50 (ΔH).** The relationship between Data Object geometry and chemistry is real but moderate. Pushing past R = 0.7 likely requires either (a) more pairs, (b) nonlinear models (perhaps physically and accurately representing the Data Object in 3D space for observation using Spatial Arithmetic or other methods for investigation), or (c) additional signal sources not yet explored. Maybe the different models could act as weights depending on the application?

5. **Operator-code encoding is structural, not predictive.** The clearance-based operator detection works (bit pairs do encode MULTIPLY/DIVIDE/ADD/SUBTRACT) but the operator count is a weak signal. The arithmetic meaning of the operators in this context is unclear and needs further investigation and clarification. Much of this is structural as expected, investigation into the precise results under various applicable conditions is perhaps required.

---

## Change Log

| Version | Date       | Change |
|---------|------------|--------|
| v1.0    | 2026-08-02 | Initial baseline from E0–E7 study. Best permutation: [Z, Valence_e, EN, Rad]. Composite R(BE)=0.68, R(ΔH)=0.50. |
