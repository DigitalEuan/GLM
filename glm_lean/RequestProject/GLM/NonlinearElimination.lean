module

public import Mathlib

/-!
# Nonlinear elimination: what the branch layer rests on

`studies/NONLINEAR_ELIMINATION_STUDY.md` (Phase 103) adds a layer to the
`solve symbolically` operation that answers systems the substitution layer
of Phase 98 refuses `NONLINEAR`.  The computational half is
`overlay/glm_universal/reasoning/symbolic_nonlinear.py`.  This file proves
the facts its readings rest on.

## 1.  A quadratic has exactly its two branches

`quadratic_branches`: over a field in which `2 ≠ 0`, with `a ≠ 0` and
`s * s = b² - 4ac`, a root of `a x² + b x + c` is `(-b + s) / 2a` or
`(-b - s) / 2a`, and both are roots.  The layer prints exactly these two
branches, so it neither loses a root nor adds one.

## 2.  Conjugation carries a branch to a branch

The layer keeps a square root it cannot take as a named generator `√D` with
the single relation `√D² = D`, so every value lives in `R[X] / (X² - D)`.
`conj D` is the `R`-algebra map of that ring sending `√D` to `-√D`
(`conj_root`); it is an involution (`conj_conj`).  `conjugate_branch`: if
values satisfy a polynomial system with coefficients in `R`, their
conjugates satisfy it too.  This is why the layer may print the conjugate
of a verified branch as a second branch without deriving it again.

## 3.  A common root makes the resultant vanish

`resultant_eq_zero_of_common_root`: if `f` (of positive degree) and `g`
over `R` have a common root `a` after a ring map `φ : R → S` -- for the
layer, `R` holds the remaining letters and `φ` specialises them to a
solution -- then `φ (Res f g) = 0`.  So eliminating an unknown by the
resultant keeps every solution; what it may add is removed by the layer's
substitution check.

## 4.  Two systems solved completely

`elastic_collision_iff`: momentum and kinetic energy together have exactly
the two branches the layer prints (the bodies pass through each other
unchanged, or the textbook elastic collision).  `sum_product_iff`: two
numbers with sum `s` and product `p` are the two branches of the quadratic
`t² - s t + p`.
-/

@[expose] public section

namespace GLM.NonlinearElimination

open Polynomial

/-! ## 1.  The quadratic -/

/-- A quadratic with `a ≠ 0` has exactly the two branches
`(-b ± s) / 2a`, where `s * s` is the discriminant. -/
theorem quadratic_branches {K : Type*} [Field K] [NeZero (2 : K)] {a b c s : K}
    (ha : a ≠ 0) (hs : s * s = b ^ 2 - 4 * a * c) (x : K) :
    a * x ^ 2 + b * x + c = 0 ↔
      x = (-b + s) / (2 * a) ∨ x = (-b - s) / (2 * a) := by
  rw [show a * x ^ 2 = a * (x * x) by ring]
  exact quadratic_eq_zero_iff ha (by rw [discrim]; exact hs.symm) x

/-! ## 2.  Conjugation -/

section Conj

variable {R : Type*} [CommRing R]

theorem aeval_neg_root (D : R) :
    aeval (-AdjoinRoot.root (X ^ 2 - C D)) (X ^ 2 - C D) = 0 := by
  have h := AdjoinRoot.aeval_eq (f := X ^ 2 - C D) (X ^ 2 - C D)
  rw [AdjoinRoot.mk_self] at h
  simpa [neg_sq] using h

/-- The conjugation of `R[X] / (X² - D)`: the algebra map fixing `R` and
sending the generator `√D` to `-√D`. -/
noncomputable def conj (D : R) :
    AdjoinRoot (X ^ 2 - C D) →ₐ[R] AdjoinRoot (X ^ 2 - C D) :=
  AdjoinRoot.liftAlgHom (X ^ 2 - C D) (Algebra.ofId R _)
    (-AdjoinRoot.root (X ^ 2 - C D)) (by
      simpa [aeval_def] using aeval_neg_root D)

@[simp] theorem conj_root (D : R) :
    conj D (AdjoinRoot.root (X ^ 2 - C D)) = -AdjoinRoot.root (X ^ 2 - C D) := by
  simp [conj]

/-- Conjugation is an involution. -/
theorem conj_conj (D : R) (z : AdjoinRoot (X ^ 2 - C D)) :
    conj D (conj D z) = z := by
  have : (conj D).comp (conj D) = AlgHom.id R _ :=
    AdjoinRoot.algHom_ext (by simp)
  exact congrArg (fun φ : AdjoinRoot (X ^ 2 - C D) →ₐ[R] _ => φ z) this

/-- The conjugate of a solution of a polynomial system over `R` is a
solution. -/
theorem conjugate_branch (D : R) {ι : Type*} (F : MvPolynomial ι R)
    (v : ι → AdjoinRoot (X ^ 2 - C D)) (h : MvPolynomial.aeval v F = 0) :
    MvPolynomial.aeval (fun i => conj D (v i)) F = 0 := by
  rw [← MvPolynomial.comp_aeval_apply, h, map_zero]

end Conj

/-! ## 3.  The resultant -/

/-- A common root after specialisation makes the specialised resultant
vanish: eliminating by the resultant keeps every solution. -/
theorem resultant_eq_zero_of_common_root {R S : Type*} [CommRing R] [CommRing S]
    (φ : R →+* S) (f g : R[X]) (a : S) (hf : 0 < f.natDegree)
    (hfa : (f.map φ).eval a = 0) (hga : (g.map φ).eval a = 0) :
    φ (f.resultant g) = 0 := by
  rw [← resultant_map_map]
  obtain ⟨p, q, -, -, e⟩ := exists_mul_add_mul_eq_C_resultant (f.map φ) (g.map φ)
    natDegree_map_le natDegree_map_le (Or.inl hf.ne')
  have := congrArg (eval a) e
  simp only [eval_add, eval_mul, hfa, hga, zero_mul, add_zero, eval_C] at this
  exact this.symm

/-! ## 4.  Two systems solved completely -/

/-- Momentum and kinetic energy conserved: exactly the two branches. -/
theorem elastic_collision_iff {K : Type*} [Field K] {m₁ m₂ u v₁ v₂ : K}
    (h₁ : m₁ ≠ 0) (h₂ : m₂ ≠ 0) (h₁₂ : m₁ + m₂ ≠ 0) :
    (m₁ * v₁ + m₂ * v₂ = m₁ * u ∧ m₁ * v₁ ^ 2 + m₂ * v₂ ^ 2 = m₁ * u ^ 2) ↔
      (v₁ = u ∧ v₂ = 0) ∨
      (v₁ = u * (m₁ - m₂) / (m₁ + m₂) ∧ v₂ = 2 * m₁ * u / (m₁ + m₂)) := by
  constructor
  · rintro ⟨e₁, e₂⟩
    have hm : m₁ * (u - v₁) = m₂ * v₂ := by linear_combination -e₁
    have key : m₂ * (v₂ * (u + v₁ - v₂)) = 0 := by
      linear_combination (u + v₁) * e₁ - e₂
    rcases mul_eq_zero.mp ((mul_eq_zero.mp key).resolve_left h₂) with h | h
    · left
      refine ⟨?_, h⟩
      have : m₁ * (u - v₁) = 0 := by rw [hm, h, mul_zero]
      have := (mul_eq_zero.mp this).resolve_left h₁
      linear_combination -this
    · right
      have hv₂ : v₂ = u + v₁ := by linear_combination -h
      have hv₁ : (m₁ + m₂) * v₁ = u * (m₁ - m₂) := by
        rw [hv₂] at hm; linear_combination -hm
      refine ⟨?_, ?_⟩
      · field_simp; linear_combination hv₁
      · rw [hv₂]; field_simp; linear_combination hv₁
  · rintro (⟨rfl, rfl⟩ | ⟨rfl, rfl⟩)
    · constructor <;> ring
    · constructor
      · field_simp; ring
      · field_simp; ring

/-- Two numbers with sum `s` and product `p` are the two branches of
`t² - s t + p`, where `σ * σ = s² - 4p`. -/
theorem sum_product_iff {K : Type*} [Field K] [NeZero (2 : K)] {s p σ x y : K}
    (hσ : σ * σ = s ^ 2 - 4 * p) :
    (x * y = p ∧ x + y = s) ↔
      (x = (s + σ) / 2 ∧ y = (s - σ) / 2) ∨
      (x = (s - σ) / 2 ∧ y = (s + σ) / 2) := by
  have h2 : (2 : K) ≠ 0 := NeZero.ne 2
  constructor
  · rintro ⟨hp, hs⟩
    have hy : y = s - x := by linear_combination hs
    subst hy
    have hq : (1 : K) * x ^ 2 + (-s) * x + p = 0 := by linear_combination -hp
    rcases (quadratic_branches (s := σ) one_ne_zero (by linear_combination hσ) x).mp hq
      with h | h
    · left
      rw [h]
      exact ⟨by ring, by field_simp; ring⟩
    · right
      rw [h]
      exact ⟨by ring, by field_simp; ring⟩
  · rintro (⟨rfl, rfl⟩ | ⟨rfl, rfl⟩)
    · exact ⟨by field_simp; linear_combination -hσ, by field_simp; ring⟩
    · exact ⟨by field_simp; linear_combination -hσ, by field_simp; ring⟩

end GLM.NonlinearElimination
