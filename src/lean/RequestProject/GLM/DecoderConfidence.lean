module

public import Mathlib

/-!
# Decoder confidence: how likely a decoding is to be the codeword sent

The formal half of `studies/DECODER_CONFIDENCE_STUDY.md` (Phase 77,
`glm_universal.reasoning.decoder_confidence`). A reading allows a finite set
of candidate codewords — every codeword for the decoder and the second reading,
the declared cases for the carried fork's context stage — and weighs each by
the likelihood `w c` of the reads given that `c` was sent. The confidence of an
answer is its posterior `w c / Σ_{s ∈ S} w s` under a uniform prior.

* `posterior_sum_one` — the posteriors over the candidates sum to one.
* `posterior_restrict_le` — restricting the candidates (the closed world of
  the context stage) never lowers a survivor's posterior.
* `equal_weight_equal_posterior` — equal likelihoods give equal posteriors:
  the six candidates of a deep hole, or the two survivors of the second
  reading's witness, are a tie at every rate.
* `resolved_bound` — a survivor whose `k - 1` rivals each have at most `r`
  times its likelihood has posterior at least `1 / (1 + (k - 1) r)`.
* `bsc_ratio`, `bsc_anti` — on the binary symmetric channel with
  `0 < p ≤ 1/2`, a candidate `e` further from the read has `(p / (1 - p))^e`
  times the likelihood, so likelihood falls with distance.
* `fork_confidence_bound` — hence a survivor whose rivals all lie at least `g`
  further from the read has posterior at least
  `1 / (1 + (k - 1) (p / (1 - p))^g)`. For a resolved deep-hole fork every
  other declared case lies at least two further, which is the floor the study
  checks on every resolved read.
-/

@[expose] public section

namespace GLM.DecoderConfidence

open Finset

variable {ι K : Type*} [Field K]

/-- The posterior of candidate `c` among the allowed candidates `S`, each
weighted by the likelihood `w` of the reads given that it was sent. -/
def posterior (w : ι → K) (S : Finset ι) (c : ι) : K := w c / ∑ s ∈ S, w s

/-- The posteriors over the allowed candidates sum to one. -/
theorem posterior_sum_one (w : ι → K) (S : Finset ι) (hS : ∑ s ∈ S, w s ≠ 0) :
    ∑ c ∈ S, posterior w S c = 1 := by
  unfold posterior
  rw [← Finset.sum_div, div_self hS]

/-- Equal likelihoods give equal posteriors. -/
theorem equal_weight_equal_posterior (w : ι → K) (S : Finset ι) {a b : ι}
    (h : w a = w b) : posterior w S a = posterior w S b := by
  unfold posterior; rw [h]

/-- Two independent reads: the joint likelihood is the product. -/
theorem product_posterior (w₁ w₂ : ι → K) (S : Finset ι) (c : ι) :
    posterior (fun s => w₁ s * w₂ s) S c
      = w₁ c * w₂ c / ∑ s ∈ S, w₁ s * w₂ s := rfl

variable [LinearOrder K] [IsStrictOrderedRing K]

/-- Restricting the candidates never lowers a survivor's posterior. -/
theorem posterior_restrict_le (w : ι → K) {T U : Finset ι} (hTU : T ⊆ U)
    (hw : ∀ s, 0 ≤ w s) {c : ι} (hc : c ∈ T) (hpos : 0 < w c) :
    posterior w U c ≤ posterior w T c := by
  unfold posterior
  have hT : 0 < ∑ s ∈ T, w s :=
    lt_of_lt_of_le hpos (Finset.single_le_sum (fun s _ => hw s) hc)
  exact div_le_div_of_nonneg_left (hw c) hT
    (Finset.sum_le_sum_of_subset_of_nonneg hTU fun s _ _ => hw s)

/-- A survivor whose rivals each have at most `r` times its likelihood has
posterior at least `1 / (1 + (k - 1) r)`, where `k` counts the candidates. -/
theorem resolved_bound [DecidableEq ι] (w : ι → K) (S : Finset ι) {c : ι}
    (hc : c ∈ S) (ha : 0 < w c) {r : K} (hw : ∀ s, 0 ≤ w s)
    (hothers : ∀ s ∈ S, s ≠ c → w s ≤ r * w c) :
    1 / (1 + ((S.card : K) - 1) * r) ≤ posterior w S c := by
  unfold posterior
  have hsplit : ∑ s ∈ S, w s = w c + ∑ s ∈ S.erase c, w s :=
    (Finset.add_sum_erase S w hc).symm
  have hle : ∑ s ∈ S.erase c, w s ≤ ((S.card : K) - 1) * (r * w c) := by
    calc ∑ s ∈ S.erase c, w s ≤ ∑ s ∈ S.erase c, r * w c :=
          Finset.sum_le_sum fun s hs => hothers s (Finset.mem_of_mem_erase hs)
            (Finset.ne_of_mem_erase hs)
      _ = ((S.card : K) - 1) * (r * w c) := by
          rw [Finset.sum_const, Finset.card_erase_of_mem hc, nsmul_eq_mul]
          rw [Nat.cast_sub (Finset.card_pos.mpr ⟨c, hc⟩)]; simp
  have hrest : 0 ≤ ∑ s ∈ S.erase c, w s := Finset.sum_nonneg fun s _ => hw s
  have hpos : 0 < ∑ s ∈ S, w s := by
    rw [hsplit]; exact add_pos_of_pos_of_nonneg ha hrest
  have hden : 0 < 1 + ((S.card : K) - 1) * r := by
    by_contra h
    push_neg at h
    nlinarith
  rw [div_le_div_iff₀ hden hpos, hsplit]
  nlinarith

/-- The binary symmetric channel's likelihood of a read of length `n` at
distance `d` from the candidate, each bit flipping at rate `p`. -/
def bsc (p : K) (n d : ℕ) : K := p ^ d * (1 - p) ^ (n - d)

theorem bsc_nonneg (p : K) (hp : 0 ≤ p) (hp1 : p ≤ 1) (n d : ℕ) :
    0 ≤ bsc p n d :=
  mul_nonneg (pow_nonneg hp _) (pow_nonneg (by linarith) _)

theorem bsc_pos (p : K) (hp : 0 < p) (hp1 : p < 1) (n d : ℕ) : 0 < bsc p n d :=
  mul_pos (pow_pos hp _) (pow_pos (by linarith) _)

/-- A candidate `e` further away has `(p / (1 - p))^e` times the likelihood. -/
theorem bsc_ratio (p : K) (hp2 : p < 1) {n d e : ℕ} (hde : d + e ≤ n) :
    bsc p n (d + e) = (p / (1 - p)) ^ e * bsc p n d := by
  unfold bsc
  have hq : (1 - p) ≠ 0 := by linarith
  have : n - d = (n - (d + e)) + e := by omega
  rw [this, pow_add, pow_add, div_pow]
  field_simp

/-- Below rate one half, the likelihood falls with distance. -/
theorem bsc_anti (p : K) (hp : 0 < p) (hp2 : p ≤ 1 / 2) {n d d' : ℕ}
    (hdd : d ≤ d') (hd' : d' ≤ n) : bsc p n d' ≤ bsc p n d := by
  obtain ⟨e, rfl⟩ := Nat.exists_eq_add_of_le hdd
  have hp1 : p < 1 := by linarith
  rw [bsc_ratio p hp1 hd']
  have hr0 : 0 ≤ p / (1 - p) := div_nonneg hp.le (by linarith)
  have hr1 : p / (1 - p) ≤ 1 := by rw [div_le_one (by linarith)]; linarith
  calc (p / (1 - p)) ^ e * bsc p n d ≤ 1 * bsc p n d :=
        mul_le_mul_of_nonneg_right (pow_le_one₀ hr0 hr1)
          (bsc_nonneg p hp.le hp1.le n d)
    _ = bsc p n d := one_mul _

/-- **The floor on a resolved fork.** On the binary symmetric channel with
`0 < p ≤ 1/2`, a survivor whose rivals all lie at least `gap` further from
the read has posterior at least `1 / (1 + (k - 1) (p / (1 - p))^gap)`. -/
theorem fork_confidence_bound [DecidableEq ι] (p : K) (hp : 0 < p)
    (hp2 : p ≤ 1 / 2) (dist : ι → ℕ) (n : ℕ) (S : Finset ι) {c : ι}
    (hc : c ∈ S) {gap : ℕ} (hfar : ∀ s ∈ S, s ≠ c → dist c + gap ≤ dist s)
    (hn : ∀ s ∈ S, dist s ≤ n) :
    1 / (1 + ((S.card : K) - 1) * (p / (1 - p)) ^ gap)
      ≤ posterior (fun s => bsc p n (dist s)) S c := by
  have hp1 : p < 1 := by linarith
  refine resolved_bound _ S hc (bsc_pos p hp hp1 n _)
    (fun s => bsc_nonneg p hp.le hp1.le n _) ?_
  intro s hs hsc
  have h1 := hfar s hs hsc
  have h2 := hn s hs
  calc bsc p n (dist s) ≤ bsc p n (dist c + gap) := bsc_anti p hp hp2 h1 h2
    _ = (p / (1 - p)) ^ gap * bsc p n (dist c) :=
        bsc_ratio p hp1 (le_trans h1 h2)

end GLM.DecoderConfidence
