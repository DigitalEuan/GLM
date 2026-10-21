import Mathlib

/-!
# Field "punctures" and "spins" (iteration 5, phase 2)

The study's vocabulary: the *puncture* of a field is multiplication by its characteristic
(it is the zero map, "deletion"); a *spin* is multiplication by a unit of order `≥ 2`.

Verified here:
* `F₂`: `2 = 0` (deletion, no spin); `F₃`: `2 = -1`, of order 2.
* `F₅`: `2` has order 4; `F₇`: `2` has order 3 while `3` has the full order 6.
* There is **no field with 6 elements** (iteration 5's "F₆ is not a field"), and `ℤ/6`
  has zero divisors.
* In every field of characteristic 2 (`F₂, F₄, F₈`, …) multiplication by 2 is still the zero
  map: extending a char-2 field never removes the puncture.
* `F₄ˣ` has order 3 and `F₈ˣ` has order 7, so every non-identity unit there has order 3 / 7.
* `F₉ˣ` is cyclic of order 8: there *is* a unit of order 8. An element `α` with `α² = -1`
  (the `F₃[α]/(α²+1)` generator used by the study's scripts) has order **4**, not 8; so the
  scripts' `spin_order = 4` for `F₉` is right, while the iteration-5 report text claiming
  "`F₉`: order 8 (the richest spin)" refers to the full group, which `α` does not generate.
-/

namespace GLMKit

/-- `F₂`: multiplication by 2 is deletion. -/
theorem f2_two_eq_zero : (2 : ZMod 2) = 0 := by decide

/-- `F₃`: multiplication by 2 is negation, a unit of order 2 ("spin"). -/
theorem f3_two_eq_neg_one : (2 : ZMod 3) = -1 := by decide

theorem f3_orderOf_two : orderOf (2 : ZMod 3) = 2 := by
  haveI : Fact (Nat.Prime 2) := ⟨Nat.prime_two⟩
  exact orderOf_eq_prime (by decide) (by decide)

theorem f5_orderOf_two : orderOf (2 : ZMod 5) = 4 :=
  (orderOf_eq_iff (by norm_num)).2 ⟨by decide, by decide⟩

theorem f7_orderOf_two : orderOf (2 : ZMod 7) = 3 := by
  haveI : Fact (Nat.Prime 3) := ⟨Nat.prime_three⟩
  exact orderOf_eq_prime (by decide) (by decide)

theorem f7_orderOf_three : orderOf (3 : ZMod 7) = 6 :=
  (orderOf_eq_iff (by norm_num)).2 ⟨by decide, by decide⟩

/-- `ℤ/6` has zero divisors: `2 · 3 = 0`. -/
theorem zmod6_zero_divisors : (2 : ZMod 6) * 3 = 0 ∧ (2 : ZMod 6) ≠ 0 ∧ (3 : ZMod 6) ≠ 0 := by
  decide

theorem zmod6_not_isDomain : ¬ IsDomain (ZMod 6) := by
  intro h
  have := zmod6_zero_divisors
  exact mul_ne_zero this.2.1 this.2.2 this.1

/-- **There is no field with 6 elements.** -/
theorem no_field_of_card_six (K : Type*) [Field K] [Fintype K] : Fintype.card K ≠ 6 := by
  obtain ⟨p, -, k, hp, hcard⟩ := FiniteField.card' K
  rw [hcard]
  intro h6
  have hdvd : p ∣ 6 := by
    rw [← h6]; exact dvd_pow_self p (PNat.ne_zero k)
  have hp6 : p ≤ 6 := Nat.le_of_dvd (by norm_num) hdvd
  have hk : (k : ℕ) ≤ 6 := by
    have : (k : ℕ) < p ^ (k : ℕ) := Nat.lt_pow_self hp.one_lt
    omega
  interval_cases p <;> norm_num at hp <;> interval_cases (k : ℕ) <;> simp_all

/-- In any characteristic-2 ring (`F₂`, `F₄`, `F₈`, …) multiplication by 2 is the zero map. -/
theorem char_two_puncture (K : Type*) [Ring K] [CharP K 2] (x : K) : 2 * x = 0 := by
  rw [show (2 : K) = ((2 : ℕ) : K) by norm_num, CharP.cast_eq_zero, zero_mul]

/-- An element with `α² = -1` in a ring where `2 ≠ 0` has multiplicative order exactly 4. -/
theorem orderOf_eq_four_of_sq_eq_neg_one {K : Type*} [Ring K] [NoZeroDivisors K]
    (h2 : (2 : K) ≠ 0) {a : K} (ha : a ^ 2 = -1) : orderOf a = 4 := by
  have hneg : (-1 : K) ≠ 1 := by
    intro h
    apply h2
    calc (2 : K) = 1 - (-1) := ((sub_neg_eq_add 1 1).trans one_add_one_eq_two).symm
      _ = 1 - 1 := by rw [h]
      _ = 0 := sub_self 1
  rw [orderOf_eq_iff (by norm_num)]
  refine ⟨by rw [show 4 = 2 * 2 by rfl, pow_mul, ha]; norm_num, ?_⟩
  intro m hm hm0
  interval_cases m
  · intro h1
    rw [pow_one] at h1
    rw [h1] at ha
    simp at ha
    exact hneg ha.symm
  · rw [ha]; exact hneg
  · intro h3
    have : a ^ 4 = a := by
      rw [show 4 = 3 + 1 by rfl, pow_succ, h3, one_mul]
    rw [show 4 = 2 * 2 by rfl, pow_mul, ha] at this
    have ha1 : a = 1 := by rw [← this]; norm_num
    rw [ha1] at ha
    simp at ha
    exact hneg ha.symm

/-- The concrete `F₉ = F₃[α]/(α²+1)` generator `α` has order 4 (not 8). -/
theorem f9_alpha_order_four (K : Type*) [Field K] [CharP K 3] {a : K} (ha : a ^ 2 = -1) :
    orderOf a = 4 := by
  refine orderOf_eq_four_of_sq_eq_neg_one ?_ ha
  intro h
  have : ((2 : ℕ) : K) = 0 := by exact_mod_cast h
  rw [CharP.cast_eq_zero_iff K 3] at this
  norm_num at this

theorem galoisField_card (p : ℕ) [Fact p.Prime] (k : ℕ) (hk : k ≠ 0) :
    Nat.card (GaloisField p k)ˣ = p ^ k - 1 := by
  rw [Nat.card_units, GaloisField.card p k hk]

/-- `F₉ˣ` is cyclic of order 8: there is a unit of order 8 (a full "spin" generator). -/
theorem f9_units_cyclic_order_eight :
    Nat.card (GaloisField 3 2)ˣ = 8 ∧ ∃ g : (GaloisField 3 2)ˣ, orderOf g = 8 := by
  haveI : Fact (Nat.Prime 3) := ⟨Nat.prime_three⟩
  have hcard : Nat.card (GaloisField 3 2)ˣ = 8 := by
    rw [galoisField_card 3 2 (by norm_num)]; norm_num
  refine ⟨hcard, ?_⟩
  obtain ⟨g, hg⟩ := IsCyclic.exists_generator (α := (GaloisField 3 2)ˣ)
  exact ⟨g, by rw [orderOf_eq_card_of_forall_mem_zpowers hg, hcard]⟩

/-- `F₄ˣ` has order 3: every non-identity unit of `F₄` has order 3. -/
theorem f4_units_order_three (g : (GaloisField 2 2)ˣ) (hg : g ≠ 1) : orderOf g = 3 := by
  haveI : Fact (Nat.Prime 2) := ⟨Nat.prime_two⟩
  haveI : Fact (Nat.Prime 3) := ⟨Nat.prime_three⟩
  have hcard : Nat.card (GaloisField 2 2)ˣ = 3 := by
    rw [galoisField_card 2 2 (by norm_num)]; norm_num
  refine orderOf_eq_prime ?_ hg
  rw [← hcard]; exact pow_card_eq_one'

/-- `F₈ˣ` has order 7: every non-identity unit of `F₈` has order 7. -/
theorem f8_units_order_seven (g : (GaloisField 2 3)ˣ) (hg : g ≠ 1) : orderOf g = 7 := by
  haveI : Fact (Nat.Prime 2) := ⟨Nat.prime_two⟩
  haveI : Fact (Nat.Prime 7) := ⟨by norm_num⟩
  have hcard : Nat.card (GaloisField 2 3)ˣ = 7 := by
    rw [galoisField_card 2 3 (by norm_num)]; norm_num
  refine orderOf_eq_prime ?_ hg
  rw [← hcard]; exact pow_card_eq_one'

end GLMKit
