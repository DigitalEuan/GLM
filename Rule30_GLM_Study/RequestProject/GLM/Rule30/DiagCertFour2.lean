import RequestProject.GLM.Rule30.DiagCert

/-!
# Round 35 certificate: period-4 word `k = 2`, slack 7, code lengths `31 ≤ d ≤ 32`

(Not a `module`: the check uses `native_decide`.)  One of the four one-black period-4 words, the
expensive ones; certified in its own file so the words build in parallel.  Together with the
Round 34 certificate on `d ≤ 30` this gives `TestCountLinearUpTo 4 7 32` (assembled in
`DiagonalSearchData.lean`).
-/

namespace GLM.Rule30.DiagCert

theorem intervalCheck_four_2 : tcIntervalCheckD 4 2 7 31 32 = true := by native_decide

end GLM.Rule30.DiagCert
