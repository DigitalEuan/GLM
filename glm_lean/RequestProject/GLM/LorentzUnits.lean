import Mathlib
import RequestProject.GLM.LorentzImproper

/-!
# Improper Lorentz maps times a change of units (Phase 181)

*Created 22 October 2026.*

The formal half of `studies/IMPROPER_UNITS_STUDY.md`. Phase 179 declared the
four components of the Lorentz group as families of `tool frame` in 1+2
dimensions, and Phase 178 a proper orthochronous Lorentz map times a change
of units (`lorentz_units`); an *improper* Lorentz map times a change of units
was the one improper case still refused (`STATUS.md` §2.1 item 10). This file
states what declaring it rests on. A map `M` is *conformal with ratio `k`*
when `Mᵀ η M = k η`: it keeps the Minkowski form up to the factor `k`.

* `smul_lorentz_conformal` — a Lorentz map times `s` is conformal with ratio
  `s²`;
* `conformal_ratio` — the ratio is read off the time column:
  `k = M₀₀² − M₁₀² − M₂₀²`;
* `conformal_split` — a map conformal with ratio `s²`, `s ≠ 0`, is `s` times
  the Lorentz map `s⁻¹ M`: the change of units divides out;
* `det_smul_three`, `conformal_det_sign`, `conformal_time_sign` — with
  `s > 0` the determinant of `M` has the sign of the Lorentz factor's
  determinant and `M₀₀` the sign of its time–time entry, so the component of
  the Lorentz factor is read from `M` itself, as the tool does;
* `conformal_eight` — **every map conformal with a positive square ratio is
  `s · B · P^a · T^b`** with `s > 0` and `B` proper orthochronous: the
  improper families times units, with the three proper and improper
  families of Phase 179, exhaust such maps;
* `scaled_plane_partner` — two demonstrations never fix the component of a
  scaled Lorentz map either: `s · M` times the reflection in the inputs'
  plane agrees with `s · M` on both inputs and has the opposite determinant
  (from `plane_partner`). The span guard's reason holds for the new families.
-/

namespace GLM.LorentzUnits

open Matrix GLM.LorentzPlane GLM.LorentzImproper

/-- `M` keeps the Minkowski form up to the factor `k`. -/
def IsConformal (M : Matrix (Fin 3) (Fin 3) ℚ) (k : ℚ) : Prop := Mᵀ * eta * M = k • eta

theorem smul_lorentz_conformal {L : Matrix (Fin 3) (Fin 3) ℚ} (hL : IsLorentz L) (s : ℚ) :
    IsConformal (s • L) (s ^ 2) := by
  unfold IsConformal
  rw [transpose_smul, Matrix.smul_mul, Matrix.smul_mul, Matrix.mul_smul, hL, smul_smul, sq]

/-- The ratio is read off the time column. -/
theorem conformal_ratio {M : Matrix (Fin 3) (Fin 3) ℚ} {k : ℚ} (h : IsConformal M k) :
    k = M 0 0 ^ 2 - M 1 0 ^ 2 - M 2 0 ^ 2 := by
  have h00 := congrFun (congrFun h 0) 0
  simp [eta, Matrix.mul_apply, Fin.sum_univ_three] at h00
  linear_combination -h00

/-- **The change of units divides out**: a map conformal with ratio `s²` is
`s` times a Lorentz map. -/
theorem conformal_split {M : Matrix (Fin 3) (Fin 3) ℚ} {s : ℚ} (hs : s ≠ 0)
    (h : IsConformal M (s ^ 2)) : IsLorentz (s⁻¹ • M) ∧ M = s • (s⁻¹ • M) := by
  refine ⟨?_, by rw [smul_smul, mul_inv_cancel₀ hs, one_smul]⟩
  unfold IsLorentz
  unfold IsConformal at h
  rw [transpose_smul, Matrix.smul_mul, Matrix.smul_mul, Matrix.mul_smul, h, smul_smul,
    smul_smul]
  have : s⁻¹ * s⁻¹ * s ^ 2 = 1 := by field_simp
  rw [this, one_smul]

theorem det_smul_three (s : ℚ) (L : Matrix (Fin 3) (Fin 3) ℚ) : (s • L).det = s ^ 3 * L.det := by
  rw [Matrix.det_smul, Fintype.card_fin]

/-- With `s > 0` the determinant of `s · L` has the sign of `det L`. -/
theorem conformal_det_sign {L : Matrix (Fin 3) (Fin 3) ℚ} (hL : IsLorentz L) {s : ℚ}
    (hs : 0 < s) : (0 < (s • L).det ↔ L.det = 1) := by
  rw [det_smul_three]
  have hd : L.det = 1 ∨ L.det = -1 := by
    have := lorentz_det_sq hL
    have : (L.det - 1) * (L.det + 1) = 0 := by linear_combination this
    rcases mul_eq_zero.mp this with h | h
    · exact Or.inl (by linarith)
    · exact Or.inr (by linarith)
  have h3 : 0 < s ^ 3 := by positivity
  rcases hd with h | h <;> rw [h] <;> constructor <;> intro hh <;> nlinarith

/-- With `s > 0` the time–time entry of `s · L` has the sign of `L₀₀`. -/
theorem conformal_time_sign (L : Matrix (Fin 3) (Fin 3) ℚ) {s : ℚ} (hs : 0 < s) :
    (0 < (s • L) 0 0 ↔ 0 < L 0 0) := by
  rw [Matrix.smul_apply, smul_eq_mul]
  constructor
  · intro h; by_contra h'; push_neg at h'; nlinarith
  · intro h; positivity

/-- **Every map conformal with a positive square ratio is `s · B · P^a · T^b`**
with `s > 0` and `B` proper orthochronous. -/
theorem conformal_eight {M : Matrix (Fin 3) (Fin 3) ℚ} {s : ℚ} (hs : 0 < s)
    (h : IsConformal M (s ^ 2)) :
    ∃ B, IsProperOrtho B ∧
      (M = s • B ∨ M = s • (B * parity) ∨ M = s • (B * timeRev) ∨
        M = s • (B * parity * timeRev)) := by
  obtain ⟨hL, hM⟩ := conformal_split hs.ne' h
  obtain ⟨B, hB, hc⟩ := lorentz_four_components hL
  refine ⟨B, hB, ?_⟩
  rcases hc with hc | hc | hc | hc <;> rw [hM, hc] <;> simp

/-- **Two demonstrations never fix the component of a scaled Lorentz map.** -/
theorem scaled_plane_partner {M : Matrix (Fin 3) (Fin 3) ℚ} (hM : IsLorentz M) (s : ℚ)
    (a b : Fin 3 → ℚ)
    (hq : crossEta a b 0 ^ 2 - crossEta a b 1 ^ 2 - crossEta a b 2 ^ 2 ≠ 0) :
    let R := householder (crossEta a b 0) (crossEta a b 1) (crossEta a b 2)
    IsLorentz (M * R) ∧ (s • (M * R)).det = -(s • M).det ∧
      (s • (M * R)) *ᵥ a = (s • M) *ᵥ a ∧ (s • (M * R)) *ᵥ b = (s • M) *ᵥ b := by
  intro R
  obtain ⟨h1, h2, h3, h4, -⟩ := plane_partner hM a b hq
  refine ⟨h1, ?_, ?_, ?_⟩
  · rw [det_smul_three, det_smul_three, h2]; ring
  · rw [Matrix.smul_mulVec, Matrix.smul_mulVec, h3]
  · rw [Matrix.smul_mulVec, Matrix.smul_mulVec, h4]

/-- A concrete instance: twice the reflection `py ↦ −py` is conformal with
ratio `4`, improper, and keeps the direction of time. -/
theorem two_parity_conformal :
    IsConformal ((2 : ℚ) • parity) 4 ∧ ((2 : ℚ) • parity).det = -8 ∧
      0 < ((2 : ℚ) • parity) 0 0 := by
  refine ⟨?_, ?_, ?_⟩
  · have := smul_lorentz_conformal parity_lorentz 2
    norm_num at this
    exact this
  · rw [det_smul_three, det_parity]; norm_num
  · simp [parity]

end GLM.LorentzUnits
