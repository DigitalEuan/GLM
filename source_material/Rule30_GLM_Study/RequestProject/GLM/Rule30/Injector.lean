module

public import RequestProject.GLM.Rule30.WeightGrowth
public import RequestProject.GLM.Rule30.Prizes
public import RequestProject.GLM.Rule30.ElementaryCA

/-!
# Round 18: the `C·R` injector, the odd parity lock on `M_{n+1}`, and why it cannot reach the seed

Rule 30 over `GF(2)` is `L + C + R + C·R`: a linear part plus one nonlinear "injector" `C·R`.
The study's target was: *the injector forces an odd number of surviving terms for `M_{n+1}`,
preventing the lower-degree cancellation wall from collapsing the sequence into periodicity.*
This file proves the first half exactly and shows, also exactly, that the second half does not
follow.

## 1. Product formula (`coeffZ_mul`)
The ANF coefficient of `x^U` in a product `F·G` is `Σ_{S ∪ S' = U} F̂(S) Ġ(S')` over `GF(2)`.

## 2. The injector carries the top degree
* `anfCoeff_succ_split`: coefficient of `a(n+1)(c)` = linear part + injector pair sum.
* `linear_part_below_wall`, `anfCoeff_succ_high_eq_injector`: for `n ≥ 2`, every coefficient of
  degree `≥ 2n` comes from the injector alone.
* `injectorPairs_card_odd` (**the target**): for every `n ≥ 1`, the number of pairs `(S, S')`
  of monomials of `a(n)(0)` and `a(n)(1)` with `S ∪ S' = M_{n+1}` is **odd**.
  `injectorPairs_card_small` (in `InjectorData.lean`): the counts are `3, 3, 5, 3` for `n = 1..4`, so this is a real
  cancellation (a parity lock), not a single surviving term.

## 3. Where Problem 1 lives
* `seed_eq_linearCoeff`: the seed's whole space-time diagram is the **degree-one slice** of the
  ANF: `a(n)(c)` on the seed = coefficient of `x_0` in `a(n)(c)`.
* `problem1_iff_linearCoeff`: Problem 1 is a statement about that one coefficient per step.
* `linearCoeff_autonomous`: the degree-one slice evolves by Rule 30 itself, closed: nothing of
  degree `≥ 2` enters it.
* `pairSum_singleton`: on that slice the injector is a single pair (plain `C·R`), in contrast with
  the multi-pair parity lock at the top.

## 4. Decoupling
* `top_structure_cannot_fix_seed`: for any target bit sequence there is a family with **all**
  ANF coefficients except that of `x_0` equal to Rule 30's, whose seed column is that sequence.
* `injector_lock_compatible_with_periodicity`: in particular the odd parity lock (and every other
  fact about degree `≥ 2`) is compatible with a periodic seed column.  The lock cannot by itself
  prevent periodicity; a proof of Problem 1 must use information about the degree-one slice.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-! ## 1. The product formula for ANF coefficients -/

/-- Möbius inversion: the value at the row `1_T` is the sum of the coefficients below `T`. -/
theorem coeffZ_inversion (F : Config → ZMod 2) (T : Finset ℤ) :
    ∑ S ∈ T.powerset, coeffZ F S = F (ind T) :=
  mobius_double_sum T (fun R => F (ind R))

/-- The `GF(2)` sum over all pairs `(S, S')` of subsets of `U` whose union is `U`. -/
def pairSum (f g : Finset ℤ → ZMod 2) (U : Finset ℤ) : ZMod 2 :=
  ∑ S ∈ U.powerset, ∑ S' ∈ U.powerset, if S ∪ S' = U then f S * g S' else 0

theorem sum_pairs_eq_sum_pairSum (f g : Finset ℤ → ZMod 2) (T : Finset ℤ) :
    (∑ S ∈ T.powerset, f S) * (∑ S' ∈ T.powerset, g S') =
      ∑ V ∈ T.powerset, pairSum f g V := by
  rw [sum_mul_sum]
  have h1 : ∀ S ∈ T.powerset, ∀ S' ∈ T.powerset, f S * g S' =
      ∑ V ∈ T.powerset, if S ∪ S' = V then f S * g S' else 0 := by
    intro S hS S' hS'
    rw [sum_ite_eq]
    rw [if_pos (mem_powerset.mpr (union_subset (mem_powerset.mp hS) (mem_powerset.mp hS')))]
  rw [sum_congr rfl (fun S hS => sum_congr rfl (fun S' hS' => h1 S hS S' hS'))]
  rw [sum_congr rfl (fun S _ => sum_comm), sum_comm]
  refine sum_congr rfl (fun V hV => ?_)
  have hVT := mem_powerset.mp hV
  unfold pairSum
  symm
  rw [sum_subset (powerset_mono.mpr hVT)]
  · refine sum_congr rfl (fun S _ => ?_)
    rw [sum_subset (powerset_mono.mpr hVT)]
    intro S' _ hS'
    rw [if_neg]
    intro h
    exact hS' (mem_powerset.mpr (h ▸ subset_union_right))
  · intro S _ hS
    refine sum_eq_zero (fun S' _ => ?_)
    rw [if_neg]
    intro h
    exact hS (mem_powerset.mpr (h ▸ subset_union_left))

/-- **Product formula.** The coefficient of `x^U` in `F · G` is the sum, over pairs of
monomials `x^S` of `F` and `x^{S'}` of `G` with `S ∪ S' = U`, of the products of coefficients. -/
theorem coeffZ_mul (F G : Config → ZMod 2) (U : Finset ℤ) :
    coeffZ (fun x => F x * G x) U = pairSum (coeffZ F) (coeffZ G) U := by
  have h : ∀ T ∈ U.powerset, F (ind T) * G (ind T) =
      ∑ V ∈ T.powerset, pairSum (coeffZ F) (coeffZ G) V := by
    intro T _
    rw [← coeffZ_inversion F T, ← coeffZ_inversion G T, sum_pairs_eq_sum_pairSum]
  unfold coeffZ
  rw [sum_congr rfl h]
  exact mobius_double_sum U _

/-! ## 2. The injector carries the top degree -/

theorem bz_rule30 (L C R : Bool) : bz (rule30 L C R) = bz L + bz C + bz R + bz C * bz R :=
  rule30_zmod L C R

/-- **One step, coefficient by coefficient.** The ANF of `a(n+1)(c)` is the linear part
`a(n)(c-1) + a(n)(c) + a(n)(c+1)` plus the injector `a(n)(c) · a(n)(c+1)`, whose coefficients
are given by the product formula. -/
theorem anfCoeff_succ_split (n : ℕ) (c : ℤ) (U : Finset ℤ) :
    anfCoeff (fun x => evolve x (n + 1) c) U =
      anfCoeff (fun x => evolve x n (c - 1)) U + anfCoeff (fun x => evolve x n c) U +
        anfCoeff (fun x => evolve x n (c + 1)) U +
        pairSum (anfCoeff (fun x => evolve x n c)) (anfCoeff (fun x => evolve x n (c + 1))) U := by
  unfold anfCoeff
  rw [← coeffZ_mul, ← coeffZ_add, ← coeffZ_add, ← coeffZ_add]
  congr 1
  funext x
  simp only
  rw [evolve_succ, bz_rule30]

/-- **The linear part sits below the wall.** For `n ≥ 2` the three linear terms have degree at
most `2n − 1`, so they contribute nothing to any monomial of degree `≥ 2n`. -/
theorem linear_part_below_wall (n : ℕ) (hn : 2 ≤ n) (c : ℤ) (U : Finset ℤ)
    (hU : 2 * n ≤ U.card) :
    anfCoeff (fun x => evolve x n (c - 1)) U + anfCoeff (fun x => evolve x n c) U +
      anfCoeff (fun x => evolve x n (c + 1)) U = 0 := by
  rw [anfDegree_le_at n hn (c - 1) U (by omega), anfDegree_le_at n hn c U (by omega),
    anfDegree_le_at n hn (c + 1) U (by omega)]
  simp

/-- **Every coefficient of degree `≥ 2n` of `a(n+1)(c)` is produced by the injector alone.** -/
theorem anfCoeff_succ_high_eq_injector (n : ℕ) (hn : 2 ≤ n) (c : ℤ) (U : Finset ℤ)
    (hU : 2 * n ≤ U.card) :
    anfCoeff (fun x => evolve x (n + 1) c) U =
      pairSum (anfCoeff (fun x => evolve x n c)) (anfCoeff (fun x => evolve x n (c + 1))) U := by
  rw [anfCoeff_succ_split, linear_part_below_wall n hn c U hU, zero_add]

/-- For the specific monomial `M_{n+1}` the linear part vanishes already for every `n ≥ 1`:
`a(n)(-1)` and `a(n)(0)` do not see `x_{n+1}`, and `a(n)(1)` is permutive in its left edge
`x_{1-n}`. -/
theorem linear_part_topMonomial (n : ℕ) (hn : 1 ≤ n) :
    anfCoeff (fun x => evolve x n (0 - 1)) (topMonomial (n + 1)) +
      anfCoeff (fun x => evolve x n 0) (topMonomial (n + 1)) +
      anfCoeff (fun x => evolve x n (0 + 1)) (topMonomial (n + 1)) = 0 := by
  have hmem : ((n : ℤ) + 1) ∈ topMonomial (n + 1) := by
    simp only [topMonomial, mem_Icc]; push_cast; omega
  have h1 : anfCoeff (fun x => evolve x n (0 - 1)) (topMonomial (n + 1)) = 0 :=
    anfCoeff_eq_zero_of_not_dependsOn _ _ hmem
      (fun x b => evolve_update_far _ _ _ _ _ (by omega))
  have h2 : anfCoeff (fun x => evolve x n 0) (topMonomial (n + 1)) = 0 :=
    anfCoeff_eq_zero_of_not_dependsOn _ _ hmem
      (fun x b => evolve_update_far _ _ _ _ _ (by omega))
  have hl : (0 + 1 : ℤ) - n ∈ topMonomial (n + 1) := by
    simp only [topMonomial, mem_Icc]; push_cast; omega
  have h3 : anfCoeff (fun x => evolve x n (0 + 1)) (topMonomial (n + 1)) = 0 :=
    anfCoeff_eq_zero_of_permutive _ _ hl (by rw [topMonomial_card _ (by omega)]; omega)
      (fun x => evolve_flip_left_edge x n _)
  rw [h1, h2, h3]; simp

/-- **The injector forces the top monomial.** For every `n ≥ 1`, the pair sum of the injector
`a(n)(0) · a(n)(1)` at `M_{n+1}` is `1`. -/
theorem injector_pairSum_topMonomial (n : ℕ) (hn : 1 ≤ n) :
    pairSum (anfCoeff (fun x => evolve x n 0)) (anfCoeff (fun x => evolve x n 1))
      (topMonomial (n + 1)) = 1 := by
  have h := anfCoeff_succ_split n 0 (topMonomial (n + 1))
  rw [linear_part_topMonomial n hn, zero_add, topMonomialConjecture_holds (n + 1) (by omega),
    zero_add] at h
  exact h.symm

/-- The **surviving injector pairs** for `M_{n+1}`: pairs `(S, S')` with `x^S` a monomial of
`a(n)(0)`, `x^{S'}` a monomial of `a(n)(1)`, and `S ∪ S' = M_{n+1}`. -/
def injectorPairs (n : ℕ) : Finset (Finset ℤ × Finset ℤ) :=
  ((topMonomial (n + 1)).powerset ×ˢ (topMonomial (n + 1)).powerset).filter (fun p =>
    p.1 ∪ p.2 = topMonomial (n + 1) ∧ anfCoeff (fun x => evolve x n 0) p.1 = 1 ∧
      anfCoeff (fun x => evolve x n 1) p.2 = 1)

theorem zmod2_cases (a : ZMod 2) : a = 0 ∨ a = 1 := by fin_cases a <;> simp

/-- The pair sum is the parity of the number of surviving pairs. -/
theorem pairSum_eq_card (f g : Finset ℤ → ZMod 2) (U : Finset ℤ) :
    pairSum f g U = (((U.powerset ×ˢ U.powerset).filter (fun p =>
      p.1 ∪ p.2 = U ∧ f p.1 = 1 ∧ g p.2 = 1)).card : ZMod 2) := by
  rw [natCast_card_filter, sum_product]
  unfold pairSum
  refine sum_congr rfl (fun S _ => sum_congr rfl (fun S' _ => ?_))
  rcases zmod2_cases (f S) with h | h <;> rcases zmod2_cases (g S') with h' | h' <;>
    by_cases hu : S ∪ S' = U <;> simp [h, h', hu]

/-- **The user's target, proved.** For every `n ≥ 1` the nonlinear `C·R` injector produces an
**odd** number of surviving pairs for `M_{n+1}`; hence `M_{n+1}` survives in `a(n+1)(0)`. -/
theorem injectorPairs_card_odd (n : ℕ) (hn : 1 ≤ n) : Odd (injectorPairs n).card := by
  rw [← ZMod.natCast_eq_one_iff_odd, ← injector_pairSum_topMonomial n hn, pairSum_eq_card]
  rfl

/-! ## 3. Where Problem 1 lives: the degree-one slice of the ANF -/

theorem ind_empty : ind ∅ = fun _ => false := by funext c; simp [ind]

theorem ind_zero : ind {0} = seed := by funext c; simp [ind, seed]

/-- The coefficient of a single variable `x_j` is `f(1_{j}) + f(white)`. -/
theorem anfCoeff_singleton (f : Config → Bool) (j : ℤ) :
    anfCoeff f {j} = bz (f (ind ∅)) + bz (f (ind {j})) := by
  unfold anfCoeff coeffZ
  rw [show ({j} : Finset ℤ) = insert j ∅ from rfl, sum_powerset_insert (notMem_empty j)]
  simp

/-- **The seed's space-time diagram is the degree-one slice of the ANF.** The cell `(n, c)` of
the single-seed run equals the coefficient of the single variable `x_0` in the ANF of `a(n)(c)`.
(The constant coefficient is always `0`, since the white row stays white.) -/
theorem seed_eq_linearCoeff (n : ℕ) (c : ℤ) :
    bz (evolve seed n c) = anfCoeff (fun x => evolve x n c) {0} := by
  rw [anfCoeff_singleton, ind_empty, evolve_false, ind_zero]; simp

/-- The centre column is the `x_0`-coefficient of the ANF of `a(n)(0)`. -/
theorem centerCol_eq_linearCoeff (n : ℕ) :
    bz (centerCol n) = anfCoeff (fun x => evolve x n 0) {0} :=
  seed_eq_linearCoeff n 0

theorem bz_injective : Function.Injective bz := by decide

/-- **Problem 1 is a question about one degree-one coefficient per step.** It asks whether
`n ↦ coeff(x_0, a(n)(0))` is eventually periodic, while the injector results above concern
the coefficient of degree `2n − 1`. -/
theorem problem1_iff_linearCoeff :
    Problem1 ↔ ¬ ∃ p > 0, ∃ N, ∀ n ≥ N,
      anfCoeff (fun x => evolve x (n + p) 0) {0} = anfCoeff (fun x => evolve x n 0) {0} := by
  unfold Problem1 EventuallyPeriodic
  simp only [← centerCol_eq_linearCoeff, bz_injective.eq_iff]

/-- **The degree-one slice evolves autonomously.** The `x_0`-coefficients of step `n + 1` are
Rule 30 applied to the `x_0`-coefficients of step `n`; no coefficient of degree `≥ 2`
(in particular nothing the injector does at the top) enters. -/
theorem linearCoeff_autonomous (n : ℕ) (c : ℤ) :
    anfCoeff (fun x => evolve x (n + 1) c) {0} =
      anfCoeff (fun x => evolve x n (c - 1)) {0} + anfCoeff (fun x => evolve x n c) {0} +
        anfCoeff (fun x => evolve x n (c + 1)) {0} +
        anfCoeff (fun x => evolve x n c) {0} * anfCoeff (fun x => evolve x n (c + 1)) {0} := by
  simp only [← seed_eq_linearCoeff]
  rw [evolve_succ, bz_rule30]

/-- **The injector at the bottom of the filtration is a single pair.** When both factors have
zero constant term (as every cell of Rule 30 does), the pair sum at a single variable is just the
product of the two single-variable coefficients: on the degree-one slice the injector is the
plain `C·R` of the seed run, with no cancellation at all. -/
theorem pairSum_singleton (f g : Finset ℤ → ZMod 2) (hf : f ∅ = 0) (hg : g ∅ = 0) (j : ℤ) :
    pairSum f g {j} = f {j} * g {j} := by
  have hp : ({j} : Finset ℤ).powerset = {∅, {j}} := by
    ext S; simp [subset_singleton_iff]
  have hne : (∅ : Finset ℤ) ∉ ({{j}} : Finset (Finset ℤ)) := by simp
  unfold pairSum
  rw [hp, sum_insert hne, sum_insert hne, sum_singleton, sum_singleton]
  simp [hf, hg]

/-! ## 4. The top-degree parity lock cannot reach the seed -/

/-- **Decoupling theorem.** For *any* target sequence `b`, there is a family of Boolean
functions `G n` on the same light cones whose ANF coincides with that of Rule 30's `a(n)(0)` in
**every** coefficient except the single one of `x_0` — so it has the same degree `2n − 1` and
the same unique top monomial — but whose seed column is `b`. -/
theorem top_structure_cannot_fix_seed (b : ℕ → Bool) :
    ∃ G : ℕ → Config → Bool,
      (∀ n, DependsOnlyOn (G n) (Icc (-(n : ℤ)) n)) ∧
      (∀ n S, S ≠ {0} → anfCoeff (G n) S = anfCoeff (fun x => evolve x n 0) S) ∧
      (∀ n, G n seed = b n) := by
  refine ⟨fun n x => xor (evolve x n 0) (xor (b n) (centerCol n) && x 0), ?_, ?_, ?_⟩
  · intro n x y h
    have h0 : x 0 = y 0 := h 0 (mem_Icc.mpr ⟨by omega, by omega⟩)
    have he := evolve_dependsOnlyOn n 0 x y (by simpa using h)
    simp only at he ⊢
    rw [he, h0]
  · intro n S hS
    have hx : ∀ a b : Bool, bz (xor a b) = bz a + bz b := by decide
    unfold anfCoeff
    simp only [hx]
    rw [coeffZ_add]
    suffices h : coeffZ (fun x => bz (xor (b n) (centerCol n) && x 0)) S = 0 by
      rw [h, add_zero]
    by_cases hE : S = ∅
    · subst hE; simp [coeffZ, ind]
    · obtain ⟨j, hj, hj0⟩ : ∃ j ∈ S, j ≠ 0 := by
        by_contra hc
        push_neg at hc
        apply hS
        obtain ⟨i, hi⟩ := nonempty_iff_ne_empty.mpr hE
        have : i = 0 := hc i hi
        subst this
        exact eq_singleton_iff_unique_mem.mpr ⟨hi, hc⟩
      refine coeffZ_eq_zero_of_not_dep _ S hj (fun x c => ?_)
      rw [Function.update_of_ne hj0.symm]
  · intro n
    simp only [seed, centerCol]
    cases b n <;> cases evolve seed n 0 <;> rfl

/-- **Consequence.** No argument that uses only the ANF coefficients of degree `≥ 2` of the
maps `a(n)(0)` — in particular the injector parity lock of §2 — can prove Problem 1: a family
with all of those coefficients identical to Rule 30's has a constant (hence periodic) seed
column. -/
theorem injector_lock_compatible_with_periodicity :
    ∃ G : ℕ → Config → Bool,
      (∀ n S, 2 ≤ S.card → anfCoeff (G n) S = anfCoeff (fun x => evolve x n 0) S) ∧
      EventuallyPeriodic (fun n => G n seed) := by
  obtain ⟨G, -, hG, hs⟩ := top_structure_cannot_fix_seed (fun _ => false)
  refine ⟨G, fun n S hS => hG n S (by rintro rfl; simp at hS), 1, one_pos, 0, fun n _ => ?_⟩
  simp only [hs]

end GLM.Rule30
