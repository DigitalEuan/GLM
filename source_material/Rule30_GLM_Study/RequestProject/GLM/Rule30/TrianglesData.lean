import RequestProject.GLM.Rule30.LeftDiagonalPeriodsData
import RequestProject.GLM.Rule30.Triangles

/-!
# Round 48: no large white triangles near the left edge (certified)

(Not a `module`: it uses `native_decide`.)

`Triangles.lean` proves that white triangles of **every** size hang one cell inside the right edge
(`arbitrarily_large_right_triangles`, at the rows `2 ^ k`).  This file certifies the other half of
the owner's observation: near the **left** edge the white runs (the tops of the triangles) stay
short, at every time.

A *white window of length `L` at depth `D`* at time `t` means the left diagonals
`D, D + 1, …, D + L − 1` are all white at time `t` (cells `D − t, …, D + L − 1 − t`).

* `left400_no_window_16` : inside the first `400` left diagonals (and inside the light cone) there
  is no white window of length `16` at **any** time.
* `left400_settled_no_window_11`, `left400_settled_window_10` : from time `501` on (when the first
  `400` diagonals have settled into period `8`) the longest white window there has length exactly
  `10`.
* `left20000_settled_no_window_17`, `left20000_settled_window_16` : from time `26834` on (period
  `16`) the longest white window inside the first `20000` left diagonals has length exactly `16`.

So inside the first `20000` left diagonals no white triangle of height more than `8` appears after
time `26834`.  In contrast, at every row `n · 2 ^ 20000` the `20000` cells inside the right edge are
white (`right_edge_white_run`).

The method: the first `N` left diagonals packed into one number evolve on their own
(`lrow`, `LeftDiagonalPeriodsData.lean`); white windows of length `L + 1` are the set bits of
`zeroWin z L = z ∧ (z ≫ 1) ∧ … ∧ (z ≫ L)` with `z` the white cells; one equality of packed rows
makes a check over one period valid for all later times.
-/

namespace GLM.Rule30

/-- Bit `D` is set iff bits `D, …, D + L` of `z` are all set. -/
def zeroWin (z : ℕ) : ℕ → ℕ
  | 0 => z
  | L + 1 => zeroWin z L &&& (z >>> (L + 1))

theorem testBit_zeroWin (z L D : ℕ) :
    (zeroWin z L).testBit D = true ↔ ∀ i ≤ L, z.testBit (D + i) = true := by
  induction L with
  | zero => simp [zeroWin]
  | succ L ih =>
    simp only [zeroWin, Nat.testBit_and, Bool.and_eq_true, ih, Nat.testBit_shiftRight]
    constructor
    · rintro ⟨h1, h2⟩ i hi
      rcases Nat.lt_or_ge i (L + 1) with h | h
      · exact h1 i (by omega)
      · rw [show i = L + 1 by omega, add_comm]; exact h2
    · intro h
      exact ⟨fun i hi => h i (by omega), by rw [add_comm]; exact h (L + 1) le_rfl⟩

/-- The white cells of the first `N` left diagonals at time `t`, inside the light cone. -/
def holeRow (N t : ℕ) : ℕ := (2 ^ (min N (2 * t + 1)) - 1) ^^^ lrow N t

theorem testBit_holeRow {N t i : ℕ} (hi : i < N) (hc : i ≤ 2 * t) :
    (holeRow N t).testBit i = !(ldiag i t) := by
  rw [holeRow, Nat.testBit_xor, Nat.testBit_two_pow_sub_one, testBit_lrow hi]
  have : i < min N (2 * t + 1) := by omega
  simp [this]

/-- No set bit in `zeroWin (holeRow N t) (L − 1)` means no white window of length `L`. -/
theorem no_window_of_zero {N t L : ℕ} (hL : 0 < L) (h : zeroWin (holeRow N t) (L - 1) = 0) :
    ∀ D : ℕ, D + L ≤ N → D + L ≤ 2 * t + 1 → ∃ i < L, ldiag ((D + i : ℕ) : ℤ) t = true := by
  intro D hN hc
  by_contra hcon
  push_neg at hcon
  have : (zeroWin (holeRow N t) (L - 1)).testBit D = true := by
    rw [testBit_zeroWin]
    intro i hi
    rw [testBit_holeRow (by omega) (by omega)]
    have := hcon i (by omega)
    simp only [Bool.not_eq_true] at this
    rw [this]; rfl
  rw [h] at this
  simp at this

/-- A set bit gives a white window. -/
theorem window_of_testBit {N t L D : ℕ} (hc : D + L ≤ 2 * t)
    (h : (zeroWin (holeRow N t) L).testBit D = true) (hL : D + L < N) :
    ∀ i ≤ L, ldiag ((D + i : ℕ) : ℤ) t = false := by
  intro i hi
  have := (testBit_zeroWin _ _ _).1 h i hi
  rw [testBit_holeRow (by omega) (by omega)] at this
  simpa using this

/-- Periodic reduction of the packed rows. -/
theorem lrow_reduce {N s p : ℕ} (h : lrow N (s + p) = lrow N s) (t : ℕ) (ht : s ≤ t) :
    lrow N t = lrow N (s + (t - s) % p) := by
  obtain ⟨n, rfl⟩ := Nat.exists_eq_add_of_le ht
  rw [Nat.add_sub_cancel_left]
  have key : ∀ q r, lrow N (s + (q * p + r)) = lrow N (s + r) := by
    intro q r
    induction q with
    | zero => simp
    | succ q ih =>
      rw [show s + ((q + 1) * p + r) = (s + p) + (q * p + r) by ring, lrow_add, h, ← lrow_add, ih]
  conv_lhs => rw [← Nat.div_add_mod n p, mul_comm]
  exact key _ _

theorem holeRow_reduce {N s p : ℕ} (h : lrow N (s + p) = lrow N s) (hs : N ≤ 2 * s + 1)
    (t : ℕ) (ht : s ≤ t) : holeRow N t = holeRow N (s + (t - s) % p) := by
  unfold holeRow
  rw [lrow_reduce h t ht, min_eq_left (by omega), min_eq_left (by omega)]

/-! ## Certificates: the first 400 left diagonals -/

/-- **CERT.** No white window of length `16` in the first `400` left diagonals, `t < 509`. -/
theorem left400_check16 :
    (List.range 509).all (fun t => zeroWin (holeRow 400 t) 15 == 0) = true := by native_decide

/-- **CERT.** No white window of length `11` in the first `400` left diagonals, `501 ≤ t < 509`. -/
theorem left400_check11 :
    (List.range 8).all (fun j => zeroWin (holeRow 400 (501 + j)) 10 == 0) = true := by
  native_decide

theorem left400_witness10 : (zeroWin (holeRow 400 505) 9).testBit 227 = true := by native_decide

theorem zeroWin_eq_zero_of_all {f : ℕ → ℕ} {n t : ℕ} (h : (List.range n).all (fun j => f j == 0) = true)
    (ht : t < n) : f t = 0 := by
  rw [List.all_eq_true] at h
  simpa using h t (List.mem_range.2 ht)

/-- **No white window of length `16` inside the first `400` left diagonals, at any time.** -/
theorem left400_no_window_16 (t : ℕ) :
    ∀ D : ℕ, D + 16 ≤ 400 → D + 16 ≤ 2 * t + 1 → ∃ i < 16, ldiag ((D + i : ℕ) : ℤ) t = true := by
  apply no_window_of_zero (by norm_num)
  rcases Nat.lt_or_ge t 509 with ht | ht
  · exact zeroWin_eq_zero_of_all (f := fun t => zeroWin (holeRow 400 t) 15) left400_check16 ht
  · rw [holeRow_reduce lrow_400_period_8 (by norm_num) t (by omega)]
    exact zeroWin_eq_zero_of_all (f := fun t => zeroWin (holeRow 400 t) 15) left400_check16
      (by have := Nat.mod_lt (t - 501) (show 0 < 8 by norm_num); omega)

/-- **After settling (`t ≥ 501`), no white window of length `11` inside the first `400` left
diagonals.** -/
theorem left400_settled_no_window_11 (t : ℕ) (ht : 501 ≤ t) :
    ∀ D : ℕ, D + 11 ≤ 400 → ∃ i < 11, ldiag ((D + i : ℕ) : ℤ) t = true := by
  intro D hD
  apply no_window_of_zero (by norm_num) _ D hD (by omega)
  rw [holeRow_reduce lrow_400_period_8 (by norm_num) t ht]
  exact zeroWin_eq_zero_of_all (f := fun j => zeroWin (holeRow 400 (501 + j)) 10) left400_check11
    (Nat.mod_lt _ (by norm_num))

/-- **The bound `10` is reached:** at time `505` (and so at every `505 + 8n`) the left diagonals
`227, …, 236` are white. -/
theorem left400_settled_window_10 (n : ℕ) :
    ∀ i < 10, ldiag ((227 + i : ℕ) : ℤ) (505 + 8 * n) = false := by
  intro i hi
  have hper := leftDiag_period_eight_below_400 (227 + i) (by omega)
  have e : ∀ m, ldiag ((227 + i : ℕ) : ℤ) (505 + 8 * m) = ldiag ((227 + i : ℕ) : ℤ) 505 := by
    intro m
    induction m with
    | zero => simp
    | succ m ih => rw [show 505 + 8 * (m + 1) = (505 + 8 * m) + 8 by ring, hper _ (by omega), ih]
  rw [e]
  exact window_of_testBit (N := 400) (L := 9) (by norm_num) left400_witness10
    (by norm_num) i (by omega)

/-! ## Certificates: the first 20000 left diagonals -/

theorem lrow_20000_period_16 : lrow 20000 (26834 + 16) = lrow 20000 26834 := by native_decide

/-- **CERT.** No white window of length `17` in the first `20000` left diagonals over one period. -/
theorem left20000_check17 :
    (List.range 16).all (fun j => zeroWin (holeRow 20000 (26834 + j)) 16 == 0) = true := by
  native_decide

theorem left20000_witness16 : (zeroWin (holeRow 20000 26840) 15).testBit 2347 = true := by
  native_decide

/-- **After settling (`t ≥ 26834`), no white window of length `17` inside the first `20000` left
diagonals.** -/
theorem left20000_settled_no_window_17 (t : ℕ) (ht : 26834 ≤ t) :
    ∀ D : ℕ, D + 17 ≤ 20000 → ∃ i < 17, ldiag ((D + i : ℕ) : ℤ) t = true := by
  intro D hD
  apply no_window_of_zero (by norm_num) _ D hD (by omega)
  rw [holeRow_reduce lrow_20000_period_16 (by norm_num) t ht]
  exact zeroWin_eq_zero_of_all (f := fun j => zeroWin (holeRow 20000 (26834 + j)) 16)
    left20000_check17 (Nat.mod_lt _ (by norm_num))

/-- **The bound `16` is reached:** at time `26840 + 16n` the left diagonals `2347, …, 2362` are
white. -/
theorem left20000_settled_window_16 (n : ℕ) :
    ∀ i < 16, ldiag ((2347 + i : ℕ) : ℤ) (26840 + 16 * n) = false := by
  intro i hi
  have hper := evPer_of_lrow lrow_20000_period_16 (2347 + i) (by omega)
  have e : ∀ m, ldiag ((2347 + i : ℕ) : ℤ) (26840 + 16 * m) = ldiag ((2347 + i : ℕ) : ℤ) 26840 := by
    intro m
    induction m with
    | zero => simp
    | succ m ih =>
      rw [show 26840 + 16 * (m + 1) = (26840 + 16 * m) + 16 by ring, hper _ (by omega), ih]
  rw [e]
  exact window_of_testBit (N := 20000) (L := 15) (by norm_num) left20000_witness16
    (by norm_num) i (by omega)

end GLM.Rule30
