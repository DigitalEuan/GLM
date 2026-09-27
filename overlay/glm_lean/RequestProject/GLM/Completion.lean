/-
# Filling a sparse register without spoiling it

The element register carries **1,257 of 1,652** cells as measurements.
`glm_universal/reasoning/element_coverage.py` widens that by derivation and by
one fitted line, and deliberately writes nothing back;
`glm_universal/reasoning/element_completion.py` goes the step that closes the
item: it *decides* every empty cell, filling the ones an admitted rule reaches
and saying, of each one it does not, which of three reasons applies.

This file is the part of that arrangement which is not a measurement: what a
layer of estimates may and may not do to the register underneath it, and what
the gate on a rule actually says.

* `Cell` is the five things a cell of the completed grid can be: a
  measurement, an estimate, or one of the three decisions about an empty cell.
* `cell` is the classification itself, over an abstract register `Base` and an
  abstract rule set `Rules`.

What is proved:

* `cell_measured_iff` -- the completed view's measured layer *is* the
  register: a cell reads `measured v` exactly when the register holds `v`
  there.  A caller who asks for measurements gets measurements;
* `readMeasured_eq_base` -- the same claim as a function identity, which is
  the form the implementation's `measured_view_is_the_register` checks;
* `estimated_of_empty` -- an estimate only ever occupies a cell the register
  leaves empty, so no estimate can overwrite a measurement;
* `filled_of_measured` and `coverage_monotone` -- adding a layer of estimates
  never loses a cell: coverage can only rise;
* `dispositions_exhaustive` and `dispositions_exclusive` -- every cell gets
  exactly one of the five readings, which is the ledger's claim that no empty
  cell is left as a failed lookup;
* `admitted_halves_the_baseline` -- what the gate says: an admitted rule's
  out-of-sample error is at most half the error of predicting the field's
  mean.  Admission is a claim that the rule beat a control, not that it fits
  closely.

The last section is the ledger of the round, as arithmetic: the four
dispositions account for all 395 empty cells and the completed view fills
1,442 of 1,652.  The counts themselves are measured by the Python; what is
checked here is that they add up to the register they are about.
-/
import Mathlib.Tactic

namespace GLM.Completion

/-! ## 1.  The register, the rules, and what a cell reads -/

/-- A sparse register: a value at some name-field pairs and nothing at others. -/
structure Base (Name Field Value : Type) where
  /-- The measurement held at a cell, if any. -/
  value : Name → Field → Option Value

/-- The layer above it.  `derivable` says whether a field is the *kind* of
thing a rule over this register could reach at all; `admitted` whether the
rule found for it passed the gate; `estimate` is what that rule produces where
its inputs are present. -/
structure Rules (Name Field Value : Type) where
  /-- Whether a field is the kind of thing a rule could reach. -/
  derivable : Field → Bool
  /-- Whether the rule found for the field passed the gate. -/
  admitted : Field → Bool
  /-- The admitted rule's value, where its inputs are present. -/
  estimate : Name → Field → Option Value

/-- What one cell of the completed grid reads.  The first two carry a value;
the last three are the decisions made about an empty cell. -/
inductive Cell (Value : Type)
  /-- The register holds a measurement here. -/
  | measured : Value → Cell Value
  /-- An admitted rule reached the cell. -/
  | estimated : Value → Cell Value
  /-- The field has an admitted rule; this element lacks its inputs. -/
  | inputsAbsent : Cell Value
  /-- Every rule tried for the field failed the gate. -/
  | noAdmittedRule : Cell Value
  /-- No rule over this register could reach the field at all. -/
  | notDerivable : Cell Value
  deriving DecidableEq

variable {Name Field Value : Type}

/-- The classification.  A measurement is read as a measurement before
anything else is considered, which is what makes the layer safe. -/
def cell (B : Base Name Field Value) (R : Rules Name Field Value)
    (n : Name) (f : Field) : Cell Value :=
  match B.value n f with
  | some v => Cell.measured v
  | none =>
      if ¬ R.derivable f then Cell.notDerivable
      else if ¬ R.admitted f then Cell.noAdmittedRule
      else
        match R.estimate n f with
        | some v => Cell.estimated v
        | none => Cell.inputsAbsent

/-! ## 2.  The register is not disturbed -/

/-- The measured layer is the register, cell for cell. -/
theorem cell_measured_iff (B : Base Name Field Value)
    (R : Rules Name Field Value) (n : Name) (f : Field) (v : Value) :
    cell B R n f = Cell.measured v ↔ B.value n f = some v := by
  unfold cell
  cases h : B.value n f with
  | some w =>
      simp only
      constructor
      · intro hc; cases hc; rfl
      · intro hw; cases hw; rfl
  | none =>
      simp only
      constructor
      · intro hc
        by_cases hd : ¬ R.derivable f
        · simp [hd] at hc
        · by_cases ha : ¬ R.admitted f
          · simp [hd, ha] at hc
          · cases he : R.estimate n f <;> simp [hd, ha, he] at hc
      · intro hw; exact absurd hw (by simp)

/-- Reading the completed grid at the measured provenance and reading the
register are the same function.  This is the identity the implementation's
`measured_view_is_the_register` checks cell by cell. -/
def readMeasured : Cell Value → Option Value
  | Cell.measured v => some v
  | _ => none

theorem readMeasured_eq_base (B : Base Name Field Value)
    (R : Rules Name Field Value) (n : Name) (f : Field) :
    readMeasured (cell B R n f) = B.value n f := by
  unfold cell
  cases h : B.value n f with
  | some w => simp [readMeasured]
  | none =>
      by_cases hd : ¬ R.derivable f
      · simp [hd, readMeasured]
      · by_cases ha : ¬ R.admitted f
        · simp [hd, ha, readMeasured]
        · cases R.estimate n f <;> simp [hd, ha, readMeasured]

/-- An estimate only ever occupies a cell the register leaves empty. -/
theorem estimated_of_empty (B : Base Name Field Value)
    (R : Rules Name Field Value) {n : Name} {f : Field} {v : Value}
    (h : cell B R n f = Cell.estimated v) : B.value n f = none := by
  unfold cell at h
  cases hb : B.value n f with
  | none => rfl
  | some w => rw [hb] at h; cases h

/-! ## 3.  Coverage can only rise -/

/-- Whether a reading carries a value at all. -/
def filled : Cell Value → Bool
  | Cell.measured _ => true
  | Cell.estimated _ => true
  | _ => false

/-- Every measured cell is filled in the completed view. -/
theorem filled_of_measured (B : Base Name Field Value)
    (R : Rules Name Field Value) {n : Name} {f : Field} {v : Value}
    (h : B.value n f = some v) : filled (cell B R n f) = true := by
  unfold cell; rw [h]; rfl

/-- So no cell is lost: over any finite set of cells, the completed view fills
at least as many as the register does. -/
theorem coverage_monotone [DecidableEq Name] [DecidableEq Field]
    (B : Base Name Field Value) (R : Rules Name Field Value)
    (s : Finset (Name × Field)) :
    (s.filter fun p => (B.value p.1 p.2).isSome).card
      ≤ (s.filter fun p => filled (cell B R p.1 p.2) = true).card := by
  apply Finset.card_le_card
  intro p hp
  simp only [Finset.mem_filter] at hp ⊢
  obtain ⟨hs, hsome⟩ := hp
  obtain ⟨v, hv⟩ := Option.isSome_iff_exists.mp hsome
  exact ⟨hs, filled_of_measured B R hv⟩

/-! ## 4.  Every cell is decided, and decided once -/

/-- Every cell reads as exactly one of the five, and the reading is total: no
cell is left as a failed lookup.  This is the ledger's claim. -/
theorem dispositions_exhaustive (B : Base Name Field Value)
    (R : Rules Name Field Value) (n : Name) (f : Field) :
    (∃ v, cell B R n f = Cell.measured v)
      ∨ (∃ v, cell B R n f = Cell.estimated v)
      ∨ cell B R n f = Cell.inputsAbsent
      ∨ cell B R n f = Cell.noAdmittedRule
      ∨ cell B R n f = Cell.notDerivable := by
  cases h : cell B R n f with
  | measured v => exact Or.inl ⟨v, rfl⟩
  | estimated v => exact Or.inr (Or.inl ⟨v, rfl⟩)
  | inputsAbsent => exact Or.inr (Or.inr (Or.inl rfl))
  | noAdmittedRule => exact Or.inr (Or.inr (Or.inr (Or.inl rfl)))
  | notDerivable => exact Or.inr (Or.inr (Or.inr (Or.inr rfl)))

/-- And no cell reads as two of them: a measurement is not an estimate, and a
decision about an empty cell is not a value. -/
theorem dispositions_exclusive (B : Base Name Field Value)
    (R : Rules Name Field Value) (n : Name) (f : Field) (v w : Value) :
    ¬ (cell B R n f = Cell.measured v ∧ cell B R n f = Cell.estimated w) := by
  rintro ⟨h₁, h₂⟩
  rw [h₁] at h₂
  cases h₂

/-! ## 5.  What the gate says -/

/-- The gate: a rule is admitted when its leave-one-out error is at most half
the error of predicting the field's mean, and it was scored on at least twenty
elements. -/
def admits (loo baseline : ℚ) (scoredOn : ℕ) : Prop :=
  0 < baseline ∧ loo / baseline ≤ 1 / 2 ∧ 20 ≤ scoredOn

/-- What admission buys, stated without the division: an admitted rule's
out-of-sample error is at most half the constant rule's.  The control is the
field's own mean, so admission is a claim that the rule found something. -/
theorem admitted_halves_the_baseline {loo baseline : ℚ} {scoredOn : ℕ}
    (h : admits loo baseline scoredOn) : 2 * loo ≤ baseline := by
  obtain ⟨hpos, hskill, -⟩ := h
  have := (div_le_iff₀ hpos).mp hskill
  linarith

/-- A rule no better than the mean is refused, whatever else is true of it. -/
theorem not_admitted_of_no_skill {loo baseline : ℚ} {scoredOn : ℕ}
    (h : baseline < 2 * loo) :
    ¬ admits loo baseline scoredOn := by
  intro hadm
  exact absurd (admitted_halves_the_baseline hadm) (not_le.mpr h)

/-! ## 6.  The ledger of the round

The counts are measured by `element_completion.element_completion_report`;
what is checked here is that they are a partition of the register they are
about -- 395 empty cells decided four ways, and 1,442 of 1,652 filled once the
estimates are read. -/

/-- The four dispositions account for every empty cell. -/
theorem ledger_accounts_for_every_empty_cell :
    185 + 100 + 97 + 13 = 1652 - 1257 := by norm_num

/-- And the completed view fills the measured cells plus the estimated ones. -/
theorem ledger_coverage : 1257 + 185 = 1442 := by norm_num

end GLM.Completion
