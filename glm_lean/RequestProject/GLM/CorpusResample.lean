module

public import Mathlib

/-!
# The declared resampling: what makes reading a sub-corpus off the census exact

`studies/CORPUS_RESAMPLE_STUDY.md` (Phase 100) resamples the Lean-corpus
retrieval figures: every sub-corpus that drops one Lean file, and every
offset of the query sample's stride.  The computational half is
`overlay/glm_universal/reasoning/corpus_resample.py`.  It ranks every query
once over the whole corpus and reads each sub-corpus's ranking off that one
ranking by filtering.  This file proves why that is exact, why a bounded
prefix of the census is enough, why the stride offsets are a partition, and
the sign-test arithmetic the study prints.

## 1.  Dropping candidates commutes with the ranking

Every ranking of the study is a sort by a strict order in which no two
candidates tie (the name is the last key).  `sorted_perm_filter_eq`: a list
sorted by such an order that is a permutation of the filtered full ranking
*is* the filtered full ranking.  So ranking the sub-corpus directly and
filtering the census give the same list (`take_sorted_perm_filter_eq` for the
top `k`).

## 2.  A bounded prefix is enough

`take_filter_take`: if at most `m` candidates are dropped, the top `k` of the
filtered ranking can be read off the first `k + m` places of the full ranking.
The census keeps the largest file's size plus ten places.

## 3.  The stride offsets partition the census

`stride_slice_iff`: Python's slice `names[o::s]` is the set of indices with
remainder `o`.  `stride_offsets_card`: over all offsets the slices count every
index exactly once.

## 4.  The sign test

`signTest b c` is the exact two-sided sign-test value of a discordance
`(b, c)`; `signTest_symm` says it does not care which ranking is named first,
and `signTest_le_one` that it is a probability bound.
-/

@[expose] public section

namespace GLM.CorpusResample

open Finset

/-! ## 1.  Dropping candidates commutes with the ranking -/

section Filter

variable {α : Type*}

/-- **The sub-corpus ranking is the filtered census.**  If `r` admits no two
candidates in both orders (a strict order with the name as the last key), a
list sorted by `r` holding exactly the candidates of `l.filter p` is
`l.filter p` itself, whenever `l` is sorted by `r`. -/
theorem sorted_perm_filter_eq {r : α → α → Prop}
    (hasymm : ∀ a b, r a b → ¬ r b a) (p : α → Bool) {l s : List α}
    (hl : l.Pairwise r) (hs : s.Pairwise r) (hperm : s.Perm (l.filter p)) :
    s = l.filter p :=
  List.Perm.eq_of_pairwise (le := r)
    (fun a b _ _ hab hba => absurd hba (hasymm a b hab)) hs (hl.filter p) hperm

/-- The top `k` of a direct ranking of the sub-corpus are the top `k` of the
filtered census. -/
theorem take_sorted_perm_filter_eq {r : α → α → Prop}
    (hasymm : ∀ a b, r a b → ¬ r b a) (p : α → Bool) {l s : List α} (k : ℕ)
    (hl : l.Pairwise r) (hs : s.Pairwise r) (hperm : s.Perm (l.filter p)) :
    s.take k = (l.filter p).take k := by
  rw [sorted_perm_filter_eq hasymm p hl hs hperm]

end Filter

/-! ## 2.  A bounded prefix is enough -/

section Prefix

variable {α : Type*}

/-- Filtering a prefix of length `n` keeps at least `n` minus the number of
dropped candidates in the whole list, when the list is that long. -/
theorem length_filter_take_ge (p : α → Bool) (l : List α) (n : ℕ)
    (hn : n ≤ l.length) :
    n - (l.filter (fun a => !p a)).length ≤ ((l.take n).filter p).length := by
  have h1 : ((l.take n).filter p).length + ((l.take n).filter (fun a => !p a)).length
      = n := by
    rw [← List.length_eq_length_filter_add, List.length_take]
    omega
  have h2 : ((l.take n).filter (fun a => !p a)).length
      ≤ (l.filter (fun a => !p a)).length :=
    ((List.take_sublist n l).filter _).length_le
  omega

/-- **The census prefix is enough.**  If at most `m` candidates of `l` are
dropped, the top `k` of the filtered list are the top `k` of the filtered
first `k + m` places. -/
theorem take_filter_take (p : α → Bool) (l : List α) (k m : ℕ)
    (hm : (l.filter (fun a => !p a)).length ≤ m) :
    (l.filter p).take k = ((l.take (k + m)).filter p).take k := by
  by_cases hlen : k + m ≤ l.length
  · conv_lhs => rw [← List.take_append_drop (k + m) l]
    rw [List.filter_append, List.take_append_of_le_length]
    have := length_filter_take_ge p l (k + m) hlen
    omega
  · rw [List.take_of_length_le (l := l) (by omega)]

end Prefix

/-! ## 3.  The stride offsets partition the census -/

/-- Python's `names[o::s]` with `o < s`: index `i` is in the slice exactly
when its remainder by `s` is `o`. -/
theorem stride_slice_iff {s o i : ℕ} (ho : o < s) :
    (o ≤ i ∧ (i - o) % s = 0) ↔ i % s = o := by
  constructor
  · rintro ⟨hoi, hmod⟩
    obtain ⟨q, hq⟩ := Nat.dvd_of_mod_eq_zero hmod
    have : i = o + s * q := by omega
    rw [this, Nat.add_mul_mod_self_left, Nat.mod_eq_of_lt ho]
  · intro h
    refine ⟨?_, ?_⟩
    · rw [← h]; exact Nat.mod_le i s
    · have := Nat.mod_add_div i s
      have hi : i - o = s * (i / s) := by omega
      rw [hi, Nat.mul_mod_right]

/-- **The offsets are a partition.**  Over the offsets `0 … s - 1`, the slices
of `range n` count every index exactly once. -/
theorem stride_offsets_card (n s : ℕ) (hs : 0 < s) :
    ∑ o ∈ range s, ((range n).filter (fun i => i % s = o)).card = n := by
  rw [← card_eq_sum_card_fiberwise (f := fun i => i % s)]
  · exact card_range n
  · intro i _
    simpa using Nat.mod_lt i hs

/-- Two different offsets share no index. -/
theorem stride_offsets_disjoint (n s o₁ o₂ : ℕ) (h : o₁ ≠ o₂) :
    Disjoint ((range n).filter (fun i => i % s = o₁))
      ((range n).filter (fun i => i % s = o₂)) := by
  rw [disjoint_filter]
  intro i _ h1 h2
  exact h (h1 ▸ h2)

/-! ## 4.  The sign test -/

/-- The exact two-sided sign-test value of a discordance `(b, c)`:
`min 1 (2 · Σ_{i ≤ min b c} C(b + c, i) / 2^(b + c))`. -/
def signTest (b c : ℕ) : ℚ :=
  min 1 (2 * (∑ i ∈ range (min b c + 1), ((b + c).choose i : ℚ)) / 2 ^ (b + c))

/-- The sign test does not care which ranking is named first. -/
theorem signTest_symm (b c : ℕ) : signTest b c = signTest c b := by
  unfold signTest
  rw [min_comm b c, add_comm b c]

/-- The value is a probability bound: never above one. -/
theorem signTest_le_one (b c : ℕ) : signTest b c ≤ 1 := min_le_left _ _

/-! ### The values the study prints

The census discordances at `k = 5` of `studies/CORPUS_RESAMPLE_STUDY.md` §4,
each `(first only, second only)`.  The values are checked by the kernel. -/

/-- The discordances whose sign test is small: readings `a`, `c`, `f` and
`i` on both query sets. -/
theorem census_signs_small :
    signTest 161 94 < 1 / 10 ^ 4 ∧ signTest 140 92 < 1 / 500 ∧
    signTest 129 33 < 1 / 10 ^ 13 ∧ signTest 109 30 < 1 / 10 ^ 11 ∧
    signTest 138 31 < 1 / 10 ^ 16 ∧ signTest 111 30 < 1 / 10 ^ 11 ∧
    signTest 185 29 < 1 / 10 ^ 28 ∧ signTest 162 28 < 1 / 10 ^ 23 := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> decide +kernel

/-- Reading `d` on the declarations: the discordance `23 : 40` runs against
the native ranking, with a sign test between `0.042` and `0.043`. -/
theorem census_sign_d_declarations :
    21 / 500 ≤ signTest 23 40 ∧ signTest 23 40 < 43 / 1000 := by
  constructor <;> decide +kernel

/-- The discordances whose sign test is not small: readings `b`, `d` (goals),
`e`, `g` and `h`. -/
theorem census_signs_large :
    1 / 10 < signTest 44 59 ∧ 1 / 10 < signTest 49 57 ∧
    1 / 10 < signTest 31 34 ∧ 1 / 10 < signTest 42 53 ∧
    1 / 10 < signTest 47 49 ∧ 1 / 20 < signTest 72 50 ∧
    1 / 10 < signTest 47 60 := by
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> decide +kernel

/-- The control `j`: discordances `3 : 0` and `2 : 2`. -/
theorem census_signs_control : signTest 3 0 = 1 / 4 ∧ signTest 2 2 = 1 := by
  constructor <;> decide +kernel

end GLM.CorpusResample
