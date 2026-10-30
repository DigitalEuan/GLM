import RequestProject.GLM.Rule30.RunBoundSearch

/-!
# Round 19: exact run bounds for periods `3, 4, 5, 6`

Round 6 (`RunBoundData.lean`) certified run bounds for periods `3, …, 6` at distances `d ≤ 4` by
brute force over all windows.  Rounds 16–17 certified the period-2 bounds to `d ≤ 18` with the
pruned diagonal search (`RunBoundSearch.lean`).  This file applies the same sound search to the
next rungs: for every left-white row, the column at distance `d` from the black edge stays
`p`-periodic for at most `B_p(d)` steps, with

| `p` | `B_p(0), B_p(1), …` | certified for |
|---|---|---|
| 3 | 4, 7, 9, 8, 8, 9, 13, 12, 16, 15, 14, 18, 17, 22, 23 | `d ≤ 14` |
| 4 | 7, 7, 9, 9, 10, 12, 13, 13, 16, 15, 18, 19, 19 | `d ≤ 12` |
| 5 | 5, 10, 9, 9, 10, 12, 12, 13, 15, 18, 17, 18, 20 | `d ≤ 12` |
| 6 | 6, 14, 13, 13, 12, 12, 15, 15, 17, 18, 18, 25, 24 | `d ≤ 12` |

and every value is attained by an explicit row (found by a search, checked here).  The values for
`d ≤ 4` agree with Round 6.  All of them satisfy `B_p(d) ≤ 2d + 12`, consistent with a linear
bound for each period; a uniform-in-`d` bound for one period `p` would settle Problem 1 for that
period (`leftWhiteAperiodic_of_runBound`), but no finite table can prove such a bound.
-/

namespace GLM.Rule30

/-- Exact period-3 run bounds, `d ≤ 14`. -/
def runBoundThree (d : ℕ) : ℕ := [4, 7, 9, 8, 8, 9, 13, 12, 16, 15, 14, 18, 17, 22, 23].getD d 0
/-- Exact period-4 run bounds, `d ≤ 12`. -/
def runBoundFour (d : ℕ) : ℕ := [7, 7, 9, 9, 10, 12, 13, 13, 16, 15, 18, 19, 19].getD d 0
/-- Exact period-5 run bounds, `d ≤ 12`. -/
def runBoundFive (d : ℕ) : ℕ := [5, 10, 9, 9, 10, 12, 12, 13, 15, 18, 17, 18, 20].getD d 0
/-- Exact period-6 run bounds, `d ≤ 12`. -/
def runBoundSix (d : ℕ) : ℕ := [6, 14, 13, 13, 12, 12, 15, 15, 17, 18, 18, 25, 24].getD d 0

theorem runBoundPeriods_agree_small :
    (∀ d ≤ 4, runBoundThree d = runBoundSmall 3 d) ∧ (∀ d ≤ 4, runBoundFour d = runBoundSmall 4 d) ∧
      (∀ d ≤ 4, runBoundFive d = runBoundSmall 5 d) ∧ (∀ d ≤ 4, runBoundSix d = runBoundSmall 6 d) := by
  decide

theorem runSearch_three : ∀ d ≤ 14, runSearch 3 d (runBoundThree d + 1) = true := by native_decide
theorem runSearch_four : ∀ d ≤ 12, runSearch 4 d (runBoundFour d + 1) = true := by native_decide
theorem runSearch_five : ∀ d ≤ 12, runSearch 5 d (runBoundFive d + 1) = true := by native_decide
theorem runSearch_six : ∀ d ≤ 12, runSearch 6 d (runBoundSix d + 1) = true := by native_decide

/-- **Period-3 run bound for `d ≤ 14` (`CERT`).** -/
theorem runBound_three_upTo_fourteen : RunBoundUpTo 3 runBoundThree 14 :=
  runBoundUpTo_of_searches (by norm_num) runSearch_three
/-- **Period-4 run bound for `d ≤ 12` (`CERT`).** -/
theorem runBound_four_upTo_twelve : RunBoundUpTo 4 runBoundFour 12 :=
  runBoundUpTo_of_searches (by norm_num) runSearch_four
/-- **Period-5 run bound for `d ≤ 12` (`CERT`).** -/
theorem runBound_five_upTo_twelve : RunBoundUpTo 5 runBoundFive 12 :=
  runBoundUpTo_of_searches (by norm_num) runSearch_five
/-- **Period-6 run bound for `d ≤ 12` (`CERT`).** -/
theorem runBound_six_upTo_twelve : RunBoundUpTo 6 runBoundSix 12 :=
  runBoundUpTo_of_searches (by norm_num) runSearch_six

/-- Witness rows (bit `i` = cell `i`) attaining the bounds. -/
def witnessThree (d : ℕ) : ℕ :=
  [1, 137, 89, 559, 377, 377, 289, 71649, 45305, 4639, 22785, 2360795, 12581923, 16847805,
    8434757].getD d 0
def witnessFour (d : ℕ) : ℕ :=
  [9, 257, 257, 129, 129, 527, 12181, 129, 147585, 16513, 16875439, 4210817, 538968705].getD d 0
def witnessFive (d : ℕ) : ℕ :=
  [1, 3, 1, 265, 73, 13, 35695, 1513, 1054405, 4325, 16812589, 16844689, 134782411].getD d 0
def witnessSix (d : ℕ) : ℕ :=
  [11, 8237, 2123, 16453, 71387, 22545, 9285, 69777, 1215, 135927, 46149, 570941, 281227].getD d 0

theorem witnessCheck_three : ∀ d ≤ 14, witnessCheck 3 d (runBoundThree d) (witnessThree d) = true := by
  native_decide
theorem witnessCheck_four : ∀ d ≤ 12, witnessCheck 4 d (runBoundFour d) (witnessFour d) = true := by
  native_decide
theorem witnessCheck_five : ∀ d ≤ 12, witnessCheck 5 d (runBoundFive d) (witnessFive d) = true := by
  native_decide
theorem witnessCheck_six : ∀ d ≤ 12, witnessCheck 6 d (runBoundSix d) (witnessSix d) = true := by
  native_decide

/-- **The bounds are sharp:** for each `p ∈ {3, 4, 5, 6}` and each certified `d` there is a
left-white row whose column at distance `d` is `p`-periodic on the whole window `[0, B_p(d)]`. -/
theorem runBound_periods_sharp :
    (∀ d ≤ 14, ∃ x : Config, (∀ j, j < 0 → x j = false) ∧ x 0 = true ∧
      ∀ t, t + 3 ≤ runBoundThree d → evolve x (t + 3) (0 + d) = evolve x t (0 + d)) ∧
    (∀ d ≤ 12, ∃ x : Config, (∀ j, j < 0 → x j = false) ∧ x 0 = true ∧
      ∀ t, t + 4 ≤ runBoundFour d → evolve x (t + 4) (0 + d) = evolve x t (0 + d)) ∧
    (∀ d ≤ 12, ∃ x : Config, (∀ j, j < 0 → x j = false) ∧ x 0 = true ∧
      ∀ t, t + 5 ≤ runBoundFive d → evolve x (t + 5) (0 + d) = evolve x t (0 + d)) ∧
    (∀ d ≤ 12, ∃ x : Config, (∀ j, j < 0 → x j = false) ∧ x 0 = true ∧
      ∀ t, t + 6 ≤ runBoundSix d → evolve x (t + 6) (0 + d) = evolve x t (0 + d)) :=
  ⟨fun d hd => exists_run_of_witness (witnessCheck_three d hd),
    fun d hd => exists_run_of_witness (witnessCheck_four d hd),
    fun d hd => exists_run_of_witness (witnessCheck_five d hd),
    fun d hd => exists_run_of_witness (witnessCheck_six d hd)⟩

/-- Every certified value is at most `2d + 12`. -/
theorem runBoundPeriods_le_linear :
    (∀ d ≤ 14, runBoundThree d ≤ 2 * d + 12) ∧ (∀ d ≤ 12, runBoundFour d ≤ 2 * d + 12) ∧
      (∀ d ≤ 12, runBoundFive d ≤ 2 * d + 12) ∧ (∀ d ≤ 12, runBoundSix d ≤ 2 * d + 12) := by
  decide

end GLM.Rule30
