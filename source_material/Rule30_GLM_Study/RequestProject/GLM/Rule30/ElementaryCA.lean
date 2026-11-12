module

public import RequestProject.GLM.Rule30.Prizes
public import RequestProject.GLM.Rule30.MachineModel

/-!
# The elementary cellular-automaton family ("the Wheel")

Round 9.  The three questions are usually posed for "Rule 30", a name that carries no
information by itself.  Here the whole family of 256 elementary cellular automata is built,
and the questions are stated **for any wheel number `r`**, so the rule is carried inside the
question as data:

* `ecaRule r L C R` : the output for the neighbourhood `(L, C, R)` is bit `4L + 2C + R` of `r`
  (Wolfram's numbering; `r = 30 = 0b00011110` gives `L xor (C or R)`, `ecaRule_30`).
* `ecaEvolve r x n c` : the cell at position `c` after `n` synchronous steps from row `x`.
* `ecaColumn r x c n` : column `c` of the space-time diagram of `x`.
* `WheelProblem1 r x c`, `WheelProblem2 r x c`, `WheelProblem3 r` : the three questions for
  wheel `r`.  `problem1_iff_wheel`, `problem2_iff_wheel`, `problem3_iff_wheel` : for
  `r = 30`, the impulse row `seed` and column `0` they **are** the prize problems.
  `problem1_selfContained`, `problem2_selfContained` : the prize problems written with nothing
  but the number `30`, the impulse row `c ↦ [c = 0]` and `ecaEvolve`.

## Symmetries of the family

* `tableNum f` : the wheel number of a local rule `f`; `ecaRule_tableNum`, `tableNum_ecaRule`.
* `mirrorNum r` (reflect space `c ↦ -c`) and `complementNum r` (swap colours).
  `mirrorNum 30 = 86`, `complementNum 30 = 135`, `mirrorNum (complementNum 30) = 149`.
* `ecaEvolve_mirror`, `ecaEvolve_complement` : how evolution transforms.
* `wheelProblem1_mirror_iff`, `wheelProblem2_mirror_iff` : each question has the same answer for
  `r` and its mirror image (with the mirrored row and column).  In particular for 30 and 86 on
  the impulse row and centre column (`problem1_iff_eightySix`, `problem2_iff_eightySix`).
* `wheelProblem1_complement_iff`, `wheelProblem2_complement_iff` : the same for `r` and its colour
  complement, with the complemented row.  (For 135 the complemented impulse is "all black except
  one white cell": a different initial condition.)
* `card_equivalence_classes` : the 256 wheels fall into exactly 88 classes under these
  symmetries; `card_leftPermutive` : 16 wheels are left-permutive (30 is one of them).

## Family-level theorems

* `ecaEvolve_flip_left_edge` : **cone separation holds for every left-permutive wheel**: flipping
  the left edge of the light cone of `(n, c)` flips that cell.  (`ConeSeparation.lean` proved this
  for 30.)  So cone separation is a family property shared by 16 wheels, which is one more reason
  (error E2) it cannot by itself decide the questions for 30.
* Wheels where the questions are **settled**:
  - `ecaColumn_ninety_centre` : wheel 90 (`L xor R`) on the impulse row has centre column
    `1, 0, 0, 0, …`.  So `not_wheelProblem1_ninety` and `not_wheelProblem2_ninety` : both
    questions have answer *no* for 90, although 90 is also left-permutive (and right-permutive).
  - `not_wheelProblem1_zero`, `not_wheelProblem1_identity` : wheels 0 and 204.
  The proof for 90 uses its mirror symmetry (`ecaEvolve_symmetric`): a symmetric wheel keeps a
  symmetric row symmetric.  Wheel 30 is not mirror-symmetric (`thirty_ne_mirror`), and 30's
  centre column is not covered by any argument of this kind.
-/

@[expose] public section

namespace GLM.Rule30

open Finset

/-! ## 1. The family -/

/-- The local rule with wheel number `r`: bit `4L + 2C + R` of `r`. -/
def ecaRule (r : ℕ) (L C R : Bool) : Bool :=
  Nat.testBit r (4 * L.toNat + 2 * C.toNat + R.toNat)

/-- Wheel 30 is Rule 30. -/
theorem ecaRule_30 : ecaRule 30 = rule30 := by
  funext L C R; cases L <;> cases C <;> cases R <;> rfl

/-- `n` synchronous steps of wheel `r` from row `x`. -/
def ecaEvolve (r : ℕ) (x : Config) : ℕ → Config
  | 0 => x
  | n + 1 => fun c => ecaRule r (ecaEvolve r x n (c - 1)) (ecaEvolve r x n c)
      (ecaEvolve r x n (c + 1))

@[simp] theorem ecaEvolve_zero (r : ℕ) (x : Config) : ecaEvolve r x 0 = x := rfl

theorem ecaEvolve_succ (r : ℕ) (x : Config) (n : ℕ) (c : ℤ) :
    ecaEvolve r x (n + 1) c = ecaRule r (ecaEvolve r x n (c - 1)) (ecaEvolve r x n c)
      (ecaEvolve r x n (c + 1)) := rfl

/-- Wheel 30 evolves exactly as Rule 30. -/
theorem ecaEvolve_thirty : ecaEvolve 30 = evolve := by
  funext x n
  induction n with
  | zero => rfl
  | succ n ih =>
    funext c
    rw [ecaEvolve_succ, ih, ecaRule_30, evolve_succ]

/-- Column `c` of the space-time diagram of wheel `r` from row `x`. -/
def ecaColumn (r : ℕ) (x : Config) (c : ℤ) (n : ℕ) : Bool := ecaEvolve r x n c

theorem ecaColumn_thirty_seed : ecaColumn 30 seed 0 = centerCol := by
  funext n; simp [ecaColumn, ecaEvolve_thirty, centerCol]

/-- Light-cone locality, for every wheel. -/
theorem ecaEvolve_congr (r : ℕ) (x y : Config) (n : ℕ) (c : ℤ)
    (h : ∀ j, c - n ≤ j → j ≤ c + n → x j = y j) : ecaEvolve r x n c = ecaEvolve r y n c := by
  induction n generalizing c with
  | zero => exact h c (by simp) (by simp)
  | succ n ih =>
    rw [ecaEvolve_succ, ecaEvolve_succ,
      ih (c - 1) (fun j h1 h2 => h j (by push_cast at *; omega) (by push_cast at *; omega)),
      ih c (fun j h1 h2 => h j (by push_cast at *; omega) (by push_cast at *; omega)),
      ih (c + 1) (fun j h1 h2 => h j (by push_cast at *; omega) (by push_cast at *; omega))]

/-! ## 2. The three questions, for any wheel -/

/-- **Question 1 for wheel `r`, row `x`, column `c`:** the column is not eventually periodic. -/
def WheelProblem1 (r : ℕ) (x : Config) (c : ℤ) : Prop := ¬ EventuallyPeriodic (ecaColumn r x c)

/-- **Question 2 for wheel `r`, row `x`, column `c`:** the black frequency tends to `1/2`. -/
def WheelProblem2 (r : ℕ) (x : Config) (c : ℤ) : Prop := HasFrequencyHalf (ecaColumn r x c)

open Asymptotics Filter in
/-- **Question 3 for wheel `r`** (impulse row, centre column), in the same Turing-machine model as
`Problem3`: no machine computes `n ↦ a_r(n)` in time `o(n)` (input `n` in binary). -/
def WheelProblem3 (r : ℕ) : Prop :=
  ∀ M : Turing.TM2ComputableInTime Computability.finEncodingNatBool
      Computability.finEncodingBoolBool (ecaColumn r seed 0),
    ¬ (fun n : ℕ => (M.time (Computability.finEncodingNatBool.encode n).length : ℝ)) =o[atTop]
      (fun n : ℕ => (n : ℝ))

/-- For wheel 30, the impulse row and column 0, question 1 is Problem 1. -/
theorem problem1_iff_wheel : Problem1 ↔ WheelProblem1 30 seed 0 := by
  rw [WheelProblem1, ecaColumn_thirty_seed]; rfl

/-- For wheel 30, the impulse row and column 0, question 2 is Problem 2. -/
theorem problem2_iff_wheel : Problem2 ↔ WheelProblem2 30 seed 0 := by
  rw [WheelProblem2, ecaColumn_thirty_seed]; rfl

/-- **Problem 1 with everything carried inside the statement**: only the bits of the number `30`,
the impulse row `c ↦ [c = 0]` and synchronous evolution appear. -/
theorem problem1_selfContained : Problem1 ↔
    ¬ ∃ p > 0, ∃ N, ∀ n ≥ N, ecaEvolve 30 (fun c => decide (c = 0)) (n + p) 0 =
      ecaEvolve 30 (fun c => decide (c = 0)) n 0 := by
  rw [problem1_iff_wheel]; rfl

/-- **Problem 2 with everything carried inside the statement.** -/
theorem problem2_selfContained : Problem2 ↔
    Filter.Tendsto (fun n : ℕ => ((((Finset.range n).filter
      (fun i => ecaEvolve 30 (fun c => decide (c = 0)) i 0 = true)).card : ℕ) : ℝ) / n)
      Filter.atTop (nhds (1 / 2)) := by
  rw [problem2_iff_wheel]; rfl

/-- For wheel 30, question 3 is Problem 3. -/
theorem problem3_iff_wheel : Problem3 ↔ WheelProblem3 30 := by
  rw [WheelProblem3, ecaColumn_thirty_seed]; rfl

/-! ## 3. Wheel numbers of local rules -/

/-- The wheel number of a local rule. -/
def tableNum (f : Bool → Bool → Bool → Bool) : ℕ :=
  (f false false false).toNat + 2 * (f false false true).toNat +
  4 * (f false true false).toNat + 8 * (f false true true).toNat +
  16 * (f true false false).toNat + 32 * (f true false true).toNat +
  64 * (f true true false).toNat + 128 * (f true true true).toNat

theorem testBit_table (b0 b1 b2 b3 b4 b5 b6 b7 : Bool) :
    let n := b0.toNat + 2 * b1.toNat + 4 * b2.toNat + 8 * b3.toNat + 16 * b4.toNat +
      32 * b5.toNat + 64 * b6.toNat + 128 * b7.toNat
    n.testBit 0 = b0 ∧ n.testBit 1 = b1 ∧ n.testBit 2 = b2 ∧ n.testBit 3 = b3 ∧
      n.testBit 4 = b4 ∧ n.testBit 5 = b5 ∧ n.testBit 6 = b6 ∧ n.testBit 7 = b7 := by
  revert b0 b1 b2 b3 b4 b5 b6 b7; decide

/-- Reading back the local rule from its wheel number. -/
theorem ecaRule_tableNum (f : Bool → Bool → Bool → Bool) : ecaRule (tableNum f) = f := by
  funext L C R
  obtain ⟨h0, h1, h2, h3, h4, h5, h6, h7⟩ := testBit_table (f false false false)
    (f false false true) (f false true false) (f false true true) (f true false false)
    (f true false true) (f true true false) (f true true true)
  cases L <;> cases C <;> cases R <;> simp_all [ecaRule, tableNum]

/-- Every wheel number below `256` is the number of its own local rule. -/
theorem tableNum_ecaRule (r : ℕ) (hr : r < 256) : tableNum (ecaRule r) = r := by
  revert r; decide +kernel

/-- Wheel `r` read in a mirror (`c ↦ -c`). -/
def mirrorNum (r : ℕ) : ℕ := tableNum (fun L C R => ecaRule r R C L)

/-- Wheel `r` with the two colours swapped. -/
def complementNum (r : ℕ) : ℕ := tableNum (fun L C R => !ecaRule r (!L) (!C) (!R))

theorem mirrorNum_thirty : mirrorNum 30 = 86 := by decide
theorem complementNum_thirty : complementNum 30 = 135 := by decide
theorem mirror_complement_thirty : mirrorNum (complementNum 30) = 149 := by decide

/-- Wheel 30 is not its own mirror image. -/
theorem thirty_ne_mirror : mirrorNum 30 ≠ 30 := by decide

theorem ecaRule_mirrorNum (r : ℕ) (L C R : Bool) : ecaRule (mirrorNum r) L C R = ecaRule r R C L := by
  rw [mirrorNum, ecaRule_tableNum]

theorem ecaRule_complementNum (r : ℕ) (L C R : Bool) :
    ecaRule (complementNum r) L C R = !ecaRule r (!L) (!C) (!R) := by
  rw [complementNum, ecaRule_tableNum]

/-- **Mirror symmetry of evolution.** -/
theorem ecaEvolve_mirror (r : ℕ) (x : Config) (n : ℕ) (c : ℤ) :
    ecaEvolve (mirrorNum r) (fun j => x (-j)) n c = ecaEvolve r x n (-c) := by
  induction n generalizing c with
  | zero => rfl
  | succ n ih =>
    rw [ecaEvolve_succ, ecaEvolve_succ, ih, ih, ih, ecaRule_mirrorNum]
    congr 2 <;> ring_nf

/-- **Colour symmetry of evolution.** -/
theorem ecaEvolve_complement (r : ℕ) (x : Config) (n : ℕ) (c : ℤ) :
    ecaEvolve (complementNum r) (fun j => !x j) n c = !ecaEvolve r x n c := by
  induction n generalizing c with
  | zero => rfl
  | succ n ih =>
    rw [ecaEvolve_succ, ecaEvolve_succ, ih, ih, ih, ecaRule_complementNum]
    simp

/-! ## 4. The questions are invariant under the symmetries -/

theorem eventuallyPeriodic_not_iff (a : ℕ → Bool) :
    EventuallyPeriodic (fun n => !a n) ↔ EventuallyPeriodic a := by
  constructor
  · rintro ⟨p, hp, N, h⟩; exact ⟨p, hp, N, fun n hn => by simpa using h n hn⟩
  · rintro ⟨p, hp, N, h⟩; exact ⟨p, hp, N, fun n hn => by simp [h n hn]⟩

theorem ones_not (a : ℕ → Bool) (n : ℕ) : ones (fun i => !a i) n + ones a n = n := by
  induction n with
  | zero => simp [ones]
  | succ n ih =>
    rw [ones_succ, ones_succ]
    cases a n <;> simp <;> omega

theorem wobble_not (a : ℕ → Bool) (n : ℕ) : wobble (fun i => !a i) n = - wobble a n := by
  have := ones_not a n
  simp only [wobble]
  omega

theorem hasFrequencyHalf_not_iff (a : ℕ → Bool) :
    HasFrequencyHalf (fun n => !a n) ↔ HasFrequencyHalf a := by
  rw [hasFrequencyHalf_iff, hasFrequencyHalf_iff]
  have : (fun n => ((wobble (fun i => !a i) n : ℤ) : ℝ) / n) =
      fun n => -(((wobble a n : ℤ) : ℝ) / n) := by
    funext n; rw [wobble_not]; push_cast; ring
  rw [this]
  constructor
  · intro h; simpa using h.neg
  · intro h; simpa using h.neg

/-- Question 1 has the same answer for a wheel and its mirror image. -/
theorem wheelProblem1_mirror_iff (r : ℕ) (x : Config) (c : ℤ) :
    WheelProblem1 (mirrorNum r) (fun j => x (-j)) (-c) ↔ WheelProblem1 r x c := by
  unfold WheelProblem1 ecaColumn
  simp only [ecaEvolve_mirror, neg_neg]

/-- Question 2 has the same answer for a wheel and its mirror image. -/
theorem wheelProblem2_mirror_iff (r : ℕ) (x : Config) (c : ℤ) :
    WheelProblem2 (mirrorNum r) (fun j => x (-j)) (-c) ↔ WheelProblem2 r x c := by
  unfold WheelProblem2 ecaColumn
  simp only [ecaEvolve_mirror, neg_neg]

/-- Question 1 has the same answer for a wheel and its colour complement (complemented row). -/
theorem wheelProblem1_complement_iff (r : ℕ) (x : Config) (c : ℤ) :
    WheelProblem1 (complementNum r) (fun j => !x j) c ↔ WheelProblem1 r x c := by
  unfold WheelProblem1 ecaColumn
  simp only [ecaEvolve_complement]
  rw [eventuallyPeriodic_not_iff (fun n => ecaEvolve r x n c)]

/-- Question 2 has the same answer for a wheel and its colour complement (complemented row). -/
theorem wheelProblem2_complement_iff (r : ℕ) (x : Config) (c : ℤ) :
    WheelProblem2 (complementNum r) (fun j => !x j) c ↔ WheelProblem2 r x c := by
  unfold WheelProblem2 ecaColumn
  simp only [ecaEvolve_complement]
  rw [hasFrequencyHalf_not_iff (fun n => ecaEvolve r x n c)]

theorem seed_mirror : (fun j : ℤ => seed (-j)) = seed := by
  funext j; simp [seed]

/-- **Problem 1 for Rule 30 is Problem 1 for Rule 86** (impulse row, centre column). -/
theorem problem1_iff_eightySix : Problem1 ↔ WheelProblem1 86 seed 0 := by
  rw [problem1_iff_wheel, ← mirrorNum_thirty, ← wheelProblem1_mirror_iff, seed_mirror, neg_zero]

/-- **Problem 2 for Rule 30 is Problem 2 for Rule 86** (impulse row, centre column). -/
theorem problem2_iff_eightySix : Problem2 ↔ WheelProblem2 86 seed 0 := by
  rw [problem2_iff_wheel, ← mirrorNum_thirty, ← wheelProblem2_mirror_iff, seed_mirror, neg_zero]

/-- **Problem 1 for Rule 30 is Problem 1 for Rule 135 on the complemented impulse row.** -/
theorem problem1_iff_oneThirtyFive : Problem1 ↔ WheelProblem1 135 (fun j => !seed j) 0 := by
  rw [problem1_iff_wheel, ← complementNum_thirty, wheelProblem1_complement_iff]

/-- **Problem 2 for Rule 30 is Problem 2 for Rule 135 on the complemented impulse row.** -/
theorem problem2_iff_oneThirtyFive : Problem2 ↔ WheelProblem2 135 (fun j => !seed j) 0 := by
  rw [problem2_iff_wheel, ← complementNum_thirty, wheelProblem2_complement_iff]

/-! ## 5. Census of the family -/

/-- Wheel `r` is left-permutive: flipping `L` always flips the output. -/
def IsLeftPermutive (r : ℕ) : Prop := ∀ C R : Bool, ecaRule r true C R = !ecaRule r false C R

instance (r : ℕ) : Decidable (IsLeftPermutive r) := by
  unfold IsLeftPermutive; infer_instance

theorem leftPermutive_thirty : IsLeftPermutive 30 := by decide

/-- Exactly 16 of the 256 wheels are left-permutive. -/
theorem card_leftPermutive : ((range 256).filter IsLeftPermutive).card = 16 := by decide

/-- The least wheel number in the symmetry class of `r` is `r` itself. -/
def IsClassRep (r : ℕ) : Prop :=
  r ≤ mirrorNum r ∧ r ≤ complementNum r ∧ r ≤ mirrorNum (complementNum r)

instance (r : ℕ) : Decidable (IsClassRep r) := by unfold IsClassRep; infer_instance

/-- The 256 wheels fall into exactly 88 classes under mirror and colour symmetry. -/
theorem card_equivalence_classes : ((range 256).filter IsClassRep).card = 88 := by decide

/-- Wheel 30 is the representative of its class `{30, 86, 135, 149}`. -/
theorem classRep_thirty : IsClassRep 30 := by decide

/-! ## 6. Cone separation for every left-permutive wheel -/

/-- **Cone separation for the whole left-permutive family.** -/
theorem ecaEvolve_flip_left_edge {r : ℕ} (hr : IsLeftPermutive r) (x : Config) (n : ℕ) (c : ℤ) :
    ecaEvolve r (flipAt x (c - n)) n c = !ecaEvolve r x n c := by
  induction n generalizing c with
  | zero => simp [flipAt]
  | succ n ih =>
    rw [ecaEvolve_succ, ecaEvolve_succ]
    have h1 : flipAt x (c - ↑(n + 1)) = flipAt x (c - 1 - n) := by push_cast; ring_nf
    rw [h1, ih (c - 1)]
    have hC : ecaEvolve r (flipAt x (c - 1 - n)) n c = ecaEvolve r x n c :=
      ecaEvolve_congr _ _ _ _ _ (fun j hj _ => by
        simp only [flipAt]; rw [Function.update_of_ne (by omega)])
    have hR : ecaEvolve r (flipAt x (c - 1 - n)) n (c + 1) = ecaEvolve r x n (c + 1) :=
      ecaEvolve_congr _ _ _ _ _ (fun j hj _ => by
        simp only [flipAt]; rw [Function.update_of_ne (by omega)])
    rw [hC, hR]
    generalize ecaEvolve r x n (c - 1) = L
    cases L
    · rw [Bool.not_false, hr]
    · rw [Bool.not_true, hr, Bool.not_not]

/-! ## 7. Settled wheels -/

/-- A mirror-symmetric wheel keeps a mirror-symmetric row mirror-symmetric. -/
theorem ecaEvolve_symmetric {r : ℕ} (hr : ∀ L C R, ecaRule r L C R = ecaRule r R C L)
    (x : Config) (hx : ∀ j, x (-j) = x j) (n : ℕ) (c : ℤ) :
    ecaEvolve r x n (-c) = ecaEvolve r x n c := by
  induction n generalizing c with
  | zero => exact hx c
  | succ n ih =>
    rw [ecaEvolve_succ, ecaEvolve_succ, hr]
    rw [show -c - 1 = -(c + 1) by ring, show -c + 1 = -(c - 1) by ring, ih, ih, ih]

theorem ecaRule_ninety (L C R : Bool) : ecaRule 90 L C R = xor L R := by
  cases L <;> cases C <;> cases R <;> decide

/-- **Wheel 90 on the impulse row has centre column `1, 0, 0, 0, …`.** -/
theorem ecaColumn_ninety_centre (n : ℕ) : ecaColumn 90 seed 0 n = decide (n = 0) := by
  cases n with
  | zero => rfl
  | succ n =>
    simp only [ecaColumn, ecaEvolve_succ, ecaRule_ninety, zero_sub, zero_add]
    have hsym := ecaEvolve_symmetric (r := 90)
      (fun L C R => by rw [ecaRule_ninety, ecaRule_ninety, Bool.xor_comm]) seed
      (fun j => by simp [seed]) n 1
    rw [hsym]
    simp

/-- Question 1 has answer **no** for wheel 90 on the impulse row. -/
theorem not_wheelProblem1_ninety : ¬ WheelProblem1 90 seed 0 := by
  unfold WheelProblem1
  rw [not_not]
  refine ⟨1, one_pos, 1, fun n hn => ?_⟩
  rw [ecaColumn_ninety_centre, ecaColumn_ninety_centre]
  simp; omega

theorem ones_ninety (n : ℕ) : ones (ecaColumn 90 seed 0) (n + 1) = 1 := by
  induction n with
  | zero => rw [ones_succ]; simp [ones, ecaColumn_ninety_centre]
  | succ n ih => rw [ones_succ, ih, ecaColumn_ninety_centre]; simp

/-- Question 2 has answer **no** for wheel 90 on the impulse row: the frequency tends to `0`. -/
theorem not_wheelProblem2_ninety : ¬ WheelProblem2 90 seed 0 := by
  unfold WheelProblem2
  rw [hasFrequencyHalf_iff]
  intro h
  -- `D(n)/n = (2 - n)/n → -1`
  have hlim : Filter.Tendsto (fun n : ℕ => ((wobble (ecaColumn 90 seed 0) n : ℤ) : ℝ) / n)
      Filter.atTop (nhds (-1)) := by
    have h2 : Filter.Tendsto (fun n : ℕ => (2 : ℝ) / n - 1) Filter.atTop (nhds (0 - 1)) :=
      (tendsto_const_div_atTop_nhds_zero_nat 2).sub tendsto_const_nhds
    rw [zero_sub] at h2
    refine h2.congr' ?_
    filter_upwards [Filter.eventually_ge_atTop 1] with n hn
    obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
    simp only [wobble, ones_ninety]
    have : ((m + 1 : ℕ) : ℝ) ≠ 0 := by positivity
    field_simp
    push_cast
    ring
  have := tendsto_nhds_unique h hlim
  norm_num at this

/-- Wheel 0 erases everything after one step: question 1 has answer **no**. -/
theorem not_wheelProblem1_zero (x : Config) (c : ℤ) : ¬ WheelProblem1 0 x c := by
  unfold WheelProblem1
  rw [not_not]
  refine ⟨1, one_pos, 1, fun n hn => ?_⟩
  obtain ⟨m, rfl⟩ : ∃ m, n = m + 1 := ⟨n - 1, by omega⟩
  simp [ecaColumn, ecaEvolve_succ, ecaRule]

/-- Wheel 204 is the identity: every column is constant, question 1 has answer **no**. -/
theorem not_wheelProblem1_identity (x : Config) (c : ℤ) : ¬ WheelProblem1 204 x c := by
  have hid : ∀ n, ecaEvolve 204 x n c = x c := by
    intro n
    induction n generalizing c with
    | zero => rfl
    | succ n ih =>
      rw [ecaEvolve_succ, ih, ih, ih]
      generalize x (c - 1) = L; generalize x c = C; generalize x (c + 1) = R
      cases L <;> cases C <;> cases R <;> decide
  unfold WheelProblem1
  rw [not_not]
  exact ⟨1, one_pos, 0, fun n _ => by simp [ecaColumn, hid]⟩

end GLM.Rule30
