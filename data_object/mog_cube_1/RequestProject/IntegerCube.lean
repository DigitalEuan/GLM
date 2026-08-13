import Mathlib
import RequestProject.MeasuredWords
import RequestProject.MeasuredSentences
import RequestProject.CubeTax

/-!
# The integer companion: carrying the *magnitude*, not just the parity

`MeasuredWords` put a word's dimension on the cube with one **bit** per face and
composed by XOR.  `MeasuredSentences` then measured the damage: of the 1758
sentences the cube accepted, **1402 were false** — precision ≈ 20% — because XOR
sees each exponent only mod 2.

This file implements the fix asked for in `test_5_three_ideas.py` /
`test_6_precision_wall.py`, but *inside* the cube rather than beside it.

**The encoding.**  Each face keeps all four of its cells, and the four cells of
face `j` are the four binary digits of the exponent of dimension `j`, written in
two's complement.  A face therefore holds an integer in `[-8, 7]`
(`intOfCol_range`), not a parity bit: `encG` (`Dim → Grid`) is a genuine integer
record on the same 24 cells.

**The composition.**  `addCol` is a ripple-carry adder wired across the four
cells of a face, and `addG` runs it on all six faces at once.  It is exactly
addition of the stored integers (`addCol_spec`), so multiplying two quantities
is adding their words (`encG_add`) — deterministic, and reversible by
`subG` (`subG_addG`).

**Why this is not XOR.**  XOR *is* the same circuit with the carry wire cut
(`xor_is_add_without_carry`: they agree exactly when no carry is generated).
The carry is precisely the information XOR throws away: `gxorCol c c = 0` always
(`xor_forgets`), while `addCol c c` doubles (`add_remembers`).

**What it buys, counted.**  Re-running the `MeasuredSentences` experiment with
the integer cube: the accepted set is *exactly* the set of true sentences
(`integer_accepts_eq_equations`), i.e. 356 accepted, **0 false positives**
(`integer_false_positive_count`), against 1402 for the parity cube.  Precision
goes from `356/1758` to `356/356`.

**What it costs, honestly.**  An integer word is essentially never a codeword:
*none* of the 156 phrases lands in the code (`phrase_codeword_count`), so the
free-storage property of the parity encoding is lost outright; what survives is
the bound `4·Q` on returning any word to the code (`encG_tax_le_four`).

**Where it still fails.**  The window is finite, so exponents differing by 16
collide (`wrap_blindness_witness`), and no encoding into 24 cells can avoid
some collision (`no_faithful_encoding`).  The gain is that the blind spot moved
from "differs by 2" to "differs by 16" — from inside the vocabulary to far
outside it.
-/

namespace IntegerCube

open CubeMOG MeasuredWords

set_option maxRecDepth 100000

/-! ## 1. A face is a two's-complement integer -/

/-- The four cells of a face, read as a 4-bit word (cell `i` is the `2^i` digit). -/
def colBV (c : Col) : BitVec 4 :=
  (if c 0 then 1 else 0) ||| (if c 1 then 2 else 0) |||
  (if c 2 then 4 else 0) ||| (if c 3 then 8 else 0)

/-- The four cells carrying a 4-bit word. -/
def bvCol (x : BitVec 4) : Col := fun i => x.getLsbD (i : Nat)

theorem bvCol_colBV : ∀ c : Col, bvCol (colBV c) = c := by decide
theorem colBV_bvCol : ∀ x : BitVec 4, colBV (bvCol x) = x := by decide

/-- **The integer a face holds**: its cells read in two's complement. -/
def intOfCol (c : Col) : ℤ := (colBV c).toInt

/-- **The face holding a given integer.** -/
def colOfInt (n : ℤ) : Col := bvCol (BitVec.ofInt 4 n)

/-- A face holds an integer in the window `[-8, 7]`. -/
theorem intOfCol_range (c : Col) : -8 ≤ intOfCol c ∧ intOfCol c ≤ 7 := by
  revert c; decide

theorem intOfCol_colOfInt (n : ℤ) : intOfCol (colOfInt n) = Int.bmod n 16 := by
  rw [intOfCol, colOfInt, colBV_bvCol, BitVec.toInt_ofInt]

theorem colOfInt_intOfCol : ∀ c : Col, colOfInt (intOfCol c) = c := by decide

/-- The window in which the record is exact. -/
def InWindow (n : ℤ) : Prop := -8 ≤ n ∧ n ≤ 7

theorem bmod_self_of_window {n : ℤ} (h : InWindow n) : Int.bmod n 16 = n := by
  obtain ⟨h1, h2⟩ := h
  simp only [Int.bmod]
  omega

/-- **The record is exact on the window**: an exponent in `[-8,7]` is read back
unchanged. -/
theorem intOfCol_colOfInt_of_window {n : ℤ} (h : InWindow n) : intOfCol (colOfInt n) = n := by
  rw [intOfCol_colOfInt, bmod_self_of_window h]

/-- Two faces are equal exactly when they hold the same residue mod 16. -/
theorem colOfInt_eq_iff (m n : ℤ) : colOfInt m = colOfInt n ↔ Int.bmod m 16 = Int.bmod n 16 := by
  constructor
  · intro h
    have := congrArg intOfCol h
    rwa [intOfCol_colOfInt, intOfCol_colOfInt] at this
  · intro h
    have : intOfCol (colOfInt m) = intOfCol (colOfInt n) := by
      rw [intOfCol_colOfInt, intOfCol_colOfInt, h]
    have h2 := congrArg colOfInt this
    rwa [colOfInt_intOfCol, colOfInt_intOfCol] at h2

/-! ## 2. Composition is addition with a carry, not XOR -/

/-- The carry-in chain of the ripple adder, cell by cell. -/
def carryAt (c d : Col) : Nat → Bool
  | 0 => false
  | (n + 1) =>
      if h : n < 4 then
        let k := carryAt c d n
        (c ⟨n, h⟩ && d ⟨n, h⟩) || (k && (c ⟨n, h⟩ || d ⟨n, h⟩))
      else false

/-- **The face adder**: a ripple-carry adder wired across the four cells of a
face.  The sum bit is the three-way XOR, the carry bit is the majority. -/
def addCol (c d : Col) : Col := fun i =>
  xor (c i) (xor (d i) (carryAt c d (i : Nat)))

/-- Cellwise XOR of two faces (the same circuit with the carry wire cut). -/
def gxorCol (c d : Col) : Col := fun i => xor (c i) (d i)

/-- **The adder really adds**: on the stored 4-bit integers it is binary
addition. -/
theorem addCol_spec : ∀ c d : Col, colBV (addCol c d) = colBV c + colBV d := by decide

/-- **XOR is the adder with the carry cut.**  The two agree exactly on the
inputs that generate no carry at all. -/
theorem xor_is_add_without_carry :
    ∀ c d : Col, (addCol c d = gxorCol c d ↔ ∀ i : Fin 4, carryAt c d (i : Nat) = false) := by
  decide

/-- XOR forgets: every face is its own inverse, so a repeated factor vanishes. -/
theorem xor_forgets (c : Col) : gxorCol c c = (fun _ => false) := by
  funext i; simp [gxorCol]

/-- The adder remembers: repeating a factor doubles it. -/
theorem add_remembers : ∃ c : Col, gxorCol c c = (fun _ => false) ∧ addCol c c ≠ (fun _ => false) := by
  refine ⟨![true, false, false, false], ?_, ?_⟩ <;> decide

/-- Face subtraction: the adder run backwards. -/
def subCol (c d : Col) : Col := bvCol (colBV c - colBV d)

/-- **Composition is reversible**: the second factor can be divided out again. -/
theorem subCol_addCol : ∀ c d : Col, subCol (addCol c d) d = c := by decide

/-! ## 3. The cube as an integer record -/

/-- **A measurable word as an integer record on the cube**: face `j` carries the
exponent of dimension `j` in two's complement. -/
def encG (v : Dim) : Grid := fun j => colOfInt (v j)

/-- Reading the dimension back off the cube. -/
def decG (g : Grid) : Dim := fun j => intOfCol (g j)

/-- Composition of words: the six face adders run in parallel. -/
def addG (g h : Grid) : Grid := fun j => addCol (g j) (h j)

/-- Decomposition of words. -/
def subG (g h : Grid) : Grid := fun j => subCol (g j) (h j)

/-- A dimension vector lies in the window when every exponent does. -/
def DimInWindow (v : Dim) : Prop := ∀ j, InWindow (v j)

/-- **Reading back is exact on the window.** -/
theorem decG_encG {v : Dim} (h : DimInWindow v) : decG (encG v) = v := by
  funext j
  exact intOfCol_colOfInt_of_window (h j)

/-- **Multiplying quantities is adding their cubes** — with carries, so nothing
is lost. -/
theorem encG_add (u v : Dim) : addG (encG u) (encG v) = encG (u + v) := by
  funext j
  have h : colBV (addCol (colOfInt (u j)) (colOfInt (v j)))
      = colBV (colOfInt ((u + v) j)) := by
    rw [addCol_spec, colOfInt, colOfInt, colOfInt, colBV_bvCol, colBV_bvCol, colBV_bvCol]
    exact (BitVec.ofInt_add (u j) (v j)).symm
  have := congrArg bvCol h
  rwa [bvCol_colBV, bvCol_colBV] at this

/-- Composition is reversible on the whole cube. -/
theorem subG_addG (g h : Grid) : subG (addG g h) h = g := by
  funext j i
  exact congrFun (subCol_addCol (g j) (h j)) i

/-- **What the integer cube decides**: two words are equal iff every exponent
agrees mod 16. -/
theorem encG_eq_iff (u v : Dim) : encG u = encG v ↔ ∀ j, Int.bmod (u j) 16 = Int.bmod (v j) 16 := by
  constructor
  · intro h j
    exact (colOfInt_eq_iff _ _).mp (congrFun h j)
  · intro h
    funext j
    exact (colOfInt_eq_iff _ _).mpr (h j)

/-- **No false positives on the window.**  Inside `[-8,7]` the cube's verdict is
the truth: it accepts exactly the dimensionally correct equations. -/
theorem encG_eq_iff_of_window {u v : Dim} (hu : DimInWindow u) (hv : DimInWindow v) :
    encG u = encG v ↔ u = v := by
  rw [encG_eq_iff]
  constructor
  · intro h
    funext j
    have := h j
    rwa [bmod_self_of_window (hu j), bmod_self_of_window (hv j)] at this
  · intro h j
    rw [h]

/-! ## 4. Re-running the precision experiment -/

open MeasuredSentences

/-- The sentences the *integer* cube accepts. -/
def integerAccepts : List (Phrase × Phrase) :=
  candidates.filter fun pq => decide (encG pq.1.2 = encG pq.2.2)

/-- Every phrase in the vocabulary is inside the window. -/
theorem phrases_in_window :
    phrases.all (fun p => decide (∀ j, -8 ≤ p.2 j ∧ p.2 j ≤ 7)) = true := by
  native_decide

/-- **The wall is gone.**  The integer cube accepts *exactly* the 356 true
sentences — the same list, not merely the same count. -/
theorem integer_accepts_eq_equations : integerAccepts = equations := by native_decide

theorem integer_accepts_count : integerAccepts.length = 356 := by
  rw [integer_accepts_eq_equations]; exact equations_count

/-- **Zero false positives**, against 1402 for the parity cube
(`MeasuredSentences.substrate_false_positive_count`). -/
theorem integer_false_positive_count :
    (integerAccepts.filter fun pq => decide (pq.1.2 ≠ pq.2.2)).length = 0 := by
  native_decide

/-- **Full recall too**: no true sentence is rejected. -/
theorem integer_accepts_all_true (e : Phrase × Phrase) (he : e ∈ equations) :
    encG e.1.2 = encG e.2.2 := by
  rw [equations_true e he]

/-- The concrete pair the parity cube could not separate is now separated. -/
theorem length_vs_acceleration_separated : encG length ≠ encG acceleration := by
  rw [Ne, encG_eq_iff]
  intro h
  have := h 2
  revert this
  decide

/-- `E = mc⁴`, accepted by the parity cube although false, is now rejected. -/
theorem rejects_energy_eq_mass_velocity_fourth :
    encG energy ≠ encG (mass + velocity + velocity + velocity + velocity) := by
  rw [Ne, encG_eq_iff]
  intro h
  have := h 0
  revert this
  decide

/-- …while the true equations are still accepted. -/
theorem integer_accepts_true_equations :
    encG energy = encG (mass + velocity + velocity) ∧
    encG force = encG (mass + acceleration) ∧
    encG action = encG (energy + time) ∧
    encG momentum = encG (mass + velocity) ∧
    encG power = encG (energy - time) ∧
    encG charge = encG (current + time) := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
    · rw [encG_eq_iff]
      decide

/-! ## 5. What it costs -/

/-- **The price of exactness.**  Not one of the 156 phrases encodes to a lawful
codeword: unlike the parity encoding — where every word was free to hold — an
integer record always sits off the code. -/
theorem phrase_codeword_count :
    (phrases.filter fun p => IsMogB (encG p.2)).length = 0 := by native_decide

/-- The dimensionless record is the one exception in principle: it is the zero
grid, which is a codeword. -/
theorem encG_zero_isMog : IsMog (encG 0) := by
  have h : encG (0 : Dim) = (0 : Grid) := by decide
  rw [h]
  exact IsMog_zero

/-- What survives is the repair bound: any integer record is returned to the
code for at most `4·Q`. -/
theorem encG_tax_le_four (v : Dim) :
    ∃ e, IsMog (gxor (encG v) e) ∧ CubeTax.taxCells (wtG e) ≤ 4 * GolayHex.Q :=
  CubeTax.tax_le_four_Q _

/-! ## 6. The remaining blind spot, stated honestly -/

/-- **The window wraps.**  Exponents differing by 16 are still confused — the
blind spot has moved from `2` to `16`, not disappeared. -/
theorem wrap_blindness_witness :
    (![16, 0, 0, 0, 0, 0] : Dim) ≠ (![0, 0, 0, 0, 0, 0] : Dim) ∧
      encG ![16, 0, 0, 0, 0, 0] = encG ![0, 0, 0, 0, 0, 0] := by
  constructor
  · intro h
    have := congrFun h 0
    revert this
    decide
  · rw [encG_eq_iff]
    decide

/-- **And it must.**  There are infinitely many dimension vectors and only
`2^24` cubes, so *no* encoding into the surface is faithful on all of them:
some window is unavoidable.  (Contrast `MeasuredWords.xor_encoding_is_mod_two`,
where the blind spot is forced to be as small as `2`.) -/
theorem no_faithful_encoding (f : Dim → Grid) : ¬ Function.Injective f := by
  intro hf
  have : Finite Dim := Finite.of_injective f hf
  exact not_finite Dim

end IntegerCube
