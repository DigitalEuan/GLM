import RequestProject.GLM.Rule30.PowerSeriesLadder
import RequestProject.GLM.Rule30.RunCountLaw
import RequestProject.GLM.Rule30.Compute

/-!
# Round 23: certificates for the power-series ladder and the counting law

(Not a `module`: the checks use `native_decide`.)  All statements here are `CERT`: theorems about
the stated finite range, computed from the verified bit-parallel centre column (`list20000`).

* **`lcProfile_centerCol_19999`** — the linear complexity of the first `19999` centre bits is at
  least `10000` (the maximum possible order of magnitude, `m/2`): no linear recurrence over `GF(2)`
  of order `< 10000` generates them.  Certified by `hankel_centerCol_det_ne_zero`
  (`det (hankel centerCol 10000) ≠ 0`, via a checked inverse).
* **`no_eventual_period_below_10000`** — consequently the centre column has no eventual period `p`
  starting at time `τ` with `τ + p < 10000` (the Round 3 bound was `p ≤ 1000`, `τ ≤ 1000`).
* `complexity_centerCol_eq` — every word of length `n ≤ 10` occurs in the centre column:
  `complexity centerCol n = 2ⁿ`.
* `twoKernel_centerCol_ge` — the decimations `a(2ᵏ n + r)`, `k ≤ 9`, `r < 2ᵏ`, are pairwise
  distinct, so the 2-kernel has at least `1023` elements (an automaton producing the column from
  the base-2 digits of `n` needs at least `1023` states).
* `runCountTwoLawDraft_false`, `deficitIncreasingAfterD_false` — the two Round 21 draft
  conjectures that the corrected `runCount_law` does not cover are false.
-/

namespace GLM.Rule30

/-! ## The counting law: sanity checks and the refuted draft statements -/

/-- The proved law on a sample, and the failure of its draft extension to `T = d`. -/
theorem runCount_samples :
    RunCount 2 6 5 = 2 ^ 7 ∧ RunCount 2 3 3 = 20 ∧ RunCount 2 4 4 = 20 ∧
      RunCount 2 1 3 = 1 ∧ RunCount 2 1 4 = 2 := by
  native_decide

/-- **The draft counting law is false at `T = d`**: `RunCount 2 3 3 = 20 ≠ 16`. -/
theorem runCountTwoLawDraft_false : ¬ RunCountTwoLawDraft := by
  intro h
  have := h 3 3 (by norm_num) le_rfl
  rw [runCount_samples.2.1] at this
  norm_num at this

/-- **The draft deficit monotonicity is false**: at `d = 1`, `T = 3` the counts go from `1` to `2`,
so `2^5 / 2 = 16` is not greater than `2^4 / 1 = 16`. -/
theorem deficitIncreasingAfterD_false : ¬ DeficitIncreasingAfterD := by
  intro h
  have := h 1 3 (by norm_num) (by rw [runCount_samples.2.2.2.2]; norm_num)
  rw [runCount_samples.2.2.2.2, runCount_samples.2.2.2.1] at this
  norm_num at this

/-! ## Centre-column prefix as an array and as a packed number -/

/-- The first 20000 centre bits as an array. -/
def arr20000 : Array Bool := list20000.toArray

theorem arr20000_getD (n : ℕ) (hn : n < 20000) : arr20000.getD n false = centerCol n := by
  rw [centerCol_eq_getD n hn, arr20000]
  simp [Array.getD_eq_getD_getElem?, List.getD_eq_getElem?_getD]

/-- The first 20000 centre bits packed into one natural number. -/
def P20000 : ℕ := packBits list20000

theorem testBit_P20000 (n : ℕ) (hn : n < 20000) : P20000.testBit n = centerCol n := by
  rw [P20000, testBit_packBits, centerCol_eq_getD n hn]

/-! ## Linear complexity via a Hankel determinant -/

theorem hankelInvCheck_10000 : hankelInvCheck P20000 10000 = true := by native_decide

/-- **`det (hankel centerCol 10000) ≠ 0`** over `GF(2)`. -/
theorem hankel_centerCol_det_ne_zero : (hankel centerCol 10000).det ≠ 0 :=
  hankel_det_ne_zero_of_check hankelInvCheck_10000 fun n hn => testBit_P20000 n (by omega)

/-- **Maximal-order linear complexity on 19999 bits.** No linear recurrence of order `< 10000`
over `GF(2)` generates the first `19999` centre bits; equivalently the truncation of `A(z)` agrees
with no rational function whose denominator has degree `< 10000`. -/
theorem lcProfile_centerCol_19999 : 10000 ≤ lcProfile centerCol 19999 :=
  le_lcProfile_of_hankel_det hankel_centerCol_det_ne_zero (by norm_num)

/-- **No eventual period with `τ + p < 10000`.** -/
theorem no_eventual_period_below_10000 :
    ∀ τ p, 0 < p → τ + p < 10000 → ¬ ∀ n ≥ τ, centerCol (n + p) = centerCol n :=
  noSmallPeriodicity_of_lcProfile lcProfile_centerCol_19999

/-! ## Factor complexity -/

theorem all_words_10 :
    ∀ w : Fin 10 → Bool, ∃ i < 19990, ∀ j : Fin 10, arr20000.getD (i + j) false = w j := by
  native_decide

/-- **Every word of length `n ≤ 10` occurs in the centre column**: `p(n) = 2ⁿ` for `n ≤ 10`. -/
theorem complexity_centerCol_eq (n : ℕ) (hn : n ≤ 10) : complexity centerCol n = 2 ^ n := by
  refine complexity_eq_two_pow (factors_univ_of_le hn fun w => ?_)
  obtain ⟨i, hi, hw⟩ := all_words_10 w
  exact ⟨i, funext fun j => by
    rw [← hw j]; exact (arr20000_getD (i + j) (by omega)).symm⟩

/-! ## The 2-kernel -/

/-- The kernel indices `(k, r)` with `k ≤ K` and `r < 2ᵏ`. -/
def kernelIndex (K : ℕ) : Finset (ℕ × ℕ) :=
  ((Finset.range (K + 1)) ×ˢ (Finset.range (2 ^ K))).filter fun x => x.2 < 2 ^ x.1

theorem kernelIndex_card_9 : (kernelIndex 9).card = 1023 := by native_decide

theorem kernel_distinct_9 : ∀ x ∈ kernelIndex 9, ∀ y ∈ kernelIndex 9, x ≠ y →
    ∃ n < 40, 2 ^ x.1 * n + x.2 < 20000 ∧ 2 ^ y.1 * n + y.2 < 20000 ∧
      arr20000.getD (2 ^ x.1 * n + x.2) false ≠ arr20000.getD (2 ^ y.1 * n + y.2) false := by
  native_decide

/-- **The 2-kernel of the centre column has at least 1023 elements**: all decimations
`n ↦ a(2ᵏ n + r)` with `k ≤ 9` are pairwise distinct. -/
theorem twoKernel_centerCol_ge : (1023 : ℕ∞) ≤ (TwoKernel centerCol).encard := by
  have h := card_le_encard_twoKernel (a := centerCol) (kernelIndex 9)
    (fun x hx => (Finset.mem_filter.1 hx).2) fun x hx y hy hxy => by
      obtain ⟨n, -, h1, h2, hne⟩ := kernel_distinct_9 x hx y hy hxy
      exact ⟨n, by rwa [← arr20000_getD _ h1, ← arr20000_getD _ h2]⟩
  rwa [kernelIndex_card_9] at h

/-- **The Round 23 frontier**, collected. -/
theorem frontier_powerSeries :
    (Problem1 ↔ LCUnbounded centerCol) ∧
    (Problem1 ↔ ∀ n, n + 1 ≤ complexity centerCol n) ∧
    (CentreNotTwoAutomatic → Problem1) ∧
    ((∀ N, ∃ M ≥ N, (hankel centerCol M).det ≠ 0) → Problem1) ∧
    10000 ≤ lcProfile centerCol 19999 ∧
    (1023 : ℕ∞) ≤ (TwoKernel centerCol).encard ∧
    (∀ d T, 1 ≤ T → T < d → RunCount 2 d T = 2 ^ (d + 1)) :=
  ⟨problem1_iff_lcUnbounded, problem1_iff_complexity, problem1_of_centreNotTwoAutomatic,
    problem1_of_hankel_infinitely_often, lcProfile_centerCol_19999, twoKernel_centerCol_ge,
    runCount_two_law⟩

end GLM.Rule30
