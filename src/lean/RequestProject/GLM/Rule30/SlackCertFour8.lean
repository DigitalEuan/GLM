import RequestProject.GLM.Rule30.SlackCert

/-!
# Round 34 certificate: period-4 word `k = 8`, slack 7, `d ≤ 30`

(Not a `module`: the check uses `native_decide`.)  One of the four one-black period-4 words,
the most expensive ones for the prefix search; certified in its own file so the words build in
parallel.  Assembled in `TestCountPeriodsData.lean`.
-/

namespace GLM.Rule30.SlackCert

theorem rangeCheck_four_8 : tcRangeCheck 4 8 7 30 = true := by native_decide

end GLM.Rule30.SlackCert
