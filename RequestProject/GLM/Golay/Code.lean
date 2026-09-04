/-
# The extended binary Golay code, concretely

`GolayBoundary.lean` proves what happens at the snap radius for *any* code of
minimum distance 8.  This file introduces the actual code the GLM substrate
uses — the systematic `[24, 12, 8]` extended binary Golay code with generator
`G = [I₁₂ | B]` and the symmetric parity block `B` of
`overlay/glm_universal/substrate/mog.py` — so that the sharper facts (how *many*
codewords tie at the covering radius, and what their supports look like) can be
stated and proved about it rather than assumed.

A word is its support: a `Finset (Fin 24)`.  Symmetric difference is addition,
so the code is the kernel of the syndrome map `syn s = ∑ k ∈ s, col k` into
`Fin 12 → ZMod 2`, where `col k` is the `k`-th column of `H = [B | I₁₂]`.

The content of this file is the algebra of that map:

* `syn_symmDiff` — the syndrome is additive over symmetric difference;
* `syn_eq_iff_isCodeword_symmDiff` — two words share a syndrome exactly when
  they differ by a codeword, i.e. syndromes name the cosets;
* `hdist` and its metric lemmas, expressed through `syn`.

The computational facts about this particular `B` live in `Golay/Sextet.lean`.
-/
import Mathlib

namespace GLM.Golay24

open Finset

/-- A 24-bit word, held as its support. -/
abbrev Word : Type := Finset (Fin 24)

/-- A syndrome: a vector of twelve parity bits. -/
abbrev Syn : Type := Fin 12 → ZMod 2

/-- The symmetric `12 × 12` parity block `B`, exactly the table used by the
substrate's `GolayCode`.  The generator is `G = [I₁₂ | B]` and, `B` being
symmetric, the parity-check matrix is `H = [B | I₁₂]`. -/
def Brows : List (List ℕ) :=
  [[0,1,1,1,1,1,1,1,1,1,1,1],
   [1,1,1,0,1,1,1,0,0,0,1,0],
   [1,1,0,1,1,1,0,0,0,1,0,1],
   [1,0,1,1,1,0,0,0,1,0,1,1],
   [1,1,1,1,0,0,0,1,0,1,1,0],
   [1,1,1,0,0,0,1,0,1,1,0,1],
   [1,1,0,0,0,1,0,1,1,0,1,1],
   [1,0,0,0,1,0,1,1,0,1,1,1],
   [1,0,0,1,0,1,1,0,1,1,1,0],
   [1,0,1,0,1,1,0,1,1,1,0,0],
   [1,1,0,1,1,0,1,1,1,0,0,0],
   [1,0,1,1,0,1,1,1,0,0,0,1]]

/-- The entry `B i j` of the parity block. -/
def Bmat (i j : Fin 12) : ZMod 2 := ((Brows.getD i []).getD j 0 : ℕ)

/-- `B` is symmetric. -/
theorem Bmat_symm (i j : Fin 12) : Bmat i j = Bmat j i := by revert i j; decide

/-- Column `k` of the parity-check matrix `H = [B | I₁₂]`. -/
def col (k : Fin 24) : Syn :=
  fun i => if h : (k : ℕ) < 12 then Bmat i ⟨(k : ℕ), h⟩
           else if (k : ℕ) = (i : ℕ) + 12 then 1 else 0

/-- The syndrome of a word: the sum of the parity-check columns it selects. -/
def syn (s : Word) : Syn := ∑ k ∈ s, col k

/-- A word is a codeword when its syndrome vanishes. -/
def IsCodeword (s : Word) : Prop := syn s = 0

instance (s : Word) : Decidable (IsCodeword s) := by
  unfold IsCodeword; infer_instance

/-- Hamming distance: the size of the symmetric difference of the supports. -/
def hdist (a b : Word) : ℕ := (symmDiff a b).card

/-- The Hamming weight of a word. -/
def wt (a : Word) : ℕ := a.card

/-! ## The syndrome map is additive -/

theorem neg_self (x : Syn) : -x = x := by
  funext i
  have : ∀ y : ZMod 2, -y = y := by decide
  exact this (x i)

/-- **Additivity.**  The syndrome of a symmetric difference is the sum of the
syndromes: symmetric difference is addition of words, and `syn` is linear. -/
theorem syn_symmDiff (a b : Word) : syn (symmDiff a b) = syn a + syn b := by
  have hsub : a ∩ b ⊆ a ∪ b := (inter_subset_left).trans subset_union_left
  have hsd : symmDiff a b = (a ∪ b) \ (a ∩ b) := by
    rw [symmDiff_eq_sup_sdiff_inf]; rfl
  have h1 : ∑ k ∈ (a ∪ b) \ (a ∩ b), col k
      = (∑ k ∈ a ∪ b, col k) - ∑ k ∈ a ∩ b, col k := Finset.sum_sdiff_eq_sub hsub
  have h2 : (∑ k ∈ a ∪ b, col k) + ∑ k ∈ a ∩ b, col k
      = (∑ k ∈ a, col k) + ∑ k ∈ b, col k := Finset.sum_union_inter
  unfold syn
  rw [hsd, h1, sub_eq_add_neg, neg_self]
  linear_combination (norm := abel) h2

theorem syn_empty : syn (∅ : Word) = 0 := by simp [syn]

theorem isCodeword_empty : IsCodeword (∅ : Word) := syn_empty

/-- Two words have the same syndrome exactly when they differ by a codeword.
Syndromes therefore name the cosets of the code. -/
theorem syn_eq_iff_isCodeword_symmDiff (a b : Word) :
    syn a = syn b ↔ IsCodeword (symmDiff a b) := by
  unfold IsCodeword
  rw [syn_symmDiff]
  constructor
  · intro h
    rw [h]
    funext i
    have hy : ∀ y : ZMod 2, y + y = 0 := by decide
    exact hy _
  · intro h
    funext i
    have hi := congrFun h i
    simp only [Pi.add_apply, Pi.zero_apply] at hi
    have hx : ∀ x y : ZMod 2, x + y = 0 → x = y := by decide
    exact hx _ _ hi

/-- The syndrome is unchanged by adding a codeword. -/
theorem syn_symmDiff_codeword {v c : Word} (hc : IsCodeword c) :
    syn (symmDiff v c) = syn v := by
  rw [syn_symmDiff, hc, add_zero]

/-! ## Distance -/

theorem hdist_comm (a b : Word) : hdist a b = hdist b a := by
  unfold hdist; rw [symmDiff_comm]

theorem hdist_eq_zero_iff {a b : Word} : hdist a b = 0 ↔ a = b := by
  unfold hdist
  rw [Finset.card_eq_zero]
  constructor
  · intro h; exact symmDiff_eq_bot.mp h
  · rintro rfl; simp

/-- The symmetric difference of `v` with a difference word recovers the other
word: this is the bijection between codewords near `v` and coset elements. -/
theorem symmDiff_symmDiff_self (v u : Word) : symmDiff v (symmDiff v u) = u :=
  symmDiff_symmDiff_cancel_left v u

/-- Distance to `v`, measured as the weight of the coset element. -/
theorem hdist_eq_wt_symmDiff (v c : Word) : hdist v c = wt (symmDiff v c) := rfl

end GLM.Golay24
