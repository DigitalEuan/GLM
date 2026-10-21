import Mathlib

/-!
# The Pless symmetry code `C(23)` over `F₃` (the code under `Λ₄₈`; iteration 8, phase 4)

`C(23)` is the ternary `[48,24]` code with generator matrix `[I₂₄ | S]`, where `S` is the
bordered Jacobsthal (Paley) matrix of `q = 23`: indices `0 = ∞, 1..23 ↔ F₂₃`,
`S ∞ ∞ = 0`, `S ∞ j = 1`, `S i ∞ = -1`, `S i j = χ(j − i)` with `χ` the quadratic character.

Verified here (iteration 8's DI3/DI5 diagnosis):
* `S · Sᵀ = −I` over `F₃` (since `23 ≡ −1 mod 3`), and `S` is skew-symmetric;
* hence `[I | S]` generates a **self-dual** code (`I + S Sᵀ = 0`);
* `S` is invertible, so `ker S = ker Sᵀ = 0`: the iteration-7 `α`-embedding condition
  "target ∈ ker Sᵀ" is met only by the zero target.
-/

namespace GLMKit

open Matrix

/-- Quadratic character of `F₂₃`, with values in `F₃`. -/
def qr23 (x : ZMod 23) : ZMod 3 :=
  if x = 0 then 0 else if ∃ y : ZMod 23, y * y = x then 1 else -1

/-- The bordered Jacobsthal matrix `S` of the Pless symmetry code `C(23)`. -/
def plessS : Matrix (Fin 24) (Fin 24) (ZMod 3) :=
  Matrix.of fun i j =>
    if i = 0 then (if j = 0 then 0 else 1)
    else if j = 0 then -1
    else qr23 ((j : ℕ) - (i : ℕ) : ZMod 23)

theorem plessS_mul_transpose : plessS * plessSᵀ = -1 := by native_decide

theorem plessS_skew : plessSᵀ = -plessS := by native_decide

/-- The rows of `[I | S]` are pairwise orthogonal and self-orthogonal: `I·Iᵀ + S·Sᵀ = 0`,
so the Pless code `C(23)` (dimension 24, length 48) is self-dual. -/
theorem pless_generator_self_orthogonal : (1 : Matrix (Fin 24) (Fin 24) (ZMod 3)) + plessS * plessSᵀ = 0 := by
  rw [plessS_mul_transpose]; exact add_neg_cancel _

theorem plessS_transpose_mul : plessSᵀ * plessS = -1 := by native_decide

theorem plessS_isUnit_det : IsUnit plessS.det := by
  have h : plessS * (-plessSᵀ) = 1 := by rw [Matrix.mul_neg, plessS_mul_transpose, neg_neg]
  exact (Matrix.isUnit_det_of_right_inverse h)

/-- `ker S = 0`. -/
theorem plessS_ker_trivial (v : Fin 24 → ZMod 3) (h : plessS *ᵥ v = 0) : v = 0 := by
  have : (plessSᵀ * plessS) *ᵥ v = 0 := by rw [← Matrix.mulVec_mulVec, h, Matrix.mulVec_zero]
  rw [plessS_transpose_mul, Matrix.neg_mulVec, Matrix.one_mulVec, neg_eq_zero] at this
  exact this

/-- `ker Sᵀ = 0`: the only target admitting the iteration-7 `α`-embedding is `0`. -/
theorem plessS_transpose_ker_trivial (v : Fin 24 → ZMod 3) (h : plessSᵀ *ᵥ v = 0) : v = 0 := by
  have : (plessS * plessSᵀ) *ᵥ v = 0 := by rw [← Matrix.mulVec_mulVec, h, Matrix.mulVec_zero]
  rw [plessS_mul_transpose, Matrix.neg_mulVec, Matrix.one_mulVec, neg_eq_zero] at this
  exact this

end GLMKit
