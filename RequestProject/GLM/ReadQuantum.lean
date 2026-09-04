/-
# The read quantum as an *operator*, and what it does and does not fix

**Retrieved from the archive.**  `source_material/GLM-main.zip/light/aristotle_01`
carries a Lean development of the observer study *"I am Y but I don't know what
or where I am"* (`ObserverY.lean`, 62 theorems), which the first salvage pass
read only for its speed-of-light chain (`Calibration.lean`).  Read again, the
part of it that is *not* already in `Constants.lean` is a sharp statement about
where the substrate's constants come from, and it is retrieved here.

`Constants.lean` takes `Y = 1/(π + 2/π)` as given.  The study derives it from a
two-parameter **read-cost operator**

    readCost Δ Π = 1 / (Π + Δ/Π)

with difference-state `Δ` and loop-check `Π`, and the substrate's `Y` is
`readCost 2 π`.  Once the operator is written down, the question "why `π`?" can
be answered, and the answer is negative:

* `readCost_le_amgm` — for every `Π > 0` the cost is at most `1/(2√Δ)`, the
  AM–GM bound, attained exactly at `Π = √Δ` (`readCost_eq_amgm_iff`);
* `Y_lt_amgm` — at `Δ = 2` the maximiser is `√2`, not `π`, and `Y = 0.2647…`
  is strictly below the maximum `1/(2√2) = 0.3536…`;
* `readCost_le_inv` and `readCost_no_pos_lower_bound` — the cost can be driven
  below any positive number by taking the loop-check large.

So `Y` is **a stipulation, not an extremum**: nothing in the operator selects
`Π = π`.  That is the same kind of correction the first pass recorded for the
speed of light, one level further down, and it is the honest statement of what
the substrate's headline constant is.

The rest of the file is the exact arithmetic of the tax that the study proves
and `Constants.lean` does not have:

* `IsSigned` and `normSq_eq_hw_iff` — geometric extent equals active weight
  exactly on patterns with entries in `{-1, 0, 1}`;
* `tax_eq_hw_mul_Q_iff` — the substrate's rule `TAX = HW·Q` is *exactly* the
  signed case, so the converse holds too: it is not merely sufficient that the
  carrier be binary;
* `Q_le_tax` and `tax_eq_Q_iff` — `Q` is the exact minimum tax of a nonzero
  pattern, attained precisely at a single `±1` activation, which is what makes
  it an activation quantum rather than a fitted constant;
* `tax_eq_of_hw_eq` — the tax is blind to lawfulness: a codeword and an error
  pattern of the same weight are charged identically;
* `signed24_tax_le`, `signed24_regime`, `signed_onBit_iff` — on the 24
  coordinates the machine actually runs on, only two of the four coherence
  regimes are reachable by signed patterns, and `OnBit` is exactly "at most six
  active distinctions";
* `regime_coherent_of_hw_ge_eight` — every nonzero Golay codeword, read as a
  `0/1` vector, is `Coherent` and never `OnBit`, because its weight is at least
  8: protection costs eight activation quanta;
* `nrci_add_info` — the coherence and the tax measured on the budget scale sum
  to one.

The archive's file is `light/aristotle_01/RequestProject/ObserverY.lean`; the
statements are retrieved here against the current `GLM.Constants` definitions.
-/
import Mathlib
import RequestProject.GLM.Constants
import RequestProject.GLM.Calibration

namespace GLM.ReadQuantum

open Finset

/-! ## 1. The read-cost operator -/

/-- The read-cost operator `Y[Π] = 1/(Π + Δ/Π)`, with difference-state `d = Δ`
and loop-check `t = Π`. -/
noncomputable def readCost (d t : ℝ) : ℝ := 1 / (t + d / t)

theorem readCost_eq (d t : ℝ) (ht : t ≠ 0) : readCost d t = t / (t ^ 2 + d) := by
  have h : t + d / t = (t ^ 2 + d) / t := by field_simp
  rw [readCost, h, one_div_div]

/-- **The substrate's `Y` is the read cost at `Δ = 2`, `Π = π`.** -/
theorem Y_eq_readCost : GLM.Y = readCost 2 Real.pi := rfl

/-- **Upper bound on the read cost (AM–GM).**  For any positive difference state
`d` and any loop-check `t > 0`, the cost is at most `1/(2√d)`. -/
theorem readCost_le_amgm {d t : ℝ} (hd : 0 < d) (ht : 0 < t) :
    readCost d t ≤ 1 / (2 * Real.sqrt d) := by
  have hs : 0 < Real.sqrt d := Real.sqrt_pos.mpr hd
  have hsq : Real.sqrt d ^ 2 = d := Real.sq_sqrt hd.le
  have hkey : 2 * Real.sqrt d ≤ t + d / t := by
    rw [← sub_nonneg]
    have hE : t + d / t - 2 * Real.sqrt d = (t ^ 2 - 2 * t * Real.sqrt d + d) / t := by
      field_simp; ring
    rw [hE]
    exact div_nonneg (by nlinarith [sq_nonneg (t - Real.sqrt d)]) ht.le
  exact one_div_le_one_div_of_le (by positivity) hkey

/-- The bound is attained exactly at the geometric mean `t = √d`. -/
theorem readCost_eq_amgm_iff {d t : ℝ} (hd : 0 < d) (ht : 0 < t) :
    readCost d t = 1 / (2 * Real.sqrt d) ↔ t = Real.sqrt d := by
  have hs : 0 < Real.sqrt d := Real.sqrt_pos.mpr hd
  have hsq : Real.sqrt d ^ 2 = d := Real.sq_sqrt hd.le
  have hpos : 0 < t + d / t := by positivity
  constructor
  · intro h
    have hpos2 : (0 : ℝ) < 2 * Real.sqrt d := by positivity
    have hden : t + d / t = 2 * Real.sqrt d := by
      have h2 : (1 : ℝ) / (t + d / t) = 1 / (2 * Real.sqrt d) := h
      rw [div_eq_div_iff hpos.ne' hpos2.ne'] at h2
      linarith
    have h3 : d / t = 2 * Real.sqrt d - t := by linarith
    rw [div_eq_iff ht.ne'] at h3
    have hfac : (t - Real.sqrt d) ^ 2 = 0 := by nlinarith
    have : t - Real.sqrt d = 0 := by
      exact pow_eq_zero_iff (n := 2) (by norm_num) |>.mp hfac
    linarith
  · rintro rfl
    rw [readCost]
    congr 1
    field_simp
    nlinarith

/-- **`π` is not the extremal loop-check.**  With `Δ = 2` the read cost is
maximised at `Π = √2`, where it is `1/(2√2) = 0.3536…`; at `Π = π` it is
`0.2647…`.  `Y` is not singled out by any extremal property of the operator. -/
theorem Y_lt_amgm : GLM.Y < 1 / (2 * Real.sqrt 2) := by
  have hs : Real.sqrt 2 < 1.5 := by
    have h : Real.sqrt 2 < Real.sqrt (1.5 ^ 2) := by
      apply Real.sqrt_lt_sqrt (by norm_num); norm_num
    rwa [Real.sqrt_sq (by norm_num)] at h
  have hs0 : 0 < Real.sqrt 2 := Real.sqrt_pos.mpr (by norm_num)
  have hbig : (0.3 : ℝ) < 1 / (2 * Real.sqrt 2) := by
    rw [lt_div_iff₀ (by positivity)]; nlinarith
  linarith [GLM.Calibration.Y_bounds.2]

/-- **The read cost has no positive lower bound**: `Y[Π] ≤ 1/Π`. -/
theorem readCost_le_inv {d t : ℝ} (hd : 0 ≤ d) (ht : 0 < t) : readCost d t ≤ 1 / t := by
  refine one_div_le_one_div_of_le ht ?_
  have : 0 ≤ d / t := div_nonneg hd ht.le
  linarith

/-- Made explicit: for every positive `ε` some loop-check reads more cheaply
than `ε`.  The *value* of `Y` is fixed by the stipulation `Π = π` alone. -/
theorem readCost_no_pos_lower_bound {d : ℝ} (hd : 0 ≤ d) {eps : ℝ} (heps : 0 < eps) :
    ∃ t : ℝ, 0 < t ∧ readCost d t < eps := by
  refine ⟨2 / eps, by positivity, ?_⟩
  have ht : 0 < 2 / eps := by positivity
  have h1 : readCost d (2 / eps) ≤ 1 / (2 / eps) := readCost_le_inv hd ht
  have h2 : 1 / (2 / eps) = eps / 2 := by field_simp
  rw [h2] at h1
  linarith

/-! ## 2. Signed patterns -/

variable {n : ℕ}

/-- A pattern is *signed* when every coordinate is `-1`, `0` or `1`.  Golay
codewords, read as `0/1` vectors, are signed. -/
def IsSigned (v : Fin n → ℤ) : Prop := ∀ i, v i = -1 ∨ v i = 0 ∨ v i = 1

theorem hammingWeight_le_card (v : Fin n → ℤ) : GLM.hammingWeight v ≤ n := by
  simpa [GLM.hammingWeight] using
    (Finset.card_filter_le (univ : Finset (Fin n)) fun i => v i ≠ 0)

theorem hammingWeight_eq_sum (v : Fin n → ℤ) :
    (GLM.hammingWeight v : ℤ) = ∑ i, (if v i = 0 then (0 : ℤ) else 1) := by
  rw [GLM.hammingWeight, Finset.card_filter]
  push_cast
  refine Finset.sum_congr rfl fun i _ => ?_
  by_cases h : v i = 0 <;> simp [h]

theorem hammingWeight_le_normSq (v : Fin n → ℤ) :
    (GLM.hammingWeight v : ℤ) ≤ GLM.normSq v := by
  rw [hammingWeight_eq_sum, GLM.normSq]
  refine Finset.sum_le_sum fun i _ => ?_
  by_cases h : v i = 0
  · simp [h]
  · have h1 : 1 ≤ |v i| := Int.one_le_abs (by omega)
    simp only [h, if_false]
    nlinarith [sq_abs (v i), abs_nonneg (v i)]

/-- **Extent equals weight exactly on signed patterns.** -/
theorem normSq_eq_hammingWeight_iff (v : Fin n → ℤ) :
    GLM.normSq v = (GLM.hammingWeight v : ℤ) ↔ IsSigned v := by
  have hsum : GLM.normSq v - (GLM.hammingWeight v : ℤ)
      = ∑ i, ((v i) ^ 2 - (if v i = 0 then (0 : ℤ) else 1)) := by
    rw [GLM.normSq, hammingWeight_eq_sum, ← Finset.sum_sub_distrib]
  have hnn : ∀ i ∈ (univ : Finset (Fin n)),
      0 ≤ (v i) ^ 2 - (if v i = 0 then (0 : ℤ) else 1) := by
    intro i _
    by_cases h : v i = 0
    · simp [h]
    · have h1 : 1 ≤ |v i| := Int.one_le_abs (by omega)
      simp only [h, if_false]
      nlinarith [sq_abs (v i), abs_nonneg (v i)]
  constructor
  · intro h i
    have hz : ∑ i, ((v i) ^ 2 - (if v i = 0 then (0 : ℤ) else 1)) = 0 := by
      rw [← hsum, h]; ring
    have hi := (Finset.sum_eq_zero_iff_of_nonneg hnn).1 hz i (mem_univ i)
    by_cases h0 : v i = 0
    · exact Or.inr (Or.inl h0)
    · simp only [h0, if_false, sub_eq_zero] at hi
      have hfac : (v i - 1) * (v i + 1) = 0 := by nlinarith
      rcases mul_eq_zero.1 hfac with h1 | h1
      · exact Or.inr (Or.inr (by omega))
      · exact Or.inl (by omega)
  · intro h
    have hz : ∀ i ∈ (univ : Finset (Fin n)),
        (v i) ^ 2 - (if v i = 0 then (0 : ℤ) else 1) = 0 := by
      intro i _
      rcases h i with h1 | h1 | h1 <;> simp [h1]
    have hfin : GLM.normSq v - (GLM.hammingWeight v : ℤ) = 0 := by
      rw [hsum]; exact Finset.sum_eq_zero hz
    linarith

/-! ## 3. The activation quantum -/

/-- **The substrate's rule `TAX = HW·Q` is exactly the signed case.**  The
converse holds: entries in `{-1,0,1}` are necessary, not merely sufficient. -/
theorem tax_eq_hammingWeight_mul_Q_iff (v : Fin n → ℤ) :
    GLM.tax v = (GLM.hammingWeight v : ℝ) * GLM.Q ↔ IsSigned v := by
  rw [← normSq_eq_hammingWeight_iff]
  constructor
  · intro h
    have hr : (GLM.normSq v : ℝ) = (GLM.hammingWeight v : ℝ) := by
      rw [GLM.tax, GLM.Q] at h; linarith
    exact_mod_cast hr
  · intro h
    have hr : (GLM.normSq v : ℝ) = (GLM.hammingWeight v : ℝ) := by exact_mod_cast h
    rw [GLM.tax, GLM.Q, hr]; ring

theorem tax_signed {v : Fin n → ℤ} (h : IsSigned v) :
    GLM.tax v = (GLM.hammingWeight v : ℝ) * GLM.Q :=
  (tax_eq_hammingWeight_mul_Q_iff v).2 h

/-- **`Q` is the minimum tax of any nonzero pattern.** -/
theorem Q_le_tax {v : Fin n → ℤ} (hv : v ≠ 0) : GLM.Q ≤ GLM.tax v := by
  have h1 : 1 ≤ GLM.hammingWeight v :=
    Nat.one_le_iff_ne_zero.2 fun h => hv (GLM.hammingWeight_eq_zero_iff.1 h)
  have h1' : (1 : ℝ) ≤ (GLM.hammingWeight v : ℝ) := by exact_mod_cast h1
  have h2 : ((GLM.hammingWeight v : ℤ) : ℝ) ≤ (GLM.normSq v : ℝ) := by
    exact_mod_cast hammingWeight_le_normSq v
  have hY := GLM.Y_pos
  rw [GLM.tax, GLM.Q]
  push_cast at h2 ⊢
  nlinarith

/-- **The cheapest nonzero patterns are exactly the single `±1` activations.** -/
theorem tax_eq_Q_iff (v : Fin n → ℤ) :
    GLM.tax v = GLM.Q ↔ GLM.hammingWeight v = 1 ∧ IsSigned v := by
  constructor
  · intro h
    have hv : v ≠ 0 := by
      rintro rfl
      rw [GLM.tax_eq_zero_iff.2 rfl] at h
      exact absurd h.symm (ne_of_gt GLM.Q_pos)
    have h1 : 1 ≤ GLM.hammingWeight v :=
      Nat.one_le_iff_ne_zero.2 fun h0 => hv (GLM.hammingWeight_eq_zero_iff.1 h0)
    have h2 : ((GLM.hammingWeight v : ℤ) : ℝ) ≤ (GLM.normSq v : ℝ) := by
      exact_mod_cast hammingWeight_le_normSq v
    push_cast at h2
    have hY := GLM.Y_pos
    have hhw : GLM.hammingWeight v = 1 := by
      by_contra hne
      have h2' : 2 ≤ GLM.hammingWeight v := by omega
      have h2'' : (2 : ℝ) ≤ (GLM.hammingWeight v : ℝ) := by exact_mod_cast h2'
      rw [GLM.tax, GLM.Q] at h
      nlinarith
    refine ⟨hhw, ?_⟩
    rw [← normSq_eq_hammingWeight_iff, hhw]
    have hr : (GLM.normSq v : ℝ) = 1 := by
      rw [GLM.tax, GLM.Q, hhw] at h; push_cast at h; linarith
    exact_mod_cast hr
  · rintro ⟨h1, h2⟩
    rw [tax_signed h2, h1]; simp

/-- **The tax is blind to lawfulness.**  On signed patterns it depends only on
the number of active distinctions, so a codeword and an error pattern of the
same weight are charged identically. -/
theorem tax_eq_of_hammingWeight_eq {v w : Fin n → ℤ} (hv : IsSigned v) (hw : IsSigned w)
    (h : GLM.hammingWeight v = GLM.hammingWeight w) : GLM.tax v = GLM.tax w := by
  rw [tax_signed hv, tax_signed hw, h]

/-! ## 4. Coherence -/

/-- **"Information is coherence cost", made exact**: the coherence and the tax
measured on the budget scale always sum to one. -/
theorem nrci_add_info (v : Fin n → ℤ) :
    GLM.nrci v + GLM.tax v / (GLM.budget + GLM.tax v) = 1 := by
  have h := GLM.budget_add_tax_pos v
  rw [GLM.nrci]
  field_simp

/-! ## 5. The 24 coordinates the machine runs on -/

/-- On signed 24-coordinate patterns the tax is at most `24·Q = 9.3522…`. -/
theorem signed24_tax_le {v : Fin 24 → ℤ} (h : IsSigned v) : GLM.tax v ≤ 24 * GLM.Q := by
  have hle : (GLM.hammingWeight v : ℝ) ≤ 24 := by
    exact_mod_cast hammingWeight_le_card v
  rw [tax_signed h]
  nlinarith [GLM.Q_pos]

/-- `Q = 0.389675…`. -/
theorem Q_bounds : 0.389675 < GLM.Q ∧ GLM.Q < 0.389676 := by
  obtain ⟨h1, h2⟩ := GLM.Calibration.Y_bounds
  constructor <;> · rw [GLM.Q]; linarith

/-- **Only two of the four regimes are reachable.**  Every signed
24-coordinate pattern is `OnBit` or `Coherent`: the largest possible tax is
`24·Q = 9.35 < 10`, so `Transitional` and `Subcoherent` cannot occur. -/
theorem signed24_regime {v : Fin 24 → ℤ} (h : IsSigned v) :
    GLM.regime v = GLM.CoherenceRegime.onBit ∨
      GLM.regime v = GLM.CoherenceRegime.coherent := by
  have hb := Q_bounds.2
  have hle : GLM.tax v ≤ 24 * GLM.Q := signed24_tax_le h
  have h10 : GLM.tax v ≤ 10 := by nlinarith
  by_cases hc : GLM.tax v ≤ 5 / 2
  · exact Or.inl (GLM.regime_onBit_iff.2 hc)
  · exact Or.inr (GLM.regime_coherent_iff.2 ⟨not_le.1 hc, h10⟩)

/-- **`OnBit` is exactly "at most six active distinctions".** -/
theorem signed_onBit_iff {v : Fin n → ℤ} (h : IsSigned v) :
    GLM.regime v = GLM.CoherenceRegime.onBit ↔ GLM.hammingWeight v ≤ 6 := by
  obtain ⟨hq1, hq2⟩ := Q_bounds
  rw [GLM.regime_onBit_iff, tax_signed h]
  constructor
  · intro hle
    by_contra hc
    have h7 : (7 : ℝ) ≤ (GLM.hammingWeight v : ℝ) := by
      exact_mod_cast Nat.succ_le_of_lt (not_le.1 hc)
    nlinarith
  · intro hle
    have h6 : (GLM.hammingWeight v : ℝ) ≤ 6 := by exact_mod_cast hle
    nlinarith [GLM.Q_pos]

/-- **Protection costs eight activation quanta.**  A nonzero Golay codeword,
read as a signed `0/1` vector on 24 coordinates, has weight at least 8 and so is
`Coherent` — never `OnBit`, the regime a single activation enjoys. -/
theorem regime_coherent_of_hammingWeight_ge_eight {v : Fin 24 → ℤ} (h : IsSigned v)
    (h8 : 8 ≤ GLM.hammingWeight v) : GLM.regime v = GLM.CoherenceRegime.coherent := by
  obtain ⟨hq1, hq2⟩ := Q_bounds
  have h8' : (8 : ℝ) ≤ (GLM.hammingWeight v : ℝ) := by exact_mod_cast h8
  have hle : GLM.tax v ≤ 24 * GLM.Q := signed24_tax_le h
  have hge : 8 * GLM.Q ≤ GLM.tax v := by rw [tax_signed h]; nlinarith [GLM.Q_pos]
  refine GLM.regime_coherent_iff.2 ⟨by nlinarith, by nlinarith⟩

end GLM.ReadQuantum
