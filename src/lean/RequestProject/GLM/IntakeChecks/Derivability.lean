module

public import Mathlib

/-!
# When a law follows from a wheel's axioms: the two certificates

*Created 1 November 2026 (Phase 186: `tool derive`, the cent wheels on the answering path,
directive D22; a standalone check, written for the absorption of `cent_compiler_v12` ahead of the
owner's build).*

A wheel's axioms are exponent vectors over the base dimensions; a law is derivable from them when
its vector is a rational combination of theirs (it lies in their span). The GLM's exact engine
answers with one of two certificates, and this file proves that each settles the question,
independently of `Wheels/CentWheels.lean` and `ConnectedMachine.lean`:

* `derivable_of_combination` — an explicit rational combination of the axioms equal to the law
  proves it derivable;
* `not_derivable_of_functional` — a linear functional that vanishes on every axiom but not on the
  law proves it *not* derivable (a separating functional);
* `force_example`, `energy_not_from_speed` — the two certificates on vectors over (L, M, T):
  force `M L T⁻²` from mass and acceleration, and energy `M L² T⁻²` not from a speed `L T⁻¹`
  alone (the functional reads the exponent of `M`).

Everything is formal; no `native_decide`.
-/

@[expose] public section

namespace GLM.IntakeChecks.Derivability

open Submodule

variable {n ι : Type*}

/-- A law is derivable from axioms when its exponent vector lies in their rational span. -/
def Derivable (axioms : ι → n → ℚ) (law : n → ℚ) : Prop :=
  law ∈ span ℚ (Set.range axioms)

/-- An explicit combination certifies derivability. -/
theorem derivable_of_combination [Fintype ι] (axioms : ι → n → ℚ) (law : n → ℚ) (c : ι → ℚ)
    (h : ∑ i, c i • axioms i = law) : Derivable axioms law := by
  rw [Derivable, ← h]
  exact sum_mem fun i _ => smul_mem _ _ (subset_span (Set.mem_range_self i))

/-- A separating functional certifies non-derivability. -/
theorem not_derivable_of_functional (axioms : ι → n → ℚ) (law : n → ℚ) (f : (n → ℚ) →ₗ[ℚ] ℚ)
    (hax : ∀ i, f (axioms i) = 0) (hlaw : f law ≠ 0) : ¬ Derivable axioms law := by
  intro hd
  apply hlaw
  have hle : span ℚ (Set.range axioms) ≤ LinearMap.ker f := by
    rw [span_le]
    rintro _ ⟨i, rfl⟩
    exact hax i
  exact hle hd

/-- Mass `M` and acceleration `L T⁻²` over (L, M, T). -/
def massAcceleration : Fin 2 → Fin 3 → ℚ := ![![0, 1, 0], ![1, 0, -2]]

/-- Force `M L T⁻²` is derivable from mass and acceleration (`F = m a`). -/
theorem force_example : Derivable massAcceleration ![1, 1, -2] :=
  derivable_of_combination _ _ ![1, 1] (by
    funext k; fin_cases k <;> simp [massAcceleration, Fin.sum_univ_two])

/-- Energy `M L² T⁻²` is not derivable from a speed `L T⁻¹` alone: the exponent of `M`
separates them. -/
theorem energy_not_from_speed : ¬ Derivable (fun _ : Fin 1 => ![1, 0, -1]) ![2, 1, -2] :=
  not_derivable_of_functional _ _ (LinearMap.proj 1) (fun _ => by simp) (by simp)

end GLM.IntakeChecks.Derivability
