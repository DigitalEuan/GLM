module

public import Mathlib
public import RequestProject.GLM.QuinticRadicals

/-!
# Roots with no expression in radicals, through a composition

`studies/COMPOSED_RADICAL_STUDY.md` (Phase 115) carries the radical-free
statement of `solve symbolically` to polynomials that are compositions
`g(h(x))`.  Their Galois groups are imprimitive — the roots fall into blocks,
one for each root of `g` — so the certificates of Phases 113 and 114, which
need a primitive group, never apply to them; `x^10 - x^2 - 1 = g(x^2)` with
`g = y^5 - y - 1` was the declared silent case of Phase 114.

## What is proved here

* `no_radical_root_of_comp` — **the certificate the layer cites**: if no
  complex root of `g` is solvable by radicals over `ℚ`, then no complex root
  of `g.comp h` is, for every `h : ℚ[X]`.  If `x` were solvable by radicals,
  so would be `h(x)`, a root of `g`: the numbers solvable by radicals form a
  field containing `ℚ`.
* `no_radical_root_of_comp_X_pow`: the same for `g(x^k)`, the case the layer
  meets most often.
* `decic_no_radical_root`: a fully proved instance in composite degree — no
  complex root of `x^10 - 4x^2 + 2` is solvable by radicals, from Phase 112's
  `x^5 - 4x + 2` (`GLM.QuinticRadicals.trinomial_no_radical_root`).

## What is not proved here

The layer applies `no_radical_root_of_comp` with a `g` certified by one of
the earlier certificates; where that certificate reads Frobenius elements,
Dedekind's theorem is used and not proved in Lean (as in Phases 113 and 114).
The decomposition `f = g ∘ h` itself is found and checked exactly by the
Python side.
-/

@[expose] public section

namespace GLM.ComposedRadicals

open Polynomial

/-- **The composition certificate.**  If no complex root of `g` is solvable by
radicals over `ℚ`, then no complex root of `g ∘ h` is. -/
theorem no_radical_root_of_comp {g : ℚ[X]}
    (hg : ∀ y : ℂ, aeval y g = 0 → ¬ IsSolvableByRad ℚ y) (h : ℚ[X])
    (x : ℂ) (hx : aeval x (g.comp h) = 0) : ¬ IsSolvableByRad ℚ x := by
  intro hsol
  have hmem : x ∈ solvableByRad ℚ ℂ := hsol
  have himg : aeval x h ∈ (solvableByRad ℚ ℂ).toSubalgebra := by
    have hcoe := aeval_subalgebra_coe h (solvableByRad ℚ ℂ).toSubalgebra ⟨x, hmem⟩
    simp only at hcoe
    rw [← hcoe]
    exact SetLike.coe_mem _
  rw [aeval_comp] at hx
  exact hg _ hx himg

/-- The composition certificate for `g(x^k)`. -/
theorem no_radical_root_of_comp_X_pow {g : ℚ[X]}
    (hg : ∀ y : ℂ, aeval y g = 0 → ¬ IsSolvableByRad ℚ y) (k : ℕ)
    (x : ℂ) (hx : aeval x (g.comp (X ^ k)) = 0) : ¬ IsSolvableByRad ℚ x :=
  no_radical_root_of_comp hg (X ^ k) x hx

/-- **A decic with no root in radicals.**  No complex root of
`x^10 - 4x^2 + 2` is solvable by radicals over `ℚ`. -/
theorem decic_no_radical_root (x : ℂ) (hx : x ^ 10 - 4 * x ^ 2 + 2 = 0) :
    ¬ IsSolvableByRad ℚ x := by
  refine no_radical_root_of_comp_X_pow
    GLM.QuinticRadicals.trinomial_no_radical_root 2 x ?_
  simp only [GLM.QuinticRadicals.trinomial, aeval_comp, map_add, map_sub,
    map_mul, map_pow, aeval_X, aeval_C]
  have : x ^ 10 = (x ^ 2) ^ 5 := by ring
  simpa [this] using hx

end GLM.ComposedRadicals
