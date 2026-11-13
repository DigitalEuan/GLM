import Mathlib
import RequestProject.Discourse

/-!
# Paragraphs that change the subject

`Discourse.lean` keeps one topic for a whole paragraph, which is what makes the
pronoun "it" safe.  The price is that the most interesting inferences in this
world cannot be said, because they join facts about *different* things:

> the water is frozen, but the lamp is boiling, so the lamp is hotter than the
> water

This file lifts the one-topic restriction.  A clause may now be about anything,
and the licensing test is the same one as before applied to that clause's own
subject:

    wstepOK ctx s  =  Discourse.stepOK ctx (subj s.lit.1) s

so every guarantee proved in `Discourse.lean` — `so_is_a_deduction`,
`but_is_contrastive`, `and_is_informative`, `para_information_increases` —
transfers unchanged (`wstep_so_is_a_deduction` and friends below).  What is lost
is topic continuity, and the rendering pays for it honestly: the pronoun "it"
is used **only** when the clause has the same subject as the clause before it,
and otherwise the thing is named (`sayStep`).

## What is measured

`wcorpus` is the paragraph the generator produces in each of the 512 worlds.
`wcorpus_facts` proves that every one of them is valid, and counts the clauses:
of 3072 joined clauses, 2524 change the subject, and 330 of those are `so`
clauses — cross-subject deductions of exactly the kind above, which the
one-topic system could not state at all.
-/

namespace WideDiscourse

open Semantics Discourse

set_option maxRecDepth 100000

/-! ## 1. Clauses about anything -/

/-- A clause is licensed exactly as before, judged against its own subject. -/
def wstepOK (ctx : Ctx) (s : Step) : Bool := stepOK ctx (subj s.lit.1) s

/-- A paragraph without a fixed topic. -/
structure WPara where
  opening : Lit
  steps : List Step
deriving Repr

/-- Validity: every clause true here, every connective licensed. -/
def wvalidFrom (w : World) (ctx : Ctx) : List Step → Bool
  | [] => true
  | s :: rest => evalLit s.lit w && wstepOK ctx s && wvalidFrom w (s.lit :: ctx) rest

def wvalid (w : World) (p : WPara) : Bool :=
  contingent p.opening && evalLit p.opening w && wvalidFrom w [p.opening] p.steps

/-- The literals of a paragraph. -/
def wparaLits (p : WPara) : List Lit := p.opening :: p.steps.map (·.lit)

/-! ## 2. The guarantees, inherited -/

/-- `so` still means the paragraph is already committed to the clause. -/
theorem wstep_so_is_a_deduction {c : Ctx} {s : Step} (h : wstepOK c s = true)
    (hso : s.conn = Conn.so) :
    ∀ w : World, (∀ l ∈ c, evalLit l w = true) → evalLit s.lit w = true :=
  so_is_a_deduction h hso

/-- `but` still means fewer than half of the live worlds agree. -/
theorem wstep_but_is_contrastive {c : Ctx} {s : Step} (h : wstepOK c s = true)
    (hbut : s.conn = Conn.but) :
    2 * ctxCountWith c s.lit < ctxCount c ∧ ctxEntails c s.lit = false :=
  but_is_contrastive h hbut

/-- `and` still means news. -/
theorem wstep_and_is_informative {c : Ctx} {s : Step} (h : wstepOK c s = true)
    (hand : s.conn = Conn.and) :
    (∃ w : World, (∀ l ∈ c, evalLit l w = true) ∧ evalLit s.lit w = false) ∧
      ctxCount c ≤ 2 * ctxCountWith c s.lit :=
  and_is_informative h hand

/-- Each `and`/`but` clause still cuts the live worlds down. -/
theorem wstep_information_increases {c : Ctx} {s : Step} (h : wstepOK c s = true)
    (hne : s.conn ≠ Conn.so) : ctxCount (s.lit :: c) < ctxCount c :=
  para_information_increases h hne

/-- **Soundness.**  Every clause is true in the world described. -/
theorem wpara_sound {w : World} {p : WPara} (h : wvalid w p = true) :
    ∀ l ∈ wparaLits p, evalLit l w = true := by
  simp only [wvalid, Bool.and_eq_true] at h
  obtain ⟨⟨_, hop⟩, hst⟩ := h
  intro l hl
  rcases List.mem_cons.mp hl with rfl | hl
  · exact hop
  · obtain ⟨s, hs, rfl⟩ := List.mem_map.mp hl
    have key : ∀ (steps : List Step) (ctx : Ctx), wvalidFrom w ctx steps = true →
        ∀ s' ∈ steps, evalLit s'.lit w = true := by
      intro steps
      induction steps with
      | nil => intro _ _ _ hmem; cases hmem
      | cons a rest ih =>
          intro ctx hv s' hs'
          simp only [wvalidFrom, Bool.and_eq_true] at hv
          rcases List.mem_cons.mp hs' with rfl | hs'
          · exact hv.1.1
          · exact ih (a.lit :: ctx) hv.2 s' hs'
    exact key p.steps [p.opening] hst s hs

/-- **No repetition**, exactly as in the one-topic case. -/
theorem wpara_no_repetition {w : World} {p : WPara} (h : wvalid w p = true) :
    (wparaLits p).Nodup := by
  simp only [wvalid, Bool.and_eq_true] at h
  obtain ⟨_, hst⟩ := h
  have key : ∀ (steps : List Step) (ctx : Ctx), wvalidFrom w ctx steps = true →
      (steps.map (·.lit)).Nodup ∧ ∀ l ∈ ctx, l ∉ steps.map (·.lit) := by
    intro steps
    induction steps with
    | nil => intro ctx _; exact ⟨List.nodup_nil, by simp⟩
    | cons s rest ih =>
        intro ctx hv
        simp only [wvalidFrom, Bool.and_eq_true] at hv
        obtain ⟨⟨_, hOK⟩, hrest⟩ := hv
        obtain ⟨hnd, hfresh⟩ := ih (s.lit :: ctx) hrest
        have hnew : s.lit ∉ rest.map (·.lit) := hfresh s.lit (by simp)
        refine ⟨by rw [List.map_cons]; exact List.nodup_cons.mpr ⟨hnew, hnd⟩, ?_⟩
        intro l hl
        simp only [wstepOK, stepOK, Bool.and_eq_true, Bool.not_eq_true',
          List.any_eq_false] at hOK
        have hne : l ≠ s.lit := by
          intro hEq
          have := hOK.1.2 l hl
          simp [hEq] at this
        simp only [List.map_cons, List.mem_cons, not_or]
        exact ⟨hne, hfresh l (by simp [hl])⟩
  obtain ⟨hnd, hfresh⟩ := key p.steps [p.opening] hst
  exact List.nodup_cons.mpr ⟨hfresh p.opening (by simp), hnd⟩

/-! ## 3. Growing one -/

/-- Everything true and contingent in `w`, about anything. -/
def wcandidates (w : World) : List Lit := usefulLits.filter fun l => evalLit l w

/-- The licensing test computed from the live worlds, for a clause about its own
subject. -/
def wokLive (live : List World) (ctx : Ctx) (c : Conn) (l : Lit) : Bool :=
  okLive live ctx (subj l.1) c l

/-- Prefer a contrast, then an addition, then a conclusion. -/
def wpick (cs : List Lit) (live : List World) (ctx : Ctx) : Option Step :=
  match cs.find? (wokLive live ctx .but) with
  | some l => some ⟨.but, l⟩
  | none =>
    match cs.find? (wokLive live ctx .and) with
    | some l => some ⟨.and, l⟩
    | none =>
      match cs.find? (wokLive live ctx .so) with
      | some l => some ⟨.so, l⟩
      | none => none

def wgrow (cs : List Lit) : Nat → List World → Ctx → List Step
  | 0, _, _ => []
  | n + 1, live, ctx =>
      match wpick cs live ctx with
      | none => []
      | some s => s :: wgrow cs n (liveWith live s.lit) (s.lit :: ctx)

/-- **The paragraph the system offers about a whole world.** -/
def wdescribe (w : World) : Option WPara :=
  let cs := wcandidates w
  match cs.head? with
  | none => none
  | some l => some ⟨l, wgrow cs 6 (liveWith allWorlds l) [l]⟩

/-! ## 4. English, with pronouns only where they are safe -/

/-- A clause, using "it" only when the subject is the same as the previous
clause's. -/
def sayStep (prev : Ent) (l : Lit) : String :=
  if subj l.1 = prev then sayIt l else sayFull l

/-- Render a paragraph, tracking the previous subject. -/
def renderW : Ent → List Step → String
  | _, [] => "."
  | prev, s :: rest =>
      connWord s.conn ++ sayStep prev s.lit ++ renderW (subj s.lit.1) rest

def renderWPara (p : WPara) : String :=
  sayFull p.opening ++ renderW (subj p.opening.1) p.steps

/-! ## 5. Measured over every world -/

/-- One paragraph per world. -/
def wcorpus : List (World × WPara) :=
  allWorlds.filterMap fun w => (wdescribe w).map fun p => (w, p)

/-- The clauses that change the subject, with the subject before them. -/
def subjectChanges (p : WPara) : List Step :=
  ((p.steps.zip (p.opening :: p.steps.map (·.lit))).filter fun sl =>
    decide (subj sl.1.lit.1 ≠ subj sl.2.1)).map (·.1)

/-- **The generator over every world.**  512 paragraphs, all valid; 3072 joined
clauses, of which 2524 change the subject and 330 are `so` clauses whose subject
differs from the clause before — cross-subject deductions, which the one-topic
system could not state at all. -/
theorem wcorpus_facts :
    wcorpus.length = 512 ∧
    (wcorpus.all fun wp => wvalid wp.1 wp.2) = true ∧
    (wcorpus.flatMap fun wp => wp.2.steps).length = 3072 ∧
    (wcorpus.flatMap fun wp => subjectChanges wp.2).length = 2524 ∧
    (wcorpus.flatMap fun wp =>
      (subjectChanges wp.2).filter fun s => decide (s.conn = Conn.so)).length = 330 := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> native_decide

/-- Everything in every one of those paragraphs is true. -/
theorem wcorpus_sound : ∀ wp ∈ wcorpus, ∀ l ∈ wparaLits wp.2, evalLit l wp.1 = true := by
  intro wp hwp l hl
  exact wpara_sound (List.all_eq_true.mp wcorpus_facts.2.1 wp hwp) l hl

/-- The paragraph about the demo world. -/
def wdemo : String :=
  match wdescribe demoWorld with
  | some p => renderWPara p
  | none => "nothing to say"

#eval wdemo

end WideDiscourse
