/-
# Why no tuning ever closes

`overlay/glm_universal/data_objects/harmonics.py` holds 28 musical intervals as
exact rational frequency ratios, and `overlay/glm_universal/reasoning/harmony.py`
measures each one against the equal-tempered step it is nearest to.  Every one
of those measurements comes out non-zero, and the register's tests pin the
individual numbers.  A test pins 28 intervals; this file says *why no interval
ever could*, and the reason is arithmetic rather than acoustic.

* `three_pow_ne_two_pow` — the kernel: `3 ^ n = 2 ^ m` forces `n = 0`.  Powers
  of three are odd, powers of two are not.
* `fifth_never_closes` — the circle of fifths is not a circle.  No stack of
  perfect fifths is a stack of octaves: `(3/2) ^ n ≠ 2 ^ m` for every `n > 0`
  and every integer `m`, so the spiral never returns.  The Python side counts
  this to `n ≤ 200` and finds nothing; here it is closed for all `n`.
* `odd_prime_ratio_ne_two_zpow` — the general statement, and the one the
  register actually needs.  If a ratio in lowest terms has **any** odd prime in
  it, no power of it is a power of two.  Equal temperament therefore misses
  every interval of the register except the unison and the octave — not by a
  small amount, but necessarily, and for every division of the octave at once,
  since the exponent `N` is arbitrary.
* `fifth_not_tempered`, `major_third_not_tempered`, `harmonic_seventh_not_tempered`
  — three named corollaries, one per prime limit.
* `pythagorean_comma_eq`, `syntonic_comma_eq`, `pythagorean_comma_ne_one` — the
  exact residues the Python report quotes, checked here rather than trusted.

The musical reading of `odd_prime_ratio_ne_two_zpow` is the classical one: a
tempered scale divides the octave into equal multiplicative steps, so every
tempered interval is `2 ^ (k / N)`, and an `N`-th root of a power of two cannot
be a ratio of integers unless it is itself a power of two.  Tuning is a
negotiation because arithmetic leaves no alternative.
-/
import Mathlib

namespace GLM.Harmony

/-! ## 1.  The kernel -/

/-- A power of three is never a power of two, unless it is `1`.

Powers of three are odd; the only odd power of two is `2 ^ 0 = 1`; and
`3 ^ n = 1` only for `n = 0`. -/
theorem three_pow_ne_two_pow (n m : ℕ) (hn : 0 < n) : (3 : ℕ) ^ n ≠ 2 ^ m := by
  intro h
  have hodd : Odd ((3 : ℕ) ^ n) := Odd.pow (by decide)
  rw [h] at hodd
  rcases Nat.eq_zero_or_pos m with hm | hm
  · subst hm
    simp only [pow_zero] at h
    have := Nat.one_lt_pow hn.ne' (by norm_num : 1 < 3)
    omega
  · exact (Nat.not_odd_iff_even.mpr ((Nat.even_pow).mpr ⟨even_two, hm.ne'⟩)) hodd

/-! ## 2.  The circle of fifths is not a circle -/

/-- **No stack of fifths is a stack of octaves.**

For every `n > 0` and every integer `m`, `(3/2) ^ n ≠ 2 ^ m`.  Twelve fifths
overshoot seven octaves by the Pythagorean comma (`pythagorean_comma_eq`
below), and no other count does better: the spiral of fifths never meets
itself. -/
theorem fifth_never_closes (n : ℕ) (hn : 0 < n) (m : ℤ) :
    ((3 : ℚ) / 2) ^ n ≠ (2 : ℚ) ^ m := by
  intro h
  have hz : ((2 : ℚ)) ^ (n : ℤ) = (2 : ℚ) ^ n := zpow_natCast 2 n
  have key : ((3 : ℚ)) ^ n = (2 : ℚ) ^ (m + n) := by
    have h1 : ((3 : ℚ) / 2) ^ n * 2 ^ (n : ℤ) = (2 : ℚ) ^ m * 2 ^ (n : ℤ) := by
      rw [h]
    rw [← zpow_add₀ (by norm_num : (2 : ℚ) ≠ 0), hz, div_pow] at h1
    field_simp at h1
    linarith [h1]
  have hgt : (1 : ℚ) < (3 : ℚ) ^ n := one_lt_pow₀ (by norm_num) hn.ne'
  rw [key] at hgt
  have hmn : 0 < m + n := by
    by_contra hc
    push_neg at hc
    have : (2 : ℚ) ^ (m + n) ≤ 1 := zpow_le_one_of_nonpos₀ (by norm_num) hc
    linarith
  obtain ⟨k, hk⟩ := Int.eq_ofNat_of_zero_le hmn.le
  rw [hk, zpow_natCast] at key
  exact three_pow_ne_two_pow n k hn (by exact_mod_cast key)

/-! ## 3.  The general obstruction -/

/-- The arithmetic core, over `ℕ`: with `x` and `y` coprime, `x ^ N = 2 ^ j * y ^ N`
leaves no room for an odd prime on either side. -/
theorem no_odd_prime_of_pow_eq_two_pow_mul_pow
    {x y j N p : ℕ} (hN : 0 < N) (hxy : Nat.Coprime x y)
    (hp : p.Prime) (hp2 : p ≠ 2) (heq : x ^ N = 2 ^ j * y ^ N)
    (hdvd : p ∣ x ∨ p ∣ y) : False := by
  -- Whichever side `p` starts on, it reaches the other, and then it divides
  -- the gcd of two coprime numbers.
  have both : p ∣ x ∧ p ∣ y := by
    rcases hdvd with hx | hy
    · have hxN : p ∣ x ^ N := dvd_pow hx hN.ne'
      rw [heq] at hxN
      rcases (Nat.Prime.dvd_mul hp).1 hxN with h2 | hyN
      · exact absurd (Nat.prime_dvd_prime_iff_eq hp Nat.prime_two |>.1
          (hp.dvd_of_dvd_pow h2)) hp2
      · exact ⟨hx, hp.dvd_of_dvd_pow hyN⟩
    · have hyN : p ∣ x ^ N := by
        rw [heq]; exact Dvd.dvd.mul_left (dvd_pow hy hN.ne') _
      exact ⟨hp.dvd_of_dvd_pow hyN, hy⟩
  have : p ∣ Nat.gcd x y := Nat.dvd_gcd both.1 both.2
  rw [hxy] at this
  exact hp.one_lt.ne' (Nat.dvd_one.1 this)

/-- **An interval with an odd prime in it is never an equal step.**

Let `a / b` be a ratio of positive integers in lowest terms, and suppose some
odd prime divides `a` or `b`.  Then for every `N > 0` and every integer `k`,
`(a / b) ^ N ≠ 2 ^ k`.

Read musically: `N`-tone equal temperament tunes its steps to `2 ^ (k / N)`, so
this says the ratio is not a step of *any* equal division of the octave, for
any number of divisions.  Only ratios built from the prime 2 alone — the
unison, the octave, and their powers — escape, which is exactly what the
harmonic register measures and `tet_error` reports as `1`. -/
theorem odd_prime_ratio_ne_two_zpow
    {a b N p : ℕ} (hb : 0 < b) (hab : Nat.Coprime a b)
    (hN : 0 < N) (hp : p.Prime) (hp2 : p ≠ 2) (hdvd : p ∣ a ∨ p ∣ b)
    (k : ℤ) : ((a : ℚ) / b) ^ N ≠ (2 : ℚ) ^ k := by
  intro h
  have hbQ : (b : ℚ) ≠ 0 := Nat.cast_ne_zero.2 hb.ne'
  have hpow : ((a : ℚ)) ^ N = (2 : ℚ) ^ k * (b : ℚ) ^ N := by
    have := congrArg (fun t : ℚ => t * (b : ℚ) ^ N) h
    simpa [div_pow, div_mul_cancel₀, pow_ne_zero _ hbQ] using this
  rcases le_or_gt 0 k with hk | hk
  · obtain ⟨j, hj⟩ := Int.eq_ofNat_of_zero_le hk
    rw [hj, zpow_natCast] at hpow
    have hnat : a ^ N = 2 ^ j * b ^ N := by exact_mod_cast hpow
    exact no_odd_prime_of_pow_eq_two_pow_mul_pow hN hab hp hp2 hnat hdvd
  · obtain ⟨j, hj⟩ := Int.eq_ofNat_of_zero_le (Int.neg_nonneg.2 hk.le)
    have hk' : k = -(j : ℤ) := by omega
    rw [hk', zpow_neg, zpow_natCast] at hpow
    have hpow' : (2 : ℚ) ^ j * (a : ℚ) ^ N = (b : ℚ) ^ N := by
      field_simp at hpow
      linarith [hpow]
    have hnat : b ^ N = 2 ^ j * a ^ N := by exact_mod_cast hpow'.symm
    exact no_odd_prime_of_pow_eq_two_pow_mul_pow hN hab.symm hp hp2 hnat
      hdvd.symm

/-! ## 4.  The register's own intervals -/

/-- The perfect fifth is not a step of any equal division of the octave. -/
theorem fifth_not_tempered (N : ℕ) (hN : 0 < N) (k : ℤ) :
    ((3 : ℚ) / 2) ^ N ≠ (2 : ℚ) ^ k := by
  have := odd_prime_ratio_ne_two_zpow (a := 3) (b := 2) (N := N) (p := 3)
    (by norm_num) (by decide) hN Nat.prime_three (by decide)
    (Or.inl dvd_rfl) k
  simpa using this

/-- The just major third is not a step of any equal division of the octave. -/
theorem major_third_not_tempered (N : ℕ) (hN : 0 < N) (k : ℤ) :
    ((5 : ℚ) / 4) ^ N ≠ (2 : ℚ) ^ k := by
  have := odd_prime_ratio_ne_two_zpow (a := 5) (b := 4) (N := N) (p := 5)
    (by norm_num) (by decide) hN (by norm_num) (by decide)
    (Or.inl dvd_rfl) k
  simpa using this

/-- The harmonic seventh is not a step of any equal division of the octave. -/
theorem harmonic_seventh_not_tempered (N : ℕ) (hN : 0 < N) (k : ℤ) :
    ((7 : ℚ) / 4) ^ N ≠ (2 : ℚ) ^ k := by
  have := odd_prime_ratio_ne_two_zpow (a := 7) (b := 4) (N := N) (p := 7)
    (by norm_num) (by decide) hN (by norm_num) (by decide)
    (Or.inl dvd_rfl) k
  simpa using this

/-! ## 5.  The two commas, exactly -/

/-- Twelve fifths overshoot seven octaves by the Pythagorean comma. -/
theorem pythagorean_comma_eq :
    ((3 : ℚ) / 2) ^ 12 / (2 : ℚ) ^ 7 = 531441 / 524288 := by
  norm_num

/-- And the overshoot is not nothing. -/
theorem pythagorean_comma_ne_one :
    ((3 : ℚ) / 2) ^ 12 / (2 : ℚ) ^ 7 ≠ 1 := by
  rw [pythagorean_comma_eq]; norm_num

/-- Four fifths overshoot the just major third by the syntonic comma. -/
theorem syntonic_comma_eq :
    ((3 : ℚ) / 2) ^ 4 / ((2 : ℚ) ^ 2 * (5 / 4)) = 81 / 80 := by
  norm_num

/-- The tempering error the harmonic register reports for the fifth, exactly:
`(3/2) ^ 12 / 2 ^ 7`, which is the Pythagorean comma again. -/
theorem fifth_tet_error : ((3 : ℚ) / 2) ^ 12 / (2 : ℚ) ^ 7 = 531441 / 524288 :=
  pythagorean_comma_eq

/-- The tempering error for the just major third, exactly. -/
theorem major_third_tet_error :
    ((5 : ℚ) / 4) ^ 12 / (2 : ℚ) ^ 4 = 244140625 / 268435456 := by
  norm_num

end GLM.Harmony
