import Mathlib
import RequestProject.IntegerCube
import RequestProject.ClauseStore

/-!
# Two records, and a window sixteen times wider

Report 2 §7.4:

> **The integer window is finite.**  Exponents differing by 16 still collide,
> and provably some collision is unavoidable on 24 cells.

The unavoidability stands — it is a counting argument, and `no_faithful_pair`
below repeats it for any number of cubes.  What was *not* forced is the size of
the window, and the role discipline of `ClauseStore.lean` says what to do about
it: a dimension is not obliged to live on one record.  Give it two — a high
record and a low record, addressed as different dimension records on the same
surface — and each exponent becomes an eight-bit two's-complement number.

## What is proved

* `decP_encP` — a pair of records reads back exactly on `[-128, 127]`, against
  `[-8, 7]` for one record.
* `encP_add` — multiplying quantities is still adding words: the ripple carry
  now crosses from the low record into the high record, and the sum of two
  dimension vectors is the sum of their pairs.
* `sixteen_no_longer_collides` — the exact witness of
  `IntegerCube.wrap_blindness_witness`, which one record confuses, is
  distinguished by two.
* `pair_window_is_256` — the blind spot has moved from 16 to 256, and is stated
  exactly: two vectors have the same pair precisely when their exponents agree
  mod 256.
* `no_faithful_pair` — and it has *only* moved: no encoding of the dimension
  vectors into any finite record is faithful, for two records as for one.
* `records_are_separated` — the two records are distinguishable on the surface
  by the same distance-8 guarantee as everything else, so the pair can be stored
  and repaired like a single record.
-/

namespace WideInteger

open CubeMOG MeasuredWords IntegerCube

set_option maxRecDepth 100000

/-! ## 1. Eight bits across two faces -/

/-- The eight-bit number held by a high face and a low face. -/
def unpack (hi lo : Col) : BitVec 8 := (colBV hi) ++ (colBV lo)

/-- Splitting an eight-bit number into a high face and a low face. -/
def pack (y : BitVec 8) : Col × Col := (bvCol (y.extractLsb' 4 4), bvCol (y.setWidth 4))

theorem unpack_pack (y : BitVec 8) : unpack (pack y).1 (pack y).2 = y := by
  revert y; decide

theorem pack_unpack (hi lo : Col) : pack (unpack hi lo) = (hi, lo) := by
  revert hi lo; decide

/-! ## 2. A dimension vector on two records -/

/-- A pair of dimension records: a high cube and a low cube, 48 cells. -/
abbrev Pair := Grid × Grid

/-- **The encoding.**  Each exponent is written in eight-bit two's complement,
its top nibble on the high record and its bottom nibble on the low record. -/
def encP (v : Dim) : Pair :=
  (fun j => (pack (BitVec.ofInt 8 (v j))).1, fun j => (pack (BitVec.ofInt 8 (v j))).2)

/-- Reading a pair back. -/
def decP (p : Pair) : Dim := fun j => (unpack (p.1 j) (p.2 j)).toInt

/-- The window of the pair. -/
def InWindow8 (n : ℤ) : Prop := -128 ≤ n ∧ n ≤ 127

def DimInWindow8 (v : Dim) : Prop := ∀ j, InWindow8 (v j)

theorem bmod_self_of_window8 {n : ℤ} (h : InWindow8 n) : Int.bmod n 256 = n := by
  obtain ⟨h1, h2⟩ := h
  simp only [Int.bmod]
  omega

theorem decP_encP_apply (v : Dim) (j : Fin 6) : decP (encP v) j = Int.bmod (v j) 256 := by
  simp only [decP, encP, unpack_pack]
  rw [BitVec.toInt_ofInt]

/-- **The pair is exact on `[-128, 127]`** — sixteen times the window of a
single record. -/
theorem decP_encP {v : Dim} (h : DimInWindow8 v) : decP (encP v) = v := by
  funext j
  rw [decP_encP_apply, bmod_self_of_window8 (h j)]

/-! ## 3. Composition is still addition -/

/-- Addition on a pair: an eight-bit ripple carry whose carry crosses from the
low record into the high record. -/
def addP (p q : Pair) : Pair :=
  (fun j => (pack (unpack (p.1 j) (p.2 j) + unpack (q.1 j) (q.2 j))).1,
   fun j => (pack (unpack (p.1 j) (p.2 j) + unpack (q.1 j) (q.2 j))).2)

/-- **Multiplying quantities is adding pairs.** -/
theorem encP_add (u v : Dim) : addP (encP u) (encP v) = encP (u + v) := by
  refine Prod.ext ?_ ?_ <;> funext j <;>
    simp only [addP, encP, unpack_pack, ← BitVec.ofInt_add, Pi.add_apply]

/-- Reading back a sum: the pair holds the sum of the exponents, mod 256. -/
theorem decP_addP (p q : Pair) (j : Fin 6) :
    decP (addP p q) j = Int.bmod (decP p j + decP q j) 256 := by
  simp only [decP, addP, unpack_pack]
  rw [BitVec.toInt_add]

/-! ## 4. What the second record buys, and what it does not -/

/-- Two vectors have the same pair exactly when their exponents agree mod
256. -/
theorem encP_eq_iff (u v : Dim) :
    encP u = encP v ↔ ∀ j, Int.bmod (u j) 256 = Int.bmod (v j) 256 := by
  constructor
  · intro h j
    have := congrArg (fun p => decP p j) h
    simpa [decP_encP_apply] using this
  · intro h
    have hj : ∀ j, BitVec.ofInt 8 (u j) = BitVec.ofInt 8 (v j) := by
      intro j
      have h1 : (BitVec.ofInt 8 (u j)).toInt = (BitVec.ofInt 8 (v j)).toInt := by
        rw [BitVec.toInt_ofInt, BitVec.toInt_ofInt]
        simpa using h j
      exact BitVec.eq_of_toInt_eq h1
    refine Prod.ext ?_ ?_ <;> funext j <;> simp only [encP, hj j]

/-- **The blind spot has moved from 16 to 256**: the very witness that one
record confuses is separated by two. -/
theorem sixteen_no_longer_collides :
    encG ![16, 0, 0, 0, 0, 0] = encG ![0, 0, 0, 0, 0, 0] ∧
      encP ![16, 0, 0, 0, 0, 0] ≠ encP ![0, 0, 0, 0, 0, 0] := by
  refine ⟨IntegerCube.wrap_blindness_witness.2, ?_⟩
  intro h
  have := (encP_eq_iff _ _).mp h 0
  revert this
  decide

/-- …and it is exactly 256: that is where the pair starts to confuse. -/
theorem pair_window_is_256 :
    encP ![256, 0, 0, 0, 0, 0] = encP ![0, 0, 0, 0, 0, 0] := by
  refine (encP_eq_iff _ _).mpr fun j => ?_
  fin_cases j <;> decide

/-- **The counting argument survives the extra record.**  There are infinitely
many dimension vectors and only finitely many pairs, so no encoding into two
records — or into any number of them — is faithful.  The window can be widened,
never removed. -/
theorem no_faithful_pair (f : Dim → Pair) : ¬ Function.Injective f := by
  intro hf
  have : Finite Dim := Finite.of_injective f hf
  exact not_finite Dim

/-! ## 5. The two records live on the surface, and stay apart -/

/-- The high record and the low record of a dimension, as records of the
`ClauseStore` frame: same role, different addresses. -/
def hiRec (eL eM eT eI eΘ : Fin 4) : ClauseStore.Rec := ClauseStore.dimRec eL eM eT eI eΘ

def loRec (eL eM eT eI eΘ : Fin 4) : ClauseStore.Rec :=
  ⟨3, eL, ⟨4 * eM.val + eT.val, by omega⟩, ⟨4 * eI.val + eΘ.val, by omega⟩⟩

/-- **The two records of a pair never collide**, by the same distance-8
guarantee that protects clauses: a high record is never read as a low one. -/
theorem records_are_separated (a b c d e a' b' c' d' e' : Fin 4) :
    8 ≤ SentenceCode.dist3 (ClauseStore.encode (hiRec a b c d e))
      (ClauseStore.encode (loRec a' b' c' d' e')) :=
  ClauseStore.roles_are_separated (by simp [hiRec, loRec, ClauseStore.dimRec])

end WideInteger
