import RequestProject.GLM.Rule30.DiagonalSearch
import RequestProject.GLM.Rule30.TestCountLawData

/-!
# Round 35: per-word slack certificates with the diagonal search (shared definitions)

(Not a `module`: it builds on `TestCountLawData.lean`, whose checks use `native_decide`.)

The same per-word check as Round 34 (`SlackCert.lean`), with the prefix search replaced by the
verified diagonal search of `DiagonalSearch.lean` (To Do 37).  The range is now an interval
`lo ≤ d ≤ hi`, so a new certificate only has to cover the code lengths beyond an existing one:

* `tcWordCheckD p k d c` — the horizon of the `(d + c)`-th test has at most `d + c` tests before
  it, and the diagonal search kills every code of length `d` before it;
* `tcIntervalCheckD p k c lo hi` — `tcWordCheckD` for every `lo ≤ d ≤ hi`;
* **`testCountLinearUpTo_extend`** — a certificate on `d ≤ D₀` and interval checks on
  `D₀ < d ≤ D` for every non-white word give the certificate on `d ≤ D`.
-/

namespace GLM.Rule30.DiagCert

open GLM.Rule30 GLM.Rule30.TestCountData

/-- The per-word check with the diagonal search. -/
def tcWordCheckD (p k d c : ℕ) : Bool :=
  decide (testsBefore (driveN p k) (testHorizon p k (d + c)) ≤ d + c) &&
    diagSearch (driveN p k) (testHorizon p k (d + c)) (d - 1) 0 0 0

/-- The per-word check for every code length `lo ≤ d ≤ hi`. -/
def tcIntervalCheckD (p k c lo hi : ℕ) : Bool :=
  (List.range (hi + 1 - lo)).all fun i => tcWordCheckD p k (lo + i) c

/-- **Soundness of one per-word check.** -/
theorem failsWithinTests_of_tcWordCheckD {p k d c S : ℕ} (hd : 1 ≤ d)
    (h : tcWordCheckD p k d c = true) (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) :
    FailsWithinTests (driveN p k) S (d + c) := by
  simp only [tcWordCheckD, Bool.and_eq_true, decide_eq_true_eq] at h
  exact failsWithinTests_of_dDiesBy (dDiesBy_of_diagSearch hd h.2 h1 h2) h.1

/-- **Extending a certificate.** -/
theorem testCountLinearUpTo_extend {p c D₀ D : ℕ} (h₀ : TestCountLinearUpTo p c D₀)
    (h : ∀ k, 0 < k → k < 2 ^ p → tcIntervalCheckD p k c (D₀ + 1) D = true) :
    TestCountLinearUpTo p c D := by
  intro k hk0 hk d S hd hdD h1 h2
  rcases le_or_gt d D₀ with hd0 | hd0
  · exact h₀ k hk0 hk d S hd hd0 h1 h2
  · have hw := List.all_eq_true.1 (h k hk0 hk) (d - (D₀ + 1)) (List.mem_range.2 (by omega))
    rw [show D₀ + 1 + (d - (D₀ + 1)) = d by omega] at hw
    exact failsWithinTests_of_tcWordCheckD hd hw h1 h2

end GLM.Rule30.DiagCert
