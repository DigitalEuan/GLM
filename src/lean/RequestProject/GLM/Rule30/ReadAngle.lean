module

public import RequestProject.GLM.Rule30.WobbleLenses

/-!
# Round 12: the read angle — lines parallel to the left edge

The observer can read the space-time diagram of Rule 30 along lines of different slope.
The centre column is the vertical line `c = 0`.  Round 11 read along the **right** edge (the
right diagonals, `RightDiagonalBalance.lean`).  This file reads along the **left** edge.

`ldiag D t = a(t)(D − t)` is the cell `D` steps inside the left edge (`D = 0` is the edge itself,
which is always black).  The rule `L xor (C or R)` becomes, in these coordinates,

  `ldiag D (t+1) = ldiag (D−2) t xor (ldiag (D−1) t ∨ ldiag D t)`   (`ldiag_succ`),

a one-bit machine driven by the two diagonals outside it.

Main results (all proved):

* `bool_transducer_periodic` : a one-bit machine driven by an input that is periodic with period
  `Q` from time `T` on is periodic with period `2Q` from time `T + Q` on.
* `ldiag_eventually_periodic` : **every left diagonal of the seed pattern is eventually periodic,
  with a power-of-two period.**
* `centerCol_eq_ldiag` : the centre column is `a(t) = ldiag t t`: at time `t` it reads diagonal `t`,
  so it meets each left diagonal once, at time `t = D`.

So every read at the angle of either edge is eventually periodic, while the read at angle zero
(the centre column) is Problem 1.  Exact computation (`EMP`, not machine-checked;
`rule30_round12/r12_read_angle.c`): the left diagonals have tiny periods (at most `8` for
`D ≤ 200`), but each becomes periodic only after a transient of length about `1.3·D` for
`D ≥ 20`, later than the time `t = D` at which the centre column reads it.  The centre column
always reads the left diagonals inside their transients.
-/

@[expose] public section

namespace GLM.Rule30

/-- Left diagonal `D`: the cell `D` steps inside the left edge at time `t`. -/
def ldiag (D : ℤ) (t : ℕ) : Bool := evolve seed t (D - t)

theorem ldiag_neg {D : ℤ} (hD : D < 0) (t : ℕ) : ldiag D t = false :=
  evolve_seed_outside t _ (by rw [abs_of_neg (by omega)]; omega)

theorem ldiag_zero (t : ℕ) : ldiag 0 t = true := by
  simpa [ldiag] using evolve_seed_left_edge t

/-- The rule in left-diagonal coordinates. -/
theorem ldiag_succ (D : ℤ) (t : ℕ) :
    ldiag D (t + 1) = xor (ldiag (D - 2) t) (ldiag (D - 1) t || ldiag D t) := by
  unfold ldiag
  rw [evolve_succ]
  have e1 : D - ((t + 1 : ℕ) : ℤ) - 1 = D - 2 - t := by push_cast; ring
  have e2 : D - ((t + 1 : ℕ) : ℤ) = D - 1 - t := by push_cast; ring
  have e3 : D - ((t + 1 : ℕ) : ℤ) + 1 = D - t := by push_cast; ring
  rw [e1, e3, e2]; rfl

/-- The centre column reads left diagonal `t` at time `t`. -/
theorem centerCol_eq_ldiag (t : ℕ) : centerCol t = ldiag t t := by
  simp [ldiag, centerCol]

/-- Running a one-bit machine from time `s` with initial bit `b`. -/
def runFrom (g : ℕ → Bool → Bool) (s : ℕ) (b : Bool) : ℕ → Bool
  | 0 => b
  | n + 1 => g (s + n) (runFrom g s b n)

theorem eq_runFrom {g : ℕ → Bool → Bool} {u : ℕ → Bool} (hu : ∀ t, u (t + 1) = g t (u t))
    (s n : ℕ) : u (s + n) = runFrom g s (u s) n := by
  induction n with
  | zero => rfl
  | succ n ih => rw [← add_assoc, hu, ih]; rfl

theorem runFrom_shift {g : ℕ → Bool → Bool} {Q T : ℕ} (hg : ∀ t ≥ T, g (t + Q) = g t)
    {s : ℕ} (hs : T ≤ s) (b : Bool) (n : ℕ) : runFrom g (s + Q) b n = runFrom g s b n := by
  induction n with
  | zero => rfl
  | succ n ih =>
    simp only [runFrom, ih]
    rw [show s + Q + n = (s + n) + Q by ring, hg _ (by omega)]

theorem bool_cube (f : Bool → Bool) (b : Bool) : f (f (f b)) = f b := by
  cases h1 : f true <;> cases h2 : f false <;> cases b <;> simp [h1, h2]

/-- **A one-bit machine with eventually periodic input is eventually periodic**, with twice the
period. -/
theorem bool_transducer_periodic {g : ℕ → Bool → Bool} {u : ℕ → Bool} {Q T : ℕ}
    (hu : ∀ t, u (t + 1) = g t (u t)) (hg : ∀ t ≥ T, g (t + Q) = g t) :
    ∀ t ≥ T + Q, u (t + 2 * Q) = u t := by
  set f := fun b => runFrom g T b Q with hf
  have step : ∀ k, u (T + (k + 1) * Q) = f (u (T + k * Q)) := by
    intro k
    rw [show T + (k + 1) * Q = (T + k * Q) + Q by ring, eq_runFrom hu]
    simp only [hf]
    have : ∀ j b, runFrom g (T + j * Q) b Q = runFrom g T b Q := by
      intro j b
      induction j with
      | zero => simp
      | succ j ih =>
        rw [show T + (j + 1) * Q = (T + j * Q) + Q by ring, runFrom_shift hg (by nlinarith), ih]
    exact this k _
  have h1 : u (T + Q) = f (u T) := by simpa using step 0
  have h2 : u (T + 2 * Q) = f (u (T + Q)) := by
    have := step 1; rwa [show (1 + 1) * Q = 2 * Q by ring, one_mul] at this
  have h3 : u (T + 3 * Q) = f (u (T + 2 * Q)) := by
    have := step 2; rwa [show (2 + 1) * Q = 3 * Q by ring] at this
  have base : u (T + Q + 2 * Q) = u (T + Q) := by
    rw [show T + Q + 2 * Q = T + 3 * Q by ring, h3, h2, h1]
    exact bool_cube f _
  have hg2 : ∀ t ≥ T, g (t + 2 * Q) = g t := by
    intro t ht
    rw [show t + 2 * Q = (t + Q) + Q by ring, hg _ (by omega), hg _ ht]
  intro t ht
  induction t, ht using Nat.le_induction with
  | base => exact base
  | succ t ht ih =>
    rw [show t + 1 + 2 * Q = (t + 2 * Q) + 1 by ring, hu, hu, ih, hg2 t (by omega)]

/-- **Every left diagonal of the seed pattern is eventually periodic**, with a power-of-two
period. -/
theorem ldiag_eventually_periodic (D : ℤ) :
    ∃ k T : ℕ, ∀ t ≥ T, ldiag D (t + 2 ^ k) = ldiag D t := by
  suffices h : ∀ n : ℕ, ∀ D : ℤ, D < n → ∃ k T : ℕ, ∀ t ≥ T, ldiag D (t + 2 ^ k) = ldiag D t by
    exact h (D.toNat + 1) D (by omega)
  intro n
  induction n with
  | zero =>
    intro D hD
    exact ⟨0, 0, fun t _ => by rw [ldiag_neg (by omega), ldiag_neg (by omega)]⟩
  | succ n ih =>
    intro D hD
    rcases lt_or_ge D n with h | h
    · exact ih D h
    obtain ⟨k1, T1, h1⟩ := ih (D - 1) (by omega)
    obtain ⟨k2, T2, h2⟩ := ih (D - 2) (by omega)
    set m := max k1 k2
    have p1 : ∀ t ≥ max T1 T2, ldiag (D - 1) (t + 2 ^ m) = ldiag (D - 1) t := by
      intro t ht
      have := periodic_mul h1 (2 ^ (m - k1)) t (by omega)
      rwa [← pow_add, Nat.sub_add_cancel (le_max_left _ _)] at this
    have p2 : ∀ t ≥ max T1 T2, ldiag (D - 2) (t + 2 ^ m) = ldiag (D - 2) t := by
      intro t ht
      have := periodic_mul h2 (2 ^ (m - k2)) t (by omega)
      rwa [← pow_add, Nat.sub_add_cancel (le_max_right _ _)] at this
    refine ⟨m + 1, max T1 T2 + 2 ^ m, fun t ht => ?_⟩
    have := bool_transducer_periodic (g := fun t b => xor (ldiag (D - 2) t) (ldiag (D - 1) t || b))
      (u := ldiag D) (Q := 2 ^ m) (T := max T1 T2) (fun t => ldiag_succ D t)
      (fun t ht => by funext b; simp only [p1 t ht, p2 t ht]) t ht
    rw [pow_succ, mul_comm]; exact this

theorem ldiag_eventuallyPeriodic (D : ℤ) : EventuallyPeriodic (ldiag D) := by
  obtain ⟨k, T, h⟩ := ldiag_eventually_periodic D
  exact ⟨2 ^ k, by positivity, T, h⟩

end GLM.Rule30
