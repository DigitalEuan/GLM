import RequestProject.GLM.Rule30.TestCountLawData

/-!
# Round 34: per-word slack certificates (shared definitions)

(Not a `module`: it builds on `TestCountLawData.lean`, whose checks use `native_decide`.)

`tcRangeCheck p k c D` runs the Round 33 per-word check `tcWordCheck` (sound prefix search to
the time of the `(d + c)`-th test) for one drive word `k` and every code length `1 ≤ d ≤ D`.
Checking the words one by one lets the expensive words (one black cell per period) be certified
in separate files, which build in parallel (`SlackCertFour1.lean`, …).
`testCountLinearUpTo_of_rangeChecks` assembles the per-word checks into `TestCountLinearUpTo`.
-/

namespace GLM.Rule30.SlackCert

open GLM.Rule30 GLM.Rule30.TestCountData

/-- The per-word range check: `tcWordCheck p k d c` for every `1 ≤ d ≤ D`. -/
def tcRangeCheck (p k c D : ℕ) : Bool :=
  (List.range D).all fun i => tcWordCheck p k (i + 1) c

/-- **Assembling per-word checks.** -/
theorem testCountLinearUpTo_of_rangeChecks {p c D : ℕ}
    (h : ∀ k, 0 < k → k < 2 ^ p → tcRangeCheck p k c D = true) :
    TestCountLinearUpTo p c D := by
  intro k hk0 hk d S hd hdD h1 h2
  have hw := List.all_eq_true.1 (h k hk0 hk) (d - 1) (List.mem_range.2 (by omega))
  rw [show d - 1 + 1 = d by omega] at hw
  simp only [tcWordCheck, Bool.and_eq_true, decide_eq_true_eq] at hw
  exact failsWithinTests_of_dDiesBy (dDiesBy_of_prefixSearch hd hw.2 h1 h2) hw.1

end GLM.Rule30.SlackCert
