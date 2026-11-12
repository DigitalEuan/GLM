import RequestProject.GolayWeights

/-!
# The Leech lattice `Λ₂₄` and the "geodesic octad step"

We use the standard Golay-code construction of the Leech lattice in the
integral (`×√8`) scaling, in which the minimal norm is `32`:

`x ∈ ℤ²⁴` lies in `Λ₂₄` iff for `m = 0` or `m = 1`

* every coordinate satisfies `x i ≡ m (mod 2)`,
* the set `{ i | x i ≡ m (mod 4) }` is a Golay codeword,
* `∑ i, x i ≡ 4m (mod 8)`.

Main results:

* `LatticeShortcut.leech_min_norm` — every nonzero lattice vector has
  `‖x‖² ≥ 32` (the kissing-sphere radius);
* `LatticeShortcut.golay_step_isLeech` — the doubled difference of **any** two
  Golay codewords is a Leech vector, of norm `4 · d(c₁,c₂)`;
* `LatticeShortcut.golay_step_minimal_iff` — such a step is a *minimal*
  (kissing) vector, `‖·‖² = 32`, exactly when the two codewords are at Hamming
  distance `8`, i.e. exactly when the step is an **octad step**.

This is the corrected form of the "Class B minimal vector octad hop" claim: it
is true for snapped transitions, provided the snap really does land on the code.
-/

namespace LatticeShortcut

/-- The 24-bit mask of a predicate on coordinates. -/
def maskOf (p : Fin 24 → Bool) : ℕ := Nat.ofBits p

/-- Squared Euclidean norm of a 24-dimensional integer vector. -/
def normSq24 (x : Fin 24 → ℤ) : ℤ := ∑ i : Fin 24, (x i) ^ 2

/-- Membership in the Leech lattice, integral (`×√8`) scaling. -/
def IsLeech (x : Fin 24 → ℤ) : Prop :=
  ∃ m : ℤ, (m = 0 ∨ m = 1) ∧
    (∀ i, (2 : ℤ) ∣ (x i - m)) ∧
    IsGolay (maskOf fun i => decide ((4 : ℤ) ∣ (x i - m))) ∧
    (8 : ℤ) ∣ ((∑ i : Fin 24, x i) - 4 * m)

/-! ### Masks of predicates -/

theorem maskOf_lt (p : Fin 24 → Bool) : maskOf p < 2 ^ 24 := Nat.ofBits_lt_two_pow p

theorem bit_maskOf (p : Fin 24 → Bool) (i : Fin 24) :
    bit (maskOf p) (i : ℕ) = if p i then 1 else 0 := by
  rw [bit_eq_testBit, maskOf, Nat.testBit_ofBits_lt p i i.isLt]

theorem pop_maskOf (p : Fin 24 → Bool) :
    pop (maskOf p) = (Finset.univ.filter fun i : Fin 24 => p i).card := by
  rw [pop, ← Fin.sum_univ_eq_sum_range (fun i => bit (maskOf p) i) 24, Finset.card_filter]
  exact Finset.sum_congr rfl fun i _ => bit_maskOf p i

/-- The all-ones word is a Golay codeword. -/
theorem golay_allOnes : IsGolay (2 ^ 24 - 1) := ⟨4095, by norm_num, by decide⟩

/-! ### The minimal norm of `Λ₂₄` -/

private theorem sq_ge_of_mul {a k : ℤ} (c : ℤ) (hk0 : k ≠ 0) (h : a = c * k) :
    c ^ 2 ≤ a ^ 2 := by
  have h1 : 1 ≤ |k| := Int.one_le_abs hk0
  have h2 : 1 ≤ k ^ 2 := by have := abs_mul_abs_self k; nlinarith
  rw [h]; nlinarith [sq_nonneg c]

/-- **The minimal norm of the Leech lattice is 32** in this scaling: every
nonzero lattice vector has `‖x‖² ≥ 32`.

The proof is the classical case analysis: an all-odd vector needs a coordinate
of size `≥ 3` unless the Golay condition and the mod-8 condition on the
coordinate sum contradict each other; an all-even vector either has `≥ 8`
coordinates `≡ 2 (mod 4)` (because a nonzero Golay codeword has weight `≥ 8`),
or is divisible by `4` throughout, in which case the mod-8 sum condition forces
a coordinate of size `≥ 8` or two coordinates of size `≥ 4`. -/
theorem leech_min_norm {x : Fin 24 → ℤ} (hx : IsLeech x) (hne : x ≠ 0) :
    32 ≤ normSq24 x := by
  obtain ⟨m, hm, hpar, hgol, hsum⟩ := hx
  have hw := golay_weight_mem hgol
  rw [pop_maskOf] at hw
  simp only [decide_eq_true_eq] at hw
  have subset_bound : ∀ (T : Finset (Fin 24)) (k : ℤ), (∀ i ∈ T, k ≤ (x i) ^ 2) →
      k * T.card ≤ normSq24 x := by
    intro T k h
    calc k * T.card = ∑ _i ∈ T, k := by rw [Finset.sum_const, nsmul_eq_mul]; ring
    _ ≤ ∑ i ∈ T, (x i) ^ 2 := Finset.sum_le_sum h
    _ ≤ normSq24 x :=
        Finset.sum_le_sum_of_subset_of_nonneg (Finset.subset_univ T) (fun i _ _ => sq_nonneg _)
  rcases hm with rfl | rfl
  · -- all coordinates even
    simp only [sub_zero, mul_zero] at hpar hw hsum
    set S := Finset.univ.filter (fun i : Fin 24 => (4 : ℤ) ∣ x i) with hS
    have hcompl : (Sᶜ.card : ℤ) = 24 - S.card := by
      have h := Finset.card_add_card_compl S
      have h24 : Fintype.card (Fin 24) = 24 := Fintype.card_fin 24
      omega
    by_cases hfull : S.card = 24
    · have hall : ∀ i, (4 : ℤ) ∣ x i := by
        intro i
        have hSu : S = Finset.univ := Finset.eq_univ_of_card S (by simpa using hfull)
        have hi : i ∈ S := hSu ▸ Finset.mem_univ i
        simpa [hS] using (Finset.mem_filter.1 hi).2
      obtain ⟨j, hj⟩ : ∃ j, x j ≠ 0 := by
        by_contra hc
        push_neg at hc
        exact hne (funext fun i => by simpa using hc i)
      have hsq : ∀ i, x i ≠ 0 → 16 ≤ (x i) ^ 2 := by
        intro i hi
        obtain ⟨k, hk⟩ := hall i
        have hk0 : k ≠ 0 := by rintro rfl; rw [mul_zero] at hk; exact hi hk
        simpa using sq_ge_of_mul 4 hk0 hk
      by_cases hother : ∃ k, k ≠ j ∧ x k ≠ 0
      · obtain ⟨k, hkj, hk⟩ := hother
        have hpair : ({j, k} : Finset (Fin 24)).card = 2 := Finset.card_pair (Ne.symm hkj)
        have hb := subset_bound {j, k} 16 (by
          intro i hi
          rcases Finset.mem_insert.1 hi with rfl | hi'
          · exact hsq i hj
          · rw [Finset.mem_singleton] at hi'; subst hi'; exact hsq i hk)
        rw [hpair] at hb
        push_cast at hb
        linarith
      · push_neg at hother
        have hsingle : (∑ i : Fin 24, x i) = x j :=
          Finset.sum_eq_single j (fun i _ hij => hother i hij)
            (fun h => absurd (Finset.mem_univ j) h)
        rw [hsingle] at hsum
        obtain ⟨k, hk⟩ := hsum
        have hk0 : k ≠ 0 := by rintro rfl; rw [mul_zero] at hk; exact hj hk
        have h64 : 64 ≤ (x j) ^ 2 := by simpa using sq_ge_of_mul 8 hk0 hk
        have hb := subset_bound {j} 64 (fun i hi => by
          rw [Finset.mem_singleton] at hi; subst hi; exact h64)
        simp at hb
        linarith
    · have hcard8 : 8 ≤ (Sᶜ.card : ℤ) := by
        rcases hw with h | h | h | h | h
        · rw [h] at hcompl; omega
        · rw [h] at hcompl; omega
        · rw [h] at hcompl; omega
        · rw [h] at hcompl; omega
        · exact absurd h hfull
      have hsq : ∀ i ∈ Sᶜ, (4 : ℤ) ≤ (x i) ^ 2 := by
        intro i hi
        have hnd : ¬ ((4 : ℤ) ∣ x i) := by
          have hm := Finset.mem_compl.1 hi
          simpa [hS] using hm
        obtain ⟨k, hk⟩ := hpar i
        have hk0 : k ≠ 0 := by
          rintro rfl; rw [mul_zero] at hk; rw [hk] at hnd; simp at hnd
        simpa using sq_ge_of_mul 2 hk0 hk
      have hb := subset_bound Sᶜ 4 hsq
      linarith
  · -- all coordinates odd
    have hodd : ∀ i, x i % 2 = 1 := by
      intro i; obtain ⟨k, hk⟩ := hpar i; omega
    have hone : ∀ i, 1 ≤ (x i) ^ 2 := by
      intro i
      have h := hodd i
      have hne0 : x i ≠ 0 := by intro h0; rw [h0] at h; simp at h
      have h1 := Int.one_le_abs hne0
      nlinarith [sq_abs (x i)]
    by_cases hbig : ∃ j, 9 ≤ (x j) ^ 2
    · obtain ⟨j, hj⟩ := hbig
      have hrest : (1 : ℤ) * ((Finset.univ.erase j).card) ≤
          ∑ i ∈ Finset.univ.erase j, (x i) ^ 2 := by
        calc (1 : ℤ) * ((Finset.univ.erase j).card) = ∑ _i ∈ Finset.univ.erase j, (1 : ℤ) := by
              rw [Finset.sum_const, nsmul_eq_mul]; ring
        _ ≤ _ := Finset.sum_le_sum fun i _ => hone i
      have hcard : (Finset.univ.erase j).card = 23 := by
        rw [Finset.card_erase_of_mem (Finset.mem_univ j)]; simp
      rw [hcard] at hrest
      have hsplit : normSq24 x = (x j) ^ 2 + ∑ i ∈ Finset.univ.erase j, (x i) ^ 2 := by
        rw [normSq24, ← Finset.add_sum_erase _ _ (Finset.mem_univ j)]
      rw [hsplit]
      push_cast at hrest
      linarith
    · push_neg at hbig
      have hpm : ∀ i, x i = 1 ∨ x i = -1 := by
        intro i
        have h1 := hodd i
        have h2 := hbig i
        have hb : -3 < x i ∧ x i < 3 := by constructor <;> nlinarith
        omega
      have hset : (Finset.univ.filter fun i : Fin 24 => (4 : ℤ) ∣ (x i - 1))
          = (Finset.univ.filter fun i : Fin 24 => x i = 1) := by
        apply Finset.filter_congr
        intro i _
        rcases hpm i with h | h <;> simp [h]
      rw [hset] at hw
      set S := Finset.univ.filter (fun i : Fin 24 => x i = 1) with hS
      have hsumS : (∑ i : Fin 24, x i) = 2 * (S.card : ℤ) - 24 := by
        rw [← Finset.sum_add_sum_compl S]
        have h1 : ∑ i ∈ S, x i = (S.card : ℤ) := by
          rw [Finset.sum_congr rfl (fun i hi => (Finset.mem_filter.1 hi).2)]
          simp [hS]
        have h2 : ∑ i ∈ Sᶜ, x i = -(Sᶜ.card : ℤ) := by
          rw [Finset.sum_congr rfl (fun i hi => by
            have hni : ¬ (x i = 1) := by
              have hc := Finset.mem_compl.1 hi
              simpa [hS] using hc
            rcases hpm i with h | h
            · exact absurd h hni
            · exact h)]
          simp [hS]
        have h3 : (Sᶜ.card : ℤ) = 24 - S.card := by
          have h := Finset.card_add_card_compl S
          have h24 : Fintype.card (Fin 24) = 24 := Fintype.card_fin 24
          omega
        rw [h1, h2, h3]; ring
      rw [hsumS] at hsum
      exfalso
      rcases hw with h | h | h | h | h <;> rw [h] at hsum <;> omega

/-! ### Golay steps -/

/-- The doubled difference of two 24-bit words, as a 24-dimensional integer
vector with entries in `{-2, 0, 2}`. -/
def stepVec (c₁ c₂ : ℕ) (i : Fin 24) : ℤ := 2 * ((bit c₂ i : ℤ) - (bit c₁ i : ℤ))

theorem normSq_stepVec (c₁ c₂ : ℕ) :
    normSq24 (stepVec c₁ c₂) = 4 * (pop (c₁ ^^^ c₂) : ℤ) := by
  unfold normSq24 stepVec pop
  rw [Fin.sum_univ_eq_sum_range (fun i => (2 * ((bit c₂ i : ℤ) - (bit c₁ i : ℤ))) ^ 2) 24,
    Nat.cast_sum, Finset.mul_sum]
  refine Finset.sum_congr rfl fun i _ => ?_
  simp only [bit_eq_testBit, Nat.testBit_xor]
  cases c₁.testBit i <;> cases c₂.testBit i <;> norm_num

theorem sum_stepVec (c₁ c₂ : ℕ) :
    (∑ i : Fin 24, stepVec c₁ c₂ i) = 2 * ((pop c₂ : ℤ) - (pop c₁ : ℤ)) := by
  unfold stepVec pop
  rw [Fin.sum_univ_eq_sum_range (fun i => 2 * ((bit c₂ i : ℤ) - (bit c₁ i : ℤ))) 24,
    Nat.cast_sum, Nat.cast_sum, ← Finset.sum_sub_distrib, Finset.mul_sum]

theorem maskOf_stepVec {c₁ c₂ : ℕ} (h₁ : c₁ < 2 ^ 24) (h₂ : c₂ < 2 ^ 24) :
    maskOf (fun i => decide ((4 : ℤ) ∣ (stepVec c₁ c₂ i - 0))) = (2 ^ 24 - 1) ^^^ (c₁ ^^^ c₂) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rcases lt_or_ge i 24 with hi | hi
  · rw [maskOf, Nat.testBit_ofBits_lt _ i hi, Nat.testBit_xor, Nat.testBit_two_pow_sub_one,
      Nat.testBit_xor]
    simp only [stepVec, sub_zero, bit_eq_testBit, hi, decide_true, Bool.true_xor]
    cases c₁.testBit i <;> cases c₂.testBit i <;> norm_num
  · rw [maskOf, Nat.testBit_ofBits_ge _ i hi, Nat.testBit_xor, Nat.testBit_two_pow_sub_one,
      Nat.testBit_xor]
    have e1 : c₁.testBit i = false :=
      Nat.testBit_eq_false_of_lt (lt_of_lt_of_le h₁ (Nat.pow_le_pow_right (by norm_num) hi))
    have e2 : c₂.testBit i = false :=
      Nat.testBit_eq_false_of_lt (lt_of_lt_of_le h₂ (Nat.pow_le_pow_right (by norm_num) hi))
    simp [e1, e2, Nat.not_lt.2 hi]

/-- **Every snapped transition is a Leech lattice vector.**  If two states snap
to Golay codewords `c₁, c₂`, the doubled jump vector `2Δv` lies in `Λ₂₄`. -/
theorem golay_step_isLeech {c₁ c₂ : ℕ} (h₁ : IsGolay c₁) (h₂ : IsGolay c₂) :
    IsLeech (stepVec c₁ c₂) := by
  refine ⟨0, Or.inl rfl, fun i => ⟨(bit c₂ i : ℤ) - (bit c₁ i : ℤ), by simp [stepVec]⟩, ?_, ?_⟩
  · rw [maskOf_stepVec (golay_lt h₁) (golay_lt h₂)]
    exact golay_xor_closed golay_allOnes (golay_xor_closed h₁ h₂)
  · rw [sum_stepVec]
    obtain ⟨k₁, hk₁⟩ := golay_weight_div_four h₁
    obtain ⟨k₂, hk₂⟩ := golay_weight_div_four h₂
    refine ⟨(k₂ : ℤ) - (k₁ : ℤ), ?_⟩
    rw [hk₁, hk₂]
    push_cast
    ring

/-- **Octad steps are exactly the minimal (kissing-sphere) transitions.** -/
theorem golay_step_minimal_iff (c₁ c₂ : ℕ) :
    normSq24 (stepVec c₁ c₂) = 32 ↔ pop (c₁ ^^^ c₂) = 8 := by
  rw [normSq_stepVec]
  constructor
  · intro h; omega
  · intro h; rw [h]; norm_num

/-- **Quantisation law for snapped transitions.**  The snapped jump norm is a
Golay weight; in particular it is divisible by `4` — a much stronger statement
than the claimed "`d² ∈ 2ℤ`". -/
theorem golay_step_quantized {c₁ c₂ : ℕ} (h₁ : IsGolay c₁) (h₂ : IsGolay c₂) :
    pop (c₁ ^^^ c₂) = 0 ∨ pop (c₁ ^^^ c₂) = 8 ∨ pop (c₁ ^^^ c₂) = 12 ∨
      pop (c₁ ^^^ c₂) = 16 ∨ pop (c₁ ^^^ c₂) = 24 :=
  golay_weight_mem (golay_xor_closed h₁ h₂)

end LatticeShortcut
