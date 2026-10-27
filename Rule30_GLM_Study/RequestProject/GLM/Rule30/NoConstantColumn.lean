module

public import RequestProject.GLM.Rule30.Prizes

/-!
# Problem 1, the period-1 case: no column is eventually constant

Problem 1 asks that the centre column is not eventually periodic for **any** period `p`.
This file settles the case `p = 1`, for every column of every row that is white far to the
left and not entirely white (in particular for Wolfram's single black cell):

* `column_not_eventually_constant` : no column is eventually constant.
* `centerCol_not_eventually_constant`, `centerCol_changes_infinitely_often`,
  `centerCol_infinitely_many_true`, `centerCol_infinitely_many_false` : the centre column
  changes colour infinitely often, and both colours occur infinitely often.

The argument reduces the claim to the adjacent-columns theorem
(`not_both_adjacent_columns_periodic`), using the rule `L xor (C or R)` in two ways:

* if column `c` is eventually black, then `C or R = 1` there, so column `c - 1` is forced to be
  `not (next value of column c) = white`; columns `c - 1` and `c` would both be constant;
* if column `c` is eventually white, then column `c + 1` obeys `new = C or R`, so it can only
  switch from white to black, never back; it is eventually constant, and columns `c` and
  `c + 1` would both be constant.
-/

@[expose] public section

namespace GLM.Rule30

/-- An eventually constant sequence is eventually periodic (with period `1`). -/
theorem eventuallyPeriodic_of_eventually_const {a : ℕ → Bool} {b : Bool} {N : ℕ}
    (h : ∀ t ≥ N, a t = b) : EventuallyPeriodic a :=
  ⟨1, one_pos, N, fun n hn => by rw [h n hn, h (n + 1) (by omega)]⟩

/-- A Boolean sequence that can only switch from `false` to `true` from time `N` on is
eventually constant. -/
theorem eventually_const_of_monotone {a : ℕ → Bool} {N : ℕ}
    (h : ∀ t ≥ N, a t = true → a (t + 1) = true) : ∃ b M, ∀ t ≥ M, a t = b := by
  by_cases hex : ∃ s ≥ N, a s = true
  · obtain ⟨s, hs, hs'⟩ := hex
    refine ⟨true, s, fun t ht => ?_⟩
    induction t, ht using Nat.le_induction with
    | base => exact hs'
    | succ t ht ih => exact h t (by omega) ih
  · push_neg at hex
    exact ⟨false, N, fun t ht => by simpa using hex t ht⟩

/-- **No column is eventually constant** (for any row that is white on `(-∞, ℓ)` and black
at `ℓ`). This is the period-`1` case of the non-periodicity question, for every column. -/
theorem column_not_eventually_constant (x : Config) (ℓ : ℤ)
    (hx : ∀ j, j < ℓ → x j = false) (hℓ : x ℓ = true) (c : ℤ) :
    ¬ ∃ b N, ∀ t ≥ N, evolve x t c = b := by
  rintro ⟨b, N, hN⟩
  cases b with
  | true =>
    -- column `c - 1` is forced white
    have hleft : ∀ t ≥ N, evolve x t (c - 1) = false := by
      intro t ht
      rw [evolve_solve_left, hN t ht, hN (t + 1) (by omega)]
      rfl
    exact not_both_adjacent_columns_periodic x ℓ hx hℓ (c - 1)
      ⟨eventuallyPeriodic_of_eventually_const hleft,
        by simpa using eventuallyPeriodic_of_eventually_const hN⟩
  | false =>
    -- column `c + 1` can only switch from white to black
    have hmono : ∀ t ≥ N, evolve x t (c + 1) = true → evolve x (t + 1) (c + 1) = true := by
      intro t ht h1
      rw [evolve_succ, show c + 1 - 1 = c by ring, hN t ht, h1]
      rfl
    obtain ⟨b', M, hM⟩ := eventually_const_of_monotone hmono
    exact not_both_adjacent_columns_periodic x ℓ hx hℓ c
      ⟨eventuallyPeriodic_of_eventually_const hN, eventuallyPeriodic_of_eventually_const hM⟩

/-- For Wolfram's single black cell, no column is eventually constant. -/
theorem seed_column_not_eventually_constant (c : ℤ) :
    ¬ ∃ b N, ∀ t ≥ N, evolve seed t c = b :=
  column_not_eventually_constant seed 0 (fun j hj => by simp [seed]; omega) (by simp [seed]) c

/-- **Problem 1 for period `1`:** the centre column is not eventually constant. -/
theorem centerCol_not_eventually_constant : ¬ ∃ b N, ∀ t ≥ N, centerCol t = b :=
  seed_column_not_eventually_constant 0

/-- The centre column changes colour infinitely often (the lag-`1` mismatches are unbounded). -/
theorem centerCol_changes_infinitely_often (N : ℕ) :
    ∃ t ≥ N, centerCol (t + 1) ≠ centerCol t := by
  by_contra h
  push_neg at h
  refine centerCol_not_eventually_constant ⟨centerCol N, N, fun t ht => ?_⟩
  induction t, ht using Nat.le_induction with
  | base => rfl
  | succ t ht ih => rw [h t ht, ih]

/-- The centre column is black infinitely often. -/
theorem centerCol_infinitely_many_true (N : ℕ) : ∃ t ≥ N, centerCol t = true := by
  by_contra h
  push_neg at h
  exact centerCol_not_eventually_constant ⟨false, N, fun t ht => by simpa using h t ht⟩

/-- The centre column is white infinitely often. -/
theorem centerCol_infinitely_many_false (N : ℕ) : ∃ t ≥ N, centerCol t = false := by
  by_contra h
  push_neg at h
  exact centerCol_not_eventually_constant ⟨true, N, fun t ht => by simpa using h t ht⟩

/-! ## A quantitative version: constant runs are at most linear in their starting time -/

/-- **Finite form of the adjacent-columns theorem.** If columns `c` and `c + 1` are both
constant on the time window `[N, N + L]`, then `L ≤ c - ℓ + N + 1`. (The constancy propagates
leftwards on shrinking windows until it meets the left light-cone edge.) -/
theorem adjacent_run_bound (x : Config) (ℓ : ℤ)
    (hx : ∀ j, j < ℓ → x j = false) (hℓ : x ℓ = true) (c : ℤ) (N L : ℕ)
    (hc : ℓ ≤ c + N + 1)
    (hrun : ∀ t, N ≤ t → t ≤ N + L →
      evolve x t c = evolve x N c ∧ evolve x t (c + 1) = evolve x N (c + 1)) :
    (L : ℤ) ≤ c - ℓ + N + 1 := by
  by_contra hL
  push_neg at hL
  have prop : ∀ k : ℕ, ∀ t, N ≤ t → t + k ≤ N + L →
      evolve x t (c - k) = evolve x N (c - k) ∧
        evolve x t (c + 1 - k) = evolve x N (c + 1 - k) := by
    intro k
    induction k with
    | zero => intro t h1 h2; simpa using hrun t h1 (by omega)
    | succ k ih =>
      intro t h1 h2
      have ih1 := ih (t + 1) (by omega) (by omega)
      have ih0 := ih t h1 (by omega)
      have ihN1 := ih (N + 1) (by omega) (by omega)
      refine ⟨?_, ?_⟩
      · have e : c - ↑(k + 1) = (c - k) - 1 := by push_cast; ring
        rw [e, evolve_solve_left, evolve_solve_left x N, ih1.1, ihN1.1, ih0.1,
          show c - ↑k + 1 = c + 1 - k by ring, ih0.2]
      · rw [show c + 1 - ↑(k + 1) = c - k by push_cast; ring]; exact ih0.1
  set k := (c - ℓ + N + 1).toNat with hk
  have hk' : (k : ℤ) = c - ℓ + N + 1 := by rw [hk]; omega
  have h := (prop k (N + 1) (by omega) (by omega)).1
  rw [show c - (k : ℤ) = ℓ - ((N + 1 : ℕ) : ℤ) by push_cast; omega,
    evolve_left_edge x ℓ hx hℓ (N + 1),
    evolve_white_left x ℓ hx N _ (by push_cast; omega)] at h
  exact absurd h (by decide)

/-- **Constant runs are short.** If column `c` is constant on the time window `[N, N + L]`
(and `ℓ ≤ c + N`), then `L ≤ 3 (c - ℓ + N) + 5`. -/
theorem column_run_bound (x : Config) (ℓ : ℤ)
    (hx : ∀ j, j < ℓ → x j = false) (hℓ : x ℓ = true) (c : ℤ) (N L : ℕ)
    (hc : ℓ ≤ c + N)
    (hrun : ∀ t, N ≤ t → t ≤ N + L → evolve x t c = evolve x N c) :
    (L : ℤ) ≤ 3 * (c - ℓ + N) + 5 := by
  cases hb : evolve x N c with
  | true =>
    -- column `c - 1` is white on `[N, N + L - 1]`
    rcases Nat.eq_zero_or_pos L with h0 | hpos
    · subst h0; push_cast; omega
    have hleft : ∀ t, N ≤ t → t ≤ N + (L - 1) → evolve x t (c - 1) = false := by
      intro t h1 h2
      rw [evolve_solve_left, hrun t h1 (by omega), hrun (t + 1) (by omega) (by omega), hb]
      rfl
    have := adjacent_run_bound x ℓ hx hℓ (c - 1) N (L - 1) (by omega) (fun t h1 h2 => by
      refine ⟨by rw [hleft t h1 h2, hleft N le_rfl (by omega)], ?_⟩
      rw [show c - 1 + 1 = c by ring, hrun t h1 (by omega), hrun N le_rfl (by omega)])
    push_cast [Nat.cast_sub (show 1 ≤ L by omega)] at this
    omega
  | false =>
    -- column `c + 1` can only switch from white to black on the window
    have hmono : ∀ t, N ≤ t → t < N + L →
        evolve x t (c + 1) = true → evolve x (t + 1) (c + 1) = true := by
      intro t h1 h2 h
      rw [evolve_succ, show c + 1 - 1 = c by ring, hrun t h1 (by omega), hb, h]
      rfl
    have hstay : ∀ s, N ≤ s → ∀ t, s ≤ t → t ≤ N + L →
        evolve x s (c + 1) = true → evolve x t (c + 1) = true := by
      intro s hs t ht htL h
      induction t, ht using Nat.le_induction with
      | base => exact h
      | succ t ht ih => exact hmono t (by omega) (by omega) (ih (by omega))
    by_contra hL
    push_neg at hL
    set d := (c - ℓ + N).toNat with hd
    have hd' : (d : ℤ) = c - ℓ + N := by rw [hd]; omega
    set M := N + (d + 2) with hM
    cases hM' : evolve x M (c + 1) with
    | false =>
      -- column `c + 1` is white on `[N, M]`
      have hwhite : ∀ t, N ≤ t → t ≤ M → evolve x t (c + 1) = false := by
        intro t h1 h2
        by_contra h
        have := hstay t h1 M h2 (by omega) (by simpa using h)
        rw [hM'] at this; exact absurd this (by decide)
      have := adjacent_run_bound x ℓ hx hℓ c N (d + 2) (by omega) (fun t h1 h2 =>
        ⟨by rw [hrun t h1 (by omega)],
          by rw [hwhite t h1 (by omega), hwhite N le_rfl (by omega)]⟩)
      push_cast at this; omega
    | true =>
      -- column `c + 1` is black on `[M, N + L]`
      have hblack : ∀ t, M ≤ t → t ≤ N + L → evolve x t (c + 1) = true :=
        fun t h1 h2 => hstay M (by omega) t h1 h2 hM'
      have := adjacent_run_bound x ℓ hx hℓ c M (N + L - M) (by omega) (fun t h1 h2 =>
        ⟨by rw [hrun t (by omega) (by omega), hrun M (by omega) (by omega)],
          by rw [hblack t h1 (by omega), hblack M le_rfl (by omega)]⟩)
      push_cast [Nat.cast_sub (show M ≤ N + L by omega)] at this
      omega

/-- **For the centre column: every window `[N, 4N + 6]` contains a colour change.**
Equivalently, a run of equal centre-column values that starts at time `N` has length at most
`3N + 6`. -/
theorem centerCol_change_in_window (N : ℕ) :
    ∃ t, N ≤ t ∧ t < 4 * N + 6 ∧ centerCol (t + 1) ≠ centerCol t := by
  by_contra h
  push_neg at h
  have hrun : ∀ t, N ≤ t → t ≤ N + (3 * N + 6) → evolve seed t 0 = evolve seed N 0 := by
    intro t h1 h2
    induction t, h1 using Nat.le_induction with
    | base => rfl
    | succ t ht ih => exact (h t ht (by omega)).trans (ih (by omega))
  have := column_run_bound seed 0 (fun j hj => by simp [seed]; omega) (by simp [seed]) 0 N
    (3 * N + 6) (by omega) hrun
  push_cast at this
  omega

end GLM.Rule30
