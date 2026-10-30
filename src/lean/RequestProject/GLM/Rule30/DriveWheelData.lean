import RequestProject.GLM.Rule30.DriveWheel
import RequestProject.GLM.Rule30.DiagonalSearchData

/-!
# Round 36: the full drive wheel up to period 8, in one certificate

(Not a `module`: it uses the `native_decide` checks of `DiagCert.lean`.)

`DriveWheel.lean` proves that the periodic drives form a wheel: only the primitive
representatives (`WheelRep`) matter.  This file makes the wheel concrete and certifies it in one
pass, instead of one period at a time.

* **CERT** `wheelReps_count`: the number of representatives of period `p = 0, 1, …, 12` is
  `0, 1, 1, 2, 3, 6, 9, 18, 30, 56, 99, 186, 335` (the Lyndon-word counts, minus the white word).
  Up to period 8 that is **70 spokes** in place of `2 + 4 + ⋯ + 256 − 8 = 502` drive words.
* **CERT** `wheelTable_sound`: one table `wheelTable` gives, for each of the 70 representatives
  of period `p ≤ 8`, a slack `c` such that every code of length `d ≤ 24` fails within `d + c`
  tests (`TestSlackUpTo`); `wheelTable_complete` says the table covers every representative.
  The largest entries are `11` (period 8, word `91`), `9` (period 8, word `11`) and `8`
  (period 3, word `1`; period 7, words `13` and `27`; period 8, word `47`).
* **CERT** `testCountLinearUpTo_wheel`: through the wheel (`testSlackUpTo_of_wheel`), every
  period `1 ≤ p ≤ 8` gets the per-period law on code lengths `d ≤ 25 − p`, with slack
  `wheelSlack p + 2 (p − 1)`.
* **CERT** `runBound_wheel_seven`, `runBound_wheel_eight`: back in Rule 30, in **every** left-white
  row, a non-white column of period `7` (resp. `8`) at distance `d ≤ 18` (resp. `d ≤ 17`) from the
  left edge keeps its pattern for at most `7 (d + 20)` (resp. `8 (d + 25)`) steps.  Periods 7 and 8
  had no run bound before this round.

None of this is a statement for all `d`.
-/

namespace GLM.Rule30.DriveWheelData

open GLM.Rule30 GLM.Rule30.DiagCert GLM.Rule30.TestCountData

/-- The wheel representatives of period `p`, as a list. -/
def wheelReps (p : ℕ) : List ℕ := (List.range (2 ^ p)).filter fun k => decide (WheelRep p k)

theorem mem_wheelReps {p k : ℕ} : k ∈ wheelReps p ↔ WheelRep p k := by
  unfold wheelReps
  simp only [List.mem_filter, List.mem_range, decide_eq_true_eq]
  exact ⟨fun h => h.2, fun h => ⟨h.2.1, h⟩⟩

/-- **How many spokes each wheel has** (periods `0 … 12`). -/
theorem wheelReps_count :
    (List.range 13).map (fun p => (wheelReps p).length) =
      [0, 1, 1, 2, 3, 6, 9, 18, 30, 56, 99, 186, 335] := by
  native_decide

/-- The representatives up to period 6, listed (time `0` is bit `0`). -/
theorem wheelReps_small :
    wheelReps 1 = [1] ∧ wheelReps 2 = [1] ∧ wheelReps 3 = [1, 3] ∧ wheelReps 4 = [1, 3, 7] ∧
    wheelReps 5 = [1, 3, 5, 7, 11, 15] ∧ wheelReps 6 = [1, 3, 5, 7, 11, 13, 15, 23, 31] := by
  native_decide

/-! ## The wheel table -/

/-- **The wheel table**: `(p, k, c)` = period, representative, slack on code lengths `d ≤ 24`.
Each `c` is the least slack found for that representative on `d ≤ 24`. -/
def wheelTable : List (ℕ × ℕ × ℕ) :=
  [(1, 1, 2), (2, 1, 5), (3, 1, 8), (3, 3, 3), (4, 1, 3), (4, 3, 2), (4, 7, 5),
   (5, 1, 4), (5, 3, 3), (5, 5, 1), (5, 7, 4), (5, 11, 4), (5, 15, 4),
   (6, 1, 2), (6, 3, 4), (6, 5, 3), (6, 7, 3), (6, 11, 3), (6, 13, 5), (6, 15, 5), (6, 23, 7),
   (6, 31, 4),
   (7, 1, 1), (7, 3, 4), (7, 5, 4), (7, 7, 5), (7, 9, 3), (7, 11, 5), (7, 13, 8), (7, 15, 7),
   (7, 19, 4), (7, 21, 4), (7, 23, 4), (7, 27, 8), (7, 29, 4), (7, 31, 3), (7, 43, 5), (7, 47, 5),
   (7, 55, 6), (7, 63, 6),
   (8, 1, 2), (8, 3, 3), (8, 5, 3), (8, 7, 2), (8, 9, 4), (8, 11, 9), (8, 13, 4), (8, 15, 7),
   (8, 19, 3), (8, 21, 4), (8, 23, 2), (8, 25, 2), (8, 27, 7), (8, 29, 6), (8, 31, 2), (8, 37, 3),
   (8, 39, 4), (8, 43, 6), (8, 45, 4), (8, 47, 8), (8, 53, 3), (8, 55, 4), (8, 59, 3), (8, 61, 3),
   (8, 63, 5), (8, 87, 5), (8, 91, 11), (8, 95, 3), (8, 111, 3), (8, 127, 3)]

/-- The table's code-length range. -/
def wheelRange : ℕ := 24

/-- **The one certificate**: every table entry passes the diagonal-search slack check on
`1 ≤ d ≤ 24`. -/
theorem wheelTable_check :
    wheelTable.all (fun e => tcIntervalCheckD e.1 e.2.1 e.2.2 1 wheelRange) = true := by
  native_decide

/-- The table covers every representative of every period `1 ≤ p ≤ 8`. -/
theorem wheelTable_complete_check :
    (List.range 8).all (fun i => (wheelReps (i + 1)).all fun k =>
      wheelTable.any fun e => e.1 == i + 1 && e.2.1 == k) = true := by
  native_decide

theorem wheelTable_complete {p k : ℕ} (hp : 0 < p) (hp8 : p ≤ 8) (hk : WheelRep p k) :
    ∃ c, (p, k, c) ∈ wheelTable := by
  have h := List.all_eq_true.1 wheelTable_complete_check (p - 1) (List.mem_range.2 (by omega))
  rw [show p - 1 + 1 = p by omega] at h
  have h2 := List.all_eq_true.1 h k (mem_wheelReps.2 hk)
  obtain ⟨⟨q, j, c⟩, he, hb⟩ := List.any_eq_true.1 h2
  simp only [Bool.and_eq_true, beq_iff_eq] at hb
  obtain ⟨rfl, rfl⟩ := hb
  exact ⟨c, he⟩

/-- **Soundness of the table.** -/
theorem wheelTable_sound {p k c : ℕ} (he : (p, k, c) ∈ wheelTable) :
    TestSlackUpTo (driveN p k) c wheelRange := by
  intro d S hd hdD h1 h2
  have hw := List.all_eq_true.1 wheelTable_check _ he
  have hd' := List.all_eq_true.1 hw (d - 1) (List.mem_range.2 (by omega))
  rw [show 1 + (d - 1) = d by omega] at hd'
  exact failsWithinTests_of_tcWordCheckD hd hd' h1 h2

/-! ## Every period up to 8 through the wheel -/

/-- The largest table slack among the representatives of the divisors of `p`. -/
def wheelSlack : ℕ → ℕ
  | 1 => 2 | 2 => 5 | 3 => 8 | 4 => 5 | 5 => 4 | 6 => 8 | 7 => 8 | 8 => 11 | _ => 0

theorem wheelSlack_check :
    (List.range 8).all (fun i => wheelTable.all fun e =>
      !(e.1 ∣ i + 1) || decide (e.2.2 ≤ wheelSlack (i + 1))) = true := by
  native_decide

theorem le_wheelSlack {p q j c : ℕ} (hp : 0 < p) (hp8 : p ≤ 8) (he : (q, j, c) ∈ wheelTable)
    (hqp : q ∣ p) : c ≤ wheelSlack p := by
  have h := List.all_eq_true.1 wheelSlack_check (p - 1) (List.mem_range.2 (by omega))
  rw [show p - 1 + 1 = p by omega] at h
  have h2 := List.all_eq_true.1 h _ he
  simp only [Bool.or_eq_true, Bool.not_eq_true', decide_eq_false_iff_not, decide_eq_true_eq] at h2
  rcases h2 with h2 | h2
  · exact absurd hqp h2
  · exact h2

/-- **The per-period law for every period `1 ≤ p ≤ 8`, from the one wheel table.** -/
theorem testCountLinearUpTo_wheel {p : ℕ} (hp : 0 < p) (hp8 : p ≤ 8) :
    TestCountLinearUpTo p (wheelSlack p + 2 * (p - 1)) (25 - p) := by
  intro k hk0 hk d S hd hdD h1 h2
  refine testSlackUpTo_of_wheel (D := 25 - p) hp (fun q hq hqp j hj => ?_) k hk0 hk d S hd hdD
    h1 h2
  have hqp' := Nat.le_of_dvd hp hqp
  obtain ⟨c, he⟩ := wheelTable_complete hq (by omega) hj
  exact testSlackUpTo_mono (le_wheelSlack hp hp8 he hqp) (by unfold wheelRange; omega)
    (wheelTable_sound he)

/-! ## Back to Rule 30: run bounds for periods 7 and 8 in every left-white row

(For periods 5 and 6 the same route gives weaker bounds than Round 22's
`drivenRunBound_linear_five`, `drivenRunBound_linear_six`, so they are not restated.) -/

theorem runBound_wheel_seven : DrivenRunBoundUpTo 7 (fun d => 7 * (d + 20)) 18 :=
  drivenRunBoundUpTo_of_testCountLinearUpTo (by norm_num)
    (testCountLinearUpTo_wheel (p := 7) (by norm_num) (by norm_num)) (by native_decide)

theorem runBound_wheel_eight : DrivenRunBoundUpTo 8 (fun d => 8 * (d + 25)) 17 :=
  drivenRunBoundUpTo_of_testCountLinearUpTo (by norm_num)
    (testCountLinearUpTo_wheel (p := 8) (by norm_num) (by norm_num)) (by native_decide)

/-- **Round 36 frontier: the full wheel to period 8.**  70 representatives replace 502 drive
words; one table certifies all of them on `d ≤ 24`; through the wheel this gives the per-period
law for every period `≤ 8` and run bounds for periods 7 and 8 in every left-white row. -/
theorem frontier_round36 :
    (List.range 9).map (fun p => (wheelReps p).length) = [0, 1, 1, 2, 3, 6, 9, 18, 30] ∧
    (∀ p, 0 < p → p ≤ 8 → TestCountLinearUpTo p (wheelSlack p + 2 * (p - 1)) (25 - p)) ∧
    DrivenRunBoundUpTo 7 (fun d => 7 * (d + 20)) 18 ∧
    DrivenRunBoundUpTo 8 (fun d => 8 * (d + 25)) 17 :=
  ⟨by native_decide, fun _ hp hp8 => testCountLinearUpTo_wheel hp hp8, runBound_wheel_seven,
    runBound_wheel_eight⟩

end GLM.Rule30.DriveWheelData
