import Mathlib
import RequestProject.GLM.CoordinateOrder
import RequestProject.GLM.ColumnExtremum

/-!
# The scales neither operation can bridge — and what a *declared* conversion
buys

`GLM.CoordinateOrder` orders two readings of one coordinate and refuses two
readings on two scales (`order_eq_none_iff`).  `GLM.ColumnExtremum` folds one
coordinate down one table and refuses a column gathered from two scales
(`extremum_eq_none_iff`).  Both refusals have the same cause, stated in both
files: *the operation holds no conversions*.  Two readings of the same
quantity under two field names are refused even where a conversion between
them exists, because nothing in the system says what that conversion is.

This file is about the thing that relaxes them: a **declared** table of
conversions, one row per scale, each saying which quantity the scale measures
and how to carry a reading on it into that quantity's canonical unit.  A
conversion here is affine — `value ↦ factor * value + offset` — because a
temperature scale needs an offset and a unit of mass does not, and its factor
is **positive**, which is the whole of what makes it a conversion rather than
a re-ordering.

What is proved:

* the conversion cannot disturb a verdict the bare operation already gave
  (`orderWith_conservative`), and with an empty table the two operations are
  the same function (`orderWith_nil`);
* a positive-affine conversion composed into the comparison leaves the verdict
  exactly as it was (`cmpQ_apply`, `order_conversion_invariant`), which is
  `GLM.CoordinateOrder.order_scale_invariant` with an offset allowed;
* the operation with conversions is silent exactly when a reading is missing,
  or the two scales differ and the table does not relate them under one
  quantity (`orderWith_eq_none_iff`) — so the wider operation still refuses at
  a stated boundary rather than by failing to find something;
* the answer does not depend on which scale the comparison is carried out in
  (`verdict_independent_of_target_scale`), which is what makes a table of
  conversions *into one canonical unit* a sound way to relate every scale of a
  quantity to every other;
* the positivity is load-bearing (`negative_factor_flips_the_verdict`), and so
  is the declaration itself: two tables can make the same pair of readings
  order two different ways (`the_table_carries_the_claim`), so a conversion is
  a fact someone wrote down and the answer is only as good as that row;
* and at the column level, converting a column by a positive-affine map moves
  the value and keeps the winners (`extremum_convert_invariant`), two columns
  converted into one unit may be gathered and folded
  (`gathered_winner_is_a_row_of_one_of_the_two_columns`), while gathering the
  same two columns *without* the conversion names the wrong row
  (`raw_gather_names_the_wrong_row`).

The shipped counterpart is `glm_universal.reasoning.scale_conversion`, whose
declared table is nine rows over four quantities and whose tests pin these
same properties on the real field surface.
-/

namespace GLM.ScaleConversion

open GLM.CoordinateOrder
open GLM.ColumnExtremum

/-! ## §1  A declared conversion -/

/-- One row of the declared table: a scale, the quantity it measures, and the
affine map that carries a reading on it into that quantity's canonical unit.

In the shipped system the scale tag is `table:field`, the quantity is one of
four declared names, and both numbers are exact rationals written down beside
the source they came from. -/
structure Conv where
  /-- The scale this row is about. -/
  scale : String
  /-- The quantity it measures.  Two scales are relatable exactly when this
  agrees. -/
  quantity : String
  /-- The positive factor carrying a reading into the canonical unit. -/
  factor : ℚ
  /-- The offset added after the factor — zero for every scale of a ratio
  quantity, non-zero for a temperature scale that does not start at absolute
  zero. -/
  offset : ℚ
deriving DecidableEq, Repr

/-- The conversion, applied: `value ↦ factor * value + offset`. -/
def apply (c : Conv) (x : ℚ) : ℚ := c.factor * x + c.offset

/-- The row a canonical scale carries: it is already in its own unit. -/
def idConv (s q : String) : Conv := ⟨s, q, 1, 0⟩

@[simp] lemma apply_idConv (s q : String) (x : ℚ) : apply (idConv s q) x = x := by
  simp [apply, idConv]

/-- The inverse conversion, which exists because the factor is not zero. -/
def inv (c : Conv) : Conv :=
  ⟨c.scale, c.quantity, 1 / c.factor, -c.offset / c.factor⟩

@[simp] lemma apply_inv_apply {c : Conv} (hc : c.factor ≠ 0) (x : ℚ) :
    apply (inv c) (apply c x) = x := by
  unfold apply inv
  field_simp
  ring

@[simp] lemma factor_inv (c : Conv) : (inv c).factor = 1 / c.factor := rfl

/-- Composition: carry through `d` and then through `c`. -/
def comp (c d : Conv) : Conv :=
  ⟨d.scale, c.quantity, c.factor * d.factor, c.factor * d.offset + c.offset⟩

@[simp] lemma apply_comp (c d : Conv) (x : ℚ) :
    apply (comp c d) x = apply c (apply d x) := by
  simp [apply, comp]; ring

/-! ## §2  A positive conversion leaves every verdict alone -/

/-- A conversion with a positive factor is strictly monotone. -/
theorem apply_lt_iff {c : Conv} (hc : 0 < c.factor) (x y : ℚ) :
    apply c x < apply c y ↔ x < y := by
  simp [apply, Rat.mul_lt_mul_left hc]

/-- **The deciding fact.**  A positive-affine conversion composed into the
comparison leaves the verdict exactly as it was.  The offset cancels and the
factor cannot reorder. -/
theorem cmpQ_apply {c : Conv} (hc : 0 < c.factor) (x y : ℚ) :
    cmpQ (apply c x) (apply c y) = cmpQ x y := by
  unfold cmpQ
  simp only [apply_lt_iff hc]

/-- The same statement at the ordering operation itself: reporting both
readings in another unit of the same quantity does not move the verdict.  This
is `GLM.CoordinateOrder.order_scale_invariant` with an offset allowed. -/
theorem order_conversion_invariant {c : Conv} (hc : 0 < c.factor)
    (x y : Reading) :
    order? (some ⟨x.scale, apply c x.value⟩) (some ⟨y.scale, apply c y.value⟩)
      = order? (some x) (some y) := by
  by_cases h : x.scale = y.scale
  · simp [order?, h, cmpQ_apply hc]
  · simp [order?, h]

/-- The difference is *not* invariant, and the statement says what it becomes:
a gap reported after a conversion is a gap in the target unit. -/
theorem apply_sub (c : Conv) (x y : ℚ) :
    apply c x - apply c y = c.factor * (x - y) := by
  simp [apply]; ring

/-! ## §3  The operation with a declared table -/

/-- The table's row for a scale, or nothing when the scale is not declared. -/
def declared (T : List Conv) (s : String) : Option Conv :=
  T.find? fun c => c.scale = s

/-- Two scales are relatable exactly when the table declares both of them
under one quantity. -/
def relates (T : List Conv) (s t : String) : Prop :=
  ∃ c d, declared T s = some c ∧ declared T t = some d ∧ c.quantity = d.quantity

/-- **The wider operation.**  Order two readings, converting when the table
says how.

Readings already on one scale are ordered exactly as before — the table is not
consulted at all, so a scale nobody declared is unaffected.  Readings on two
scales are ordered only when the table declares both under one quantity, and
then both are carried into that quantity's canonical unit before they are
compared. -/
def orderWith (T : List Conv) : Option Reading → Option Reading → Option Ordering
  | some x, some y =>
      if x.scale = y.scale then some (cmpQ x.value y.value)
      else
        match declared T x.scale, declared T y.scale with
        | some c, some d =>
            if c.quantity = d.quantity then
              some (cmpQ (apply c x.value) (apply d y.value))
            else none
        | _, _ => none
  | _, _ => none

/-- **With no conversions declared, this is the operation it extends.** -/
theorem orderWith_nil (a b : Option Reading) : orderWith [] a b = order? a b := by
  cases a with
  | none => cases b <;> simp [orderWith, order?]
  | some x =>
    cases b with
    | none => simp [orderWith, order?]
    | some y =>
        by_cases h : x.scale = y.scale <;> simp [orderWith, order?, h, declared]

/-- **The conversion layer never changes an answer.**  Anything the bare
operation ordered, the wider one orders the same way, whatever the table says:
a declared conversion can only turn a refusal into an answer. -/
theorem orderWith_conservative {T : List Conv} {a b : Option Reading}
    {o : Ordering} (h : order? a b = some o) : orderWith T a b = some o := by
  cases a with
  | none => simp [order?] at h
  | some x =>
    cases b with
    | none => simp [order?] at h
    | some y =>
        by_cases hs : x.scale = y.scale
        · simpa [orderWith, hs] using (by simpa [order?, hs] using h :
            some (cmpQ x.value y.value) = some o)
        · simp [order?, hs] at h

/-- **Silent exactly when a reading is missing, or the scales differ and the
table does not relate them.**  The wider operation refuses at a stated
boundary too: what it now needs is a row of the table, and the absence of one
is a fact about the table rather than a failed search. -/
theorem orderWith_eq_none_iff (T : List Conv) (a b : Option Reading) :
    orderWith T a b = none ↔
      a = none ∨ b = none ∨
        ∃ x y, a = some x ∧ b = some y ∧ x.scale ≠ y.scale ∧
          ¬ relates T x.scale y.scale := by
  cases a with
  | none => simp [orderWith]
  | some x =>
    cases b with
    | none => simp [orderWith]
    | some y =>
        by_cases hs : x.scale = y.scale
        · simp [orderWith, hs]
        · simp only [orderWith, hs, Option.some.injEq, relates,
            exists_and_left, not_exists, not_and]
          cases hc : declared T x.scale with
          | none => simp [hs, hc]
          | some c =>
            cases hd : declared T y.scale with
            | none => simp [hs, hc, hd]
            | some d =>
              by_cases hq : c.quantity = d.quantity <;> simp [hs, hc, hd, hq]

/-- **Nothing is invented.**  When the two scales differ and the table relates
them, the verdict returned is the comparison of the two *converted* values. -/
theorem orderWith_across_scales {T : List Conv} {x y : Reading} {c d : Conv}
    (hs : x.scale ≠ y.scale)
    (hc : declared T x.scale = some c) (hd : declared T y.scale = some d)
    (hq : c.quantity = d.quantity) :
    orderWith T (some x) (some y) = some (cmpQ (apply c x.value) (apply d y.value)) := by
  simp [orderWith, hs, hc, hd, hq]

/-! ## §4  Why the table may point at one canonical unit -/

/-- **The verdict does not depend on the unit it is taken in.**  Two readings
carried into the canonical unit compare exactly as they do after both are
carried on into any further scale of the same quantity.  This is what makes a
table of conversions *into one unit* enough to relate every scale of a
quantity to every other: there is no path to choose. -/
theorem verdict_independent_of_target_scale {e : Conv} (he : 0 < e.factor)
    (u v : ℚ) :
    cmpQ (apply (inv e) u) (apply (inv e) v) = cmpQ u v := by
  have : 0 < (inv e).factor := by
    simpa [factor_inv] using (one_div_pos.mpr he)
  simpa using cmpQ_apply this u v

/-- **The positivity is load-bearing.**  A factor below zero is a
re-ordering, not a conversion: it turns *below* into *above*. -/
theorem negative_factor_flips_the_verdict :
    ∃ (c : Conv) (x y : ℚ), c.factor < 0 ∧
      cmpQ x y = .lt ∧ cmpQ (apply c x) (apply c y) = .gt := by
  exact ⟨⟨"s", "q", -1, 0⟩, 1, 2, by norm_num, by norm_num [cmpQ],
    by norm_num [cmpQ, apply]⟩

/-- **And the declaration carries the claim.**  The same two readings order
one way under one table and the other way under another: the operation reports
what was declared, so a conversion is only as good as the row someone wrote
down.  This is why the shipped table names a source for each of its rows and
why a scale it does not mention stays refused. -/
theorem the_table_carries_the_claim :
    ∃ (x y : Reading) (T T' : List Conv),
      orderWith T (some x) (some y) = some .lt ∧
      orderWith T' (some x) (some y) = some .gt := by
  have hne : ¬ (("a" : String) = "b") := by decide
  refine ⟨⟨"a", 1⟩, ⟨"b", 2⟩,
    [⟨"a", "q", 1, 0⟩, ⟨"b", "q", 1, 0⟩],
    [⟨"a", "q", 100, 0⟩, ⟨"b", "q", 1, 0⟩], ?_, ?_⟩ <;>
    norm_num [orderWith, declared, List.find?, hne, cmpQ, apply]

/-! ## §5  The column, gathered from two scales -/

/-- A list of cells all carrying one scale has exactly that one scale. -/
lemma scales_const {u : String} : ∀ {col : Column}, col ≠ [] →
    (∀ cell ∈ col, cell.scale = u) → scales col = [u] := by
  intro col
  induction col with
  | nil => intro h _; exact absurd rfl h
  | cons c rest ih =>
    intro _ h
    have hc : c.scale = u := h c (by simp)
    cases rest with
    | nil => simp [scales, hc]
    | cons d ds =>
      have hrest := ih (by simp) (fun x hx => h x (by simp [hx]))
      have hmem : u ∈ d.scale :: List.map Cell.scale ds := by
        simp only [List.mem_cons]
        exact Or.inl (h d (by simp)).symm
      simp only [scales, List.map_cons] at hrest ⊢
      rw [hc, List.dedup_cons_of_mem hmem]
      exact hrest

/-- The fold's two supporting lemmas, for an affine conversion rather than the
bare rescaling `GLM.ColumnExtremum` proves them for. -/
lemma maxValue_map_apply {c : Conv} (hc : 0 < c.factor) (l : List (String × ℚ)) :
    maxValue (l.map fun p => (p.1, apply c p.2)) = (maxValue l).map (apply c) := by
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
      refine (List.max?_eq_some_iff (xs := l.map fun p => apply c p.2)
        (a := apply c m)).2 ⟨?_, ?_⟩
      · obtain ⟨p, hp, hval⟩ := List.mem_map.1 hmem
        exact List.mem_map.2 ⟨p, hp, by rw [hval]⟩
      · intro b hb
        obtain ⟨p, hp, hval⟩ := List.mem_map.1 hb
        rw [← hval]
        have : p.2 ≤ m := hle _ (List.mem_map_of_mem hp)
        simpa [apply] using
          add_le_add_right (mul_le_mul_of_nonneg_left this hc.le) c.offset

lemma winnersOf_map_apply {c : Conv} (hc : 0 < c.factor)
    (l : List (String × ℚ)) (m : ℚ) :
    winnersOf (l.map fun p => (p.1, apply c p.2)) (apply c m) = winnersOf l m := by
  induction l with
  | nil => simp [winnersOf]
  | cons p rest ih =>
      have hiff : apply c p.2 = apply c m ↔ p.2 = m := by
        constructor
        · intro h
          have := congrArg (apply (inv c)) h
          simpa [apply_inv_apply hc.ne'] using this
        · intro h; rw [h]
      simp only [List.map_cons, winnersOf, List.filter_cons] at ih ⊢
      by_cases h : p.2 = m
      · simp [h] at ih ⊢
        simp [ih]
      · have hne : ¬ apply c p.2 = apply c m := fun hcon => h (hiff.1 hcon)
        simp [h, hne] at ih ⊢
        simp [ih]

/-- Carry a whole column into one unit: every reading through the conversion,
every cell relabelled with the unit it now names. -/
def convert (c : Conv) (u : String) (col : Column) : Column :=
  col.map fun cell =>
    { cell with scale := u, reading := cell.reading.map (apply c) }

@[simp] lemma holes_convert (c : Conv) (u : String) (col : Column) :
    holes (convert c u col) = holes col := by
  induction col with
  | nil => simp [convert, holes]
  | cons cell rest ih =>
      cases hc : cell.reading <;> simp [convert, holes, hc] at ih ⊢ <;> simp [ih]

@[simp] lemma readings_convert (c : Conv) (u : String) (col : Column) :
    readings (convert c u col) = (readings col).map fun p => (p.1, apply c p.2) := by
  induction col with
  | nil => simp [convert, readings]
  | cons cell rest ih =>
      rw [convert, List.map_cons, ← convert]
      cases hc : cell.reading with
      | none => simpa [readings, hc] using ih
      | some v => simpa [readings, hc] using ih

lemma scales_convert (c : Conv) (u : String) {col : Column} (h : col ≠ []) :
    scales (convert c u col) = [u] := by
  refine scales_const (by simpa [convert] using h) ?_
  intro cell hcell
  obtain ⟨_, _, rfl⟩ := List.mem_map.1 hcell
  rfl

/-- **A column converted is the same column.**  A positive-affine conversion
carries the extremum by the same map and leaves the winning rows exactly as
they were — so reporting a column in another unit of its quantity is a change
of unit and not a change of answer. -/
theorem extremum_convert_invariant {c : Conv} (hc : 0 < c.factor)
    (u : String) (col : Column) {m : ℚ} {ws : List String}
    (h : extremum? col = some (m, ws)) :
    extremum? (convert c u col) = some (apply c m, ws) := by
  have hne : col ≠ [] := by
    intro hnil
    rw [hnil] at h
    simp [extremum?, scales, holes] at h
  unfold extremum? at h ⊢
  rw [scales_convert c u hne, holes_convert, readings_convert]
  split at h
  · rename_i hcond
    rw [if_pos ⟨by simp, hcond.2⟩]
    simp only [peak, Option.map_eq_some_iff] at h ⊢
    obtain ⟨v, hv, hpair⟩ := h
    have hm : m = v := congrArg Prod.fst hpair.symm
    have hw : ws = winnersOf (readings col) v := (congrArg Prod.snd hpair).symm
    subst hm
    subst hw
    refine ⟨apply c m, ?_, ?_⟩
    · rw [maxValue_map_apply hc, hv]; simp
    · rw [winnersOf_map_apply hc]
  · simp at h

/-- The gathered column: two columns, each carried into the same unit. -/
def gather (c d : Conv) (u : String) (col₁ col₂ : Column) : Column :=
  convert c u col₁ ++ convert d u col₂

@[simp] lemma readings_append (l₁ l₂ : Column) :
    readings (l₁ ++ l₂) = readings l₁ ++ readings l₂ := by
  simp [readings, List.filterMap_append]

lemma scales_gather (c d : Conv) (u : String) {col₁ col₂ : Column}
    (h₁ : col₁ ≠ []) : scales (gather c d u col₁ col₂) = [u] := by
  refine scales_const ?_ ?_
  · intro hnil
    have := (List.append_eq_nil_iff.1 (by simpa [gather] using hnil)).1
    exact h₁ (by simpa [convert] using this)
  · intro cell hcell
    rcases List.mem_append.1 hcell with h | h <;>
      · obtain ⟨_, _, rfl⟩ := List.mem_map.1 h
        rfl

/-- **A gathered column answers with a row of one of the two columns.**  When
two columns of one quantity are carried into one unit and folded, the value
returned is one of the converted readings and every row named attains it — the
fold is the one `GLM.ColumnExtremum` already proved sound, and the conversion
is what made the two columns one. -/
theorem gathered_winner_is_a_row_of_one_of_the_two_columns
    {c d : Conv} {u : String} {col₁ col₂ : Column} {m : ℚ} {ws : List String}
    (h : extremum? (gather c d u col₁ col₂) = some (m, ws)) :
    (∀ r ∈ ws, (r, m) ∈ (readings col₁).map (fun p => (p.1, apply c p.2)) ++
        (readings col₂).map (fun p => (p.1, apply d p.2))) ∧
      ws ≠ [] := by
  refine ⟨fun r hr => ?_, extremum_winners_ne_nil h⟩
  have := (mem_extremum_winners_iff h (r := r)).1 hr
  simpa [gather, readings_append, readings_convert] using this

/-- **And gathering without the conversion names the wrong row.**  One reading
of `5` on a scale whose unit is 96 times the other's is larger than a reading
of `200` on that other, and the unconverted gather says the opposite.  This is
the column-level form of `GLM.CoordinateOrder.naive_order_is_not_scale_free`,
and it is why the gather is refused until a row of the table licenses it. -/
theorem raw_gather_names_the_wrong_row :
    ∃ (c d : Conv) (col₁ col₂ : Column),
      extremum? (gather c d "kJ/mol" col₁ col₂) = some (480, ["a"]) ∧
      extremum? (gather (idConv "" "") (idConv "" "") "kJ/mol" col₁ col₂)
        = some (200, ["b"]) := by
  refine ⟨⟨"eV", "molar energy", 96, 0⟩, ⟨"kJ/mol", "molar energy", 1, 0⟩,
    [⟨"a", "eV", some 5⟩], [⟨"b", "kJ/mol", some 200⟩], ?_, ?_⟩
  · have h : gather ⟨"eV", "molar energy", 96, 0⟩ ⟨"kJ/mol", "molar energy", 1, 0⟩
        "kJ/mol" [⟨"a", "eV", some 5⟩] [⟨"b", "kJ/mol", some 200⟩]
        = [⟨"a", "kJ/mol", some 480⟩, ⟨"b", "kJ/mol", some 200⟩] := by
      norm_num [gather, convert, apply]
    rw [h]; rfl
  · have h : gather (idConv "" "") (idConv "" "") "kJ/mol"
        [⟨"a", "eV", some 5⟩] [⟨"b", "kJ/mol", some 200⟩]
        = [⟨"a", "kJ/mol", some 5⟩, ⟨"b", "kJ/mol", some 200⟩] := by
      norm_num [gather, convert]
    rw [h]; rfl

end GLM.ScaleConversion
