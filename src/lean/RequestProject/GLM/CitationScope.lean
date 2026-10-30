module

public import Mathlib

/-!
# Citations read in Lean's scope

`studies/CITATION_SCOPE_STUDY.md` (Phase 101) repairs the citation reader of
`glm_universal/reasoning/lean_address.py`.  Up to Phase 100 a token
was resolved by its short name wherever that short name was unique in the
development, so a bound variable `a` read as a citation of
`GLM.Heisenberg.a`.  The repaired reader follows Lean's own order for an
identifier, as far as a reader of the text can see it.  This file states that
order as a function and proves the properties the study relies on.

## 1.  The resolver

A name is a list of components.  `candidates scope opens tok` lists, in
Lean's order, the full names a token `tok` may denote from inside the
declaration `scope`: `P ++ tok` for every non-empty prefix `P` of `scope`,
longest first; then `O ++ tok` for every opened namespace `O`; then `tok` at
the root.  `resolve` returns the first candidate that is a declaration of the
corpus, unless the token's head is bound locally.

* `resolve_bound` — a token whose head is a local is never a citation.
* `resolve_mem` — a resolved name is a declaration of the corpus.
* `resolve_first` — it is the *first* candidate in Lean's order that is one.
* `cites_mem`, `cites_ne_self` — the cited set holds only corpus
  declarations other than the citing one.
* `cites_antitone` — binding more names can only remove citations.

## 2.  The leak, as a counter-model

`legacy` is the Phase 100 rule: a token resolves by its unique short name
anywhere.  `legacy_reads_bound_variable` exhibits the leak on a two-line
corpus — the bound variable `a` of `GLM.Gen3.foo` is read as a citation of
`GLM.Heisenberg.a` — while `scoped_ignores_bound_variable` says the repaired
resolver does not, even when `a` is *not* bound, because `GLM.Heisenberg` is
not in scope.

## 3.  The type-word repair

`typeCount ws text` counts the tokens of `text` that are type words.
`typeCount_rename` — a renaming that fixes every type word and sends no other
token to one leaves the count unchanged: exactly the anonymiser's renaming,
so the carrier coordinates cannot move under it.  `infixCount` is the
Phase 100 rule (a type word counted inside any token), and
`infixCount_not_rename_invariant` is the counterexample: renaming
`IntSet` to a placeholder moves it.
-/

@[expose] public section

namespace GLM.CitationScope

/-- A Lean name, as its list of components. -/
abbrev LName := List String

/-! ## 1.  The resolver -/

/-- The non-empty prefixes of a name, longest first. -/
def prefixes (p : LName) : List LName :=
  (List.range p.length).reverse.map fun k => p.take (k + 1)

/-- The full names a token may denote from inside `scope`, in Lean's order. -/
def candidates (scope : LName) (opens : List LName) (tok : LName) : List LName :=
  (prefixes scope).map (· ++ tok) ++ opens.map (· ++ tok) ++ [tok]

/-- Resolve a token: nothing if its head is local, otherwise the first
candidate in Lean's order that is a declaration of the corpus. -/
def resolve (corpus : List LName) (locals : List String) (scope : LName)
    (opens : List LName) (tok : LName) : Option LName :=
  match tok with
  | [] => none
  | h :: _ => if h ∈ locals then none
              else (candidates scope opens tok).find? (· ∈ corpus)

/-- **A local shadows every declaration.** -/
theorem resolve_bound (corpus : List LName) (locals : List String) (scope : LName)
    (opens : List LName) (h : String) (t : List String) (hb : h ∈ locals) :
    resolve corpus locals scope opens (h :: t) = none := by
  simp [resolve, hb]

/-- **A resolved name is a declaration of the corpus.** -/
theorem resolve_mem {corpus : List LName} {locals : List String} {scope : LName}
    {opens : List LName} {tok n : LName}
    (hr : resolve corpus locals scope opens tok = some n) : n ∈ corpus := by
  unfold resolve at hr
  split at hr
  · simp at hr
  · split at hr
    · simp at hr
    · simpa using List.find?_some hr

/-- **Resolution is the first match in Lean's order.** -/
theorem resolve_first {corpus : List LName} {locals : List String} {scope : LName}
    {opens : List LName} {tok n : LName}
    (hr : resolve corpus locals scope opens tok = some n) :
    ∃ as bs, candidates scope opens tok = as ++ n :: bs ∧ ∀ a ∈ as, a ∉ corpus := by
  unfold resolve at hr
  split at hr
  · simp at hr
  · split at hr
    · simp at hr
    · obtain ⟨_, as, bs, he, hall⟩ := List.find?_eq_some_iff_append.mp hr
      exact ⟨as, bs, he, fun a ha => by simpa using hall a ha⟩

/-- The declarations a token list cites from inside `self`. -/
def cites (corpus : List LName) (locals : List String) (self : LName)
    (opens : List LName) (toks : List LName) : List LName :=
  (toks.filterMap (resolve corpus locals (self.dropLast) opens)).filter (· ≠ self)

theorem cites_mem {corpus : List LName} {locals : List String} {self : LName}
    {opens : List LName} {toks : List LName} {n : LName}
    (h : n ∈ cites corpus locals self opens toks) : n ∈ corpus := by
  simp only [cites, List.mem_filter, List.mem_filterMap] at h
  obtain ⟨⟨t, _, ht⟩, _⟩ := h
  exact resolve_mem ht

theorem cites_ne_self {corpus : List LName} {locals : List String} {self : LName}
    {opens : List LName} {toks : List LName} {n : LName}
    (h : n ∈ cites corpus locals self opens toks) : n ≠ self := by
  simp only [cites, List.mem_filter, decide_eq_true_eq] at h
  exact h.2

/-- Binding more names only removes citations, and never adds one. -/
theorem cites_antitone {corpus : List LName} {locals more : List String}
    {self : LName} {opens : List LName} {toks : List LName} {n : LName}
    (h : n ∈ cites corpus (locals ++ more) self opens toks) :
    n ∈ cites corpus locals self opens toks := by
  simp only [cites, List.mem_filter, List.mem_filterMap] at h ⊢
  obtain ⟨⟨t, ht, hr⟩, hne⟩ := h
  refine ⟨⟨t, ht, ?_⟩, hne⟩
  unfold resolve at hr ⊢
  split at hr
  · simp at hr
  · rename_i hd tl
    by_cases hb : hd ∈ locals
    · simp [hb] at hr
    · have hb' : hd ∉ locals ++ more ∨ hd ∈ locals ++ more := by tauto
      rcases hb' with hb' | hb'
      · simpa [hb, hb'] using hr
      · simp [hb'] at hr

/-! ## 2.  The leak, as a counter-model -/

/-- The Phase 100 rule: a token resolves by its unique short name anywhere in
the corpus, whatever is bound and whatever is in scope. -/
def legacy (corpus : List LName) (tok : LName) : Option LName :=
  match tok with
  | [s] => match corpus.filter (fun n => n.getLast? = some s) with
           | [n] => some n
           | _ => none
  | _ => none

/-- A two-declaration corpus: `GLM.Heisenberg.a` and `GLM.Gen3.foo`. -/
def toyCorpus : List LName := [["GLM", "Heisenberg", "a"], ["GLM", "Gen3", "foo"]]

/-- **The leak.** Inside `GLM.Gen3.foo`, where `a` is a bound variable, the
legacy rule reads `a` as a citation of `GLM.Heisenberg.a`. -/
theorem legacy_reads_bound_variable :
    legacy toyCorpus ["a"] = some ["GLM", "Heisenberg", "a"] := by decide

/-- **The repair.** The scoped resolver does not, whether `a` is bound or
not: bound, it shadows; unbound, `GLM.Heisenberg` is not in scope. -/
theorem scoped_ignores_bound_variable :
    resolve toyCorpus ["a"] ["GLM", "Gen3"] [] ["a"] = none ∧
    resolve toyCorpus [] ["GLM", "Gen3"] [] ["a"] = none := by decide

/-- …while inside `GLM.Heisenberg` an unbound `a` is the declaration. -/
theorem scoped_reads_in_scope :
    resolve toyCorpus [] ["GLM", "Heisenberg", "b"] [] ["a"] =
      some ["GLM", "Heisenberg", "a"] := by decide

/-! ## 3.  The type-word repair -/

/-- How many tokens of `text` are type words. -/
def typeCount {α : Type*} [DecidableEq α] (ws : List α) (text : List α) : ℕ :=
  (text.filter (· ∈ ws)).length

/-- **The carrier counts survive the anonymiser.**  A renaming that fixes
every type word and sends no other token to one leaves the count unchanged. -/
theorem typeCount_rename {α : Type*} [DecidableEq α] (ws : List α) (r : α → α)
    (hfix : ∀ w ∈ ws, r w = w) (hout : ∀ t, t ∉ ws → r t ∉ ws)
    (text : List α) : typeCount ws (text.map r) = typeCount ws text := by
  unfold typeCount
  induction text with
  | nil => rfl
  | cons t ts ih =>
    by_cases ht : t ∈ ws
    · simp [ht, hfix t ht, ih]
    · simp [ht, hout t ht, ih]

/-- The Phase 100 rule: a type word counted wherever it occurs inside a
token, tokens read as their lists of characters. -/
def infixCount (ws : List (List Char)) (text : List (List Char)) : ℕ :=
  (text.filter fun t => ws.any fun w => decide (w <:+: t)).length

/-- **The leak in the feature map.**  Renaming the identifier `IntSet` to the
placeholder `v0` moves the Phase 100 count of the type word `Int`, while the
repaired count is unmoved. -/
theorem infixCount_not_rename_invariant :
    infixCount [['I', 'n', 't']] [['I', 'n', 't', 'S', 'e', 't']] = 1 ∧
    infixCount [['I', 'n', 't']] [['v', '0']] = 0 ∧
    typeCount [['I', 'n', 't']] [['I', 'n', 't', 'S', 'e', 't']] =
      typeCount [['I', 'n', 't']] [['v', '0']] := by
  decide

end GLM.CitationScope
