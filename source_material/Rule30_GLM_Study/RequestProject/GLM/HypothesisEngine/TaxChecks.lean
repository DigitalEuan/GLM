module

public import Mathlib
public import RequestProject.GLM.Rule30.LeftDiagonalPeriods

/-!
# Round 42: checking the TAX statements of `hypothesis_engine_v13.py`

Engine v13 adds a "TAX tool". For a binary pattern of weight `w` (number of black cells) it sets

  `TAX(w) = Y · w + w² / 8`,  with `Y = 1 / (π + 2/π)`,

and calls the pair of patterns `(a, b)` *TAX-conserved* when

  `TAX(w(a XOR b)) = TAX(w(a)) + TAX(w(b)) − 2 · TAX(w(a AND b))`.

The integer `defect = w(a)² + w(b)² − 2·w(a AND b)² − w(a XOR b)²` is its "TAX defect".
v13 tests whether TAX defects explain the period-doubling diagonals of Rule 30. This file checks
the mathematical statements it makes along the way.

| v13 statement | verdict | Lean |
|---|---|---|
| "because `Y` is irrational, conservation holds iff the quadratic identity holds" | the conclusion is true for **every** real `Y`; irrationality is not needed (the linear part always cancels) | `tax_conserved_iff_defect_zero` |
| "this in turn holds iff `w(a AND b) ∈ {0, w(a), w(b)}`" | **false in both directions** | `docstring_iff_fails_disjoint`, `docstring_iff_fails_partial` |
| — (the correct criterion) | `defect = −2·(3c² − 2c(a+b) + ab)` with `a, b, c` the weights of `a`, `b`, `a AND b` | `tax_defect_eq` |
| "at every jump the defect is 0 … the white pattern is the common cause" | true, and trivial: **any** pair with a white member is conserved | `tax_conserved_of_right_empty` |
| "TAX breakdown is NECESSARY for a jump" (v12, repeated in v13's verdict) | **false at every doubling diagonal** | `tax_conserved_at_doubling` |

The last row is about Rule 30 itself: whenever the doubling law `ldiag_doubles` applies at
diagonal `D` (diagonal `D − 1` white from time `T`, odd parity of `D − 2`), the window patterns of
diagonals `D` and `D − 1` are TAX-conserved, for every `Y` and every window length. So a TAX defect
can never mark a period doubling; v13's own data (defect 0 at `D = 3, 8, 29, 400`) agree with this.

Everything here is FORMAL (no `native_decide`).
-/

@[expose] public section

namespace GLM.HypothesisEngine.Tax

open GLM.Rule30

/-! ## 1. The TAX of a weight and the defect of a pair of patterns -/

/-- v13's TAX of a binary pattern of weight `w`, for a parameter `Y` (v13 uses `1/(π + 2/π)`). -/
noncomputable def tax (Y : ℝ) (w : ℕ) : ℝ := Y * w + (w : ℝ) ^ 2 / 8

/-- v13's TAX conservation for the pair of patterns `A`, `B` (sets of black positions):
`TAX(A XOR B) = TAX(A) + TAX(B) − 2·TAX(A AND B)`. -/
def TaxConserved (Y : ℝ) (A B : Finset ℕ) : Prop :=
  tax Y (symmDiff A B).card = tax Y A.card + tax Y B.card - 2 * tax Y (A ∩ B).card

/-- v13's integer TAX defect `w(a)² + w(b)² − 2·w(a AND b)² − w(a XOR b)²`. -/
def taxDefect (A B : Finset ℕ) : ℤ :=
  (A.card : ℤ) ^ 2 + (B.card : ℤ) ^ 2 - 2 * ((A ∩ B).card : ℤ) ^ 2 - ((symmDiff A B).card : ℤ) ^ 2

/-- Weight conservation (always true): `w(a XOR b) + 2·w(a AND b) = w(a) + w(b)`. -/
theorem card_symmDiff_add_two_inter (A B : Finset ℕ) :
    (symmDiff A B).card + 2 * (A ∩ B).card = A.card + B.card := by
  have h1 : symmDiff A B = (A ∪ B) \ (A ∩ B) := symmDiff_eq_sup_sdiff_inf A B
  have h2 : (A ∩ B) ⊆ (A ∪ B) := Finset.inter_subset_union
  have h3 := Finset.card_sdiff_add_card_eq_card h2
  have h4 := Finset.card_union_add_card_inter A B
  rw [h1]
  omega

/-- **The correct criterion.** With `a = w(A)`, `b = w(B)`, `c = w(A ∩ B)`,
`defect = −2·(3c² − 2c(a + b) + ab)`. -/
theorem tax_defect_eq (A B : Finset ℕ) :
    taxDefect A B = -2 * (3 * ((A ∩ B).card : ℤ) ^ 2
      - 2 * ((A ∩ B).card : ℤ) * ((A.card : ℤ) + B.card) + (A.card : ℤ) * B.card) := by
  have h := card_symmDiff_add_two_inter A B
  have h' : ((symmDiff A B).card : ℤ) = A.card + B.card - 2 * (A ∩ B).card := by
    have : ((symmDiff A B).card : ℤ) + 2 * (A ∩ B).card = A.card + B.card := by exact_mod_cast h
    linarith
  unfold taxDefect
  rw [h']
  ring

/-- **Conservation does not depend on `Y`.** For every real `Y` (rational or not), TAX
conservation holds exactly when the integer defect is `0`. -/
theorem tax_conserved_iff_defect_zero (Y : ℝ) (A B : Finset ℕ) :
    TaxConserved Y A B ↔ taxDefect A B = 0 := by
  have h := card_symmDiff_add_two_inter A B
  have hR : ((symmDiff A B).card : ℝ) = A.card + B.card - 2 * (A ∩ B).card := by
    have : ((symmDiff A B).card : ℝ) + 2 * (A ∩ B).card = A.card + B.card := by exact_mod_cast h
    linarith
  have hZ : ((symmDiff A B).card : ℤ) = A.card + B.card - 2 * (A ∩ B).card := by
    have : ((symmDiff A B).card : ℤ) + 2 * (A ∩ B).card = A.card + B.card := by exact_mod_cast h
    linarith
  unfold TaxConserved tax taxDefect
  rw [hR, hZ]
  constructor
  · intro hc
    have : (((A.card : ℤ) ^ 2 + (B.card : ℤ) ^ 2 - 2 * ((A ∩ B).card : ℤ) ^ 2
        - ((A.card : ℤ) + B.card - 2 * (A ∩ B).card) ^ 2 : ℤ) : ℝ) = 0 := by
      push_cast; linarith
    exact_mod_cast this
  · intro hc
    have : (((A.card : ℤ) ^ 2 + (B.card : ℤ) ^ 2 - 2 * ((A ∩ B).card : ℤ) ^ 2
        - ((A.card : ℤ) + B.card - 2 * (A ∩ B).card) ^ 2 : ℤ) : ℝ) = 0 := by
      exact_mod_cast hc
    push_cast at this; linarith

/-- A pair with a white (empty) second pattern is always TAX-conserved, for every `Y`. -/
theorem tax_conserved_of_right_empty (Y : ℝ) (A : Finset ℕ) : TaxConserved Y A ∅ := by
  rw [tax_conserved_iff_defect_zero, tax_defect_eq]; simp

/-- A pair with a white (empty) first pattern is always TAX-conserved, for every `Y`. -/
theorem tax_conserved_of_left_empty (Y : ℝ) (B : Finset ℕ) : TaxConserved Y ∅ B := by
  rw [tax_conserved_iff_defect_zero, tax_defect_eq]; simp

/-- Equal patterns are always TAX-conserved. -/
theorem tax_conserved_of_eq (Y : ℝ) (A : Finset ℕ) : TaxConserved Y A A := by
  rw [tax_conserved_iff_defect_zero, tax_defect_eq]; simp; ring

/-! ## 2. v13's stated criterion is false in both directions -/

/-- v13's docstring criterion: "conserved iff `w(a AND b) ∈ {0, w(a), w(b)}`". -/
def DocstringCriterion (A B : Finset ℕ) : Prop :=
  (A ∩ B).card = 0 ∨ (A ∩ B).card = A.card ∨ (A ∩ B).card = B.card

/-- **Criterion ⇏ conservation.** Two disjoint single cells: `w(a AND b) = 0`, yet the defect is
`−2`. -/
theorem docstring_iff_fails_disjoint :
    DocstringCriterion {0} {1} ∧ taxDefect {0} {1} = -2 := by
  refine ⟨Or.inl (by decide), by decide⟩

/-- **Conservation ⇏ criterion.** Patterns of weights `5` and `8` overlapping in `2` cells are
conserved (for every `Y`), although `2 ∉ {0, 5, 8}`. -/
theorem docstring_iff_fails_partial :
    ¬ DocstringCriterion (Finset.range 5) (Finset.Icc 3 10) ∧
      taxDefect (Finset.range 5) (Finset.Icc 3 10) = 0 := by
  refine ⟨by unfold DocstringCriterion; decide, by decide⟩

/-- v13's criterion is not equivalent to TAX conservation, for any `Y`. -/
theorem docstring_criterion_wrong (Y : ℝ) :
    ¬ ∀ A B : Finset ℕ, TaxConserved Y A B ↔ DocstringCriterion A B := by
  intro h
  have h1 := (h {0} {1}).2 docstring_iff_fails_disjoint.1
  rw [tax_conserved_iff_defect_zero, docstring_iff_fails_disjoint.2] at h1
  exact absurd h1 (by decide)

/-! ## 3. Rule 30: a TAX defect never marks a period doubling -/

/-- The black positions of the sequence `s` in the window `[T, T + Q)`, as phases `0 … Q − 1`. -/
def windowPattern (s : ℕ → Bool) (T Q : ℕ) : Finset ℕ :=
  (Finset.range Q).filter (fun i => s (T + i) = true)

/-- A sequence white from time `T` has the empty window pattern from `T`. -/
theorem windowPattern_eq_empty {s : ℕ → Bool} {T : ℕ} (hw : ∀ t ≥ T, s t = false) (Q : ℕ) :
    windowPattern s T Q = ∅ := by
  unfold windowPattern
  rw [Finset.filter_eq_empty_iff]
  intro i _
  simp [hw (T + i) (by omega)]

/-- **At every period doubling of a Rule 30 left diagonal, TAX is conserved.** Under the
hypotheses of the doubling law `ldiag_doubles` (diagonal `D − 2` is `Q`-periodic from `T`,
diagonal `D − 1` is white from `T`, and `D − 2` has odd parity over a period), the diagonal `D`
doubles its period, and the window patterns of diagonals `D` and `D − 1` from time `T`
are TAX-conserved for every `Y` and every window length `L`. So "a TAX defect at `(D − 1, D)` is
necessary for a jump at `D`" is false at every jump the doubling law produces. -/
theorem tax_conserved_at_doubling {D : ℤ} {Q T : ℕ}
    (h2 : ∀ t ≥ T, ldiag (D - 2) (t + Q) = ldiag (D - 2) t)
    (hw : ∀ t ≥ T, ldiag (D - 1) t = false) (hodd : parityOn (ldiag (D - 2)) T Q = true)
    (Y : ℝ) (L : ℕ) :
    (¬ EvPer (ldiag D) Q ∧ EvPer (ldiag D) (2 * Q)) ∧
      TaxConserved Y (windowPattern (ldiag D) T L) (windowPattern (ldiag (D - 1)) T L) := by
  refine ⟨ldiag_doubles h2 hw hodd, ?_⟩
  rw [windowPattern_eq_empty hw]
  exact tax_conserved_of_right_empty Y _

end GLM.HypothesisEngine.Tax
