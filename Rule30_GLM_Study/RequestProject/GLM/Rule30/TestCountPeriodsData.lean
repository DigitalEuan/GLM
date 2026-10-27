import RequestProject.GLM.Rule30.TestCountPeriods
import RequestProject.GLM.Rule30.SlackCertFour1
import RequestProject.GLM.Rule30.SlackCertFour2
import RequestProject.GLM.Rule30.SlackCertFour4
import RequestProject.GLM.Rule30.SlackCertFour8
import RequestProject.GLM.Rule30.SlackCertFourRest
import RequestProject.GLM.Rule30.SlackCertThreeTwo

/-!
# Round 34 certificates: the observer-clock slack of periods 2, 3, 4 on longer ranges

(Not a `module`: it assembles the `native_decide` checks of the `SlackCert*.lean` files; the
period-4 words are checked one file per expensive word so that they build in parallel.)

To Do 35 asked whether period 4 has a finite observer-clock slack at all, after Round 33 found
that the slack `5` certified on `d ≤ 22` is broken at `d = 30` (the code `974520100` passes 36
tests of the word `0111`, `not_testCountLinear_four_six`).

* **CERT** `testCountLinearUpTo_four_seven`: every code of length `d ≤ 30` fails within `d + 7`
  tests of **every** non-white word of period 4.  With `not_testCountLinear_four_six` the least
  period-4 slack on `d ≤ 30` is exactly `7`.
* **CERT** `testCountLinearUpTo_three_eight_long`, `testCountLinearUpTo_two_five_long`: the
  Round 33 slacks `8` (period 3) and `5` (period 2) persist to `d ≤ 28` and `d ≤ 34`.
* **FORMAL, from `TestCountPeriods.lean`**: each refutation passes to every multiple of its
  period (`not_testCountLinear_mul_two`, `_mul_three`, `_mul_four`).

EMP (exact exhaustive search, study folder `rule30_round34/test_slack34.c` and
`test_slack34_output.txt`): no period-4 word exceeds slack 7 on `d ≤ 37` (all 15 words); the
three-black words `0111, 1110, 1101, 1011` (among them the record word `0111`) stay within 7 up
to `d ≥ 102`, and on the upper half of their searched ranges their excess is at most 3 (it drifts
*downwards*).  This
supports a finite period-4 slack (`TestCountLinear 4 7`) but does not prove it.
-/

namespace GLM.Rule30.TestCountPeriodsData

open GLM.Rule30 GLM.Rule30.TestCountData

/-! ## Survival on the longer ranges (CERT) -/

open GLM.Rule30.SlackCert in
theorem testCountLinearUpTo_four_seven : TestCountLinearUpTo 4 7 30 := by
  apply testCountLinearUpTo_of_rangeChecks
  intro k hk0 hk
  have hr := rangeCheck_four_rest
  simp only [Bool.and_eq_true] at hr
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨h3, h5⟩, h6⟩, h7⟩, h9⟩, h10⟩, h11⟩, h12⟩, h13⟩, h14⟩, h15⟩ := hr
  have hk' : k < 16 := hk
  interval_cases k
  exacts [rangeCheck_four_1, rangeCheck_four_2, h3, rangeCheck_four_4, h5, h6, h7,
    rangeCheck_four_8, h9, h10, h11, h12, h13, h14, h15]

theorem testCountLinearUpTo_three_eight_long : TestCountLinearUpTo 3 8 28 :=
  testCountLinearUpTo_of_tcCheck SlackCert.tcCheck_three_eight_long
theorem testCountLinearUpTo_two_five_long : TestCountLinearUpTo 2 5 34 :=
  testCountLinearUpTo_of_tcCheck SlackCert.tcCheck_two_five_long

/-! ## Refutations pass to multiples of the period (FORMAL) -/

theorem not_testCountLinear_mul_two (m : ℕ) (hm : 0 < m) : ¬ TestCountLinear (2 * m) 4 :=
  not_testCountLinear_of_dvd (Dvd.intro m rfl) (by omega) not_testCountLinear_two_four

theorem not_testCountLinear_mul_three (m : ℕ) (hm : 0 < m) : ¬ TestCountLinear (3 * m) 7 :=
  not_testCountLinear_of_dvd (Dvd.intro m rfl) (by omega) not_testCountLinear_three_seven

theorem not_testCountLinear_mul_four (m : ℕ) (hm : 0 < m) : ¬ TestCountLinear (4 * m) 6 :=
  not_testCountLinear_of_dvd (Dvd.intro m rfl) (by omega) not_testCountLinear_four_six

/-- **Round 34 frontier.**  On the observer's clock:
* the least period-4 slack on `d ≤ 30` is exactly `7` (it was `5` on `d ≤ 22`);
* the period-3 slack `8` and the period-2 slack `5` persist to `d ≤ 28` and `d ≤ 34`;
* per-period laws pass to divisors of the period, refutations to multiples; in particular every
  period divisible by 4 needs slack at least 7 and every period divisible by 3 at least 8. -/
theorem frontier_round34 :
    (TestCountLinearUpTo 4 7 30 ∧ ¬ TestCountLinear 4 6) ∧
    (TestCountLinearUpTo 3 8 28 ∧ ¬ TestCountLinear 3 7) ∧
    (TestCountLinearUpTo 2 5 34 ∧ ¬ TestCountLinear 2 4) ∧
    (∀ p q c, p ∣ q → 0 < q → TestCountLinear q c → TestCountLinear p c) ∧
    (∀ p q, p ∣ q → 0 < q → HalfLineDies q → HalfLineDies p) ∧
    (∀ m, 0 < m → ¬ TestCountLinear (4 * m) 6 ∧ ¬ TestCountLinear (3 * m) 7 ∧
      ¬ TestCountLinear (2 * m) 4) :=
  ⟨⟨testCountLinearUpTo_four_seven, not_testCountLinear_four_six⟩,
    ⟨testCountLinearUpTo_three_eight_long, not_testCountLinear_three_seven⟩,
    ⟨testCountLinearUpTo_two_five_long, not_testCountLinear_two_four⟩,
    fun _ _ _ h hq => testCountLinear_of_dvd h hq,
    fun _ _ h hq => halfLineDies_of_dvd h hq,
    fun m hm => ⟨not_testCountLinear_mul_four m hm, not_testCountLinear_mul_three m hm,
      not_testCountLinear_mul_two m hm⟩⟩

end GLM.Rule30.TestCountPeriodsData
