module

public import RequestProject.GLM.AdversarialDialogue

/-!
# The open tie kept across turns (Phase 172)

*Created 20 October 2026.*

The formal half of `studies/RESUMED_DIALOGUE_STUDY.md`. Until Phase 172 a reply
was read only when the turn just before it had put the question; one unrelated
turn in between and the dialogue was dropped (Phase 167, informant A4). Since
Phase 172 the conversation keeps the question open across turns that leave it
alone (`runtime/conversation.py`, `Conversation.open_tie`). This file states
that rule on a conversation reduced to what matters for it — each turn either
put a question, gave a reply, or did neither — and proves what it does and
what it cannot do.

* `run_unrelated`, `run_strip` — **an unrelated turn is invisible**: the replies
  read, and the question left open, are those of the same conversation with
  every unrelated turn removed.
* `resumed_live_eq` — so a resumed dialogue leaves exactly the live set the
  uninterrupted one leaves, and `resumed_least` — whatever the turns and the
  replies, every live member is at the scan's least distance (Phase 167's
  `adversary_least`, carried over).
* `old_rule_drops` — under the reading before Phase 172 the same reply after an
  unrelated turn is not read at all.
* `reply_closes` — a question is answered once: a second reply (an echo) is not
  read against it.
* `newest_supersedes` — a later question replaces an earlier one: a reply is
  read against the newest question only.
-/

@[expose] public section

namespace GLM.ResumedDialogue

open Finset GLM.TimedQuestion GLM.NearestQuestion

variable {ι β : Type*}

/-- What one turn of a conversation does, as far as an open question goes:
it put a question (`ask`), it is a text read as a reply (`reply`), or it is
anything else — a whole query that put no question, a refusal, a follow-up
(`unrelated`). A reply turn whose answer puts a new question is `reply b`
followed by `ask q`. -/
inductive Turn (ι β : Type*) where
  | ask (q : ι → β)
  | reply (b : β)
  | unrelated

/-- The state the conversation carries: the replies read so far, oldest first,
each paired with the question it answered, and the question still open. -/
structure State (ι β : Type*) where
  replies : List ((ι → β) × β)
  open? : Option (ι → β)

/-- The empty conversation. -/
def State.init : State ι β := ⟨[], none⟩

/-- One turn under the rule of Phase 172. A reply is read against the open
question and closes it; a reply with no open question is not read; an
unrelated turn changes nothing. -/
def step (s : State ι β) : Turn ι β → State ι β
  | .ask q => ⟨s.replies, some q⟩
  | .reply b =>
      match s.open? with
      | some q => ⟨s.replies ++ [(q, b)], none⟩
      | none => s
  | .unrelated => s

/-- One turn under the reading of Phases 146–171: an unrelated turn closes the
open question, because only the previous turn's question could be replied to. -/
def stepOld (s : State ι β) : Turn ι β → State ι β
  | .unrelated => ⟨s.replies, none⟩
  | t => step s t

/-- A conversation, oldest turn first, under the rule of Phase 172. -/
def run (ts : List (Turn ι β)) : State ι β := ts.foldl step State.init

/-- The same conversation under the older reading. -/
def runOld (ts : List (Turn ι β)) : State ι β := ts.foldl stepOld State.init

/-- Whether a turn is unrelated. -/
def Turn.isUnrelated : Turn ι β → Bool
  | .unrelated => true
  | _ => false

/-- The conversation with its unrelated turns removed. -/
def strip (ts : List (Turn ι β)) : List (Turn ι β) :=
  ts.filter (fun t => !t.isUnrelated)

/-- Folding from any state, unrelated turns are invisible. -/
theorem foldl_strip (s : State ι β) (ts : List (Turn ι β)) :
    ts.foldl step s = (strip ts).foldl step s := by
  induction ts generalizing s with
  | nil => rfl
  | cons t ts ih =>
    cases t with
    | ask q => simp [strip, List.filter, Turn.isUnrelated, ih]
    | reply b => simp [strip, List.filter, Turn.isUnrelated, ih]
    | unrelated =>
      simp only [strip, List.filter, Turn.isUnrelated, Bool.not_true,
        List.foldl_cons]
      exact ih (step s .unrelated)

/-- **An unrelated turn is invisible**: appending one changes neither the
replies read nor the question left open. -/
theorem run_unrelated (ts : List (Turn ι β)) :
    run (ts ++ [.unrelated]) = run ts := by
  simp [run, List.foldl_append, step]

/-- **A conversation reads as if its unrelated turns had never been asked.** -/
theorem run_strip (ts : List (Turn ι β)) : run ts = run (strip ts) :=
  foldl_strip State.init ts

/-- **A resumed dialogue ends where the uninterrupted one ends**: the live set
left by the replies is that of the same conversation without its unrelated
turns. -/
theorem resumed_live_eq [DecidableEq β] (S : Finset ι) (ts : List (Turn ι β)) :
    after S (run ts).replies = after S (run (strip ts)).replies := by
  rw [← run_strip]

/-- **Resumption never promotes a carrier the measurement excluded**: whatever
the turns, unrelated or not, and whatever the replies, every live member is at
the scan's least distance. -/
theorem resumed_least {α : Type*} [MetricSpace α] [DecidableEq β] {c : ι → α}
    {q : α} {S : Finset ι} (hS : HeadSet c q S) (ts : List (Turn ι β)) {i : ι}
    (hi : i ∈ after S (run ts).replies) (j : ι) : dist q (c i) ≤ dist q (c j) :=
  GLM.AdversarialDialogue.adversary_least hS _ hi j

/-- **What the older reading did**: a question, an unrelated turn, then the
reply — the reply is not read. -/
theorem old_rule_drops (q : ι → β) (b : β) :
    (runOld [.ask q, .unrelated, .reply b]).replies = [] := rfl

/-- **The new rule reads it**, against the question put before the unrelated
turn. -/
theorem resumed_reads (q : ι → β) (b : β) :
    (run [.ask q, .unrelated, .reply b]).replies = [(q, b)] := rfl

/-- **A question is answered once**: a second reply, after any number of
unrelated turns, is not read against it. -/
theorem reply_closes (q : ι → β) (b b' : β) (n : ℕ) :
    (run ([.ask q, .reply b] ++ List.replicate n .unrelated ++ [.reply b'])).replies
      = [(q, b)] := by
  have h : run ([.ask q, .reply b] ++ List.replicate n .unrelated ++ [.reply b'])
      = run ([.ask q, .reply b] ++ [.reply b']) := by
    rw [run_strip]
    congr 1
    simp [strip, List.filter_append, Turn.isUnrelated]
  rw [h]
  rfl

/-- **The newest question supersedes**: a reply after two questions is read
against the second only. -/
theorem newest_supersedes (q q' : ι → β) (b : β) :
    (run [.ask q, .unrelated, .ask q', .unrelated, .reply b]).replies
      = [(q', b)] := rfl

/-- **The new rule reads every reply the older one read, the same way**: on a
conversation with no unrelated turn the two readings agree. -/
theorem agrees_without_unrelated (ts : List (Turn ι β))
    (h : ∀ t ∈ ts, t.isUnrelated = false) : runOld ts = run ts := by
  unfold runOld run
  generalize (State.init : State ι β) = s
  induction ts generalizing s with
  | nil => rfl
  | cons t ts ih =>
    simp only [List.foldl_cons]
    have ht := h t (List.mem_cons_self ..)
    have hs : stepOld s t = step s t := by
      cases t with
      | ask q => rfl
      | reply b => rfl
      | unrelated => simp [Turn.isUnrelated] at ht
    rw [hs]
    exact ih (fun t' ht' => h t' (List.mem_cons_of_mem _ ht')) _

end GLM.ResumedDialogue
