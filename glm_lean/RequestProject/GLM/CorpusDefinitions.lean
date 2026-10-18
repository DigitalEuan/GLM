module

public import Mathlib

/-!
# The corpus's definitions graded, and a word's place on the lattice (Phase 155)

The formal half of `studies/CORPUS_DEFINITIONS_STUDY.md`.

* `grade_comm`, `grade_le_left`, `grade_le_right`, `grade_mono` — the grade of an answer
  against a gloss (the number of content words they share) is symmetric,
  bounded by either side's size, and monotone in the answer.
* `heldout_clean`, `heldout_keeps`, `heldout_sublist` — the hold-out is
  complete (no surviving sentence contains a held-out gloss as a contiguous
  run), removes nothing else, and only removes.
* `coord_le_cap`, `coord_mono` — a word's coordinate against an anchor lies in
  `[0, 12]` and never decreases when the window count grows with the word and
  anchor counts fixed.
-/

@[expose] public section

namespace GLM.CorpusDefinitions

open Finset

/-! ## The grade -/

section Grade

variable {α : Type*} [DecidableEq α]

/-- The grade of an answer `a` against a gloss `g`: the content words they share. -/
def grade (a g : Finset α) : ℕ := (a ∩ g).card

theorem grade_comm (a g : Finset α) : grade a g = grade g a := by
  unfold grade; rw [inter_comm]

theorem grade_le_left (a g : Finset α) : grade a g ≤ a.card :=
  card_le_card inter_subset_left

theorem grade_le_right (a g : Finset α) : grade a g ≤ g.card :=
  card_le_card inter_subset_right

theorem grade_mono {a a' : Finset α} (h : a ⊆ a') (g : Finset α) :
    grade a g ≤ grade a' g :=
  card_le_card (inter_subset_inter_right h)

end Grade

/-! ## The hold-out -/

section Heldout

variable {α : Type*} [DecidableEq α]

/-- Does sentence `s` contain none of the held-out glosses as a contiguous run? -/
def clean (glosses : List (List α)) (s : List α) : Bool :=
  glosses.all fun p => !decide (p <:+: s)

/-- The corpus with every sentence containing a held-out gloss removed. -/
def heldout (glosses : List (List α)) (corpus : List (List α)) : List (List α) :=
  corpus.filter (clean glosses)

theorem heldout_clean {glosses corpus : List (List α)} {s p : List α}
    (hs : s ∈ heldout glosses corpus) (hp : p ∈ glosses) : ¬ p <:+: s := by
  unfold heldout clean at hs
  rw [List.mem_filter, List.all_eq_true] at hs
  simpa using hs.2 p hp

theorem heldout_keeps {glosses corpus : List (List α)} {s : List α}
    (hs : s ∈ corpus) (hc : ∀ p ∈ glosses, ¬ p <:+: s) :
    s ∈ heldout glosses corpus := by
  unfold heldout clean
  rw [List.mem_filter, List.all_eq_true]
  exact ⟨hs, fun p hp => by simpa using hc p hp⟩

theorem heldout_sublist (glosses corpus : List (List α)) :
    (heldout glosses corpus).Sublist corpus :=
  List.filter_sublist

end Heldout

/-! ## The word coordinate -/

/-- The exact lift `n(w,a)·T² / (n(w)·n(a)·P)` as a rational. -/
def lift (nwa nw na T P : ℕ) : ℚ := (nwa * T ^ 2 : ℚ) / (nw * na * P)

/-- A word's coordinate against an anchor: `0` below the pair support of 2,
otherwise `6 + ⌊log₂ lift⌋` clamped to `[1, 12]`. -/
def coord (nwa nw na T P : ℕ) : ℕ :=
  if nwa < 2 then 0 else (max 1 (min 12 (6 + Int.log 2 (lift nwa nw na T P)))).toNat

theorem coord_le_cap (nwa nw na T P : ℕ) : coord nwa nw na T P ≤ 12 := by
  unfold coord
  split_ifs
  · omega
  · omega

theorem lift_mono {nwa nwa' : ℕ} (h : nwa ≤ nwa') (nw na T P : ℕ) :
    lift nwa nw na T P ≤ lift nwa' nw na T P := by
  unfold lift
  apply div_le_div_of_nonneg_right _ (by positivity)
  gcongr

theorem coord_mono {nwa nwa' : ℕ} (h : nwa ≤ nwa') (nw na T P : ℕ) :
    coord nwa nw na T P ≤ coord nwa' nw na T P := by
  unfold coord
  by_cases h1 : nwa < 2
  · simp [h1]
  · have h2 : ¬ nwa' < 2 := by omega
    simp only [h1, h2, if_false]
    have hl := lift_mono h nw na T P
    have hlog : Int.log 2 (lift nwa nw na T P) ≤ Int.log 2 (lift nwa' nw na T P) := by
      by_cases hz : (T : ℚ) = 0 ∨ (nw * na * P : ℚ) = 0
      · have e : ∀ m : ℕ, lift m nw na T P = 0 := by
          intro m; unfold lift
          rcases hz with hz | hz
          · rw [hz]; simp
          · rw [hz, div_zero]
        rw [e, e]
      · push_neg at hz
        have hpos : 0 < lift nwa nw na T P := by
          unfold lift
          have : (0 : ℚ) < nwa := by exact_mod_cast (show 0 < nwa by omega)
          have hd : (0 : ℚ) < nw * na * P := lt_of_le_of_ne (by positivity) (Ne.symm hz.2)
          have hT : (0 : ℚ) < T ^ 2 := pow_pos (lt_of_le_of_ne (by positivity) (Ne.symm hz.1)) 2
          exact div_pos (mul_pos this hT) hd
        exact Int.log_mono_right hpos hl
    omega

end GLM.CorpusDefinitions
