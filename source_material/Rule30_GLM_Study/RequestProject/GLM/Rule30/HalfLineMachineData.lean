import RequestProject.GLM.Rule30.HalfLineMachine
import RequestProject.GLM.Rule30.RunBoundSearch
import RequestProject.GLM.Rule30.PeriodTwoHalfLineData

/-!
# Round 21: finite certificates for the driven half-line, periods 3–6

The driven half-line machine (`HalfLineMachine.lean`) gives run bounds for every period without
looking at the cells right of the column.  A certificate for period `p` and distance `d`
enumerates the `2^p - 1` non-white drive words and the `2^(d-1)` codes of the cells between the
edge and the column.

* `machineBound p d` — the largest first-failure time of the machine over all drive words and
  codes (exact for the machine, `machineBound_sharp`).
* `drivenRunBound_three` (`d ≤ 20`), `drivenRunBound_four` (`d ≤ 18`),
  `drivenRunBound_five` (`d ≤ 16`), `drivenRunBound_six` (`d ≤ 16`) — `CERT`.
* `runBound_upTo_of_driven` — together with the proved constant-run bound `3d + 5` (white
  drives), a full period-`p` run bound.  `runBound_three_upTo_20` etc.

The earlier exact certificates (`RunBoundPeriods.lean`) covered periods 3 (`d ≤ 14`) and 4–6
(`d ≤ 12`); their values are the true maxima and are smaller.  The machine values here are upper
bounds valid further out.
-/

namespace GLM.Rule30

/-- Machine bounds (maximum first-failure time), period `p`, distance `d`. -/
def machineBound : ℕ → ℕ → ℕ
  | 3, d => [5, 7, 10, 15, 14, 14, 13, 14, 24, 23, 29, 28, 29, 41, 40, 39, 41, 41, 56, 56,
      55].getD d 0
  | 4, d => [7, 13, 12, 11, 15, 14, 18, 31, 30, 34, 33, 39, 38, 62, 61, 73, 72, 71, 70].getD d 0
  | 5, d => [8, 19, 18, 17, 16, 40, 39, 38, 37, 44, 43, 46, 53, 60, 59, 62, 63].getD d 0
  | 6, d => [10, 17, 25, 24, 23, 29, 37, 49, 48, 58, 57, 79, 78, 79, 78, 77, 104].getD d 0
  | _, _ => 0

/-! ### Period 3 -/

theorem drivenCheckZero_three : drivenCheckZero 3 (machineBound 3 0 + 1) = true := by native_decide

theorem drivenCheck_three_a : ∀ d ≤ 16, 1 ≤ d → drivenCheck 3 d (machineBound 3 d + 1) = true := by
  native_decide

theorem drivenCheck_three_b : ∀ d ≤ 18, 17 ≤ d → drivenCheck 3 d (machineBound 3 d + 1) = true := by
  native_decide

theorem drivenCheck_three_19 : drivenCheck 3 19 (machineBound 3 19 + 1) = true := by native_decide

theorem drivenCheck_three_20 : drivenCheck 3 20 (machineBound 3 20 + 1) = true := by native_decide

/-- **Period 3, non-white drives, `d ≤ 20`** (`CERT`). -/
theorem drivenRunBound_three : DrivenRunBoundUpTo 3 (machineBound 3) 20 := by
  refine drivenRunBoundUpTo_of_checks (by norm_num) drivenCheckZero_three fun d hd h1 => ?_
  rcases Nat.lt_or_ge d 17 with h | h
  · exact drivenCheck_three_a d (by omega) h1
  rcases Nat.lt_or_ge d 19 with h' | h'
  · exact drivenCheck_three_b d (by omega) h
  interval_cases d
  · exact drivenCheck_three_19
  · exact drivenCheck_three_20

/-! ### Period 4 -/

theorem drivenCheckZero_four : drivenCheckZero 4 (machineBound 4 0 + 1) = true := by native_decide

theorem drivenCheck_four_a : ∀ d ≤ 16, 1 ≤ d → drivenCheck 4 d (machineBound 4 d + 1) = true := by
  native_decide

theorem drivenCheck_four_17 : drivenCheck 4 17 (machineBound 4 17 + 1) = true := by native_decide

theorem drivenCheck_four_18 : drivenCheck 4 18 (machineBound 4 18 + 1) = true := by native_decide

/-- **Period 4, non-white drives, `d ≤ 18`** (`CERT`). -/
theorem drivenRunBound_four : DrivenRunBoundUpTo 4 (machineBound 4) 18 := by
  refine drivenRunBoundUpTo_of_checks (by norm_num) drivenCheckZero_four fun d hd h1 => ?_
  rcases Nat.lt_or_ge d 17 with h | h
  · exact drivenCheck_four_a d (by omega) h1
  interval_cases d
  · exact drivenCheck_four_17
  · exact drivenCheck_four_18

/-! ### Periods 5 and 6 -/

theorem drivenCheckZero_five : drivenCheckZero 5 (machineBound 5 0 + 1) = true := by native_decide

theorem drivenCheck_five : ∀ d ≤ 16, 1 ≤ d → drivenCheck 5 d (machineBound 5 d + 1) = true := by
  native_decide

/-- **Period 5, non-white drives, `d ≤ 16`** (`CERT`). -/
theorem drivenRunBound_five : DrivenRunBoundUpTo 5 (machineBound 5) 16 :=
  drivenRunBoundUpTo_of_checks (by norm_num) drivenCheckZero_five drivenCheck_five

theorem drivenCheckZero_six : drivenCheckZero 6 (machineBound 6 0 + 1) = true := by native_decide

theorem drivenCheck_six : ∀ d ≤ 16, 1 ≤ d → drivenCheck 6 d (machineBound 6 d + 1) = true := by
  native_decide

/-- **Period 6, non-white drives, `d ≤ 16`** (`CERT`). -/
theorem drivenRunBound_six : DrivenRunBoundUpTo 6 (machineBound 6) 16 :=
  drivenRunBoundUpTo_of_checks (by norm_num) drivenCheckZero_six drivenCheck_six

/-- **The machine bounds are exact for the machine** (`CERT`): one less horizon is not enough. -/
theorem machineBound_sharp :
    (∀ d ≤ 16, 1 ≤ d → drivenCheck 3 d (machineBound 3 d) = false) ∧
    (∀ d ≤ 14, 1 ≤ d → drivenCheck 4 d (machineBound 4 d) = false) ∧
    (∀ d ≤ 12, 1 ≤ d → drivenCheck 5 d (machineBound 5 d) = false) ∧
    (∀ d ≤ 12, 1 ≤ d → drivenCheck 6 d (machineBound 6 d) = false) := by
  native_decide

/-! ### Full run bounds (white drives by the period-1 bound) -/

/-- **A driven run bound plus the constant-run bound gives a full run bound.** -/
theorem runBound_upTo_of_driven {p D : ℕ} {B : ℕ → ℕ} (hp : 0 < p)
    (h : DrivenRunBoundUpTo p B D) : RunBoundUpTo p (fun d => max (3 * d + 5) (B d)) D := by
  intro x ℓ hw hb d L hd hrun
  rcases Nat.eq_zero_or_pos (bitsOf (fun s => evolve x s (ℓ + d)) p) with h0 | hk
  · refine le_trans (runBound_one x ℓ hw hb d L fun t ht => ?_) (le_max_left _ _)
    rw [col_white_of_driveN_zero x _ p L hp hrun h0 (t + 1) ht,
      col_white_of_driveN_zero x _ p L hp hrun h0 t (by omega)]
  · exact le_trans (h x ℓ hw hb d L hd hrun hk) (le_max_right _ _)

theorem runBound_three_upTo_20 :
    RunBoundUpTo 3 (fun d => max (3 * d + 5) (machineBound 3 d)) 20 :=
  runBound_upTo_of_driven (by norm_num) drivenRunBound_three

theorem runBound_four_upTo_18 :
    RunBoundUpTo 4 (fun d => max (3 * d + 5) (machineBound 4 d)) 18 :=
  runBound_upTo_of_driven (by norm_num) drivenRunBound_four

theorem runBound_five_upTo_16 :
    RunBoundUpTo 5 (fun d => max (3 * d + 5) (machineBound 5 d)) 16 :=
  runBound_upTo_of_driven (by norm_num) drivenRunBound_five

theorem runBound_six_upTo_16 :
    RunBoundUpTo 6 (fun d => max (3 * d + 5) (machineBound 6 d)) 16 :=
  runBound_upTo_of_driven (by norm_num) drivenRunBound_six

/-- All certified machine bounds are at most `(p + 1) d + 14` (an observed envelope; `EMP` beyond
the certified range). -/
theorem machineBound_envelope :
    (∀ d ≤ 20, machineBound 3 d ≤ 4 * d + 14) ∧ (∀ d ≤ 18, machineBound 4 d ≤ 5 * d + 14) ∧
    (∀ d ≤ 16, machineBound 5 d ≤ 6 * d + 14) ∧ (∀ d ≤ 16, machineBound 6 d ≤ 7 * d + 14) := by
  decide

/-! ## The Round 21 frontier, checked -/

/-- **Round 21 frontier.** The one-sided (half-line) targets and what they give:
* `HalfLineDies 1` is proved;
* `HalfLineDies p` for every `p ≥ 1` implies Problem 1;
* `HalfLineDies p` implies the lifted statement `LeftWhiteAperiodic p`;
* the period-2 one-sided targets (`PeriodTwoHalfLineDies`, and the linear form
  `PeriodTwoHalfLineLinear` with horizon `2d + 8`) imply `LeftWhiteAperiodic 2`;
* the linear form is certified for `d ≤ 24`. -/
theorem frontier_halfLine :
    HalfLineDies 1 ∧
    ((∀ p, 0 < p → HalfLineDies p) → Problem1) ∧
    (∀ p, 0 < p → HalfLineDies p → LeftWhiteAperiodic p) ∧
    (PeriodTwoHalfLineDies → LeftWhiteAperiodic 2) ∧
    (PeriodTwoHalfLineLinear → LeftWhiteAperiodic 2) ∧
    (∀ d S : ℕ, d ≤ 24 → 2 ^ (d - 1) ≤ S → S < 2 ^ d → 1 ≤ d →
      ∀ φ : ℕ, φ = 0 ∨ φ = 1 → halfDiesBy S φ (2 * d + 9) = true) :=
  ⟨halfLineDies_one, problem1_of_halfLineDies, fun _ hp h => leftWhiteAperiodic_of_halfLineDies hp h,
    leftWhiteAperiodic_two_of_halfLineDies, leftWhiteAperiodic_two_of_halfLineLinear,
    halfLineLinear_upTo_24⟩

end GLM.Rule30
