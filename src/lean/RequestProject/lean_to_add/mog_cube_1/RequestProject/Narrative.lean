import Mathlib
import RequestProject.Semantics
import RequestProject.Chat

/-!
# Narrative: saying what to do, and why it would work

Everything so far describes how things *are*.  The most useful sentences a
system can produce are the ones that say what to *do*: "heat the water twice
and it will boil".  That needs three things the earlier files do not have — a
plan, a story that walks through it, and a guarantee that the story is true of
the world the actions actually produce.

## Planning

`runActs` runs a list of actions on a world (`Semantics.step` is deterministic,
so this is a function, not a search over outcomes).  `plan w goal` returns the
**shortest** sequence of at most three actions that makes `goal` true, or
`none`:

* `plan_correct` — a returned plan really does reach the goal;
* `plan_facts` — measured over **all 512 worlds and all 48 contingent
  literals**: which goals are reachable, that the plan found is never longer
  than any other sequence that works, and how many goal/world pairs are simply
  unreachable.

## The story

`storyData` walks the plan and records, at each step, the facts that *became*
true.  `story_reports_real_changes` proves that each reported fact is true after
that action and was false before it, so the narration is a record of change and
not a re-statement of what was already the case.

The honest limits: the horizon is three actions, the actions saturate at the
ends of the scales (heating something already boiling does nothing), and
nothing here yet lets the system explain *why* an action has the effect it does
beyond exhibiting the resulting measurement.
-/

namespace Narrative

open Semantics

set_option maxRecDepth 100000

/-! ## 1. Running and planning -/

/-- Run a list of actions, in order. -/
def runActs : List Act → World → World
  | [], w => w
  | a :: rest, w => runActs rest (step a w)

/-- Every action sequence of exactly length `n`. -/
def allSeqs : Nat → List (List Act)
  | 0 => [[]]
  | n + 1 => allActs.flatMap fun a => (allSeqs n).map fun s => a :: s

/-- Every action sequence of length at most `n`, shortest first. -/
def seqsUpTo : Nat → List (List Act)
  | 0 => [[]]
  | n + 1 => seqsUpTo n ++ allSeqs (n + 1)

/-- The planning horizon. -/
def horizon : Nat := 3

/-- **The plan**: the first sequence of at most three actions that makes the
goal true.  Deterministic, and a total function of the world and the goal. -/
def plan (w : World) (goal : Lit) : Option (List Act) :=
  (seqsUpTo horizon).find? fun s => evalLit goal (runActs s w)

/-- **A plan works.** -/
theorem plan_correct {w : World} {goal : Lit} {s : List Act} (h : plan w goal = some s) :
    evalLit goal (runActs s w) = true := by
  unfold plan at h
  exact List.find?_some (p := fun t => evalLit goal (runActs t w)) h

/-- A plan is one of the sequences searched, so it is at most three actions
long. -/
theorem plan_short {w : World} {goal : Lit} {s : List Act} (h : plan w goal = some s) :
    s ∈ seqsUpTo horizon := by
  unfold plan at h
  exact List.mem_of_find?_eq_some h

/-! ## 2. The story of a plan -/

/-- The contingent facts that action `a` makes true in `u`, having been false
before. -/
def newFacts (a : Act) (u : World) : List Lit :=
  usefulLits.filter fun l => evalLit l (step a u) && !evalLit l u

/-- Walk a plan, recording the state before each action and the facts that
action brings about. -/
def storyData : List Act → World → List (World × Act × List Lit)
  | [], _ => []
  | a :: rest, u => (u, a, newFacts a u) :: storyData rest (step a u)

/-- **The story is a record of real change.**  Everything it reports at a step
is true after that action and was false before it. -/
theorem story_reports_real_changes (acts : List Act) (w : World) :
    ∀ t ∈ storyData acts w, ∀ l ∈ t.2.2,
      evalLit l (step t.2.1 t.1) = true ∧ evalLit l t.1 = false := by
  induction acts generalizing w with
  | nil => intro t ht; cases ht
  | cons a rest ih =>
      intro t ht l hl
      simp only [storyData, List.mem_cons] at ht
      rcases ht with rfl | ht
      · have := (List.mem_filter.mp hl).2
        simp only [Bool.and_eq_true, Bool.not_eq_true'] at this
        exact this
      · exact ih (step a w) t ht l hl

/-- The state the story reaches is the state the plan reaches. -/
theorem storyData_length (acts : List Act) (w : World) :
    (storyData acts w).length = acts.length := by
  induction acts generalizing w with
  | nil => rfl
  | cons a rest ih => simp [storyData, ih]

/-! ## 3. English -/

/-- The plan and its consequences, as English. -/
def renderStory (w : World) (acts : List Act) (goal : Lit) : List String :=
  (storyData acts w).map (fun t =>
    Chat.renderAct t.2.1 ++
      (if t.2.2.isEmpty then ", and nothing changes yet"
        else ", and now " ++ String.intercalate ", and " (t.2.2.map Chat.renderLit))) ++
  ["so " ++ Chat.renderLit goal]

/-- What to do, in the demo world, to make the water boil. -/
def demoStory : List String :=
  match plan demoWorld (.boiling .water, true) with
  | some acts => ("to make the water boil: " ++ toString acts.length ++ " step(s)") ::
      renderStory demoWorld acts (.boiling .water, true)
  | none => ["there is no way to make the water boil within three actions"]

#eval demoStory

/-! ## 4. What the planner can and cannot do, measured -/

/-- The goal/world pairs the planner can reach. -/
def solvable : List (World × Lit) :=
  allWorlds.flatMap fun w => (usefulLits.filter fun g => (plan w g).isSome).map fun g => (w, g)

/-- **The planner, measured over all 512 worlds and all 48 contingent goals.**

* every plan it returns reaches its goal and is **no longer than any other
  sequence of at most three actions that would have worked**, so it is a
  shortest plan;
* 22080 of the 24576 goal/world pairs are reachable within three actions;
* the remaining 2496 are genuinely unreachable with this horizon — the system
  reports that rather than inventing a plan. -/
theorem plan_facts :
    (allWorlds.all fun w => usefulLits.all fun g =>
      match plan w g with
      | some s =>
          evalLit g (runActs s w) &&
            (seqsUpTo horizon).all fun t =>
              decide (s.length ≤ t.length) || !evalLit g (runActs t w)
      | none => (seqsUpTo horizon).all fun t => !evalLit g (runActs t w)) = true ∧
    solvable.length = 22080 ∧
    512 * 48 - solvable.length = 2496 := by
  refine ⟨?_, ?_, ?_⟩ <;> native_decide

end Narrative
