import RequestProject.Decoder
import RequestProject.Leech

/-!
# The corrected "lattice shortcut" pipeline, and an audit of the published data

The generator of the published directory
(`lattice_shortcut_directory_standalone.json`) uses the *byte-wise* Gray map
for **primes**: the three 8-bit channels `x = n & 0xFF`, `y = (n >>> 8) & 0xFF`,
`z = (n >>> 16) & 0xFF` are Gray encoded separately and written MSB-first into
coordinates `8k … 8k+7`.  That map is `LatticeShortcut.grayBytes`, and it is
the map documented in the write-up.  (For **composites** the generator instead
fills the channels with the prime powers `p₁^e₁`, `p₂^e₂` and the product of
the remaining ones, reduced mod 256; that branch is audited in
`audit_ubp_directory.py`, since it needs integer factorisation.)

The corrected pipeline is

`n ↦ grayBytes n ↦ decode (grayBytes n) ↦ 2Δ ∈ Λ₂₄`,

where `decode` is the complete (nearest-codeword) Golay decoder of
`RequestProject.Decoder`, not the weight-`≤ 3` corrector of the substrate.

Main results:

* `LatticeShortcut.corrected_step_isLeech` — every corrected transition,
  doubled, is a genuine Leech lattice vector;
* `LatticeShortcut.corrected_quantized` — its squared norm is
  `4 · d² with d² ∈ {0,8,12,16,24}`; the true quantisation is by `4`
  (equivalently, the doubled norm is quantised by `32`), not by `2`;
* `LatticeShortcut.corrected_octad_iff_minimal` — the transition is a
  *minimal* (kissing-sphere) Leech vector exactly when `d² = 8`, i.e. exactly
  when the two snapped states differ by an octad;
* the audit theorems at the end, which evaluate the pipeline on the two
  published catalogues.
-/

namespace LatticeShortcut

set_option maxRecDepth 4000

/-! ### The byte-wise Gray map actually used by the generator -/

/-- Gray encoding of one 8-bit channel. -/
def gray8 (b : ℕ) : ℕ := b ^^^ (b >>> 1)

/-- Bit reversal inside a byte (the generator writes each channel MSB first). -/
def rev8 (b : ℕ) : ℕ := ∑ i ∈ Finset.range 8, bit b (7 - i) * 2 ^ i

/-- The byte-wise Gray map: three separately Gray-encoded 8-bit channels. -/
def grayBytes (n : ℕ) : ℕ :=
  rev8 (gray8 (n % 256)) + 256 * rev8 (gray8 (n / 256 % 256)) +
    65536 * rev8 (gray8 (n / 65536 % 256))

theorem rev8_le (b : ℕ) : rev8 b ≤ 255 := by
  have h : ∀ i ∈ Finset.range 8, bit b (7 - i) * 2 ^ i ≤ 2 ^ i := by
    intro i _
    have := Nat.lt_succ_iff.1 (bit_lt_two b (7 - i))
    exact Nat.mul_le_of_le_div _ _ _ (by simpa using this)
  have := Finset.sum_le_sum h
  simpa [rev8] using this.trans (by decide)

theorem grayBytes_lt (n : ℕ) : grayBytes n < 2 ^ 24 := by
  have h1 := rev8_le (gray8 (n % 256))
  have h2 := rev8_le (gray8 (n / 256 % 256))
  have h3 := rev8_le (gray8 (n / 65536 % 256))
  unfold grayBytes
  omega

/-- The state of `n` after Gray encoding **and** complete Golay snapping. -/
def snapEnc (n : ℕ) : ℕ := decode (grayBytes n)

/-- Squared jump norm of the raw (unsnapped) transition. -/
def rawD2 (a b : ℕ) : ℕ := pop (grayBytes a ^^^ grayBytes b)

/-- Squared jump norm of the snapped transition. -/
def snapD2 (a b : ℕ) : ℕ := pop (snapEnc a ^^^ snapEnc b)

theorem snapEnc_isGolay (n : ℕ) : IsGolay (snapEnc n) :=
  decode_isGolay (grayBytes_lt n)

/-! ### The corrected pipeline lands in the Leech lattice -/

/-- **Every corrected transition is a Leech lattice vector.** -/
theorem corrected_step_isLeech (a b : ℕ) : IsLeech (stepVec (snapEnc a) (snapEnc b)) :=
  golay_step_isLeech (snapEnc_isGolay a) (snapEnc_isGolay b)

/-- **The true quantisation law**: snapped jump norms are Golay weights, hence
multiples of `4` (the doubled lattice vectors have norms in
`{0, 32, 48, 64, 96}`). -/
theorem corrected_quantized (a b : ℕ) :
    snapD2 a b = 0 ∨ snapD2 a b = 8 ∨ snapD2 a b = 12 ∨ snapD2 a b = 16 ∨ snapD2 a b = 24 :=
  golay_step_quantized (snapEnc_isGolay a) (snapEnc_isGolay b)

theorem corrected_normSq (a b : ℕ) :
    normSq24 (stepVec (snapEnc a) (snapEnc b)) = 4 * (snapD2 a b : ℤ) :=
  normSq_stepVec _ _

/-- **Octad steps are exactly the minimal-vector (kissing sphere) steps.** -/
theorem corrected_octad_iff_minimal (a b : ℕ) :
    snapD2 a b = 8 ↔ normSq24 (stepVec (snapEnc a) (snapEnc b)) = 32 :=
  (golay_step_minimal_iff _ _).symm

/-- An octad step is a **minimal** vector of `Λ₂₄`: it has norm `32` and no
nonzero lattice vector has smaller norm. -/
theorem corrected_octad_is_minimal_vector (a b : ℕ) (h : snapD2 a b = 8) :
    normSq24 (stepVec (snapEnc a) (snapEnc b)) = 32 ∧
      ∀ y : Fin 24 → ℤ, IsLeech y → y ≠ 0 → 32 ≤ normSq24 y :=
  ⟨(corrected_octad_iff_minimal a b).1 h, fun _ hy hne => leech_min_norm hy hne⟩

/-! ### Audit of the published catalogues

The generator of `lattice_shortcut_directory_standalone.json` used
`grayBytes` followed by the substrate's weight-`≤ 3` corrector.  The following
theorems evaluate the true jump norms. -/

/-- The byte-wise Gray map reproduces the generator's encoding. -/
theorem grayBytes_1000033 : grayBytes 1000033 = 1099402 := by decide

/-- Under the **documented** map every transition `n → n+1` in
`1000033 … 1000050` has raw jump norm `d² = 1`.  The directory lists
`8, 10, 12, 14` for these steps because its generator encodes composites
through their prime powers instead, so consecutive integers are not adjacent
states at all. -/
theorem rawD2_interfacial :
    ∀ n ∈ Finset.Ico 1000033 1000050, rawD2 n (n + 1) = 1 := by decide

/-- With **correct** Golay decoding the same transitions become genuine
lattice steps: every one of them is either a collision (`d² = 0`) or an octad
step (`d² = 8`). -/
theorem snapD2_interfacial :
    ∀ n ∈ Finset.Ico 1000033 1000050, snapD2 n (n + 1) = 0 ∨ snapD2 n (n + 1) = 8 := by
  decide +kernel

/-- The published prime-to-prime trajectory: true raw jump norms. -/
theorem rawD2_prime_trajectory :
    (List.zipWith rawD2
      [1000003, 1000033, 1000037, 1000039, 1000081, 1000099, 1000117, 1000121, 1000133,
       1000151, 1000159, 1000171, 1000183, 1000187, 1000193, 1000199, 1000211, 1000213,
       1000231]
      [1000033, 1000037, 1000039, 1000081, 1000099, 1000117, 1000121, 1000133, 1000151,
       1000159, 1000171, 1000183, 1000187, 1000193, 1000199, 1000211, 1000213, 1000231,
       1000249])
      = [4, 2, 2, 4, 4, 4, 2, 2, 4, 2, 4, 2, 2, 5, 2, 4, 2, 4, 2] := by decide

/-- Before snapping there is no even-quantisation law: `1000187 → 1000193` has
an odd raw jump norm.  Evenness is produced by the Golay snap alone — see
`RequestProject.Substrate.legacy_even_quantisation`. -/
theorem rawD2_odd_example : rawD2 1000187 1000193 = 5 := by decide

/-- The corrected prime-to-prime trajectory: all steps are collisions or octad
steps. -/
theorem snapD2_prime_trajectory :
    (List.zipWith snapD2
      [1000003, 1000033, 1000037, 1000039, 1000081, 1000099, 1000117, 1000121, 1000133,
       1000151, 1000159, 1000171, 1000183, 1000187, 1000193, 1000199, 1000211, 1000213,
       1000231]
      [1000033, 1000037, 1000039, 1000081, 1000099, 1000117, 1000121, 1000133, 1000151,
       1000159, 1000171, 1000183, 1000187, 1000193, 1000199, 1000211, 1000213, 1000231,
       1000249])
      = [8, 0, 0, 8, 8, 8, 8, 8, 8, 8, 8, 0, 8, 0, 8, 8, 8, 8, 0] := by decide +kernel

/-! ### Information loss of the snap stage -/

/-- Snapped states are codewords, so the whole of `ℕ` is compressed into the
`4096` Golay codewords: the snapped state does not identify the integer. -/
theorem snapEnc_range (n : ℕ) : ∃ m < 4096, snapEnc n = cw m := by
  obtain ⟨m, hm, hcw⟩ := snapEnc_isGolay n
  exact ⟨m, hm, hcw.symm⟩

/-- An explicit collision of the corrected pipeline: two different integers
with the *same* snapped 24D state (a `d² = 0` "transition"). -/
theorem snapEnc_collision : snapEnc 1000037 = snapEnc 1000038 ∧ (1000037 : ℕ) ≠ 1000038 :=
  ⟨by decide +kernel, by decide⟩

end LatticeShortcut
