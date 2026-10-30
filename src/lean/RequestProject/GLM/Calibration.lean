/-
# The EM scale calibration, and what it does and does not determine

The GLM archive contains an electromagnetic calibration chain — `light/`, in two
rounds — that tries to obtain a *length* for the substrate's cell, and then
reads the speed of light off it:

```
  κ = 190 kJ/mol per unit of geometric work    (the empirical anchor)
        ↓  divide by the Avogadro number
  E₁ = κ / N_A                                 (energy of one work unit)
        ↓  Planck–Einstein
  τ  = h / E₁                                  (tick duration)
        ↓  multiply by the tick budget, 24 bits + 3 TAX
  T_cell = 27 τ
        ↓  multiply by c
  ℓ_cell = c · T_cell
```

Since the 2019 SI redefinition `c`, `h` and `N_A` are exact rationals, so the
whole chain is exact rational arithmetic and is developed here over `ℚ` — no
float appears, in keeping with directive D7.

The chain's own headline was *"the speed of light is not an input constant, it
is an output of how fast the substrate cycles through 24-bit error
correction"*.  That claim is **false**, and this file proves precisely why:

* `cellLength_div_cellDuration` and `substrate_c_is_circular` — dividing the
  cell length by the cell duration returns `c` identically, for **every**
  anchor `κ` and **every** tick budget.  `c` goes in and the same `c` comes
  out; the chain determines the cell length, not `c`.
* `speed_not_from_action_and_energy` — the structural reason.  An action and an
  energy generate only the dimensions `Mᵃ⁺ᵇ L²ᵃ⁺²ᵇ T⁻ᵃ⁻²ᵇ`, which never contains
  `L T⁻¹`.  A calibration that supplies an energy scale fixes a *time*
  (`time_from_action_and_energy`) but never a velocity; an independent length is
  needed (`speed_from_length_and_time`), and that is exactly what the substrate
  does not supply.

What survives the audit is the dimensionless part, and it survives intact:

* `refIndex` — the propagation law `n(T) = (24+T)/(24+T₀)` has no dimensionful
  input at all, and is falsifiable;
* `signalSpeed_le_c_iff` — causality forces the reference TAX to be the
  *minimum* admissible TAX, which is what makes the choice `T₀ = 3` a claim
  rather than a convention;
* `octad_min_tax` — and on the Golay layer that minimum is identified: among
  nonzero codewords the tax `wt · Q` is minimised exactly by the octads, at
  `8Q = 3.117…`, whose integer part is the `3` of "24 bits + 3 TAX"
  (`octadTax_floor_three`).  The tax here is the shipped `GLM.tax` of
  `Constants.lean` read on a binary carrier, and the weight bound is
  `GLM.Golay24.golay_min_weight`, so the identification is made against the
  development's own substrate rather than a restatement of it.

The numbers of the source note are machine-checked exactly: `E₁`, `τ`,
`T_cell`, `ℓ_cell` and the wavelength `λ₁` all appear below as two-sided
rational bounds.
-/
import RequestProject.GLM.TaxConservation
import RequestProject.GLM.Golay.Sextet

namespace GLM.Calibration

open Finset

/-! ## 1. The SI-defined constants

Since 20 May 2019 these are exact rationals by definition, so no measurement
uncertainty enters the chain. -/

/-- Speed of light in vacuum, m·s⁻¹ (exact, SI 2019). -/
def cSI : ℚ := 299792458

/-- Planck constant, J·s (exact, SI 2019). -/
def hSI : ℚ := 662607015 / 10 ^ 42

/-- Avogadro number, mol⁻¹ (exact, SI 2019). -/
def NA : ℚ := 602214076 * 10 ^ 15

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
The archive's value is `κ = 190 kJ/mol`, a bond-energy scale. -/

/-- The empirical anchor: 190 kJ/mol per unit of geometric work, in J·mol⁻¹. -/
def kappaBond : ℚ := 190000

/-- Energy of one unit of geometric work, in joules. -/
def workEnergy (kappa : ℚ) : ℚ := kappa / NA

/-- Tick duration, in seconds: the Planck–Einstein period of a quantum carrying
one unit of geometric work. -/
def tick (kappa : ℚ) : ℚ := hSI / workEnergy kappa

/-- Tick budget of one cell: 24 bit-shifts plus `T` ticks of TAX overhead. -/
def ticksPerCell (T : ℚ) : ℚ := 24 + T

/-- The vacuum/reference TAX used by the chain: `24 + 3 = 27` ticks per cell. -/
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

/-! ## 3. The numbers of the source note, verified exactly -/

/-- `E₁ = κ/N_A = 3.1550…×10⁻¹⁹ J` (the note rounds this to `3.16×10⁻¹⁹ J`). -/
theorem workEnergy_value : workEnergy kappaBond = 19 / (602214076 * 10 ^ 11) := by
  norm_num [workEnergy, kappaBond, NA]

theorem workEnergy_bounds :
    3155024 / 10 ^ 25 < workEnergy kappaBond ∧ workEnergy kappaBond < 3155025 / 10 ^ 25 := by
  rw [workEnergy_value]; constructor <;> norm_num

/-- `τ = 2.100164…×10⁻¹⁵ s = 2.10 fs`, exactly as claimed. -/
theorem tick_value : tick kappaBond = 19951563564467157 / (95 * 10 ^ 29) := by
  rw [tick_eq kappaBond (by norm_num [kappaBond]), molarPlanck_eq]
  norm_num [kappaBond]

theorem tick_bounds :
    2100164 / 10 ^ 21 < tick kappaBond ∧ tick kappaBond < 2100165 / 10 ^ 21 := by
  rw [tick_value]; constructor <;> norm_num

/-- `T_cell = 27τ = 5.6704…×10⁻¹⁴ s`, exactly as claimed. -/
theorem cellDuration_bounds :
    5670444 / 10 ^ 20 < cellDuration kappaBond taxVacuum ∧
      cellDuration kappaBond taxVacuum < 5670445 / 10 ^ 20 := by
  have h : cellDuration kappaBond taxVacuum = 27 * tick kappaBond := by
    norm_num [cellDuration, ticksPerCell, taxVacuum]
  rw [h, tick_value]; constructor <;> norm_num

/-- `ℓ_cell = 1.69995…×10⁻⁵ m = 17.0 μm`, as claimed (the note's `17.0` uses
`c ≈ 3×10⁸`; with the exact `c` the value is `16.9996 μm`). -/
theorem cellLength_bounds :
    1699956 / 10 ^ 11 < cellLength kappaBond taxVacuum ∧
      cellLength kappaBond taxVacuum < 1699957 / 10 ^ 11 := by
  have h : cellLength kappaBond taxVacuum = cSI * (27 * tick kappaBond) := by
    norm_num [cellLength, cellDuration, ticksPerCell, taxVacuum]
  rw [h, tick_value, cSI]; constructor <;> norm_num

/-! ## 4. What the chain really is

The composite of "divide by `N_A`", "apply `E = h/τ`" and "multiply by `c`" is
the Planck relation for a photon: the cell length is `24+T` wavelengths of the
quantum whose energy is one unit of geometric work. -/

/-- Wavelength of a photon carrying one unit of geometric work. -/
def workWavelength (kappa : ℚ) : ℚ := cSI * tick kappa

/-- **The chain in one line.**  The "cell length" is `24+T` wavelengths of the
one-work-unit photon. -/
theorem cellLength_eq_wavelengths (kappa T : ℚ) :
    cellLength kappa T = ticksPerCell T * workWavelength kappa := by
  rw [cellLength, cellDuration, workWavelength]; ring

/-- With `κ = 190 kJ/mol` that photon is red visible light, `λ₁ = 629.6 nm` —
not, as the note says, a molecular vibration quantum, which would lie between
roughly `2` and `20 μm`. -/
theorem workWavelength_bounds :
    6296 / 10 ^ 10 < workWavelength kappaBond ∧ workWavelength kappaBond < 6297 / 10 ^ 10 := by
  rw [workWavelength, tick_value, cSI]; constructor <;> norm_num

/-! ## 5. `c` is an input, not an output -/

/-- Dividing the cell length by the cell duration returns `c` identically — for
**every** anchor `κ` and **every** tick budget `T`.  A quantity that comes back
unchanged whatever the inputs were is not being predicted. -/
theorem cellLength_div_cellDuration (kappa T : ℚ) (h : cellDuration kappa T ≠ 0) :
    cellLength kappa T / cellDuration kappa T = cSI := by
  rw [cellLength]; field_simp

/-- The same statement with the conclusion made explicit: had the substrate's
speed of light been any other value `c'`, running the identical chain with `c'`
would return `c'`.  The chain places no constraint whatsoever on `c`. -/
theorem substrate_c_is_circular (c' kappa T : ℚ) (h : cellDuration kappa T ≠ 0) :
    c' * cellDuration kappa T / cellDuration kappa T = c' := by
  field_simp

/-- Rescaling the empirical anchor rescales the tick inversely: the anchor fixes
the absolute scale, and the substrate contributes only the dimensionless budget. -/
theorem tick_scale (r kappa : ℚ) (hr : r ≠ 0) (hk : kappa ≠ 0) :
    tick (r * kappa) = tick kappa / r := by
  rw [tick_eq _ (mul_ne_zero hr hk), tick_eq _ hk]; field_simp

theorem cellLength_scale (r kappa T : ℚ) (hr : r ≠ 0) (hk : kappa ≠ 0) :
    cellLength (r * kappa) T = cellLength kappa T / r := by
  rw [cellLength_eq _ _ (mul_ne_zero hr hk), cellLength_eq _ _ hk]
  field_simp

/-! ### The dimensional obstruction

Dimensions are exponent triples `(mass, length, time)`. -/

/-- A physical dimension as an exponent vector `(M, L, T)`. -/
abbrev Dim := ℤ × ℤ × ℤ

def dMass : Dim := (1, 0, 0)
def dLength : Dim := (0, 1, 0)
def dTime : Dim := (0, 0, 1)
def dSpeed : Dim := (0, 1, -1)
def dEnergy : Dim := (1, 2, -2)
def dAction : Dim := (1, 2, -1)

/-- A product of powers of dimensionless quantities is dimensionless: the
elementary Buckingham-Π obstruction.  No amount of dimensionless substrate
structure produces a dimensionful constant. -/
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
energy has the dimension of a speed, so the chain cannot produce `c`: it must be
given `c`. -/
theorem speed_not_from_action_and_energy :
    ¬ ∃ a b : ℤ, a • dAction + b • dEnergy = dSpeed := by
  rintro ⟨a, b, h⟩
  simp only [dAction, dEnergy, dSpeed, Prod.ext_iff, Prod.smul_mk, smul_eq_mul,
    Prod.mk_add_mk] at h
  obtain ⟨h1, h2, _⟩ := h
  omega

/-- An action and an energy do determine a *time*: the step `τ = h/E₁` is
sound, and is the only part of the chain that is. -/
theorem time_from_action_and_energy :
    (1 : ℤ) • dAction + (-1 : ℤ) • dEnergy = dTime := by decide

/-- Nor do they determine a mass. -/
theorem mass_not_from_action_and_energy :
    ¬ ∃ a b : ℤ, a • dAction + b • dEnergy = dMass := by
  rintro ⟨a, b, h⟩
  simp only [dAction, dEnergy, dMass, Prod.ext_iff, Prod.smul_mk, smul_eq_mul,
    Prod.mk_add_mk] at h
  obtain ⟨h1, h2, _⟩ := h
  omega

/-- **What would close the gap.**  One independent *length* anchor and the speed
follows.  The chain would be a derivation of `c` exactly if the substrate
predicted `ℓ_cell` on its own; instead it computes `ℓ_cell` *from* `c`. -/
theorem speed_from_length_and_time :
    (1 : ℤ) • dLength + (-1 : ℤ) • dTime = dSpeed := by decide

/-! ## 6. What survives: the refractive-index law

`n(T) = (24+T)/(24+T₀)` is dimensionless, involves no empirical anchor, and is
falsifiable. -/

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

/-- **Causality forces the reference TAX to be the minimum TAX.**  With `T₀ = 3`
the model is subluminal exactly on regions of TAX `≥ 3`; an admissible state of
TAX `< 3` would transmit signals faster than light. -/
theorem signalSpeed_le_c_iff (T₀ T : ℚ) (hT : 0 < ticksPerCell T) :
    signalSpeed T₀ T ≤ cSI ↔ T₀ ≤ T := by
  have hT' : (0 : ℚ) < 24 + T := hT
  rw [signalSpeed, ticksPerCell, ticksPerCell, div_le_iff₀ hT']
  constructor
  · intro h; nlinarith [cSI_pos]
  · intro h; nlinarith [cSI_pos]

/-- Vacuum, `T = T₀ = 3`: the model reproduces `v = c`, by construction. -/
theorem signalSpeed_vacuum : signalSpeed taxVacuum taxVacuum = cSI := by
  norm_num [signalSpeed, ticksPerCell, taxVacuum]

/-- The refractive index is strictly increasing in the TAX. -/
theorem refIndex_strictMono (T₀ : ℚ) (h₀ : 0 < ticksPerCell T₀) :
    StrictMono (refIndex T₀) := by
  intro a b hab
  rw [refIndex, refIndex, div_lt_div_iff_of_pos_right h₀]
  simpa [ticksPerCell] using hab

/-- The worked example: a region whose TAX rises from `3` to `8` has refractive
index `32/27 ≈ 1.185`. -/
theorem refIndex_tax_eight : refIndex 3 8 = 32 / 27 := by
  norm_num [refIndex, ticksPerCell]

/-- **A falsifiable ceiling.**  If the TAX of a region is bounded by `24` — the
largest Hamming weight available in 24 bits — the law caps the refractive index
at `48/27 = 16/9 ≈ 1.778`.  Diamond (`n = 2.417`) exceeds this, so either the
TAX budget must exceed `24` or the law is wrong for dense media. -/
theorem refIndex_le_of_tax_le (T : ℚ) (h : T ≤ 24) : refIndex 3 T ≤ 16 / 9 := by
  rw [refIndex, ticksPerCell, ticksPerCell, div_le_iff₀ (by norm_num : (0:ℚ) < 24 + 3)]
  linarith

/-! ## 7. The `3` in "24 bits + 3 TAX"

The shipped tax of `Constants.lean` on a binary carrier is `HW · Q` with
`Q = Y + 1/8` (`GLM.tax_ofBits`).  On the Golay layer the carrier is a codeword,
so the question "what is the cheapest nonzero state?" is answered by the code's
minimum weight — which is `8` (`GLM.Golay24.golay_min_weight`). -/

/-- The binary carrier of a 24-cell Golay word. -/
def bitsOf (c : Golay24.Word) : Fin 24 → Bool := fun i => decide (i ∈ c)

@[simp] theorem support_bitsOf (c : Golay24.Word) : support (bitsOf c) = c := by
  ext i; simp [bitsOf]

/-- The tax of a Golay word's carrier is its Hamming weight times `Q`. -/
theorem tax_bitsOf (c : Golay24.Word) : tax (ofBits (bitsOf c)) = (Golay24.wt c : ℝ) * Q := by
  rw [tax_ofBits, support_bitsOf]; rfl

/-- Sharper bounds on the read quantum than `Constants.lean` needs: `Y = π/(π²+2)`
lies in `(0.264675, 0.264676)`. -/
theorem Y_bounds : 0.264675 < Y ∧ Y < 0.264676 := by
  have hpi : (0:ℝ) < Real.pi := Real.pi_pos
  have h1 : (3.141592 : ℝ) < Real.pi := Real.pi_gt_d6
  have h2 : Real.pi < 3.141593 := Real.pi_lt_d6
  have hden : (0:ℝ) < Real.pi ^ 2 + 2 := by positivity
  have hY : Y = Real.pi / (Real.pi ^ 2 + 2) := by
    unfold Y; field_simp
  rw [hY]
  constructor
  · rw [lt_div_iff₀ hden]; nlinarith
  · rw [div_lt_iff₀ hden]; nlinarith

/-- Symmetry tax of a codeword of Hamming weight `w`, as a function of the
weight alone. -/
noncomputable def codewordTax (w : ℕ) : ℝ := (w : ℝ) * Q

/-- The bridge to `Constants.lean`: for a carrier all of whose coordinates are
`0` or `1`, `GLM.tax` is `codewordTax` of its Hamming weight. No new cost
function is introduced by the light chain. -/
theorem tax_indicator {n : ℕ} (v : Fin n → ℤ) (hv : ∀ i, v i = 0 ∨ v i = 1) :
    GLM.tax v = codewordTax (GLM.hammingWeight v) := by
  have hns : GLM.normSq v = (GLM.hammingWeight v : ℤ) := by
    classical
    simp only [GLM.normSq, GLM.hammingWeight]
    rw [Finset.card_filter]
    push_cast
    refine Finset.sum_congr rfl ?_
    intro i _
    rcases hv i with h | h <;> simp [h]
  simp only [GLM.tax, codewordTax, hns, GLM.Q]
  push_cast
  ring

theorem codewordTax_strictMono : StrictMono codewordTax := by
  intro a b hab
  have h : (a : ℝ) < b := by exact_mod_cast hab
  have := Q_pos
  unfold codewordTax
  nlinarith

/-- **The octads minimise the symmetry tax among nonzero Golay codewords.**
This is the precise — and true — form of the archive's "photon = minimum-TAX
octad" claim: it holds on the code layer. -/
theorem octad_min_tax {c : Golay24.Word} (hc : Golay24.IsCodeword c) (hne : c ≠ ∅) :
    codewordTax 8 ≤ tax (ofBits (bitsOf c)) := by
  rw [tax_bitsOf]
  have hw : 8 ≤ Golay24.wt c := Golay24.golay_min_weight hc hne
  rcases eq_or_lt_of_le hw with h | h
  · rw [← h]; rfl
  · exact le_of_lt (codewordTax_strictMono h)

/-- Equality holds only for the octads. -/
theorem octad_min_tax_strict {c : Golay24.Word} (hc : Golay24.IsCodeword c) (hne : c ≠ ∅)
    (h8 : Golay24.wt c ≠ 8) : codewordTax 8 < tax (ofBits (bitsOf c)) := by
  rw [tax_bitsOf]
  exact codewordTax_strictMono (lt_of_le_of_ne (Golay24.golay_min_weight hc hne) (Ne.symm h8))

/-- The minimum is attained: an octad exists. -/
theorem octad_min_tax_attained :
    ∃ c : Golay24.Word, Golay24.IsCodeword c ∧ tax (ofBits (bitsOf c)) = codewordTax 8 := by
  obtain ⟨c, hc, hw⟩ := Golay24.golay_min_distance_eight.2
  exact ⟨c, hc, by rw [tax_bitsOf, hw]; rfl⟩

/-- The minimum nonzero codeword tax is `8Q = 8Y + 1`. -/
theorem octadTax_eq : codewordTax 8 = 8 * Y + 1 := by
  unfold codewordTax Q; push_cast; ring

/-- **Where the `3` comes from.**  `⌊8Q⌋ = 3`: the "3 TAX overhead" of the
calibration chain is the integer part of the minimum nonzero symmetry tax. -/
theorem octadTax_floor_three : (3 : ℝ) < codewordTax 8 ∧ codewordTax 8 < 4 := by
  obtain ⟨hl, hu⟩ := Y_bounds
  rw [octadTax_eq]
  constructor <;> nlinarith

/-- Using the exact tax instead of the rounded `3` moves the tick budget from
`27` to `24 + 8Q = 27.1174…`, i.e. the cell length by about `+0.43 %`.  The
rounding is therefore a real approximation, not a definition. -/
theorem exactTicksPerCell_bounds :
    (27.1174 : ℝ) < 24 + codewordTax 8 ∧ 24 + codewordTax 8 < 27.1175 := by
  obtain ⟨hl, hu⟩ := Y_bounds
  rw [octadTax_eq]
  constructor <;> nlinarith

/-! ### The correction the second round made

At the *Leech* layer the tax audit ranks the minimal-vector classes by Hamming
weight, and all minimal vectors have `‖v‖² = 32`, so the tax is `w·Y + 4`.  The
shape `(∓4², 0²²)` has weight 2 and is strictly cheaper than the octad shape
`(∓2⁸, 0¹⁶)`.  "Photon = minimum-tax octad" is therefore true on the Golay layer
and false among Leech minimal vectors. -/

/-- Tax of a Leech minimal vector of Hamming weight `w`: `‖v‖² = 32`, so
`Tax = w·Y + 4`. -/
noncomputable def minimalVectorTax (w : ℕ) : ℝ := (w : ℝ) * Y + 4

theorem classA_tax_lt_octad_tax : minimalVectorTax 2 < minimalVectorTax 8 := by
  have := Y_pos
  unfold minimalVectorTax
  push_cast
  nlinarith

theorem minimalVectorTax_values :
    (4.5293 : ℝ) < minimalVectorTax 2 ∧ minimalVectorTax 2 < 4.5294 ∧
      (6.1174 : ℝ) < minimalVectorTax 8 ∧ minimalVectorTax 8 < 6.1175 := by
  obtain ⟨hl, hu⟩ := Y_bounds
  refine ⟨?_, ?_, ?_, ?_⟩ <;> unfold minimalVectorTax <;> push_cast <;> nlinarith

end GLM.Calibration
