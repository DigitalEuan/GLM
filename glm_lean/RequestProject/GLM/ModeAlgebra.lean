/-
# The mode algebra: Kracht signs, and what the argmax collapse costs

Retrieved from `source_material/GLM-main.zip/glm_machine/GLM32_mode_algebra.py`
(with the sextet conventions of `GLM22_ontological_grammar.py`).

The archive's §32 implements Marcus Kracht's sign grammar: a sign is a triple
`⟨E, C, M⟩` -- exponent, category, meaning -- and a combination is *definite*
("strong") only when all three homomorphisms are defined at once.  Its stated
complaint against the rest of that engine is that `computed_role` collapses the
category `C`, a four-vector of sextet weights, to its argmax, and that a
combination cannot be licensed from the argmax alone.

This file is the arithmetic of that complaint.  A category is a map
`Fin 4 → Fin 7`: one weight per sextet of a 24-bit word, each between 0 and 6.
The four roles are NOUN, ADJECTIVE, VERB, OPERATOR in that order, and the
archive's `dominant_role` takes the *first* index attaining the maximum.

What is proved:

* `dominantIndex_is_maximal`, `dominantIndex_is_first` -- the collapse is what
  the archive says it is, ties breaking to the lowest index.
* `dominantRole_ne_property` -- `dominant_role` can never return `PROPERTY`,
  so the `PROPERTY` disjunct of the ELABORATION test is dead, and
  `elaborationOk_eq_without_property` removes it without changing the test.
* `svo_not_a_function_of_dominant_role` against
  `definitionOk_is_a_function_of_dominant_role` -- the complaint is exact for
  one mode and empty for another: the SVO verb slot separates two categories
  with the same argmax, while the DEFINITION test depends on the argmax alone.
* the census of the 2401 categories: `card_dominance` `[784, 644, 532, 441]`,
  `card_subjectOk = 1724`, `card_verbOk = 1717`, and the licensed counts
  `svo_licensed_triples = 5103226192`, `definition_licensed_pairs = 614656`.
* `catOf_surjective` -- every one of the 2401 categories is realised by a
  24-bit word, so the census is a census of reachable states.
* `contradiction_never_definite` with `strongness_is_strictly_stronger` --
  the CONTRADICTION mode passes its category test on 614656 pairs and is
  definite on none of them, which is Kracht strongness doing work: category
  agreement does not imply a definite combination.

Every proof here is complete: no holes.
-/
import Mathlib

namespace GLM.ModeAlgebra

open Finset

/-! ## Categories and roles -/

/-- The grammatical roles the archive names.  `dominant_role` returns one of
the first four; `PROPERTY` is named in the ELABORATION test and in the
comments of the SVO test, and is never produced. -/
inductive Role
  | noun | adjective | verb | operator | property
  deriving DecidableEq, Repr, Fintype

/-- A category vector: the weight of each of the four sextets of a 24-bit
word, so a value in `0, …, 6` for each of the four positions. -/
abbrev Cat := Fin 4 → Fin 7

/-- `GRAMMAR_ROLE = {0: "NOUN", 1: "ADJECTIVE", 2: "VERB", 3: "OPERATOR"}`. -/
def roleOfIndex : Fin 4 → Role
  | 0 => .noun
  | 1 => .adjective
  | 2 => .verb
  | 3 => .operator

/-- `list(cv).index(max(cv))`: the first index attaining the maximum. -/
def dominantIndex (c : Cat) : Fin 4 :=
  let i₁ : Fin 4 := if c 0 < c 1 then 1 else 0
  let i₂ : Fin 4 := if c i₁ < c 2 then 2 else i₁
  if c i₂ < c 3 then 3 else i₂

/-- The archive's `dominant_role`. -/
def dominantRole (c : Cat) : Role := roleOfIndex (dominantIndex c)

theorem dominantIndex_is_maximal : ∀ (c : Cat) (i : Fin 4), c i ≤ c (dominantIndex c) := by
  decide +kernel

theorem dominantIndex_is_first :
    ∀ (c : Cat) (i : Fin 4), i < dominantIndex c → c i < c (dominantIndex c) := by
  decide +kernel

/-- The `PROPERTY` role is unreachable: `dominant_role` returns an index of
the four-vector, and the table has only four entries. -/
theorem dominantRole_ne_property (c : Cat) : dominantRole c ≠ Role.property := by
  have : ∀ j : Fin 4, roleOfIndex j ≠ Role.property := by decide
  exact this _

/-! ## The category tests of the modes -/

/-- `has_category_affordance cv role threshold`. -/
def affords (c : Cat) (i : Fin 4) (t : ℕ) : Bool := decide (t ≤ (c i : ℕ))

/-- The subject and object slots of `_svo_category`: NOUN-dominant, or two
bits of NOUN affordance. -/
def subjectOk (c : Cat) : Bool := (dominantRole c == .noun) || affords c 0 2

/-- The verb slot of `_svo_category`. -/
def verbOk (c : Cat) : Bool := (dominantRole c == .verb) || affords c 2 2

/-- `_svo_category`. -/
def svoOk (s v o : Cat) : Bool := subjectOk s && verbOk v && subjectOk o

/-- `_definition_category`, and also `_contradiction_category`. -/
def definitionOk (a b : Cat) : Bool :=
  (dominantRole a == .noun) && (dominantRole b == .noun)

/-- `_elaboration_category`, transcribed with the dead `PROPERTY` disjunct
still in place. -/
def elaborationOk (m d : Cat) : Bool :=
  ((dominantRole m == .noun) || (dominantRole m == .verb)) &&
    ((dominantRole d == .noun) || (dominantRole d == .adjective) ||
      (dominantRole d == .property))

theorem elaborationOk_eq_without_property (m d : Cat) :
    elaborationOk m d =
      (((dominantRole m == .noun) || (dominantRole m == .verb)) &&
        ((dominantRole d == .noun) || (dominantRole d == .adjective))) := by
  have h : (dominantRole d == Role.property) = false := by
    simp [dominantRole_ne_property d]
  simp [elaborationOk, h]

/-! ## What the argmax collapse costs

The DEFINITION test reads only the argmax, so collapsing the category loses
nothing there.  The SVO test does not, and two categories with the same argmax
disagree on it. -/

theorem definitionOk_is_a_function_of_dominant_role
    (a b a' b' : Cat) (ha : dominantRole a = dominantRole a')
    (hb : dominantRole b = dominantRole b') :
    definitionOk a b = definitionOk a' b' := by
  simp [definitionOk, ha, hb]

/-- Two categories with the same dominant role, one licensed in the verb slot
and one not: `(2,0,2,0)` and `(2,0,1,0)` are both NOUN-dominant, and only the
first has the two bits of VERB affordance the SVO test asks for. -/
theorem svo_not_a_function_of_dominant_role :
    ∃ c c' : Cat, dominantRole c = dominantRole c' ∧
      verbOk c = true ∧ verbOk c' = false :=
  ⟨![2, 0, 2, 0], ![2, 0, 1, 0], by decide, by decide, by decide⟩

/-- The same failure inside a full SVO triple: one licensed sentence and one
refused, with the same three dominant roles throughout. -/
theorem svo_triple_not_a_function_of_dominant_role :
    ∃ s v o v' : Cat, dominantRole v = dominantRole v' ∧
      svoOk s v o = true ∧ svoOk s v' o = false :=
  ⟨![6, 0, 0, 0], ![2, 0, 2, 0], ![6, 0, 0, 0], ![2, 0, 1, 0],
    by decide, by decide, by decide⟩

/-! ## The census of categories -/

theorem card_all : (univ : Finset Cat).card = 2401 := by decide +kernel

/-- How many of the 2401 categories are dominated by each of the four roles.
-/
theorem card_dominance :
    [Role.noun, Role.adjective, Role.verb, Role.operator].map
        (fun r => (univ.filter fun c : Cat => dominantRole c == r).card)
      = [784, 644, 532, 441] := by decide +kernel

theorem card_subjectOk : (univ.filter fun c : Cat => subjectOk c).card = 1724 := by
  decide +kernel

theorem card_verbOk : (univ.filter fun c : Cat => verbOk c).card = 1717 := by
  decide +kernel

/-- `svoOk` factors slot by slot, so the licensed triples are a product. -/
theorem svoOk_factors (s v o : Cat) :
    svoOk s v o = true ↔ subjectOk s = true ∧ verbOk v = true ∧ subjectOk o = true := by
  simp [svoOk, and_assoc]

/-- The number of SVO-licensed triples of categories. -/
theorem svo_licensed_triples :
    (univ.filter fun c : Cat => subjectOk c).card *
      (univ.filter fun c : Cat => verbOk c).card *
      (univ.filter fun c : Cat => subjectOk c).card = 5103226192 := by
  rw [card_subjectOk, card_verbOk]

/-- The number of DEFINITION-licensed pairs -- and, since
`_contradiction_category` is the same test, the number of pairs the
CONTRADICTION mode accepts and then refuses. -/
theorem definition_licensed_pairs :
    (univ.filter fun c : Cat => dominantRole c == Role.noun).card *
      (univ.filter fun c : Cat => dominantRole c == Role.noun).card = 614656 := by
  have h : (univ.filter fun c : Cat => dominantRole c == Role.noun).card = 784 := by
    have := card_dominance
    simpa using congrArg (fun l => l.headI) this
  rw [h]

/-! ## Every category is realised by a 24-bit word

`QUADRANT_RANGES = [(0,6), (6,12), (12,18), (18,24)]`: the category of a word
is the list of its four sextet weights. -/

/-- The weight of sextet `i` of a 24-bit word. -/
def sextetWeight (v : Fin 24 → Bool) (i : Fin 4) : ℕ :=
  (univ.filter fun j : Fin 6 =>
    v ⟨6 * i.val + j.val, by have := i.isLt; have := j.isLt; omega⟩).card

theorem sextetWeight_le (v : Fin 24 → Bool) (i : Fin 4) : sextetWeight v i ≤ 6 := by
  simpa using (card_filter_le (univ : Finset (Fin 6)) _)

/-- `quadrant_weights`: the category vector of a 24-bit word. -/
def catOf (v : Fin 24 → Bool) : Cat :=
  fun i => ⟨sextetWeight v i, Nat.lt_succ_of_le (sextetWeight_le v i)⟩

theorem catOf_val (v : Fin 24 → Bool) (i : Fin 4) : (catOf v i : ℕ) = sextetWeight v i := rfl

private theorem card_filter_lt (m : ℕ) (hm : m ≤ 6) :
    (univ.filter fun j : Fin 6 => j.val < m).card = m := by
  interval_cases m <;> decide

theorem catOf_surjective : Function.Surjective catOf := by
  intro c
  refine ⟨fun k => decide (k.val % 6 < (c ⟨k.val / 6, by omega⟩ : ℕ)), ?_⟩
  funext i
  apply Fin.ext
  rw [catOf_val]
  have hi := i.isLt
  have key : (univ.filter fun j : Fin 6 =>
      decide ((6 * i.val + j.val) % 6 < (c ⟨(6 * i.val + j.val) / 6, by omega⟩ : ℕ)) = true)
      = (univ.filter fun j : Fin 6 => j.val < (c i : ℕ)) := by
    apply filter_congr
    intro j _
    have hj := j.isLt
    have h1 : (6 * i.val + j.val) % 6 = j.val := by omega
    have h2 : (6 * i.val + j.val) / 6 = i.val := by omega
    have h3 : (⟨(6 * i.val + j.val) / 6, by omega⟩ : Fin 4) = i := by
      apply Fin.ext; simpa using h2
    simp [h1, h3]
  simp only [sextetWeight, key]
  exact card_filter_lt _ (Nat.lt_succ_iff.mp (c i).isLt)

/-! ## Strongness: the CONTRADICTION mode is nowhere definite -/

/-- The seventeen CRG edge labels the verbalisation table covers, plus the
`identity` label a single concept carries. -/
inductive Label
  | isA | hasProperty | dependsOn | commutesWith | scalesAs | isDualTo
  | generates | measures | latticeAdjacent | latticeAdjacent1 | latticeAdjacent2
  | latticeAdjacent3 | latticeAdjacent4 | latticeAdjacent5 | autoProposed
  | contradicts | incompatibleWith | coOccurs
  deriving DecidableEq, Repr, Fintype

/-- `_INDEFINITE_LABELS`: the meaning homomorphism is bottom on these. -/
def indefinite : Label → Bool
  | .contradicts => true
  | .incompatibleWith => true
  | _ => false

theorem card_labels : Fintype.card Label = 18 := by decide

theorem card_indefinite_labels :
    (univ.filter fun l : Label => indefinite l).card = 2 := by decide

/-- A sign, reduced to the two components that decide definiteness: the
category vector and the label its meaning carries. -/
structure Sign where
  cat : Cat
  label : Label

/-- `_relation_category`: both categories nonzero, and the label definite. -/
def relationCategory (src edge : Sign) : Bool :=
  decide (0 < ∑ i, (src.cat i : ℕ)) && decide (0 < ∑ i, (edge.cat i : ℕ)) &&
    !indefinite edge.label

/-- `_relation_meaning` returns bottom exactly on the indefinite labels. -/
def relationMeaningDefined (edge : Sign) : Bool := !indefinite edge.label

/-- `combine` under the RELATION mode: definite iff both halves are. -/
def relationDefinite (src edge : Sign) : Bool :=
  relationCategory src edge && relationMeaningDefined edge

theorem relationDefinite_iff (src edge : Sign) :
    relationDefinite src edge = true ↔
      0 < ∑ i, (src.cat i : ℕ) ∧ 0 < ∑ i, (edge.cat i : ℕ) ∧
        indefinite edge.label = false := by
  simp [relationDefinite, relationCategory, relationMeaningDefined, and_assoc]

/-- `_contradiction_category`: both NOUN-dominant. -/
def contradictionCategory (a b : Sign) : Bool := definitionOk a.cat b.cat

/-- `_contradiction_meaning` returns `None` for every argument. -/
def contradictionMeaning (_ _ : Sign) : Option Unit := none

/-- `combine` under the CONTRADICTION mode. -/
def contradictionDefinite (a b : Sign) : Bool :=
  contradictionCategory a b && (contradictionMeaning a b).isSome

theorem contradiction_never_definite (a b : Sign) :
    contradictionDefinite a b = false := by
  simp [contradictionDefinite, contradictionMeaning]

/-- Category agreement is strictly weaker than Kracht's strongness: the
CONTRADICTION mode accepts a pair in the category algebra and is still not a
definite combination.  The mode is registered in `MODES` and can never fire. -/
theorem strongness_is_strictly_stronger :
    ∃ a b : Sign, contradictionCategory a b = true ∧
      contradictionDefinite a b = false := by
  refine ⟨⟨![6, 0, 0, 0], .isA⟩, ⟨![6, 0, 0, 0], .isA⟩, ?_, contradiction_never_definite _ _⟩
  decide

end GLM.ModeAlgebra
