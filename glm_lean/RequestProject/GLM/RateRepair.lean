module

public import Mathlib

/-!
# The rate repairs: what any rule can promise at a fixed rate

The formal half of `studies/RATE_POSTERIOR_STUDY.md` §4 (Phase 86,
`glm_universal.reasoning.rate_posterior_marks.repair_table`). At a fixed true
rate the reads of a call are independent, so whether the subject's decoding is
right depends only on its own coset class `d`, and the corpus reads carry no
information about it once `d` is known. A rule that decides to answer from
(corpus, subject class) therefore answers class `d` with some mass `a d`, and
is wrong on that mass exactly in the class's error fraction `e d = 1 - conf_r d`.

* `fixed_rate_wrong_eq` — the wrong mass of any such rule is the
  class-by-class sum `Σ_d a d * e d`, with `a d` the answered mass of class
  `d` (the corpus summed out): the residual is an answered-mass average.
* `fixed_rate_keep` — if every class answered with positive mass has error
  fraction at most `1 - t`, the floor's promise holds at that rate.
* `fixed_rate_break` — if every class answered with positive mass has error
  fraction above `1 - t`, and anything is answered, the promise breaks. So no
  rule that ever answers such a class can be repaired by a finer grid or a
  higher guard point: only by never answering it.
-/

@[expose] public section

namespace GLM.RateRepair

open Finset

variable {ι κ K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

omit [LinearOrder K] [IsStrictOrderedRing K] in
/-- **The residual is an answered-mass average.** Corpus outcomes `c ∈ C`
with mass `π c`, subject classes `d ∈ D` with mass `s d` (independent of the
corpus at a fixed rate) and error fraction `e d`; a rule answers the pairs
where `ans c d`. Its wrong mass is the sum over classes of the class's
answered mass times its error fraction. -/
theorem fixed_rate_wrong_eq (C : Finset ι) (D : Finset κ) (π : ι → K)
    (s e : κ → K) (ans : ι → κ → Prop) [∀ c d, Decidable (ans c d)] :
    ∑ c ∈ C, ∑ d ∈ D.filter (ans c), π c * s d * e d
      = ∑ d ∈ D, (∑ c ∈ C.filter (fun c => ans c d), π c * s d) * e d := by
  simp_rw [Finset.sum_filter]
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun d _ => ?_
  rw [Finset.sum_mul]
  refine Finset.sum_congr rfl fun c _ => ?_
  split_ifs <;> simp

/-- **Keeping the promise at a fixed rate.** If every class answered with
positive mass has error fraction at most `1 - t`, the wrong mass is at most
`1 - t` times the answered mass. -/
theorem fixed_rate_keep (D : Finset κ) (a e : κ → K) (t : K)
    (ha : ∀ d ∈ D, 0 ≤ a d) (he : ∀ d ∈ D, 0 < a d → e d ≤ 1 - t) :
    ∑ d ∈ D, a d * e d ≤ (1 - t) * ∑ d ∈ D, a d := by
  rw [Finset.mul_sum]
  refine Finset.sum_le_sum fun d hd => ?_
  rcases (ha d hd).lt_or_eq with h | h
  · rw [mul_comm (1 - t)]
    exact mul_le_mul_of_nonneg_left (he d hd h) h.le
  · rw [← h]; simp

/-- **Breaking the promise at a fixed rate.** If every class answered with
positive mass has error fraction above `1 - t`, and the answered mass is
positive, the wrong mass exceeds `1 - t` times the answered mass. -/
theorem fixed_rate_break (D : Finset κ) (a e : κ → K) (t : K)
    (ha : ∀ d ∈ D, 0 ≤ a d) (he : ∀ d ∈ D, 0 < a d → 1 - t < e d)
    (hpos : 0 < ∑ d ∈ D, a d) :
    (1 - t) * ∑ d ∈ D, a d < ∑ d ∈ D, a d * e d := by
  rw [Finset.mul_sum]
  obtain ⟨d₀, hd₀, h₀⟩ : ∃ d ∈ D, 0 < a d := by
    by_contra hne
    push_neg at hne
    have : ∑ d ∈ D, a d ≤ 0 := Finset.sum_nonpos hne
    linarith
  refine Finset.sum_lt_sum (fun d hd => ?_) ⟨d₀, hd₀, ?_⟩
  · rcases (ha d hd).lt_or_eq with h | h
    · rw [mul_comm (1 - t)]
      exact mul_le_mul_of_nonneg_left (he d hd h).le h.le
    · rw [← h]; simp
  · rw [mul_comm (1 - t)]
    exact mul_lt_mul_of_pos_left (he d₀ hd₀ h₀) h₀

end GLM.RateRepair
