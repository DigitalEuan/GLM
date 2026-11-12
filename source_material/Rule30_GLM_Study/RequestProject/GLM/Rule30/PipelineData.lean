import RequestProject.GLM.Rule30.Pipeline
import RequestProject.GLM.Rule30.PrefixSearch
import RequestProject.GLM.Rule30.AmortizedHalving

/-!
# Round 30 certificates: the statement planner's frontier, made sharp in Lean

(Not a `module`: the checks use `native_decide`.)  Stage 4 of the Round 30 pipeline
(`rule30_round30/glm_glm_universal/reasoning/statement_planner.py`) is the Round 29
planner run over *statements*: chains of structural steps (`steeper`, `analogy`, and the proved
implication `halfLineLinear_of_amortized`) from the seeds `HalfLineLinear 2 1 _` and
`AmortizedHalving 2 1 _`, each closed by a **fitted** offset (the least offset surviving every
level, `Conjecture.narrow`).  This file is its hard gate: for every statement on the planner's
frontier it proves

* **survival on the range** (`CERT`): the statement holds for every code length `d ≤ D`
  (`linCheck` / `amortCheck`, by `native_decide`); and
* **sharpness** (`FORMAL` once the witness is checked): the statement with offset one smaller is
  *false*, refuted by one explicit code (`not_halfLineLinear_of_witness`,
  `not_amortizedHalving_of_witness`).

So on each range the fitted offset is exactly the least one, which is what the planner's fitted
finisher claims (`Conjecture.narrow_spec`, `narrow_le`).  Survival on a range never proves a
statement (`no_finite_confirmation`); every member implies the period-`p` rung `HalfLineDies p`
(`halfLineDies_of_linear`, `halfLineDies_of_amortized`).

## The frontier (ranges: `HalfLineLinear` to `d ≤ 20 / 18 / 16` for `p = 2 / 3 / 4`;
`AmortizedHalving` to `d ≤ 12`)

| period | `HalfLineLinear p a b`, sharp `(a, b)` | `AmortizedHalving p c e`, sharp `(c, e)` |
|---|---|---|
| 2 | (1, 20) (2, 9) (3, 5) (4, 4) (5, 3) (6, 2) | (1, 11) (2, 3) (3, 2) (4, 1) |
| 3 | (1, 39) (2, 21) (3, 7) (4, 4) (5, 3) (6, 2) | (1, 14) (2, 4) (3, 2) (4, 1) |
| 4 | (1, 59) (2, 44) (3, 29) (4, 14) (5, 9) | (1, 19) (2, 6) (3, 4) (4, 3) (5, 2) |

The offsets of slope 1 and 2 for periods 3 and 4 are not stable in the level data (the Occam
measurement of `statement_planner.py`): they are sharp *on their range* only.
-/

namespace GLM.Rule30.PipelineData

/-! ## General lemmas: range certificates and single-witness refutations -/

/-- `HalfLineLinear p a b` on the code lengths `d ≤ D`. -/
def HalfLineLinearUpTo (p a b D : ℕ) : Prop :=
  ∀ k, 0 < k → k < 2 ^ p → ∀ d S : ℕ, d ≤ D → 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
    dDiesBy (driveN p k) S (a * d + b) = true

/-- The range check: the prefix search succeeds for every `1 ≤ d ≤ D`. -/
def linCheck (p a b D : ℕ) : Bool :=
  (List.range (D + 1)).all fun d => d == 0 || prefixCheck p d (a * d + b)

theorem halfLineLinearUpTo_of_linCheck {p a b D : ℕ} (h : linCheck p a b D = true) :
    HalfLineLinearUpTo p a b D := by
  apply halfLineLinear_upTo_of_prefixCheck
  intro d hd hd1
  have := List.all_eq_true.1 h d (List.mem_range.2 (by omega))
  simpa [show d ≠ 0 by omega] using this

/-- **One surviving code refutes a linear bound.** -/
theorem not_halfLineLinear_of_witness {p a b k d S : ℕ} (hk0 : 0 < k) (hk : k < 2 ^ p)
    (hd : 1 ≤ d) (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d)
    (hw : dDiesBy (driveN p k) S (a * d + b) = false) : ¬ HalfLineLinear p a b := fun h => by
  have := h k hk0 hk d S hd h1 h2
  rw [hw] at this
  exact Bool.noConfusion this

/-- **One over-full population refutes amortised halving.** -/
theorem not_amortizedHalving_of_witness {p c e k d m : ℕ} (hk0 : 0 < k) (hk : k < 2 ^ p)
    (hd : 1 ≤ d)
    (hw : 2 ^ (d - 1 + e) < (aliveCodes (driveN p k) d (d - 1 + m)).card * 2 ^ (m / c)) :
    ¬ AmortizedHalving p c e := fun h => by
  have := h k hk0 hk d m hd
  omega

/-- A **sharp linear frontier point** on the range `d ≤ D`: the bound holds there, and the bound
with offset one smaller is false. -/
def SharpLinear (p a b D : ℕ) : Prop := HalfLineLinearUpTo p a b D ∧ ¬ HalfLineLinear p a (b - 1)

/-- A **sharp amortised frontier point** on the range `d ≤ D`. -/
def SharpAmortized (p c e D : ℕ) : Prop :=
  AmortizedHalvingUpTo p c e D ∧ ¬ AmortizedHalving p c (e - 1)

/-! ## Period 2 -/

theorem linCheck_2_1_20 : linCheck 2 1 20 20 = true := by native_decide
theorem linCheck_2_2_9 : linCheck 2 2 9 20 = true := by native_decide
theorem linCheck_2_3_5 : linCheck 2 3 5 20 = true := by native_decide
theorem linCheck_2_4_4 : linCheck 2 4 4 20 = true := by native_decide
theorem linCheck_2_5_3 : linCheck 2 5 3 20 = true := by native_decide
theorem linCheck_2_6_2 : linCheck 2 6 2 20 = true := by native_decide

-- witnesses: (word, length, code); the code first fails exactly at the refuted horizon
theorem wit_2_11_1493 : dDiesBy (driveN 2 1) 1493 30 = false := by native_decide
theorem wit_2_1_1 : dDiesBy (driveN 2 2) 1 7 = false := by native_decide

theorem sharp_2_1_20 : SharpLinear 2 1 20 20 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_2_1_20,
    not_halfLineLinear_of_witness (k := 1) (d := 11) (S := 1493) (by norm_num) (by norm_num)
      (by norm_num) (by norm_num) (by norm_num) wit_2_11_1493⟩

theorem sharp_2_2_9 : SharpLinear 2 2 9 20 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_2_2_9,
    not_halfLineLinear_of_witness (k := 1) (d := 11) (S := 1493) (by norm_num) (by norm_num)
      (by norm_num) (by norm_num) (by norm_num) wit_2_11_1493⟩

theorem sharp_2_3_5 : SharpLinear 2 3 5 20 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_2_3_5,
    not_halfLineLinear_of_witness (k := 2) (d := 1) (S := 1) (by norm_num) (by norm_num)
      le_rfl (by norm_num) (by norm_num) wit_2_1_1⟩

theorem sharp_2_4_4 : SharpLinear 2 4 4 20 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_2_4_4,
    not_halfLineLinear_of_witness (k := 2) (d := 1) (S := 1) (by norm_num) (by norm_num)
      le_rfl (by norm_num) (by norm_num) wit_2_1_1⟩

theorem sharp_2_5_3 : SharpLinear 2 5 3 20 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_2_5_3,
    not_halfLineLinear_of_witness (k := 2) (d := 1) (S := 1) (by norm_num) (by norm_num)
      le_rfl (by norm_num) (by norm_num) wit_2_1_1⟩

theorem sharp_2_6_2 : SharpLinear 2 6 2 20 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_2_6_2,
    not_halfLineLinear_of_witness (k := 2) (d := 1) (S := 1) (by norm_num) (by norm_num)
      le_rfl (by norm_num) (by norm_num) wit_2_1_1⟩

theorem amortCheck_2_1_11 : amortCheck 2 1 11 12 = true := by native_decide
theorem amortCheck_2_2_3 : amortCheck 2 2 3 12 = true := by native_decide
theorem amortCheck_2_3_2 : amortCheck 2 3 2 12 = true := by native_decide

theorem alive_2_1_11_30 : (aliveCodes (driveN 2 1) 11 30).card = 2 := by native_decide
theorem alive_2_2_1_6 : (aliveCodes (driveN 2 2) 1 6).card = 1 := by native_decide

theorem sharpA_2_1_11 : SharpAmortized 2 1 11 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_2_1_11,
    not_amortizedHalving_of_witness (k := 1) (d := 11) (m := 20) (by norm_num) (by norm_num)
      (by norm_num) (by rw [show 11 - 1 + 20 = 30 by rfl, alive_2_1_11_30]; norm_num)⟩

theorem sharpA_2_2_3 : SharpAmortized 2 2 3 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_2_2_3,
    not_amortizedHalving_of_witness (k := 2) (d := 1) (m := 6) (by norm_num) (by norm_num)
      le_rfl (by rw [show 1 - 1 + 6 = 6 by rfl, alive_2_2_1_6]; norm_num)⟩

theorem sharpA_2_3_2 : SharpAmortized 2 3 2 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_2_3_2,
    not_amortizedHalving_of_witness (k := 2) (d := 1) (m := 6) (by norm_num) (by norm_num)
      le_rfl (by rw [show 1 - 1 + 6 = 6 by rfl, alive_2_2_1_6]; norm_num)⟩

theorem amortCheck_2_4_1' : amortCheck 2 4 1 12 = true := by native_decide
theorem alive_2_2_1_4 : (aliveCodes (driveN 2 2) 1 4).card = 1 := by native_decide

theorem sharpA_2_4_1 : SharpAmortized 2 4 1 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_2_4_1',
    not_amortizedHalving_of_witness (k := 2) (d := 1) (m := 4) (by norm_num) (by norm_num)
      le_rfl (by rw [show 1 - 1 + 4 = 4 by rfl, alive_2_2_1_4]; norm_num)⟩

/-! ## Period 3 -/

theorem linCheck_3_1_39 : linCheck 3 1 39 18 = true := by native_decide
theorem linCheck_3_2_21 : linCheck 3 2 21 18 = true := by native_decide
theorem linCheck_3_3_7 : linCheck 3 3 7 18 = true := by native_decide
theorem linCheck_3_4_4 : linCheck 3 4 4 18 = true := by native_decide
theorem linCheck_3_5_3 : linCheck 3 5 3 18 = true := by native_decide
theorem linCheck_3_6_2 : linCheck 3 6 2 18 = true := by native_decide

theorem wit_3_18_133325 : dDiesBy (driveN 3 4) 133325 56 = false := by native_decide
theorem wit_3_3_5 : dDiesBy (driveN 3 1) 5 15 = false := by native_decide
theorem wit_3_1_1 : dDiesBy (driveN 3 2) 1 7 = false := by native_decide

theorem sharp_3_1_39 : SharpLinear 3 1 39 18 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_3_1_39,
    not_halfLineLinear_of_witness (k := 4) (d := 18) (S := 133325) (by norm_num) (by norm_num)
      (by norm_num) (by norm_num) (by norm_num) wit_3_18_133325⟩

theorem sharp_3_2_21 : SharpLinear 3 2 21 18 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_3_2_21,
    not_halfLineLinear_of_witness (k := 4) (d := 18) (S := 133325) (by norm_num) (by norm_num)
      (by norm_num) (by norm_num) (by norm_num) wit_3_18_133325⟩

theorem sharp_3_3_7 : SharpLinear 3 3 7 18 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_3_3_7,
    not_halfLineLinear_of_witness (k := 1) (d := 3) (S := 5) (by norm_num) (by norm_num)
      (by norm_num) (by norm_num) (by norm_num) wit_3_3_5⟩

theorem sharp_3_4_4 : SharpLinear 3 4 4 18 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_3_4_4,
    not_halfLineLinear_of_witness (k := 2) (d := 1) (S := 1) (by norm_num) (by norm_num)
      le_rfl (by norm_num) (by norm_num) wit_3_1_1⟩

theorem sharp_3_5_3 : SharpLinear 3 5 3 18 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_3_5_3,
    not_halfLineLinear_of_witness (k := 2) (d := 1) (S := 1) (by norm_num) (by norm_num)
      le_rfl (by norm_num) (by norm_num) wit_3_1_1⟩

theorem sharp_3_6_2 : SharpLinear 3 6 2 18 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_3_6_2,
    not_halfLineLinear_of_witness (k := 2) (d := 1) (S := 1) (by norm_num) (by norm_num)
      le_rfl (by norm_num) (by norm_num) wit_3_1_1⟩

theorem amortCheck_3_1_14 : amortCheck 3 1 14 12 = true := by native_decide
theorem amortCheck_3_2_4 : amortCheck 3 2 4 12 = true := by native_decide
theorem amortCheck_3_3_2 : amortCheck 3 3 2 12 = true := by native_decide
theorem amortCheck_3_4_1' : amortCheck 3 4 1 12 = true := by native_decide

theorem alive_3_4_10_29 : (aliveCodes (driveN 3 4) 10 29).card = 6 := by native_decide
theorem alive_3_1_3_14 : (aliveCodes (driveN 3 1) 3 14).card = 1 := by native_decide
theorem alive_3_1_1_6 : (aliveCodes (driveN 3 1) 1 6).card = 1 := by native_decide
theorem alive_3_1_1_4 : (aliveCodes (driveN 3 1) 1 4).card = 1 := by native_decide

theorem sharpA_3_1_14 : SharpAmortized 3 1 14 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_3_1_14,
    not_amortizedHalving_of_witness (k := 4) (d := 10) (m := 20) (by norm_num) (by norm_num)
      (by norm_num) (by rw [show 10 - 1 + 20 = 29 by rfl, alive_3_4_10_29]; norm_num)⟩

theorem sharpA_3_2_4 : SharpAmortized 3 2 4 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_3_2_4,
    not_amortizedHalving_of_witness (k := 1) (d := 3) (m := 12) (by norm_num) (by norm_num)
      (by norm_num) (by rw [show 3 - 1 + 12 = 14 by rfl, alive_3_1_3_14]; norm_num)⟩

theorem sharpA_3_3_2 : SharpAmortized 3 3 2 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_3_3_2,
    not_amortizedHalving_of_witness (k := 1) (d := 1) (m := 6) (by norm_num) (by norm_num)
      le_rfl (by rw [show 1 - 1 + 6 = 6 by rfl, alive_3_1_1_6]; norm_num)⟩

theorem sharpA_3_4_1 : SharpAmortized 3 4 1 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_3_4_1',
    not_amortizedHalving_of_witness (k := 1) (d := 1) (m := 4) (by norm_num) (by norm_num)
      le_rfl (by rw [show 1 - 1 + 4 = 4 by rfl, alive_3_1_1_4]; norm_num)⟩

/-! ## Period 4 -/

theorem linCheck_4_1_59 : linCheck 4 1 59 16 = true := by native_decide
theorem linCheck_4_2_44 : linCheck 4 2 44 16 = true := by native_decide
theorem linCheck_4_3_29 : linCheck 4 3 29 16 = true := by native_decide
theorem linCheck_4_4_14 : linCheck 4 4 14 16 = true := by native_decide
theorem linCheck_4_5_9 : linCheck 4 5 9 16 = true := by native_decide

theorem wit_4_15_20202 : dDiesBy (driveN 4 2) 20202 73 = false := by native_decide
theorem wit_4_1_1 : dDiesBy (driveN 4 2) 1 13 = false := by native_decide

theorem sharp_4_1_59 : SharpLinear 4 1 59 16 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_4_1_59,
    not_halfLineLinear_of_witness (k := 2) (d := 15) (S := 20202) (by norm_num) (by norm_num)
      (by norm_num) (by norm_num) (by norm_num) wit_4_15_20202⟩

theorem sharp_4_2_44 : SharpLinear 4 2 44 16 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_4_2_44,
    not_halfLineLinear_of_witness (k := 2) (d := 15) (S := 20202) (by norm_num) (by norm_num)
      (by norm_num) (by norm_num) (by norm_num) wit_4_15_20202⟩

theorem sharp_4_3_29 : SharpLinear 4 3 29 16 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_4_3_29,
    not_halfLineLinear_of_witness (k := 2) (d := 15) (S := 20202) (by norm_num) (by norm_num)
      (by norm_num) (by norm_num) (by norm_num) wit_4_15_20202⟩

theorem sharp_4_4_14 : SharpLinear 4 4 14 16 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_4_4_14,
    not_halfLineLinear_of_witness (k := 2) (d := 15) (S := 20202) (by norm_num) (by norm_num)
      (by norm_num) (by norm_num) (by norm_num) wit_4_15_20202⟩

theorem sharp_4_5_9 : SharpLinear 4 5 9 16 :=
  ⟨halfLineLinearUpTo_of_linCheck linCheck_4_5_9,
    not_halfLineLinear_of_witness (k := 2) (d := 1) (S := 1) (by norm_num) (by norm_num)
      le_rfl (by norm_num) (by norm_num) wit_4_1_1⟩

theorem amortCheck_4_1_19 : amortCheck 4 1 19 12 = true := by native_decide
theorem amortCheck_4_2_6 : amortCheck 4 2 6 12 = true := by native_decide
theorem amortCheck_4_3_4 : amortCheck 4 3 4 12 = true := by native_decide
theorem amortCheck_4_4_3 : amortCheck 4 4 3 12 = true := by native_decide
theorem amortCheck_4_5_2 : amortCheck 4 5 2 12 = true := by native_decide

theorem alive_4_4_9_34 : (aliveCodes (driveN 4 4) 9 34).card = 2 := by native_decide
theorem alive_4_1_1_12 : (aliveCodes (driveN 4 1) 1 12).card = 1 := by native_decide
theorem alive_4_1_1_10 : (aliveCodes (driveN 4 1) 1 10).card = 1 := by native_decide

theorem sharpA_4_1_19 : SharpAmortized 4 1 19 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_4_1_19,
    not_amortizedHalving_of_witness (k := 4) (d := 9) (m := 26) (by norm_num) (by norm_num)
      (by norm_num) (by rw [show 9 - 1 + 26 = 34 by rfl, alive_4_4_9_34]; norm_num)⟩

theorem sharpA_4_2_6 : SharpAmortized 4 2 6 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_4_2_6,
    not_amortizedHalving_of_witness (k := 1) (d := 1) (m := 12) (by norm_num) (by norm_num)
      le_rfl (by rw [show 1 - 1 + 12 = 12 by rfl, alive_4_1_1_12]; norm_num)⟩

theorem sharpA_4_3_4 : SharpAmortized 4 3 4 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_4_3_4,
    not_amortizedHalving_of_witness (k := 1) (d := 1) (m := 12) (by norm_num) (by norm_num)
      le_rfl (by rw [show 1 - 1 + 12 = 12 by rfl, alive_4_1_1_12]; norm_num)⟩

theorem sharpA_4_4_3 : SharpAmortized 4 4 3 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_4_4_3,
    not_amortizedHalving_of_witness (k := 1) (d := 1) (m := 12) (by norm_num) (by norm_num)
      le_rfl (by rw [show 1 - 1 + 12 = 12 by rfl, alive_4_1_1_12]; norm_num)⟩

theorem sharpA_4_5_2 : SharpAmortized 4 5 2 12 :=
  ⟨amortizedHalvingUpTo_of_check (by norm_num) amortCheck_4_5_2,
    not_amortizedHalving_of_witness (k := 1) (d := 1) (m := 10) (by norm_num) (by norm_num)
      le_rfl (by rw [show 1 - 1 + 10 = 10 by rfl, alive_4_1_1_10]; norm_num)⟩

/-! ## The round -/

/-- **The statement planner's frontier, certified.**  Every fitted offset on the frontier holds
on its range and is sharp there (offset − 1 is refuted by an explicit code). -/
theorem frontier_round30 :
    (SharpLinear 2 1 20 20 ∧ SharpLinear 2 2 9 20 ∧ SharpLinear 2 3 5 20 ∧
      SharpLinear 2 4 4 20 ∧ SharpLinear 2 5 3 20 ∧ SharpLinear 2 6 2 20) ∧
    (SharpLinear 3 1 39 18 ∧ SharpLinear 3 2 21 18 ∧ SharpLinear 3 3 7 18 ∧
      SharpLinear 3 4 4 18 ∧ SharpLinear 3 5 3 18 ∧ SharpLinear 3 6 2 18) ∧
    (SharpLinear 4 1 59 16 ∧ SharpLinear 4 2 44 16 ∧ SharpLinear 4 3 29 16 ∧
      SharpLinear 4 4 14 16 ∧ SharpLinear 4 5 9 16) ∧
    (SharpAmortized 2 1 11 12 ∧ SharpAmortized 2 2 3 12 ∧ SharpAmortized 2 3 2 12 ∧
      SharpAmortized 2 4 1 12) ∧
    (SharpAmortized 3 1 14 12 ∧ SharpAmortized 3 2 4 12 ∧ SharpAmortized 3 3 2 12 ∧
      SharpAmortized 3 4 1 12) ∧
    (SharpAmortized 4 1 19 12 ∧ SharpAmortized 4 2 6 12 ∧ SharpAmortized 4 3 4 12 ∧
      SharpAmortized 4 4 3 12 ∧ SharpAmortized 4 5 2 12) :=
  ⟨⟨sharp_2_1_20, sharp_2_2_9, sharp_2_3_5, sharp_2_4_4, sharp_2_5_3, sharp_2_6_2⟩,
    ⟨sharp_3_1_39, sharp_3_2_21, sharp_3_3_7, sharp_3_4_4, sharp_3_5_3, sharp_3_6_2⟩,
    ⟨sharp_4_1_59, sharp_4_2_44, sharp_4_3_29, sharp_4_4_14, sharp_4_5_9⟩,
    ⟨sharpA_2_1_11, sharpA_2_2_3, sharpA_2_3_2, sharpA_2_4_1⟩,
    ⟨sharpA_3_1_14, sharpA_3_2_4, sharpA_3_3_2, sharpA_3_4_1⟩,
    ⟨sharpA_4_1_19, sharpA_4_2_6, sharpA_4_3_4, sharpA_4_4_3, sharpA_4_5_2⟩⟩

end GLM.Rule30.PipelineData
