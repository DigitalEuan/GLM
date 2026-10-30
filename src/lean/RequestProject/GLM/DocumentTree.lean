module

public import Mathlib
public import RequestProject.GLM.CorpusResample

/-!
# The document tree as a third native book: the leak, and the ceiling

`studies/DOCUMENT_TREE_STUDY.md` (Phase 102) asks whether a section's position
in the document tree, held as a Golay word, can move the document rankings
past parity.  The computational half is
`glm_universal/reasoning/document_tree.py`.  This file proves the two
structural facts the study's reading rests on.

## 1.  A book that names the relevance class finds it first

The document benchmark counts a section relevant exactly when it is in the
query's document.  `separating_key_head`: if a ranking is sorted by a key that
is zero exactly on the relevant candidates, and some candidate is relevant,
then the first candidate is relevant.  `injective_word_separates`: the
Hamming distance between the words of two documents under an injective word
map (the `path` book) is such a key.  Together they are why the `path` book
must score a hit at 1 on every query — it reads the answer, so its score is a
leak and not a refinement.

## 2.  A later layer acts only through a tie at the boundary

`take_perm_of_gap`: two rankings that are permutations of one another and
are both sorted by the same cost (for instance the first two layers of the
lexicographic key) have the same top `k` as a *set* whenever every cost in
the first `k` is strictly below every cost after it.  So a third layer can
change the first five only on a query whose first two layers tie across the
boundary between rank five and rank six; the study counts those queries.

## 3.  The sign tests the study prints

`census_signs`: the census discordances at `k = 5` of the study's §3, each
`(first only, second only)`, checked by the kernel with
`GLM.CorpusResample.signTest`.
-/

@[expose] public section

namespace GLM.DocumentTree

/-! ### 1.  The leak -/

/-- **A key that is zero exactly on the relevant candidates puts a relevant
candidate first**, whenever there is one. -/
theorem separating_key_head {α : Type*} (k : α → ℕ) (R : α → Prop)
    {y : α} {t : List α}
    (hsort : (y :: t).Pairwise (fun a b => k a ≤ k b))
    (hsep : ∀ x ∈ y :: t, k x = 0 ↔ R x)
    (hex : ∃ x ∈ y :: t, R x) : R y := by
  obtain ⟨x, hx, hRx⟩ := hex
  have hkx : k x = 0 := (hsep x hx).2 hRx
  have hle : k y ≤ k x := by
    rcases List.mem_cons.1 hx with rfl | hxt
    · exact le_rfl
    · exact (List.pairwise_cons.1 hsort).1 x hxt
  exact (hsep y List.mem_cons_self).1 (by omega)

/-- **An injective word map gives a separating key**: two documents' words
are at Hamming distance zero exactly when the documents are the same. -/
theorem injective_word_separates {D : Type*} {n : ℕ}
    (w : D → (Fin n → Bool)) (hw : Function.Injective w) (d e : D) :
    hammingDist (w d) (w e) = 0 ↔ e = d := by
  rw [hammingDist_eq_zero]
  exact ⟨fun h => (hw h).symm, fun h => h ▸ rfl⟩

/-! ### 2.  The ceiling of a later layer -/

/-- Two permutations sorted by the same cost list the same costs. -/
theorem map_eq_of_perm_sorted {α β : Type*} [LinearOrder β] (c : α → β)
    {l₁ l₂ : List α} (hperm : l₁.Perm l₂)
    (h₁ : l₁.Pairwise (fun a b => c a ≤ c b))
    (h₂ : l₂.Pairwise (fun a b => c a ≤ c b)) :
    l₁.map c = l₂.map c := by
  apply List.Perm.eq_of_pairwise (le := (· ≤ ·)) _ (List.pairwise_map.2 h₁)
    (List.pairwise_map.2 h₂) (hperm.map c)
  intro a b _ _ hab hba
  exact le_antisymm hab hba

/-- **No tie at the boundary, no change in the top `k`.**  If every cost in
the first `k` places of `l₁` is strictly below every cost after them, any
permutation of `l₁` sorted by the same cost has the same first `k`
candidates, up to order. -/
theorem take_perm_of_gap {α β : Type*} [LinearOrder β] (c : α → β)
    {l₁ l₂ : List α} (k : ℕ) (hperm : l₁.Perm l₂)
    (h₁ : l₁.Pairwise (fun a b => c a ≤ c b))
    (h₂ : l₂.Pairwise (fun a b => c a ≤ c b))
    (hgap : ∀ a ∈ l₁.take k, ∀ b ∈ l₁.drop k, c a < c b) :
    (l₁.take k).Perm (l₂.take k) := by
  classical
  have hmap := map_eq_of_perm_sorted c hperm h₁ h₂
  have htake : (l₁.take k).map c = (l₂.take k).map c := by
    rw [List.map_take, List.map_take, hmap]
  have hdrop : (l₁.drop k).map c = (l₂.drop k).map c := by
    rw [List.map_drop, List.map_drop, hmap]
  let p : α → Bool := fun x => decide (c x ∈ (l₁.take k).map c)
  have hf : ∀ l : List α, (l.take k).map c = (l₁.take k).map c →
      (l.drop k).map c = (l₁.drop k).map c → l.filter p = l.take k := by
    intro l ht hd
    conv_lhs => rw [← List.take_append_drop k l]
    rw [List.filter_append]
    have e1 : (l.take k).filter p = l.take k := by
      rw [List.filter_eq_self]
      intro x hx
      simp only [p, decide_eq_true_eq]
      rw [← ht]
      exact List.mem_map_of_mem hx
    have e2 : (l.drop k).filter p = [] := by
      rw [List.filter_eq_nil_iff]
      intro x hx
      simp only [p, decide_eq_true_eq]
      have hcx : c x ∈ (l₁.drop k).map c := by
        rw [← hd]
        exact List.mem_map_of_mem hx
      obtain ⟨b, hb, hbx⟩ := List.mem_map.1 hcx
      rintro hmem
      obtain ⟨a, ha, hax⟩ := List.mem_map.1 hmem
      have hlt := hgap a ha b hb
      rw [hax, hbx] at hlt
      exact lt_irrefl _ hlt
    rw [e1, e2, List.append_nil]
  rw [← hf l₁ rfl rfl, ← hf l₂ htake.symm hdrop.symm]
  exact hperm.filter p

/-! ### 3.  The sign tests -/

open GLM.CorpusResample in
/-- **The census discordances.**  `lexical_native3` against `lexical_raw`
(and `lexical_native2` against it) is `7 : 6`; `lexical_place2` against
`lexical_raw` is `3 : 7`; `path3` against `lexical_native2` is `1 : 0`; and
`lexical_native3` against `lexical_native2` is `0 : 0`.  None is small. -/
theorem census_signs :
    signTest 7 6 = 1 ∧ signTest 3 7 = 11 / 32 ∧ signTest 1 0 = 1 ∧
      signTest 0 0 = 1 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> decide +kernel

end GLM.DocumentTree
