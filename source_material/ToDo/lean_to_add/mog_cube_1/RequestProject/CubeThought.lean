import Mathlib
import RequestProject.ClauseStore

/-!
# Reasoning on the cube

Report 3 §5.8, the last of the things that were still missing:

> **The cube is still storage, not thought.**  §3 shows the least-effort code
> makes the cube hold 33% more language, and report 2 showed clauses can be
> stored with three-cell repair, but the reasoning itself does not happen on
> the cube.

Here it does.  A law of the world — "boiling implies hot", "frozen implies not
warm" — is *itself* a point of the surface: the difference of the record of its
premise and the record of its conclusion.  Since the code is linear that
difference is a codeword, and inference is then a single bitwise addition:

    conclusion = premise ⊕ law

That is not a lookup and not a search.  It is 24 exclusive-ors.

## What is proved

* `lawWord_is_a_codeword` — every law occupies a point of the surface.
* `apply_law` — adding the law word to the premise record gives exactly the
  conclusion record.
* `negation_is_a_translation` — denial is one *fixed* word, the same for all 48
  literals: `¬` is a rigid motion of the cube (`negWord_is_universal`).
* `inference_survives_damage` — the payoff, and the reason to do arithmetic
  rather than lookup: reasoning commutes with repair.  A premise record
  received with up to three cells wrong, added to the law word, decodes to the
  *correct* conclusion.  So a corrupted premise still yields a sound conclusion
  with no intermediate decoding step.
* `laws_are_sound_on_the_surface` — every law word used here really is an
  entailment of the semantics, checked over all 512 worlds.
* `law_words_counted` — the honest limit.  Inference is a translation, but not
  *one* translation: the 78 entailing pairs of the narrow world use 27 distinct
  law words, so the surface stores a small law table rather than a single rule.
  Only negation collapses to one word.
-/

namespace CubeThought

open ThreeCube SentenceCode Semantics ClauseStore

set_option maxRecDepth 100000

/-! ## 1. Translation of the surface -/

/-- Adding a fixed word to both sides changes no distance. -/
theorem dist3_xor_right (t u c : Tri) : dist3 (dxor t c) (dxor u c) = dist3 t u := by
  have h : dxor (dxor t c) (dxor u c) = dxor t u := by
    funext n v
    simp only [dxor]
    cases t n v <;> cases u n v <;> cases c n v <;> rfl
  rw [dist3, dist3, h]

theorem dxor_self (t c : Tri) : dxor (dxor t c) c = t := by
  funext n v
  simp only [dxor]
  cases t n v <;> cases c n v <;> rfl

/-! ## 2. A law as a point of the surface -/

/-- The word of a law: the difference of the two clause records. -/
def lawWord (l m : Lit) : Tri := dxor (encode (clauseRec l)) (encode (clauseRec m))

/-- **Every law occupies a point of the surface**: the difference of two records
is again a word of the code, addressed by a field triple. -/
theorem lawWord_is_a_codeword (l m : Lit) :
    ∃ f : Fin 16 × Fin 16 × Fin 16, lawWord l m = recOf f := by
  refine ⟨(xor16 (fields (clauseRec l)).1 (fields (clauseRec m)).1,
      xor16 (fields (clauseRec l)).2.1 (fields (clauseRec m)).2.1,
      xor16 (fields (clauseRec l)).2.2 (fields (clauseRec m)).2.2), ?_⟩
  rw [lawWord, encode_eq_recOf, encode_eq_recOf, dxor_recOf]

/-- **Inference is addition.**  The conclusion record is the premise record plus
the law word — twenty-four exclusive-ors, no lookup and no search. -/
theorem apply_law (l m : Lit) :
    dxor (encode (clauseRec l)) (lawWord l m) = encode (clauseRec m) := by
  funext n v
  simp only [dxor, lawWord]
  cases h1 : encode (clauseRec l) n v <;> cases h2 : encode (clauseRec m) n v <;> rfl

/-! ## 3. Denial is one fixed motion -/

/-- The word of denial: flip the polarity bit of the first field. -/
def negWord : Tri := recOf (1, 0, 0)

/-- **Denial is a rigid motion of the cube.**  One word, added to any clause
record whatsoever, gives the record of its denial. -/
theorem negation_is_a_translation (l : Lit) :
    dxor (encode (clauseRec l)) negWord = encode (clauseRec (negL l)) := by
  revert l
  have : ∀ l ∈ allLits, dxor (encode (clauseRec l)) negWord = encode (clauseRec (negL l)) := by
    native_decide
  intro l
  exact this l (mem_allLits l)

/-- …and it is the *same* word for every one of the 48 literals, which no other
law is. -/
theorem negWord_is_universal :
    ∀ l ∈ allLits, lawWord l (negL l) = negWord := by
  intro l hl
  rw [lawWord, ← negation_is_a_translation l]
  funext n v
  simp only [dxor]
  cases encode (clauseRec l) n v <;> cases negWord n v <;> rfl

/-! ## 4. Reasoning survives damage -/

/-- **The payoff.**  A premise record received with up to three cells wrong,
added to the law word, decodes to exactly the conclusion record.  Repair and
inference commute: the reasoning can be done on the damaged surface and the
answer is still right. -/
theorem inference_survives_damage {t : Tri} {l m : Lit}
    (h : dist3 t (encode (clauseRec l)) ≤ 3) :
    decodeRec (dxor t (lawWord l m)) = some (clauseRec m) := by
  refine decodeRec_correct ?_
  have h1 : dist3 (dxor t (lawWord l m)) (dxor (encode (clauseRec l)) (lawWord l m))
      = dist3 t (encode (clauseRec l)) := dist3_xor_right _ _ _
  rw [apply_law l m] at h1
  omega

/-- The same for denial, with the single universal word. -/
theorem denial_survives_damage {t : Tri} {l : Lit} (h : dist3 t (encode (clauseRec l)) ≤ 3) :
    decodeRec (dxor t negWord) = some (clauseRec (negL l)) := by
  refine decodeRec_correct ?_
  have h1 : dist3 (dxor t negWord) (dxor (encode (clauseRec l)) negWord)
      = dist3 t (encode (clauseRec l)) := dist3_xor_right _ _ _
  rw [negation_is_a_translation l] at h1
  omega

/-! ## 5. The law table, and how big it has to be -/

/-- The entailing pairs of the narrow world, among contingent literals. -/
def lawPairs : List (Lit × Lit) :=
  (allLits.filter contingent).flatMap fun l =>
    ((allLits.filter contingent).filter fun m => entails l m && decide (l ≠ m)).map fun m => (l, m)

/-- The law words those pairs use. -/
def lawTable : List Tri := lawPairs.map fun p => lawWord p.1 p.2

/-- **Every law word on the table is a genuine entailment**, checked over all
512 worlds: nothing is stored that the semantics does not license. -/
theorem laws_are_sound_on_the_surface :
    ∀ p ∈ lawPairs, ∀ w : World, evalLit p.1 w = true → evalLit p.2 w = true := by
  have h : lawPairs.all (fun p => entails p.1 p.2) = true := by native_decide
  intro p hp w hw
  exact (entails_iff p.1 p.2).mp (List.all_eq_true.mp h p hp) w hw

/-- **The honest limit.**  Inference is a translation, but not one translation:
the 78 entailing pairs of distinct contingent literals use 27 distinct words, so
the surface has to carry a law table — though a small one, since the same
translation serves many pairs.  Denial is the extreme case: a single word covers
all 48 literals. -/
theorem law_words_counted :
    lawPairs.length = 78 ∧ lawTable.eraseDups.length = 27 := by
  refine ⟨by native_decide, by native_decide⟩

/-- Every stored law is applied by addition, and every application lands on a
record of the clause role. -/
theorem law_table_applies :
    ∀ p ∈ lawPairs, dxor (encode (clauseRec p.1)) (lawWord p.1 p.2) = encode (clauseRec p.2) := by
  intro p _
  exact apply_law p.1 p.2

/-- A chain of two laws is the sum of their words: reasoning composes on the
surface. -/
theorem laws_compose (l m k : Lit) :
    dxor (lawWord l m) (lawWord m k) = lawWord l k := by
  funext n v
  simp only [dxor, lawWord]
  cases encode (clauseRec l) n v <;> cases encode (clauseRec m) n v <;>
    cases encode (clauseRec k) n v <;> rfl

end CubeThought
