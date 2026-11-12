import Mathlib
import RequestProject.PlanCost

/-!
# Planning without a horizon

Report 3 §5.7: *"Planning has a three-action horizon and no notion of cost or
preference between plans of equal length."*  `PlanCost.lean` supplied the
prices; the horizon remained, because both planners enumerate action
*sequences*, and there are `9^k` of those.

This file plans over the **worlds** instead.  There are only 512 of them, so a
relaxation over the world graph — each world joined to its nine successors, the
edges priced by `PlanCost.costAct` — settles in a handful of rounds and knows
the cheapest cost to reach every world, at any depth whatever.

## The certificate

The table is computed by iterating relaxation, but nothing is trusted to the
iteration.  What is checked afterwards is a **certificate**, which is a
different and much weaker thing to verify:

* `costOf_start` — the starting world costs nothing;
* `costOf_relaxed` — no edge can improve the table: `d(step a w) ≤ d w + cost a`
  for every world and every action;
* `plan_is_real` — every finite entry of the table is witnessed by an actual
  action sequence of exactly that cost, which really reaches that world.

From the first two, `costOf_le_cost_of_plan` follows **by induction over the
plan**, for plans of *any* length: no sequence of actions, however long, reaches
a world more cheaply than the table says.  So `bestCost` and `bestPlan` are
optimal with no horizon at all (`unbounded_optimality`).

## What it buys, measured

`horizon_gain` compares this planner with the three-action planner of
`PlanCost.lean`.  The comparison is a split verdict, and both halves are
counted rather than asserted: on single-literal goals the horizon costs
nothing — the two planners solve the same 54 goals at the same price — while on
*world* goals three actions reach only 63 of the 512 worlds and the table
reaches all of them, at up to 12 actions.
-/

namespace ReachPlan

open Semantics Narrative PlanCost

set_option maxRecDepth 100000

/-! ## 1. Indexing the world graph -/

/-- The position of a world in the standard enumeration. -/
def idxOf (w : World) : Nat := allWorlds.findIdx fun v => decide (v = w)

theorem idxOf_lt (w : World) : idxOf w < allWorlds.length := by
  refine List.findIdx_lt_length.mpr ?_
  exact ⟨w, mem_allWorlds w, by simp⟩

theorem allWorlds_idxOf (w : World) : allWorlds[idxOf w]! = w := by
  have h1 : idxOf w < allWorlds.length := idxOf_lt w
  have h2 := List.findIdx_getElem (xs := allWorlds) (p := fun v => decide (v = w)) (w := h1)
  rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem h1]
  simpa [idxOf] using h2

/-! ## 2. The relaxation -/

/-- A large value standing for "not reached". -/
def inf : Nat := 1000000

/-- The starting world of the demonstration: everything cold and light. -/
def w0 : World := (fun _ => 0, fun _ => 0)

/-- One round of relaxation over every world and every action. -/
def round (s : Array Nat × Array (List Act)) : Array Nat × Array (List Act) :=
  (List.range allWorlds.length).foldl
    (fun acc i =>
      allActs.foldl
        (fun acc a =>
          let w := allWorlds[i]!
          let j := idxOf (step a w)
          let c := acc.1[i]! + costAct a
          if acc.1[i]! < inf ∧ c < acc.1[j]! then
            (acc.1.set! j c, acc.2.set! j (acc.2[i]! ++ [a]))
          else acc)
        acc)
    s

/-- Iterate the relaxation. -/
def rounds : Nat → Array Nat × Array (List Act) → Array Nat × Array (List Act)
  | 0, s => s
  | k + 1, s => rounds k (round s)

/-- The table: cheapest known cost, and a plan of that cost, for each of the
512 worlds. -/
def tbl : Array Nat × Array (List Act) :=
  rounds 12
    ((Array.replicate allWorlds.length inf).set! (idxOf w0) 0,
     Array.replicate allWorlds.length ([] : List Act))

/-- The cheapest cost of reaching `w` from the start, as the table has it. -/
def costOf (w : World) : Nat := tbl.1[idxOf w]!

/-- The plan the table offers for reaching `w`. -/
def planOf (w : World) : List Act := tbl.2[idxOf w]!

/-! ## 3. The certificate -/

/-- **The start costs nothing.** -/
theorem costOf_start : costOf w0 = 0 := by native_decide

/-- **No edge can improve the table.**  For every world and every action, the
successor is already recorded at no more than the cost of getting here plus the
price of the action.  This is the fixpoint property of the relaxation, checked
over all 512 × 9 edges. -/
theorem costOf_relaxed : ∀ w ∈ allWorlds, ∀ a ∈ allActs,
    costOf (step a w) ≤ costOf w + costAct a := by native_decide

/-- **Every entry is witnessed by a real plan** of exactly that cost. -/
theorem plan_is_real : ∀ w ∈ allWorlds,
    runActs (planOf w) w0 = w ∧ cost (planOf w) = costOf w := by native_decide

/-- Every world is reached: no entry of the table is left at infinity. -/
theorem all_worlds_reached : ∀ w ∈ allWorlds, costOf w < inf := by native_decide

/-! ## 4. Optimality, at any depth -/

/-- **The table is a lower bound on every plan, of every length.**  Proved by
induction over the action sequence from the two checked facts above — not by
enumerating sequences, which is why there is no horizon. -/
theorem costOf_le_cost_of_plan : ∀ (s : List Act) (w : World),
    costOf (runActs s w) ≤ costOf w + cost s := by
  intro s
  induction s with
  | nil => intro w; simp [runActs, cost]
  | cons a t ih =>
      intro w
      have h1 : costOf (step a w) ≤ costOf w + costAct a :=
        costOf_relaxed w (mem_allWorlds w) a (by
          cases a <;> simp [allActs, ents] <;> rename_i e <;> cases e <;> simp)
      have h2 := ih (step a w)
      simp only [runActs, cost_cons]
      omega

/-- The cheapest cost of making a goal true, over all the worlds that make it
true. -/
def bestCost (goal : Lit) : Nat :=
  (allWorlds.filter fun w => evalLit goal w).foldl (fun acc w => min acc (costOf w)) inf

private theorem foldl_min_le_acc (L : List World) (acc : Nat) :
    L.foldl (fun acc v => min acc (costOf v)) acc ≤ acc := by
  induction L generalizing acc with
  | nil => simp
  | cons v t ih => exact le_trans (ih (min acc (costOf v))) (min_le_left _ _)

private theorem foldl_min_le_mem (w : World) : ∀ (L : List World) (acc : Nat), w ∈ L →
    L.foldl (fun acc v => min acc (costOf v)) acc ≤ costOf w := by
  intro L
  induction L with
  | nil => intro acc h; cases h
  | cons v t ih =>
      intro acc h
      rcases List.mem_cons.mp h with rfl | h'
      · exact le_trans (foldl_min_le_acc t (min acc (costOf w))) (min_le_right _ _)
      · exact ih _ h'

/-- The table's minimum over the goal-satisfying worlds is at most the entry of
any one of them. -/
theorem bestCost_le {goal : Lit} {w : World} (hw : evalLit goal w = true) :
    bestCost goal ≤ costOf w :=
  foldl_min_le_mem w _ inf (List.mem_filter.mpr ⟨mem_allWorlds w, hw⟩)

/-- **No plan of any length beats the table.**  Whatever sequence of actions is
proposed, if it makes the goal true then it costs at least `bestCost`. -/
theorem unbounded_optimality (goal : Lit) (s : List Act)
    (h : evalLit goal (runActs s w0) = true) : bestCost goal ≤ cost s := by
  have h1 : bestCost goal ≤ costOf (runActs s w0) := bestCost_le h
  have h2 : costOf (runActs s w0) ≤ costOf w0 + cost s := costOf_le_cost_of_plan s w0
  rw [costOf_start] at h2
  omega

/-- The plan the system offers for a goal: the cheapest recorded world that
satisfies it. -/
def bestGoalPlan (goal : Lit) : Option (List Act) :=
  match (allWorlds.filter fun w => evalLit goal w).find? fun w =>
      decide (costOf w = bestCost goal) with
  | none => none
  | some w => some (planOf w)

/-- **And the plan it offers works, and costs exactly the optimum.** -/
theorem bestGoalPlan_correct (goal : Lit) (s : List Act) (h : bestGoalPlan goal = some s) :
    evalLit goal (runActs s w0) = true ∧ cost s = bestCost goal := by
  unfold bestGoalPlan at h
  cases hw : (allWorlds.filter fun w => evalLit goal w).find?
      (fun w => decide (costOf w = bestCost goal)) with
  | none =>
      rw [hw] at h
      have h' : (none : Option (List Act)) = some s := h
      cases h'
  | some w =>
      rw [hw] at h
      have hs : s = planOf w := (Option.some.inj (show some (planOf w) = some s from h)).symm
      have hmem := List.mem_of_find?_eq_some hw
      have hgoal : evalLit goal w = true := (List.mem_filter.mp hmem).2
      have hcost : costOf w = bestCost goal := of_decide_eq_true
        (List.find?_some (p := fun v => decide (costOf v = bestCost goal)) hw)
      obtain ⟨hrun, hc⟩ := plan_is_real w (mem_allWorlds w)
      refine ⟨?_, ?_⟩
      · rw [hs, hrun]; exact hgoal
      · rw [hs, hc, hcost]

/-! ## 5. What the horizon was costing -/

/-- The three-action planner's cost for a goal from `w0`, if it has a plan. -/
def horizonCost (goal : Lit) : Option Nat :=
  (PlanCost.bestPlan w0 goal).map cost

/-- The worlds the three-action planner can reach at all. -/
def reachableWithinHorizon : List World :=
  (Narrative.seqsUpTo Narrative.horizon).map fun s => runActs s w0

set_option maxHeartbeats 2000000 in
/-- **What planning over worlds buys, measured — and where it buys nothing.**

On *literal* goals the horizon was not binding at all: of the 60 literals both
planners solve the same 54, at exactly the same price, and the 6 neither solves
are the 6 no world satisfies.  So for single-literal goals the horizon-free
planner is complete, and it is no cheaper: the three-action planner was already
optimal, it just could not say so.

On *world* goals the difference is large: three actions reach only 63 of the
512 worlds, while the table reaches all 512, at up to 30 units of cost and 12
actions — four times the horizon. -/
theorem horizon_gain :
    (allLits.filter fun g => (horizonCost g).isSome).length = 54 ∧
    (allLits.filter fun g => decide (bestCost g < inf)).length = 54 ∧
    (allLits.all fun g => match horizonCost g with
      | none => true
      | some c => decide (bestCost g = c)) = true ∧
    (allLits.all fun g =>
      decide ((bestCost g < inf) = (allWorlds.any fun w => evalLit g w))) = true ∧
    (allWorlds.filter fun w => reachableWithinHorizon.contains w).length = 63 ∧
    (allWorlds.filter fun w => decide (costOf w < inf)).length = 512 ∧
    allWorlds.foldl (fun a w => max a (costOf w)) 0 = 30 ∧
    allWorlds.foldl (fun a w => max a (planOf w).length) 0 = 12 := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> native_decide

end ReachPlan
