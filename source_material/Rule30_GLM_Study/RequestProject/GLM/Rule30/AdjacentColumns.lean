module

public import RequestProject.GLM.Rule30.ConeSeparation

/-!
# Problem 1, partial result: two adjacent columns are never both eventually periodic

This is the theorem usually attributed to Erica Jen (1986), proved here directly from the
cone-separation invariant (left-permutivity), and in a slightly more general form: it holds
for **every** starting row that is white far to the left and not entirely white (in
particular for Wolfram's single black cell).

The argument: if columns `c` and `c+1` were both periodic with period `p` from time `N` on,
then `evolve_solve_left` (which is the cone separation read backwards) makes every column to
the left periodic with the same `p` and the *same* `N`.  But far to the left the light-cone
edge arrives at time `N + p` exactly — the column is white at time `N` and black at time
`N + p`, contradicting periodicity.

This is genuinely about the specific seed: without the "white on the left" hypothesis the
statement is false (see `periodic_columns_exist` below, built from the stationary left wall).
-/

@[expose] public section

namespace GLM.Rule30

/-- `a` is eventually periodic: `a (n + p) = a n` for all `n ≥ N`, for some `p > 0`. -/
def EventuallyPeriodic (a : ℕ → Bool) : Prop :=
  ∃ p > 0, ∃ N, ∀ n ≥ N, a (n + p) = a n

theorem periodic_mul {a : ℕ → Bool} {p N : ℕ} (h : ∀ n ≥ N, a (n + p) = a n) (k : ℕ) :
    ∀ n ≥ N, a (n + k * p) = a n := by
  induction k with
  | zero => simp
  | succ k ih =>
    intro n hn
    rw [show n + (k + 1) * p = (n + k * p) + p by ring, h _ (by omega), ih n hn]

/-- **Two adjacent columns are never both eventually periodic** (for any row that is white
on `(-∞, ℓ)` and black at `ℓ`). -/
theorem not_both_adjacent_columns_periodic (x : Config) (ℓ : ℤ)
    (hx : ∀ j, j < ℓ → x j = false) (hℓ : x ℓ = true) (c : ℤ) :
    ¬ (EventuallyPeriodic (fun t => evolve x t c) ∧
        EventuallyPeriodic (fun t => evolve x t (c + 1))) := by
  rintro ⟨⟨p₁, hp₁, N₁, h₁⟩, ⟨p₂, hp₂, N₂, h₂⟩⟩
  -- a common period and a common starting time
  set p := p₁ * p₂ with hp
  set N := max N₁ N₂
  have hp0 : 0 < p := Nat.mul_pos hp₁ hp₂
  have g₁ : ∀ t ≥ N, evolve x (t + p) c = evolve x t c := by
    intro t ht
    have := periodic_mul (a := fun t => evolve x t c) h₁ p₂ t (le_trans (le_max_left _ _) ht)
    simpa [hp, mul_comm] using this
  have g₂ : ∀ t ≥ N, evolve x (t + p) (c + 1) = evolve x t (c + 1) := by
    intro t ht
    exact periodic_mul (a := fun t => evolve x t (c + 1)) h₂ p₁ t (le_trans (le_max_right _ _) ht)
  -- periodicity propagates to every column on the left, with the same `p` and `N`
  have prop : ∀ k : ℕ, ∀ t ≥ N, evolve x (t + p) (c - k) = evolve x t (c - k) ∧
      evolve x (t + p) (c + 1 - k) = evolve x t (c + 1 - k) := by
    intro k
    induction k with
    | zero => intro t ht; simp [g₁ t ht, g₂ t ht]
    | succ k ih =>
      intro t ht
      refine ⟨?_, ?_⟩
      · have e : c - ↑(k + 1) = (c - k) - 1 := by push_cast; ring
        rw [e, evolve_solve_left, evolve_solve_left, show t + p + 1 = (t + 1) + p by ring,
          (ih (t + 1) (by omega)).1, (ih t ht).1, show c - ↑k + 1 = c + 1 - k by ring,
          (ih t ht).2]
      · rw [show c + 1 - ↑(k + 1) = c - k by push_cast; ring]; exact (ih t ht).1
  -- far to the left, the light-cone edge breaks periodicity
  set m := N + (ℓ - c).toNat
  obtain ⟨k, hk⟩ : ∃ k : ℕ, ℓ - ((m + p : ℕ) : ℤ) = c - k :=
    ⟨(c - ℓ + ((m + p : ℕ) : ℤ)).toNat, by push_cast; omega⟩
  have hper := (prop k m (by omega)).1
  rw [← hk, evolve_left_edge x ℓ hx hℓ (m + p),
    evolve_white_left x ℓ hx m _ (by push_cast; omega)] at hper
  exact absurd hper (by decide)

/-- **For Wolfram's single black cell: no two adjacent columns are both eventually
periodic.** -/
theorem seed_not_both_adjacent_columns_periodic (c : ℤ) :
    ¬ (EventuallyPeriodic (fun t => evolve seed t c) ∧
        EventuallyPeriodic (fun t => evolve seed t (c + 1))) :=
  not_both_adjacent_columns_periodic seed 0 (fun j hj => by simp [seed]; omega)
    (by simp [seed]) c

/-- **Consequence for Problem 1.** If the centre column were eventually periodic, then both
neighbouring columns (`-1` and `+1`) would have to be non-periodic. -/
theorem centerCol_periodic_forces_neighbours_aperiodic (h : EventuallyPeriodic centerCol) :
    ¬ EventuallyPeriodic (fun t => evolve seed t (-1)) ∧
      ¬ EventuallyPeriodic (fun t => evolve seed t 1) := by
  refine ⟨fun h' => seed_not_both_adjacent_columns_periodic (-1) ⟨h', ?_⟩,
    fun h' => seed_not_both_adjacent_columns_periodic 0 ⟨h, ?_⟩⟩
  · simpa using h
  · simpa using h'

/-- The hypothesis "white far to the left" cannot be dropped: from the stationary left
wall `…010101` every column `≤ 1` is constant, hence periodic. -/
theorem periodic_columns_exist :
    ∃ x : Config, ∀ c ≤ 0, EventuallyPeriodic (fun t => evolve x t c) ∧
      EventuallyPeriodic (fun t => evolve x t (c + 1)) := by
  refine ⟨leftWall (fun _ => false), fun c hc => ⟨⟨1, one_pos, 0, fun n _ => ?_⟩,
    ⟨1, one_pos, 0, fun n _ => ?_⟩⟩⟩
  · simp only; rw [left_wall_stationary _ _ _ (by omega), left_wall_stationary _ _ _ (by omega)]
  · simp only; rw [left_wall_stationary _ _ _ (by omega), left_wall_stationary _ _ _ (by omega)]

end GLM.Rule30
