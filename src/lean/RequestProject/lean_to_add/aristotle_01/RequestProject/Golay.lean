import RequestProject.GrayCode

/-!
# The extended binary Golay code `[24,12,8]` — definitions and linear algebra

We take the generator matrix `G = [I₁₂ | B]` with the parity block `B` used by
the substrate implementation (`GolayCodeEngine.B` in `ubp_unified_v5.py`) and
encode 24-bit words as natural numbers (bit `j` = coordinate `j`; coordinates
`0..11` are the information positions).

This file contains the definitions, `GF(2)`-linearity and elementary Hamming
weight arithmetic.  The exhaustive verification that this really is the Golay
code (weight enumerator, minimum distance 8) is in `RequestProject.GolayWeights`.
-/

namespace LatticeShortcut

/-- Rows of the generator matrix `G = [I₁₂ | B]`, as 24-bit masks. -/
def golayRows : List ℕ :=
  [16769025, 4681730, 10727428, 13750280, 6877200, 11825184,
   14299200, 15536256, 7770368, 3887616, 1946624, 9361408]

/-- Auxiliary XOR-fold: `encAux fuel j m` XORs the rows `j, j+1, …` selected by
the bits of `m`. -/
def encAux : ℕ → ℕ → ℕ → ℕ
  | 0, _, _ => 0
  | fuel + 1, j, m =>
      (if m % 2 = 1 then golayRows.getD j 0 else 0) ^^^ encAux fuel (j + 1) (m / 2)

/-- Systematic encoding of a 12-bit message `m`. -/
def cw (m : ℕ) : ℕ := encAux 12 0 m

/-- Membership in the Golay code. -/
def IsGolay (c : ℕ) : Prop := ∃ m < 4096, cw m = c

instance : DecidablePred IsGolay := fun c => decidable_of_iff _ (by
  simp only [IsGolay]
  exact Iff.rfl)

/-! ### XOR utilities -/

theorem xor4 (x y A B : ℕ) : (x ^^^ y) ^^^ (A ^^^ B) = (x ^^^ A) ^^^ (y ^^^ B) := by
  apply Nat.eq_of_testBit_eq; intro i
  simp only [Nat.testBit_xor]
  cases x.testBit i <;> cases y.testBit i <;> cases A.testBit i <;> cases B.testBit i <;> simp

theorem xor_div_two (a b : ℕ) : (a ^^^ b) / 2 = (a / 2) ^^^ (b / 2) := by
  have h : ((a ^^^ b) >>> 1) = (a >>> 1) ^^^ (b >>> 1) := Nat.shiftRight_xor_distrib
  simpa [Nat.shiftRight_eq_div_pow] using h

/-! ### Elementary facts about the encoder -/

theorem encAux_xor (fuel : ℕ) : ∀ j a b : ℕ,
    encAux fuel j (a ^^^ b) = encAux fuel j a ^^^ encAux fuel j b := by
  induction fuel with
  | zero => intro j a b; simp [encAux]
  | succ f ih =>
    intro j a b
    show (if (a ^^^ b) % 2 = 1 then golayRows.getD j 0 else 0) ^^^
        encAux f (j + 1) ((a ^^^ b) / 2) = _
    rw [xor_div_two, ih (j + 1) (a / 2) (b / 2)]
    show _ = ((if a % 2 = 1 then golayRows.getD j 0 else 0) ^^^ encAux f (j + 1) (a / 2)) ^^^
      ((if b % 2 = 1 then golayRows.getD j 0 else 0) ^^^ encAux f (j + 1) (b / 2))
    rw [xor4]
    congr 1
    rcases Nat.mod_two_eq_zero_or_one a with ha | ha <;>
      rcases Nat.mod_two_eq_zero_or_one b with hb | hb <;>
        simp [ha, hb, Nat.xor_self] <;> omega

/-- The encoder is `GF(2)`-linear. -/
theorem cw_xor (a b : ℕ) : cw (a ^^^ b) = cw a ^^^ cw b := encAux_xor 12 0 a b

theorem row_lt (j : ℕ) : golayRows.getD j 0 < 2 ^ 24 := by
  rcases lt_or_ge j 12 with h | h
  · interval_cases j <;> decide
  · rw [List.getD_eq_default]
    · norm_num
    · simpa [golayRows] using h

theorem encAux_lt (fuel : ℕ) : ∀ j m, encAux fuel j m < 2 ^ 24 := by
  induction fuel with
  | zero => intro j m; simp [encAux]
  | succ f ih =>
    intro j m
    show (if m % 2 = 1 then golayRows.getD j 0 else 0) ^^^ encAux f (j + 1) (m / 2) < 2 ^ 24
    refine Nat.xor_lt_two_pow ?_ (ih (j + 1) (m / 2))
    split
    · exact row_lt j
    · norm_num

theorem cw_lt (m : ℕ) : cw m < 2 ^ 24 := encAux_lt 12 0 m

theorem cw_zero : cw 0 = 0 := by decide

theorem golay_lt {c : ℕ} (hc : IsGolay c) : c < 2 ^ 24 := by
  obtain ⟨m, _, rfl⟩ := hc; exact cw_lt m

theorem golay_zero : IsGolay 0 := ⟨0, by norm_num, cw_zero⟩

/-- The Golay code is closed under XOR. -/
theorem golay_xor_closed {a b : ℕ} (ha : IsGolay a) (hb : IsGolay b) :
    IsGolay (a ^^^ b) := by
  obtain ⟨m₁, hm₁, rfl⟩ := ha
  obtain ⟨m₂, hm₂, rfl⟩ := hb
  exact ⟨m₁ ^^^ m₂, by
      have : m₁ ^^^ m₂ < 2 ^ 12 := Nat.xor_lt_two_pow (by simpa using hm₁) (by simpa using hm₂)
      simpa using this,
    cw_xor m₁ m₂⟩

/-! ### Hamming weight arithmetic -/

/-- Only the zero word has weight `0` (among 24-bit words). -/
theorem pop_eq_zero_iff (n : ℕ) (h : n < 2 ^ 24) : pop n = 0 ↔ n = 0 := by
  constructor
  · intro hp
    have hbits : ∀ i ∈ Finset.range 24, bit n i = 0 :=
      (Finset.sum_eq_zero_iff).1 hp
    apply Nat.eq_of_testBit_eq
    intro i
    rcases lt_or_ge i 24 with hi | hi
    · have := hbits i (Finset.mem_range.2 hi)
      rw [bit_eq_testBit] at this
      cases hb : n.testBit i
      · simp
      · rw [hb] at this; simp at this
    · have hlt : n < 2 ^ i := lt_of_lt_of_le h (Nat.pow_le_pow_right (by norm_num) hi)
      simp [Nat.testBit_eq_false_of_lt hlt]
  · rintro rfl
    simp [pop, bit]

/-- Inclusion–exclusion: `|a Δ b| + 2|a ∩ b| = |a| + |b|`. -/
theorem pop_xor_add (a b : ℕ) :
    pop (a ^^^ b) + 2 * pop (a &&& b) = pop a + pop b := by
  unfold pop
  rw [Finset.mul_sum, ← Finset.sum_add_distrib, ← Finset.sum_add_distrib]
  refine Finset.sum_congr rfl fun i _ => ?_
  simp only [bit_eq_testBit, Nat.testBit_xor, Nat.testBit_and]
  cases a.testBit i <;> cases b.testBit i <;> norm_num

theorem pop_and_le (a b : ℕ) : pop (a &&& b) ≤ pop a := by
  unfold pop
  refine Finset.sum_le_sum fun i _ => ?_
  simp only [bit_eq_testBit, Nat.testBit_and]
  cases a.testBit i <;> cases b.testBit i <;> norm_num

end LatticeShortcut
