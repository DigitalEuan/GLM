module

public import Mathlib

/-!
# Native words: word overlap computed on Golay words of the tokens

`studies/NATIVE_WORDS_STUDY.md` (Phase 71) computes the word-overlap ranking
on Golay words of the tokens rather than on the tokens.  The computational
half is `overlay/glm_universal/reasoning/native_words.py`.  This file is the
half that is a theorem.

## 1.  The Golay names carry exactly the token overlap

`jaccard A B = |A ∩ B| / |A ∪ B|` (0 on two empty sets, by Lean's division).
`jaccard_image_of_injOn`: relabelling both sets by a map that is injective on
their union changes no overlap.  `name_injOn`: a name made of a word and an
index that separates the tokens sharing that word is injective on the
vocabulary.  Together (`jaccard_names`) the overlap of Golay names *is* the
token overlap, which is mark W1 of the study.

## 2.  A refinement only reorders inside ties

`take_map_overlap_eq`: two rankings of the same candidates, each sorted by the
same rational overlap (largest first), carry the same sequence of overlaps in
every prefix.  So the native ranking, whose first layer is the Golay-name
overlap, differs from the standard ranking only in which candidates fill a tie
of the overlap; `sorted_overlap_of_sorted_lex` says a lexicographic key sorted
ranking is sorted by its first layer.

## 3.  A shared Golay class is a near letter set

A letter word is a subset of the 24 coordinates, and its Hamming distance to
another is the size of the symmetric difference.  `hamming_triangle` is the
triangle inequality; `shared_class_near`: two letter words inside the packing
radius (distance at most 3) of one codeword differ in at most 6 letter
buckets.  `letterWord_congr`: a letter word reads only the set of letters, so
two parts with the same letters (anagrams) share it — the stated limit of the
native layer.
-/

@[expose] public section

namespace GLM.NativeWords

open Finset

variable {α β : Type*} [DecidableEq α] [DecidableEq β]

/-- The Jaccard overlap of two finite sets, as a rational. -/
def jaccard (A B : Finset α) : ℚ := ((A ∩ B).card : ℚ) / ((A ∪ B).card : ℚ)

theorem jaccard_comm (A B : Finset α) : jaccard A B = jaccard B A := by
  unfold jaccard; rw [inter_comm, union_comm]

/-- **Relabelling by a map injective on the union changes no overlap.** -/
theorem jaccard_image_of_injOn (f : α → β) (A B : Finset α)
    (hf : Set.InjOn f ↑(A ∪ B)) :
    jaccard (A.image f) (B.image f) = jaccard A B := by
  unfold jaccard
  have hi : (A ∩ B).image f = A.image f ∩ B.image f := by
    ext y
    simp only [mem_image, mem_inter]
    constructor
    · rintro ⟨x, ⟨hxA, hxB⟩, rfl⟩
      exact ⟨⟨x, hxA, rfl⟩, ⟨x, hxB, rfl⟩⟩
    · rintro ⟨⟨x, hxA, rfl⟩, ⟨x', hx'B, hx'⟩⟩
      have : x' = x := hf (by simp [hx'B]) (by simp [hxA]) hx'
      subst this
      exact ⟨x', ⟨hxA, hx'B⟩, rfl⟩
  rw [← hi, ← image_union, card_image_of_injOn hf,
    card_image_of_injOn (hf.mono (Finset.coe_subset.mpr inter_subset_union))]

/-- A map injective everywhere changes no overlap. -/
theorem jaccard_image (f : α → β) (hf : Function.Injective f) (A B : Finset α) :
    jaccard (A.image f) (B.image f) = jaccard A B :=
  jaccard_image_of_injOn f A B (hf.injOn)

omit [DecidableEq α] [DecidableEq β] in
/-- **A Golay name is injective on the vocabulary.**  The name of a token is its
letter word `w` and an index `i`; if the index separates the tokens of the
vocabulary that share a word, the name map is injective there. -/
theorem name_injOn (V : Finset α) (w : α → β) (i : α → ℕ)
    (hsep : ∀ a ∈ V, ∀ b ∈ V, w a = w b → i a = i b → a = b) :
    Set.InjOn (fun t => (w t, i t)) ↑V := by
  intro a ha b hb h
  simp only [Prod.mk.injEq] at h
  exact hsep a ha b hb h.1 h.2

/-- **The overlap of Golay names is the token overlap** (mark W1): for any two
token sets inside the vocabulary. -/
theorem jaccard_names (V : Finset α) (w : α → β) (i : α → ℕ)
    (hsep : ∀ a ∈ V, ∀ b ∈ V, w a = w b → i a = i b → a = b)
    (A B : Finset α) (hA : A ⊆ V) (hB : B ⊆ V) :
    jaccard (A.image fun t => (w t, i t)) (B.image fun t => (w t, i t))
      = jaccard A B :=
  jaccard_image_of_injOn _ A B
    ((name_injOn V w i hsep).mono (Finset.coe_subset.mpr (union_subset hA hB)))

/-- The index the running system uses: a token's position among the
vocabulary's tokens with the same word, in any fixed order of the vocabulary.
It separates those tokens, so the hypothesis of `jaccard_names` holds. -/
theorem index_separates (V : Finset α) (w : α → β) (order : List α)
    (hV : ∀ a ∈ V, a ∈ order) :
    ∀ a ∈ V, ∀ b ∈ V, w a = w b →
      (order.filter (fun t => w t = w a)).idxOf a
        = (order.filter (fun t => w t = w b)).idxOf b → a = b := by
  intro a ha b hb hw hidx
  rw [hw] at hidx
  have hbm : b ∈ order.filter (fun t => w t = w b) := by
    simp [hV b hb]
  have ham : a ∈ order.filter (fun t => w t = w b) := by
    simp [hV a ha, hw]
  exact (List.idxOf_inj ham).mp hidx

/-! ## 2. A refinement only reorders inside ties -/

omit [DecidableEq α] [DecidableEq β] in
/-- **Two rankings sorted by the same overlap carry the same overlaps in every
prefix.**  Largest overlap first. -/
theorem take_map_overlap_eq (c : α → ℚ) {l₁ l₂ : List α} (k : ℕ)
    (hperm : l₁.Perm l₂)
    (h₁ : l₁.Pairwise (fun a b => c b ≤ c a))
    (h₂ : l₂.Pairwise (fun a b => c b ≤ c a)) :
    (l₁.take k).map c = (l₂.take k).map c := by
  have h : l₁.map c = l₂.map c :=
    List.Perm.eq_of_pairwise (le := fun x y => y ≤ x)
      (fun _ _ _ _ h1 h2 => le_antisymm h2 h1)
      (List.pairwise_map.mpr h₁) (List.pairwise_map.mpr h₂) (hperm.map c)
  rw [List.map_take, List.map_take, h]

omit [DecidableEq α] [DecidableEq β] in
/-- A ranking sorted by a key whose first layer is the overlap is sorted by the
overlap. -/
theorem sorted_overlap_of_sorted_lex (c : α → ℚ) {R : α → α → Prop}
    (hR : ∀ a b, R a b → c b ≤ c a) {l : List α} (h : l.Pairwise R) :
    l.Pairwise (fun a b => c b ≤ c a) :=
  h.imp (hR _ _)

/-! ## 3. Letter words and Golay classes -/

/-- The Hamming distance of two letter words (subsets of the 24 coordinates). -/
def hamming (x y : Finset (Fin 24)) : ℕ := (symmDiff x y).card

theorem hamming_comm (x y : Finset (Fin 24)) : hamming x y = hamming y x := by
  unfold hamming; rw [symmDiff_comm]

/-- The triangle inequality for the Hamming distance of letter words. -/
theorem hamming_triangle (x y z : Finset (Fin 24)) :
    hamming x z ≤ hamming x y + hamming y z := by
  unfold hamming
  calc (symmDiff x z).card ≤ (symmDiff x y ∪ symmDiff y z).card :=
        card_le_card (symmDiff_triangle x y z)
    _ ≤ (symmDiff x y).card + (symmDiff y z).card := card_union_le _ _

/-- **A shared Golay class inside the packing radius is a near letter set**:
two letter words within distance 3 of the same codeword differ in at most 6
letter buckets. -/
theorem shared_class_near (x y c : Finset (Fin 24))
    (hx : hamming x c ≤ 3) (hy : hamming y c ≤ 3) : hamming x y ≤ 6 := by
  have := hamming_triangle x c y
  rw [hamming_comm c y] at this
  omega

/-- The letter bucket of a character under the stated folding: `a`…`x` keep
their bucket and `y`, `z` join `a`, `b`. -/
def bucket (n : ℕ) : Fin 24 := ⟨n % 24, Nat.mod_lt _ (by norm_num)⟩

/-- The letter word of a part given as the list of its letter indices. -/
def letterWord (part : List ℕ) : Finset (Fin 24) := (part.map bucket).toFinset

/-- **A letter word reads only the set of letters**: two parts with the same
letters share their letter word, whatever the order or multiplicity. -/
theorem letterWord_congr (p q : List ℕ) (h : p.toFinset = q.toFinset) :
    letterWord p = letterWord q := by
  unfold letterWord
  ext x
  simp only [List.mem_toFinset, List.mem_map]
  simp only [Finset.ext_iff, List.mem_toFinset] at h
  simp [h]

/-- The stated limit, on an example: `le` and `el` share a letter word. -/
theorem letterWord_anagram : letterWord [11, 4] = letterWord [4, 11] := by
  decide

/-- `y` (index 24) and `a` (index 0) fall in one bucket. -/
theorem bucket_fold : bucket 24 = bucket 0 := by decide

end GLM.NativeWords
