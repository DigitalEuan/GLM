module

public import RequestProject.GLM.Rule30.ANF

/-!
# The top-monomial conjecture is true: `deg a(n)(0) = 2n − 1` for every `n ≥ 2`

Round 8.  All results proved (no `sorry`, standard axioms only).

## The statement

`TopMonomialConjecture` (`ANF.lean`) says that the coefficient of the monomial
`M_n = x_{2−n} ⋯ x_n` in the algebraic normal form of `a(n)(0)` is `1`; by
`topMonomialConjecture_iff` this is the parity statement `Odd (whiteDiagonalCount n)`.
Here it is proved for all `n ≥ 2` (`topMonomialConjecture_holds`), which closes the
degree formula `deg a(n)(0) = 2n − 1` (`center_anfDegree_eq`).

## The idea (the "second-cell involution")

Look at a light-cone triangle of size `m`: a row on the window `[a, a + 2m − 2]`
and the cells it determines, with

* left side  `l_s = a(s)(a + s)`,          `s < m`,
* right side `r_s = a(s)(a + 2m − 2 − s)`, `s < m` (the apex is `l_{m−1} = r_{m−1}`).

For coefficients `β : ℕ → ZMod 2` and `γ : ZMod 2` let

  `triQ β γ m a = Σ_{rows} [r ≡ 0] · (γ + Σ_s β_s l_s)   (mod 2)`.

**Key theorem (`triQ_eq`).**  For `m ≥ 2`, `triQ β γ m a = β_0`.

Proof by induction on `m`, peeling off the two leftmost cells `x_a, x_{a+1}`:

1. The right side `r_s`, `s < m − 1`, does not see `x_a, x_{a+1}`; what is left of the row is a
   triangle of size `m − 1` anchored at `a + 2` with the *same* right side.
2. Every `l_s` has `x_a` as the left edge of its cone, so flipping `x_a` flips every `l_s`
   (cone separation).  Summing over `x_a` uses up the apex condition `l_{m−1} = 0`.
3. Flipping the second cell `x_{a+1}` changes `l_s` by
   `D_s = Σ_{s' < s} (1 + l'_{s'})`, where `l'` is the left side of the smaller triangle
   (`evolve_update_second_left`, an exact Boolean-derivative formula).
   Summing over `x_{a+1}` therefore leaves an *affine* function of `l'`.

So `triQ β γ m a = triQ w c (m − 1) (a + 2)` with `w_j = Σ_{s ≤ j} β_s` (`triQ_succ`), and
`w_0 = β_0`.  The base case `m = 1` gives `triQ β γ 1 a = γ`.

Finally `whiteDiagonalCount n ≡ triQ δ₀ 1 n (1 − n)` (`whiteDiagonalCount_eq_triQ`): a
row counted by `whiteDiagonalCount n` is exactly a triangle of size `n` anchored at `1 − n`
with white right side and `l_0 = x_{1−n} = 0`.  Hence `whiteDiagonalCount n` is odd.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-- Indicator (in `ZMod 2`) that the right side of the size-`m` triangle anchored at `a` is
white. -/
def triR (m : ℕ) (a : ℤ) (x : Config) : ZMod 2 :=
  ∏ s ∈ range m, (1 + bz (evolve x s (a + 2 * (m : ℤ) - 2 - s)))

/-- The affine functional `γ + Σ_s β_s l_s` of the left side of the triangle. -/
def triL (β : ℕ → ZMod 2) (γ : ZMod 2) (m : ℕ) (a : ℤ) (x : Config) : ZMod 2 :=
  γ + ∑ s ∈ range m, β s * bz (evolve x s (a + s))

/-- `Σ_{rows on [a, a+2m−2]} [right side white] · (γ + Σ_s β_s l_s)`  (mod 2). -/
def triQ (β : ℕ → ZMod 2) (γ : ZMod 2) (m : ℕ) (a : ℤ) : ZMod 2 :=
  coeffZ (fun x => triR m a x * triL β γ m a x) (Icc a (a + 2 * (m : ℤ) - 2))

/-- Rule 30 with a flipped centre and a changed left input, in `ZMod 2`. -/
theorem bz_rule30_flip (L L' C R : Bool) :
    bz (rule30 L' (!C) R) = bz (rule30 L C R) + (bz L' + bz L) + (1 + bz R) := by
  cases L <;> cases L' <;> cases C <;> cases R <;> decide

/-- **Second-cell derivative formula.** Turning on the cell `e + 1` (white in `x`) changes the
cell `a(t)(e + t)` (whose cone has left edge `e`) by the number of white cells, mod 2, on the
diagonal `a(s)(e + s + 2)`, `s < t`. -/
theorem evolve_update_second_left (x : Config) (e : ℤ) (hx : x (e + 1) = false) (t : ℕ) :
    bz (evolve (Function.update x (e + 1) true) t (e + t)) =
      bz (evolve x t (e + t)) + ∑ s ∈ range t, (1 + bz (evolve x s (e + s + 2))) := by
  induction t with
  | zero =>
    simp
  | succ t ih =>
    set y := Function.update x (e + 1) true
    -- the centre input: left edge `e + 1`, flipped
    have hC : evolve y t (e + t + 1) = !evolve x t (e + t + 1) := by
      have h1 := cone_separation_decomposition y t (e + t + 1)
      have h2 := cone_separation_decomposition x t (e + t + 1)
      have hpos : e + (t : ℤ) + 1 - t = e + 1 := by ring
      rw [hpos] at h1 h2
      have hupd : Function.update y (e + 1) false = Function.update x (e + 1) false := by
        simp [y]
      rw [h1, h2, hupd]
      simp [y, hx]
    -- the right input is not affected
    have hR : evolve y t (e + t + 2) = evolve x t (e + t + 2) := by
      apply evolve_congr
      intro j hj _
      have : j ≠ e + 1 := by omega
      simp [y, Function.update_of_ne this]
    have hpos1 : e + ((t + 1 : ℕ) : ℤ) - 1 = e + t := by push_cast; ring
    have hpos2 : e + ((t + 1 : ℕ) : ℤ) = e + t + 1 := by push_cast; ring
    have hpos3 : e + ((t + 1 : ℕ) : ℤ) + 1 = e + t + 2 := by push_cast; ring
    rw [evolve_succ, evolve_succ, hpos1, hpos3, hpos2, hC, hR,
      bz_rule30_flip (evolve x t (e + t)), ih, sum_range_succ]
    have h2 : (2 : ZMod 2) = 0 := rfl
    linear_combination (bz (evolve x t (e + t))) * h2

/-- The product of `1 + bz b_s` is the indicator that all `b_s` are white. -/
theorem prod_one_add_bz (n : ℕ) (b : ℕ → Bool) :
    ∏ s ∈ range n, (1 + bz (b s)) = if ∀ s < n, b s = false then 1 else 0 := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [prod_range_succ, ih]
    by_cases h : ∀ s < n, b s = false
    · rw [if_pos h]
      cases hb : b n
      · rw [if_pos (fun s hs => by
          rcases Nat.lt_succ_iff_lt_or_eq.mp hs with hs | rfl
          exacts [h s hs, hb])]
        simp
      · rw [if_neg (fun h' => by simpa [hb] using h' n (by omega))]
        decide
    · rw [if_neg h, if_neg (fun h' => h (fun s hs => h' s (by omega))), zero_mul]

/-- The summation identity behind the change of coefficients. -/
theorem sum_change_coeffs (β v : ℕ → ZMod 2) (m : ℕ) :
    ∑ s ∈ range (m + 1), β s * (∑ j ∈ range s, v j + ∑ j ∈ range m, v j) =
      ∑ j ∈ range m, (∑ s ∈ range (j + 1), β s) * v j := by
  have h2 : (2 : ZMod 2) = 0 := rfl
  induction m with
  | zero => simp
  | succ m ih =>
    rw [sum_range_succ (fun s => β s * _), sum_range_succ (fun j => v j), sum_range_succ
      (fun j => (∑ s ∈ range (j + 1), β s) * v j), ← ih]
    have hsplit : ∑ s ∈ range (m + 1), β s * (∑ j ∈ range s, v j + (∑ j ∈ range m, v j + v m)) =
        ∑ s ∈ range (m + 1), β s * (∑ j ∈ range s, v j + ∑ j ∈ range m, v j) +
          (∑ s ∈ range (m + 1), β s) * v m := by
      rw [sum_mul, ← sum_add_distrib]
      exact sum_congr rfl (fun s _ => by ring)
    rw [hsplit]
    linear_combination (β (m + 1) * (∑ j ∈ range m, v j + v m)) * h2

/-- New coefficients after peeling two cells. -/
def peelCoeff (β : ℕ → ZMod 2) (j : ℕ) : ZMod 2 := ∑ s ∈ range (j + 1), β s

/-- New constant after peeling two cells. -/
def peelConst (β : ℕ → ZMod 2) (m : ℕ) : ZMod 2 := ∑ j ∈ range m, peelCoeff β j

/-- **The per-row step**: summing over the two leftmost cells of a size-`m+1` triangle. -/
theorem peel_two (β : ℕ → ZMod 2) (γ : ZMod 2) (m : ℕ) (a : ℤ) (y : Config)
    (hy0 : y a = false) (hy1 : y (a + 1) = false) :
    let F := fun x => triR (m + 1) a x * triL β γ (m + 1) a x
    F y + F (Function.update y (a + 1) true) + F (Function.update y a true) +
        F (Function.update (Function.update y (a + 1) true) a true) =
      triR m (a + 2) y * triL (peelCoeff β) (peelConst β m) m (a + 2) y := by
  intro F
  have h2 : (2 : ZMod 2) = 0 := rfl
  set y1 := Function.update y (a + 1) true with hy1def
  set R' := triR m (a + 2) y
  -- the right side, for any row agreeing with `y` from `a + 2` on
  have hR : ∀ z : Config, (∀ j, a + 2 ≤ j → z j = y j) →
      triR (m + 1) a z = R' * (1 + bz (evolve z m (a + m))) := by
    intro z hz
    unfold triR
    rw [prod_range_succ]
    congr 1
    · refine prod_congr rfl (fun s hs => ?_)
      have hs' := mem_range.mp hs
      have hpos : a + 2 * ((m + 1 : ℕ) : ℤ) - 2 - s = a + 2 + 2 * (m : ℤ) - 2 - s := by
        push_cast; ring
      rw [hpos]
      congr 2
      apply evolve_congr
      intro j hj _
      exact hz j (by omega)
    · congr 3; push_cast; ring
  -- flipping the left edge flips every cell of the left side
  have hflip : ∀ z : Config, z a = false → ∀ s : ℕ,
      bz (evolve (Function.update z a true) s (a + s)) = 1 + bz (evolve z s (a + s)) := by
    intro z hz s
    have h1 := cone_separation_decomposition (Function.update z a true) s (a + s)
    have h2' := cone_separation_decomposition z s (a + s)
    have hpos : a + (s : ℤ) - s = a := by ring
    rw [hpos] at h1 h2'
    rw [h1, h2', Function.update_idem]
    have : Function.update z a false = z := by
      rw [Function.update_eq_self_iff]; exact hz.symm
    simp [this, hz, add_comm]
  -- the pair `(z, z with x_a on)`
  have hpair : ∀ z : Config, z a = false → (∀ j, a + 2 ≤ j → z j = y j) →
      F z + F (Function.update z a true) =
        R' * (γ + ∑ s ∈ range (m + 1),
          β s * (bz (evolve z s (a + s)) + bz (evolve z m (a + m)))) := by
    intro z hz hzy
    have hzy' : ∀ j, a + 2 ≤ j → Function.update z a true j = y j := by
      intro j hj
      rw [Function.update_of_ne (by omega)]; exact hzy j hj
    simp only [F, triL]
    rw [hR z hzy, hR _ hzy', hflip z hz m]
    simp only [hflip z hz, mul_add, sum_add_distrib, mul_one]
    rw [← sum_mul]
    linear_combination (R' * (1 + bz (evolve z m (a + m))) * (γ + ∑ s ∈ range (m + 1),
      β s * bz (evolve z s (a + s))) + R' * ∑ s ∈ range (m + 1), β s) * h2
  have hy1a : y1 a = false := by
    rw [hy1def, Function.update_of_ne (by omega)]; exact hy0
  have hy1y : ∀ j, a + 2 ≤ j → y1 j = y j := by
    intro j hj; rw [hy1def, Function.update_of_ne (by omega)]
  have hsecond := evolve_update_second_left y a hy1
  have e1 : F y + F y1 + F (Function.update y a true) + F (Function.update y1 a true) =
      (F y + F (Function.update y a true)) + (F y1 + F (Function.update y1 a true)) := by ring
  rw [e1, hpair y hy0 (fun _ _ => rfl), hpair y1 hy1a hy1y]
  simp only [hy1def, hsecond]
  set D := fun s : ℕ => ∑ s' ∈ range s, (1 + bz (evolve y s' (a + s' + 2))) with hD
  have hsum : ∑ s ∈ range (m + 1), β s * (bz (evolve y s (a + s)) + bz (evolve y m (a + m))) +
      ∑ s ∈ range (m + 1), β s * (bz (evolve y s (a + s)) + D s +
        (bz (evolve y m (a + m)) + D m)) =
      ∑ s ∈ range (m + 1), β s * (D s + D m) := by
    rw [← sum_add_distrib]
    refine sum_congr rfl (fun s _ => ?_)
    linear_combination (β s * (bz (evolve y s (a + s)) + bz (evolve y m (a + m)))) * h2
  have hchange := sum_change_coeffs β (fun j => 1 + bz (evolve y j (a + j + 2))) m
  have hfinal : ∑ s ∈ range (m + 1), β s * (D s + D m) =
      triL (peelCoeff β) (peelConst β m) m (a + 2) y := by
    simp only [hD]
    rw [hchange, triL, peelConst]
    simp only [mul_add, mul_one, sum_add_distrib, peelCoeff]
    congr 1
    refine sum_congr rfl (fun j _ => ?_)
    congr 3; ring
  rw [← hfinal, ← hsum]
  linear_combination (R' * γ) * h2

/-- **The induction step**: `triQ β γ (m+1) a = triQ w c m (a+2)`. -/
theorem triQ_succ (β : ℕ → ZMod 2) (γ : ZMod 2) (m : ℕ) (hm : 1 ≤ m) (a : ℤ) :
    triQ β γ (m + 1) a = triQ (peelCoeff β) (peelConst β m) m (a + 2) := by
  unfold triQ coeffZ
  set S := Icc (a + 2) (a + 2 + 2 * (m : ℤ) - 2)
  have hS : Icc a (a + 2 * ((m + 1 : ℕ) : ℤ) - 2) = insert a (insert (a + 1) S) := by
    ext j; simp only [S, mem_Icc, mem_insert]; push_cast; omega
  have ha : a ∉ insert (a + 1) S := by simp [S]
  have ha1 : a + 1 ∉ S := by simp [S]
  rw [hS, sum_powerset_insert ha, sum_powerset_insert ha1, sum_powerset_insert ha1,
    ← sum_add_distrib, ← sum_add_distrib, ← sum_add_distrib]
  refine sum_congr rfl (fun T hT => ?_)
  have hTS := mem_powerset.mp hT
  have hy0 : ind T a = false := by
    simp only [ind, decide_eq_false_iff_not]
    intro h; have := mem_Icc.mp (hTS h); omega
  have hy1 : ind T (a + 1) = false := by
    simp only [ind, decide_eq_false_iff_not]
    intro h; have := mem_Icc.mp (hTS h); omega
  have := peel_two β γ m a (ind T) hy0 hy1
  simp only [ind_insert] at this ⊢
  rw [← this]
  ring

/-- Base case: a triangle of size one. -/
theorem triQ_one (β : ℕ → ZMod 2) (γ : ZMod 2) (a : ℤ) : triQ β γ 1 a = γ := by
  have hS : Icc a (a + 2 * ((1 : ℕ) : ℤ) - 2) = {a} := by
    ext j; simp only [mem_Icc, mem_singleton]; push_cast; omega
  unfold triQ
  rw [hS, coeffZ_split _ _ (mem_singleton_self a), erase_singleton, powerset_empty,
    sum_singleton]
  simp [triR, triL, ind]
  left; decide

/-- **Key theorem.** For every triangle of size `m ≥ 2`, `triQ β γ m a = β 0`. -/
theorem triQ_eq (m : ℕ) (hm : 2 ≤ m) (β : ℕ → ZMod 2) (γ : ZMod 2) (a : ℤ) :
    triQ β γ m a = β 0 := by
  induction m, hm using Nat.le_induction generalizing β γ a with
  | base =>
    rw [triQ_succ β γ 1 le_rfl a, triQ_one]
    simp [peelConst, peelCoeff]
  | succ m hm ih =>
    rw [triQ_succ β γ m (by omega) a, ih]
    simp [peelCoeff]

/-- `whiteDiagonalCount n` mod 2 is a triangle sum. -/
theorem whiteDiagonalCount_eq_triQ (n : ℕ) (hn : 1 ≤ n) :
    (whiteDiagonalCount n : ZMod 2) = triQ (fun s => if s = 0 then 1 else 0) 1 n (1 - n) := by
  have hmem : (1 - n : ℤ) ∈ Icc (1 - (n : ℤ)) (1 - n + 2 * (n : ℤ) - 2) := by
    simp only [mem_Icc]; omega
  have herase : (Icc (1 - (n : ℤ)) (1 - n + 2 * (n : ℤ) - 2)).erase (1 - n) =
      Icc (2 - (n : ℤ)) (n - 1) := by
    ext j; simp only [mem_erase, mem_Icc]; omega
  have hL : ∀ x : Config, triL (fun s => if s = 0 then 1 else 0) 1 n (1 - n) x =
      1 + bz (x (1 - n)) := by
    intro x
    simp only [triL, ite_mul, one_mul, zero_mul, sum_ite_eq', mem_range,
      if_pos (show 0 < n by omega)]
    simp
  have hR : ∀ x : Config, triR n (1 - n) x =
      if ∀ k < n, evolve x k ((n : ℤ) - 1 - k) = false then 1 else 0 := by
    intro x
    unfold triR
    rw [← prod_one_add_bz n (fun k => evolve x k ((n : ℤ) - 1 - k))]
    refine prod_congr rfl (fun s _ => ?_)
    congr 3; ring
  unfold triQ
  rw [coeffZ_split _ _ hmem, herase, whiteDiagonalCount, natCast_card_filter]
  refine sum_congr rfl (fun T hT => ?_)
  have hnT : (1 - n : ℤ) ∉ T := fun h => by
    have := mem_Icc.mp (mem_powerset.mp hT h); omega
  rw [hL, hL, ind_insert, Function.update_self, hR]
  simp [ind, hnT]
  right; decide

/-- **`whiteDiagonalCount n` is odd for every `n ≥ 2`.** -/
theorem whiteDiagonalCount_odd (n : ℕ) (hn : 2 ≤ n) : Odd (whiteDiagonalCount n) := by
  rw [← ZMod.natCast_eq_one_iff_odd, whiteDiagonalCount_eq_triQ n (by omega), triQ_eq n hn]
  simp

/-- **The top-monomial conjecture holds.** -/
theorem topMonomialConjecture_holds : TopMonomialConjecture :=
  topMonomialConjecture_iff.mpr whiteDiagonalCount_odd

/-- **`deg a(n)(0) = 2n − 1` for every `n ≥ 2`**: the ANF degree of the centre cell after `n`
steps, as a Boolean function of the initial row, is exactly `2n − 1`. -/
theorem center_anfDegree_eq (n : ℕ) (hn : 2 ≤ n) :
    AnfDegreeEq (fun x => evolve x n 0) (2 * n - 1) :=
  anfDegree_eq_of_conjecture topMonomialConjecture_holds n hn

/-- **`deg a(n)(c) = 2n − 1` at every position `c`** (translation invariance): the monomial
`x_{c+2−n} ⋯ x_{c+n}` occurs in the ANF of the cell `(n, c)`. -/
theorem anfDegree_eq_at (n : ℕ) (hn : 2 ≤ n) (c : ℤ) :
    AnfDegreeEq (fun x => evolve x n c) (2 * n - 1) := by
  refine ⟨anfDegree_le_at n hn c, (topMonomial n).image (· + c), ?_, ?_⟩
  · rw [card_image_of_injective _ (add_left_injective _), topMonomial_card n hn]
  · have key := anfCoeff_evolve_shift n 0 c (topMonomial n)
    rw [zero_add] at key
    rw [key]
    exact topMonomialConjecture_holds n hn

end GLM.Rule30
