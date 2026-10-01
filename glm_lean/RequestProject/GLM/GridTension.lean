/-
# The grid metrics of the ARC generation, as exact bounds

**Retrieved from the archive.**  `source_material/GLM-main.zip/arc_agi_15`
carries `ldp_grid_metrics.py`, which scores a grid by three "literal data
physics" quantities attached to each object's cell count `N`:

    mass    M(N) = ⌊N/2⌋ − φ(N)/2
    tension T(N) = 1 − Area(regular N-gon) / Area(circumscribed circle)
    radius  R(N) = 1 / (2 sin(π/N))

The first salvage pass retrieved the mass — it is the sub-cycle count of
`Totient.lean`, proved there for every `N` — and recorded the other two as
"float geometry; they could be retrieved as rational bounds, and were not,
because nothing in the current system consumes them".  This file closes that
item: the two quantities are defined exactly and bounded exactly, which is what
a system under the no-floats rule needs in order to use them at all.

For the regular `N`-gon inscribed in the unit circle the area is
`(N/2)·sin(2π/N)`, so — `tension_eq` — the tension is `1 − sin x / x` at
`x = 2π/N`, and:

* `tension_pos` — the tension is strictly positive for every `N ≥ 3`: a polygon
  never fills its circle;
* `tension_lt_one` — and never reaches 1, so `1 − T` is a genuine fill
  fraction;
* `tension_lt_inv_sq` — for `N ≥ 7` the tension is below `π²/N²`, so it decays
  quadratically, and `tension_lt_ten_div_sq` puts that in the rational form a
  no-floats scorer can act on: `T(N) < 10/N²`.

For the circumradius of the `N`-gon of unit side:

* `circumradius_gt` — `R(N) > N/(2π)` for every `N ≥ 3`;
* `circumradius_lt` — `R(N) < N/(2π) + 1/N` for every `N ≥ 4`.

Together these say the archive's `radius` is the perimeter over `2π` up to an
error below `1/N`.  That is the statement a grid scorer can act on, and it is
also the limitation: of the three grid metrics only the mass is arithmetic —
the other two are smooth, quadratically decaying functions of the cell count
alone, so they can rank objects by size but cannot separate two objects of the
same size, and past `N = 7` the tension is already below `10/N²`.
-/
import Mathlib

namespace GLM.GridTension

/-! ## 1. Tension -/

/-- The area of the regular `N`-gon inscribed in the unit circle. -/
noncomputable def polyArea (N : ℕ) : ℝ := (N : ℝ) / 2 * Real.sin (2 * Real.pi / N)

/-- The geometric tension `T(N) = 1 − Area(N-gon)/Area(circle)`: the archive's
`ldp.tension`. -/
noncomputable def tension (N : ℕ) : ℝ := 1 - polyArea N / Real.pi

/-- The tension is the deficit of `sin x / x` at `x = 2π/N`. -/
theorem tension_eq (N : ℕ) (hN : 3 ≤ N) :
    tension N = 1 - Real.sin (2 * Real.pi / N) / (2 * Real.pi / N) := by
  have hN3 : (3 : ℝ) ≤ N := by exact_mod_cast hN
  have hN0 : (0 : ℝ) < N := by linarith
  have hpi := Real.pi_pos
  unfold tension polyArea
  congr 1
  field_simp

/-- **A polygon never fills its circle.** -/
theorem tension_pos (N : ℕ) (hN : 3 ≤ N) : 0 < tension N := by
  have hN3 : (3 : ℝ) ≤ N := by exact_mod_cast hN
  have hN0 : (0 : ℝ) < N := by linarith
  have hpi := Real.pi_pos
  have hx : 0 < 2 * Real.pi / N := by positivity
  rw [tension_eq N hN, sub_pos, div_lt_one hx]
  exact Real.sin_lt hx

/-- The tension is a fill deficit: it never reaches 1. -/
theorem tension_lt_one (N : ℕ) (hN : 3 ≤ N) : tension N < 1 := by
  have hN3 : (3 : ℝ) ≤ N := by exact_mod_cast hN
  have hpi := Real.pi_pos
  have hN0 : (0 : ℝ) < N := by linarith
  have hx : 0 < 2 * Real.pi / N := by positivity
  have hxlt : 2 * Real.pi / N < Real.pi := by
    rw [div_lt_iff₀ hN0]; nlinarith
  have hs : 0 < Real.sin (2 * Real.pi / N) := Real.sin_pos_of_pos_of_lt_pi hx hxlt
  have hpos : 0 < Real.sin (2 * Real.pi / N) / (2 * Real.pi / N) := by positivity
  rw [tension_eq N hN]
  linarith

/-- **Quadratic decay.**  For `N ≥ 7` the tension is below `π²/N²`. -/
theorem tension_lt_inv_sq (N : ℕ) (hN : 7 ≤ N) : tension N < Real.pi ^ 2 / (N : ℝ) ^ 2 := by
  have hN7 : (7 : ℝ) ≤ N := by exact_mod_cast hN
  have hpi := Real.pi_pos
  have hpi2 : Real.pi < 3.15 := Real.pi_lt_d2
  have hN0 : (0 : ℝ) < N := by linarith
  set x : ℝ := 2 * Real.pi / N with hxdef
  have hx : 0 < x := by positivity
  have hx1 : x ≤ 1 := by rw [hxdef, div_le_one hN0]; nlinarith
  have hcube := Real.sin_gt_sub_cube hx hx1
  have hten : tension N = 1 - Real.sin x / x := tension_eq N (by omega)
  have hkey : 1 - Real.sin x / x < x ^ 2 / 4 := by
    have h : 1 - x ^ 2 / 4 < Real.sin x / x := by
      rw [lt_div_iff₀ hx]; nlinarith
    linarith
  have hx2 : x ^ 2 / 4 = Real.pi ^ 2 / (N : ℝ) ^ 2 := by
    rw [hxdef]; field_simp; ring
  rw [hten]
  linarith [hx2 ▸ hkey]

/-- The same bound in the rational form a no-floats scorer can use. -/
theorem tension_lt_ten_div_sq (N : ℕ) (hN : 7 ≤ N) : tension N < 10 / (N : ℝ) ^ 2 := by
  have hN7 : (7 : ℝ) ≤ N := by exact_mod_cast hN
  have hN0 : (0 : ℝ) < N := by linarith
  have hpi2 : Real.pi < 3.15 := Real.pi_lt_d2
  have hpi := Real.pi_pos
  have h := tension_lt_inv_sq N hN
  have h2 : Real.pi ^ 2 / (N : ℝ) ^ 2 < 10 / (N : ℝ) ^ 2 := by
    gcongr
    nlinarith
  linarith

/-! ## 2. Circumradius -/

/-- The circumradius of the regular `N`-gon of unit side: the archive's
`ldp.radius`. -/
noncomputable def circumradius (N : ℕ) : ℝ := 1 / (2 * Real.sin (Real.pi / N))

/-- **The radius is above the perimeter over `2π`.** -/
theorem circumradius_gt (N : ℕ) (hN : 3 ≤ N) : (N : ℝ) / (2 * Real.pi) < circumradius N := by
  have hN3 : (3 : ℝ) ≤ N := by exact_mod_cast hN
  have hpi := Real.pi_pos
  have hN0 : (0 : ℝ) < N := by linarith
  have hy : 0 < Real.pi / N := by positivity
  have hylt : Real.pi / N < Real.pi := by rw [div_lt_iff₀ hN0]; nlinarith
  have hs : 0 < Real.sin (Real.pi / N) := Real.sin_pos_of_pos_of_lt_pi hy hylt
  have hlt : Real.sin (Real.pi / N) < Real.pi / N := Real.sin_lt hy
  have hcancel : (N : ℝ) * (Real.pi / N) = Real.pi := by field_simp
  rw [circumradius, lt_div_iff₀ (by positivity), div_mul_eq_mul_div, div_lt_iff₀ (by positivity)]
  nlinarith [mul_lt_mul_of_pos_left hlt hN0]

/-- **And within `1/N` of it.**  So for large objects the radius carries no
information the cell count does not already carry. -/
theorem circumradius_lt (N : ℕ) (hN : 4 ≤ N) :
    circumradius N < (N : ℝ) / (2 * Real.pi) + 1 / (N : ℝ) := by
  have hN4 : (4 : ℝ) ≤ N := by exact_mod_cast hN
  have hpi := Real.pi_pos
  have hpi2 : Real.pi < 3.15 := Real.pi_lt_d2
  have hN0 : (0 : ℝ) < N := by linarith
  set y : ℝ := Real.pi / N with hydef
  have hy : 0 < y := by positivity
  have hy1 : y ≤ 1 := by rw [hydef, div_le_one hN0]; nlinarith
  have hy2 : y ^ 2 ≤ 1 := by nlinarith
  have hcube := Real.sin_gt_sub_cube hy hy1
  have hlow : 0 < y - y ^ 3 / 4 := by nlinarith
  have hs : 0 < Real.sin y := by linarith
  have hNy : (N : ℝ) = Real.pi / y := by rw [hydef]; field_simp
  have hgoal : 1 / (2 * Real.sin y) < 1 / (2 * y) + y / Real.pi := by
    rw [div_add_div _ _ (by positivity) (by positivity),
      div_lt_div_iff₀ (by positivity) (by positivity)]
    nlinarith [mul_lt_mul_of_pos_left hcube (show (0:ℝ) < 2 * (Real.pi + 2 * y * y) by positivity),
      mul_pos hy (mul_pos hy hy)]
  rw [circumradius, ← hydef]
  have hrw : (N : ℝ) / (2 * Real.pi) = 1 / (2 * y) := by rw [hNy]; field_simp
  have hrw2 : 1 / (N : ℝ) = y / Real.pi := by rw [hNy]; field_simp
  rw [hrw, hrw2]
  exact hgoal

end GLM.GridTension
