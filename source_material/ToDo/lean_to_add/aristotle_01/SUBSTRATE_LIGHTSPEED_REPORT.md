# The Substrate Speed of Light — exact definitions, verification and correction

**Scope.** This report gives the exact mathematical content of
`substrate_speed_of_light.md`, checked against `LIGHTSPEED_STUDY_SYNTHESIS.md`
and against the substrate code (`ubp_unified_v5.py`).  Every number in the
original note is reproduced exactly; three of its interpretive claims are shown
to be wrong; and the part of the idea that is genuinely predictive is isolated
and stated as a falsifiable law.

**Artifacts**

| File | What it is |
|---|---|
| `substrate_lightspeed.py` | exact-rational implementation and audit (`--selftest`, `--report`, `--chain`, `--index`, `--constants`, `--json`) |
| `RequestProject/Lightspeed.lean` | machine-checked: the chain, the circularity theorem, the dimensional no-go, the refractive-index law, the origin of the "3 TAX" |
| `RequestProject/SubstrateConstants.lean` | machine-checked: `MONAD`, `WOBBLE`, `L`, `Y` and the accuracy of alignment points P2, P4, P6, P7, P8 |
| `lightspeed_audit.json` | machine-readable dump of every quantity below |

```bash
python3 substrate_lightspeed.py --selftest   # 30 checks, all pass
python3 substrate_lightspeed.py --report     # the tables reproduced below
lake build                                   # the proofs (no sorry, standard axioms)
```

---

## 0. Verdict in one page

| # | Claim of `substrate_speed_of_light.md` | Verdict |
|---|---|---|
| 1 | `E₁ = κ/N_A = 3.16×10⁻¹⁹ J` | **Reproduces exactly** (`3.1550×10⁻¹⁹ J`) |
| 2 | `τ = h/E₁ = 2.10 fs` | **Reproduces exactly** (`2.100165 fs`) |
| 3 | `T_cell = 27τ = 5.67×10⁻¹⁴ s` | **Reproduces exactly** |
| 4 | `ℓ_cell = c·T_cell = 17.0 μm` | **Reproduces exactly** (`16.9996 μm` with the exact `c`) |
| 5 | "The speed of light is not an input constant. It's an output." | **False.** `c` enters at step 4 and is returned unchanged; `ℓ_cell/T_cell = c` identically, for every `κ` and every tick budget |
| 6 | "`3.16×10⁻¹⁹ J` = one molecular vibration quantum" | **False.** That is `15 883 cm⁻¹`, i.e. a `630 nm` *visible-light* photon; molecular vibrations lie at `500–4 400 cm⁻¹` |
| 7 | "`2.10 fs` matches molecular vibration timescales" | **False.** It is the optical period of red light; the fastest molecular vibration (H₂, `4 401 cm⁻¹`) has a `7.6 fs` period, ordinary stretches `11–70 fs` |
| 8 | "`17 μm` = molecular scale" | **False.** Molecular diameters are `10⁻¹⁰ m`; `17 μm` is `10⁵` times larger (mid-IR wavelength / eukaryotic-cell scale) |
| 9 | "`190 kJ/mol` is the exact Br–Br bond energy" | **Approximate.** The tabulated value is `193 kJ/mol`; the agreement is to `1.6 %`, not exact |
| 10 | "Refractive index emerges from lattice geometry", `TAX 3→8` | **This is the real result.** `n(T) = (24+T)/27` is dimensionless, anchor-free and falsifiable; `n(8) = 32/27 = 1.185` is correct within the model |
| 11 | "24 bits + 3 TAX = 27 ticks" | **Justified, with a correction.** The minimum symmetry tax of a nonzero Golay codeword is `8Y + 1 = 3.1174`, whose integer part is `3`. Using the exact value gives `27.1174` ticks and `ℓ_cell = 17.07 μm` |

And from `LIGHTSPEED_STUDY_SYNTHESIS.md`:

| Point | Verdict |
|---|---|
| P5 "photon = minimum-Tax octad, MATHEMATICAL FACT" | **True on the Golay layer only.** Among the Leech minimal vectors the substrate's own tax audit ranks class A (`Tax = 4.5294`) below the octad class B (`Tax = 6.1174`) |
| P6 "γ = MONAD/13, EXACT IDENTITY" | **True but empty.** `MONAD = 13 + WOBBLE` and `L = WOBBLE/13`, so `MONAD/13 = 1 + L` is the definition of `L` rewritten. The resulting `v/c = 0.338878` is a definition, not a prediction |
| P2 `m_μ/m_e = 169/WOBBLE`, "0.03 %" | **Confirmed:** `0.02938 %` |
| P7 `1/α = 220−83+L`, "0.02 %" | **Confirmed:** `0.01962 %` |
| P8 `m_p/m_e = 1836+2L_s`, "0.001 %" | **Better than quoted:** `0.0000374 %` |
| P4 `m_e = Y²·WOBBLE·24⁴·29⁴·hΔν_Cs/c²`, "0.007 %" | **Quoted error is too small:** the reproducible value is `0.00919 %` |
| "Deriving `c` directly is structurally closed by Buckingham's Π" | **Correct**, and now proved in the specific form that applies here |

---

## 1. The exact definitions

### 1.1 Inputs

Since 20 May 2019 the following are *exact rational numbers by definition*, so
the entire chain is exact rational arithmetic with no measurement uncertainty:

| Symbol | Value | Unit |
|---|---|---|
| `c` | `299 792 458` | m·s⁻¹ |
| `h` | `6.626 070 15 × 10⁻³⁴` | J·s |
| `N_A` | `6.022 140 76 × 10²³` | mol⁻¹ |
| `Δν_Cs` | `9 192 631 770` | Hz |

Only one combination is ever used:

> **Definition 1 (molar Planck constant).**
> `h·N_A = 19 951 563 564 467 157 / (5 × 10²⁵) J·s·mol⁻¹ = 3.990 312 712 893 43 × 10⁻¹⁰`
> — exact.  *(`UBPLightspeed.molarPlanck_eq`)*

The one empirical input is the calibration anchor:

> **Definition 2 (work anchor).** `κ` = joules **per mole** per unit of
> geometric work.  The note's fitted value from 114 element pairs is
> `κ = 190 kJ/mol = 190 000 J·mol⁻¹`.

### 1.2 The chain

> **Definition 3 (work energy).** `E₁(κ) = κ / N_A`, joules per work unit.
>
> **Definition 4 (tick).** `τ(κ) = h / E₁(κ)`, seconds.
> Equivalently `τ(κ) = h·N_A / κ`.  *(`UBPLightspeed.tick_eq`)*
> This is the Planck–Einstein period of a quantum of energy `E₁`.
>
> **Definition 5 (tick budget).** `ν(T) = 24 + T`, dimensionless: 24 bit-shifts
> plus `T` ticks of TAX overhead.  The note takes `T = T₀ = 3` for the vacuum.
>
> **Definition 6 (cell duration and cell length).**
> `T_cell(κ,T) = ν(T)·τ(κ)` seconds, and `ℓ_cell(κ,T) = c · T_cell(κ,T)` metres.

Closed form: `ℓ_cell(κ,T) = (24+T)·c·h·N_A / κ`
*(`UBPLightspeed.cellLength_eq`)*.

### 1.3 The derived quantities

> **Definition 7 (signal speed and refractive index).** For a region of TAX `T`
> against a reference TAX `T₀`,
>
> ```
>   v(T)  =  ℓ_cell(κ,T₀) / (ν(T)·τ(κ))  =  c·(24+T₀)/(24+T)
>   n(T)  =  c / v(T)                     =  (24+T)/(24+T₀)
> ```
>
> Both are independent of `κ`.  *(`UBPLightspeed.signalSpeed`, `refIndex`)*

---

## 2. The published numbers, reproduced exactly

All values below are exact rationals; the decimals are truncations.
Machine-checked in `RequestProject/Lightspeed.lean`.

| Quantity | Exact value | Note's value | Lean theorem |
|---|---|---|---|
| `E₁ = κ/N_A` | `19 / (602 214 076 × 10¹¹) = 3.155 024 2×10⁻¹⁹ J` | `3.16×10⁻¹⁹ J` | `workEnergy_value`, `workEnergy_bounds` |
| `τ = h N_A/κ` | `19 951 563 564 467 157 / (95 × 10²⁹) = 2.100 164 6×10⁻¹⁵ s` | `2.10 fs` | `tick_value`, `tick_bounds` |
| `T_cell = 27τ` | `5.670 444 4×10⁻¹⁴ s` | `5.67×10⁻¹⁴ s` | `cellDuration_bounds` |
| `ℓ_cell = c·T_cell` | `1.699 956 5×10⁻⁵ m = 16.9996 μm` | `17.0 μm` | `cellLength_bounds` |
| `λ₁ = c·τ` | `6.296 1×10⁻⁷ m = 629.6 nm` | (not given) | `workWavelength_bounds` |

The note's `17.0` uses `c ≈ 3×10⁸`; with the defined `c` the answer is
`16.9996 μm`.  **Everything in the note's arithmetic is correct.**

---

## 3. What the chain actually is

> **Theorem 1 (the chain in one line).**
> `ℓ_cell(κ,T) = (24+T) · λ₁(κ)`, where `λ₁(κ) = c·τ(κ) = h c N_A/κ` is the
> wavelength of a photon whose energy is one unit of geometric work.
> *(`UBPLightspeed.cellLength_eq_wavelengths`)*

So the composite of "divide by `N_A`", "apply `E = h/τ`" and "multiply by `c`"
is nothing but the Planck relation `λ = hc/E`, times the integer `27`.  At
`κ = 190 kJ/mol` the one-work-unit photon is **red visible light**,
`λ₁ = 629.6 nm` (`15 883 cm⁻¹`), and the cell is 27 of its wavelengths.

This immediately gives the correct reading of items 6–8 of the verdict table:

* `E₁ = 3.155×10⁻¹⁹ J` is an *electronic* / visible-photon energy, not a
  vibrational quantum.  Vibrational quanta run `1×10⁻²⁰` to `9×10⁻²⁰ J`.
* `τ = 2.10 fs` is the optical period of that photon.  Molecular vibration
  periods are `7.6 fs` (H₂) to `~70 fs` (heavy-atom stretches) — a factor 4–30
  longer.
* `17 μm` is not a molecular scale.  It is `~10⁵` molecular diameters; it is
  the mid-infrared wavelength scale, or the size of a eukaryotic cell.

None of this invalidates the arithmetic.  It means the note's *physical gloss*
should be replaced by: **the calibration places one work unit at the energy of a
red photon, and one cell at 27 of its wavelengths.**

---

## 4. `c` is an input, not an output

The note's headline is:

> *"The speed of light is not an input constant. It's an output of how fast the
> substrate can cycle through 24-bit error correction."*

> **Theorem 2 (circularity).** For every `κ` and every tick budget `T` with
> `T_cell ≠ 0`,
> ```
>   ℓ_cell(κ,T) / T_cell(κ,T) = c .
> ```
> *(`UBPLightspeed.cellLength_div_cellDuration`)*
> Moreover, had the true speed been some other `c'`, running the identical chain
> with `c'` in place of `c` returns `c'`.
> *(`UBPLightspeed.substrate_c_is_circular`)*

A quantity that is returned unchanged whatever the inputs were is not being
predicted.  Step 4 of the chain *defines* `ℓ_cell` from `c`; step 5 divides it
back out.

The structural reason is dimensional, and it is exactly the Buckingham
obstruction the synthesis document already suspected — here in the specific
form that applies:

> **Theorem 3 (no speed from an action and an energy).** Writing dimensions as
> exponent triples `(M, L, T)`, there are **no** integers `a, b` with
> ```
>   a·(1,2,−1) + b·(1,2,−2) = (0,1,−1) .
> ```
> *(`UBPLightspeed.speed_not_from_action_and_energy`)*
> By contrast `1·(1,2,−1) − 1·(1,2,−2) = (0,0,1)`: an action and an energy do
> determine a **time**.  *(`UBPLightspeed.time_from_action_and_energy`)*

The calibration supplies an action (`h`) and an energy (`κ/N_A`).  That is
enough to fix the tick `τ` — and the tick is a genuine output.  It is *not*
enough to fix a length, hence not enough to fix a speed.

> **Theorem 4 (what would close the gap).** `(0,1,0) − (0,0,1) = (0,1,−1)`:
> a length plus a time gives a speed.  *(`UBPLightspeed.speed_from_length_and_time`)*

**So the chain would become a genuine derivation of `c` if and only if the
substrate predicted `ℓ_cell` independently of `c`.**  It does not.  Nothing in
`ubp_unified_v5.py` fixes a length; `PhysicsALU` takes `c` and `h` as given
constants.

There is a further covariance that makes the point sharper:

> **Theorem 5 (anchor covariance).** `τ(rκ) = τ(κ)/r` and
> `ℓ_cell(rκ,T) = ℓ_cell(κ,T)/r`.
> *(`UBPLightspeed.tick_scale`, `cellLength_scale`)*

The absolute scale comes entirely from the empirical `κ`; the substrate's whole
contribution to the chain is the **integer 27**.  (`--report` section 3
tabulates this: `κ = 100 kJ/mol` would give a `32.3 μm` cell, `κ = 500` would
give `6.46 μm`.)

### 4.1 Could the substrate supply the missing length itself?

There is exactly one place in `ubp_unified_v5.py` where a *dimensionful*
constant is asserted from substrate numbers — `PhysicsALU`:

```python
    G_N = F(39, 29) * (_Y ** 18 / _UBP_CONSTS["WOBBLE"])      #  6.683155e-11
```

This is a pure number declared to be `G` in SI units.  It is within `0.13 %` of
the CODATA value `6.67430×10⁻¹¹ m³ kg⁻¹ s⁻²`.  If it were taken at face value it
*would* supply an independent length, via `ℓ_P = √(ħG/c³)`, and that would make
`c` derivable in principle.  Two reasons it cannot be used here:

1. The synthesis document's own Phase 14 found this family of formulas to be
   precision-unstable — it works with the substrate's approximate `π` and fails
   with the true `π`.  A length built on it is not trustworthy.
2. Even taken at face value it is **inconsistent with the cell length**:
   `ℓ_P = 1.617×10⁻³⁵ m`, which is `1.05×10³⁰` times smaller than
   `ℓ_cell = 1.700×10⁻⁵ m`.  The substrate would then possess two length scales
   thirty orders of magnitude apart with no relation between them.  The note
   acknowledges the gap ("Planck length … too small") but presents it as a
   feature rather than as the tension it is.

So the missing length has to come from somewhere else — see §10.2.

### 4.2 The honest statement of the result

> **Chemistry data + the Planck relation + the defined `c` determine a single
> new number: the substrate cell length, `ℓ_cell = 27·h c N_A/κ = 17.0 μm`.**

That is a real, non-trivial output of the study.  It is a *calibration*, not a
derivation, and it is only as good as the `190 kJ/mol` fit.

---

## 5. What survives: the refractive-index law

The one part of the note that predicts rather than calibrates is
`n(T) = (24+T)/(24+T₀)`.  It contains no `κ`, no `h`, no `N_A`, no `c` — it is
purely a statement about the substrate's tick accounting, and it is
falsifiable.

> **Theorem 6 (causality fixes the reference TAX).**
> `v(T) ≤ c ⟺ T ≥ T₀`.  *(`UBPLightspeed.signalSpeed_le_c_iff`)*

So `T₀` must be the **minimum** admissible TAX, or the model transmits signals
faster than light.  This is a *derivation* of the role of the "3": it is not a
free parameter, it is forced to be the floor of the tax spectrum.

> **Theorem 7 (monotonicity and ceiling).** `n` is strictly increasing in `T`
> *(`refIndex_strictMono`)*, `n(8) = 32/27 = 1.1852`
> *(`refIndex_tax_eight`)*, and if `T ≤ 24` then `n ≤ 48/27 = 16/9 = 1.7778`
> *(`refIndex_le_of_tax_le`)*.

Inverting the law against measured indices (`--index`):

| medium | `n` | required TAX `= 27n − 24` | admissible? |
|---|---|---|---|
| vacuum | 1.00000 | 3.0000 | yes |
| air (STP) | 1.00029 | 3.0079 | yes |
| water | 1.33300 | **11.9910** | yes |
| ethanol | 1.36100 | 12.7470 | yes |
| fused silica | 1.45850 | 15.3795 | yes |
| crown glass | 1.52000 | 17.0400 | yes |
| sapphire | 1.76820 | 23.7414 | yes |
| diamond | 2.41750 | 41.2725 | **TAX > 24** |
| silicon (1.55 μm) | 3.47570 | 69.8439 | **TAX > 24** |

Two observations, stated without over-interpretation:

* Water lands on `T = 11.99`, i.e. on the Golay weight `12` to four figures.
  This is a single coincidence in a nine-row table and is reported as such —
  it is not evidence for anything on its own.
* The model has a hard ceiling.  If TAX cannot exceed 24, no medium can have
  `n > 1.778`, and diamond falsifies the law.  **This is the concrete
  experimental content of the idea, and it is where it should be tested first.**

---

## 6. Where the `3` and the `27` come from

The substrate's symmetry tax (`ubp_unified_v5.py`,
`LeechEngine.calculate_symmetry_tax`) is

```
    Tax(v) = HW(v)·Y + ‖v‖²/8 ,        Y = 1/(π + 2/π) = 0.264675430405
```

On the **Golay layer** a codeword is a 0/1 vector, so `‖v‖² = HW(v)` and
`Tax = HW·(Y + 1/8)`, a strictly increasing function of the weight.

> **Theorem 8 (the octads minimise the tax).** For every nonzero Golay codeword
> `v`, `Tax(octad) ≤ Tax(v)`, with equality only if `HW(v) = 8`.
> *(`UBPLightspeed.octad_min_tax`, `octad_min_tax_strict`)*
>
> **Theorem 9 (the value).** `Tax(octad) = 8Y + 1`, and
> `3 < 8Y + 1 < 4`.  *(`UBPLightspeed.octadTax_eq`, `octadTax_floor_three`)*

Numerically `8Y + 1 = 3.117403`.  **That is the "3 TAX overhead":** the minimum
nonzero symmetry tax, truncated to an integer number of ticks.  Combined with
Theorem 6 (the reference TAX must be the minimum TAX) the `27 = 24 + 3` of the
note is now fully accounted for, and the octad is exactly the state that
realises it — which is the defensible core of alignment point P5.

Using the exact tax rather than the rounded `3` gives
`24 + 8Y + 1 = 27.117403` ticks per cell
*(`UBPLightspeed.exactTicksPerCell_bounds`)* and hence
`ℓ_cell = 17.0735 μm`, a `+0.43 %` correction.  The full spectrum:

| Golay weight | `Tax = w(Y+1/8)` | ticks/cell | `n = ticks/27` |
|---|---|---|---|
| 8 (octad) | 3.117403 | 27.117403 | 1.004348 |
| 12 | 4.676105 | 28.676105 | 1.062078 |
| 16 | 6.234807 | 30.234807 | 1.119808 |
| 24 | 9.352210 | 33.352210 | 1.235267 |

Note that with the *codeword* tax the reachable index range is only
`[1.004, 1.235]`, narrower than the `[1, 1.778]` obtained from integer TAX `≤ 24`.
Which spectrum is the physical one is the model's main undetermined choice, and
it should be fixed before the law is tested.

### 6.1 Correction to P5

`LIGHTSPEED_STUDY_SYNTHESIS.md` records P5 as "Photon = minimum-Tax octad
(HW=8), EXACT, MATHEMATICAL FACT".  On Leech **minimal vectors** all three
classes have `‖v‖² = 32`, so `Tax = HW·Y + 4`, and the substrate's own audit
(`python3 ubp_unified_v5.py --audit`) prints

| class | shape | HW | Tax |
|---|---|---|---|
| A | `(∓4², 0²²)` | 2 | **4.529351** |
| B (octads) | `(∓2⁸, 0¹⁶)` | 8 | 6.117403 |
| C | `(∓3, ±1²³)` | 24 | 10.352210 |

Class A is cheaper.  *(`UBPLightspeed.classA_tax_lt_octad_tax`,
`minimalVectorTax_values`)*  P5 should be restated as:

> **P5′.** Among the *nonzero codewords of the Golay code*, the octads uniquely
> minimise the symmetry tax, at `8Y + 1 = 3.1174`.

---

## 7. The chemistry anchor

`κ = 190 kJ/mol` is the only empirical number in the chain, fitted from 114
element pairs.  The supporting data set is not in this repository, so the fit
itself could not be re-run; what *can* be checked is the note's own table, and
it is internally consistent:

| bond | tabulated | note's work units | `E/190` |
|---|---|---|---|
| Br–Br | 190 (note) / **193** (standard) | — | 1.000 / 1.016 |
| C–C | 347 | 1.83 | 1.826 ✓ |
| O=O | 498 | 2.62 | 2.621 ✓ |
| C=O | 799 | 4.21 | 4.205 ✓ |
| N≡N | 946 | 4.98 | 4.979 ✓ |

The claim "this matches the exact energy required to break a Br–Br bond" should
be softened: the commonly tabulated Br₂ bond dissociation enthalpy is
`193 kJ/mol`, so the agreement is to `1.6 %`.  It is also selection-sensitive —
a fitted constant landing within a couple of percent of *some* entry in a table
of bond enthalpies spanning `150–950 kJ/mol` is not surprising.  Using
`κ = 193 kJ/mol` instead moves the cell length to `16.735 μm`.

---

## 8. The alignment points of `LIGHTSPEED_STUDY_SYNTHESIS.md`

### 8.1 Exact definitions

From `UBPUltimateSubstrate.get_v6_constants` and
`UBPSourceCodeParticlePhysics`:

```
    π, φ, e   50-term continued-fraction convergents (exact rationals)
    MONAD  = π · φ · e                    = 13.817580227176
    WOBBLE = MONAD − ⌊MONAD⌋ = MONAD − 13 =  0.817580227176
    L      = WOBBLE / 13                  =  0.062890786706
    Y      = 1 / (π + 2/π)                =  0.264675430405
    σ      = 29/24 ,   L_s = L·σ          =  0.075993033936
    U_e    = 24³
```

*(`UBPLightspeed.monad`, `wobble`, `sinkL`, `Yc`, `sigmaS`, `sinkLs`;
`monad_bounds`, `wobble_bounds`, `sinkL_bounds`, `Yc_bounds_tight`)*

### 8.2 P6 is a tautology

> **Theorem 10.** `MONAD / 13 = 1 + L`.  *(`UBPLightspeed.monad_div_thirteen`)*

Because `⌊MONAD⌋ = 13` *(`monad_floor`)*, `MONAD = 13 + WOBBLE`, and `L` is
*defined* as `WOBBLE/13`.  Setting `γ = MONAD/13` and reading off
`v/c = √(1 − 1/γ²) = 0.338878`
*(`UBPLightspeed.vOverC_bounds`: `0.338877 < v/c < 0.338878`)*
therefore defines a substrate velocity; it does not predict a measured one.
Listing it as an "EXACT IDENTITY" alongside empirical alignments overstates it.

### 8.3 The numerical alignments, re-measured

Reproduced by `substrate_lightspeed.py --constants` and proved in
`RequestProject/SubstrateConstants.lean`.

| Point | Formula | Value | Target | Relative error | Quoted | Lean |
|---|---|---|---|---|---|---|
| P2 | `169/WOBBLE` | 206.707543 | 206.7682830 | **0.02938 %** | 0.03 % ✓ | `muonRatio_error` |
| P7 | `220 − 83 + L` | 137.062891 | 137.035999084 | **0.01962 %** | 0.02 % ✓ | `alphaInv_error` |
| P8 | `1836 + 2L_s` | 1836.151986 | 1836.15267343 | **0.0000374 %** | 0.001 % (pessimistic) | `protonRatio_error` |
| P4 | `Y²·WOBBLE·24⁴·29⁴·hΔν_Cs/c²` | `9.108547×10⁻³¹ kg` | `9.1093837015×10⁻³¹` | **0.00919 %** | 0.007 % ✗ | `electronMass_error` |

**Correction.** The P4 residual is `9.19×10⁻⁵`, not `7.2×10⁻⁵`.  The synthesis
document's "Priority 1: the 0.007 % mass residual" should read **0.0092 %**.
This matters for the α²-correction hypothesis floated there: `α² = 5.325×10⁻⁵`,
so the residual is `1.726 α²`, not `1.35 α²`.  Neither is a clean coefficient;
the α² hypothesis is not supported by the corrected number either.

### 8.4 The common shape

Every alignment point has the form

```
    measured quantity  ≈  (dimensionless substrate number) × (SI-defined unit)
```

with the unit `1` for the ratios (P2, P7, P8) and `h·Δν_Cs/c²` for the mass
(P4).  `h·Δν_Cs/c²` is exact by SI definition and *is* dimensionally a mass
*(`UBPLightspeed.siMassUnit`, `mass_from_action_frequency_speed`)*, so P4 is
dimensionally legitimate.  The lightspeed chain is not, because there is no
corresponding SI-defined length in play — and none can be manufactured from `h`
and an energy (Theorem 3).

This is precisely the "productive reframing" the synthesis document proposes,
and this report supports it: **the substrate supplies dimensionless numbers; the
SI supplies the dimensions.**

---

## 9. A corrected version of the note

The following is `substrate_speed_of_light.md` rewritten so that every sentence
is defensible.  It keeps the entire construction; it changes only the claims.

> ### The substrate cell scale
>
> We encode chemical elements as 24-bit vectors in the Golay lattice and measure
> the geometric work of bond formation.  Fitting 114 element pairs against
> tabulated bond energies gives one unit of geometric work `≈ 190 kJ/mol`
> (close to, but not identical with, the Br–Br bond enthalpy of 193 kJ/mol).
>
> Dividing by the Avogadro number and applying the Planck relation converts that
> into a **time**:
>
> ```
>   E₁ = κ/N_A         = 3.1550 × 10⁻¹⁹ J     (the energy of a 630 nm photon)
>   τ  = h/E₁ = hN_A/κ = 2.1002 fs            (its optical period)
> ```
>
> `τ` is a genuine output of the calibration: an action and an energy determine
> a time.  They do **not** determine a length, so the speed of light cannot be
> derived this way; it must be supplied.  Supplying it converts the tick into a
> cell size:
>
> ```
>   ℓ_cell = 27 · c · τ = 27 λ₁ = 17.0 μm
> ```
>
> — the substrate cell is 27 wavelengths of the one-work-unit photon.  So the
> result of the calibration is a single new number, the **cell length**, and it
> is proportional to `1/κ`.
>
> What the substrate does predict, without any empirical anchor, is the
> **propagation-speed law**.  A region whose states carry TAX `T` needs `24+T`
> ticks per cell, so
>
> ```
>   v(T) = 27c/(24+T),     n(T) = (24+T)/27 .
> ```
>
> Causality forces the vacuum TAX to be the minimum of the tax spectrum, and on
> the Golay layer that minimum is realised uniquely by the octads, at
> `Tax = 8Y + 1 = 3.1174` — which is where the "24 bits + 3 TAX" comes from.
> The law is falsifiable: if the TAX is bounded by 24 then `n ≤ 16/9 = 1.778`,
> which water (`T = 11.99`), glass (`T = 17.0`) and sapphire (`T = 23.7`)
> satisfy and diamond (`T = 41.3`) does not.

---

## 10. Open questions, in order of value

1. **Fix the tax spectrum.**  Integer TAX (`n ≤ 1.778`) and codeword TAX
   (`n ≤ 1.235`) give different, both falsifiable, ceilings.  The model must
   commit before it can be tested.  This is the single highest-value next step,
   because it turns the idea into an experiment.
2. **Find an independent cell length** (referenced from §4.1).  Only this can make `c` an output.  It
   would need a substrate quantity with the dimension of length that is not
   built from `c` — for example a predicted absorption or scattering length in
   a real medium.  Absent that, the correct claim is "the substrate calibrates
   to a 17 μm cell", not "the substrate derives `c`".
3. **Re-run the `κ` fit and publish its uncertainty.**  Every downstream number
   is exactly proportional to `1/κ`, so a `±5 %` fit uncertainty is a `±5 %`
   uncertainty on the cell length.  The note quotes `17.0 μm` to three
   significant figures with no error bar.
4. **Re-do the P4 residual hunt with the corrected `9.19×10⁻⁵`** (see §8.3).
5. **Drop P6 from the alignment table**, or relabel it "definition" rather than
   "exact identity" — it is `MONAD = 13 + WOBBLE` restated.

---

## 11. Index of machine-checked statements

`RequestProject/Lightspeed.lean` and `RequestProject/SubstrateConstants.lean`
build with no `sorry` and depend only on `propext`, `Classical.choice`,
`Quot.sound`.

| Statement | Name |
|---|---|
| `h·N_A` exact | `molarPlanck_eq` |
| `τ = h N_A/κ` | `tick_eq` |
| `E₁, τ, T_cell, ℓ_cell, λ₁` numerical values | `workEnergy_bounds`, `tick_bounds`, `cellDuration_bounds`, `cellLength_bounds`, `workWavelength_bounds` |
| cell = `(24+T)` wavelengths | `cellLength_eq_wavelengths` |
| **`c` is recovered identically** | `cellLength_div_cellDuration`, `substrate_c_is_circular` |
| anchor covariance | `tick_scale`, `cellLength_scale` |
| dimensionless ⇒ not `c` | `dim_prod_of_dimensionless`, `c_not_dimensionless` |
| **no speed from (action, energy)** | `speed_not_from_action_and_energy` |
| but a time, yes | `time_from_action_and_energy` |
| length + time ⇒ speed | `speed_from_length_and_time` |
| `n = c/v`, `n(3)=1`, `n(8)=32/27` | `refIndex_mul_signalSpeed`, `refIndex_self`, `refIndex_tax_eight` |
| **causality ⟺ `T ≥ T₀`** | `signalSpeed_le_c_iff` |
| `n` monotone, `n ≤ 16/9` | `refIndex_strictMono`, `refIndex_le_of_tax_le` |
| `Y = π/(π²+2)`, value | `Yc_eq`, `Yc_bounds`, `Yc_bounds_tight` |
| **octads minimise the codeword tax** | `octad_min_tax`, `octad_min_tax_strict` |
| `Tax(octad) = 8Y+1 ∈ (3,4)` | `octadTax_eq`, `octadTax_floor_three` |
| exact tick budget `27.1174` | `exactTicksPerCell_bounds` |
| class A cheaper than octads (P5 correction) | `classA_tax_lt_octad_tax`, `minimalVectorTax_values` |
| `MONAD = π φ e`, `⌊MONAD⌋ = 13` | `monad_bounds`, `monad_floor` |
| **`MONAD/13 = 1 + L`** (P6) | `monad_div_thirteen` |
| `v/c = 0.338878` | `vOverC_bounds` |
| P2 error `0.0293–0.0294 %` | `muonRatio_error` |
| P7 error `0.01962–0.01963 %` | `alphaInv_error` |
| P8 error `3.74×10⁻⁷` | `protonRatio_error` |
| **P4 error `0.0090–0.0093 %`** (not 0.007 %) | `electronMass_error` |
| `h Δν_Cs/c²` is a mass | `mass_from_action_frequency_speed` |
