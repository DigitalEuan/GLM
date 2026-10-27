import RequestProject.GLM.Rule30.ConjectureLoop
import RequestProject.GLM.Rule30.EchoBound
import RequestProject.GLM.Rule30.AmortizedHalving
import RequestProject.GLM.Rule30.XorAlternativesData
import RequestProject.GLM.Rule30.Compute

/-!
# Round 26 certificates: what the conjecture loop pruned and what survived

(Not a `module`: the checks use `native_decide`.)  The loop itself is run by
`scripts/conjecture_loop.py` (EMP); this file turns its verdicts into Lean theorems.  A
**refutation** is a theorem `¬ Candidate` proved from one finite instance: it is final.  A
**survival** is a theorem about the stated finite range only (`CERT`); no finite range proves a
candidate (`no_finite_confirmation`).

## 1. The echo family `EchoLogBound a b` (longest echo `≤ a·log₂ n + b`), to `n = 131072`

The loop narrows each slope to its sharp frontier at level `131072`:

| slope `a` | frontier `b` (certified to `n ≤ 131072`) | refuted just below (witness) |
|---|---|---|
| 0 | 33 (`echoLogBound_0_33_upto`) | `¬ EchoLogBound 0 32` (`n = 83154`, echo 33, period 37595) |
| 1 | 17 (`echoLogBound_1_17_upto`) | `¬ EchoLogBound 1 16` (same echo) |
| 2 | 2 (`tuneExcessLog_upto_131072`) | `¬ EchoLogBound 2 1` (`n = 1995`, echo 22, period 1767) |
| 3 | 0 (`echoLogBound_3_0_upto`) | — |

So Round 25's `TuneExcessLog = EchoLogBound 2 2` is now certified to `n ≤ 131072` (was 2000),
and it is **sharp**: the offset 2 cannot be lowered.  Every member implies Problem 1.

## 2. The half-line machine

* **Analogy refuted** (period 1 → period `p`): the period-1 bound "dies by `d + 2`"
  (`constDrive_dies`) does not transport: `¬ HalfLineLinear 2 1 2`, `¬ HalfLineLinear 3 1 2`.
* **Window halving refuted** (To Do 1/10): for the drive `1, 0, 1, 0, …` and `d = 11`, two codes
  stay alive from time 17 to time 29, so `¬ WindowHalving 2 m num den` for every window
  `m ≤ 12` and every fraction `num/den < 1` (`not_windowHalving_two`).
* **Amortised halving survives**: `AmortizedHalvingUpTo 2 4 1 12` and
  `AmortizedHalvingUpTo 3 4 1 12` (all words, `d ≤ 12`, all times), and the slack `e = 1` is sharp:
  `¬ AmortizedHalving 2 4 0`, `¬ AmortizedHalving 3 4 0`.

## 3. Analogy Rule 86 → Rule 30 refuted

`analogy_rule86_rule30`: the counting law holds for Rule 86 at every time
(`runCountW_eightySix`) but its transport to Rule 30 fails at `T = d = 3`.

`frontier_round26` collects the round.
-/

namespace GLM.Rule30

open Conjecture

/-! ## The centre column, 131072 notes -/

/-- The first 131072 centre bits as an array. -/
def centreArr131072 : Array Bool := (fastList 131072).toArray

/-- Fast access to the centre column. -/
def centre131072 (i : ℕ) : Bool := centreArr131072.getD i false

theorem centre131072_eq {i : ℕ} (hi : i < 131072) : centre131072 i = centerCol i := by
  simp only [centre131072, centreArr131072, fastList_eq, Array.getD_eq_getD_getElem?,
    List.getElem?_toArray, List.getElem?_map, List.getElem?_range hi, Option.map_some,
    Option.getD_some]

/-! ## 1. The echo family -/

theorem echoLogCheck_2_2 : echoLogCheck centre131072 2 2 131072 = true := by native_decide
theorem echoLogCheck_0_33 : echoLogCheck centre131072 0 33 131072 = true := by native_decide
theorem echoLogCheck_1_17 : echoLogCheck centre131072 1 17 131072 = true := by native_decide
theorem echoLogCheck_3_0 : echoLogCheck centre131072 3 0 131072 = true := by native_decide

/-- **`TuneExcessLog` holds for every `n ≤ 131072`** (Round 25 certified `n ≤ 2000`). -/
theorem tuneExcessLog_upto_131072 :
    ∀ n ≤ 131072, n ≤ tuneCost centerCol n + (2 * Nat.log 2 n + 2) :=
  echoLogBound_upto_of_check (fun _ hi => centre131072_eq hi) echoLogCheck_2_2

/-- The constant form: the longest echo up to `131072` is at most 33. -/
theorem echoLogBound_0_33_upto : ∀ n ≤ 131072, n ≤ tuneCost centerCol n + (0 * Nat.log 2 n + 33) :=
  echoLogBound_upto_of_check (fun _ hi => centre131072_eq hi) echoLogCheck_0_33

theorem echoLogBound_1_17_upto :
    ∀ n ≤ 131072, n ≤ tuneCost centerCol n + (1 * Nat.log 2 n + 17) :=
  echoLogBound_upto_of_check (fun _ hi => centre131072_eq hi) echoLogCheck_1_17

theorem echoLogBound_3_0_upto : ∀ n ≤ 131072, n ≤ tuneCost centerCol n + (3 * Nat.log 2 n + 0) :=
  echoLogBound_upto_of_check (fun _ hi => centre131072_eq hi) echoLogCheck_3_0

theorem echoB_83154 : echoB centre131072 83154 33 37595 = true := by native_decide
theorem echoB_1995 : echoB centre131072 1995 22 1767 = true := by native_decide

/-- The longest echo at `n = 83154` has length (at least) 33. -/
theorem echo_83154 : Echo centerCol 83154 33 :=
  (echo_congr fun i hi => centre131072_eq (by omega)).1 (echo_of_echoB echoB_83154)

/-- At `n = 1995` there is an echo of length 22 (Round 25's equality case of `TuneExcessLog`). -/
theorem echo_1995 : Echo centerCol 1995 22 :=
  (echo_congr fun i hi => centre131072_eq (by omega)).1 (echo_of_echoB echoB_1995)

theorem log_83154 : Nat.log 2 83154 = 16 := by native_decide
theorem log_1995 : Nat.log 2 1995 = 10 := by native_decide

/-- **Refuted**: no constant bound below 33. -/
theorem not_echoLogBound_0_32 : ¬ EchoLogBound 0 32 :=
  not_echoLogBound_of_echo (n := 83154) (by rw [log_83154]; exact echo_83154)

/-- **Refuted**: slope 1 needs offset at least 17. -/
theorem not_echoLogBound_1_16 : ¬ EchoLogBound 1 16 :=
  not_echoLogBound_of_echo (n := 83154) (by rw [log_83154]; exact echo_83154)

/-- **Refuted**: slope 2 needs offset at least 2, so `TuneExcessLog` is sharp. -/
theorem not_echoLogBound_2_1 : ¬ EchoLogBound 2 1 :=
  not_echoLogBound_of_echo (n := 1995) (by rw [log_1995]; exact echo_1995)

/-! ## 2. The half-line machine -/

theorem dDiesBy_two_two_one : dDiesBy (driveN 2 2) 1 3 = false := by native_decide
theorem dDiesBy_three_one_one : dDiesBy (driveN 3 1) 1 3 = false := by native_decide

/-- **Analogy refuted**: the period-1 bound `d + 2` fails for period 2 (drive `0, 1, 0, 1, …`,
`d = 1`). -/
theorem not_halfLineLinear_two_one_two : ¬ HalfLineLinear 2 1 2 := fun h => by
  have := h 2 (by norm_num) (by norm_num) 1 1 le_rfl (by norm_num) (by norm_num)
  rw [dDiesBy_two_two_one] at this
  exact Bool.noConfusion this

/-- **Analogy refuted**: the period-1 bound `d + 2` fails for period 3 (drive `1, 0, 0, …`,
`d = 1`). -/
theorem not_halfLineLinear_three_one_two : ¬ HalfLineLinear 3 1 2 := fun h => by
  have := h 1 (by norm_num) (by norm_num) 1 1 le_rfl (by norm_num) (by norm_num)
  rw [dDiesBy_three_one_one] at this
  exact Bool.noConfusion this

theorem alive_two_one_11_17 : (aliveCodes (driveN 2 1) 11 17).card = 2 := by native_decide
theorem alive_two_one_11_29 : (aliveCodes (driveN 2 1) 11 29).card = 2 := by native_decide

/-- **Window halving refuted for every window up to 12 steps**: for the drive `1, 0, 1, 0, …` and
`d = 11`, two codes stay alive from time 17 to time 29. -/
theorem not_windowHalving_two {m num den : ℕ} (hm : m ≤ 12) (hnd : num < den) :
    ¬ WindowHalving 2 m num den := by
  have h1 := Finset.card_le_card
    (aliveCodes_antitone (driveN 2 1) 11 (show 17 + m ≤ 29 by omega))
  have h2 := Finset.card_le_card
    (aliveCodes_antitone (driveN 2 1) 11 (show 17 ≤ 17 + m by omega))
  rw [alive_two_one_11_29] at h1
  rw [alive_two_one_11_17] at h2
  exact not_windowHalving_of_plateau hnd (k := 1) (d := 11) (t := 17) (by norm_num) (by norm_num)
    (by norm_num) (by norm_num) (by rw [alive_two_one_11_17]; norm_num)
    (by rw [alive_two_one_11_17]; omega)

theorem amortCheck_2_4_1 : amortCheck 2 4 1 12 = true := by native_decide
theorem amortCheck_3_4_1 : amortCheck 3 4 1 12 = true := by native_decide

/-- **Amortised halving survives** for period 2, `c = 4`, `e = 1`, every `d ≤ 12`, all times. -/
theorem amortizedHalvingUpTo_2_4_1 : AmortizedHalvingUpTo 2 4 1 12 :=
  amortizedHalvingUpTo_of_check (by norm_num) amortCheck_2_4_1

/-- **Amortised halving survives** for period 3, `c = 4`, `e = 1`, every `d ≤ 12`, all times. -/
theorem amortizedHalvingUpTo_3_4_1 : AmortizedHalvingUpTo 3 4 1 12 :=
  amortizedHalvingUpTo_of_check (by norm_num) amortCheck_3_4_1

theorem alive_two_two_1_4 : (aliveCodes (driveN 2 2) 1 4).card = 1 := by native_decide
theorem alive_three_one_1_4 : (aliveCodes (driveN 3 1) 1 4).card = 1 := by native_decide

/-- **The slack `e = 1` is sharp** for period 2 (`d = 1`, `m = 4`). -/
theorem not_amortizedHalving_2_4_0 : ¬ AmortizedHalving 2 4 0 := fun h => by
  have := h 2 (by norm_num) (by norm_num) 1 4 le_rfl
  rw [show 1 - 1 + 4 = 4 by rfl, alive_two_two_1_4] at this
  norm_num at this

/-- **The slack `e = 1` is sharp** for period 3 (`d = 1`, `m = 4`). -/
theorem not_amortizedHalving_3_4_0 : ¬ AmortizedHalving 3 4 0 := fun h => by
  have := h 1 (by norm_num) (by norm_num) 1 4 le_rfl
  rw [show 1 - 1 + 4 = 4 by rfl, alive_three_one_1_4] at this
  norm_num at this

/-! ## 3. Analogy Rule 86 → Rule 30 -/

/-- **An analogy that fails**: the counting law is exact for Rule 86 at every time, and its
transport to Rule 30 is false at `d = T = 3`. -/
theorem analogy_rule86_rule30 :
    (∀ d T, 1 ≤ T → RunCountW 86 2 d T = 2 ^ (d + 1)) ∧ RunCountW 30 2 3 3 ≠ 2 ^ (3 + 1) :=
  ⟨runCountW_eightySix, by rw [runCountW_thirty_edge]; norm_num⟩

/-! ## The frontier after Round 26 -/

/-- **Round 26 in one theorem.** Proved implications, sharp certified frontiers, and refutations
produced by the conjecture loop. -/
theorem frontier_round26 :
    -- the echo family: every member implies Problem 1, the frontier at slope 2 is sharp
    (∀ a b, EchoLogBound a b → Problem1) ∧
    (∀ n ≤ 131072, n ≤ tuneCost centerCol n + (2 * Nat.log 2 n + 2)) ∧
    ¬ EchoLogBound 2 1 ∧ ¬ EchoLogBound 1 16 ∧ ¬ EchoLogBound 0 32 ∧
    -- the half-line machine: amortised halving implies the rung, window halving is refuted
    (∀ p c e, 0 < c → AmortizedHalving p c e → HalfLineDies p) ∧
    AmortizedHalvingUpTo 2 4 1 12 ∧ AmortizedHalvingUpTo 3 4 1 12 ∧
    ¬ AmortizedHalving 2 4 0 ∧ ¬ AmortizedHalving 3 4 0 ∧
    (∀ m num den, m ≤ 12 → num < den → ¬ WindowHalving 2 m num den) ∧
    -- analogies refuted
    ¬ HalfLineLinear 2 1 2 ∧ ¬ HalfLineLinear 3 1 2 ∧
    -- drive symmetry: periods 2 and 3 need one and two drive words
    (HalfLineDies 2 ↔ WordDies (driveN 2 1)) ∧
    (HalfLineDies 3 ↔ WordDies (driveN 3 1) ∧ WordDies (driveN 3 3)) :=
  ⟨fun _ _ h => problem1_of_echoLogBound h, tuneExcessLog_upto_131072, not_echoLogBound_2_1,
    not_echoLogBound_1_16, not_echoLogBound_0_32, fun _ _ _ hc h => halfLineDies_of_amortized hc h,
    amortizedHalvingUpTo_2_4_1, amortizedHalvingUpTo_3_4_1, not_amortizedHalving_2_4_0,
    not_amortizedHalving_3_4_0, fun _ _ _ hm hnd => not_windowHalving_two hm hnd,
    not_halfLineLinear_two_one_two, not_halfLineLinear_three_one_two, halfLineDies_two_iff,
    halfLineDies_three_iff⟩

end GLM.Rule30
