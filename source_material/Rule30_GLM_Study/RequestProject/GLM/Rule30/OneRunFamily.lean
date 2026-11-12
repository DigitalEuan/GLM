module

public import RequestProject.GLM.Rule30.TurnCost
public import RequestProject.GLM.Rule30.BlackRunWindow

/-!
# Round 37: an infinite family of hubs, uniformly in the period (To Do 39)

The hubs `1^(q−1)0` (one black run of length `q − 1` per period, the word `2^(q−1) − 1` with
time `0` in bit `0`) form an infinite family of wheels.  This file proves, **uniformly in `q`
and in the code length `d`**:

* `wheelRep_oneRun`: every word `1^(q−1)0`, `q ≥ 2`, is a hub (`WheelRep`).
* `failsWithinTests_of_initial_blackRun`: for **every** drive whose first `r` times are black,
  every code of length `d ≤ r − 3` fails within `d + 2` tests (the period-1 slack), because the
  machine cannot tell the drive from the constant black drive before it fails.
* **`oneRun_band`**: for every `q` and every code length `1 ≤ d ≤ q − 4`, every code fails within
  `d + 2` tests of `1^(q−1)0`.  The band of settled code lengths grows linearly with the period;
  no finite certificate gives this for all `q`.
* **The exact remaining requirement.** `oneRunDies_iff_long`: the hub `1^(q−1)0` kills every
  non-empty half-line iff it kills every code of length `d ≥ q − 3`.  The family statement
  `OneRunFamilyDies` contains the open period-2 rung (`halfLineDies_two_of_oneRunFamily`, the
  case `q = 2`), so a proof for the whole family is at least as hard as `HalfLineDies 2`;
  `OneRunFamilyDiesFrom q₀` (all `q ≥ q₀`) is the honest family target for To Do 39.

All results use only the standard axioms.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## Long initial black runs -/

/-- Tests before `t` of a drive black on `[0, t)` are `t`. -/
theorem testsBefore_of_black {bd : ℕ → Bool} {t : ℕ} (h : ∀ s < t, bd s = true) :
    testsBefore bd t = t := by
  induction t with
  | zero => rfl
  | succ t ih =>
    rw [testsBefore_succ, ih (fun s hs => h s (by omega)), h t (by omega)]
    rfl

/-- **A long initial black run behaves like the constant drive.**  If the first `r` times of
`bd` are black and `d + 3 ≤ r`, every code `S < 2^d` fails within `d + 2` tests. -/
theorem failsWithinTests_of_initial_blackRun {bd : ℕ → Bool} {r d S : ℕ}
    (hrun : ∀ t < r, bd t = true) (hr : d + 3 ≤ r) (hS : S < 2 ^ d) :
    FailsWithinTests bd S (d + 2) := by
  obtain ⟨t, ht, -, hf⟩ := (dDiesBy_spec _ S _).1 (constDrive_dies S d hS)
  refine ⟨t, hrun t (by omega), ?_, ?_⟩
  · rw [testsBefore_of_black fun s hs => hrun s (by omega)]; exact ht
  · rw [halfStateD_congr_before S t fun s hs => by rw [hrun s (by omega)], hf,
      hrun (t + 1) (by omega)]

/-! ## The family `1^(q−1)0` -/

/-- The word `1^(q−1)0`: black at times `0, …, q − 2`, white at `q − 1`. -/
def oneRunWord (q : ℕ) : ℕ := 2 ^ (q - 1) - 1

theorem driveN_oneRun_black_mod {q t : ℕ} (ht : t % q < q - 1) :
    driveN q (oneRunWord q) t = true := by
  simp [driveN, oneRunWord, Nat.testBit_two_pow_sub_one, ht]

theorem driveN_oneRun_black {q t : ℕ} (ht : t < q - 1) : driveN q (oneRunWord q) t = true :=
  driveN_oneRun_black_mod (by rw [Nat.mod_eq_of_lt (by omega)]; exact ht)

theorem oneRunWord_lt_half (q : ℕ) : oneRunWord q < 2 ^ (q - 1) := by
  unfold oneRunWord; have := Nat.one_le_two_pow (n := q - 1); omega

/-- **Every word `1^(q−1)0` is a hub.** -/
theorem wheelRep_oneRun {q : ℕ} (hq : 2 ≤ q) : WheelRep q (oneRunWord q) := by
  have hlt := oneRunWord_lt_half q
  have hpow : 2 ^ (q - 1) < 2 ^ q := Nat.pow_lt_pow_right (by norm_num) (by omega)
  -- every proper turn has its top bit set
  have htop : ∀ s, 0 < s → s < q → 2 ^ (q - 1) ≤ wheelTurn q (oneRunWord q) s := by
    intro s hs0 hsq
    apply Nat.ge_two_pow_of_testBit
    rw [wheelTurn, testBit_bitsOf]
    simp only [show q - 1 < q by omega, decide_true, Bool.true_and]
    apply driveN_oneRun_black_mod
    rw [show q - 1 + s = (s - 1) + q * 1 by omega, Nat.add_mul_mod_self_left,
      Nat.mod_eq_of_lt (by omega)]
    omega
  have hturn0 : wheelTurn q (oneRunWord q) 0 = oneRunWord q := wheelTurn_zero (by omega)
  refine ⟨?_, by omega, ?_, ?_⟩
  · unfold oneRunWord
    have : 2 ≤ 2 ^ (q - 1) := by
      calc 2 = 2 ^ 1 := by norm_num
        _ ≤ 2 ^ (q - 1) := Nat.pow_le_pow_right (by norm_num) (by omega)
    omega
  · intro s hs
    rcases Nat.eq_zero_or_pos s with rfl | hs0
    · rw [hturn0]
    · have := htop s hs0 hs; omega
  · intro s hs hs0 heq
    have := htop s hs0 hs; omega

/-- **The band, uniformly in the period.**  For every `q` and every code length `1 ≤ d ≤ q − 4`,
every code of length `d` fails within `d + 2` tests of the hub `1^(q−1)0`. -/
theorem oneRun_band {q d S : ℕ} (hdq : d + 4 ≤ q) (hS : S < 2 ^ d) :
    FailsWithinTests (driveN q (oneRunWord q)) S (d + 2) :=
  failsWithinTests_of_initial_blackRun (r := q - 1) (fun _ ht => driveN_oneRun_black ht)
    (by omega) hS

/-- **The exact remaining requirement for one hub of the family**: it kills every non-empty
half-line iff it kills every code of length `d ≥ q − 3`. -/
theorem oneRunDies_iff_long (q : ℕ) :
    WordDies (driveN q (oneRunWord q)) ↔
      ∀ d S, q ≤ d + 3 → 1 ≤ d → 2 ^ (d - 1) ≤ S → S < 2 ^ d →
        ∃ T, dDiesBy (driveN q (oneRunWord q)) S T = true := by
  constructor
  · intro h d S _ hd h1 _
    exact h S (lt_of_lt_of_le (Nat.one_le_two_pow) h1)
  · intro h S hS
    obtain ⟨h0, h1, h2⟩ := code_length_bounds hS
    by_cases hlong : q ≤ Nat.log2 S + 1 + 3
    · exact h _ S hlong h0 h1 h2
    · exact dDiesBy_of_failsWithinTests (oneRun_band (by omega) h2)

/-- **The family target**: every hub `1^(q−1)0` kills every non-empty half-line. -/
def OneRunFamilyDies : Prop := ∀ q, 2 ≤ q → WordDies (driveN q (oneRunWord q))

/-- The family target from period `q₀` on. -/
def OneRunFamilyDiesFrom (q₀ : ℕ) : Prop := ∀ q, q₀ ≤ q → WordDies (driveN q (oneRunWord q))

theorem oneRunFamilyDies_iff : OneRunFamilyDies ↔ OneRunFamilyDiesFrom 2 := Iff.rfl

/-- **The whole family contains the open period-2 rung** (the case `q = 2`, word `10`). -/
theorem halfLineDies_two_of_oneRunFamily (h : OneRunFamilyDies) : HalfLineDies 2 :=
  halfLineDies_two_iff.2 (by simpa [oneRunWord] using h 2 le_rfl)

/-- The family from `q₀` on is implied by the full wheel. -/
theorem oneRunFamilyDiesFrom_of_wheelDies (h : WheelDies) (q₀ : ℕ) (hq₀ : 2 ≤ q₀) :
    OneRunFamilyDiesFrom q₀ := fun q hq =>
  h q _ (by omega) (wheelRep_oneRun (by omega))

end GLM.Rule30
