import RequestProject.GLM.Rule30.TestCountLaw

/-!
# Round 33 certificates: the test-count law for periods 1–4

(Not a `module`: the checks use `native_decide`.)

For each period `p ≤ 4` this file determines the least slack `c_p` of the per-period test-count
law `TestCountLinear p c` (`TestCountLaw.lean`) on the code lengths `d ≤ 22`:

| period `p` | `c_p` on `d ≤ 22` | refuting witness for `c_p − 1` (word, `d`, code) |
|---|---|---|
| 1 | 2 (FORMAL for every `d`: `testCountLinear_one`) | `1`, `d = 2`, `S = 2` |
| 2 | 5 | `10`, `d = 11`, `S = 1493` |
| 3 | 8 | `100`, `d = 22`, `S = 4161297` |
| 4 | 5 | `1010`, `d = 11`, `S = 1493` |

**Correction found later in Round 33:** the period-4 slack on *all* `d` is at least 7 — the code
`974520100` (`d = 30`) passes 36 tests of the word `0111` (`not_testCountLinear_four_six`).  The
range `d ≤ 22` was too short to see it.

* **Survival on the range** (CERT): every code of length `d ≤ 22` fails within `d + c_p` tests of
  every non-white word of period `p` (`testCountLinearUpTo_two` … `_four`, by the sound prefix
  search of `PrefixSearch.lean` run to the time of the `(d + c_p)`-th test).
* **Sharpness** (FORMAL, one simulation each): `TestCountLinear p (c_p − 1)` is false *for all
  `d`*, refuted by the listed code, which passes all of its first `d + c_p − 1` tests
  (`not_testCountLinear_one_one` … `not_testCountLinear_four_four`).

So, on each range, the slack is exactly `c_p`; the refutations hold outright.  The ordinary-clock
view of the same data is the per-word slope `p / (black cells of the word)`
(`scripts/word_lifetimes33_output.txt`, EMP).  `frontier_round33` collects the round.
-/

namespace GLM.Rule30.TestCountData

open GLM.Rule30

/-- The time just before the `(n+1)`-th test: walk forward while the test count stays `≤ n`. -/
def testHorizonAux (bd : ℕ → Bool) (n : ℕ) : ℕ → ℕ → ℕ → ℕ
  | 0, t, _ => t
  | fuel + 1, t, cnt =>
    if cnt + (bd t).toNat ≤ n then testHorizonAux bd n fuel (t + 1) (cnt + (bd t).toNat) else t

/-- The horizon used by the certificate (its test count is re-checked, so no specification of
`testHorizonAux` is needed). -/
def testHorizon (p k n : ℕ) : ℕ := testHorizonAux (driveN p k) n (p * (n + 1) + 1) 0 0

/-- The per-word check: the horizon has at most `d + c` tests before it, and the prefix search
kills every code of length `d` before it. -/
def tcWordCheck (p k d c : ℕ) : Bool :=
  decide (testsBefore (driveN p k) (testHorizon p k (d + c)) ≤ d + c) &&
    prefixSearch (driveN p k) (testHorizon p k (d + c)) (d - 1) 0 0

/-- The range check for period `p`: every non-white word, every `1 ≤ d ≤ D`. -/
def tcCheck (p c D : ℕ) : Bool :=
  (List.range (2 ^ p - 1)).all fun j =>
    (List.range D).all fun i => tcWordCheck p (j + 1) (i + 1) c

/-- `TestCountLinear p c` on the code lengths `d ≤ D`. -/
def TestCountLinearUpTo (p c D : ℕ) : Prop :=
  ∀ k, 0 < k → k < 2 ^ p → ∀ d S, 1 ≤ d → d ≤ D → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
    FailsWithinTests (driveN p k) S (d + c)

theorem testCountLinearUpTo_of_tcCheck {p c D : ℕ} (h : tcCheck p c D = true) :
    TestCountLinearUpTo p c D := by
  intro k hk0 hk d S hd hdD h1 h2
  have hw := List.all_eq_true.1 (List.all_eq_true.1 h (k - 1) (List.mem_range.2 (by
    have : 1 ≤ 2 ^ p := Nat.one_le_two_pow; omega))) (d - 1) (List.mem_range.2 (by omega))
  rw [show k - 1 + 1 = k by omega, show d - 1 + 1 = d by omega] at hw
  simp only [tcWordCheck, Bool.and_eq_true, decide_eq_true_eq] at hw
  exact failsWithinTests_of_dDiesBy (dDiesBy_of_prefixSearch hd hw.2 h1 h2) hw.1

/-- **One code refutes a per-period law**: if it passes every check before `T` and `T` has at
least `d + c` tests before it, then `TestCountLinear p c` is false. -/
theorem not_testCountLinear_of_witness {p c k d S T : ℕ} (hk0 : 0 < k) (hk : k < 2 ^ p)
    (hd : 1 ≤ d) (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d)
    (hw : dDiesBy (driveN p k) S T = false) (hT : d + c ≤ testsBefore (driveN p k) T) :
    ¬ TestCountLinear p c := fun h =>
  not_failsWithinTests_of_dDiesBy hw hT (h k hk0 hk d S hd h1 h2)

/-! ## Survival on the range (CERT) -/

theorem tcCheck_two : tcCheck 2 5 22 = true := by native_decide
theorem tcCheck_three : tcCheck 3 8 22 = true := by native_decide
theorem tcCheck_four : tcCheck 4 5 22 = true := by native_decide

theorem testCountLinearUpTo_two : TestCountLinearUpTo 2 5 22 :=
  testCountLinearUpTo_of_tcCheck tcCheck_two
theorem testCountLinearUpTo_three : TestCountLinearUpTo 3 8 22 :=
  testCountLinearUpTo_of_tcCheck tcCheck_three
theorem testCountLinearUpTo_four : TestCountLinearUpTo 4 5 22 :=
  testCountLinearUpTo_of_tcCheck tcCheck_four

/-! ## Sharpness: the slack one smaller is false for all `d` -/

theorem wit_1 : dDiesBy (driveN 1 1) 2 3 = false ∧ 3 ≤ testsBefore (driveN 1 1) 3 := by
  native_decide
theorem wit_2 : dDiesBy (driveN 2 1) 1493 30 = false ∧ 15 ≤ testsBefore (driveN 2 1) 30 := by
  native_decide
theorem wit_3 : dDiesBy (driveN 3 1) 4161297 87 = false ∧ 29 ≤ testsBefore (driveN 3 1) 87 := by
  native_decide
theorem wit_4 : dDiesBy (driveN 4 5) 1493 30 = false ∧ 15 ≤ testsBefore (driveN 4 5) 30 := by
  native_decide

theorem not_testCountLinear_one_one : ¬ TestCountLinear 1 1 :=
  not_testCountLinear_of_witness (k := 1) (d := 2) (S := 2) (by norm_num) (by norm_num)
    (by norm_num) (by norm_num) (by norm_num) wit_1.1 wit_1.2

theorem not_testCountLinear_two_four : ¬ TestCountLinear 2 4 :=
  not_testCountLinear_of_witness (k := 1) (d := 11) (S := 1493) (by norm_num) (by norm_num)
    (by norm_num) (by norm_num) (by norm_num) wit_2.1 wit_2.2

theorem not_testCountLinear_three_seven : ¬ TestCountLinear 3 7 :=
  not_testCountLinear_of_witness (k := 1) (d := 22) (S := 4161297) (by norm_num) (by norm_num)
    (by norm_num) (by norm_num) (by norm_num) wit_3.1 wit_3.2

theorem not_testCountLinear_four_four : ¬ TestCountLinear 4 4 :=
  not_testCountLinear_of_witness (k := 5) (d := 11) (S := 1493) (by norm_num) (by norm_num)
    (by norm_num) (by norm_num) (by norm_num) wit_4.1 wit_4.2

/-! ## A longer code: the period-4 slack is not 5

The range `d ≤ 22` does not show the whole law.  Found by `scripts/word_lifetimes33.c` (every
period-4 word to `d = 32`): the code `974520100` of length 30 passes the first 36 tests of the word
`0111` (`driveN 4 14`) and fails its 37th test, at time 49.  So period 4 needs slack at least 7,
although slack 5 holds on `d ≤ 22`. -/

theorem wit_4_long :
    dDiesBy (driveN 4 14) 974520100 49 = false ∧ 36 ≤ testsBefore (driveN 4 14) 49 := by
  native_decide

theorem not_testCountLinear_four_six : ¬ TestCountLinear 4 6 :=
  not_testCountLinear_of_witness (k := 14) (d := 30) (S := 974520100) (by norm_num) (by norm_num)
    (by norm_num) (by norm_num) (by norm_num) wit_4_long.1 wit_4_long.2

/-- **Round 33 frontier.**  Period 1 is settled with the exact slack `2`; for periods 2, 3, 4 the
least slack on `d ≤ 22` is `5, 8, 5`, and each smaller slack is refuted for all `d`; the uniform
(period-free) law is refuted; any per-period law gives the rung of that period. -/
theorem frontier_round33 :
    (TestCountLinear 1 2 ∧ ¬ TestCountLinear 1 1) ∧
    (TestCountLinearUpTo 2 5 22 ∧ ¬ TestCountLinear 2 4) ∧
    (TestCountLinearUpTo 3 8 22 ∧ ¬ TestCountLinear 3 7) ∧
    (TestCountLinearUpTo 4 5 22 ∧ ¬ TestCountLinear 4 4) ∧
    (∀ g, ¬ TestCountBound g) ∧
    (∀ p c, TestCountLinear p c → HalfLineDies p) :=
  ⟨⟨testCountLinear_one, not_testCountLinear_one_one⟩,
    ⟨testCountLinearUpTo_two, not_testCountLinear_two_four⟩,
    ⟨testCountLinearUpTo_three, not_testCountLinear_three_seven⟩,
    ⟨testCountLinearUpTo_four, not_testCountLinear_four_four⟩,
    not_testCountBound, fun _ _ h => halfLineDies_of_testCountLinear h⟩

end GLM.Rule30.TestCountData
