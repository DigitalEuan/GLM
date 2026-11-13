import Mathlib
import RequestProject.Abstract

/-!
# Talking about the wide world

`Conversation.lean` answers questions in the narrow world of three things and
six predicates, where every check can be run over all 512 worlds.  This file
carries the same discipline into the world of `WideWorld.lean` and
`Abstract.lean` — twenty-four things, 4200 words, measured and abstract — where
no check may enumerate worlds.

Everything the speaker says is therefore justified in one of exactly two ways:

* a **fact** is read off the world it is talking about, so its truth is by
  construction (`answer_is_true`);
* a **reason** comes from the fixed table `ground`, every entry of which is a
  schema law of `WideWorld` or `Abstract` — proved once, for every number of
  things and every structured world, with no enumeration (`ground_sound`).

## What is proved

* `answer_is_true` — every clause the system utters is true in the world.
* `ground_sound` — a reason really forces what it is a reason for, in *every*
  structured world of *every* size.
* `ground_is_true_when_offered` — the system never offers a reason that is
  false here.
* `reply_no_repetition` — nothing already said is said again; when the stock
  about a thing runs out the system says so instead of repeating itself.
* `demo_transcript` — a six-exchange conversation about the demonstration
  world, pinned exactly.
-/

namespace WideChat

open WideWorld Abstract

set_option maxRecDepth 100000

/-! ## 1. Reasons, from the schema laws -/

/-- The reason table: for a claim, the one thing that would force it.  Every
entry is discharged by a law schema below, so the table is sound for every
number of things and every structured world. -/
def ground {n} : KLit n → Option (KLit n)
  | (.measured (.hot e), true) => some (.measured (.boiling e), true)
  | (.measured (.frozen e), false) => some (.measured (.boiling e), true)
  | (.measured (.warm e), false) => some (.measured (.frozen e), true)
  | (.measured (.heavy e), true) => some (.measured (.massive e), true)
  | (.ancestor a e, true) => some (.mother a e, true)
  | _ => none

/-- **Every reason in the table really forces its claim** — in every structured
world, of every size, by the schemas of `WideWorld` and `Abstract` and no
enumeration at all. -/
theorem ground_sound {n} (s : SWorld n) (l m : KLit n) (h : ground l = some m)
    (hm : evalKLit m s = true) : evalKLit l s = true := by
  match l with
  | (.measured (.hot e), true) =>
      simp only [ground, Option.some.injEq] at h
      subst h
      simp only [evalKLit, evalK, decide_eq_true_eq] at hm ⊢
      exact schema_boiling_hot e s.read hm
  | (.measured (.frozen e), false) =>
      simp only [ground, Option.some.injEq] at h
      subst h
      simp only [evalKLit, evalK, decide_eq_true_eq] at hm ⊢
      exact schema_boiling_not_frozen e s.read hm
  | (.measured (.warm e), false) =>
      simp only [ground, Option.some.injEq] at h
      subst h
      simp only [evalKLit, evalK, decide_eq_true_eq] at hm ⊢
      exact schema_frozen_not_warm e s.read hm
  | (.measured (.heavy e), true) =>
      simp only [ground, Option.some.injEq] at h
      subst h
      simp only [evalKLit, evalK, decide_eq_true_eq] at hm ⊢
      exact schema_massive_heavy e s.read hm
  | (.ancestor a e, true) =>
      simp only [ground, Option.some.injEq] at h
      subst h
      simp only [evalKLit, evalK, decide_eq_true_eq] at hm ⊢
      exact mother_implies_ancestor s a e hm
  | (.measured (.frozen e), true) => simp [ground] at h
  | (.measured (.warm e), true) => simp [ground] at h
  | (.measured (.hot e), false) => simp [ground] at h
  | (.measured (.boiling e), p) => simp [ground] at h
  | (.measured (.heavy e), false) => simp [ground] at h
  | (.measured (.massive e), p) => simp [ground] at h
  | (.measured (.hotter e f), p) => simp [ground] at h
  | (.measured (.heavier e f), p) => simp [ground] at h
  | (.measured (.sameTemp e f), p) => simp [ground] at h
  | (.mother a e, p) => simp [ground] at h
  | (.ancestor a e, false) => simp [ground] at h
  | (.grandmother a e, p) => cases p <;> simp [ground] at h
  | (.sibling a e, p) => simp [ground] at h
  | (.orphan e, p) => simp [ground] at h

/-! ## 2. What there is to say about a thing -/

/-- The words that are about `e`: measured words whose subject is `e`, and kin
words in which `e` comes first. -/
def aboutK {n} (e : Fin n) : KAtom n → Bool
  | .measured (.frozen f) | .measured (.warm f) | .measured (.hot f)
  | .measured (.boiling f) | .measured (.heavy f) | .measured (.massive f) => decide (f = e)
  | .measured (.hotter f _) | .measured (.heavier f _) | .measured (.sameTemp f _) =>
      decide (f = e)
  | .mother f _ | .ancestor f _ | .grandmother f _ | .sibling f _ | .orphan f => decide (f = e)

/-- The stock of assertions about `e` drawn from a given part of the lexicon,
in the order that part lists them. -/
def stockFrom (s : SWorld 24) (src : List (KAtom 24)) (e : Fin 24) : List (KLit 24) :=
  ((src.filter (aboutK e)).filterMap fun a =>
    if evalK a s then some ((a, true) : KLit 24) else none)

/-- Everything in a stock is true. -/
theorem stock_true {s : SWorld 24} {src : List (KAtom 24)} {e : Fin 24} {l : KLit 24}
    (h : l ∈ stockFrom s src e) : evalKLit l s = true := by
  simp only [stockFrom, List.mem_filterMap] at h
  obtain ⟨a, _, ha⟩ := h
  split at ha
  · rename_i hev
    have : l = (a, true) := by simpa using ha.symm
    subst this
    simpa [evalKLit] using hev
  · exact absurd ha (by simp)

/-! ## 3. The conversation -/

/-- What the speaker has been asked. -/
inductive Ask
  /-- "tell me about the stone" -/
  | about (e : Fin 24)
  /-- "tell me about the stone's family" -/
  | family (e : Fin 24)
  /-- "why?" — about the last thing said -/
  | why
deriving DecidableEq, Repr

/-- The state of the conversation: the world, and what has been said. -/
structure Chat where
  world : SWorld 24
  said : List (KLit 24)
  last : Option (KLit 24)

/-- One reply: the new state and the sentence. -/
structure Reply where
  chat : Chat
  text : String
  uttered : List (KLit 24)

/-- The first thing about `e` from this part of the lexicon that has not been
said yet. -/
def freshFact (c : Chat) (src : List (KAtom 24)) (e : Fin 24) : Option (KLit 24) :=
  (stockFrom c.world src e).find? fun l => !c.said.contains l

/-- The reason for the last thing said, if the table has one and it holds
here. -/
def freshReasonK (c : Chat) : Option (KLit 24) :=
  match c.last with
  | none => none
  | some l =>
      match ground l with
      | none => none
      | some m => if evalKLit m c.world then some m else none

/-- **The speaker.**  A request for news about a thing is answered with a fact
not yet said; when the stock is exhausted the speaker says so rather than
repeating itself.  "Why?" is answered from the reason table, and only when the
reason is true here. -/
def replyFact (c : Chat) (src : List (KAtom 24)) (e : Fin 24) : Reply :=
  match freshFact c src e with
  | some l => ⟨⟨c.world, l :: c.said, some l⟩, renderK l ++ ".", [l]⟩
  | none => ⟨c, "there is nothing further I can tell you about " ++ name24 e ++ ".", []⟩

def reply (c : Chat) : Ask → Reply
  | .about e => replyFact c (allKAtoms 24) e
  | .family e => replyFact c (kinAtoms 24) e
  | .why =>
      match c.last with
      | none => ⟨c, "you have not asked me about anything yet.", []⟩
      | some l =>
        match freshReasonK c with
        | some m =>
            if c.said.contains m then
              ⟨⟨c.world, c.said, some m⟩,
                "as I said, " ++ renderK m ++ ", and that is why " ++ renderK l ++ ".", [m]⟩
            else
              ⟨⟨c.world, m :: c.said, some m⟩,
                renderK m ++ ", and that is why " ++ renderK l ++ ".", [m]⟩
        | none => ⟨c, "I have no reason to give: " ++ renderK l ++ " is simply so.", []⟩

/-- **Everything the speaker says is true in the world it is describing.** -/
theorem replyFact_true (c : Chat) (src : List (KAtom 24)) (e : Fin 24) :
    ∀ l ∈ (replyFact c src e).uttered, evalKLit l c.world = true := by
  intro l hl
  simp only [replyFact] at hl
  split at hl
  · rename_i m hm
    have hml : l = m := by simpa using hl
    subst hml
    exact stock_true (List.mem_of_find?_eq_some hm)
  · simp at hl

theorem answer_is_true (c : Chat) (q : Ask) :
    ∀ l ∈ (reply c q).uttered, evalKLit l c.world = true := by
  intro l hl
  cases q with
  | about e => exact replyFact_true c _ e l hl
  | family e => exact replyFact_true c _ e l hl
  | why =>
      simp only [reply] at hl
      split at hl
      · simp at hl
      · rename_i k hk
        split at hl
        · rename_i m hm
          have hmt : evalKLit m c.world = true := by
            simp only [freshReasonK, hk] at hm
            split at hm
            · exact absurd hm (by simp)
            · rename_i m' hm'
              split at hm
              · rename_i hev
                have : m = m' := by simpa using hm.symm
                subst this; exact hev
              · exact absurd hm (by simp)
          split at hl <;> · have : l = m := by simpa using hl
                            subst this; exact hmt
        · simp at hl

/-- **A reason offered is a reason that holds and that forces the claim.** -/
theorem reason_is_a_ground (c : Chat) (l m : KLit 24) (hl : c.last = some l)
    (hm : freshReasonK c = some m) :
    evalKLit m c.world = true ∧ ground l = some m ∧ evalKLit l c.world = true := by
  simp only [freshReasonK, hl] at hm
  split at hm
  · exact absurd hm (by simp)
  · rename_i m' hg
    split at hm
    · rename_i hev
      have hmm : m = m' := by simpa using hm.symm
      subst hmm
      exact ⟨hev, hg, ground_sound c.world l m hg hev⟩
    · exact absurd hm (by simp)

/-- **Nothing is said twice.**  A fact offered as news was not in the record,
and it is in the record afterwards. -/
theorem reply_no_repetition (c : Chat) (src : List (KAtom 24)) (e : Fin 24) (l : KLit 24)
    (h : (replyFact c src e).uttered = [l]) :
    l ∉ c.said ∧ l ∈ (replyFact c src e).chat.said := by
  rcases hf : freshFact c src e with _ | m
  · simp [replyFact, hf] at h
  · have hr : replyFact c src e =
        ⟨⟨c.world, m :: c.said, some m⟩, renderK m ++ ".", [m]⟩ := by
      simp [replyFact, hf]
    rw [hr] at h ⊢
    have hml : m = l := by simpa using h
    subst hml
    have hfind := List.find?_some hf
    simp only [Bool.not_eq_true', List.contains_eq_mem, decide_eq_false_iff_not] at hfind
    exact ⟨by simpa using hfind, by simp⟩

/-- When the stock about a thing is exhausted the speaker says so and utters no
clause at all. -/
theorem exhausted_says_nothing (c : Chat) (src : List (KAtom 24)) (e : Fin 24)
    (h : freshFact c src e = none) : (replyFact c src e).uttered = [] := by
  simp only [replyFact, h]

/-! ## 4. A conversation about the demonstration world -/

/-- The opening state: the structured demonstration world, nothing said yet. -/
def start : Chat := ⟨demoS, [], none⟩

/-- Run a list of questions. -/
def run : Chat → List Ask → List String
  | _, [] => []
  | c, q :: rest => let r := reply c q; r.text :: run r.chat rest

/-- Six exchanges: a measured fact with its reason, then the abstract half of
the lexicon, ending in a reason already on the record. -/
def script : List Ask :=
  [.about ⟨16, by norm_num⟩, .why, .family ⟨9, by norm_num⟩,
   .family ⟨9, by norm_num⟩, .family ⟨9, by norm_num⟩, .why]

/-- **The transcript, pinned exactly.**  A measured fact and its reason, then
three abstract facts, then a reason that the speaker notices it has already
given. -/
theorem demo_transcript :
    run start script =
      ["the clay is hot.",
       "the clay is boiling, and that is why the clay is hot.",
       "the glass is a sibling of the wood.",
       "the glass is the mother of the brick.",
       "the glass is an ancestor of the brick.",
       "as I said, the glass is the mother of the brick, and that is why " ++
         "the glass is an ancestor of the brick."] := by
  native_decide

/-- The transcript, for reading. -/
def demoChat : List String := run start script

end WideChat
