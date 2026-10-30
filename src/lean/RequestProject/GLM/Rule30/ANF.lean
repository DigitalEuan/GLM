module

public import RequestProject.GLM.Rule30.ConeSeparation

/-!
# Algebraic normal form (ANF) of the `n`-step Rule 30 map (Target 3)

For a Boolean function `f` of the row `x : ℤ → Bool` and a finite set of positions `S`,
the **ANF coefficient** of the monomial `∏_{i ∈ S} x_i` is the Möbius transform

  `anfCoeff f S = Σ_{T ⊆ S} f(1_T)   (mod 2)`,

where `1_T` is the row that is black exactly on `T`.  `anf_representation` proves that
every `f` depending only on a finite window `W` satisfies

  `f(x) = Σ_{S ⊆ W} anfCoeff f S · ∏_{i ∈ S} x_i   (mod 2)`,

so these really are the ANF coefficients, and the ANF degree of `f` is the largest `|S|`
with `anfCoeff f S = 1`.

## Main results

* `anfCoeff_eq_zero_of_not_dependsOn`, `anfCoeff_eq_zero_of_permutive`,
  `coeffZ_mul_of_permutive` — three general tools.
* `center_anfDegree_le` (**proved for all `n ≥ 2`**): the ANF degree of `a(n)(0)` (as a
  function of the initial row) is at most `2n − 1`.  This is the upper half of the study's
  degree conjecture `deg a(n) = 2n − 1`; it uses cone separation twice.
* `anfCoeff_topMonomial_small`: the coefficient of `M_n = ∏_{i=-(n-2)}^{n} x_i` is `1` for
  `2 ≤ n ≤ 7` (machine-checked computation), so `deg a(n)(0) = 2n − 1` for those `n`.
* `topMonomial_unique_small`: for `3 ≤ n ≤ 6`, `M_n` is the *only* monomial of degree
  `2n − 1` (machine-checked computation + the general tools).
* `TopMonomialConjecture`: `anfCoeff a(n)(0) M_n = 1` for all `n ≥ 2`;
  `anfDegree_eq_of_conjecture` shows it is exactly what is missing for `deg = 2n − 1`.
  **Proved in Round 8** (`TopMonomial.lean`, `topMonomialConjecture_holds`).
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-- `Bool → ZMod 2`. -/
def bz (b : Bool) : ZMod 2 := (b.toNat : ZMod 2)

@[simp] theorem bz_not (b : Bool) : bz (!b) = bz b + 1 := by cases b <;> decide

@[simp] theorem bz_true : bz true = 1 := rfl
@[simp] theorem bz_false : bz false = 0 := rfl

theorem zmod2_add_self (a : ZMod 2) : a + a = 0 := by fin_cases a <;> decide

/-- The row that is black exactly on `T`. -/
def ind (T : Finset ℤ) : Config := fun c => decide (c ∈ T)

/-- Möbius transform of a `ZMod 2`-valued function of the row. -/
def coeffZ (F : Config → ZMod 2) (S : Finset ℤ) : ZMod 2 := ∑ T ∈ S.powerset, F (ind T)

/-- The ANF coefficient of the monomial `∏_{i ∈ S} x_i` in the Boolean function `f`. -/
def anfCoeff (f : Config → Bool) (S : Finset ℤ) : ZMod 2 := coeffZ (fun x => bz (f x)) S

/-- `f` only depends on the cells in `W`. -/
def DependsOnlyOn {α : Type*} (f : Config → α) (W : Finset ℤ) : Prop :=
  ∀ x y : Config, (∀ j ∈ W, x j = y j) → f x = f y

/-- The ANF degree of `f` is at most `d`. -/
def AnfDegreeLE (f : Config → Bool) (d : ℕ) : Prop :=
  ∀ S : Finset ℤ, d < S.card → anfCoeff f S = 0

/-- The ANF degree of `f` is exactly `d`. -/
def AnfDegreeEq (f : Config → Bool) (d : ℕ) : Prop :=
  AnfDegreeLE f d ∧ ∃ S : Finset ℤ, S.card = d ∧ anfCoeff f S = 1

/-! ## The ANF representation theorem (Möbius inversion over `GF(2)`) -/

theorem mobius_double_sum (U : Finset ℤ) (g : Finset ℤ → ZMod 2) :
    ∑ S ∈ U.powerset, ∑ T ∈ S.powerset, g T = g U := by
  induction U using Finset.induction_on generalizing g with
  | empty => simp
  | @insert a U ha ih =>
    rw [sum_powerset_insert ha]
    have h2 : ∀ S ∈ U.powerset, ∑ T ∈ (insert a S).powerset, g T =
        ∑ T ∈ S.powerset, g T + ∑ T ∈ S.powerset, g (insert a T) := by
      intro S hS
      exact sum_powerset_insert (fun h => ha (mem_powerset.mp hS h)) g
    rw [sum_congr rfl h2, sum_add_distrib, ← add_assoc, zmod2_add_self, zero_add]
    exact ih (fun T => g (insert a T))

theorem ind_agree (x : Config) (W : Finset ℤ) :
    ∀ j ∈ W, ind (W.filter (fun i => x i = true)) j = x j := by
  intro j hj
  simp only [ind, mem_filter, hj, true_and]
  cases x j <;> simp

/-- **ANF representation.** A Boolean function depending only on the window `W` is the
`GF(2)` polynomial `Σ_{S ⊆ W} anfCoeff f S · ∏_{i ∈ S} x_i`. -/
theorem anf_representation (f : Config → Bool) (W : Finset ℤ) (hf : DependsOnlyOn f W)
    (x : Config) :
    bz (f x) = ∑ S ∈ W.powerset, anfCoeff f S * ∏ i ∈ S, bz (x i) := by
  set U := W.filter (fun i => x i = true)
  have hprod : ∀ S ∈ W.powerset, anfCoeff f S * ∏ i ∈ S, bz (x i) =
      if S ⊆ U then anfCoeff f S else 0 := by
    intro S hS
    split_ifs with h
    · rw [prod_eq_one, mul_one]
      intro i hi
      have := (mem_filter.mp (h hi)).2
      simp [this]
    · obtain ⟨i, hi, hiU⟩ := not_subset.mp h
      have hxi : x i = false := by
        have hiW := mem_powerset.mp hS hi
        cases hx : x i
        · rfl
        · exact absurd (mem_filter.mpr ⟨hiW, hx⟩) hiU
      rw [prod_eq_zero hi (by simp [hxi]), mul_zero]
  rw [sum_congr rfl hprod, ← sum_filter]
  have hfilt : W.powerset.filter (fun S => S ⊆ U) = U.powerset := by
    ext S; simp only [mem_filter, mem_powerset]
    exact ⟨fun h => h.2, fun h => ⟨h.trans (filter_subset _ _), h⟩⟩
  rw [hfilt]
  unfold anfCoeff coeffZ
  rw [mobius_double_sum U (fun T => bz (f (ind T)))]
  congr 1
  exact (hf _ _ (ind_agree x W)).symm

/-! ## Three general tools -/

theorem ind_insert (T : Finset ℤ) (j : ℤ) : ind (insert j T) = Function.update (ind T) j true := by
  funext c
  by_cases h : c = j
  · subst h; simp [ind]
  · simp [ind, h]

theorem ind_insert_flip (T : Finset ℤ) (j : ℤ) (hj : j ∉ T) :
    ind (insert j T) = flipAt (ind T) j := by
  rw [ind_insert]; simp [flipAt, ind, hj]

theorem coeffZ_split (F : Config → ZMod 2) (S : Finset ℤ) {j : ℤ} (hj : j ∈ S) :
    coeffZ F S = ∑ T ∈ (S.erase j).powerset, (F (ind T) + F (ind (insert j T))) := by
  unfold coeffZ
  conv_lhs => rw [← insert_erase hj]
  rw [sum_powerset_insert (notMem_erase j S), sum_add_distrib]

theorem coeffZ_add (F G : Config → ZMod 2) (S : Finset ℤ) :
    coeffZ (fun x => F x + G x) S = coeffZ F S + coeffZ G S := sum_add_distrib

/-- **Tool 1.** If `f` does not depend on some `x_j` with `j ∈ S`, the coefficient vanishes. -/
theorem coeffZ_eq_zero_of_not_dep (F : Config → ZMod 2) (S : Finset ℤ) {j : ℤ} (hj : j ∈ S)
    (hF : ∀ x b, F (Function.update x j b) = F x) : coeffZ F S = 0 := by
  rw [coeffZ_split F S hj]
  refine sum_eq_zero (fun T _ => ?_)
  rw [ind_insert, hF, zmod2_add_self]

theorem anfCoeff_eq_zero_of_not_dependsOn (f : Config → Bool) (S : Finset ℤ) {j : ℤ}
    (hj : j ∈ S) (hf : ∀ x b, f (Function.update x j b) = f x) : anfCoeff f S = 0 :=
  coeffZ_eq_zero_of_not_dep _ S hj (fun x b => by simp [hf])

/-- **Tool 2.** If `f` is permutive in some `x_j` with `j ∈ S` and `|S| ≥ 2`, the
coefficient vanishes (the only monomial containing `x_j` is `x_j` itself). -/
theorem coeffZ_eq_zero_of_permutive (F : Config → ZMod 2) (S : Finset ℤ) {j : ℤ} (hj : j ∈ S)
    (hS : 2 ≤ S.card) (hF : ∀ x, F (flipAt x j) = F x + 1) : coeffZ F S = 0 := by
  rw [coeffZ_split F S hj]
  have : ∀ T ∈ (S.erase j).powerset, F (ind T) + F (ind (insert j T)) = 1 := by
    intro T hT
    have hjT : j ∉ T := fun h => notMem_erase j S (mem_powerset.mp hT h)
    rw [ind_insert_flip T j hjT, hF, ← add_assoc, zmod2_add_self, zero_add]
  rw [sum_congr rfl this, sum_const, card_powerset, card_erase_of_mem hj, nsmul_eq_mul,
    mul_one]
  obtain ⟨k, hk⟩ : ∃ k, S.card - 1 = k + 1 := ⟨S.card - 2, by omega⟩
  rw [hk, pow_succ]; push_cast
  rw [show (2 : ZMod 2) = 0 from rfl, mul_zero]

theorem anfCoeff_eq_zero_of_permutive (f : Config → Bool) (S : Finset ℤ) {j : ℤ} (hj : j ∈ S)
    (hS : 2 ≤ S.card) (hf : ∀ x, f (flipAt x j) = !f x) : anfCoeff f S = 0 :=
  coeffZ_eq_zero_of_permutive _ S hj hS (fun x => by simp [hf])

/-- **Tool 3.** If `B` is permutive in `x_j` (`j ∈ S`) and `C` does not depend on `x_j`, then
the coefficient of `S` in `B·C` equals the coefficient of `S ∖ {j}` in `C`. -/
theorem coeffZ_mul_of_permutive (B C : Config → ZMod 2) (S : Finset ℤ) {j : ℤ} (hj : j ∈ S)
    (hB : ∀ x, B (flipAt x j) = B x + 1) (hC : ∀ x b, C (Function.update x j b) = C x) :
    coeffZ (fun x => B x * C x) S = coeffZ C (S.erase j) := by
  rw [coeffZ_split _ S hj]
  unfold coeffZ
  refine sum_congr rfl (fun T hT => ?_)
  have hjT : j ∉ T := fun h => notMem_erase j S (mem_powerset.mp hT h)
  have h1 : C (ind (insert j T)) = C (ind T) := by rw [ind_insert, hC]
  rw [h1, ind_insert_flip T j hjT, hB]
  -- `B·C + (B+1)·C = 2·B·C + C = C` in characteristic 2
  linear_combination (B (ind T) * C (ind T)) * zmod2_add_self 1

/-! ## Facts about the `n`-step map -/

theorem evolve_update_far (x : Config) (n : ℕ) (c j : ℤ) (b : Bool)
    (hj : j < c - n ∨ c + n < j) : evolve (Function.update x j b) n c = evolve x n c :=
  evolve_congr _ _ _ _ (fun i h1 h2 => by rw [Function.update_of_ne (by omega)])

theorem evolve_dependsOnlyOn (n : ℕ) (c : ℤ) :
    DependsOnlyOn (fun x => evolve x n c) (Icc (c - n) (c + n)) :=
  fun x y h => evolve_congr x y n c (fun j h1 h2 => h j (mem_Icc.mpr ⟨h1, h2⟩))

/-- **Upper bound, the key case.** For `n ≥ 2` the coefficient of `x_{-n+1} ⋯ x_n` vanishes. -/
theorem anfCoeff_center_right_block (m : ℕ) (hm : 1 ≤ m) :
    anfCoeff (fun x => evolve x (m + 1) 0) (Icc (-(m : ℤ)) (m + 1)) = 0 := by
  set S := Icc (-(m : ℤ)) (m + 1)
  set A : Config → ZMod 2 := fun x => bz (evolve x m (-1))
  set B : Config → ZMod 2 := fun x => bz (evolve x m 0)
  set C : Config → ZMod 2 := fun x => bz (evolve x m 1)
  have hF : (fun x => bz (evolve x (m + 1) 0)) = fun x => (A x + B x + C x) + B x * C x := by
    funext x
    simp only [A, B, C, bz, evolve_succ, rule30_zmod]
    norm_num
  unfold anfCoeff
  rw [hF, coeffZ_add, coeffZ_add, coeffZ_add]
  have hA : coeffZ A S = 0 := coeffZ_eq_zero_of_not_dep A S (j := m + 1) (by simp only [S, mem_Icc]; omega)
    (fun x b => by simp only [A]; rw [evolve_update_far _ _ _ _ _ (by omega)])
  have hB : coeffZ B S = 0 := coeffZ_eq_zero_of_not_dep B S (j := m + 1) (by simp only [S, mem_Icc]; omega)
    (fun x b => by simp only [B]; rw [evolve_update_far _ _ _ _ _ (by omega)])
  have hC : coeffZ C S = 0 := coeffZ_eq_zero_of_not_dep C S (j := -m) (by simp only [S, mem_Icc]; omega)
    (fun x b => by simp only [C]; rw [evolve_update_far _ _ _ _ _ (by omega)])
  have hBC : coeffZ (fun x => B x * C x) S = coeffZ C (S.erase (-m)) :=
    coeffZ_mul_of_permutive B C S (j := -m) (by simp only [S, mem_Icc]; omega)
      (fun x => by
        simp only [B]
        have := evolve_flip_left_edge x m 0
        rw [show (0 : ℤ) - m = -m by ring] at this
        rw [this, bz_not])
      (fun x b => by simp only [C]; rw [evolve_update_far _ _ _ _ _ (by omega)])
  have hC' : coeffZ C (S.erase (-m)) = 0 := by
    refine coeffZ_eq_zero_of_permutive C _ (j := 1 - m) ?_ ?_ ?_
    · simp only [S, mem_erase, mem_Icc]; omega
    · rw [card_erase_of_mem (by simp only [S, mem_Icc]; omega), Int.card_Icc]; omega
    · intro x
      simp only [C]
      rw [evolve_flip_left_edge x m 1, bz_not]
  rw [hA, hB, hC, hBC, hC']; simp

/-- **Degree upper bound (proved for all `n ≥ 2`).** Every monomial of degree `≥ 2n` has
coefficient `0` in the ANF of the centre cell `a(n)(0)`. -/
theorem center_anfDegree_le (n : ℕ) (hn : 2 ≤ n) :
    AnfDegreeLE (fun x => evolve x n 0) (2 * n - 1) := by
  intro S hS
  by_cases hsub : S ⊆ Icc (-(n : ℤ)) n
  · by_cases hl : -(n : ℤ) ∈ S
    · refine anfCoeff_eq_zero_of_permutive _ S hl (by omega) (fun x => ?_)
      have := evolve_flip_left_edge x n 0
      rwa [show (0 : ℤ) - n = -n by ring] at this
    · have hsub' : S ⊆ Icc (-(n : ℤ) + 1) n := by
        intro j hj
        have := mem_Icc.mp (hsub hj)
        have hne : j ≠ -n := fun h => hl (h ▸ hj)
        exact mem_Icc.mpr ⟨by omega, this.2⟩
      have hcard : (Icc (-(n : ℤ) + 1) n).card ≤ S.card := by
        rw [Int.card_Icc]; omega
      have hS' := eq_of_subset_of_card_le hsub' hcard
      obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
      rw [hS']
      have := anfCoeff_center_right_block m (by omega)
      convert this using 2
      push_cast; ring_nf
  · obtain ⟨j, hj, hjn⟩ := not_subset.mp hsub
    refine anfCoeff_eq_zero_of_not_dependsOn _ S hj (fun x b => ?_)
    rw [mem_Icc, not_and_or, not_le, not_le] at hjn
    exact evolve_update_far _ _ _ _ _ (by omega)

/-! ## Translation invariance of the ANF -/

/-- Shifting the output cell by `d` shifts every monomial by `d`. -/
theorem anfCoeff_evolve_shift (n : ℕ) (c d : ℤ) (S : Finset ℤ) :
    anfCoeff (fun x => evolve x n (c + d)) (S.image (· + d)) =
      anfCoeff (fun x => evolve x n c) S := by
  unfold anfCoeff coeffZ
  rw [powerset_image, sum_image (fun T _ U _ h => image_injective (add_left_injective d) h)]
  refine sum_congr rfl (fun T _ => ?_)
  show bz (evolve (ind (T.image (· + d))) n (c + d)) = bz (evolve (ind T) n c)
  rw [← evolve_shift]
  congr 2
  funext j
  simp [ind]

/-- **Degree upper bound at every position.** By translation invariance the bound
`deg a(n)(c) ≤ 2n − 1` holds for every cell `c`, so the "spatial asymmetry" reported in the
study (`deg a(n)(1) = 2n − 2`) is an artefact of truncating the window: it is what one gets
after fixing the rightmost variable `x_{n+1}` to `0` (compare `booleanDerivative_right_edge`).
-/
theorem anfDegree_le_at (n : ℕ) (hn : 2 ≤ n) (c : ℤ) :
    AnfDegreeLE (fun x => evolve x n c) (2 * n - 1) := by
  intro S hS
  have hS' : S = (S.image (· + -c)).image (· + c) := by
    rw [image_image]; ext j; simp
  have key := anfCoeff_evolve_shift n 0 c (S.image (· + -c))
  rw [zero_add] at key
  rw [hS', key]
  refine center_anfDegree_le n hn _ ?_
  rwa [card_image_of_injective _ (add_left_injective _)]

/-! ## The top monomial -/

/-- The conjectured top monomial `M_n = ∏_{i = -(n-2)}^{n} x_i` (as its set of positions). -/
def topMonomial (n : ℕ) : Finset ℤ := Icc (2 - (n : ℤ)) n

theorem topMonomial_card (n : ℕ) (hn : 2 ≤ n) : (topMonomial n).card = 2 * n - 1 := by
  rw [topMonomial, Int.card_Icc]; omega

/-- The "right-cone weight" of a monomial: rightmost minus leftmost position. -/
def weight (S : Finset ℤ) (h : S.Nonempty) : ℤ := S.max' h - S.min' h

theorem topMonomial_weight (n : ℕ) (hn : 2 ≤ n) (h : (topMonomial n).Nonempty) :
    weight (topMonomial n) h = 2 * n - 2 := by
  have h1 : (topMonomial n).max' h = n := by
    apply le_antisymm
    · exact max'_le _ _ _ (fun y hy => (mem_Icc.mp hy).2)
    · exact le_max' _ _ (mem_Icc.mpr ⟨by omega, le_refl _⟩)
  have h2 : (topMonomial n).min' h = 2 - n := by
    apply le_antisymm
    · exact min'_le _ _ (mem_Icc.mpr ⟨le_refl _, by omega⟩)
    · exact le_min' _ _ _ (fun y hy => (mem_Icc.mp hy).1)
  simp only [weight, h1, h2]; ring

/-- **The top-monomial conjecture** (open until Round 8; proved as `topMonomialConjecture_holds`
in `TopMonomial.lean`). For every `n ≥ 2` the monomial `M_n` appears
in the ANF of `a(n)(0)`.  (Equivalent, given `center_anfDegree_le`, to
`deg a(n)(0) = 2n − 1`; it is the precise content of the study's "weight growth"
conjecture `w(M_{n+1}) = w(M_n) + 2`.) -/
def TopMonomialConjecture : Prop :=
  ∀ n : ℕ, 2 ≤ n → anfCoeff (fun x => evolve x n 0) (topMonomial n) = 1

/-- The conjecture is exactly what is missing for the exact degree formula. -/
theorem anfDegree_eq_of_conjecture (h : TopMonomialConjecture) (n : ℕ) (hn : 2 ≤ n) :
    AnfDegreeEq (fun x => evolve x n 0) (2 * n - 1) :=
  ⟨center_anfDegree_le n hn, topMonomial n, topMonomial_card n hn, h n hn⟩

/-! ## A combinatorial reformulation of the conjecture -/

/-- The number of rows `T ⊆ [2-n, n-1]` (white elsewhere) whose space-time diagram is white
along the whole diagonal `(k, n-1-k)`, `k < n`, just inside the right edge of the light cone
of `(n, 0)`. -/
def whiteDiagonalCount (n : ℕ) : ℕ :=
  ((Icc (2 - (n : ℤ)) (n - 1)).powerset.filter
    (fun T => ∀ k < n, evolve (ind T) k ((n : ℤ) - 1 - k) = false)).card

/-- **Reduction (proved).** The coefficient of `M_n` in `a(n)(0)` is the parity of
`whiteDiagonalCount n`.  Proof: extract `x_n` with a Boolean derivative and apply the
right-edge derivative formula. -/
theorem anfCoeff_topMonomial_eq_count (n : ℕ) (hn : 1 ≤ n) :
    anfCoeff (fun x => evolve x n 0) (topMonomial n) = (whiteDiagonalCount n : ZMod 2) := by
  have hmem : (n : ℤ) ∈ topMonomial n := by simp only [topMonomial, mem_Icc]; omega
  unfold anfCoeff
  rw [coeffZ_split _ _ hmem]
  have herase : (topMonomial n).erase (n : ℤ) = Icc (2 - (n : ℤ)) (n - 1) := by
    ext j; simp only [topMonomial, mem_erase, mem_Icc]; omega
  rw [herase, whiteDiagonalCount, natCast_card_filter]
  refine sum_congr rfl (fun T hT => ?_)
  have hnT : (n : ℤ) ∉ T := fun h => by
    have := mem_Icc.mp (mem_powerset.mp hT h); omega
  have h0 : ind T = Function.update (ind T) n false := by
    funext j; by_cases hj : j = n
    · subst hj; simp [ind, hnT]
    · simp [Function.update_of_ne hj]
  have hd := booleanDerivative_right_edge n 0 (ind T)
  simp only [booleanDerivative, zero_add] at hd
  rw [ind_insert]
  conv_lhs => rw [h0]
  have hxor : ∀ a b : Bool, bz a + bz b = bz (xor a b) := by decide
  show bz (evolve _ n 0) + bz (evolve _ n 0) = _
  rw [add_comm, hxor, Function.update_idem, hd]
  by_cases hP : ∀ k < n, evolve (ind T) k ((n : ℤ) - 1 - k) = false
  · rw [if_pos hP, decide_eq_true hP]; rfl
  · rw [if_neg hP, decide_eq_false hP]; rfl

/-- **The top-monomial conjecture is equivalent to a parity statement.** -/
theorem topMonomialConjecture_iff :
    TopMonomialConjecture ↔ ∀ n : ℕ, 2 ≤ n → Odd (whiteDiagonalCount n) := by
  unfold TopMonomialConjecture
  refine forall_congr' (fun n => imp_congr_right (fun hn => ?_))
  rw [anfCoeff_topMonomial_eq_count n (by omega), ZMod.natCast_eq_one_iff_odd]

end GLM.Rule30
