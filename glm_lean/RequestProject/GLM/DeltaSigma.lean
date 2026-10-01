/-
# The dynamic carrier: reaching a real target with finite carriers

`Tower.lean` builds an unbounded ladder of layers over `ℚ` and shows that the
ascent never stops.  This file answers the question the ladder raises next:

> can the machine work with values that are *not* carriers at all — with
> irrational targets, and with the infinite generally?

The mechanism is the one the dynamic-carrier study describes: **first-order
delta-sigma modulation**, carried out here in exact arithmetic.  A target
`t ∈ [0, 1)` is chased by a one-bit quantiser with an error accumulator:

```
s 0     = 0
bit n   = 1 if 1 ≤ s n + t else 0
s (n+1) = s n + t - bit n
```

Nothing about this is random and nothing about it is approximate: the state is
an exact value, the output is a bit, and the whole trajectory is determined by
the target.  Everything the study claims about it is proved here.

* `dsState_mem_Ico` — the accumulator never escapes `[0, 1)`.  This is the
  invariant that makes the loop a *homeostasis* rather than a divergence.
* `dsSum_eq` — the running sum of the bits is exactly `N·t - s N`: the bits
  carry the target, offset by the bounded state.
* `dsAverage_error_le` — hence the time average, a **rational** number
  computed from finitely many bits, is within `1/N` of the target.  The
  `O(1/N)` convergence of the study, as a theorem with an explicit constant.
* `dsAverage_tendsto` — so the trajectory converges to the target, whatever
  the target is: rational, irrational, or transcendental.
* `dsAverage_eq_div` — after `N` steps the average is one of the `N + 1`
  values `k/N`, so `N` steps carry `log₂(N+1)` bits and no more.  The gain is
  real and it is also bounded: this is where the "resolution grows with time"
  claim is made exact.
* `ds_target_unique` — and nothing is lost in the limit: two targets with the
  same trajectory are equal.  The finite carriers do not merely approach the
  target, they *determine* it.

The last two together are the study's thesis in its sharpest form.  A carrier
is finite and always will be; the trajectory is infinite and pins the target
exactly.  `dsLayer` packages each finite prefix of the trajectory as a
`Layer ℝ`, so the delta-sigma stack is a tower in exactly the sense of
`Layers.lean` — but a tower over the *reals*, which `Tower.lean`'s dyadic
tower over `ℚ` could not reach.
-/
import RequestProject.GLM.Layers

namespace GLM.Info

open Layer Filter Topology

/-! ## The modulator -/

/-- The exact error accumulator of a first-order delta-sigma modulator chasing
the target `t`.  The state is the part of the target the emitted bits have not
yet accounted for. -/
noncomputable def dsState (t : ℝ) : ℕ → ℝ
  | 0 => 0
  | n + 1 => if 1 ≤ dsState t n + t then dsState t n + t - 1 else dsState t n + t

/-- The bit emitted at step `n`: the quantiser fires exactly when the
accumulated error plus the target reaches one. -/
noncomputable def dsBit (t : ℝ) (n : ℕ) : ℕ :=
  if 1 ≤ dsState t n + t then 1 else 0

@[simp] lemma dsState_zero (t : ℝ) : dsState t 0 = 0 := rfl

lemma dsBit_le_one (t : ℝ) (n : ℕ) : dsBit t n ≤ 1 := by
  unfold dsBit; split_ifs <;> simp

/-- The defining recurrence, with the bit made explicit: the state carries
forward exactly what the emitted bit did not spend. -/
lemma dsState_succ (t : ℝ) (n : ℕ) :
    dsState t (n + 1) = dsState t n + t - (dsBit t n : ℝ) := by
  show (if 1 ≤ dsState t n + t then dsState t n + t - 1 else dsState t n + t) = _
  unfold dsBit
  split_ifs <;> simp

/-- **The accumulator is bounded.**  It never leaves `[0, 1)`, whatever the
target and however long the loop runs: the repair is a homeostasis, not a
drift. -/
lemma dsState_mem_Ico {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n : ℕ) :
    0 ≤ dsState t n ∧ dsState t n < 1 := by
  induction n with
  | zero => simp
  | succ k ih =>
      obtain ⟨hk0, hk1⟩ := ih
      show 0 ≤ (if 1 ≤ dsState t k + t then dsState t k + t - 1 else dsState t k + t) ∧
        (if 1 ≤ dsState t k + t then dsState t k + t - 1 else dsState t k + t) < 1
      split_ifs with h
      · constructor <;> linarith
      · constructor <;> linarith

lemma dsState_nonneg {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n : ℕ) :
    0 ≤ dsState t n := (dsState_mem_Ico ht0 ht1 n).1

lemma dsState_lt_one {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) (n : ℕ) :
    dsState t n < 1 := (dsState_mem_Ico ht0 ht1 n).2

/-! ## The bits carry the target -/

/-- **The exact bit budget.**  The sum of the first `N` bits is `N·t` minus the
current state — the target, less the part not yet spent. -/
theorem dsSum_eq (t : ℝ) (N : ℕ) :
    ∑ i ∈ Finset.range N, (dsBit t i : ℝ) = N * t - dsState t N := by
  induction N with
  | zero => simp
  | succ k ih =>
      rw [Finset.sum_range_succ, ih, dsState_succ]
      push_cast
      ring

/-- The time average of the first `N` bits: a **rational** number, read off a
finite piece of the trajectory. -/
noncomputable def dsAverage (t : ℝ) (N : ℕ) : ℝ :=
  (∑ i ∈ Finset.range N, (dsBit t i : ℝ)) / N

/-- The average after `N` steps is `k/N` for one of the `N + 1` integers
`k ≤ N`: the resolution available from `N` steps is exactly `1/N`, so a
trajectory of length `N` carries `log₂(N + 1)` bits of the target and no
more. -/
theorem dsAverage_eq_div (t : ℝ) (N : ℕ) :
    ∃ k : ℕ, k ≤ N ∧ dsAverage t N = (k : ℝ) / N := by
  refine ⟨∑ i ∈ Finset.range N, dsBit t i, ?_, ?_⟩
  · calc ∑ i ∈ Finset.range N, dsBit t i
        ≤ ∑ _i ∈ Finset.range N, 1 := Finset.sum_le_sum fun i _ => dsBit_le_one t i
      _ = N := by simp
  · unfold dsAverage
    push_cast
    ring

/-- **The `O(1/N)` law.**  The average of `N` bits is within `1/N` of the
target — an exact bound, not an asymptotic one. -/
theorem dsAverage_error_le {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) {N : ℕ} (hN : 0 < N) :
    |dsAverage t N - t| ≤ 1 / N := by
  have hNpos : (0 : ℝ) < N := by exact_mod_cast hN
  have hs := dsState_mem_Ico ht0 ht1 N
  have key : dsAverage t N - t = -(dsState t N / N) := by
    unfold dsAverage
    rw [dsSum_eq]
    field_simp
    ring
  rw [key, abs_neg, abs_of_nonneg (div_nonneg hs.1 hNpos.le)]
  rw [div_le_div_iff_of_pos_right hNpos]
  exact le_of_lt hs.2

/-- **The trajectory converges to the target.**  Whatever the target is —
rational, irrational, transcendental — the sequence of rational time averages
tends to it.  This is the precise sense in which the machine works with values
no carrier can hold. -/
theorem dsAverage_tendsto {t : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1) :
    Tendsto (fun N => dsAverage t N) atTop (𝓝 t) := by
  have hbound : ∀ N : ℕ, 0 < N → |dsAverage t N - t| ≤ 1 / N :=
    fun N hN => dsAverage_error_le ht0 ht1 hN
  have h0 : Tendsto (fun N : ℕ => (1 : ℝ) / N) atTop (𝓝 0) :=
    tendsto_one_div_atTop_nhds_zero_nat
  have hdiff : Tendsto (fun N => dsAverage t N - t) atTop (𝓝 0) := by
    refine squeeze_zero_norm' ?_ h0
    filter_upwards [eventually_gt_atTop 0] with N hN
    simpa [Real.norm_eq_abs] using hbound N hN
  have := hdiff.add (tendsto_const_nhds : Tendsto (fun _ : ℕ => t) atTop (𝓝 t))
  simpa using this

/-! ## The trajectory determines the target -/

/-- **Nothing is lost in the limit.**  Two targets whose modulators emit the
same bits are the same target.  The infinite trajectory of finite carriers is
a faithful representation of the real number, even though no single carrier
is. -/
theorem ds_target_unique {t u : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1)
    (hu0 : 0 ≤ u) (hu1 : u < 1) (h : ∀ n, dsBit t n = dsBit u n) : t = u := by
  have hEq : ∀ N, dsAverage t N = dsAverage u N := by
    intro N
    unfold dsAverage
    congr 1
    exact Finset.sum_congr rfl fun i _ => by rw [h i]
  have h1 := dsAverage_tendsto ht0 ht1
  have h2 : Tendsto (fun N => dsAverage t N) atTop (𝓝 u) := by
    simpa [hEq] using dsAverage_tendsto hu0 hu1
  exact tendsto_nhds_unique h1 h2

/-! ## The delta-sigma stack as a tower of layers -/

/-- Layer `N` of the delta-sigma stack: what is visible after `N` ticks, namely
the first `N` bits of the trajectory.  Unlike the dyadic tower of `Tower.lean`,
whose carriers are rationals, this is a tower of layers over `ℝ`. -/
noncomputable def dsLayer (N : ℕ) : Layer ℝ where
  View := Fin N → ℕ
  perceive t := fun i => dsBit t i

@[simp] lemma dsLayer_indist_iff (N : ℕ) (t u : ℝ) :
    (dsLayer N).Indist t u ↔ ∀ i : Fin N, dsBit t i = dsBit u i := by
  constructor
  · intro h i; exact congrFun h i
  · intro h; funext i; exact h i

/-- **The stack is cumulative.**  One more tick never costs a distinction: a
longer prefix of the trajectory sees at least as much as a shorter one. -/
theorem ds_refines_succ (N : ℕ) : Refines (dsLayer (N + 1)) (dsLayer N) := by
  intro a b hab
  rw [dsLayer_indist_iff] at hab ⊢
  intro i
  exact hab ⟨i.1, Nat.lt_succ_of_lt i.2⟩

theorem ds_refines_of_le {M N : ℕ} (h : M ≤ N) : Refines (dsLayer N) (dsLayer M) := by
  intro a b hab
  rw [dsLayer_indist_iff] at hab ⊢
  intro i
  exact hab ⟨i.1, lt_of_lt_of_le i.2 h⟩

/-- **The stack separates the reals.**  Two distinct targets in `[0, 1)` are
told apart after finitely many ticks.  Where the dyadic tower over `ℚ` could
only separate rationals, the delta-sigma tower resolves every real. -/
theorem ds_separates {t u : ℝ} (ht0 : 0 ≤ t) (ht1 : t < 1)
    (hu0 : 0 ≤ u) (hu1 : u < 1) (h : t ≠ u) :
    ∃ N : ℕ, ¬ (dsLayer N).Indist t u := by
  by_contra hcon
  push_neg at hcon
  refine h (ds_target_unique ht0 ht1 hu0 hu1 fun n => ?_)
  have := hcon (n + 1)
  rw [dsLayer_indist_iff] at this
  exact this ⟨n, Nat.lt_succ_self n⟩

/-! ## A small target runs the accumulator up in a straight line -/

/-- Before the quantiser first fires, the state is just the accumulated
target. -/
lemma dsState_eq_nsmul {t : ℝ} (ht0 : 0 ≤ t) :
    ∀ n : ℕ, (n : ℝ) * t < 1 → dsState t n = n * t := by
  intro n
  induction n with
  | zero => simp
  | succ k ih =>
      intro hk
      have hkt : (k : ℝ) * t < 1 := by
        have : (k : ℝ) * t ≤ ((k : ℝ) + 1) * t := by nlinarith
        push_cast at hk
        linarith
      have hstate := ih hkt
      show (if 1 ≤ dsState t k + t then dsState t k + t - 1 else dsState t k + t) = _
      rw [hstate]
      have : ¬ (1 ≤ (k : ℝ) * t + t) := by push_cast at hk; linarith
      rw [if_neg this]
      push_cast
      ring

lemma dsBit_eq_zero_of_lt {t : ℝ} (ht0 : 0 ≤ t) {n : ℕ}
    (h : ((n : ℝ) + 1) * t < 1) : dsBit t n = 0 := by
  have hn : (n : ℝ) * t < 1 := by nlinarith
  unfold dsBit
  rw [dsState_eq_nsmul ht0 n hn, if_neg (by nlinarith)]

/-- **Every step of the delta-sigma stack is a strict gain.**  Layer `N`
conflates the target `0` with the target `1/(N+1)`, and layer `N + 1` tells
them apart: the ladder never runs out of work, exactly as the dyadic tower
does not. -/
theorem ds_boundary_nonempty (N : ℕ) :
    (Boundary (dsLayer (N + 1)) (dsLayer N)).Nonempty := by
  set t : ℝ := 1 / ((N : ℝ) + 1) with ht
  have hpos : (0 : ℝ) < (N : ℝ) + 1 := by positivity
  have ht0 : 0 ≤ t := by rw [ht]; positivity
  have hzero : ∀ n : ℕ, dsBit (0 : ℝ) n = 0 := by
    intro n
    exact dsBit_eq_zero_of_lt le_rfl (by simp)
  have hsmall : ∀ n : ℕ, n < N → dsBit t n = 0 := by
    intro n hn
    refine dsBit_eq_zero_of_lt ht0 ?_
    rw [ht]
    rw [mul_one_div, div_lt_one hpos]
    have : (n : ℝ) < N := by exact_mod_cast hn
    linarith
  have hfire : dsBit t N = 1 := by
    have hstate : dsState t N = (N : ℝ) * t := by
      refine dsState_eq_nsmul ht0 N ?_
      rw [ht, mul_one_div, div_lt_one hpos]
      linarith
    have hone : (N : ℝ) * t + t = 1 := by
      rw [ht]
      field_simp
    unfold dsBit
    rw [hstate, if_pos (le_of_eq hone.symm)]
  refine ⟨((0 : ℝ), t), ?_, ?_⟩
  · rw [dsLayer_indist_iff]
    intro i
    rw [hzero, hsmall i.1 i.2]
  · rw [dsLayer_indist_iff]
    push_neg
    exact ⟨⟨N, Nat.lt_succ_self N⟩, by rw [hzero, hfire]; exact zero_ne_one⟩

/-- Restated in the vocabulary of the study: every tick adds a proposition the
previous tick could not state. -/
theorem ds_new_visible (N : ℕ) :
    ∃ P : ℝ → Prop, Visible (dsLayer (N + 1)) P ∧ ¬ Visible (dsLayer N) P :=
  (boundary_nonempty_iff_new_visible (ds_refines_succ N)).1 (ds_boundary_nonempty N)

end GLM.Info
