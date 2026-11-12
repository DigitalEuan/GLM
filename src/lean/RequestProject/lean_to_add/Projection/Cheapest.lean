import Mathlib
import UBP.SeedClasses

set_option autoImplicit false

/-!
# Module 4 — in what sense `φ` is "cheapest", and in what sense it is not

The framework says `φ` is "the cheapest self-similarity an integer lattice
supports".  That is nearly right, and this module makes it exact — including the
two places where the claim as stated is **wrong**.

* **Right, in two dimensions.**  `φ` is the smallest quadratic Pisot number: if
  a real algebraic integer `β > 1` of degree ≤ 2 has its conjugate inside the
  unit circle, then `β ≥ φ` (`quadratic_pisot_ge_phi`), and `φ` itself is such a
  number (`phi_isQuadPisot`).  The proof is a two-line integer case analysis, so
  no Pisot theory is needed.
* **Wrong, absolutely.**  The smallest Pisot number of all is the *plastic
  number* `ρ ≈ 1.3247`, the real root of `x³ = x + 1`, which is smaller than `φ`
  (`plastic_lt_phi`) and is a Pisot number (`plastic_conjugates_inside_disc`:
  its two conjugates have modulus `√(ρ²−1) < 1`).  So `φ` is cheapest in
  dimension 2, not cheapest.
* **A different property, often conflated with self-similarity.**  What makes
  `φ` appear in packing and stability arguments is that it is the *worst
  approximable* real number: `|φ − p/q| ≥ 1/(3q²)` for every rational `p/q`
  (`phi_badly_approximable`).  The sharp constant is `1/(√5 q²)` (Hurwitz); the
  bound proved here is the same statement with a safe constant, which is all the
  qualitative claim needs.  By contrast `φ` is not a Liouville number
  (`phi_not_liouville`) — no rational approximates it to arbitrary order.

Findings: P4-1 … P4-6.
-/

namespace UBPProjection

open Real

/-! ## 1. `φ` is the smallest quadratic Pisot number -/

/-- `IsQuadPisotPair b b' p q` : `b` and `b'` are the two roots of the monic
integer quadratic `x² − p x − q`, with `b > 1` and the conjugate `b'` strictly
inside the unit circle.  (Vieta's relations are taken as the definition, which
avoids any polynomial machinery.) -/
def IsQuadPisotPair (b b' : ℝ) (p q : ℤ) : Prop :=
  b + b' = (p : ℝ) ∧ b * b' = -(q : ℝ) ∧ 1 < b ∧ |b'| < 1

/-- **P4-1.**  `φ` is a quadratic Pisot number: `x² − x − 1`, conjugate
`1 − φ = −1/φ` of modulus `0.618… < 1`. -/
theorem phi_isQuadPisot : IsQuadPisotPair UBP.phi (1 - UBP.phi) 1 1 := by
  have hsq : UBP.phi ^ 2 = UBP.phi + 1 := UBP.phi_sq
  have h1 : (1.618 : ℝ) < UBP.phi := by have := UBP.phi_enc.1; norm_num at this ⊢; linarith
  have h2 : UBP.phi < 1.6181 := by have := UBP.phi_enc.2; norm_num at this ⊢; linarith
  refine ⟨by push_cast; ring, by push_cast; nlinarith [hsq], by linarith, ?_⟩
  rw [abs_lt]
  constructor <;> linarith

/-- **P4-2.**  *No quadratic Pisot number is smaller than `φ`.*  The proof is
pure integer arithmetic: the trace `p` is positive, the value of the polynomial
at `1` is negative so `p + q ≥ 2`, and those two facts force the polynomial to
be non-positive at `φ`. -/
theorem quadratic_pisot_ge_phi {b b' : ℝ} {p q : ℤ} (h : IsQuadPisotPair b b' p q) :
    UBP.phi ≤ b := by
  obtain ⟨hsum, hprod, hb, hb'⟩ := h
  rw [abs_lt] at hb'
  have hsq : UBP.phi ^ 2 = UBP.phi + 1 := UBP.phi_sq
  have hphi1 : (1 : ℝ) < UBP.phi := by have := UBP.phi_enc.1; norm_num at this ⊢; linarith
  -- the trace is a positive integer
  have hp0 : (0 : ℝ) < (p : ℝ) := by rw [← hsum]; linarith [hb'.1]
  have hp1 : (1 : ℤ) ≤ p := by
    have hp0' : (0 : ℤ) < p := by exact_mod_cast hp0
    omega
  -- the polynomial is negative at 1, so `p + q ≥ 2`
  have hval1 : (1 : ℝ) - p - q < 0 := by nlinarith [hb'.2]
  have hpq : (2 : ℤ) ≤ p + q := by
    have : (1 : ℝ) < (p : ℝ) + q := by linarith
    have h' : (1 : ℤ) < p + q := by exact_mod_cast this
    omega
  -- hence the polynomial is non-positive at `φ`
  have hkey : UBP.phi ^ 2 - (p : ℝ) * UBP.phi - (q : ℝ) ≤ 0 := by
    have hp1' : (1 : ℝ) ≤ (p : ℝ) := by exact_mod_cast hp1
    have hpq' : (2 : ℝ) ≤ (p : ℝ) + (q : ℝ) := by exact_mod_cast hpq
    nlinarith [hsq, hphi1, hp1', hpq']
  -- and the polynomial factors as `(x − b)(x − b')`
  have hfac : UBP.phi ^ 2 - (p : ℝ) * UBP.phi - (q : ℝ) = (UBP.phi - b) * (UBP.phi - b') := by
    rw [← hsum, ← neg_neg ((q : ℝ)), ← hprod]
    ring
  have hpos : 0 < UBP.phi - b' := by linarith [hb'.2]
  nlinarith [hkey, hfac, hpos]

/-! ## 2. The plastic number is smaller, and is Pisot -/

theorem exists_plastic : ∃ r : ℝ, r ^ 3 = r + 1 ∧ 1.32 < r ∧ r < 1.33 := by
  have hcont : ContinuousOn (fun x : ℝ => x ^ 3 - x - 1) (Set.Icc (1.32 : ℝ) 1.33) := by fun_prop
  have h := intermediate_value_Icc (by norm_num : (1.32 : ℝ) ≤ 1.33) hcont
  have h0 : (0 : ℝ) ∈ Set.Icc ((fun x : ℝ => x ^ 3 - x - 1) 1.32)
      ((fun x : ℝ => x ^ 3 - x - 1) 1.33) := by
    constructor <;> norm_num
  obtain ⟨r, hr, hr0⟩ := h h0
  simp only at hr0
  refine ⟨r, by linarith, ?_, ?_⟩
  · rcases lt_or_eq_of_le hr.1 with h' | h'
    · exact h'
    · exfalso; rw [← h'] at hr0; norm_num at hr0
  · rcases lt_or_eq_of_le hr.2 with h' | h'
    · exact h'
    · exfalso; rw [h'] at hr0; norm_num at hr0

/-- The plastic number: the real root of `x³ = x + 1`. -/
noncomputable def plastic : ℝ := Classical.choose exists_plastic

theorem plastic_cubic : plastic ^ 3 = plastic + 1 := (Classical.choose_spec exists_plastic).1

theorem plastic_bounds : 1.32 < plastic ∧ plastic < 1.33 :=
  ⟨(Classical.choose_spec exists_plastic).2.1, (Classical.choose_spec exists_plastic).2.2⟩

/-- Any real solution of `x³ = x + 1` exceeds `1`. -/
theorem cubic_root_gt_one {t : ℝ} (h : t ^ 3 = t + 1) : 1 < t := by
  nlinarith [sq_nonneg (t - 1), sq_nonneg (t + 1), sq_nonneg t]

/-- `x³ = x + 1` has exactly one real solution. -/
theorem cubic_real_root_unique {x y : ℝ} (hx : x ^ 3 = x + 1) (hy : y ^ 3 = y + 1) : x = y := by
  have hx1 := cubic_root_gt_one hx
  have hy1 := cubic_root_gt_one hy
  by_contra hne
  have hfac : (x - y) * (x ^ 2 + x * y + y ^ 2 - 1) = 0 := by nlinarith [hx, hy]
  rcases mul_eq_zero.mp hfac with h | h
  · exact hne (by linarith)
  · nlinarith [hx1, hy1]

/-- **P4-3.**  The plastic number is smaller than `φ`. -/
theorem plastic_lt_phi : plastic < UBP.phi := by
  have h1 := plastic_bounds.2
  have h2 : (1.618 : ℝ) < UBP.phi := by have := UBP.phi_enc.1; norm_num at this ⊢; linarith
  linarith

/-- **P4-4.**  The plastic number is a Pisot number: its two conjugates lie
strictly inside the unit circle.  Hence the smallest Pisot number is of degree 3
and `φ` is *not* the cheapest self-similarity in general — only the cheapest one
a rank-2 lattice supports. -/
theorem plastic_conjugates_inside_disc (z : ℂ) (hz : z ^ 3 = z + 1)
    (hne : z ≠ (plastic : ℂ)) : ‖z‖ < 1 := by
  have hr : (plastic : ℂ) ^ 3 = (plastic : ℂ) + 1 := by
    exact_mod_cast congrArg (fun t : ℝ => (t : ℂ)) plastic_cubic
  -- `z` is a root of the quadratic cofactor
  have hquad : z ^ 2 + (plastic : ℂ) * z + ((plastic : ℂ) ^ 2 - 1) = 0 := by
    have hfac : (z - (plastic : ℂ)) * (z ^ 2 + (plastic : ℂ) * z + ((plastic : ℂ) ^ 2 - 1)) = 0 := by
      linear_combination hz - hr
    rcases mul_eq_zero.mp hfac with h | h
    · exact absurd (sub_eq_zero.mp h) hne
    · exact h
  -- `z` is not real
  have hnotreal : z ≠ (z.re : ℂ) := by
    intro hreal
    have : (z.re : ℝ) ^ 3 = z.re + 1 := by
      have h1 : ((z.re : ℂ)) ^ 3 = (z.re : ℂ) + 1 := by rw [← hreal]; exact hz
      exact_mod_cast h1
    exact hne (by rw [hreal, cubic_real_root_unique this plastic_cubic])
  -- the conjugate is the other root
  have hconj : (starRingEnd ℂ) z ≠ z := by
    intro h
    exact hnotreal (Complex.conj_eq_iff_re.mp h).symm
  have hquad' : ((starRingEnd ℂ) z) ^ 2 + (plastic : ℂ) * ((starRingEnd ℂ) z) +
      ((plastic : ℂ) ^ 2 - 1) = 0 := by
    have := congrArg (starRingEnd ℂ) hquad
    simpa using this
  have hsum : z + (starRingEnd ℂ) z = -(plastic : ℂ) := by
    have hdiff : (z - (starRingEnd ℂ) z) * (z + (starRingEnd ℂ) z + (plastic : ℂ)) = 0 := by
      linear_combination hquad - hquad'
    rcases mul_eq_zero.mp hdiff with h | h
    · exact absurd (sub_eq_zero.mp h).symm hconj
    · linear_combination h
  have hprod : z * (starRingEnd ℂ) z = ((plastic : ℂ) ^ 2 - 1) := by
    have hs : (starRingEnd ℂ) z = -(plastic : ℂ) - z := by linear_combination hsum
    rw [hs]
    linear_combination -hquad
  -- so `‖z‖² = ρ² − 1 < 1`
  have hnormSq : (Complex.normSq z : ℝ) = plastic ^ 2 - 1 := by
    have := Complex.mul_conj z
    rw [hprod] at this
    exact_mod_cast this.symm
  have hb := plastic_bounds
  have hlt : plastic ^ 2 - 1 < 1 := by nlinarith [hb.1, hb.2]
  have hsq : ‖z‖ ^ 2 = plastic ^ 2 - 1 := by rw [Complex.sq_norm, hnormSq]
  nlinarith [norm_nonneg z, hsq, hlt]

/-! ## 3. Worst approximability — the property that actually matters -/

theorem sqrt5_lt : Real.sqrt 5 < 2.24 := by
  have := UBP.sqrt5_enc.2; norm_num at this ⊢; linarith

theorem phi_conj_sum : UBP.phi + (1 - UBP.phi) = 1 := by ring

theorem phi_conj_prod : UBP.phi * (1 - UBP.phi) = -1 := by
  have hsq : UBP.phi ^ 2 = UBP.phi + 1 := UBP.phi_sq
  nlinarith [hsq]

theorem phi_sub_conj : UBP.phi - (1 - UBP.phi) = Real.sqrt 5 := by
  rw [UBP.phi, Real.goldenRatio]
  ring

/-- The integer form `p² − pq − q²` never vanishes for `q > 0`: otherwise `√5`
would be rational. -/
theorem norm_form_ne_zero (p q : ℤ) (hq : 0 < q) : p ^ 2 - p * q - q ^ 2 ≠ 0 := by
  intro h
  have hsq : (2 * p - q) ^ 2 = 5 * q ^ 2 := by ring_nf; linarith [h]
  have hqR : (0 : ℝ) < (q : ℝ) := by exact_mod_cast hq
  have hR : ((2 * p - q : ℤ) : ℝ) ^ 2 = 5 * ((q : ℤ) : ℝ) ^ 2 := by exact_mod_cast hsq
  have habs : (|((2 * p - q : ℤ) : ℝ)| / (q : ℝ)) ^ 2 = 5 := by
    rw [div_pow, sq_abs, hR]
    field_simp
  have h5 : Real.sqrt 5 = |((2 * p - q : ℤ) : ℝ)| / (q : ℝ) := by
    rw [← habs, Real.sqrt_sq (by positivity)]
  have hirr : Irrational (Real.sqrt 5) := by
    simpa using (Nat.prime_five).irrational_sqrt
  refine hirr ⟨(|2 * p - q| : ℤ) / (q : ℚ), ?_⟩
  rw [h5]
  push_cast
  ring

/-- **P4-5.**  *`φ` is badly approximable.*  For every rational `p/q` with
`q > 0`, `|φ − p/q| ≥ 1/(3q²)`.  (The sharp constant is `1/(√5 q²)`; the point
of the theorem is the exponent 2 with a positive constant, which is what makes
`φ` the extremal case in packing and stability arguments.) -/
theorem phi_badly_approximable (p q : ℤ) (hq : 0 < q) :
    1 / (3 * (q : ℝ) ^ 2) ≤ |UBP.phi - (p : ℝ) / (q : ℝ)| := by
  have hqR : (0 : ℝ) < (q : ℝ) := by exact_mod_cast hq
  have hq1 : (1 : ℝ) ≤ (q : ℝ) := by exact_mod_cast hq
  set t : ℝ := |(p : ℝ) - (q : ℝ) * UBP.phi| with ht
  have hfac : ((p : ℝ) - q * UBP.phi) * ((p : ℝ) - q * (1 - UBP.phi)) =
      ((p ^ 2 - p * q - q ^ 2 : ℤ) : ℝ) := by
    have h1 : UBP.phi * (1 - UBP.phi) = -1 := phi_conj_prod
    push_cast
    nlinarith [h1]
  have hne : ((p ^ 2 - p * q - q ^ 2 : ℤ) : ℝ) ≠ 0 := by
    exact_mod_cast norm_form_ne_zero p q hq
  have hge1 : (1 : ℝ) ≤ |((p ^ 2 - p * q - q ^ 2 : ℤ) : ℝ)| := by
    have h1 : (1 : ℤ) ≤ |p ^ 2 - p * q - q ^ 2| := by
      rcases lt_trichotomy (p ^ 2 - p * q - q ^ 2) 0 with h | h | h
      · rw [abs_of_neg h]; omega
      · exact absurd (by exact_mod_cast congrArg (fun n : ℤ => (n : ℝ)) h) hne
      · rw [abs_of_pos h]; omega
    calc (1 : ℝ) = ((1 : ℤ) : ℝ) := by norm_num
      _ ≤ ((|p ^ 2 - p * q - q ^ 2| : ℤ) : ℝ) := by exact_mod_cast h1
      _ = |((p ^ 2 - p * q - q ^ 2 : ℤ) : ℝ)| := by push_cast [Int.cast_abs]; ring_nf
  have hkey : 1 ≤ t * |(p : ℝ) - q * (1 - UBP.phi)| := by
    rw [ht, ← abs_mul, hfac]
    exact hge1
  have hbound : |(p : ℝ) - q * (1 - UBP.phi)| ≤ t + (q : ℝ) * Real.sqrt 5 := by
    have hrw : (p : ℝ) - q * (1 - UBP.phi) =
        ((p : ℝ) - q * UBP.phi) + (q : ℝ) * (UBP.phi - (1 - UBP.phi)) := by ring
    calc |(p : ℝ) - q * (1 - UBP.phi)|
        ≤ |(p : ℝ) - q * UBP.phi| + |(q : ℝ) * (UBP.phi - (1 - UBP.phi))| := by
          rw [hrw]; exact abs_add_le _ _
      _ = t + (q : ℝ) * Real.sqrt 5 := by
          rw [phi_sub_conj, abs_mul, abs_of_pos hqR, abs_of_nonneg (Real.sqrt_nonneg 5)]
  -- lower bound on `t`
  have htpos : 0 ≤ t := abs_nonneg _
  have hprod2 : 1 ≤ t * (t + (q : ℝ) * Real.sqrt 5) := by
    have := mul_le_mul_of_nonneg_left hbound htpos
    linarith [hkey, this]
  have htlb : 1 / (3 * (q : ℝ)) ≤ t := by
    by_contra hcon
    push_neg at hcon
    have hA : t * (3 * (q : ℝ)) < 1 := (lt_div_iff₀ (by positivity)).1 hcon
    have h5 : Real.sqrt 5 < 2.24 := sqrt5_lt
    have hs0 : 0 ≤ Real.sqrt 5 := Real.sqrt_nonneg 5
    have htq : t * (q : ℝ) < 1 / 3 := by linarith
    have ht13 : t < 1 / 3 := by nlinarith [htq, hq1, htpos]
    nlinarith [hprod2, ht13, htq, h5, htpos, hs0, hqR]
  -- convert to the statement about `|φ − p/q|`
  have hdiv : |UBP.phi - (p : ℝ) / (q : ℝ)| = t / (q : ℝ) := by
    rw [ht, abs_sub_comm]
    rw [show (p : ℝ) - (q : ℝ) * UBP.phi = ((p : ℝ) / q - UBP.phi) * q by field_simp]
    rw [abs_mul, abs_of_pos hqR]
    field_simp
  rw [hdiv]
  have hrw : 1 / (3 * (q : ℝ) ^ 2) = (1 / (3 * (q : ℝ))) / (q : ℝ) := by
    field_simp
  rw [hrw]
  gcongr

/-- **P4-6.**  `φ` is not a Liouville number: being algebraic, it admits no
approximation of arbitrarily high order.  Together with `phi_badly_approximable`
this places `φ` at the *opposite* extreme from the Liouville numbers. -/
theorem phi_not_liouville : ¬ Liouville UBP.phi := by
  intro h
  have halg : IsAlgebraic ℤ UBP.phi := by
    refine ⟨Polynomial.X ^ 2 - Polynomial.X - 1, ?_, ?_⟩
    · intro hzero
      have := congrArg (fun P : Polynomial ℤ => P.coeff 2) hzero
      simp [Polynomial.coeff_X, Polynomial.coeff_one] at this
    · have hsq : UBP.phi ^ 2 = UBP.phi + 1 := UBP.phi_sq
      simp only [map_sub, map_pow, Polynomial.aeval_X, Polynomial.aeval_one]
      rw [hsq]
      ring
  exact h.transcendental halg

end UBPProjection
