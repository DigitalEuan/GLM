module

public import Mathlib
public import RequestProject.GLM.StepwisePlanner

/-!
# The stepwise planner, round two: frames, units, and the register in the wheels

Round two of the stepwise planner (`glm_universal.runtime.stepwise`,
`glm_universal.runtime.quantity_units`, Phase 73,
`studies/STEPWISE_TWO_STUDY.md`) reads the four kinds of question round one
could not — *how many more*, parity, averages, givens written with units — and
lets a register value feed a wheel derivation.  This file proves what its
answers and refusals rest on.

* **The mean** (`mean_perm`, `le_mean`, `mean_le`): the mean of the items is
  independent of their order, and lies between any lower and upper bound of
  the items, so *the average of A, B and C* has one answer however the list is
  written, and never leaves the range of what was averaged.
* **Parity** (`parity_witness`, `odd_iff_emod`): the column-2 equation
  `n = 2 x q + r` with `r ∈ {0, 1}` is a witness that decides parity, and
  `r = 1` exactly when `n` is odd.
* **The difference** (`more_eq_none_iff`, `more_eq_some_iff`): *how many more*
  is answered exactly when the first is at least the second, with the
  difference; it is refused (`DIFFERENCE_REVERSED`) exactly when the first is
  smaller.
* **Units** (`monomial_rescale`, `invariant_iff_homogeneous`): under a change
  of base units every quantity is multiplied by a product of powers of the
  scale factors, and a monomial law is multiplied by the powers of its
  degrees; so the law holds in every system of units exactly when it is
  dimensionally homogeneous.  That is why a given is converted only through a
  unit of the quantity's own dimension (`UNIT_MISMATCH` otherwise).
* **Offsets** (`offset_not_multiplicative`, `offset_changes_product`): a
  conversion with an offset is no multiplication, and reading a temperature
  as a level or as a difference changes a product law by `m c o`; so
  `OFFSET_UNIT` withholds a real ambiguity, not a formality.
* **Conversions are exact and leave the veto alone** (`unit_round_trip`,
  `veto_unit_free`): stating an SI value in a unit and back is the identity,
  and a given disagrees with its re-derivation in SI exactly when it disagrees
  in the unit it was written in.
* **The register feed is a given** (`register_feed_sound`): a derivation in
  which a register value (carried into SI) stands for one of the givens
  evaluates to the true value in every model of the rules in which the
  register is right — the soundness of round one, with the register's own
  correctness as its stated hypothesis.
-/

namespace GLM.StepwiseFrames

open scoped BigOperators

/-! ## The mean -/

/-- The mean of a list of exact rationals. -/
@[expose] public def mean (l : List ℚ) : ℚ := l.sum / l.length

/-- The mean does not depend on the order of the items. -/
public theorem mean_perm {l l' : List ℚ} (h : l.Perm l') : mean l = mean l' := by
  unfold mean
  rw [h.sum_eq, h.length_eq]

/-- Every lower bound of the items bounds the mean. -/
public theorem le_mean {l : List ℚ} {a : ℚ} (hne : l ≠ [])
    (h : ∀ x ∈ l, a ≤ x) : a ≤ mean l := by
  unfold mean
  have hlen : (0 : ℚ) < l.length := by
    exact_mod_cast List.length_pos_iff.mpr hne
  rw [le_div_iff₀ hlen]
  have := List.card_nsmul_le_sum l a h
  simpa [nsmul_eq_mul, mul_comm] using this

/-- Every upper bound of the items bounds the mean. -/
public theorem mean_le {l : List ℚ} {b : ℚ} (hne : l ≠ [])
    (h : ∀ x ∈ l, x ≤ b) : mean l ≤ b := by
  unfold mean
  have hlen : (0 : ℚ) < l.length := by
    exact_mod_cast List.length_pos_iff.mpr hne
  rw [div_le_iff₀ hlen]
  have := List.sum_le_card_nsmul l b h
  simpa [nsmul_eq_mul, mul_comm] using this

/-! ## Parity -/

/-- The column-2 witness `n = 2 * q + r` with `r ∈ {0, 1}`. -/
public theorem parity_witness (n : ℤ) :
    n = 2 * (n / 2) + n % 2 ∧ (n % 2 = 0 ∨ n % 2 = 1) :=
  ⟨(Int.mul_ediv_add_emod n 2).symm, Int.emod_two_eq_zero_or_one n⟩

/-- The remainder is `1` exactly when `n` is odd. -/
public theorem odd_iff_emod (n : ℤ) : Odd n ↔ n % 2 = 1 := Int.odd_iff

/-! ## The difference -/

/-- *How many more is `x` than `y`*: the difference when it is not negative,
and no answer otherwise. -/
public def more (x y : ℚ) : Option ℚ := if y ≤ x then some (x - y) else none

/-- The difference is refused exactly when the first is smaller. -/
public theorem more_eq_none_iff (x y : ℚ) : more x y = none ↔ x < y := by
  unfold more
  split_ifs with h
  · simp only [false_iff, not_lt]; exact h
  · simp only [true_iff]; exact lt_of_not_ge h

/-- An answer is the difference, and it is never negative. -/
public theorem more_eq_some_iff (x y d : ℚ) :
    more x y = some d ↔ y ≤ x ∧ d = x - y := by
  unfold more
  split_ifs with h
  · simp only [Option.some.injEq]; constructor
    · intro e; exact ⟨h, e.symm⟩
    · rintro ⟨-, e⟩; exact e.symm
  · simp only [false_iff, not_and]; intro h'; exact absurd h' h

/-! ## Units: a change of base units, and dimensional homogeneity -/

variable {n k : ℕ}

/-- A monomial `∏ xᵢ ^ eᵢ` with integer exponents. -/
public def monomial (e : Fin n → ℤ) (x : Fin n → ℚ) : ℚ := ∏ i, x i ^ e i

/-- A change of base units: base unit `a` is scaled by `lam a`, and a
quantity of dimension `d i` (its exponent on each base axis) is multiplied
by `∏ₐ lam a ^ d i a`. -/
public def rescale (lam : Fin k → ℚ) (d : Fin n → Fin k → ℤ)
    (x : Fin n → ℚ) : Fin n → ℚ :=
  fun i => (∏ a, lam a ^ d i a) * x i

/-- The degree of a monomial on base axis `a`: `∑ᵢ eᵢ · dᵢₐ`.  The monomial
is dimensionally homogeneous when every degree is `0`. -/
public def degree (e : Fin n → ℤ) (d : Fin n → Fin k → ℤ) (a : Fin k) : ℤ :=
  ∑ i, e i * d i a

private lemma zpow_sum_of_ne {ι : Type} [DecidableEq ι] {a : ℚ} (ha : a ≠ 0)
    (s : Finset ι) (f : ι → ℤ) : ∏ x ∈ s, a ^ f x = a ^ ∑ i ∈ s, f i := by
  induction s using Finset.induction_on with
  | empty => simp
  | insert j s hj ih =>
      rw [Finset.prod_insert hj, Finset.sum_insert hj, ih, zpow_add₀ ha]

/-- **A change of base units multiplies a monomial by the powers of its
degrees.** -/
public theorem monomial_rescale (e : Fin n → ℤ) (d : Fin n → Fin k → ℤ)
    (x : Fin n → ℚ) {lam : Fin k → ℚ} (hlam : ∀ a, lam a ≠ 0) :
    monomial e (rescale lam d x) = (∏ a, lam a ^ degree e d a) * monomial e x := by
  unfold monomial rescale degree
  simp only [mul_zpow, Finset.prod_mul_distrib]
  congr 1
  have h1 : ∀ i, (∏ a, lam a ^ d i a) ^ e i = ∏ a, lam a ^ (e i * d i a) := by
    intro i
    rw [← Finset.prod_zpow]
    refine Finset.prod_congr rfl (fun a _ => ?_)
    rw [← zpow_mul, mul_comm]
  simp only [h1]
  rw [Finset.prod_comm]
  refine Finset.prod_congr rfl (fun a _ => ?_)
  exact zpow_sum_of_ne (hlam a) _ _

/-- **A monomial law holds in every system of base units exactly when it is
dimensionally homogeneous** (for a monomial that is not zero). -/
public theorem invariant_iff_homogeneous (e : Fin n → ℤ) (d : Fin n → Fin k → ℤ)
    (x : Fin n → ℚ) (hx : monomial e x ≠ 0) :
    (∀ lam : Fin k → ℚ, (∀ a, lam a ≠ 0) →
        monomial e (rescale lam d x) = monomial e x) ↔
      ∀ a, degree e d a = 0 := by
  constructor
  · intro h a
    set lam : Fin k → ℚ := fun b => if b = a then 2 else 1 with hlamdef
    have hlam : ∀ b, lam b ≠ 0 := by
      intro b; simp only [hlamdef]; split_ifs <;> norm_num
    have key := h lam hlam
    rw [monomial_rescale e d x hlam] at key
    have hprod : (∏ b, lam b ^ degree e d b) = 1 := by
      have := mul_right_cancel₀ hx (key.trans (one_mul _).symm)
      exact this
    have hsingle : (∏ b, lam b ^ degree e d b) = (2 : ℚ) ^ degree e d a := by
      rw [Finset.prod_eq_single a]
      · simp [hlamdef]
      · intro b _ hb; simp [hlamdef, hb]
      · intro ha; exact absurd (Finset.mem_univ a) ha
    rw [hsingle] at hprod
    have h2 : (2 : ℚ) ^ degree e d a = (2 : ℚ) ^ (0 : ℤ) := by
      rw [hprod, zpow_zero]
    exact zpow_right_injective₀ (by norm_num : (0 : ℚ) < 2)
      (by norm_num : (2 : ℚ) ≠ 1) h2
  · intro h lam hlam
    rw [monomial_rescale e d x hlam]
    simp [h]

/-! ## Offsets -/

/-- A conversion with a non-zero offset is no multiplication: no factor
represents it. -/
public theorem offset_not_multiplicative {o : ℚ} (ho : o ≠ 0) :
    ¬ ∃ f : ℚ, ∀ x, x + o = f * x := by
  rintro ⟨f, hf⟩
  have := hf 0
  simp at this
  exact ho this

/-- Reading a temperature `t` as a level (`t + o`) or as a difference (`t`)
changes the product law `m * c * t` whenever `m * c ≠ 0` and `o ≠ 0`. -/
public theorem offset_changes_product {m c t o : ℚ} (hmc : m * c ≠ 0)
    (ho : o ≠ 0) : m * c * (t + o) ≠ m * c * t := by
  intro h
  have : m * c * o = 0 := by linarith [h]
  rcases mul_eq_zero.mp this with h1 | h1
  · exact hmc h1
  · exact ho h1

/-! ## Conversions are exact, and leave the veto alone -/

/-- Stating an SI value in a unit of factor `f` and carrying it back into SI
is the identity. -/
public theorem unit_round_trip {f : ℚ} (hf : f ≠ 0) (x : ℚ) :
    x * f / f = x := by
  field_simp

/-- A given `x`, written in a unit of factor `f`, agrees with an SI
re-derivation `y` exactly when it agrees with `y` stated in that unit: the
consistency veto does not depend on the unit a given was written in. -/
public theorem veto_unit_free {f : ℚ} (hf : f ≠ 0) (x y : ℚ) :
    x * f = y ↔ x = y / f := by
  constructor
  · intro h; rw [← h]; field_simp
  · intro h; rw [h]; field_simp

/-! ## The register feed -/

open GLM.StepwisePlanner

/-- **A register value feeds a derivation as a given.**  Let `q` be the
given whose value is read from the register — `v`, carried into SI by the
exact factor `f`.  In every model of the rules that agrees with the other
givens and in which the register is right (`m q = f * v`), an admissible
derivation evaluates to the model's value of what it derives. -/
public theorem register_feed_sound {X : Type} [DecidableEq X]
    {R : Set (Rule X)} {G : Set X} {g m : X → ℚ} {q : X} {f v : ℚ}
    (hrules : ∀ r ∈ R, Satisfies m r)
    (hgivens : ∀ x ∈ G, x ≠ q → m x = g x)
    (hregister : m q = f * v) (t : StepwisePlanner.Tree X)
    (ht : t.Admissible R G) :
    t.eval (Function.update g q (f * v)) = m t.root := by
  have hm : IsModel R G (Function.update g q (f * v)) m := by
    unfold IsModel
    refine ⟨hrules, fun x hx => ?_⟩
    by_cases hxq : x = q
    · subst hxq; simp [hregister]
    · rw [Function.update_of_ne hxq]; exact hgivens x hx hxq
  exact eval_eq_model hm t ht

end GLM.StepwiseFrames
