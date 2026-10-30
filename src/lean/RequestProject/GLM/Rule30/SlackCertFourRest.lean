import RequestProject.GLM.Rule30.SlackCert

/-!
# Round 34 certificate: the other eleven period-4 words, slack 7, `d ≤ 30`

(Not a `module`: the checks use `native_decide`.)  The words with two or more black cells per
period (`k = 3, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15`).  Assembled in `TestCountPeriodsData.lean`.
-/

namespace GLM.Rule30.SlackCert

theorem rangeCheck_four_rest :
    (tcRangeCheck 4 3 7 30 && tcRangeCheck 4 5 7 30 && tcRangeCheck 4 6 7 30 &&
      tcRangeCheck 4 7 7 30 && tcRangeCheck 4 9 7 30 && tcRangeCheck 4 10 7 30 &&
      tcRangeCheck 4 11 7 30 && tcRangeCheck 4 12 7 30 && tcRangeCheck 4 13 7 30 &&
      tcRangeCheck 4 14 7 30 && tcRangeCheck 4 15 7 30) = true := by native_decide

end GLM.Rule30.SlackCert
