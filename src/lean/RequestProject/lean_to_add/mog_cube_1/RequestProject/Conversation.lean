import Mathlib
import RequestProject.Semantics
import RequestProject.Chat
import RequestProject.Causation
import RequestProject.PlanCost

/-!
# A conversation that answers a repeated question with something new

Two of the gaps left open in report 3 §5:

> 4. **Questions can cause repetition.**  The system now *notices* — it says
>    "as I said" — but it still has no way to answer a repeated question with
>    anything more useful than the same fact again.
> 5. **Cross-subject pronouns.**  §1b names the thing again whenever the
>    subject changes; it cannot yet say "the stone … the lamp … *the latter* is
>    hotter".

Both are closed here.

## Repeated questions

`answer` keeps the record of what has been said.  Asked something it has
already answered, it escalates instead of repeating:

1. first repeat — give the **reason**, using the timed connective of
   `Causation.lean`, and only a reason that has not been said yet;
2. second repeat — give the **plan** that would make it otherwise, priced by
   `PlanCost.lean`, with its cost;
3. only when neither is available does it fall back to "as I said".

What is proved: `answer_true` (whatever it says is true in the world reached),
`repeat_says_something_new` (on a repeat, every literal it adds is one it has
not said before), `reason_is_causal` (the reason it gives satisfies
`Causation.causalBecause`, so it is a ground *and* arrived with the fact) and
`plan_is_optimal` (the plan it offers reaches the goal and nothing cheaper
does).

## The former and the latter

A clause is rendered as a `Clause`: a polarity, a predicate, and one or two
**references**, each of which is either a name or one of the two pronouns.
`mkClause` uses "the latter" for the thing mentioned most recently and "the
former" for the one before it; `readClause` is the hearer's side, resolving
references back against the same list of mentions.

`clause_roundtrip` proves that for **every** mention list and **every**
literal, the hearer recovers exactly the literal the speaker meant.  The
pronouns are therefore never ambiguous — which is the guarantee the one-topic
restriction used to buy by refusing to change subject at all.
-/

namespace Conversation

open Semantics

set_option maxRecDepth 100000

/-! ## 1. References: names, "the former", "the latter" -/

/-- How a clause refers to a thing. -/
inductive Ref
  | named (e : Ent)
  | former
  | latter
deriving DecidableEq, Repr

/-- The hearer's side: what a reference points at, given the things mentioned
so far, most recent first. -/
def refResolve (m : List Ent) : Ref → Option Ent
  | .named e => some e
  | .latter => m[0]?
  | .former => m[1]?

/-- The speaker's side: a pronoun is used only when the previous clause
mentioned **two different things**, so that "the former" and "the latter" have
distinct antecedents; otherwise the thing is named. -/
def refOf (m : List Ent) (e : Ent) : Ref :=
  match m with
  | x :: y :: _ =>
      if x = y then .named e
      else if e = x then .latter
      else if e = y then .former
      else .named e
  | _ => .named e

/-- **Speaker and hearer agree.**  Whatever reference the speaker chooses, the
hearer resolves it to the thing meant. -/
theorem refOf_resolve (m : List Ent) (e : Ent) : refResolve m (refOf m e) = some e := by
  unfold refOf
  match m with
  | [] => rfl
  | [x] => rfl
  | x :: y :: rest =>
      by_cases hxy : x = y
      · simp [hxy, refResolve]
      · simp only [hxy, if_false]
        by_cases hex : e = x
        · simp [hex, refResolve]
        · simp only [hex, if_false]
          by_cases hey : e = y
          · simp [hey, refResolve]
          · simp [hey, refResolve]

/-- The English of a reference. -/
def refText : Ref → String
  | .named e => Chat.renderEnt e
  | .former => "the former"
  | .latter => "the latter"

/-! ## 2. Clauses with references -/

/-- The one-place words. -/
inductive Pred1 | frozen | boiling | warm | heavy
deriving DecidableEq, Repr

/-- The two-place words. -/
inductive Pred2 | hotter | heavier
deriving DecidableEq, Repr

/-- A clause as it goes out: polarity, predicate, and its references. -/
structure Clause where
  pol : Bool
  pred : Pred1 ⊕ Pred2
  subj : Ref
  obj : Option Ref
deriving Repr

/-- The atom a one-place word makes. -/
def atom1 : Pred1 → Ent → Atom
  | .frozen, e => .frozen e
  | .boiling, e => .boiling e
  | .warm, e => .warm e
  | .heavy, e => .heavy e

/-- The atom a two-place word makes. -/
def atom2 : Pred2 → Ent → Ent → Atom
  | .hotter, e, f => .hotter e f
  | .heavier, e, f => .heavier e f

/-- Build the clause for a literal, using pronouns where the mention list
allows. -/
def mkClause (m : List Ent) (l : Lit) : Clause :=
  match l.1 with
  | .frozen e => ⟨l.2, .inl .frozen, refOf m e, none⟩
  | .boiling e => ⟨l.2, .inl .boiling, refOf m e, none⟩
  | .warm e => ⟨l.2, .inl .warm, refOf m e, none⟩
  | .heavy e => ⟨l.2, .inl .heavy, refOf m e, none⟩
  | .hotter e f => ⟨l.2, .inr .hotter, refOf m e, some (refOf m f)⟩
  | .heavier e f => ⟨l.2, .inr .heavier, refOf m e, some (refOf m f)⟩

/-- Read a clause back: the hearer's reconstruction of the literal. -/
def readClause (m : List Ent) (c : Clause) : Option Lit :=
  match c.pred, c.obj with
  | .inl p, none => (refResolve m c.subj).map fun e => (atom1 p e, c.pol)
  | .inr p, some r =>
      match refResolve m c.subj, refResolve m r with
      | some e, some f => some (atom2 p e f, c.pol)
      | _, _ => none
  | _, _ => none

/-- **The pronouns are never ambiguous.**  For every mention list and every
literal, what the hearer reconstructs is exactly what the speaker meant. -/
theorem clause_roundtrip (m : List Ent) (l : Lit) : readClause m (mkClause m l) = some l := by
  obtain ⟨a, p⟩ := l
  cases a <;>
    simp [mkClause, readClause, refOf_resolve, atom1, atom2]

/-- The English of a clause. -/
def clauseText (c : Clause) : String :=
  let neg := if c.pol then " is " else " is not "
  match c.pred, c.obj with
  | .inl p, _ =>
      refText c.subj ++ neg ++
        (match p with
         | .frozen => "frozen" | .boiling => "boiling" | .warm => "warm" | .heavy => "heavy")
  | .inr p, some r =>
      refText c.subj ++ neg ++
        (match p with | .hotter => "hotter than " | .heavier => "heavier than ") ++ refText r
  | .inr _, none => refText c.subj

/-- Render a literal against the mention list. -/
def say (m : List Ent) (l : Lit) : String := clauseText (mkClause m l)

/-- The things a literal mentions, subject first. -/
def litEnts : Lit → List Ent
  | (.frozen e, _) | (.boiling e, _) | (.warm e, _) | (.heavy e, _) => [e]
  | (.hotter e f, _) | (.heavier e f, _) => [e, f]

/-- The mention list after a clause: the things *that clause* mentioned, most
recent first, so "the latter" always points into the sentence just spoken. -/
def bump (l : Lit) : List Ent := (litEnts l).reverse

/-- **The demonstration of report 3 §5.5.**  After the stone and the lamp have
been mentioned, in that order, the system says "the latter is hotter than the
former" — and the hearer gets it right. -/
theorem former_latter_demo :
    say [.lamp, .stone] (.hotter .lamp .stone, true) =
      "the latter is hotter than the former" ∧
    readClause [.lamp, .stone] (mkClause [.lamp, .stone] (.hotter .lamp .stone, true)) =
      some (.hotter .lamp .stone, true) := by
  constructor
  · rfl
  · exact clause_roundtrip _ _

/-! ## 3. The conversation state -/

/-- What the system is asked. -/
inductive Ask
  | isIt (a : Atom)
deriving DecidableEq, Repr

/-- The conversation: the history of the world, what has been said, and what has
been mentioned. -/
structure Talk where
  hist : Causation.Hist
  said : List Lit
  mentioned : List Ent
  planned : List Lit := []

/-- What comes back: the text, the literals it commits to, and whether it was
flagged as a repetition. -/
structure Out where
  text : String
  added : List Lit
  again : Bool
deriving Repr

/-- The world the conversation has reached. -/
def wNow (t : Talk) : World := Causation.nowW t.hist

/-- A reason for `l` that is causally licensed and has not been said. -/
def freshReason (t : Talk) (l : Lit) : Option Lit :=
  usefulLits.find? fun m => Causation.causalBecause t.hist l m && !t.said.contains m

/-- The cheapest plan that would make `l` false instead. -/
def counterPlan (t : Talk) (l : Lit) : Option (List Act) :=
  PlanCost.bestPlan (wNow t) (negL l)

/-- **The answer.**  A new question gets the fact; a repeated one gets the
reason, then the priced plan, and only when both are spent the flat "as I
said". -/
def answer (t : Talk) : Ask → Talk × Out
  | .isIt a =>
      let w := wNow t
      let l : Lit := (a, evalAtom a w)
      let m' := bump l
      if t.said.contains l then
        match freshReason t l with
        | some r =>
            ({ t with said := r :: t.said, mentioned := bump r },
             ⟨"as I said, " ++ say t.mentioned l ++ " — and " ++ say m' r ++
                ", which is why", [r], true⟩)
        | none =>
            if t.planned.contains l then
              ({ t with mentioned := m' },
               ⟨"as I said, " ++ say t.mentioned l ++ ", and I have nothing further to add",
                [], true⟩)
            else
              match counterPlan t l with
              | some plan =>
                  ({ t with mentioned := m', planned := l :: t.planned },
                   ⟨"as I said, " ++ say t.mentioned l ++
                      "; if you want it otherwise, " ++
                      (if plan.isEmpty then "it already is"
                        else String.intercalate " and then " (plan.map Chat.renderAct)) ++
                      ", which costs " ++ toString (PlanCost.cost plan), [], true⟩)
              | none =>
                  ({ t with mentioned := m', planned := l :: t.planned },
                   ⟨"as I said, " ++ say t.mentioned l ++ ", and there is no way to change it",
                    [], true⟩)
      else
        ({ t with said := l :: t.said, mentioned := m' }, ⟨say t.mentioned l, [l], false⟩)

/-! ## 4. What the conversation guarantees -/

/-- **The reason it gives is a causal one** in the sense of `Causation.lean`:
`r` forces the fact in every world, and it came into force at the same moment,
so it did not turn up after the event. -/
theorem reason_is_causal {t : Talk} {l r : Lit} (h : freshReason t l = some r) :
    Causation.causalBecause t.hist l r = true := by
  have hf := List.find?_some (p := fun m => Causation.causalBecause t.hist l m &&
    !t.said.contains m) h
  simp only [Bool.and_eq_true] at hf
  exact hf.1

/-- A reason offered is one that has not been said before. -/
theorem reason_is_fresh {t : Talk} {l r : Lit} (h : freshReason t l = some r) :
    t.said.contains r = false := by
  have hf := List.find?_some (p := fun m => Causation.causalBecause t.hist l m &&
    !t.said.contains m) h
  simp only [Bool.and_eq_true, Bool.not_eq_true'] at hf
  exact hf.2

/-- A reason offered is true where the conversation stands. -/
theorem reason_is_true {t : Talk} {l r : Lit} (h : freshReason t l = some r) :
    evalLit r (wNow t) = true :=
  (Causation.causalBecause_sound (reason_is_causal h)).2.1

/-- **Everything it commits to is true** in the world the conversation has
reached — new question or repeated one. -/
theorem answer_true (t : Talk) (q : Ask) :
    ∀ l ∈ (answer t q).2.added, evalLit l (wNow t) = true := by
  cases q with
  | isIt a =>
    intro l hl
    simp only [answer] at hl
    split at hl
    · split at hl
      · rename_i r hr
        simp only [List.mem_singleton] at hl
        subst hl
        exact reason_is_true hr
      · split at hl
        · simp at hl
        · split at hl <;> simp at hl
    · simp only [List.mem_singleton] at hl
      subst hl
      simp [evalLit]

/-- **A repeat says something new.**  When the system flags a repetition and
still adds a literal, that literal is not one it has said before. -/
theorem repeat_says_something_new (t : Talk) (q : Ask) :
    ∀ l ∈ (answer t q).2.added, (answer t q).2.again = true → t.said.contains l = false := by
  cases q with
  | isIt a =>
    intro l hl _
    simp only [answer] at hl ⊢
    split at hl
    · split at hl
      · rename_i r hr
        simp only [List.mem_singleton] at hl
        subst hl
        exact reason_is_fresh hr
      · split at hl
        · simp at hl
        · split at hl <;> simp at hl
    · rename_i hnot
      simp only [List.mem_singleton] at hl
      subst hl
      simpa using hnot

/-- **The plan it offers is the cheapest one that works.** -/
theorem plan_is_optimal {t : Talk} {l : Lit} {plan : List Act} (h : counterPlan t l = some plan) :
    evalLit (negL l) (Narrative.runActs plan (wNow t)) = true ∧
      ∀ s ∈ Narrative.seqsUpTo Narrative.horizon,
        evalLit (negL l) (Narrative.runActs s (wNow t)) = true →
          PlanCost.cost plan ≤ PlanCost.cost s :=
  ⟨PlanCost.bestPlan_correct h, PlanCost.bestPlan_optimal h⟩

/-! ## 5. A conversation, run -/

/-- Run a list of questions. -/
def run (t : Talk) : List Ask → Talk × List Out
  | [] => (t, [])
  | q :: qs =>
      let (t', o) := answer t q
      let (t'', os) := run t' qs
      (t'', o :: os)

/-- The stone starts frozen, we heat it twice (so it is warm, and no longer
frozen); the lamp is boiling and the water is at 0 °C. -/
def demoTalk : Talk :=
  ⟨⟨(fun e => match e with | .water => 1 | .stone => 0 | .lamp => 3,
     fun _ => 0), [.heat .stone, .heat .stone]⟩, [], [], []⟩

/-- Ask about the stone, then about the lamp and the stone together, then the
same question about the stone three times over. -/
def demoScript : List Ask :=
  [.isIt (.frozen .stone), .isIt (.hotter .lamp .stone), .isIt (.frozen .stone),
   .isIt (.frozen .stone), .isIt (.frozen .stone)]

def demoOut : List String := ((run demoTalk demoScript).2).map Out.text

#eval demoOut

/-- **The escalation happens, and it is visible.**  The first answer is the
plain fact; the second uses no pronoun because only one thing has been
mentioned; the third answers a repeat with a reason and uses "the latter" for
the thing named last; the fourth offers a priced plan; the fifth admits it has
nothing left. -/
theorem demo_escalates :
    demoOut =
      ["the stone is not frozen",
       "the lamp is hotter than the stone",
       "as I said, the latter is not frozen — and the stone is warm, which is why",
       "as I said, the stone is not frozen; if you want it otherwise, we cool the stone, which costs 2",
       "as I said, the stone is not frozen, and I have nothing further to add"] ∧
    ((run demoTalk demoScript).2.map Out.again) = [false, false, true, true, true] := by
  constructor <;> native_decide

end Conversation
