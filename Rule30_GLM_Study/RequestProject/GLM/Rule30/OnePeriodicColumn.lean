module

public import RequestProject.GLM.Rule30.SeedBoundary

/-!
# Problem 1, partial result: at most one column is eventually periodic

Jen's theorem (`not_both_adjacent_columns_periodic`) says that two **adjacent** columns are never
both eventually periodic. Here it is extended to **any** two distinct columns:

* `not_both_columns_periodic` : for a row that is white on `(-∞, ℓ)` and black at `ℓ`, two
  distinct columns `c ≠ d` are never both eventually periodic.
* `seed_at_most_one_periodic_column` : for Wolfram's single black cell, **at most one column is
  eventually periodic**.
* `problem1_iff_centre_not_the_exception` : so Problem 1 says exactly that the centre is not that
  one exceptional column; `problem1_of_other_periodic_column` : if any column `c ≠ 0` were shown
  to be eventually periodic, Problem 1 would follow.

The argument: if columns `c` and `c + m + 2` are both eventually periodic, then the `m + 1`
columns strictly between them form a finite register (`m + 1` bits) driven by an eventually
periodic input (the two outer columns). A finite-state machine with eventually periodic input has
eventually periodic output (`Transducer.output_eventuallyPeriodic`), so column `c + 1` is
eventually periodic too, and columns `c`, `c + 1` contradict Jen's theorem.
-/

@[expose] public section

namespace GLM.Rule30

/-- The cell `c + j` of a window `[c, c + m + 2]`, read from the two boundary values `l`, `r`
and the interior register `s` (columns `c + 1, …, c + m + 1`). -/
def windowCell (m : ℕ) (s : Fin (m + 1) → Bool) (l r : Bool) (j : ℕ) : Bool :=
  if j = 0 then l else if h : j ≤ m + 1 then s ⟨j - 1, by omega⟩ else r

/-- The interior of a window `[c, c + m + 2]` as a finite transducer driven by the two
boundary columns. Its output is the column `c + 1`. -/
def windowTransducer (x : Config) (c : ℤ) (m : ℕ) : Transducer (Fin (m + 1) → Bool) (Bool × Bool) where
  init := fun i => x (c + 1 + i.val)
  next := fun s lr i =>
    rule30 (windowCell m s lr.1 lr.2 i.val) (windowCell m s lr.1 lr.2 (i.val + 1))
      (windowCell m s lr.1 lr.2 (i.val + 2))
  out := fun s => s 0

/-- The transducer tracks the actual interior columns. -/
theorem windowTransducer_run (x : Config) (c : ℤ) (m : ℕ) (t : ℕ) :
    (windowTransducer x c m).run (fun t => (evolve x t c, evolve x t (c + m + 2))) t =
      fun i => evolve x t (c + 1 + i.val) := by
  induction t with
  | zero => rfl
  | succ t ih =>
    funext i
    rw [Transducer.run, ih]
    simp only [windowTransducer]
    rw [evolve_succ]
    have hcell : ∀ j : ℕ, j ≤ m + 2 →
        windowCell m (fun i : Fin (m + 1) => evolve x t (c + 1 + i.val))
          (evolve x t c) (evolve x t (c + m + 2)) j = evolve x t (c + j) := by
      intro j hj
      unfold windowCell
      split_ifs with h0 h1
      · subst h0; simp
      · beta_reduce; congr 1; push_cast [Nat.cast_sub (show 1 ≤ j by omega)]; ring
      · congr 1; omega
    have hi := i.isLt
    rw [hcell _ (by omega), hcell _ (by omega), hcell _ (by omega)]
    push_cast
    congr 2 <;> ring

/-- Two eventually periodic sequences have a common period and a common starting time. -/
theorem pair_eventuallyPeriodic {a b : ℕ → Bool} (ha : EventuallyPeriodic a)
    (hb : EventuallyPeriodic b) :
    ∃ p > 0, ∃ T, ∀ t ≥ T, (a (t + p), b (t + p)) = (a t, b t) := by
  obtain ⟨p₁, hp₁, N₁, h₁⟩ := ha
  obtain ⟨p₂, hp₂, N₂, h₂⟩ := hb
  refine ⟨p₁ * p₂, Nat.mul_pos hp₁ hp₂, max N₁ N₂, fun t ht => ?_⟩
  have e₁ := periodic_mul h₁ p₂ t (le_trans (le_max_left _ _) ht)
  have e₂ := periodic_mul h₂ p₁ t (le_trans (le_max_right _ _) ht)
  rw [Prod.mk.injEq]
  exact ⟨by simpa [mul_comm] using e₁, e₂⟩

/-- If columns `c` and `c + m + 2` are both eventually periodic, so is column `c + 1`. -/
theorem column_periodic_of_window (x : Config) (c : ℤ) (m : ℕ)
    (h₁ : EventuallyPeriodic (fun t => evolve x t c))
    (h₂ : EventuallyPeriodic (fun t => evolve x t (c + m + 2))) :
    EventuallyPeriodic (fun t => evolve x t (c + 1)) := by
  have := (windowTransducer x c m).output_eventuallyPeriodic
    (fun t => (evolve x t c, evolve x t (c + m + 2))) (pair_eventuallyPeriodic h₁ h₂)
  have heq : (windowTransducer x c m).output
      (fun t => (evolve x t c, evolve x t (c + m + 2))) = fun t => evolve x t (c + 1) := by
    funext t
    rw [Transducer.output, windowTransducer_run]
    simp [windowTransducer]
  rwa [heq] at this

/-- **Two distinct columns are never both eventually periodic** (for any row that is white on
`(-∞, ℓ)` and black at `ℓ`). -/
theorem not_both_columns_periodic (x : Config) (ℓ : ℤ)
    (hx : ∀ j, j < ℓ → x j = false) (hℓ : x ℓ = true) {c d : ℤ} (hcd : c ≠ d) :
    ¬ (EventuallyPeriodic (fun t => evolve x t c) ∧ EventuallyPeriodic (fun t => evolve x t d)) := by
  -- reduce to `c < d`
  wlog hlt : c < d generalizing c d
  · exact fun h => this (Ne.symm hcd) (by omega) ⟨h.2, h.1⟩
  rintro ⟨hc, hd⟩
  rcases Int.lt_iff_add_one_le.mp hlt |>.eq_or_lt with h | h
  · exact not_both_adjacent_columns_periodic x ℓ hx hℓ c ⟨hc, h ▸ hd⟩
  · obtain ⟨m, hm⟩ : ∃ m : ℕ, d = c + m + 2 := ⟨(d - c - 2).toNat, by omega⟩
    subst hm
    exact not_both_adjacent_columns_periodic x ℓ hx hℓ c
      ⟨hc, column_periodic_of_window x c m hc hd⟩

/-- **For Wolfram's single black cell, at most one column is eventually periodic.** -/
theorem seed_at_most_one_periodic_column {c d : ℤ}
    (hc : EventuallyPeriodic (fun t => evolve seed t c))
    (hd : EventuallyPeriodic (fun t => evolve seed t d)) : c = d := by
  by_contra hcd
  exact not_both_columns_periodic seed 0 (fun j hj => by simp [seed]; omega) (by simp [seed])
    hcd ⟨hc, hd⟩

/-- **Problem 1 restated:** it says exactly that the centre is not the (at most one) exceptional
eventually periodic column, i.e. that every eventually periodic column (if any) is off-centre. -/
theorem problem1_iff_centre_not_the_exception :
    Problem1 ↔ ∀ c : ℤ, EventuallyPeriodic (fun t => evolve seed t c) → c ≠ 0 := by
  constructor
  · intro h c hc hc0
    subst hc0
    exact h hc
  · intro h hp
    exact h 0 hp rfl

/-- If **any** off-centre column were shown to be eventually periodic, Problem 1 would follow. -/
theorem problem1_of_other_periodic_column {c : ℤ} (hc0 : c ≠ 0)
    (hc : EventuallyPeriodic (fun t => evolve seed t c)) : Problem1 := fun h =>
  hc0 (seed_at_most_one_periodic_column hc h)

end GLM.Rule30
