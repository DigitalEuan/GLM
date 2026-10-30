module

public import Mathlib

/-!
# Round 16: what fraction of all space-time directions does a lattice light cone fill?

Work in `k`-dimensional space-time `Fin k → ℝ`, coordinate `0` being time (so `k = d + 1` for a
cellular automaton in `d` space dimensions).  The light cone of a rule with the Moore
neighbourhood (radius one in every space direction) is

  `axisCone 0 true = {x | ∀ i, |x i| ≤ x 0}`.

Together with the past cone and the `2(k − 1)` "space-like" cones around the space axes these are
the `2k` cones `axisCone j b` around the `k` axes in both directions.  They are images of each
other under signed coordinate permutations, they cover everything, and they overlap only in a
null set.  Hence (`axisCone_fraction`):

  **for every measurable set `A` invariant under signed coordinate permutations,
  `2k · vol (cone ∩ A) = vol A`.**

Taking `A` to be the Euclidean unit ball (`euclidBall_invariant`), the light cone fills exactly
`1 / (2k)` of all directions (`lightCone_ball_fraction`):

* `k = 2` (one space dimension, e.g. Rule 30): `1/4` of the circle, i.e. `90°` of `360°`.  The
  future and past triangles together take `180°`; the other `180°` is space-like.
* `k = 3` (two space dimensions): `1/6` of the sphere, solid angle `4π/6 = 2π/3`.  The cone is a
  square pyramid, one of the six pyramids that cut a cube from its centre.

The same holds with `A` the cube (`cube_invariant`), since a cube is cut by these cones into `2k`
congruent pyramids.
-/

@[expose] public section

namespace GLM.LatticeCone

open MeasureTheory Function

variable {k : ℕ}

/-- `true ↦ 1`, `false ↦ −1`. -/
def sgn (b : Bool) : ℝ := if b then 1 else -1

@[simp] theorem sgn_mul_self (b : Bool) : sgn b * sgn b = 1 := by cases b <;> norm_num [sgn]

theorem abs_sgn_mul (b : Bool) (r : ℝ) : |sgn b * r| = |r| := by
  cases b <;> simp [sgn]

/-- The cone around axis `j` pointing in direction `b`: the coordinate `j` (with sign `b`)
dominates every coordinate in absolute value. -/
def axisCone (j : Fin k) (b : Bool) : Set (Fin k → ℝ) := {x | ∀ i, |x i| ≤ sgn b * x j}

/-- A signed coordinate permutation. -/
def signedPerm (e : Equiv.Perm (Fin k)) (d : Fin k → Bool) (x : Fin k → ℝ) : Fin k → ℝ :=
  fun i => sgn (d i) * x (e i)

theorem measurableSet_axisCone (j : Fin k) (b : Bool) : MeasurableSet (axisCone j b) := by
  have : axisCone j b = ⋂ i, {x : Fin k → ℝ | |x i| ≤ sgn b * x j} := by
    ext x; simp [axisCone]
  rw [this]
  exact MeasurableSet.iInter (fun i => measurableSet_le (by fun_prop) (by fun_prop))

/-- Signed coordinate permutations preserve volume. -/
theorem measurePreserving_signedPerm (e : Equiv.Perm (Fin k)) (d : Fin k → Bool) :
    MeasurePreserving (signedPerm e d) (volume : Measure (Fin k → ℝ)) volume := by
  have h1 : MeasurePreserving (fun x : Fin k → ℝ => fun i => x (e i)) volume volume := by
    have := volume_preserving_arrowCongr' (α₁ := Fin k) (β₁ := ℝ) e.symm
      (MeasurableEquiv.refl ℝ) (MeasurePreserving.id volume)
    convert this using 1
  have h2 : MeasurePreserving (fun y : Fin k → ℝ => fun i => sgn (d i) * y i) volume volume := by
    refine volume_preserving_pi (fun i => ?_)
    cases d i
    · convert Measure.measurePreserving_neg (volume : Measure ℝ) using 1
      funext r; simp [sgn]
    · convert MeasurePreserving.id (volume : Measure ℝ) using 1
      funext r; simp [sgn]
  exact h2.comp h1

/-- Every point lies in some axis cone. -/
theorem exists_axisCone (hk : 0 < k) (x : Fin k → ℝ) : ∃ j b, x ∈ axisCone j b := by
  haveI : Nonempty (Fin k) := ⟨⟨0, hk⟩⟩
  obtain ⟨j, hj⟩ := Finite.exists_max (fun i => |x i|)
  refine ⟨j, decide (0 ≤ x j), fun i => ?_⟩
  by_cases h : 0 ≤ x j
  · simpa [sgn, h, abs_of_nonneg h] using hj i
  · push_neg at h
    simpa [sgn, h.not_ge, abs_of_neg h] using hj i

/-- On the cone `(j, b)` the dominant coordinate equals `sgn b · x j`. -/
theorem axisCone_overlap_subset {j j' : Fin k} {b b' : Bool} {x : Fin k → ℝ}
    (hx : x ∈ axisCone j b) (hx' : x ∈ axisCone j' b') : sgn b * x j = sgn b' * x j' := by
  have h1 := hx j'
  have h2 := hx' j
  have h3 : sgn b * x j ≤ |x j| := by rw [← abs_sgn_mul b]; exact le_abs_self _
  have h4 : sgn b' * x j' ≤ |x j'| := by rw [← abs_sgn_mul b']; exact le_abs_self _
  linarith

/-- The hyperplane `sgn b · x j = sgn b' · x j'` is a null set when `(j, b) ≠ (j', b')`. -/
theorem volume_hyperplane_zero {j j' : Fin k} {b b' : Bool} (hne : (j, b) ≠ (j', b')) :
    volume {x : Fin k → ℝ | sgn b * x j = sgn b' * x j'} = 0 := by
  set φ : (Fin k → ℝ) →ₗ[ℝ] ℝ := sgn b • LinearMap.proj j - sgn b' • LinearMap.proj j'
  have hset : {x : Fin k → ℝ | sgn b * x j = sgn b' * x j'} = (LinearMap.ker φ : Set _) := by
    ext x; simp [φ, sub_eq_zero]
  rw [hset]
  refine Measure.addHaar_submodule _ _ (fun htop => ?_)
  have hmem : (Pi.single j 1 : Fin k → ℝ) ∈ LinearMap.ker φ := htop ▸ Submodule.mem_top
  rw [LinearMap.mem_ker] at hmem
  simp only [φ, LinearMap.sub_apply, LinearMap.smul_apply, LinearMap.proj_apply,
    Pi.single_eq_same, smul_eq_mul, mul_one] at hmem
  by_cases hjj : j = j'
  · subst hjj
    have hb : b ≠ b' := fun h => hne (by rw [h])
    simp only [Pi.single_eq_same, mul_one] at hmem
    cases b <;> cases b' <;> simp_all [sgn]; norm_num at hmem
  · rw [Pi.single_eq_of_ne' hjj, mul_zero, sub_zero] at hmem
    cases b <;> simp [sgn] at hmem

/-- **The fraction theorem.** For every measurable set `A` invariant under signed coordinate
permutations, the `2k` axis cones cut `A` into pieces of equal volume:
`2k · vol (axisCone j b ∩ A) = vol A`. -/
theorem axisCone_fraction (hk : 0 < k) (A : Set (Fin k → ℝ)) (hAm : MeasurableSet A)
    (hA : ∀ (e : Equiv.Perm (Fin k)) (d : Fin k → Bool) (x : Fin k → ℝ),
      signedPerm e d x ∈ A ↔ x ∈ A)
    (j : Fin k) (b : Bool) :
    (2 * k : ENNReal) * volume (axisCone j b ∩ A) = volume A := by
  classical
  -- all cones meet `A` in the same volume
  have hsame : ∀ j' b', volume (axisCone j' b' ∩ A) = volume (axisCone j b ∩ A) := by
    suffices H : ∀ j' b', volume (axisCone j' b' ∩ A) = volume (axisCone j true ∩ A) by
      intro j' b'; rw [H, H j b]
    intro j' b'
    set e : Equiv.Perm (Fin k) := Equiv.swap j' j
    set d : Fin k → Bool := fun i => if i = j' then b' else true
    have hpre : signedPerm e d ⁻¹' (axisCone j' b' ∩ A) = axisCone j true ∩ A := by
      ext x
      simp only [Set.mem_preimage, Set.mem_inter_iff, hA, and_congr_left_iff]
      intro _
      simp only [axisCone, Set.mem_setOf_eq, signedPerm, abs_sgn_mul]
      have hd : d j' = b' := by simp [d]
      rw [hd, show e j' = j from Equiv.swap_apply_left j' j, ← mul_assoc, sgn_mul_self, one_mul]
      simp only [sgn, if_true, one_mul]
      constructor
      · intro h i
        have := h (e i)
        rwa [show e (e i) = i from Equiv.swap_apply_self j' j i] at this
      · intro h i; exact h _
    rw [← hpre, (measurePreserving_signedPerm e d).measure_preimage
      ((measurableSet_axisCone j' b').inter hAm).nullMeasurableSet]
  -- the cones cover `A`, with null overlaps
  have hcover : A = ⋃ p ∈ (Finset.univ : Finset (Fin k × Bool)), axisCone p.1 p.2 ∩ A := by
    ext x
    simp only [Set.mem_iUnion, Set.mem_inter_iff, Finset.mem_univ, true_and, exists_prop]
    constructor
    · intro hx
      obtain ⟨j', b', h⟩ := exists_axisCone hk x
      exact ⟨(j', b'), h, hx⟩
    · rintro ⟨_, _, hx⟩; exact hx
  have hdisj : Set.Pairwise ((Finset.univ : Finset (Fin k × Bool)) : Set (Fin k × Bool))
      (AEDisjoint volume on fun p : Fin k × Bool => axisCone p.1 p.2 ∩ A) := by
    intro p _ q _ hpq
    refine measure_mono_null (fun x hx => ?_) (volume_hyperplane_zero hpq)
    exact axisCone_overlap_subset hx.1.1 hx.2.1
  conv_rhs => rw [hcover]
  rw [measure_biUnion_finset₀ hdisj (fun p _ =>
      ((measurableSet_axisCone p.1 p.2).inter hAm).nullMeasurableSet)]
  rw [Finset.sum_congr rfl (fun p _ => hsame p.1 p.2), Finset.sum_const, Finset.card_univ,
    Fintype.card_prod, Fintype.card_fin, Fintype.card_bool, nsmul_eq_mul]
  push_cast; ring

/-- The Euclidean ball is invariant under signed coordinate permutations. -/
theorem euclidBall_invariant (r : ℝ) (e : Equiv.Perm (Fin k)) (d : Fin k → Bool)
    (x : Fin k → ℝ) :
    signedPerm e d x ∈ {y : Fin k → ℝ | ∑ i, y i ^ 2 ≤ r} ↔
      x ∈ {y : Fin k → ℝ | ∑ i, y i ^ 2 ≤ r} := by
  simp only [Set.mem_setOf_eq, signedPerm, mul_pow]
  have : ∀ i, sgn (d i) ^ 2 = 1 := fun i => by rw [sq, sgn_mul_self]
  simp only [this, one_mul]
  rw [Equiv.sum_comp e (fun i => x i ^ 2)]

/-- The cube is invariant under signed coordinate permutations. -/
theorem cube_invariant (r : ℝ) (e : Equiv.Perm (Fin k)) (d : Fin k → Bool) (x : Fin k → ℝ) :
    signedPerm e d x ∈ {y : Fin k → ℝ | ∀ i, |y i| ≤ r} ↔
      x ∈ {y : Fin k → ℝ | ∀ i, |y i| ≤ r} := by
  simp only [Set.mem_setOf_eq, signedPerm, abs_sgn_mul]
  exact ⟨fun h i => by simpa using h (e.symm i), fun h i => h _⟩

/-- **The light cone fills exactly `1/(2k)` of all space-time directions:** it meets the
Euclidean unit ball of `k`-dimensional space-time in `1/(2k)` of its volume.  For Rule 30
(`k = 2`) this is `1/4` (`90°`); for a 2D rule (`k = 3`) it is `1/6` of the sphere. -/
theorem lightCone_ball_fraction (hk : 0 < k) :
    (2 * k : ENNReal) * volume (axisCone (⟨0, hk⟩ : Fin k) true ∩ {y | ∑ i, y i ^ 2 ≤ 1}) =
      volume {y : Fin k → ℝ | ∑ i, y i ^ 2 ≤ 1} :=
  axisCone_fraction hk _ (measurableSet_le (by fun_prop) (by fun_prop))
    (euclidBall_invariant 1) _ _

/-- The same fraction for the cube: the light cone cuts out one of `2k` congruent pyramids. -/
theorem lightCone_cube_fraction (hk : 0 < k) :
    (2 * k : ENNReal) * volume (axisCone (⟨0, hk⟩ : Fin k) true ∩ {y | ∀ i, |y i| ≤ 1}) =
      volume {y : Fin k → ℝ | ∀ i, |y i| ≤ 1} := by
  refine axisCone_fraction hk _ ?_ (cube_invariant 1) _ _
  have : {y : Fin k → ℝ | ∀ i, |y i| ≤ 1} = ⋂ i, {y : Fin k → ℝ | |y i| ≤ 1} := by
    ext; simp
  rw [this]
  exact MeasurableSet.iInter (fun i => measurableSet_le (by fun_prop) (by fun_prop))

end GLM.LatticeCone
