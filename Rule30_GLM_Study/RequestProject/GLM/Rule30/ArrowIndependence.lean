import RequestProject.GLM.Rule30.Perspective
import RequestProject.GLM.Rule30.WobbleLensesData

/-!
# Audit round: the wobble arrow is logically independent of Problem 2

The observer's arrow `−sign D(N)` (`observerArrow`, `Perspective.lean`) says which way the run is
currently converging. Round 12 proved that a **persistent** arrow (one that never flips) is
compatible with frequency exactly `1/2` (`exists_balanced_persistent_arrow`). This file proves the
other half:

* `exists_flipping_arrow_unbalanced`: there is a bit sequence whose wobble is positive infinitely
  often **and** negative infinitely often (so its arrow flips forever), and whose frequency of
  ones does **not** tend to `1/2`.

The example is "ones on the dyadic blocks `[2^k − 1, 2^{k+1} − 1)` with `k` even, zeros on the
others"; its wobble at the block ends is exactly `(1 − (−2)^k)/3` (`blockSeq_wobble`).

Together: neither "the arrow keeps flipping" nor "the arrow never flips" says anything about
whether the frequency tends to `1/2`. The arrow is a **local steering signal** for the observer,
not evidence about the limit; this is the precise sense in which it can serve the GLM as a
perspective (which way we are currently heading) but not as a proof object.
-/

namespace GLM.Rule30

open Filter Topology

/-- A run of equal bits moves the wobble by `±` its length. -/
theorem wobble_add_const_block (a : ℕ → Bool) (m L : ℕ) (b : Bool)
    (h : ∀ i, m ≤ i → i < m + L → a i = b) :
    wobble a (m + L) = wobble a m + (if b then (L : ℤ) else -(L : ℤ)) := by
  induction L with
  | zero => simp
  | succ L ih =>
    rw [← add_assoc, wobble_succ, ih (fun i h1 h2 => h i h1 (by omega)), h (m + L) (by omega)
      (by omega)]
    cases b <;> simp <;> ring

/-- Ones on the dyadic blocks `[2^k − 1, 2^{k+1} − 1)` with `k` even, zeros on the others. -/
def blockSeq (n : ℕ) : Bool := decide (Even (Nat.log 2 (n + 1)))

theorem blockSeq_on_block (k i : ℕ) (h1 : 2 ^ k - 1 ≤ i) (h2 : i < 2 ^ k - 1 + 2 ^ k) :
    blockSeq i = decide (Even k) := by
  have hk : 1 ≤ 2 ^ k := Nat.one_le_two_pow
  have hlog : Nat.log 2 (i + 1) = k := by
    rw [Nat.log_eq_iff (Or.inr ⟨by norm_num, by omega⟩)]
    constructor
    · omega
    · rw [pow_succ]; omega
  simp [blockSeq, hlog]

/-- **The wobble at the block ends:** `3 · D(2^k − 1) = 1 − (−2)^k`. -/
theorem blockSeq_wobble (k : ℕ) : 3 * wobble blockSeq (2 ^ k - 1) = 1 - (-2) ^ k := by
  induction k with
  | zero => simp
  | succ k ih =>
    have hk : 1 ≤ 2 ^ k := Nat.one_le_two_pow
    have e : 2 ^ (k + 1) - 1 = (2 ^ k - 1) + 2 ^ k := by rw [pow_succ]; omega
    rw [e, wobble_add_const_block blockSeq _ _ (decide (Even k))
      (fun i h1 h2 => blockSeq_on_block k i h1 h2)]
    rcases Nat.even_or_odd k with hk' | hk'
    · have hp : ((-2 : ℤ)) ^ k = 2 ^ k := hk'.neg_pow 2
      simp only [hk', decide_true, if_true]
      rw [pow_succ, hp]; push_cast; linarith
    · have hp : ((-2 : ℤ)) ^ k = -2 ^ k := hk'.neg_pow 2
      have hne : ¬ Even k := Nat.not_even_iff_odd.mpr hk'
      simp only [hne, decide_false, Bool.false_eq_true, if_false]
      rw [pow_succ, hp]; push_cast; linarith

theorem blockSeq_wobble_odd (m : ℕ) : 0 < wobble blockSeq (2 ^ (2 * m + 1) - 1) := by
  have h := blockSeq_wobble (2 * m + 1)
  have hp : ((-2 : ℤ)) ^ (2 * m + 1) = -2 ^ (2 * m + 1) := (odd_two_mul_add_one m).neg_pow 2
  rw [hp] at h
  have : (0 : ℤ) < 2 ^ (2 * m + 1) := by positivity
  omega

theorem blockSeq_wobble_even (m : ℕ) : wobble blockSeq (2 ^ (2 * m + 2) - 1) < 0 := by
  have h := blockSeq_wobble (2 * m + 2)
  have hp : ((-2 : ℤ)) ^ (2 * m + 2) = 2 ^ (2 * m + 2) :=
    (show Even (2 * m + 2) from ⟨m + 1, by ring⟩).neg_pow 2
  rw [hp] at h
  have : (4 : ℤ) ≤ 2 ^ (2 * m + 2) := by
    rw [pow_add]; nlinarith [one_le_pow₀ (show (1 : ℤ) ≤ 2 ^ 2 by norm_num) (n := m),
      show ((2 : ℤ) ^ (2 * m)) = (2 ^ 2) ^ m by rw [← pow_mul]]
  omega

/-- At the block ends the wobble is at least a third of the length. -/
theorem blockSeq_wobble_large (k : ℕ) :
    ((2 ^ k - 1 : ℕ) : ℝ) ≤ 3 * |(wobble blockSeq (2 ^ k - 1) : ℝ)| := by
  have h := blockSeq_wobble k
  have hk : 1 ≤ 2 ^ k := Nat.one_le_two_pow
  have hle : ((2 ^ k - 1 : ℕ) : ℤ) ≤ |3 * wobble blockSeq (2 ^ k - 1)| := by
    rw [h]
    push_cast [Nat.cast_sub hk]
    rcases Nat.even_or_odd k with hk' | hk'
    · rw [hk'.neg_pow 2]
      rw [abs_of_nonpos (by linarith)]; linarith
    · rw [hk'.neg_pow 2]
      have : (0 : ℤ) < 2 ^ k := by positivity
      rw [abs_of_nonneg (by linarith)]; linarith
  rw [abs_mul] at hle
  have : ((2 ^ k - 1 : ℕ) : ℝ) ≤ |(3 : ℝ)| * |(wobble blockSeq (2 ^ k - 1) : ℝ)| := by
    exact_mod_cast hle
  simpa using this

theorem blockSeq_not_hasFrequencyHalf : ¬ HasFrequencyHalf blockSeq := by
  rw [hasFrequencyHalf_iff]
  intro ht
  have hev := (Metric.tendsto_atTop.mp ht) (1 / 3) (by norm_num)
  obtain ⟨N, hN⟩ := hev
  -- choose a block end beyond `N`
  have hkN : N + 1 ≤ 2 ^ (N + 2) - 1 := by
    have : N + 2 < 2 ^ (N + 2) := Nat.lt_two_pow_self
    omega
  have h1 := hN (2 ^ (N + 2) - 1) (by omega)
  have hpos : (0 : ℝ) < ((2 ^ (N + 2) - 1 : ℕ) : ℝ) := by
    exact_mod_cast (show 0 < 2 ^ (N + 2) - 1 by omega)
  have h2 := blockSeq_wobble_large (N + 2)
  rw [Real.dist_eq, sub_zero, abs_div, abs_of_pos hpos, div_lt_iff₀ hpos] at h1
  linarith

/-- **The arrow can flip forever without the frequency tending to `1/2`.** There is a bit sequence
whose wobble is positive infinitely often and negative infinitely often, and which does not have
frequency `1/2`. -/
theorem exists_flipping_arrow_unbalanced :
    ∃ a : ℕ → Bool, (∀ N, ∃ n ≥ N, 0 < wobble a n) ∧ (∀ N, ∃ n ≥ N, wobble a n < 0) ∧
      ¬ HasFrequencyHalf a := by
  refine ⟨blockSeq, fun N => ⟨2 ^ (2 * N + 1) - 1, ?_, blockSeq_wobble_odd N⟩,
    fun N => ⟨2 ^ (2 * N + 2) - 1, ?_, blockSeq_wobble_even N⟩, blockSeq_not_hasFrequencyHalf⟩
  · have : 2 * N + 1 < 2 ^ (2 * N + 1) := Nat.lt_two_pow_self
    omega
  · have : 2 * N + 2 < 2 ^ (2 * N + 2) := Nat.lt_two_pow_self
    omega

/-- **The arrow is logically independent of Problem 2's condition.** A never-flipping arrow is
compatible with frequency `1/2` (Round 12), and a forever-flipping arrow is compatible with a
frequency that does not tend to `1/2`. -/
theorem arrow_independent_of_frequency :
    (∃ a : ℕ → Bool, HasFrequencyHalf a ∧ ∀ N, 1 ≤ N → 0 < wobble a N) ∧
    (∃ a : ℕ → Bool, (∀ N, ∃ n ≥ N, 0 < wobble a n) ∧ (∀ N, ∃ n ≥ N, wobble a n < 0) ∧
      ¬ HasFrequencyHalf a) :=
  ⟨exists_balanced_persistent_arrow, exists_flipping_arrow_unbalanced⟩

end GLM.Rule30
