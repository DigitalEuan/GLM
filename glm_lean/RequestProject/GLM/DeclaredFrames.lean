module

public import Mathlib
public import RequestProject.GLM.HoleBounds

/-!
# Frames from a declaration: the bounds round five of the stepwise planner answers

Round five of the stepwise planner (`glm_universal.runtime.frame_declarations`,
Phase 91, `studies/DECLARED_FRAMES_STUDY.md`) generates its fold frames from one
declaration and adds, as entries in it, further order statistics, superlatives
and the top `k`, and *the bounds on* a sum, a mean or a parity count over a
column with missing readings.  This file proves the statements those answers
rest on.  As in `GLM.HoleBounds`, a column is the list `P` of readings present
with the list `H` of missing ones appended; only `H`'s length is a fact about
the register.

* **A parity count under holes** (`countP_append_bounds`,
  `countP_fill_low`, `countP_fill_high`): the number of readings with a
  property lies between the present count and that plus `h`, and both ends
  are attained — by filling every hole with a value without the property,
  and with one with it.  For integer readings and oddness the two fills are
  `0` and `1` (`oddCount_fill_even`, `oddCount_fill_odd`).
* **A sum under a declared range** (`sum_append_bounds`,
  `sum_fill_const`): when every missing reading lies in `[L, U]`, the sum lies
  between `S + hL` and `S + hU`, attained by filling every hole at `L` (`U`);
  the mean likewise over the count (`mean_append_bounds`).
* **The positions an order fold reads** (`quartilePositions_lt`,
  `kthLargest_pos_lt`): the quartile positions (the median of the lower or
  upper half, the middle value left out of both halves when the count is odd)
  and the position of the `k`-th largest lie inside the column, so
  `GLM.HoleBounds.kth_append_le` and `GLM.HoleBounds.le_kth_append` bound
  each of them under holes (`orderStat_bounds`).
* **The top `k` under a hole** (`top_open`): a missing reading filled above a
  present row's reading moves that row's rank down by one, while filled below
  it leaves the rank as it is — so whether a present row is in the top `k`
  depends on the completion, which is why the top `k` of a column with a hole
  is refused and answered only over the present rows.
-/

namespace GLM.DeclaredFrames

open GLM.HoleBounds

/-! ## A parity count under holes -/

/-- **A count, bounded.** With `h` readings missing, the number of readings with
a property lies between the present count and that plus `h`. -/
public theorem countP_append_bounds {α : Type*} (p : α → Bool) (P H : List α) :
    P.countP p ≤ (P ++ H).countP p ∧ (P ++ H).countP p ≤ P.countP p + H.length := by
  rw [List.countP_append]
  have := List.countP_le_length (p := p) (l := H)
  constructor <;> omega

/-- The present count is attained when no hole has the property. -/
public theorem countP_fill_low {α : Type*} (p : α → Bool) (P : List α) (h : ℕ) (a : α)
    (ha : p a = false) : (P ++ List.replicate h a).countP p = P.countP p := by
  rw [List.countP_append, List.countP_replicate]
  simp [ha]

/-- The present count plus `h` is attained when every hole has the property. -/
public theorem countP_fill_high {α : Type*} (p : α → Bool) (P : List α) (h : ℕ) (a : α)
    (ha : p a = true) : (P ++ List.replicate h a).countP p = P.countP p + h := by
  rw [List.countP_append, List.countP_replicate]
  simp [ha]

/-- The number of odd readings of an integer column. -/
public def oddCount (L : List ℤ) : ℕ := L.countP (fun x => decide (Odd x))

/-- Filling every hole with `0` (even) attains the low end of the odd count. -/
public theorem oddCount_fill_even (P : List ℤ) (h : ℕ) :
    oddCount (P ++ List.replicate h 0) = oddCount P := by
  unfold oddCount
  exact countP_fill_low _ P h 0 (by decide)

/-- Filling every hole with `1` (odd) attains the high end of the odd count. -/
public theorem oddCount_fill_odd (P : List ℤ) (h : ℕ) :
    oddCount (P ++ List.replicate h 1) = oddCount P + h := by
  unfold oddCount
  exact countP_fill_high _ P h 1 (by decide)

/-- Whatever the missing readings, the odd count lies between the present
count and that plus `h`. -/
public theorem oddCount_append_bounds (P H : List ℤ) :
    oddCount P ≤ oddCount (P ++ H) ∧ oddCount (P ++ H) ≤ oddCount P + H.length :=
  countP_append_bounds _ P H

/-! ## A sum and a mean under a declared range -/

lemma sum_bounds_of_mem {L U : ℚ} :
    ∀ H : List ℚ, (∀ y ∈ H, L ≤ y ∧ y ≤ U) →
      (H.length : ℚ) * L ≤ H.sum ∧ H.sum ≤ (H.length : ℚ) * U
  | [], _ => by simp
  | a :: t, hH => by
    have ha := hH a (by simp)
    have ht := sum_bounds_of_mem t (fun y hy => hH y (by simp [hy]))
    simp only [List.length_cons, List.sum_cons, Nat.cast_succ]
    constructor <;> nlinarith [ha.1, ha.2, ht.1, ht.2]

/-- **A sum, bounded through a declared range.** When every missing reading
lies in `[L, U]`, the sum of the whole column lies between `S + hL` and
`S + hU`, with `S` the sum of the readings present. -/
public theorem sum_append_bounds (P H : List ℚ) (L U : ℚ)
    (hH : ∀ y ∈ H, L ≤ y ∧ y ≤ U) :
    P.sum + (H.length : ℚ) * L ≤ (P ++ H).sum ∧
      (P ++ H).sum ≤ P.sum + (H.length : ℚ) * U := by
  rw [List.sum_append]
  have := sum_bounds_of_mem H hH
  constructor <;> linarith [this.1, this.2]

/-- **Both ends are attained**: filling every hole with the same value `c`
gives the sum `S + hc`; `c = L` and `c = U` give the two ends. -/
public theorem sum_fill_const (P : List ℚ) (h : ℕ) (c : ℚ) :
    (P ++ List.replicate h c).sum = P.sum + (h : ℚ) * c := by
  rw [List.sum_append, List.sum_replicate, nsmul_eq_mul]

/-- **A mean, bounded through a declared range**: the sum's bounds over the
count of the whole column. -/
public theorem mean_append_bounds (P H : List ℚ) (L U : ℚ)
    (hH : ∀ y ∈ H, L ≤ y ∧ y ≤ U) (hn : 0 < P.length + H.length) :
    (P.sum + (H.length : ℚ) * L) / ((P.length + H.length : ℕ) : ℚ) ≤
        (P ++ H).sum / ((P ++ H).length : ℚ) ∧
      (P ++ H).sum / ((P ++ H).length : ℚ) ≤
        (P.sum + (H.length : ℚ) * U) / ((P.length + H.length : ℕ) : ℚ) := by
  have hb := sum_append_bounds P H L U hH
  have hlen : ((P ++ H).length : ℚ) = ((P.length + H.length : ℕ) : ℚ) := by simp
  rw [hlen]
  have hpos : (0 : ℚ) < ((P.length + H.length : ℕ) : ℚ) := by exact_mod_cast hn
  constructor
  · exact div_le_div_of_nonneg_right hb.1 hpos.le
  · exact div_le_div_of_nonneg_right hb.2 hpos.le

/-! ## The positions an order fold reads -/

/-- The middle positions of a column of `m`: one for an odd count, two for an
even one. -/
public def midPositions (m : ℕ) : List ℕ :=
  if m % 2 = 1 then [m / 2] else [m / 2 - 1, m / 2]

/-- The quartile positions over a column of `n` (0-based, ascending order): the
middle of the lower half `[0, n / 2)`, or of the upper half `[n - n / 2, n)`;
the middle value of an odd count is in neither half. -/
public def quartilePositions (upper : Bool) (n : ℕ) : List ℕ :=
  (midPositions (n / 2)).map (fun p => (if upper then n - n / 2 else 0) + p)

lemma midPositions_lt (m : ℕ) (hm : 0 < m) : ∀ p ∈ midPositions m, p < m := by
  intro p hp
  unfold midPositions at hp
  split_ifs at hp with h
  · simp at hp; omega
  · simp at hp; omega

/-- **The quartile positions lie inside the column** (for a column of at least
two readings), so the order-statistic bound applies at each. -/
public theorem quartilePositions_lt (upper : Bool) (n : ℕ) (hn : 2 ≤ n) :
    ∀ p ∈ quartilePositions upper n, p < n := by
  intro p hp
  unfold quartilePositions at hp
  rw [List.mem_map] at hp
  obtain ⟨q, hq, rfl⟩ := hp
  have hm : 0 < n / 2 := by omega
  have := midPositions_lt (n / 2) hm q hq
  cases upper <;> simp <;> omega

/-- The lower quartile reads only positions of the lower half, the upper only
positions of the upper half; neither reads the middle of an odd count. -/
public theorem quartile_halves (n : ℕ) (hn : 2 ≤ n) :
    (∀ p ∈ quartilePositions false n, p < n / 2) ∧
      (∀ p ∈ quartilePositions true n, n - n / 2 ≤ p) := by
  have hm : 0 < n / 2 := by omega
  constructor
  · intro p hp
    unfold quartilePositions at hp
    rw [List.mem_map] at hp
    obtain ⟨q, hq, rfl⟩ := hp
    have := midPositions_lt (n / 2) hm q hq
    simp; omega
  · intro p hp
    unfold quartilePositions at hp
    rw [List.mem_map] at hp
    obtain ⟨q, hq, rfl⟩ := hp
    simp

/-- **The `k`-th largest lies inside the column**: for `1 ≤ k ≤ n` its
position `n - k` is a position of the column, and `k > n` is the refusal
`ORDER_OUT_OF_RANGE`. -/
public theorem kthLargest_pos_lt (n k : ℕ) (hk1 : 1 ≤ k) (hkn : k ≤ n) : n - k < n := by
  omega

/-- **Every order fold of round five is bounded under holes by the rule of
round four**: at any position `p` of the completed column, the reading lies
between the present readings at `p - h` and `p` whenever both exist. -/
public theorem orderStat_bounds (P H : List ℚ) (p : ℕ) (hh : H.length ≤ p)
    (hp : p < P.length) :
    kth P (p - H.length) ≤ kth (P ++ H) p ∧ kth (P ++ H) p ≤ kth P p :=
  ⟨le_kth_append P H p hh (by omega), kth_append_le P H p hp⟩

/-! ## The top `k` under a hole -/

/-- **The top `k` under a hole is open.** A non-empty set of missing readings
filled above a present reading `x` gives `x` a rank larger than it has when
they are filled at or below it — so whether `x` is among the first `k` depends
on the completion. -/
public theorem top_open (x : ℚ) (P Hhigh Hlow : List ℚ) (hne : Hhigh ≠ [])
    (hhigh : ∀ y ∈ Hhigh, x < y) (hlow : ∀ y ∈ Hlow, y ≤ x) :
    rankOf x (P ++ Hlow) < rankOf x (P ++ Hhigh) := by
  rw [rank_append_eq_low x P Hlow hlow, rank_append_eq_high x P Hhigh hhigh]
  have : 0 < Hhigh.length := List.length_pos_iff.mpr hne
  omega

/-- A present row ranked exactly `k` among the present readings drops out of
the top `k` when one hole is filled above it. -/
public theorem top_drops (x M : ℚ) (P : List ℚ) (k : ℕ) (hx : rankOf x P = k)
    (hM : x < M) : k < rankOf x (P ++ [M]) := by
  rw [rank_append_eq_high x P [M] (by simpa using hM)]
  simp; omega

/-! ## The register's figures

The noble gases' Pauling electronegativity: two readings present (krypton
3.00, xenon 2.60) and five missing, each declared in `[0, 3.98]`; the mean is
answered between `4/5` and `51/14`, and both ends are attained. -/

example : ((([3, 13/5] : List ℚ) ++ List.replicate 5 0).sum) / 7 = 4 / 5 := by
  norm_num

example : ((([3, 13/5] : List ℚ) ++ List.replicate 5 (398/100)).sum) / 7 = 51 / 14 := by
  norm_num

end GLM.DeclaredFrames
