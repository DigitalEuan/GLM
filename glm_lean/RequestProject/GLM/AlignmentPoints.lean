/-
# The substrate's "alignment points", audited

The archive's lightspeed synthesis tabulates eight *alignment points* between
the substrate's own numbers and measured physical constants.  `FitCapacity.lean`
scores three of them for surprisal; this file finishes the audit by checking the
two that are of a different kind, and by naming the common shape of all of them.

`Calibration.lean` covers the chain that tries to produce `c`; the seeds
`ℳ = πφe`, `w = ℳ − 13` and `L = w/13` are those of `FitCapacity.lean`.

* **P6, the velocity.**  The substrate sets `γ = ℳ/13` and reads a velocity off
  `γ = 1/√(1 − v²/c²)`, obtaining `v/c = 0.3389`.  But `GLM.FitCapacity.derived_layer_is_definitional` says
  `ℳ/13 = 1 + L` *exactly* — the "exact identity" is the definition of `L`
  rewritten — so `gammaS_eq` and `vOverC_bounds` verify the number while
  establishing that nothing is predicted by it.
* **P4, the electron mass.**  `m_e = Y²·w·24⁴·29⁴·(hΔν_Cs/c²)`.  Here the
  dimensional situation is *legitimate*: an action, a frequency and a speed do
  determine a mass (`mass_from_action_frequency_speed`), unlike the action and
  energy of the lightspeed chain.  The accuracy, however, is not as quoted:
  `electronMass_error` proves the relative error lies between `0.0090 %` and
  `0.0093 %`, against a claimed `0.007 %`.  That is a correction to the source
  table, not a confirmation of it.
* **The common shape.**  Every alignment point has the form
  `measured ≈ (dimensionless substrate number) × (SI-defined unit)`, with the
  unit `1` for the ratios and `hΔν_Cs/c²` for the mass.  The substrate supplies
  dimensionless numbers; the SI supplies the dimensions.  That is the honest
  reading, and `GLM.Calibration.speed_not_from_action_and_energy` is what
  happens when it is violated.
-/
import RequestProject.GLM.Calibration
import RequestProject.GLM.FitCapacity

namespace GLM.AlignmentPoints

open GLM.FitCapacity (phi eSeed monad wobble leak relErr monad_bounds wobble_bounds
  leak_bounds wobble_pos pi_bounds)

/-! ## P6 — the velocity alignment is a tautology -/

/-- The substrate Lorentz factor `γ = ℳ/13`. -/
noncomputable def gammaS : ℝ := monad / 13

/-- **`ℳ/13 = 1 + L` exactly.**  P6's "exact identity" status carries no
physical content: it is the definition of the leak, rewritten. -/
theorem gammaS_eq : gammaS = 1 + leak := by
  unfold gammaS FitCapacity.leak FitCapacity.wobble
  ring

theorem gammaS_bounds : 1.06289078 < gammaS ∧ gammaS < 1.06289080 := by
  obtain ⟨h1, h2⟩ := leak_bounds
  rw [gammaS_eq]
  constructor <;> linarith

/-- The substrate velocity `v/c = √(1 − 1/γ²)`. -/
noncomputable def vOverC : ℝ := Real.sqrt (1 - 1 / gammaS ^ 2)

/-- The quoted `0.339` is right — as a consequence of the definition, not as a
measurement. -/
theorem vOverC_bounds : 0.338877 < vOverC ∧ vOverC < 0.338878 := by
  obtain ⟨hg1, hg2⟩ := gammaS_bounds
  have hgp : (0:ℝ) < gammaS := by linarith
  have harg : 0.1148380 < 1 - 1 / gammaS ^ 2 ∧ 1 - 1 / gammaS ^ 2 < 0.1148382 := by
    constructor
    · have h : 1 / gammaS ^ 2 < 0.8851620 := by
        rw [div_lt_iff₀ (by positivity)]; nlinarith
      linarith
    · have h : (0.8851618 : ℝ) < 1 / gammaS ^ 2 := by
        rw [lt_div_iff₀ (by positivity)]; nlinarith
      linarith
  obtain ⟨ha1, ha2⟩ := harg
  constructor
  · have h : (0.338877 : ℝ) ^ 2 < 1 - 1 / gammaS ^ 2 := by nlinarith
    calc (0.338877 : ℝ) = Real.sqrt (0.338877 ^ 2) := (Real.sqrt_sq (by norm_num)).symm
      _ < vOverC := Real.sqrt_lt_sqrt (by positivity) h
  · have h : 1 - 1 / gammaS ^ 2 < (0.338878 : ℝ) ^ 2 := by nlinarith
    calc vOverC < Real.sqrt (0.338878 ^ 2) := Real.sqrt_lt_sqrt (by nlinarith) h
      _ = 0.338878 := Real.sqrt_sq (by norm_num)

/-! ## P4 — the electron mass, and the correction to the quoted accuracy -/

/-- Caesium hyperfine transition frequency, Hz (exact, SI 2019). -/
def dnuCs : ℚ := 9192631770

/-- The SI mass quantum `h·Δν_Cs/c²`, kg — exact by the SI 2019 definitions. -/
def siMassUnit : ℚ := Calibration.hSI * dnuCs / Calibration.cSI ^ 2

theorem siMassUnit_bounds : (6 : ℚ) / 10 ^ 41 < siMassUnit ∧ siMassUnit < 7 / 10 ^ 41 := by
  constructor <;> · rw [siMassUnit, dnuCs, Calibration.hSI, Calibration.cSI]; norm_num

/-- The full SI prefactor `24⁴·29⁴·h·Δν_Cs/c²`, kg. -/
def massScale : ℚ := 24 ^ 4 * 29 ^ 4 * siMassUnit

theorem massScale_eq :
    massScale = 142431752991103838545059 / (895602657382830078125 * 10 ^ 31) := by
  rw [massScale, siMassUnit, dnuCs, Calibration.hSI, Calibration.cSI]; norm_num

theorem massScale_bounds :
    (15903453 : ℚ) / 10 ^ 36 < massScale ∧ massScale < 15903454 / 10 ^ 36 := by
  rw [massScale_eq]; constructor <;> norm_num

/-- Substrate prediction for the electron mass, kg. -/
noncomputable def electronMassPred : ℝ := Y ^ 2 * wobble * (massScale : ℝ)

/-- CODATA electron mass, kg. -/
noncomputable def electronMassTarget : ℝ := 9.1093837015 / 10 ^ 31

/-- Tighter bounds on the read quantum than `Calibration.Y_bounds`, using the
20-digit `π` bound. -/
theorem Y_bounds_tight : 0.26467543 < Y ∧ Y < 0.26467544 := by
  obtain ⟨h1, h2⟩ := pi_bounds
  have hden : (0:ℝ) < Real.pi ^ 2 + 2 := by positivity
  have hY : Y = Real.pi / (Real.pi ^ 2 + 2) := by
    unfold Y; field_simp
  rw [hY]
  constructor
  · rw [lt_div_iff₀ hden]; nlinarith
  · rw [div_lt_iff₀ hden]; nlinarith

theorem electronMassPred_bounds :
    9108541 / 10 ^ 37 < electronMassPred ∧ electronMassPred < 9108550 / 10 ^ 37 := by
  obtain ⟨hy1, hy2⟩ := Y_bounds_tight
  obtain ⟨hw1, hw2⟩ := wobble_bounds
  have hy0 : (0:ℝ) < Y := Y_pos
  have hw0 : (0:ℝ) < wobble := wobble_pos
  have hsq : (7005308 : ℝ) / 10 ^ 8 < Y ^ 2 ∧ Y ^ 2 < 7005309 / 10 ^ 8 := by
    constructor <;> nlinarith
  obtain ⟨hs1, hs2⟩ := hsq
  have hprod : (5727401 : ℝ) / 10 ^ 8 < Y ^ 2 * wobble ∧
      Y ^ 2 * wobble < 5727403 / 10 ^ 8 := by
    constructor <;> nlinarith
  obtain ⟨hp1, hp2⟩ := hprod
  have hm1 : (15903453 : ℝ) / 10 ^ 36 < (massScale : ℝ) := by
    have h : ((15903453 / 10 ^ 36 : ℚ) : ℝ) < (massScale : ℝ) := by
      exact_mod_cast massScale_bounds.1
    push_cast at h; exact h
  have hm2 : (massScale : ℝ) < 15903454 / 10 ^ 36 := by
    have h : (massScale : ℝ) < ((15903454 / 10 ^ 36 : ℚ) : ℝ) := by
      exact_mod_cast massScale_bounds.2
    push_cast at h; exact h
  rw [electronMassPred]
  constructor
  · calc (9108541 : ℝ) / 10 ^ 37 < 5727401 / 10 ^ 8 * (15903453 / 10 ^ 36) := by norm_num
      _ ≤ Y ^ 2 * wobble * (massScale : ℝ) :=
          mul_le_mul hp1.le hm1.le (by norm_num) (by positivity)
  · calc Y ^ 2 * wobble * (massScale : ℝ)
        < 5727403 / 10 ^ 8 * (15903454 / 10 ^ 36) :=
          mul_lt_mul'' hp2 hm2 (by positivity) (by positivity)
      _ < 9108550 / 10 ^ 37 := by norm_num

/-- **A correction to the source table.**  The relative error of the P4 mass
formula is `0.0092 %`, not the quoted `0.007 %`; the bound proved here is
`0.0090 % < error < 0.0093 %`. -/
theorem electronMass_error :
    0.00009 < relErr electronMassPred electronMassTarget ∧
      relErr electronMassPred electronMassTarget < 0.000093 := by
  obtain ⟨h1, h2⟩ := electronMassPred_bounds
  have habs : |electronMassPred - electronMassTarget|
      = electronMassTarget - electronMassPred := by
    rw [abs_sub_comm, abs_of_pos]; rw [electronMassTarget]; nlinarith
  unfold relErr
  rw [habs, electronMassTarget]
  constructor
  · rw [lt_div_iff₀ (by norm_num)]; nlinarith
  · rw [div_lt_iff₀ (by norm_num)]; nlinarith

/-! ## The common shape of every alignment point -/

/-- A mass *can* be built from an action, a frequency and a speed — which is why
P4 is dimensionally legitimate where the `c`-derivation of `Calibration.lean` is
not. -/
theorem mass_from_action_frequency_speed :
    (1 : ℤ) • Calibration.dAction + (1 : ℤ) • ((0, 0, -1) : Calibration.Dim) +
      (-2 : ℤ) • Calibration.dSpeed = Calibration.dMass := by decide

end GLM.AlignmentPoints
