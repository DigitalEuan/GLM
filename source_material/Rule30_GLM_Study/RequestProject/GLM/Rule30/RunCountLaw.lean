module

public import RequestProject.GLM.Rule30.Basic

/-!
# Round 23: the exact counting law for periodic runs (two-sided rows)

Round 21's draft proposed a *counting law*: in a left-white row with its black edge at `0` and
free cells `x 1, …, x (d + T)`, exactly `2^(d+1)` of the `2^(d+T)` contexts keep the column at
distance `d` 2-periodic through time `T`, for `2 ≤ T ≤ d`.

* **`runCount_law`** (proved, every period `p ≥ 1`): for `p - 1 ≤ T < d`,
  `RunCount p d T = 2^(d + p - 1)`.  For `p = 2` this is `2^(d+1)` for `1 ≤ T < d`.
* The draft's endpoint `T = d` is **false** in general: `RunCount 2 3 3 = 20 ≠ 16` and
  `RunCount 2 4 4 = 20 ≠ 32` (`runCountTwoLaw_false` in `PowerSeriesLadderData.lean`).  The case
  `T = d` is exactly where the argument below stops: the cell the new test would read is the black
  edge, which is not free.

## Why the law holds (the proof)

Rule 30 is *left-permutive*: `new = left xor (centre or right)`.  Hence (`evolve_flip_left`)
changing only the far-left cell `j` of the light cone of `(t, j + t)` flips that cell.  The column
at distance `d` reads, at time `t`, the cells `d - t, …, d + t`; for `t < d` the far-left cell
`d - t` is a free cell that no earlier test reads.  Flipping it (`Nat.xor` with a power of two)
is an involution of the contexts that keeps all earlier tests and toggles the new one, so each new
test keeps **exactly half** of the surviving contexts (`card_tests_succ`).  This is the two-sided
analogue of Round 22's `survivors_card` for the half-line machine.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-! ## Left-permutivity of Rule 30 on the whole line -/

/-- **Left-permutivity.** If two rows agree on `(j, j + 2t]` and differ at `j`, then after `t`
steps they differ at `j + t`. -/
theorem evolve_flip_left (x y : Config) (j : ℤ) :
    ∀ t : ℕ, x j ≠ y j → (∀ i, j < i → i ≤ j + 2 * t → x i = y i) →
      evolve x t (j + t) ≠ evolve y t (j + t) := by
  intro t
  induction t with
  | zero => intro h _; simpa using h
  | succ t ih =>
    intro hj hagree
    have e1 : evolve x t (j + (t + 1 : ℕ)) = evolve y t (j + (t + 1 : ℕ)) :=
      evolve_congr x y t _ fun i h1 h2 => hagree i (by push_cast at *; omega)
        (by push_cast at *; omega)
    have e2 : evolve x t (j + (t + 1 : ℕ) + 1) = evolve y t (j + (t + 1 : ℕ) + 1) :=
      evolve_congr x y t _ fun i h1 h2 => hagree i (by push_cast at *; omega)
        (by push_cast at *; omega)
    have hl := ih hj fun i h1 h2 => hagree i h1 (by push_cast; omega)
    rw [evolve_succ, evolve_succ, e2,
      show j + ((t + 1 : ℕ) : ℤ) - 1 = j + t by push_cast; ring,
      show j + ((t + 1 : ℕ) : ℤ) = j + (t + 1 : ℕ) from rfl, e1]
    simp only [rule30]
    intro h
    exact hl (by simpa using congrArg (fun b => xor b (evolve y t (j + (t + 1 : ℕ)) ||
      evolve y t (j + (t + 1 : ℕ) + 1))) h)

/-! ## Contexts and the count -/

/-- The left-white row with black edge at `0` and free cells `x 1, …, x n` read from the bits of
`P` (`x c = P.testBit (c - 1)`), white beyond `n`. -/
def ctxRow (n P : ℕ) : Config := fun c =>
  if c = 0 then true else if 0 < c ∧ c ≤ n then P.testBit (c.toNat - 1) else false

/-- The column at distance `d` repeats with period `p` at time `t`. -/
def PeriodTest (p d : ℕ) (x : Config) (t : ℕ) : Prop := evolve x t d = evolve x (t - p) d

instance (p d : ℕ) (x : Config) (t : ℕ) : Decidable (PeriodTest p d x t) := by
  unfold PeriodTest; infer_instance

/-- The contexts `P < 2^n` passing every period test at the times `p ≤ t ≤ T`. -/
def passing (p d n T : ℕ) : Finset ℕ :=
  (range (2 ^ n)).filter fun P => ∀ t ∈ Icc p T, PeriodTest p d (ctxRow n P) t

/-- **`RunCount p d T`**: the number of left-white contexts (free cells `x 1 … x (d+T)`, black edge)
keeping the column at distance `d` `p`-periodic through time `T`. -/
def RunCount (p d T : ℕ) : ℕ := (passing p d (d + T) T).card

/-- Flipping bit `k` of the context changes exactly the cell `k + 1`. -/
theorem ctxRow_xor (n P k : ℕ) (hk : k < n) (c : ℤ) :
    ctxRow n (P ^^^ 2 ^ k) c = if c = (k + 1 : ℕ) then !ctxRow n P c else ctxRow n P c := by
  unfold ctxRow
  by_cases h0 : c = 0
  · subst h0
    rw [if_neg (by omega : (0 : ℤ) ≠ ((k + 1 : ℕ) : ℤ))]
    simp
  · by_cases hc : 0 < c ∧ c ≤ n
    · simp only [h0, if_false, hc, and_self, if_true, Nat.testBit_xor, Nat.testBit_two_pow]
      by_cases hck : c = (k + 1 : ℕ)
      · subst hck; simp
      · rw [if_neg hck]
        have : ¬ (k = c.toNat - 1) := by omega
        simp [this]
    · simp only [h0, if_false, hc]
      have : c ≠ (k + 1 : ℕ) := by omega
      rw [if_neg this]

/-- The column test at time `t` with `t < d` is toggled by flipping the cell `d - t`, and the tests
(and column values) at earlier times are unchanged. -/
theorem column_flip (n P d t : ℕ) (ht : t < d) (hn : d ≤ n) :
    (∀ s < t, evolve (ctxRow n (P ^^^ 2 ^ (d - t - 1))) s d = evolve (ctxRow n P) s d) ∧
      evolve (ctxRow n (P ^^^ 2 ^ (d - t - 1))) t d ≠ evolve (ctxRow n P) t d := by
  have hx := ctxRow_xor n P (d - t - 1) (by omega)
  constructor
  · intro s hs
    refine evolve_congr _ _ s _ fun i h1 h2 => ?_
    rw [hx i, if_neg (by push_cast; omega)]
  · have := evolve_flip_left (ctxRow n (P ^^^ 2 ^ (d - t - 1))) (ctxRow n P) ((d : ℤ) - t) t
      (by rw [hx, if_pos (by push_cast; omega)]; simp)
      (fun i h1 h2 => by rw [hx i, if_neg (by push_cast; omega)])
    simpa using this

theorem xor_two_pow_lt {P n k : ℕ} (hP : P < 2 ^ n) (hk : k < n) : P ^^^ 2 ^ k < 2 ^ n :=
  Nat.xor_lt_two_pow hP (Nat.pow_lt_pow_right (by norm_num) hk)

/-- **Each fresh test halves the survivors, exactly.** -/
theorem card_tests_succ (p d n T : ℕ) (hp : 1 ≤ p) (hpT : p ≤ T + 1) (hTd : T + 1 < d)
    (hn : d ≤ n) : 2 * (passing p d n (T + 1)).card = (passing p d n T).card := by
  set k := d - (T + 1) - 1
  have hk : k < n := by omega
  have hsplit : passing p d n (T + 1) =
      (passing p d n T).filter fun P => PeriodTest p d (ctxRow n P) (T + 1) := by
    ext P
    simp only [passing, mem_filter, mem_range, mem_Icc]
    constructor
    · rintro ⟨h1, h2⟩; exact ⟨⟨h1, fun t ht => h2 t ⟨ht.1, by omega⟩⟩, h2 _ ⟨hpT, le_rfl⟩⟩
    · rintro ⟨⟨h1, h2⟩, h3⟩
      refine ⟨h1, fun t ht => ?_⟩
      rcases Nat.lt_or_ge t (T + 1) with h | h
      · exact h2 t ⟨ht.1, by omega⟩
      · rwa [show t = T + 1 by omega]
  have hcf : ∀ P, (∀ s < T + 1, evolve (ctxRow n (P ^^^ 2 ^ k)) s d = evolve (ctxRow n P) s d) ∧
      evolve (ctxRow n (P ^^^ 2 ^ k)) (T + 1) d ≠ evolve (ctxRow n P) (T + 1) d :=
    fun P => column_flip n P d (T + 1) (by omega) hn
  -- flipping keeps the earlier tests
  have hkeep : ∀ P, ∀ t ≤ T, (PeriodTest p d (ctxRow n (P ^^^ 2 ^ k)) t ↔
      PeriodTest p d (ctxRow n P) t) := by
    intro P t ht
    unfold PeriodTest
    rw [(hcf P).1 t (by omega), (hcf P).1 (t - p) (by omega)]
  -- and toggles the new one
  have htog : ∀ P, (PeriodTest p d (ctxRow n (P ^^^ 2 ^ k)) (T + 1) ↔
      ¬ PeriodTest p d (ctxRow n P) (T + 1)) := by
    intro P
    unfold PeriodTest
    rw [(hcf P).1 (T + 1 - p) (by omega)]
    have := (hcf P).2
    cases h1 : evolve (ctxRow n (P ^^^ 2 ^ k)) (T + 1) d <;>
      cases h2 : evolve (ctxRow n P) (T + 1) d <;>
      cases evolve (ctxRow n P) (T + 1 - p) d <;> simp_all
  have hmem : ∀ P, P ∈ passing p d n T → P ^^^ 2 ^ k ∈ passing p d n T := by
    intro P hP
    simp only [passing, mem_filter, mem_range, mem_Icc] at hP ⊢
    exact ⟨xor_two_pow_lt hP.1 hk, fun t ht => (hkeep P t ht.2).2 (hP.2 t ht)⟩
  have hbij : ((passing p d n T).filter fun P => PeriodTest p d (ctxRow n P) (T + 1)).card =
      ((passing p d n T).filter fun P => ¬ PeriodTest p d (ctxRow n P) (T + 1)).card := by
    refine Finset.card_nbij' (fun P => P ^^^ 2 ^ k) (fun P => P ^^^ 2 ^ k) ?_ ?_ ?_ ?_
    · intro P hP
      simp only [coe_filter, Set.mem_setOf_eq] at hP ⊢
      exact ⟨hmem P hP.1, fun h => (htog P).1 h hP.2⟩
    · intro P hP
      simp only [coe_filter, Set.mem_setOf_eq] at hP ⊢
      exact ⟨hmem P hP.1, (htog P).2 hP.2⟩
    · intro P _
      show (P ^^^ 2 ^ k) ^^^ 2 ^ k = P
      rw [Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]
    · intro P _
      show (P ^^^ 2 ^ k) ^^^ 2 ^ k = P
      rw [Nat.xor_assoc, Nat.xor_self, Nat.xor_zero]
  have := Finset.card_filter_add_card_filter_not (s := passing p d n T)
    (fun P => PeriodTest p d (ctxRow n P) (T + 1))
  rw [hsplit]
  omega

/-- Before the first test nothing is excluded. -/
theorem passing_card_of_lt (p d n T : ℕ) (hT : T < p) : (passing p d n T).card = 2 ^ n := by
  rw [passing, Finset.filter_true_of_mem, card_range]
  intro P _ t ht
  simp only [mem_Icc] at ht
  omega

/-- The count at level `T` (for `T < d`): `2^n` before the first test, then halved per test. -/
theorem passing_card (p d n : ℕ) (hp : 1 ≤ p) (hn : d ≤ n) :
    ∀ T, T < d → (passing p d n T).card * 2 ^ (T + 1 - p) = 2 ^ n := by
  intro T
  induction T with
  | zero => intro _; rw [passing_card_of_lt p d n 0 (by omega)]; simp [show 1 - p = 0 by omega]
  | succ T ih =>
    intro hT
    rcases Nat.lt_or_ge (T + 1) p with h | h
    · rw [passing_card_of_lt p d n (T + 1) h, show T + 1 + 1 - p = 0 by omega]; simp
    · have h2 := card_tests_succ p d n T hp h (by omega) hn
      rw [← ih (by omega), ← h2, show T + 1 + 1 - p = (T + 1 - p) + 1 by omega, pow_succ]
      ring

/-- **The counting law (corrected).** For every period `p ≥ 1` and `p - 1 ≤ T < d`, exactly
`2^(d + p - 1)` of the `2^(d + T)` contexts keep the column at distance `d` `p`-periodic through
time `T`.  For `p = 2`: `RunCount 2 d T = 2^(d+1)` for `1 ≤ T < d`. -/
theorem runCount_law (p d T : ℕ) (hp : 1 ≤ p) (hpT : p ≤ T + 1) (hTd : T < d) :
    RunCount p d T = 2 ^ (d + p - 1) := by
  have h := passing_card p d (d + T) hp (by omega) T hTd
  have h2 : 2 ^ (d + T) = 2 ^ (d + p - 1) * 2 ^ (T + 1 - p) := by
    rw [← pow_add]; congr 1; omega
  rw [h2] at h
  exact Nat.eq_of_mul_eq_mul_right (by positivity) h

/-- The period-2 case of the counting law. -/
theorem runCount_two_law (d T : ℕ) (hT : 1 ≤ T) (hTd : T < d) : RunCount 2 d T = 2 ^ (d + 1) :=
  runCount_law 2 d T (by norm_num) (by omega) hTd

/-! ## The Round 21 draft statements (refuted in `PowerSeriesLadderData.lean`) -/

/-- The draft counting law, with the endpoint `T = d` included.  **False**:
`runCountTwoLawDraft_false` (`RunCount 2 3 3 = 20`). -/
def RunCountTwoLawDraft : Prop := ∀ d T, 2 ≤ T → T ≤ d → RunCount 2 d T = 2 ^ (d + 1)

/-- The draft "barrier entropy" monotonicity: after `T = d` the deficit
`d + T - log₂ RunCount 2 d T` strictly increases (integer form).  **False**:
`deficitIncreasingAfterD_false` (`d = 1`, `T = 3`: the counts are `1` then `2`, so the deficit
stays at `4`). -/
def DeficitIncreasingAfterD : Prop :=
  ∀ d T, d < T → (RunCount 2 d (T + 1) ≠ 0 →
    2 ^ (d + T + 1) / RunCount 2 d (T + 1) > 2 ^ (d + T) / RunCount 2 d T)

end GLM.Rule30
