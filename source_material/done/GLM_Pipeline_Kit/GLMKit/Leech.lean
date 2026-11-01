import GLMKit.Golay

/-!
# The Leech lattice layer: the parity wall, its real cause, and junction classes

We use the standard integer model of the Leech lattice (Conway–Sloane, *SPLAG* ch. 4 §11,
coordinates scaled by `√8`): `x ∈ ℤ²⁴` lies in `Λ₂₄` iff for some `m ∈ {0,1}`

* every `xᵢ ≡ m (mod 2)`,
* the set `{i | xᵢ ≡ 2 + m (mod 4)}` is a Golay codeword, and
* `∑ xᵢ ≡ 4m (mod 8)`.

This is the membership test used by the iteration-3/4 snaps. We state everything for an
*arbitrary* binary code `C` of any length `n` (only `0 ∈ C` is ever needed), so the results
apply verbatim to the GLM substrate's own (MOG-ordered) Golay code, whatever its coordinate
order; the concrete Golay instance from `GLMKit.Golay` is plugged in at the end.

Main results
* `parity_wall`        : `4·b ∈ Λ  ↔  wt(b)` is even (iteration 3's wall, confirmed).
* `parity_wall_glue`   : the odd-coset candidate `4·b + (-3,1²³)` obeys the same rule.
* `eight_mul_mem`      : `8·v ∈ Λ` for **every** integer vector `v`. So the wall is an artifact of
                         the `4×` embedding, not a limit of `Λ₂₄`: the `8×` embedding never hits it.
* `junction_iff`       : `4b ≡ 4b' (mod 2Λ)  ↔  b ⊕ b' ∈ C ∧ wt b ≡ wt b' (mod 4)`.
* `junction_same_parity` : carriers in the same junction always have the same parity
                         (iteration 8's 100 % same-parity observation, now a theorem).
-/



namespace GLMKit

open Finset

variable {n : ℕ}

/-- Hamming weight (popcount) of a binary vector. -/
def wt (b : Fin n → Bool) : ℕ := (univ.filter fun i => b i = true).card

/-- Integer value `0/1` of a bit. -/
def bitZ (x : Bool) : ℤ := if x then 1 else 0

/-- Leech-type lattice built from a binary code `C` (Construction of SPLAG ch. 4 §11).
For `n = 24` and `C = G₂₄` this is the Leech lattice `Λ₂₄` (scaled by `√8`). -/
def LeechMem (C : Set (Fin n → Bool)) (x : Fin n → ℤ) : Prop :=
  ((∀ i, x i % 2 = 0) ∧ (fun i => decide (x i % 4 = 2)) ∈ C ∧ (∑ i, x i) % 8 = 0) ∨
  ((∀ i, x i % 2 = 1) ∧ (fun i => decide (x i % 4 = 3)) ∈ C ∧ (∑ i, x i) % 8 = 4)

/-- Two integer vectors lie in the same class of `ℤⁿ / 2Λ` (the substrate's `class_of`). -/
def SameClass (C : Set (Fin n → Bool)) (x y : Fin n → ℤ) : Prop :=
  ∃ z, LeechMem C z ∧ ∀ i, x i - y i = 2 * z i

lemma bitZ_cases (x : Bool) : bitZ x = 0 ∨ bitZ x = 1 := by
  cases x <;> simp [bitZ]

lemma sum_bitZ (b : Fin n → Bool) : ∑ i, bitZ (b i) = (wt b : ℤ) := by
  simp [bitZ, wt, Finset.sum_boole]

lemma exists_true_of_wt_pos (b : Fin n → Bool) (h : 0 < wt b) : ∃ i, b i = true := by
  obtain ⟨i, hi⟩ := Finset.card_pos.1 h
  exact ⟨i, (Finset.mem_filter.1 hi).2⟩

/-- **Parity wall (iteration 3).** The `4×` embedding of a binary word `b` is a lattice point
iff `b` has even weight. Holds for any code containing `0`. -/
theorem parity_wall (C : Set (Fin n → Bool)) (h0 : (fun _ => false) ∈ C) (b : Fin n → Bool) :
    LeechMem C (fun i => 4 * bitZ (b i)) ↔ Even (wt b) := by
  have hsum : ∑ i, 4 * bitZ (b i) = 4 * (wt b : ℤ) := by rw [← Finset.mul_sum, sum_bitZ]
  have hset : (fun i => decide (4 * bitZ (b i) % 4 = 2)) = fun _ => false := by
    funext i; cases b i <;> simp [bitZ]
  rw [Nat.even_iff]
  unfold LeechMem
  rw [hsum, hset]
  constructor
  · rintro (⟨-, -, h⟩ | ⟨h1, -, h⟩)
    · omega
    · exfalso
      have hpos : 0 < wt b := by omega
      obtain ⟨i, hi⟩ := exists_true_of_wt_pos b hpos
      have := h1 i
      simp [hi, bitZ] at this
  · intro h
    refine Or.inl ⟨fun i => ?_, h0, by omega⟩
    rcases bitZ_cases (b i) with h' | h' <;> simp only [h'] <;> omega

/-- The canonical odd-coset glue vector `(-3, 1, …, 1)` of length 24. -/
def glue24 (i : Fin 24) : ℤ := if i = 0 then -3 else 1

lemma sum_glue24 : ∑ i, glue24 i = 20 := by
  simp [glue24, Finset.sum_ite, Finset.filter_eq', Finset.filter_ne']

/-- **Parity wall, odd coset.** `4·b + (-3,1²³)` is a lattice point iff `wt b` is even.
So the odd-coset candidate of iteration 3 never rescues an odd-weight target. -/
theorem parity_wall_glue (C : Set (Fin 24 → Bool)) (h0 : (fun _ => false) ∈ C)
    (b : Fin 24 → Bool) :
    LeechMem C (fun i => 4 * bitZ (b i) + glue24 i) ↔ Even (wt b) := by
  have hsum : ∑ i, (4 * bitZ (b i) + glue24 i) = 4 * (wt b : ℤ) + 20 := by
    rw [Finset.sum_add_distrib, ← Finset.mul_sum, sum_bitZ, sum_glue24]
  have hset : (fun i => decide ((4 * bitZ (b i) + glue24 i) % 4 = 3)) = fun _ => false := by
    funext i; unfold glue24; split_ifs <;> cases b i <;> simp [bitZ]
  rw [Nat.even_iff]
  unfold LeechMem
  rw [hsum, hset]
  constructor
  · rintro (⟨h1, -, -⟩ | ⟨-, -, h⟩)
    · exfalso
      have := h1 0
      cases h : b 0 <;> simp [h, bitZ, glue24] at this
    · omega
  · intro h
    refine Or.inr ⟨fun i => ?_, h0, by omega⟩
    show (4 * bitZ (b i) + glue24 i) % 2 = 1
    unfold glue24
    rcases bitZ_cases (b i) with h' | h' <;> rw [h'] <;> split_ifs <;> omega

/-- **The wall is an embedding artifact.** Every vector of `8ℤⁿ` is a lattice point, so the
`8×` embedding `b ↦ 8·b` places *every* binary target (odd or even) inside `Λ₂₄`, without any
escalation to `Λ₃₂`/`Λ₄₈`. -/
theorem eight_mul_mem (C : Set (Fin n → Bool)) (h0 : (fun _ => false) ∈ C) (v : Fin n → ℤ) :
    LeechMem C (fun i => 8 * v i) := by
  have hset : (fun i => decide (8 * v i % 4 = 2)) = fun _ => false := by
    funext i; simp only [decide_eq_false_iff_not]; omega
  refine Or.inl ⟨fun i => by beta_reduce; omega, by rw [hset]; exact h0, ?_⟩
  rw [← Finset.mul_sum]; omega

/-- Binary-target corollary of `eight_mul_mem`. -/
theorem eight_mul_binary_mem (C : Set (Fin n → Bool)) (h0 : (fun _ => false) ∈ C)
    (b : Fin n → Bool) : LeechMem C (fun i => 8 * bitZ (b i)) :=
  eight_mul_mem C h0 _

/-- **Junction classes (iteration 8).** Two `4×`-embedded binary words lie in the same
`Λ/2Λ` class iff they differ by a codeword and their weights agree mod 4. -/
theorem junction_iff (C : Set (Fin n → Bool)) (b b' : Fin n → Bool) :
    SameClass C (fun i => 4 * bitZ (b i)) (fun i => 4 * bitZ (b' i)) ↔
      (fun i => b i != b' i) ∈ C ∧ wt b % 4 = wt b' % 4 := by
  have hsum : ∑ i, 2 * (bitZ (b i) - bitZ (b' i)) = 2 * ((wt b : ℤ) - wt b') := by
    rw [← Finset.mul_sum, Finset.sum_sub_distrib, sum_bitZ, sum_bitZ]
  have hset : (fun i => decide (2 * (bitZ (b i) - bitZ (b' i)) % 4 = 2)) =
      fun i => b i != b' i := by
    funext i; cases b i <;> cases b' i <;> simp [bitZ]
  constructor
  · rintro ⟨z, hz, hdiff⟩
    have hz' : z = fun i => 2 * (bitZ (b i) - bitZ (b' i)) := by
      funext i; have := hdiff i; simp only at this; omega
    subst hz'
    unfold LeechMem at hz
    rw [hsum, hset] at hz
    rcases hz with ⟨-, hC, h⟩ | ⟨h1, -, h⟩
    · exact ⟨hC, by omega⟩
    · exfalso
      rcases isEmpty_or_nonempty (Fin n) with hn | ⟨⟨i⟩⟩
      · have hb : wt b = 0 := by simp [wt]
        have hb' : wt b' = 0 := by simp [wt]
        rw [hb, hb'] at h; omega
      · have := h1 i; beta_reduce at this; omega
  · rintro ⟨hC, hw⟩
    refine ⟨fun i => 2 * (bitZ (b i) - bitZ (b' i)), ?_, fun i => by ring⟩
    unfold LeechMem
    rw [hsum, hset]
    exact Or.inl ⟨fun i => by beta_reduce; omega, hC, by omega⟩

/-- Carriers in the same junction (same `Λ/2Λ` class) always have the same parity. -/
theorem junction_same_parity (C : Set (Fin n → Bool)) (b b' : Fin n → Bool)
    (h : SameClass C (fun i => 4 * bitZ (b i)) (fun i => 4 * bitZ (b' i))) :
    wt b % 2 = wt b' % 2 := by
  have := ((junction_iff C b b').1 h).2
  omega

/-! ### The concrete Leech lattice `Λ₂₄` over the verified Golay code -/

/-- Bitmask of a binary vector of length 24 (coordinate `i` ↦ bit `i`). -/
def toMask (v : Fin 24 → Bool) : ℕ := ∑ i, if v i then 2 ^ (i : ℕ) else 0

/-- The extended Golay code `G₂₄` as a set of binary vectors. -/
def golaySet : Set (Fin 24 → Bool) := {v | toMask v ∈ golayCode}

instance : DecidablePred (· ∈ golaySet) := fun v =>
  inferInstanceAs (Decidable (toMask v ∈ golayCode))

/-- The Leech lattice `Λ₂₄` (integer model, scaled by `√8`). -/
abbrev Leech24 (x : Fin 24 → ℤ) : Prop := LeechMem golaySet x

instance : DecidablePred Leech24 := fun x => by
  unfold Leech24 LeechMem; infer_instance

theorem zero_mem_golaySet : (fun _ => false) ∈ golaySet := by
  show toMask _ ∈ golayCode
  simp [toMask, zero_mem_golay]

/-- Parity wall for the actual Leech lattice. -/
theorem leech24_parity_wall (b : Fin 24 → Bool) :
    Leech24 (fun i => 4 * bitZ (b i)) ↔ Even (wt b) :=
  parity_wall golaySet zero_mem_golaySet b

/-- `8ℤ²⁴ ⊆ Λ₂₄`: the `8×` embedding of any binary grid lands in the Leech lattice. -/
theorem leech24_eight_mul (v : Fin 24 → ℤ) : Leech24 (fun i => 8 * v i) :=
  eight_mul_mem golaySet zero_mem_golaySet v

/-- Sanity checks against the three shapes of minimal Leech vectors (norm 32),
and a non-member. -/
example : Leech24 glue24 := by native_decide
example : Leech24 (fun i => if (i : ℕ) < 2 then 4 else 0) := by native_decide
example : ¬ Leech24 (fun i => if (i : ℕ) = 0 then 4 else 0) := by native_decide

/-! ### Arithmetic of the Leech / Conway layers -/

/-- Minimal-vector count from the three shapes `(±2⁸0¹⁶)`, `(∓3,±1²³)`, `(±4²0²²)`
(uses the 759 octads verified in `GLMKit.Golay`). -/
theorem leech_min_vectors_count :
    759 * 2 ^ 7 + 24 * 2 ^ 12 + Nat.choose 24 2 * 4 = 196560 := by decide

/-- `Λ/2Λ` class census `1 + 98280 + 8386560 + 8292375 = 2²⁴`. -/
theorem leech_class_census : 1 + 98280 + 8386560 + 8292375 = 2 ^ 24 := by norm_num

/-- Sum of cubes of divisors. -/
def sigma3 (k : ℕ) : ℤ := ∑ d ∈ k.divisors, (d : ℤ) ^ 3

/-- Truncated product of power series (coefficient functions). -/
def psMul (a b : ℕ → ℤ) (k : ℕ) : ℤ := ∑ i ∈ range (k + 1), a i * b (k - i)

/-- Eisenstein series `E₄ = 1 + 240 ∑ σ₃(k) qᵏ`. -/
def eisenstein4 (k : ℕ) : ℤ := if k = 0 then 1 else 240 * sigma3 k

/-- `∏_{m=1}^{M} (1 - q^m)`, as a coefficient function. -/
def etaPart : ℕ → ℕ → ℤ
  | 0 => fun k => if k = 0 then 1 else 0
  | m + 1 => psMul (etaPart m) (fun k => if k = 0 then 1 else if k = m + 1 then -1 else 0)

/-- `Δ = q ∏ (1-qᵐ)²⁴`, correct for coefficients up to `q⁵`. -/
def delta (k : ℕ) : ℤ :=
  if k = 0 then 0 else ((List.replicate 24 (etaPart 5)).foldl psMul (fun k => if k = 0 then 1 else 0)) (k - 1)

/-- **Leech theta series** `E₄³ − 720Δ = 1 + 0·q + 196560 q² + 16773120 q³ + 398034000 q⁴ + …`
(here `qᵏ` counts vectors of norm `16k` in the `√8`-scaled model; no vectors of norm 16 =
"no roots", 196560 minimal vectors). -/
theorem leech_theta_coefficients :
    (List.range 5).map (fun k => psMul eisenstein4 (psMul eisenstein4 eisenstein4) k - 720 * delta k)
      = [1, 0, 196560, 16773120, 398034000] := by
  native_decide

end GLMKit
