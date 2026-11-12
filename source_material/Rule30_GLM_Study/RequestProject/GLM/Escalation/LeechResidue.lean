import RequestProject.GLM.Rule30.ShortcutNetworkData

/-!
# Round 44: residue "syndromes" mod 8, 144 and 256 do not see the Leech lattice

§5.3 of `GLM_Escalation_Boundaries_Exploration.md` proposes the syndromes
`syn_m(v) = (v mod m) + Λ₂₄^(m)` for `m = 2, 4, 8, 144, 256` as a cascade that tells deep-hole
types apart. This file shows, for the GLM's own Golay code, that the last three filters carry no
information at all.

We use the standard integer coordinates of the Leech lattice (Conway's construction from the
extended Golay code `C`): `√8 · Λ₂₄` is the set `LeechZ` of `x ∈ ℤ²⁴` such that

* all `xᵢ` have the same parity `m`,
* `∑ xᵢ ≡ 4m (mod 8)`,
* for each `ν ∈ {0, 1, 2, 3}` the set `{i | xᵢ ≡ ν (mod 4)}` is a codeword of `C`.

Here `C` is the GLM's Golay code `golayWord` (the code of the lattice-shortcut layer). Any
extended binary Golay code gives a lattice isometric to the Leech lattice.

* `leechZ_add_smul` — adding `m · z` (any `z ∈ ℤ²⁴`) keeps a vector in `LeechZ` when `8 ∣ m`:
  `LeechZ + mℤ²⁴ = LeechZ` for `m = 8, 144, 256`.
* `leechZ_sub_of_modEq` — so two integer vectors that agree mod `m` (with `8 ∣ m`) differ by a
  lattice vector: the "syndrome mod m" is the lattice coset itself, the same for `m = 8, 144, 256`.
  Three of the five filters are one filter, and none of them is a finite quotient of order `m²⁴`.
* `leechZ_examples` — sanity checks: `8eᵢ`, `(4, 4, 0, …)`, `(2⁸ on an octad)` and
  `(−3, 1²³)` are lattice vectors (norms 64, 32, 32, 32, i.e. 8, 4, 4, 4 after scaling); `eᵢ` is
  not.

Trust: `leechZ_add_smul` and `leechZ_sub_of_modEq` are FORMAL. The examples are `decide`.
-/

namespace GLM.Escalation.Leech

open GLM.Rule30

/-- `s` is a codeword of the GLM's Golay code (codewords are fixed by their low 12 bits). -/
def IsCodeword (s : ℕ) : Prop := golayWord (s % 4096) = s

instance : DecidablePred IsCodeword := fun s => by unfold IsCodeword; infer_instance

/-- The 24-bit mask of the coordinates congruent to `ν` mod 4. -/
def mask (x : Fin 24 → ℤ) (ν : ℤ) : ℕ :=
  ∑ i : Fin 24, if x i % 4 = ν then 2 ^ (i : ℕ) else 0

/-- `√8 · Λ₂₄` in Conway's integer coordinates. -/
def LeechZ (x : Fin 24 → ℤ) : Prop :=
  (∀ i, x i % 2 = x 0 % 2) ∧ (∑ i, x i) % 8 = 4 * (x 0 % 2) ∧
    ∀ ν : Fin 4, IsCodeword (mask x ν)

instance : DecidablePred LeechZ := fun x => by unfold LeechZ; infer_instance

theorem emod_add_mul_of_dvd {a b m k : ℤ} (hk : k ∣ m) : (a + m * b) % k = a % k := by
  obtain ⟨c, rfl⟩ := hk
  rw [show a + k * c * b = a + k * (c * b) by ring, Int.add_mul_emod_self_left]

/-- **`LeechZ + mℤ²⁴ = LeechZ` when `8 ∣ m`.** -/
theorem leechZ_add_smul {m : ℤ} (hm : 8 ∣ m) (z : Fin 24 → ℤ) {x : Fin 24 → ℤ}
    (hx : LeechZ x) : LeechZ (x + m • z) := by
  have h2 : (2 : ℤ) ∣ m := dvd_trans (by norm_num) hm
  have h4 : (4 : ℤ) ∣ m := dvd_trans (by norm_num) hm
  obtain ⟨hpar, hsum, hcode⟩ := hx
  have e2 : ∀ i, (x + m • z) i % 2 = x i % 2 := fun i => by
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]; exact emod_add_mul_of_dvd h2
  have e4 : ∀ i, (x + m • z) i % 4 = x i % 4 := fun i => by
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]; exact emod_add_mul_of_dvd h4
  refine ⟨fun i => by rw [e2, e2, hpar], ?_, fun ν => ?_⟩
  · have : ∑ i, (x + m • z) i = ∑ i, x i + m * ∑ i, z i := by
      simp [Finset.sum_add_distrib, Finset.mul_sum]
    rw [this, emod_add_mul_of_dvd hm, e2, hsum]
  · have : mask (x + m • z) ν = mask x ν := by
      unfold mask; exact Finset.sum_congr rfl fun i _ => by rw [e4]
    rw [this]; exact hcode ν

/-- The zero vector is in `LeechZ` (the all-ones word is a codeword). -/
theorem leechZ_zero : LeechZ 0 := by decide

/-- **Agreement mod `m` (`8 ∣ m`) means same lattice coset.** -/
theorem leechZ_sub_of_modEq {m : ℤ} (hm : 8 ∣ m) {x y : Fin 24 → ℤ}
    (h : ∀ i, x i ≡ y i [ZMOD m]) : LeechZ (x - y) := by
  have hz : ∀ i, m ∣ x i - y i := fun i => (Int.ModEq.dvd (h i).symm)
  choose z hz using hz
  have : x - y = 0 + m • z := by
    funext i; simp [hz i]
  rw [this]
  exact leechZ_add_smul hm z leechZ_zero

/-- The three moduli of the sketch above the arithmetic regime. -/
theorem eight_dvd_sketch_moduli : (8 : ℤ) ∣ 8 ∧ (8 : ℤ) ∣ 144 ∧ (8 : ℤ) ∣ 256 := by decide

/-- Sanity checks on the construction. -/
theorem leechZ_examples :
    LeechZ (fun i => if i = 0 then 8 else 0) ∧
    LeechZ (fun i => if i.val < 2 then 4 else 0) ∧
    LeechZ (fun i => if i = 0 then -3 else 1) ∧
    ¬ LeechZ (fun i => if i = 0 then 1 else 0) := by
  decide

/-- An octad example: the support of a weight-8 codeword, with entries 2. -/
theorem leechZ_octad :
    ∃ s < 4096, (List.range 24).countP (fun i => (golayWord s).testBit i) = 8 ∧
      LeechZ (fun i => if (golayWord s).testBit i then 2 else 0) := by
  refine ⟨2, by norm_num, by decide, by decide⟩

end GLM.Escalation.Leech
