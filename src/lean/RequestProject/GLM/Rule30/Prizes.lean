module

public import RequestProject.GLM.Rule30.ANF
public import RequestProject.GLM.Rule30.AdjacentColumns
public import RequestProject.GLM.Rule30.Wobble

/-!
# The three Rule 30 prize problems: honest statements and an audit

The prize problems are **open**.  They are stated here as `Prop`s (not as axioms — an
axiom asserting an open problem would make every downstream "proof" conditional on it,
and two of the original axioms were in fact inconsistent; see below).

* `Problem1` — the centre column is not eventually periodic.
* `Problem2` — the frequency of black cells in the centre column tends to `1/2`
  (`problem2_iff_wobble`: equivalently the wobble `D(n)` is `o(n)`).
* Problem 3 asks for a lower bound on the *computational cost* of `n ↦ a(n)`.  It depends on
  a machine model; we do not formalise a model here, but we record why the study's two
  formal attempts do not capture it (`unconstrained_cost_refutes`, and the remark below).

## Audit results

* `map_properties_cannot_decide_periodicity`: **any** property of the `n`-step maps
  `x ↦ a(n)(0)` (ANF degree, cone separation, right-cone weight, …) holds equally for the
  all-white row, whose centre column is periodic.  So "degree growth ⇒ non-periodicity"
  (the route proposed for Problem 1 via Targets 1+3) is not a valid inference: any proof of
  Problem 1 must use the specific seed, as `seed_not_both_adjacent_columns_periodic` does.
* For the same reason, the degree of the generic map says nothing about the cost of
  computing the *specific* sequence `n ↦ a(n)` (Problem 3): a circuit lower bound for the
  map `(x_{-n}, …, x_n) ↦ a(n)(0)` concerns a different function, with `2n+1` input bits
  instead of the `log n` bits of `n`.
* `not_forall_sqrt_bound` (in `Wobble`): the original `wobbleBoundedness_sqrt` axiom quantified
  over *all* sequences and is refutable.  `unconstrained_cost_refutes`: the original
  `r30_complexity` axiom, whose `cost` field is unconstrained, is refutable as well.
-/

@[expose] public section

namespace GLM.Rule30

/-- **Problem 1** (open): the centre column of Rule 30 is not eventually periodic. -/
def Problem1 : Prop := ¬ EventuallyPeriodic centerCol

/-- **Problem 2** (open): the frequency of black cells in the centre column tends to `1/2`. -/
def Problem2 : Prop := HasFrequencyHalf centerCol

/-- Problem 2 is equivalent to the wobble being sub-linear: `D(n)/n → 0`. -/
theorem problem2_iff_wobble :
    Problem2 ↔ Filter.Tendsto (fun n => (wobble centerCol n : ℝ) / n) Filter.atTop (nhds 0) :=
  hasFrequencyHalf_iff centerCol

/-- The study's wobble bound would settle Problem 2. -/
theorem problem2_of_sqrt_bound (C : ℝ)
    (h : ∀ᶠ n in Filter.atTop, |(wobble centerCol n : ℝ)| ≤ C * Real.sqrt n) : Problem2 :=
  hasFrequencyHalf_of_sqrt_bound centerCol C h

/-- Partial result towards Problem 1 (proved): if the centre column is eventually periodic,
then neither neighbouring column is. -/
theorem problem1_partial (h : EventuallyPeriodic centerCol) :
    ¬ EventuallyPeriodic (fun t => evolve seed t (-1)) ∧
      ¬ EventuallyPeriodic (fun t => evolve seed t 1) :=
  centerCol_periodic_forces_neighbours_aperiodic h

/-- The all-white row has an eventually periodic (constant) centre column. -/
theorem white_centre_periodic : EventuallyPeriodic (fun n => evolve (fun _ => false) n 0) :=
  ⟨1, one_pos, 0, fun n _ => by simp only [evolve_false]⟩

/-- **Seed-independent properties cannot decide periodicity.** Whatever property `P` the
family of `n`-step maps `x ↦ a(n)(0)` has, it cannot imply that the centre column is
non-periodic for every starting row. -/
theorem map_properties_cannot_decide_periodicity
    (P : (ℕ → Config → Bool) → Prop) (hP : P (fun n x => evolve x n 0)) :
    ¬ (P (fun n x => evolve x n 0) →
        ∀ x : Config, ¬ EventuallyPeriodic (fun n => evolve x n 0)) :=
  fun h => h hP (fun _ => false) white_centre_periodic

/-- In particular the degree bound, cone separation and the top-monomial conjecture are all
compatible with a periodic centre column (for the all-white row). -/
theorem degree_facts_compatible_with_periodicity :
    (∀ n, 2 ≤ n → AnfDegreeLE (fun x => evolve x n 0) (2 * n - 1)) ∧
      (∀ (n : ℕ) (x : Config), evolve (flipAt x (0 - n)) n 0 = !evolve x n 0) ∧
      EventuallyPeriodic (fun n => evolve (fun _ => false) n 0) :=
  ⟨center_anfDegree_le, fun n x => evolve_flip_left_edge x n 0, white_centre_periodic⟩

/-- An "algorithm" whose cost is just a recorded number, as in the original formalisation
of Problem 3. -/
structure UnconstrainedAlgorithm (a : ℕ → Bool) where
  compute : ℕ → Bool
  computes : ∀ n, compute n = a n
  cost : ℕ → ℕ

/-- **The original Problem 3 axiom is refutable.** With an unconstrained `cost` field, every
sequence has an "algorithm" of cost `0`. -/
theorem unconstrained_cost_refutes (a : ℕ → Bool) :
    ∃ A : UnconstrainedAlgorithm a, ∃ c : ℚ, c < 1 ∧ ∃ N : ℕ, ∀ n ≥ N, (A.cost n : ℚ) ≤ c * n :=
  ⟨⟨a, fun _ => rfl, fun _ => 0⟩, 0, by norm_num, 0, fun n _ => by simp⟩

end GLM.Rule30
