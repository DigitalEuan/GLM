module

public import Mathlib

/-!
# Adversarial replies at the `nearest` ties (Phase 167)

*Created 22 October 2026. Rebuilt 15 November 2026 (Phase 190) from
`studies/ADVERSARIAL_DIALOGUE_STUDY.md`, `reasoning/adversarial_dialogue_study.py`
and the two held files that import it (`ResumedDialogue.lean`,
`StackedDialogue.lean`).*
-/

@[expose] public section

namespace GLM.AdversarialDialogue

variable {ι β : Type*}

/-- The scan's answer: every carrier of `S` is at the least distance from the
question's state `q`. -/
def HeadSet {α : Type*} [MetricSpace α] (c : ι → α) (q : α) (S : Finset ι) : Prop :=
  ∀ i ∈ S, ∀ j, dist q (c i) ≤ dist q (c j)

/-- The live set after a list of replies: the carriers of `S` that every reply
names. -/
def after (S : Finset ι) (replies : List (ι × β)) : Set ι :=
  {i | i ∈ S ∧ ∀ r ∈ replies, r.1 = i}

/-- The replies contradict on `S` when no candidate inside `S` is named by all of
them. -/
def ContradictoryOn (S : Finset ι) (replies : List (ι × β)) : Prop :=
  ∀ i ∈ S, ∃ r ∈ replies, r.1 ≠ i

/-- **A reply never promotes a carrier the scan excluded.** -/
theorem adversary_live_subset (S : Finset ι) (replies : List (ι × β)) :
    after S replies ⊆ (S : Set ι) :=
  fun _ hi => hi.1

/-- **Every live member is at the least distance.** -/
theorem adversary_least {α : Type*} [MetricSpace α] {c : ι → α} {q : α}
    {S : Finset ι} (hS : HeadSet c q S) (replies : List (ι × β)) {i : ι}
    (hi : i ∈ after S replies) (j : ι) : dist q (c i) ≤ dist q (c j) :=
  hS i hi.1 j

/-- **A single reply resolves to its own carrier.** -/
theorem adversary_resolved_mem (S : Finset ι) {i : ι} (b : β) (hi : i ∈ S) :
    i ∈ after S [(i, b)] := by
  refine ⟨hi, fun r hr => ?_⟩
  rw [List.mem_singleton] at hr
  rw [hr]

/-- **Contradiction on `S` is exactly an empty live set.** -/
theorem contradicted_iff_inconsistent (S : Finset ι) (replies : List (ι × β)) :
    ContradictoryOn S replies ↔ after S replies = ∅ := by
  constructor
  · intro hcon
    ext k
    simp only [Set.mem_empty_iff_false, iff_false]
    rintro ⟨hk, hall⟩
    obtain ⟨r, hr, hne⟩ := hcon k hk
    exact hne (hall r hr)
  · intro hempty i hi
    by_contra hnot
    push_neg at hnot
    have hmem : i ∈ after S replies := ⟨hi, hnot⟩
    rw [hempty] at hmem
    exact hmem

/-- **Two replies naming different carriers contradict.** -/
theorem conflicting_replies_contradict (S : Finset ι) {i j : ι} (b b' : β) (h : i ≠ j) :
    after S [(i, b), (j, b')] = ∅ := by
  ext k
  simp only [Set.mem_empty_iff_false, iff_false]
  rintro ⟨-, hall⟩
  have h1 : i = k := hall (i, b) (by simp)
  have h2 : j = k := hall (j, b') (by simp)
  exact h (h1.trans h2.symm)

/-- **A reply repeated changes nothing.** -/
theorem repeat_reply_idem (S : Finset ι) (replies : List (ι × β)) (i : ι) (b : β) :
    after S (replies ++ [(i, b), (i, b)]) = after S (replies ++ [(i, b)]) := by
  unfold after
  ext k
  simp only [Set.mem_setOf_eq, List.mem_append, List.mem_cons, List.not_mem_nil, or_false]
  constructor
  · rintro ⟨hk, hall⟩
    exact ⟨hk, fun r hr => hall r (hr.imp_right Or.inl)⟩
  · rintro ⟨hk, hall⟩
    refine ⟨hk, fun r hr => ?_⟩
    rcases hr with hmem | heq | heq
    · exact hall r (Or.inl hmem)
    · rw [heq]; exact hall (i, b) (Or.inr rfl)
    · rw [heq]; exact hall (i, b) (Or.inr rfl)

/-- **A lie consistent with every reply stays live.** -/
theorem consistent_lie_live (S : Finset ι) (replies : List (ι × β)) {i : ι}
    (hi : i ∈ S) (h : ∀ r ∈ replies, r.1 = i) : i ∈ after S replies :=
  ⟨hi, h⟩

/-- **A consistent lie resolves the question to a singleton.** -/
theorem consistent_lie_resolves (S : Finset ι) (replies : List (ι × β)) {i : ι} (b : β) :
    after S (replies ++ [(i, b)]) ⊆ ({i} : Set ι) := by
  rintro k ⟨-, hall⟩
  have hk : i = k := hall (i, b) (by simp)
  simp only [Set.mem_singleton_iff]
  exact hk.symm

/-- **A consistent reply stays live when it is repeated.** -/
theorem consistent_lie_confirmed (S : Finset ι) (replies : List (ι × β)) {i : ι}
    (hi : i ∈ after S replies) (b : β) : i ∈ after S (replies ++ [(i, b)]) := by
  refine ⟨hi.1, fun r hr => ?_⟩
  rcases List.mem_append.1 hr with hr | hr
  · exact hi.2 r hr
  · rw [List.mem_singleton] at hr
    rw [hr]

end GLM.AdversarialDialogue
