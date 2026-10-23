import Mathlib
import RequestProject.GLM.LorentzPlane

/-!
# Improper Lorentz maps in 1+2 dimensions: reflections and time reversal (Phase 179)

*Created 22 October 2026.*

The formal half of `studies/IMPROPER_FRAME_STUDY.md`: `tool frame` in 1+2
dimensions (`reasoning/frame_plane.py`) used to refuse every improper map —
a spatial reflection, time reversal — as outside its families (`STATUS.md`
§2.1 item 10). Phase 179 declares them as families. Everything is over `ℚ`,
with the definitions of `LorentzPlane.lean`.

* `parity_lorentz`, `det_parity`, `timeRev_lorentz`, `det_timeRev`,
  `timeRev_flips_time` — the reflection `py ↦ −py` and time reversal
  `E ↦ −E` keep the Minkowski form and have determinant `−1`; time reversal
  sends the rest state into the past;
* `reflect_lorentz`, `det_reflect` — the reflection of the spatial plane in
  the line of the rational unit point `(c, s)`'s half angle,
  `rot c s * parity`, is a Lorentz map of determinant `−1`;
* `lorentz_det_sq` — every Lorentz map has determinant `±1`;
  `lorentz_time_sq` — its time–time entry satisfies
  `A₀₀² − A₁₀² − A₂₀² = 1`, so `A₀₀ ≠ 0` (`lorentz_time_ne_zero`): a Lorentz
  map either keeps the direction of time or reverses it;
* `lorentz_four_components` — every Lorentz map is a proper orthochronous one
  times `1`, `parity`, `timeRev` or `parity * timeRev`: the four declared
  families exhaust the group, and the tool's decomposition of an answer
  (`frame_plane.improper_split`) is always available;
* `householder_lorentz`, `householder_det`, `householder_fixes`,
  `householder_flips` — the reflection in the Minkowski-orthogonal complement
  of a non-null `n` is a Lorentz map of determinant `−1` that fixes every
  state orthogonal to `n` and reverses `n`;
* `plane_partner` — for any Lorentz map `M` and any two inputs whose
  Minkowski cross product is not null, `M` times the reflection in their
  plane is a Lorentz map of the opposite determinant that agrees with `M` on
  both inputs and differs from it off their plane: two demonstrations never
  fix the component, which is why a query outside the span of rank-2
  demonstrations is still refused once improper families are declared (the
  span guard of Phase 178, now a theorem rather than an argument);
* `reflection_agrees_on_plane` — a concrete instance: the identity and
  `parity` agree on `(1,0,0)` and `(2,1,0)` and disagree on `(2,0,1)`.
-/

namespace GLM.LorentzImproper

open Matrix GLM.LorentzPlane

/-- The spatial reflection `py ↦ −py`. -/
def parity : Matrix (Fin 3) (Fin 3) ℚ := !![1, 0, 0; 0, 1, 0; 0, 0, -1]

/-- Time reversal `E ↦ −E`. -/
def timeRev : Matrix (Fin 3) (Fin 3) ℚ := !![-1, 0, 0; 0, 1, 0; 0, 0, 1]

/-- The reflection of the spatial plane: `rot c s * parity`. -/
def reflect (c s : ℚ) : Matrix (Fin 3) (Fin 3) ℚ := !![1, 0, 0; 0, c, s; 0, s, -c]

theorem parity_lorentz : IsLorentz parity := by
  unfold IsLorentz parity eta
  ext i j
  fin_cases i <;> fin_cases j <;> simp [Matrix.mul_apply, Fin.sum_univ_three]

theorem det_parity : parity.det = -1 := by
  simp [parity, Matrix.det_fin_three]

theorem timeRev_lorentz : IsLorentz timeRev := by
  unfold IsLorentz timeRev eta
  ext i j
  fin_cases i <;> fin_cases j <;> simp [Matrix.mul_apply, Fin.sum_univ_three]

theorem det_timeRev : timeRev.det = -1 := by
  simp [timeRev, Matrix.det_fin_three]

/-- Time reversal sends the rest state to `(−1, 0, 0)`. -/
theorem timeRev_flips_time : timeRev *ᵥ ![1, 0, 0] = ![-1, 0, 0] := by
  ext i
  fin_cases i <;> simp [timeRev, Matrix.mulVec, dotProduct, Fin.sum_univ_three]

theorem reflect_eq (c s : ℚ) : reflect c s = rot c s * parity := by
  unfold reflect rot parity
  ext i j
  fin_cases i <;> fin_cases j <;> simp [Matrix.mul_apply, Fin.sum_univ_three]

theorem reflect_lorentz (c s : ℚ) (h : c ^ 2 + s ^ 2 = 1) : IsLorentz (reflect c s) := by
  rw [reflect_eq]
  exact lorentz_mul (rot_lorentz c s h) parity_lorentz

theorem det_reflect (c s : ℚ) (h : c ^ 2 + s ^ 2 = 1) : (reflect c s).det = -1 := by
  simp [reflect, Matrix.det_fin_three]
  nlinarith [h]

theorem det_eta : eta.det = 1 := by
  simp [eta, Matrix.det_fin_three]

/-- Every Lorentz map has determinant `±1`. -/
theorem lorentz_det_sq {A : Matrix (Fin 3) (Fin 3) ℚ} (hA : IsLorentz A) :
    A.det ^ 2 = 1 := by
  have h := congrArg Matrix.det hA
  rw [Matrix.det_mul, Matrix.det_mul, Matrix.det_transpose, det_eta] at h
  linear_combination h

/-- The time–time entry of a Lorentz map: `A₀₀² − A₁₀² − A₂₀² = 1`. -/
theorem lorentz_time_sq {A : Matrix (Fin 3) (Fin 3) ℚ} (hA : IsLorentz A) :
    A 0 0 ^ 2 - A 1 0 ^ 2 - A 2 0 ^ 2 = 1 := by
  have h := congrFun (congrFun hA 0) 0
  simp [eta, Matrix.mul_apply, Fin.sum_univ_three] at h
  linear_combination h

/-- A Lorentz map keeps or reverses the direction of time; it never sends it
sideways. -/
theorem lorentz_time_ne_zero {A : Matrix (Fin 3) (Fin 3) ℚ} (hA : IsLorentz A) :
    A 0 0 ≠ 0 := by
  intro h0
  have := lorentz_time_sq hA
  rw [h0] at this
  nlinarith [sq_nonneg (A 1 0), sq_nonneg (A 2 0)]

/-- A proper orthochronous Lorentz map. -/
def IsProperOrtho (B : Matrix (Fin 3) (Fin 3) ℚ) : Prop :=
  IsLorentz B ∧ B.det = 1 ∧ 0 < B 0 0

lemma mul_parity_00 (A : Matrix (Fin 3) (Fin 3) ℚ) : (A * parity) 0 0 = A 0 0 := by
  simp [parity, Matrix.mul_apply, Fin.sum_univ_three]

lemma mul_timeRev_00 (A : Matrix (Fin 3) (Fin 3) ℚ) : (A * timeRev) 0 0 = -A 0 0 := by
  simp [timeRev, Matrix.mul_apply, Fin.sum_univ_three]

lemma parity_mul_self : parity * parity = 1 := by
  unfold parity
  ext i j
  fin_cases i <;> fin_cases j <;> simp [Matrix.mul_apply, Fin.sum_univ_three]

lemma timeRev_mul_self : timeRev * timeRev = 1 := by
  unfold timeRev
  ext i j
  fin_cases i <;> fin_cases j <;> simp [Matrix.mul_apply, Fin.sum_univ_three]

/-- The four components: every Lorentz map is a proper orthochronous one times
`1`, `parity`, `timeRev` or `parity * timeRev`. -/
theorem lorentz_four_components {A : Matrix (Fin 3) (Fin 3) ℚ} (hA : IsLorentz A) :
    ∃ B, IsProperOrtho B ∧
      (A = B ∨ A = B * parity ∨ A = B * timeRev ∨ A = B * parity * timeRev) := by
  have hdet : A.det = 1 ∨ A.det = -1 := by
    have := lorentz_det_sq hA
    have : (A.det - 1) * (A.det + 1) = 0 := by linear_combination this
    rcases mul_eq_zero.mp this with h | h
    · exact Or.inl (by linarith)
    · exact Or.inr (by linarith)
  have h0 := lorentz_time_ne_zero hA
  rcases lt_or_gt_of_ne h0 with hneg | hpos
  · -- reverses time: `A * timeRev` keeps it
    rcases hdet with hd | hd
    · refine ⟨A * timeRev * parity, ⟨lorentz_mul (lorentz_mul hA timeRev_lorentz)
          parity_lorentz, ?_, ?_⟩, Or.inr (Or.inr (Or.inr ?_))⟩
      · rw [Matrix.det_mul, Matrix.det_mul, hd, det_timeRev, det_parity]; norm_num
      · rw [mul_parity_00, mul_timeRev_00]; linarith
      · rw [Matrix.mul_assoc (A * timeRev), parity_mul_self, Matrix.mul_one,
          Matrix.mul_assoc, timeRev_mul_self, Matrix.mul_one]
    · refine ⟨A * timeRev, ⟨lorentz_mul hA timeRev_lorentz, ?_, ?_⟩,
          Or.inr (Or.inr (Or.inl ?_))⟩
      · rw [Matrix.det_mul, hd, det_timeRev]; norm_num
      · rw [mul_timeRev_00]; linarith
      · rw [Matrix.mul_assoc, timeRev_mul_self, Matrix.mul_one]
  · rcases hdet with hd | hd
    · exact ⟨A, ⟨hA, hd, hpos⟩, Or.inl rfl⟩
    · refine ⟨A * parity, ⟨lorentz_mul hA parity_lorentz, ?_, ?_⟩, Or.inr (Or.inl ?_)⟩
      · rw [Matrix.det_mul, hd, det_parity]; norm_num
      · rw [mul_parity_00]; exact hpos
      · rw [Matrix.mul_assoc, parity_mul_self, Matrix.mul_one]

/-- The reflection in the Minkowski-orthogonal complement of `n`:
`x ↦ x − 2 ⟨n, x⟩ n / ⟨n, n⟩` (a Householder map for the form `η`). -/
def householder (n0 n1 n2 : ℚ) : Matrix (Fin 3) (Fin 3) ℚ :=
  let q := n0 ^ 2 - n1 ^ 2 - n2 ^ 2
  !![1 - 2 * n0 * n0 / q, 2 * n0 * n1 / q, 2 * n0 * n2 / q;
     -(2 * n1 * n0 / q), 1 + 2 * n1 * n1 / q, 2 * n1 * n2 / q;
     -(2 * n2 * n0 / q), 2 * n2 * n1 / q, 1 + 2 * n2 * n2 / q]

theorem householder_lorentz (n0 n1 n2 : ℚ) (hq : n0 ^ 2 - n1 ^ 2 - n2 ^ 2 ≠ 0) :
    IsLorentz (householder n0 n1 n2) := by
  unfold IsLorentz householder eta
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [Matrix.mul_apply, Fin.sum_univ_three] <;> field_simp <;> ring

theorem householder_det (n0 n1 n2 : ℚ) (hq : n0 ^ 2 - n1 ^ 2 - n2 ^ 2 ≠ 0) :
    (householder n0 n1 n2).det = -1 := by
  simp [householder, Matrix.det_fin_three]
  field_simp
  ring

/-- It fixes every state Minkowski-orthogonal to `n`. -/
theorem householder_fixes (n0 n1 n2 : ℚ) (x : Fin 3 → ℚ)
    (h : x 0 * n0 - x 1 * n1 - x 2 * n2 = 0) : householder n0 n1 n2 *ᵥ x = x := by
  ext i
  fin_cases i <;> simp [householder, Matrix.mulVec, dotProduct, Fin.sum_univ_three]
  · linear_combination (-2 * n0 / (n0 ^ 2 - n1 ^ 2 - n2 ^ 2)) * h
  · linear_combination (-2 * n1 / (n0 ^ 2 - n1 ^ 2 - n2 ^ 2)) * h
  · linear_combination (-2 * n2 / (n0 ^ 2 - n1 ^ 2 - n2 ^ 2)) * h

/-- It reverses `n`. -/
theorem householder_flips (n0 n1 n2 : ℚ) (hq : n0 ^ 2 - n1 ^ 2 - n2 ^ 2 ≠ 0) :
    householder n0 n1 n2 *ᵥ ![n0, n1, n2] = -![n0, n1, n2] := by
  ext i
  fin_cases i <;> simp [householder, Matrix.mulVec, dotProduct, Fin.sum_univ_three] <;>
    field_simp <;> ring

/-- The Minkowski cross product of two states, `η (a × b)`: Minkowski-orthogonal
to both (`frame_plane.cross_eta`). -/
def crossEta (a b : Fin 3 → ℚ) : Fin 3 → ℚ :=
  ![a 1 * b 2 - a 2 * b 1, -(a 2 * b 0 - a 0 * b 2), -(a 0 * b 1 - a 1 * b 0)]

/-- **Two demonstrations never fix the component.** For any Lorentz map `M` and
any two inputs whose Minkowski cross product `n` is not null, `M` times the
reflection in their plane is a Lorentz map of the opposite determinant that
sends both inputs where `M` does and differs from `M` on `n`. So whichever
component the true map lies in, a map in another component agrees with it on
both demonstrations: the general form of `reflection_agrees_on_plane`, and
the reason for the span guard. -/
theorem plane_partner {M : Matrix (Fin 3) (Fin 3) ℚ} (hM : IsLorentz M)
    (a b : Fin 3 → ℚ)
    (hq : crossEta a b 0 ^ 2 - crossEta a b 1 ^ 2 - crossEta a b 2 ^ 2 ≠ 0) :
    let R := householder (crossEta a b 0) (crossEta a b 1) (crossEta a b 2)
    IsLorentz (M * R) ∧ (M * R).det = -M.det ∧ (M * R) *ᵥ a = M *ᵥ a ∧
      (M * R) *ᵥ b = M *ᵥ b ∧ (M * R) *ᵥ crossEta a b ≠ M *ᵥ crossEta a b := by
  intro R
  have hR := householder_lorentz _ _ _ hq
  have hRd := householder_det _ _ _ hq
  have hn : crossEta a b = ![crossEta a b 0, crossEta a b 1, crossEta a b 2] := by
    ext i; fin_cases i <;> rfl
  refine ⟨lorentz_mul hM hR, ?_, ?_, ?_, ?_⟩
  · rw [Matrix.det_mul, hRd]; ring
  · rw [← Matrix.mulVec_mulVec, householder_fixes]
    simp [crossEta]; ring
  · rw [← Matrix.mulVec_mulVec, householder_fixes]
    simp [crossEta]; ring
  · rw [← Matrix.mulVec_mulVec]
    intro h
    have hflip : R *ᵥ crossEta a b = -crossEta a b := by
      rw [hn]; exact householder_flips _ _ _ hq
    rw [hflip, Matrix.mulVec_neg] at h
    have h0 : M *ᵥ crossEta a b = 0 := by
      have : (2 : ℚ) • (M *ᵥ crossEta a b) = 0 := by
        rw [two_smul]; nth_rewrite 1 [← h]; simp
      exact (smul_eq_zero.mp this).resolve_left (by norm_num)
    have hdet : M.det ≠ 0 := by
      intro hd; have := lorentz_det_sq hM; rw [hd] at this; norm_num at this
    have hz := Matrix.eq_zero_of_mulVec_eq_zero hdet h0
    apply hq
    have h0' := congrFun hz 0
    have h1' := congrFun hz 1
    have h2' := congrFun hz 2
    simp only [Pi.zero_apply] at h0' h1' h2'
    rw [h0', h1', h2']; ring

/-- Two Lorentz maps — the identity, proper, and `parity`, improper — agree on
the rank-2 inputs `(1,0,0)` and `(2,1,0)` and disagree on `(2,0,1)`: rank-2
demonstrations cannot tell a proper map from its reflection off their plane. -/
theorem reflection_agrees_on_plane :
    IsLorentz (1 : Matrix (Fin 3) (Fin 3) ℚ) ∧ IsLorentz parity ∧
    parity *ᵥ ![1, 0, 0] = (1 : Matrix (Fin 3) (Fin 3) ℚ) *ᵥ ![1, 0, 0] ∧
    parity *ᵥ ![2, 1, 0] = (1 : Matrix (Fin 3) (Fin 3) ℚ) *ᵥ ![2, 1, 0] ∧
    parity *ᵥ ![2, 0, 1] ≠ (1 : Matrix (Fin 3) (Fin 3) ℚ) *ᵥ ![2, 0, 1] := by
  refine ⟨by simp [IsLorentz], parity_lorentz, ?_, ?_, ?_⟩
  · rw [Matrix.one_mulVec]
    ext i; fin_cases i <;> simp [parity, Matrix.mulVec, dotProduct, Fin.sum_univ_three]
  · rw [Matrix.one_mulVec]
    ext i; fin_cases i <;> simp [parity, Matrix.mulVec, dotProduct, Fin.sum_univ_three]
  · rw [Matrix.one_mulVec]
    intro h
    have := congrFun h 2
    simp [parity, Matrix.mulVec, dotProduct, Fin.sum_univ_three] at this
    norm_num at this

end GLM.LorentzImproper
