import Mathlib
import RequestProject.GLM.LorentzianLift

/-!
# The Lorentzian evidence space (Phase 183)

*Created 23 October 2026.*

The formal half of `studies/LORENTZIAN_EVIDENCE_STUDY.md`, the next layer of
`studies/LORENTZIAN_LIFT_STUDY.md`. Phase 182 proved that the lift
`L(x) = (x, (1 − |x|²)/2, (1 + |x|²)/2)` turns nearest-point decoding into a
linear maximisation (`inner_lift_root`), that a tie is a mirror, and that no
reflection-invariant rule breaks a tie. This file asks what the *linear space*
upstairs gives reasoning in general — for any finite set of cues, in any
dimension, with any weights, over any candidate points.

* `inner_evid`, `evid_score` — the evidence vector `V = Σ wᵢ L(xᵢ)` scores a
  candidate `λ` by `W − ½ Σ wᵢ |xᵢ − λ|²`: scores of cues **add**;
* `steiner` — `Σ wᵢ |xᵢ − λ|² = D + W |x̄ − λ|²` (the parallel-axis theorem),
  with `x̄` the weighted centroid and `D` the dispersion;
* `evidence_decomp` — **the decomposition** `V = W · L(x̄) + (D/2) · w`: the
  evidence is one lifted point, the consensus, plus the Weyl vector times the
  disagreement;
* `evid_rank`, `evid_tie` — for `W > 0` the evidence prefers the candidate
  nearer the consensus, and ties exactly on the consensus's mirrors;
* `evid_norm` — **`⟨V, V⟩ = −W · D`**: the Lorentzian norm of the evidence is
  minus its disagreement;
* `disp_nonneg`, `disp_le`, `dispersion_guard_sound` — the dispersion of
  readings that all lie within `ρᵢ` of one common point is at most `Σ wᵢ ρᵢ`:
  a guard that refuses above that budget never refuses an honest set;
* `disp_eq_zero_iff`, `evid_null_iff` — with positive weights the evidence is
  null exactly when every cue agrees;
* `analogy_evidence`, `analogy_score` — `A : B :: C : ?` is the evidence
  `L B − L A + L C` (weights `1, −1, 1`): its consensus is `C + B − A`, the
  displacement solver's target, and its Weyl part is `−(A − B)·(A − C)`;
* `agree_on_iff`, `separates_iff`, `card_ge_of_separates` — the question a
  tie asks: when the tied candidates are a word flipped on pairwise disjoint
  blocks (a Golay sextet: six disjoint tetrads), revealing the positions `Q`
  tells two candidates apart exactly when `Q` meets one of their blocks, so a
  question settling all `m` candidates must meet `m − 1` blocks and has at
  least `m − 1` positions (five for a sextet).
-/

namespace GLM.LorentzianEvidence

open Finset GLM.LorentzianLift

variable {n : ℕ} {ι : Type*}

/-! ## 0. Small facts about the dot product -/

lemma nsq_nonneg (x : Fin n → ℚ) : 0 ≤ nsq x := by
  unfold nsq dot; exact sum_nonneg fun i _ => mul_self_nonneg _

lemma nsq_eq_zero_iff (x : Fin n → ℚ) : nsq x = 0 ↔ x = 0 := by
  constructor
  · intro h
    have hz : ∀ i ∈ (univ : Finset (Fin n)), x i * x i = 0 :=
      (sum_eq_zero_iff_of_nonneg fun i _ => mul_self_nonneg (x i)).mp h
    funext i; exact mul_self_eq_zero.mp (hz i (mem_univ i))
  · rintro rfl; simp [nsq, dot]

lemma dot_sum_left (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) (y : Fin n → ℚ) :
    dot (∑ i ∈ s, w i • x i) y = ∑ i ∈ s, w i * dot (x i) y := by
  unfold dot
  simp only [Finset.sum_apply, Pi.smul_apply, smul_eq_mul, Finset.sum_mul, Finset.mul_sum]
  rw [Finset.sum_comm]
  exact sum_congr rfl fun i _ => sum_congr rfl fun j _ => by ring

lemma dot_add_left (x y z : Fin n → ℚ) : dot (x + y) z = dot x z + dot y z := by
  unfold dot; rw [← sum_add_distrib]; exact sum_congr rfl fun i _ => by simp [add_mul]

/-! ## 1. The evidence vector -/

/-- The total weight `W = Σ wᵢ`. -/
def wsum (s : Finset ι) (w : ι → ℚ) : ℚ := ∑ i ∈ s, w i

/-- The weighted centroid `x̄ = W⁻¹ Σ wᵢ xᵢ` — the consensus of the cues. -/
def cent (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) : Fin n → ℚ :=
  (wsum s w)⁻¹ • ∑ i ∈ s, w i • x i

/-- The dispersion `D = Σ wᵢ |xᵢ − x̄|²` — the disagreement of the cues. -/
def disp (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) : ℚ :=
  ∑ i ∈ s, w i * nsq (x i - cent s w x)

/-- The evidence vector `V = Σ wᵢ L(xᵢ)`, written out by components. -/
def evid (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) : LVec n :=
  ⟨∑ i ∈ s, w i • x i, ∑ i ∈ s, w i * ((1 - nsq (x i)) / 2),
    ∑ i ∈ s, w i * ((1 + nsq (x i)) / 2)⟩

/-- **Scores add**: the evidence vector's inner product with anything is the
weighted sum of the cues' inner products. -/
theorem inner_evid (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) (b : LVec n) :
    inner (evid s w x) b = ∑ i ∈ s, w i * inner (lift (x i)) b := by
  unfold LorentzianLift.inner evid lift
  simp only
  rw [dot_sum_left, Finset.sum_mul, Finset.sum_mul, ← sum_add_distrib, ← sum_sub_distrib]
  exact sum_congr rfl fun i _ => by ring

/-- The evidence score of a candidate: `⟨V, r_λ⟩ = W − ½ Σ wᵢ |xᵢ − λ|²`. -/
theorem evid_score (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) (l : Fin n → ℚ) :
    inner (evid s w x) (root l) = wsum s w - (∑ i ∈ s, w i * nsq (x i - l)) / 2 := by
  rw [inner_evid, wsum, Finset.sum_div, ← sum_sub_distrib]
  exact sum_congr rfl fun i _ => by rw [inner_lift_root]; ring

/-- `W · x̄ = Σ wᵢ xᵢ` when `W ≠ 0`. -/
lemma wsum_smul_cent (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) (hW : wsum s w ≠ 0) :
    wsum s w • cent s w x = ∑ i ∈ s, w i • x i := by
  unfold cent; rw [smul_smul, mul_inv_cancel₀ hW, one_smul]

/-- `Σ wᵢ |xᵢ − λ|² = Σ wᵢ|xᵢ|² − 2 (Σ wᵢ xᵢ)·λ + W |λ|²`. -/
lemma wsum_nsq_sub (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) (l : Fin n → ℚ) :
    ∑ i ∈ s, w i * nsq (x i - l) =
      ∑ i ∈ s, w i * nsq (x i) - 2 * dot (∑ i ∈ s, w i • x i) l + wsum s w * nsq l := by
  rw [dot_sum_left, wsum, Finset.mul_sum, Finset.sum_mul, ← sum_sub_distrib,
    ← sum_add_distrib]
  exact sum_congr rfl fun i _ => by rw [nsq_sub]; ring

/-- `D = Σ wᵢ|xᵢ|² − W |x̄|²`. -/
lemma disp_eq (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) (hW : wsum s w ≠ 0) :
    disp s w x = ∑ i ∈ s, w i * nsq (x i) - wsum s w * nsq (cent s w x) := by
  unfold disp
  rw [wsum_nsq_sub, ← wsum_smul_cent s w x hW, dot_smul_left]
  unfold nsq; ring

/-- **The parallel-axis theorem**: `Σ wᵢ |xᵢ − λ|² = D + W |x̄ − λ|²`. -/
theorem steiner (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) (hW : wsum s w ≠ 0)
    (l : Fin n → ℚ) :
    ∑ i ∈ s, w i * nsq (x i - l) = disp s w x + wsum s w * nsq (cent s w x - l) := by
  rw [wsum_nsq_sub, disp_eq s w x hW, nsq_sub, ← wsum_smul_cent s w x hW, dot_smul_left]
  ring

/-- **The decomposition of the evidence**: `V = W · L(x̄) + (D/2) · w`. The
evidence of any finite set of weighted cues is one lifted point — the
consensus — plus the Weyl vector times half the disagreement. -/
theorem evidence_decomp (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ)
    (hW : wsum s w ≠ 0) :
    evid s w x = wsum s w • lift (cent s w x) + (disp s w x / 2) • (weyl : LVec n) := by
  have hd := disp_eq s w x hW
  ext j
  · simp only [evid, add_x, smul_x, lift, weyl, smul_zero, add_zero]
    rw [wsum_smul_cent s w x hW]
  · simp only [evid, add_t, smul_t, lift, weyl]
    rw [hd]
    have : ∑ i ∈ s, w i * ((1 - nsq (x i)) / 2) =
        (wsum s w - ∑ i ∈ s, w i * nsq (x i)) / 2 := by
      rw [wsum, ← sum_sub_distrib, Finset.sum_div]
      exact sum_congr rfl fun i _ => by ring
    rw [this]; ring
  · simp only [evid, add_τ, smul_τ, lift, weyl]
    rw [hd]
    have : ∑ i ∈ s, w i * ((1 + nsq (x i)) / 2) =
        (wsum s w + ∑ i ∈ s, w i * nsq (x i)) / 2 := by
      rw [wsum, ← sum_add_distrib, Finset.sum_div]
      exact sum_congr rfl fun i _ => by ring
    rw [this]; ring

/-- The evidence score in consensus form: `⟨V, r_λ⟩ = W − D/2 − W |x̄ − λ|²/2`. -/
theorem evid_score_cent (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ)
    (hW : wsum s w ≠ 0) (l : Fin n → ℚ) :
    inner (evid s w x) (root l) =
      wsum s w - disp s w x / 2 - wsum s w * nsq (cent s w x - l) / 2 := by
  rw [evid_score, steiner s w x hW]; ring

/-- **The evidence prefers the candidate nearer the consensus** (`W > 0`). -/
theorem evid_rank (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) (hW : 0 < wsum s w)
    (l m : Fin n → ℚ) :
    inner (evid s w x) (root m) < inner (evid s w x) (root l) ↔
      nsq (cent s w x - l) < nsq (cent s w x - m) := by
  rw [evid_score_cent s w x hW.ne', evid_score_cent s w x hW.ne']
  constructor
  · intro h; by_contra h'; push_neg at h'; nlinarith
  · intro h; nlinarith

/-- **The evidence ties exactly on the consensus's mirrors** (`W ≠ 0`). -/
theorem evid_tie (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) (hW : wsum s w ≠ 0)
    (l m : Fin n → ℚ) :
    inner (evid s w x) (root l) = inner (evid s w x) (root m) ↔
      nsq (cent s w x - l) = nsq (cent s w x - m) := by
  rw [evid_score_cent s w x hW, evid_score_cent s w x hW]
  constructor
  · intro h
    have : wsum s w * (nsq (cent s w x - l) - nsq (cent s w x - m)) = 0 := by linarith
    rcases mul_eq_zero.mp this with h0 | h0
    · exact absurd h0 hW
    · linarith
  · intro h; rw [h]

/-- **The norm of the evidence is minus its disagreement**: `⟨V, V⟩ = −W · D`. -/
theorem evid_norm (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ) (hW : wsum s w ≠ 0) :
    inner (evid s w x) (evid s w x) = -(wsum s w * disp s w x) := by
  rw [disp_eq s w x hW]
  have hx : (evid s w x).x = wsum s w • cent s w x := (wsum_smul_cent s w x hW).symm
  have ht : (evid s w x).t = (wsum s w - ∑ i ∈ s, w i * nsq (x i)) / 2 := by
    simp only [evid]; rw [wsum, ← sum_sub_distrib, Finset.sum_div]
    exact sum_congr rfl fun i _ => by ring
  have hτ : (evid s w x).τ = (wsum s w + ∑ i ∈ s, w i * nsq (x i)) / 2 := by
    simp only [evid]; rw [wsum, ← sum_add_distrib, Finset.sum_div]
    exact sum_congr rfl fun i _ => by ring
  unfold LorentzianLift.inner
  rw [hx, ht, hτ, dot_smul_left, dot_smul_right]
  unfold nsq; ring

/-! ## 2. The dispersion as a guard -/

theorem disp_nonneg (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ)
    (hw : ∀ i ∈ s, 0 ≤ w i) : 0 ≤ disp s w x :=
  sum_nonneg fun i hi => mul_nonneg (hw i hi) (nsq_nonneg _)

/-- **The consensus minimises the weighted spread**: for non-negative weights
the dispersion is at most `Σ wᵢ |xᵢ − c|²` for every point `c`. -/
theorem disp_le (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ)
    (hw : ∀ i ∈ s, 0 ≤ w i) (hW : wsum s w ≠ 0) (c : Fin n → ℚ) :
    disp s w x ≤ ∑ i ∈ s, w i * nsq (x i - c) := by
  rw [steiner s w x hW c]
  have : 0 ≤ wsum s w := sum_nonneg hw
  have := nsq_nonneg (cent s w x - c)
  nlinarith

/-- **The dispersion guard is sound**: if every cue lies within its budget
`ρᵢ` (squared distance) of one common point `c` — the readings are honest
readings of `c` — their dispersion is at most `Σ wᵢ ρᵢ`. A guard that refuses
only above that budget never refuses an honest set. -/
theorem dispersion_guard_sound (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ)
    (hw : ∀ i ∈ s, 0 ≤ w i) (hW : wsum s w ≠ 0) (c : Fin n → ℚ) (ρ : ι → ℚ)
    (hρ : ∀ i ∈ s, nsq (x i - c) ≤ ρ i) :
    disp s w x ≤ ∑ i ∈ s, w i * ρ i :=
  (disp_le s w x hw hW c).trans
    (sum_le_sum fun i hi => mul_le_mul_of_nonneg_left (hρ i hi) (hw i hi))

/-- **No disagreement, exactly when every cue agrees** (positive weights). -/
theorem disp_eq_zero_iff (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ)
    (hw : ∀ i ∈ s, 0 < w i) (hs : s.Nonempty) :
    disp s w x = 0 ↔ ∀ i ∈ s, ∀ j ∈ s, x i = x j := by
  have hW : wsum s w ≠ 0 := (sum_pos hw hs).ne'
  constructor
  · intro h
    have hz := (sum_eq_zero_iff_of_nonneg fun i hi =>
      mul_nonneg (hw i hi).le (nsq_nonneg (x i - cent s w x))).mp h
    have he : ∀ i ∈ s, x i = cent s w x := by
      intro i hi
      rcases mul_eq_zero.mp (hz i hi) with h0 | h0
      · exact absurd h0 (hw i hi).ne'
      · exact sub_eq_zero.mp ((nsq_eq_zero_iff _).mp h0)
    intro i hi j hj; rw [he i hi, he j hj]
  · intro h
    obtain ⟨k, hk⟩ := hs
    have hc : cent s w x = x k := by
      have : ∑ i ∈ s, w i • x i = wsum s w • x k := by
        rw [wsum, Finset.sum_smul]; exact sum_congr rfl fun i hi => by rw [h i hi k hk]
      unfold cent; rw [this, smul_smul, inv_mul_cancel₀ hW, one_smul]
    unfold disp
    exact sum_eq_zero fun i hi => by rw [hc, h i hi k hk, sub_self]; simp [nsq, dot]

/-- **The evidence is null exactly when every cue agrees** (positive weights):
agreement is light-like, any disagreement makes the evidence time-like. -/
theorem evid_null_iff (s : Finset ι) (w : ι → ℚ) (x : ι → Fin n → ℚ)
    (hw : ∀ i ∈ s, 0 < w i) (hs : s.Nonempty) :
    inner (evid s w x) (evid s w x) = 0 ↔ ∀ i ∈ s, ∀ j ∈ s, x i = x j := by
  have hWp : 0 < wsum s w := sum_pos hw hs
  rw [evid_norm s w x hWp.ne', ← disp_eq_zero_iff s w x hw hs, neg_eq_zero,
    mul_eq_zero]
  exact ⟨fun h => h.resolve_left hWp.ne', Or.inr⟩

/-! ## 3. Analogy is evidence with weights `1, −1, 1` -/

/-- **`A : B :: C : ?` is an evidence vector.** `L B − L A + L C` is the lift
of the displacement solver's target `C + B − A` plus the Weyl vector times
`−(A − B)·(A − C)`. -/
theorem analogy_evidence (a b c : Fin n → ℚ) :
    lift b - lift a + lift c = lift (c + b - a) + (-dot (a - b) (a - c)) • (weyl : LVec n) := by
  have key : nsq (c + b - a) =
      nsq b - nsq a + nsq c + 2 * dot (a - b) (a - c) := by
    unfold nsq dot
    simp only [Pi.add_apply, Pi.sub_apply]
    rw [← sum_sub_distrib, ← sum_add_distrib, Finset.mul_sum, ← sum_add_distrib]
    exact sum_congr rfl fun i _ => by ring
  ext j
  · simp only [add_x, sub_x, lift, smul_x, weyl, smul_zero, Pi.add_apply,
      Pi.sub_apply, Pi.zero_apply]; ring
  · simp only [add_t, sub_t, lift, smul_t, weyl]; rw [key]; ring
  · simp only [add_τ, sub_τ, lift, smul_τ, weyl]; rw [key]; ring

/-- The analogy's score of a candidate: `1 + (A − B)·(A − C) − |C + B − A − λ|²/2`
— the same shift for every candidate, so the ranking is by distance to the
target. -/
theorem analogy_score (a b c l : Fin n → ℚ) :
    inner (lift b - lift a + lift c) (root l) =
      1 + dot (a - b) (a - c) - nsq (c + b - a - l) / 2 := by
  rw [analogy_evidence]
  have h1 : inner (lift (c + b - a) + (-dot (a - b) (a - c)) • (weyl : LVec n)) (root l) =
      inner (lift (c + b - a)) (root l) + (-dot (a - b) (a - c)) * inner weyl (root l) := by
    unfold LorentzianLift.inner; simp only [add_x, add_t, add_τ, smul_x, smul_t, smul_τ]
    rw [dot_add_left, dot_smul_left]; ring
  rw [h1, inner_lift_root, inner_weyl_root]; ring

/-! ## 4. The question a tie asks -/

section Question

variable {α : Type*} [DecidableEq α] {κ : Type*}

/-- Two flips of the same word agree on the revealed positions `Q` exactly
when the two flipped blocks differ nowhere on `Q`. -/
lemma agree_on_iff_symmDiff (b t u Q : Finset α) :
    symmDiff b t ∩ Q = symmDiff b u ∩ Q ↔ symmDiff t u ∩ Q = ∅ := by
  simp only [Finset.ext_iff, Finset.mem_inter, Finset.mem_symmDiff,
    Finset.notMem_empty, iff_false]
  constructor
  · intro h a ⟨hx, hq⟩
    have := h a; tauto
  · intro h a
    have := h a; tauto

/-- **Two tied candidates are told apart by `Q` exactly when `Q` meets one of
their blocks** (the blocks disjoint, as the tetrads of a sextet are). -/
theorem agree_on_iff (b t u Q : Finset α) (hd : Disjoint t u) :
    symmDiff b t ∩ Q = symmDiff b u ∩ Q ↔ t ∩ Q = ∅ ∧ u ∩ Q = ∅ := by
  rw [agree_on_iff_symmDiff, hd.symmDiff_eq_sup]
  simp only [Finset.sup_eq_union, Finset.union_inter_distrib_right, Finset.union_eq_empty]

/-- **The question that settles a tie**: revealing `Q` tells every pair of the
candidates `b ∆ tⱼ` apart exactly when at most one block misses `Q`. -/
theorem separates_iff (b Q : Finset α) (t : κ → Finset α)
    (hd : Pairwise fun j k => Disjoint (t j) (t k)) :
    (∀ j k, j ≠ k → symmDiff b (t j) ∩ Q ≠ symmDiff b (t k) ∩ Q) ↔
      ∀ j k, j ≠ k → t j ∩ Q = ∅ → t k ∩ Q ≠ ∅ := by
  constructor
  · intro h j k hjk hj hk
    exact h j k hjk ((agree_on_iff b (t j) (t k) Q (hd hjk)).mpr ⟨hj, hk⟩)
  · intro h j k hjk heq
    obtain ⟨hj, hk⟩ := (agree_on_iff b (t j) (t k) Q (hd hjk)).mp heq
    exact h j k hjk hj hk

/-- **A settling question is at least `m − 1` positions long**: with `m`
candidates on pairwise disjoint blocks, a `Q` that tells every pair apart has
at least `m − 1` elements — five for the six tetrads of a Golay sextet. -/
theorem card_ge_of_separates [Fintype κ] (b Q : Finset α) (t : κ → Finset α)
    (hd : Pairwise fun j k => Disjoint (t j) (t k))
    (hsep : ∀ j k, j ≠ k → symmDiff b (t j) ∩ Q ≠ symmDiff b (t k) ∩ Q) :
    Fintype.card κ - 1 ≤ Q.card := by
  classical
  have h := (separates_iff b Q t hd).mp hsep
  set M := (univ : Finset κ).filter fun j => (t j ∩ Q).Nonempty with hM
  have hmiss : ((univ : Finset κ).filter fun j => ¬ (t j ∩ Q).Nonempty).card ≤ 1 := by
    rw [Finset.card_le_one]
    intro j hj k hk
    by_contra hjk
    simp only [Finset.mem_filter, mem_univ, true_and, Finset.not_nonempty_iff_eq_empty] at hj hk
    exact h j k hjk hj hk
  have hsplit : M.card + ((univ : Finset κ).filter fun j => ¬ (t j ∩ Q).Nonempty).card =
      Fintype.card κ := by
    rw [hM, Finset.card_filter_add_card_filter_not, Finset.card_univ]
  have hinj : M.card ≤ Q.card := by
    rcases isEmpty_or_nonempty α with hα | hα
    · have : M = ∅ := by
        rw [hM, Finset.filter_eq_empty_iff]
        intro j _ hne
        obtain ⟨a, _⟩ := hne
        exact hα.false a
      rw [this]; simp
    refine Finset.card_le_card_of_injOn (fun j => if hj : (t j ∩ Q).Nonempty then hj.choose
      else Classical.arbitrary α) ?_ ?_
    · intro j hj
      have hj' : (t j ∩ Q).Nonempty := by
        simpa [hM] using hj
      simp only [hj', dite_true]
      exact (Finset.mem_inter.mp hj'.choose_spec).2
    · intro j hj k hk hjk
      have hj' : (t j ∩ Q).Nonempty := by simpa [hM] using hj
      have hk' : (t k ∩ Q).Nonempty := by simpa [hM] using hk
      simp only [hj', hk', dite_true] at hjk
      by_contra hne
      have h1 := (Finset.mem_inter.mp hj'.choose_spec).1
      have h2 := (Finset.mem_inter.mp hk'.choose_spec).1
      rw [hjk] at h1
      exact Finset.disjoint_left.mp (hd hne) h1 h2
  omega

end Question

end GLM.LorentzianEvidence
