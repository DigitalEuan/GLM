/-
# The state–field map `Y(u, z)` on the `2A` Sakuma algebra

`Sakuma.lean` builds the three-dimensional span of one triple of pairwise-`2A`
axes and shows that its product is commutative and **not** associative.  That
algebra is the Griess-algebra layer of a vertex operator algebra: in a VOA the
Griess product of two weight-two states `u, v` is the single mode `u₁ v`, one
coefficient of the state–field map

  `Y(u, z) = ∑_{n ∈ ℤ} uₙ z^{-n-1}`.

This file builds that map on the `2A` algebra — the modes, the truncation
condition, the invariant form and the vacuum — and then states exactly how far
it gets, which is the honest answer to the question the study left open.

## What is built

* `mode u n` — the `n`-th mode operator of the state `u`.  On the Griess layer
  only `n = 1` survives, and `mode u 1 v = u ⋆ v` is the Sakuma product.
* `Y u v` — the state–field map as a formal Laurent series in `z`, presented by
  its coefficient function `n ↦ uₙ v`.
* `form` — the invariant bilinear form.  It is not chosen: invariance
  (`form_invariant`) plus the normalisation `⟨eᵢ, eᵢ⟩ = 1` forces
  `⟨eᵢ, eⱼ⟩ = 1/8` for `i ≠ j`, because `⟨eᵢ ⋆ eᵢ, eⱼ⟩ = ⟨eᵢ, eᵢ ⋆ eⱼ⟩` reads
  `⟨eᵢ, eⱼ⟩ = (1/8)⟨eᵢ, eᵢ⟩` off the diagonal.
* `vac` — the identity of the algebra, `(4/5)(e₀ + e₁ + e₂)`, which is what
  plays the part of the vacuum at this layer.

## What is proved

* `mode_truncated` — every field is truncated: `uₙ v = 0` for `n ≥ 2`, so
  `Y(u, z) v` really is a formal Laurent series with finitely many positive
  modes.  Here it is a single term, `(u ⋆ v) z^{-2}`.
* `mode_linear_left`, `mode_linear_right` — each mode is bilinear in the state
  and the argument.
* `mode_skew` — `u₁ v = v₁ u`, the skew-symmetry axiom at this weight; it is
  exactly the commutativity of the Griess product.
* `form_symm`, `form_invariant`, `mode_self_adjoint` — the form is symmetric
  and invariant, so every mode operator is self-adjoint for it.  This is the
  VOA-theoretic content the finite layer does carry.
* `form_nondegenerate` — the form is nondegenerate, so the layer is a Frobenius
  algebra.
* `vac_mul`, `mul_vac`, `form_vac` — the vacuum is a two-sided identity and has
  square length `12/5`.

## What is *not* true, and why the finite layer is not enough

Borcherds' commutator formula, at `m = n = 1`, reads

  `[u₁, v₁] w = ∑_{i ≥ 0} (1 choose i) (uᵢ v)_{2-i} w = (u₀ v)₂ w + (u₁ v)₁ w`.

On the Griess layer every mode but the first vanishes, so the formula would
demand

  `u ⋆ (v ⋆ w) - v ⋆ (u ⋆ w) = (u ⋆ v) ⋆ w`.

`borcherds_commutator_fails` exhibits the triple `e₀, e₁, e₂` where the two
sides are `(-3/32) e₀ + (3/32) e₁` and `(-3/32) e₂`.  So the three-dimensional
algebra, with its modes truncated to the one the Griess product provides, is
**not** a vertex algebra: the modes `u₀`, `u₂`, `u₃`, … that the truncation
throws away are load-bearing, and reinstating them leaves the finite
dimensional setting for good.  `modes_do_not_commute` records the same fact in
operator form — the mode operators of two distinct axes fail to commute, which
is precisely the non-associativity of `Sakuma.lean` seen from the field side.

This is as far as a finite-dimensional model reaches.  The infinite-dimensional
half of the Moonshine bridge is not built here, and nothing in this file
claims it is.
-/
import RequestProject.GLM.Sakuma

namespace GLM.VOA

open Finset GLM.Sakuma

/-- The Griess-algebra layer: the span of one triple of pairwise-`2A` axes. -/
abbrev V : Type := GLM.Sakuma.V

/-! ## 1.  The modes of the state–field map -/

/-- The `n`-th mode operator of the state `u`, on the Griess layer.

In a vertex operator algebra the Griess product of two weight-two states is
the mode `u₁ v`; the layer this file models carries that mode and no other. -/
noncomputable def mode (u : V) (n : ℤ) (v : V) : V :=
  if n = 1 then u ⋆ v else 0

/-- The state–field map `Y(u, z) = ∑ₙ uₙ z^{-n-1}`, presented by its
coefficient function: `Y u v n` is the coefficient of `z^{-n-1}`. -/
noncomputable def Y (u v : V) (n : ℤ) : V := mode u n v

theorem Y_apply (u v : V) (n : ℤ) : Y u v n = mode u n v := rfl

@[simp] theorem mode_one (u v : V) : mode u 1 v = u ⋆ v := by
  simp [mode]

@[simp] theorem mode_of_ne {n : ℤ} (h : n ≠ 1) (u v : V) : mode u n v = 0 := by
  simp [mode, h]

/-- **Truncation.**  A field has only finitely many positive modes; here the
last one is `n = 1`, so `Y(u, z) v = (u ⋆ v) z^{-2}`. -/
theorem mode_truncated (u v : V) {n : ℤ} (hn : 2 ≤ n) : mode u n v = 0 :=
  mode_of_ne (by omega) u v

/-- The only surviving coefficient is the one at `z^{-2}`. -/
theorem Y_eq_single (u v : V) (n : ℤ) :
    Y u v n = if n = 1 then u ⋆ v else 0 := rfl

/-! ## 2.  Bilinearity -/

theorem mul_add_left (u v w : V) : (u + v) ⋆ w = u ⋆ w + v ⋆ w := by
  funext k
  simp only [mul, Pi.add_apply, Finset.sum_apply, Pi.smul_apply, smul_eq_mul]
  rw [← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl fun j _ => by ring

theorem mul_add_right (u v w : V) : u ⋆ (v + w) = u ⋆ v + u ⋆ w := by
  funext k
  simp only [mul, Pi.add_apply, Finset.sum_apply, Pi.smul_apply, smul_eq_mul]
  rw [← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [← Finset.sum_add_distrib]
  exact Finset.sum_congr rfl fun j _ => by ring

theorem mul_smul_left (c : ℚ) (u v : V) : (c • u) ⋆ v = c • (u ⋆ v) := by
  funext k
  simp only [mul, Pi.smul_apply, Finset.sum_apply, smul_eq_mul,
    Finset.mul_sum]
  exact Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => by ring

theorem mul_smul_right (c : ℚ) (u v : V) : u ⋆ (c • v) = c • (u ⋆ v) := by
  funext k
  simp only [mul, Pi.smul_apply, Finset.sum_apply, smul_eq_mul,
    Finset.mul_sum]
  exact Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => by ring

/-- Each mode is linear in the state it comes from. -/
theorem mode_linear_left (n : ℤ) (c : ℚ) (u u' v : V) :
    mode (u + c • u') n v = mode u n v + c • mode u' n v := by
  by_cases h : n = 1
  · subst h; simp [mul_add_left, mul_smul_left]
  · simp [h]

/-- Each mode is a linear operator. -/
theorem mode_linear_right (n : ℤ) (c : ℚ) (u v v' : V) :
    mode u n (v + c • v') = mode u n v + c • mode u n v' := by
  by_cases h : n = 1
  · subst h; simp [mul_add_right, mul_smul_right]
  · simp [h]

/-! ## 3.  Skew-symmetry -/

theorem mul_comm' (u v : V) : u ⋆ v = v ⋆ u := by
  funext k
  simp only [mul, Finset.sum_apply, Pi.smul_apply, smul_eq_mul]
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => by
    rw [axisProduct_comm]; ring

/-- **Skew-symmetry at weight two.**  In a VOA the skew-symmetry axiom relates
`Y(u, z) v` to `Y(v, -z) u`; at this single mode it says the Griess product is
commutative, which it is. -/
theorem mode_skew (u v : V) : mode u 1 v = mode v 1 u := by
  simp [mul_comm']

/-! ## 4.  The invariant form -/

/-- The form on the axes.  The off-diagonal value is forced by invariance and
the normalisation `⟨eᵢ, eᵢ⟩ = 1`; see `form_forced_off_diagonal`. -/
def formCoeff (i j : Fin 3) : ℚ := if i = j then 1 else 1 / 8

/-- The invariant bilinear form of the layer. -/
def form (u v : V) : ℚ := ∑ i : Fin 3, ∑ j : Fin 3, u i * v j * formCoeff i j

@[simp] theorem form_axis (i j : Fin 3) : form (e i) (e j) = formCoeff i j := by
  fin_cases i <;> fin_cases j <;>
    simp [form, formCoeff, e, Fin.sum_univ_three]

theorem form_symm (u v : V) : form u v = form v u := by
  simp only [form]
  rw [Finset.sum_comm]
  exact Finset.sum_congr rfl fun i _ => Finset.sum_congr rfl fun j _ => by
    unfold formCoeff
    by_cases h : j = i
    · subst h; ring
    · rw [if_neg h, if_neg (Ne.symm h)]; ring

/-- **Invariance.**  `⟨u ⋆ v, w⟩ = ⟨u, v ⋆ w⟩`: every mode operator is
self-adjoint for the form.  This is the piece of vertex-algebra structure the
finite layer does carry. -/
theorem form_invariant (u v w : V) : form (u ⋆ v) w = form u (v ⋆ w) := by
  simp [form, mul, formCoeff, axisProduct, third, e, Fin.sum_univ_three]
  ring

/-- The same statement in the language of modes: `u₁` is self-adjoint. -/
theorem mode_self_adjoint (u v w : V) :
    form (mode u 1 v) w = form v (mode u 1 w) := by
  rw [mode_one, mode_one, mul_comm' u v, form_invariant]

/-- The off-diagonal value of the form is not a choice.  Invariance applied to
`⟨eᵢ ⋆ eᵢ, eⱼ⟩ = ⟨eᵢ, eᵢ ⋆ eⱼ⟩` reads `⟨eᵢ, eⱼ⟩ = (1/8)⟨eᵢ, eᵢ⟩`. -/
theorem form_forced_off_diagonal {i j : Fin 3} (h : i ≠ j) :
    form (e i) (e j) = (1 / 8 : ℚ) * form (e i) (e i) := by
  fin_cases i <;> fin_cases j <;> simp_all [formCoeff]

/-- **Nondegeneracy.**  The layer is a Frobenius algebra. -/
theorem form_nondegenerate {u : V} (h : ∀ w : V, form u w = 0) : u = 0 := by
  have h0 := h (e 0)
  have h1 := h (e 1)
  have h2 := h (e 2)
  simp [form, formCoeff, e, Fin.sum_univ_three] at h0 h1 h2
  funext k
  fin_cases k <;> simp <;> linarith

/-! ## 5.  The vacuum -/

/-- The identity of the layer, `(4/5)(e₀ + e₁ + e₂)`.  It is what plays the
part of the vacuum: `Y(vac, z)` acts as the identity operator at the single
surviving mode. -/
def vac : V := fun _ => 4 / 5

theorem vac_mul (v : V) : vac ⋆ v = v := by
  funext k
  fin_cases k <;>
    simp [mul, vac, axisProduct, third, e, Fin.sum_univ_three] <;> ring

theorem mul_vac (v : V) : v ⋆ vac = v := by
  rw [mul_comm', vac_mul]

/-- `Y(vac, z)` is the identity operator at the mode the layer carries. -/
theorem mode_vac (v : V) : mode vac 1 v = v := by
  simp [vac_mul]

/-- The vacuum has square length `12/5`. -/
theorem form_vac : form vac vac = 12 / 5 := by
  simp [form, vac, formCoeff, Fin.sum_univ_three]
  norm_num

/-! ## 6.  Where the finite layer stops -/

/-- The mode operators of two distinct axes do not commute.  This is the
non-associativity of `Sakuma.lean` read on the field side. -/
theorem modes_do_not_commute :
    mode (e 0) 1 (mode (e 1) 1 (e 2)) ≠ mode (e 1) 1 (mode (e 0) 1 (e 2)) := by
  simp only [mode_one]
  intro hcontra
  have h := congrFun hcontra 0
  revert h
  simp [mul, axisProduct, third, e, Fin.sum_univ_three]
  norm_num

/-- **The Griess layer is not a vertex algebra.**

Borcherds' commutator formula at `m = n = 1` would read, once every mode but
the first is discarded,

  `u ⋆ (v ⋆ w) - v ⋆ (u ⋆ w) = (u ⋆ v) ⋆ w`.

It fails on the triple of axes: the left side is `(-3/32) e₀ + (3/32) e₁` and
the right side is `(-3/32) e₂`.  So the modes the truncation throws away are
load-bearing, and the infinite-dimensional development is genuinely required. -/
theorem borcherds_commutator_fails :
    e 0 ⋆ (e 1 ⋆ e 2) - e 1 ⋆ (e 0 ⋆ e 2) ≠ (e 0 ⋆ e 1) ⋆ e 2 := by
  intro hcontra
  have h := congrFun hcontra 0
  revert h
  simp [mul, axisProduct, third, e, Fin.sum_univ_three]
  norm_num

/-- The two sides of the failed commutator formula, computed. -/
theorem borcherds_commutator_lhs :
    e 0 ⋆ (e 1 ⋆ e 2) - e 1 ⋆ (e 0 ⋆ e 2)
      = (-3 / 32 : ℚ) • e 0 + (3 / 32 : ℚ) • e 1 := by
  funext k
  fin_cases k <;>
    simp [mul, axisProduct, third, e, Fin.sum_univ_three] <;> norm_num

theorem borcherds_commutator_rhs :
    (e 0 ⋆ e 1) ⋆ e 2 = (-3 / 32 : ℚ) • e 2 := sakuma_left

end GLM.VOA
