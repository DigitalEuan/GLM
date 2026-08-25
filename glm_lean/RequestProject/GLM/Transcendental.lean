/-
# The error budgets the transcendental layer is built on

`Computable.lean` says what is computable about a value that is only ever
approximated: addition and multiplication are unproblematic, division needs a
nonzero witness, and equality is never decided.  `exp`, `log`, `sin`, `cos`
and a real power `x ^ y` need one more thing each — a statement of how
precisely the *argument* must be known to return the value to a stated
precision.  Those statements are the error budgets that
`reasoning.transcendental` divides its precision among, and they are proved
here.

* `exp_error_le` — `|exp x - exp a| ≤ exp (max x a) * |x - a|`.  The factor is
  what the implementation multiplies its argument precision by before calling
  the series, and it is the reason the cost of `exp` grows with the argument.
* `sin_error_le`, `cos_error_le` — both functions are 1-Lipschitz, so one
  extra bit of argument precision is enough.  No budget grows here.
* `log_error_le` — `|log x - log a| ≤ |x - a| / c` whenever `c` bounds both
  arguments below.  The bound *needs* that `c`: it is the positivity witness,
  and it plays exactly the role the nonzero witness plays for division.
* `pos_iff_witness` — and a positivity witness is precisely what positivity
  is, so requiring one is not a weakness of the search.  Together with
  `GLM.Info.witness_depth_not_uniform` (no fixed depth suffices) this says the
  refusal of `log` at a value that has not moved above zero is the exact shape
  of what is computable, not a gap.
* `log_mul_two_pow` — the range reduction the logarithm kernel performs:
  writing `a = f * 2 ^ s` turns `log a` into `log f + s * log 2`, and the
  series is only ever asked for an `f` in `[1, 2)`.
* `rpow_eq_exp_mul_log` — the power route: for a positive base, `x ^ y` *is*
  `exp (y * log x)`, which is why the real power inherits the positivity
  witness rather than needing one of its own.
* `rpow_natCast_eq_pow` — and on an integer exponent the two routes agree, so
  the grammar's split between an integer power and a real one is a choice of
  algorithm and not a change of meaning.
-/
import Mathlib

namespace GLM.Info

/-- **The exponential's error budget.**  Knowing the argument to within `ε`
gives the value to within `exp (max x a) * ε`.  The proof is convexity in the
form `1 + t ≤ exp t`, so the constant is the value itself and not an
asymptotic stand-in: it is the number the implementation divides its precision
by before summing the series. -/
theorem exp_error_le (x a : ℝ) :
    |Real.exp x - Real.exp a| ≤ Real.exp (max x a) * |x - a| := by
  rcases le_total a x with hax | hax
  · have hmax : max x a = x := max_eq_left hax
    have habs : |x - a| = x - a := abs_of_nonneg (by linarith)
    have key : Real.exp x * ((a - x) + 1) ≤ Real.exp a := by
      have h := Real.add_one_le_exp (a - x)
      have hpos : (0 : ℝ) < Real.exp x := Real.exp_pos x
      calc Real.exp x * ((a - x) + 1) ≤ Real.exp x * Real.exp (a - x) := by
            exact mul_le_mul_of_nonneg_left h hpos.le
        _ = Real.exp a := by rw [← Real.exp_add]; ring_nf
    rw [hmax, habs, abs_le]
    constructor <;> nlinarith [Real.exp_pos x, Real.exp_le_exp.mpr hax]
  · have hmax : max x a = a := max_eq_right hax
    have habs : |x - a| = a - x := by
      rw [abs_sub_comm]; exact abs_of_nonneg (by linarith)
    have key : Real.exp a * ((x - a) + 1) ≤ Real.exp x := by
      have h := Real.add_one_le_exp (x - a)
      have hpos : (0 : ℝ) < Real.exp a := Real.exp_pos a
      calc Real.exp a * ((x - a) + 1) ≤ Real.exp a * Real.exp (x - a) := by
            exact mul_le_mul_of_nonneg_left h hpos.le
        _ = Real.exp x := by rw [← Real.exp_add]; ring_nf
    rw [hmax, habs, abs_le]
    constructor <;> nlinarith [Real.exp_pos a, Real.exp_le_exp.mpr hax]

/-- **The sine costs one extra bit.**  `sin` is 1-Lipschitz, so an argument
known to `2⁻⁽ᵏ⁺¹⁾` gives the value to `2⁻ᵏ` with room to spare. -/
theorem sin_error_le (x a : ℝ) : |Real.sin x - Real.sin a| ≤ |x - a| := by
  simpa [Real.dist_eq] using Real.lipschitzWith_sin.dist_le_mul x a

/-- **And so does the cosine**, for the same reason. -/
theorem cos_error_le (x a : ℝ) : |Real.cos x - Real.cos a| ≤ |x - a| := by
  simpa [Real.dist_eq] using Real.lipschitzWith_cos.dist_le_mul x a

/-- **The logarithm's error budget, and the witness it needs.**  If `c > 0`
bounds both arguments below, the logarithm is `1/c`-Lipschitz between them.
The hypothesis is unavoidable: as the arguments approach zero the constant
blows up, which is why `log` must be handed a positivity witness rather than
guess one. -/
theorem log_error_le {x a c : ℝ} (hc : 0 < c) (hx : c ≤ x) (ha : c ≤ a) :
    |Real.log x - Real.log a| ≤ |x - a| / c := by
  have hx0 : 0 < x := lt_of_lt_of_le hc hx
  have ha0 : 0 < a := lt_of_lt_of_le hc ha
  -- One direction, then the same argument with the roles exchanged.
  have step : ∀ u v : ℝ, c ≤ v → 0 < v → v ≤ u →
      Real.log u - Real.log v ≤ (u - v) / c := by
    intro u v hcv hv hvu
    have hu : 0 < u := lt_of_lt_of_le hv hvu
    have hquot : Real.log (u / v) ≤ u / v - 1 :=
      Real.log_le_sub_one_of_pos (by positivity)
    have hsplit : Real.log (u / v) = Real.log u - Real.log v :=
      Real.log_div (ne_of_gt hu) (ne_of_gt hv)
    have hstep : u / v - 1 = (u - v) / v := by field_simp
    have hmono : (u - v) / v ≤ (u - v) / c := by
      gcongr
      linarith
    rw [hsplit, hstep] at hquot
    linarith
  rcases le_total a x with hax | hax
  · have h1 := step x a ha ha0 hax
    have hlog : Real.log a ≤ Real.log x := Real.log_le_log ha0 hax
    have habs : |x - a| = x - a := abs_of_nonneg (by linarith)
    rw [habs, abs_of_nonneg (by linarith : (0 : ℝ) ≤ Real.log x - Real.log a)]
    exact h1
  · have h1 := step a x hx hx0 hax
    have hlog : Real.log x ≤ Real.log a := Real.log_le_log hx0 hax
    have habs : |x - a| = a - x := by
      rw [abs_sub_comm]; exact abs_of_nonneg (by linarith)
    rw [habs, abs_sub_comm,
      abs_of_nonneg (by linarith : (0 : ℝ) ≤ Real.log a - Real.log x)]
    exact h1

/-- **A positivity witness is exactly what positivity is.**  A real is
positive precisely when some dyadic `2⁻ᵐ` sits below it — the same shape as
`nonzero_iff_witness`, and the reason `log` refuses in the same way division
does. -/
theorem pos_iff_witness (x : ℝ) : 0 < x ↔ ∃ m : ℕ, (1 : ℝ) / 2 ^ m ≤ x := by
  constructor
  · intro hx
    obtain ⟨n, hn⟩ := exists_nat_gt (1 / x)
    have hle : (n : ℝ) ≤ 2 ^ n := by
      exact_mod_cast (Nat.lt_two_pow_self (n := n)).le
    refine ⟨n, ?_⟩
    have h2 : (0 : ℝ) < 2 ^ n := by positivity
    rw [div_le_iff₀ h2]
    rw [div_lt_iff₀ hx] at hn
    nlinarith
  · rintro ⟨m, hm⟩
    have : (0 : ℝ) < 1 / 2 ^ m := by positivity
    linarith

/-- **The range reduction the kernel performs.**  Writing the argument as
`f * 2 ^ s` moves the series onto an `f` in `[1, 2)`, where it converges
fastest, at the cost of `s` copies of `log 2` — which is itself computed once,
as `2 * atanh (1/3)`. -/
theorem log_mul_two_pow {f : ℝ} (hf : 0 < f) (s : ℕ) :
    Real.log (f * 2 ^ s) = Real.log f + s * Real.log 2 := by
  rw [Real.log_mul (ne_of_gt hf) (by positivity), Real.log_pow]

/-- **The power route.**  For a positive base the real power *is* the
exponential of the scaled logarithm, so `x ^ y` needs no machinery of its own
— and inherits the positivity witness the logarithm needs. -/
theorem rpow_eq_exp_mul_log {x : ℝ} (hx : 0 < x) (y : ℝ) :
    x ^ y = Real.exp (y * Real.log x) := by
  rw [Real.rpow_def_of_pos hx, mul_comm]

/-- **On an integer exponent the two routes agree.**  The grammar computes an
integer power by repeated multiplication and a general one through
`exp`/`log`; this says the split is a choice of algorithm, not of meaning. -/
theorem rpow_natCast_eq_pow (x : ℝ) (n : ℕ) : x ^ (n : ℝ) = x ^ n :=
  Real.rpow_natCast x n

end GLM.Info
