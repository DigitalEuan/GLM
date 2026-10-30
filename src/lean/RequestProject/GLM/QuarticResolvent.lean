module

public import Mathlib

/-!
# A quartic with four real roots, answered in steps (Phase 109)

The normal modes of a four-degree-of-freedom system whose mass and stiffness
matrices are symmetric and positive definite are the four real, positive
roots `w2` of a quartic `a w2⁴ + b w2³ + c w2² + d w2 + e`.  The modes route
`modes.higher:ferrari` (`glm_universal/reasoning/derivation.py`)
writes them in steps rather than as one expanded formula:

1. `w2 = y - b/(4a)` turns the quartic into `a (y⁴ + p y² + q y + r)`
   (`depressed_quartic`);
2. the resolvent cubic `z³ + 2p z² + (p² - 4r) z - q²` has the three roots
   `z = (y₁ + y₂)², (y₁ + y₃)², (y₁ + y₄)²` (`resolvent_roots`), so all
   three are real and non-negative when the four `y` are real; it is solved
   by Viète's formula (`CubicTrig.lean`);
3. with `s₁ = √z₁`, `s₂ = √z₂` and `s₃ = -q/(s₁ s₂)`, the four roots are the
   half-sums `(±s₁ ± s₂ ± s₃)/2` with an even number of minus signs
   (`ferrari_roots`).

`half_sums_recover` checks the converse bookkeeping: the half-sums of
`y₁ + y₂, y₁ + y₃, y₁ + y₄` give back `y₁, …, y₄`, and their product is `-q`
(`resolvent_product`).
-/

namespace GLM.QuarticResolvent

/-- Step 1: the shift `w = y - b/(4a)` removes the cubic term. -/
public theorem depressed_quartic (a b c d e y : ℝ) (ha : a ≠ 0) :
    a * (y - b / (4 * a)) ^ 4 + b * (y - b / (4 * a)) ^ 3 +
        c * (y - b / (4 * a)) ^ 2 + d * (y - b / (4 * a)) + e =
      a * (y ^ 4 + (8 * a * c - 3 * b ^ 2) / (8 * a ^ 2) * y ^ 2 +
        (b ^ 3 - 4 * a * b * c + 8 * a ^ 2 * d) / (8 * a ^ 3) * y +
        (-3 * b ^ 4 + 256 * a ^ 3 * e - 64 * a ^ 2 * b * d +
          16 * a * b ^ 2 * c) / (256 * a ^ 4)) := by
  field_simp
  ring

/-- The coefficients of a depressed quartic with roots `y₁, …, y₄`
(`y₁ + y₂ + y₃ + y₄ = 0`): `p = e₂`, `q = -e₃`, `r = e₄`. -/
public theorem depressed_from_roots (y₁ y₂ y₃ y₄ t : ℝ)
    (hsum : y₁ + y₂ + y₃ + y₄ = 0) :
    (t - y₁) * (t - y₂) * (t - y₃) * (t - y₄) =
      t ^ 4 + (y₁ * y₂ + y₁ * y₃ + y₁ * y₄ + y₂ * y₃ + y₂ * y₄ + y₃ * y₄) * t ^ 2
        - (y₁ * y₂ * y₃ + y₁ * y₂ * y₄ + y₁ * y₃ * y₄ + y₂ * y₃ * y₄) * t
        + y₁ * y₂ * y₃ * y₄ := by
  have h4 : y₄ = -(y₁ + y₂ + y₃) := by linarith
  subst h4
  ring

/-- Step 2: each `(y₁ + yⱼ)²` is a root of the resolvent cubic. -/
public theorem resolvent_roots (y₁ y₂ y₃ y₄ : ℝ) (hsum : y₁ + y₂ + y₃ + y₄ = 0) :
    let p := y₁ * y₂ + y₁ * y₃ + y₁ * y₄ + y₂ * y₃ + y₂ * y₄ + y₃ * y₄
    let q := -(y₁ * y₂ * y₃ + y₁ * y₂ * y₄ + y₁ * y₃ * y₄ + y₂ * y₃ * y₄)
    let r := y₁ * y₂ * y₃ * y₄
    ∀ z ∈ ({(y₁ + y₂) ^ 2, (y₁ + y₃) ^ 2, (y₁ + y₄) ^ 2} : Set ℝ),
      z ^ 3 + 2 * p * z ^ 2 + (p ^ 2 - 4 * r) * z - q ^ 2 = 0 := by
  intro p q r z hz
  have h4 : y₄ = -(y₁ + y₂ + y₃) := by linarith
  simp only [Set.mem_insert_iff, Set.mem_singleton_iff] at hz
  rcases hz with rfl | rfl | rfl <;> simp only [p, q, r] <;> subst h4 <;> ring

/-- The resolvent cubic factors over its three roots. -/
public theorem resolvent_factors (y₁ y₂ y₃ y₄ z : ℝ) (hsum : y₁ + y₂ + y₃ + y₄ = 0) :
    let p := y₁ * y₂ + y₁ * y₃ + y₁ * y₄ + y₂ * y₃ + y₂ * y₄ + y₃ * y₄
    let q := -(y₁ * y₂ * y₃ + y₁ * y₂ * y₄ + y₁ * y₃ * y₄ + y₂ * y₃ * y₄)
    let r := y₁ * y₂ * y₃ * y₄
    z ^ 3 + 2 * p * z ^ 2 + (p ^ 2 - 4 * r) * z - q ^ 2 =
      (z - (y₁ + y₂) ^ 2) * (z - (y₁ + y₃) ^ 2) * (z - (y₁ + y₄) ^ 2) := by
  intro p q r
  have h4 : y₄ = -(y₁ + y₂ + y₃) := by linarith
  simp only [p, q, r]
  subst h4
  ring

/-- The product of the three pair sums is `-q`. -/
public theorem resolvent_product (y₁ y₂ y₃ y₄ : ℝ) (hsum : y₁ + y₂ + y₃ + y₄ = 0) :
    (y₁ + y₂) * (y₁ + y₃) * (y₁ + y₄) =
      y₁ * y₂ * y₃ + y₁ * y₂ * y₄ + y₁ * y₃ * y₄ + y₂ * y₃ * y₄ := by
  have h4 : y₄ = -(y₁ + y₂ + y₃) := by linarith
  subst h4
  ring

/-- The half-sums of the pair sums give back the four roots. -/
public theorem half_sums_recover (y₁ y₂ y₃ y₄ : ℝ) (hsum : y₁ + y₂ + y₃ + y₄ = 0) :
    let s₁ := y₁ + y₂
    let s₂ := y₁ + y₃
    let s₃ := y₁ + y₄
    (s₁ + s₂ + s₃) / 2 = y₁ ∧ (s₁ - s₂ - s₃) / 2 = y₂ ∧
      (-s₁ + s₂ - s₃) / 2 = y₃ ∧ (-s₁ - s₂ + s₃) / 2 = y₄ := by
  intro s₁ s₂ s₃
  refine ⟨?_, ?_, ?_, ?_⟩ <;> simp only [s₁, s₂, s₃] <;> linarith

/-- The four half-sums of any `s₁, s₂, s₃` are the roots of the depressed
quartic whose coefficients the `sᵢ` determine. -/
public theorem half_sums_quartic (s₁ s₂ s₃ t : ℝ) :
    (t - (s₁ + s₂ + s₃) / 2) * (t - (s₁ - s₂ - s₃) / 2) *
        (t - (-s₁ + s₂ - s₃) / 2) * (t - (-s₁ - s₂ + s₃) / 2) =
      t ^ 4 - (s₁ ^ 2 + s₂ ^ 2 + s₃ ^ 2) / 2 * t ^ 2 - s₁ * s₂ * s₃ * t +
        ((s₁ ^ 2 + s₂ ^ 2 + s₃ ^ 2) ^ 2 -
          4 * (s₁ ^ 2 * s₂ ^ 2 + s₁ ^ 2 * s₃ ^ 2 + s₂ ^ 2 * s₃ ^ 2)) / 16 := by
  ring

/-- Step 3, the route as the layer takes it: if `z₁, z₂, z₃` are the roots
of the resolvent cubic, `s₁² = z₁`, `s₂² = z₂`, `s₁ s₂ ≠ 0` and
`s₃ = -q/(s₁ s₂)`, then the four half-sums are exactly the roots of
`y⁴ + p y² + q y + r`. -/
public theorem ferrari_roots (p q r z₁ z₂ z₃ s₁ s₂ : ℝ)
    (hz : ∀ z : ℝ, z ^ 3 + 2 * p * z ^ 2 + (p ^ 2 - 4 * r) * z - q ^ 2 =
      (z - z₁) * (z - z₂) * (z - z₃))
    (h₁ : s₁ ^ 2 = z₁) (h₂ : s₂ ^ 2 = z₂) (hne : s₁ * s₂ ≠ 0) (t : ℝ) :
    let s₃ := -q / (s₁ * s₂)
    (t - (s₁ + s₂ + s₃) / 2) * (t - (s₁ - s₂ - s₃) / 2) *
        (t - (-s₁ + s₂ - s₃) / 2) * (t - (-s₁ - s₂ + s₃) / 2) =
      t ^ 4 + p * t ^ 2 + q * t + r := by
  intro s₃
  -- Vieta for the resolvent, read off three values of `z`
  have e0 := hz 0
  have e1 := hz 1
  have e2 := hz (-1)
  have v1 : z₁ + z₂ + z₃ = -2 * p := by nlinarith
  have v2 : z₁ * z₂ + z₁ * z₃ + z₂ * z₃ = p ^ 2 - 4 * r := by nlinarith
  have v3 : z₁ * z₂ * z₃ = q ^ 2 := by nlinarith
  have hs3 : s₁ * s₂ * s₃ = -q := by
    simp only [s₃]
    rw [mul_div_assoc', mul_comm, mul_div_assoc, div_self hne, mul_one]
  have hs3sq : s₃ ^ 2 = z₃ := by
    have : (s₁ * s₂) ^ 2 * s₃ ^ 2 = (s₁ * s₂) ^ 2 * z₃ := by
      calc (s₁ * s₂) ^ 2 * s₃ ^ 2 = (s₁ * s₂ * s₃) ^ 2 := by ring
        _ = q ^ 2 := by rw [hs3]; ring
        _ = z₁ * z₂ * z₃ := v3.symm
        _ = (s₁ * s₂) ^ 2 * z₃ := by rw [← h₁, ← h₂]; ring
    exact mul_left_cancel₀ (pow_ne_zero 2 hne) this
  rw [half_sums_quartic]
  have hp : (s₁ ^ 2 + s₂ ^ 2 + s₃ ^ 2) = -2 * p := by rw [h₁, h₂, hs3sq]; exact v1
  have hr : s₁ ^ 2 * s₂ ^ 2 + s₁ ^ 2 * s₃ ^ 2 + s₂ ^ 2 * s₃ ^ 2 = p ^ 2 - 4 * r := by
    rw [h₁, h₂, hs3sq]; exact v2
  rw [hp, hr, hs3]
  ring

end GLM.QuarticResolvent
