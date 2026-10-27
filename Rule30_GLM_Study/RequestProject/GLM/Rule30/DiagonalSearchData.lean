import RequestProject.GLM.Rule30.TestCountPeriodsData
import RequestProject.GLM.Rule30.DiagCertTwo
import RequestProject.GLM.Rule30.DiagCertThree
import RequestProject.GLM.Rule30.DiagCertFour1
import RequestProject.GLM.Rule30.DiagCertFour2
import RequestProject.GLM.Rule30.DiagCertFour4
import RequestProject.GLM.Rule30.DiagCertFour8
import RequestProject.GLM.Rule30.DiagCertFourRest

/-!
# Round 35: the observer-clock slacks further out, with the faster checker (To Do 35, 37)

(Not a `module`: it assembles the `native_decide` checks of the `DiagCert*.lean` files.)

The verified diagonal search of `DiagonalSearch.lean` (To Do 37) replaces the Round 22 prefix
search in the per-word slack checks.  Each new certificate covers only the code lengths beyond
the Round 34 one and is joined to it by `testCountLinearUpTo_extend`.

* **CERT** `testCountLinearUpTo_two_five_42`: every code of length `d ≤ 42` fails within `d + 5`
  tests of every non-white period-2 word (Round 34: `d ≤ 34`).
* **CERT** `testCountLinearUpTo_three_eight_32`: slack `8` for period 3 on `d ≤ 32`
  (Round 34: `d ≤ 28`).
* **CERT** `testCountLinearUpTo_four_seven_32`: slack `7` for period 4 on `d ≤ 32`
  (Round 34: `d ≤ 30`).  With `not_testCountLinear_four_six` the least period-4 slack on `d ≤ 32`
  is exactly `7`; likewise `5` (period 2, `d ≤ 42`) and `8` (period 3, `d ≤ 32`).
* **FORMAL bridge** `drivenRunBoundUpTo_of_testCountLinearUpTo` and the **CERT** corollaries
  `runBound_two_upTo_42`, `runBound_three_upTo_32`, `runBound_four_upTo_32`: back in the original
  setting, in **every** left-white row of Rule 30, a column at distance `d` from the left edge
  that follows a non-white periodic pattern of period `2` (`d ≤ 42`), `3` (`d ≤ 32`) or `4`
  (`d ≤ 32`) does so for at most `2(d + 5)`, `3(d + 8)`, `4(d + 7)` steps.

`frontier_round35` collects the round.  None of this is a statement for all `d`: the uniform
laws `TestCountLinear 2 5`, `TestCountLinear 3 8`, `TestCountLinear 4 7` remain open.
-/

namespace GLM.Rule30.DiagCert

open GLM.Rule30 GLM.Rule30.TestCountData

/-- **From the observer's clock back to the wall clock, in the original setting.**  A slack-`c`
certificate on the code lengths `d ≤ D` (plus the trivial check for the white half-line) bounds
the run of every `p`-periodic, non-white column at distance `d ≤ D` from the left edge of a
left-white row by `p · (d + c)` steps. -/
theorem drivenRunBoundUpTo_of_testCountLinearUpTo {p c D : ℕ} (hp : 0 < p)
    (h : TestCountLinearUpTo p c D) (h0 : drivenCheckZero p (p * (0 + c) + 1) = true) :
    DrivenRunBoundUpTo p (fun d => p * (d + c)) D := by
  refine drivenRunBoundUpTo_of_checks hp h0 fun d hdD hd => ?_
  unfold drivenCheck
  rw [List.all_eq_true]
  intro j hj
  rw [List.mem_range] at hj
  rw [List.all_eq_true]
  intro i hi
  rw [List.mem_range] at hi
  have hk : j + 1 < 2 ^ p := by omega
  have hd' : 2 ^ d = 2 ^ (d - 1) + 2 ^ (d - 1) := by
    rw [← two_mul, ← pow_succ']; congr 1; omega
  have hf := h (j + 1) (by omega) hk d (2 ^ (d - 1) + i) hd hdD (by omega) (by omega)
  exact dDiesBy_mono (dDiesBy_of_failsWithinTests_driveN (by omega) hk hf) (by omega)

/-! ## The longer ranges (CERT) -/

theorem testCountLinearUpTo_two_five_42 : TestCountLinearUpTo 2 5 42 := by
  apply testCountLinearUpTo_extend TestCountPeriodsData.testCountLinearUpTo_two_five_long
  intro k hk0 hk
  have hk' : k < 4 := hk
  interval_cases k
  exacts [intervalCheck_two_1, intervalCheck_two_2, intervalCheck_two_3]

theorem testCountLinearUpTo_three_eight_32 : TestCountLinearUpTo 3 8 32 := by
  apply testCountLinearUpTo_extend TestCountPeriodsData.testCountLinearUpTo_three_eight_long
  intro k hk0 hk
  have hr := intervalCheck_three_rest
  simp only [Bool.and_eq_true] at hr
  obtain ⟨⟨⟨h3, h5⟩, h6⟩, h7⟩ := hr
  have hk' : k < 8 := hk
  interval_cases k
  exacts [intervalCheck_three_1, intervalCheck_three_2, h3, intervalCheck_three_4, h5, h6, h7]

theorem testCountLinearUpTo_four_seven_32 : TestCountLinearUpTo 4 7 32 := by
  apply testCountLinearUpTo_extend TestCountPeriodsData.testCountLinearUpTo_four_seven
  intro k hk0 hk
  have hr := intervalCheck_four_rest
  simp only [Bool.and_eq_true] at hr
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨h3, h5⟩, h6⟩, h7⟩, h9⟩, h10⟩, h11⟩, h12⟩, h13⟩, h14⟩, h15⟩ := hr
  have hk' : k < 16 := hk
  interval_cases k
  exacts [intervalCheck_four_1, intervalCheck_four_2, h3, intervalCheck_four_4, h5, h6, h7,
    intervalCheck_four_8, h9, h10, h11, h12, h13, h14, h15]

/-! ## Back to the original setting: run bounds in every left-white row (CERT) -/

/-- **Period 2, `d ≤ 42`.**  In every left-white row, a column at distance `d ≤ 42` from the left
edge that is non-white and `2`-periodic on `[0, L]` has `L ≤ 2 (d + 5)`. -/
theorem runBound_two_upTo_42 : DrivenRunBoundUpTo 2 (fun d => 2 * (d + 5)) 42 :=
  drivenRunBoundUpTo_of_testCountLinearUpTo (by norm_num) testCountLinearUpTo_two_five_42
    (by native_decide)

/-- **Period 3, `d ≤ 32`**: at most `3 (d + 8)` steps. -/
theorem runBound_three_upTo_32 : DrivenRunBoundUpTo 3 (fun d => 3 * (d + 8)) 32 :=
  drivenRunBoundUpTo_of_testCountLinearUpTo (by norm_num) testCountLinearUpTo_three_eight_32
    (by native_decide)

/-- **Period 4, `d ≤ 32`**: at most `4 (d + 7)` steps. -/
theorem runBound_four_upTo_32 : DrivenRunBoundUpTo 4 (fun d => 4 * (d + 7)) 32 :=
  drivenRunBoundUpTo_of_testCountLinearUpTo (by norm_num) testCountLinearUpTo_four_seven_32
    (by native_decide)

/-- **Round 35 frontier.**  On the observer's clock the least slacks are exactly `5` (period 2,
`d ≤ 42`), `8` (period 3, `d ≤ 32`) and `7` (period 4, `d ≤ 32`); the smaller slacks are refuted
for every `d`.  In the original setting this bounds the runs of periodic columns of periods
2, 3, 4 near the left edge of every left-white row. -/
theorem frontier_round35 :
    (TestCountLinearUpTo 2 5 42 ∧ ¬ TestCountLinear 2 4) ∧
    (TestCountLinearUpTo 3 8 32 ∧ ¬ TestCountLinear 3 7) ∧
    (TestCountLinearUpTo 4 7 32 ∧ ¬ TestCountLinear 4 6) ∧
    DrivenRunBoundUpTo 2 (fun d => 2 * (d + 5)) 42 ∧
    DrivenRunBoundUpTo 3 (fun d => 3 * (d + 8)) 32 ∧
    DrivenRunBoundUpTo 4 (fun d => 4 * (d + 7)) 32 :=
  ⟨⟨testCountLinearUpTo_two_five_42, not_testCountLinear_two_four⟩,
    ⟨testCountLinearUpTo_three_eight_32, not_testCountLinear_three_seven⟩,
    ⟨testCountLinearUpTo_four_seven_32, not_testCountLinear_four_six⟩,
    runBound_two_upTo_42, runBound_three_upTo_32, runBound_four_upTo_32⟩

end GLM.Rule30.DiagCert
