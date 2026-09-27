/-
# What the archive's "44 balanced octads" is a fact about

`TriadCensus.lean` settles the archive's headline count: of the 759 octads of
the substrate's Golay code, exactly **44** have their three eight-bit blocks
pairwise at Hamming distance 4, which is the perfect score of
`GMHGL/tgic_verification.py`.  `Triad.lean` settles the shape of the score: the
deviation `Δ = |4−d₀₁| + |4−d₀₂| + |4−d₁₂|` is even, so `(4,4,4)` is a genuine
maximum rather than a normalisation.

Neither of those says what the 44 *measures*, and this file answers that, in
the two ways a count can be interrogated.

* **Against chance.**  `chance_census` counts, over all
  `C(24,8) = 735,471` eight-element subsets of the twenty-four coordinates —
  not only the 759 that happen to be codewords — how many sit at each
  deviation.  37,800 of them are balanced, so 759 subsets drawn without regard
  to the code would be expected to contain `759 · 37800 / 735471 = 12600/323`,
  just over **39**, balanced ones.  The code supplies 44.  Every class of the
  observed census (44, 336, 312, 58, 9) is within a few of the chance census
  scaled the same way (39.0, 329.4, 324.6, 57.2, 8.0).

* **Against relabelling.**  The blocks are the coordinate ranges `0–7`, `8–15`,
  `16–23` of the runtime's own ordering, and that ordering is a convention.
  `balanced_after_swap` transposes coordinates `0` and `8` — the smallest
  relabelling there is — and counts **49** balanced octads instead of 44, and
  `deviation_ten_after_swap` finds an octad at deviation 10, a value no octad
  reaches in the runtime's ordering (`no_deviation_ten`).  So neither the 44
  nor the shape of the census is a property of the Golay code: both are
  properties of the code *together with* its labelling, and the archive's
  verification measured the labelling.

The two readings agree.  A statistic that a two-coordinate swap moves by five,
and whose value is what an arbitrary collection of eight-element subsets would
give anyway, is not detecting the code.

`glm_universal.reasoning.balance` recomputes all of it, and adds the exact
range over all 276 transpositions, which is 27 to 63.
-/
import Mathlib
import RequestProject.GLM.Triad
import RequestProject.GLM.TriadCensus

namespace GLM.Triad

open Finset GLM.Golay24

/-! ## 1. The deviation of a word

`Triad.lean` has the deviation for three Boolean vectors of any length; this is
that quantity for the three blocks of a 24-bit word, spelled monomorphically so
that the censuses below compile to a loop (the reason `dist8` exists at all). -/

/-- The archive's deviation `Δ` of a word, written with truncated subtraction:
`(d - 4) + (4 - d)` is `|4 − d|` in `ℕ`. -/
def dev (s : Word) : ℕ :=
  ((dist8 (block s 0) (block s 1) - 4) + (4 - dist8 (block s 0) (block s 1)))
    + ((dist8 (block s 0) (block s 2) - 4) + (4 - dist8 (block s 0) (block s 2)))
    + ((dist8 (block s 1) (block s 2) - 4) + (4 - dist8 (block s 1) (block s 2)))

/-- It is the general `axisDev` of `Triad.lean` at the word's three blocks, so
everything proved there applies to it. -/
theorem dev_eq_axisDev (s : Word) :
    dev s = axisDev (block s 0) (block s 1) (block s 2) := rfl

/-- Hence the deviation of a word is even. -/
theorem dev_even (s : Word) : 2 ∣ dev s := by
  rw [dev_eq_axisDev]; exact axisDev_even _ _ _

/-- And it vanishes exactly on the balanced words, so `dev` is the archive's
score and `axisBalancedB` is its perfect value. -/
theorem dev_eq_zero_iff (s : Word) : dev s = 0 ↔ axisBalancedB s = true := by
  rw [dev_eq_axisDev, axisBalanced_iff]

/-! ## 2. The chance census: every eight-element subset, not only the octads -/

/-- All `C(24,8)` eight-element subsets of the twenty-four coordinates. -/
def allEight : Finset Word := (univ : Finset (Fin 24)).powersetCard 8

theorem card_allEight : #allEight = 735471 := by unfold allEight; native_decide

/-- **The chance census.**  How many of the 735,471 eight-element subsets sit at
each even deviation `0, 2, …, 12`.  37,800 of them are balanced; three sit at
the maximum 12.  This is the raw computation directive D2 asks for: the whole
family is walked, not sampled. -/
theorem chance_census :
    (List.range 7).map (fun k => #(allEight.filter (fun s => dev s == 2 * k)))
      = [37800, 319200, 314580, 55440, 7728, 720, 3] := by
  unfold allEight dev; native_decide

/-- The seven classes exhaust the family, so no subset was missed by counting
only even deviations. -/
theorem chance_census_total :
    ((List.range 7).map (fun k => #(allEight.filter (fun s => dev s == 2 * k)))).sum
      = #allEight := by
  rw [chance_census, card_allEight]; norm_num

/-- **Expected against observed.**  759 eight-element subsets drawn without
regard to the code would carry `12600/323 ≈ 39.01` balanced ones; the code's
759 octads carry 44 (`balanced_octad_count`). -/
theorem expected_balanced :
    (759 : ℚ) * 37800 / 735471 = 12600 / 323 := by norm_num

/-! ## 3. The extreme of the score -/

/-- Block `t` of the grid: the eight coordinates `8t, …, 8t+7`. -/
def blockSet (t : Fin 3) : Word :=
  univ.filter (fun k : Fin 24 => (k : ℕ) / 8 = (t : ℕ))

/-- The deviation reaches its maximum 12 on exactly three of the 735,471
subsets: the three blocks themselves.  A full block puts all eight points in one
row of the 3 × 8 grid, so two of the three distances are 8 and one is 0. -/
theorem dev_twelve_class :
    allEight.filter (fun s => dev s == 12) = {blockSet 0, blockSet 1, blockSet 2} := by
  unfold allEight dev blockSet; native_decide

/-! ## 4. The count is a fact about the labelling -/

/-- A relabelling of the coordinates, carried to words. -/
def relabel (e : Equiv.Perm (Fin 24)) (s : Word) : Word := s.map e.toEmbedding

/-- The smallest relabelling there is: exchange coordinates `0` and `8`. -/
def swap08 : Equiv.Perm (Fin 24) := Equiv.swap 0 8

/-- **The 44 is not a code invariant.**  Relabelled by a single transposition,
the same 759 octads supply 49 balanced ones. -/
theorem balanced_after_swap :
    #(octadMessages.filter (fun m => axisBalancedB (relabel swap08 (encode m))))
      = 49 := by
  unfold octadMessages wt relabel swap08; native_decide

theorem balance_not_invariant :
    #(octadMessages.filter (fun m => axisBalancedB (relabel swap08 (encode m))))
      ≠ #(octadMessages.filter (fun m => axisBalancedB (encode m))) := by
  rw [balanced_after_swap, balanced_octad_count]; decide

/-- Nor is the shape of the census.  In the runtime's ordering no octad reaches
deviation 10; after the same transposition one does. -/
theorem no_deviation_ten :
    #(octadMessages.filter (fun m => dev (encode m) == 10)) = 0 := by
  unfold octadMessages wt dev; native_decide

theorem deviation_ten_after_swap :
    #(octadMessages.filter (fun m => dev (relabel swap08 (encode m)) == 10)) = 1 := by
  unfold octadMessages wt relabel swap08 dev; native_decide

end GLM.Triad
