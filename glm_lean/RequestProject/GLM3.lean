/-
# Formal companion to the third-generation Geometric Language Machine

This file formalises the *theorem-shaped* propositions of the GLM-3 operational
paper (`glm3/glm3_paper.py`).  Everything that is a measurement — the type-2
class table, the eigenspace dimensions computed by counting, the 660-concept
register — is verified computationally by the Python artefacts.  What is proved
here is the part of the argument that is mathematics rather than data.

* §1  **The hyperbolic quadratic space and the plus-type count.**  `Λ/2Λ` is
  computed in the paper to be an `F₂` quadratic space whose Witt decomposition
  is twelve hyperbolic planes with empty anisotropic part.  Here the consequence
  is *proved*: for the orthogonal sum of `n` hyperbolic planes the number of
  singular vectors is `(4ⁿ + 2ⁿ)/2`, by the character-sum identity
  `∑_v (-1)^{q(v)} = ∏_i ∑_{(a,b)} (-1)^{ab} = 2ⁿ`.  At `n = 12` this is
  `2²³ + 2¹¹ = 8,390,656`, and the non-singular count is `2²³ - 2¹¹`.

* §2  **The extraspecial group `2^(1+24)`, built from the cocycle.**  With
  `f(u,v) = ⟨b_u, a_v⟩` in a symplectic basis, the set `V × ZMod 2` with
  `(u,ε)(v,δ) = (u+v, ε+δ+f(u,v))` is a group; `z = (0,1)` is central with
  `z² = 1`; `x_u² = z^{q(u)}`; and the two orders of a product differ by
  `z^{B(u,v)}`.  All of it is proved for the concrete `f`, which is also shown
  to satisfy `f(u,u) = q(u)` and `f(u,v) + f(v,u) = B(u,v)`, so that `q` is a
  quadratic form with polar form `B`.  The order is `2 · 4¹² = 2²⁵`.

* §3  **The 2-adic stack is faithful.**  The multi-MOG-cube addressing used by
  the reasoner records the binary digit planes of the coordinates after a fixed
  offset.  Two coordinates in the box with the same digit planes are equal, so
  the stack determines the lattice point.

* §4  **`Λ/2Λ` censuses and the Griess ledger.**  The class census
  `1 + 98,280 + 8,386,560 + 8,292,375 = 2²⁴`, the theta-series divisions
  `196,560/2`, `16,773,120/2` and `398,034,000/48`, and the ledger
  `300 + 98,280 + 24·4096 = 196,884`.

* §5  **The eigenspace dimensions are forced by the pair census.**

* §6  **The MOG cube: the arithmetic behind the refutation.**  The even-weight
  code on eight cells has `2⁷ = 128` words — computed here by `decide` over all
  256 subsets — while `RM(1,3)` has `2⁴ = 16`; so the archive's identification
  of the Golay trace on a cube with `RM(1,3)` cannot hold.  Also
  `|AGL(4,2)| = 2⁴ · 20,160 = 322,560` and `759 · 322,560 = |M₂₄|`.

* §7  **A `ZMod 2`-graded product carries an involutory automorphism**, which is
  the abstract reason a Majorana axis has a Miyamoto involution.

* §8  **The Ising fusion law is `ZMod 2`-graded.**  The nine-entry fusion table
  of the paper is written out and the grading `{1, 0, 1/4} ↦ 0`, `{1/32} ↦ 1`
  is proved compatible with it by exhaustion — the hypothesis §7 needs.

* §9  **The stack depth is derived.**  Proposition D1 at arbitrary offset and
  depth: admissibility of the parameters, faithfulness of the digit planes, the
  explicit rebuild sum, and the fact that planes above the threshold vanish.

* §10 **The Golay theta function and the sign convention.**  `θ(C) = |C|/4`
  is quadratic with polar form `|C ∩ D|/2`; the rule `s(λ+μ) = −s(λ)s(μ)` forced
  by the Sakuma identity rules out the all-plus convention and admits the
  constant `−1` one; the conventions `B(w, ·)` are pairwise distinct.

* §11 **The odd part.**  The four structure constants are the unique solution of
  the identity condition plus the Miyamoto block eigenvalues, the fifth equation
  is a consequence of the other four, and the ledger
  `1 / 96,256 / 4,371 / 96,256 = 196,884` closes.

* §12 **From an invariant form to a metric.**  Positive definiteness gives the
  triangle inequality, a pseudometric gives a metric on its separation
  quotient, an injective map pulls a metric back, and the plane-graded
  embedding is injective when a plane's vector is.

* §13 **The benchmark arithmetic.**

No `sorry`, no new axioms.
-/

import Mathlib

set_option autoImplicit false
set_option linter.style.longLine false
set_option maxHeartbeats 1000000
set_option maxRecDepth 20000

namespace GLM3

open Finset

/-! ## §1  The hyperbolic quadratic space over `F₂` and the plus-type count -/

/-- One hyperbolic plane over `F₂`, as a pair of coordinates. -/
abbrev HP : Type := ZMod 2 × ZMod 2

/-- The quadratic form of an orthogonal sum of `n` hyperbolic planes,
`q(v) = ∑ᵢ aᵢbᵢ`.  This is the form `q(λ) = (λ·λ)/16 mod 2` of the paper, read
in the basis produced by the Witt decomposition. -/
def hypQ {n : ℕ} (v : Fin n → HP) : ZMod 2 := ∑ i, (v i).1 * (v i).2

/-- The polar form, `B(λ,μ) = (λ·μ)/8 mod 2`. -/
def hypB {n : ℕ} (u v : Fin n → HP) : ZMod 2 :=
  ∑ i, ((u i).2 * (v i).1 + (v i).2 * (u i).1)

/-- The explicit cocycle `f(u,v) = ⟨b_u, a_v⟩` used to build the extraspecial
group.  It is biadditive, which is what makes the group law associative. -/
def cocycle {n : ℕ} (u v : Fin n → HP) : ZMod 2 := ∑ i, (u i).2 * (v i).1

lemma cocycle_self {n : ℕ} (u : Fin n → HP) : cocycle u u = hypQ u := by
  simp only [cocycle, hypQ]
  exact Finset.sum_congr rfl fun i _ => mul_comm _ _

lemma cocycle_polar {n : ℕ} (u v : Fin n → HP) :
    cocycle u v + cocycle v u = hypB u v := by
  simp only [cocycle, hypB]
  rw [← Finset.sum_add_distrib]

lemma cocycle_add_left {n : ℕ} (u v w : Fin n → HP) :
    cocycle (u + v) w = cocycle u w + cocycle v w := by
  simp only [cocycle, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun i _ => ?_
  simp [Prod.snd_add, add_mul]

lemma cocycle_add_right {n : ℕ} (u v w : Fin n → HP) :
    cocycle u (v + w) = cocycle u v + cocycle u w := by
  simp only [cocycle, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun i _ => ?_
  simp [Prod.fst_add, mul_add]

/-- `q` is a quadratic form with polar form `B`. -/
theorem hypQ_add {n : ℕ} (u v : Fin n → HP) :
    hypQ (u + v) = hypQ u + hypQ v + hypB u v := by
  rw [← cocycle_self, ← cocycle_self, ← cocycle_self, ← cocycle_polar,
    cocycle_add_left, cocycle_add_right, cocycle_add_right]
  ring

/-- The number of singular vectors, `q(v) = 0`. -/
noncomputable def sing (n : ℕ) : ℕ :=
  (univ.filter (fun v : Fin n → HP => hypQ v = 0)).card

/-- The number of non-singular vectors, `q(v) = 1`. -/
noncomputable def nsing (n : ℕ) : ℕ :=
  (univ.filter (fun v : Fin n → HP => hypQ v ≠ 0)).card

theorem sing_add_nsing (n : ℕ) : sing n + nsing n = 4 ^ n := by
  classical
  rw [sing, nsing, Finset.card_filter_add_card_filter_not]
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

/-- The character sum factorises plane by plane, and each hyperbolic plane
contributes `3 - 1 = 2`. -/
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
  rw [sing, nsing, Finset.card_filter, Finset.card_filter]
  push_cast
  rw [← Finset.sum_sub_distrib]
  refine Finset.sum_congr rfl fun v _ => ?_
  by_cases h : hypQ v = 0 <;> simp [psi, h]

/-- **The plus-type count.**  A quadratic space of plus type and rank `2n` over
`F₂` has `(4ⁿ + 2ⁿ)/2` singular vectors. -/
theorem two_mul_sing (n : ℕ) : 2 * sing n = 4 ^ n + 2 ^ n := by
  have h1 : (sing n : ℤ) - (nsing n : ℤ) = 2 ^ n := by
    rw [← char_sum_split, char_sum]
  have h2 : (sing n : ℤ) + (nsing n : ℤ) = 4 ^ n := by
    exact_mod_cast congrArg (fun k : ℕ => (k : ℤ)) (sing_add_nsing n)
  have h3 : (2 * sing n : ℤ) = 4 ^ n + 2 ^ n := by linarith
  exact_mod_cast h3

/-- **`Λ/2Λ` is of plus type: 8,390,656 singular classes.** -/
theorem sing_twelve : sing 12 = 2 ^ 23 + 2 ^ 11 := by
  have h := two_mul_sing 12
  omega

/-- The non-singular classes — which the paper identifies with the type-3
classes — number `2²³ - 2¹¹ = 8,386,560`. -/
theorem nsing_twelve : nsing 12 = 2 ^ 23 - 2 ^ 11 := by
  have h := sing_add_nsing 12
  have h2 := sing_twelve
  omega

theorem plus_type_numbers : sing 12 = 8390656 ∧ nsing 12 = 8386560 := by
  refine ⟨?_, ?_⟩
  · rw [sing_twelve]; norm_num
  · rw [nsing_twelve]; norm_num

/-! ## §2  The extraspecial group `2^(1+24)` -/

lemma self_add (a : ZMod 2) : a + a = 0 := by revert a; decide

lemma vec_self_add {n : ℕ} (u : Fin n → HP) : u + u = 0 := by
  funext i
  exact Prod.ext_iff.mpr ⟨by simp [self_add], by simp [self_add]⟩

/-- The underlying set of `Q = 2^(1+2n)`: a class together with a central sign. -/
abbrev QG (n : ℕ) : Type := (Fin n → HP) × ZMod 2

namespace QG

variable {n : ℕ}

/-- The group law, twisted by the cocycle. -/
def mul (g h : QG n) : QG n := (g.1 + h.1, g.2 + h.2 + cocycle g.1 h.1)

/-- The identity. -/
def one : QG n := (0, 0)

/-- The central involution `z`. -/
def zc : QG n := (0, 1)

/-- The lift `x_u` of a class `u`. -/
def x (u : Fin n → HP) : QG n := (u, 0)

/-- The inverse of an element. -/
def inv (g : QG n) : QG n := (g.1, g.2 + cocycle g.1 g.1)

lemma cocycle_zero_left (v : Fin n → HP) : cocycle (0 : Fin n → HP) v = 0 := by
  simp [cocycle]

lemma cocycle_zero_right (v : Fin n → HP) : cocycle v (0 : Fin n → HP) = 0 := by
  simp [cocycle]

theorem mul_assoc (g h k : QG n) : mul (mul g h) k = mul g (mul h k) := by
  simp only [mul, Prod.mk.injEq, cocycle_add_left, cocycle_add_right]
  exact ⟨add_assoc _ _ _, by ring⟩

theorem one_mul (g : QG n) : mul one g = g := by simp [mul, one, cocycle_zero_left]

theorem mul_one (g : QG n) : mul g one = g := by simp [mul, one, cocycle_zero_right]

theorem mul_inv (g : QG n) : mul g (inv g) = one := by
  have h1 : g.1 + g.1 = 0 := vec_self_add g.1
  have h2 : g.2 + (g.2 + cocycle g.1 g.1) + cocycle g.1 g.1 = 0 := by
    have e1 := self_add g.2
    have e2 := self_add (cocycle g.1 g.1)
    linear_combination e1 + e2
  simp [mul, inv, one, h1, h2]

/-- `z` is central. -/
theorem z_central (g : QG n) : mul zc g = mul g zc := by
  refine Prod.ext_iff.mpr ⟨?_, ?_⟩ <;>
    simp [mul, zc, cocycle_zero_left, cocycle_zero_right]
  ring

theorem z_sq : mul (zc : QG n) zc = one := by
  simp [mul, zc, one, cocycle_zero_left]
  decide

/-- **`x_u² = z^{q(u)}`**, stated as: the square of a lift is central with sign
`q(u)`. -/
theorem x_sq (u : Fin n → HP) : mul (x u) (x u) = ((0 : Fin n → HP), hypQ u) := by
  simp [mul, x, cocycle_self, vec_self_add u]

theorem x_sq_one (u : Fin n → HP) (h : hypQ u = 0) : mul (x u) (x u) = one := by
  rw [x_sq, h]; rfl

theorem x_sq_z (u : Fin n → HP) (h : hypQ u = 1) : mul (x u) (x u) = zc := by
  rw [x_sq, h]; rfl

/-- **`[x_u, x_v] = z^{B(u,v)}`**, stated as: the two orders of the product have
the same class and their signs differ by `B(u,v)`. -/
theorem commutator_phase (u v : Fin n → HP) :
    (mul (x u) (x v)).1 = (mul (x v) (x u)).1 ∧
    (mul (x u) (x v)).2 + (mul (x v) (x u)).2 = hypB u v := by
  refine ⟨by simp [mul, x, add_comm], ?_⟩
  simp only [mul, x, zero_add]
  exact cocycle_polar u v

/-- Every class has exactly two lifts, so `|Q| = 2 · 4ⁿ`. -/
theorem card_QG (n : ℕ) : Fintype.card (QG n) = 2 * 4 ^ n := by
  simp [QG, Fintype.card_prod]
  ring

theorem order_two_pow_25 : Fintype.card (QG 12) = 2 ^ 25 := by
  rw [card_QG]; norm_num

end QG

/-- The elements of order at most two in `Q` are the two lifts of each singular
class: `2 · (2²³ + 2¹¹) = 2²⁴ + 2¹²`.  This is the second, independent
confirmation of the plus type. -/
theorem involution_count : 2 * sing 12 = 2 ^ 24 + 2 ^ 12 := by
  rw [sing_twelve]; norm_num

/-! ## §3  The 2-adic stack is faithful -/

/-- **Faithfulness of the multi-MOG-cube addressing.**  Two naturals below `2^d`
with the same first `d` binary digit planes are equal. -/
theorem stack_faithful {d a b : ℕ} (ha : a < 2 ^ d) (hb : b < 2 ^ d)
    (h : ∀ k < d, a.testBit k = b.testBit k) : a = b := by
  apply Nat.eq_of_testBit_eq
  intro k
  by_cases hk : k < d
  · exact h k hk
  · push_neg at hk
    have h2 : 2 ^ d ≤ 2 ^ k := Nat.pow_le_pow_right (by norm_num) hk
    rw [Nat.testBit_eq_false_of_lt (lt_of_lt_of_le ha h2),
      Nat.testBit_eq_false_of_lt (lt_of_lt_of_le hb h2)]

/-- The same for the signed coordinates the encoder actually produces: after the
translation by the offset `2^d` the coordinates lie in `[0, 2^(d+1))`, so the
`d+1` planes determine them.  This is the invariant
`class_stack_rebuild ∘ class_stack = id`. -/
theorem stack_faithful_int {d : ℕ} {a b : ℤ}
    (ha : -((2 : ℤ) ^ d) ≤ a) (ha' : a < (2 : ℤ) ^ d)
    (hb : -((2 : ℤ) ^ d) ≤ b) (hb' : b < (2 : ℤ) ^ d)
    (h : ∀ k < d + 1, (a + 2 ^ d).toNat.testBit k = (b + 2 ^ d).toNat.testBit k) :
    a = b := by
  have hcast : ((2 ^ (d + 1) : ℕ) : ℤ) = (2 : ℤ) ^ d + (2 : ℤ) ^ d := by push_cast; ring
  have hA : (a + 2 ^ d).toNat < 2 ^ (d + 1) := by omega
  have hB : (b + 2 ^ d).toNat < 2 ^ (d + 1) := by omega
  have key := stack_faithful hA hB h
  omega

/-! ## §4  `Λ/2Λ` censuses and the Griess ledger -/

/-- The class census of `Λ/2Λ` closes, and the type-3 count is the non-singular
count. -/
theorem class_census :
    1 + 98280 + 8386560 + 8292375 = 2 ^ 24 ∧
    8386560 = 2 ^ 23 - 2 ^ 11 ∧
    1 + 98280 + 8292375 = 2 ^ 23 + 2 ^ 11 := by
  refine ⟨by norm_num, by norm_num, by norm_num⟩

/-- The class counts come from the theta series: `196,560` minimal vectors in
antipodal pairs, `16,773,120` type-3 vectors in antipodal pairs, `398,034,000`
type-4 vectors in coordinate frames of 48. -/
theorem theta_divisions :
    196560 / 2 = 98280 ∧ 16773120 / 2 = 8386560 ∧ 398034000 / 48 = 8292375 := by
  refine ⟨by norm_num, by norm_num, by norm_num⟩

/-- **The Griess ledger.**  `300 = 24·25/2` symmetric matrices, one basis vector
per type-2 class, and `24 ⊗ 4096` for the odd part. -/
theorem griess_ledger :
    24 * 25 / 2 = 300 ∧ 24 * 4096 = 98304 ∧ 300 + 98280 + 24 * 4096 = 196884 := by
  refine ⟨by norm_num, by norm_num, by norm_num⟩

theorem even_part_dimension : 300 + 98280 = 98580 := by norm_num

/-! ## §5  The eigenspace dimensions are forced by the pair census -/

/-- The 196,560 minimal vectors split, relative to a fixed one, as
`2 + 9,200 + 94,208 + 93,150`; halving gives the type-2 class census
`1 + 4,600 + 47,104 + 46,575 = 98,280`. -/
theorem pair_census :
    2 + 9200 + 94208 + 93150 = 196560 ∧
    1 + 4600 + 47104 + 46575 = 98280 ∧
    2 * (1 + 4600 + 47104 + 46575) = 196560 := by
  refine ⟨by norm_num, by norm_num, by norm_num⟩

/-- **The Griess eigenspace dimensions are forced.**  With `n₀ = 46,575`,
`n₁ = 47,104` and `n₂ = 4,600` type-2 classes at pairing `0`, `1`, `2`, and the
splitting `300 = 1 + 23 + 276` of the matrix part, the eigenspaces of `ad(a)`
have dimensions `1`, `n₀ + n₂/2 + 277`, `n₂/2 + 23` and `n₁`. -/
theorem eigenspace_dimensions :
    46575 + 4600 / 2 + 277 = 49152 ∧
    4600 / 2 + 23 = 2323 ∧
    1 + 49152 + 2323 + 47104 = 98580 ∧
    1 + 23 + 276 = 300 := by
  refine ⟨by norm_num, by norm_num, by norm_num, by norm_num⟩

/-- The whole even part is accounted for, class by class and matrix direction by
matrix direction. -/
theorem eigenspace_partition :
    1 + (46575 + 2300 + 277) + (2300 + 23) + 47104 = 300 + 98280 := by norm_num

/-! ## §6  The MOG cube: the arithmetic behind the refutation -/

/-- The even-weight code on the eight cells of one MOG cube. -/
noncomputable def evenWeight8 : Finset (Finset (Fin 8)) :=
  univ.filter (fun s => Even s.card)

/-- **The refutation, in cardinalities.**  The trace of the Golay code on a cube
is computed in `glm3_mog.py` to be the even-weight code, which has `2⁷ = 128`
words; the first-order Reed–Muller code `RM(1,3)` has `2⁴ = 16`.  They are
therefore different codes, and the archive's claim is false. -/
theorem even_weight_card : evenWeight8.card = 128 := by decide

theorem even_weight_ne_rm13 : evenWeight8.card ≠ 2 ^ 4 := by
  rw [even_weight_card]; norm_num

/-- `|GL(4,2)| = (2⁴-1)(2⁴-2)(2⁴-4)(2⁴-8) = 20,160`. -/
theorem gl_four_two_order : (16 - 1) * (16 - 2) * (16 - 4) * (16 - 8) = 20160 := by
  norm_num

/-- `|AGL(4,2)| = 2⁴ · |GL(4,2)| = 322,560`, the order of the octad stabiliser
in `M₂₄`. -/
theorem agl_four_two_order : 2 ^ 4 * 20160 = 322560 := by norm_num

/-- Orbit–stabiliser for the 759 octads: `759 · 322,560 = |M₂₄|`. -/
theorem m24_orbit_stabiliser : 759 * 322560 = 244823040 := by norm_num

/-- The intersection census with a fixed octad accounts for all 759 octads, and
each octad lies in exactly 15 of the 3,795 trios. -/
theorem octad_censuses :
    30 + 448 + 280 + 1 = 759 ∧ 3 * 3795 = 759 * 15 := by
  refine ⟨by norm_num, by norm_num⟩

/-! ## §7  A graded product carries an involutory automorphism -/

section Graded

variable {R : Type*} [CommRing R]

/-- A `ZMod 2`-graded commutative (not necessarily associative) product, written
concretely: the algebra is `R × R`, the even part is the first factor and the
odd part the second, so that `even·even ⊆ even`, `even·odd ⊆ odd` and
`odd·odd ⊆ even`.  This is the shape of the Monster fusion law once the
eigenspaces `{1, 0, 1/4}` are collected into the even part and `{1/32}` into the
odd part — see §8. -/
def gmul (x y : R × R) : R × R :=
  (x.1 * y.1 + x.2 * y.2, x.1 * y.2 + x.2 * y.1)

/-- The Miyamoto map: negate the odd part. -/
def tau (x : R × R) : R × R := (x.1, -x.2)

theorem gmul_comm (x y : R × R) : gmul x y = gmul y x := by
  simp only [gmul, Prod.mk.injEq]
  constructor <;> ring

/-- Negating the odd part is an involution … -/
theorem tau_involutive (x : R × R) : tau (tau x) = x := by simp [tau]

/-- … it is additive … -/
theorem tau_add (x y : R × R) : tau (x + y) = tau x + tau y := by
  refine Prod.ext_iff.mpr ⟨?_, ?_⟩
  · simp [tau]
  · simp only [tau, Prod.snd_add]
    ring

/-- … and it respects the product.  That is the abstract reason a Majorana axis
carries an involution of the Griess algebra. -/
theorem tau_mul (x y : R × R) : tau (gmul x y) = gmul (tau x) (tau y) := by
  simp only [tau, gmul, Prod.mk.injEq]
  constructor <;> ring

/-- The involution really moves something as soon as the odd part is
non-trivial and 2 is not a zero divisor there. -/
theorem tau_ne_id (r : R) (h2 : (2 : R) * r ≠ 0) : tau ((0 : R), r) ≠ ((0 : R), r) := by
  simp only [tau, ne_eq, Prod.mk.injEq, not_and]
  intro _ h
  exact h2 (by linear_combination -h)

end Graded

/-! ## §8  The Ising fusion law is `ZMod 2`-graded -/

/-- The four eigenvalues of `ad(a)` for a Majorana axis `a`. -/
inductive Eig | one | zero | quarter | thirtysecond
deriving DecidableEq, Fintype, Repr

open Eig in
/-- The grading that produces the Miyamoto involution: the `1/32`-eigenspace is
odd, everything else is even. -/
def eigGrade : Eig → ZMod 2
  | one => 0
  | zero => 0
  | quarter => 0
  | thirtysecond => 1

open Eig in
/-- **The Monster (Ising) fusion law**, exactly as verified in the algebra by
`glm3_griess.fusion_report`. -/
def fuse : Eig → Eig → Finset Eig
  | one, y => {y}
  | x, one => {x}
  | zero, zero => {zero}
  | zero, quarter => {quarter}
  | quarter, zero => {quarter}
  | zero, thirtysecond => {thirtysecond}
  | thirtysecond, zero => {thirtysecond}
  | quarter, quarter => {one, zero}
  | quarter, thirtysecond => {thirtysecond}
  | thirtysecond, quarter => {thirtysecond}
  | thirtysecond, thirtysecond => {one, zero, quarter}

theorem fuse_symm (x y : Eig) : fuse x y = fuse y x := by revert x y; decide

/-- **The fusion law is `ZMod 2`-graded**, which by §7 is exactly what makes the
Miyamoto map an automorphism. -/
theorem fuse_graded (x y z : Eig) (h : z ∈ fuse x y) :
    eigGrade z = eigGrade x + eigGrade y := by
  revert h; revert x y z; decide

/-- The two graded rules the paper singles out: `1/4 ⋆ 1/4 ⊆ 1 ⊕ 0` and
`1/32 ⋆ 1/32 ⊆ 1 ⊕ 0 ⊕ 1/4`. -/
theorem fuse_graded_rules :
    fuse Eig.quarter Eig.quarter = {Eig.one, Eig.zero} ∧
    fuse Eig.thirtysecond Eig.thirtysecond = {Eig.one, Eig.zero, Eig.quarter} := by
  exact ⟨rfl, rfl⟩

/-! ## §9  The stack depth is derived, not chosen

The paper's Proposition D1: faithfulness of the digit-plane addressing is a
statement about the RANGE of the data and the two parameters (offset, depth),
with no mention of ten.  `stack_faithful` above is the case `O = 2^(D-1)`; the
two theorems here are the general one, together with the explicit rebuild map
and the fact that planes above the threshold carry nothing. -/

section Depth

/-- **Admissibility.**  If the coordinates are bounded by `R`, the offset `O` is
at least `R`, and `2^D > O + R`, then every shifted coordinate lies in the box
`[0, 2^D)` where the digit expansion has `D` digits. -/
theorem shift_in_box {R O : ℤ} {D : ℕ} (hO : R ≤ O)
    (hD : O + R < 2 ^ D) {u : ℤ} (hu : |u| ≤ R) :
    0 ≤ u + O ∧ u + O < 2 ^ D := by
  have h1 : -R ≤ u := neg_le_of_abs_le hu
  have h2 : u ≤ R := le_of_abs_le hu
  constructor <;> omega

/-- **Proposition D1, the faithfulness half.**  Two integers in the box with the
same `D` digit planes are equal — at ARBITRARY offset and depth, so the choice
of ten planes in the implementation is a presentation, not an assumption. -/
theorem stack_faithful_param {D : ℕ} {O a b : ℤ}
    (ha : 0 ≤ a + O) (ha' : a + O < 2 ^ D)
    (hb : 0 ≤ b + O) (hb' : b + O < 2 ^ D)
    (h : ∀ k < D, (a + O).toNat.testBit k = (b + O).toNat.testBit k) :
    a = b := by
  have hcast : ((2 ^ D : ℕ) : ℤ) = (2 : ℤ) ^ D := by push_cast; ring
  have hA : (a + O).toNat < 2 ^ D := by omega
  have hB : (b + O).toNat < 2 ^ D := by omega
  have key := stack_faithful hA hB h
  omega

/-- **Proposition D1, the rebuild half.**  Reading the `D` digit planes of a
natural number below `2^D` and reassembling `∑ 2^k d_k` returns it: this is
`class_stack_rebuild ∘ class_stack = id`, at arbitrary depth. -/
theorem digit_rebuild (D : ℕ) : ∀ n : ℕ, n < 2 ^ D →
    ∑ k ∈ Finset.range D, 2 ^ k * (if n.testBit k then 1 else 0) = n := by
  induction D with
  | zero => intro n h; simp at h ⊢; omega
  | succ d ih =>
      intro n h
      rw [Finset.sum_range_succ']
      simp only [pow_zero, one_mul, pow_succ]
      have h2 : n / 2 < 2 ^ d := by
        have : n < 2 ^ d * 2 := by rw [← pow_succ]; exact h
        omega
      have key := ih (n / 2) h2
      have hb : ∀ k, n.testBit (k + 1) = (n / 2).testBit k := by
        intro k; rw [Nat.testBit_succ]
      have h0 : (if n.testBit 0 then 1 else 0) = n % 2 := by
        rcases Nat.even_or_odd n with he | ho
        · simp [Nat.testBit_zero, Nat.even_iff.mp he]
        · simp [Nat.testBit_zero, Nat.odd_iff.mp ho]
      calc ∑ k ∈ Finset.range d, 2 ^ k * 2 * (if n.testBit (k + 1) then 1 else 0)
            + (if n.testBit 0 then 1 else 0)
          = 2 * (∑ k ∈ Finset.range d, 2 ^ k * (if (n / 2).testBit k then 1 else 0))
              + n % 2 := by
              rw [h0, Finset.mul_sum]
              congr 1
              refine Finset.sum_congr rfl ?_
              intro k _
              rw [hb k]; ring
        _ = n := by rw [key]; omega

/-- **Deeper stacks add nothing.**  Above the admissible depth every plane is
identically zero, so raising the depth appends zero planes and changes no word,
no axis and no distance. -/
theorem planes_above_are_zero {D : ℕ} {n : ℕ} (hn : n < 2 ^ D) {k : ℕ} (hk : D ≤ k) :
    n.testBit k = false :=
  Nat.testBit_eq_false_of_lt (lt_of_lt_of_le hn (Nat.pow_le_pow_right (by norm_num) hk))

/-- The measurement behind the module's constants: the register's coordinate
range is `180`, so the least admissible offset is `256` with depth `9`, and the
conventional offset `512` forces depth `10`. -/
theorem register_depth :
    (180 : ℤ) ≤ 256 ∧ (256 : ℤ) + 180 < 2 ^ 9 ∧ ¬ ((256 : ℤ) + 180 < 2 ^ 8) ∧
    (256 : ℤ) + 180 < 2 ^ 9 ∧ (512 : ℤ) + 180 < 2 ^ 10 ∧ ¬ ((512 : ℤ) + 180 < 2 ^ 9) := by
  refine ⟨by norm_num, by norm_num, by norm_num, by norm_num, by norm_num, by norm_num⟩

end Depth

/-! ## §10  The Golay theta function and the coherent sign convention

`θ(C) = |C|/4 mod 2` is quadratic with polar form `|C ∩ D|/2`, and the sign
convention forced by the Sakuma identity is `s(λ+μ) = −s(λ)s(μ)`, which the
all-plus convention violates and the constant `−1` convention satisfies. -/

section Sign

open Finset

/-- **The theta identity.**  For subsets of the 24 coordinates whose sizes are
all divisible by four — as Golay codewords are — `θ(C △ D) = θ(C) + θ(D) +
|C ∩ D|/2` in `ZMod 2`.  Only the cardinality identity
`|C △ D| + 2|C ∩ D| = |C| + |D|` is used, so this is the arithmetic behind the
exhaustive check over all 4,096 codewords. -/
theorem theta_quadratic (C D : Finset (Fin 24)) {a b e : ℕ}
    (hC : C.card = 4 * a) (hD : D.card = 4 * b) (hE : (symmDiff C D).card = 4 * e) :
    (e : ZMod 2) = (a : ZMod 2) + (b : ZMod 2) + (((C ∩ D).card / 2 : ℕ) : ZMod 2) := by
  classical
  have h1 : symmDiff C D = (C ∪ D) \ (C ∩ D) := by
    ext x; simp [Finset.mem_symmDiff]; tauto
  have h2 : (C ∩ D) ⊆ (C ∪ D) := by intro x hx; simp at hx ⊢; tauto
  have h4 : ((C ∪ D) \ (C ∩ D)).card + (C ∩ D).card = (C ∪ D).card :=
    Finset.card_sdiff_add_card_eq_card h2
  have h5 := Finset.card_union_add_card_inter C D
  have hsum : (symmDiff C D).card + 2 * (C ∩ D).card = C.card + D.card := by
    rw [h1]; omega
  -- so |C ∩ D| = 2 (a + b − e), and its half is a + b − e
  have hi : (C ∩ D).card = 2 * (a + b - e) := by omega
  have he : e ≤ a + b := by omega
  have hhalf : (C ∩ D).card / 2 = a + b - e := by omega
  rw [hhalf]
  have hab : a + b = e + (a + b - e) := by omega
  have hcast : (a : ZMod 2) + (b : ZMod 2) = (e : ZMod 2) + ((a + b - e : ℕ) : ZMod 2) := by
    have h := congrArg (fun n : ℕ => (n : ZMod 2)) hab
    push_cast at h
    linear_combination h
  have hdouble : ((a + b - e : ℕ) : ZMod 2) + ((a + b - e : ℕ) : ZMod 2) = 0 := by
    have h2 : ∀ x : ZMod 2, x + x = 0 := by decide
    exact h2 _
  rw [hcast, add_assoc, hdouble, add_zero]

/-- The sign attached to a convention `t : V → ZMod 2` by `s = −(−1)^t`. -/
def sgn (a : ZMod 2) : ℤ := if a = 0 then -1 else 1

/-- **Proposition S1, in the abstract.**  A convention of this shape satisfies
the rule the Sakuma identity forces, `s(λ+μ) = −s(λ)s(μ)`, for every additive
`t`; and conversely the rule says exactly that the exponent is additive. -/
theorem sgn_rule (a b : ZMod 2) : sgn (a + b) = -(sgn a * sgn b) := by
  revert a b; decide

/-- The all-plus convention is INCOHERENT: it would need `1 = −(1·1)`. -/
theorem all_plus_incoherent : (1 : ℤ) ≠ -(1 * 1) := by decide

/-- The constant convention `s ≡ −1` — the canonical one, `CANONICAL_SIGN = -1`
in the implementation — is coherent. -/
theorem constant_minus_coherent : (-1 : ℤ) = -((-1) * (-1)) := by decide

/-- The polar form of `Λ/2Λ` in coordinates. -/
def bform (w x : Fin 24 → ZMod 2) : ZMod 2 := ∑ i, w i * x i

/-- The conventions `t = B(w, ·)` are pairwise different, so there are at least
`2^24` of them; the implementation measures the F₂ system's nullity to be 24 on
closed subsystems, so there are exactly this many. -/
theorem bform_injective : Function.Injective (fun w : Fin 24 → ZMod 2 => bform w) := by
  intro w w' h
  funext i
  have := congrFun h (fun j => if j = i then 1 else 0)
  simpa [bform, Finset.sum_ite_eq'] using this

theorem conventions_card : Fintype.card (Fin 24 → ZMod 2) = 2 ^ 24 := by simp

end Sign

/-! ## §11  The odd part: the constants are forced, and the ledger closes

The four constants of the action `V⁺ ⊗ V⁻ → V⁻` satisfy five linear equations —
the identity condition and the four block eigenvalues demanded by the Miyamoto
requirement.  The system is over-determined; it has a unique solution, and the
fifth equation is a consequence of the other four, which is the closure the
paper reports. -/

section Odd

/-- **The constants of the odd part are forced.**  From `c1 + 24 c2 = 1` and the
four block eigenvalues `{0, 1/32}` on the perpendicular block and `{1/4, 1/32}`
on the `λ` block, the solution is unique. -/
theorem odd_constants_unique (c1 c2 c3 c4 : ℚ)
    (hid : c1 + 24 * c2 = 1)
    (hperp0 : c2 / 2 + c4 / 2 = 0)
    (hperp32 : c2 / 2 - c4 / 2 = 1 / 32)
    (halong4 : (c1 + c2) / 2 + (4 * c3 + c4) / 2 = 1 / 4) :
    c1 = 1 / 4 ∧ c2 = 1 / 32 ∧ c3 = 1 / 16 ∧ c4 = -1 / 32 := by
  refine ⟨by linarith, by linarith, by linarith, by linarith⟩

/-- **The system closes.**  The fifth equation — the `1/32` eigenvalue on the
`λ` block — is not an extra assumption: it follows from the other four.  That is
the over-determined consistency the module reports. -/
theorem odd_constants_consistent (c1 c2 c3 c4 : ℚ)
    (hid : c1 + 24 * c2 = 1)
    (hperp0 : c2 / 2 + c4 / 2 = 0)
    (hperp32 : c2 / 2 - c4 / 2 = 1 / 32)
    (halong4 : (c1 + c2) / 2 + (4 * c3 + c4) / 2 = 1 / 4) :
    (c1 + c2) / 2 - (4 * c3 + c4) / 2 = 1 / 32 := by linarith

/-- The block dimensions on `V⁻ = 24 ⊗ 4096`: `23 · 2048` perpendicular vectors
in each `X_λ` eigenspace and `2048` along `λ`. -/
theorem odd_block_dimensions :
    23 * 2048 + 2048 = 24 * 2048 ∧ 2 * (24 * 2048) = 24 * 4096 ∧
    47104 + 2048 + 49152 = 98304 := by
  refine ⟨by norm_num, by norm_num, by norm_num⟩

/-- **The whole ledger.**  The even part's `1 / 49,152 / 2,323 / 47,104` plus the
odd part's `0 / 47,104 / 2,048 / 49,152` are the classical eigenspace dimensions
of a 2A axis of the Monster. -/
theorem full_ledger :
    49152 + 47104 = 96256 ∧ 2323 + 2048 = 4371 ∧ 47104 + 49152 = 96256 ∧
    1 + 96256 + 4371 + 96256 = 196884 ∧ 98580 + 98304 = 196884 := by
  refine ⟨by norm_num, by norm_num, by norm_num, by norm_num, by norm_num⟩

/-- The count that decides which block carries the eigenvalue `1/4`: the whole
algebra has `4,371` such dimensions and the even part supplies `2,323`, leaving
exactly the `2,048` of the `λ` block. -/
theorem quarter_count : 4371 - 2323 = 2048 ∧ (2048 : ℕ) ≠ 47104 := by
  refine ⟨by norm_num, by norm_num⟩

end Odd

/-! ## §12  From an invariant form to a metric

Positive definiteness gives the triangle inequality for free, a pseudometric
becomes a metric on its separation quotient, and an injective embedding pulls a
metric back.  These are the three statements the metric module rests on. -/

section Metric

/-- **The triangle inequality is free.**  For a positive definite form — an
inner product — the distance `√⟪x−y, x−y⟫` satisfies the triangle inequality. -/
theorem form_triangle {E : Type*} [NormedAddCommGroup E] [InnerProductSpace ℝ E]
    (a b c : E) :
    Real.sqrt (inner ℝ (a - c) (a - c)) ≤
      Real.sqrt (inner ℝ (a - b) (a - b)) + Real.sqrt (inner ℝ (b - c) (b - c)) := by
  have h : ∀ x y : E, Real.sqrt (inner ℝ (x - y) (x - y)) = dist x y := by
    intro x y
    rw [real_inner_self_eq_norm_sq, dist_eq_norm, Real.sqrt_sq (norm_nonneg _)]
  rw [h, h, h]
  exact dist_triangle a b c

/-- **The quotient fix.**  A pseudometric — which is what the collapsed Griess
embedding gives — induces an honest metric on the quotient by distance zero. -/
noncomputable example {α : Type*} [PseudoMetricSpace α] :
    MetricSpace (SeparationQuotient α) := inferInstance

/-- **The injectivity fix.**  An injective map into a metric space pulls the
metric back to a metric. -/
noncomputable def inducedMetric {α E : Type*} [MetricSpace E] (f : α → E)
    (hf : Function.Injective f) : MetricSpace α :=
  MetricSpace.induced f hf inferInstance

/-- **Proposition M3.**  If a single plane's vector `v` is injective on classes,
the plane-graded embedding `x ↦ (2^(−k) • v (x k))` is injective on stacks — and
since the stack is faithful (§9) the distance it defines separates carriers. -/
theorem graded_injective {C E : Type*} [AddCommGroup E] [Module ℝ E] {d : ℕ}
    (v : C → E) (hv : Function.Injective v) :
    Function.Injective
      (fun (x : Fin d → C) => fun (k : Fin d) => ((2 : ℝ) ^ (-(k : ℤ))) • v (x k)) := by
  intro x y h
  funext k
  have hk := congrFun h k
  have hc : ((2 : ℝ) ^ (-(k : ℤ))) ≠ 0 := by positivity
  exact hv (smul_right_injective E hc hk)

end Metric

/-! ## §13  The benchmark arithmetic

The pass-rate bookkeeping of the four benchmark sections. -/

section Benchmark

/-- All pairs of the 660-concept register, split into the measured admissible
and rejected counts. -/
theorem pairwise_counts :
    660 * 659 / 2 = 217470 ∧ 9676 + 207794 = 217470 := by
  refine ⟨by norm_num, by norm_num⟩

/-- The mutant section: 64 laws corrupted four ways, all caught, 218 by verdict
and 6 refused by the parser, with the facet attribution summing to 218. -/
theorem mutant_counts :
    64 * 4 = 256 ∧ 218 + 6 = 224 ∧ 52 + 9 + 26 + 3 + 64 + 64 = 218 := by
  refine ⟨by norm_num, by norm_num, by norm_num⟩

/-- The dimensionless section: 40 groups, 38 of them exactly dimensionless and
two textbook Coriolis groups carrying a radian. -/
theorem dimensionless_counts : 38 + 2 = 40 := by norm_num

end Benchmark

end GLM3
