import Mathlib
import RequestProject.Lightspeed

/-!
# The substrate constants and the "alignment points" of the lightspeed study

`LIGHTSPEED_STUDY_SYNTHESIS.md` tabulates eight "alignment points" P1–P8 between
the UBP substrate and measured physical constants.  This file gives the exact
mathematical definitions behind them (as read off `ubp_unified_v5.py`,
`UBPUltimateSubstrate.get_v6_constants` and
`UBPSourceCodeParticlePhysics.get_ultimate_predictions`) and machine-checks the
quoted accuracies.

The substrate computes with 50-term continued-fraction convergents of `π`, `φ`
and `e`; those agree with the real numbers to far more digits than any claim
here uses, so we work with the genuine reals.

```
  MONAD  = π · φ · e                     (the "triadic monad")
  WOBBLE = MONAD − ⌊MONAD⌋ = MONAD − 13  (its fractional part)
  L      = WOBBLE / 13                   (the "sink leakage")
  Y      = 1 / (π + 2/π)                 (the wobble/tax constant)
  σ      = 29/24 ,  L_s = L·σ
```

The single most clarifying identity is `monad_div_thirteen`:

    MONAD / 13  =  1 + L

so alignment point **P6** ("γ = MONAD/13, an exact identity") is not an
independent statement — it is the definition of `L` rewritten.  The velocity it
produces, `v/c = √(1 − (13/MONAD)²) = 0.33888…`, is a *definition* of a
substrate velocity, not a measured one; nothing is being predicted.

Verdicts on the quoted accuracies (all proved below):

| Point | Formula | Quoted | Verified |
|---|---|---|---|
| P6 | `v/c = √(1 − 1/(1+L)²)` | `0.339` | `0.33887 < v/c < 0.33889` ✓ |
| P2 | `m_μ/m_e = 169/WOBBLE` | `0.03 %` | `0.0293 % … 0.0294 %` ✓ |
| P7 | `1/α = 220 − 83 + L` | `0.02 %` | `0.0196 % … 0.0197 %` ✓ |
| P8 | `m_p/m_e = 1836 + 2L_s` | `0.001 %` | `0.0000374 %` — much better than quoted |
| P4 | `m_e = Y²·WOBBLE·24⁴·29⁴·hΔν_Cs/c²` | `0.007 %` | `0.0092 %` (proved in `0.0090 %…0.0093 %`) ✗ |
-/

namespace UBPLightspeed

open scoped Real

/-! ## 1. Definitions -/

/-- The golden ratio, `φ = (1+√5)/2`. -/
noncomputable def phi : ℝ := (1 + Real.sqrt 5) / 2

/-- The triadic monad `MONAD = π·φ·e`. -/
noncomputable def monad : ℝ := Real.pi * phi * Real.exp 1

/-- `WOBBLE`, the fractional part of `MONAD`. -/
noncomputable def wobble : ℝ := monad - 13

/-- The sink leakage `L = WOBBLE/13`. -/
noncomputable def sinkL : ℝ := wobble / 13

/-- The stereoscopic factor `σ = 29/24`. -/
noncomputable def sigmaS : ℝ := 29 / 24

/-- `L_s = L·σ`. -/
noncomputable def sinkLs : ℝ := sinkL * sigmaS

/-! ## 2. Numerical bounds -/

theorem sqrt5_bounds : 2.2360679774 < Real.sqrt 5 ∧ Real.sqrt 5 < 2.2360679775 := by
  have h5 : Real.sqrt 5 ^ 2 = 5 := Real.sq_sqrt (by norm_num)
  have hp : 0 < Real.sqrt 5 := Real.sqrt_pos.mpr (by norm_num)
  constructor <;> nlinarith [h5, hp]

theorem phi_bounds : 1.6180339887 < phi ∧ phi < 1.61803398875 := by
  obtain ⟨h1, h2⟩ := sqrt5_bounds
  constructor <;> · rw [phi]; linarith

theorem pi_bounds : 3.1415926535 < Real.pi ∧ Real.pi < 3.1415926536 := by
  refine ⟨by linarith [Real.pi_gt_d20], by linarith [Real.pi_lt_d20]⟩

theorem exp_one_bounds : 2.7182818283 < Real.exp 1 ∧ Real.exp 1 < 2.7182818286 :=
  ⟨Real.exp_one_gt_d9, Real.exp_one_lt_d9⟩

theorem pi_mul_phi_bounds : 5.08320369 < Real.pi * phi ∧ Real.pi * phi < 5.08320370 := by
  obtain ⟨hp1, hp2⟩ := pi_bounds
  obtain ⟨hf1, hf2⟩ := phi_bounds
  constructor <;> nlinarith

/-- `MONAD = 13.81758…`; in particular `⌊MONAD⌋ = 13`, which is what makes
`WOBBLE = MONAD − 13` the fractional part. -/
theorem monad_bounds : 13.8175802 < monad ∧ monad < 13.8175803 := by
  obtain ⟨h1, h2⟩ := pi_mul_phi_bounds
  obtain ⟨he1, he2⟩ := exp_one_bounds
  constructor <;> · rw [monad]; nlinarith

theorem monad_floor : (13 : ℝ) < monad ∧ monad < 14 := by
  obtain ⟨h1, h2⟩ := monad_bounds; exact ⟨by linarith, by linarith⟩

theorem wobble_bounds : 0.8175802 < wobble ∧ wobble < 0.8175803 := by
  obtain ⟨h1, h2⟩ := monad_bounds
  exact ⟨by rw [wobble]; linarith, by rw [wobble]; linarith⟩

theorem wobble_pos : 0 < wobble := by have := wobble_bounds.1; linarith

theorem sinkL_bounds : 0.06289078 < sinkL ∧ sinkL < 0.06289080 := by
  obtain ⟨h1, h2⟩ := wobble_bounds
  constructor <;> · rw [sinkL]; linarith

/-! ## 3. P6 — the "velocity alignment" is a tautology

The substrate sets `γ = MONAD/13` and then reads off `v/c` from
`γ = 1/√(1−v²/c²)`.  But `MONAD = 13 + WOBBLE` and `L = WOBBLE/13`, so: -/

/-- **`MONAD/13 = 1 + L` exactly.**  Alignment point P6 is the definition of the
sink leakage `L` written in another way, so its "EXACT IDENTITY" status carries
no physical content. -/
theorem monad_div_thirteen : monad / 13 = 1 + sinkL := by
  rw [sinkL, wobble]; ring

/-- The substrate Lorentz factor. -/
noncomputable def gammaS : ℝ := monad / 13

theorem gammaS_eq : gammaS = 1 + sinkL := monad_div_thirteen

theorem gammaS_bounds : 1.06289078 < gammaS ∧ gammaS < 1.06289080 := by
  obtain ⟨h1, h2⟩ := sinkL_bounds
  rw [gammaS_eq]; constructor <;> linarith

/-- The substrate velocity `v/c = √(1 − 1/γ²)`. -/
noncomputable def vOverC : ℝ := Real.sqrt (1 - 1 / gammaS ^ 2)

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

/-! ## 4. P2 — the muon/electron mass ratio -/

/-- Measured `m_μ/m_e = 206.7682830` (CODATA 2018). -/
def muonRatioTarget : ℝ := 206.7682830

/-- Substrate prediction `169/WOBBLE`. -/
noncomputable def muonRatioPred : ℝ := 169 / wobble

theorem muonRatioPred_bounds : 206.7075 < muonRatioPred ∧ muonRatioPred < 206.7076 := by
  obtain ⟨h1, h2⟩ := wobble_bounds
  have hp : (0:ℝ) < wobble := wobble_pos
  constructor
  · rw [muonRatioPred, lt_div_iff₀ hp]; nlinarith
  · rw [muonRatioPred, div_lt_iff₀ hp]; nlinarith

/-- The quoted `0.03 %` is right: the relative error is `0.0293…%`. -/
theorem muonRatio_error :
    0.000293 < |muonRatioPred - muonRatioTarget| / muonRatioTarget ∧
      |muonRatioPred - muonRatioTarget| / muonRatioTarget < 0.000294 := by
  obtain ⟨h1, h2⟩ := muonRatioPred_bounds
  have habs : |muonRatioPred - muonRatioTarget| = muonRatioTarget - muonRatioPred := by
    rw [abs_sub_comm, abs_of_pos]; rw [muonRatioTarget]; linarith
  rw [habs, muonRatioTarget]
  constructor
  · rw [lt_div_iff₀ (by norm_num)]; linarith
  · rw [div_lt_iff₀ (by norm_num)]; linarith

/-! ## 5. P7 — the fine-structure constant -/

def alphaInvTarget : ℝ := 137.035999084

/-- Substrate prediction `1/α = 220 − 83 + L = 137 + L`. -/
noncomputable def alphaInvPred : ℝ := 220 - 83 + sinkL

theorem alphaInvPred_eq : alphaInvPred = 137 + sinkL := by rw [alphaInvPred]; ring

/-- The quoted `0.02 %` is right: the relative error is `0.0196…%`. -/
theorem alphaInv_error :
    0.0001962 < |alphaInvPred - alphaInvTarget| / alphaInvTarget ∧
      |alphaInvPred - alphaInvTarget| / alphaInvTarget < 0.0001963 := by
  obtain ⟨h1, h2⟩ := sinkL_bounds
  rw [alphaInvPred_eq] at *
  have habs : |137 + sinkL - alphaInvTarget| = 137 + sinkL - alphaInvTarget := by
    rw [abs_of_pos]; rw [alphaInvTarget]; linarith
  rw [habs, alphaInvTarget]
  constructor
  · rw [lt_div_iff₀ (by norm_num)]; linarith
  · rw [div_lt_iff₀ (by norm_num)]; linarith

/-! ## 6. P8 — the proton/electron mass ratio

The synthesis flags this one as "LEAKED (1836 = target)", which is the right
call: the integer `1836` *is* the answer to four digits, and `2L_s = 0.152` is a
small correction.  Its accuracy is nevertheless far better than the quoted
`0.001 %`. -/

def protonRatioTarget : ℝ := 1836.15267343

noncomputable def protonRatioPred : ℝ := 1836 + 2 * sinkLs

theorem protonRatioPred_eq : protonRatioPred = 1836 + sinkL * (29 / 12) := by
  rw [protonRatioPred, sinkLs, sigmaS]; ring

/-- The relative error is `3.7×10⁻⁷ = 0.0000374 %`, i.e. **better** than the
quoted `0.001 %` by a factor of about 27. -/
theorem protonRatio_error :
    0.00000037 < |protonRatioPred - protonRatioTarget| / protonRatioTarget ∧
      |protonRatioPred - protonRatioTarget| / protonRatioTarget < 0.00000038 := by
  obtain ⟨h1, h2⟩ := sinkL_bounds
  rw [protonRatioPred_eq]
  have habs : |1836 + sinkL * (29 / 12) - protonRatioTarget|
      = protonRatioTarget - (1836 + sinkL * (29 / 12)) := by
    rw [abs_sub_comm, abs_of_pos]; rw [protonRatioTarget]; nlinarith
  rw [habs, protonRatioTarget]
  constructor
  · rw [lt_div_iff₀ (by norm_num)]; nlinarith
  · rw [div_lt_iff₀ (by norm_num)]; nlinarith

/-! ## 7. P4 — the electron mass

`m_e = Y² · WOBBLE · 24⁴ · 29⁴ · h·Δν_Cs/c²`.

Note the structure, which is the same one as in the lightspeed chain: a
dimensionless substrate number multiplied by `h·Δν_Cs/c²`, a mass built purely
from SI-*defined* constants.  Nothing dimensionful is derived. -/

/-- The SI mass quantum `h·Δν_Cs/c²`, kg — exact by the SI 2019 definitions. -/
def siMassUnit : ℚ := hSI * dnuCs / cSI ^ 2

theorem siMassUnit_bounds :
    (6 : ℚ) / 10 ^ 41 < siMassUnit ∧ siMassUnit < 7 / 10 ^ 41 := by
  constructor <;> · rw [siMassUnit, hSI, dnuCs, cSI]; norm_num

/-- The full SI prefactor `24⁴·29⁴·h·Δν_Cs/c²`, kg. -/
def massScale : ℚ := 24 ^ 4 * 29 ^ 4 * siMassUnit

theorem massScale_eq :
    massScale = 142431752991103838545059 / (895602657382830078125 * 10 ^ 31) := by
  rw [massScale, siMassUnit, hSI, dnuCs, cSI]; norm_num

theorem massScale_bounds :
    (15903453 : ℚ) / 10 ^ 36 < massScale ∧ massScale < 15903454 / 10 ^ 36 := by
  rw [massScale_eq]; constructor <;> norm_num

/-- Substrate prediction for the electron mass, kg. -/
noncomputable def electronMassPred : ℝ := Yc ^ 2 * wobble * (massScale : ℝ)

/-- CODATA 2018 electron mass, kg. -/
noncomputable def electronMassTarget : ℝ := 9.1093837015 / 10 ^ 31

theorem Yc_bounds_tight : 0.26467543 < Yc ∧ Yc < 0.26467544 := by
  obtain ⟨h1, h2⟩ := pi_bounds
  have hden : (0:ℝ) < Real.pi ^ 2 + 2 := by positivity
  rw [Yc_eq]
  constructor
  · rw [lt_div_iff₀ hden]; nlinarith
  · rw [div_lt_iff₀ hden]; nlinarith

theorem electronMassPred_bounds :
    9108541 / 10 ^ 37 < electronMassPred ∧ electronMassPred < 9108550 / 10 ^ 37 := by
  obtain ⟨hy1, hy2⟩ := Yc_bounds_tight
  obtain ⟨hw1, hw2⟩ := wobble_bounds
  have hy0 : (0:ℝ) < Yc := Yc_pos
  have hw0 : (0:ℝ) < wobble := wobble_pos
  have hsq : (7005308 : ℝ) / 10 ^ 8 < Yc ^ 2 ∧ Yc ^ 2 < 7005309 / 10 ^ 8 := by
    constructor <;> nlinarith
  obtain ⟨hs1, hs2⟩ := hsq
  have hprod : (5727401 : ℝ) / 10 ^ 8 < Yc ^ 2 * wobble ∧
      Yc ^ 2 * wobble < 5727403 / 10 ^ 8 := by
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
      _ ≤ Yc ^ 2 * wobble * (massScale : ℝ) :=
          mul_le_mul hp1.le hm1.le (by norm_num) (by positivity)
  · calc Yc ^ 2 * wobble * (massScale : ℝ)
        < 5727403 / 10 ^ 8 * (15903454 / 10 ^ 36) :=
          mul_lt_mul'' hp2 hm2 (by positivity) (by positivity)
      _ < 9108550 / 10 ^ 37 := by norm_num

/-- **Correction to the synthesis table.**  The relative error of the P4 mass
formula is `0.00919 %`, not the quoted `0.007 %`; the bound proved here is
`0.0090 % < error < 0.0093 %`. -/
theorem electronMass_error :
    0.00009 < |electronMassPred - electronMassTarget| / electronMassTarget ∧
      |electronMassPred - electronMassTarget| / electronMassTarget < 0.000093 := by
  obtain ⟨h1, h2⟩ := electronMassPred_bounds
  have habs : |electronMassPred - electronMassTarget|
      = electronMassTarget - electronMassPred := by
    rw [abs_sub_comm, abs_of_pos]; rw [electronMassTarget]; nlinarith
  rw [habs, electronMassTarget]
  constructor
  · rw [lt_div_iff₀ (by norm_num)]; nlinarith
  · rw [div_lt_iff₀ (by norm_num)]; nlinarith

/-! ## 8. The common shape of every alignment point

Each of P2, P4, P6, P7, P8 has the form

    measured quantity  ≈  (dimensionless substrate number) × (SI-defined unit)

with the unit equal to `1` for the ratios and to `h·Δν_Cs/c²` for the mass.
This is exactly the "productive reframing" the synthesis document proposes, and
it is the honest reading: the substrate supplies dimensionless numbers, the SI
supplies the dimensions.  The corresponding no-go for the lightspeed chain is
`UBPLightspeed.speed_not_from_action_and_energy`. -/

/-- A mass *can* be built from an action, a frequency and a speed — which is why
P4 is dimensionally legitimate where the `c`-derivation is not. -/
theorem mass_from_action_frequency_speed :
    (1 : ℤ) • dAction + (1 : ℤ) • (0, 0, -1) + (-2 : ℤ) • dSpeed = dMass := by decide

end UBPLightspeed
