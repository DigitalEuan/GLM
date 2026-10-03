module

public import Mathlib

/-!
# Typed operators: three powers of one dimension, and dot against cross

The formal half of `studies/TYPED_OPERATORS_STUDY.md` (Phase 90,
`glm_universal.runtime.typed_operators`). With RMS phasors `V` and `I`, the
complex power is `S = V * conj I`; the real power is `S.re`, the reactive
power `S.im`, the apparent power `‖S‖`. The torque is the cross product of a
position with a force, the work the dot product of a force with a
displacement.

* `complex_power_normSq` — `|S|² = |V|² |I|²`: the apparent power is the
  product of the magnitudes, which is all a monomial wheel can compute.
* `power_triangle` — `P² + Q² = |V|² |I|²` (the census of mark T7).
* `real_power_le_apparent`, `reactive_power_le_apparent`,
  `power_factor_mem` — `|P| ≤ |S|`, `|Q| ≤ |S|` and the power factor lies in
  `[-1, 1]`, which is why a larger side is refused
  `POWER_TRIANGLE_VIOLATED` and a power factor outside `[-1, 1]`
  `POWER_FACTOR_OUT_OF_RANGE`.
* `complex_power_impedance`, `complex_power_admittance` — `S = |I|² Z`
  when `V = Z I`, and `S = |V|² / conj Z` when `I = V / Z`.
* `reactive_sign_undetermined` — two sides of the power triangle fix the
  reactive power only up to sign: `PF_SENSE_UNDECLARED`.
* `naive_real_power_wrong` — the monomial answer `|V| |I|` for the real power
  is wrong whenever the reactive power is not zero (the naive control).
* `lagrange_identity`, `cross_orthogonal_left`, `cross_orthogonal_right`,
  `cross_anticomm'` — the cross product's identities the column-3 scripts
  check, and `naive_torque_wrong`: `|r| |F|` is the torque's magnitude only
  when `r · F = 0`.
-/

@[expose] public section

namespace GLM.TypedOperators

open Complex ComplexConjugate

/-- The complex power of two phasors. -/
noncomputable def complexPower (V I : ℂ) : ℂ := V * conj I

/-- **The apparent power is the product of the magnitudes.** -/
theorem complex_power_normSq (V I : ℂ) :
    normSq (complexPower V I) = normSq V * normSq I := by
  simp [complexPower, map_mul, normSq_conj]

/-- **The power triangle**: `P² + Q² = |V|² |I|²`. -/
theorem power_triangle (V I : ℂ) :
    (complexPower V I).re ^ 2 + (complexPower V I).im ^ 2
      = normSq V * normSq I := by
  rw [← complex_power_normSq, normSq_apply]
  ring

/-- **The real power never exceeds the apparent power.** -/
theorem real_power_le_apparent (S : ℂ) : |S.re| ≤ ‖S‖ :=
  abs_re_le_norm S

/-- **The reactive power never exceeds the apparent power.** -/
theorem reactive_power_le_apparent (S : ℂ) : |S.im| ≤ ‖S‖ :=
  abs_im_le_norm S

/-- **A power factor lies in `[-1, 1]`.** -/
theorem power_factor_mem (S : ℂ) (h : S ≠ 0) :
    -1 ≤ S.re / ‖S‖ ∧ S.re / ‖S‖ ≤ 1 := by
  have hpos : 0 < ‖S‖ := norm_pos_iff.mpr h
  have hle := abs_re_le_norm S
  constructor
  · rw [le_div_iff₀ hpos]
    linarith [neg_abs_le S.re]
  · rw [div_le_iff₀ hpos]
    linarith [le_abs_self S.re]

/-- **Through an impedance, `S = |I|² Z`.** -/
theorem complex_power_impedance (Z I : ℂ) :
    complexPower (Z * I) I = (normSq I : ℂ) * Z := by
  rw [complexPower, mul_assoc, mul_conj]
  ring

/-- **Across an impedance, `S = |V|² / conj Z`.** -/
theorem complex_power_admittance (V Z : ℂ) (hZ : Z ≠ 0) :
    complexPower V (V / Z) = (normSq V : ℂ) / conj Z := by
  have hc : conj Z ≠ 0 := (map_ne_zero _).mpr hZ
  rw [complexPower, map_div₀, ← mul_conj]
  field_simp

/-- **Two sides fix the reactive power only up to sign.** Given the real
power `P` and the apparent power `S` with `P² < S²`, both `q` and `-q` solve
the triangle and they differ. -/
theorem reactive_sign_undetermined (P S q : ℝ) (hq : P ^ 2 + q ^ 2 = S ^ 2)
    (hlt : P ^ 2 < S ^ 2) :
    P ^ 2 + (-q) ^ 2 = S ^ 2 ∧ q ≠ -q := by
  refine ⟨by rw [neg_sq]; exact hq, ?_⟩
  intro h
  have : q = 0 := by linarith
  subst this
  linarith

/-- **The monomial answer for the real power is wrong whenever `Q ≠ 0`.** -/
theorem naive_real_power_wrong (V I : ℂ) (hQ : (complexPower V I).im ≠ 0) :
    ‖V‖ * ‖I‖ ≠ (complexPower V I).re := by
  intro h
  have hn : ‖complexPower V I‖ = ‖V‖ * ‖I‖ := by
    simp [complexPower]
  have h2 : ‖complexPower V I‖ ^ 2 = (complexPower V I).re ^ 2 +
      (complexPower V I).im ^ 2 := by
    rw [← normSq_eq_norm_sq, normSq_apply]; ring
  rw [hn, h] at h2
  have : (complexPower V I).im ^ 2 = 0 := by linarith
  exact hQ (pow_eq_zero_iff (n := 2) (by norm_num) |>.mp this)

/-- The cross product of two triples. -/
def cross3 (a b : ℚ × ℚ × ℚ) : ℚ × ℚ × ℚ :=
  (a.2.1 * b.2.2 - a.2.2 * b.2.1, a.2.2 * b.1 - a.1 * b.2.2,
   a.1 * b.2.1 - a.2.1 * b.1)

/-- The dot product of two triples. -/
def dot3 (a b : ℚ × ℚ × ℚ) : ℚ := a.1 * b.1 + a.2.1 * b.2.1 + a.2.2 * b.2.2

/-- **Lagrange's identity**: `|a × b|² + (a · b)² = |a|² |b|²`. -/
theorem lagrange_identity (a b : ℚ × ℚ × ℚ) :
    dot3 (cross3 a b) (cross3 a b) + dot3 a b ^ 2 = dot3 a a * dot3 b b := by
  simp only [dot3, cross3]
  ring

/-- **The torque is perpendicular to the lever arm.** -/
theorem cross_orthogonal_left (a b : ℚ × ℚ × ℚ) : dot3 a (cross3 a b) = 0 := by
  simp only [dot3, cross3]
  ring

/-- **The torque is perpendicular to the force.** -/
theorem cross_orthogonal_right (a b : ℚ × ℚ × ℚ) :
    dot3 b (cross3 a b) = 0 := by
  simp only [dot3, cross3]
  ring

/-- **The cross product is anticommutative** (the dot product commutes:
`dot3_comm`), so the two are different operators. -/
theorem cross_anticomm' (a b : ℚ × ℚ × ℚ) :
    cross3 b a = (-(cross3 a b).1, -(cross3 a b).2.1, -(cross3 a b).2.2) := by
  simp only [cross3]
  ext <;> simp <;> ring

theorem dot3_comm (a b : ℚ × ℚ × ℚ) : dot3 a b = dot3 b a := by
  simp only [dot3]
  ring

/-- **The monomial torque `|r| |F|` is right only for perpendicular
vectors**: its square equals `|r × F|²` exactly when `r · F = 0`. -/
theorem naive_torque_wrong (r F : ℚ × ℚ × ℚ) :
    dot3 (cross3 r F) (cross3 r F) = dot3 r r * dot3 F F ↔ dot3 r F = 0 := by
  have h := lagrange_identity r F
  constructor
  · intro e
    have : dot3 r F ^ 2 = 0 := by linarith
    exact pow_eq_zero_iff (n := 2) (by norm_num) |>.mp this
  · intro e
    rw [e] at h
    linarith

/-- The corpus's first case: `V = 120`, `I = 3 - 4j` give `S = 360 + 480j`. -/
theorem case_a01 : complexPower 120 (3 - 4 * I) = 360 + 480 * I := by
  simp only [complexPower, map_sub, map_mul, conj_I, map_ofNat]
  ring

end GLM.TypedOperators
