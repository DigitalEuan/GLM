import RequestProject.GLM.Rule30.PostEdgeSpec

/-!
# Round 29 certificate: the uniform inner-survivor form is refuted (To Do 22)

(Not a `module`: the check uses `native_decide`, like the other `…Data.lean` files.)

To Do 19 asked whether long survivors of the period-2 half-line machine (drive word `10`) always
carry a long alternating inner column, which with `inner_alternation_bound` would give a recursion
on the width.  Round 28 tested it outside Lean (EMP, `rule30_round28/inner_survivors.py`) and found
no support.  This file states the uniform form and refutes it with a checked witness.

* `AltRun bd S k s A` — inner column `c − k` alternates at the `A` consecutive times
  `s, …, s + A − 1`.
* `InnerFollows a` — every code of length `d` that dies at time `L` after its edge (`L > d − 1`)
  has, for some `k ≥ 1`, an alternating stretch inside `[0, L]` of length at least
  `(L − (d − 1)) − a` (its post-edge life minus the slack `a`).

**`not_innerFollows`**: `InnerFollows a` is false for every `a ≤ 7`.  Witness: `d = 14`,
code `11083`, first failure at time `L = 32` (post-edge life `19`), and no inner column at any
depth alternates for `12` consecutive times within `[0, 32]` (`witness_no_long_alternation`;
depths beyond the light cone are constant by `halfStateD_width`).  The EMP range `d ≤ 22` gives
slack `8` as the sharpest value; the slack grows with `d` in the data, so no fixed slack is
expected to work.
-/

namespace GLM.Rule30

/-- Inner column `c − k` alternates at the `A` consecutive times `s, …, s + A − 1`. -/
def AltRun (bd : ℕ → Bool) (S k s A : ℕ) : Prop :=
  ∀ u, u + 1 < A → innerCol bd S k (s + u) ≠ innerCol bd S k (s + u + 1)

/-- **To Do 19, uniform form with slack `a`.** Every code that survives past its edge carries an
inner alternating stretch at least as long as its post-edge life minus `a`. -/
def InnerFollows (a : ℕ) : Prop :=
  ∀ d S L : ℕ, 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
    dDiesBy (driveN 2 1) S L = false → dDiesBy (driveN 2 1) S (L + 1) = true → d - 1 < L →
    ∃ k, 1 ≤ k ∧ ∃ s A, s + A ≤ L + 1 ∧ L - (d - 1) ≤ A + a ∧ AltRun (driveN 2 1) S k s A

/-- The checked part: inside the light cone (`k ≤ 14 + 32`), no window of `12` consecutive
times in `[0, 32]` is alternating for the code `11083`. -/
def noLongAltCheck : Bool :=
  (List.range 46).all fun k' => (List.range 22).all fun s =>
    (List.range 11).any fun u =>
      innerCol (driveN 2 1) 11083 (k' + 1) (s + u) == innerCol (driveN 2 1) 11083 (k' + 1) (s + u + 1)

theorem noLongAltCheck_eq : noLongAltCheck = true := by native_decide

/-- The witness: code `11083` of length `14` first fails at time `32`. -/
theorem witness_life :
    dDiesBy (driveN 2 1) 11083 32 = false ∧ dDiesBy (driveN 2 1) 11083 33 = true := by
  native_decide

/-- **No inner column of the witness alternates for 12 consecutive times within `[0, 32]`.** -/
theorem witness_no_long_alternation {k s A : ℕ} (hk : 1 ≤ k) (hsA : s + A ≤ 33)
    (h : AltRun (driveN 2 1) 11083 k s A) : A ≤ 11 := by
  by_contra hA
  push_neg at hA
  by_cases hkc : k ≤ 46
  · have h1 := List.all_eq_true.1 noLongAltCheck_eq (k - 1) (List.mem_range.2 (by omega))
    have h2 := List.all_eq_true.1 h1 s (List.mem_range.2 (by omega))
    obtain ⟨u, hu, hEq⟩ := List.any_eq_true.1 h2
    rw [List.mem_range] at hu
    rw [show k - 1 + 1 = k by omega, beq_iff_eq] at hEq
    exact h u (by omega) hEq
  · -- beyond the light cone the column is constantly white
    have hw : ∀ t ≤ 32, innerCol (driveN 2 1) 11083 k t = false := by
      intro t ht
      have hb := (halfStateD_width (driveN 2 1) (S := 11083) (d := 14) (by norm_num)
        (by norm_num) (by norm_num) t).2
      unfold innerCol
      exact Nat.testBit_lt_two_pow (lt_of_lt_of_le hb (Nat.pow_le_pow_right (by norm_num)
        (by omega)))
    exact h 0 (by omega) (by rw [hw _ (by omega), hw _ (by omega)])

/-- **The uniform inner-survivor form is refuted for every slack `a ≤ 7`** (To Do 22). -/
theorem not_innerFollows {a : ℕ} (ha : a ≤ 7) : ¬ InnerFollows a := by
  intro h
  obtain ⟨k, hk, s, A, hsA, hlen, hrun⟩ :=
    h 14 11083 32 (by norm_num) (by norm_num) (by norm_num) witness_life.1 witness_life.2
      (by norm_num)
  have := witness_no_long_alternation hk hsA hrun
  omega

end GLM.Rule30
