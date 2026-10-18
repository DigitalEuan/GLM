module

public import Mathlib
public import RequestProject.GLM.ConnectedMachine

/-!
# Domain wheels W11–W15: the oscillator conflation and the swept volume (Phase 157)

The formal half of `studies/DOMAIN_WHEELS_STUDY.md` (§5).  A relation `L = R` is
the vector of exponents of `L / R`, as `wheels.relation_vector` writes it, with
coordinate `0` the exponent of the prime 2 of the coefficient.

* `oscillator_naive` — over the naive union of W13 (period and the mass-spring
  oscillator) and W14 (inductors and the LC circuit), with one
  `angular_frequency`, `spring_constant * inductance * capacitance = mass` is
  derivable: a mechanical oscillator conflated with an electrical one.
* `oscillator_refused_split` — once `angular_frequency` is split per wheel (the
  declared non-identity W13/W14), a linear functional vanishing on all six axioms
  of the two wheels certifies that it is not, by
  `GLM.ConnectedMachine.not_derivable_of_functional`.
* `swept_volume_licensed` — over W6, W11 and W12 joined at the declared junctions
  (`area` W6/W12, `velocity` W5/W11 with W6's, `length` W11/W12),
  `volume_flow_rate * time = volume` is derivable, so it is derivable from any
  larger set of axioms (`GLM.ConnectedMachine.derivable_mono`).
-/

@[expose] public section

namespace GLM.DomainWheels

open GLM.ConnectedMachine

/-! ## The oscillator conflation

Naive coordinates (`Fin 12`): `0` the prime 2, `1` spring constant, `2` mass,
`3` angular frequency, `4` inductance, `5` capacitance, `6` frequency,
`7` period, `8` angle, `9` reactance, `10` energy, `11` current. -/

section Oscillator

/-- W13 and W14 over the naive names (one angular frequency). -/
def naiveW13W14 : Set (Fin 12 → ℚ) :=
  { ![0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0],      -- frequency = 1 / period
    ![0, 0, 0, 1, 0, 0, -1, 0, -1, 0, 0, 0],    -- angular_frequency = angle * frequency
    ![0, 1, -1, -2, 0, 0, 0, 0, 0, 0, 0, 0],    -- spring_constant = mass * ω^2
    ![0, 0, 0, -1, -1, 0, 0, 0, 0, 1, 0, 0],    -- reactance = inductance * ω
    ![0, 0, 0, 2, 1, 1, 0, 0, 0, 0, 0, 0],      -- inductance * capacitance * ω^2 = 1
    ![1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, -2] }   -- energy = 1/2 * inductance * current^2

/-- `spring_constant * inductance * capacitance = mass`. -/
def oscillatorConflation : Fin 12 → ℚ := ![0, 1, -1, 0, 1, 1, 0, 0, 0, 0, 0, 0]

/-- The naive union derives the conflation: the spring law plus the LC law. -/
theorem oscillator_naive : Derivable naiveW13W14 oscillatorConflation := by
  have h : oscillatorConflation = ![0, 1, -1, -2, 0, 0, 0, 0, 0, 0, 0, 0]
      + ![0, 0, 0, 2, 1, 1, 0, 0, 0, 0, 0, 0] := by
    ext i; fin_cases i <;> simp [oscillatorConflation]
  rw [Derivable, h]
  refine Submodule.add_mem _ ?_ ?_ <;>
    exact Submodule.subset_span (by simp [naiveW13W14])

/-- Split coordinates (`Fin 13`): as above, with `3` now W13's angular frequency
and `12` W14's own copy. -/
def splitW13W14 : Set (Fin 13 → ℚ) :=
  { ![0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    ![0, 0, 0, 1, 0, 0, -1, 0, -1, 0, 0, 0, 0],
    ![0, 1, -1, -2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ![0, 0, 0, 0, -1, 0, 0, 0, 0, 1, 0, 0, -1],
    ![0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 2],
    ![1, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, -2, 0] }

/-- The certificate: twice the capacitance, minus W14's angular frequency, minus
the reactance.  It vanishes on every split axiom. -/
def oscillatorWitness : (Fin 13 → ℚ) →ₗ[ℚ] ℚ :=
  (2 : ℚ) • LinearMap.proj (R := ℚ) (φ := fun _ : Fin 13 => ℚ) 5
    - LinearMap.proj (R := ℚ) (φ := fun _ : Fin 13 => ℚ) 12
    - LinearMap.proj (R := ℚ) (φ := fun _ : Fin 13 => ℚ) 9

theorem oscillatorWitness_vanishes : ∀ s ∈ splitW13W14, oscillatorWitness s = 0 := by
  intro s hs
  simp only [splitW13W14, Set.mem_insert_iff, Set.mem_singleton_iff] at hs
  rcases hs with rfl | rfl | rfl | rfl | rfl | rfl <;>
    simp [oscillatorWitness]

/-- After splitting, the oscillator conflation is refused. -/
theorem oscillator_refused_split :
    ¬ Derivable splitW13W14 ![0, 1, -1, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0] :=
  not_derivable_of_functional oscillatorWitness oscillatorWitness_vanishes
    (by simp [oscillatorWitness])

end Oscillator

/-! ## The swept volume

Coordinates (`Fin 6`): `0` volume flow rate, `1` area, `2` velocity, `3` length,
`4` time, `5` volume. -/

section Swept

/-- The three axioms joined at the declared junctions. -/
def junctionW6W11W12 : Set (Fin 6 → ℚ) :=
  { ![1, -1, -1, 0, 0, 0],    -- volume_flow_rate = area * velocity (W6)
    ![0, 0, 1, -1, 1, 0],     -- velocity = length / time           (W11)
    ![0, -1, 0, -1, 0, 1] }   -- volume = area * length             (W12)

/-- `volume_flow_rate * time = volume` is licensed across the junctions. -/
theorem swept_volume_licensed : Derivable junctionW6W11W12 ![1, 0, 0, 0, 1, -1] := by
  have h : (![1, 0, 0, 0, 1, -1] : Fin 6 → ℚ) = ![1, -1, -1, 0, 0, 0]
      + ![0, 0, 1, -1, 1, 0] - ![0, -1, 0, -1, 0, 1] := by
    ext i; fin_cases i <;> simp
  rw [Derivable, h]
  refine Submodule.sub_mem _ (Submodule.add_mem _ ?_ ?_) ?_ <;>
    exact Submodule.subset_span (by simp [junctionW6W11W12])

/-- Hence it stays licensed over any larger set of axioms. -/
theorem swept_volume_licensed_mono {S : Set (Fin 6 → ℚ)} (hS : junctionW6W11W12 ⊆ S) :
    Derivable S ![1, 0, 0, 0, 1, -1] :=
  derivable_mono hS swept_volume_licensed

end Swept

end GLM.DomainWheels
