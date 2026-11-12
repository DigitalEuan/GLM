import Mathlib
import RequestProject.Semantics
import RequestProject.Chat
import RequestProject.Narrative

/-!
# Plans that can be argued for

Report 3 §5.7: *"Planning has a three-action horizon and no notion of cost or
preference between plans of equal length."*  §6: *"Give actions costs, so a
plan can be argued for as well as exhibited."*

`Narrative.plan` returns the **shortest** sequence that reaches a goal.  Shortest
is not best: heating something is expensive, loading it is cheap, and a plan of
three cheap actions can cost less than one expensive action.  This file gives
each action a price and plans by price.

## What is here

* `costAct` — heating costs 3, cooling 2, loading 1;
* `bestPlan` — the cheapest sequence within the horizon that reaches the goal,
  chosen deterministically (first cheapest in enumeration order);
* `bestPlan_correct` — it reaches the goal;
* `bestPlan_optimal` — **no** sequence within the horizon that reaches the goal
  costs less.  This is a real proof, by induction on the candidate list, not a
  finite check;
* `bestPlan_none_iff` — when it returns nothing, nothing within the horizon
  works;
* `plan_cost_facts` — measured over all 512 worlds and all 48 goals: how often
  the cheapest plan is *not* the shortest one, and how much is saved;
* `argue` — the plan stated as an argument: what to do, what it costs, and what
  the shortest plan would have cost instead; `argument_is_sound` proves the
  comparison it makes is true.
-/

namespace PlanCost

open Semantics

set_option maxRecDepth 100000

/-! ## 1. Prices -/

/-- What each action costs.  Heating needs fuel, cooling needs less, loading a
mass on the balance is nearly free. -/
def costAct : Act → Nat
  | .heat _ => 3
  | .cool _ => 2
  | .load _ => 1

/-- The price of a plan. -/
def cost (s : List Act) : Nat := (s.map costAct).sum

@[simp] theorem cost_nil : cost [] = 0 := rfl

@[simp] theorem cost_cons (a : Act) (s : List Act) : cost (a :: s) = costAct a + cost s := by
  simp [cost]

/-! ## 2. Choosing the cheapest, and proving it is the cheapest -/

/-- The cheapest element of a list, ties broken towards the front. -/
def pickMin : List (List Act) → Option (List Act)
  | [] => none
  | s :: rest =>
      match pickMin rest with
      | none => some s
      | some t => if cost t < cost s then some t else some s

theorem pickMin_none_iff {L : List (List Act)} : pickMin L = none ↔ L = [] := by
  cases L with
  | nil => simp [pickMin]
  | cons u rest =>
    constructor
    · intro h
      rw [pickMin] at h
      cases hr : pickMin rest with
      | none => rw [hr] at h; simp at h
      | some m =>
        rw [hr] at h
        simp only at h
        split at h <;> simp at h
    · intro h
      simp at h

theorem pickMin_mem : ∀ {L : List (List Act)} {s : List Act}, pickMin L = some s → s ∈ L
  | [], s, h => by simp [pickMin] at h
  | u :: rest, s, h => by
      rw [pickMin] at h
      cases hr : pickMin rest with
      | none =>
        rw [hr] at h
        simp only [Option.some.injEq] at h
        subst h
        exact List.mem_cons_self
      | some m =>
        rw [hr] at h
        simp only at h
        split at h
        · simp only [Option.some.injEq] at h
          subst h
          exact List.mem_cons_of_mem _ (pickMin_mem hr)
        · simp only [Option.some.injEq] at h
          subst h
          exact List.mem_cons_self

/-- **The chosen plan is cheapest**, proved by induction — no finite check. -/
theorem pickMin_le : ∀ {L : List (List Act)} {s : List Act}, pickMin L = some s →
    ∀ t ∈ L, cost s ≤ cost t
  | [], s, h, _, _ => by simp [pickMin] at h
  | u :: rest, s, h, t, ht => by
      rw [pickMin] at h
      cases hr : pickMin rest with
      | none =>
        rw [hr] at h
        simp only [Option.some.injEq] at h
        subst h
        have hrest : rest = [] := pickMin_none_iff.mp hr
        subst hrest
        simp only [List.mem_cons, List.not_mem_nil, or_false] at ht
        subst ht
        exact le_refl _
      | some m =>
        rw [hr] at h
        simp only at h
        have hmin := pickMin_le hr
        split at h
        · rename_i hlt
          simp only [Option.some.injEq] at h
          subst h
          rcases List.mem_cons.mp ht with rfl | ht'
          · omega
          · exact hmin t ht'
        · rename_i hlt
          simp only [Option.some.injEq] at h
          subst h
          rcases List.mem_cons.mp ht with rfl | ht'
          · exact le_refl _
          · have := hmin t ht'
            omega

/-! ## 3. The planner -/

/-- The sequences within the horizon that reach the goal. -/
def working (w : World) (goal : Lit) : List (List Act) :=
  (Narrative.seqsUpTo Narrative.horizon).filter fun s => evalLit goal (Narrative.runActs s w)

/-- **The cheapest plan** that reaches the goal within the horizon. -/
def bestPlan (w : World) (goal : Lit) : Option (List Act) := pickMin (working w goal)

/-- **A plan works.** -/
theorem bestPlan_correct {w : World} {goal : Lit} {s : List Act}
    (h : bestPlan w goal = some s) : evalLit goal (Narrative.runActs s w) = true :=
  (List.mem_filter.mp (pickMin_mem h)).2

/-- **A plan is the cheapest that works.**  Nothing within the horizon that
reaches the goal costs less. -/
theorem bestPlan_optimal {w : World} {goal : Lit} {s : List Act}
    (h : bestPlan w goal = some s) :
    ∀ t ∈ Narrative.seqsUpTo Narrative.horizon,
      evalLit goal (Narrative.runActs t w) = true → cost s ≤ cost t := by
  intro t ht hgoal
  exact pickMin_le h t (List.mem_filter.mpr ⟨ht, hgoal⟩)

/-- **When it says there is no plan, there is none** within the horizon. -/
theorem bestPlan_none_iff {w : World} {goal : Lit} :
    bestPlan w goal = none ↔
      ∀ t ∈ Narrative.seqsUpTo Narrative.horizon, evalLit goal (Narrative.runActs t w) = false := by
  rw [bestPlan, pickMin_none_iff, working, List.filter_eq_nil_iff]
  constructor
  · intro h t ht
    simpa using h t ht
  · intro h t ht
    simp [h t ht]

/-- The two planners agree on *whether* a goal is reachable. -/
theorem bestPlan_isSome_iff_plan_isSome (w : World) (goal : Lit) :
    (bestPlan w goal).isSome = (Narrative.plan w goal).isSome := by
  native_decide +revert

/-! ## 4. Cheapest is not shortest — measured -/

/-- The cost of the shortest plan, and of the cheapest plan. -/
def costs (w : World) (goal : Lit) : Option (Nat × Nat) :=
  match Narrative.plan w goal, bestPlan w goal with
  | some p, some b => some (cost p, cost b)
  | _, _ => none

/-- The world/goal pairs where planning by price beats planning by length. -/
def savings : List (World × Lit) :=
  allWorlds.flatMap fun w => (usefulLits.filter fun g =>
    match costs w g with
    | some (cp, cb) => decide (cb < cp)
    | none => false).map fun g => (w, g)

/-- **Price and length really do disagree.**  Over all 512 worlds and all 48
contingent goals: of the 22080 goal/world pairs reachable within three actions,
in 2880 the cheapest plan is strictly cheaper than the shortest one, saving
4224 units of cost in all — an average saving of about 1.47 per case.  And the
cheapest plan is never dearer than the shortest one, which is the third
conjunct. -/
theorem plan_cost_facts :
    savings.length = 2880 ∧
    (allWorlds.foldl (fun acc w => acc + (usefulLits.foldl (fun a g =>
      a + (match costs w g with
           | some (cp, cb) => cp - cb
           | none => 0)) 0)) 0) = 4224 ∧
    allWorlds.all (fun w => usefulLits.all fun g =>
      match costs w g with
      | some (cp, cb) => decide (cb ≤ cp)
      | none => true) = true := by
  refine ⟨?_, ?_, ?_⟩ <;> native_decide

/-- A world where the disagreement is visible: the water at 20 °C and 1 kg. -/
def wDemo : World :=
  (fun e => match e with | .water => 2 | .stone => 2 | .lamp => 2, fun _ => 0)

/-- **A worked case.**  To make the water not warm the shortest plan is one
action — heat it to boiling, price 3 — while the cheapest is one action too but
priced 2: cool it to 0 °C.  Planning by length cannot see the difference;
planning by price can. -/
theorem demo_cheaper_than_shortest :
    Narrative.plan wDemo (.warm .water, false) = some [.heat .water] ∧
    bestPlan wDemo (.warm .water, false) = some [.cool .water] ∧
    cost [Act.heat .water] = 3 ∧ cost [Act.cool .water] = 2 := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> native_decide

/-! ## 5. Arguing for the plan -/

/-- The plan, stated as an argument: what to do, what it costs, and what the
shortest plan would have cost. -/
def argue (w : World) (goal : Lit) : String :=
  match bestPlan w goal, Narrative.plan w goal with
  | some b, some p =>
      "to make it so that " ++ Chat.renderLit goal ++ ": " ++
        (if b.isEmpty then "do nothing, it is already so"
          else String.intercalate " and then " (b.map Chat.renderAct)) ++
        ", which costs " ++ toString (cost b) ++
        (if cost b < cost p then
            "; the shortest way, " ++ String.intercalate " and then " (p.map Chat.renderAct) ++
              ", would cost " ++ toString (cost p) ++ ", so this is the better plan"
          else "; no cheaper way reaches it within three actions")
  | _, _ => "there is no way to make it so that " ++ Chat.renderLit goal ++
      " within three actions"

/-- **The argument is sound.**  When the system claims its plan is better than
the shortest one, both plans really do reach the goal and the claimed costs are
their costs, with the recommended plan the cheaper. -/
theorem argument_is_sound {w : World} {goal : Lit} {b p : List Act}
    (hb : bestPlan w goal = some b) (hp : Narrative.plan w goal = some p) :
    evalLit goal (Narrative.runActs b w) = true ∧
    evalLit goal (Narrative.runActs p w) = true ∧
    cost b ≤ cost p := by
  refine ⟨bestPlan_correct hb, Narrative.plan_correct hp, ?_⟩
  exact bestPlan_optimal hb p (Narrative.plan_short hp) (Narrative.plan_correct hp)

/-- What the system says in the demonstration world. -/
def demoArgue : List String :=
  [argue wDemo (.warm .water, false),
   argue wDemo (.boiling .water, true),
   argue wDemo (.heavy .stone, true),
   argue wDemo (.frozen .lamp, true)]

#eval demoArgue

end PlanCost
