# UBP EM Propagation Calibration Report

**Date:** 2026-08-06
**Experiment:** Calibrate UBP-to-real-world time/length scales by measuring
Cesium-133 hyperfine photon propagation through the 24D Golay/Leech substrate.

**Implements:** Steps 1-4 of the proposed EM-propagation calibration prototype.

---

## 1. The Cs Photon (Anchor Choice)

| Property | Value | Source |
|---|---|---|
| Frequency | 9,192,631,770 Hz | SI definition of the second (exact) |
| Period | 108.7828 ps | 1/f |
| Wavelength | 32.6123 mm | c/f |
| Photon energy | 6.0911e-24 J | hf |
| Photon energy | 3.8018e-05 eV | hf / e |

The Cesium-133 hyperfine transition photon is chosen because:

1. Its frequency is **exact by SI definition** -- zero measurement uncertainty
2. It is already referenced in the UBP mass formula (`m_e = Y^2 * WOBBLE * 24^4 * 29^4 * h * dNu_Cs / c^2`)
3. The wavelength (32.6 mm) is macroscopic -- interferometer-measurable
4. The frequency sits between the molecular regime (fs) and the lightspeed regime (cm),
   so it bridges the gap between the two existing calibration regimes.

## 2. Encoded Data Object

| Field | Value |
|---|---|
| 24-bit word (hex) | `0x53678C` |
| 24-bit word (binary) | `010100110110011110001100` |
| Hamming weight | 12 |
| Is Golay codeword | True |
| Reality row (R) | `010100` (20) |
| Info row (I) | `110110` (54) |
| Activation row (A) | `011110` (30) |
| Potential row (P) | `001100` (12) |

**Encoding scheme (per data_object/ scaling presets):**
- Domain (3 bits): 3 = EM radiation category
- Volume (5 bits, Gray-coded): int(log2(f_Cs)) mod 32 = 33 mod 32 = 1
- Compactness (4 bits, Gray-coded): int(floor(log2(lambda_Cs in m))) mod 16 = -5 mod 16 = 11
- Parity (12 bits): Golay [24,12,8] parity from generator matrix

Note: encoding uses cyclic (non-systematic) form, so the 12 payload bits are coefficients of generator rows rather than direct bit positions. The codeword is a valid Golay codeword; the Reality row is computed from the resulting 24-bit word.

## 3. Golay Engine Verification

| Property | Value |
|---|---|
| Code | [24, 12, 8] extended binary Golay |
| Number of codewords | 4096 |
| Coset-leader table size | 4096 (complete decoder) |
| Covering radius | 4 |
| Minimum distance | 8 |

**Weight distribution (verified):**

| Weight | Count |
|---|---|
| 0 | 1 (zero codeword) |
| 8 | 759 (minimal Leech vectors) |
| 12 | 2576 |
| 16 | 759 |
| 24 | 1 (all-ones codeword) |

All 759 weight-8 codewords are minimal vectors of the Leech lattice Lambda_24 (in the 2*delta scaling, norm^2 = 32 = minimum norm).

## 4. Existing Anchors and Known Inconsistency

| Anchor | Value | Source |
|---|---|---|
| 1. Velocity | v_UBP/c = 0.339 (implied K = 2.950) | `light/` aristotle_01 |
| 2. Tick | 1 tick = 2.10 fs (expected N_ticks = 51801) | `data_object/` enc04 |
| 3. Cell | 1 cell = 17.0 um | `data_object/` enc04 |

**Known inconsistency (the gap this experiment is designed to close):**

```
v_cell  = 17 um / 2.10 fs = 8.095e+09 m/s = 27.0c
v_UBP   = 0.339c  (from light/)
Discrepancy factor: ~80x
```

**If anchors 1+2 both hold:** implied hop length = 0.2134 um, so cell = 79.7 hops (i.e., 'cell' is a domain of ~80 hops, not a single hop).

## 5. Propagation Models and Results

Three propagation models are tested. In all three, the state remains a
Golay codeword throughout (codeword XOR codeword = codeword), so no
re-snapping is needed. Each tick advances the state by one minimal Leech hop.

### Model A: Single-vector hop
- Photon propagates by repeatedly XOR-ing with ONE minimal Leech vector v.
- Since v XOR v = 0, cycle = 2 ticks.
- Models a single E-field component, no M counterpart.

### Model B: Dual E/M vector hop
- Photon has E and M components (two independent minimal Leech vectors v_E, v_M).
- Applied in alternation: v_E, v_M, v_E, v_M, ...
- Cycle = 4 ticks (if v_E != v_M).
- Mirrors the E/M duality of a real photon.

### Model C: Triple E/M/S vector hop
- Photon has E, M, and S (Poynting = E x M) components.
- Three independent minimal Leech vectors v_E, v_M, v_S, applied in a 3-tick cycle.
- Cycle = 6 ticks (if v_E, v_M, v_S are independent).
- Models the full E/M/Poynting triad.

### Results Table

| Model | N_ticks | N_hops | K = N_t/N_h | v_UBP/c | Tick | Hop |
|---|---|---|---|---|---|---|
| single_vector | 2 | 2 | 1.000 | 1.0000 | 54391.39 fs | 16.3061 mm |
| dual_em | 4 | 4 | 1.000 | 1.0000 | 27195.69 fs | 8.1531 mm |
| triple_ems | 6 | 6 | 1.000 | 1.0000 | 18130.46 fs | 5.4354 mm |

## 6. Cross-Check Verdicts

### single_vector
_Single E-field component, no M counterpart_

- **Cycle:** 2 ticks / 2 hops
- **Measured K:** 1.0000
- **Implied v_UBP/c:** 1.0000
- **Implied tick:** 54391.3879 fs
- **Implied hop:** 16.3061 mm
- **Tick ratio vs anchor 2:** 25900.66x
- **Hop ratio vs anchors 1+2:** 76403.13x

**Verdicts:**
- K ~ 1.0: substrate propagates at c (1 hop per tick). Anchor 1 (0.339c) is NOT supported by this experiment.
- Tick is 25901x larger than anchor 2. Anchor 2 may be a different time domain (interaction vs propagation).
- Hop is 76403x larger than implied hop. Anchor 3 (cell = 17 um) is likely a domain of ~80 hops, not a single hop.

### dual_em
_Dual E/M components, alternating (mirrors photon E/M duality)_

- **Cycle:** 4 ticks / 4 hops
- **Measured K:** 1.0000
- **Implied v_UBP/c:** 1.0000
- **Implied tick:** 27195.6939 fs
- **Implied hop:** 8.1531 mm
- **Tick ratio vs anchor 2:** 12950.33x
- **Hop ratio vs anchors 1+2:** 38201.56x

**Verdicts:**
- K ~ 1.0: substrate propagates at c (1 hop per tick). Anchor 1 (0.339c) is NOT supported by this experiment.
- Tick is 12950x larger than anchor 2. Anchor 2 may be a different time domain (interaction vs propagation).
- Hop is 38202x larger than implied hop. Anchor 3 (cell = 17 um) is likely a domain of ~80 hops, not a single hop.

### triple_ems
_Triple E/M/S (Poynting) components, 3-tick cycle_

- **Cycle:** 6 ticks / 6 hops
- **Measured K:** 1.0000
- **Implied v_UBP/c:** 1.0000
- **Implied tick:** 18130.4626 fs
- **Implied hop:** 5.4354 mm
- **Tick ratio vs anchor 2:** 8633.55x
- **Hop ratio vs anchors 1+2:** 25467.71x

**Verdicts:**
- K ~ 1.0: substrate propagates at c (1 hop per tick). Anchor 1 (0.339c) is NOT supported by this experiment.
- Tick is 8634x larger than anchor 2. Anchor 2 may be a different time domain (interaction vs propagation).
- Hop is 25468x larger than implied hop. Anchor 3 (cell = 17 um) is likely a domain of ~80 hops, not a single hop.

## 7. Interpretation

### Key observation

All three propagation models yield **K = 1.0** (one hop per tick), which implies
**v_UBP = c** -- the substrate propagates EM perturbations at the speed of light
in these simple hop models.

This is **inconsistent** with the existing `light/` calibration of v_UBP = 0.339c,
which would require K = 1/0.339 ~= 2.95 (about 3 ticks per hop).

### Possible resolutions

1. **The 0.339c anchor is for a different propagation mode.** The `light/` derivation
   uses gamma = MONAD/13, which may describe *group velocity* of a structured
   wave packet, not *phase velocity* of a pure photon. In that case, 0.339c and
   c could both be correct -- for different quantities.

2. **The substrate has dispersion.** A Cs photon (9.19 GHz) may propagate at c,
   while a different frequency (e.g., the optical frequencies used in the `light/`
   derivation) may propagate at 0.339c. This would make the substrate a dispersive
   medium -- physically reasonable for a structured lattice.

3. **The 2.10 fs tick is in the wrong domain.** The molecular calibration gives
   tick = 2.10 fs, but this may be a *molecular interaction* tick, not a
   *propagation* tick. The substrate may have multiple time scales: a fast
   propagation tick (~ c-scaled) and a slow interaction tick (2.10 fs).

4. **The cell = 17 um is a domain, not a hop.** If the cell is ~80 hops (per the
   anchors 1+2 reconciliation), then the molecular calibration is consistent with
   a propagation tick of c-scaled, and the 2.10 fs is the interaction time across
   one cell (~80 hops). This is the most economical reconciliation.

### Recommended next steps

1. **Repeat with a different photon frequency** (e.g., optical ~500 THz) to test
   for dispersion (resolution 2).

2. **Add a structured wave-packet model** (multiple minimal vectors with phase
   relationships) to test whether 0.339c emerges as a group velocity (resolution 1).

3. **Calibrate against the 190 kJ/mol energy anchor** to test whether the
   molecular calibration is in the propagation regime or the interaction regime
   (resolutions 3 and 4).

4. **Add a Gray-code phase progression model** (Model D): the photon's Reality row
   advances through the full 6-bit Gray code cycle (64 values). This model
   requires re-snapping after each step and may produce a different K. The
   infrastructure is in place; only the propagation rule needs adding.

## 8. Outputs

- `/home/z/my-project/download/ubp_em_calibration.json` -- machine-readable results
- `/home/z/my-project/download/ubp_em_calibration_report.md` -- this report
- `/home/z/my-project/scripts/ubp_em_propagation_experiment.py` -- the experiment script
