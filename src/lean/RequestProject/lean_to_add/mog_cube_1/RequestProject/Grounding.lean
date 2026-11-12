import Mathlib
import RequestProject.IntegerCube
import RequestProject.Semantics

/-!
# Grounding the language in the measurable layer

Two layers have been built:

* the **measurable** layer (`MeasuredWords`, `IntegerCube`) — a word's dimension
  on the 24 cells, with exact integer exponents and free composition;
* the **semantic** layer (`Semantics`, `Chat`) — a micro-world, sentences,
  reasons and predictions.

This file states precisely how they meet, and — just as precisely — where each
one stops.

## Every sentence of the language is a comparison of dimensioned readings

`compsOf` unpacks each atom into the comparisons it actually performs: "the
water is frozen" is `temp(water) ≤ 0 °C`, "the water is warm" is
`0 °C < temp(water)` together with `temp(water) < 100 °C`, "the stone is heavier
than the water" is `mass(water) < mass(stone)`.  `compsOf_correct` proves this
unpacking is exactly the truth condition already used by `Semantics.evalAtom` —
it is a description of the language, not a second definition of it.

## What the measurable layer contributes: a type discipline

`atoms_are_well_typed` — in every comparison the language performs, the two
sides carry the same dimension: temperatures with temperatures (including the
thresholds `0 °C` and `100 °C`), masses with masses (including `10 kg`).  On the
cube that comparison is accepted at **zero tax** (`well_typed_tax_zero`), while
a category error — a temperature against a mass — is rejected and costs at
least `8·Q` (`category_error_is_rejected`).  The substrate is thus a type
checker for the language: it rules out "the water is hotter than the stone's
mass" without knowing anything about water or stones.

## Where it stops: dimensions cannot decide truth

`dimension_cannot_decide_truth` — the dimensional record of an atom is the same
in every world while its truth is not, so no computation on dimensions can
settle "is the water frozen?"; that takes the reading.  And
`truth_cannot_supply_types` — truth values do not determine dimensions either.
The two layers are genuinely complementary: the cube types and protects the
sentence, the measurement makes it true or false.

## One thing the surface cannot do at once

The 24 cells hold *either* the dimensional record of a quantity
(`IntegerCube.encG`) *or* the three-cube record of a clause
(`SentenceCode.clauseCode`).  Nothing here lets one cube be both; a full system
needs one cube per role.
-/

namespace Grounding

open MeasuredWords IntegerCube Semantics

/-- The dimension of a temperature. -/
def temperatureDim : Dim := ![0, 0, 0, 0, 1, 0]

/-- The dimension of a mass. -/
def massDim : Dim := ![0, 1, 0, 0, 0, 0]

/-- A comparison of two dimensioned readings: `right < left` when `strict`,
`right ≤ left` otherwise. -/
structure Comparison where
  /-- The larger side of the comparison. -/
  left : World → ℤ
  /-- Its dimension. -/
  leftDim : Dim
  /-- The smaller side. -/
  right : World → ℤ
  /-- Its dimension. -/
  rightDim : Dim
  /-- Whether the comparison is strict. -/
  strict : Bool

/-- The truth of a comparison in a world. -/
def evalComp (c : Comparison) (w : World) : Bool :=
  if c.strict then decide (c.right w < c.left w) else decide (c.right w ≤ c.left w)

/-- A dimensioned constant, used for the thresholds. -/
def constComp (k : ℤ) : World → ℤ := fun _ => k

/-- **What each atom actually measures.** -/
def compsOf : Atom → List Comparison
  | .frozen e =>
      [{ left := constComp 0, leftDim := temperatureDim,
         right := fun w => temp w e, rightDim := temperatureDim, strict := false }]
  | .boiling e =>
      [{ left := fun w => temp w e, leftDim := temperatureDim,
         right := constComp 100, rightDim := temperatureDim, strict := false }]
  | .warm e =>
      [{ left := fun w => temp w e, leftDim := temperatureDim,
         right := constComp 0, rightDim := temperatureDim, strict := true },
       { left := constComp 100, leftDim := temperatureDim,
         right := fun w => temp w e, rightDim := temperatureDim, strict := true }]
  | .heavy e =>
      [{ left := fun w => mass w e, leftDim := massDim,
         right := constComp 10, rightDim := massDim, strict := false }]
  | .hotter e f =>
      [{ left := fun w => temp w e, leftDim := temperatureDim,
         right := fun w => temp w f, rightDim := temperatureDim, strict := true }]
  | .heavier e f =>
      [{ left := fun w => mass w e, leftDim := massDim,
         right := fun w => mass w f, rightDim := massDim, strict := true }]

/-- **The unpacking is faithful**: an atom is true exactly when all the
comparisons it performs hold. -/
theorem compsOf_correct (a : Atom) (w : World) :
    evalAtom a w = (compsOf a).all fun c => evalComp c w := by
  cases a <;> simp [evalAtom, compsOf, evalComp, constComp, Bool.decide_and]

/-- **Every comparison the language performs is between like and like.** -/
theorem atoms_are_well_typed (a : Atom) :
    ∀ c ∈ compsOf a, c.leftDim = c.rightDim := by
  cases a <;> intro c hc <;> simp [compsOf] at hc <;> rcases hc with rfl | rfl <;> rfl

/-- **…so the cube accepts every comparison for nothing.** -/
theorem well_typed_accepted (a : Atom) :
    ∀ c ∈ compsOf a, encG c.leftDim = encG c.rightDim := fun c hc => by
  rw [atoms_are_well_typed a c hc]

/-- The same statement in the substrate's own price list. -/
theorem well_typed_tax_zero (a : Atom) :
    ∀ c ∈ compsOf a, MeasuredWords.taxOf c.leftDim c.rightDim = 0 := fun c hc => by
  rw [atoms_are_well_typed a c hc]
  exact MeasuredWords.taxOf_accepted _ _ rfl

/-- **A category error is rejected, at full price.**  Comparing a temperature
with a mass is not a sentence of this language, and the substrate charges at
least `8·Q` for it: the type discipline is the cube's, not a convention. -/
theorem category_error_is_rejected :
    encG temperatureDim ≠ encG massDim ∧
      8 * GolayHex.Q ≤ MeasuredWords.taxOf temperatureDim massDim := by
  have hne : dimWord temperatureDim ≠ dimWord massDim := by
    rw [Ne, dimWord_eq_iff]
    intro h
    have := h 1
    revert this
    decide
  refine ⟨?_, MeasuredWords.taxOf_detected _ _ hne⟩
  rw [Ne, encG_eq_iff]
  intro h
  have := h 1
  revert this
  decide

/-- **Dimensions cannot decide truth.**  The comparison an atom performs is the
same in every world, but its truth is not: the reading has to be taken. -/
theorem dimension_cannot_decide_truth :
    ∃ (a : Atom) (w w' : World),
      (∀ c ∈ compsOf a, c.leftDim = c.rightDim) ∧ evalAtom a w ≠ evalAtom a w' := by
  refine ⟨.frozen .water, demoWorld, (fun _ => 3, fun _ => 0), atoms_are_well_typed _, ?_⟩
  decide

/-- The converse half: truth values do not determine dimensions, so the semantic
layer cannot supply the type discipline either. -/
theorem truth_cannot_supply_types :
    ∃ (a b : Atom) (ca cb : Comparison),
      evalAtom a demoWorld = evalAtom b demoWorld ∧
        ca ∈ compsOf a ∧ cb ∈ compsOf b ∧ ca.leftDim ≠ cb.leftDim := by
  refine ⟨.frozen .water, .heavy .stone,
    { left := constComp 0, leftDim := temperatureDim,
      right := fun w => temp w .water, rightDim := temperatureDim, strict := false },
    { left := fun w => Semantics.mass w .stone, leftDim := massDim,
      right := constComp 10, rightDim := massDim, strict := false },
    by decide, by simp [compsOf], by simp [compsOf], ?_⟩
  intro h
  have := congrFun h 1
  revert this
  decide

end Grounding
