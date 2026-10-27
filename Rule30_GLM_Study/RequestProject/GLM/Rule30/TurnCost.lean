module

public import RequestProject.GLM.Rule30.DriveWheel

/-!
# Round 37: the exact cost of a turn, and the observer's best phase (To Do 40)

Round 36 bounded the cost of turning the wheel by `2` slack per step of phase
(`testSlack_wheelTurn`).  The exact cost is smaller: a step over a **white** time costs `1`, a
step over a **black** time (a test) costs `2`.  So starting the clock `m` steps later costs

  `m + (tests in the skipped m times)`                (`testSlack_of_shift_count`),

and between two phases `a`, `b` of one wheel (`a + m ≡ b mod p`)

  `slack(a) ≤ slack(b) + m + testsBefore (phase a) m`   (`testSlack_phase_transfer`).

The exact search of Round 37 (`scripts/wheel_phases37.py`, EMP, periods `≤ 8`, `d ≤ 28`) finds no
violation on 2876 ordered phase pairs, and in 66 of the 69 wheels with more than one phase some
pair of phases attains the bound exactly, so it cannot be lowered as a general rule.  (From the
best phase alone it predicts 84 of the 401 other phases exactly.)  For periods 2 and 3 the
attained cases are certified (`TurnCostData`).

**The observer's best phase.**  Because every phase of a wheel controls every other phase, a
slack at *any one* phase of each wheel is enough (`testCountLinear_of_phases`); the observer may
read each wheel from the phase where it is cheapest.  For period 2 this gives a sharper target:
the phase `01` (black at odd times) with slack `3` gives the optimal period-2 slack `5` for all
`d` (`testCountLinear_two_of_phase`), and the same for period 3 (`testCountLinear_three_of_phases`).

All results use only the standard axioms.  Finite certificates are in `TurnCostData.lean`.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## Exact cost of starting the clock later -/

/-- **One step, exact.**  Starting the clock one step later costs `1` slack, plus `1` if the
skipped time is a test. -/
theorem testSlack_of_shift_exact {bd : ℕ → Bool} {c : ℕ} (h : TestSlack (fun u => bd (u + 1)) c) :
    TestSlack bd (c + 1 + (bd 0).toNat) := by
  intro d S hd h1 h2
  obtain ⟨l1, l2⟩ := halfStep_length (b := bd 0) hd h1 h2
  obtain ⟨t, hb, hn, hf⟩ := failsWithinTests_of_shift (h (d + 1) (halfStep (bd 0) S) (by omega)
    (by simpa using l1) l2)
  exact ⟨t, hb, by omega, hf⟩

/-- **`s` steps, exact**: the cost is `s` plus the number of tests skipped. -/
theorem testSlack_of_shift_count (bd : ℕ → Bool) (c s : ℕ)
    (h : TestSlack (fun u => bd (u + s)) c) : TestSlack bd (c + s + testsBefore bd s) := by
  induction s generalizing bd c with
  | zero => show TestSlack bd (c + 0 + 0); simpa using h
  | succ s ih =>
    have h' : TestSlack (fun u => (fun u => bd (u + 1)) (u + s)) c := by
      simpa [Nat.add_assoc, Nat.add_comm 1 s] using h
    have h2 := testSlack_of_shift_exact (ih (fun u => bd (u + 1)) c h')
    rw [testsBefore_shift]
    convert h2 using 1
    omega

/-- One step on a finite range of code lengths, exact. -/
theorem testSlackUpTo_of_shift_exact {bd : ℕ → Bool} {c D : ℕ}
    (h : TestSlackUpTo (fun u => bd (u + 1)) c (D + 1)) :
    TestSlackUpTo bd (c + 1 + (bd 0).toNat) D := by
  intro d S hd hdD h1 h2
  obtain ⟨l1, l2⟩ := halfStep_length (b := bd 0) hd h1 h2
  obtain ⟨t, hb, hn, hf⟩ := failsWithinTests_of_shift (h (d + 1) (halfStep (bd 0) S) (by omega)
    (by omega) (by simpa using l1) l2)
  exact ⟨t, hb, by omega, hf⟩

/-- `s` steps on a finite range, exact: a certificate on code lengths `≤ D + s` for the later
start gives one on `≤ D` for the earlier start. -/
theorem testSlackUpTo_of_shift_count (bd : ℕ → Bool) (c s D : ℕ)
    (h : TestSlackUpTo (fun u => bd (u + s)) c (D + s)) :
    TestSlackUpTo bd (c + s + testsBefore bd s) D := by
  induction s generalizing bd c D with
  | zero => show TestSlackUpTo bd (c + 0 + 0) D; simpa using h
  | succ s ih =>
    have h' : TestSlackUpTo (fun u => (fun u => bd (u + 1)) (u + s)) c (D + 1 + s) := by
      simpa [Nat.add_assoc, Nat.add_comm 1 s] using h
    have h2 := testSlackUpTo_of_shift_exact (ih (fun u => bd (u + 1)) c (D + 1) h')
    rw [testsBefore_shift]
    convert h2 using 1
    omega

/-! ## Between two phases of one wheel -/

theorem hasPeriod_shift_eq {bd : ℕ → Bool} {p : ℕ} (hper : HasPeriod bd p) {x y : ℕ}
    (hxy : x % p = y % p) (u : ℕ) : bd (u + x) = bd (u + y) := by
  rw [hper.eq_mod (u + x), hper.eq_mod (u + y), Nat.add_mod, hxy, ← Nat.add_mod]

/-- **The exact cost of a turn between two phases.**  For a drive of period `p`, if phase `b`
has slack `c` and `a + m ≡ b (mod p)`, then phase `a` has slack
`c + m + (tests of phase a in its first m times)`. -/
theorem testSlack_phase_transfer {bd : ℕ → Bool} {p : ℕ} (hper : HasPeriod bd p) {a b m c : ℕ}
    (hm : (a + m) % p = b % p) (h : TestSlack (fun u => bd (u + b)) c) :
    TestSlack (fun u => bd (u + a)) (c + m + testsBefore (fun u => bd (u + a)) m) := by
  apply testSlack_of_shift_count
  have : (fun u => (fun u => bd (u + a)) (u + m)) = fun u => bd (u + b) := by
    funext u
    simp only
    rw [Nat.add_assoc, Nat.add_comm m a]
    exact hasPeriod_shift_eq hper hm u
  rw [this]
  exact h

/-- The same on a finite range of code lengths. -/
theorem testSlackUpTo_phase_transfer {bd : ℕ → Bool} {p : ℕ} (hper : HasPeriod bd p)
    {a b m c D : ℕ} (hm : (a + m) % p = b % p) (h : TestSlackUpTo (fun u => bd (u + b)) c (D + m)) :
    TestSlackUpTo (fun u => bd (u + a)) (c + m + testsBefore (fun u => bd (u + a)) m) D := by
  apply testSlackUpTo_of_shift_count
  have : (fun u => (fun u => bd (u + a)) (u + m)) = fun u => bd (u + b) := by
    funext u
    simp only
    rw [Nat.add_assoc, Nat.add_comm m a]
    exact hasPeriod_shift_eq hper hm u
  rw [this]
  exact h

/-- **The exact cost of a turn, in words.**  If the turn `b` of the word `k` has slack `c`, the
turn `a` (with `a + m ≡ b mod p`) has slack `c + m + testsBefore (turn a) m`. -/
theorem testSlack_wheelTurn_transfer {p : ℕ} (hp : 0 < p) {k a b m c : ℕ}
    (hm : (a + m) % p = b % p) (h : TestSlack (driveN p (wheelTurn p k b)) c) :
    TestSlack (driveN p (wheelTurn p k a))
      (c + m + testsBefore (driveN p (wheelTurn p k a)) m) := by
  rw [driveN_wheelTurn hp] at h ⊢
  exact testSlack_phase_transfer (driveN_hasPeriod p k) hm h

/-- The same on a finite range. -/
theorem testSlackUpTo_wheelTurn_transfer {p : ℕ} (hp : 0 < p) {k a b m c D : ℕ}
    (hm : (a + m) % p = b % p) (h : TestSlackUpTo (driveN p (wheelTurn p k b)) c (D + m)) :
    TestSlackUpTo (driveN p (wheelTurn p k a))
      (c + m + testsBefore (driveN p (wheelTurn p k a)) m) D := by
  rw [driveN_wheelTurn hp] at h ⊢
  exact testSlackUpTo_phase_transfer (driveN_hasPeriod p k) hm h

/-- Tests in `m` times are at most `m`. -/
theorem testsBefore_le (bd : ℕ → Bool) (m : ℕ) : testsBefore bd m ≤ m := by
  induction m with
  | zero => simp [testsBefore]
  | succ m ih =>
    rw [testsBefore_succ]
    have : (bd m).toNat ≤ 1 := by cases bd m <;> simp
    omega

/-! ## The observer's best phase -/

/-- A slack gives death. -/
theorem wordDies_of_testSlack {bd : ℕ → Bool} {c : ℕ} (h : TestSlack bd c) : WordDies bd := by
  intro S hS
  obtain ⟨h0, h1, h2⟩ := code_length_bounds hS
  exact dDiesBy_of_failsWithinTests (h _ S h0 h1 h2)

/-- **One phase decides the wheel**: a slack at any one phase of a word kills every half-line
under the word and under every turn of it. -/
theorem wordDies_of_phase {p : ℕ} (hp : 0 < p) {k s c : ℕ}
    (h : TestSlack (driveN p (wheelTurn p k s)) c) (a : ℕ) :
    WordDies (driveN p (wheelTurn p k a)) := by
  rw [wordDies_wheelTurn_iff hp]
  exact (wordDies_wheelTurn_iff hp k s).1 (wordDies_of_testSlack h)

/-- Every word of period `p` is a turn, by a phase `< p`, of any turn of itself. -/
theorem wheelTurn_turn_back {p : ℕ} (hp : 0 < p) {k : ℕ} (hk : k < 2 ^ p) (s : ℕ) :
    wheelTurn p (wheelTurn p k s) (p - s % p) = k := by
  rw [wheelTurn_add hp, wheelTurn_mod]
  have h1 := Nat.mod_add_div s p
  have h2 := Nat.mod_lt s hp
  have : (s + (p - s % p)) % p = 0 := by
    rw [show s + (p - s % p) = p * (s / p + 1) by rw [Nat.mul_add]; omega]
    exact Nat.mul_mod_right _ _
  rw [this, wheelTurn_zero hk]

/-- Between any two phases there is a forward gap `m < q`. -/
theorem exists_phase_gap {q : ℕ} (hq : 0 < q) (a s : ℕ) : ∃ m < q, (a + m) % q = s % q := by
  refine ⟨(s % q + (q - a % q)) % q, Nat.mod_lt _ hq, ?_⟩
  have ha := Nat.mod_lt a hq
  have h1 := Nat.mod_add_div a q
  rw [Nat.add_mod_mod, show a + (s % q + (q - a % q)) = s % q + q * (a / q + 1) by
    rw [Nat.mul_add, Nat.mul_one]; omega, Nat.add_mul_mod_self_left, Nat.mod_mod]

/-- **The per-period law from one phase per wheel.**  If each representative of each divisor
`q ∣ p` has *some* phase with slack `c` (the observer's choice of read position), every
non-white word of period `p` has slack `c + 2 (p − 1)`. -/
theorem testCountLinear_of_phases {p c : ℕ} (hp : 0 < p)
    (h : ∀ q, 0 < q → q ∣ p → ∀ j, WheelRep q j → ∃ s, TestSlack (driveN q (wheelTurn q j s)) c) :
    TestCountLinear p (c + 2 * (p - 1)) := by
  intro k hk0 hk
  obtain ⟨q, j, s₀, hq, hqp, hj, he⟩ := exists_wheelRep p hp k hk0 hk
  obtain ⟨s, hs⟩ := h q hq hqp j hj
  -- the word is a turn of the hub
  have hdrive : driveN p k = driveN q (wheelTurn q j (p * s₀ - s₀)) := by
    rw [driveN_wheelTurn hq, he]
    funext u
    have hs' : s₀ ≤ p * s₀ := Nat.le_mul_of_pos_left s₀ hp
    simp only
    rw [show u + (p * s₀ - s₀) + s₀ = u + p * s₀ by omega,
      drive_periodic_mul (driveN_periodic k)]
  rw [hdrive]
  obtain ⟨m, hmq, hm⟩ := exists_phase_gap hq (p * s₀ - s₀) s
  have := testSlack_wheelTurn_transfer (k := j) hq hm hs
  have hle := testsBefore_le (driveN q (wheelTurn q j (p * s₀ - s₀))) m
  have hqle := Nat.le_of_dvd hp hqp
  exact testSlack_mono (by omega) this

/-- **The full wheel from one phase per wheel.** -/
theorem wheelDies_of_phases
    (h : ∀ q j, 0 < q → WheelRep q j → ∃ s c, TestSlack (driveN q (wheelTurn q j s)) c) :
    WheelDies := by
  intro q j hq hj
  obtain ⟨s, c, hs⟩ := h q j hq hj
  have := wordDies_of_phase hq hs 0
  rwa [wheelTurn_zero hj.2.1] at this

/-! ## Periods 2 and 3: the best phase gives the optimal per-period slack -/

theorem driveN_two_three : driveN 2 3 = driveN 1 1 := by
  funext t
  have h := Nat.mod_lt t (show 0 < 2 by norm_num)
  simp only [driveN, Nat.mod_one]
  interval_cases (t % 2) <;> rfl

theorem testSlack_const_one : TestSlack (driveN 1 1) 2 :=
  testCountLinear_one 1 (by norm_num) (by norm_num)

/-- **Period 2 from its best phase.**  The phase `01` (black at odd times, word `2`) with slack
`3` gives the optimal period-2 law `TestCountLinear 2 5`, for all `d`. -/
theorem testCountLinear_two_of_phase (h : TestSlack (driveN 2 2) 3) : TestCountLinear 2 5 := by
  intro k hk0 hk
  have hk' : k = 1 ∨ k = 2 ∨ k = 3 := by norm_num at hk; omega
  rcases hk' with rfl | rfl | rfl
  · have hw : (fun u => driveN 2 1 (u + 1)) = driveN 2 2 := by
      funext u
      have := Nat.mod_lt u (show 0 < 2 by norm_num)
      simp only [driveN, Nat.add_mod u 1 2]
      interval_cases (u % 2) <;> rfl
    have := testSlack_of_shift_count (driveN 2 1) 3 1 (by rw [hw]; exact h)
    have ht : testsBefore (driveN 2 1) 1 = 1 := by decide
    rwa [ht] at this
  · exact testSlack_mono (by norm_num) h
  · rw [driveN_two_three]; exact testSlack_mono (by norm_num) testSlack_const_one

theorem driveN_three_seven : driveN 3 7 = driveN 1 1 := by
  funext t
  have h := Nat.mod_lt t (show 0 < 3 by norm_num)
  simp only [driveN, Nat.mod_one]
  interval_cases (t % 3) <;> rfl

/-- **Period 3 from its best phases.**  The phase `010` (word `2`) of the wheel `100` with slack
`5` and the phase `101` (word `5`) of the wheel `110` with slack `2` give the optimal period-3
law `TestCountLinear 3 8`, for all `d`. -/
theorem testCountLinear_three_of_phases (h2 : TestSlack (driveN 3 2) 5)
    (h5 : TestSlack (driveN 3 5) 2) : TestCountLinear 3 8 := by
  have sh : ∀ k m k', (∀ r, r < 3 → driveN 3 k (r + m) = driveN 3 k' r) →
      (fun u => driveN 3 k (u + m)) = driveN 3 k' := by
    intro k m k' hr
    funext u
    have e1 : driveN 3 k (u + m) = driveN 3 k (u % 3 + m) := by
      simp only [driveN, Nat.mod_add_mod]
    have e2 : driveN 3 k' u = driveN 3 k' (u % 3) := by simp only [driveN, Nat.mod_mod]
    rw [e1, e2]
    exact hr _ (Nat.mod_lt u (by norm_num))
  have tr : ∀ k m k' c, (∀ r, r < 3 → driveN 3 k (r + m) = driveN 3 k' r) →
      TestSlack (driveN 3 k') c → TestSlack (driveN 3 k) (c + m + testsBefore (driveN 3 k) m) :=
    fun k m k' c hr h => testSlack_of_shift_count _ c m (by rw [sh k m k' hr]; exact h)
  intro k hk0 hk
  have hk' : k = 1 ∨ k = 2 ∨ k = 3 ∨ k = 4 ∨ k = 5 ∨ k = 6 ∨ k = 7 := by norm_num at hk; omega
  rcases hk' with rfl | rfl | rfl | rfl | rfl | rfl | rfl
  · exact testSlack_mono (by decide) (tr 1 2 2 5 (by decide) h2)
  · exact testSlack_mono (by norm_num) h2
  · exact testSlack_mono (by decide) (tr 3 1 5 2 (by decide) h5)
  · exact testSlack_mono (by decide) (tr 4 1 2 5 (by decide) h2)
  · exact testSlack_mono (by norm_num) h5
  · exact testSlack_mono (by decide) (tr 6 2 5 2 (by decide) h5)
  · rw [driveN_three_seven]; exact testSlack_mono (by norm_num) testSlack_const_one

end GLM.Rule30
