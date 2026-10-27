import RequestProject.GLM.Rule30.Compute

/-!
# Round 45: a certificate for the full-range statement of engine v17's H16

(Not a `module`: the check uses `native_decide`, so the result is CERT.)

In its full run, the engine states H16 with a longer preperiod than the Wheel's version
(`WheelChecksData.wheel_H16_true`, preperiod `≤ 10000`):

  the centre column is not eventually periodic with period `p ≤ 64` and preperiod `≤ 30000`.

The v17 ledger gate declined to call that "proved", because no Lean result covered preperiod
`30000`. This file supplies one, with one witness per period, read from the verified
bit-parallel centre column (`fastList_eq`).
-/

namespace GLM.HypothesisEngine.GateLoopData

open GLM.Rule30

/-- The first 32000 centre bits, from the verified fast generator. -/
def arr32000 : Array Bool := (fastList 32000).toArray

theorem arr32000_getD (n : ℕ) (hn : n < 32000) : arr32000.getD n false = centerCol n := by
  rw [arr32000, fastList_eq]
  simp [Array.getD_eq_getD_getElem?, List.getElem?_range hn]

theorem h16_30000_check : ∀ p < 65, 1 ≤ p →
    ∃ n < 31900, 30000 ≤ n ∧ arr32000.getD (n + p) false ≠ arr32000.getD n false := by
  native_decide

/-- **Engine v17's full-range H16 is true**: the centre column has no eventual period `p ≤ 64`
with preperiod `τ ≤ 30000`. -/
theorem centre_no_short_period_30000 : ∀ τ ≤ 30000, ∀ p, 1 ≤ p → p ≤ 64 →
    ¬ ∀ n ≥ τ, centerCol (n + p) = centerCol n := by
  intro τ hτ p hp1 hp h
  obtain ⟨n, hn, hn', hne⟩ := h16_30000_check p (by omega) hp1
  rw [arr32000_getD _ (by omega), arr32000_getD _ (by omega)] at hne
  exact hne (h n (by omega))

end GLM.HypothesisEngine.GateLoopData
