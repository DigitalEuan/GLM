module

public import RequestProject.GLM.Rule30.AdjacentColumns

/-!
# Seed-specific structure: the right-hand diagonals are periodic

This file is about the **specific seed** (one black cell), not about the generic `n`-step map.
It proves exactly where periodicity lives in Rule 30 started from the seed.

The `D`-th *right diagonal* is the sequence of cells at distance `D` inside the right edge of
the light cone:

  `rdiag D t = a(t)(t − D)`.

* `rdiag_succ` : the diagonals satisfy a **triangular, linear-in-the-top-variable recursion**
  `rdiag D (t+1) = rdiag D t xor (rdiag (D−1) t ∨ rdiag (D−2) t)`.
  Diagonal `D` is the running XOR (a discrete integral over `GF(2)`) of an expression in the
  two diagonals outside it. This is the seed-specific algebra of the right side.
* `rdiag_periodic` : **every right diagonal is periodic from time `0`, with period `2^D`**.
  The period at most doubles each time one moves one diagonal inwards.
* `rdiag_mod` : consequently `a(t)(t − D) = a(t mod 2^D)(t mod 2^D − D)`. A cell at fixed depth
  `D` behind the right edge is computable from `t mod 2^D` alone (a lookup of size `2^D`).
* `rdiag_not_periodic`, `rdiag_period_unbounded` : **but the periods are unbounded**. Diagonal
  `D` is not eventually `p`-periodic for any `0 < p ≤ ⌈D/2⌉`, so its least period `P_D` satisfies
  `⌈D/2⌉ < P_D ≤ 2^D`. (Outside Lean, a simulation to `t = 600` finds `P_D = 1, 2, 2, 4, 8, 8,
  16, 32, 32` for `D = 0, …, 8`. That is not machine-checked.)
* `centerCol_eq_rdiag` : the centre column is `a(t) = rdiag t t`. It reads diagonal `t` at
  time `t`, so it crosses every diagonal and never stays on one. Each diagonal is periodic,
  but the diagonal through the centre cell at time `t` has period larger than `t/2`. Its
  periodicity has not had time to show by the time the centre reads it.

**Orientation.** These diagonals sit behind the *right* edge, the side where Rule 30's picture looks
irregular. The exponentially growing periods are what makes it look irregular. Rule 30's visible
diagonal stripes sit on the *left* side. Outside Lean, a simulation to `t = 4000` finds the left
diagonals `a(t)(−t+E)` for `E ≤ 57` eventually periodic with periods `≤ 8`, after transients
growing roughly like `1.4·E`. That is not machine-checked, and the left diagonals do not satisfy a
running-XOR recursion: their recursion is nonlinear in the diagonal itself.
-/

@[expose] public section

namespace GLM.Rule30

/-- The `D`-th right diagonal of the seed pattern: the cell at distance `D` inside the right
edge of the light cone at time `t`. -/
def rdiag (D : ℤ) (t : ℕ) : Bool := evolve seed t (t - D)

/-- Diagonals outside the light cone are white. -/
theorem rdiag_neg {D : ℤ} (hD : D < 0) (t : ℕ) : rdiag D t = false := by
  unfold rdiag
  apply evolve_seed_outside
  rw [abs_of_nonneg (by omega)]
  omega

/-- At time `0` only diagonal `0` is black. -/
theorem rdiag_zero (D : ℤ) : rdiag D 0 = decide (D = 0) := by
  simp [rdiag, seed]

/-- **The diagonal recursion.** Diagonal `D` is the running XOR of
`rdiag (D-1) ∨ rdiag (D-2)`. -/
theorem rdiag_succ (D : ℤ) (t : ℕ) :
    rdiag D (t + 1) = xor (rdiag D t) (rdiag (D - 1) t || rdiag (D - 2) t) := by
  unfold rdiag
  rw [evolve_succ]
  unfold rule30
  rw [show ((t + 1 : ℕ) : ℤ) - D - 1 = (t : ℤ) - D by push_cast; ring,
    show ((t + 1 : ℕ) : ℤ) - D + 1 = (t : ℤ) - (D - 2) by push_cast; ring,
    show ((t + 1 : ℕ) : ℤ) - D = (t : ℤ) - (D - 1) by push_cast; ring]

/-- The centre column is diagonal `t` read at time `t`. -/
theorem centerCol_eq_rdiag (t : ℕ) : centerCol t = rdiag t t := by
  simp [centerCol, rdiag]

/-- Iterating a period. -/
theorem periodic_nat_mul {f : ℕ → Bool} {q : ℕ} (h : ∀ t, f (t + q) = f t) (k : ℕ) :
    ∀ t, f (t + k * q) = f t := by
  induction k with
  | zero => simp
  | succ k ih => intro t; rw [Nat.succ_mul, ← Nat.add_assoc, h, ih]

/-- **Running XOR doubles the period.** If `v (t+1) = v t xor u t` and `u` is `q`-periodic,
then `v` is `2q`-periodic. -/
theorem runningXor_periodic {u v : ℕ → Bool} {q : ℕ} (hv : ∀ t, v (t + 1) = xor (v t) (u t))
    (hu : ∀ t, u (t + q) = u t) : ∀ t, v (t + 2 * q) = v t := by
  have hw : ∀ t, xor (v (t + q)) (v t) = xor (v q) (v 0) := by
    intro t
    induction t with
    | zero => simp
    | succ t ih =>
      rw [show t + 1 + q = (t + q) + 1 by omega, hv, hv, hu, ← ih]
      cases v (t + q) <;> cases v t <;> cases u t <;> rfl
  intro t
  have h1 := hw t
  have h2 := hw (t + q)
  rw [show t + q + q = t + 2 * q by omega] at h2
  revert h1 h2
  cases v (t + 2 * q) <;> cases v (t + q) <;> cases v t <;> cases xor (v q) (v 0) <;> simp

/-- **Every right diagonal of the seed pattern is periodic from time `0`, with period `2^D`.** -/
theorem rdiag_periodic (D : ℕ) : ∀ t, rdiag D (t + 2 ^ D) = rdiag D t := by
  induction D using Nat.strong_induction_on with
  | _ D ih =>
    rcases Nat.eq_zero_or_pos D with rfl | hD
    · intro t
      rw [pow_zero, rdiag_succ]
      simp only [Nat.cast_zero, zero_sub]
      rw [rdiag_neg (D := -1) (by norm_num), rdiag_neg (D := -2) (by norm_num)]
      simp
    · -- the driving term `u t = rdiag (D-1) t ∨ rdiag (D-2) t` is `2^(D-1)`-periodic
      have hu : ∀ t, (rdiag ((D : ℤ) - 1) (t + 2 ^ (D - 1)) || rdiag ((D : ℤ) - 2) (t + 2 ^ (D - 1)))
          = (rdiag ((D : ℤ) - 1) t || rdiag ((D : ℤ) - 2) t) := by
        intro t
        have h1 : rdiag ((D : ℤ) - 1) (t + 2 ^ (D - 1)) = rdiag ((D : ℤ) - 1) t := by
          have := ih (D - 1) (by omega) t
          rwa [show ((D - 1 : ℕ) : ℤ) = (D : ℤ) - 1 by omega] at this
        have h2 : rdiag ((D : ℤ) - 2) (t + 2 ^ (D - 1)) = rdiag ((D : ℤ) - 2) t := by
          rcases Nat.lt_or_ge D 2 with hD2 | hD2
          · rw [rdiag_neg (by omega), rdiag_neg (by omega)]
          · have := periodic_nat_mul (f := rdiag ((D : ℤ) - 2)) (q := 2 ^ (D - 2)) (by
              intro s
              have := ih (D - 2) (by omega) s
              rwa [show ((D - 2 : ℕ) : ℤ) = (D : ℤ) - 2 by omega] at this) 2 t
            rwa [show 2 * 2 ^ (D - 2) = 2 ^ (D - 1) by
              rw [← pow_succ']; congr 1; omega] at this
        rw [h1, h2]
      have := runningXor_periodic (v := rdiag (D : ℤ))
        (u := fun t => rdiag ((D : ℤ) - 1) t || rdiag ((D : ℤ) - 2) t) (q := 2 ^ (D - 1))
        (fun t => rdiag_succ _ t) hu
      intro t
      rw [show 2 ^ D = 2 * 2 ^ (D - 1) by rw [← pow_succ']; congr 1; omega]
      exact this t

/-- Each right diagonal is eventually periodic in the sense of Problem 1. -/
theorem rdiag_eventuallyPeriodic (D : ℕ) : EventuallyPeriodic (rdiag D) :=
  ⟨2 ^ D, by positivity, 0, fun t _ => rdiag_periodic D t⟩

/-- **Fixed-depth cells are a table lookup.** `a(t)(t − D)` depends only on `t mod 2^D`. -/
theorem rdiag_mod (D t : ℕ) : rdiag D t = rdiag D (t % 2 ^ D) := by
  conv_lhs => rw [← Nat.mod_add_div t (2 ^ D), mul_comm]
  exact periodic_nat_mul (rdiag_periodic D) _ _

/-- Before time `⌈D/2⌉` the diagonal `D` lies outside the light cone. -/
theorem rdiag_before (D t : ℕ) (h : 2 * t < D) : rdiag D t = false := by
  unfold rdiag
  apply evolve_seed_outside
  rw [abs_of_neg (by omega)]
  omega

/-- The diagonal `D ≥ 1` turns black at time `⌈D/2⌉`: it enters the light cone on the left edge
(`D` even) or one cell inside it (`D` odd). -/
theorem rdiag_first_black (D : ℕ) (hD : 1 ≤ D) : rdiag D ((D + 1) / 2) = true := by
  rcases Nat.even_or_odd D with ⟨k, hk⟩ | ⟨k, hk⟩
  · -- `D = 2k`, entry on the left edge
    have h2 : (D + 1) / 2 = k := by omega
    rw [h2]
    unfold rdiag
    have := evolve_seed_left_edge k
    convert this using 2
    omega
  · -- `D = 2k + 1`, entry one cell inside the left edge
    have h2 : (D + 1) / 2 = k + 1 := by omega
    rw [h2]
    unfold rdiag
    rw [evolve_succ, evolve_seed_outside k _ (by rw [abs_of_neg (by push_cast; omega)]; push_cast; omega)]
    have : ((k + 1 : ℕ) : ℤ) - D = -(k : ℤ) := by push_cast; omega
    rw [this, evolve_seed_left_edge]
    rfl

/-- **Lower bound on the periods.** The diagonal `D` is not eventually `p`-periodic for any
`0 < p ≤ ⌈D/2⌉`. Together with `rdiag_periodic`, the least period `P_D` of diagonal `D` is a power of
two with `⌈D/2⌉ < P_D ≤ 2^D`. -/
theorem rdiag_not_periodic (D p : ℕ) (hp : 0 < p) (hpD : p ≤ (D + 1) / 2) :
    ¬ ∃ N, ∀ t ≥ N, rdiag D (t + p) = rdiag D t := by
  rintro ⟨N, hN⟩
  have hD : 1 ≤ D := by omega
  set t0 := (D + 1) / 2
  have hper := periodic_nat_mul (rdiag_periodic D) N
  have h1 := rdiag_first_black D hD
  have h0 : rdiag D (t0 - p) = false := rdiag_before D _ (by omega)
  have key := hN (t0 - p + N * 2 ^ D) (by
    have : N ≤ N * 2 ^ D := Nat.le_mul_of_pos_right N (by positivity)
    omega)
  rw [show t0 - p + N * 2 ^ D + p = t0 + N * 2 ^ D by omega, hper, hper, h1, h0] at key
  exact Bool.noConfusion key

/-- **No common period.** For every `p > 0` there is a right diagonal (for example `D = 2p`) which
is not eventually `p`-periodic. So the periods of the diagonals are unbounded. -/
theorem rdiag_period_unbounded (p : ℕ) (hp : 0 < p) :
    ∃ D : ℕ, ¬ ∃ N, ∀ t ≥ N, rdiag D (t + p) = rdiag D t :=
  ⟨2 * p, rdiag_not_periodic (2 * p) p hp (by omega)⟩

/-- Packaged: every right diagonal is periodic from time `0`, but the periods are unbounded. -/
theorem right_diagonals_periodic_with_unbounded_periods :
    (∀ D : ℕ, ∀ t, rdiag D (t + 2 ^ D) = rdiag D t) ∧
      (∀ p > 0, ∃ D : ℕ, ¬ ∃ N, ∀ t ≥ N, rdiag D (t + p) = rdiag D t) :=
  ⟨rdiag_periodic, rdiag_period_unbounded⟩

end GLM.Rule30
