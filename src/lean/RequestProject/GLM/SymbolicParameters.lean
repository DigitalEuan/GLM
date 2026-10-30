/-
# Symbolic parameters: the identities the formula answers rest on

Phase 98 (`studies/SYMBOLIC_PARAMETERS_STUDY.md`). The machine now answers
questions whose answer is a formula in letters, by writing the governing laws
as equations and eliminating the unknowns by declared substitution
(`glm_universal.reasoning.symbolic`). Its column-3 scripts check every answer
at rational points. What a finite check cannot give — that the formula holds
for *every* value of the letters — is proved here, for the outside frames
whose answer is a closed formula.

* `rolling_acceleration`, `rolling_friction_ratio` — a body with moment of
  inertia `k M R²` rolling without slipping down an incline of angle `θ` has
  `a = g sin θ / (1 + k)` and needs `μ = (k / (1 + k)) tan θ`; for every `k`
  (solid cylinder `1/2`, sphere `2/5`, hoop `1`, shell `2/3`).
* `invariant_mass_sq`, `invariant_mass_sq_identical` — a particle of rest
  mass `m₀` and Lorentz factor `γ` fusing with one of rest mass `k m₀` at
  rest gives `M² = m₀² (1 + k² + 2 k γ)`; for identical particles
  `M² = 2 m₀² (1 + γ)`.
* `disturbance_transfer` — with the setpoint at zero, a disturbance entering
  after the actuator reaches the output as `Gd Gp / (1 + Gc Gv Gp Gm)`.
* `interface_tangent_ratio` — continuity of tangential `E` and normal `D`
  gives `tan θ₁ / tan θ₂ = ε₁ / ε₂`.
* `ar1_autocorrelation` — white noise of unit variance through
  `h[n] = aⁿ u[n]`, `|a| < 1`, has output autocorrelation at lag `m` the sum
  of `aⁿ aⁿ⁺ᵐ`, which is `aᵐ / (1 − a²)`.
* `poly_eq_of_agree` — why checking at points is evidence at all: two
  polynomials of degree below `d` that agree at `d` distinct points are
  equal.
* `cramer_solves` — the path the operation takes for a square linear system
  of four or more unknowns: when the coefficient determinant is nonzero, the
  system holds exactly for `xᵢ = cramerᵢ / det` (existence and uniqueness),
  so answering by Cramer's rule loses and invents no solution.
-/
import Mathlib

namespace GLM.SymbolicParameters

/-- A body of moment of inertia `k M R²` rolling without slipping. -/
theorem rolling_acceleration (M g s R k a f α I : ℝ) (hM : M ≠ 0) (hR : R ≠ 0)
    (hk : 1 + k ≠ 0) (h1 : M * a = M * g * s - f) (h2 : f * R = I * α)
    (h3 : I = k * M * R ^ 2) (h4 : a = α * R) :
    a = g * s / (1 + k) := by
  have hfR : f * R = k * M * a * R := by
    linear_combination h2 + α * h3 - k * M * R * h4
  have hf : f = k * M * a := mul_right_cancel₀ hR hfR
  rw [eq_div_iff hk]
  apply mul_left_cancel₀ hM
  linear_combination h1 - hf

/-- The least coefficient of static friction for the rolling body. -/
theorem rolling_friction_ratio (M g s c R k a f α I N μ : ℝ) (hM : M ≠ 0)
    (hR : R ≠ 0) (hg : g ≠ 0) (hc : c ≠ 0) (hk : 1 + k ≠ 0)
    (h1 : M * a = M * g * s - f) (h2 : f * R = I * α)
    (h3 : I = k * M * R ^ 2) (h4 : a = α * R) (h5 : N = M * g * c)
    (h6 : f = μ * N) :
    μ = k / (1 + k) * (s / c) := by
  have ha := rolling_acceleration M g s R k a f α I hM hR hk h1 h2 h3 h4
  have hfR : f * R = k * M * a * R := by
    linear_combination h2 + α * h3 - k * M * R * h4
  have hf : f = k * M * a := mul_right_cancel₀ hR hfR
  have h7 : μ * (M * g * c) = k * M * (g * s / (1 + k)) := by
    rw [← h5, ← h6, hf, ha]
  have h8 : μ * (M * g * c) * (1 + k) = k * M * g * s := by
    rw [h7]; field_simp
  have hMg : M * g ≠ 0 := mul_ne_zero hM hg
  rw [div_mul_div_comm, eq_div_iff (mul_ne_zero hk hc)]
  apply mul_left_cancel₀ hMg
  linear_combination h8

/-- The invariant mass of the fusion product, target of rest mass `k m₀`. -/
theorem invariant_mass_sq (γ m₀ c v E p M k : ℝ) (hc : c ≠ 0)
    (hE : E = γ * m₀ * c ^ 2 + k * m₀ * c ^ 2) (hp : p = γ * m₀ * v)
    (hv : γ ^ 2 * (c ^ 2 - v ^ 2) = c ^ 2)
    (hM : M ^ 2 * c ^ 4 = E ^ 2 - p ^ 2 * c ^ 2) :
    M ^ 2 = m₀ ^ 2 * (1 + k ^ 2 + 2 * k * γ) := by
  subst hE hp
  have hc4 : c ^ 4 ≠ 0 := pow_ne_zero 4 hc
  apply mul_right_cancel₀ hc4
  linear_combination hM + m₀ ^ 2 * c ^ 2 * hv

/-- Identical particles: `M² = 2 m₀² (1 + γ)`. -/
theorem invariant_mass_sq_identical (γ m₀ c v E p M : ℝ) (hc : c ≠ 0)
    (hE : E = γ * m₀ * c ^ 2 + m₀ * c ^ 2) (hp : p = γ * m₀ * v)
    (hv : γ ^ 2 * (c ^ 2 - v ^ 2) = c ^ 2)
    (hM : M ^ 2 * c ^ 4 = E ^ 2 - p ^ 2 * c ^ 2) :
    M ^ 2 = 2 * m₀ ^ 2 * (1 + γ) := by
  have := invariant_mass_sq γ m₀ c v E p M 1 hc (by rw [hE]; ring) hp hv hM
  rw [this]; ring

/-- The closed loop with the disturbance entering after the actuator. -/
theorem disturbance_transfer (Gc Gv Gp Gm Gd D E U Y : ℝ)
    (hE : E = -Gm * Y) (hU : U = Gc * E) (hY : Y = Gp * (Gv * U + Gd * D))
    (h : 1 + Gc * Gv * Gp * Gm ≠ 0) :
    Y = Gd * Gp * D / (1 + Gc * Gv * Gp * Gm) := by
  rw [eq_div_iff h]
  linear_combination hY + Gp * Gv * hU + Gp * Gv * Gc * hE

/-- The tangent law at a dielectric interface. -/
theorem interface_tangent_ratio (E₁ E₂ ε₁ ε₂ s₁ c₁ s₂ c₂ : ℝ) (hE : E₁ ≠ 0)
    (hc₁ : c₁ ≠ 0) (hs₂ : s₂ ≠ 0) (hε : ε₂ ≠ 0)
    (h1 : E₁ * s₁ = E₂ * s₂) (h2 : ε₁ * E₁ * c₁ = ε₂ * E₂ * c₂) :
    (s₁ / c₁) / (s₂ / c₂) = ε₁ / ε₂ := by
  have key : E₁ * (ε₁ * c₁ * s₂ - ε₂ * s₁ * c₂) = 0 := by
    linear_combination s₂ * h2 - ε₂ * c₂ * h1
  have hrel : ε₁ * c₁ * s₂ = ε₂ * s₁ * c₂ := by
    rcases mul_eq_zero.mp key with h | h
    · exact absurd h hE
    · linear_combination h
  field_simp
  linear_combination -hrel

/-- Output autocorrelation of filtered unit white noise, lag `m ≥ 0`. -/
theorem ar1_autocorrelation (a : ℝ) (ha : |a| < 1) (m : ℕ) :
    HasSum (fun n : ℕ => a ^ n * a ^ (n + m)) (a ^ m / (1 - a ^ 2)) := by
  have h2 : |a ^ 2| < 1 := by
    rw [abs_pow]
    have h0 : 0 ≤ |a| := abs_nonneg a
    nlinarith
  have hg := (hasSum_geometric_of_abs_lt_one h2).mul_left (a ^ m)
  convert hg using 1
  funext n
  ring

/-- Two polynomials of degree below `card s` that agree on `s` are equal. -/
theorem poly_eq_of_agree {K : Type*} [Field K] (f g : Polynomial K)
    (s : Finset K) (hdeg : (f - g).degree < s.card)
    (hagree : ∀ x ∈ s, f.eval x = g.eval x) : f = g :=
  Polynomial.eq_of_degree_sub_lt_of_eval_finset_eq s hdeg hagree

open Matrix in
/-- Cramer's rule as an equivalence: with `det A ≠ 0`, `A x = b` holds exactly
for `x = cramer A b / det A`. -/
theorem cramer_solves {K : Type*} [Field K] {n : Type*} [Fintype n]
    [DecidableEq n] (A : Matrix n n K) (b : n → K) (h : A.det ≠ 0)
    (x : n → K) :
    A *ᵥ x = b ↔ x = fun i => cramer A b i / A.det := by
  constructor
  · rintro rfl
    funext i
    rw [cramer_eq_adjugate_mulVec, mulVec_mulVec, adjugate_mul, smul_mulVec,
      one_mulVec]
    simp [h]
  · rintro rfl
    have : (fun i => cramer A b i / A.det) = (A.det)⁻¹ • cramer A b := by
      funext i
      simp [div_eq_inv_mul]
    rw [this, mulVec_smul, mulVec_cramer, smul_smul, inv_mul_cancel₀ h,
      one_smul]

end GLM.SymbolicParameters
