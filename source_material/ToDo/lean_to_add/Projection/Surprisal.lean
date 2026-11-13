import FirstPrinciples.FitCapacity

set_option autoImplicit false

/-!
# Module 6 — the bit-score ledger

The parent sub-study proved that the framework's numerical fits are *shapes*
that would match almost any target: a formula "fixed integer plus a multiple of a
small constant" is an arithmetic progression, and a progression of spacing `s`
lands within `s/2` of every real number.  That turns "is this agreement
impressive?" into a measurement rather than an argument, and this module records
the measurement in **bits**.

## Definitions

* `bitScore generic achieved = log₂(generic / achieved)` — how many binary digits
  of agreement a fit buys over the guarantee that holds for *every* target of the
  same size.  Zero bits means the fit is exactly as good as guessing.
* `capacityBits N δ R = log₂(R / (2Nδ))` — the same quantity computed from the
  capacity bound: `N` candidate predictions, each matching within `δ`, cover a
  set of measure at most `2Nδ` inside a plausible range of width `R`
  (`UBPFirstPrinciples.fit_capacity`).

## The ledger (P6-1 … P6-3)

| fit | generic guarantee | achieved | bits |
|---|---|---|---|
| `α⁻¹ = 137 + L` | `2.3×10⁻⁴` | `1.9624×10⁻⁴` | `0 < b < 1` (`alpha_bits_lt_one`) |
| `m_μ/m_e = 169/w` | `2.97×10⁻³` | `2.9376×10⁻⁴` | `3 < b < 4` (`muon_bits_between_three_and_four`) |
| `m_p/m_e = 1836 + 2Lσ` | `1.5×10⁻⁶` | `3.7434×10⁻⁷` | `2 < b < 3` (`proton_bits_between_two_and_three`) |

So the fine-structure agreement is worth **less than one bit** — it is not
evidence; the muon fit is worth between three and four bits; the proton fit
between two and three.  A ranked development queue follows directly, and that is
the intended use: the ledger is a triage tool, not a verdict.

`capacityBits_pos` is the general statement behind the table: a match is
informative exactly to the extent that the candidate family covers little of the
plausible range.  `capacityBits_antitone_in_card` records the obvious but
important corollary — doubling the number of candidate formulas costs exactly one
bit of surprisal.
-/

namespace UBPProjection

open Real UBP UBPFirstPrinciples

/-! ## 1. The score -/

/-- The surprisal, in bits, of an agreement `achieved` against the guarantee
`generic` that holds for every target of the same size. -/
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
  Real.logb_lt_logb (by norm_num) (by positivity) h

theorem bitScore_gt_of_ratio_gt {g a c : ℝ} (hc : 0 < c) (h : c < g / a) :
    Real.logb 2 c < bitScore g a :=
  Real.logb_lt_logb (by norm_num) hc h

/-! ## 2. The three entries of the ledger -/

theorem alpha_relErr_pos : 0 < relErr alphaBaseline alphaInvTarget :=
  alphaBaseline_relErr.pos (by norm_num)

theorem muon_relErr_pos : 0 < relErr muonPred muonRatioTarget :=
  muonPred_relErr.pos (by norm_num)

theorem proton_relErr_pos : 0 < relErr protonPred protonRatioTarget :=
  protonPred_relErr.pos (by norm_num)

/-- **P6-1.**  *The fine-structure fit is worth less than one bit.*  It is
strictly better than the blind guarantee — but by less than a factor 2, so it
carries under one binary digit of information. -/
theorem alpha_bits_lt_one :
    0 < bitScore 0.00023 (relErr alphaBaseline alphaInvTarget) ∧
      bitScore 0.00023 (relErr alphaBaseline alphaInvTarget) < 1 := by
  have hpos := alpha_relErr_pos
  have h1 := alphaBaseline_relErr.1
  have h2 := alphaBaseline_relErr.2
  norm_num at h1 h2
  constructor
  · have hgt : (1 : ℝ) < 0.00023 / relErr alphaBaseline alphaInvTarget := by
      rw [lt_div_iff₀ hpos]
      linarith
    have := bitScore_gt_of_ratio_gt (c := 1) (by norm_num) hgt
    simpa using this
  · have hlt : 0.00023 / relErr alphaBaseline alphaInvTarget < 2 := by
      rw [div_lt_iff₀ hpos]
      linarith
    have := bitScore_lt_of_ratio_lt (by norm_num) hpos hlt
    rwa [logb_two_two] at this

/-- **P6-2.**  *The muon fit is worth between three and four bits.* -/
theorem muon_bits_between_three_and_four :
    3 < bitScore 0.00297 (relErr muonPred muonRatioTarget) ∧
      bitScore 0.00297 (relErr muonPred muonRatioTarget) < 4 := by
  have hpos := muon_relErr_pos
  have h1 := muonPred_relErr.1
  have h2 := muonPred_relErr.2
  norm_num at h1 h2
  constructor
  · have hgt : (8 : ℝ) < 0.00297 / relErr muonPred muonRatioTarget := by
      rw [lt_div_iff₀ hpos]
      linarith
    have := bitScore_gt_of_ratio_gt (c := 8) (by norm_num) hgt
    rwa [logb_two_eight] at this
  · have hlt : 0.00297 / relErr muonPred muonRatioTarget < 16 := by
      rw [div_lt_iff₀ hpos]
      linarith
    have := bitScore_lt_of_ratio_lt (by norm_num) hpos hlt
    rwa [logb_two_sixteen] at this

/-- **P6-3.**  *The proton fit is worth between two and three bits.* -/
theorem proton_bits_between_two_and_three :
    2 < bitScore 0.0000015 (relErr protonPred protonRatioTarget) ∧
      bitScore 0.0000015 (relErr protonPred protonRatioTarget) < 3 := by
  have hpos := proton_relErr_pos
  have h1 := protonPred_relErr.1
  have h2 := protonPred_relErr.2
  norm_num at h1 h2
  constructor
  · have hgt : (4 : ℝ) < 0.0000015 / relErr protonPred protonRatioTarget := by
      rw [lt_div_iff₀ hpos]
      linarith
    have := bitScore_gt_of_ratio_gt (c := 4) (by norm_num) hgt
    rwa [logb_two_four] at this
  · have hlt : 0.0000015 / relErr protonPred protonRatioTarget < 8 := by
      rw [div_lt_iff₀ hpos]
      linarith
    have := bitScore_lt_of_ratio_lt (by norm_num) hpos hlt
    rwa [logb_two_eight] at this

/-- The ledger, as one statement: three fits, three bit-scores, ranked. -/
theorem bit_ledger :
    bitScore 0.00023 (relErr alphaBaseline alphaInvTarget) < 1 ∧
      2 < bitScore 0.0000015 (relErr protonPred protonRatioTarget) ∧
      bitScore 0.0000015 (relErr protonPred protonRatioTarget) < 3 ∧
      3 < bitScore 0.00297 (relErr muonPred muonRatioTarget) ∧
      bitScore 0.00297 (relErr muonPred muonRatioTarget) < 4 :=
  ⟨alpha_bits_lt_one.2, proton_bits_between_two_and_three.1,
   proton_bits_between_two_and_three.2, muon_bits_between_three_and_four.1,
   muon_bits_between_three_and_four.2⟩

/-! ## 3. The capacity form of the score -/

/-- The surprisal available from a family of `N` candidate predictions, each
matching within `δ`, inside a plausible range of width `R`. -/
noncomputable def capacityBits (N : ℕ) (δ R : ℝ) : ℝ := Real.logb 2 (R / (2 * N * δ))

/-- **P6-4.**  A match is informative exactly when the candidate family covers
little of the plausible range: the surprisal is positive iff `2Nδ < R`.  The
measure statement behind it is `UBPFirstPrinciples.fit_capacity`. -/
theorem capacityBits_pos {N : ℕ} {δ R : ℝ} (hN : 0 < N) (hδ : 0 < δ)
    (h : 2 * N * δ < R) : 0 < capacityBits N δ R := by
  have hden : (0 : ℝ) < 2 * N * δ := by positivity
  have hgt : (1 : ℝ) < R / (2 * N * δ) := by
    rw [lt_div_iff₀ hden]
    linarith
  have := Real.logb_lt_logb (b := 2) (by norm_num) (by norm_num) hgt
  simpa [capacityBits] using this

/-- **P6-5.**  Doubling the number of candidate formulas costs exactly one bit. -/
theorem capacityBits_double {N : ℕ} {δ R : ℝ} (hN : 0 < N) (hδ : 0 < δ) (hR : 0 < R) :
    capacityBits (2 * N) δ R = capacityBits N δ R - 1 := by
  have hN' : (0 : ℝ) < N := by exact_mod_cast hN
  have hden : (0 : ℝ) < 2 * N * δ := by positivity
  have hrw : R / (2 * ((2 * N : ℕ) : ℝ) * δ) = (R / (2 * N * δ)) / 2 := by
    push_cast
    field_simp
  rw [capacityBits, capacityBits, hrw, Real.logb_div (by positivity) (by norm_num), logb_two_two]

end UBPProjection
