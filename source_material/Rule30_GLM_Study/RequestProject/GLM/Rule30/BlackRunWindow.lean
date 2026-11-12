module

public import RequestProject.GLM.Rule30.AmortizedHalving
public import RequestProject.GLM.Rule30.TestCountPeriods

/-!
# Round 35: a black run of the drive is one window read (To Do 36)

To Do 36 asks why, after the edge, the observer's tests keep removing about half of the surviving
codes, and suggests starting with words that have adjacent black cells.  This file proves the
exact mechanism for **runs of black drive times**, for every drive and every run length:

* **`blackRun_window`** — if the drive is black at the `r` consecutive times `t, …, t + r - 1`,
  then the machine passes all `r` tests of the run **iff the `r` cells next to the column at time
  `t` show one particular word `w < 2^r`** (which depends only on the drive value at time `t + r`).
  In other words the `r` tests of a black run are *one* question: "is the window of width `r`
  next to the observer equal to `w`?".  No other cell of the state matters, and exactly one of the
  `2^r` windows passes.
* `passesRun_iff` — the same statement read on the original machine started from a code `S`
  (the tests at times `t, …, t + r - 1`).
* `window_step` — the induction step: one step of Rule 30 under a black boundary maps the windows
  of width `r + 1` with a fixed first cell bijectively onto the windows of width `r` (Rule 30 is
  left-permutive, so the window can be reconstructed cell by cell, `winPre`).
* `blackPair_window` — the case `r = 2` (words with two adjacent black cells): the two tests read
  the two cells next to the column, and pass iff they show the word fixed by the next drive value.
* **`blackRun_word`** — the word explicitly: `runWord r b` is the period-1 pattern `0101…`
  (cell `i` black iff `i` is odd) with its last cell flipped iff the run is followed by a white
  time (`b = false`).
* **`dDiesBy_of_long_blackRun`** — consequence, for **every** drive: a code of length `d` cannot
  survive a black run of length `r ≥ d + t + 3` starting at time `t` (the state then has only
  `d + t` cells, `halfStateD_length`, but the run's word has a black cell beyond them,
  `not_passesRun_of_long`).  Period 1 is the case of an infinite run.

So the post-edge question for such words is exactly how the *windows* next to the column are
distributed among the surviving codes: the run removes all codes but those with the one passing
window.  If the surviving windows were uniform, a run of `r` tests would keep a fraction `2^(-r)`
(one bit per test, the measured rate of C331).  The pre-edge case is exactly uniform
(`survivors_card`); after the edge uniformity is what is not proved.  The constant black drive
(period 1) is the infinite run: the window grows without bound, which is why period 1 has a
forced-pattern proof (`constDrive_pattern`).
-/

@[expose] public section

namespace GLM.Rule30

/-- The machine, started at time `t` in state `X`, passes the tests at the `r` times
`t, …, t + r - 1` (each of them assumed black): the cell next to the column is the complement of
the drive's next value. -/
def PassesRun (bd : ℕ → Bool) (t r X : ℕ) : Prop :=
  ∀ s < r, (halfStateD (fun u => bd (u + t)) X s).testBit 0 = !bd (t + s + 1)

/-- Reconstruction of a window cell by cell: `(winPre c w i).1` is cell `i` of the unique window
with first cell `c` whose image under one black-boundary step is `w`; the second component
remembers the previous cell (the boundary value `true` for `i = 0`). -/
def winPre (c : Bool) (w : ℕ) : ℕ → Bool × Bool
  | 0 => (c, true)
  | i + 1 => (xor (w.testBit i) ((winPre c w i).1 || (winPre c w i).2), (winPre c w i).1)

theorem winPre_succ_fst (c : Bool) (w i : ℕ) :
    (winPre c w (i + 1)).1 =
      xor (w.testBit i) ((winPre c w i).1 || (if i = 0 then true else (winPre c w (i - 1)).1)) := by
  cases i with
  | zero => rfl
  | succ i => rfl

/-- **One black-boundary step is a bijection on windows** (fixed first cell). -/
theorem window_step (c : Bool) (r w : ℕ) (hw : w < 2 ^ r) (X : ℕ) :
    (X.testBit 0 = c ∧ halfStep true X % 2 ^ r = w) ↔
      X % 2 ^ (r + 1) = bitsOf (fun i => (winPre c w i).1) (r + 1) := by
  set y : ℕ → Bool := fun i => (winPre c w i).1 with hy
  have hy0 : y 0 = c := rfl
  have hys : ∀ i, y (i + 1) = xor (w.testBit i) (y i || (if i = 0 then true else y (i - 1))) :=
    fun i => winPre_succ_fst c w i
  -- bits of `X % 2^(r+1)` versus the window
  have hiff : X % 2 ^ (r + 1) = bitsOf y (r + 1) ↔ ∀ i ≤ r, X.testBit i = y i := by
    constructor
    · intro h i hi
      have := congrArg (fun n => n.testBit i) h
      simp only [Nat.testBit_mod_two_pow, testBit_bitsOf, show i < r + 1 by omega,
        decide_true, Bool.true_and] at this
      exact this
    · intro h
      apply Nat.eq_of_testBit_eq
      intro i
      rw [Nat.testBit_mod_two_pow, testBit_bitsOf]
      by_cases hi : i < r + 1
      · simp [hi, h i (by omega)]
      · simp [hi]
  rw [hiff]
  constructor
  · rintro ⟨h0, hm⟩
    have hb : ∀ i < r, (halfStep true X).testBit i = w.testBit i := by
      intro i hi
      have := congrArg (fun n => n.testBit i) hm
      simpa [Nat.testBit_mod_two_pow, hi] using this
    intro i
    induction i using Nat.strong_induction_on with
    | _ i ih =>
      intro hi
      match i, ih, hi with
      | 0, _, _ => exact h0
      | j + 1, ih, hi =>
        have e := hb j (by omega)
        rw [testBit_halfStep] at e
        rw [hys j, ← e, ih j (by omega) (by omega)]
        by_cases hj : j = 0
        · simp [hj]
        · simp only [if_neg hj, ih (j - 1) (by omega) (by omega)]
          cases X.testBit (j + 1) <;> cases y j <;> cases y (j - 1) <;> simp
  · intro h
    refine ⟨by rw [h 0 (by omega), hy0], ?_⟩
    apply Nat.eq_of_testBit_eq
    intro i
    rw [Nat.testBit_mod_two_pow]
    by_cases hi : i < r
    · simp only [hi, decide_true, Bool.true_and]
      rw [testBit_halfStep, h (i + 1) (by omega), h i (by omega), hys i]
      by_cases hi0 : i = 0
      · simp [hi0]
      · simp only [if_neg hi0, h (i - 1) (by omega)]
        cases w.testBit i <;> cases y i <;> cases y (i - 1) <;> simp
    · simp only [hi, decide_false, Bool.false_and]
      exact (Nat.testBit_lt_two_pow (lt_of_lt_of_le hw
        (Nat.pow_le_pow_right (by norm_num) (by omega)))).symm

/-- Unfolding one test of a run. -/
theorem passesRun_succ (bd : ℕ → Bool) (t r X : ℕ) :
    PassesRun bd t (r + 1) X ↔
      X.testBit 0 = !bd (t + 1) ∧ PassesRun bd (t + 1) r (halfStep (bd t) X) := by
  have hshift : ∀ s, halfStateD (fun u => bd (u + t)) X (s + 1) =
      halfStateD (fun u => bd (u + (t + 1))) (halfStep (bd t) X) s := by
    intro s
    rw [Nat.add_comm s 1, halfStateD_add]
    congr 1
    · funext u; congr 1; omega
    · simp [halfStateD]
  constructor
  · intro h
    refine ⟨by simpa using h 0 (by omega), fun s hs => ?_⟩
    have := h (s + 1) (by omega)
    rw [hshift] at this
    rw [this]; congr 2; omega
  · rintro ⟨h0, h⟩ s hs
    match s with
    | 0 => simpa using h0
    | s + 1 =>
      rw [hshift, h s (by omega)]; congr 2; omega

/-- **A black run of the drive is one window read.**  If the drive is black at the `r` times
`t, …, t + r - 1`, there is a word `w < 2^r` such that, from any state `X` at time `t`, the machine
passes all `r` tests of the run iff the `r` cells next to the column show `w`. -/
theorem blackRun_window (bd : ℕ → Bool) :
    ∀ r t, (∀ s < r, bd (t + s) = true) →
      ∃ w, w < 2 ^ r ∧ ∀ X, PassesRun bd t r X ↔ X % 2 ^ r = w := by
  intro r
  induction r with
  | zero =>
    intro t _
    refine ⟨0, by norm_num, fun X => ?_⟩
    simp [PassesRun, Nat.mod_one]
  | succ r ih =>
    intro t hrun
    obtain ⟨w', hw', hiff⟩ := ih (t + 1) fun s hs => by
      rw [show t + 1 + s = t + (s + 1) by omega]; exact hrun (s + 1) (by omega)
    have hbt : bd t = true := by simpa using hrun 0 (by omega)
    refine ⟨bitsOf (fun i => (winPre (!bd (t + 1)) w' i).1) (r + 1), bitsOf_lt _ _, fun X => ?_⟩
    rw [passesRun_succ, hiff, hbt]
    exact window_step _ r w' hw' X

/-- **The same statement on the original machine.**  For a code `S`, the tests at the black times
`t, …, t + r - 1` all pass iff the window of width `r` next to the column at time `t` is the
run's word. -/
theorem passesRun_iff (bd : ℕ → Bool) (S t r : ℕ) :
    PassesRun bd t r (halfStateD bd S t) ↔
      ∀ s < r, (halfStateD bd S (t + s)).testBit 0 = !bd (t + s + 1) := by
  unfold PassesRun
  refine forall_congr' fun s => imp_congr_right fun _ => ?_
  rw [halfStateD_add]

/-- **Two adjacent black cells** (To Do 36's first case): if the drive is black at `t` and
`t + 1`, both tests pass iff the two cells next to the column at time `t` show one fixed word of
two bits. -/
theorem blackPair_window (bd : ℕ → Bool) (t : ℕ) (h0 : bd t = true) (h1 : bd (t + 1) = true) :
    ∃ w, w < 4 ∧ ∀ S, (∀ s < 2, (halfStateD bd S (t + s)).testBit 0 = !bd (t + s + 1)) ↔
      halfStateD bd S t % 4 = w := by
  obtain ⟨w, hw, h⟩ := blackRun_window bd 2 t fun s hs => by
    interval_cases s
    · simpa using h0
    · exact h1
  exact ⟨w, hw, fun S => by rw [← passesRun_iff, h]; rfl⟩

/-! ## The run's word, explicitly, and long runs are fatal -/

/-- **The word of a black run** of length `r` followed by the drive value `b`: the period-1
pattern `0101…` (cell `i` black iff `i` is odd), with the last cell flipped iff the run is
followed by a white time. -/
def runWord (r : ℕ) (b : Bool) : ℕ :=
  bitsOf (fun i => xor (decide (i % 2 = 1)) (decide (i + 1 = r) && !b)) r

theorem runWord_lt (r : ℕ) (b : Bool) : runWord r b < 2 ^ r := bitsOf_lt _ _

theorem testBit_runWord (r : ℕ) (b : Bool) (i : ℕ) :
    (runWord r b).testBit i =
      (decide (i < r) && xor (decide (i % 2 = 1)) (decide (i + 1 = r) && !b)) :=
  testBit_bitsOf _ _ _

/-- One black-boundary step takes the word of a run of length `r + 1` to the word of the
remaining run of length `r`. -/
theorem runWord_step (r : ℕ) (hr : 1 ≤ r) (b : Bool) :
    (runWord (r + 1) b).testBit 0 = false ∧ halfStep true (runWord (r + 1) b) % 2 ^ r =
      runWord r b := by
  constructor
  · rw [testBit_runWord]; simp; omega
  · apply Nat.eq_of_testBit_eq
    intro i
    rw [Nat.testBit_mod_two_pow, testBit_runWord]
    by_cases hi : i < r
    · have hW : ∀ j < r, (runWord (r + 1) b).testBit j = decide (j % 2 = 1) := by
        intro j hj
        rw [testBit_runWord]
        simp [show j < r + 1 by omega, show j ≠ r by omega]
      have hor : ((runWord (r + 1) b).testBit i ||
          (if i = 0 then true else (runWord (r + 1) b).testBit (i - 1))) = true := by
        by_cases hi0 : i = 0
        · simp [hi0]
        · rw [if_neg hi0, hW i hi, hW (i - 1) (by omega)]
          rcases Nat.mod_two_eq_zero_or_one i with h | h
          · have : (i - 1) % 2 = 1 := by omega
            simp [this]
          · simp [h]
      rw [testBit_halfStep, hor, Bool.xor_true, testBit_runWord]
      have e : (i + 1 + 1 = r + 1) ↔ (i + 1 = r) := by omega
      simp only [hi, decide_true, Bool.true_and, show i + 1 < r + 1 by omega, e]
      rcases Nat.mod_two_eq_zero_or_one i with h | h
      · have : (i + 1) % 2 = 1 := by omega
        simp [h, this]
      · have : (i + 1) % 2 = 0 := by omega
        simp [h, this]
    · simp [hi]

/-- **The run's word, explicitly.**  If the drive is black at `t, …, t + r - 1`, the machine
passes the run's tests from the state `X` iff the `r` cells next to the column show
`runWord r (bd (t + r))`. -/
theorem blackRun_word (bd : ℕ → Bool) :
    ∀ r t, (∀ s < r, bd (t + s) = true) →
      ∀ X, PassesRun bd t r X ↔ X % 2 ^ r = runWord r (bd (t + r)) := by
  intro r
  induction r with
  | zero =>
    intro t _ X
    simp [PassesRun, Nat.mod_one, runWord, bitsOf]
  | succ r ih =>
    intro t hrun X
    have hbt : bd t = true := by simpa using hrun 0 (by omega)
    rw [passesRun_succ, hbt]
    rcases Nat.eq_zero_or_pos r with rfl | hr
    · -- the last test of the run
      have h0 : PassesRun bd (t + 1) 0 (halfStep true X) := fun s hs => absurd hs (by omega)
      simp only [h0, and_true, zero_add, pow_one]
      have hw : runWord 1 (bd (t + 1)) = (!bd (t + 1)).toNat := by
        cases h : bd (t + 1) <;> rfl
      rw [hw, Nat.testBit_zero]
      cases h : bd (t + 1) <;> rcases Nat.mod_two_eq_zero_or_one X with hx | hx <;> simp [hx]
    · have hb1 : bd (t + 1) = true := by simpa using hrun 1 (by omega)
      rw [ih (t + 1) (fun s hs => by
        rw [show t + 1 + s = t + (s + 1) by omega]; exact hrun (s + 1) (by omega)), hb1,
        show t + 1 + r = t + (r + 1) by omega, Bool.not_true]
      rw [window_step false r _ (runWord_lt _ _) X]
      have hW := (window_step false r _ (runWord_lt r (bd (t + (r + 1)))) (runWord (r + 1)
        (bd (t + (r + 1))))).1 (runWord_step r hr _)
      rw [Nat.mod_eq_of_lt (runWord_lt _ _)] at hW
      rw [← hW]

/-- **A long black run is fatal.**  If the state at time `t` has fewer than `L` cells
(`X < 2^L`) and the drive is black at `r ≥ L + 3` consecutive times from `t`, the machine fails a
test of the run: the run's word needs a black cell beyond the state. -/
theorem not_passesRun_of_long (bd : ℕ → Bool) {t r L X : ℕ} (hrun : ∀ s < r, bd (t + s) = true)
    (hX : X < 2 ^ L) (hr : L + 3 ≤ r) : ¬ PassesRun bd t r X := by
  rw [blackRun_word bd r t hrun X, Nat.mod_eq_of_lt (lt_of_lt_of_le hX
    (Nat.pow_le_pow_right (by norm_num) (by omega)))]
  intro h
  -- an odd position `j` with `L ≤ j < r - 1`
  obtain ⟨j, hj1, hj2, hj3⟩ : ∃ j, L ≤ j ∧ j + 1 < r ∧ j % 2 = 1 := by
    rcases Nat.mod_two_eq_zero_or_one (r - 2) with h | h
    · exact ⟨r - 3, by omega, by omega, by omega⟩
    · exact ⟨r - 2, by omega, by omega, h⟩
  have h1 := congrArg (fun n => n.testBit j) h
  simp only [testBit_runWord, show j < r by omega, decide_true, Bool.true_and, hj3,
    show ¬ (j + 1 = r) by omega, decide_false, Bool.false_and, Bool.xor_false] at h1
  rw [Nat.testBit_lt_two_pow (lt_of_lt_of_le hX (Nat.pow_le_pow_right (by norm_num) hj1))] at h1
  exact Bool.noConfusion h1

/-- A code of length `d` is a code of length `d + t` after `t` steps. -/
theorem halfStateD_length (bd : ℕ → Bool) {d S : ℕ} (hd : 1 ≤ d) (h1 : 2 ^ (d - 1) ≤ S)
    (h2 : S < 2 ^ d) : ∀ t, 2 ^ (d + t - 1) ≤ halfStateD bd S t ∧ halfStateD bd S t < 2 ^ (d + t)
  | 0 => by simpa using And.intro h1 h2
  | t + 1 => by
    obtain ⟨a, b⟩ := halfStateD_length bd hd h1 h2 t
    have := halfStep_length (b := bd t) (by omega : 1 ≤ d + t) a b
    simp only [halfStateD]
    rw [show d + (t + 1) - 1 = d + t by omega, show d + (t + 1) = d + t + 1 by omega]
    exact this

/-- **Long black runs kill, for every drive.**  A code of length `d` cannot survive a black run of
length `r ≥ d + t + 3` that starts at time `t`: the machine fails before the run ends.  (The
constant black drive, period 1, is the case `t = 0`.) -/
theorem dDiesBy_of_long_blackRun (bd : ℕ → Bool) {d S t r : ℕ} (hd : 1 ≤ d)
    (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) (hrun : ∀ s < r, bd (t + s) = true)
    (hr : d + t + 3 ≤ r) : dDiesBy bd S (t + r) = true := by
  have hlen := (halfStateD_length bd hd h1 h2 t).2
  have hnot := not_passesRun_of_long bd hrun hlen hr
  rw [passesRun_iff] at hnot
  push_neg at hnot
  obtain ⟨s, hs, hfail⟩ := hnot
  rw [dDiesBy_spec]
  refine ⟨t + s, by omega, hrun s hs, ?_⟩
  cases h : bd (t + s + 1) <;> simp_all

end GLM.Rule30
