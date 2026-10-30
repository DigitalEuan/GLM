module

public import RequestProject.GLM.Rule30.PeriodTwoHalfLine

/-!
# Round 21: Problem 1 needs only the left half-line, for every period

`PeriodTwoHalfLine.lean` treats period 2.  The same idea works for **every** period `p`.

If column `c` of a left-white row is `p`-periodic, the cells left of `c` evolve on their own: the
cell next to the column reads the column itself as its right input.  So the left half-line is a
deterministic machine **driven** by the periodic column.  Rule 30 also gives one check: when the
column is black at time `t`, its next value is `not (cell c-1 at time t)`
(`col_black_forces_left`).  So at every black time of the drive, the machine's cell next to the
boundary must be the complement of the drive's next value.

* `driveN p k t = k.testBit (t % p)` — the periodic drive whose period word is the bits of `k`.
* `halfStateD bd S t` — the half-line state (bit `i` = cell `c - 1 - i`) driven by `bd`.
* `dDiesBy bd S T` — the machine fails a check before time `T`.
* `run_lt_of_dDiesBy` — if it fails, the real column cannot follow the drive on `[0, T]`.
* `col_eq_driveN` — a column that is `p`-periodic on `[0, L]` follows `driveN p k` there, where
  `k` encodes its first `p` values.
* **`HalfLineDies p`** — the one-sided target for period `p`: for every drive word `k ≠ 0` of
  length `p` and every half-line code `S > 0`, the machine eventually fails.
* **`leftWhiteAperiodic_of_halfLineDies`** — `HalfLineDies p → LeftWhiteAperiodic p`.
* **`problem1_of_halfLineDies`** — if `HalfLineDies p` holds for every `p ≥ 1`, Problem 1 holds.
  The cells to the right of the column never enter.
* **`halfLineDies_one`** — `HalfLineDies 1` is **proved**: under the constant black drive the
  machine is forced into the fixed pattern `0101…` (`constDrive_pattern`) and fails by time
  `d + 2` (`constDrive_dies`).  This re-derives the period-1 rung inside the framework.
* **`blackRun_bound`** — uniform corollary: a black constant run at distance `d` from the edge
  lasts at most `d + 1` steps (the general period-1 bound is `3d + 5`).

The finite certificates are in `HalfLineMachineData.lean`.
-/

@[expose] public section

namespace GLM.Rule30

/-- The periodic drive with period `p` whose period word is the bits of `k`. -/
def driveN (p k t : ℕ) : Bool := k.testBit (t % p)

/-- The half-line state driven by the boundary sequence `bd`. -/
def halfStateD (bd : ℕ → Bool) (S : ℕ) : ℕ → ℕ
  | 0 => S
  | t + 1 => halfStep (bd t) (halfStateD bd S t)

/-- Single-pass failure search: is there a time `s ∈ [t, t + n)` with a failed check? -/
def dRunAux (bd : ℕ → Bool) : ℕ → ℕ → ℕ → Bool
  | 0, _, _ => false
  | n + 1, t, S => (bd t && (S.testBit 0 == bd (t + 1))) || dRunAux bd n (t + 1) (halfStep (bd t) S)

/-- The driven machine fails a check before time `T`. -/
def dDiesBy (bd : ℕ → Bool) (S T : ℕ) : Bool := dRunAux bd T 0 S

theorem dRunAux_spec (bd : ℕ → Bool) (S : ℕ) (n t : ℕ) :
    dRunAux bd n t (halfStateD bd S t) = true ↔
      ∃ s, t ≤ s ∧ s < t + n ∧ bd s = true ∧ (halfStateD bd S s).testBit 0 = bd (s + 1) := by
  induction n generalizing t with
  | zero => simp [dRunAux]; intro s h1 h2; omega
  | succ n ih =>
    simp only [dRunAux, Bool.or_eq_true, Bool.and_eq_true, beq_iff_eq]
    rw [show halfStep (bd t) (halfStateD bd S t) = halfStateD bd S (t + 1) from rfl, ih]
    constructor
    · rintro (h | ⟨s, h1, h2, h⟩)
      · exact ⟨t, le_rfl, by omega, h⟩
      · exact ⟨s, by omega, by omega, h⟩
    · rintro ⟨s, h1, h2, h⟩
      rcases Nat.eq_or_lt_of_le h1 with rfl | h1
      · exact Or.inl h
      · exact Or.inr ⟨s, by omega, by omega, h⟩

theorem dDiesBy_spec (bd : ℕ → Bool) (S T : ℕ) :
    dDiesBy bd S T = true ↔
      ∃ t < T, bd t = true ∧ (halfStateD bd S t).testBit 0 = bd (t + 1) := by
  rw [dDiesBy, show S = halfStateD bd S 0 from rfl, dRunAux_spec]
  constructor
  · rintro ⟨s, -, h2, h⟩; exact ⟨s, by omega, h⟩
  · rintro ⟨s, h2, h⟩; exact ⟨s, by omega, by omega, h⟩

theorem dDiesBy_mono {bd : ℕ → Bool} {S T T' : ℕ} (h : dDiesBy bd S T = true) (hT : T ≤ T') :
    dDiesBy bd S T' = true := by
  rw [dDiesBy_spec] at *
  obtain ⟨t, ht, h⟩ := h
  exact ⟨t, by omega, h⟩

/-- **The driven machine is exact** while the column follows the drive. -/
theorem halfStateD_eq_evolve (x : Config) (c : ℤ) (bd : ℕ → Bool) (S T : ℕ)
    (hS : ∀ i : ℕ, S.testBit i = x (c - 1 - i))
    (hcol : ∀ t < T, evolve x t c = bd t) :
    ∀ t ≤ T, ∀ i : ℕ, (halfStateD bd S t).testBit i = evolve x t (c - 1 - i) := by
  intro t
  induction t with
  | zero => intro _ i; simpa using hS i
  | succ t ih =>
    intro ht i
    simp only [halfStateD]
    rw [testBit_halfStep, evolve_succ, ih (by omega) (i + 1), ih (by omega) i]
    have e1 : c - 1 - ((i + 1 : ℕ) : ℤ) = c - 1 - i - 1 := by push_cast; ring
    rw [e1]
    congr 2
    rcases Nat.eq_zero_or_pos i with rfl | hi
    · simp only [if_true]
      rw [← hcol t (by omega)]
      congr 1
      push_cast; ring
    · rw [if_neg hi.ne', ih (by omega) (i - 1)]
      congr 1
      have : ((i - 1 : ℕ) : ℤ) = (i : ℤ) - 1 := by omega
      rw [this]; ring

/-- **The forced check, in general.** When column `c` is black at time `t`, the cell left of it
is the complement of the column's next value. -/
theorem col_black_forces_left (x : Config) (c : ℤ) (t : ℕ) (h0 : evolve x t c = true) :
    evolve x t (c - 1) = !evolve x (t + 1) c := by
  rw [evolve_succ, h0]
  cases evolve x t (c - 1) <;> rfl

/-- **Soundness.** If the machine started from the code of the cells left of `c` fails by time
`T`, the column cannot follow the drive on `[0, T]`. -/
theorem run_lt_of_dDiesBy (x : Config) (c : ℤ) (bd : ℕ → Bool) (S T : ℕ)
    (hS : ∀ i : ℕ, S.testBit i = x (c - 1 - i))
    (hdie : dDiesBy bd S T = true) :
    ¬ ∀ t ≤ T, evolve x t c = bd t := by
  intro hcol
  obtain ⟨t, ht, hb, hw⟩ := (dDiesBy_spec bd S T).1 hdie
  have heq := halfStateD_eq_evolve x c bd S T hS (fun s hs => hcol s (by omega)) t (by omega) 0
  have h0 : evolve x t c = true := by rw [hcol t (by omega)]; exact hb
  have := col_black_forces_left x c t h0
  simp only [Nat.cast_zero, sub_zero] at heq
  rw [heq, this, hcol (t + 1) (by omega)] at hw
  cases h : bd (t + 1) <;> simp [h] at hw

/-! ## Periodic columns follow a periodic drive -/

/-- A column that is `p`-periodic on `[0, L]` follows the drive whose word encodes its first `p`
values. -/
theorem col_eq_driveN (x : Config) (c : ℤ) (p L : ℕ) (hp : 0 < p)
    (hrun : ∀ t, t + p ≤ L → evolve x (t + p) c = evolve x t c) :
    ∀ t ≤ L, evolve x t c = driveN p (bitsOf (fun s => evolve x s c) p) t := by
  intro t
  induction t using Nat.strong_induction_on with
  | _ t ih =>
    intro ht
    rw [driveN, testBit_bitsOf]
    rcases Nat.lt_or_ge t p with h | h
    · simp [Nat.mod_eq_of_lt h, h]
    · obtain ⟨s, rfl⟩ : ∃ s, t = s + p := ⟨t - p, by omega⟩
      rw [hrun s (by omega), ih s (by omega) (by omega), driveN, testBit_bitsOf,
        Nat.add_mod_right]

/-- If the drive word is `0`, a `p`-periodic column is white on the whole window. -/
theorem col_white_of_driveN_zero (x : Config) (c : ℤ) (p L : ℕ) (hp : 0 < p)
    (hrun : ∀ t, t + p ≤ L → evolve x (t + p) c = evolve x t c)
    (h0 : bitsOf (fun s => evolve x s c) p = 0) :
    ∀ t ≤ L, evolve x t c = false := by
  intro t ht
  rw [col_eq_driveN x c p L hp hrun t ht, h0, driveN, Nat.zero_testBit]

/-! ## The one-sided target and Problem 1 -/

/-- **The one-sided target for period `p`.** For every non-zero drive word `k < 2^p` and every
half-line code `S > 0`, the driven machine eventually fails a check. -/
def HalfLineDies (p : ℕ) : Prop :=
  ∀ k, 0 < k → k < 2 ^ p → ∀ S, 0 < S → ∃ T, dDiesBy (driveN p k) S T = true

/-- **The one-sided target implies the lifted statement for period `p`.** -/
theorem leftWhiteAperiodic_of_halfLineDies {p : ℕ} (hp : 0 < p) (h : HalfLineDies p) :
    LeftWhiteAperiodic p := by
  rw [leftWhiteAperiodic_iff_from_start]
  rintro x ⟨ℓ, hw, hb⟩ c hper
  -- move to a row of the stack whose edge lies strictly left of `c`
  set M : ℕ := (ℓ - c).toNat + 1 with hM
  set y := evolve x M
  have hyw : ∀ j, j < ℓ - M → y j = false := fun j hj => evolve_white_left x ℓ hw M j hj
  have hyb : y (ℓ - M) = true := evolve_left_edge x ℓ hw hb M
  have hyper : ∀ t, evolve y (t + p) c = evolve y t c := fun t => by
    simp only [y]; rw [evolve_evolve, evolve_evolve, show M + (t + p) = (M + t) + p by ring]
    exact hper (M + t) (by omega)
  set k := bitsOf (fun s => evolve y s c) p with hk
  rcases Nat.eq_zero_or_pos k with hk0 | hkpos
  · -- white drive: the column is constant white, excluded by the period-1 case
    refine leftWhiteAperiodic_one y (isLeftWhite_evolve ⟨ℓ, hw, hb⟩ M) c 0 fun t _ => ?_
    rw [col_white_of_driveN_zero y c p (t + 1) hp (fun s _ => hyper s) hk0 (t + 1) le_rfl,
      col_white_of_driveN_zero y c p (t + 1) hp (fun s _ => hyper s) hk0 t (by omega)]
  · set d : ℕ := (c - (ℓ - M)).toNat with hd
    have hd1 : 1 ≤ d := by omega
    have hcd : c - d = ℓ - M := by omega
    obtain ⟨S, hS1, _, hS⟩ := exists_code y c d hd1 (fun j hj => hyw j (by omega))
      (by rw [hcd]; exact hyb)
    obtain ⟨T, hT⟩ := h k hkpos (bitsOf_lt _ _) S (lt_of_lt_of_le (Nat.two_pow_pos _) hS1)
    exact run_lt_of_dDiesBy y c (driveN p k) S T hS hT
      (col_eq_driveN y c p T hp (fun t _ => hyper t))

/-- **Problem 1 from the one-sided targets.** If, for every period `p ≥ 1`, no periodic drive
with a black cell can keep a finite half-line consistent forever, then the centre column of
Rule 30 is not eventually periodic. -/
theorem problem1_of_halfLineDies (h : ∀ p, 0 < p → HalfLineDies p) : Problem1 :=
  problem1_of_leftWhiteAperiodic fun p hp => leftWhiteAperiodic_of_halfLineDies hp (h p hp)

/-! ## Period 1 inside the machine: `HalfLineDies 1` is proved -/

/-- Under the constant black drive, a machine that has not failed before time `T` holds the
fixed pattern `0, 1, 0, 1, …` (bit `i` is `1` iff `i` is odd) in every cell `i` at every time
`t` with `t + i < T`. -/
theorem constDrive_pattern (S T : ℕ)
    (hsurv : ∀ t < T, (halfStateD (fun _ => true) S t).testBit 0 = false) :
    ∀ i t, t + i < T → (halfStateD (fun _ => true) S t).testBit i = decide (i % 2 = 1) := by
  intro i
  induction i using Nat.strong_induction_on with
  | _ i ih =>
    intro t ht
    match i, ih with
    | 0, _ => simpa using hsurv t (by omega)
    | 1, _ =>
      have h := hsurv (t + 1) (by omega)
      simp only [halfStateD] at h
      rw [testBit_halfStep] at h
      simp only [if_true, Bool.or_true, Bool.xor_true, Bool.not_eq_false'] at h
      simpa using h
    | j + 2, ih =>
      have h := ih (j + 1) (by omega) (t + 1) (by omega)
      simp only [halfStateD] at h
      rw [testBit_halfStep, if_neg (by omega), ih (j + 1) (by omega) t (by omega),
        show j + 1 - 1 = j by omega, ih j (by omega) t (by omega)] at h
      have hor : (decide ((j + 1) % 2 = 1) || decide (j % 2 = 1)) = true := by
        rcases Nat.mod_two_eq_zero_or_one j with hj | hj <;> simp [hj, Nat.add_mod]
      rw [hor, Bool.xor_true] at h
      have e : decide ((j + 2) % 2 = 1) = !decide ((j + 1) % 2 = 1) := by
        rcases Nat.mod_two_eq_zero_or_one j with hj | hj <;> simp [hj, Nat.add_mod]
      rw [e, ← h, Bool.not_not]

/-- **Constant black drive: the machine fails by time `d + 2`** for every code `S < 2^d`. -/
theorem constDrive_dies (S d : ℕ) (hS : S < 2 ^ d) :
    dDiesBy (fun _ => true) S (d + 2) = true := by
  by_contra hne
  have hsurv : ∀ t < d + 2, (halfStateD (fun _ => true) S t).testBit 0 = false := by
    intro t ht
    by_contra h
    exact hne ((dDiesBy_spec _ S _).2 ⟨t, ht, rfl, by simpa using h⟩)
  -- pick the odd index among `d` and `d + 1`
  obtain ⟨i, hi1, hi2, hodd⟩ : ∃ i, d ≤ i ∧ i ≤ d + 1 ∧ i % 2 = 1 := by
    rcases Nat.mod_two_eq_zero_or_one d with h | h
    · exact ⟨d + 1, by omega, le_rfl, by omega⟩
    · exact ⟨d, le_rfl, by omega, h⟩
  have h1 := constDrive_pattern S (d + 2) hsurv i 0 (by omega)
  have h0 : S.testBit i = false :=
    Nat.testBit_eq_false_of_lt (lt_of_lt_of_le hS (Nat.pow_le_pow_right (by norm_num) hi1))
  simp only [halfStateD] at h1
  rw [h0] at h1
  simp [hodd] at h1

/-- **`HalfLineDies 1` holds** (proved for every code): the period-1 rung, re-derived inside the
half-line framework.  The only non-white drive of period `1` is constant black. -/
theorem halfLineDies_one : HalfLineDies 1 := by
  intro k hk0 hk1 S _
  obtain rfl : k = 1 := by omega
  refine ⟨S + 2, ?_⟩
  have : driveN 1 1 = fun _ => true := by
    funext t; simp [driveN, Nat.mod_one]
  rw [this]
  exact constDrive_dies S S Nat.lt_two_pow_self

/-- **Uniform run bound for black constant runs** (proved for every `d`): in a left-white row
with edge `ℓ`, a column at distance `d` that is black and constant on `[0, L]` has `L ≤ d + 1`.
(The general period-1 bound `runBound_one` is `3d + 5`; white constant runs are not covered
here.) -/
theorem blackRun_bound (x : Config) (ℓ : ℤ) (hw : ∀ j, j < ℓ → x j = false) (d L : ℕ)
    (hrun : ∀ t, t + 1 ≤ L → evolve x (t + 1) (ℓ + d) = evolve x t (ℓ + d))
    (hblack : evolve x 0 (ℓ + d) = true) : L ≤ d + 1 := by
  by_contra hL
  push_neg at hL
  set c := ℓ + d
  set S := bitsOf (fun i => x (c - 1 - i)) d
  have hS : ∀ i : ℕ, S.testBit i = x (c - 1 - i) := fun i => by
    rw [testBit_bitsOf]
    by_cases hi : i < d
    · simp [hi]
    · simp only [hi, decide_false, Bool.false_and]
      exact (hw _ (by omega)).symm
  have hcol : ∀ t ≤ d + 2, evolve x t c = (fun _ => true) t := by
    intro t ht
    induction t with
    | zero => exact hblack
    | succ t ih => rw [hrun t (by omega), ih (by omega)]
  exact run_lt_of_dDiesBy x c _ S (d + 2) hS (constDrive_dies S d (bitsOf_lt _ _)) hcol

/-! ## Run bounds from finite checks -/

/-- **Periodic run bound with a non-white drive**, for distances `d ≤ D`: a column at distance
`d` that is `p`-periodic on `[0, L]` and has a black cell among its first `p` values has
`L ≤ B d`.  (White drives give constant runs, covered by `runBound_one`.) -/
def DrivenRunBoundUpTo (p : ℕ) (B : ℕ → ℕ) (D : ℕ) : Prop :=
  ∀ (x : Config) (ℓ : ℤ), (∀ j, j < ℓ → x j = false) → x ℓ = true →
    ∀ d L : ℕ, d ≤ D → (∀ t, t + p ≤ L → evolve x (t + p) (ℓ + d) = evolve x t (ℓ + d)) →
      0 < bitsOf (fun s => evolve x s (ℓ + d)) p → L ≤ B d

/-- The finite check for period `p`, distance `d`, horizon `T`: every non-zero drive word and
every code of `d` cells (black at the far end) fails before `T`. -/
def drivenCheck (p d T : ℕ) : Bool :=
  (List.range (2 ^ p - 1)).all fun j =>
    (List.range (2 ^ (d - 1))).all fun k =>
      dDiesBy (driveN p (j + 1)) (2 ^ (d - 1) + k) T

theorem dDiesBy_of_drivenCheck {p d T k S : ℕ} (h : drivenCheck p d T = true) (hd : 1 ≤ d)
    (hk1 : 0 < k) (hk2 : k < 2 ^ p) (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) :
    dDiesBy (driveN p k) S T = true := by
  unfold drivenCheck at h
  rw [List.all_eq_true] at h
  have hd' : 2 ^ d = 2 ^ (d - 1) + 2 ^ (d - 1) := by
    rw [← two_mul, ← pow_succ']; congr 1; omega
  have := h (k - 1) (List.mem_range.2 (by omega))
  rw [List.all_eq_true] at this
  have := this (S - 2 ^ (d - 1)) (List.mem_range.2 (by omega))
  rwa [show k - 1 + 1 = k by omega, show 2 ^ (d - 1) + (S - 2 ^ (d - 1)) = S by omega] at this

/-- The finite check at distance `0` (the column starts at the edge; the half-line is white,
code `0`). -/
def drivenCheckZero (p T : ℕ) : Bool :=
  (List.range (2 ^ p - 1)).all fun j => dDiesBy (driveN p (j + 1)) 0 T

/-- **From finite checks to a driven run bound.** -/
theorem drivenRunBoundUpTo_of_checks {p D : ℕ} {B : ℕ → ℕ} (hp : 0 < p)
    (hc0 : drivenCheckZero p (B 0 + 1) = true)
    (hc : ∀ d ≤ D, 1 ≤ d → drivenCheck p d (B d + 1) = true) : DrivenRunBoundUpTo p B D := by
  intro x ℓ hw hb d L hdD hrun hk
  by_contra hL
  push_neg at hL
  set c := ℓ + d with hc'
  have hcol := fun t (ht : t ≤ B d + 1) => col_eq_driveN x c p L hp hrun t (by omega)
  rcases Nat.eq_zero_or_pos d with rfl | hd
  · -- distance `0`: the cells left of the column are white, code `0`
    have hS : ∀ i : ℕ, (0 : ℕ).testBit i = x (c - 1 - i) := fun i => by
      rw [Nat.zero_testBit, hw _ (by omega)]
    unfold drivenCheckZero at hc0
    rw [List.all_eq_true] at hc0
    have hk2 := bitsOf_lt (fun s => evolve x s c) p
    have := hc0 (bitsOf (fun s => evolve x s c) p - 1) (List.mem_range.2 (by omega))
    rw [show bitsOf (fun s => evolve x s c) p - 1 + 1 = bitsOf (fun s => evolve x s c) p by
      omega] at this
    exact run_lt_of_dDiesBy x c _ 0 (B 0 + 1) hS this hcol
  obtain ⟨S, hS1, hS2, hS⟩ := exists_code x c d hd (fun j hj => hw j (by omega))
    (by rw [show c - d = ℓ by omega]; exact hb)
  have hdie := dDiesBy_of_drivenCheck (hc d hdD hd) hd hk (bitsOf_lt _ _) hS1 hS2
  exact run_lt_of_dDiesBy x c _ S (B d + 1) hS hdie hcol

end GLM.Rule30
