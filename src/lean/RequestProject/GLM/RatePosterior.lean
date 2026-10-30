module

public import Mathlib

/-!
# The rate posterior: what a confidence marginalized over the rate promises

The formal half of `studies/RATE_POSTERIOR_STUDY.md` (Phase 82,
`glm_universal.reasoning.rate_posterior`). The bit-flip rate `p` ranges over a
declared finite grid `P`; an observation `ω` (the reads of one call) has joint
mass `m p ω` with the rate (prior times likelihood), and at rate `p` the
answer given `ω` is right with probability `conf p ω`. The marginal
confidence of the answer is `R ω / M ω` with `R ω = Σ_p m p ω * conf p ω` and
`M ω = Σ_p m p ω`.

* `soft_floor_error_le` — answering only where the marginal confidence is at
  least `t` (written without division, `t * M ω ≤ R ω`), the answered
  observations are wrong with joint mass at most `(1 - t)` times their mass:
  the floor's promise, under the joint measure of rate, truth and reads.
* `rate_posterior_prod` — updating a posterior on one likelihood and then on a
  second gives the posterior on their product: reads may be taken one at a
  time or all at once.
* `naive_rate_underestimates` — a statistic pointwise at most another, and
  strictly below it at one point of positive mass, has a strictly smaller
  mean (the distance from a read to its nearest codeword against the number
  of flipped bits).
* `read_marginal_eq_coset_mass` — summing a function of `y - c` over the code
  is summing it over the coset `y - C`: the likelihood of a read with the
  truth summed out is its coset's mass.
-/

@[expose] public section

namespace GLM.RatePosterior

open Finset

variable {ι κ K : Type*} [Field K] [LinearOrder K] [IsStrictOrderedRing K]

/-- **The promise of the soft floor.** Over the observations whose marginal
confidence is at least `t`, the wrong mass is at most `1 - t` times the mass
answered. -/
theorem soft_floor_error_le (Ω : Finset ι) (P : Finset κ) (m conf : κ → ι → K)
    (t : K) :
    ∑ ω ∈ Ω.filter (fun ω => t * ∑ p ∈ P, m p ω ≤ ∑ p ∈ P, m p ω * conf p ω),
        (∑ p ∈ P, m p ω - ∑ p ∈ P, m p ω * conf p ω)
      ≤ (1 - t) * ∑ ω ∈ Ω.filter
          (fun ω => t * ∑ p ∈ P, m p ω ≤ ∑ p ∈ P, m p ω * conf p ω),
          ∑ p ∈ P, m p ω := by
  rw [Finset.mul_sum]
  refine Finset.sum_le_sum fun ω hω => ?_
  rw [Finset.mem_filter] at hω
  linarith [hω.2]

/-- One Bayes update over a finite grid. -/
def update (P : Finset κ) (prior L : κ → K) (p : κ) : K :=
  prior p * L p / ∑ q ∈ P, prior q * L q

/-- **Sequential updates give the batch posterior.** -/
theorem rate_posterior_prod (P : Finset κ) (prior L₁ L₂ : κ → K)
    (h₁ : ∑ q ∈ P, prior q * L₁ q ≠ 0) (p : κ) :
    update P (update P prior L₁) L₂ p
      = update P prior (fun q => L₁ q * L₂ q) p := by
  unfold update
  set Z := ∑ q ∈ P, prior q * L₁ q with hZ
  have hs : ∑ q ∈ P, prior q * L₁ q / Z * L₂ q
      = (∑ q ∈ P, prior q * (L₁ q * L₂ q)) / Z := by
    rw [Finset.sum_div]
    refine Finset.sum_congr rfl fun q _ => ?_
    ring
  rw [hs]
  rcases eq_or_ne (∑ q ∈ P, prior q * (L₁ q * L₂ q)) 0 with h | h
  · rw [h, zero_div, div_zero, div_zero]
  · field_simp

/-- **A smaller statistic has a smaller mean.** -/
theorem naive_rate_underestimates (Ω : Finset ι) (m f g : ι → K)
    (hm : ∀ ω ∈ Ω, 0 ≤ m ω) (hfg : ∀ ω ∈ Ω, f ω ≤ g ω)
    {ω₀ : ι} (h₀ : ω₀ ∈ Ω) (hpos : 0 < m ω₀) (hlt : f ω₀ < g ω₀) :
    ∑ ω ∈ Ω, m ω * f ω < ∑ ω ∈ Ω, m ω * g ω :=
  Finset.sum_lt_sum (fun ω hω => mul_le_mul_of_nonneg_left (hfg ω hω) (hm ω hω))
    ⟨ω₀, h₀, mul_lt_mul_of_pos_left hlt hpos⟩

/-- **The truth summed out is the coset's mass.** -/
theorem read_marginal_eq_coset_mass {G M : Type*} [AddGroup G] [DecidableEq G]
    [AddCommMonoid M] (C : Finset G) (f : G → M) (y : G) :
    ∑ c ∈ C, f (y - c) = ∑ e ∈ C.image (fun c => y - c), f e := by
  rw [Finset.sum_image]
  intro a _ b _ h
  simpa using h

end GLM.RatePosterior
