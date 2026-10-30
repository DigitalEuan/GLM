module

public import RequestProject.GLM.Rule30.Prizes

/-!
# The 2-adic layer tower of a column (Round 47)

A column `a : ℕ → Bool` is read layer by layer: layer `n` sees the first `n` cells, packed as
the integer `adicTrunc a n = ∑_{k<n} a(k)·2^k`, i.e. a residue modulo `2^n`. Each layer refines
the one below it (`adicTrunc_dvd_sub`), so the layers form the tower

  `ℤ/2 ← ℤ/4 ← ℤ/8 ← ⋯ ← ℤ/2^n ← ⋯`

whose limit is the ring of 2-adic integers. Unlike the moduli `2, 4, 8, 144, 256` of the
escalation sketch, this tower is a *chain* under refinement.

A column is *2-adically rational* when one fixed linear relation `q·x = r` (`q ≠ 0`) holds
on every layer at once.

Main results:
* `eventuallyPeriodic_iff_adicRational` : a column is eventually periodic iff it is
  2-adically rational.
* `problem1_iff_not_adicRational` : **Rule 30 Problem 1 is equivalent to the 2-adic
  irrationality of the centre column.**
* `rational_carry_bounded` : for a rational column with odd denominator `q`, the *carry*
  `t(n) = (r - q·x_n)/2^n` eventually stays in `[-|q|, |q|]`; it is the finite-state
  machine that makes a rational column periodic.
* `problem1_iff_padic_irrational` : the same in the limit `ℤ₂` of the tower.
* `AdicTowerData.lean` (CERT) : a finite certificate read on layer 256 of the tower: the
  centre column is not `r/q` for any `1 ≤ |q| ≤ 2^16`, `|r| ≤ 2^200`
  (`centerCol_not_small_rational`).
-/

@[expose] public section

namespace GLM.Rule30

/-- Layer `n` of the 2-adic tower: the integer `∑_{k<n} a(k)·2^k`. -/
def adicTrunc (a : ℕ → Bool) : ℕ → ℤ
  | 0 => 0
  | n + 1 => adicTrunc a n + (a n).toNat * 2 ^ n

/-- The column is *2-adically rational*: a single relation `q·x ≡ r` holds on every layer. -/
def AdicRational (a : ℕ → Bool) : Prop :=
  ∃ q r : ℤ, q ≠ 0 ∧ ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc a n - r

theorem adicTrunc_succ (a : ℕ → Bool) (n : ℕ) :
    adicTrunc a (n + 1) = adicTrunc a n + (a n).toNat * 2 ^ n := rfl

/-- **Layers are compatible**: layer `m ≥ n` reduces to layer `n` modulo `2^n`. -/
theorem adicTrunc_dvd_sub (a : ℕ → Bool) {n m : ℕ} (h : n ≤ m) :
    (2 : ℤ) ^ n ∣ adicTrunc a m - adicTrunc a n := by
  obtain ⟨k, rfl⟩ := Nat.exists_eq_add_of_le h
  induction k with
  | zero => simp
  | succ k ih =>
    rw [← add_assoc, adicTrunc_succ,
      show adicTrunc a (n + k) + ((a (n + k)).toNat : ℤ) * 2 ^ (n + k) - adicTrunc a n
        = (adicTrunc a (n + k) - adicTrunc a n) + (a (n + k)).toNat * 2 ^ (n + k) by ring]
    exact dvd_add (ih (by omega)) (Dvd.dvd.mul_left (pow_dvd_pow 2 (by omega)) _)

/-- Periodic columns are rational: `q = 2^p - 1`. -/
theorem adicRational_of_eventuallyPeriodic {a : ℕ → Bool} (h : EventuallyPeriodic a) :
    AdicRational a := by
  obtain ⟨p, hp, N, hN⟩ := h
  have hC : ∀ n ≥ N, adicTrunc a (n + p) - 2 ^ p * adicTrunc a n =
      adicTrunc a (N + p) - 2 ^ p * adicTrunc a N := by
    intro n hn
    induction n, hn using Nat.le_induction with
    | base => rfl
    | succ n hn ih =>
      rw [show n + 1 + p = (n + p) + 1 by ring, adicTrunc_succ, adicTrunc_succ, hN n hn, ← ih,
        pow_add]
      ring
  refine ⟨2 ^ p - 1, -(adicTrunc a (N + p) - 2 ^ p * adicTrunc a N), ?_, ?_⟩
  · have : (2 : ℤ) ≤ 2 ^ p := by
      calc (2 : ℤ) = 2 ^ 1 := by norm_num
        _ ≤ 2 ^ p := pow_le_pow_right₀ (by norm_num) hp
    omega
  · have big : ∀ n ≥ N, (2 : ℤ) ^ n ∣ (2 ^ p - 1) * adicTrunc a n -
        -(adicTrunc a (N + p) - 2 ^ p * adicTrunc a N) := by
      intro n hn
      rw [← hC n hn, show (2 ^ p - 1) * adicTrunc a n -
          -(adicTrunc a (n + p) - 2 ^ p * adicTrunc a n) = adicTrunc a (n + p) - adicTrunc a n by
          ring]
      exact adicTrunc_dvd_sub a (by omega)
    intro n
    rcases le_or_gt N n with hn | hn
    · exact big n hn
    · have h1 := (pow_dvd_pow (2 : ℤ) hn.le).trans (big N le_rfl)
      have h2 := adicTrunc_dvd_sub a hn.le
      have := dvd_sub h1 (Dvd.dvd.mul_left h2 (2 ^ p - 1))
      convert this using 1
      ring

/-- A rational column has an odd-denominator presentation. -/
theorem adicRational_odd {a : ℕ → Bool} (h : AdicRational a) :
    ∃ q r : ℤ, q % 2 = 1 ∧ ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc a n - r := by
  obtain ⟨q, r, hq, h⟩ := h
  induction hk : q.natAbs using Nat.strong_induction_on generalizing q r with
  | _ k ih =>
    rcases Int.emod_two_eq_zero_or_one q with h0 | h1
    · obtain ⟨q₀, rfl⟩ : 2 ∣ q := Int.dvd_of_emod_eq_zero h0
      have hr : 2 ∣ r := by
        have := h 1
        rw [pow_one] at this
        have h2 := dvd_sub (Dvd.dvd.mul_right (dvd_mul_right 2 q₀) (adicTrunc a 1)) this
        simpa using h2
      obtain ⟨r₀, rfl⟩ := hr
      have hq₀ : q₀ ≠ 0 := by omega
      have hlt : q₀.natAbs < k := by
        rw [← hk, Int.natAbs_mul]
        have := Int.natAbs_pos.2 hq₀
        simp only [Int.reduceAbs]
        omega
      refine ih q₀.natAbs hlt q₀ r₀ hq₀ ?_ rfl
      intro n
      have h3 := h (n + 1)
      rw [show 2 * q₀ * adicTrunc a (n + 1) - 2 * r₀ = 2 * (q₀ * adicTrunc a (n + 1) - r₀) by
        ring, pow_succ, mul_comm _ (2 : ℤ)] at h3
      have h4 := (mul_dvd_mul_iff_left (by norm_num : (2 : ℤ) ≠ 0)).1 h3
      have h5 := Dvd.dvd.mul_left (adicTrunc_dvd_sub a (Nat.le_succ n)) q₀
      have := dvd_sub h4 h5
      convert this using 1
      ring
    · exact ⟨q, r, h1, h⟩


/-- The carry of a rational presentation. -/
def adicCarry (a : ℕ → Bool) (q r : ℤ) (n : ℕ) : ℤ := (r - q * adicTrunc a n) / 2 ^ n

/-- For an odd-denominator presentation, the carry eventually lies in `[-|q|, |q|]`. -/
theorem adicCarry_spec {a : ℕ → Bool} {q r : ℤ}
    (h : ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc a n - r) (n : ℕ) :
    2 ^ n * adicCarry a q r n = r - q * adicTrunc a n := by
  unfold adicCarry
  have : (2 : ℤ) ^ n ∣ r - q * adicTrunc a n := by
    have := (h n).neg_right; convert this using 1; ring
  exact Int.mul_ediv_cancel' this

/-- The carry recurrence: `2·t(n+1) = t(n) - q·a(n)`. -/
theorem adicCarry_succ {a : ℕ → Bool} {q r : ℤ}
    (h : ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc a n - r) (n : ℕ) :
    2 * adicCarry a q r (n + 1) = adicCarry a q r n - q * (a n).toNat := by
  have h1 := adicCarry_spec h (n + 1)
  have h0 := adicCarry_spec h n
  rw [adicTrunc_succ, pow_succ] at h1
  have hpos : (2 : ℤ) ^ n ≠ 0 := pow_ne_zero _ (by norm_num)
  apply mul_left_cancel₀ hpos
  linear_combination h1 - h0

/-- The carry eventually lies in `[-|q|, |q|]`. -/
theorem rational_carry_bounded {a : ℕ → Bool} {q r : ℤ}
    (h : ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc a n - r) :
    ∃ N, ∀ n ≥ N, |adicCarry a q r n| ≤ |q| := by
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
  refine ⟨(|t 0|).toNat, fun n hn => ?_⟩
  by_contra hc
  push_neg at hc
  have h1 : (1 : ℤ) ≤ |t n| - |q| := by omega
  have h2 : (n : ℤ) < 2 ^ n := by exact_mod_cast Nat.lt_two_pow_self
  have h3 : |t 0| ≤ n := by omega
  have := decay n
  nlinarith [abs_nonneg q, abs_nonneg (t 0)]

/-- Rational columns are eventually periodic. -/
theorem eventuallyPeriodic_of_adicRational {a : ℕ → Bool} (h : AdicRational a) :
    EventuallyPeriodic a := by
  obtain ⟨q, r, hq, h⟩ := adicRational_odd h
  set t := adicCarry a q r with ht
  have hmod : ∀ n, t n % 2 = (a n).toNat := by
    intro n
    have := adicCarry_succ h n
    rw [← ht] at this
    have hq' : q = 2 * (q / 2) + 1 := by omega
    cases han : a n <;> simp [han] at this ⊢ <;> omega
  have hpar : ∀ n, a n = decide (t n % 2 = 1) := by
    intro n
    rw [hmod]
    cases a n <;> simp
  have hF : ∀ n, t (n + 1) = (t n - q * (t n % 2)) / 2 := by
    intro n
    have := adicCarry_succ h n
    rw [← ht] at this
    rw [hmod]
    cases han : a n <;> simp [han] at this ⊢ <;> omega
  obtain ⟨N, hN⟩ := rational_carry_bounded h
  let g : ℕ → Set.Icc (-|q|) |q| := fun n =>
    ⟨t (N + n), by have := hN (N + n) (by omega); exact abs_le.1 this⟩
  obtain ⟨i, j, hij, hg⟩ := Finite.exists_ne_map_eq_of_infinite g
  have key : ∀ i j, t (N + i) = t (N + j) → ∀ k, t (N + i + k) = t (N + j + k) := by
    intro i j e k
    induction k with
    | zero => simpa using e
    | succ k ih => rw [← add_assoc, ← add_assoc, hF, hF, ih]
  have e : t (N + i) = t (N + j) := congrArg Subtype.val hg
  rcases lt_or_gt_of_ne hij with hlt | hlt
  · refine ⟨j - i, by omega, N + i, fun n hn => ?_⟩
    obtain ⟨k, rfl⟩ := Nat.exists_eq_add_of_le hn
    rw [hpar, hpar, show N + i + k + (j - i) = N + j + k by omega, key i j e k]
  · refine ⟨i - j, by omega, N + j, fun n hn => ?_⟩
    obtain ⟨k, rfl⟩ := Nat.exists_eq_add_of_le hn
    rw [hpar, hpar, show N + j + k + (i - j) = N + i + k by omega, key j i e.symm k]

/-- **Eventually periodic ⇔ 2-adically rational.** -/
theorem eventuallyPeriodic_iff_adicRational (a : ℕ → Bool) :
    EventuallyPeriodic a ↔ AdicRational a :=
  ⟨adicRational_of_eventuallyPeriodic, eventuallyPeriodic_of_adicRational⟩

/-- **Rule 30 Problem 1 ⇔ the centre column is 2-adically irrational.** -/
theorem problem1_iff_not_adicRational : Problem1 ↔ ¬ AdicRational centerCol := by
  unfold Problem1
  rw [eventuallyPeriodic_iff_adicRational]

/-! ## The limit of the tower: the 2-adic integer of a column -/

section Padic

open Filter Topology

/-- The `k`-th term `a(k)·2^k` of the 2-adic expansion. -/
noncomputable def adicTerm (a : ℕ → Bool) (k : ℕ) : ℤ_[2] := ((a k).toNat : ℤ_[2]) * 2 ^ k

theorem adicTerm_norm_le (a : ℕ → Bool) (k : ℕ) :
    ‖adicTerm a k‖ ≤ ((2 : ℕ) : ℝ) ^ (-(k : ℤ)) := by
  unfold adicTerm
  rw [norm_mul]
  have h1 := PadicInt.norm_p_pow (p := 2) k
  have h2 := PadicInt.norm_le_one (((a k).toNat : ℕ) : ℤ_[2])
  push_cast at h1 ⊢
  rw [h1]
  calc ‖(((a k).toNat : ℕ) : ℤ_[2])‖ * (2 : ℝ) ^ (-(k : ℤ)) ≤ 1 * (2 : ℝ) ^ (-(k : ℤ)) :=
        mul_le_mul_of_nonneg_right h2 (by positivity)
    _ = _ := one_mul _

theorem adicTerm_summable (a : ℕ → Bool) : Summable (adicTerm a) := by
  apply NonarchimedeanAddGroup.summable_of_tendsto_cofinite_zero
  rw [Nat.cofinite_eq_atTop]
  apply squeeze_zero_norm (adicTerm_norm_le a)
  have : Tendsto (fun k : ℕ => ((1 : ℝ) / 2) ^ k) atTop (𝓝 0) :=
    tendsto_pow_atTop_nhds_zero_of_lt_one (by norm_num) (by norm_num)
  refine this.congr fun k => ?_
  push_cast
  rw [zpow_neg, zpow_natCast, one_div, inv_pow]

/-- **The 2-adic integer of a column**: `x = ∑ a(k)·2^k ∈ ℤ₂`, the limit of the layer tower. -/
noncomputable def adicValue (a : ℕ → Bool) : ℤ_[2] := ∑' k, adicTerm a k

theorem adicTerm_partial (a : ℕ → Bool) (n : ℕ) :
    ∑ k ∈ Finset.range n, adicTerm a k = ((adicTrunc a n : ℤ) : ℤ_[2]) := by
  induction n with
  | zero => simp [adicTrunc]
  | succ n ih =>
    rw [Finset.sum_range_succ, ih, adicTrunc_succ, adicTerm]
    push_cast
    ring

/-- Layer `n` of the tower approximates the 2-adic value to precision `2^{-n}`. -/
theorem adicValue_sub_trunc_norm_le (a : ℕ → Bool) (n : ℕ) :
    ‖adicValue a - ((adicTrunc a n : ℤ) : ℤ_[2])‖ ≤ ((2 : ℕ) : ℝ) ^ (-(n : ℤ)) := by
  have T := (adicTerm_summable a).hasSum.tendsto_sum_nat
  simp only [adicTerm_partial] at T
  have T2 := (T.sub_const (((adicTrunc a n : ℤ) : ℤ_[2]))).norm
  apply le_of_tendsto T2
  filter_upwards [eventually_ge_atTop n] with m hm
  rw [← Int.cast_sub]
  exact PadicInt.norm_int_le_pow_iff_dvd.2 (by exact_mod_cast adicTrunc_dvd_sub a hm)

theorem eq_zero_of_norm_le_two_pow {z : ℤ_[2]} (h : ∀ n : ℕ, ‖z‖ ≤ ((2 : ℕ) : ℝ) ^ (-(n : ℤ))) :
    z = 0 := by
  have : Tendsto (fun k : ℕ => ((2 : ℕ) : ℝ) ^ (-(k : ℤ))) atTop (𝓝 0) := by
    have := tendsto_pow_atTop_nhds_zero_of_lt_one (r := (1 : ℝ) / 2) (by norm_num) (by norm_num)
    refine this.congr fun k => ?_
    push_cast
    rw [zpow_neg, zpow_natCast, one_div, inv_pow]
  have h0 : ‖z‖ ≤ 0 := ge_of_tendsto' this h
  exact norm_le_zero_iff.1 h0

/-- A single relation `q·x = r` in `ℤ₂` holds on every layer of the tower. -/
theorem layers_of_padic_eq {a : ℕ → Bool} {q r : ℤ} (h : (q : ℤ_[2]) * adicValue a = r) :
    ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc a n - r := by
  intro n
  have := PadicInt.norm_int_le_pow_iff_dvd (p := 2) (k := q * adicTrunc a n - r) (n := n)
  push_cast at this
  refine this.1 ?_
  have e : (q : ℤ_[2]) * (adicTrunc a n : ℤ_[2]) - r =
      -(q * (adicValue a - ((adicTrunc a n : ℤ) : ℤ_[2]))) := by rw [← h]; ring
  rw [e, norm_neg, norm_mul]
  have := adicValue_sub_trunc_norm_le a n
  push_cast at this
  calc ‖(q : ℤ_[2])‖ * ‖adicValue a - (adicTrunc a n : ℤ_[2])‖ ≤ 1 * (2 : ℝ) ^ (-(n : ℤ)) :=
        mul_le_mul (PadicInt.norm_le_one _) this (norm_nonneg _) zero_le_one
    _ = _ := one_mul _

/-- **Rationality on every layer ⇔ rationality in `ℤ₂`.** -/
theorem adicRational_iff_padic (a : ℕ → Bool) :
    AdicRational a ↔ ∃ q r : ℤ, q ≠ 0 ∧ (q : ℤ_[2]) * adicValue a = r := by
  constructor
  · rintro ⟨q, r, hq, h⟩
    refine ⟨q, r, hq, ?_⟩
    rw [← sub_eq_zero]
    apply eq_zero_of_norm_le_two_pow
    intro n
    have e : (q : ℤ_[2]) * adicValue a - r =
        q * (adicValue a - ((adicTrunc a n : ℤ) : ℤ_[2])) +
          (((q * adicTrunc a n - r : ℤ)) : ℤ_[2]) := by push_cast; ring
    rw [e]
    refine (PadicInt.nonarchimedean _ _).trans (max_le ?_ ?_)
    · rw [norm_mul]
      calc ‖(q : ℤ_[2])‖ * ‖adicValue a - ((adicTrunc a n : ℤ) : ℤ_[2])‖
          ≤ 1 * ((2 : ℕ) : ℝ) ^ (-(n : ℤ)) :=
            mul_le_mul (PadicInt.norm_le_one _) (adicValue_sub_trunc_norm_le a n)
              (norm_nonneg _) zero_le_one
        _ = _ := one_mul _
    · exact PadicInt.norm_int_le_pow_iff_dvd.2 (by exact_mod_cast h n)
  · rintro ⟨q, r, hq, h⟩
    exact ⟨q, r, hq, layers_of_padic_eq h⟩

/-- **Rule 30 Problem 1 ⇔ the 2-adic integer `∑ a(k)·2^k` of the centre column is not a
rational number** (no relation `q·x = r` with integers `q ≠ 0`, `r`). -/
theorem problem1_iff_padic_irrational :
    Problem1 ↔ ∀ q r : ℤ, q ≠ 0 → (q : ℤ_[2]) * adicValue centerCol ≠ r := by
  rw [problem1_iff_not_adicRational, adicRational_iff_padic]
  push_neg
  rfl

end Padic

end GLM.Rule30
