/-
# Delta–sigma with a lattice alphabet, and the Gibbs-style rule

`DeltaSigma.lean` chases a scalar with one bit, `Cascade.lean` chases a signal,
`Feedback.lean` chases a vector through a rational matrix.  All three emit from
a *fixed, small* alphabet, and `HullExpansion.lean` records the price of that:
what a modulator can read back is exactly the convex hull of what it may emit,
so a target outside the hull is unreachable no matter how long the loop runs.

This file is the general statement of what a **larger alphabet** buys, which is
what "sigma–delta on the Leech shells" asks for.  The quantiser is no longer a
bit or a codeword; it is an arbitrary map `q : V → V` onto a set `A`, and the
only thing assumed about it is a **covering radius**:

```
∀ x, ‖x − q x‖ ≤ ρ.
```

That single hypothesis carries the whole theory.

* `sState_norm_le` — the accumulator never leaves the ball of radius `ρ`,
  whatever the input is.  No hypothesis on the target at all: this is the
  precise sense in which widening the alphabet removes the reachability wall of
  `HullExpansion.lean`.
* `sSum_eq` — the exact accounting identity `∑ out = ∑ in − state`.
* `sAverage_error_le` — hence the emitted points track the input's running mean
  at rate `ρ/N`, and `sAverage_error_le_const` is the constant-target case.
* `avg_mem_convexHull` — every reading is a convex combination of the alphabet,
  which is the other half of `HullExpansion.lean`'s statement, proved here for
  an arbitrary alphabet.

The Leech lattice is the intended instance: its covering radius is `√2` when
its minimum is `4`, so a 24-dimensional loop emitting Leech points tracks *any*
target at rate `√2/N`.  That number is not proved here — a covering-radius
theorem for `Λ₂₄` is a long way outside this development — so it enters as the
hypothesis `hq`, and `roundQuant_covering` shows the hypothesis is satisfiable
rather than vacuous.

## A shell alphabet

A *shell* is not a covering: it is a sphere, and `hq` above is unavailable for
it.  Section 2 supplies the replacement.  The rule is **matched** rather than
nearest — emit the alphabet point the accumulator points at hardest, i.e. the
`argmax` that computes the alphabet's support function — and the hypothesis is
a **margin** `μ`: the support function beats the target by `μ‖s‖` in every
direction, which says exactly that the target sits at distance `μ` inside the
convex hull.

* `shState_norm_le` — the accumulator never leaves the ball of radius
  `D²/(2μ) + D`, where `D` bounds `‖t − v‖` over the alphabet.
* `shAverage_error_le` — hence the `B/N` law for a finite, non-covering
  alphabet.

Together with `HullExpansion.lean` this closes the question for the Leech
shells: outside the hull of the shell no rule can track, inside it the matched
rule tracks at `1/N`, and the constant is explicit.

## The Gibbs-style rule

The second half of the file replaces the *hard snap* — always the nearest
alphabet point — by a temperature-weighted choice among candidates, which is
what the to-do list calls the Gibbs-style rule.  With integer energies `E` and
a rational temperature parameter `t ≥ 1`,

```
gibbsWeight E t i = t ^ (Emax − E i) / ∑ⱼ t ^ (Emax − E j).
```

* `gibbsWeight_uniform` — at `t = 1` every candidate has weight `1/m`: infinite
  temperature is the uniform ensemble.
* `gibbsWeight_le_inv` — a candidate that is not of least energy has weight at
  most `1/t`: as the temperature falls the rule collapses onto the hard snap,
  with an explicit rate.
* `gibbsWeight_mono` — lower energy never has lower weight.

Randomness is not available to a machine that constructs no floats and draws no
samples, so the ensemble is realised **deterministically**, by the same error
feedback the modulator uses: `gibbsCount` is the greedy accumulator rule, and
`gibbsFreq_error_le` proves its visit frequencies converge to the Gibbs weights
at rate `(m−1)/N`.  The trajectory *is* the distribution.
-/
import Mathlib

namespace GLM.Shell

open Finset

/-! ## 1.  A modulator whose alphabet is a lattice -/

section Modulator

variable {V : Type*} [NormedAddCommGroup V]

/-- The accumulator of a vector modulator with quantiser `q` and input `u`. -/
def sState (q : V → V) (u : ℕ → V) : ℕ → V
  | 0 => 0
  | (n + 1) => (sState q u n + u n) - q (sState q u n + u n)

/-- What the modulator emits at tick `n`: a point of the alphabet. -/
def sOut (q : V → V) (u : ℕ → V) (n : ℕ) : V := q (sState q u n + u n)

theorem sState_zero (q : V → V) (u : ℕ → V) : sState q u 0 = 0 := rfl

theorem sState_succ (q : V → V) (u : ℕ → V) (n : ℕ) :
    sState q u (n + 1) = (sState q u n + u n) - sOut q u n := rfl

/-- The covering hypothesis is not vacuous: rounding to the nearest integer
covers `ℝ` at radius `1/2`, which is `DeltaSigma.lean`'s quantiser. -/
theorem roundQuant_covering (x : ℝ) : ‖x - (round x : ℝ)‖ ≤ 1 / 2 := by
  rw [Real.norm_eq_abs]
  exact abs_sub_round x

/-- **The accumulator is bounded by the covering radius**, whatever the input.
This is the statement that a wide enough alphabet has no reachability wall. -/
theorem sState_norm_le {q : V → V} {ρ : ℝ} (hq : ∀ x : V, ‖x - q x‖ ≤ ρ)
    (u : ℕ → V) (n : ℕ) : ‖sState q u n‖ ≤ ρ := by
  cases n with
  | zero =>
      have h0 : (0:ℝ) ≤ ρ := le_trans (norm_nonneg _) (hq 0)
      simpa [sState] using h0
  | succ k => exact hq _

/-- The exact accounting identity: what came out is what went in, less the
accumulator. -/
theorem sSum_eq (q : V → V) (u : ℕ → V) (N : ℕ) :
    ∑ k ∈ range N, sOut q u k = (∑ k ∈ range N, u k) - sState q u N := by
  induction N with
  | zero => simp [sState]
  | succ n ih =>
      rw [Finset.sum_range_succ, Finset.sum_range_succ, ih]
      show _ = _
      simp only [sState, sOut]
      abel

variable [NormedSpace ℝ V]

/-- **The `ρ/N` law.**  The mean of the emitted lattice points tracks the mean
of the input to `ρ/N`, for every input and every target. -/
theorem sAverage_error_le {q : V → V} {ρ : ℝ} (hq : ∀ x : V, ‖x - q x‖ ≤ ρ)
    (u : ℕ → V) {N : ℕ} (hN : 0 < N) :
    ‖(N : ℝ)⁻¹ • (∑ k ∈ range N, sOut q u k)
      - (N : ℝ)⁻¹ • (∑ k ∈ range N, u k)‖ ≤ ρ / N := by
  have hNpos : (0:ℝ) < N := by exact_mod_cast hN
  rw [← smul_sub, sSum_eq, sub_sub_cancel_left, norm_smul, norm_neg]
  simp only [norm_inv, Real.norm_natCast]
  rw [div_eq_inv_mul]
  exact mul_le_mul_of_nonneg_left (sState_norm_le hq u N) (by positivity)

/-- The constant-target case: a fixed point of `V` is held to `ρ/N`. -/
theorem sAverage_error_le_const {q : V → V} {ρ : ℝ} (hq : ∀ x : V, ‖x - q x‖ ≤ ρ)
    (t : V) {N : ℕ} (hN : 0 < N) :
    ‖(N : ℝ)⁻¹ • (∑ k ∈ range N, sOut q (fun _ => t) k) - t‖ ≤ ρ / N := by
  have hNne : (N : ℝ) ≠ 0 := by
    have : (0:ℝ) < N := by exact_mod_cast hN
    exact ne_of_gt this
  have hconst : (N : ℝ)⁻¹ • (∑ _k ∈ range N, t) = t := by
    rw [Finset.sum_const, Finset.card_range, ← Nat.cast_smul_eq_nsmul ℝ,
      inv_smul_smul₀ hNne]
  have h := sAverage_error_le hq (fun _ => t) hN
  rwa [hconst] at h

omit [NormedSpace ℝ V] in
/-- Every emitted point lies in the alphabet. -/
theorem sOut_mem {q : V → V} {A : Set V} (hA : ∀ x : V, q x ∈ A)
    (u : ℕ → V) (n : ℕ) : sOut q u n ∈ A := hA _

/-- **Readings are convex combinations of the alphabet.**  The other half of
`HullExpansion.lean`, for an arbitrary alphabet: widening `A` widens the hull,
and nothing else does. -/
theorem avg_mem_convexHull {A : Set V} (f : ℕ → V) (hf : ∀ n, f n ∈ A)
    {N : ℕ} (hN : 0 < N) :
    (N : ℝ)⁻¹ • (∑ k ∈ range N, f k) ∈ convexHull ℝ A := by
  have hNpos : (0:ℝ) < N := by exact_mod_cast hN
  have hcm : (N : ℝ)⁻¹ • (∑ k ∈ range N, f k)
      = (range N).centerMass (fun _ => (1:ℝ)) f := by
    rw [Finset.centerMass]
    simp
  rw [hcm]
  refine Finset.centerMass_mem_convexHull _ (fun i _ => zero_le_one) ?_ (fun i _ => hf i)
  simpa using hNpos

end Modulator

/-! ## 2.  A *shell* alphabet: finite, non-covering, matched by support -/

section Shell

variable {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]

/-- The accumulator of the **matched** rule chasing a constant target `t`: at
each tick the emitted point is the one the accumulator points at hardest.  Only
`sel` is assumed — it stands for `argmax_{v ∈ A} ⟪s, v⟫`, the support map of the
alphabet — so nothing here needs `A` to cover space. -/
def shState (sel : V → V) (t : V) : ℕ → V
  | 0 => 0
  | (n + 1) => (shState sel t n + t) - sel (shState sel t n)

/-- What the matched rule emits at tick `n`. -/
def shOut (sel : V → V) (t : V) (n : ℕ) : V := sel (shState sel t n)

omit [InnerProductSpace ℝ V] in
theorem shState_zero (sel : V → V) (t : V) : shState sel t 0 = 0 := rfl

omit [InnerProductSpace ℝ V] in
theorem shState_succ (sel : V → V) (t : V) (n : ℕ) :
    shState sel t (n + 1) = (shState sel t n + t) - shOut sel t n := rfl

/-- **A finite alphabet still tracks, provided the target is strictly inside
its hull.**  The alphabet's covering radius is infinite — a shell is a sphere,
it covers nothing — so `sState_norm_le` is unavailable.  What replaces it is a
*margin*: `hmargin` says the support function of the alphabet beats the target
by `μ‖s‖` in every direction `s`, which is exactly the statement that `t` lies
in the interior of the convex hull at distance `μ`.  Then the accumulator never
leaves the ball of radius `D²/(2μ) + D`.

The proof is the one-line energy estimate
`‖s + t − v‖² = ‖s‖² + 2⟪s, t − v⟫ + ‖t − v‖² ≤ ‖s‖² − 2μ‖s‖ + D²`:
far out the drift term wins and the accumulator shrinks; close in the triangle
inequality alone keeps it inside. -/
theorem shState_norm_le {sel : V → V} {t : V} {μ D : ℝ} (hμ : 0 < μ)
    (hD : ∀ s : V, ‖t - sel s‖ ≤ D)
    (hmargin : ∀ s : V, inner ℝ s t ≤ inner ℝ s (sel s) - μ * ‖s‖) (n : ℕ) :
    ‖shState sel t n‖ ≤ D ^ 2 / (2 * μ) + D := by
  have hD0 : 0 ≤ D := le_trans (norm_nonneg _) (hD 0)
  have hB0 : 0 ≤ D ^ 2 / (2 * μ) + D := by positivity
  induction n with
  | zero => simpa [shState] using hB0
  | succ k ih =>
      set s := shState sel t k with hs
      have hstep : shState sel t (k + 1) = s + (t - sel s) := by
        simp [shState, ← hs]; abel
      set e : V := t - sel s with he
      have hinner : inner ℝ s e ≤ -(μ * ‖s‖) := by
        have h := hmargin s
        have : inner ℝ s e = inner ℝ s t - inner ℝ s (sel s) := by
          rw [he, inner_sub_right]
        rw [this]; linarith
      have hnorm : ‖s + e‖ ^ 2 ≤ ‖s‖ ^ 2 - 2 * (μ * ‖s‖) + D ^ 2 := by
        have hexp := norm_add_sq_real s e
        have hE : ‖e‖ ≤ D := hD s
        have hE0 : (0:ℝ) ≤ ‖e‖ := norm_nonneg _
        nlinarith [hexp, hinner, hE, hE0]
      rw [hstep]
      rcases le_or_gt (D ^ 2 / (2 * μ)) ‖s‖ with hfar | hnear
      · have h2 : D ^ 2 ≤ 2 * (μ * ‖s‖) := by
          rw [div_le_iff₀ (by positivity)] at hfar; nlinarith
        have hsq : ‖s + e‖ ^ 2 ≤ ‖s‖ ^ 2 := by linarith
        have : ‖s + e‖ ≤ ‖s‖ := by
          nlinarith [norm_nonneg (s + e), norm_nonneg s]
        exact le_trans this ih
      · calc ‖s + e‖ ≤ ‖s‖ + ‖e‖ := norm_add_le _ _
          _ ≤ D ^ 2 / (2 * μ) + D := add_le_add (le_of_lt hnear) (hD s)

theorem shSum_eq (sel : V → V) (t : V) (N : ℕ) :
    ∑ k ∈ range N, shOut sel t k = (N : ℝ) • t - shState sel t N := by
  induction N with
  | zero => simp [shState]
  | succ n ih =>
      rw [Finset.sum_range_succ, ih, shState_succ]
      push_cast
      rw [add_smul, one_smul]
      abel

/-- **The `B/N` law for a shell alphabet.**  A finite, non-covering alphabet
tracks any target strictly inside its hull at rate `1/N`, with the constant
governed by the margin.  This is the quantitative converse of
`HullExpansion.lean`: outside the hull nothing works, inside it everything
does. -/
theorem shAverage_error_le {sel : V → V} {t : V} {μ D : ℝ} (hμ : 0 < μ)
    (hD : ∀ s : V, ‖t - sel s‖ ≤ D)
    (hmargin : ∀ s : V, inner ℝ s t ≤ inner ℝ s (sel s) - μ * ‖s‖)
    {N : ℕ} (hN : 0 < N) :
    ‖(N : ℝ)⁻¹ • (∑ k ∈ range N, shOut sel t k) - t‖
      ≤ (D ^ 2 / (2 * μ) + D) / N := by
  have hNpos : (0:ℝ) < N := by exact_mod_cast hN
  have hsum := shSum_eq sel t N
  have hrw : (N : ℝ)⁻¹ • (∑ k ∈ range N, shOut sel t k) - t
      = -((N : ℝ)⁻¹ • shState sel t N) := by
    rw [hsum, smul_sub, smul_smul, inv_mul_cancel₀ (ne_of_gt hNpos), one_smul]
    abel
  rw [hrw, norm_neg, norm_smul]
  simp only [norm_inv, Real.norm_natCast]
  rw [div_eq_inv_mul]
  exact mul_le_mul_of_nonneg_left (shState_norm_le hμ hD hmargin N) (by positivity)

end Shell

/-! ## 3.  The Gibbs-style rule -/

section Gibbs

variable {m : ℕ}

/-- The unnormalised Gibbs mass of candidate `i` at temperature parameter `t`,
with integer energies measured down from the largest. -/
def gibbsMass (E : Fin m → ℕ) (t : ℚ) (i : Fin m) : ℚ :=
  t ^ ((Finset.univ.sup E) - E i)

/-- The Gibbs weight: the mass of `i` against the total mass. -/
noncomputable def gibbsWeight (E : Fin m → ℕ) (t : ℚ) (i : Fin m) : ℚ :=
  gibbsMass E t i / ∑ j : Fin m, gibbsMass E t j

theorem gibbsMass_pos {E : Fin m → ℕ} {t : ℚ} (ht : 0 < t) (i : Fin m) :
    0 < gibbsMass E t i := by
  simpa [gibbsMass] using pow_pos ht _

/-- **Infinite temperature is the uniform ensemble.** -/
theorem gibbsWeight_uniform (E : Fin m → ℕ) (i : Fin m) :
    gibbsWeight E 1 i = 1 / m := by
  simp [gibbsWeight, gibbsMass]

/-- **Falling temperature collapses onto the hard snap**, at an explicit rate:
a candidate whose energy is not least has weight at most `1/t`. -/
theorem gibbsWeight_le_inv {E : Fin m → ℕ} {t : ℚ} (ht : 1 ≤ t) {i j : Fin m}
    (hij : E j < E i) : gibbsWeight E t i ≤ 1 / t := by
  have ht0 : (0:ℚ) < t := lt_of_lt_of_le zero_lt_one ht
  have hsupi : E i ≤ Finset.univ.sup E := Finset.le_sup (Finset.mem_univ i)
  have hexp : (Finset.univ.sup E) - E i + 1 ≤ (Finset.univ.sup E) - E j := by omega
  have hmassj : t * gibbsMass E t i ≤ gibbsMass E t j := by
    have h := pow_le_pow_right₀ ht hexp
    simpa [gibbsMass, pow_succ, mul_comm] using h
  have hsum : t * gibbsMass E t i ≤ ∑ k : Fin m, gibbsMass E t k :=
    le_trans hmassj (Finset.single_le_sum (f := fun k => gibbsMass E t k)
      (fun k _ => le_of_lt (gibbsMass_pos ht0 k)) (Finset.mem_univ j))
  have hposi := gibbsMass_pos (E := E) ht0 i
  have hden : (0:ℚ) < ∑ k : Fin m, gibbsMass E t k := lt_of_lt_of_le (by positivity) hsum
  rw [gibbsWeight, div_le_div_iff₀ hden ht0]
  nlinarith [hsum, hposi]

/-- Lower energy never has lower weight. -/
theorem gibbsWeight_mono {E : Fin m → ℕ} {t : ℚ} (ht : 1 ≤ t) {i j : Fin m}
    (hij : E i ≤ E j) : gibbsWeight E t j ≤ gibbsWeight E t i := by
  have ht0 : (0:ℚ) < t := lt_of_lt_of_le zero_lt_one ht
  have hsupj : E j ≤ Finset.univ.sup E := Finset.le_sup (Finset.mem_univ j)
  have hexp : (Finset.univ.sup E) - E j ≤ (Finset.univ.sup E) - E i := by omega
  have hmass : gibbsMass E t j ≤ gibbsMass E t i := pow_le_pow_right₀ ht hexp
  have hden : (0:ℚ) < ∑ k : Fin m, gibbsMass E t k :=
    Finset.sum_pos (fun k _ => gibbsMass_pos ht0 k) ⟨i, Finset.mem_univ i⟩
  exact (div_le_div_iff_of_pos_right hden).mpr hmass

/-! ### Realising the ensemble deterministically -/

/-- A greedy selector: `pick s` is an index at which the accumulator `s` is
largest.  Such a function exists on any nonempty index type
(`exists_maxPick`), and everything below is stated for any of them. -/
def IsMaxPick (pick : (Fin m → ℚ) → Fin m) : Prop :=
  ∀ s : Fin m → ℚ, ∀ i : Fin m, s i ≤ s (pick s)

/-- The hypothesis is satisfiable whenever there is a candidate at all. -/
theorem exists_maxPick (hm : 0 < m) :
    ∃ pick : (Fin m → ℚ) → Fin m, IsMaxPick pick := by
  classical
  have hne : (Finset.univ : Finset (Fin m)).Nonempty := ⟨⟨0, hm⟩, Finset.mem_univ _⟩
  refine ⟨fun s => (Finset.exists_max_image Finset.univ s hne).choose, ?_⟩
  intro s i
  exact (Finset.exists_max_image Finset.univ s hne).choose_spec.2 i (Finset.mem_univ i)

/-- The accumulator state of the scheduler after `n` ticks: every candidate
gains its weight each tick, and the one that is emitted pays a whole unit
back. -/
noncomputable def gibbsState (pick : (Fin m → ℚ) → Fin m) (w : Fin m → ℚ) :
    ℕ → (Fin m → ℚ)
  | 0 => fun _ => 0
  | (n + 1) => fun i =>
      (gibbsState pick w n i + w i) -
        (if i = pick (fun j => gibbsState pick w n j + w j) then 1 else 0)

/-- Which candidate the scheduler emits at tick `n`. -/
noncomputable def gibbsEmit (pick : (Fin m → ℚ) → Fin m) (w : Fin m → ℚ)
    (n : ℕ) : Fin m :=
  pick (fun j => gibbsState pick w n j + w j)

/-- How often candidate `i` has been emitted in the first `N` ticks. -/
noncomputable def gibbsCount (pick : (Fin m → ℚ) → Fin m) (w : Fin m → ℚ)
    (i : Fin m) (N : ℕ) : ℕ :=
  ((range N).filter (fun n => gibbsEmit pick w n = i)).card

theorem gibbsCount_succ (pick : (Fin m → ℚ) → Fin m) (w : Fin m → ℚ)
    (i : Fin m) (N : ℕ) :
    gibbsCount pick w i (N + 1)
      = gibbsCount pick w i N + (if gibbsEmit pick w N = i then 1 else 0) := by
  classical
  unfold gibbsCount
  rw [Finset.range_add_one, Finset.filter_insert]
  by_cases h : gibbsEmit pick w N = i
  · rw [if_pos h, Finset.card_insert_of_notMem (by simp), if_pos h]
  · rw [if_neg h, if_neg h, add_zero]

/-- The accumulator bookkeeping: what has accrued, less what has been paid
out. -/
theorem gibbsState_eq (pick : (Fin m → ℚ) → Fin m) (w : Fin m → ℚ)
    (i : Fin m) (N : ℕ) :
    gibbsState pick w N i = N * w i - gibbsCount pick w i N := by
  induction N with
  | zero => simp [gibbsState, gibbsCount]
  | succ n ih =>
      rw [gibbsCount_succ]
      show gibbsState pick w n i + w i - (if i = gibbsEmit pick w n then 1 else 0) = _
      rw [ih]
      by_cases h : gibbsEmit pick w n = i
      · rw [if_pos h.symm, if_pos h]
        push_cast
        ring
      · rw [if_neg (fun hh => h hh.symm), if_neg h]
        push_cast
        ring

/-- The accumulators always sum to zero: one unit accrues per tick and one unit
is paid out per tick. -/
theorem gibbsState_sum (pick : (Fin m → ℚ) → Fin m) {w : Fin m → ℚ}
    (hsum : ∑ i : Fin m, w i = 1) (N : ℕ) :
    ∑ i : Fin m, gibbsState pick w N i = 0 := by
  induction N with
  | zero => simp [gibbsState]
  | succ n ih =>
      show ∑ i : Fin m, (gibbsState pick w n i + w i
        - (if i = pick (fun j => gibbsState pick w n j + w j) then 1 else 0)) = 0
      rw [Finset.sum_sub_distrib, Finset.sum_add_distrib, ih, hsum]
      simp

/-- Every accumulator stays above `-1`: a candidate only pays out when it is
the largest, and the largest is positive because the accumulators sum to one
just before the payment. -/
theorem gibbsState_neg_one_lt {pick : (Fin m → ℚ) → Fin m}
    (hpick : IsMaxPick pick) {w : Fin m → ℚ} (hw : ∀ i, 0 ≤ w i)
    (hsum : ∑ i : Fin m, w i = 1) (i : Fin m) (N : ℕ) :
    -1 < gibbsState pick w N i := by
  induction N generalizing i with
  | zero => simp [gibbsState]
  | succ n ih =>
      set s : Fin m → ℚ := fun j => gibbsState pick w n j + w j with hs
      have hsum' : ∑ j : Fin m, s j = 1 := by
        rw [hs, Finset.sum_add_distrib, gibbsState_sum pick hsum n, hsum, zero_add]
      have hmaxpos : 0 < s (pick s) := by
        by_contra hcon
        push_neg at hcon
        have hle : ∑ j : Fin m, s j ≤ 0 := by
          calc ∑ j : Fin m, s j ≤ ∑ _j : Fin m, s (pick s) :=
                Finset.sum_le_sum (fun j _ => hpick s j)
            _ = m * s (pick s) := by simp
            _ ≤ 0 := by
                have hmnn : (0:ℚ) ≤ m := by positivity
                nlinarith
        rw [hsum'] at hle
        norm_num at hle
      show gibbsState pick w n i + w i - (if i = pick s then 1 else 0) > -1
      by_cases h : i = pick s
      · rw [if_pos h]
        have hval : gibbsState pick w n i + w i = s (pick s) := by rw [hs, h]
        rw [hval]
        linarith
      · rw [if_neg h]
        have h1 := ih i
        have h2 := hw i
        linarith

/-- **The trajectory is the distribution.**  The visit frequencies of the
deterministic scheduler converge to the Gibbs weights at rate `(m−1)/N`: no
randomness is drawn anywhere, and the ensemble is realised exactly. -/
theorem gibbsFreq_error_le {pick : (Fin m → ℚ) → Fin m}
    (hpick : IsMaxPick pick) {w : Fin m → ℚ} (hw : ∀ i, 0 ≤ w i)
    (hsum : ∑ i : Fin m, w i = 1) (i : Fin m) {N : ℕ} (hN : 0 < N) :
    |(gibbsCount pick w i N : ℚ) / N - w i| ≤ (m - 1) / N := by
  classical
  have hNpos : (0:ℚ) < N := by exact_mod_cast hN
  have hm1 : 1 ≤ m := i.pos
  have hcard : ((Finset.univ.erase i).card : ℚ) = (m : ℚ) - 1 := by
    rw [Finset.card_erase_of_mem (Finset.mem_univ i)]
    simp
    push_cast [Nat.cast_sub hm1]
    ring
  have hsum0 := gibbsState_sum pick hsum N
  have hsplit : gibbsState pick w N i
      + ∑ j ∈ Finset.univ.erase i, gibbsState pick w N j = 0 := by
    rw [← Finset.add_sum_erase _ _ (Finset.mem_univ i)] at hsum0
    exact hsum0
  have hlow : -((m:ℚ) - 1) ≤ ∑ j ∈ Finset.univ.erase i, gibbsState pick w N j := by
    calc -((m:ℚ) - 1) = ∑ _j ∈ Finset.univ.erase i, (-1:ℚ) := by
          rw [Finset.sum_const, nsmul_eq_mul, hcard]; ring
      _ ≤ _ := Finset.sum_le_sum
          (fun j _ => le_of_lt (gibbsState_neg_one_lt hpick hw hsum j N))
  have hupper : gibbsState pick w N i ≤ (m:ℚ) - 1 := by linarith
  have hlower : -((m:ℚ) - 1) ≤ gibbsState pick w N i := by
    rcases Nat.lt_or_ge m 2 with hm | hm
    · have hm' : m = 1 := by omega
      have hempty : Finset.univ.erase i = (∅ : Finset (Fin m)) := by
        apply Finset.eq_empty_of_forall_notMem
        intro j hj
        simp only [Finset.mem_erase] at hj
        exact hj.1 (Fin.ext (by omega))
      rw [hempty] at hsplit
      simp at hsplit
      rw [hsplit, hm']
      norm_num
    · have h2 : (2:ℚ) ≤ (m:ℚ) := by exact_mod_cast hm
      have := gibbsState_neg_one_lt hpick hw hsum i N
      linarith
  have hstate := gibbsState_eq pick w i N
  have hkey : (gibbsCount pick w i N : ℚ) / N - w i = -(gibbsState pick w N i) / N := by
    field_simp
    linarith [hstate]
  rw [hkey, abs_div, abs_of_pos hNpos]
  refine (div_le_div_iff_of_pos_right hNpos).mpr ?_
  rw [abs_le]
  constructor <;> linarith

end Gibbs

end GLM.Shell
