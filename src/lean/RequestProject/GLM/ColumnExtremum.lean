import Mathlib

/-!
# The extremum of a column — and the two ways a column has none

`GLM.CoordinateOrder` orders **two** readings of one coordinate.  The question
it stops short of names no rows at all: *which element is the most
electronegative?* is one coordinate across **every** row of a table, and the
answer is whichever row attains the end.

This file states that operation and proves what it is worth.  A `Cell` is one
row's answer for the coordinate: the row's name, the scale it was read on, and
either a value or nothing — a register that records a cell as missing gives
nothing, and that is the case the whole file is written around.

* The operation is silent exactly when the column was gathered from more than
  one scale, when it has a hole in it, or when it has no rows
  (`extremum_eq_none_iff`), so a refusal states a fact about the column rather
  than reporting a failed search.
* When it answers, the value it returns is one of the column's own
  (`extremum_value_mem`) and no reading exceeds it (`le_extremum`).
* It names **every** row that attains the end and only those
  (`mem_extremum_winners_iff`), and it always names at least one
  (`extremum_winners_ne_nil`); a tie is reported rather than resolved.
* Rescaling the shared scale by a positive factor moves the value by that
  factor and leaves the winners alone (`extremum_scale_invariant`), which is
  what makes *one scale* the right side condition — and
  `extremum_not_invariant_under_one_row_rescaling` exhibits a rescaling of a
  single row that moves the winner, which is why a column gathered from two
  scales is refused rather than folded.
* And the hole is not fussiness either:
  `extremum_over_present_is_not_the_extremum` exhibits a column whose extremum
  over the rows that are filled in is not its extremum once the hole is
  filled, so an answer taken over the present rows is a wrong answer rather
  than a partial one.

The shipped counterpart is `glm_universal.reasoning.column_extremum`, whose
tests pin these same properties on the real field surface.
-/

namespace GLM.ColumnExtremum

/-- One row's answer for one coordinate: the row, the scale it was read on,
and either a value or nothing.

`reading = none` is the register's own missingness mask — the field surface
refuses a missing cell rather than answering it blank, and this is that
refusal carried into the column. -/
structure Cell where
  /-- The row the reading was taken off. -/
  row : String
  /-- The scale it was read on: in the shipped system the table and field. -/
  scale : String
  /-- The value, exactly, or nothing when the register records none. -/
  reading : Option ℚ
deriving DecidableEq, Repr

/-- A column: one cell per row of a table. -/
abbrev Column := List Cell

/-- The rows that do answer, with their values. -/
def readings (col : Column) : List (String × ℚ) :=
  col.filterMap fun c => c.reading.map fun v => (c.row, v)

/-- The rows that do not. -/
def holes (col : Column) : List String :=
  (col.filter fun c => c.reading.isNone).map Cell.row

/-- The distinct scales the column was gathered from. -/
def scales (col : Column) : List String := (col.map Cell.scale).dedup

/-! ## §1  The fold, on a list of readings -/

/-- The largest value of a list of readings, or nothing when it is empty. -/
def maxValue (l : List (String × ℚ)) : Option ℚ := (l.map Prod.snd).max?

/-- Every row of the list attaining a given value. -/
def winnersOf (l : List (String × ℚ)) (m : ℚ) : List String :=
  (l.filter fun p => p.2 = m).map Prod.fst

/-- The extremum of a list of readings: the value, and every row attaining it. -/
def peak (l : List (String × ℚ)) : Option (ℚ × List String) :=
  (maxValue l).map fun m => (m, winnersOf l m)

lemma maxValue_eq_none_iff (l : List (String × ℚ)) :
    maxValue l = none ↔ l = [] := by
  simp [maxValue, List.max?_eq_none_iff]

lemma maxValue_mem {l : List (String × ℚ)} {m : ℚ} (h : maxValue l = some m) :
    m ∈ l.map Prod.snd := List.max?_mem h

lemma le_maxValue {l : List (String × ℚ)} {m : ℚ} {p : String × ℚ}
    (h : maxValue l = some m) (hp : p ∈ l) : p.2 ≤ m :=
  ((List.max?_eq_some_iff (xs := l.map Prod.snd) (a := m)).1 h).2 _
    (List.mem_map_of_mem hp)

@[simp] lemma mem_winnersOf {l : List (String × ℚ)} {m : ℚ} {r : String} :
    r ∈ winnersOf l m ↔ (r, m) ∈ l := by
  constructor
  · intro h
    simp only [winnersOf, List.mem_map, List.mem_filter] at h
    obtain ⟨p, ⟨hp, hval⟩, hrow⟩ := h
    have : p = (r, m) := by
      cases p with
      | mk a b => simp_all
    simpa [this] using hp
  · intro h
    simp only [winnersOf, List.mem_map, List.mem_filter]
    exact ⟨(r, m), ⟨h, by simp⟩, rfl⟩

lemma winnersOf_ne_nil {l : List (String × ℚ)} {m : ℚ}
    (h : maxValue l = some m) : winnersOf l m ≠ [] := by
  obtain ⟨p, hp, hval⟩ := List.mem_map.1 (maxValue_mem h)
  have hmem : p.1 ∈ winnersOf l m := by
    have : (p.1, m) ∈ l := by
      cases p with
      | mk a b => simpa [← hval] using hp
    simpa using this
  exact fun hnil => by simp [hnil] at hmem

/-! ## §2  The operation -/

/-- **The operation.**  The extremum of a column, or a refusal.

It refuses in exactly three situations: a column gathered from more than one
scale, a column with a hole in it, and a column with no rows. -/
def extremum? (col : Column) : Option (ℚ × List String) :=
  if (scales col).length = 1 ∧ holes col = [] then peak (readings col) else none

/-! ## §3  The refusal states a fact -/

/-- **Silent exactly when the column is mixed, holed, or empty.** -/
theorem extremum_eq_none_iff (col : Column) :
    extremum? col = none ↔
      (scales col).length ≠ 1 ∨ holes col ≠ [] ∨ readings col = [] := by
  unfold extremum?
  by_cases hs : (scales col).length = 1
  · by_cases hh : holes col = []
    · simp only [hs, hh, and_self, if_pos, ne_eq, not_true_eq_false, false_or,
        peak, Option.map_eq_none_iff, maxValue_eq_none_iff]
    · simp [hs, hh]
  · simp [hs]

/-- Read the other way: it answers exactly when the column is on one scale,
has no hole, and has a row. -/
theorem extremum_isSome_iff (col : Column) :
    (extremum? col).isSome ↔
      (scales col).length = 1 ∧ holes col = [] ∧ readings col ≠ [] := by
  rw [Option.isSome_iff_ne_none, ne_eq, extremum_eq_none_iff]
  tauto

/-! ## §4  When it answers, the answer is the column's own -/

/-- **Nothing is invented.**  The value returned is a value of the column. -/
theorem extremum_value_mem {col : Column} {m : ℚ} {ws : List String}
    (h : extremum? col = some (m, ws)) :
    m ∈ (readings col).map Prod.snd := by
  unfold extremum? at h
  split at h
  · simp only [peak, Option.map_eq_some_iff] at h
    obtain ⟨v, hv, hpair⟩ := h
    have hm : m = v := congrArg Prod.fst hpair.symm
    subst hm
    exact maxValue_mem hv
  · simp at h

/-- **Nothing is above it.**  Every reading of the column is at most the value
returned. -/
theorem le_extremum {col : Column} {m : ℚ} {ws : List String}
    (h : extremum? col = some (m, ws)) :
    ∀ p ∈ readings col, p.2 ≤ m := by
  unfold extremum? at h
  split at h
  · simp only [peak, Option.map_eq_some_iff] at h
    obtain ⟨v, hv, hpair⟩ := h
    have hm : m = v := congrArg Prod.fst hpair.symm
    subst hm
    exact fun p hp => le_maxValue hv hp
  · simp at h

/-- **Every row that attains it is named, and only those.**  A tie is reported
as a tie: the operation returns the whole set. -/
theorem mem_extremum_winners_iff {col : Column} {m : ℚ} {ws : List String}
    (h : extremum? col = some (m, ws)) (r : String) :
    r ∈ ws ↔ (r, m) ∈ readings col := by
  unfold extremum? at h
  split at h
  · simp only [peak, Option.map_eq_some_iff] at h
    obtain ⟨v, hv, hpair⟩ := h
    have hm : m = v := congrArg Prod.fst hpair.symm
    have hw : ws = winnersOf (readings col) v := (congrArg Prod.snd hpair).symm
    subst hm
    subst hw
    simp
  · simp at h

/-- And at least one row is always named. -/
theorem extremum_winners_ne_nil {col : Column} {m : ℚ} {ws : List String}
    (h : extremum? col = some (m, ws)) : ws ≠ [] := by
  unfold extremum? at h
  split at h
  · simp only [peak, Option.map_eq_some_iff] at h
    obtain ⟨v, hv, hpair⟩ := h
    have hm : m = v := congrArg Prod.fst hpair.symm
    have hw : ws = winnersOf (readings col) v := (congrArg Prod.snd hpair).symm
    subst hm
    subst hw
    exact winnersOf_ne_nil hv
  · simp at h

/-! ## §5  Why the side condition is *one scale* -/

/-- Carry every reading of a column by the same factor. -/
def rescale (k : ℚ) (col : Column) : Column :=
  col.map fun c => { c with reading := c.reading.map (k * ·) }

@[simp] lemma holes_rescale (k : ℚ) (col : Column) :
    holes (rescale k col) = holes col := by
  induction col with
  | nil => simp [rescale, holes]
  | cons c rest ih =>
      cases hc : c.reading <;>
        simp [rescale, holes, hc] at ih ⊢ <;> simp [ih]

@[simp] lemma scales_rescale (k : ℚ) (col : Column) :
    scales (rescale k col) = scales col := by
  simp [scales, rescale, List.map_map, Function.comp_def]

@[simp] lemma readings_rescale (k : ℚ) (col : Column) :
    readings (rescale k col) = (readings col).map fun p => (p.1, k * p.2) := by
  induction col with
  | nil => simp [rescale, readings]
  | cons c rest ih =>
      rw [rescale, List.map_cons, ← rescale]
      cases hc : c.reading with
      | none => simpa [readings, hc] using ih
      | some v => simpa [readings, hc] using ih

lemma maxValue_map_mul {k : ℚ} (hk : 0 < k) (l : List (String × ℚ)) :
    maxValue (l.map fun p => (p.1, k * p.2)) = (maxValue l).map (k * ·) := by
  unfold maxValue
  simp only [List.map_map, Function.comp_def]
  cases h : (l.map Prod.snd).max? with
  | none =>
      have : l = [] := by simpa [List.max?_eq_none_iff] using h
      simp [this]
  | some m =>
      obtain ⟨hmem, hle⟩ :=
        (List.max?_eq_some_iff (xs := l.map Prod.snd) (a := m)).1 h
      simp only [Option.map_some]
      refine (List.max?_eq_some_iff (xs := l.map fun p => k * p.2)
        (a := k * m)).2 ⟨?_, ?_⟩
      · obtain ⟨p, hp, hval⟩ := List.mem_map.1 hmem
        exact List.mem_map.2 ⟨p, hp, by rw [hval]⟩
      · intro b hb
        obtain ⟨p, hp, hval⟩ := List.mem_map.1 hb
        rw [← hval]
        exact mul_le_mul_of_nonneg_left (hle _ (List.mem_map_of_mem hp)) hk.le

lemma winnersOf_map_mul {k : ℚ} (hk : 0 < k) (l : List (String × ℚ)) (m : ℚ) :
    winnersOf (l.map fun p => (p.1, k * p.2)) (k * m) = winnersOf l m := by
  induction l with
  | nil => simp [winnersOf]
  | cons p rest ih =>
      have hiff : k * p.2 = k * m ↔ p.2 = m := by
        constructor
        · intro h
          exact mul_left_cancel₀ hk.ne' h
        · intro h
          rw [h]
      simp only [List.map_cons, winnersOf, List.filter_cons] at ih ⊢
      by_cases h : p.2 = m
      · simp [h] at ih ⊢
        simp [ih]
      · have hne : ¬ k * p.2 = k * m := fun hc => h (hiff.1 hc)
        simp [h, hne] at ih ⊢
        simp [ih]

/-- **A scale may be rescaled without disturbing the answer.**  The value moves
by the factor and the winners are exactly the same rows: that is what it is for
the whole column to be *on one scale*. -/
theorem extremum_scale_invariant {k : ℚ} (hk : 0 < k) (col : Column)
    {m : ℚ} {ws : List String} (h : extremum? col = some (m, ws)) :
    extremum? (rescale k col) = some (k * m, ws) := by
  unfold extremum? at h ⊢
  rw [scales_rescale, holes_rescale, readings_rescale]
  split at h
  · rename_i hcond
    rw [if_pos hcond]
    simp only [peak, Option.map_eq_some_iff] at h ⊢
    obtain ⟨v, hv, hpair⟩ := h
    have hm : m = v := congrArg Prod.fst hpair.symm
    have hw : ws = winnersOf (readings col) v := (congrArg Prod.snd hpair).symm
    subst hm
    subst hw
    exact ⟨k * m, by rw [maxValue_map_mul hk, hv]; simp,
      by rw [winnersOf_map_mul hk]⟩
  · simp at h

/-- **And the refusal is not fussiness.**  Carry *one* row of a column by a
positive factor — which is exactly what gathering a column from two scales
permits — and the extremum moves to a different row.  Three metres is three
hundred centimetres; the tallest of three and four is the second, and the
tallest of three hundred and four is the first. -/
theorem extremum_not_invariant_under_one_row_rescaling :
    ∃ (k a b : ℚ) (s : String), 0 < k ∧
      extremum? [⟨"a", s, some a⟩, ⟨"b", s, some b⟩] = some (b, ["b"]) ∧
      extremum? [⟨"a", s, some (k * a)⟩, ⟨"b", s, some b⟩]
        = some (k * a, ["a"]) := by
  refine ⟨100, 3, 4, "s", by norm_num, by decide, ?_⟩
  norm_num
  decide

/-! ## §6  Why a hole is refused rather than skipped -/

/-- Fill a column's holes with a value. -/
def fill (v : ℚ) (col : Column) : Column :=
  col.map fun c => { c with reading := some (c.reading.getD v) }

/-- **An extremum over the rows that are filled in is a wrong answer, not a
partial one.**  Here the column has one hole; the extremum of the rows present
is `1`, and filling the hole with `3` makes it `3` — a different value at a
different row.  So the operation refuses the column and says which rows are
missing, rather than answering over what is left. -/
theorem extremum_over_present_is_not_the_extremum :
    ∃ (col : Column) (v : ℚ),
      holes col ≠ [] ∧
      extremum? col = none ∧
      peak (readings col) = some (1, ["a"]) ∧
      extremum? (fill v col) = some (3, ["b"]) := by
  refine ⟨[⟨"a", "s", some 1⟩, ⟨"b", "s", none⟩], 3, by decide, by decide,
    by decide, by decide⟩

/-! ## §7  The other end of the column -/

/-- The smallest value, taken as the largest of the negated column. -/
def trough? (col : Column) : Option (ℚ × List String) :=
  (extremum? (rescale (-1) col)).map fun p => (-p.1, p.2)

/-- The two ends are one operation: the smallest is the largest of the negated
column, and it refuses in exactly the same three situations. -/
theorem trough_eq_none_iff (col : Column) :
    trough? col = none ↔ extremum? (rescale (-1) col) = none := by
  unfold trough?
  cases h : extremum? (rescale (-1) col) <;> simp

/-- And the rows it names are the rows attaining the smallest value: on the
witness column the two ends are the two different rows. -/
theorem trough_names_the_smallest :
    trough? [⟨"a", "s", some 3⟩, ⟨"b", "s", some 4⟩] = some (3, ["a"]) := by
  simp [trough?, extremum?, rescale, scales, holes, readings, peak, maxValue,
    winnersOf, List.dedup]
  norm_num

end GLM.ColumnExtremum
