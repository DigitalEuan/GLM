import RequestProject.GLM.Calibration

/-!
# The work–energy anchor `κ = 190 kJ/mol`: what it fixes, what it cannot, and how fine it is (Phase 177)

*Created 21 October 2026.*

The second formal half of `studies/FRAME_OPERATOR_STUDY.md`. `Calibration.lean` already proves
that the archive's light chain returns the `c` it was given (`substrate_c_is_circular`) and that an
action and an energy fix a time but never a speed (`speed_not_from_action_and_energy`). The owner's
document `source_material/Lorentz boosts.pdf` puts `κ` beside `c` as a "calibration dial"; this
file makes that reading exact and measures how much the dial could be refined.

**κ is a unit, so every dimensionless output is free of it.**

* `cellLength_ratio_kappa_free` — the ratio of two cell lengths is `(24+T)/(24+T₀)`, the
  refractive-index law, whatever `κ` (and whatever `c`): setting the dial changes no dimensionless
  prediction, exactly as setting `c = 1` changes no physics.
* `tick_scale_inv` — rescaling `κ` by `r` rescales every dimensionful output by `1/r`, so a
  relative error in `κ` is a relative error of the same size in the tick, the cell and the
  wavelength (`tick_relative_change`).

**What κ is, in the GLM's own data.** The diatomic register
(`data_objects/_data`, read by `load_diatomic_register`) holds `D₀(Br₂) = 951/5 = 190.2 kJ/mol`
with a stated uncertainty of `3/10 kJ/mol`; the element register's homonuclear bond energy for
bromine is `193 kJ/mol`.

* `kappa_within_br2_d0` — `κ = 190` lies inside the register's interval for `D₀(Br₂)`: the anchor
  *is* the bromine dissociation energy, to its stated precision.
* `kappa_tick_ratio_d0`, `kappa_tick_ratio_bde` — moving the anchor to `190.2` moves every output
  by the factor `950/951` (−0.105 %); moving it to the element register's `193` moves it by
  `190/193` (−1.55 %). Which tabulated quantity `κ` names matters fifteen times more than its third
  significant figure.
* `kappa_relative_uncertainty_lt` — the register's own uncertainty is below `0.16 %` of the value.
* `tax_rounding_dominates_kappa` — rounding the tick budget `24 + 8Q = 27.117…` down to `27`
  (`exactTicksPerCell_bounds`) is a `0.43 %` effect, larger than the anchor's whole uncertainty
  interval (`0.32 %` wide): the dimensionless knob, not `κ`'s digits, limits the chain's
  precision.

**κ in other units.** `kappa_eV_bounds` — per particle, `κ` is `1.9692 eV` (the exact
`F = e·N_A` of the 2019 SI); `Calibration.workWavelength_bounds` already places the one-work-unit
photon at `629.6 nm`, red light.

What is *not* claimed: that `κ` is derived from the substrate (it is a measured bond energy put in
by hand), or that the dimensionless geometric work the archive scaled by `κ` predicts bond
energies — the archive's own Step 3 measured `r² = 0.0011` for that and refuted it.
-/

namespace GLM.KappaAnchor

open GLM.Calibration

/-- **Dimensionless outputs are free of the anchor.** The ratio of two cell lengths is the
refractive-index law `(24+T)/(24+T₀)`, for every `κ ≠ 0`. -/
theorem cellLength_ratio_kappa_free (kappa T₀ T : ℚ) (hk : kappa ≠ 0)
    (h₀ : ticksPerCell T₀ ≠ 0) :
    cellLength kappa T / cellLength kappa T₀ = refIndex T₀ T := by
  have hc : cSI ≠ 0 := ne_of_gt cSI_pos
  have hm : molarPlanck ≠ 0 := ne_of_gt molarPlanck_pos
  rw [cellLength_eq _ _ hk, cellLength_eq _ _ hk, refIndex]
  field_simp

/-- The same holds for any value of the speed of light put into the chain: the ratio does not
read `c` either. -/
theorem ratio_free_of_c (c' d₀ d : ℚ) (hc : c' ≠ 0) (hd : d₀ ≠ 0) :
    (c' * d) / (c' * d₀) = d / d₀ := by
  field_simp

/-- Rescaling the anchor rescales the tick inversely (restated from `Calibration.tick_scale`). -/
theorem tick_scale_inv (r kappa : ℚ) (hr : r ≠ 0) (hk : kappa ≠ 0) :
    tick (r * kappa) = tick kappa / r :=
  tick_scale r kappa hr hk

/-- **A relative error in κ is the same relative error in the tick**, with the sign reversed:
`(τ(κ') − τ(κ))/τ(κ) = (κ − κ')/κ'`. -/
theorem tick_relative_change (kappa kappa' : ℚ) (hk : kappa ≠ 0) (hk' : kappa' ≠ 0) :
    (tick kappa' - tick kappa) / tick kappa = (kappa - kappa') / kappa' := by
  have hm : molarPlanck ≠ 0 := ne_of_gt molarPlanck_pos
  rw [tick_eq _ hk, tick_eq _ hk']
  field_simp

/-- `D₀(Br₂)` as the GLM's diatomic register holds it, J·mol⁻¹. -/
def br2D0 : ℚ := 190200

/-- The register's stated uncertainty of `D₀(Br₂)`, J·mol⁻¹. -/
def br2D0Unc : ℚ := 300

/-- The element register's homonuclear bond energy of bromine, J·mol⁻¹. -/
def brBde : ℚ := 193000

/-- **The anchor is the bromine dissociation energy to its stated precision.** -/
theorem kappa_within_br2_d0 : |kappaBond - br2D0| ≤ br2D0Unc := by
  norm_num [kappaBond, br2D0, br2D0Unc, abs_le]

/-- Moving the anchor to the register's `D₀(Br₂)` multiplies every dimensionful output by
`950/951`. -/
theorem kappa_tick_ratio_d0 : tick br2D0 / tick kappaBond = 950 / 951 := by
  have hm : molarPlanck ≠ 0 := ne_of_gt molarPlanck_pos
  rw [tick_eq _ (by norm_num [br2D0]), tick_eq _ (by norm_num [kappaBond])]
  field_simp
  norm_num [br2D0, kappaBond]

/-- Moving the anchor to the element register's `193 kJ/mol` multiplies it by `190/193`. -/
theorem kappa_tick_ratio_bde : tick brBde / tick kappaBond = 190 / 193 := by
  have hm : molarPlanck ≠ 0 := ne_of_gt molarPlanck_pos
  rw [tick_eq _ (by norm_num [brBde]), tick_eq _ (by norm_num [kappaBond])]
  field_simp
  norm_num [brBde, kappaBond]

/-- The choice of tabulated quantity outweighs the third significant figure more than fourteen
times over: `1 − 190/193` against `1 − 950/951`. -/
theorem quantity_choice_dominates : 14 * (1 - 950 / 951 : ℚ) < 1 - 190 / 193 := by
  norm_num

/-- The register's uncertainty is below `0.16 %` of the value. -/
theorem kappa_relative_uncertainty_lt : br2D0Unc / br2D0 < 16 / 10000 := by
  norm_num [br2D0Unc, br2D0]

/-- **The tick-budget rounding outweighs the anchor's uncertainty.** Replacing `27` by the exact
`24 + 8Q` changes the cell by more than `0.43 %`, more than the whole relative width
`2 · 300/190200 ≈ 0.32 %` of the anchor's interval (and over two and a half times its
half-width). -/
theorem tax_rounding_dominates_kappa :
    ((2 * (br2D0Unc / br2D0) : ℚ) : ℝ) < (24 + codewordTax 8) / 27 - 1 := by
  obtain ⟨h1, _⟩ := exactTicksPerCell_bounds
  have : ((2 * (br2D0Unc / br2D0) : ℚ) : ℝ) = 2 * (300 / 190200) := by
    norm_num [br2D0Unc, br2D0]
  rw [this]
  have h27 : (27.1174 : ℝ) / 27 - 1 ≤ (24 + codewordTax 8) / 27 - 1 := by
    have := h1.le; linarith [div_le_div_of_nonneg_right this (by norm_num : (0:ℝ) ≤ 27)]
  norm_num at h27 ⊢
  linarith

/-- The elementary charge, C (exact, SI 2019). -/
def eSI : ℚ := 1602176634 / 10 ^ 28

/-- The anchor per particle, in electronvolts: `κ / (e·N_A)`. -/
def kappaEV (kappa : ℚ) : ℚ := kappa / (eSI * NA)

/-- `κ = 190 kJ/mol` is `1.9692 eV` per particle. -/
theorem kappa_eV_bounds : 19692 / 10000 < kappaEV kappaBond ∧ kappaEV kappaBond < 19693 / 10000 := by
  norm_num [kappaEV, kappaBond, eSI, NA]

end GLM.KappaAnchor
