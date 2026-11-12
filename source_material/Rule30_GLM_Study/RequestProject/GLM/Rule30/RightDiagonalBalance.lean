import RequestProject.GLM.Rule30.Diagonals
import RequestProject.GLM.Rule30.Wobble
import RequestProject.GLM.Rule30.Compute

/-!
# The seed's right side: infinitely many right diagonals are exactly balanced

Round 11, track A (the seed's right-edge boundary as a carrier).

The right diagonals `rdiag D t = a(t)(t − D)` of the seed pattern obey the running-XOR recursion
`rdiag D (t+1) = rdiag D t xor (rdiag (D−1) t ∨ rdiag (D−2) t)` (`rdiag_succ`), and each is
periodic (`rdiag_periodic`).  This file asks the Problem-2 question **along the right
diagonals** and answers it exactly.

* `runningXor_shift` : for a running XOR `v` of a `Q`-periodic input, `v (t+Q) xor v t` is the
  same for every `t`.  So, shifted by a period of its input, a running XOR either repeats or
  flips everywhere.
* `rdiag_periodic_or_antiPeriodic` : if diagonals `D−1` and `D−2` are `Q`-periodic, diagonal `D`
  is either `Q`-periodic or **anti-periodic**: `rdiag D (t+Q) = ! rdiag D t` for all `t`.
* `wobble_antiPeriodic_bound`, `antiPeriodic_balanced` : an anti-periodic sequence has
  wobble `|D(N)| ≤ Q` for **every** `N` (the bounded, ideal delta-sigma regime), exactly `Q`
  ones in its first `2Q` terms, and frequency exactly `1/2`.
* `exists_antiPeriodic_rdiag` : **for every `D₀` there is a right diagonal `D ≥ D₀` that is
  anti-periodic.**  (Otherwise all diagonals from `D₀` on would share one period, against
  `rdiag_period_unbounded`.)
* `infinitely_many_balanced_rdiag` : so infinitely many right diagonals of the seed pattern have
  bounded wobble and frequency exactly `1/2`.
* `rdiag_seven_antiPeriodic`, `rdiag_seven_bounded` : a concrete instance: diagonal `7` is
  anti-periodic with half-period `16`, so `|D(N)| ≤ 16` for every `N`.
* `rdiag_five_not_half` : but not all of them: diagonal `5` has `12` black cells in each period
  of `32` (least period `8`, `3` black), so its frequency is `3/8` and its wobble grows linearly
  (`wobble_rdiag_five`: `D(32k) = −8k`).

The mechanism is the "jump" of the period: when diagonal `D` is not periodic with the period of
its input `rdiag (D−1) ∨ rdiag (D−2)`, it is anti-periodic and hence perfectly balanced.  (`EMP`,
not machine-checked; `rule30_round11/r11_diagonals.c`: to `D = 39` the anti-periodic diagonals are
`D = 1, 2, 3, 4, 6, 7, 9, 15, 16, 24, 25, 27, 29, 34, 36, 37, 39`.  Diagonals `8, 10, 17, 18` are
also balanced over a period without being anti-periodic; the others, e.g. `5, 11–14, 19–23`, are
not balanced.)

The centre column `a(t) = rdiag t t` crosses every diagonal once, so none of this decides
Problem 2 for the centre: it shows that the bounded-wobble regime genuinely occurs in the seed
pattern, on an infinite family of lines, and that it is forced there by the right-edge data.
-/

namespace GLM.Rule30

open Filter Topology

/-- `f` is anti-periodic with half-period `Q`: shifting by `Q` swaps the colours. -/
def AntiPeriodic (f : ℕ → Bool) (Q : ℕ) : Prop := ∀ t, f (t + Q) = !f t

/-- **Shift of a running XOR.** If `v (t+1) = v t xor u t` and `u` is `Q`-periodic, then
`v (t+Q) xor v t` does not depend on `t`. -/
theorem runningXor_shift {u v : ℕ → Bool} {Q : ℕ} (hv : ∀ t, v (t + 1) = xor (v t) (u t))
    (hu : ∀ t, u (t + Q) = u t) : ∀ t, xor (v (t + Q)) (v t) = xor (v Q) (v 0) := by
  intro t
  induction t with
  | zero => simp
  | succ t ih =>
    rw [show t + 1 + Q = (t + Q) + 1 by omega, hv, hv, hu, ← ih]
    cases v (t + Q) <;> cases v t <;> cases u t <;> rfl

/-- A running XOR of a `Q`-periodic input is either `Q`-periodic or anti-periodic with `Q`. -/
theorem runningXor_periodic_or_antiPeriodic {u v : ℕ → Bool} {Q : ℕ}
    (hv : ∀ t, v (t + 1) = xor (v t) (u t)) (hu : ∀ t, u (t + Q) = u t) :
    (∀ t, v (t + Q) = v t) ∨ AntiPeriodic v Q := by
  have h := runningXor_shift hv hu
  cases hs : xor (v Q) (v 0) with
  | false =>
    left; intro t; have := h t; rw [hs] at this
    revert this; cases v (t + Q) <;> cases v t <;> simp
  | true =>
    right; intro t; have := h t; rw [hs] at this
    revert this; cases v (t + Q) <;> cases v t <;> simp

/-- **Periodic or anti-periodic.** If diagonals `D − 1` and `D − 2` are both `Q`-periodic, then
diagonal `D` is `Q`-periodic or anti-periodic with half-period `Q`. -/
theorem rdiag_periodic_or_antiPeriodic (D : ℤ) (Q : ℕ)
    (h1 : ∀ t, rdiag (D - 1) (t + Q) = rdiag (D - 1) t)
    (h2 : ∀ t, rdiag (D - 2) (t + Q) = rdiag (D - 2) t) :
    (∀ t, rdiag D (t + Q) = rdiag D t) ∨ AntiPeriodic (rdiag D) Q :=
  runningXor_periodic_or_antiPeriodic (u := fun t => rdiag (D - 1) t || rdiag (D - 2) t)
    (fun t => rdiag_succ D t) (fun t => by simp only [h1, h2])

/-- The wobble of an anti-periodic sequence: shifting by `Q` reflects it. -/
theorem wobble_antiPeriodic_shift {f : ℕ → Bool} {Q : ℕ} (h : AntiPeriodic f Q) (n : ℕ) :
    wobble f (n + Q) = wobble f Q - wobble f n := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [show n + 1 + Q = (n + Q) + 1 by omega, wobble_succ, ih, wobble_succ, h n]
    cases f n <;> simp <;> ring

/-- An anti-periodic sequence has `2Q`-periodic wobble. -/
theorem wobble_antiPeriodic_periodic {f : ℕ → Bool} {Q : ℕ} (h : AntiPeriodic f Q) (n : ℕ) :
    wobble f (n + 2 * Q) = wobble f n := by
  rw [show n + 2 * Q = (n + Q) + Q by omega, wobble_antiPeriodic_shift h,
    wobble_antiPeriodic_shift h]
  ring

/-- The wobble over a window: `|D(m + k) − D(m)| ≤ k`. -/
theorem abs_wobble_add_sub_le (f : ℕ → Bool) (m k : ℕ) :
    |wobble f (m + k) - wobble f m| ≤ k := by
  induction k with
  | zero => simp
  | succ k ih =>
    rw [show m + (k + 1) = (m + k) + 1 by omega, wobble_succ]
    have : |(if f (m + k) = true then (1 : ℤ) else -1)| ≤ 1 := by split_ifs <;> simp
    calc |wobble f (m + k) + (if f (m + k) = true then 1 else -1) - wobble f m|
        = |(wobble f (m + k) - wobble f m) + (if f (m + k) = true then 1 else -1)| := by
          ring_nf
      _ ≤ |wobble f (m + k) - wobble f m| + |(if f (m + k) = true then (1 : ℤ) else -1)| :=
          abs_add_le _ _
      _ ≤ k + 1 := by linarith
      _ = ((k + 1 : ℕ) : ℤ) := by push_cast; ring

/-- **Bounded wobble.** An anti-periodic sequence with half-period `Q` has `|D(N)| ≤ Q` for
every `N`: it is in the ideal delta-sigma (bounded) regime. -/
theorem wobble_antiPeriodic_bound {f : ℕ → Bool} {Q : ℕ} (h : AntiPeriodic f Q) (n : ℕ) :
    |wobble f n| ≤ Q := by
  induction n using Nat.strong_induction_on with
  | _ n ih =>
    rcases lt_or_ge n (2 * Q) with hn | hn
    · rcases lt_or_ge n Q with hnQ | hnQ
      · exact (abs_wobble_le f n).trans (by exact_mod_cast hnQ.le)
      · -- `n = Q + m` with `m < Q`: `D(n) = D(Q) − D(m)`, the wobble of the window `[m, Q)`
        obtain ⟨m, rfl⟩ : ∃ m, n = m + Q := ⟨n - Q, by omega⟩
        rw [wobble_antiPeriodic_shift h]
        have := abs_wobble_add_sub_le f m (Q - m)
        rw [show m + (Q - m) = Q by omega] at this
        calc |wobble f Q - wobble f m| ≤ ((Q - m : ℕ) : ℤ) := this
          _ ≤ Q := by omega
    · obtain ⟨m, rfl⟩ : ∃ m, n = m + 2 * Q := ⟨n - 2 * Q, by omega⟩
      rw [wobble_antiPeriodic_periodic h]
      rcases Nat.eq_zero_or_pos Q with hQ | hQ
      · subst hQ
        have h0 := h 0
        cases hf : f (0 + 0) <;> simp_all
      · exact ih m (by omega)

/-- **Exact balance.** An anti-periodic sequence has exactly `Q` ones in its first `2Q` terms
(and in any `2Q` consecutive terms, by `wobble_antiPeriodic_periodic`). -/
theorem antiPeriodic_balanced {f : ℕ → Bool} {Q : ℕ} (h : AntiPeriodic f Q) :
    ones f (2 * Q) = Q := by
  have h0 := wobble_antiPeriodic_periodic h 0
  simp only [zero_add, wobble_zero] at h0
  unfold wobble at h0
  push_cast at h0
  omega

/-- An anti-periodic sequence has bounded wobble and frequency exactly `1/2`. -/
theorem antiPeriodic_boundedWobble {f : ℕ → Bool} {Q : ℕ} (h : AntiPeriodic f Q) :
    BoundedWobble f :=
  ⟨Q, fun n => by exact_mod_cast wobble_antiPeriodic_bound h n⟩

theorem antiPeriodic_hasFrequencyHalf {f : ℕ → Bool} {Q : ℕ} (h : AntiPeriodic f Q) :
    HasFrequencyHalf f :=
  hasFrequencyHalf_of_bounded f (antiPeriodic_boundedWobble h)

/-- Iterating a period of `rdiag` (for integer depth). -/
theorem rdiag_periodic_pow_le {D m : ℕ} (h : D ≤ m) :
    ∀ t, rdiag (D : ℤ) (t + 2 ^ m) = rdiag D t := by
  have := periodic_nat_mul (rdiag_periodic D) (2 ^ (m - D))
  intro t
  rw [show 2 ^ m = 2 ^ (m - D) * 2 ^ D by rw [← pow_add]; congr 1; omega]
  exact this t

/-- **Infinitely many anti-periodic right diagonals.** For every `D₀` some diagonal `D ≥ D₀` is
anti-periodic (with a power-of-two half-period). -/
theorem exists_antiPeriodic_rdiag (D₀ : ℕ) :
    ∃ D : ℕ, D₀ ≤ D ∧ ∃ m : ℕ, AntiPeriodic (rdiag D) (2 ^ m) := by
  by_contra hcon
  push_neg at hcon
  -- every diagonal from `D₀' - 1` on is `2^D₀'`-periodic
  set D₀' := max D₀ 1 with hD₀'
  set Q := 2 ^ D₀' with hQ
  have key : ∀ k : ℕ, ∀ t, rdiag ((D₀' - 1 + k : ℕ) : ℤ) (t + Q) = rdiag ((D₀' - 1 + k : ℕ) : ℤ) t
      ∧ rdiag ((D₀' + k : ℕ) : ℤ) (t + Q) = rdiag ((D₀' + k : ℕ) : ℤ) t := by
    intro k
    induction k with
    | zero =>
      intro t
      exact ⟨rdiag_periodic_pow_le (by omega) t, rdiag_periodic_pow_le (by omega) t⟩
    | succ k ih =>
      intro t
      refine ⟨by rw [show D₀' - 1 + (k + 1) = D₀' + k by omega]; exact (ih t).2, ?_⟩
      have hD : ((D₀' + (k + 1) : ℕ) : ℤ) - 1 = ((D₀' + k : ℕ) : ℤ) := by push_cast; ring
      have hD2 : ((D₀' + (k + 1) : ℕ) : ℤ) - 2 = ((D₀' - 1 + k : ℕ) : ℤ) := by
        push_cast; omega
      rcases rdiag_periodic_or_antiPeriodic ((D₀' + (k + 1) : ℕ) : ℤ) Q
          (fun s => by rw [hD]; exact (ih s).2) (fun s => by rw [hD2]; exact (ih s).1) with
        hp | ha
      · exact hp t
      · exact absurd ha (hcon (D₀' + (k + 1)) (by omega) D₀')
  -- but some diagonal is not `Q`-periodic
  obtain ⟨D, hD⟩ := rdiag_period_unbounded Q (by positivity)
  apply hD
  refine ⟨0, fun t _ => ?_⟩
  rcases le_or_gt D₀' D with h | h
  · have := (key (D - D₀') t).2
    rwa [show D₀' + (D - D₀') = D by omega] at this
  · exact rdiag_periodic_pow_le h.le t

/-- **Problem 2 along the right diagonals, for infinitely many of them.** For every `D₀` there is
a right diagonal `D ≥ D₀` of the seed pattern whose wobble is bounded (by a power of two) and whose
frequency of black cells is exactly `1/2`. -/
theorem infinitely_many_balanced_rdiag (D₀ : ℕ) :
    ∃ D : ℕ, D₀ ≤ D ∧ ∃ m : ℕ, (∀ N, |wobble (rdiag D) N| ≤ 2 ^ m) ∧
      ones (rdiag D) (2 * 2 ^ m) = 2 ^ m ∧ HasFrequencyHalf (rdiag D) := by
  obtain ⟨D, hD, m, hm⟩ := exists_antiPeriodic_rdiag D₀
  refine ⟨D, hD, m, fun N => ?_, antiPeriodic_balanced hm, antiPeriodic_hasFrequencyHalf hm⟩
  exact_mod_cast wobble_antiPeriodic_bound hm N

/-! ## Not every right diagonal is balanced -/

/-- Right diagonals through the bit-parallel step (for exact computation). -/
def fastRdiag (D t : ℕ) : Bool := if D ≤ 2 * t then (rowStep^[t] 1).testBit (2 * t - D) else false

theorem rdiag_eq_fast (D t : ℕ) : rdiag D t = fastRdiag D t := by
  unfold fastRdiag
  split_ifs with h
  · rw [testBit_rowStep_iterate 0 1 t (2 * t - D), ← seed_eq_maskConfig, rdiag]
    congr 1; push_cast [h]; ring
  · exact rdiag_before D t (by omega)

/-- The wobble of a `P`-periodic sequence is additive over a period. -/
theorem wobble_periodic_add {f : ℕ → Bool} {P : ℕ} (h : ∀ t, f (t + P) = f t) (n : ℕ) :
    wobble f (P + n) = wobble f P + wobble f n := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [← Nat.add_assoc, wobble_succ, ih, wobble_succ, show P + n = n + P by ring, h]
    ring

/-- One period (`32 = 2^5`) of diagonal `5` holds `12` black cells: wobble `−8`. -/
theorem wobble_rdiag_five_32 : wobble (rdiag 5) 32 = -8 := by
  have : rdiag ((5 : ℕ) : ℤ) = fastRdiag 5 := funext (rdiag_eq_fast 5)
  rw [show ((5 : ℤ)) = ((5 : ℕ) : ℤ) by norm_num, this, wobble, ones_eq_count]
  decide +kernel

/-- The wobble of diagonal `5` falls by `8` on every period of length `32`. -/
theorem wobble_rdiag_five (k : ℕ) : wobble (rdiag 5) (32 * k) = -8 * k := by
  have hp : ∀ t, rdiag ((5 : ℕ) : ℤ) (t + 32) = rdiag ((5 : ℕ) : ℤ) t := rdiag_periodic 5
  simp only [Nat.cast_ofNat] at hp
  induction k with
  | zero => simp
  | succ k ih =>
    rw [show 32 * (k + 1) = 32 + 32 * k by ring, wobble_periodic_add hp, ih,
      wobble_rdiag_five_32]
    push_cast; ring

/-- **Diagonal `5` is not balanced**: its frequency of black cells is `12/32 = 3/8`, so its wobble
grows linearly and the frequency is not `1/2`. -/
theorem rdiag_five_not_half : ¬ HasFrequencyHalf (rdiag 5) := by
  rw [hasFrequencyHalf_iff]
  intro h
  have hsub : Tendsto (fun k : ℕ => 32 * (k + 1)) atTop atTop :=
    tendsto_atTop_mono (fun k => show id k ≤ 32 * (k + 1) by simp only [id]; omega) tendsto_id
  have h2 := h.comp hsub
  have hconst : (fun k : ℕ => (wobble (rdiag 5) (32 * (k + 1)) : ℝ) / ((32 * (k + 1) : ℕ) : ℝ))
      = fun _ => (-1 / 4 : ℝ) := by
    funext k
    rw [wobble_rdiag_five]
    have : ((k : ℝ) + 1) ≠ 0 := by positivity
    push_cast
    field_simp
    ring
  have h3 : Tendsto (fun _ : ℕ => (-1 / 4 : ℝ)) atTop (𝓝 0) := by
    rw [← hconst]; exact h2
  have := tendsto_nhds_unique h3 tendsto_const_nhds
  norm_num at this

/-! ## A concrete anti-periodic diagonal -/

private theorem rdiag_seven_check :
    ∀ t < 128, fastRdiag 7 (t + 16) = !fastRdiag 7 t := by
  decide +kernel

/-- **Diagonal `7` is anti-periodic** with half-period `16` (least period `32`). -/
theorem rdiag_seven_antiPeriodic : AntiPeriodic (rdiag 7) 16 := by
  have hp : ∀ t, rdiag ((7 : ℕ) : ℤ) (t + 128) = rdiag ((7 : ℕ) : ℤ) t := rdiag_periodic 7
  have h7 : ((7 : ℕ) : ℤ) = 7 := by norm_num
  rw [h7] at hp
  intro t
  have key : ∀ s < 128, rdiag 7 (s + 16) = !rdiag 7 s := by
    intro s hs
    have := rdiag_seven_check s hs
    rw [← h7, rdiag_eq_fast, rdiag_eq_fast]; exact this
  conv_lhs => rw [← Nat.mod_add_div t 128]
  conv_rhs => rw [← Nat.mod_add_div t 128]
  have hper : ∀ s k, rdiag 7 (s + 128 * k) = rdiag 7 s := by
    intro s k
    have := periodic_nat_mul hp k s
    rwa [mul_comm] at this
  rw [show t % 128 + 128 * (t / 128) + 16 = (t % 128 + 16) + 128 * (t / 128) by ring, hper, hper]
  exact key _ (Nat.mod_lt _ (by norm_num))

/-- So diagonal `7` has bounded wobble, `|D(N)| ≤ 16` for every `N`, and frequency exactly `1/2`. -/
theorem rdiag_seven_bounded : (∀ N, |wobble (rdiag 7) N| ≤ 16) ∧ HasFrequencyHalf (rdiag 7) :=
  ⟨fun N => by exact_mod_cast wobble_antiPeriodic_bound rdiag_seven_antiPeriodic N,
    antiPeriodic_hasFrequencyHalf rdiag_seven_antiPeriodic⟩

end GLM.Rule30
