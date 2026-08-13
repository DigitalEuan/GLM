import Mathlib
import RequestProject.Semantics
import RequestProject.Chat

/-!
# Discourse: sentences that connect, and paragraphs that grow

`Semantics.lean` gave single sentences whose truth is measurement, and
`Chat.lean` answered single questions.  Both stop at one sentence.  Real
language *connects*: the second sentence has to earn its place after the first,
and the words that do that work — `and`, `but`, `so` — are exactly the ones the
system did not have.

This file adds them, with truth conditions that are decided by counting worlds,
so nothing here is stipulated either.

## The context, and what a connective means

At any point in a paragraph the system has said a list of literals `ctx`.  The
worlds still compatible with everything said so far are `ctxWorlds ctx` — the
*live* worlds.  A next literal `q` is judged against them:

* **`so q`** — `q` holds in *every* live world.  It is a deduction: the
  paragraph has already committed to it (`so_is_a_deduction`).
* **`and q`** — `q` does not hold in every live world (so it is news), and it
  holds in *at least half* of them: an unsurprising addition
  (`and_is_informative`).
* **`but q`** — `q` is news, and it holds in *fewer than half* of the live
  worlds: the hearer would not have expected it (`but_is_contrastive`).

That is a defeasible, counting notion of expectation — the first thing in this
project that is not strict logic — and it is still completely deterministic:
the same context and the same world always give the same connective.

## What is proved about a paragraph

* `para_sound` — every clause of it is true in the world being described.
* `para_no_repetition` — it never says the same thing twice.
* `para_information_increases` — each `and`/`but` clause strictly cuts down the
  live worlds, so the paragraph really is going somewhere.
* `para_topic_continuity` — every clause is about the same thing, which is what
  makes the pronoun "it" in the rendered English unambiguous.
* `so_is_a_deduction`, `and_is_informative`, `but_is_contrastive` — each
  connective means what it says.

## The generator

`describe w e` builds a paragraph about `e` in `w` by greedily preferring a
contrast, then an addition, then a conclusion.  It is checked
**for every one of the 512 worlds and all three things**
(`describe_always_valid`, `describe_always_speaks`, `describe_min_length`), not
on a chosen example.
-/

namespace Discourse

open Semantics

set_option maxRecDepth 100000

/-! ## 1. Live worlds -/

/-- The literals said so far. -/
abbrev Ctx := List Lit

/-- The worlds still compatible with everything said so far. -/
def ctxWorlds (ctx : Ctx) : List World :=
  allWorlds.filter fun w => ctx.all fun l => evalLit l w

/-- How many worlds are still live. -/
def ctxCount (ctx : Ctx) : Nat := (ctxWorlds ctx).length

/-- `q` holds in every live world. -/
def ctxEntails (ctx : Ctx) (q : Lit) : Bool := (ctxWorlds ctx).all fun w => evalLit q w

theorem mem_ctxWorlds (ctx : Ctx) (w : World) :
    w ∈ ctxWorlds ctx ↔ ctx.all (fun l => evalLit l w) = true := by
  simp [ctxWorlds, List.mem_filter, mem_allWorlds w]

theorem ctxEntails_iff (ctx : Ctx) (q : Lit) :
    ctxEntails ctx q = true ↔
      ∀ w : World, (∀ l ∈ ctx, evalLit l w = true) → evalLit q w = true := by
  constructor
  · intro h w hw
    refine (List.all_eq_true.mp h) w ?_
    exact (mem_ctxWorlds ctx w).mpr (List.all_eq_true.mpr fun l hl => hw l hl)
  · intro h
    refine List.all_eq_true.mpr fun w hw => h w ?_
    have := (mem_ctxWorlds ctx w).mp hw
    exact fun l hl => List.all_eq_true.mp this l hl

/-- The live worlds in which `q` also holds. -/
def ctxCountWith (ctx : Ctx) (q : Lit) : Nat := ctxCount (q :: ctx)

/-- `q` is *surprising* in this context: it holds in fewer than half of the live
worlds.  This is the only defeasible notion in the project, and it is still a
count, not an opinion. -/
def surprising (ctx : Ctx) (q : Lit) : Bool :=
  decide (2 * ctxCountWith ctx q < ctxCount ctx)

/-! ## 2. Connectives and paragraphs -/

/-- The three words that join clauses. -/
inductive Conn
  | and | but | so
deriving DecidableEq, Repr

/-- One further clause of a paragraph. -/
structure Step where
  conn : Conn
  lit : Lit
deriving DecidableEq, Repr

/-- What a clause is about. -/
def subj : Atom → Ent
  | .frozen e => e
  | .boiling e => e
  | .warm e => e
  | .heavy e => e
  | .hotter e _ => e
  | .heavier e _ => e

/-- **When a connective is licensed.**  In every case the clause must be about
the topic, be contingent, and not have been said already; then `so` demands
entailment, `and` demands news that is unsurprising, `but` demands news that is
surprising. -/
def stepOK (ctx : Ctx) (topic : Ent) (s : Step) : Bool :=
  decide (subj s.lit.1 = topic) && contingent s.lit &&
    !ctx.any (fun l => decide (l = s.lit)) &&
    (match s.conn with
      | .so => ctxEntails ctx s.lit
      | .and => !ctxEntails ctx s.lit && !surprising ctx s.lit
      | .but => !ctxEntails ctx s.lit && surprising ctx s.lit)

/-- A paragraph: an opening clause about a topic, then further clauses. -/
structure Para where
  topic : Ent
  opening : Lit
  steps : List Step
deriving Repr

/-- Each step paired with the context it was uttered in. -/
def annot (ctx : Ctx) : List Step → List (Ctx × Step)
  | [] => []
  | s :: rest => (ctx, s) :: annot (s.lit :: ctx) rest

/-- A continuation is valid in `w` when each clause is true there and its
connective is licensed by what came before. -/
def validFrom (w : World) (topic : Ent) (ctx : Ctx) : List Step → Bool
  | [] => true
  | s :: rest => evalLit s.lit w && stepOK ctx topic s && validFrom w topic (s.lit :: ctx) rest

/-- A whole paragraph is valid in `w`. -/
def validPara (w : World) (p : Para) : Bool :=
  decide (subj p.opening.1 = p.topic) && contingent p.opening && evalLit p.opening w &&
    validFrom w p.topic [p.opening] p.steps

/-- The literals of a paragraph, opening first. -/
def paraLits (p : Para) : List Lit := p.opening :: p.steps.map (·.lit)

/-! ## 3. What a valid paragraph guarantees -/

theorem validFrom_iff (w : World) (topic : Ent) (ctx : Ctx) (steps : List Step) :
    validFrom w topic ctx steps = true ↔
      ∀ cs ∈ annot ctx steps, evalLit cs.2.lit w = true ∧ stepOK cs.1 topic cs.2 = true := by
  induction steps generalizing ctx with
  | nil => simp [validFrom, annot]
  | cons s rest ih =>
      simp only [validFrom, annot, Bool.and_eq_true, List.mem_cons, ih]
      constructor
      · rintro ⟨⟨h1, h2⟩, h3⟩ cs hcs
        rcases hcs with rfl | hcs
        · exact ⟨h1, h2⟩
        · exact h3 cs hcs
      · intro h
        exact ⟨⟨(h _ (Or.inl rfl)).1, (h _ (Or.inl rfl)).2⟩, fun cs hcs => h cs (Or.inr hcs)⟩

/-- **Soundness.**  Every clause of a valid paragraph is true in the world it
describes. -/
theorem para_sound {w : World} {p : Para} (h : validPara w p = true) :
    ∀ l ∈ paraLits p, evalLit l w = true := by
  simp only [validPara, Bool.and_eq_true] at h
  obtain ⟨⟨⟨_, _⟩, hop⟩, hst⟩ := h
  intro l hl
  rcases List.mem_cons.mp hl with rfl | hl
  · exact hop
  · obtain ⟨s, hs, rfl⟩ := List.mem_map.mp hl
    have hann : ∀ s' ∈ p.steps, ∃ c, (c, s') ∈ annot [p.opening] p.steps := by
      clear hs hst
      generalize [p.opening] = ctx
      induction p.steps generalizing ctx with
      | nil => intro _ h; cases h
      | cons a rest ih =>
          intro s' hs'
          rcases List.mem_cons.mp hs' with rfl | hs'
          · exact ⟨ctx, by simp [annot]⟩
          · obtain ⟨c, hc⟩ := ih (ctx := a.lit :: ctx) s' hs'
            exact ⟨c, by simp [annot, hc]⟩
    obtain ⟨c, hc⟩ := hann s hs
    exact ((validFrom_iff w p.topic _ _).mp hst (c, s) hc).1

/-- Every step of a valid paragraph is licensed in the context it was said in. -/
theorem para_steps_licensed {w : World} {p : Para} (h : validPara w p = true)
    {c : Ctx} {s : Step} (hc : (c, s) ∈ annot [p.opening] p.steps) :
    stepOK c p.topic s = true := by
  simp only [validPara, Bool.and_eq_true] at h
  exact ((validFrom_iff w p.topic _ _).mp h.2 (c, s) hc).2

/-- **`so` is a deduction.**  When the paragraph says "so `q`", every world
compatible with what it has already said satisfies `q`. -/
theorem so_is_a_deduction {c : Ctx} {s : Step} {topic : Ent}
    (hOK : stepOK c topic s = true) (hso : s.conn = Conn.so) :
    ∀ w : World, (∀ l ∈ c, evalLit l w = true) → evalLit s.lit w = true := by
  simp only [stepOK, hso, Bool.and_eq_true] at hOK
  exact (ctxEntails_iff c s.lit).mp hOK.2

/-- **`and` is news.**  When the paragraph says "and `q`", some world compatible
with what it has already said fails `q`, so the clause rules something out — and
`q` still holds in at least half of those worlds, so it is not a contrast. -/
theorem and_is_informative {c : Ctx} {s : Step} {topic : Ent}
    (hOK : stepOK c topic s = true) (hand : s.conn = Conn.and) :
    (∃ w : World, (∀ l ∈ c, evalLit l w = true) ∧ evalLit s.lit w = false) ∧
      ctxCount c ≤ 2 * ctxCountWith c s.lit := by
  simp only [stepOK, hand, Bool.and_eq_true, Bool.not_eq_true'] at hOK
  obtain ⟨_, hent, hsur⟩ := hOK
  constructor
  · by_contra hcon
    push_neg at hcon
    have : ctxEntails c s.lit = true := by
      refine (ctxEntails_iff c s.lit).mpr fun w hw => ?_
      have := hcon w hw
      cases hv : evalLit s.lit w
      · exact absurd hv this
      · rfl
    rw [this] at hent; exact Bool.noConfusion hent
  · simp only [surprising, decide_eq_false_iff_not, Nat.not_lt] at hsur
    exact hsur

/-- **`but` is a contrast.**  When the paragraph says "but `q`", strictly fewer
than half of the worlds still compatible with what it has said satisfy `q`: the
hearer would not have expected it.  And it is still news. -/
theorem but_is_contrastive {c : Ctx} {s : Step} {topic : Ent}
    (hOK : stepOK c topic s = true) (hbut : s.conn = Conn.but) :
    2 * ctxCountWith c s.lit < ctxCount c ∧ ctxEntails c s.lit = false := by
  simp only [stepOK, hbut, Bool.and_eq_true, Bool.not_eq_true'] at hOK
  obtain ⟨_, hent, hsur⟩ := hOK
  exact ⟨by simpa [surprising] using hsur, hent⟩

/-- **The paragraph never repeats itself.** -/
theorem para_no_repetition {w : World} {p : Para} (h : validPara w p = true) :
    (paraLits p).Nodup := by
  simp only [validPara, Bool.and_eq_true] at h
  obtain ⟨_, hst⟩ := h
  -- general statement: a valid continuation from `ctx` never repeats, and never
  -- repeats anything already in `ctx`.
  have key : ∀ (steps : List Step) (ctx : Ctx), validFrom w p.topic ctx steps = true →
      (steps.map (·.lit)).Nodup ∧ ∀ l ∈ ctx, l ∉ steps.map (·.lit) := by
    intro steps
    induction steps with
    | nil => intro ctx _; exact ⟨List.nodup_nil, by simp⟩
    | cons s rest ih =>
        intro ctx hv
        simp only [validFrom, Bool.and_eq_true] at hv
        obtain ⟨⟨_, hOK⟩, hrest⟩ := hv
        obtain ⟨hnd, hfresh⟩ := ih (s.lit :: ctx) hrest
        have hnew : s.lit ∉ rest.map (·.lit) := hfresh s.lit (by simp)
        refine ⟨by rw [List.map_cons]; exact List.nodup_cons.mpr ⟨hnew, hnd⟩, ?_⟩
        intro l hl
        simp only [stepOK, Bool.and_eq_true, Bool.not_eq_true', List.any_eq_false] at hOK
        have hne : l ≠ s.lit := by
          intro hEq
          have := hOK.1.2 l hl
          simp [hEq] at this
        simp only [List.map_cons, List.mem_cons, not_or]
        exact ⟨hne, hfresh l (by simp [hl])⟩
  obtain ⟨hnd, hfresh⟩ := key p.steps [p.opening] hst
  exact List.nodup_cons.mpr ⟨hfresh p.opening (by simp), hnd⟩

/-- **Every clause is about the same thing.**  This is what makes the pronoun
"it" in the English rendering unambiguous. -/
theorem para_topic_continuity {w : World} {p : Para} (h : validPara w p = true) :
    ∀ l ∈ paraLits p, subj l.1 = p.topic := by
  have hop : subj p.opening.1 = p.topic := by
    simp only [validPara, Bool.and_eq_true, decide_eq_true_eq] at h; tauto
  intro l hl
  rcases List.mem_cons.mp hl with rfl | hl
  · exact hop
  · obtain ⟨s, hs, rfl⟩ := List.mem_map.mp hl
    simp only [validPara, Bool.and_eq_true] at h
    have key : ∀ (steps : List Step) (ctx : Ctx), validFrom w p.topic ctx steps = true →
        ∀ s' ∈ steps, subj s'.lit.1 = p.topic := by
      intro steps
      induction steps with
      | nil => intro _ _ _ hmem; cases hmem
      | cons a rest ih =>
          intro ctx hv s' hs'
          simp only [validFrom, Bool.and_eq_true] at hv
          rcases List.mem_cons.mp hs' with rfl | hs'
          · simp only [stepOK, Bool.and_eq_true, decide_eq_true_eq] at hv
            tauto
          · exact ih (a.lit :: ctx) hv.2 s' hs'
    exact key p.steps [p.opening] h.2 s hs

/-- **The paragraph gets somewhere.**  Each `and` or `but` clause strictly
reduces the number of worlds still compatible with what has been said. -/
theorem para_information_increases {c : Ctx} {s : Step} {topic : Ent}
    (hOK : stepOK c topic s = true) (hne : s.conn ≠ Conn.so) :
    ctxCount (s.lit :: c) < ctxCount c := by
  have hent : ctxEntails c s.lit = false := by
    cases hc : s.conn with
    | so => exact absurd hc hne
    | and => simp only [stepOK, hc, Bool.and_eq_true, Bool.not_eq_true'] at hOK; tauto
    | but => simp only [stepOK, hc, Bool.and_eq_true, Bool.not_eq_true'] at hOK; tauto
  -- the live worlds after are a strict sublist-filter of the live worlds before
  have hsub : ctxWorlds (s.lit :: c) = (ctxWorlds c).filter (fun w => evalLit s.lit w) := by
    simp [ctxWorlds, List.filter_filter]
  have hle : ctxCount (s.lit :: c) ≤ ctxCount c := by
    rw [ctxCount, ctxCount, hsub]
    exact List.filter_sublist.length_le
  rcases Nat.lt_or_ge (ctxCount (s.lit :: c)) (ctxCount c) with h | h
  · exact h
  · exfalso
    have heq : ctxCount (s.lit :: c) = ctxCount c := Nat.le_antisymm hle h
    have hall : ∀ w ∈ ctxWorlds c, evalLit s.lit w = true := by
      intro w hw
      have hfil : ((ctxWorlds c).filter (fun w => evalLit s.lit w)).length =
          (ctxWorlds c).length := by
        rw [← hsub]; exact heq
      have := List.filter_eq_self.mp (List.Sublist.eq_of_length List.filter_sublist hfil)
      exact this w hw
    have : ctxEntails c s.lit = true := List.all_eq_true.mpr hall
    rw [this] at hent; exact Bool.noConfusion hent

/-! ## 4. English, with pronouns -/

/-- A literal with the subject spelled out. -/
def sayFull (l : Lit) : String := Chat.renderLit l

/-- A literal with the subject replaced by "it" — legitimate exactly because
`para_topic_continuity` says every clause of a paragraph has the same subject. -/
def sayIt (l : Lit) : String :=
  let neg := if l.2 then " is " else " is not "
  match l.1 with
  | .frozen _ => "it" ++ neg ++ "frozen"
  | .boiling _ => "it" ++ neg ++ "boiling"
  | .warm _ => "it" ++ neg ++ "warm"
  | .heavy _ => "it" ++ neg ++ "heavy"
  | .hotter _ f => "it" ++ neg ++ "hotter than " ++ Chat.renderEnt f
  | .heavier _ f => "it" ++ neg ++ "heavier than " ++ Chat.renderEnt f

def connWord : Conn → String
  | .and => ", and "
  | .but => ", but "
  | .so => ", so "

/-- The paragraph in English: the topic named once, then pronouns. -/
def renderPara (p : Para) : String :=
  sayFull p.opening ++
    String.join (p.steps.map fun s => connWord s.conn ++ sayIt s.lit) ++ "."


/-! ## 5. Growing a paragraph

The truth conditions above are written in terms of the context, which is the
honest way to state them, but recomputing the live worlds for every candidate
would be wasteful.  The generator therefore carries the live-world list along
and re-derives the same conditions from it; the paragraphs it produces are then
checked against the *context* definitions (`corpus_facts`), so the shortcut is
verified rather than trusted. -/

/-- The true, contingent things one can say about `e` in `w`. -/
def candidates (w : World) (e : Ent) : List Lit :=
  usefulLits.filter fun l => decide (subj l.1 = e) && evalLit l w

/-- How many of the live worlds satisfy `q`. -/
def liveWith (live : List World) (q : Lit) : List World := live.filter fun w => evalLit q w

/-- The licensing test, computed from the live worlds. -/
def okLive (live : List World) (ctx : Ctx) (topic : Ent) (c : Conn) (l : Lit) : Bool :=
  decide (subj l.1 = topic) && !ctx.any (fun x => decide (x = l)) &&
    (let n := (liveWith live l).length
     let m := live.length
     match c with
     | .so => decide (n = m)
     | .and => decide (n < m) && decide (m ≤ 2 * n)
     | .but => decide (2 * n < m))

/-- The next clause: prefer a contrast, then an addition, then a conclusion. -/
def pick (cs : List Lit) (live : List World) (ctx : Ctx) (topic : Ent) : Option Step :=
  match cs.find? (okLive live ctx topic .but) with
  | some l => some ⟨.but, l⟩
  | none =>
    match cs.find? (okLive live ctx topic .and) with
    | some l => some ⟨.and, l⟩
    | none =>
      match cs.find? (okLive live ctx topic .so) with
      | some l => some ⟨.so, l⟩
      | none => none

/-- Keep adding clauses while the fuel lasts and there is something to add. -/
def grow (cs : List Lit) (topic : Ent) : Nat → List World → Ctx → List Step
  | 0, _, _ => []
  | n + 1, live, ctx =>
      match pick cs live ctx topic with
      | none => []
      | some s => s :: grow cs topic n (liveWith live s.lit) (s.lit :: ctx)

/-- **The paragraph the system offers about `e` in `w`.** -/
def describe (w : World) (e : Ent) : Option Para :=
  let cs := candidates w e
  match cs.head? with
  | none => none
  | some l => some ⟨e, l, grow cs e 6 (liveWith allWorlds l) [l]⟩

/-- Every paragraph the generator produces, over every world and every thing. -/
def corpus : List (World × Para) :=
  allWorlds.flatMap fun w => ents.filterMap fun e => (describe w e).map fun p => (w, p)

/-- The connectives used in the whole corpus. -/
def corpusConns : List Conn := corpus.flatMap fun wp => wp.2.steps.map (·.conn)

/-- **The generator, measured over the whole world set.**  It produces a
paragraph for every one of the 512 worlds and each of the three things — 1536
paragraphs — and *every one of them is a valid paragraph* in the sense above:
sound, non-repeating, on topic, and with each connective licensed.  Of the 9216
clauses it joins, 4824 are `and`, 1512 are `but` and 2880 are `so`.

Every paragraph ends at exactly seven clauses, which is the fuel running out
rather than the system running out of things to say — an honest limit of the
generator, not of the semantics. -/
theorem corpus_facts :
    corpus.length = 1536 ∧
    (corpus.all fun wp => validPara wp.1 wp.2) = true ∧
    corpusConns.length = 9216 ∧
    (corpusConns.filter fun c => decide (c = Conn.and)).length = 4824 ∧
    (corpusConns.filter fun c => decide (c = Conn.but)).length = 1512 ∧
    (corpusConns.filter fun c => decide (c = Conn.so)).length = 2880 ∧
    (corpus.all fun wp => decide ((paraLits wp.2).length = 7)) = true := by
  native_decide

/-- **Everything in every paragraph is true**, in the world that paragraph
describes.  This is `para_sound` applied to the whole generated corpus. -/
theorem corpus_sound : ∀ wp ∈ corpus, ∀ l ∈ paraLits wp.2, evalLit l wp.1 = true := by
  intro wp hwp l hl
  exact para_sound (List.all_eq_true.mp corpus_facts.2.1 wp hwp) l hl

/-- The paragraphs about the demo world. -/
def demoParas : List String :=
  ents.filterMap fun e => (describe demoWorld e).map renderPara

#eval demoParas

end Discourse
