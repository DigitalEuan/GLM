module

public import RequestProject.GLM.NearestAddress
public import RequestProject.GLM.AnsweringQuestion

/-!
# The question at the `nearest` tie (Phase 150)

The formal half of `studies/NEAREST_QUESTION_STUDY.md`. Since Phase 146 only
the `locate` junction answer put a question and read a reply. Phase 148 gave
the `nearest` kind a ranking of a point against the carriers of the address
table; its head can be a **tie**: a certified junction (several carriers at
one coordinate vector), or, where the guarded read refuses, two or more
carriers the scan finds at one least distance (128 of the 620 refused points
of Phase 148's sets). This round gives that tie the same question and reply
turn as `locate`. What the question may and may not do to a ranking is here.

* `HeadSet` — the head of a ranking: every carrier at the least distance from
  the point, and only those.
* `head_mem_least`, `after_least` — every member of the head, and so every
  member a reply leaves live, is at the least distance: **a reply never moves
  the answer off the scan's head.**
* `resolved_least` — a tie resolved by replies names a carrier no other
  carrier is strictly nearer to.
* `resolved_is_meant` — if the carrier meant is in the head and the replies
  are true of it, the tie resolves to that carrier
  (`GLM.TimedQuestion.resolved_eq_truth` on the head).
* `outside_never_confirmed` — if the carrier meant is **not** in the head (the
  point is nearer to other carriers than to the one it came from), true
  replies never confirm a member: the confirming reply empties the live set,
  and the GLM reports a contradiction rather than a carrier.
* `head_card_le_one_iff` — the head of a ranking has more than one member
  exactly when no carrier is the strict nearest: the question is put only
  where `ranking_head_of_strict` does not already name the head.
-/

@[expose] public section

namespace GLM.NearestQuestion

open Finset GLM.TimedQuestion GLM.AnsweringQuestion GLM.CellGuard

variable {α ι : Type*} [MetricSpace α]

/-- The head of a ranking of the carriers `c` by distance to `q`: the carriers
at the least distance, and every one of them. -/
structure HeadSet (c : ι → α) (q : α) (S : Finset ι) : Prop where
  least : ∀ i ∈ S, ∀ j, dist q (c i) ≤ dist q (c j)
  complete : ∀ j, (∀ k, dist q (c j) ≤ dist q (c k)) → j ∈ S

/-- Every member of the head is at the least distance. -/
theorem head_mem_least {c : ι → α} {q : α} {S : Finset ι} (hS : HeadSet c q S)
    {i : ι} (hi : i ∈ S) (j : ι) : dist q (c i) ≤ dist q (c j) :=
  hS.least i hi j

/-- **A reply never moves the answer off the scan's head**: every member a
history of replies leaves live is at the least distance. -/
theorem after_least {β : Type*} [DecidableEq β] {c : ι → α} {q : α}
    {S : Finset ι} (hS : HeadSet c q S) (h : List ((ι → β) × β)) {i : ι}
    (hi : i ∈ after S h) (j : ι) : dist q (c i) ≤ dist q (c j) :=
  hS.least i (after_subset S h hi) j

/-- A tie resolved by replies names a carrier no other carrier is strictly
nearer to. -/
theorem resolved_least {β : Type*} [DecidableEq β] {c : ι → α} {q : α}
    {S : Finset ι} (hS : HeadSet c q S) {h : List ((ι → β) × β)} {i : ι}
    (hres : after S h = {i}) : ∀ j, ¬ dist q (c j) < dist q (c i) := by
  intro j hlt
  have hi : i ∈ after S h := by rw [hres]; exact mem_singleton_self i
  exact absurd (after_least hS h hi j) (not_le.mpr hlt)

/-- **The tie resolves to the carrier meant** when that carrier is in the head
and every reply is true of it. -/
theorem resolved_is_meant {β : Type*} [DecidableEq β] {S : Finset ι}
    {h : List ((ι → β) × β)} {t i : ι} (ht : t ∈ S) (htr : Truthful t h)
    (hres : after S h = {i}) : t = i :=
  resolved_eq_truth ht htr hres

/-- **A carrier meant outside the head is never confirmed.** If the replies
resolved the tie to a member `i` while the carrier meant `t` is not in the
head, the true reply to *is it exactly `i`?* empties the live set. -/
theorem outside_never_confirmed [DecidableEq ι] {S : Finset ι}
    {h : List ((ι → Bool) × Bool)} {t i : ι} (ht : t ∉ S)
    (hres : after S h = {i}) :
    after S (h ++ [(confirmQ i, confirmQ i t)]) = ∅ := by
  have hi : i ∈ S := after_subset S h (by rw [hres]; exact mem_singleton_self i)
  have hne : t ≠ i := fun hti => ht (hti ▸ hi)
  exact confirm_catches hres hne

/-- **The question is put only where the scan names no strict nearest.** The
head has at most one member exactly when it is empty or its member is the
strict nearest carrier. -/
theorem head_card_le_one_iff {c : ι → α} {q : α} {S : Finset ι}
    (hS : HeadSet c q S) {i : ι} (hi : i ∈ S) :
    S.card ≤ 1 ↔ StrictNearest c q i := by
  constructor
  · intro hcard j hji
    by_contra hnot
    have hle : dist q (c j) ≤ dist q (c i) := not_lt.mp hnot
    have hj : j ∈ S := hS.complete j (fun k => le_trans hle (hS.least i hi k))
    exact hji (Finset.card_le_one.mp hcard j hj i hi)
  · intro hstrict
    refine Finset.card_le_one.mpr ?_
    intro a ha b hb
    have hai : a = i := by
      by_contra hne
      exact absurd (hS.least a ha i) (not_le.mpr (hstrict a hne))
    have hbi : b = i := by
      by_contra hne
      exact absurd (hS.least b hb i) (not_le.mpr (hstrict b hne))
    rw [hai, hbi]

end GLM.NearestQuestion
