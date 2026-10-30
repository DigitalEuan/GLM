module

public import Mathlib

/-!
# Round 17: spinning the triangle and the pyramid through space-time

Question (user, Round 17): *can the 2D triangle (or the 3D pyramid) be rotated through the space,
anchored at its apex/centroid, so that it "collects" the points it passes through as it spins?*

Coordinates: time `t : ℝ` and a two-dimensional space written as the complex plane `ℂ`, so a
space-time point is `(t, z) : ℝ × ℂ`.  A rotation of space by the angle `θ` about the time axis
is **multiplication by the unit complex number `e^{iθ}`** — the rotation literally is a
multiplication factor.  `spin θ S` is the set `S` turned by `θ`.

* `tri` is Rule 30's light-cone triangle `|s| ≤ t`, placed in the plane `Im z = 0`.
* `pyr` is the light cone of a 2D rule with the 3×3 (Moore) neighbourhood, the square pyramid
  `max(|Re z|, |Im z|) ≤ t` (`ConeGeometry.mooreCone`).
* `roundCone k` is the round cone `‖z‖ ≤ k·t`.

## Results (all exact)

1. **The spinning triangle collects exactly the round 90° cone** (`spin_sweep_triangle`).  Each
   point off the axis is collected at exactly two moments of every turn: when the plane's angle
   satisfies `sin (arg z − θ) = 0`, i.e. `θ = arg z` (front half of the triangle) or
   `θ = arg z + π` (back half) (`mem_spin_tri_iff`).
2. **The spinning pyramid sweeps the round cone of apex angle `2·arctan √2 ≈ 109.47°`**
   (`spin_sweep_pyramid`) **and always contains the round 90° cone** (`spin_core_pyramid`).  These
   are exactly the extreme vertical-slice angles found in Round 16 (`ConeGeometry`): spinning
   turns the square pyramid's angle range into a pair of nested round cones.  Points between
   the two cones are collected only for part of each turn (`mem_spin_pyr_iff`).
3. **Spinning as time advances (the helical/screw sweep).**  Let the plane turn by `ω` per time
   step.  If `ω/π` is irrational the plane never comes back to a previous position
   (`helical_planes_distinct`) and its positions are dense among all planes
   (`helical_planes_dense`); if `ω/π = p/q` is rational it repeats with period `q`
   (`helical_planes_periodic`).  So the spin rate `ω` acts as a multiplication factor whose
   arithmetic (rational or irrational) decides whether the sweep closes up or fills the circle.
-/

@[expose] public section

namespace GLM.Spin

open Complex Set Real

/-- The rotation of space by `θ`: multiplication by `e^{iθ}`. -/
noncomputable def rot (θ : ℝ) : ℂ := exp (θ * I)

theorem norm_rot (θ : ℝ) : ‖rot θ‖ = 1 := norm_exp_ofReal_mul_I θ

theorem rot_add (a b : ℝ) : rot (a + b) = rot a * rot b := by
  simp [rot, ← Complex.exp_add, add_mul]

theorem rot_neg_mul_rot (θ : ℝ) : rot (-θ) * rot θ = 1 := by
  rw [← rot_add, neg_add_cancel]; simp [rot]

/-- `e^{iφ}` in coordinates. -/
theorem rot_re_im (φ : ℝ) : (rot φ).re = Real.cos φ ∧ (rot φ).im = Real.sin φ := by
  constructor
  · simp [rot, Complex.exp_ofReal_mul_I_re]
  · simp [rot, Complex.exp_ofReal_mul_I_im]

/-- A set of space-time points turned by `θ` about the time axis: `p` lies in the turned set iff
turning `p` back by `θ` lands in `S`. -/
def spin (θ : ℝ) (S : Set (ℝ × ℂ)) : Set (ℝ × ℂ) := {p | (p.1, rot (-θ) * p.2) ∈ S}

/-- Rule 30's light-cone triangle, in the plane `Im z = 0`. -/
def tri : Set (ℝ × ℂ) := {p | p.2.im = 0 ∧ |p.2.re| ≤ p.1}

/-- The square light-cone pyramid of a 2D rule with the Moore neighbourhood. -/
def pyr : Set (ℝ × ℂ) := {p | max |p.2.re| |p.2.im| ≤ p.1}

/-- The round cone `‖z‖ ≤ k·t`. -/
def roundCone (k : ℝ) : Set (ℝ × ℂ) := {p | ‖p.2‖ ≤ k * p.1}

/-- Polar form of the point turned back by `θ`: `e^{-iθ} z = ‖z‖·e^{i(arg z − θ)}`. -/
theorem rot_neg_mul_polar (θ : ℝ) (z : ℂ) :
    rot (-θ) * z = (‖z‖ : ℂ) * rot (arg z - θ) := by
  conv_lhs => rw [← norm_mul_exp_arg_mul_I z]
  rw [sub_eq_add_neg, rot_add]
  simp only [rot]; ring

theorem rot_neg_mul_re_im (θ : ℝ) (z : ℂ) :
    (rot (-θ) * z).re = ‖z‖ * Real.cos (arg z - θ) ∧
      (rot (-θ) * z).im = ‖z‖ * Real.sin (arg z - θ) := by
  rw [rot_neg_mul_polar]
  obtain ⟨h1, h2⟩ := rot_re_im (arg z - θ)
  constructor
  · simp [Complex.mul_re, h1]
  · simp [Complex.mul_im, h2]

/-! ## 1. The spinning triangle -/

/-- **When is a point collected by the triangle turned by `θ`?**  Exactly when it is inside the
round cone and the plane's angle `θ` is `arg z` or `arg z + π` (mod `2π`), i.e.
`sin (arg z − θ) = 0`. -/
theorem mem_spin_tri_iff (θ t : ℝ) (z : ℂ) :
    (t, z) ∈ spin θ tri ↔ Real.sin (arg z - θ) * ‖z‖ = 0 ∧ ‖z‖ ≤ t := by
  obtain ⟨hre, him⟩ := rot_neg_mul_re_im θ z
  simp only [spin, tri, mem_setOf_eq, hre, him]
  constructor
  · rintro ⟨h0, h1⟩
    refine ⟨by linarith, ?_⟩
    rcases mul_eq_zero.mp h0 with h | h
    · rw [h] at h1; simpa [h] using h1
    · have hc := Real.sin_sq_add_cos_sq (arg z - θ)
      rw [h, zero_pow two_ne_zero, zero_add] at hc
      have : |Real.cos (arg z - θ)| = 1 := by
        rw [← abs_one, ← sq_eq_sq_iff_abs_eq_abs] at *; simpa using hc
      rw [abs_mul, this, abs_norm, mul_one] at h1; exact h1
  · rintro ⟨h0, h1⟩
    refine ⟨by linarith, ?_⟩
    rw [abs_mul, abs_norm]
    calc ‖z‖ * |Real.cos (arg z - θ)| ≤ ‖z‖ * 1 :=
          mul_le_mul_of_nonneg_left (Real.abs_cos_le_one _) (norm_nonneg _)
      _ ≤ t := by linarith

/-- **The spinning triangle collects exactly the round cone `‖z‖ ≤ t`** (apex angle `90°`). -/
theorem spin_sweep_triangle : (⋃ θ : ℝ, spin θ tri) = roundCone 1 := by
  ext ⟨t, z⟩
  simp only [mem_iUnion, roundCone, mem_setOf_eq, one_mul]
  constructor
  · rintro ⟨θ, h⟩; exact ((mem_spin_tri_iff θ t z).mp h).2
  · intro h
    exact ⟨arg z, (mem_spin_tri_iff _ t z).mpr ⟨by simp, h⟩⟩

/-- Each point off the axis is collected by both halves of the triangle: at `θ = arg z` and at
`θ = arg z + π`. -/
theorem spin_tri_two_moments (t : ℝ) (z : ℂ) (hz : ‖z‖ ≤ t) :
    (t, z) ∈ spin (arg z) tri ∧ (t, z) ∈ spin (arg z + π) tri := by
  refine ⟨(mem_spin_tri_iff _ t z).mpr ⟨by simp, hz⟩,
    (mem_spin_tri_iff _ t z).mpr ⟨?_, hz⟩⟩
  rw [show arg z - (arg z + π) = -π by ring, Real.sin_neg, Real.sin_pi]; simp

/-- …and at no other moment: for `z ≠ 0` inside the cone, the angles at which it is collected are
exactly the angles with `sin (arg z − θ) = 0`, i.e. `θ ∈ arg z + πℤ`. -/
theorem spin_tri_moments (θ t : ℝ) (z : ℂ) (hz0 : z ≠ 0) :
    (t, z) ∈ spin θ tri ↔ (∃ n : ℤ, θ = arg z + n * π) ∧ ‖z‖ ≤ t := by
  rw [mem_spin_tri_iff, mul_eq_zero, or_iff_left (norm_ne_zero_iff.mpr hz0),
    Real.sin_eq_zero_iff]
  constructor
  · rintro ⟨⟨n, hn⟩, h⟩; exact ⟨⟨-n, by push_cast; linarith⟩, h⟩
  · rintro ⟨⟨n, hn⟩, h⟩; exact ⟨⟨-n, by push_cast; linarith⟩, h⟩

/-! ## 2. The spinning pyramid -/

/-- **When is a point inside the pyramid turned by `θ`?** -/
theorem mem_spin_pyr_iff (θ t : ℝ) (z : ℂ) :
    (t, z) ∈ spin θ pyr ↔
      ‖z‖ * |Real.cos (arg z - θ)| ≤ t ∧ ‖z‖ * |Real.sin (arg z - θ)| ≤ t := by
  obtain ⟨hre, him⟩ := rot_neg_mul_re_im θ z
  simp only [spin, pyr, mem_setOf_eq, hre, him, abs_mul, abs_norm, max_le_iff]

theorem norm_le_sqrt_two_mul_max (w : ℂ) : ‖w‖ ≤ Real.sqrt 2 * max |w.re| |w.im| := by
  set m := max |w.re| |w.im|
  have hm : 0 ≤ m := le_max_of_le_left (abs_nonneg _)
  have h1 : w.re ^ 2 ≤ m ^ 2 := by
    rw [← sq_abs]; exact pow_le_pow_left₀ (abs_nonneg _) (le_max_left _ _) 2
  have h2 : w.im ^ 2 ≤ m ^ 2 := by
    rw [← sq_abs]; exact pow_le_pow_left₀ (abs_nonneg _) (le_max_right _ _) 2
  rw [← Real.sqrt_sq hm, ← Real.sqrt_mul (by norm_num), Complex.norm_eq_sqrt_sq_add_sq]
  exact Real.sqrt_le_sqrt (by nlinarith)

theorem max_le_norm (w : ℂ) : max |w.re| |w.im| ≤ ‖w‖ :=
  max_le (Complex.abs_re_le_norm w) (Complex.abs_im_le_norm w)

/-- **The spinning pyramid sweeps the round cone `‖z‖ ≤ √2·t`**, of apex angle
`2·arctan √2 ≈ 109.47°` (the diagonal-slice angle of Round 16). -/
theorem spin_sweep_pyramid : (⋃ θ : ℝ, spin θ pyr) = roundCone (Real.sqrt 2) := by
  ext ⟨t, z⟩
  simp only [mem_iUnion, roundCone, mem_setOf_eq]
  constructor
  · rintro ⟨θ, h⟩
    simp only [spin, pyr, mem_setOf_eq] at h
    have := norm_le_sqrt_two_mul_max (rot (-θ) * z)
    rw [norm_mul, norm_rot, one_mul] at this
    calc ‖z‖ ≤ _ := this
      _ ≤ Real.sqrt 2 * t := mul_le_mul_of_nonneg_left h (Real.sqrt_nonneg 2)
  · intro h
    refine ⟨arg z - π / 4, (mem_spin_pyr_iff _ t z).mpr ?_⟩
    rw [show arg z - (arg z - π / 4) = π / 4 by ring, Real.cos_pi_div_four,
      Real.sin_pi_div_four, abs_of_pos (by positivity), and_self]
    have hs : Real.sqrt 2 * Real.sqrt 2 = 2 := Real.mul_self_sqrt (by norm_num)
    have hs0 : 0 < Real.sqrt 2 := by positivity
    nlinarith [norm_nonneg z]

/-- **The spinning pyramid always contains the round cone `‖z‖ ≤ t`** (apex angle `90°`), and
nothing more is inside it at every moment of the turn. -/
theorem spin_core_pyramid : (⋂ θ : ℝ, spin θ pyr) = roundCone 1 := by
  ext ⟨t, z⟩
  simp only [mem_iInter, roundCone, mem_setOf_eq, one_mul]
  constructor
  · intro h
    have := (mem_spin_pyr_iff _ t z).mp (h (arg z))
    simpa using this.1
  · intro h θ
    simp only [spin, pyr, mem_setOf_eq]
    calc _ ≤ ‖rot (-θ) * z‖ := max_le_norm _
      _ = ‖z‖ := by rw [norm_mul, norm_rot, one_mul]
      _ ≤ t := h

/-- The pyramid's two sweep cones have apex angles `90°` and `2·arctan √2`, the latter with
cosine `−1/3`. -/
theorem sweep_cone_angles :
    2 * Real.arctan 1 = π / 2 ∧ Real.cos (2 * Real.arctan (Real.sqrt 2)) = -1 / 3 := by
  refine ⟨by rw [Real.arctan_one]; ring, ?_⟩
  rw [Real.cos_two_mul, Real.cos_arctan, div_pow, one_pow, Real.sq_sqrt (by positivity),
    Real.sq_sqrt (by norm_num)]
  norm_num

/-! ## 3. The helical sweep: spin rate as a multiplication factor -/

/-- The plane at angle `θ` (through the time axis) is the same plane as at angle `θ'` iff
`θ − θ' ∈ πℤ`. We say the planes coincide when `sin (θ − θ') = 0`. -/
def SamePlane (θ θ' : ℝ) : Prop := Real.sin (θ - θ') = 0

/-- **Irrational spin never repeats a plane.**  If the triangle turns by `ω` per time step and
`ω/π` is irrational, its planes at different times are all different. -/
theorem helical_planes_distinct (ω : ℝ) (hω : Irrational (ω / π)) {t₁ t₂ : ℤ}
    (h : SamePlane (ω * t₁) (ω * t₂)) : t₁ = t₂ := by
  by_contra hne
  obtain ⟨n, hn⟩ := Real.sin_eq_zero_iff.mp h
  have hd : ((t₁ - t₂ : ℤ) : ℝ) ≠ 0 := by exact_mod_cast sub_ne_zero.mpr hne
  apply hω
  refine ⟨(n : ℚ) / (t₁ - t₂ : ℤ), ?_⟩
  push_cast at hd ⊢
  field_simp
  linarith

/-- **Rational spin repeats with period `q`.**  If `ω = π·p/q` the plane at time `t + q` is the
plane at time `t`. -/
theorem helical_planes_periodic (p : ℤ) (q : ℕ) (hq : q ≠ 0) (t : ℤ) :
    SamePlane (π * p / q * (t + q)) (π * p / q * t) := by
  unfold SamePlane
  rw [show π * p / q * (t + q) - π * p / q * t = p * π by field_simp; ring]
  exact Real.sin_int_mul_pi p

/-- **Irrational spin fills the circle of planes.**  If `ω/π` is irrational, the angles `ω·t`
(`t ∈ ℤ`) taken modulo `π` (i.e. the planes visited) are dense. -/
theorem helical_planes_dense (ω : ℝ) (hω : Irrational (ω / π)) :
    DenseRange (fun t : ℤ => t • (ω : AddCircle π)) :=
  AddCircle.denseRange_zsmul_coe_iff.mpr hω

end GLM.Spin
