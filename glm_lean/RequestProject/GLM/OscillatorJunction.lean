module

public import Mathlib
public import RequestProject.GLM.ConnectedMachine

/-!
# The oscillator junction tried three ways (Phase 158)

The formal half of `studies/OSCILLATOR_JUNCTION_STUDY.md` (§5), over the axioms of
W4 (rotational mechanics), W9 (wave kinematics) and W13 (period and the mass-spring
oscillator).  A relation `L = R` is the vector of exponents of `L / R`, as
`wheels.relation_vector` writes it.

* `rotor_chain_turn_and_rate` — with W4/W9 joining `angular_velocity` and W9/W13
  joining `frequency` and `angle` (variant A, as shipped by Phase 157), the
  oscillator's angular frequency times a rotating body's torque is its power:
  `angular_frequency * torque = power` is derivable.
* `rotor_chain_refused_rate_only` — once `angle` is split across W9/W13 (variant B),
  a linear functional vanishing on every axiom certifies that it is not;
  `wave_period_rate_only` — the wave's period `wave_speed * period = wavelength`
  is still derivable under B.
* `rotor_chain_refused_reference_circle` — with W4/W9 not used (variant D), the
  chain is refused, while `reference_circle_identity` — the oscillator's angular
  frequency is the wave's angular velocity — is derivable.
-/

@[expose] public section

namespace GLM.OscillatorJunction

open GLM.ConnectedMachine

/-! ## Variant A: `frequency` and `angle` joined, W4/W9 used

Coordinates (`Fin 14`): `0` torque, `1` moment of inertia, `2` angular acceleration,
`3` power, `4` angular velocity (W4 = W9), `5` angular momentum, `6` wave speed,
`7` frequency (W9 = W13), `8` wavelength, `9` angle (W9 = W13), `10` period,
`11` angular frequency, `12` spring constant, `13` mass. -/

section TurnAndRate

/-- The eight axioms of W4, W9 and W13 under variant A. -/
def axiomsA : Set (Fin 14 → ℚ) :=
  { ![1, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],    -- torque = I * α
    ![-1, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0],    -- power = torque * ω
    ![0, -1, 0, 0, -1, 1, 0, 0, 0, 0, 0, 0, 0, 0],    -- L = I * ω
    ![0, 0, 0, 0, 0, 0, 1, -1, -1, 0, 0, 0, 0, 0],    -- wave_speed = f * λ
    ![0, 0, 0, 0, 1, 0, 0, -1, 0, -1, 0, 0, 0, 0],    -- ω = angle * f
    ![0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0],      -- f = 1 / period
    ![0, 0, 0, 0, 0, 0, 0, -1, 0, -1, 0, 1, 0, 0],    -- Ω = angle * f
    ![0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -2, 1, -1] }   -- k = m * Ω^2

/-- `angular_frequency * torque = power`. -/
def rotorChainA : Fin 14 → ℚ := ![1, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]

/-- Under variant A the oscillator is tied to the rotating body: W13's angular
frequency, minus W9's angular velocity, minus the shaft-power law. -/
theorem rotor_chain_turn_and_rate : Derivable axiomsA rotorChainA := by
  have h : rotorChainA = ![0, 0, 0, 0, 0, 0, 0, -1, 0, -1, 0, 1, 0, 0]
      - ![0, 0, 0, 0, 1, 0, 0, -1, 0, -1, 0, 0, 0, 0]
      - ![-1, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0] := by
    ext i; fin_cases i <;> simp [rotorChainA]
  rw [Derivable, h]
  refine Submodule.sub_mem _ (Submodule.sub_mem _ ?_ ?_) ?_ <;>
    exact Submodule.subset_span (by simp [axiomsA])

end TurnAndRate

/-! ## Variant B: only `frequency` joined

Coordinates (`Fin 15`): as for A, with `9` now W9's angle and `14` W13's own. -/

section RateOnly

/-- The eight axioms under variant B. -/
def axiomsB : Set (Fin 15 → ℚ) :=
  { ![1, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ![-1, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ![0, -1, 0, 0, -1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ![0, 0, 0, 0, 0, 0, 1, -1, -1, 0, 0, 0, 0, 0, 0],
    ![0, 0, 0, 0, 1, 0, 0, -1, 0, -1, 0, 0, 0, 0, 0],
    ![0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
    ![0, 0, 0, 0, 0, 0, 0, -1, 0, 0, 0, 1, 0, 0, -1],   -- Ω = angle@W13 * f
    ![0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -2, 1, -1, 0] }

/-- The certificate: the angular frequency, plus W13's angle, plus twice the
spring constant.  It vanishes on every axiom of variant B. -/
def rateOnlyWitness : (Fin 15 → ℚ) →ₗ[ℚ] ℚ :=
  LinearMap.proj (R := ℚ) (φ := fun _ : Fin 15 => ℚ) 11
    + LinearMap.proj (R := ℚ) (φ := fun _ : Fin 15 => ℚ) 14
    + (2 : ℚ) • LinearMap.proj (R := ℚ) (φ := fun _ : Fin 15 => ℚ) 12

theorem rateOnlyWitness_vanishes : ∀ s ∈ axiomsB, rateOnlyWitness s = 0 := by
  intro s hs
  simp only [axiomsB, Set.mem_insert_iff, Set.mem_singleton_iff] at hs
  rcases hs with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl <;>
    simp [rateOnlyWitness]

/-- Under variant B the rotor chain is refused. -/
theorem rotor_chain_refused_rate_only :
    ¬ Derivable axiomsB ![1, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0] :=
  not_derivable_of_functional rateOnlyWitness rateOnlyWitness_vanishes
    (by simp [rateOnlyWitness])

/-- Under variant B the wave's period is still derived:
`wave_speed * period = wavelength`. -/
theorem wave_period_rate_only :
    Derivable axiomsB ![0, 0, 0, 0, 0, 0, 1, 0, -1, 0, 1, 0, 0, 0, 0] := by
  have h : (![0, 0, 0, 0, 0, 0, 1, 0, -1, 0, 1, 0, 0, 0, 0] : Fin 15 → ℚ)
      = ![0, 0, 0, 0, 0, 0, 1, -1, -1, 0, 0, 0, 0, 0, 0]
      + ![0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0] := by
    ext i; fin_cases i <;> simp
  rw [Derivable, h]
  refine Submodule.add_mem _ ?_ ?_ <;>
    exact Submodule.subset_span (by simp [axiomsB])

end RateOnly

/-! ## Variant D: `frequency` and `angle` joined, W4/W9 not used

Coordinates (`Fin 15`): as for A, with `4` now W4's angular velocity and `14` W9's. -/

section ReferenceCircle

/-- The eight axioms under variant D. -/
def axiomsD : Set (Fin 15 → ℚ) :=
  { ![1, -1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ![-1, 0, 0, 1, -1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ![0, -1, 0, 0, -1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ![0, 0, 0, 0, 0, 0, 1, -1, -1, 0, 0, 0, 0, 0, 0],
    ![0, 0, 0, 0, 0, 0, 0, -1, 0, -1, 0, 0, 0, 0, 1],   -- ω@W9 = angle * f
    ![0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
    ![0, 0, 0, 0, 0, 0, 0, -1, 0, -1, 0, 1, 0, 0, 0],
    ![0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, -2, 1, -1, 0] }

/-- The certificate: the angular frequency, plus the angle, plus W9's angular
velocity, plus twice the spring constant. -/
def referenceWitness : (Fin 15 → ℚ) →ₗ[ℚ] ℚ :=
  LinearMap.proj (R := ℚ) (φ := fun _ : Fin 15 => ℚ) 11
    + LinearMap.proj (R := ℚ) (φ := fun _ : Fin 15 => ℚ) 9
    + LinearMap.proj (R := ℚ) (φ := fun _ : Fin 15 => ℚ) 14
    + (2 : ℚ) • LinearMap.proj (R := ℚ) (φ := fun _ : Fin 15 => ℚ) 12

theorem referenceWitness_vanishes : ∀ s ∈ axiomsD, referenceWitness s = 0 := by
  intro s hs
  simp only [axiomsD, Set.mem_insert_iff, Set.mem_singleton_iff] at hs
  rcases hs with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl <;>
    simp [referenceWitness]

/-- Under variant D the rotor chain is refused. -/
theorem rotor_chain_refused_reference_circle :
    ¬ Derivable axiomsD ![1, 0, 0, -1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0] :=
  not_derivable_of_functional referenceWitness referenceWitness_vanishes
    (by simp [referenceWitness])

/-- Under variant D the reference circle holds: the oscillator's angular frequency
is the wave's angular velocity, `angular_frequency = angular_velocity@W9`. -/
theorem reference_circle_identity :
    Derivable axiomsD ![0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, -1] := by
  have h : (![0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, -1] : Fin 15 → ℚ)
      = ![0, 0, 0, 0, 0, 0, 0, -1, 0, -1, 0, 1, 0, 0, 0]
      - ![0, 0, 0, 0, 0, 0, 0, -1, 0, -1, 0, 0, 0, 0, 1] := by
    ext i; fin_cases i <;> simp
  rw [Derivable, h]
  refine Submodule.sub_mem _ ?_ ?_ <;>
    exact Submodule.subset_span (by simp [axiomsD])

end ReferenceCircle

end GLM.OscillatorJunction
