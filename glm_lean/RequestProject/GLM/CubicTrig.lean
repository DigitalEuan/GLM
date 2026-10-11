module

public import Mathlib

/-!
# A cubic with three real roots: what the Phase 108 readings rest on

`studies/CUBIC_TRIG_STUDY.md` (Phase 108) answers a cubic in letters whose
discriminant is negative -- the *casus irreducibilis*, which Phase 104
refused because no real radical form exists -- through the branch layer of
`solve symbolically` (`overlay/glm_universal/reasoning/symbolic_nonlinear.py`).
This file proves the facts its readings rest on.

## 1.  The trigonometric (Viète) root

`vieta_root`: with `p < 0` and `cos φ = (3q/(2p)) √(-3/p)`, every value
`2 √(-p/3) cos(φ/3 - 2πk/3)` is a root of `t³ + p t + q = 0`.

`vieta_arg_le_one` / `vieta_arg_lt_one`: `K = (3q/(2p)) √(-3/p)` lies in
`[-1, 1]` when `4p³ + 27q² ≤ 0` (in `(-1, 1)` when the inequality is
strict), so `φ = arccos K` exists with `cos φ = K`; `vieta_arg_sq` is the
identity `K² = 27q²/(-4p³)` behind both.

## 2.  Three distinct roots, and no others

`vieta_cos_strictly_ordered`: for `0 < φ < π` the three cosines
`cos(φ/3)`, `cos(φ/3 - 2π/3)`, `cos(φ/3 - 4π/3)` are strictly decreasing --
the order `k = 0, 1, 2` the layer states ("largest, middle, smallest").

`cubic_three_roots_complete`: three distinct roots of `t³ + p t + q` are all
of its roots.

`vieta_roots_iff`: assembled -- when `p < 0` and `4p³ + 27q² < 0`, a real
`x` is a root exactly when it is one of the three trigonometric values.

## 3.  The homogeneous route

`scaled_root`: if `μ` is a root of `μ³ + c₂μ² + c₁μ + c₀`, then `s μ` is a
root of `u³ + c₂ s u² + c₁ s² u + c₀ s³`; `scaled_root_iff` gives the
converse for `s ≠ 0`, so the layer's `u = s · root(f, lo, hi)` loses no root
and adds none.
-/

@[expose] public section

namespace GLM.CubicTrig

open Real

/-! ## 1.  The trigonometric root -/

/-- Viète's trigonometric root of the depressed cubic `t³ + p t + q`. -/
theorem vieta_root {p q φ : ℝ} (hp : p < 0)
    (hφ : cos φ = 3 * q / (2 * p) * √(-3 / p)) (k : ℤ) :
    (2 * √(-p / 3) * cos (φ / 3 - 2 * π * k / 3)) ^ 3 +
      p * (2 * √(-p / 3) * cos (φ / 3 - 2 * π * k / 3)) + q = 0 := by
  set r := √(-p / 3) with hr
  set c := cos (φ / 3 - 2 * π * k / 3) with hc
  have hp3 : 0 < -p / 3 := by linarith
  have hr2 : r ^ 2 = -p / 3 := Real.sq_sqrt hp3.le
  have hrpos : 0 < r := Real.sqrt_pos.mpr hp3
  have hrne : r ≠ 0 := hrpos.ne'
  have hp' : p = -3 * r ^ 2 := by linarith
  have hs : √(-3 / p) = 1 / r := by
    rw [show -3 / p = (1 / r) ^ 2 by rw [hp']; field_simp]
    exact Real.sqrt_sq (by positivity)
  have h3 : 4 * c ^ 3 - 3 * c = cos φ := by
    have := cos_three_mul (φ / 3 - 2 * π * k / 3)
    rw [← hc] at this
    rw [← this]
    have : 3 * (φ / 3 - 2 * π * k / 3) = φ - (k : ℝ) * (2 * π) := by ring
    rw [this, cos_sub_int_mul_two_pi]
  rw [hφ, hs] at h3
  rw [hp'] at h3 ⊢
  field_simp at h3
  nlinarith [h3]

/-- `K² = 27q²/(-4p³)` for `K = (3q/(2p)) √(-3/p)`. -/
lemma vieta_arg_sq {p q : ℝ} (hp : p < 0) :
    (3 * q / (2 * p) * √(-3 / p)) ^ 2 = 27 * q ^ 2 / (-4 * p ^ 3) := by
  rw [mul_pow, Real.sq_sqrt (div_pos_of_neg_of_neg (by norm_num) hp).le]
  have : p ≠ 0 := hp.ne
  field_simp
  ring

/-- `|K| ≤ 1` when `4p³ + 27q² ≤ 0`: the arccosine is defined. -/
theorem vieta_arg_le_one {p q : ℝ} (hp : p < 0) (hD : 4 * p ^ 3 + 27 * q ^ 2 ≤ 0) :
    |3 * q / (2 * p) * √(-3 / p)| ≤ 1 := by
  have hp3 : p ^ 3 < 0 := Odd.pow_neg (by decide) hp
  rw [← sq_le_one_iff_abs_le_one, vieta_arg_sq hp, div_le_one (by linarith)]
  linarith

/-- `|K| < 1` when `4p³ + 27q² < 0`. -/
theorem vieta_arg_lt_one {p q : ℝ} (hp : p < 0) (hD : 4 * p ^ 3 + 27 * q ^ 2 < 0) :
    |3 * q / (2 * p) * √(-3 / p)| < 1 := by
  have hp3 : p ^ 3 < 0 := Odd.pow_neg (by decide) hp
  rw [← sq_lt_one_iff_abs_lt_one, vieta_arg_sq hp, div_lt_one (by linarith)]
  linarith

/-! ## 2.  Three distinct roots, and no others -/

/-- For `0 < φ < π` the three cosines are strictly decreasing in `k`. -/
theorem vieta_cos_strictly_ordered {φ : ℝ} (h0 : 0 < φ) (hπ : φ < π) :
    cos (φ / 3 - 4 * π / 3) < cos (φ / 3 - 2 * π / 3) ∧
      cos (φ / 3 - 2 * π / 3) < cos (φ / 3) := by
  have e1 : cos (φ / 3 - 2 * π / 3) = cos (2 * π / 3 - φ / 3) := by
    rw [← cos_neg]; ring_nf
  have e2 : cos (φ / 3 - 4 * π / 3) = cos (2 * π / 3 + φ / 3) := by
    rw [show φ / 3 - 4 * π / 3 = (2 * π / 3 + φ / 3) - (1 : ℤ) * (2 * π) by push_cast; ring,
      cos_sub_int_mul_two_pi]
  have hpi := pi_pos
  rw [e1, e2]
  constructor
  · exact cos_lt_cos_of_nonneg_of_le_pi (by linarith) (by linarith) (by linarith)
  · exact cos_lt_cos_of_nonneg_of_le_pi (by linarith) (by linarith) (by linarith)

/-- Three distinct roots of a depressed cubic are all of its roots. -/
theorem cubic_three_roots_complete {p q a b c x : ℝ} (hab : a ≠ b) (hac : a ≠ c)
    (hbc : b ≠ c) (ha : a ^ 3 + p * a + q = 0) (hb : b ^ 3 + p * b + q = 0)
    (hc : c ^ 3 + p * c + q = 0) (hx : x ^ 3 + p * x + q = 0) :
    x = a ∨ x = b ∨ x = c := by
  have e1 : a ^ 2 + a * b + b ^ 2 + p = 0 := by
    have : (a - b) * (a ^ 2 + a * b + b ^ 2 + p) = 0 := by linear_combination ha - hb
    exact (mul_eq_zero.mp this).resolve_left (sub_ne_zero.mpr hab)
  have e2 : a ^ 2 + a * c + c ^ 2 + p = 0 := by
    have : (a - c) * (a ^ 2 + a * c + c ^ 2 + p) = 0 := by linear_combination ha - hc
    exact (mul_eq_zero.mp this).resolve_left (sub_ne_zero.mpr hac)
  have hs : a + b + c = 0 := by
    have : (b - c) * (a + b + c) = 0 := by linear_combination e1 - e2
    exact (mul_eq_zero.mp this).resolve_left (sub_ne_zero.mpr hbc)
  by_cases hxa : x = a
  · exact Or.inl hxa
  right
  have e3 : x ^ 2 + x * a + a ^ 2 + p = 0 := by
    have : (x - a) * (x ^ 2 + x * a + a ^ 2 + p) = 0 := by linear_combination hx - ha
    exact (mul_eq_zero.mp this).resolve_left (sub_ne_zero.mpr hxa)
  have : (x - b) * (x - c) = 0 := by
    have hc' : c = -a - b := by linarith
    subst hc'
    linear_combination e3 - e1
  rcases mul_eq_zero.mp this with h | h
  · exact Or.inl (by linarith)
  · exact Or.inr (by linarith)

/-- The three trigonometric values, `k = 0, 1, 2`. -/
noncomputable def vietaValue (p q : ℝ) (k : ℤ) : ℝ :=
  2 * √(-p / 3) * cos (arccos (3 * q / (2 * p) * √(-3 / p)) / 3 - 2 * π * k / 3)

/-- Assembled: when `p < 0` and `4p³ + 27q² < 0`, the real roots of
`t³ + p t + q` are exactly the three trigonometric values, and they are
strictly decreasing in `k`. -/
theorem vieta_roots_iff {p q : ℝ} (hp : p < 0) (hD : 4 * p ^ 3 + 27 * q ^ 2 < 0) :
    (vietaValue p q 2 < vietaValue p q 1 ∧ vietaValue p q 1 < vietaValue p q 0) ∧
      ∀ x : ℝ, x ^ 3 + p * x + q = 0 ↔
        x = vietaValue p q 0 ∨ x = vietaValue p q 1 ∨ x = vietaValue p q 2 := by
  set K := 3 * q / (2 * p) * √(-3 / p) with hK
  have hK1 := vieta_arg_lt_one hp hD
  rw [← hK] at hK1
  have hKlo : -1 < K := by linarith [neg_abs_le K]
  have hKhi : K < 1 := lt_of_le_of_lt (le_abs_self K) hK1
  set φ := arccos K with hφ
  have hcos : cos φ = K := cos_arccos hKlo.le hKhi.le
  have h0 : 0 < φ := arccos_pos.mpr hKhi
  have hπ : φ < π := arccos_lt_pi.mpr hKlo
  have hroot : ∀ k : ℤ, (vietaValue p q k) ^ 3 + p * vietaValue p q k + q = 0 :=
    fun k => vieta_root hp (by rw [hcos]) k
  have hr : 0 < 2 * √(-p / 3) := by
    have : 0 < -p / 3 := by linarith
    positivity
  obtain ⟨o1, o2⟩ := vieta_cos_strictly_ordered h0 hπ
  have v0 : vietaValue p q 0 = 2 * √(-p / 3) * cos (φ / 3) := by
    simp [vietaValue, hφ, hK]
  have v1 : vietaValue p q 1 = 2 * √(-p / 3) * cos (φ / 3 - 2 * π / 3) := by
    simp [vietaValue, hφ, hK]
  have v2 : vietaValue p q 2 = 2 * √(-p / 3) * cos (φ / 3 - 4 * π / 3) := by
    simp only [vietaValue, ← hK, ← hφ]; push_cast; ring_nf
  have l21 : vietaValue p q 2 < vietaValue p q 1 := by
    rw [v1, v2]; exact mul_lt_mul_of_pos_left o1 hr
  have l10 : vietaValue p q 1 < vietaValue p q 0 := by
    rw [v0, v1]; exact mul_lt_mul_of_pos_left o2 hr
  refine ⟨⟨l21, l10⟩, fun x => ⟨fun hx => ?_, ?_⟩⟩
  · exact cubic_three_roots_complete (ne_of_gt l10) (ne_of_gt (l21.trans l10))
      (ne_of_gt l21) (hroot 0) (hroot 1) (hroot 2) hx
  · rintro (h | h | h) <;> rw [h] <;> exact hroot _

/-! ## 3.  The homogeneous route -/

/-- `s μ` is a root of the scaled cubic when `μ` is a root of the cubic. -/
theorem scaled_root {c₂ c₁ c₀ s μ : ℝ} (h : μ ^ 3 + c₂ * μ ^ 2 + c₁ * μ + c₀ = 0) :
    (s * μ) ^ 3 + c₂ * s * (s * μ) ^ 2 + c₁ * s ^ 2 * (s * μ) + c₀ * s ^ 3 = 0 := by
  linear_combination s ^ 3 * h

/-- For `s ≠ 0`, `u` is a root of the scaled cubic exactly when `u / s` is a
root of the cubic. -/
theorem scaled_root_iff {c₂ c₁ c₀ s u : ℝ} (hs : s ≠ 0) :
    u ^ 3 + c₂ * s * u ^ 2 + c₁ * s ^ 2 * u + c₀ * s ^ 3 = 0 ↔
      (u / s) ^ 3 + c₂ * (u / s) ^ 2 + c₁ * (u / s) + c₀ = 0 := by
  have hs3 : s ^ 3 ≠ 0 := pow_ne_zero 3 hs
  constructor
  · intro h
    have : s ^ 3 * ((u / s) ^ 3 + c₂ * (u / s) ^ 2 + c₁ * (u / s) + c₀) = 0 := by
      field_simp; linear_combination h
    exact (mul_eq_zero.mp this).resolve_left hs3
  · intro h
    have := scaled_root (s := s) h
    rwa [mul_div_cancel₀ u hs] at this

end GLM.CubicTrig
