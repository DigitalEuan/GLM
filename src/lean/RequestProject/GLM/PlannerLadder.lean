module

public import RequestProject.GLM.OperationsLadder

/-!
# The operations ladder in the planner (Phase 151)

The formal half of `studies/PLANNER_LADDER_STUDY.md`. Phase 125 built GLM-BAT,
a small batch machine, and the DevOps ladder it grounds; until this round they
were reached only through `tool ladder` and `tool machine`. This round gives
the stepwise planner the ladder's vocabulary: every step of a chain is said as
GLM-BAT lines, the machine runs the program, **drift** (the steps whose
machine value differs from the value the planner claims) is a planner check,
and the program runs as a pipeline with **rollback**, so a chain is admitted
all or nothing. This file proves what those checks rest on.

* `Rep`, `rep_int`, `rep_add`, `rep_sub`, `rep_mul`, `rep_div` — GLM-BAT's
  `SET /A` is integer arithmetic, so a rational step value is carried as a
  numerator and a nonzero denominator; the four operations on pairs represent
  the four operations on the rationals.
* `rep_check_iff` — the machine's drift check, a cross-multiplication
  `N * q - D * p = 0`, holds exactly when the represented value is `p / q`.
* `machine_eq_honest` — if every computed step depends only on earlier steps,
  and every carried step (a register value, a given) carries the honest value,
  the machine's values are the honest chain's, step for step.
* `drift_eq_lies`, `no_drift_iff` — so the drift is exactly the set of steps
  whose claimed value is not the honest one: every lie at a computed step is
  found at its own step and nowhere else, and no drift means the chain is
  honest.
* `rollback_journal` — writing a list of files and then restoring the journal
  of their old contents, newest first, gives back the files as they were: a
  stage that stops part-way leaves nothing behind.
* `promoted_iff_no_drift` — the pipeline with one gate per step promotes
  exactly when no step drifts (`promoted_iff_all_pass`).
-/

@[expose] public section

namespace GLM.PlannerLadder

open GLM.OperationsLadder

/-! ## Rationals as integer pairs -/

/-- The pair `(n, d)` of integers represents the rational `x`. -/
def Rep (n d : ℤ) (x : ℚ) : Prop := d ≠ 0 ∧ (n : ℚ) / d = x

theorem rep_int (p q : ℤ) (hq : q ≠ 0) : Rep p q ((p : ℚ) / q) := ⟨hq, rfl⟩

theorem rep_add {a b c d : ℤ} {x y : ℚ} (hx : Rep a b x) (hy : Rep c d y) :
    Rep (a * d + c * b) (b * d) (x + y) := by
  obtain ⟨hb, rfl⟩ := hx
  obtain ⟨hd, rfl⟩ := hy
  refine ⟨mul_ne_zero hb hd, ?_⟩
  have hb' : (b : ℚ) ≠ 0 := by exact_mod_cast hb
  have hd' : (d : ℚ) ≠ 0 := by exact_mod_cast hd
  push_cast
  field_simp

theorem rep_sub {a b c d : ℤ} {x y : ℚ} (hx : Rep a b x) (hy : Rep c d y) :
    Rep (a * d - c * b) (b * d) (x - y) := by
  obtain ⟨hb, rfl⟩ := hx
  obtain ⟨hd, rfl⟩ := hy
  refine ⟨mul_ne_zero hb hd, ?_⟩
  have hb' : (b : ℚ) ≠ 0 := by exact_mod_cast hb
  have hd' : (d : ℚ) ≠ 0 := by exact_mod_cast hd
  push_cast
  field_simp

theorem rep_mul {a b c d : ℤ} {x y : ℚ} (hx : Rep a b x) (hy : Rep c d y) :
    Rep (a * c) (b * d) (x * y) := by
  obtain ⟨hb, rfl⟩ := hx
  obtain ⟨hd, rfl⟩ := hy
  refine ⟨mul_ne_zero hb hd, ?_⟩
  push_cast
  rw [mul_div_mul_comm]

/-- Division needs a nonzero divisor, which for a pair is a nonzero numerator:
the machine tests it before the line, and refuses where the planner refuses. -/
theorem rep_div {a b c d : ℤ} {x y : ℚ} (hx : Rep a b x) (hy : Rep c d y)
    (hc : c ≠ 0) : Rep (a * d) (b * c) (x / y) := by
  obtain ⟨hb, rfl⟩ := hx
  obtain ⟨hd, rfl⟩ := hy
  refine ⟨mul_ne_zero hb hc, ?_⟩
  have hb' : (b : ℚ) ≠ 0 := by exact_mod_cast hb
  have hd' : (d : ℚ) ≠ 0 := by exact_mod_cast hd
  have hc' : (c : ℚ) ≠ 0 := by exact_mod_cast hc
  push_cast
  field_simp

/-- **The drift check.** A pair represents `p / q` exactly when the machine's
cross-multiplication `n * q - d * p` is zero. -/
theorem rep_check_iff {n d p q : ℤ} {x : ℚ} (hx : Rep n d x) (hq : q ≠ 0) :
    n * q - d * p = 0 ↔ x = (p : ℚ) / q := by
  obtain ⟨hd, rfl⟩ := hx
  have hd' : (d : ℚ) ≠ 0 := by exact_mod_cast hd
  have hq' : (q : ℚ) ≠ 0 := by exact_mod_cast hq
  rw [div_eq_div_iff hd' hq', sub_eq_zero]
  constructor
  · intro h
    have := congrArg (fun z : ℤ => (z : ℚ)) h
    push_cast at this
    linarith
  · intro h
    have h' : ((n * q : ℤ) : ℚ) = ((p * d : ℤ) : ℚ) := by push_cast; linarith
    have := Int.cast_injective h'
    linarith

/-! ## The machine against the chain -/

section Chain

variable {V : Type*}

/-- A step function depends only on the values of earlier steps. -/
def Causal (f : ℕ → (ℕ → V) → V) : Prop :=
  ∀ k (v w : ℕ → V), (∀ i < k, v i = w i) → f k v = f k w

/-- The machine's values: a computed step is computed from the machine's own
earlier values; a carried step takes the value the planner claims. -/
def MachineEq (comp : ℕ → Prop) [DecidablePred comp] (f : ℕ → (ℕ → V) → V)
    (claimed m : ℕ → V) : Prop :=
  ∀ k, m k = if comp k then f k m else claimed k

/-- **The machine recomputes the honest chain.** If the computed steps are
causal and every carried step carries the honest value, the machine's value is
the honest value at every step. -/
theorem machine_eq_honest {comp : ℕ → Prop} [DecidablePred comp]
    {f : ℕ → (ℕ → V) → V} {claimed m h : ℕ → V} (hf : Causal f)
    (hm : MachineEq comp f claimed m) (hh : ∀ k, comp k → h k = f k h)
    (hcar : ∀ k, ¬ comp k → claimed k = h k) : m = h := by
  funext k
  induction k using Nat.strong_induction_on with
  | _ k ih =>
    rw [hm k]
    split_ifs with hk
    · rw [hh k hk]
      exact hf k m h ih
    · exact hcar k hk

/-- **Drift is exactly the lies.** Under the same conditions, a step drifts
(its machine value differs from its claimed value) exactly when its claimed
value is not the honest one. -/
theorem drift_eq_lies {comp : ℕ → Prop} [DecidablePred comp]
    {f : ℕ → (ℕ → V) → V} {claimed m h : ℕ → V} (hf : Causal f)
    (hm : MachineEq comp f claimed m) (hh : ∀ k, comp k → h k = f k h)
    (hcar : ∀ k, ¬ comp k → claimed k = h k) :
    {k | m k ≠ claimed k} = {k | claimed k ≠ h k} := by
  rw [machine_eq_honest hf hm hh hcar]
  ext k
  exact ⟨fun hne e => hne e.symm, fun hne e => hne e.symm⟩

/-- **No drift means an honest chain**, and conversely. -/
theorem no_drift_iff {comp : ℕ → Prop} [DecidablePred comp]
    {f : ℕ → (ℕ → V) → V} {claimed m h : ℕ → V} (hf : Causal f)
    (hm : MachineEq comp f claimed m) (hh : ∀ k, comp k → h k = f k h)
    (hcar : ∀ k, ¬ comp k → claimed k = h k) :
    (∀ k, m k = claimed k) ↔ claimed = h := by
  rw [machine_eq_honest hf hm hh hcar]
  exact ⟨fun hall => funext fun k => (hall k).symm, fun he k => he ▸ rfl⟩

end Chain

/-! ## Rollback by journal -/

section Journal

variable {K V : Type*} [DecidableEq K]

/-- Write each `(file, content)` in order. -/
def writeAll : (K → V) → List (K × V) → (K → V)
  | fs, [] => fs
  | fs, (k, v) :: r => writeAll (Function.update fs k v) r

/-- The journal of old contents a run of writes keeps, newest first. -/
def journal : (K → V) → List (K × V) → List (K × V)
  | _, [] => []
  | fs, (k, v) :: r => journal (Function.update fs k v) r ++ [(k, fs k)]

theorem writeAll_append (fs : K → V) (a b : List (K × V)) :
    writeAll fs (a ++ b) = writeAll (writeAll fs a) b := by
  induction a generalizing fs with
  | nil => rfl
  | cons p a ih =>
    obtain ⟨k, v⟩ := p
    exact ih _

/-- **Rollback restores.** Restoring the journal after the writes gives back
the files as they were, however many writes the stage made before it
stopped. -/
theorem rollback_journal (fs : K → V) (ws : List (K × V)) :
    writeAll (writeAll fs ws) (journal fs ws) = fs := by
  induction ws generalizing fs with
  | nil => rfl
  | cons p r ih =>
    obtain ⟨k, v⟩ := p
    simp only [writeAll, journal]
    rw [writeAll_append, ih]
    simp [writeAll]

end Journal

/-- **The pipeline promotes exactly when no step drifts**: one gate per step,
passing when the machine's value is the claimed one. -/
theorem promoted_iff_no_drift {V : Type*} [DecidableEq V] (m claimed : ℕ → V)
    (steps : List ℕ) :
    runPipeline (steps.map fun k => decide (m k = claimed k)) = true ↔
      ∀ k ∈ steps, m k = claimed k := by
  rw [promoted_iff_all_pass]
  simp

end GLM.PlannerLadder
