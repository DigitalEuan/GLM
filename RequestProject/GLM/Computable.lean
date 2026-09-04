/-
# What can be computed about a value that is only ever approximated

A real number in the GLM is held as a **process**: a rule that returns, for
any precision asked of it, an exact rational within that precision.  Addition,
subtraction and multiplication of processes are unproblematic — an error bound
on the inputs gives an error bound on the output.  Division is not, and this
file says exactly why, and exactly what repairs it.

* `nonzero_iff_witness` — a real is nonzero **iff** some `2⁻ᵐ` bounds it below.
  So what a divider needs to know is precisely that its divisor is nonzero:
  neither more nor less.
* `inv_error_le` — given that witness, division *is* computable, with the error
  bound the implementation uses: to get `1/x` within `2⁻ᵏ` it is enough to know
  `x` within `2⁻⁽ᵏ⁺²ᵐ⁺²⁾`.  This is the correctness statement of
  `reasoning.exact_real.ExactReal.reciprocal`.
* `witness_depth_not_uniform` — and no fixed search depth suffices for every
  divisor: below any depth there is a nonzero value that has not yet separated
  from zero.  The GLM's `real_expr.divide` therefore searches to a stated depth
  and *refuses* beyond it, rather than returning an answer it cannot justify.
* `eq_of_forall_abs_sub_le` — the other side of the same coin.  Two processes
  never separated are equal; but "never" quantifies over all precisions at
  once, which no finite computation reaches.  This is why `decide_equal`
  answers `False` or "not yet", and never `True`.

Together these say that the refusals the machine makes around zero are not
gaps in the implementation.  They are the exact shape of what is computable
about a value that is only ever approximated.
-/
import Mathlib

namespace GLM.Info

/-- **A witness of nonzeroness is exactly what nonzeroness is.**  A real is
nonzero precisely when some dyadic bound `2⁻ᵐ` sits below its absolute value.
That bound is the only extra thing a divider ever needs — and it cannot be read
off any finite number of approximations, which is the whole difficulty. -/
theorem nonzero_iff_witness (x : ℝ) :
    x ≠ 0 ↔ ∃ m : ℕ, (1 : ℝ) / 2 ^ m ≤ |x| := by
  constructor
  · intro hx
    have hpos : 0 < |x| := abs_pos.mpr hx
    obtain ⟨n, hn⟩ := exists_nat_gt (1 / |x|)
    have hle : (n : ℝ) ≤ 2 ^ n := by
      exact_mod_cast (Nat.lt_two_pow_self (n := n)).le
    refine ⟨n, ?_⟩
    have h2 : (0 : ℝ) < 2 ^ n := by positivity
    rw [div_le_iff₀ h2]
    rw [div_lt_iff₀ hpos] at hn
    nlinarith
  · rintro ⟨m, hm⟩ rfl
    rw [abs_zero] at hm
    have : (0 : ℝ) < 1 / 2 ^ m := by positivity
    linarith

/-- **Given the witness, division is computable — with this error bound.**
If `|x| ≥ 2⁻ᵐ` and `a` approximates `x` to within `2⁻⁽ᵏ⁺²ᵐ⁺²⁾`, then `1/a`
approximates `1/x` to within `2⁻ᵏ`.  These are exactly the exponents the
implementation uses, so this is its correctness proof and not a weaker
statement in the same direction. -/
theorem inv_error_le {x a : ℝ} {m k : ℕ}
    (hx : (1 : ℝ) / 2 ^ m ≤ |x|)
    (ha : |x - a| ≤ (1 : ℝ) / 2 ^ (k + 2 * m + 2)) :
    |1 / x - 1 / a| ≤ (1 : ℝ) / 2 ^ k := by
  set A : ℝ := 2 ^ m with hAdef
  set B : ℝ := 2 ^ k with hBdef
  have hA1 : (1 : ℝ) ≤ A := one_le_pow₀ (by norm_num)
  have hB1 : (1 : ℝ) ≤ B := one_le_pow₀ (by norm_num)
  have hA0 : (0 : ℝ) < A := lt_of_lt_of_le one_pos hA1
  have hB0 : (0 : ℝ) < B := lt_of_lt_of_le one_pos hB1
  have hAAB : A ≤ A * A * B := by nlinarith
  have hpow : (2 : ℝ) ^ (k + 2 * m + 2) = 4 * A * A * B := by
    rw [hAdef, hBdef, pow_add, pow_add, two_mul, pow_add]; ring
  rw [hpow] at ha
  have hxpos : 0 < |x| := lt_of_lt_of_le (by positivity) hx
  have hx0 : x ≠ 0 := abs_pos.mp hxpos
  -- The approximation cannot have reached zero, so `1/a` is defined.
  have hstep : (1 : ℝ) / (4 * A * A * B) ≤ 1 / (2 * A) := by
    rw [div_le_div_iff₀ (by positivity) (by positivity)]
    nlinarith
  have hage : (1 : ℝ) / (2 * A) ≤ |a| := by
    have h1 : |x| - |x - a| ≤ |a| := by
      have := abs_sub_abs_le_abs_sub x a; linarith
    have h2 : (1 : ℝ) / (2 * A) + 1 / (2 * A) = 1 / A := by field_simp; ring
    linarith [ha.trans hstep]
  have hapos : (0 : ℝ) < |a| := lt_of_lt_of_le (by positivity) hage
  have ha0 : a ≠ 0 := abs_pos.mp hapos
  have hdiff : |1 / x - 1 / a| = |x - a| / (|x| * |a|) := by
    rw [div_sub_div _ _ hx0 ha0, abs_div, abs_mul]
    simp [abs_sub_comm]
  rw [hdiff, div_le_div_iff₀ (by positivity) (by positivity)]
  have hmul : |x - a| * B ≤ (1 : ℝ) / (4 * A * A * B) * B :=
    mul_le_mul_of_nonneg_right ha hB0.le
  have heq : (1 : ℝ) / (4 * A * A * B) * B = 1 / (4 * A * A) := by field_simp
  have hprod : (1 : ℝ) / A * (1 / (2 * A)) ≤ |x| * |a| :=
    mul_le_mul hx hage (by positivity) (abs_nonneg x)
  have heq2 : (1 : ℝ) / A * (1 / (2 * A)) = 1 / (2 * A * A) := by field_simp
  have hcmp : (1 : ℝ) / (4 * A * A) ≤ 1 / (2 * A * A) := by
    apply one_div_le_one_div_of_le (by positivity)
    nlinarith
  rw [heq] at hmul
  rw [heq2] at hprod
  linarith

/-- **No fixed search depth is enough.**  However deep a divider looks, there is
a nonzero value it has not yet separated from zero, so the search for a witness
cannot be made total.  A machine that must answer at some depth can only refuse
there — and the GLM does. -/
theorem witness_depth_not_uniform (m : ℕ) :
    ∃ x : ℝ, x ≠ 0 ∧ |x| < (1 : ℝ) / 2 ^ m := by
  refine ⟨1 / 2 ^ (m + 1), by positivity, ?_⟩
  rw [abs_of_pos (by positivity)]
  have h : (2 : ℝ) ^ m < 2 ^ (m + 1) :=
    pow_lt_pow_right₀ (by norm_num) (Nat.lt_succ_self m)
  exact one_div_lt_one_div_of_lt (by positivity) h

/-- **Two processes that are never separated are equal.**  The hypothesis
quantifies over *every* precision, which is why no finite computation can
establish it: the machine reports a separation when it finds one, and "not yet
distinguished" otherwise. -/
theorem eq_of_forall_abs_sub_le {x y : ℝ}
    (h : ∀ k : ℕ, |x - y| ≤ (1 : ℝ) / 2 ^ k) : x = y := by
  by_contra hne
  obtain ⟨k, hk⟩ := (nonzero_iff_witness (x - y)).mp (sub_ne_zero.mpr hne)
  have hlt : (1 : ℝ) / 2 ^ (k + 1) < (1 : ℝ) / 2 ^ k :=
    one_div_lt_one_div_of_lt (by positivity)
      (pow_lt_pow_right₀ (by norm_num) (Nat.lt_succ_self k))
  have := h (k + 1)
  linarith

end GLM.Info
