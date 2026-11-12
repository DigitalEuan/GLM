module

public import RequestProject.GLM.Rule30.Injector

/-!
# Round 18 (part 2): the three analogies, made exact

The user proposed three analogies for a "filtration-preserving operator on `GF(2)` with a
coboundary parity lock".  This file proves the precise statements behind each one inside the
Rule 30 setting, so that the GLM can import exactly what is true.

* **Coboundary / `δ² = 0`** (discrete exterior calculus).  The Boolean derivative
  `Δ_i f (x) = f(x | x_i = 1) + f(x | x_i = 0)` satisfies `Δ_i Δ_i = 0` (`booleanDerivative_twice`)
  and the derivatives commute (`booleanDerivative_comm`).  An ANF coefficient is an iterated
  derivative at the white row: removing one variable from the monomial is one derivative
  (`anfCoeff_eq_anfCoeff_derivative`).  This is the exact form of "interior faces cancel in pairs".
* **Stabilizer / Clifford propagation.**  Rule 30 is the linear Rule 150 plus the single
  nonlinear term `C·R` (`rule30_eq_rule150_xor_injector`).  Rule 150 is `GF(2)`-linear for every
  number of steps (`ecaEvolve150_additive`), so all its ANF coefficients of degree `≥ 2` vanish
  forever (`rule150_anfDegree_le_one`): like Pauli propagation through Clifford circuits it is
  fully trackable.  The `C·R` term breaks linearity at the first step (`rule30_not_additive`)
  and is the only source of degree growth (`deg a(n) = 2n − 1`).
* **Charge conservation / telescoping (delta-sigma, Kirchhoff).**  Already formal in
  `ChemistryLab.lean`: `coboundary_total_zero` (a telescoping weight has total `0` on every
  finite row) and `coboundary_of_cert` (every additive quantity that is conserved along the
  seed run in the tested range is such a telescoping coboundary, i.e. carries no information).
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-! ## Analogy 3: `δ² = 0` -/

/-- **`Δ_i Δ_i = 0`**: differentiating twice in the same direction gives zero. -/
theorem booleanDerivative_twice (f : Config → Bool) (i : ℤ) :
    booleanDerivative (booleanDerivative f i) i = fun _ => false := by
  funext x
  simp [booleanDerivative, Function.update_idem]

/-- Boolean derivatives in different directions commute. -/
theorem booleanDerivative_comm (f : Config → Bool) (i j : ℤ) :
    booleanDerivative (booleanDerivative f i) j = booleanDerivative (booleanDerivative f j) i := by
  funext x
  by_cases hij : i = j
  · subst hij; rfl
  · simp only [booleanDerivative]
    rw [Function.update_comm hij, Function.update_comm hij, Function.update_comm hij,
      Function.update_comm hij]
    generalize f (Function.update (Function.update x j true) i true) = a
    generalize f (Function.update (Function.update x j true) i false) = b
    generalize f (Function.update (Function.update x j false) i true) = c
    generalize f (Function.update (Function.update x j false) i false) = d
    revert a b c d; decide

/-- **An ANF coefficient is an iterated derivative.** For `j ∈ S`, the coefficient of `x^S` in
`f` is the coefficient of `x^{S \ {j}}` in `Δ_j f`. -/
theorem anfCoeff_eq_anfCoeff_derivative (f : Config → Bool) (S : Finset ℤ) {j : ℤ} (hj : j ∈ S) :
    anfCoeff f S = anfCoeff (booleanDerivative f j) (S.erase j) := by
  unfold anfCoeff
  rw [coeffZ_split _ S hj]
  unfold coeffZ
  refine sum_congr rfl (fun T hT => ?_)
  have hjT : j ∉ T := fun h => notMem_erase j S (mem_powerset.mp hT h)
  have h0 : Function.update (ind T) j false = ind T := by
    funext c; by_cases hc : c = j
    · subst hc; simp [ind, hjT]
    · simp [Function.update_of_ne hc]
  have hx : ∀ a b : Bool, bz a + bz b = bz (xor b a) := by decide
  simp only [booleanDerivative, ind_insert, h0, hx]

/-! ## Analogy 2: linear (Clifford-like) part and the nonlinear injector -/

theorem ecaRule_150 (L C R : Bool) : ecaRule 150 L C R = xor L (xor C R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- **Rule 30 = Rule 150 ⊕ the injector `C·R`.** -/
theorem rule30_eq_rule150_xor_injector (L C R : Bool) :
    rule30 L C R = xor (ecaRule 150 L C R) (C && R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- **Rule 150 is `GF(2)`-linear at every step**: the run of a sum of rows is the sum of the
runs. -/
theorem ecaEvolve150_additive (x y : Config) (n : ℕ) (c : ℤ) :
    ecaEvolve 150 (fun i => xor (x i) (y i)) n c =
      xor (ecaEvolve 150 x n c) (ecaEvolve 150 y n c) := by
  induction n generalizing c with
  | zero => rfl
  | succ n ih =>
    rw [ecaEvolve_succ, ecaEvolve_succ, ecaEvolve_succ, ih, ih, ih, ecaRule_150, ecaRule_150,
      ecaRule_150]
    cases ecaEvolve 150 x n (c - 1) <;> cases ecaEvolve 150 x n c <;>
      cases ecaEvolve 150 x n (c + 1) <;> cases ecaEvolve 150 y n (c - 1) <;>
      cases ecaEvolve 150 y n c <;> cases ecaEvolve 150 y n (c + 1) <;> rfl

theorem ind_insert_xor (T : Finset ℤ) (j : ℤ) (hj : j ∉ T) :
    ind (insert j T) = fun i => xor (ind T i) (ind {j} i) := by
  funext i
  by_cases h : i = j
  · subst h; simp [ind, hj]
  · simp [ind, h]

/-- **No degree growth without the injector.** Every cell of Rule 150 is a `GF(2)`-linear
function of the initial row: all ANF coefficients of degree `≥ 2` vanish, for every `n`. -/
theorem rule150_anfDegree_le_one (n : ℕ) (c : ℤ) :
    AnfDegreeLE (fun x => ecaEvolve 150 x n c) 1 := by
  intro S hS
  obtain ⟨j, hj⟩ : S.Nonempty := card_pos.mp (by omega)
  unfold anfCoeff
  rw [coeffZ_split _ S hj]
  have key : ∀ T ∈ (S.erase j).powerset,
      bz (ecaEvolve 150 (ind T) n c) + bz (ecaEvolve 150 (ind (insert j T)) n c) =
        bz (ecaEvolve 150 (ind {j}) n c) := by
    intro T hT
    have hjT : j ∉ T := fun h => notMem_erase j S (mem_powerset.mp hT h)
    rw [ind_insert_xor T j hjT, ecaEvolve150_additive]
    cases ecaEvolve 150 (ind T) n c <;> cases ecaEvolve 150 (ind {j}) n c <;> decide
  rw [sum_congr rfl key, sum_const, card_powerset, card_erase_of_mem hj, nsmul_eq_mul]
  obtain ⟨k, hk⟩ : ∃ k, S.card - 1 = k + 1 := ⟨S.card - 2, by omega⟩
  rw [hk, pow_succ]; push_cast
  rw [show (2 : ZMod 2) = 0 from rfl, mul_zero, zero_mul]

/-- **The injector breaks linearity at the first step.** -/
theorem rule30_not_additive :
    ∃ x y : Config, evolve (fun i => xor (x i) (y i)) 1 0 ≠ xor (evolve x 1 0) (evolve y 1 0) :=
  ⟨ind {0}, ind {1}, by decide⟩

/-- **The contrast in one statement.** Rule 150 (the linear part) keeps ANF degree `≤ 1` for
ever, while Rule 30 (linear part + injector) has degree exactly `2n − 1` for every `n ≥ 2`. -/
theorem injector_is_the_only_degree_source (n : ℕ) (hn : 2 ≤ n) :
    AnfDegreeLE (fun x => ecaEvolve 150 x n 0) 1 ∧
      AnfDegreeEq (fun x => evolve x n 0) (2 * n - 1) :=
  ⟨rule150_anfDegree_le_one n 0, center_anfDegree_eq n hn⟩

end GLM.Rule30
