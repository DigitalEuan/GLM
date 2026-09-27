/-
# The cumulativity rule, and the failure mode it does *not* repair

`Cumulative.lean` proves what a cumulative layer is and that a tower of them is
a refinement chain.  This file states the standing rule the project now works
under, and — more usefully — separates the two failure modes that look alike
and have different remedies.  The checked instrument is
`overlay/glm_universal/reasoning/cumulativity.py`.

**A refinement violation** is a pair the lower layer separates and the higher
one conflates.  It is a defect of construction, and `Cumulative.lean`'s
`cumulative_refines_left` is the remedy: carry the lower reading alongside the
new one.

**A conflation** is a pair one layer cannot see apart at all.  It is not a
defect; it is the layer's resolution.  The distinction matters because the two
have *different* repairs, and this file proves why:

* `factored_conflates` — anything computed from a layer's view conflates
  whatever that layer conflates.  So refining a reading *of that layer's
  output* can never repair its conflation, however much machinery is added.
* `join_separates` — a join with a layer that does see the pair repairs it, and
  `join_needs_a_second_reading` shows the join is the only route: the repair
  must read the carrier again, not read the view again.

That is the deep-hole ladder's `A_1^24` / `A_2^12` conflation in general form.
The rational reading gives both holes a single-atom distance measure, so no
refinement *of that reading* separates them; the pair is separated by joining
it to a reading that sees something else, which is what the joint rung does.
-/
import RequestProject.GLM.Cumulative

namespace GLM.Info

namespace Layer

universe u v

variable {C : Type u}

/-! ## A reading of a view is not a finer reading of the carrier -/

/-- The layer that reads `L`'s view through `f`: everything it knows, it knows
from `L`. -/
def factor (L : Layer.{u, v} C) {W : Type v} (f : L.View → W) :
    Layer.{u, v} C where
  View := W
  perceive c := f (L.perceive c)

@[simp] theorem factor_perceive (L : Layer.{u, v} C) {W : Type v}
    (f : L.View → W) (c : C) : (factor L f).perceive c = f (L.perceive c) :=
  rfl

/-- **A conflation is not repaired by reading the view again.**  Whatever `L`
cannot tell apart, no function of `L`'s view can tell apart either. -/
theorem factored_conflates (L : Layer.{u, v} C) {W : Type v} (f : L.View → W)
    {a b : C} (h : L.Indist a b) : (factor L f).Indist a b := by
  show f (L.perceive a) = f (L.perceive b)
  rw [h]

/-- The same fact as a refinement statement: a reading of a view is coarser
than the view, never finer. -/
theorem factor_refined_by (L : Layer.{u, v} C) {W : Type v} (f : L.View → W) :
    Refines L (factor L f) := fun _ _ h => factored_conflates L f h

/-- **A join repairs a conflation, when the joined layer sees the pair.**  This
is the other half: the repair exists, and it comes from reading the carrier
again rather than from reading the view again. -/
theorem join_separates (L M : Layer.{u, v} C) {a b : C}
    (hM : ¬ M.Indist a b) : ¬ (cumulative L M).Indist a b := by
  intro h
  exact hM ((cumulative_indist_iff (L := L) (M := M)).1 h).2

/-- And the join is the *only* route: if the second reading conflates the pair
too, so does the join.  A pair separated by nothing available is separated by
no join of the things available. -/
theorem join_needs_a_second_reading (L M : Layer.{u, v} C) {a b : C}
    (hL : L.Indist a b) (hM : M.Indist a b) : (cumulative L M).Indist a b :=
  (cumulative_indist_iff (L := L) (M := M)).2 ⟨hL, hM⟩

/-! ## The rule -/

/-- A family of layers, indexed by the order they are declared in, together
with the claim that each refines the one below.  `Cumulative.lean` builds such
families; this predicate is what the shipped check tests. -/
def RefinementChain (read : ℕ → Layer.{u, v} C) : Prop :=
  ∀ n, Refines (read (n + 1)) (read n)

/-- A refinement chain refines across any gap, not only between neighbours:
the property the check tests pairwise is the property the stack needs. -/
theorem refines_of_le {read : ℕ → Layer.{u, v} C} (h : RefinementChain read)
    {m n : ℕ} (hmn : m ≤ n) : Refines (read n) (read m) := by
  induction n with
  | zero =>
      have : m = 0 := Nat.le_zero.1 hmn
      subst this
      exact refines_refl _
  | succ k ih =>
      rcases Nat.lt_succ_iff_lt_or_eq.1 (Nat.lt_succ_of_le hmn) with hlt | heq
      · exact Refines.trans (h k) (ih (Nat.lt_succ_iff.1 hlt))
      · subst heq
        exact refines_refl _

/-- **A cumulative construction satisfies the rule by construction**, which is
why the rule is cheap to obey: a new layer that carries the one below it cannot
violate the chain. -/
theorem refinementChain_cumulativeTower (base : Layer.{u, v} C)
    (read : ℕ → Layer.{u, v} C) :
    RefinementChain (cumulativeTower base read) := by
  intro n
  exact cumulativeTower_refines_succ base read n

end Layer

end GLM.Info
