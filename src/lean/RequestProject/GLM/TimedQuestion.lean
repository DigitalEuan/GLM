module

public import Mathlib

/-!
# Time and the question: resolving a tie by information that arrives later

The formal half of `studies/TIMED_QUESTION_STUDY.md` (Phase 145). The Python
module `glm_universal/reasoning/timed_question.py` keeps a tie — several
candidates no read in hand can separate — open as a live set, and lets
information arrive *later*: either passively, as observations a later step
happens to make (waiting), or actively, as the answer to a question the GLM
puts because it has worked out exactly what it needs to know (asking). At
this stage of the system the answers are supplied by the developer; later a
user supplies them. This file proves what makes that sound and economical.

* `after_eq_filter`, `after_subset`, `after_perm` — information only ever
  removes candidates, and the order in which it arrives does not matter.
* `truth_mem_after`, `resolved_eq_truth`, `contradicted_not_truthful` — if
  every answer is true of the truth and the truth was a candidate, the truth
  is never removed, a tie left with one candidate holds the truth, and a tie
  left with none proves some answer was false.
* `no_time_resolves`, `no_coordinate_question_resolves` — waiting cannot help
  when every observation that can arrive takes one value on the whole tie:
  then the tie never shrinks. In particular, for a junction (carriers with
  equal coordinates) no observation that is a function of the coordinates
  ever resolves it; the GLM must ask for something outside the coordinates.
* `prune_ssubset_iff`, `splits_iff` — a question is worth asking exactly
  when it takes two values on the live set; then every answer removes
  something.
* `exists_halving`, `halveRun_eq_singleton` — there is always a yes/no
  question that leaves at most half (rounded up) of the live set, and asking
  such questions resolves a tie of `n` candidates in `Nat.clog 2 n`
  questions, to the truth.
* `adversary`, `questions_needed`, `optimal` — no adaptive yes/no strategy
  does better: with fewer than `Nat.clog 2 n` questions there is always a
  truth for which the tie is still open. So asking halving questions is
  asking for exactly the information needed, and no less.
-/

@[expose] public section

namespace GLM.TimedQuestion

open Finset

variable {α β : Type*}

section Prune

variable [DecidableEq β]

/-- The candidates of `S` consistent with the answer `b` to the question `q`. -/
def prune (S : Finset α) (q : α → β) (b : β) : Finset α :=
  S.filter (fun c => q c = b)

/-- The live set after a history of questions and their answers, in the order
they arrived. -/
def after (S : Finset α) : List ((α → β) × β) → Finset α
  | [] => S
  | p :: h => after (prune S p.1 p.2) h

/-- A history is truthful for `t` when every answer is the answer `t` gives. -/
def Truthful (t : α) (h : List ((α → β) × β)) : Prop :=
  ∀ p ∈ h, p.2 = p.1 t

theorem after_eq_filter (S : Finset α) (h : List ((α → β) × β)) :
    after S h = S.filter (fun c => ∀ p ∈ h, p.1 c = p.2) := by
  induction h generalizing S with
  | nil => simp [after]
  | cons p h ih =>
    ext c
    simp only [after, ih, prune, mem_filter, List.mem_cons, forall_eq_or_imp]
    tauto

/-- Information only removes candidates. -/
theorem after_subset (S : Finset α) (h : List ((α → β) × β)) : after S h ⊆ S := by
  rw [after_eq_filter]; exact filter_subset _ _

/-- The order in which the information arrives does not matter. -/
theorem after_perm (S : Finset α) {h h' : List ((α → β) × β)} (hp : h.Perm h') :
    after S h = after S h' := by
  simp only [after_eq_filter]
  ext c
  simp only [mem_filter]
  constructor
  · rintro ⟨hc, hall⟩; exact ⟨hc, fun p hp' => hall p (hp.mem_iff.mpr hp')⟩
  · rintro ⟨hc, hall⟩; exact ⟨hc, fun p hp' => hall p (hp.mem_iff.mp hp')⟩

/-- Later information appended to a history only removes more. -/
theorem after_append (S : Finset α) (h h' : List ((α → β) × β)) :
    after S (h ++ h') = after (after S h) h' := by
  induction h generalizing S with
  | nil => rfl
  | cons p h ih => simp [after, ih]

/-- Truthful answers never remove the truth. -/
theorem truth_mem_after {S : Finset α} {h : List ((α → β) × β)} {t : α}
    (ht : t ∈ S) (htr : Truthful t h) : t ∈ after S h := by
  rw [after_eq_filter, mem_filter]
  exact ⟨ht, fun p hp => (htr p hp).symm⟩

/-- A tie left with one candidate holds the truth. -/
theorem resolved_eq_truth {S : Finset α} {h : List ((α → β) × β)} {t c : α}
    (ht : t ∈ S) (htr : Truthful t h) (hres : after S h = {c}) : t = c := by
  have := truth_mem_after ht htr
  rw [hres, mem_singleton] at this
  exact this

/-- A tie left with no candidate proves that the truth was not a candidate or
that some answer was false: it is reported, never resolved. -/
theorem contradicted_not_truthful {S : Finset α} {h : List ((α → β) × β)}
    (hempty : after S h = ∅) (t : α) : ¬ (t ∈ S ∧ Truthful t h) := by
  rintro ⟨ht, htr⟩
  have := truth_mem_after ht htr
  rw [hempty] at this
  exact absurd this (notMem_empty t)

/-- Once resolved to the truth, later truthful information keeps it resolved. -/
theorem resolved_stays {S : Finset α} {h h' : List ((α → β) × β)} {t : α}
    (ht : t ∈ S) (htr : Truthful t (h ++ h')) (hres : after S h = {t}) :
    after S (h ++ h') = {t} := by
  rw [after_append, hres]
  apply Subset.antisymm
  · exact after_subset _ _
  · intro c hc
    rw [mem_singleton] at hc
    subst hc
    have := truth_mem_after (S := S) ht htr
    rwa [after_append, hres] at this

/-- **Waiting cannot help** when every observation that arrives takes a single
value on the tie: truthful observations then remove nothing. -/
theorem no_time_resolves {S : Finset α} {h : List ((α → β) × β)} {t : α}
    (htr : Truthful t h)
    (hconst : ∀ p ∈ h, ∀ c ∈ S, p.1 c = p.1 t) : after S h = S := by
  rw [after_eq_filter]
  apply filter_true_of_mem
  intro c hc p hp
  rw [hconst p hp c hc, htr p hp]

/-- So a tie of two or more candidates on which every arriving observation is
constant is never resolved by waiting. -/
theorem no_time_resolves_card {S : Finset α} {h : List ((α → β) × β)} {t : α}
    (htr : Truthful t h)
    (hconst : ∀ p ∈ h, ∀ c ∈ S, p.1 c = p.1 t) (hcard : 2 ≤ S.card) :
    2 ≤ (after S h).card := by
  rwa [no_time_resolves htr hconst]

/-- **A junction is never resolved by its coordinates.** If the candidates
share their coordinates and every observation is a function of the
coordinates, waiting resolves nothing: the GLM has to ask for something the
coordinates do not carry. -/
theorem no_coordinate_question_resolves {γ : Type*} (coord : α → γ)
    {S : Finset α} {h : List ((α → β) × β)} {t : α}
    (htr : Truthful t h)
    (hjunction : ∀ c ∈ S, coord c = coord t)
    (hfactor : ∀ p ∈ h, ∃ g : γ → β, p.1 = g ∘ coord) : after S h = S := by
  apply no_time_resolves htr
  intro p hp c hc
  obtain ⟨g, hg⟩ := hfactor p hp
  rw [hg, Function.comp_apply, Function.comp_apply, hjunction c hc]

/-- An answer removes something exactly when some candidate gives another. -/
theorem prune_ssubset_iff (S : Finset α) (q : α → β) (b : β) :
    prune S q b ⊂ S ↔ ∃ c ∈ S, q c ≠ b := by
  unfold prune
  constructor
  · intro hss
    by_contra hne
    push_neg at hne
    exact hss.ne (filter_true_of_mem hne)
  · rintro ⟨c, hc, hqc⟩
    refine Finset.ssubset_iff_subset_ne.mpr ⟨filter_subset _ _, fun heq => ?_⟩
    have : c ∈ S.filter (fun c => q c = b) := by rw [heq]; exact hc
    exact hqc (mem_filter.mp this).2

/-- **A question is worth asking exactly when it takes two values on the live
set**: then every answer removes at least one candidate. -/
theorem splits_iff {S : Finset α} (hS : S.Nonempty) (q : α → β) :
    (∀ b, prune S q b ⊂ S) ↔ ∃ a ∈ S, ∃ c ∈ S, q a ≠ q c := by
  constructor
  · intro hall
    obtain ⟨c, hc⟩ := hS
    obtain ⟨d, hd, hqd⟩ := (prune_ssubset_iff S q (q c)).mp (hall (q c))
    exact ⟨d, hd, c, hc, hqd⟩
  · rintro ⟨a, ha, c, hc, hac⟩ b
    rw [prune_ssubset_iff]
    by_cases hb : q a = b
    · exact ⟨c, hc, fun h => hac (hb.trans h.symm)⟩
    · exact ⟨a, ha, hb⟩

end Prune

/-! ### Yes/no questions: how many are needed -/

/-- An adaptive yes/no strategy: the next question as a function of the answers
received so far (most recent first). -/
abbrev Strategy (α : Type*) := List Bool → α → Bool

/-- The live set after `k` questions of the strategy `σ`, answered truthfully
for `t`. -/
def liveRun : ℕ → Finset α → Strategy α → α → Finset α
  | 0, S, _, _ => S
  | k + 1, S, σ, t => liveRun k (prune S (σ []) (σ [] t)) (fun h => σ (σ [] t :: h)) t

theorem card_prune_add (S : Finset α) (q : α → Bool) :
    (prune S q true).card + (prune S q false).card = S.card := by
  unfold prune
  have := card_filter_add_card_filter_not (s := S) (fun c => q c = true)
  simpa using this

/-- **The adversary.** Whatever adaptive strategy of yes/no questions is used,
some candidate, answered for truthfully, leaves at least `|S| / 2^k` candidates
after `k` questions. -/
theorem adversary (k : ℕ) :
    ∀ (S : Finset α) (σ : Strategy α), S.Nonempty →
      ∃ t ∈ S, S.card ≤ 2 ^ k * (liveRun k S σ t).card := by
  induction k with
  | zero =>
    intro S σ ⟨t, ht⟩
    exact ⟨t, ht, by simp [liveRun]⟩
  | succ k ih =>
    intro S σ hS
    have hsum := card_prune_add S (σ [])
    -- choose the larger half
    obtain ⟨b, hb⟩ : ∃ b : Bool, S.card ≤ 2 * (prune S (σ []) b).card := by
      by_cases h : (prune S (σ []) false).card ≤ (prune S (σ []) true).card
      · exact ⟨true, by omega⟩
      · exact ⟨false, by omega⟩
    have hP : (prune S (σ []) b).Nonempty := by
      rw [← card_pos]
      have := hS.card_pos
      omega
    obtain ⟨t, ht, hcard⟩ := ih (prune S (σ []) b) (fun h => σ (b :: h)) hP
    have hqt : σ [] t = b := (mem_filter.mp ht).2
    refine ⟨t, (mem_filter.mp ht).1, ?_⟩
    simp only [liveRun, hqt]
    calc S.card ≤ 2 * (prune S (σ []) b).card := hb
      _ ≤ 2 * (2 ^ k * (liveRun k (prune S (σ []) b) (fun h => σ (b :: h)) t).card) :=
          Nat.mul_le_mul_left 2 hcard
      _ = 2 ^ (k + 1) * (liveRun k (prune S (σ []) b) (fun h => σ (b :: h)) t).card := by
          ring

/-- **Fewer questions cannot always resolve.** If `|S| > 2^k`, every adaptive
strategy of `k` yes/no questions leaves some truth with the tie still open. -/
theorem questions_needed {S : Finset α} {k : ℕ} (hk : 2 ^ k < S.card) (σ : Strategy α) :
    ∃ t ∈ S, 2 ≤ (liveRun k S σ t).card := by
  have hS : S.Nonempty := by
    rw [← card_pos]; have := Nat.one_le_two_pow (n := k); omega
  obtain ⟨t, ht, hcard⟩ := adversary k S σ hS
  refine ⟨t, ht, ?_⟩
  by_contra hlt
  push_neg at hlt
  have : 2 ^ k * (liveRun k S σ t).card ≤ 2 ^ k * 1 :=
    Nat.mul_le_mul_left _ (by omega)
  omega

/-- **A halving question always exists**: membership in a subset holding half
the live set leaves at most half (rounded up) whichever way it is answered. -/
theorem exists_halving (S : Finset α) :
    ∃ q : α → Bool, ∀ b, (prune S q b).card ≤ (S.card + 1) / 2 := by
  classical
  obtain ⟨T, hTS, hTcard⟩ := exists_subset_card_eq (s := S) (n := S.card / 2)
    (Nat.div_le_self _ _)
  refine ⟨fun c => decide (c ∈ T), fun b => ?_⟩
  cases b with
  | true =>
    have : prune S (fun c => decide (c ∈ T)) true = T := by
      ext c
      simp only [prune, mem_filter, decide_eq_true_eq]
      exact ⟨fun h => h.2, fun h => ⟨hTS h, h⟩⟩
    rw [this, hTcard]
    omega
  | false =>
    have : prune S (fun c => decide (c ∈ T)) false = S \ T := by
      ext c
      simp [prune, mem_filter, mem_sdiff]
    rw [this, card_sdiff_of_subset hTS, hTcard]
    omega

/-- A chosen halving question for each live set. -/
noncomputable def halveQ (S : Finset α) : α → Bool :=
  Classical.choose (exists_halving S)

theorem halveQ_spec (S : Finset α) (b : Bool) :
    (prune S (halveQ S) b).card ≤ (S.card + 1) / 2 :=
  Classical.choose_spec (exists_halving S) b

/-- Asking a halving question of the current live set, `k` times, answered
truthfully for `t`. -/
noncomputable def halveRun : ℕ → Finset α → α → Finset α
  | 0, S, _ => S
  | k + 1, S, t => halveRun k (prune S (halveQ S) (halveQ S t)) t

theorem halveRun_card_le (k : ℕ) :
    ∀ (S : Finset α) (t : α), S.card ≤ 2 ^ k → (halveRun k S t).card ≤ 1 := by
  induction k with
  | zero => intro S t h; simpa [halveRun] using h
  | succ k ih =>
    intro S t h
    apply ih
    have := halveQ_spec S (halveQ S t)
    have h2 : (S.card + 1) / 2 ≤ 2 ^ k := by
      rw [pow_succ] at h; omega
    exact this.trans h2

theorem mem_halveRun (k : ℕ) :
    ∀ (S : Finset α) (t : α), t ∈ S → t ∈ halveRun k S t := by
  induction k with
  | zero => intro S t h; simpa [halveRun] using h
  | succ k ih =>
    intro S t h
    apply ih
    simp [prune, h]

/-- Halving questions resolve a tie within `S.card ≤ 2^k` in `k` questions,
and to the truth. -/
theorem halveRun_eq_singleton {S : Finset α} {t : α} {k : ℕ} (ht : t ∈ S)
    (hk : S.card ≤ 2 ^ k) : halveRun k S t = {t} := by
  have hmem := mem_halveRun k S t ht
  have hle := halveRun_card_le k S t hk
  rw [eq_singleton_iff_unique_mem]
  exact ⟨hmem, fun x hx => card_le_one.mp hle x hx t hmem⟩

/-- **Asking for exactly what is needed.** `Nat.clog 2 |S|` halving questions
resolve every truth in `S`, and no adaptive strategy of fewer yes/no questions
resolves every truth. -/
theorem optimal (S : Finset α) :
    (∀ t ∈ S, halveRun (Nat.clog 2 S.card) S t = {t}) ∧
    (∀ k < Nat.clog 2 S.card, ∀ σ : Strategy α, ∃ t ∈ S, 2 ≤ (liveRun k S σ t).card) := by
  refine ⟨fun t ht => halveRun_eq_singleton ht (Nat.le_pow_clog one_lt_two _), ?_⟩
  intro k hk σ
  exact questions_needed ((Nat.lt_clog_iff_pow_lt one_lt_two).mp hk) σ

/-- The study's six-way Golay tie: three questions, and two are not enough. -/
theorem six_needs_three : Nat.clog 2 6 = 3 := by decide

end GLM.TimedQuestion
