import Mathlib

/-!
# The third sort: count-first literals, CPython's slice reading, ranges

Round 7 of the order of work (`glm_universal.reasoning.reverse_tct_seq` and
`glm_universal.reasoning.python_containers`, Phase 94,
`studies/THIRD_SORT_STUDY.md`) adds strings, tuples and ranges to the reverse
grammar, each literal spelled with its count first, and widens the Python
dialect.  This file proves what the round rests on.

* **Count-first literals are uniquely readable** (`decItems_encItems`,
  `listCode`, `encLit_injective`): for any spelling of items that has a left
  inverse on its own prefix, the spelling *count, item, separator, item, …*
  of a list has a left inverse on its own prefix too.  So a literal followed
  by anything reads back to itself and leaves the rest untouched, and — since
  the literal's spelling is again such a code — a tuple of tuples of strings
  is as readable as a tuple of numbers.
* **A range is what the evaluator says it is** (`mem_rangeList_iff`,
  `two_mul_sum_rangeList`): for a positive step, `x` is an entry of
  `range(a, b, c)` exactly when `a ≤ x < b` and `c ∣ x − a` (the membership
  test the evaluator uses without listing the range), and twice the total of
  its `k` entries is `k · (2a + (k − 1)c)` (the closed form `sum` uses).
* **CPython's slice reading stays inside the sequence**
  (`slicePos_mem_bounds`, `sliceNeg_mem_bounds`): after the negative indices
  are read from the end and both ends are clamped, every index the slice reads
  lies in `0 … n − 1`, for a positive and for a negative step; and a
  positive-step slice reads `⌈(stop − start) / step⌉` indices after clamping
  (`length_slicePos`, with `lt_rangeLen_iff` saying that count is the
  ceiling).
* **ASCII case mapping** (`upper_lower_of_lower`, `lower_upper_of_upper`,
  `upper_idem`, `length_mapUpper`): it keeps the length, undoes itself on
  letters, and applying it twice is applying it once.
-/

namespace GLM.ThirdSort

/-! ## Count-first literals -/

/-- A spelling of items with a left inverse on its own prefix. -/
structure PrefixCode (W α : Type*) where
  enc : α → List W
  dec : List W → Option (α × List W)
  dec_enc : ∀ a rest, dec (enc a ++ rest) = some (a, rest)

variable {W α : Type*} [DecidableEq W]

/-- The items of a list, separated by `sep` (no count). -/
def encItems (c : PrefixCode W α) (sep : W) : List α → List W
  | [] => []
  | [a] => c.enc a
  | a :: b :: t => c.enc a ++ sep :: encItems c sep (b :: t)

/-- Read exactly `k` items separated by `sep`. -/
def decItems (c : PrefixCode W α) (sep : W) : ℕ → List W → Option (List α × List W)
  | 0, ws => some ([], ws)
  | 1, ws => (c.dec ws).map fun p => ([p.1], p.2)
  | n + 2, ws =>
    match c.dec ws with
    | none => none
    | some (a, r) =>
      match r with
      | [] => none
      | s :: r' =>
        if s = sep then (decItems c sep (n + 1) r').map fun p => (a :: p.1, p.2)
        else none

theorem decItems_encItems (c : PrefixCode W α) (sep : W) :
    ∀ (xs : List α) (rest : List W),
      decItems c sep xs.length (encItems c sep xs ++ rest) = some (xs, rest)
  | [], rest => by simp [decItems, encItems]
  | [a], rest => by simp [decItems, encItems, c.dec_enc]
  | a :: b :: t, rest => by
    have ih := decItems_encItems c sep (b :: t) rest
    simp only [List.length_cons] at ih ⊢
    simp only [decItems, encItems, List.append_assoc, List.cons_append,
      c.dec_enc]
    rw [ih]
    rfl

/-- The count-first literal: the count's spelling, then the items. -/
def encLit (n : PrefixCode W ℕ) (c : PrefixCode W α) (sep : W) (xs : List α) :
    List W :=
  n.enc xs.length ++ encItems c sep xs

/-- Read a count, then that many items. -/
def decLit (n : PrefixCode W ℕ) (c : PrefixCode W α) (sep : W) (ws : List W) :
    Option (List α × List W) :=
  match n.dec ws with
  | none => none
  | some (k, r) => decItems c sep k r

theorem decLit_encLit (n : PrefixCode W ℕ) (c : PrefixCode W α) (sep : W)
    (xs : List α) (rest : List W) :
    decLit n c sep (encLit n c sep xs ++ rest) = some (xs, rest) := by
  unfold decLit encLit
  rw [List.append_assoc, n.dec_enc]
  exact decItems_encItems c sep xs rest

/-- The count-first literal is itself a prefix code, so literals nest: a
tuple's entries may be tuples, strings or masks. -/
def listCode (n : PrefixCode W ℕ) (c : PrefixCode W α) (sep : W) :
    PrefixCode W (List α) where
  enc := encLit n c sep
  dec := decLit n c sep
  dec_enc := decLit_encLit n c sep

/-- No two lists share a literal. -/
theorem encLit_injective (n : PrefixCode W ℕ) (c : PrefixCode W α) (sep : W) :
    Function.Injective (encLit n c sep) := by
  intro xs ys h
  have hx := decLit_encLit n c sep xs []
  have hy := decLit_encLit n c sep ys []
  rw [h, hy] at hx
  exact (Prod.mk.inj (Option.some.inj hx)).1.symm

/-! ## Ranges -/

/-- The number of entries of `range(a, b, c)` for `c > 0`:
`⌈(b − a) / c⌉` when `a < b`, else zero. -/
def rangeLen (a b c : ℤ) : ℕ := if a < b then ((b - a + c - 1) / c).toNat else 0

/-- The entries of `range(a, b, c)`, `c > 0`. -/
def rangeList (a b c : ℤ) : List ℤ :=
  (List.range (rangeLen a b c)).map fun i : ℕ => a + (i : ℤ) * c

theorem length_rangeList (a b c : ℤ) : (rangeList a b c).length = rangeLen a b c := by
  simp [rangeList]

theorem lt_rangeLen_iff {a b c : ℤ} (hc : 0 < c) (i : ℕ) :
    i < rangeLen a b c ↔ a + i * c < b := by
  unfold rangeLen
  split_ifs with h
  · rw [Int.lt_toNat, Int.lt_iff_add_one_le, Int.le_ediv_iff_mul_le hc]
    constructor <;> intro h' <;> nlinarith
  · simp only [Nat.not_lt_zero, false_iff, not_lt]
    have : (0 : ℤ) ≤ i * c := by positivity
    omega

theorem mem_rangeList_iff {a b c : ℤ} (hc : 0 < c) (x : ℤ) :
    x ∈ rangeList a b c ↔ a ≤ x ∧ x < b ∧ c ∣ x - a := by
  unfold rangeList
  simp only [List.mem_map, List.mem_range]
  constructor
  · rintro ⟨i, hi, rfl⟩
    rw [lt_rangeLen_iff hc] at hi
    refine ⟨?_, hi, ⟨i, by ring⟩⟩
    have : (0 : ℤ) ≤ i * c := by positivity
    linarith
  · rintro ⟨h1, h2, ⟨q, hq⟩⟩
    have hq0 : 0 ≤ q := by
      by_contra hneg
      push_neg at hneg
      nlinarith
    refine ⟨q.toNat, ?_, ?_⟩
    · rw [lt_rangeLen_iff hc, Int.toNat_of_nonneg hq0]
      linarith
    · rw [Int.toNat_of_nonneg hq0]
      linarith

theorem two_mul_sum_rangeList (a b c : ℤ) :
    2 * (rangeList a b c).sum
      = (rangeLen a b c : ℤ) * (2 * a + ((rangeLen a b c : ℤ) - 1) * c) := by
  unfold rangeList
  generalize rangeLen a b c = k
  induction k with
  | zero => simp
  | succ k ih =>
    rw [List.range_succ, List.map_append, List.sum_append, mul_add, ih]
    simp
    ring

/-! ## CPython's slice reading -/

/-- Read a possibly negative index from the end, then clamp it to `lo … hi`. -/
def clampIdx (n lo hi : ℤ) (x : ℤ) : ℤ :=
  let y := if x < 0 then x + n else x
  min (max y lo) hi

theorem clampIdx_bounds {n lo hi : ℤ} (h : lo ≤ hi) (x : ℤ) :
    lo ≤ clampIdx n lo hi x ∧ clampIdx n lo hi x ≤ hi := by
  unfold clampIdx
  constructor
  · exact le_min (le_max_right _ _) h
  · exact min_le_right _ _

/-- The indices a positive-step slice reads: clamp both ends to `0 … n`, then
the progression from the start, short of the stop. -/
def slicePos (n start stop step : ℤ) : List ℤ :=
  rangeList (clampIdx n 0 n start) (clampIdx n 0 n stop) step

/-- A positive-step slice reads `⌈(stop − start) / step⌉` indices after
clamping (none when the clamped start is not below the clamped stop). -/
theorem length_slicePos (n start stop step : ℤ) :
    (slicePos n start stop step).length
      = if clampIdx n 0 n start < clampIdx n 0 n stop then
          ((clampIdx n 0 n stop - clampIdx n 0 n start + step - 1) / step).toNat
        else 0 := by
  simp [slicePos, length_rangeList, rangeLen]

theorem slicePos_mem_bounds {n start stop step : ℤ} (hn : 0 ≤ n) (hs : 0 < step)
    {i : ℤ} (hi : i ∈ slicePos n start stop step) : 0 ≤ i ∧ i < n := by
  unfold slicePos at hi
  rw [mem_rangeList_iff hs] at hi
  have h1 := clampIdx_bounds hn start (n := n)
  have h2 := clampIdx_bounds hn stop (n := n)
  omega

/-- The indices a negative-step slice reads: clamp both ends to `−1 … n − 1`,
then the progression downward from the start, above the stop.  It is the
mirror image of a positive-step reading. -/
def sliceNeg (n start stop step : ℤ) : List ℤ :=
  (rangeList (-clampIdx n (-1) (n - 1) start) (-clampIdx n (-1) (n - 1) stop)
    (-step)).map Neg.neg

theorem sliceNeg_mem_bounds {n start stop step : ℤ} (hn : 0 ≤ n) (hs : step < 0)
    {i : ℤ} (hi : i ∈ sliceNeg n start stop step) : 0 ≤ i ∧ i < n := by
  unfold sliceNeg at hi
  rw [List.mem_map] at hi
  obtain ⟨j, hj, rfl⟩ := hi
  rw [mem_rangeList_iff (by linarith)] at hj
  have h1 := clampIdx_bounds (show (-1 : ℤ) ≤ n - 1 by linarith) start (n := n)
  have h2 := clampIdx_bounds (show (-1 : ℤ) ≤ n - 1 by linarith) stop (n := n)
  omega

/-! ## ASCII case mapping -/

/-- `str.upper` on one ASCII code point. -/
def upper (c : ℕ) : ℕ := if 97 ≤ c ∧ c ≤ 122 then c - 32 else c

/-- `str.lower` on one ASCII code point. -/
def lower (c : ℕ) : ℕ := if 65 ≤ c ∧ c ≤ 90 then c + 32 else c

theorem upper_lower_of_lower {c : ℕ} (h1 : 97 ≤ c) (h2 : c ≤ 122) :
    lower (upper c) = c := by
  unfold upper lower
  split_ifs <;> omega

theorem lower_upper_of_upper {c : ℕ} (h1 : 65 ≤ c) (h2 : c ≤ 90) :
    upper (lower c) = c := by
  unfold upper lower
  split_ifs <;> omega

theorem upper_idem (c : ℕ) : upper (upper c) = upper c := by
  unfold upper
  split_ifs <;> omega

theorem length_mapUpper (s : List ℕ) : (s.map upper).length = s.length :=
  List.length_map _

end GLM.ThirdSort
