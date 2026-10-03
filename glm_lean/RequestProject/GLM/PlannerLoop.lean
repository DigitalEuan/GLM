module

public import Mathlib

/-!
# The loop through the planner: programs that call the rest of the machine

The formal half of `studies/PLANNER_LOOP_STUDY.md` (Phase 88,
`glm_universal.runtime.planner_bridge`). A dialect program may call
`derive`, `ask` and `solve`; each call goes to another surface, which answers
with a value or refuses. The program's column-3 script does not call those
surfaces again: it re-runs each answer's own script, writes the checked
answers into a table, and re-runs the program against the table. These are
the facts that make that sound.

A program is modelled as a tree that either returns a value or calls an
oracle at a key and continues with the answer (`Prog`); `run` evaluates it
against an oracle `K → Option V` (`none` is a refusal), and `asked` lists the
keys the run asks, in order, up to the end or the first refusal.

* `run_eq_of_agree` — a table that agrees with the oracle at every key the
  run asks gives the same verdict: column 3's table is enough.
* `run_restrict` — in particular, the oracle restricted to the asked keys
  (and refusing everywhere else) gives the same verdict.
* `isSome_of_run_eq_some` — an answered run had an answer at every key it
  asked: no answer rests on a refused call.
* `run_eq_none_of_refused` — a refusal at any key the run asks is the run's
  refusal: a surface's refusal reaches the program by name, never as a
  partial answer.
* `affine_root_unique`, `affine_slope_ne_zero` — the binding check of a
  solved value: an affine function whose values at 0 and 1 differ has
  non-zero slope, and then at most one root.
* `least_resistance_thirteen` — the declared loop `l02`: 13 is the least
  whole resistance `r ≥ 1` with `12 / r < 1`.
-/

@[expose] public section

namespace GLM.PlannerLoop

/-- A program that may call the rest of the machine. -/
inductive Prog (K V : Type) where
  | ret : V → Prog K V
  | call : K → (V → Prog K V) → Prog K V

variable {K V : Type}

/-- Run a program against an oracle; `none` is a refusal. -/
def run (o : K → Option V) : Prog K V → Option V
  | .ret v => some v
  | .call k f => (o k).bind fun v => run o (f v)

/-- The keys a run asks, in order, up to its end or its first refusal. -/
def asked (o : K → Option V) : Prog K V → List K
  | .ret _ => []
  | .call k f =>
      k :: (match o k with
        | some v => asked o (f v)
        | none => [])

/-- **Column 3's table is enough.** A table that agrees with the oracle at
every key the run asks gives the same verdict. -/
theorem run_eq_of_agree (o t : K → Option V) :
    ∀ p : Prog K V, (∀ k ∈ asked o p, t k = o k) → run t p = run o p
  | .ret _, _ => rfl
  | .call k f, h => by
      have hk : t k = o k := h k (by simp [asked])
      simp only [run, hk]
      cases hok : o k with
      | none => rfl
      | some v =>
          simp only [Option.bind_some]
          apply run_eq_of_agree o t (f v)
          intro k' hk'
          exact h k' (by simp [asked, hok, hk'])

/-- The oracle restricted to the keys the run asks gives the same verdict. -/
theorem run_restrict [DecidableEq K] (o : K → Option V) (p : Prog K V) :
    run (fun k => if k ∈ asked o p then o k else none) p = run o p :=
  run_eq_of_agree o _ p (fun k hk => by simp [hk])

/-- **No answer rests on a refused call.** -/
theorem isSome_of_run_eq_some (o : K → Option V) :
    ∀ (p : Prog K V) (v : V), run o p = some v →
      ∀ k ∈ asked o p, (o k).isSome
  | .ret _, _, _, k, hk => by simp [asked] at hk
  | .call k f, v, h, k', hk' => by
      cases hok : o k with
      | none => simp [run, hok] at h
      | some w =>
          simp only [asked, hok, List.mem_cons] at hk'
          rcases hk' with rfl | hk'
          · simp [hok]
          · simp only [run, hok, Option.bind_some] at h
            exact isSome_of_run_eq_some o (f w) v h k' hk'

/-- **A refusal at an asked key is the run's refusal.** -/
theorem run_eq_none_of_refused (o : K → Option V) (p : Prog K V) (k : K)
    (hk : k ∈ asked o p) (hno : o k = none) : run o p = none := by
  cases h : run o p with
  | none => rfl
  | some v =>
      have := isSome_of_run_eq_some o p v h k hk
      simp [hno] at this

/-- An affine function whose values at `0` and `1` differ has non-zero
slope. -/
theorem affine_slope_ne_zero (a b : ℚ) (h : a * 1 + b ≠ a * 0 + b) :
    a ≠ 0 := by
  rintro rfl
  simp at h

/-- **A solved value is the only one.** An affine function with non-zero
slope has at most one root. -/
theorem affine_root_unique (a b v w : ℚ) (ha : a ≠ 0)
    (hv : a * v + b = 0) (hw : a * w + b = 0) : v = w := by
  have : a * (v - w) = 0 := by linarith
  rcases mul_eq_zero.mp this with h | h
  · exact absurd h ha
  · linarith

/-- An affine function has zero second difference — the check column 3
makes at `0, 1, 2`. -/
theorem affine_second_difference (a b : ℚ) :
    (a * 2 + b) - 2 * (a * 1 + b) + (a * 0 + b) = 0 := by ring

/-- **The declared loop `l02`.** 13 is the least whole resistance `r ≥ 1`
for which the current `12 / r` at 12 volts is below one ampere. -/
theorem least_resistance_thirteen :
    (12 : ℚ) / 13 < 1 ∧ ∀ r : ℕ, 1 ≤ r → r < 13 → 1 ≤ (12 : ℚ) / r := by
  refine ⟨by norm_num, fun r h1 h2 => ?_⟩
  have hr : (0 : ℚ) < r := by exact_mod_cast h1
  have hr12 : (r : ℚ) ≤ 12 := by exact_mod_cast Nat.lt_succ_iff.mp h2
  rw [le_div_iff₀ hr]
  linarith

end GLM.PlannerLoop
