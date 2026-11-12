module

public import RequestProject.GLM.Rule30.TestCountLaw

/-!
# Round 33, To Do 34: halving on the observer's clock

The test-count law (`TestCountLaw.lean`) asks that *every* code of length `d` fail within `d + c`
tests.  The halving form asks for a *counting* statement instead: after `n` tests at most
`2^(d-1+e) / 2^n` of the `2^(d-1)` codes of length `d` are still alive, i.e. each test removes
about half of the survivors, up to a fixed excess `e`.

* `aliveCount bd d n` — the number of codes of length `d` that do not fail within `n` tests;
* `TestHalving p e` — for every non-white word of period `p`, every `d ≥ 1` and every `n`,
  `aliveCount * 2^n ≤ 2^(d-1+e)`;
* `testCountLinear_of_testHalving` — halving with excess `e` gives the test-count law with
  slack `e` (take `n = d + e`: fewer than one code is alive);
* `halfLineDies_of_testHalving`, `problem1_of_testHalving` — the rungs it gives;
* `TestHalvingUpTo p e D` — the same on the code lengths `d ≤ D`, with the two easy halves
  `testHalving_small_n` (nothing to check for `n ≤ e`) and `aliveCount_antitone`
  (nothing to check for `n > d + e` once `n = d + e` is checked).

The certificates for periods 2 and 4 are in `TestHalvingData.lean`.
-/

@[expose] public section

namespace GLM.Rule30

open Classical in
/-- The number of codes of length `d` (top bit `d - 1`) that do **not** fail within their first
`n` tests under the drive `bd`. -/
noncomputable def aliveCount (bd : ℕ → Bool) (d n : ℕ) : ℕ :=
  ((Finset.Ico (2 ^ (d - 1)) (2 ^ d)).filter fun S => ¬ FailsWithinTests bd S n).card

/-- Failing within `n` tests implies failing within any larger number of tests. -/
theorem failsWithinTests_mono {bd : ℕ → Bool} {S m n : ℕ} (h : m ≤ n)
    (hf : FailsWithinTests bd S m) : FailsWithinTests bd S n := by
  obtain ⟨t, hb, hlt, hx⟩ := hf
  exact ⟨t, hb, by omega, hx⟩

/-- The alive count never grows with the number of tests. -/
theorem aliveCount_antitone (bd : ℕ → Bool) (d : ℕ) {m n : ℕ} (h : m ≤ n) :
    aliveCount bd d n ≤ aliveCount bd d m := by
  classical
  unfold aliveCount
  refine Finset.card_le_card fun S hS => ?_
  simp only [Finset.mem_filter] at hS ⊢
  exact ⟨hS.1, fun hm => hS.2 (failsWithinTests_mono h hm)⟩

/-- At most all `2^(d-1)` codes of length `d` are alive. -/
theorem aliveCount_le (bd : ℕ → Bool) {d : ℕ} (hd : 1 ≤ d) (n : ℕ) :
    aliveCount bd d n ≤ 2 ^ (d - 1) := by
  classical
  unfold aliveCount
  refine (Finset.card_filter_le _ _).trans ?_
  rw [Nat.card_Ico]
  obtain ⟨d, rfl⟩ : ∃ d', d = d' + 1 := ⟨d - 1, by omega⟩
  simp [pow_succ]; omega

/-- No code alive means every code fails. -/
theorem failsWithinTests_of_aliveCount_eq_zero {bd : ℕ → Bool} {d n S : ℕ}
    (h0 : aliveCount bd d n = 0) (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) :
    FailsWithinTests bd S n := by
  classical
  by_contra hS
  have : S ∈ (Finset.Ico (2 ^ (d - 1)) (2 ^ d)).filter fun S => ¬ FailsWithinTests bd S n :=
    Finset.mem_filter.2 ⟨Finset.mem_Ico.2 ⟨h1, h2⟩, hS⟩
  have hpos := Finset.card_pos.2 ⟨S, this⟩
  unfold aliveCount at h0
  convert hpos.ne' using 0
  simp only [ne_eq, false_iff, not_not]
  convert h0

/-- **The halving law with excess `e`**: for every non-white word of period `p`, at most
`2^(d-1+e) / 2^n` codes of length `d` survive `n` tests. -/
def TestHalving (p e : ℕ) : Prop :=
  ∀ k, 0 < k → k < 2 ^ p → ∀ d n, 1 ≤ d → aliveCount (driveN p k) d n * 2 ^ n ≤ 2 ^ (d - 1 + e)

/-- The halving law on the code lengths `d ≤ D`. -/
def TestHalvingUpTo (p e D : ℕ) : Prop :=
  ∀ k, 0 < k → k < 2 ^ p → ∀ d n, 1 ≤ d → d ≤ D →
    aliveCount (driveN p k) d n * 2 ^ n ≤ 2 ^ (d - 1 + e)

/-- The halving bound at `n = d + e` forces the alive count to be zero. -/
theorem aliveCount_eq_zero_of_bound {bd : ℕ → Bool} {d e : ℕ} (hd : 1 ≤ d)
    (h : aliveCount bd d (d + e) * 2 ^ (d + e) ≤ 2 ^ (d - 1 + e)) :
    aliveCount bd d (d + e) = 0 := by
  by_contra h0
  have hlt : 2 ^ (d - 1 + e) < 2 ^ (d + e) := Nat.pow_lt_pow_right (by norm_num) (by omega)
  have : 2 ^ (d + e) ≤ aliveCount bd d (d + e) * 2 ^ (d + e) :=
    Nat.le_mul_of_pos_left _ (Nat.pos_of_ne_zero h0)
  omega

/-- **Halving gives the test-count law** with the same constant. -/
theorem testCountLinear_of_testHalving {p e : ℕ} (h : TestHalving p e) : TestCountLinear p e :=
  fun k hk0 hk d _ hd h1 h2 =>
    failsWithinTests_of_aliveCount_eq_zero
      (aliveCount_eq_zero_of_bound hd (h k hk0 hk d (d + e) hd)) h1 h2

/-- The same on a finite range of code lengths. -/
theorem testCountLinearUpTo_of_testHalvingUpTo {p e D : ℕ} (h : TestHalvingUpTo p e D) :
    ∀ k, 0 < k → k < 2 ^ p → ∀ d S, 1 ≤ d → d ≤ D → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
      FailsWithinTests (driveN p k) S (d + e) :=
  fun k hk0 hk d _ hd hdD h1 h2 =>
    failsWithinTests_of_aliveCount_eq_zero
      (aliveCount_eq_zero_of_bound hd (h k hk0 hk d (d + e) hd hdD)) h1 h2

theorem halfLineDies_of_testHalving {p e : ℕ} (h : TestHalving p e) : HalfLineDies p :=
  halfLineDies_of_testCountLinear (testCountLinear_of_testHalving h)

/-- Halving laws for every period (the excess may depend on the period) give Problem 1. -/
theorem problem1_of_testHalving (e : ℕ → ℕ) (h : ∀ p, 0 < p → TestHalving p (e p)) : Problem1 :=
  problem1_of_testCountLinear e fun p hp => testCountLinear_of_testHalving (h p hp)

/-- For `n ≤ e` the halving bound holds for free. -/
theorem testHalving_small_n (bd : ℕ → Bool) {d n e : ℕ} (hd : 1 ≤ d) (hn : n ≤ e) :
    aliveCount bd d n * 2 ^ n ≤ 2 ^ (d - 1 + e) := by
  rw [pow_add]
  exact Nat.mul_le_mul (aliveCount_le bd hd n) (Nat.pow_le_pow_right (by norm_num) hn)

/-- For `n ≥ d + e` the halving bound follows from the bound at `n = d + e`. -/
theorem testHalving_large_n {bd : ℕ → Bool} {d n e : ℕ} (hd : 1 ≤ d) (hn : d + e ≤ n)
    (h : aliveCount bd d (d + e) * 2 ^ (d + e) ≤ 2 ^ (d - 1 + e)) :
    aliveCount bd d n * 2 ^ n ≤ 2 ^ (d - 1 + e) := by
  have h0 := aliveCount_eq_zero_of_bound hd h
  have := aliveCount_antitone bd d hn
  rw [show aliveCount bd d n = 0 by omega]
  simp

end GLM.Rule30
