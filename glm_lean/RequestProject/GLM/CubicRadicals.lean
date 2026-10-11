module

public import Mathlib

/-!
# Cubics and nested square roots: what the Phase 104 readings rest on

`studies/CUBIC_RADICAL_STUDY.md` (Phase 104) extends the branch layer of
`solve symbolically` (`overlay/glm_universal/reasoning/symbolic_nonlinear.py`)
to cubics, nested square roots and numeric polynomials of higher degree.
This file proves the facts its readings rest on.

## 1.  Cardano

`cardano_root`: with `A ≠ 0`, `A³ = q/2 + s` and `s² = q²/4 + p³/27`, the
value `A - p/(3A)` is a root of `x³ + p x = q`.  This is the Vieta form the
layer prints, with the stated condition `P ≠ 0` (so that `A ≠ 0`).

`depressed_cubic_unique_real_root`: when `q²/4 + p³/27 > 0` a real depressed
cubic has only one real root.  This is the stated inequality
"D > 0 (then it is the only real root)".

## 2.  Nested square roots

`biquadratic_iff`: `x⁴ + b x² + c = 0` exactly when `x²` is one of the two
quadratic branches.  The layer's tower `x = ±√((-b ± s)/2)` therefore loses
no root and adds none.

`even_quartic_factor`: when the constant term is a square `k²`, the quartic
factors into two quadratics with `m² = 2k - b`; this is the denesting step
the layer takes before falling back to a tower.

## 3.  Numeric roots

`cubic_irreducible_of_no_rational_root`: a rational polynomial of degree at
most three with no rational root is irreducible, so the layer's
`root(f, lo, hi)` generator for a cubic without a rational root is a
genuine algebraic number of degree three, not a disguised rational.

`root_of_sign_change`: a sign change of a real polynomial on `[a, b]` holds
a root there -- the check each Sturm-isolated interval in the column-3
script carries.
-/

@[expose] public section

namespace GLM.CubicRadicals

open Polynomial

/-! ## 1.  Cardano -/

/-- Cardano's formula in Vieta form: `A - p/(3A)` is a root of
`x³ + p x = q` when `A³ = q/2 + s` and `s² = q²/4 + p³/27`. -/
theorem cardano_root {A s p q : ℝ} (hA : A ≠ 0) (hA3 : A ^ 3 = q / 2 + s)
    (hs : s ^ 2 = q ^ 2 / 4 + p ^ 3 / 27) :
    (A - p / (3 * A)) ^ 3 + p * (A - p / (3 * A)) = q := by
  have hA3' : A ^ 3 ≠ 0 := pow_ne_zero 3 hA
  have hB : (-p / (3 * A)) ^ 3 = q / 2 - s := by
    have hprod : A ^ 3 * (q / 2 - s) = -p ^ 3 / 27 := by
      rw [hA3]; linear_combination (-1 : ℝ) * hs
    have hprodB : A ^ 3 * (-p / (3 * A)) ^ 3 = -p ^ 3 / 27 := by
      field_simp; ring
    exact mul_left_cancel₀ hA3' (hprodB.trans hprod.symm)
  have key : (A - p / (3 * A)) ^ 3 + p * (A - p / (3 * A))
      = A ^ 3 + (-p / (3 * A)) ^ 3 := by
    field_simp; ring
  rw [key, hA3, hB]; ring

/-- When `q²/4 + p³/27 > 0` the depressed cubic `x³ + p x = q` has only one
real root. -/
theorem depressed_cubic_unique_real_root {p q r t : ℝ}
    (hD : q ^ 2 / 4 + p ^ 3 / 27 > 0)
    (hr : r ^ 3 + p * r = q) (ht : t ^ 3 + p * t = q) : t = r := by
  have hfac : (t - r) * (t ^ 2 + t * r + r ^ 2 + p) = 0 := by
    linear_combination ht - hr
  rcases mul_eq_zero.1 hfac with h | h
  · linarith
  · exfalso
    have h1 : -3 * r ^ 2 - 4 * p = (2 * t + r) ^ 2 := by linear_combination -4 * h
    have hid : 4 * p ^ 3 + 27 * q ^ 2 = -((2 * t + r) ^ 2 * (3 * r ^ 2 + p) ^ 2) := by
      rw [← h1, ← hr]; ring
    have hnn : 0 ≤ (2 * t + r) ^ 2 * (3 * r ^ 2 + p) ^ 2 := by positivity
    nlinarith

/-! ## 2.  Nested square roots -/

/-- A biquadratic vanishes exactly when `x²` is one of the two quadratic
branches `(-b ± s)/2`, where `s * s = b² - 4c`. -/
theorem biquadratic_iff {K : Type*} [Field K] [NeZero (2 : K)] {b c s : K}
    (hs : s * s = b ^ 2 - 4 * c) (x : K) :
    x ^ 4 + b * x ^ 2 + c = 0 ↔
      x ^ 2 = (-b + s) / 2 ∨ x ^ 2 = (-b - s) / 2 := by
  have h2 : (2 : K) ≠ 0 := NeZero.ne 2
  have hfac : x ^ 4 + b * x ^ 2 + c
      = (x ^ 2 - (-b + s) / 2) * (x ^ 2 - (-b - s) / 2) := by
    field_simp; linear_combination hs
  rw [hfac, mul_eq_zero, sub_eq_zero, sub_eq_zero]

/-- An even quartic whose constant term is a square `k²` factors into two
quadratics, with `m * m = 2k - b`. -/
theorem even_quartic_factor {R : Type*} [CommRing R] {b k m : R}
    (hm : m * m = 2 * k - b) (x : R) :
    x ^ 4 + b * x ^ 2 + k ^ 2 = (x ^ 2 + m * x + k) * (x ^ 2 - m * x + k) := by
  linear_combination x ^ 2 * hm

/-! ## 3.  Numeric roots -/

/-- A rational polynomial of degree one to three with no rational root is
irreducible. -/
theorem cubic_irreducible_of_no_rational_root {f : ℚ[X]}
    (hdeg : f.natDegree ∈ Finset.Icc 1 3) (hroot : ∀ x : ℚ, ¬ f.IsRoot x) :
    Irreducible f :=
  Polynomial.irreducible_of_degree_le_three_of_not_isRoot hdeg hroot

/-- A sign change of a real polynomial on `[a, b]` holds a root there. -/
theorem root_of_sign_change (f : ℝ[X]) {a b : ℝ} (hab : a ≤ b)
    (h : f.eval a * f.eval b ≤ 0) : ∃ x ∈ Set.Icc a b, f.eval x = 0 := by
  have hc : ContinuousOn (fun x => f.eval x) (Set.Icc a b) :=
    f.continuous.continuousOn
  rcases le_total (f.eval a) 0 with ha | ha
  · have hb : 0 ≤ f.eval b ∨ f.eval a = 0 := by
      rcases lt_or_eq_of_le ha with ha' | ha'
      · left; nlinarith
      · right; exact ha'
    rcases hb with hb | hb
    · exact intermediate_value_Icc hab hc ⟨ha, hb⟩
    · exact ⟨a, ⟨le_rfl, hab⟩, hb⟩
  · have hb : f.eval b ≤ 0 ∨ f.eval a = 0 := by
      rcases lt_or_eq_of_le ha with ha' | ha'
      · left; nlinarith
      · right; exact ha'.symm
    rcases hb with hb | hb
    · exact intermediate_value_Icc' hab hc ⟨hb, ha⟩
    · exact ⟨a, ⟨le_rfl, hab⟩, hb⟩

end GLM.CubicRadicals
