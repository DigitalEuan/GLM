/-
# The protected tag: a sender tag with a code of its own

The formal half of `studies/PROTECTED_TAG_STUDY.md` (Phase 134).
`DesignedSubstrate.lean` proved the seven-bit sender tag resolves every six-way
tie (`tag_resolves`) — provided the tag arrives intact. Phase 133 measured
what happens when it does not: a tag with one bit flipped resolves 4.1 % of
tied reads to the wrong carrier. This file proves why, and what fixes it.

**The tag of a tie is the tag of an octad.** Two candidates of one fork are
both within distance `4` of the received word, so they differ by a codeword of
weight at most `8` — an octad. A tag made of parities is linear, so the two
candidates' tags differ by the tag of that octad. How many flips of the tag a
stage can absorb is therefore decided by the smallest tag weight over the 759
octads, and nothing else.

* `mtag_separation` — for any list of parity masks, if every octad's tag has
  weight at least `D`, then for two distinct candidates of one fork and any
  received tag `τ`, `D ≤ d(τ, tag c) + d(τ, tag c')`. The finite step is one
  check over the 4,096 messages, as for `tag_nonzero_on_octads`.
* `mtag_resolves` — so a stage that keeps the candidates whose tag lies
  within `s` of `τ`, with `2s < D`, keeps at most one; and it keeps the sent
  one whenever the tag took at most `s` flips.
* `tag7_one_flip_misleads` — the seven-bit tag of Phase 133 has an octad of
  tag weight `1`, so one flipped tag bit can name the wrong candidate exactly.
* The protected tags: the seven tag bits followed by the parities of a code on
  them. `tag11_octad_weight` (the shortened Hamming `[11,7,3]` code, 11 bits)
  gives every octad tag weight at least `3`, so it corrects one flipped tag
  bit (`tag11_corrects_one`); `tag15_octad_weight` (the `[15,7,5]` BCH code,
  15 bits) gives at least `5`, so it corrects two (`tag15_corrects_two`), or,
  read at radius `1`, corrects one and never misleads on three
  (`tag15_radius_one_safe`). `tag15_three_flips_mislead` shows radius `2` is
  sharp: three flips can mislead it.
-/
import Mathlib
import RequestProject.GLM.DesignedSubstrate

namespace GLM.Golay24

open Finset

/-! ## 1. Tags from any list of parity masks -/

/-- Coordinate `k`'s contribution to an `r`-bit tag read through masks `M`. -/
def mtagCol (M : List ℕ) (r : ℕ) (k : Fin 24) : Fin r → ZMod 2 :=
  fun i => if (M.getD i 0).testBit k then 1 else 0

/-- The `r`-bit tag of a word through masks `M`: the parity of its overlap
with each mask. -/
def mtag (M : List ℕ) (r : ℕ) (w : Word) : Fin r → ZMod 2 := ∑ k ∈ w, mtagCol M r k

/-- The seven-bit tag of Phase 133 is the case `M = tagMasks`, `r = 7`. -/
theorem mtag_tagMasks (w : Word) : mtag tagMasks 7 w = tagOf w := rfl

theorem mtag_neg_self {r : ℕ} (x : Fin r → ZMod 2) : -x = x := by
  funext i
  have : ∀ y : ZMod 2, -y = y := by decide
  exact this (x i)

/-- A mask tag is linear. -/
theorem mtag_symmDiff (M : List ℕ) (r : ℕ) (a b : Word) :
    mtag M r (symmDiff a b) = mtag M r a + mtag M r b := by
  have hsub : a ∩ b ⊆ a ∪ b := (inter_subset_left).trans subset_union_left
  have hsd : symmDiff a b = (a ∪ b) \ (a ∩ b) := by
    rw [symmDiff_eq_sup_sdiff_inf]; rfl
  have h1 : ∑ k ∈ (a ∪ b) \ (a ∩ b), mtagCol M r k
      = (∑ k ∈ a ∪ b, mtagCol M r k) - ∑ k ∈ a ∩ b, mtagCol M r k :=
    Finset.sum_sdiff_eq_sub hsub
  have h2 : (∑ k ∈ a ∪ b, mtagCol M r k) + ∑ k ∈ a ∩ b, mtagCol M r k
      = (∑ k ∈ a, mtagCol M r k) + ∑ k ∈ b, mtagCol M r k := Finset.sum_union_inter
  unfold mtag
  rw [hsd, h1, sub_eq_add_neg, mtag_neg_self]
  linear_combination (norm := abel) h2

/-- Two distinct codewords at most `11` apart differ by an octad. -/
theorem close_pair_octad {c c' : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (hne : c ≠ c') (hd : hdist c c' ≤ 11) :
    IsCodeword (symmDiff c c') ∧ wt (symmDiff c c') = 8 := by
  have ho : IsCodeword (symmDiff c c') := isCodeword_symmDiff hc hc'
  have hne' : symmDiff c c' ≠ ∅ := fun h0 => hne (symmDiff_eq_bot.1 h0)
  have h8 : 8 ≤ wt (symmDiff c c') := golay_min_weight ho hne'
  have hd' : wt (symmDiff c c') ≤ 11 := hd
  refine ⟨ho, ?_⟩
  rcases golay_weight_mem ho with h0 | h0 | h0 | h0 | h0 <;> omega

/-- The distance between two words is at most the sum of their distances to
a third. -/
theorem hdist_triangle (c y c' : Word) : hdist c c' ≤ hdist y c + hdist y c' := by
  have hsub : symmDiff c c' ⊆ symmDiff c y ∪ symmDiff y c' := symmDiff_triangle c y c'
  have := (card_le_card hsub).trans (card_union_le _ _)
  rw [hdist_comm y c]
  exact this

/-- **Separation.** If every octad's tag has weight at least `D`, the tags of
two distinct codewords at most `11` apart are at least `D` apart, measured
through any received tag. Two candidates of one fork are at most `8` apart;
a sent carrier with at most `7` flips and a wrong candidate of its read are at
most `11` apart. -/
theorem mtag_separation (M : List ℕ) (r D : ℕ)
    (hM : ∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → D ≤ hammingNorm (mtag M r (encode m)))
    {c c' : Word} (hc : IsCodeword c) (hc' : IsCodeword c') (hne : c ≠ c')
    (hd : hdist c c' ≤ 11) (τ : Fin r → ZMod 2) :
    D ≤ hammingDist τ (mtag M r c) + hammingDist τ (mtag M r c') := by
  obtain ⟨ho, hw⟩ := close_pair_octad hc hc' hne hd
  obtain ⟨m, hm⟩ := exists_encode ho
  have hD : D ≤ hammingNorm (mtag M r (symmDiff c c')) := by
    rw [← hm] at hw ⊢
    exact hM m hw
  have hnorm : hammingNorm (mtag M r (symmDiff c c'))
      = hammingDist (mtag M r c) (mtag M r c') := by
    rw [hammingDist_eq_hammingNorm, mtag_symmDiff, sub_eq_add_neg, mtag_neg_self]
  have htri := hammingDist_triangle (mtag M r c) τ (mtag M r c')
  rw [hammingDist_comm (mtag M r c) τ] at htri
  omega

/-- **The tag stage of radius `s` resolves.** With `2s < D`, at most one
candidate of a fork has its tag within `s` of the received tag. -/
theorem mtag_resolves (M : List ℕ) (r D s : ℕ)
    (hM : ∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → D ≤ hammingNorm (mtag M r (encode m)))
    (hs : 2 * s < D) {y c c' : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (h : hdist y c ≤ 4) (h' : hdist y c' ≤ 4) {τ : Fin r → ZMod 2}
    (ht : hammingDist τ (mtag M r c) ≤ s) (ht' : hammingDist τ (mtag M r c') ≤ s) :
    c = c' := by
  by_contra hne
  have := mtag_separation M r D hM hc hc' hne
    ((hdist_triangle c y c').trans (by omega)) τ
  omega

/-- **The intact seven-bit tag flags every miscorrection up to seven flips.**
If the sent carrier `c` took at most `7` flips and `c'` is any other codeword
within `4` of the received word (a decoder's wrong answer, or a wrong
candidate of its fork), the two carry different tags. -/
theorem tag_flags_miscorrection {y c c' : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (hne : c ≠ c') (h : hdist y c ≤ 7) (h' : hdist y c' ≤ 4) : tagOf c ≠ tagOf c' := by
  intro ht
  have hM : ∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 →
      1 ≤ hammingNorm (mtag tagMasks 7 (encode m)) := by
    intro m hm
    rw [Nat.one_le_iff_ne_zero, Ne, hammingNorm_eq_zero, mtag_tagMasks]
    exact tag_nonzero_on_octads m hm
  have := mtag_separation tagMasks 7 1 hM hc hc' hne
    ((hdist_triangle c y c').trans (by omega)) (tagOf c)
  rw [mtag_tagMasks, mtag_tagMasks, ← ht, hammingDist_self] at this
  omega

/-! ## 2. The seven-bit tag absorbs no flip -/

/-- One flipped bit of the seven-bit tag can name the wrong candidate exactly:
the received tag is one flip from the sent carrier's tag and equal to the tag
of another candidate of the same fork. -/
theorem tag7_one_flip_misleads :
    ∃ y c c' : Word, ∃ τ : Fin 7 → ZMod 2, IsCodeword c ∧ IsCodeword c' ∧ c ≠ c' ∧
      hdist y c ≤ 4 ∧ hdist y c' ≤ 4 ∧
      hammingDist τ (tagOf c) = 1 ∧ hammingDist τ (tagOf c') = 0 := by
  refine ⟨{0, 1, 3, 8}, ∅, {0, 1, 3, 8, 10, 13, 14, 17},
    tagOf {0, 1, 3, 8, 10, 13, 14, 17}, isCodeword_empty, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · unfold IsCodeword; native_decide
  · decide
  · unfold hdist; decide
  · unfold hdist; decide
  · native_decide
  · simp

/-! ## 3. The protected tags -/

/-- The eleven masks of the protected tag of radius `1`: the seven tag masks,
then the four parities of the shortened Hamming `[11,7,3]` code (generator
`x⁴ + x + 1`) on the tag bits. -/
def tagMasks11 : List ℕ :=
  [7442265, 11191954, 5298992, 12955048, 9854244, 14599079, 3151149,
   1207032, 15741673, 6051243, 4961599]

/-- The fifteen masks of the protected tag of radius `2`: the seven tag masks,
then the eight parities of the `[15,7,5]` BCH code (generator
`x⁸ + x⁷ + x⁶ + x⁴ + 1`) on the tag bits. -/
def tagMasks15 : List ℕ :=
  [7442265, 11191954, 5298992, 12955048, 9854244, 14599079, 3151149,
   2024547, 7094406, 4961599, 6546849, 5667552, 8558092, 6636657, 1130820]

/-- The protected tags begin with the seven-bit tag. -/
theorem tagMasks11_prefix : tagMasks11.take 7 = tagMasks := by decide
theorem tagMasks15_prefix : tagMasks15.take 7 = tagMasks := by decide

/-- **Finite step, radius 1.** Every octad's eleven-bit tag has weight at
least `3`, checked over the 4,096 messages. -/
theorem tag11_octad_weight :
    ∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → 3 ≤ hammingNorm (mtag tagMasks11 11 (encode m)) := by
  unfold wt; native_decide

/-- **Finite step, radius 2.** Every octad's fifteen-bit tag has weight at
least `5`, checked over the 4,096 messages. -/
theorem tag15_octad_weight :
    ∀ m : Fin 12 → ZMod 2, wt (encode m) = 8 → 5 ≤ hammingNorm (mtag tagMasks15 15 (encode m)) := by
  unfold wt; native_decide

/-- **The eleven-bit tag corrects one flip.** If the sent carrier took at most
seven flips and the received tag is within one flip of its tag, every other
codeword within `4` of the received word has its tag more than one flip away. -/
theorem tag11_corrects_one {y c c' : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (h : hdist y c ≤ 7) (h' : hdist y c' ≤ 4) (hne : c ≠ c') {τ : Fin 11 → ZMod 2}
    (ht : hammingDist τ (mtag tagMasks11 11 c) ≤ 1) :
    1 < hammingDist τ (mtag tagMasks11 11 c') := by
  have := mtag_separation tagMasks11 11 3 tag11_octad_weight hc hc' hne
    ((hdist_triangle c y c').trans (by omega)) τ
  omega

/-- **The fifteen-bit tag corrects two flips.** If the sent carrier took at
most seven flips and the received tag is within two flips of its tag, every
other codeword within `4` of the received word has its tag more than two flips
away. -/
theorem tag15_corrects_two {y c c' : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (h : hdist y c ≤ 7) (h' : hdist y c' ≤ 4) (hne : c ≠ c') {τ : Fin 15 → ZMod 2}
    (ht : hammingDist τ (mtag tagMasks15 15 c) ≤ 2) :
    2 < hammingDist τ (mtag tagMasks15 15 c') := by
  have := mtag_separation tagMasks15 15 5 tag15_octad_weight hc hc' hne
    ((hdist_triangle c y c').trans (by omega)) τ
  omega

/-- **Read at radius 1, the fifteen-bit tag never misleads on three flips.**
If the sent carrier took at most seven flips and the received tag is within
three flips of its tag, no other codeword within `4` of the received word has
its tag within one flip, so the stage resolves to the truth or
keeps nothing — it never names a wrong candidate. -/
theorem tag15_radius_one_safe {y c c' : Word} (hc : IsCodeword c) (hc' : IsCodeword c')
    (h : hdist y c ≤ 7) (h' : hdist y c' ≤ 4) (hne : c ≠ c') {τ : Fin 15 → ZMod 2}
    (ht : hammingDist τ (mtag tagMasks15 15 c) ≤ 3) :
    1 < hammingDist τ (mtag tagMasks15 15 c') := by
  have := mtag_separation tagMasks15 15 5 tag15_octad_weight hc hc' hne
    ((hdist_triangle c y c').trans (by omega)) τ
  omega

/-- **Radius 2 is sharp.** Three flips of the fifteen-bit tag can bring it
within two flips of another candidate's tag. -/
theorem tag15_three_flips_mislead :
    ∃ y c c' : Word, ∃ τ : Fin 15 → ZMod 2, IsCodeword c ∧ IsCodeword c' ∧ c ≠ c' ∧
      hdist y c ≤ 4 ∧ hdist y c' ≤ 4 ∧
      hammingDist τ (mtag tagMasks15 15 c) = 3 ∧
      hammingDist τ (mtag tagMasks15 15 c') = 2 := by
  refine ⟨{1, 3, 5, 6}, ∅, {1, 3, 5, 6, 8, 11, 13, 15},
    fun i => if (i : ℕ) = 0 ∨ (i : ℕ) = 4 ∨ (i : ℕ) = 6 then 1 else 0,
    isCodeword_empty, ?_, ?_, ?_, ?_, ?_, ?_⟩
  · unfold IsCodeword; native_decide
  · decide
  · unfold hdist; decide
  · unfold hdist; decide
  · native_decide
  · native_decide

end GLM.Golay24
