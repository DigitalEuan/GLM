/-
# Why the 24-bit word is a derived carrier and not the primary one

This file is **retrieved material**: `glm_lean/RequestProject/GLM.lean` of the
supplied archive (`source_material/GLM-main.zip`) is the first Lean-backed
iteration of the GLM, and its opening two sections settle a design question the
present system still answers the same way — *what is the primary object, the
meaning or the bit pattern?*

The archive's answer, proved here and sharpened, is that the bit pattern
**cannot** be primary as soon as its composition law is XOR:

* `xor_blind` — an encoder of dimension vectors into an abelian group of
  exponent 2 (which is exactly what an `F₂` word under XOR is) cannot see any
  even shift of its argument;
* `xor_kernel_iff` — and that is the whole of the obstruction: two dimension
  vectors are identified by *every* such encoder precisely when they agree
  componentwise mod 2, the universal such encoder being reduction into
  `Fin 7 → ZMod 2`;
* `no_injective_additive_into_char_two`, `f2_carrier_cannot_be_primary` — so no
  such encoder is injective at all, whatever the encoding and however wide the
  word;
* `mc4_indistinguishable_under_xor` — the concrete failure the archive uses as
  its witness: `E = m c⁴` and `E = m c²` get the same code, although the
  exact `ℤ⁷` comparison rejects the first.

What survives is the *derived* carrier, and this file adds the part the archive
left implicit — that the box it chose is maximal:

* `digits_injOn` — the base-9 zigzag digit vector of a dimension determines the
  dimension on the representable box `[-4,4]⁷`, so deriving bits from meaning
  loses nothing;
* `carrier_card`, `carrier_fits_24_bits`, `carrier_embeds` — `9⁷ = 4 782 969`
  digit vectors, which fit in a 24-bit word;
* `carrier_slack` — with `11 994 247` words left over;
* `carrier_box_maximal_in_rank` and `carrier_box_maximal_in_radius` — and an
  eighth dimension, or a ninth exponent value, would not fit. The box
  `[-4,4]⁷` is therefore the largest of its shape that a 24-bit word carries.

Finally the archive's 16-state column codec, which is the reason a MOG column
can be recoded as a (label, fibre index) pair without loss:

* `colLabel_xor` — the column label map is `GF(2)`-linear;
* `fibre_card`, `fibres_partition` — and it is a 4-to-1 fibration of the
  sixteen column states onto the four labels.
-/
import Mathlib

namespace GLM.DimensionCarrier

open Finset

/-! ## 1. The mod-2 ceiling -/

/-- A physical dimension is an exponent vector in `ℤ⁷`: length, mass, time,
current, temperature, amount of substance, luminous intensity. -/
abbrev Dim : Type := Fin 7 → ℤ

/-- **XOR is blind to even shifts.** Let `f` carry composition of quantities
(addition of exponent vectors) to the operation of an abelian group in which
every element is its own inverse — the defining property of XOR on bit vectors,
`F₂`-vector spaces being exactly the abelian groups of exponent two. Then `f`
cannot distinguish `d` from `d + 2u`. -/
theorem xor_blind {M : Type*} [AddCommGroup M] (hM : ∀ m : M, m + m = 0)
    (f : Dim →+ M) (d u : Dim) : f (d + (2 : ℤ) • u) = f d := by
  have h : f ((2 : ℤ) • u) = 0 := by rw [two_zsmul, map_add, hM]
  rw [map_add, h, add_zero]

/-- The mod-2 reduction of a dimension vector: the universal XOR-composing
encoder, through which every other one factors. -/
def modTwo (d : Dim) : Fin 7 → ZMod 2 := fun i => (d i : ZMod 2)

/-- **The ceiling is exactly a mod-2 phenomenon.** Two dimension vectors differ
by an even shift — equivalently, are identified by every XOR-composing encoder
— precisely when they agree componentwise mod 2. -/
theorem xor_kernel_iff (d e : Dim) :
    (∃ u : Dim, e = d + (2 : ℤ) • u) ↔ modTwo e = modTwo d := by
  constructor
  · rintro ⟨u, rfl⟩
    funext i
    simp only [modTwo, Pi.add_apply, Pi.smul_apply, smul_eq_mul]
    push_cast
    rw [show (2 : ZMod 2) = 0 by decide]
    ring
  · intro h
    refine ⟨fun i => (e i - d i) / 2, ?_⟩
    funext i
    have hi : ((e i : ZMod 2)) = ((d i : ZMod 2)) := congrFun h i
    have h2 : (2 : ℤ) ∣ (e i - d i) := by
      have : ((e i - d i : ℤ) : ZMod 2) = 0 := by push_cast; rw [hi]; ring
      exact (ZMod.intCast_zmod_eq_zero_iff_dvd _ 2).mp this
    obtain ⟨k, hk⟩ := h2
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]
    rw [hk]
    omega

/-- **No bit pattern can be primary.** An encoder whose composition law is XOR
is never injective: it identifies `d` with `d + 2u` for every `u`. -/
theorem no_injective_additive_into_char_two {M : Type*} [AddCommGroup M]
    (hM : ∀ m : M, m + m = 0) (f : Dim →+ M) : ¬ Function.Injective f := by
  intro hinj
  have h := xor_blind hM f 0 (fun _ => 1)
  rw [zero_add] at h
  have h0 : ((2 : ℤ) • (fun _ => 1 : Dim)) = (0 : Dim) := hinj h
  have h1 := congrFun h0 0
  simp at h1

/-- The case the GLM cares about: no XOR-composing encoder into 24-bit words
separates all dimension vectors, whatever the encoding. -/
theorem f2_carrier_cannot_be_primary (f : Dim →+ (Fin 24 → ZMod 2)) :
    ¬ Function.Injective f :=
  no_injective_additive_into_char_two
    (fun m => by funext i; exact CharTwo.add_self_eq_zero (m i)) f

/-! ## 2. The witness: `m c⁴` -/

/-- The dimension of energy, `L² M T⁻²`. -/
def energyDim : Dim := ![2, 1, -2, 0, 0, 0, 0]

/-- The dimension of `m c⁴`, that is `L⁴ M T⁻⁴`. -/
def mc4Dim : Dim := ![4, 1, -4, 0, 0, 0, 0]

/-- The even shift separating `m c²` from `m c⁴`. -/
def mc4Shift : Dim := ![1, 0, -1, 0, 0, 0, 0]

/-- `m c⁴` differs from energy by an even shift. -/
theorem mc4_eq : mc4Dim = energyDim + (2 : ℤ) • mc4Shift := by
  funext i
  fin_cases i <;> simp [mc4Dim, energyDim, mc4Shift]

/-- Exactly over `ℤ⁷`, `m c⁴` is not energy: the exact checker rejects it. -/
theorem mc4_ne : mc4Dim ≠ energyDim := by
  intro h
  have := congrFun h 0
  simp [mc4Dim, energyDim] at this

/-- **The failure, concretely.** No XOR-composing encoder can reject
`E = m c⁴`: it gives `m c⁴` and energy the same code although the two
dimensions differ. -/
theorem mc4_indistinguishable_under_xor {M : Type*} [AddCommGroup M]
    (hM : ∀ m : M, m + m = 0) (f : Dim →+ M) :
    f mc4Dim = f energyDim ∧ mc4Dim ≠ energyDim :=
  ⟨by rw [mc4_eq]; exact xor_blind hM f _ _, mc4_ne⟩

/-! ## 3. The derived carrier, and why its box is maximal -/

/-- The zigzag digit map `[-4,4] → {0,…,8}`: `0 ↦ 0`, `1 ↦ 1`, `-1 ↦ 2`,
`2 ↦ 3`, `-2 ↦ 4`, and so on. -/
def zigzag (n : ℤ) : ℕ := if 0 ≤ n then 2 * n.toNat else 2 * (-n).toNat - 1

/-- On `[-4,4]` the zigzag map lands in `{0,…,8}`. -/
theorem zigzag_lt_nine {n : ℤ} (h : -4 ≤ n) (h' : n ≤ 4) : zigzag n < 9 := by
  unfold zigzag
  split <;> omega

/-- On `[-4,4]` the zigzag map is injective. -/
theorem zigzag_injOn {m n : ℤ} (hm : -4 ≤ m) (hm' : m ≤ 4) (hn : -4 ≤ n)
    (hn' : n ≤ 4) (h : zigzag m = zigzag n) : m = n := by
  unfold zigzag at h
  split at h <;> split at h <;> omega

/-- The digit vector of a dimension: the derived quantity, before it is packed
into a word. It is a function of the meaning alone. -/
def digits (d : Dim) : Fin 7 → ℕ := fun i => zigzag (d i)

/-- **The derivation is faithful.** On the representable box `[-4,4]⁷` the
derived digit vector determines the dimension it came from, so storing only the
meaning and deriving the bits loses nothing. -/
theorem digits_injOn {d e : Dim} (hd : ∀ i, -4 ≤ d i ∧ d i ≤ 4)
    (he : ∀ i, -4 ≤ e i ∧ e i ≤ 4) (h : digits d = digits e) : d = e := by
  funext i
  exact zigzag_injOn (hd i).1 (hd i).2 (he i).1 (he i).2 (congrFun h i)

/-- Seven base-9 digits: `9⁷ = 4 782 969` distinct carriers. -/
theorem carrier_card : Fintype.card (Fin 7 → Fin 9) = 4782969 := by simp

/-- The carrier fits inside a 24-bit word. -/
theorem carrier_fits_24_bits : Fintype.card (Fin 7 → Fin 9) < 2 ^ 24 := by
  rw [carrier_card]; norm_num

/-- Explicitly: the carrier embeds in the 24-bit words. -/
theorem carrier_embeds : Nonempty ((Fin 7 → Fin 9) ↪ Fin (2 ^ 24)) := by
  refine ⟨(finFunctionFinEquiv.toEmbedding).trans (Fin.castLEEmb ?_)⟩
  norm_num

/-- The slack: `11 994 247` of the sixteen-odd million words are unused. -/
theorem carrier_slack : 2 ^ 24 - Fintype.card (Fin 7 → Fin 9) = 11994247 := by
  rw [carrier_card]; norm_num

/-- **An eighth dimension would not fit.** `9⁸ > 2²⁴`, so the seven SI base
dimensions are as many as a 24-bit word carries at this radius. -/
theorem carrier_box_maximal_in_rank : 2 ^ 24 < Fintype.card (Fin 8 → Fin 9) := by
  simp

/-- **A ninth exponent value would not fit either.** `11⁷ > 2²⁴`, so widening
the box from `[-4,4]` to `[-5,5]` overflows the word. -/
theorem carrier_box_maximal_in_radius : 2 ^ 24 < Fintype.card (Fin 7 → Fin 11) := by
  simp

/-! ## 4. The 16-state column codec -/

/-- The MOG column label of a 4-bit column state `v` (bit `r` is row `r`): the
XOR of the row labels of the rows that are set. -/
def colLabel (v : ℕ) : ℕ :=
  (List.range 4).foldl (fun acc r => if (v >>> r) % 2 = 1 then acc ^^^ r else acc) 0

/-- The label map agrees with the tabulated column labels. -/
theorem colLabel_table :
    (List.range 16).map colLabel = [0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0] := by
  decide

/-- The label map is `GF(2)`-linear on the sixteen column states. -/
theorem colLabel_xor (a b : ℕ) (ha : a < 16) (hb : b < 16) :
    colLabel (a ^^^ b) = colLabel a ^^^ colLabel b := by
  interval_cases a <;> interval_cases b <;> decide

/-- The states carrying a given label. -/
def fibre (l : ℕ) : List ℕ := (List.range 16).filter fun s => colLabel s = l

/-- Each of the four labels has exactly four preimages: the label map is a
4-to-1 fibration of the sixteen column states, which is what makes the pair
(label, fibre index) a lossless recoding of a column. -/
theorem fibre_card (l : ℕ) (hl : l < 4) : (fibre l).length = 4 := by
  interval_cases l <;> decide

/-- The four fibres are disjoint and exhaust the sixteen states. -/
theorem fibres_partition :
    ((List.range 4).flatMap fibre).length = 16 ∧
      ((List.range 4).flatMap fibre).Perm (List.range 16) :=
  ⟨by decide, by decide⟩

end GLM.DimensionCarrier
