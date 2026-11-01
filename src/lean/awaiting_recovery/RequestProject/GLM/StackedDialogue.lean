module

public import RequestProject.GLM.ResumedDialogue

/-!
# Several open ties, a window, and which question a reply answers (Phase 173)

*Created 20 October 2026.*

The formal half of `studies/STACKED_DIALOGUE_STUDY.md`. Since Phase 172 a
question stays open across turns that leave it alone, but only the newest
question can be answered: a second question closes the first for good, and a
question stays open however many unrelated turns pass
(`GLM.ResumedDialogue`). Since Phase 173 the conversation keeps every open
question in a stack, newest first (`runtime/conversation.py`,
`Conversation.open_ties`, switch `OPEN_TIE_STACK`), with three rules:

* a reply is read against the **newest open question it fits** — the newest
  question still wins whenever the reply is one of its options, so nothing the
  Phase 172 rule read is read differently (`newest_fit_agrees`);
* a reply **closes exactly the question it answered** and leaves every other
  open question open (`reply_erases`, `reply_closes_one`);
* a question survives at most `W` unrelated turns (the window): within it an
  unrelated turn changes no open question (`unrelated_within_window`), past it
  every question is closed (`window_closes`).

A reply that fits no open question is not read (`unfit_unread`). The bound
question is always one the reply fits and no newer open question fits
(`bound_fits`, `bound_newest`), and whatever the turns and the replies the live
set keeps only members at the scan's least distance (`stacked_least`).

The model is the one of `GLM.ResumedDialogue` with one addition: `fits q b`
says whether the text `b` is one of the options of the question `q`
(`timed_question.match_reply`), left abstract.
-/

@[expose] public section

namespace GLM.StackedDialogue

open Finset GLM.TimedQuestion GLM.NearestQuestion
open GLM.ResumedDialogue (Turn)

variable {ι β : Type*}

/-- The state: the replies read so far, oldest first, each with the question
it answered; and the open questions, newest first, each with the number of
unrelated turns it has survived. -/
structure State (ι β : Type*) where
  replies : List ((ι → β) × β)
  opens : List ((ι → β) × ℕ)

/-- The empty conversation. -/
def State.init : State ι β := ⟨[], []⟩

section rule

variable (fits : (ι → β) → β → Bool) (W : ℕ)

/-- The open question a reply `b` is read against: the newest it fits. -/
def bound (s : State ι β) (b : β) : Option ((ι → β) × ℕ) :=
  s.opens.find? (fun e => fits e.1 b)

/-- An unrelated turn ages every open question by one and closes those past
the window. -/
def age (os : List ((ι → β) × ℕ)) : List ((ι → β) × ℕ) :=
  (os.map (fun e => (e.1, e.2 + 1))).filter (fun e => decide (e.2 ≤ W))

/-- One turn under the rule of Phase 173. -/
def step (s : State ι β) : Turn ι β → State ι β
  | .ask q => ⟨s.replies, (q, 0) :: s.opens⟩
  | .reply b =>
      match s.opens.findIdx? (fun e => fits e.1 b) with
      | some k => ⟨s.replies ++ [((s.opens[k]?.map Prod.fst).getD (fun _ => b), b)],
                    s.opens.eraseIdx k⟩
      | none => s
  | .unrelated => ⟨s.replies, age W s.opens⟩

/-- A conversation, oldest turn first, under the rule of Phase 173. -/
def run (ts : List (Turn ι β)) : State ι β := ts.foldl (step fits W) State.init

/-- **The bound question fits the reply.** -/
theorem bound_fits {s : State ι β} {b : β} {e : (ι → β) × ℕ}
    (h : bound fits s b = some e) : fits e.1 b = true := by
  unfold bound at h
  simpa using List.find?_some h

/-- **No newer open question fits it**: every question opened after the bound
one (earlier in the stack) is not one the reply answers. -/
theorem bound_newest {s : State ι β} {b : β} {e : (ι → β) × ℕ}
    (h : bound fits s b = some e) :
    ∃ pre post, s.opens = pre ++ e :: post ∧ ∀ x ∈ pre, fits x.1 b = false := by
  unfold bound at h
  rw [List.find?_eq_some_iff_append] at h
  obtain ⟨_, pre, post, hs, hpre⟩ := h
  exact ⟨pre, post, hs, fun x hx => by simpa using hpre x hx⟩

/-- The index the step erases is the position of the bound question. -/
theorem findIdx_bound {s : State ι β} {b : β} {k : ℕ}
    (hk : s.opens.findIdx? (fun e => fits e.1 b) = some k) :
    ∃ e, s.opens[k]? = some e ∧ bound fits s b = some e := by
  have hfind : s.opens.find? (fun e => fits e.1 b) = s.opens[k]? := by
    rw [List.findIdx?_eq_some_iff_getElem] at hk
    obtain ⟨hlt, hk1, hk2⟩ := hk
    rw [List.getElem?_eq_getElem hlt]
    rw [List.find?_eq_some_iff_getElem]
    exact ⟨hk1, k, hlt, rfl, fun j hj => by simpa using hk2 j hj⟩
  have hlt : k < s.opens.length := by
    rw [List.findIdx?_eq_some_iff_getElem] at hk
    exact hk.1
  exact ⟨s.opens[k], List.getElem?_eq_getElem hlt, by
    unfold bound; rw [hfind, List.getElem?_eq_getElem hlt]⟩

/-- A bound reply has an index in the stack. -/
theorem findIdx_of_bound {s : State ι β} {b : β} {e : (ι → β) × ℕ}
    (h : bound fits s b = some e) :
    ∃ k, s.opens.findIdx? (fun e => fits e.1 b) = some k := by
  have hfit := bound_fits fits h
  unfold bound at h
  rcases hk : s.opens.findIdx? (fun e => fits e.1 b) with _ | k
  · rw [List.findIdx?_eq_none_iff] at hk
    have := hk e (List.mem_of_find?_eq_some h)
    simp [hfit] at this
  · exact ⟨k, hk⟩

/-- **A reply is read against the newest open question it fits**, and the
reply is recorded with that question. -/
theorem reply_reads {s : State ι β} {b : β} {e : (ι → β) × ℕ}
    (h : bound fits s b = some e) :
    (step fits W s (.reply b)).replies = s.replies ++ [(e.1, b)] := by
  obtain ⟨k, hk⟩ := findIdx_of_bound fits h
  obtain ⟨e', he', hb⟩ := findIdx_bound fits hk
  rw [h] at hb
  cases hb
  simp [step, hk, he']

/-- **A reply closes exactly the question it answered**: that entry is removed
from the stack and every other open question stays open, in order. -/
theorem reply_erases {s : State ι β} {b : β} {k : ℕ}
    (hk : s.opens.findIdx? (fun e => fits e.1 b) = some k) :
    (step fits W s (.reply b)).opens = s.opens.eraseIdx k := by
  simp [step, hk]

/-- **A question is answered once**: a read reply removes one open question. -/
theorem reply_closes_one {s : State ι β} {b : β} {e : (ι → β) × ℕ}
    (h : bound fits s b = some e) :
    (step fits W s (.reply b)).opens.length + 1 = s.opens.length := by
  obtain ⟨k, hk⟩ := findIdx_of_bound fits h
  have hlt : k < s.opens.length := by
    rw [List.findIdx?_eq_some_iff_getElem] at hk
    exact hk.1
  rw [reply_erases fits W hk, List.length_eraseIdx_of_lt hlt]
  omega

/-- **A reply that fits no open question is not read**: the state is
unchanged. -/
theorem unfit_unread {s : State ι β} {b : β} (h : bound fits s b = none) :
    step fits W s (.reply b) = s := by
  unfold bound at h
  have : s.opens.findIdx? (fun e => fits e.1 b) = none := by
    rw [List.findIdx?_eq_none_iff]
    rw [List.find?_eq_none] at h
    simpa using h
  simp [step, this]

/-- **The newest question still wins when it fits**: whenever the reply is one
of the newest open question's options, it is read against that question —
what the rule of Phase 172 did. -/
theorem newest_fit_agrees {s : State ι β} {b : β} {e : (ι → β) × ℕ}
    {rest : List ((ι → β) × ℕ)} (hs : s.opens = e :: rest) (he : fits e.1 b = true) :
    bound fits s b = some e := by
  simp [bound, hs, he]

/-- **Within the window an unrelated turn changes no open question**: if every
open question has survived fewer than `W` unrelated turns, the questions open
after one more are the same, in the same order. -/
theorem unrelated_within_window {s : State ι β} (h : ∀ e ∈ s.opens, e.2 < W) :
    ((step fits W s .unrelated).opens.map Prod.fst) = s.opens.map Prod.fst := by
  simp only [step, age]
  rw [List.filter_eq_self.mpr]
  · simp [Function.comp_def]
  · intro x hx
    simp only [List.mem_map] at hx
    obtain ⟨e, he, rfl⟩ := hx
    simpa using h e he

/-- Ageing adds one to every surviving count. -/
theorem age_mem {os : List ((ι → β) × ℕ)} {x : (ι → β) × ℕ} (hx : x ∈ age W os) :
    ∃ e ∈ os, x = (e.1, e.2 + 1) ∧ e.2 + 1 ≤ W := by
  simp only [age, List.mem_filter, List.mem_map, decide_eq_true_eq] at hx
  obtain ⟨⟨e, he, rfl⟩, hle⟩ := hx
  exact ⟨e, he, rfl, hle⟩

/-- After `n` unrelated turns every open question has survived at least `n`. -/
theorem age_iter_ge (os : List ((ι → β) × ℕ)) (n : ℕ) :
    ∀ x ∈ (age W)^[n] os, n ≤ x.2 := by
  induction n generalizing os with
  | zero => intro x _; exact Nat.zero_le _
  | succ n ih =>
    intro x hx
    rw [Function.iterate_succ_apply'] at hx
    obtain ⟨e, he, rfl, _⟩ := age_mem W hx
    have := ih os e he
    simp only
    omega

/-- **Past the window every question is closed**: after `W + 1` unrelated
turns no question is open, whatever was open before. -/
theorem window_closes (os : List ((ι → β) × ℕ)) : (age W)^[W + 1] os = [] := by
  rw [Function.iterate_succ_apply']
  rw [List.eq_nil_iff_forall_not_mem]
  intro x hx
  obtain ⟨e, he, _, hle⟩ := age_mem W hx
  have := age_iter_ge W os W e he
  omega

/-- **Stacked dialogue never promotes a carrier the measurement excluded**:
whatever the turns and the replies, and whichever question each reply was read
against, every live member is at the scan's least distance. -/
theorem stacked_least {α : Type*} [MetricSpace α] [DecidableEq β] {c : ι → α}
    {q : α} {S : Finset ι} (hS : HeadSet c q S) (ts : List (Turn ι β)) {i : ι}
    (hi : i ∈ after S (run fits W ts).replies) (j : ι) :
    dist q (c i) ≤ dist q (c j) :=
  GLM.AdversarialDialogue.adversary_least hS _ hi j

end rule

/-- **An older question can be answered** — the case Phase 172 could not read:
a question, a second question, then a reply that fits the first only. The
reply is read against the first question, and the second stays open. -/
theorem older_answered (fits : (ι → β) → β → Bool) (W : ℕ) (q q' : ι → β) (b : β)
    (h1 : fits q b = true) (h2 : fits q' b = false) :
    run fits W [.ask q, .ask q', .reply b] = ⟨[(q, b)], [(q', 0)]⟩ := by
  simp [run, step, State.init, List.findIdx?_cons, h1, h2]

/-- **Under the rule of Phase 172 the same reply is lost**: the second
question superseded the first. -/
theorem resumed_rule_loses (q q' : ι → β) (b : β) :
    (GLM.ResumedDialogue.run [.ask q, .ask q', .reply b]).replies = [(q', b)] := rfl

end GLM.StackedDialogue
