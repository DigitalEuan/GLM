# Summary of changes for run 741f4506-3ed1-4749-88b6-e980d392b4cc
I documented the "I am Y" study stage by stage, with a machine-checked proof behind every claim that is a claim, and a clean rewriting of the study itself. Your original text is unmodified apart from a short pointer note at the top.

**New files**

- `Y_STUDY_CLEAN_RESTATEMENT.md` — the study rewritten in its own structure and vocabulary (sections 0–17 correspond one-to-one), with every sentence tagged **[def] / [stip] / [thm] / [open]** and worded so that it is defensible exactly as written.
- `Y_OBSERVER_STUDY_REPORT.md` — the audit behind that rewriting: notation pinned to one object per symbol, a verdict table, stage-by-stage analysis, three corrections, four strengthening results, and an index of every machine-checked statement.
- `RequestProject/ObserverY.lean` — the proofs (compiles with no `sorry`, standard axioms only).
- `observer_y.py` — exact-rational audit; `--selftest` runs 46 checks, all passing, including exact agreement with `ubp_unified_v5.py`'s own tax and NRCI functions.

**What the verification found**

Right, and provable: the vacuum is the *unique* zero-tax, unit-coherence state; `TAX = HW·Q`; NRCI strictly decreasing into (0,1].

Stronger than the study claims: `Q = Y + 1/8` is *exactly* the minimum tax of any nonzero pattern, attained precisely by a single ±1 activation — so "activation quantum" is earned in the strict sense. The identity `TAX = HW·Q` was sharpened to an "if and only if": it holds exactly for patterns with entries in {−1,0,1}, hence on the code layer and not on the Leech layer. Stage V's "not-quite-closed loop" was identified with the Golay syndrome, giving three exact statements (closes ⟺ lawful; additive; same record ⟺ differ by a lawful pattern). And protection has an exact price: the cheapest protected distinction costs 8Q = 3.1174, eight times the unprotected minimum.

Corrections: (1) `Y` is *not* a minimum — the read operator 1/(Π + Δ/Π) is capped at 1/(2√Δ), attained at Π = √Δ, and has no positive lower bound; `Y` is its value at the stipulated Π = π. (2) "binary" is the wrong scope word for `TAX = HW·Q`. (3) The four-regime ladder is mis-scaled on 24 coordinates: Transitional and Subcoherent are unreachable and every nonzero Golay codeword sits in one and the same regime.

Two constructive additions: choosing the budget B = 8Q makes NRCI = 8/(8+HW) on the code layer and makes all four regimes carry information (proved); and refinement §14 A is carried out with a canonical syndrome penalty that vanishes exactly on lawful patterns and never exceeds 4Q. A side finding: at the Leech layer the ladder does discriminate — classes A and B are Coherent, but class C (weight 24) is already Transitional.

All work is committed and pushed; `lake build` is clean and the whole project remains free of `sorry`.

# Summary of changes for run da156cc5-4ec2-4c8a-8933-8ada5b9c3ff7
I took `LIGHTSPEED_STUDY_SYNTHESIS.md` and `substrate_speed_of_light.md`, extracted the exact mathematical definitions behind them from `ubp_unified_v5.py`, verified every number in exact rational arithmetic, and machine-checked the mathematical core in Lean. Your original documents are untouched apart from a prepended audit note on each.

**Start here:** `SUBSTRATE_LIGHTSPEED_REPORT.md`.

## The exact definitions

Since the 2019 SI redefinition `c`, `h`, `N_A`, `Δν_Cs` are exact rationals, so the whole chain is exact:

```
E₁(κ) = κ/N_A          τ(κ) = h/E₁ = h·N_A/κ          ν(T) = 24 + T
T_cell = ν(T)·τ        ℓ_cell = c·T_cell = (24+T)·c·h·N_A/κ
v(T) = 27c/(24+T)      n(T) = (24+T)/27
```

**All four of your published numbers reproduce exactly**: `E₁ = 3.1550×10⁻¹⁹ J`, `τ = 2.100165 fs`, `T_cell = 5.6704×10⁻¹⁴ s`, `ℓ_cell = 16.9996 μm` (your `17.0` used `c ≈ 3×10⁸`).

## What the concept actually is

The chain collapses to one line: `ℓ_cell = 27·λ₁`, where `λ₁ = hcN_A/κ = 629.6 nm` is the wavelength of the photon carrying one work unit. It is the Planck relation times the integer 27.

## Three corrections

1. **`c` is an input, not an output.** `ℓ_cell/T_cell = c` holds identically for every `κ` and every tick budget; run the chain with any other `c′` and it returns `c′`. The structural reason is proved: no power product of an action and an energy has the dimension of a speed — enough to fix a *time* (so `τ` is a genuine output), never a length. The chain would derive `c` if and only if the substrate predicted `ℓ_cell` independently; it does not. The honest result is: chemistry + Planck + defined `c` determine one new number, the 17 μm cell length, exactly proportional to `1/κ`.
2. **Scale interpretation.** `3.16×10⁻¹⁹ J` is a 630 nm visible photon (15 883 cm⁻¹), not a vibrational quantum (500–4 400 cm⁻¹); `2.10 fs` is its optical period, not a vibrational period (7.6–70 fs); `17 μm` is ~10⁵ molecular diameters. And the tabulated Br–Br value is 193 kJ/mol, so the anchor match is 1.6 %, not exact.
3. **Alignment points.** P2 (0.02938 %), P7 (0.01962 %) confirmed; P8 is better than quoted (0.0000374 %). **P4's residual is 0.00919 %, not 0.007 %** — worth re-running the residual hunt with `1.726 α²` rather than `1.35 α²`. **P6 is a tautology**: `⌊MONAD⌋ = 13`, so `MONAD/13 = 1 + L` is the definition of `L` rewritten. **P5 holds on the Golay layer only** — among Leech minimal vectors your own tax audit ranks class A (4.5294) below the octads (6.1174).

## What survives, and is worth testing

`n(T) = (24+T)/27` uses no empirical anchor and is falsifiable. Causality forces the vacuum TAX to be the *minimum* of the tax spectrum, and that minimum is the octad tax `8Y + 1 = 3.1174` — which is where your "+3" comes from, now derived rather than assumed (using the exact value gives 27.1174 ticks and 17.07 μm). Inverting against measured indices: water needs TAX 11.99, glass 17.0, sapphire 23.7 — but diamond needs 41.3, so if TAX ≤ 24 the law caps `n` at 16/9 = 1.778 and diamond falsifies it. Fixing the tax spectrum (integer vs codeword) is the highest-value next step. I also checked the one place the substrate asserts a dimensionful constant (`PhysicsALU.G_N`): it implies a Planck length 10³⁰ times smaller than the cell, so it cannot supply the missing length.

## Artifacts

- `SUBSTRATE_LIGHTSPEED_REPORT.md` — definitions, verification tables, corrections, and a rewritten version of the note in which every sentence is defensible.
- `substrate_lightspeed.py` — exact-rational implementation; `--selftest` (32 checks, all pass), `--report`, `--chain`, `--index`, `--constants`, `--json`.
- `RequestProject/Lightspeed.lean`, `RequestProject/SubstrateConstants.lean` — the machine-checked statements (the chain's numbers, the circularity theorem, the dimensional no-go, the refractive-index law and its causality constraint, the octad tax minimum, and the accuracy of P2/P4/P6/P7/P8). The project builds with no `sorry` and only the standard axioms.
- `lightspeed_audit.json`, README index, audit notes on both source documents.

All work is committed and pushed.

# Summary of changes for run f5bbc876-1524-481c-abfd-682b1c26ccbb
Both requests are done; everything is committed and pushed.

## 1) The test/report, refined with the newly supplied files

With `value_geometry.py`, `ubp_tgic_engine.py` and `tgic_v3.py` present, the original generator can actually be run, and this changes two conclusions from the first pass. `LATTICE_SHORTCUT_REPORT.md` is now **revision 2** (§7 lists exactly what changed), and the audit note prepended to `lattice_shortcode_directory.md` was updated to match (your original text untouched).

- **The directory is fully reproducible: 36/36 transitions**, both catalogues, identical except for last-digit float noise in five `factor_imbalance` fields. The first pass reported the "Deep Interfacial Sequence" as unreproducible; the missing ingredient was the **composite branch of the encoder** — composites are mapped through their prime powers (x = p₁^e₁, y = p₂^e₂, z = rest), not the bit-shift channels the write-up documents. That is also why consecutive integers show large jumps: they are not adjacent states.
- **"Even quantisation, d² ∈ 2ℤ, 100 %" is TRUE** — the first pass judged this against the raw layer and got it wrong. It is now proved in general: the Golay code is doubly even, so weight parity is constant on cosets, and the cosets the snap engine fails on have weight-4 (even) leaders; hence every snapped state has even weight and every d² is even, for any encoder and any integers. It therefore says nothing about primes.
- **Section-4 benchmark table is now auditable**: 8 of 10 cells reproduce exactly (samples: first 10 primes and first 10 composites ≥ 1,000,000). The prime "6-Face Coherence" (0.664642) and "RuneCube tax" (5.247629) cells do not, and are inconsistent with the table's own Master Stability entry; consistent values are 0.721295 and 3.896754.
- **Propeller imbalance**: "primes 0.0000" is true but vacuous (every prime power scores 0, e.g. 1018081 = 1009²); "composites > 0.1500" is false (2.68 % of composites in [10⁶,10⁶+10⁴) fall below; 1005973 = 997×1009 scores 0.00087).
- **The snap bug is confirmed**: 43.4 % of outputs are not codewords. `tgic_v3.py`'s own self-tests pass and its 9-neighbour off-by-one fix is an improvement, but its "snap only when certified" policy still leaves states off the code.
- New audit script `audit_ubp_directory.py` runs against your modules (parts A–G), and verifies my clean implementation agrees with the substrate function by function in exact rational arithmetic. Outputs: `lattice_shortcut_audit.json`, `lattice_shortcut_audit.log`, and a regenerated `lattice_shortcut_directory_corrected.json`.

## 2) The working operational system

- **`lattice_shortcut.py`** — self-contained (stdlib only) implementation of the fixed method: both encoders, complete nearest-codeword Golay decoding (the fix), jump vectors, Leech vectors and norms, the O(1) distance formula, and the TGIC 3-6-9 metrics. `--explain A B` narrates a transition stage by stage; `--walk/--range/--primes/--stats/--tgic/--json` for use; `--selftest` re-verifies every guarantee (all pass).
- **`LATTICE_SHORTCUT_METHOD.md`** — the explainer: pipeline, what the fix is and why, a worked example, a guarantee table cross-referenced to the proofs and the self-test, the TGIC metrics, and the honest limits (4096 states, collisions, no arithmetic acceleration, tie-break convention).

With the fix, every transition is an exact Leech-lattice vector with d² ∈ {0,8,12,16,24} (doubled norm quantised by 32, not 2), and d² = 8 steps are genuine minimal/kissing-sphere hops. Over 10 000 consecutive integers: 74.8 % octad steps, 25.2 % collisions.

## Machine-checked

`RequestProject/*.lean` builds with no `sorry`, only standard axioms, no `native_decide`. New this session:
- `Substrate.lean`: `legacySnap_even_weight`, `legacy_even_quantisation` (the even-quantisation law as a theorem about the code), `legacySnap_not_codeword`, `legacy_d2_not_div_four`.
- `FactorMap.lean`: `interfacial_factorisations` (certified factorisations of 1000033…1000050) and `legacyD2_interfacial_reproduces_directory` — a proof-level reproduction of the 17 published jump norms — plus `snapD2_interfacial_factor` for the corrected walk.
- Docstrings in `GrayCode.lean` / `Shortcut.lean` were re-framed where revision 1's wording no longer matched the evidence (the theorems themselves are unchanged and still true).


# Summary of changes for run ee71597d-15fc-4673-8a36-0dd75c5653ba
I fully tested the 24D Leech-lattice "geodesic shortcut" method: I re-implemented the pipeline from scratch, audited the published directory against it, formalised and machine-checked the mathematical core in Lean, and wrote a clean report. The concept is close to workable — with one bug fixed it becomes stronger than claimed — but three headline claims are false as stated.

**Report:** `LATTICE_SHORTCUT_REPORT.md` (full claim-by-claim verdict, corrected method, recommended revisions). An audit note was prepended to `lattice_shortcode_directory.md`; its original text is untouched.

**Reproducibility of the published data** (script `verify_lattice_shortcut.py`): the prime-to-prime catalogue reproduces exactly (19/19 jump vectors and 38/38 `nrci` values) using byte-wise Gray encoding plus the substrate's snap. The "Deep Interfacial Sequence" reproduces 0/17 under every pipeline variant tried, and its tabulated norms are impossible for this pipeline.

**Findings (Lean-proved unless noted):**
- Adjacent integers always have d² = 1 (Gray-code property), not d² ∈ {8,10,12}: `d2_succ`, `d2_interfacial_all_one`, `rawD2_interfacial`.
- "Even quantisation d² ∈ 2ℤ, 100 %" is false; the exact law is d² ≡ a+b (mod 2), so d² is even iff endpoints share parity — automatic for prime-to-prime walks: `d2_mod_two`, `d2_even_iff`, `d2_even_of_odd`, `exists_odd_d2`. Under the byte-wise map even that fails (`rawD2 1000187 1000193 = 5`).
- The octad/minimal-vector claim is true in corrected form and now proved: doubled differences of snapped states lie in Λ₂₄ with norm 4·d², minimal (32) exactly for octad steps — `golay_step_isLeech`, `normSq_stepVec`, `golay_step_minimal_iff` — together with a from-scratch proof that 32 is the minimum norm of the Leech lattice (`leech_min_norm`).
- The generator matrix in the substrate does give the Golay [24,12,8] code (weight enumerator 1+759x⁸+2576x¹²+759x¹⁶+x²⁴, doubly even, min distance 8, all verified exhaustively over the 4096 codewords). Its decoder, however, only corrects weight ≤ 3 errors and returns the input unchanged otherwise, so ~43 % of "snapped" states are not codewords (`substrate_snap_fails`; script-measured rates 441/1000 and 4316/10000).
- Fix: a complete decoder with a packed coset-leader table — covering radius 4 proved (`golay_covering_radius`, `decode_isGolay`, `decode_dist_le_four`), with the tie ambiguity at distance 4 made explicit (`decoding_not_unique`). With it, both published walks become exact lattice walks with d² ∈ {0,8} (`snapD2_interfacial`, `snapD2_prime_trajectory`), and in general d² ∈ {0,8,12,16,24}, i.e. the real quantisation is by 4 (doubled norm by 32).
- Efficiency: Gray encoding is GF(2)-linear, so d²(a,b) = popcount(gray(a⊕b)) (`d2_eq_pop_gray_xor`) — three machine instructions, no interval traversal and no octad enumeration.
- Limitation made explicit: snapping compresses everything into 4096 states (10 000 consecutive integers hit only 526; explicit collision `snapEnc_collision`), so the method is a metric/encoding layer, not an arithmetic shortcut.
- The propeller-imbalance / TGIC / RuneCube metrics are not defined anywhere in the supplied substrate, so that benchmark table could not be audited.

**Artifacts:** `RequestProject/{GrayCode,Golay,GolayWeights,Decoder,Leech,Shortcut,Main}.lean` build cleanly with no `sorry` and only the standard axioms (all exhaustive checks kernel-evaluated, no `native_decide`); `verify_lattice_shortcut.py` regenerates `lattice_shortcut_directory_corrected.json` with corrected catalogues. All work is committed and pushed.