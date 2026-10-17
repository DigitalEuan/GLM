module

public import RequestProject.GLM.TimedQuestion

/-!
# The question in the answering path: a reply is the next turn

The formal half of `studies/ANSWERING_QUESTION_STUDY.md` (Phase 146). Phase 145
(`GLM.TimedQuestion`) held a tie open as a live set and resolved it by
information that arrives later. This round puts the question into the answer
itself: a junction answer ends with the one question the GLM computes would
split it, and the reply is taken as the conversation's next turn, rewritten to
a whole query (`locate X given q is a; ...`) that the session answers. This file
proves what that turn-by-turn reading rests on.

* `after_reply` — a reply taken as the next turn prunes the live set the
  previous turn left; the answer to the whole query with every reply given
  is the answer reached turn by turn.
* `reply_removes`, `dialogue_bound`, `dialogue_length_lt` — every question the
  GLM puts splits the live set it is asked of, so every reply removes at least
  one candidate, and a dialogue over a tie of `n` candidates ends, under true
  replies, within `n - 1` replies, whatever the replies are.
* `confirm_yes`, `confirm_no`, `confirm_catches` — the confirming question put
  after a tie is resolved keeps the answer when the reply is *yes*, and turns
  a false resolution into a contradiction (an empty live set, reported and
  never resolved) when the truth is any other candidate.
-/

@[expose] public section

namespace GLM.AnsweringQuestion

open Finset GLM.TimedQuestion

variable {α β : Type*}

section Replies

variable [DecidableEq β]

/-- A history in which every question splits the live set it was asked of:
the only questions the GLM puts (`GLM.TimedQuestion.splits_iff`). -/
def Splitting : Finset α → List ((α → β) × β) → Prop
  | _, [] => True
  | S, p :: h => (∃ a ∈ S, ∃ c ∈ S, p.1 a ≠ p.1 c) ∧ Splitting (prune S p.1 p.2) h

/-- **A reply is the next turn.** The live set after a history with one more
answer is the live set the history left, pruned by that answer. -/
theorem after_reply (S : Finset α) (h : List ((α → β) × β)) (p : (α → β) × β) :
    after S (h ++ [p]) = prune (after S h) p.1 p.2 := by
  rw [after_append]
  rfl

/-- Every reply to a question that splits the live set removes a candidate. -/
theorem reply_removes {S : Finset α} {q : α → β}
    (hs : ∃ a ∈ S, ∃ c ∈ S, q a ≠ q c) (b : β) :
    (prune S q b).card < S.card := by
  have hS : S.Nonempty := by
    obtain ⟨a, ha, -⟩ := hs
    exact ⟨a, ha⟩
  exact card_lt_card ((splits_iff hS q).mpr hs b)

/-- **Each reply removes at least one candidate**: after a splitting history
the live set has lost at least as many candidates as there were replies. -/
theorem dialogue_bound :
    ∀ (S : Finset α) (h : List ((α → β) × β)), Splitting S h →
      (after S h).card + h.length ≤ S.card := by
  intro S h
  induction h generalizing S with
  | nil => intro _; simp [after]
  | cons p h ih =>
    intro hs
    obtain ⟨hsplit, hrest⟩ := hs
    have h1 := ih (prune S p.1 p.2) hrest
    have h2 := reply_removes hsplit p.2
    simp only [after, List.length_cons]
    omega

/-- **A dialogue ends.** Under true replies the truth stays live, so a
splitting dialogue over a tie of `n` candidates has fewer than `n` replies. -/
theorem dialogue_length_lt {S : Finset α} {h : List ((α → β) × β)}
    (hs : Splitting S h) {t : α} (ht : t ∈ S) (htr : Truthful t h) :
    h.length < S.card := by
  have hb := dialogue_bound S h hs
  have hpos : 0 < (after S h).card := card_pos.mpr ⟨t, truth_mem_after ht htr⟩
  omega

end Replies

section Confirm

variable [DecidableEq α]

/-- The confirming question *is it exactly `c`?* -/
def confirmQ (c : α) : α → Bool := fun x => decide (x = c)

/-- A *yes* to the confirming question keeps a resolved tie resolved. -/
theorem confirm_yes (c : α) : prune {c} (confirmQ c) true = {c} := by
  ext x
  simp [prune, confirmQ]

/-- A *no* to the confirming question leaves no candidate: a contradiction. -/
theorem confirm_no (c : α) : prune {c} (confirmQ c) false = ∅ := by
  ext x
  simp only [prune, confirmQ, mem_filter, mem_singleton, notMem_empty, iff_false,
    not_and]
  intro hx
  simp [hx]

/-- **The confirming question catches a false resolution.** If the replies
resolved the tie to `c` while the truth is another candidate, the true answer
to *is it exactly `c`?* empties the live set, which is reported as
contradicted and never resolved. -/
theorem confirm_catches {S : Finset α} {h : List ((α → Bool) × Bool)} {t c : α}
    (hres : after S h = {c}) (hne : t ≠ c) :
    after S (h ++ [(confirmQ c, confirmQ c t)]) = ∅ := by
  rw [after_reply, hres]
  have : confirmQ c t = false := by simp [confirmQ, hne]
  simp only [this]
  exact confirm_no c

end Confirm

end GLM.AnsweringQuestion
