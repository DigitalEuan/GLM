import Projection.OneParameter

set_option autoImplicit false

/-!
# Module 3 — projection and fibre: what a single number forgets

"One cube carries no meaning; you need several and you must move them."  The
mathematical content of that is: **a number is a projection of a group action,
and the fibre is the data the projection destroys.**  This module makes the two
projections the framework actually uses into theorems.

## The trace projection

On `SL(2,ℤ)`, `A ↦ tr A` is the model case.  It is a class function
(`trace_conj_eq`), so it cannot see anything finer than a conjugacy class — and
it cannot even see *that*:

* `trace_fibre_infinite` — infinitely many integral motions share the trace `2`;
* `same_trace_not_conjugate` — two of them, the shears by `1` and by `2`, are
  genuinely different motions: **no** integral change of basis carries one to
  the other, although their traces, determinants and characteristic polynomials
  agree.

That is "same number, several genuinely different motions", proved.

## The hull projection

`ℳ ↦ ⌊ℳ⌋ = 13` is the framework's own projection, and it is lossy in two
independent ways:

* `floor_fibre_thirteen` — the fibre of `⌊·⌋` over `13` is the whole interval
  `[13,14)`, of measure 1 (`floor_fibre_measure`).  So `13` determines nothing
  about `ℳ` beyond one bit of size;
* `three_monomials_give_thirteen` — three different monomials in the seeds have
  hull `13`: `πφe = 13.817…`, `πφ³ = 13.308…`, `π⁴/e² = 13.182…`.  So the hull
  does not even determine the exponents (`hull_map_not_injective`).

Consequence, stated as `thirteen_not_invertible`: "run 13 backwards to recover
the seeds" cannot work, and this is a theorem rather than a difficulty.
-/

namespace UBPProjection

open Matrix

/-! ## 1. The trace projection on integral motions -/

/-- The trace is a class function: conjugation cannot change it. -/
theorem trace_conj_eq {n : Type*} [Fintype n] [DecidableEq n]
    (A P Q : Matrix n n ℤ) (h : Q * P = 1) : (P * A * Q).trace = A.trace := by
  rw [Matrix.trace_mul_cycle, h, Matrix.one_mul]

/-- The integral shear by `k`. -/
def intShear (k : ℤ) : Matrix (Fin 2) (Fin 2) ℤ := !![1, k; 0, 1]

theorem intShear_det (k : ℤ) : (intShear k).det = 1 := by
  simp [intShear, Matrix.det_fin_two]

theorem intShear_trace (k : ℤ) : (intShear k).trace = 2 := by
  simp [intShear, Matrix.trace_fin_two]

theorem intShear_injective : Function.Injective intShear := by
  intro a b hab
  have := congrArg (fun M : Matrix (Fin 2) (Fin 2) ℤ => M 0 1) hab
  simpa [intShear] using this

/-- **P3-1.**  The fibre of the trace projection over `2` is infinite: the number
`2` remembers nothing about which motion produced it. -/
theorem trace_fibre_infinite :
    {A : Matrix (Fin 2) (Fin 2) ℤ | A.det = 1 ∧ A.trace = 2}.Infinite := by
  refine Set.Infinite.mono (s := Set.range intShear) ?_
    (Set.infinite_range_of_injective intShear_injective)
  rintro _ ⟨k, rfl⟩
  exact ⟨intShear_det k, intShear_trace k⟩

/-- **P3-2.**  Same trace, same determinant, same characteristic polynomial —
and yet not the same motion: no integral change of basis conjugates the shear by
`1` into the shear by `2`.  The fibre of the trace is not a single conjugacy
class. -/
theorem same_trace_not_conjugate (P : Matrix (Fin 2) (Fin 2) ℤ)
    (hP : P.det = 1 ∨ P.det = -1) : P * intShear 1 ≠ intShear 2 * P := by
  intro h
  have h01 : P 0 0 = P 0 0 + 2 * P 1 0 := by
    have := congrFun (congrFun h 0) 0
    simpa [intShear, Matrix.mul_apply, Fin.sum_univ_two] using this
  have h02 : P 0 0 + P 0 1 = P 0 1 + 2 * P 1 1 := by
    have := congrFun (congrFun h 0) 1
    simpa [intShear, Matrix.mul_apply, Fin.sum_univ_two] using this
  have hc : P 1 0 = 0 := by omega
  have ha : P 0 0 = 2 * P 1 1 := by omega
  have hdet : P.det = 2 * P 1 1 * P 1 1 := by
    rw [Matrix.det_fin_two, ha, hc]
    ring
  have hdvd : (2 : ℤ) ∣ P.det := ⟨P 1 1 * P 1 1, by rw [hdet]; ring⟩
  rcases hP with hP | hP <;> rw [hP] at hdvd <;> omega

/-! ## 2. The hull projection -/

/-- **P3-3.**  The fibre of `⌊·⌋` over `13` is the interval `[13,14)`. -/
theorem floor_fibre_thirteen : {x : ℝ | ⌊x⌋ = 13} = Set.Ico 13 14 := by
  ext x
  simp only [Set.mem_setOf_eq, Set.mem_Ico]
  constructor
  · intro h
    constructor
    · have := Int.floor_le x
      rw [h] at this
      exact_mod_cast this
    · have := Int.lt_floor_add_one x
      rw [h] at this
      norm_num at this ⊢
      linarith
  · rintro ⟨h1, h2⟩
    exact Int.floor_eq_iff.mpr ⟨by exact_mod_cast h1, by push_cast; linarith⟩

open MeasureTheory in
/-- The fibre has measure 1: the hull destroys a full unit interval of
information. -/
theorem floor_fibre_measure : volume {x : ℝ | ⌊x⌋ = 13} = 1 := by
  rw [floor_fibre_thirteen, Real.volume_Ico]
  norm_num

/-! ## 3. The hull does not determine the exponents -/

theorem phi_cubed_enc : UBP.Enc (UBP.phi ^ 3) 4.2360679774997896 4.2360679774997897 :=
  (UBP.phi_enc.pow (by norm_num) 3).mono (by norm_num) (by norm_num)

theorem pi_fourth_enc : UBP.Enc (Real.pi ^ 4) 97.4090910340024371 97.4090910340024374 :=
  (UBP.pi_enc.pow (by norm_num) 4).mono (by norm_num) (by norm_num)

theorem eSeed_sq_enc : UBP.Enc (UBP.eSeed ^ 2) 7.38905609893065022 7.38905609893065024 :=
  (UBP.eSeed_enc.pow (by norm_num) 2).mono (by norm_num) (by norm_num)

/-- `⌊π φ³⌋ = 13`. -/
theorem floor_pi_phi_cubed : ⌊Real.pi * UBP.phi ^ 3⌋ = 13 := by
  have h := UBP.pi_enc.mul phi_cubed_enc (by norm_num) (by norm_num)
  have h1 : (13 : ℝ) ≤ Real.pi * UBP.phi ^ 3 := by
    have := h.1; norm_num at this ⊢; linarith
  have h2 : Real.pi * UBP.phi ^ 3 < 14 := by
    have := h.2; norm_num at this ⊢; linarith
  exact Int.floor_eq_iff.mpr ⟨by exact_mod_cast h1, by push_cast; linarith⟩

/-- `⌊π⁴/e²⌋ = 13`. -/
theorem floor_pi_fourth_div_e_sq : ⌊Real.pi ^ 4 / UBP.eSeed ^ 2⌋ = 13 := by
  have h := pi_fourth_enc.div eSeed_sq_enc (by norm_num) (by norm_num)
  have h1 : (13 : ℝ) ≤ Real.pi ^ 4 / UBP.eSeed ^ 2 := by
    have := h.1; norm_num at this ⊢; linarith
  have h2 : Real.pi ^ 4 / UBP.eSeed ^ 2 < 14 := by
    have := h.2; norm_num at this ⊢; linarith
  exact Int.floor_eq_iff.mpr ⟨by exact_mod_cast h1, by push_cast; linarith⟩

/-- **P3-4.**  Three different monomials in the seeds have the same hull. -/
theorem three_monomials_give_thirteen :
    ⌊Real.pi * UBP.phi * UBP.eSeed⌋ = 13 ∧ ⌊Real.pi * UBP.phi ^ 3⌋ = 13 ∧
      ⌊Real.pi ^ 4 / UBP.eSeed ^ 2⌋ = 13 :=
  ⟨UBP.monad_floor, floor_pi_phi_cubed, floor_pi_fourth_div_e_sq⟩

/-- The hull map on exponent triples: `(a,b,c) ↦ ⌊π^a φ^b e^c⌋`, restricted to
non-negative exponents in the numerator and `e` in the denominator, is written
here concretely as the three monomials above. -/
theorem hull_map_not_injective :
    ∃ x y : ℝ, x ≠ y ∧ ⌊x⌋ = 13 ∧ ⌊y⌋ = 13 := by
  refine ⟨Real.pi * UBP.phi * UBP.eSeed, Real.pi * UBP.phi ^ 3, ?_, UBP.monad_floor,
    floor_pi_phi_cubed⟩
  intro h
  have h1 : (13.8 : ℝ) < Real.pi * UBP.phi * UBP.eSeed := by
    have := UBP.monad_enc.1
    rw [UBP.monad] at this
    norm_num at this ⊢
    linarith
  have h2 : Real.pi * UBP.phi ^ 3 < 13.4 := by
    have := (UBP.pi_enc.mul phi_cubed_enc (by norm_num) (by norm_num)).2
    norm_num at this ⊢
    linarith
  rw [h] at h1
  linarith

open MeasureTheory in
/-- **P3-5.**  *The hull cannot be run backwards.*  Knowing `⌊ℳ⌋ = 13` leaves a
whole unit interval of possible `ℳ`, and at least three different seed monomials
inside it.  The framework's "recover the seeds from 13" is not merely hard; it is
impossible. -/
theorem thirteen_not_invertible :
    volume {x : ℝ | ⌊x⌋ = 13} = 1 ∧ (∃ x y : ℝ, x ≠ y ∧ ⌊x⌋ = 13 ∧ ⌊y⌋ = 13) :=
  ⟨floor_fibre_measure, hull_map_not_injective⟩

end UBPProjection
