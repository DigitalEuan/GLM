module

public import Mathlib
public import RequestProject.GLM.DecoderConfidence

/-!
# The confidence floor: what a floor promises, and why overstating the rate is safe

The formal half of `studies/CONFIDENCE_FLOOR_STUDY.md` (Phase 80,
`glm_universal.reasoning.confidence_floor`). A reading answers a read `r` with
confidence `post r` (its posterior, `GLM.DecoderConfidence.posterior`); a
floor `t` answers only the reads with `t ≤ post r`. Each read carries a
probability mass `m r` on the channel, and the probability that an answered
read is wrong is `Σ m r (1 - post r)` over the answered reads.

* `floor_error_le` — every answered read at least `t` sure means the answered
  reads are wrong with total mass at most `(1 - t)` times their own mass:
  the promise of the floor, `P(wrong | answered) ≤ 1 - t`.
* `floor_retention_antitone` — raising the floor never raises the right
  answers it keeps.
* `posterior_eq_ratio` — on the binary symmetric channel, a survivor no
  further from the read than any rival has posterior
  `1 / Σ_s (p / (1 - p))^(d s - d c)`.
* `posterior_antitone_rate` — hence its posterior falls as the rate rises.
* `floor_pass_lower_rate` — a floor passed at a declared rate is passed at
  every lower true rate.
* `floor_safe_overdeclared` — and, over a whole channel, a floor chosen with
  confidences no higher than the true ones still keeps its promise.
-/

@[expose] public section

namespace GLM.ConfidenceFloor

open Finset GLM.DecoderConfidence

variable {ι K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

/-- **The promise of a floor.** Over the reads a floor `t` answers, the mass
of wrong answers is at most `1 - t` times the mass answered. -/
theorem floor_error_le (R : Finset ι) (m post : ι → K) (t : K)
    (hm : ∀ r ∈ R, 0 ≤ m r) :
    ∑ r ∈ R.filter (fun r => t ≤ post r), m r * (1 - post r)
      ≤ (1 - t) * ∑ r ∈ R.filter (fun r => t ≤ post r), m r := by
  rw [Finset.mul_sum]
  refine Finset.sum_le_sum fun r hr => ?_
  rw [Finset.mem_filter] at hr
  have h0 := hm r hr.1
  nlinarith [hr.2]

/-- **Raising the floor never raises what it keeps.** -/
theorem floor_retention_antitone (R : Finset ι) (m post : ι → K) {t t' : K}
    (htt : t ≤ t') (hm : ∀ r ∈ R, 0 ≤ m r * post r) :
    ∑ r ∈ R.filter (fun r => t' ≤ post r), m r * post r
      ≤ ∑ r ∈ R.filter (fun r => t ≤ post r), m r * post r := by
  refine Finset.sum_le_sum_of_subset_of_nonneg ?_ fun r hr _ =>
    hm r (Finset.mem_filter.mp hr).1
  intro r hr
  rw [Finset.mem_filter] at hr ⊢
  exact ⟨hr.1, le_trans htt hr.2⟩

/-- On the binary symmetric channel, a survivor `c` no further from the read
than any candidate has posterior `1 / Σ_s (p / (1 - p))^(d s - d c)`. -/
theorem posterior_eq_ratio (p : K) (hp : 0 < p) (hp1 : p < 1) (dist : ι → ℕ)
    (n : ℕ) (S : Finset ι) {c : ι}
    (hnear : ∀ s ∈ S, dist c ≤ dist s) (hn : ∀ s ∈ S, dist s ≤ n) :
    posterior (fun s => bsc p n (dist s)) S c
      = 1 / ∑ s ∈ S, (p / (1 - p)) ^ (dist s - dist c) := by
  unfold posterior
  have hw : ∀ s ∈ S, bsc p n (dist s)
      = (p / (1 - p)) ^ (dist s - dist c) * bsc p n (dist c) := by
    intro s hs
    have h1 : dist c + (dist s - dist c) = dist s := by
      have := hnear s hs; omega
    have h2 := bsc_ratio p hp1 (d := dist c) (e := dist s - dist c)
      (n := n) (by rw [h1]; exact hn s hs)
    rw [h1] at h2
    exact h2
  rw [Finset.sum_congr rfl hw, ← Finset.sum_mul]
  have hpos : 0 < bsc p n (dist c) := bsc_pos p hp hp1 n _
  field_simp

/-- The sum `Σ_s ρ^(d s - d c)` over the candidates is at least one: the
survivor contributes `ρ^0 = 1` and no term is negative. -/
theorem ratio_sum_ge_one (ρ : K) (hρ : 0 ≤ ρ) (dist : ι → ℕ) (S : Finset ι)
    {c : ι} (hc : c ∈ S) :
    1 ≤ ∑ s ∈ S, ρ ^ (dist s - dist c) := by
  have := Finset.single_le_sum (f := fun s => ρ ^ (dist s - dist c))
    (fun s _ => pow_nonneg hρ _) hc
  simpa using this

/-- `p / (1 - p)` rises with `p` below one. -/
theorem odds_mono {p p' : K} (hpp : p ≤ p') (hp1 : p' < 1) :
    p / (1 - p) ≤ p' / (1 - p') := by
  have h1 : 0 < 1 - p := by linarith
  have h2 : 0 < 1 - p' := by linarith
  rw [div_le_div_iff₀ h1 h2]
  nlinarith

/-- **The posterior of a nearest survivor falls as the rate rises.** -/
theorem posterior_antitone_rate {p p' : K} (hp : 0 < p) (hpp : p ≤ p')
    (hp1 : p' < 1) (dist : ι → ℕ) (n : ℕ) (S : Finset ι) {c : ι}
    (hc : c ∈ S) (hnear : ∀ s ∈ S, dist c ≤ dist s)
    (hn : ∀ s ∈ S, dist s ≤ n) :
    posterior (fun s => bsc p' n (dist s)) S c
      ≤ posterior (fun s => bsc p n (dist s)) S c := by
  have hp1' : p < 1 := lt_of_le_of_lt hpp hp1
  have hp' : 0 < p' := lt_of_lt_of_le hp hpp
  rw [posterior_eq_ratio p hp hp1' dist n S hnear hn,
    posterior_eq_ratio p' hp' hp1 dist n S hnear hn]
  have hρ : 0 ≤ p / (1 - p) := div_nonneg hp.le (by linarith)
  have hle : ∑ s ∈ S, (p / (1 - p)) ^ (dist s - dist c)
      ≤ ∑ s ∈ S, (p' / (1 - p')) ^ (dist s - dist c) :=
    Finset.sum_le_sum fun s _ =>
      pow_le_pow_left₀ hρ (odds_mono hpp hp1) _
  have h1 := ratio_sum_ge_one _ hρ dist S hc
  exact one_div_le_one_div_of_le (by linarith) hle

/-- **A floor passed at a declared rate is passed at every lower true
rate.** -/
theorem floor_pass_lower_rate {p p' t : K} (hp : 0 < p) (hpp : p ≤ p')
    (hp1 : p' < 1) (dist : ι → ℕ) (n : ℕ) (S : Finset ι) {c : ι}
    (hc : c ∈ S) (hnear : ∀ s ∈ S, dist c ≤ dist s)
    (hn : ∀ s ∈ S, dist s ≤ n)
    (hpass : t ≤ posterior (fun s => bsc p' n (dist s)) S c) :
    t ≤ posterior (fun s => bsc p n (dist s)) S c :=
  le_trans hpass (posterior_antitone_rate hp hpp hp1 dist n S hc hnear hn)

/-- **Overstating the rate is safe.** If the floor is applied to declared
confidences `decl r` no higher than the true posteriors `post r` (as
`floor_pass_lower_rate` gives when the declared rate is the higher), the reads
it answers are wrong, at the true rate, with mass at most `1 - t` times the
mass answered. -/
theorem floor_safe_overdeclared (R : Finset ι) (m decl post : ι → K) (t : K)
    (hm : ∀ r ∈ R, 0 ≤ m r) (hdecl : ∀ r ∈ R, decl r ≤ post r) :
    ∑ r ∈ R.filter (fun r => t ≤ decl r), m r * (1 - post r)
      ≤ (1 - t) * ∑ r ∈ R.filter (fun r => t ≤ decl r), m r := by
  rw [Finset.mul_sum]
  refine Finset.sum_le_sum fun r hr => ?_
  rw [Finset.mem_filter] at hr
  have h0 := hm r hr.1
  have h1 := hdecl r hr.1
  nlinarith [hr.2]

end GLM.ConfidenceFloor
