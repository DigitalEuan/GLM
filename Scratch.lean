import Mathlib

noncomputable def entropyOf {Ω β : Type*} [Fintype Ω] [DecidableEq β]
    (p : Ω → ℝ) (f : Ω → β) : ℝ :=
  -∑ ω, p ω * Real.log (∑ ω', if f ω' = f ω then p ω' else 0)

noncomputable def ingletonLaw : Fin 4 → ℝ := ![1/3, 1/3, 1/6, 1/6]
def ingA : Fin 4 → Bool := ![false, true, true, true]
def ingB : Fin 4 → Bool := ![false, true, false, false]
def ingC : Fin 4 → Bool := ![false, true, true, false]
def ingD : Fin 4 → Bool := ![false, true, false, true]
noncomputable def ingH {β : Type*} [DecidableEq β] (f : Fin 4 → β) : ℝ :=
  entropyOf ingletonLaw f

noncomputable def ingIAB : ℝ := ingH ingA + ingH ingB - ingH (fun ω => (ingA ω, ingB ω))
noncomputable def ingRHS : ℝ :=
  (ingH (fun ω => (ingA ω, ingC ω)) + ingH (fun ω => (ingB ω, ingC ω)) -
      ingH (fun ω => (ingA ω, ingB ω, ingC ω)) - ingH ingC) +
    (ingH (fun ω => (ingA ω, ingD ω)) + ingH (fun ω => (ingB ω, ingD ω)) -
      ingH (fun ω => (ingA ω, ingB ω, ingD ω)) - ingH ingD) +
    (ingH ingC + ingH ingD - ingH (fun ω => (ingC ω, ingD ω)))

theorem ingleton_violated :
    ingIAB - ingRHS = 2 * Real.log 3 - 3 * Real.log 2 ∧ ingRHS < ingIAB := by
  have h6 : Real.log 6 = Real.log 2 + Real.log 3 := by
    rw [show (6:ℝ) = 2 * 3 by norm_num, Real.log_mul (by norm_num) (by norm_num)]
  have h12 : Real.log (1/2) = - Real.log 2 := by simp
  have h13 : Real.log (1/3) = - Real.log 3 := by simp
  have h16 : Real.log (1/6) = -(Real.log 2 + Real.log 3) := by simp [h6]
  have h23 : Real.log (2/3) = Real.log 2 - Real.log 3 := Real.log_div (by norm_num) (by norm_num)
  have h32 : Real.log (3/2) = Real.log 3 - Real.log 2 := Real.log_div (by norm_num) (by norm_num)
  have key : ingIAB - ingRHS = 2 * Real.log 3 - 3 * Real.log 2 := by
    simp [ingIAB, ingRHS, ingH, entropyOf, Fin.sum_univ_four, ingletonLaw, ingA, ingB, ingC, ingD]
    norm_num [h6, h12, h13, h16, h23, h32]
    ring
  refine ⟨key, ?_⟩
  have h89 : Real.log 8 < Real.log 9 := Real.log_lt_log (by norm_num) (by norm_num)
  rw [show (8:ℝ) = 2 ^ 3 by norm_num, show (9:ℝ) = 3 ^ 2 by norm_num, Real.log_pow,
    Real.log_pow] at h89
  push_cast at h89
  linarith
