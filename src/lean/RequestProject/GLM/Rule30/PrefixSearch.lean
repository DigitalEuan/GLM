module

public import RequestProject.GLM.Rule30.HalfLineLightCone

/-!
# Round 22: the prefix search — a sound certificate that visits about `2^(d/2)` codes

`drivenCheck p d T` (Round 21) simulates all `2^(d-1)` codes of length `d`.  By the light cone
(`dDiesBy_congr`) a code that fails before time `k` fails because of its bits `< k` alone, so all
of its extensions fail too.  The prefix search builds the code bit by bit, from the column outward,
and drops a prefix as soon as it fails a check:

* `prefixSearch bd T n k P` — every code `S` with `S % 2^k = P` and top bit at `k + n` fails before
  `T` (`prefixSearch_sound`);
* `prefixCheck p d T` — the prefix search for every non-zero drive word of period `p`;
* **`drivenCheck_of_prefixCheck`** — the prefix check implies the full check, so every Round 21
  consequence (`drivenRunBoundUpTo_of_checks`) applies unchanged.

By `survivors_card` the search keeps exactly `2^(k - blacks k)` prefixes of length `k`, so for an
alternating drive it visits about `2^(d/2)` nodes instead of `2^d` codes.

For period 2 the Round 21 machine `halfDiesBy` is the driven machine with drive word `1` or `2`
(`halfDiesBy_eq_dDiesBy`); `halfLineLinear_of_prefixCheck` turns prefix checks into the linear
target `PeriodTwoHalfLineLinear` on a range of `d`.

Also new: `HalfLineLinear p a b`, the linear one-sided target for every period, and
`halfLineDies_of_linear`.
-/

@[expose] public section

namespace GLM.Rule30

/-- The prefix search.  `prefixSearch bd T n k P` checks the codes `S` with `S % 2^k = P` whose top
(black) bit is bit `k + n`: either the prefix `P` already fails before time `k ≤ T`, or both
one-bit extensions pass the search; at `n = 0` the code is `P + 2^k`, simulated to time `T`. -/
def prefixSearch (bd : ℕ → Bool) (T : ℕ) : ℕ → ℕ → ℕ → Bool
  | 0, k, P => dDiesBy bd (P + 2 ^ k) T
  | n + 1, k, P => (decide (k ≤ T) && dDiesBy bd P k) ||
      (prefixSearch bd T n (k + 1) P && prefixSearch bd T n (k + 1) (P + 2 ^ k))

/-- `S % 2^(k+1)` is `S % 2^k` plus the bit `k`. -/
theorem mod_two_pow_succ_cases (S k : ℕ) :
    S % 2 ^ (k + 1) = S % 2 ^ k ∨ S % 2 ^ (k + 1) = S % 2 ^ k + 2 ^ k := by
  rw [Nat.mod_pow_succ]
  have : S / 2 ^ k % 2 < 2 := Nat.mod_lt _ (by norm_num)
  interval_cases h : S / 2 ^ k % 2 <;> simp

/-- **Soundness of the prefix search.** -/
theorem prefixSearch_sound (bd : ℕ → Bool) (T : ℕ) :
    ∀ n k P, prefixSearch bd T n k P = true →
      ∀ S, S % 2 ^ k = P → 2 ^ (k + n) ≤ S → S < 2 ^ (k + n + 1) → dDiesBy bd S T = true := by
  intro n
  induction n with
  | zero =>
    intro k P h S hP h1 h2
    simp only [prefixSearch] at h
    have hdiv : S / 2 ^ k = 1 := by
      apply Nat.div_eq_of_lt_le
      · simpa using h1
      · rw [pow_succ] at h2; omega
    have := Nat.div_add_mod S (2 ^ k)
    rw [hdiv, mul_one, hP] at this
    rwa [← this, add_comm]
  | succ n ih =>
    intro k P h S hP h1 h2
    simp only [prefixSearch, Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq] at h
    rcases h with ⟨hkT, hd⟩ | ⟨ha, hb⟩
    · rw [← hP, dDiesBy_mod] at hd
      exact dDiesBy_mono hd hkT
    · rcases mod_two_pow_succ_cases S k with e | e
      · exact ih (k + 1) P ha S (by rw [e, hP]) (by rw [show k + 1 + n = k + (n + 1) by ring]; exact h1)
          (by rw [show k + 1 + n = k + (n + 1) by ring]; exact h2)
      · exact ih (k + 1) (P + 2 ^ k) hb S (by rw [e, hP])
          (by rw [show k + 1 + n = k + (n + 1) by ring]; exact h1)
          (by rw [show k + 1 + n = k + (n + 1) by ring]; exact h2)

/-- Every code of length `d ≥ 1` (top bit `d - 1`) fails before `T` if the search from the empty
prefix succeeds. -/
theorem dDiesBy_of_prefixSearch {bd : ℕ → Bool} {T d S : ℕ} (hd : 1 ≤ d)
    (h : prefixSearch bd T (d - 1) 0 0 = true) (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) :
    dDiesBy bd S T = true :=
  prefixSearch_sound bd T (d - 1) 0 0 h S (by simp [Nat.mod_one]) (by simpa using h1)
    (by rw [show 0 + (d - 1) + 1 = d by omega]; exact h2)

/-- The prefix check for period `p`, distance `d`, horizon `T`: the prefix search succeeds for
every non-zero drive word. -/
def prefixCheck (p d T : ℕ) : Bool :=
  (List.range (2 ^ p - 1)).all fun j => prefixSearch (driveN p (j + 1)) T (d - 1) 0 0

/-- **The prefix check implies the full Round 21 check.** -/
theorem drivenCheck_of_prefixCheck {p d T : ℕ} (hd : 1 ≤ d) (h : prefixCheck p d T = true) :
    drivenCheck p d T = true := by
  unfold prefixCheck at h
  unfold drivenCheck
  rw [List.all_eq_true] at h ⊢
  intro j hj
  rw [List.all_eq_true]
  intro k hk
  rw [List.mem_range] at hk
  have hd' : 2 ^ d = 2 ^ (d - 1) + 2 ^ (d - 1) := by
    rw [← two_mul, ← pow_succ']; congr 1; omega
  exact dDiesBy_of_prefixSearch hd (h j hj) (by omega) (by omega)

/-! ## Period 2: the Round 21 machine is the driven machine -/

theorem halfState_eq_halfStateD (S φ : ℕ) : ∀ t, halfState S φ t = halfStateD (altBit φ) S t
  | 0 => rfl
  | t + 1 => by simp only [halfState, halfStateD, halfState_eq_halfStateD S φ t]

theorem altBit_zero_eq_driveN : altBit 0 = driveN 2 1 := by
  funext t
  simp only [altBit, driveN]
  rcases Nat.mod_two_eq_zero_or_one t with h | h <;> simp only [h] <;> decide

theorem altBit_one_eq_driveN : altBit 1 = driveN 2 2 := by
  funext t
  simp only [altBit, driveN]
  rcases Nat.mod_two_eq_zero_or_one t with h | h <;> simp only [h] <;> decide

/-- **The period-2 machine of Round 21 is the driven machine** with the alternating drive. -/
theorem halfDiesBy_eq_dDiesBy (S φ T : ℕ) : halfDiesBy S φ T = dDiesBy (altBit φ) S T := by
  apply Bool.eq_iff_iff.2
  rw [halfDiesBy_spec, dDiesBy_spec]
  have hnext : ∀ t, altBit φ t = true → altBit φ (t + 1) = false := by
    intro t h
    simp only [altBit, decide_eq_true_eq, decide_eq_false_iff_not] at h ⊢
    omega
  constructor
  · rintro ⟨t, ht, hb, h⟩
    exact ⟨t, ht, hb, by rw [← halfState_eq_halfStateD, h, hnext t hb]⟩
  · rintro ⟨t, ht, hb, h⟩
    exact ⟨t, ht, hb, by rw [halfState_eq_halfStateD, h, hnext t hb]⟩

/-- **Prefix checks give the period-2 linear target on a range.** -/
theorem halfLineLinear_of_prefixCheck {D : ℕ}
    (h : ∀ d ≤ D, 1 ≤ d → prefixCheck 2 d (2 * d + 9) = true) :
    ∀ d S : ℕ, d ≤ D → 2 ^ (d - 1) ≤ S → S < 2 ^ d → 1 ≤ d →
      ∀ φ : ℕ, φ = 0 ∨ φ = 1 → halfDiesBy S φ (2 * d + 9) = true := by
  intro d S hd h1 h2 hd1 φ hφ
  have hc := h d hd hd1
  unfold prefixCheck at hc
  rw [List.all_eq_true] at hc
  rw [halfDiesBy_eq_dDiesBy]
  rcases hφ with rfl | rfl
  · rw [altBit_zero_eq_driveN]
    exact dDiesBy_of_prefixSearch hd1 (hc 0 (by simp)) h1 h2
  · rw [altBit_one_eq_driveN]
    exact dDiesBy_of_prefixSearch hd1 (hc 1 (by simp)) h1 h2

/-! ## The linear one-sided target, every period -/

/-- **Linear one-sided target for period `p`**, slope `a`, offset `b`: for every non-zero drive
word of period `p` and every code with top bit `d - 1`, the machine fails by time `a d + b`. -/
def HalfLineLinear (p a b : ℕ) : Prop :=
  ∀ k, 0 < k → k < 2 ^ p → ∀ d S : ℕ, 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
    dDiesBy (driveN p k) S (a * d + b) = true

/-- The linear target implies the one-sided target `HalfLineDies p`. -/
theorem halfLineDies_of_linear {p a b : ℕ} (h : HalfLineLinear p a b) : HalfLineDies p := by
  intro k hk0 hk S hS
  refine ⟨_, h k hk0 hk (Nat.log 2 S + 1) S (by omega) ?_ ?_⟩
  · simpa using Nat.pow_log_le_self 2 hS.ne'
  · exact Nat.lt_pow_succ_log_self (by norm_num) S

/-- Prefix checks give the linear target on a range of `d`. -/
theorem halfLineLinear_upTo_of_prefixCheck {p a b D : ℕ}
    (h : ∀ d ≤ D, 1 ≤ d → prefixCheck p d (a * d + b) = true) :
    ∀ k, 0 < k → k < 2 ^ p → ∀ d S : ℕ, d ≤ D → 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
      dDiesBy (driveN p k) S (a * d + b) = true := by
  intro k hk0 hk d S hd hd1 h1 h2
  have hc := h d hd hd1
  unfold prefixCheck at hc
  rw [List.all_eq_true] at hc
  have := hc (k - 1) (List.mem_range.2 (by omega))
  rw [show k - 1 + 1 = k by omega] at this
  exact dDiesBy_of_prefixSearch hd1 this h1 h2

end GLM.Rule30
