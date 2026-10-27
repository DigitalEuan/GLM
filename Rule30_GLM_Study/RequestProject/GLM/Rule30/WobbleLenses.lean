module

public import RequestProject.GLM.Rule30.Spectral
public import RequestProject.GLM.Rule30.NoConstantColumn

/-!
# Round 12: reading the wobble through different lenses — the strobe (clock) lens

The wobble `D(N) = ∑_{t<N} w(t)` reads the centre column *continuously*, one bit per step.
A **strobe read** with stride `p` and phase `r` reads only every `p`-th bit:

  `strobe a p r t = a (p·t + r)`.

This is the observer `Y` with a clock and no memory of the data: its "read angle" is the
rational frequency `r/p`.  The ordinary wobble is the stride-1 strobe, and the stride-`p` wobble
splits into `p` phase wobbles (`wobble_strobe_sum`).

Main results (all proved):

* `eventuallyPeriodic_iff_strobes_const` : a bit sequence is eventually periodic **iff** for some
  stride `p ≥ 1` *every* phase of the stride-`p` strobe is eventually constant.
  `problem1_iff_strobes` : **Problem 1 is equivalent to**: for every stride `p ≥ 1` some phase of
  the strobe keeps changing colour.  (The stride-1 case is `centerCol_not_eventually_constant`.)
* `APBalanced a` : every strobe of `a` (every arithmetic progression) has frequency `1/2`.
  `problems_one_and_two_of_apBalanced` : **`APBalanced` gives both Problem 1 and Problem 2.**
* `apBalanced_of_fsTypical` : finite-state typicality implies `APBalanced` (a strobe is a
  finite-state observer whose state is only a clock).
* `exists_apBalanced_not_fsTypical` : the converse fails: some sequence is `APBalanced` but not
  `FSTypical`.  So `SeedAPBalanced` is a **strictly weaker sufficient target** for Problems 1 and 2
  than the Round 5 target `SeedFSTypical` (in the sense that the implication
  `FSTypical → APBalanced` is proved and its converse is refuted for general sequences).
-/

@[expose] public section

namespace GLM.Rule30

open Filter Topology Finset

/-! ## The strobe read -/

/-- The strobe read of stride `p` and phase `r`: `t ↦ a (p·t + r)`. -/
def strobe (a : ℕ → Bool) (p r : ℕ) : ℕ → Bool := fun t => a (p * t + r)

/-- Every arithmetic progression of `a` has frequency `1/2`. -/
def APBalanced (a : ℕ → Bool) : Prop := ∀ p r : ℕ, r < p → HasFrequencyHalf (strobe a p r)

/-- **The strobe target** (open): every arithmetic progression of the centre column has
frequency `1/2`. -/
def SeedAPBalanced : Prop := APBalanced centerCol

@[simp] theorem strobe_one_zero (a : ℕ → Bool) : strobe a 1 0 = a := by
  funext t; simp [strobe]

/-- The stride-`p` wobble is the sum of the `p` phase wobbles. -/
theorem wobble_strobe_sum (a : ℕ → Bool) (p N : ℕ) :
    wobble a (p * N) = ∑ r ∈ range p, wobble (strobe a p r) N := by
  simp only [wobble_eq_sum_wave]
  induction N with
  | zero => simp
  | succ N ih =>
    rw [show p * (N + 1) = p * N + p by ring, Finset.sum_range_add, ih]
    simp only [Finset.sum_range_succ, Finset.sum_add_distrib]
    rfl

/-! ## Analytic helpers -/

/-- Sub-linearity passes to the subsequence `p·M` (rescaled by `M`). -/
theorem tendsto_div_comp_mul {f : ℕ → ℝ} (hf : Tendsto (fun n => f n / n) atTop (𝓝 0)) {p : ℕ}
    (hp : 0 < p) : Tendsto (fun M => f (p * M) / M) atTop (𝓝 0) := by
  have hm : Tendsto (fun M : ℕ => p * M) atTop atTop :=
    tendsto_id.const_mul_atTop' hp
  have h2 := (hf.comp hm).const_mul (p : ℝ)
  rw [mul_zero] at h2
  refine h2.congr' ?_
  filter_upwards [eventually_gt_atTop 0] with M hM
  simp only [Function.comp]
  have : (M : ℝ) ≠ 0 := by positivity
  have : (p : ℝ) ≠ 0 := by positivity
  push_cast
  field_simp

/-- Conversely, a wobble that is sub-linear along multiples of `p` is sub-linear. -/
theorem hasFrequencyHalf_of_mul (a : ℕ → Bool) {p : ℕ} (hp : 0 < p)
    (h : Tendsto (fun M => (wobble a (p * M) : ℝ) / M) atTop (𝓝 0)) : HasFrequencyHalf a := by
  rw [hasFrequencyHalf_iff]
  -- `wobble a n` differs from `wobble a (p * (n / p))` by at most `p`
  have hclose : ∀ n, |(wobble a n : ℝ) - wobble a (p * (n / p))| ≤ p := by
    intro n
    have hle : p * (n / p) ≤ n := Nat.mul_div_le n p
    have hlt : n < p * (n / p) + p := by
      have := Nat.lt_mul_div_succ n hp; rw [mul_add, mul_one] at this; exact this
    have key : ∀ k, |(wobble a (p * (n / p) + k) : ℝ) - wobble a (p * (n / p))| ≤ k := by
      intro k
      induction k with
      | zero => simp
      | succ k ih =>
        rw [show p * (n / p) + (k + 1) = (p * (n / p) + k) + 1 by ring, wobble_succ]
        push_cast
        have : |((if a (p * (n / p) + k) = true then (1 : ℤ) else -1) : ℝ)| = 1 := by
          split_ifs <;> simp
        calc _ = |((wobble a (p * (n / p) + k) : ℝ) - wobble a (p * (n / p)))
              + ((if a (p * (n / p) + k) = true then (1 : ℤ) else -1) : ℝ)| := by ring_nf
          _ ≤ _ := abs_add_le _ _
          _ ≤ (k : ℝ) + 1 := by rw [this]; linarith
    have := key (n - p * (n / p))
    rw [Nat.add_sub_cancel' hle] at this
    calc _ ≤ ((n - p * (n / p) : ℕ) : ℝ) := this
      _ ≤ p := by exact_mod_cast (by omega)
  -- the subsequence along `n / p`
  have hdiv : Tendsto (fun n : ℕ => n / p) atTop atTop := Nat.tendsto_div_const_atTop hp.ne'
  have h1 : Tendsto (fun n : ℕ => (wobble a (p * (n / p)) : ℝ) / (n / p : ℕ) * ((n / p : ℕ) / n))
      atTop (𝓝 (0 * (1 / p))) := by
    refine (h.comp hdiv).mul ?_
    -- `(n / p) / n → 1 / p`
    have hlow : ∀ n : ℕ, 0 < n → (1 / p : ℝ) - 1 / n ≤ ((n / p : ℕ) : ℝ) / n := by
      intro n hn
      have hn' : (0 : ℝ) < n := by exact_mod_cast hn
      have hp' : (0 : ℝ) < p := by exact_mod_cast hp
      have : (n : ℝ) < p * ((n / p : ℕ) : ℝ) + p := by
        have := Nat.lt_mul_div_succ n hp; rw [mul_add, mul_one] at this; exact_mod_cast this
      rw [div_sub_div _ _ hp'.ne' hn'.ne', div_le_div_iff₀ (by positivity) hn']
      nlinarith
    have hup : ∀ n : ℕ, 0 < n → ((n / p : ℕ) : ℝ) / n ≤ 1 / p := by
      intro n hn
      have hn' : (0 : ℝ) < n := by exact_mod_cast hn
      have hp' : (0 : ℝ) < p := by exact_mod_cast hp
      have : (p : ℝ) * ((n / p : ℕ) : ℝ) ≤ n := by exact_mod_cast Nat.mul_div_le n p
      rw [div_le_div_iff₀ hn' hp']; linarith
    have hlim : Tendsto (fun n : ℕ => (1 / p : ℝ) - 1 / n) atTop (𝓝 (1 / p)) := by
      simpa using (tendsto_const_div_atTop_nhds_zero_nat (1 : ℝ)).const_sub (1 / (p : ℝ))
    exact tendsto_of_tendsto_of_tendsto_of_le_of_le' hlim tendsto_const_nhds
      (eventually_atTop.2 ⟨1, fun n hn => hlow n hn⟩) (eventually_atTop.2 ⟨1, fun n hn => hup n hn⟩)
  rw [zero_mul] at h1
  have h2 : Tendsto (fun n : ℕ => (wobble a (p * (n / p)) : ℝ) / n) atTop (𝓝 0) := by
    refine h1.congr' ?_
    filter_upwards [eventually_ge_atTop p] with n hn
    have : (0 : ℝ) < ((n / p : ℕ) : ℝ) := by
      exact_mod_cast Nat.div_pos hn hp
    field_simp
  have h3 : Tendsto (fun n : ℕ => (p : ℝ) / n) atTop (𝓝 0) :=
    tendsto_const_div_atTop_nhds_zero_nat _
  rw [tendsto_zero_iff_abs_tendsto_zero] at h2 ⊢
  have h4 := h2.add h3
  rw [add_zero] at h4
  refine squeeze_zero (fun _ => abs_nonneg _) (fun n => ?_) h4
  simp only [Function.comp]
  rcases Nat.eq_zero_or_pos n with rfl | hn
  · simp
  · have hn' : (0 : ℝ) < n := by exact_mod_cast hn
    rw [abs_div, abs_div, abs_of_pos hn', ← add_div, div_le_div_iff_of_pos_right hn']
    have := hclose n
    calc |(wobble a n : ℝ)| = |((wobble a n : ℝ) - wobble a (p * (n / p)))
          + wobble a (p * (n / p))| := by ring_nf
      _ ≤ _ := abs_add_le _ _
      _ ≤ _ := by linarith

/-- **Balanced phases give a balanced whole**: if every phase of the stride-`p` strobe has
frequency `1/2`, so does the sequence. -/
theorem hasFrequencyHalf_of_strobes (a : ℕ → Bool) {p : ℕ} (hp : 0 < p)
    (h : ∀ r < p, HasFrequencyHalf (strobe a p r)) : HasFrequencyHalf a := by
  refine hasFrequencyHalf_of_mul a hp ?_
  have hs : ∀ r ∈ range p,
      Tendsto (fun M => (wobble (strobe a p r) M : ℝ) / M) atTop (𝓝 0) :=
    fun r hr => (hasFrequencyHalf_iff _).1 (h r (Finset.mem_range.1 hr))
  have := tendsto_finset_sum (range p) hs
  simp only [Finset.sum_const_zero] at this
  refine this.congr (fun M => ?_)
  rw [wobble_strobe_sum, ← Finset.sum_div]; push_cast; rfl

theorem wobble_not (a : ℕ → Bool) (n : ℕ) : wobble (fun t => !a t) n = - wobble a n := by
  induction n with
  | zero => simp
  | succ n ih => rw [wobble_succ, wobble_succ, ih]; cases a n <;> simp <;> ring

theorem hasFrequencyHalf_not {a : ℕ → Bool} (h : HasFrequencyHalf a) :
    HasFrequencyHalf (fun t => !a t) := by
  rw [hasFrequencyHalf_iff] at *
  have := h.neg
  simp only [neg_zero] at this
  refine this.congr (fun n => ?_)
  rw [wobble_not]; push_cast; ring

/-- An eventually constant sequence does not have frequency `1/2`. -/
theorem not_hasFrequencyHalf_of_eventually_const (a : ℕ → Bool) (b : Bool) (N : ℕ)
    (h : ∀ t ≥ N, a t = b) : ¬ HasFrequencyHalf a := by
  cases b with
  | true => exact not_hasFrequencyHalf_of_eventually_true a N h
  | false =>
    intro ha
    exact not_hasFrequencyHalf_of_eventually_true _ N (fun t ht => by simp [h t ht])
      (hasFrequencyHalf_not ha)

/-! ## Problem 1 in the strobe lens -/

/-- A periodic sequence has eventually constant strobes at its period. -/
theorem strobe_eventually_const_of_periodic {a : ℕ → Bool} {p N : ℕ} (hp : 0 < p)
    (h : ∀ n ≥ N, a (n + p) = a n) (r : ℕ) : ∀ t ≥ N, strobe a p r t = strobe a p r N := by
  intro t ht
  induction t, ht using Nat.le_induction with
  | base => rfl
  | succ t ht ih =>
    rw [← ih]
    simp only [strobe]
    rw [show p * (t + 1) + r = (p * t + r) + p by ring]
    exact h _ (by nlinarith)

/-- **Eventual periodicity in the strobe lens**: `a` is eventually periodic iff, for some stride
`p ≥ 1`, every phase of the stride-`p` strobe is eventually constant. -/
theorem eventuallyPeriodic_iff_strobes_const (a : ℕ → Bool) :
    EventuallyPeriodic a ↔ ∃ p > 0, ∀ r < p, ∃ b N, ∀ t ≥ N, strobe a p r t = b := by
  constructor
  · rintro ⟨p, hp, N, h⟩
    exact ⟨p, hp, fun r _ => ⟨_, N, strobe_eventually_const_of_periodic hp h r⟩⟩
  · rintro ⟨p, hp, h⟩
    choose! b N hN using h
    refine ⟨p, hp, p * (range p).sup N, fun n hn => ?_⟩
    have hr : n % p < p := Nat.mod_lt _ hp
    have hdiv : n = p * (n / p) + n % p := (Nat.div_add_mod n p).symm
    have ht : (range p).sup N ≤ n / p := by
      rw [Nat.le_div_iff_mul_le hp]; linarith [mul_comm p ((range p).sup N)]
    have hNr : N (n % p) ≤ n / p :=
      le_trans (Finset.le_sup (f := N) (Finset.mem_range.2 hr)) ht
    have e1 := hN (n % p) hr (n / p) hNr
    have e2 := hN (n % p) hr (n / p + 1) (by omega)
    simp only [strobe] at e1 e2
    rw [show p * (n / p + 1) + n % p = n + p by rw [mul_add]; omega] at e2
    rw [← hdiv] at e1
    rw [e1, e2]

/-- **Problem 1 in the strobe lens**: for every stride `p ≥ 1`, some phase of the strobe of the
centre column keeps changing colour. -/
theorem problem1_iff_strobes :
    Problem1 ↔ ∀ p > 0, ∃ r < p, ¬ ∃ b N, ∀ t ≥ N, strobe centerCol p r t = b := by
  unfold Problem1
  rw [eventuallyPeriodic_iff_strobes_const]
  push_neg
  rfl

/-! ## The strobe target `APBalanced` -/

theorem not_eventuallyPeriodic_of_apBalanced {a : ℕ → Bool} (h : APBalanced a) :
    ¬ EventuallyPeriodic a := by
  intro hp
  obtain ⟨p, hp, hc⟩ := (eventuallyPeriodic_iff_strobes_const a).1 hp
  obtain ⟨b, N, hN⟩ := hc 0 hp
  exact not_hasFrequencyHalf_of_eventually_const _ b N hN (h p 0 hp)

theorem hasFrequencyHalf_of_apBalanced {a : ℕ → Bool} (h : APBalanced a) :
    HasFrequencyHalf a := by
  simpa using h 1 0 one_pos

/-- **The strobe target settles Problems 1 and 2.** -/
theorem problems_one_and_two_of_seed_apBalanced (h : SeedAPBalanced) : Problem1 ∧ Problem2 :=
  ⟨not_eventuallyPeriodic_of_apBalanced h, hasFrequencyHalf_of_apBalanced h⟩

/-! ## Strobes are clock observers: `FSTypical → APBalanced` -/

/-- The clock observer: its state is `t mod p`, and it guesses `g (t mod p)`. -/
def clockObserver (p : ℕ) (hp : 0 < p) (g : ℕ → Bool) : FSObserver (Fin p) where
  init := ⟨0, hp⟩
  update s _ := ⟨(s.val + 1) % p, Nat.mod_lt _ hp⟩
  guess s := g s.val

theorem clockObserver_state (p : ℕ) (hp : 0 < p) (g : ℕ → Bool) (a : ℕ → Bool) (t : ℕ) :
    (clockObserver p hp g).state a t = ⟨t % p, Nat.mod_lt _ hp⟩ := by
  induction t with
  | zero => simp [FSObserver.state, clockObserver]
  | succ t ih =>
    change (clockObserver p hp g).update ((clockObserver p hp g).state a t) (a t) = _
    rw [ih]; ext; simp [clockObserver, Nat.add_mod]

theorem clockObserver_predict (p : ℕ) (hp : 0 < p) (g : ℕ → Bool) (a : ℕ → Bool) (t : ℕ) :
    (clockObserver p hp g).predict t a = g (t % p) := by
  simp only [FSObserver.predict, clockObserver_state]; rfl

theorem wave_decide_eq (a b : ℕ → Bool) (t : ℕ) :
    wave (fun t => decide (a t = b t)) t = wave a t * wave b t := by
  unfold wave; cases ha : a t <;> cases hb : b t <;> simp [ha, hb]

theorem sum_range_mul_ite_mod (f : ℕ → ℤ) {p r : ℕ} (hr : r < p) (M : ℕ) :
    ∑ t ∈ range (p * M), (if t % p = r then f t else 0) = ∑ m ∈ range M, f (p * m + r) := by
  induction M with
  | zero => simp
  | succ M ih =>
    rw [show p * (M + 1) = p * M + p by ring, Finset.sum_range_add, ih, Finset.sum_range_succ]
    congr 1
    have : ∀ i ∈ range p, (if (p * M + i) % p = r then f (p * M + i) else 0) =
        if i = r then f (p * M + r) else 0 := by
      intro i hi
      rw [Finset.mem_range] at hi
      rw [show (p * M + i) % p = i by rw [Nat.mul_add_mod]; exact Nat.mod_eq_of_lt hi]
      split_ifs with h <;> simp [h]
    rw [Finset.sum_congr rfl this, Finset.sum_ite_eq']
    simp [hr]

/-- The hit-count difference of two clock observers isolates one phase of the strobe. -/
theorem clock_wobble_diff (a : ℕ → Bool) {p r : ℕ} (hr : r < p) (M : ℕ) :
    wobble (fun t => decide (a t = decide (t % p = r))) (p * M)
      - wobble (fun t => decide (a t = false)) (p * M) = 2 * wobble (strobe a p r) M := by
  rw [wobble_eq_sum_wave, wobble_eq_sum_wave, wobble_eq_sum_wave]
  simp only [wave_decide_eq (a := a) (b := fun t => decide (t % p = r)),
    wave_decide_eq (a := a) (b := fun _ => false)]
  rw [← Finset.sum_sub_distrib]
  have := sum_range_mul_ite_mod (fun t => wave a t) hr M
  have e : ∀ m, wave (strobe a p r) m = wave a (p * m + r) := fun m => rfl
  simp only [e]
  rw [← this, Finset.mul_sum]
  refine Finset.sum_congr rfl (fun t _ => ?_)
  by_cases h : t % p = r <;> simp only [h, wave] <;> cases a t <;> simp

/-- **Finite-state typical ⇒ AP-balanced.** -/
theorem apBalanced_of_fsTypical {a : ℕ → Bool} (h : FSTypical a) : APBalanced a := by
  intro p r hr
  have hp : 0 < p := by omega
  have h1 := h p (clockObserver p hp (fun s => decide (s = r)))
  have h0 := h p (clockObserver p hp (fun _ => false))
  simp only [clockObserver_predict] at h1 h0
  rw [hasFrequencyHalf_iff] at h1 h0 ⊢
  have hf : Tendsto (fun n : ℕ =>
      (((wobble (fun t => decide (a t = decide (t % p = r))) n : ℝ)
        - wobble (fun t => decide (a t = false)) n) / 2) / n) atTop (𝓝 0) := by
    have := (h1.sub h0).div_const 2
    rw [sub_zero, zero_div] at this
    refine this.congr (fun n => ?_)
    ring
  refine (tendsto_div_comp_mul hf hp).congr (fun M => ?_)
  congr 1
  have := clock_wobble_diff a hr M
  have : ((wobble (fun t => decide (a t = decide (t % p = r))) (p * M) : ℤ) : ℝ)
      - (wobble (fun t => decide (a t = false)) (p * M) : ℝ)
        = 2 * (wobble (strobe a p r) M : ℝ) := by
    exact_mod_cast this
  rw [this]; ring

theorem seedAPBalanced_of_seedFSTypical (h : SeedFSTypical) : SeedAPBalanced :=
  apBalanced_of_fsTypical h

/-! ## The strobe target is strictly weaker than finite-state typicality -/

/-- The doubled sequence `t ↦ c (t / 2)` (each bit read twice). -/
def doubled (c : ℕ → Bool) : ℕ → Bool := fun t => c (t / 2)

theorem apBalanced_doubled {c : ℕ → Bool} (hc : APBalanced c) : APBalanced (doubled c) := by
  intro p r hr
  refine hasFrequencyHalf_of_strobes _ two_pos (fun j hj => ?_)
  have hlt : (p * j + r) / 2 < p := by
    interval_cases j <;> omega
  have : strobe (strobe (doubled c) p r) 2 j = strobe c p ((p * j + r) / 2) := by
    funext t
    simp only [strobe, doubled]
    congr 1
    rw [show p * (2 * t + j) + r = (p * j + r) + 2 * (p * t) by ring, Nat.add_mul_div_left _ _ two_pos]
    ring
  rw [this]
  exact hc p _ hlt

/-- The "repeat at odd times" observer: state `2·(t mod 2) + (last bit)`; at odd times it guesses
the previous bit, at even times it guesses black. -/
def repeatObserver : FSObserver (Fin 4) where
  init := 0
  update s bit := ⟨2 * ((s.val / 2 + 1) % 2) + (if bit then 1 else 0), by split_ifs <;> omega⟩
  guess s := if s.val / 2 = 1 then decide (s.val % 2 = 1) else true

theorem repeatObserver_update_val (s : Fin 4) (bit : Bool) :
    (repeatObserver.update s bit).val = 2 * ((s.val / 2 + 1) % 2) + (if bit then 1 else 0) := rfl

theorem repeatObserver_guess (s : Fin 4) :
    repeatObserver.guess s = if s.val / 2 = 1 then decide (s.val % 2 = 1) else true := rfl

theorem repeatObserver_state_succ (a : ℕ → Bool) (t : ℕ) :
    (repeatObserver.state a (t + 1)).val = 2 * ((t + 1) % 2) + (if a t then 1 else 0) := by
  induction t with
  | zero =>
    change (repeatObserver.update repeatObserver.init (a 0)).val = _
    rw [repeatObserver_update_val]; rfl
  | succ t ih =>
    change (repeatObserver.update (repeatObserver.state a (t + 1)) (a (t + 1))).val = _
    rw [repeatObserver_update_val, ih]
    split_ifs <;> omega

theorem repeatObserver_predict_even (a : ℕ → Bool) (t : ℕ) :
    repeatObserver.predict (2 * t) a = true := by
  rcases Nat.eq_zero_or_pos t with rfl | ht
  · change repeatObserver.guess repeatObserver.init = true
    decide
  · obtain ⟨s, rfl⟩ : ∃ s, t = s + 1 := ⟨t - 1, by omega⟩
    have h := repeatObserver_state_succ a (2 * s + 1)
    rw [show 2 * s + 1 + 1 = 2 * (s + 1) by ring] at h
    simp only [FSObserver.predict]
    rw [repeatObserver_guess, if_neg]
    rw [h]; split_ifs <;> omega

theorem repeatObserver_predict_odd (a : ℕ → Bool) (t : ℕ) :
    repeatObserver.predict (2 * t + 1) a = a (2 * t) := by
  have h := repeatObserver_state_succ a (2 * t)
  simp only [FSObserver.predict]
  rw [repeatObserver_guess, if_pos (by rw [h]; split_ifs <;> omega), h]
  cases a (2 * t) <;> simp

theorem wobble_const_true (n : ℕ) : wobble (fun _ => true) n = n := by
  induction n with
  | zero => simp
  | succ n ih => rw [wobble_succ, ih]; simp

theorem not_fsTypical_doubled {c : ℕ → Bool} (hc : HasFrequencyHalf c) :
    ¬ FSTypical (doubled c) := by
  intro h
  have hO := h 4 repeatObserver
  set hit := fun t => decide (doubled c t = repeatObserver.predict t (doubled c)) with hhit
  have h0 : strobe hit 2 0 = c := by
    funext t
    simp only [hhit, strobe, doubled, add_zero, repeatObserver_predict_even]
    rw [show 2 * t / 2 = t by omega]; cases c t <;> rfl
  have h1 : strobe hit 2 1 = fun _ => true := by
    funext t
    simp only [hhit, strobe, doubled, repeatObserver_predict_odd]
    rw [show (2 * t + 1) / 2 = t by omega, show 2 * t / 2 = t by omega]; simp
  have hw : ∀ M, (wobble hit (2 * M) : ℝ) = wobble c M + M := by
    intro M
    rw [wobble_strobe_sum, Finset.sum_range_succ, Finset.sum_range_one, h0, h1, wobble_const_true]
    push_cast; ring
  rw [hasFrequencyHalf_iff] at hO hc
  have hA := tendsto_div_comp_mul hO two_pos
  have hB := hA.sub hc
  rw [sub_zero] at hB
  have : Tendsto (fun M : ℕ => (M : ℝ) / M) atTop (𝓝 0) :=
    hB.congr (fun M => by rw [hw]; ring)
  have h1' : Tendsto (fun M : ℕ => (M : ℝ) / M) atTop (𝓝 1) := by
    refine tendsto_const_nhds.congr' ?_
    filter_upwards [eventually_gt_atTop 0] with M hM
    have : (M : ℝ) ≠ 0 := by positivity
    field_simp
  exact absurd (tendsto_nhds_unique this h1') (by norm_num)

/-- **The strobe target is strictly weaker**: some sequence is AP-balanced but not finite-state
typical (a doubled finite-state typical sequence: every bit is read twice). -/
theorem exists_apBalanced_not_fsTypical : ∃ a : ℕ → Bool, APBalanced a ∧ ¬ FSTypical a := by
  obtain ⟨x, hx⟩ := exists_fsTypical_column 0
  have hc := apBalanced_of_fsTypical hx
  exact ⟨doubled _, apBalanced_doubled hc, not_fsTypical_doubled (hasFrequencyHalf_of_apBalanced hc)⟩

end GLM.Rule30
