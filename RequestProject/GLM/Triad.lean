/-
# The triad, and the decomposition-richness of 24

Three of the archive's engines — `tgic_v3.py`, `tgic_audit.py` and
`ubp_tgic_engine.py` — are built on the "Triad Graph Interaction Constraint",
the triple `3, 6, 9`, and the whole system is built on `24`.  Both are quoted as
structural discoveries.  This file is the audit, and it is short because the
result is negative and clean.

* `tgic_counts` — `3, 6, 9` is one number, not three: fixing a frame of three
  axes determines `6 = 3·2` signed directions and `9 = 3²` ordered axis pairs.
* `tgic_counts_generic` — and those counts are not a property of the substrate.
  *Any* three-element set produces them, so exhibiting `3, 6, 9` cannot
  distinguish the GLM substrate from any other three-fold structure.
* `interaction_counts_differ` — even the `9` is a convention: on three axes
  there are `3` unordered pairs of distinct axes, `6` unordered pairs allowing
  repetition and `9` ordered pairs.  "Nine interactions" is a choice of which
  of the three to name.
* `twentyfour_decompositions` — `24` is decomposition-rich: eight divisors, and
  simultaneously `4!`, `2·12`, `3·8`, `2³·3` and `23+1`.  Matching a structure
  to *a* decomposition of 24 is close to costless and is not evidence.

Compare `Packing.lean`: the one place in the whole development where a number
near 24 really is forced, the forced number is **23**, and 24 is the parity
extension of it.  This file and that one are the two halves of the same audit,
and `FitCapacity.lean` is the quantitative version of the same caution.
-/
import Mathlib

namespace GLM.Triad

open Finset

/-- Three axes, six signed directions, nine ordered axis pairs. -/
theorem tgic_counts :
    Fintype.card (Fin 3) = 3 ∧ Fintype.card (Fin 3 × Bool) = 6 ∧
      Fintype.card (Fin 3 × Fin 3) = 9 := by
  refine ⟨rfl, ?_, ?_⟩ <;> simp

/-- **The counts are generic.**  The same numbers follow from any three-element
set, so they say nothing about the substrate. -/
theorem tgic_counts_generic (α : Type) [Fintype α] (h : Fintype.card α = 3) :
    Fintype.card (α × Bool) = 6 ∧ Fintype.card (α × α) = 9 := by
  constructor
  · rw [Fintype.card_prod, h]; rfl
  · rw [Fintype.card_prod, h]

/-- **"Nine interactions" is a convention.**  Three axes support three unordered
pairs of *distinct* axes, six unordered pairs if repetition is allowed, and nine
ordered pairs. -/
theorem interaction_counts_differ :
    ((univ : Finset (Fin 3)).powersetCard 2).card = 3 ∧
      Fintype.card (Sym2 (Fin 3)) = 6 ∧ Fintype.card (Fin 3 × Fin 3) = 9 := by
  refine ⟨by decide, by decide, by simp⟩

/-- **24 is decomposition-rich**, so matching a structure to some decomposition
of it is close to costless. -/
theorem twentyfour_decompositions :
    (Nat.divisors 24).card = 8 ∧ Nat.factorial 4 = 24 ∧ 2 * 12 = 24 ∧ 3 * 8 = 24 ∧
      2 ^ 3 * 3 = 24 ∧ 23 + 1 = 24 := by
  refine ⟨by decide, by decide, by norm_num, by norm_num, by norm_num, by norm_num⟩

/-! ## The shape of the archive's three-axis score

`tgic_verification.py` scores a 24-bit word by the three pairwise Hamming
distances of its eight-bit blocks, calling `(4,4,4)` perfect and
`Δ = |4−d₀₁| + |4−d₀₂| + |4−d₁₂|` the deviation from it.  The definitions below
are that score for three Boolean vectors of *any* length, and `axisDev_even`
is the fact that makes `(4,4,4)` a genuine maximum rather than a normalisation:
the deviation can only ever be even, so there is no word one step off perfect.
`TriadCensus.lean` instantiates them at length eight and counts. -/

/-- Hamming distance of two Boolean vectors of the same length. -/
def dist {n : ℕ} (a b : Fin n → Bool) : ℕ := #(univ.filter (fun i => a i ≠ b i))

/-- Among three Boolean values the number of unequal pairs is `0` or `2`, so the
three pairwise distances of three vectors always sum to an even number. -/
theorem dist_sum_even {n : ℕ} (a b c : Fin n → Bool) :
    2 ∣ dist a b + dist a c + dist b c := by
  classical
  unfold dist
  simp only [Finset.card_filter]
  rw [← Finset.sum_add_distrib, ← Finset.sum_add_distrib]
  refine Finset.dvd_sum ?_
  intro i _
  rcases a i <;> rcases b i <;> rcases c i <;> simp

/-- The archive's deviation of three blocks: `|4−d₀₁| + |4−d₀₂| + |4−d₁₂|`,
written with truncated subtraction, in which `(d − 4) + (4 − d)` is `|4 − d|`. -/
def axisDev {n : ℕ} (a b c : Fin n → Bool) : ℕ :=
  ((dist a b - 4) + (4 - dist a b)) + ((dist a c - 4) + (4 - dist a c))
    + ((dist b c - 4) + (4 - dist b c))

/-- **The deviation is always even.**  So the score `(4,4,4)` is a genuine
maximum: no configuration sits one unit away from it. -/
theorem axisDev_even {n : ℕ} (a b c : Fin n → Bool) : 2 ∣ axisDev a b c := by
  have h := dist_sum_even a b c
  unfold axisDev
  omega

/-- The deviation vanishes exactly on the perfectly balanced triples. -/
theorem axisDev_eq_zero_iff {n : ℕ} (a b c : Fin n → Bool) :
    axisDev a b c = 0 ↔ dist a b = 4 ∧ dist a c = 4 ∧ dist b c = 4 := by
  unfold axisDev; omega

end GLM.Triad
