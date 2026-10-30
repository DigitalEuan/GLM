module

public import RequestProject.GLM.Rule30.ConeSeparation
public import RequestProject.GLM.Rule30.SeedBoundary
public import Mathlib.Analysis.SpecialFunctions.Trigonometric.Arctan

/-!
# Round 16: the triangle, its angle, and whether it is a slice of a cone

Question (user, Round 16): *stepping back we see a triangle; there is a ratio of empty space
around it in degrees.  Is this always a 2D slice of a circle, or sometimes a slice of a cone
inside a sphere?*

## 1. Rule 30's own triangles (exact)

Rule 30 has one space dimension, so its space-time diagram is genuinely two-dimensional and the
triangle is the whole light cone, not a slice of something bigger.  There are two different
triangles, and they have different shapes:

* **The dependency triangle (what a cell reads).** The cell `(t, c)` reads exactly the cells
  `[c − t, c + t]` of row 0 (`evolve_update_far`; all of them matter, `WholeCone.lean`).  From the
  seed, the black pattern fills exactly the triangle `|i| ≤ t` and both corners are always black
  (`seed_pattern_triangle`).  Its sides have slope `±1`: with square cells the apex angle is `90°`.
* **The influence triangle (where a change can go).**  Flip one cell `j` of any row.
  - The **right side is rigid**: the cell `(n, j + n)` flips, for **every** row and every `n`
    (`influence_right_ray`).  The right edge always moves at speed `1`.
  - The **left side is not**: it can move at full speed (white background,
    `influence_left_ray_fast`) or not at all (`influence_left_ray_stalls`: behind a "wall" no
    cell to the left of `j` ever changes).
  So the influence triangle has one fixed `45°` side and one side anywhere between `0°` and `45°`
  from the time axis.  This is the chirality of Rule 30 seen as geometry, and it is the
  "arrow"/perspective the GLM can use: the rigid side points to the right, the reading direction
  (`columns_determine_left`) points to the left.

## 2. Slices of higher-dimensional lattice cones (exact)

For a cellular automaton in `d` space dimensions with the usual (Moore) neighbourhood, the light
cone in `(d+1)`-dimensional space-time is `{(t, x) | max_i |x_i| ≤ t}`: a pyramid over a square
(cube), **never a round cone**.  For `d = 2`:

* `moore_slice_mem`: the vertical slice in the direction `(cos θ, sin θ)` is the triangle
  `|s| · max(|cos θ|, |sin θ|) ≤ t`.
* `moore_slice_factor_bounds`: `1/√2 ≤ max(|cos θ|, |sin θ|) ≤ 1`, so the slice's half-angle has
  tangent between `1` and `√2`: the apex angle of the slice is between `90°` (slice parallel to
  a face, `θ = 0`) and `2·arctan √2 ≈ 109.47°` (diagonal slice, `θ = π/4`), and
  `cos (2 · arctan √2) = −1/3` (`diagonal_slice_angle`).

So a 1D rule like Rule 30 seen as a slice of a 2D rule gives a triangle whose angle depends on the
slicing direction; a round cone (and a round circle of directions) would need a
rotation-invariant speed of light, which a lattice rule does not have.  The fraction of all
directions that a lattice cone occupies is computed in `LatticeConeFraction.lean`.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## The dependency triangle of the seed -/

/-- **The seed's pattern is exactly the triangle `|i| ≤ t`:** every black cell is inside it, and
both corners `(t, −t)`, `(t, t)` are black. -/
theorem seed_pattern_triangle (t : ℕ) :
    (∀ i : ℤ, evolve seed t i = true → -(t : ℤ) ≤ i ∧ i ≤ t) ∧
      evolve seed t (-t) = true ∧ evolve seed t t = true := by
  refine ⟨fun i hi => ?_, evolve_seed_left_edge t, evolve_seed_right_edge t⟩
  by_contra h
  rw [evolve_seed_outside t i (by rw [lt_abs]; omega)] at hi
  exact Bool.false_ne_true hi

/-! ## The influence triangle -/

/-- **Nothing moves faster than one cell per step:** flipping cell `j` cannot change the cell
`(n, c)` unless `|c − j| ≤ n`. -/
theorem influence_inside_cone (x : Config) (j : ℤ) (n : ℕ) (c : ℤ) (hc : n < |c - j|) :
    evolve (flipAt x j) n c = evolve x n c := by
  unfold flipAt
  exact evolve_update_far x n c j _ (by rcases lt_abs.mp hc with h | h <;> omega)

/-- **The right side of the influence triangle is rigid:** for every row, flipping cell `j`
flips the cell `(n, j + n)` for every `n`. -/
theorem influence_right_ray (x : Config) (j : ℤ) (n : ℕ) :
    evolve (flipAt x j) n (j + n) = !evolve x n (j + n) := by
  have := evolve_flip_left_edge x n (j + n)
  rwa [show j + (n : ℤ) - n = j by ring] at this

/-- **The left side can move at full speed:** on the white row, flipping cell `j` changes the cell
`(n, j − n)` for every `n`. -/
theorem influence_left_ray_fast (j : ℤ) (n : ℕ) :
    evolve (flipAt (fun _ => false) j) n (j - n) ≠ evolve (fun _ => false) n (j - n) := by
  have h1 : flipAt (fun _ => false) j = fun i => seed (i + -j) := by
    funext i; by_cases h : i = j <;> simp [flipAt, seed, Function.update, h]; omega
  rw [h1, evolve_shift, evolve_false, show j - n + -j = -(n : ℤ) by ring,
    evolve_seed_left_edge]
  decide

/-- **The left side can stall completely:** there is a row such that flipping its cell `2`
never changes any cell at a position `≤ 1`, at any time. -/
theorem influence_left_ray_stalls :
    ∃ x : Config, ∀ n : ℕ, ∀ c ≤ (1 : ℤ), evolve (flipAt x 2) n c = evolve x n c := by
  refine ⟨leftWall (fun _ => false), fun n c hc => ?_⟩
  have h : flipAt (leftWall (fun _ => false)) 2 =
      leftWall (Function.update (fun _ => false) 2 true) := by
    funext i
    by_cases hi : i = 2
    · subst hi; simp [flipAt, leftWall]
    · simp only [flipAt, leftWall, Function.update_of_ne hi]
  rw [h, left_wall_stationary _ n c hc, left_wall_stationary _ n c hc]

/-! ## Slices of the 2D lattice cone -/

/-- The light cone of a 2D cellular automaton with the Moore (3×3) neighbourhood, in space-time
coordinates `(t, x, y)`. -/
def mooreCone : Set (ℝ × ℝ × ℝ) := {p | max |p.2.1| |p.2.2| ≤ p.1}

/-- **The vertical slice in direction `θ`** is the triangle `|s| · max(|cos θ|, |sin θ|) ≤ t`. -/
theorem moore_slice_mem (θ t s : ℝ) :
    (t, s * Real.cos θ, s * Real.sin θ) ∈ mooreCone ↔
      |s| * max |Real.cos θ| |Real.sin θ| ≤ t := by
  simp only [mooreCone, Set.mem_setOf_eq, abs_mul]
  rw [mul_max_of_nonneg _ _ (abs_nonneg s)]

/-- **The slice factor lies between `1/√2` and `1`.**  So the half-angle `α` of every vertical
slice satisfies `1 ≤ tan α ≤ √2`. -/
theorem moore_slice_factor_bounds (θ : ℝ) :
    1 / Real.sqrt 2 ≤ max |Real.cos θ| |Real.sin θ| ∧ max |Real.cos θ| |Real.sin θ| ≤ 1 := by
  refine ⟨?_, max_le (Real.abs_cos_le_one θ) (Real.abs_sin_le_one θ)⟩
  set m := max |Real.cos θ| |Real.sin θ|
  have hm0 : 0 ≤ m := le_max_of_le_left (abs_nonneg _)
  have h1 : Real.cos θ ^ 2 ≤ m ^ 2 := by
    rw [← sq_abs]; exact pow_le_pow_left₀ (abs_nonneg _) (le_max_left _ _) 2
  have h2 : Real.sin θ ^ 2 ≤ m ^ 2 := by
    rw [← sq_abs]; exact pow_le_pow_left₀ (abs_nonneg _) (le_max_right _ _) 2
  have hsq : (1 / Real.sqrt 2) ^ 2 ≤ m ^ 2 := by
    rw [div_pow, Real.sq_sqrt (by norm_num)]
    nlinarith [Real.sin_sq_add_cos_sq θ]
  exact (pow_le_pow_iff_left₀ (by positivity) hm0 (by norm_num)).mp hsq

/-- The face-parallel slice (`θ = 0`) has factor `1`: apex angle `90°`. -/
theorem moore_slice_face : max |Real.cos 0| |Real.sin 0| = 1 := by simp

/-- The diagonal slice (`θ = π/4`) has factor `1/√2`: half-angle `arctan √2`. -/
theorem moore_slice_diagonal :
    max |Real.cos (Real.pi / 4)| |Real.sin (Real.pi / 4)| = 1 / Real.sqrt 2 := by
  rw [Real.cos_pi_div_four, Real.sin_pi_div_four, max_self,
    abs_of_pos (by positivity)]
  field_simp
  rw [Real.sq_sqrt (by norm_num)]

/-- **The diagonal slice's apex angle `2·arctan √2` has cosine `−1/3`** (about `109.47°`, the
tetrahedral angle). -/
theorem diagonal_slice_angle : Real.cos (2 * Real.arctan (Real.sqrt 2)) = -1 / 3 := by
  rw [Real.cos_two_mul, Real.cos_arctan]
  rw [div_pow, one_pow, Real.sq_sqrt (by positivity), Real.sq_sqrt (by norm_num)]
  norm_num

/-- The face-parallel slice's apex angle is `90°`. -/
theorem face_slice_angle : 2 * Real.arctan 1 = Real.pi / 2 := by
  rw [Real.arctan_one]; ring

end GLM.Rule30
