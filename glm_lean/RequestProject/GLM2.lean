/-
# Formal companion to the second-generation Geometric Language Machine

This file formalises the *structural* propositions of the GLM-2 operational
paper (`glm2/glm2_paper.py`).  Everything that is a measurement — the Golay
weight enumerator, the Leech theta series, the Conway orbit census, the 462
concepts of the register — is verified computationally by the Python
artefacts.  What is proved here is the part of the argument that is a theorem.

* §1  **The meaning module.**  Ten rational exponents, a decimal scale, a
  tensor rank and three parities.  The parity part has 2-torsion, so no
  injective homomorphism into a torsion-free group (in particular into `ℤ^24`
  or the Leech lattice) can exist; that is why the codec reduces exactly three
  slots mod 2, and why nothing else is reduced.

* §2  **The mod-2 ceiling, and its rational strengthening.**  GLM-1's ceiling
  theorem says an XOR-composing encoder cannot see an even shift.  Over
  *rational* exponents the situation is far worse for such an encoder, and far
  better for the argument: since `ℚ^10` is divisible, **every** additive map
  from the meaning module into a group of exponent 2 is identically zero.  A
  mod-2 carrier is not merely lossy on GLM-2's meanings, it is blind.

* §3  **The new axes carry real distinctions.**  Torque is not energy (the
  plane-angle exponent separates them), `E = m c^4` is not `E = m c^2`, and
  `√(E/m) = c` holds exactly — a statement that cannot even be written with
  integer exponents.

* §4  **The derived gradings.**  `T = e_T + e_I` and `C = e_I`, read in
  `ZMod 2`, are group homomorphisms out of the exponent lattice; hence they
  are automatically additive over products, and `d/dt` flips `T`.

* §5  **The operator algebra.**  The plain cross product and the rotational
  cross product differ by one inverse radian, so they are never equal; this is
  the same one-radian gap that separates torque from energy.

* §6  **Unique decoding inside the packing radius.**  In any metric space, if
  distinct carriers are at distance at least `D` and a received point is
  within `r` of a carrier with `2r < D`, that carrier is strictly the nearest.
  For the Leech lattice in the integer model, `D² = 32` and `r² = 7`.

* §7  **Lattice and ledger arithmetic.**  The index `2^36`, the
  `Λ/2Λ` class census `1 + 98,280 + 8,386,560 + 8,292,375 = 2^24`, and the
  Griess ledger `300 + 98,280 + 98,304 = 196,884`.

* §8  **The Matsuo algebra of `S_3`**, built here rather than quoted:
  commutative, non-associative, every basis vector an idempotent whose adjoint
  has spectrum `{1, 0, η}` with an explicit eigenbasis, the Jordan-type fusion
  rule `η ⋆ η ⊆ 1 ⊕ 0`, and at `η = 1/4` the Norton–Sakuma structure constants
  `a₀a₁ = (1/8)(a₀ + a₁ - a_ρ)` of the Monster's 2A algebra.

No `sorry`, no new axioms.
-/

import Mathlib

set_option autoImplicit false
set_option linter.style.longLine false
set_option maxHeartbeats 1000000

namespace GLM2

/-- In `ZMod 2` every element is its own negative. -/
theorem zmod2_add_self (x : ZMod 2) : x + x = 0 := by revert x; decide

theorem zmod2_neg (x : ZMod 2) : -x = x := by revert x; decide

/-! ## §1  The meaning module and its torsion -/

/-- The exponent vector of a GLM-2 meaning: ten rationals, in the axis order
`L M T I H N J A S B` (length, mass, time, current, temperature, amount,
luminous intensity, plane angle, solid angle, information). -/
abbrev Exps : Type := Fin 10 → ℚ

/-- The integral exponent vectors, the ones a mod-2 carrier could even try to
represent. -/
abbrev IntExps : Type := Fin 10 → ℤ

/-- A GLM-2 meaning: the exponents, the decimal scale, the tensor rank and the
three parities.  The two nominal labels play no part in the group law and are
omitted here. -/
structure Meaning where
  exps : Exps
  scale : ℚ
  rank : ℤ
  par : Fin 3 → ZMod 2

namespace Meaning

instance : Zero Meaning := ⟨⟨0, 0, 0, 0⟩⟩

instance : Add Meaning :=
  ⟨fun a b => ⟨a.exps + b.exps, a.scale + b.scale, a.rank + b.rank, a.par + b.par⟩⟩

instance : Neg Meaning := ⟨fun a => ⟨-a.exps, -a.scale, -a.rank, -a.par⟩⟩

@[simp] theorem add_exps (a b : Meaning) : (a + b).exps = a.exps + b.exps := rfl
@[simp] theorem add_par (a b : Meaning) : (a + b).par = a.par + b.par := rfl
@[simp] theorem zero_par : (0 : Meaning).par = 0 := rfl

/-- The parity of a meaning, as an element of `(ZMod 2)^3`.  This is a
homomorphism for the group law of the meaning module. -/
def parity (m : Meaning) : Fin 3 → ZMod 2 := m.par

@[simp] theorem parity_add (a b : Meaning) : (a + b).parity = a.parity + b.parity := rfl

/-- Every meaning is annihilated by 2 in its parity component: the meaning
module has 2-torsion. -/
theorem parity_two_torsion (m : Meaning) : m.parity + m.parity = 0 := by
  funext i
  exact zmod2_add_self (m.par i)

/-- There is a meaning with nonzero parity: a pseudoscalar. -/
def pseudoscalar : Meaning := ⟨0, 0, 0, ![1, 0, 0]⟩

theorem pseudoscalar_parity_ne_zero : pseudoscalar.parity ≠ 0 := by
  intro h
  have := congrFun h 0
  simp [pseudoscalar, parity] at this

end Meaning

/--
**Torsion obstruction (paper Proposition 2.3).**  A group in which `g + g = 0`
forces `g = 0` — a torsion-free group, in particular `ℤ^24` and the Leech
lattice — admits no injective additive map from a group with an element of
order two.  Consequently the encoder cannot be an injective homomorphism on
all of the meaning module: three slots must be read mod 2, and because a
parity genuinely is an element of `ZMod 2`, nothing is lost by doing so.
-/
theorem no_injective_of_two_torsion {A G : Type*} [AddCommGroup A] [AddCommGroup G]
    (hG : ∀ g : G, g + g = 0 → g = 0) (a : A) (ha : a ≠ 0) (haa : a + a = 0)
    (f : A →+ G) : ¬ Function.Injective f := by
  intro hf
  have h : f a + f a = 0 := by rw [← map_add, haa, map_zero]
  exact ha (hf (by rw [hG _ h, map_zero]))

/-- The parity group `(ZMod 2)^3` really does have an element of order two. -/
theorem parity_has_order_two :
    ∃ a : Fin 3 → ZMod 2, a ≠ 0 ∧ a + a = 0 := by
  refine ⟨![1, 0, 0], ?_, ?_⟩
  · intro h
    have := congrFun h 0
    simp at this
  · funext i
    exact zmod2_add_self _

/-- Spelled out for the parity group: no injective homomorphism into a
torsion-free group. -/
theorem parity_not_embeddable {G : Type*} [AddCommGroup G]
    (hG : ∀ g : G, g + g = 0 → g = 0) (f : (Fin 3 → ZMod 2) →+ G) :
    ¬ Function.Injective f := by
  obtain ⟨a, ha, haa⟩ := parity_has_order_two
  exact no_injective_of_two_torsion hG a ha haa f

/-! ## §2  The mod-2 ceiling, and its rational strengthening -/

/--
**The mod-2 ceiling (GLM-1, Proposition 1).**  An encoder of integer exponent
vectors whose composition law satisfies `m + m = 0` — that is, XOR — cannot
distinguish `d` from `d + 2u`.
-/
theorem xor_blind {M : Type*} [AddCommGroup M] (hM : ∀ m : M, m + m = 0)
    (f : IntExps →+ M) (d u : IntExps) : f (d + (2 : ℤ) • u) = f d := by
  have h : f ((2 : ℤ) • u) = 0 := by rw [two_zsmul, map_add, hM]
  rw [map_add, h, add_zero]

/--
**The rational strengthening (GLM-2).**  The meaning module is *divisible*:
every exponent vector is twice another one.  Hence every additive map from it
into a group of exponent 2 is identically zero.  An XOR carrier is not merely
unable to separate `d` from `d + 2u` on GLM-2's meanings — it separates
nothing at all.  This is the precise sense in which GLM-2 has left the mod-2
regime rather than merely working around it.
-/
theorem xor_is_blind_on_rational_meanings {M : Type*} [AddCommGroup M]
    (hM : ∀ m : M, m + m = 0) (f : Exps →+ M) (d : Exps) : f d = 0 := by
  have hd : ((2 : ℚ)⁻¹ • d) + ((2 : ℚ)⁻¹ • d) = d := by
    funext i
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]
    ring
  calc f d = f ((2 : ℚ)⁻¹ • d) + f ((2 : ℚ)⁻¹ • d) := by rw [← map_add, hd]
    _ = 0 := hM _

/-- The same statement, phrased as the paper states it: no nonzero XOR encoder
of GLM-2 meanings exists. -/
theorem no_nonzero_xor_encoder {M : Type*} [AddCommGroup M]
    (hM : ∀ m : M, m + m = 0) (f : Exps →+ M) : f = 0 :=
  AddMonoidHom.ext fun d => by
    simpa using xor_is_blind_on_rational_meanings hM f d

/-! ## §3  The new axes carry real distinctions -/

/-- Energy: `L^2 M T^-2`. -/
def energy : Exps := ![2, 1, -2, 0, 0, 0, 0, 0, 0, 0]

/-- Mass. -/
def mass : Exps := ![0, 1, 0, 0, 0, 0, 0, 0, 0, 0]

/-- Speed: `L T^-1`. -/
def speed : Exps := ![1, 0, -1, 0, 0, 0, 0, 0, 0, 0]

/-- Torque: `L^2 M T^-2 A^-1`, an energy per radian. -/
def torque : Exps := ![2, 1, -2, 0, 0, 0, 0, -1, 0, 0]

/-- The dimension of `m c^4`. -/
def mc4 : Exps := ![4, 1, -4, 0, 0, 0, 0, 0, 0, 0]

/-- `E = m c²` holds exactly. -/
theorem energy_eq_mass_add_two_speed : mass + (2 : ℚ) • speed = energy := by
  funext i
  fin_cases i <;> norm_num [mass, speed, energy]

/-- `E = m c⁴` is false. -/
theorem mc4_ne_energy : mass + (4 : ℚ) • speed ≠ energy := by
  intro h
  have h0 := congrFun h 0
  norm_num [mass, speed, energy] at h0

/-- `m c⁴` and energy agree modulo 2 in every exponent, so a mod-2 carrier
would accept `E = m c⁴`.  (Compare `xor_blind`.) -/
theorem mc4_agrees_mod_two (i : Fin 10) :
    ((mc4 i).num : ZMod 2) = ((energy i).num : ZMod 2) := by
  fin_cases i <;> simp [mc4, energy] <;> decide

/-- `√(E/m) = c`, exactly.  The half-power is the reason the exponents live in
`ℚ` and not in `ℤ`: this equation cannot even be *written* in GLM-1. -/
theorem sqrt_energy_over_mass : (2 : ℚ)⁻¹ • (energy - mass) = speed := by
  funext i
  fin_cases i <;> norm_num [energy, mass, speed]

/-- Half-powers genuinely leave the integer lattice: `√c` has a length
exponent of `1/2`, which no integral exponent vector reaches.  This is why the
meaning module is stated over `ℚ` and not over `ℤ`. -/
theorem half_speed_not_integral :
    ¬ ∃ z : IntExps, ∀ i, ((2 : ℚ)⁻¹ • speed) i = (z i : ℚ) := by
  rintro ⟨z, hz⟩
  have h0 := hz 0
  norm_num [speed] at h0
  have h1 : ((2 * z 0 : ℤ) : ℚ) = ((1 : ℤ) : ℚ) := by push_cast; linarith
  have h2 : (2 * z 0 : ℤ) = 1 := by exact_mod_cast h1
  omega

/-- Torque is not energy: they differ in the plane-angle exponent, the axis
GLM-1 did not have. -/
theorem torque_ne_energy : torque ≠ energy := by
  intro h
  have h7 : torque 7 = energy 7 := congrFun h 7
  simp [torque, energy] at h7

/-- and they agree in every other exponent, so *only* the angle axis separates
them. -/
theorem torque_eq_energy_off_angle (i : Fin 10) (hi : i ≠ 7) : torque i = energy i := by
  fin_cases i <;> simp_all [torque, energy]

/-! ## §4  The derived gradings -/

/-- The time-reversal grading of an integral exponent vector:
`T = e_T + e_I` in `ZMod 2`, where `e_T` is the time exponent (axis 2) and
`e_I` the current exponent (axis 3). -/
def tGrade (e : IntExps) : ZMod 2 := (e 2 : ZMod 2) + (e 3 : ZMod 2)

/-- The charge-conjugation grading: `C = e_I` in `ZMod 2`. -/
def cGrade (e : IntExps) : ZMod 2 := (e 3 : ZMod 2)

/-- **The gradings are homomorphisms.**  Because they are read off the
exponents rather than stored, they are additive over products for free: there
is no way to tag a concept inconsistently. -/
theorem tGrade_add (a b : IntExps) : tGrade (a + b) = tGrade a + tGrade b := by
  simp only [tGrade, Pi.add_apply]
  push_cast
  ring

theorem cGrade_add (a b : IntExps) : cGrade (a + b) = cGrade a + cGrade b := by
  simp only [cGrade, Pi.add_apply]
  push_cast
  ring

theorem tGrade_neg (a : IntExps) : tGrade (-a) = tGrade a := by
  simp only [tGrade, Pi.neg_apply]
  push_cast
  rw [zmod2_neg, zmod2_neg]

/-- One unit of time, as an integral exponent vector. -/
def unitT : IntExps := ![0, 0, 1, 0, 0, 0, 0, 0, 0, 0]

/-- **`d/dt` flips the time-reversal grading**, for every concept, with no
table and no special case. -/
theorem tGrade_ddt (a : IntExps) : tGrade (a - unitT) = tGrade a + 1 := by
  have h : ((a - unitT) 2 : ℤ) = a 2 - 1 := by simp [unitT]
  have h' : ((a - unitT) 3 : ℤ) = a 3 := by simp [unitT]
  simp only [tGrade, h, h']
  push_cast
  rw [sub_eq_add_neg, show (-1 : ZMod 2) = 1 from by decide]
  ring

/-- Time is T-odd, energy is T-even. -/
theorem tGrade_examples :
    tGrade unitT = 1 ∧ tGrade ![2, 1, -2, 0, 0, 0, 0, 0, 0, 0] = 0 := by
  constructor
  · simp [tGrade, unitT]
  · simp [tGrade]
    decide

/-! ## §5  The operator algebra: two different cross products -/

/-- One unit of plane angle (axis 7). -/
def unitA : Exps := ![0, 0, 0, 0, 0, 0, 0, 1, 0, 0]

/-- The plain cross product on exponents: `E × H`, no radian. -/
def crossE (a b : Exps) : Exps := a + b

/-- The rotational cross product: `r × F`, one radian consumed. -/
def momentE (a b : Exps) : Exps := a + b - unitA

/-- The two products differ in the angle exponent by exactly one, hence are
never equal.  This is the same gap as `torque ≠ energy`. -/
theorem crossE_ne_momentE (a b : Exps) : crossE a b ≠ momentE a b := by
  intro h
  have h7 := congrFun h 7
  simp [crossE, momentE, unitA] at h7
  linarith

theorem momentE_angle (a b : Exps) :
    momentE a b 7 = crossE a b 7 - 1 := by
  simp [crossE, momentE, unitA]

/-- Torque is the rotational cross product of position with force. -/
theorem torque_is_moment :
    momentE ![1, 0, 0, 0, 0, 0, 0, 0, 0, 0] ![1, 1, -2, 0, 0, 0, 0, 0, 0, 0] = torque := by
  funext i
  fin_cases i <;> norm_num [momentE, unitA, torque]

/-! ## §6  Unique decoding inside the packing radius -/

/--
**Unique decoding.**  If two carriers are at distance at least `D`, a received
point within `r` of one of them, with `2r < D`, is strictly closer to that one
than to the other.  Nearest-point decoding therefore returns the original
concept, unchanged — as opposed to snapping, which returns a different one.
-/
theorem unique_decoding {X : Type*} [MetricSpace X] {x z y : X} {D r : ℝ}
    (hxz : D ≤ dist x z) (hyx : dist y x ≤ r) (h2r : 2 * r < D) :
    dist y x < dist y z := by
  have htri : dist x z ≤ dist x y + dist y z := dist_triangle x y z
  have hxy : dist x y = dist y x := dist_comm x y
  have : D - r ≤ dist y z := by
    have := htri.trans (by linarith [hxy ▸ hyx] : dist x y + dist y z ≤ r + dist y z)
    linarith
  linarith

/-- In the Leech lattice's integer model the minimal squared norm is 32 and
every corruption of squared magnitude at most 7 is repaired exactly, because
`2√7 < √32`. -/
theorem packing_radius_gap : 2 * Real.sqrt 7 < Real.sqrt 32 := by
  have h7 : (0 : ℝ) ≤ 7 := by norm_num
  have hsq : (2 * Real.sqrt 7) ^ 2 = 28 := by
    rw [mul_pow, Real.sq_sqrt h7]; norm_num
  have hnn : (0 : ℝ) ≤ 2 * Real.sqrt 7 := by positivity
  rw [show (32 : ℝ) = 32 from rfl]
  nlinarith [Real.sq_sqrt (show (0:ℝ) ≤ 32 by norm_num),
             Real.sqrt_nonneg (32 : ℝ), hsq, hnn]

/-- The instantiation the codec uses. -/
theorem leech_unique_decoding {X : Type*} [MetricSpace X] {x z y : X}
    (hxz : Real.sqrt 32 ≤ dist x z) (hyx : dist y x ≤ Real.sqrt 7) :
    dist y x < dist y z :=
  unique_decoding hxz hyx packing_radius_gap

/-! ## §7  Lattice and ledger arithmetic -/

/-- The index of the Leech lattice in `ℤ^24` in the integer (×√8) model,
derived exactly as the paper derives it: two parities, a Golay codeword for
the mod-4 pattern, two lifts mod 8 per coordinate, and the sum condition
halving the result. -/
theorem leech_index : 2 * 2 ^ 12 * 2 ^ 24 / 2 = 2 ^ 36 ∧ 8 ^ 24 / 2 ^ 36 = 2 ^ 36 := by
  refine ⟨by norm_num, by norm_num⟩

/-- The `Λ/2Λ` class census closes exactly, from the theta coefficients alone:
one zero class, 98,280 type-2 classes (antipodal pairs of minimal vectors),
8,386,560 type-3 classes, and 8,292,375 type-4 classes (coordinate frames of
48 vectors each). -/
theorem class_census :
    196560 / 2 = 98280 ∧ 16773120 / 2 = 8386560 ∧ 398034000 / 48 = 8292375 ∧
    1 + 98280 + 8386560 + 8292375 = 2 ^ 24 := by
  refine ⟨by norm_num, by norm_num, by norm_num, by norm_num⟩

/-- The Griess ledger: `dim S²(ℝ^24) = 300`, the 98,280 type-2 classes and
`24 × 4096 = 98,304` add to the 196,884 of the `j`-function. -/
theorem griess_ledger :
    24 * 25 / 2 = 300 ∧ 24 * 4096 = 98304 ∧ 300 + 98280 + 98304 = 196884 := by
  refine ⟨by norm_num, by norm_num, by norm_num⟩

/-- The kissing number and the packing radius, in the integer model. -/
theorem leech_metrics : 32 / 4 = 8 ∧ 2 * 98280 = 196560 := by
  refine ⟨by norm_num, by norm_num⟩

/-! ## §8  The Matsuo algebra of `S_3` -/

/-- The Matsuo algebra of the three transpositions of `S_3` with parameter
`η`, given by `aᵢaᵢ = aᵢ` and `aᵢaⱼ = (η/2)(aᵢ + aⱼ - a_k)` for the third
index `k`.  Written out componentwise so that every identity below is an
identity of rational functions in `η`. -/
def mmul (η : ℚ) (x y : Fin 3 → ℚ) : Fin 3 → ℚ :=
  ![ x 0 * y 0 + (η/2) * (x 0 * y 1 + x 1 * y 0) + (η/2) * (x 0 * y 2 + x 2 * y 0)
       - (η/2) * (x 1 * y 2 + x 2 * y 1),
     x 1 * y 1 + (η/2) * (x 0 * y 1 + x 1 * y 0) + (η/2) * (x 1 * y 2 + x 2 * y 1)
       - (η/2) * (x 0 * y 2 + x 2 * y 0),
     x 2 * y 2 + (η/2) * (x 0 * y 2 + x 2 * y 0) + (η/2) * (x 1 * y 2 + x 2 * y 1)
       - (η/2) * (x 0 * y 1 + x 1 * y 0) ]

/-- The three axes. -/
def a0 : Fin 3 → ℚ := ![1, 0, 0]
def a1 : Fin 3 → ℚ := ![0, 1, 0]
def a2 : Fin 3 → ℚ := ![0, 0, 1]

/-- The algebra is commutative. -/
theorem mmul_comm (η : ℚ) (x y : Fin 3 → ℚ) : mmul η x y = mmul η y x := by
  funext i
  fin_cases i <;> simp [mmul] <;> ring

/-- Every axis is an idempotent. -/
theorem mmul_idem (η : ℚ) : mmul η a0 a0 = a0 ∧ mmul η a1 a1 = a1 ∧ mmul η a2 a2 = a2 := by
  refine ⟨?_, ?_, ?_⟩ <;>
    (funext i; fin_cases i <;> simp [mmul, a0, a1, a2])

/-- The defining structure constant: `a₀a₁ = (η/2)(a₀ + a₁ - a₂)`. -/
theorem mmul_a0_a1 (η : ℚ) : mmul η a0 a1 = (η/2) • (a0 + a1 - a2) := by
  funext i
  fin_cases i <;> simp [mmul, a0, a1, a2]

/-- **Norton–Sakuma 2A.**  At `η = 1/4` the structure constants are
`a₀a₁ = (1/8)(a₀ + a₁ - a_ρ)`, which is the algebra generated by two 2A axes
of the Monster's Griess algebra. -/
theorem norton_sakuma_2A : mmul (1/4) a0 a1 = (1/8 : ℚ) • (a0 + a1 - a2) := by
  rw [mmul_a0_a1]
  norm_num

/-- At `η = 1/32` the algebra is 3C. -/
theorem matsuo_3C : mmul (1/32) a0 a1 = (1/64 : ℚ) • (a0 + a1 - a2) := by
  rw [mmul_a0_a1]
  norm_num

/-- The algebra is **not** associative: `(a₀a₀)a₁ ≠ a₀(a₀a₁)` at `η = 1/4`,
so the Norton–Sakuma 2A algebra is a genuine commutative non-associative
algebra, which is what the Griess product is and what GLM-1's snap-based
"product" turned out not to be. -/
theorem mmul_not_assoc_quarter :
    mmul (1/4) (mmul (1/4) a0 a0) a1 ≠ mmul (1/4) a0 (mmul (1/4) a0 a1) := by
  intro h
  have h1 : (mmul (1/4) (mmul (1/4) a0 a0) a1) 1
      = (mmul (1/4) a0 (mmul (1/4) a0 a1)) 1 := congrFun h 1
  simp [mmul, a0, a1] at h1
  norm_num at h1

/-- Likewise at `η = 1/32`, the 3C algebra. -/
theorem mmul_not_assoc_3C :
    mmul (1/32) (mmul (1/32) a0 a0) a1 ≠ mmul (1/32) a0 (mmul (1/32) a0 a1) := by
  intro h
  have h1 : (mmul (1/32) (mmul (1/32) a0 a0) a1) 1
      = (mmul (1/32) a0 (mmul (1/32) a0 a1)) 1 := congrFun h 1
  simp [mmul, a0, a1] at h1
  norm_num at h1

/-- **The spectrum of `ad(a₀)` is `{1, 0, η}`**, with an explicit eigenbasis:
`a₀` has eigenvalue 1, `a₁ + a₂ - η a₀` has eigenvalue 0, and `a₁ - a₂` has
eigenvalue `η`.  This is exactly the statement that `a₀` is an axis of Jordan
type `η`. -/
theorem ad_a0_eigen (η : ℚ) :
    mmul η a0 a0 = (1 : ℚ) • a0 ∧
    mmul η a0 (a1 + a2 - η • a0) = (0 : ℚ) • (a1 + a2 - η • a0) ∧
    mmul η a0 (a1 - a2) = η • (a1 - a2) := by
  refine ⟨?_, ?_, ?_⟩ <;> (funext i; fin_cases i <;> simp [mmul, a0, a1, a2] <;> ring)

/-- The three eigenvectors are a basis of `ℚ³`: the determinant of the change
of basis is `-2`, independently of `η`. -/
theorem ad_a0_eigenbasis (η : ℚ) :
    Matrix.det !![(1 : ℚ), -η, 0; 0, 1, 1; 0, 1, -1] = -2 := by
  simp [Matrix.det_fin_three]
  ring

/-- **The Jordan-type fusion rule `η ⋆ η ⊆ 1 ⊕ 0`.**  The square of the
`η`-eigenvector is `(a₁ - a₂)² = η a₀ + (1 - η)(a₁ + a₂)`, which lies in the
span of the `1`- and `0`-eigenvectors and has no component along the
`η`-eigenvector `a₁ - a₂`.  That is exactly what makes the Miyamoto map
(`+1` on `1 ⊕ 0`, `-1` on the `η`-part) an algebra automorphism. -/
theorem fusion_eta_eta (η : ℚ) :
    mmul η (a1 - a2) (a1 - a2) = η • a0 + (1 - η) • (a1 + a2) := by
  funext i
  fin_cases i <;> simp [mmul, a0, a1, a2] <;> ring

end GLM2
