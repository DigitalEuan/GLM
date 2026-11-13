# MACHINE: Y_out(t) ≈ √2

```text
==============================================================================
MACHINE: Y_out(t) ≈ √2
==============================================================================
12/12 required roles present; 3/3 core parts selected; digital error 4.573e-06; 5 unmodeled stage(s) remain gaps.
status: executable-digital-branch · target: sqrt(2)

Y_out(t) ≈ √2 [partial] — carry and recover the declared irrational sqrt(2) as a one-bit temporal stream
├── 1 INPUT & REFERENCE CONDITIONING [declared]
│   law: condition a physical signal and bound the loop rails
│   ├── 1.1 Physical input source [declared]
│   │   law: x_raw(t) = A·√2 + n_env(t), A = 1.0
│   ├── 1.2 Anti-aliasing filter [declared]
│   │   law: H_aaf(s) = 1 / (1 + s·R·C); x_in = x_raw * h_aaf
│   └── 1.3 Reference scaling [declared]
│       law: V_ref > 1.4142·A; x_norm = x_raw·input_scale
│       scale: input 0.700035713374682 -> normalized 0.990000000000000; reconstruction 1.428498547851611
├── 2 CORE SIGMA-DELTA MODULATOR LOOP [executed]
│   law: error feedback with a one-bit quantizer and a delayed DAC
│   ├── 2.1 Summing junction (error node) [executed]
│   │   law: e[n] = x_in[n] - y_dac[n]
│   │   part: sum -> kcl-conservation (rank 2, electronics)
│   ├── 2.2 Loop filter [executed]
│   │   law: u[n] = u[n-1] + e[n-1]; H_loop(z) = 1 / (1 - z^-1)
│   ├── 2.3 1-bit quantizer [executed]
│   │   law: b[n] = sgn(u[n]) in {-1, +1}
│   │   part: sign -> threshold-comparator (rank 1, electronics)
│   ├── 2.4 1-bit feedback DAC [executed]
│   │   law: y_dac[n] = V_ref·b[n] (zero-order hold)
│   └── 2.5 Closed-loop output node [executed]
│       law: B(z) = STF(z)·X(z) + NTF(z)·Q(z)
│       note: The measured slope is a finite-window log-PSD fit, not an asymptotic filter order; the ideal first-order NTF is 20.00 dB/dec.
├── 3 TIMING & ENERGY BACKBONE [declared]
│   law: constraints that set the realizable clock and supply boundary
│   ├── 3.1 Master clock sampling [gap]
│   │   law: t_n = n·T_s + Δt_jitter[n]
│   └── 3.2 Power-supply rejection [gap]
│       law: V_rail(t) = V_dc + PSRR·δv_digital(t)
└── 4 RECONSTRUCTION / DEMODULATION STAGE [partial]
    law: extract the target value in digital and physical forms
    ├── 4A Digital output branch [executed]
    │   law: decimate the bitstream and reconstruct the target value
    │   ├── 4A.1 CIC / FIR low-pass filter [executed]
    │   │   law: H_dec(z) = [(1 - z^-M) / (1 - z^-1)]^K
    │   └── 4A.2 Downsampler [executed]
    │       law: Y_dig[k] = (b * h_dec)[k·M] ≈ √2
    └── 4B Analog / physical output branch [gap]
        law: reconstruct the one-bit stream into a physical load
        ├── 4B.1 Reconstruction filter [gap]
        │   law: H_rec(s) = ω0² / (s² + (ω0/Q)·s + ω0²)
        └── 4B.2 Power buffer / actuator [gap]
            law: Y_phys(t) = G_driver·(y_dac * h_rec)(t) ≈ √2

COMPILER-SELECTED CORE PARTS
  sum: sum -> kcl-conservation (rank 2, electronics)
    alternatives: fluid-continuity (rank 1, fluidics), opamp-summing (rank 3, electronics)
  sign: sign -> threshold-comparator (rank 1, electronics)
    alternatives: fluid-continuity (rank 2, fluidics), kcl-conservation (rank 3, electronics)
  quantized_carry: quantized_carry -> delta-sigma-error-feedback (rank 1, audio)
    alternatives: pll-phase-tracking (rank 2, electronics), orifice-pressure-flow (rank 3, fluidics)

EXECUTED CORE
  sqrt(2) -> 1.414208989714491 (error 4.573e-06)
  in-band suppression 36.92 dB; NTF slope 28.02 dB/dec
  [pass] one-bit bitstream: 100000 samples; values are exactly -1 and +1
  [pass] decimated sqrt(2) output: decimated=1.414208989714491; target=1.414213562373095; error=4.573e-06; tolerance=1e-04
  [pass] in-band noise suppression: 36.92 dB measured against the unshaped reference
  [pass] noise-transfer slope: 28.02 dB/decade measured from the bitstream spectrum
  note: The measured slope is a finite-window log-PSD fit, not an asymptotic filter order; the ideal first-order NTF is 20.00 dB/dec.

COVERAGE
  roles: 12/12 present
  unmodeled: Master clock sampling, Power-supply rejection, Analog / physical output branch, Reconstruction filter, Power buffer / actuator

GAPS
  - the analog reconstruction and power-buffer branches are declared, not simulated
  - clock jitter and supply rejection are declared constraints, not modeled
  - the anti-alias filter and reference rail are declared, not transient-simulated
  - machine.cir is a behavioral electrical core, not a fabrication netlist
  - no measured device or physical prototype is claimed
  - the electrical reconstruction filter and power buffer are declared, not simulated

A machine composes declared stages into a complete concept and executes only the stages named in its validation. It is not a fabricated device, no measured device is claimed, and it is not a proof that every declared physical stage works.
```
