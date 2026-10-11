module

public import Mathlib

/-!
# Deciding a sign by factorisation (Phase 109)

The cubic route (`overlay/glm_universal/reasoning/routes.py`, decision point
`cubic.letters`) reads the sign of a discriminant in letters.  Two tests are
applied, in order (`overlay/glm_universal/reasoning/sign_factor.py`):

* **surface** -- every term of the expanded polynomial is a positive
  multiple of even powers of the letters, so the polynomial is `≥ 0`
  everywhere (`surface_nonneg`);
* **factor** -- the polynomial is `c · ∏ fᵢ ^ eᵢ` with each factor to an odd
  power of a known sign; a factor to an even power is `≥ 0` whatever its
  sign.  After flipping each non-positive odd factor into the constant
  (`odd_pow_neg`), the product of non-negative factors and even powers has
  the sign of the constant (`factored_nonneg`, `factored_nonpos`).
-/

namespace GLM.SignFactor

open Finset

/-- The surface test: a sum of positive multiples of products of even powers
of the letters is non-negative. -/
public theorem surface_nonneg {ι κ : Type*} (s : Finset ι) (vars : Finset κ)
    (c : ι → ℝ) (e : ι → κ → ℕ) (x : κ → ℝ) (hc : ∀ i ∈ s, 0 < c i) :
    0 ≤ ∑ i ∈ s, c i * ∏ j ∈ vars, x j ^ (2 * e i j) := by
  refine sum_nonneg fun i hi => mul_nonneg (hc i hi).le ?_
  exact prod_nonneg fun j _ => by rw [pow_mul]; positivity

/-- A factor to an even power is non-negative, whatever its sign. -/
public theorem even_pow_nonneg (f : ℝ) (k : ℕ) : 0 ≤ f ^ (2 * k) := by
  rw [pow_mul]; positivity

/-- A non-positive factor to an odd power moves a sign into the constant. -/
public theorem odd_pow_neg (f : ℝ) (k : ℕ) :
    f ^ (2 * k + 1) = -((-f) ^ (2 * k + 1)) := by
  rw [Odd.neg_pow ⟨k, rfl⟩, neg_neg]

/-- The factor test: when every factor is either raised to an even power or
non-negative, the product has the sign of the constant. -/
public theorem factored_nonneg (c : ℝ) (L : List (ℝ × ℕ)) (hc : 0 ≤ c)
    (hL : ∀ fe ∈ L, Even fe.2 ∨ 0 ≤ fe.1) :
    0 ≤ c * (L.map fun fe => fe.1 ^ fe.2).prod := by
  refine mul_nonneg hc (List.prod_nonneg ?_)
  intro a ha
  obtain ⟨fe, hfe, rfl⟩ := List.mem_map.mp ha
  rcases hL fe hfe with h | h
  · exact h.pow_nonneg fe.1
  · exact pow_nonneg h _

/-- The same with a non-positive constant: the product is non-positive. -/
public theorem factored_nonpos (c : ℝ) (L : List (ℝ × ℕ)) (hc : c ≤ 0)
    (hL : ∀ fe ∈ L, Even fe.2 ∨ 0 ≤ fe.1) :
    c * (L.map fun fe => fe.1 ^ fe.2).prod ≤ 0 := by
  have := factored_nonneg (-c) L (by linarith) hL
  linarith [neg_mul c (L.map fun fe => fe.1 ^ fe.2).prod]

/-- An example the surface test misses: `(a - b)⁶ (c² + 1)` has a negative
term once expanded, and is non-negative for every real `a, b, c`. -/
public theorem example_cardano (a b c : ℝ) : 0 ≤ (a - b) ^ 6 * (c ^ 2 + 1) := by
  positivity

/-- The other example of the Phase 109 study: the discriminant of
`x³ - (a² + ab + b²) x + ab(a + b)` is `-(a - b)²(2a + b)²(a + 2b)²/108`,
non-positive for every real `a, b`, so the three roots are real. -/
public theorem example_viete (a b : ℝ) :
    let P := -(a ^ 2 + a * b + b ^ 2)
    let Q := a * b * (a + b)
    Q ^ 2 / 4 + P ^ 3 / 27 = -((a - b) * (2 * a + b) * (a + 2 * b)) ^ 2 / 108 ∧
      Q ^ 2 / 4 + P ^ 3 / 27 ≤ 0 := by
  intro P Q
  have h : Q ^ 2 / 4 + P ^ 3 / 27 = -((a - b) * (2 * a + b) * (a + 2 * b)) ^ 2 / 108 := by
    simp only [P, Q]; ring
  refine ⟨h, ?_⟩
  rw [h]
  have := sq_nonneg ((a - b) * (2 * a + b) * (a + 2 * b))
  linarith

end GLM.SignFactor
