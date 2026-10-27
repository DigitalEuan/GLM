import RequestProject.GLM.Rule30.DiagCert

/-!
# Round 35 certificate: period 3, slack 8, code lengths `29 ≤ d ≤ 32`

(Not a `module`: the checks use `native_decide`.)  The diagonal search (`DiagonalSearch.lean`)
for the seven non-white period-3 words; together with the Round 34 certificate on `d ≤ 28` this
gives `TestCountLinearUpTo 3 8 32` (assembled in `DiagonalSearchData.lean`).
-/

namespace GLM.Rule30.DiagCert

theorem intervalCheck_three_1 : tcIntervalCheckD 3 1 8 29 32 = true := by native_decide
theorem intervalCheck_three_2 : tcIntervalCheckD 3 2 8 29 32 = true := by native_decide
theorem intervalCheck_three_4 : tcIntervalCheckD 3 4 8 29 32 = true := by native_decide
theorem intervalCheck_three_rest :
    (tcIntervalCheckD 3 3 8 29 32 && tcIntervalCheckD 3 5 8 29 32 &&
      tcIntervalCheckD 3 6 8 29 32 && tcIntervalCheckD 3 7 8 29 32) = true := by native_decide

end GLM.Rule30.DiagCert
