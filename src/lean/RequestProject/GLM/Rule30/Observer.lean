module

public import RequestProject.GLM.Rule30.ElementaryCA
public import RequestProject.GLM.Rule30.Perspective

/-!
# What an observer can read: inducing the wheel, and the direction of view

Round 10.  The GLM reads Rule 30 the way it reads an ARC task: it is shown part of a
space-time diagram and asked which local rule (which *wheel*) produced it.  This file
proves exactly how much of the diagram is needed, and what a single column can and cannot
reveal.  This is the formal side of "perspective" (which way the observer `Y` is looking).

## Exact simulation on a finite window

* `windowStep r` : one step of wheel `r` on a finite list of cells (the list shrinks by one
  cell at each end).  `sample x a n` : the cells `x a, …, x (a + n - 1)`.
* `windowStep_iterate_sample` : `t` window steps applied to the `2t + n` cells around
  `[a, a + n)` give row `t` of the true evolution on `[a, a + n)`.  So every finite question
  about the diagram is decided by a list computation (`ecaEvolve_eq_window`).

## Inducing the wheel from the rows (the ARC-style reading)

* `rows_identify_thirty` : among all 256 wheels, **rows `0, …, 4` of the impulse run, read
  inside the light cone, determine wheel 30**.
* `rows_three_do_not_identify` : rows `0, …, 3` do not: wheel 62 produces exactly the same rows
  (at every cell, not only in the cone).  The two wheels differ only on the neighbourhood
  `(1,0,1)`, which first occurs in row 3 (`thirty_sixtyTwo_differ_only_at_101`).  So row 4 is
  not determined by rows `0..3` (`row_four_not_determined`).
* `ecaEvolve_seed_outside` : for any wheel that keeps white white, the impulse run is white
  outside its light cone.

## One column: the observer at the centre cannot tell left from right

* `centre_column_class` : for `r < 256`, the centre column of wheel `r` from the impulse equals
  Rule 30's centre column **iff `r = 30` or `r = 86`** (the mirror image).
* `centre_prefix_class` : seven values of the centre column already cut the family down to
  `{30, 86}`; no number of further values cuts it further (`centre_column_class`).
* `column_one_identifies` : the observer one cell to the right, at column 1, **does** determine
  the wheel: its column equals Rule 30's iff `r = 30`, and eight values suffice
  (`column_one_prefix_identifies`).
* `offCentre_column_identifies` : the same holds at every column `c` with `1 ≤ |c| ≤ 5`
  (thirteen values suffice).

So the left/right orientation of the run is invisible from the centre column and from every
statistic of it, but an observer who moves one cell off-centre reads it in eight steps.

## The wobble arrow is a perspective: mirror-invariant, colour-reversed

* `ecaColumn_mirror`, `ecaColumn_complement` : how a column transforms.
* `observerArrow_mirror` : the arrow `-sign D(N)` is unchanged by reflecting space
  (wheel `r ↦ mirrorNum r`, row and column reflected).
* `observerArrow_complement` : it is reversed by swapping the colours.
* `wobble_eightySix`, `observerArrow_eightySix`, `wobble_oneThirtyFive`,
  `observerArrow_oneThirtyFive` : the instances for Rule 30's class `{30, 86, 135}`.

The arrow therefore records the observer's **colour frame** (which colour counts as "black")
and is blind to the **spatial frame** (which way is "right").  Together with
`wobble_reverse` (`Perspective.lean`, reading time backwards) this gives the three
"perspective" operations on the wobble and how each acts on the arrow.

None of this decides the prize problems: every statement is about which wheel produced the
data or how a statistic transforms, not about the limit behaviour of Rule 30's centre column.
-/

@[expose] public section

namespace GLM.Rule30

/-! ## 1. Exact simulation on a finite window -/

/-- One step of wheel `r` on a finite window of cells.  The output has two cells fewer: the
first and last cells lack a neighbour. -/
def windowStep (r : ℕ) : List Bool → List Bool
  | a :: b :: c :: rest => ecaRule r a b c :: windowStep r (b :: c :: rest)
  | _ => []

/-- The `n` cells `x a, x (a+1), …, x (a + n - 1)`. -/
def sample (x : Config) (a : ℤ) (n : ℕ) : List Bool :=
  (List.range n).map (fun i : ℕ => x (a + (i : ℤ)))

/-- One step of wheel `r` on a whole row. -/
def ecaStep (r : ℕ) (x : Config) : Config := fun c => ecaRule r (x (c - 1)) (x c) (x (c + 1))

theorem ecaEvolve_succ_eq_step (r : ℕ) (x : Config) (n : ℕ) :
    ecaEvolve r x (n + 1) = ecaStep r (ecaEvolve r x n) := by
  funext c; rw [ecaEvolve_succ]; rfl

theorem sample_succ (x : Config) (a : ℤ) (n : ℕ) :
    sample x a (n + 1) = x a :: sample x (a + 1) n := by
  simp only [sample, List.range_succ_eq_map, List.map_cons, List.map_map]
  congr 1
  · simp
  · apply List.map_congr_left
    intro i _
    simp only [Function.comp, Nat.cast_succ]
    congr 1; ring

theorem windowStep_sample (r : ℕ) (x : Config) (a : ℤ) (n : ℕ) :
    windowStep r (sample x a (n + 2)) = sample (ecaStep r x) (a + 1) n := by
  induction n generalizing a with
  | zero => rw [sample_succ, sample_succ]; simp [sample, windowStep]
  | succ n ih =>
    rw [sample_succ, sample_succ, sample_succ, windowStep, ← sample_succ, ← sample_succ, ih,
      sample_succ (ecaStep r x)]
    congr 1
    simp only [ecaStep]
    congr 1
    ring_nf

/-- `t` window steps on the `n + 2t` cells starting at `a - t` give row `t` on `[a, a + n)`. -/
theorem windowStep_iterate_sample (r : ℕ) (x : Config) (t : ℕ) :
    ∀ (a : ℤ) (n : ℕ), (windowStep r)^[t] (sample x (a - t) (n + 2 * t)) =
      sample (ecaEvolve r x t) a n := by
  induction t with
  | zero => intro a n; simp
  | succ t ih =>
    intro a n
    rw [Function.iterate_succ_apply', ecaEvolve_succ_eq_step]
    have h1 : a - ((t + 1 : ℕ) : ℤ) = (a - 1) - t := by push_cast; ring
    have h2 : n + 2 * (t + 1) = (n + 2) + 2 * t := by ring
    rw [h1, h2, ih (a - 1) (n + 2), windowStep_sample]
    congr 1; ring

/-- A single cell of the evolution, read off a finite list computation. -/
theorem ecaEvolve_eq_window (r : ℕ) (x : Config) (t : ℕ) (c : ℤ) :
    ecaEvolve r x t c = ((windowStep r)^[t] (sample x (c - t) (1 + 2 * t))).headD false := by
  rw [windowStep_iterate_sample]; simp [sample]

/-- The first `K` values of column `c`, computed on finite windows. -/
def windowColumn (r : ℕ) (x : Config) (c : ℤ) (K : ℕ) : List Bool :=
  (List.range K).map fun t => ((windowStep r)^[t] (sample x (c - t) (1 + 2 * t))).headD false

theorem windowColumn_eq (r : ℕ) (x : Config) (c : ℤ) (K : ℕ) :
    windowColumn r x c K = (List.range K).map (ecaColumn r x c) := by
  apply List.map_congr_left
  intro t _
  rw [ecaColumn, ecaEvolve_eq_window]

theorem prefix_eq_iff {α : Type*} (a b : ℕ → α) (K : ℕ) :
    (List.range K).map a = (List.range K).map b ↔ ∀ t < K, a t = b t := by
  constructor
  · intro h t ht
    have := congrArg (fun l => l[t]?) h
    simpa [ht] using this
  · intro h
    apply List.map_congr_left
    intro t ht
    exact h t (List.mem_range.mp ht)

/-! ## 2. Inducing the wheel from rows of the diagram -/

/-- For a wheel that keeps the white neighbourhood white, the impulse run is white outside
its light cone. -/
theorem ecaEvolve_seed_outside {r : ℕ} (hr : ecaRule r false false false = false) (t : ℕ) :
    ∀ c : ℤ, (t : ℤ) < |c| → ecaEvolve r seed t c = false := by
  induction t with
  | zero =>
    intro c hc
    simp only [ecaEvolve_zero, seed, decide_eq_false_iff_not]
    intro h; subst h; simp at hc
  | succ t ih =>
    intro c hc
    rw [ecaEvolve_succ, ih (c - 1) (by cases abs_cases c <;> cases abs_cases (c - 1) <;>
        push_cast at hc ⊢ <;> linarith),
      ih c (by push_cast at hc; linarith),
      ih (c + 1) (by cases abs_cases c <;> cases abs_cases (c + 1) <;>
        push_cast at hc ⊢ <;> linarith), hr]

/-- The light-cone cells of rows `0..T` of the impulse run of wheel `r`, row by row. -/
def coneRows (r : ℕ) (T : ℕ) : List (List Bool) :=
  (List.range (T + 1)).map fun t => sample (ecaEvolve r seed t) (-t) (2 * t + 1)

/-- The same, computed on finite windows. -/
def windowConeRows (r : ℕ) (T : ℕ) : List (List Bool) :=
  (List.range (T + 1)).map fun t =>
    (windowStep r)^[t] (sample seed (-t - t) (2 * t + 1 + 2 * t))

theorem windowConeRows_eq (r T : ℕ) : windowConeRows r T = coneRows r T := by
  simp only [windowConeRows, coneRows]
  apply List.map_congr_left
  intro t _
  have := windowStep_iterate_sample r seed t (-t) (2 * t + 1)
  rw [this]

theorem sample_eq_iff (x y : Config) (a : ℤ) (n : ℕ) :
    sample x a n = sample y a n ↔ ∀ i < n, x (a + i) = y (a + i) := by
  simp only [sample]
  exact prefix_eq_iff (fun i => x (a + i)) (fun i => y (a + i)) n

/-- Agreement of the light-cone rows `0..T` as a list equality. -/
theorem coneRows_eq_iff (r s T : ℕ) :
    coneRows r T = coneRows s T ↔
      ∀ t : ℕ, t ≤ T → ∀ c : ℤ, |c| ≤ t → ecaEvolve r seed t c = ecaEvolve s seed t c := by
  simp only [coneRows]
  rw [prefix_eq_iff (fun t => sample (ecaEvolve r seed t) (-t) (2 * t + 1))
    (fun t => sample (ecaEvolve s seed t) (-t) (2 * t + 1)) (T + 1)]
  constructor
  · intro h t ht c hc
    have h' := (sample_eq_iff _ _ _ _).mp (h t (by omega)) (c + t).toNat (by
      have := abs_le.mp hc; omega)
    have hc' : -(t : ℤ) + ((c + t).toNat : ℕ) = c := by
      have := abs_le.mp hc; omega
    rwa [hc'] at h'
  · intro h t ht
    rw [sample_eq_iff]
    intro i hi
    apply h t (by omega)
    rw [abs_le]; constructor <;> omega

private theorem rows_identify_check :
    ∀ r ∈ List.range 256, windowConeRows r 4 = windowConeRows 30 4 → r = 30 := by
  decide +kernel

/-- **Rows `0..4` of the impulse run, read in the light cone, determine wheel 30** among all
256 wheels. -/
theorem rows_identify_thirty (r : ℕ) (hr : r < 256)
    (h : ∀ t : ℕ, t ≤ 4 → ∀ c : ℤ, |c| ≤ t → ecaEvolve r seed t c = ecaEvolve 30 seed t c) :
    r = 30 := by
  apply rows_identify_check r (List.mem_range.mpr hr)
  rw [windowConeRows_eq, windowConeRows_eq, coneRows_eq_iff]
  exact h

private theorem rows_three_window :
    windowConeRows 62 3 = windowConeRows 30 3 := by decide +kernel

/-- **Rows `0..3` do not determine the wheel**: wheel 62 (`0b00111110`) produces exactly the
rows `0..3` of wheel 30 from the impulse, at every cell. -/
theorem rows_three_do_not_identify :
    (62 : ℕ) ≠ 30 ∧ ∀ t : ℕ, t ≤ 3 → ∀ c : ℤ, ecaEvolve 62 seed t c = ecaEvolve 30 seed t c := by
  refine ⟨by decide, fun t ht c => ?_⟩
  by_cases hc : |c| ≤ t
  · have := (coneRows_eq_iff 62 30 3).mp (by
      rw [← windowConeRows_eq, ← windowConeRows_eq]; exact rows_three_window)
    exact this t ht c hc
  · push_neg at hc
    rw [ecaEvolve_seed_outside (by decide) t c hc, ecaEvolve_seed_outside (by decide) t c hc]

/-- So row 4 is not determined by rows `0..3`: wheels 62 and 30 share rows `0..3` and differ in
row 4. -/
theorem row_four_not_determined : ecaEvolve 62 seed 4 ≠ ecaEvolve 30 seed 4 := by
  intro h
  have := rows_identify_thirty 62 (by norm_num) (fun t ht c _ => by
    rcases Nat.lt_or_ge t 4 with h4 | h4
    · exact rows_three_do_not_identify.2 t (by omega) c
    · obtain rfl : t = 4 := by omega
      exact congrFun h c)
  norm_num at this

/-- Wheels 30 and 62 differ only on the neighbourhood `(1,0,1)`. -/
theorem thirty_sixtyTwo_differ_only_at_101 (L C R : Bool) :
    ecaRule 62 L C R ≠ ecaRule 30 L C R ↔ (L = true ∧ C = false ∧ R = true) := by
  cases L <;> cases C <;> cases R <;> decide

/-! ## 3. One column: the centre cannot tell left from right -/

/-- How a column transforms under the mirror. -/
theorem ecaColumn_mirror (r : ℕ) (x : Config) (c : ℤ) :
    ecaColumn (mirrorNum r) (fun j => x (-j)) (-c) = ecaColumn r x c := by
  funext n
  simp only [ecaColumn]
  rw [ecaEvolve_mirror, neg_neg]

/-- How a column transforms under the colour swap. -/
theorem ecaColumn_complement (r : ℕ) (x : Config) (c : ℤ) :
    ecaColumn (complementNum r) (fun j => !x j) c = fun n => !ecaColumn r x c n := by
  funext n
  simp only [ecaColumn]
  rw [ecaEvolve_complement]

/-- Wheel 86 has exactly Rule 30's centre column from the impulse. -/
theorem ecaColumn_eightySix_centre : ecaColumn 86 seed 0 = centerCol := by
  have := ecaColumn_mirror 30 seed 0
  rw [seed_mirror, mirrorNum_thirty, neg_zero] at this
  rw [this, ecaColumn_thirty_seed]

private theorem centre_prefix_check :
    ∀ r ∈ List.range 256, windowColumn r seed 0 7 = windowColumn 30 seed 0 7 →
      r = 30 ∨ r = 86 := by
  decide +kernel

/-- Seven values of the centre column already narrow the 256 wheels to `{30, 86}`. -/
theorem centre_prefix_class (r : ℕ) (hr : r < 256)
    (h : ∀ t < 7, ecaColumn r seed 0 t = centerCol t) : r = 30 ∨ r = 86 := by
  apply centre_prefix_check r (List.mem_range.mpr hr)
  rw [windowColumn_eq, windowColumn_eq, ecaColumn_thirty_seed, prefix_eq_iff]
  exact h

/-- Six values do not: wheels 175 and 245 also produce the first six. -/
theorem centre_six_not_enough :
    (∀ t < 6, ecaColumn 175 seed 0 t = centerCol t) ∧
      (∀ t < 6, ecaColumn 245 seed 0 t = centerCol t) := by
  have h1 : windowColumn 175 seed 0 6 = windowColumn 30 seed 0 6 := by decide +kernel
  have h2 : windowColumn 245 seed 0 6 = windowColumn 30 seed 0 6 := by decide +kernel
  rw [windowColumn_eq, windowColumn_eq, ecaColumn_thirty_seed, prefix_eq_iff] at h1 h2
  exact ⟨h1, h2⟩

/-- **The observer at the centre cannot tell left from right.**  Among the 256 wheels, the
ones whose centre column from the impulse is Rule 30's centre column are exactly 30 and its
mirror image 86.  No statistic of the centre column (the wobble, the frequency, any
finite-state observer) can therefore tell which way the run is oriented. -/
theorem centre_column_class (r : ℕ) (hr : r < 256) :
    ecaColumn r seed 0 = centerCol ↔ r = 30 ∨ r = 86 := by
  constructor
  · intro h
    exact centre_prefix_class r hr fun t _ => congrFun h t
  · rintro (rfl | rfl)
    · exact ecaColumn_thirty_seed
    · exact ecaColumn_eightySix_centre

private theorem column_one_check :
    ∀ r ∈ List.range 256, windowColumn r seed 1 8 = windowColumn 30 seed 1 8 → r = 30 := by
  decide +kernel

/-- Eight values of column 1 determine wheel 30 among all 256. -/
theorem column_one_prefix_identifies (r : ℕ) (hr : r < 256)
    (h : ∀ t < 8, ecaColumn r seed 1 t = ecaColumn 30 seed 1 t) : r = 30 := by
  apply column_one_check r (List.mem_range.mpr hr)
  rw [windowColumn_eq, windowColumn_eq, prefix_eq_iff]
  exact h

/-- Seven values of column 1 do not (wheel 17 also produces them). -/
theorem column_one_seven_not_enough :
    (17 : ℕ) ≠ 30 ∧ ∀ t < 7, ecaColumn 17 seed 1 t = ecaColumn 30 seed 1 t := by
  refine ⟨by decide, ?_⟩
  have h : windowColumn 17 seed 1 7 = windowColumn 30 seed 1 7 := by decide +kernel
  rwa [windowColumn_eq, windowColumn_eq, prefix_eq_iff] at h

/-- **One cell off-centre, the orientation is readable.**  The observer at column 1 sees a
column that only wheel 30 produces. -/
theorem column_one_identifies (r : ℕ) (hr : r < 256) :
    ecaColumn r seed 1 = ecaColumn 30 seed 1 ↔ r = 30 := by
  constructor
  · intro h; exact column_one_prefix_identifies r hr fun t _ => congrFun h t
  · rintro rfl; rfl

/-- In particular the mirror image is told apart at column 1. -/
theorem column_one_separates_mirror : ecaColumn 86 seed 1 ≠ ecaColumn 30 seed 1 := by
  intro h
  have := (column_one_identifies 86 (by norm_num)).mp h
  norm_num at this

private theorem offCentre_check :
    ∀ c ∈ ([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5] : List ℤ), ∀ r ∈ List.range 256,
      windowColumn r seed c 13 = windowColumn 30 seed c 13 → r = 30 := by
  decide +kernel

/-- **Every observer near the centre, but not at it, reads the orientation.**  For each column
`c` with `1 ≤ |c| ≤ 5`, the column of the impulse run determines wheel 30 among all 256
(thirteen values suffice).  The centre column is the exception (`centre_column_class`). -/
theorem offCentre_column_identifies (c : ℤ) (hc0 : c ≠ 0) (hc : |c| ≤ 5) (r : ℕ)
    (hr : r < 256) : ecaColumn r seed c = ecaColumn 30 seed c ↔ r = 30 := by
  constructor
  · intro h
    have hmem : c ∈ ([-5, -4, -3, -2, -1, 1, 2, 3, 4, 5] : List ℤ) := by
      have := abs_le.mp hc
      have : c = -5 ∨ c = -4 ∨ c = -3 ∨ c = -2 ∨ c = -1 ∨ c = 1 ∨ c = 2 ∨ c = 3 ∨ c = 4 ∨
          c = 5 := by omega
      rcases this with h | h | h | h | h | h | h | h | h | h <;> subst h <;> decide
    apply offCentre_check c hmem r (List.mem_range.mpr hr)
    rw [windowColumn_eq, windowColumn_eq, h]
  · rintro rfl; rfl

/-! ## 4. The wobble arrow under the change of perspective -/

/-- The arrow is unchanged by reflecting space. -/
theorem observerArrow_mirror (r : ℕ) (x : Config) (c : ℤ) (N : ℕ) :
    observerArrow (ecaColumn (mirrorNum r) (fun j => x (-j)) (-c)) N =
      observerArrow (ecaColumn r x c) N := by
  rw [ecaColumn_mirror]

/-- The wobble is negated by swapping the colours. -/
theorem wobble_complement (r : ℕ) (x : Config) (c : ℤ) (N : ℕ) :
    wobble (ecaColumn (complementNum r) (fun j => !x j) c) N = - wobble (ecaColumn r x c) N := by
  rw [ecaColumn_complement, wobble_not]

/-- The arrow is reversed by swapping the colours. -/
theorem observerArrow_complement (r : ℕ) (x : Config) (c : ℤ) (N : ℕ) :
    observerArrow (ecaColumn (complementNum r) (fun j => !x j) c) N =
      - observerArrow (ecaColumn r x c) N := by
  simp only [observerArrow, wobble_complement, Int.sign_neg]

theorem wobble_eightySix (N : ℕ) : wobble (ecaColumn 86 seed 0) N = wobble centerCol N := by
  rw [ecaColumn_eightySix_centre]

theorem observerArrow_eightySix (N : ℕ) :
    observerArrow (ecaColumn 86 seed 0) N = observerArrow centerCol N := by
  rw [ecaColumn_eightySix_centre]

theorem wobble_oneThirtyFive (N : ℕ) :
    wobble (ecaColumn 135 (fun j => !seed j) 0) N = - wobble centerCol N := by
  rw [← complementNum_thirty, wobble_complement, ecaColumn_thirty_seed]

theorem observerArrow_oneThirtyFive (N : ℕ) :
    observerArrow (ecaColumn 135 (fun j => !seed j) 0) N = - observerArrow centerCol N := by
  rw [← complementNum_thirty, observerArrow_complement, ecaColumn_thirty_seed]

end GLM.Rule30
