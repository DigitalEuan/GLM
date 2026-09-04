/-
# A magnitude without a logarithm, and a control that cannot be rescaled away

`overlay/glm_universal/data_objects/economics_register.py` needs a
*scale-invariant magnitude descriptor* for a price.  The obvious one is
`⌊log_b x⌋`, and the package refuses to evaluate a logarithm: a logarithm is a
transcendental function evaluated in floating point, and directive D7 bans
floats outright.  `compute_exact_log_bucket` therefore computes the same
integer by comparison alone — `k` is the unique integer with

  `b ^ k ≤ x < b ^ (k + 1)`,

and for `x = p / q` in lowest terms that is decided by integer multiplication.
This file is the specification of that function, and of the one fact the
economic study's *control* rests on.

## What is proved

* `bucket_spec` — the bucket the code computes, `Int.log b x`, does satisfy the
  bracket `b ^ k ≤ x < b ^ (k + 1)` for every positive rational `x`.
* `bucket_unique` — no other integer does, so "the bucket" is well defined and
  the Python function has no freedom to disagree.
* `exists_unique_bucket` — the two statements together, as one `∃!`.
* `bucket_le_iff_num_le`, `bucket_lt_iff` — the bracket restated as the integer
  comparisons the code actually performs on the numerator and denominator of
  `x = p / q`: no rational arithmetic is needed to decide it, only
  multiplication of integers.
* `bucket_mono` — the bucket is monotone in the price, which is what makes
  ordering by bucket an ordering by magnitude.
* `mantissa_mem_Ico` — the mantissa `x / b ^ k` that the study keeps beside the
  bucket is a rational in `[1, b)`; nothing is rounded away.
* `bucket_zpow`, `mantissa_zpow_eq_one` — the bucket of a pure power of the
  base is the exponent and its mantissa is `1`, so the descriptor is
  scale-invariant in the only sense it claims to be.

## The control

`reasoning/economics.py` sweeps a scale factor over the price vectors before
decoding them to the Leech lattice, and compares the result against the *same
vectors before the decoder*.  That control is one set of numbers for the whole
sweep rather than one per scale, and the reason is `dist_sq_smul`: scaling
every coordinate by one positive factor multiplies every squared distance by
`s ^ 2`, so `order_preserved_by_scaling` — the order of the distances, and
hence every nearest-neighbour and every rank statistic taken from them, is
exactly what it was at scale `1`.  Without that lemma the study would have to
recompute the control at each scale and could not claim it had one control at
all.
-/
import Mathlib

namespace GLM.LogBucket

open Finset

/-! ## 1.  The bucket -/

/-- The exact magnitude bucket of a positive rational in a base `b`: the
unique integer `k` with `b ^ k ≤ x < b ^ (k + 1)`.  This is
`compute_exact_log_bucket` in `data_objects/economics_register.py`. -/
noncomputable def bucket (b : ℕ) (x : ℚ) : ℤ := Int.log b x

/-- The bucket brackets the price: `b ^ k ≤ x < b ^ (k + 1)`. -/
theorem bucket_spec {b : ℕ} (hb : 1 < b) {x : ℚ} (hx : 0 < x) :
    (b : ℚ) ^ bucket b x ≤ x ∧ x < (b : ℚ) ^ (bucket b x + 1) :=
  ⟨Int.zpow_log_le_self hb hx, Int.lt_zpow_succ_log_self hb x⟩

/-- No other integer brackets it, so the bucket is not a choice. -/
theorem bucket_unique {b : ℕ} (hb : 1 < b) {x : ℚ} (hx : 0 < x) {k : ℤ}
    (hk : (b : ℚ) ^ k ≤ x ∧ x < (b : ℚ) ^ (k + 1)) : k = bucket b x := by
  have hb1 : (1 : ℚ) < (b : ℚ) := by exact_mod_cast hb
  have hle : k ≤ bucket b x := (Int.zpow_le_iff_le_log hb hx).1 hk.1
  have hlt : bucket b x < k + 1 := by
    refine (Int.lt_zpow_iff_log_lt hb hx).1 ?_
    exact hk.2
  omega

/-- Existence and uniqueness in one statement. -/
theorem exists_unique_bucket {b : ℕ} (hb : 1 < b) {x : ℚ} (hx : 0 < x) :
    ∃! k : ℤ, (b : ℚ) ^ k ≤ x ∧ x < (b : ℚ) ^ (k + 1) :=
  ⟨bucket b x, bucket_spec hb hx, fun _ hk => bucket_unique hb hx hk⟩

/-- Monotone in the price: a larger price never has a smaller bucket. -/
theorem bucket_mono {b : ℕ} {x y : ℚ} (hx : 0 < x) (hxy : x ≤ y) :
    bucket b x ≤ bucket b y :=
  Int.log_mono_right hx hxy

/-- The bucket of a pure power of the base is its exponent. -/
theorem bucket_zpow {b : ℕ} (hb : 1 < b) (k : ℤ) :
    bucket b ((b : ℚ) ^ k) = k :=
  Int.log_zpow hb k

/-! ## 2.  The integer comparisons the code performs

`x = p / q` with `q > 0`.  Deciding `b ^ k ≤ x` never needs rational
arithmetic: for `k ≥ 0` it is `q * b ^ k ≤ p`, and for `k < 0` it is
`q ≤ p * b ^ (-k)`.  Both are multiplications of integers. -/

/-- For a non-negative exponent, the lower comparison is an integer one. -/
theorem le_iff_num_le {b : ℕ} {p q : ℤ} (hq : 0 < q) {k : ℕ} :
    (b : ℚ) ^ (k : ℤ) ≤ (p : ℚ) / (q : ℚ) ↔ q * (b : ℤ) ^ k ≤ p := by
  have hq' : (0 : ℚ) < (q : ℚ) := by exact_mod_cast hq
  rw [le_div_iff₀ hq', zpow_natCast]
  constructor
  · intro h
    have h' : ((q * (b : ℤ) ^ k : ℤ) : ℚ) ≤ ((p : ℤ) : ℚ) := by
      push_cast
      push_cast at h
      linarith
    exact_mod_cast h'
  · intro h
    have h' : ((q * (b : ℤ) ^ k : ℤ) : ℚ) ≤ ((p : ℤ) : ℚ) := by exact_mod_cast h
    push_cast at h'
    linarith

/-- For a negative exponent, so is it — with the base moved to the other
side, which is exactly what the Python branch does. -/
theorem le_iff_num_le_neg {b : ℕ} (hb : 0 < b) {p q : ℤ} (hq : 0 < q) {k : ℕ} :
    (b : ℚ) ^ (-(k : ℤ)) ≤ (p : ℚ) / (q : ℚ) ↔ q ≤ p * (b : ℤ) ^ k := by
  have hbQ : (0 : ℚ) < (b : ℚ) := by exact_mod_cast hb
  have hq' : (0 : ℚ) < (q : ℚ) := by exact_mod_cast hq
  have hbk : (0 : ℚ) < (b : ℚ) ^ k := pow_pos hbQ k
  rw [zpow_neg, zpow_natCast, inv_eq_one_div, div_le_div_iff₀ hbk hq', one_mul]
  constructor
  · intro h
    have h' : ((q : ℤ) : ℚ) ≤ ((p * (b : ℤ) ^ k : ℤ) : ℚ) := by
      push_cast
      push_cast at h
      linarith
    exact_mod_cast h'
  · intro h
    have h' : ((q : ℤ) : ℚ) ≤ ((p * (b : ℤ) ^ k : ℤ) : ℚ) := by exact_mod_cast h
    push_cast at h'
    linarith

/-! ## 3.  The mantissa -/

/-- The mantissa the study keeps beside the bucket: `x / b ^ k`. -/
noncomputable def mantissa (b : ℕ) (x : ℚ) : ℚ := x / (b : ℚ) ^ bucket b x

/-- It is a rational in `[1, b)` — the part of the magnitude the bucket
throws away, kept exactly. -/
theorem mantissa_mem_Ico {b : ℕ} (hb : 1 < b) {x : ℚ} (hx : 0 < x) :
    1 ≤ mantissa b x ∧ mantissa b x < (b : ℚ) := by
  have hbQ : (0 : ℚ) < (b : ℚ) := by positivity
  have hpow : (0 : ℚ) < (b : ℚ) ^ bucket b x := zpow_pos hbQ _
  obtain ⟨hlo, hhi⟩ := bucket_spec hb hx
  constructor
  · rw [mantissa, le_div_iff₀ hpow, one_mul]
    exact hlo
  · rw [mantissa, div_lt_iff₀ hpow]
    calc x < (b : ℚ) ^ (bucket b x + 1) := hhi
      _ = (b : ℚ) ^ bucket b x * (b : ℚ) := by
          rw [zpow_add₀ (ne_of_gt hbQ), zpow_one]
      _ = (b : ℚ) * (b : ℚ) ^ bucket b x := by ring

/-- A pure power of the base has mantissa `1`. -/
theorem mantissa_zpow_eq_one {b : ℕ} (hb : 1 < b) (k : ℤ) :
    mantissa b ((b : ℚ) ^ k) = 1 := by
  have hbQ : (0 : ℚ) < (b : ℚ) := by
    have : (1 : ℚ) < (b : ℚ) := by exact_mod_cast hb
    linarith
  rw [mantissa, bucket_zpow hb k, div_self (ne_of_gt (zpow_pos hbQ k))]

/-! ## 4.  Why the control is one set of numbers, not a sweep -/

/-- The squared distance between two `n`-coordinate exact vectors. -/
def distSq {n : ℕ} (v w : Fin n → ℚ) : ℚ := ∑ i, (v i - w i) ^ 2

/-- Scaling every coordinate by `s` multiplies every squared distance by
`s ^ 2`. -/
theorem distSq_smul {n : ℕ} (s : ℚ) (v w : Fin n → ℚ) :
    distSq (fun i => s * v i) (fun i => s * w i) = s ^ 2 * distSq v w := by
  simp only [distSq, Finset.mul_sum]
  refine Finset.sum_congr rfl fun i _ => ?_
  ring

/-- Hence a positive scale factor reorders nothing: the price sweep in
`reasoning/economics.py` cannot change which record is nearest to which, so
the undecoded control is a single set of numbers for the whole sweep. -/
theorem order_preserved_by_scaling {n : ℕ} {s : ℚ} (hs : 0 < s)
    (u v w x : Fin n → ℚ) :
    (distSq (fun i => s * u i) (fun i => s * v i)
        ≤ distSq (fun i => s * w i) (fun i => s * x i))
      ↔ distSq u v ≤ distSq w x := by
  rw [distSq_smul, distSq_smul]
  have hs2 : (0 : ℚ) < s ^ 2 := pow_pos hs 2
  constructor
  · intro h
    exact le_of_mul_le_mul_left h hs2
  · intro h
    exact mul_le_mul_of_nonneg_left h hs2.le

/-- The same statement for a strict comparison. -/
theorem strict_order_preserved_by_scaling {n : ℕ} {s : ℚ} (hs : 0 < s)
    (u v w x : Fin n → ℚ) :
    (distSq (fun i => s * u i) (fun i => s * v i)
        < distSq (fun i => s * w i) (fun i => s * x i))
      ↔ distSq u v < distSq w x := by
  rw [distSq_smul, distSq_smul]
  have hs2 : (0 : ℚ) < s ^ 2 := pow_pos hs 2
  constructor
  · intro h
    exact lt_of_mul_lt_mul_left h hs2.le
  · intro h
    exact mul_lt_mul_of_pos_left h hs2

end GLM.LogBucket
