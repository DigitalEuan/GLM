/-
# Where each seed is allowed to enter

The GLM's constants are built from three seeds — `π`, `φ` and `e` — and the
archive's projection sub-study asked the question that decides how much of the
framework's "chain of levels" is real: *given that the substrate is a finite
symmetry acting on a lattice, which of the three can it possibly produce?*

The answer is a theorem, not an analogy, and it is retrieved here.

**Layer 0, counting.**  Everything a combinatorial substrate produces is a
natural number, and ratios of counts are rational.

**Layer 1, finite symmetry.**  A linear map of finite order has only roots of
unity as eigenvalues (`eigenvalue_of_finite_order_pow_eq_one`), so its character
values are sums of roots of unity and hence *algebraic*
(`trace_isAlgebraic_of_finite_order`).  No finite group acting linearly — on any
module, in any dimension — has a transcendental character value
(`transcendental_not_trace_of_finite_order`).  When the module is a *lattice*,
which is the case for Golay, Leech, `M₂₄` and `Co₀`, the statement is
unconditional and much stronger: characters are integers, so `π` is excluded by
irrationality alone (`lattice_character_ne_pi`).

**Layer 2, flows.**  `π` is the generator of the period lattice of the rotation
flow (`two_pi_least_period`), and that is where it lives.

**And the placement of `φ`.**  `φ` is native to Layer 1, but not in the way the
framework assumed:

* `phi_is_trace_of_order_ten` — `φ` *is* a character value: the trace of the
  rotation of order 10, `φ = 2 cos(π/5)`;
* `phi_not_eigenvalue_of_finite_order` — but `φ` is **not** an eigenvalue of any
  finite-order map, since those have modulus one and `φ > 1`.  So `φ` cannot
  enter a finite symmetry group "as a scaling";
* `fibMat_eigenvector` — it is an eigenvalue of an *infinite*-order lattice
  automorphism, the Fibonacci matrix, and `quadratic_eigenvalue_fibre` shows the
  whole fibre is `{φ, 1−φ}`: two points, no limit and no topology needed;
* `shear_eigenvalue_eq_one` and `phi_pow_beats_linear` — and the motion is a
  *stretch*, not a shear.  A shear has eigenvalue 1 and moves vectors linearly;
  the Fibonacci matrix moves them exponentially, and exponential beats linear.

Classical transcendence facts are carried as explicit hypotheses wherever they
are needed, exactly as in the source study; nothing here is assumed about the
GLM itself.
-/
import RequestProject.GLM.FitCapacity

namespace GLM.SeedLayers

open Matrix

/-! ## 1. Eigenvalues of a finite-order map are roots of unity -/

section FiniteOrder

variable {n : Type*} [Fintype n] [DecidableEq n]

/-- If `M ^ k = 1` then every eigenvalue of `M` is a `k`-th root of unity. -/
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

/-- The same for the roots of the characteristic polynomial. -/
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

/-- The trace of a finite-order matrix is a sum of roots of unity. -/
theorem trace_eq_sum_of_roots_of_unity (M : Matrix n n ℂ) (k : ℕ) (hM : M ^ k = 1) :
    ∃ s : Multiset ℂ, (∀ z ∈ s, z ^ k = 1) ∧ M.trace = s.sum := by
  refine ⟨M.charpoly.roots, fun z hz => ?_, Matrix.trace_eq_sum_roots_charpoly M⟩
  have hne : M.charpoly ≠ 0 := M.charpoly_monic.ne_zero
  exact charpoly_root_of_finite_order_pow_eq_one M k hM ((Polynomial.mem_roots hne).1 hz)

/-- **Every character value of a finite-order linear map is algebraic** — in
particular every character value of a finite group, in every representation. -/
theorem trace_isAlgebraic_of_finite_order (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k)
    (hM : M ^ k = 1) : IsAlgebraic ℚ M.trace := by
  obtain ⟨s, hs, htr⟩ := trace_eq_sum_of_roots_of_unity M k hM
  rw [htr]
  exact multiset_sum_isAlgebraic s fun z hz => rootOfUnity_isAlgebraic hk (hs z hz)

/-- **No finite symmetry produces a transcendental number.**  This is the
constraint the framework's chain of levels needs: a transcendental constant is
never a character value of a finite-order linear map, in any dimension. -/
theorem transcendental_not_trace_of_finite_order (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k)
    (hM : M ^ k = 1) {x : ℂ} (hx : Transcendental ℚ x) : M.trace ≠ x := by
  intro h
  exact hx (h ▸ trace_isAlgebraic_of_finite_order M k hk hM)

/-- The same for eigenvalues. -/
theorem transcendental_not_eigenvalue_of_finite_order (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k)
    (hM : M ^ k = 1) {x : ℂ} {v : n → ℂ} (hv : v ≠ 0) (heig : M *ᵥ v = x • v) :
    ¬ Transcendental ℚ x := by
  intro hx
  exact hx (rootOfUnity_isAlgebraic hk (eigenvalue_of_finite_order_pow_eq_one M k hM hv heig))

/-! ## 3. The unconditional lattice version -/

omit [DecidableEq n] in
/-- A symmetry of a *lattice* is an integer matrix, so its character value is an
integer.  Trivial, and exactly the point: Layer 1 as the GLM uses it — Golay,
Leech, `M₂₄`, `Co₀` — acts on `ℤⁿ`. -/
theorem lattice_character_isInt (M : Matrix n n ℤ) : ∃ m : ℤ, ((M.trace : ℤ) : ℝ) = m :=
  ⟨M.trace, rfl⟩

omit [DecidableEq n] in
/-- **Unconditionally: no lattice symmetry has `π` as a character value.**
Irrationality is enough; no transcendence input is needed. -/
theorem lattice_character_ne_pi (M : Matrix n n ℤ) : ((M.trace : ℤ) : ℝ) ≠ Real.pi :=
  fun h => (irrational_pi.ne_int M.trace) h.symm

omit [DecidableEq n] in
/-- The same for `e`, given its irrationality.  (Mathlib does not carry that
fact at this version, so it is an explicit hypothesis, as in the source study.) -/
theorem lattice_character_ne_eSeed (he : Irrational FitCapacity.eSeed) (M : Matrix n n ℤ) :
    ((M.trace : ℤ) : ℝ) ≠ FitCapacity.eSeed :=
  fun h => (he.ne_int M.trace) h.symm

end FiniteOrder

/-! ## 4. The rotation flow: where `π` lives -/

/-- The rotation by angle `t` in the plane. -/
noncomputable def rot (t : ℝ) : Matrix (Fin 2) (Fin 2) ℝ :=
  !![Real.cos t, -Real.sin t; Real.sin t, Real.cos t]

/-- The rotations form a one-parameter group. -/
theorem rot_mul (a b : ℝ) : rot a * rot b = rot (a + b) := by
  ext i j
  fin_cases i <;> fin_cases j <;>
    simp [rot, Matrix.mul_apply, Fin.sum_univ_two, Real.cos_add, Real.sin_add] <;> ring

theorem rot_zero : rot 0 = 1 := by
  ext i j
  fin_cases i <;> fin_cases j <;> simp [rot]

theorem rot_pow (t : ℝ) (n : ℕ) : rot t ^ n = rot (n * t) := by
  induction n with
  | zero => simpa using rot_zero.symm
  | succ n ih => rw [pow_succ, ih, rot_mul]; push_cast; ring_nf

theorem rot_trace (t : ℝ) : (rot t).trace = 2 * Real.cos t := by
  simp [rot, Matrix.trace_fin_two]; ring

theorem rot_det (t : ℝ) : (rot t).det = 1 := by
  simp only [rot, Matrix.det_fin_two_of]
  nlinarith [Real.sin_sq_add_cos_sq t]

/-- `rot t` is the identity exactly when `t` is an integer multiple of `2π`: the
period lattice of the rotation flow is `2πℤ`. -/
theorem rot_eq_one_iff (t : ℝ) : rot t = 1 ↔ ∃ k : ℤ, t = k * (2 * Real.pi) := by
  constructor
  · intro h
    have h00 : Real.cos t = 1 := by
      have := congrArg (fun M : Matrix (Fin 2) (Fin 2) ℝ => M 0 0) h
      simpa [rot, Matrix.one_apply] using this
    obtain ⟨k, hk⟩ := (Real.cos_eq_one_iff t).1 h00
    exact ⟨k, hk.symm⟩
  · rintro ⟨k, rfl⟩
    have hc : Real.cos ((k : ℝ) * (2 * Real.pi)) = 1 := Real.cos_int_mul_two_pi k
    have hs : Real.sin ((k : ℝ) * (2 * Real.pi)) = 0 := by
      have h2 : ((k : ℝ) * (2 * Real.pi)) = ((2 * k : ℤ) : ℝ) * Real.pi := by push_cast; ring
      rw [h2]; exact Real.sin_int_mul_pi (2 * k)
    ext i j
    fin_cases i <;> fin_cases j <;> simp [rot, hc, hs]

/-- **`2π` is the least positive period**: `π` is not an arbitrary normalisation
but the generator of the period lattice. -/
theorem two_pi_least_period :
    rot (2 * Real.pi) = 1 ∧ ∀ t : ℝ, 0 < t → t < 2 * Real.pi → rot t ≠ 1 := by
  refine ⟨(rot_eq_one_iff _).2 ⟨1, by push_cast; ring⟩, ?_⟩
  intro t ht htlt h
  obtain ⟨k, rfl⟩ := (rot_eq_one_iff t).1 h
  have hpi : 0 < 2 * Real.pi := by positivity
  have hk0 : (0 : ℝ) < k := by
    by_contra hc
    push_neg at hc
    nlinarith
  have hk1 : (k : ℝ) < 1 := by
    by_contra hc
    push_neg at hc
    nlinarith
  have hk0' : (0 : ℤ) < k := by exact_mod_cast hk0
  have hk1' : (k : ℤ) < 1 := by exact_mod_cast hk1
  omega

/-! ## 5. `φ` is native to the symmetry layer -/

open FitCapacity (phi eSeed)

theorem phi_sq : phi ^ 2 = phi + 1 := by
  have h5 : Real.sqrt 5 ^ 2 = 5 := Real.sq_sqrt (by norm_num)
  unfold FitCapacity.phi
  field_simp
  nlinarith [h5]

theorem phi_gt_one : 1 < phi := by
  have := FitCapacity.phi_bounds.1
  norm_num at this ⊢
  linarith

/-- `φ = 2 cos(π/5)`. -/
theorem phi_eq_two_cos : phi = 2 * Real.cos (Real.pi / 5) := by
  rw [Real.cos_pi_div_five]
  unfold FitCapacity.phi
  ring

/-- **`φ` is a character value of a finite symmetry**: the trace of the rotation
of order 10.  So `φ` is not merely algebraic — it is available inside Layer 1,
unlike `π` and `e`. -/
theorem phi_is_trace_of_order_ten :
    rot (Real.pi / 5) ^ 10 = 1 ∧ (rot (Real.pi / 5)).trace = phi := by
  constructor
  · rw [rot_pow]
    refine (rot_eq_one_iff _).2 ⟨1, ?_⟩
    push_cast
    ring
  · rw [rot_trace, phi_eq_two_cos]

/-- **The correction the framework needs.**  `φ` is *not* an eigenvalue of any
finite-order linear map, because `φ > 1` and eigenvalues of finite-order maps are
roots of unity.  `φ` enters a finite symmetry group as a character value, never
as a scaling. -/
theorem phi_not_eigenvalue_of_finite_order {n : Type*} [Fintype n] [DecidableEq n]
    (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k) (hM : M ^ k = 1) {v : n → ℂ} (hv : v ≠ 0) :
    M *ᵥ v ≠ (phi : ℂ) • v := by
  intro heig
  have h1 : ((phi : ℂ)) ^ k = 1 := eigenvalue_of_finite_order_pow_eq_one M k hM hv heig
  have h2 : (phi : ℝ) ^ k = 1 := by exact_mod_cast h1
  have hne : k ≠ 0 := Nat.pos_iff_ne_zero.1 hk
  have : (1 : ℝ) < phi ^ k := one_lt_pow₀ phi_gt_one hne
  linarith

/-! ## 6. `φ` stretches, it does not shear -/

/-- The shear with parameter `t`. -/
def shear (t : ℝ) : Matrix (Fin 2) (Fin 2) ℝ := !![1, t; 0, 1]

theorem shear_trace (t : ℝ) : (shear t).trace = 2 := by
  simp [shear, Matrix.trace_fin_two]; norm_num

theorem shear_det (t : ℝ) : (shear t).det = 1 := by simp [shear, Matrix.det_fin_two]

/-- A shear is unipotent: `(shear t − 1)² = 0`. -/
theorem shear_unipotent (t : ℝ) : (shear t - 1) ^ 2 = 0 := by
  have h : shear t - 1 = !![0, t; 0, 0] := by
    ext i j; fin_cases i <;> fin_cases j <;> simp [shear]
  rw [h, pow_two]
  ext i j
  fin_cases i <;> fin_cases j <;> simp [Matrix.mul_apply, Fin.sum_univ_two]

theorem shear_mul (a b : ℝ) : shear a * shear b = shear (a + b) := by
  ext i j
  fin_cases i <;> fin_cases j <;> simp [shear, Matrix.mul_apply, Fin.sum_univ_two, add_comm]

theorem shear_pow (t : ℝ) (n : ℕ) : shear t ^ n = shear (n * t) := by
  induction n with
  | zero =>
      ext i j
      fin_cases i <;> fin_cases j <;> simp [shear]
  | succ n ih => rw [pow_succ, ih, shear_mul]; push_cast; ring_nf

/-- A shear moves every vector *linearly* in the number of steps. -/
theorem shear_pow_mulVec (a b : ℝ) (n : ℕ) :
    (shear 1 ^ n).mulVec ![a, b] = ![a + n * b, b] := by
  rw [shear_pow]
  ext i
  fin_cases i <;> simp [shear, Matrix.mulVec, dotProduct, Fin.sum_univ_two]

/-- **The only eigenvalue of a shear is `1`**; in particular no shear has `φ` as
an eigenvalue.  A shear is not the motion behind the golden ratio. -/
theorem shear_eigenvalue_eq_one (t lam : ℝ) (v : Fin 2 → ℝ) (hv : v ≠ 0)
    (h : (shear t).mulVec v = lam • v) : lam = 1 := by
  have h1 : v 1 = lam * v 1 := by
    have := congrFun h 1
    simpa [shear, Matrix.mulVec, dotProduct, Fin.sum_univ_two] using this
  have h0 : v 0 + t * v 1 = lam * v 0 := by
    have := congrFun h 0
    simpa [shear, Matrix.mulVec, dotProduct, Fin.sum_univ_two] using this
  by_cases hb : v 1 = 0
  · have hv0 : v 0 ≠ 0 := by
      intro h00
      refine hv ?_
      funext i
      fin_cases i <;> simp [h00, hb]
    rw [hb] at h0
    have : (lam - 1) * v 0 = 0 := by linarith
    rcases mul_eq_zero.mp this with h | h
    · linarith
    · exact absurd h hv0
  · have h2 : (lam - 1) * v 1 = 0 := by linarith
    rcases mul_eq_zero.mp h2 with h | h
    · linarith
    · exact absurd h hb

/-- The Fibonacci matrix `[[1,1],[1,0]]`: the cheapest non-trivial motion of a
rank-2 integer lattice. -/
def fibMat : Matrix (Fin 2) (Fin 2) ℝ := !![1, 1; 1, 0]

theorem fibMat_trace : fibMat.trace = 1 := by simp [fibMat, Matrix.trace_fin_two]

theorem fibMat_det : fibMat.det = -1 := by simp [fibMat, Matrix.det_fin_two]

/-- **`φ` is an eigenvalue of the Fibonacci matrix** — an automorphism of `ℤ²`
of infinite order. -/
theorem fibMat_eigenvector : fibMat.mulVec ![phi, 1] = phi • ![phi, 1] := by
  have hsq : phi ^ 2 = phi + 1 := phi_sq
  funext i
  fin_cases i
  all_goals simp [fibMat, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
  all_goals nlinarith [hsq]

/-- The Galois conjugate `1 − φ` is the second eigenvalue. -/
theorem fibMat_conj_eigenvector :
    fibMat.mulVec ![1 - phi, 1] = (1 - phi) • ![1 - phi, 1] := by
  have hsq : phi ^ 2 = phi + 1 := phi_sq
  funext i
  fin_cases i
  all_goals simp [fibMat, Matrix.mulVec, dotProduct, Fin.sum_univ_two]
  all_goals nlinarith [hsq]

/-- **The fibre of the eigenvalue equation is finite, of size two.**  This is the
precise sense in which `φ` needs no limit and no topology: only a rank-2 integer
lattice and one integer matrix. -/
theorem quadratic_eigenvalue_fibre : {x : ℝ | x ^ 2 = x + 1} = {phi, 1 - phi} := by
  have hsq : phi ^ 2 = phi + 1 := phi_sq
  ext x
  simp only [Set.mem_setOf_eq, Set.mem_insert_iff, Set.mem_singleton_iff]
  constructor
  · intro hx
    have key : (x - phi) * (x - (1 - phi)) = 0 := by nlinarith [hx, hsq]
    rcases mul_eq_zero.mp key with h | h
    · left; linarith
    · right; linarith
  · rintro (rfl | rfl) <;> nlinarith [hsq]

theorem fibMat_pow_mulVec (n : ℕ) :
    (fibMat ^ n).mulVec ![phi, 1] = (phi ^ n) • ![phi, 1] := by
  induction n with
  | zero => simp
  | succ n ih =>
      rw [pow_succ, ← Matrix.mulVec_mulVec, fibMat_eigenvector, Matrix.mulVec_smul, ih,
        smul_smul, pow_succ]
      congr 1
      ring

/-- **Exponential beats linear**: the stretch really is a different kind of
motion from the shear. -/
theorem phi_pow_beats_linear (C : ℝ) : ∃ n : ℕ, C * (1 + n) < phi ^ n := by
  obtain ⟨m, hm⟩ := exists_nat_gt (10 * |C| + 20)
  refine ⟨2 * m, ?_⟩
  have hphi : (1.6 : ℝ) < phi := by
    have := FitCapacity.phi_bounds.1; norm_num at this ⊢; linarith
  have hCabs : (0:ℝ) ≤ |C| := abs_nonneg C
  have hm0 : (20 : ℝ) < m := by linarith
  have hlin : (1 : ℝ) + (0.6 : ℝ) * m ≤ phi ^ m := by
    calc (1 : ℝ) + (0.6 : ℝ) * m ≤ (1 + 0.6) ^ m := by
          have h := one_add_mul_le_pow (a := (0.6 : ℝ)) (by norm_num) m
          linarith
      _ ≤ phi ^ m := pow_le_pow_left₀ (by norm_num) (by linarith) m
  have hpos : (0 : ℝ) < 1 + 0.6 * m := by linarith
  have hsq : (1 + (0.6 : ℝ) * m) ^ 2 ≤ phi ^ (2 * m) := by
    have h2 : phi ^ (2 * m) = (phi ^ m) ^ 2 := by rw [← pow_mul, Nat.mul_comm]
    rw [h2]
    exact pow_le_pow_left₀ (le_of_lt hpos) hlin 2
  have hC : C ≤ |C| := le_abs_self C
  have hfin : C * (1 + ((2 * m : ℕ) : ℝ)) < (1 + 0.6 * m) ^ 2 := by
    push_cast
    nlinarith [hm, hm0, hC, hCabs]
  calc C * (1 + ((2 * m : ℕ) : ℝ)) < (1 + 0.6 * m) ^ 2 := hfin
    _ ≤ phi ^ (2 * m) := hsq

/-! ## 7. The layer placement, in one statement -/

/-- **The layer theorem for the three seeds.**  Conditionally on transcendence —
carried as hypotheses — `π` and `e` are not character values of any finite-order
linear map, in any dimension; while `φ` is the trace of an order-10 rotation. -/
theorem seed_layer_placement
    (hpi : Transcendental ℚ ((Real.pi : ℂ))) (he : Transcendental ℚ ((eSeed : ℂ)))
    {n : Type*} [Fintype n] [DecidableEq n] (M : Matrix n n ℂ) (k : ℕ) (hk : 0 < k)
    (hM : M ^ k = 1) :
    M.trace ≠ ((Real.pi : ℂ)) ∧ M.trace ≠ ((eSeed : ℂ)) ∧
      (rot (Real.pi / 5)).trace = phi :=
  ⟨transcendental_not_trace_of_finite_order M k hk hM hpi,
   transcendental_not_trace_of_finite_order M k hk hM he,
   phi_is_trace_of_order_ten.2⟩

end GLM.SeedLayers
