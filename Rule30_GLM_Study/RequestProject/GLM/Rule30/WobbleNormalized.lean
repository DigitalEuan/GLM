module

public import RequestProject.GLM.Rule30.Wobble

/-!
# Round 16: a normalisation operator for wobble carriers

Suggestion (Round 16 feedback): comparing raw accumulators `D(N)` across different sample sizes
can mislead; add a normalised carrier `D(N)/√N`.

This file gives the exact reason, for words of every length `N`, with no probability theory
beyond counting.  Write a word of `N` bits as `w : Fin N → Bool` and its wobble (the `±1`
accumulator, as in `Wobble.lean`) as `wordWobble w = Σ_i (±1)`.

* `sum_wordWobble`: summed over all `2^N` words the wobble is `0` (no drift).
* **`sum_wordWobble_sq`**: summed over all `2^N` words, `D(N)^2` totals exactly `N · 2^N`.  So the
  mean square of the raw carrier **grows like `N`**, and raw values at different `N` are not
  comparable.
* **`mean_sq_zScore`**: the normalised carrier `z = D(N)/√N` has mean square exactly `1` for every
  `N ≥ 1`.  This is the scale-free quantity to compare.
* **`card_large_zScore_le`** (calibration): at most a fraction `1/λ²` of all words have
  `|z| ≥ λ`.  For example a reading `|z| ≥ 4.3` occurs in fewer than `5.5%` of words of any
  length (a crude but exact bound).

These are statements about the uniform ("fair coin") reference; whether the Rule 30 centre column
behaves like it is Problem 2.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-- `±1` value of a bit. -/
def pm (b : Bool) : ℤ := if b then 1 else -1

@[simp] theorem pm_not (b : Bool) : pm (!b) = -pm b := by cases b <;> rfl

@[simp] theorem pm_mul_self (b : Bool) : pm b * pm b = 1 := by cases b <;> rfl

/-- The wobble (`#ones − #zeros`) of a word of length `N`. -/
def wordWobble {N : ℕ} (w : Fin N → Bool) : ℤ := ∑ i, pm (w i)

/-- Flip bit `i` of a word. -/
def flipBit {N : ℕ} (i : Fin N) (w : Fin N → Bool) : Fin N → Bool := Function.update w i (!w i)

theorem flipBit_involutive {N : ℕ} (i : Fin N) : Function.Involutive (flipBit i) := by
  intro w; funext j
  by_cases h : j = i
  · subst h; simp [flipBit]
  · simp [flipBit, Function.update_of_ne h]

/-- Summing an odd function of bit `i` over all words gives `0`. -/
theorem sum_pm_mul_eq_zero {N : ℕ} (i : Fin N) (g : (Fin N → Bool) → ℤ)
    (hg : ∀ w, g (flipBit i w) = g w) : ∑ w, pm (w i) * g w = 0 := by
  have h := Fintype.sum_equiv (flipBit_involutive i).toPerm
    (fun w => pm (flipBit i w i) * g (flipBit i w)) (fun w => pm (w i) * g w)
    (fun w => by simp)
  have h2 : ∀ w, pm (flipBit i w i) * g (flipBit i w) = -(pm (w i) * g w) := by
    intro w; rw [hg]; simp [flipBit]
  simp only [h2, sum_neg_distrib] at h
  linarith

/-- **No drift:** the wobble sums to `0` over all words of length `N`. -/
theorem sum_wordWobble (N : ℕ) : ∑ w : Fin N → Bool, wordWobble w = 0 := by
  unfold wordWobble
  rw [sum_comm]
  refine sum_eq_zero (fun i _ => ?_)
  simpa using sum_pm_mul_eq_zero i (fun _ => 1) (fun _ => rfl)

/-- **Second moment of the raw carrier:** `Σ_w D(w)² = N · 2^N`. -/
theorem sum_wordWobble_sq (N : ℕ) :
    ∑ w : Fin N → Bool, wordWobble w ^ 2 = N * 2 ^ N := by
  unfold wordWobble
  simp only [sq, sum_mul_sum]
  rw [sum_comm]
  have hterm : ∀ i : Fin N, ∑ w : Fin N → Bool, ∑ j, pm (w i) * pm (w j) = 2 ^ N := by
    intro i
    rw [sum_comm, ← add_sum_erase _ _ (mem_univ i)]
    have hzero : ∀ j ∈ univ.erase i, ∑ w : Fin N → Bool, pm (w i) * pm (w j) = 0 := by
      intro j hj
      have hji : j ≠ i := ne_of_mem_erase hj
      refine sum_pm_mul_eq_zero i (fun w => pm (w j)) (fun w => ?_)
      simp [flipBit, Function.update_of_ne hji]
    rw [sum_eq_zero hzero, add_zero]
    simp [Fintype.card_bool, Fintype.card_fin]
  rw [sum_congr rfl (fun i _ => hterm i)]
  simp

/-- The normalised carrier `z = D(N)/√N`. -/
noncomputable def zScore {N : ℕ} (w : Fin N → Bool) : ℝ := (wordWobble w : ℝ) / Real.sqrt N

/-- **The normalised carrier is scale-free:** its mean square over all words is exactly `1`,
for every length `N ≥ 1`. -/
theorem mean_sq_zScore (N : ℕ) (hN : 1 ≤ N) :
    (∑ w : Fin N → Bool, zScore w ^ 2) / 2 ^ N = 1 := by
  have hN' : (0 : ℝ) < N := by exact_mod_cast hN
  simp only [zScore, div_pow, Real.sq_sqrt hN'.le]
  rw [← sum_div]
  have h := congrArg (fun z : ℤ => (z : ℝ)) (sum_wordWobble_sq N)
  push_cast at h
  rw [h]
  field_simp

/-- **Calibration (Chebyshev, exact counting):** for `λ > 0`, at most `2^N / λ²` words of length
`N ≥ 1` have `|z| ≥ λ`. -/
theorem card_large_zScore_le (N : ℕ) (hN : 1 ≤ N) (lam : ℝ) (hl : 0 < lam) :
    ((univ.filter (fun w : Fin N → Bool => lam ≤ |zScore w|)).card : ℝ) ≤ 2 ^ N / lam ^ 2 := by
  rw [le_div_iff₀ (by positivity)]
  have hmean := mean_sq_zScore N hN
  have hsum : ∑ w : Fin N → Bool, zScore w ^ 2 = 2 ^ N := by
    field_simp at hmean; linarith
  calc ((univ.filter (fun w : Fin N → Bool => lam ≤ |zScore w|)).card : ℝ) * lam ^ 2
      = ∑ w ∈ univ.filter (fun w : Fin N → Bool => lam ≤ |zScore w|), lam ^ 2 := by
        rw [sum_const, nsmul_eq_mul]
    _ ≤ ∑ w ∈ univ.filter (fun w : Fin N → Bool => lam ≤ |zScore w|), zScore w ^ 2 := by
        refine sum_le_sum (fun w hw => ?_)
        have := (mem_filter.mp hw).2
        rw [← sq_abs (zScore w)]
        exact pow_le_pow_left₀ hl.le this 2
    _ ≤ ∑ w : Fin N → Bool, zScore w ^ 2 :=
        sum_le_sum_of_subset_of_nonneg (filter_subset _ _) (fun _ _ _ => sq_nonneg _)
    _ = 2 ^ N := hsum

/-- **Bridge to `Wobble.lean`:** the wobble of the first `N` terms of a sequence is the word wobble
of its length-`N` prefix. -/
theorem wobble_eq_wordWobble (a : ℕ → Bool) (N : ℕ) :
    wobble a N = wordWobble (fun i : Fin N => a i) := by
  induction N with
  | zero => simp [wordWobble]
  | succ N ih =>
    rw [wobble_succ, ih, wordWobble, wordWobble, Fin.sum_univ_castSucc]
    simp [pm]

/-- The normalised carrier of a sequence after `N` terms: `D(N)/√N`.  For the centre column of
Rule 30, `seqZScore centerCol N` is the scale-free reading the GLM should compare across `N`. -/
noncomputable def seqZScore (a : ℕ → Bool) (N : ℕ) : ℝ := (wobble a N : ℝ) / Real.sqrt N

theorem seqZScore_eq (a : ℕ → Bool) (N : ℕ) :
    seqZScore a N = zScore (fun i : Fin N => a i) := by
  rw [seqZScore, zScore, wobble_eq_wordWobble]

end GLM.Rule30
