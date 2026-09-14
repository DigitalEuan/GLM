/-
# The relay: what a multi-part stack can promise when one part goes silent

`Retrieval.lean` proves what an index built on the lattice can promise when it
answers a question *alone*.  The measured half of that, in
`studies/ADDRESS_RETRIEVAL_STUDY.md`, records a negative result: the address
layer beats chance by 7.6× and is beaten decisively by a plain lexical overlap
of the statement text.

This file is about the arrangement that negative result does not settle.  The
machine is not one faculty: it has an address book, a second address book over
the identifiers, a lexical search and a name search, and in the other register
of `studies/STACK_RELAY_STUDY.md` a generator, a visual filter and a
cross-domain check.  When the strong faculty has *no evidence for this query* —
a goal whose identifiers appear nowhere else — the stack can let a weaker
faculty answer instead.  `overlay/glm_universal/reasoning/stack.py` measures
what that is worth; this file proves what it costs and what it guarantees.

## 1.  The answer keeps no duplicates and invents nothing

`interleave` lays down a stated quota from each member in a stated order, then
the remainders in the same order, and keeps the first occurrence of each
candidate (`firstOnly`).  `mem_interleave` says the result holds exactly the
candidates the members proposed — no invention, no loss — and
`interleave_nodup` says it holds each of them once, however many members
proposed it.

## 2.  A confident leader is not disturbed

`relay_confident`: while the leader's confidence is at or above the gate, the
relay *is* the leader's ranking, unchanged.  The stack therefore cannot cost
anything on the queries the leader answers well, which is what makes it safe
to run always rather than only when a human suspects trouble.  `relay_abstain`
is the other branch, stated so that the two exhaust the definition.

## 3.  The carry theorem

`relay_carry` is the guarantee the multi-part claim rests on: whatever a member
holds inside its own quota is inside the relayed answer's window of the summed
quotas.  A faculty that has the answer cannot be drowned out by the faculties
that do not — the window is wide enough, by construction, to hold every
member's quota at once.  `carry_hit` restates it in the vocabulary the
measurement uses: if some member's quota contains a relevant candidate, the
relayed answer hits within the summed window.

## 4.  Widening the window adds at the end

`relay_take_prefix`: the first `k` of the answer is a prefix of the first `k'`
whenever `k ≤ k'`, so a hit at `k` is a hit at `k'` (`hit_mono`) and the ladder
the study reports is monotone by theorem rather than by observation.

Everything here is computable, and §6 evaluates it on a worked example by
`decide` — the same lists the Python module's example uses, with the names
carried as numbers so that the kernel can check the evaluation itself.
-/
import Mathlib

namespace GLM.Relay

/-! ## 1.  Keeping the first occurrence -/

/-- The accumulating form of `firstOnly`: emit an element the first time it is
seen and never again. -/
def firstOnlyAux {α : Type*} [DecidableEq α] : List α → List α → List α
  | [], _ => []
  | a :: l, seen =>
      if a ∈ seen then firstOnlyAux l seen else a :: firstOnlyAux l (a :: seen)

/-- Keep the first occurrence of each element and drop every later copy.

Mathlib's `List.dedup` keeps the *last* occurrence; a ranking must keep the
first, because the position of the first occurrence is the rank the member
gave it. -/
def firstOnly {α : Type*} [DecidableEq α] (l : List α) : List α :=
  firstOnlyAux l []

section FirstOnly

variable {α : Type*} [DecidableEq α]

@[simp] theorem firstOnlyAux_nil (seen : List α) :
    firstOnlyAux ([] : List α) seen = [] := rfl

theorem firstOnlyAux_cons (a : α) (l seen : List α) :
    firstOnlyAux (a :: l) seen =
      if a ∈ seen then firstOnlyAux l seen
      else a :: firstOnlyAux l (a :: seen) := rfl

theorem mem_firstOnlyAux {x : α} :
    ∀ (l seen : List α), x ∈ firstOnlyAux l seen ↔ x ∈ l ∧ x ∉ seen := by
  intro l
  induction l with
  | nil => intro seen; simp
  | cons a l ih =>
      intro seen
      rw [firstOnlyAux_cons]
      by_cases ha : a ∈ seen
      · simp only [ha, if_true, ih, List.mem_cons]
        constructor
        · rintro ⟨hx, hs⟩; exact ⟨Or.inr hx, hs⟩
        · rintro ⟨rfl | hx, hs⟩
          · exact absurd ha hs
          · exact ⟨hx, hs⟩
      · simp only [ha, if_false, List.mem_cons, ih]
        constructor
        · rintro (rfl | ⟨hx, hs⟩)
          · exact ⟨Or.inl rfl, ha⟩
          · exact ⟨Or.inr hx, fun h => hs (Or.inr h)⟩
        · rintro ⟨rfl | hx, hs⟩
          · exact Or.inl rfl
          · by_cases hxa : x = a
            · exact Or.inl hxa
            · exact Or.inr ⟨hx, by simp [hxa, hs]⟩

@[simp] theorem mem_firstOnly {x : α} {l : List α} :
    x ∈ firstOnly l ↔ x ∈ l := by
  simp [firstOnly, mem_firstOnlyAux]

theorem firstOnlyAux_nodup : ∀ (l seen : List α), (firstOnlyAux l seen).Nodup := by
  intro l
  induction l with
  | nil => intro seen; simp
  | cons a l ih =>
      intro seen
      rw [firstOnlyAux_cons]
      by_cases ha : a ∈ seen
      · simpa [ha] using ih seen
      · simp only [ha, if_false]
        refine List.nodup_cons.mpr ⟨?_, ih _⟩
        intro hmem
        exact ((mem_firstOnlyAux l (a :: seen)).mp hmem).2
          (List.mem_cons_self)

theorem firstOnly_nodup (l : List α) : (firstOnly l).Nodup :=
  firstOnlyAux_nodup l []

theorem length_firstOnlyAux_le :
    ∀ (l seen : List α), (firstOnlyAux l seen).length ≤ l.length := by
  intro l
  induction l with
  | nil => intro seen; simp
  | cons a l ih =>
      intro seen
      rw [firstOnlyAux_cons]
      by_cases ha : a ∈ seen
      · simp only [ha, if_true, List.length_cons]
        exact (ih seen).trans (Nat.le_succ _)
      · simp only [ha, if_false, List.length_cons]
        exact Nat.succ_le_succ (ih _)

theorem length_firstOnly_le (l : List α) : (firstOnly l).length ≤ l.length :=
  length_firstOnlyAux_le l []

theorem firstOnlyAux_prefix_append :
    ∀ (A B seen : List α), firstOnlyAux A seen <+: firstOnlyAux (A ++ B) seen := by
  intro A
  induction A with
  | nil => intro B seen; simp
  | cons a A ih =>
      intro B seen
      rw [List.cons_append, firstOnlyAux_cons, firstOnlyAux_cons]
      by_cases ha : a ∈ seen
      · simpa [ha] using ih B seen
      · simpa [ha] using (List.prefix_cons_inj a).mpr (ih B (a :: seen))

theorem firstOnly_prefix_append (A B : List α) :
    firstOnly A <+: firstOnly (A ++ B) :=
  firstOnlyAux_prefix_append A B []

end FirstOnly

/-! ## 2.  The interleave and the relay -/

/-- A member's proposal together with the quota it is allowed at the front. -/
abbrev Plan (α : Type*) := List (List α × ℕ)

/-- The quota prefixes, in member order. -/
def quotaHead {α : Type*} (plan : Plan α) : List α :=
  plan.flatMap (fun p => p.1.take p.2)

/-- What each member proposed beyond its quota, in member order. -/
def quotaTail {α : Type*} (plan : Plan α) : List α :=
  plan.flatMap (fun p => p.1.drop p.2)

/-- The relayed answer: every member's quota first, then the remainders,
keeping the first occurrence of each candidate. -/
def interleave {α : Type*} [DecidableEq α] (plan : Plan α) : List α :=
  firstOnly (quotaHead plan ++ quotaTail plan)

/-- The summed quota: the width of the window the carry theorem promises. -/
def window {α : Type*} (plan : Plan α) : ℕ := (plan.map (fun p => p.2)).sum

/-- One faculty's answer to one query: what it proposes, and how much evidence
it claims for this query. -/
structure Answer (α : Type*) where
  /-- The candidates, best first. -/
  names : List α
  /-- The evidence the faculty has for *this* query, exactly. -/
  confidence : ℚ

/-- The stack's answer: the leader alone while it is confident, and the
interleave of the whole plan when it is not. -/
def relay {α : Type*} [DecidableEq α] (lead : Answer α) (plan : Plan α)
    (gate : ℚ) : List α :=
  if gate ≤ lead.confidence then lead.names else interleave plan

/-! ## 3.  No invention, no duplicates, no disturbance -/

section Relay

variable {α : Type*} [DecidableEq α]

omit [DecidableEq α] in
theorem mem_quotaHead_or_tail {x : α} {plan : Plan α}
    (h : x ∈ quotaHead plan ++ quotaTail plan) : ∃ p ∈ plan, x ∈ p.1 := by
  rcases List.mem_append.mp h with h | h
  · obtain ⟨p, hp, hx⟩ := List.mem_flatMap.mp h
    exact ⟨p, hp, List.mem_of_mem_take hx⟩
  · obtain ⟨p, hp, hx⟩ := List.mem_flatMap.mp h
    exact ⟨p, hp, List.mem_of_mem_drop hx⟩

theorem mem_interleave {x : α} {plan : Plan α} :
    x ∈ interleave plan ↔ ∃ p ∈ plan, x ∈ p.1 := by
  rw [interleave, mem_firstOnly]
  constructor
  · exact mem_quotaHead_or_tail
  · rintro ⟨p, hp, hx⟩
    have hsplit : x ∈ p.1.take p.2 ∨ x ∈ p.1.drop p.2 := by
      have : x ∈ p.1.take p.2 ++ p.1.drop p.2 := by
        rwa [List.take_append_drop]
      exact List.mem_append.mp this
    rcases hsplit with h | h
    · exact List.mem_append_left _
        (List.mem_flatMap.mpr ⟨p, hp, h⟩)
    · exact List.mem_append_right _
        (List.mem_flatMap.mpr ⟨p, hp, h⟩)

theorem interleave_nodup (plan : Plan α) : (interleave plan).Nodup :=
  firstOnly_nodup _

theorem relay_confident {lead : Answer α} {plan : Plan α} {gate : ℚ}
    (h : gate ≤ lead.confidence) : relay lead plan gate = lead.names := by
  simp [relay, h]

theorem relay_abstain {lead : Answer α} {plan : Plan α} {gate : ℚ}
    (h : lead.confidence < gate) : relay lead plan gate = interleave plan := by
  simp [relay, not_le.mpr h]

theorem mem_relay {x : α} {lead : Answer α} {plan : Plan α} {gate : ℚ}
    (h : x ∈ relay lead plan gate) :
    x ∈ lead.names ∨ ∃ p ∈ plan, x ∈ p.1 := by
  by_cases hc : gate ≤ lead.confidence
  · exact Or.inl (by rwa [relay_confident hc] at h)
  · exact Or.inr (mem_interleave.mp (by rwa [relay_abstain (not_le.mp hc)] at h))

theorem relay_nodup {lead : Answer α} {plan : Plan α} {gate : ℚ}
    (h : lead.names.Nodup) : (relay lead plan gate).Nodup := by
  by_cases hc : gate ≤ lead.confidence
  · rwa [relay_confident hc]
  · rw [relay_abstain (not_le.mp hc)]
    exact interleave_nodup plan

/-! ## 4.  The carry theorem -/

omit [DecidableEq α] in
theorem length_quotaHead_le (plan : Plan α) :
    (quotaHead plan).length ≤ window plan := by
  induction plan with
  | nil => simp [quotaHead, window]
  | cons p ps ih =>
      simp only [quotaHead, window, List.flatMap_cons, List.length_append,
        List.map_cons, List.sum_cons] at *
      exact Nat.add_le_add (List.length_take_le _ _) ih

omit [DecidableEq α] in
theorem take_prefix_take {l : List α} {k k' : ℕ} (h : k ≤ k') :
    l.take k <+: l.take k' := by
  have hk : (l.take k').take k = l.take k := by
    rw [List.take_take, Nat.min_eq_left h]
  exact hk ▸ List.take_prefix k (l.take k')

omit [DecidableEq α] in
theorem mem_take_of_prefix {x : α} {P L : List α} {n : ℕ}
    (hp : P <+: L) (hn : P.length ≤ n) (hx : x ∈ P) : x ∈ L.take n := by
  obtain ⟨B, rfl⟩ := hp
  have hmem : x ∈ (P ++ B).take P.length := by
    simpa [List.take_left] using hx
  exact (take_prefix_take hn).subset hmem

theorem relay_carry {x : α} {plan : Plan α} {p : List α × ℕ}
    (hp : p ∈ plan) (hx : x ∈ p.1.take p.2) :
    x ∈ (interleave plan).take (window plan) := by
  have hhead : x ∈ quotaHead plan := List.mem_flatMap.mpr ⟨p, hp, hx⟩
  have hfirst : x ∈ firstOnly (quotaHead plan) := mem_firstOnly.mpr hhead
  refine mem_take_of_prefix (firstOnly_prefix_append _ _) ?_ hfirst
  exact (length_firstOnly_le _).trans (length_quotaHead_le plan)

/-- The carry theorem in the vocabulary of the measurement: a relevant
candidate inside any member's quota is a hit inside the summed window. -/
theorem carry_hit {rel : α → Prop} {plan : Plan α} {p : List α × ℕ}
    (hp : p ∈ plan) (h : ∃ x ∈ p.1.take p.2, rel x) :
    ∃ x ∈ (interleave plan).take (window plan), rel x := by
  obtain ⟨x, hx, hrel⟩ := h
  exact ⟨x, relay_carry hp hx, hrel⟩

/-! ## 5.  Widening the window -/

theorem relay_take_prefix {lead : Answer α} {plan : Plan α} {gate : ℚ}
    {k k' : ℕ} (h : k ≤ k') :
    (relay lead plan gate).take k <+: (relay lead plan gate).take k' :=
  take_prefix_take h

/-- A hit inside a window is a hit inside every wider window. -/
theorem hit_mono {rel : α → Prop} {lead : Answer α} {plan : Plan α} {gate : ℚ}
    {k k' : ℕ} (h : k ≤ k')
    (hit : ∃ x ∈ (relay lead plan gate).take k, rel x) :
    ∃ x ∈ (relay lead plan gate).take k', rel x := by
  obtain ⟨x, hx, hrel⟩ := hit
  exact ⟨x, (relay_take_prefix (lead := lead) (plan := plan) (gate := gate)
    h).subset hx, hrel⟩

end Relay

/-! ## 6.  A worked example, decided -/

/-- The example the Python module runs: a leader that keeps two places, a
second book that keeps two and a third that keeps one, with one candidate
proposed twice. -/
def examplePlan : Plan ℕ := [([1, 2, 3], 2), ([2, 4], 2), ([5], 1)]

example : interleave examplePlan = [1, 2, 4, 5, 3] := by decide

example : window examplePlan = 5 := by decide

example : (interleave examplePlan).Nodup := by decide

/-- A confident leader is returned untouched. -/
example : relay ⟨[7, 8], (1 : ℚ) / 2⟩ examplePlan (1 / 10) = [7, 8] :=
  relay_confident (by norm_num)

/-- An abstaining leader hands over to the plan. -/
example : relay ⟨[7, 8], (0 : ℚ)⟩ examplePlan (1 / 10) = [1, 2, 4, 5, 3] := by
  rw [relay_abstain (by norm_num)]
  decide

end GLM.Relay
