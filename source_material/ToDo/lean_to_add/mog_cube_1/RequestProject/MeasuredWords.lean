import Mathlib
import RequestProject.CubeSurfaceMOG

/-!
# Words with measurable content on the cube

The brief asks to start from words whose information is *tangible and
measurable*, so that the logic is computable.  The most tangible content a
physics word has is its **dimension**: the exponents of the six base quantities

    L (length), M (mass), T (time), I (current), Θ (temperature), N (amount).

This file puts that content on the cube and proves exactly what the substrate
can and cannot decide about it.

**The encoding.**  Dimension `d` is carried by the top cell of face `d`
(`dimWord`).  The remaining cells are filled in by the code, so *every* word is
a lawful codeword: a measurable word costs nothing to hold.  Multiplying two
quantities adds their dimension vectors, and that is exactly XOR of their
codewords (`dimWord_mul`) — the free, `TAX = 0` operation of the substrate.

**What it decides.**  An equation is accepted iff the two sides' codewords are
equal, and `dimWord_eq_iff` says precisely when that happens: iff the exponents
agree **mod 2**.  So

* `E = mc²`, `F = ma`, `E = ħ/t`, `p = mv`, `P = E/t`, `Q = It` are accepted
  (`accepts_true_equations`), and they are true;
* `E = mc` is rejected (`rejects_energy_eq_mass_velocity`), and it is false;
* `E = mc⁴` is **accepted although it is false**
  (`mod_two_blindness_witness`) — the exponents differ by 2.

**Why that ceiling is unavoidable.**  `xor_encoding_is_mod_two`: *any* encoding
of dimension vectors into the substrate for which composition is XOR is blind
to exponent differences of 2.  This is not a defect of the placement chosen
here; it is what characteristic 2 costs.  Getting beyond it needs a nonlinear
(priced) operation, not a better linear code.

**The price structure is sharp.**  A rejected equation is a nonzero codeword,
so by the minimum weight its tax is at least `8·Q` (`detected_error_min_tax`),
while an accepted one costs `0` (`accepted_tax_zero`).  There is nothing in
between: the substrate either sees a dimensional error at full price or does
not see it at all.

**One dimension per face.**  Dimension `d` lives on face `d`, so losing a face
is losing one dimension's channel — and that is repairable
(`dimension_channel_repairable`, a corollary of `face_erasure_correctable`).
-/

namespace MeasuredWords

open CubeMOG GolayHex

set_option maxRecDepth 100000

/-! ## 1. Dimension vectors -/

/-- A dimension: the exponents of `L, M, T, I, Θ, N`. -/
abbrev Dim := Fin 6 → ℤ

/-- The measurable content of some physics words. -/
def length : Dim := ![1, 0, 0, 0, 0, 0]
/-- Mass. -/
def mass : Dim := ![0, 1, 0, 0, 0, 0]
/-- Time. -/
def time : Dim := ![0, 0, 1, 0, 0, 0]
/-- Electric current. -/
def current : Dim := ![0, 0, 0, 1, 0, 0]
/-- Velocity (in particular the speed of light). -/
def velocity : Dim := ![1, 0, -1, 0, 0, 0]
/-- Acceleration. -/
def acceleration : Dim := ![1, 0, -2, 0, 0, 0]
/-- Force. -/
def force : Dim := ![1, 1, -2, 0, 0, 0]
/-- Energy. -/
def energy : Dim := ![2, 1, -2, 0, 0, 0]
/-- Action (the dimension of `ħ`). -/
def action : Dim := ![2, 1, -1, 0, 0, 0]
/-- Momentum. -/
def momentum : Dim := ![1, 1, -1, 0, 0, 0]
/-- Power. -/
def power : Dim := ![2, 1, -3, 0, 0, 0]
/-- Electric charge. -/
def charge : Dim := ![0, 0, 1, 1, 0, 0]

/-! ## 2. The encoding -/

theorem gxor_self (g : Grid) : gxor g g = 0 := by
  funext j i
  simp only [gxor, Bool.xor_self]
  rfl

theorem gxor_zero (g : Grid) : gxor g 0 = g := by
  funext j i
  show xor (g j i) false = g j i
  simp

/-- The parity of an exponent. -/
def oddZ (n : ℤ) : Bool := decide (n % 2 ≠ 0)

theorem oddZ_add (m n : ℤ) : oddZ (m + n) = xor (oddZ m) (oddZ n) := by
  have h : (m + n) % 2 = (m % 2 + n % 2) % 2 := Int.add_emod m n 2
  rcases Int.emod_two_eq_zero_or_one m with hm | hm <;>
    rcases Int.emod_two_eq_zero_or_one n with hn | hn <;>
      simp [oddZ, h, hm, hn]

/-- The message carried by a dimension vector: dimension `d` is switched into
the top cell of face `d`.  (The first six generators, which move the hexacode
word, are left alone.) -/
def dimBits (v : Dim) : Fin 12 → Bool := fun k =>
  if h : 6 ≤ (k : Nat) then oddZ (v ⟨(k : Nat) - 6, by have := k.isLt; omega⟩) else false

/-- **A measurable word as an object of the substrate.**  It is a codeword, so
holding it costs nothing. -/
def dimWord (v : Dim) : Grid := selG mogBasis (dimBits v)

theorem dimWord_isMog (v : Dim) : IsMog (dimWord v) :=
  selG_isMog mogBasis mogBasis_isMog _

/-- **Multiplication of quantities is XOR of their words.**  Composition is the
free operation of the substrate. -/
theorem dimWord_mul (u v : Dim) : gxor (dimWord u) (dimWord v) = dimWord (u + v) := by
  rw [dimWord, dimWord, selG_xor]
  congr 1
  funext k
  by_cases h : 6 ≤ (k : Nat) <;> simp [dimBits, h, oddZ_add]

/-! ## 3. What the substrate decides -/

/-- Reading the message back off a codeword. -/
def mogDecode (G : Grid) : Fin 12 → Bool :=
  ![bit0 (symbols G 0), bit1 (symbols G 0), bit0 (symbols G 1), bit1 (symbols G 1),
    bit0 (symbols G 2), bit1 (symbols G 2), G 0 0, G 1 0, G 2 0, G 3 0, G 4 0, G 5 0]

theorem mogDecode_selG : ∀ m : Fin 12 → Bool, mogDecode (selG mogBasis m) = m := by native_decide

theorem selG_mogBasis_injective : Function.Injective (selG mogBasis) := by
  intro m m' h
  rw [← mogDecode_selG m, ← mogDecode_selG m', h]

/-- **Exactly what the substrate can see**: two measurable words have the same
codeword iff their exponents agree mod 2. -/
theorem dimWord_eq_iff (u v : Dim) : dimWord u = dimWord v ↔ ∀ d, oddZ (u d) = oddZ (v d) := by
  constructor
  · intro h d
    have hb := selG_mogBasis_injective h
    have := congrFun hb ⟨6 + (d : Nat), by have := d.isLt; omega⟩
    have hd : (⟨(6 + (d : Nat)) - 6, by have := d.isLt; omega⟩ : Fin 6) = d := by
      apply Fin.ext; simp
    simpa [dimBits, hd] using this
  · intro h
    rw [dimWord, dimWord]
    congr 1
    funext k
    by_cases hk : 6 ≤ (k : Nat) <;> simp [dimBits, hk, h]

/-! ## 4. The measured verdicts -/

/-- The equations the substrate accepts, all of them physically true:
`E = mc²`, `F = ma`, `E·t = ħ`, `p = mv`, `P = E/t`, `Q = It`. -/
theorem accepts_true_equations :
    dimWord energy = dimWord (mass + velocity + velocity) ∧
    dimWord force = dimWord (mass + acceleration) ∧
    dimWord action = dimWord (energy + time) ∧
    dimWord momentum = dimWord (mass + velocity) ∧
    dimWord power = dimWord (energy - time) ∧
    dimWord charge = dimWord (current + time) := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
    · rw [dimWord_eq_iff]
      decide

/-- `E = mc` is rejected: the substrate sees the error. -/
theorem rejects_energy_eq_mass_velocity : dimWord energy ≠ dimWord (mass + velocity) := by
  rw [Ne, dimWord_eq_iff]
  intro h
  have := h 0
  revert this
  decide

/-- **The honest failure.**  `E = mc⁴` is accepted although it is false: the
exponents differ by 2, and the substrate composes by XOR, so it cannot see an
even discrepancy. -/
theorem mod_two_blindness_witness :
    energy ≠ mass + velocity + velocity + velocity + velocity ∧
    dimWord energy = dimWord (mass + velocity + velocity + velocity + velocity) := by
  constructor
  · intro h
    have := congrFun h 0
    revert this
    decide
  · rw [dimWord_eq_iff]
    decide

/-- **The ceiling is structural.**  Any encoding of dimensions into the grid
whose composition is XOR is blind to exponent differences of 2 — so no choice
of code or placement can do better, only a nonlinear (priced) operation can. -/
theorem xor_encoding_is_mod_two {enc : Dim → Grid}
    (hadd : ∀ u v, enc (u + v) = gxor (enc u) (enc v)) (u w : Dim) :
    enc (u + (w + w)) = enc u := by
  have hzero : enc (w + w) = 0 := by
    rw [hadd w w, gxor_self]
  rw [hadd u (w + w), hzero, gxor_zero]

/-! ## 5. The price of a verdict -/

/-- A word is a codeword, so it is held for free. -/
theorem accepted_tax_zero (u v : Dim) (h : dimWord u = dimWord v) :
    wtG (gxor (dimWord u) (dimWord v)) = 0 := by
  rw [h, (wtG_eq_zero_iff _).mpr (gxor_self _)]

/-- **A detected dimensional error costs at least `8·Q`.**  The difference of
two measurable words is a codeword, so if it is nonzero its weight is at least
the minimum weight 8.  Together with `accepted_tax_zero`: the substrate either
charges full price or sees nothing — there is no small error. -/
theorem detected_error_min_tax (u v : Dim) (h : dimWord u ≠ dimWord v) :
    8 ≤ wtG (gxor (dimWord u) (dimWord v)) := by
  refine mog_min_weight _ (IsMog_gxor (dimWord_isMog u) (dimWord_isMog v)) ?_
  intro hz
  apply h
  funext j i
  have := congrFun (congrFun hz j) i
  simp only [gxor, zero_apply] at this
  revert this
  cases dimWord u j i <;> cases dimWord v j i <;> simp

/-- The tax of a verdict, in the substrate's own units `Q = Y + 1/8`. -/
noncomputable def taxOf (u v : Dim) : ℝ := (wtG (gxor (dimWord u) (dimWord v)) : ℝ) * Q

theorem taxOf_accepted (u v : Dim) (h : dimWord u = dimWord v) : taxOf u v = 0 := by
  rw [taxOf, accepted_tax_zero u v h]
  simp

theorem taxOf_detected (u v : Dim) (h : dimWord u ≠ dimWord v) : 8 * Q ≤ taxOf u v := by
  have h8 := detected_error_min_tax u v h
  have hQ : (0:ℝ) < Q := Q_pos
  have : (8:ℝ) ≤ (wtG (gxor (dimWord u) (dimWord v)) : ℝ) := by exact_mod_cast h8
  rw [taxOf]
  nlinarith

/-! ## 6. One dimension per face -/

/-- Dimension `d` is carried by the top cell of face `d`. -/
theorem dimWord_face (v : Dim) (d : Fin 6) : dimWord v d 0 = oddZ (v d) := by
  have e : ∀ k : Fin 12, mogDecode (dimWord v) k = dimBits v k :=
    congrFun (mogDecode_selG (dimBits v))
  have hd : dimBits v ⟨6 + (d : Nat), by omega⟩ = oddZ (v d) := by
    simp [dimBits]
  rw [← hd, ← e]
  clear hd e
  fin_cases d <;> rfl

/-- **A lost dimension channel is repairable.**  If two measurable words are
known to agree on every face but one, they are equal: the exponent of the
missing dimension is reconstructed by the code. -/
theorem dimension_channel_repairable (u v : Dim) (d : Fin 6)
    (h : ∀ j, j ≠ d → dimWord u j = dimWord v j) : dimWord u = dimWord v :=
  face_erasure_correctable (dimWord_isMog u) (dimWord_isMog v) d h

end MeasuredWords
