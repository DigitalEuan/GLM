import RequestProject.GLM.Rule30.TestHalving
import RequestProject.GLM.Rule30.TestCountLawData

/-!
# Round 33, To Do 34: halving certificates for periods 2 and 4

(Not a `module`: the checks use `native_decide`.)

The halving law `TestHalving p e` (`TestHalving.lean`) says that after `n` tests at most
`2^(d-1+e) / 2^n` codes of length `d` are alive.  Measured exactly by
`scripts/test_halving34.c` (every code, every word of period `≤ 4`, `d ≤ 24`), the least
excess is `2, 6, 11, 6` for `p = 1, 2, 3, 4` (EMP; for `p = 3` it is still growing at `d = 24`).
This file certifies the periods 2 and 4:

* `testHalvingUpTo_two : TestHalvingUpTo 2 6 18` and `testHalvingUpTo_four : TestHalvingUpTo 4 6 16`
  (CERT): every alive count is computed exactly, by running every code to the time of the
  `n`-th test, for `e < n ≤ d + e` (the other `n` follow from `testHalving_small_n` and
  `testHalving_large_n`);
* `not_testHalving_two_five`, `not_testHalving_four_five` (CERT, valid for all `d`): excess 5 is
  false — for the word `10`, 2 of the 1024 codes of length 11 survive 15 tests,
  `2 * 2^15 > 2^(10+5)`; for the word `1000`, 18 of the 16384 codes of length 15 survive 15
  tests, `18 * 2^15 > 2^(14+5)`.

On these ranges halving needs one more unit of excess than the test-count law (slack 5 on
`d ≤ 22` for both periods, `frontier_round33`).  For period 4 neither range is the whole story:
the code `974520100` of length 30 refutes slack 6 and hence excess 6
(`not_testCountLinear_four_six`, `not_testHalving_four_six`).  `frontier_round33_halving`
collects this.
-/

namespace GLM.Rule30.TestHalvingData

open GLM.Rule30 GLM.Rule30.TestCountData

/-- The computable alive count: codes of length `d` that pass every check before `T`. -/
def aliveB (p k d T : ℕ) : ℕ :=
  ((Finset.Ico (2 ^ (d - 1)) (2 ^ d)).filter fun S => dDiesBy (driveN p k) S T = false).card

/-- At a time with exactly `n` tests before it, the computable count is the alive count. -/
theorem aliveCount_eq_aliveB {p k d n T : ℕ} (hT : testsBefore (driveN p k) T = n) :
    aliveCount (driveN p k) d n = aliveB p k d T := by
  classical
  unfold aliveCount aliveB
  congr 1
  refine Finset.filter_congr fun S _ => ?_
  constructor
  · intro hS
    cases hd : dDiesBy (driveN p k) S T
    · rfl
    · exact absurd (failsWithinTests_of_dDiesBy hd hT.le) hS
  · intro hd
    exact not_failsWithinTests_of_dDiesBy hd hT.ge

/-- The check for one word: for every `d ≤ D` and `e < n ≤ d + e`, the horizon has exactly `n`
tests before it and the computable alive count obeys the halving bound. -/
def halvWordCheck (p k e D : ℕ) : Bool :=
  (List.range D).all fun i => (List.range (i + 1)).all fun j =>
    decide (testsBefore (driveN p k) (testHorizon p k (e + 1 + j)) = e + 1 + j) &&
      decide (aliveB p k (i + 1) (testHorizon p k (e + 1 + j)) * 2 ^ (e + 1 + j) ≤
        2 ^ (i + 1 - 1 + e))

/-- The check for every non-white word of period `p`. -/
def halvCheck (p e D : ℕ) : Bool :=
  (List.range (2 ^ p - 1)).all fun j => halvWordCheck p (j + 1) e D

theorem testHalvingUpTo_of_halvCheck {p e D : ℕ} (h : halvCheck p e D = true) :
    TestHalvingUpTo p e D := by
  intro k hk0 hk d n hd hdD
  have hw : halvWordCheck p k e D = true := by
    have := List.all_eq_true.1 h (k - 1) (List.mem_range.2 (by
      have : 1 ≤ 2 ^ p := Nat.one_le_two_pow; omega))
    rwa [show k - 1 + 1 = k by omega] at this
  have hrow := List.all_eq_true.1 hw (d - 1) (List.mem_range.2 (by omega))
  rw [show d - 1 + 1 = d by omega] at hrow
  -- the checked range `e < m ≤ d + e`
  have hmid : ∀ m, e < m → m ≤ d + e →
      aliveCount (driveN p k) d m * 2 ^ m ≤ 2 ^ (d - 1 + e) := by
    intro m hm1 hm2
    have hc := List.all_eq_true.1 hrow (m - e - 1) (List.mem_range.2 (by omega))
    rw [show e + 1 + (m - e - 1) = m by omega] at hc
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
    rw [aliveCount_eq_aliveB hc.1]
    exact hc.2
  rcases Nat.lt_or_ge e n with hn | hn
  · rcases Nat.lt_or_ge (d + e) n with hn2 | hn2
    · exact testHalving_large_n hd hn2.le (hmid (d + e) (by omega) le_rfl)
    · exact hmid n hn hn2
  · exact testHalving_small_n _ hd hn

/-- **One count refutes a halving law**: if at a time with exactly `n` tests before it more than
`2^(d-1+e) / 2^n` codes of length `d` are alive, `TestHalving p e` is false. -/
theorem not_testHalving_of_count {p e k d n T : ℕ} (hk0 : 0 < k) (hk : k < 2 ^ p) (hd : 1 ≤ d)
    (hT : testsBefore (driveN p k) T = n) (hc : 2 ^ (d - 1 + e) < aliveB p k d T * 2 ^ n) :
    ¬ TestHalving p e := fun h => by
  have := h k hk0 hk d n hd
  rw [aliveCount_eq_aliveB hT] at this
  omega

/-! ## Certificates -/

theorem halvCheck_two : halvCheck 2 6 18 = true := by native_decide
theorem halvCheck_four : halvCheck 4 6 16 = true := by native_decide

theorem testHalvingUpTo_two : TestHalvingUpTo 2 6 18 := testHalvingUpTo_of_halvCheck halvCheck_two
theorem testHalvingUpTo_four : TestHalvingUpTo 4 6 16 :=
  testHalvingUpTo_of_halvCheck halvCheck_four

theorem count_two :
    testsBefore (driveN 2 1) (testHorizon 2 1 15) = 15 ∧
      2 ^ (11 - 1 + 5) < aliveB 2 1 11 (testHorizon 2 1 15) * 2 ^ 15 := by native_decide

theorem count_four :
    testsBefore (driveN 4 1) (testHorizon 4 1 15) = 15 ∧
      2 ^ (15 - 1 + 5) < aliveB 4 1 15 (testHorizon 4 1 15) * 2 ^ 15 := by native_decide

theorem not_testHalving_two_five : ¬ TestHalving 2 5 :=
  not_testHalving_of_count (k := 1) (d := 11) (by norm_num) (by norm_num) (by norm_num)
    count_two.1 count_two.2

theorem not_testHalving_four_five : ¬ TestHalving 4 5 :=
  not_testHalving_of_count (k := 1) (d := 15) (by norm_num) (by norm_num) (by norm_num)
    count_four.1 count_four.2

/-- Halving with excess 6 fails for period 4 beyond the certified range: it would give
`TestCountLinear 4 6`, refuted by a code of length 30 (`not_testCountLinear_four_six`). -/
theorem not_testHalving_four_six : ¬ TestHalving 4 6 := fun h =>
  not_testCountLinear_four_six (testCountLinear_of_testHalving h)

/-- **Round 33 halving frontier.**  Halving with excess 6 holds for every word of period 2 on
`d ≤ 18` and of period 4 on `d ≤ 16`; for period 2 excess 5 is false (for all `d`), although the
test-count law holds with slack 5 on `d ≤ 22`; for period 4 even excess 6 and slack 6 are false
(a code of length 30), so both period-4 range certificates stop short of the law; halving gives the test-count law with the same
constant, and halving for every period gives Problem 1. -/
theorem frontier_round33_halving :
    (TestHalvingUpTo 2 6 18 ∧ ¬ TestHalving 2 5 ∧ TestCountLinearUpTo 2 5 22) ∧
    (TestHalvingUpTo 4 6 16 ∧ ¬ TestHalving 4 6 ∧ TestCountLinearUpTo 4 5 22 ∧
      ¬ TestCountLinear 4 6) ∧
    (∀ p e, TestHalving p e → TestCountLinear p e) ∧
    (∀ e : ℕ → ℕ, (∀ p, 0 < p → TestHalving p (e p)) → Problem1) :=
  ⟨⟨testHalvingUpTo_two, not_testHalving_two_five, testCountLinearUpTo_two⟩,
    ⟨testHalvingUpTo_four, not_testHalving_four_six, testCountLinearUpTo_four,
      not_testCountLinear_four_six⟩,
    fun _ _ h => testCountLinear_of_testHalving h, problem1_of_testHalving⟩

end GLM.Rule30.TestHalvingData
