/-
# The plus-type count of `Λ/2Λ`, and the extraspecial group above it

This file is **retrieved material**: `glm_lean/RequestProject/GLM3.lean` of the
supplied archive (`source_material/GLM-main.zip`) opens with a census of the
Leech quotient `Λ/2Λ` regarded as a quadratic space over `F₂`, and with the
extraspecial group `2^(1+24)` that sits above it. Neither is anywhere in the
present development, and both are the arithmetic the `LLVQTable` and
`HigherLattices` files assume without proving.

`Λ/2Λ` is a 24-dimensional `F₂`-space carrying `q(λ) = (λ·λ)/16 mod 2`; the
Witt decomposition writes it as an orthogonal sum of twelve hyperbolic planes,
which is the form used here. What is proved:

* `hypQ_add` — `q` really is a quadratic form, with polar form `B`;
* `char_sum` — the quadratic character sum factorises plane by plane, each
  plane contributing `3 − 1 = 2`, so the total is `2ⁿ`;
* `two_mul_sing` — hence the **plus-type count**: a rank-`2n` quadratic space of
  plus type over `F₂` has `(4ⁿ + 2ⁿ)/2` singular vectors;
* `sing_twelve`, `nsing_twelve` — at `n = 12`, `8 390 656` singular classes and
  `8 386 560` non-singular ones, the latter being the type-3 classes.

Above the space sits the group. The archive builds the cocycle extension by
hand and checks the group axioms one at a time; here it is a genuine `Group`
instance, so the statements below are statements about a group:

* `card_QG`, `card_QG_twelve` — `|Q| = 2·4ⁿ`, so `|Q| = 2²⁵` at `n = 12`;
* `sq_eq_one_iff` — `x_u² = z^{q(u)}`: a lift squares to the identity exactly on
  the singular classes;
* `commutator_eq` — `[x_u, x_v] = z^{B(u,v)}`, the extraspecial commutator;
* `centre_z` — `z` is central and an involution;
* `card_sq_eq_one`, `involution_count` — and therefore `Q` has exactly
  `4ⁿ + 2ⁿ` elements of order dividing two, that is `2²⁴ + 2¹²` when `n = 12`.

The last line is the point of the file: the involution count of the group is a
second, independent confirmation that the form is of plus type, arrived at by
group theory rather than by the character sum.
-/
import Mathlib

namespace GLM.Extraspecial

open Finset

/-! ## 1. The hyperbolic quadratic space -/

/-- One hyperbolic plane over `F₂`, as a pair of coordinates. -/
abbrev HP : Type := ZMod 2 × ZMod 2

/-- The quadratic form of an orthogonal sum of `n` hyperbolic planes,
`q(v) = ∑ᵢ aᵢbᵢ`. For `Λ/2Λ` this is `q(λ) = (λ·λ)/16 mod 2`, read in the basis
produced by the Witt decomposition. -/
def hypQ {n : ℕ} (v : Fin n → HP) : ZMod 2 := ∑ i, (v i).1 * (v i).2

/-- The polar form, `B(λ,μ) = (λ·μ)/8 mod 2`. -/
def hypB {n : ℕ} (u v : Fin n → HP) : ZMod 2 :=
  ∑ i, ((u i).2 * (v i).1 + (v i).2 * (u i).1)

/-- The explicit cocycle `f(u,v) = ⟨b_u, a_v⟩` used to build the extraspecial
group. It is biadditive, which is what makes the group law associative. -/
def cocycle {n : ℕ} (u v : Fin n → HP) : ZMod 2 := ∑ i, (u i).2 * (v i).1

variable {n : ℕ}

lemma cocycle_self (u : Fin n → HP) : cocycle u u = hypQ u :=
  Finset.sum_congr rfl fun _ _ => mul_comm _ _

lemma cocycle_polar (u v : Fin n → HP) :
    cocycle u v + cocycle v u = hypB u v := by
  simp only [cocycle, hypB]
  rw [← Finset.sum_add_distrib]

lemma cocycle_add_left (u v w : Fin n → HP) :
    cocycle (u + v) w = cocycle u w + cocycle v w := by
  simp only [cocycle, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun i _ => ?_
  simp [Prod.snd_add, add_mul]

lemma cocycle_add_right (u v w : Fin n → HP) :
    cocycle u (v + w) = cocycle u v + cocycle u w := by
  simp only [cocycle, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun i _ => ?_
  simp [Prod.fst_add, mul_add]

lemma cocycle_zero_left (v : Fin n → HP) : cocycle (0 : Fin n → HP) v = 0 := by
  simp [cocycle]

lemma cocycle_zero_right (v : Fin n → HP) : cocycle v (0 : Fin n → HP) = 0 := by
  simp [cocycle]

/-- `q` is a quadratic form with polar form `B`. -/
theorem hypQ_add (u v : Fin n → HP) :
    hypQ (u + v) = hypQ u + hypQ v + hypB u v := by
  rw [← cocycle_self, ← cocycle_self, ← cocycle_self, ← cocycle_polar,
    cocycle_add_left, cocycle_add_right, cocycle_add_right]
  ring

/-! ## 2. The plus-type count -/

/-- The singular classes, `q(v) = 0`. -/
def singSet (n : ℕ) : Finset (Fin n → HP) := univ.filter fun v => hypQ v = 0

/-- The number of singular classes. -/
def sing (n : ℕ) : ℕ := (singSet n).card

/-- The number of non-singular classes, `q(v) = 1`. -/
def nsing (n : ℕ) : ℕ := (univ.filter fun v : Fin n → HP => hypQ v ≠ 0).card

theorem sing_add_nsing (n : ℕ) : sing n + nsing n = 4 ^ n := by
  classical
  rw [sing, singSet, nsing, Finset.card_filter_add_card_filter_not]
  simp

/-- The quadratic character `(-1)^q`. -/
def psi (x : ZMod 2) : ℤ := if x = 0 then 1 else -1

lemma psi_add (a b : ZMod 2) : psi (a + b) = psi a * psi b := by revert a b; decide

lemma prod_psi {ι : Type} (s : Finset ι) (f : ι → ZMod 2) :
    ∏ i ∈ s, psi (f i) = psi (∑ i ∈ s, f i) := by
  classical
  induction s using Finset.induction with
  | empty => simp [psi]
  | insert a s ha ih => rw [Finset.prod_insert ha, Finset.sum_insert ha, ih, psi_add]

/-- **The character sum.** It factorises plane by plane, and each hyperbolic
plane contributes `3 − 1 = 2`. -/
theorem char_sum (n : ℕ) : ∑ v : Fin n → HP, psi (hypQ v) = 2 ^ n := by
  classical
  have h : ∀ v : Fin n → HP, psi (hypQ v) = ∏ i, psi ((v i).1 * (v i).2) := by
    intro v; rw [prod_psi]; rfl
  simp only [h]
  have key := Finset.prod_univ_sum (fun _ : Fin n => (univ : Finset HP))
    (fun _ (a : HP) => psi (a.1 * a.2))
  rw [Fintype.piFinset_univ] at key
  rw [← key]
  have h2 : ∑ a : HP, psi (a.1 * a.2) = 2 := by decide
  simp [h2]

lemma char_sum_split (n : ℕ) :
    ∑ v : Fin n → HP, psi (hypQ v) = (sing n : ℤ) - (nsing n : ℤ) := by
  classical
  rw [sing, singSet, nsing, Finset.card_filter, Finset.card_filter]
  push_cast
  rw [← Finset.sum_sub_distrib]
  refine Finset.sum_congr rfl fun v _ => ?_
  by_cases h : hypQ v = 0 <;> simp [psi, h]

/-- **The plus-type count.** A quadratic space of plus type and rank `2n` over
`F₂` has `(4ⁿ + 2ⁿ)/2` singular vectors. -/
theorem two_mul_sing (n : ℕ) : 2 * sing n = 4 ^ n + 2 ^ n := by
  have h1 : (sing n : ℤ) - (nsing n : ℤ) = 2 ^ n := by
    rw [← char_sum_split, char_sum]
  have h2 : (sing n : ℤ) + (nsing n : ℤ) = 4 ^ n :=
    mod_cast congrArg (fun k : ℕ => (k : ℤ)) (sing_add_nsing n)
  have h3 : (2 * sing n : ℤ) = 4 ^ n + 2 ^ n := by linarith
  exact_mod_cast h3

/-- **`Λ/2Λ` is of plus type: `8 390 656` singular classes.** -/
theorem sing_twelve : sing 12 = 2 ^ 23 + 2 ^ 11 := by
  have h := two_mul_sing 12
  omega

/-- The non-singular classes — the type-3 classes — number `2²³ − 2¹¹`. -/
theorem nsing_twelve : nsing 12 = 2 ^ 23 - 2 ^ 11 := by
  have h := sing_add_nsing 12
  have h2 := sing_twelve
  omega

theorem plus_type_numbers : sing 12 = 8390656 ∧ nsing 12 = 8386560 := by
  refine ⟨?_, ?_⟩
  · rw [sing_twelve]; norm_num
  · rw [nsing_twelve]; norm_num

/-! ## 3. The extraspecial group `2^(1+2n)` -/

lemma zmod2_self_add (a : ZMod 2) : a + a = 0 := by revert a; decide

lemma vec_self_add (u : Fin n → HP) : u + u = 0 := by
  funext i
  show u i + u i = 0
  exact Prod.ext_iff.mpr ⟨zmod2_self_add _, zmod2_self_add _⟩

/-- An element of `Q = 2^(1+2n)`: a class in the quadratic space together with
a central sign. -/
@[ext]
structure QG (n : ℕ) where
  /-- The class in `Λ/2Λ`, in Witt coordinates. -/
  cls : Fin n → HP
  /-- The central sign: which of the two lifts of `cls` this is. -/
  sgn : ZMod 2
deriving DecidableEq

namespace QG

/-- Forgetting the group law, `Q` is the set of (class, sign) pairs. -/
def equivProd (n : ℕ) : QG n ≃ (Fin n → HP) × ZMod 2 where
  toFun g := (g.cls, g.sgn)
  invFun p := ⟨p.1, p.2⟩
  left_inv _ := rfl
  right_inv _ := rfl

instance : Fintype (QG n) := Fintype.ofEquiv _ (equivProd n).symm

/-- The group law, twisted by the cocycle. -/
instance : Group (QG n) where
  mul g h := ⟨g.cls + h.cls, g.sgn + h.sgn + cocycle g.cls h.cls⟩
  one := ⟨0, 0⟩
  inv g := ⟨g.cls, g.sgn + cocycle g.cls g.cls⟩
  mul_assoc g h k := by
    refine QG.ext (add_assoc _ _ _) ?_
    show g.sgn + h.sgn + cocycle g.cls h.cls + k.sgn + cocycle (g.cls + h.cls) k.cls
      = g.sgn + (h.sgn + k.sgn + cocycle h.cls k.cls) + cocycle g.cls (h.cls + k.cls)
    rw [cocycle_add_left, cocycle_add_right]
    ring
  one_mul g := by
    refine QG.ext (zero_add _) ?_
    show (0 : ZMod 2) + g.sgn + cocycle 0 g.cls = g.sgn
    rw [cocycle_zero_left, zero_add, add_zero]
  mul_one g := by
    refine QG.ext (add_zero _) ?_
    show g.sgn + 0 + cocycle g.cls 0 = g.sgn
    rw [cocycle_zero_right, add_zero, add_zero]
  inv_mul_cancel g := by
    refine QG.ext (vec_self_add g.cls) ?_
    show g.sgn + cocycle g.cls g.cls + g.sgn + cocycle g.cls g.cls = 0
    have e1 := zmod2_self_add g.sgn
    have e2 := zmod2_self_add (cocycle g.cls g.cls)
    linear_combination e1 + e2

@[simp] lemma mul_cls (g h : QG n) : (g * h).cls = g.cls + h.cls := rfl

@[simp] lemma mul_sgn (g h : QG n) :
    (g * h).sgn = g.sgn + h.sgn + cocycle g.cls h.cls := rfl

@[simp] lemma one_cls : (1 : QG n).cls = 0 := rfl

@[simp] lemma one_sgn : (1 : QG n).sgn = 0 := rfl

/-- The central involution `z`. -/
def zc : QG n := ⟨0, 1⟩

/-- The lift `x_u` of a class `u`. -/
def x (u : Fin n → HP) : QG n := ⟨u, 0⟩

/-- `z` is central. -/
theorem centre_z (g : QG n) : zc * g = g * zc := by
  refine QG.ext ?_ ?_
  · simp [zc]
  · simp only [mul_sgn, zc, cocycle_zero_left, cocycle_zero_right]
    ring

/-- `z` is an involution. -/
theorem z_sq : (zc : QG n) * zc = 1 := by
  refine QG.ext ?_ ?_
  · simp [zc]
  · simp only [mul_sgn, zc, one_sgn, cocycle_zero_left]
    decide

theorem z_ne_one : (zc : QG n) ≠ 1 := by
  intro h
  have h1 : (1 : ZMod 2) = 0 := congrArg QG.sgn h
  exact absurd h1 (by decide)

/-- **`x_u² = z^{q(u)}`.** The square of a lift is central, with sign `q(u)`. -/
theorem x_sq (u : Fin n → HP) : x u * x u = ⟨0, hypQ u⟩ := by
  refine QG.ext (vec_self_add u) ?_
  show (0 : ZMod 2) + 0 + cocycle u u = hypQ u
  rw [cocycle_self, zero_add, zero_add]

/-- A lift squares to the identity exactly on the singular classes. -/
theorem sq_eq_one_iff (u : Fin n → HP) : x u * x u = 1 ↔ hypQ u = 0 := by
  rw [x_sq]
  constructor
  · intro h; simpa using congrArg QG.sgn h
  · intro h; exact QG.ext rfl (by simpa using h)

/-- **`[x_u, x_v] = z^{B(u,v)}`.** The two orders of the product agree in the
class coordinate, and their signs differ by the polar form. -/
theorem commutator_eq (u v : Fin n → HP) :
    (x u * x v).cls = (x v * x u).cls ∧
      (x u * x v).sgn + (x v * x u).sgn = hypB u v := by
  refine ⟨by simp [x, add_comm], ?_⟩
  show ((0 : ZMod 2) + 0 + cocycle u v) + ((0 : ZMod 2) + 0 + cocycle v u) = hypB u v
  simp only [zero_add]
  exact cocycle_polar u v

/-- Every class has exactly two lifts, so `|Q| = 2 · 4ⁿ`. -/
theorem card_QG (n : ℕ) : Fintype.card (QG n) = 2 * 4 ^ n := by
  have h1 : Fintype.card (QG n) = Fintype.card ((Fin n → HP) × ZMod 2) :=
    Fintype.card_congr (equivProd n)
  have h3 : Fintype.card (Fin n → HP) = 4 ^ n := by
    rw [Fintype.card_fun]
    norm_num
  rw [h1, Fintype.card_prod, h3, ZMod.card, mul_comm]

theorem card_QG_twelve : Fintype.card (QG 12) = 2 ^ 25 := by
  rw [card_QG]; norm_num

/-- A general element squares to the identity exactly when its class is
singular: the sign plays no part, so each singular class contributes both of
its lifts. -/
theorem sq_eq_one_iff_gen (g : QG n) : g * g = 1 ↔ hypQ g.cls = 0 := by
  constructor
  · intro h
    have hs := congrArg QG.sgn h
    simp only [mul_sgn, one_sgn, cocycle_self] at hs
    have e := zmod2_self_add g.sgn
    linear_combination hs - e
  · intro h
    refine QG.ext (vec_self_add g.cls) ?_
    show g.sgn + g.sgn + cocycle g.cls g.cls = 0
    rw [cocycle_self, h, add_zero]
    exact zmod2_self_add _

/-- **The involution count.** `Q` has exactly `4ⁿ + 2ⁿ` elements of order
dividing two: two lifts for each of the `(4ⁿ + 2ⁿ)/2` singular classes. -/
theorem card_sq_eq_one :
    Fintype.card {g : QG n // g * g = 1} = 4 ^ n + 2 ^ n := by
  have e : {g : QG n // g * g = 1} ≃ {v : Fin n → HP // hypQ v = 0} × ZMod 2 :=
    { toFun := fun g => (⟨g.1.cls, (sq_eq_one_iff_gen g.1).1 g.2⟩, g.1.sgn)
      invFun := fun p => ⟨⟨p.1.1, p.2⟩, (sq_eq_one_iff_gen _).2 p.1.2⟩
      left_inv := by rintro ⟨⟨c, s⟩, h⟩; rfl
      right_inv := by rintro ⟨⟨c, hc⟩, s⟩; rfl }
  rw [Fintype.card_congr e, Fintype.card_prod, ZMod.card]
  have hs : Fintype.card {v : Fin n → HP // hypQ v = 0} = sing n := by
    rw [sing, singSet, Fintype.card_subtype]
  rw [hs, mul_comm]
  exact two_mul_sing n

/-- At `n = 12`: the group of order `2²⁵` above `Λ/2Λ` has `2²⁴ + 2¹²`
elements of order dividing two — an independent confirmation, by group theory
rather than by the character sum, that the form is of plus type. -/
theorem involution_count :
    Fintype.card {g : QG 12 // g * g = 1} = 2 ^ 24 + 2 ^ 12 := by
  rw [card_sq_eq_one]; norm_num

end QG

end GLM.Extraspecial
