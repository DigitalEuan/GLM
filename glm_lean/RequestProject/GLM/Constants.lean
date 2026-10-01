/-
# GLM substrate constants: `Y`, `Q`, `TAX`, `NRCI`, coherence regimes

This file formalises the constants table of the GLM top-level README:

| Symbol | Value | Meaning |
|---|---|---|
| `Y` | `1/(π + 2/π)` | read quantum (cost of one active coordinate) |
| `Q` | `Y + 1/8` | activation quantum |
| `B` | `10` | coherence budget |
| `TAX(v)` | `HW(v)·Y + ‖v‖²/8` | topological + geometric cost of a carrier |
| `NRCI(v)` | `B/(B + TAX(v))` | coherence of a carrier |

together with the four coherence regimes (`OnBit ≥ 0.8`, `Coherent ≥ 0.5`,
`Transitional ≥ 0.3`, `Subcoherent < 0.3`) and the proof that each regime,
stated as a band of `NRCI`, is *equivalently* a band of `TAX`.
-/
import Mathlib

namespace GLM

open Finset

/-! ## The two quanta -/

/-- The read quantum `Y = 1/(π + 2/π)`. -/
noncomputable def Y : ℝ := 1 / (Real.pi + 2 / Real.pi)

/-- The activation quantum `Q = Y + 1/8`, the minimum tax of one active coordinate. -/
noncomputable def Q : ℝ := Y + 1 / 8

/-- The coherence budget `B = 10`. -/
def budget : ℝ := 10

lemma pi_add_two_div_pi_pos : 0 < Real.pi + 2 / Real.pi := by
  have h := Real.pi_pos
  positivity

theorem Y_pos : 0 < Y := by
  unfold Y
  exact div_pos one_pos pi_add_two_div_pi_pos

/-- `Y < 1/2`: the read quantum is smaller than the primitive difference share. -/
theorem Y_lt_half : Y < 1 / 2 := by
  unfold Y
  rw [div_lt_div_iff₀ pi_add_two_div_pi_pos (by norm_num)]
  have h1 : (3 : ℝ) < Real.pi := Real.pi_gt_three
  have h2 : (0 : ℝ) < 2 / Real.pi := by positivity
  linarith

/-- `1/4 < Y`. -/
theorem Y_gt_quarter : 1 / 4 < Y := by
  unfold Y
  rw [div_lt_div_iff₀ (by norm_num) pi_add_two_div_pi_pos]
  have h1 : Real.pi < 3.15 := Real.pi_lt_d2
  have h2 : (3 : ℝ) < Real.pi := Real.pi_gt_three
  have h3 : 2 / Real.pi < 2 / 3 := by
    apply div_lt_div_of_pos_left <;> linarith
  linarith

theorem Q_pos : 0 < Q := by
  have := Y_pos
  unfold Q
  linarith

theorem Q_lt_one : Q < 1 := by
  have := Y_lt_half
  unfold Q
  linarith

/-! ## Carriers, Hamming weight, norm, TAX and NRCI -/

variable {n : ℕ}

/-- The Hamming weight of an integer carrier: the number of active coordinates. -/
def hammingWeight (v : Fin n → ℤ) : ℕ := #{i | v i ≠ 0}

/-- The squared Euclidean norm of an integer carrier. -/
def normSq (v : Fin n → ℤ) : ℤ := ∑ i, v i ^ 2

/-- `TAX(v) = HW(v)·Y + ‖v‖²/8`: topological cost plus geometric cost. -/
noncomputable def tax (v : Fin n → ℤ) : ℝ := (hammingWeight v : ℝ) * Y + (normSq v : ℝ) / 8

/-- `NRCI(v) = B/(B + TAX(v))`, the coherence of a carrier. -/
noncomputable def nrci (v : Fin n → ℤ) : ℝ := budget / (budget + tax v)

theorem normSq_nonneg (v : Fin n → ℤ) : 0 ≤ normSq v :=
  Finset.sum_nonneg fun i _ => sq_nonneg (v i)

theorem normSq_eq_zero_iff {v : Fin n → ℤ} : normSq v = 0 ↔ v = 0 := by
  constructor
  · intro h
    funext i
    have := (Finset.sum_eq_zero_iff_of_nonneg
      (fun j (_ : j ∈ (univ : Finset (Fin n))) => sq_nonneg (v j))).1 h i (mem_univ i)
    simpa [pow_eq_zero_iff] using this
  · rintro rfl
    simp [normSq]

theorem hammingWeight_eq_zero_iff {v : Fin n → ℤ} : hammingWeight v = 0 ↔ v = 0 := by
  unfold hammingWeight
  rw [Finset.card_eq_zero, Finset.filter_eq_empty_iff]
  constructor
  · intro h; funext i; simpa using h (mem_univ i)
  · rintro rfl i _; simp

theorem tax_nonneg (v : Fin n → ℤ) : 0 ≤ tax v := by
  have h1 : (0 : ℝ) ≤ (hammingWeight v : ℝ) * Y :=
    mul_nonneg (Nat.cast_nonneg _) Y_pos.le
  have h2 : (0 : ℝ) ≤ (normSq v : ℝ) / 8 := by
    have h : (0 : ℝ) ≤ (normSq v : ℝ) := by exact_mod_cast normSq_nonneg v
    linarith
  unfold tax; linarith

/-- The zero carrier is the unique carrier of zero tax: no disturbance, no cost. -/
theorem tax_eq_zero_iff {v : Fin n → ℤ} : tax v = 0 ↔ v = 0 := by
  constructor
  · intro h
    have h1 : (0 : ℝ) ≤ (hammingWeight v : ℝ) * Y :=
      mul_nonneg (Nat.cast_nonneg _) Y_pos.le
    have h2 : (0 : ℝ) ≤ (normSq v : ℝ) / 8 := by
      have : (0 : ℝ) ≤ (normSq v : ℝ) := by exact_mod_cast normSq_nonneg v
      linarith
    have hw : (hammingWeight v : ℝ) * Y = 0 := by unfold tax at h; linarith
    have : (hammingWeight v : ℝ) = 0 := by
      rcases mul_eq_zero.1 hw with h' | h'
      · exact h'
      · exact absurd h' Y_pos.ne'
    exact hammingWeight_eq_zero_iff.1 (by exact_mod_cast this)
  · rintro rfl
    simp [tax, normSq, hammingWeight]

theorem budget_add_tax_pos (v : Fin n → ℤ) : 0 < budget + tax v := by
  have := tax_nonneg v
  unfold budget
  linarith

theorem nrci_pos (v : Fin n → ℤ) : 0 < nrci v :=
  div_pos (by norm_num [budget]) (budget_add_tax_pos v)

theorem nrci_le_one (v : Fin n → ℤ) : nrci v ≤ 1 := by
  rw [nrci, div_le_one (budget_add_tax_pos v)]
  have := tax_nonneg v
  linarith

/-- Perfect coherence is exactly the vacuum. -/
theorem nrci_eq_one_iff {v : Fin n → ℤ} : nrci v = 1 ↔ v = 0 := by
  rw [nrci, div_eq_one_iff_eq (budget_add_tax_pos v).ne']
  constructor
  · intro h; exact tax_eq_zero_iff.1 (by linarith)
  · rintro rfl; rw [tax_eq_zero_iff.2 rfl]; ring

/-- NRCI is strictly decreasing in TAX. -/
theorem nrci_lt_nrci_of_tax_lt {v w : Fin n → ℤ} (h : tax v < tax w) : nrci w < nrci v := by
  unfold nrci
  apply div_lt_div_of_pos_left (by norm_num [budget]) (budget_add_tax_pos v)
  linarith

/-- A band of NRCI is equivalently a band of TAX. -/
theorem le_nrci_iff {v : Fin n → ℤ} {c : ℝ} :
    c ≤ nrci v ↔ c * (budget + tax v) ≤ budget := by
  rw [nrci, le_div_iff₀ (budget_add_tax_pos v)]

/-! ## Coherence regimes -/

/-- The four coherence regimes of the GLM. -/
inductive CoherenceRegime
  | onBit
  | coherent
  | transitional
  | subcoherent
  deriving DecidableEq, Repr

open scoped Classical in
/-- The regime of a carrier, read off its NRCI. -/
noncomputable def regime (v : Fin n → ℤ) : CoherenceRegime :=
  if 8 / 10 ≤ nrci v then .onBit
  else if 5 / 10 ≤ nrci v then .coherent
  else if 3 / 10 ≤ nrci v then .transitional
  else .subcoherent

theorem regime_onBit_iff {v : Fin n → ℤ} : regime v = .onBit ↔ tax v ≤ 5 / 2 := by
  unfold regime
  constructor
  · intro h
    by_contra hc
    push_neg at hc
    have hn : ¬ (8 / 10 : ℝ) ≤ nrci v := by
      rw [le_nrci_iff]; unfold budget; push_neg; linarith
    rw [if_neg hn] at h
    split_ifs at h
  · intro h
    have hp : (8 / 10 : ℝ) ≤ nrci v := by rw [le_nrci_iff]; unfold budget; linarith
    rw [if_pos hp]

theorem regime_coherent_iff {v : Fin n → ℤ} :
    regime v = .coherent ↔ 5 / 2 < tax v ∧ tax v ≤ 10 := by
  unfold regime
  have h8 : ((8 / 10 : ℝ) ≤ nrci v) ↔ tax v ≤ 5 / 2 := by
    rw [le_nrci_iff]; unfold budget; constructor <;> intro <;> linarith
  have h5 : ((5 / 10 : ℝ) ≤ nrci v) ↔ tax v ≤ 10 := by
    rw [le_nrci_iff]; unfold budget; constructor <;> intro <;> linarith
  constructor
  · intro h
    by_cases hA : (8 / 10 : ℝ) ≤ nrci v
    · rw [if_pos hA] at h; exact absurd h (by simp)
    · rw [if_neg hA] at h
      by_cases hB : (5 / 10 : ℝ) ≤ nrci v
      · rw [h8] at hA; push_neg at hA
        exact ⟨hA, h5.1 hB⟩
      · rw [if_neg hB] at h; split_ifs at h
  · rintro ⟨h1, h2⟩
    have hA : ¬ ((8 / 10 : ℝ) ≤ nrci v) := by rw [h8]; push_neg; linarith
    rw [if_neg hA, if_pos (h5.2 h2)]

theorem regime_transitional_iff {v : Fin n → ℤ} :
    regime v = .transitional ↔ 10 < tax v ∧ tax v ≤ 70 / 3 := by
  unfold regime
  have h8 : ((8 / 10 : ℝ) ≤ nrci v) ↔ tax v ≤ 5 / 2 := by
    rw [le_nrci_iff]; unfold budget; constructor <;> intro <;> linarith
  have h5 : ((5 / 10 : ℝ) ≤ nrci v) ↔ tax v ≤ 10 := by
    rw [le_nrci_iff]; unfold budget; constructor <;> intro <;> linarith
  have h3 : ((3 / 10 : ℝ) ≤ nrci v) ↔ tax v ≤ 70 / 3 := by
    rw [le_nrci_iff]; unfold budget; constructor <;> intro <;> linarith
  constructor
  · intro h
    by_cases hA : (8 / 10 : ℝ) ≤ nrci v
    · rw [if_pos hA] at h; exact absurd h (by simp)
    · rw [if_neg hA] at h
      by_cases hB : (5 / 10 : ℝ) ≤ nrci v
      · rw [if_pos hB] at h; exact absurd h (by simp)
      · rw [if_neg hB] at h
        by_cases hC : (3 / 10 : ℝ) ≤ nrci v
        · rw [h5] at hB; push_neg at hB
          exact ⟨hB, h3.1 hC⟩
        · rw [if_neg hC] at h; exact absurd h (by simp)
  · rintro ⟨h1, h2⟩
    have hA : ¬ ((8 / 10 : ℝ) ≤ nrci v) := by rw [h8]; push_neg; linarith
    have hB : ¬ ((5 / 10 : ℝ) ≤ nrci v) := by rw [h5]; push_neg; linarith
    rw [if_neg hA, if_neg hB, if_pos (h3.2 h2)]

theorem regime_subcoherent_iff {v : Fin n → ℤ} :
    regime v = .subcoherent ↔ 70 / 3 < tax v := by
  unfold regime
  have h8 : ((8 / 10 : ℝ) ≤ nrci v) ↔ tax v ≤ 5 / 2 := by
    rw [le_nrci_iff]; unfold budget; constructor <;> intro <;> linarith
  have h5 : ((5 / 10 : ℝ) ≤ nrci v) ↔ tax v ≤ 10 := by
    rw [le_nrci_iff]; unfold budget; constructor <;> intro <;> linarith
  have h3 : ((3 / 10 : ℝ) ≤ nrci v) ↔ tax v ≤ 70 / 3 := by
    rw [le_nrci_iff]; unfold budget; constructor <;> intro <;> linarith
  constructor
  · intro h
    by_contra hc
    push_neg at hc
    have hC : (3 / 10 : ℝ) ≤ nrci v := h3.2 hc
    by_cases hA : (8 / 10 : ℝ) ≤ nrci v
    · rw [if_pos hA] at h; exact absurd h (by simp)
    · rw [if_neg hA] at h
      by_cases hB : (5 / 10 : ℝ) ≤ nrci v
      · rw [if_pos hB] at h; exact absurd h (by simp)
      · rw [if_neg hB, if_pos hC] at h; exact absurd h (by simp)
  · intro h
    have hA : ¬ ((8 / 10 : ℝ) ≤ nrci v) := by rw [h8]; push_neg; linarith
    have hB : ¬ ((5 / 10 : ℝ) ≤ nrci v) := by rw [h5]; push_neg; linarith
    have hC : ¬ ((3 / 10 : ℝ) ≤ nrci v) := by rw [h3]; push_neg; linarith
    rw [if_neg hA, if_neg hB, if_neg hC]

/-- The vacuum is `OnBit`. -/
theorem regime_zero : regime (0 : Fin n → ℤ) = .onBit := by
  rw [regime_onBit_iff, tax_eq_zero_iff.2 rfl]
  norm_num

end GLM
