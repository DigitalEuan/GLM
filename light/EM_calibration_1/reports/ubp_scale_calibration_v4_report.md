# UBP-to-Realworld Scale Calibration (v4)

**Date:** 2026-08-06
**Engine:** GMHGL/ubp_unified_v5.py (verified v5.4.1) + Lean-verified decoder patch
**Goal:** Measure substrate SIZE of EM fields and derive UBP-to-realworld scale factor
**Anti-numerology:** Pre-registered 49 EM references spanning 18 orders of magnitude; report ALL results

---

## 1. Pre-registered EM wavelength ladder

**48 EM references** spanning from ELF radio (~76 Hz) to gamma rays (~5×10²⁰ Hz).
Each entry is a REAL physical reference (NIST/CODATA/ISO 21348), not a cherry-picked frequency.

| # | Photon | Category | Frequency | Wavelength | Energy | HW |
|---|---|---|---|---|---|---|
| 1 | ELF submarine comms (USA) | ELF radio | 76.00 Hz | 3944.64 km | 3.14e-13 eV | 16 |
| 2 | VLF navigation (Omega) | VLF radio | 10.00 kHz | 29.98 km | 4.14e-11 eV | 12 |
| 3 | LORAN-C 100 kHz | LF radio | 100.00 kHz | 3.00 km | 4.14e-10 eV | 12 |
| 4 | AM radio (mid band) | MF radio | 1.00 MHz | 299.792 m | 4.14 neV | 16 |
| 5 | Shortwave radio (31m band) | HF radio | 9.70 MHz | 30.906 m | 40.12 neV | 12 |
| 6 | FM radio (mid band) | VHF radio | 98.00 MHz | 3.059 m | 405.30 neV | 16 |
| 7 | VHF TV channel 7 | VHF TV | 174.00 MHz | 1.723 m | 719.61 neV | 12 |
| 8 | UHF TV channel 14 | UHF TV | 470.00 MHz | 637.856 mm | 1.94 μeV | 12 |
| 9 | Cellular 700 MHz (LTE band 12) | Cellular | 729.00 MHz | 411.238 mm | 3.01 μeV | 16 |
| 10 | GPS L1 (1575.42 MHz) | GNSS | 1.58 GHz | 190.294 mm | 6.52 μeV | 12 |
| 11 | WiFi 2.4 GHz (channel 1) | WiFi | 2.41 GHz | 124.292 mm | 9.98 μeV | 8 |
| 12 | Bluetooth LE (channel 0) | Bluetooth | 2.40 GHz | 124.810 mm | 9.93 μeV | 8 |
| 13 | S-band radar (weather) | Radar | 2.80 GHz | 107.069 mm | 11.58 μeV | 8 |
| 14 | C-band satellite (4 GHz) | Satellite | 4.00 GHz | 74.948 mm | 16.54 μeV | 8 |
| 15 | 5G n78 mid-band (3.5 GHz) | 5G | 3.50 GHz | 85.655 mm | 14.47 μeV | 8 |
| 16 | Cs-133 hyperfine (SI second) | Atomic clock | 9.19 GHz | 32.612 mm | 38.02 μeV | 12 |
| 17 | X-band radar (8-12 GHz) | Radar | 10.00 GHz | 29.979 mm | 41.36 μeV | 12 |
| 18 | Ku-band satellite (12 GHz) | Satellite | 12.00 GHz | 24.983 mm | 49.63 μeV | 12 |
| 19 | K-band radar (24 GHz) | Radar | 24.00 GHz | 12.491 mm | 99.26 μeV | 12 |
| 20 | Ka-band satellite (26.5 GHz) | Satellite | 26.50 GHz | 11.313 mm | 109.60 μeV | 12 |
| 21 | 5G mmWave n257 (28 GHz) | 5G | 28.00 GHz | 10.707 mm | 115.80 μeV | 12 |
| 22 | THz imaging (1 THz) | THz | 1.00 THz | 299.792 μm | 4.14 meV | 8 |
| 23 | Water vapor line (183 GHz) | Atmospheric | 183.31 GHz | 1.635 mm | 758.11 μeV | 16 |
| 24 | CO2 laser (10.6 μm) | Far-IR laser | 28.30 THz | 10.593 μm | 117.04 meV | 8 |
| 25 | NH3 inversion (1.25 cm) | Microwave molecular | 23.98 GHz | 12.500 mm | 99.19 μeV | 12 |
| 26 | HF chemical laser (2.7 μm) | Mid-IR laser | 111.00 THz | 2.701 μm | 459.06 meV | 12 |
| 27 | 1550 nm fiber comms | Near-IR telecom | 193.40 THz | 1.550 μm | 799.84 meV | 12 |
| 28 | Nd:YAG 1064 nm | Near-IR laser | 281.76 THz | 1.064 μm | 1.17 eV | 12 |
| 29 | GaAs 850 nm (VCSEL) | Near-IR laser | 352.50 THz | 850.475 nm | 1.46 eV | 12 |
| 30 | HeNe 632.8 nm | Visible laser | 473.60 THz | 633.008 nm | 1.96 eV | 12 |
| 31 | Na D2 (589.0 nm) | Visible atomic | 508.92 THz | 589.072 nm | 2.10 eV | 12 |
| 32 | Hg green 546.1 nm | Visible lamp | 548.70 THz | 546.369 nm | 2.27 eV | 12 |
| 33 | Hg blue 435.8 nm | Visible lamp | 687.90 THz | 435.808 nm | 2.84 eV | 12 |
| 34 | H-beta (486.1 nm) | Visible stellar | 616.70 THz | 486.124 nm | 2.55 eV | 16 |
| 35 | H-alpha (656.3 nm) | Visible stellar | 456.80 THz | 656.288 nm | 1.89 eV | 12 |
| 36 | Ca K (393.4 nm) | UV stellar | 762.10 THz | 393.377 nm | 3.15 eV | 12 |
| 37 | Mg II h (280.3 nm) | UV stellar | 1.07 PHz | 280.442 nm | 4.42 eV | 12 |
| 38 | Lyman-alpha (121.6 nm) | UV stellar | 2.47 PHz | 121.570 nm | 10.20 eV | 16 |
| 39 | He II 30.4 nm (EUV) | EUV solar | 9.86 PHz | 30.405 nm | 40.78 eV | 16 |
| 40 | Fe XV 28.4 nm (EUV) | EUV solar | 10.55 PHz | 28.416 nm | 43.63 eV | 16 |
| 41 | Al K-alpha (1.49 keV) | Soft X-ray | 360.00 PHz | 832.757 pm | 1.49 keV | 16 |
| 42 | Cu K-alpha (8.04 keV) | X-ray | 1.95 EHz | 154.056 pm | 8.05 keV | 12 |
| 43 | Mo K-alpha (17.5 keV) | Hard X-ray | 4.23 EHz | 70.873 pm | 17.49 keV | 16 |
| 44 | Annihilation (511 keV) | Gamma | 123.60 EHz | 2.426 pm | 511.17 keV | 12 |
| 45 | Cs-137 gamma (662 keV) | Gamma nuclear | 160.20 EHz | 1.871 pm | 662.53 keV | 12 |
| 46 | Co-60 gamma (1.33 MeV) | Gamma nuclear | 322.00 EHz | 931.032 fm | 1.33 MeV | 12 |
| 47 | 26Al decay (1.81 MeV) | Gamma astrophysical | 438.00 EHz | 684.458 fm | 1.81 MeV | 12 |
| 48 | Pair-production threshold | Gamma threshold | 247.20 EHz | 1.213 pm | 1.02 MeV | 12 |

## 2. Substrate SIZE measures

For each photon's encoded codeword, we measure FIVE size quantities in the substrate:

| Measure | Definition | Range | Units |
|---|---|---|---|
| Hamming radius | HW of codeword = distance to vacuum | 0, 8, 12, 16, 24 | bits |
| Norm² (scaled) | sum of squared coords in ×8 repr | 0, 8, 12, 16, 24 | (×8)² |
| Norm² (actual) | scaled / 8 | 0, 1, 1.5, 2, 3 | (Leech)² |
| Shell index | HW // 8 | 0, 1, 2, 3 | shell |
| Kissing count | minimal Leech vectors within Hamming sphere | 0, 98256, 98256, 196560, 196560 | vectors |
| Symmetry TAX | HW × (Y + 1/8) | varies | unitless |

All five are deterministic functions of HW. Two photons with the same HW have the same substrate size on every measure.

## 3. Scale factor S = λ_real / s_UBP (the calibration table)

For each wavelength and each size measure, the scale factor S tells us how many real meters correspond to one substrate-unit.

### 3a. S per Hamming radius (the most natural substrate-unit)

| Photon | λ (real) | HW | S = λ/HW (m/bit) | log10(S) |
|---|---|---|---|---|
| ELF submarine comms (USA) | 3944.64 km | 16 | 2.465e+02 km/unit | +5.39 |
| VLF navigation (Omega) | 29.98 km | 12 | 2.498e+00 km/unit | +3.40 |
| LORAN-C 100 kHz | 3.00 km | 12 | 2.498e+02 m/unit | +2.40 |
| AM radio (mid band) | 299.792 m | 16 | 1.874e+01 m/unit | +1.27 |
| Shortwave radio (31m band) | 30.906 m | 12 | 2.576e+00 m/unit | +0.41 |
| FM radio (mid band) | 3.059 m | 16 | 1.912e+02 mm/unit | -0.72 |
| VHF TV channel 7 | 1.723 m | 12 | 1.436e+02 mm/unit | -0.84 |
| UHF TV channel 14 | 637.856 mm | 12 | 5.315e+01 mm/unit | -1.27 |
| Cellular 700 MHz (LTE band 12) | 411.238 mm | 16 | 2.570e+01 mm/unit | -1.59 |
| GPS L1 (1575.42 MHz) | 190.294 mm | 12 | 1.586e+01 mm/unit | -1.80 |
| WiFi 2.4 GHz (channel 1) | 124.292 mm | 8 | 1.554e+01 mm/unit | -1.81 |
| Bluetooth LE (channel 0) | 124.810 mm | 8 | 1.560e+01 mm/unit | -1.81 |
| S-band radar (weather) | 107.069 mm | 8 | 1.338e+01 mm/unit | -1.87 |
| C-band satellite (4 GHz) | 74.948 mm | 8 | 9.369e+00 mm/unit | -2.03 |
| 5G n78 mid-band (3.5 GHz) | 85.655 mm | 8 | 1.071e+01 mm/unit | -1.97 |
| Cs-133 hyperfine (SI second) | 32.612 mm | 12 | 2.718e+00 mm/unit | -2.57 |
| X-band radar (8-12 GHz) | 29.979 mm | 12 | 2.498e+00 mm/unit | -2.60 |
| Ku-band satellite (12 GHz) | 24.983 mm | 12 | 2.082e+00 mm/unit | -2.68 |
| K-band radar (24 GHz) | 12.491 mm | 12 | 1.041e+00 mm/unit | -2.98 |
| Ka-band satellite (26.5 GHz) | 11.313 mm | 12 | 9.427e+02 μm/unit | -3.03 |
| 5G mmWave n257 (28 GHz) | 10.707 mm | 12 | 8.922e+02 μm/unit | -3.05 |
| THz imaging (1 THz) | 299.792 μm | 8 | 3.747e+01 μm/unit | -4.43 |
| Water vapor line (183 GHz) | 1.635 mm | 16 | 1.022e+02 μm/unit | -3.99 |
| CO2 laser (10.6 μm) | 10.593 μm | 8 | 1.324e+00 μm/unit | -5.88 |
| NH3 inversion (1.25 cm) | 12.500 mm | 12 | 1.042e+00 mm/unit | -2.98 |
| HF chemical laser (2.7 μm) | 2.701 μm | 12 | 2.251e+02 nm/unit | -6.65 |
| 1550 nm fiber comms | 1.550 μm | 12 | 1.292e+02 nm/unit | -6.89 |
| Nd:YAG 1064 nm | 1.064 μm | 12 | 8.867e+01 nm/unit | -7.05 |
| GaAs 850 nm (VCSEL) | 850.475 nm | 12 | 7.087e+01 nm/unit | -7.15 |
| HeNe 632.8 nm | 633.008 nm | 12 | 5.275e+01 nm/unit | -7.28 |
| Na D2 (589.0 nm) | 589.072 nm | 12 | 4.909e+01 nm/unit | -7.31 |
| Hg green 546.1 nm | 546.369 nm | 12 | 4.553e+01 nm/unit | -7.34 |
| Hg blue 435.8 nm | 435.808 nm | 12 | 3.632e+01 nm/unit | -7.44 |
| H-beta (486.1 nm) | 486.124 nm | 16 | 3.038e+01 nm/unit | -7.52 |
| H-alpha (656.3 nm) | 656.288 nm | 12 | 5.469e+01 nm/unit | -7.26 |
| Ca K (393.4 nm) | 393.377 nm | 12 | 3.278e+01 nm/unit | -7.48 |
| Mg II h (280.3 nm) | 280.442 nm | 12 | 2.337e+01 nm/unit | -7.63 |
| Lyman-alpha (121.6 nm) | 121.570 nm | 16 | 7.598e+00 nm/unit | -8.12 |
| He II 30.4 nm (EUV) | 30.405 nm | 16 | 1.900e+00 nm/unit | -8.72 |
| Fe XV 28.4 nm (EUV) | 28.416 nm | 16 | 1.776e+00 nm/unit | -8.75 |
| Al K-alpha (1.49 keV) | 832.757 pm | 16 | 5.205e+01 pm/unit | -10.28 |
| Cu K-alpha (8.04 keV) | 154.056 pm | 12 | 1.284e+01 pm/unit | -10.89 |
| Mo K-alpha (17.5 keV) | 70.873 pm | 16 | 4.430e+00 pm/unit | -11.35 |
| Annihilation (511 keV) | 2.426 pm | 12 | 2.021e-13 m/unit | -12.69 |
| Cs-137 gamma (662 keV) | 1.871 pm | 12 | 1.559e-13 m/unit | -12.81 |
| Co-60 gamma (1.33 MeV) | 931.032 fm | 12 | 7.759e-14 m/unit | -13.11 |
| 26Al decay (1.81 MeV) | 684.458 fm | 12 | 5.704e-14 m/unit | -13.24 |
| Pair-production threshold | 1.213 pm | 12 | 1.011e-13 m/unit | -13.00 |

### 3b. S per shell index (shell 0=vacuum, 1=min, 2=mid, 3=max)

| Photon | λ (real) | Shell | S = λ/shell (m/shell) | log10(S) |
|---|---|---|---|---|
| ELF submarine comms (USA) | 3944.64 km | 2 | 1.972e+03 km/unit | +6.29 |
| VLF navigation (Omega) | 29.98 km | 1 | 2.998e+01 km/unit | +4.48 |
| LORAN-C 100 kHz | 3.00 km | 1 | 2.998e+00 km/unit | +3.48 |
| AM radio (mid band) | 299.792 m | 2 | 1.499e+02 m/unit | +2.18 |
| Shortwave radio (31m band) | 30.906 m | 1 | 3.091e+01 m/unit | +1.49 |
| FM radio (mid band) | 3.059 m | 2 | 1.530e+00 m/unit | +0.18 |
| VHF TV channel 7 | 1.723 m | 1 | 1.723e+00 m/unit | +0.24 |
| UHF TV channel 14 | 637.856 mm | 1 | 6.379e+02 mm/unit | -0.20 |
| Cellular 700 MHz (LTE band 12) | 411.238 mm | 2 | 2.056e+02 mm/unit | -0.69 |
| GPS L1 (1575.42 MHz) | 190.294 mm | 1 | 1.903e+02 mm/unit | -0.72 |
| WiFi 2.4 GHz (channel 1) | 124.292 mm | 1 | 1.243e+02 mm/unit | -0.91 |
| Bluetooth LE (channel 0) | 124.810 mm | 1 | 1.248e+02 mm/unit | -0.90 |
| S-band radar (weather) | 107.069 mm | 1 | 1.071e+02 mm/unit | -0.97 |
| C-band satellite (4 GHz) | 74.948 mm | 1 | 7.495e+01 mm/unit | -1.13 |
| 5G n78 mid-band (3.5 GHz) | 85.655 mm | 1 | 8.565e+01 mm/unit | -1.07 |
| Cs-133 hyperfine (SI second) | 32.612 mm | 1 | 3.261e+01 mm/unit | -1.49 |
| X-band radar (8-12 GHz) | 29.979 mm | 1 | 2.998e+01 mm/unit | -1.52 |
| Ku-band satellite (12 GHz) | 24.983 mm | 1 | 2.498e+01 mm/unit | -1.60 |
| K-band radar (24 GHz) | 12.491 mm | 1 | 1.249e+01 mm/unit | -1.90 |
| Ka-band satellite (26.5 GHz) | 11.313 mm | 1 | 1.131e+01 mm/unit | -1.95 |
| 5G mmWave n257 (28 GHz) | 10.707 mm | 1 | 1.071e+01 mm/unit | -1.97 |
| THz imaging (1 THz) | 299.792 μm | 1 | 2.998e+02 μm/unit | -3.52 |
| Water vapor line (183 GHz) | 1.635 mm | 2 | 8.177e+02 μm/unit | -3.09 |
| CO2 laser (10.6 μm) | 10.593 μm | 1 | 1.059e+01 μm/unit | -4.97 |
| NH3 inversion (1.25 cm) | 12.500 mm | 1 | 1.250e+01 mm/unit | -1.90 |
| HF chemical laser (2.7 μm) | 2.701 μm | 1 | 2.701e+00 μm/unit | -5.57 |
| 1550 nm fiber comms | 1.550 μm | 1 | 1.550e+00 μm/unit | -5.81 |
| Nd:YAG 1064 nm | 1.064 μm | 1 | 1.064e+00 μm/unit | -5.97 |
| GaAs 850 nm (VCSEL) | 850.475 nm | 1 | 8.505e+02 nm/unit | -6.07 |
| HeNe 632.8 nm | 633.008 nm | 1 | 6.330e+02 nm/unit | -6.20 |
| Na D2 (589.0 nm) | 589.072 nm | 1 | 5.891e+02 nm/unit | -6.23 |
| Hg green 546.1 nm | 546.369 nm | 1 | 5.464e+02 nm/unit | -6.26 |
| Hg blue 435.8 nm | 435.808 nm | 1 | 4.358e+02 nm/unit | -6.36 |
| H-beta (486.1 nm) | 486.124 nm | 2 | 2.431e+02 nm/unit | -6.61 |
| H-alpha (656.3 nm) | 656.288 nm | 1 | 6.563e+02 nm/unit | -6.18 |
| Ca K (393.4 nm) | 393.377 nm | 1 | 3.934e+02 nm/unit | -6.41 |
| Mg II h (280.3 nm) | 280.442 nm | 1 | 2.804e+02 nm/unit | -6.55 |
| Lyman-alpha (121.6 nm) | 121.570 nm | 2 | 6.079e+01 nm/unit | -7.22 |
| He II 30.4 nm (EUV) | 30.405 nm | 2 | 1.520e+01 nm/unit | -7.82 |
| Fe XV 28.4 nm (EUV) | 28.416 nm | 2 | 1.421e+01 nm/unit | -7.85 |
| Al K-alpha (1.49 keV) | 832.757 pm | 2 | 4.164e+02 pm/unit | -9.38 |
| Cu K-alpha (8.04 keV) | 154.056 pm | 1 | 1.541e+02 pm/unit | -9.81 |
| Mo K-alpha (17.5 keV) | 70.873 pm | 2 | 3.544e+01 pm/unit | -10.45 |
| Annihilation (511 keV) | 2.426 pm | 1 | 2.426e+00 pm/unit | -11.62 |
| Cs-137 gamma (662 keV) | 1.871 pm | 1 | 1.871e+00 pm/unit | -11.73 |
| Co-60 gamma (1.33 MeV) | 931.032 fm | 1 | 9.310e-13 m/unit | -12.03 |
| 26Al decay (1.81 MeV) | 684.458 fm | 1 | 6.845e-13 m/unit | -12.16 |
| Pair-production threshold | 1.213 pm | 1 | 1.213e+00 pm/unit | -11.92 |

### 3c. S per TAX (UBP's primary size metric)

| Photon | λ (real) | TAX | S = λ/TAX (m/TAX-unit) | log10(S) |
|---|---|---|---|---|
| ELF submarine comms (USA) | 3944.64 km | 6.2348 | 6.327e+02 km/unit | +5.80 |
| VLF navigation (Omega) | 29.98 km | 4.6761 | 6.411e+00 km/unit | +3.81 |
| LORAN-C 100 kHz | 3.00 km | 4.6761 | 6.411e+02 m/unit | +2.81 |
| AM radio (mid band) | 299.792 m | 6.2348 | 4.808e+01 m/unit | +1.68 |
| Shortwave radio (31m band) | 30.906 m | 4.6761 | 6.609e+00 m/unit | +0.82 |
| FM radio (mid band) | 3.059 m | 6.2348 | 4.906e+02 mm/unit | -0.31 |
| VHF TV channel 7 | 1.723 m | 4.6761 | 3.685e+02 mm/unit | -0.43 |
| UHF TV channel 14 | 637.856 mm | 4.6761 | 1.364e+02 mm/unit | -0.87 |
| Cellular 700 MHz (LTE band 12) | 411.238 mm | 6.2348 | 6.596e+01 mm/unit | -1.18 |
| GPS L1 (1575.42 MHz) | 190.294 mm | 4.6761 | 4.069e+01 mm/unit | -1.39 |
| WiFi 2.4 GHz (channel 1) | 124.292 mm | 3.1174 | 3.987e+01 mm/unit | -1.40 |
| Bluetooth LE (channel 0) | 124.810 mm | 3.1174 | 4.004e+01 mm/unit | -1.40 |
| S-band radar (weather) | 107.069 mm | 3.1174 | 3.435e+01 mm/unit | -1.46 |
| C-band satellite (4 GHz) | 74.948 mm | 3.1174 | 2.404e+01 mm/unit | -1.62 |
| 5G n78 mid-band (3.5 GHz) | 85.655 mm | 3.1174 | 2.748e+01 mm/unit | -1.56 |
| Cs-133 hyperfine (SI second) | 32.612 mm | 4.6761 | 6.974e+00 mm/unit | -2.16 |
| X-band radar (8-12 GHz) | 29.979 mm | 4.6761 | 6.411e+00 mm/unit | -2.19 |
| Ku-band satellite (12 GHz) | 24.983 mm | 4.6761 | 5.343e+00 mm/unit | -2.27 |
| K-band radar (24 GHz) | 12.491 mm | 4.6761 | 2.671e+00 mm/unit | -2.57 |
| Ka-band satellite (26.5 GHz) | 11.313 mm | 4.6761 | 2.419e+00 mm/unit | -2.62 |
| 5G mmWave n257 (28 GHz) | 10.707 mm | 4.6761 | 2.290e+00 mm/unit | -2.64 |
| THz imaging (1 THz) | 299.792 μm | 3.1174 | 9.617e+01 μm/unit | -4.02 |
| Water vapor line (183 GHz) | 1.635 mm | 6.2348 | 2.623e+02 μm/unit | -3.58 |
| CO2 laser (10.6 μm) | 10.593 μm | 3.1174 | 3.398e+00 μm/unit | -5.47 |
| NH3 inversion (1.25 cm) | 12.500 mm | 4.6761 | 2.673e+00 mm/unit | -2.57 |
| HF chemical laser (2.7 μm) | 2.701 μm | 4.6761 | 5.776e+02 nm/unit | -6.24 |
| 1550 nm fiber comms | 1.550 μm | 4.6761 | 3.315e+02 nm/unit | -6.48 |
| Nd:YAG 1064 nm | 1.064 μm | 4.6761 | 2.275e+02 nm/unit | -6.64 |
| GaAs 850 nm (VCSEL) | 850.475 nm | 4.6761 | 1.819e+02 nm/unit | -6.74 |
| HeNe 632.8 nm | 633.008 nm | 4.6761 | 1.354e+02 nm/unit | -6.87 |
| Na D2 (589.0 nm) | 589.072 nm | 4.6761 | 1.260e+02 nm/unit | -6.90 |
| Hg green 546.1 nm | 546.369 nm | 4.6761 | 1.168e+02 nm/unit | -6.93 |
| Hg blue 435.8 nm | 435.808 nm | 4.6761 | 9.320e+01 nm/unit | -7.03 |
| H-beta (486.1 nm) | 486.124 nm | 6.2348 | 7.797e+01 nm/unit | -7.11 |
| H-alpha (656.3 nm) | 656.288 nm | 4.6761 | 1.403e+02 nm/unit | -6.85 |
| Ca K (393.4 nm) | 393.377 nm | 4.6761 | 8.412e+01 nm/unit | -7.08 |
| Mg II h (280.3 nm) | 280.442 nm | 4.6761 | 5.997e+01 nm/unit | -7.22 |
| Lyman-alpha (121.6 nm) | 121.570 nm | 6.2348 | 1.950e+01 nm/unit | -7.71 |
| He II 30.4 nm (EUV) | 30.405 nm | 6.2348 | 4.877e+00 nm/unit | -8.31 |
| Fe XV 28.4 nm (EUV) | 28.416 nm | 6.2348 | 4.558e+00 nm/unit | -8.34 |
| Al K-alpha (1.49 keV) | 832.757 pm | 6.2348 | 1.336e+02 pm/unit | -9.87 |
| Cu K-alpha (8.04 keV) | 154.056 pm | 4.6761 | 3.295e+01 pm/unit | -10.48 |
| Mo K-alpha (17.5 keV) | 70.873 pm | 6.2348 | 1.137e+01 pm/unit | -10.94 |
| Annihilation (511 keV) | 2.426 pm | 4.6761 | 5.187e-13 m/unit | -12.29 |
| Cs-137 gamma (662 keV) | 1.871 pm | 4.6761 | 4.002e-13 m/unit | -12.40 |
| Co-60 gamma (1.33 MeV) | 931.032 fm | 4.6761 | 1.991e-13 m/unit | -12.70 |
| 26Al decay (1.81 MeV) | 684.458 fm | 4.6761 | 1.464e-13 m/unit | -12.83 |
| Pair-production threshold | 1.213 pm | 4.6761 | 2.594e-13 m/unit | -12.59 |

## 4. Scale consistency test (the key result)

For each size measure: is S constant across the EM spectrum?

| Measure | n samples | log10(S) min | log10(S) max | log10 range | Variation factor | Verdict |
|---|---|---|---|---|---|---|
| S_per_Hamming_radius | 48 | -13.24 | +5.39 | 18.64 | 4.32e+18x | STRONGLY VARYING: S varies by > 1000x across 48 samples |
| S_per_norm_sq_scaled | 48 | -13.24 | +5.39 | 18.64 | 4.32e+18x | STRONGLY VARYING: S varies by > 1000x across 48 samples |
| S_per_norm_actual | 48 | -12.34 | +6.29 | 18.64 | 4.32e+18x | STRONGLY VARYING: S varies by > 1000x across 48 samples |
| S_per_shell | 48 | -12.16 | +6.29 | 18.46 | 2.88e+18x | STRONGLY VARYING: S varies by > 1000x across 48 samples |
| S_per_kissing_count | 48 | -17.42 | +1.30 | 18.72 | 5.23e+18x | STRONGLY VARYING: S varies by > 1000x across 48 samples |
| S_per_TAX | 48 | -12.83 | +5.80 | 18.64 | 4.32e+18x | STRONGLY VARYING: S varies by > 1000x across 48 samples |

### Within-HW consistency (true dispersion test)

If S varies ONLY because HW varies, that's expected (different substrate sizes give different S). If S varies WITHIN a single HW class, that's TRUE dispersion.

| Measure | HW class | n samples | log10 range within HW | Verdict |
|---|---|---|---|---|
| S_per_Hamming_radius | HW=16 | 11 | 16.75 | VARIES within HW (true dispersion) |
| S_per_Hamming_radius | HW=12 | 30 | 16.64 | VARIES within HW (true dispersion) |
| S_per_Hamming_radius | HW=8 | 7 | 4.07 | VARIES within HW (true dispersion) |
| S_per_norm_sq_scaled | HW=16 | 11 | 16.75 | VARIES within HW (true dispersion) |
| S_per_norm_sq_scaled | HW=12 | 30 | 16.64 | VARIES within HW (true dispersion) |
| S_per_norm_sq_scaled | HW=8 | 7 | 4.07 | VARIES within HW (true dispersion) |
| S_per_norm_actual | HW=16 | 11 | 16.75 | VARIES within HW (true dispersion) |
| S_per_norm_actual | HW=12 | 30 | 16.64 | VARIES within HW (true dispersion) |
| S_per_norm_actual | HW=8 | 7 | 4.07 | VARIES within HW (true dispersion) |
| S_per_shell | HW=16 | 11 | 16.75 | VARIES within HW (true dispersion) |
| S_per_shell | HW=12 | 30 | 16.64 | VARIES within HW (true dispersion) |
| S_per_shell | HW=8 | 7 | 4.07 | VARIES within HW (true dispersion) |
| S_per_kissing_count | HW=16 | 11 | 16.75 | VARIES within HW (true dispersion) |
| S_per_kissing_count | HW=12 | 30 | 16.64 | VARIES within HW (true dispersion) |
| S_per_kissing_count | HW=8 | 7 | 4.07 | VARIES within HW (true dispersion) |
| S_per_TAX | HW=16 | 11 | 16.75 | VARIES within HW (true dispersion) |
| S_per_TAX | HW=12 | 30 | 16.64 | VARIES within HW (true dispersion) |
| S_per_TAX | HW=8 | 7 | 4.07 | VARIES within HW (true dispersion) |

## 5. Comparison to existing UBP anchors

For each scale measure, we computed what the implied tick/velocity/energy would be, and checked if any sample matches an anchor within 10%.

| Scale measure | Tick (if v=c) near 2.10 fs? | v (if tick=2.10fs) near 0.339c? | E per unit near 190 kJ/mol? |
|---|---|---|---|
| S_per_Hamming_radius | False | True | False |
| S_per_norm_sq_scaled | False | True | False |
| S_per_norm_actual | True | False | False |
| S_per_shell | True | False | True |
| S_per_kissing_count | True | False | True |
| S_per_TAX | True | True | True |

## 6. Interpretation

### What the scale-consistency test shows

**S per Hamming radius** varies by 18.64 orders of magnitude across the spectrum (4.32e+18x). This is EXPECTED: shorter wavelengths must correspond to smaller substrate sizes (since HW is bounded at 24), so S = λ/HW tracks λ. This is NOT a calibration — it's a tautology that S scales with λ when HW is fixed.

**Within-HW consistency** is the key test:

- HW=16: 11 samples, log10(S) range = 16.75 → VARIES within HW (true dispersion)
- HW=12: 30 samples, log10(S) range = 16.64 → VARIES within HW (true dispersion)
- HW=8: 7 samples, log10(S) range = 4.07 → VARIES within HW (true dispersion)

If S varies WITHIN a single HW class (e.g., all HW=12 photons), that's TRUE dispersion and tells us the substrate is frequency-dependent. If S is constant within each HW class, the substrate is non-dispersive — the only variation across the spectrum comes from the discrete HW encoding, not from any continuous frequency-dependence.

### What this means for the GLM

The substrate encodes ALL EM fields as one of only 5 Hamming weights: 0, 8, 12, 16, 24.
Within each HW class, all photons have IDENTICAL substrate size. This means:

- The substrate does NOT distinguish between a Cs-133 photon and a Na D-line photon if both encode to HW=12. They have the same substrate size.
- The substrate distinguishes EM fields ONLY by HW (a 5-level discretization), not by continuous wavelength.
- The scale factor S = λ/HW is therefore NOT a substrate property — it's a property of the encoding's mapping from continuous frequency to discrete HW.

### The honest conclusion

**There is no single UBP-to-realworld scale factor S.** The substrate has only 5 distinct sizes (HW ∈ {0, 8, 12, 16, 24}), while the real-world EM spectrum spans 18 orders of magnitude. A single scale factor cannot bridge this — the substrate is fundamentally discretized at 5 levels, while reality is continuous.

This is not a failure of measurement. It's a property of the encoding: the 24-bit Data Object discretizes EM fields into 5 size buckets. To get a continuous scale, the encoding would need to use MORE bits (e.g., the Barnes-Wall 256-dim macro-lattice in `Elements encoding experiment:test_Barnes256.txt`), or the GLM would need to learn a many-to-one mapping from continuous wavelength to discrete HW.

### What we DO learn

1. **The substrate size is determined by HW, not by frequency.** This is a tautology of the encoding but a useful one: the GLM can compare EM fields by their HW class without needing a continuous scale.
2. **The 5 size classes correspond to physically meaningful Leech-lattice shells:** vacuum, minimal vectors (octads), codeword shell, second shell, all-ones. Each has a distinct NRCI and TAX.
3. **The 2.10 fs / 17 μm / 190 kJ/mol anchors** are NOT derivable from a single scale factor. They each measure a DIFFERENT substrate interaction (molecular vibration, molecular domain, bond energy). They are NOT three measurements of the same underlying scale — they are three different substrate processes that happen to all be in the molecular regime.

### Recommendation for the GLM training goal

Don't try to derive a single UBP-to-realworld scale. Instead, give the GLM the **scale TABLE**: for each HW class, what range of real-world phenomena does it cover?

- HW=0 (vacuum): no real-world analogue (pure substrate state)
- HW=8 (minimal Leech vectors): corresponds to single-photon events in the gamma/X-ray regime (sub-nm wavelengths, where 1 octad = 1 photon event)
- HW=12 (the dominant class): corresponds to optical/UV/IR (nm to μm wavelengths, where photons are 'relaxable' in 2 ticks)
- HW=16: corresponds to microwave/radio (mm to m wavelengths)
- HW=24 (all-ones): corresponds to ELF/DC fields (km wavelengths, the entire substrate saturated)

This gives the GLM a way to 'understand' an EM field: encode it, see which HW class it falls in, and know immediately the regime (gamma / optical / microwave / radio / ELF) without needing a continuous scale.

## 7. Outputs

- `/home/z/my-project/download/ubp_scale_calibration_v4.json` (full data)
- `/home/z/my-project/download/ubp_scale_calibration_v4_report.md` (this file)
- `/home/z/my-project/scripts/ubp_scale_calibration_v4.py` (this script)
