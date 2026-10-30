module

public import Mathlib

/-!
# Polynomials with no root in radicals: what the Phase 112 refusals rest on

`studies/QUINTIC_RADICAL_STUDY.md` (Phase 112) gives the branch layer of
`solve symbolically` (`glm_universal/reasoning/symbolic_nonlinear.py`)
two things it lacked: numeric polynomials above degree 6 are factored, and a
root that has no expression in radicals is *said* to have none, with the
reason, instead of the layer simply not finding one.  This file proves the
facts those statements rest on.

## 1.  The certificate the layer checks

`no_radical_root_of_prime_degree`: an irreducible polynomial over `ℚ` of prime
degree `n ≥ 5` with exactly two non-real roots (so `n - 2` real ones) has no
root that is solvable by radicals.  Its Galois group is the full symmetric
group on its `n` roots, which is not solvable.  Every hypothesis is one the
layer decides exactly: irreducibility from its factoring, the degree, and the
number of real roots from a Sturm chain.

## 2.  The quintic in letters

`trinomial_no_radical_root`: no complex root of `x⁵ - 4x + 2` is solvable by
radicals (Eisenstein at 2, three real roots).

`quintic_in_letters_no_radical_formula`: there are rational `p`, `q` (namely
`p = -4`, `q = -2`) and a complex `x` with `x⁵ + p x = q` that is not solvable
by radicals over `ℚ`.  So no expression in radicals of `p` and `q` gives a
root of `x⁵ + p x = q` at every rational point where it is defined: at that
point it would be a root in radicals.  This is the reason the layer now gives
when it refuses `x^5 + p*x = q`.

The construction in §2 follows Thomas Browning's Abel–Ruffini example in
Mathlib's `Archive/Wiedijk100Theorems/AbelRuffini.lean`, which is not part of
the importable library, specialised to the one trinomial used.
-/

@[expose] public section

namespace GLM.QuinticRadicals

open Function Polynomial Polynomial.Gal Ideal

attribute [local instance] splits_ℚ_ℂ

/-- The number of complex roots of an irreducible polynomial over `ℚ` is its
degree. -/
theorem card_complex_roots_of_irreducible {p : ℚ[X]} (p_irr : Irreducible p) :
    Fintype.card (p.rootSet ℂ) = p.natDegree :=
  card_rootSet_eq_natDegree p_irr.separable (IsAlgClosed.splits _)

/-- **The certificate.** An irreducible polynomial over `ℚ` of prime degree at
least 5 with exactly two non-real roots has no root solvable by radicals. -/
theorem no_radical_root_of_prime_degree {p : ℚ[X]} (p_irr : Irreducible p)
    (p_deg : p.natDegree.Prime) (p_five : 5 ≤ p.natDegree)
    (p_roots : Fintype.card (p.rootSet ℂ) = Fintype.card (p.rootSet ℝ) + 2)
    (x : ℂ) (hx : aeval x p = 0) : ¬ IsSolvableByRad ℚ x := by
  apply mt (solvableByRad.isSolvable' p_irr hx)
  intro h
  refine Equiv.Perm.not_solvable _ ?_
    (solvable_of_surjective (galActionHom_bijective_of_prime_degree p_irr p_deg p_roots).2)
  rw [Cardinal.mk_fintype, card_complex_roots_of_irreducible p_irr]
  exact_mod_cast p_five


/-! ### §2.  The trinomial `x⁵ - a x + b` (after Mathlib's Archive) -/

section Trinomial

variable (R : Type*) [CommRing R] (a b : ℕ)

/-- The trinomial `x⁵ - a x + b`. -/
noncomputable def trinomial : R[X] :=
  X ^ 5 - C (a : R) * X + C (b : R)

variable {R}

@[simp]
theorem map_trinomial {S : Type*} [CommRing S] (f : R →+* S) : (trinomial R a b).map f = trinomial S a b := by simp [trinomial]

@[simp]
theorem coeff_zero_trinomial : (trinomial R a b).coeff 0 = (b : R) := by simp [trinomial, coeff_X_pow]

@[simp]
theorem coeff_five_trinomial : (trinomial R a b).coeff 5 = 1 := by
  simp [trinomial, -map_natCast]

variable [Nontrivial R]

theorem degree_trinomial : (trinomial R a b).degree = ((5 : ℕ) : WithBot ℕ) := by
  suffices degree (X ^ 5 - C (a : R) * X) = ((5 : ℕ) : WithBot ℕ) by
    rwa [trinomial, degree_add_eq_left_of_degree_lt]
    convert (degree_C_le (R := R)).trans_lt (WithBot.coe_lt_coe.mpr (show 0 < 5 by simp))
  rw [degree_sub_eq_left_of_degree_lt] <;> rw [degree_X_pow]
  exact (degree_C_mul_X_le (a : R)).trans_lt (WithBot.coe_lt_coe.mpr (show 1 < 5 by simp))

theorem natDegree_trinomial : (trinomial R a b).natDegree = 5 :=
  natDegree_eq_of_degree_eq_some (degree_trinomial a b)

theorem leadingCoeff_trinomial : (trinomial R a b).leadingCoeff = 1 := by
  rw [Polynomial.leadingCoeff, natDegree_trinomial, coeff_five_trinomial]

theorem monic_trinomial : (trinomial R a b).Monic :=
  leadingCoeff_trinomial a b

theorem irreducible_trinomial (p : ℕ) (hp : p.Prime) (hpa : p ∣ a) (hpb : p ∣ b) (hp2b : ¬p ^ 2 ∣ b) :
    Irreducible (trinomial ℚ a b) := by
  rw [← map_trinomial a b (Int.castRingHom ℚ), ← IsPrimitive.Int.irreducible_iff_irreducible_map_cast]
  on_goal 1 =>
    apply irreducible_of_eisenstein_criterion
    · rwa [span_singleton_prime (Int.natCast_ne_zero.mpr hp.ne_zero), Int.prime_iff_natAbs_prime]
    · rw [leadingCoeff_trinomial, mem_span_singleton]
      exact mod_cast mt Nat.dvd_one.mp hp.ne_one
    · intro n hn
      rw [mem_span_singleton]
      rw [degree_trinomial] at hn; norm_cast at hn
      interval_cases n <;>
      simp +decide only [trinomial, coeff_X_pow, coeff_C, Int.natCast_dvd_natCast.mpr,
        hpb, if_true, coeff_C_mul, if_false, coeff_X_zero, hpa, coeff_add, zero_add, mul_zero,
        coeff_sub, add_zero, zero_sub, dvd_neg, neg_zero, dvd_mul_of_dvd_left]
    · simp only [degree_trinomial, ← WithBot.coe_zero]
      decide
    · rw [coeff_zero_trinomial, span_singleton_pow, mem_span_singleton]
      exact mt Int.natCast_dvd_natCast.mp hp2b
  all_goals exact Monic.isPrimitive (monic_trinomial a b)

attribute [local simp] map_ofNat in -- use `ofNat` simp theorem with bad keys
theorem real_roots_trinomial_le : Fintype.card ((trinomial ℚ a b).rootSet ℝ) ≤ 3 := by
  rw [← map_trinomial a b (algebraMap ℤ ℚ), trinomial, ← one_mul (X ^ 5), ← C_1]
  apply (card_rootSet_le_derivative _).trans
    (Nat.succ_le_succ ((card_rootSet_le_derivative _).trans (Nat.succ_le_succ _)))
  suffices (Polynomial.rootSet (C (20 : ℚ) * X ^ 3) ℝ).Subsingleton by
    norm_num [Fintype.card_le_one_iff_subsingleton, ← mul_assoc] at *
    exact this
  rw [rootSet_C_mul_X_pow] <;>
  norm_num

theorem real_roots_trinomial_ge_aux (hab : b < a) :
    ∃ x y : ℝ, x ≠ y ∧ aeval x (trinomial ℚ a b) = 0 ∧ aeval y (trinomial ℚ a b) = 0 := by
  let f : ℝ → ℝ := fun x : ℝ => aeval x (trinomial ℚ a b)
  have hf : f = fun x : ℝ => x ^ 5 - a * x + b := by simp [f, trinomial]
  have hc : ∀ s : Set ℝ, ContinuousOn f s := fun s => (trinomial ℚ a b).continuousOn_aeval
  have ha : (1 : ℝ) ≤ a := Nat.one_le_cast.mpr (Nat.one_le_of_lt hab)
  have hle : (0 : ℝ) ≤ 1 := zero_le_one
  have hf0 : 0 ≤ f 0 := by simp [hf]
  by_cases hb : (1 : ℝ) - a + b < 0
  · have hf1 : f 1 < 0 := by simp [hf, hb]
    have hfa : 0 ≤ f a := by
      simp_rw [hf, ← sq]
      refine add_nonneg (sub_nonneg.mpr (pow_right_mono₀ ha ?_)) ?_ <;> norm_num
    obtain ⟨x, ⟨-, hx1⟩, hx2⟩ := intermediate_value_Ico' hle (hc _) (Set.mem_Ioc.mpr ⟨hf1, hf0⟩)
    obtain ⟨y, ⟨hy1, -⟩, hy2⟩ := intermediate_value_Ioc ha (hc _) (Set.mem_Ioc.mpr ⟨hf1, hfa⟩)
    exact ⟨x, y, (hx1.trans hy1).ne, hx2, hy2⟩
  · replace hb : (b : ℝ) = a - 1 := by linarith [show (b : ℝ) + 1 ≤ a from mod_cast hab]
    have hf1 : f 1 = 0 := by simp [hf, hb]
    have hfa :=
      calc
        f (-a) = (a : ℝ) ^ 2 - (a : ℝ) ^ 5 + b := by
          norm_num [hf, ← sq, sub_eq_add_neg, add_comm, Odd.neg_pow (by decide : Odd 5)]
        _ ≤ (a : ℝ) ^ 2 - (a : ℝ) ^ 3 + (a - 1) := by gcongr <;> linarith
        _ = -((a : ℝ) - 1) ^ 2 * (a + 1) := by ring
        _ ≤ 0 := by nlinarith
    have ha' := neg_nonpos.mpr (hle.trans ha)
    obtain ⟨x, ⟨-, hx1⟩, hx2⟩ := intermediate_value_Icc ha' (hc _) (Set.mem_Icc.mpr ⟨hfa, hf0⟩)
    exact ⟨x, 1, (hx1.trans_lt zero_lt_one).ne, hx2, hf1⟩

theorem real_roots_trinomial_ge (hab : b < a) : 2 ≤ Fintype.card ((trinomial ℚ a b).rootSet ℝ) := by
  have q_ne_zero : trinomial ℚ a b ≠ 0 := (monic_trinomial a b).ne_zero
  obtain ⟨x, y, hxy, hx, hy⟩ := real_roots_trinomial_ge_aux a b hab
  have key : ↑({x, y} : Finset ℝ) ⊆ (trinomial ℚ a b).rootSet ℝ := by
    simp [Set.insert_subset, mem_rootSet_of_ne q_ne_zero, hx, hy]
  convert Fintype.card_le_of_embedding (Set.embeddingOfSubset _ _ key)
  simp only [Finset.coe_sort_coe, Fintype.card_coe, Finset.card_singleton,
    Finset.card_insert_of_notMem (mt Finset.mem_singleton.mp hxy)]

theorem complex_roots_trinomial (h : (trinomial ℚ a b).Separable) : Fintype.card ((trinomial ℚ a b).rootSet ℂ) = 5 :=
  (card_rootSet_eq_natDegree h (IsAlgClosed.splits _)).trans (natDegree_trinomial a b)

theorem gal_trinomial (hab : b < a) (h_irred : Irreducible (trinomial ℚ a b)) :
    Bijective (galActionHom (trinomial ℚ a b) ℂ) := by
  apply galActionHom_bijective_of_prime_degree' h_irred
  · simp only [natDegree_trinomial]; decide
  · rw [complex_roots_trinomial a b h_irred.separable, Nat.succ_le_succ_iff]
    exact (real_roots_trinomial_le a b).trans (Nat.le_succ 3)
  · simp_rw [complex_roots_trinomial a b h_irred.separable, Nat.succ_le_succ_iff]
    exact real_roots_trinomial_ge a b hab

/-- With `b < a` and a prime dividing `a` and `b` once, no root of `x⁵ - a x + b`
is solvable by radicals. -/
theorem trinomial_family_no_radical_root (p : ℕ) (x : ℂ) (hx : aeval x (trinomial ℚ a b) = 0) (hab : b < a)
    (hp : p.Prime) (hpa : p ∣ a) (hpb : p ∣ b) (hp2b : ¬p ^ 2 ∣ b) : ¬IsSolvableByRad ℚ x := by
  have h_irred := irreducible_trinomial a b p hp hpa hpb hp2b
  apply mt (solvableByRad.isSolvable' h_irred hx)
  intro h
  refine Equiv.Perm.not_solvable _ (le_of_eq ?_)
    (solvable_of_surjective (gal_trinomial a b hab h_irred).2)
  rw_mod_cast [Cardinal.mk_fintype, complex_roots_trinomial a b h_irred.separable]

/-- No complex root of `x⁵ - 4x + 2` is solvable by radicals. -/
theorem trinomial_no_radical_root (x : ℂ) (hx : aeval x (trinomial ℚ 4 2) = 0) : ¬IsSolvableByRad ℚ x := by
  apply trinomial_family_no_radical_root 4 2 2 x hx <;> decide

/-- **Abel-Ruffini Theorem** -/
theorem exists_not_solvable_by_rad_trinomial : ∃ x : ℂ, IsAlgebraic ℚ x ∧ ¬IsSolvableByRad ℚ x := by
  obtain ⟨x, hx⟩ := (IsAlgClosed.splits (trinomial ℂ 4 2)).exists_eval_eq_zero (by simp [degree_trinomial])
  rw [← map_trinomial 4 2 (algebraMap ℚ ℂ), eval_map] at hx
  exact ⟨x, ⟨trinomial ℚ 4 2, (monic_trinomial 4 2).ne_zero, hx⟩, trinomial_no_radical_root x hx⟩


end Trinomial

/-- **The quintic in letters.** At `p = -4`, `q = -2` the equation `x⁵ + p x = q`
has a complex root that is not solvable by radicals over `ℚ`, so no radical
expression in `p` and `q` defined at that point gives a root there. -/
theorem quintic_in_letters_no_radical_formula :
    ∃ p q : ℚ, ∃ x : ℂ, x ^ 5 + (p : ℂ) * x = (q : ℂ) ∧ ¬ IsSolvableByRad ℚ x := by
  obtain ⟨x, hx⟩ := (IsAlgClosed.splits (trinomial ℂ 4 2)).exists_eval_eq_zero
    (by simp [degree_trinomial])
  rw [← map_trinomial 4 2 (algebraMap ℚ ℂ), eval_map] at hx
  refine ⟨-4, -2, x, ?_, trinomial_no_radical_root x hx⟩
  have h : x ^ 5 - 4 * x + 2 = 0 := by
    simpa [trinomial, eval₂_sub, eval₂_add] using hx
  push_cast
  linear_combination h

end GLM.QuinticRadicals
