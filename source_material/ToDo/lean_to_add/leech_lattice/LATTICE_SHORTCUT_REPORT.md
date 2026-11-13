# Verification report — 24D Leech-lattice "geodesic shortcut" method

**Revision 2** (supersedes revision 1, which was written before
`value_geometry.py`, `ubp_tgic_engine.py` and `tgic_v3.py` were available;
§2 and §3.2 of that revision were wrong as a result — see §7).

**Subject:** the method described in `lattice_shortcode_directory.md`, the data
in `lattice_shortcut_directory_standalone.json`, and the code that produced
them: `generate_shortcut_directory_standalone.py` on top of `ubp_unified_v5.py`,
`value_geometry.py`, `ubp_tgic_engine.py`, with `tgic_v3.py` as the newer TGIC
layer.

**What was done**

1. The published directory was regenerated with the author's own code and
   compared row by row (`audit_ubp_directory.py`, part A).
2. A clean from-scratch implementation (`lattice_shortcut.py`) was checked
   against the substrate function by function — encoders, snap, tax, NRCI and
   all TGIC metrics agree exactly, in exact rational arithmetic (part B).
3. The section-4 benchmark table, which could not be audited before, was
   recomputed (part C).
4. The mathematical core was formalised and machine-checked in Lean 4
   (`RequestProject/*.lean`; builds with no `sorry`, axioms limited to
   `propext, Classical.choice, Quot.sound`, all exhaustive checks
   kernel-evaluated).

**Bottom line.** The published data is now **fully reproducible** (36/36
transitions). The geometric idea is sound and, with one bug fixed, becomes a
correct and efficient method — that fixed method is written up in
`LATTICE_SHORTCUT_METHOD.md` and implemented in `lattice_shortcut.py`. Of the
headline claims: the octad/minimal-vector claim is true in corrected form; the
even-quantisation claim is true but is a property of the Golay code, not of
deep integers; the "adjacent integers jump with `d² ∈ {8,10,12}`" claim is false
as stated; and the propeller-imbalance separation of primes from composites is
false. The `snap_to_codeword` engine has a genuine bug: ~43 % of its outputs are
not codewords.

---

## 1. What the method actually is

For an integer `n`:

1. **Channel split.** Two different maps are used by the generator, and only the
   first is documented in the write-up:
   * `n` **prime** → `x = n & 0xFF`, `y = (n >> 8) & 0xFF`, `z = (n >> 16) & 0xFF`;
   * `n` **composite** → `x = p₁^e₁`, `y = p₂^e₂`, `z = ∏ remaining prime powers`,
     each reduced mod 256.
2. **Gray encoding.** Each 8-bit channel is Gray coded separately (`b ^ b>>1`)
   and written MSB-first. (The write-up describes a *continuous 24-bit* Gray
   code; the code uses the byte-wise version. Both are analysed in Lean:
   `gray`, `grayBytes`.)
3. **Golay snap.** The 24-bit word is corrected towards the extended binary
   Golay code `[24,12,8]`.
4. **Jump vector.** For `a → b`, `Δv = v(b) − v(a) ∈ {−1,0,1}²⁴` and
   `d² = ‖Δv‖²`, which is the Hamming distance of the two encodings
   (`normSq_eq_d2`).

The dual encoder in step 1 is the single most important undocumented detail: it
is why consecutive integers in the published "interfacial" walk are not adjacent
states, and hence why they show large jump norms.

---

## 2. Reproducibility of the published directory

| Catalogue | jump vectors reproduced | jump norms |
|---|---|---|
| Deep Interfacial Sequence, `1 000 033 … 1 000 050` (17 steps) | **17 / 17** | 17 / 17 |
| Deep Prime-to-Prime Trajectory (19 steps) | **19 / 19** | 19 / 19 |

Re-running `generate_shortcut_directory_standalone.py` reproduces
`lattice_shortcut_directory_standalone.json` byte for byte except for last-digit
floating-point noise in five `factor_imbalance` fields (e.g.
`0.6998561597838115` vs `…17`), which is ordinary `math.log` summation
non-determinism. **The published data is authentic output of the supplied
pipeline.**

The `nrci`, `symmetry_tax`, `3axis_orthogonality` and `tgic_stability` fields
also reproduce exactly, as exact rationals, in the independent implementation
(`audit_ubp_directory.py`, part B).

The interfacial catalogue is reproduced at proof level as well:
`interfacial_factorisations` **[Lean]** certifies the prime factorisation of
each of `1 000 033 … 1 000 050`, and
`legacyD2_interfacial_reproduces_directory` **[Lean]** evaluates the generator's
encoder plus the substrate's snap on those factorisations and obtains exactly
the 17 tabulated jump norms `10,8,12,10,8,10,12,14,10,12,8,8,10,10,12,12,14`.

One documentation defect remains: `lattice_shortcode_directory.md` §3 contains
the generator's unexpanded Python template code instead of the rendered table.

---

## 3. Claim-by-claim verdict

Legend: **[Lean]** = machine-checked theorem in `RequestProject/`;
**[audit]** = computed by `audit_ubp_directory.py`; **[self-test]** = checked by
`lattice_shortcut.py --selftest`.

### 3.1 "Adjacent deep integers jump with `d² ∈ {8,10,12}`" — **FALSE as stated**

* The published table itself contains `d² ∈ {8,10,12,14}` for the interfacial
  walk and `{0,2,4,6,8,10,12,14}` overall **[audit]** — so the claimed set is
  wrong even against the author's own data.
* The values have nothing to do with lattice geometry. Under the *documented*
  bit-shift + Gray map, consecutive integers differ in exactly one bit:
  `d2_succ`, `d2_interfacial_all_one`, `rawD2_interfacial` **[Lean]** give
  `d² = 1` for every step of `1 000 033 … 1 000 050`. The large values come
  from the composite branch of the encoder, which throws the Gray adjacency
  away by encoding prime powers instead of the integer.
* Correct statement: *after correct snapping* the interfacial walk has
  `d² ∈ {8,12,16}` under the factor encoder and `d² ∈ {0,8}` under the
  bit-shift encoder (`snapD2_interfacial` **[Lean]**).

### 3.2 "Even quantisation: `d² ∈ 2ℤ`, 100 %" — **TRUE, but it is a theorem about the code, not a measurement**

This is the claim revision 1 of this report got wrong (it evaluated the raw,
unsnapped layer). Verified and then proved:

* 0 odd jump norms in 2 999 consecutive transitions **[audit]**; every state
  produced by the substrate snap has even Hamming weight **[audit]**,
  **[self-test]**.
* `legacySnap_even_weight` **[Lean]**: *every* output of the substrate's
  weight-≤ 3 corrector has even weight. Reason: the Golay code is doubly even,
  so Hamming-weight parity is constant on each coset; the cosets the corrector
  fails on are exactly those whose leader has weight 4 — even. So both branches
  of the engine emit even-weight states.
* `legacy_even_quantisation` **[Lean]**: therefore `d²` is even for **any** two
  snapped states — any encoder, any integers, primes or not. The "100 %" rate
  carries no information about deep integers, primality or the Leech lattice.
* Before snapping there is no such law: on the raw layer `d² ≡ a + b (mod 2)`
  (`d2_mod_two`, `d2_even_iff` **[Lean]**), and `rawD2 1000187 1000193 = 5`
  **[Lean]** is an odd raw norm between two primes.
* Even quantisation is also strictly weaker than what the corrected pipeline
  gives: `legacy_d2_not_div_four` **[Lean]** exhibits a legacy transition with
  `d² = 2`, impossible between genuine codewords. See §4.

### 3.3 "`d² = 8` steps are Class-B minimal-vector octad hops (norm² 32)" — **TRUE in corrected form, and proved**

* `golay_step_isLeech` **[Lean]** — if two states are Golay codewords, the
  doubled jump vector `2Δv` is a genuine element of `Λ₂₄`.
* `normSq_stepVec` **[Lean]** — `‖2Δv‖² = 4·d²`.
* `golay_step_minimal_iff` **[Lean]** — `‖2Δv‖² = 32 ⟺ d² = 8`.
* `leech_min_norm` **[Lean]** — 32 is the minimum norm of `Λ₂₄` (proved from
  scratch), so octad steps really are kissing-sphere hops.
* Caveat for the *published* table: with the buggy snap, 13 of the 20 nodes of
  the prime trajectory are not codewords, and the tabulated norms `0,2,4,6`
  are impossible between real codewords (minimum distance 8). The four steps it
  labels octad steps do have octad supports, but the classification is
  accidental.

### 3.4 The Golay engine — **generator matrix correct, decoder buggy**

* The parity block `B` in `ubp_unified_v5.py` does generate the extended binary
  Golay code: weight enumerator `1 + 759x⁸ + 2576x¹² + 759x¹⁶ + x²⁴`
  (`golay_weight_distribution` **[Lean]**, exhaustive over all 4096 codewords),
  doubly even (`golay_weight_div_four`), minimum distance 8 (`golay_min_dist`).
* **Bug:** `snap_to_codeword` only inverts error patterns of weight ≤ 3. The
  covering radius is 4; on a weight-4 coset it silently returns its input, so
  the "snapped" word is not a codeword.
  * `substrate_snap_fails` **[Lean]** — the word `15` is at distance 4 from the
    code (checked against all 4096 codewords) and is not a codeword;
    `legacySnap_not_codeword` **[Lean]** — the engine returns it unchanged.
  * Measured failure rate: **43.4 %** over a uniform sample of the state space
    and **43.16 %** on 10 000 consecutive integers **[self-test]**, **[audit]**;
    141 of 300 states of the factor-encoded walk **[audit]**.
* `tgic_v3.py` improves on this honestly — it snaps only when the decoder
  certifies the result — but that still leaves states off the code (9 of 60
  face vectors in the sampled rows **[audit]**). `ubp_tgic_engine.py` instead
  re-encodes the information half, which always yields a codeword but can move
  the state by up to 12 bits. The complete decoder removes the dilemma.

### 3.5 The section-4 benchmark table — **now auditable; 8 of 10 cells reproduce**

The sample sets are the first 10 primes ≥ 1 000 000 and the first 10 composites
≥ 1 000 000 **[audit]**:

| Metric | primes (recomputed) | primes (published) | composites (recomputed) | composites (published) |
|---|---|---|---|---|
| Propeller imbalance | 0.000000 | 0.000000 ✔ | 0.622207 | 0.622207 ✔ |
| TGIC 3-axis orthogonality | 0.536182 | 0.536182 ✔ | 0.540989 | 0.540989 ✔ |
| TGIC 6-face coherence | **0.721295** | 0.664642 ✘ | 0.758866 | 0.758866 ✔ |
| RuneCube 3-face avg tax | **3.896754** | 5.247629 ✘ | 3.273274 | 3.273274 ✔ |
| Master TGIC stability | 0.663450 | 0.663450 ✔ | 0.681089 | 0.681089 ✔ |

The two failing cells are also **internally inconsistent with the published
table itself**: master stability is defined as the mean of orthogonality,
face coherence and NRCI, so the printed orthogonality (0.536182) and coherence
(0.664642) imply a stability of 0.644566, not the printed 0.663450. The
recomputed coherence 0.721295 and tax 3.896754 are the values consistent with
the rest of the row; the two published cells appear to come from a different
run. `tgic_v3.py` gives the same corrected figures (0.721295 / 0.663450 for
primes) **[audit]**.

The "Even Quantization Rate 100 %" row is correct but, per §3.2, empty of
content.

### 3.6 "Propeller imbalance: primes 0.0000, composites > 0.1500" — **half true, half false**

`imbalance(n)` is the coefficient of variation of `log p` over the **distinct**
prime factors of `n` (exponents are ignored) **[audit]**.

* "Primes = 0" is true but vacuous: the statistic is 0 for *every* prime power,
  e.g. `1018081 = 1009²` and `1048576 = 2²⁰`.
* "Composites > 0.15" is false: 248 of the 9 247 composites in
  `[10⁶, 10⁶+10⁴)` (2.68 %) fall below 0.15, and `1005973 = 997 × 1009` scores
  0.000866 — inside the "Smooth" band reserved for primes.

The statistic measures how spread out the distinct prime factors are, which is
a real and mildly interesting quantity; it is not a primality test.

---

## 4. The corrected method

Full write-up: `LATTICE_SHORTCUT_METHOD.md`. Implementation:
`lattice_shortcut.py` (`--selftest` re-verifies every guarantee).

### 4.1 Fix — a complete decoder

Replace the weight-≤ 3 corrector by nearest-codeword decoding: syndrome plus a
full 4096-entry coset-leader table. Same run-time cost, one lookup.

* `golay_covering_radius` **[Lean]** — every 24-bit word is within distance 4 of
  a codeword, so complete decoding never fails (`decode_isGolay`,
  `decode_dist_le_four`, `decode_eq_self_of_golay`);
* `decoding_not_unique` **[Lean]** — at distance 4 the nearest codeword is not
  unique (1771 of 4096 cosets have 6 tied weight-4 leaders **[self-test]**), so
  a tie-break convention is required and is fixed explicitly.

With the fix, on the published sequences **[Lean]**, **[audit]**:

| walk | encoder | `d²` per step |
|---|---|---|
| interfacial `1000033 … 1000050` | shift | `8,8,8,8,0,0,8,8,8,8,8,8,8,8,8,8,8` |
| interfacial `1000033 … 1000050` | factor | `16,8,12,12,12,12,12,12,12,12,12,12,8,8,12,12,12` (`snapD2_interfacial_factor` **[Lean]**) |
| prime trajectory (20 primes) | shift | `8,0,0,8,8,8,8,8,8,8,8,0,8,0,8,8,8,8,0` |

and over 10 000 consecutive integers: 74.83 % octad steps, 25.17 % collisions,
every step an exact Leech vector **[audit]**.

* `corrected_step_isLeech`, `corrected_quantized`,
  `corrected_octad_is_minimal_vector` **[Lean]** — *every* transition is an
  exact Leech vector with `d² ∈ {0,8,12,16,24}`, i.e. `‖2Δv‖² ∈ {0,32,48,64,96}`.

So the correct quantisation identity is **`4 ∣ d²`** (doubled norm quantised by
32) — structurally meaningful, unlike the mod-2 version.

### 4.2 The shortcut, stated correctly

Gray coding is `GF(2)`-linear, so

> `d²(a,b) = popcount( gray(a ⊕ b) )`   (`d2_eq_pop_gray_xor` **[Lean]**)

Three machine instructions, independent of `|b − a|`: no interval traversal, no
759-octad expansion (the substrate's `leech_info` path enumerates octads per
query; nothing in the directory needs it). The snapped norm costs two more
table lookups.

### 4.3 What the method does **not** do

Snapping compresses everything into 4096 states: 10 000 consecutive integers
occupy 526 of them **[audit]**, and explicit collisions exist
(`snapEnc_collision`, `snapEnc_range` **[Lean]**). A "geodesic jump" therefore
carries no information that would let one recover or skip to the target
integer. Nothing here accelerates primality testing, factoring or prime search;
in particular the `factor` encoder consumes a factorisation, it does not
produce one.

---

## 5. What is machine-checked

`RequestProject/` builds with Lean 4.28 / Mathlib, **no `sorry`**, axioms
limited to `propext, Classical.choice, Quot.sound`, no `native_decide`.

| File | Contents |
|---|---|
| `GrayCode.lean` | 24-bit Gray layer: `normSq_eq_d2`, `gray_xor`, `d2_eq_pop_gray_xor`, `d2_succ`, `d2_mod_two`, `d2_even_iff`, `d2_interfacial_all_one` |
| `Golay.lean` | Golay code from the substrate's generator: linearity, bounds, weight arithmetic |
| `GolayWeights.lean` | exhaustive weight enumerator, doubly even, minimum distance 8 |
| `Decoder.lean` | syndrome map, packed coset-leader table, covering radius 4, decoder correctness, `substrate_snap_fails`, `decoding_not_unique` |
| `Substrate.lean` | the substrate's engine: `legacySnap_even_weight`, **`legacy_even_quantisation`**, `legacySnap_not_codeword`, `legacy_d2_not_div_four` |
| `Leech.lean` | `Λ₂₄`, **`leech_min_norm`**, `golay_step_isLeech`, `normSq_stepVec`, `golay_step_minimal_iff` |
| `Shortcut.lean` | byte-wise Gray map, corrected pipeline, audit theorems on both catalogues, information-loss statements |
| `FactorMap.lean` | the generator's factorisation encoder: `interfacial_factorisations`, **`legacyD2_interfacial_reproduces_directory`**, `snapD2_interfacial_factor` |

Reproduce with:

```
lake build                        # Lean proofs
python3 lattice_shortcut.py --selftest    # the operational method
python3 audit_ubp_directory.py            # audit of the published directory
```

The last command writes `lattice_shortcut_audit.json` (machine-readable),
`lattice_shortcut_audit.log` (the console transcript) and
`lattice_shortcut_directory_corrected.json` (both catalogues regenerated with
the complete decoder: 53 transitions, all states codewords, all norms in
`{0,8,12,16}`).  Parts A–G of the audit correspond to §2–§3 above.

---

## 6. Recommended revisions to the write-up

1. Document the **dual encoder**. As written, the pipeline diagram implies the
   bit-shift map for all `n`; the composite branch changes every conclusion
   about "adjacent" integers.
2. Replace "adjacent transitions have `d² ∈ {8,10,12}`" by the measured sets:
   raw `d² = 1` under the documented map; `{8,12,16}` under the factor encoder
   after correct snapping; `{0,8}` under the bit-shift encoder.
3. Restate "even quantisation" as what it is: a parity property of Golay cosets
   that holds for any input whatsoever. Report the substantive law `4 ∣ d²`
   instead.
4. Keep the octad claim, in the proved form: doubled differences of snapped
   states are Leech vectors of norm `4·d²`, minimal (32) exactly for octad
   steps.
5. Fix the snap engine to a complete decoder with an explicit tie-break, and
   regenerate all catalogues.
6. Correct the two inconsistent cells of the section-4 table (prime 6-face
   coherence 0.721295, RuneCube tax 3.896754), and render the section-3 table.
7. Withdraw the propeller-imbalance claim about composites, or restate it as a
   statement about the spread of distinct prime factors.
8. Document the collision behaviour (4096 states) so the method is not read as
   an arithmetic shortcut.

---

## 7. What changed since revision 1

Revision 1 was produced without `value_geometry.py`, `ubp_tgic_engine.py` and
`tgic_v3.py`, so `generate_shortcut_directory_standalone.py` could not be run.
Two conclusions were wrong and are corrected here:

* **§2.** Revision 1 reported the "Deep Interfacial Sequence" as unreproducible
  (0/17). It reproduces exactly, 17/17; the missing ingredient was the
  factorisation-based encoder for composites in `value_geometry.py`.
* **§3.2.** Revision 1 called "even quantisation" false. That verdict applied to
  the raw Gray layer. For the pipeline as implemented — i.e. between *snapped*
  states — the claim is true, and is now proved in general
  (`legacy_even_quantisation`), together with the reason it carries no
  information about primes.

Also new: the section-4 benchmark table is now auditable (§3.5), the
propeller-imbalance claim is tested (§3.6), `tgic_v3.py` is compared against
`ubp_tgic_engine.py` (§3.4), and the corrected method has been extracted into a
standalone operational script and explainer.
