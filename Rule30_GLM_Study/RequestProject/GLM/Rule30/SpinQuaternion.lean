module

public import RequestProject.GLM.Rule30.SpinSweep

/-!
# Round 17: spin as a multiplication factor — when does the motion become higher-dimensional?

The user's proposal: *the spin or rotation could be a multiplication factor, so the motion is
higher-dimensional than simple 2D/3D motion.*  This file makes that precise.

1. **Spins in one plane only add.**  Turning by `a` and then by `b` in the same plane is the
   multiplication `e^{ia}·e^{ib} = e^{i(a+b)}`; the order does not matter
   (`plane_spins_commute`).  Combining spins in a single plane never leaves that plane.
2. **Spinning in two planes at once (4D double rotation).**  On `ℂ² ≅ ℝ⁴`, turn the first plane at
   rate `α` and the second at rate `β`.
   * `double_rotation_closes_iff`: the motion ever returns to its start iff `α/β` is rational —
     the ratio of the two rates is the multiplication factor that decides it.
   * `double_rotation_section_dense`: if `α/β` is irrational, then at the moments the first spin
     completes a full turn, the second angle is dense on the circle: the motion winds densely
     around the torus and comes arbitrarily close to every pair of angles.
3. **Quaternions: rotation is literally multiplication.**
   * 3D (`conj_comp`, `conj_fixes_axis`): rotating space by `v ↦ q v q⋆` composes by multiplying
     the quaternions, and every such rotation has an axis (the imaginary part of `q`) that it
     fixes; quarter turns about different axes do not commute (`quaternion_spins_noncommute`).
   * 4D (`left_mul_no_fixed_vector`, `norm_left_mul`): multiplying by a unit quaternion `p ≠ 1`
     preserves length and **fixes no nonzero vector** — there is no axis; every direction moves.
   * `left_right_double_rotation`: `v ↦ e^{iα} v e^{iβ}` turns the plane `(1, i)` by `α + β` and
     the plane `(j, k)` by `α − β` at the same time.  Every pair of plane angles `(θ₁, θ₂)` is
     reached with `α = (θ₁+θ₂)/2`, `β = (θ₁−θ₂)/2`.  So "spin × rotation", written as a left and a
     right multiplication factor, is exactly a general 4D double rotation.
-/

@[expose] public section

namespace GLM.Spin

open Complex Real

/-! ## 1. One plane -/

/-- Spins in a single plane commute and their angles add. -/
theorem plane_spins_commute (a b : ℝ) : rot a * rot b = rot b * rot a ∧ rot a * rot b = rot (a + b) :=
  ⟨mul_comm _ _, (rot_add a b).symm⟩

/-- `e^{ix} = 1` iff `x` is a whole number of turns. -/
theorem rot_eq_one_iff (x : ℝ) : rot x = 1 ↔ ∃ n : ℤ, x = 2 * π * n := by
  rw [rot, Complex.exp_eq_one_iff]
  constructor
  · rintro ⟨n, hn⟩
    refine ⟨n, ?_⟩
    have := congrArg Complex.im hn
    simpa [mul_comm, mul_assoc, mul_left_comm] using this
  · rintro ⟨n, rfl⟩
    exact ⟨n, by push_cast; ring⟩

/-! ## 2. Two planes: the 4D double rotation -/

/-- The double rotation of `ℂ² ≅ ℝ⁴` at rates `α`, `β`, after time `φ`. -/
noncomputable def doubleRot (α β φ : ℝ) (v : ℂ × ℂ) : ℂ × ℂ :=
  (rot (α * φ) * v.1, rot (β * φ) * v.2)

/-- **The double rotation closes up iff the rate ratio is rational.**  For a non-zero second rate, there is
a time `φ ≠ 0` returning every point to itself iff `α / β ∈ ℚ`. -/
theorem double_rotation_closes_iff (α β : ℝ) (hβ : β ≠ 0) :
    (∃ φ : ℝ, φ ≠ 0 ∧ ∀ v, doubleRot α β φ v = v) ↔ ∃ q : ℚ, α / β = q := by
  constructor
  · rintro ⟨φ, hφ, h⟩
    have h1 := congrArg Prod.fst (h (1, 1))
    have h2 := congrArg Prod.snd (h (1, 1))
    simp only [doubleRot, mul_one] at h1 h2
    obtain ⟨m, hm⟩ := (rot_eq_one_iff _).mp h1
    obtain ⟨n, hn⟩ := (rot_eq_one_iff _).mp h2
    have hn0 : (n : ℝ) ≠ 0 := by
      intro h0; rw [h0, mul_zero] at hn; exact mul_ne_zero hβ hφ hn
    refine ⟨(m : ℚ) / n, ?_⟩
    push_cast
    field_simp
    have hpi : (2 * π) ≠ 0 := by positivity
    have : α * φ * n = β * φ * m := by rw [hm, hn]; ring
    have := mul_right_cancel₀ hφ (show α * n * φ = β * m * φ by linarith)
    linarith
  · rintro ⟨q, hq⟩
    have hqden : (q.den : ℝ) ≠ 0 := by exact_mod_cast q.den_ne_zero
    refine ⟨2 * π * q.den / β, by positivity, fun v => ?_⟩
    have hα' : α = β * q := by field_simp at hq; linarith
    have hq' : (q : ℝ) = q.num / q.den := by exact_mod_cast (Rat.num_div_den q).symm
    have e1 : rot (α * (2 * π * q.den / β)) = 1 := by
      rw [rot_eq_one_iff]
      refine ⟨q.num, ?_⟩
      rw [hα', hq']; field_simp
    have e2 : rot (β * (2 * π * q.den / β)) = 1 := by
      rw [rot_eq_one_iff]
      exact ⟨q.den, by push_cast; field_simp⟩
    simp [doubleRot, e1, e2]

/-- **Irrational ratio: the motion winds densely.**  At the times `φ = 2πn/α` (`n ∈ ℤ`), when the
first spin has made exactly `n` full turns, the angle of the second spin is
`n · (2πβ/α)` modulo `2π`; if `β/α` is irrational these angles are dense on the circle. -/
theorem double_rotation_section_dense (α β : ℝ) (hα : α ≠ 0) (hirr : Irrational (β / α)) :
    (∀ n : ℤ, rot (α * (2 * π * n / α)) = 1) ∧
      DenseRange (fun n : ℤ => n • ((2 * π * β / α : ℝ) : AddCircle (2 * π))) := by
  refine ⟨fun n => (rot_eq_one_iff _).mpr ⟨n, by field_simp⟩, ?_⟩
  apply AddCircle.denseRange_zsmul_coe_iff.mpr
  have : 2 * π * β / α / (2 * π) = β / α := by field_simp
  rw [this]; exact hirr

/-! ## 3. Quaternions -/

open Quaternion

/-- 3D rotation by a quaternion: `v ↦ q v q⋆`. -/
def conjRot (q v : ℍ[ℝ]) : ℍ[ℝ] := q * v * star q

/-- **Rotations compose by multiplying their quaternions.** -/
theorem conj_comp (q₁ q₂ v : ℍ[ℝ]) : conjRot q₁ (conjRot q₂ v) = conjRot (q₁ * q₂) v := by
  simp only [conjRot, star_mul, mul_assoc]

/-- **Every 3D quaternion rotation has an axis:** for a unit quaternion `q`, the imaginary part of
`q` is fixed. -/
theorem conj_fixes_axis (q : ℍ[ℝ]) (hq : normSq q = 1) : conjRot q q.im = q.im := by
  have hc : q * q.im = q.im * q := by
    ext <;> simp <;> ring
  simp only [conjRot]
  rw [hc, mul_assoc, Quaternion.self_mul_star, hq]; simp

/-- **Quarter turns about different axes do not commute** (`i·j = k` but `j·i = −k`). -/
theorem quaternion_spins_noncommute :
    (⟨0, 1, 0, 0⟩ : ℍ[ℝ]) * ⟨0, 0, 1, 0⟩ ≠ (⟨0, 0, 1, 0⟩ : ℍ[ℝ]) * ⟨0, 1, 0, 0⟩ := by
  intro h
  have := congrArg (fun x : ℍ[ℝ] => x.imK) h
  norm_num [Quaternion.imK_mul] at this

/-- Multiplying by a quaternion scales length by its norm; by a unit quaternion it preserves
length. -/
theorem norm_left_mul (p v : ℍ[ℝ]) (hp : ‖p‖ = 1) : ‖p * v‖ = ‖v‖ := by
  rw [norm_mul, hp, one_mul]

/-- **4D multiplication spin has no axis:** if `p ≠ 1`, then `v ↦ p v` fixes no nonzero vector. -/
theorem left_mul_no_fixed_vector (p v : ℍ[ℝ]) (hp : p ≠ 1) (hv : v ≠ 0) : p * v ≠ v := by
  intro h
  apply hp
  have : p * v = 1 * v := by rw [h, one_mul]
  exact mul_right_cancel₀ hv this

/-- The unit quaternion `cos a + i sin a`. -/
noncomputable def qrot (a : ℝ) : ℍ[ℝ] := ⟨Real.cos a, Real.sin a, 0, 0⟩

theorem normSq_qrot (a : ℝ) : normSq (qrot a) = 1 := by
  simp [qrot, Quaternion.normSq_def', Real.cos_sq_add_sin_sq]

/-- **Left × right multiplication is a double rotation.**  `v ↦ (cos α + i sin α) v (cos β + i sin β)`
turns the coordinate plane `(re, i)` by `α + β` and the plane `(j, k)` by `α − β`. -/
theorem left_right_double_rotation (α β : ℝ) (v : ℍ[ℝ]) :
    let w := qrot α * v * qrot β
    w.re = Real.cos (α + β) * v.re - Real.sin (α + β) * v.imI ∧
    w.imI = Real.sin (α + β) * v.re + Real.cos (α + β) * v.imI ∧
    w.imJ = Real.cos (α - β) * v.imJ - Real.sin (α - β) * v.imK ∧
    w.imK = Real.sin (α - β) * v.imJ + Real.cos (α - β) * v.imK := by
  simp only [qrot, Quaternion.re_mul, Quaternion.imI_mul, Quaternion.imJ_mul, Quaternion.imK_mul,
    Real.cos_add, Real.sin_add, Real.cos_sub, Real.sin_sub]
  refine ⟨by ring, by ring, by ring, by ring⟩

/-- Every pair of plane angles is reached by a left and a right factor. -/
theorem double_rotation_reachable (θ₁ θ₂ : ℝ) :
    ∃ α β : ℝ, α + β = θ₁ ∧ α - β = θ₂ :=
  ⟨(θ₁ + θ₂) / 2, (θ₁ - θ₂) / 2, by ring, by ring⟩

end GLM.Spin
