/-
# Cumulative layers: how a stack is made into a refinement chain

`Layers.lean` says what a refinement is; `Stack.lean` instantiates the GLM
stack on an idealised carrier space where each layer's view happens to be a
function of the one above it.  The GLM's *real* layers are not built that way.
The substrate reads a parity bit off each of 24 coordinates; the integer layer
reads seven SI exponents off coordinates 0–6.  Neither view is a function of
the other, and the consequence is exactly what
`glm_universal/reasoning/information_loss.py` measured on real carriers: a unit
on coordinate 10 is separated from the vacuum by the substrate and conflated by
a reading that takes only the exponents.  Escalating one layer *lost* a
distinction the layer below already had, and the ladder had a hole in it.

This file is the fix, stated and proved in general.

* `Layer.cumulative L M` is the layer that sees `L`'s view **and** `M`'s view.
* It refines both (`cumulative_refines_left`, `cumulative_refines_right`), and
  it is the **coarsest** layer that does (`refines_cumulative_iff`,
  `cumulative_least`): keeping the lower reading costs nothing beyond what
  keeping it requires.
* What it adds over the layer below is exactly what the new reading adds
  (`boundary_cumulative_left`), so making a step cumulative repairs the hole
  without inventing resolution.
* A stack of cumulative layers is a refinement chain by construction
  (`cumulativeTower_refines_of_le`), which is the property the code now has.

The concrete model at the end is the GLM's own situation in miniature: two
coordinates, one inside the exponent window and one outside.  `si7Model` reads
the first coordinate only and is proved **not** to refine the substrate --
the hole, as a theorem, on the same witness pair the Python report prints --
while `integerModel`, the cumulative layer that keeps both readings, refines it
and still gains strictly over it.

The counterpart in code is `dimension_layers.LAYER_INTEGER` (cumulative, in the
stack) beside `dimension_layers.LAYER_INTEGER_RAW` (the discarded reading, kept
so the hole can be exhibited), and the `refinement_chain_intact` field of
`information_loss.information_loss_report`.
-/
import RequestProject.GLM.Layers

namespace GLM.Info

namespace Layer

universe u v

variable {C : Type u} {L M N L' : Layer.{u, v} C} {a b : C}

/-! ## The cumulative layer -/

/-- The layer that sees both readings: escalating from `L` to `cumulative L M`
adds `M`'s view to `L`'s instead of trading one for the other. -/
def cumulative (L M : Layer.{u, v} C) : Layer.{u, v} C where
  View := L.View × M.View
  perceive c := (L.perceive c, M.perceive c)

@[simp] theorem cumulative_perceive (L M : Layer.{u, v} C) (c : C) :
    (cumulative L M).perceive c = (L.perceive c, M.perceive c) := rfl

/-- Two carriers are the same to a cumulative layer exactly when both readings
agree.  This is the `measure` of the code: a sum of non-negative terms, zero
only when each is. -/
theorem cumulative_indist_iff :
    (cumulative L M).Indist a b ↔ L.Indist a b ∧ M.Indist a b := by
  constructor
  · intro h
    exact ⟨congrArg Prod.fst h, congrArg Prod.snd h⟩
  · rintro ⟨h₁, h₂⟩
    exact Prod.ext h₁ h₂

/-- **Nothing below is given up.**  A cumulative layer refines the layer whose
view it keeps. -/
theorem cumulative_refines_left (L M : Layer.{u, v} C) :
    Refines (cumulative L M) L := fun _ _ h => (cumulative_indist_iff.1 h).1

/-- A cumulative layer also refines the reading it adds. -/
theorem cumulative_refines_right (L M : Layer.{u, v} C) :
    Refines (cumulative L M) M := fun _ _ h => (cumulative_indist_iff.1 h).2

/-- **The universal property.**  Refining the cumulative layer is exactly
refining both of its parts. -/
theorem refines_cumulative_iff :
    Refines N (cumulative L M) ↔ Refines N L ∧ Refines N M := by
  constructor
  · intro h
    exact ⟨fun a b hab => (cumulative_indist_iff.1 (h a b hab)).1,
      fun a b hab => (cumulative_indist_iff.1 (h a b hab)).2⟩
  · rintro ⟨h₁, h₂⟩ a b hab
    exact cumulative_indist_iff.2 ⟨h₁ a b hab, h₂ a b hab⟩

/-- **The cumulative layer is the least one that keeps both readings**: any
layer refining `L` and `M` refines it, so cumulating adds no resolution beyond
what keeping the two views forces. -/
theorem cumulative_least (h₁ : Refines N L) (h₂ : Refines N M) :
    Refines N (cumulative L M) := refines_cumulative_iff.2 ⟨h₁, h₂⟩

/-- Cumulating with a layer one already refines changes nothing. -/
theorem cumulative_indist_eq_left (h : Refines L M) :
    (cumulative L M).Indist a b ↔ L.Indist a b := by
  rw [cumulative_indist_iff]
  exact ⟨And.left, fun hab => ⟨hab, h a b hab⟩⟩

/-- **What cumulating gains is exactly what the added reading sees.**  The
boundary between the layer below and the cumulative layer is the set of pairs
`L` conflates and `M` splits: repairing the ladder invents no resolution. -/
theorem boundary_cumulative_left (L M : Layer.{u, v} C) :
    Boundary (cumulative L M) L = {p | L.Indist p.1 p.2 ∧ ¬ M.Indist p.1 p.2} := by
  ext ⟨a, b⟩
  simp only [Boundary, Set.mem_setOf_eq, cumulative_indist_iff, not_and]
  constructor
  · rintro ⟨h, h'⟩
    exact ⟨h, h' h⟩
  · rintro ⟨h, h'⟩
    exact ⟨h, fun _ => h'⟩

/-- A cumulative layer is lossless as soon as either part is. -/
theorem cumulative_lossless_left (h : L.Lossless) (M : Layer.{u, v} C) :
    (cumulative L M).Lossless := fun _ _ hab =>
  h (cumulative_indist_iff.1 hab).1

/-! ## A tower built by cumulating is a refinement chain

This is the shape the code now has: `layer (n+1)` sees everything `layer n` saw
plus one new reading, so no step can cost anything. -/

/-- The tower obtained by cumulating a family of readings: step `n` sees the
base and every reading up to `n`. -/
def cumulativeTower (base : Layer.{u, v} C) (read : ℕ → Layer.{u, v} C) :
    ℕ → Layer.{u, v} C
  | 0 => base
  | n + 1 => cumulative (cumulativeTower base read n) (read n)

@[simp] theorem cumulativeTower_zero (base : Layer.{u, v} C)
    (read : ℕ → Layer.{u, v} C) : cumulativeTower base read 0 = base := rfl

@[simp] theorem cumulativeTower_succ (base : Layer.{u, v} C)
    (read : ℕ → Layer.{u, v} C) (n : ℕ) :
    cumulativeTower base read (n + 1) =
      cumulative (cumulativeTower base read n) (read n) := rfl

/-- Each step of a cumulative tower refines the one below it. -/
theorem cumulativeTower_refines_succ (base : Layer.{u, v} C)
    (read : ℕ → Layer.{u, v} C) (n : ℕ) :
    Refines (cumulativeTower base read (n + 1)) (cumulativeTower base read n) :=
  cumulative_refines_left _ _

/-- **A cumulative tower is a refinement chain**: every layer sees at least as
much as every layer below it, so escalating never costs anything. -/
theorem cumulativeTower_refines_of_le (base : Layer.{u, v} C)
    (read : ℕ → Layer.{u, v} C) {m n : ℕ} (h : m ≤ n) :
    Refines (cumulativeTower base read n) (cumulativeTower base read m) := by
  induction n with
  | zero =>
      obtain rfl : m = 0 := Nat.le_zero.1 h
      exact refines_refl _
  | succ n ih =>
      rcases Nat.lt_succ_iff_lt_or_eq.1 (Nat.lt_succ_of_le h) with hlt | rfl
      · exact (cumulativeTower_refines_succ base read n).trans
          (ih (Nat.lt_succ_iff.1 hlt))
      · exact refines_refl _

end Layer

/-! ## The GLM's own situation, in miniature

A carrier is two rational coordinates: `c.1` inside the seven-exponent window
the integer layer reads, `c.2` outside it (coordinate 10 in the real system).
The substrate reads a parity bit off *both*; the SI7 reading takes the integer
part of the first *only*. -/

open Layer

/-- The substrate: a parity bit off each coordinate.  This is
`_substrate_perceive` restricted to two coordinates. -/
def substrateModel : Layer (ℚ × ℚ) where
  View := ZMod 2 × ZMod 2
  perceive c := ((⌊c.1⌋ : ZMod 2), (⌊c.2⌋ : ZMod 2))

/-- The non-cumulative integer reading: the exponent on the first coordinate,
and nothing else.  This is `LAYER_INTEGER_RAW` -- `_integer_raw_perceive`. -/
def si7Model : Layer (ℚ × ℚ) where
  View := ℤ × ℤ
  perceive c := (⌊c.1⌋, 0)

/-- The integer layer as the code now has it: the SI7 reading carried *on top
of* the substrate's.  This is `LAYER_INTEGER` -- `_integer_perceive`, whose
view holds `substrate_bits` beside `exponents_SI7`. -/
def integerModel : Layer (ℚ × ℚ) := cumulative substrateModel si7Model

@[simp] lemma substrateModel_perceive (c : ℚ × ℚ) :
    substrateModel.perceive c = ((⌊c.1⌋ : ZMod 2), (⌊c.2⌋ : ZMod 2)) := rfl

@[simp] lemma si7Model_perceive (c : ℚ × ℚ) :
    si7Model.perceive c = (⌊c.1⌋, 0) := rfl

/-- The witness pair: the vacuum, and a unit on the coordinate outside the
exponent window.  These are carriers 0 and 4 of `information_loss.sample_carriers`. -/
private lemma vacuum_far_substrate_distinct :
    ¬ substrateModel.Indist (0, 0) (0, 1) := by
  intro h
  have h2 : ((⌊(0 : ℚ)⌋ : ZMod 2)) = ((⌊(1 : ℚ)⌋ : ZMod 2)) := congrArg Prod.snd h
  simp at h2

private lemma vacuum_far_si7_same : si7Model.Indist ((0 : ℚ), (0 : ℚ)) (0, 1) := rfl

/-- **The hole, as a theorem.**  The reading that takes only the exponents does
*not* refine the substrate: it calls the vacuum and a unit on the outside
coordinate the same thing, while the substrate below it tells them apart.  A
stack whose first step is this reading loses information by escalating -- which
is what the report measured on the real 24-coordinate carriers. -/
theorem si7Model_not_refines_substrateModel : ¬ Refines si7Model substrateModel := by
  intro h
  exact vacuum_far_substrate_distinct (h _ _ vacuum_far_si7_same)

/-- **The fix.**  The cumulative integer layer refines the substrate. -/
theorem integerModel_refines_substrateModel : Refines integerModel substrateModel :=
  cumulative_refines_left _ _

/-- It also refines the reading it added, so nothing the SI7 view could say is
given up either. -/
theorem integerModel_refines_si7Model : Refines integerModel si7Model :=
  cumulative_refines_right _ _

/-- And it is the coarsest layer that does both: cumulating repairs the ladder
without inventing resolution. -/
theorem integerModel_least {N : Layer.{0, 0} (ℚ × ℚ)}
    (h₁ : Refines N substrateModel) (h₂ : Refines N si7Model) :
    Refines N integerModel := cumulative_least h₁ h₂

/-- The repair is genuine: the pair the raw reading got wrong is split by the
cumulative layer. -/
theorem integerModel_separates_witness :
    ¬ integerModel.Indist ((0 : ℚ), (0 : ℚ)) (0, 1) := by
  intro h
  exact vacuum_far_substrate_distinct (integerModel_refines_substrateModel _ _ h)

/-- Cumulating does not flatten the stack either: the integer layer still gains
strictly over the substrate, on a pair of equal parity and different exponent. -/
theorem boundary_integerModel_substrateModel_nonempty :
    (Boundary integerModel substrateModel).Nonempty := by
  refine ⟨(((0 : ℚ), (0 : ℚ)), ((2 : ℚ), (0 : ℚ))), ?_, ?_⟩
  · show substrateModel.perceive _ = substrateModel.perceive _
    simp [substrateModel]
    decide
  · intro h
    have h1 : (⌊(0 : ℚ)⌋, (0 : ℤ)) = (⌊(2 : ℚ)⌋, (0 : ℤ)) :=
      integerModel_refines_si7Model _ _ h
    have h2 := congrArg Prod.fst h1
    simp at h2

end GLM.Info
