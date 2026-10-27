module

public import RequestProject.GLM.Rule30.Ergodic
public import RequestProject.GLM.Rule30.Perspective
public import RequestProject.GLM.Rule30.Prizes

/-!
# No causal observer beats chance on a typical row

A *predictor* (an observer reading the column from the past towards the future) is a rule
`pred t a` that guesses bit `t` of a column `a` from the bits `a 0, …, a (t−1)` only
(`IsCausal`). Examples: "repeat the last bit", any finite-memory machine, any betting system,
and the wobble arrow of `Perspective.lean`.

* `ae_predictor_hits_half` : for **every** causal predictor and every column `c`, for almost every
  row the predictor is right with asymptotic frequency exactly `1/2`.
* `ae_arrow_followed_half` : in particular the observer's arrow (`step up when D(n) ≤ 0, down
  when D(n) > 0`) is followed exactly half the time on a typical row. This is the a.s. version of
  `arrow_stats_10000` (the seed's centre column follows the arrow 4968 times out of 9964).

The engine is the same as in `Ergodic.lean`: the event "the predictor is right at time `t`" is
`x_{c−t} = (function of the inner cone)`, which has probability `1/2` given anything in the past.
So the hit indicators are independent fair coins, and the strong law applies.

For the GLM: an observer's "perspective" (a reading direction plus a causal rule) carries **no**
predictive advantage on a typical row. Showing that the seed is typical in this sense, for every
causal predictor, would prove Problem 2 (take `pred = const true`) and Problem 1 (an eventually
periodic column is predicted perfectly from some time on by a causal rule).
-/

@[expose] public section

namespace GLM.Rule30

open MeasureTheory ProbabilityTheory Filter Topology

/-- `pred t a` depends only on `a 0, …, a (t-1)`. -/
def IsCausal (pred : ℕ → (ℕ → Bool) → Bool) : Prop :=
  ∀ t a b, (∀ i < t, a i = b i) → pred t a = pred t b

/-- Did the predictor guess bit `t` of column `c` correctly? -/
def hit (pred : ℕ → (ℕ → Bool) → Bool) (c : ℤ) (t : ℕ) (x : Config) : Bool :=
  decide (evolve x t c = pred t (fun i => evolve x i c))

/-- The guess, computed from the inner cone. -/
def innerGuess (pred : ℕ → (ℕ → Bool) → Bool) (c : ℤ) (t : ℕ) (v : innerCone c t → Bool) : Bool :=
  pred t (fun i => evolve (extW (innerCone c t) v) i c)

theorem pred_eq_innerGuess {pred : ℕ → (ℕ → Bool) → Bool} (hc : IsCausal pred) (c : ℤ) (t : ℕ)
    (x : Config) : pred t (fun i => evolve x i c) = innerGuess pred c t (restr (innerCone c t) x) :=
  hc t _ _ (fun i hi => (evolve_extW_eq c i t hi x).symm)

theorem measurable_hit (pred : ℕ → (ℕ → Bool) → Bool) (hc : IsCausal pred) (c : ℤ) (t : ℕ) :
    Measurable (hit pred c t) := by
  have : hit pred c t = fun x => decide (evolve x t c = innerGuess pred c t (restr (innerCone c t) x)) := by
    funext x; simp only [hit, pred_eq_innerGuess hc]
  rw [this]
  have h2 : Measurable (fun x : Config => (evolve x t c, innerGuess pred c t (restr (innerCone c t) x))) :=
    (measurable_evolve t c).prodMk ((measurable_of_finite (innerGuess pred c t)).comp (measurable_restr _))
  exact (measurable_of_finite (fun p : Bool × Bool => decide (p.1 = p.2))).comp h2

/-- The hit at time `t` has probability `1/2` given any event about the inner cone. -/
theorem hit_step {pred : ℕ → (ℕ → Bool) → Bool} (hc : IsCausal pred) (c : ℤ) (t : ℕ) (b : Bool)
    (A : Set (innerCone c t → Bool)) :
    bernoulliRow (hit pred c t ⁻¹' {b} ∩ restr (innerCone c t) ⁻¹' A) =
      1 / 2 * bernoulliRow (restr (innerCone c t) ⁻¹' A) := by
  rw [← col_step c t (fun v => if b then innerGuess pred c t v else !innerGuess pred c t v) A]
  congr 1
  ext x
  simp only [Set.mem_inter_iff, Set.mem_preimage, Set.mem_singleton_iff, Set.mem_setOf_eq, hit,
    pred_eq_innerGuess hc]
  cases b <;> cases evolve x t c <;> cases innerGuess pred c t (restr (innerCone c t) x) <;> simp

theorem hit_fair {pred : ℕ → (ℕ → Bool) → Bool} (hc : IsCausal pred) (c : ℤ) (t : ℕ) (b : Bool) :
    bernoulliRow (hit pred c t ⁻¹' {b}) = 1 / 2 := by
  have := hit_step hc c t b Set.univ
  simp only [Set.preimage_univ, Set.inter_univ, measure_univ, mul_one] at this
  exact this

/-- Earlier hits only depend on the inner cone. -/
theorem hit_extW {pred : ℕ → (ℕ → Bool) → Bool} (hc : IsCausal pred) (c : ℤ) {s t : ℕ} (hst : s < t)
    (x : Config) : hit pred c s (extW (innerCone c t) (restr (innerCone c t) x)) = hit pred c s x := by
  unfold hit
  rw [evolve_extW_eq c s t hst]
  congr 2
  exact hc s _ _ (fun i hi => evolve_extW_eq c i t (by omega) x)

theorem hit_indep {pred : ℕ → (ℕ → Bool) → Bool} (hc : IsCausal pred) (c : ℤ) {s t : ℕ} (hst : s < t) :
    IndepFun (hit pred c t) (hit pred c s) bernoulliRow := by
  rw [indepFun_iff_measure_inter_preimage_eq_mul]
  intro B A' _ _
  have hrep : hit pred c s ⁻¹' A' =
      restr (innerCone c t) ⁻¹' {v | hit pred c s (extW (innerCone c t) v) ∈ A'} := by
    ext x; simp only [Set.mem_preimage, Set.mem_setOf_eq, hit_extW hc c hst]
  rw [hrep]
  rcases set_bool_cases B with rfl | rfl | rfl | rfl
  · simp
  · rw [hit_fair hc, hit_step hc]
  · rw [hit_fair hc, hit_step hc]
  · rw [Set.preimage_univ, Set.univ_inter, measure_univ, one_mul]

/-- **Strong law for fair, pairwise independent bits.** -/
theorem ae_hasFrequencyHalf_of_fair_pairwise (Y : ℕ → Config → Bool) (hY : ∀ t, Measurable (Y t))
    (hfair : ∀ t b, bernoulliRow (Y t ⁻¹' {b}) = 1 / 2)
    (hind : Pairwise (fun i j => IndepFun (Y i) (Y j) bernoulliRow)) :
    ∀ᵐ x ∂bernoulliRow, HasFrequencyHalf (fun t => Y t x) := by
  let g : Bool → ℝ := fun b => if b then 1 else 0
  let X : ℕ → Config → ℝ := fun t x => g (Y t x)
  have hmeas : ∀ t, Measurable (X t) := fun t => (measurable_of_finite g).comp (hY t)
  have hint : Integrable (X 0) bernoulliRow := by
    refine (integrable_const (1 : ℝ)).mono' (hmeas 0).aestronglyMeasurable (ae_of_all _ ?_)
    intro x; simp only [X, g]; split_ifs <;> simp
  have hmap : ∀ t, bernoulliRow.map (Y t) = coin := by
    intro t
    rw [Measure.ext_iff_singleton]
    intro b
    rw [Measure.map_apply (hY t) (measurableSet_singleton b), hfair, coin_singleton]
  have hindep : Pairwise (fun i j => IndepFun (X i) (X j) bernoulliRow) := by
    intro i j hij
    exact (hind hij).comp (measurable_of_finite g) (measurable_of_finite g)
  have hident : ∀ i, IdentDistrib (X i) (X 0) bernoulliRow bernoulliRow := by
    intro i
    have : IdentDistrib (Y i) (Y 0) bernoulliRow bernoulliRow :=
      ⟨(hY i).aemeasurable, (hY 0).aemeasurable, by rw [hmap, hmap]⟩
    exact this.comp (measurable_of_finite g)
  have hmean : bernoulliRow[X 0] = 1 / 2 := by
    have : ∫ x, X 0 x ∂bernoulliRow = ∫ b, g b ∂coin := by
      rw [← hmap 0, integral_map (hY 0).aemeasurable (measurable_of_finite g).aestronglyMeasurable]
    rw [this, integral_fintype]
    · simp [g, Measure.real, coin_singleton]
    · exact Integrable.of_finite
  have hslln := strong_law_ae X hint hindep hident
  rw [hmean] at hslln
  filter_upwards [hslln] with x hx
  unfold HasFrequencyHalf freq
  refine hx.congr (fun n => ?_)
  have : ∑ i ∈ Finset.range n, X i x = (ones (fun t => Y t x) n : ℝ) := by
    simp only [X, g, ones]
    rw [Finset.sum_boole]
  rw [this, smul_eq_mul, div_eq_inv_mul]

/-- **No causal predictor beats chance on a typical row.** For every causal predictor and every
column `c`, for almost every row the predictor guesses the column correctly with asymptotic
frequency exactly `1/2`. -/
theorem ae_predictor_hits_half (pred : ℕ → (ℕ → Bool) → Bool) (hc : IsCausal pred) (c : ℤ) :
    ∀ᵐ x ∂bernoulliRow, HasFrequencyHalf (fun t => hit pred c t x) := by
  refine ae_hasFrequencyHalf_of_fair_pairwise (fun t => hit pred c t) (measurable_hit pred hc c)
    (hit_fair hc c) ?_
  intro i j hij
  rcases lt_or_gt_of_ne hij with h | h
  · exact (hit_indep hc c h).symm
  · exact hit_indep hc c h

/-- The wobble at time `t` only depends on the first `t` bits. -/
theorem wobble_causal (t : ℕ) (a b : ℕ → Bool) (h : ∀ i < t, a i = b i) : wobble a t = wobble b t := by
  unfold wobble ones
  rw [Finset.filter_congr (p := fun i => a i = true) (q := fun i => b i = true)
    (fun i hi => by simp only [h i (Finset.mem_range.mp hi)])]

/-- The arrow as a predictor: guess `true` (step up) when `D(t) ≤ 0`, `false` when `D(t) > 0`. -/
def arrowPredictor (t : ℕ) (a : ℕ → Bool) : Bool := decide (wobble a t ≤ 0)

theorem arrowPredictor_causal : IsCausal arrowPredictor := by
  intro t a b h
  unfold arrowPredictor
  rw [wobble_causal t a b h]

/-- When the arrow is non-zero, following it is the same as agreeing with `arrowPredictor`. -/
theorem arrowPredictor_follows (a : ℕ → Bool) (t : ℕ) (h : observerArrow a t ≠ 0) :
    (arrowPredictor t a = a t) ↔ stepDir a t = observerArrow a t := by
  unfold arrowPredictor observerArrow stepDir at *
  rcases lt_trichotomy (wobble a t) 0 with hw | hw | hw
  · rw [Int.sign_eq_neg_one_of_neg hw]
    cases a t <;> simp [hw.le]
  · rw [hw] at h; simp at h
  · rw [Int.sign_eq_one_of_pos hw]
    cases a t <;> simp [not_le.mpr hw]

/-- **The arrow is followed half the time on a typical row.** -/
theorem ae_arrow_followed_half (c : ℤ) :
    ∀ᵐ x ∂bernoulliRow, HasFrequencyHalf (fun t => hit arrowPredictor c t x) :=
  ae_predictor_hits_half arrowPredictor arrowPredictor_causal c

/-- A sequence that is eventually always `true` does not have frequency `1/2`. -/
theorem not_hasFrequencyHalf_of_eventually_true (a : ℕ → Bool) (M : ℕ) (h : ∀ t ≥ M, a t = true) :
    ¬ HasFrequencyHalf a := by
  intro hfreq
  have hones : ∀ n, n - M ≤ ones a n := by
    intro n
    unfold ones
    calc n - M = (Finset.Ico M n).card := by simp
      _ ≤ _ := Finset.card_le_card (fun i hi => by
        simp only [Finset.mem_Ico] at hi
        simp only [Finset.mem_filter, Finset.mem_range]
        exact ⟨hi.2, h i hi.1⟩)
  have hlow : ∀ n : ℕ, 0 < n → 1 - (M : ℝ) / n ≤ freq a n := by
    intro n hn
    unfold freq
    have hn' : (0 : ℝ) < n := by exact_mod_cast hn
    have key : (n : ℝ) - M ≤ ones a n := by
      have := hones n
      rcases le_total M n with hMn | hMn
      · have := Nat.cast_le (α := ℝ) |>.mpr this; push_cast [hMn] at this; linarith
      · have : (n : ℝ) ≤ M := by exact_mod_cast hMn
        have : (0 : ℝ) ≤ ones a n := by positivity
        linarith
    calc 1 - (M : ℝ) / n = ((n : ℝ) - M) / n := by field_simp
      _ ≤ (ones a n : ℝ) / n := div_le_div_of_nonneg_right key hn'.le
  have hlim : Tendsto (fun n : ℕ => 1 - (M : ℝ) / n) atTop (𝓝 1) := by
    simpa using (tendsto_const_div_atTop_nhds_zero_nat (M : ℝ)).const_sub 1
  have := le_of_tendsto_of_tendsto hlim hfreq (eventually_atTop.2 ⟨1, fun n hn => hlow n hn⟩)
  norm_num at this

/-- The lag-`p` predictor: guess that bit `t` repeats bit `t − p`. -/
def lagPredictor (p : ℕ) (t : ℕ) (a : ℕ → Bool) : Bool := if p ≤ t then a (t - p) else false

theorem lagPredictor_causal (p : ℕ) (hp : 0 < p) : IsCausal (lagPredictor p) := by
  intro t a b hab
  simp only [lagPredictor]
  split_ifs with ht
  · exact hab _ (by omega)
  · rfl

/-- The constant predictor "always black". Its hits are the column itself. -/
def constPredictor : ℕ → (ℕ → Bool) → Bool := fun _ _ => true

theorem constPredictor_causal : IsCausal constPredictor := fun _ _ _ _ => rfl

theorem hit_constPredictor (c : ℤ) (t : ℕ) (x : Config) : hit constPredictor c t x = evolve x t c := by
  simp [hit, constPredictor]

/-- **Problem 2 is typicality for the constant predictor.** -/
theorem problem2_iff_const_typical :
    Problem2 ↔ HasFrequencyHalf (fun t => hit constPredictor 0 t seed) := by
  simp only [hit_constPredictor]
  rfl

/-- **Problem 1 follows from typicality for the lag predictors.** If, for every lag `p ≥ 1`, the
guess "bit `t` repeats bit `t − p`" is right on the seed's centre column with frequency `1/2`, then the
centre column is not eventually periodic. (Each lag predictor is typical for almost every row, by
`ae_predictor_hits_half`.) -/
theorem problem1_of_lag_typical
    (h : ∀ p, 0 < p → HasFrequencyHalf (fun t => hit (lagPredictor p) 0 t seed)) :
    Problem1 := by
  rintro ⟨p, hp, N, hN⟩
  have hhit : ∀ t ≥ N + p, hit (lagPredictor p) 0 t seed = true := by
    intro t ht
    simp only [hit, lagPredictor, if_pos (show p ≤ t by omega), decide_eq_true_eq]
    have := hN (t - p) (by omega)
    rw [show t - p + p = t by omega] at this
    exact this
  exact not_hasFrequencyHalf_of_eventually_true _ (N + p) hhit (h p hp)

/-- For almost every row, the column is typical for the constant predictor and for every lag
predictor at once (countably many conditions). -/
theorem ae_typical_const_and_lags (c : ℤ) :
    ∀ᵐ x ∂bernoulliRow, HasFrequencyHalf (fun t => hit constPredictor c t x) ∧
      ∀ p, 0 < p → HasFrequencyHalf (fun t => hit (lagPredictor p) c t x) := by
  have hlag : ∀ᵐ x ∂bernoulliRow, ∀ p, 0 < p → HasFrequencyHalf (fun t => hit (lagPredictor p) c t x) := by
    rw [ae_all_iff]
    intro p
    rcases Nat.eq_zero_or_pos p with rfl | hp
    · exact ae_of_all _ (fun _ h => absurd h (lt_irrefl 0))
    · filter_upwards [ae_predictor_hits_half _ (lagPredictor_causal p hp) c] with x hx
      exact fun _ => hx
  filter_upwards [ae_predictor_hits_half _ constPredictor_causal c, hlag] with x h1 h2
  exact ⟨h1, h2⟩

/-- **No row is typical for all causal predictors.** For every row `x` there is a causal
predictor (one that ignores the past and outputs the column of `x` itself) that is always right. So
"typical" must refer to a restricted class of observers. The seed's centre column is computable,
so it is not typical for every computable predictor either. The classes that matter for the
prize problems are the constant predictor (Problem 2) and the finite-memory lag predictors
(Problem 1). -/
theorem no_row_typical_for_all_predictors (x : Config) (c : ℤ) :
    ∃ pred, IsCausal pred ∧ ¬ HasFrequencyHalf (fun t => hit pred c t x) := by
  refine ⟨fun t _ => evolve x t c, fun _ _ _ _ => rfl, ?_⟩
  apply not_hasFrequencyHalf_of_eventually_true _ 0
  intro t _
  simp [hit]

end GLM.Rule30
