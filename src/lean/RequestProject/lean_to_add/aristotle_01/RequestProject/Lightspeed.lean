import Mathlib
import RequestProject.Golay
import RequestProject.GolayWeights

/-!
# The substrate "speed of light": exact definitions and what they do (and do not) say

This file makes the calibration chain of `substrate_speed_of_light.md` completely
precise and machine-checks every numerical claim in it, together with the
structural facts that decide what the chain actually establishes.

The chain, as written in the source note, is

```
  190 kJ/mol per unit of geometric work        (empirical anchor, κ)
        ↓  divide by the Avogadro number
  E₁ = κ / N_A                = 3.16e-19 J     (energy of one work unit)
        ↓  Planck–Einstein relation
  τ  = h / E₁                 = 2.10 fs        ("tick duration")
        ↓  multiply by the tick budget of one cell, 24 bits + 3 TAX
  T_cell = 27 τ               = 5.67e-14 s
        ↓  multiply by c
  ℓ_cell = c · T_cell         = 17.0 μm        ("cell length")
```

Since the 2019 SI redefinition `c`, `h`, `N_A` and `Δν_Cs` are *exact rational
numbers*, so the whole chain is exact rational arithmetic and is developed here
over `ℚ`.

The two headline results are:

* `cellLength_div_cellDuration` / `substrate_c_is_circular` — the note's claim
  that "the speed of light is not an input constant, it is an output" is false
  as stated: `c` is used once (to convert the cell *duration* into a cell
  *length*) and is then recovered identically, for **every** value of the
  calibration constant `κ` and every tick budget.  The chain determines the cell
  length, not `c`.
* `speed_not_from_action_and_energy` — the structural reason: an action `h` and
  an energy `E` generate only the dimensions `Mᵃ⁺ᵇ L²ᵃ⁺²ᵇ T⁻ᵃ⁻²ᵇ`, which never
  contains `L T⁻¹`.  A calibration that supplies an energy scale can fix a time
  but never a velocity; an independent *length* is required, and that is exactly
  what the substrate does not supply (`speed_from_length_and_time`).

What survives is genuine and dimensionless: the propagation-speed / refractive
index law `n(T) = (24+T)/(24+T₀)` (`refIndex`), which contains no dimensionful
input at all, is falsifiable, and forces the reference TAX `T₀` to be the
*minimum* admissible TAX if the model is to be causal
(`signalSpeed_le_c_iff`).  Section 6 identifies that minimum on the Golay layer:
among nonzero codewords the symmetry tax is minimised exactly by the octads
(`octad_min_tax`), with value `8Y + 1 = 3.117…`, whose integer part is the `3`
of "24 bits + 3 TAX" (`octadTax_floor_three`).
-/

namespace UBPLightspeed

open scoped Real

/-! ## 1. The SI-defined constants

Since 20 May 2019 these are exact rationals by definition, so no measurement
uncertainty enters the chain. -/

/-- Speed of light in vacuum, m·s⁻¹ (exact, SI 2019). -/
def cSI : ℚ := 299792458

/-- Planck constant, J·s (exact, SI 2019). -/
def hSI : ℚ := 662607015 / 10 ^ 42

/-- Avogadro number, mol⁻¹ (exact, SI 2019). -/
def NA : ℚ := 602214076 * 10 ^ 15

/-- Caesium hyperfine transition frequency, Hz (exact, SI 2019). -/
def dnuCs : ℚ := 9192631770

theorem cSI_pos : 0 < cSI := by norm_num [cSI]

theorem hSI_pos : 0 < hSI := by norm_num [hSI]

theorem NA_pos : 0 < NA := by norm_num [NA]

/-- The molar Planck constant `h·N_A`, J·s·mol⁻¹ — exact, and the only
combination of `h` and `N_A` the chain ever uses. -/
def molarPlanck : ℚ := hSI * NA

theorem molarPlanck_eq : molarPlanck = 19951563564467157 / (5 * 10 ^ 25) := by
  norm_num [molarPlanck, hSI, NA]

theorem molarPlanck_pos : 0 < molarPlanck := by
  rw [molarPlanck_eq]; norm_num

/-! ## 2. The calibration chain

`κ` is the empirical anchor: joules **per mole** per unit of geometric work.
The note's value is `κ = 190 kJ/mol`. -/

/-- The empirical anchor of the note: 190 kJ/mol per unit of geometric work,
expressed in J·mol⁻¹. -/
def kappaBr : ℚ := 190000

/-- Energy of one unit of geometric work, in joules. -/
def workEnergy (kappa : ℚ) : ℚ := kappa / NA

/-- Tick duration, in seconds: the Planck–Einstein period of a quantum carrying
one unit of geometric work. -/
def tick (kappa : ℚ) : ℚ := hSI / workEnergy kappa

/-- Tick budget of one cell: 24 bit-shifts plus `T` ticks of TAX overhead. -/
def ticksPerCell (T : ℚ) : ℚ := 24 + T

/-- The vacuum/reference TAX used by the note: `24 + 3 = 27` ticks per cell. -/
def taxVacuum : ℚ := 3

/-- Duration of one cell crossing, in seconds. -/
def cellDuration (kappa T : ℚ) : ℚ := ticksPerCell T * tick kappa

/-- Cell length, in metres — obtained by multiplying the cell duration by `c`. -/
def cellLength (kappa T : ℚ) : ℚ := cSI * cellDuration kappa T

/-- Closed form of the tick duration: `τ = h·N_A / κ`. -/
theorem tick_eq (kappa : ℚ) (hk : kappa ≠ 0) : tick kappa = molarPlanck / kappa := by
  have hN : (NA : ℚ) ≠ 0 := ne_of_gt NA_pos
  simp only [tick, workEnergy, molarPlanck]
  field_simp

theorem tick_pos {kappa : ℚ} (hk : 0 < kappa) : 0 < tick kappa := by
  rw [tick_eq kappa (ne_of_gt hk)]
  exact div_pos molarPlanck_pos hk

/-- Closed form of the cell length: `ℓ = (24+T)·c·h·N_A / κ`. -/
theorem cellLength_eq (kappa T : ℚ) (hk : kappa ≠ 0) :
    cellLength kappa T = ticksPerCell T * cSI * molarPlanck / kappa := by
  rw [cellLength, cellDuration, tick_eq kappa hk]; ring

/-! ## 3. The numbers of the note, verified exactly -/

/-- `E₁ = κ/N_A = 3.1550…×10⁻¹⁹ J` (the note rounds this to `3.16×10⁻¹⁹ J`). -/
theorem workEnergy_value : workEnergy kappaBr = 19 / (602214076 * 10 ^ 11) := by
  norm_num [workEnergy, kappaBr, NA]

theorem workEnergy_bounds :
    3155024 / 10 ^ 25 < workEnergy kappaBr ∧ workEnergy kappaBr < 3155025 / 10 ^ 25 := by
  rw [workEnergy_value]; constructor <;> norm_num

/-- `τ = 2.100164…×10⁻¹⁵ s = 2.10 fs`, exactly as claimed. -/
theorem tick_value : tick kappaBr = 19951563564467157 / (95 * 10 ^ 29) := by
  rw [tick_eq kappaBr (by norm_num [kappaBr]), molarPlanck_eq]
  norm_num [kappaBr]

theorem tick_bounds :
    2100164 / 10 ^ 21 < tick kappaBr ∧ tick kappaBr < 2100165 / 10 ^ 21 := by
  rw [tick_value]; constructor <;> norm_num

/-- `T_cell = 27τ = 5.6704…×10⁻¹⁴ s`, exactly as claimed. -/
theorem cellDuration_bounds :
    5670444 / 10 ^ 20 < cellDuration kappaBr taxVacuum ∧
      cellDuration kappaBr taxVacuum < 5670445 / 10 ^ 20 := by
  have h : cellDuration kappaBr taxVacuum = 27 * tick kappaBr := by
    norm_num [cellDuration, ticksPerCell, taxVacuum]
  rw [h, tick_value]; constructor <;> norm_num

/-- `ℓ_cell = 1.69995…×10⁻⁵ m = 17.0 μm`, exactly as claimed (the note's `17.0`
uses `c ≈ 3×10⁸`; with the exact `c` the value is `16.9996 μm`). -/
theorem cellLength_bounds :
    1699956 / 10 ^ 11 < cellLength kappaBr taxVacuum ∧
      cellLength kappaBr taxVacuum < 1699957 / 10 ^ 11 := by
  have h : cellLength kappaBr taxVacuum = cSI * (27 * tick kappaBr) := by
    norm_num [cellLength, cellDuration, ticksPerCell, taxVacuum]
  rw [h, tick_value, cSI]; constructor <;> norm_num

/-! ## 4. What the chain really is

The composite of "divide by `N_A`", "apply `E = h/τ`" and "multiply by `c`" is
nothing but the Planck relation for a photon: the cell length is `24+T`
wavelengths of the quantum whose energy is one unit of geometric work. -/

/-- Wavelength of a photon carrying one unit of geometric work. -/
def workWavelength (kappa : ℚ) : ℚ := cSI * tick kappa

/-- **The chain in one line.**  The "cell length" is just `24+T` wavelengths of
the one-work-unit photon. -/
theorem cellLength_eq_wavelengths (kappa T : ℚ) :
    cellLength kappa T = ticksPerCell T * workWavelength kappa := by
  rw [cellLength, cellDuration, workWavelength]; ring

/-- With `κ = 190 kJ/mol` that photon is red visible light, `λ₁ = 629.6 nm`
(not, as the note says, "one molecular vibration quantum": molecular vibrations
lie between roughly `500` and `4400 cm⁻¹`, i.e. `2` to `20 μm`). -/
theorem workWavelength_bounds :
    6296 / 10 ^ 10 < workWavelength kappaBr ∧ workWavelength kappaBr < 6297 / 10 ^ 10 := by
  rw [workWavelength, tick_value, cSI]; constructor <;> norm_num

/-! ## 5. `c` is an input, not an output

The note asserts: *"The speed of light is not an input constant. It's an output
of how fast the substrate can cycle through 24-bit error correction."*

That is false as stated, and the following two theorems say exactly why. -/

/-- Dividing the cell length by the cell duration returns `c` identically — for
**every** calibration constant `κ` and **every** tick budget `T`.  A quantity
that comes back unchanged whatever the inputs were is not being predicted. -/
theorem cellLength_div_cellDuration (kappa T : ℚ)
    (h : cellDuration kappa T ≠ 0) : cellLength kappa T / cellDuration kappa T = cSI := by
  rw [cellLength]; field_simp

/-- The same statement in contrapositive form: the chain places no constraint
whatsoever on `c`.  Had the substrate's true speed of light been any other
value `c'`, running the identical chain with `c'` in place of `c` would return
`c'`.  Hence the chain cannot be used as evidence for the value of `c`. -/
theorem substrate_c_is_circular (c' kappa T : ℚ) (h : cellDuration kappa T ≠ 0) :
    (c' * cellDuration kappa T) / cellDuration kappa T = c' := by
  field_simp

/-- Rescaling the empirical anchor rescales both the tick and the cell length
inversely, so the anchor fixes the absolute scale and the substrate contributes
only the dimensionless tick budget. -/
theorem cellLength_scale (r kappa T : ℚ) (hr : r ≠ 0) (hk : kappa ≠ 0) :
    cellLength (r * kappa) T = cellLength kappa T / r := by
  rw [cellLength_eq _ _ (mul_ne_zero hr hk), cellLength_eq _ _ hk]
  field_simp

theorem tick_scale (r kappa : ℚ) (hr : r ≠ 0) (hk : kappa ≠ 0) :
    tick (r * kappa) = tick kappa / r := by
  rw [tick_eq _ (mul_ne_zero hr hk), tick_eq _ hk]; field_simp

/-! ### The dimensional obstruction

Dimensions are recorded as exponent triples `(mass, length, time)`. -/

/-- A physical dimension as an exponent vector `(M, L, T)`. -/
abbrev Dim := ℤ × ℤ × ℤ

def dMass : Dim := (1, 0, 0)
def dLength : Dim := (0, 1, 0)
def dTime : Dim := (0, 0, 1)
def dSpeed : Dim := (0, 1, -1)
def dEnergy : Dim := (1, 2, -2)
def dAction : Dim := (1, 2, -1)

/-- A product of powers of dimensionless quantities is dimensionless.  This is
the elementary form of Buckingham's Π-theorem obstruction: no amount of
dimensionless substrate structure can produce a dimensionful constant. -/
theorem dim_prod_of_dimensionless {n : ℕ} (d : Fin n → Dim) (hd : ∀ i, d i = 0)
    (k : Fin n → ℤ) : ∑ i, k i • d i = 0 := by
  simp [hd]

theorem dSpeed_ne_zero : dSpeed ≠ 0 := by decide

/-- **Nothing dimensionless gives `c`.** -/
theorem c_not_dimensionless {n : ℕ} (d : Fin n → Dim) (hd : ∀ i, d i = 0) (k : Fin n → ℤ) :
    ∑ i, k i • d i ≠ dSpeed := by
  rw [dim_prod_of_dimensionless d hd k]; exact fun h => dSpeed_ne_zero h.symm

/-- **The specific obstruction in this chain.**  The calibration supplies an
action (`h`) and an energy (`κ/N_A`).  No product of powers of an action and an
energy has the dimension of a speed, so the chain *cannot* produce `c`; it must
be given `c`. -/
theorem speed_not_from_action_and_energy :
    ¬ ∃ a b : ℤ, a • dAction + b • dEnergy = dSpeed := by
  rintro ⟨a, b, h⟩
  simp only [dAction, dEnergy, dSpeed, Prod.ext_iff, Prod.smul_mk, smul_eq_mul,
    Prod.mk_add_mk] at h
  obtain ⟨h1, h2, _⟩ := h
  omega

/-- An action and an energy do determine a *time*: that part of the chain
(`τ = h/E₁`) is sound. -/
theorem time_from_action_and_energy :
    (1 : ℤ) • dAction + (-1 : ℤ) • dEnergy = dTime := by decide

/-- An action and an energy also determine a *mass*, `E/c²`-style anchors aside. -/
theorem mass_not_from_action_and_energy :
    ¬ ∃ a b : ℤ, a • dAction + b • dEnergy = dMass := by
  rintro ⟨a, b, h⟩
  simp only [dAction, dEnergy, dMass, Prod.ext_iff, Prod.smul_mk, smul_eq_mul,
    Prod.mk_add_mk] at h
  obtain ⟨h1, h2, _⟩ := h
  omega

/-- **What would fix the gap.**  Add one independent *length* anchor and the
speed follows.  So the chain would become a genuine derivation of `c` exactly if
the substrate predicted the cell length `ℓ_cell` on its own, independently of
`c`; the note does not do this — it computes `ℓ_cell` *from* `c`. -/
theorem speed_from_length_and_time :
    (1 : ℤ) • dLength + (-1 : ℤ) • dTime = dSpeed := by decide

/-! ## 6. What does survive: the refractive-index law

`n(T) = (24+T)/(24+T₀)` is purely dimensionless, involves no empirical anchor,
and is falsifiable. -/

/-- Signal speed in a region of TAX `T`, given reference (vacuum) TAX `T₀`. -/
def signalSpeed (T₀ T : ℚ) : ℚ := cSI * ticksPerCell T₀ / ticksPerCell T

/-- Refractive index of a region of TAX `T`. -/
def refIndex (T₀ T : ℚ) : ℚ := ticksPerCell T / ticksPerCell T₀

theorem refIndex_self (T₀ : ℚ) (h : ticksPerCell T₀ ≠ 0) : refIndex T₀ T₀ = 1 := by
  rw [refIndex]; field_simp

/-- `n = c / v`. -/
theorem refIndex_mul_signalSpeed (T₀ T : ℚ) (h₀ : ticksPerCell T₀ ≠ 0)
    (hT : ticksPerCell T ≠ 0) : refIndex T₀ T * signalSpeed T₀ T = cSI := by
  rw [refIndex, signalSpeed]; field_simp

/-- **Causality forces the reference TAX to be the minimum TAX.**  With the
note's `T₀ = 3` the model is subluminal exactly on regions of TAX `≥ 3`; any
admissible state of TAX `< 3` would transmit signals faster than light. -/
theorem signalSpeed_le_c_iff (T₀ T : ℚ) (hT : 0 < ticksPerCell T) :
    signalSpeed T₀ T ≤ cSI ↔ T₀ ≤ T := by
  have hT' : (0 : ℚ) < 24 + T := hT
  rw [signalSpeed, ticksPerCell, ticksPerCell, div_le_iff₀ hT']
  constructor
  · intro h; nlinarith [cSI_pos]
  · intro h; nlinarith [cSI_pos]

/-- Vacuum, `T = T₀ = 3`: the model reproduces `v = c` — by construction. -/
theorem signalSpeed_vacuum : signalSpeed taxVacuum taxVacuum = cSI := by
  norm_num [signalSpeed, ticksPerCell, taxVacuum]

/-- The refractive index is strictly increasing in the TAX. -/
theorem refIndex_strictMono (T₀ : ℚ) (h₀ : 0 < ticksPerCell T₀) :
    StrictMono (refIndex T₀) := by
  intro a b hab
  rw [refIndex, refIndex, div_lt_div_iff_of_pos_right h₀]
  simpa [ticksPerCell] using hab

/-- The note's example: a region whose TAX rises from `3` to `8` has refractive
index `32/27 ≈ 1.185`. -/
theorem refIndex_tax_eight : refIndex 3 8 = 32 / 27 := by
  norm_num [refIndex, ticksPerCell]

/-- **A falsifiable ceiling.**  If the TAX of a region is bounded by `24` (the
largest Hamming weight available in 24 bits), the model caps the refractive
index at `48/27 = 16/9 ≈ 1.778`.  Diamond (`n = 2.417`) exceeds this, so either
the TAX budget must exceed `24` or the law is wrong for dense media. -/
theorem refIndex_le_of_tax_le (T : ℚ) (h : T ≤ 24) : refIndex 3 T ≤ 16 / 9 := by
  rw [refIndex, ticksPerCell, ticksPerCell, div_le_iff₀ (by norm_num : (0:ℚ) < 24 + 3)]
  linarith

/-! ## 7. The `3` in "24 bits + 3 TAX"

The substrate's symmetry tax of a 24-bit vector `v` is
`Tax(v) = HW(v)·Y + ‖v‖²/8` with `Y = 1/(π + 2/π)` (`ubp_unified_v5.py`,
`LeechEngine.calculate_symmetry_tax`).  On the Golay layer a codeword is a
`0/1`-vector, so `‖v‖² = HW(v)` and `Tax = HW·(Y + 1/8)`. -/

/-- The substrate's wobble constant `Y = 1/(π + 2/π)`. -/
noncomputable def Yc : ℝ := 1 / (Real.pi + 2 / Real.pi)

theorem Yc_pos : 0 < Yc := by
  have hpi : (0:ℝ) < Real.pi := Real.pi_pos
  have : (0:ℝ) < Real.pi + 2 / Real.pi := by positivity
  exact div_pos one_pos this

/-- `Y = π/(π²+2)`. -/
theorem Yc_eq : Yc = Real.pi / (Real.pi ^ 2 + 2) := by
  have hpi : (0:ℝ) < Real.pi := Real.pi_pos
  rw [Yc]; field_simp

theorem Yc_bounds : 0.264675 < Yc ∧ Yc < 0.264676 := by
  have h1 : (3.141592 : ℝ) < Real.pi := Real.pi_gt_d6
  have h2 : Real.pi < 3.141593 := Real.pi_lt_d6
  have hden : (0:ℝ) < Real.pi ^ 2 + 2 := by positivity
  rw [Yc_eq]
  constructor
  · rw [lt_div_iff₀ hden]; nlinarith
  · rw [div_lt_iff₀ hden]; nlinarith

/-- Symmetry tax of a Golay codeword of Hamming weight `w`
(`Tax = w·Y + w/8`, since `‖v‖² = w` for a `0/1` vector). -/
noncomputable def codewordTax (w : ℕ) : ℝ := (w : ℝ) * Yc + (w : ℝ) / 8

theorem codewordTax_strictMono : StrictMono codewordTax := by
  intro a b hab
  have h : (a : ℝ) < b := by exact_mod_cast hab
  have := Yc_pos
  rw [codewordTax, codewordTax]
  nlinarith

/-- **The octads minimise the symmetry tax among nonzero Golay codewords.**
This is the precise (and true) form of the "photon = minimum-TAX octad" claim:
it holds on the *code* layer. -/
theorem octad_min_tax {v : ℕ} (hv : LatticeShortcut.IsGolay v) (hne : v ≠ 0) :
    codewordTax 8 ≤ codewordTax (LatticeShortcut.pop v) := by
  have hw := LatticeShortcut.golay_weight_mem hv
  have h0 : LatticeShortcut.pop v ≠ 0 := by
    intro h
    exact hne ((LatticeShortcut.pop_eq_zero_iff v (LatticeShortcut.golay_lt hv)).1 h)
  rcases hw with h | h | h | h | h
  · exact absurd h h0
  · rw [h]
  · rw [h]; exact le_of_lt (codewordTax_strictMono (by norm_num))
  · rw [h]; exact le_of_lt (codewordTax_strictMono (by norm_num))
  · rw [h]; exact le_of_lt (codewordTax_strictMono (by norm_num))

/-- Equality holds only for the octads. -/
theorem octad_min_tax_strict {v : ℕ} (hv : LatticeShortcut.IsGolay v) (hne : v ≠ 0)
    (h8 : LatticeShortcut.pop v ≠ 8) : codewordTax 8 < codewordTax (LatticeShortcut.pop v) := by
  have hw := LatticeShortcut.golay_weight_mem hv
  have h0 : LatticeShortcut.pop v ≠ 0 := by
    intro h
    exact hne ((LatticeShortcut.pop_eq_zero_iff v (LatticeShortcut.golay_lt hv)).1 h)
  rcases hw with h | h | h | h | h
  · exact absurd h h0
  · exact absurd h h8
  · rw [h]; exact codewordTax_strictMono (by norm_num)
  · rw [h]; exact codewordTax_strictMono (by norm_num)
  · rw [h]; exact codewordTax_strictMono (by norm_num)

/-- The minimum nonzero codeword tax is `8Y + 1 = 3.1174…`. -/
theorem octadTax_eq : codewordTax 8 = 8 * Yc + 1 := by
  rw [codewordTax]; push_cast; ring

/-- **Where the `3` comes from.**  `⌊Tax(octad)⌋ = 3`: the "3 TAX overhead" of
the note is the integer part of the minimum nonzero symmetry tax. -/
theorem octadTax_floor_three : (3 : ℝ) < codewordTax 8 ∧ codewordTax 8 < 4 := by
  obtain ⟨hl, hu⟩ := Yc_bounds
  rw [octadTax_eq]
  constructor <;> nlinarith

/-- Using the exact tax instead of the rounded `3` changes the tick budget from
`27` to `25 + 8Y = 27.1174…`, i.e. the cell length by `+0.43 %`. -/
theorem exactTicksPerCell_bounds :
    (27.1174 : ℝ) < 24 + codewordTax 8 ∧ 24 + codewordTax 8 < 27.1175 := by
  obtain ⟨hl, hu⟩ := Yc_bounds
  rw [octadTax_eq]
  constructor <;> nlinarith

/-! ### Correction: the octad is *not* the global minimum-tax state

At the *Leech* layer the substrate's own tax audit ranks the three classes of
minimal vectors as `A < B < C`, and class `A` (shape `(∓4², 0²²)`, Hamming
weight 2) is strictly cheaper than the octad class `B` (shape `(∓2⁸, 0¹⁶)`).
So `LIGHTSPEED_STUDY_SYNTHESIS.md`'s claim P5, "photon = minimum-Tax octad", is
true only on the Golay layer, not among Leech minimal vectors. -/

/-- Tax of a Leech minimal vector of Hamming weight `w`: all minimal vectors
have `‖v‖² = 32`, so `Tax = w·Y + 4`. -/
noncomputable def minimalVectorTax (w : ℕ) : ℝ := (w : ℝ) * Yc + 4

theorem classA_tax_lt_octad_tax : minimalVectorTax 2 < minimalVectorTax 8 := by
  have := Yc_pos; rw [minimalVectorTax, minimalVectorTax]; push_cast; nlinarith

theorem minimalVectorTax_values :
    (4.5293 : ℝ) < minimalVectorTax 2 ∧ minimalVectorTax 2 < 4.5294 ∧
      (6.1174 : ℝ) < minimalVectorTax 8 ∧ minimalVectorTax 8 < 6.1175 := by
  obtain ⟨hl, hu⟩ := Yc_bounds
  refine ⟨?_, ?_, ?_, ?_⟩ <;> rw [minimalVectorTax] <;> push_cast <;> nlinarith

end UBPLightspeed
