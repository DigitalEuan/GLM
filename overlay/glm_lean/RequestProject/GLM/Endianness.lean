/-
# Bit order is a coordinate permutation, so reading a stored word backwards is an isometry

The migration audit of the repository's stored state turned up a frame
question that is easy to mistake for data corruption.  The `hexcolour`
addresses are stored as integers, and the obvious reading — coordinate `i` is
bit `i` — puts *none* of them on the Golay code.  Reading them the other way
round — coordinate `i` is bit `n - 1 - i`, i.e. most significant bit first —
puts *all* of them on the code.

This file isolates the mathematics behind that.  Reversing bit order is the
coordinate permutation `Fin.revPerm`, so everything already proved in
`RequestProject.GLM.Permutation` about coordinate permutations applies to it:

* `bitsMSB_eq_bitReverse_bitsLSB` — the two readings of one stored integer
  differ exactly by bit reversal, which is what makes this a frame question
  and not a data question;
* `bitReverse_involutive` — the two readings are symmetric; neither is
  privileged by the mathematics, only by the convention the data was written
  with;
* `hdist_bitReverse` — bit reversal preserves Hamming distance, hence weight;
* `nearest_bitReverse_iff` — nearest-codeword decoding therefore commutes with
  it, so a decoder may be wrapped in it without changing what it decodes to;
* `min_distance_bitReverse` — minimum distance `8` survives the reversal, so
  the reversed image of the Golay code is again a `[24, 12, 8]` code and the
  weight-`3` correction guarantee still holds in the reversed frame.

Together these say the audit's fix is legitimate: choosing the MSB-first
reading recovers the code without altering a single stored bit, and no
guarantee that held in one frame is lost in the other.

Nothing here is special to 24 coordinates or to the Golay code.
-/
import Mathlib
import RequestProject.GLM.Permutation

namespace GLM.Golay

open Finset

variable {n : ℕ}

/-! ## Bit reversal as a coordinate permutation -/

/-- Reverse the coordinate order of a bit pattern: the value at coordinate `i`
becomes the value at coordinate `n - 1 - i`.  This is exactly `permute` along
`Fin.revPerm`, so it inherits every property of a coordinate permutation. -/
def bitReverse (v : Fin n → Bool) : Fin n → Bool := permute Fin.revPerm v

@[simp] theorem bitReverse_apply (v : Fin n → Bool) (i : Fin n) :
    bitReverse v i = v i.rev := rfl

/-- Reversing twice is the identity: the two bit orders are symmetric. -/
@[simp] theorem bitReverse_bitReverse (v : Fin n → Bool) :
    bitReverse (bitReverse v) = v := by
  funext i; simp

theorem bitReverse_involutive : Function.Involutive (bitReverse (n := n)) :=
  bitReverse_bitReverse

theorem bitReverse_injective : Function.Injective (bitReverse (n := n)) :=
  bitReverse_involutive.injective

/-! ## The two readings of a stored integer

A stored address is an integer.  Reading it *least significant bit first*
gives one bit pattern; reading it *most significant bit first* gives another.
The whole content of the audit finding is that these two differ by
`bitReverse`. -/

/-- Read a stored integer with coordinate `i` at bit `i` (LSB-first). -/
def bitsLSB (n x : ℕ) : Fin n → Bool := fun i => x.testBit i.val

/-- Read a stored integer with coordinate `i` at bit `n - 1 - i` (MSB-first).
This is the convention the repository's stored addresses were written with. -/
def bitsMSB (n x : ℕ) : Fin n → Bool := fun i => x.testBit i.rev.val

/-- **The frame question, stated exactly.**  The MSB-first reading of a stored
integer is the bit reversal of its LSB-first reading.  So the two readings
carry the same information; only the coordinate labelling differs. -/
theorem bitsMSB_eq_bitReverse_bitsLSB (n x : ℕ) :
    bitsMSB n x = bitReverse (bitsLSB n x) := rfl

theorem bitsLSB_eq_bitReverse_bitsMSB (n x : ℕ) :
    bitsLSB n x = bitReverse (bitsMSB n x) := by
  rw [bitsMSB_eq_bitReverse_bitsLSB, bitReverse_bitReverse]

/-! ## Bit reversal is an isometry -/

/-- Bit reversal preserves Hamming distance. -/
theorem hdist_bitReverse (a b : Fin n → Bool) :
    hdist (bitReverse a) (bitReverse b) = hdist a b :=
  hdist_permute Fin.revPerm a b

/-- Hence it preserves Hamming weight. -/
theorem weight_bitReverse (v : Fin n → Bool) :
    hdist (bitReverse v) (bitReverse (fun _ => false)) = hdist v (fun _ => false) :=
  weight_permute Fin.revPerm v

/-- The image of a code under bit reversal. -/
def bitReverseSet (C : Set (Fin n → Bool)) : Set (Fin n → Bool) :=
  permuteSet Fin.revPerm C

/-- **Decoding commutes with a change of bit order.**  A word is nearest to `c`
in `C` exactly when its reversal is nearest to `c`'s reversal in the reversed
code.  Reading the stored data MSB-first, decoding there, and reading back is
therefore the same decoder. -/
theorem nearest_bitReverse_iff {C : Set (Fin n → Bool)} {v c : Fin n → Bool} :
    IsNearest C v c ↔ IsNearest (bitReverseSet C) (bitReverse v) (bitReverse c) :=
  nearest_permute_iff Fin.revPerm

theorem nearest_bitReverse {C : Set (Fin n → Bool)} {v c : Fin n → Bool}
    (h : IsNearest C v c) :
    IsNearest (bitReverseSet C) (bitReverse v) (bitReverse c) :=
  nearest_bitReverse_iff.mp h

/-- Minimum distance `8` survives bit reversal, so the reversed image of the
Golay code is again a minimum-distance-`8` code. -/
theorem min_distance_bitReverse {C : Set (Fin n → Bool)}
    (hmin : ∀ c ∈ C, ∀ c' ∈ C, c ≠ c' → 8 ≤ hdist c c') :
    ∀ c ∈ bitReverseSet C, ∀ c' ∈ bitReverseSet C, c ≠ c' → 8 ≤ hdist c c' :=
  min_distance_permute Fin.revPerm hmin

/-- Consequently the weight-`3` correction guarantee transports: in the
reversed frame, too, a pattern within distance `3` of the code has exactly one
nearest codeword. -/
theorem snap_unique_of_le_three_bitReverse {C : Set (Fin n → Bool)}
    (hmin : ∀ c ∈ C, ∀ c' ∈ C, c ≠ c' → 8 ≤ hdist c c')
    {v c c' : Fin n → Bool} (hc : c ∈ bitReverseSet C) (hc' : c' ∈ bitReverseSet C)
    (h : hdist v c ≤ 3) (h' : hdist v c' ≤ 3) : c = c' :=
  snap_unique_of_le_three (min_distance_bitReverse hmin) hc hc' h h'

/-! ## The audit's conclusion, as a single statement -/

/-- **The migration audit, formally.**  Suppose a stored integer's MSB-first
reading lies on the code `C`.  Then:

* its LSB-first reading lies on the *reversed* code, so the data is not
  corrupt — it was written in the other frame;
* the two readings are at the same Hamming distance from any pair of words,
  so no metric fact is lost by switching; and
* the reversed code still has minimum distance `8`, so the decoder's
  guarantees are unchanged.

This is why the migration may fix the frame rather than repair the data. -/
theorem endianness_is_a_frame_choice {C : Set (Fin n → Bool)} (x : ℕ)
    (hmem : bitsMSB n x ∈ C)
    (hmin : ∀ c ∈ C, ∀ c' ∈ C, c ≠ c' → 8 ≤ hdist c c') :
    bitsLSB n x ∈ bitReverseSet C
      ∧ (∀ a b : Fin n → Bool, hdist (bitReverse a) (bitReverse b) = hdist a b)
      ∧ (∀ c ∈ bitReverseSet C, ∀ c' ∈ bitReverseSet C, c ≠ c' →
          8 ≤ hdist c c') := by
  refine ⟨?_, hdist_bitReverse, min_distance_bitReverse hmin⟩
  refine ⟨bitsMSB n x, hmem, ?_⟩
  exact (bitsLSB_eq_bitReverse_bitsMSB n x).symm

end GLM.Golay
