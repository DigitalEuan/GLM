module

public import Mathlib
public import RequestProject.GLM.ConnectedMachine

/-!
# The cent compiler's wheels: balance, derivations and refusals

*Created 31 October 2026 (repository check; the intake of cent_compiler_v12, directive D22).*
The formal half of `studies/CENT_WHEELS_STUDY.md` (§5). The supplied item
`source_material/ToDo/cent_compiler_v12` carries 31 formula wheels; this file proves, for the
wheels absorbed into `src/glm_universal/wheels/cent_wheels.py`, the finite facts their absorption
rests on.

A relation `L = R` is the vector of exponents of `L / R` (quantities, then the primes of the
coefficient), as `wheels.relation_vector` writes it; exponents are rational, so a fractional
power `(…)^(1/2)` is read exactly. A formula is derivable when its vector lies in the rational
span of the axioms' vectors (`GLM.ConnectedMachine.Derivable`).

* `dimL D` is a wheel's dimension map: a relation vector `v` goes to `∑ j, v j • D j`, the
  difference of the exponent vectors (over `L M T I H N J A`) of its two sides. An axiom's two
  sides have equal exponent vectors exactly when `dimL D` sends it to `0`. Each wheel proves
  `axioms_balanced`, or, where an axiom has a residual, states it exactly (`axiom_i_residual`):
  the angle convention is the repository's — SI7 decides (the first seven axes), the angle axis
  `A` is recorded.
* `derivable_of_combo` — a question is derivable when it equals an explicit rational combination
  of the axioms (the certificate, checked coordinate by coordinate).
* `not_derivable_of_dot` — a question is not derivable when an explicit rational functional
  vanishes on every axiom and not on it (`GLM.ConnectedMachine.not_derivable_of_functional`).

Sections: the absorbed wheels W16–W25, W28, W29, W32–W34 (each with its cases and the
questions of the study's §4 attributed to it, as corrected under the study's rule R); the W4 and
W6 additions; the W11–W15 axioms and their 14 supplied cases; and the supplied axioms that fail at
SI7 on their own tables (`Supplied`), each with its exact residual. `tests/test_cent_wheels.py`
reads every vector, table, certificate and verdict below and re-checks it against the Python in
exact arithmetic. Everything here is formal (`norm_num`; no `native_decide`).
-/

@[expose] public section

namespace GLM.CentWheels

open GLM.ConnectedMachine

/-! ## The dimension map and the two certificates -/

/-- The dimension map of a table `D` (one row of exponents over `L M T I H N J A` per
coordinate). -/
def dimL {n : ℕ} (D : Fin n → Fin 8 → ℚ) : (Fin n → ℚ) →ₗ[ℚ] (Fin 8 → ℚ) where
  toFun v := ∑ j, v j • D j
  map_add' x y := by simp [add_smul, Finset.sum_add_distrib]
  map_smul' c x := by simp [smul_smul, Finset.smul_sum]

theorem dimL_apply {n : ℕ} (D : Fin n → Fin 8 → ℚ) (v : Fin n → ℚ) :
    dimL D v = ∑ j, v j • D j := rfl

/-- The functional `v ↦ ∑ j, w j * v j`. -/
def dotL {n : ℕ} (w : Fin n → ℚ) : (Fin n → ℚ) →ₗ[ℚ] ℚ where
  toFun v := ∑ j, w j * v j
  map_add' x y := by simp [mul_add, Finset.sum_add_distrib]
  map_smul' c x := by
    simp only [Pi.smul_apply, smul_eq_mul, RingHom.id_apply, Finset.mul_sum]
    exact Finset.sum_congr rfl fun j _ => by ring

/-- **A rational combination of the axioms is derivable.** -/
theorem derivable_of_combo {n k : ℕ} (ax : Fin k → Fin n → ℚ) (c : Fin k → ℚ)
    (v : Fin n → ℚ) (h : v = ∑ i, c i • ax i) : Derivable (Set.range ax) v := by
  rw [h, Derivable]
  exact Submodule.sum_mem _ fun i _ => Submodule.smul_mem _ _ (Submodule.subset_span ⟨i, rfl⟩)

/-- **A separating functional refuses.** -/
theorem not_derivable_of_dot {n k : ℕ} (ax : Fin k → Fin n → ℚ) (w v : Fin n → ℚ)
    (hax : ∀ i, ∑ j, w j * ax i j = 0) (hv : ∑ j, w j * v j ≠ 0) :
    ¬ Derivable (Set.range ax) v :=
  not_derivable_of_functional (dotL w) (by rintro _ ⟨i, rfl⟩; exact hax i) hv

/-! ## The absorbed wheels -/

/-! ### W16 — Magnetic flux and induction -/

namespace W16

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["area", "current", "emf", "flux", "inductance", "magnetic_field", "time", "#2"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: flux = magnetic_field * area
-- 1: flux = inductance * current
-- 2: emf = flux / time
def ax : Fin 3 → Fin 8 → ℚ :=
  ![![-1, 0, 0, 1, 0, -1, 0, 0],
   ![0, -1, 0, 1, -1, 0, 0, 0],
   ![0, 0, 1, -1, 0, 0, 1, 0]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 8 → Fin 8 → ℚ :=
  ![![2, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 1, 0, 0, 0, 0],
   ![2, 1, -3, -1, 0, 0, 0, 0],
   ![2, 1, -2, -1, 0, 0, 0, 0],
   ![2, 1, -2, -2, 0, 0, 0, 0],
   ![0, 1, -2, -1, 0, 0, 0, 0],
   ![0, 0, 1, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W16-01`: magnetic_field = flux / area -/
theorem q_W16_01 : Derivable (Set.range ax) ![1, 0, 0, -1, 0, 1, 0, 0] :=
  derivable_of_combo ax ![-1, 0, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W16-02`: inductance = flux / current -/
theorem q_W16_02 : Derivable (Set.range ax) ![0, 1, 0, -1, 1, 0, 0, 0] :=
  derivable_of_combo ax ![0, -1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W16-03`: emf = flux / time -/
theorem q_W16_03 : Derivable (Set.range ax) ![0, 0, 1, -1, 0, 0, 1, 0] :=
  derivable_of_combo ax ![0, 0, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W16-N1`: flux = magnetic_field / area -/
theorem q_W16_N1 : ¬ Derivable (Set.range ax) ![1, 0, 0, 1, 0, -1, 0, 0] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 0, -1, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H16-1`: emf = magnetic_field * area / time -/
theorem q_H16_1 : Derivable (Set.range ax) ![-1, 0, 1, 0, 0, -1, 1, 0] :=
  derivable_of_combo ax ![1, 0, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H16-2`: inductance * current = magnetic_field * area -/
theorem q_H16_2 : Derivable (Set.range ax) ![-1, 1, 0, 0, 1, -1, 0, 0] :=
  derivable_of_combo ax ![1, -1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H16-3`: emf = inductance * current / time -/
theorem q_H16_3 : Derivable (Set.range ax) ![0, -1, 1, 0, -1, 0, 1, 0] :=
  derivable_of_combo ax ![0, 1, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H16-F`: flux = 2 * magnetic_field * area -/
theorem q_H16_F : ¬ Derivable (Set.range ax) ![-1, 0, 0, 1, 0, -1, 0, -1] :=
  not_derivable_of_dot ax ![0, 0, 0, 0, 0, 0, 0, 1] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W16

/-! ### W17 — Gravitation and orbital mechanics -/

namespace W17

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["distance", "gravitational_constant", "period", "source_mass", "surface_gravity", "#2"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: surface_gravity = gravitational_constant * source_mass / distance^2
-- 1: period^2 = distance^3 / (gravitational_constant * source_mass)
def ax : Fin 2 → Fin 6 → ℚ :=
  ![![2, -1, 0, -1, 1, 0],
   ![-3, 1, 2, 1, 0, 0]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 6 → Fin 8 → ℚ :=
  ![![1, 0, 0, 0, 0, 0, 0, 0],
   ![3, -1, -2, 0, 0, 0, 0, 0],
   ![0, 0, 1, 0, 0, 0, 0, 0],
   ![0, 1, 0, 0, 0, 0, 0, 0],
   ![1, 0, -2, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W17-01`: gravitational_constant = surface_gravity * distance^2 / source_mass -/
theorem q_W17_01 : Derivable (Set.range ax) ![-2, 1, 0, 1, -1, 0] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W17-02`: source_mass = surface_gravity * distance^2 / gravitational_constant -/
theorem q_W17_02 : Derivable (Set.range ax) ![-2, 1, 0, 1, -1, 0] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W17-03`: period^2 = distance^3 / (gravitational_constant * source_mass) -/
theorem q_W17_03 : Derivable (Set.range ax) ![-3, 1, 2, 1, 0, 0] :=
  derivable_of_combo ax ![0, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W17-N1`: surface_gravity = distance^2 / (gravitational_constant * source_mass) -/
theorem q_W17_N1 : ¬ Derivable (Set.range ax) ![-2, 1, 0, 1, 1, 0] :=
  not_derivable_of_dot ax ![1, 3, 0, 0, 1, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H17-1`: period^2 = distance / surface_gravity -/
theorem q_H17_1 : Derivable (Set.range ax) ![-1, 0, 2, 0, 1, 0] :=
  derivable_of_combo ax ![1, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H17-2`: gravitational_constant * source_mass = surface_gravity * distance^2 -/
theorem q_H17_2 : Derivable (Set.range ax) ![-2, 1, 0, 1, -1, 0] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H17-F`: period^2 = 2 * distance / surface_gravity -/
theorem q_H17_F : ¬ Derivable (Set.range ax) ![-1, 0, 2, 0, 1, -1] :=
  not_derivable_of_dot ax ![0, 0, 0, 0, 0, 1] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W17

/-! ### W18 — Ideal gas law -/

namespace W18

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["amount", "gas_constant", "pressure", "temperature", "volume", "#2"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: pressure * volume = amount * gas_constant * temperature
def ax : Fin 1 → Fin 6 → ℚ :=
  ![![-1, -1, 1, -1, 1, 0]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 6 → Fin 8 → ℚ :=
  ![![0, 0, 0, 0, 0, 1, 0, 0],
   ![2, 1, -2, 0, -1, -1, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 1, 0, 0, 0],
   ![3, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i; (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W18-01`: volume = amount * gas_constant * temperature / pressure -/
theorem q_W18_01 : Derivable (Set.range ax) ![-1, -1, 1, -1, 1, 0] :=
  derivable_of_combo ax ![1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W18-02`: temperature = pressure * volume / (amount * gas_constant) -/
theorem q_W18_02 : Derivable (Set.range ax) ![1, 1, -1, 1, -1, 0] :=
  derivable_of_combo ax ![-1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W18-03`: amount = pressure * volume / (gas_constant * temperature) -/
theorem q_W18_03 : Derivable (Set.range ax) ![1, 1, -1, 1, -1, 0] :=
  derivable_of_combo ax ![-1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W18-N1`: pressure = amount * gas_constant * temperature * volume -/
theorem q_W18_N1 : ¬ Derivable (Set.range ax) ![-1, -1, 1, -1, -1, 0] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 1, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H18-1`: pressure = amount * gas_constant * temperature / volume -/
theorem q_H18_1 : Derivable (Set.range ax) ![-1, -1, 1, -1, 1, 0] :=
  derivable_of_combo ax ![1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H18-2`: gas_constant = pressure * volume / (amount * temperature) -/
theorem q_H18_2 : Derivable (Set.range ax) ![1, 1, -1, 1, -1, 0] :=
  derivable_of_combo ax ![-1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H18-F`: pressure * volume = 2 * amount * gas_constant * temperature -/
theorem q_H18_F : ¬ Derivable (Set.range ax) ![-1, -1, 1, -1, 1, -1] :=
  not_derivable_of_dot ax ![0, 0, 0, 0, 0, 1] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W18

/-! ### W19 — Electromagnetic waves -/

namespace W19

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["electric_field", "magnetic_field", "permeability", "permittivity", "speed_of_light"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: speed_of_light^2 = 1 / (permittivity * permeability)
-- 1: electric_field = speed_of_light * magnetic_field
def ax : Fin 2 → Fin 5 → ℚ :=
  ![![0, 0, 1, 1, 2],
   ![1, -1, 0, 0, -1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 5 → Fin 8 → ℚ :=
  ![![1, 1, -3, -1, 0, 0, 0, 0],
   ![0, 1, -2, -1, 0, 0, 0, 0],
   ![1, 1, -2, -2, 0, 0, 0, 0],
   ![-3, -1, 4, 2, 0, 0, 0, 0],
   ![1, 0, -1, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W19-01`: permittivity * permeability = 1 / speed_of_light^2 -/
theorem q_W19_01 : Derivable (Set.range ax) ![0, 0, 1, 1, 2] :=
  derivable_of_combo ax ![1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W19-02`: magnetic_field = electric_field / speed_of_light -/
theorem q_W19_02 : Derivable (Set.range ax) ![-1, 1, 0, 0, 1] :=
  derivable_of_combo ax ![0, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W19-03`: permittivity = 1 / (permeability * speed_of_light^2) -/
theorem q_W19_03 : Derivable (Set.range ax) ![0, 0, 1, 1, 2] :=
  derivable_of_combo ax ![1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W19-N1`: speed_of_light = permittivity * permeability -/
theorem q_W19_N1 : ¬ Derivable (Set.range ax) ![0, 0, -1, -1, 1] :=
  not_derivable_of_dot ax ![1, 0, -2, 0, 1] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H19-1`: electric_field^2 = magnetic_field^2 / (permittivity * permeability) -/
theorem q_H19_1 : Derivable (Set.range ax) ![2, -2, 1, 1, 0] :=
  derivable_of_combo ax ![1, 2] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H19-2`: electric_field = magnetic_field / (permittivity * permeability)^(1/2) -/
theorem q_H19_2 : Derivable (Set.range ax) ![1, -1, 1/2, 1/2, 0] :=
  derivable_of_combo ax ![1/2, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H19-F`: electric_field = magnetic_field * speed_of_light^2 -/
theorem q_H19_F : ¬ Derivable (Set.range ax) ![1, -1, 0, 0, -2] :=
  not_derivable_of_dot ax ![1, 0, -2, 0, 1] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W19

/-! ### W20 — Elasticity & Continuum Mechanics -/

namespace W20

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["area_moment_inertia", "bending_moment", "flexural_rigidity", "radius_curvature", "strain", "stress", "youngs_modulus"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: stress = youngs_modulus * strain
-- 1: bending_moment = youngs_modulus * area_moment_inertia / radius_curvature
-- 2: flexural_rigidity = youngs_modulus * area_moment_inertia
def ax : Fin 3 → Fin 7 → ℚ :=
  ![![0, 0, 0, 0, -1, 1, -1],
   ![-1, 1, 0, 1, 0, 0, -1],
   ![-1, 0, 1, 0, 0, 0, -1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 7 → Fin 8 → ℚ :=
  ![![4, 0, 0, 0, 0, 0, 0, 0],
   ![2, 1, -2, 0, 0, 0, 0, 0],
   ![3, 1, -2, 0, 0, 0, 0, 0],
   ![1, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W20-01`: youngs_modulus = stress / strain -/
theorem q_W20_01 : Derivable (Set.range ax) ![0, 0, 0, 0, 1, -1, 1] :=
  derivable_of_combo ax ![-1, 0, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W20-02`: strain = stress / youngs_modulus -/
theorem q_W20_02 : Derivable (Set.range ax) ![0, 0, 0, 0, 1, -1, 1] :=
  derivable_of_combo ax ![-1, 0, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W20-03`: radius_curvature = youngs_modulus * area_moment_inertia / bending_moment -/
theorem q_W20_03 : Derivable (Set.range ax) ![-1, 1, 0, 1, 0, 0, -1] :=
  derivable_of_combo ax ![0, 1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W20-N1`: stress = youngs_modulus / strain -/
theorem q_W20_N1 : ¬ Derivable (Set.range ax) ![0, 0, 0, 0, 1, 1, -1] :=
  not_derivable_of_dot ax ![0, 0, 0, 0, 1, 1, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H20-1`: bending_moment = flexural_rigidity / radius_curvature -/
theorem q_H20_1 : Derivable (Set.range ax) ![0, 1, -1, 1, 0, 0, 0] :=
  derivable_of_combo ax ![0, 1, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H20-2`: flexural_rigidity = stress * area_moment_inertia / strain -/
theorem q_H20_2 : Derivable (Set.range ax) ![-1, 0, 1, 0, 1, -1, 0] :=
  derivable_of_combo ax ![-1, 0, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H20-F`: stress = youngs_modulus -/
theorem q_H20_F : ¬ Derivable (Set.range ax) ![0, 0, 0, 0, 0, 1, -1] :=
  not_derivable_of_dot ax ![0, 0, 0, 0, 1, 1, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W20

/-! ### W21 — Fracture Mechanics & Plasticity -/

namespace W21

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["crack_length", "dimensionless_factor", "fracture_toughness", "stress", "stress_intensity_factor", "surface_energy", "youngs_modulus", "#2", "#3", "#5", "#7", "#127", "#7853"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: fracture_toughness = (2 * youngs_modulus * surface_energy / crack_length)^(1/2)
-- 1: stress_intensity_factor = dimensionless_factor * stress * crack_length^(1/2)
def ax : Fin 2 → Fin 13 → ℚ :=
  ![![1/2, 0, 1, 0, 0, -1/2, -1/2, -1/2, 0, 0, 0, 0, 0],
   ![-1/2, -1, 0, -1, 1, 0, 0, 0, 0, 0, 0, 0, 0]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 13 → Fin 8 → ℚ :=
  ![![1, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0],
   ![-1/2, 1, -2, 0, 0, 0, 0, 0],
   ![0, 1, -2, 0, 0, 0, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W21-01`: surface_energy = fracture_toughness^2 * crack_length / (2 * youngs_modulus) -/
theorem q_W21_01 : Derivable (Set.range ax) ![-1, 0, -2, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0] :=
  derivable_of_combo ax ![-2, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W21-02`: crack_length = (stress_intensity_factor / (dimensionless_factor * stress))^2 -/
theorem q_W21_02 : Derivable (Set.range ax) ![1, 2, 0, 2, -2, 0, 0, 0, 0, 0, 0, 0, 0] :=
  derivable_of_combo ax ![0, -2] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W21-03`: stress = stress_intensity_factor / (dimensionless_factor * crack_length^(1/2)) -/
theorem q_W21_03 : Derivable (Set.range ax) ![1/2, 1, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0] :=
  derivable_of_combo ax ![0, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W21-N1`: fracture_toughness = stress / crack_length -/
theorem q_W21_N1 : ¬ Derivable (Set.range ax) ![1, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0] :=
  not_derivable_of_dot ax ![0, 1, 0, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F21-ax1`: fracture_toughness = (2 * youngs_modulus * surface_energy / (314159265 * crack_length))^(1/2) -/
theorem q_F21_ax1 : ¬ Derivable (Set.range ax) ![1/2, 0, 1, 0, 0, -1/2, -1/2, -1/2, 1, 1/2, 1/2, 1/2, 1/2] :=
  not_derivable_of_dot ax ![0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H21-1`: youngs_modulus = fracture_toughness^2 * crack_length / (2 * surface_energy) -/
theorem q_H21_1 : Derivable (Set.range ax) ![-1, 0, -2, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0] :=
  derivable_of_combo ax ![-2, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H21-2`: stress_intensity_factor^2 = dimensionless_factor^2 * stress^2 * crack_length -/
theorem q_H21_2 : Derivable (Set.range ax) ![-1, -2, 0, -2, 2, 0, 0, 0, 0, 0, 0, 0, 0] :=
  derivable_of_combo ax ![0, 2] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H21-F`: fracture_toughness = youngs_modulus -/
theorem q_H21_F : ¬ Derivable (Set.range ax) ![0, 0, 1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 0] :=
  not_derivable_of_dot ax ![2, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W21

/-! ### W22 — Chemical Kinetics & Transport -/

namespace W22

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["concentration", "concentration_gradient", "diffusion_coefficient", "diffusion_flux", "pre_exponential_factor", "rate_constant", "reaction_rate"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: reaction_rate = rate_constant * concentration
def ax : Fin 1 → Fin 7 → ℚ :=
  ![![-1, 0, 0, 0, 0, -1, 1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 7 → Fin 8 → ℚ :=
  ![![-3, 0, 0, 0, 0, 1, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, -1, 0, 0, 0, 0, 0],
   ![0, 0, -1, 0, 0, 0, 0, 0],
   ![-3, 0, -1, 0, 0, 1, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i; (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W22-01`: rate_constant = reaction_rate / concentration -/
theorem q_W22_01 : Derivable (Set.range ax) ![1, 0, 0, 0, 0, 1, -1] :=
  derivable_of_combo ax ![-1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W22-02`: concentration = reaction_rate / rate_constant -/
theorem q_W22_02 : Derivable (Set.range ax) ![1, 0, 0, 0, 0, 1, -1] :=
  derivable_of_combo ax ![-1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W22-03`: diffusion_coefficient = diffusion_flux / concentration_gradient -/
theorem q_W22_03 : ¬ Derivable (Set.range ax) ![0, 1, 1, -1, 0, 0, 0] :=
  not_derivable_of_dot ax ![0, 1, 0, 0, 0, 0, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `W22-N1`: reaction_rate = rate_constant / concentration -/
theorem q_W22_N1 : ¬ Derivable (Set.range ax) ![1, 0, 0, 0, 0, -1, 1] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 0, -1, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F22-ax2`: rate_constant = pre_exponential_factor * concentration / rate_constant -/
theorem q_F22_ax2 : ¬ Derivable (Set.range ax) ![-1, 0, 0, 0, -1, 2, 0] :=
  not_derivable_of_dot ax ![0, 0, 0, 0, 1, 0, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H22-F`: reaction_rate = rate_constant * concentration^2 -/
theorem q_H22_F : ¬ Derivable (Set.range ax) ![-2, 0, 0, 0, 0, -1, 1] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 0, -1, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W22

/-! ### W23 — Electrochemistry & Energy Storage -/

namespace W23

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["charge", "current", "faraday_constant", "mass", "molar_mass", "time", "#2"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: mass = charge * molar_mass / faraday_constant
-- 1: charge = current * time
def ax : Fin 2 → Fin 7 → ℚ :=
  ![![-1, 0, 1, 1, -1, 0, 0],
   ![1, -1, 0, 0, 0, -1, 0]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 7 → Fin 8 → ℚ :=
  ![![0, 0, 1, 1, 0, 0, 0, 0],
   ![0, 0, 0, 1, 0, 0, 0, 0],
   ![0, 0, 1, 1, 0, -1, 0, 0],
   ![0, 1, 0, 0, 0, 0, 0, 0],
   ![0, 1, 0, 0, 0, -1, 0, 0],
   ![0, 0, 1, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W23-01`: molar_mass = mass * faraday_constant / charge -/
theorem q_W23_01 : Derivable (Set.range ax) ![1, 0, -1, -1, 1, 0, 0] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W23-02`: charge = mass * faraday_constant / molar_mass -/
theorem q_W23_02 : Derivable (Set.range ax) ![1, 0, -1, -1, 1, 0, 0] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W23-03`: current = charge / time -/
theorem q_W23_03 : Derivable (Set.range ax) ![-1, 1, 0, 0, 0, 1, 0] :=
  derivable_of_combo ax ![0, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W23-N1`: mass = charge / faraday_constant -/
theorem q_W23_N1 : ¬ Derivable (Set.range ax) ![-1, 0, 1, 1, 0, 0, 0] :=
  not_derivable_of_dot ax ![1, 1, 0, 0, -1, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H23-1`: mass = current * time * molar_mass / faraday_constant -/
theorem q_H23_1 : Derivable (Set.range ax) ![0, -1, 1, 1, -1, -1, 0] :=
  derivable_of_combo ax ![1, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H23-2`: time = mass * faraday_constant / (current * molar_mass) -/
theorem q_H23_2 : Derivable (Set.range ax) ![0, 1, -1, -1, 1, 1, 0] :=
  derivable_of_combo ax ![-1, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H23-F`: mass = 2 * charge * molar_mass / faraday_constant -/
theorem q_H23_F : ¬ Derivable (Set.range ax) ![-1, 0, 1, 1, -1, 0, -1] :=
  not_derivable_of_dot ax ![0, 0, 0, 0, 0, 0, 1] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W23

/-! ### W24 — Semiconductor Device Physics -/

namespace W24

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["carrier_concentration", "current", "debye_length", "diffusion_constant", "mobility", "permittivity", "saturation_current", "thermal_voltage", "voltage", "#2"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: saturation_current = current
-- 1: diffusion_constant = mobility * thermal_voltage
def ax : Fin 2 → Fin 10 → ℚ :=
  ![![0, -1, 0, 0, 0, 0, 1, 0, 0, 0],
   ![0, 0, 0, 1, -1, 0, 0, -1, 0, 0]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 10 → Fin 8 → ℚ :=
  ![![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 1, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![2, 0, -1, 0, 0, 0, 0, 0],
   ![0, -1, 2, 1, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 1, 0, 0, 0, 0],
   ![2, 1, -3, -1, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W24-01`: mobility = diffusion_constant / thermal_voltage -/
theorem q_W24_01 : Derivable (Set.range ax) ![0, 0, 0, -1, 1, 0, 0, 1, 0, 0] :=
  derivable_of_combo ax ![0, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W24-02`: thermal_voltage = diffusion_constant / mobility -/
theorem q_W24_02 : Derivable (Set.range ax) ![0, 0, 0, -1, 1, 0, 0, 1, 0, 0] :=
  derivable_of_combo ax ![0, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W24-03`: debye_length = (permittivity * thermal_voltage / (2 * carrier_concentration))^(1/2) -/
theorem q_W24_03 : ¬ Derivable (Set.range ax) ![1/2, 0, 1, 0, 0, -1/2, 0, -1/2, 0, 1/2] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 0, 0, 0, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `W24-N1`: current = saturation_current / voltage -/
theorem q_W24_N1 : ¬ Derivable (Set.range ax) ![0, 1, 0, 0, 0, 0, -1, 0, 1, 0] :=
  not_derivable_of_dot ax ![0, 0, 0, 0, 0, 0, 0, 0, 1, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H24-F`: diffusion_constant = mobility / thermal_voltage -/
theorem q_H24_F : ¬ Derivable (Set.range ax) ![0, 0, 0, 1, -1, 0, 0, 1, 0, 0] :=
  not_derivable_of_dot ax ![0, 0, 0, 1, 0, 0, 0, 1, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W24

/-! ### W25 — Plasma Physics & Magnetohydrodynamics -/

namespace W25

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["alfven_velocity", "charge", "cyclotron_frequency", "magnetic_field", "mass", "mass_density", "permeability"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: cyclotron_frequency = charge * magnetic_field / mass
-- 1: alfven_velocity = magnetic_field / (permeability * mass_density)^(1/2)
def ax : Fin 2 → Fin 7 → ℚ :=
  ![![0, -1, 1, -1, 1, 0, 0],
   ![1, 0, 0, -1, 0, 1/2, 1/2]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 7 → Fin 8 → ℚ :=
  ![![1, 0, -1, 0, 0, 0, 0, 0],
   ![0, 0, 1, 1, 0, 0, 0, 0],
   ![0, 0, -1, 0, 0, 0, 0, 0],
   ![0, 1, -2, -1, 0, 0, 0, 0],
   ![0, 1, 0, 0, 0, 0, 0, 0],
   ![-3, 1, 0, 0, 0, 0, 0, 0],
   ![1, 1, -2, -2, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W25-01`: magnetic_field = cyclotron_frequency * mass / charge -/
theorem q_W25_01 : Derivable (Set.range ax) ![0, 1, -1, 1, -1, 0, 0] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W25-02`: mass = charge * magnetic_field / cyclotron_frequency -/
theorem q_W25_02 : Derivable (Set.range ax) ![0, -1, 1, -1, 1, 0, 0] :=
  derivable_of_combo ax ![1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W25-03`: mass_density = magnetic_field^2 / (permeability * alfven_velocity^2) -/
theorem q_W25_03 : Derivable (Set.range ax) ![2, 0, 0, -2, 0, 1, 1] :=
  derivable_of_combo ax ![0, 2] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W25-N1`: cyclotron_frequency = mass / magnetic_field -/
theorem q_W25_N1 : ¬ Derivable (Set.range ax) ![0, 0, 1, 1, -1, 0, 0] :=
  not_derivable_of_dot ax ![0, 1, 1, 0, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F25-01`: magnetic_field = cyclotron_frequency * mass -/
theorem q_F25_01 : ¬ Derivable (Set.range ax) ![0, 0, -1, 1, -1, 0, 0] :=
  not_derivable_of_dot ax ![0, 1, 1, 0, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F25-02`: mass = magnetic_field / cyclotron_frequency -/
theorem q_F25_02 : ¬ Derivable (Set.range ax) ![0, 0, 1, -1, 1, 0, 0] :=
  not_derivable_of_dot ax ![0, 1, 1, 0, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F25-03`: mass_density = (magnetic_field / alfven_velocity)^2 -/
theorem q_F25_03 : ¬ Derivable (Set.range ax) ![2, 0, 0, -2, 0, 1, 0] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 0, 0, -2] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F25-ax1`: cyclotron_frequency = magnetic_field / mass -/
theorem q_F25_ax1 : ¬ Derivable (Set.range ax) ![0, 0, 1, -1, 1, 0, 0] :=
  not_derivable_of_dot ax ![0, 1, 1, 0, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F25-ax2`: alfven_velocity = magnetic_field / mass_density^(1/2) -/
theorem q_F25_ax2 : ¬ Derivable (Set.range ax) ![1, 0, 0, -1, 0, 1/2, 0] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 0, 0, -2] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H25-1`: charge = cyclotron_frequency * mass / magnetic_field -/
theorem q_H25_1 : Derivable (Set.range ax) ![0, 1, -1, 1, -1, 0, 0] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H25-2`: alfven_velocity^2 = magnetic_field^2 / (permeability * mass_density) -/
theorem q_H25_2 : Derivable (Set.range ax) ![2, 0, 0, -2, 0, 1, 1] :=
  derivable_of_combo ax ![0, 2] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H25-F`: cyclotron_frequency = charge * magnetic_field * mass -/
theorem q_H25_F : ¬ Derivable (Set.range ax) ![0, -1, 1, -1, -1, 0, 0] :=
  not_derivable_of_dot ax ![0, 1, 0, 0, 1, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W25

/-! ### W28 — Superconductivity & Josephson Effects -/

namespace W28

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["flux_quantum", "josephson_voltage", "magnetic_flux", "time"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: josephson_voltage = magnetic_flux / time
-- 1: flux_quantum = magnetic_flux
def ax : Fin 2 → Fin 4 → ℚ :=
  ![![0, 1, -1, 1],
   ![1, 0, -1, 0]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 4 → Fin 8 → ℚ :=
  ![![2, 1, -2, -1, 0, 0, 0, 0],
   ![2, 1, -3, -1, 0, 0, 0, 0],
   ![2, 1, -2, -1, 0, 0, 0, 0],
   ![0, 0, 1, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W28-01`: magnetic_flux = josephson_voltage * time -/
theorem q_W28_01 : Derivable (Set.range ax) ![0, -1, 1, -1] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W28-02`: time = magnetic_flux / josephson_voltage -/
theorem q_W28_02 : Derivable (Set.range ax) ![0, 1, -1, 1] :=
  derivable_of_combo ax ![1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W28-03`: magnetic_flux = flux_quantum -/
theorem q_W28_03 : Derivable (Set.range ax) ![-1, 0, 1, 0] :=
  derivable_of_combo ax ![0, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W28-N1`: josephson_voltage = time / magnetic_flux -/
theorem q_W28_N1 : ¬ Derivable (Set.range ax) ![0, 1, 1, -1] :=
  not_derivable_of_dot ax ![0, 1, 0, -1] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H28-1`: josephson_voltage = flux_quantum / time -/
theorem q_H28_1 : Derivable (Set.range ax) ![-1, 1, 0, 1] :=
  derivable_of_combo ax ![1, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H28-2`: time = flux_quantum / josephson_voltage -/
theorem q_H28_2 : Derivable (Set.range ax) ![-1, 1, 0, 1] :=
  derivable_of_combo ax ![1, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H28-F`: josephson_voltage = flux_quantum * time -/
theorem q_H28_F : ¬ Derivable (Set.range ax) ![-1, 1, 0, -1] :=
  not_derivable_of_dot ax ![0, 1, 0, -1] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W28

/-! ### W29 — Spintronics & Spin Transport -/

namespace W29

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["diffusion_coefficient", "gyromagnetic_ratio", "larmor_frequency", "magnetic_field", "spin_diffusion_length", "time"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: larmor_frequency = gyromagnetic_ratio * magnetic_field
-- 1: spin_diffusion_length = (diffusion_coefficient * time)^(1/2)
def ax : Fin 2 → Fin 6 → ℚ :=
  ![![0, -1, 1, -1, 0, 0],
   ![-1/2, 0, 0, 0, 1, -1/2]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 6 → Fin 8 → ℚ :=
  ![![2, 0, -1, 0, 0, 0, 0, 0],
   ![0, -1, 1, 1, 0, 0, 0, 0],
   ![0, 0, -1, 0, 0, 0, 0, 0],
   ![0, 1, -2, -1, 0, 0, 0, 0],
   ![1, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 1, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W29-01`: gyromagnetic_ratio = larmor_frequency / magnetic_field -/
theorem q_W29_01 : Derivable (Set.range ax) ![0, 1, -1, 1, 0, 0] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W29-02`: magnetic_field = larmor_frequency / gyromagnetic_ratio -/
theorem q_W29_02 : Derivable (Set.range ax) ![0, 1, -1, 1, 0, 0] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W29-03`: time = spin_diffusion_length^2 / diffusion_coefficient -/
theorem q_W29_03 : Derivable (Set.range ax) ![1, 0, 0, 0, -2, 1] :=
  derivable_of_combo ax ![0, -2] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W29-N1`: larmor_frequency = magnetic_field / gyromagnetic_ratio -/
theorem q_W29_N1 : ¬ Derivable (Set.range ax) ![0, 1, 1, -1, 0, 0] :=
  not_derivable_of_dot ax ![0, 1, 1, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F29-03`: time = (spin_diffusion_length / diffusion_coefficient)^2 -/
theorem q_F29_03 : ¬ Derivable (Set.range ax) ![2, 0, 0, 0, -2, 1] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 0, -1] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F29-ax2`: spin_diffusion_length = diffusion_coefficient * time^(1/2) -/
theorem q_F29_ax2 : ¬ Derivable (Set.range ax) ![-1, 0, 0, 0, 1, -1/2] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 0, -1] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H29-1`: diffusion_coefficient = spin_diffusion_length^2 / time -/
theorem q_H29_1 : Derivable (Set.range ax) ![1, 0, 0, 0, -2, 1] :=
  derivable_of_combo ax ![0, -2] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H29-F`: spin_diffusion_length = diffusion_coefficient * time -/
theorem q_H29_F : ¬ Derivable (Set.range ax) ![-1, 0, 0, 0, 1, -1] :=
  not_derivable_of_dot ax ![2, 0, 0, 0, 1, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W29

/-! ### W32 — Capillarity & Surface Phenomena -/

namespace W32

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["capillary_height", "capillary_radius", "pressure", "surface_tension", "viscosity", "wetting_coefficient"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: pressure = surface_tension / capillary_radius
def ax : Fin 1 → Fin 6 → ℚ :=
  ![![0, 1, 1, -1, 0, 0]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 6 → Fin 8 → ℚ :=
  ![![1, 0, 0, 0, 0, 0, 0, 0],
   ![1, 0, 0, 0, 0, 0, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0],
   ![0, 1, -2, 0, 0, 0, 0, 0],
   ![-1, 1, -1, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i; (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W32-01`: surface_tension = pressure * capillary_radius -/
theorem q_W32_01 : Derivable (Set.range ax) ![0, -1, -1, 1, 0, 0] :=
  derivable_of_combo ax ![-1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W32-02`: capillary_radius = surface_tension / pressure -/
theorem q_W32_02 : Derivable (Set.range ax) ![0, 1, 1, -1, 0, 0] :=
  derivable_of_combo ax ![1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W32-03`: viscosity = surface_tension * wetting_coefficient / (capillary_height * capillary_radius) -/
theorem q_W32_03 : ¬ Derivable (Set.range ax) ![1, 1, 0, -1, 1, -1] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 0, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `W32-N1`: pressure = capillary_radius / surface_tension -/
theorem q_W32_N1 : ¬ Derivable (Set.range ax) ![0, -1, 1, 1, 0, 0] :=
  not_derivable_of_dot ax ![0, 1, -1, 0, 0, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F32-ax2`: capillary_height = surface_tension * wetting_coefficient / (viscosity * capillary_radius) -/
theorem q_F32_ax2 : ¬ Derivable (Set.range ax) ![1, 1, 0, -1, 1, -1] :=
  not_derivable_of_dot ax ![1, 0, 0, 0, 0, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H32-F`: pressure = surface_tension * capillary_radius -/
theorem q_H32_F : ¬ Derivable (Set.range ax) ![0, -1, 1, -1, 0, 0] :=
  not_derivable_of_dot ax ![0, 1, -1, 0, 0, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W32

/-! ### W33 — Multi-Phase Heat & Mass Transfer -/

namespace W33

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["characteristic_length", "heat_transfer_coefficient", "nusselt_number", "thermal_conductivity"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: nusselt_number = heat_transfer_coefficient * characteristic_length / thermal_conductivity
def ax : Fin 1 → Fin 4 → ℚ :=
  ![![-1, -1, 1, 1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 4 → Fin 8 → ℚ :=
  ![![1, 0, 0, 0, 0, 0, 0, 0],
   ![0, 1, -3, 0, -1, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![1, 1, -3, 0, -1, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i; (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W33-01`: thermal_conductivity = heat_transfer_coefficient * characteristic_length -/
theorem q_W33_01 : ¬ Derivable (Set.range ax) ![-1, -1, 0, 1] :=
  not_derivable_of_dot ax ![1, 0, 1, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `W33-02`: characteristic_length = thermal_conductivity / heat_transfer_coefficient -/
theorem q_W33_02 : ¬ Derivable (Set.range ax) ![1, 1, 0, -1] :=
  not_derivable_of_dot ax ![1, 0, 1, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `W33-03`: heat_transfer_coefficient = nusselt_number * thermal_conductivity / characteristic_length -/
theorem q_W33_03 : Derivable (Set.range ax) ![1, 1, -1, -1] :=
  derivable_of_combo ax ![-1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W33-N1`: nusselt_number = thermal_conductivity / heat_transfer_coefficient -/
theorem q_W33_N1 : ¬ Derivable (Set.range ax) ![0, 1, 1, -1] :=
  not_derivable_of_dot ax ![1, -1, 0, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `F33-ax1`: heat_transfer_coefficient = thermal_conductivity / characteristic_length -/
theorem q_F33_ax1 : ¬ Derivable (Set.range ax) ![1, 1, 0, -1] :=
  not_derivable_of_dot ax ![1, 0, 1, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H33-1`: characteristic_length = nusselt_number * thermal_conductivity / heat_transfer_coefficient -/
theorem q_H33_1 : Derivable (Set.range ax) ![1, 1, -1, -1] :=
  derivable_of_combo ax ![-1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H33-F`: nusselt_number = 1 -/
theorem q_H33_F : ¬ Derivable (Set.range ax) ![0, 0, 1, 0] :=
  not_derivable_of_dot ax ![1, 0, 1, 0] _
    (by intro i; fin_cases i; norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W33

/-! ### W34 — Biomechanics & Hemodynamics -/

namespace W34

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["length", "pipe_radius", "pressure", "vascular_resistance", "viscosity", "volume_flow_rate"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: vascular_resistance = viscosity * length / pipe_radius^4
-- 1: volume_flow_rate = pressure / vascular_resistance
def ax : Fin 2 → Fin 6 → ℚ :=
  ![![-1, 4, 0, 1, -1, 0],
   ![0, 0, -1, 1, 0, 1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 6 → Fin 8 → ℚ :=
  ![![1, 0, 0, 0, 0, 0, 0, 0],
   ![1, 0, 0, 0, 0, 0, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0],
   ![-4, 1, -1, 0, 0, 0, 0, 0],
   ![-1, 1, -1, 0, 0, 0, 0, 0],
   ![3, 0, -1, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W34-01`: viscosity = vascular_resistance * pipe_radius^4 / length -/
theorem q_W34_01 : Derivable (Set.range ax) ![1, -4, 0, -1, 1, 0] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W34-02`: pipe_radius = (viscosity * length / vascular_resistance)^(1/4) -/
theorem q_W34_02 : Derivable (Set.range ax) ![-1/4, 1, 0, 1/4, -1/4, 0] :=
  derivable_of_combo ax ![1/4, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W34-03`: pressure = volume_flow_rate * vascular_resistance -/
theorem q_W34_03 : Derivable (Set.range ax) ![0, 0, 1, -1, 0, -1] :=
  derivable_of_combo ax ![0, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W34-N1`: vascular_resistance = pipe_radius^4 / (viscosity * length) -/
theorem q_W34_N1 : ¬ Derivable (Set.range ax) ![1, -4, 0, 1, 1, 0] :=
  not_derivable_of_dot ax ![1, 0, 1, 1, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `H34-1`: pressure = viscosity * length * volume_flow_rate / pipe_radius^4 -/
theorem q_H34_1 : Derivable (Set.range ax) ![-1, 4, 1, 0, -1, -1] :=
  derivable_of_combo ax ![1, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H34-2`: volume_flow_rate = pressure * pipe_radius^4 / (viscosity * length) -/
theorem q_H34_2 : Derivable (Set.range ax) ![1, -4, -1, 0, 1, 1] :=
  derivable_of_combo ax ![-1, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `H34-F`: vascular_resistance = viscosity * length / pipe_radius^3 -/
theorem q_H34_F : ¬ Derivable (Set.range ax) ![-1, 3, 0, 1, -1, 0] :=
  not_derivable_of_dot ax ![4, 1, 0, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W34

/-! ## The W4 and W6 additions (W4 and W6 of `engineering/wheels.py` are unchanged) -/

/-! ### W4Ext — Rotational mechanics (with the supplied addition) -/

namespace W4Ext

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["angular_acceleration", "angular_momentum", "angular_velocity", "energy", "frequency", "moment_of_inertia", "power", "torque", "#2"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: torque = moment_of_inertia * angular_acceleration
-- 1: power = torque * angular_velocity
-- 2: angular_momentum = moment_of_inertia * angular_velocity
-- 3: energy = 1/2 * moment_of_inertia * angular_velocity^2
def ax : Fin 4 → Fin 9 → ℚ :=
  ![![-1, 0, 0, 0, 0, -1, 0, 1, 0],
   ![0, 0, -1, 0, 0, 0, 1, -1, 0],
   ![0, 1, -1, 0, 0, -1, 0, 0, 0],
   ![0, 0, -2, 1, 0, -1, 0, 0, 1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 9 → Fin 8 → ℚ :=
  ![![0, 0, -2, 0, 0, 0, 0, 1],
   ![2, 1, -1, 0, 0, 0, 0, -1],
   ![0, 0, -1, 0, 0, 0, 0, 1],
   ![2, 1, -2, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![2, 1, 0, 0, 0, 0, 0, -2],
   ![2, 1, -3, 0, 0, 0, 0, 0],
   ![2, 1, -2, 0, 0, 0, 0, -1],
   ![0, 0, 0, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W4-01`: angular_acceleration = torque / moment_of_inertia -/
theorem q_W4_01 : Derivable (Set.range ax) ![1, 0, 0, 0, 0, 1, 0, -1, 0] :=
  derivable_of_combo ax ![-1, 0, 0, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W4-02`: power = torque * angular_velocity -/
theorem q_W4_02 : Derivable (Set.range ax) ![0, 0, -1, 0, 0, 0, 1, -1, 0] :=
  derivable_of_combo ax ![0, 1, 0, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W4-03`: angular_momentum = moment_of_inertia * angular_velocity -/
theorem q_W4_03 : Derivable (Set.range ax) ![0, 1, -1, 0, 0, -1, 0, 0, 0] :=
  derivable_of_combo ax ![0, 0, 1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W4-N1`: torque = moment_of_inertia * angular_velocity -/
theorem q_W4_N1 : ¬ Derivable (Set.range ax) ![0, 0, -1, 0, 0, -1, 0, 1, 0] :=
  not_derivable_of_dot ax ![1, -1, 0, -1, 0, -1, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `W4-M1`: angular_velocity = frequency -/
theorem q_W4_M1 : ¬ Derivable (Set.range ax) ![0, 0, 1, 0, -1, 0, 0, 0, 0] :=
  not_derivable_of_dot ax ![0, 0, 0, 0, 1, 0, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- `W4-04`: energy = 1/2 * moment_of_inertia * angular_velocity^2 -/
theorem q_W4_04 : Derivable (Set.range ax) ![0, 0, -2, 1, 0, -1, 0, 0, 1] :=
  derivable_of_combo ax ![0, 0, 0, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

end W4Ext

/-! ### W6Ext — Fluid statics and flow (with the supplied addition) -/

namespace W6Ext

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["area", "force", "power", "pressure", "velocity", "volume_flow_rate"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: pressure = force / area
-- 1: volume_flow_rate = area * velocity
-- 2: force = pressure * area
-- 3: power = pressure * volume_flow_rate
def ax : Fin 4 → Fin 6 → ℚ :=
  ![![1, -1, 0, 1, 0, 0],
   ![-1, 0, 0, 0, -1, 1],
   ![-1, 1, 0, -1, 0, 0],
   ![0, 0, 1, -1, 0, -1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 6 → Fin 8 → ℚ :=
  ![![2, 0, 0, 0, 0, 0, 0, 0],
   ![1, 1, -2, 0, 0, 0, 0, 0],
   ![2, 1, -3, 0, 0, 0, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0],
   ![1, 0, -1, 0, 0, 0, 0, 0],
   ![3, 0, -1, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W6-01`: force = pressure * area -/
theorem q_W6_01 : Derivable (Set.range ax) ![-1, 1, 0, -1, 0, 0] :=
  derivable_of_combo ax ![-1, 0, 0, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W6-02`: velocity = volume_flow_rate / area -/
theorem q_W6_02 : Derivable (Set.range ax) ![1, 0, 0, 0, 1, -1] :=
  derivable_of_combo ax ![0, -1, 0, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W6-03`: power = pressure * volume_flow_rate -/
theorem q_W6_03 : Derivable (Set.range ax) ![0, 0, 1, -1, 0, -1] :=
  derivable_of_combo ax ![0, 0, 0, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W6-N1`: pressure = force * area -/
theorem q_W6_N1 : ¬ Derivable (Set.range ax) ![-1, -1, 0, 1, 0, 0] :=
  not_derivable_of_dot ax ![1, 1, 0, 0, -1, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

/-- Without the addition, W6-03 is not derivable: the hydraulic-power axiom is
what makes it so (`engineering/wheels.py` records W6-03 as not derivable). -/
theorem q_W6_03_without_addition :
    ¬ Derivable (Set.range (fun i : Fin 3 => ax (Fin.castSucc i))) ![0, 0, 1, -1, 0, -1] :=
  not_derivable_of_dot _ ![0, 0, 1, 0, 0, 0] _
    (by intro i; fin_cases i <;> norm_num [ax, Fin.sum_univ_succ])
    (by norm_num [Fin.sum_univ_succ])

end W6Ext

/-! ## The W11–W15 axioms and their supplied cases -/

/-! ### W11Dom — Uniform motion -/

namespace W11Dom

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["length", "time", "velocity"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: velocity = length / time
def ax : Fin 1 → Fin 3 → ℚ :=
  ![![-1, 1, 1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 3 → Fin 8 → ℚ :=
  ![![1, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 1, 0, 0, 0, 0, 0],
   ![1, 0, -1, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i; (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W11-01`: length = velocity * time -/
theorem q_W11_01 : Derivable (Set.range ax) ![1, -1, -1] :=
  derivable_of_combo ax ![-1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W11-02`: time = length / velocity -/
theorem q_W11_02 : Derivable (Set.range ax) ![-1, 1, 1] :=
  derivable_of_combo ax ![1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

end W11Dom

/-! ### W12Dom — Density, volume and amount of substance -/

namespace W12Dom

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["amount", "area", "density", "length", "mass", "molar_mass", "volume"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: density = mass / volume
-- 1: volume = area * length
-- 2: amount = mass / molar_mass
def ax : Fin 3 → Fin 7 → ℚ :=
  ![![0, 0, 1, 0, -1, 0, 1],
   ![0, -1, 0, -1, 0, 0, 1],
   ![1, 0, 0, 0, -1, 1, 0]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 7 → Fin 8 → ℚ :=
  ![![0, 0, 0, 0, 0, 1, 0, 0],
   ![2, 0, 0, 0, 0, 0, 0, 0],
   ![-3, 1, 0, 0, 0, 0, 0, 0],
   ![1, 0, 0, 0, 0, 0, 0, 0],
   ![0, 1, 0, 0, 0, 0, 0, 0],
   ![0, 1, 0, 0, 0, -1, 0, 0],
   ![3, 0, 0, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W12-01`: volume = mass / density -/
theorem q_W12_01 : Derivable (Set.range ax) ![0, 0, 1, 0, -1, 0, 1] :=
  derivable_of_combo ax ![1, 0, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W12-02`: length = volume / area -/
theorem q_W12_02 : Derivable (Set.range ax) ![0, 1, 0, 1, 0, 0, -1] :=
  derivable_of_combo ax ![0, -1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W12-03`: molar_mass = mass / amount -/
theorem q_W12_03 : Derivable (Set.range ax) ![1, 0, 0, 0, -1, 1, 0] :=
  derivable_of_combo ax ![0, 0, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

end W12Dom

/-! ### W13Dom — Period and the mass-spring oscillator -/

namespace W13Dom

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["angle", "angular_frequency", "frequency", "mass", "period", "spring_constant"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: frequency = 1 / period
-- 1: angular_frequency = angle * frequency
-- 2: spring_constant = mass * angular_frequency * angular_frequency
def ax : Fin 3 → Fin 6 → ℚ :=
  ![![0, 0, 1, 0, 1, 0],
   ![-1, 1, -1, 0, 0, 0],
   ![0, -2, 0, -1, 0, 1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 6 → Fin 8 → ℚ :=
  ![![0, 0, 0, 0, 0, 0, 0, 1],
   ![0, 0, -1, 0, 0, 0, 0, 1],
   ![0, 0, -1, 0, 0, 0, 0, 0],
   ![0, 1, 0, 0, 0, 0, 0, 0],
   ![0, 0, 1, 0, 0, 0, 0, 0],
   ![0, 1, -2, 0, 0, 0, 0, 0]]

/-- Axiom 0 balances on all eight axes. -/
theorem axiom_0_residual : dimL dim (ax 0) = ![0, 0, 0, 0, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ]

/-- Axiom 1 balances on all eight axes. -/
theorem axiom_1_residual : dimL dim (ax 1) = ![0, 0, 0, 0, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ]

/-- Axiom 2 balances at SI7; its residual on the angle axis A is -2. -/
theorem axiom_2_residual : dimL dim (ax 2) = ![0, 0, 0, 0, 0, 0, 0, -2] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ]

/-- `W13-01`: period = 1 / frequency -/
theorem q_W13_01 : Derivable (Set.range ax) ![0, 0, 1, 0, 1, 0] :=
  derivable_of_combo ax ![1, 0, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W13-02`: angular_frequency = angle * frequency -/
theorem q_W13_02 : Derivable (Set.range ax) ![-1, 1, -1, 0, 0, 0] :=
  derivable_of_combo ax ![0, 1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W13-03`: spring_constant = mass * angular_frequency^2 -/
theorem q_W13_03 : Derivable (Set.range ax) ![0, -2, 0, -1, 0, 1] :=
  derivable_of_combo ax ![0, 0, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

end W13Dom

/-! ### W14Dom — Inductors and the LC circuit -/

namespace W14Dom

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["angular_frequency", "capacitance", "current", "energy", "inductance", "reactance", "#2"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: reactance = inductance * angular_frequency
-- 1: inductance * capacitance * angular_frequency * angular_frequency = 1
-- 2: energy = 1/2 * inductance * current * current
def ax : Fin 3 → Fin 7 → ℚ :=
  ![![-1, 0, 0, 0, -1, 1, 0],
   ![2, 1, 0, 0, 1, 0, 0],
   ![0, 0, -2, 1, -1, 0, 1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 7 → Fin 8 → ℚ :=
  ![![0, 0, -1, 0, 0, 0, 0, 1],
   ![-2, -1, 4, 2, 0, 0, 0, 0],
   ![0, 0, 0, 1, 0, 0, 0, 0],
   ![2, 1, -2, 0, 0, 0, 0, 0],
   ![2, 1, -2, -2, 0, 0, 0, 0],
   ![2, 1, -3, -2, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0]]

/-- Axiom 0 balances at SI7; its residual on the angle axis A is -1. -/
theorem axiom_0_residual : dimL dim (ax 0) = ![0, 0, 0, 0, 0, 0, 0, -1] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ]

/-- Axiom 1 balances at SI7; its residual on the angle axis A is 2. -/
theorem axiom_1_residual : dimL dim (ax 1) = ![0, 0, 0, 0, 0, 0, 0, 2] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ]

/-- Axiom 2 balances on all eight axes. -/
theorem axiom_2_residual : dimL dim (ax 2) = ![0, 0, 0, 0, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ]

/-- `W14-01`: angular_frequency = 1 / (inductance * capacitance * angular_frequency) -/
theorem q_W14_01 : Derivable (Set.range ax) ![2, 1, 0, 0, 1, 0, 0] :=
  derivable_of_combo ax ![0, 1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W14-02`: reactance = inductance * angular_frequency -/
theorem q_W14_02 : Derivable (Set.range ax) ![-1, 0, 0, 0, -1, 1, 0] :=
  derivable_of_combo ax ![1, 0, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W14-03`: energy = 1/2 * inductance * current^2 -/
theorem q_W14_03 : Derivable (Set.range ax) ![0, 0, -2, 1, -1, 0, 1] :=
  derivable_of_combo ax ![0, 0, 1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

end W14Dom

/-! ### W15Dom — Charge and energy over time -/

namespace W15Dom

/-- The coordinates: quantities, then the primes of the coefficients. -/
def coords : List String :=
  ["charge", "current", "energy", "power", "time"]

/-- The axioms' relation vectors, in the order of the wheel: -/
-- 0: charge = current * time
-- 1: energy = power * time
def ax : Fin 2 → Fin 5 → ℚ :=
  ![![1, -1, 0, 0, -1],
   ![0, 0, 1, -1, -1]]

/-- The wheel's dimension table, one row per coordinate over `L M T I H N J A`
(the zero row for a prime or a name no axiom uses). -/
def dim : Fin 5 → Fin 8 → ℚ :=
  ![![0, 0, 1, 1, 0, 0, 0, 0],
   ![0, 0, 0, 1, 0, 0, 0, 0],
   ![2, 1, -2, 0, 0, 0, 0, 0],
   ![2, 1, -3, 0, 0, 0, 0, 0],
   ![0, 0, 1, 0, 0, 0, 0, 0]]

/-- Every axiom balances on all eight axes. -/
theorem axioms_balanced : ∀ i, dimL dim (ax i) = 0 := by
  intro i
  fin_cases i <;> (funext a; fin_cases a <;> norm_num [dimL_apply, ax, dim, Fin.sum_univ_succ])

/-- `W15-01`: current = charge / time -/
theorem q_W15_01 : Derivable (Set.range ax) ![-1, 1, 0, 0, 1] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W15-02`: power = energy / time -/
theorem q_W15_02 : Derivable (Set.range ax) ![0, 0, -1, 1, 1] :=
  derivable_of_combo ax ![0, -1] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

/-- `W15-03`: time = charge / current -/
theorem q_W15_03 : Derivable (Set.range ax) ![-1, 1, 0, 0, 1] :=
  derivable_of_combo ax ![-1, 0] _
    (by funext j; fin_cases j <;> norm_num [ax, Fin.sum_univ_succ])

end W15Dom

/-! ## The supplied axioms that fail at SI7, on their own tables -/

/-! Numbered from 1, as in the study; each with its supplied table's rows. -/

namespace Supplied

/-- W21 axiom 2 as supplied: stress_intensity_factor = dimensionless_factor * stress * crack_length^(1/2) -/
def W21_axiom_2_coords : List String :=
  ["crack_length", "dimensionless_factor", "stress", "stress_intensity_factor"]
def W21_axiom_2 : Fin 4 → ℚ := ![-1/2, -1, -1, 1]
def W21_axiom_2_dim : Fin 4 → Fin 8 → ℚ :=
  ![![1, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0],
   ![-1, 1, -2, 0, 0, 0, 0, 0]]
/-- Its residual on the supplied table: not zero at SI7 (axis L). -/
theorem W21_axiom_2_residual : dimL W21_axiom_2_dim W21_axiom_2 = ![-1/2, 0, 0, 0, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, W21_axiom_2, W21_axiom_2_dim, Fin.sum_univ_succ]
theorem W21_axiom_2_unbalanced : dimL W21_axiom_2_dim W21_axiom_2 ≠ 0 := by
  rw [W21_axiom_2_residual]; intro h; have := congrFun h 0; norm_num at this

/-- W22 axiom 2 as supplied: rate_constant = pre_exponential_factor * concentration / rate_constant -/
def W22_axiom_2_coords : List String :=
  ["concentration", "pre_exponential_factor", "rate_constant"]
def W22_axiom_2 : Fin 3 → ℚ := ![-1, -1, 2]
def W22_axiom_2_dim : Fin 3 → Fin 8 → ℚ :=
  ![![-3, 0, 0, 0, 0, 1, 0, 0],
   ![0, 0, -1, 0, 0, 0, 0, 0],
   ![0, 0, -1, 0, 0, 0, 0, 0]]
/-- Its residual on the supplied table: not zero at SI7 (axis L). -/
theorem W22_axiom_2_residual : dimL W22_axiom_2_dim W22_axiom_2 = ![3, 0, -1, 0, 0, -1, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, W22_axiom_2, W22_axiom_2_dim, Fin.sum_univ_succ]
theorem W22_axiom_2_unbalanced : dimL W22_axiom_2_dim W22_axiom_2 ≠ 0 := by
  rw [W22_axiom_2_residual]; intro h; have := congrFun h 0; norm_num at this

/-- W25 axiom 1 as supplied: cyclotron_frequency = magnetic_field / mass -/
def W25_axiom_1_coords : List String :=
  ["cyclotron_frequency", "magnetic_field", "mass"]
def W25_axiom_1 : Fin 3 → ℚ := ![1, -1, 1]
def W25_axiom_1_dim : Fin 3 → Fin 8 → ℚ :=
  ![![0, 0, -1, 0, 0, 0, 0, 0],
   ![0, 1, -2, -1, 0, 0, 0, 0],
   ![0, 1, 0, 0, 0, 0, 0, 0]]
/-- Its residual on the supplied table: not zero at SI7 (axis T). -/
theorem W25_axiom_1_residual : dimL W25_axiom_1_dim W25_axiom_1 = ![0, 0, 1, 1, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, W25_axiom_1, W25_axiom_1_dim, Fin.sum_univ_succ]
theorem W25_axiom_1_unbalanced : dimL W25_axiom_1_dim W25_axiom_1 ≠ 0 := by
  rw [W25_axiom_1_residual]; intro h; have := congrFun h 2; norm_num at this

/-- W25 axiom 2 as supplied: alfven_velocity = magnetic_field / mass_density^(1/2) -/
def W25_axiom_2_coords : List String :=
  ["alfven_velocity", "magnetic_field", "mass_density"]
def W25_axiom_2 : Fin 3 → ℚ := ![1, -1, 1/2]
def W25_axiom_2_dim : Fin 3 → Fin 8 → ℚ :=
  ![![1, 0, -1, 0, 0, 0, 0, 0],
   ![0, 1, -2, -1, 0, 0, 0, 0],
   ![-3, 1, 0, 0, 0, 0, 0, 0]]
/-- Its residual on the supplied table: not zero at SI7 (axis L). -/
theorem W25_axiom_2_residual : dimL W25_axiom_2_dim W25_axiom_2 = ![-1/2, -1/2, 1, 1, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, W25_axiom_2, W25_axiom_2_dim, Fin.sum_univ_succ]
theorem W25_axiom_2_unbalanced : dimL W25_axiom_2_dim W25_axiom_2 ≠ 0 := by
  rw [W25_axiom_2_residual]; intro h; have := congrFun h 0; norm_num at this

/-- W29 axiom 2 as supplied: spin_diffusion_length = diffusion_coefficient * time^(1/2) -/
def W29_axiom_2_coords : List String :=
  ["diffusion_coefficient", "spin_diffusion_length", "time"]
def W29_axiom_2 : Fin 3 → ℚ := ![-1, 1, -1/2]
def W29_axiom_2_dim : Fin 3 → Fin 8 → ℚ :=
  ![![2, 0, -1, 0, 0, 0, 0, 0],
   ![1, 0, 0, 0, 0, 0, 0, 0],
   ![0, 0, 1, 0, 0, 0, 0, 0]]
/-- Its residual on the supplied table: not zero at SI7 (axis L). -/
theorem W29_axiom_2_residual : dimL W29_axiom_2_dim W29_axiom_2 = ![-1, 0, 1/2, 0, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, W29_axiom_2, W29_axiom_2_dim, Fin.sum_univ_succ]
theorem W29_axiom_2_unbalanced : dimL W29_axiom_2_dim W29_axiom_2 ≠ 0 := by
  rw [W29_axiom_2_residual]; intro h; have := congrFun h 0; norm_num at this

/-- W32 axiom 2 as supplied: capillary_height = surface_tension * wetting_coefficient / (viscosity * capillary_radius) -/
def W32_axiom_2_coords : List String :=
  ["capillary_height", "capillary_radius", "surface_tension", "viscosity", "wetting_coefficient"]
def W32_axiom_2 : Fin 5 → ℚ := ![1, 1, -1, 1, -1]
def W32_axiom_2_dim : Fin 5 → Fin 8 → ℚ :=
  ![![1, 0, 0, 0, 0, 0, 0, 0],
   ![1, 0, 0, 0, 0, 0, 0, 0],
   ![0, 1, -2, 0, 0, 0, 0, 0],
   ![-1, 1, -1, 0, 0, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0]]
/-- Its residual on the supplied table: not zero at SI7 (axis L). -/
theorem W32_axiom_2_residual : dimL W32_axiom_2_dim W32_axiom_2 = ![1, 0, 1, 0, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, W32_axiom_2, W32_axiom_2_dim, Fin.sum_univ_succ]
theorem W32_axiom_2_unbalanced : dimL W32_axiom_2_dim W32_axiom_2 ≠ 0 := by
  rw [W32_axiom_2_residual]; intro h; have := congrFun h 0; norm_num at this

/-- W34 axiom 1 as supplied: vascular_resistance = viscosity * length / pipe_radius^4 -/
def W34_axiom_1_coords : List String :=
  ["length", "pipe_radius", "vascular_resistance", "viscosity"]
def W34_axiom_1 : Fin 4 → ℚ := ![-1, 4, 1, -1]
def W34_axiom_1_dim : Fin 4 → Fin 8 → ℚ :=
  ![![1, 0, 0, 0, 0, 0, 0, 0],
   ![1, 0, 0, 0, 0, 0, 0, 0],
   ![-4, 1, 1, 0, 0, 0, 0, 0],
   ![-1, 1, -1, 0, 0, 0, 0, 0]]
/-- Its residual on the supplied table: not zero at SI7 (axis T). -/
theorem W34_axiom_1_residual : dimL W34_axiom_1_dim W34_axiom_1 = ![0, 0, 2, 0, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, W34_axiom_1, W34_axiom_1_dim, Fin.sum_univ_succ]
theorem W34_axiom_1_unbalanced : dimL W34_axiom_1_dim W34_axiom_1 ≠ 0 := by
  rw [W34_axiom_1_residual]; intro h; have := congrFun h 2; norm_num at this

/-- W34 axiom 2 as supplied: volume_flow_rate = pressure / vascular_resistance -/
def W34_axiom_2_coords : List String :=
  ["pressure", "vascular_resistance", "volume_flow_rate"]
def W34_axiom_2 : Fin 3 → ℚ := ![-1, 1, 1]
def W34_axiom_2_dim : Fin 3 → Fin 8 → ℚ :=
  ![![-1, 1, -2, 0, 0, 0, 0, 0],
   ![-4, 1, 1, 0, 0, 0, 0, 0],
   ![3, 0, -1, 0, 0, 0, 0, 0]]
/-- Its residual on the supplied table: not zero at SI7 (axis T). -/
theorem W34_axiom_2_residual : dimL W34_axiom_2_dim W34_axiom_2 = ![0, 0, 2, 0, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, W34_axiom_2, W34_axiom_2_dim, Fin.sum_univ_succ]
theorem W34_axiom_2_unbalanced : dimL W34_axiom_2_dim W34_axiom_2 ≠ 0 := by
  rw [W34_axiom_2_residual]; intro h; have := congrFun h 2; norm_num at this

/-- W35 axiom 1 as supplied: membrane_voltage = temperature / valence -/
def W35_axiom_1_coords : List String :=
  ["membrane_voltage", "temperature", "valence"]
def W35_axiom_1 : Fin 3 → ℚ := ![1, -1, 1]
def W35_axiom_1_dim : Fin 3 → Fin 8 → ℚ :=
  ![![2, 1, -3, -1, 0, 0, 0, 0],
   ![0, 0, 0, 0, 1, 0, 0, 0],
   ![0, 0, 0, 0, 0, 0, 0, 0]]
/-- Its residual on the supplied table: not zero at SI7 (axis L). -/
theorem W35_axiom_1_residual : dimL W35_axiom_1_dim W35_axiom_1 = ![2, 1, -3, -1, -1, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, W35_axiom_1, W35_axiom_1_dim, Fin.sum_univ_succ]
theorem W35_axiom_1_unbalanced : dimL W35_axiom_1_dim W35_axiom_1 ≠ 0 := by
  rw [W35_axiom_1_residual]; intro h; have := congrFun h 0; norm_num at this

/-- W35 axiom 2 as supplied: ion_flux = diffusion_coefficient * ion_concentration -/
def W35_axiom_2_coords : List String :=
  ["diffusion_coefficient", "ion_concentration", "ion_flux"]
def W35_axiom_2 : Fin 3 → ℚ := ![-1, -1, 1]
def W35_axiom_2_dim : Fin 3 → Fin 8 → ℚ :=
  ![![2, 0, -1, 0, 0, 0, 0, 0],
   ![-3, 0, 0, 0, 0, 1, 0, 0],
   ![-2, 0, -1, 0, 0, 1, 0, 0]]
/-- Its residual on the supplied table: not zero at SI7 (axis L). -/
theorem W35_axiom_2_residual : dimL W35_axiom_2_dim W35_axiom_2 = ![-1, 0, 0, 0, 0, 0, 0, 0] := by
  funext a; fin_cases a <;> norm_num [dimL_apply, W35_axiom_2, W35_axiom_2_dim, Fin.sum_univ_succ]
theorem W35_axiom_2_unbalanced : dimL W35_axiom_2_dim W35_axiom_2 ≠ 0 := by
  rw [W35_axiom_2_residual]; intro h; have := congrFun h 0; norm_num at this

end Supplied

end GLM.CentWheels
