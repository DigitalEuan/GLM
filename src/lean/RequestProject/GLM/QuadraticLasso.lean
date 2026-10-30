module

public import RequestProject.GLM.CounterLasso
import all RequestProject.GLM.CounterLasso

/-!
# Quadratic lassos: jumping a pass whose step grows (Phase 142)

The formal half of `studies/QUADRATIC_LASSO_STUDY.md`
(`glm_universal.reasoning.batch_machine.jumped_run`, the quadratic reading).

Phase 130 (`GLM.CounterLasso`) jumps a pass that adds a *fixed* vector `d` to
the counters. A loop such as

    SET /A A=0 / SET /A B=0 / :UP / SET /A A=A+1 / SET /A B=B+A / IF %B% LSS 50000000 GOTO UP

has no such pass: `B` is an *accumulator*, a variable to which a line adds a
counter, so the amount it moves by grows by `1` on every pass. Phase 132
diagnosed it as quadratic (`GLM.AffineOutput.const_second_diff_closed_form`)
and refused it. What comes back now is everything except the counters and the
accumulators, and they come back displaced by the *drift*
`m • d + C(m, 2) • g`, where `d` is what the first pass adds and `g` how much
more each pass adds than the one before.

* `drift`, `drift_zero`, `drift_succ` — the displacement after `m` passes, and
  its recurrence `drift (m + 1) = drift m + d + m • g`;
* `seq_accelerate`, `halts_of_seq_jump`, `never_halts_of_seq_lasso` — Phase
  130's jump, halting and non-termination certificates for passes that move the
  state by any sequence of displacements starting at `0`, not only by `m • d`;
* `accStep`, `acc_shift` — the new kind of line, `SET /A B=B+A` (with a sign
  `σ`): from a displaced state it gives the displaced result, displaced once
  more by `σ` times `A`'s displacement in `B`'s place;
* `quadratic_iterate`, `quadratic_accelerate`, `halts_of_quadratic_jump`,
  `never_halts_of_quadratic_lasso` — so a pass whose steps carry the
  displacement this way, adding `m • g` over pass `m`, is repeated `K` times in
  one jump to the start displaced by `drift d g K`;
* `quad`, `quad_diff`, `quad_closed_form` — a comparison read along the passes
  is `e₀ + b·m + c·C(m, 2)`, whose first differences `b + c·m` are linear;
* `monotone_on_of_diff_nonneg`, `antitone_on_of_diff_nonpos` — a sequence whose
  differences keep one sign on an interval is monotone there, so by the linear
  lemmas of `GLM.CounterLasso` the comparison is monotone on each side of the
  pass where `b + c·m` changes sign;
* `sign_change_persists`, `sign_change_persists_anti` — along a monotone
  stretch, once the sign of the comparison differs from its sign at the start
  of the stretch it never comes back; `cmp_of_sign` — the outcome of each of
  the six comparisons is a function of that sign. This is why the Python may
  find the first pass at which a comparison changes by bisection on at most two
  stretches, and why, when the sign at the start of the unbounded stretch is
  already the extreme one in its direction, it never changes;
* `quad_eventually_pos`, `quad_eventually_neg` — with `c ≠ 0` the comparison
  leaves every bound, so the search for the end of a stretch terminates.

The theorems do not say the Python's reading of a line is right; the column-3
script checks that with its own reading and its own way of finding the first
change.
-/

@[expose] public section

namespace GLM.QuadraticLasso

open GLM.OperationsLadder GLM.CounterLasso

variable {C ι : Type*}

/-! ## The drift -/

/-- The displacement after `m` passes: `m • d + C(m, 2) • g`. -/
def drift (d g : ι → ℤ) (m : ℕ) : ι → ℤ := (m : ℤ) • d + ((m.choose 2 : ℕ) : ℤ) • g

@[simp] theorem drift_zero (d g : ι → ℤ) : drift d g 0 = 0 := by
  simp [drift]

/-- Pass `m` moves the state by `d + m • g`. -/
theorem drift_succ (d g : ι → ℤ) (m : ℕ) :
    drift d g (m + 1) = drift d g m + d + (m : ℤ) • g := by
  simp only [drift, Nat.choose_succ_succ', Nat.choose_one_right]
  push_cast
  rw [add_smul, add_smul, one_smul]
  abel

/-! ## Passes that move the state by a sequence of displacements -/

/-- **The jump, for any displacements.** If pass `m` takes the start displaced
by `D m` to the start displaced by `D (m + 1)`, and `D 0 = 0`, then `K` passes
take the start to the start displaced by `D K`, in `K * p` steps. -/
theorem seq_accelerate (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (s : C × (ι → ℤ)) (D : ℕ → ι → ℤ) (hD : D 0 = 0) (p K : ℕ)
    (hiter : ∀ m < K, run step p (shift (D m) s) = some (shift (D (m + 1)) s)) :
    run step (K * p) s = some (shift (D K) s) := by
  induction K with
  | zero => simp [run, hD]
  | succ K ih =>
    rw [Nat.succ_mul, run_add, ih (fun m hm => hiter m (by omega)), Option.bind_some,
      hiter K (by omega)]

/-- **The halting certificate.** Run `i` steps to the start of the pass, jump
`K` passes, run `n` more steps to a state with no successor. -/
theorem halts_of_seq_jump (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (s₀ s : C × (ι → ℤ)) (D : ℕ → ι → ℤ) (hD : D 0 = 0) (i p K n : ℕ)
    (t : C × (ι → ℤ)) (hi : run step i s₀ = some s)
    (hiter : ∀ m < K, run step p (shift (D m) s) = some (shift (D (m + 1)) s))
    (hn : run step n (shift (D K) s) = some t) (ht : step t = none) :
    run step (i + K * p + n) s₀ = some t ∧ Halts step s₀ := by
  have h : run step (i + K * p + n) s₀ = some t := by
    rw [run_add, run_add, hi, Option.bind_some, seq_accelerate step s D hD p K hiter,
      Option.bind_some, hn]
  exact ⟨h, _, t, h, ht⟩

/-- **The non-termination certificate.** Passes that can be repeated for every
`m` never let the machine halt. -/
theorem never_halts_of_seq_lasso (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (s : C × (ι → ℤ)) (D : ℕ → ι → ℤ) (hD : D 0 = 0) {p : ℕ} (hp : 0 < p)
    (hiter : ∀ m : ℕ, run step p (shift (D m) s) = some (shift (D (m + 1)) s)) :
    ¬ Halts step s := by
  rintro ⟨n, t, hn, ht⟩
  have hK := seq_accelerate step s D hD p (n + 1) (fun m _ => hiter m)
  have hle : n + 1 ≤ (n + 1) * p := Nat.le_mul_of_pos_right _ hp
  obtain ⟨e, he⟩ : ∃ e, (n + 1) * p = n + (e + 1) := ⟨(n + 1) * p - n - 1, by omega⟩
  rw [he, run_add, hn, Option.bind_some] at hK
  simp [run, ht] at hK

/-! ## The accumulator line -/

/-- `SET /A B=B+A` (`σ = 1`) or `SET /A B=B-A` (`σ = -1`): add `σ` times
variable `i` to variable `j` and go on to `next`. -/
def accStep [DecidableEq ι] (next : C → C) (j i : ι) (σ : ℤ) (s : C × (ι → ℤ)) :
    Option (C × (ι → ℤ)) :=
  some (next s.1, s.2 + Pi.single j (σ * s.2 i))

/-- From a state displaced by `v`, the accumulator line gives its result
displaced by `v` and by `σ • v i` more in `j`'s place. -/
theorem acc_shift [DecidableEq ι] (next : C → C) (j i : ι) (σ : ℤ) (v : ι → ℤ)
    (s : C × (ι → ℤ)) :
    accStep next j i σ (shift v s) =
      (accStep next j i σ s).map (shift (v + Pi.single j (σ * v i))) := by
  simp only [accStep, shift, Option.map_some, Pi.add_apply, mul_add]
  congr 2
  rw [Pi.single_add]
  abel

/-! ## One pass, displaced, and the quadratic jump -/

/-- **One pass, from a displaced start.** If at step `r` of pass `m` the state
is the first pass's state displaced by `W m r`, starting at `drift d g m` and
ending `m • g` further on, and the first pass closes up to `d`, then pass `m`
takes the start displaced by `drift d g m` to the start displaced by
`drift d g (m + 1)`. -/
theorem quadratic_iterate (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (path : ℕ → C × (ι → ℤ)) (p K : ℕ) (d g : ι → ℤ) (W : ℕ → ℕ → ι → ℤ)
    (hW0 : ∀ m, W m 0 = drift d g m) (hWp : ∀ m, W m p = drift d g m + (m : ℤ) • g)
    (hclose : path p = shift d (path 0))
    (hstep : ∀ m < K, ∀ r < p,
      step (shift (W m r) (path r)) = some (shift (W m (r + 1)) (path (r + 1)))) :
    ∀ m < K, run step p (shift (drift d g m) (path 0)) =
      some (shift (drift d g (m + 1)) (path 0)) := by
  intro m hm
  have hr : ∀ r ≤ p, run step r (shift (drift d g m) (path 0)) =
      some (shift (W m r) (path r)) := by
    intro r hrp
    induction r with
    | zero => rw [hW0]; rfl
    | succ r ih =>
      rw [run_succ', ih (by omega), Option.bind_some, hstep m hm r (by omega)]
  rw [hr p le_rfl, hWp, hclose, shift_shift, drift_succ]
  congr 2
  abel

/-- **The quadratic jump.** `K` passes take the start of the first pass to the
start displaced by `drift d g K = K • d + C(K, 2) • g`, in `K * p` steps. -/
theorem quadratic_accelerate (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (path : ℕ → C × (ι → ℤ)) (p K : ℕ) (d g : ι → ℤ) (W : ℕ → ℕ → ι → ℤ)
    (hW0 : ∀ m, W m 0 = drift d g m) (hWp : ∀ m, W m p = drift d g m + (m : ℤ) • g)
    (hclose : path p = shift d (path 0))
    (hstep : ∀ m < K, ∀ r < p,
      step (shift (W m r) (path r)) = some (shift (W m (r + 1)) (path (r + 1)))) :
    run step (K * p) (path 0) = some (shift (drift d g K) (path 0)) :=
  seq_accelerate step (path 0) (drift d g) (drift_zero d g) p K
    (quadratic_iterate step path p K d g W hW0 hWp hclose hstep)

/-- **The halting certificate of a quadratic jump**, after exactly
`i + K * p + n` steps. -/
theorem halts_of_quadratic_jump (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (s₀ : C × (ι → ℤ)) (path : ℕ → C × (ι → ℤ)) (i p K n : ℕ) (d g : ι → ℤ)
    (W : ℕ → ℕ → ι → ℤ) (t : C × (ι → ℤ))
    (hW0 : ∀ m, W m 0 = drift d g m) (hWp : ∀ m, W m p = drift d g m + (m : ℤ) • g)
    (hclose : path p = shift d (path 0))
    (hstep : ∀ m < K, ∀ r < p,
      step (shift (W m r) (path r)) = some (shift (W m (r + 1)) (path (r + 1))))
    (hi : run step i s₀ = some (path 0))
    (hn : run step n (shift (drift d g K) (path 0)) = some t) (ht : step t = none) :
    run step (i + K * p + n) s₀ = some t ∧ Halts step s₀ :=
  halts_of_seq_jump step s₀ (path 0) (drift d g) (drift_zero d g) i p K n t hi
    (quadratic_iterate step path p K d g W hW0 hWp hclose hstep) hn ht

/-- **The non-termination certificate of a quadratic lasso**: if every pass,
however far displaced, follows the first, the machine never halts. -/
theorem never_halts_of_quadratic_lasso (step : C × (ι → ℤ) → Option (C × (ι → ℤ)))
    (path : ℕ → C × (ι → ℤ)) {p : ℕ} (hp : 0 < p) (d g : ι → ℤ) (W : ℕ → ℕ → ι → ℤ)
    (hW0 : ∀ m, W m 0 = drift d g m) (hWp : ∀ m, W m p = drift d g m + (m : ℤ) • g)
    (hclose : path p = shift d (path 0))
    (hstep : ∀ m : ℕ, ∀ r < p,
      step (shift (W m r) (path r)) = some (shift (W m (r + 1)) (path (r + 1)))) :
    ¬ Halts step (path 0) :=
  never_halts_of_seq_lasso step (path 0) (drift d g) (drift_zero d g) hp
    (fun m => quadratic_iterate step path p (m + 1) d g W hW0 hWp hclose
      (fun m' _ => hstep m') m (Nat.lt_succ_self m))

/-! ## A comparison along the passes -/

/-- The value of a comparison's difference at pass `m`:
`e₀ + b·m + c·C(m, 2)`. -/
def quad (e₀ b c : ℤ) (m : ℕ) : ℤ := e₀ + b * m + c * (m.choose 2 : ℕ)

/-- Its first differences are linear: `b + c·m`. -/
theorem quad_diff (e₀ b c : ℤ) (m : ℕ) :
    quad e₀ b c (m + 1) - quad e₀ b c m = b + c * m := by
  simp only [quad, Nat.choose_succ_succ', Nat.choose_one_right]
  push_cast
  ring

/-- Without division: `2·quad = 2e₀ + 2bm + c·m(m − 1)`. -/
theorem quad_closed_form (e₀ b c : ℤ) (m : ℕ) :
    2 * quad e₀ b c m = 2 * e₀ + 2 * b * m + c * (m * ((m : ℤ) - 1)) := by
  have h : ((m.choose 2 : ℕ) : ℤ) * 2 = m * ((m : ℤ) - 1) := by
    induction m with
    | zero => simp
    | succ m ih =>
      rw [Nat.choose_succ_succ', Nat.choose_one_right]
      push_cast
      linear_combination ih
  simp only [quad]
  linear_combination c * h

/-- A sequence whose differences are non-negative on `[a, b)` is monotone on
`[a, b]`. -/
theorem monotone_on_of_diff_nonneg (x : ℕ → ℤ) {a b : ℕ}
    (h : ∀ t, a ≤ t → t < b → 0 ≤ x (t + 1) - x t) :
    ∀ m m', a ≤ m → m ≤ m' → m' ≤ b → x m ≤ x m' := by
  intro m m' ham hmm' hm'b
  induction m', hmm' using Nat.le_induction with
  | base => exact le_rfl
  | succ k hk ih =>
    have := h k (by omega) (by omega)
    have := ih (by omega)
    linarith

/-- A sequence whose differences are non-positive on `[a, b)` is antitone on
`[a, b]`. -/
theorem antitone_on_of_diff_nonpos (x : ℕ → ℤ) {a b : ℕ}
    (h : ∀ t, a ≤ t → t < b → x (t + 1) - x t ≤ 0) :
    ∀ m m', a ≤ m → m ≤ m' → m' ≤ b → x m' ≤ x m := by
  intro m m' ham hmm' hm'b
  have := monotone_on_of_diff_nonneg (fun t => -x t) (a := a) (b := b)
    (fun t h1 h2 => by have := h t h1 h2; simp only; linarith) m m' ham hmm' hm'b
  simp only at this
  linarith

/-- The sign of an integer is monotone. -/
theorem sign_mono {u v : ℤ} (h : u ≤ v) : Int.sign u ≤ Int.sign v := by
  rcases lt_trichotomy u 0 with hu | hu | hu <;>
  rcases lt_trichotomy v 0 with hv | hv | hv <;>
  simp [Int.sign_eq_neg_one_of_neg, Int.sign_eq_one_of_pos, hu, hv] <;> omega

/-- **Once changed, never back.** On a stretch `[a, b]` where `x` is monotone,
if the sign of `x m` differs from the sign of `x a`, so does the sign of every
later `x m'` in the stretch. -/
theorem sign_change_persists (x : ℕ → ℤ) {a b : ℕ}
    (hmono : ∀ m m', a ≤ m → m ≤ m' → m' ≤ b → x m ≤ x m')
    {m m' : ℕ} (ham : a ≤ m) (hmm' : m ≤ m') (hm'b : m' ≤ b)
    (hm : Int.sign (x m) ≠ Int.sign (x a)) : Int.sign (x m') ≠ Int.sign (x a) := by
  have h1 := sign_mono (hmono a m le_rfl ham (by omega))
  have h2 := sign_mono (hmono m m' ham hmm' hm'b)
  intro h
  exact hm (le_antisymm (h ▸ h2) h1)

/-- The same on a stretch where `x` is antitone. -/
theorem sign_change_persists_anti (x : ℕ → ℤ) {a b : ℕ}
    (hanti : ∀ m m', a ≤ m → m ≤ m' → m' ≤ b → x m' ≤ x m)
    {m m' : ℕ} (ham : a ≤ m) (hmm' : m ≤ m') (hm'b : m' ≤ b)
    (hm : Int.sign (x m) ≠ Int.sign (x a)) : Int.sign (x m') ≠ Int.sign (x a) := by
  have h1 := sign_mono (hanti a m le_rfl ham (by omega))
  have h2 := sign_mono (hanti m m' ham hmm' hm'b)
  intro h
  exact hm (le_antisymm h1 (h ▸ h2))

/-- **A comparison sees only the sign.** Two differences with the same sign
give the same outcome for each of `= 0`, `≠ 0`, `< 0`, `≤ 0`, `> 0`, `≥ 0`. -/
theorem cmp_of_sign {u v : ℤ} (h : Int.sign u = Int.sign v) :
    (u = 0 ↔ v = 0) ∧ (u ≠ 0 ↔ v ≠ 0) ∧ (u < 0 ↔ v < 0) ∧ (u ≤ 0 ↔ v ≤ 0) ∧
      (0 < u ↔ 0 < v) ∧ (0 ≤ u ↔ 0 ≤ v) := by
  rcases lt_trichotomy u 0 with hu | hu | hu <;>
  rcases lt_trichotomy v 0 with hv | hv | hv <;>
  simp [Int.sign_eq_neg_one_of_neg, Int.sign_eq_one_of_pos, hu, hv] at h ⊢ <;> omega

/-- With `c > 0` the comparison eventually exceeds every bound. -/
theorem quad_eventually_pos (e₀ b c : ℤ) (hc : 0 < c) (B : ℤ) :
    ∃ M : ℕ, ∀ m ≥ M, B < quad e₀ b c m := by
  refine ⟨(2 * (|e₀| + |b| + |B|) + 3).toNat, fun m hm => ?_⟩
  have hm' : (2 * (|e₀| + |b| + |B|) + 3 : ℤ) ≤ m := by
    have := Int.self_le_toNat (2 * (|e₀| + |b| + |B|) + 3)
    omega
  have h2 := quad_closed_form e₀ b c m
  have hae := abs_nonneg e₀
  have hab := abs_nonneg b
  have haB := abs_nonneg B
  have hm1 : (1 : ℤ) ≤ m := by linarith
  have hk : (2 * (|e₀| + |b| + |B|) + 2 : ℤ) ≤ (m : ℤ) - 1 := by linarith
  have hmm : (m : ℤ) * (2 * (|e₀| + |b| + |B|) + 2) ≤ (m : ℤ) * ((m : ℤ) - 1) :=
    mul_le_mul_of_nonneg_left hk (by linarith)
  have hq0 : (0 : ℤ) ≤ (m : ℤ) * ((m : ℤ) - 1) := by nlinarith
  have hc1 : (m : ℤ) * ((m : ℤ) - 1) ≤ c * ((m : ℤ) * ((m : ℤ) - 1)) := by nlinarith
  have hbm : -(|b| * m) ≤ b * m := by
    have := neg_abs_le b
    nlinarith
  have he : -|e₀| ≤ e₀ := neg_abs_le e₀
  have hB : B ≤ |B| := le_abs_self B
  have hlin : 2 * |e₀| + 2 * |B| + 2 ≤ (m : ℤ) * (2 * |e₀| + 2 * |B| + 2) := by nlinarith
  nlinarith

/-- With `c < 0` the comparison eventually falls below every bound. -/
theorem quad_eventually_neg (e₀ b c : ℤ) (hc : c < 0) (B : ℤ) :
    ∃ M : ℕ, ∀ m ≥ M, quad e₀ b c m < B := by
  obtain ⟨M, hM⟩ := quad_eventually_pos (-e₀) (-b) (-c) (by linarith) (-B)
  refine ⟨M, fun m hm => ?_⟩
  have := hM m hm
  simp only [quad] at this ⊢
  linarith

end GLM.QuadraticLasso
