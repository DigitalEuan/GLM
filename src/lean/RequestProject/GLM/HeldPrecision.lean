/-
# Held precision: a register value's stated precision, carried exactly

`studies/HELD_PRECISION_STUDY.md` (Phase 76,
`glm_universal.reasoning.held_precision`).  The answer of a goal or narrative
chain of the stepwise planner is one monomial `C · Π leafᵢ ^ eᵢ` in its leaves
with integer exponents: every wheel step is an axiom solved for a variable of
power `±1`, and a step into or out of SI multiplies by an exact positive
factor.  A register leaf is read at its stated precision, an interval
`[loᵢ, hiᵢ]` with `loᵢ > 0`.

* **The corner bound** (`monomial_corner_bounds`, `scaled_corner_bounds`):
  over a box of positive intervals the monomial lies between its values at two
  corners — each leaf at its low or high end according to the sign of its
  exponent.  The corners are points of the box (`corner_mem`), so the bound
  is attained: the interval the GLM states is exact, not merely safe.  A leaf
  of exponent `0` contributes the factor `1` whatever its interval: its
  precision cancels.
* **Step-by-step interval arithmetic is wider** (`stepwise_strictly_wider`):
  for the chain `x · y / x` with `x ∈ [1, 2]` and `y = 1`, taking each step's
  interval from its inputs' intervals alone gives `[1/2, 2]`, while the chain's
  value is `1` at every point of the box.  This is the shape of the declared
  case — the melting point of iron read into the energy and divided out again
  for the entropy.
-/
import Mathlib

namespace GLM.HeldPrecision

open Finset

/-- A nonnegative integer power is monotone on the positive reals. -/
theorem zpow_mono_pos {a b : ℝ} (ha : 0 < a) (hab : a ≤ b) {n : ℤ} (hn : 0 ≤ n) :
    a ^ n ≤ b ^ n := by
  lift n to ℕ using hn
  simp only [zpow_natCast]
  exact pow_le_pow_left₀ ha.le hab n

/-- A nonpositive integer power is antitone on the positive reals. -/
theorem zpow_anti_neg {a b : ℝ} (ha : 0 < a) (hab : a ≤ b) {n : ℤ} (hn : n ≤ 0) :
    b ^ n ≤ a ^ n := by
  obtain ⟨k, rfl⟩ : ∃ k : ℕ, n = -k := ⟨n.natAbs, by omega⟩
  simp only [zpow_neg, zpow_natCast]
  exact inv_anti₀ (pow_pos ha k) (pow_le_pow_left₀ ha.le hab k)

/-- The corner of the box where the monomial is least. -/
def lowCorner {ι : Type*} (e : ι → ℤ) (lo hi : ι → ℝ) (i : ι) : ℝ :=
  if 0 ≤ e i then lo i else hi i

/-- The corner of the box where the monomial is greatest. -/
def highCorner {ι : Type*} (e : ι → ℤ) (lo hi : ι → ℝ) (i : ι) : ℝ :=
  if 0 ≤ e i then hi i else lo i

/-- Both corners are points of the box. -/
theorem corner_mem {ι : Type*} (e : ι → ℤ) (lo hi : ι → ℝ) (i : ι) (h : lo i ≤ hi i) :
    (lo i ≤ lowCorner e lo hi i ∧ lowCorner e lo hi i ≤ hi i) ∧
      (lo i ≤ highCorner e lo hi i ∧ highCorner e lo hi i ≤ hi i) := by
  unfold lowCorner highCorner
  split_ifs <;> exact ⟨⟨by linarith, by linarith⟩, ⟨by linarith, by linarith⟩⟩

/-- **The corner bound**: over a box of positive intervals, a monomial with
integer exponents lies between its values at the low and the high corner. -/
theorem monomial_corner_bounds {ι : Type*} (s : Finset ι) (e : ι → ℤ) (lo hi x : ι → ℝ)
    (hlo : ∀ i ∈ s, 0 < lo i) (hx : ∀ i ∈ s, lo i ≤ x i ∧ x i ≤ hi i) :
    ∏ i ∈ s, lowCorner e lo hi i ^ e i ≤ ∏ i ∈ s, x i ^ e i ∧
      ∏ i ∈ s, x i ^ e i ≤ ∏ i ∈ s, highCorner e lo hi i ^ e i := by
  unfold lowCorner highCorner
  constructor
  · apply Finset.prod_le_prod
    · intro i hi'
      split_ifs with h
      · exact (zpow_pos (hlo i hi') _).le
      · exact (zpow_pos (lt_of_lt_of_le (hlo i hi') ((hx i hi').1.trans (hx i hi').2)) _).le
    · intro i hi'
      have h0 := hlo i hi'
      obtain ⟨h1, h2⟩ := hx i hi'
      split_ifs with h
      · exact zpow_mono_pos h0 h1 h
      · exact zpow_anti_neg (lt_of_lt_of_le h0 h1) h2 (by omega)
  · apply Finset.prod_le_prod
    · intro i hi'
      exact (zpow_pos (lt_of_lt_of_le (hlo i hi') (hx i hi').1) _).le
    · intro i hi'
      have h0 := hlo i hi'
      obtain ⟨h1, h2⟩ := hx i hi'
      split_ifs with h
      · exact zpow_mono_pos (lt_of_lt_of_le h0 h1) h2 h
      · exact zpow_anti_neg h0 h1 (by omega)

/-- The same with a positive coefficient, the form a chain's answer takes. -/
theorem scaled_corner_bounds {ι : Type*} (s : Finset ι) (c : ℝ) (hc : 0 < c) (e : ι → ℤ)
    (lo hi x : ι → ℝ) (hlo : ∀ i ∈ s, 0 < lo i) (hx : ∀ i ∈ s, lo i ≤ x i ∧ x i ≤ hi i) :
    c * ∏ i ∈ s, lowCorner e lo hi i ^ e i ≤ c * ∏ i ∈ s, x i ^ e i ∧
      c * ∏ i ∈ s, x i ^ e i ≤ c * ∏ i ∈ s, highCorner e lo hi i ^ e i := by
  obtain ⟨h1, h2⟩ := monomial_corner_bounds s e lo hi x hlo hx
  exact ⟨mul_le_mul_of_nonneg_left h1 hc.le, mul_le_mul_of_nonneg_left h2 hc.le⟩

/-- A leaf of exponent zero has cancelled: its interval does not reach the
answer. -/
theorem cancelled_leaf (x : ℝ) : x ^ (0 : ℤ) = 1 := zpow_zero x

/-- Step-by-step interval multiplication of positive intervals. -/
def mulI (a b : ℝ × ℝ) : ℝ × ℝ := (a.1 * b.1, a.2 * b.2)

/-- Step-by-step interval division of positive intervals. -/
noncomputable def divI (a b : ℝ × ℝ) : ℝ × ℝ := (a.1 / b.2, a.2 / b.1)

/-- **Step-by-step interval arithmetic is strictly wider**: the chain
`x · y / x` over `x ∈ [1, 2]`, `y = 1` is `1` everywhere, while the step-by-step
interval is `[1/2, 2]`. -/
theorem stepwise_strictly_wider :
    divI (mulI (1, 2) (1, 1)) (1, 2) = (1 / 2, 2) ∧
      ∀ x ∈ Set.Icc (1 : ℝ) 2, x * 1 / x = 1 := by
  refine ⟨?_, fun x hx => ?_⟩
  · simp [divI, mulI]
  · have : x ≠ 0 := by linarith [hx.1]
    field_simp

end GLM.HeldPrecision
