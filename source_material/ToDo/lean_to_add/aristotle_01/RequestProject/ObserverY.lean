import Mathlib
import RequestProject.Golay
import RequestProject.GolayWeights
import RequestProject.Decoder
import RequestProject.Lightspeed

/-!
# The observer/read quantum `Y`: a stage-by-stage formalisation

This file is the machine-checked spine of the study
*"I am Y but I don't know what or where I am"* (E R A Craig).  Each section
corresponds to one stage of that document, and each stage is split into

* **definitions** — what the symbols mean, stated once and used unchanged;
* **stipulations** — choices the study makes; they are recorded as definitions,
  never proved, and flagged as stipulations in the prose report;
* **theorems** — the statements that actually follow, with proofs.

The companion prose document is `Y_OBSERVER_STUDY_REPORT.md`, which quotes each
Lean name next to the corresponding sentence of the original.

## The objects

For a pattern (the study's "disturbance") `v : Fin n → ℤ`:

```
  hw v      = #{i | v i ≠ 0}                     active distinctions
  normSq v  = ∑ i, (v i)^2                       geometric extent
  Y         = 1/(π + 2/π)                        read cost per distinction
  Q         = Y + 1/8                            activation quantum
  tax v     = hw v · Y + normSq v / 8            symmetry tax
  nrci v    = 10 / (10 + tax v)                  coherence after tax
```

`Y`, `tax` and `nrci` are exactly the quantities computed by
`ubp_unified_v5.py` (`UBPUltimateSubstrate.get_constants`,
`LeechLatticeEngine.calculate_symmetry_tax`, `LeechLatticeEngine.calculate_nrci`); the
coherence regimes are taken from §8 of the study.

## What the file establishes

* the vacuum is the *unique* state of perfect coherence (`tax_eq_zero_iff`,
  `nrci_eq_one_iff`);
* the read-cost operator `Y[Π] = 1/(Π + Δ/Π)` is bounded above by `1/(2√Δ)`
  and has no positive lower bound (`readCost_le_amgm`, `readCost_le_inv`), so
  `Y` is a *chosen* value at `Π = π`, not an extremal one (`Y_lt_amgm`);
* `Q` really is the activation quantum: it is the exact minimum tax of a
  nonzero pattern, attained precisely at a single `±1` coordinate
  (`Q_le_tax`, `tax_eq_Q_iff`);
* `TAX = HW · Q` holds *exactly* on patterns with entries in `{-1,0,1}` and
  nowhere else (`tax_eq_hw_mul_Q_iff`), which is the sharp form of §5;
* `NRCI` is a strictly decreasing function of the tax alone, with values in
  `(0,1]` (`coh_strictAnti`, `coh_pos`, `coh_le_one`), and the coherence budget
  is a pure scale (`nrciB_eq_coh`);
* the four regimes are exactly four tax bands (`regime_eq_onBit_iff`, …);
* on 24 coordinates only two of those bands are reachable by signed patterns
  (`signed24_regime`), and on the Golay layer the ladder collapses further:
  every nonzero codeword is `Coherent`, never `OnBit` (`golay_regime_coherent`),
  while at the Leech layer the deepest minimal-vector class is already
  `Transitional` (`minimalVector_classC_transitional`).
-/

namespace ObserverY

open Finset

/-! ## Stage V′ — the read-cost operator

The study writes the observer quantum as `Y[Π] = Reciprocal(Π + Δ/Π)`, with
loop-check `Π` and difference-state `Δ`.  We take that literally as a
two-parameter function and record what it does and does not determine. -/

/-- The read-cost operator `Y[Π] = 1/(Π + Δ/Π)` of §11, with difference-state
`d = Δ` and loop-check `t = Π`. -/
noncomputable def readCost (d t : ℝ) : ℝ := 1 / (t + d / t)

theorem readCost_eq (d t : ℝ) (ht : t ≠ 0) : readCost d t = t / (t ^ 2 + d) := by
  have h : t + d / t = (t ^ 2 + d) / t := by field_simp
  rw [readCost, h, one_div_div]

/-- **`Y` is the read cost at difference-state `Δ = 2` and loop-check `Π = π`.**
This is the substrate's constant `Y` verbatim. -/
noncomputable def Y : ℝ := readCost 2 Real.pi

theorem Y_eq_Yc : Y = UBPLightspeed.Yc := rfl

theorem Y_pos : 0 < Y := UBPLightspeed.Yc_pos

theorem Y_eq : Y = Real.pi / (Real.pi ^ 2 + 2) := UBPLightspeed.Yc_eq

/-- `Y = 0.2646754…`. -/
theorem Y_bounds : 0.264675 < Y ∧ Y < 0.264676 := UBPLightspeed.Yc_bounds

/-- **Upper bound on the read cost (AM–GM).**  For any positive difference
state `d` and any loop-check `t > 0`, `Y[Π] ≤ 1/(2√d)`, with equality only at
`Π = √d`.  The read cost can never exceed this, whatever loop is chosen. -/
theorem readCost_le_amgm {d t : ℝ} (hd : 0 < d) (ht : 0 < t) :
    readCost d t ≤ 1 / (2 * Real.sqrt d) := by
  have hsq : Real.sqrt d ^ 2 = d := Real.sq_sqrt hd.le
  have hs : 0 < Real.sqrt d := Real.sqrt_pos.mpr hd
  have hkey : 2 * Real.sqrt d ≤ t + d / t := by
    rw [← sub_nonneg]
    have hE : t + d / t - 2 * Real.sqrt d = (t ^ 2 - 2 * t * Real.sqrt d + d) / t := by
      field_simp; ring
    rw [hE]
    exact div_nonneg (by nlinarith [sq_nonneg (t - Real.sqrt d)]) ht.le
  exact one_div_le_one_div_of_le (by positivity) hkey

/-- **`π` is not the extremal loop-check.**  With `Δ = 2` the read cost is
maximised at `Π = √2`, where it equals `1/(2√2) = 0.3536…`; at `Π = π` it is
`0.2647…`.  So `Y` is not singled out by any extremal property of the
operator. -/
theorem Y_lt_amgm : Y < 1 / (2 * Real.sqrt 2) := by
  have hs : Real.sqrt 2 < 1.5 := by
    have h : Real.sqrt 2 < Real.sqrt (1.5 ^ 2) := by
      apply Real.sqrt_lt_sqrt (by norm_num); norm_num
    rwa [Real.sqrt_sq (by norm_num)] at h
  have hs0 : 0 < Real.sqrt 2 := Real.sqrt_pos.mpr (by norm_num)
  have hbig : (0.3 : ℝ) < 1 / (2 * Real.sqrt 2) := by
    rw [lt_div_iff₀ (by positivity)]; nlinarith
  linarith [Y_bounds.2]

/-- **The read cost has no positive lower bound.**  `Y[Π] ≤ 1/Π`, so letting the
loop-check grow drives the observer quantum to `0`.  The *value* of `Y` is
therefore fixed only by the stipulation `Π = π`; nothing in the operator selects
it. -/
theorem readCost_le_inv {d t : ℝ} (hd : 0 ≤ d) (ht : 0 < t) : readCost d t ≤ 1 / t := by
  refine one_div_le_one_div_of_le ht ?_
  have : 0 ≤ d / t := div_nonneg hd ht.le
  linarith

/-- The substrate's second constant `Y_CONST = 1/(Y⁻¹ + 2/Y⁻¹)`
(`ubp_unified_v5.py`, `get_constants`): the same operator applied a second time,
to `Y⁻¹` rather than to `Y`.  It is a distinct number from `Y` and is *not* the
constant used by the symmetry tax. -/
noncomputable def Yconst : ℝ := readCost 2 (Real.pi + 2 / Real.pi)

/-- `Y_CONST = 0.2321498…`, distinct from `Y = 0.2646754…`. -/
theorem Yconst_bounds : 0.232149 < Yconst ∧ Yconst < 0.232150 := by
  have h1 : (3.141592 : ℝ) < Real.pi := Real.pi_gt_d6
  have h2 : Real.pi < 3.141593 := Real.pi_lt_d6
  have hpi : (0 : ℝ) < Real.pi := Real.pi_pos
  have hu1 : (3.7782116 : ℝ) < Real.pi + 2 / Real.pi := by
    have : (0.6366196 : ℝ) < 2 / Real.pi := by rw [lt_div_iff₀ hpi]; nlinarith
    linarith
  have hu2 : Real.pi + 2 / Real.pi < 3.7782130 := by
    have : 2 / Real.pi < 0.6366200 := by rw [div_lt_iff₀ hpi]; nlinarith
    linarith
  have ht : Real.pi + 2 / Real.pi ≠ 0 := by positivity
  rw [Yconst, readCost_eq _ _ ht]
  have hden : (0 : ℝ) < (Real.pi + 2 / Real.pi) ^ 2 + 2 := by positivity
  constructor
  · rw [lt_div_iff₀ hden]; nlinarith
  · rw [div_lt_iff₀ hden]; nlinarith

/-! ## Stage IV — capacity, zones, and the activation quantum -/

/-- The zone-share `1/8` of §4: the cost of occupying a permitted zone.  It is a
stipulation of the study, matching the substrate's lattice scale factor `8`. -/
noncomputable def zoneShare : ℝ := 1 / 8

/-- The activation quantum `Q = Y + 1/8` (§4): read cost plus zone-entry cost. -/
noncomputable def Q : ℝ := Y + zoneShare

theorem Q_pos : 0 < Q := by
  have := Y_pos; rw [Q, zoneShare]; linarith

/-- `Q = 0.3896754…`. -/
theorem Q_bounds : 0.389675 < Q ∧ Q < 0.389676 := by
  obtain ⟨h1, h2⟩ := Y_bounds
  constructor <;> · rw [Q, zoneShare]; linarith

/-! ## Stages I–IV — patterns, weight and extent

A *pattern* (the study's disturbance `v`) is an integer vector on `n`
coordinates.  `hw` counts its active distinctions; `normSq` measures its
geometric extent. -/

variable {n : ℕ}

/-- Hamming weight: the number of active coordinates. -/
def hw (v : Fin n → ℤ) : ℕ := (univ.filter fun i => v i ≠ 0).card

/-- Squared norm: the geometric extent of the pattern. -/
def normSq (v : Fin n → ℤ) : ℤ := ∑ i, (v i) ^ 2

theorem hw_le_card (v : Fin n → ℤ) : hw v ≤ n := by
  simpa using (card_filter_le (univ : Finset (Fin n)) fun i => v i ≠ 0)

theorem hw_eq_sum (v : Fin n → ℤ) :
    (hw v : ℤ) = ∑ i, (if v i = 0 then (0 : ℤ) else 1) := by
  classical
  rw [hw, card_eq_sum_ones]
  push_cast
  rw [sum_filter]
  exact sum_congr rfl fun i _ => by by_cases h : v i = 0 <;> simp [h]

theorem normSq_nonneg (v : Fin n → ℤ) : 0 ≤ normSq v :=
  sum_nonneg fun _ _ => sq_nonneg _

theorem normSq_eq_zero_iff (v : Fin n → ℤ) : normSq v = 0 ↔ v = 0 := by
  constructor
  · intro h
    have hz := (sum_eq_zero_iff_of_nonneg fun j _ => sq_nonneg (v j)).1 h
    funext i
    have hi := hz i (mem_univ i)
    simpa [pow_eq_zero_iff] using hi
  · rintro rfl; simp [normSq]

theorem hw_eq_zero_iff (v : Fin n → ℤ) : hw v = 0 ↔ v = 0 := by
  constructor
  · intro h
    have h' : (univ.filter fun i => v i ≠ 0) = ∅ := card_eq_zero.1 h
    funext i
    by_contra hi
    have hmem : i ∈ (univ.filter fun i => v i ≠ 0) := mem_filter.2 ⟨mem_univ i, hi⟩
    simp [h'] at hmem
  · rintro rfl; simp [hw]

/-- **Each active coordinate contributes at least `1` to the extent.** -/
theorem hw_le_normSq (v : Fin n → ℤ) : (hw v : ℤ) ≤ normSq v := by
  classical
  calc (hw v : ℤ) = ∑ _i ∈ univ.filter (fun i => v i ≠ 0), (1 : ℤ) := by
        rw [hw, card_eq_sum_ones]; push_cast; ring
    _ ≤ ∑ i ∈ univ.filter (fun i => v i ≠ 0), (v i) ^ 2 := by
        refine sum_le_sum fun i hi => ?_
        have hne : v i ≠ 0 := (mem_filter.1 hi).2
        have h1 : 1 ≤ |v i| := Int.one_le_abs (by omega)
        nlinarith [sq_abs (v i), abs_nonneg (v i)]
    _ ≤ ∑ i, (v i) ^ 2 :=
        sum_le_sum_of_subset_of_nonneg (filter_subset _ _) (by intro i _ _; positivity)
    _ = normSq v := rfl

/-- A pattern is *signed* if every coordinate is `-1`, `0` or `1`.  Golay
codewords, read as `0/1` vectors, are signed. -/
def IsSigned (v : Fin n → ℤ) : Prop := ∀ i, v i = -1 ∨ v i = 0 ∨ v i = 1

/-- **Extent equals weight exactly on signed patterns.** -/
theorem normSq_eq_hw_iff (v : Fin n → ℤ) : normSq v = (hw v : ℤ) ↔ IsSigned v := by
  classical
  have hsum : normSq v - (hw v : ℤ)
      = ∑ i, ((v i) ^ 2 - (if v i = 0 then (0 : ℤ) else 1)) := by
    rw [normSq, hw_eq_sum, ← sum_sub_distrib]
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
    have hi := (sum_eq_zero_iff_of_nonneg hnn).1 hz i (mem_univ i)
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
    have hfin : normSq v - (hw v : ℤ) = 0 := by rw [hsum]; exact sum_eq_zero hz
    linarith

/-! ## Stage V — TAX

`TAX(v) = HW(v)·Y + ‖v‖²/8`: the read cost of the active distinctions plus the
cost of embodying them in the protected geometry. -/

/-- The symmetry tax of §5. -/
noncomputable def tax (v : Fin n → ℤ) : ℝ := (hw v : ℝ) * Y + (normSq v : ℝ) / 8

theorem tax_nonneg (v : Fin n → ℤ) : 0 ≤ tax v := by
  have h1 : (0 : ℝ) ≤ (hw v : ℝ) * Y := mul_nonneg (Nat.cast_nonneg _) Y_pos.le
  have h2 : (0 : ℝ) ≤ (normSq v : ℝ) := by exact_mod_cast normSq_nonneg v
  rw [tax]; linarith

/-- **Stage I and §7: the vacuum is the unique tax-free state.** -/
theorem tax_eq_zero_iff (v : Fin n → ℤ) : tax v = 0 ↔ v = 0 := by
  constructor
  · intro h
    have h1 : (0 : ℝ) ≤ (hw v : ℝ) * Y := mul_nonneg (Nat.cast_nonneg _) Y_pos.le
    have h2 : (0 : ℝ) ≤ (normSq v : ℝ) := by exact_mod_cast normSq_nonneg v
    have hns : (normSq v : ℝ) = 0 := by rw [tax] at h; linarith
    exact (normSq_eq_zero_iff v).1 (by exact_mod_cast hns)
  · rintro rfl; simp [tax, hw, normSq]

/-- **§5, sharp form: `TAX = HW · Q` holds exactly on signed patterns.**  The
study derives it "for a binary vector"; the converse is also true, so entries in
`{-1,0,1}` are not merely sufficient but necessary. -/
theorem tax_eq_hw_mul_Q_iff (v : Fin n → ℤ) : tax v = (hw v : ℝ) * Q ↔ IsSigned v := by
  rw [← normSq_eq_hw_iff]
  constructor
  · intro h
    have hr : (normSq v : ℝ) = (hw v : ℝ) := by rw [tax, Q, zoneShare] at h; linarith
    exact_mod_cast hr
  · intro h
    have hr : (normSq v : ℝ) = (hw v : ℝ) := by exact_mod_cast h
    rw [tax, Q, zoneShare, hr]; ring

theorem tax_signed (v : Fin n → ℤ) (h : IsSigned v) : tax v = (hw v : ℝ) * Q :=
  (tax_eq_hw_mul_Q_iff v).2 h

/-- **§4, justified: `Q` is the minimum cost of any nonzero pattern.** -/
theorem Q_le_tax {v : Fin n → ℤ} (hv : v ≠ 0) : Q ≤ tax v := by
  have h1 : 1 ≤ hw v := Nat.one_le_iff_ne_zero.2 fun h => hv ((hw_eq_zero_iff v).1 h)
  have h1' : (1 : ℝ) ≤ (hw v : ℝ) := by exact_mod_cast h1
  have h2 : (hw v : ℝ) ≤ (normSq v : ℝ) := by exact_mod_cast hw_le_normSq v
  have hY := Y_pos
  rw [tax, Q, zoneShare]
  nlinarith

/-- **Equality: the cheapest nonzero patterns are exactly the single `±1`
activations.**  The activation quantum is therefore realised, not merely a
lower bound. -/
theorem tax_eq_Q_iff (v : Fin n → ℤ) : tax v = Q ↔ hw v = 1 ∧ IsSigned v := by
  constructor
  · intro h
    have hv : v ≠ 0 := by
      rintro rfl
      rw [(tax_eq_zero_iff (0 : Fin n → ℤ)).2 rfl] at h
      exact absurd h.symm (ne_of_gt Q_pos)
    have h1 : 1 ≤ hw v := Nat.one_le_iff_ne_zero.2 fun h0 => hv ((hw_eq_zero_iff v).1 h0)
    have h2 : (hw v : ℝ) ≤ (normSq v : ℝ) := by exact_mod_cast hw_le_normSq v
    have hY := Y_pos
    have hhw : hw v = 1 := by
      by_contra hne
      have h2' : 2 ≤ hw v := by omega
      have h2'' : (2 : ℝ) ≤ (hw v : ℝ) := by exact_mod_cast h2'
      rw [tax, Q, zoneShare] at h
      nlinarith
    refine ⟨hhw, ?_⟩
    rw [← normSq_eq_hw_iff, hhw]
    have hr : (normSq v : ℝ) = 1 := by
      rw [tax, Q, zoneShare, hhw] at h; push_cast at h; linarith
    exact_mod_cast hr
  · rintro ⟨h1, h2⟩
    rw [tax_signed v h2, h1]; simp

/-! ## Stage VI — NRCI

`NRCI = B/(B + TAX)` with coherence budget `B = 10`.  We isolate the
one-variable function `coh` so that every statement about coherence is visibly a
statement about the tax alone. -/

/-- Coherence as a function of the tax, with the study's budget `B = 10`. -/
noncomputable def coh (t : ℝ) : ℝ := 10 / (10 + t)

/-- Coherence with an arbitrary budget `B` (the generalisation asked for in
§14 D). -/
noncomputable def nrciB (B t : ℝ) : ℝ := B / (B + t)

/-- `NRCI` of a pattern. -/
noncomputable def nrci (v : Fin n → ℤ) : ℝ := coh (tax v)

/-- **The coherence budget is a pure scale.**  Changing `B` only rescales the
tax axis; no statement about coherence depends on the value `10` except through
that scale.  This is the precise content of §14 D. -/
theorem nrciB_eq_coh {B t : ℝ} (hB : B ≠ 0) : nrciB B t = coh (10 * t / B) := by
  rw [nrciB, coh]; field_simp

theorem coh_zero : coh 0 = 1 := by norm_num [coh]

theorem coh_pos {t : ℝ} (ht : 0 ≤ t) : 0 < coh t := by
  rw [coh]; positivity

theorem coh_le_one {t : ℝ} (ht : 0 ≤ t) : coh t ≤ 1 := by
  rw [coh, div_le_one (by linarith)]; linarith

/-- Coherence is strictly decreasing in the tax. -/
theorem coh_strictAnti : StrictAntiOn coh (Set.Ici (0 : ℝ)) := by
  intro a ha b hb hab
  simp only [Set.mem_Ici] at ha hb
  rw [coh, coh, div_lt_div_iff₀ (by linarith) (by linarith)]
  linarith

/-- **§7: perfect coherence is exactly the vacuum.** -/
theorem nrci_eq_one_iff (v : Fin n → ℤ) : nrci v = 1 ↔ v = 0 := by
  have hpos : (0 : ℝ) < 10 + tax v := by have := tax_nonneg v; linarith
  rw [nrci, coh, div_eq_one_iff_eq (ne_of_gt hpos)]
  constructor
  · intro h; exact (tax_eq_zero_iff v).1 (by linarith)
  · rintro rfl; rw [(tax_eq_zero_iff (0 : Fin n → ℤ)).2 rfl]; ring

theorem nrci_pos (v : Fin n → ℤ) : 0 < nrci v := coh_pos (tax_nonneg v)

theorem nrci_le_one (v : Fin n → ℤ) : nrci v ≤ 1 := coh_le_one (tax_nonneg v)

/-- **"Information is coherence cost", made exact**: the coherence lost is the
tax measured on the same budget scale, and the two always sum to one. -/
theorem coh_add_info (t : ℝ) (ht : 0 ≤ t) : coh t + t / (10 + t) = 1 := by
  have h : (0 : ℝ) < 10 + t := by linarith
  rw [coh]; field_simp

/-! ## Stage VIII — the coherence regimes

The four regimes of §8 are thresholds on `NRCI`.  Since `NRCI` is a strictly
decreasing function of the tax, they are equivalently four bands of tax, and
that is the form in which they can be checked. -/

/-- The four coherence regimes of §8. -/
inductive Regime
  | onBit
  | coherent
  | transitional
  | subcoherent
  deriving DecidableEq, Repr

open Classical in
/-- The regime belonging to a coherence value, by the study's thresholds
`0.8 / 0.5 / 0.3`. -/
noncomputable def regimeOfCoh (x : ℝ) : Regime :=
  if 4 / 5 ≤ x then Regime.onBit
  else if 1 / 2 ≤ x then Regime.coherent
  else if 3 / 10 ≤ x then Regime.transitional
  else Regime.subcoherent

/-- The regime of a pattern of tax `t`, on the study's budget `B = 10`. -/
noncomputable def regime (t : ℝ) : Regime := regimeOfCoh (coh t)

/-- A coherence threshold `c` is a tax ceiling `10/c − 10`. -/
theorem coh_ge_iff {t c : ℝ} (ht : 0 ≤ t) (hc : 0 < c) :
    c ≤ coh t ↔ t ≤ 10 / c - 10 := by
  have h : (0 : ℝ) < 10 + t := by linarith
  rw [coh, le_div_iff₀ h, le_sub_iff_add_le, ← le_div_iff₀' hc]
  constructor <;> intro h' <;> nlinarith

private theorem coh_ge_four_fifths {t : ℝ} (ht : 0 ≤ t) :
    (4 / 5 : ℝ) ≤ coh t ↔ t ≤ 5 / 2 := by
  have h := coh_ge_iff (c := 4 / 5) ht (by norm_num); norm_num at h ⊢; exact h

private theorem coh_ge_half {t : ℝ} (ht : 0 ≤ t) : (1 / 2 : ℝ) ≤ coh t ↔ t ≤ 10 := by
  have h := coh_ge_iff (c := 1 / 2) ht (by norm_num); norm_num at h ⊢; exact h

private theorem coh_ge_three_tenths {t : ℝ} (ht : 0 ≤ t) :
    (3 / 10 : ℝ) ≤ coh t ↔ t ≤ 70 / 3 := by
  have h := coh_ge_iff (c := 3 / 10) ht (by norm_num); norm_num at h ⊢; exact h

/-- `OnBit` ⟺ `TAX ≤ 5/2`. -/
theorem regime_eq_onBit_iff {t : ℝ} (ht : 0 ≤ t) : regime t = Regime.onBit ↔ t ≤ 5 / 2 := by
  have hA := coh_ge_four_fifths ht
  rw [regime, regimeOfCoh]
  split_ifs with h1 h2 h3
  · exact ⟨fun _ => hA.1 h1, fun _ => rfl⟩
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hA.2 hc) h1⟩
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hA.2 hc) h1⟩
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hA.2 hc) h1⟩

/-- `Coherent` ⟺ `5/2 < TAX ≤ 10`. -/
theorem regime_eq_coherent_iff {t : ℝ} (ht : 0 ≤ t) :
    regime t = Regime.coherent ↔ 5 / 2 < t ∧ t ≤ 10 := by
  have hA := coh_ge_four_fifths ht
  have hB := coh_ge_half ht
  rw [regime, regimeOfCoh]
  split_ifs with h1 h2 h3
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hA.1 h1) (by linarith [hc.1])⟩
  · exact ⟨fun _ => ⟨not_le.mp fun hc => h1 (hA.2 hc), hB.1 h2⟩, fun _ => rfl⟩
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hB.2 hc.2) h2⟩
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hB.2 hc.2) h2⟩

/-- `Transitional` ⟺ `10 < TAX ≤ 70/3`. -/
theorem regime_eq_transitional_iff {t : ℝ} (ht : 0 ≤ t) :
    regime t = Regime.transitional ↔ 10 < t ∧ t ≤ 70 / 3 := by
  have hA := coh_ge_four_fifths ht
  have hB := coh_ge_half ht
  have hC := coh_ge_three_tenths ht
  rw [regime, regimeOfCoh]
  split_ifs with h1 h2 h3
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hA.1 h1) (by linarith [hc.1])⟩
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hB.1 h2) (by linarith [hc.1])⟩
  · exact ⟨fun _ => ⟨not_le.mp fun hc => h2 (hB.2 hc), hC.1 h3⟩, fun _ => rfl⟩
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hC.2 hc.2) h3⟩

/-- `Subcoherent` ⟺ `70/3 < TAX`. -/
theorem regime_eq_subcoherent_iff {t : ℝ} (ht : 0 ≤ t) :
    regime t = Regime.subcoherent ↔ 70 / 3 < t := by
  have hA := coh_ge_four_fifths ht
  have hB := coh_ge_half ht
  have hC := coh_ge_three_tenths ht
  rw [regime, regimeOfCoh]
  split_ifs with h1 h2 h3
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hA.1 h1) (by linarith)⟩
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hB.1 h2) (by linarith)⟩
  · exact ⟨fun h => absurd h (by decide), fun hc => absurd (hC.1 h3) (by linarith)⟩
  · exact ⟨fun _ => not_le.mp fun hc => h3 (hC.2 hc), fun _ => rfl⟩

/-! ## The regime ladder on 24 coordinates

The study's instrument lives on 24 coordinates.  There the four-regime ladder is
far coarser than it looks: on signed patterns only two of the four regimes are
reachable at all. -/

/-- On signed 24-coordinate patterns the tax is at most `24·Q = 9.3522…`. -/
theorem signed24_tax_le {v : Fin 24 → ℤ} (h : IsSigned v) : tax v ≤ 24 * Q := by
  have hle : (hw v : ℝ) ≤ 24 := by exact_mod_cast hw_le_card v
  rw [tax_signed v h]
  nlinarith [Q_pos]

/-- **Only two of the four regimes are reachable.**  Every signed
24-coordinate pattern is `OnBit` or `Coherent`; `Transitional` and
`Subcoherent` cannot occur, because the largest possible tax is `9.35 < 10`. -/
theorem signed24_regime {v : Fin 24 → ℤ} (h : IsSigned v) :
    regime (tax v) = Regime.onBit ∨ regime (tax v) = Regime.coherent := by
  have hb := Q_bounds.2
  have hle : tax v ≤ 24 * Q := signed24_tax_le h
  have h10 : tax v ≤ 10 := by nlinarith
  have ht := tax_nonneg v
  by_cases hc : tax v ≤ 5 / 2
  · exact Or.inl ((regime_eq_onBit_iff ht).2 hc)
  · exact Or.inr ((regime_eq_coherent_iff ht).2 ⟨not_le.1 hc, h10⟩)

/-- **`OnBit` is exactly "at most six active distinctions".** -/
theorem signed_onBit_iff {v : Fin n → ℤ} (h : IsSigned v) :
    regime (tax v) = Regime.onBit ↔ hw v ≤ 6 := by
  obtain ⟨hq1, hq2⟩ := Q_bounds
  rw [regime_eq_onBit_iff (tax_nonneg v), tax_signed v h]
  constructor
  · intro hle
    by_contra hc
    have h7 : (7 : ℝ) ≤ (hw v : ℝ) := by exact_mod_cast Nat.succ_le_of_lt (not_le.1 hc)
    nlinarith
  · intro hle
    have h6 : (hw v : ℝ) ≤ 6 := by exact_mod_cast hle
    nlinarith [Q_pos]

/-! ## Stage VII — the Golay layer

A Golay codeword, read as a `0/1` vector, is signed with
`HW ∈ {0, 8, 12, 16, 24}`, so its tax is `HW·Q`
(`UBPLightspeed.codewordTax`). -/

theorem codewordTax_eq (w : ℕ) : UBPLightspeed.codewordTax w = (w : ℝ) * Q := by
  rw [UBPLightspeed.codewordTax, Q, zoneShare, Y_eq_Yc]; ring

theorem codewordTax_nonneg (w : ℕ) : 0 ≤ UBPLightspeed.codewordTax w := by
  rw [codewordTax_eq]
  exact mul_nonneg (Nat.cast_nonneg _) Q_pos.le

/-- **Every nonzero Golay codeword is `Coherent` — never `OnBit`.**  The code's
minimum distance `8` exceeds the `OnBit` ceiling of six active distinctions, and
its maximum weight `24` stays below the `Coherent` floor.  So on the Golay layer
the four-regime ladder degenerates: the vacuum is the only `OnBit` state and
every protected distinction sits in one single regime. -/
theorem golay_regime_coherent {c : ℕ} (hc : LatticeShortcut.IsGolay c) (hne : c ≠ 0) :
    regime (UBPLightspeed.codewordTax (LatticeShortcut.pop c)) = Regime.coherent := by
  obtain ⟨hq1, hq2⟩ := Q_bounds
  have h0 : LatticeShortcut.pop c ≠ 0 := fun h =>
    hne ((LatticeShortcut.pop_eq_zero_iff c (LatticeShortcut.golay_lt hc)).1 h)
  have key : ∀ w : ℕ, w = 8 ∨ w = 12 ∨ w = 16 ∨ w = 24 →
      regime (UBPLightspeed.codewordTax w) = Regime.coherent := by
    intro w hw'
    refine (regime_eq_coherent_iff (codewordTax_nonneg w)).2 ⟨?_, ?_⟩ <;>
      rw [codewordTax_eq] <;> rcases hw' with h | h | h | h <;> rw [h] <;> norm_num <;> nlinarith
  rcases LatticeShortcut.golay_weight_mem hc with h | h | h | h | h
  · exact absurd h h0
  · exact key _ (Or.inl h)
  · exact key _ (Or.inr (Or.inl h))
  · exact key _ (Or.inr (Or.inr (Or.inl h)))
  · exact key _ (Or.inr (Or.inr (Or.inr h)))

/-- The coherence of an octad: `NRCI = 10/(10 + 8Y + 1) = 0.76234…`. -/
theorem octad_nrci_bounds :
    0.76234 < coh (UBPLightspeed.codewordTax 8) ∧
      coh (UBPLightspeed.codewordTax 8) < 0.76235 := by
  obtain ⟨h1, h2⟩ := Q_bounds
  have hval : UBPLightspeed.codewordTax 8 = 8 * Q := by rw [codewordTax_eq]; norm_num
  have hpos : (0 : ℝ) < 10 + UBPLightspeed.codewordTax 8 := by rw [hval]; nlinarith
  rw [coh]
  constructor
  · rw [lt_div_iff₀ hpos, hval]; nlinarith
  · rw [div_lt_iff₀ hpos, hval]; nlinarith

/-! ## Stages V–VII joined — the loop, the syndrome, and the price of protection

The study's Stage V says a not-quite-closed loop leaves a *gap*, and that the
gap is the history of the measurement; Stage VII says the Golay structure turns
lawful history into *protected* distinction.  Both have an exact counterpart in
the code: the loop-check is the syndrome map `syn`, and "the loop closes" is
literally "the pattern is a codeword". -/

/-- **Stage V, exactly: the loop closes iff the distinction is lawful.** -/
theorem loop_closes_iff_lawful {v : ℕ} :
    LatticeShortcut.syn v = 0 ↔ LatticeShortcut.IsGolay v :=
  LatticeShortcut.syn_eq_zero_iff

/-- **History is additive.**  The gap of a superposition of disturbances is the
superposition of their gaps, so the loop-check is a homomorphism, not an ad hoc
record. -/
theorem history_additive (a b : ℕ) :
    LatticeShortcut.syn (a ^^^ b) = LatticeShortcut.syn a ^^^ LatticeShortcut.syn b :=
  LatticeShortcut.syn_xor a b

/-- **Two patterns carry the same history exactly when they differ by a lawful
distinction.**  This is what makes "gap = history" a *complete* record: the
syndrome forgets precisely the protected content and nothing else. -/
theorem same_history_iff (a b : ℕ) :
    LatticeShortcut.syn a = LatticeShortcut.syn b ↔ LatticeShortcut.IsGolay (a ^^^ b) := by
  rw [← LatticeShortcut.syn_eq_zero_iff, history_additive, Nat.xor_eq_zero_iff]

/-- **The price of protection is exactly eight activation quanta.**  An
unprotected distinction can be activated for `Q` (`tax_eq_Q_iff`), but the
cheapest nonzero *protected* distinction is an octad, costing `8Q = 3.1174…`.
Protection multiplies the minimum cost of being read by eight. -/
theorem protection_costs_eight_quanta {c : ℕ} (hc : LatticeShortcut.IsGolay c) (hne : c ≠ 0) :
    8 * Q ≤ UBPLightspeed.codewordTax (LatticeShortcut.pop c) := by
  have h := UBPLightspeed.octad_min_tax hc hne
  rwa [codewordTax_eq, Nat.cast_ofNat] at h

/-- **TAX is blind to lawfulness.**  On signed patterns the tax depends only on
the number of active distinctions, so a Golay codeword and a random error
pattern of the same weight are charged identically.  This is the exact content
of the study's own refinement note §14 C. -/
theorem tax_eq_of_hw_eq {v w : Fin n → ℤ} (hv : IsSigned v) (hw' : IsSigned w)
    (h : hw v = hw w) : tax v = tax w := by
  rw [tax_signed v hv, tax_signed w hw', h]

/-! ## The Leech layer

All Leech minimal vectors have `‖v‖² = 32` in the substrate's integer
representation, so their tax is `HW·Y + 4` (`UBPLightspeed.minimalVectorTax`).
The three shape classes have `HW = 2, 8, 24`, and — unlike on the Golay layer —
the regime ladder does separate them. -/

theorem minimalVectorTax_eq (w : ℕ) : UBPLightspeed.minimalVectorTax w = (w : ℝ) * Y + 4 := by
  rw [UBPLightspeed.minimalVectorTax, Y_eq_Yc]

theorem minimalVectorTax_nonneg (w : ℕ) : 0 ≤ UBPLightspeed.minimalVectorTax w := by
  rw [minimalVectorTax_eq]
  have h : (0 : ℝ) ≤ (w : ℝ) * Y := mul_nonneg (Nat.cast_nonneg _) Y_pos.le
  linarith

/-- Classes A (`HW = 2`) and B (`HW = 8`, the octad class) are `Coherent`. -/
theorem minimalVector_classAB_coherent :
    regime (UBPLightspeed.minimalVectorTax 2) = Regime.coherent ∧
      regime (UBPLightspeed.minimalVectorTax 8) = Regime.coherent := by
  obtain ⟨h1, h2⟩ := Y_bounds
  constructor <;>
    refine (regime_eq_coherent_iff (minimalVectorTax_nonneg _)).2 ⟨?_, ?_⟩ <;>
      rw [minimalVectorTax_eq] <;> norm_num <;> nlinarith

/-- **Class C (`HW = 24`, shape `(∓3, ±1²³)`) is already `Transitional`.**  Its
tax is `24Y + 4 = 10.352… > 10`, so `NRCI = 0.4913… < 0.5`.  The deepest shell
of the Leech lattice therefore falls out of the `Coherent` band, even though
every one of its vectors is a minimal (kissing-sphere) vector. -/
theorem minimalVector_classC_transitional :
    regime (UBPLightspeed.minimalVectorTax 24) = Regime.transitional := by
  obtain ⟨h1, h2⟩ := Y_bounds
  refine (regime_eq_transitional_iff (minimalVectorTax_nonneg _)).2 ⟨?_, ?_⟩ <;>
    rw [minimalVectorTax_eq] <;> norm_num <;> nlinarith

theorem minimalVector_classC_nrci :
    0.4913 < coh (UBPLightspeed.minimalVectorTax 24) ∧
      coh (UBPLightspeed.minimalVectorTax 24) < 0.4914 := by
  obtain ⟨h1, h2⟩ := Y_bounds
  have hval : UBPLightspeed.minimalVectorTax 24 = 24 * Y + 4 := by
    rw [minimalVectorTax_eq]; norm_num
  have hpos : (0 : ℝ) < 10 + UBPLightspeed.minimalVectorTax 24 := by rw [hval]; nlinarith
  rw [coh]
  constructor
  · rw [lt_div_iff₀ hpos, hval]; nlinarith
  · rw [div_lt_iff₀ hpos, hval]; nlinarith

/-! ## Refinement §14 A — a MOG-aware tax

The study asks for a tax that distinguishes lawful patterns from random ones of
the same weight, by adding a *syndrome penalty* and a *closure credit*.
`tax_eq_of_hw_eq` shows some such term is unavoidable if that distinction is
wanted.  There is a canonical choice: charge the pattern for the correction it
needs, i.e. for the weight of the coset leader of its syndrome.  The resulting
penalty vanishes exactly on lawful patterns and is bounded by `4Q`, because the
covering radius of the code is `4`. -/

/-- The tax of a `0/1` bit-pattern held in a 24-bit word: `HW · Q`. -/
noncomputable def bitTax (v : ℕ) : ℝ := (LatticeShortcut.pop v : ℝ) * Q

/-- The syndrome penalty: the activation cost of the correction the pattern
needs, `HW(leader(syn v)) · Q`. -/
noncomputable def syndromePenalty (v : ℕ) : ℝ :=
  (LatticeShortcut.pop (LatticeShortcut.leader (LatticeShortcut.syn v)) : ℝ) * Q

/-- The MOG-aware tax proposed in §14 A, with the penalty made explicit. -/
noncomputable def taxMOG (v : ℕ) : ℝ := bitTax v + syndromePenalty v

/-- The coset leader of a syndrome is zero exactly for the zero syndrome:  a
word of weight `≤ 4` with vanishing syndrome is a codeword, and the only
codeword of weight `< 8` is `0`. -/
theorem leader_eq_zero_iff {s : ℕ} (h : s < 4096) : LatticeShortcut.leader s = 0 ↔ s = 0 := by
  constructor
  · intro hl
    have hs := (LatticeShortcut.leader_props h).2.1
    rw [hl] at hs
    simpa [LatticeShortcut.syn, LatticeShortcut.cw_zero] using hs.symm
  · rintro rfl
    have hp := LatticeShortcut.leader_props (s := 0) (by norm_num)
    have hg : LatticeShortcut.IsGolay (LatticeShortcut.leader 0) :=
      LatticeShortcut.syn_eq_zero_iff.1 hp.2.1
    have hw := LatticeShortcut.golay_weight_mem hg
    have h4 := hp.1
    exact (LatticeShortcut.pop_eq_zero_iff _ hp.2.2).1 (by omega)

/-- **The penalty vanishes exactly on lawful patterns.** -/
theorem syndromePenalty_eq_zero_iff {v : ℕ} (h : v < 2 ^ 24) :
    syndromePenalty v = 0 ↔ LatticeShortcut.IsGolay v := by
  have hlt := LatticeShortcut.syn_lt h
  rw [syndromePenalty, mul_eq_zero, or_iff_left (ne_of_gt Q_pos)]
  rw [show ((LatticeShortcut.pop (LatticeShortcut.leader (LatticeShortcut.syn v)) : ℝ) = 0)
      ↔ LatticeShortcut.pop (LatticeShortcut.leader (LatticeShortcut.syn v)) = 0 from
    Nat.cast_eq_zero]
  rw [LatticeShortcut.pop_eq_zero_iff _ (LatticeShortcut.leader_props hlt).2.2,
    leader_eq_zero_iff hlt, LatticeShortcut.syn_eq_zero_iff]

/-- **The penalty is bounded by four activation quanta**, the covering radius of
the code measured in activation cost. -/
theorem syndromePenalty_le {v : ℕ} (h : v < 2 ^ 24) : syndromePenalty v ≤ 4 * Q := by
  have key : ∀ k : ℕ, k ≤ 4 → (k : ℝ) * Q ≤ 4 * Q := by
    intro k hk
    have hk' : (k : ℝ) ≤ 4 := by exact_mod_cast hk
    nlinarith [Q_pos]
  exact key _ (LatticeShortcut.leader_props (LatticeShortcut.syn_lt h)).1

/-- **The MOG-aware tax charges extra exactly for unlawful patterns**, and never
by more than `4Q`.  This is refinement §14 A carried out. -/
theorem taxMOG_eq_bitTax_iff {v : ℕ} (h : v < 2 ^ 24) :
    taxMOG v = bitTax v ↔ LatticeShortcut.IsGolay v := by
  rw [taxMOG]
  constructor
  · intro hh; exact (syndromePenalty_eq_zero_iff h).1 (by linarith)
  · intro hg; rw [(syndromePenalty_eq_zero_iff h).2 hg]; ring

theorem taxMOG_le {v : ℕ} (h : v < 2 ^ 24) : taxMOG v ≤ bitTax v + 4 * Q := by
  have := syndromePenalty_le h
  rw [taxMOG]; linarith

/-! ## A calibrated budget: making the regime ladder informative

The previous two sections show that on the study's own budget `B = 10` the
four-regime ladder cannot separate the code: every nonzero codeword is
`Coherent`.  The cause is a scale mismatch, and `nrciB_eq_coh` says the scale is
the only thing the budget controls.  Choosing the budget to be the cheapest
protected distinction, `B = 8Q` (the octad tax), repairs this exactly. -/

/-- With the calibrated budget `B = 8Q`, the coherence of a codeword of weight
`w` is the scale-free ratio `8/(8+w)`: the read cost drops out entirely and only
the weight relative to the minimum distance remains. -/
theorem nrciB_calibrated (w : ℕ) : nrciB (8 * Q) ((w : ℝ) * Q) = 8 / (8 + w) := by
  have hQ : Q ≠ 0 := ne_of_gt Q_pos
  have hw : (0 : ℝ) < 8 + (w : ℝ) := by positivity
  rw [nrciB]
  field_simp

/-- **The calibrated budget separates all four regimes.**  On `B = 8Q` the five
Golay weight classes land in four distinct regimes — vacuum `OnBit`, octads
`Coherent`, weights `12` and `16` `Transitional`, the all-ones word
`Subcoherent` — instead of collapsing into one.  This is a change of scale only:
no definition in the study is altered. -/
theorem calibrated_regime_separates :
    regimeOfCoh (nrciB (8 * Q) ((0 : ℕ) * Q)) = Regime.onBit ∧
      regimeOfCoh (nrciB (8 * Q) ((8 : ℕ) * Q)) = Regime.coherent ∧
        regimeOfCoh (nrciB (8 * Q) ((12 : ℕ) * Q)) = Regime.transitional ∧
          regimeOfCoh (nrciB (8 * Q) ((16 : ℕ) * Q)) = Regime.transitional ∧
            regimeOfCoh (nrciB (8 * Q) ((24 : ℕ) * Q)) = Regime.subcoherent := by
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> rw [nrciB_calibrated] <;> norm_num [regimeOfCoh]

end ObserverY
