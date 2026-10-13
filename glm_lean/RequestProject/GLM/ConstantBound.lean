module

public import RequestProject.GLM.CounterLasso
import all RequestProject.GLM.CounterLasso

/-!
# Constant bounds and repeated output: two more counter lassos (Phase 131)

The formal half of `studies/CONSTANT_BOUND_STUDY.md`
(`glm_universal.reasoning.batch_machine.jumped_run`, the extended reading).

Phase 130 (`GLM.CounterLasso`) jumps a pass of a loop whose counters come back
translated, but refuses two kinds of pass that halt:

    SET /A N=0 / :UP / SET /A N=N+1 / ECHO tick / IF %N% LSS 20000 GOTO UP
    SET /A N=0 / SET L=20000 / :UP / SET /A N=N+1 / IF %N% LSS %L% GOTO UP

The first writes a line on every pass, so a jump must say what the skipped
passes wrote; the second compares the counter with a variable that is not a
counter. Both are read here.

* **Repeated output.** `wrun` is `run` with the lines each step writes
  collected. If what a step writes does not read the counters
  (`emit (shift v s) = emit s` along the pass), then `K` passes write the
  first pass's block `K` times over: `wrun_pass`, `lasso_output`, and with a
  run in and out of the passes, `halts_of_jump_output`. `wrun_fst` says the
  collected run is the plain run with its output forgotten.
* **Constant bounds.** A test may read the part `C` of the state as well as
  the counters (`testStepC`); it commutes with a translation exactly while its
  outcome is unchanged (`testC_equivariant`). A translation never moves the
  part `C` (`shift_fst`), so a bound read from `C` at step `r` of a pass is the
  same at step `r` of every later pass, and the comparison of a counter with
  it is the linear form `e₀ + b·m` of Phase 130 with the bound folded into
  `e₀` (`const_bound_linear`).
-/

@[expose] public section

namespace GLM.ConstantBound

open GLM.OperationsLadder GLM.CounterLasso

/-! ## A run that collects what it writes -/

section Writer

variable {S O : Type*}

/-- Run `n` steps, collecting the lines `emit s` written by each step from
`s`; `none` once the machine has halted. -/
def wrun (step : S → Option S) (emit : S → List O) : ℕ → S → Option (S × List O)
  | 0, s => some (s, [])
  | n + 1, s => (step s).bind fun t => (wrun step emit n t).map fun r => (r.1, emit s ++ r.2)

/-- The collected run is the plain run with its output forgotten. -/
theorem wrun_fst (step : S → Option S) (emit : S → List O) (n : ℕ) (s : S) :
    (wrun step emit n s).map Prod.fst = run step n s := by
  induction n generalizing s with
  | zero => rfl
  | succ n ih =>
    simp only [wrun, run]
    cases step s with
    | none => rfl
    | some t =>
      simp only [Option.bind_some, Option.map_map]
      rw [← ih t]
      rfl

/-- Two runs in a row write what the first wrote, then what the second wrote. -/
theorem wrun_add (step : S → Option S) (emit : S → List O) (m n : ℕ) (s : S) :
    wrun step emit (m + n) s = (wrun step emit m s).bind fun r =>
      (wrun step emit n r.1).map fun q => (q.1, r.2 ++ q.2) := by
  induction m generalizing s with
  | zero =>
    simp only [Nat.zero_add, wrun, Option.bind_some, List.nil_append]
    cases wrun step emit n s <;> rfl
  | succ m ih =>
    rw [Nat.succ_add]
    simp only [wrun]
    cases step s with
    | none => rfl
    | some t =>
      simp only [Option.bind_some]
      rw [ih t]
      cases wrun step emit m t with
      | none => rfl
      | some r =>
        simp only [Option.bind_some, Option.map_some]
        cases wrun step emit n r.1 <;> simp

end Writer

/-! ## A pass that writes, repeated -/

section Pass

variable {C ι O : Type*}

/-- The lines one pass `path 0 → … → path p` writes. -/
def block (emit : C × (ι → ℤ) → List O) (path : ℕ → C × (ι → ℤ)) (p : ℕ) : List O :=
  ((List.range p).map fun r => emit (path r)).flatten

theorem block_succ (emit : C × (ι → ℤ) → List O) (path : ℕ → C × (ι → ℤ)) (p : ℕ) :
    block emit path (p + 1) = block emit path p ++ emit (path p) := by
  simp [block, List.range_succ]

/-- **One pass, with its output.** From the start translated by `m • d`, a
pass whose steps commute with that translation and whose written lines do not
read the counters ends at the start translated by `(m + 1) • d`, having
written exactly the first pass's block. -/
theorem wrun_pass (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (emit : C × (ι → ℤ) → List O) (path : ℕ → C × (ι → ℤ)) (p : ℕ) (d : ι → ℤ) (m : ℤ)
    (hclose : path p = shift d (path 0))
    (hequi : ∀ r < p, step (shift (m • d) (path r)) = some (shift (m • d) (path (r + 1))))
    (hemit : ∀ r < p, emit (shift (m • d) (path r)) = emit (path r)) :
    wrun step emit p (shift (m • d) (path 0)) =
      some (shift ((m + 1) • d) (path 0), block emit path p) := by
  have hr : ∀ r ≤ p, wrun step emit r (shift (m • d) (path 0)) =
      some (shift (m • d) (path r), block emit path r) := by
    intro r hrp
    induction r with
    | zero => rfl
    | succ r ih =>
      rw [wrun_add, ih (by omega), Option.bind_some]
      simp only [wrun, hequi r (by omega), Option.bind_some, Option.map_some,
        hemit r (by omega), List.append_nil, block_succ]
  rw [hr p le_rfl, hclose, shift_shift, add_smul, one_smul, add_comm d]

/-- **The jump, with its output.** `K` passes write the first pass's block `K`
times over and end at the start translated by `K • d`, in `K * p` steps. -/
theorem lasso_output (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (emit : C × (ι → ℤ) → List O) (path : ℕ → C × (ι → ℤ)) (p K : ℕ) (d : ι → ℤ)
    (hclose : path p = shift d (path 0))
    (hequi : ∀ m < K, ∀ r < p,
      step (shift ((m : ℤ) • d) (path r)) = some (shift ((m : ℤ) • d) (path (r + 1))))
    (hemit : ∀ m < K, ∀ r < p, emit (shift ((m : ℤ) • d) (path r)) = emit (path r)) :
    wrun step emit (K * p) (path 0) =
      some (shift ((K : ℤ) • d) (path 0), (List.replicate K (block emit path p)).flatten) := by
  induction K with
  | zero => simp [wrun]
  | succ K ih =>
    rw [Nat.succ_mul, wrun_add, ih (fun m hm => hequi m (by omega)) (fun m hm => hemit m (by omega)),
      Option.bind_some, wrun_pass step emit path p d K hclose (hequi K (by omega))
        (hemit K (by omega)), Option.map_some]
    simp [List.replicate_succ', List.flatten_append]

/-- **The halting certificate, with the output.** Run `i` steps to the start
of the pass writing `w₀`, jump `K` passes, and run `n` more steps writing `w₁`
to a state with no successor: the machine halts after exactly `i + K * p + n`
steps, having written `w₀`, then the pass's block `K` times, then `w₁`. -/
theorem halts_of_jump_output (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (emit : C × (ι → ℤ) → List O) (s₀ : C × (ι → ℤ)) (path : ℕ → C × (ι → ℤ))
    (i p K n : ℕ) (d : ι → ℤ) (t : C × (ι → ℤ)) (w₀ w₁ : List O)
    (hi : wrun step emit i s₀ = some (path 0, w₀))
    (hclose : path p = shift d (path 0))
    (hequi : ∀ m < K, ∀ r < p,
      step (shift ((m : ℤ) • d) (path r)) = some (shift ((m : ℤ) • d) (path (r + 1))))
    (hemit : ∀ m < K, ∀ r < p, emit (shift ((m : ℤ) • d) (path r)) = emit (path r))
    (hn : wrun step emit n (shift ((K : ℤ) • d) (path 0)) = some (t, w₁))
    (ht : step t = none) :
    wrun step emit (i + K * p + n) s₀ =
        some (t, w₀ ++ (List.replicate K (block emit path p)).flatten ++ w₁) ∧
      Halts step s₀ := by
  have h : wrun step emit (i + K * p + n) s₀ =
      some (t, w₀ ++ (List.replicate K (block emit path p)).flatten ++ w₁) := by
    rw [wrun_add, wrun_add, hi, Option.bind_some, lasso_output step emit path p K d hclose hequi hemit,
      Option.map_some, Option.bind_some, hn, Option.map_some]
  refine ⟨h, i + K * p + n, t, ?_, ht⟩
  have := congrArg (Option.map Prod.fst) h
  rwa [wrun_fst] at this

end Pass

/-! ## A test that reads a constant bound -/

section Bound

variable {C ι : Type*}

/-- A translation never moves the part of the state that is not a counter. -/
@[simp] theorem shift_fst (v : ι → ℤ) (s : C × (ι → ℤ)) : (shift v s).1 = s.1 := rfl

/-- `IF %N% OP %L% …`: a test on the counters *and* the rest of the state
chooses the next part of the state. -/
def testStepC (P : C → (ι → ℤ) → Prop) [∀ c, DecidablePred (P c)] (yes no : C → C)
    (s : C × (ι → ℤ)) : Option (C × (ι → ℤ)) :=
  some (if P s.1 s.2 then yes s.1 else no s.1, s.2)

/-- A test reading a bound from the rest of the state commutes with a
translation exactly when its outcome is unchanged by it. -/
theorem testC_equivariant (P : C → (ι → ℤ) → Prop) [∀ c, DecidablePred (P c)]
    (yes no : C → C) (v : ι → ℤ) (s : C × (ι → ℤ)) (h : P s.1 (s.2 + v) ↔ P s.1 s.2) :
    testStepC P yes no (shift v s) = (testStepC P yes no s).map (shift v) := by
  simp only [testStepC, shift, Option.map_some]
  by_cases hp : P s.1 s.2
  · rw [if_pos (h.mpr hp), if_pos hp]
  · rw [if_neg (fun h' => hp (h.mp h')), if_neg hp]

/-- **The bound folds into `e₀`.** At pass `m`, a counter `a` against a bound
`L` read from the rest of the state differs by `(x_a − L) + d_a · m`: the
linear form whose first change Phase 130 computes, with slope `d_a`. -/
theorem const_bound_linear (L : C → ℤ) (a : ι) (d : ι → ℤ) (m : ℤ) (s : C × (ι → ℤ)) :
    (shift (m • d) s).2 a - L (shift (m • d) s).1 = (s.2 a - L s.1) + d a * m := by
  simp only [shift, Pi.add_apply, Pi.smul_apply, smul_eq_mul]
  ring

/-- The same with the counter on the right: `L − x_a` has slope `−d_a`. -/
theorem const_bound_linear' (L : C → ℤ) (a : ι) (d : ι → ℤ) (m : ℤ) (s : C × (ι → ℤ)) :
    L (shift (m • d) s).1 - (shift (m • d) s).2 a = (L s.1 - s.2 a) + (-d a) * m := by
  simp only [shift, Pi.add_apply, Pi.smul_apply, smul_eq_mul]
  ring

end Bound

end GLM.ConstantBound
