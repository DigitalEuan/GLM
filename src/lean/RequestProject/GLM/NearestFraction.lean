module

public import Mathlib
public import RequestProject.GLM.ToolValues

/-!
# The nearest fraction: the classical best-approximation theorem

The formal half of `studies/NEAREST_FRACTION_STUDY.md` (Phase 138). Until
Phase 137 the tool `best approximation` picked two candidates — the last
convergent `p_k / q_k` within the denominator bound `N` and the
semiconvergent `(p_(k-1) + j p_k) / (q_(k-1) + j q_k)` with the largest `j`
that keeps the denominator within `N` — and relied on the classical theorem
that the nearest fraction is one of them. That theorem was not proved, so an
exhaustive search over every denominator stood in for it, and only up to
`N = 20,000`. This file proves it, so the bound goes.

**The certificate** (no continued fractions needed).

* `farey_denominator` — a fraction strictly between Farey neighbours `a/b`,
  `c/d` (`b c - a d = ±1`) has denominator at least `b + d`.
* `endpoint_nearest` — a point outside an interval is no nearer an inner
  point than the nearer endpoint.
* `farey_certificate` — so if `x` lies between Farey neighbours whose
  denominators add up past `N`, the nearer of the two is a nearest fraction
  to `x` among all with denominator at most `N`. The tool checks these three
  conditions at run time, for every `N`.

**The classical theorem** (the certificate always exists).

* `complete_quotient` — `x = (p t + p') / (q t + q')` with `t` the complete
  quotient after the first `k` terms, while the expansion goes on.
* `conv_denominators` — `1 ≤ q` and `0 ≤ q' ≤ q`.
* `between_candidates` — `x` lies between the convergent and the
  semiconvergent with index `j ≤ t`.
* `nearest_fraction_candidates` — **the closest-fraction theorem**: with
  `q_k ≤ N < q_(k+1)` and `j = ⌊(N - q_(k-1)) / q_k⌋`, both candidates have
  denominator in `[1, N]`, and the nearer of them is at least as near `x` as
  every fraction `r / s` with `1 ≤ s ≤ N`.

**The search's measure** (Phase 138's unrolled search).

* `conv_denominators_fib`, `search_terminates` — convergent denominators grow
  at least like the Fibonacci numbers, so the search for the first convergent
  whose denominator passes `N` ends within `N + 1` rounds (in practice about
  `log_φ N`); no iteration cap is needed.
-/

@[expose] public section

namespace GLM.NearestFraction

open GLM.CertifiedStreams GLM.ToolValues

/-- **Farey neighbours leave no room.** If `a/b` and `c/d` are Farey
neighbours (`b c - a d = ±1`, `b, d > 0`), every fraction `r/s` (`s > 0`)
strictly between them has denominator at least `b + d`. -/
theorem farey_denominator {a b c d r s : ℤ} (hb : 0 < b) (hd : 0 < d) (hs : 0 < s)
    (hdet : b * c - a * d = 1 ∨ b * c - a * d = -1)
    (hin : ((r : ℝ) / s - a / b) * ((r : ℝ) / s - c / d) < 0) : b + d ≤ s := by
  have hbr : (0:ℝ) < b := by exact_mod_cast hb
  have hdr : (0:ℝ) < d := by exact_mod_cast hd
  have hsr : (0:ℝ) < s := by exact_mod_cast hs
  have h1 : ((r : ℝ) / s - a / b) = ((r * b - a * s : ℤ) : ℝ) / (s * b) := by
    push_cast; field_simp
  have h2 : ((r : ℝ) / s - c / d) = -((c * s - r * d : ℤ) : ℝ) / (s * d) := by
    push_cast; field_simp; ring
  have hden : (0:ℝ) < s * b * (s * d) := by positivity
  rw [h1, h2, div_mul_div_comm, div_neg_iff] at hin
  have hef : 0 < (r * b - a * s) * (c * s - r * d) := by
    have : (0:ℝ) < ((r * b - a * s) * (c * s - r * d) : ℤ) := by
      rcases hin with ⟨_, h⟩ | ⟨h, _⟩
      · linarith
      · push_cast at h ⊢; linarith
    exact_mod_cast this
  have key : s * (b * c - a * d) = b * (c * s - r * d) + d * (r * b - a * s) := by ring
  rcases pos_and_pos_or_neg_and_neg_of_mul_pos hef with ⟨he, hf⟩ | ⟨he, hf⟩
  · rcases hdet with h | h <;> rw [h] at key <;> nlinarith
  · rcases hdet with h | h <;> rw [h] at key <;> nlinarith

/-- **The nearer endpoint wins.** If `x` lies in the closed interval between
`u` and `v`, and `r` is not strictly inside it, then `r` is no nearer `x` than
the nearer of `u` and `v`. -/
theorem endpoint_nearest {x u v r : ℝ} (hx : (x - u) * (x - v) ≤ 0)
    (hr : 0 ≤ (r - u) * (r - v)) : min |x - u| |x - v| ≤ |x - r| := by
  rcases le_total u v with huv | huv
  · have hxu : u ≤ x := by nlinarith
    have hxv : x ≤ v := by nlinarith
    rcases le_or_gt r u with hru | hru
    · refine (min_le_left _ _).trans ?_
      rw [abs_of_nonneg (by linarith), abs_of_nonneg (by linarith)]; linarith
    · have : v ≤ r := by nlinarith
      refine (min_le_right _ _).trans ?_
      rw [abs_of_nonpos (by linarith), abs_of_nonpos (by linarith)]; linarith
  · have hxu : v ≤ x := by nlinarith
    have hxv : x ≤ u := by nlinarith
    rcases le_or_gt r v with hru | hru
    · refine (min_le_right _ _).trans ?_
      rw [abs_of_nonneg (by linarith), abs_of_nonneg (by linarith)]; linarith
    · have : u ≤ r := by nlinarith
      refine (min_le_left _ _).trans ?_
      rw [abs_of_nonpos (by linarith), abs_of_nonpos (by linarith)]; linarith

/-- **The Farey certificate.** If `x` lies in the closed interval between the
Farey neighbours `a/b` and `c/d` and `b + d > N`, then for every fraction
`r/s` with `0 < s ≤ N` the nearer of `a/b`, `c/d` is at least as near `x`. -/
theorem farey_certificate {a b c d N : ℤ} {x : ℝ} (hb : 0 < b) (hd : 0 < d)
    (hdet : b * c - a * d = 1 ∨ b * c - a * d = -1) (hN : N < b + d)
    (hx : (x - a / b) * (x - c / d) ≤ 0) :
    ∀ r s : ℤ, 0 < s → s ≤ N →
      min |x - a / b| |x - c / d| ≤ |x - (r : ℝ) / s| := by
  intro r s hs hsN
  rcases le_or_gt 0 (((r : ℝ) / s - a / b) * ((r : ℝ) / s - c / d)) with h | h
  · exact endpoint_nearest hx h
  · have := farey_denominator hb hd hs hdet h
    omega

/-- The remainder map `y ↦ 1 / fract y` of the continued fraction. -/
noncomputable abbrev rem (y : ℝ) : ℝ := 1 / Int.fract y

/-- **The complete quotient.** While the first `k` remainders are not whole
numbers, `x = (p t + p') / (q t + q')`, where `!![p, p'; q, q']` is the
convergent matrix of the first `k` terms and `t = rem^[k] x`; the denominator
is positive. -/
theorem complete_quotient (k : ℕ) (x : ℝ)
    (hirr : ∀ i < k, Int.fract (rem^[i] x) ≠ 0) :
    0 < (conv (cfPrefix k x) 1 0 : ℝ) * rem^[k] x + conv (cfPrefix k x) 1 1 ∧
    x * ((conv (cfPrefix k x) 1 0 : ℝ) * rem^[k] x + conv (cfPrefix k x) 1 1) =
      (conv (cfPrefix k x) 0 0 : ℝ) * rem^[k] x + conv (cfPrefix k x) 0 1 := by
  induction k generalizing x with
  | zero => simp [conv]
  | succ k ih =>
    have h0 : Int.fract x ≠ 0 := hirr 0 (by omega)
    obtain ⟨hD, hE⟩ := ih (rem x) (fun i hi => by
      have := hirr (i + 1) (by omega)
      rwa [Function.iterate_succ_apply] at this)
    have hf : 0 < Int.fract x := lt_of_le_of_ne (Int.fract_nonneg x) (Ne.symm h0)
    have hrem : rem x * Int.fract x = 1 := by simp [rem, h0]
    have hx : x = ⌊x⌋ + Int.fract x := (Int.floor_add_fract x).symm
    have hrp : 0 < rem x := by simp [rem]; exact hf
    rw [cfPrefix_succ, conv_cons, Function.iterate_succ_apply]
    rw [show 1 / Int.fract x = rem x from rfl]
    generalize rem x = R at *
    generalize Int.fract x = f at *
    set Q := conv (cfPrefix k R)
    set t := rem^[k] R
    simp only [cvM, Matrix.mul_apply, Fin.sum_univ_two, Matrix.of_apply,
      Matrix.cons_val', Matrix.cons_val_zero, Matrix.cons_val_one,
      Matrix.empty_val', Matrix.cons_val_fin_one]
    push_cast
    constructor
    · nlinarith
    · linear_combination (-(x - ⌊x⌋)) * hE + (R * ((Q 1 0 : ℝ) * t + Q 1 1)) * hx +
        ((Q 1 0 : ℝ) * t + Q 1 1) * hrem

/-- The denominators of the convergent matrix grow. -/
theorem conv_denominators (a : ℤ) (l : List ℤ) (hl : ∀ t ∈ l, 1 ≤ t) :
    1 ≤ conv (a :: l) 1 0 ∧ 0 ≤ conv (a :: l) 1 1 ∧
      conv (a :: l) 1 1 ≤ conv (a :: l) 1 0 := by
  induction l using List.reverseRecOn with
  | nil => simp [conv, cvM]
  | append_singleton l b ih =>
    obtain ⟨h1, h2, h3⟩ := ih (fun t ht => hl t (by simp [ht]))
    have hb : 1 ≤ b := hl b (by simp)
    rw [← List.cons_append, conv_append]
    simp only [cvM, Matrix.mul_apply, Fin.sum_univ_two, Matrix.of_apply,
      Matrix.cons_val', Matrix.cons_val_zero, Matrix.cons_val_one,
      Matrix.empty_val', Matrix.cons_val_fin_one]
    refine ⟨by nlinarith, by nlinarith, by nlinarith⟩

/-- Every term after the first is at least one, while the expansion goes on. -/
theorem cfPrefix_rem_ge_one (k : ℕ) (y : ℝ)
    (hirr : ∀ i < k, Int.fract (rem^[i] y) ≠ 0) :
    ∀ t ∈ cfPrefix k (rem y), 1 ≤ t := by
  induction k generalizing y with
  | zero => simp
  | succ k ih =>
    intro t ht
    rw [cfPrefix_succ] at ht
    rcases List.mem_cons.mp ht with rfl | ht
    · have h0 : Int.fract y ≠ 0 := hirr 0 (by omega)
      have hf : 0 < Int.fract y := lt_of_le_of_ne (Int.fract_nonneg y) (Ne.symm h0)
      have hlt : Int.fract y < 1 := Int.fract_lt_one y
      rw [Int.le_floor]
      push_cast
      rw [rem, le_div_iff₀ hf]; linarith
    · exact ih (rem y) (fun i hi => by
        have := hirr (i + 1) (by omega)
        rwa [Function.iterate_succ_apply] at this) t ht

/-- **Where `x` sits.** If `x = (p t + p') / (q t + q')` and `j ≤ t`, then `x`
lies in the closed interval between `p / q` and the semiconvergent
`(p' + j p) / (q' + j q)`. -/
theorem between_candidates {p q p' q' x t j : ℝ} (hq : 0 < q) (hD : 0 < q * t + q')
    (hE : 0 < q' + j * q) (hx : x * (q * t + q') = p * t + p') (htj : j ≤ t) :
    (x - p / q) * (x - (p' + j * p) / (q' + j * q)) ≤ 0 := by
  have hq0 := hq.ne'
  have hD0 := hD.ne'
  have hE0 := hE.ne'
  have hx' : x = (p * t + p') / (q * t + q') := by rw [eq_div_iff hD0]; exact hx
  have : (x - p / q) * (x - (p' + j * p) / (q' + j * q)) =
      -((p * q' - p' * q) ^ 2 * (t - j)) / (q * (q * t + q') ^ 2 * (q' + j * q)) := by
    rw [hx', div_sub_div _ _ hD0 hq0, div_sub_div _ _ hD0 hE0, div_mul_div_comm]
    rw [div_eq_div_iff (by positivity) (by positivity)]
    ring
  rw [this]
  apply div_nonpos_of_nonpos_of_nonneg
  · have : 0 ≤ t - j := by linarith
    have := mul_nonneg (sq_nonneg (p * q' - p' * q)) this
    linarith
  · positivity

/-- **The classical closest-fraction theorem.** Let the expansion of `x` go on
past term `k` (the first `k + 1` remainders are not whole numbers), let
`P = !![p_k, p_(k-1); q_k, q_(k-1)]` be the convergent matrix of its first
`k + 1` terms, and let `q_k ≤ N < q_(k+1) = q_(k-1) + a_(k+1) q_k`. With
`j = ⌊(N - q_(k-1)) / q_k⌋`, the convergent `p_k / q_k` and the semiconvergent
`(p_(k-1) + j p_k) / (q_(k-1) + j q_k)` both have denominator between `1` and
`N`, and every fraction `r / s` with `1 ≤ s ≤ N` is at least as far from `x`
as the nearer of the two. -/
theorem nearest_fraction_candidates (x : ℝ) (k : ℕ) (N : ℤ)
    (hirr : ∀ i ≤ k, Int.fract (rem^[i] x) ≠ 0)
    (hq : conv (cfPrefix (k + 1) x) 1 0 ≤ N)
    (hnext : N < conv (cfPrefix (k + 1) x) 1 1 +
      cfTerm (k + 1) x * conv (cfPrefix (k + 1) x) 1 0) :
    let P := conv (cfPrefix (k + 1) x)
    let j := (N - P 1 1) / P 1 0
    1 ≤ P 1 0 ∧ 1 ≤ P 1 1 + j * P 1 0 ∧ P 1 1 + j * P 1 0 ≤ N ∧
    ∀ r s : ℤ, 0 < s → s ≤ N →
      min |x - (P 0 0 : ℝ) / (P 1 0 : ℝ)|
          |x - ((P 0 1 + j * P 0 0 : ℤ) : ℝ) / ((P 1 1 + j * P 1 0 : ℤ) : ℝ)|
        ≤ |x - (r : ℝ) / s| := by
  intro P j
  have hq' : P 1 0 ≤ N := hq
  have hnext' : N < P 1 1 + cfTerm (k + 1) x * P 1 0 := hnext
  clear hq hnext
  have hterms := cfPrefix_rem_ge_one k x (fun i hi => hirr i (by omega))
  have hP : P = conv (⌊x⌋ :: cfPrefix k (rem x)) := rfl
  obtain ⟨hq1, hq'0, hq'q⟩ := conv_denominators ⌊x⌋ (cfPrefix k (rem x)) hterms
  rw [← hP] at hq1 hq'0 hq'q
  obtain ⟨hD, hE⟩ := complete_quotient (k + 1) x (fun i hi => hirr i (by omega))
  have hdet := conv_det (cfPrefix (k + 1) x)
  rw [cfPrefix_length, Matrix.det_fin_two] at hdet
  have hdet' : P 0 0 * P 1 1 - P 0 1 * P 1 0 = 1 ∨ P 0 0 * P 1 1 - P 0 1 * P 1 0 = -1 := by
    rcases neg_one_pow_eq_or ℤ (k + 1) with h | h <;> rw [h] at hdet
    · exact Or.inl hdet
    · exact Or.inr hdet
  have ht : (cfTerm (k + 1) x : ℝ) ≤ rem^[k + 1] x := Int.floor_le _
  have hq0 : P 1 0 ≠ 0 := by omega
  have hj1 : j * P 1 0 ≤ N - P 1 1 := Int.ediv_mul_le _ hq0
  have hj2 : N - P 1 1 < (j + 1) * P 1 0 := Int.lt_ediv_add_one_mul_self _ (by omega)
  have hj0 : 0 ≤ j := Int.ediv_nonneg (by omega) (by omega)
  have hja : j ≤ cfTerm (k + 1) x := by nlinarith
  have hE1 : 1 ≤ P 1 1 + j * P 1 0 := by
    rcases lt_or_ge 0 (P 1 1) with h | h
    · nlinarith
    · have : P 1 1 = 0 := by omega
      rw [this] at hj2 ⊢
      nlinarith
  refine ⟨hq1, hE1, by linarith, ?_⟩
  refine farey_certificate (by omega) (by omega) ?_ (by linarith) ?_
  · rcases hdet' with h | h
    · right; linear_combination -h
    · left; linear_combination -h
  · have hjr : (j : ℝ) ≤ rem^[k + 1] x := le_trans (by exact_mod_cast hja) ht
    have := between_candidates (p := (P 0 0 : ℝ)) (p' := (P 0 1 : ℝ)) (q := (P 1 0 : ℝ))
      (q' := (P 1 1 : ℝ)) (j := (j : ℝ)) (by exact_mod_cast hq1) hD
      (by exact_mod_cast hE1) hE hjr
    push_cast
    exact this



/-! ## The search's measure

The planner's search *the first convergent of `x` whose denominator is above
`N`* runs with no iteration cap. It is admitted because the denominators grow
at least like the Fibonacci numbers, so the test holds within `N + 1` rounds
whenever the expansion has that many terms. -/

/-- **Denominators grow like Fibonacci numbers**: with every term after the
first at least one, `q_n ≥ F(n + 1)` and `q_(n-1) ≥ F(n)`. -/
theorem conv_denominators_fib (a : ℤ) (l : List ℤ) (hl : ∀ t ∈ l, 1 ≤ t) :
    (Nat.fib (l.length + 1) : ℤ) ≤ conv (a :: l) 1 0 ∧
      (Nat.fib l.length : ℤ) ≤ conv (a :: l) 1 1 := by
  induction l using List.reverseRecOn with
  | nil => simp [conv, cvM]
  | append_singleton l b ih =>
    obtain ⟨h1, h2⟩ := ih (fun t ht => hl t (by simp [ht]))
    have hb : 1 ≤ b := hl b (by simp)
    rw [← List.cons_append, conv_append]
    simp only [cvM, Matrix.mul_apply, Fin.sum_univ_two, Matrix.of_apply,
      Matrix.cons_val', Matrix.cons_val_zero, Matrix.cons_val_one,
      Matrix.empty_val', Matrix.cons_val_fin_one, List.length_append, List.length_singleton]
    have hf : (Nat.fib (l.length + 1 + 1) : ℤ) = Nat.fib (l.length + 1) + Nat.fib l.length := by
      rw [Nat.fib_add_two]; push_cast; ring
    have hq : 0 ≤ conv (a :: l) 1 0 := le_trans (by positivity) h1
    constructor
    · rw [hf]; nlinarith
    · simpa using h1

/-- `n ≤ F(n + 1)`. -/
theorem le_fib_succ (n : ℕ) : n ≤ Nat.fib (n + 1) := by
  induction n using Nat.strong_induction_on with
  | _ n ih =>
    rcases n with _ | _ | n
    · simp
    · simp
    · rw [Nat.fib_add_two]
      have := ih (n + 1) (by omega)
      have h2 : 1 ≤ Nat.fib (n + 1) := Nat.fib_pos.mpr (by omega)
      omega

/-- **The search terminates**: once more than `N` terms follow the first, the
convergent denominator is above `N`. -/
theorem search_terminates (a : ℤ) (l : List ℤ) (hl : ∀ t ∈ l, 1 ≤ t) (N : ℕ)
    (hN : N < l.length) : (N : ℤ) < conv (a :: l) 1 0 := by
  have h := (conv_denominators_fib a l hl).1
  have h2 := le_fib_succ l.length
  have : (l.length : ℤ) ≤ Nat.fib (l.length + 1) := by exact_mod_cast h2
  omega

end GLM.NearestFraction
