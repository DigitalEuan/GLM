import RequestProject.GLM.Rule30.DiagCert

/-!
# Round 35 certificate: period 2, slack 5, code lengths `35 ≤ d ≤ 42`

(Not a `module`: the checks use `native_decide`.)  The diagonal search (`DiagonalSearch.lean`)
for the three non-white period-2 words; together with the Round 34 certificate on `d ≤ 34` this
gives `TestCountLinearUpTo 2 5 42` (assembled in `DiagonalSearchData.lean`).
-/

namespace GLM.Rule30.DiagCert

theorem intervalCheck_two_1 : tcIntervalCheckD 2 1 5 35 42 = true := by native_decide
theorem intervalCheck_two_2 : tcIntervalCheckD 2 2 5 35 42 = true := by native_decide
theorem intervalCheck_two_3 : tcIntervalCheckD 2 3 5 35 42 = true := by native_decide

end GLM.Rule30.DiagCert
