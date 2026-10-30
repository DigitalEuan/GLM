import RequestProject.GLM.Rule30.ParityReduction
import RequestProject.GLM.Rule30.DegreeData

/-!
# The reduced parity count, computed: `deg a(n)(0) = 2n − 1` further

(This file is deliberately not a `module`: it uses `native_decide`.)

`whiteDiagonalCount_eq_reduced` turns the count over `2^(2n−2)` rows into a count over `2^(n−1)`
free-cell patterns.  Here the right-to-left scan is run on bit masks (`buildMask`), proved equal
to the specification `buildAux` (`maskConfig_buildMask`), and the resulting fast count
`fastReducedCount` is evaluated.

* `whiteDiagonalCount_eq_fastReduced` : `whiteDiagonalCount n = fastReducedCount n` (proved).
* `fastReducedCount_odd_*` : the count is odd (computation, `native_decide`).
* `anfDegree_eq_upto20` : **`deg a(n)(0) = 2n − 1` for every `2 ≤ n ≤ 20`** (exhaustive evidence for
  the open `TopMonomialConjecture`, extending the earlier range `n ≤ 14`).
-/

namespace GLM.Rule30

open Finset

/-- The scan on bit masks (bit `b` ↔ position `b − n`). -/
def buildMask (n g : ℕ) : ℕ → ℕ
  | 0 => 0
  | m + 1 =>
    let r := buildMask n g m
    let v := if m % 2 = 0 then (rowStep^[m / 2] r).testBit (2 * n - 1) else g.testBit (m / 2)
    if v then r ||| 2 ^ (2 * n - 1 - m) else r

/-- Setting a white bit of a mask is a single-cell update of the row. -/
theorem maskConfig_set (o r b : ℕ) (v : Bool) (hb : r.testBit b = false) :
    maskConfig o (if v then r ||| 2 ^ b else r) =
      Function.update (maskConfig o r) ((b : ℤ) - o) v := by
  funext c
  by_cases hc : c = (b : ℤ) - o
  · subst hc
    rw [Function.update_self]
    simp only [maskConfig, sub_add_cancel, Int.toNat_natCast, Nat.cast_nonneg, if_true]
    cases v <;> simp [Nat.testBit_or, hb]
  · rw [Function.update_of_ne hc]
    cases v
    · rfl
    · simp only [maskConfig, if_true]
      split_ifs with h0
      · rw [Nat.testBit_or, Nat.testBit_two_pow]
        have : ¬ (b = (c + o).toNat) := by omega
        simp [this]
      · rfl

/-- **The mask scan computes the specification scan.** -/
theorem maskConfig_buildMask (n g : ℕ) (hn : 1 ≤ n) (m : ℕ) (hm : m ≤ 2 * n - 1) :
    maskConfig n (buildMask n g m) = buildAux n (fun i => g.testBit i) m := by
  induction m with
  | zero =>
    funext c; simp [buildMask, buildAux, maskConfig]
  | succ m ih =>
    have ih' := ih (by omega)
    have hpos : ((2 * n - 1 - m : ℕ) : ℤ) - n = scanPos n m := by
      simp only [scanPos]; push_cast [show m ≤ 2 * n - 1 by omega, show 1 ≤ 2 * n by omega]; omega
    have hwhite : (buildMask n g m).testBit (2 * n - 1 - m) = false := by
      have h := congrFun ih' (scanPos n m)
      rw [buildAux_eq_false _ _ (Or.inl le_rfl)] at h
      rw [← h, maskConfig, if_pos (by simp only [scanPos]; omega)]
      congr 1; simp only [scanPos]; omega
    have hforced : ∀ k, 2 * k = m → (rowStep^[k] (buildMask n g m)).testBit (2 * n - 1) =
        evolve (buildAux n (fun i => g.testBit i) m) k ((n : ℤ) - 1 - (k : ℕ)) := by
      intro k hk
      rw [testBit_rowStep_iterate n _ k (2 * n - 1), ih']
      congr 1; push_cast [show 1 ≤ 2 * n by omega]; ring
    simp only [buildMask]
    rw [maskConfig_set _ _ _ _ hwhite, hpos, ih', buildAux]
    congr 1
    split_ifs with hpar
    · exact hforced (m / 2) (by omega)
    · rfl

/-- The reduced Boolean function, evaluated on masks. -/
theorem reducedPhi_eq_mask (n g : ℕ) (hn : 1 ≤ n) :
    reducedPhi n (fun i => g.testBit i) = (buildMask n g (2 * n - 1)).testBit 1 := by
  rw [reducedPhi, build, ← maskConfig_buildMask n g hn _ le_rfl, maskConfig,
    if_pos (by omega)]
  congr 1; omega

/-- The fast reduced count. -/
def fastReducedCount (n : ℕ) : ℕ :=
  countLoop (fun g => !(buildMask n g (2 * n - 1)).testBit 1) (2 ^ (n - 1)) 0

/-- **`whiteDiagonalCount n = fastReducedCount n`** (proved). -/
theorem whiteDiagonalCount_eq_fastReduced (n : ℕ) (hn : 1 ≤ n) :
    whiteDiagonalCount n = fastReducedCount n := by
  rw [whiteDiagonalCount_eq_reduced hn, fastReducedCount, countLoop_spec, zero_add]
  congr 1
  apply filter_congr
  intro g _
  rw [reducedPhi_eq_mask n g hn]
  cases (buildMask n g (2 * n - 1)).testBit 1 <;> simp

/-! ## The computation -/

theorem fastReducedCount_odd_2_16 : ∀ n ∈ Icc (2 : ℕ) 16, fastReducedCount n % 2 = 1 := by
  native_decide

theorem fastReducedCount_odd_17 : fastReducedCount 17 % 2 = 1 := by native_decide
theorem fastReducedCount_odd_18 : fastReducedCount 18 % 2 = 1 := by native_decide
theorem fastReducedCount_odd_19 : fastReducedCount 19 % 2 = 1 := by native_decide
theorem fastReducedCount_odd_20 : fastReducedCount 20 % 2 = 1 := by native_decide

theorem fastReducedCount_odd (n : ℕ) (hn : n ∈ Icc (2 : ℕ) 20) : fastReducedCount n % 2 = 1 := by
  obtain ⟨h1, h2⟩ := mem_Icc.mp hn
  by_cases h16 : n ≤ 16
  · exact fastReducedCount_odd_2_16 n (mem_Icc.mpr ⟨h1, h16⟩)
  · interval_cases n
    · exact fastReducedCount_odd_17
    · exact fastReducedCount_odd_18
    · exact fastReducedCount_odd_19
    · exact fastReducedCount_odd_20

/-- **The top-monomial coefficient is `1` for `2 ≤ n ≤ 20`.** -/
theorem anfCoeff_topMonomial_upto20 (n : ℕ) (hn : n ∈ Icc (2 : ℕ) 20) :
    anfCoeff (fun x => evolve x n 0) (topMonomial n) = 1 := by
  have h := mem_Icc.mp hn
  rw [anfCoeff_topMonomial_eq_count n (by omega), whiteDiagonalCount_eq_fastReduced n (by omega),
    ZMod.natCast_eq_one_iff_odd, Nat.odd_iff]
  exact fastReducedCount_odd n hn

/-- **`deg a(n)(0) = 2n − 1` for every `2 ≤ n ≤ 20`.** -/
theorem anfDegree_eq_upto20 (n : ℕ) (hn : n ∈ Icc (2 : ℕ) 20) :
    AnfDegreeEq (fun x => evolve x n 0) (2 * n - 1) := by
  have h := mem_Icc.mp hn
  exact ⟨center_anfDegree_le n h.1, topMonomial n, topMonomial_card n h.1,
    anfCoeff_topMonomial_upto20 n hn⟩

end GLM.Rule30
