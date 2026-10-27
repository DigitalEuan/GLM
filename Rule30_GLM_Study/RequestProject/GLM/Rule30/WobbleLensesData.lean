import RequestProject.GLM.Rule30.WobbleCertificate
import RequestProject.GLM.Rule30.WobbleLenses

/-!
# Round 12: exact readings of the centre column through the strobe and arrow lenses

Machine-checked finite facts (computed with `native_decide` from the verified fast generator
`fastList`, as in `WobbleCertificate.lean`).

* `strobe_wobble_table` : the phase wobbles `D_{p,r}(⌊10⁶/p⌋)` of the centre column for strides
  `p = 2, …, 6` (all phases `r < p`).  The largest is `D_{3,1}(333333) = 1583`, about `2.7`
  standard deviations of a fair coin; at `10⁷` bits it falls back to `1.8` (`EMP`,
  `rule30_round12/r12_lens_survey_output_10M.txt`).
* `arrow_last_flip_1e6` : the plain wobble is `0` at `N = 195112` and **strictly positive for every
  `N` from `195113` to `10⁶`**: the observer's arrow `−sign D(N)` does not flip in that range.
  A persistent arrow is what a fair coin typically shows too (the arcsine law: the last return to
  zero before `N` falls in the first 2% of the run with probability about 9%), so on its own it
  is not evidence of bias; and `exists_balanced_persistent_arrow` shows that a sequence can have
  exactly balanced frequency with an arrow that never flips at all.
-/

namespace GLM.Rule30

/-- Phase wobble computed from an array of bits. -/
def strobeWobbleFast (arr : Array Bool) (p r M : ℕ) : ℤ :=
  2 * (((List.range M).map (fun t => arr.getD (p * t + r) false)).count true : ℤ) - M

theorem fastList_toArray_getD {L i : ℕ} (hi : i < L) :
    (fastList L).toArray.getD i false = centerCol i := by
  rw [fastList_eq]
  simp [Array.getD, hi]

theorem strobeWobbleFast_eq {p r M L : ℕ} (hr : r < p) (hL : p * M ≤ L) :
    strobeWobbleFast (fastList L).toArray p r M = wobble (strobe centerCol p r) M := by
  rw [strobeWobbleFast, wobble, ones_eq_count]
  congr 3
  congr 1
  refine List.map_congr_left ?_
  intro t ht
  rw [List.mem_range] at ht
  rw [fastList_toArray_getD (by nlinarith)]
  rfl

/-- All phase wobbles for strides `2..6` at `p·M ≤ 10⁶`, checked in one pass. -/
def strobeTable : List (ℕ × ℕ × ℤ) :=
  [(2, 0, 704), (2, 1, 832),
   (3, 0, 179), (3, 1, 1583), (3, 2, -227),
   (4, 0, 18), (4, 1, 388), (4, 2, 686), (4, 3, 444),
   (5, 0, 1044), (5, 1, -72), (5, 2, 1144), (5, 3, -376), (5, 4, -204),
   (6, 0, 298), (6, 1, 568), (6, 2, -610), (6, 3, -120), (6, 4, 1014), (6, 5, 382)]

theorem strobeTable_check :
    (let arr := (fastList 1000000).toArray
     strobeTable.all (fun e => strobeWobbleFast arr e.1 e.2.1 (1000000 / e.1) == e.2.2)) = true := by
  native_decide

/-- **The strobe lens on the first `10⁶` bits**: every listed phase wobble is exact. -/
theorem strobe_wobble_table :
    ∀ e ∈ strobeTable, wobble (strobe centerCol e.1 e.2.1) (1000000 / e.1) = e.2.2 := by
  intro e he
  have h := strobeTable_check
  simp only [List.all_eq_true, beq_iff_eq] at h
  have hp : e.2.1 < e.1 ∧ e.1 * (1000000 / e.1) ≤ 1000000 := by
    refine ⟨?_, Nat.mul_div_le _ _⟩
    have hall : strobeTable.all (fun e => decide (e.2.1 < e.1)) = true := by decide
    simp only [List.all_eq_true, decide_eq_true_eq] at hall
    exact hall e he
  rw [← strobeWobbleFast_eq hp.1 hp.2]
  exact h e he

/-- The largest phase wobble at stride `3`. -/
theorem strobe_three_one : wobble (strobe centerCol 3 1) 333333 = 1583 :=
  strobe_wobble_table (3, 1, 1583) (by simp [strobeTable])

/-! ## The arrow lens -/

/-- Linear scan: check that the accumulator stays strictly positive. -/
def posScan : List Bool → ℤ → Bool
  | [], _ => true
  | b :: bs, D =>
    let D' := D + (if b then 1 else -1)
    decide (0 < D') && posScan bs D'

theorem posScan_spec (a : ℕ → Bool) (L k : ℕ)
    (h : posScan ((List.range' k L).map a) (wobble a k) = true) :
    ∀ n, k < n → n ≤ k + L → 0 < wobble a n := by
  induction L generalizing k with
  | zero => intro n h1 h2; omega
  | succ L ih =>
    rw [List.range'_succ, List.map_cons, posScan, Bool.and_eq_true, decide_eq_true_eq,
      ← wobble_succ] at h
    intro n h1 h2
    rcases Nat.lt_or_ge (k + 1) n with h3 | h3
    · exact ih (k + 1) h.2 n h3 (by omega)
    · obtain rfl : n = k + 1 := by omega
      exact h.1

theorem arrow_check :
    (let l := fastList 1000000
     decide (2 * ((l.take 195112).count true : ℤ) - 195112 = 0) &&
       posScan (l.drop 195112) 0) = true := by
  native_decide

/-- **The arrow does not flip on `(195112, 10⁶]`**: `D(195112) = 0` and `D(N) > 0` for every
`195112 < N ≤ 10⁶`. -/
theorem arrow_last_flip_1e6 :
    wobble centerCol 195112 = 0 ∧ ∀ N, 195112 < N → N ≤ 1000000 → 0 < wobble centerCol N := by
  have h := arrow_check
  simp only [Bool.and_eq_true, decide_eq_true_eq] at h
  have h0 : wobble centerCol 195112 = 0 := by
    rw [wobble, ones_eq_count]
    have : (List.range 195112).map centerCol = (fastList 1000000).take 195112 := by
      rw [fastList_eq, ← List.map_take, List.take_range]; rfl
    rw [this]; have := h.1; push_cast at this ⊢; linarith
  refine ⟨h0, fun N h1 h2 => ?_⟩
  have hd : (fastList 1000000).drop 195112 = (List.range' 195112 804888).map centerCol := by
    rw [fastList_eq, ← List.map_drop, List.range_eq_range', List.drop_range']
  have := h.2
  rw [hd, ← h0] at this
  exact posScan_spec centerCol 804888 195112 this N h1 (by omega)

/-- A sequence with frequency exactly balanced whose arrow never flips: `1, 1, 0, 1, 0, 1, 0, …`
has `D(N) ∈ {1, 2}` for every `N ≥ 1`. -/
theorem exists_balanced_persistent_arrow :
    ∃ a : ℕ → Bool, HasFrequencyHalf a ∧ ∀ N, 1 ≤ N → 0 < wobble a N := by
  let a : ℕ → Bool := fun n => decide (n = 0 ∨ n % 2 = 1)
  have key : ∀ k, wobble a (2 * k + 1) = 1 ∧ wobble a (2 * k + 2) = 2 := by
    intro k
    induction k with
    | zero => refine ⟨?_, ?_⟩ <;> decide
    | succ k ih =>
      have e1 : wobble a (2 * (k + 1) + 1) = wobble a (2 * k + 2) - 1 := by
        rw [show 2 * (k + 1) + 1 = (2 * k + 2) + 1 by ring, wobble_succ]
        simp [a]; omega
      have e2 : wobble a (2 * (k + 1) + 2) = wobble a (2 * (k + 1) + 1) + 1 := by
        rw [show 2 * (k + 1) + 2 = (2 * (k + 1) + 1) + 1 by ring, wobble_succ]
        simp [a]
      constructor
      · rw [e1, ih.2]; norm_num
      · rw [e2, e1, ih.2]; norm_num
  have hpos : ∀ N, 1 ≤ N → 0 < wobble a N ∧ wobble a N ≤ 2 := by
    intro N hN
    obtain ⟨k, rfl | rfl⟩ : ∃ k, N = 2 * k + 1 ∨ N = 2 * k + 2 :=
      ⟨(N - 1) / 2, by omega⟩
    · rw [(key k).1]; norm_num
    · rw [(key k).2]; norm_num
  refine ⟨a, hasFrequencyHalf_of_le a (fun _ => 2) ?_ ?_, fun N hN => (hpos N hN).1⟩
  · exact tendsto_const_div_atTop_nhds_zero_nat 2
  · filter_upwards [Filter.eventually_ge_atTop 1] with N hN
    have h1 : (0 : ℝ) < wobble a N := by exact_mod_cast (hpos N hN).1
    have h2 : (wobble a N : ℝ) ≤ 2 := by exact_mod_cast (hpos N hN).2
    rw [abs_le]; constructor <;> linarith

end GLM.Rule30
