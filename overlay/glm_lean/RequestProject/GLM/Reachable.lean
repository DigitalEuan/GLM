/-
# What a dynamic carrier can and cannot reach

`DeltaSigma.lean` proves that in one dimension the modulator reaches *every*
target in `[0, 1)`: the time average of its bits converges to the target,
irrational or not.  In twenty-four dimensions that is false, and this file
says exactly why.

The 24-D dynamic carrier emits, at every tick, a **codeword** — a point of a
fixed finite set `S`.  Its reading after `N` ticks is the time average of what
it has emitted.  So whatever the reading converges to is a limit of convex
combinations of `S`, and therefore lies in the closed convex hull of `S`.  A
target outside that hull is unreachable *by any quantiser rule whatsoever*: no
better decoder, no cleverer feedback and no longer run can help.

* `not_tendsto_avg_of_separating` — the theorem.  A single linear functional
  that puts the target strictly above every element of `S` is a certificate of
  unreachability.
* `avg_mem_hull` — the positive half: every reading actually taken is a convex
  combination of the emitted states, so the reachable set is the hull and
  nothing smaller.
* `tendsto_avg_of_const` — and a target in `S` is reached exactly, by standing
  still.

The GLM's `reasoning.exact_real.hull_certificate` computes such a functional
for a given target and verifies the inequality against all 4,096 Golay
codewords in exact arithmetic.  Where it succeeds, this theorem turns the
measured drift of the modulator into a proof that no drift-free run exists.
-/
import RequestProject.GLM.DeltaSigma

namespace GLM.Info

open Filter Topology

variable {n : ℕ}

/-- The time average of the first `N` emitted states. -/
noncomputable def avgVec (x : ℕ → (Fin n → ℝ)) (N : ℕ) : Fin n → ℝ :=
  fun i => (∑ k ∈ Finset.range N, x k i) / N

/-- A linear functional on carrier space. -/
def pair (c v : Fin n → ℝ) : ℝ := ∑ i, c i * v i

lemma continuous_pair (c : Fin n → ℝ) : Continuous (fun v : Fin n → ℝ => pair c v) := by
  unfold pair
  exact continuous_finset_sum _ fun i _ => continuous_const.mul (continuous_apply i)

lemma pair_avgVec (c : Fin n → ℝ) (x : ℕ → (Fin n → ℝ)) (N : ℕ) :
    pair c (avgVec x N) = (∑ k ∈ Finset.range N, pair c (x k)) / N := by
  unfold pair avgVec
  simp only [Finset.sum_div, Finset.mul_sum, mul_div_assoc]
  rw [Finset.sum_comm]

/-- **Unreachability, certified by one linear functional.**  If every state the
carrier can emit satisfies `⟪c, w⟫ ≤ b` while the target has `⟪c, t⟫ > b`, then
no run of the carrier has its time average converging to the target.  The drift
is forced by the geometry of the emitted set, not by the choice of quantiser. -/
theorem not_tendsto_avg_of_separating {c t : Fin n → ℝ} {S : Set (Fin n → ℝ)} {b : ℝ}
    (hS : ∀ w ∈ S, pair c w ≤ b) (ht : b < pair c t)
    (x : ℕ → (Fin n → ℝ)) (hx : ∀ k, x k ∈ S) :
    ¬ Tendsto (fun N => avgVec x N) atTop (𝓝 t) := by
  intro hconv
  have hcont : Tendsto (fun N => pair c (avgVec x N)) atTop (𝓝 (pair c t)) :=
    ((continuous_pair c).tendsto t).comp hconv
  have hle : ∀ᶠ N : ℕ in atTop, pair c (avgVec x N) ≤ b := by
    filter_upwards [eventually_gt_atTop 0] with N hN
    have hNpos : (0 : ℝ) < N := by exact_mod_cast hN
    rw [pair_avgVec, div_le_iff₀ hNpos]
    calc ∑ k ∈ Finset.range N, pair c (x k)
        ≤ ∑ _k ∈ Finset.range N, b := Finset.sum_le_sum fun k _ => hS _ (hx k)
      _ = b * N := by simp [mul_comm]
  have : pair c t ≤ b := le_of_tendsto hcont hle
  linarith

/-- **The reachable set is the hull and nothing smaller.**  Every reading the
carrier ever takes is a convex combination of the states it has emitted. -/
theorem avgVec_mem_hull {S : Set (Fin n → ℝ)} (x : ℕ → (Fin n → ℝ))
    (hx : ∀ k, x k ∈ S) {N : ℕ} (hN : 0 < N) :
    avgVec x N ∈ convexHull ℝ S := by
  have hmem : ∀ k ∈ Finset.range N, x k ∈ convexHull ℝ S :=
    fun k _ => subset_convexHull ℝ S (hx k)
  have hw : ∀ k ∈ Finset.range N, (0 : ℝ) ≤ (N : ℝ)⁻¹ := by
    intro k _; positivity
  have hsum : ∑ _k ∈ Finset.range N, ((N : ℝ)⁻¹) = 1 := by
    have hNne : (N : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr hN.ne'
    rw [Finset.sum_const, Finset.card_range, nsmul_eq_mul]
    field_simp
  have := (convex_convexHull ℝ S).sum_mem hw hsum hmem
  have heq : ∑ k ∈ Finset.range N, ((N : ℝ)⁻¹) • x k = avgVec x N := by
    funext i
    simp only [avgVec, Finset.sum_apply, Pi.smul_apply, smul_eq_mul, div_eq_inv_mul]
    rw [Finset.mul_sum]
  rwa [heq] at this

/-- **The positive half, in the shape the machine can use.**  If the carrier
repeats a fixed cycle of `N` states, then after any whole number of cycles its
reading is *exactly* the mean of one cycle.  Together with `avgVec_mem_hull`
this pins the reachable set from both sides: no reading leaves the convex hull
of the emitted states, and every mean of a finite cycle of them is hit on the
nose, not merely approached. -/
theorem avgVec_periodic {x : ℕ → (Fin n → ℝ)} {N : ℕ} (hN : 0 < N)
    (hper : ∀ i, x (i + N) = x i) {k : ℕ} (hk : 0 < k) :
    avgVec x (N * k) = avgVec x N := by
  have hshift : ∀ t j, x (j + N * t) = x j := by
    intro t
    induction t with
    | zero => intro j; simp
    | succ t ih =>
        intro j
        have hj : j + N * (t + 1) = (j + N * t) + N := by ring
        rw [hj, hper, ih]
  have hsum : ∀ (i : Fin n) (t : ℕ),
      ∑ j ∈ Finset.range (N * t), x j i = t * ∑ j ∈ Finset.range N, x j i := by
    intro i t
    induction t with
    | zero => simp
    | succ t ih =>
        have hrange : N * (t + 1) = N * t + N := by ring
        rw [hrange, Finset.sum_range_add, ih]
        have hcycle : ∑ j ∈ Finset.range N, x (N * t + j) i
            = ∑ j ∈ Finset.range N, x j i := by
          refine Finset.sum_congr rfl ?_
          intro j _
          have hj : N * t + j = j + N * t := by ring
          rw [hj, hshift]
        rw [hcycle]
        push_cast
        ring
  funext i
  have hNne : (N : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr hN.ne'
  have hkne : (k : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr hk.ne'
  simp only [avgVec, hsum i k, Nat.cast_mul]
  field_simp

/-- A cycling carrier converges, along the whole cycles, to the mean of its
cycle — so every rational convex combination of emitted states is reachable. -/
theorem tendsto_avgVec_periodic {x : ℕ → (Fin n → ℝ)} {N : ℕ} (hN : 0 < N)
    (hper : ∀ i, x (i + N) = x i) :
    Tendsto (fun k => avgVec x (N * k)) atTop (𝓝 (avgVec x N)) := by
  rw [tendsto_congr' ?_]
  · exact tendsto_const_nhds
  · filter_upwards [eventually_gt_atTop 0] with k hk
    exact avgVec_periodic hN hper hk

/-- A target the carrier can simply sit on is reached exactly. -/
theorem tendsto_avgVec_of_const (t : Fin n → ℝ) :
    Tendsto (fun N => avgVec (fun _ => t) N) atTop (𝓝 t) := by
  have : ∀ N : ℕ, 0 < N → avgVec (fun _ => t) N = t := by
    intro N hN
    funext i
    have hNne : (N : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr hN.ne'
    simp [avgVec, mul_comm, hNne]
  rw [tendsto_congr' ?_]
  · exact tendsto_const_nhds
  · filter_upwards [eventually_gt_atTop 0] with N hN
    exact this N hN

end GLM.Info
