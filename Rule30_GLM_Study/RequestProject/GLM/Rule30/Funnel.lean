module

public import RequestProject.GLM.Rule30.ConeGeometry
public import RequestProject.GLM.Rule30.SpinSweep
public import RequestProject.GLM.Rule30.SpinLattice
public import RequestProject.GLM.Rule30.Diagonals

/-!
# Round 19: is the triangle the 2D view of a curved surface — a hole pulled down to a point?

Question (user, Round 19): *is the 2D triangle we see perhaps a pattern on a curved surface, of
which we only see the 2D perspective?  Is the point pulled down into a deep hole stretching to
the core?*

Space-time points are `(t, z) : ℝ × ℂ` as in `SpinSweep.lean` (depth/time `t`, a 2D space `ℂ`).
The **side view** keeps `(t, Re z)` and forgets the depth direction `Im z`.

## 1. The side view cannot tell which surface it is looking at

* `sideView_tri`, `sideView_roundCone`, `sideView_pyr`: the flat triangle, the round 90° cone (the
  "hole" `‖z‖ ≤ t` with the seed at its tip) and the square pyramid all have **the same side view**,
  Rule 30's triangle `|x| ≤ t`.
* `side_view_bodies_distinct`: the three bodies are different.  So the 2D picture alone cannot
  decide whether it is flat or the outline of a hole; the depth is exactly what it forgets.

## 2. If it is a round hole, it is a straight cone, not a curved bowl

* `funnel f` is the round hole whose radius at depth `t` is `f t` (any profile: a bowl, a
  gravity-well funnel, a horn, …).  `sideView_funnel`: its side view is `|x| ≤ f t`.
* `funnel_side_view_triangle`: if that side view is Rule 30's triangle, then `f t = t` for every
  `t ≥ 0` — the hole is the 45° cone.  A curved profile shows curved edges; e.g. the paraboloid
  bowl `f t = √t` does not give the triangle (`paraboloid_not_triangle`).  Rule 30's edges are
  exactly straight (`seed_pattern_triangle`), so the walls of any round hole behind it are straight.

## 3. A cone is flat everywhere except at its tip: the whole curvature sits in the point

* `coneEmbed Θ s θ` rolls the flat sector of opening angle `Θ` (polar coordinates `s`, `θ`) up into
  a cone in `ℝ³`.  `coneEmbed_dist_apex`: the point is at distance `s` from the tip.
  `coneEmbed_metric`: the two coordinate velocities have squared lengths `1` and `s²` and are
  perpendicular — the flat metric `ds² + s² dθ²`.  So, away from the tip, the cone is just the
  plane bent without stretching: **no curvature**.
* `coneEmbed_circle_length`: the circle at distance `s` from the tip has length `Θ·s` instead of
  `2π·s`.  The missing angle `2π − Θ` (the angle deficit) is all the curvature of the surface, and
  it is concentrated in the tip.  This is the picture of a point mass in 2+1-dimensional gravity:
  flat everywhere, with a conical point.

## 4. Rule 30's triangle rolled into a hole

* `rolled_seam_black`: the two edges of Rule 30's triangle are black in every row, so gluing the
  left edge to the right edge is consistent with the colours: the pattern really can be drawn on
  the rolled-up surface without a seam mismatch.  `rolledRow` is row `t` drawn on the ring
  `ZMod (2t)`; `rolledRow_seam` checks the glued cell.
* `rolled_ring_card`: after gluing, row `t` is a ring of exactly `2t` cells at distance `t` from
  the seed.  Circumference `2t` at radius `t` means the sector angle is `Θ = 2` (radians), so the
  cone has angle deficit `2π − 2 ≈ 4.28` (`rule30_cone_deficit`): a narrow, deep hole whose walls
  make the angle `arcsin (1/π) ≈ 18.6°` with its axis, depth `√(π² − 1) ≈ 2.98` times its rim
  radius (`rule30_cone_shape`).
* `spun_cone_angle`: the round 90° cone of §1 (the spun triangle of Round 17) is `coneEmbed` with
  `Θ = √2·π`; it is a wider hole, deficit `(2 − √2)·π`.
-/

@[expose] public section

namespace GLM.Funnel

open Complex Set Real GLM.Spin

/-! ## 1. Side views -/

/-- The side view of a body: keep the depth `t` and the coordinate `Re z`, forget `Im z`. -/
def sideView (S : Set (ℝ × ℂ)) : Set (ℝ × ℝ) := {q | ∃ p ∈ S, p.1 = q.1 ∧ p.2.re = q.2}

/-- Rule 30's triangle as a picture in the plane: `|x| ≤ t`. -/
def flatTriangle : Set (ℝ × ℝ) := {q | |q.2| ≤ q.1}

theorem sideView_tri : sideView tri = flatTriangle := by
  ext ⟨t, x⟩
  simp only [sideView, flatTriangle, tri, mem_setOf_eq]
  constructor
  · rintro ⟨⟨t', z⟩, ⟨hz, hle⟩, rfl, rfl⟩; exact hle
  · intro h; exact ⟨(t, (x : ℂ)), ⟨by simp, by simpa using h⟩, rfl, by simp⟩

theorem sideView_roundCone : sideView (roundCone 1) = flatTriangle := by
  ext ⟨t, x⟩
  simp only [sideView, flatTriangle, roundCone, mem_setOf_eq, one_mul]
  constructor
  · rintro ⟨⟨t', z⟩, hz, rfl, rfl⟩; exact (abs_re_le_norm z).trans hz
  · intro h; exact ⟨(t, (x : ℂ)), by simpa using h, rfl, by simp⟩

theorem sideView_pyr : sideView pyr = flatTriangle := by
  ext ⟨t, x⟩
  simp only [sideView, flatTriangle, pyr, mem_setOf_eq]
  constructor
  · rintro ⟨⟨t', z⟩, hz, rfl, rfl⟩; exact (le_max_left _ _).trans hz
  · intro h; exact ⟨(t, (x : ℂ)), by simpa using h, rfl, by simp⟩

/-- **Same side view, three different bodies.** -/
theorem side_view_bodies_distinct : tri ≠ roundCone 1 ∧ roundCone 1 ≠ pyr ∧ tri ≠ pyr := by
  refine ⟨fun h => ?_, fun h => ?_, fun h => ?_⟩
  · have : ((1:ℝ), I) ∈ roundCone 1 := by simp [roundCone]
    rw [← h] at this; simp [tri] at this
  · have : ((1:ℝ), 1 + I) ∈ pyr := by simp [pyr]
    rw [← h] at this
    simp only [roundCone, mem_setOf_eq, one_mul] at this
    have h2 : ‖(1:ℂ) + I‖ = √2 := by
      rw [Complex.norm_def, Complex.normSq_apply]; norm_num
    rw [h2] at this
    nlinarith [Real.sq_sqrt (show (0:ℝ) ≤ 2 by norm_num), Real.sqrt_nonneg 2]
  · have : ((1:ℝ), I) ∈ pyr := by simp [pyr]
    rw [← h] at this; simp [tri] at this

/-! ## 2. Round holes with an arbitrary profile -/

/-- The round hole whose radius at depth `t` is `f t`. -/
def funnel (f : ℝ → ℝ) : Set (ℝ × ℂ) := {p | ‖p.2‖ ≤ f p.1}

theorem sideView_funnel (f : ℝ → ℝ) : sideView (funnel f) = {q | |q.2| ≤ f q.1} := by
  ext ⟨t, x⟩
  simp only [sideView, funnel, mem_setOf_eq]
  constructor
  · rintro ⟨⟨t', z⟩, hz, rfl, rfl⟩; exact (abs_re_le_norm z).trans hz
  · intro h; exact ⟨(t, (x : ℂ)), by simpa using h, rfl, by simp⟩

/-- **A round hole whose side view is Rule 30's triangle has straight walls:** its radius at
depth `t` is `t`. -/
theorem funnel_side_view_triangle (f : ℝ → ℝ) (h : sideView (funnel f) = flatTriangle) :
    ∀ t, 0 ≤ t → f t = t := by
  intro t ht
  rw [sideView_funnel] at h
  have h1 : (t, t) ∈ {q : ℝ × ℝ | |q.2| ≤ f q.1} := by
    rw [h]; simp [flatTriangle, abs_of_nonneg ht]
  simp only [mem_setOf_eq, abs_of_nonneg ht] at h1
  have h2 : (t, f t) ∈ flatTriangle := by
    rw [← h]; simp only [mem_setOf_eq]; rw [abs_of_nonneg (ht.trans h1)]
  simp only [flatTriangle, mem_setOf_eq, abs_of_nonneg (ht.trans h1)] at h2
  linarith

/-- A paraboloid bowl does not look like the triangle from the side. -/
theorem paraboloid_not_triangle : sideView (funnel Real.sqrt) ≠ flatTriangle := by
  intro h
  have := funnel_side_view_triangle _ h 4 (by norm_num)
  have h4 : Real.sqrt 4 = 2 := by
    rw [show (4:ℝ) = 2 ^ 2 by norm_num, Real.sqrt_sq (by norm_num)]
  rw [h4] at this; norm_num at this

/-! ## 3. The cone: flat except at the tip -/

/-- The flat sector of angle `Θ`, polar coordinates `(s, θ)`, rolled up into a cone in `ℝ³`.
Coordinates: (depth, x, y).  `a = Θ / (2π)` is the ratio rim-radius : slant distance. -/
noncomputable def coneEmbed (Θ s θ : ℝ) : ℝ × ℝ × ℝ :=
  (s * √(1 - (Θ / (2 * π)) ^ 2), s * (Θ / (2 * π)) * Real.cos (θ * (2 * π / Θ)),
    s * (Θ / (2 * π)) * Real.sin (θ * (2 * π / Θ)))

/-- Squared Euclidean length in `ℝ³`. -/
def sqLen (v : ℝ × ℝ × ℝ) : ℝ := v.1 ^ 2 + v.2.1 ^ 2 + v.2.2 ^ 2

/-- Euclidean dot product in `ℝ³`. -/
def dot3 (v w : ℝ × ℝ × ℝ) : ℝ := v.1 * w.1 + v.2.1 * w.2.1 + v.2.2 * w.2.2

theorem cone_ratio_sq_le_one (Θ : ℝ) (hΘ : 0 < Θ) (hΘ' : Θ ≤ 2 * π) :
    (Θ / (2 * π)) ^ 2 ≤ 1 := by
  have hp := Real.pi_pos
  have h1 : Θ / (2 * π) ≤ 1 := by rw [div_le_one (by positivity)]; exact hΘ'
  have h0 : 0 ≤ Θ / (2 * π) := by positivity
  nlinarith

/-- Every point of the rolled sector is at distance `s` from the tip. -/
theorem coneEmbed_dist_apex (Θ s θ : ℝ) (hΘ : 0 < Θ) (hΘ' : Θ ≤ 2 * π) :
    sqLen (coneEmbed Θ s θ) = s ^ 2 := by
  have h := Real.sq_sqrt (sub_nonneg.mpr (cone_ratio_sq_le_one Θ hΘ hΘ'))
  simp only [sqLen, coneEmbed]
  have hc := Real.sin_sq_add_cos_sq (θ * (2 * π / Θ))
  linear_combination s ^ 2 * h + (s * (Θ / (2 * π))) ^ 2 * hc

/-- The velocity of the cone point when `s` moves (with `θ` fixed). -/
noncomputable def coneDs (Θ θ : ℝ) : ℝ × ℝ × ℝ :=
  (√(1 - (Θ / (2 * π)) ^ 2), (Θ / (2 * π)) * Real.cos (θ * (2 * π / Θ)),
    (Θ / (2 * π)) * Real.sin (θ * (2 * π / Θ)))

/-- The velocity of the cone point when `θ` moves (with `s` fixed). -/
noncomputable def coneDθ (Θ s θ : ℝ) : ℝ × ℝ × ℝ :=
  (0, -(s * Real.sin (θ * (2 * π / Θ))), s * Real.cos (θ * (2 * π / Θ)))

theorem coneDs_hasDeriv (Θ s θ : ℝ) :
    HasDerivAt (fun u => (coneEmbed Θ u θ).1) (coneDs Θ θ).1 s ∧
    HasDerivAt (fun u => (coneEmbed Θ u θ).2.1) (coneDs Θ θ).2.1 s ∧
    HasDerivAt (fun u => (coneEmbed Θ u θ).2.2) (coneDs Θ θ).2.2 s := by
  simp only [coneEmbed, coneDs]
  refine ⟨?_, ?_, ?_⟩
  · simpa using (hasDerivAt_id s).mul_const (√(1 - (Θ / (2 * π)) ^ 2))
  · simpa [mul_assoc] using
      (hasDerivAt_id s).mul_const ((Θ / (2 * π)) * Real.cos (θ * (2 * π / Θ)))
  · simpa [mul_assoc] using
      (hasDerivAt_id s).mul_const ((Θ / (2 * π)) * Real.sin (θ * (2 * π / Θ)))

theorem coneDθ_hasDeriv (Θ s θ : ℝ) (hΘ : Θ ≠ 0) :
    HasDerivAt (fun u => (coneEmbed Θ s u).1) (coneDθ Θ s θ).1 θ ∧
    HasDerivAt (fun u => (coneEmbed Θ s u).2.1) (coneDθ Θ s θ).2.1 θ ∧
    HasDerivAt (fun u => (coneEmbed Θ s u).2.2) (coneDθ Θ s θ).2.2 θ := by
  have hp := Real.pi_pos.ne'
  simp only [coneEmbed, coneDθ]
  refine ⟨hasDerivAt_const _ _, ?_, ?_⟩
  · have := ((hasDerivAt_id θ).mul_const (2 * π / Θ)).cos.const_mul (s * (Θ / (2 * π)))
    convert this using 1
    simp; field_simp
  · have := ((hasDerivAt_id θ).mul_const (2 * π / Θ)).sin.const_mul (s * (Θ / (2 * π)))
    convert this using 1
    simp; field_simp

/-- **The cone is flat away from its tip:** its metric is `ds² + s² dθ²`, the metric of the flat
plane in polar coordinates. -/
theorem coneEmbed_metric (Θ s θ : ℝ) (hΘ : 0 < Θ) (hΘ' : Θ ≤ 2 * π) :
    sqLen (coneDs Θ θ) = 1 ∧ sqLen (coneDθ Θ s θ) = s ^ 2 ∧ dot3 (coneDs Θ θ) (coneDθ Θ s θ) = 0 := by
  have h := Real.sq_sqrt (sub_nonneg.mpr (cone_ratio_sq_le_one Θ hΘ hΘ'))
  have hc := Real.sin_sq_add_cos_sq (θ * (2 * π / Θ))
  simp only [sqLen, coneDs, coneDθ, dot3]
  refine ⟨?_, ?_, ?_⟩
  · linear_combination h + (Θ / (2 * π)) ^ 2 * hc
  · linear_combination s ^ 2 * hc
  · ring

/-- The sector angle `θ ∈ [0, Θ)` goes once around the cone: `θ = Θ` returns to `θ = 0`. -/
theorem coneEmbed_closes (Θ s : ℝ) (hΘ : Θ ≠ 0) : coneEmbed Θ s Θ = coneEmbed Θ s 0 := by
  have hp := Real.pi_pos.ne'
  have : Θ * (2 * π / Θ) = 2 * π := by field_simp
  simp [coneEmbed, this]

/-- **The circle at distance `s` from the tip has length `Θ·s`** (its radius in `ℝ³` is
`s·Θ/(2π)`), short of the flat `2π·s` by the angle deficit `(2π − Θ)·s`. -/
theorem coneEmbed_circle_length (Θ s : ℝ) :
    2 * π * (s * (Θ / (2 * π))) = Θ * s ∧ 2 * π * s - Θ * s = (2 * π - Θ) * s := by
  have hp := Real.pi_pos.ne'
  constructor
  · field_simp
  · ring

/-! ## 4. Rule 30's triangle, rolled up -/

open GLM.Rule30 in
/-- Both edges of Rule 30's triangle are black in every row: gluing them is colour-consistent. -/
theorem rolled_seam_black (t : ℕ) :
    evolve seed t (-(t : ℤ)) = true ∧ evolve seed t t = true ∧
      evolve seed t (-(t : ℤ)) = evolve seed t t := by
  obtain ⟨-, h1, h2⟩ := seed_pattern_triangle t
  exact ⟨h1, h2, h1.trans h2.symm⟩

open GLM.Rule30 in
/-- Row `t` drawn on a ring of `2t` cells (the left edge `-t` and the right edge `t` glued). -/
def rolledRow (t : ℕ) (k : ZMod (2 * t)) : Bool := evolve seed t (-(t : ℤ) + (k.val : ℤ))

open GLM.Rule30 in
/-- The glued cell: position `0` of the ring is the left edge and also the right edge. -/
theorem rolledRow_seam (t : ℕ) :
    rolledRow t 0 = evolve seed t (-(t : ℤ)) ∧ rolledRow t 0 = evolve seed t t := by
  have h0 : rolledRow t 0 = evolve seed t (-(t : ℤ)) := by simp [rolledRow]
  exact ⟨h0, h0.trans (rolled_seam_black t).2.2⟩

open GLM.Rule30 in
/-- Every cell of row `t` appears on the ring. -/
theorem rolledRow_covers (t : ℕ) (i : ℤ) (hi : -(t : ℤ) ≤ i) (hi' : i < t) :
    ∃ k : ZMod (2 * t), rolledRow t k = evolve seed t i := by
  haveI : NeZero (2 * t) := ⟨by omega⟩
  refine ⟨((i + t).toNat : ZMod (2 * t)), ?_⟩
  rw [rolledRow, ZMod.val_cast_of_lt (by omega)]
  congr 1
  omega

/-- After gluing, row `t` is a ring of exactly `2t` cells. -/
theorem rolled_ring_card (t : ℕ) : (Finset.Ioc (-(t : ℤ)) t).card = 2 * t := by
  simp; omega

/-- **Rule 30's rolled triangle is a cone of sector angle `2`:** positive angle deficit `2π − 2`. -/
theorem rule30_cone_deficit : 0 < 2 * π - 2 ∧ (2 : ℝ) < 2 * π := by
  have := Real.pi_gt_three; constructor <;> linarith

/-- Shape of Rule 30's hole: walls at `arcsin (1/π)` from the axis, depth `√(π² − 1)` times the rim
radius (from `coneEmbed 2`: rim ratio `1/π`, depth ratio `√(1 − 1/π²)`). -/
theorem rule30_cone_shape :
    (2 : ℝ) / (2 * π) = 1 / π ∧ √(1 - (1 / π) ^ 2) / (1 / π) = √(π ^ 2 - 1) ∧
      Real.arcsin (1 / π) < π / 6 := by
  have hp := Real.pi_pos
  have h3 := Real.pi_gt_three
  refine ⟨by field_simp, ?_, ?_⟩
  · rw [div_eq_mul_inv, one_div, inv_inv]
    have : 1 - (π⁻¹) ^ 2 = (π ^ 2 - 1) / π ^ 2 := by field_simp
    rw [this, Real.sqrt_div' _ (by positivity), Real.sqrt_sq hp.le]
    field_simp
  · rw [← Real.arcsin_sin (show -(π / 2) ≤ π / 6 by linarith) (show π / 6 ≤ π / 2 by linarith),
      Real.sin_pi_div_six]
    have : 0 < 1 / π := by positivity
    have h2 : 1 / π < 1 / 2 := by rw [div_lt_div_iff₀ hp (by norm_num)]; linarith
    exact Real.arcsin_lt_arcsin (by linarith) h2 (by norm_num)

/-- **The spun 90° cone is `coneEmbed` with `Θ = √2·π`:** depth equals rim radius (walls at
`45°`), and the angle deficit is `(2 − √2)·π`. -/
theorem spun_cone_angle (s θ : ℝ) :
    let p := coneEmbed (√2 * π) s θ
    p.1 = s * (√2 / 2) ∧ p.2.1 ^ 2 + p.2.2 ^ 2 = p.1 ^ 2 ∧
      2 * π - √2 * π = (2 - √2) * π ∧ 0 < (2 - √2) * π := by
  intro p
  have hp := Real.pi_pos
  have h2 := Real.sq_sqrt (show (0:ℝ) ≤ 2 by norm_num)
  have ha : √2 * π / (2 * π) = √2 / 2 := by field_simp
  have hs : √2 < 2 := by
    rw [show (2:ℝ) = √4 by rw [show (4:ℝ) = 2 ^ 2 by norm_num, Real.sqrt_sq (by norm_num)]]
    exact Real.sqrt_lt_sqrt (by norm_num) (by norm_num)
  have h1 : (1 : ℝ) - (√2 / 2) ^ 2 = (√2 / 2) ^ 2 := by nlinarith
  have hq : √(1 - (√2 / 2) ^ 2) = √2 / 2 := by
    rw [h1, Real.sqrt_sq (by positivity)]
  have hp1 : p.1 = s * (√2 / 2) := by simp only [p, coneEmbed, ha, hq]
  refine ⟨hp1, ?_, by ring, by nlinarith⟩
  rw [hp1]; simp only [p, coneEmbed, ha]
  have hc := Real.sin_sq_add_cos_sq (θ * (2 * π / (√2 * π)))
  linear_combination (s * (√2 / 2)) ^ 2 * hc

/-! ## 5. What the rolled hole looks like: the seam and the line opposite it -/

open GLM.Rule30 in
/-- **The seam is visible.**  From row `2` on, the two cells on either side of the glued seam
differ (cells `±(t − 1)` for even `t`, `±(t − 2)` for odd `t`): the hole has a marked meridian and
is not symmetric about it. -/
theorem rolled_seam_visible (t : ℕ) (ht : 2 ≤ t) :
    (t % 2 = 0 → evolve seed t (-((t : ℤ) - 1)) ≠ evolve seed t ((t : ℤ) - 1)) ∧
      (t % 2 = 1 → evolve seed t (-((t : ℤ) - 2)) ≠ evolve seed t ((t : ℤ) - 2)) :=
  rule30_row_not_mirror t ht

open GLM.Rule30 in
/-- **The centre column runs down the meridian opposite the seam:** on the ring of row `t`
(`2t` cells, seam at position `0`) the centre cell sits at position `t`, half way round. -/
theorem rolledRow_centre (t : ℕ) (ht : 0 < t) :
    rolledRow t (t : ZMod (2 * t)) = centerCol t := by
  haveI : NeZero (2 * t) := ⟨by omega⟩
  rw [rolledRow, ZMod.val_cast_of_lt (by omega), centerCol]
  congr 1
  ring

/-- Angle around the hole (seam at `0` and `2π`) of the cell `c` of row `t`. -/
noncomputable def ringAngle (t : ℕ) (c : ℤ) : ℝ := π * ((c : ℝ) + t) / t

open Filter Topology in
/-- **Every fixed column winds onto the meridian opposite the seam** (angle `π`). -/
theorem ringAngle_column_tendsto (c : ℤ) :
    Tendsto (fun t : ℕ => ringAngle t c) atTop (𝓝 π) := by
  have h := (tendsto_one_div_atTop_nhds_zero_nat).const_mul (π * c)
  rw [mul_zero] at h
  have h2 := h.const_add π
  rw [add_zero] at h2
  refine h2.congr' ?_
  filter_upwards [eventually_gt_atTop 0] with t ht
  have : (t : ℝ) ≠ 0 := by exact_mod_cast ht.ne'
  simp only [ringAngle]
  field_simp
  ring

open Filter Topology in
/-- **Every diagonal at a fixed distance `D` from the right edge winds onto the seam**
(angle `2π`); these are the diagonals that are exactly periodic, with period `2^D`
(`rdiag_periodic`). -/
theorem ringAngle_right_diagonal_tendsto (D : ℕ) :
    Tendsto (fun t : ℕ => ringAngle t ((t : ℤ) - D)) atTop (𝓝 (2 * π)) := by
  have h := (tendsto_one_div_atTop_nhds_zero_nat).const_mul (-(π * D))
  rw [mul_zero] at h
  have h2 := h.const_add (2 * π)
  rw [add_zero] at h2
  refine h2.congr' ?_
  filter_upwards [eventually_gt_atTop 0] with t ht
  have : (t : ℝ) ≠ 0 := by exact_mod_cast ht.ne'
  simp only [ringAngle]
  push_cast
  field_simp
  ring

end GLM.Funnel
