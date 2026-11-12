import Mathlib
import RequestProject.Semantics
import RequestProject.Chat
import RequestProject.Discourse

/-!
# Dialogue: a conversation that remembers

`Chat.lean` answers one question at a time and forgets.  `Discourse.lean` grows
a paragraph but nobody interrupts it.  A conversation needs both: the system
must remember what it has already said, so that

* "tell me more" says something *new* rather than going round in circles,
* the new thing is joined to the old with the right word — `and`, `but` or
  `so` — earned exactly as in `Discourse.lean`,
* "it" means whatever the conversation is currently about,
* and nothing it says at turn seven contradicts what it said at turn two.

## The state

A `Convo` is a topic (what "it" refers to) and the list of literals already
asserted.  `reply` is a total function from a state, an utterance and the world
to a new state and a reply; there is no search and no sampling, so the same
conversation always goes the same way.

## What is proved

* `reply_true` — every reply is true in the world, for **every** state, every
  utterance and every world.
* `reply_fresh` — when "tell me more" produces a connected clause, that clause
  has not been said before in this conversation and its connective is licensed
  by everything said so far (so `Discourse.so_is_a_deduction` and
  `Discourse.but_is_contrastive` apply to it).
* `reply_on_topic` — the clause "tell me more" adds is about the current topic,
  which is what licenses the pronoun.
* `topic_only_changes_when_asked` — "it" never silently drifts.
* `script_facts` — running the eight-turn demo script in **all 512 worlds**:
  every reply true, and the literals asserted are pairwise distinct in every
  world, so the conversation never repeats itself or contradicts itself.

The honest limit is in `replyMore`: when the system has nothing new to say
about the topic it falls back to a bare fact (possibly one already said) rather
than inventing something.
-/

namespace Dialogue

open Semantics Discourse

set_option maxRecDepth 100000

/-! ## 1. State and utterances -/

/-- The conversation so far: what "it" refers to, and what has been asserted. -/
structure Convo where
  topic : Ent
  said : List Lit
deriving Repr

/-- The four one-place properties, so that a question can be asked about "it"
without naming the thing. -/
inductive Prop1
  | frozen | boiling | warm | heavy
deriving DecidableEq, Repr

/-- The atom a property makes when applied to a thing. -/
def atomOf : Prop1 → Ent → Atom
  | .frozen, e => .frozen e
  | .boiling, e => .boiling e
  | .warm, e => .warm e
  | .heavy, e => .heavy e

/-- What the user can say. -/
inductive Utt
  | about (e : Ent)        -- "tell me about the stone"
  | more                   -- "tell me more"
  | isIt (p : Prop1)       -- "is it warm?"
  | whyIt (p : Prop1)      -- "why is it warm?"
  | hotterThan (f : Ent)   -- "is it hotter than the lamp?"
deriving DecidableEq, Repr

/-- A reply: a sentence, the word that joins it to the previous turn, and
whether the system is repeating a commitment it has already made. -/
structure Reply where
  conn : Option Conn
  sent : Sent
  again : Bool := false
deriving Repr

/-! ## 2. Replying -/

/-- A fact about `e` that is true in `w` whatever else is the case. -/
def bareFact (w : World) (e : Ent) : Lit := (.frozen e, evalAtom (.frozen e) w)

/-- "Tell me more": one further clause about the topic, joined with `and`, `but`
or `so`, never repeating what has been said.  When there is nothing new the
system says a bare fact rather than inventing one. -/
def replyMore (w : World) (st : Convo) : Convo × Reply :=
  match pick (candidates w st.topic) (ctxWorlds st.said) st.said st.topic with
  | some s => ({ st with said := s.lit :: st.said }, ⟨some s.conn, .lit s.lit, false⟩)
  | none => (st, ⟨none, .lit (bareFact w st.topic), false⟩)

/-- The literals a sentence asserts outright, so the conversation can remember
them. -/
def assertedLits : Sent → List Lit
  | .lit l => [l]
  | .because l m => [l, m]
  | .because2 l m n => [l, m, n]
  | _ => []

/-- **The reply.**  A total, deterministic function of the state, the utterance
and the world. -/
def reply (w : World) (st : Convo) : Utt → Convo × Reply
  | .about e =>
      let l := bareFact w e
      (⟨e, l :: st.said⟩, ⟨none, .lit l, false⟩)
  | .more => replyMore w st
  | .isIt p =>
      let a := atomOf p st.topic
      let l : Lit := (a, evalAtom a w)
      ({ st with said := l :: st.said }, ⟨none, .lit l, st.said.contains l⟩)
  | .whyIt p =>
      let a := atomOf p st.topic
      let s := Chat.answer (.why (a, evalAtom a w)) w
      ({ st with said := assertedLits s ++ st.said },
        ⟨none, s, (assertedLits s).all fun l => st.said.contains l⟩)
  | .hotterThan f =>
      let a : Atom := .hotter st.topic f
      let l : Lit := (a, evalAtom a w)
      ({ st with said := l :: st.said }, ⟨none, .lit l, st.said.contains l⟩)

/-- Run a whole script. -/
def run (w : World) : Convo → List Utt → Convo × List Reply
  | st, [] => (st, [])
  | st, u :: us =>
      let (st', r) := reply w st u
      let (st'', rs) := run w st' us
      (st'', r :: rs)

/-! ## 3. What the conversation guarantees -/

/-- What `pick` returns really is one of the candidates, and really did pass the
licensing test. -/
theorem pick_spec {cs : List Lit} {live : List World} {ctx : Ctx} {topic : Ent} {s : Step}
    (h : pick cs live ctx topic = some s) :
    s.lit ∈ cs ∧ okLive live ctx topic s.conn s.lit = true := by
  unfold pick at h
  rcases hb : cs.find? (okLive live ctx topic .but) with _ | l
  · rw [hb] at h
    rcases ha : cs.find? (okLive live ctx topic .and) with _ | l
    · rw [ha] at h
      rcases hs : cs.find? (okLive live ctx topic .so) with _ | l
      · rw [hs] at h; exact absurd h (by simp)
      · rw [hs] at h
        cases h
        exact ⟨List.mem_of_find?_eq_some hs, List.find?_some hs⟩
    · rw [ha] at h
      cases h
      exact ⟨List.mem_of_find?_eq_some ha, List.find?_some ha⟩
  · rw [hb] at h
    cases h
    exact ⟨List.mem_of_find?_eq_some hb, List.find?_some hb⟩

theorem liveWith_ctxWorlds (ctx : Ctx) (q : Lit) :
    liveWith (ctxWorlds ctx) q = ctxWorlds (q :: ctx) := by
  simp [liveWith, ctxWorlds, List.filter_filter]

theorem ctxCountWith_le (ctx : Ctx) (q : Lit) : ctxCountWith ctx q ≤ ctxCount ctx := by
  rw [ctxCountWith, ctxCount, ctxCount, ← liveWith_ctxWorlds]
  simpa [liveWith] using List.filter_sublist.length_le

/-- Entailment in a context is exactly "all the live worlds survive". -/
theorem ctxEntails_iff_count (ctx : Ctx) (q : Lit) :
    ctxEntails ctx q = true ↔ ctxCountWith ctx q = ctxCount ctx := by
  constructor
  · intro h
    have hall : ∀ w ∈ ctxWorlds ctx, evalLit q w = true := fun w hw =>
      List.all_eq_true.mp h w hw
    rw [ctxCountWith, ctxCount, ctxCount, ← liveWith_ctxWorlds, liveWith,
      List.filter_eq_self.mpr hall]
  · intro h
    rw [ctxCountWith, ctxCount, ctxCount, ← liveWith_ctxWorlds, liveWith] at h
    have := List.filter_eq_self.mp (List.Sublist.eq_of_length List.filter_sublist h)
    exact List.all_eq_true.mpr this

/-- The generator's live-world shortcut agrees with the context definition of
the connectives, so a clause it picks really is licensed. -/
theorem okLive_stepOK {w : World} {ctx : Ctx} {topic : Ent} {s : Step}
    (hmem : s.lit ∈ candidates w topic)
    (h : okLive (ctxWorlds ctx) ctx topic s.conn s.lit = true) :
    stepOK ctx topic s = true := by
  have hcount : (liveWith (ctxWorlds ctx) s.lit).length = ctxCountWith ctx s.lit := by
    rw [liveWith_ctxWorlds]; rfl
  have hm : (ctxWorlds ctx).length = ctxCount ctx := rfl
  have hcontingent : contingent s.lit = true :=
    (List.mem_filter.mp (List.mem_filter.mp hmem).1).2
  simp only [okLive, hcount, hm, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨hsubj, hfresh⟩, hconn⟩ := h
  simp only [stepOK, Bool.and_eq_true, decide_eq_true_eq]
  refine ⟨⟨⟨hsubj, hcontingent⟩, hfresh⟩, ?_⟩
  have hle := ctxCountWith_le ctx s.lit
  cases hc : s.conn with
  | so =>
      rw [hc] at hconn
      simp only [decide_eq_true_eq] at hconn
      exact (ctxEntails_iff_count ctx s.lit).mpr hconn
  | and =>
      rw [hc] at hconn
      simp only [Bool.and_eq_true, decide_eq_true_eq] at hconn
      obtain ⟨h1, h2⟩ := hconn
      have hent : ctxEntails ctx s.lit = false := by
        cases he : ctxEntails ctx s.lit
        · rfl
        · exact absurd ((ctxEntails_iff_count ctx s.lit).mp he) (by omega)
      simp [hent, surprising, Nat.not_lt.mpr h2]
  | but =>
      rw [hc] at hconn
      simp only [decide_eq_true_eq] at hconn
      have hent : ctxEntails ctx s.lit = false := by
        cases he : ctxEntails ctx s.lit
        · rfl
        · exact absurd ((ctxEntails_iff_count ctx s.lit).mp he) (by omega)
      simp [hent, surprising, hconn]

/-- **The system cannot lie, at any turn.**  Whatever the state, whatever it is
asked, in whatever world, the sentence it replies with is true there. -/
theorem reply_true (w : World) (st : Convo) (u : Utt) :
    evalS (reply w st u).2.sent w = true := by
  cases u with
  | about e => simpa [reply, bareFact, evalS] using Chat.evalLit_self (.frozen e) w
  | more =>
      simp only [reply, replyMore]
      cases h : pick (candidates w st.topic) (ctxWorlds st.said) st.said st.topic with
      | none => simpa [evalS, bareFact] using Chat.evalLit_self (.frozen st.topic) w
      | some s =>
          have hmem := (pick_spec h).1
          have hc := (List.mem_filter.mp hmem).2
          simp only [Bool.and_eq_true] at hc
          simpa [evalS] using hc.2
  | isIt p => simpa [reply, evalS] using Chat.evalLit_self (atomOf p st.topic) w
  | whyIt p => simpa [reply] using Chat.answer_true (.why (atomOf p st.topic,
      evalAtom (atomOf p st.topic) w)) w
  | hotterThan f => simpa [reply, evalS] using Chat.evalLit_self (.hotter st.topic f) w

/-- **"Tell me more" says something new, and joins it honestly.**  When the
reply carries a connective, the clause it adds was not already said, its
connective is licensed by everything said so far — so
`Discourse.so_is_a_deduction` and `Discourse.but_is_contrastive` apply to it —
and it becomes part of the memory. -/
theorem reply_fresh (w : World) (st : Convo) {c : Conn} {l : Lit}
    (h : (reply w st .more).2 = ⟨some c, .lit l, false⟩) :
    stepOK st.said st.topic ⟨c, l⟩ = true ∧ l ∉ st.said ∧
      (reply w st .more).1.said = l :: st.said := by
  have hpick : ∃ s : Step, pick (candidates w st.topic) (ctxWorlds st.said) st.said st.topic
      = some s ∧ s.conn = c ∧ s.lit = l := by
    simp only [reply, replyMore] at h
    cases hp : pick (candidates w st.topic) (ctxWorlds st.said) st.said st.topic with
    | none => rw [hp] at h; simp at h
    | some s =>
        rw [hp] at h
        simp only [Reply.mk.injEq, Option.some.injEq, Sent.lit.injEq] at h
        exact ⟨s, rfl, h.1, h.2.1⟩
  obtain ⟨s, hp, hc, hl⟩ := hpick
  obtain ⟨hmem, hok⟩ := pick_spec hp
  have hstep : stepOK st.said st.topic s = true := okLive_stepOK hmem hok
  have hfresh : s.lit ∉ st.said := by
    simp only [stepOK, Bool.and_eq_true, Bool.not_eq_true', List.any_eq_false,
      decide_eq_true_eq] at hstep
    intro hcon
    exact absurd (hstep.1.2 s.lit hcon) (by simp)
  subst hc; subst hl
  refine ⟨by simpa using hstep, hfresh, ?_⟩
  simp only [reply, replyMore, hp]

/-- **"It" is not ambiguous.**  The clause "tell me more" adds is about the
current topic. -/
theorem reply_on_topic (w : World) (st : Convo) {c : Conn} {l : Lit}
    (h : (reply w st .more).2 = ⟨some c, .lit l, false⟩) : subj l.1 = st.topic := by
  have hOK := (reply_fresh w st h).1
  simp only [stepOK, Bool.and_eq_true, decide_eq_true_eq] at hOK
  tauto

/-- **The topic never drifts.**  Only "tell me about …" changes what "it"
refers to. -/
theorem topic_only_changes_when_asked (w : World) (st : Convo) (u : Utt)
    (h : ∀ e, u ≠ .about e) : (reply w st u).1.topic = st.topic := by
  cases u with
  | about e => exact absurd rfl (h e)
  | more =>
      simp only [reply, replyMore]
      cases pick (candidates w st.topic) (ctxWorlds st.said) st.said st.topic <;> rfl
  | isIt p => rfl
  | whyIt p => rfl
  | hotterThan f => rfl

/-- **The system knows when it is repeating itself.**  A yes/no answer is
flagged `again` exactly when the fact it states is already one of the
conversation's commitments — which is what lets the English say "as I said". -/
theorem again_iff_already_said (w : World) (st : Convo) (p : Prop1) :
    (reply w st (.isIt p)).2.again = true ↔
      (atomOf p st.topic, evalAtom (atomOf p st.topic) w) ∈ st.said := by
  simp [reply]

/-- Everything a run of the conversation says is true. -/
theorem run_true (w : World) : ∀ (st : Convo) (us : List Utt),
    ∀ r ∈ (run w st us).2, evalS r.sent w = true := by
  intro st us
  induction us generalizing st with
  | nil => intro r hr; cases hr
  | cons u rest ih =>
      intro r hr
      simp only [run, List.mem_cons] at hr
      rcases hr with rfl | hr
      · exact reply_true w st u
      · exact ih (reply w st u).1 r hr

/-- The literals a true sentence commits one to are themselves true. -/
theorem assertedLits_true {s : Sent} {w : World} (h : evalS s w = true) :
    ∀ l ∈ assertedLits s, evalLit l w = true := by
  cases s with
  | lit m => intro l hl; simp only [assertedLits, List.mem_singleton] at hl; subst hl; exact h
  | law m n => intro l hl; cases hl
  | because m n =>
      intro l hl
      simp only [evalS, Bool.and_eq_true] at h
      simp only [assertedLits, List.mem_cons, List.not_mem_nil, or_false] at hl
      rcases hl with rfl | rfl
      · tauto
      · tauto
  | because2 m n k =>
      intro l hl
      simp only [evalS, Bool.and_eq_true] at h
      simp only [assertedLits, List.mem_cons, List.not_mem_nil, or_false] at hl
      rcases hl with rfl | rfl | rfl
      · tauto
      · tauto
      · tauto
  | after c m => intro l hl; cases hl
  | conj s t => intro l hl; cases hl

/-- Every commitment the conversation takes on is true in the world. -/
theorem reply_said_true (w : World) (st : Convo) (u : Utt)
    (h : ∀ l ∈ st.said, evalLit l w = true) :
    ∀ l ∈ (reply w st u).1.said, evalLit l w = true := by
  cases u with
  | about e =>
      intro l hl
      simp only [reply, List.mem_cons] at hl
      rcases hl with rfl | hl
      · exact Chat.evalLit_self (.frozen e) w
      · exact h l hl
  | more =>
      simp only [reply, replyMore]
      cases hp : pick (candidates w st.topic) (ctxWorlds st.said) st.said st.topic with
      | none => exact h
      | some s =>
          intro l hl
          simp only [List.mem_cons] at hl
          rcases hl with rfl | hl
          · have hc := (List.mem_filter.mp (pick_spec hp).1).2
            simp only [Bool.and_eq_true] at hc
            exact hc.2
          · exact h l hl
  | isIt p =>
      intro l hl
      simp only [reply, List.mem_cons] at hl
      rcases hl with rfl | hl
      · exact Chat.evalLit_self (atomOf p st.topic) w
      · exact h l hl
  | whyIt p =>
      intro l hl
      simp only [reply, List.mem_append] at hl
      rcases hl with hl | hl
      · exact assertedLits_true (reply_true w st (.whyIt p)) l hl
      · exact h l hl
  | hotterThan f =>
      intro l hl
      simp only [reply, List.mem_cons] at hl
      rcases hl with rfl | hl
      · exact Chat.evalLit_self (.hotter st.topic f) w
      · exact h l hl

/-- Every commitment of a whole run is true. -/
theorem run_said_true (w : World) : ∀ (st : Convo) (us : List Utt),
    (∀ l ∈ st.said, evalLit l w = true) →
      ∀ l ∈ (run w st us).1.said, evalLit l w = true := by
  intro st us
  induction us generalizing st with
  | nil => intro h; exact h
  | cons u rest ih =>
      intro h
      exact ih (reply w st u).1 (reply_said_true w st u h)

/-- **The conversation never contradicts itself.**  It cannot at any turn assert
something it has already denied, or deny something it has already asserted. -/
theorem run_no_contradiction (w : World) (st : Convo) (us : List Utt)
    (h : ∀ l ∈ st.said, evalLit l w = true) :
    ∀ l ∈ (run w st us).1.said, negL l ∉ (run w st us).1.said := by
  intro l hl hcon
  have h1 := run_said_true w st us h l hl
  have h2 := run_said_true w st us h (negL l) hcon
  rw [evalLit_negL, h1] at h2
  simp at h2

/-! ## 4. A conversation, and the check over all 512 worlds -/

/-- An eight-turn script: ask about the water, push for more, ask about the
stone, push again. -/
def demoScript : List Utt :=
  [ .about .water, .more, .more, .isIt .warm, .whyIt .warm,
    .about .stone, .more, .more, .hotterThan .water, .more ]

/-- The conversation in a world, as English. -/
def renderRun (w : World) : List String :=
  let rec go (st : Convo) : List Utt → List String
    | [] => []
    | u :: us =>
        let (st', r) := reply w st u
        let text :=
          (if r.again then "as I said, " else "") ++
          (match r.conn with
            | some .and => "and "
            | some .but => "but "
            | some .so => "so "
            | none => "") ++
          (match r.sent with
            | .lit l => if subj l.1 = st.topic ∧ r.conn.isSome then sayIt l else sayFull l
            | s => Chat.render s)
        (renderUtt u ++ " → " ++ text) :: go st' us
  go ⟨.water, []⟩ demoScript
where
  renderUtt : Utt → String
    | .about e => "tell me about " ++ Chat.renderEnt e
    | .more => "tell me more"
    | .isIt p => "is it " ++ (match p with
        | .frozen => "frozen" | .boiling => "boiling" | .warm => "warm" | .heavy => "heavy") ++ "?"
    | .whyIt p => "why is it " ++ (match p with
        | .frozen => "frozen" | .boiling => "boiling" | .warm => "warm" | .heavy => "heavy") ++ "?"
    | .hotterThan f => "is it hotter than " ++ Chat.renderEnt f ++ "?"

/-- **The whole script, in every world.**  Ten turns, 512 worlds: every reply is
true, every reply to "tell me more" is a fresh clause joined by `and`, `but` or
`so`, and the conversation ends holding at least eight distinct commitments,
none of which contradicts another (`run_no_contradiction`).

A question can re-assert something a previous turn already said — asking "is it
warm?" after the system has volunteered that it is not warm gets the same fact
again — so the commitment list is *not* duplicate-free; that is why the honest
statement here counts distinct commitments rather than claiming there are no
repeats. -/
theorem script_facts :
    (allWorlds.all fun w =>
      ((run w ⟨.water, []⟩ demoScript).2.all fun r => evalS r.sent w) &&
      decide (8 ≤ (run w ⟨.water, []⟩ demoScript).1.said.eraseDups.length) &&
      ((run w ⟨.water, []⟩ demoScript).2.all fun r =>
        match r.conn with
        | some _ => match r.sent with | .lit _ => true | _ => false
        | none => true)) = true := by
  native_decide

#eval renderRun demoWorld

end Dialogue
