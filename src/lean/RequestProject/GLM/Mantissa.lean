/-
# Where floating-point drift actually comes from

The unification blueprint's section 5.1 asks where a float's precision goes.
The Python module `glm_universal/reasoning/mantissa.py` measures it; this file
proves the two statements that measurement rests on.

The instrument is the **doubling map** `x ↦ 2x mod 1`, which reads off one bit
of a binary expansion per step.  Every step of it is exact in binary floating
point — doubling only moves the exponent, and subtracting `1` from a value in
`[1, 2)` loses nothing — so whatever a float does under this map cannot be
blamed on any later rounding.  The point is that it fails anyway, and that the
failure is total.

* `dyadicOrbit_eq`, `dyadicOrbit_collapses`, `dyadicOrbit_zero_stays` — a
  dyadic rational with `k` bits after the point reaches `0` in `k` steps and
  stays there.  A float *is* a dyadic rational, so a float's orbit always
  dies.
* `oddOrbit_ne_zero` — the exact orbit of `1 / p`, for odd `p > 1`, never
  reaches `0`.
* `oddOrbit_periodic`, `exists_period` — it is periodic, and a period is any
  `d` with `2 ^ d ≡ 1 mod p`; one exists by Euler's theorem, and the least
  one is the multiplicative order of `2` mod `p`, which is the blueprint's
  "exact binary period" and the frequency of the drift.
* `dyadic_ne_odd_orbit` — the two behaviours cannot be confused: no dyadic
  orbit is the orbit of `1 / p`.

Together: the exact value keeps oscillating for ever with a period that is a
property of `p`, and the rounded value stops.  All of the loss is spent in the
single act of rounding, and no amount of exact arithmetic afterwards recovers
any of it.
-/

import Mathlib

namespace GLM.Mantissa

/-! ## 1.  The doubling map on the dyadic rationals

A dyadic rational in `[0, 1)` with `k` bits after the point is `m / 2 ^ k`
with `m < 2 ^ k`, and the doubling map `x ↦ 2x mod 1` acts on the numerator as
`m ↦ 2 * m mod 2 ^ k`.  Working with the numerator keeps everything in `ℕ`. -/

/-- One step of the doubling map on the numerator of a `k`-bit dyadic. -/
def dyadicStep (k m : ℕ) : ℕ := 2 * m % 2 ^ k

/-- `n` steps of the doubling map. -/
def dyadicOrbit (k : ℕ) : ℕ → ℕ → ℕ
  | 0, m => m
  | n + 1, m => dyadicStep k (dyadicOrbit k n m)

@[simp] theorem dyadicOrbit_zero (k m : ℕ) : dyadicOrbit k 0 m = m := rfl

@[simp] theorem dyadicOrbit_succ (k n m : ℕ) :
    dyadicOrbit k (n + 1) m = dyadicStep k (dyadicOrbit k n m) := rfl

/-- After `n` steps the numerator is `2 ^ n * m`, reduced mod `2 ^ k`. -/
theorem dyadicOrbit_eq (k m : ℕ) (hm : m < 2 ^ k) :
    ∀ n, dyadicOrbit k n m = 2 ^ n * m % 2 ^ k
  | 0 => by simpa [dyadicOrbit] using (Nat.mod_eq_of_lt hm).symm
  | n + 1 => by
      have h : dyadicOrbit k n m = 2 ^ n * m % 2 ^ k := dyadicOrbit_eq k m hm n
      have h2 : (2 * (2 ^ n * m % 2 ^ k)) % 2 ^ k = (2 * (2 ^ n * m)) % 2 ^ k :=
        Nat.ModEq.mul_left 2 (Nat.mod_modEq _ _)
      simp only [dyadicOrbit, dyadicStep, h, h2]
      ring_nf

/-- **A float's orbit dies.**  A dyadic with `k` bits after the point reaches
`0` after exactly `k` steps of the doubling map. -/
theorem dyadicOrbit_collapses (k m : ℕ) (hm : m < 2 ^ k) :
    dyadicOrbit k k m = 0 := by
  rw [dyadicOrbit_eq k m hm, Nat.mul_mod_right]

/-- And once there it stays there: from then on the float reports a constant
where the exact value goes on moving. -/
theorem dyadicOrbit_zero_stays (k n : ℕ) : dyadicOrbit k n 0 = 0 := by
  induction n with
  | zero => rfl
  | succ n ih => simp [dyadicStep, ih]

/-- The collapse is permanent: every step at or after `k` is `0`. -/
theorem dyadicOrbit_eq_zero_of_le (k m n : ℕ) (hm : m < 2 ^ k) (hn : k ≤ n) :
    dyadicOrbit k n m = 0 := by
  obtain ⟨j, rfl⟩ := Nat.exists_eq_add_of_le hn
  induction j with
  | zero => simpa using dyadicOrbit_collapses k m hm
  | succ j ih => simp [← Nat.add_assoc, dyadicStep, ih]

/-! ## 2.  The exact orbit of `1 / p` for odd `p`

`1 / p` is not dyadic.  Its orbit under the doubling map is carried by the
residues `2 ^ n mod p`: the value at step `n` is `(2 ^ n mod p) / p`. -/

/-- The numerator of the exact orbit of `1 / p` at step `n`. -/
def oddOrbit (p n : ℕ) : ℕ := 2 ^ n % p

@[simp] theorem oddOrbit_zero_step {p : ℕ} (hp : 1 < p) : oddOrbit p 0 = 1 := by
  simp [oddOrbit, Nat.mod_eq_of_lt hp]

/-- **The exact orbit never dies.**  For odd `p > 1` no step of the orbit of
`1 / p` is `0` — in contrast with every dyadic orbit. -/
theorem oddOrbit_ne_zero {p : ℕ} (hp : 1 < p) (hodd : p % 2 = 1) (n : ℕ) :
    oddOrbit p n ≠ 0 := by
  intro h
  have hdvd : p ∣ 2 ^ n := Nat.dvd_iff_mod_eq_zero.mpr h
  have hcop2 : Nat.Coprime p 2 :=
    Nat.coprime_two_right.mpr (Nat.odd_iff.mpr hodd)
  have hcop : Nat.Coprime p (2 ^ n) := hcop2.pow_right n
  have hone : p = 1 := hcop.eq_one_of_dvd hdvd
  omega

/-- **The exact orbit is periodic**: any `d` with `2 ^ d ≡ 1 mod p` is a
period, and the least such `d` is the multiplicative order of `2` mod `p` —
the blueprint's exact binary period of `1 / p`. -/
theorem oddOrbit_periodic {p d : ℕ} (hd : 2 ^ d % p = 1) (n : ℕ) :
    oddOrbit p (n + d) = oddOrbit p n := by
  unfold oddOrbit
  rw [pow_add, Nat.mul_mod, hd, mul_one]
  simp

/-- A period exists, by Euler's theorem: `d = φ(p)` will do. -/
theorem exists_period {p : ℕ} (hp : 1 < p) (hodd : p % 2 = 1) :
    ∃ d, 0 < d ∧ ∀ n, oddOrbit p (n + d) = oddOrbit p n := by
  have hcop : Nat.Coprime 2 p :=
    (Nat.coprime_two_right.mpr (Nat.odd_iff.mpr hodd)).symm
  have hEuler : 2 ^ Nat.totient p % p = 1 % p := Nat.ModEq.pow_totient hcop
  refine ⟨Nat.totient p, Nat.totient_pos.mpr (by omega), fun n => ?_⟩
  exact oddOrbit_periodic (by rwa [Nat.mod_eq_of_lt hp] at hEuler) n

/-- The two behaviours cannot be confused: a dyadic orbit is eventually `0`
and the orbit of `1 / p` never is, so no dyadic reproduces it. -/
theorem dyadic_ne_odd_orbit {p k m : ℕ} (hp : 1 < p) (hodd : p % 2 = 1)
    (hm : m < 2 ^ k) : ∃ n, dyadicOrbit k n m ≠ oddOrbit p n :=
  ⟨k, by
    rw [dyadicOrbit_collapses k m hm]
    exact fun h => oddOrbit_ne_zero hp hodd k h.symm⟩

end GLM.Mantissa
