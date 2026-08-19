import Mathlib

set_option autoImplicit false

/-!
# Stage 5 — the decorative arithmetic: 3, 6, 9 and 24

The UBP literature attaches significance to the triple `3, 6, 9` (the "Triad
Graph Interaction Constraint") and to the number `24`.  A first-principles
investigation must ask whether these numbers are *inputs* or *consequences*, and
whether exhibiting them is evidence for anything.

Findings (FP-32 … FP-35):

* **FP-32** `3, 6, 9` is one number, not three: fixing a frame of `3` axes
  determines `6 = 3·2` signed directions and `9 = 3²` ordered axis pairs
  (`tgic_counts`).  Whatever content TGIC has is the choice of `3`.
* **FP-33** Those counts are not a property of the substrate: *any* three-element
  set produces them (`tgic_counts_generic`).  So reproducing `3, 6, 9` cannot
  distinguish the UBP substrate from any other three-fold structure.
* **FP-34** Even the `9` is conventional: on three axes there are `3` unordered
  pairs of distinct axes, `6` unordered pairs allowing repetition, and `9`
  ordered pairs (`interaction_counts_differ`).  "Nine interactions" is a choice
  of which of the three counts to name.
* **FP-35** `24` is decomposition-rich: it has `8` divisors and simultaneously
  equals `4!`, `2·12`, `3·8`, `2³·3` and `23+1` (`twentyfour_decompositions`).
  Matching some structure to *a* decomposition of 24 is therefore close to
  costless, and is not evidence.  Compare FP-15: the one place where a number
  near 24 really is forced, the forced number is **23**.
-/

namespace UBPFirstPrinciples

open Finset

/-! ## FP-32  The triadic counts -/

/-- Three axes, six signed directions, nine ordered axis pairs. -/
theorem tgic_counts :
    Fintype.card (Fin 3) = 3 ∧ Fintype.card (Fin 3 × Bool) = 6 ∧
      Fintype.card (Fin 3 × Fin 3) = 9 := by
  refine ⟨rfl, ?_, ?_⟩ <;> simp

/-! ## FP-33  The counts are generic -/

/-- The same counts follow from any three-element set, so they say nothing about
the substrate. -/
theorem tgic_counts_generic (α : Type) [Fintype α] (h : Fintype.card α = 3) :
    Fintype.card (α × Bool) = 6 ∧ Fintype.card (α × α) = 9 := by
  constructor
  · rw [Fintype.card_prod, h]; rfl
  · rw [Fintype.card_prod, h]

/-! ## FP-34  "Nine interactions" is a convention -/

/-- Three axes support three unordered pairs of *distinct* axes, six unordered
pairs if repetition is allowed, and nine ordered pairs. -/
theorem interaction_counts_differ :
    ((univ : Finset (Fin 3)).powersetCard 2).card = 3 ∧
      Fintype.card (Sym2 (Fin 3)) = 6 ∧ Fintype.card (Fin 3 × Fin 3) = 9 := by
  refine ⟨by decide, by decide, by simp⟩

/-! ## FP-35  24 is decomposition-rich -/

theorem twentyfour_decompositions :
    (Nat.divisors 24).card = 8 ∧ Nat.factorial 4 = 24 ∧ 2 * 12 = 24 ∧ 3 * 8 = 24 ∧
      2 ^ 3 * 3 = 24 ∧ 23 + 1 = 24 := by
  refine ⟨by decide, by decide, by norm_num, by norm_num, by norm_num, by norm_num⟩

end UBPFirstPrinciples
