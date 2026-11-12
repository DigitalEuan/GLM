import Mathlib
import RequestProject.Semantics
import RequestProject.Chat
import RequestProject.Narrative

/-!
# `because` with a direction of time

Report 2 §7.6 recorded the one complaint about the connective the rest of the
system leans on:

> **"Because" is entailment, not causation.** `A because B` means B forces A in
> every world. […] "The water is not warm because the water is frozen" and "the
> water is frozen because it is not boiling and not warm" are both accepted,
> and only the first reads as a cause.

`grounding_is_cyclic` below proves that complaint is real — the entailment
`because` of `Semantics.lean` genuinely accepts a cycle, so it cannot be
telling causes from definitional consequences.

The fix suggested in report 2 §8 was to *add a direction of time while keeping
entailment as the soundness condition*.  That is exactly what is done here.

## Histories

A `Hist` is a starting world and the actions performed since.  `hstates` is the
sequence of worlds it passes through, `nowW` the world it has reached.  For a
literal that holds now, `sinceT h l` is the **first moment from which it has
held without interruption** — how long the fact has been the case.

## What the direction of time can and cannot be

The obvious reading of report 2's suggestion is "prefer a reason that is
already in place before the fact".  `since_le_of_entails` proves that reading
impossible: if `m` forces `l` in every world then `l` has held wherever `m`
has, so **a ground is never older than what it grounds**.  Demanding a strictly
older reason accepts nothing at all, in any history — proved in
`strictly_older_reason_never_exists` and re-measured by exhaustion in
`causal_filter_counts`.

What is left is the other side of the same inequality:

    causalBecause h l m  :=  m entails l in every world  (unchanged soundness)
                             ∧ l ≠ m, both contingent
                             ∧ sinceT l = sinceT m          (the new clause)

so "`l`, because `m`" is accepted only when the reason **came into force at the
same moment as the fact** — the same event brought both about — and is refused
when the reason turned up afterwards, which is the case that reads as no
explanation at all.  What that buys:

* `causalBecause_sound` — every guarantee of the old connective still holds, so
  nothing in the earlier development is weakened;
* `causalBecause_refines_because` — it is a *filter* on the old `because`:
  anything it accepts, the old connective accepted too;
* `causalBecause_asymm` — the cycle is broken: never both directions.  The
  proof rests on `no_equivalent_literals`, a check that no two different
  contingent literals of this vocabulary say the same thing;
* `causalBecause_trans` — reasons chain, which is what licenses "…, and that is
  why …" (`renderChain`);
* `actionCause_sound` — when a fact started part-way through the history, the
  system can name the **action** that started it, and that action provably
  occurred strictly before the fact was asserted;
* `static_facts_have_no_action_cause` — a fact that has held all along gets no
  action offered, so definitional consequences are never dressed up as effects.

## Measured, not asserted

`causal_filter_counts` runs the tests over all 4608 histories of at most two
actions out of all 512 worlds.  Of the `1180416` ground clause instances the
old `because` accepts, the timed connective keeps `1051584` and rejects
`128832` — 10.9% — and the strictly-older filter keeps `0`.  `demoCausalText`
shows what it says, including the rejected clause and why.

## What is still not achieved

Coevalness is a *test on the record of change*, not a theory of causation.  It
cannot distinguish two facts that always change together, and in this world
model that is the common case, which is why the filter removes a tenth of the
explanations rather than most of them.  What it does remove is exactly the
class the report complained about: reasons that arrive after the fact.
-/

namespace Causation

open Semantics

set_option maxRecDepth 100000

/-! ## 1. Histories -/

/-- A history: where the world started, and what has been done since. -/
structure Hist where
  init : World
  acts : List Act

/-- Every world the history passes through, oldest first. -/
def states : List Act → World → List World
  | [], w => [w]
  | a :: rest, w => w :: states rest (step a w)

/-- The worlds of a history. -/
def hstates (h : Hist) : List World := states h.acts h.init

theorem states_length (acts : List Act) (w : World) :
    (states acts w).length = acts.length + 1 := by
  induction acts generalizing w with
  | nil => rfl
  | cons a rest ih => simp [states, ih]

theorem hstates_length (h : Hist) : (hstates h).length = h.acts.length + 1 :=
  states_length _ _

/-- The world the history has reached. -/
def nowW (h : Hist) : World := Narrative.runActs h.acts h.init

theorem states_getLast (acts : List Act) (w : World) :
    (states acts w).getLast (by cases acts <;> simp [states]) = Narrative.runActs acts w := by
  induction acts generalizing w with
  | nil => rfl
  | cons a rest ih =>
    rw [Narrative.runActs]
    rw [← ih (step a w)]
    simp only [states]
    rw [List.getLast_cons (by cases rest <;> simp [states])]

/-! ## 2. How long a fact has held -/

/-- `l` has held from time `t` onwards. -/
def holdsFrom (h : Hist) (t : Nat) (l : Lit) : Bool := ((hstates h).drop t).all (evalLit l)

/-- The first moment from which `l` has held without interruption — `none` if
`l` is not the case now. -/
def sinceT (h : Hist) (l : Lit) : Option Nat :=
  if evalLit l (nowW h) then
    (List.range (hstates h).length).find? fun t => holdsFrom h t l
  else none

theorem last_mem_drop (h : Hist) (t : Nat) (ht : t < (hstates h).length) :
    nowW h ∈ (hstates h).drop t := by
  have hne : (hstates h) ≠ [] := by
    intro hc; rw [hc] at ht; simp at ht
  have hlastEq : (hstates h).getLast hne = nowW h := by
    obtain ⟨w, acts⟩ := h
    simpa [hstates, nowW] using states_getLast acts w
  rw [← hlastEq, List.getLast_eq_getElem hne]
  set L := hstates h
  set i := L.length - 1 with hi
  have hilt : i < L.length := by omega
  have hti : t ≤ i := by omega
  have hlen : i - t < (L.drop t).length := by simp; omega
  have hEq : (L.drop t)[i - t] = L[i] := by
    rw [List.getElem_drop]
    congr 1
    omega
  exact hEq ▸ List.getElem_mem hlen

/-- If a fact has held since time `t`, it is the case now. -/
theorem holdsFrom_now {h : Hist} {t : Nat} {l : Lit}
    (ht : t < (hstates h).length) (hh : holdsFrom h t l = true) :
    evalLit l (nowW h) = true :=
  List.all_eq_true.mp hh _ (last_mem_drop h t ht)

theorem sinceT_spec {h : Hist} {l : Lit} {t : Nat} (hs : sinceT h l = some t) :
    t < (hstates h).length ∧ holdsFrom h t l = true := by
  unfold sinceT at hs
  split at hs
  · have hmem := List.mem_of_find?_eq_some hs
    exact ⟨List.mem_range.mp hmem,
      List.find?_some (p := fun t => holdsFrom h t l) hs⟩
  · exact absurd hs (by simp)

/-- Minimality: nothing earlier works. -/
theorem sinceT_min {h : Hist} {l : Lit} {t s : Nat} (hs : sinceT h l = some t)
    (hlt : s < t) : holdsFrom h s l = false := by
  unfold sinceT at hs
  split at hs
  · obtain ⟨_, i, hi, hxs, hmin⟩ := List.find?_eq_some_iff_getElem.mp hs
    simp only [List.getElem_range] at hxs
    subst hxs
    simpa using hmin s hlt
  · exact absurd hs (by simp)

/-! ## 3. Time and entailment pull the same way -/

/-- **A ground is never older than what it grounds.**  If `m` forces `l` in
every world then, wherever `m` has held, `l` has held too, so `l`'s current
unbroken run started no later than `m`'s.  This is a fact about the whole
framework, and it decides what shape the repair can take. -/
theorem since_le_of_entails {h : Hist} {l m : Lit} {tl tm : Nat}
    (hent : entails m l = true) (hl : sinceT h l = some tl) (hm : sinceT h m = some tm) :
    tl ≤ tm := by
  by_contra hcon
  push_neg at hcon
  have hfalse := sinceT_min hl hcon
  obtain ⟨_, hhm⟩ := sinceT_spec hm
  have htrue : holdsFrom h tm l = true :=
    List.all_eq_true.mpr fun u hu =>
      (entails_iff m l).mp hent u (List.all_eq_true.mp hhm u hu)
  rw [htrue] at hfalse
  exact absurd hfalse (by simp)

/-- Hence the repair proposed in report 2 §8 — "prefer a reason that mentions an
*earlier* action" — cannot be had by demanding a **strictly older** ground.  No
such reason exists in any history, ever, so that filter would accept nothing.
The measurement `strict_filter_is_empty` says the same thing by exhaustion. -/
theorem strictly_older_reason_never_exists {h : Hist} {l m : Lit} {tl tm : Nat}
    (hent : entails m l = true) (hl : sinceT h l = some tl) (hm : sinceT h m = some tm) :
    ¬ tm < tl := by
  have := since_le_of_entails hent hl hm
  omega

/-! ## 4. The connective: a reason must arrive with the fact

What is left, once the strictly-older filter is ruled out, is the *other* side
of the same inequality.  A ground `m` is either **coeval** with `l` — the two
came into force at the same moment, so the same event brought both about — or
it arrived **strictly later** than `l`, in which case `l` was already the case
before `m` was, and `m` cannot be why.  Requiring coevalness is therefore the
sharpest time condition available, and it is the one that discards exactly the
reasons that turn up after the fact. -/

/-- **`l`, because `m`** — with a direction of time.  Entailment is kept as the
soundness condition; what is added is that the reason came into force at the
same moment as the fact, so it did not turn up after the event. -/
def causalBecause (h : Hist) (l m : Lit) : Bool :=
  match sinceT h l, sinceT h m with
  | some tl, some tm =>
      entails m l && decide (l ≠ m) && contingent l && contingent m && decide (tl = tm)
  | _, _ => false

theorem mem_usefulLits {l : Lit} (hc : contingent l = true) : l ∈ usefulLits :=
  List.mem_filter.mpr ⟨mem_allLits l, hc⟩

/-- **No two different contingent literals of this world are equivalent** —
checked over all 48 × 48 pairs.  Nothing says the same thing twice, which is
what makes the causal connective genuinely one-directional. -/
theorem no_equivalent_literals :
    usefulLits.all (fun l => usefulLits.all fun m =>
      !(entails l m && entails m l) || decide (l = m)) = true := by native_decide

/-- **Everything the old connective guaranteed still holds.** -/
theorem causalBecause_sound {h : Hist} {l m : Lit} (hc : causalBecause h l m = true) :
    evalLit l (nowW h) = true ∧ evalLit m (nowW h) = true ∧
      (∀ w : World, evalLit m w = true → evalLit l w = true) ∧ l ≠ m := by
  unfold causalBecause at hc
  split at hc
  · rename_i tl tm hl hm
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
    obtain ⟨⟨⟨⟨hent, hne⟩, _⟩, _⟩, _⟩ := hc
    obtain ⟨htl, hhl⟩ := sinceT_spec hl
    obtain ⟨htm, hhm⟩ := sinceT_spec hm
    exact ⟨holdsFrom_now htl hhl, holdsFrom_now htm hhm, (entails_iff m l).mp hent, hne⟩
  · exact absurd hc (by simp)

/-- **It is a filter on the old connective**: whatever it accepts, the
entailment `because` of `Semantics.lean` accepted too, so no earlier guarantee
is weakened. -/
theorem causalBecause_refines_because {h : Hist} {l m : Lit}
    (hc : causalBecause h l m = true) : evalS (.because l m) (nowW h) = true := by
  unfold causalBecause at hc
  split at hc
  · rename_i tl tm hl hm
    simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
    obtain ⟨⟨⟨⟨hent, hne⟩, hcon⟩, _⟩, _⟩ := hc
    obtain ⟨htl, hhl⟩ := sinceT_spec hl
    obtain ⟨htm, hhm⟩ := sinceT_spec hm
    simp only [evalS, Bool.and_eq_true, decide_eq_true_eq]
    exact ⟨⟨⟨⟨holdsFrom_now htl hhl, holdsFrom_now htm hhm⟩, hent⟩, hne⟩, hcon⟩
  · exact absurd hc (by simp)

/-- The two entailments a two-way explanation would need. -/
theorem causalBecause_entails {h : Hist} {l m : Lit} (hc : causalBecause h l m = true) :
    entails m l = true ∧ l ≠ m ∧ contingent l = true ∧ contingent m = true := by
  unfold causalBecause at hc
  split at hc
  · simp only [Bool.and_eq_true, decide_eq_true_eq] at hc
    exact ⟨hc.1.1.1.1, hc.1.1.1.2, hc.1.1.2, hc.1.2⟩
  · exact absurd hc (by simp)

/-- **The cycle of report 2 §7.6 is broken.**  A fact and its reason can never
explain each other: that would make two different contingent literals
equivalent, and `no_equivalent_literals` shows this world has no such pair. -/
theorem causalBecause_asymm (h : Hist) (l m : Lit) :
    ¬(causalBecause h l m = true ∧ causalBecause h m l = true) := by
  rintro ⟨h1, h2⟩
  obtain ⟨he1, hne, hc1, hc2⟩ := causalBecause_entails h1
  obtain ⟨he2, _, _, _⟩ := causalBecause_entails h2
  have hall := List.all_eq_true.mp no_equivalent_literals l (mem_usefulLits hc1)
  have := List.all_eq_true.mp hall m (mem_usefulLits hc2)
  simp only [he1, he2, Bool.and_self, Bool.not_true, Bool.false_or, decide_eq_true_eq] at this
  exact hne this

/-- **Reasons chain**, which is what licenses "…, and that is why …". -/
theorem causalBecause_trans {h : Hist} {l m n : Lit}
    (h1 : causalBecause h l m = true) (h2 : causalBecause h m n = true) :
    causalBecause h l n = true := by
  have hb1 := causalBecause_entails h1
  have hb2 := causalBecause_entails h2
  unfold causalBecause at h1 h2 ⊢
  split at h1
  · rename_i tl tm hl hm
    rw [hm] at h2
    split at h2
    · rename_i tm' tn hm' hn
      rw [Option.some.injEq] at hm'
      subst hm'
      rw [hl, hn]
      simp only [Bool.and_eq_true, decide_eq_true_eq] at h1 h2 ⊢
      obtain ⟨⟨⟨⟨hent1, _⟩, hcon1⟩, _⟩, hEq1⟩ := h1
      obtain ⟨⟨⟨⟨hent2, _⟩, _⟩, hcon3⟩, hEq2⟩ := h2
      refine ⟨⟨⟨⟨law_trans hent2 hent1, ?_⟩, hcon1⟩, hcon3⟩, by omega⟩
      intro hc
      subst hc
      have hall := List.all_eq_true.mp no_equivalent_literals l (mem_usefulLits hcon1)
      have := List.all_eq_true.mp hall m (mem_usefulLits hb1.2.2.2)
      simp only [hent1, hent2, Bool.and_self, Bool.not_true, Bool.false_or,
        decide_eq_true_eq] at this
      exact hb1.2.1 this
    · exact absurd h2 (by simp)
  · exact absurd h1 (by simp)

/-! ## 5. Naming the action that did it -/

/-- If a fact started part-way through the history, the action that started
it. -/
def actionCause (h : Hist) (l : Lit) : Option (Nat × Act) :=
  match sinceT h l with
  | some (t + 1) => (h.acts[t]?).map fun a => (t, a)
  | _ => none

/-- **A named cause is a real one**: the fact was false just before that action
and has held ever since, and the action is the `t`-th thing that was done, with
`t` strictly earlier than now. -/
theorem actionCause_sound {h : Hist} {l : Lit} {t : Nat} {a : Act}
    (hc : actionCause h l = some (t, a)) :
    t < h.acts.length ∧ h.acts[t]? = some a ∧
      holdsFrom h (t + 1) l = true ∧ holdsFrom h t l = false ∧
      evalLit l (nowW h) = true := by
  unfold actionCause at hc
  split at hc
  · rename_i t' hs
    obtain ⟨ht, hh⟩ := sinceT_spec hs
    rw [hstates_length] at ht
    have htlen : t' < h.acts.length := by omega
    have hget : h.acts[t']? = some (h.acts[t']'htlen) := by
      simp [List.getElem?_eq_getElem htlen]
    rw [hget] at hc
    simp only [Option.map_some, Option.some.injEq, Prod.mk.injEq] at hc
    obtain ⟨hteq, haeq⟩ := hc
    subst hteq
    subst haeq
    refine ⟨htlen, hget, hh, sinceT_min hs (Nat.lt_succ_self t'), ?_⟩
    exact holdsFrom_now (by rw [hstates_length]; omega) hh
  · exact absurd hc (by simp)

/-- **A fact that has held all along is never given an action as its cause.**
This is what keeps definitional consequences from being dressed up as
effects. -/
theorem static_facts_have_no_action_cause {h : Hist} {l : Lit}
    (hstatic : holdsFrom h 0 l = true) : actionCause h l = none := by
  unfold actionCause
  have hzero : sinceT h l = some 0 := by
    unfold sinceT
    have hnow : evalLit l (nowW h) = true :=
      holdsFrom_now (by rw [hstates_length]; omega) hstatic
    rw [if_pos hnow]
    refine List.find?_eq_some_iff_getElem.mpr ⟨by simpa using hstatic, 0, ?_, ?_, ?_⟩
    · simp [hstates_length]
    · simp
    · intro j hj
      omega
  rw [hzero]

/-! ## 6. The complaint of report 2 §7.6, proved and then repaired -/

/-- Water at 20 °C, 1 kg; stone at −10 °C, 1 kg; lamp at −10 °C, 1 kg. -/
def w0 : World :=
  (fun e => match e with | .water => 2 | .stone => 0 | .lamp => 0,
   fun _ => 0)

/-- **The complaint is real.**  Entailment `because` accepts "the water is not
warm because the water is frozen" *and* — through the pair form — "the water is
frozen because it is not boiling and it is not warm", in the very same world.
Grounding, on its own, is cyclic. -/
theorem grounding_is_cyclic :
    evalS (.because (.warm .water, false) (.frozen .water, true))
        (step (.cool .water) w0) = true ∧
    evalS (.because2 (.frozen .water, true) (.boiling .water, false)
        (.warm .water, false)) (step (.cool .water) w0) = true := by
  constructor <;> native_decide

/-- The demonstration history: the water starts warm, we cool it, then we heat
the stone twice. -/
def demoHist : Hist := ⟨w0, [.cool .water, .heat .stone, .heat .stone]⟩

/-- **A reason that arrives with the fact is accepted.**  Cooling the water made
it frozen and not warm at the same instant, so "the water is not warm, because
the water is frozen" stands. -/
theorem coeval_reason_accepted :
    causalBecause demoHist (.warm .water, false) (.frozen .water, true) = true := by
  native_decide

/-- **A reason that arrives after the fact is rejected.**  The water has not
been boiling since the beginning, and the stone only became hotter than it at
step three; entailment `because` accepts "the water is not boiling because the
stone is hotter than the water", the timed connective does not. -/
theorem late_reason_rejected :
    evalS (.because (.boiling .water, false) (.hotter .stone .water, true))
        (nowW demoHist) = true ∧
    causalBecause demoHist (.boiling .water, false) (.hotter .stone .water, true) = false := by
  constructor <;> native_decide

/-- And the action that did it is named: the water became frozen at step one,
when we cooled it. -/
theorem demo_action_cause :
    actionCause demoHist (.frozen .water, true) = some (0, .cool .water) := by
  native_decide

/-! ## 7. Counting the filter -/

/-- The pairs `(l, m)` for which "`l` because `m`" is a *ground* at all: `m`
forces `l` in every world, they differ, and both say something.  There are 78
of them in this vocabulary. -/
def groundPairs : List (Lit × Lit) :=
  usefulLits.flatMap fun l => (usefulLits.filter fun m =>
    entails m l && decide (l ≠ m) && contingent l).map fun m => (l, m)

/-- Every history of at most two actions out of every one of the 512 worlds:
4608 histories. -/
def allHists : List Hist :=
  allWorlds.flatMap fun w => (Narrative.seqsUpTo 2).map fun s => ⟨w, s⟩

def tally (f : Hist → Lit × Lit → Bool) : Nat :=
  allHists.foldl (fun acc h => acc + (groundPairs.filter (f h)).length) 0

/-- Both parts of the pair hold now — this is exactly what the old `because`
asks for. -/
def bothNow (h : Hist) (p : Lit × Lit) : Bool :=
  evalLit p.1 (nowW h) && evalLit p.2 (nowW h)

/-- The fact and its reason came into force at the same moment. -/
def coevalNow (h : Hist) (p : Lit × Lit) : Bool :=
  match sinceT h p.1, sinceT h p.2 with
  | some tl, some tm => decide (tl = tm)
  | _, _ => false

/-- The strictly-older filter, which `strictly_older_reason_never_exists` says
must be empty. -/
def strictlyOlder (h : Hist) (p : Lit × Lit) : Bool :=
  match sinceT h p.1, sinceT h p.2 with
  | some tl, some tm => decide (tm < tl)
  | _, _ => false

/-- On a ground pair, the timed connective *is* the coevalness test — the
entailment side conditions are already met — so the counts below are counts of
`causalBecause`. -/
theorem causalBecause_eq_coeval {h : Hist} {l m : Lit}
    (hent : entails m l = true) (hne : l ≠ m)
    (hcl : contingent l = true) (hcm : contingent m = true) :
    causalBecause h l m = coevalNow h (l, m) := by
  unfold causalBecause coevalNow
  cases hl : sinceT h l <;> cases hm : sinceT h m <;>
    simp [hent, hne, hcl, hcm]

/-- Every pair in `groundPairs` satisfies the side conditions. -/
theorem groundPairs_spec {p : Lit × Lit} (hp : p ∈ groundPairs) :
    entails p.2 p.1 = true ∧ p.1 ≠ p.2 ∧ contingent p.1 = true ∧ contingent p.2 = true := by
  obtain ⟨l, hl, hp⟩ := List.mem_flatMap.mp hp
  obtain ⟨m, hm, rfl⟩ := List.mem_map.mp hp
  obtain ⟨hmu, hfil⟩ := List.mem_filter.mp hm
  simp only [Bool.and_eq_true, decide_eq_true_eq] at hfil
  exact ⟨hfil.1.1, hfil.1.2, hfil.2, (List.mem_filter.mp hmu).2⟩

/-- **The filter, measured over all 4608 histories.**  The counts are the
honest measure of what a direction of time buys:

* the entailment `because` accepts 1180416 clause instances;
* the timed connective accepts fewer — it throws out exactly the explanations
  whose reason turned up after the fact;
* the strictly-older filter suggested in report 2 §8 accepts none at all, as
  `strictly_older_reason_never_exists` proves it must. -/
theorem causal_filter_counts :
    tally bothNow = 1180416 ∧
    tally coevalNow = 1051584 ∧
    tally strictlyOlder = 0 := by
  refine ⟨?_, ?_, ?_⟩ <;> native_decide

/-! ## 8. English, with "that is why" -/

/-- "…, and that is why …": a chain of reasons rendered as connected clauses.
Soundness of the chain is `causalBecause_trans`. -/
def renderChain (ls : List Lit) : String :=
  match ls with
  | [] => ""
  | l :: rest =>
      Chat.renderLit l ++
        String.intercalate "" (rest.map fun m => ", and that is why " ++ Chat.renderLit m)

/-- What the system says about the demonstration history. -/
def demoCausalText : List String :=
  let l : Lit := (.warm .water, false)
  let m : Lit := (.frozen .water, true)
  [ Chat.renderLit l ++ ", because " ++ Chat.renderLit m,
    match actionCause demoHist m with
    | some (t, a) => Chat.renderLit m ++ ", because at step " ++ toString (t + 1) ++
        " " ++ Chat.renderAct a
    | none => Chat.renderLit m ++ " has been the case all along",
    renderChain [m, l],
    "not: " ++ Chat.renderLit (.boiling .water, false) ++ ", because " ++
      Chat.renderLit (.hotter .stone .water, true) ++
      " — the reason turned up after the fact" ]

#eval demoCausalText

end Causation
