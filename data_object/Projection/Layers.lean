import Projection.OneParameter

set_option autoImplicit false

/-!
# Module 1 — the layer theorem: what a finite symmetry can and cannot produce

This is the headline module of the sub-study.  The UBP framework has a "chain of
levels": counting, then finite symmetry (Golay, Leech, `M₂₄`, `Co₀`, the
Monster), then the analytic constants.  The question this module settles is
**where each seed is allowed to enter**.

The answer is a genuine constraint, not an analogy:

* **Layer 0 — counting.**  Everything the combinatorial substrate produces is a
  natural number; ratios of counts are rational.  (Proved in the parent
  sub-study, `UBPFirstPrinciples.seeds_not_ratio_of_counts`.)
* **Layer 1 — finite symmetry.**  A linear map of finite order has *only roots
  of unity* as eigenvalues (`eigenvalue_of_finite_order_pow_eq_one`), so its
  character values are sums of roots of unity and therefore **algebraic**
  (`trace_isAlgebraic_of_finite_order`).  No finite group acting linearly on
  anything can produce a transcendental invariant
  (`transcendental_not_trace_of_finite_order`).  When the module is a *lattice*
  the statement is unconditional and stronger: characters are **integers**, so
  `π` and `e` are excluded by irrationality alone
  (`lattice_character_ne_pi`, `lattice_character_ne_e`).
* **Layer 2 — flows.**  `π` and `e` live here (Module 2), and by the above they
  are unreachable from Layer 1.

And the placement of the three seeds:

* `φ` is **native to Layer 1**.  It is not merely algebraic: it is literally the
  trace of a linear map of order 10 (`phi_is_trace_of_order_ten`), and equals
  `ζ + ζ⁻¹` for a primitive 10th root of unity, hence lies in a cyclotomic —
  in particular abelian — field (`phi_mem_cyclotomic`).
* The correction the framework needs: `φ` is **not an eigenvalue** of any
  finite-order map (`phi_not_eigenvalue_of_finite_order`), because eigenvalues
  of finite-order maps have modulus 1 and `φ > 1`.  So `φ` cannot enter `Co₀`
  "as a scaling"; it enters as a **character value** and through the `ℤ[φ]`
  module structure.  It *is* an eigenvalue of an infinite-order lattice map, the
  Fibonacci matrix (Module 2, `fibMat_eigenvector`).
* `π` and `e` are excluded from Layer 1 outright: conditionally on the classical
  transcendence theorems (carried, as everywhere in this project, as explicit
  hypotheses) they are not character values of any finite-order linear map
  (`pi_not_character_of_finite_order`, `e_not_character_of_finite_order`), and
  unconditionally they are not character values of any lattice symmetry.

Nothing here assumes anything about UBP; the two seed-specific statements at the
end simply place `π`, `φ`, `e` in the layers.
-/

namespace UBPProjection

open Matrix

section FiniteOrder

variable {n : Type*} [Fintype n] [DecidableEq n]

/-! ## 1. Eigenvalues of a finite-order map are roots of unity -/

/-- **L-1.**  If `M ^ k = 1` then every eigenvalue of `M` is a `k`-th root of
unity. -/
theorem eigenvalue_of_finite_order_pow_eq_one (M : Matrix n n ℂ) (k : ℕ) (hM : M ^ k = 1)
    {mu : ℂ} {v : n → ℂ} (hv : v ≠ 0) (heig : M *ᵥ v = mu • v) : mu ^ k = 1 := by
  have hpow : ∀ j : ℕ, (M ^ j) *ᵥ v = (mu ^ j) • v := by
    intro j
    induction j with
    | zero => simp
    | succ j ih =>
        rw [pow_succ, ← Matrix.mulVec_mulVec, heig, Matrix.mulVec_smul, ih, smul_smul, pow_succ]
        congr 1
        ring
  have h := hpow k
  rw [hM, Matrix.one_mulVec] at h
  obtain ⟨i, hi⟩ := Function.ne_iff.mp hv
  have hc := congrFun h i
  simp only [Pi.smul_apply, smul_eq_mul] at hc
  have h2 : (mu ^ k - 1) * v i = 0 := by linear_combination -hc
  rcases mul_eq_zero.mp h2 with h3 | h3
  · exact sub_eq_zero.mp h3
  · exact absurd h3 hi

/-- **L-2.**  The same for the roots of the characteristic polynomial. -/
theorem charpoly_root_of_finite_order_pow_eq_one (M : Matrix n n ℂ) (k : ℕ) (hM : M ^ k = 1)
    {mu : ℂ} (hroot : M.charpoly.IsRoot mu) : mu ^ k = 1 := by
  have hdet : ((Matrix.scalar n) mu - M).det = 0 := by
    rw [← Matrix.eval_charpoly]; exact hroot
  obtain ⟨v, hv, hvz⟩ := Matrix.exists_mulVec_eq_zero_iff.2 hdet
  refine eigenvalue_of_finite_order_pow_eq_one M k hM hv ?_
  rw [Matrix.sub_mulVec] at hvz
  have hs : (Matrix.scalar n mu) *ᵥ v = mu • v := by
    funext i
    simp [Matrix.scalar, Matrix.mulVec_diagonal]
  rw [hs] at hvz
  exact (sub_eq_zero.mp hvz).symm

/-! ## 2. Character values are algebraic -/

/-- A root of unity is algebraic over `ℚ`. -/
theorem rootOfUnity_isAlgebraic {k : ℕ} (hk : 0 < k) {z : ℂ} (hz : z ^ k = 1) :
    IsAlgebraic ℚ z :=
  ⟨Polynomial.X ^ k - Polynomial.C 1, Polynomial.X_pow_sub_C_ne_zero hk 1, by simp [hz]⟩

/-- A finite sum of algebraic numbers is algebraic. -/
theorem multiset_sum_isAlgebraic (s : Multiset ℂ) (h : ∀ z ∈ s, IsAlgebraic ℚ z) :
    IsAlgebraic ℚ s.sum := by
  induction s using Multiset.induction_on with
  | empty => simpa using isAlgebraic_zero
  | cons a s ih =>
      rw [Multiset.sum_cons]
      exact (h a (Multiset.mem_cons_self a s)).add
        (ih fun z hz => h z (Multiset.mem_cons_of_mem hz))

/-- **L-3.**  The trace of a finite-order matrix is a sum of roots of unity. -/
theorem trace_eq_sum_of_roots_of_unity (M : Matrix n n ℂ) (k : ℕ) (hM : M ^ k = 1) :
    ∃ s : Multiset ℂ, (∀ z ∈ s, z ^ k = 1) ∧ M.trace = s.sum := by
  refine ⟨M.charpoly.roots, fun z hz => ?_, Matrix.trace_eq_sum_roots_charpoly M⟩
  have hne : M.charpoly ≠ 0 := M.charpoly_monic.ne_zero
  exact charpoly_root_of_finite_order_pow_eq_one M k hM ((Polynomial.mem_roots hne).1 hz)

/-- **L-4.**  Hence every character value of a finite-order linear map — in
particular every character value of a finite group, in every representation — is
an **algebraic** number. -/
theorem trace_isAlgebraic_of_finite_order (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k)
    (hM : M ^ k = 1) : IsAlgebraic ℚ M.trace := by
  obtain ⟨s, hs, htr⟩ := trace_eq_sum_of_roots_of_unity M k hM
  rw [htr]
  exact multiset_sum_isAlgebraic s fun z hz => rootOfUnity_isAlgebraic hk (hs z hz)

/-- **L-5.**  *No finite symmetry produces a transcendental number.*  This is the
theorem the framework's chain of levels needs: a transcendental constant can
never be a character value of a finite-order linear map, in any dimension, over
any module. -/
theorem transcendental_not_trace_of_finite_order (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k)
    (hM : M ^ k = 1) {x : ℂ} (hx : Transcendental ℚ x) : M.trace ≠ x := by
  intro h
  exact hx (h ▸ trace_isAlgebraic_of_finite_order M k hk hM)

/-- The same for eigenvalues: a transcendental number is never an eigenvalue of a
finite-order map. -/
theorem transcendental_not_eigenvalue_of_finite_order (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k)
    (hM : M ^ k = 1) {x : ℂ} {v : n → ℂ} (hv : v ≠ 0) (heig : M *ᵥ v = x • v) :
    ¬ Transcendental ℚ x := by
  intro hx
  exact hx (rootOfUnity_isAlgebraic hk (eigenvalue_of_finite_order_pow_eq_one M k hM hv heig))

/-! ## 3. The unconditional lattice version -/

omit [DecidableEq n] in
/-- **L-6.**  A symmetry of a *lattice* is an integer matrix, and its character
value is an integer.  (Trivial, and exactly the point: Layer 1 as the framework
uses it — Golay, Leech, `M₂₄`, `Co₀` — acts on `ℤⁿ`.) -/
theorem lattice_character_isInt (M : Matrix n n ℤ) : ∃ m : ℤ, ((M.trace : ℤ) : ℝ) = m :=
  ⟨M.trace, rfl⟩

omit [DecidableEq n] in
/-- **L-7.**  *Unconditionally*: no lattice symmetry has `π` as a character
value.  Irrationality is enough; no transcendence input is needed. -/
theorem lattice_character_ne_pi (M : Matrix n n ℤ) : ((M.trace : ℤ) : ℝ) ≠ Real.pi :=
  fun h => (irrational_pi.ne_int M.trace) h.symm

omit [DecidableEq n] in
/-- The same for `e`. -/
theorem lattice_character_ne_e (M : Matrix n n ℤ) : ((M.trace : ℤ) : ℝ) ≠ UBP.eSeed := by
  obtain ⟨_, he, _⟩ := UBP.seeds_irrational
  exact fun h => (he.ne_int M.trace) h.symm

end FiniteOrder

/-! ## 4. `φ` is native to Layer 1 -/

/-- **L-8.**  `φ = 2 cos(π/5)`. -/
theorem phi_eq_two_cos : UBP.phi = 2 * Real.cos (Real.pi / 5) := by
  rw [Real.cos_pi_div_five, UBP.phi, Real.goldenRatio]
  ring

/-- **L-9.**  `φ` **is** a character value of a finite symmetry: it is the trace
of the rotation of order 10.  So `φ` is not merely algebraic — it is available
inside Layer 1, unlike `π` and `e`. -/
theorem phi_is_trace_of_order_ten :
    rot (Real.pi / 5) ^ 10 = 1 ∧ (rot (Real.pi / 5)).trace = UBP.phi := by
  constructor
  · rw [rot_pow]
    refine (rot_eq_one_iff _).2 ⟨1, ?_⟩
    push_cast
    ring
  · rw [rot_trace, phi_eq_two_cos]

/-- **L-10.**  `φ = ζ + ζ⁻¹` for `ζ` a primitive 10th root of unity: `φ` lies in
a cyclotomic field, hence is abelian over `ℚ`.  (This is the exact form of the
framework's intuition that `φ` is "reachable from the symmetry layer".) -/
theorem phi_mem_cyclotomic :
    ((Complex.exp (Real.pi / 5 * Complex.I)) ^ 10 = 1) ∧
      (UBP.phi : ℂ) = Complex.exp (Real.pi / 5 * Complex.I) +
        (Complex.exp (Real.pi / 5 * Complex.I))⁻¹ := by
  constructor
  · rw [← Complex.exp_nat_mul]
    have h : ((10 : ℕ) : ℂ) * ((Real.pi : ℂ) / 5 * Complex.I) = (2 * Real.pi) * Complex.I := by
      push_cast; ring
    rw [h, Complex.exp_mul_I]
    have hc : Complex.cos ((2 : ℂ) * Real.pi) = 1 := by
      rw [show ((2 : ℂ) * Real.pi) = ((2 * Real.pi : ℝ) : ℂ) by push_cast; ring,
        ← Complex.ofReal_cos]
      norm_cast
      simp [Real.cos_two_pi]
    have hs : Complex.sin ((2 : ℂ) * Real.pi) = 0 := by
      rw [show ((2 : ℂ) * Real.pi) = ((2 * Real.pi : ℝ) : ℂ) by push_cast; ring,
        ← Complex.ofReal_sin]
      norm_cast
      simp [Real.sin_two_pi]
    rw [hc, hs]
    ring
  · have hz : Complex.exp ((Real.pi : ℂ) / 5 * Complex.I) =
        Complex.cos ((Real.pi : ℂ) / 5) + Complex.sin ((Real.pi : ℂ) / 5) * Complex.I :=
      Complex.exp_mul_I _
    have hzi : (Complex.exp ((Real.pi : ℂ) / 5 * Complex.I))⁻¹ =
        Complex.cos ((Real.pi : ℂ) / 5) - Complex.sin ((Real.pi : ℂ) / 5) * Complex.I := by
      rw [← Complex.exp_neg]
      have h : -((Real.pi : ℂ) / 5 * Complex.I) = (-((Real.pi : ℂ) / 5)) * Complex.I := by ring
      rw [h, Complex.exp_mul_I, Complex.cos_neg, Complex.sin_neg]
      ring
    rw [hzi, hz]
    have hcos : Complex.cos ((Real.pi : ℂ) / 5) = ((Real.cos (Real.pi / 5) : ℝ) : ℂ) := by
      rw [Complex.ofReal_cos]
      norm_cast
    rw [hcos, phi_eq_two_cos]
    push_cast
    ring

/-- **L-11.**  The correction the framework needs: `φ` is **not** an eigenvalue
of any finite-order linear map, because `φ > 1` and eigenvalues of finite-order
maps are roots of unity.  `φ` enters a finite symmetry group as a *character
value*, never as a scaling. -/
theorem phi_not_eigenvalue_of_finite_order {n : Type*} [Fintype n] [DecidableEq n]
    (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k) (hM : M ^ k = 1) {v : n → ℂ} (hv : v ≠ 0) :
    M *ᵥ v ≠ (UBP.phi : ℂ) • v := by
  intro heig
  have h1 : ((UBP.phi : ℂ)) ^ k = 1 := eigenvalue_of_finite_order_pow_eq_one M k hM hv heig
  have h2 : (UBP.phi : ℝ) ^ k = 1 := by exact_mod_cast h1
  have hgt : (1 : ℝ) < UBP.phi := by
    have := UBP.phi_enc.1; norm_num at this ⊢; linarith
  have hne : k ≠ 0 := Nat.pos_iff_ne_zero.1 hk
  have : (1 : ℝ) < UBP.phi ^ k := one_lt_pow₀ hgt hne
  linarith

/-! ## 5. The layer placement of the three seeds -/

/-- **L-12.**  The layer theorem for the seeds.  Unconditionally: no lattice
symmetry produces `π` or `e`, while `φ` is the trace of an order-10 rotation.
Conditionally on transcendence — carried as hypotheses, as everywhere in this
project — `π` and `e` are not character values of *any* finite-order linear map,
in any dimension, over `ℂ`. -/
theorem seed_layer_placement
    (hpi : Transcendental ℚ ((Real.pi : ℂ))) (he : Transcendental ℚ ((UBP.eSeed : ℂ)))
    {n : Type*} [Fintype n] [DecidableEq n] (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k)
    (hM : M ^ k = 1) :
    M.trace ≠ ((Real.pi : ℂ)) ∧ M.trace ≠ ((UBP.eSeed : ℂ)) ∧
      (rot (Real.pi / 5)).trace = UBP.phi :=
  ⟨transcendental_not_trace_of_finite_order M k hk hM hpi,
   transcendental_not_trace_of_finite_order M k hk hM he,
   phi_is_trace_of_order_ten.2⟩

/-- Convenience: `π` is not a character value of a finite-order map. -/
theorem pi_not_character_of_finite_order (hpi : Transcendental ℚ ((Real.pi : ℂ)))
    {n : Type*} [Fintype n] [DecidableEq n] (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k)
    (hM : M ^ k = 1) : M.trace ≠ ((Real.pi : ℂ)) :=
  transcendental_not_trace_of_finite_order M k hk hM hpi

/-- Convenience: `e` is not a character value of a finite-order map. -/
theorem e_not_character_of_finite_order (he : Transcendental ℚ ((UBP.eSeed : ℂ)))
    {n : Type*} [Fintype n] [DecidableEq n] (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k)
    (hM : M ^ k = 1) : M.trace ≠ ((UBP.eSeed : ℂ)) :=
  transcendental_not_trace_of_finite_order M k hk hM he

end UBPProjection
