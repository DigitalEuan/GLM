module

public import RequestProject.GLM.OperationsLadder

/-!
# Inert variables: a non-termination certificate past the control state (Phase 126)

The formal half of `studies/INERT_COUNTER_STUDY.md`
(`glm_universal.reasoning.batch_machine.inert_variables`).

GLM-BAT's first certificate of non-termination (Phase 125) is a recurring
control state. A loop whose counter grows (`SET /A N=N+1 / GOTO UP`) never
repeats one, because the counter is part of the state. But the counter is
*inert*: no instruction reads it except to update an inert variable, and no
such update can fail. Split the state into the part that is read and the inert
store; then the next read part and whether the machine halts are functions of
the read part alone, and a recurrence of the read part is a proof that the
machine never halts.

* `inert_step_commutes` — under that split, forgetting the inert store
  commutes with the step;
* `never_halts_of_inert_repeat` — so a recurrence of the read part, whatever
  the inert store holds, proves non-termination;
* `inert_run_fst` — the read part of a run is the run of the read part, so
  the certificate the machine finds on the forgetful run is about the real one.
-/

@[expose] public section

namespace GLM.InertCounter

open GLM.OperationsLadder

variable {C X : Type*}

/-- A machine whose state is a read part `C` and an inert store `X`: the next
read part, and whether there is one, depend on the read part only; the inert
store is updated from both. -/
def inertStep (stepC : C → Option C) (upd : C → X → X) : C × X → Option (C × X) :=
  fun s => (stepC s.1).map (fun c' => (c', upd s.1 s.2))

theorem inert_step_commutes (stepC : C → Option C) (upd : C → X → X) (s : C × X) :
    (inertStep stepC upd s).map Prod.fst = stepC s.1 := by
  simp only [inertStep, Option.map_map]
  cases stepC s.1 <;> rfl

theorem inert_run_fst (stepC : C → Option C) (upd : C → X → X) (n : ℕ) (s : C × X) :
    (run (inertStep stepC upd) n s).map Prod.fst = run stepC n s.1 :=
  run_map _ _ Prod.fst (inert_step_commutes stepC upd) n s

/-- **The certificate.** If the read part at step `i` recurs at step `j > i`,
the machine never halts, whatever the inert store holds. -/
theorem never_halts_of_inert_repeat (stepC : C → Option C) (upd : C → X → X)
    (c : C) (x : X) (d : C) {i j : ℕ} (hij : i < j)
    (hi : run stepC i c = some d) (hj : run stepC j c = some d) :
    ¬ Halts (inertStep stepC upd) (c, x) :=
  never_halts_of_projected_repeat _ stepC Prod.fst (inert_step_commutes stepC upd)
    (c, x) d hij hi hj

end GLM.InertCounter
