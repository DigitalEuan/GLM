import RequestProject.GLM.Rule30.SlackCert

/-!
# Round 34 certificates: periods 3 and 2 on longer ranges

(Not a `module`: the checks use `native_decide`.)  Period 3 with slack 8 on `d ≤ 28` and period 2
with slack 5 on `d ≤ 34`, every non-white word.  Assembled in `TestCountPeriodsData.lean`.
-/

namespace GLM.Rule30.SlackCert

open GLM.Rule30.TestCountData

theorem tcCheck_three_eight_long : tcCheck 3 8 28 = true := by native_decide
theorem tcCheck_two_five_long : tcCheck 2 5 34 = true := by native_decide

end GLM.Rule30.SlackCert
