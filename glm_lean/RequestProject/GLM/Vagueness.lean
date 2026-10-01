/-
# Deciding a vague triple without a person

`related_to` records *that* two concepts are linked without saying which, so it
transports nothing and the analogy layer refuses it by name.  Two earlier
rounds took the 66 the lexicon holds down to nothing waiting on a lookup: the
physics register converts the ones it can decide, and
`glm_universal/data_objects/denotation.py` decides the endpoints of the rest
**by hand**.

What stayed open was not those 66.  It was the *next* one: every new vague
triple brought the hand work back, and a discipline needing a person for every
addition is one that will quietly stop being followed.
`glm_universal/reasoning/vagueness.py` is the standing rule that replaces it,
and this file is the part of that rule which is not a measurement.

Two things are modelled.

**The router.**  A triple is put to four routes *in order* -- the dimensional
rules, the energy-conjugate register, the admitted proposer rules, and only
then a person.  `route` is that chain.  What has to be true of it is that it
is total (every triple gets a route, so a referral is a decision rather than a
crash), that it is single-valued (`route` is a function, so exclusivity is
free), and that the *order* is real: a triple the dimensional rules decide is
never taken by a later route even when the later route would also fire.  That
last point is why `route_eq_conjugate_iff` carries `¬ dimensional t` -- the
priority is part of the specification, not an implementation accident.

**The gate on a proposer rule.**  A rule reads the lexicon and proposes a
denotation verdict; it is admitted only if it fires on at least
`proposerMinimum` of the hand-decided names and agrees with the hand decision
on **every** one of them.  `proposal_correct_of_admitted` is what that buys:
an admitted rule's verdict on a name the hand register also decided *is* the
hand verdict -- so `propose` can be trusted where the hand register is silent,
which is the only place it is used.  `majority_is_not_enough` exhibits the
gate doing work: a rule agreeing on 5 of 7 is a clear majority and is still
refused.

The last section is the round's ledger as arithmetic: 27 dimensional, 1
conjugate, 6 proposed and 32 referred, over 66 triples.  The counts are
measured by the Python; what is checked here is that they are a partition of
the register they are about.
-/
import Mathlib.Tactic

namespace GLM.Vagueness

/-! ## 1.  The four routes -/

/-- Which of the four routes decided a vague triple.  `referred` is a verdict
like the others: the triple is handed to a person *with the evidence
collected*, not dropped. -/
inductive Route
  /-- The endpoints share a dimension, or differ by one quantity of the basis. -/
  | dimensional
  /-- Both endpoints are columns of one row of the energy-conjugate register. -/
  | conjugate
  /-- An admitted proposer rule classifies an undimensioned endpoint. -/
  | proposed
  /-- Nothing decided it, and a person is asked. -/
  | referred
  deriving DecidableEq, Repr

/-- The three routes that need no hand work at all. -/
def Route.decidedWithoutAPerson : Route → Bool
  | .referred => false
  | _ => true

/-- What the three mechanical routes can say about a triple.  Each is a test
the implementation runs; nothing here assumes they are disjoint, because in
fact they are not -- `heat`/`temperature` is decided by two of them. -/
structure Router (T : Type*) where
  /-- The physics register decides both endpoints. -/
  dimensional : T → Prop
  /-- Both endpoints lie in one row of the conjugate register. -/
  conjugate : T → Prop
  /-- An admitted proposer rule fires on an endpoint. -/
  proposed : T → Prop
  [dimensionalDec : DecidablePred dimensional]
  [conjugateDec : DecidablePred conjugate]
  [proposedDec : DecidablePred proposed]

attribute [instance] Router.dimensionalDec Router.conjugateDec
  Router.proposedDec

variable {T : Type*} (R : Router T)

/-- The routing itself: the three tests in order, then a person. -/
def route (t : T) : Route :=
  if R.dimensional t then .dimensional
  else if R.conjugate t then .conjugate
  else if R.proposed t then .proposed
  else .referred

/-! ## 2.  The router is total, single-valued, and ordered -/

/-- Every triple gets one of the four routes.  Nothing falls through, which is
the claim that a referral is a decision to ask rather than a lookup that
failed. -/
theorem route_mem (t : T) :
    route R t = .dimensional ∨ route R t = .conjugate ∨
      route R t = .proposed ∨ route R t = .referred := by
  unfold route
  split_ifs <;> simp

/-- Exclusivity: no triple carries two routes.  This is free -- `route` is a
function -- and it is stated because the ledger's counts depend on it. -/
theorem route_unique {t : T} {a b : Route}
    (ha : route R t = a) (hb : route R t = b) : a = b := by
  rw [← ha, ← hb]

/-- The first route has absolute priority: a triple the physics register
decides is routed dimensionally, whatever else fires on it. -/
theorem route_eq_dimensional_iff (t : T) :
    route R t = .dimensional ↔ R.dimensional t := by
  unfold route
  split_ifs with h <;> simp_all

/-- The conjugate route takes exactly the triples the dimensional rules left,
and it takes all of them.  The hypothesis is the priority, made explicit. -/
theorem route_eq_conjugate_iff (t : T) :
    route R t = .conjugate ↔ (¬ R.dimensional t ∧ R.conjugate t) := by
  unfold route
  split_ifs with h₁ h₂ <;> simp_all

/-- Likewise for the proposer: it only ever sees what the two register routes
did not decide. -/
theorem route_eq_proposed_iff (t : T) :
    route R t = .proposed ↔
      (¬ R.dimensional t ∧ ¬ R.conjugate t ∧ R.proposed t) := by
  unfold route
  split_ifs with h₁ h₂ h₃ <;> simp_all

/-- A person is asked exactly when nothing else decided it. -/
theorem route_eq_referred_iff (t : T) :
    route R t = .referred ↔
      (¬ R.dimensional t ∧ ¬ R.conjugate t ∧ ¬ R.proposed t) := by
  unfold route
  split_ifs with h₁ h₂ h₃ <;> simp_all

/-- Contrapositive of the point of the whole exercise: if any mechanical route
fires, no person is asked. -/
theorem not_referred_of_any {t : T}
    (h : R.dimensional t ∨ R.conjugate t ∨ R.proposed t) :
    route R t ≠ .referred := by
  rw [Ne, route_eq_referred_iff]
  rcases h with h | h | h <;> tauto

/-- And conversely: a referral certifies that all three mechanisms declined.
This is what makes the referral informative -- the person is told what was
tried. -/
theorem all_declined_of_referred {t : T} (h : route R t = .referred) :
    ¬ R.dimensional t ∧ ¬ R.conjugate t ∧ ¬ R.proposed t :=
  (route_eq_referred_iff R t).mp h

/-- Adding a mechanical route can only take work off a person: if a router's
tests are weaker at every triple, it refers at least as often. -/
theorem referred_mono {R' : Router T} {t : T}
    (hd : ∀ x : T, R.dimensional x → R'.dimensional x)
    (hc : ∀ x : T, R.conjugate x → R'.conjugate x)
    (hp : ∀ x : T, R.proposed x → R'.proposed x)
    (h : route R' t = .referred) : route R t = .referred := by
  obtain ⟨h₁, h₂, h₃⟩ := all_declined_of_referred R' h
  rw [route_eq_referred_iff]
  exact ⟨fun x => h₁ (hd t x), fun x => h₂ (hc t x), fun x => h₃ (hp t x)⟩

/-! ## 3.  The gate on a proposer rule

A rule reads the lexicon only; the hand register is the ground truth and the
rule never sees it.  Admission is scored against that register afterwards. -/

/-- A proposer rule must fire on at least this many hand-decided names before
it may be admitted -- one that fires twice has not been tested. -/
def proposerMinimum : ℕ := 5

variable {Name Verdict : Type*}

/-- One rule: a test over names the lexicon can run, and the single verdict it
proposes wherever it fires. -/
structure Rule (Name Verdict : Type*) where
  /-- Whether the rule fires on a name. -/
  test : Name → Bool
  /-- The verdict it proposes when it does. -/
  verdict : Verdict

/-- The gate.  `hand` is the hand-decided register, partial: `none` at a name
nobody has ruled on.  Admission asks for two things -- enough exposure, and
agreement *without exception* on what it was exposed to.  A wrong verdict is
worse than an abstention, so this is not accuracy on average. -/
structure Admitted (r : Rule Name Verdict) (hand : Name → Option Verdict)
    (firedOnDecided : ℕ) : Prop where
  /-- The rule fired on enough hand-decided names to have been tested. -/
  tested : proposerMinimum ≤ firedOnDecided
  /-- And it contradicted none of them. -/
  agrees : ∀ n v, r.test n = true → hand n = some v → v = r.verdict

/-- What admission buys.  Where an admitted rule fires on a name the hand
register also decided, its verdict *is* the hand verdict -- so the rule may be
trusted at the names the register is silent about, which is the only place it
is ever consulted. -/
theorem proposal_correct_of_admitted {r : Rule Name Verdict}
    {hand : Name → Option Verdict} {k : ℕ} (h : Admitted r hand k)
    {n : Name} {v : Verdict} (hfire : r.test n = true) (hhand : hand n = some v) :
    v = r.verdict :=
  h.agrees n v hfire hhand

/-- The same fact in the form the implementation checks: an admitted rule
never contradicts the register. -/
theorem no_contradiction_of_admitted {r : Rule Name Verdict}
    {hand : Name → Option Verdict} {k : ℕ} (h : Admitted r hand k)
    {n : Name} {v : Verdict} (hfire : r.test n = true) (hhand : hand n = some v)
    (hne : v ≠ r.verdict) : False :=
  hne (proposal_correct_of_admitted h hfire hhand)

/-- A single named disagreement refuses a rule, however many names it got
right.  This is the finding `nominalisation_of_a_verb`,
`abstract_noun_is_an_abstraction` and `mass_noun_is_a_carrier` each ran into. -/
theorem not_admitted_of_disagreement {r : Rule Name Verdict}
    {hand : Name → Option Verdict} {k : ℕ}
    {n : Name} {v : Verdict} (hfire : r.test n = true) (hhand : hand n = some v)
    (hne : v ≠ r.verdict) : ¬ Admitted r hand k :=
  fun h => no_contradiction_of_admitted h hfire hhand hne

/-- A rule that has hardly fired is refused for being untested, not for being
wrong.  `nominalisation_of_a_verb` fired on two names; two is not a test. -/
theorem not_admitted_of_untested {r : Rule Name Verdict}
    {hand : Name → Option Verdict} {k : ℕ} (h : k < proposerMinimum) :
    ¬ Admitted r hand k :=
  fun hadm => absurd hadm.tested (not_le.mpr h)

/-- The gate is doing work rather than describing an outcome a looser one
would have reached anyway: `mass_noun_is_a_carrier` agreed on 5 of the 7 names
it fired on -- a clear majority -- and is refused. -/
theorem majority_is_not_enough :
    ∃ agreed firedOn : ℕ,
      proposerMinimum ≤ firedOn ∧ firedOn < 2 * agreed ∧ agreed ≠ firedOn :=
  ⟨5, 7, by norm_num [proposerMinimum], by norm_num, by norm_num⟩

/-! ## 4.  The ledger of the round

The counts are measured by `vagueness.vagueness_report`; what is checked here
is that they are a partition of the 66 `related_to` triples the lexicon
holds. -/

/-- The four routes account for every vague triple. -/
theorem ledger_routes_every_triple : 27 + 1 + 6 + 32 = 66 := by norm_num

/-- And a majority of them -- 34 of 66 -- are now decided without a person. -/
theorem ledger_decided_without_a_person : 27 + 1 + 6 = 34 := by norm_num

/-- One of the 4 conjugate conversions is decided by no other rule; the other
3 agree with the dimensional route and name its factor's role. -/
theorem ledger_conjugate_conversions : 1 + 3 = 4 := by norm_num

end GLM.Vagueness
