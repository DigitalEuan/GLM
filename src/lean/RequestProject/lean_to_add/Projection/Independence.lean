import UBP.OpenClaims

set_option autoImplicit false

/-!
# Appendix module — the two branches of the `trdeg ℚ(π,e)` question

The framework's minimality argument ("no seed is derivable from the others")
needs the algebraic independence of `π` and `e`, which is open.  What is *not*
open is that there are exactly two branches: the transcendence degree of
`ℚ(π,e)` over `ℚ` is `1` or `2`, and there is no third possibility.  The
productive move is therefore to formalise both branches conditionally and record
what each does to the framework, which is what this module does.

The scalar shadow of the question, and the one the study actually depends on, is
whether `π e` is transcendental.

* **Branch A — `π e` transcendental.**  Then the triadic monad `ℳ = π φ e`, the
  wobble `w` and the leakage `L` are all irrational
  (`monad_irrational_of_pi_mul_e_transcendental`,
  `wobble_irrational_of_pi_mul_e_transcendental`), and the framework's picture
  of three independent inputs survives.
* **Branch B — `π e` algebraic.**  Then `ℳ` need not be irrational, and worse
  for the framework: a rational value of `ℳ` *forces* `π e` to be algebraic
  (`pi_mul_e_isAlgebraic_of_monad_rat`), i.e. an algebraic relation between `π`
  and `e`.  In that branch the three seeds are not independent inputs at all.

Both branches are stated with the transcendence status as an explicit
hypothesis; neither is asserted.  `pi_mul_e_dichotomy` records that these two
are exhaustive — the informal suggestion that the transcendence degree might be
"1 or 2 mod 2", i.e. that some third option exists, is not available.
-/

namespace UBPProjection

open UBP

/-- The two branches are exhaustive: `π e` is either transcendental or
algebraic over `ℚ`.  There is no third option. -/
theorem pi_mul_e_dichotomy :
    Transcendental ℚ (Real.pi * eSeed) ∨ IsAlgebraic ℚ (Real.pi * eSeed) := by
  by_cases h : IsAlgebraic ℚ (Real.pi * eSeed)
  · exact Or.inr h
  · exact Or.inl h

/-- **Branch B.**  If the monad is rational then `π e` is algebraic — an
algebraic relation between `π` and `e`.  So the framework's independence claim
and the rationality of `ℳ` cannot both hold. -/
theorem pi_mul_e_isAlgebraic_of_monad_rat (r : ℚ) (h : monad = (r : ℝ)) :
    IsAlgebraic ℚ (Real.pi * eSeed) := by
  have hphi : IsAlgebraic ℚ phi := phi_isAlgebraic
  have hr : IsAlgebraic ℚ ((r : ℝ)) := isAlgebraic_algebraMap r
  have hpos : (0 : ℝ) < phi := phi_enc.pos (by norm_num)
  have hne : phi ≠ 0 := ne_of_gt hpos
  have hval : Real.pi * eSeed = (r : ℝ) / phi := by
    have hmon : Real.pi * phi * eSeed = (r : ℝ) := by rw [← h, monad]
    field_simp
    linarith [hmon]
  rw [hval, div_eq_mul_inv]
  exact hr.mul hphi.inv

/-- **Branch A.**  If `π e` is transcendental then the monad is irrational. -/
theorem monad_irrational_of_pi_mul_e_transcendental
    (h : Transcendental ℚ (Real.pi * eSeed)) : Irrational monad := by
  rintro ⟨r, hr⟩
  exact h (pi_mul_e_isAlgebraic_of_monad_rat r hr.symm)

/-- **Branch A, continued.**  Then the wobble `w = ℳ − 13` is irrational too,
and hence so is the leakage `L = w/13`. -/
theorem wobble_irrational_of_pi_mul_e_transcendental
    (h : Transcendental ℚ (Real.pi * eSeed)) : Irrational wobble ∧ Irrational leak := by
  have hm : Irrational monad := monad_irrational_of_pi_mul_e_transcendental h
  have hw : Irrational wobble := by
    have := irrational_monad_iff_irrational_wobble
    exact this.1 hm
  refine ⟨hw, ?_⟩
  rw [leak]
  rintro ⟨r, hr⟩
  exact hw ⟨13 * r, by push_cast at hr ⊢; linarith⟩

end UBPProjection
