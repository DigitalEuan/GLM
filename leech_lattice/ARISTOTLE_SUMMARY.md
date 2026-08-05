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