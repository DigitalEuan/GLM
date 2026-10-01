/-
# Grounding: when is an encoding about the subject?

The formal counterpart of `overlay/glm_universal/semantics/reference.py`,
`relations.py` and `audit.py`, and the semantic half of the information-loss
study.

The question this file answers precisely is the one the project turns on:

> what does it take for a carrier, or a relation between carriers, to be
> *information about the subject* rather than information about the notation?

The answer is factorisation.  A map on notations is **semantic** exactly when
it factors through denotation -- when it is a function of what the notation
means and of nothing else (`semantic_iff_respects`).  Everything else follows:

* `spelling_not_semantic` -- an encoding that separates every notation cannot
  be semantic as soon as two notations denote the same thing.  This is the
  legacy carrier's problem in one line: `sha256` of a spelling is injective on
  spellings, so it is a measurement of the spelling.
* `legacy_threshold_dichotomy` -- and no threshold repairs it.  On the measured
  Hamming distances between the legacy carriers of `add`, `addition`, `plus`
  and `sum` (four notations for one operation), every radius below 15 splits a
  synonym pair, and every radius from 15 up relates all four to everything.
  There is no radius at which the legacy proximity relation is synonymy.
* `derived_relation_is_semantic` -- the positive counterpart: a relation
  *derived from* meanings is semantic by construction.  This is why the
  replacement graph's edges carry information and the old proximity edges did
  not.
* `notation_invariant_of_denote` -- the meaning carrier gives every notation
  for one subject the same 24 coordinates.

The second half instantiates `GLM.Info.Layer` on meanings, and locates a
boundary in the sense of the study: EXT10 dimensions refine the SI7
projection, and the pair `(energy, torque)` lies in the boundary -- true and
distinct at the EXT10 layer, conflated one layer down.
-/
import Mathlib
import RequestProject.GLM.Layers
import RequestProject.GLM.Semantics.Meaning

namespace GLM.Semantics

open GLM.Info

/-! ## Semantic maps -/

variable {N : Type*} {A : Type*} {M : Type*}

/-- A map on notations is **semantic** for a denotation when it factors
through it: the value depends on what the notation denotes and on nothing
else. -/
def IsSemantic (f : N → A) (denote : N → M) : Prop :=
  ∃ g : M → A, ∀ n, f n = g (denote n)

/-- Being semantic is exactly respecting synonymy. -/
theorem semantic_iff_respects [Nonempty A] (f : N → A) (denote : N → M) :
    IsSemantic f denote ↔ ∀ a b, denote a = denote b → f a = f b := by
  classical
  constructor
  · rintro ⟨g, hg⟩ a b hab
    rw [hg a, hg b, hab]
  · intro h
    refine ⟨fun m => if hm : ∃ n, denote n = m then f hm.choose else
      Classical.arbitrary A, fun n => ?_⟩
    have hn : ∃ k, denote k = denote n := ⟨n, rfl⟩
    show f n = if hm : ∃ k, denote k = denote n then f hm.choose else Classical.arbitrary A
    rw [dif_pos hn]
    exact h n hn.choose hn.choose_spec.symm

/-- **A spelling is not a meaning.**  An encoding that separates every
notation cannot be a function of meaning once two notations denote the same
subject.  Hashing a name is injective on names; that is precisely why it
carries no information about what the name is about. -/
theorem spelling_not_semantic {f : N → A} {denote : N → M}
    (hf : Function.Injective f) {a b : N} (hab : a ≠ b) (hd : denote a = denote b) :
    ¬ IsSemantic f denote := by
  haveI : Nonempty A := ⟨f a⟩
  intro h
  exact hab (hf ((semantic_iff_respects f denote).1 h a b hd))

/-- Anything computed from the meaning is semantic, by construction. -/
theorem semantic_of_comp (g : M → A) (denote : N → M) :
    IsSemantic (fun n => g (denote n)) denote := ⟨g, fun _ => rfl⟩

/-! ## Semantic relations -/

/-- A relation between notations is **semantic** when it is the pullback of a
relation between meanings. -/
def IsSemanticRel (R : N → N → Prop) (denote : N → M) : Prop :=
  ∃ S : M → M → Prop, ∀ a b, R a b ↔ S (denote a) (denote b)

/-- A semantic relation cannot separate synonyms. -/
theorem semanticRel_respects {R : N → N → Prop} {denote : N → M}
    (h : IsSemanticRel R denote) {a b c d : N}
    (hac : denote a = denote c) (hbd : denote b = denote d) : R a b ↔ R c d := by
  obtain ⟨S, hS⟩ := h
  rw [hS a b, hS c d, hac, hbd]

/-- **The split test.**  A relation that holds of one pair and fails of a
synonymous pair is not a relation between meanings, whatever it is called. -/
theorem not_semanticRel_of_split {R : N → N → Prop} {denote : N → M} {a b c d : N}
    (hac : denote a = denote c) (hbd : denote b = denote d)
    (hab : R a b) (hcd : ¬ R c d) : ¬ IsSemanticRel R denote := by
  intro h
  exact hcd ((semanticRel_respects h hac hbd).1 hab)

/-- **The positive counterpart.**  A relation *derived from* meanings -- the
kind the replacement graph carries -- is semantic by construction. -/
theorem derived_relation_is_semantic (S : M → M → Prop) (denote : N → M) :
    IsSemanticRel (fun a b => S (denote a) (denote b)) denote := ⟨S, fun _ _ => Iff.rfl⟩

/-! ## The measured witness: four notations for one operation

`add`, `addition`, `plus` and `sum` denote the same operation.  The legacy
carriers are `sha256` of the spelling, snapped to a Golay codeword; the
pairwise Hamming distances between them, measured on the shipped state file,
are the entries of `legacyHamming` below. -/

/-- Four notations for one operation. -/
inductive Syn
  | add | addition | plus | sum
  deriving DecidableEq, Repr

/-- The measured pairwise Hamming distance between the legacy 24-bit carriers
of the four notations.  Symmetric, zero on the diagonal. -/
def legacyHamming : Syn → Syn → ℕ
  | .add, .add => 0 | .add, .addition => 15 | .add, .plus => 15 | .add, .sum => 11
  | .addition, .add => 15 | .addition, .addition => 0
  | .addition, .plus => 14 | .addition, .sum => 10
  | .plus, .add => 15 | .plus, .addition => 14 | .plus, .plus => 0 | .plus, .sum => 12
  | .sum, .add => 11 | .sum, .addition => 10 | .sum, .plus => 12 | .sum, .sum => 0

/-- The proximity relation the ARC-era graph used: carriers within a radius. -/
def legacyNear (r : ℕ) (a b : Syn) : Prop := legacyHamming a b ≤ r

/-- All four notations denote the same thing: the operation `add`. -/
def synDenote : Syn → Meaning :=
  fun _ => ⟨Kind.operation, fun _ => 0, 0, [], some Op.add⟩

/-- **Notation invariance, concretely.**  The meaning carrier gives the four
notations the same 24 coordinates, where the legacy carrier gave them four
carriers at Hamming distance 10 to 15 from each other. -/
theorem synDenote_coords_eq (a b : Syn) : (synDenote a).coords = (synDenote b).coords := rfl

/-- Below radius 15 the legacy proximity relation splits a synonym pair. -/
theorem legacyNear_not_semantic {r : ℕ} (hr : r < 15) :
    ¬ IsSemanticRel (legacyNear r) synDenote := by
  refine not_semanticRel_of_split (a := Syn.add) (b := Syn.add) (c := Syn.add)
    (d := Syn.addition) rfl rfl ?_ ?_
  · simp [legacyNear, legacyHamming]
  · simp only [legacyNear, legacyHamming, not_le]
    omega

/-- From radius 15 up the legacy proximity relation relates everything. -/
theorem legacyNear_trivial {r : ℕ} (hr : 15 ≤ r) (a b : Syn) : legacyNear r a b := by
  cases a <;> cases b <;> simp only [legacyNear, legacyHamming] <;> omega

/-- **No threshold recovers synonymy.**  Every radius either splits notations
that denote the same operation, or relates every notation to every other.  The
legacy carrier has no setting at which its proximity is meaning: the quantity
it measures is spelling. -/
theorem legacy_threshold_dichotomy (r : ℕ) :
    ¬ IsSemanticRel (legacyNear r) synDenote ∨ (∀ a b, legacyNear r a b) := by
  rcases lt_or_ge r 15 with hr | hr
  · exact Or.inl (legacyNear_not_semantic hr)
  · exact Or.inr (legacyNear_trivial hr)

/-- The replacement: `sameMeaning` is semantic, and on these four notations it
relates all of them -- which is the correct answer, since they denote one
operation. -/
theorem sameMeaning_is_semantic {N : Type*} (denote : N → Meaning) :
    IsSemanticRel (fun a b => denote a = denote b) denote :=
  derived_relation_is_semantic (fun x y => x = y) denote

/-! ## Layers on the meaning space

`GLM.Info.Layer` from `Layers.lean`, instantiated on meanings.  The stack runs
from the full meaning down through its EXT10 dimension to the SI7 projection,
and each step down is a boundary at which something true above becomes
invisible below. -/

/-- The finest layer: the meaning itself. -/
def meaningLayer : Layer Meaning := ⟨Meaning, id⟩

/-- The EXT10 dimension layer: a meaning seen as its ten exponents. -/
def dimLayer : Layer Meaning := ⟨Fin 10 → ℚ, Meaning.exponents⟩

/-- The SI7 layer: the seven base-quantity exponents, dropping angle (`A`),
information (`S`) and the tenth axis (`B`). -/
def si7Layer : Layer Meaning := ⟨Fin 7 → ℚ, fun m i => m.exponents ⟨i.1, by omega⟩⟩

theorem meaningLayer_lossless : meaningLayer.Lossless := fun _ _ h => h

theorem meaningLayer_refines_dim : Layer.Refines meaningLayer dimLayer := by
  intro a b hab
  simpa [Layer.Indist, dimLayer] using congrArg Meaning.exponents hab

theorem dim_refines_si7 : Layer.Refines dimLayer si7Layer := by
  intro a b hab
  funext i
  exact congrFun hab ⟨i.1, by omega⟩

/-- `energy`: `L^2 M T^-2` in EXT10, as the physics register holds it. -/
def energyDim : Meaning := ⟨Kind.dimension, ![2, 1, -2, 0, 0, 0, 0, 0, 0, 0], 0, [], none⟩

/-- `torque`: `L^2 M T^-2 A^-1` -- energy per unit angle.  EXT10 keeps the
angle exponent that SI7 has no axis for. -/
def torqueDim : Meaning := ⟨Kind.dimension, ![2, 1, -2, 0, 0, 0, 0, -1, 0, 0], 0, [], none⟩

/-- Energy and torque are distinguished by EXT10. -/
theorem dim_separates_energy_torque : ¬ dimLayer.Indist energyDim torqueDim := by
  intro h
  have h7 := congrFun h 7
  simp [dimLayer, energyDim, torqueDim] at h7

theorem energy_ne_torque : energyDim ≠ torqueDim := by
  intro h
  exact dim_separates_energy_torque (congrArg Meaning.exponents h)

/-- SI7 conflates them: the seven base exponents agree. -/
theorem si7_conflates_energy_torque : si7Layer.Indist energyDim torqueDim := by
  funext i
  simp only [si7Layer, energyDim, torqueDim]
  fin_cases i <;> simp

/-- **A boundary, concretely.**  `(energy, torque)` is information the EXT10
layer holds and the SI7 layer does not: true and distinct above, identical
below. -/
theorem energy_torque_mem_boundary :
    (energyDim, torqueDim) ∈ Layer.Boundary dimLayer si7Layer :=
  ⟨si7_conflates_energy_torque, dim_separates_energy_torque⟩

/-- Hence there is a property of meanings expressible at the EXT10 layer and
not expressible at the SI7 layer: the loss at the boundary is not a matter of
precision, it is a matter of what can be said. -/
theorem exists_visible_dim_not_si7 :
    ∃ P : Meaning → Prop, Layer.Visible dimLayer P ∧ ¬ Layer.Visible si7Layer P :=
  (Layer.boundary_nonempty_iff_new_visible dim_refines_si7).1
    ⟨(energyDim, torqueDim), energy_torque_mem_boundary⟩

/-- The notation layer sits *outside* this stack rather than above it.  It
separates carriers that denote one subject, so what it adds is information
about spelling, not resolution on the subject: **any** relation on these four
notations that holds of one pair and fails of another is, for that reason
alone, not a relation between meanings. -/
theorem notation_split_not_semantic {R : Syn → Syn → Prop} {a b c d : Syn}
    (hab : R a b) (hcd : ¬ R c d) : ¬ IsSemanticRel R synDenote :=
  not_semanticRel_of_split (a := a) (b := b) (c := c) (d := d) rfl rfl hab hcd

end GLM.Semantics
