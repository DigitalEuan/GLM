import RequestProject.GLM.Rule30.DiagCert

/-!
# Round 35 certificate: the other eleven period-4 words, slack 7, code lengths `31 ≤ d ≤ 32`

(Not a `module`: the check uses `native_decide`.)  The non-white period-4 words with at least two
black cells.  Assembled in `DiagonalSearchData.lean`.
-/

namespace GLM.Rule30.DiagCert

theorem intervalCheck_four_rest :
    (tcIntervalCheckD 4 3 7 31 32 && tcIntervalCheckD 4 5 7 31 32 &&
      tcIntervalCheckD 4 6 7 31 32 && tcIntervalCheckD 4 7 7 31 32 &&
      tcIntervalCheckD 4 9 7 31 32 && tcIntervalCheckD 4 10 7 31 32 &&
      tcIntervalCheckD 4 11 7 31 32 && tcIntervalCheckD 4 12 7 31 32 &&
      tcIntervalCheckD 4 13 7 31 32 && tcIntervalCheckD 4 14 7 31 32 &&
      tcIntervalCheckD 4 15 7 31 32) = true := by native_decide

end GLM.Rule30.DiagCert
