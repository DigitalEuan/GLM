module

public import Mathlib

/-!
# Kinds of quantity: what a dimension check alone gets wrong

The formal half of `studies/MEASURANDS_STUDY.md` (Phase 86,
`glm_universal.runtime.measurands`). A dimension check compares the exponents
of the seven SI base units; the kinds of quantity it cannot tell apart are
exactly the ones this file is about.

* `offset_difference_free` — an affine change of temperature scale
  `T ↦ a * T + b` (degrees Celsius or Fahrenheit into kelvins) carries a
  *difference* of two levels by the factor alone: the offset cancels. So a
  temperature difference converts with the factor, and a level with factor
  and offset.
* `level_as_difference_depends_on_zero` — a law read with a *level* where it
  wants a difference (`Q = m c T` with `T` a thermodynamic temperature)
  changes its value under a shift of the zero of the scale whenever
  `m c ≠ 0`: the answer depends on the arbitrary zero, which is why
  `LEVEL_AS_DIFFERENCE` is refused.
* `difference_law_zero_free` — the same law read with a difference of two
  levels does not depend on the zero.
* `fahrenheit_kelvin` — the declared Fahrenheit reading is the Celsius
  reading composed with the Fahrenheit-to-Celsius map, exactly.
* `hertz_as_angular_velocity_wrong` — reading a frequency `f` in hertz as an
  angular velocity is wrong by `2π` for every `f ≠ 0`: `2 * π * f ≠ f`.
* `absolute_zero_celsius` — the Celsius level `-273.15` is `0 K`, and a
  Celsius level below it is a negative thermodynamic temperature.
-/

@[expose] public section

namespace GLM.MeasurandKinds

/-- **Differences are offset-free.** -/
theorem offset_difference_free (a b T₁ T₂ : ℚ) :
    (a * T₂ + b) - (a * T₁ + b) = a * (T₂ - T₁) := by
  ring

/-- **A level read as a difference depends on the zero.** Shifting the zero
of the scale by `z ≠ 0` changes `m * c * T` whenever `m * c ≠ 0`. -/
theorem level_as_difference_depends_on_zero (m c T z : ℚ) (hmc : m * c ≠ 0)
    (hz : z ≠ 0) : m * c * (T + z) ≠ m * c * T := by
  intro h
  have : m * c * z = 0 := by linarith
  rcases mul_eq_zero.mp this with h1 | h1
  · exact hmc h1
  · exact hz h1

/-- **The same law read with a difference does not depend on the zero.** -/
theorem difference_law_zero_free (m c T₁ T₂ z : ℚ) :
    m * c * ((T₂ + z) - (T₁ + z)) = m * c * (T₂ - T₁) := by
  ring

/-- Degrees Celsius into kelvins, as a level. -/
def celsiusLevel (t : ℚ) : ℚ := t + 27315 / 100

/-- Degrees Fahrenheit into degrees Celsius, as a level. -/
def fahrenheitToCelsius (t : ℚ) : ℚ := (t - 32) * 5 / 9

/-- Degrees Fahrenheit into kelvins, as a level: the declared reading
`T = t * 5/9 + 45967/180`. -/
def fahrenheitLevel (t : ℚ) : ℚ := t * (5 / 9) + 45967 / 180

/-- **The declared Fahrenheit reading is the composite.** -/
theorem fahrenheit_kelvin (t : ℚ) :
    fahrenheitLevel t = celsiusLevel (fahrenheitToCelsius t) := by
  unfold fahrenheitLevel celsiusLevel fahrenheitToCelsius
  ring

/-- **Absolute zero in degrees Celsius**, and a Celsius level below it is a
negative thermodynamic temperature. -/
theorem absolute_zero_celsius (t : ℚ) :
    celsiusLevel (-27315 / 100) = 0 ∧ (t < -27315 / 100 → celsiusLevel t < 0) := by
  unfold celsiusLevel
  constructor
  · ring
  · intro h
    linarith

/-- **Hertz read as an angular velocity is wrong by `2π`.** -/
theorem hertz_as_angular_velocity_wrong (f : ℝ) (hf : f ≠ 0) :
    2 * Real.pi * f ≠ f := by
  intro h
  have h1 : (2 * Real.pi - 1) * f = 0 := by linarith
  rcases mul_eq_zero.mp h1 with h2 | h2
  · have := Real.pi_gt_three
    linarith
  · exact hf h2

end GLM.MeasurandKinds
