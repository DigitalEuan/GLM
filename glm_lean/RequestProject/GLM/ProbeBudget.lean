import Mathlib
import RequestProject.GLM.LatticeCompletion

/-!
# The probe budget: a stopping rule for the certifying reading (Phase 124)

The certifying reading of a deep hole runs modulator starts at the centre and
stops the moment the vertices in hand carry the completeness certificate.  The
census of Phase 123 also stopped it after a fixed number of barren starts (the
*patience*), and three of its centres were left uncertified because the last
vertex had not yet been seen.  This file states the arithmetic of the rule that
replaces the patience: no barren stop, and a budget fixed in advance.

* `miss_bound` — if each of `k` vertices is reached by a start with
  probability at least `p ≥ c / k`, and the budget `B` is at least
  `(k / c) · log (k / δ)`, then the union bound `k (1 - p)^B` is at most `δ`.
* `budget_mono` — that requirement grows with `k`, so a budget that serves the
  largest vertex count serves every smaller one.
* `niemeier_vertexCount_le` — every deep hole has at most 48 vertices
  (`A_1^24`), read off the catalogue of `GLM.LatticeCompletion`.
* `budget_1056_suffices` — with `c = 1/2` and `δ = 1/1000`, the budget
  `B = 1056` serves every Niemeier type.

The probability model (independent starts, each vertex reached with at least
its share) is a model of the deterministic sweep, not a theorem about it; the
file proves the arithmetic the model needs, and the study measures the shares.
-/

namespace GLM.ProbeBudget

open GLM.LatticeCompletion

/-- **The union bound under a budget.**  If every one of `k` vertices is hit by
a start with probability at least `p ≥ c / k`, and the budget is at least
`(k / c) · log (k / δ)`, then the chance that some vertex is still unseen after
the budget, `k (1 - p)^B` by the union bound, is at most `δ`. -/
theorem miss_bound {k : ℕ} (hk : 0 < k) {c p δ : ℝ} (hc : 0 < c)
    (hp : c / k ≤ p) (hp1 : p ≤ 1) (hδ : 0 < δ) {B : ℕ}
    (hB : (k / c) * Real.log (k / δ) ≤ B) :
    (k : ℝ) * (1 - p) ^ B ≤ δ := by
  have hkpos : (0 : ℝ) < k := by exact_mod_cast hk
  have h1 : (1 - p) ^ B ≤ (Real.exp (-(c / k))) ^ B := by
    apply pow_le_pow_left₀ (by linarith)
    calc 1 - p ≤ 1 - c / k := by linarith
      _ ≤ Real.exp (-(c / k)) := by
        have := Real.add_one_le_exp (-(c / k)); linarith
  have h2 : (Real.exp (-(c / k))) ^ B = Real.exp (-(c / k) * B) := by
    rw [← Real.exp_nat_mul]; ring_nf
  have h3 : Real.log (k / δ) ≤ (c / k) * B := by
    have := mul_le_mul_of_nonneg_left hB (le_of_lt (div_pos hc hkpos))
    calc Real.log (k / δ) = (c / k) * ((k / c) * Real.log (k / δ)) := by
          field_simp
      _ ≤ (c / k) * B := this
  have h4 : Real.exp (-(c / k) * B) ≤ δ / k := by
    have : -(c / k) * B ≤ -Real.log (k / δ) := by linarith
    calc Real.exp (-(c / k) * B) ≤ Real.exp (-Real.log (k / δ)) :=
          Real.exp_le_exp.mpr this
      _ = δ / k := by
        rw [Real.exp_neg, Real.exp_log (div_pos hkpos hδ)]; field_simp
  calc (k : ℝ) * (1 - p) ^ B ≤ k * (δ / k) := by
        apply mul_le_mul_of_nonneg_left _ hkpos.le
        calc (1 - p) ^ B ≤ _ := h1
          _ = _ := h2
          _ ≤ _ := h4
    _ = δ := by field_simp

/-- **The requirement grows with the vertex count**, so a budget fixed for the
largest count serves every smaller one. -/
theorem budget_mono {k K : ℕ} (hkK : k ≤ K) {c δ : ℝ} (hc : 0 < c) (hδ : 0 < δ)
    (hδk : δ ≤ k) :
    (k / c) * Real.log (k / δ) ≤ (K / c) * Real.log (K / δ) := by
  have hk : (k : ℝ) ≤ K := by exact_mod_cast hkK
  have hkpos : 0 < (k : ℝ) := lt_of_lt_of_le hδ hδk
  have hl0 : 0 ≤ Real.log (k / δ) :=
    Real.log_nonneg (by rw [le_div_iff₀ hδ]; linarith)
  have hl : Real.log (k / δ) ≤ Real.log (K / δ) :=
    Real.log_le_log (div_pos hkpos hδ) (div_le_div_of_nonneg_right hk hδ.le)
  calc (k / c) * Real.log (k / δ) ≤ (K / c) * Real.log (k / δ) := by
        apply mul_le_mul_of_nonneg_right _ hl0
        exact div_le_div_of_nonneg_right hk hc.le
    _ ≤ (K / c) * Real.log (K / δ) := by
        apply mul_le_mul_of_nonneg_left hl
        have : (0 : ℝ) ≤ K := by linarith
        positivity

/-- **Every deep hole has at most 48 vertices**: the vertex count of a
Niemeier type is its rank, 24, plus its number of components, at most 24. -/
theorem niemeier_vertexCount_le : ∀ L ∈ niemeier, vertexCount L ≤ 48 := by
  decide

/-- `log 48000 ≤ 11`, since `e ≥ 2.7` and `2.7^11 > 48000`. -/
theorem log_48000_le : Real.log ((48 : ℕ) / (1 / 1000 : ℝ)) ≤ 11 := by
  rw [Real.log_le_iff_le_exp (by norm_num)]
  have he : (2.7 : ℝ) ≤ Real.exp 1 := by
    have := Real.exp_one_gt_d9; linarith
  have : (2.7 : ℝ) ^ 11 ≤ Real.exp 1 ^ 11 := pow_le_pow_left₀ (by norm_num) he 11
  rw [← Real.exp_nat_mul] at this
  norm_num at this ⊢
  linarith

/-- **The budget `1056` serves every vertex count up to 48** with `c = 1/2`
and `δ = 1/1000`: whenever every vertex is reached with probability at least
`1 / (2k)`, the union bound on an unseen vertex after 1056 starts is at most
`1/1000`. -/
theorem budget_1056_suffices {k : ℕ} (hk : 0 < k) (hk48 : k ≤ 48) {p : ℝ}
    (hp : (1 / 2 : ℝ) / k ≤ p) (hp1 : p ≤ 1) :
    (k : ℝ) * (1 - p) ^ 1056 ≤ 1 / 1000 := by
  apply miss_bound hk (c := 1 / 2) (by norm_num) hp hp1 (by norm_num)
  have hk1 : (1 : ℝ) ≤ k := by exact_mod_cast hk
  have hmono := budget_mono hk48 (c := 1 / 2) (δ := 1 / 1000) (by norm_num)
    (by norm_num) (by linarith)
  have h48 : ((48 : ℕ) / (1 / 2 : ℝ)) * Real.log ((48 : ℕ) / (1 / 1000 : ℝ))
      ≤ 1056 := by
    have := log_48000_le
    have h96 : ((48 : ℕ) / (1 / 2 : ℝ)) = 96 := by norm_num
    rw [h96]
    push_cast
    nlinarith
  push_cast at hmono h48 ⊢
  linarith

/-- **Every Niemeier type is served by the budget.** -/
theorem budget_serves_every_type :
    ∀ L ∈ niemeier, ∀ p : ℝ, (1 / 2 : ℝ) / vertexCount L ≤ p → p ≤ 1 →
      (vertexCount L : ℝ) * (1 - p) ^ 1056 ≤ 1 / 1000 := by
  intro L hL p hp hp1
  exact budget_1056_suffices (niemeier_vertexCount_pos L hL)
    (niemeier_vertexCount_le L hL) hp hp1

end GLM.ProbeBudget
