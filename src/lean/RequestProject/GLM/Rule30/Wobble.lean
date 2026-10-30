module

public import Mathlib

/-!
# The wobble (delta-sigma accumulator) and the frequency problem (Target 2)

For any bit sequence `a : ℕ → Bool` we define

* `ones a n`   — the number of `true`s among `a 0, …, a (n-1)`;
* `wobble a n` — the delta-sigma accumulator `D(n) = 2·ones a n − n` (an integer);
* `freq a n`   — the empirical frequency `ones a n / n` (a real number);
* `HasFrequencyHalf a` — `freq a n → 1/2` (Wolfram's Problem 2 for one colour).

Results (all for arbitrary sequences):

* `freq_sub_half`             : `f(n) − 1/2 = D(n) / (2n)`.
* `wobble_succ`, `abs_wobble_le`, `wobble_parity` : `D` is a `±1` walk with `|D(n)| ≤ n`
  and `D(n) ≡ n (mod 2)`.
* `hasFrequencyHalf_iff`      : normality of frequency **is equivalent** to `D(n)/n → 0`,
  i.e. to the wobble being sub-linear. This is the exact (and weakest) form of Target 2.
* `hasFrequencyHalf_of_sqrt_bound` : the study's `|D(n)| ≤ C√n` implies normality.
* `hasFrequencyHalf_of_bounded`    : the bounded (true delta-sigma) regime gives the rate
  `|f(n) − 1/2| ≤ B/(2n)`.
* `not_forall_sqrt_bound`     : the statement "every sequence satisfies `|D(n)| ≤ C√n`"
  (stated for *all* sequences in the original `wobbleBoundedness_sqrt` axiom) is **false**.
* `deltaSigma_wobble`         : the ideal delta-sigma modulator for `1/2` has `D ∈ {0, 1}`.
-/

@[expose] public section

namespace GLM.Rule30

open Filter Topology

/-- Number of `true`s among the first `n` terms. -/
def ones (a : ℕ → Bool) (n : ℕ) : ℕ := ((Finset.range n).filter (fun i => a i = true)).card

/-- The delta-sigma accumulator ("wobble") `D(n) = 2·#ones − n`. -/
def wobble (a : ℕ → Bool) (n : ℕ) : ℤ := 2 * (ones a n : ℤ) - n

/-- Empirical frequency of `true` among the first `n` terms. -/
noncomputable def freq (a : ℕ → Bool) (n : ℕ) : ℝ := (ones a n : ℝ) / n

/-- Problem 2 (one colour): the frequency of `true` tends to `1/2`. -/
def HasFrequencyHalf (a : ℕ → Bool) : Prop := Tendsto (freq a) atTop (𝓝 (1 / 2))

@[simp] theorem ones_zero (a : ℕ → Bool) : ones a 0 = 0 := rfl

theorem ones_succ (a : ℕ → Bool) (n : ℕ) :
    ones a (n + 1) = ones a n + (if a n then 1 else 0) := by
  unfold ones
  rw [Finset.range_add_one, Finset.filter_insert]
  by_cases h : a n = true
  · simp [h]
  · simp [h]

theorem ones_le (a : ℕ → Bool) (n : ℕ) : ones a n ≤ n := by
  unfold ones
  exact (Finset.card_filter_le _ _).trans (by simp)

@[simp] theorem wobble_zero (a : ℕ → Bool) : wobble a 0 = 0 := by simp [wobble]

/-- The wobble is a `±1` walk. -/
theorem wobble_succ (a : ℕ → Bool) (n : ℕ) :
    wobble a (n + 1) = wobble a n + (if a n then 1 else -1) := by
  unfold wobble; rw [ones_succ]; split_ifs <;> push_cast <;> ring

theorem abs_wobble_le (a : ℕ → Bool) (n : ℕ) : |wobble a n| ≤ n := by
  have := ones_le a n
  unfold wobble; rw [abs_le]; constructor <;> omega

theorem wobble_parity (a : ℕ → Bool) (n : ℕ) : wobble a n % 2 = (n : ℤ) % 2 := by
  unfold wobble; omega

/-- **Key identity.** `f(n) − 1/2 = D(n) / (2n)` for `n > 0`. -/
theorem freq_sub_half (a : ℕ → Bool) {n : ℕ} (hn : 0 < n) :
    freq a n - 1 / 2 = (wobble a n : ℝ) / (2 * n) := by
  have hn' : (n : ℝ) ≠ 0 := by positivity
  unfold freq wobble; push_cast; field_simp

/-- **Normality of frequency is equivalent to a sub-linear wobble.** -/
theorem hasFrequencyHalf_iff (a : ℕ → Bool) :
    HasFrequencyHalf a ↔ Tendsto (fun n => (wobble a n : ℝ) / n) atTop (𝓝 0) := by
  have key : ∀ᶠ n in atTop, freq a n = 1 / 2 + (1 / 2) * ((wobble a n : ℝ) / n) := by
    filter_upwards [eventually_gt_atTop 0] with n hn
    have := freq_sub_half a hn
    have hn' : (n : ℝ) ≠ 0 := by positivity
    field_simp at this ⊢; linarith
  unfold HasFrequencyHalf
  rw [tendsto_congr' key]
  constructor
  · intro h
    have h2 := (h.sub_const (1 / 2)).const_mul 2
    simp only [add_sub_cancel_left, sub_self, mul_zero] at h2
    refine h2.congr (fun n => ?_)
    ring
  · intro h
    have h2 := (h.const_mul (1 / 2)).const_add (1 / 2)
    simpa using h2

/-- **Sub-linear wobble ⇒ normality.** Any bound `|D(n)| ≤ g(n)` with `g(n)/n → 0`
(eventually) is enough. -/
theorem hasFrequencyHalf_of_le (a : ℕ → Bool) (g : ℕ → ℝ)
    (hg : Tendsto (fun n => g n / n) atTop (𝓝 0))
    (hb : ∀ᶠ n in atTop, |(wobble a n : ℝ)| ≤ g n) : HasFrequencyHalf a := by
  rw [hasFrequencyHalf_iff]
  rw [tendsto_zero_iff_abs_tendsto_zero]
  refine squeeze_zero' (Eventually.of_forall fun n => abs_nonneg _) ?_ hg
  filter_upwards [hb] with n hn
  show |(wobble a n : ℝ) / n| ≤ g n / n
  rw [abs_div]
  rcases Nat.eq_zero_or_pos n with rfl | hpos
  · simp
  · have : (0 : ℝ) < |(n : ℝ)| := by positivity
    rw [abs_of_pos (by positivity : (0:ℝ) < n)]
    exact div_le_div_of_nonneg_right hn (by positivity)

/-- **Target 2 (the study's form): `|D(n)| ≤ C√n` eventually ⇒ normality.** -/
theorem hasFrequencyHalf_of_sqrt_bound (a : ℕ → Bool) (C : ℝ)
    (hb : ∀ᶠ n in atTop, |(wobble a n : ℝ)| ≤ C * Real.sqrt n) : HasFrequencyHalf a := by
  refine hasFrequencyHalf_of_le a (fun n => C * Real.sqrt n) ?_ hb
  have h1 : Tendsto (fun n : ℕ => C * (Real.sqrt n)⁻¹) atTop (𝓝 0) := by
    have : Tendsto (fun n : ℕ => (Real.sqrt n)⁻¹) atTop (𝓝 0) := by
      refine tendsto_inv_atTop_zero.comp ?_
      exact Real.tendsto_sqrt_atTop.comp tendsto_natCast_atTop_atTop
    simpa using this.const_mul C
  refine h1.congr' ?_
  filter_upwards [eventually_gt_atTop 0] with n hn
  have hs : Real.sqrt n ≠ 0 := by positivity
  have hsq : Real.sqrt n * Real.sqrt n = n := Real.mul_self_sqrt (by positivity)
  show C * (Real.sqrt n)⁻¹ = C * Real.sqrt n / n
  rw [mul_div_assoc]
  congr 1
  rw [inv_eq_iff_eq_inv, inv_div, eq_div_iff hs, hsq]

/-- The bounded ("true delta-sigma") regime. -/
def BoundedWobble (a : ℕ → Bool) : Prop := ∃ B : ℝ, ∀ n, |(wobble a n : ℝ)| ≤ B

/-- **Bounded regime ⇒ normality, with rate `B/(2n)`.** -/
theorem freq_rate_of_bounded (a : ℕ → Bool) (B : ℝ) (hB : ∀ n, |(wobble a n : ℝ)| ≤ B)
    {n : ℕ} (hn : 0 < n) : |freq a n - 1 / 2| ≤ B / (2 * n) := by
  rw [freq_sub_half a hn, abs_div, abs_of_pos (by positivity : (0:ℝ) < 2 * n)]
  exact div_le_div_of_nonneg_right (hB n) (by positivity)

theorem hasFrequencyHalf_of_bounded (a : ℕ → Bool) (h : BoundedWobble a) :
    HasFrequencyHalf a := by
  obtain ⟨B, hB⟩ := h
  refine hasFrequencyHalf_of_le a (fun _ => B) ?_ (Eventually.of_forall hB)
  simpa using (tendsto_const_div_atTop_nhds_zero_nat B)

/-- **The "for all sequences" wobble axiom is false.** The original
`wobbleBoundedness_sqrt` was stated for an *arbitrary* sequence `a`; the all-`true` sequence
has `D(n) = n`, which is not `O(√n)`. (So that axiom would make the theory inconsistent.) -/
theorem not_forall_sqrt_bound :
    ¬ ∀ a : ℕ → Bool, ∃ C : ℕ, ∀ n ≥ 1, |wobble a n| ≤ C * (Nat.sqrt n : ℤ) := by
  intro h
  obtain ⟨C, hC⟩ := h (fun _ => true)
  have hall : ∀ n, wobble (fun _ => true) n = n := by
    intro n; induction n with
    | zero => simp
    | succ n ih => rw [wobble_succ, ih]; simp
  have := hC ((C + 1) ^ 2) (Nat.succ_le_of_lt (by positivity))
  rw [hall, Nat.sqrt_eq', abs_of_nonneg (by positivity)] at this
  push_cast at this
  nlinarith

/-! ## The ideal delta-sigma modulator for target `1/2` -/

/-- Accumulator of the ideal first-order delta-sigma modulator for the target `1/2`:
emit `1` when the accumulator is `≤ 0`, otherwise emit `0`. -/
def dsAcc : ℕ → ℤ
  | 0 => 0
  | n + 1 => if dsAcc n ≤ 0 then dsAcc n + 1 else dsAcc n - 1

/-- The bit emitted by the ideal delta-sigma modulator. -/
def deltaSigma (n : ℕ) : Bool := decide (dsAcc n ≤ 0)

theorem deltaSigma_wobble (n : ℕ) : wobble deltaSigma n = dsAcc n ∧ (dsAcc n = 0 ∨ dsAcc n = 1) := by
  induction n with
  | zero => simp [dsAcc]
  | succ n ih =>
    obtain ⟨h1, h2⟩ := ih
    rw [wobble_succ, h1]
    simp only [deltaSigma, dsAcc]
    rcases h2 with h | h <;> simp [h]

/-- The ideal delta-sigma modulator is the periodic sequence `1010…`. -/
theorem deltaSigma_eq (n : ℕ) : deltaSigma n = decide (n % 2 = 0) := by
  have key : ∀ n, dsAcc n = if n % 2 = 0 then 0 else 1 := by
    intro n; induction n with
    | zero => rfl
    | succ n ih =>
      simp only [dsAcc, ih]
      rcases Nat.mod_two_eq_zero_or_one n with h | h
      · simp [h, Nat.succ_mod_two_eq_one_iff.mpr h]
      · simp [h, Nat.succ_mod_two_eq_zero_iff.mpr h]
  simp only [deltaSigma, key]; split_ifs with h <;> simp [h]

theorem deltaSigma_bounded : BoundedWobble deltaSigma :=
  ⟨1, fun n => by
    rcases (deltaSigma_wobble n).2 with h | h <;> simp [(deltaSigma_wobble n).1, h]⟩

end GLM.Rule30
