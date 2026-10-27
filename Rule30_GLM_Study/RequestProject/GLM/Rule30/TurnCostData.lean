import RequestProject.GLM.Rule30.TurnCost
import RequestProject.GLM.Rule30.OneRunFamily
import RequestProject.GLM.Rule30.DiagCert

/-!
# Round 37: the best phases of periods 2 and 3, certified (To Do 40)

(Not a `module`: it uses the `native_decide` checks of `DiagCert.lean`.)

`TurnCost.lean` proves that a slack at one phase of a wheel gives every phase, at the exact cost
`m + (tests skipped)`.  This file certifies the best phases of the period-2 and period-3 wheels
and shows that the cost is **attained**:

* **CERT** `phaseTwo01_slack`: the phase `01` of period 2 (word `2`, black at odd times): every
  code of length `d ≤ 40` fails within `d + 3` tests; slack `2` is false for all `d`
  (`not_phaseTwo01_two`, the code `1`).  So its least slack on `d ≤ 40` is exactly `3`.
* The phase `10` (word `1`) needs slack `5` (`not_phaseTwo10_four`, the Round 33 witness `1493`):
  the difference `5 − 3 = 2` is exactly the proved turn cost `1 + (one test skipped)`.
* **CERT** `phaseThree010_slack`, `phaseThree101_slack`: the phases `010` (word `2`) and `101`
  (word `5`) of period 3 have slacks `5` and `2` on `d ≤ 32`, and `4` resp. `1` are false for all
  `d`.  The worst period-3 phase `100` needs `8 = 5 + 3`, again exactly the turn cost.
* By `testCountLinear_two_of_phase` and `testCountLinear_three_of_phases` the per-period laws
  `TestCountLinear 2 5` and `TestCountLinear 3 8` (the optimal slacks) now follow from **one
  phase statement** for period 2 and two for period 3.

None of this is a statement for all `d`.
-/

namespace GLM.Rule30.TurnCostData

open GLM.Rule30 GLM.Rule30.DiagCert GLM.Rule30.TestCountData

/-- A finite slack check for one word is sound on its range. -/
theorem testSlackUpTo_of_check {p k c D : ℕ} (h : tcIntervalCheckD p k c 1 D = true) :
    TestSlackUpTo (driveN p k) c D := by
  intro d S hd hdD h1 h2
  have hd' := List.all_eq_true.1 h (d - 1) (List.mem_range.2 (by omega))
  rw [show 1 + (d - 1) = d by omega] at hd'
  exact failsWithinTests_of_tcWordCheckD hd hd' h1 h2

/-- A code that passes `d + c` tests refutes slack `c` for one drive, for all `d`. -/
theorem not_testSlack_of_witness {bd : ℕ → Bool} {c d S T : ℕ} (hd : 1 ≤ d)
    (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) (hw : dDiesBy bd S T = false)
    (hT : d + c ≤ testsBefore bd T) : ¬ TestSlack bd c := fun h =>
  not_failsWithinTests_of_dDiesBy hw hT (h d S hd h1 h2)

/-! ## Period 2 -/

theorem check_two_01 : tcIntervalCheckD 2 2 3 1 40 = true := by native_decide

/-- **CERT**: the phase `01` of period 2 has slack `3` on code lengths `d ≤ 40`. -/
theorem phaseTwo01_slack : TestSlackUpTo (driveN 2 2) 3 40 := testSlackUpTo_of_check check_two_01

theorem wit_two_01 : dDiesBy (driveN 2 2) 1 7 = false ∧ 3 ≤ testsBefore (driveN 2 2) 7 := by
  native_decide

/-- Slack `2` is false for the phase `01`, for all `d` (the code `1` passes `3` tests). -/
theorem not_phaseTwo01_two : ¬ TestSlack (driveN 2 2) 2 :=
  not_testSlack_of_witness (d := 1) (S := 1) (by norm_num) (by norm_num) (by norm_num)
    wit_two_01.1 wit_two_01.2

/-- The phase `10` needs slack `5`: slack `4` is false for all `d` (the code `1493`). -/
theorem not_phaseTwo10_four : ¬ TestSlack (driveN 2 1) 4 :=
  not_testSlack_of_witness (d := 11) (S := 1493) (by norm_num) (by norm_num) (by norm_num)
    wit_2.1 wit_2.2

/-- The exact turn cost for period 2: the phase `01` with slack `3` on `d ≤ D + 1` gives the phase
`10` with slack `5` on `d ≤ D`. -/
theorem phaseTwo10_of_01 {D : ℕ} (h : TestSlackUpTo (driveN 2 2) 3 (D + 1)) :
    TestSlackUpTo (driveN 2 1) 5 D := by
  have hw : (fun u => driveN 2 1 (u + 1)) = driveN 2 2 := by
    funext u
    have := Nat.mod_lt u (show 0 < 2 by norm_num)
    simp only [driveN, Nat.add_mod u 1 2]
    interval_cases (u % 2) <;> rfl
  have := testSlackUpTo_of_shift_count (driveN 2 1) 3 1 D (by rw [hw]; exact h)
  have ht : testsBefore (driveN 2 1) 1 = 1 := by decide
  rwa [ht] at this

/-- Through the exact turn cost, the best-phase certificate gives the phase `10` on `d ≤ 39`. -/
theorem phaseTwo10_slack : TestSlackUpTo (driveN 2 1) 5 39 := phaseTwo10_of_01 phaseTwo01_slack

/-! ## Period 3 -/

theorem check_three_010 : tcIntervalCheckD 3 2 5 1 32 = true := by native_decide
theorem check_three_101 : tcIntervalCheckD 3 5 2 1 32 = true := by native_decide

/-- **CERT**: the phase `010` of period 3 has slack `5` on `d ≤ 32`. -/
theorem phaseThree010_slack : TestSlackUpTo (driveN 3 2) 5 32 :=
  testSlackUpTo_of_check check_three_010

/-- **CERT**: the phase `101` of period 3 has slack `2` on `d ≤ 32`. -/
theorem phaseThree101_slack : TestSlackUpTo (driveN 3 5) 2 32 :=
  testSlackUpTo_of_check check_three_101

theorem wit_three_010 :
    dDiesBy (driveN 3 2) 13692578 85 = false ∧ 28 ≤ testsBefore (driveN 3 2) 85 := by
  native_decide

theorem not_phaseThree010_four : ¬ TestSlack (driveN 3 2) 4 :=
  not_testSlack_of_witness (d := 24) (S := 13692578) (by norm_num) (by norm_num) (by norm_num)
    wit_three_010.1 wit_three_010.2

theorem wit_three_101 : dDiesBy (driveN 3 5) 1 3 = false ∧ 2 ≤ testsBefore (driveN 3 5) 3 := by
  native_decide

theorem not_phaseThree101_one : ¬ TestSlack (driveN 3 5) 1 :=
  not_testSlack_of_witness (d := 1) (S := 1) (by norm_num) (by norm_num) (by norm_num)
    wit_three_101.1 wit_three_101.2

/-- The phase `100` needs slack `8`: slack `7` is false for all `d` (the Round 33 code `4161297`),
so the gap `8 − 5 = 3` to the best phase `010` is exactly the turn cost `2 + (one test)`. -/
theorem not_phaseThree100_seven : ¬ TestSlack (driveN 3 1) 7 :=
  not_testSlack_of_witness (d := 22) (S := 4161297) (by norm_num) (by norm_num) (by norm_num)
    wit_3.1 wit_3.2

/-- **Round 37 frontier.**  The exact turn cost (for all `d`), the best phases of periods 2 and 3
with their exact least slacks on the certified ranges, the optimal per-period laws from those
phases alone (for all `d`), and the one-run hub family: a hub for every `q ≥ 2`, the band
`d ≤ q − 4` settled uniformly, and the family containing period 2. -/
theorem frontier_round37 :
    (∀ (bd : ℕ → Bool) (c s : ℕ), TestSlack (fun u => bd (u + s)) c →
        TestSlack bd (c + s + testsBefore bd s)) ∧
    (TestSlackUpTo (driveN 2 2) 3 40 ∧ ¬ TestSlack (driveN 2 2) 2 ∧ ¬ TestSlack (driveN 2 1) 4) ∧
    (TestSlackUpTo (driveN 3 2) 5 32 ∧ ¬ TestSlack (driveN 3 2) 4 ∧
      TestSlackUpTo (driveN 3 5) 2 32 ∧ ¬ TestSlack (driveN 3 5) 1) ∧
    (TestSlack (driveN 2 2) 3 → TestCountLinear 2 5) ∧
    (TestSlack (driveN 3 2) 5 → TestSlack (driveN 3 5) 2 → TestCountLinear 3 8) ∧
    (∀ q, 2 ≤ q → WheelRep q (oneRunWord q)) ∧
    (∀ q d S, d + 4 ≤ q → S < 2 ^ d → FailsWithinTests (driveN q (oneRunWord q)) S (d + 2)) ∧
    (OneRunFamilyDies → HalfLineDies 2) :=
  ⟨testSlack_of_shift_count, ⟨phaseTwo01_slack, not_phaseTwo01_two, not_phaseTwo10_four⟩,
    ⟨phaseThree010_slack, not_phaseThree010_four, phaseThree101_slack, not_phaseThree101_one⟩,
    testCountLinear_two_of_phase, testCountLinear_three_of_phases, fun _ hq => wheelRep_oneRun hq,
    fun _ _ _ hdq hS => oneRun_band hdq hS, halfLineDies_two_of_oneRunFamily⟩

end GLM.Rule30.TurnCostData
