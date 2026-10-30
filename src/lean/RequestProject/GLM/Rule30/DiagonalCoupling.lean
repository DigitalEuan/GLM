module

public import RequestProject.GLM.Rule30.Diagonals
public import RequestProject.GLM.Rule30.ColumnInverse
public import RequestProject.GLM.Rule30.FiniteState

/-!
# The diagonal coupling is not seed-specific: an audit of the "diagonal bridge"

`Diagonals.lean` proved that the right diagonals of the seed pattern satisfy the triangular
running-XOR recursion and have period `2^D`, and that the centre column reads diagonal `t` at
time `t`. A proposed bridge for Problems 1–3 is: *"because the centre column runs through
diagonals with unbounded periods, coupled triangularly, no finite-state predictor can lock on and
no circuit can compress it."*

This file shows that this inference is **not valid** as it stands, using Rule 30 itself:

* `rdiagOf x D t := a(t)(t − D)` for an arbitrary row `x`.
  - `rdiagOf_succ` : the same triangular recursion holds for **every** row.
  - `rdiagOf_periodic` : for **every** row that is white on `(0, ∞)` (like the seed), every right
    diagonal is periodic with period `2^D`.
  - `rdiagOf_zero` : the only freedom is the initial data `rdiagOf x D 0 = x (−D)`.
  - `centre_eq_rdiagOf` : the centre column always reads diagonal `t` at time `t`.
* `diagonal_coupling_does_not_decide_problem1` : there is a right-white row with **all** of this
  structure whose centre column is `1, 0, 1, 0, …` (periodic, perfectly predictable by a 2-state
  observer).
* `diagonal_coupling_does_not_decide_problem2` : and one whose centre column has frequency `1/3`.
* `unbounded_periods_do_not_force_aperiodicity` : abstractly, a family of sequences with least
  periods exactly `2^D` (unbounded) can have a constant diagonal read-out.

Conclusion (formal): the triangular running-XOR coupling and the `2^D` periods hold for a whole
family of rows that includes counterexamples to Problems 1 and 2. A proof of P1/P2 along this
route **must use the seed's initial data** `rdiag D 0 = [D = 0]`
(`seed_is_unique_initial_data`), not just the recursion and the periods. The same rows refute the
analogous "periods ⇒ incompressibility" inference for Problem 3: their centre column `1,0,1,0,…`
is computable in constant time although it, too, is read off diagonals with the triangular
coupling.
-/

@[expose] public section

namespace GLM.Rule30

open Filter

/-- The `D`-th right diagonal of the space-time pattern of an arbitrary row `x`. -/
def rdiagOf (x : Config) (D : ℤ) (t : ℕ) : Bool := evolve x t (t - D)

theorem rdiagOf_seed : rdiagOf seed = rdiag := rfl

/-- **The triangular recursion holds for every row.** -/
theorem rdiagOf_succ (x : Config) (D : ℤ) (t : ℕ) :
    rdiagOf x D (t + 1) = xor (rdiagOf x D t) (rdiagOf x (D - 1) t || rdiagOf x (D - 2) t) := by
  unfold rdiagOf
  rw [evolve_succ]
  unfold rule30
  rw [show ((t + 1 : ℕ) : ℤ) - D - 1 = (t : ℤ) - D by push_cast; ring,
    show ((t + 1 : ℕ) : ℤ) - D + 1 = (t : ℤ) - (D - 2) by push_cast; ring,
    show ((t + 1 : ℕ) : ℤ) - D = (t : ℤ) - (D - 1) by push_cast; ring]

/-- The initial data of the diagonals is the left half of the row. -/
theorem rdiagOf_zero (x : Config) (D : ℤ) : rdiagOf x D 0 = x (-D) := by
  simp [rdiagOf]

/-- The centre column reads diagonal `t` at time `t`, for every row. -/
theorem centre_eq_rdiagOf (x : Config) (t : ℕ) : evolve x t 0 = rdiagOf x t t := by
  simp [rdiagOf]

/-- For a right-white row, diagonals with `D < 0` are white. -/
theorem rdiagOf_neg (x : Config) (hx : ∀ i, 0 < i → x i = false) {D : ℤ} (hD : D < 0) (t : ℕ) :
    rdiagOf x D t = false :=
  evolve_white_right x 0 hx t _ (by omega)

/-- **For every right-white row, every right diagonal has period `2^D`.** -/
theorem rdiagOf_periodic (x : Config) (hx : ∀ i, 0 < i → x i = false) (D : ℕ) :
    ∀ t, rdiagOf x D (t + 2 ^ D) = rdiagOf x D t := by
  induction D using Nat.strong_induction_on with
  | _ D ih =>
    rcases Nat.eq_zero_or_pos D with rfl | hD
    · intro t
      rw [pow_zero, rdiagOf_succ]
      simp only [Nat.cast_zero, zero_sub]
      rw [rdiagOf_neg x hx (D := -1) (by norm_num), rdiagOf_neg x hx (D := -2) (by norm_num)]
      simp
    · have hu : ∀ t, (rdiagOf x ((D : ℤ) - 1) (t + 2 ^ (D - 1)) ||
            rdiagOf x ((D : ℤ) - 2) (t + 2 ^ (D - 1)))
          = (rdiagOf x ((D : ℤ) - 1) t || rdiagOf x ((D : ℤ) - 2) t) := by
        intro t
        have h1 : rdiagOf x ((D : ℤ) - 1) (t + 2 ^ (D - 1)) = rdiagOf x ((D : ℤ) - 1) t := by
          have := ih (D - 1) (by omega) t
          rwa [show ((D - 1 : ℕ) : ℤ) = (D : ℤ) - 1 by omega] at this
        have h2 : rdiagOf x ((D : ℤ) - 2) (t + 2 ^ (D - 1)) = rdiagOf x ((D : ℤ) - 2) t := by
          rcases Nat.lt_or_ge D 2 with hD2 | hD2
          · rw [rdiagOf_neg x hx (by omega), rdiagOf_neg x hx (by omega)]
          · have := periodic_nat_mul (f := rdiagOf x ((D : ℤ) - 2)) (q := 2 ^ (D - 2)) (by
              intro s
              have := ih (D - 2) (by omega) s
              rwa [show ((D - 2 : ℕ) : ℤ) = (D : ℤ) - 2 by omega] at this) 2 t
            rwa [show 2 * 2 ^ (D - 2) = 2 ^ (D - 1) by
              rw [← pow_succ']; congr 1; omega] at this
        rw [h1, h2]
      have := runningXor_periodic (v := rdiagOf x (D : ℤ))
        (u := fun t => rdiagOf x ((D : ℤ) - 1) t || rdiagOf x ((D : ℤ) - 2) t) (q := 2 ^ (D - 1))
        (fun t => rdiagOf_succ x _ t) hu
      intro t
      rw [show 2 ^ D = 2 * 2 ^ (D - 1) by rw [← pow_succ']; congr 1; omega]
      exact this t

/-- All the diagonal structure used by the "diagonal bridge", for a row `x`. -/
def HasDiagonalStructure (x : Config) : Prop :=
  (∀ D : ℤ, D < 0 → ∀ t, rdiagOf x D t = false) ∧
  (∀ (D : ℤ) t, rdiagOf x D (t + 1) = xor (rdiagOf x D t) (rdiagOf x (D - 1) t || rdiagOf x (D - 2) t)) ∧
  (∀ (D : ℕ) t, rdiagOf x D (t + 2 ^ D) = rdiagOf x D t) ∧
  (∀ t, evolve x t 0 = rdiagOf x t t)

/-- Every right-white row has the diagonal structure. -/
theorem hasDiagonalStructure_of_rightWhite (x : Config) (hx : ∀ i, 0 < i → x i = false) :
    HasDiagonalStructure x :=
  ⟨fun _ hD t => rdiagOf_neg x hx hD t, rdiagOf_succ x, rdiagOf_periodic x hx, centre_eq_rdiagOf x⟩

/-- The seed has it (this is `Diagonals.lean`). -/
theorem seed_hasDiagonalStructure : HasDiagonalStructure seed :=
  hasDiagonalStructure_of_rightWhite seed (fun i hi => by simp [seed]; omega)

/-- **The diagonal structure does not decide Problem 1.** Some row has the full diagonal structure
and the periodic centre column `1, 0, 1, 0, …`, which a 2-state observer predicts perfectly. -/
theorem diagonal_coupling_does_not_decide_problem1 :
    ∃ x : Config, HasDiagonalStructure x ∧ EventuallyPeriodic (fun t => evolve x t 0) ∧
      ∃ n, ∃ O : FSObserver (Fin n), ∀ t, O.predict t (fun t => evolve x t 0) = evolve x t 0 := by
  obtain ⟨x, hx, -, hper⟩ := exists_row_with_periodic_column
  exact ⟨x, hasDiagonalStructure_of_rightWhite x hx, hper,
    exists_fsObserver_of_eventuallyPeriodic _ hper⟩

/-- **The diagonal structure does not decide Problem 2.** Some row has the full diagonal structure
and a centre column of frequency `1/3`. -/
theorem diagonal_coupling_does_not_decide_problem2 :
    ∃ x : Config, HasDiagonalStructure x ∧ ¬ HasFrequencyHalf (fun t => evolve x t 0) := by
  obtain ⟨x, hx, -, hb⟩ := exists_row_with_biased_column
  exact ⟨x, hasDiagonalStructure_of_rightWhite x hx, hb⟩

/-- **What singles out the seed is its initial data.** Among right-white rows, the diagonal
initial data `rdiagOf x D 0 = [D = 0]` holds only for the seed, and the seed is the only
right-white row producing Rule 30's centre column. -/
theorem seed_is_unique_initial_data (x : Config) (hx : ∀ i, 0 < i → x i = false) :
    ((∀ D : ℕ, rdiagOf x D 0 = decide (D = 0)) ↔ x = seed) ∧
      ((∀ t, evolve x t 0 = centerCol t) → x = seed) := by
  refine ⟨⟨fun h => funext fun i => ?_, fun h D => by subst h; simp [rdiagOf, seed]⟩,
    seed_unique_preimage x hx⟩
  rcases lt_or_ge 0 i with hi | hi
  · rw [hx i hi]; simp [seed]; omega
  · have := h i.natAbs
    rw [rdiagOf_zero, show -((i.natAbs : ℕ) : ℤ) = i by omega] at this
    rw [this]; simp [seed]

/-- **Unbounded periods alone force nothing.** A family of sequences `d D` with least period
exactly `2^D` (so the periods are unbounded), whose diagonal read-out `t ↦ d t t` is constant. -/
theorem unbounded_periods_do_not_force_aperiodicity :
    ∃ d : ℕ → ℕ → Bool,
      (∀ D t, d D (t + 2 ^ D) = d D t) ∧
      (∀ D p, 1 ≤ D → 0 < p → p < 2 ^ D → ¬ ∀ t, d D (t + p) = d D t) ∧
      (∀ t, d t t = false) := by
  refine ⟨fun D t => decide (1 ≤ D ∧ t % 2 ^ D = 0), fun D t => by simp, ?_, fun t => ?_⟩
  · intro D p hD hp hpD h
    have := h 0
    simp only [zero_add, Nat.zero_mod, decide_eq_decide] at this
    have h2 : p % 2 ^ D = p := Nat.mod_eq_of_lt hpD
    have h3 := (this.mpr ⟨hD, trivial⟩).2
    omega
  · have : t < 2 ^ t := Nat.lt_two_pow_self
    simp only [decide_eq_false_iff_not, not_and]
    intro ht
    rw [Nat.mod_eq_of_lt this]; omega

end GLM.Rule30
