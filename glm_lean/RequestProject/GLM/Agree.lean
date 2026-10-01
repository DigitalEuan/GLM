module

public import Mathlib
public import RequestProject.GLM.DecoderConfidence

/-!
# The second reading's channel: what two reads of one carrier add

The formal half of `studies/AGREE_CHANNEL_STUDY.md` (Phase 81,
`glm_universal.reasoning.agree_channel_marks`). Two reads of one carrier are
conditionally independent given the truth: the pair `(y₁, y₂)` has mass
`P y₁ * P y₂`.

* `agree_answered_sq` — the two reads decode to `j` together with probability
  `A_j²`, where `A_j` is the probability that one read decodes to `j`.
* `agree_residual_le_single` — if the truth is the modal answer (`A_s ≤ A_t`
  for every answer `s`), then among the pairs that agree the wrong mass is a
  smaller share than among single reads: strict agreement's
  `P(wrong | answered)` is at most the single reading's.
* `agree_conf_sum` — on the binary symmetric channel the product of two reads'
  likelihoods is the likelihood at the summed distance over twice the length,
  so the pair's posterior depends on the pair only through summed distances.
* `pair_distance_split` — bit by bit, `[x ≠ c] + [y ≠ c] = [x ≠ y] +
  2 [x = y ∧ x ≠ c]`: summed over the coordinates, two reads are an erasure
  where they differ and a doubled read where they agree.
-/

@[expose] public section

namespace GLM.Agree

open Finset GLM.DecoderConfidence

variable {ι β K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

omit [LinearOrder K] [IsStrictOrderedRing K] in
/-- **Two independent reads agree on `j` with probability `A_j²`.** -/
theorem agree_answered_sq [DecidableEq β] (Y : Finset ι) (P : ι → K)
    (dec : ι → β) (j : β) :
    ∑ y ∈ (Y ×ˢ Y).filter (fun y => dec y.1 = j ∧ dec y.2 = j), P y.1 * P y.2
      = (∑ y ∈ Y.filter (fun y => dec y = j), P y) ^ 2 := by
  rw [Finset.filter_product (p := fun y => dec y = j)
    (q := fun y => dec y = j), Finset.sum_product, sq, Finset.sum_mul_sum]

/-- **Agreement lowers the residual.** If the truth `t` is the modal answer,
the wrong share of the agreeing pairs (masses `A s ^ 2`) is at most the wrong
share of single reads (masses `A s`), written without division:
`(Σ_{s ≠ t} A_s²) (Σ_s A_s) ≤ (Σ_{s ≠ t} A_s) (Σ_s A_s²)`. -/
theorem agree_residual_le_single [DecidableEq β] (S : Finset β) (A : β → K)
    {t : β} (ht : t ∈ S) (hA : ∀ s ∈ S, 0 ≤ A s)
    (hmodal : ∀ s ∈ S, A s ≤ A t) :
    (∑ s ∈ S.erase t, A s ^ 2) * ∑ s ∈ S, A s
      ≤ (∑ s ∈ S.erase t, A s) * ∑ s ∈ S, A s ^ 2 := by
  rw [← Finset.add_sum_erase S _ ht, ← Finset.add_sum_erase S (fun s => A s ^ 2) ht]
  have ha : 0 ≤ A t := hA t ht
  have hY : ∑ s ∈ S.erase t, A s ^ 2 ≤ A t * ∑ s ∈ S.erase t, A s := by
    rw [Finset.mul_sum]
    refine Finset.sum_le_sum fun s hs => ?_
    have hs' := Finset.mem_of_mem_erase hs
    have h0 := hA s hs'
    have h1 := hmodal s hs'
    nlinarith
  have hX : 0 ≤ ∑ s ∈ S.erase t, A s :=
    Finset.sum_nonneg fun s hs => hA s (Finset.mem_of_mem_erase hs)
  nlinarith [mul_le_mul_of_nonneg_left hY ha]

omit [LinearOrder K] [IsStrictOrderedRing K] in
/-- The product of two reads' likelihoods is the likelihood at the summed
distance over twice the length. -/
theorem bsc_mul_bsc (p : K) {n d₁ d₂ : ℕ} (h₁ : d₁ ≤ n) (h₂ : d₂ ≤ n) :
    bsc p n d₁ * bsc p n d₂ = bsc p (2 * n) (d₁ + d₂) := by
  unfold bsc
  have : 2 * n - (d₁ + d₂) = (n - d₁) + (n - d₂) := by omega
  rw [this, pow_add, pow_add]
  ring

omit [LinearOrder K] [IsStrictOrderedRing K] in
/-- **The pair's confidence depends only on summed distances.** The posterior
of a candidate under the product of two reads' likelihoods equals its
posterior under one read at the summed distance over twice the length. -/
theorem agree_conf_sum (p : K) (n : ℕ) (d₁ d₂ : ι → ℕ) (S : Finset ι) (c : ι)
    (h₁ : ∀ s, d₁ s ≤ n) (h₂ : ∀ s, d₂ s ≤ n) :
    posterior (fun s => bsc p n (d₁ s) * bsc p n (d₂ s)) S c
      = posterior (fun s => bsc p (2 * n) (d₁ s + d₂ s)) S c := by
  unfold posterior
  simp only [bsc_mul_bsc p (h₁ _) (h₂ _)]

/-- One coordinate of `pair_distance_split`. -/
theorem bit_split (x y c : Bool) :
    ((if x ≠ c then 1 else 0) + (if y ≠ c then 1 else 0) : ℕ)
      = (if x ≠ y then 1 else 0) + 2 * (if x = y ∧ x ≠ c then 1 else 0) := by
  cases x <;> cases y <;> cases c <;> decide

/-- **Two reads: an erasure where they differ, a doubled read where they
agree.** Over `n` coordinates, `d(x, c) + d(y, c) = d(x, y) + 2 · #{i : x i =
y i ≠ c i}`. -/
theorem pair_distance_split {n : ℕ} (x y c : Fin n → Bool) :
    hammingDist x c + hammingDist y c
      = hammingDist x y
        + 2 * (Finset.univ.filter (fun i => x i = y i ∧ x i ≠ c i)).card := by
  simp only [hammingDist, Finset.card_filter, Finset.mul_sum,
    ← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl fun i _ => bit_split (x i) (y i) (c i)

end GLM.Agree
