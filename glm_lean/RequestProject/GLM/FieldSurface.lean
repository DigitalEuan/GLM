/-
# The field surface: what a table of rows can and cannot answer

`studies/PROBE_ORACLE_STUDY.md` hand-translated twenty pre-registered probe
questions into the system's own query grammar and found the refusals were
three different failures.  Ten of the twenty were *held and unreachable*: a
shipped register row or a shipped function carried the answer and no query
kind returned it.  The instrument that closes those is a **field surface** —
one query kind returning a named field of a named row — and
`overlay/glm_universal/runtime/fields.py` is that surface, measured in
`studies/FIELD_SURFACE_STUDY.md`.

A surface of this kind is the weakest thing the system does: it derives
nothing.  What it must do instead is be *exact about its own boundary*, and
that is what this file states.  The surface is a list of tables consulted in
a fixed order; each table holds rows, and each row holds named fields.  Four
things are proved about the lookup:

1. `lookup_eq_none_iff` — it answers nothing exactly when no table holds the
   pair.  The answerable `(row, field)` pairs are exactly the declared ones,
   so a refusal is a fact about the tables and never a failure of search.
   This is the field surface's counterpart of `GLM.Recipe.Spec` proving that
   the derivable coordinates are exactly the described ones.
2. `lookup_sound` — an answer is some table's own value.  Nothing on the path
   invents, interpolates or defaults a field.
3. `lookup_eq_isSome_mem_names` — the listing shape and the lookup shape
   agree: `fields of r` names exactly the fields `field n of r` answers.
   A row's advertised index cannot promise what the lookup refuses.
4. `lookup_append_of_isSome` and `lookup_cons_of_some` — priority is
   monotone.  A table appended after the ones that already answer cannot
   change an answer, and the first table holding the pair decides it.  That
   is what makes adding a table to the surface a safe operation rather than a
   re-measurement.
-/
import Mathlib

namespace GLM.FieldSurface

/-! ## 1.  Tables, rows and fields -/

/-- One addressable table: a label, and rows of named fields.  Both levels
are association lists, which is what a register row and a returned mapping
both are once they reach the surface. -/
structure Table where
  label : String
  rows : List (String × List (String × String))
  deriving Repr

namespace Table

/-- The fields of one row, or `none` when the table does not hold it. -/
def row (t : Table) (r : String) : Option (List (String × String)) :=
  (t.rows.find? (fun entry => entry.1 = r)).map Prod.snd

/-- One field of one row of one table. -/
def field (t : Table) (r n : String) : Option String :=
  (t.row r).bind fun fields =>
    (fields.find? (fun entry => entry.1 = n)).map Prod.snd

/-- The field names one table advertises for one row. -/
def names (t : Table) (r : String) : List String :=
  match t.row r with
  | some fields => fields.map Prod.fst
  | none => []

end Table

/-- The surface consults its tables in a fixed order and the first one
holding the pair answers. -/
def lookup : List Table → String → String → Option String
  | [], _, _ => none
  | t :: rest, r, n =>
      match t.field r n with
      | some v => some v
      | none => lookup rest r n

/-- The listing shape: every field name any table advertises for the row, in
table order. -/
def names (ts : List Table) (r : String) : List String :=
  ts.flatMap (fun t => t.names r)

/-! ## 2.  A name in a row's index is a name the row answers to -/

theorem find?_isSome_of_mem_keys {fields : List (String × String)}
    {n : String} (h : n ∈ fields.map Prod.fst) :
    (fields.find? (fun entry => entry.1 = n)).isSome := by
  induction fields with
  | nil => simp at h
  | cons head tail ih =>
      simp only [List.map_cons, List.mem_cons] at h
      by_cases hhead : head.1 = n
      · simp [List.find?_cons_of_pos, hhead]
      · have : n ∈ tail.map Prod.fst := by
          rcases h with h | h
          · exact absurd h.symm hhead
          · exact h
        simp [List.find?_cons_of_neg, hhead, ih this]

theorem mem_keys_of_find?_isSome {fields : List (String × String)}
    {n : String} (h : (fields.find? (fun entry => entry.1 = n)).isSome) :
    n ∈ fields.map Prod.fst := by
  induction fields with
  | nil => simp at h
  | cons head tail ih =>
      by_cases hhead : head.1 = n
      · simp [List.map_cons, hhead]
      · simp only [List.find?_cons, hhead, decide_false] at h
        simp [List.map_cons, ih h]

/-- One table answers a field exactly when it advertises it. -/
theorem Table.field_isSome_iff (t : Table) (r n : String) :
    (t.field r n).isSome ↔ n ∈ t.names r := by
  unfold Table.field Table.names
  cases hrow : t.row r with
  | none => simp
  | some fields =>
      simp only [Option.bind_some, Option.isSome_map]
      exact ⟨mem_keys_of_find?_isSome, find?_isSome_of_mem_keys⟩

/-! ## 3.  The boundary: what the surface refuses, and why -/

/-- **The answerable pairs are exactly the declared ones.**  The lookup is
silent precisely when every table is, so a refusal states a fact about the
tables rather than the failure of a search. -/
theorem lookup_eq_none_iff (ts : List Table) (r n : String) :
    lookup ts r n = none ↔ ∀ t ∈ ts, t.field r n = none := by
  induction ts with
  | nil => simp [lookup]
  | cons t rest ih =>
      cases hfield : t.field r n with
      | some v => simp [lookup, hfield]
      | none =>
          simp only [lookup, hfield, List.mem_cons, forall_eq_or_imp,
            true_and]
          exact ih

/-- **Nothing is invented.**  An answer is some table's own value for that
row and that field. -/
theorem lookup_sound {ts : List Table} {r n v : String}
    (h : lookup ts r n = some v) : ∃ t ∈ ts, t.field r n = some v := by
  induction ts with
  | nil => simp [lookup] at h
  | cons t rest ih =>
      cases hfield : t.field r n with
      | some w =>
          have : w = v := by
            simpa [lookup, hfield] using h
          exact ⟨t, by simp, by simp [hfield, this]⟩
      | none =>
          have : lookup rest r n = some v := by
            simpa [lookup, hfield] using h
          obtain ⟨u, hu, hval⟩ := ih this
          exact ⟨u, by simp [hu], hval⟩

/-- **The listing shape and the lookup shape agree.**  A row answers to a
name exactly when its advertised index carries that name, so the surface
cannot promise a field it refuses, nor hide one it holds. -/
theorem lookup_isSome_iff_mem_names (ts : List Table) (r n : String) :
    (lookup ts r n).isSome ↔ n ∈ names ts r := by
  induction ts with
  | nil => simp [lookup, names]
  | cons t rest ih =>
      cases hfield : t.field r n with
      | some v =>
          have : n ∈ t.names r := (t.field_isSome_iff r n).1 (by simp [hfield])
          simp [lookup, hfield, names, this]
      | none =>
          have hnot : n ∉ t.names r := by
            intro hmem
            have := (t.field_isSome_iff r n).2 hmem
            simp [hfield] at this
          simp [lookup, hfield, names, hnot, ih]

/-! ## 4.  Priority is monotone -/

/-- The first table holding the pair decides the answer. -/
theorem lookup_cons_of_some {t : Table} {ts : List Table} {r n v : String}
    (h : t.field r n = some v) : lookup (t :: ts) r n = some v := by
  simp [lookup, h]

/-- A table that does not hold the pair does not shadow the ones behind it. -/
theorem lookup_cons_of_none {t : Table} {ts : List Table} {r n : String}
    (h : t.field r n = none) : lookup (t :: ts) r n = lookup ts r n := by
  simp [lookup, h]

/-- **Appending a table never changes an answer.**  A surface that already
answers a pair answers it the same way after any table is added behind the
ones it has, so extending the surface is safe: no existing answer has to be
re-measured. -/
theorem lookup_append_of_isSome {ts us : List Table} {r n : String}
    (h : (lookup ts r n).isSome) :
    lookup (ts ++ us) r n = lookup ts r n := by
  induction ts with
  | nil => simp [lookup] at h
  | cons t rest ih =>
      cases hfield : t.field r n with
      | some v => simp [lookup, hfield]
      | none =>
          have hrest : (lookup rest r n).isSome := by
            simpa [lookup, hfield] using h
          simp [lookup, hfield, ih hrest]

/-- The surface as a whole answers a pair exactly when some table does. -/
theorem lookup_isSome_iff_exists (ts : List Table) (r n : String) :
    (lookup ts r n).isSome ↔ ∃ t ∈ ts, (t.field r n).isSome := by
  constructor
  · intro h
    obtain ⟨v, hv⟩ := Option.isSome_iff_exists.1 h
    obtain ⟨t, ht, hval⟩ := lookup_sound hv
    exact ⟨t, ht, by simp [hval]⟩
  · intro h
    by_contra hnone
    have : lookup ts r n = none := by
      simpa [Option.isSome_iff_ne_none] using hnone
    obtain ⟨t, ht, hsome⟩ := h
    have := (lookup_eq_none_iff ts r n).1 this t ht
    simp [this] at hsome

end GLM.FieldSurface
