/-
# Formal companion to the Geometric Language Machine paper

This file formalises the small number of *structural* claims that the GLM paper
(`glm/glm_paper.py`) states as propositions rather than as measurements.  The
measured facts (Golay weight enumerator, Leech shell decomposition, library
statistics, ...) are verified computationally by the Python artefacts; what is
proved here is the part of the argument that is a theorem:

* §1  **The mod-2 ceiling** (paper Proposition 1 and its corollaries).  Any
  encoder whose composition law is XOR is blind to the difference between two
  dimension vectors that agree modulo 2; in particular it cannot separate
  `E = m c^2` from `E = m c^4`, while the exact `(Z^7, +)` comparison does.
  Sharper: no such encoder is injective at all, so a bit pattern cannot be the
  primary object of the system.  That is why the GLM makes the meaning primary
  and derives the bits from it (paper §5.2), rather than carrying an integer
  vector alongside a bit pattern.

* §2  **The derived carrier** (paper §3.2 and §5.2).  The digit vector derived
  from a meaning determines that meaning on the representable box, and exponent
  vectors in `[-4,4]^7` are in bijection with `Fin 9 → Fin 7` many digits, of
  which there are `9^7 = 4782969 < 2^24`, so the carrier embeds injectively in
  a 24-bit word.

* §3  **The 16-state column codec** (paper §3.1): the four MOG column labels
  each have exactly four preimages among the sixteen column states.

* §4  **Winding integrality** (paper Proposition 2, §9.3).  For any closed walk
  carrying a `ZMod 4`-valued invariant, the sum of the integer lifts of the
  steps is divisible by 4, so the winding number is an integer.

* §5  **The Schrödinger relations** (paper §8.2).  The signed-permutation
  operators of the extraspecial group `2^(1+2n)` satisfy
  `X_b Y_a = (-1)^{⟨a,b⟩} Y_a X_b`, and in particular anticommute when
  `a = b = e_i`; that sign is the extraspecial commutator `[x_i, y_i] = z`.

* §6  The orbit–stabiliser arithmetic behind `|M_24| = 244,823,040`
  (paper §8.1) and the Griess/Leech **dimension ledger** of paper §10.

No `sorry`, no new axioms.
-/

import Mathlib

set_option autoImplicit false
set_option linter.style.longLine false

namespace GLM

/-! ## §1  The mod-2 ceiling -/

/-- A physical dimension is an exponent vector in `Z^7`
(length, mass, time, current, temperature, amount, luminous intensity). -/
abbrev Dim : Type := Fin 7 → ℤ

/--
**The mod-2 ceiling.**  Let `f` be any encoder of dimension vectors into an
abelian group `M` which turns composition of quantities (addition of exponent
vectors) into the group operation of `M`, and in which every element is its own
inverse — the defining property of XOR on bit vectors, `F_2`-vector spaces
being exactly the abelian groups of exponent 2.  Then `f` cannot see any even
shift of its argument.
-/
theorem xor_blind {M : Type*} [AddCommGroup M] (hM : ∀ m : M, m + m = 0)
    (f : Dim →+ M) (d u : Dim) : f (d + (2 : ℤ) • u) = f d := by
  have h : f ((2 : ℤ) • u) = 0 := by
    rw [two_zsmul, map_add, hM]
  rw [map_add, h, add_zero]

/-- The dimension of energy, `L^2 M T^-2`. -/
def energyDim : Dim := ![2, 1, -2, 0, 0, 0, 0]

/-- The dimension of `m c^4`, i.e. `L^4 M T^-4`. -/
def mc4Dim : Dim := ![4, 1, -4, 0, 0, 0, 0]

/-- The even shift separating `m c^2` from `m c^4`. -/
def mc4Shift : Dim := ![1, 0, -1, 0, 0, 0, 0]

/-- `m c^4` differs from energy by an even shift. -/
theorem mc4_eq : mc4Dim = energyDim + (2 : ℤ) • mc4Shift := by
  funext i
  fin_cases i <;> simp [mc4Dim, energyDim, mc4Shift]

/-- Exactly over `Z^7`, `m c^4` is *not* energy: the exact checker rejects it. -/
theorem mc4_ne : mc4Dim ≠ energyDim := by
  intro h
  have := congrFun h 0
  simp [mc4Dim, energyDim] at this

/--
**Corollary 2 (paper §5.3).**  No XOR-composing encoder can reject `E = m c^4`:
it assigns `m c^4` and energy the same code, although the two dimensions differ.
-/
theorem mc4_indistinguishable_under_xor {M : Type*} [AddCommGroup M]
    (hM : ∀ m : M, m + m = 0) (f : Dim →+ M) :
    f mc4Dim = f energyDim ∧ mc4Dim ≠ energyDim :=
  ⟨by rw [mc4_eq]; exact xor_blind hM f _ _, mc4_ne⟩

/--
The ceiling is exactly a mod-2 phenomenon: two dimension vectors have the same
image under *every* XOR-composing encoder iff they agree componentwise mod 2.
Here the universal such encoder is reduction into `Fin 7 → ZMod 2`.
-/
theorem xor_universal_kernel (d e : Dim) :
    (∃ u : Dim, e = d + (2 : ℤ) • u) ↔ ∀ i, (e i : ZMod 2) = (d i : ZMod 2) := by
  constructor
  · rintro ⟨u, rfl⟩ i
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]
    push_cast
    rw [show (2 : ZMod 2) = 0 by decide]
    ring
  · intro h
    refine ⟨fun i => (e i - d i) / 2, ?_⟩
    funext i
    have h2 : (2 : ℤ) ∣ (e i - d i) := by
      have := h i
      have : ((e i - d i : ℤ) : ZMod 2) = 0 := by push_cast; rw [this]; ring
      exact (ZMod.intCast_zmod_eq_zero_iff_dvd _ 2).mp this
    obtain ⟨k, hk⟩ := h2
    simp only [Pi.add_apply, Pi.smul_apply, smul_eq_mul]
    rw [hk]
    omega

/--
**Corollary 1 (no primary bit pattern).**  An encoder whose composition law is
XOR is never injective: it identifies `d` with `d + 2u` for every `u`.  This is
the theorem behind the architecture of paper §5.2 — a bit pattern cannot be the
object that carries meaning, so meaning is primary and the bits are derived
from it.
-/
theorem no_injective_additive_into_char_two {M : Type*} [AddCommGroup M]
    (hM : ∀ m : M, m + m = 0) (f : Dim →+ M) : ¬ Function.Injective f := by
  intro hinj
  have h := xor_blind hM f 0 (fun _ => 1)
  rw [zero_add] at h
  have h0 : ((2 : ℤ) • (fun _ => 1 : Dim)) = (0 : Dim) := hinj h
  have h1 := congrFun h0 0
  simp at h1

/-- The concrete case the GLM cares about: no XOR-composing encoder into
24-bit words separates all dimension vectors, whatever the encoding. -/
theorem f2_carrier_cannot_be_primary (f : Dim →+ (Fin 24 → ZMod 2)) :
    ¬ Function.Injective f :=
  no_injective_additive_into_char_two
    (fun m => by funext i; exact CharTwo.add_self_eq_zero (m i)) f

/-! ## §2  Capacity of the base-9 dimension carrier -/

/-- The zigzag digit map `[-4,4] → {0,…,8}` used by the carrier:
`0 ↦ 0`, `1 ↦ 1`, `-1 ↦ 2`, `2 ↦ 3`, `-2 ↦ 4`, … -/
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

/-- The digit vector of a dimension: the derived quantity of paper §5.2,
before it is packed into a word.  It is a function of the meaning alone. -/
def digits (d : Dim) : Fin 7 → ℕ := fun i => zigzag (d i)

/-- **The derivation is faithful.**  On the representable box `[-4,4]^7` the
derived digit vector determines the meaning it came from, so nothing is lost
by storing only the meaning and deriving the bits: `decode ∘ encode = id`. -/
theorem digits_injOn {d e : Dim} (hd : ∀ i, -4 ≤ d i ∧ d i ≤ 4)
    (he : ∀ i, -4 ≤ e i ∧ e i ≤ 4) (h : digits d = digits e) : d = e := by
  funext i
  exact zigzag_injOn (hd i).1 (hd i).2 (he i).1 (he i).2 (congrFun h i)

/-- Seven base-9 digits are carried by `9^7 = 4782969` distinct words. -/
theorem carrier_card : Fintype.card (Fin 7 → Fin 9) = 4782969 := by
  simp

/-- The carrier fits inside a 24-bit word, with room to spare. -/
theorem carrier_fits_24_bits : Fintype.card (Fin 7 → Fin 9) < 2 ^ 24 := by
  rw [carrier_card]; norm_num

/-- Explicitly, the carrier's injection into 24-bit words:
`Fin 7 → Fin 9` embeds in `Fin (2^24)`. -/
theorem carrier_embeds : Nonempty ((Fin 7 → Fin 9) ↪ Fin (2 ^ 24)) := by
  refine ⟨(finFunctionFinEquiv.toEmbedding).trans (Fin.castLEEmb ?_)⟩
  norm_num

/-! ## §3  The 16-state column codec -/

/-- The MOG column label of a 4-bit column state `v` (bit `r` = row `r`): the
XOR of the row labels `0, 1, w, w^2` of the rows that are set, written here as
the XOR of the indices of the set bits (`glm_substrate.py`, `_column_label`). -/
def colLabel (v : ℕ) : ℕ :=
  (List.range 4).foldl (fun acc r => if (v >>> r) % 2 = 1 then acc ^^^ r else acc) 0

/-- The label map agrees with the tabulated `MOG.COLUMN_LABEL`. -/
theorem colLabel_table :
    (List.range 16).map colLabel = [0,0,1,1,2,2,3,3,3,3,2,2,1,1,0,0] := by
  decide

/-- The label map is `GF(2)`-linear on the sixteen column states. -/
theorem colLabel_xor (a b : ℕ) (ha : a < 16) (hb : b < 16) :
    colLabel (a ^^^ b) = colLabel a ^^^ colLabel b := by
  interval_cases a <;> interval_cases b <;> decide

/-- The states carrying a given label. -/
def fibre (l : ℕ) : List ℕ := (List.range 16).filter fun s => colLabel s = l

/-- Every one of the four labels has exactly four preimages: the label map is a
4-to-1 fibration of the sixteen column states, which is what makes the pair
(label, fibre index) a lossless recoding of a column. -/
theorem fibre_card (l : ℕ) (hl : l < 4) : (fibre l).length = 4 := by
  interval_cases l <;> decide

/-- The four fibres are disjoint and exhaust the sixteen states. -/
theorem fibres_partition :
    ((List.range 4).flatMap fibre).length = 16 ∧
      ((List.range 4).flatMap fibre).Perm (List.range 16) := by
  refine ⟨by decide, by decide⟩

/-! ## §4  Winding integrality (paper Proposition 2) -/

/--
**Winding integrality.**  Let `u : ℕ → ZMod 4` be the versor invariant along a
walk `w_0, …, w_n` which is *closed*, `u n = u 0`, and let `L` be any lift of
`ZMod 4` to the integers (the paper uses the representatives `{-1,0,1,2}`; all
that matters is that `L x` reduces to `x`).  Then the sum of the lifted steps
is divisible by `4`, so `winding = (Σ lifted steps) / 4` is an integer.
-/
theorem winding_integral (n : ℕ) (u : ℕ → ZMod 4) (hclosed : u n = u 0)
    (L : ZMod 4 → ℤ) (hL : ∀ x, ((L x : ℤ) : ZMod 4) = x) :
    (4 : ℤ) ∣ ∑ i ∈ Finset.range n, L (u (i + 1) - u i) := by
  have hcast : ((∑ i ∈ Finset.range n, L (u (i + 1) - u i) : ℤ) : ZMod 4) = 0 := by
    push_cast
    rw [Finset.sum_congr rfl (fun i _ => hL (u (i + 1) - u i))]
    rw [Finset.sum_range_sub (f := u)]
    rw [hclosed, sub_self]
  exact_mod_cast (ZMod.intCast_zmod_eq_zero_iff_dvd _ 4).mp hcast

/-- The concrete lift used by `glm_geometry.py`: representatives `{-1,0,1,2}`
of `ZMod 4`, i.e. the step is reported as the smallest-magnitude turn. -/
def liftStep (x : ZMod 4) : ℤ := if x.val ≤ 2 then (x.val : ℤ) else (x.val : ℤ) - 4

/-- `liftStep` really is a lift. -/
theorem liftStep_spec (x : ZMod 4) : ((liftStep x : ℤ) : ZMod 4) = x := by
  revert x; decide

/-- The paper's statement: with the concrete lift, closed walks wind by an
integer number of full turns. -/
theorem winding_integral_liftStep (n : ℕ) (u : ℕ → ZMod 4) (hclosed : u n = u 0) :
    (4 : ℤ) ∣ ∑ i ∈ Finset.range n, liftStep (u (i + 1) - u i) :=
  winding_integral n u hclosed liftStep liftStep_spec

/-! ## §5  The Schrödinger representation of `2^(1+2n)` (paper §8.2) -/

/-- Heisenberg coordinates: bit vectors of length `n`. -/
abbrev Bits (n : ℕ) : Type := Fin n → ZMod 2

/-- The `F_2` inner product `⟨a, k⟩`. -/
def dotp {n : ℕ} (a k : Bits n) : ZMod 2 := ∑ i, a i * k i

/-- The sign character of `F_2`. -/
def sgn (x : ZMod 2) : ℤ := if x = 0 then 1 else -1

theorem sgn_add (x y : ZMod 2) : sgn (x + y) = sgn x * sgn y := by
  revert x y; decide

theorem dotp_add_right {n : ℕ} (a k b : Bits n) :
    dotp a (k + b) = dotp a k + dotp a b := by
  simp [dotp, mul_add, Finset.sum_add_distrib]

/-- The shift operator `X_b : |k⟩ ↦ |k + b⟩`, acting on functions. -/
def shiftOp {n : ℕ} (b : Bits n) (f : Bits n → ℤ) : Bits n → ℤ := fun k => f (k + b)

/-- The sign operator `Y_a : |k⟩ ↦ (-1)^⟨a,k⟩ |k⟩`. -/
def signOp {n : ℕ} (a : Bits n) (f : Bits n → ℤ) : Bits n → ℤ :=
  fun k => sgn (dotp a k) * f k

/--
**The Schrödinger relation.**  Shift and sign operators commute up to the sign
`(-1)^⟨a,b⟩`; this is the defining commutation law of the extraspecial group
`2^(1+2n)` in its faithful `2^n`-dimensional representation (`n = 12`, so
`4096`, in the paper).
-/
theorem shift_sign_comm {n : ℕ} (a b : Bits n) (f : Bits n → ℤ) :
    shiftOp b (signOp a f) = fun k => sgn (dotp a b) * signOp a (shiftOp b f) k := by
  funext k
  simp only [shiftOp, signOp, dotp_add_right, sgn_add]
  ring

/-- On the diagonal `a = b = e_i` the sign is `-1`: the two generators
*anticommute*, which is the extraspecial commutator `[x_i, y_i] = z`. -/
theorem shift_sign_anticomm {n : ℕ} (i : Fin n) (f : Bits n → ℤ) :
    shiftOp (Pi.single i 1) (signOp (Pi.single i 1) f) =
      fun k => -signOp (Pi.single i 1) (shiftOp (Pi.single i 1) f) k := by
  have hd : dotp (Pi.single i (1 : ZMod 2)) (Pi.single i (1 : ZMod 2)) = 1 := by
    simp [dotp, Pi.single_apply, Finset.sum_ite_eq']
  rw [shift_sign_comm, hd]
  funext k
  simp [sgn]

/-- Distinct generators `x_i`, `y_j` with `i ≠ j` commute. -/
theorem shift_sign_comm_off_diag {n : ℕ} (i j : Fin n) (hij : i ≠ j) (f : Bits n → ℤ) :
    shiftOp (Pi.single j 1) (signOp (Pi.single i 1) f) =
      signOp (Pi.single i 1) (shiftOp (Pi.single j 1) f) := by
  have hd : dotp (Pi.single i (1 : ZMod 2)) (Pi.single j (1 : ZMod 2)) = 0 := by
    simp [dotp, Pi.single_apply, Finset.sum_ite_eq', Ne.symm hij]
  rw [shift_sign_comm, hd]
  funext k
  simp [sgn]

/-! ## §6  Arithmetic of the ledgers (paper §8.1 and §10) -/

/--
The orbit–stabiliser arithmetic of paper §8.1: the computed stabiliser chain of
`Aut(C)` has orbit lengths `24, 23, 22, 21, 20` on ordered 5-tuples and a
pointwise stabiliser of order 48, and the group is transitive on the 759
octads with octad stabiliser of order 322,560.
-/
theorem mathieu_order_arithmetic :
    24 * 23 * 22 * 21 * 20 * 48 = 244823040 ∧
    759 * 322560 = 244823040 := by
  refine ⟨by norm_num, by norm_num⟩

/--
The bookkeeping of paper §10, stated so that the arithmetic is checked rather
than asserted: the 196,560 minimal Leech vectors fall into 98,280 antipodal
lines; class C of the Griess construction is indexed by `24 × 4096`; the three
blocks together with the Virasoro/identity summand and the 299-dimensional
space `S²₀(R^24)` give the Griess algebra's 196,884 dimensions, which is also
the first nontrivial coefficient of `j`, split as `324 + 196,560`.
-/
theorem dimension_ledger :
    2 * 98280 = 196560 ∧
    552 + 48576 + 49152 = 98280 ∧
    24 * 4096 = 98304 ∧
    1 + 299 + 98280 + 98304 = 196884 ∧
    196884 = 324 + 196560 := by
  refine ⟨by norm_num, by norm_num, by norm_num, by norm_num, by norm_num⟩

end GLM
