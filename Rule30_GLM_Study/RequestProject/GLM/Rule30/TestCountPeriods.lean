module

public import RequestProject.GLM.Rule30.TestCountLaw

/-!
# Round 34: how the observer-clock slack depends on the period

A word of period `p`, written out `m` times, is a word of period `m * p` that drives the machine
in exactly the same way (`driveN_repeat`).  So every per-period statement about the half-line
machine passes **down** from a period to each of its divisors:

* `testCountLinear_of_dvd` — `TestCountLinear q c → TestCountLinear p c` whenever `p ∣ q`;
* `halfLineDies_of_dvd` — `HalfLineDies q → HalfLineDies p` whenever `p ∣ q`;
* `testCountLinear_mono` — a larger slack is weaker.

**The observer's phase.**  `TestSlack bd c` is the slack of a single drive.  Starting the clock
one step later turns each code of length `d` into a code of length `d + 1` (`halfStep_length`)
and skips at most one test, so a slack seen from the later start gives the slack `+ 2` from the
earlier start (`testSlack_of_shift`; `+ 1` if the skipped time is white,
`testSlack_of_shift_white`; `+ 2 s` for `s` steps, `testSlack_of_shift_iter`).  This is the
user's "perspective" idea in exact form: the read position of the observer `Y` (the phase of the
word) changes the measured excess by a bounded amount, in one direction per step.  Measured
(study folder `rule30_round34/test_slack34_output.txt`): the rotations `0111, 1110, 1101, 1011` of one word have
records `7, 6, 5, 4` on the searched ranges (EMP): each step of phase changes the record by `1`,
within the proved allowance (`1` when the skipped time is white, `2` when it is black).

Read the other way, every refutation passes **up** to all multiples
(`not_testCountLinear_of_dvd`).  Hence the least slack of a period (when it exists) is at least
the least slack of each divisor: the slack sequence is monotone along divisibility.  Together
with `testCountLinear_slack_ge` (period `2m+1` needs slack `≥ m - 1`) this gives a lower bound
for every period that has an odd divisor (`testCountLinear_slack_ge_of_dvd`).

All statements are exact; there are no finite checks in this file.
-/

@[expose] public section

namespace GLM.Rule30

/-- The word `k` of period `p`, written out over `q` positions. -/
def repeatWord (p k q : ℕ) : ℕ := bitsOf (driveN p k) q

/-- **Repeating a word does not change the drive.**  If `p ∣ q` and `0 < q`, the word of period
`q` obtained by writing out `k` drives exactly like `k`. -/
theorem driveN_repeat {p q : ℕ} (k : ℕ) (hpq : p ∣ q) (hq : 0 < q) :
    driveN q (repeatWord p k q) = driveN p k := by
  funext t
  have hlt : t % q < q := Nat.mod_lt _ hq
  simp only [driveN, repeatWord, testBit_bitsOf, hlt, decide_true, Bool.true_and]
  rw [Nat.mod_mod_of_dvd t hpq]

theorem repeatWord_lt (p k q : ℕ) : repeatWord p k q < 2 ^ q := bitsOf_lt _ _

/-- A non-white word stays non-white when it is written out over a multiple of its period. -/
theorem repeatWord_pos {p k q : ℕ} (hk0 : 0 < k) (hk : k < 2 ^ p) (hpq : p ∣ q) (hq : 0 < q) :
    0 < repeatWord p k q := by
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
  have hpq' : p ≤ q := Nat.le_of_dvd hq hpq
  have hb : (repeatWord p k q).testBit j = true := by
    simp only [repeatWord, testBit_bitsOf, driveN, Nat.mod_eq_of_lt hjp, hj,
      show j < q by omega, decide_true, Bool.true_and]
  exact Nat.pos_of_ne_zero fun h => by rw [h] at hb; simp at hb

/-- **The test-count law passes to divisors of the period.** -/
theorem testCountLinear_of_dvd {p q c : ℕ} (hpq : p ∣ q) (hq : 0 < q)
    (h : TestCountLinear q c) : TestCountLinear p c := by
  intro k hk0 hk d S hd h1 h2
  have := h (repeatWord p k q) (repeatWord_pos hk0 hk hpq hq) (repeatWord_lt p k q) d S hd h1 h2
  rwa [driveN_repeat k hpq hq] at this

/-- **Refutations pass to multiples of the period.** -/
theorem not_testCountLinear_of_dvd {p q c : ℕ} (hpq : p ∣ q) (hq : 0 < q)
    (h : ¬ TestCountLinear p c) : ¬ TestCountLinear q c :=
  fun hq' => h (testCountLinear_of_dvd hpq hq hq')

/-- **The one-sided target passes to divisors of the period.** -/
theorem halfLineDies_of_dvd {p q : ℕ} (hpq : p ∣ q) (hq : 0 < q) (h : HalfLineDies q) :
    HalfLineDies p := by
  intro k hk0 hk S hS
  have := h (repeatWord p k q) (repeatWord_pos hk0 hk hpq hq) (repeatWord_lt p k q) S hS
  rwa [driveN_repeat k hpq hq] at this

/-- A larger slack is a weaker law. -/
theorem testCountLinear_mono {p c c' : ℕ} (hc : c ≤ c') (h : TestCountLinear p c) :
    TestCountLinear p c' := by
  intro k hk0 hk d S hd h1 h2
  obtain ⟨t, hb, hn, hf⟩ := h k hk0 hk d S hd h1 h2
  exact ⟨t, hb, by omega, hf⟩

/-- **Lower bound for every period with an odd divisor**: if `2 m + 1` divides `q`, the law for
period `q` needs slack at least `m - 1`. -/
theorem testCountLinear_slack_ge_of_dvd {m q c : ℕ} (hdvd : 2 * m + 1 ∣ q) (hq : 0 < q)
    (h : TestCountLinear q c) : m ≤ c + 1 :=
  testCountLinear_slack_ge (testCountLinear_of_dvd hdvd hq h)

/-! ## The observer's phase: starting the clock one step later

The drive word fixes *what* the column says; its phase fixes *when the observer starts
listening*.  Starting one step later turns a code of length `d` into the code of length `d + 1`
that the machine holds after one step, and removes at most one test from the count.  So the
slack seen from a later starting point bounds the slack seen from the earlier one, up to `2`
per step (`testSlack_of_shift`, `testSlack_of_shift_iter`).  The direction matters: this is a
one-way inequality, an arrow from the later perspective to the earlier one. -/

/-- **The slack of one drive**: every code of length `d` fails within `d + c` tests of `bd`. -/
def TestSlack (bd : ℕ → Bool) (c : ℕ) : Prop :=
  ∀ d S, 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d → FailsWithinTests bd S (d + c)

/-- `TestCountLinear` is the slack of every non-white word of the period. -/
theorem testCountLinear_iff_testSlack (p c : ℕ) :
    TestCountLinear p c ↔ ∀ k, 0 < k → k < 2 ^ p → TestSlack (driveN p k) c :=
  Iff.rfl

/-- A code of length `d` becomes a code of length `d + 1` after one step (the edge moves one
cell outwards). -/
theorem halfStep_length {b : Bool} {d S : ℕ} (hd : 1 ≤ d) (h1 : 2 ^ (d - 1) ≤ S)
    (h2 : S < 2 ^ d) : 2 ^ d ≤ halfStep b S ∧ halfStep b S < 2 ^ (d + 1) := by
  have hz : ∀ i, d ≤ i → S.testBit i = false := fun i hi =>
    Nat.testBit_eq_false_of_lt (lt_of_lt_of_le h2 (Nat.pow_le_pow_right (by norm_num) hi))
  have htop : S.testBit (d - 1) = true := by
    rw [Nat.testBit_eq_decide_div_mod_eq]
    have : S / 2 ^ (d - 1) = 1 := by
      apply Nat.div_eq_of_lt_le
      · simpa using h1
      · rw [show 2 * 2 ^ (d - 1) = 2 ^ d by rw [← pow_succ']; congr 1; omega]
        simpa using h2
    simp [this]
  constructor
  · apply Nat.ge_two_pow_of_testBit
    rw [testBit_halfStep, if_neg (by omega), hz (d + 1) (by omega), hz d le_rfl,
      show d - 1 = d - 1 from rfl, htop]
    rfl
  · apply Nat.lt_pow_two_of_testBit
    intro i hi
    rw [testBit_halfStep, if_neg (by omega), hz (i + 1) (by omega), hz i (by omega),
      hz (i - 1) (by omega)]
    rfl

/-- Tests before `t + 1` = the test at time `0` plus the tests of the shifted drive before `t`. -/
theorem testsBefore_shift (bd : ℕ → Bool) (t : ℕ) :
    testsBefore bd (t + 1) = (bd 0).toNat + testsBefore (fun u => bd (u + 1)) t := by
  induction t with
  | zero => simp [testsBefore]
  | succ t ih =>
    rw [testsBefore_succ, ih, testsBefore_succ]
    simp only [Nat.add_assoc]

/-- A failure of the machine started one step later is a failure of the original machine, one
step later and with at most one more test. -/
theorem failsWithinTests_of_shift {bd : ℕ → Bool} {S n : ℕ}
    (h : FailsWithinTests (fun u => bd (u + 1)) (halfStep (bd 0) S) n) :
    FailsWithinTests bd S (n + (bd 0).toNat) := by
  obtain ⟨t, hb, hn, hf⟩ := h
  refine ⟨t + 1, hb, ?_, ?_⟩
  · rw [testsBefore_shift]; omega
  · have := halfStateD_add bd S 1 t
    rw [Nat.add_comm 1 t] at this
    rw [this]
    exact hf

/-- **The observer's phase, one step.**  If every code fails within `d + c` tests when the clock
starts one step later, then every code fails within `d + c + 2` tests from the original start. -/
theorem testSlack_of_shift {bd : ℕ → Bool} {c : ℕ} (h : TestSlack (fun u => bd (u + 1)) c) :
    TestSlack bd (c + 2) := by
  intro d S hd h1 h2
  obtain ⟨l1, l2⟩ := halfStep_length (b := bd 0) hd h1 h2
  obtain ⟨t, hb, hn, hf⟩ := failsWithinTests_of_shift (h (d + 1) (halfStep (bd 0) S) (by omega)
    (by simpa using l1) l2)
  refine ⟨t, hb, ?_, hf⟩
  have : (bd 0).toNat ≤ 1 := by cases bd 0 <;> simp
  omega

/-- When the skipped time is white (no test), the slack moves by at most `1`. -/
theorem testSlack_of_shift_white {bd : ℕ → Bool} {c : ℕ} (h0 : bd 0 = false)
    (h : TestSlack (fun u => bd (u + 1)) c) : TestSlack bd (c + 1) := by
  intro d S hd h1 h2
  obtain ⟨l1, l2⟩ := halfStep_length (b := bd 0) hd h1 h2
  obtain ⟨t, hb, hn, hf⟩ := failsWithinTests_of_shift (h (d + 1) (halfStep (bd 0) S) (by omega)
    (by simpa using l1) l2)
  refine ⟨t, hb, ?_, hf⟩
  rw [h0] at hn
  simp at hn
  omega

/-- **The observer's phase, `s` steps.**  Starting the clock `s` steps later can lower the slack by
at most `2 s`. -/
theorem testSlack_of_shift_iter (bd : ℕ → Bool) (c s : ℕ)
    (h : TestSlack (fun u => bd (u + s)) c) : TestSlack bd (c + 2 * s) := by
  induction s generalizing c with
  | zero => simpa using h
  | succ s ih =>
    have h' : TestSlack (fun u => (fun u => bd (u + s)) (u + 1)) c := by
      simpa [Nat.add_assoc, Nat.add_comm 1 s] using h
    have := ih (c + 2) (testSlack_of_shift h')
    rwa [show c + 2 + 2 * s = c + 2 * (s + 1) by ring] at this

end GLM.Rule30
