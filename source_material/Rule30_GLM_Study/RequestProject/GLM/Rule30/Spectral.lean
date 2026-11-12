module

public import RequestProject.GLM.Rule30.FiniteState

/-!
# The observer's continuous wave: echoes, resonance and the wobble

This file makes the "continuous-wave radar" picture exact (Round 6, feedback #2).

The observer emits the `±1` *wave* `w(n) = +1` (black) / `−1` (white) of a bit sequence and
listens for its *echo at lag `k`* over a window of length `N`:

  `echo a N k = ∑_{n < N − k} w(n) · w(n + k)`.

Main results (all proved, for arbitrary sequences unless the centre column is named):

* `wobble_eq_sum_wave` : the wobble is the running sum of the wave, `D(N) = ∑_{n<N} w(n)`.
* `wobble_sq_eq_echo` : **the radar identity** (the finite Fejér / Wiener–Khinchin identity)
  `D(N)² = N + 2 · ∑_{1 ≤ k < N} echo a N k`.
  The squared wobble is *exactly* the total echo of the wave.
* `hasFrequencyHalf_iff_totalEcho` and `problem2_iff_totalEcho` : **Problem 2 is equivalent to the
  total echo being `o(N²)`** (no "atom at frequency zero" in the Cesàro sense).  So the spectral
  route is an exact *restatement* of Problem 2, not a shortcut: proving "no resonance at frequency
  zero" for the seed is the same task as proving Problem 2.
* `echo_eq_mismatches` : `echo a N p = (N − p) − 2 · (#mismatches at lag p)`.
* `echo_resonance` : **periodicity is a resonance.** If `a` is eventually periodic with period `p`,
  then `echo a N p / N → 1`.  Contrapositive `problem1_of_no_resonance`: if no lag `p ≥ 1` has a
  full resonance on the centre column, Problem 1 holds.
* `problem1_iff_lag_mismatch` : Problem 1 is equivalent to: for every lag `p ≥ 1` there are
  arbitrarily late mismatches `a(t + p) ≠ a(t)`; and `problem1_iff_mismatches_unbounded`: for every
  `p ≥ 1` the number of lag-`p` mismatches is unbounded.  (This is the "lag-predictor" form of P1
  suggested in feedback #3; it is an equivalence, so excluding one period `p` at a time is genuine
  partial progress, and excluding all of them is Problem 1.)
-/

@[expose] public section

namespace GLM.Rule30

open Finset Filter Topology

/-- The observer's `±1` wave: `+1` for black, `−1` for white. -/
def wave (a : ℕ → Bool) (n : ℕ) : ℤ := if a n then 1 else -1

theorem wave_mul_self (a : ℕ → Bool) (n : ℕ) : wave a n * wave a n = 1 := by
  unfold wave; split_ifs <;> norm_num

/-- The wobble is the running sum of the wave. -/
theorem wobble_eq_sum_wave (a : ℕ → Bool) (N : ℕ) : wobble a N = ∑ n ∈ range N, wave a n := by
  induction N with
  | zero => simp
  | succ N ih => rw [wobble_succ, ih, sum_range_succ]; rfl

/-- The echo of the wave at lag `k` over a window of length `N`. -/
def echo (a : ℕ → Bool) (N k : ℕ) : ℤ := ∑ n ∈ range (N - k), wave a n * wave a (n + k)

/-- The total echo over all positive lags `1 ≤ k < N`. -/
def totalEcho (a : ℕ → Bool) (N : ℕ) : ℤ := ∑ k ∈ Ico 1 N, echo a N k

theorem echo_succ (a : ℕ → Bool) (N k : ℕ) (hk : k ≤ N) :
    echo a (N + 1) k = echo a N k + wave a (N - k) * wave a N := by
  unfold echo
  rw [show N + 1 - k = (N - k) + 1 by omega, sum_range_succ, show N - k + k = N by omega]

theorem totalEcho_succ (a : ℕ → Bool) (N : ℕ) :
    totalEcho a (N + 1) = totalEcho a N + wave a N * wobble a N := by
  unfold totalEcho
  have h1 : ∑ k ∈ Ico 1 (N + 1), echo a (N + 1) k =
      ∑ k ∈ Ico 1 (N + 1), echo a N k + ∑ k ∈ Ico 1 (N + 1), wave a (N - k) * wave a N := by
    rw [← sum_add_distrib]
    refine sum_congr rfl (fun k hk => ?_)
    rw [echo_succ a N k (by simp at hk; omega)]
  have h2 : ∑ k ∈ Ico 1 (N + 1), echo a N k = ∑ k ∈ Ico 1 N, echo a N k := by
    rcases Nat.eq_zero_or_pos N with rfl | hN
    · simp
    · rw [sum_Ico_succ_top (by omega)]
      simp [echo]
  have h3 : ∑ k ∈ Ico 1 (N + 1), wave a (N - k) * wave a N = wave a N * wobble a N := by
    rw [wobble_eq_sum_wave, ← sum_mul, mul_comm, sum_Ico_eq_sum_range, Nat.add_sub_cancel,
      ← sum_range_reflect (fun j => wave a j) N]
    congr 1
    refine sum_congr rfl (fun j hj => ?_)
    simp only [mem_range] at hj
    congr 1; omega
  rw [h1, h2, h3]

/-- **The radar identity.** The squared wobble is the total echo of the wave:
`D(N)² = N + 2 ∑_{1 ≤ k < N} echo a N k`. -/
theorem wobble_sq_eq_echo (a : ℕ → Bool) (N : ℕ) :
    wobble a N ^ 2 = N + 2 * totalEcho a N := by
  induction N with
  | zero => simp [totalEcho]
  | succ N ih =>
    rw [totalEcho_succ, wobble_succ]
    have hw : (if a N = true then (1 : ℤ) else -1) = wave a N := rfl
    rw [hw]
    have := wave_mul_self a N
    push_cast
    nlinarith [ih, this]

/-- **Problem 2 for any sequence is "the total echo is `o(N²)`".** -/
theorem hasFrequencyHalf_iff_totalEcho (a : ℕ → Bool) :
    HasFrequencyHalf a ↔
      Tendsto (fun N : ℕ => (totalEcho a N : ℝ) / (N : ℝ) ^ 2) atTop (𝓝 0) := by
  rw [hasFrequencyHalf_iff]
  have key : ∀ N : ℕ, 0 < N → ((wobble a N : ℝ) / N) ^ 2 =
      1 / N + 2 * ((totalEcho a N : ℝ) / (N : ℝ) ^ 2) := by
    intro N hN
    have hN' : (N : ℝ) ≠ 0 := by positivity
    have h := congrArg (fun z : ℤ => (z : ℝ)) (wobble_sq_eq_echo a N)
    push_cast at h
    field_simp
    rw [h]
  have hinv : Tendsto (fun N : ℕ => (1 : ℝ) / N) atTop (𝓝 0) :=
    tendsto_const_div_atTop_nhds_zero_nat 1
  constructor
  · intro h
    have hsq : Tendsto (fun N : ℕ => ((wobble a N : ℝ) / N) ^ 2) atTop (𝓝 0) := by
      simpa using h.pow 2
    have : Tendsto (fun N : ℕ => (((wobble a N : ℝ) / N) ^ 2 - 1 / N) / 2) atTop (𝓝 0) := by
      simpa using (hsq.sub hinv).div_const 2
    refine this.congr' ?_
    filter_upwards [eventually_gt_atTop 0] with N hN
    rw [key N hN]; ring
  · intro h
    have hsq : Tendsto (fun N : ℕ => ((wobble a N : ℝ) / N) ^ 2) atTop (𝓝 0) := by
      have : Tendsto (fun N : ℕ => 1 / (N : ℝ) + 2 * ((totalEcho a N : ℝ) / (N : ℝ) ^ 2))
          atTop (𝓝 0) := by simpa using hinv.add (h.const_mul 2)
      refine this.congr' ?_
      filter_upwards [eventually_gt_atTop 0] with N hN
      rw [key N hN]
    have habs : Tendsto (fun N : ℕ => |(wobble a N : ℝ) / N|) atTop (𝓝 0) := by
      have := hsq.sqrt
      simp only [Real.sqrt_sq_eq_abs, Real.sqrt_zero] at this
      exact this
    exact (tendsto_zero_iff_abs_tendsto_zero _).mpr habs

/-- **Problem 2 ⇔ the centre column's total echo is `o(N²)`.** -/
theorem problem2_iff_totalEcho :
    Problem2 ↔ Tendsto (fun N : ℕ => (totalEcho centerCol N : ℝ) / (N : ℝ) ^ 2) atTop (𝓝 0) :=
  hasFrequencyHalf_iff_totalEcho centerCol

/-! ## Lag mismatches, resonance and Problem 1 -/

/-- Number of lag-`p` mismatches `a(n + p) ≠ a(n)` with `n < N − p`. -/
def mismatches (a : ℕ → Bool) (N p : ℕ) : ℕ :=
  ((range (N - p)).filter (fun n => a (n + p) ≠ a n)).card

theorem echo_eq_mismatches (a : ℕ → Bool) (N p : ℕ) :
    echo a N p = ((N - p : ℕ) : ℤ) - 2 * (mismatches a N p : ℤ) := by
  unfold echo mismatches
  have : ∀ n, wave a n * wave a (n + p) = 1 - 2 * (if a (n + p) ≠ a n then (1 : ℤ) else 0) := by
    intro n; unfold wave
    cases a n <;> cases a (n + p) <;> simp
  simp_rw [this, sum_sub_distrib, ← mul_sum, sum_boole]
  simp

theorem mismatches_le_of_periodic (a : ℕ → Bool) {p T : ℕ} (h : ∀ n ≥ T, a (n + p) = a n)
    (N : ℕ) : mismatches a N p ≤ T := by
  unfold mismatches
  calc _ ≤ (range T).card := by
        apply card_le_card
        intro n hn
        simp only [mem_filter, mem_range] at hn ⊢
        by_contra hT
        exact hn.2 (h n (by omega))
    _ = T := card_range T

/-- **Periodicity is a resonance.** If `a` is eventually periodic with period `p`, the normalised
echo at lag `p` tends to `1`. -/
theorem echo_resonance (a : ℕ → Bool) {p T : ℕ} (h : ∀ n ≥ T, a (n + p) = a n) :
    Tendsto (fun N : ℕ => (echo a N p : ℝ) / N) atTop (𝓝 1) := by
  have hlow : ∀ N : ℕ, p + 1 ≤ N → 1 - ((p : ℝ) + 2 * T) / N ≤ (echo a N p : ℝ) / N := by
    intro N hN1
    have hN : p ≤ N := by omega
    have hN0 : 0 < N := by omega
    have hm := mismatches_le_of_periodic a h N
    have he := echo_eq_mismatches a N p
    have hNr : (0 : ℝ) < N := by positivity
    rw [one_sub_div hNr.ne', div_le_div_iff_of_pos_right hNr]
    have : (echo a N p : ℝ) = ((N - p : ℕ) : ℝ) - 2 * (mismatches a N p : ℝ) := by
      rw [he]; push_cast; ring
    rw [this, Nat.cast_sub hN]
    have : (mismatches a N p : ℝ) ≤ T := by exact_mod_cast hm
    linarith
  have hup : ∀ N : ℕ, (echo a N p : ℝ) / N ≤ 1 := by
    intro N
    rcases Nat.eq_zero_or_pos N with rfl | hN0
    · simp
    have hNr : (0 : ℝ) < N := by positivity
    rw [div_le_one hNr]
    have he := echo_eq_mismatches a N p
    have : (echo a N p : ℝ) = ((N - p : ℕ) : ℝ) - 2 * (mismatches a N p : ℝ) := by
      rw [he]; push_cast; ring
    rw [this]
    have : ((N - p : ℕ) : ℝ) ≤ N := by exact_mod_cast Nat.sub_le N p
    have : (0 : ℝ) ≤ mismatches a N p := by positivity
    linarith
  have hlim : Tendsto (fun N : ℕ => 1 - ((p : ℝ) + 2 * T) / N) atTop (𝓝 1) := by
    simpa using (tendsto_const_div_atTop_nhds_zero_nat ((p : ℝ) + 2 * T)).const_sub 1
  exact tendsto_of_tendsto_of_tendsto_of_le_of_le' hlim tendsto_const_nhds
    (eventually_atTop.2 ⟨p + 1, hlow⟩) (Eventually.of_forall hup)

/-- **No resonance ⇒ Problem 1.** If at no lag `p ≥ 1` the normalised echo of the centre column
tends to `1`, the centre column is not eventually periodic. -/
theorem problem1_of_no_resonance
    (h : ∀ p, 0 < p → ¬ Tendsto (fun N : ℕ => (echo centerCol N p : ℝ) / N) atTop (𝓝 1)) :
    Problem1 := by
  rintro ⟨p, hp, T, hT⟩
  exact h p hp (echo_resonance centerCol hT)

/-- **Problem 1 in lag form.** For every lag `p ≥ 1` there are arbitrarily late mismatches. -/
theorem problem1_iff_lag_mismatch :
    Problem1 ↔ ∀ p, 0 < p → ∀ N, ∃ t ≥ N, centerCol (t + p) ≠ centerCol t := by
  unfold Problem1 EventuallyPeriodic
  push_neg
  rfl

theorem mismatches_mono (a : ℕ → Bool) (p : ℕ) {N M : ℕ} (h : N ≤ M) :
    mismatches a N p ≤ mismatches a M p := by
  unfold mismatches
  apply card_le_card
  intro n hn
  simp only [mem_filter, mem_range] at hn ⊢
  exact ⟨by omega, hn.2⟩

/-- Infinitely many lag-`p` mismatches ⇔ an unbounded mismatch count. -/
theorem lag_mismatch_iff_unbounded (a : ℕ → Bool) (p : ℕ) :
    (∀ N, ∃ t ≥ N, a (t + p) ≠ a t) ↔ ∀ B, ∃ N, B < mismatches a N p := by
  constructor
  · intro h B
    induction B with
    | zero =>
      obtain ⟨t, -, ht⟩ := h 0
      refine ⟨t + 1 + p, ?_⟩
      unfold mismatches
      rw [Finset.card_pos]
      exact ⟨t, by simp [ht]⟩
    | succ B ih =>
      obtain ⟨N, hN⟩ := ih
      obtain ⟨t, htN, ht⟩ := h N
      refine ⟨t + 1 + p, ?_⟩
      have hsub : (range (N - p)).filter (fun n => a (n + p) ≠ a n) ⊆
          ((range (t + 1 + p - p)).filter (fun n => a (n + p) ≠ a n)).erase t := by
        intro n hn
        simp only [mem_filter, mem_range, mem_erase] at hn ⊢
        exact ⟨by omega, by omega, hn.2⟩
      have hc := card_le_card hsub
      rw [card_erase_of_mem (by simp [ht])] at hc
      unfold mismatches at hN ⊢
      have : 1 ≤ ((range (t + 1 + p - p)).filter (fun n => a (n + p) ≠ a n)).card :=
        Finset.card_pos.mpr ⟨t, by simp [ht]⟩
      omega
  · intro h N
    by_contra hcon
    push_neg at hcon
    obtain ⟨M, hM⟩ := h N
    have : mismatches a M p ≤ N := mismatches_le_of_periodic a (fun n hn => hcon n hn) M
    omega

/-- **Problem 1 ⇔ for every lag `p ≥ 1` the lag-`p` mismatch count is unbounded.** -/
theorem problem1_iff_mismatches_unbounded :
    Problem1 ↔ ∀ p, 0 < p → ∀ B, ∃ N, B < mismatches centerCol N p := by
  rw [problem1_iff_lag_mismatch]
  exact forall_congr' (fun p => imp_congr_right (fun _ => lag_mismatch_iff_unbounded centerCol p))

end GLM.Rule30
