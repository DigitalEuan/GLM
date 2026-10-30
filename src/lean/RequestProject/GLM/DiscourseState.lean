import Mathlib
import RequestProject.GLM.Conversation

/-!
# Discourse state: a set carried as a column, and the fourth shape

`GLM.Conversation` binds a pronoun to one name or refuses.  Its sharpest
refusal is the tie: fourteen rows attain the top of the lexicon's
`abstract_concrete` column, and *describe it* has fourteen equally good
referents.  Round 5 of the order of work (`glm_universal.runtime.discourse`,
Phase 92, `studies/DISCOURSE_STATE_STUDY.md`) reads that tie differently: a
fold whose end is attained by several rows **produced a set**, and *it* names
the set.  The question is then asked of every row and answered as a column.

This file states the new operation over the same turns, with one more bit per
turn — whether its answer side is a set the turn produced (a tie, or a column
turn) — and proves what it is worth.

* **A conservative extension** (`resolveD_eq_lift_resolve`): on a
  conversation in which no turn produced a set, the new operation is exactly
  Phase 55's.  Nothing is moved that the round did not declare.
* **A column is a produced set, every row of which answers**
  (`resolveD_column_licensed`, `resolveD_column_produced`,
  `resolveD_column_two_le`).  A set some of whose rows do not answer is
  refused `incomplete`, and the refusal is earned: one row answers and one
  does not (`resolveD_incomplete_hole`).
* **A column computes nothing** (`column_cell_eq_alone`): its `i`-th cell is
  the answer the `i`-th row gets asked alone.
* **The plural** (`resolvePlural`): *both of them* comes to a column of
  exactly two rows or a refusal (`resolvePlural_both_two`), never to a single
  binding (`resolvePlural_never_single`), and every row of its column answers
  (`resolvePlural_column_licensed`).
* **The one before that** (`resolvePrior`): it binds from strictly older
  turns than the one *that* names (`resolvePrior_cons_deciding`), and a newer
  turn that names nothing usable moves it no more than it moves *it*
  (`resolvePrior_stable_under_dead_turn`).
* The shipped cases, decided by computation: the tie carried as a column
  (`tie_is_a_column`), the hole refused (`tie_with_a_hole_is_incomplete`),
  *the one before that* walking past an unlicensed name
  (`prior_walks_past_unlicensed`), *both* across two turns
  (`both_across_turns`) and *them* with one referent (`them_one_row`).
-/

namespace GLM.DiscourseState

open GLM.Conversation (Licence licensed mem_licensed decideSide scan mentions
  sides)

/-- One turn: its two sides, and whether its answer side is a set the turn
produced (the tied winners of a fold, or the rows of a column turn). -/
structure Turn where
  answers : List String
  subjects : List String
  produced : Bool
deriving DecidableEq, Repr

/-- A conversation, newest turn first. -/
abbrev Script := List Turn

/-- Every refusal: Phase 55's three and the two this round adds. -/
inductive Reason where
  | noAntecedent
  | ambiguous
  | unlicensed
  /-- A set-valued referent some of whose rows do not answer. -/
  | incomplete
  /-- A plural with one referent, or *both* with other than two. -/
  | numberMismatch
deriving DecidableEq, Repr

/-- What a follow-up comes to: one row, a column of rows, or a refusal. -/
inductive Outcome where
  | bound (name : String)
  | column (rows : List String)
  | refused (reason : Reason)
deriving DecidableEq, Repr

/-- Phase 55's turn, forgetting the new bit. -/
def Turn.old (t : Turn) : GLM.Conversation.Turn := ⟨t.answers, t.subjects⟩

/-- Phase 55's outcomes, read as outcomes of this round. -/
def lift : GLM.Conversation.Outcome → Outcome
  | .bound x => .bound x
  | .refused .noAntecedent => .refused .noAntecedent
  | .refused .ambiguous => .refused .ambiguous
  | .refused .unlicensed => .refused .unlicensed

/-- A set: every row answers, or the set is incomplete, or no row answers
and the set does not decide. -/
def decideSet (L : Licence) (names : List String) : Option Outcome :=
  match licensed L names with
  | [] => none
  | _ :: _ =>
      if (licensed L names).length = names.length then some (.column names)
      else some (.refused .incomplete)

/-- One ordinary side, as Phase 55 decides it. -/
def decideOne (L : Licence) (names : List String) : Option Outcome :=
  (decideSide L names).map lift

/-- Whether a side is read as a set. -/
def isSet (produced : Bool) (names : List String) : Bool :=
  produced && decide (2 ≤ names.length)

/-- What one turn decides for a singular pronoun: the answer side first (as a
set when the turn produced one), then the subject side. -/
def decideTurn (L : Licence) (t : Turn) : Option Outcome :=
  match (if isSet t.produced t.answers then decideSet L t.answers
         else decideOne L t.answers) with
  | some o => some o
  | none => decideOne L t.subjects

/-- The first turn that decides, newest first: its decision and the turns
older than it. -/
def firstDecision {α : Type} (D : Turn → Option α) :
    Script → Option (α × Script)
  | [] => none
  | t :: rest =>
      match D t with
      | some o => some (o, rest)
      | none => firstDecision D rest

/-- Every name the conversation mentioned. -/
def mentionsD (c : Script) : List String :=
  c.flatMap (fun t => t.answers ++ t.subjects)

/-- Silence: Phase 55's two readings of it. -/
def silence (c : Script) : Outcome :=
  if mentionsD c = [] then .refused .noAntecedent else .refused .unlicensed

/-- **The operation** for *it*: bind one row, carry a set as a column, or
refuse. -/
def resolveD (L : Licence) (c : Script) : Outcome :=
  match firstDecision (decideTurn L) c with
  | some (o, _) => o
  | none => silence c

/-! ## §1  The conservative extension -/

lemma decideOne_eq_none {L : Licence} {names : List String} :
    decideOne L names = none ↔ decideSide L names = none := by
  unfold decideOne; cases decideSide L names <;> simp

lemma decideTurn_of_not_produced {L : Licence} {t : Turn}
    (h : t.produced = false) :
    decideTurn L t = (scan L (sides t.old)).map lift := by
  unfold decideTurn isSet
  simp only [h, Bool.false_and, Bool.false_eq_true, ↓reduceIte]
  unfold decideOne
  simp only [sides, Turn.old, scan]
  rcases decideSide L t.answers with _ | o
  · simp only [Option.map_none]
    rcases decideSide L t.subjects with _ | o'
    · rfl
    · rfl
  · rfl

lemma scan_append_sides {L : Licence} (s : List (List String))
    (rest : List (List String)) :
    scan L (s ++ rest) =
      match scan L s with
      | some o => some o
      | none => scan L rest := by
  induction s with
  | nil => rfl
  | cons a s ih =>
      simp only [List.cons_append, scan]
      rcases decideSide L a with _ | o
      · exact ih
      · rfl

lemma firstDecision_map_of_not_produced {L : Licence} {c : Script}
    (h : ∀ t ∈ c, t.produced = false) :
    (firstDecision (decideTurn L) c).map Prod.fst =
      (scan L ((c.map Turn.old).flatMap sides)).map lift := by
  induction c with
  | nil => rfl
  | cons t rest ih =>
      have ht := h t List.mem_cons_self
      have hr : ∀ u ∈ rest, u.produced = false :=
        fun u hu => h u (List.mem_cons_of_mem _ hu)
      simp only [firstDecision, List.map_cons, List.flatMap_cons]
      rw [scan_append_sides, decideTurn_of_not_produced ht]
      rcases scan L (sides t.old) with _ | o
      · simpa using ih hr
      · rfl

lemma mentionsD_eq {c : Script} :
    mentionsD c = mentions (c.map Turn.old) := by
  simp [mentionsD, mentions, Turn.old, List.flatMap_map]

/-- **Nothing moves that the round did not declare.**  On a conversation in
which no turn produced a set, the new operation is exactly Phase 55's. -/
theorem resolveD_eq_lift_resolve {L : Licence} {c : Script}
    (h : ∀ t ∈ c, t.produced = false) :
    resolveD L c = lift (GLM.Conversation.resolve L (c.map Turn.old)) := by
  have hm := firstDecision_map_of_not_produced (L := L) h
  unfold resolveD GLM.Conversation.resolve silence
  rcases hf : firstDecision (decideTurn L) c with _ | ⟨o, older⟩
  · rw [hf] at hm
    rcases hs : scan L ((c.map Turn.old).flatMap sides) with _ | o'
    · simp only [mentionsD_eq]
      split_ifs <;> rfl
    · rw [hs] at hm; simp at hm
  · rw [hf] at hm
    rcases hs : scan L ((c.map Turn.old).flatMap sides) with _ | o'
    · rw [hs] at hm; simp at hm
    · rw [hs] at hm
      simp only [Option.map_some, Option.some.injEq] at hm
      simpa using hm

/-! ## §2  What a column is -/

lemma decideSet_column {L : Licence} {names xs : List String}
    (h : decideSet L names = some (.column xs)) :
    xs = names ∧ ∀ x ∈ names, L x = true := by
  unfold decideSet at h
  rcases hl : licensed L names with _ | ⟨a, t⟩
  · rw [hl] at h; simp at h
  · rw [hl] at h
    simp only at h
    split_ifs at h with hlen
    · simp only [Option.some.injEq, Outcome.column.injEq] at h
      refine ⟨h.symm, ?_⟩
      have hfil : names.filter L = names := by
        apply List.filter_eq_self.2
        have := List.length_filter_eq_length_iff.1 (by
          rw [← hl] at hlen; simpa [licensed] using hlen)
        intro x hx; simpa using this x hx
      intro x hx
      have : x ∈ names.filter L := by rw [hfil]; exact hx
      simpa using (List.mem_filter.1 this).2
    · simp at h

lemma decideSet_incomplete {L : Licence} {names : List String}
    (h : decideSet L names = some (.refused .incomplete)) :
    (∃ x ∈ names, L x = true) ∧ (∃ y ∈ names, L y = false) := by
  unfold decideSet at h
  rcases hl : licensed L names with _ | ⟨a, t⟩
  · rw [hl] at h; simp at h
  · rw [hl] at h
    simp only at h
    split_ifs at h with hlen
    · simp at h
    · refine ⟨⟨a, ?_⟩, ?_⟩
      · have : a ∈ licensed L names := by rw [hl]; exact List.mem_cons_self
        exact (mem_licensed.1 this)
      · by_contra hall
        push_neg at hall
        apply hlen
        rw [← hl]
        unfold licensed
        congr 1
        apply List.filter_eq_self.2
        intro x hx
        have := hall x hx
        cases hL : L x <;> simp_all

lemma decideOne_not_column {L : Licence} {names xs : List String} :
    decideOne L names ≠ some (.column xs) := by
  unfold decideOne
  rcases decideSide L names with _ | o
  · simp
  · rcases o with x | r
    · simp [lift]
    · rcases r <;> simp [lift]

lemma decideOne_not_incomplete {L : Licence} {names : List String} :
    decideOne L names ≠ some (.refused .incomplete) := by
  unfold decideOne
  rcases decideSide L names with _ | o
  · simp
  · rcases o with x | r
    · simp [lift]
    · rcases r <;> simp [lift]

lemma decideTurn_column {L : Licence} {t : Turn} {xs : List String}
    (h : decideTurn L t = some (.column xs)) :
    t.produced = true ∧ xs = t.answers ∧ 2 ≤ xs.length ∧
      ∀ x ∈ xs, L x = true := by
  unfold decideTurn at h
  by_cases hs : isSet t.produced t.answers = true
  · rw [if_pos hs] at h
    rcases hd : decideSet L t.answers with _ | o
    · rw [hd] at h; exact absurd h decideOne_not_column
    · rw [hd] at h
      simp only [Option.some.injEq] at h
      subst h
      obtain ⟨rfl, hall⟩ := decideSet_column hd
      simp only [isSet, Bool.and_eq_true, decide_eq_true_eq] at hs
      exact ⟨hs.1, rfl, hs.2, hall⟩
  · rw [if_neg hs] at h
    rcases hd : decideOne L t.answers with _ | o
    · rw [hd] at h; exact absurd h decideOne_not_column
    · rw [hd] at h
      simp only [Option.some.injEq] at h
      subst h
      exact absurd hd decideOne_not_column

lemma decideTurn_incomplete {L : Licence} {t : Turn}
    (h : decideTurn L t = some (.refused .incomplete)) :
    t.produced = true ∧ (∃ x ∈ t.answers, L x = true) ∧
      (∃ y ∈ t.answers, L y = false) := by
  unfold decideTurn at h
  by_cases hs : isSet t.produced t.answers = true
  · rw [if_pos hs] at h
    rcases hd : decideSet L t.answers with _ | o
    · rw [hd] at h; exact absurd h decideOne_not_incomplete
    · rw [hd] at h
      simp only [Option.some.injEq] at h
      subst h
      simp only [isSet, Bool.and_eq_true] at hs
      exact ⟨hs.1, decideSet_incomplete hd⟩
  · rw [if_neg hs] at h
    rcases hd : decideOne L t.answers with _ | o
    · rw [hd] at h; exact absurd h decideOne_not_incomplete
    · rw [hd] at h
      simp only [Option.some.injEq] at h
      subst h
      exact absurd hd decideOne_not_incomplete

lemma firstDecision_some {α : Type} {D : Turn → Option α} {c : Script}
    {o : α} {older : Script}
    (h : firstDecision D c = some (o, older)) :
    ∃ t ∈ c, D t = some o := by
  induction c with
  | nil => simp [firstDecision] at h
  | cons t rest ih =>
      simp only [firstDecision] at h
      rcases hd : D t with _ | o'
      · rw [hd] at h
        obtain ⟨u, hu, he⟩ := ih h
        exact ⟨u, List.mem_cons_of_mem _ hu, he⟩
      · rw [hd] at h
        simp only [Option.some.injEq, Prod.mk.injEq] at h
        exact ⟨t, List.mem_cons_self, h.1 ▸ hd⟩

lemma silence_ne_column {c : Script} {xs : List String} :
    silence c ≠ .column xs := by
  unfold silence; split_ifs <;> simp

lemma silence_ne_incomplete {c : Script} :
    silence c ≠ .refused .incomplete := by
  unfold silence; split_ifs <;> simp

lemma resolveD_column_turn {L : Licence} {c : Script} {xs : List String}
    (h : resolveD L c = .column xs) :
    ∃ t ∈ c, decideTurn L t = some (.column xs) := by
  unfold resolveD at h
  rcases hf : firstDecision (decideTurn L) c with _ | ⟨o, older⟩
  · rw [hf] at h; exact absurd h silence_ne_column
  · rw [hf] at h
    simp only at h
    subst h
    exact firstDecision_some hf

/-- **Every row of a column answers.** -/
theorem resolveD_column_licensed {L : Licence} {c : Script} {xs : List String}
    (h : resolveD L c = .column xs) : ∀ x ∈ xs, L x = true := by
  obtain ⟨t, _, ht⟩ := resolveD_column_turn h
  exact (decideTurn_column ht).2.2.2

/-- **A column is a set some turn produced**, and it is that set whole. -/
theorem resolveD_column_produced {L : Licence} {c : Script}
    {xs : List String} (h : resolveD L c = .column xs) :
    ∃ t ∈ c, t.produced = true ∧ t.answers = xs := by
  obtain ⟨t, hmem, ht⟩ := resolveD_column_turn h
  obtain ⟨hp, hx, _, _⟩ := decideTurn_column ht
  exact ⟨t, hmem, hp, hx.symm⟩

/-- **A column has at least two rows** — a set of one is a single binding. -/
theorem resolveD_column_two_le {L : Licence} {c : Script} {xs : List String}
    (h : resolveD L c = .column xs) : 2 ≤ xs.length := by
  obtain ⟨t, _, ht⟩ := resolveD_column_turn h
  exact (decideTurn_column ht).2.2.1

/-- **`incomplete` is earned**: some produced set holds a row that answers and
a row that does not — a hole, which refuses the column. -/
theorem resolveD_incomplete_hole {L : Licence} {c : Script}
    (h : resolveD L c = .refused .incomplete) :
    ∃ t ∈ c, t.produced = true ∧ (∃ x ∈ t.answers, L x = true) ∧
      (∃ y ∈ t.answers, L y = false) := by
  unfold resolveD at h
  rcases hf : firstDecision (decideTurn L) c with _ | ⟨o, older⟩
  · rw [hf] at h; exact absurd h silence_ne_incomplete
  · rw [hf] at h
    simp only at h
    subst h
    obtain ⟨t, hmem, ht⟩ := firstDecision_some hf
    exact ⟨t, hmem, decideTurn_incomplete ht⟩

/-- The column's cells: each row asked alone. -/
def columnCells {α : Type} (ask : String → α) (rows : List String) : List α :=
  rows.map ask

/-- **A column computes nothing**: its `i`-th cell is the answer the `i`-th
row gets asked alone, and it has one cell per row. -/
theorem column_cell_eq_alone {α : Type} (ask : String → α)
    (rows : List String) (i : ℕ) (hi : i < rows.length) :
    (columnCells ask rows).length = rows.length ∧
      (columnCells ask rows)[i]'(by simpa [columnCells] using hi) =
        ask (rows[i]'hi) := by
  simp [columnCells]

/-! ## §3  The plural -/

/-- One side, read for a plural: two or more names are a set; one name is a
single row. -/
def decidePluralSide (L : Licence) (names : List String) : Option Outcome :=
  if 2 ≤ names.length then decideSet L names else decideOne L names

/-- One turn, read for a plural. -/
def decidePluralTurn (L : Licence) (t : Turn) : Option Outcome :=
  match decidePluralSide L t.answers with
  | some o => some o
  | none => decidePluralSide L t.subjects

/-- **The plural.**  `number` is the number the phrasing states: `some 2` for
*both of them*, `none` for *them*.  A set decides; a single row reads on only
for *both*, to the single row of the next deciding turn. -/
def resolvePlural (L : Licence) (number : Option ℕ) (c : Script) : Outcome :=
  match firstDecision (decidePluralTurn L) c with
  | none => silence c
  | some (.column xs, _) =>
      match number with
      | some n => if xs.length = n then .column xs
                  else .refused .numberMismatch
      | none => .column xs
  | some (.bound x, older) =>
      if number = some 2 then
        match firstDecision (decidePluralTurn L) older with
        | some (.bound y, _) => .column [y, x]
        | _ => .refused .numberMismatch
      else .refused .numberMismatch
  | some (.refused r, _) => .refused r

lemma decidePluralSide_bound {L : Licence} {names : List String} {x : String}
    (h : decidePluralSide L names = some (.bound x)) : L x = true := by
  unfold decidePluralSide at h
  split_ifs at h with h2
  · unfold decideSet at h
    rcases hl : licensed L names with _ | ⟨a, t⟩
    · rw [hl] at h; simp at h
    · rw [hl] at h; simp only at h; split_ifs at h <;> simp at h
  · unfold decideOne at h
    rcases hd : decideSide L names with _ | o
    · rw [hd] at h; simp at h
    · rw [hd] at h
      rcases o with y | r
      · simp only [Option.map_some, lift, Option.some.injEq,
          Outcome.bound.injEq] at h
        subst h
        exact (mem_licensed.1 (GLM.Conversation.decideSide_bound hd)).2
      · rcases r <;> simp [lift] at h

lemma decidePluralSide_column {L : Licence} {names xs : List String}
    (h : decidePluralSide L names = some (.column xs)) :
    ∀ x ∈ xs, L x = true := by
  unfold decidePluralSide at h
  split_ifs at h
  · obtain ⟨rfl, hall⟩ := decideSet_column h; exact hall
  · exact absurd h decideOne_not_column

lemma decidePluralTurn_bound {L : Licence} {t : Turn} {x : String}
    (h : decidePluralTurn L t = some (.bound x)) : L x = true := by
  unfold decidePluralTurn at h
  rcases hd : decidePluralSide L t.answers with _ | o
  · rw [hd] at h; exact decidePluralSide_bound h
  · rw [hd] at h
    simp only [Option.some.injEq] at h
    subst h
    exact decidePluralSide_bound hd

lemma decidePluralTurn_column {L : Licence} {t : Turn} {xs : List String}
    (h : decidePluralTurn L t = some (.column xs)) :
    ∀ x ∈ xs, L x = true := by
  unfold decidePluralTurn at h
  rcases hd : decidePluralSide L t.answers with _ | o
  · rw [hd] at h; exact decidePluralSide_column h
  · rw [hd] at h
    simp only [Option.some.injEq] at h
    subst h
    exact decidePluralSide_column hd

/-- **A plural never binds a single row.** -/
theorem resolvePlural_never_single {L : Licence} {n : Option ℕ} {c : Script}
    {x : String} : resolvePlural L n c ≠ .bound x := by
  unfold resolvePlural
  rcases firstDecision (decidePluralTurn L) c with _ | ⟨o, older⟩
  · unfold silence; split_ifs <;> simp
  · rcases o with y | xs | r
    · simp only
      split_ifs
      · rcases firstDecision (decidePluralTurn L) older with _ | ⟨o', _⟩
        · simp
        · rcases o' <;> simp
      · simp
    · rcases n with _ | m
      · simp
      · simp only; split_ifs <;> simp
    · simp

/-- ***Both of them* is two rows or a refusal.** -/
theorem resolvePlural_both_two {L : Licence} {c : Script} {xs : List String}
    (h : resolvePlural L (some 2) c = .column xs) : xs.length = 2 := by
  unfold resolvePlural at h
  rcases hf : firstDecision (decidePluralTurn L) c with _ | ⟨o, older⟩
  · rw [hf] at h; exact absurd h silence_ne_column
  · rw [hf] at h
    rcases o with y | ys | r
    · simp only [if_true] at h
      rcases hg : firstDecision (decidePluralTurn L) older with _ | ⟨o', _⟩
      · rw [hg] at h; simp at h
      · rw [hg] at h
        rcases o' with z | _ | _
        · simp only [Outcome.column.injEq] at h; subst h; rfl
        · simp at h
        · simp at h
    · simp only at h
      split_ifs at h with hlen
      · simp only [Outcome.column.injEq] at h; subst h; exact hlen
    · simp at h

/-- **Every row of a plural's column answers.** -/
theorem resolvePlural_column_licensed {L : Licence} {n : Option ℕ}
    {c : Script} {xs : List String} (h : resolvePlural L n c = .column xs) :
    ∀ x ∈ xs, L x = true := by
  unfold resolvePlural at h
  rcases hf : firstDecision (decidePluralTurn L) c with _ | ⟨o, older⟩
  · rw [hf] at h; exact absurd h silence_ne_column
  · rw [hf] at h
    obtain ⟨t, _, ht⟩ := firstDecision_some hf
    rcases o with y | ys | r
    · simp only at h
      split_ifs at h
      · rcases hg : firstDecision (decidePluralTurn L) older with _ | ⟨o', _⟩
        · rw [hg] at h; simp at h
        · rw [hg] at h
          rcases o' with z | _ | _
          · simp only [Outcome.column.injEq] at h
            subst h
            obtain ⟨u, _, hu⟩ := firstDecision_some hg
            intro w hw
            simp only [List.mem_cons, List.not_mem_nil, or_false] at hw
            rcases hw with rfl | rfl
            · exact decidePluralTurn_bound hu
            · exact decidePluralTurn_bound ht
          · simp at h
          · simp at h
    · have hys := decidePluralTurn_column ht
      rcases n with _ | m
      · simp only [Outcome.column.injEq] at h; subst h; exact hys
      · simp only at h
        split_ifs at h
        · simp only [Outcome.column.injEq] at h; subst h; exact hys
    · simp at h

/-! ## §4  The one before that -/

/-- **The one before that.**  *That* is the first turn that decides; the
referent is what the first deciding turn **older** than it decides. -/
def resolvePrior (L : Licence) (c : Script) : Outcome :=
  match firstDecision (decideTurn L) c with
  | none => silence c
  | some (_, older) =>
      match firstDecision (decideTurn L) older with
      | some (o, _) => o
      | none => .refused .noAntecedent

/-- **It binds from strictly older turns.**  When the newest turn decides,
*that* is that turn, and the referent is decided by the turns before it
alone. -/
theorem resolvePrior_cons_deciding {L : Licence} {t : Turn} {rest : Script}
    {o : Outcome} (ht : decideTurn L t = some o) :
    resolvePrior L (t :: rest) =
      match firstDecision (decideTurn L) rest with
      | some (o', _) => o'
      | none => .refused .noAntecedent := by
  simp [resolvePrior, firstDecision, ht]

lemma decideTurn_dead {L : Licence} {t : Turn}
    (hdead : ∀ y ∈ t.answers ++ t.subjects, L y = false) :
    decideTurn L t = none := by
  have hans : licensed L t.answers = [] := by
    rw [List.eq_nil_iff_forall_not_mem]
    intro y hy
    obtain ⟨hmem, hL⟩ := mem_licensed.1 hy
    rw [hdead y (List.mem_append_left _ hmem)] at hL
    exact absurd hL (by simp)
  have hsub : licensed L t.subjects = [] := by
    rw [List.eq_nil_iff_forall_not_mem]
    intro y hy
    obtain ⟨hmem, hL⟩ := mem_licensed.1 hy
    rw [hdead y (List.mem_append_right _ hmem)] at hL
    exact absurd hL (by simp)
  have h1 : decideSet L t.answers = none := by unfold decideSet; rw [hans]
  have h2 : decideOne L t.answers = none := by
    unfold decideOne decideSide; rw [hans]; rfl
  have h3 : decideOne L t.subjects = none := by
    unfold decideOne decideSide; rw [hsub]; rfl
  unfold decideTurn
  split_ifs <;> simp [h1, h2, h3]

/-- **A newer turn that names nothing usable does not move it.** -/
theorem resolvePrior_stable_under_dead_turn {L : Licence} {t : Turn}
    {c : Script} (hdead : ∀ y ∈ t.answers ++ t.subjects, L y = false)
    (hc : firstDecision (decideTurn L) c ≠ none) :
    resolvePrior L (t :: c) = resolvePrior L c := by
  have hd := decideTurn_dead (L := L) hdead
  unfold resolvePrior
  simp only [firstDecision, hd]
  rcases hf : firstDecision (decideTurn L) c with _ | ⟨o, older⟩
  · exact absurd hf hc
  · rfl

/-! ## §5  The shipped cases, decided -/

/-- **The tie, carried.**  Phase 55's `tie_is_refused` — two licensed tied
winners, refused `ambiguous` — is now a column of both, because the turn
produced them as one set. -/
theorem tie_is_a_column :
    resolveD (fun _ => true) [⟨["atom", "bond"], [], true⟩]
      = .column ["atom", "bond"] := by
  decide

/-- The same two winners named by a comparison, not produced by a fold, are
still ambiguous. -/
theorem comparison_still_ambiguous :
    resolveD (fun _ => true) [⟨[], ["C", "O"], false⟩]
      = .refused .ambiguous := by
  decide

/-- **A hole refuses the column**: of the tie `atom, C`, only `C` holds an
electronegativity. -/
theorem tie_with_a_hole_is_incomplete :
    resolveD (fun s => s == "C") [⟨["atom", "C"], [], true⟩]
      = .refused .incomplete := by
  decide

/-- A set no row of which answers does not decide, and the older turn does. -/
theorem dead_set_walked_past :
    resolveD (fun s => s == "C")
      [⟨["carbonate ion", "sulfate ion"], [], true⟩, ⟨[], ["C"], false⟩]
      = .bound "C" := by
  decide

/-- ***The one before that* walks past an unlicensed name.**  *describe
carbon; describe oxygen; describe water; field electronegativity_pauling of
the one before that*: water answers nothing, so *that* is oxygen and the
referent is carbon. -/
theorem prior_walks_past_unlicensed :
    resolvePrior (fun s => s == "C" || s == "O")
      [⟨[], ["water"], false⟩, ⟨[], ["O"], false⟩, ⟨[], ["C"], false⟩]
      = .bound "C" := by
  decide

/-- ***Both of them* across two turns of one row each**, in the order they
were named. -/
theorem both_across_turns :
    resolvePlural (fun _ => true) (some 2)
      [⟨[], ["O"], false⟩, ⟨[], ["C"], false⟩] = .column ["C", "O"] := by
  decide

/-- ***Them* with one referent is a number mismatch.** -/
theorem them_one_row :
    resolvePlural (fun _ => true) none [⟨[], ["C"], false⟩]
      = .refused .numberMismatch := by
  decide

/-- ***Both* of a fourteen-row set — here three — is a number mismatch.** -/
theorem both_of_three :
    resolvePlural (fun _ => true) (some 2) [⟨["a", "b", "c"], [], true⟩]
      = .refused .numberMismatch := by
  decide

end GLM.DiscourseState
