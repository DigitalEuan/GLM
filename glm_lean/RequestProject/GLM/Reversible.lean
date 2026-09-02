/-
# Reversible bit dynamics: the read channel, the gates, and the kinks

Part V of the unification blueprint asks for three things, and the Python
module `glm_universal/reasoning/reversible.py` measures all three at width 24.
This file proves them, at every width, so that the measurement is a check on
the code rather than the evidence for the claim.

**The read channel.**  Counting in binary disturbs many bits at once at every
power-of-two boundary; the binary reflected Gray code disturbs exactly one bit
per step.

* `gray_step` — consecutive Gray codes differ by a *single* bit: their `xor`
  is a power of two.
* `gray_single_bit` — the same statement bit by bit.
* `sum_flipCount`, `binaryCycleFlips_eq`, `grayCycleFlips_eq` — over one full
  cycle of a `w`-bit counter, binary counting flips `2^(w+1) - 2` bits and
  Gray counting flips `2^w`.
* `gray_not_exactly_half` and `gray_two_mul_eq` — so the blueprint's claim
  that Gray "dissipates exactly half" is *false at every finite width*, and
  the sharp statement is `2 * grayCycleFlips w = binaryCycleFlips w + 2`:
  Gray costs one step more than half, and exactly half only in the limit.

**The gates.**  `toffoli` and `fredkin` on a three-bit block are involutions
and bijections (`toffoli_involutive`, `fredkin_involutive`,
`toffoli_bijective`, `fredkin_bijective`), so nothing is erased and nothing is
dissipated.  Their *composition* is not an involution
(`round_not_involutive`): undoing a run of rounds means running the inverse
round, which is what the Python cycle does.

**The kinks.**  A circular string's kink count -- the number of places where
adjacent coordinates differ -- is the blueprint's topological invariant.

* `kinks_rotate` — it is invariant under every rotation.
* `kinks_even` — it is always even.
* `kinks_flip_le` and `le_kinks_flip` — flipping one coordinate moves it by at
  most 2, and by an even amount, so the change is in `{-2, 0, +2}`.  The
  blueprint's "exactly ±2" is therefore too strong: `kinks_flip_eq_of_ne`
  exhibits the case where a flip changes nothing at all.
-/

import Mathlib

namespace GLM.Reversible

/-! ## 1.  The binary reflected Gray code -/

/-- The binary reflected Gray code of `n`. -/
def gray (n : ℕ) : ℕ := n ^^^ (n >>> 1)

theorem two_mul_xor (a b : ℕ) : 2 * a ^^^ 2 * b = 2 * (a ^^^ b) := by
  have h : ∀ x : ℕ, 2 * x = x <<< 1 := by
    intro x; simp [Nat.shiftLeft_eq]; ring
  simp [h, Nat.shiftLeft_xor_distrib]

/-- Consecutive integers differ in a *block* of low bits: `n xor (n+1)` is
always of the form `2 ^ k - 1` with `k > 0`.  This is what makes binary
counting expensive at the boundaries. -/
theorem xor_succ_allones (n : ℕ) : ∃ k, 0 < k ∧ n ^^^ (n + 1) = 2 ^ k - 1 := by
  induction n using Nat.strong_induction_on with
  | _ n ih =>
    rcases Nat.even_or_odd n with he | ho
    · refine ⟨1, one_pos, ?_⟩
      have h1 : n ^^^ 1 = n + 1 := Nat.xor_one_of_even he
      calc n ^^^ (n + 1) = n ^^^ (n ^^^ 1) := by rw [h1]
        _ = 1 := by rw [← Nat.xor_assoc, Nat.xor_self, Nat.zero_xor]
        _ = 2 ^ 1 - 1 := by norm_num
    · obtain ⟨m, rfl⟩ := ho
      obtain ⟨k, hk, hm⟩ := ih m (by omega)
      refine ⟨k + 1, by omega, ?_⟩
      have he2 : Even (2 * m) := ⟨m, by ring⟩
      have h1 : 2 * m ^^^ 1 = 2 * m + 1 := Nat.xor_one_of_even he2
      have h2 : (2 * m + 1) + 1 = 2 * (m + 1) := by ring
      have hev : Even (2 * (m ^^^ (m + 1))) := ⟨m ^^^ (m + 1), by ring⟩
      have hpos : 0 < 2 ^ k := by positivity
      calc (2 * m + 1) ^^^ ((2 * m + 1) + 1)
          = (2 * m ^^^ 1) ^^^ (2 * (m + 1)) := by rw [h1, h2]
        _ = 1 ^^^ (2 * m ^^^ 2 * (m + 1)) := by
              rw [Nat.xor_comm (2 * m) 1, Nat.xor_assoc]
        _ = 1 ^^^ (2 * (m ^^^ (m + 1))) := by rw [two_mul_xor]
        _ = 2 * (m ^^^ (m + 1)) + 1 := by
              rw [Nat.xor_comm]; exact Nat.xor_one_of_even hev
        _ = 2 ^ (k + 1) - 1 := by
              rw [hm]
              have h3 : (2 : ℕ) ^ (k + 1) = 2 * 2 ^ k := by ring
              omega

theorem allones_xor_half (j : ℕ) :
    (2 ^ (j + 1) - 1) ^^^ (2 ^ j - 1) = 2 ^ j := by
  apply Nat.eq_of_testBit_eq
  intro i
  simp only [Nat.testBit_xor, Nat.testBit_two_pow_sub_one, Nat.testBit_two_pow]
  rcases lt_trichotomy i j with h | h | h
  · simp [h, Nat.lt_succ_of_lt h, Nat.ne_of_gt h]
  · subst h; simp
  · have h1 : ¬ i < j := by omega
    have h2 : ¬ i < j + 1 := by omega
    simp [h1, h2, Nat.ne_of_lt h]

/-- **One bit per step.**  Consecutive Gray codes differ by a power of two,
that is, in exactly one bit position. -/
theorem gray_step (n : ℕ) : ∃ i, gray n ^^^ gray (n + 1) = 2 ^ i := by
  obtain ⟨k, hk, hX⟩ := xor_succ_allones n
  obtain ⟨j, rfl⟩ : ∃ j, k = j + 1 := ⟨k - 1, by omega⟩
  refine ⟨j, ?_⟩
  have hshift : (n >>> 1) ^^^ ((n + 1) >>> 1) = (n ^^^ (n + 1)) >>> 1 :=
    (Nat.shiftRight_xor_distrib ..).symm
  have hhalf : (2 ^ (j + 1) - 1) >>> 1 = 2 ^ j - 1 := by
    rw [Nat.shiftRight_eq_div_pow]
    have : (2 : ℕ) ^ (j + 1) = 2 * 2 ^ j := by ring
    omega
  calc gray n ^^^ gray (n + 1)
      = (n ^^^ (n + 1)) ^^^ ((n >>> 1) ^^^ ((n + 1) >>> 1)) := by
        unfold gray
        rw [Nat.xor_assoc, ← Nat.xor_assoc (n >>> 1),
            Nat.xor_comm (n >>> 1) (n + 1), Nat.xor_assoc, ← Nat.xor_assoc]
    _ = (n ^^^ (n + 1)) ^^^ ((n ^^^ (n + 1)) >>> 1) := by rw [hshift]
    _ = (2 ^ (j + 1) - 1) ^^^ ((2 ^ (j + 1) - 1) >>> 1) := by rw [hX]
    _ = 2 ^ j := by rw [hhalf, allones_xor_half]

/-- The same statement bit by bit: exactly one position changes. -/
theorem gray_single_bit (n : ℕ) :
    ∃ i, ∀ j, ((gray n).testBit j ≠ (gray (n + 1)).testBit j) ↔ j = i := by
  obtain ⟨i, hi⟩ := gray_step n
  refine ⟨i, fun j => ?_⟩
  have h : ((gray n).testBit j ^^ (gray (n + 1)).testBit j) = (2 ^ i).testBit j := by
    rw [← Nat.testBit_xor, hi]
  rw [Nat.testBit_two_pow] at h
  cases hx : (gray n).testBit j <;> cases hy : (gray (n + 1)).testBit j <;>
    simp [hx, hy] at h ⊢ <;> omega

/-! ## 2.  What a full cycle of the counter costs -/

/-- How many bits change when a binary counter steps from `n` to `n + 1`. -/
def flipCount (n : ℕ) : ℕ :=
  if n % 2 = 0 then 1 else flipCount (n / 2) + 1
termination_by n
decreasing_by omega

theorem flipCount_zero : flipCount 0 = 1 := by rw [flipCount]; norm_num

@[simp] theorem flipCount_even (m : ℕ) : flipCount (2 * m) = 1 := by
  rw [flipCount]; simp [Nat.mul_mod_right]

@[simp] theorem flipCount_odd (m : ℕ) :
    flipCount (2 * m + 1) = flipCount m + 1 := by
  rw [flipCount]
  have h1 : (2 * m + 1) % 2 = 1 := by omega
  have h2 : (2 * m + 1) / 2 = m := by omega
  simp [h1, h2]

theorem sum_range_two_mul (f : ℕ → ℕ) :
    ∀ N, ∑ n ∈ Finset.range (2 * N), f n
        = ∑ m ∈ Finset.range N, (f (2 * m) + f (2 * m + 1))
  | 0 => by simp
  | N + 1 => by
      have h : 2 * (N + 1) = (2 * N + 1) + 1 := by ring
      rw [h, Finset.sum_range_succ, Finset.sum_range_succ,
          Finset.sum_range_succ, sum_range_two_mul f N]
      ring_nf

theorem sum_flipCount (w : ℕ) :
    ∑ n ∈ Finset.range (2 ^ w), flipCount n = 2 ^ (w + 1) - 1 := by
  induction w with
  | zero => simp [flipCount_zero]
  | succ w ih =>
      have h : (2 : ℕ) ^ (w + 1) = 2 * 2 ^ w := by ring
      rw [h, sum_range_two_mul]
      simp only [flipCount_even, flipCount_odd, Finset.sum_add_distrib,
        Finset.sum_const, Finset.card_range, smul_eq_mul, mul_one]
      rw [ih]
      have hpos : 0 < 2 ^ w := by positivity
      have h4 : (2 : ℕ) ^ (w + 1 + 1) = 4 * 2 ^ w := by ring
      have h3 : (2 : ℕ) ^ (w + 1) = 2 * 2 ^ w := by ring
      omega

/-- The last step of the cycle is the worst one: every bit rolls over. -/
theorem flipCount_allones (w : ℕ) : flipCount (2 ^ w - 1) = w + 1 := by
  induction w with
  | zero => simpa using flipCount_zero
  | succ w ih =>
      have hpos : 0 < 2 ^ w := by positivity
      have h : 2 ^ (w + 1) - 1 = 2 * (2 ^ w - 1) + 1 := by
        have : (2 : ℕ) ^ (w + 1) = 2 * 2 ^ w := by ring
        omega
      rw [h, flipCount_odd, ih]

/-- The bits a `w`-bit binary counter flips over one full cycle: the `2^w - 1`
increments, plus the wrap-around from all ones back to zero, which flips all
`w` bits. -/
def binaryCycleFlips (w : ℕ) : ℕ :=
  (∑ n ∈ Finset.range (2 ^ w - 1), flipCount n) + w

/-- The bits a `w`-bit Gray counter flips over one full cycle: one per step,
by `gray_step`, over `2^w` steps. -/
def grayCycleFlips (w : ℕ) : ℕ := 2 ^ w

theorem binaryCycleFlips_eq (w : ℕ) : binaryCycleFlips w = 2 ^ (w + 1) - 2 := by
  have hpos : 0 < 2 ^ w := by positivity
  have hsplit : ∑ n ∈ Finset.range (2 ^ w), flipCount n
      = (∑ n ∈ Finset.range (2 ^ w - 1), flipCount n) + flipCount (2 ^ w - 1) := by
    have h : 2 ^ w = (2 ^ w - 1) + 1 := by omega
    rw [h, Finset.sum_range_succ]
    simp
  have htotal := sum_flipCount w
  have hlast := flipCount_allones w
  have hpow : (2 : ℕ) ^ (w + 1) = 2 * 2 ^ w := by ring
  unfold binaryCycleFlips
  omega

@[simp] theorem grayCycleFlips_eq (w : ℕ) : grayCycleFlips w = 2 ^ w := rfl

/-- **The sharp statement.**  Gray counting costs one step more than half of
binary counting: `2 * gray = binary + 2`. -/
theorem gray_two_mul_eq (w : ℕ) :
    2 * grayCycleFlips w = binaryCycleFlips w + 2 := by
  rw [binaryCycleFlips_eq, grayCycleFlips_eq]
  have hpos : 0 < 2 ^ w := by positivity
  have hpow : (2 : ℕ) ^ (w + 1) = 2 * 2 ^ w := by ring
  omega

/-- **So "exactly half" is false at every finite width.** -/
theorem gray_not_exactly_half (w : ℕ) :
    2 * grayCycleFlips w ≠ binaryCycleFlips w := by
  rw [gray_two_mul_eq]; omega

/-! ## 3.  The reversible gates -/

/-- Toffoli (CCNOT) on a three-bit block. -/
def toffoli : Bool × Bool × Bool → Bool × Bool × Bool
  | (a, b, c) => (a, b, xor c (a && b))

/-- Fredkin (CSWAP) on a three-bit block. -/
def fredkin : Bool × Bool × Bool → Bool × Bool × Bool
  | (a, b, c) => if a then (a, c, b) else (a, b, c)

theorem toffoli_involutive : Function.Involutive toffoli := by
  intro x; revert x; decide

theorem fredkin_involutive : Function.Involutive fredkin := by
  intro x; revert x; decide

theorem toffoli_bijective : Function.Bijective toffoli :=
  toffoli_involutive.bijective

theorem fredkin_bijective : Function.Bijective fredkin :=
  fredkin_involutive.bijective

/-- One forward round: Toffoli then Fredkin. -/
def round (x : Bool × Bool × Bool) : Bool × Bool × Bool := fredkin (toffoli x)

/-- Its inverse: Fredkin then Toffoli, each gate being its own inverse. -/
def roundInv (x : Bool × Bool × Bool) : Bool × Bool × Bool := toffoli (fredkin x)

theorem roundInv_round : ∀ x, roundInv (round x) = x := by decide

theorem round_roundInv : ∀ x, round (roundInv x) = x := by decide

/-- The composition is *not* an involution, so a run of rounds must be undone
by the inverse round rather than by repeating itself. -/
theorem round_not_involutive : ¬ Function.Involutive round := by
  intro h
  have := h (true, true, false)
  revert this
  decide

/-- In fact the round has order three. -/
theorem round_cubed : ∀ x, round (round (round x)) = x := by decide

/-! ## 4.  Kinks: information as a topological defect -/

variable {n : ℕ} [NeZero n]

/-- The number of places where a circular string changes value. -/
def kinks (v : Fin n → Bool) : ℕ :=
  (Finset.univ.filter fun i : Fin n => v i ≠ v (i + 1)).card

/-- **The invariant.**  Rotating the string does not change its kink count. -/
theorem kinks_rotate (v : Fin n → Bool) (k : Fin n) :
    kinks (fun i => v (i + k)) = kinks v := by
  unfold kinks
  apply Finset.card_equiv (Equiv.addRight k)
  intro a
  have h : a + 1 + k = a + k + 1 := add_right_comm a 1 k
  simp [Equiv.addRight, h]

/-- **The kink count is always even**: kinks come in pairs, which is why a
flip can only move it by an even amount. -/
theorem kinks_even (v : Fin n → Bool) : Even (kinks v) := by
  have hcast : ((kinks v : ℕ) : ZMod 2) = 0 := by
    unfold kinks
    rw [Finset.card_filter]
    push_cast
    have h : ∀ i : Fin n, (if v i ≠ v (i + 1) then (1 : ZMod 2) else 0)
        = (if v i then (1 : ZMod 2) else 0)
          + (if v (i + 1) then (1 : ZMod 2) else 0) := by
      intro i
      cases hv : v i <;> cases hw : v (i + 1) <;> rfl
    rw [Finset.sum_congr rfl (fun i _ => h i), Finset.sum_add_distrib]
    have hre : ∑ i : Fin n, (if v (i + 1) then (1 : ZMod 2) else 0)
        = ∑ i : Fin n, (if v i then (1 : ZMod 2) else 0) :=
      Fintype.sum_equiv (Equiv.addRight (1 : Fin n)) _ _ (fun _ => rfl)
    rw [hre]
    have hsq : ∀ x : ZMod 2, x + x = 0 := by decide
    exact hsq _
  exact even_iff_two_dvd.mpr (Fin.natCast_eq_zero.mp hcast)

/-- Flipping a single coordinate: the soliton injection. -/
def flipAt (v : Fin n → Bool) (j : Fin n) : Fin n → Bool :=
  Function.update v j (!v j)

omit [NeZero n] in
@[simp] theorem flipAt_flipAt (v : Fin n → Bool) (j : Fin n) :
    flipAt (flipAt v j) j = v := by
  funext i
  by_cases h : i = j
  · subst h; simp [flipAt]
  · simp [flipAt, Function.update_of_ne h]

theorem kinks_flip_le (v : Fin n → Bool) (j : Fin n) :
    kinks (flipAt v j) ≤ kinks v + 2 := by
  classical
  set A := Finset.univ.filter fun i : Fin n =>
    flipAt v j i ≠ flipAt v j (i + 1) with hA
  set B := Finset.univ.filter fun i : Fin n => v i ≠ v (i + 1) with hB
  have hsub : A \ B ⊆ ({j - 1, j} : Finset (Fin n)) := by
    intro i hi
    simp only [Finset.mem_sdiff, hA, hB, Finset.mem_filter, Finset.mem_univ,
      true_and] at hi
    by_contra hc
    simp only [Finset.mem_insert, Finset.mem_singleton, not_or] at hc
    obtain ⟨h1, h2⟩ := hc
    have hne : i + 1 ≠ j := by
      intro h; apply h1; rw [← h]; simp
    have e1 : flipAt v j i = v i := by simp [flipAt, Function.update_of_ne h2]
    have e2 : flipAt v j (i + 1) = v (i + 1) := by
      simp [flipAt, Function.update_of_ne hne]
    exact hi.2 (e1 ▸ e2 ▸ hi.1)
  have hcard : (A \ B).card ≤ 2 :=
    le_trans (Finset.card_le_card hsub)
      (le_trans (Finset.card_insert_le _ _) (by simp))
  calc kinks (flipAt v j) = A.card := rfl
    _ ≤ (A ∩ B).card + (A \ B).card := by rw [Finset.card_inter_add_card_sdiff]
    _ ≤ B.card + 2 :=
        Nat.add_le_add (Finset.card_le_card Finset.inter_subset_right) hcard
    _ = kinks v + 2 := rfl

theorem le_kinks_flip (v : Fin n → Bool) (j : Fin n) :
    kinks v ≤ kinks (flipAt v j) + 2 := by
  have := kinks_flip_le (flipAt v j) j
  rwa [flipAt_flipAt] at this

/-- A flip that does destroy a pair of kinks: on `0100`, flipping the set
coordinate leaves the constant string, with no kinks at all. -/
theorem kinks_flip_drops_two :
    kinks (flipAt (fun i : Fin 4 => decide (i.val = 1)) 1) + 2
      = kinks (fun i : Fin 4 => decide (i.val = 1)) := by
  decide

/-- **"Exactly ±2" is too strong.**  On `0001`, flipping coordinate `0`
destroys one kink and creates another, so the count does not move: the change
a single flip makes is in `{-2, 0, +2}`, not in `{-2, +2}`. -/
theorem kinks_flip_unchanged :
    kinks (flipAt (fun i : Fin 4 => decide (i.val = 3)) 0)
      = kinks (fun i : Fin 4 => decide (i.val = 3)) := by
  decide

end GLM.Reversible
