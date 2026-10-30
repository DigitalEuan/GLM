module

public import RequestProject.GLM.Rule30.SpinSweep
public import RequestProject.GLM.Rule30.Observer
public import RequestProject.GLM.Rule30.LatticeConeFraction
public import RequestProject.GLM.Rule30.ReadAngle
public import RequestProject.GLM.Rule30.SeedBoundary

/-!
# Round 17: spinning on the lattice — which points are collected, and what the spin reveals

`SpinSweep.lean` spins the triangle and the pyramid continuously.  Cellular automata live on a
lattice, so this file asks what survives on the integer grid.

## 1. Lattice points collected by a full turn (exact)

* `lattice_collected_iff`: the integer point `(t, a, b)` is collected by the spinning triangle iff
  `a² + b² ≤ t²`, and by the spinning pyramid iff `a² + b² ≤ 2t²`.
* `collected_counts`: per time layer `t = 0…10` the spinning triangle collects
  `1, 5, 13, 29, 49, 81, 113, 149, 197, 253, 317` lattice points (Gauss's circle numbers), the
  spinning pyramid `1, 9, 25, 61, 101, 161, 225, 305, 405, 509, 633`, while the pyramid at rest holds
  `(2t+1)²`.  The ratios tend to `π/4` and `π/2` (areas of the round cones over the square).

## 2. Spins that keep the lattice (exact)

* `rot_lattice_iff`: a rotation `e^{iθ}` of the plane maps the integer grid to itself only for
  the four quarter turns `1, i, −1, −i`.  A spinning lattice object therefore has only four
  lattice "snapshots" per turn about the time axis.
* `pyramid_orbit` / `pyramid_spin_stabilizer` (any dimension): the lattice symmetries (signed
  coordinate permutations) carry the light-cone pyramid onto each of the `2k` axis pyramids,
  and those fixing the time axis leave it in place.  With `LatticeConeFraction` (the `2k`
  pyramids fill space with equal shares), "rotating the pyramid through all its lattice
  positions" collects all of space-time, `1/(2k)` per position: `1/6` for 2D rules.

## 3. Spinning Rule 30's plane: the spin angle is readable, except on the axis (exact)

Plant Rule 30's space-time diagram in the plane `b = 0` of the grid and turn it by `k` quarter
turns about the time axis (`spunDiagram`).  Then:

* `spun_half_turn_read`: after a half turn, the reference axis shows **Rule 86** (the mirror
  wheel); a full turn gives Rule 30 back (`spunDiagram_add_four`).
* `spun_axis_invariant`: the time axis — the **centre column** — reads the same at every angle.
  This is the geometric reason the centre column can never tell 30 from 86
  (`Observer.centre_column_class`).
* `rule30_spin_readable`: the turned diagram determines the number of quarter turns modulo `4`
  (the full angle): Rule 30's chirality is an absolute compass.
* `rule90_spin_halfturn_invisible`: for the mirror-symmetric Rule 90 a half turn changes
  nothing, so only the angle modulo `π` is readable.

* `rule30_row_not_mirror`: **from time `2` on, no row of Rule 30 is mirror-symmetric**; the
  asymmetry is always within two cells of the edges (cell `t−1` vs `1−t` for even `t`, cell
  `t−2` vs `2−t` for odd `t`).  Hence `spun_half_turn_visible_every_row`: the half turn is
  visible in every single row from `t = 2`, not only in the diagram as a whole.  Rows `0` and `1`
  are symmetric (`rule30_rows_zero_one_mirror`).

So the spin angle of the observer's plane — the user's "Read position/angle of the observer" —
is recoverable from Rule 30 off the axis, but invisible from the axis itself.
-/

@[expose] public section

namespace GLM.Spin

open Complex

/-! ## 1. Lattice points collected -/

/-- The integer point `(t, a, b)` as a space-time point. -/
noncomputable def latticePt (t a b : ℤ) : ℝ × ℂ := ((t : ℝ), (a : ℂ) + (b : ℂ) * I)

theorem norm_latticePt_sq (a b : ℤ) : ‖(a : ℂ) + (b : ℂ) * I‖ ^ 2 = (a : ℝ) ^ 2 + (b : ℝ) ^ 2 := by
  rw [Complex.sq_norm, Complex.normSq_apply]; simp; ring

/-- **Which lattice points a full turn collects.**  For `t ≥ 0`: the spinning triangle collects
`(t, a, b)` iff `a² + b² ≤ t²`, the spinning pyramid iff `a² + b² ≤ 2t²`. -/
theorem lattice_collected_iff (t a b : ℤ) (ht : 0 ≤ t) :
    (latticePt t a b ∈ ⋃ θ : ℝ, spin θ tri ↔ a ^ 2 + b ^ 2 ≤ t ^ 2) ∧
      (latticePt t a b ∈ ⋃ θ : ℝ, spin θ pyr ↔ a ^ 2 + b ^ 2 ≤ 2 * t ^ 2) := by
  rw [spin_sweep_triangle, spin_sweep_pyramid]
  simp only [roundCone, latticePt, Set.mem_setOf_eq, one_mul]
  have htR : (0 : ℝ) ≤ t := by exact_mod_cast ht
  have hn := norm_latticePt_sq a b
  have hz := norm_nonneg ((a : ℂ) + (b : ℂ) * I)
  constructor
  · rw [← @Int.cast_le ℝ]; push_cast
    rw [← hn]
    exact ⟨fun h => pow_le_pow_left₀ hz h 2, fun h => (pow_le_pow_iff_left₀ hz htR two_ne_zero).mp h⟩
  · rw [← @Int.cast_le ℝ]; push_cast
    rw [← hn]
    have hs : Real.sqrt 2 ^ 2 = 2 := Real.sq_sqrt (by norm_num)
    have hst : 0 ≤ Real.sqrt 2 * t := mul_nonneg (Real.sqrt_nonneg 2) htR
    constructor
    · intro h; have := pow_le_pow_left₀ hz h 2; rw [mul_pow, hs] at this; exact this
    · intro h
      refine (pow_le_pow_iff_left₀ hz hst two_ne_zero).mp ?_
      rw [mul_pow, hs]; exact h

/-- Number of lattice points of layer `t` with `a² + b² ≤ m·t²` (`m = 1`: triangle sweep;
`m = 2`: pyramid sweep).  The box `|a|, |b| ≤ 2t` contains all of them. -/
def collectedCount (m t : ℕ) : ℕ :=
  ((Finset.Icc (-(2 * t : ℤ)) (2 * t) ×ˢ Finset.Icc (-(2 * t : ℤ)) (2 * t)).filter
    (fun p : ℤ × ℤ => p.1 ^ 2 + p.2 ^ 2 ≤ m * (t : ℤ) ^ 2)).card

/-- **Lattice points collected per layer**, `t = 0…10`, compared with the resting pyramid's
`(2t+1)²`. -/
theorem collected_counts :
    (List.range 11).map (collectedCount 1) = [1, 5, 13, 29, 49, 81, 113, 149, 197, 253, 317] ∧
    (List.range 11).map (collectedCount 2) = [1, 9, 25, 61, 101, 161, 225, 305, 405, 509, 633] ∧
    (List.range 11).map (fun t => (2 * t + 1) ^ 2) =
      [1, 9, 25, 49, 81, 121, 169, 225, 289, 361, 441] := by
  refine ⟨by decide +kernel, by decide +kernel, by decide⟩

/-! ## 2. Spins that keep the lattice -/

/-- **Only the quarter turns keep the integer grid.**  `e^{iθ}` is a Gaussian integer (equivalently,
multiplication by it maps the grid `ℤ + ℤi` into itself) iff it is `1, i, −1` or `−i`. -/
theorem rot_lattice_iff (θ : ℝ) :
    (∃ a b : ℤ, rot θ = a + b * I) ↔ rot θ = 1 ∨ rot θ = I ∨ rot θ = -1 ∨ rot θ = -I := by
  constructor
  · rintro ⟨a, b, h⟩
    have hn : (a : ℝ) ^ 2 + (b : ℝ) ^ 2 = 1 := by
      rw [← norm_latticePt_sq, ← h, norm_rot, one_pow]
    have hz : a ^ 2 + b ^ 2 = 1 := by exact_mod_cast hn
    have ha : a ^ 2 ≤ 1 := by nlinarith
    have hb : b ^ 2 ≤ 1 := by nlinarith
    have ha' : -1 ≤ a ∧ a ≤ 1 := by constructor <;> nlinarith
    have hb' : -1 ≤ b ∧ b ≤ 1 := by constructor <;> nlinarith
    obtain ⟨ha1, ha2⟩ := ha'
    obtain ⟨hb1, hb2⟩ := hb'
    interval_cases a <;> interval_cases b <;> simp_all
  · rintro (h | h | h | h)
    · exact ⟨1, 0, by simp [h]⟩
    · exact ⟨0, 1, by simp [h]⟩
    · exact ⟨-1, 0, by simp [h]⟩
    · exact ⟨0, -1, by simp [h]⟩

end GLM.Spin

namespace GLM.LatticeCone

variable {k : ℕ}

/-- **The lattice symmetries carry the light-cone pyramid onto every axis pyramid.**  For each
axis `j` and direction `b` there is a signed coordinate permutation taking `axisCone j b` back
onto `axisCone j₀ true`. -/
theorem pyramid_orbit (j₀ j : Fin k) (b : Bool) :
    ∃ (e : Equiv.Perm (Fin k)) (d : Fin k → Bool),
      signedPerm e d ⁻¹' axisCone j b = axisCone j₀ true := by
  classical
  refine ⟨Equiv.swap j j₀, fun i => if i = j then b else true, ?_⟩
  ext x
  simp only [Set.mem_preimage, axisCone, Set.mem_setOf_eq, signedPerm, abs_sgn_mul]
  rw [if_pos trivial, show Equiv.swap j j₀ j = j₀ from Equiv.swap_apply_left j j₀, ← mul_assoc,
    sgn_mul_self, one_mul]
  simp only [sgn, if_true, one_mul]
  constructor
  · intro h i
    have := h (Equiv.swap j j₀ i)
    rwa [Equiv.swap_apply_self] at this
  · intro h i; exact h _

/-- **Spinning the pyramid about its own axis by lattice moves leaves it in place.**  A signed
coordinate permutation fixing the axis `j` (with sign `+`) maps `axisCone j b` onto itself. -/
theorem pyramid_spin_stabilizer (j : Fin k) (b : Bool) (e : Equiv.Perm (Fin k))
    (d : Fin k → Bool) (hej : e j = j) (hdj : d j = true) :
    signedPerm e d ⁻¹' axisCone j b = axisCone j b := by
  ext x
  simp only [Set.mem_preimage, axisCone, Set.mem_setOf_eq, signedPerm, abs_sgn_mul, hej, hdj]
  simp only [sgn, if_true, one_mul]
  constructor
  · intro h i
    have := h (e.symm i)
    rwa [Equiv.apply_symm_apply] at this
  · intro h i; exact h _

end GLM.LatticeCone

namespace GLM.Rule30

/-- The inverse quarter turn of the grid, `(a, b) ↦ (b, −a)`. -/
def qturnInv (p : ℤ × ℤ) : ℤ × ℤ := (p.2, -p.1)

/-- A 1D space-time diagram planted in the plane `b = 0` of the 2D grid. -/
def plant (D : ℕ → ℤ → Bool) (t : ℕ) (p : ℤ × ℤ) : Bool := if p.2 = 0 then D t p.1 else false

/-- The planted diagram turned by `k` quarter turns about the time axis. -/
def spunDiagram (D : ℕ → ℤ → Bool) (k : ℕ) (t : ℕ) (p : ℤ × ℤ) : Bool :=
  plant D t (qturnInv^[k] p)

theorem qturnInv_four (p : ℤ × ℤ) : qturnInv^[4] p = p := by
  simp [qturnInv, Function.iterate_succ]

/-- A full turn changes nothing. -/
theorem spunDiagram_add_four (D : ℕ → ℤ → Bool) (k : ℕ) :
    spunDiagram D (k + 4) = spunDiagram D k := by
  funext t p
  simp only [spunDiagram, Function.iterate_add_apply, qturnInv_four]

/-- Reading on the reference axis after `k` quarter turns. -/
def spunRead (D : ℕ → ℤ → Bool) (k : ℕ) (t : ℕ) (a : ℤ) : Bool := spunDiagram D k t (a, 0)

theorem spunRead_zero (D : ℕ → ℤ → Bool) (t : ℕ) (a : ℤ) : spunRead D 0 t a = D t a := by
  simp [spunRead, spunDiagram, plant]

theorem spunRead_two (D : ℕ → ℤ → Bool) (t : ℕ) (a : ℤ) : spunRead D 2 t a = D t (-a) := by
  simp [spunRead, spunDiagram, plant, qturnInv]

/-- After a quarter turn (either way) the reference axis meets the planted line only on the time
axis. -/
theorem spunRead_odd (D : ℕ → ℤ → Bool) (t : ℕ) (a : ℤ) :
    spunRead D 1 t a = (if a = 0 then D t 0 else false) ∧
      spunRead D 3 t a = (if a = 0 then D t 0 else false) := by
  by_cases ha : a = 0
  · subst ha; simp [spunRead, spunDiagram, plant, qturnInv]
  · simp [spunRead, spunDiagram, plant, qturnInv, ha]

/-- **The time axis (centre column) reads the same at every spin angle.** -/
theorem spun_axis_invariant (D : ℕ → ℤ → Bool) (k t : ℕ) :
    spunDiagram D k t (0, 0) = D t 0 := by
  have : qturnInv^[k] ((0 : ℤ), (0 : ℤ)) = (0, 0) := by
    induction k with
    | zero => rfl
    | succ k ih => rw [Function.iterate_succ_apply', ih]; simp [qturnInv]
  simp [spunDiagram, plant, this]

/-- **A half turn of Rule 30's plane shows Rule 86 on the reference axis.** -/
theorem spun_half_turn_read (t : ℕ) (a : ℤ) :
    spunRead (evolve seed) 2 t a = ecaEvolve 86 seed t a := by
  rw [spunRead_two, ← mirrorNum_thirty]
  have := ecaEvolve_mirror 30 seed t a
  rw [seed_mirror, ecaEvolve_thirty] at this
  exact this.symm

/-- …and the half-turned reading differs from the original one (already at column `1`). -/
theorem spun_half_turn_visible : spunRead (evolve seed) 2 ≠ spunRead (evolve seed) 0 := by
  intro h
  apply column_one_separates_mirror
  funext n
  have := congrFun (congrFun h n) 1
  rw [spun_half_turn_read, spunRead_zero] at this
  simp only [ecaColumn, this, ecaEvolve_thirty]

/-- Four probe cells at time `2`, one on each half-axis. -/
def spinSignature (D : ℕ → ℤ → Bool) (k : ℕ) : List Bool :=
  [spunDiagram D k 2 (1, 0), spunDiagram D k 2 (0, 1), spunDiagram D k 2 (-1, 0),
    spunDiagram D k 2 (0, -1)]

theorem spinSignature_thirty :
    (List.range 4).map (spinSignature (evolve seed)) =
      [[false, false, true, false], [false, false, false, true], [true, false, false, false],
        [false, true, false, false]] := by
  decide

/-- **Rule 30's turned plane determines the spin angle modulo a full turn.**  Different numbers of
quarter turns (mod 4) give different diagrams. -/
theorem rule30_spin_readable (k k' : ℕ) :
    spunDiagram (evolve seed) k = spunDiagram (evolve seed) k' ↔ k % 4 = k' % 4 := by
  have hmod : ∀ m, spunDiagram (evolve seed) m = spunDiagram (evolve seed) (m % 4) := by
    intro m
    conv_lhs => rw [← Nat.mod_add_div m 4]
    induction m / 4 with
    | zero => rfl
    | succ q ih => rw [Nat.mul_succ, ← add_assoc, spunDiagram_add_four, ih]
  rw [hmod k, hmod k']
  constructor
  · intro h
    have hs : spinSignature (evolve seed) (k % 4) = spinSignature (evolve seed) (k' % 4) := by
      simp only [spinSignature, h]
    have key : ∀ m < 4, ∀ m' < 4,
        spinSignature (evolve seed) m = spinSignature (evolve seed) m' → m = m' := by decide
    exact key _ (Nat.mod_lt k (by norm_num)) _ (Nat.mod_lt k' (by norm_num)) hs
  · intro h; rw [h]

/-- **For the mirror-symmetric Rule 90 a half turn is invisible**: only the angle modulo `π` can
be read. -/
theorem rule90_spin_halfturn_invisible (k : ℕ) :
    spunDiagram (ecaEvolve 90 seed) (k + 2) = spunDiagram (ecaEvolve 90 seed) k := by
  have hsym : ∀ t c, ecaEvolve 90 seed t (-c) = ecaEvolve 90 seed t c := fun t c =>
    ecaEvolve_symmetric (by decide) seed (fun j => by simp [seed]) t c
  funext t p
  rw [show k + 2 = 2 + k by ring]
  simp only [spunDiagram, Function.iterate_add_apply]
  generalize qturnInv^[k] p = q
  obtain ⟨a, b⟩ := q
  simp only [plant, Function.iterate_succ, Function.comp_apply, Function.iterate_zero, id_eq,
    qturnInv, neg_eq_zero]
  split_ifs <;> simp [hsym]

/-! ## Every row from time 2 shows the half turn -/

theorem rdiag_two_eq (t : ℕ) : rdiag 2 t = decide (t % 2 = 1) := by
  induction t with
  | zero => simp [rdiag_zero]
  | succ t ih =>
    rw [rdiag_succ, ih, show (2 : ℤ) - 1 = 1 by norm_num, show (2 : ℤ) - 2 = 0 by norm_num,
      rdiag_zero_eq_true, Bool.or_true]
    rcases Nat.mod_two_eq_zero_or_one t with h | h <;> simp [h, Nat.succ_mod_two_eq_one_iff]

theorem ldiag_one_eq (t : ℕ) (ht : 1 ≤ t) : ldiag 1 t = true := by
  obtain ⟨s, rfl⟩ : ∃ s, t = s + 1 := ⟨t - 1, by omega⟩
  rw [ldiag_succ, show (1 : ℤ) - 2 = -1 by norm_num, show (1 : ℤ) - 1 = 0 by norm_num,
    ldiag_neg (by norm_num), ldiag_zero]; rfl

theorem ldiag_two_eq (t : ℕ) (ht : 2 ≤ t) : ldiag 2 t = false := by
  obtain ⟨s, rfl⟩ : ∃ s, t = s + 1 := ⟨t - 1, by omega⟩
  rw [ldiag_succ, show (2 : ℤ) - 2 = 0 by norm_num, show (2 : ℤ) - 1 = 1 by norm_num,
    ldiag_zero, ldiag_one_eq s (by omega)]; rfl

/-- **No row of Rule 30 from time `2` on is mirror-symmetric**, and the asymmetry sits within two
cells of the edges. -/
theorem rule30_row_not_mirror (t : ℕ) (ht : 2 ≤ t) :
    (t % 2 = 0 → evolve seed t (-((t : ℤ) - 1)) ≠ evolve seed t ((t : ℤ) - 1)) ∧
      (t % 2 = 1 → evolve seed t (-((t : ℤ) - 2)) ≠ evolve seed t ((t : ℤ) - 2)) := by
  have hl1 := ldiag_one_eq t (by omega)
  have hl2 := ldiag_two_eq t ht
  have hr1 := rdiag_one_eq t
  have hr2 := rdiag_two_eq t
  simp only [ldiag, rdiag] at hl1 hl2 hr1 hr2
  refine ⟨fun h => ?_, fun h => ?_⟩
  · rw [show -((t : ℤ) - 1) = 1 - t by ring, hl1, hr1]; simp [h]
  · rw [show -((t : ℤ) - 2) = 2 - t by ring, hl2, hr2]; simp [h]

/-- Rows `0` and `1` are mirror-symmetric. -/
theorem rule30_rows_zero_one_mirror (c : ℤ) :
    evolve seed 0 (-c) = evolve seed 0 c ∧ evolve seed 1 (-c) = evolve seed 1 c := by
  refine ⟨by simp [evolve, seed], ?_⟩
  rcases le_or_gt |c| 1 with h | h
  · have : c = -1 ∨ c = 0 ∨ c = 1 := by rcases abs_le.mp h with ⟨h1, h2⟩; omega
    rcases this with rfl | rfl | rfl <;> decide
  · rw [evolve_seed_outside 1 c (by exact_mod_cast h),
      evolve_seed_outside 1 (-c) (by rw [abs_neg]; exact_mod_cast h)]

/-- **The half turn is visible in every row from `t = 2`.** -/
theorem spun_half_turn_visible_every_row (t : ℕ) (ht : 2 ≤ t) :
    spunRead (evolve seed) 2 t ≠ spunRead (evolve seed) 0 t := by
  intro h
  rcases Nat.mod_two_eq_zero_or_one t with he | ho
  · apply (rule30_row_not_mirror t ht).1 he
    have := congrFun h ((t : ℤ) - 1)
    rwa [spunRead_two, spunRead_zero] at this
  · apply (rule30_row_not_mirror t ht).2 ho
    have := congrFun h ((t : ℤ) - 2)
    rwa [spunRead_two, spunRead_zero] at this

end GLM.Rule30
