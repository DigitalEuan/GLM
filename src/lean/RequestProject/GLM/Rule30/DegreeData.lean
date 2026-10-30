import RequestProject.GLM.Rule30.ANF
import RequestProject.GLM.Rule30.Compute

/-!
# Exact ANF degree `2n − 1` for `2 ≤ n ≤ 14`

(This file is deliberately not a `module`: it uses `native_decide`.)

`anfCoeff_topMonomial_eq_count` (in `ANF.lean`) reduces the top-monomial coefficient to the
parity of `whiteDiagonalCount n`, a count over the `2^(2n−2)` rows supported on
`[2−n, n−1]`.  Here that count is turned into a verified fast loop:

* `card_filter_powerset_eq_masks` : subsets of a window ↔ bit masks `m < 2^K`;
* `diagOK_spec`                   : in the bit-parallel frame the whole diagonal
  `(k, n−1−k)` is the single bit column `2n − 3`;
* `whiteDiagonalCount_eq_fast`    : `whiteDiagonalCount n = fastWhiteCount n` (proved);
* `fastWhiteCount_odd_*`          : the counts are odd for `2 ≤ n ≤ 14` (computation);
* `anfDegree_eq_upto14`           : **`deg a(n)(0) = 2n − 1` for every `2 ≤ n ≤ 14`.**

This extends the earlier range `2 ≤ n ≤ 7`.  It is exhaustive evidence (`EXH`) for the
open `TopMonomialConjecture`, not a proof of it.
-/

namespace GLM.Rule30

open Finset

/-! ## Subsets of a window are bit masks -/

/-- The cells of `[−o, −o + K)` that are black in the mask `m`. -/
def maskSet (o K m : ℕ) : Finset ℤ :=
  (Ico (-(o : ℤ)) (-(o : ℤ) + K)).filter (fun c => m.testBit (c + o).toNat)

theorem ind_maskSet (o K m : ℕ) (hm : m < 2 ^ K) : ind (maskSet o K m) = maskConfig o m := by
  funext c
  simp only [ind, maskSet, mem_filter, mem_Ico, maskConfig]
  by_cases h0 : 0 ≤ c + o
  · rw [if_pos h0]
    by_cases hK : c < -(o : ℤ) + K
    · simp [hK, show -(o : ℤ) ≤ c by omega]
    · have : m.testBit (c + o).toNat = false :=
        Nat.testBit_eq_false_of_lt (lt_of_lt_of_le hm (Nat.pow_le_pow_right (by norm_num)
          (by omega)))
      simp [this]
  · rw [if_neg h0]; simp; omega

theorem maskSet_injOn (o K : ℕ) {m₁ m₂ : ℕ} (h₁ : m₁ < 2 ^ K) (h₂ : m₂ < 2 ^ K)
    (h : maskSet o K m₁ = maskSet o K m₂) : m₁ = m₂ := by
  have hc := congrArg ind h
  rw [ind_maskSet o K m₁ h₁, ind_maskSet o K m₂ h₂] at hc
  apply Nat.eq_of_testBit_eq
  intro i
  have := congrFun hc ((i : ℤ) - o)
  simpa [maskConfig] using this

/-- **Subsets ↔ masks.** Counting subsets `T` of the window `[−o, −o + K)` with a property
of the row `1_T` is the same as counting masks `m < 2^K`. -/
theorem card_filter_powerset_eq_masks (Q : Config → Prop) [DecidablePred Q] (o K : ℕ) :
    ((Ico (-(o : ℤ)) (-(o : ℤ) + K)).powerset.filter (fun T => Q (ind T))).card =
      ((range (2 ^ K)).filter (fun m => Q (maskConfig o m))).card := by
  symm
  refine card_bij (fun m _ => maskSet o K m) ?_ ?_ ?_
  · intro m hm
    obtain ⟨hm1, hm2⟩ := mem_filter.mp hm
    have hmK := mem_range.mp hm1
    refine mem_filter.mpr ⟨mem_powerset.mpr (filter_subset _ _), ?_⟩
    rwa [ind_maskSet o K m hmK]
  · intro m₁ hm₁ m₂ hm₂ h
    exact maskSet_injOn o K (mem_range.mp (mem_filter.mp hm₁).1)
      (mem_range.mp (mem_filter.mp hm₂).1) h
  · intro T hT
    obtain ⟨hT1, hT2⟩ := mem_filter.mp hT
    have hsurj := surj_on_of_inj_on_of_card_le (s := range (2 ^ K))
      (t := (Ico (-(o : ℤ)) (-(o : ℤ) + K)).powerset)
      (fun m _ => maskSet o K m) (fun m _ => mem_powerset.mpr (filter_subset _ _))
      (fun m₁ m₂ h₁ h₂ h => maskSet_injOn o K (mem_range.mp h₁) (mem_range.mp h₂) h)
      (by rw [card_range, card_powerset, Int.card_Ico]; simp) T hT1
    obtain ⟨m, hm, hmT⟩ := hsurj
    refine ⟨m, mem_filter.mpr ⟨hm, ?_⟩, hmT.symm⟩
    have hmT' : T = maskSet o K m := hmT
    rw [← ind_maskSet o K m (mem_range.mp hm), ← hmT']; exact hT2

/-! ## The diagonal is one bit column in the bit-parallel frame -/

/-- `diagOK b k r`: bit `b` stays white for the `k` steps starting from the encoded row `r`
(evaluated with early exit). -/
def diagOK (b : ℕ) : ℕ → ℕ → Bool
  | 0, _ => true
  | k + 1, r => !r.testBit b && diagOK b k (rowStep r)

theorem diagOK_spec (b k r : ℕ) :
    diagOK b k r = decide (∀ j < k, (rowStep^[j] r).testBit b = false) := by
  induction k generalizing r with
  | zero => simp [diagOK]
  | succ k ih =>
    rw [diagOK, ih]
    by_cases h0 : r.testBit b = false
    · simp only [h0, Bool.not_false, Bool.true_and]
      congr 1
      apply propext
      constructor
      · intro h j hj
        rcases j with _ | j
        · simpa using h0
        · rw [Function.iterate_succ_apply]; exact h j (by omega)
      · intro h j hj
        have := h (j + 1) (by omega)
        rwa [Function.iterate_succ_apply] at this
    · simp only [Bool.not_eq_false] at h0
      simp only [h0, Bool.not_true, Bool.false_and, false_eq_decide_iff, not_forall]
      exact ⟨0, by omega, by simp [h0]⟩

/-- Tail-recursive counter: `countLoop p N acc = acc + #{m < N : p m}`. -/
def countLoop (p : ℕ → Bool) : ℕ → ℕ → ℕ
  | 0, acc => acc
  | N + 1, acc => countLoop p N (if p N then acc + 1 else acc)

theorem countLoop_spec (p : ℕ → Bool) (N acc : ℕ) :
    countLoop p N acc = acc + ((range N).filter (fun m => p m = true)).card := by
  induction N generalizing acc with
  | zero => simp [countLoop]
  | succ N ih =>
    rw [countLoop, ih, range_add_one, filter_insert]
    by_cases h : p N = true
    · rw [if_pos h, if_pos h, card_insert_of_notMem (by simp)]; ring
    · rw [if_neg h, if_neg h]

/-- Fast evaluation of `whiteDiagonalCount n`. -/
def fastWhiteCount (n : ℕ) : ℕ := countLoop (diagOK (2 * n - 3) n) (2 ^ (2 * n - 2)) 0

/-- **`whiteDiagonalCount n = fastWhiteCount n`** for `n ≥ 2` (proved). -/
theorem whiteDiagonalCount_eq_fast (n : ℕ) (hn : 2 ≤ n) :
    whiteDiagonalCount n = fastWhiteCount n := by
  have hwin : Icc (2 - (n : ℤ)) (n - 1) =
      Ico (-((n - 2 : ℕ) : ℤ)) (-((n - 2 : ℕ) : ℤ) + ((2 * n - 2 : ℕ) : ℤ)) := by
    ext c; simp only [mem_Icc, mem_Ico]; push_cast [Nat.cast_sub hn,
      Nat.cast_sub (show 2 ≤ 2 * n by omega)]; omega
  rw [whiteDiagonalCount, hwin, card_filter_powerset_eq_masks
    (fun x => ∀ k < n, x |> fun x => evolve x k ((n : ℤ) - 1 - k) = false),
    fastWhiteCount, countLoop_spec, zero_add]
  congr 1
  apply filter_congr
  intro m _
  rw [diagOK_spec]
  simp only [decide_eq_true_eq]
  refine forall_congr' (fun k => imp_congr_right (fun _ => ?_))
  rw [testBit_rowStep_iterate (n - 2) m k (2 * n - 3)]
  congr! 2
  push_cast [Nat.cast_sub hn, Nat.cast_sub (show 3 ≤ 2 * n by omega)]
  ring

/-! ## The computation -/

theorem fastWhiteCount_odd_2_12 : ∀ n ∈ Icc (2 : ℕ) 12, fastWhiteCount n % 2 = 1 := by
  native_decide

theorem fastWhiteCount_odd_13 : fastWhiteCount 13 % 2 = 1 := by native_decide
theorem fastWhiteCount_odd_14 : fastWhiteCount 14 % 2 = 1 := by native_decide

theorem fastWhiteCount_odd (n : ℕ) (hn : n ∈ Icc (2 : ℕ) 14) : fastWhiteCount n % 2 = 1 := by
  obtain ⟨h1, h2⟩ := mem_Icc.mp hn
  rcases (show n ≤ 12 ∨ n = 13 ∨ n = 14 by omega) with h | h | h
  · exact fastWhiteCount_odd_2_12 n (mem_Icc.mpr ⟨h1, h⟩)
  · subst h; exact fastWhiteCount_odd_13
  · subst h; exact fastWhiteCount_odd_14

/-- The top monomial `M_n` appears in the ANF of `a(n)(0)` for every `2 ≤ n ≤ 14`. -/
theorem anfCoeff_topMonomial_upto14 (n : ℕ) (hn : n ∈ Icc (2 : ℕ) 14) :
    anfCoeff (fun x => evolve x n 0) (topMonomial n) = 1 := by
  have h2 := (mem_Icc.mp hn).1
  rw [anfCoeff_topMonomial_eq_count n (by omega), whiteDiagonalCount_eq_fast n h2,
    ZMod.natCast_eq_one_iff_odd, Nat.odd_iff]
  exact fastWhiteCount_odd n hn

/-- **`deg a(n)(0) = 2n − 1` exactly, for every `2 ≤ n ≤ 14`** (exhaustive evidence for
`TopMonomialConjecture`). -/
theorem anfDegree_eq_upto14 (n : ℕ) (hn : n ∈ Icc (2 : ℕ) 14) :
    AnfDegreeEq (fun x => evolve x n 0) (2 * n - 1) :=
  ⟨center_anfDegree_le n (mem_Icc.mp hn).1, topMonomial n,
    topMonomial_card n (mem_Icc.mp hn).1, anfCoeff_topMonomial_upto14 n hn⟩

end GLM.Rule30
