/-
# The reasoning loop, and what its verification gate does and does not buy

The archive's ARC experiments run a cognitive cycle rather than a solver
pipeline: *perceive → goal → gap → propose → inspect*, with the inspection step
described as "a hard gate, sacred" — a proposal is returned only if it
reproduces every training pair.  That architecture is the part of the old ARC
work most worth carrying into the current system, and this file states what it
guarantees, in a form that is independent of grids, colours and ARC itself.

Two properties, and one limit.

* `solve_sound` — **the gate holds.**  Whatever the proposer offers and in
  whatever order, a returned candidate has passed verification on every training
  pair.  The loop cannot return an unchecked answer.
* `solve_eq_none_iff` — **refusal is exactly the absence of a passing
  candidate**, so a `none` is informative: it says the pool was searched and
  nothing verified.  This is the same asymmetry the current evaluation harness
  scores by, where a refusal costs less than a confident wrong answer.
* `gate_not_sufficient` — **and the limit, stated as a theorem rather than a
  caveat.**  Two candidates can agree on every training pair and disagree on the
  test input, so passing the gate does not determine the answer.  Enlarging the
  candidate pool therefore cannot be free: `FitCapacity.fit_capacity` is the
  quantitative form of the same warning.

Then the loop itself:

* `loop_terminates` — if each pass strictly decreases a `ℕ`-valued gap whenever
  the gap is nonzero, iterating reaches gap zero in finitely many passes;
* `loop_reaches_zero_gap` — and the state it reaches has no gap left.

Nothing here assumes the gap is a good measure of progress: that is the
modelling choice the architecture makes, and these theorems say exactly what
follows from it once it is made.
-/
import Mathlib

namespace GLM.ReasoningLoop

variable {Obj : Type*} [DecidableEq Obj]

/-- A candidate transformation: the loop's `PROPOSE` step offers these. -/
abbrev Cand (Obj : Type*) := Obj → Obj

/-- `Verifies f train`: the candidate reproduces every training pair.  This is
the `INSPECT` gate. -/
def Verifies (f : Cand Obj) (train : List (Obj × Obj)) : Prop :=
  ∀ p ∈ train, f p.1 = p.2

instance (f : Cand Obj) (train : List (Obj × Obj)) : Decidable (Verifies f train) := by
  unfold Verifies; infer_instance

/-- The loop: take the first proposal that passes the gate, and refuse if none
does. -/
def solve (cands : List (Cand Obj)) (train : List (Obj × Obj)) : Option (Cand Obj) :=
  cands.find? (fun f => decide (Verifies f train))

/-- **The gate holds.**  A returned candidate has passed verification on every
training pair. -/
theorem solve_sound {cands : List (Cand Obj)} {train : List (Obj × Obj)} {f : Cand Obj}
    (h : solve cands train = some f) : Verifies f train := by
  have := List.find?_some h
  simpa using this

/-- A returned candidate comes from the pool: the loop invents nothing. -/
theorem solve_mem {cands : List (Cand Obj)} {train : List (Obj × Obj)} {f : Cand Obj}
    (h : solve cands train = some f) : f ∈ cands :=
  List.mem_of_find?_eq_some h

/-- **Refusal is exactly the absence of a passing candidate.** -/
theorem solve_eq_none_iff {cands : List (Cand Obj)} {train : List (Obj × Obj)} :
    solve cands train = none ↔ ∀ f ∈ cands, ¬ Verifies f train := by
  unfold solve
  rw [List.find?_eq_none]
  constructor
  · intro h f hf hv
    exact absurd (decide_eq_true hv) (by simpa using h f hf)
  · intro h f hf
    simpa using fun hv => h f hf (of_decide_eq_true hv)

/-- If some candidate passes, the loop answers rather than refusing. -/
theorem solve_isSome_of_exists {cands : List (Cand Obj)} {train : List (Obj × Obj)}
    {f : Cand Obj} (hf : f ∈ cands) (hv : Verifies f train) : (solve cands train).isSome := by
  rcases h : solve cands train with _ | g
  · exact absurd hv (solve_eq_none_iff.1 h f hf)
  · rfl

/-! ## The limit of the gate -/

/-- **Passing the gate does not determine the answer.**  Two candidates agree on
every training pair and disagree on a test input, so verification on the training
set is a necessary condition and never a sufficient one. -/
theorem gate_not_sufficient :
    ∃ (train : List (ℕ × ℕ)) (f g : Cand ℕ) (test : ℕ),
      Verifies f train ∧ Verifies g train ∧ f test ≠ g test := by
  refine ⟨[(0, 0)], id, fun n => if n = 0 then 0 else 1, 2, ?_, ?_, ?_⟩
  · intro p hp
    simp at hp
    simp [hp]
  · intro p hp
    simp at hp
    simp [hp]
  · norm_num

/-! ## The loop itself -/

variable {State : Type*}

/-- **The loop terminates.**  If each pass strictly decreases the gap whenever
the gap is nonzero, then iterating reaches gap zero. -/
theorem loop_terminates (gap : State → ℕ) (step : State → State)
    (hdec : ∀ s, gap s ≠ 0 → gap (step s) < gap s) (s : State) :
    ∃ n : ℕ, gap (step^[n] s) = 0 := by
  generalize hk : gap s = k
  induction k using Nat.strong_induction_on generalizing s with
  | _ k ih =>
      rcases Nat.eq_zero_or_pos k with rfl | hpos
      · exact ⟨0, by simpa using hk⟩
      · have hne : gap s ≠ 0 := by omega
        obtain ⟨n, hn⟩ := ih (gap (step s)) (by rw [← hk]; exact hdec s hne) (step s) rfl
        exact ⟨n + 1, by rwa [Function.iterate_succ_apply]⟩

/-- The state the loop reaches has no gap left: the exit condition is the goal,
not a step budget. -/
theorem loop_reaches_zero_gap (gap : State → ℕ) (step : State → State)
    (hdec : ∀ s, gap s ≠ 0 → gap (step s) < gap s) (s : State) :
    ∃ t : State, (∃ n : ℕ, t = step^[n] s) ∧ gap t = 0 := by
  obtain ⟨n, hn⟩ := loop_terminates gap step hdec s
  exact ⟨step^[n] s, ⟨n, rfl⟩, hn⟩

/-- A loop that reduces the gap by at least one per pass finishes within
`gap s` passes. -/
theorem loop_bounded (gap : State → ℕ) (step : State → State)
    (hdec : ∀ s, gap s ≠ 0 → gap (step s) < gap s) (s : State) :
    ∃ n ≤ gap s, gap (step^[n] s) = 0 := by
  generalize hk : gap s = k
  induction k using Nat.strong_induction_on generalizing s with
  | _ k ih =>
      rcases Nat.eq_zero_or_pos k with rfl | hpos
      · exact ⟨0, by simp, by simpa using hk⟩
      · have hne : gap s ≠ 0 := by omega
        have hlt : gap (step s) < k := by rw [← hk]; exact hdec s hne
        obtain ⟨n, hnle, hn⟩ := ih (gap (step s)) hlt (step s) rfl
        refine ⟨n + 1, by omega, ?_⟩
        rwa [Function.iterate_succ_apply]

end GLM.ReasoningLoop
