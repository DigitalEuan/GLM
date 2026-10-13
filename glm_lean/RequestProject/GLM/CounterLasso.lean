module

public import RequestProject.GLM.OperationsLadder
import all RequestProject.GLM.OperationsLadder

/-!
# Counter lassos: halting and non-termination past the budget (Phase 130)

The formal half of `studies/COUNTER_LASSO_STUDY.md`
(`glm_universal.reasoning.batch_machine.accelerated_run`).

GLM-BAT's earlier certificates (Phases 125 and 126) are recurrences: a control
state, or what is left of it once the inert variables are forgotten, comes
back. A loop such as

    SET /A N=0 / :UP / SET /A N=N+1 / IF %N% LSS 20000 GOTO UP / ECHO done

repeats no such state, and halts only after 40,003 steps, past the machine's
budget. What does repeat is everything *except* the counters, and the counters
come back *translated*: one pass of the loop adds a fixed vector `d` to them.
Split the state into a part `C` and integer counters `ι → ℤ`. If every step
along one pass commutes with translating the counters by `m • d` — the steps
that do not read a counter always do, an update `x_i := x_i + k` always does,
and a comparison does exactly while its outcome is unchanged — then:

* `lasso_iterate`, `lasso_accelerate` — the pass can be repeated `K` times in
  one jump: the state after `K` passes is the start translated by `K • d`;
* `never_halts_of_lasso` — if it can be repeated for every `m`, the machine
  never halts (a recurrence is the case `d = 0`);
* `halts_of_jump` — if the machine halts from the translated state, it halts
  from the start, after exactly `i + K * p + n` steps;
* `indep_equivariant`, `add_equivariant`, `test_equivariant` — the three kinds
  of line the Python admits on a pass, and why each commutes with translation;
* `linear_neg_stable`, `linear_nonneg_stable`, `linear_zero_unique` — the
  outcome of a comparison `e₀ + b·m ⋈ 0` is the same at every `m` between two
  points where it agrees, for `<` and `≥`, and `= 0` holds at one `m` at most
  when `b ≠ 0`. This is why the Python may find the first pass at which a
  comparison changes from the endpoints alone.

The comparison that changes first is a linear ranking function for the loop:
`e₀ + b·m` crosses zero after a number of passes computed exactly, and the
jump replaces running those passes out.
-/

@[expose] public section

namespace GLM.CounterLasso

open GLM.OperationsLadder

variable {C ι : Type*}

/-- Translate the counters of a state by `v`. -/
def shift (v : ι → ℤ) (s : C × (ι → ℤ)) : C × (ι → ℤ) := (s.1, s.2 + v)

@[simp] theorem shift_zero (s : C × (ι → ℤ)) : shift 0 s = s := by
  simp [shift]

theorem shift_shift (u v : ι → ℤ) (s : C × (ι → ℤ)) :
    shift u (shift v s) = shift (v + u) s := by
  simp [shift, add_assoc]

theorem run_succ' {S : Type*} (step : S → Option S) (n : ℕ) (s : S) :
    run step (n + 1) s = (run step n s).bind step := by
  rw [run_add]
  cases run step n s with
  | none => rfl
  | some t =>
    simp only [Option.bind_some, run]
    cases step t <;> rfl

/-! ## One pass, repeated -/

/-- If every step of a pass `path 0 → … → path p` commutes with translating
the counters by `m • d` for every `m < K`, and the pass ends at the start
translated by `d`, then from the start translated by `m • d` the pass ends at
the start translated by `(m + 1) • d`. -/
theorem lasso_iterate (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (path : ℕ → C × (ι → ℤ)) (p K : ℕ) (d : ι → ℤ)
    (hclose : path p = shift d (path 0))
    (hequi : ∀ m < K, ∀ r < p,
      step (shift ((m : ℤ) • d) (path r)) = some (shift ((m : ℤ) • d) (path (r + 1)))) :
    ∀ m < K, run step p (shift ((m : ℤ) • d) (path 0)) =
      some (shift (((m : ℤ) + 1) • d) (path 0)) := by
  intro m hm
  have hr : ∀ r ≤ p, run step r (shift ((m : ℤ) • d) (path 0)) =
      some (shift ((m : ℤ) • d) (path r)) := by
    intro r hrp
    induction r with
    | zero => rfl
    | succ r ih =>
      rw [run_succ', ih (by omega), Option.bind_some, hequi m hm r (by omega)]
  rw [hr p le_rfl, hclose, shift_shift, add_smul, one_smul, add_comm d]

/-- **The jump.** `K` passes, each from the start translated by `m • d`, take
the start to the start translated by `K • d` in `K * p` steps. -/
theorem lasso_accelerate (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (s : C × (ι → ℤ)) (d : ι → ℤ) (p K : ℕ)
    (hiter : ∀ m < K, run step p (shift ((m : ℤ) • d) s) =
      some (shift (((m : ℤ) + 1) • d) s)) :
    run step (K * p) s = some (shift ((K : ℤ) • d) s) := by
  induction K with
  | zero => simp [run]
  | succ K ih =>
    rw [Nat.succ_mul, run_add, ih (fun m hm => hiter m (by omega)), Option.bind_some,
      hiter K (by omega)]
    push_cast
    rfl

/-- **The non-termination certificate.** A pass that can be repeated from
every translate never lets the machine halt. -/
theorem never_halts_of_lasso (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (s : C × (ι → ℤ)) (d : ι → ℤ) {p : ℕ} (hp : 0 < p)
    (hiter : ∀ m : ℕ, run step p (shift ((m : ℤ) • d) s) =
      some (shift (((m : ℤ) + 1) • d) s)) :
    ¬ Halts step s := by
  rintro ⟨n, t, hn, ht⟩
  have hK := lasso_accelerate step s d p (n + 1) (fun m _ => hiter m)
  have hle : n + 1 ≤ (n + 1) * p := Nat.le_mul_of_pos_right _ hp
  obtain ⟨e, he⟩ : ∃ e, (n + 1) * p = n + (e + 1) := ⟨(n + 1) * p - n - 1, by omega⟩
  rw [he, run_add, hn, Option.bind_some] at hK
  simp [run, ht] at hK

/-- **The halting certificate.** Run `i` steps to the start of the pass, jump
`K` passes, and run `n` more steps to a state with no successor: the machine
halts, and after exactly `i + K * p + n` steps. -/
theorem halts_of_jump (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (s₀ s : C × (ι → ℤ)) (d : ι → ℤ) (i p K n : ℕ) (t : C × (ι → ℤ))
    (hi : run step i s₀ = some s)
    (hiter : ∀ m < K, run step p (shift ((m : ℤ) • d) s) =
      some (shift (((m : ℤ) + 1) • d) s))
    (hn : run step n (shift ((K : ℤ) • d) s) = some t) (ht : step t = none) :
    run step (i + K * p + n) s₀ = some t ∧ Halts step s₀ := by
  have h : run step (i + K * p + n) s₀ = some t := by
    rw [run_add, run_add, hi, Option.bind_some, lasso_accelerate step s d p K hiter,
      Option.bind_some, hn]
  exact ⟨h, _, t, h, ht⟩

/-! ## The three kinds of line a pass may hold -/

/-- A line that reads and writes no counter: its effect is a function of the
rest of the state. -/
def indepStep (f : C → Option C) (s : C × (ι → ℤ)) : Option (C × (ι → ℤ)) :=
  (f s.1).map (fun c => (c, s.2))

/-- `SET /A V=V+k`: add `k` to one counter and go on to `next`. -/
def addStep [DecidableEq ι] (next : C → C) (i : ι) (k : ℤ) (s : C × (ι → ℤ)) :
    Option (C × (ι → ℤ)) :=
  some (next s.1, s.2 + Pi.single i k)

/-- `IF … GOTO`: a test on the counters chooses the next part of the state. -/
def testStep (P : (ι → ℤ) → Prop) [DecidablePred P] (yes no : C → C)
    (s : C × (ι → ℤ)) : Option (C × (ι → ℤ)) :=
  some (if P s.2 then yes s.1 else no s.1, s.2)

theorem indep_equivariant (f : C → Option C) (v : ι → ℤ) (s : C × (ι → ℤ)) :
    indepStep f (shift v s) = (indepStep f s).map (shift v) := by
  simp only [indepStep, shift, Option.map_map]
  cases f s.1 <;> rfl

theorem add_equivariant [DecidableEq ι] (next : C → C) (i : ι) (k : ℤ) (v : ι → ℤ)
    (s : C × (ι → ℤ)) :
    addStep next i k (shift v s) = (addStep next i k s).map (shift v) := by
  simp only [addStep, shift, Option.map_some]
  congr 2
  abel

/-- A test commutes with a translation exactly when its outcome is unchanged
by it — which the linear lemmas below decide for a comparison. -/
theorem test_equivariant (P : (ι → ℤ) → Prop) [DecidablePred P] (yes no : C → C)
    (v : ι → ℤ) (s : C × (ι → ℤ)) (h : P (s.2 + v) ↔ P s.2) :
    testStep P yes no (shift v s) = (testStep P yes no s).map (shift v) := by
  simp only [testStep, shift, Option.map_some]
  by_cases hp : P s.2
  · rw [if_pos (h.mpr hp), if_pos hp]
  · rw [if_neg (fun h' => hp (h.mp h')), if_neg hp]

/-! ## A comparison along the passes -/

/-- `e₀ + b·m < 0` at two passes holds at every pass between them. -/
theorem linear_neg_stable {e₀ b m₁ m m₂ : ℤ} (h₁ : m₁ ≤ m) (h₂ : m ≤ m₂)
    (hm₁ : e₀ + b * m₁ < 0) (hm₂ : e₀ + b * m₂ < 0) : e₀ + b * m < 0 := by
  rcases le_total 0 b with hb | hb
  · nlinarith [mul_le_mul_of_nonneg_left h₂ hb]
  · nlinarith [mul_le_mul_of_nonpos_left h₁ hb]

/-- `e₀ + b·m ≥ 0` at two passes holds at every pass between them. -/
theorem linear_nonneg_stable {e₀ b m₁ m m₂ : ℤ} (h₁ : m₁ ≤ m) (h₂ : m ≤ m₂)
    (hm₁ : 0 ≤ e₀ + b * m₁) (hm₂ : 0 ≤ e₀ + b * m₂) : 0 ≤ e₀ + b * m := by
  rcases le_total 0 b with hb | hb
  · nlinarith [mul_le_mul_of_nonneg_left h₁ hb]
  · nlinarith [mul_le_mul_of_nonpos_left h₂ hb]

/-- With `b ≠ 0`, `e₀ + b·m = 0` holds at one pass at most. -/
theorem linear_zero_unique {e₀ b m m' : ℤ} (hb : b ≠ 0) (h : e₀ + b * m = 0)
    (h' : e₀ + b * m' = 0) : m = m' := by
  have : b * (m - m') = 0 := by linarith
  rcases mul_eq_zero.mp this with h0 | h0
  · exact absurd h0 hb
  · linarith

end GLM.CounterLasso
