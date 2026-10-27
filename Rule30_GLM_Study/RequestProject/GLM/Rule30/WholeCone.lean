module

public import RequestProject.GLM.Rule30.TopMonomial
public import RequestProject.GLM.Rule30.MachineModel

/-!
# Whole-cone dependence holds for every `t`

Round 9.  `WholeConeDependence` (`MachineModel.lean`) says that the centre cell `a(t)(0)`,
read as a Boolean function of the `2t + 1` cells `x_{-t}, …, x_t` of its light cone, depends
on **every** one of them.  Until this round it was checked only for `t ≤ 6`
(`MachineModelData.wholeCone_le_6`).  Here it is proved for all `t`
(`wholeConeDependence_holds`), from three ingredients:

* `x_{-t}` (left edge): cone separation (`centreWindow_essential_left`).
* `x_{1-t}` (second cell): the second-cell derivative formula `evolve_update_second_left`.
  On the all-white row, turning on `x_{1-t}` changes `a(t)(0)` by `t mod 2`; on the row with a
  single black cell at `x_t`, by `(t - 1) mod 2`.  One of the two is odd.
* `x_j`, `2 - t ≤ j ≤ t`: the top monomial `x_{2-t} ⋯ x_t` has coefficient `1` in the ANF
  (`topMonomialConjecture_holds`), and a monomial containing `x_j` can only occur if the function
  depends on `x_j` (`anfCoeff_eq_zero_of_not_dependsOn`).

Consequence (`circuit_size_ge`): every Boolean circuit (fan-in ≤ 2) computing the light-cone map
`(x_{-t}, …, x_t) ↦ a(t)(0)` has at least `t` gates, for every `t`.

This is a statement about the `n`-step **map**, not about the specific single-cell sequence;
by error E2 / `map_properties_cannot_decide_periodicity` it does not by itself bear on the prize
problems (Problem 3 asks about computing `n ↦ a(n)` from the `log n` bits of `n`).
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-- Transfer a witness row to the light-cone map: if flipping `x_j` changes `a(t)(0)` for
some row `x`, then the light-cone map depends essentially on input `j`. -/
theorem essential_of_row (t : ℕ) (j : ℤ) (h : -(t : ℤ) ≤ j ∧ j ≤ t) (x : Config)
    (hx : evolve (flipAt x j) t 0 ≠ evolve x t 0) :
    Essential (centreWindow t) (windowIdx t j h) := by
  refine ⟨fun i => x ((i : ℕ) - (t : ℤ)), ?_⟩
  unfold centreWindow
  rw [windowRow_flip]
  have hagree : ∀ k, (0 : ℤ) - t ≤ k → k ≤ 0 + t →
      windowRow t (fun i : Fin (2 * t + 1) => x ((i : ℕ) - (t : ℤ))) k = x k := by
    intro k h1 h2
    have hk : -(t : ℤ) ≤ k ∧ k ≤ t := ⟨by omega, by omega⟩
    simp only [windowRow, dif_pos hk]
    congr 1
    omega
  rw [evolve_congr _ (flipAt x j) t 0, evolve_congr _ x t 0 hagree]
  · exact hx
  · intro k h1 h2
    simp only [flipAt]
    by_cases hk : k = j
    · subst hk; simp [hagree k h1 h2]
    · rw [Function.update_of_ne hk, Function.update_of_ne hk, hagree k h1 h2]

/-- If `a(t)(0)` ignores flips of `x_j`, it ignores every update of `x_j`. -/
theorem update_invariant_of_flip_invariant (t : ℕ) (j : ℤ)
    (h : ∀ x : Config, evolve (flipAt x j) t 0 = evolve x t 0) (x : Config) (b : Bool) :
    evolve (Function.update x j b) t 0 = evolve x t 0 := by
  by_cases hb : b = x j
  · subst hb; simp
  · have : b = !x j := by cases b <;> cases hx : x j <;> simp_all
    subst this
    exact h x

/-- **Interior inputs** `2 - t ≤ j ≤ t` are essential (from the top monomial). -/
theorem essential_interior (t : ℕ) (ht : 2 ≤ t) (j : ℤ) (hj1 : 2 - (t : ℤ) ≤ j) (hj2 : j ≤ t) :
    ∃ x : Config, evolve (flipAt x j) t 0 ≠ evolve x t 0 := by
  by_contra hcon
  push_neg at hcon
  have h0 := anfCoeff_eq_zero_of_not_dependsOn (fun x => evolve x t 0) (topMonomial t)
    (j := j) (mem_Icc.mpr ⟨hj1, hj2⟩) (update_invariant_of_flip_invariant t j hcon)
  rw [topMonomialConjecture_holds t ht] at h0
  exact one_ne_zero h0

/-- The single black cell at position `d`. -/
def cellAt (d : ℤ) : Config := fun c => decide (c = d)

/-- **The second input** `x_{1-t}` is essential, for every `t ≥ 1`. -/
theorem essential_second (t : ℕ) (ht : 1 ≤ t) :
    ∃ x : Config, evolve (flipAt x (1 - t)) t 0 ≠ evolve x t 0 := by
  have hpos : (-(t : ℤ)) + t = 0 := by ring
  rcases Nat.even_or_odd t with he | ho
  · -- `t` even: the row with a single black cell at `t`
    refine ⟨cellAt t, ?_⟩
    have hx : cellAt (t : ℤ) (-(t : ℤ) + 1) = false := by simp [cellAt]; omega
    have key := evolve_update_second_left (cellAt t) (-(t : ℤ)) hx t
    have hflip : flipAt (cellAt (t : ℤ)) (1 - t) =
        Function.update (cellAt t) (-(t : ℤ) + 1) true := by
      simp only [flipAt, show (1 : ℤ) - t = -(t : ℤ) + 1 by ring, hx, Bool.not_false]
    rw [hflip]
    rw [hpos] at key
    -- the diagonal: white except at the last step
    obtain ⟨u, rfl⟩ : ∃ u, t = u + 1 := ⟨t - 1, by omega⟩
    rw [sum_range_succ] at key
    have hwhite : ∀ s ∈ range u,
        (1 + bz (evolve (cellAt ((u + 1 : ℕ) : ℤ)) s (-((u + 1 : ℕ) : ℤ) + s + 2)) : ZMod 2) = 1 := by
      intro s hs
      rw [mem_range] at hs
      rw [evolve_congr (cellAt _) (fun _ => false) s _ (fun k h1 h2 => by
        simp only [cellAt, decide_eq_false_iff_not]; push_cast at *; omega), evolve_false]
      simp [bz]
    have hlast : evolve (cellAt ((u + 1 : ℕ) : ℤ)) u (-((u + 1 : ℕ) : ℤ) + u + 2) = true := by
      have hs := evolve_shift seed (-((u + 1 : ℕ) : ℤ)) u (-((u + 1 : ℕ) : ℤ) + u + 2)
      have hcell : (fun j => seed (j + -((u + 1 : ℕ) : ℤ))) = cellAt ((u + 1 : ℕ) : ℤ) := by
        funext j; simp only [seed, cellAt]; congr 1; apply propext; omega
      rw [hcell] at hs
      rw [hs, show -((u + 1 : ℕ) : ℤ) + u + 2 + -((u + 1 : ℕ) : ℤ) = -(u : ℤ) by push_cast; ring]
      exact evolve_seed_left_edge u
    rw [sum_congr rfl hwhite, hlast] at key
    simp only [sum_const, card_range, nsmul_eq_mul, mul_one] at key
    have hu : (u : ZMod 2) = 1 := by
      rw [ZMod.natCast_eq_one_iff_odd]
      obtain ⟨k, hk⟩ := he
      exact ⟨k - 1, by omega⟩
    have hb : bz true = 1 := rfl
    rw [hu, hb] at key
    intro hcontra
    rw [hcontra] at key
    have h3 : (1 + (1 + 1) : ZMod 2) = 1 := by decide
    rw [h3] at key
    simp at key
  · -- `t` odd: the all-white row
    refine ⟨fun _ => false, ?_⟩
    have hx : (fun _ : ℤ => false) (-(t : ℤ) + 1) = false := rfl
    have key := evolve_update_second_left (fun _ => false) (-(t : ℤ)) hx t
    have hflip : flipAt (fun _ : ℤ => false) (1 - t) =
        Function.update (fun _ => false) (-(t : ℤ) + 1) true := by
      simp only [flipAt, show (1 : ℤ) - t = -(t : ℤ) + 1 by ring, Bool.not_false]
    rw [hflip]
    rw [hpos] at key
    simp only [evolve_false] at key
    have h1 : ∀ s ∈ range t, (1 + bz false : ZMod 2) = 1 := fun _ _ => by simp [bz]
    rw [sum_congr rfl h1] at key
    simp only [sum_const, card_range, nsmul_eq_mul, mul_one] at key
    rw [(ZMod.natCast_eq_one_iff_odd).mpr ho] at key
    rw [evolve_false]
    intro hcontra
    rw [hcontra] at key
    simp [bz] at key

/-- **Whole-cone dependence holds for every `t`** (proved; previously checked for `t ≤ 6`):
the centre cell after `t` steps depends essentially on every one of the `2t + 1` cells of its
light cone. -/
theorem wholeConeDependence_holds : WholeConeDependence := by
  intro t i
  -- write the index as a position `j ∈ [-t, t]`
  set j : ℤ := (i : ℕ) - (t : ℤ) with hjdef
  have hj : -(t : ℤ) ≤ j ∧ j ≤ t := ⟨by omega, by have := i.isLt; omega⟩
  have hi : i = windowIdx t j hj := by
    ext; simp only [windowIdx, hjdef]; omega
  rw [hi]
  by_cases hleft : j = -(t : ℤ)
  · have := centreWindow_essential_left t
    convert this using 2
  by_cases hsecond : j = 1 - t
  · obtain ⟨x, hx⟩ := essential_second t (by omega)
    rw [← hsecond] at hx
    exact essential_of_row t _ hj x hx
  by_cases hright : j = t
  · have := centreWindow_essential_right t
    convert this using 2
  · have ht : 2 ≤ t := by omega
    obtain ⟨x, hx⟩ := essential_interior t ht j (by omega) hj.2
    exact essential_of_row t j hj x hx

/-- **Unconditional circuit lower bound for the light-cone map:** for every `t`, every circuit
computing `(x_{-t}, …, x_t) ↦ a(t)(0)` has at least `t` gates. -/
theorem circuit_size_ge (t : ℕ) (C : Circuit (2 * t + 1)) (hC : C.Computes (centreWindow t)) :
    t ≤ C.size :=
  circuit_size_ge_of_wholeCone wholeConeDependence_holds t C hC

/-- **Audit (error E2 again).** Whole-cone dependence is a property of the `t`-step map, and it
holds while the all-white row has a periodic centre column; so it cannot by itself imply
Problem 1 (compare `degree_facts_compatible_with_periodicity`). -/
theorem wholeCone_compatible_with_periodicity :
    WholeConeDependence ∧ EventuallyPeriodic (fun n => evolve (fun _ => false) n 0) :=
  ⟨wholeConeDependence_holds, white_centre_periodic⟩

end GLM.Rule30
