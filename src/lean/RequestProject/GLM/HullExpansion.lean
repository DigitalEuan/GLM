/-
# Broadening the hull: what expanding the emitted alphabet does, and does not, do

`Reachable.lean` shows that a 24-D dynamic carrier which emits Golay codewords
can only ever read points of the convex hull of the code, and that a single
linear functional certifies a target as unreachable.  The proposal this file
tests is to *widen* the alphabet — "allow the modulator to emit Leech lattice
points or scaled codewords" — so that the carrier can wiggle through a larger
space.

Both halves of that proposal are settled here, and they do not agree.

* **Scaling does not help.**  `concTarget_not_mem_hull_scaled` and
  `concTarget_unreachable_scaled`: the target `½·e₀` — half a unit on one
  coordinate and nothing anywhere else — is outside the convex hull of the
  codewords *and stays outside* when every non-negative multiple `λ·c` of every
  codeword is admitted as well.  The obstruction is not the size of the
  codewords but their **supports**: a codeword through coordinate `0` drags at
  least seven other coordinates with it (minimum weight `8`), and scaling
  cannot separate them.  The certificate is the single functional
  `7·x₀ − ∑_{j≠0} xⱼ`, which is `≤ 0` on the whole scaled alphabet — this needs
  nothing but `golay_min_weight`, so it is a statement about the code, not
  about a particular numerical search.

* **New supports do help.**  `concTarget_reached_by_leech`: admitting the
  minimal Leech vectors of shape `(±4², 0²²)` — which have support `2`, a
  support no nonzero codeword has — puts the same target inside reach, and the
  witness is an explicit 16-tick cycle whose reading is *exactly* `½·e₀` at
  every completed cycle, not merely in the limit.

* **The general converse to `Reachable.lean`.**  `cycle_avgVec_eq` says that any
  finite cycle of emitted states is read back exactly as the mean of the cycle.
  With `avgVec_mem_hull` this pins the reachable set from both sides: it is the
  convex hull of the alphabet, no more (`not_tendsto_avg_of_separating`) and no
  less.

The moral for the runtime: widening the alphabet is worth doing, but the thing
to widen is the set of *supports* the quantiser may emit, not the scale.
-/
import RequestProject.GLM.Reachable
import RequestProject.GLM.Golay.Sextet

namespace GLM.Hull

open Finset Filter Topology
open GLM.Golay24 GLM.Info

/-! ## Alphabets -/

/-- A word as a `0/1` vector of reals: what the carrier emits when its alphabet
is the code itself. -/
def indR (s : Word) : Fin 24 → ℝ := fun i => if i ∈ s then 1 else 0

/-- The codeword alphabet. -/
def golayVecs : Set (Fin 24 → ℝ) := {x | ∃ c : Word, IsCodeword c ∧ x = indR c}

/-- The alphabet of *scaled* codewords: every non-negative multiple of every
codeword. -/
def scaledGolayVecs : Set (Fin 24 → ℝ) :=
  {x | ∃ (l : ℝ) (c : Word), 0 ≤ l ∧ IsCodeword c ∧ x = l • indR c}

theorem golayVecs_subset_scaled : golayVecs ⊆ scaledGolayVecs := by
  rintro x ⟨c, hc, rfl⟩
  exact ⟨1, c, zero_le_one, hc, by simp⟩

/-! ## The concentration wall -/

/-- The separating functional `7·x₀ − ∑_{j ≠ 0} xⱼ`, written so that its value
at a `0/1` word is `8·[0 ∈ s] − |s|`. -/
def cvec : Fin 24 → ℝ := fun i => 8 * (if i = 0 then 1 else 0) - 1

/-- The target: half a unit on coordinate `0`, nothing elsewhere. -/
noncomputable def concTarget : Fin 24 → ℝ := fun i => if i = 0 then 1 / 2 else 0

theorem pair_cvec_indR (s : Word) :
    pair cvec (indR s) = 8 * (if (0 : Fin 24) ∈ s then 1 else 0) - s.card := by
  have h1 : pair cvec (indR s) = ∑ i ∈ s, cvec i := by
    unfold pair indR
    rw [Finset.sum_congr rfl (fun i _ => by
      by_cases hi : i ∈ s <;> simp [hi] : ∀ i ∈ (univ : Finset (Fin 24)),
        cvec i * (if i ∈ s then (1 : ℝ) else 0) = if i ∈ s then cvec i else 0)]
    rw [Finset.sum_ite_mem, Finset.univ_inter]
  rw [h1]
  simp only [cvec]
  rw [Finset.sum_sub_distrib, ← Finset.mul_sum,
    Finset.sum_ite_eq' s (0 : Fin 24) (fun _ => (1 : ℝ))]
  simp

/-- The functional is non-positive on every codeword: this is exactly the
minimum-weight bound `8`. -/
theorem pair_cvec_nonpos_codeword {c : Word} (hc : IsCodeword c) :
    pair cvec (indR c) ≤ 0 := by
  rw [pair_cvec_indR]
  by_cases h0 : (0 : Fin 24) ∈ c
  · have hne : c ≠ ∅ := by
      intro hcon; rw [hcon] at h0; simp at h0
    have h8 : (8 : ℕ) ≤ c.card := golay_min_weight hc hne
    have h8' : (8 : ℝ) ≤ (c.card : ℝ) := by exact_mod_cast h8
    rw [if_pos h0]
    linarith
  · rw [if_neg h0]
    have : (0 : ℝ) ≤ (c.card : ℝ) := Nat.cast_nonneg _
    linarith

/-- And therefore on every scaled codeword. -/
theorem pair_cvec_nonpos_scaled {x : Fin 24 → ℝ} (hx : x ∈ scaledGolayVecs) :
    pair cvec x ≤ 0 := by
  obtain ⟨l, c, hl, hc, rfl⟩ := hx
  have hlin : pair cvec (l • indR c) = l * pair cvec (indR c) := by
    unfold pair
    rw [Finset.mul_sum]
    exact Finset.sum_congr rfl fun i _ => by simp [Pi.smul_apply]; ring
  rw [hlin]
  exact mul_nonpos_of_nonneg_of_nonpos hl (pair_cvec_nonpos_codeword hc)

theorem pair_cvec_concTarget : pair cvec concTarget = 7 / 2 := by
  unfold pair cvec concTarget
  rw [Finset.sum_congr rfl (fun i _ => by
      by_cases hi : i = 0
      · simp [hi]; norm_num
      · simp [hi] : ∀ i ∈ (univ : Finset (Fin 24)),
        (8 * (if i = 0 then (1 : ℝ) else 0) - 1) * (if i = 0 then 1 / 2 else 0)
          = if i = 0 then (7 : ℝ) / 2 else 0)]
  simp

/-- **Scaling does not broaden the hull enough.**  The target `½·e₀` is outside
the convex hull of all scaled codewords. -/
theorem concTarget_not_mem_hull_scaled :
    concTarget ∉ convexHull ℝ scaledGolayVecs := by
  intro hmem
  have hconv : Convex ℝ {x : Fin 24 → ℝ | pair cvec x ≤ 0} := by
    intro x hx y hy a b ha hb hab
    have hx' : pair cvec x ≤ 0 := hx
    have hy' : pair cvec y ≤ 0 := hy
    have hlin : pair cvec (a • x + b • y) = a * pair cvec x + b * pair cvec y := by
      unfold pair
      rw [Finset.mul_sum, Finset.mul_sum, ← Finset.sum_add_distrib]
      exact Finset.sum_congr rfl fun i _ => by simp [Pi.add_apply, Pi.smul_apply]; ring
    show pair cvec (a • x + b • y) ≤ 0
    rw [hlin]
    have h1 : a * pair cvec x ≤ 0 := mul_nonpos_of_nonneg_of_nonpos ha hx'
    have h2 : b * pair cvec y ≤ 0 := mul_nonpos_of_nonneg_of_nonpos hb hy'
    linarith
  have hsub : convexHull ℝ scaledGolayVecs ⊆ {x : Fin 24 → ℝ | pair cvec x ≤ 0} :=
    convexHull_min (fun x hx => pair_cvec_nonpos_scaled hx) hconv
  have := hsub hmem
  rw [Set.mem_setOf_eq, pair_cvec_concTarget] at this
  linarith

/-- **No quantiser rule reaches it either.**  Whatever feedback law drives the
carrier, if every emitted state is a scaled codeword then its reading never
converges to `½·e₀`. -/
theorem concTarget_unreachable_scaled (x : ℕ → (Fin 24 → ℝ))
    (hx : ∀ k, x k ∈ scaledGolayVecs) :
    ¬ Tendsto (fun N => avgVec x N) atTop (𝓝 concTarget) := by
  refine not_tendsto_avg_of_separating (c := cvec) (b := 0) (fun w hw => pair_cvec_nonpos_scaled hw)
    ?_ x hx
  rw [pair_cvec_concTarget]
  norm_num

/-! ## A cycle is read back exactly -/

/-- **Every finite cycle is read back as its mean.**  If the carrier repeats a
cycle of `N` emitted states, then at every completed cycle its reading is
exactly the mean of the cycle — not merely close to it.  With
`avgVec_mem_hull` and `not_tendsto_avg_of_separating` this pins the reachable
set of an alphabet as precisely the convex hull of that alphabet. -/
theorem cycle_avgVec_eq {N : ℕ} (hN : 0 < N) (y : Fin N → (Fin 24 → ℝ)) {k : ℕ} (hk : 0 < k) :
    avgVec (fun m => y ⟨m % N, Nat.mod_lt _ hN⟩) (N * k)
      = fun i => (∑ j, y j i) / N := by
  have hper : ∀ i, (fun m => y ⟨m % N, Nat.mod_lt _ hN⟩) (i + N)
      = (fun m => y ⟨m % N, Nat.mod_lt _ hN⟩) i := by
    intro i
    simp [Nat.add_mod_right]
  rw [avgVec_periodic hN hper hk]
  funext i
  unfold avgVec
  congr 1
  rw [← Fin.sum_univ_eq_sum_range (fun m => y ⟨m % N, Nat.mod_lt _ hN⟩ i) N]
  refine Finset.sum_congr rfl fun j _ => ?_
  congr 1
  exact Fin.ext (by simp [Nat.mod_eq_of_lt j.isLt])

/-! ## Leech points of shape `(±4², 0²²)` break the wall -/

/-- `4·e₀ + 4·e₁`: a minimal Leech vector in the `×√8` integer model the
substrate uses, of shape `(±4², 0²²)` and support `2`. -/
def leechPairPlus : Fin 24 → ℝ := fun i => if i = 0 then 4 else if i = 1 then 4 else 0

/-- `4·e₀ − 4·e₁`, the sign-flipped partner. -/
def leechPairMinus : Fin 24 → ℝ := fun i => if i = 0 then 4 else if i = 1 then -4 else 0

/-- The expanded alphabet: the origin together with the two Leech points. -/
def leechAlphabet : Set (Fin 24 → ℝ) := {0, leechPairPlus, leechPairMinus}

/-- The 16-tick emission cycle: one tick on each Leech point, then fourteen
ticks at the origin. -/
def leechCycle : Fin 16 → (Fin 24 → ℝ) :=
  fun j => if j = 0 then leechPairPlus else if j = 1 then leechPairMinus else 0

/-- The schedule the cycle defines. -/
def leechSchedule : ℕ → (Fin 24 → ℝ) := fun m => leechCycle ⟨m % 16, Nat.mod_lt _ (by norm_num)⟩

theorem leechSchedule_mem (m : ℕ) : leechSchedule m ∈ leechAlphabet := by
  unfold leechSchedule leechCycle leechAlphabet
  by_cases h0 : (⟨m % 16, Nat.mod_lt _ (by norm_num)⟩ : Fin 16) = 0
  · simp [h0]
  · by_cases h1 : (⟨m % 16, Nat.mod_lt _ (by norm_num)⟩ : Fin 16) = 1 <;> simp [h0, h1]

theorem leechCycle_sum (i : Fin 24) :
    (∑ j, leechCycle j i) = 8 * (if i = 0 then 1 else 0) := by
  unfold leechCycle leechPairPlus leechPairMinus
  by_cases hi : i = 0
  · simp [hi, Fin.sum_univ_succ]; norm_num
  · by_cases hi1 : i = 1 <;> simp [hi, hi1, Fin.sum_univ_succ]

/-- **The expanded alphabet reaches the target exactly.**  With the two Leech
points admitted, the carrier's reading at every completed 16-tick cycle is
exactly `½·e₀`, the target no scaled-codeword alphabet can approach. -/
theorem concTarget_reached_by_leech {k : ℕ} (hk : 0 < k) :
    (∀ m, leechSchedule m ∈ leechAlphabet) ∧
      avgVec leechSchedule (16 * k) = concTarget := by
  refine ⟨leechSchedule_mem, ?_⟩
  rw [show leechSchedule = fun m => leechCycle ⟨m % 16, Nat.mod_lt _ (by norm_num)⟩ from rfl,
    cycle_avgVec_eq (by norm_num) leechCycle hk]
  funext i
  rw [leechCycle_sum]
  unfold concTarget
  by_cases hi : i = 0
  · simp [hi]; norm_num
  · simp [hi]

/-- The reading converges to the target along the cycles, as well as hitting it
exactly at every one of them. -/
theorem concTarget_tendsto_leech :
    Tendsto (fun k => avgVec leechSchedule (16 * k)) atTop (𝓝 concTarget) := by
  rw [tendsto_congr' ?_]
  · exact tendsto_const_nhds
  · filter_upwards [eventually_gt_atTop 0] with k hk
    exact (concTarget_reached_by_leech hk).2

/-- **The comparison, in one statement.**  The same target is unreachable by
every carrier restricted to scaled codewords, and reached exactly — at every
completed cycle — by a carrier allowed two Leech points of support `2`.  What
broadened the hull was the new support, not the new scale. -/
theorem alphabet_expansion_strictly_helps :
    (∀ x : ℕ → (Fin 24 → ℝ), (∀ k, x k ∈ scaledGolayVecs) →
        ¬ Tendsto (fun N => avgVec x N) atTop (𝓝 concTarget)) ∧
      (∀ m, leechSchedule m ∈ leechAlphabet) ∧
      (∀ k : ℕ, 0 < k → avgVec leechSchedule (16 * k) = concTarget) :=
  ⟨concTarget_unreachable_scaled, leechSchedule_mem,
    fun _ hk => (concTarget_reached_by_leech hk).2⟩

end GLM.Hull
