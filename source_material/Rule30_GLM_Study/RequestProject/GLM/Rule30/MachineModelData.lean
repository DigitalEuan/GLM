import RequestProject.GLM.Rule30.MachineModel

/-!
# Machine model: exhaustive checks

(This file is deliberately not a `module`: it uses `native_decide`, which needs the compiled code
of the definitions.)

* `wholeCone_le_6` : for `t ≤ 6` the centre cell `a(t)(0)` depends on every one of the `2t+1`
  cells of its light cone (evidence class `EXH`).
* `circuit_size_ge_le_6` : so for `t ≤ 6` every circuit computing the light-cone map has at least
  `t` gates.
-/

namespace GLM.Rule30

/-- Whole-cone dependence holds for `t ≤ 6` (exhaustive computation). -/
theorem wholeCone_le_6 : ∀ t ≤ 6, ∀ i : Fin (2 * t + 1), Essential (centreWindow t) i := by
  have h : ∀ t : Fin 7, ∀ i : Fin (2 * t + 1), essentialB (centreWindow t) i = true := by
    native_decide
  intro t ht i
  have := h ⟨t, by omega⟩ i
  simpa [essentialB] using this

/-- Unconditionally for `t ≤ 6`. -/
theorem circuit_size_ge_le_6 (t : ℕ) (ht : t ≤ 6)
    (C : Circuit (2 * t + 1)) (hC : C.Computes (centreWindow t)) : t ≤ C.size := by
  have := card_essential_le C _ hC Finset.univ (fun i _ => wholeCone_le_6 t ht i)
  simp at this
  omega

end GLM.Rule30
