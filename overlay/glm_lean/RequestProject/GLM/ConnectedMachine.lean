module

public import Mathlib

/-!
# The connected machine: routing to the first reader, and derivation across wheels

The formal half of `studies/CONNECTED_MACHINE_STUDY.md`.

**The router.** `glm_universal/runtime/router.py` gives a text to the first
surface, in a declared order, that reads it; a surface either reads the text
(`some verdict`, an answer or a refusal) or does not (`none`).

* `route_cons_none`, `route_prefix_none` — a surface in front of the others
  changes the verdict only for text it reads. This is why "the router leaves
  the planner's answers alone" reduces to counting which declared questions
  the earlier surfaces read.
* `route_cons_some`, `route_append_of_some` — a surface that reads decides,
  and adding surfaces at the end never changes a verdict already given.
* `route_total` — with a last surface that reads everything, every text gets
  a verdict.

**The union of wheels.** A formula wheel's axioms are relation vectors, and a
formula is derivable when its relation vector lies in their rational span
(`Derivable`), as `glm_universal/engineering/wheels.py` solves it.

* `derivable_mono` — a larger union of wheels derives everything a smaller
  one does.
* `licensed_sound` — splitting a shared name into one copy per wheel is sound:
  a derivation over the split names maps, by forgetting the copies, to a
  derivation over the naive names (any linear map carries derivations).
* `not_derivable_of_functional` — a linear functional that vanishes on every
  axiom and not on the target certifies that the target is not derivable.
* `emc2_naive`, `emc2_refused_split`, `emc2_refused_split_photon` — the naive
  union of the linear-dynamics wheel W5 and the photon wheel W10 derives
  `energy = 2 * mass * speed_of_light ^ 2`; once `energy` and `momentum` are
  split between the two wheels, neither copy of `energy` is derivable so.
* `hydraulic_licensed` — across the declared junction of W5 and W6 (force and
  velocity identified), `power = pressure * volume_flow_rate` is derivable.
-/

@[expose] public section

namespace GLM.ConnectedMachine

/-! ## The router -/

section Router

variable {T V : Type*}

/-- Give `t` to the first surface that reads it. -/
def route : List (T → Option V) → T → Option V
  | [], _ => none
  | s :: ss, t =>
    match s t with
    | some v => some v
    | none => route ss t

theorem route_nil (t : T) : route ([] : List (T → Option V)) t = none := rfl

theorem route_cons_none (s : T → Option V) (ss : List (T → Option V)) (t : T)
    (h : s t = none) : route (s :: ss) t = route ss t := by
  simp [route, h]

theorem route_cons_some (s : T → Option V) (ss : List (T → Option V)) (t : T)
    (v : V) (h : s t = some v) : route (s :: ss) t = some v := by
  simp [route, h]

/-- Surfaces placed in front that do not read `t` leave its verdict alone. -/
theorem route_prefix_none (pre ss : List (T → Option V)) (t : T)
    (h : ∀ s ∈ pre, s t = none) : route (pre ++ ss) t = route ss t := by
  induction pre with
  | nil => rfl
  | cons p ps ih =>
    rw [List.cons_append, route_cons_none p _ t (h p (by simp))]
    exact ih (fun s hs => h s (by simp [hs]))

/-- Adding surfaces at the end never changes a verdict already given. -/
theorem route_append_of_some (ss tt : List (T → Option V)) (t : T) (v : V)
    (h : route ss t = some v) : route (ss ++ tt) t = some v := by
  induction ss with
  | nil => simp [route] at h
  | cons s ss ih =>
    cases hs : s t with
    | none =>
      rw [route_cons_none s ss t hs] at h
      rw [List.cons_append, route_cons_none s _ t hs]
      exact ih h
    | some w =>
      rw [route_cons_some s ss t w hs] at h
      rw [List.cons_append, route_cons_some s _ t w hs]
      exact h

/-- With a last surface that reads everything, every text gets a verdict. -/
theorem route_total (ss : List (T → Option V)) (last : T → Option V)
    (h : ∀ t, (last t).isSome) (t : T) : (route (ss ++ [last]) t).isSome := by
  induction ss with
  | nil =>
    cases hl : last t with
    | none => simpa [hl] using h t
    | some w => simp [route, hl]
  | cons s ss ih =>
    cases hs : s t with
    | none => rw [List.cons_append, route_cons_none s _ t hs]; exact ih
    | some w => rw [List.cons_append, route_cons_some s _ t w hs]; rfl

end Router

/-! ## Derivation across a union of wheels -/

section Union

variable {M N : Type*} [AddCommGroup M] [Module ℚ M] [AddCommGroup N] [Module ℚ N]

/-- A relation is derivable from axioms when it lies in their rational span. -/
def Derivable (S : Set M) (v : M) : Prop := v ∈ Submodule.span ℚ S

theorem derivable_mono {S S' : Set M} (hS : S ⊆ S') {v : M}
    (h : Derivable S v) : Derivable S' v :=
  Submodule.span_mono hS h

/-- Soundness of splitting: any linear map — in particular forgetting which
wheel a copy of a name belongs to — carries derivations to derivations. -/
theorem licensed_sound (f : M →ₗ[ℚ] N) {S : Set M} {v : M}
    (h : Derivable S v) : Derivable (f '' S) (f v) := by
  unfold Derivable
  rw [Submodule.span_image]
  exact Submodule.mem_map_of_mem h

/-- A functional vanishing on every axiom and not on the target certifies
that the target is not derivable. -/
theorem not_derivable_of_functional (φ : M →ₗ[ℚ] ℚ) {S : Set M} {v : M}
    (hS : ∀ s ∈ S, φ s = 0) (hv : φ v ≠ 0) : ¬ Derivable S v := by
  intro h
  have hle : Submodule.span ℚ S ≤ LinearMap.ker φ :=
    Submodule.span_le.mpr (fun s hs => by simpa using hS s hs)
  exact hv (by simpa using hle h)

end Union

/-! ### The photon conflation, concretely

Naive coordinates (`Fin 11`): `0` the prime 2 of the coefficient, `1` energy,
`2` mass, `3` velocity, `4` momentum, `5` speed of light, `6` Planck's
constant, `7` frequency, `8` force, `9` acceleration, `10` power. A relation
`L = R` is the vector of exponents of `L / R`, as `wheels.relation_vector`
writes it. -/

section Photon

/-- W5 and W10 over the naive names. -/
def naiveW5W10 : Set (Fin 11 → ℚ) :=
  { ![0, 0, -1, 0, 0, 0, 0, 0, 1, -1, 0],     -- force = mass * acceleration
    ![0, 0, -1, -1, 1, 0, 0, 0, 0, 0, 0],     -- momentum = mass * velocity
    ![0, 0, 0, -1, 0, 0, 0, 0, -1, 0, 1],     -- power = force * velocity
    ![1, 1, -1, -2, 0, 0, 0, 0, 0, 0, 0],     -- energy = 1/2 * mass * velocity^2
    ![0, 1, 0, 0, 0, 0, -1, -1, 0, 0, 0],     -- energy = planck * frequency
    ![0, 1, 0, 0, -1, -1, 0, 0, 0, 0, 0] }    -- energy = c * momentum

/-- `energy = 2 * mass * speed_of_light ^ 2` over the naive names. -/
def emc2 : Fin 11 → ℚ := ![-1, 1, -1, 0, 0, -2, 0, 0, 0, 0, 0]

/-- The naive union derives the conflation: `-1` times kinetic energy, `2`
times momentum, `2` times the photon's `energy = c * momentum`. -/
theorem emc2_naive : Derivable naiveW5W10 emc2 := by
  have h : emc2 = (-1 : ℚ) • ![1, 1, -1, -2, 0, 0, 0, 0, 0, 0, 0]
      + (2 : ℚ) • ![0, 0, -1, -1, 1, 0, 0, 0, 0, 0, 0]
      + (2 : ℚ) • ![0, 1, 0, 0, -1, -1, 0, 0, 0, 0, 0] := by
    ext i; fin_cases i <;> simp [emc2] <;> norm_num
  rw [Derivable, h]
  refine Submodule.add_mem _ (Submodule.add_mem _ ?_ ?_) ?_ <;>
    refine Submodule.smul_mem _ _ (Submodule.subset_span ?_) <;>
    simp [naiveW5W10]

/-- Split coordinates (`Fin 13`): as above, with `1` and `4` now W5's energy
and momentum, and `11`, `12` the photon wheel's own copies. -/
def splitW5W10 : Set (Fin 13 → ℚ) :=
  { ![0, 0, -1, 0, 0, 0, 0, 0, 1, -1, 0, 0, 0],
    ![0, 0, -1, -1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    ![0, 0, 0, -1, 0, 0, 0, 0, -1, 0, 1, 0, 0],
    ![1, 1, -1, -2, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    ![0, 0, 0, 0, 0, 0, -1, -1, 0, 0, 0, 1, 0],
    ![0, 0, 0, 0, 0, -1, 0, 0, 0, 0, 0, 1, -1] }

/-- The certificate: speed of light plus the photon's energy plus Planck's
constant. It vanishes on every split axiom. -/
def photonWitness : (Fin 13 → ℚ) →ₗ[ℚ] ℚ :=
  LinearMap.proj (R := ℚ) (φ := fun _ : Fin 13 => ℚ) 5
    + LinearMap.proj (R := ℚ) (φ := fun _ : Fin 13 => ℚ) 11
    + LinearMap.proj (R := ℚ) (φ := fun _ : Fin 13 => ℚ) 6

theorem photonWitness_vanishes : ∀ s ∈ splitW5W10, photonWitness s = 0 := by
  intro s hs
  simp only [splitW5W10, Set.mem_insert_iff, Set.mem_singleton_iff] at hs
  rcases hs with rfl | rfl | rfl | rfl | rfl | rfl <;>
    simp [photonWitness]

/-- After splitting, W5's energy is not `2 * mass * speed_of_light ^ 2`. -/
theorem emc2_refused_split :
    ¬ Derivable splitW5W10 ![-1, 1, -1, 0, 0, -2, 0, 0, 0, 0, 0, 0, 0] :=
  not_derivable_of_functional photonWitness photonWitness_vanishes
    (by simp [photonWitness])

/-- Nor is the photon wheel's copy of energy. -/
theorem emc2_refused_split_photon :
    ¬ Derivable splitW5W10 ![-1, 0, -1, 0, 0, -2, 0, 0, 0, 0, 0, 1, 0] :=
  not_derivable_of_functional photonWitness photonWitness_vanishes
    (by simp [photonWitness]; norm_num)

end Photon

/-! ### Hydraulic power across the declared junction

Coordinates (`Fin 6`): `0` power, `1` force, `2` velocity, `3` pressure,
`4` area, `5` volume flow rate; W5's force and velocity are W6's. -/

section Hydraulic

def junctionW5W6 : Set (Fin 6 → ℚ) :=
  { ![1, -1, -1, 0, 0, 0],     -- power = force * velocity        (W5)
    ![0, -1, 0, 1, 1, 0],      -- pressure = force / area          (W6)
    ![0, 0, -1, 0, -1, 1],     -- volume_flow_rate = area * velocity (W6)
    ![0, 1, 0, -1, -1, 0] }    -- force = pressure * area          (W6)

theorem hydraulic_licensed : Derivable junctionW5W6 ![1, 0, 0, -1, 0, -1] := by
  have h : (![1, 0, 0, -1, 0, -1] : Fin 6 → ℚ) = ![1, -1, -1, 0, 0, 0]
      + ![0, 1, 0, -1, -1, 0] - ![0, 0, -1, 0, -1, 1] := by
    ext i; fin_cases i <;> simp
  rw [Derivable, h]
  refine Submodule.sub_mem _ (Submodule.add_mem _ ?_ ?_) ?_ <;>
    exact Submodule.subset_span (by simp [junctionW5W6])

end Hydraulic

end GLM.ConnectedMachine
