module

public import RequestProject.GLM.Rule30.ElementaryCA

/-!
# Round 24: alternatives to XOR

Rule 30 is `new = L xor (C or R)`.  This file tests whether the *implementation choice* of the
XOR matters, in two senses.

## A. Other ways of writing the same rule (implementation only)

`rule30_eq_bne`, `rule30_eq_ite`, `rule30_eq_orAndNot`, `rule30_eq_natMod`, `rule30_eq_intSq`,
`rule30_eq_intAbs`, `rule30_eq_maxSubMin`: seven XOR-free formulas for the same local rule
(inequality, a branch on `L`, OR/AND/NOT, arithmetic mod 2, `(L - (C ∨ R))²`, `|L - (C ∨ R)|`,
`max - min`).  `tableNum_implementations` : each of them has wheel number `30`, so
(`implementation_invariance`) every one of them produces the same space-time diagram and the same
centre column: **no question about Rule 30 can depend on how the XOR is implemented**.  The one
thing every implementation must contain is a non-monotone gate (`rule30_not_monotone`).

## B. Other gates in place of XOR (a different rule)

`outerRule g` is the wheel `g(L, C or R)` for a two-input gate `g : BinGate` (16 gates).
* `outerRule_xor` : `g = xor` gives 30.
* **`outer_alternative_periodic`** : for **every** other gate `g` (including `xnor`, which gives
  wheel 225), the centre column from the single black cell is eventually periodic.  So, among the
  16 ways of combining `L` with `C or R`, Rule 30 is the only one whose Problem 1 is open.
* `outerRule_leftPermutive_iff` : `g(L, C or R)` is left-permutive iff `g` is `xor`, `xnor`, `L`
  or `not L` (wheels 30, 225, 240, 15).  Wheel 225 (`xnor`) is left-permutive and genuinely reads
  `C or R`, but its centre column is eventually all black (`centre225_eventually_black`,
  `leftPermutive_not_sufficient`): left-permutivity alone does not produce the irregularity; the
  white background (`g(0, 0) = 0`) matters too.

`innerRule h` is the wheel `L xor h(C, R)` (16 gates `h`); these are exactly the 16 left-permutive
wheels (`leftPermutive_iff_innerRule`).
* **`inner_alternative_periodic`** : if `h` is not of OR type (OR type = exactly three of the four
  inputs give `true`: `or`, `nand`, and the two implications), the centre column of
  `L xor h(C, R)` from the single black cell is eventually periodic.  Affine `h` (8 gates) and
  AND-type `h` (4 gates) all collapse.
* The four OR-type gates give wheels 30, 45, 75, 135 (`innerRule_orType`), whose centre-column
  questions are all open here.

So the XOR is what makes the counting law work (Round 23; `RunCountGeneral.lean` proves the law
for all 16 left-permutive wheels), and the OR (more precisely: a gate with three `true` outputs) is
what keeps the column from collapsing.  Neither alone is enough.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## A. Implementations of the same rule -/

/-- Rule 30 as an inequality test: black iff `L ≠ (C ∨ R)`. -/
theorem rule30_eq_bne (L C R : Bool) : rule30 L C R = (L != (C || R)) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Rule 30 as a branch on the left cell. -/
theorem rule30_eq_ite (L C R : Bool) : rule30 L C R = if L then !(C || R) else (C || R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Rule 30 with OR, AND and NOT only: black iff some cell is black and not both `L` and
`C ∨ R`. -/
theorem rule30_eq_orAndNot (L C R : Bool) :
    rule30 L C R = ((L || C || R) && !(L && (C || R))) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Rule 30 as arithmetic mod 2 on `{0, 1}`: `L + C + R + C·R mod 2`. -/
theorem rule30_eq_natMod (L C R : Bool) :
    (rule30 L C R).toNat = (L.toNat + C.toNat + R.toNat + C.toNat * R.toNat) % 2 := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Rule 30 as a square over the integers: `(L - (C ∨ R))²`. -/
theorem rule30_eq_intSq (L C R : Bool) :
    ((rule30 L C R).toNat : ℤ) = ((L.toNat : ℤ) - (C || R).toNat) ^ 2 := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Rule 30 as a distance: `|L - (C ∨ R)|`. -/
theorem rule30_eq_intAbs (L C R : Bool) :
    ((rule30 L C R).toNat : ℤ) = |(L.toNat : ℤ) - (C || R).toNat| := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Rule 30 as `max − min` of `L` and `C ∨ R`. -/
theorem rule30_eq_maxSubMin (L C R : Bool) :
    (rule30 L C R).toNat = max L.toNat (C || R).toNat - min L.toNat (C || R).toNat := by
  cases L <;> cases C <;> cases R <;> rfl

/-- All seven implementations have wheel number `30`. -/
theorem tableNum_implementations :
    tableNum (fun L C R => L != (C || R)) = 30 ∧
    tableNum (fun L C R => if L then !(C || R) else (C || R)) = 30 ∧
    tableNum (fun L C R => (L || C || R) && !(L && (C || R))) = 30 ∧
    tableNum (fun L C R => decide ((L.toNat + C.toNat + R.toNat + C.toNat * R.toNat) % 2 = 1))
      = 30 ∧
    tableNum (fun L C R => decide (((L.toNat : ℤ) - (C || R).toNat) ^ 2 = 1)) = 30 ∧
    tableNum (fun L C R => decide (|(L.toNat : ℤ) - (C || R).toNat| = 1)) = 30 ∧
    tableNum (fun L C R => decide (max L.toNat (C || R).toNat - min L.toNat (C || R).toNat = 1))
      = 30 := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> decide

/-- **Implementation invariance.** Any local rule that agrees with `rule30` on the eight
neighbourhoods (however it is computed) has the same evolution from every row, hence the same
centre column. -/
theorem implementation_invariance (f : Bool → Bool → Bool → Bool)
    (hf : ∀ L C R, f L C R = rule30 L C R) (x : Config) :
    ecaEvolve (tableNum f) x = evolve x := by
  have : tableNum f = 30 := by
    have : f = rule30 := funext fun L => funext fun C => funext fun R => hf L C R
    subst this; decide
  rw [this, ecaEvolve_thirty]

/-- Rule 30 is not monotone (black `L` can turn the output white), so every implementation needs
a negation-like gate. -/
theorem rule30_not_monotone : ¬ (∀ L L' C R : Bool, L ≤ L' → rule30 L C R ≤ rule30 L' C R) := by
  intro h
  have := h false true true false (by decide)
  revert this; decide

/-! ## Tools: closed forms and invariants for the impulse row -/

/-- If `F` starts at `x` and satisfies the update equation of wheel `r`, it *is* the evolution. -/
theorem ecaEvolve_eq_closed {r : ℕ} {x : Config} (F : ℕ → ℤ → Bool) (h0 : ∀ c, x c = F 0 c)
    (hs : ∀ (n : ℕ) (c : ℤ), ecaRule r (F n (c - 1)) (F n c) (F n (c + 1)) = F (n + 1) c) :
    ∀ n c, ecaEvolve r x n c = F n c := by
  intro n
  induction n with
  | zero => exact h0
  | succ n ih => intro c; rw [ecaEvolve_succ, ih, ih, ih, hs]

/-- A column that agrees from some time on with an eventually periodic sequence is eventually
periodic. -/
theorem eventuallyPeriodic_of_eventually_eq {a b : ℕ → Bool} (hb : EventuallyPeriodic b) (M : ℕ)
    (h : ∀ n ≥ M, a n = b n) : EventuallyPeriodic a := by
  obtain ⟨p, hp, N, hN⟩ := hb
  exact ⟨p, hp, max M N, fun n hn => by
    rw [h n (by omega), h (n + p) (by omega), hN n (by omega)]⟩

/-- Eventually constant sequences are eventually periodic. -/
theorem eventuallyPeriodic_of_eventually_const {a : ℕ → Bool} (b : Bool) (M : ℕ)
    (h : ∀ n ≥ M, a n = b) : EventuallyPeriodic a :=
  ⟨1, one_pos, M, fun n hn => by rw [h n hn, h (n + 1) (by omega)]⟩

/-- Sequences that eventually depend only on the parity of the time are eventually periodic. -/
theorem eventuallyPeriodic_of_eventually_parity {a : ℕ → Bool} (b : Bool) (M : ℕ)
    (h : ∀ n ≥ M, a n = (decide (n % 2 = 0) == b)) : EventuallyPeriodic a :=
  ⟨2, two_pos, M, fun n hn => by
    rw [h n hn, h (n + 2) (by omega), show (n + 2) % 2 = n % 2 by omega]⟩

/-! ## Closed forms on the impulse row -/

theorem ecaRule_1_formula (L C R : Bool) : ecaRule 1 L C R = (!L && !C && !R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 1 on the impulse row. -/
theorem ecaEvolve_1_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 1 seed n c = decide ((n % 2 = 0 ∧ c = 0) ∨ (n % 2 = 1 ∧ (c < -1 ∨ 1 < c))) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide ((n % 2 = 0 ∧ c = 0) ∨ (n % 2 = 1 ∧ (c < -1 ∨ 1 < c))))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_1_formula, ← Bool.decide_and, ← decide_not]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_14_formula (L C R : Bool) : ecaRule 14 L C R = (!L && (C || R)) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 14 on the impulse row. -/
theorem ecaEvolve_14_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 14 seed n c = decide ((n = 0 ∧ c = 0) ∨ (1 ≤ n ∧ (c = -n ∨ c = -n + 1))) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide ((n = 0 ∧ c = 0) ∨ (1 ≤ n ∧ (c = -n ∨ c = -n + 1))))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_14_formula, ← Bool.decide_or, ← Bool.decide_and, ← decide_not]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_15_formula (L C R : Bool) : ecaRule 15 L C R = (!L) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 15 on the impulse row. -/
theorem ecaEvolve_15_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 15 seed n c = decide ((n % 2 = 0 ∧ c = n) ∨ (n % 2 = 1 ∧ c ≠ n)) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide ((n % 2 = 0 ∧ c = n) ∨ (n % 2 = 1 ∧ c ≠ n)))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_15_formula, ← decide_not]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_16_formula (L C R : Bool) : ecaRule 16 L C R = (L && !C && !R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 16 on the impulse row. -/
theorem ecaEvolve_16_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 16 seed n c = decide (c = n) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide (c = n))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_16_formula, ← Bool.decide_and, ← decide_not]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_17_formula (L C R : Bool) : ecaRule 17 L C R = (!C && !R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 17 on the impulse row. -/
theorem ecaEvolve_17_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 17 seed n c = decide ((n % 2 = 0 ∧ 2 * c = -n) ∨ (n % 2 = 1 ∧ ¬ (2 * c = -n - 1 ∨ 2 * c = -n + 1))) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide ((n % 2 = 0 ∧ 2 * c = -n) ∨ (n % 2 = 1 ∧ ¬ (2 * c = -n - 1 ∨ 2 * c = -n + 1))))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_17_formula, ← Bool.decide_and, ← decide_not]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_31_formula (L C R : Bool) : ecaRule 31 L C R = (!L || !(C || R)) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 31 on the impulse row. -/
theorem ecaEvolve_31_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 31 seed n c = decide ((n = 0 ∧ c = 0) ∨ n % 2 = 1) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide ((n = 0 ∧ c = 0) ∨ n % 2 = 1))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_31_formula, ← Bool.decide_or, ← decide_not]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_120_formula (L C R : Bool) : ecaRule 120 L C R = ((L && !(C && R)) || (!L && (C && R))) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 120 on the impulse row. -/
theorem ecaEvolve_120_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 120 seed n c = decide (c = n) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide (c = n))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_120_formula, ← Bool.decide_or, ← Bool.decide_and, ← decide_not]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_180_formula (L C R : Bool) : ecaRule 180 L C R = ((L && !(C && !R)) || (!L && (C && !R))) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 180 on the impulse row. -/
theorem ecaEvolve_180_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 180 seed n c = decide ((n % 2 = 0 ∧ c = n) ∨ (n % 2 = 1 ∧ (c = n - 1 ∨ c = n))) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide ((n % 2 = 0 ∧ c = n) ∨ (n % 2 = 1 ∧ (c = n - 1 ∨ c = n))))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_180_formula, ← Bool.decide_or, ← Bool.decide_and, ← decide_not]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_224_formula (L C R : Bool) : ecaRule 224 L C R = (L && (C || R)) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 224 on the impulse row. -/
theorem ecaEvolve_224_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 224 seed n c = decide (n = 0 ∧ c = 0) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide (n = 0 ∧ c = 0))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_224_formula, ← Bool.decide_or, ← Bool.decide_and]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_238_formula (L C R : Bool) : ecaRule 238 L C R = (C || R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 238 on the impulse row. -/
theorem ecaEvolve_238_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 238 seed n c = decide (-n ≤ c ∧ c ≤ 0) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide (-n ≤ c ∧ c ≤ 0))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_238_formula, ← Bool.decide_or]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_239_formula (L C R : Bool) : ecaRule 239 L C R = (!L || C || R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 239 on the impulse row. -/
theorem ecaEvolve_239_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 239 seed n c = decide ((n = 0 ∧ c = 0) ∨ (n = 1 ∧ c ≠ 1) ∨ 2 ≤ n) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide ((n = 0 ∧ c = 0) ∨ (n = 1 ∧ c ≠ 1) ∨ 2 ≤ n))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_239_formula, ← Bool.decide_or, ← decide_not]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_240_formula (L C R : Bool) : ecaRule 240 L C R = (L) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 240 on the impulse row. -/
theorem ecaEvolve_240_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 240 seed n c = decide (c = n) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide (c = n))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_240_formula]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_241_formula (L C R : Bool) : ecaRule 241 L C R = (L || !(C || R)) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 241 on the impulse row. -/
theorem ecaEvolve_241_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 241 seed n c = decide ((n = 0 ∧ c = 0) ∨ (1 ≤ n ∧ c ≠ n - 2 ∧ c ≠ n - 1)) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide ((n = 0 ∧ c = 0) ∨ (1 ≤ n ∧ c ≠ n - 2 ∧ c ≠ n - 1)))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_241_formula, ← Bool.decide_or, ← decide_not]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

theorem ecaRule_254_formula (L C R : Bool) : ecaRule 254 L C R = (L || C || R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Closed form of wheel 254 on the impulse row. -/
theorem ecaEvolve_254_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 254 seed n c = decide (-n ≤ c ∧ c ≤ n) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (c : ℤ) => decide (-n ≤ c ∧ c ≤ n))
    (fun c => decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩) ?_ n c
  intro n c
  simp only [ecaRule_254_formula, ← Bool.decide_or]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩

/-! ## Wheels settled by a one-sided invariant -/

theorem ecaRule_60_formula (L C R : Bool) : ecaRule 60 L C R = ((L && !C) || (!L && C)) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Wheel 60 (`L xor C`) on the impulse row: the left half stays white and the centre stays
black. -/
theorem ecaEvolve_60_seed (n : ℕ) :
    (∀ c < 0, ecaEvolve 60 seed n c = false) ∧ ecaEvolve 60 seed n 0 = true := by
  induction n with
  | zero => exact ⟨fun c hc => decide_eq_false (by omega), rfl⟩
  | succ n ih =>
    refine ⟨fun c hc => ?_, ?_⟩
    · rw [ecaEvolve_succ, ecaRule_60_formula, ih.1 _ (by omega), ih.1 _ hc]; rfl
    · rw [ecaEvolve_succ, ecaRule_60_formula, ih.1 _ (by omega), ih.2]; rfl

theorem ecaRule_195_formula (L C R : Bool) : ecaRule 195 L C R = ((L && C) || (!L && !C)) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Wheel 195 (`L xor not C`) on the impulse row: from time 1 on, the left half is black and the
centre is white. -/
theorem ecaEvolve_195_seed (n : ℕ) (hn : 1 ≤ n) :
    (∀ c < 0, ecaEvolve 195 seed n c = true) ∧ ecaEvolve 195 seed n 0 = false := by
  induction n with
  | zero => omega
  | succ n ih =>
    rcases Nat.eq_zero_or_pos n with rfl | hn'
    · refine ⟨fun c hc => ?_, rfl⟩
      rw [ecaEvolve_succ, ecaRule_195_formula]
      simp only [ecaEvolve_zero, seed]
      rw [decide_eq_false (by omega : ¬ (c - 1 = 0)), decide_eq_false (by omega : ¬ (c = 0))]; rfl
    · refine ⟨fun c hc => ?_, ?_⟩
      · rw [ecaEvolve_succ, ecaRule_195_formula, (ih hn').1 _ (by omega), (ih hn').1 _ hc]; rfl
      · rw [ecaEvolve_succ, ecaRule_195_formula, zero_sub, (ih hn').1 _ (by omega), (ih hn').2]
        rfl

theorem ecaRule_225_formula (L C R : Bool) :
    ecaRule 225 L C R = ((L && (C || R)) || (!L && !(C || R))) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Wheel 225 on the all-white row: all black from time 1 on. -/
theorem ecaEvolve_225_white (n : ℕ) (c : ℤ) :
    ecaEvolve 225 (fun _ => false) n c = decide (1 ≤ n) := by
  refine ecaEvolve_eq_closed (fun (n : ℕ) (_ : ℤ) => decide (1 ≤ n))
    (fun c => rfl) ?_ n c
  intro n c
  show ecaRule 225 (decide (1 ≤ n)) (decide (1 ≤ n)) (decide (1 ≤ n)) = decide (1 ≤ n + 1)
  cases n with
  | zero => rfl
  | succ n => simp [ecaRule_225_formula]

/-- Wheel 225 at time 5: every cell at or left of the centre is black. -/
theorem ecaEvolve_225_five (c : ℤ) (hc : c ≤ 0) : ecaEvolve 225 seed 5 c = true := by
  by_cases hfar : c ≤ -6
  · rw [ecaEvolve_congr 225 seed (fun _ => false) 5 c
      (fun j h1 h2 => decide_eq_false (by push_cast at *; omega)), ecaEvolve_225_white]
    rfl
  · obtain ⟨k, hk⟩ : ∃ k : ℕ, c = -(k : ℤ) := ⟨c.natAbs, by omega⟩
    have hk6 : k < 6 := by omega
    subst hk
    interval_cases k <;> decide

/-- **Wheel 225 (`xnor(L, C or R)`) on the impulse row: from time 5 on, every cell at or left of
the centre is black.**  A black pair `L = C = 1` gives `xnor(1, 1) = 1`, so the black left half
can never shrink. -/
theorem ecaEvolve_225_seed (n : ℕ) (hn : 5 ≤ n) (c : ℤ) (hc : c ≤ 0) :
    ecaEvolve 225 seed n c = true := by
  induction n generalizing c with
  | zero => omega
  | succ n ih =>
    rcases Nat.lt_or_ge n 5 with h | h
    · rw [show n + 1 = 5 by omega]; exact ecaEvolve_225_five c hc
    · rw [ecaEvolve_succ, ecaRule_225_formula, ih h _ (by omega), ih h _ hc]; rfl

/-- The centre column of wheel 225 is eventually all black. -/
theorem centre225_eventually_black : ∀ n ≥ 5, ecaColumn 225 seed 0 n = true :=
  fun n hn => ecaEvolve_225_seed n hn 0 le_rfl

theorem ecaRule_210_formula (L C R : Bool) :
    ecaRule 210 L C R = ((L && !(!C && R)) || (!L && (!C && R))) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- Wheel 210 (`L xor (not C and R)`) on the impulse row coincides with wheel 90, and both vanish
off the checkerboard `c + n` even. -/
theorem ecaEvolve_210_seed (n : ℕ) (c : ℤ) :
    ecaEvolve 210 seed n c = ecaEvolve 90 seed n c ∧
      ((c + n) % 2 = 1 → ecaEvolve 90 seed n c = false) := by
  induction n generalizing c with
  | zero => exact ⟨rfl, fun h => decide_eq_false (by omega)⟩
  | succ n ih =>
    have h1 := ih (c - 1)
    have h2 := ih c
    have h3 := ih (c + 1)
    rw [ecaEvolve_succ, ecaEvolve_succ, ecaRule_210_formula, ecaRule_ninety, h1.1, h2.1, h3.1]
    refine ⟨?_, fun hpar => ?_⟩
    · rcases Int.emod_two_eq_zero_or_one (c + n) with hp | hp
      · rw [h1.2 (by omega), h3.2 (by omega)]
        cases ecaEvolve 90 seed n c <;> rfl
      · rw [h2.2 (by omega)]
        cases ecaEvolve 90 seed n (c - 1) <;> cases ecaEvolve 90 seed n (c + 1) <;> rfl
    · push_cast at hpar
      rw [h1.2 (by omega), h3.2 (by omega)]; rfl

/-! ## Mirror-symmetric wheels: the centre sees two equal neighbours -/

theorem seed_symm (j : ℤ) : seed (-j) = seed j := by simp [seed]

theorem ecaRule_150_formula (L C R : Bool) : ecaRule 150 L C R = xor (xor L C) R := by
  cases L <;> cases C <;> cases R <;> rfl

theorem ecaRule_105_formula (L C R : Bool) : ecaRule 105 L C R = !(xor (xor L C) R) := by
  cases L <;> cases C <;> cases R <;> rfl

theorem ecaRule_165_formula (L C R : Bool) : ecaRule 165 L C R = !(xor L R) := by
  cases L <;> cases C <;> cases R <;> rfl

/-- The centre of a mirror-symmetric wheel on the impulse row is updated from `(x 1, x 0, x 1)`. -/
theorem centre_symm_step {r : ℕ} (hr : ∀ L C R, ecaRule r L C R = ecaRule r R C L) (n : ℕ) :
    ecaEvolve r seed (n + 1) 0 =
      ecaRule r (ecaEvolve r seed n 1) (ecaEvolve r seed n 0) (ecaEvolve r seed n 1) := by
  rw [ecaEvolve_succ, zero_sub, ecaEvolve_symmetric hr seed seed_symm n 1, zero_add]

/-- Wheel 150 (`L xor C xor R`): the centre column is all black. -/
theorem centre150 (n : ℕ) : ecaColumn 150 seed 0 n = true := by
  induction n with
  | zero => rfl
  | succ n ih =>
    simp only [ecaColumn] at ih ⊢
    rw [centre_symm_step (fun L C R => by
      rw [ecaRule_150_formula, ecaRule_150_formula]; cases L <;> cases C <;> cases R <;> rfl),
      ecaRule_150_formula, ih]
    cases ecaEvolve 150 seed n 1 <;> rfl

/-- Wheel 105 (`not (L xor C xor R)`): the centre column alternates. -/
theorem centre105 (n : ℕ) : ecaColumn 105 seed 0 n = (decide (n % 2 = 0) == true) := by
  induction n with
  | zero => rfl
  | succ n ih =>
    simp only [ecaColumn] at ih ⊢
    rw [centre_symm_step (fun L C R => by
      rw [ecaRule_105_formula, ecaRule_105_formula]; cases L <;> cases C <;> cases R <;> rfl),
      ecaRule_105_formula, ih]
    rcases Nat.mod_two_eq_zero_or_one n with h | h
    · rw [decide_eq_true h, decide_eq_false (by omega)]
      cases ecaEvolve 105 seed n 1 <;> rfl
    · rw [decide_eq_false (by omega), decide_eq_true (by omega)]
      cases ecaEvolve 105 seed n 1 <;> rfl

/-- Wheel 165 (`not (L xor R)`): the centre column is black from time 1 on. -/
theorem centre165 (n : ℕ) : ecaColumn 165 seed 0 (n + 1) = true := by
  simp only [ecaColumn]
  rw [centre_symm_step (fun L C R => by
    rw [ecaRule_165_formula, ecaRule_165_formula]; cases L <;> cases C <;> cases R <;> rfl),
    ecaRule_165_formula]
  cases ecaEvolve 165 seed n 1 <;> rfl

/-- Wheel 255: everything black from time 1 on. -/
theorem centre255 (n : ℕ) : ecaColumn 255 seed 0 (n + 1) = true := by
  simp only [ecaColumn, ecaEvolve_succ]
  cases ecaEvolve 255 seed n (0 - 1) <;> cases ecaEvolve 255 seed n 0 <;>
    cases ecaEvolve 255 seed n (0 + 1) <;> rfl

/-! ## Centre columns of the alternative wheels -/

/-- Shorthand: the centre column of wheel `r` on the impulse row. -/
abbrev centreOf (r : ℕ) : ℕ → Bool := ecaColumn r seed 0

/-! The closed-form wheels: their centre columns repeat with period 2 from time 3 on. -/

theorem periodic_1 : EventuallyPeriodic (centreOf 1) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_1_seed, Nat.add_mod_right]⟩

theorem periodic_14 : EventuallyPeriodic (centreOf 14) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_14_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_15 : EventuallyPeriodic (centreOf 15) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_15_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_16 : EventuallyPeriodic (centreOf 16) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_16_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_17 : EventuallyPeriodic (centreOf 17) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_17_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_31 : EventuallyPeriodic (centreOf 31) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_31_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_120 : EventuallyPeriodic (centreOf 120) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_120_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_180 : EventuallyPeriodic (centreOf 180) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_180_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_224 : EventuallyPeriodic (centreOf 224) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_224_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_238 : EventuallyPeriodic (centreOf 238) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_238_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_239 : EventuallyPeriodic (centreOf 239) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_239_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_240 : EventuallyPeriodic (centreOf 240) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_240_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_241 : EventuallyPeriodic (centreOf 241) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_241_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_254 : EventuallyPeriodic (centreOf 254) := ⟨2, two_pos, 3, fun n hn => by
  simp only [centreOf, ecaColumn, ecaEvolve_254_seed]
  exact decide_eq_decide.mpr ⟨fun h => by omega, fun h => by omega⟩⟩

theorem periodic_0 : EventuallyPeriodic (centreOf 0) := not_not.mp (not_wheelProblem1_zero seed 0)

theorem periodic_60 : EventuallyPeriodic (centreOf 60) :=
  eventuallyPeriodic_of_eventually_const true 0 fun n _ => (ecaEvolve_60_seed n).2

theorem periodic_90 : EventuallyPeriodic (centreOf 90) := not_not.mp not_wheelProblem1_ninety

theorem periodic_105 : EventuallyPeriodic (centreOf 105) :=
  eventuallyPeriodic_of_eventually_parity true 0 fun n _ => centre105 n

theorem periodic_150 : EventuallyPeriodic (centreOf 150) :=
  eventuallyPeriodic_of_eventually_const true 0 fun n _ => centre150 n

theorem periodic_165 : EventuallyPeriodic (centreOf 165) :=
  eventuallyPeriodic_of_eventually_const true 1 fun n hn => by
    obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
    exact centre165 m

theorem periodic_195 : EventuallyPeriodic (centreOf 195) :=
  eventuallyPeriodic_of_eventually_const false 1 fun n hn => (ecaEvolve_195_seed n hn).2

theorem periodic_210 : EventuallyPeriodic (centreOf 210) :=
  eventuallyPeriodic_of_eventually_const false 1 fun n hn => by
    show ecaEvolve 210 seed n 0 = false
    rw [(ecaEvolve_210_seed n 0).1]
    have := ecaColumn_ninety_centre n
    simp only [ecaColumn] at this
    rw [this]; exact decide_eq_false (by omega)

theorem periodic_225 : EventuallyPeriodic (centreOf 225) :=
  eventuallyPeriodic_of_eventually_const true 5 centre225_eventually_black

theorem periodic_255 : EventuallyPeriodic (centreOf 255) :=
  eventuallyPeriodic_of_eventually_const true 1 fun n hn => by
    obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
    exact centre255 m

/-! ## Gates -/

/-- A two-input Boolean gate. -/
abbrev BinGate := Bool → Bool → Bool

/-- The gate with outputs `b0, b1, b2, b3` on the inputs `00, 01, 10, 11`. -/
def gateOf (b0 b1 b2 b3 : Bool) : BinGate :=
  fun a b => if a then (if b then b3 else b2) else (if b then b1 else b0)

theorem gate_eq_gateOf (g : BinGate) :
    g = gateOf (g false false) (g false true) (g true false) (g true true) := by
  funext a b; cases a <;> cases b <;> rfl

/-- **Replace the XOR.** The wheel `g(L, C or R)`. -/
def outerRule (g : BinGate) : ℕ := tableNum (fun L C R => g L (C || R))

/-- **Replace the OR.** The wheel `L xor h(C, R)`. -/
def innerRule (h : BinGate) : ℕ := tableNum (fun L C R => xor L (h C R))

/-- A gate is of *OR type* if exactly three of its four inputs give `true` (`or`, `nand`, and the
two implications). -/
def IsOrType (h : BinGate) : Prop :=
  ((Finset.univ : Finset (Bool × Bool)).filter (fun p => h p.1 p.2 = true)).card = 3

instance (h : BinGate) : Decidable (IsOrType h) := by unfold IsOrType; infer_instance

theorem outerRule_xor : outerRule (fun a b => xor a b) = 30 := by decide

theorem innerRule_or : innerRule (fun a b => a || b) = 30 := by decide

/-- The sixteen outer alternatives: every gate other than XOR gives one of fifteen wheels. -/
theorem outerRule_mem (g : BinGate) (hg : g ≠ fun a b => xor a b) :
    outerRule g ∈ ({0, 1, 14, 15, 16, 17, 31, 224, 225, 238, 239, 240, 241, 254, 255} :
      Finset ℕ) := by
  rw [gate_eq_gateOf g] at hg ⊢
  generalize g false false = b0 at hg ⊢
  generalize g false true = b1 at hg ⊢
  generalize g true false = b2 at hg ⊢
  generalize g true true = b3 at hg ⊢
  revert b0 b1 b2 b3
  decide

/-- The sixteen inner alternatives that are not of OR type. -/
theorem innerRule_mem (h : BinGate) (hh : ¬ IsOrType h) :
    innerRule h ∈ ({240, 225, 210, 195, 180, 165, 150, 120, 105, 90, 60, 15} : Finset ℕ) := by
  rw [gate_eq_gateOf h] at hh ⊢
  generalize h false false = b0 at hh ⊢
  generalize h false true = b1 at hh ⊢
  generalize h true false = b2 at hh ⊢
  generalize h true true = b3 at hh ⊢
  revert b0 b1 b2 b3
  decide

/-- The four OR-type gates give the wheels 30, 45, 75 and 135. -/
theorem innerRule_orType (h : BinGate) :
    IsOrType h ↔ innerRule h ∈ ({30, 45, 75, 135} : Finset ℕ) := by
  rw [gate_eq_gateOf h]
  generalize h false false = b0
  generalize h false true = b1
  generalize h true false = b2
  generalize h true true = b3
  revert b0 b1 b2 b3
  decide

/-- **Only XOR survives.** For every two-input gate `g` other than XOR, the centre column of
`g(L, C or R)` from a single black cell is eventually periodic.  Among the sixteen ways to combine
`L` with `C or R`, Rule 30 is the only one whose Problem 1 is not settled. -/
theorem outer_alternative_periodic (g : BinGate) (hg : g ≠ fun a b => xor a b) :
    EventuallyPeriodic (ecaColumn (outerRule g) seed 0) := by
  have h := outerRule_mem g hg
  simp only [Finset.mem_insert, Finset.mem_singleton] at h
  rcases h with h | h | h | h | h | h | h | h | h | h | h | h | h | h | h <;> rw [h]
  exacts [periodic_0, periodic_1, periodic_14, periodic_15, periodic_16, periodic_17, periodic_31,
    periodic_224, periodic_225, periodic_238, periodic_239, periodic_240, periodic_241,
    periodic_254, periodic_255]

/-- **Only OR-type gates survive.** For every gate `h` that is not of OR type, the centre column
of `L xor h(C, R)` from a single black cell is eventually periodic. -/
theorem inner_alternative_periodic (h : BinGate) (hh : ¬ IsOrType h) :
    EventuallyPeriodic (ecaColumn (innerRule h) seed 0) := by
  have h' := innerRule_mem h hh
  simp only [Finset.mem_insert, Finset.mem_singleton] at h'
  rcases h' with h' | h' | h' | h' | h' | h' | h' | h' | h' | h' | h' | h' <;> rw [h']
  exacts [periodic_240, periodic_225, periodic_210, periodic_195, periodic_180, periodic_165,
    periodic_150, periodic_120, periodic_105, periodic_90, periodic_60, periodic_15]

/-! ## Which alternatives keep left-permutivity -/

/-- `g(L, C or R)` is left-permutive exactly for `g = xor` (wheel 30), `g = xnor` (wheel 225) and
the two gates that ignore `C or R`: `g = L` (wheel 240) and `g = not L` (wheel 15). -/
theorem outerRule_leftPermutive_iff (g : BinGate) :
    IsLeftPermutive (outerRule g) ↔ (g = fun a b => xor a b) ∨ (g = fun a b => !(xor a b)) ∨
      (g = fun a _ => a) ∨ (g = fun a _ => !a) := by
  rw [gate_eq_gateOf g]
  generalize g false false = b0
  generalize g false true = b1
  generalize g true false = b2
  generalize g true true = b3
  revert b0 b1 b2 b3
  decide

/-- Every inner alternative is left-permutive. -/
theorem innerRule_leftPermutive (h : BinGate) : IsLeftPermutive (innerRule h) := by
  intro C R
  simp only [innerRule, ecaRule_tableNum]
  cases h C R <;> rfl

/-- **The left-permutive wheels are exactly the inner alternatives** `L xor h(C, R)`. -/
theorem leftPermutive_iff_innerRule (r : ℕ) (hr : r < 256) :
    IsLeftPermutive r ↔ ∃ h : BinGate, innerRule h = r := by
  constructor
  · intro hp
    refine ⟨fun C R => ecaRule r false C R, ?_⟩
    have : (fun L C R => xor L (ecaRule r false C R)) = ecaRule r := by
      funext L C R
      cases L
      · simp
      · rw [hp C R]; simp
    simp only [innerRule, this, tableNum_ecaRule r hr]
  · rintro ⟨h, rfl⟩; exact innerRule_leftPermutive h

/-- Wheel 225 is left-permutive, yet its centre column is eventually black: left-permutivity
alone does not make a column irregular. -/
theorem leftPermutive_not_sufficient :
    IsLeftPermutive 225 ∧ EventuallyPeriodic (ecaColumn 225 seed 0) :=
  ⟨by decide, periodic_225⟩

end GLM.Rule30
