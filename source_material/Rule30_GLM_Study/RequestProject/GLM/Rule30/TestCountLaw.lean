module

public import RequestProject.GLM.Rule30.PrefixSearch
public import RequestProject.GLM.Rule30.ProofRoutes

/-!
# Round 33: the test-count law — count the column's questions, not the clock

The half-line machine (`HalfLineMachine.lean`) asks one question per **black** drive time: at a
black time `t` the cell next to the column must be `!bd (t + 1)` (`col_black_forces_left`).  At
white times it asks nothing.  So the machine has its own clock, which ticks once per test.  This
is the observer `Y`'s proper time: the column only "reads" the half-line when it is black.

Measured on that clock, the longest lives of different drive words line up (EMP,
`scripts/word_lifetimes33.c`): the word `1000` lives about `4d` steps and the word `1110`
about `1.3 d` (`lmax_ratio_word`), but both fail after about `d` **tests**.  For every word of
period `p ≤ 4` and every `d ≤ 32`, every code of length `d` fails within `d + 8` tests
(and the slack is `5, 8` for the words `10`, `100` up to `d = 44`).

This file states the observation as targets and settles what can be settled exactly.

* `testsBefore bd t` — the number of tests (black drive times) before time `t`;
  `FailsWithinTests bd S n` — the machine started from `S` fails one of its first `n` tests.
* `failsWithinTests_of_dDiesBy`, `not_failsWithinTests_of_dDiesBy` — the bridges to the
  time-based checks (`dDiesBy`), used by the certificates in `TestCountLawData.lean`.
* **The uniform form is false** (FORMAL, `not_testCountBound`): no slack function of the code
  length alone works for all periods.  A drive can be *steered* so that a code passes every check
  (`steer`, `steer_passes`), and cutting it after `p` steps gives a word of period `p` under which
  the code passes about `p / 2` tests (`exists_word_passing_tests`).
* **The per-period form** `TestCountLinear p c` (every code of length `d` fails within `d + c`
  tests of every non-white word of period `p`):
  * gives `HalfLineDies p` and the linear target `HalfLineLinear p p (p * c)`
    (`halfLineDies_of_testCountLinear`, `halfLineLinear_of_testCountLinear`), and for all periods
    Problem 1 (`problem1_of_testCountLinear`, the slack may depend on `p`);
  * needs a slack that grows with the period: `c ≥ m − 1` for `p = 2m + 1`
    (`testCountLinear_slack_ge`);
  * holds for period 1 with `c = 2` (`testCountLinear_one`, from `constDrive_dies`).

A word of period `p` tests at least once every `p` steps (`testsBefore_mul_ge`), which turns
test counts into times (`dDiesBy_of_failsWithinTests_driveN`).  Everything here is exact Boolean /
natural-number arithmetic; there are no finite checks.
-/

@[expose] public section

namespace GLM.Rule30

/-- The number of tests (black drive times) strictly before time `t`. -/
def testsBefore (bd : ℕ → Bool) : ℕ → ℕ
  | 0 => 0
  | t + 1 => testsBefore bd t + (bd t).toNat

theorem testsBefore_succ (bd : ℕ → Bool) (t : ℕ) :
    testsBefore bd (t + 1) = testsBefore bd t + (bd t).toNat := rfl

theorem testsBefore_mono (bd : ℕ → Bool) {s t : ℕ} (h : s ≤ t) :
    testsBefore bd s ≤ testsBefore bd t := by
  induction t, h using Nat.le_induction with
  | base => exact le_rfl
  | succ t _ ih => rw [testsBefore_succ]; omega

/-- A black time is followed by one more test. -/
theorem testsBefore_succ_of_black {bd : ℕ → Bool} {t : ℕ} (h : bd t = true) :
    testsBefore bd (t + 1) = testsBefore bd t + 1 := by
  rw [testsBefore_succ, h]; rfl

/-- The machine started from `S` fails one of its first `n` tests. -/
def FailsWithinTests (bd : ℕ → Bool) (S n : ℕ) : Prop :=
  ∃ t, bd t = true ∧ testsBefore bd t < n ∧ (halfStateD bd S t).testBit 0 = bd (t + 1)

/-- **The test-count law with slack `g`.**  For every period `p`, every non-white drive word `k`
of length `p` and every code `S` of length `d` (top bit `d - 1`), the driven half-line machine
fails within `d + g d` tests. -/
def TestCountBound (g : ℕ → ℕ) : Prop :=
  ∀ p k, 0 < k → k < 2 ^ p → ∀ d S, 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
    FailsWithinTests (driveN p k) S (d + g d)

/-- A failure within some number of tests is a failure before a finite time. -/
theorem dDiesBy_of_failsWithinTests {bd : ℕ → Bool} {S n : ℕ} (h : FailsWithinTests bd S n) :
    ∃ T, dDiesBy bd S T = true := by
  obtain ⟨t, hb, _, hf⟩ := h
  exact ⟨t + 1, (dDiesBy_spec bd S (t + 1)).2 ⟨t, by omega, hb, hf⟩⟩

/-- **Certificate bridge.** A failure before `T`, with at most `n` tests before `T`, is a failure
within `n` tests. -/
theorem failsWithinTests_of_dDiesBy {bd : ℕ → Bool} {S T n : ℕ} (h : dDiesBy bd S T = true)
    (hT : testsBefore bd T ≤ n) : FailsWithinTests bd S n := by
  obtain ⟨t, htT, hb, hf⟩ := (dDiesBy_spec bd S T).1 h
  refine ⟨t, hb, ?_, hf⟩
  have h1 := testsBefore_succ_of_black hb
  have h2 := testsBefore_mono bd (show t + 1 ≤ T by omega)
  omega

/-- **Witness bridge.** If the machine passes every check before `T` and at least `n` tests lie
before `T`, it does not fail within `n` tests. -/
theorem not_failsWithinTests_of_dDiesBy {bd : ℕ → Bool} {S T n : ℕ}
    (h : dDiesBy bd S T = false) (hT : n ≤ testsBefore bd T) : ¬ FailsWithinTests bd S n := by
  rintro ⟨t, hb, hn, hf⟩
  have htT : t < T := by
    by_contra hle
    have := testsBefore_mono bd (show T ≤ t by omega)
    omega
  have := (dDiesBy_spec bd S T).2 ⟨t, htT, hb, hf⟩
  rw [h] at this
  exact Bool.noConfusion this

/-! ## From tests to time: a word of period `p` tests at least once every `p` steps -/

/-- A non-white word of period `p` has at least `m + 1` tests before time `m * p + p`. -/
theorem testsBefore_mul_ge {p k : ℕ} (hk0 : 0 < k) (hk : k < 2 ^ p) (m : ℕ) :
    m + 1 ≤ testsBefore (driveN p k) (m * p + p) := by
  -- a black position `j < p` of the word
  obtain ⟨j, hj⟩ : ∃ j, k.testBit j = true := by
    by_contra hne
    push_neg at hne
    have : k = 0 := Nat.eq_of_testBit_eq fun i => by simpa using hne i
    omega
  have hjp : j < p := by
    by_contra hle
    have := Nat.testBit_eq_false_of_lt (lt_of_lt_of_le hk (Nat.pow_le_pow_right (by norm_num)
      (show p ≤ j by omega)))
    rw [hj] at this; exact Bool.noConfusion this
  have hblack : ∀ m, driveN p k (m * p + j) = true := fun m => by
    simp only [driveN]
    rw [show (m * p + j) % p = j by
      rw [Nat.add_comm, Nat.add_mul_mod_self_right]; exact Nat.mod_eq_of_lt hjp]
    exact hj
  induction m with
  | zero =>
    have h1 := testsBefore_succ_of_black (hblack 0)
    have h2 := testsBefore_mono (driveN p k) (show 0 * p + j + 1 ≤ 0 * p + p by omega)
    omega
  | succ m ih =>
    have h1 := testsBefore_succ_of_black (hblack (m + 1))
    have h2 := testsBefore_mono (driveN p k) (show m * p + p ≤ (m + 1) * p + j by
      rw [Nat.succ_mul]; omega)
    have h3 := testsBefore_mono (driveN p k) (show (m + 1) * p + j + 1 ≤ (m + 1) * p + p by omega)
    omega

/-- A failure within `n` tests of a non-white word of period `p` happens before time `p * n`. -/
theorem dDiesBy_of_failsWithinTests_driveN {p k S n : ℕ} (hk0 : 0 < k) (hk : k < 2 ^ p)
    (h : FailsWithinTests (driveN p k) S n) : dDiesBy (driveN p k) S (p * n) = true := by
  obtain ⟨t, hb, hn, hf⟩ := h
  refine (dDiesBy_spec _ S _).2 ⟨t, ?_, hb, hf⟩
  rcases Nat.eq_zero_or_pos n with rfl | hn0
  · omega
  by_contra hle
  have h1 := testsBefore_mul_ge hk0 hk (n - 1)
  have h2 := testsBefore_mono (driveN p k) (show (n - 1) * p + p ≤ t by
    have : (n - 1) * p + p = p * n := by
      rw [Nat.mul_comm p n]; cases n with
      | zero => omega
      | succ n => simp [Nat.succ_mul]
    omega)
  omega

/-! ## The uniform form is false: the period has to enter

`TestCountBound g` asks for one slack function for **all** periods.  That cannot hold: a drive
can be steered so that a given code passes every check for as long as we like, and cutting the
steered drive after `p` steps gives a periodic word of period `p` under which the code passes
about `p / 2` tests.  This is the across-periods analogue of `survivor_for_every_horizon`. -/

/-- Changing the drive at times `≥ t` does not change the state at time `t`. -/
theorem halfStateD_congr_before {bd bd' : ℕ → Bool} (S : ℕ) :
    ∀ t, (∀ s < t, bd s = bd' s) → halfStateD bd S t = halfStateD bd' S t := by
  intro t
  induction t with
  | zero => intro _; rfl
  | succ t ih =>
    intro h
    simp only [halfStateD]
    rw [ih (fun s hs => h s (by omega)), h t (by omega)]

/-- The **steered drive** for the code `S`: start black; after a black time choose the next
drive value that passes the check, after a white time choose black.  The pair is
(state, drive value). -/
def steer (S : ℕ) : ℕ → ℕ × Bool
  | 0 => (S, true)
  | t + 1 =>
    let q := steer S t
    (halfStep q.2 q.1, if q.2 then !q.1.testBit 0 else true)

/-- The steered drive sequence. -/
def steerDrive (S : ℕ) (t : ℕ) : Bool := (steer S t).2

theorem steer_fst (S : ℕ) : ∀ t, (steer S t).1 = halfStateD (steerDrive S) S t := by
  intro t
  induction t with
  | zero => rfl
  | succ t ih => simp only [steer, halfStateD, steerDrive] at ih ⊢; rw [ih]

/-- The steered drive passes every check. -/
theorem steer_passes (S t : ℕ) (hb : steerDrive S t = true) :
    (halfStateD (steerDrive S) S t).testBit 0 = !steerDrive S (t + 1) := by
  have h : steerDrive S (t + 1) = !(steer S t).1.testBit 0 := by
    simp only [steerDrive] at hb ⊢
    simp only [steer, hb, if_true]
  rw [h, steer_fst, Bool.not_not]

/-- In any two consecutive times the steered drive tests at least once. -/
theorem steer_tests_two (S t : ℕ) : testsBefore (steerDrive S) t + 1 ≤
    testsBefore (steerDrive S) (t + 2) := by
  rw [testsBefore_succ, testsBefore_succ]
  cases hb : steerDrive S t
  · have : steerDrive S (t + 1) = true := by
      simp only [steerDrive] at hb ⊢; simp only [steer, hb]; rfl
    rw [this]; simp
  · simp

theorem steer_tests_ge (S m : ℕ) : m ≤ testsBefore (steerDrive S) (2 * m) := by
  induction m with
  | zero => exact Nat.zero_le _
  | succ m ih =>
    have := steer_tests_two S (2 * m)
    rw [show 2 * (m + 1) = 2 * m + 2 by ring]
    omega

/-- **Any code survives `m` tests of a suitable word of period `2 m + 1`.**  For every code `S`
and every `m` there is a non-white word `k` of period `p = 2 m + 1` under which the machine
started from `S` passes all of its first `m` tests. -/
theorem exists_word_passing_tests (S m : ℕ) :
    ∃ k, 0 < k ∧ k < 2 ^ (2 * m + 1) ∧ ¬ FailsWithinTests (driveN (2 * m + 1) k) S m := by
  set p := 2 * m + 1 with hp
  set k := bitsOf (steerDrive S) p with hk
  have hagree : ∀ t < p, driveN p k t = steerDrive S t := by
    intro t ht
    simp only [driveN, hk, testBit_bitsOf, Nat.mod_eq_of_lt ht]
    simp [ht]
  have hk0 : 0 < k := by
    have h0 : k.testBit 0 = true := by
      rw [hk, testBit_bitsOf]; simp [show 0 < p by omega, steerDrive, steer]
    exact Nat.pos_of_ne_zero fun h => by rw [h] at h0; simp at h0
  refine ⟨k, hk0, bitsOf_lt _ _, ?_⟩
  rintro ⟨t, hb, hn, hf⟩
  -- the failing test lies before time `2 m`
  have htm : t < 2 * m := by
    by_contra hle
    have h1 := steer_tests_ge S m
    have h2 : testsBefore (driveN p k) (2 * m) = testsBefore (steerDrive S) (2 * m) := by
      have : ∀ T ≤ p, testsBefore (driveN p k) T = testsBefore (steerDrive S) T := by
        intro T hT
        induction T with
        | zero => rfl
        | succ T ih => rw [testsBefore_succ, testsBefore_succ, ih (by omega),
            hagree T (by omega)]
      exact this _ (by omega)
    have h3 := testsBefore_mono (driveN p k) (show 2 * m ≤ t by omega)
    omega
  have hst : halfStateD (driveN p k) S t = halfStateD (steerDrive S) S t :=
    halfStateD_congr_before S t fun s hs => hagree s (by omega)
  rw [hagree t (by omega)] at hb
  rw [hst, hagree (t + 1) (by omega), steer_passes S t hb] at hf
  cases h : steerDrive S (t + 1) <;> simp [h] at hf

/-- **Refutation of the uniform test-count law.**  No slack function of the code length alone
works for all periods: `TestCountBound g` is false for every `g`. -/
theorem not_testCountBound (g : ℕ → ℕ) : ¬ TestCountBound g := by
  intro h
  obtain ⟨k, hk0, hk, hpass⟩ := exists_word_passing_tests 1 (1 + g 1)
  exact hpass (h _ k hk0 hk 1 1 le_rfl (by norm_num) (by norm_num))

/-! ## The per-period law -/

/-- **The test-count law for one period**, with a constant slack `c`: for every non-white word of
period `p` and every code of length `d`, the machine fails within `d + c` tests. -/
def TestCountLinear (p c : ℕ) : Prop :=
  ∀ k, 0 < k → k < 2 ^ p → ∀ d S, 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
    FailsWithinTests (driveN p k) S (d + c)

/-- The per-period law gives the one-sided target for that period. -/
theorem halfLineDies_of_testCountLinear {p c : ℕ} (h : TestCountLinear p c) : HalfLineDies p := by
  intro k hk0 hk S hS
  obtain ⟨h0, h1, h2⟩ := code_length_bounds hS
  exact dDiesBy_of_failsWithinTests (h k hk0 hk _ S h0 h1 h2)

/-- The per-period law gives the linear target `HalfLineLinear p p (p * c)`. -/
theorem halfLineLinear_of_testCountLinear {p c : ℕ} (h : TestCountLinear p c) :
    HalfLineLinear p p (p * c) := by
  intro k hk0 hk d S hd h1 h2
  have := dDiesBy_of_failsWithinTests_driveN hk0 hk (h k hk0 hk d S hd h1 h2)
  rwa [Nat.mul_add] at this

/-- The per-period laws for all periods give Problem 1 (the slack may grow with the period). -/
theorem problem1_of_testCountLinear (c : ℕ → ℕ) (h : ∀ p, 0 < p → TestCountLinear p (c p)) :
    Problem1 :=
  problem1_of_halfLineDies fun p hp => halfLineDies_of_testCountLinear (h p hp)

/-- **The slack must grow with the period**: for odd `p = 2 m + 1`, `TestCountLinear p c`
needs `c ≥ m - 1` (the code `1` of length `1` passes `m` tests of a steered word). -/
theorem testCountLinear_slack_ge {m c : ℕ} (h : TestCountLinear (2 * m + 1) c) : m ≤ c + 1 := by
  by_contra hlt
  obtain ⟨k, hk0, hk, hpass⟩ := exists_word_passing_tests 1 m
  have := h k hk0 hk 1 1 le_rfl (by norm_num) (by norm_num)
  obtain ⟨t, hb, hn, hf⟩ := this
  exact hpass ⟨t, hb, by omega, hf⟩

/-- **Period 1** (FORMAL): every code of length `d` fails within `d + 2` tests of the constant
black drive (`constDrive_dies`; every time is a test). -/
theorem testCountLinear_one : TestCountLinear 1 2 := by
  intro k hk0 hk d S _ _ h2
  obtain rfl : k = 1 := by omega
  have hd : driveN 1 1 = fun _ => true := by funext t; simp [driveN, Nat.mod_one]
  rw [hd]
  refine failsWithinTests_of_dDiesBy (constDrive_dies S d h2) (le_of_eq ?_)
  have : ∀ T, testsBefore (fun _ => true) T = T := by
    intro T; induction T with
    | zero => rfl
    | succ T ih => rw [testsBefore_succ, ih]; rfl
  exact this _

end GLM.Rule30
