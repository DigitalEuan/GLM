module

public import Mathlib

/-!
# The operations ladder: an old-style machine, and the ladder it grounds (Phase 125)

The formal half of `studies/OPERATIONS_LADDER_STUDY.md`
(`glm_universal.reasoning.ops_ladder`, `glm_universal.reasoning.batch_machine`).
The study turns the owner's DevOps ladder into a register of terms, each built
from lower ones, and its two lowest tiers into a small batch machine (GLM-BAT).
This file states what the Python relies on.

* `never_halts_of_repeat` — a deterministic machine whose state recurs never
  halts: the certificate the machine gives for a run that does not end.
* `never_halts_of_projected_repeat` — the same through a projection that
  commutes with the step: GLM-BAT forgets its output streams, which no
  instruction reads back, and a recurring *control* state is still a proof.
* `andThen_assoc`, `orElse_assoc` — `&&` and `||` over exit codes group either
  way, so the reader may group them left to right.
* `reconcile_idempotent`, `reconcile_no_drift`, `reconcile_eq_self_iff` —
  reconciling actual files to desired ones removes every drift, a second
  reconciliation changes nothing, and reconciliation is the identity exactly
  when there is no drift.
* `rollback_restores` — writing a file and then restoring its journaled old
  content gives back the files as they were.
* `layered_wf` — a composition relation along which a rank strictly decreases
  in a well-founded order has no infinite descending chain, so the ladder's
  closures are finite and every term grounds.
* `promoted_iff_all_pass` — a pipeline stopping at the first failed stage
  promotes exactly when every stage passed.
* `find_find`, `sort_sort` — `FIND "s" | FIND "s"` is `FIND "s"`, and
  `SORT | SORT` is `SORT`: two pipe filters are idempotent.
-/

public section

namespace GLM.OperationsLadder

/-! ## Deterministic machines and the certificate of non-termination -/

section Machine

variable {S T : Type*}

/-- Run a partial step function `n` times; `none` once the machine has halted. -/
def run (step : S → Option S) : ℕ → S → Option S
  | 0, s => some s
  | n + 1, s => (step s).bind (run step n)

/-- A machine halts from `s` when some run ends with no successor. -/
def Halts (step : S → Option S) (s : S) : Prop :=
  ∃ n t, run step n s = some t ∧ step t = none

theorem run_add (step : S → Option S) (m n : ℕ) (s : S) :
    run step (m + n) s = (run step m s).bind (run step n) := by
  induction m generalizing s with
  | zero => simp [run]
  | succ m ih =>
    rw [Nat.succ_add]
    simp only [run]
    cases h : step s with
    | none => simp
    | some t => simp [ih]

/-- If the state at step `i` recurs at a later step `j`, every run from `s`
is defined: the machine never halts. -/
theorem never_halts_of_repeat (step : S → Option S) (s u : S) {i j : ℕ}
    (hij : i < j) (hi : run step i s = some u) (hj : run step j s = some u) :
    ¬ Halts step s := by
  rintro ⟨n, t, hn, ht⟩
  -- every run of length `n` from `u` stays defined, by induction on blocks
  have hper : ∀ k, run step (i + k * (j - i)) s = some u := by
    intro k
    induction k with
    | zero => simpa using hi
    | succ k ih =>
      have : i + (k + 1) * (j - i) = (i + k * (j - i)) + (j - i) := by ring
      rw [this, run_add, ih]
      have hj' : run step (i + (j - i)) s = some u := by
        rwa [Nat.add_sub_cancel' hij.le]
      rw [run_add, hi] at hj'
      simpa using hj'
  -- take a block boundary beyond `n + 1`
  have hpos : 0 < j - i := Nat.sub_pos_of_lt hij
  obtain ⟨k, hk⟩ : ∃ k, n + 1 ≤ i + k * (j - i) :=
    ⟨n + 1, by nlinarith⟩
  obtain ⟨d, hd⟩ := Nat.exists_eq_add_of_le hk
  have h := hper k
  rw [hd, run_add, run_add, hn] at h
  simp [run, ht] at h

/-- A projection that commutes with the step carries runs to runs. -/
theorem run_map (step : S → Option S) (step' : T → Option T) (p : S → T)
    (hcomm : ∀ s, (step s).map p = step' (p s)) (n : ℕ) (s : S) :
    (run step n s).map p = run step' n (p s) := by
  induction n generalizing s with
  | zero => simp [run]
  | succ n ih =>
    simp only [run]
    rw [← hcomm s]
    cases step s with
    | none => simp
    | some t => simp [ih]

/-- **The certificate GLM-BAT gives.** If the projected (control) state at
step `i` recurs at step `j > i`, the full machine never halts, provided the
projection commutes with the step and the projected step is itself defined
exactly when the full one is (both facts hold for forgetting the output
streams). -/
theorem never_halts_of_projected_repeat (step : S → Option S)
    (step' : T → Option T) (p : S → T)
    (hcomm : ∀ s, (step s).map p = step' (p s)) (s : S) (c : T) {i j : ℕ}
    (hij : i < j) (hi : run step' i (p s) = some c)
    (hj : run step' j (p s) = some c) :
    ¬ Halts step s := by
  rintro ⟨n, t, hn, ht⟩
  have hn' : run step' n (p s) = some (p t) := by
    rw [← run_map step step' p hcomm, hn]; rfl
  have ht' : step' (p t) = none := by rw [← hcomm, ht]; rfl
  exact never_halts_of_repeat step' (p s) c hij hi hj ⟨n, p t, hn', ht'⟩

end Machine

/-! ## `&&` and `||` over exit codes -/

section ShortCircuit

variable {σ : Type*}

/-- A command: a state change and whether it succeeded. -/
abbrev Cmd (σ : Type*) := σ → σ × Bool

/-- `a && b`: run `b` only when `a` succeeded. -/
def andThen (a b : Cmd σ) : Cmd σ := fun s =>
  let r := a s
  if r.2 then b r.1 else (r.1, false)

/-- `a || b`: run `b` only when `a` failed. -/
def orElse (a b : Cmd σ) : Cmd σ := fun s =>
  let r := a s
  if r.2 then (r.1, true) else b r.1

theorem andThen_assoc (a b c : Cmd σ) :
    andThen (andThen a b) c = andThen a (andThen b c) := by
  funext s
  simp only [andThen]
  cases (a s).2 <;> simp

theorem orElse_assoc (a b c : Cmd σ) :
    orElse (orElse a b) c = orElse a (orElse b c) := by
  funext s
  simp only [orElse]
  cases (a s).2 <;> simp

end ShortCircuit

/-! ## Desired state, drift and reconciliation -/

section Reconcile

variable {K V : Type*}

/-- Write every desired file over the actual ones; files the desired state
does not name are left alone. -/
def reconcile (desired actual : K → Option V) : K → Option V := fun k =>
  match desired k with
  | some v => some v
  | none => actual k

/-- The drift: the desired files whose actual content differs or is missing. -/
def drift (desired actual : K → Option V) : Set K :=
  {k | ∃ v, desired k = some v ∧ actual k ≠ some v}

theorem reconcile_idempotent (desired actual : K → Option V) :
    reconcile desired (reconcile desired actual) = reconcile desired actual := by
  funext k
  simp only [reconcile]
  cases desired k <;> rfl

theorem reconcile_no_drift (desired actual : K → Option V) :
    drift desired (reconcile desired actual) = ∅ := by
  ext k
  simp only [drift, reconcile, Set.mem_setOf_eq, Set.mem_empty_iff_false,
    iff_false, not_exists, not_and, not_not]
  intro v hv
  simp [hv]

theorem reconcile_eq_self_iff (desired actual : K → Option V) :
    reconcile desired actual = actual ↔ drift desired actual = ∅ := by
  constructor
  · intro h
    rw [← h]
    exact reconcile_no_drift desired actual
  · intro h
    funext k
    simp only [reconcile]
    cases hk : desired k with
    | none => rfl
    | some v =>
      by_contra hne
      have : k ∈ drift desired actual := ⟨v, hk, fun e => hne e.symm⟩
      rw [h] at this
      exact this

end Reconcile

/-! ## Rollback -/

theorem rollback_restores {K V : Type*} [DecidableEq K] (fs : K → V) (k : K)
    (v : V) : Function.update (Function.update fs k v) k (fs k) = fs := by
  simp

/-! ## The ladder: layered compositions are well founded -/

/-- If every composition edge `r b a` ("`b` is a part of `a`") lowers a rank
in a well-founded order, the relation is well founded: there is no infinite
chain of parts, so every closure is finite and every term grounds. -/
theorem layered_wf {α β : Type*} {lt : β → β → Prop} (hwf : WellFounded lt)
    (r : α → α → Prop) (rank : α → β) (h : ∀ a b, r b a → lt (rank b) (rank a)) :
    WellFounded r :=
  Subrelation.wf (fun {b a} hr => h a b hr) (InvImage.wf rank hwf)

/-- The rank the register uses: `(tier, index)` in the lexicographic order. -/
theorem lex_rank_wf : WellFounded (fun x y : ℕ ×ₗ ℕ => x < y) :=
  wellFounded_lt

/-! ## Pipelines with gates -/

/-- Run stages in order; stop at the first failure.  The result is whether the
artifact is promoted. -/
def runPipeline : List Bool → Bool
  | [] => true
  | ok :: rest => if ok then runPipeline rest else false

theorem promoted_iff_all_pass (stages : List Bool) :
    runPipeline stages = true ↔ ∀ ok ∈ stages, ok = true := by
  induction stages with
  | nil => simp [runPipeline]
  | cons ok rest ih =>
    cases ok <;> simp [runPipeline, ih]

/-! ## Two pipe filters are idempotent -/

theorem find_find (p : String → Bool) (lines : List String) :
    (lines.filter p).filter p = lines.filter p := by
  simp [List.filter_filter]

theorem sort_sort (lines : List String) :
    (lines.mergeSort (fun a b => decide (a ≤ b))).mergeSort
        (fun a b => decide (a ≤ b)) =
      lines.mergeSort (fun a b => decide (a ≤ b)) := by
  apply List.mergeSort_of_pairwise
  exact List.pairwise_mergeSort (le := fun a b => decide (a ≤ b))
    (fun a b c hab hbc => by simpa using le_trans (by simpa using hab) (by simpa using hbc))
    (fun a b => by simpa using le_total a b) lines

end GLM.OperationsLadder
