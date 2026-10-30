/-
# The 44 balanced octads

`Triad.lean` proves what the archive's "3-axis" score depends on for three
arbitrary Boolean vectors: the sum of the three pairwise distances is even and
at most `2n`, so the deviation from the balanced triple `(4,4,4)` is even and
the perfect score is a maximum.  This file supplies the census that goes with
it, for the code the substrate actually uses.

`GMHGL/tgic_verification.py` in the supplied archive tests the claim that **44
of the 759 octads score a perfect 1 on the 3-axis measure** — that is, that
their three eight-bit blocks are pairwise at Hamming distance exactly 4.  The
claim is true, and `balanced_octad_count` proves it by walking all 4,096
messages, which is the raw computation directive D2 asks for.

Two things keep that walk cheap, and both are deliberate.

* The counts are separated from the theory of `Triad.lean`, which imports this
  file, because `native_decide` compiles the module it runs in: keeping the
  general, length-polymorphic definitions of the theory out of this module
  keeps the census cheap to build.
* The balance test is a `Bool`-valued function, `axisBalancedB`, and the two
  counts are computed from it directly rather than transported across a
  `Prop`-valued wrapper.  Wrapping it costs more than the computation does:
  the transport has to reconcile two `Decidable` instances for a filter over
  4,096 messages, which sends the elaborator into the census by `whnf`.  The
  reading of `axisBalancedB` as a statement about the three distances is
  `axisBalanced_iff_dists`, and it is proved once, for an arbitrary word.
-/
import Mathlib
import RequestProject.GLM.Golay.Code
import RequestProject.GLM.GolayWeightEnum
import RequestProject.GLM.Triad

namespace GLM.Triad

open Finset

/-! ## 2. The blocks of a 24-bit word, and the 44 balanced octads -/

open GLM.Golay24

/-- The `j`-th coordinate of block `t` of a word: position `8t + j`. -/
def blockBit (s : Word) (t : Fin 3) (j : Fin 8) : Bool :=
  decide ((⟨8 * (t : ℕ) + (j : ℕ), by omega⟩ : Fin 24) ∈ s)

/-- Block `t` of a word, as a Boolean vector of length 8. -/
def block (s : Word) (t : Fin 3) : Fin 8 → Bool := blockBit s t

/-- The Hamming distance of two eight-bit blocks.  This is the `dist` of
`Triad.lean` at `n = 8`, spelled without the length parameter so that the
census below compiles to a monomorphic loop; `GLM.Triad.dist8_eq` proves the
two agree. -/
def dist8 (a b : Fin 8 → Bool) : ℕ := #(univ.filter (fun i => a i ≠ b i))

/-- The archive's perfect "3-axis" score, as a Boolean test: the three block
distances of the word are all `4`. -/
def axisBalancedB (s : Word) : Bool :=
  (dist8 (block s 0) (block s 1) == 4) && (dist8 (block s 0) (block s 2) == 4)
    && (dist8 (block s 1) (block s 2) == 4)

/-- What the test says, read as a statement about the three distances. -/
theorem axisBalanced_iff_dists (s : Word) :
    axisBalancedB s = true ↔ dist8 (block s 0) (block s 1) = 4 ∧
      dist8 (block s 0) (block s 2) = 4 ∧ dist8 (block s 1) (block s 2) = 4 := by
  unfold axisBalancedB
  simp [and_assoc]

/-- `dist8` is the general `dist` of `Triad.lean` at length eight; the two
spellings agree definitionally, so everything proved there applies here. -/
theorem dist8_eq (a b : Fin 8 → Bool) : dist8 a b = dist a b := rfl

/-- The general deviation of `Triad.lean`, read on the three blocks of a word,
vanishes exactly on the balanced words. -/
theorem axisBalanced_iff (s : Word) :
    axisDev (block s 0) (block s 1) (block s 2) = 0 ↔ axisBalancedB s = true := by
  rw [axisDev_eq_zero_iff, axisBalanced_iff_dists]
  simp only [dist8_eq]

/-- The octads of the substrate's Golay code, as the messages whose encoding
has weight 8. -/
def octadMessages : Finset (Fin 12 → ZMod 2) :=
  univ.filter (fun m => wt (encode m) = 8)

/-- There are 759 of them: the weight enumerator's `x⁸` coefficient, transported
along the bijection `encode` between messages and codewords. -/
theorem card_octadMessages : #octadMessages = 759 := by
  have himg : (univ : Finset (Fin 12 → ZMod 2)).image encode = codewords := by
    ext c
    simp only [Finset.mem_image, Finset.mem_univ, true_and, mem_codewords]
    exact ⟨by rintro ⟨m, rfl⟩; exact encode_isCodeword m, fun hc => exists_encode hc⟩
  have h := golay_weight_enumerator.2.1
  rw [← himg, Finset.filter_image,
    Finset.card_image_of_injective _ encode_injective] at h
  exact h

/-- **The archive's 44.**  Of the 759 octads, exactly 44 have all three block
distances equal to `4`. -/
theorem balanced_octad_count :
    #(octadMessages.filter (fun m => axisBalancedB (encode m))) = 44 := by
  unfold octadMessages wt; native_decide

/-- And the balanced octads are a small minority: 715 octads are not balanced.
Counted the same way, rather than subtracted, so that the two counts and
`card_octadMessages` check each other: `44 + 715 = 759`. -/
theorem unbalanced_octad_count :
    #(octadMessages.filter (fun m => axisBalancedB (encode m) = false)) = 715 := by
  unfold octadMessages wt; native_decide

/-- The two counts exhaust the octads. -/
theorem balanced_add_unbalanced :
    #(octadMessages.filter (fun m => axisBalancedB (encode m)))
      + #(octadMessages.filter (fun m => axisBalancedB (encode m) = false))
      = #octadMessages := by
  rw [balanced_octad_count, unbalanced_octad_count, card_octadMessages]

end GLM.Triad
