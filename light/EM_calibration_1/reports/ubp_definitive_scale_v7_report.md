# UBP Definitive Scale Search v7

**Date:** 2026-08-06
**Engine:** GMHGL/ubp_unified_v5.py + Lean-verified decoder patch
**Goal:** Find a definitive UBP-to-realworld scale, even departing from light/EM/elements

**Part A — Definitive scale search (4 methods)**
**Part B — v1 follow-ups (3 experiments)**

---

## Part A1: Full seed sweep (all 4096 codewords)

**Sweep size:** 4096 codewords (the entire 12-bit info space)

**HW distribution across all 4096 codewords:**

| HW | Count |
|---|---|
| 0 | 1 |
| 8 | 759 |
| 12 | 2576 |
| 16 | 759 |
| 24 | 1 |

**Key finding:** The 4096 codewords fall into 5 distinct HW classes. Within each HW class, TAX and NRCI are CONSTANT (they depend only on HW). So the substrate has 5 intrinsic scale levels, not 4096. The 4096 codewords are degenerate: many codewords, only 5 sizes.

**Monotonicity test:** Some monotonic variation detected (HW: r=0.353, TAX: r=0.353)

**TAX and NRCI by HW class:**

| HW | TAX (min–max) | NRCI (min–max) |
|---|---|---|
| 0 | 0.0000 – 0.0000 | 1.0000 – 1.0000 |
| 8 | 3.1174 – 3.1174 | 0.7623 – 0.7623 |
| 12 | 4.6761 – 4.6761 | 0.6814 – 0.6814 |
| 16 | 6.2348 – 6.2348 | 0.6160 – 0.6160 |
| 24 | 9.3522 – 9.3522 | 0.5167 – 0.5167 |

**Anti-numerology note:** Within each HW class, TAX and NRCI are EXACTLY constant (not just similar). The 4096 codewords are 100% degenerate at the HW level. The substrate has only 5 intrinsic scale levels (HW ∈ {0, 8, 12, 16, 24}), not 4096.

## Part A2: Music scale (88 piano keys)

**Test:** Encode all 88 piano keys (A0 to C8) using 12-TET with A4=440Hz exact.

- Notes encoded: 88
- Distinct codewords: 16
- Distinct HW classes: 3
- Distinct msg12 values: 16

**Verdict:** Of 88 piano keys, only 16 distinct substrate states. Many piano keys map to the SAME codeword — the encoding saturates across the audio range. The substrate does NOT preserve musical pitch.

**Monotonicity test:**

- Spearman(key_n, HW) = -0.2852
- Spearman(key_n, TAX) = -0.2852
- Spearman(key_n, msg12) = -0.8101

**Sample encoding (first 10 notes):**

| Note | Freq (Hz) | HW | msg12 |
|---|---|---|---|
| A0 | 27.50 | 12 | 1078 |
| A#0 | 29.14 | 12 | 1078 |
| B0 | 30.87 | 12 | 1078 |
| C1 | 32.70 | 8 | 1086 |
| C#1 | 34.65 | 8 | 1086 |
| D1 | 36.71 | 16 | 1342 |
| D#1 | 38.89 | 16 | 1342 |
| E1 | 41.20 | 16 | 1342 |
| F1 | 43.65 | 16 | 1342 |
| F#1 | 46.25 | 16 | 1342 |

## Part A3: Atomic numbers (Z=1 to Z=118)

**Test:** Encode each atomic number directly as the lower 7 bits of msg12, then Golay-encode.

- Elements encoded: 118
- Distinct codewords: 118
- Distinct HW classes: 2

**Verdict:** All 118 elements encode to 118 distinct codewords (2 distinct HW classes). HW does NOT vary monotonically with Z (r=0.300) — the encoding scrambles atomic number ordering.

**Monotonicity test:**

- Spearman(Z, HW) = 0.3003
- Spearman(Z, TAX) = 0.3003
- Spearman(Z, NRCI) = -0.3003

**HW distribution across all 118 elements:**

| HW | Count |
|---|---|
| 8 | 76 |
| 12 | 42 |

**Sample (first 10 elements):**

| Z | HW | TAX | NRCI |
|---|---|---|---|
| 1 | 12 | 4.6761 | 0.6814 |
| 2 | 8 | 3.1174 | 0.7623 |
| 3 | 8 | 3.1174 | 0.7623 |
| 4 | 8 | 3.1174 | 0.7623 |
| 5 | 8 | 3.1174 | 0.7623 |
| 6 | 8 | 3.1174 | 0.7623 |
| 7 | 8 | 3.1174 | 0.7623 |
| 8 | 8 | 3.1174 | 0.7623 |
| 9 | 8 | 3.1174 | 0.7623 |
| 10 | 8 | 3.1174 | 0.7623 |

## Part A4: Magic numbers (nuclear shell closures)

**Test:** Encode the 7 nuclear magic numbers (2, 8, 20, 28, 50, 82, 126) directly.

| N | HW | TAX | NRCI | Physical meaning |
|---|---|---|---|---|
| 2 | 8 | 3.1174 | 0.7623 | Helium-4 shell (most stable light nucleus) |
| 8 | 8 | 3.1174 | 0.7623 | Oxygen-16 shell |
| 20 | 8 | 3.1174 | 0.7623 | Calcium-40 shell |
| 28 | 8 | 3.1174 | 0.7623 | Nickel-58 shell |
| 50 | 12 | 4.6761 | 0.6814 | Tin-120 shell |
| 82 | 12 | 4.6761 | 0.6814 | Lead-208 shell (heaviest stable) |
| 126 | 12 | 4.6761 | 0.6814 | Hypothetical neutron magic (island of stability) |

**Verdict:** Magic numbers encode to HW classes {8, 12}. No special pattern distinguishes magic numbers from non-magic — the substrate doesn't 'know' about nuclear shell structure (which is expected: the encoding uses only the integer value, not the physical meaning).

## Part B2: Wave-packet model (testing for 0.339c group velocity)

**Model:** Wave packet = 64 consecutive Gray-coded integers, each snapped to a Golay codeword. Phase velocity = 1 state per tick (carrier). Group velocity = 1/period of the TAX envelope. If group velocity = 0.339 × phase velocity, the 0.339c anchor emerges.

- Packet length: 64 states
- Phase velocity: 1 state per tick (by construction)
- TAX envelope period: 2
- v_group / v_phase (TAX): 0.5
- HW envelope period: 29
- v_group / v_phase (HW): 0.034482758620689655
- Matches 0.339c within 10%? **False**

**Verdict:** Group velocity (TAX envelope) = 0.5000 × phase velocity. This does NOT match the 0.339c anchor. The wave packet does not produce 0.339c as group velocity.

**Anti-numerology:** The packet length (64) and starting integer (1000033) are pre-registered. We tested TAX envelope and HW envelope. We report BOTH, not just the one that matches (if any).

## Part B3: Energy calibration vs 190 kJ/mol anchor

**Test:** Encode 24 real chemical bond energies (kJ/mol) directly, check if any substrate quantity correlates.

**Encoding:** Bond energy (kJ/mol, integer) in lower 10 bits of msg12

**Correlations:**

- Spearman(energy, HW) = 0.3358
- Spearman(energy, TAX) = 0.3358
- Spearman(energy, NRCI) = -0.3358

**Verdict:** Across 24 real chemical bonds, correlation of bond energy with: HW r=0.336, TAX r=0.336, NRCI r=-0.336. Some correlation exists, but may be coincidental.

**Br-Br anchor check:**

- HW=8, TAX=3.1174, NRCI=0.7623
- Is Br-Br special? no — Br-Br is not distinguished by the substrate

## Part B4: Model D — Gray-code phase progression

Per v1: 'the photon's Reality row advances through the full 6-bit Gray code cycle (64 values). This model requires re-snapping after each step and may produce a different K.'

| Photon | N_ticks | N_hops | K | v/c | Returns to start? | Verdict |
|---|---|---|---|---|---|---|
| Cs-133 hyperfine (SI second) | 30 | 240 | 0.1250 | 8.0000 | True | K = 0.1250, v_UBP/c = 8.0000. Does NOT match 0.339c anchor. |
| Na D2 (589.0 nm) | 29 | 232 | 0.1250 | 8.0000 | False | K = 0.1250, v_UBP/c = 8.0000. Does NOT match 0.339c anchor. |
| Cs-137 gamma (662 keV) | 30 | 240 | 0.1250 | 8.0000 | True | K = 0.1250, v_UBP/c = 8.0000. Does NOT match 0.339c anchor. |
| ELF submarine comms (USA) | 29 | 232 | 0.1250 | 8.0000 | False | K = 0.1250, v_UBP/c = 8.0000. Does NOT match 0.339c anchor. |

**Hamming distance distribution (Model D):**

- Cs-133 hyperfine (SI second): {0: 33, 8: 30}
- Na D2 (589.0 nm): {0: 34, 8: 29}
- Cs-137 gamma (662 keV): {0: 33, 8: 30}
- ELF submarine comms (USA): {8: 29, 0: 34}

**Per Lean `corrected_quantized`:** transitions between codewords should have d² ∈ {0, 8, 12, 16, 24}. The HD distribution above shows whether Model D respects this law.

## Summary: What did we learn?

### Part A — Definitive scale search

1. **Full seed sweep (4096 codewords):** The substrate has exactly **5 intrinsic scale levels** (HW ∈ {0, 8, 12, 16, 24}). The 4096 codewords are 100% degenerate at the HW level — within each HW class, TAX and NRCI are EXACTLY constant. The substrate does NOT have a hidden continuous scale.

2. **Music scale (88 piano keys):** Only a few distinct substrate states across the entire audible range. The encoding saturates — many different notes map to the same codeword. The substrate does NOT preserve musical pitch.

3. **Atomic numbers (118 elements):** Direct encoding of Z produces a few distinct HW classes. The substrate does NOT preserve atomic number ordering. Two elements with very different Z can have the same substrate state.

4. **Magic numbers (7 nuclear closures):** No special pattern. The substrate doesn't 'know' about nuclear shell structure (expected, since the encoding uses only the integer value).

### Part B — v1 follow-ups

5. **Wave-packet model:** Tested whether 0.339c emerges as group velocity. Group velocity (TAX envelope) = 0.5000 × phase velocity. This does NOT match the 0.339c anchor. The wave packet does not produce 0.339c as group velocity.

6. **Energy calibration:** Tested whether any substrate quantity correlates with real chemical bond energies. Across 24 real chemical bonds, correlation of bond energy with: HW r=0.336, TAX r=0.336, NRCI r=-0.336. Some correlation exists, but may be coincidental.

7. **Model D (Gray-code phase progression):** Tested whether re-snapping after each Gray-code step produces K matching 0.339c. See results above.

## The honest conclusion

**There is no hidden definitive scale in the substrate.** The substrate has exactly 5 intrinsic scale levels (HW ∈ {0, 8, 12, 16, 24}), and these are the ONLY scale information the substrate carries. All 4096 codewords project onto these 5 levels.

This is not a failure of measurement — it's a property of the encoding. The 24-bit Data Object uses 12 payload bits, and the payload bits determine HW through the Golay code's structure. The recursive |u | u+v| construction preserves HW exactly across all Barnes-Wall dimensions.

**To get a definitive scale, you need one of:**

1. **A different encoding** that uses more payload bits (e.g., 32-bit or 48-bit info space). The current 12-bit info space is the bottleneck.

2. **A different substrate quantity** that varies continuously within an HW class. Currently, TAX/NRCI/HW/norm² are all HW-determined. We'd need a quantity that depends on the SPECIFIC codeword, not just its HW.

3. **Accept the 5-level discretization** and treat the substrate as a 5-class classifier, not a continuous scale. This is the most honest approach.

### What the GLM should do

The GLM should NOT try to derive a continuous scale from the substrate. Instead, it should:

1. **Classify** every encoded concept by HW class (5 levels)
2. **Use the 3D landscape** (vibration, domain, bond-energy) for real-world context
3. **Use the hexcolour** for visual association
4. **Accept that two concepts with the same HW class are substrate-identical** — the GLM cannot distinguish them from substrate properties alone. It needs external context (language, real-world measurements) to tell them apart.

## Anti-numerology audit

1. **All 4096 codewords tested** (no cherry-picking). HW distribution is {0:1, 8:759, 12:2576, 16:759, 24:1} — exactly the Golay weight distribution.

2. **All 88 piano keys tested** (pre-registered, exact frequencies). The encoding saturates — this is a measurement, not a curve-fit.

3. **All 118 atomic numbers tested** (pre-registered, pure integers). No monotonic relationship with HW — this is a negative result, reported honestly.

4. **All 7 magic numbers tested** (pre-registered, physically meaningful). No special pattern — reported honestly.

5. **Wave-packet model:** We tested BOTH TAX envelope and HW envelope. We report both, not just the one that might match.

6. **Energy calibration:** We tested 24 real chemical bonds (CRC Handbook values). We report correlations with HW, TAX, and NRCI — all three, not just one.

7. **Model D:** We tested multiple photons. We report all results, not just the one that might match 0.339c.

## Outputs

- `/home/z/my-project/download/ubp_definitive_scale_v7.json` (full data)
- `/home/z/my-project/download/ubp_definitive_scale_v7_report.md` (this file)
- `/home/z/my-project/scripts/ubp_definitive_scale_v7.py` (this script)
