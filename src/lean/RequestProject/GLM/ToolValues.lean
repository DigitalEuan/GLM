module

public import Mathlib
public import RequestProject.GLM.CertifiedStreams

/-!
# Tool values: what the stepwise planner may take from a tool

The formal half of `studies/TOOL_VALUES_STUDY.md` (Phase 137). The stepwise
planner now takes a number from a tool — *the third term of the continued
fraction of pi*, *the fourth convergent of pi*, *the closest fraction to
`sqrt 2` with denominator at most 100* — and composes it with arithmetic.
This file proves the rules those numbers are taken by.

**Selecting from a certified prefix** (`tool continued fraction`, the
selectors `index` and `fold`).

* `cfTerm k x` — the `k`-th continued-fraction term of `x` (from 0).
* `cfPrefix_take`, `cfPrefix_getElem` — the first `k` terms of a longer prefix
  are the prefix of length `k`, and entry `k` of a prefix is `cfTerm k x`.
* `select_certified`, `fold_certified` — so entry `k` of the prefix the tool
  certified from an interval `[lo, hi]` is the `k`-th term of every `x` in the
  interval, and a sum over its first `m` entries is the sum of the first `m`
  terms of `x`: composing with a selector does not weaken the certificate.

**Convergents** (`tool convergent`).

* `cvM a` — the matrix `!![a, 1; 1, 0]`, and `conv l` the product over `l`.
* `conv_append` — appending a term multiplies on the right: the forward
  recurrence `p_k = a_k p_(k-1) + p_(k-2)` the tool computes.
* `conv_det` — `det (conv l) = (-1)^length`, hence `conv_coprime`: the
  convergent `p / q` the tool prints is in lowest terms.
* `cfValue_eq_conv` — `p / q` is the value of the finite expansion
  `a₀ + 1/(a₁ + 1/(⋯))` when every term after the first is at least one.

**Choosing the nearer of two fractions** (`tool best approximation`).

* `closer_iff_midpoint` — `|x - c₁| < |x - c₂|` exactly when `x` lies on
  `c₁`'s side of the midpoint.
* `nearer_of_margin` — a rational reading `mid` within `ε` of `x` decides the
  nearer of two fractions when it separates them by more than `2 ε`.
* `farther_than_candidate` — for denominator `q`, every numerator other than
  `⌊q·mid⌋` and `⌊q·mid⌋ + 1` is at least `1/q` farther from `mid` than one of
  those two, so the exhaustive check needs to try only two per denominator.
-/

@[expose] public section

namespace GLM.ToolValues

open GLM.CertifiedStreams

/-! ## Selecting from a certified prefix -/

/-- The `k`-th continued-fraction term of `x`, counting from `0`. -/
noncomputable def cfTerm (k : ℕ) (x : ℝ) : ℤ :=
  ⌊(fun y : ℝ => 1 / Int.fract y)^[k] x⌋

theorem cfPrefix_length (n : ℕ) (x : ℝ) : (cfPrefix n x).length = n := by
  induction n generalizing x with
  | zero => rfl
  | succ n ih => simp [cfPrefix_succ, ih]

/-- The first `k` terms of a longer prefix are the prefix of length `k`. -/
theorem cfPrefix_take (n k : ℕ) (x : ℝ) (h : k ≤ n) :
    (cfPrefix n x).take k = cfPrefix k x := by
  induction k generalizing n x with
  | zero => simp
  | succ k ih =>
    obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
    simp only [cfPrefix_succ, List.take_succ_cons]
    rw [ih m _ (by omega)]

/-- Entry `k` of a prefix of length `n > k` is the `k`-th term. -/
theorem cfPrefix_getElem (n k : ℕ) (x : ℝ) (h : k < n) :
    (cfPrefix n x)[k]? = some (cfTerm k x) := by
  induction k generalizing n x with
  | zero =>
    obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
    simp [cfPrefix_succ, cfTerm]
  | succ k ih =>
    obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
    simp only [cfPrefix_succ, List.getElem?_cons_succ]
    rw [ih m _ (by omega)]
    simp [cfTerm, Function.iterate_succ_apply]

/-- **The `index` selector is sound.** Entry `k` of the prefix the tool
certified from `[lo, hi]` is the `k`-th term of every `x` in the interval. -/
theorem select_certified {n k : ℕ} {lo x hi : ℝ} (hlo : lo ≤ x) (hhi : x ≤ hi)
    (heq : cfPrefix n lo = cfPrefix n hi) (hk : k < n) :
    (cfPrefix n lo)[k]? = some (cfTerm k x) := by
  rw [← cfPrefix_certified n hlo hhi heq]
  exact cfPrefix_getElem n k x hk

/-- **The `fold` selector is sound** (shown for the sum): the sum of the first
`m` entries of the certified prefix is the sum of the first `m` terms of `x`. -/
theorem fold_certified {n m : ℕ} {lo x hi : ℝ} (hlo : lo ≤ x) (hhi : x ≤ hi)
    (heq : cfPrefix n lo = cfPrefix n hi) (hm : m ≤ n) :
    ((cfPrefix n lo).take m).sum = ∑ j ∈ Finset.range m, cfTerm j x := by
  rw [← cfPrefix_certified n hlo hhi heq, cfPrefix_take n m x hm]
  clear hm heq hlo hhi
  induction m generalizing x with
  | zero => simp
  | succ m ih =>
    rw [cfPrefix_succ, List.sum_cons, ih, Finset.sum_range_succ']
    simp [cfTerm, Function.iterate_succ_apply, add_comm]

/-! ## Convergents -/

/-- One term as a matrix. -/
def cvM (a : ℤ) : Matrix (Fin 2) (Fin 2) ℤ := !![a, 1; 1, 0]

/-- The convergent matrix `!![p_n, p_(n-1); q_n, q_(n-1)]` of a term list. -/
def conv (l : List ℤ) : Matrix (Fin 2) (Fin 2) ℤ := (l.map cvM).prod

/-- **The forward recurrence the tool computes.** Appending the term `a`
multiplies on the right by `cvM a`, i.e. `p_new = a p + p_prev` and
`q_new = a q + q_prev`. -/
theorem conv_append (l : List ℤ) (a : ℤ) : conv (l ++ [a]) = conv l * cvM a := by
  simp [conv, List.map_append, List.prod_append]

theorem conv_cons (a : ℤ) (l : List ℤ) : conv (a :: l) = cvM a * conv l := by
  simp [conv]

theorem det_cvM (a : ℤ) : (cvM a).det = -1 := by
  simp [cvM, Matrix.det_fin_two]

/-- **The determinant identity** `p_n q_(n-1) - p_(n-1) q_n = (-1)^n`. -/
theorem conv_det (l : List ℤ) : (conv l).det = (-1) ^ l.length := by
  induction l with
  | nil => simp [conv]
  | cons a l ih => rw [conv_cons, Matrix.det_mul, det_cvM, ih, List.length_cons, pow_succ]; ring

/-- **The convergent is in lowest terms.** -/
theorem conv_coprime (l : List ℤ) : IsCoprime (conv l 0 0) (conv l 1 0) := by
  have h := conv_det l
  rw [Matrix.det_fin_two] at h
  rcases neg_one_pow_eq_or ℤ l.length with h1 | h1 <;> rw [h1] at h
  · exact ⟨conv l 1 1, -conv l 0 1, by linarith⟩
  · exact ⟨-conv l 1 1, conv l 0 1, by linarith⟩

/-- The value of a finite continued fraction `a₀ + 1/(a₁ + 1/(⋯))`. -/
def cfValue : List ℤ → ℚ
  | [] => 0
  | [a] => a
  | a :: b :: l => a + 1 / cfValue (b :: l)

/-- With every term at least one, both left entries of the convergent matrix
are positive. -/
theorem conv_pos : ∀ (l : List ℤ), l ≠ [] → (∀ t ∈ l, 1 ≤ t) →
    0 < conv l 0 0 ∧ 0 < conv l 1 0
  | [], h, _ => absurd rfl h
  | [a], _, ht => by
    have := ht a (by simp)
    simp [conv, cvM]; omega
  | a :: b :: l, _, ht => by
    obtain ⟨h1, h2⟩ := conv_pos (b :: l) (by simp) (fun t h => ht t (by simp_all))
    have ha := ht a (by simp)
    rw [conv_cons]
    simp only [cvM, Matrix.mul_apply, Fin.sum_univ_two, Matrix.of_apply,
      Matrix.cons_val', Matrix.cons_val_zero, Matrix.cons_val_one,
      Matrix.empty_val', Matrix.cons_val_fin_one]
    constructor <;> nlinarith

/-- **The convergent is the value of the finite expansion**, when every term
after the first is at least one (the first, the integer part, may be any
integer). -/
theorem cfValue_eq_conv : ∀ (a : ℤ) (l : List ℤ), (∀ t ∈ l, 1 ≤ t) →
    cfValue (a :: l) = (conv (a :: l) 0 0 : ℚ) / (conv (a :: l) 1 0 : ℚ)
  | a, [], _ => by simp [cfValue, conv, cvM]
  | a, b :: l, ht => by
    have ih := cfValue_eq_conv b l (fun t h => ht t (by simp [h]))
    obtain ⟨h1, -⟩ := conv_pos (b :: l) (by simp) ht
    have hP : (conv (b :: l) 0 0 : ℚ) ≠ 0 := by exact_mod_cast h1.ne'
    rw [cfValue, ih, conv_cons a (b :: l)]
    simp only [cvM, Matrix.mul_apply, Fin.sum_univ_two, Matrix.of_apply,
      Matrix.cons_val', Matrix.cons_val_zero, Matrix.cons_val_one,
      Matrix.empty_val', Matrix.cons_val_fin_one]
    push_cast
    rw [one_div_div, add_div' _ _ _ hP]
    congr 1 <;> ring

/-! ## Choosing the nearer of two fractions -/

/-- **The midpoint rule.** `c₁` is strictly nearer `x` than `c₂` exactly when
`x` lies strictly on `c₁`'s side of their midpoint. -/
theorem closer_iff_midpoint (x c₁ c₂ : ℝ) :
    |x - c₁| < |x - c₂| ↔ 0 < (c₁ - c₂) * (x - (c₁ + c₂) / 2) := by
  rw [← sq_lt_sq]
  constructor <;> intro h <;> nlinarith

/-- **The margin rule of the exhaustive check.** If the reading `mid` is within
`ε` of `x` and puts `c` nearer than `r` by more than `2 ε`, then `c` is nearer
`x` than `r`. -/
theorem nearer_of_margin {x mid c r ε : ℝ} (hx : |x - mid| ≤ ε)
    (hm : |mid - c| + 2 * ε < |mid - r|) : |x - c| < |x - r| := by
  have h1 : |x - c| ≤ |x - mid| + |mid - c| := abs_sub_le x mid c
  have h2 : |mid - r| ≤ |mid - x| + |x - r| := abs_sub_le mid x r
  rw [abs_sub_comm mid x] at h2
  linarith

/-- **Two numerators per denominator suffice.** For `q > 0` and
`b = ⌊q · mid⌋`, every numerator `p` other than `b` and `b + 1` is at least
`1/q` farther from `mid` than one of `b/q`, `(b+1)/q`. -/
theorem farther_than_candidate {mid : ℝ} {q : ℕ} (hq : 0 < q) (p : ℤ)
    (hp : p ≠ ⌊(q : ℝ) * mid⌋ ∧ p ≠ ⌊(q : ℝ) * mid⌋ + 1) :
    ∃ c ∈ ({⌊(q : ℝ) * mid⌋, ⌊(q : ℝ) * mid⌋ + 1} : Set ℤ),
      |mid - (c : ℝ) / q| + 1 / q ≤ |mid - (p : ℝ) / q| := by
  set b := ⌊(q : ℝ) * mid⌋ with hb
  have hqr : (0 : ℝ) < q := by exact_mod_cast hq
  have hlo : (b : ℝ) ≤ q * mid := Int.floor_le _
  have hhi : q * mid < (b : ℝ) + 1 := Int.lt_floor_add_one _
  have hlo' : (b : ℝ) / q ≤ mid := by rw [div_le_iff₀ hqr]; linarith
  have hhi' : mid < ((b : ℝ) + 1) / q := by rw [lt_div_iff₀ hqr]; linarith
  have hq1 : (0 : ℝ) < 1 / q := by positivity
  rcases lt_or_gt_of_ne hp.1 with hlt | hgt
  · refine ⟨b, by simp, ?_⟩
    have hp' : (p : ℝ) + 1 ≤ b := by exact_mod_cast hlt
    have hpq : (p : ℝ) / q + 1 / q ≤ (b : ℝ) / q := by
      rw [← add_div]; exact div_le_div_of_nonneg_right hp' hqr.le
    rw [abs_of_nonneg (by linarith), abs_of_nonneg (by linarith)]
    linarith
  · have hgt2 : b + 1 < p := by
      rcases lt_or_gt_of_ne hp.2 with h | h
      · omega
      · exact h
    refine ⟨b + 1, by simp, ?_⟩
    have hp' : (b : ℝ) + 1 + 1 ≤ p := by exact_mod_cast hgt2
    have hpq : ((b : ℝ) + 1) / q + 1 / q ≤ (p : ℝ) / q := by
      rw [← add_div]; exact div_le_div_of_nonneg_right hp' hqr.le
    push_cast
    rw [abs_of_nonpos (by linarith), abs_of_nonpos (by linarith)]
    linarith

/-- A worked check of the tool's arithmetic: the convergent matrix of the
first four terms `[3, 7, 15, 1]` of pi is `!![355, 333; 113, 106]`, so the
fourth convergent is `355 / 113`. -/
theorem conv_pi_four : conv [3, 7, 15, 1] = !![355, 333; 113, 106] := by
  decide

end GLM.ToolValues
