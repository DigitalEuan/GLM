module

public import RequestProject.GLM.Rule30.FiniteState
public import RequestProject.GLM.Rule30.NoConstantColumn

/-!
# Round 14: shortcut paths — jump rules and lattice lenses

The study asked whether the centre column might be "jumping through shortcut paths" — following a
rule that takes it through its own past (or through the GLM's lattice network) by long jumps
rather than along an obvious straight path.  This file makes both readings exact.

## Jump rules (shortcuts through the column's own past)

A *jump rule* with look-back `J` predicts bit `t` from the `J` previous bits:
`a t = f (a (t-1), …, a (t-J))`.  The function `f` may use only a few of these positions (the
"taps"), which may lie far back: that is a shortcut path.  A *linear* jump rule is one where `f`
is the XOR of a set of taps.

* `eventuallyPeriodic_iff_jumpRule` : a bit sequence is eventually periodic **iff** some jump rule
  holds from some time on — and then already a linear one with a single tap
  (`eventuallyPeriodic_iff_linearJumpRule`).
* `problem1_iff_no_jumpRule`, `problem1_iff_no_linearJumpRule` : **Problem 1 is equivalent to:**
  no jump rule, with any taps and any rule `f`, ever takes over the centre column — and equally,
  no linear one does.  "The path follows a hidden shortcut forever" is exactly the negation of
  Problem 1.
* `centerCol_lookback_one` : the ladder starts at look-back 1, and there only one rule survives
  the proved facts — "flip the last bit".  Ruling it out is the period-2 case of Problem 1, the
  narrowest open rung.
* `jumpRule_hits_half_of_seedFSTypical` : under the Seed Typicality target, every jump rule is
  right exactly half of the time in the long run (a jump rule is a finite-state observer).

## Lattice lenses (the GLM's network)

A *lens* reads the column through a window of `k` bits every `s` steps and maps the window to a
point of some network (`lensWalk F s`).  The GLM's Golay/Leech network is one such lens: 24-bit
words, snapped to Golay codewords.

* `evPeriodic_lensWalk`, `problem1_of_lensWalk_not_evPeriodic` : every lens walk of an eventually
  periodic sequence is eventually periodic.  So proving that *some* lens walk of the centre column
  never settles into a cycle would prove Problem 1 — a pattern in the network is a pattern of the
  column.
* `problem1_iff_lensWalk_not_evPeriodic` : for a lossless lens (injective `F`, `1 ≤ s ≤ k`, such
  as the raw 24-bit words before snapping) this is an equivalence: the walk view of Problem 1 is
  Problem 1 itself, neither weaker nor stronger.
* `lens_freq_of_blockNormal` : if every `k`-bit word occurs in the column with frequency `2^-k`,
  then every network point (every hop type) occurs with frequency exactly
  `#(preimage) / 2^k` — the "pattern-free prediction" computed in `rule30_round14`.
* `hasFrequencyHalf_of_blockNormal_one` : the case `k = 1` is Problem 2.
-/

@[expose] public section

namespace GLM.Rule30

open Filter Topology Finset

/-! ## Jump rules -/

/-- The `J` bits before time `t`, newest first (`pastWindow a J t i = a (t - 1 - i)`); positions
before time `0` read as white. -/
def pastWindow (a : ℕ → Bool) (J t : ℕ) : Fin J → Bool :=
  fun i => if (i : ℕ) < t then a (t - 1 - i) else false

/-- The jump rule `f` with look-back `J` reproduces `a` at every time `t ≥ N`. -/
def JumpRuleFrom (a : ℕ → Bool) (J : ℕ) (f : (Fin J → Bool) → Bool) (N : ℕ) : Prop :=
  ∀ t ≥ N, a t = f (pastWindow a J t)

/-- The linear rule with tap set `S`: the XOR (parity) of the bits at the taps. -/
def parityRule {J : ℕ} (S : Finset (Fin J)) (w : Fin J → Bool) : Bool :=
  decide (Odd (S.filter (fun i => w i = true)).card)

theorem parityRule_singleton {J : ℕ} (i : Fin J) (w : Fin J → Bool) :
    parityRule {i} w = w i := by
  unfold parityRule
  cases h : w i <;> simp [Finset.filter_singleton, h]

/-- The finite-state observer that remembers the last `J` bits and applies `f`. -/
def jumpObserver (J : ℕ) (f : (Fin J → Bool) → Bool) : FSObserver (Fin J → Bool) where
  init := fun _ => false
  update w b := fun i => if h : (i : ℕ) = 0 then b else w ⟨(i : ℕ) - 1, by omega⟩
  guess := f

theorem jumpObserver_state (J : ℕ) (f : (Fin J → Bool) → Bool) (a : ℕ → Bool) (t : ℕ) :
    (jumpObserver J f).state a t = pastWindow a J t := by
  induction t with
  | zero => funext i; simp [FSObserver.state, jumpObserver, pastWindow]
  | succ t ih =>
    funext i
    show (jumpObserver J f).update ((jumpObserver J f).state a t) (a t) i = _
    rw [ih]
    simp only [jumpObserver, pastWindow]
    by_cases h : (i : ℕ) = 0
    · simp [h]
    · rw [dif_neg h]
      by_cases h2 : (i : ℕ) - 1 < t
      · rw [if_pos h2, if_pos (by omega)]
        congr 1; omega
      · rw [if_neg h2, if_neg (by omega)]

theorem jumpObserver_predict (J : ℕ) (f : (Fin J → Bool) → Bool) (a : ℕ → Bool) (t : ℕ) :
    (jumpObserver J f).predict t a = f (pastWindow a J t) := by
  show f ((jumpObserver J f).state a t) = _
  rw [jumpObserver_state]

/-- A jump rule that holds from some time on forces eventual periodicity. -/
theorem eventuallyPeriodic_of_jumpRule {a : ℕ → Bool} {J : ℕ} {f : (Fin J → Bool) → Bool} {N : ℕ}
    (h : JumpRuleFrom a J f N) : EventuallyPeriodic a :=
  eventuallyPeriodic_of_fsObserver (jumpObserver J f) a
    ⟨N, fun t ht => by rw [jumpObserver_predict]; exact (h t ht).symm⟩

/-- An eventually periodic sequence follows the one-tap linear rule `a t = a (t - p)`. -/
theorem linearJumpRule_of_eventuallyPeriodic {a : ℕ → Bool} (h : EventuallyPeriodic a) :
    ∃ J, ∃ S : Finset (Fin J), ∃ N, JumpRuleFrom a J (parityRule S) N := by
  obtain ⟨p, hp, N, hN⟩ := h
  refine ⟨p, {⟨p - 1, by omega⟩}, N + p, fun t ht => ?_⟩
  rw [parityRule_singleton]
  simp only [pastWindow, show p - 1 < t by omega, if_true]
  have := hN (t - p) (by omega)
  rw [show t - p + p = t by omega] at this
  rw [this]; congr 1; omega

/-- **Eventual periodicity is exactly "some jump rule eventually takes over".** -/
theorem eventuallyPeriodic_iff_jumpRule (a : ℕ → Bool) :
    EventuallyPeriodic a ↔ ∃ J, ∃ f : (Fin J → Bool) → Bool, ∃ N, JumpRuleFrom a J f N := by
  constructor
  · intro h
    obtain ⟨J, S, N, hS⟩ := linearJumpRule_of_eventuallyPeriodic h
    exact ⟨J, parityRule S, N, hS⟩
  · rintro ⟨J, f, N, h⟩
    exact eventuallyPeriodic_of_jumpRule h

/-- … and equally "some *linear* jump rule eventually takes over". -/
theorem eventuallyPeriodic_iff_linearJumpRule (a : ℕ → Bool) :
    EventuallyPeriodic a ↔ ∃ J, ∃ S : Finset (Fin J), ∃ N, JumpRuleFrom a J (parityRule S) N :=
  ⟨linearJumpRule_of_eventuallyPeriodic, fun ⟨_, _, _, h⟩ => eventuallyPeriodic_of_jumpRule h⟩

/-- **Problem 1, restated through shortcut paths.** The centre column is not eventually periodic
iff no jump rule — any look-back, any taps, any rule — ever takes it over. -/
theorem problem1_iff_no_jumpRule :
    Problem1 ↔ ∀ J (f : (Fin J → Bool) → Bool) N, ¬ JumpRuleFrom centerCol J f N := by
  unfold Problem1
  rw [eventuallyPeriodic_iff_jumpRule]
  push_neg
  rfl

/-- **Problem 1 through linear shortcuts.** Equivalently, no linear jump rule (XOR of taps)
ever takes over the centre column. -/
theorem problem1_iff_no_linearJumpRule :
    Problem1 ↔ ∀ J (S : Finset (Fin J)) N, ¬ JumpRuleFrom centerCol J (parityRule S) N := by
  unfold Problem1
  rw [eventuallyPeriodic_iff_linearJumpRule]
  push_neg
  rfl

/-- **The narrowest open rung, in shortcut language.** Of the jump rules with look-back `1`
("copy the last bit", "flip the last bit", "always black", "always white"), only "flip the last
bit" is not already excluded for the centre column (`centerCol_not_eventually_constant`): any
look-back-1 rule that takes over the centre column makes it alternate.  Excluding alternation is
the period-2 case of Problem 1, which remains open. -/
theorem centerCol_lookback_one {f : (Fin 1 → Bool) → Bool} {N : ℕ}
    (h : JumpRuleFrom centerCol 1 f N) : ∀ t ≥ N + 1, centerCol t = !centerCol (t - 1) := by
  have hw : ∀ t ≥ N + 1, centerCol t = f (fun _ => centerCol (t - 1)) := by
    intro t ht
    rw [h t (by omega)]
    congr 1; funext i
    fin_cases i
    simp [pastWindow, show 0 < t by omega]
  have hconst : ∀ b, (∀ t ≥ N + 1, centerCol t = b) → False := fun b hb =>
    centerCol_not_eventually_constant ⟨b, N + 1, hb⟩
  cases h0 : f (fun _ => false) <;> cases h1 : f (fun _ => true)
  · exact (hconst false fun t ht => by
      rw [hw t ht]; cases centerCol (t - 1) <;> simp [h0, h1]).elim
  · exfalso
    refine hconst (centerCol (N + 1)) (fun t ht => ?_)
    induction t, ht using Nat.le_induction with
    | base => rfl
    | succ t ht ih =>
      rw [hw (t + 1) (by omega), Nat.add_sub_cancel, ← ih]
      cases hc : centerCol t <;> simp [h0, h1]
  · intro t ht
    rw [hw t ht]; cases centerCol (t - 1) <;> simp [h0, h1]
  · exact (hconst true fun t ht => by
      rw [hw t ht]; cases centerCol (t - 1) <;> simp [h0, h1]).elim

/-! ### Jump rules as observers: the statistical version -/

/-- Transport a finite-state observer along an equivalence of state spaces. -/
def FSObserver.transport {σ τ : Type} (O : FSObserver σ) (e : σ ≃ τ) : FSObserver τ where
  init := e O.init
  update s b := e (O.update (e.symm s) b)
  guess s := O.guess (e.symm s)

theorem FSObserver.transport_state {σ τ : Type} (O : FSObserver σ) (e : σ ≃ τ) (a : ℕ → Bool)
    (t : ℕ) : (O.transport e).state a t = e (O.state a t) := by
  induction t with
  | zero => rfl
  | succ t ih =>
    show e (O.update (e.symm ((O.transport e).state a t)) (a t)) = e (O.update (O.state a t) (a t))
    rw [ih, Equiv.symm_apply_apply]

theorem FSObserver.transport_predict {σ τ : Type} (O : FSObserver σ) (e : σ ≃ τ) (a : ℕ → Bool)
    (t : ℕ) : (O.transport e).predict t a = O.predict t a := by
  show O.guess (e.symm ((O.transport e).state a t)) = O.guess (O.state a t)
  rw [FSObserver.transport_state, Equiv.symm_apply_apply]

/-- Every observer with a finite state space is covered by `FSTypical`. -/
theorem FSTypical.hits_half {a : ℕ → Bool} (h : FSTypical a) {σ : Type} [Fintype σ]
    (O : FSObserver σ) : HasFrequencyHalf (fun t => decide (a t = O.predict t a)) := by
  have := h _ (O.transport (Fintype.equivFin σ))
  simpa [FSObserver.transport_predict] using this

/-- **Under the Seed Typicality target no jump shortcut beats a coin**: every jump rule, with any
look-back and any taps, is right on the centre column exactly half of the time in the long run. -/
theorem jumpRule_hits_half_of_seedFSTypical (h : SeedFSTypical) (J : ℕ)
    (f : (Fin J → Bool) → Bool) :
    HasFrequencyHalf (fun t => decide (centerCol t = f (pastWindow centerCol J t))) := by
  have := FSTypical.hits_half h (jumpObserver J f)
  simpa [jumpObserver_predict] using this

/-! ## Lattice lenses -/

/-- Eventual periodicity for sequences with values in any type. -/
def EvPeriodic {α : Type*} (b : ℕ → α) : Prop := ∃ p > 0, ∃ N, ∀ n ≥ N, b (n + p) = b n

/-- The walk seen through a lens: the `k`-bit window starting at `s * t`, mapped by `F` to a point
of a network.  (`s = 24, k = 24` is the GLM block lens, `s = 1, k = 24` the sliding lens.) -/
def lensWalk {α : Type*} {k : ℕ} (F : (Fin k → Bool) → α) (s : ℕ) (a : ℕ → Bool) (t : ℕ) : α :=
  F (fun i => a (s * t + i))

/-- **A lens cannot create aperiodicity**: the lens walk of an eventually periodic sequence is
eventually periodic, with the same period. -/
theorem evPeriodic_lensWalk {α : Type*} {k : ℕ} (F : (Fin k → Bool) → α) (s : ℕ) {a : ℕ → Bool}
    (h : EventuallyPeriodic a) : EvPeriodic (lensWalk F s a) := by
  obtain ⟨p, hp, N, hN⟩ := h
  refine ⟨p, hp, N, fun n hn => ?_⟩
  unfold lensWalk
  congr 1
  funext i
  rcases Nat.eq_zero_or_pos s with hs | hs
  · simp [hs]
  · rw [show s * (n + p) + i = (s * n + i) + s * p by ring]
    exact periodic_mul hN s _ (by nlinarith)

/-- **A never-repeating network walk would prove Problem 1.** If the centre column, read through
*any* lens, gives a walk that never settles into a cycle, Problem 1 follows. -/
theorem problem1_of_lensWalk_not_evPeriodic {α : Type*} {k : ℕ} (F : (Fin k → Bool) → α) (s : ℕ)
    (h : ¬ EvPeriodic (lensWalk F s centerCol)) : Problem1 :=
  fun hp => h (evPeriodic_lensWalk F s hp)

/-- For a lossless lens (injective `F`, consecutive windows overlapping or touching) the walk
determines the column, and periodicity transfers back. -/
theorem eventuallyPeriodic_of_lensWalk {α : Type*} {k : ℕ} {F : (Fin k → Bool) → α}
    (hF : Function.Injective F) {s : ℕ} (hs : 0 < s) (hsk : s ≤ k) {a : ℕ → Bool}
    (h : EvPeriodic (lensWalk F s a)) : EventuallyPeriodic a := by
  obtain ⟨p, hp, N, hN⟩ := h
  refine ⟨s * p, Nat.mul_pos hs hp, s * N, fun m hm => ?_⟩
  have hq : N ≤ m / s := (Nat.le_div_iff_mul_le hs).2 (by linarith [mul_comm N s])
  have hw := hF (hN (m / s) hq)
  have := congrFun hw ⟨m % s, lt_of_lt_of_le (Nat.mod_lt _ hs) hsk⟩
  simp only at this
  have e1 : s * (m / s + p) + m % s = m + s * p := by
    have := Nat.div_add_mod m s; nlinarith
  have e2 : s * (m / s) + m % s = m := Nat.div_add_mod m s
  rwa [e1, e2] at this

/-- **For a lossless lens the walk view of Problem 1 is Problem 1 itself.** -/
theorem problem1_iff_lensWalk_not_evPeriodic {α : Type*} {k : ℕ} {F : (Fin k → Bool) → α}
    (hF : Function.Injective F) {s : ℕ} (hs : 0 < s) (hsk : s ≤ k) :
    Problem1 ↔ ¬ EvPeriodic (lensWalk F s centerCol) :=
  ⟨fun h1 h2 => h1 (eventuallyPeriodic_of_lensWalk hF hs hsk h2),
    problem1_of_lensWalk_not_evPeriodic F s⟩

/-! ### Frequencies seen through a lens -/

/-- The `k`-bit window starting at time `t`. -/
def windowAt (a : ℕ → Bool) (k t : ℕ) : Fin k → Bool := fun i => a (t + i)

/-- Number of times `t < n` at which the `k`-window equals `w`. -/
def windowCount (a : ℕ → Bool) (k : ℕ) (w : Fin k → Bool) (n : ℕ) : ℕ :=
  ((range n).filter (fun t => windowAt a k t = w)).card

/-- Every `k`-bit word occurs with asymptotic frequency `2^-k` (normality at block length `k`). -/
def BlockNormal (a : ℕ → Bool) (k : ℕ) : Prop :=
  ∀ w : Fin k → Bool, Tendsto (fun n => (windowCount a k w n : ℝ) / n) atTop (𝓝 (1 / 2 ^ k))

theorem lensWalk_one {α : Type*} {k : ℕ} (F : (Fin k → Bool) → α) (a : ℕ → Bool) (t : ℕ) :
    lensWalk F 1 a t = F (windowAt a k t) := by
  unfold lensWalk windowAt; simp

/-- **Normality fixes the network statistics.** If every `k`-bit word occurs with frequency
`2^-k`, then the sliding lens visits each network point `v` with frequency exactly
`#{w | F w = v} / 2^k`. -/
theorem lens_freq_of_blockNormal {a : ℕ → Bool} {k : ℕ} (h : BlockNormal a k) {α : Type*}
    [DecidableEq α] (F : (Fin k → Bool) → α) (v : α) :
    Tendsto (fun n => (((range n).filter (fun t => lensWalk F 1 a t = v)).card : ℝ) / n) atTop
      (𝓝 (((univ.filter (fun w => F w = v)).card : ℝ) / 2 ^ k)) := by
  have hsplit : ∀ n, (((range n).filter (fun t => lensWalk F 1 a t = v)).card : ℝ) / n =
      ∑ w ∈ univ.filter (fun w => F w = v), (windowCount a k w n : ℝ) / n := by
    intro n
    rw [← Finset.sum_div]
    congr 1
    rw [Finset.card_eq_sum_card_fiberwise (f := fun t => windowAt a k t)
      (t := univ.filter (fun w => F w = v))]
    · push_cast
      refine Finset.sum_congr rfl (fun w hw => ?_)
      simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hw
      unfold windowCount
      rw [Finset.filter_filter]
      congr 2
      refine Finset.filter_congr (fun t _ => ?_)
      rw [lensWalk_one]
      constructor
      · rintro ⟨_, h3⟩; exact h3
      · intro h3; exact ⟨by rw [h3]; exact hw, h3⟩
    · intro t ht
      have ht' := (Finset.mem_filter.1 (Finset.mem_coe.1 ht)).2
      exact Finset.mem_coe.2 (Finset.mem_filter.2 ⟨Finset.mem_univ _, by rw [← lensWalk_one F a t]; exact ht'⟩)
  simp_rw [hsplit]
  have : ((univ.filter (fun w => F w = v)).card : ℝ) / 2 ^ k =
      ∑ _w ∈ univ.filter (fun w => F w = v), (1 / 2 ^ k : ℝ) := by
    rw [Finset.sum_const, nsmul_eq_mul]; ring
  rw [this]
  exact tendsto_finset_sum _ (fun w _ => h w)

/-- Normality at block length `1` is Problem 2's frequency condition. -/
theorem hasFrequencyHalf_of_blockNormal_one {a : ℕ → Bool} (h : BlockNormal a 1) :
    HasFrequencyHalf a := by
  have h1 := h (fun _ => true)
  unfold HasFrequencyHalf freq
  convert h1 using 2 with n
  · unfold ones windowCount
    congr 2
    apply congrArg Finset.card
    ext t
    simp only [Finset.mem_filter, Finset.mem_range, windowAt, funext_iff, Fin.forall_fin_one]
    simp
  · norm_num

end GLM.Rule30
