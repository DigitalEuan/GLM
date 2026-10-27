module

public import RequestProject.GLM.Rule30.Diagonals
public import RequestProject.GLM.Rule30.Prizes

/-!
# The seed's boundary data, and the "periodically driven shift register" proposal

Round 6 audit of feedback #1 (the "NLFSR bridge").  All results are proved.

**The edges of the seed pattern.**
* `evolve_seed_right_edge` / `rdiag_zero_eq_true` : the right edge `a(t)(t)` of the seed pattern is
  always **black** (diagonal `0` is constantly `1`, not `0` as the proposal assumed).
* `rdiag_one_eq` : the first inner right diagonal alternates `0,1,0,1,…` (`= t mod 2`).
* The right-diagonal system is **autonomous**: diagonal `D` is driven only by diagonals `D−1`,
  `D−2` (`rdiag_succ`, in `Diagonals.lean`).  There is no "left input" entering it; the left edge
  `a(t)(−t)` is also constantly black (`evolve_seed_left_edge`).

**The seed's value is the linear ANF coefficient (feedback #1, Track B).**
* `seed_value_eq_linear_coeff` : for every position `c`, the seed value `a(n)(c)` is the ANF
  coefficient of the single monomial `x₀` in the map `x ↦ a(n)(c)`.  This is true, but it is
  the evaluation of a polynomial with zero constant term at the unit vector `e₀`, so it carries no
  extra information: the centre column *is* the sequence of linear coefficients, by definition.
  It is unrelated to `whiteDiagonalCount` (which computes the *top* coefficient, a map property).

**A fixed-size shift register with periodic input cannot produce an aperiodic column.**
* `Transducer` : a finite-state machine reading an input stream (an NLFSR/filter generator with a
  finite register is one).
* `Transducer.output_eventuallyPeriodic` : if the state set is finite and the input is eventually
  periodic, the output is eventually periodic.
* `problem1_no_finite_driven_register` : so **if Problem 1 holds**, the centre column is *not* the
  output of any finite-state machine driven by an eventually periodic input.  The "NLFSR caught
  between a periodic edge and a zero edge" picture therefore needs an *unbounded* register; with an
  unbounded register it is exactly the diagonal read-out of `Diagonals.lean`, whose limits were
  established in `DiagonalCoupling.lean`.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-! ## The edges of the seed pattern -/

/-- Diagonal `0` (the right edge) is constantly black. -/
theorem rdiag_zero_eq_true (t : ℕ) : rdiag 0 t = true := by
  have := rdiag_mod 0 t
  simp only [pow_zero, Nat.mod_one, Nat.cast_zero] at this
  rw [this, rdiag_zero]; rfl

/-- **The right edge of the seed pattern is always black.** -/
theorem evolve_seed_right_edge (n : ℕ) : evolve seed n n = true := by
  have := rdiag_zero_eq_true n
  simpa [rdiag] using this

/-- The first inner right diagonal alternates: `a(t)(t − 1) = t mod 2`. -/
theorem rdiag_one_eq (t : ℕ) : rdiag 1 t = decide (t % 2 = 1) := by
  induction t with
  | zero => simp [rdiag_zero]
  | succ t ih =>
    rw [rdiag_succ, ih, show (1 : ℤ) - 1 = 0 by norm_num, rdiag_zero_eq_true]
    rcases Nat.mod_two_eq_zero_or_one t with h | h <;> simp [h, Nat.succ_mod_two_eq_one_iff]

/-! ## Seed value = linear ANF coefficient -/

/-- The all-white row is `ind ∅`, and `ind {0}` is the seed. -/
theorem ind_singleton_zero : ind {0} = seed := by
  funext c; simp [ind, seed]

/-- **The seed value is the linear ANF coefficient of `x₀`.** For every `n` and `c`, the bit
`a(n)(c)` of the seed pattern equals the coefficient of the monomial `x₀` in the ANF of the map
`x ↦ a(n)(c)`. -/
theorem seed_value_eq_linear_coeff (n : ℕ) (c : ℤ) :
    bz (evolve seed n c) = anfCoeff (fun x => evolve x n c) {0} := by
  unfold anfCoeff coeffZ
  have hps : ({0} : Finset ℤ).powerset = {∅, {0}} := by
    ext T; simp [Finset.subset_singleton_iff]
  rw [hps, Finset.sum_pair (by simp)]
  have h0 : ind (∅ : Finset ℤ) = fun _ => false := by funext c; simp [ind]
  rw [h0, ind_singleton_zero]
  simp [bz, evolve_false]

/-- The centre column is the sequence of linear coefficients. -/
theorem centerCol_eq_linear_coeff (n : ℕ) :
    bz (centerCol n) = anfCoeff (fun x => evolve x n 0) {0} :=
  seed_value_eq_linear_coeff n 0

/-! ## Finite-state machines driven by periodic input -/

/-- A finite-state transducer (Moore machine) reading an input stream over `α`. -/
structure Transducer (σ α : Type) where
  init : σ
  next : σ → α → σ
  out : σ → Bool

namespace Transducer

variable {σ α : Type} (M : Transducer σ α)

/-- The state after reading `u 0, …, u (t-1)`. -/
def run (u : ℕ → α) : ℕ → σ
  | 0 => M.init
  | t + 1 => M.next (run u t) (u t)

/-- The output stream. -/
def output (u : ℕ → α) (t : ℕ) : Bool := M.out (M.run u t)

/-- An autonomous map on a finite set: the orbit is eventually periodic. -/
theorem orbit_eventually_periodic {β : Type} [Finite β] (H : β → β) (z : ℕ → β)
    (hz : ∀ t, z (t + 1) = H (z t)) : ∃ q > 0, ∃ i, ∀ t ≥ i, z (t + q) = z t := by
  obtain ⟨i, j, hij, heq⟩ := Finite.exists_ne_map_eq_of_infinite z
  wlog hlt : i < j generalizing i j
  · exact this j i (Ne.symm hij) heq.symm (by omega)
  refine ⟨j - i, by omega, i, fun t ht => ?_⟩
  obtain ⟨m, rfl⟩ : ∃ m, t = i + m := ⟨t - i, by omega⟩
  induction m with
  | zero => rw [add_zero, show i + (j - i) = j by omega, heq]
  | succ m ih =>
    rw [show i + (m + 1) + (j - i) = (i + m + (j - i)) + 1 by omega, hz, ih (by omega), ← hz]
    rfl

theorem periodic_shift {u : ℕ → α} {p T : ℕ} (hu : ∀ t ≥ T, u (t + p) = u t) (m : ℕ) :
    u (T + m) = u (T + m % p) := by
  have key : ∀ k r, u (T + r + k * p) = u (T + r) := by
    intro k r
    induction k with
    | zero => simp
    | succ k ih =>
      rw [show T + r + (k + 1) * p = (T + r + k * p) + p by ring, hu _ (by omega), ih]
  conv_lhs => rw [← Nat.mod_add_div m p]
  rw [← add_assoc, mul_comm, key]

/-- **Periodic input ⇒ periodic output.** A finite-state transducer driven by an eventually
periodic input produces an eventually periodic output. -/
theorem output_eventuallyPeriodic [Finite σ] (u : ℕ → α)
    (hu : ∃ p > 0, ∃ T, ∀ t ≥ T, u (t + p) = u t) : EventuallyPeriodic (M.output u) := by
  obtain ⟨p, hp, T, hT⟩ := hu
  let H : σ × Fin p → σ × Fin p := fun z =>
    (M.next z.1 (u (T + z.2.val)), ⟨(z.2.val + 1) % p, Nat.mod_lt _ hp⟩)
  let z : ℕ → σ × Fin p := fun t => (M.run u (T + t), ⟨t % p, Nat.mod_lt _ hp⟩)
  have hz : ∀ t, z (t + 1) = H (z t) := by
    intro t
    simp only [z, H, Prod.mk.injEq]
    refine ⟨?_, ?_⟩
    · show M.next (M.run u (T + t)) (u (T + t)) = _
      rw [periodic_shift hT t]
    · ext
      simp only
      rw [Nat.add_mod, Nat.add_mod (t % p) 1 p, Nat.mod_mod]
  obtain ⟨q, hq, i, hi⟩ := orbit_eventually_periodic H z hz
  refine ⟨q, hq, T + i, fun n hn => ?_⟩
  have := congrArg Prod.fst (hi (n - T) (by omega))
  simp only [z] at this
  rw [show T + (n - T + q) = n + q by omega, show T + (n - T) = n by omega] at this
  simp only [output, this]

end Transducer

/-- **If Problem 1 holds, no finite register driven by a periodic input produces the centre
column.** -/
theorem problem1_no_finite_driven_register (h : Problem1) {σ α : Type} [Finite σ]
    (M : Transducer σ α) (u : ℕ → α) (hu : ∃ p > 0, ∃ T, ∀ t ≥ T, u (t + p) = u t) :
    M.output u ≠ centerCol := by
  intro heq
  exact h (heq ▸ M.output_eventuallyPeriodic u hu)

/-- Equivalently: a finite periodically-driven register producing the centre column would
*refute* Problem 1. -/
theorem not_problem1_of_finite_driven_register {σ α : Type} [Finite σ]
    (M : Transducer σ α) (u : ℕ → α) (hu : ∃ p > 0, ∃ T, ∀ t ≥ T, u (t + p) = u t)
    (heq : M.output u = centerCol) : ¬ Problem1 :=
  fun h => problem1_no_finite_driven_register h M u hu heq

end GLM.Rule30
