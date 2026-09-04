/-
# The lattice shortcut's jump norm: an `O(1)` formula, and what it does not say

**Retrieved from the archive.**  `source_material/GLM-main.zip/leech_lattice` is
the "Leech lattice shortcut": a method for mapping integers into `Λ₂₄` quickly,
whose first stage is a 24-bit Gray encoding and whose published directory
tabulates a *jump norm* `d²` for each transition of a walk.  The first salvage
pass recorded the folder as "an implementation"; read again, its Lean
development carries three exact statements about that first stage which the
current development does not have, and which are worth having because the
runtime walks integer neighbourhoods constantly.

`Reversible.lean` already has the Gray map `gray n = n ^^^ (n >>> 1)` and its
one-bit-per-step property.  This file adds the *metric* layer on top of it:

* `normSq_eq_d2` — the 24-dimensional jump vector `Δv i = bit (gray b) i −
  bit (gray a) i` has squared norm exactly the Hamming distance of the two
  encodings, so "`d²`" is a distance and not a separate quantity;
* `gray_xor` and `d2_eq_pop_gray_xor` — **the shortcut formula.**  Gray coding
  is `GF(2)`-linear, so `d²(a,b) = pop (gray (a ^^^ b))`: the jump norm of a
  transition is a handful of machine instructions on `a ^^^ b` and never
  requires walking the integers between `a` and `b`;
* `d2_succ` — adjacent integers are always at `d² = 1`.

The last one is a **correction**, and it is why the file is worth its length.
The published directory tabulates `d² ∈ {8, 10, 12, 14}` for *consecutive*
integers of its "deep interfacial sequence"; `d2_interfacial_all_one` evaluates
the documented pipeline on that very walk and gets `1` at every step.  The
tabulated values are real output of the generator, but they measure the
distance between the *factorisations* of `n` and `n+1`, which is a different
map from the one the write-up documents.

The same holds for the directory's "100 % even quantisation".  `d2_mod_two`
proves the exact parity law `d² ≡ a + b (mod 2)`: on this layer `d²` is even
exactly when `a` and `b` have the same parity, so a walk on odd numbers — a
walk on primes, say — has even `d²` at every step for trivial reasons
(`d2_even_of_odd`), with no lattice input at all, and `exists_odd_d2` exhibits
an odd `d²`.  Evenness is imposed by the Golay snap further down the pipeline,
not by the encoding.

The archive's file is `leech_lattice/RequestProject/GrayCode.lean` (the same
file appears in `light/aristotle_01`); the statements are retrieved here on the
`gray` of `Reversible.lean`.
-/
import Mathlib
import RequestProject.GLM.Reversible

namespace GLM.GrayJump

open GLM.Reversible (gray)

/-- `bit n i` is the `i`-th binary digit of `n`. -/
def bit (n i : ℕ) : ℕ := n / 2 ^ i % 2

/-- Hamming weight of the low 24 bits. -/
def pop (n : ℕ) : ℕ := ∑ i ∈ Finset.range 24, bit n i

/-- The 24-dimensional jump vector `Δv = v b − v a` of a transition `a → b`. -/
def jumpVec (a b : ℕ) (i : ℕ) : ℤ := (bit (gray b) i : ℤ) - (bit (gray a) i : ℤ)

/-- The squared norm `d² = ‖Δv‖²` of a jump vector. -/
def jumpNormSq (a b : ℕ) : ℤ := ∑ i ∈ Finset.range 24, (jumpVec a b i) ^ 2

/-- The Hamming distance of the two 24-bit Gray encodings. -/
def d2 (a b : ℕ) : ℕ := pop (gray a ^^^ gray b)

/-! ## 1. Bits -/

theorem bit_eq_testBit (n i : ℕ) : bit n i = if n.testBit i then 1 else 0 := by
  rw [bit, Nat.testBit_eq_decide_div_mod_eq]
  rcases Nat.mod_two_eq_zero_or_one (n / 2 ^ i) with h | h <;> simp [h]

theorem bit_lt_two (n i : ℕ) : bit n i < 2 := Nat.mod_lt _ (by norm_num)

theorem bit_xor (a b i : ℕ) : bit (a ^^^ b) i = (bit a i) ^^^ (bit b i) := by
  simp only [bit_eq_testBit, Nat.testBit_xor]
  cases a.testBit i <;> cases b.testBit i <;> simp

theorem bit_two_pow (t i : ℕ) : bit (2 ^ t) i = if t = i then 1 else 0 := by
  simp [bit_eq_testBit, Nat.testBit_two_pow]

theorem pop_two_pow (t : ℕ) (h : t < 24) : pop (2 ^ t) = 1 := by
  simp [pop, bit_two_pow, Finset.sum_ite_eq, Finset.mem_range, h]

/-! ## 2. The jump norm is the Hamming distance -/

/-- The squared norm of the 24-dimensional jump vector is the Hamming distance
of the two Gray encodings. -/
theorem normSq_eq_d2 (a b : ℕ) : jumpNormSq a b = (d2 a b : ℤ) := by
  unfold jumpNormSq d2 pop jumpVec
  push_cast
  refine Finset.sum_congr rfl fun i _ => ?_
  simp only [bit_eq_testBit, Nat.testBit_xor]
  cases (gray a).testBit i <;> cases (gray b).testBit i <;> norm_num

/-! ## 3. The shortcut formula -/

/-- Gray coding is `GF(2)`-linear. -/
theorem gray_xor (a b : ℕ) : gray a ^^^ gray b = gray (a ^^^ b) := by
  apply Nat.eq_of_testBit_eq
  intro i
  simp only [GLM.Reversible.gray, Nat.testBit_xor, Nat.testBit_shiftRight]
  cases a.testBit i <;> cases b.testBit i <;> cases a.testBit (1 + i) <;>
    cases b.testBit (1 + i) <;> simp

/-- **The `O(1)` shortcut formula.**  The jump norm between two states depends
only on `a ^^^ b`, so it is evaluated with a handful of machine instructions and
never requires traversing the integers between `a` and `b`. -/
theorem d2_eq_pop_gray_xor (a b : ℕ) : d2 a b = pop (gray (a ^^^ b)) := by
  rw [d2, gray_xor]

/-! ## 4. Adjacent transitions -/

theorem gray_two_pow_sub_one (t : ℕ) : gray (2 ^ (t + 1) - 1) = 2 ^ t := by
  apply Nat.eq_of_testBit_eq
  intro i
  simp only [GLM.Reversible.gray, Nat.testBit_xor, Nat.testBit_shiftRight,
    Nat.testBit_two_pow_sub_one, Nat.testBit_two_pow]
  rcases lt_trichotomy i t with h | h | h
  · simp [Nat.lt_succ_of_lt h, show 1 + i < t + 1 by omega, show ¬ (t = i) by omega]
  · subst h; simp [show ¬ (1 + i < i + 1) by omega]
  · simp [show ¬ (i < t + 1) by omega, show ¬ (1 + i < t + 1) by omega,
      show ¬ (t = i) by omega]

/-- **Adjacent integers are at Hamming distance exactly `1`.**  The step from
`n` to `n+1` is never a `d² ∈ {8, 10, 12, 14}` "geodesic jump" on this layer;
that is the defining property of a Gray code. -/
theorem d2_succ (n : ℕ) (h : n + 1 < 2 ^ 24) : d2 n (n + 1) = 1 := by
  obtain ⟨k, hk, hxor⟩ := GLM.Reversible.xor_succ_allones n
  obtain ⟨t, rfl⟩ : ∃ t, k = t + 1 := ⟨k - 1, by omega⟩
  have hlt : n ^^^ (n + 1) < 2 ^ 24 := Nat.xor_lt_two_pow (by omega) h
  have htlt : t < 24 := by
    by_contra hc
    push_neg at hc
    have h1 : (2 : ℕ) ^ 25 ≤ 2 ^ (t + 1) := Nat.pow_le_pow_right (by norm_num) (by omega)
    have h2 : (2 : ℕ) ^ 24 + 1 ≤ 2 ^ 25 := by norm_num
    omega
  rw [d2_eq_pop_gray_xor, hxor, gray_two_pow_sub_one, pop_two_pow t htlt]

/-! ## 5. The parity law -/

theorem bit_gray_cast (n i : ℕ) :
    (bit (gray n) i : ZMod 2) = (bit n i : ZMod 2) + (bit n (i + 1) : ZMod 2) := by
  simp only [GLM.Reversible.gray, bit_eq_testBit, Nat.testBit_xor, Nat.testBit_shiftRight]
  rw [show 1 + i = i + 1 by omega]
  cases n.testBit i <;> cases n.testBit (i + 1) <;> (norm_num; try decide)

theorem pop_gray_cast (n : ℕ) :
    (pop (gray n) : ZMod 2) = (bit n 0 : ZMod 2) + (bit n 24 : ZMod 2) := by
  unfold pop
  push_cast
  simp only [bit_gray_cast]
  rw [Finset.sum_add_distrib,
    Finset.sum_range_succ' (fun i => ((bit n i : ℕ) : ZMod 2)) 23,
    Finset.sum_range_succ (fun i => ((bit n (i + 1) : ℕ) : ZMod 2)) 23]
  have hself : ∀ x : ZMod 2, x + x = 0 := by decide
  rw [show ((∑ i ∈ Finset.range 23, ((bit n (i + 1) : ℕ) : ZMod 2)) + (bit n 0 : ℕ)) +
        ((∑ i ∈ Finset.range 23, ((bit n (i + 1) : ℕ) : ZMod 2)) + (bit n (23 + 1) : ℕ))
      = ((∑ i ∈ Finset.range 23, ((bit n (i + 1) : ℕ) : ZMod 2)) +
          (∑ i ∈ Finset.range 23, ((bit n (i + 1) : ℕ) : ZMod 2))) +
        ((bit n 0 : ℕ) + (bit n 24 : ℕ)) by ring_nf]
  rw [hself]
  ring

/-- `pop (gray n) ≡ n (mod 2)` for 24-bit `n`: the Gray weight is a telescoping
sum of adjacent bits, so only the lowest bit survives mod 2. -/
theorem pop_gray_mod_two (n : ℕ) (h : n < 2 ^ 24) : pop (gray n) % 2 = n % 2 := by
  have h24 : bit n 24 = 0 := by
    have hd : n / 2 ^ 24 = 0 := Nat.div_eq_of_lt h
    unfold bit
    rw [hd]
  have h0 : bit n 0 = n % 2 := by simp [bit]
  have hc := pop_gray_cast n
  rw [h24, h0] at hc
  simp only [Nat.cast_zero, add_zero] at hc
  have h2 := (ZMod.natCast_eq_natCast_iff' (pop (gray n)) (n % 2) 2).1 hc
  simpa [Nat.mod_mod_of_dvd] using h2

theorem xor_mod_two (a b : ℕ) : (a ^^^ b) % 2 = (a + b) % 2 := by
  have h := Nat.testBit_xor a b 0
  simp only [Nat.testBit_eq_decide_div_mod_eq, pow_zero, Nat.div_one] at h
  rcases Nat.mod_two_eq_zero_or_one a with ha | ha <;>
    rcases Nat.mod_two_eq_zero_or_one b with hb | hb <;> simp [ha, hb] at h ⊢

/-- **The exact parity law of the raw Gray layer.**  `d²(a,b)` is even exactly
when `a` and `b` have the same parity, so evenness is not a feature of the
encoding stage. -/
theorem d2_mod_two (a b : ℕ) (ha : a < 2 ^ 24) (hb : b < 2 ^ 24) :
    d2 a b % 2 = (a + b) % 2 := by
  rw [d2_eq_pop_gray_xor, pop_gray_mod_two _ (Nat.xor_lt_two_pow ha hb), xor_mod_two]

theorem d2_even_iff (a b : ℕ) (ha : a < 2 ^ 24) (hb : b < 2 ^ 24) :
    Even (d2 a b) ↔ a % 2 = b % 2 := by
  rw [Nat.even_iff, d2_mod_two a b ha hb]
  omega

/-- A walk whose states are all odd — a walk on primes above 2, for instance —
has even `d²` at every step for parity reasons alone, with no lattice input. -/
theorem d2_even_of_odd (a b : ℕ) (ha : a < 2 ^ 24) (hb : b < 2 ^ 24)
    (ha2 : a % 2 = 1) (hb2 : b % 2 = 1) : Even (d2 a b) :=
  (d2_even_iff a b ha hb).2 (by rw [ha2, hb2])

/-! ## 6. The published walk, evaluated -/

/-- The published directory lists `d² = 10` for the transition
`1000033 → 1000034`.  The documented pipeline gives `1`. -/
theorem d2_1000033_1000034 : d2 1000033 1000034 = 1 := by decide

/-- Under the documented map every transition of the published
`1000033 → … → 1000050` walk has `d² = 1`. -/
theorem d2_interfacial_all_one :
    ∀ n ∈ Finset.Ico 1000033 1000050, d2 n (n + 1) = 1 := by decide

/-- Odd `d²` really occurs on the raw layer: "`d²` is always even" is not a
property of the Gray encoding, only of the snapped states. -/
theorem exists_odd_d2 : ¬ (∀ a b : ℕ, a < 2 ^ 24 → b < 2 ^ 24 → Even (d2 a b)) := by
  intro h
  have h2 := h 1000033 1000034 (by norm_num) (by norm_num)
  rw [d2_1000033_1000034] at h2
  exact (Nat.not_even_iff_odd.2 ⟨0, rfl⟩) h2

end GLM.GrayJump
