module

public import RequestProject.GLM.Rule30.LeftWhiteLift

/-!
# Round 21: the period-2 rung needs only the left half-line

`LeftWhiteAperiodic 2` (no column of a left-white row is eventually 2-periodic) is the narrowest
open rung of the stack lift.  Period 1 is proved, so the only case left is a column that
**alternates** `1 0 1 0 …`.

This file shows that the cells to the **right** of the alternating column never matter.  If column
`c` alternates, the cells left of `c` evolve on their own: Rule 30 reads `L, C, R`, and for the cell
next to the column the right input `R` is the alternating column itself.  So the left half-line is a
deterministic machine fed by the alternating column.  The alternation also forces a check on this
machine: **whenever column `c` is black, the cell just to its left must be black too**
(`alt_forces_left_black`; Rule 30 gives `next(c) = not cell(c-1)` when `c` is black).

The half-line is stored as a natural number: bit `i` is the cell `c - 1 - i`.

* `halfStep b S` — one Rule 30 step of the half-line with boundary input `b`
  (`testBit_halfStep`: it is Rule 30, bit by bit).
* `halfState S φ t` — the state after `t` steps when the boundary is black exactly at the times
  `t ≡ φ (mod 2)`.
* `halfDiesBy S φ T` — the machine **fails the check** before time `T`: at some black boundary time
  `t < T`, the cell next to the boundary is white.
* `halfState_eq_evolve` — the machine is exactly the left part of the real run, for as long as the
  column alternates.
* **`altRun_lt_of_halfDiesBy`** — if the machine started from a left-white row's cells fails by time
  `T`, then the real column cannot alternate on a window of length `T`.
* **`PeriodTwoHalfLineDies`** — the one-sided target: every finite half-line word (black at its far
  end) fails the check eventually, for both phases.
* **`leftWhiteAperiodic_two_of_halfLineDies`** — the one-sided target implies `LeftWhiteAperiodic 2`.
  With the period-1 case already proved, the alternating case is all that is needed.

The finite certificates for this target are in `PeriodTwoHalfLineData.lean`.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## The half-line machine -/

/-- One Rule 30 step of the half-line `(…, c-2, c-1)`, stored with bit `i` = cell `c - 1 - i`;
`b` is the cell `c` (the boundary). -/
def halfStep (b : Bool) (S : ℕ) : ℕ := (S >>> 1) ^^^ (S ||| ((S <<< 1) ||| b.toNat))

/-- The boundary is black exactly at the times `t ≡ φ (mod 2)`. -/
def altBit (φ t : ℕ) : Bool := decide (t % 2 = φ % 2)

/-- The state of the half-line after `t` steps with an alternating boundary of phase `φ`. -/
def halfState (S φ : ℕ) : ℕ → ℕ
  | 0 => S
  | t + 1 => halfStep (altBit φ t) (halfState S φ t)

theorem testBit_halfStep (b : Bool) (S i : ℕ) :
    (halfStep b S).testBit i =
      xor (S.testBit (i + 1)) (S.testBit i || (if i = 0 then b else S.testBit (i - 1))) := by
  unfold halfStep
  rw [Nat.testBit_xor, Nat.testBit_or, Nat.testBit_or, Nat.testBit_shiftRight,
    Nat.testBit_shiftLeft]
  rcases Nat.eq_zero_or_pos i with rfl | hi
  · cases b <;> simp
  · have h1 : (b.toNat).testBit i = false := by
      cases b
      · simp
      · show Nat.testBit 1 i = false
        cases h : Nat.testBit 1 i
        · rfl
        · exact absurd (Nat.testBit_one_eq_true_iff_self_eq_zero.1 h) hi.ne'
    simp only [h1, Bool.or_false, if_neg hi.ne', add_comm 1 i]
    congr 2
    simp [show 1 ≤ i from hi]

/-- `halfDiesBy S φ T`: the machine fails the check at some black boundary time `t < T`. -/
def halfDiesBy (S φ : ℕ) : ℕ → Bool
  | 0 => false
  | T + 1 => halfDiesBy S φ T || (altBit φ T && !(halfState S φ T).testBit 0)

theorem halfDiesBy_spec (S φ T : ℕ) :
    halfDiesBy S φ T = true ↔
      ∃ t < T, altBit φ t = true ∧ (halfState S φ t).testBit 0 = false := by
  induction T with
  | zero => simp [halfDiesBy]
  | succ T ih =>
    simp only [halfDiesBy, Bool.or_eq_true, ih, Bool.and_eq_true, Bool.not_eq_true']
    constructor
    · rintro (⟨t, ht, h⟩ | h)
      · exact ⟨t, by omega, h⟩
      · exact ⟨T, by omega, h⟩
    · rintro ⟨t, ht, h⟩
      rcases Nat.lt_succ_iff_lt_or_eq.1 ht with ht | rfl
      · exact Or.inl ⟨t, ht, h⟩
      · exact Or.inr h

theorem halfDiesBy_mono {S φ T T' : ℕ} (h : halfDiesBy S φ T = true) (hT : T ≤ T') :
    halfDiesBy S φ T' = true := by
  rw [halfDiesBy_spec] at *
  obtain ⟨t, ht, h⟩ := h
  exact ⟨t, by omega, h⟩

/-- A fast (single pass) version of `halfDiesBy`, used by the finite checks. -/
def halfRunAux (φ : ℕ) : ℕ → ℕ → ℕ → Bool
  | 0, _, _ => false
  | n + 1, t, S => (altBit φ t && !S.testBit 0) || halfRunAux φ n (t + 1) (halfStep (altBit φ t) S)

theorem halfRunAux_spec (S φ : ℕ) (n t : ℕ) :
    halfRunAux φ n t (halfState S φ t) = true ↔
      ∃ s, t ≤ s ∧ s < t + n ∧ altBit φ s = true ∧ (halfState S φ s).testBit 0 = false := by
  induction n generalizing t with
  | zero => simp [halfRunAux]; intro s h1 h2; omega
  | succ n ih =>
    simp only [halfRunAux, Bool.or_eq_true, Bool.and_eq_true, Bool.not_eq_true']
    rw [show halfStep (altBit φ t) (halfState S φ t) = halfState S φ (t + 1) from rfl, ih]
    constructor
    · rintro (h | ⟨s, h1, h2, h⟩)
      · exact ⟨t, le_rfl, by omega, h⟩
      · exact ⟨s, by omega, by omega, h⟩
    · rintro ⟨s, h1, h2, h⟩
      rcases Nat.eq_or_lt_of_le h1 with rfl | h1
      · exact Or.inl h
      · exact Or.inr ⟨s, by omega, by omega, h⟩

/-- `halfDiesFast S φ T` computes `halfDiesBy S φ T` in one pass. -/
def halfDiesFast (S φ T : ℕ) : Bool := halfRunAux φ T 0 S

theorem halfDiesFast_eq (S φ T : ℕ) : halfDiesFast S φ T = halfDiesBy S φ T := by
  apply Bool.eq_iff_iff.2
  rw [halfDiesBy_spec, halfDiesFast, show S = halfState S φ 0 from rfl, halfRunAux_spec]
  constructor
  · rintro ⟨s, -, h2, h⟩; exact ⟨s, by omega, h⟩
  · rintro ⟨s, h2, h⟩; exact ⟨s, by omega, by omega, h⟩

/-! ## The machine is the left part of the real run -/

/-- **The machine is exact.** If the cells left of `c` are encoded by `S` at time `0`, and
column `c` agrees with the alternating boundary at all times `< T`, then for every `t ≤ T` the
machine state encodes the cells left of `c` at time `t`. -/
theorem halfState_eq_evolve (x : Config) (c : ℤ) (S φ T : ℕ)
    (hS : ∀ i : ℕ, S.testBit i = x (c - 1 - i))
    (hcol : ∀ t < T, evolve x t c = altBit φ t) :
    ∀ t ≤ T, ∀ i : ℕ, (halfState S φ t).testBit i = evolve x t (c - 1 - i) := by
  intro t
  induction t with
  | zero => intro _ i; simpa using hS i
  | succ t ih =>
    intro ht i
    simp only [halfState]
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

/-- **The forced check.** If column `c` is black at time `t` and white at time `t + 1`, the cell
just left of it is black at time `t`. -/
theorem alt_forces_left_black (x : Config) (c : ℤ) (t : ℕ)
    (h0 : evolve x t c = true) (h1 : evolve x (t + 1) c = false) :
    evolve x t (c - 1) = true := by
  rw [evolve_succ, h0] at h1
  simpa [rule30] using h1

/-! ## From the machine to run bounds -/

/-- A column that is `2`-periodic on `[0, L]` and not constant at the start follows the
alternating boundary of phase `φ` (where `φ = 0` if it starts black) on the whole window. -/
theorem col_eq_altBit_of_alt (x : Config) (c : ℤ) (L : ℕ)
    (hrun : ∀ t, t + 2 ≤ L → evolve x (t + 2) c = evolve x t c)
    (hne : evolve x 1 c ≠ evolve x 0 c) :
    ∀ t ≤ L, evolve x t c = altBit (if evolve x 0 c then 0 else 1) t := by
  intro t
  induction t using Nat.strong_induction_on with
  | _ t ih =>
    intro ht
    match t, ih with
    | 0, _ =>
      cases h : evolve x 0 c <;> simp [altBit]
    | 1, _ =>
      have h1 : evolve x 1 c = !evolve x 0 c := by
        revert hne
        cases evolve x 0 c <;> cases evolve x 1 c <;> simp
      rw [h1]
      cases h : evolve x 0 c <;> simp [altBit]
    | s + 2, ih =>
      rw [hrun s (by omega), ih s (by omega) (by omega)]
      unfold altBit
      rw [Nat.add_mod_right]

/-- **Main soundness theorem.** Let `x` be white left of `c - d` and black at `c - d`
(`1 ≤ d`), and let `S` encode the `d` cells `c - 1, …, c - d` (so `S < 2 ^ d` and bit `d - 1`
is set).  If the machine started at `S` with phase `φ` fails the check by time `T`, then
column `c` cannot follow the alternating boundary of phase `φ` on the window `[0, T]`. -/
theorem altRun_lt_of_halfDiesBy (x : Config) (c : ℤ) (S φ T : ℕ)
    (hS : ∀ i : ℕ, S.testBit i = x (c - 1 - i))
    (hdie : halfDiesBy S φ T = true) :
    ¬ ∀ t ≤ T, evolve x t c = altBit φ t := by
  intro hcol
  obtain ⟨t, ht, hb, hw⟩ := (halfDiesBy_spec S φ T).1 hdie
  have heq := halfState_eq_evolve x c S φ T hS (fun s hs => hcol s (by omega)) t (by omega) 0
  have h0 : evolve x t c = true := by rw [hcol t (by omega)]; exact hb
  have h1 : evolve x (t + 1) c = false := by
    rw [hcol (t + 1) (by omega)]
    revert hb
    simp only [altBit, decide_eq_true_eq, decide_eq_false_iff_not]
    omega
  have := alt_forces_left_black x c t h0 h1
  simp only [Nat.cast_zero, sub_zero] at heq
  rw [heq, this] at hw
  exact absurd hw (by simp)

/-! ## Encoding the cells of a left-white row -/

/-- The number whose bit `i` is `f i` for `i < d` (and `0` above). -/
def bitsOf (f : ℕ → Bool) : ℕ → ℕ
  | 0 => 0
  | d + 1 => Nat.bit (f 0) (bitsOf (fun i => f (i + 1)) d)

theorem testBit_bitsOf (f : ℕ → Bool) (d i : ℕ) :
    (bitsOf f d).testBit i = (decide (i < d) && f i) := by
  induction d generalizing f i with
  | zero => simp [bitsOf]
  | succ d ih =>
    simp only [bitsOf]
    rcases i with _ | i
    · simp
    · rw [Nat.testBit_bit_succ, ih]
      simp

theorem bitsOf_lt (f : ℕ → Bool) (d : ℕ) : bitsOf f d < 2 ^ d := by
  induction d generalizing f with
  | zero => simp [bitsOf]
  | succ d ih =>
    simp only [bitsOf, Nat.bit_val]
    have := ih (fun i => f (i + 1))
    cases f 0 <;> simp [pow_succ] <;> omega

/-- The code of the `d` cells left of `c` in a row that is white left of `c - d` and black at
`c - d`: it satisfies the hypothesis of `altRun_lt_of_halfDiesBy`, and lies in `[2^(d-1), 2^d)`. -/
theorem exists_code (x : Config) (c : ℤ) (d : ℕ) (hd : 1 ≤ d)
    (hw : ∀ j, j < c - d → x j = false) (hb : x (c - d) = true) :
    ∃ S, 2 ^ (d - 1) ≤ S ∧ S < 2 ^ d ∧ ∀ i : ℕ, S.testBit i = x (c - 1 - i) := by
  refine ⟨bitsOf (fun i => x (c - 1 - i)) d, ?_, bitsOf_lt _ _, fun i => ?_⟩
  · apply Nat.ge_two_pow_of_testBit
    rw [testBit_bitsOf]
    simp only [show d - 1 < d by omega, decide_true, Bool.true_and]
    convert hb using 2
    omega
  · rw [testBit_bitsOf]
    by_cases hi : i < d
    · simp [hi]
    · simp only [hi, decide_false, Bool.false_and]
      exact (hw _ (by omega)).symm

/-! ## Run bounds for alternating columns -/

/-- **Alternating run bound** (period 2, non-constant runs only): in a left-white row with edge
`ℓ`, a column at distance `d` from the edge that is `2`-periodic and not constant on `[0, L]` has
`L ≤ B d`.  (Constant runs are covered by `runBound_one`.) -/
def AltRunBound (B : ℕ → ℕ) : Prop :=
  ∀ (x : Config) (ℓ : ℤ), (∀ j, j < ℓ → x j = false) → x ℓ = true →
    ∀ d L : ℕ, (∀ t, t + 2 ≤ L → evolve x (t + 2) (ℓ + d) = evolve x t (ℓ + d)) →
      evolve x 1 (ℓ + d) ≠ evolve x 0 (ℓ + d) → L ≤ B d

/-- `AltRunBound` restricted to distances `d ≤ D`. -/
def AltRunBoundUpTo (B : ℕ → ℕ) (D : ℕ) : Prop :=
  ∀ (x : Config) (ℓ : ℤ), (∀ j, j < ℓ → x j = false) → x ℓ = true →
    ∀ d L : ℕ, d ≤ D → (∀ t, t + 2 ≤ L → evolve x (t + 2) (ℓ + d) = evolve x t (ℓ + d)) →
      evolve x 1 (ℓ + d) ≠ evolve x 0 (ℓ + d) → L ≤ B d

/-- The edge column itself (`d = 0`) never starts alternating: the cell at the edge is black at
times `0` and `1`. -/
theorem edge_not_alt (x : Config) (ℓ : ℤ) (hw : ∀ j, j < ℓ → x j = false) (hb : x ℓ = true) :
    evolve x 1 (ℓ + (0 : ℕ)) = evolve x 0 (ℓ + (0 : ℕ)) := by
  simp only [Nat.cast_zero, add_zero]
  rw [evolve_succ]
  simp [hw (ℓ - 1) (by omega), hb, rule30]

/-- The finite check: every code of `d` cells (black at the far end) fails by time `T`, in both
phases. -/
def halfCheck (d T : ℕ) : Bool :=
  (List.range (2 ^ (d - 1))).all fun k =>
    halfDiesFast (2 ^ (d - 1) + k) 0 T && halfDiesFast (2 ^ (d - 1) + k) 1 T

theorem halfDiesBy_of_halfCheck {d T S : ℕ} (h : halfCheck d T = true) (hd : 1 ≤ d)
    (h1 : 2 ^ (d - 1) ≤ S) (h2 : S < 2 ^ d) (φ : ℕ) (hφ : φ = 0 ∨ φ = 1) :
    halfDiesBy S φ T = true := by
  unfold halfCheck at h
  rw [List.all_eq_true] at h
  have hd' : 2 ^ d = 2 ^ (d - 1) + 2 ^ (d - 1) := by
    rw [← two_mul, ← pow_succ']; congr 1; omega
  have := h (S - 2 ^ (d - 1)) (List.mem_range.2 (by omega))
  rw [show 2 ^ (d - 1) + (S - 2 ^ (d - 1)) = S by omega, Bool.and_eq_true,
    halfDiesFast_eq, halfDiesFast_eq] at this
  rcases hφ with rfl | rfl
  · exact this.1
  · exact this.2

/-- **From the finite check to an alternating run bound.** If `halfCheck d (B d + 1)` holds for
every `1 ≤ d ≤ D`, then `AltRunBoundUpTo B D`. -/
theorem altRunBoundUpTo_of_halfCheck {B : ℕ → ℕ} {D : ℕ}
    (hc : ∀ d ≤ D, 1 ≤ d → halfCheck d (B d + 1) = true) : AltRunBoundUpTo B D := by
  intro x ℓ hw hb d L hdD hrun hne
  rcases Nat.eq_zero_or_pos d with rfl | hd
  · exact absurd (edge_not_alt x ℓ hw hb) hne
  by_contra hL
  push_neg at hL
  set c := ℓ + d with hc'
  obtain ⟨S, hS1, hS2, hS⟩ := exists_code x c d hd (fun j hj => hw j (by omega))
    (by rw [show c - d = ℓ by omega]; exact hb)
  set φ : ℕ := if evolve x 0 c then 0 else 1
  have hφ : φ = 0 ∨ φ = 1 := by simp only [φ]; split <;> simp
  have hdie := halfDiesBy_of_halfCheck (hc d hdD hd) hd hS1 hS2 φ hφ
  have hcol := col_eq_altBit_of_alt x c L hrun hne
  exact altRun_lt_of_halfDiesBy x c S φ (B d + 1) hS hdie
    (fun t ht => hcol t (by omega))

/-! ## The one-sided target -/

/-- **The one-sided period-2 target.** Every half-line word (a code `S ≥ 1`, i.e. a finite row
segment whose far-left cell is black), fed with an alternating boundary of either phase, eventually
fails the check \"black boundary ⇒ black neighbour\".  It mentions no cell to the right of the
column. -/
def PeriodTwoHalfLineDies : Prop :=
  ∀ S : ℕ, 0 < S → ∀ φ : ℕ, φ = 0 ∨ φ = 1 → ∃ T, halfDiesBy S φ T = true

/-- **The one-sided target implies the period-2 rung** `LeftWhiteAperiodic 2`. -/
theorem leftWhiteAperiodic_two_of_halfLineDies (h : PeriodTwoHalfLineDies) :
    LeftWhiteAperiodic 2 := by
  rw [leftWhiteAperiodic_iff_from_start]
  rintro x hx c hper
  -- the constant case is the proved period-1 case
  by_cases hconst : evolve x 1 c = evolve x 0 c
  · refine leftWhiteAperiodic_one x hx c 0 fun t _ => ?_
    induction t using Nat.strong_induction_on with
    | _ t ih =>
      match t, ih with
      | 0, _ => exact hconst
      | 1, _ => rw [hper 0 (by omega)]; exact hconst.symm
      | s + 2, ih =>
        rw [hper (s + 1) (by omega), ih (s + 1) (by omega) (by omega), ih s (by omega) (by omega)]
  -- the alternating case: move to a row of the stack whose edge lies strictly left of `c`
  obtain ⟨ℓ, hw, hb⟩ := hx
  set M : ℕ := 2 * ((ℓ - c).toNat + 1) with hM
  set y := evolve x M
  have hyw : ∀ j, j < ℓ - M → y j = false := fun j hj => evolve_white_left x ℓ hw M j hj
  have hyb : y (ℓ - M) = true := evolve_left_edge x ℓ hw hb M
  set d : ℕ := (c - (ℓ - M)).toNat with hd
  have hd1 : 1 ≤ d := by omega
  have hcd : c - d = ℓ - M := by omega
  have hyper : ∀ t, evolve y (t + 2) c = evolve y t c := fun t => by
    simp only [y]; rw [evolve_evolve, evolve_evolve, show M + (t + 2) = (M + t) + 2 by ring]
    exact hper (M + t) (by omega)
  have hyne : evolve y 1 c ≠ evolve y 0 c := by
    simp only [y]; rw [evolve_evolve, evolve_zero]
    -- `M` is even, so the values at `M + 1` and `M` are those at `1` and `0`
    have hev : ∀ k : ℕ, evolve x (2 * k) c = evolve x 0 c ∧
        evolve x (2 * k + 1) c = evolve x 1 c := by
      intro k
      induction k with
      | zero => simp
      | succ k ih =>
        refine ⟨?_, ?_⟩
        · rw [show 2 * (k + 1) = 2 * k + 2 by ring, hper _ (by omega), ih.1]
        · rw [show 2 * (k + 1) + 1 = (2 * k + 1) + 2 by ring, hper _ (by omega), ih.2]
    rw [show M + 1 = 2 * ((ℓ - c).toNat + 1) + 1 by omega, (hev _).2, hM, (hev _).1]
    exact hconst
  obtain ⟨S, hS1, _, hS⟩ := exists_code y c d hd1 (fun j hj => hyw j (by omega))
    (by rw [hcd]; exact hyb)
  set φ : ℕ := if evolve y 0 c then 0 else 1
  have hφ : φ = 0 ∨ φ = 1 := by simp only [φ]; split <;> simp
  obtain ⟨T, hT⟩ := h S (lt_of_lt_of_le (Nat.two_pow_pos _) hS1) φ hφ
  have hcol := col_eq_altBit_of_alt y c T (fun t _ => hyper t) hyne
  exact altRun_lt_of_halfDiesBy y c S φ T hS hT hcol

end GLM.Rule30
