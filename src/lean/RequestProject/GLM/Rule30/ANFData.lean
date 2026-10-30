import RequestProject.GLM.Rule30.ANF

/-!
# ANF of Rule 30: machine-checked small cases

(This file is deliberately not a `module`: it evaluates the Möbius transform with
`native_decide`, which needs the compiled code of the definitions.)

* `anfCoeff_topMonomial_small` : `anfCoeff a(n)(0) M_n = 1` for `2 ≤ n ≤ 7`.
* `anfDegree_eq_small`         : hence `deg a(n)(0) = 2n − 1` exactly for `2 ≤ n ≤ 7`.
* `anfDegree_one`              : `deg a(1)(0) = 2`.
* `topMonomial_unique_small`   : for `3 ≤ n ≤ 6`, `M_n` is the unique monomial of top degree.
-/

namespace GLM.Rule30

open Finset

/-! ## Machine-checked small cases -/

/-- `anfCoeff a(n)(0) M_n = 1` for `2 ≤ n ≤ 7` (direct evaluation of the Möbius transform). -/
theorem anfCoeff_topMonomial_small :
    ∀ n ∈ Icc (2 : ℕ) 7, anfCoeff (fun x => evolve x n 0) (topMonomial n) = 1 := by
  native_decide

/-- **`deg a(n)(0) = 2n − 1` for `2 ≤ n ≤ 7`.** -/
theorem anfDegree_eq_small (n : ℕ) (hn : n ∈ Icc (2 : ℕ) 7) :
    AnfDegreeEq (fun x => evolve x n 0) (2 * n - 1) :=
  ⟨center_anfDegree_le n (mem_Icc.mp hn).1, topMonomial n,
    topMonomial_card n (mem_Icc.mp hn).1, anfCoeff_topMonomial_small n hn⟩

/-- `n = 1` is special: `a(1)(0) = x_{-1} + x_0 + x_1 + x_0 x_1` has degree `2`. -/
theorem anfDegree_one : AnfDegreeEq (fun x => evolve x 1 0) 2 := by
  refine ⟨fun S hS => ?_, {0, 1}, by decide, by native_decide⟩
  by_cases hsub : S ⊆ Icc (-1 : ℤ) 1
  · by_cases hl : (-1 : ℤ) ∈ S
    · refine anfCoeff_eq_zero_of_permutive _ S hl (by omega) (fun x => ?_)
      have := evolve_flip_left_edge x 1 0
      rwa [show (0 : ℤ) - (1 : ℕ) = -1 by norm_num] at this
    · exfalso
      have : S ⊆ Icc (0 : ℤ) 1 := fun j hj => by
        have := mem_Icc.mp (hsub hj)
        have hne : j ≠ -1 := fun h => hl (h ▸ hj)
        exact mem_Icc.mpr ⟨by omega, this.2⟩
      have := card_le_card this
      rw [Int.card_Icc] at this; omega
  · obtain ⟨j, hj, hjn⟩ := not_subset.mp hsub
    refine anfCoeff_eq_zero_of_not_dependsOn _ S hj (fun x b => ?_)
    rw [mem_Icc, not_and_or, not_le, not_le] at hjn
    exact evolve_update_far _ _ _ _ _ (by push_cast; omega)

/-- Computation: for `3 ≤ n ≤ 6`, among the `2n − 1`-subsets of `[-n+1, n]`, only `M_n`
has coefficient `1`. -/
theorem erase_coeff_small :
    ∀ n ∈ Icc (3 : ℕ) 6, ∀ k ∈ Icc (2 - (n : ℤ)) n,
      anfCoeff (fun x => evolve x n 0) ((Icc (1 - (n : ℤ)) n).erase k) = 0 := by
  native_decide

/-- **Uniqueness of the top monomial for `3 ≤ n ≤ 6`.** -/
theorem topMonomial_unique_small (n : ℕ) (hn : n ∈ Icc (3 : ℕ) 6) (S : Finset ℤ)
    (hS : S.card = 2 * n - 1) :
    anfCoeff (fun x => evolve x n 0) S = 1 ↔ S = topMonomial n := by
  have hn' := mem_Icc.mp hn
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
        -- `S` misses exactly one element `k` of `[1-n, n]`
        obtain ⟨k, hk, hkS⟩ : ∃ k ∈ Icc (1 - (n : ℤ)) n, k ∉ S := by
          by_contra hall
          push_neg at hall
          have := card_le_card hall
          rw [Int.card_Icc] at this; omega
        have hSe : S = (Icc (1 - (n : ℤ)) n).erase k := by
          apply eq_of_subset_of_card_le
          · intro j hj; exact mem_erase.mpr ⟨fun h => hkS (h ▸ hj), hsub' hj⟩
          · rw [card_erase_of_mem hk, Int.card_Icc]; omega
        have hk' : k ≠ 1 - n := by
          rintro rfl; apply hne; rw [hSe]; ext j
          simp only [mem_erase, mem_Icc, topMonomial]; omega
        rw [hSe]
        exact erase_coeff_small n hn k (mem_Icc.mpr ⟨by
          have := mem_Icc.mp hk; omega, (mem_Icc.mp hk).2⟩)
    · obtain ⟨j, hj, hjn⟩ := not_subset.mp hsub
      refine anfCoeff_eq_zero_of_not_dependsOn _ S hj (fun x b => ?_)
      rw [mem_Icc, not_and_or, not_le, not_le] at hjn
      exact evolve_update_far _ _ _ _ _ (by omega)
  · rintro rfl
    exact anfCoeff_topMonomial_small n (mem_Icc.mpr ⟨by omega, by omega⟩)

end GLM.Rule30
