import RequestProject.GLM.HypothesisEngine.TaxChecks
import RequestProject.GLM.Rule30.LeftDiagonalPeriodsData

/-!
# Round 42: where TAX is conserved on Rule 30's left diagonals (certificate)

(Not a `module`: it uses `native_decide`, like `LeftDiagonalPeriodsData.lean`.)

Engine v13 ends its TAX section with the claim that the interesting boundary is "where TAX is
CONSERVED (only at the white diagonals, which are exactly the period-doubling inputs)". This
file checks that claim on the exact eventual patterns of the left diagonals `D < 400`.

Every left diagonal `D < 400` is `8`-periodic from time `501` (`leftDiag_period_eight_below_400`),
so the window `[501, 509)` holds one full eventual period of each of them. On these windows:

* `tax_conserved_pairs_below_400` : the pairs `(D − 1, D)` with `2 ≤ D < 400` that are
  TAX-conserved are exactly the `25` listed diagonals;
* `tax_conserved_nontrivial_below_400` : `15` of them have **two black, different** patterns (for
  example `D = 33`: weights `3, 3`, overlap `1`), so they are neither "white" nor "equal";
* `tax_conserved_not_only_white` : hence "TAX is conserved only at the white diagonals" is false
  on Rule 30 itself.

Of the `25` conserved pairs, `7` have a white member (`D = 2, 3, 7, 8, 28, 29, 399`), `3` have
equal patterns (`D = 6, 27, 398`) and `15` are neither. Below `6000` the engine's own profile gives
`116` conserved pairs, only `8` of them with a white member (study folder `rule30_round42/`, EMP).
-/

namespace GLM.HypothesisEngine.Tax

open GLM.Rule30

/-- The eventual pattern of left diagonal `D < 400` (one period, from time `501`). -/
def evPattern400 (D : ℕ) : Finset ℕ := windowPattern (ldiag D) 501 8

/-- The same pattern read off the packed row (computable). -/
def evPattern400' (D : ℕ) : Finset ℕ :=
  (Finset.range 8).filter (fun i => (lrow 400 (501 + i)).testBit D = true)

theorem evPattern400_eq {D : ℕ} (hD : D < 400) : evPattern400 D = evPattern400' D := by
  unfold evPattern400 evPattern400' windowPattern
  refine Finset.filter_congr (fun i _ => ?_)
  rw [testBit_lrow hD]

/-- The `25` TAX-conserved consecutive pairs below `400`. -/
def conservedBelow400 : Finset ℕ :=
  {2, 3, 6, 7, 8, 27, 28, 29, 33, 36, 54, 92, 102, 125, 156, 161, 184, 191, 213, 268, 293,
    376, 381, 398, 399}

theorem conserved_check :
    (Finset.Ico 2 400).filter (fun D => taxDefect (evPattern400' D) (evPattern400' (D - 1)) = 0)
      = conservedBelow400 := by
  native_decide

/-- **The TAX-conserved pairs below `400`.** For `2 ≤ D < 400`, the eventual patterns of left
diagonals `D` and `D − 1` are TAX-conserved (for any `Y`) exactly when `D` is in the list. -/
theorem tax_conserved_pairs_below_400 (Y : ℝ) {D : ℕ} (h2 : 2 ≤ D) (hD : D < 400) :
    TaxConserved Y (evPattern400 D) (evPattern400 (D - 1)) ↔ D ∈ conservedBelow400 := by
  rw [tax_conserved_iff_defect_zero, evPattern400_eq hD, evPattern400_eq (by omega),
    ← conserved_check, Finset.mem_filter, Finset.mem_Ico]
  tauto

/-- The conserved pairs below `400` with two black, different patterns. -/
def nontrivialBelow400 : Finset ℕ :=
  {33, 36, 54, 92, 102, 125, 156, 161, 184, 191, 213, 268, 293, 376, 381}

theorem nontrivial_check :
    conservedBelow400.filter (fun D => evPattern400' D ≠ ∅ ∧ evPattern400' (D - 1) ≠ ∅ ∧
      evPattern400' D ≠ evPattern400' (D - 1)) = nontrivialBelow400 := by
  native_decide

/-- **15 conserved pairs are neither white nor equal.** Each `D` in the list has a conserved pair
`(D − 1, D)` in which both eventual patterns are non-white and different. -/
theorem tax_conserved_nontrivial_below_400 (Y : ℝ) {D : ℕ} (hD : D ∈ nontrivialBelow400) :
    TaxConserved Y (evPattern400 D) (evPattern400 (D - 1)) ∧
      evPattern400 D ≠ ∅ ∧ evPattern400 (D - 1) ≠ ∅ ∧ evPattern400 D ≠ evPattern400 (D - 1) := by
  have hmem : D ∈ conservedBelow400 ∧ (evPattern400' D ≠ ∅ ∧ evPattern400' (D - 1) ≠ ∅ ∧
      evPattern400' D ≠ evPattern400' (D - 1)) := by
    have hD' := hD
    rw [← nontrivial_check] at hD'
    exact Finset.mem_filter.1 hD'
  have hr : 2 ≤ D ∧ D < 400 := by
    revert hD; unfold nontrivialBelow400; simp only [Finset.mem_insert, Finset.mem_singleton]
    omega
  rw [evPattern400_eq hr.2, evPattern400_eq (by omega)]
  refine ⟨?_, hmem.2⟩
  rw [← evPattern400_eq hr.2, ← evPattern400_eq (by omega)]
  exact (tax_conserved_pairs_below_400 Y hr.1 hr.2).2 hmem.1

theorem card_nontrivialBelow400 : nontrivialBelow400.card = 15 := by decide

/-- A sequence that is `Q`-periodic from `T` and has a black cell in the window `[T, T + Q)` is
not eventually white. -/
theorem not_eventuallyWhite_of_window {s : ℕ → Bool} {T Q : ℕ}
    (hper : ∀ t ≥ T, s (t + Q) = s t) (hne : windowPattern s T Q ≠ ∅) : ¬ EventuallyWhite s := by
  obtain ⟨i, hi⟩ := Finset.nonempty_iff_ne_empty.2 hne
  simp only [windowPattern, Finset.mem_filter, Finset.mem_range] at hi
  have hrep : ∀ k, s (T + i + Q * k) = true := by
    intro k
    induction k with
    | zero => simpa using hi.2
    | succ k ih =>
      rw [Nat.mul_succ, ← Nat.add_assoc, hper _ (by omega), ih]
  rintro ⟨T', hT'⟩
  have h1 := hrep T'
  have hQ : 1 ≤ Q := by omega
  rw [hT' _ (by nlinarith)] at h1
  exact absurd h1 (by decide)

/-- **"TAX is conserved only at the white diagonals" is false on Rule 30.** Diagonals `32` and
`33` are both non-white, have different eventual patterns, and are TAX-conserved. -/
theorem tax_conserved_not_only_white (Y : ℝ) :
    TaxConserved Y (evPattern400 33) (evPattern400 32) ∧
      ¬ EventuallyWhite (ldiag 33) ∧ ¬ EventuallyWhite (ldiag 32) ∧
      evPattern400 33 ≠ evPattern400 32 := by
  obtain ⟨hc, hne, hne', hdiff⟩ := tax_conserved_nontrivial_below_400 Y (D := 33) (by decide)
  refine ⟨hc, ?_, ?_, hdiff⟩
  · exact not_eventuallyWhite_of_window
      (fun t ht => leftDiag_period_eight_below_400 33 (by norm_num) t ht) hne
  · exact not_eventuallyWhite_of_window
      (fun t ht => leftDiag_period_eight_below_400 32 (by norm_num) t ht) hne'

end GLM.HypothesisEngine.Tax
