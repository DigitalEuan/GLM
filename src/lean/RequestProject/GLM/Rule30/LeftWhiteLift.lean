module

public import RequestProject.GLM.Rule30.NoConstantColumn
public import RequestProject.GLM.Rule30.OnePeriodicColumn

/-!
# Round 13: lifting Problem 1 from the seed to every row of the stack

Problem 1 is a statement about **one** row (Wolfram's single black cell).  Every row of its
space-time diagram ("the stack") is again a row that is white to the left of a black cell: a
*left-white* row.  The period-1 case of Problem 1 (Round 7) was in fact proved for **every**
left-white row, not only for the seed.  This file names the lifted statement and connects it to
Problem 1 and to the GLM's propose-and-check loop.

* `IsLeftWhite x` — `x` is white on `(-∞, ℓ)` and black at `ℓ`, for some `ℓ`.
* `LeftWhiteAperiodic p` — no column of any left-white row is periodic with period `p` from some
  time on.
* `isLeftWhite_evolve` — the class is closed under the rule: every row of the stack of a
  left-white row is left-white.  So a statement about all left-white rows can be applied at any
  row of the stack (`leftWhiteAperiodic_iff_from_start`: the time `N` may always be taken `0`).
* `leftWhiteAperiodic_one` — the period-1 case (proved, Round 7).
* `leftWhiteAperiodic_of_mul` — period `p` is implied by period `p·k`; so it is enough to know the
  statement for a cofinal family such as the factorials (`problem1_of_leftWhiteAperiodic_factorial`).
* `problem1_of_leftWhiteAperiodic` — **if `LeftWhiteAperiodic p` holds for every `p ≥ 1`, then
  Problem 1 holds.**

## The quantitative form and the propose-and-check loop

* `RunBound p B` — in a left-white row, a column at distance `d` from the black edge cannot stay
  `p`-periodic for more than `B d` steps.
* `runBound_one` — `RunBound 1 (3d + 5)` (proved, Round 7's run bound).
* `leftWhiteAperiodic_of_runBound` — a run bound implies the qualitative statement.
* `Refutes a p N t` — the observation at time `t` refutes the proposal "the column has period `p`
  from time `N` on".  `problem1_iff_every_proposal_refuted`: Problem 1 says every proposal is
  eventually refuted.  `refutation_horizon_of_runBound`: with a run bound, the refutation of the
  proposal `(p, N)` arrives by time `N + B N + 1`, so the loop is guaranteed to terminate.  For
  `p = 1` this is proved (`refutation_horizon_one`).
-/

@[expose] public section

namespace GLM.Rule30

/-- Evolving `s` steps and then `t` more. -/
theorem evolve_evolve (x : Config) (s t : ℕ) : evolve (evolve x s) t = evolve x (s + t) := by
  induction t with
  | zero => rfl
  | succ t ih => funext c; rw [evolve_succ, ih, show s + (t + 1) = (s + t) + 1 by ring, evolve_succ]

/-- A row is *left-white* if it is white on `(-∞, ℓ)` and black at `ℓ`. -/
def IsLeftWhite (x : Config) : Prop := ∃ ℓ : ℤ, (∀ j, j < ℓ → x j = false) ∧ x ℓ = true

theorem isLeftWhite_seed : IsLeftWhite seed :=
  ⟨0, fun j hj => by simp [seed]; omega, by simp [seed]⟩

/-- **The class is closed under the rule:** every row of the stack of a left-white row is
left-white (its edge moves left at speed one). -/
theorem isLeftWhite_evolve {x : Config} (hx : IsLeftWhite x) (t : ℕ) : IsLeftWhite (evolve x t) := by
  obtain ⟨ℓ, hw, hb⟩ := hx
  exact ⟨ℓ - t, fun j hj => evolve_white_left x ℓ hw t j hj, evolve_left_edge x ℓ hw hb t⟩

/-- The class is closed under translation. -/
theorem isLeftWhite_shift {x : Config} (hx : IsLeftWhite x) (d : ℤ) :
    IsLeftWhite (fun j => x (j + d)) := by
  obtain ⟨ℓ, hw, hb⟩ := hx
  exact ⟨ℓ - d, fun j hj => hw _ (by omega), by simpa using hb⟩

/-- Column `c` of the run from `x` is periodic with period `p` from time `N` on. -/
def ColumnPeriodicFrom (x : Config) (c : ℤ) (p N : ℕ) : Prop :=
  ∀ t ≥ N, evolve x (t + p) c = evolve x t c

/-- **The lifted statement for period `p`:** no column of any left-white row is periodic with
period `p` from some time on. -/
def LeftWhiteAperiodic (p : ℕ) : Prop :=
  ∀ x, IsLeftWhite x → ∀ (c : ℤ) (N : ℕ), ¬ ColumnPeriodicFrom x c p N

/-- **Stack invariance:** the lifted statement may be checked from the first row of the run only,
because every later row of the stack is again left-white. -/
theorem leftWhiteAperiodic_iff_from_start (p : ℕ) :
    LeftWhiteAperiodic p ↔ ∀ x, IsLeftWhite x → ∀ c : ℤ, ¬ ColumnPeriodicFrom x c p 0 := by
  constructor
  · intro h x hx c; exact h x hx c 0
  · intro h x hx c N hper
    refine h (evolve x N) (isLeftWhite_evolve hx N) c (fun t _ => ?_)
    rw [evolve_evolve, evolve_evolve, show N + (t + p) = (N + t) + p by ring]
    exact hper (N + t) (by omega)

/-- **Period 1 (proved):** no column of a left-white row is eventually constant. -/
theorem leftWhiteAperiodic_one : LeftWhiteAperiodic 1 := by
  rintro x ⟨ℓ, hw, hb⟩ c N hper
  refine column_not_eventually_constant x ℓ hw hb c ⟨evolve x N c, N, fun t ht => ?_⟩
  induction t, ht using Nat.le_induction with
  | base => rfl
  | succ t ht ih => rw [hper t ht, ih]

/-- Period `p` implies period `p * k`, so the lifted statement for `p * k` gives it for `p`. -/
theorem leftWhiteAperiodic_of_mul {p k : ℕ} (h : LeftWhiteAperiodic (p * k)) :
    LeftWhiteAperiodic p := by
  intro x hx c N hper
  exact h x hx c N (fun t ht => by
    rw [mul_comm]; exact periodic_mul (a := fun t => evolve x t c) hper k t ht)

/-- **The lift implies Problem 1.** -/
theorem problem1_of_leftWhiteAperiodic (h : ∀ p, 0 < p → LeftWhiteAperiodic p) : Problem1 := by
  rintro ⟨p, hp, N, hN⟩
  exact h p hp seed isLeftWhite_seed 0 N hN

/-- It suffices to know the lifted statement for the factorials `1!, 2!, 3!, …`. -/
theorem problem1_of_leftWhiteAperiodic_factorial
    (h : ∀ k : ℕ, LeftWhiteAperiodic (k + 1).factorial) : Problem1 := by
  refine problem1_of_leftWhiteAperiodic fun p hp => ?_
  obtain ⟨k, hk⟩ := Nat.dvd_factorial hp (le_refl p)
  obtain ⟨q, rfl⟩ : ∃ q, p = q + 1 := ⟨p - 1, by omega⟩
  exact leftWhiteAperiodic_of_mul (k := k) (hk ▸ h q)

/-! ## The quantitative form: run bounds -/

/-- **Run bound for period `p`.** In a left-white row with edge `ℓ`, the column at distance `d`
from the edge cannot be `p`-periodic on the time window `[0, L]` unless `L ≤ B d`. -/
def RunBound (p : ℕ) (B : ℕ → ℕ) : Prop :=
  ∀ (x : Config) (ℓ : ℤ), (∀ j, j < ℓ → x j = false) → x ℓ = true →
    ∀ d L : ℕ, (∀ t, t + p ≤ L → evolve x (t + p) (ℓ + d) = evolve x t (ℓ + d)) → L ≤ B d

/-- **Period 1:** a column at distance `d` from the edge is constant for at most `3d + 5` steps. -/
theorem runBound_one : RunBound 1 (fun d => 3 * d + 5) := by
  intro x ℓ hw hb d L hrun
  have hconst : ∀ t, 0 ≤ t → t ≤ 0 + L → evolve x t (ℓ + d) = evolve x 0 (ℓ + d) := by
    intro t _ ht
    induction t with
    | zero => rfl
    | succ t ih => rw [hrun t (by omega), ih (by omega) (by omega)]
  have := column_run_bound x ℓ hw hb (ℓ + d) 0 L (by omega) hconst
  push_cast at this
  show L ≤ 3 * d + 5
  omega

/-- **A run bound implies the lifted statement.** -/
theorem leftWhiteAperiodic_of_runBound {p : ℕ} {B : ℕ → ℕ} (h : RunBound p B) :
    LeftWhiteAperiodic p := by
  rintro x ⟨ℓ, hw, hb⟩ c N hper
  -- move to a row `M ≥ N` of the stack whose edge `ℓ - M` lies left of `c`
  set M : ℕ := N + (ℓ - c).toNat with hM
  set y := evolve x M
  have hyw : ∀ j, j < ℓ - M → y j = false := fun j hj => evolve_white_left x ℓ hw M j hj
  have hyb : y (ℓ - M) = true := evolve_left_edge x ℓ hw hb M
  set d : ℕ := (c - (ℓ - M)).toNat with hd
  have hc : ℓ - M + d = c := by rw [hd]; omega
  have := h y (ℓ - M) hyw hyb d (B d + 1) (fun t _ => by
    simp only [y]
    rw [evolve_evolve, evolve_evolve, hc, show M + (t + p) = (M + t) + p by ring]
    exact hper (M + t) (by omega))
  omega

/-! ## The propose-and-check loop on the centre column -/

/-- The observation at time `t` refutes the proposal "`a` has period `p` from time `N` on". -/
def Refutes (a : ℕ → Bool) (p N t : ℕ) : Prop := N ≤ t ∧ a (t + p) ≠ a t

/-- **Problem 1 as a propose-and-check loop:** every proposal `(p, N)` with `p ≥ 1` is eventually
refuted by an observation of the centre column. -/
theorem problem1_iff_every_proposal_refuted :
    Problem1 ↔ ∀ p, 0 < p → ∀ N, ∃ t, Refutes centerCol p N t := by
  constructor
  · intro h p hp N
    by_contra hne
    push_neg at hne
    exact h ⟨p, hp, N, fun t ht => by
      by_contra h'; exact hne t ⟨ht, h'⟩⟩
  · rintro h ⟨p, hp, N, hN⟩
    obtain ⟨t, ht, hne⟩ := h p hp N
    exact hne (hN t ht)

/-- **A run bound gives the loop a horizon:** the proposal `(p, N)` is refuted by time
`N + B N + 1`. (Row `N` of the seed's stack has its edge at `-N`, so the centre is at distance
`N` from it.) -/
theorem refutation_horizon_of_runBound {p : ℕ} {B : ℕ → ℕ} (h : RunBound p B) (N : ℕ) :
    ∃ t, Refutes centerCol p N t ∧ t + p ≤ N + B N + 1 := by
  by_contra hne
  push_neg at hne
  have hyw : ∀ j, j < -(N : ℤ) → evolve seed N j = false :=
    fun j hj => evolve_white_left seed 0 (fun j hj => by simp [seed]; omega) N j (by omega)
  have hyb : evolve seed N (-(N : ℤ)) = true := evolve_seed_left_edge N
  have := h (evolve seed N) (-(N : ℤ)) hyw hyb N (B N + 1) (fun t ht => by
    rw [evolve_evolve, evolve_evolve, show (-(N : ℤ) + (N : ℤ)) = 0 by ring,
      show N + (t + p) = (N + t) + p by ring]
    by_contra hne'
    exact absurd (hne (N + t) ⟨by omega, hne'⟩) (by omega))
  omega

/-- **The loop terminates for period 1 (proved):** the proposal "constant from time `N`" is
refuted by time `4N + 6`. -/
theorem refutation_horizon_one (N : ℕ) :
    ∃ t, Refutes centerCol 1 N t ∧ t + 1 ≤ 4 * N + 6 := by
  obtain ⟨t, h1, h2⟩ := refutation_horizon_of_runBound runBound_one N
  exact ⟨t, h1, by omega⟩

end GLM.Rule30
