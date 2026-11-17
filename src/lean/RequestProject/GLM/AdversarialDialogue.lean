module

public import Mathlib

/-!
# Adversarial replies at the `nearest` ties (Phase 167)

*Created 22 October 2026. Rebuilt 15 November 2026 (Phase 190) from
`studies/ADVERSARIAL_DIALOGUE_STUDY.md`, `reasoning/adversarial_dialogue_study.py`
and the two held files that import it (`ResumedDialogue.lean`,
`StackedDialogue.lean`): the original was lost in the October 2026
reorganisation and never uploaded. **Not yet built** — see
`source_material/ToDo/lean_recovery/README.md`.*

At a `nearest` tie the machine asks a question and reads a reply. The reply is
the adversary's, so the question is what survives it. This file states the nine
theorems the study declares, on the model the study measures:

* `HeadSet c q S` — `S` is the scan's answer: every carrier in it is at the
  least distance from `q`. `reasoning/nearest.py` produces it, and "every
  carrier of `S` is at the least distance" is the only property the proofs
  below use;
* `after S replies` — the live set: the carriers of `S` that every reply
  names. One reply keeps one carrier, two replies naming different carriers
  keep none, and no replies keep the whole scan;
* `Contradictory replies` — no single carrier is named by every reply;
* `adversary_live_subset`, `adversary_least` — a reply never promotes a
  carrier the scan excluded, so every live member is at the least distance
  (`ResumedDialogue.resumed_least` is this theorem applied to a
  conversation's replies);
* `adversary_resolved_mem` — a single reply resolves to its own carrier;
* `contradicted_iff_inconsistent`, `conflicting_replies_contradict` — an
  empty live set is exactly a contradiction, and two replies naming different
  carriers contradict;
* `repeat_reply_idem`, `consistent_lie_live`, `consistent_lie_resolves`,
  `consistent_lie_confirmed` — a repeated reply changes nothing; a reply
  consistent with every other stays live, resolves the question to a
  singleton, and stays live when repeated. That last group is the adversary:
  a *consistent* lie is never detected, only contradicted, which is why the
  rule reads a yes/no question by its words (`YES_NO_BY_NUMBER` in
  `reasoning/timed_question.py`) and why a resolution is reported, not
  trusted.

Nothing here ranks options: that is `nearest.py`'s census and the study's
measurement. These are the facts the reply path may rely on.
-/

namespace GLM.AdversarialDialogue

variable {ι β : Type*}

/-- The scan's answer: every carrier of `S` is at the least distance from the
question's state `q`. -/
def HeadSet {α : Type*} [MetricSpace α] (c : ι → α) (q : α) (S : Finset ι) : Prop :=
  ∀ i ∈ S, ∀ j, dist q (c i) ≤ dist q (c j)

/-- The live set after a list of replies: the carriers of `S` that every reply
names. A reply is a carrier and what was said about it; what was said decides
which carrier it names, never whether a named carrier survives. -/
def after (S : Finset ι) (replies : List (ι × β)) : Set ι :=
  {i | i ∈ S ∧ ∀ r ∈ replies, r.1 = i}

/-- The replies contradict when no single carrier is named by all of them. -/
def Contradictory (replies : List (ι × β)) : Prop :=
  ∀ i, ∃ r ∈ replies, r.1 ≠ i

/-- **A reply never promotes a carrier the scan excluded.** -/
theorem adversary_live_subset (S : Finset ι) (replies : List (ι × β)) :
    after S replies ⊆ (S : Set ι) :=
  fun _ hi => hi.1

/-- **Every live member is at the least distance**: resumption never promotes a
carrier the measurement excluded. -/
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

/-- **Contradiction is exactly an empty live set**: with a nonempty scan, the
replies leave nothing live precisely when no carrier is named by all of them. -/
theorem contradicted_iff_inconsistent {S : Finset ι} (hS : S.Nonempty)
    (replies : List (ι × β)) : Contradictory replies ↔ after S replies = ∅ := by
  constructor
  · intro hcon
    apply Set.eq_empty_iff_forall_not_mem.2
    rintro k ⟨-, hall⟩
    obtain ⟨r, hr, hne⟩ := hcon k
    exact hne (hall r hr)
  · intro hempty i
    by_contra hnot
    push_neg at hnot
    obtain ⟨k, hk⟩ := hS
    have : k ∈ after S replies := ⟨hk, hnot⟩
    rw [hempty] at this
    exact this

/-- **Two replies naming different carriers contradict.** -/
theorem conflicting_replies_contradict (S : Finset ι) {i j : ι} (b b' : β) (h : i ≠ j) :
    after S [(i, b), (j, b')] = ∅ := by
  apply Set.eq_empty_iff_forall_not_mem.2
  rintro k ⟨-, hall⟩
  have h1 : i = k := hall (i, b) (by simp)
  have h2 : j = k := hall (j, b') (by simp)
  exact h (h1.trans h2.symm)

/-- **A reply repeated changes nothing.** -/
theorem repeat_reply_idem (S : Finset ι) (replies : List (ι × β)) (i : ι) (b : β) :
    after S (replies ++ [(i, b), (i, b)]) = after S (replies ++ [(i, b)]) := by
  unfold after
  ext k
  simp only [Set.mem_setOf_eq, List.mem_append, List.mem_cons, List.mem_singleton,
    not_false_eq_true, or_false]
  constructor
  · rintro ⟨hk, hall⟩
    exact ⟨hk, fun r hr => hall r (Or.inl hr)⟩
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

/-- **A consistent lie resolves the question to a singleton**: every reply names
it, so nothing else is live. -/
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
