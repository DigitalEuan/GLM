module

public import Mathlib

/-!
# The corpus as what the GLM knows: counting instead of training (Phase 154)

The formal half of `studies/CORPUS_KNOWLEDGE_STUDY.md`. The GLM's corpus model
(`glm_universal/knowledge/model.py`) is nothing but counts: for a feature
extractor `f` (the tokens of a sentence, its adjacent pairs, its two-token
contexts with what follows, the content-word pairs inside a window), the count
of a feature is the number of times it is extracted from the distinct
sentences of each document, summed over the documents. This file proves the
properties that make such a model safe to keep growing, and the two readings
the GLM takes from it.

* `count_append`, `count_perm` — the count over a concatenated list of
  sentences is the sum of the counts, and a reordering changes nothing.
* `train_append` — **learning as the corpus collects**: the model of a corpus
  with documents appended is the old model plus the new documents' model, so
  an incremental model *equals* a recount.
* `train_perm` — the order the documents arrive in cannot change the model.
* `count_pos_iff` — **every figure has a witness**: a count is positive
  exactly when some sentence of the corpus carries the feature.
* `predict_some_iff` — the guarded prediction returns a continuation exactly
  when it is the unique strict maximum of the counts;
  `predict_eq_none_of_tie` — a tie at the top is refused, never broken.
* `sqcos_nonneg`, `sqcos_le_one`, `sqcos_eq_one_iff` — the squared cosine
  `|A ∩ B|² / (|A| |B|)` of two associated-context sets lies in `[0, 1]` and
  is `1` exactly when the sets are equal.
-/

@[expose] public section

namespace GLM.CorpusKnowledge

open Finset

variable {S β : Type*} [DecidableEq β]

/-! ## Counting -/

/-- The count of feature `x` over a list of sentences, for the extractor `f`. -/
def count (f : S → List β) (c : List S) (x : β) : ℕ :=
  (c.map fun s => (f s).count x).sum

theorem count_nil (f : S → List β) (x : β) : count f [] x = 0 := rfl

/-- The count of a concatenation is the sum of the counts. -/
theorem count_append (f : S → List β) (c₁ c₂ : List S) (x : β) :
    count f (c₁ ++ c₂) x = count f c₁ x + count f c₂ x := by
  simp [count, List.map_append, List.sum_append]

/-- Reordering the sentences does not change a count. -/
theorem count_perm (f : S → List β) {c₁ c₂ : List S} (h : c₁.Perm c₂) (x : β) :
    count f c₁ x = count f c₂ x := by
  unfold count
  exact (h.map _).sum_eq

/-- **Every figure has a witness**: a count is positive exactly when some
sentence carries the feature. -/
theorem count_pos_iff (f : S → List β) (c : List S) (x : β) :
    0 < count f c x ↔ ∃ s ∈ c, x ∈ f s := by
  induction c with
  | nil => simp [count]
  | cons s c ih =>
    have : count f (s :: c) x = (f s).count x + count f c x := by
      simp [count]
    rw [this, Nat.add_pos_iff_pos_or_pos, ih, List.count_pos_iff]
    simp

variable [DecidableEq S]

/-- A document counts its *distinct* sentences: a sentence repeated verbatim
is said once. -/
def docCount (f : S → List β) (d : List S) (x : β) : ℕ :=
  count f d.dedup x

/-- The model of a corpus of documents: the sum of the documents' counts. -/
def train (f : S → List β) (ds : List (List S)) (x : β) : ℕ :=
  (ds.map fun d => docCount f d x).sum

/-- **Learning as the corpus collects**: appending documents adds their
counts, so an incremental model equals a recount from nothing. -/
theorem train_append (f : S → List β) (ds₁ ds₂ : List (List S)) (x : β) :
    train f (ds₁ ++ ds₂) x = train f ds₁ x + train f ds₂ x := by
  simp [train, List.map_append, List.sum_append]

/-- Adding one document is adding its counts. -/
theorem train_snoc (f : S → List β) (ds : List (List S)) (d : List S) (x : β) :
    train f (ds ++ [d]) x = train f ds x + docCount f d x := by
  simp [train]

/-- The order in which documents arrive cannot change the model. -/
theorem train_perm (f : S → List β) {ds₁ ds₂ : List (List S)} (h : ds₁.Perm ds₂)
    (x : β) : train f ds₁ x = train f ds₂ x := by
  unfold train
  exact (h.map _).sum_eq

/-- Every count of the model has a witness sentence in some document. -/
theorem train_pos_iff (f : S → List β) (ds : List (List S)) (x : β) :
    0 < train f ds x ↔ ∃ d ∈ ds, ∃ s ∈ d, x ∈ f s := by
  induction ds with
  | nil => simp [train]
  | cons d ds ih =>
    have : train f (d :: ds) x = docCount f d x + train f ds x := by
      simp [train]
    rw [this, Nat.add_pos_iff_pos_or_pos, ih, docCount, count_pos_iff]
    simp [List.mem_dedup]

/-! ## The guarded prediction -/

/-- Is `w` the strict maximum of `cnt` over `cands`? -/
def IsStrictMax (cands : List β) (cnt : β → ℕ) (w : β) : Prop :=
  w ∈ cands ∧ ∀ v ∈ cands, v ≠ w → cnt v < cnt w

instance (cands : List β) (cnt : β → ℕ) (w : β) :
    Decidable (IsStrictMax cands cnt w) := by
  unfold IsStrictMax; infer_instance

/-- The guarded prediction: the continuation whose count beats every other,
or nothing. -/
def predict (cands : List β) (cnt : β → ℕ) : Option β :=
  cands.find? fun w => decide (IsStrictMax cands cnt w)

theorem strictMax_unique {cands : List β} {cnt : β → ℕ} {w w' : β}
    (h : IsStrictMax cands cnt w) (h' : IsStrictMax cands cnt w') : w = w' := by
  by_contra hne
  have h1 := h.2 w' h'.1 (Ne.symm hne)
  have h2 := h'.2 w h.1 hne
  omega

/-- The prediction returns `w` exactly when `w` is the unique strict maximum. -/
theorem predict_some_iff (cands : List β) (cnt : β → ℕ) (w : β) :
    predict cands cnt = some w ↔ IsStrictMax cands cnt w := by
  constructor
  · intro h
    have := List.find?_some h
    simpa using this
  · intro hw
    unfold predict
    cases hfind : cands.find? (fun w => decide (IsStrictMax cands cnt w)) with
    | none =>
      exfalso
      have := List.find?_eq_none.mp hfind w hw.1
      simp [hw] at this
    | some w' =>
      have := List.find?_some hfind
      have hw' : IsStrictMax cands cnt w' := by simpa using this
      rw [strictMax_unique hw' hw]

/-- When the prediction answers, its count is at least every candidate's. -/
theorem predict_some_max {cands : List β} {cnt : β → ℕ} {w : β}
    (h : predict cands cnt = some w) : ∀ v ∈ cands, cnt v ≤ cnt w := by
  have hw := (predict_some_iff cands cnt w).mp h
  intro v hv
  by_cases hvw : v = w
  · rw [hvw]
  · exact (hw.2 v hv hvw).le

/-- **A tie is refused, never broken**: two distinct candidates attaining the
maximum count give no prediction. -/
theorem predict_eq_none_of_tie {cands : List β} {cnt : β → ℕ} {a b : β}
    (ha : a ∈ cands) (hb : b ∈ cands) (hab : a ≠ b) (heq : cnt a = cnt b)
    (hmax : ∀ v ∈ cands, cnt v ≤ cnt a) : predict cands cnt = none := by
  cases h : predict cands cnt with
  | none => rfl
  | some w =>
    exfalso
    have hw := (predict_some_iff cands cnt w).mp h
    by_cases hwa : w = a
    · subst hwa
      have := hw.2 b hb (Ne.symm hab)
      omega
    · have h1 := hw.2 a ha (Ne.symm hwa)
      have h2 := hmax w hw.1
      omega

/-! ## The squared cosine of two context sets -/

/-- `|A ∩ B|² / (|A| |B|)`: the exact squared cosine of the indicator vectors
of two finite sets. -/
def sqcos (A B : Finset β) : ℚ :=
  ((A ∩ B).card ^ 2 : ℚ) / ((A.card : ℚ) * B.card)

theorem sqcos_nonneg (A B : Finset β) : 0 ≤ sqcos A B := by
  unfold sqcos; positivity

theorem sqcos_le_one (A B : Finset β) : sqcos A B ≤ 1 := by
  unfold sqcos
  rcases Nat.eq_zero_or_pos A.card with hA | hA
  · simp [hA]
  rcases Nat.eq_zero_or_pos B.card with hB | hB
  · simp [hB]
  have h1 : (A ∩ B).card ≤ A.card := card_le_card inter_subset_left
  have h2 : (A ∩ B).card ≤ B.card := card_le_card inter_subset_right
  rw [div_le_one (by positivity)]
  have : (A ∩ B).card ^ 2 ≤ A.card * B.card := by
    rw [sq]; exact Nat.mul_le_mul h1 h2
  exact_mod_cast this

/-- The squared cosine is `1` exactly when the two (nonempty) sets are equal. -/
theorem sqcos_eq_one_iff {A B : Finset β} (hA : A.Nonempty) :
    sqcos A B = 1 ↔ A = B := by
  constructor
  · intro h
    unfold sqcos at h
    have hA' : 0 < A.card := hA.card_pos
    rcases Nat.eq_zero_or_pos B.card with hB | hB
    · simp [hB] at h
    have hne : ((A.card : ℚ) * B.card) ≠ 0 := by positivity
    rw [div_eq_one_iff_eq hne] at h
    have h' : (A ∩ B).card ^ 2 = A.card * B.card := by exact_mod_cast h
    have h1 : (A ∩ B).card ≤ A.card := card_le_card inter_subset_left
    have h2 : (A ∩ B).card ≤ B.card := card_le_card inter_subset_right
    have e1 : (A ∩ B).card = A.card := by
      by_contra hne1
      have hlt : (A ∩ B).card < A.card := lt_of_le_of_ne h1 hne1
      have : (A ∩ B).card ^ 2 < A.card * B.card := by
        rw [sq]; exact Nat.mul_lt_mul_of_lt_of_le hlt h2 (by omega)
      omega
    have e2 : (A ∩ B).card = B.card := by
      by_contra hne2
      have hlt : (A ∩ B).card < B.card := lt_of_le_of_ne h2 hne2
      have : (A ∩ B).card ^ 2 < A.card * B.card := by
        rw [sq]; exact Nat.mul_lt_mul_of_le_of_lt h1 hlt hA'
      omega
    have sA : A ⊆ B := by
      have := eq_of_subset_of_card_le (inter_subset_left (s₁ := A) (s₂ := B)) e1.ge
      rw [← this]; exact inter_subset_right
    have sB : B ⊆ A := by
      have := eq_of_subset_of_card_le (inter_subset_right (s₁ := A) (s₂ := B)) e2.ge
      rw [← this]; exact inter_subset_left
    exact Subset.antisymm sA sB
  · rintro rfl
    unfold sqcos
    have : (0 : ℚ) < A.card := by exact_mod_cast hA.card_pos
    rw [inter_self, div_eq_one_iff_eq (by positivity), sq]

end GLM.CorpusKnowledge
