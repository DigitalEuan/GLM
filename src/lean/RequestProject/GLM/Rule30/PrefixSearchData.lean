import RequestProject.GLM.Rule30.PrefixSearch
import RequestProject.GLM.Rule30.HalfLineMachineData

/-!
# Round 22: certificates from the prefix search

The prefix search (`PrefixSearch.lean`) visits about `2^(d - blacks)` prefixes instead of `2^d`
codes, so the same finite checks reach further.  All statements here are `CERT` (they use
`native_decide`).

* **`halfLineLinear_upTo_36`** — the period-2 linear target `PeriodTwoHalfLineLinear` (every code
  fails by time `2d + 8`, both phases) holds for every `d ≤ 36`.  Round 21 reached `d ≤ 24`.
* `drivenRunBound_two_linear` — in every left-white row, a column at distance `d ≤ 36` that is
  2-periodic on `[0, L]` with a black cell in its period has `L ≤ 2d + 8`;
  `runBound_two_upTo_36` adds the constant runs (`3d + 5`).
* `halfLineLinear_three_upTo_26`, `…_four_upTo_23`, `…_five_upTo_21`, `…_six_upTo_19` — the
  linear target `HalfLineLinear p (p + 1) 15` (failure by time `(p + 1) d + 14`) on these ranges;
  Round 21 had the machine bounds up to `20 / 18 / 16 / 16`.
* `drivenRunBound_linear_three` … `_six` and `runBound_three_upTo_26` … — the corresponding run
  bounds for real columns.

The horizons are the linear envelopes, not the exact machine values (the exact values, computed by
`scripts/prefix_search.c`, are `EMP` beyond the Round 21 tables).
-/

namespace GLM.Rule30

/-! ## Period 2 -/

theorem prefixCheck_two_a : ∀ d ≤ 28, 1 ≤ d → prefixCheck 2 d (2 * d + 9) = true := by
  native_decide

theorem prefixCheck_two_b : ∀ d ≤ 32, 29 ≤ d → prefixCheck 2 d (2 * d + 9) = true := by
  native_decide

theorem prefixCheck_two_33 : prefixCheck 2 33 (2 * 33 + 9) = true := by native_decide

theorem prefixCheck_two_34 : prefixCheck 2 34 (2 * 34 + 9) = true := by native_decide

theorem prefixCheck_two_35 : prefixCheck 2 35 (2 * 35 + 9) = true := by native_decide

theorem prefixCheck_two_36 : prefixCheck 2 36 (2 * 36 + 9) = true := by native_decide

theorem prefixCheck_two : ∀ d ≤ 36, 1 ≤ d → prefixCheck 2 d (2 * d + 9) = true := by
  intro d hd h1
  rcases Nat.lt_or_ge d 29 with h | h
  · exact prefixCheck_two_a d (by omega) h1
  rcases Nat.lt_or_ge d 33 with h' | h'
  · exact prefixCheck_two_b d (by omega) h
  interval_cases d
  · exact prefixCheck_two_33
  · exact prefixCheck_two_34
  · exact prefixCheck_two_35
  · exact prefixCheck_two_36

/-- **The period-2 linear target holds for every `d ≤ 36`** (`CERT`): every half-line code of
length `d ≤ 36` fails the check by time `2d + 8`, in both phases. -/
theorem halfLineLinear_upTo_36 : ∀ d S : ℕ, d ≤ 36 → 2 ^ (d - 1) ≤ S → S < 2 ^ d → 1 ≤ d →
    ∀ φ : ℕ, φ = 0 ∨ φ = 1 → halfDiesBy S φ (2 * d + 9) = true :=
  halfLineLinear_of_prefixCheck prefixCheck_two

/-- Driven period-2 runs (alternating or constant black), `d ≤ 36`: `L ≤ 2d + 8` (`CERT`). -/
theorem drivenRunBound_two_linear : DrivenRunBoundUpTo 2 (fun d => 2 * d + 8) 36 :=
  drivenRunBoundUpTo_of_checks (by norm_num) (by native_decide)
    fun d hd h1 => drivenCheck_of_prefixCheck h1 (prefixCheck_two d hd h1)

/-- **All period-2 runs, `d ≤ 36`** (`CERT`). -/
theorem runBound_two_upTo_36 :
    RunBoundUpTo 2 (fun d => max (3 * d + 5) (2 * d + 8)) 36 :=
  runBound_upTo_of_driven (by norm_num) drivenRunBound_two_linear

/-! ## Periods 3–6 -/

theorem prefixCheck_three_a : ∀ d ≤ 22, 1 ≤ d → prefixCheck 3 d (4 * d + 15) = true := by
  native_decide

theorem prefixCheck_three_b : ∀ d ≤ 24, 23 ≤ d → prefixCheck 3 d (4 * d + 15) = true := by
  native_decide

theorem prefixCheck_three_25 : prefixCheck 3 25 (4 * 25 + 15) = true := by native_decide

theorem prefixCheck_three_26 : prefixCheck 3 26 (4 * 26 + 15) = true := by native_decide

theorem prefixCheck_three : ∀ d ≤ 26, 1 ≤ d → prefixCheck 3 d (4 * d + 15) = true := by
  intro d hd h1
  rcases Nat.lt_or_ge d 23 with h | h
  · exact prefixCheck_three_a d (by omega) h1
  rcases Nat.lt_or_ge d 25 with h' | h'
  · exact prefixCheck_three_b d (by omega) h
  interval_cases d
  · exact prefixCheck_three_25
  · exact prefixCheck_three_26

theorem prefixCheck_four_a : ∀ d ≤ 21, 1 ≤ d → prefixCheck 4 d (5 * d + 15) = true := by
  native_decide

theorem prefixCheck_four_22 : prefixCheck 4 22 (5 * 22 + 15) = true := by native_decide

theorem prefixCheck_four_23 : prefixCheck 4 23 (5 * 23 + 15) = true := by native_decide

theorem prefixCheck_four : ∀ d ≤ 23, 1 ≤ d → prefixCheck 4 d (5 * d + 15) = true := by
  intro d hd h1
  rcases Nat.lt_or_ge d 22 with h | h
  · exact prefixCheck_four_a d (by omega) h1
  interval_cases d
  · exact prefixCheck_four_22
  · exact prefixCheck_four_23

theorem prefixCheck_five_a : ∀ d ≤ 19, 1 ≤ d → prefixCheck 5 d (6 * d + 15) = true := by
  native_decide

theorem prefixCheck_five_20 : prefixCheck 5 20 (6 * 20 + 15) = true := by native_decide

theorem prefixCheck_five_21 : prefixCheck 5 21 (6 * 21 + 15) = true := by native_decide

theorem prefixCheck_five : ∀ d ≤ 21, 1 ≤ d → prefixCheck 5 d (6 * d + 15) = true := by
  intro d hd h1
  rcases Nat.lt_or_ge d 20 with h | h
  · exact prefixCheck_five_a d (by omega) h1
  interval_cases d
  · exact prefixCheck_five_20
  · exact prefixCheck_five_21

theorem prefixCheck_six_a : ∀ d ≤ 17, 1 ≤ d → prefixCheck 6 d (7 * d + 15) = true := by
  native_decide

theorem prefixCheck_six_18 : prefixCheck 6 18 (7 * 18 + 15) = true := by native_decide

theorem prefixCheck_six_19 : prefixCheck 6 19 (7 * 19 + 15) = true := by native_decide

theorem prefixCheck_six : ∀ d ≤ 19, 1 ≤ d → prefixCheck 6 d (7 * d + 15) = true := by
  intro d hd h1
  rcases Nat.lt_or_ge d 18 with h | h
  · exact prefixCheck_six_a d (by omega) h1
  interval_cases d
  · exact prefixCheck_six_18
  · exact prefixCheck_six_19

/-- `HalfLineLinear 3 4 15` on `d ≤ 26` (`CERT`): failure by time `4d + 14`. -/
theorem halfLineLinear_three_upTo_26 :
    ∀ k, 0 < k → k < 2 ^ 3 → ∀ d S : ℕ, d ≤ 26 → 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
      dDiesBy (driveN 3 k) S (4 * d + 15) = true :=
  halfLineLinear_upTo_of_prefixCheck prefixCheck_three

/-- `HalfLineLinear 4 5 15` on `d ≤ 23` (`CERT`): failure by time `5d + 14`. -/
theorem halfLineLinear_four_upTo_23 :
    ∀ k, 0 < k → k < 2 ^ 4 → ∀ d S : ℕ, d ≤ 23 → 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
      dDiesBy (driveN 4 k) S (5 * d + 15) = true :=
  halfLineLinear_upTo_of_prefixCheck prefixCheck_four

/-- `HalfLineLinear 5 6 15` on `d ≤ 21` (`CERT`): failure by time `6d + 14`. -/
theorem halfLineLinear_five_upTo_21 :
    ∀ k, 0 < k → k < 2 ^ 5 → ∀ d S : ℕ, d ≤ 21 → 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
      dDiesBy (driveN 5 k) S (6 * d + 15) = true :=
  halfLineLinear_upTo_of_prefixCheck prefixCheck_five

/-- `HalfLineLinear 6 7 15` on `d ≤ 19` (`CERT`): failure by time `7d + 14`. -/
theorem halfLineLinear_six_upTo_19 :
    ∀ k, 0 < k → k < 2 ^ 6 → ∀ d S : ℕ, d ≤ 19 → 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
      dDiesBy (driveN 6 k) S (7 * d + 15) = true :=
  halfLineLinear_upTo_of_prefixCheck prefixCheck_six

theorem drivenRunBound_linear_three : DrivenRunBoundUpTo 3 (fun d => 4 * d + 14) 26 :=
  drivenRunBoundUpTo_of_checks (by norm_num) (by native_decide)
    fun d hd h1 => drivenCheck_of_prefixCheck h1 (prefixCheck_three d hd h1)

theorem drivenRunBound_linear_four : DrivenRunBoundUpTo 4 (fun d => 5 * d + 14) 23 :=
  drivenRunBoundUpTo_of_checks (by norm_num) (by native_decide)
    fun d hd h1 => drivenCheck_of_prefixCheck h1 (prefixCheck_four d hd h1)

theorem drivenRunBound_linear_five : DrivenRunBoundUpTo 5 (fun d => 6 * d + 14) 21 :=
  drivenRunBoundUpTo_of_checks (by norm_num) (by native_decide)
    fun d hd h1 => drivenCheck_of_prefixCheck h1 (prefixCheck_five d hd h1)

theorem drivenRunBound_linear_six : DrivenRunBoundUpTo 6 (fun d => 7 * d + 14) 19 :=
  drivenRunBoundUpTo_of_checks (by norm_num) (by native_decide)
    fun d hd h1 => drivenCheck_of_prefixCheck h1 (prefixCheck_six d hd h1)

/-- **Run bounds for periods 3–6 on the extended ranges** (`CERT`). -/
theorem runBound_three_to_six_linear :
    RunBoundUpTo 3 (fun d => max (3 * d + 5) (4 * d + 14)) 26 ∧
    RunBoundUpTo 4 (fun d => max (3 * d + 5) (5 * d + 14)) 23 ∧
    RunBoundUpTo 5 (fun d => max (3 * d + 5) (6 * d + 14)) 21 ∧
    RunBoundUpTo 6 (fun d => max (3 * d + 5) (7 * d + 14)) 19 :=
  ⟨runBound_upTo_of_driven (by norm_num) drivenRunBound_linear_three,
    runBound_upTo_of_driven (by norm_num) drivenRunBound_linear_four,
    runBound_upTo_of_driven (by norm_num) drivenRunBound_linear_five,
    runBound_upTo_of_driven (by norm_num) drivenRunBound_linear_six⟩

/-! ## The Round 22 frontier, checked -/

/-- **Round 22 frontier.**
* every drive sequence: exactly `2^(k - blacks k)` codes of length `k` survive the checks before
  time `k` (`survivors_card`, `FORMAL`);
* the linear one-sided target of any period implies `HalfLineDies` of that period;
* the period-2 linear target implies `LeftWhiteAperiodic 2` and holds for `d ≤ 36` (`CERT`). -/
theorem frontier_prefixSearch :
    (∀ (bd : ℕ → Bool) (k : ℕ), (survivors bd k).card = 2 ^ (k - blacks bd k)) ∧
    (∀ p a b, HalfLineLinear p a b → HalfLineDies p) ∧
    (PeriodTwoHalfLineLinear → LeftWhiteAperiodic 2) ∧
    (∀ d S : ℕ, d ≤ 36 → 2 ^ (d - 1) ≤ S → S < 2 ^ d → 1 ≤ d →
      ∀ φ : ℕ, φ = 0 ∨ φ = 1 → halfDiesBy S φ (2 * d + 9) = true) :=
  ⟨survivors_card, fun _ _ _ => halfLineDies_of_linear,
    leftWhiteAperiodic_two_of_halfLineLinear, halfLineLinear_upTo_36⟩

end GLM.Rule30
