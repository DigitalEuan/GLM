import UBP.Alpha
import UBP.Masses

set_option autoImplicit false

/-!
# Stage 4 — how much a numerical agreement can possibly prove

Stages 0–3 end with three real seeds and a pile of integers.  The framework's
evidential case is that expressions built from them reproduce measured
constants: `137 + L` matches `α⁻¹` to `0.0196 %`, `169/w` matches `m_μ/m_e` to
`0.0294 %`, `1836 + 2Lσ` matches `m_p/m_e` to `3.74×10⁻⁷`.

The parent study verified that those numbers are correct.  The first-principles
question is different and prior to it: **how surprising is an agreement of that
size?**  A formula of the shape "fixed integer plus a multiple of a small
constant" is a *lattice of candidate values*, and a lattice with spacing `s`
approximates every real target to within `s/2` whether or not it has anything to
do with physics.  The theorems below make that quantitative, and the answer is
uncomfortable for two of the three headline fits.

Findings (FP-25 … FP-31):

* **FP-25** Lattice approximation: for any spacing `s > 0` and any target `t`
  there is an integer `p` with `|p·s − t| ≤ s/2` (`lattice_approx`).  Nothing
  about the seeds is used.
* **FP-26** *The `α⁻¹` fit is not evidence.*  For **every** target `t ≥ 137`
  some integer multiple of `L` added to `137` reproduces it to
  relative accuracy `≤ 2.3×10⁻⁴` (`alpha_generic_guarantee`).  The framework's
  actual agreement is `1.96×10⁻⁴`, i.e. **less than 1.2× better than the
  guarantee that holds for any target whatsoever**
  (`alpha_fit_barely_beats_generic`).
* **FP-27** The same is true with `L` replaced by any positive number of the
  same size: the phenomenon is a property of the *shape* of the formula, not of
  the seeds (`matching_is_seed_independent`).
* **FP-28** *The `m_μ/m_e` fit is worth about one order of magnitude.*  The
  family `n/w`, `n ∈ ℤ`, reproduces every target near `206.77` to relative
  accuracy `≤ 2.97×10⁻³` (`muon_generic_guarantee`); the framework achieves
  `2.94×10⁻⁴`, about `10×` better (`muon_fit_beats_generic_by_ten`).
* **FP-29** *The `m_p/m_e` fit is worth about a factor 4.*  `1836 + 2Lσ` with
  `σ = 29/24` is `1836 + (29/12)·L`; the family `1836 + (p/12)·L`, `p ∈ ℤ`,
  reproduces every target near `1836` to `≤ 1.5×10⁻⁶` relative
  (`proton_generic_guarantee`), against an achieved `3.74×10⁻⁷`
  (`proton_fit_beats_generic_by_four`).
* **FP-30** The general form of the argument: a finite family of `N` candidate
  predictions can match a set of targets of Lebesgue measure at most `2Nδ`
  within `δ` (`fit_capacity`); so a match is evidence only in so far as
  `2Nδ` is small compared with the range of plausible targets
  (`unmatched_target_exists`).
* **FP-31** The intermediate layer of the "seed hierarchy" adds nothing:
  `13L = w` and `ℳ/13 = 1 + L` are the definition of `L` rewritten
  (`derived_layer_is_definitional`, quoting the parent study).
-/

namespace UBPFirstPrinciples

open MeasureTheory UBP

/-! ## FP-25  Lattice approximation -/

/-- Any arithmetic progression of spacing `s > 0` comes within `s/2` of every
real target. -/
theorem lattice_approx (s : ℝ) (hs : 0 < s) (t : ℝ) : ∃ p : ℤ, |(p : ℝ) * s - t| ≤ s / 2 := by
  refine ⟨round (t / s), ?_⟩
  have h := abs_sub_round (t / s)
  have he : (round (t / s) : ℝ) * s - t = -((t / s - (round (t / s) : ℝ)) * s) := by
    field_simp; ring
  rw [he, abs_neg, abs_mul, abs_of_pos hs]
  nlinarith [h, hs, abs_nonneg (t / s - (round (t / s) : ℝ))]

/-- Shifted form: a progression through a fixed offset `c`. -/
theorem lattice_approx_offset (c s : ℝ) (hs : 0 < s) (t : ℝ) :
    ∃ p : ℤ, |c + (p : ℝ) * s - t| ≤ s / 2 := by
  obtain ⟨p, hp⟩ := lattice_approx s hs (t - c)
  exact ⟨p, by simpa [sub_sub_eq_add_sub, add_comm, add_sub_assoc] using hp⟩

/-! ## FP-27  The phenomenon does not involve the seeds -/

/-- For *any* positive step `s`, the formula shape `137 + p·s` reproduces every
target to within `s/2`.  The seeds are irrelevant to this. -/
theorem matching_is_seed_independent (s : ℝ) (hs : 0 < s) (t : ℝ) :
    ∃ p : ℤ, |137 + (p : ℝ) * s - t| ≤ s / 2 :=
  lattice_approx_offset 137 s hs t

/-! ## FP-26  The fine-structure fit -/

theorem leak_lt : leak < 0.063 := by
  have := leak_enc.2; norm_num at this ⊢; linarith

theorem leak_gt : 0.0628 < leak := by
  have := leak_enc.1; norm_num at this ⊢; linarith

/-- **FP-26.**  Every target `t ≥ 137` is reproduced by `137 + p·L`
for some integer `p`, to relative accuracy at most `2.3×10⁻⁴`. -/
theorem alpha_generic_guarantee (t : ℝ) (h1 : 137 ≤ t) :
    ∃ p : ℤ, |137 + (p : ℝ) * leak - t| / t ≤ 0.00023 := by
  obtain ⟨p, hp⟩ := lattice_approx_offset 137 leak leak_pos t
  refine ⟨p, ?_⟩
  rw [div_le_iff₀ (by linarith)]
  have hL : leak / 2 < 0.0315 := by linarith [leak_lt]
  nlinarith [hp, hL, h1]

/-- The framework's actual `α⁻¹` accuracy is less than `1.2` times better than
the guarantee of `alpha_generic_guarantee`, which holds for *every* target: the
agreement carries essentially no evidential weight. -/
theorem alpha_fit_barely_beats_generic :
    relErr alphaBaseline alphaInvTarget * 1.2 > 0.00023 := by
  have h := alphaBaseline_relErr.1
  norm_num at h ⊢
  linarith

/-! ## FP-28  The muon fit -/

theorem wobble_lt : wobble < 0.8176 := by
  have := wobble_enc.2; norm_num at this ⊢; linarith

theorem wobble_gt : 0.81758 < wobble := by
  have := wobble_enc.1; norm_num at this ⊢; linarith

/-- **FP-28.**  Every target `t ≥ 206` is reproduced by `n/w` for some
integer `n`, to relative accuracy at most `2.96×10⁻³`. -/
theorem muon_generic_guarantee (t : ℝ) (h1 : 206 ≤ t) :
    ∃ n : ℤ, |(n : ℝ) / wobble - t| / t ≤ 0.00297 := by
  have hs : 0 < 1 / wobble := one_div_pos.mpr wobble_pos
  obtain ⟨n, hn⟩ := lattice_approx (1 / wobble) hs t
  refine ⟨n, ?_⟩
  have hdiv : (n : ℝ) / wobble = (n : ℝ) * (1 / wobble) := by ring
  rw [hdiv, div_le_iff₀ (by linarith)]
  have hw2 : (0 : ℝ) < 2 * wobble := by linarith [wobble_pos]
  have hhalf : (1 / wobble) / 2 < 0.6116 := by
    have he : (1 / wobble) / 2 = 1 / (2 * wobble) := by ring
    rw [he, div_lt_iff₀ hw2]
    nlinarith [wobble_gt]
  nlinarith [hn, hhalf, h1]

/-- The framework's `m_μ/m_e` accuracy is better than the generic guarantee by a
factor strictly between 10 and 11: this fit does carry some information, of
order one decimal digit. -/
theorem muon_fit_beats_generic_by_ten :
    relErr muonPred muonRatioTarget * 10 < 0.00297 ∧
      relErr muonPred muonRatioTarget * 11 > 0.00297 := by
  have h1 := muonPred_relErr.1
  have h2 := muonPred_relErr.2
  norm_num at h1 h2 ⊢
  constructor <;> linarith

/-! ## FP-29  The proton fit -/

/-- `1836 + 2Lσ` with `σ = 29/24` is `1836 + 29·(L/12)`. -/
theorem protonPred_eq : protonPred = 1836 + (29 : ℝ) * (leak / 12) := by
  rw [protonPred]; ring

/-- **FP-29.**  Every target `t ≥ 1836` is reproduced by
`1836 + p·(L/12)` for some integer `p`, to relative accuracy at most
`1.5×10⁻⁶`. -/
theorem proton_generic_guarantee (t : ℝ) (h1 : 1836 ≤ t) :
    ∃ p : ℤ, |1836 + (p : ℝ) * (leak / 12) - t| / t ≤ 0.0000015 := by
  have hs : 0 < leak / 12 := div_pos leak_pos (by norm_num)
  obtain ⟨p, hp⟩ := lattice_approx_offset 1836 (leak / 12) hs t
  refine ⟨p, ?_⟩
  rw [div_le_iff₀ (by linarith)]
  have hhalf : (leak / 12) / 2 < 0.002625 := by linarith [leak_lt]
  nlinarith [hp, hhalf, h1]

/-- The framework's `m_p/m_e` accuracy is better than the generic guarantee for a
coefficient of denominator 12 by a factor strictly between 4 and 5. -/
theorem proton_fit_beats_generic_by_four :
    relErr protonPred protonRatioTarget * 4 < 0.0000015 ∧
      relErr protonPred protonRatioTarget * 5 > 0.0000015 := by
  have h1 := protonPred_relErr.1
  have h2 := protonPred_relErr.2
  norm_num at h1 h2 ⊢
  constructor <;> linarith

/-! ## FP-30  The general no-miracle bound -/

/-- **FP-30.**  A finite family of candidate predictions matches only a set of
targets of measure at most `2·N·δ`. -/
theorem fit_capacity (s : Finset ℝ) (δ : ℝ) :
    volume {x : ℝ | ∃ y ∈ s, |x - y| ≤ δ} ≤ (s.card : ENNReal) * ENNReal.ofReal (2 * δ) := by
  have hset : {x : ℝ | ∃ y ∈ s, |x - y| ≤ δ} = ⋃ y ∈ s, Metric.closedBall y δ := by
    ext x; simp [Metric.mem_closedBall, Real.dist_eq]
  rw [hset]
  calc volume (⋃ y ∈ s, Metric.closedBall y δ) ≤ ∑ y ∈ s, volume (Metric.closedBall y δ) :=
        measure_biUnion_finset_le s _
    _ = (s.card : ENNReal) * ENNReal.ofReal (2 * δ) := by
        simp [Real.volume_closedBall, Finset.sum_const, nsmul_eq_mul]

/-- Contrapositive form: if the candidate family is small compared with the
range of plausible targets, some target is *not* matched — which is exactly the
condition under which a match would have been informative. -/
theorem unmatched_target_exists (s : Finset ℝ) (δ : ℝ) (hδ : 0 ≤ δ) (a b : ℝ)
    (h : (s.card : ℝ) * (2 * δ) < b - a) : ∃ t ∈ Set.Icc a b, ∀ y ∈ s, δ < |t - y| := by
  by_contra hcon
  push_neg at hcon
  have hsub : Set.Icc a b ⊆ {x : ℝ | ∃ y ∈ s, |x - y| ≤ δ} := by
    intro x hx
    obtain ⟨y, hy, hle⟩ := hcon x hx
    exact ⟨y, hy, hle⟩
  have h1 : volume (Set.Icc a b) ≤ (s.card : ENNReal) * ENNReal.ofReal (2 * δ) :=
    le_trans (measure_mono hsub) (fit_capacity s δ)
  rw [Real.volume_Icc] at h1
  rw [← ENNReal.ofReal_natCast, ← ENNReal.ofReal_mul (by positivity)] at h1
  rw [ENNReal.ofReal_le_ofReal_iff (by positivity)] at h1
  linarith

/-! ## FP-31  The derived layer is definitional -/

/-- `13L = w` and `ℳ/13 = 1 + L`: Level 2 of the framework's "seed hierarchy"
is the definition of `L` written twice, and adds no content. -/
theorem derived_layer_is_definitional :
    13 * leak = wobble ∧ monad / 13 = 1 + leak :=
  ⟨leak_thirteen, monad_div_thirteen⟩

end UBPFirstPrinciples
