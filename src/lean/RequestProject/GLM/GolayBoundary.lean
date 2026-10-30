/-
# The snap boundary: nearest-codeword reading is true up to weight 3 and untrue at 4

The GLM's substrate layer "snaps" a pattern to the nearest Golay codeword.  The
repository records a defect of that operation: it corrects errors of weight at
most 3, not 4.  This file proves that this is not an implementation accident but
a boundary of the layer itself.

For any code of minimum distance `8` (the Golay `[24,12,8]` code is one):

* `snap_unique_of_le_three` — a pattern within Hamming distance `3` of a codeword
  is within distance `3` of *no other* codeword, so nearest-codeword reading
  returns the true codeword.  The substrate layer is exactly right in this range.
* `snap_ambiguous_at_four` — as soon as two codewords are at distance `8`, there
  is a pattern at distance `4` from both.  Nearest-codeword reading has no
  correct answer there: the information saying which codeword was sent is gone.

Nothing here uses the specific structure of the Golay code, so the statements
apply verbatim to the `[24,12,8]` code used by the substrate layer.
-/
import Mathlib

namespace GLM.Golay

open Finset

variable {n : ℕ}

/-- The coordinates on which two bit patterns differ. -/
def diffSet (a b : Fin n → Bool) : Finset (Fin n) := {i | a i ≠ b i}

/-- Hamming distance between two bit patterns. -/
def hdist (a b : Fin n → Bool) : ℕ := #(diffSet a b)

lemma diffSet_comm (a b : Fin n → Bool) : diffSet a b = diffSet b a := by
  ext i; simp [diffSet, ne_comm]

lemma hdist_comm (a b : Fin n → Bool) : hdist a b = hdist b a := by
  unfold hdist; rw [diffSet_comm]

lemma hdist_eq_zero_iff {a b : Fin n → Bool} : hdist a b = 0 ↔ a = b := by
  unfold hdist diffSet
  rw [Finset.card_eq_zero, Finset.filter_eq_empty_iff]
  constructor
  · intro h; funext i; by_contra hc; exact h (Finset.mem_univ i) hc
  · rintro rfl i _; simp

lemma hdist_triangle (a b c : Fin n → Bool) : hdist a c ≤ hdist a b + hdist b c := by
  have hsub : diffSet a c ⊆ diffSet a b ∪ diffSet b c := by
    intro i hi
    simp only [diffSet, Finset.mem_filter, Finset.mem_univ, true_and] at hi
    simp only [diffSet, Finset.mem_union, Finset.mem_filter, Finset.mem_univ, true_and]
    by_contra hc
    push_neg at hc
    exact hi (hc.1.trans hc.2)
  calc hdist a c ≤ #(diffSet a b ∪ diffSet b c) := Finset.card_le_card hsub
    _ ≤ #(diffSet a b) + #(diffSet b c) := Finset.card_union_le _ _

/-! ## Inside the radius: the layer is exactly right -/

/-- **Unique decoding up to weight 3.**  In a code of minimum distance `8`, a
pattern within distance `3` of a codeword is within distance `3` of no other
codeword: snapping recovers the codeword that was sent. -/
theorem snap_unique_of_le_three {C : Set (Fin n → Bool)}
    (hmin : ∀ c ∈ C, ∀ c' ∈ C, c ≠ c' → 8 ≤ hdist c c')
    {v c c' : Fin n → Bool} (hc : c ∈ C) (hc' : c' ∈ C)
    (h : hdist v c ≤ 3) (h' : hdist v c' ≤ 3) : c = c' := by
  by_contra hne
  have hcc' : 8 ≤ hdist c c' := hmin c hc c' hc' hne
  have htri : hdist c c' ≤ hdist c v + hdist v c' := hdist_triangle c v c'
  rw [hdist_comm c v] at htri
  omega

/-! ## At the radius: the layer has no correct answer -/

/-- The pattern obtained from `c` by flipping the coordinates in `s`. -/
def flipOn (c : Fin n → Bool) (s : Finset (Fin n)) : Fin n → Bool :=
  fun i => if i ∈ s then !c i else c i

lemma diffSet_flipOn (c : Fin n → Bool) (s : Finset (Fin n)) :
    diffSet c (flipOn c s) = s := by
  ext i; by_cases hi : i ∈ s <;> simp [diffSet, flipOn, hi]

lemma hdist_flipOn (c : Fin n → Bool) (s : Finset (Fin n)) : hdist c (flipOn c s) = #s := by
  unfold hdist; rw [diffSet_flipOn]

lemma diffSet_flipOn_of_subset {c c' : Fin n → Bool} {s : Finset (Fin n)}
    (hs : s ⊆ diffSet c c') : diffSet (flipOn c s) c' = diffSet c c' \ s := by
  ext i
  by_cases hi : i ∈ s
  · have hne : c i ≠ c' i := by simpa [diffSet] using hs hi
    cases hci : c i <;> cases hci' : c' i <;> simp_all [diffSet, flipOn]
  · simp [diffSet, flipOn, hi]

lemma hdist_flipOn_of_subset {c c' : Fin n → Bool} {s : Finset (Fin n)}
    (hs : s ⊆ diffSet c c') : hdist (flipOn c s) c' = hdist c c' - #s := by
  unfold hdist
  rw [diffSet_flipOn_of_subset hs, Finset.card_sdiff, Finset.inter_eq_left.2 hs]

/-- **Ambiguity at weight 4.**  If two codewords sit at the minimum distance `8`,
flipping half of the coordinates on which they differ produces a pattern at
distance exactly `4` from each.  Nearest-codeword reading cannot choose: the
information identifying the sent codeword has been lost. -/
theorem snap_ambiguous_at_four {c c' : Fin n → Bool} (h : hdist c c' = 8) :
    ∃ v : Fin n → Bool, hdist v c = 4 ∧ hdist v c' = 4 := by
  obtain ⟨s, hs, hcard⟩ : ∃ s ⊆ diffSet c c', #s = 4 := by
    refine Finset.exists_subset_card_eq ?_
    unfold hdist at h
    omega
  refine ⟨flipOn c s, ?_, ?_⟩
  · rw [hdist_comm, hdist_flipOn, hcard]
  · rw [hdist_flipOn_of_subset hs, h, hcard]

/-- The two candidate readings of such a pattern really are different codewords,
so the ambiguity is genuine. -/
theorem snap_ambiguous_ne {c c' : Fin n → Bool} (h : hdist c c' = 8) : c ≠ c' := by
  intro hcc
  rw [hcc, hdist_eq_zero_iff.2 rfl] at h
  exact absurd h (by norm_num)

/-- The boundary, stated as one theorem: correction is guaranteed at weight `≤ 3`
and impossible at weight `4`. -/
theorem snap_boundary_at_three {C : Set (Fin n → Bool)}
    (hmin : ∀ c ∈ C, ∀ c' ∈ C, c ≠ c' → 8 ≤ hdist c c')
    {c c' : Fin n → Bool} (h : hdist c c' = 8) :
    (∀ v : Fin n → Bool, ∀ d ∈ C, ∀ d' ∈ C, hdist v d ≤ 3 → hdist v d' ≤ 3 → d = d')
      ∧ ∃ v : Fin n → Bool, c ≠ c' ∧ hdist v c = 4 ∧ hdist v c' = 4 := by
  refine ⟨fun v d hd d' hd' h1 h2 => snap_unique_of_le_three hmin hd hd' h1 h2, ?_⟩
  obtain ⟨v, hv, hv'⟩ := snap_ambiguous_at_four h
  exact ⟨v, snap_ambiguous_ne h, hv, hv'⟩

end GLM.Golay
