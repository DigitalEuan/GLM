module

public import Mathlib

/-!
# The measurand register: conversions through a stated efficiency

The formal half of `studies/MEASURAND_REGISTER_STUDY.md` (Phase 87,
`glm_universal.runtime.measurand_register`). A conversion law reads
`P_out = η * P_in` with `0 < η ≤ 1`; a register measurand read as a photon's
energy gives a frequency `f = E / h`.

* `efficiency_out_le_in` — a declared conversion never gives out more power
  than it takes in (only `η ≤ 1` and `P ≥ 0` are needed).
* `naive_identity_wrong` — reading the conversion as an identity (the shared
  name `power` identified across the wheels, the efficiency dropped) is wrong
  for every `η ≠ 1` and every non-zero power: this is why the naive control
  answers wrongly.
* `derived_efficiency_gt_one` — givens with more power out than in imply an
  efficiency above 1, which is why such a derivation is refused
  `EFFICIENCY_OUT_OF_RANGE`.
* `efficiency_range_of_powers` — conversely, `0 < P_out ≤ P_in` gives an
  efficiency in `(0, 1]`.
* `conversion_compose` — two conversions in series are one conversion whose
  efficiency is the product, and the product stays in `(0, 1]`.
* `photon_threshold_frequency_monotone` — read through `E = h f` with `h > 0`,
  a larger threshold energy is a larger frequency.
* `capacitor_energy_half_QV` — on the capacitor wheel, `Q = C V` makes the
  stored energy `½ C V²` equal to `½ Q V`; with `Q = e` and `V = 1 V` this is
  half an electronvolt.
-/

@[expose] public section

namespace GLM.MeasurandRegister

/-- **A conversion gives out no more than it takes in.** -/
theorem efficiency_out_le_in (η P : ℚ) (h1 : η ≤ 1) (hP : 0 ≤ P) :
    η * P ≤ P := by
  nlinarith

/-- **The naive identity is wrong whenever the efficiency is not 1.** -/
theorem naive_identity_wrong (η P : ℚ) (hη : η ≠ 1) (hP : P ≠ 0) :
    η * P ≠ P := by
  intro h
  apply hη
  have : (η - 1) * P = 0 := by linarith
  rcases mul_eq_zero.mp this with h' | h'
  · linarith
  · exact absurd h' hP

/-- **More power out than in is an efficiency above 1.** -/
theorem derived_efficiency_gt_one (Pin Pout : ℚ) (hin : 0 < Pin) (h : Pin < Pout) :
    1 < Pout / Pin := by
  rw [lt_div_iff₀ hin]
  linarith

/-- **Powers with `0 < P_out ≤ P_in` give an efficiency in `(0, 1]`.** -/
theorem efficiency_range_of_powers (Pin Pout : ℚ) (hout : 0 < Pout) (h : Pout ≤ Pin) :
    0 < Pout / Pin ∧ Pout / Pin ≤ 1 := by
  have hin : 0 < Pin := lt_of_lt_of_le hout h
  refine ⟨div_pos hout hin, ?_⟩
  rw [div_le_one hin]
  exact h

/-- **Conversions in series compose**, and the composite efficiency stays in
`(0, 1]`. -/
theorem conversion_compose (η₁ η₂ P : ℚ) (h₁ : 0 < η₁) (h₁' : η₁ ≤ 1)
    (h₂ : 0 < η₂) (h₂' : η₂ ≤ 1) :
    η₂ * (η₁ * P) = (η₁ * η₂) * P ∧ 0 < η₁ * η₂ ∧ η₁ * η₂ ≤ 1 := by
  refine ⟨by ring, mul_pos h₁ h₂, ?_⟩
  nlinarith

/-- **A larger photon threshold is a larger frequency** under `E = h f`. -/
theorem photon_threshold_frequency_monotone (h E₁ E₂ : ℚ) (hh : 0 < h) (hE : E₁ < E₂) :
    E₁ / h < E₂ / h :=
  div_lt_div_of_pos_right hE hh

/-- **The capacitor's energy is half the charge times the voltage.** -/
theorem capacitor_energy_half_QV (C V Q : ℚ) (hQ : Q = C * V) :
    1 / 2 * C * V ^ 2 = 1 / 2 * Q * V := by
  subst hQ
  ring

end GLM.MeasurandRegister
