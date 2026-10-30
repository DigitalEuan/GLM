module

public import Mathlib

/-!
# Folds with a hole: order statistics and ranks bounded where the register is silent

Round four of the stepwise planner (`glm_universal.runtime.stepwise`, Phase 85,
`studies/HOLE_FOLDS_STUDY.md`) answers the median and the rank of a column
with missing readings as an exact interval, answers a single value when the
interval closes, and refuses `COLUMN_HOLE` when a side is left open.  This file
proves the rule those answers rest on.

A column is the list `P` of the readings that are present with the list `H`
of the missing ones appended; `H` is unknown, and only its length `h` is a
fact about the register.

* **Counting** (`kth_le_iff`): the `k`-th smallest reading (0-based) is at
  most `v` exactly when more than `k` readings are at most `v`.
* **The two bounds** (`kth_append_le`, `le_kth_append`): whatever the missing
  readings are, the `k`-th smallest of the whole column lies between the
  `(k - h)`-th and the `k`-th smallest of the present readings.
* **Both bounds are attained** (`kth_append_eq_low`, `kth_append_eq_high`,
  `kth_fill_below`): filling every hole below the present readings attains
  the lower bound, and filling every hole above the `k`-th present reading
  attains the upper — so the interval the planner answers is the smallest
  one that is right for every completion.
* **An open side** (`kth_fill_const_low`, `kth_fill_const_high`): when
  `k < h`, a completion puts the `k`-th smallest at any value below every
  reading, and when `k` is past the present readings, at any value above
  every reading — which is why the largest value of a column with a hole,
  and a median with too many holes on one side, are refused.
* **The rank** (`rank_append_bounds`, `rank_append_eq_low`,
  `rank_append_eq_high`): the rank of a reading, largest first, is one more
  than the number of readings strictly above it; with `h` holes it lies
  between its present rank and that plus `h`, and both ends are attained.
* **The median of an even count** (`mid_bounds`): the mean of two bounded
  middle values is bounded by the means of their bounds.
-/

namespace GLM.HoleBounds

/-- The readings in increasing order. -/
public def sorted (L : List ℚ) : List ℚ := L.mergeSort (fun a b => decide (a ≤ b))

/-- The `k`-th smallest reading, counting from `0`. -/
public def kth (L : List ℚ) (k : ℕ) : ℚ := (sorted L).getD k 0

/-- How many readings are at most `v`. -/
public def countLE (L : List ℚ) (v : ℚ) : ℕ := L.countP (fun x => decide (x ≤ v))

/-- The rank of a reading `x` in a column, largest first, ties sharing the
better rank: one more than the number of readings strictly above it. -/
public def rankOf (x : ℚ) (L : List ℚ) : ℕ := 1 + L.countP (fun y => decide (x < y))

lemma sorted_perm (L : List ℚ) : (sorted L).Perm L := List.mergeSort_perm _ _

lemma sorted_pairwise (L : List ℚ) : (sorted L).Pairwise (· ≤ ·) := by
  have h := List.pairwise_mergeSort (le := fun a b : ℚ => decide (a ≤ b))
    (fun a b c hab hbc => by simp only [decide_eq_true_eq] at *; exact le_trans hab hbc)
    (fun a b => by simpa using le_total a b) L
  exact h.imp (fun hab => by simpa using hab)

lemma sorted_length (L : List ℚ) : (sorted L).length = L.length :=
  (sorted_perm L).length_eq

lemma countLE_sorted (L : List ℚ) (v : ℚ) :
    (sorted L).countP (fun x => decide (x ≤ v)) = countLE L v :=
  (sorted_perm L).countP_eq _

/-- The counting characterisation on a list that is already in order. -/
lemma getElem_le_iff_of_pairwise :
    ∀ (s : List ℚ), s.Pairwise (· ≤ ·) → ∀ (k : ℕ) (hk : k < s.length) (v : ℚ),
      s[k] ≤ v ↔ k + 1 ≤ s.countP (fun x => decide (x ≤ v))
  | [], _, k, hk, _ => by simp at hk
  | a :: t, hs, k, hk, v => by
    rw [List.pairwise_cons] at hs
    obtain ⟨ha, ht⟩ := hs
    rw [List.countP_cons]
    cases k with
    | zero =>
      simp only [List.getElem_cons_zero, zero_add]
      constructor
      · intro h; simp [h]
      · intro h
        by_contra hav
        push_neg at hav
        have hz : t.countP (fun x => decide (x ≤ v)) = 0 := by
          rw [List.countP_eq_zero]
          intro x hx
          have := ha x hx
          simp only [decide_eq_true_eq, not_le]
          exact lt_of_lt_of_le hav this
        simp [hz, not_le.mpr hav] at h
    | succ k =>
      simp only [List.getElem_cons_succ]
      have hk' : k < t.length := by simpa using hk
      rw [getElem_le_iff_of_pairwise t ht k hk' v]
      constructor
      · intro h
        have hav : a ≤ v := by
          by_contra hav
          push_neg at hav
          have hz : t.countP (fun x => decide (x ≤ v)) = 0 := by
            rw [List.countP_eq_zero]
            intro x hx
            simp only [decide_eq_true_eq, not_le]
            exact lt_of_lt_of_le hav (ha x hx)
          omega
        simp [hav]; omega
      · intro h
        split_ifs at h <;> omega

/-- **Counting.** The `k`-th smallest reading is at most `v` exactly when more
than `k` readings are at most `v`. -/
public theorem kth_le_iff (L : List ℚ) (k : ℕ) (hk : k < L.length) (v : ℚ) :
    kth L k ≤ v ↔ k + 1 ≤ countLE L v := by
  have hk' : k < (sorted L).length := by rw [sorted_length]; exact hk
  unfold kth
  rw [List.getD_eq_getElem _ _ hk', ← countLE_sorted]
  exact getElem_le_iff_of_pairwise _ (sorted_pairwise L) k hk' v

/-- The `k`-th smallest reading is one of the readings. -/
public theorem kth_mem (L : List ℚ) (k : ℕ) (hk : k < L.length) : kth L k ∈ L := by
  have hk' : k < (sorted L).length := by rw [sorted_length]; exact hk
  unfold kth
  rw [List.getD_eq_getElem _ _ hk']
  exact (sorted_perm L).subset (List.getElem_mem hk')

lemma countLE_append (P H : List ℚ) (v : ℚ) :
    countLE (P ++ H) v = countLE P v + countLE H v := by
  simp [countLE, List.countP_append]

lemma countLE_le_length (L : List ℚ) (v : ℚ) : countLE L v ≤ L.length :=
  List.countP_le_length

/-- **The upper bound.** Whatever the missing readings are, the `k`-th smallest
of the whole column is at most the `k`-th smallest present reading. -/
public theorem kth_append_le (P H : List ℚ) (k : ℕ) (hk : k < P.length) :
    kth (P ++ H) k ≤ kth P k := by
  have hk' : k < (P ++ H).length := by simp; omega
  rw [kth_le_iff _ _ hk', countLE_append]
  have := (kth_le_iff P k hk (kth P k)).1 le_rfl
  omega

/-- **The lower bound.** With `h` readings missing, the `k`-th smallest of the
whole column is at least the `(k - h)`-th smallest present reading. -/
public theorem le_kth_append (P H : List ℚ) (k : ℕ) (hh : H.length ≤ k)
    (hk : k - H.length < P.length) :
    kth P (k - H.length) ≤ kth (P ++ H) k := by
  have hk' : k < (P ++ H).length := by simp; omega
  by_contra hlt
  push_neg at hlt
  set v := kth (P ++ H) k
  have h1 := (kth_le_iff _ _ hk' v).1 le_rfl
  rw [countLE_append] at h1
  have h2 := countLE_le_length H v
  have h3 : k - H.length + 1 ≤ countLE P v := by omega
  exact absurd ((kth_le_iff P _ hk v).2 h3) (not_le.mpr hlt)

/-- **The lower bound is attained**: when every missing reading is at most the
`(k - h)`-th present reading, the `k`-th smallest is exactly that reading. -/
public theorem kth_append_eq_low (P H : List ℚ) (k : ℕ) (hh : H.length ≤ k)
    (hk : k - H.length < P.length) (hlow : ∀ x ∈ H, x ≤ kth P (k - H.length)) :
    kth (P ++ H) k = kth P (k - H.length) := by
  refine le_antisymm ?_ (le_kth_append P H k hh hk)
  have hk' : k < (P ++ H).length := by simp; omega
  rw [kth_le_iff _ _ hk', countLE_append]
  have h1 := (kth_le_iff P _ hk (kth P (k - H.length))).1 le_rfl
  have h2 : countLE H (kth P (k - H.length)) = H.length := by
    unfold countLE
    rw [List.countP_eq_length]
    intro x hx
    simpa using hlow x hx
  omega

/-- **The upper bound is attained**: when every missing reading is above the
`k`-th present reading, the `k`-th smallest is exactly that reading. -/
public theorem kth_append_eq_high (P H : List ℚ) (k : ℕ) (hk : k < P.length)
    (hhigh : ∀ x ∈ H, kth P k < x) :
    kth (P ++ H) k = kth P k := by
  refine le_antisymm (kth_append_le P H k hk) ?_
  have hk' : k < (P ++ H).length := by simp; omega
  by_contra hlt
  push_neg at hlt
  set v := kth (P ++ H) k
  have h1 := (kth_le_iff _ _ hk' v).1 le_rfl
  rw [countLE_append] at h1
  have h2 : countLE H v = 0 := by
    unfold countLE
    rw [List.countP_eq_zero]
    intro x hx
    have := hhigh x hx
    simp only [decide_eq_true_eq, not_le]
    exact lt_trans hlt this
  exact absurd ((kth_le_iff P k hk v).2 (by omega)) (not_le.mpr hlt)

/-- **One completion attains every lower bound at once**: filling every hole
below every present reading puts each order statistic on its lower bound. -/
public theorem kth_fill_below (P H : List ℚ) (k : ℕ) (hh : H.length ≤ k)
    (hk : k - H.length < P.length) (hbelow : ∀ x ∈ H, ∀ y ∈ P, x ≤ y) :
    kth (P ++ H) k = kth P (k - H.length) :=
  kth_append_eq_low P H k hh hk
    (fun x hx => hbelow x hx _ (kth_mem P _ hk))

/-- **An open side below**: when `k < h`, filling the holes with any value `c`
at most every present reading puts the `k`-th smallest at `c` — so no lower
bound holds for every completion. -/
public theorem kth_fill_const_low (P : List ℚ) (h k : ℕ) (hk : k < h) (c : ℚ)
    (hc : ∀ y ∈ P, c ≤ y) :
    kth (P ++ List.replicate h c) k = c := by
  have hk' : k < (P ++ List.replicate h c).length := by simp; omega
  apply le_antisymm
  · rw [kth_le_iff _ _ hk', countLE_append]
    have : countLE (List.replicate h c) c = h := by
      simp [countLE, List.countP_replicate]
    omega
  · by_contra hlt
    push_neg at hlt
    set v := kth (P ++ List.replicate h c) k
    have h1 := (kth_le_iff _ _ hk' v).1 le_rfl
    have hz : countLE (P ++ List.replicate h c) v = 0 := by
      unfold countLE
      rw [List.countP_eq_zero]
      intro x hx
      simp only [decide_eq_true_eq, not_le]
      rcases List.mem_append.1 hx with hx | hx
      · exact lt_of_lt_of_le hlt (hc x hx)
      · rw [List.eq_of_mem_replicate hx]; exact hlt
    omega

/-- **An open side above**: when `k` is past the present readings, filling the
holes with any value `c` at least every present reading puts the `k`-th
smallest at `c` — so no upper bound holds for every completion.  The largest
value of a column with a hole is always of this kind. -/
public theorem kth_fill_const_high (P : List ℚ) (h k : ℕ) (hPk : P.length ≤ k)
    (hk : k < P.length + h) (c : ℚ) (hc : ∀ y ∈ P, y ≤ c) :
    kth (P ++ List.replicate h c) k = c := by
  have hk' : k < (P ++ List.replicate h c).length := by simp; omega
  apply le_antisymm
  · rw [kth_le_iff _ _ hk', countLE_append]
    have h1 : countLE P c = P.length := by
      unfold countLE
      rw [List.countP_eq_length]
      intro x hx; simpa using hc x hx
    have h2 : countLE (List.replicate h c) c = h := by
      simp [countLE, List.countP_replicate]
    omega
  · by_contra hlt
    push_neg at hlt
    set v := kth (P ++ List.replicate h c) k
    have h1 := (kth_le_iff _ _ hk' v).1 le_rfl
    rw [countLE_append] at h1
    have h2 : countLE (List.replicate h c) v = 0 := by
      unfold countLE
      rw [List.countP_eq_zero]
      intro x hx
      rw [List.eq_of_mem_replicate hx]
      simpa using hlt
    have h3 := countLE_le_length P v
    omega

/-- **The rank, bounded.** With `h` readings missing, the rank of a reading lies
between its rank among the present readings and that plus `h`. -/
public theorem rank_append_bounds (x : ℚ) (P H : List ℚ) :
    rankOf x P ≤ rankOf x (P ++ H) ∧ rankOf x (P ++ H) ≤ rankOf x P + H.length := by
  unfold rankOf
  rw [List.countP_append]
  have := List.countP_le_length (p := fun y => decide (x < y)) (l := H)
  constructor <;> omega

/-- The present rank is attained when every hole is at most the reading. -/
public theorem rank_append_eq_low (x : ℚ) (P H : List ℚ) (hlow : ∀ y ∈ H, y ≤ x) :
    rankOf x (P ++ H) = rankOf x P := by
  unfold rankOf
  rw [List.countP_append]
  have : H.countP (fun y => decide (x < y)) = 0 := by
    rw [List.countP_eq_zero]
    intro y hy
    simpa using hlow y hy
  omega

/-- The present rank plus `h` is attained when every hole is above the reading. -/
public theorem rank_append_eq_high (x : ℚ) (P H : List ℚ) (hhigh : ∀ y ∈ H, x < y) :
    rankOf x (P ++ H) = rankOf x P + H.length := by
  unfold rankOf
  rw [List.countP_append]
  have : H.countP (fun y => decide (x < y)) = H.length := by
    rw [List.countP_eq_length]
    intro y hy
    simpa using hhigh y hy
  omega

/-- **The median of an even count**: the mean of two middle values, each
bounded, is bounded by the means of the bounds. -/
public theorem mid_bounds {a b c d x y : ℚ} (hx : a ≤ x ∧ x ≤ b) (hy : c ≤ y ∧ y ≤ d) :
    (a + c) / 2 ≤ (x + y) / 2 ∧ (x + y) / 2 ≤ (b + d) / 2 := by
  constructor <;> linarith [hx.1, hx.2, hy.1, hy.2]

/-! ## A worked column

Six rows, five readings present and one missing (`h = 1`), as the halogens'
density column is in the register.  The 3rd smallest of the whole column
(index 2) lies between the 2nd and 3rd smallest present readings, whatever
the missing reading is; here it is filled with `100`. -/

example : kth [1, 2, 3, 5, 7] 1 ≤ kth ([1, 2, 3, 5, 7] ++ [100]) 2 ∧
    kth ([1, 2, 3, 5, 7] ++ [100]) 2 ≤ kth [1, 2, 3, 5, 7] 2 :=
  ⟨by simpa using le_kth_append [1, 2, 3, 5, 7] [100] 2 (by simp) (by simp),
   kth_append_le _ _ 2 (by simp)⟩

end GLM.HoleBounds
