/-
# The UBP laws absorbed: the two corrections the GLM now answers with

`studies/LAW_ABSORPTION_STUDY.md` (Phase 75) turns the surviving UBP laws into
facts the GLM computes about its own substrate
(`glm_universal.reasoning.law_absorption`).  Two of those facts correct a law
rather than restate it, and this file proves the corrections.

Each of the 24 bits is flipped independently with probability `p`; an error
pattern `e` then has probability `p ^ wt e * (1 - p) ^ (24 - wt e)`
(`patternProb`), and these add up to one over all `2²⁴` patterns
(`total_prob`).

* **The storage law, corrected.** `LAW_STORAGE_HARDENED_001` said a hardened
  store keeps 100% integrity at noise up to 3%.  Complete decoding is right
  exactly on the patterns that are the unique lightest word of their coset
  (`GLM.LawRegister.unique_leader_iff`: the patterns of weight at most 3).  The
  probability of that, `rightProb p`, is strictly below one at every
  `0 < p < 1` (`right_prob_lt_one`) and equal to one exactly at `p = 0`
  (`right_prob_eq_one_iff`).  What holds without exception is the worst-case
  form: every pattern of at most three flips is corrected, and some pattern of
  four is not (`worst_case_integrity`).
* **The decoder's confidence, and its refusal.** Below rate `1/2` the unique
  coset leader is strictly the most probable error of its coset
  (`leader_most_likely`), so complete decoding is the maximum-a-posteriori
  decision; two patterns of equal weight are equally probable
  (`equal_weight_equal_prob`), so at a weight-4 coset each of the six tied
  codewords has posterior probability at most `1/6`
  (`tie_posterior_le_sixth`) and no single answer is licensed.
* **An odd number of flips is never refused** (`odd_error_never_refused`): the
  code is even, so a tie needs an even error, and every odd error of five or
  more flips is miscorrected without warning (`odd_heavy_miscorrected`).  This
  sharpens the register's "fourth flip" law: the deep hole is reached only by
  an even number of flips.
-/
import Mathlib
import RequestProject.GLM.LawRegister

namespace GLM.LawAbsorption

open Finset GLM.Golay24 GLM.LawRegister

/-- The probability of the error pattern `e` when each of the 24 bits flips
independently with probability `p`. -/
def patternProb (p : ℝ) (e : Word) : ℝ := p ^ wt e * (1 - p) ^ (24 - wt e)

/-- The pattern probabilities add up to one. -/
theorem total_prob (p : ℝ) : ∑ e : Word, patternProb p e = 1 := by
  have h := Finset.sum_pow_mul_eq_add_pow p (1 - p) (univ : Finset (Fin 24))
  rw [Finset.powerset_univ] at h
  simp only [card_univ, Fintype.card_fin, add_sub_cancel, one_pow] at h
  exact h

/-- A heavier pattern is less probable below rate `1/2`. -/
theorem pow_mul_lt_of_lt {p : ℝ} (hp0 : 0 < p) (hp : p < 1 / 2) {a b : ℕ} (hab : b < a)
    (ha : a ≤ 24) : p ^ a * (1 - p) ^ (24 - a) < p ^ b * (1 - p) ^ (24 - b) := by
  have hq : p < 1 - p := by linarith
  have hq0 : 0 < 1 - p := by linarith
  obtain ⟨k, rfl⟩ : ∃ k, a = b + (k + 1) := ⟨a - b - 1, by omega⟩
  have e1 : 24 - b = (24 - (b + (k + 1))) + (k + 1) := by omega
  have hpk : p ^ (k + 1) < (1 - p) ^ (k + 1) := pow_lt_pow_left₀ hq hp0.le (by omega)
  have := mul_lt_mul_of_pos_left hpk
    (mul_pos (pow_pos hp0 b) (pow_pos hq0 (24 - (b + (k + 1)))))
  calc p ^ (b + (k + 1)) * (1 - p) ^ (24 - (b + (k + 1)))
      = p ^ b * (1 - p) ^ (24 - (b + (k + 1))) * p ^ (k + 1) := by rw [pow_add]; ring
    _ < p ^ b * (1 - p) ^ (24 - (b + (k + 1))) * (1 - p) ^ (k + 1) := this
    _ = p ^ b * (1 - p) ^ (24 - b) := by rw [e1, pow_add]; ring

/-- The first tetrad, a pattern of four flips. -/
def tetrad0 : Word := {0, 1, 2, 3}

theorem wt_tetrad0 : wt tetrad0 = 4 := by decide

theorem not_leader_tetrad0 : ¬ IsUniqueLeader tetrad0 := by
  rw [unique_leader_iff, wt_tetrad0]; omega

open scoped Classical in
/-- The probability that complete decoding is right: the error was the unique
lightest word of its coset. -/
noncomputable def rightProb (p : ℝ) : ℝ :=
  ∑ e ∈ univ.filter IsUniqueLeader, patternProb p e

open scoped Classical in
/-- The right-probability and the probability of everything else add to one. -/
theorem right_add_rest (p : ℝ) :
    rightProb p + ∑ e ∈ univ.filter (fun e => ¬ IsUniqueLeader e), patternProb p e = 1 := by
  unfold rightProb
  rw [Finset.sum_filter_add_sum_filter_not, total_prob]

open scoped Classical in
/-- **The storage law, corrected: never certain at a positive noise rate.** -/
theorem right_prob_lt_one {p : ℝ} (hp0 : 0 < p) (hp1 : p < 1) : rightProb p < 1 := by
  have hq0 : 0 < 1 - p := by linarith
  have hpos : 0 < patternProb p tetrad0 := by unfold patternProb; positivity
  have hle : patternProb p tetrad0 ≤
      ∑ e ∈ univ.filter (fun e => ¬ IsUniqueLeader e), patternProb p e :=
    Finset.single_le_sum (f := patternProb p)
      (fun e _ => by unfold patternProb; positivity)
      (by simp [not_leader_tetrad0])
  linarith [right_add_rest p]

open scoped Classical in
/-- Certain exactly at noise zero. -/
theorem right_prob_eq_one_iff {p : ℝ} (hp0 : 0 ≤ p) (hp1 : p ≤ 1) :
    rightProb p = 1 ↔ p = 0 := by
  constructor
  · intro h
    by_contra hne
    rcases lt_or_eq_of_le hp1 with hlt | heq
    · exact absurd h (ne_of_lt (right_prob_lt_one (lt_of_le_of_ne hp0 (Ne.symm hne)) hlt))
    · subst heq
      have : rightProb 1 = 0 := by
        unfold rightProb
        refine Finset.sum_eq_zero fun e he => ?_
        have h3 := (unique_leader_iff e).1 (Finset.mem_filter.1 he).2
        unfold patternProb
        rw [sub_self, zero_pow (by omega), mul_zero]
      linarith
  · rintro rfl
    have hrest : ∑ e ∈ univ.filter (fun e => ¬ IsUniqueLeader e), patternProb 0 e = 0 := by
      refine Finset.sum_eq_zero fun e he => ?_
      have h4 : ¬ wt e ≤ 3 := fun h =>
        (Finset.mem_filter.1 he).2 ((unique_leader_iff e).2 h)
      unfold patternProb
      rw [zero_pow (by omega), zero_mul]
    linarith [right_add_rest 0]

/-- **What does hold without exception**: every pattern of at most three flips
is corrected, and some pattern of four is not. -/
theorem worst_case_integrity :
    (∀ e : Word, wt e ≤ 3 → IsUniqueLeader e) ∧
      ∃ e : Word, wt e = 4 ∧ ¬ IsUniqueLeader e :=
  ⟨fun e h => (unique_leader_iff e).2 h, tetrad0, wt_tetrad0, not_leader_tetrad0⟩

/-- **Complete decoding is the maximum-a-posteriori decision below rate 1/2**:
the unique leader is strictly more probable than every other error with the
same syndrome. -/
theorem leader_most_likely {p : ℝ} (hp0 : 0 < p) (hp : p < 1 / 2) {e u : Word}
    (he : IsUniqueLeader e) (hsu : syn u = syn e) (hne : u ≠ e) :
    patternProb p u < patternProb p e := by
  have hlt := he u hsu hne
  have hu : wt u ≤ 24 := by
    have := Finset.card_le_univ u
    simpa [wt] using this
  exact pow_mul_lt_of_lt hp0 hp hlt hu

/-- Two patterns of equal weight are equally probable. -/
theorem equal_weight_equal_prob (p : ℝ) {e u : Word} (h : wt u = wt e) :
    patternProb p u = patternProb p e := by
  unfold patternProb; rw [h]

open scoped Classical in
/-- **At a six-way tie no answer is licensed**: each of the six tied codewords
of a weight-4 coset has posterior probability at most `1/6`. -/
theorem tie_posterior_le_sixth {p : ℝ} (hp0 : 0 < p) (hp1 : p < 1) {t : Word}
    (ht : wt t = 4) :
    patternProb p t / ∑ u ∈ univ.filter (fun u => syn u = syn t), patternProb p u ≤ 1 / 6 := by
  have hq0 : 0 < 1 - p := by linarith
  have hnn : ∀ u : Word, 0 ≤ patternProb p u := fun u => by unfold patternProb; positivity
  have hpos : 0 < patternProb p t := by unfold patternProb; positivity
  have hsix : ∑ u ∈ tetrads.filter (fun u => syn u = syn t), patternProb p u =
      6 * patternProb p t := by
    rw [Finset.sum_congr rfl (fun u hu => equal_weight_equal_prob p
      ((mem_tetrads.1 (Finset.mem_filter.1 hu).1).trans ht.symm)),
      Finset.sum_const, tetrad_class_card ht, nsmul_eq_mul]
    norm_num
  have hsub : tetrads.filter (fun u => syn u = syn t) ⊆
      univ.filter (fun u => syn u = syn t) := by
    intro u hu
    simp only [Finset.mem_filter] at hu ⊢
    exact ⟨Finset.mem_univ _, hu.2⟩
  have hge := Finset.sum_le_sum_of_subset_of_nonneg hsub (fun u _ _ => hnn u)
  rw [hsix] at hge
  have hS : 0 < ∑ u ∈ univ.filter (fun u => syn u = syn t), patternProb p u := by linarith
  rw [div_le_iff₀ hS]
  linarith

/-! ## An odd number of flips is never refused -/

/-- The weight of a symmetric difference has the parity of the sum of the two
weights. -/
theorem card_symmDiff_parity (e u : Word) :
    (symmDiff e u).card + 2 * (e ∩ u).card = e.card + u.card := by
  have h1 := Finset.card_sdiff_add_card_inter e u
  have h2 := Finset.card_sdiff_add_card_inter u e
  have hd : Disjoint (e \ u) (u \ e) := disjoint_sdiff_sdiff
  have h3 : (symmDiff e u).card = (e \ u).card + (u \ e).card := by
    rw [symmDiff_def, Finset.sup_eq_union, Finset.card_union_of_disjoint hd]
  rw [Finset.inter_comm u e] at h2
  omega

/-- **An odd error is never refused**: every codeword has even weight, so a
coset carries only one parity, and the six-way ties (coset weight `4`) are all
even. -/
theorem odd_error_never_refused {e : Word} (h : Odd (wt e)) : cosetWt (syn e) ≠ 4 := by
  obtain ⟨u, hsu, hwu⟩ := exists_wt_eq_cosetWt (syn e)
  intro h4
  have hc : IsCodeword (symmDiff e u) := (syn_eq_iff_isCodeword_symmDiff e u).1 hsu.symm
  have hpar := card_symmDiff_parity e u
  have hw : wt u = 4 := by omega
  unfold wt at h hw
  rcases golay_weight_mem hc with h' | h' | h' | h' | h' <;> unfold wt at h' <;>
    rcases h with ⟨k, hk⟩ <;> omega

/-- **So every odd error of five or more flips is miscorrected, silently**: it
is not the unique leader of its coset (so the decoder's answer is not the sent
word) and its coset is not a tie (so the decoder does answer). -/
theorem odd_heavy_miscorrected {e : Word} (h : Odd (wt e)) (h5 : 5 ≤ wt e) :
    ¬ IsUniqueLeader e ∧ cosetWt (syn e) ≠ 4 :=
  ⟨fun hu => by have := (unique_leader_iff e).1 hu; omega, odd_error_never_refused h⟩

end GLM.LawAbsorption
