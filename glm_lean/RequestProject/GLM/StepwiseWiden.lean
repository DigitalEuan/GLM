module

public import Mathlib
public import RequestProject.GLM.StepwiseFrames

/-!
# The stepwise planner, round three: declared comparatives and folds over a column

Round three of the stepwise planner (`glm_universal.runtime.stepwise`,
`glm_universal.runtime.declared_frames`, Phase 84,
`studies/STEPWISE_THREE_STUDY.md`) reads comparatives with a declared register
field (*which is heavier, iron or copper*), further count nouns, the tera- and
pico- prefixes, and folds — a sum, a mean or a parity count — over a whole
column or a declared class of rows.  This file proves what its answers and
refusals rest on.

* **The comparative** (`winner_swap`, `winner_flip_ne`, `winner_eq_none_iff`):
  the row a declared comparative names does not depend on the order the two
  rows are written in; the comparative and its opposite (*heavier* and
  *lighter*, *older* and *newer*) never name the same row of two distinct
  rows; and no row is named exactly when the two values are equal.
* **A fold over a partition** (`fold_sum_partition`): the sum over the whole
  column is the sum, over the classes, of the sums over each class — so the
  declared classes of the register can be checked against the whole column.
* **Parity counts** (`even_sum_iff_even_odd_count`, `odd_count_add_even_count`):
  a sum of integers is even exactly when an even number of its terms is odd,
  and the odd and even counts together are the size of the column.
* **The hole** (`mean_cons_eq_iff`, `hole_mean_injective`): with one reading
  missing, the mean over the present rows is the column's mean only if the
  missing reading happens to equal it, and distinct missing readings give
  distinct means — so no answer from the present rows is right for every
  completion, and `COLUMN_HOLE` withholds nothing that could be known.
-/

namespace GLM.StepwiseWiden

open scoped BigOperators
open GLM.StepwiseFrames

/-! ## The comparative -/

/-- The row a declared comparative names, of two rows `a` and `b` with values
`x` and `y`: `dir = true` names the one with the larger value (*heavier*,
*denser*, *newer*), `dir = false` the one with the smaller (*lighter*,
*older*); equal values name neither. -/
public def winner {α : Type*} (dir : Bool) (a b : α) (x y : ℚ) : Option α :=
  if x = y then none else if decide (y < x) = dir then some a else some b

/-- The named row does not depend on the order the two rows are written. -/
public theorem winner_swap {α : Type*} (dir : Bool) (a b : α) (x y : ℚ) :
    winner dir a b x y = winner dir b a y x := by
  unfold winner
  by_cases h : x = y
  · subst h; simp
  · have h' : y ≠ x := fun e => h e.symm
    rw [if_neg h, if_neg h']
    rcases lt_or_gt_of_ne h with hlt | hlt
    · have : ¬ y < x := not_lt.mpr hlt.le
      cases dir <;> simp [this, hlt]
    · have : ¬ x < y := not_lt.mpr hlt.le
      cases dir <;> simp [this, hlt]

/-- A comparative and its opposite never name the same row of two distinct
rows. -/
public theorem winner_flip_ne {α : Type*} (dir : Bool) {a b : α} (hab : a ≠ b)
    {x y : ℚ} (hxy : x ≠ y) : winner (!dir) a b x y ≠ winner dir a b x y := by
  unfold winner
  rw [if_neg hxy, if_neg hxy]
  cases dir <;> by_cases h : y < x <;> simp [h, hab, hab.symm]

/-- No row is named exactly when the two values are equal. -/
public theorem winner_eq_none_iff {α : Type*} (dir : Bool) (a b : α) (x y : ℚ) :
    winner dir a b x y = none ↔ x = y := by
  unfold winner
  by_cases h : x = y
  · simp [h]
  · rw [if_neg h]; split_ifs <;> simp [h]

/-! ## A fold over a partition -/

/-- The sum over the whole column is the sum over the classes of the sums over
each class. -/
public theorem fold_sum_partition {α β : Type*} [DecidableEq β] (s : Finset α)
    (cls : α → β) (f : α → ℚ) :
    ∑ b ∈ s.image cls, ∑ a ∈ s.filter (fun a => cls a = b), f a =
      ∑ a ∈ s, f a :=
  Finset.sum_fiberwise_of_maps_to (fun _ ha => Finset.mem_image_of_mem cls ha) f

/-! ## Parity counts -/

/-- A sum of integers is even exactly when an even number of its terms is
odd. -/
public theorem even_sum_iff_even_odd_count {α : Type*} (s : Finset α)
    (f : α → ℤ) :
    Even (∑ a ∈ s, f a) ↔ Even (s.filter (fun a => Odd (f a))).card := by
  classical
  induction s using Finset.induction_on with
  | empty => simp
  | insert j s hj ih =>
      rw [Finset.sum_insert hj, Finset.filter_insert]
      by_cases hodd : Odd (f j)
      · rw [if_pos hodd, Finset.card_insert_of_notMem
          (fun h => hj (Finset.mem_filter.mp h).1)]
        rw [Int.even_add, Nat.even_add_one, ih]
        constructor
        · intro h1 h2; exact (Int.not_even_iff_odd.mpr hodd) (h1.mpr h2)
        · intro h1
          constructor
          · intro h2; exact absurd h2 (Int.not_even_iff_odd.mpr hodd)
          · intro h2; exact absurd h2 h1
      · rw [if_neg hodd, Int.even_add, ih]
        have he : Even (f j) := Int.not_odd_iff_even.mp hodd
        constructor
        · intro h; exact h.mp he
        · intro h; exact ⟨fun _ => h, fun _ => he⟩

/-- The odd count and the even count together are the size of the column. -/
public theorem odd_count_add_even_count {α : Type*} (s : Finset α)
    (f : α → ℤ) :
    (s.filter (fun a => Odd (f a))).card +
      (s.filter (fun a => ¬ Odd (f a))).card = s.card :=
  Finset.card_filter_add_card_filter_not _

/-! ## The hole -/

/-- With one reading `v` missing from a nonempty column `l`, the mean over the
present rows is the column's mean exactly when the missing reading equals
it. -/
public theorem mean_cons_eq_iff {l : List ℚ} (hne : l ≠ []) (v : ℚ) :
    mean (v :: l) = mean l ↔ v = mean l := by
  unfold mean
  have hlen : (0 : ℚ) < l.length := by exact_mod_cast List.length_pos_iff.mpr hne
  simp only [List.sum_cons, List.length_cons, Nat.cast_add, Nat.cast_one]
  rw [div_eq_div_iff (by positivity) hlen.ne', eq_div_iff hlen.ne']
  constructor <;> intro h <;> linarith

/-- Distinct missing readings give distinct means: the column's mean is not
determined by the rows that are present. -/
public theorem hole_mean_injective (l : List ℚ) {v w : ℚ} (h : v ≠ w) :
    mean (v :: l) ≠ mean (w :: l) := by
  unfold mean
  intro e
  have hlen : (0 : ℚ) < ((v :: l).length : ℚ) := by
    exact_mod_cast List.length_pos_iff.mpr (List.cons_ne_nil v l)
  simp only [List.sum_cons, List.length_cons] at e hlen
  rw [div_left_inj' hlen.ne'] at e
  exact h (by linarith)

end GLM.StepwiseWiden
