import RequestProject.GLM.Rule30.LeftDiagonalPeriodsData
import RequestProject.GLM.Rule30.Transients

/-!
# Round 40: every row with a left edge has the seed's left side, up to a time shift, to `53207`

(Not a `module`: it uses `native_decide` through the Round 38 certificates.)

Round 38 showed (`seed_first_difference`) that a row with a left edge can first differ eventually
from the single black cell only one step past a white diagonal: at `3, 8, 29, 400, 53208, …`.
Round 40 proved that at an **odd** white diagonal the difference is only a time shift
(`shift_equiv_extend_odd`).  The white diagonals `2, 7, 28, 399` of the seed are all odd
(outer periods `1, 2, 4, 8`), and the first even one is `53207`.  Chaining the two extension
lemmas along the certified white list gives:

* `left_edge_rows_agree_up_to_shift` : **for every row `x` white on `(-∞, 0)` and black at `0`
  there is a time shift `k` such that each left diagonal `D ≤ 53207` of `x` eventually equals
  the seed's left diagonal `D` shifted by `k`.**

So up to the first even white diagonal the eventual left side of Rule 30 does not depend on the
row at all.  Beyond `53207` the same statement needs the open bit at the even white diagonal; the
Round 40 computations (study folder `rule30_round40/`, EMP) found the same bit for all 325 rows
tried, including fully random rows of width up to `99999`.
-/

namespace GLM.Rule30

/-- The data needed at an odd white diagonal, read from one packed-row certificate: the white
diagonal is `D + 1`, its outer neighbour `D` has period `Q` and odd parity. -/
theorem odd_white_bundle {D s Q : ℕ} (hQ : 0 < Q) (h : lrow (D + 2) (s + Q) = lrow (D + 2) s)
    (hw : (orRun (2 ^ (D + 2) - 1) (lrow (D + 2) s) Q).testBit (D + 1) = false)
    (hp : parityOn (fun t => (lrow (D + 2) t).testBit D) s Q = true) :
    (∀ D' : ℕ, D' ≤ D + 1 → EvPer (ldiag (D' : ℤ)) Q) ∧ PerFrom (ldiag (D : ℤ)) Q s ∧
      parityOn (ldiag (D : ℤ)) s Q = true ∧ ∀ t ≥ s, ldiag ((D + 1 : ℕ) : ℤ) t = false := by
  have hper := evPer_of_lrow h
  refine ⟨fun D' hD' => ⟨s, hper D' (by omega)⟩, hper D (by omega), ?_,
    white_of_orRun (by omega) hQ h hw⟩
  have : (fun t => (lrow (D + 2) t).testBit D) = ldiag (D : ℤ) :=
    funext fun t => testBit_lrow (by omega) t
  rw [← this]; exact hp

theorem lrow_3_period_1 : lrow 3 (2 + 1) = lrow 3 2 := by native_decide
theorem orRun_3_bit_2 : (orRun (2 ^ 3 - 1) (lrow 3 2) 1).testBit 2 = false := by native_decide
theorem parity_1_packed : parityOn (fun t => (lrow 3 t).testBit 1) 2 1 = true := by native_decide

theorem lrow_8_period_2 : lrow 8 (20 + 2) = lrow 8 20 := by native_decide
theorem orRun_8_bit_7 : (orRun (2 ^ 8 - 1) (lrow 8 20) 2).testBit 7 = false := by native_decide
theorem parity_6_packed : parityOn (fun t => (lrow 8 t).testBit 6) 20 2 = true := by native_decide

theorem lrow_29_period_4 : lrow 29 (60 + 4) = lrow 29 60 := by native_decide
theorem orRun_29_bit_28 : (orRun (2 ^ 29 - 1) (lrow 29 60) 4).testBit 28 = false := by
  native_decide
theorem parity_27_packed : parityOn (fun t => (lrow 29 t).testBit 27) 60 4 = true := by
  native_decide

set_option exponentiation.threshold 512 in
/-- **Every row with a left edge has the seed's left side up to a time shift, through the first
even white diagonal.**  For every row `x` white on `(-∞, 0)` and black at `0` there is a shift
`k` such that for every `D ≤ 53207` the left diagonal `D` of `x` eventually equals the seed's left
diagonal `D` read `k` steps later. -/
theorem left_edge_rows_agree_up_to_shift {x : Config} (hx : LeftEdgeAtZero x) :
    ∃ k, ∀ D : ℕ, D ≤ 53207 → EventuallyEq (fun t => ldiag (D : ℤ) (t + k)) (ldiagOf x D) := by
  have hu : LeftMachine (fun D t => ldiag (D : ℤ) t) := ldiag_leftMachine
  have hv : LeftMachine (fun D t => ldiagOf x (D : ℤ) t) := ldiagOf_leftMachine x
  have key : ∀ n, n ≤ 53206 → ∃ k, ∀ D' : ℕ, D' ≤ n + 1 →
      EventuallyEq (fun t => ldiag (D' : ℤ) (t + k)) (ldiagOf x D') := by
    intro n
    induction n with
    | zero =>
      intro _
      refine ⟨0, fun D' hD' => ?_⟩
      interval_cases D'
      · exact ⟨0, fun t _ => by
          have h1 := ldiagOf_zero seed_leftEdgeAtZero (t + 0)
          have h2 := ldiagOf_zero hx t
          simp only [ldiagOf_seed] at h1
          simp only [Nat.cast_zero, h1, h2]⟩
      · refine ⟨1, fun t ht => ?_⟩
        obtain ⟨m, rfl⟩ := Nat.exists_eq_add_of_le' ht
        have h1 := ldiagOf_one seed_leftEdgeAtZero (m + 0)
        have h2 := ldiagOf_one hx m
        simp only [ldiagOf_seed] at h1
        simp only [Nat.cast_one, show m + 1 + 0 = m + 0 + 1 by ring, h1, h2]
    | succ n ih =>
      intro hn
      obtain ⟨k, hk⟩ := ih (by omega)
      by_cases hw : EventuallyWhite (ldiag ((n + 1 : ℕ) : ℤ))
      · have hmem := (leftDiag_white_below_87868 (n + 1) (by omega)).1 hw
        rcases hmem with h | h | h | h | h | h | h
        · obtain rfl : n = 1 := by omega
          obtain ⟨hper, hDq, hodd, hwh⟩ :=
            odd_white_bundle (D := 1) (by norm_num) lrow_3_period_1 orRun_3_bit_2 parity_1_packed
          exact shift_equiv_extend_odd (u := fun D t => ldiag (D : ℤ) t)
            (v := fun D t => ldiagOf x (D : ℤ) t) hu hv hk hper hDq hodd hwh
        · obtain rfl : n = 6 := by omega
          obtain ⟨hper, hDq, hodd, hwh⟩ :=
            odd_white_bundle (D := 6) (by norm_num) lrow_8_period_2 orRun_8_bit_7 parity_6_packed
          exact shift_equiv_extend_odd (u := fun D t => ldiag (D : ℤ) t)
            (v := fun D t => ldiagOf x (D : ℤ) t) hu hv hk hper hDq hodd hwh
        · obtain rfl : n = 27 := by omega
          obtain ⟨hper, hDq, hodd, hwh⟩ :=
            odd_white_bundle (D := 27) (by norm_num) lrow_29_period_4 orRun_29_bit_28
              parity_27_packed
          exact shift_equiv_extend_odd (u := fun D t => ldiag (D : ℤ) t)
            (v := fun D t => ldiagOf x (D : ℤ) t) hu hv hk hper hDq hodd hwh
        · obtain rfl : n = 398 := by omega
          obtain ⟨hper, hDq, hodd, hwh⟩ :=
            odd_white_bundle (D := 398) (by norm_num) lrow_400_period_8 orRun_400_bit_399
              parity_398_packed
          exact shift_equiv_extend_odd (u := fun D t => ldiag (D : ℤ) t)
            (v := fun D t => ldiagOf x (D : ℤ) t) hu hv hk hper hDq hodd hwh
        all_goals omega
      · exact ⟨k, shift_equiv_extend (u := fun D t => ldiag (D : ℤ) t)
          (v := fun D t => ldiagOf x (D : ℤ) t) hu hv hk hw⟩
  obtain ⟨k, hk⟩ := key 53206 le_rfl
  exact ⟨k, fun D hD => hk D (by omega)⟩

end GLM.Rule30
