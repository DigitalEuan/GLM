/-
# The 2A Sakuma product is not associative, and the XOR shortcut is

The GLM composes Monster addresses plane by plane.  The implementation used to
do this with a bitwise `XOR` of the class labels, which is the group law of
`Λ / 2Λ`.  The exact rule is the Norton–Sakuma relation for a `2A` pair,

  `a · b = (1/8) (a + b - a_ρ)`,

where `a_ρ` is the third axis of the pair.  The two disagree in a way that no
amount of care with the shortcut can repair: the shortcut is **associative** and
the algebra is **not**.

This file makes that precise on the smallest structure that carries it — the
three-dimensional space spanned by one triple of pairwise-`2A` axes.  The
product of two distinct axes is the Sakuma combination, an axis squares to
itself, and the product is extended bilinearly.  Then:

* `axisProduct_comm` — the product is commutative;
* `sakuma_left`, `sakuma_right` — the two bracketings of `e₀ · e₁ · e₂` are the
  exact vectors `-3/32 · e₂` and `-3/32 · e₀`;
* `sakuma_not_associative` — they differ, so the algebra is not associative;
* `xor_shortcut_assoc` — the label `XOR` the implementation used instead *is*
  associative.

The rational coefficient `-3/32` is the same one the package's
`reasoning/monster_stack` reports for its own witness triple, computed there
over the substrate's exhaustive table of type-2 classes.
-/
import Mathlib

namespace GLM.Sakuma

open Finset

/-- The span of one triple of pairwise-`2A` axes, over `ℚ`. -/
abbrev V : Type := Fin 3 → ℚ

/-- The `i`-th axis. -/
def e (i : Fin 3) : V := fun j => if j = i then 1 else 0

/-- The third axis of a `2A` pair; on the diagonal the value is unused. -/
def third : Fin 3 → Fin 3 → Fin 3 := ![![0, 2, 1], ![2, 1, 0], ![1, 0, 2]]

/-- The product of two axes: idempotent on the diagonal, and the Norton–Sakuma
combination `(1/8)(a + b - a_ρ)` off it. -/
noncomputable def axisProduct (i j : Fin 3) : V :=
  if i = j then e i else (1 / 8 : ℚ) • (e i + e j - e (third i j))

/-- The bilinear extension of `axisProduct` to the whole space. -/
noncomputable def mul (u v : V) : V :=
  ∑ i : Fin 3, ∑ j : Fin 3, (u i * v j) • axisProduct i j

@[inherit_doc] infixl:70 " ⋆ " => mul

/-! ## The product on axes -/

theorem third_symm (i j : Fin 3) (h : i ≠ j) : third i j = third j i := by
  fin_cases i <;> fin_cases j <;> simp_all [third]

theorem axisProduct_comm (i j : Fin 3) : axisProduct i j = axisProduct j i := by
  fin_cases i <;> fin_cases j <;> funext k <;> fin_cases k <;>
    simp [axisProduct, third, e]

theorem axisProduct_self (i : Fin 3) : axisProduct i i = e i := by
  simp [axisProduct]

/-- The Sakuma relation, in the form the implementation must use. -/
theorem axisProduct_of_ne {i j : Fin 3} (h : i ≠ j) :
    axisProduct i j = (1 / 8 : ℚ) • (e i + e j - e (third i j)) := by
  simp [axisProduct, h]

theorem mul_axis (i j : Fin 3) : e i ⋆ e j = axisProduct i j := by
  fin_cases i <;> fin_cases j <;> simp [mul, e]

/-! ## The two bracketings -/

theorem sakuma_left : (e 0 ⋆ e 1) ⋆ e 2 = (-3 / 32 : ℚ) • e 2 := by
  rw [mul_axis]
  funext k
  fin_cases k <;>
    all_goals (simp [mul, axisProduct, third, e, Fin.sum_univ_three]
               try norm_num)

theorem sakuma_right : e 0 ⋆ (e 1 ⋆ e 2) = (-3 / 32 : ℚ) • e 0 := by
  rw [mul_axis]
  funext k
  fin_cases k <;>
    all_goals (simp [mul, axisProduct, third, e, Fin.sum_univ_three]
               try norm_num)

/-- **The algebra is not associative.**  The two bracketings of the same triple
of pairwise-`2A` axes are supported on *different* axes. -/
theorem sakuma_not_associative : (e 0 ⋆ e 1) ⋆ e 2 ≠ e 0 ⋆ (e 1 ⋆ e 2) := by
  rw [sakuma_left, sakuma_right]
  intro h
  have := congrFun h 0
  norm_num [e] at this
  exact absurd this (by decide)

/-- **The shortcut is associative.**  Composing address labels by bitwise `XOR`
is the group law of `Λ / 2Λ`, so it can never see the failure above. -/
theorem xor_shortcut_assoc (a b c : ℕ) : (a ^^^ b) ^^^ c = a ^^^ (b ^^^ c) :=
  Nat.xor_assoc a b c

/-- The shortcut returns the third-axis label, which is one term of a
three-term product: precisely the two terms it discards are `e i` and `e j`. -/
theorem sakuma_has_three_terms {i j : Fin 3} (h : i ≠ j) :
    axisProduct i j
      = (1 / 8 : ℚ) • e i + (1 / 8 : ℚ) • e j - (1 / 8 : ℚ) • e (third i j) := by
  rw [axisProduct_of_ne h]
  module

end GLM.Sakuma
