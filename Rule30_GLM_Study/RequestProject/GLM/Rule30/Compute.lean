import RequestProject.GLM.Rule30.Wobble
import RequestProject.GLM.Rule30.AdjacentColumns
import RequestProject.GLM.Rule30.Perspective

/-!
# Rule 30: verified fast evaluation and machine-checked finite facts

(This file is deliberately not a `module`: its finite checks use `native_decide`.)

A row that is white outside a finite window is a natural number read in binary, and one
Rule 30 step is the bit-parallel formula

  `rowStep r = (r <<< 2) ^^^ ((r <<< 1) ||| r)`.

`testBit_rowStep_iterate` proves this agrees with the specification `evolve`, and
`centerCol_eq_fast` specialises it to the centre column.  On top of this we check:

* `centerCol_first_30`  — agreement with OEIS A051023 (first 30 terms);
* `wobble_milestones`   — the accumulator values `D(10) = 4`, `D(100) = 4`, `D(1000) = −38`,
  `D(10000) = 64`, `D(20000) = 240` reported in the study;
* `wobble_max_10000`    — `max_{n ≤ 10000} |D(n)| = 80`;
* `no_small_eventual_period` — the centre column has no eventual period `p ≤ 1000`
  starting at or before time `1000` (finite evidence for Problem 1, not a proof).
-/

namespace GLM.Rule30

/-- One Rule 30 step on a finite row encoded as a natural number. -/
def rowStep (r : ℕ) : ℕ := (r <<< 2) ^^^ ((r <<< 1) ||| r)

/-- The row encoded by `m`, with bit `k` of `m` placed at position `k - o`. -/
def maskConfig (o m : ℕ) : Config := fun c => if 0 ≤ c + o then m.testBit (c + o).toNat else false

theorem maskConfig_white (o m : ℕ) : ∀ j, j < -(o : ℤ) → maskConfig o m j = false := by
  intro j hj; simp [maskConfig]; omega

/-- **Correctness of the bit-parallel step.** After `t` steps, bit `k` of the encoded row
is the cell at position `k − o − t`. -/
theorem testBit_rowStep_iterate (o m t k : ℕ) :
    (rowStep^[t] m).testBit k = evolve (maskConfig o m) t ((k : ℤ) - o - t) := by
  induction t generalizing k with
  | zero =>
    simp only [Function.iterate_zero, id_eq, evolve_zero, maskConfig, CharP.cast_eq_zero,
      sub_zero]
    rw [if_pos (by omega)]; congr 1; omega
  | succ t ih =>
    have hw := evolve_white_left (maskConfig o m) (-(o : ℤ)) (maskConfig_white o m) t
    have L : evolve (maskConfig o m) t ((k : ℤ) - o - ↑(t + 1) - 1) =
        (decide (2 ≤ k) && (rowStep^[t] m).testBit (k - 2)) := by
      rcases Nat.lt_or_ge k 2 with h | h
      · rw [hw _ (by push_cast; omega)]; simp [show ¬ (2 ≤ k) by omega]
      · rw [ih (k - 2)]; simp only [h, decide_true, Bool.true_and]
        congr 1; push_cast; omega
    have Cc : evolve (maskConfig o m) t ((k : ℤ) - o - ↑(t + 1)) =
        (decide (1 ≤ k) && (rowStep^[t] m).testBit (k - 1)) := by
      rcases Nat.lt_or_ge k 1 with h | h
      · rw [hw _ (by push_cast; omega)]; simp [show ¬ (1 ≤ k) by omega]
      · rw [ih (k - 1)]; simp only [h, decide_true, Bool.true_and]
        congr 1; push_cast; omega
    have e2 : (k : ℤ) - o - ↑(t + 1) + 1 = k - o - t := by push_cast; ring
    rw [Function.iterate_succ_apply', evolve_succ, L, Cc, e2, ← ih k]
    simp only [rowStep, Nat.testBit_xor, Nat.testBit_or, Nat.testBit_shiftLeft, rule30, ge_iff_le]

theorem seed_eq_maskConfig : seed = maskConfig 0 1 := by
  funext c
  simp only [seed, maskConfig, CharP.cast_eq_zero, add_zero]
  by_cases h : 0 ≤ c
  · rw [if_pos h]
    rcases eq_or_lt_of_le h with h' | h'
    · subst h'; simp
    · rw [decide_eq_false (by omega)]
      obtain ⟨k, hk⟩ : ∃ k : ℕ, c.toNat = k + 1 := ⟨c.toNat - 1, by omega⟩
      rw [hk, Nat.testBit_succ]; simp
  · rw [if_neg h]; simp; omega

/-- The centre column via the bit-parallel step. -/
def fastCenter (n : ℕ) : Bool := (rowStep^[n] 1).testBit n

theorem centerCol_eq_fast (n : ℕ) : centerCol n = fastCenter n := by
  rw [fastCenter, testBit_rowStep_iterate 0 1 n n, ← seed_eq_maskConfig]
  simp [centerCol]

/-! ## Generating many centre bits in one pass -/

/-- Tail-recursive generator: `genAux k t r acc` runs `k` more steps from time `t` with
current row `r`, pushing the centre bits onto `acc`. -/
def genAux : ℕ → ℕ → ℕ → List Bool → List Bool
  | 0, _, _, acc => acc
  | k + 1, t, r, acc => genAux k (t + 1) (rowStep r) (r.testBit t :: acc)

theorem genAux_spec (k t : ℕ) (acc : List Bool) :
    genAux k t (rowStep^[t] 1) acc = ((List.range' t k).map centerCol).reverse ++ acc := by
  induction k generalizing t acc with
  | zero => simp [genAux]
  | succ k ih =>
    rw [genAux, ← Function.iterate_succ_apply' rowStep t 1, ih (t + 1)]
    simp [List.range'_succ, centerCol_eq_fast, fastCenter]

/-- The first `N` centre bits, computed in one pass. -/
def fastList (N : ℕ) : List Bool := (genAux N 0 1 []).reverse

theorem fastList_eq (N : ℕ) : fastList N = (List.range N).map centerCol := by
  have := genAux_spec N 0 []
  simp only [Function.iterate_zero, id_eq, List.append_nil] at this
  rw [fastList, this, List.reverse_reverse, List.range_eq_range']

theorem ones_eq_count (a : ℕ → Bool) (N : ℕ) : ones a N = ((List.range N).map a).count true := by
  induction N with
  | zero => simp
  | succ N ih =>
    rw [ones_succ, ih, List.range_succ, List.map_append, List.count_append]
    cases h : a N <;> simp [h]

theorem wobble_eq_fast (N : ℕ) :
    wobble centerCol N = 2 * ((fastList N).count true : ℤ) - N := by
  rw [wobble, ones_eq_count, fastList_eq]

/-! ## Machine-checked finite facts -/

/-- Agreement with OEIS A051023 (first 30 terms). -/
theorem centerCol_first_30 :
    (List.range 30).map (fun n => (centerCol n).toNat) =
      [1, 1, 0, 1, 1, 1, 0, 0, 1, 1, 0, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 1, 1, 1, 0, 1, 0, 1, 1] := by
  simp only [centerCol_eq_fast]
  native_decide

/-- The wobble milestones reported in the study. -/
theorem wobble_milestones :
    wobble centerCol 10 = 4 ∧ wobble centerCol 100 = 4 ∧ wobble centerCol 1000 = -38 ∧
      wobble centerCol 10000 = 64 ∧ wobble centerCol 20000 = 240 := by
  simp only [wobble_eq_fast]
  native_decide

/-- The first 20000 centre bits (a closed constant, evaluated once). -/
def list20000 : List Bool := fastList 20000

theorem list20000_eq : list20000 = (List.range 20000).map centerCol := fastList_eq 20000

theorem wobble_eq_take (n : ℕ) (hn : n ≤ 20000) :
    wobble centerCol n = 2 * ((list20000.take n).count true : ℤ) - n := by
  rw [wobble, ones_eq_count, list20000_eq, ← List.map_take, List.take_range,
    min_eq_left hn]

theorem centerCol_eq_getD (n : ℕ) (hn : n < 20000) : centerCol n = list20000.getD n false := by
  rw [list20000_eq, List.getD_eq_getElem?_getD, List.getElem?_map, List.getElem?_range hn]
  rfl

/-- **Running maximum of the wobble up to `10⁴`:** `max_{n ≤ 10000} |D(n)| = 80`,
attained at `n = 1462`. -/
theorem wobble_max_10000 :
    (∀ n ≤ 10000, |wobble centerCol n| ≤ 80) ∧ |wobble centerCol 1462| = 80 := by
  have h : ((List.range 10001).all fun n =>
      decide (|2 * ((list20000.take n).count true : ℤ) - n| ≤ 80)) = true := by
    native_decide
  refine ⟨fun n hn => ?_, ?_⟩
  · have := List.all_eq_true.mp h n (List.mem_range.mpr (by omega))
    rw [wobble_eq_take n (by omega)]
    simpa using this
  · rw [wobble_eq_take 1462 (by omega)]
    native_decide

/-- **No small eventual period.** For every `1 ≤ p ≤ 1000` there is a time
`1000 ≤ n < 2000` with `a(n + p) ≠ a(n)`. -/
theorem no_period_witness :
    ∀ p, 1 ≤ p → p ≤ 1000 → ∃ n, 1000 ≤ n ∧ n < 2000 ∧ centerCol (n + p) ≠ centerCol n := by
  have h : ((List.range' 1 1000).all fun p => (List.range' 1000 1000).any fun n =>
      list20000.getD (n + p) false != list20000.getD n false) = true := by
    native_decide
  intro p hp1 hp2
  have hp := List.all_eq_true.mp h p (List.mem_range'_1.mpr ⟨hp1, by omega⟩)
  obtain ⟨n, hn, hne⟩ := List.any_eq_true.mp hp
  obtain ⟨hn1, hn2⟩ := List.mem_range'_1.mp hn
  refine ⟨n, hn1, by omega, ?_⟩
  rw [centerCol_eq_getD n (by omega), centerCol_eq_getD (n + p) (by omega)]
  simpa using hne

/-- **Finite evidence for Problem 1.** The centre column has no eventual period `p ≤ 1000`
that starts at or before time `1000`. -/
theorem no_small_eventual_period (p N : ℕ) (hp : 1 ≤ p) (hp' : p ≤ 1000) (hN : N ≤ 1000) :
    ¬ ∀ n ≥ N, centerCol (n + p) = centerCol n := by
  intro h
  obtain ⟨n, hn1, _, hne⟩ := no_period_witness p hp hp'
  exact hne (h n (by omega))

/-- **The wobble arrow and Rule 30 (`n < 10⁴`).** At 9964 of the first 10000 times the arrow
is non-zero, and the centre column follows it at 4968 of them — about half, as for an
"open-loop" (random-like) source, in contrast with the ideal delta-sigma modulator
(`deltaSigma_follows_arrow`). -/
theorem arrow_stats_10000 :
    ((Finset.range 10000).filter (fun n => observerArrow centerCol n ≠ 0)).card = 9964 ∧
      ((Finset.range 10000).filter (fun n => observerArrow centerCol n ≠ 0 ∧
        stepDir centerCol n = observerArrow centerCol n)).card = 4968 := by
  have hw : ∀ n ∈ Finset.range 10000, observerArrow centerCol n =
      -Int.sign (2 * ((list20000.take n).count true : ℤ) - n) := by
    intro n hn
    rw [observerArrow, wobble_eq_take n (by simp at hn; omega)]
  have hs : ∀ n ∈ Finset.range 10000, stepDir centerCol n =
      if list20000.getD n false then 1 else -1 := by
    intro n hn
    rw [stepDir, centerCol_eq_getD n (by simp at hn; omega)]
  refine ⟨?_, ?_⟩
  · rw [Finset.filter_congr
      (q := fun n => -Int.sign (2 * ((list20000.take n).count true : ℤ) - n) ≠ 0)
      (fun n hn => by rw [hw n hn])]
    native_decide
  · rw [Finset.filter_congr
      (q := fun n => -Int.sign (2 * ((list20000.take n).count true : ℤ) - n) ≠ 0 ∧
        (if list20000.getD n false then 1 else -1) =
          -Int.sign (2 * ((list20000.take n).count true : ℤ) - n))
      (fun n hn => by rw [hw n hn, hs n hn])]
    native_decide

end GLM.Rule30
