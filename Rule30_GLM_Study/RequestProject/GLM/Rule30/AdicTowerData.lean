import RequestProject.GLM.Rule30.AdicTower
import RequestProject.GLM.Rule30.AdicPeriod
import RequestProject.GLM.Rule30.Compute
import RequestProject.GLM.HypothesisEngine.GateLoopData

/-!
# The 2-adic tower of the centre column: a finite certificate (Round 47)

(Not a `module`: the check uses `native_decide`, so the result is CERT.)

`AdicTower.lean` proves that Problem 1 is the statement "the 2-adic integer
`x = ∑ centerCol(k)·2^k` is not a rational number `r/q`" (`problem1_iff_padic_irrational`).
This file reads layer 256 of the tower and excludes every *small* fraction.

* `not_layer_rel_of_window` (FORMAL): if `q·x_n mod 2^n` lies strictly between `2^e` and
  `2^n − 2^e`, then no `r` with `|r| ≤ 2^e` satisfies `2^n ∣ q·x_n − r`.
* `adicCheck` (CERT, `adicCheck_ok`): the window condition holds at layer `n = 256` with
  `e = 200` for every `q = 1, …, 2^16`.
* **`centerCol_not_small_rational`** : the centre column satisfies no relation `q·x = r` on all
  layers with `1 ≤ |q| ≤ 2^16`, `|r| ≤ 2^200`; equivalently (`centerCol_padic_ne_small`) its
  2-adic integer is not `r/q` for such `q, r`.

* **`centerCol_not_fraction_of_period_cert`** : the layer ↔ period dictionary
  (`AdicPeriod.period_of_dvd`) applied to the period certificate `no_small_eventual_period`:
  the centre column is not `r/q` whenever `q ∣ 2^p − 1` for some `1 ≤ p` and `|r| < 2^N` with
  `N + p ≤ 1000`.  In particular (`centerCol_not_fraction_500`) it is not `r/q` for any `q` with
  `q ∣ 2^p − 1`, `1 ≤ p ≤ 500` (every odd `q` in which 2 has order at most 500, e.g.
  `q = 2^500 − 1`) and `|r| < 2^500`.

* `centerCol_not_fraction_64` : the same with the longer certificate
  `GateLoopData.centre_no_short_period_30000`: no `r/q` with `q ∣ 2^p − 1`, `1 ≤ p ≤ 64` and
  `|r| < 2^29936`.

This is finite evidence only: no finite layer decides Problem 1.
-/

namespace GLM.Rule30

/-- If the residue of `q·T` modulo `2^n` keeps a margin `2^e` from `0` on both sides, then
`q·T` is not congruent modulo `2^n` to any `r` with `|r| ≤ 2^e`. -/
theorem not_layer_rel_of_window {T q r : ℤ} {n e : ℕ} (hr : |r| ≤ 2 ^ e)
    (h1 : (2 : ℤ) ^ e < (q * T) % 2 ^ n) (h2 : (q * T) % 2 ^ n < 2 ^ n - 2 ^ e) :
    ¬ (2 : ℤ) ^ n ∣ q * T - r := by
  intro h
  have hmod : (q * T) % 2 ^ n = r % 2 ^ n :=
    Int.emod_eq_emod_iff_emod_sub_eq_zero.2 (Int.emod_eq_zero_of_dvd h)
  have hpos : (0 : ℤ) < 2 ^ e := by positivity
  rcases abs_le.1 hr with ⟨hr1, hr2⟩
  rcases le_or_gt 0 r with h0 | h0
  · rw [Int.emod_eq_of_lt h0 (by linarith)] at hmod
    linarith
  · have : r % 2 ^ n = r + 2 ^ n := by
      rw [← Int.add_emod_right, Int.emod_eq_of_lt (by linarith) (by linarith)]
    linarith

/-- Layer 256 of the centre column's tower, computed with the verified fast evaluator. -/
def centreLayer256 : ℤ := adicTrunc fastCenter 256

theorem adicTrunc_centerCol_eq (n : ℕ) : adicTrunc centerCol n = adicTrunc fastCenter n := by
  have : centerCol = fastCenter := funext centerCol_eq_fast
  rw [this]

/-- The window check at layer 256, margin `2^200`, for `q = 1, …, 2^16`. -/
def adicCheck : Bool :=
  (List.range 65536).all fun i =>
    decide ((2 : ℤ) ^ 200 < ((i + 1 : ℕ) * centreLayer256) % 2 ^ 256 ∧
      ((i + 1 : ℕ) * centreLayer256) % 2 ^ 256 < 2 ^ 256 - 2 ^ 200)

theorem adicCheck_ok : adicCheck = true := by native_decide

theorem adicCheck_spec {q : ℕ} (h1 : 1 ≤ q) (h2 : q ≤ 65536) :
    (2 : ℤ) ^ 200 < ((q : ℤ) * centreLayer256) % 2 ^ 256 ∧
      ((q : ℤ) * centreLayer256) % 2 ^ 256 < 2 ^ 256 - 2 ^ 200 := by
  have h := adicCheck_ok
  unfold adicCheck at h
  rw [List.all_eq_true] at h
  have := h (q - 1) (List.mem_range.2 (by omega))
  rw [show q - 1 + 1 = q by omega] at this
  simpa using this

/-- **The centre column is not 2-adically a small fraction**: no relation `q·x ≡ r` holds on
every layer of its tower with `1 ≤ |q| ≤ 2^16` and `|r| ≤ 2^200`. -/
theorem centerCol_not_small_rational (q r : ℤ) (hq : q ≠ 0) (hq' : |q| ≤ 2 ^ 16)
    (hr : |r| ≤ 2 ^ 200) : ¬ ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc centerCol n - r := by
  intro h
  have h256 := h 256
  rw [adicTrunc_centerCol_eq] at h256
  change (2 : ℤ) ^ 256 ∣ q * centreLayer256 - r at h256
  rcases le_or_gt 0 q with h0 | h0
  · obtain ⟨m, rfl⟩ := Int.eq_ofNat_of_zero_le h0
    have hm1 : 1 ≤ m := by omega
    have hm2 : m ≤ 65536 := by rw [abs_of_nonneg h0] at hq'; omega
    obtain ⟨c1, c2⟩ := adicCheck_spec hm1 hm2
    exact not_layer_rel_of_window hr c1 c2 h256
  · obtain ⟨m, hm⟩ := Int.eq_ofNat_of_zero_le (show 0 ≤ -q by omega)
    have hm1 : 1 ≤ m := by omega
    have hm2 : m ≤ 65536 := by rw [abs_of_neg h0] at hq'; omega
    obtain ⟨c1, c2⟩ := adicCheck_spec hm1 hm2
    have hr' : |-r| ≤ 2 ^ 200 := by rw [abs_neg]; exact hr
    apply not_layer_rel_of_window hr' c1 c2
    rw [← hm, show -q * centreLayer256 - -r = -(q * centreLayer256 - r) by ring]
    exact (dvd_neg).2 h256

/-- The same in the limit `ℤ₂` of the tower: `q · x ≠ r` for `1 ≤ |q| ≤ 2^16`, `|r| ≤ 2^200`. -/
theorem centerCol_padic_ne_small (q r : ℤ) (hq : q ≠ 0) (hq' : |q| ≤ 2 ^ 16)
    (hr : |r| ≤ 2 ^ 200) : (q : ℤ_[2]) * adicValue centerCol ≠ r := fun h =>
  centerCol_not_small_rational q r hq hq' hr (layers_of_padic_eq h)

/-- **Period certificates exclude fractions.**  If `q ∣ 2^p − 1` with `p ≥ 1` and `|r| < 2^N`
with `N + p ≤ 1000`, then the centre column is not `r/q` on its 2-adic tower. -/
theorem centerCol_not_fraction_of_period_cert (q r : ℤ) (p N : ℕ) (hp : 1 ≤ p)
    (hNp : N + p ≤ 1000) (hqp : q ∣ 2 ^ p - 1) (hr : |r| < 2 ^ N) :
    ¬ ∀ n, (2 : ℤ) ^ n ∣ q * adicTrunc centerCol n - r := fun h =>
  no_small_eventual_period p (N + p) hp (by omega) hNp (period_of_dvd h hp hqp hr)

/-- The case `N = p = 500`, in `ℤ₂`: `q · x ≠ r` whenever `q ∣ 2^p − 1` for some
`1 ≤ p ≤ 500` and `|r| < 2^500`. -/
theorem centerCol_not_fraction_500 (q r : ℤ) (p : ℕ) (hp : 1 ≤ p) (hp' : p ≤ 500)
    (hqp : q ∣ 2 ^ p - 1) (hr : |r| < 2 ^ 500) : (q : ℤ_[2]) * adicValue centerCol ≠ r :=
  fun h => centerCol_not_fraction_of_period_cert q r p 500 hp (by omega) hqp hr
    (layers_of_padic_eq h)

/-- With the preperiod-30000 certificate: `q · x ≠ r` whenever `q ∣ 2^p − 1` for some
`1 ≤ p ≤ 64` and `|r| < 2^29936`. -/
theorem centerCol_not_fraction_64 (q r : ℤ) (p : ℕ) (hp : 1 ≤ p) (hp' : p ≤ 64)
    (hqp : q ∣ 2 ^ p - 1) (hr : |r| < 2 ^ 29936) : (q : ℤ_[2]) * adicValue centerCol ≠ r :=
  fun h => GLM.HypothesisEngine.GateLoopData.centre_no_short_period_30000 (29936 + p)
    (by omega) p hp hp' (period_of_dvd (layers_of_padic_eq h) hp hqp hr)

end GLM.Rule30
