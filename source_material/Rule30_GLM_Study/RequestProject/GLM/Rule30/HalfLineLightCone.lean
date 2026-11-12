module

public import RequestProject.GLM.Rule30.HalfLineMachine

/-!
# Round 22: the light cone of the half-line machine, and the exact count of the early tests

The driven half-line machine of `HalfLineMachine.lean` has a light cone: cell `i` at time `t`
reads only the cells `0, …, i + t` of the starting code.  Rule 30 is also *left-permutive*: a new
cell is `left xor (centre or right)`, so the far-left cell of the cone enters by `xor`.  Two
consequences, both proved here for **every** drive sequence:

* `halfStateD_testBit_congr` — two codes that agree on the bits `< n` give states that agree on
  the bits `i` with `i + t < n` at time `t`.
* `halfStateD_testBit_flip` — if the codes agree below bit `n` and differ at bit `n`, then at time
  `t ≤ n` the states differ at bit `n - t`.  In particular the cell next to the column at time `t`
  flips when bit `t` of the code flips.
* `dDiesBy_congr` — whether the machine fails before time `k` depends only on the bits `< k` of the
  code.  (This makes the prefix search of `PrefixSearch.lean` sound.)
* **`survivors_card`** — the number of codes `P < 2^k` that pass every check before time `k` is
  exactly `2^(k - blacks k)`, where `blacks k` is the number of black drive times before `k`.
  Each black time halves the survivors, exactly.

The last statement is the formal half of the Round 21 counting heuristic ("one test every black
time, each test kills half"): it holds **exactly** for the first `d - 1` tests of a code of length
`d`, because each of those tests reads a fresh free bit of the code (`survivors_card`).  After time
`d - 1` the code has no free bits left and the tests are deterministic; whether they keep killing
is the open core of `HalfLineDies`.
-/

@[expose] public section

namespace GLM.Rule30

/-- **Light cone.** Codes agreeing on the bits `< n` give states agreeing on the bits `i` with
`i + t < n` at time `t`, for every drive. -/
theorem halfStateD_testBit_congr (bd : ℕ → Bool) {S S' n : ℕ}
    (h : ∀ i < n, S.testBit i = S'.testBit i) :
    ∀ t i, i + t < n → (halfStateD bd S t).testBit i = (halfStateD bd S' t).testBit i := by
  intro t
  induction t with
  | zero => intro i hi; exact h i (by omega)
  | succ t ih =>
    intro i hi
    simp only [halfStateD]
    rw [testBit_halfStep, testBit_halfStep, ih (i + 1) (by omega), ih i (by omega)]
    rcases Nat.eq_zero_or_pos i with rfl | hi0
    · simp
    · rw [if_neg hi0.ne', if_neg hi0.ne', ih (i - 1) (by omega)]

/-- **Left-permutivity in the half-line.** If two codes agree below bit `n` and differ at bit `n`,
the states at time `t ≤ n` differ at bit `n - t`. -/
theorem halfStateD_testBit_flip (bd : ℕ → Bool) {S S' n : ℕ}
    (h : ∀ i < n, S.testBit i = S'.testBit i) (hn : S.testBit n ≠ S'.testBit n) :
    ∀ t ≤ n, (halfStateD bd S t).testBit (n - t) ≠ (halfStateD bd S' t).testBit (n - t) := by
  intro t
  induction t with
  | zero => intro _; simpa using hn
  | succ t ih =>
    intro ht
    simp only [halfStateD]
    rw [testBit_halfStep, testBit_halfStep, show n - (t + 1) + 1 = n - t by omega]
    have hc := halfStateD_testBit_congr bd h
    have e : ((halfStateD bd S t).testBit (n - (t + 1)) ||
          (if n - (t + 1) = 0 then bd t else (halfStateD bd S t).testBit (n - (t + 1) - 1))) =
        ((halfStateD bd S' t).testBit (n - (t + 1)) ||
          (if n - (t + 1) = 0 then bd t else (halfStateD bd S' t).testBit (n - (t + 1) - 1))) := by
      rw [hc t (n - (t + 1)) (by omega)]
      split
      · rfl
      · rw [hc t (n - (t + 1) - 1) (by omega)]
    rw [e]
    intro h'
    exact ih (by omega) (by simpa using h')

/-- Whether the machine fails before time `k` depends only on the bits `< k` of the code. -/
theorem dDiesBy_congr (bd : ℕ → Bool) {S S' k : ℕ} (h : ∀ i < k, S.testBit i = S'.testBit i) :
    dDiesBy bd S k = dDiesBy bd S' k := by
  apply Bool.eq_iff_iff.2
  rw [dDiesBy_spec, dDiesBy_spec]
  have hc := halfStateD_testBit_congr bd h
  constructor
  · rintro ⟨t, ht, hb, h'⟩; exact ⟨t, ht, hb, by rw [← hc t 0 (by omega)]; exact h'⟩
  · rintro ⟨t, ht, hb, h'⟩; exact ⟨t, ht, hb, by rw [hc t 0 (by omega)]; exact h'⟩

/-- Failure before `k` depends only on `S % 2^k`. -/
theorem dDiesBy_mod (bd : ℕ → Bool) (S k : ℕ) : dDiesBy bd (S % 2 ^ k) k = dDiesBy bd S k :=
  dDiesBy_congr bd fun i hi => by rw [Nat.testBit_mod_two_pow]; simp [hi]

/-- One more step of the failure search. -/
theorem dDiesBy_succ (bd : ℕ → Bool) (S k : ℕ) :
    dDiesBy bd S (k + 1) =
      (dDiesBy bd S k || (bd k && ((halfStateD bd S k).testBit 0 == bd (k + 1)))) := by
  apply Bool.eq_iff_iff.2
  simp only [Bool.or_eq_true, Bool.and_eq_true, beq_iff_eq, dDiesBy_spec]
  constructor
  · rintro ⟨t, ht, h⟩
    rcases Nat.lt_succ_iff_lt_or_eq.1 ht with ht | rfl
    · exact Or.inl ⟨t, ht, h⟩
    · exact Or.inr h
  · rintro (⟨t, ht, h⟩ | h)
    · exact ⟨t, by omega, h⟩
    · exact ⟨k, by omega, h⟩

/-! ## The exact count of the early tests -/

/-- The number of black drive times before `k`. -/
def blacks (bd : ℕ → Bool) (k : ℕ) : ℕ := ((Finset.range k).filter fun t => bd t = true).card

/-- The codes `P < 2^k` that pass every check before time `k`. -/
def survivors (bd : ℕ → Bool) (k : ℕ) : Finset ℕ :=
  (Finset.range (2 ^ k)).filter fun P => dDiesBy bd P k = false

theorem blacks_succ (bd : ℕ → Bool) (k : ℕ) :
    blacks bd (k + 1) = blacks bd k + (if bd k = true then 1 else 0) := by
  simp only [blacks, Finset.range_add_one, Finset.filter_insert]
  split
  · rw [Finset.card_insert_of_notMem (by simp)]
  · simp

theorem blacks_le (bd : ℕ → Bool) (k : ℕ) : blacks bd k ≤ k :=
  (Finset.card_filter_le _ _).trans (by simp)

/-- The survivors of length `k + 1` split by their top bit. -/
theorem survivors_card_succ (bd : ℕ → Bool) (k : ℕ) :
    (survivors bd (k + 1)).card =
      (if bd k = true then 1 else 2) * (survivors bd k).card := by
  simp only [survivors, Finset.card_filter]
  rw [pow_succ, mul_two, Finset.sum_range_add, Finset.mul_sum, ← Finset.sum_add_distrib]
  apply Finset.sum_congr rfl
  intro P hP
  rw [Finset.mem_range] at hP
  -- the two extensions agree with `P` below bit `k`
  have hagree : ∀ i < k, P.testBit i = (2 ^ k + P).testBit i := by
    intro i hi
    rw [Nat.testBit_two_pow_add_gt hi]
  have hk1 : P.testBit k = false := Nat.testBit_eq_false_of_lt hP
  have hk2 : (2 ^ k + P).testBit k = true := by
    rw [Nat.testBit_two_pow_add_eq, hk1]; rfl
  have hsame : dDiesBy bd (2 ^ k + P) k = dDiesBy bd P k := (dDiesBy_congr bd hagree).symm
  have hflip := halfStateD_testBit_flip bd hagree (by rw [hk1, hk2]; simp) k le_rfl
  rw [Nat.sub_self] at hflip
  rw [dDiesBy_succ, dDiesBy_succ, hsame]
  cases hD : dDiesBy bd P k
  · cases hb : bd k
    · simp
    · simp only [Bool.false_or, Bool.true_and, if_true]
      cases h1 : (halfStateD bd P k).testBit 0 <;>
        cases h2 : (halfStateD bd (2 ^ k + P) k).testBit 0 <;>
        cases bd (k + 1) <;> simp_all
  · simp

/-- **Each black time halves the survivors, exactly.** For every drive sequence, the number of
codes `P < 2^k` that pass every check before time `k` is `2^(k - blacks k)`. -/
theorem survivors_card (bd : ℕ → Bool) (k : ℕ) :
    (survivors bd k).card = 2 ^ (k - blacks bd k) := by
  induction k with
  | zero => simp [survivors, blacks, dDiesBy, dRunAux]
  | succ k ih =>
    rw [survivors_card_succ, ih, blacks_succ]
    have := blacks_le bd k
    split
    · rw [one_mul]; congr 1; omega
    · rw [show k + 1 - (blacks bd k + 0) = (k - blacks bd k) + 1 by omega, pow_succ]; ring

end GLM.Rule30
