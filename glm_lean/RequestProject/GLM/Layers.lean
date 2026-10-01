/-
# Information loss at layer boundaries

This is the abstract half of the "information loss at boundaries" study.  It
makes precise the GLM's layered-projection thesis:

> each layer is both true from its limited perspective and works to that degree
> of implementation, then becomes untrue when the next dimension layer is
> required to take over.

The model.  A **layer** is a resolution: a map `perceive : C → View` from
carriers to whatever that layer can see.  Everything else is derived from it.

* Two carriers are **indistinguishable** at a layer when they have the same view.
* A layer `L'` **refines** `L` when it distinguishes at least as much.
* A property of carriers is **visible** at a layer when the layer's own
  indistinguishability cannot separate a carrier satisfying it from one that
  does not.  Visible properties are exactly the layer's expressible truths.
* The **boundary** between `L` and a finer `L'` is the set of pairs that `L`
  conflates and `L'` splits.  That set *is* the information lost at `L`.
* An operation **descends** to a layer exactly when the layer's kernel is a
  congruence for it — this is the precise content of the GLM's `can_multiply`
  flag, and the precise sense in which a law can hold on one region of carriers
  and fail on a larger one.
* The **capacity** of a layer is the number of views it has; capacity below the
  size of the carrier space forces loss (pigeonhole), and refinement increases
  the number of classes a layer resolves.

`Stack.lean` instantiates all of this on the concrete GLM layer stack.
-/
import Mathlib

namespace GLM.Info

universe u v

/-- A layer of the GLM: a resolution at which carriers are perceived. -/
structure Layer (C : Type u) where
  /-- What this layer sees. -/
  View : Type v
  /-- How a carrier is projected into the layer's coordinate space. -/
  perceive : C → View

namespace Layer

variable {C : Type u} {L L' L'' : Layer C} {a b c : C}

/-- Two carriers are indistinguishable at a layer when their views agree. -/
def Indist (L : Layer C) (a b : C) : Prop := L.perceive a = L.perceive b

@[refl] theorem indist_refl (L : Layer C) (a : C) : L.Indist a a := rfl

@[symm] theorem indist_symm (h : L.Indist a b) : L.Indist b a := Eq.symm h

theorem indist_trans (h : L.Indist a b) (h' : L.Indist b c) : L.Indist a c := Eq.trans h h'

/-- Indistinguishability at a layer is an equivalence relation: the layer's kernel. -/
def setoid (L : Layer C) : Setoid C where
  r := L.Indist
  iseqv := ⟨indist_refl L, indist_symm, indist_trans⟩

/-- A layer is *lossless* when it distinguishes every pair of distinct carriers. -/
def Lossless (L : Layer C) : Prop := Function.Injective L.perceive

theorem lossless_iff (L : Layer C) : L.Lossless ↔ ∀ a b, L.Indist a b → a = b := Iff.rfl

/-! ## Refinement -/

/-- `L'` refines `L`: whatever `L'` calls the same, `L` calls the same too, so
`L'` sees at least as much as `L`. -/
def Refines (L' L : Layer C) : Prop := ∀ a b, L'.Indist a b → L.Indist a b

@[refl] theorem refines_refl (L : Layer C) : Refines L L := fun _ _ h => h

theorem Refines.trans (h : Refines L'' L') (h' : Refines L' L) : Refines L'' L :=
  fun a b hab => h' a b (h a b hab)

/-- A lossless layer refines every layer: nothing is above the finest resolution. -/
theorem Refines.of_lossless (h : L'.Lossless) (L : Layer C) : Refines L' L := by
  intro a b hab
  rw [h hab]

/-! ## Visible properties: what is true *at* a layer -/

/-- A property of carriers is visible at a layer when the layer has enough
resolution to state it: it never separates two carriers the layer conflates. -/
def Visible (L : Layer C) (P : C → Prop) : Prop := ∀ a b, L.Indist a b → (P a ↔ P b)

/-- **Truths survive upward.**  Anything expressible at a layer is expressible at
every finer layer. -/
theorem Visible.mono (h : Refines L' L) {P : C → Prop} (hP : Visible L P) : Visible L' P :=
  fun a b hab => hP a b (h a b hab)

/-- Every property is visible at a lossless layer. -/
theorem visible_of_lossless (h : L.Lossless) (P : C → Prop) : Visible L P := by
  intro a b hab
  rw [h hab]

/-- The properties visible at `L` are exactly those that factor through the view. -/
theorem visible_iff_factors {P : C → Prop} :
    Visible L P ↔ ∃ p : L.View → Prop, ∀ a, P a ↔ p (L.perceive a) := by
  classical
  constructor
  · intro h
    refine ⟨fun w => ∃ a, L.perceive a = w ∧ P a, fun a => ⟨fun ha => ⟨a, rfl, ha⟩, ?_⟩⟩
    rintro ⟨b, hb, hPb⟩
    exact (h a b (indist_symm hb)).2 hPb
  · rintro ⟨p, hp⟩ a b hab
    rw [hp a, hp b, show L.perceive a = L.perceive b from hab]

/-! ## The boundary: the information a layer loses -/

/-- The boundary between a layer and a finer one: the pairs the lower layer
conflates and the higher layer splits.  This set *is* the information lost. -/
def Boundary (L' L : Layer C) : Set (C × C) :=
  {p | L.Indist p.1 p.2 ∧ ¬ L'.Indist p.1 p.2}

theorem mem_boundary {a b : C} :
    (a, b) ∈ Boundary L' L ↔ L.Indist a b ∧ ¬ L'.Indist a b := Iff.rfl

/-- No boundary means no loss: the two layers have the same kernel. -/
theorem boundary_eq_empty_iff (h : Refines L' L) :
    Boundary L' L = ∅ ↔ ∀ a b, L.Indist a b ↔ L'.Indist a b := by
  constructor
  · intro hb a b
    refine ⟨fun hab => ?_, fun hab => h a b hab⟩
    by_contra hc
    have hmem : (a, b) ∈ Boundary L' L := ⟨hab, hc⟩
    rw [hb] at hmem
    exact hmem
  · intro hiff
    ext ⟨a, b⟩
    simp only [Boundary, Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false, not_and, not_not]
    intro hab
    exact (hiff a b).1 hab

/-- A pair on the boundary is exactly a pair about which the lower layer's verdict
("these are the same") is true at its own resolution and false one layer up.
This is the formal content of "true up to a point, then untrue". -/
theorem boundary_verdict {a b : C} (hab : (a, b) ∈ Boundary L' L) :
    L.Indist a b ∧ ¬ L'.Indist a b := hab

/-- Nothing is lost above a lossless layer: once a layer resolves every carrier,
higher layers can add structure but no further resolution. -/
theorem boundary_eq_empty_of_lossless (h : L.Lossless) (L' : Layer C) :
    Boundary L' L = ∅ := by
  ext ⟨a, b⟩
  simp only [Boundary, Set.mem_setOf_eq, Set.mem_empty_iff_false, iff_false, not_and, not_not]
  intro hab
  rw [h hab]

/-- **A boundary exists iff the higher layer can express something the lower one
cannot.**  Information lost at a boundary is exactly new expressive power. -/
theorem boundary_nonempty_iff_new_visible (h : Refines L' L) :
    (Boundary L' L).Nonempty ↔ ∃ P : C → Prop, Visible L' P ∧ ¬ Visible L P := by
  constructor
  · rintro ⟨⟨a, b⟩, hab, hab'⟩
    refine ⟨fun x => L'.Indist a x, fun x y hxy => ?_, ?_⟩
    · exact ⟨fun hx => indist_trans hx hxy, fun hy => indist_trans hy (indist_symm hxy)⟩
    · intro hvis
      exact hab' ((hvis a b hab).1 (indist_refl L' a))
  · rintro ⟨P, hP', hP⟩
    by_contra hempty
    rw [Set.not_nonempty_iff_eq_empty] at hempty
    exact hP (fun a b hab => hP' a b ((boundary_eq_empty_iff h).1 hempty a b |>.1 hab))

/-! ## Descent of operations: the precise meaning of `can_multiply` -/

/-- An operation is *congruent* for a layer on a region `S` when the layer's
resolution is enough to determine the result: replacing the operands by
carriers the layer cannot tell apart does not change what the layer sees of the
result. -/
def CongruentOn (L : Layer C) (S : Set C) (op : C → C → C) : Prop :=
  ∀ a b a' b', a ∈ S → b ∈ S → a' ∈ S → b' ∈ S →
    L.Indist a a' → L.Indist b b' → L.Indist (op a b) (op a' b')

/-- **The reach of a law shrinks, never grows.**  If an operation is computable at
a layer's resolution on a region, it is computable on every smaller region — the
formal statement of "a layer works to its degree of implementation". -/
theorem CongruentOn.mono {S T : Set C} {op : C → C → C} (hST : S ⊆ T)
    (h : CongruentOn L T op) : CongruentOn L S op :=
  fun a b a' b' ha hb ha' hb' => h a b a' b' (hST ha) (hST hb) (hST ha') (hST hb')

/-- **An operation descends to a layer exactly when the layer is congruent for it.**
Descent means the layer can carry out the operation entirely in its own view
space; this is what the GLM's `can_multiply` flag asserts. -/
theorem descends_iff_congruent [Nonempty C] (op : C → C → C) :
    (∃ f : L.View → L.View → L.View,
        ∀ a b, L.perceive (op a b) = f (L.perceive a) (L.perceive b))
      ↔ CongruentOn L Set.univ op := by
  classical
  constructor
  · rintro ⟨f, hf⟩ a b a' b' - - - - haa hbb
    show L.perceive (op a b) = L.perceive (op a' b')
    rw [hf, hf, show L.perceive a = L.perceive a' from haa,
      show L.perceive b = L.perceive b' from hbb]
  · intro h
    refine ⟨fun u w => L.perceive
      (op (Function.invFun L.perceive u) (Function.invFun L.perceive w)), fun a b => ?_⟩
    have ha : L.perceive (Function.invFun L.perceive (L.perceive a)) = L.perceive a :=
      Function.invFun_eq ⟨a, rfl⟩
    have hb : L.perceive (Function.invFun L.perceive (L.perceive b)) = L.perceive b :=
      Function.invFun_eq ⟨b, rfl⟩
    exact h a b _ _ trivial trivial trivial trivial ha.symm hb.symm

/-! ## Capacity: the dimension count that forces loss -/

/-- The capacity of a layer: the number of distinct views it can hold. -/
noncomputable def capacity (L : Layer C) [Fintype L.View] : ℕ := Fintype.card L.View

/-- **Capacity forces loss.**  A layer whose capacity is smaller than the number of
carriers must conflate two distinct carriers. -/
theorem exists_indist_of_capacity_lt [Fintype C] [Fintype L.View]
    (h : capacity L < Fintype.card C) : ∃ a b : C, a ≠ b ∧ L.Indist a b := by
  obtain ⟨a, b, hab, h'⟩ := Fintype.exists_ne_map_eq_of_card_lt L.perceive h
  exact ⟨a, b, hab, h'⟩

/-- A lossless layer has capacity at least the size of the carrier space. -/
theorem card_le_capacity_of_lossless [Fintype C] [Fintype L.View] (h : L.Lossless) :
    Fintype.card C ≤ capacity L := Fintype.card_le_of_injective _ h

/-! ## Resolution on a finite region, and the loss count -/

/-- How many distinct things a layer resolves on a finite region of carriers. -/
def resolution (L : Layer C) [DecidableEq L.View] (S : Finset C) : ℕ :=
  (S.image L.perceive).card

/-- How much a layer loses on a finite region: the number of carriers there
minus the number of things the layer can tell apart. -/
def lossCount (L : Layer C) [DecidableEq L.View] (S : Finset C) : ℕ :=
  S.card - resolution L S

theorem resolution_le_card (L : Layer C) [DecidableEq L.View] (S : Finset C) :
    resolution L S ≤ S.card := Finset.card_image_le

/-- **Resolution increases up the stack.**  A finer layer resolves at least as
many classes on every region. -/
theorem resolution_mono [DecidableEq L.View] [DecidableEq L'.View]
    (h : Refines L' L) (S : Finset C) :
    resolution L S ≤ resolution L' S := by
  classical
  rcases S.eq_empty_or_nonempty with rfl | ⟨a₀, ha₀⟩
  · simp [resolution]
  · have hne : Nonempty L.View := ⟨L.perceive a₀⟩
    -- the lower view factors through the higher view on `S`
    set g : L'.View → L.View := fun w =>
      if hw : ∃ x ∈ S, L'.perceive x = w then L.perceive hw.choose else L.perceive a₀ with hg
    have hfactor : S.image L.perceive = (S.image L'.perceive).image g := by
      ext u
      simp only [Finset.mem_image, Finset.image_image, Function.comp_apply]
      constructor
      · rintro ⟨x, hx, rfl⟩
        refine ⟨x, hx, ?_⟩
        have hw : ∃ y ∈ S, L'.perceive y = L'.perceive x := ⟨x, hx, rfl⟩
        have hspec := hw.choose_spec
        simp only [hg, dif_pos hw]
        exact Eq.symm (h x hw.choose (Eq.symm hspec.2))
      · rintro ⟨x, hx, rfl⟩
        have hw : ∃ y ∈ S, L'.perceive y = L'.perceive x := ⟨x, hx, rfl⟩
        have hspec := hw.choose_spec
        refine ⟨hw.choose, hspec.1, ?_⟩
        simp only [hg, dif_pos hw]
    unfold resolution
    rw [hfactor]
    exact Finset.card_image_le

/-- **Loss decreases up the stack.** -/
theorem lossCount_anti [DecidableEq L.View] [DecidableEq L'.View]
    (h : Refines L' L) (S : Finset C) :
    lossCount L' S ≤ lossCount L S := by
  have := resolution_mono h S
  unfold lossCount
  omega

/-- A layer loses nothing on a region iff it resolves every carrier there. -/
theorem lossCount_eq_zero_iff (L : Layer C) [DecidableEq L.View] (S : Finset C) :
    lossCount L S = 0 ↔ resolution L S = S.card := by
  have := resolution_le_card L S
  unfold lossCount
  omega

end Layer

/-! ## Stacks and escalation -/

open Layer

/-- A stack of layers, ordered lowest to highest, each refining the ones below. -/
structure Stack (C : Type u) where
  /-- The number of steps above the bottom layer. -/
  steps : ℕ
  /-- The layers, in order. -/
  layer : Fin (steps + 1) → Layer C
  /-- Every higher layer refines every lower one. -/
  refines : ∀ i j : Fin (steps + 1), i ≤ j → Refines (layer j) (layer i)

namespace Stack

variable {C : Type u} (S : Stack C)

/-- A layer separates a pair when it can tell the two carriers apart. -/
def Separates (S : Stack C) (i : Fin (S.steps + 1)) (a b : C) : Prop :=
  ¬ (S.layer i).Indist a b

/-- Once a layer separates a pair, so does every layer above it. -/
theorem separates_up {i j : Fin (S.steps + 1)} (hij : i ≤ j) {a b : C}
    (h : S.Separates i a b) : S.Separates j a b :=
  fun hj => h (S.refines i j hij a b hj)

open Classical in
/-- The set of layers of the stack that separate a given pair. -/
noncomputable def separating (a b : C) : Finset (Fin (S.steps + 1)) :=
  {i | S.Separates i a b}

open Classical in
/-- **Escalation.**  The least layer of the stack that can tell the pair apart,
if there is one.  This is the GLM's `escalate`: start at the bottom and climb
until a layer's reach suffices. -/
noncomputable def escalate (a b : C) : Option (Fin (S.steps + 1)) :=
  if h : (S.separating a b).Nonempty then some ((S.separating a b).min' h) else none

open Classical in
theorem mem_separating {i : Fin (S.steps + 1)} {a b : C} :
    i ∈ S.separating a b ↔ S.Separates i a b := by
  simp [separating]

open Classical in
/-- Escalation returns nothing exactly when the whole stack conflates the pair. -/
theorem escalate_eq_none_iff {a b : C} :
    S.escalate a b = none ↔ ∀ i, (S.layer i).Indist a b := by
  unfold escalate
  split_ifs with h
  · simp only [false_iff, not_forall]
    obtain ⟨i, hi⟩ := h
    exact ⟨i, (S.mem_separating).1 hi⟩
  · rw [Finset.not_nonempty_iff_eq_empty] at h
    simp only [true_iff]
    intro i
    by_contra hc
    have : i ∈ S.separating a b := (S.mem_separating).2 hc
    rw [h] at this
    exact absurd this (Finset.notMem_empty i)

open Classical in
/-- The layer escalation stops at does separate the pair. -/
theorem escalate_separates {a b : C} {i : Fin (S.steps + 1)} (h : S.escalate a b = some i) :
    S.Separates i a b := by
  unfold escalate at h
  split_ifs at h with hne
  · rw [Option.some_inj] at h
    subst h
    exact (S.mem_separating).1 ((S.separating a b).min'_mem hne)

open Classical in
/-- **Escalation is minimal**: every layer strictly below the one it stops at is
blind to the difference.  The lower layers are true in their own range — they
simply cannot see this pair. -/
theorem escalate_minimal {a b : C} {i : Fin (S.steps + 1)} (h : S.escalate a b = some i)
    {j : Fin (S.steps + 1)} (hj : j < i) : (S.layer j).Indist a b := by
  unfold escalate at h
  split_ifs at h with hne
  · rw [Option.some_inj] at h
    subst h
    by_contra hc
    exact absurd ((S.separating a b).min'_le j ((S.mem_separating).2 hc)) (not_le.2 hj)

open Classical in
/-- The characterisation used to compute escalation: the least separating layer. -/
theorem escalate_eq_some_of {a b : C} {i : Fin (S.steps + 1)} (hi : S.Separates i a b)
    (hlt : ∀ j : Fin (S.steps + 1), j < i → ¬ S.Separates j a b) : S.escalate a b = some i := by
  have hmem : i ∈ S.separating a b := (S.mem_separating).2 hi
  have hne : (S.separating a b).Nonempty := ⟨i, hmem⟩
  unfold escalate
  rw [dif_pos hne, Option.some_inj]
  refine le_antisymm ((S.separating a b).min'_le i hmem) ?_
  by_contra hc
  push_neg at hc
  exact hlt _ hc ((S.mem_separating).1 ((S.separating a b).min'_mem hne))

/-- Above the escalation point, every layer still separates the pair. -/
theorem escalate_le_separates {a b : C} {i : Fin (S.steps + 1)} (h : S.escalate a b = some i)
    {j : Fin (S.steps + 1)} (hj : i ≤ j) : S.Separates j a b :=
  S.separates_up hj (S.escalate_separates h)

/-- The boundary crossed by escalation: the pair sits on the boundary between the
layer that stops it and every layer below. -/
theorem escalate_mem_boundary {a b : C} {i j : Fin (S.steps + 1)}
    (h : S.escalate a b = some i) (hj : j < i) :
    (a, b) ∈ Boundary (S.layer i) (S.layer j) :=
  ⟨S.escalate_minimal h hj, S.escalate_separates h⟩

end Stack

end GLM.Info
