/-
# How much a numerical agreement can possibly prove

The GLM archive is full of numerical fits: `α⁻¹ = 137 + L`, `m_μ/m_e = 169/w`,
`m_p/m_e = 1836 + 2Lσ`, where the constants come from the "monad"
`ℳ = π φ e = 13.8175…`, its integer part `13`, the *wobble* `w = ℳ − 13` and the
*leak* `L = w/13`.  Each fit is numerically correct, and each was reported as
evidence for the framework.

This file retrieves the instrument that decides how much such an agreement is
worth, and it is the piece of the archive most obviously worth keeping: it turns
"is this impressive?" from an argument into a measurement.

**The general statement.**  A formula of the shape "fixed number plus an integer
multiple of a small constant" is an arithmetic progression, and a progression of
spacing `s` lands within `s/2` of *every* real target:

* `lattice_approx`, `lattice_approx_offset` — the approximation itself;
* `generic_relative_guarantee` — in relative terms, every target `t ≥ T > 0` is
  matched to within `s/(2T)` by *some* member of the family.  Nothing about the
  constants is used, which is the point: `matching_is_seed_independent`;
* `fit_capacity` — the measure-theoretic form.  A family of `N` candidate
  predictions matching within `δ` can only match a set of targets of Lebesgue
  measure at most `2Nδ`;
* `unmatched_target_exists` — and if the family is small compared with the range
  of plausible targets then some target is missed, which is exactly the
  condition under which a hit would have been informative.

**The ledger.**  `bitScore generic achieved = log₂(generic / achieved)` counts
how many binary digits of agreement a fit buys over the guarantee that holds for
any target of the same size, and the three headline fits are scored:

| fit | generic guarantee | achieved | bits |
|---|---|---|---|
| `α⁻¹ = 137 + L` | `2.3×10⁻⁴` | `1.9624×10⁻⁴` | `0 < b < 1` (`alpha_bits_lt_one`) |
| `m_μ/m_e = 169/w` | `2.97×10⁻³` | `2.9376×10⁻⁴` | `3 < b < 4` (`muon_bits_between_three_and_four`) |
| `m_p/m_e = 1836 + 2Lσ` | `1.5×10⁻⁶` | `3.7434×10⁻⁷` | `2 < b < 3` (`proton_bits_between_two_and_three`) |

So the fine-structure agreement is worth **less than one bit** and is not
evidence; the muon fit is worth three to four bits; the proton fit two to three.
`capacityBits_double` records the corollary that doubling the number of
candidate formulas costs exactly one bit, which is what makes the ledger a
triage tool rather than a verdict.

All the numerical bounds below are derived from `Real.pi_gt_d6` / `Real.pi_lt_d6`
and `Real.exp_one_gt_d9` / `Real.exp_one_lt_d9`, so the intervals are as tight as
the available `π` bound allows and no tighter.
-/
import Mathlib

namespace GLM.FitCapacity

open MeasureTheory

/-! ## 1. Lattice approximation: the shape, not the constants -/

/-- Any arithmetic progression of spacing `s > 0` comes within `s/2` of every
real target. -/
theorem lattice_approx (s : ℝ) (hs : 0 < s) (t : ℝ) : ∃ p : ℤ, |(p : ℝ) * s - t| ≤ s / 2 := by
  refine ⟨round (t / s), ?_⟩
  have h := abs_sub_round (t / s)
  have he : (round (t / s) : ℝ) * s - t = -((t / s - (round (t / s) : ℝ)) * s) := by
    field_simp
    ring
  rw [he, abs_neg, abs_mul, abs_of_pos hs]
  nlinarith [h, hs, abs_nonneg (t / s - (round (t / s) : ℝ))]

/-- The same through a fixed offset `c`. -/
theorem lattice_approx_offset (c s : ℝ) (hs : 0 < s) (t : ℝ) :
    ∃ p : ℤ, |c + (p : ℝ) * s - t| ≤ s / 2 := by
  obtain ⟨p, hp⟩ := lattice_approx s hs (t - c)
  exact ⟨p, by simpa [sub_sub_eq_add_sub, add_comm, add_sub_assoc] using hp⟩

/-- **The generic guarantee.**  For any offset `c`, any spacing `s > 0` and any
target `t` at least `T > 0`, some member of the family `c + p·s` matches `t` to
relative accuracy `s/(2T)`.  This is the number every claimed fit must be
compared against. -/
theorem generic_relative_guarantee (c s T t : ℝ) (hs : 0 < s) (hT : 0 < T) (ht : T ≤ t) :
    ∃ p : ℤ, |c + (p : ℝ) * s - t| / t ≤ s / (2 * T) := by
  obtain ⟨p, hp⟩ := lattice_approx_offset c s hs t
  refine ⟨p, ?_⟩
  have ht0 : 0 < t := lt_of_lt_of_le hT ht
  rw [div_le_div_iff₀ ht0 (by positivity)]
  nlinarith [hp, abs_nonneg (c + (p : ℝ) * s - t)]

/-- The phenomenon has nothing to do with the framework's constants: for *any*
positive step the shape `137 + p·s` reproduces every target to within `s/2`. -/
theorem matching_is_seed_independent (s : ℝ) (hs : 0 < s) (t : ℝ) :
    ∃ p : ℤ, |137 + (p : ℝ) * s - t| ≤ s / 2 :=
  lattice_approx_offset 137 s hs t

/-! ## 2. The capacity bound -/

/-- **No miracles.**  A finite family of candidate predictions matches only a set
of targets of measure at most `2·N·δ`. -/
theorem fit_capacity (s : Finset ℝ) (δ : ℝ) :
    volume {x : ℝ | ∃ y ∈ s, |x - y| ≤ δ} ≤ (s.card : ENNReal) * ENNReal.ofReal (2 * δ) := by
  have hset : {x : ℝ | ∃ y ∈ s, |x - y| ≤ δ} = ⋃ y ∈ s, Metric.closedBall y δ := by
    ext x; simp [Metric.mem_closedBall, Real.dist_eq]
  rw [hset]
  calc volume (⋃ y ∈ s, Metric.closedBall y δ) ≤ ∑ y ∈ s, volume (Metric.closedBall y δ) :=
        measure_biUnion_finset_le s _
    _ = (s.card : ENNReal) * ENNReal.ofReal (2 * δ) := by
        simp [Real.volume_closedBall, Finset.sum_const, nsmul_eq_mul]

/-- Contrapositive: if the candidate family is small compared with the range of
plausible targets, some target is not matched. -/
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

/-! ## 3. The archive's constants, bounded exactly -/

/-- The golden ratio. -/
noncomputable def phi : ℝ := (1 + Real.sqrt 5) / 2

/-- Euler's number, as the archive's third seed. -/
noncomputable def eSeed : ℝ := Real.exp 1

/-- The "monad" `ℳ = π φ e`. -/
noncomputable def monad : ℝ := Real.pi * phi * eSeed

/-- The "wobble" `w = ℳ − 13`. -/
noncomputable def wobble : ℝ := monad - 13

/-- The "leak" `L = w/13`. -/
noncomputable def leak : ℝ := wobble / 13

/-- The relative error of a prediction against a target. -/
noncomputable def relErr (pred target : ℝ) : ℝ := |pred - target| / target

theorem sqrt5_bounds : 2.2360679774 < Real.sqrt 5 ∧ Real.sqrt 5 < 2.2360679775 := by
  have h5 : Real.sqrt 5 ^ 2 = 5 := Real.sq_sqrt (by norm_num)
  have hnn : 0 ≤ Real.sqrt 5 := Real.sqrt_nonneg 5
  constructor <;> nlinarith [h5, hnn]

theorem phi_bounds : 1.6180339887 < phi ∧ phi < 1.61803398875 := by
  obtain ⟨hl, hu⟩ := sqrt5_bounds
  unfold phi
  constructor <;> linarith

theorem eSeed_bounds : 2.7182818283 < eSeed ∧ eSeed < 2.7182818286 :=
  ⟨Real.exp_one_gt_d9, Real.exp_one_lt_d9⟩

theorem pi_bounds : 3.1415926535 < Real.pi ∧ Real.pi < 3.1415926536 :=
  ⟨by linarith [Real.pi_gt_d20], by linarith [Real.pi_lt_d20]⟩

theorem pi_mul_phi_bounds : 5.08320369 < Real.pi * phi ∧ Real.pi * phi < 5.08320370 := by
  obtain ⟨hp1, hp2⟩ := pi_bounds
  obtain ⟨hf1, hf2⟩ := phi_bounds
  constructor <;> nlinarith

/-- `ℳ = π φ e ∈ (13.8175802, 13.8175803)`. -/
theorem monad_bounds : 13.8175802 < monad ∧ monad < 13.8175803 := by
  obtain ⟨h1, h2⟩ := pi_mul_phi_bounds
  obtain ⟨he1, he2⟩ := eSeed_bounds
  constructor <;> · unfold monad eSeed at *; nlinarith

/-- `⌊ℳ⌋ = 13`: the integer the framework reads off the monad. -/
theorem monad_floor : ⌊monad⌋ = 13 := by
  obtain ⟨hl, hu⟩ := monad_bounds
  have h1 : (13 : ℝ) ≤ monad := by linarith
  have h2 : monad < 14 := by linarith
  exact Int.floor_eq_iff.2 ⟨by exact_mod_cast h1, by push_cast; linarith⟩

theorem wobble_bounds : 0.8175802 < wobble ∧ wobble < 0.8175803 := by
  obtain ⟨hl, hu⟩ := monad_bounds
  unfold wobble
  constructor <;> linarith

theorem wobble_pos : 0 < wobble := by linarith [wobble_bounds.1]

theorem leak_bounds : 0.06289078 < leak ∧ leak < 0.06289080 := by
  obtain ⟨hl, hu⟩ := wobble_bounds
  unfold leak
  constructor <;> linarith

theorem leak_pos : 0 < leak := by linarith [leak_bounds.1]

/-- The framework's "derived layer" is its own definition rewritten: `13L = w`
and `ℳ/13 = 1 + L` are both immediate, so that layer adds no content. -/
theorem derived_layer_is_definitional : 13 * leak = wobble ∧ monad / 13 = 1 + leak := by
  unfold leak wobble
  constructor <;> ring

/-! ## 4. The three fits, and what each is worth -/

/-- CODATA `α⁻¹`. -/
def alphaInvTarget : ℝ := 137.035999177

/-- CODATA `m_μ/m_e`. -/
def muonRatioTarget : ℝ := 206.7682827

/-- CODATA `m_p/m_e`. -/
def protonRatioTarget : ℝ := 1836.152673426

/-- The framework's `α⁻¹` prediction. -/
noncomputable def alphaBaseline : ℝ := 137 + leak

/-- The framework's `m_μ/m_e` prediction. -/
noncomputable def muonPred : ℝ := 169 / wobble

/-- The framework's `m_p/m_e` prediction, `1836 + 2Lσ` with `σ = 29/24`. -/
noncomputable def protonPred : ℝ := 1836 + 29 * (leak / 12)

/-! ### The fine-structure fit -/

/-- Every target `t ≥ 137` is reproduced by `137 + p·L` for some integer `p`, to
relative accuracy at most `2.3×10⁻⁴`.  Nothing about the target is used. -/
theorem alpha_generic_guarantee (t : ℝ) (h1 : 137 ≤ t) :
    ∃ p : ℤ, |137 + (p : ℝ) * leak - t| / t ≤ 0.00023 := by
  obtain ⟨p, hp⟩ := generic_relative_guarantee 137 leak 137 t leak_pos (by norm_num) h1
  refine ⟨p, le_trans hp ?_⟩
  rw [div_le_iff₀ (by norm_num)]
  linarith [leak_bounds.2]

theorem alpha_relErr_bounds :
    0.00019623 < relErr alphaBaseline alphaInvTarget ∧
      relErr alphaBaseline alphaInvTarget < 0.00019624 := by
  obtain ⟨hl, hu⟩ := leak_bounds
  have habs : |alphaBaseline - alphaInvTarget| = leak - 0.035999177 := by
    unfold alphaBaseline alphaInvTarget
    rw [abs_of_pos (by linarith)]
    ring
  unfold relErr
  rw [habs, alphaInvTarget]
  constructor
  · rw [lt_div_iff₀ (by norm_num)]; linarith
  · rw [div_lt_iff₀ (by norm_num)]; linarith

/-- **The fine-structure agreement is not evidence.**  It beats the guarantee
that holds for *every* target by a factor smaller than `1.2`. -/
theorem alpha_fit_barely_beats_generic :
    relErr alphaBaseline alphaInvTarget < 0.00023 ∧
      0.00023 < relErr alphaBaseline alphaInvTarget * 1.2 := by
  obtain ⟨hl, hu⟩ := alpha_relErr_bounds
  constructor <;> linarith

/-! ### The muon fit -/

/-- Every target `t ≥ 206` is reproduced by `n/w` for some integer `n`, to
relative accuracy at most `2.97×10⁻³`. -/
theorem muon_generic_guarantee (t : ℝ) (h1 : 206 ≤ t) :
    ∃ n : ℤ, |(n : ℝ) / wobble - t| / t ≤ 0.00297 := by
  have hs : 0 < 1 / wobble := one_div_pos.mpr wobble_pos
  obtain ⟨n, hn⟩ := generic_relative_guarantee 0 (1 / wobble) 206 t hs (by norm_num) h1
  refine ⟨n, ?_⟩
  have hrw : (n : ℝ) / wobble = 0 + (n : ℝ) * (1 / wobble) := by ring
  rw [hrw]
  refine le_trans hn ?_
  rw [div_le_iff₀ (by norm_num : (0:ℝ) < 2 * 206), div_le_iff₀ wobble_pos]
  nlinarith [wobble_bounds.1]

theorem muon_relErr_bounds :
    0.00029348 < relErr muonPred muonRatioTarget ∧
      relErr muonPred muonRatioTarget < 0.00029397 := by
  obtain ⟨hwl, hwu⟩ := wobble_bounds
  have hw : (0:ℝ) < wobble := wobble_pos
  have hpl : 206.7075 < muonPred := by
    unfold muonPred
    rw [lt_div_iff₀ hw]
    nlinarith
  have hpu : muonPred < 206.7076 := by
    unfold muonPred
    rw [div_lt_iff₀ hw]
    nlinarith
  have habs : |muonPred - muonRatioTarget| = muonRatioTarget - muonPred := by
    rw [abs_of_neg (by unfold muonRatioTarget; linarith)]
    ring
  unfold relErr
  rw [habs, muonRatioTarget]
  constructor
  · rw [lt_div_iff₀ (by norm_num)]; linarith
  · rw [div_lt_iff₀ (by norm_num)]; linarith

/-- The muon fit does carry information: it beats the generic guarantee by a
factor between 10 and 11, i.e. by about one decimal digit. -/
theorem muon_fit_beats_generic_by_ten :
    relErr muonPred muonRatioTarget * 10 < 0.00297 ∧
      0.00297 < relErr muonPred muonRatioTarget * 11 := by
  obtain ⟨hl, hu⟩ := muon_relErr_bounds
  constructor <;> linarith

/-! ### The proton fit -/

/-- Every target `t ≥ 1836` is reproduced by `1836 + p·(L/12)` for some integer
`p`, to relative accuracy at most `1.5×10⁻⁶`. -/
theorem proton_generic_guarantee (t : ℝ) (h1 : 1836 ≤ t) :
    ∃ p : ℤ, |1836 + (p : ℝ) * (leak / 12) - t| / t ≤ 0.0000015 := by
  have hs : 0 < leak / 12 := by linarith [leak_pos]
  obtain ⟨p, hp⟩ := generic_relative_guarantee 1836 (leak / 12) 1836 t hs (by norm_num) h1
  refine ⟨p, le_trans hp ?_⟩
  rw [div_le_iff₀ (by norm_num)]
  linarith [leak_bounds.2]

theorem proton_relErr_bounds :
    0.0000003743 < relErr protonPred protonRatioTarget ∧
      relErr protonPred protonRatioTarget < 0.00000037436 := by
  obtain ⟨hl, hu⟩ := leak_bounds
  have habs : |protonPred - protonRatioTarget| = protonRatioTarget - protonPred := by
    rw [abs_of_neg (by unfold protonPred protonRatioTarget; linarith)]
    ring
  unfold relErr
  rw [habs, protonPred, protonRatioTarget]
  constructor
  · rw [lt_div_iff₀ (by norm_num)]; linarith
  · rw [div_lt_iff₀ (by norm_num)]; linarith

/-- The proton fit beats the generic guarantee by a factor between 4 and 5. -/
theorem proton_fit_beats_generic_by_four :
    relErr protonPred protonRatioTarget * 4 < 0.0000015 ∧
      0.0000015 < relErr protonPred protonRatioTarget * 5 := by
  obtain ⟨hl, hu⟩ := proton_relErr_bounds
  constructor <;> linarith

/-! ## 5. The ledger, in bits -/

/-- The surprisal, in bits, of an agreement `achieved` against the guarantee
`generic` that holds for every target of the same size.  Zero bits means the
fit is exactly as good as guessing. -/
noncomputable def bitScore (generic achieved : ℝ) : ℝ := Real.logb 2 (generic / achieved)

theorem logb_two_two : Real.logb 2 2 = 1 := Real.logb_self_eq_one (by norm_num)

theorem logb_two_four : Real.logb 2 4 = 2 := by
  rw [show (4 : ℝ) = 2 ^ (2 : ℕ) by norm_num, Real.logb_pow, logb_two_two]
  norm_num

theorem logb_two_eight : Real.logb 2 8 = 3 := by
  rw [show (8 : ℝ) = 2 ^ (3 : ℕ) by norm_num, Real.logb_pow, logb_two_two]
  norm_num

theorem logb_two_sixteen : Real.logb 2 16 = 4 := by
  rw [show (16 : ℝ) = 2 ^ (4 : ℕ) by norm_num, Real.logb_pow, logb_two_two]
  norm_num

theorem bitScore_lt_of_ratio_lt {g a c : ℝ} (hg : 0 < g) (ha : 0 < a) (h : g / a < c) :
    bitScore g a < Real.logb 2 c :=
  Real.logb_lt_logb (by norm_num) (div_pos hg ha) h

theorem bitScore_gt_of_ratio_gt {g a c : ℝ} (hc : 0 < c) (h : c < g / a) :
    Real.logb 2 c < bitScore g a :=
  Real.logb_lt_logb (by norm_num) hc h

theorem alpha_relErr_pos : 0 < relErr alphaBaseline alphaInvTarget := by
  linarith [alpha_relErr_bounds.1]

theorem muon_relErr_pos : 0 < relErr muonPred muonRatioTarget := by
  linarith [muon_relErr_bounds.1]

theorem proton_relErr_pos : 0 < relErr protonPred protonRatioTarget := by
  linarith [proton_relErr_bounds.1]

/-- **The fine-structure fit is worth less than one bit.**  It is strictly
better than the blind guarantee — but by less than a factor two, so it carries
under one binary digit of information. -/
theorem alpha_bits_lt_one :
    0 < bitScore 0.00023 (relErr alphaBaseline alphaInvTarget) ∧
      bitScore 0.00023 (relErr alphaBaseline alphaInvTarget) < 1 := by
  have hpos := alpha_relErr_pos
  obtain ⟨h1, h2⟩ := alpha_relErr_bounds
  constructor
  · have hgt : (1 : ℝ) < 0.00023 / relErr alphaBaseline alphaInvTarget := by
      rw [lt_div_iff₀ hpos]; linarith
    have := bitScore_gt_of_ratio_gt (c := 1) (by norm_num) hgt
    simpa using this
  · have hlt : 0.00023 / relErr alphaBaseline alphaInvTarget < 2 := by
      rw [div_lt_iff₀ hpos]; linarith
    have := bitScore_lt_of_ratio_lt (by norm_num) hpos hlt
    rwa [logb_two_two] at this

/-- **The muon fit is worth between three and four bits.** -/
theorem muon_bits_between_three_and_four :
    3 < bitScore 0.00297 (relErr muonPred muonRatioTarget) ∧
      bitScore 0.00297 (relErr muonPred muonRatioTarget) < 4 := by
  have hpos := muon_relErr_pos
  obtain ⟨h1, h2⟩ := muon_relErr_bounds
  constructor
  · have hgt : (8 : ℝ) < 0.00297 / relErr muonPred muonRatioTarget := by
      rw [lt_div_iff₀ hpos]; linarith
    have := bitScore_gt_of_ratio_gt (c := 8) (by norm_num) hgt
    rwa [logb_two_eight] at this
  · have hlt : 0.00297 / relErr muonPred muonRatioTarget < 16 := by
      rw [div_lt_iff₀ hpos]; linarith
    have := bitScore_lt_of_ratio_lt (by norm_num) hpos hlt
    rwa [logb_two_sixteen] at this

/-- **The proton fit is worth between two and three bits.** -/
theorem proton_bits_between_two_and_three :
    2 < bitScore 0.0000015 (relErr protonPred protonRatioTarget) ∧
      bitScore 0.0000015 (relErr protonPred protonRatioTarget) < 3 := by
  have hpos := proton_relErr_pos
  obtain ⟨h1, h2⟩ := proton_relErr_bounds
  constructor
  · have hgt : (4 : ℝ) < 0.0000015 / relErr protonPred protonRatioTarget := by
      rw [lt_div_iff₀ hpos]; linarith
    have := bitScore_gt_of_ratio_gt (c := 4) (by norm_num) hgt
    rwa [logb_two_four] at this
  · have hlt : 0.0000015 / relErr protonPred protonRatioTarget < 8 := by
      rw [div_lt_iff₀ hpos]; linarith
    have := bitScore_lt_of_ratio_lt (by norm_num) hpos hlt
    rwa [logb_two_eight] at this

/-- The capacity bound read in bits: `N` candidates matching within `δ` inside a
plausible range of width `R`. -/
noncomputable def capacityBits (N : ℕ) (δ R : ℝ) : ℝ := Real.logb 2 (R / (2 * N * δ))

/-- Doubling the number of candidate formulas costs exactly one bit. -/
theorem capacityBits_double {N : ℕ} {δ R : ℝ} (hN : 0 < N) (hδ : 0 < δ) (hR : 0 < R) :
    capacityBits (2 * N) δ R = capacityBits N δ R - 1 := by
  have hN' : (0:ℝ) < (N : ℝ) := by exact_mod_cast hN
  unfold capacityBits
  rw [show ((2 * N : ℕ) : ℝ) = 2 * (N : ℝ) by push_cast; ring]
  rw [show R / (2 * (2 * (N:ℝ)) * δ) = (R / (2 * (N:ℝ) * δ)) / 2 by field_simp]
  rw [Real.logb_div (by positivity) (by norm_num), Real.logb_self_eq_one (by norm_num)]

end GLM.FitCapacity
