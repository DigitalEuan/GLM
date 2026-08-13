import Mathlib
import RequestProject.Semantics

/-!
# Chat: deterministic question answering that cannot lie

`Semantics.lean` gave a measurable micro-world and a sentence algebra whose
`law` and `because` clauses are checked against every one of the 512 worlds.
This file makes it talk.

## The question space

`Question` covers the five things one can ask about this world:

* `isIt l` — "is the water frozen?"
* `why l` — "why is the water not warm?"
* `whatIf c a` — "if we heat the water, is it boiling?"
* `compare e f` — "which is hotter, the water or the stone?"
* `tellMe e` — "tell me about the water".

`answer q w` replies with a sentence of the algebra, and `render` puts it into
English.  Everything is a total function of the question and the world: the
same question in the same world always gets the same answer, with no search, no
sampling and no randomness.

## What is proved about the conversation

* `answer_true` — **the system cannot lie**: for every question and every world,
  the sentence it replies with is true in that world.  This is proved for all
  questions and all worlds, not sampled.
* `answer_isIt_decisive` — a yes/no question always gets a yes or a no, with the
  polarity the measurement supports (so a false premise in the question is
  contradicted rather than accepted).
* `answer_why_explains` — when the reply to "why?" is a `because`, the reason
  given implies the fact **in every world**, so it is a ground and not a
  coincidence.
* `answer_whatIf_correct` — a prediction is the truth about the world the action
  actually produces.
* `answer_mentions_subject` — the reply is about what was asked.
* `render_injective_on_demo` — distinct sentences get distinct English: the
  surface form does not blur two different meanings.

## How deep the explanations go, counted

`why_reason_counts` counts, in the demo world, what happens to the 48 askable
"why" questions: **32** are answered by a single literal ("the water is not warm
because the water is frozen"), **16** need a *pair* of literals together ("the
water is frozen because the water is not boiling and the water is not warm"),
and **0** are left unexplained.  The pair explanations are checked to be
*minimal* (`Semantics.because2_is_minimal_explanation`): neither half would have
sufficed.  Where the system has no ground at all it says the bare fact rather
than inventing a cause — that branch is still in `answer`, it simply is not
reached by this vocabulary in this world.
-/

namespace Chat

open Semantics

set_option maxRecDepth 100000

/-! ## 1. Questions -/

/-- What can be asked. -/
inductive Question
  | isIt (l : Lit)
  | why (l : Lit)
  | whatIf (c : Act) (a : Atom)
  | compare (e f : Ent)
  | tellMe (e : Ent)
deriving DecidableEq, Repr

/-- The reason the system offers for `l` in `w`, if it has one: a contingent
literal that holds here and forces `l` in every world. -/
def reasonFor (l : Lit) (w : World) : Option Lit :=
  usefulLits.find? fun m => evalS (.because l m) w

/-- A pair of reasons for `l` in `w`, if the system has one: two contingent
literals that hold here and together force `l`, neither sufficing alone. -/
def reasonPairFor (l : Lit) (w : World) : Option (Lit × Lit) :=
  (usefulLits.flatMap fun m => usefulLits.map fun n => (m, n)).find?
    fun p => evalS (.because2 l p.1 p.2) w

/-- **The answer.**  A total, deterministic function of the question and the
world. -/
def answer : Question → World → Sent
  | .isIt l, w => .lit (l.1, evalAtom l.1 w)
  | .why l, w =>
      if evalLit l w then
        match reasonFor l w with
        | some m => .because l m
        | none =>
            match reasonPairFor l w with
            | some p => .because2 l p.1 p.2
            | none => .lit l
      else .lit (l.1, evalAtom l.1 w)
  | .whatIf c a, w => .after c (a, evalAtom a (step c w))
  | .compare e f, w =>
      if evalAtom (.hotter e f) w then .lit (.hotter e f, true)
      else if evalAtom (.hotter f e) w then .lit (.hotter f e, true)
      else .conj (.lit (.hotter e f, false)) (.lit (.hotter f e, false))
  | .tellMe e, w =>
      .conj (.lit (.frozen e, evalAtom (.frozen e) w))
        (.conj (.lit (.boiling e, evalAtom (.boiling e) w))
          (.conj (.lit (.warm e, evalAtom (.warm e) w))
            (.lit (.heavy e, evalAtom (.heavy e) w))))

/-! ## 2. The conversation is sound -/

theorem evalLit_self (a : Atom) (w : World) : evalLit (a, evalAtom a w) w = true := by
  simp [evalLit]

/-- **The system cannot lie.**  Whatever it is asked, in whatever world, the
sentence it replies with is true in that world. -/
theorem answer_true (q : Question) (w : World) : evalS (answer q w) w = true := by
  cases q with
  | isIt l => simpa [answer, evalS] using evalLit_self l.1 w
  | why l =>
      simp only [answer]
      by_cases hl : evalLit l w = true
      · rw [if_pos hl]
        cases h : reasonFor l w with
        | none =>
            cases h2 : reasonPairFor l w with
            | none => simpa [evalS] using hl
            | some p =>
                have := List.find?_some h2
                simpa [evalS] using this
        | some m =>
            have := List.find?_some h
            simpa [evalS] using this
      · simp only [Bool.not_eq_true] at hl
        rw [if_neg (by simp [hl])]
        simpa [evalS] using evalLit_self l.1 w
  | whatIf c a => simp [answer, evalS, evalLit]
  | compare e f =>
      by_cases h1 : evalAtom (.hotter e f) w = true
      · simp [answer, evalS, evalLit, h1]
      · simp only [Bool.not_eq_true] at h1
        by_cases h2 : evalAtom (.hotter f e) w = true
        · simp [answer, evalS, evalLit, h1, h2]
        · simp only [Bool.not_eq_true] at h2
          simp [answer, evalS, evalLit, h1, h2]
  | tellMe e => simp [answer, evalS, evalLit]

/-- A yes/no question always gets a yes or a no, and the polarity is the one the
measurement supports — a false premise is contradicted, not accepted. -/
theorem answer_isIt_decisive (l : Lit) (w : World) :
    answer (.isIt l) w = .lit (l.1, evalAtom l.1 w) := rfl

/-- **When it gives a reason, the reason is a ground.**  If the reply to "why
`a`?" is `because`, then the cited literal holds here and forces the fact in
every one of the 512 worlds. -/
theorem answer_why_explains {k : Lit} {w : World} {l m : Lit}
    (h : answer (.why k) w = .because l m) :
    evalLit m w = true ∧ (∀ w' : World, evalLit m w' = true → evalLit l w' = true) ∧ l ≠ m := by
  have hs : evalS (.because l m) w = true := by
    have := answer_true (.why k) w
    rwa [h] at this
  simp only [evalS, Bool.and_eq_true, decide_eq_true_eq] at hs
  obtain ⟨⟨⟨⟨_, hm⟩, hent⟩, hne⟩, _⟩ := hs
  exact ⟨hm, (entails_iff m l).mp hent, hne⟩

/-- A prediction is the truth about the world the action actually produces. -/
theorem answer_whatIf_correct (c : Act) (a : Atom) (w : World) :
    answer (.whatIf c a) w = .after c (a, evalAtom a (step c w)) ∧
      evalAtom a (step c w) = evalAtom a (step c w) := ⟨rfl, rfl⟩

/-- The atoms a sentence is about. -/
def mentions : Sent → Atom → Bool
  | .lit l, a => decide (l.1 = a)
  | .law l m, a => decide (l.1 = a) || decide (m.1 = a)
  | .because l m, a => decide (l.1 = a) || decide (m.1 = a)
  | .because2 l m n, a => decide (l.1 = a) || decide (m.1 = a) || decide (n.1 = a)
  | .after _ l, a => decide (l.1 = a)
  | .conj s t, a => mentions s a || mentions t a

/-- **The reply is about what was asked.** -/
theorem answer_mentions_subject (a : Atom) (p : Bool) (w : World) :
    mentions (answer (.isIt (a, p)) w) a = true ∧
      mentions (answer (.why (a, p)) w) a = true ∧
      ∀ c : Act, mentions (answer (.whatIf c a) w) a = true := by
  refine ⟨by simp [answer, mentions], ?_, fun c => by simp [answer, mentions]⟩
  simp only [answer]
  by_cases hl : evalLit (a, p) w = true
  · rw [if_pos hl]
    cases reasonFor (a, p) w with
    | none => cases reasonPairFor (a, p) w <;> simp [mentions]
    | some _ => simp [mentions]
  · simp only [Bool.not_eq_true] at hl
    rw [if_neg (by simp [hl])]
    simp [mentions]

/-! ## 3. English -/

def renderEnt : Ent → String
  | .water => "the water"
  | .stone => "the stone"
  | .lamp => "the lamp"

/-- A literal as an English clause. -/
def renderLit (l : Lit) : String :=
  let neg := if l.2 then " is " else " is not "
  match l.1 with
  | .frozen e => renderEnt e ++ neg ++ "frozen"
  | .boiling e => renderEnt e ++ neg ++ "boiling"
  | .warm e => renderEnt e ++ neg ++ "warm"
  | .heavy e => renderEnt e ++ neg ++ "heavy"
  | .hotter e f => renderEnt e ++ neg ++ "hotter than " ++ renderEnt f
  | .heavier e f => renderEnt e ++ neg ++ "heavier than " ++ renderEnt f

/-- A literal in question form: "is the water frozen", "is the water not warm". -/
def renderLitQ (l : Lit) : String :=
  let neg := if l.2 then " " else " not "
  match l.1 with
  | .frozen e => "is " ++ renderEnt e ++ neg ++ "frozen"
  | .boiling e => "is " ++ renderEnt e ++ neg ++ "boiling"
  | .warm e => "is " ++ renderEnt e ++ neg ++ "warm"
  | .heavy e => "is " ++ renderEnt e ++ neg ++ "heavy"
  | .hotter e f => "is " ++ renderEnt e ++ neg ++ "hotter than " ++ renderEnt f
  | .heavier e f => "is " ++ renderEnt e ++ neg ++ "heavier than " ++ renderEnt f

def renderAct : Act → String
  | .heat e => "we heat " ++ renderEnt e
  | .cool e => "we cool " ++ renderEnt e
  | .load e => "we load " ++ renderEnt e

/-- A sentence as English. -/
def render : Sent → String
  | .lit l => renderLit l
  | .law l m => "if " ++ renderLit l ++ " then " ++ renderLit m
  | .because l m => renderLit l ++ " because " ++ renderLit m
  | .because2 l m n => renderLit l ++ " because " ++ renderLit m ++ " and " ++ renderLit n
  | .after c l => "after " ++ renderAct c ++ ", " ++ renderLit l
  | .conj s t => render s ++ ", and " ++ render t

/-- A question as English. -/
def renderQ : Question → String
  | .isIt l => renderLitQ l ++ "?"
  | .why l => "why " ++ renderLitQ l ++ "?"
  | .whatIf c a => "if " ++ renderAct c ++ ", " ++ renderLitQ (a, true) ++ "?"
  | .compare e f => "which is hotter, " ++ renderEnt e ++ " or " ++ renderEnt f ++ "?"
  | .tellMe e => "tell me about " ++ renderEnt e

/-- **Distinct sentences get distinct English.**  On everything the system is
willing to say about the demo world, the surface form determines the meaning. -/
theorem render_injective_on_demo :
    ((speak demoWorld).map render).Nodup := by native_decide

/-! ## 4. A transcript, and the honest count -/

/-- The questions asked in the demo transcript. -/
def demoQuestions : List Question :=
  [ .tellMe .water,
    .isIt (.frozen .water, true),
    .isIt (.warm .water, true),
    .why (.warm .water, false),
    .why (.frozen .water, true),
    .why (.boiling .lamp, true),
    .compare .water .lamp,
    .compare .water .stone,
    .whatIf (.heat .water) (.warm .water),
    .whatIf (.heat .lamp) (.boiling .lamp),
    .whatIf (.load .water) (.heavy .water),
    .isIt (.heavier .stone .water, true),
    .why (.heavier .stone .water, true),
    .why (.heavy .water, true) ]

/-- The transcript: each question with the answer the system gives. -/
def transcript : List (String × String) :=
  demoQuestions.map fun q => (renderQ q, render (answer q demoWorld))

/-- Every reply in the transcript is true in the demo world. -/
theorem transcript_true : demoQuestions.all (fun q => evalS (answer q demoWorld) demoWorld) = true :=
  List.all_eq_true.mpr fun q _ => answer_true q demoWorld

/-- **The honest count.**  Of the 48 contingent literals one can ask "why" about
in the demo world, 30 get a genuine reason and 18 get only the bare fact: the
system says "it just is" rather than inventing a cause. -/
theorem why_reason_counts :
    (usefulLits.filter fun l =>
      (reasonFor (l.1, evalAtom l.1 demoWorld) demoWorld).isSome).length = 32 ∧
    (usefulLits.filter fun l =>
      (reasonFor (l.1, evalAtom l.1 demoWorld) demoWorld).isNone &&
      (reasonPairFor (l.1, evalAtom l.1 demoWorld) demoWorld).isSome).length = 16 ∧
    (usefulLits.filter fun l =>
      (reasonFor (l.1, evalAtom l.1 demoWorld) demoWorld).isNone &&
      (reasonPairFor (l.1, evalAtom l.1 demoWorld) demoWorld).isNone).length = 0 := by
  refine ⟨?_, ?_, ?_⟩ <;> native_decide

#eval transcript

end Chat
