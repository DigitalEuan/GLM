import RequestProject.GLM.Rule30.Compute
import RequestProject.GLM.Rule30.Prizes

/-!
# The wobble certificate (Track 2), with exact arithmetic

(This file is deliberately not a `module`: it uses `native_decide`.)

All comparisons are exact: `|D(N)| ≤ C·√N` is checked in the squared integer form
`q·D(N)² ≤ p·N` for a rational `C² = p/q`.

## Proved

* `wobbleBoundedness_implies_normality` : `|D(N)| ≤ C√N` for all `N ≥ 1` implies Problem 2's
  conclusion, with the explicit rate `|f(N) − 1/2| ≤ C/(2√N)` (`freq_dev_of_wobble_le`).
* `sqrt_bound_two_fails` : for the centre column the bound **fails with `C = 2`**:
  `|D(1462)| = 80 > 2·√1462`.
* `wobble_sq_ratio_cert` : for `1 ≤ N ≤ 10⁶`, `D(N)²/N ≤ 175561/24979`, with equality at
  `N = 24979` (`|D(24979)| = 419`); also `D(10⁶) = 1536` (`wobble_1e6`).  So the best
  constant on this range is exactly
  `C = √(175561/24979) ≈ 2.651`, and `sqrt_bound_fails_below` shows every smaller `C` fails.
* `no_finite_certificate_problem2` : **no finite computation can prove (or refute)
  Problem 2.**  For every `N` the first `N` centre bits extend both to a sequence with
  frequency `1/2` and to one without.  `no_finite_certificate_problem1` is the same
  statement for eventual periodicity.

The exact-arithmetic script `scripts/wobble_certificate.py` (integers and `Fraction` only)
reproduces these numbers independently; its output is in
`scripts/wobble_certificate_output.txt`.
-/

namespace GLM.Rule30

open Filter Topology

/-! ## From a wobble bound to normality, with a rate -/

/-- **Rate.** `|D(N)| ≤ C√N` gives `|f(N) − 1/2| ≤ C / (2√N)`. -/
theorem freq_dev_of_wobble_le (a : ℕ → Bool) (C : ℝ) {N : ℕ} (hN : 0 < N)
    (h : |(wobble a N : ℝ)| ≤ C * Real.sqrt N) :
    |freq a N - 1 / 2| ≤ C / (2 * Real.sqrt N) := by
  have hs : 0 < Real.sqrt N := Real.sqrt_pos.mpr (by exact_mod_cast hN)
  have hsq : Real.sqrt N * Real.sqrt N = N := Real.mul_self_sqrt (by positivity)
  rw [freq_sub_half a hN, abs_div, abs_of_pos (by positivity : (0:ℝ) < 2 * N),
    div_le_div_iff₀ (by positivity) (by positivity)]
  calc |(wobble a N : ℝ)| * (2 * Real.sqrt N) ≤ C * Real.sqrt N * (2 * Real.sqrt N) :=
        mul_le_mul_of_nonneg_right h (by positivity)
    _ = C * (2 * (Real.sqrt N * Real.sqrt N)) := by ring
    _ = C * (2 * N) := by rw [hsq]

/-- **`wobbleBoundedness_implies_normality`** (the study's Target 2, stated for one
sequence, not for all sequences). -/
theorem wobbleBoundedness_implies_normality (a : ℕ → Bool) (C : ℝ)
    (h : ∀ N ≥ 1, |(wobble a N : ℝ)| ≤ C * Real.sqrt N) : HasFrequencyHalf a :=
  hasFrequencyHalf_of_sqrt_bound a C (eventually_atTop.mpr ⟨1, h⟩)

/-! ## Exact checks for the centre column -/

/-- Linear scan: from accumulator `D` at time `N`, check `q·D(n)² ≤ p·n` for each further
bit. -/
def scanOK (p q : ℕ) : List Bool → ℤ → ℕ → Bool
  | [], _, _ => true
  | b :: bs, D, N =>
    let D' := D + (if b then 1 else -1)
    decide ((q : ℤ) * D' ^ 2 ≤ p * (N + 1 : ℕ)) && scanOK p q bs D' (N + 1)

theorem scanOK_spec (a : ℕ → Bool) (p q : ℕ) (L k : ℕ)
    (h : scanOK p q ((List.range' k L).map a) (wobble a k) k = true) :
    ∀ n, k < n → n ≤ k + L → (q : ℤ) * wobble a n ^ 2 ≤ p * n := by
  induction L generalizing k with
  | zero => intro n h1 h2; omega
  | succ L ih =>
    rw [List.range'_succ, List.map_cons, scanOK, Bool.and_eq_true, decide_eq_true_eq,
      ← wobble_succ] at h
    intro n h1 h2
    rcases Nat.lt_or_ge (k + 1) n with h3 | h3
    · exact ih (k + 1) h.2 n h3 (by omega)
    · obtain rfl : n = k + 1 := by omega
      exact h.1

/-- One pass over the first `10⁶` centre bits: the squared-ratio scan and the final value
`D(10⁶) = 1536`. -/
theorem wobble_scan_1e6 :
    (let l := fastList 1000000
     scanOK 175561 24979 l 0 0 && decide (2 * (l.count true : ℤ) - 1000000 = 1536)) = true := by
  native_decide

theorem wobble_sq_ratio_scan : scanOK 175561 24979 (fastList 1000000) 0 0 = true := by
  have h := wobble_scan_1e6
  simp only [Bool.and_eq_true] at h
  exact h.1

/-- `D(10⁶) = 1536`. -/
theorem wobble_1e6 : wobble centerCol 1000000 = 1536 := by
  have h := wobble_scan_1e6
  simp only [Bool.and_eq_true, decide_eq_true_eq] at h
  rw [wobble_eq_fast]; exact_mod_cast h.2

theorem wobble_24979 : wobble centerCol 24979 = 419 ∨ wobble centerCol 24979 = -419 := by
  rw [wobble_eq_fast]; native_decide

/-- **Exact wobble certificate on `1 ≤ N ≤ 10⁶`:** `D(N)²/N ≤ 175561/24979`, attained at
`N = 24979`. -/
theorem wobble_sq_ratio_cert :
    (∀ N, 1 ≤ N → N ≤ 1000000 → (24979 : ℤ) * wobble centerCol N ^ 2 ≤ 175561 * N) ∧
      (24979 : ℤ) * wobble centerCol 24979 ^ 2 = 175561 * 24979 := by
  refine ⟨fun N h1 h2 => ?_, ?_⟩
  · have h := wobble_sq_ratio_scan
    rw [fastList_eq, List.range_eq_range', show (0 : ℤ) = wobble centerCol 0 by simp] at h
    exact_mod_cast scanOK_spec centerCol 175561 24979 1000000 0 h N (by omega) (by omega)
  · rcases wobble_24979 with h | h <;> rw [h] <;> norm_num

/-- **`|D(N)| ≤ 2√N` is false for the centre column** (already at `N = 1462`, where
`|D| = 80` and `80² = 6400 > 4·1462 = 5848`). -/
theorem sqrt_bound_two_fails : ¬ ∀ N ≥ 1, |(wobble centerCol N : ℝ)| ≤ 2 * Real.sqrt N := by
  intro h
  have h1 := h 1462 (by norm_num)
  have h80 : |(wobble centerCol 1462 : ℝ)| = 80 := by
    have := wobble_max_10000.2
    rw [← Int.cast_abs, this]; norm_num
  rw [h80] at h1
  have : (40 : ℝ) ≤ Real.sqrt 1462 := by push_cast at h1; linarith
  nlinarith [Real.sq_sqrt (show (0:ℝ) ≤ 1462 by norm_num), Real.sqrt_nonneg 1462]

/-- **Sharpness (witness `N = 24979`):** if `C² < 175561/24979 ≈ 7.028` then `|D(N)| ≤ C√N` fails
for the centre column. -/
theorem sqrt_bound_fails_below (C : ℝ) (hC : C ^ 2 < 175561 / 24979) :
    ¬ ∀ N ≥ 1, |(wobble centerCol N : ℝ)| ≤ C * Real.sqrt N := by
  intro h
  have h1 := h 24979 (by norm_num)
  have hab : |(wobble centerCol 24979 : ℝ)| = 419 := by
    rcases wobble_24979 with e | e <;> rw [e] <;> norm_num
  rw [hab] at h1
  have hs : 0 ≤ Real.sqrt (24979 : ℕ) := Real.sqrt_nonneg _
  have hsq : Real.sqrt (24979 : ℕ) ^ 2 = 24979 := by rw [Real.sq_sqrt (by positivity)]; norm_num
  have hCpos : 0 < C := by
    by_contra hneg; push_neg at hneg
    have : C * Real.sqrt (24979 : ℕ) ≤ 0 := mul_nonpos_of_nonpos_of_nonneg hneg hs
    linarith
  have : (419 : ℝ) ^ 2 ≤ (C * Real.sqrt (24979 : ℕ)) ^ 2 := by
    exact pow_le_pow_left₀ (by norm_num) h1 2
  rw [mul_pow, hsq] at this
  have : (175561 : ℝ) / 24979 ≤ C ^ 2 := by rw [div_le_iff₀ (by norm_num)]; linarith
  linarith

/-! ## No finite certificate decides Problem 2 (or Problem 1) -/

/-- Two sequences that agree from time `N` on have wobbles within `2N` of each other. -/
theorem wobble_close (a b : ℕ → Bool) (N : ℕ) (h : ∀ i ≥ N, a i = b i) (n : ℕ) :
    |wobble a n - wobble b n| ≤ 2 * (min n N : ℕ) := by
  induction n with
  | zero => simp
  | succ n ih =>
    rw [wobble_succ, wobble_succ]
    rcases Nat.lt_or_ge n N with hn | hn
    · rw [show min (n + 1) N = min n N + 1 by omega]
      have ih' : |wobble a n - wobble b n| ≤ 2 * ((min n N : ℕ) : ℤ) := ih
      have : |(if a n = true then (1 : ℤ) else -1) - (if b n = true then 1 else -1)| ≤ 2 := by
        split_ifs <;> norm_num
      calc |wobble a n + (if a n = true then 1 else -1) - (wobble b n +
            (if b n = true then 1 else -1))|
          = |(wobble a n - wobble b n) + ((if a n = true then (1 : ℤ) else -1) -
              (if b n = true then 1 else -1))| := by ring_nf
        _ ≤ |wobble a n - wobble b n| + |(if a n = true then (1 : ℤ) else -1) -
              (if b n = true then 1 else -1)| := abs_add_le _ _
        _ ≤ 2 * ((min n N + 1 : ℕ) : ℤ) := by rw [Nat.cast_add, Nat.cast_one]; linarith
    · rw [h n hn, show min (n + 1) N = min n N by omega]
      simpa using ih

theorem wobble_allTrue (n : ℕ) : wobble (fun _ => true) n = n := by
  induction n with
  | zero => simp
  | succ n ih => rw [wobble_succ, ih]; simp

/-- The first `N` bits of `c`, then the sequence `b`. -/
def prefixThen (c : ℕ → Bool) (N : ℕ) (b : ℕ → Bool) : ℕ → Bool := fun i => if i < N then c i else b i

theorem prefixThen_agree (c : ℕ → Bool) (N : ℕ) (b : ℕ → Bool) :
    ∀ i < N, prefixThen c N b i = c i := fun i hi => by simp [prefixThen, hi]

theorem prefixThen_tail (c : ℕ → Bool) (N : ℕ) (b : ℕ → Bool) :
    ∀ i ≥ N, prefixThen c N b i = b i := fun i hi => by simp [prefixThen, show ¬ i < N by omega]

/-- **No finite certificate for Problem 2.** Whatever the first `N` bits are, they extend
both to a sequence whose frequency tends to `1/2` and to one whose frequency does not. -/
theorem no_finite_certificate_problem2 (c : ℕ → Bool) (N : ℕ) :
    (∃ a : ℕ → Bool, (∀ i < N, a i = c i) ∧ HasFrequencyHalf a) ∧
      (∃ b : ℕ → Bool, (∀ i < N, b i = c i) ∧ ¬ HasFrequencyHalf b) := by
  refine ⟨⟨prefixThen c N deltaSigma, prefixThen_agree _ _ _, ?_⟩,
    ⟨prefixThen c N (fun _ => true), prefixThen_agree _ _ _, ?_⟩⟩
  · apply hasFrequencyHalf_of_bounded
    refine ⟨2 * N + 1, fun n => ?_⟩
    have h1 := wobble_close _ _ N (prefixThen_tail c N deltaSigma) n
    have h2 : |wobble deltaSigma n| ≤ 1 := by
      rcases (deltaSigma_wobble n).2 with h | h <;> simp [(deltaSigma_wobble n).1, h]
    have h3 : ((min n N : ℕ) : ℤ) ≤ N := by exact_mod_cast min_le_right n N
    have : |wobble (prefixThen c N deltaSigma) n| ≤ 2 * N + 1 := by
      calc |wobble (prefixThen c N deltaSigma) n|
          = |(wobble (prefixThen c N deltaSigma) n - wobble deltaSigma n) + wobble deltaSigma n| := by
            ring_nf
        _ ≤ |wobble (prefixThen c N deltaSigma) n - wobble deltaSigma n| + |wobble deltaSigma n| :=
            abs_add_le _ _
        _ ≤ 2 * N + 1 := by linarith
    exact_mod_cast this
  · rw [hasFrequencyHalf_iff]
    intro hlim
    have hev : ∀ᶠ n : ℕ in atTop,
        (1 / 2 : ℝ) ≤ (wobble (prefixThen c N fun _ => true) n : ℝ) / n := by
      filter_upwards [eventually_ge_atTop (4 * N + 1)] with n hn
      have h1 := wobble_close _ _ N (prefixThen_tail c N (fun _ => true)) n
      rw [wobble_allTrue] at h1
      have h3 : ((min n N : ℕ) : ℤ) ≤ N := by exact_mod_cast min_le_right n N
      have h4 : (n : ℤ) - 2 * N ≤ wobble (prefixThen c N fun _ => true) n := by
        have := (abs_le.mp h1).1; linarith
      have hnpos : (0 : ℝ) < n := by exact_mod_cast (show 0 < n by omega)
      rw [le_div_iff₀ hnpos]
      have h5 : ((n : ℤ) - 2 * N : ℝ) ≤ (wobble (prefixThen c N fun _ => true) n : ℝ) := by
        exact_mod_cast h4
      have h6 : (4 * N + 1 : ℝ) ≤ n := by exact_mod_cast hn
      push_cast at h5
      linarith
    have := ge_of_tendsto hlim hev
    norm_num at this

/-- Powers of two. -/
def isPow2 (i : ℕ) : Bool := decide (i = 2 ^ Nat.log 2 i)

theorem not_eventuallyPeriodic_of_pow2_tail (a : ℕ → Bool) (N : ℕ)
    (h : ∀ i ≥ N, a i = isPow2 i) : ¬ EventuallyPeriodic a := by
  rintro ⟨p, hp, M, hM⟩
  obtain ⟨k, hk1⟩ : ∃ k, N + M + p < 2 ^ k := ⟨N + M + p, Nat.lt_two_pow_self⟩
  have hpow : a (2 ^ k) = true := by
    rw [h _ (by omega)]; simp [isPow2, Nat.log_pow]
  have hnext := hM (2 ^ k) (by omega)
  rw [hpow, h _ (by omega)] at hnext
  have hlog : Nat.log 2 (2 ^ k + p) = k := by
    apply Nat.log_eq_of_pow_le_of_lt_pow (by omega)
    rw [pow_succ]; omega
  simp only [isPow2, hlog, decide_eq_true_eq] at hnext
  omega

/-- **No finite certificate for Problem 1.** Whatever the first `N` bits are, they extend
both to an eventually periodic sequence and to one that is not eventually periodic. -/
theorem no_finite_certificate_problem1 (c : ℕ → Bool) (N : ℕ) :
    (∃ a : ℕ → Bool, (∀ i < N, a i = c i) ∧ EventuallyPeriodic a) ∧
      (∃ b : ℕ → Bool, (∀ i < N, b i = c i) ∧ ¬ EventuallyPeriodic b) := by
  refine ⟨⟨prefixThen c N (fun _ => false), prefixThen_agree _ _ _, 1, by norm_num, N,
    fun n hn => ?_⟩, ⟨prefixThen c N isPow2, prefixThen_agree _ _ _,
    not_eventuallyPeriodic_of_pow2_tail _ N (prefixThen_tail _ _ _)⟩⟩
  rw [prefixThen_tail _ _ _ _ hn, prefixThen_tail _ _ _ _ (by omega)]

/-- For the centre column: no statement about its first `N` bits implies Problem 2. -/
theorem prefix_cannot_imply_problem2 (N : ℕ) :
    ¬ ∀ a : ℕ → Bool, (∀ i < N, a i = centerCol i) → HasFrequencyHalf a := by
  intro h
  obtain ⟨b, hb, hnb⟩ := (no_finite_certificate_problem2 centerCol N).2
  exact hnb (h b hb)

end GLM.Rule30
