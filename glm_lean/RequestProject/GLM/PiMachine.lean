module

public import Mathlib

/-!
# The machine sums `π` itself: Machin's formula and the arctangent series (Phase 166)

*Created 19 October 2026.*

The formal half of `studies/PI_MACHINE_STUDY.md`. Since Phase 163 the batch
machine GLM-BAT computes `e` (it sums the series) and `√m` (it checks a root by
squaring), but `π` was a declared constant: the two twenty-digit decimals
Mathlib proves (`GLM.ToolMachine.pi_enclosure`), written into the program. This
file proves the rules by which the machine now computes an enclosure of `π`
from integers alone.

* `machin` — Machin's formula, `π = 16 arctan (1/5) − 4 arctan (1/239)`, from
  Mathlib's addition and doubling formulas for `arctan` and `arctan 1 = π/4`.
* `arctan_series_bound` — for `0 ≤ x < 1`, `arctan x` lies within
  `x^(2n+1)/(2n+1)` of the first `n` terms of its series (Mathlib's series for
  `arctan` and its alternating-series error bound).
* `atStep`, `atH`, `atH_div`, `atH_arctan_sum` — the machine's loop. Horner's
  rule on the series, run from the last term back to the first with two
  integers: `P ← m² Q − (2k+1) P`, `Q ← (2k+1) m² Q`, starting from
  `(P, Q) = (0, 1)`. After `n` steps `P / (m Q)` is exactly the sum of the
  first `n` terms of the series for `arctan (1/m)`.
* `pi_series_bound` — the two sums put together by Machin's formula lie within
  `16 (1/5)^(2a+1)/(2a+1) + 4 (1/239)^(2b+1)/(2b+1)` of `π`.
* `piEnds`, `piEnds_enclose` — the four integers the machine forms (lower and
  upper numerator and denominator) and the theorem that `π` lies between the
  two fractions, for every number of terms `a` and `b`.
-/

@[expose] public section

open Real Finset

namespace GLM.PiMachine

/-- **Machin's formula**: `π = 16 arctan (1/5) − 4 arctan (1/239)`. -/
theorem machin : Real.pi = 16 * arctan (1 / 5) - 4 * arctan (1 / 239) := by
  have h1 : 2 * arctan (1 / 5 : ℝ) = arctan (5 / 12) := by
    rw [two_mul_arctan (by norm_num) (by norm_num)]; norm_num
  have h2 : 2 * arctan (5 / 12 : ℝ) = arctan (120 / 119) := by
    rw [two_mul_arctan (by norm_num) (by norm_num)]; norm_num
  have h3 : arctan (120 / 119 : ℝ) + arctan (-(1 / 239)) = arctan 1 := by
    rw [arctan_add (by norm_num)]; norm_num
  rw [arctan_neg, arctan_one] at h3
  linarith

/-- **The arctangent series with its error**: for `0 ≤ x < 1`, the first `n`
terms of `∑ (-1)^i x^(2i+1)/(2i+1)` are within `x^(2n+1)/(2n+1)` of
`arctan x`. -/
theorem arctan_series_bound {x : ℝ} (h0 : 0 ≤ x) (h1 : x < 1) (n : ℕ) :
    |arctan x - ∑ i ∈ range n, (-1) ^ i * (x ^ (2 * i + 1) / (2 * i + 1))| ≤
      x ^ (2 * n + 1) / (2 * n + 1) := by
  have hs := Real.hasSum_arctan (x := x)
    (by rw [Real.norm_eq_abs, abs_of_nonneg h0]; exact h1)
  set f : ℕ → ℝ := fun i => x ^ (2 * i + 1) / (2 * i + 1) with hf
  have hsum : HasSum (fun i => (-1) ^ i * f i) (arctan x) := by
    convert hs using 1
    ext i; simp [hf]; ring
  have hanti : Antitone f := by
    intro i j hij
    simp only [hf]
    apply div_le_div₀ (by positivity) (pow_le_pow_of_le_one h0 h1.le (by omega))
      (by positivity)
    have : (i : ℝ) ≤ j := by exact_mod_cast hij
    linarith
  have hfs : Summable f := by
    have hg : Summable (fun i : ℕ => x * (x ^ 2) ^ i) :=
      (summable_geometric_of_lt_one (by positivity) (by nlinarith)).mul_left x
    refine Summable.of_nonneg_of_le (fun i => by positivity) (fun i => ?_) hg
    have : x * (x ^ 2) ^ i = x ^ (2 * i + 1) := by ring
    rw [this]
    exact div_le_self (by positivity) (by linarith [show (0 : ℝ) ≤ i from by positivity])
  have := alternating_series_error_bound f hanti hfs n
  rw [hsum.tsum_eq] at this
  exact this

/-- One step of the machine's loop for `arctan (1/m)`, at term `k`:
`P ← m² Q − (2k+1) P`, `Q ← (2k+1) m² Q`. -/
def atStep (m k : ℕ) (pq : ℤ × ℤ) : ℤ × ℤ :=
  ((m : ℤ) ^ 2 * pq.2 - (2 * k + 1) * pq.1, (2 * k + 1) * (m : ℤ) ^ 2 * pq.2)

/-- The loop run over the `r` terms `k, k+1, …, k+r−1`, from the last back to
the first (Horner's rule), starting from `(0, 1)`. The machine runs
`atH m 0 n`. -/
def atH (m : ℕ) : ℕ → ℕ → ℤ × ℤ
  | _, 0 => (0, 1)
  | k, r + 1 => atStep m k (atH m (k + 1) r)

/-- The loop's denominator stays positive. -/
theorem atH_snd_pos (m : ℕ) (hm : 0 < m) (k r : ℕ) : 0 < (atH m k r).2 := by
  induction r generalizing k with
  | zero => simp [atH]
  | succ r ih => simp only [atH, atStep]; have := ih (k + 1); positivity

/-- **What the loop computes**: `P / Q = ∑_{j<r} (-1)^j (1/m²)^j / (2(k+j)+1)`. -/
theorem atH_div (m : ℕ) (hm : 0 < m) (k r : ℕ) :
    ((atH m k r).1 : ℝ) / (atH m k r).2 =
      ∑ j ∈ range r, (-1) ^ j * ((1 / (m : ℝ) ^ 2) ^ j / (2 * (k + j : ℕ) + 1)) := by
  induction r generalizing k with
  | zero => simp [atH]
  | succ r ih =>
    rw [sum_range_succ', atH]
    have hq := atH_snd_pos m hm (k + 1) r
    have ih' := ih (k + 1)
    have hq' : ((atH m (k + 1) r).2 : ℝ) ≠ 0 := by exact_mod_cast hq.ne'
    have hm' : (m : ℝ) ≠ 0 := by exact_mod_cast hm.ne'
    have : ∑ j ∈ range r, (-1 : ℝ) ^ (j + 1) *
          ((1 / (m : ℝ) ^ 2) ^ (j + 1) / (2 * (k + (j + 1) : ℕ) + 1))
        = -(1 / (m : ℝ) ^ 2) * ∑ j ∈ range r, (-1) ^ j *
          ((1 / (m : ℝ) ^ 2) ^ j / (2 * (k + 1 + j : ℕ) + 1)) := by
      rw [mul_sum]; refine sum_congr rfl fun j _ => ?_
      rw [show k + (j + 1) = k + 1 + j by omega]; ring
    rw [this, ← ih']
    simp only [atStep]
    push_cast
    field_simp
    ring

/-- **The loop's result is the partial sum of the arctangent series**:
`P / (m Q)` after `n` steps is the first `n` terms of the series for
`arctan (1/m)`. -/
theorem atH_arctan_sum (m : ℕ) (hm : 0 < m) (n : ℕ) :
    ((atH m 0 n).1 : ℝ) / ((m : ℝ) * (atH m 0 n).2) =
      ∑ i ∈ range n, (-1) ^ i * ((1 / (m : ℝ)) ^ (2 * i + 1) / (2 * i + 1)) := by
  rw [div_mul_eq_div_div_swap, atH_div m hm, sum_div]
  refine sum_congr rfl fun i _ => ?_
  have hm' : (m : ℝ) ≠ 0 := by exact_mod_cast hm.ne'
  rw [show (1 / (m : ℝ)) ^ (2 * i + 1) = (1 / (m : ℝ) ^ 2) ^ i * (1 / m) by ring, zero_add]
  field_simp

/-- **`π` from the two loops**: with `a` terms for `arctan (1/5)` and `b` for
`arctan (1/239)`, Machin's combination of the two loop results is within
`16 (1/5)^(2a+1)/(2a+1) + 4 (1/239)^(2b+1)/(2b+1)` of `π`. -/
theorem pi_series_bound (a b : ℕ) :
    |Real.pi - (16 * (((atH 5 0 a).1 : ℝ) / (5 * (atH 5 0 a).2)) -
        4 * (((atH 239 0 b).1 : ℝ) / (239 * (atH 239 0 b).2)))| ≤
      16 * ((1 / 5 : ℝ) ^ (2 * a + 1) / (2 * a + 1)) +
        4 * ((1 / 239 : ℝ) ^ (2 * b + 1) / (2 * b + 1)) := by
  have h5 := atH_arctan_sum 5 (by norm_num) a
  have h239 := atH_arctan_sum 239 (by norm_num) b
  push_cast at h5 h239
  rw [h5, h239, machin]
  have e5 := arctan_series_bound (x := 1 / 5) (by norm_num) (by norm_num) a
  have e239 := arctan_series_bound (x := 1 / 239) (by norm_num) (by norm_num) b
  rw [abs_le] at e5 e239 ⊢
  constructor <;> nlinarith [e5.1, e5.2, e239.1, e239.2]

/-- The four integers the machine forms after `a` and `b` steps:
`((lower numerator, lower denominator), (upper numerator, upper denominator))`.
With `S = SN/SD` Machin's combination and `E = EN/ED` the error bound,
the ends are `S − E` and `S + E` over the common denominator `SD·ED`. -/
def piEnds (a b : ℕ) : (ℤ × ℤ) × (ℤ × ℤ) :=
  let p5 := (atH 5 0 a).1
  let q5 := (atH 5 0 a).2
  let p239 := (atH 239 0 b).1
  let q239 := (atH 239 0 b).2
  let SN := 16 * p5 * (239 * q239) - 4 * p239 * (5 * q5)
  let SD := 5 * q5 * (239 * q239)
  let ea : ℤ := (2 * a + 1) * 5 ^ (2 * a + 1)
  let eb : ℤ := (2 * b + 1) * 239 ^ (2 * b + 1)
  let EN := 16 * eb + 4 * ea
  let ED := ea * eb
  ((SN * ED - EN * SD, SD * ED), (SN * ED + EN * SD, SD * ED))

/-- **The enclosure the machine computes**: for every `a` and `b`, the
denominators are positive and `π` lies between the two fractions. -/
theorem piEnds_enclose (a b : ℕ) :
    0 < (piEnds a b).1.2 ∧ 0 < (piEnds a b).2.2 ∧
    ((piEnds a b).1.1 : ℝ) / (piEnds a b).1.2 ≤ Real.pi ∧
    Real.pi ≤ ((piEnds a b).2.1 : ℝ) / (piEnds a b).2.2 := by
  have q5 := atH_snd_pos 5 (by norm_num) 0 a
  have q239 := atH_snd_pos 239 (by norm_num) 0 b
  have h := pi_series_bound a b
  rw [abs_le] at h
  set p5 := (atH 5 0 a).1
  set Q5 := (atH 5 0 a).2
  set p239 := (atH 239 0 b).1
  set Q239 := (atH 239 0 b).2
  have hQ5 : (0 : ℝ) < Q5 := by exact_mod_cast q5
  have hQ239 : (0 : ℝ) < Q239 := by exact_mod_cast q239
  have hD : (0 : ℤ) < 5 * Q5 * (239 * Q239) *
      (((2 * a + 1) * 5 ^ (2 * a + 1)) * ((2 * b + 1) * 239 ^ (2 * b + 1))) := by
    positivity
  have hDr : (0 : ℝ) < 5 * Q5 * (239 * Q239) *
      (((2 * a + 1) * 5 ^ (2 * a + 1)) * ((2 * b + 1) * 239 ^ (2 * b + 1))) := by
    exact_mod_cast hD
  refine ⟨hD, hD, ?_, ?_⟩
  · simp only [piEnds]
    rw [div_le_iff₀ (by exact_mod_cast hD)]
    push_cast
    have key : (16 * (p5 / (5 * Q5)) - 4 * (p239 / (239 * Q239)) -
        (16 * ((1 / 5 : ℝ) ^ (2 * a + 1) / (2 * a + 1)) +
          4 * ((1 / 239 : ℝ) ^ (2 * b + 1) / (2 * b + 1)))) *
        (5 * Q5 * (239 * Q239) *
          (((2 * a + 1) * 5 ^ (2 * a + 1)) * ((2 * b + 1) * 239 ^ (2 * b + 1)))) =
        ((16 * p5 * (239 * Q239) - 4 * p239 * (5 * Q5)) *
            (((2 * a + 1) * 5 ^ (2 * a + 1)) * ((2 * b + 1) * 239 ^ (2 * b + 1))) -
          (16 * ((2 * b + 1) * 239 ^ (2 * b + 1)) + 4 * ((2 * a + 1) * 5 ^ (2 * a + 1))) *
            (5 * Q5 * (239 * Q239))) := by
      rw [one_div_pow, one_div_pow]
      field_simp
    rw [← key]
    exact mul_le_mul_of_nonneg_right (by linarith) hDr.le
  · simp only [piEnds]
    rw [le_div_iff₀ (by exact_mod_cast hD)]
    push_cast
    have key : (16 * (p5 / (5 * Q5)) - 4 * (p239 / (239 * Q239)) +
        (16 * ((1 / 5 : ℝ) ^ (2 * a + 1) / (2 * a + 1)) +
          4 * ((1 / 239 : ℝ) ^ (2 * b + 1) / (2 * b + 1)))) *
        (5 * Q5 * (239 * Q239) *
          (((2 * a + 1) * 5 ^ (2 * a + 1)) * ((2 * b + 1) * 239 ^ (2 * b + 1)))) =
        ((16 * p5 * (239 * Q239) - 4 * p239 * (5 * Q5)) *
            (((2 * a + 1) * 5 ^ (2 * a + 1)) * ((2 * b + 1) * 239 ^ (2 * b + 1))) +
          (16 * ((2 * b + 1) * 239 ^ (2 * b + 1)) + 4 * ((2 * a + 1) * 5 ^ (2 * a + 1))) *
            (5 * Q5 * (239 * Q239))) := by
      rw [one_div_pow, one_div_pow]
      field_simp
    rw [← key]
    exact mul_le_mul_of_nonneg_right (by linarith) hDr.le

end GLM.PiMachine
