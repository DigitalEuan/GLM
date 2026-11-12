import RequestProject.GLM.Rule30.RunBoundSearch

/-!
# Round 17: the period-2 run bounds extended to `d ≤ 18`

Round 16 (`RunBoundSearch.lean`) certified the exact period-2 run bounds for `d ≤ 16`.  This file
adds `d = 17` and `d = 18` with the same sound search: a column at distance `17` (resp. `18`) from
the black edge of a left-white row stays 2-periodic for at most `24` (resp. `23`) steps, and both
values are attained by explicit rows.  All bounds so far stay below the conjectured `2d + 7`.

The values for `d = 17, 18` agree with the ones Round 16 computed outside Lean.
-/


namespace GLM.Rule30

/-- The exact period-2 run bounds for `d = 0, …, 18`. -/
def runBoundTwoExt18 (d : ℕ) : ℕ :=
  [1, 7, 6, 5, 5, 8, 9, 9, 16, 15, 14, 13, 14, 16, 19, 21, 25, 24, 23].getD d 0

theorem runBoundTwoExt18_agrees : ∀ d ≤ 16, runBoundTwoExt18 d = runBoundTwoExt d := by decide

theorem runSearch_two_seventeen : runSearch 2 17 25 = true := by native_decide

theorem runSearch_two_eighteen : runSearch 2 18 24 = true := by native_decide

/-- **Period-2 run bound for `d ≤ 18` (`CERT`).** -/
theorem runBound_two_upTo_eighteen : RunBoundUpTo 2 runBoundTwoExt18 18 := by
  refine runBoundUpTo_of_searches (by norm_num) fun d hd => ?_
  rcases Nat.lt_or_ge d 17 with h | h
  · rw [runBoundTwoExt18_agrees d (by omega)]
    exact runSearch_two_upTo_sixteen d (by omega)
  · interval_cases d
    · exact runSearch_two_seventeen
    · exact runSearch_two_eighteen

/-- Rows attaining the bounds for `d = 17, 18` (found by a search outside Lean, checked here). -/
theorem witnessCheck_two_seventeen_eighteen :
    witnessCheck 2 17 24 3112283 = true ∧ witnessCheck 2 18 23 4328083 = true := by
  constructor <;> native_decide

/-- **The bounds for `d ≤ 18` are sharp.** -/
theorem runBound_two_witness18 (d : ℕ) (hd : d ≤ 18) :
    ∃ x : Config, (∀ j, j < 0 → x j = false) ∧ x 0 = true ∧
      ∀ t, t + 2 ≤ runBoundTwoExt18 d → evolve x (t + 2) (0 + d) = evolve x t (0 + d) := by
  rcases Nat.lt_or_ge d 17 with h | h
  · rw [runBoundTwoExt18_agrees d (by omega)]
    exact runBound_two_witness d (by omega)
  · interval_cases d
    · exact exists_run_of_witness witnessCheck_two_seventeen_eighteen.1
    · exact exists_run_of_witness witnessCheck_two_seventeen_eighteen.2

theorem runBoundTwoExt18_le_linear : ∀ d ≤ 18, runBoundTwoExt18 d ≤ 2 * d + 7 := by decide

end GLM.Rule30
