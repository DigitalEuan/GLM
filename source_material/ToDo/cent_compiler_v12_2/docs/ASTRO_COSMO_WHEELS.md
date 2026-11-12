# W26/W27 — astrophysics and cosmology wheels

W26 and W27 turn the astrophysics/cosmology intent in
[`expansion/02_Expanding_Wheels.md`](../expansion/02_Expanding_Wheels.md)
into declared wheel data. They contain only algebraic monomial relations,
exact dimension checks and negative controls. They do **not** assert a measured
star, a measured cosmological parameter or a full Lambda-CDM model.

## Sources and conventions

| Wheel | Equation | Source | Status |
|---|---|---|---|
| W26 | `L = 4πR²σT⁴` | [Luminosity and the Stefan-Boltzmann law](https://astro.unl.edu/newRTs/Luminosity/Background/HR_Luminosity1.html) | The wheel declares `L = σR²T⁴`; the conventional `4π` is omitted and labelled `model_convention`. |
| W26 | `r_s = 2GM/c²` | [NASA: The Anatomy of Black Holes](https://imagine.gsfc.nasa.gov/educators/blackholes/imagine/page22.html) | Exact coefficient retained. |
| W26 | `v² = GM/r` | [OpenStax/LibreTexts: Satellite Orbits and Energy](https://phys.libretexts.org/Bookshelves/University_Physics/University_Physics_%28OpenStax%29/Book%3A_University_Physics_I_-_Mechanics_Sound_Oscillations_and_Waves_%28OpenStax%29/13%3A_Gravitation/13.05%3A_Satellite_Orbits_and_Energy) | Circular-orbit relation; no additional constant. |
| W26 | `T_H = ħc³/(8πGMk_B)` | [Hawking, Nature 248, 30–31 (1974)](https://doi.org/10.1038/248030a0) | The wheel declares `T_H = ħc³/(GMk_B)`; the conventional `8π` is omitted and labelled `model_convention`. |
| W27 | `v = H₀d` | [Hogg, Distance measures in cosmology](https://ned.ipac.caltech.edu/level5/Hogg/Hogg2.html) | Local/low-redshift Hubble-flow form; no relativistic correction or peculiar velocity is declared. |
| W27 | `ρ_c = 3H₀²/(8πG)` | [Weinberg cosmology notes](https://www.astronomy.ohio-state.edu/weinberg.21/A8873/notes4.pdf) | The wheel declares `ρ_c = H₀²/G`; the dimensionless `3/(8π)` is omitted and labelled `model_convention`. |
| W27 | `t_H = 1/H₀` | [Hogg, Distance measures in cosmology](https://ned.ipac.caltech.edu/level5/Hogg/Hogg2.html) | Definition of the Hubble time. |
| W27 | `D_H = c/H₀` | [Hogg, Distance measures in cosmology](https://ned.ipac.caltech.edu/level5/Hogg/Hogg2.html) | Definition of the Hubble horizon. |

The constant conventions are those published by the
[PDG 2025 review of astrophysical constants](https://pdg.lbl.gov/2025/reviews/rpp2025-rev-astrophysical-constants.pdf).
The publisher DOI for Carroll & Ostlie,
[*An Introduction to Modern Astrophysics*, 2nd edition](https://doi.org/10.1017/9781108380980),
is retained as general textbook provenance. No numerical constant is inserted
into a wheel axiom; the symbols and their exact exponent vectors are the data.

## Exact dimensions

The axes are exactly `["L", "M", "T", "I", "H", "N", "J", "A"]`.

### W26 — Astrophysics & Stellar Structure

| Quantity | Exact exponents |
|---|---|
| `luminosity` | `L² M T⁻³` |
| `stefan_boltzmann_constant` | `M T⁻³ H⁻⁴` |
| `radius` | `L` |
| `temperature` | `H` |
| `schwarzschild_radius` | `L` |
| `gravitational_constant` | `L³ M⁻¹ T⁻²` |
| `mass` | `M` |
| `speed_of_light` | `L T⁻¹` |
| `orbital_velocity` | `L T⁻¹` |
| `orbital_radius` | `L` |
| `hawking_temperature` | `H` |
| `hbar` | `L² M T⁻¹` |
| `boltzmann_constant` | `L² M T⁻² H⁻¹` |

### W27 — Cosmology & Cosmic Expansion

| Quantity | Exact exponents |
|---|---|
| `recession_velocity` | `L T⁻¹` |
| `hubble_constant` | `T⁻¹` |
| `distance` | `L` |
| `critical_density` | `L⁻³ M` |
| `gravitational_constant` | `L³ M⁻¹ T⁻²` |
| `hubble_time` | `T` |
| `horizon_distance` | `L` |
| `speed_of_light` | `L T⁻¹` |

All rows are checked by `cent axioms` and by the case regression. Unknown
dimensions remain unknown; none are inferred from a name or a text match.

## Cases and negative controls

Both wheels declare five cases. Four are algebraic inverses or restatements of
a declared axiom, and one is a negative control with a deliberately broken
exponent or operation.

| Case | Expectation | Status |
|---|---|---|
| `W26-01` | `σ = L/(R²T⁴)` is dimensionally consistent and derivable | `model_convention` (omitted `4π`) |
| `W26-02` | `M = r_s c²/(2G)` is consistent and derivable | `physically_supported` |
| `W26-03` | `r = GM/v²` is consistent and derivable | `physically_supported` |
| `W26-04` | `M = ħc³/(Gk_BT_H)` is consistent and derivable | `model_convention` (omitted `8π`) |
| `W26-N1` | `L = σR²/T⁴` is not consistent or derivable | `negative_control` |
| `W27-01` | `H₀ = v/d` is consistent and derivable | `model_convention` (local Hubble flow) |
| `W27-02` | `ρ_c = H₀²/G` is consistent and derivable | `model_convention` (omitted `3/(8π)`) |
| `W27-03` | `t_H = 1/H₀` is consistent and derivable | `physically_supported` |
| `W27-04` | `D_H = c/H₀` is consistent and derivable | `physically_supported` |
| `W27-N1` | `v = H₀/d` is not consistent or derivable | `negative_control` |

The exact case regression reports **153/153** dimensional agreement and
**153/153** derivability agreement. The negative controls are expected to fail
both checks; they are not counted as passes of a physical law.

## Cross-domain junctions

Ten declared identities connect the new wheels to existing quantities. A
junction is an explicit wheel-local identity, not a claim that two similar
names are interchangeable without it.

| New quantity | Existing quantity | Reason |
|---|---|---|
| `W26.mass` | `W17.source_mass` | stellar mass is the gravitational source mass |
| `W26.gravitational_constant` | `W17.gravitational_constant` | the same gravitational constant |
| `W26.temperature` | `W8.temperature` | photospheric temperature is thermodynamic temperature |
| `W26.luminosity` | `W15.power` | bolometric luminosity is radiant power in the power channel |
| `W27.distance` | `W11.length` | cosmological distance is a length in the uniform-motion channel |
| `W27.recession_velocity` | `W11.velocity` | cosmological recession speed is a velocity |
| `W27.hubble_time` | `W11.time` | the Hubble time is a time interval |
| `W27.critical_density` | `W12.density` | critical density is a mass density |
| `W27.speed_of_light` | `W19.speed_of_light` | the same speed of light |
| `W27.gravitational_constant` | `W17.gravitational_constant` | the same gravitational constant |

These identities make W26/W27 reachable from the existing thermal, power,
motion, density, gravity and electromagnetic wheels. They do not merge
`luminosity` with `power`, or `critical_density` with `density`, outside the
declared graph paths.

## Measured coverage

At the current gate:

- **39 wheels**, **98 axioms**, **153 cases**, **230** wheel-local quantity
  nodes and **65** exact dimension nodes.
- **366** two-input spokes. W27 contributes **30**; W26 contributes **0**
  because its four laws each have at least three non-target inputs under the
  current spoke definition. This is a measured property, not a fabricated
  formula or a hidden pass.
- **57 declared junctions**, of which **54** resolve to graph edges. The three
  existing endpoint gaps remain explicit.
- **824/824** checks pass across the seventeen-suite canonical gate.

## Explicit gaps

- W26/W27 are algebraic relations, not a stellar-structure solver, a
  cosmological parameter fit or a measured-data compilation.
- The omitted `4π`, `8π` and `3/(8π)` factors are documented conventions. A
  future wheel that needs those factors should declare them explicitly rather
  than silently changing these axioms.
- W26 has no two-input spoke. Its relations are still available to the exact
  graph, the case regression and cross-domain derivations.
- W30/W31 remain reserved with no declared domain content. They are not filled
  by analogy or by an empty table.
