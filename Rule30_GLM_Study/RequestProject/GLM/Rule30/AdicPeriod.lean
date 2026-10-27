module

public import RequestProject.GLM.Rule30.AdicTower

/-!
# The layer ↔ period dictionary of the 2-adic tower (Round 47)

`AdicTower.lean` proves that a column is eventually periodic iff one relation `q·x_n ≡ r (mod 2^n)`
holds on every layer `n` of its 2-adic tower.  This file makes the correspondence quantitative:
**the denominator `q` fixes the period, and the numerator `r` bounds the preperiod.**

* `adicTrunc_add_block` : layer `n + p` is layer `n` plus `2^n` times the block of the `p` cells
  from `n` (`blockVal a n p`).
* `carry_block` : the carry over `p` layers, `t(n) = q·B(n) + 2^p·t(n+p)`.
* `carry_le_of_two_pow` : the carry is in `[-|q|, |q|]` as soon as `2^n > |r|`.
* **`period_of_dvd`** : if `q ∣ 2^p − 1` (`p ≥ 1`) and `2^N > |r|`, then
  `a(n + p) = a(n)` for every `n ≥ N + p`.  So a column that is `r/q` in `ℤ₂` has eventual period
  the order of `2` modulo `q` (or any multiple), with preperiod at most `log₂|r| + 1 + p`.
* `periodic_presentation` : conversely, an eventually periodic column (period `p`, from `N`) is
  `r/(2^p − 1)` with `|r| < 2^(N + p)`.

Together with a period certificate this turns "no short period" into "no small fraction"
(`AdicTowerData.lean`, `centerCol_not_fraction_of_period_cert`).
-/

@[expose] public section

namespace GLM.Rule30

/-- The block of `p` cells starting at `n`, read as the integer `∑_{k<p} a(n+k)·2^k`. -/
def blockVal (a : ℕ → Bool) (n p : ℕ) : ℤ := ∑ k ∈ Finset.range p, ((a (n + k)).toNat : ℤ) * 2 ^ k

theorem adicTrunc_add_block (a : ℕ → Bool) (n p : ℕ) :
    adicTrunc a (n + p) = adicTrunc a n + 2 ^ n * blockVal a n p := by
  induction p with
  | zero => simp [blockVal]
  | succ p ih =>
    rw [← add_assoc, adicTrunc_succ, ih]
    simp only [blockVal, Finset.sum_range_succ]
    ring

theorem blockVal_nonneg (a : ℕ → Bool) (n p : ℕ) : 0 ≤ blockVal a n p :=
  Finset.sum_nonneg fun k _ => by positivity

theorem blockVal_lt (a : ℕ → Bool) (n p : ℕ) : blockVal a n p < 2 ^ p := by
  induction p with
  | zero => simp [blockVal]
  | succ p ih =>
    rw [blockVal, Finset.sum_range_succ, ← blockVal, pow_succ]
    have : ((a (n + p)).toNat : ℤ) ≤ 1 := by cases a (n + p) <;> simp
    nlinarith [pow_pos (show (0 : ℤ) < 2 by norm_num) p]

theorem blockVal_emod_two (a : ℕ → Bool) (n p : ℕ) (hp : 0 < p) :
    blockVal a n p % 2 = (a n).toNat := by
  obtain ⟨p, rfl⟩ := Nat.exists_eq_add_of_lt hp
  rw [blockVal, show 0 + p + 1 = p + 1 by omega, Finset.sum_range_succ']
  have : ∑ k ∈ Finset.range p, ((a (n + (k + 1))).toNat : ℤ) * 2 ^ (k + 1) =
      2 * ∑ k ∈ Finset.range p, ((a (n + (k + 1))).toNat : ℤ) * 2 ^ k := by
    rw [Finset.mul_sum]; exact Finset.sum_congr rfl fun k _ => by ring
  rw [this, add_comm, Int.add_mul_emod_self_left]
  cases h : a n <;> simp [h]

/-- The carry over `p` layers. -/
theorem carry_block {a : ℕ → Bool} {q r : ℤ} (h : ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc a n - r)
    (n p : ℕ) : adicCarry a q r n = q * blockVal a n p + 2 ^ p * adicCarry a q r (n + p) := by
  have h0 := adicCarry_spec h n
  have h1 := adicCarry_spec h (n + p)
  rw [adicTrunc_add_block, pow_add] at h1
  have hpos : (2 : ℤ) ^ n ≠ 0 := pow_ne_zero _ (by norm_num)
  apply mul_left_cancel₀ hpos
  linear_combination h0 - h1

/-- The carry is in `[-|q|, |q|]` as soon as `2^n > |r|`. -/
theorem carry_le_of_two_pow {a : ℕ → Bool} {q r : ℤ}
    (h : ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc a n - r) {n : ℕ} (hn : |r| < 2 ^ n) :
    |adicCarry a q r n| ≤ |q| := by
  set t := adicCarry a q r with ht
  have step : ∀ n, 2 * |t (n + 1)| ≤ |t n| + |q| := by
    intro n
    have := adicCarry_succ h n
    rw [← ht] at this
    have hb : |q * ((a n).toNat : ℤ)| ≤ |q| := by
      rw [abs_mul]; cases a n <;> simp
    calc 2 * |t (n + 1)| = |t n - q * (a n).toNat| := by
          rw [← this, abs_mul]; norm_num
      _ ≤ |t n| + |q * ((a n).toNat : ℤ)| := abs_sub _ _
      _ ≤ |t n| + |q| := by linarith
  have decay : ∀ n, 2 ^ n * (|t n| - |q|) ≤ |t 0| - |q| := by
    intro n
    induction n with
    | zero => simp
    | succ n ih =>
      calc (2 : ℤ) ^ (n + 1) * (|t (n + 1)| - |q|) = 2 ^ n * (2 * |t (n + 1)| - 2 * |q|) := by
            ring
        _ ≤ 2 ^ n * (|t n| - |q|) := by
            apply mul_le_mul_of_nonneg_left _ (by positivity)
            linarith [step n, abs_nonneg q]
        _ ≤ _ := ih
  have ht0 : t 0 = r := by simp [ht, adicCarry, adicTrunc]
  by_contra hc
  push_neg at hc
  have h1 : (1 : ℤ) ≤ |t n| - |q| := by omega
  have := decay n
  rw [ht0] at this
  nlinarith [abs_nonneg q, pow_pos (show (0 : ℤ) < 2 by norm_num) n]

/-- The integer core of the period argument. -/
theorem carry_pair_step {e e' B P : ℤ} (hP : 2 ≤ P) (hB0 : 0 ≤ B) (hB : B ≤ P - 1)
    (he : |e| ≤ P - 1) (he' : |e'| ≤ P - 1) (h : e = (P - 1) * B + P * e') :
    (e ≤ 0 → e' = e ∧ B = -e) ∧ (0 < e → e' ≤ 0) := by
  rcases abs_le.1 he with ⟨he1, he2⟩
  rcases abs_le.1 he' with ⟨he'1, he'2⟩
  have hk : e + B = P * (B + e') := by rw [h]; ring
  have k0 : 0 ≤ B + e' := by
    by_contra hc; push_neg at hc
    have : P * (B + e') ≤ -P := by nlinarith
    linarith
  have k1 : B + e' ≤ 1 := by
    by_contra hc; push_neg at hc
    have : 2 * P ≤ P * (B + e') := by nlinarith
    linarith
  rcases (show B + e' = 0 ∨ B + e' = 1 by omega) with k | k
  · rw [k, mul_zero] at hk
    exact ⟨fun _ => ⟨by linarith, by linarith⟩, fun hpos => by linarith⟩
  · rw [k, mul_one] at hk
    exact ⟨fun hneg => by linarith, fun _ => by linarith⟩

/-- **The denominator fixes the period.**  If every layer satisfies `q·x_n ≡ r (mod 2^n)`,
`q ∣ 2^p − 1` with `p ≥ 1`, and `2^N > |r|`, then the column repeats with period `p` from
`N + p` on. -/
theorem period_of_dvd {a : ℕ → Bool} {q r : ℤ} (h : ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc a n - r)
    {p : ℕ} (hp : 0 < p) (hqp : q ∣ 2 ^ p - 1) {N : ℕ} (hN : |r| < 2 ^ N) :
    ∀ n ≥ N + p, a (n + p) = a n := by
  obtain ⟨M, hM⟩ := hqp
  set t := adicCarry a q r
  set P : ℤ := 2 ^ p with hPdef
  have hP : 2 ≤ P := by
    have : (2 : ℤ) ^ 1 ≤ 2 ^ p := pow_le_pow_right₀ (by norm_num) hp
    simpa using this
  -- bounded carries from `N` on, scaled by `M`
  have hbd : ∀ m ≥ N, |M * t m| ≤ P - 1 := by
    intro m hm
    have h2 : |r| < 2 ^ m := lt_of_lt_of_le hN (pow_le_pow_right₀ (by norm_num) hm)
    have hc := carry_le_of_two_pow h h2
    rw [abs_mul]
    calc |M| * |t m| ≤ |M| * |q| := mul_le_mul_of_nonneg_left hc (abs_nonneg M)
      _ = |q * M| := by rw [abs_mul, mul_comm]
      _ = P - 1 := by rw [← hM, abs_of_nonneg (by linarith)]
  have hrel : ∀ m, M * t m = (P - 1) * blockVal a m p + P * (M * t (m + p)) := by
    intro m
    have hc := carry_block h m p
    simp only [t]
    rw [hc]
    linear_combination (-(blockVal a m p)) * hM
  have hstep : ∀ m ≥ N, (M * t m ≤ 0 → M * t (m + p) = M * t m ∧ blockVal a m p = -(M * t m)) ∧
      (0 < M * t m → M * t (m + p) ≤ 0) := fun m hm =>
    carry_pair_step hP (blockVal_nonneg a m p) (by linarith [blockVal_lt a m p])
      (hbd m hm) (hbd (m + p) (by omega)) (hrel m)
  -- from `N + p` on the scaled carry is `≤ 0`
  have hneg : ∀ m ≥ N + p, M * t m ≤ 0 := by
    intro m hm
    obtain ⟨j, rfl⟩ : ∃ j, m = j + p := ⟨m - p, by omega⟩
    rcases le_or_gt (M * t j) 0 with h1 | h1
    · rw [((hstep j (by omega)).1 h1).1]; exact h1
    · exact (hstep j (by omega)).2 h1
  intro n hn
  have e1 := (hstep n (by omega)).1 (hneg n hn)
  have e2 := (hstep (n + p) (by omega)).1 (hneg (n + p) (by omega))
  have hB : blockVal a (n + p) p = blockVal a n p := by rw [e2.2, e1.1, e1.2]
  have hc : ((a (n + p)).toNat : ℤ) = (a n).toNat := by
    rw [← blockVal_emod_two a _ p hp, ← blockVal_emod_two a _ p hp, hB]
  revert hc
  cases a (n + p) <;> cases a n <;> simp

/-- **Conversely, the period fixes a denominator**: a column with `a(n + p) = a(n)` for `n ≥ N`
satisfies `(2^p − 1)·x_n ≡ r (mod 2^n)` on every layer for some `r` with `|r| < 2^(N+p)`. -/
theorem periodic_presentation {a : ℕ → Bool} {p N : ℕ} (hp : 0 < p)
    (h : ∀ n ≥ N, a (n + p) = a n) :
    ∃ r : ℤ, |r| < 2 ^ (N + p) ∧ ∀ n, (2 : ℤ) ^ n ∣ (2 ^ p - 1) * adicTrunc a n - r := by
  refine ⟨(2 ^ p - 1) * adicTrunc a N - 2 ^ N * blockVal a N p, ?_, ?_⟩
  · have h1 := blockVal_nonneg a N p
    have h2 := blockVal_lt a N p
    have h3 : 0 ≤ adicTrunc a N := by
      have := adicTrunc_add_block a 0 N
      simp only [zero_add, pow_zero, one_mul] at this
      rw [this]; simp [adicTrunc]; exact blockVal_nonneg a 0 N
    have h4 : adicTrunc a N < 2 ^ N := by
      have := adicTrunc_add_block a 0 N
      simp only [zero_add, pow_zero, one_mul] at this
      rw [this]; simp [adicTrunc]; exact blockVal_lt a 0 N
    have hP : (1 : ℤ) ≤ 2 ^ p := one_le_pow₀ (by norm_num)
    have hN : (0 : ℤ) < 2 ^ N := by positivity
    rw [abs_lt, pow_add]
    constructor <;> nlinarith
  · -- periodicity of the blocks
    have hblock : ∀ k, blockVal a (N + k * p) p = blockVal a N p := by
      intro k
      induction k with
      | zero => simp
      | succ k ih =>
        rw [← ih]
        unfold blockVal
        refine Finset.sum_congr rfl fun j _ => ?_
        rw [show N + (k + 1) * p + j = N + k * p + j + p by ring, h _ (by omega)]
    -- the relation on layers `N + k·p`
    have hlayer : ∀ k, (2 ^ p - 1) * adicTrunc a (N + k * p) -
        ((2 ^ p - 1) * adicTrunc a N - 2 ^ N * blockVal a N p) =
          2 ^ (N + k * p) * blockVal a N p := by
      intro k
      induction k with
      | zero => simp
      | succ k ih =>
        rw [show N + (k + 1) * p = N + k * p + p by ring, adicTrunc_add_block, hblock k]
        rw [show (2 ^ p - 1) * (adicTrunc a (N + k * p) + 2 ^ (N + k * p) * blockVal a N p) -
            ((2 ^ p - 1) * adicTrunc a N - 2 ^ N * blockVal a N p) =
            ((2 ^ p - 1) * adicTrunc a (N + k * p) -
            ((2 ^ p - 1) * adicTrunc a N - 2 ^ N * blockVal a N p)) +
            (2 ^ p - 1) * 2 ^ (N + k * p) * blockVal a N p by ring, ih, pow_add]
        ring
    intro n
    obtain ⟨k, hk⟩ : ∃ k, n ≤ N + k * p := ⟨n, by nlinarith⟩
    have hdvd := adicTrunc_dvd_sub a hk
    have e := hlayer k
    have : (2 : ℤ) ^ n ∣ 2 ^ (N + k * p) * blockVal a N p :=
      Dvd.dvd.mul_right (pow_dvd_pow 2 hk) _
    rw [← e] at this
    have h5 := Dvd.dvd.mul_left hdvd (2 ^ p - 1)
    have := dvd_sub this h5
    convert this using 1
    ring

end GLM.Rule30
