module

public import RequestProject.GLM.Rule30.TopMonomial

/-!
# Round 16: the top-degree part of `a(n)` is exactly one monomial, for every `n ≥ 3`

This closes the study's "Layer 4" (right-cone weight growth) in its strongest form.

* Round 8 (`center_anfDegree_eq`) proved `deg a(n)(0) = 2n − 1` and that `M_n = x_{2−n} ⋯ x_n`
  occurs.  Round 3 checked by computation that `M_n` is the **only** monomial of top degree for
  `3 ≤ n ≤ 6` (`topMonomial_unique_small`), and noted that at `n = 2` there are two (error E7).
* Here uniqueness is proved for **every** `n ≥ 3` (`topMonomial_unique`).

## The argument

A monomial of degree `2n − 1 ≥ 2` lies in the light cone `[−n, n]`.  It cannot contain `x_{−n}`
(cone separation: `a(n)(0)` is `x_{−n}` plus a function of the other cells).  The new step:

* **`anfCoeff_second_left_small`** — it cannot contain `x_{1−n}` either.  By the second-cell
  derivative formula (`evolve_update_second_left`, Round 8) the derivative of `a(n)(0)` in
  `x_{1−n}` (on rows with `x_{−n}` free) is `Σ_{s<n} (1 + a(s)(s + 2 − n))`, a sum of cells of
  earlier rows.  Each of these has ANF degree at most `2n − 3` (`anfDegree_le_cone`), so every
  monomial containing `x_{1−n}` has degree at most `2n − 2`.

That leaves `2n − 1` positions `[2 − n, n]` for `2n − 1` variables: the monomial is `M_n`.

## Weight growth

`weight (topMonomial n) = 2n − 2` was already known; with uniqueness it is now **the** weight of
the top-degree part of `a(n)(0)`, and it grows by exactly `+2` per step for every `n ≥ 3`
(`topDegree_weight_growth`).

As recorded since Round 3 (error E2, `map_properties_cannot_decide_periodicity`), these are
properties of the `n`-step map from all rows; they do not by themselves decide Problems 1 or 3
for the single-cell seed.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-- A function of the row that only reads the cells in `W` has ANF degree at most `|W|`. -/
theorem anfDegreeLE_of_dependsOnlyOn (f : Config → Bool) (W : Finset ℤ)
    (hf : DependsOnlyOn f W) : AnfDegreeLE f W.card := by
  intro S hS
  obtain ⟨j, hjS, hjW⟩ : ∃ j ∈ S, j ∉ W := by
    by_contra h
    push_neg at h
    exact absurd (card_le_card h) (by omega)
  refine anfCoeff_eq_zero_of_not_dependsOn f S hjS (fun x b => ?_)
  refine hf _ _ (fun i hi => ?_)
  rw [Function.update_of_ne (by rintro rfl; exact hjW hi)]

/-- **Crude degree bound for every row index:** `deg a(s)(c) ≤ 2s + 1`, because the light cone
has `2s + 1` cells.  (The sharp bound `2s − 1` for `s ≥ 2` is `anfDegree_le_at`.) -/
theorem anfDegree_le_cone (s : ℕ) (c : ℤ) : AnfDegreeLE (fun x => evolve x s c) (2 * s + 1) := by
  have h := anfDegreeLE_of_dependsOnlyOn _ _ (evolve_dependsOnlyOn s c)
  rwa [Int.card_Icc, show c + s + 1 - (c - s) = ((2 * s + 1 : ℕ) : ℤ) by push_cast; ring,
    Int.toNat_natCast] at h

/-- Coefficients of a constant vanish on non-empty monomials. -/
theorem coeffZ_const (a : ZMod 2) (S : Finset ℤ) (hS : S.Nonempty) :
    coeffZ (fun _ => a) S = 0 := by
  obtain ⟨j, hj⟩ := hS
  exact coeffZ_eq_zero_of_not_dep _ S hj (fun _ _ => rfl)

theorem coeffZ_sum (ι : Finset ℕ) (F : ℕ → Config → ZMod 2) (S : Finset ℤ) :
    coeffZ (fun x => ∑ s ∈ ι, F s x) S = ∑ s ∈ ι, coeffZ (F s) S := by
  unfold coeffZ
  rw [sum_comm]

/-- **No monomial of degree `≥ 2n − 1` contains the second-left cell `x_{1−n}`** (`n ≥ 3`). -/
theorem anfCoeff_second_left_small (n : ℕ) (hn : 3 ≤ n) (S : Finset ℤ)
    (hS : 2 * n - 1 ≤ S.card) (hj : 1 - (n : ℤ) ∈ S) :
    anfCoeff (fun x => evolve x n 0) S = 0 := by
  set j : ℤ := 1 - n
  set G : Config → ZMod 2 :=
    fun x => ∑ s ∈ range n, (1 + bz (evolve x s (-(n : ℤ) + s + 2)))
  -- the pairs `(T, T ∪ {j})` differ by `G T`
  have hpair : ∀ T ∈ (S.erase j).powerset,
      bz (evolve (ind T) n 0) + bz (evolve (ind (insert j T)) n 0) = G (ind T) := by
    intro T hT
    have hjT : j ∉ T := fun h => notMem_erase j S (mem_powerset.mp hT h)
    have hx : ind T (-(n : ℤ) + 1) = false := by
      simp only [ind, decide_eq_false_iff_not]
      intro h; apply hjT; convert h using 1; simp only [j]; ring
    have key := evolve_update_second_left (ind T) (-(n : ℤ)) hx n
    rw [show -(n : ℤ) + n = 0 by ring, show -(n : ℤ) + 1 = j by simp only [j]; ring] at key
    rw [ind_insert, key]
    simp only [G]
    linear_combination (bz (evolve (ind T) n 0)) * zmod2_add_self 1
  unfold anfCoeff
  rw [coeffZ_split _ S hj, sum_congr rfl hpair]
  change coeffZ G (S.erase j) = 0
  have hcard : (S.erase j).card = S.card - 1 := card_erase_of_mem hj
  simp only [G]
  rw [coeffZ_sum]
  refine sum_eq_zero (fun s hs => ?_)
  have hs' := mem_range.mp hs
  rw [show (fun x => 1 + bz (evolve x s (-(n : ℤ) + s + 2))) =
      (fun x => (fun _ => (1 : ZMod 2)) x + (fun x => bz (evolve x s (-(n : ℤ) + s + 2))) x)
      from rfl, coeffZ_add, coeffZ_const _ _ (card_pos.mp (by omega)), zero_add]
  change anfCoeff (fun x => evolve x s (-(n : ℤ) + s + 2)) (S.erase j) = 0
  by_cases hs2 : s + 2 ≤ n
  · exact anfDegree_le_cone s _ _ (by omega)
  · have : s = n - 1 := by omega
    subst this
    exact anfDegree_le_at (n - 1) (by omega) _ _ (by omega)

/-- **Uniqueness of the top monomial for every `n ≥ 3`.** Among all monomials of degree
`2n − 1`, exactly one occurs in the ANF of `a(n)(0)`, namely `M_n = x_{2−n} ⋯ x_n`.
(At `n = 2` this fails: there are two, see `topMonomial_unique_small`'s docstring and E7.) -/
theorem topMonomial_unique (n : ℕ) (hn : 3 ≤ n) (S : Finset ℤ) (hS : S.card = 2 * n - 1) :
    anfCoeff (fun x => evolve x n 0) S = 1 ↔ S = topMonomial n := by
  constructor
  · intro h1
    by_contra hne
    apply absurd h1
    rw [show anfCoeff (fun x => evolve x n 0) S = 0 from ?_]; · decide
    by_cases hsub : S ⊆ Icc (-(n : ℤ)) n
    · by_cases hl : -(n : ℤ) ∈ S
      · refine anfCoeff_eq_zero_of_permutive _ S hl (by omega) (fun x => ?_)
        have := evolve_flip_left_edge x n 0
        rwa [show (0 : ℤ) - n = -n by ring] at this
      · have hsub' : S ⊆ Icc (1 - (n : ℤ)) n := by
          intro j hj
          have := mem_Icc.mp (hsub hj)
          have hne : j ≠ -n := fun h => hl (h ▸ hj)
          exact mem_Icc.mpr ⟨by omega, this.2⟩
        by_cases hj : 1 - (n : ℤ) ∈ S
        · exact anfCoeff_second_left_small n hn S (by omega) hj
        · exfalso
          apply hne
          apply eq_of_subset_of_card_le
          · intro i hi
            have := mem_Icc.mp (hsub' hi)
            have hne : i ≠ 1 - n := fun h => hj (h ▸ hi)
            exact mem_Icc.mpr ⟨by omega, this.2⟩
          · rw [topMonomial_card n (by omega), hS]
    · obtain ⟨j, hj, hjn⟩ := not_subset.mp hsub
      refine anfCoeff_eq_zero_of_not_dependsOn _ S hj (fun x b => ?_)
      rw [mem_Icc, not_and_or, not_le, not_le] at hjn
      exact evolve_update_far _ _ _ _ _ (by omega)
  · rintro rfl
    exact topMonomialConjecture_holds n (by omega)

/-- **The same at every cell `c`:** the only top-degree monomial of `a(n)(c)` is
`x_{c+2−n} ⋯ x_{c+n}`. -/
theorem topMonomial_unique_at (n : ℕ) (hn : 3 ≤ n) (c : ℤ) (S : Finset ℤ)
    (hS : S.card = 2 * n - 1) :
    anfCoeff (fun x => evolve x n c) S = 1 ↔ S = (topMonomial n).image (· + c) := by
  have hS' : S = (S.image (· + -c)).image (· + c) := by
    rw [image_image]; ext j; simp
  have key := anfCoeff_evolve_shift n 0 c (S.image (· + -c))
  rw [zero_add] at key
  rw [hS', key, topMonomial_unique n hn _ (by rwa [card_image_of_injective _ (add_left_injective _)]),
    (image_injective (add_left_injective c)).eq_iff]

/-- **Right-cone weight growth, closed.** For every `n ≥ 3`, every top-degree monomial `S` of
`a(n)(0)` has weight `2n − 2`, and every top-degree monomial of `a(n + 1)(0)` has weight
exactly `2` more. -/
theorem topDegree_weight_growth (n : ℕ) (hn : 3 ≤ n)
    (S : Finset ℤ) (hS : S.card = 2 * n - 1) (hS1 : anfCoeff (fun x => evolve x n 0) S = 1)
    (S' : Finset ℤ) (hS' : S'.card = 2 * (n + 1) - 1)
    (hS'1 : anfCoeff (fun x => evolve x (n + 1) 0) S' = 1)
    (h : S.Nonempty) (h' : S'.Nonempty) :
    weight S h = 2 * n - 2 ∧ weight S' h' = weight S h + 2 := by
  obtain rfl := (topMonomial_unique n hn S hS).mp hS1
  obtain rfl := (topMonomial_unique (n + 1) (by omega) S' hS').mp hS'1
  rw [topMonomial_weight n (by omega), topMonomial_weight (n + 1) (by omega)]
  push_cast; constructor <;> ring

end GLM.Rule30
