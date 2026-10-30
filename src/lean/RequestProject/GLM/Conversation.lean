import Mathlib

/-!
# The turn that refers back to an earlier turn

`describe carbon` is a whole question.  `describe it` is not one, and the
shipped parser says so.  Yet *describe it* is how the second question is
actually asked, and binding the pronoun is the only thing standing between a
register the system can already read and a conversation it can hold.

This file states the binding and proves what it is worth.  A `Turn` is what
one turn leaves behind: the names it **produced** (its answer side) and the
names it was **about** (its subject side).  A `Script` is the conversation,
newest turn first.  A `Licence` is the only test the operation applies to a
candidate: *does the question, asked of this candidate, have an answer?*  In
the shipped system that is the solver itself — the candidate is substituted
for the pronoun and the query is run — so the reference is decided by what the
registers hold rather than by where the words fell.

* Recency decides *between* turns and licensing decides *within* one: the
  sides are scanned newest first, answer side before subject side, and the
  first side with exactly one licensed candidate binds it
  (`resolve_bound_licensed`, `resolve_bound_mem`).
* Silence is a fact rather than a failed search.  `.noAntecedent` says the
  conversation named nothing at all (`resolve_noAntecedent_iff`);
  `.unlicensed` says it named things and not one of them answers
  (`resolve_unlicensed_all_refused`); `.ambiguous` says the side that decided
  offered at least two (`resolve_ambiguous_two_licensed`) — fourteen rows
  attain the top of the lexicon's `abstract_concrete` column, and naming one
  of them would be a choice the conversation does not make.
* A turn that names nothing usable cannot move a binding that was already
  decided (`resolve_stable_under_unlicensed_turn`).
* And the cheap rule is refuted rather than argued with:
  `most_recent_mention_is_not_the_antecedent` exhibits a conversation in which
  the most recently mentioned name does not answer the question and an older
  one does, which is the shipped case *describe carbon; describe water; field
  electronegativity_pauling of it* — the molecule table holds no
  electronegativity and the element table does.

The shipped counterpart is `glm_universal.runtime.conversation`, whose tests
pin these same properties on the real session.
-/

namespace GLM.Conversation

/-- What one turn leaves behind: the names it produced and the names it was
about.

The two sides are kept apart because they are consulted in order: a turn that
produced a name is a turn about that name, so the answer side outranks the
subject side. -/
structure Turn where
  /-- The names the turn produced — the winners of a fold, the answer of an
  analogy. -/
  answers : List String
  /-- The names the turn was asked about. -/
  subjects : List String
deriving DecidableEq, Repr

/-- A conversation: its turns, **newest first**. -/
abbrev Script := List Turn

/-- Why a follow-up was refused. -/
inductive Reason where
  /-- The conversation names nothing the pronoun could stand for. -/
  | noAntecedent
  /-- The side that decided offers more than one licensed candidate. -/
  | ambiguous
  /-- Candidates exist and not one of them answers the question. -/
  | unlicensed
deriving DecidableEq, Repr

/-- What a follow-up comes to: a binding, or a refusal with its reason. -/
inductive Outcome where
  /-- The pronoun binds to this name. -/
  | bound (name : String)
  /-- No binding, for this reason. -/
  | refused (reason : Reason)
deriving DecidableEq, Repr

/-- The licensing test: whether the question asked of this candidate has an
answer.  In the shipped system this is the solver. -/
abbrev Licence := String → Bool

/-- The candidates of a side that the licence admits. -/
def licensed (L : Licence) (names : List String) : List String :=
  names.filter L

/-- The two sides of a turn, in the order they are consulted. -/
def sides (t : Turn) : List (List String) := [t.answers, t.subjects]

/-- What one side decides: nothing, a binding, or a refusal for ambiguity. -/
def decideSide (L : Licence) (names : List String) : Option Outcome :=
  match licensed L names with
  | [] => none
  | [x] => some (.bound x)
  | _ :: _ :: _ => some (.refused .ambiguous)

/-- Consult the sides in order and stop at the first that decides. -/
def scan (L : Licence) : List (List String) → Option Outcome
  | [] => none
  | s :: rest =>
      match decideSide L s with
      | some o => some o
      | none => scan L rest

/-- Every name the conversation has mentioned. -/
def mentions (c : Script) : List String :=
  c.flatMap (fun t => t.answers ++ t.subjects)

/-- **The operation.**  Bind the pronoun, or refuse and say why. -/
def resolve (L : Licence) (c : Script) : Outcome :=
  match scan L (c.flatMap sides) with
  | some o => o
  | none =>
      if mentions c = [] then .refused .noAntecedent
      else .refused .unlicensed

/-! ## §1  Reading one side -/

lemma mem_licensed {L : Licence} {names : List String} {x : String} :
    x ∈ licensed L names ↔ x ∈ names ∧ L x = true := by
  simp [licensed, List.mem_filter]

lemma decideSide_bound {L : Licence} {names : List String} {x : String}
    (h : decideSide L names = some (.bound x)) : x ∈ licensed L names := by
  unfold decideSide at h
  rcases hl : licensed L names with _ | ⟨a, t⟩
  · rw [hl] at h; simp at h
  · cases t with
    | nil => rw [hl] at h; simp at h; simp [h]
    | cons b u => rw [hl] at h; simp at h

lemma decideSide_ambiguous {L : Licence} {names : List String}
    (h : decideSide L names = some (.refused .ambiguous)) :
    2 ≤ (licensed L names).length := by
  unfold decideSide at h
  rcases hl : licensed L names with _ | ⟨a, t⟩
  · rw [hl] at h; simp at h
  · cases t with
    | nil => rw [hl] at h; simp at h
    | cons b u => simp

lemma decideSide_none {L : Licence} {names : List String}
    (h : decideSide L names = none) : licensed L names = [] := by
  unfold decideSide at h
  rcases hl : licensed L names with _ | ⟨a, t⟩
  · rfl
  · cases t with
    | nil => rw [hl] at h; simp at h
    | cons b u => rw [hl] at h; simp at h

/-- A side refuses for one reason only: two licensed candidates.  The other
two refusals are facts about the whole conversation, not about a side. -/
lemma decideSide_refuses_only_for_ambiguity {L : Licence}
    {names : List String} {r : Reason}
    (h : decideSide L names = some (.refused r)) : r = .ambiguous := by
  unfold decideSide at h
  rcases hl : licensed L names with _ | ⟨a, t⟩
  · rw [hl] at h; simp at h
  · cases t with
    | nil => rw [hl] at h; simp at h
    | cons b u => rw [hl] at h; simp at h; exact h.symm

/-! ## §2  Reading the scan -/

/-- Whatever the scan returns, some side returned it. -/
lemma scan_some {L : Licence} {ss : List (List String)} {o : Outcome}
    (h : scan L ss = some o) : ∃ s ∈ ss, decideSide L s = some o := by
  induction ss with
  | nil => simp [scan] at h
  | cons s rest ih =>
      unfold scan at h
      rcases hd : decideSide L s with _ | o'
      · rw [hd] at h
        obtain ⟨s', hs', he⟩ := ih h
        exact ⟨s', List.mem_cons_of_mem _ hs', he⟩
      · rw [hd] at h
        simp only [Option.some.injEq] at h
        subst h
        exact ⟨s, List.mem_cons_self, hd⟩

lemma scan_bound {L : Licence} {ss : List (List String)} {x : String}
    (h : scan L ss = some (.bound x)) : ∃ s ∈ ss, x ∈ licensed L s := by
  obtain ⟨s, hs, hd⟩ := scan_some h
  exact ⟨s, hs, decideSide_bound hd⟩

lemma scan_ambiguous {L : Licence} {ss : List (List String)}
    (h : scan L ss = some (.refused .ambiguous)) :
    ∃ s ∈ ss, 2 ≤ (licensed L s).length := by
  obtain ⟨s, hs, hd⟩ := scan_some h
  exact ⟨s, hs, decideSide_ambiguous hd⟩

lemma scan_not_noAntecedent {L : Licence} {ss : List (List String)} :
    scan L ss ≠ some (.refused .noAntecedent) := by
  intro h
  obtain ⟨_, _, hd⟩ := scan_some h
  exact absurd (decideSide_refuses_only_for_ambiguity hd) (by decide)

lemma scan_not_unlicensed {L : Licence} {ss : List (List String)} :
    scan L ss ≠ some (.refused .unlicensed) := by
  intro h
  obtain ⟨_, _, hd⟩ := scan_some h
  exact absurd (decideSide_refuses_only_for_ambiguity hd) (by decide)

lemma scan_none {L : Licence} {ss : List (List String)}
    (h : scan L ss = none) : ∀ s ∈ ss, licensed L s = [] := by
  induction ss with
  | nil => simp
  | cons s rest ih =>
      unfold scan at h
      rcases hd : decideSide L s with _ | o
      · rw [hd] at h
        intro s' hs'
        rcases List.mem_cons.1 hs' with rfl | hmem
        · exact decideSide_none hd
        · exact ih h s' hmem
      · rw [hd] at h; simp at h

lemma scan_of_all_unlicensed {L : Licence} {ss : List (List String)}
    (h : ∀ s ∈ ss, licensed L s = []) : scan L ss = none := by
  induction ss with
  | nil => rfl
  | cons s rest ih =>
      have hs : licensed L s = [] := h s List.mem_cons_self
      have hd : decideSide L s = none := by unfold decideSide; rw [hs]
      unfold scan
      rw [hd]
      exact ih fun s' hs' => h s' (List.mem_cons_of_mem _ hs')

/-! ## §3  A side of the conversation is part of the conversation -/

lemma mem_sides_mem_mentions {c : Script} {s : List String} {x : String}
    (hs : s ∈ c.flatMap sides) (hx : x ∈ s) : x ∈ mentions c := by
  simp only [List.mem_flatMap] at hs
  obtain ⟨t, ht, hts⟩ := hs
  simp only [mentions, List.mem_flatMap]
  refine ⟨t, ht, ?_⟩
  simp only [sides, List.mem_cons, List.not_mem_nil, or_false] at hts
  rcases hts with rfl | rfl
  · exact List.mem_append_left _ hx
  · exact List.mem_append_right _ hx

lemma mem_mentions_mem_sides {c : Script} {x : String}
    (hx : x ∈ mentions c) : ∃ s ∈ c.flatMap sides, x ∈ s := by
  simp only [mentions, List.mem_flatMap] at hx
  obtain ⟨t, ht, hxt⟩ := hx
  rcases List.mem_append.1 hxt with hx' | hx'
  · exact ⟨t.answers, List.mem_flatMap.2 ⟨t, ht, by simp [sides]⟩, hx'⟩
  · exact ⟨t.subjects, List.mem_flatMap.2 ⟨t, ht, by simp [sides]⟩, hx'⟩

lemma sides_empty_of_mentions_empty {c : Script} (h : mentions c = [])
    (s : List String) (hs : s ∈ c.flatMap sides) : s = [] := by
  by_contra hne
  obtain ⟨x, hx⟩ := List.exists_mem_of_ne_nil s hne
  have hmem : x ∈ mentions c := mem_sides_mem_mentions hs hx
  rw [h] at hmem
  exact absurd hmem (by simp)

/-! ## §4  What the operation decided, and on what -/

/-- A binding is a binding the scan made. -/
lemma resolve_bound_scan {L : Licence} {c : Script} {x : String}
    (h : resolve L c = .bound x) :
    scan L (c.flatMap sides) = some (.bound x) := by
  unfold resolve at h
  rcases hsc : scan L (c.flatMap sides) with _ | o
  · rw [hsc] at h
    by_cases hm : mentions c = []
    · rw [if_pos hm] at h; exact absurd h (by simp)
    · rw [if_neg hm] at h; exact absurd h (by simp)
  · rw [hsc] at h
    simp only at h
    subst h
    rfl

/-- A refusal is either the scan's, or the scan's silence. -/
lemma resolve_refused_scan {L : Licence} {c : Script} {r : Reason}
    (h : resolve L c = .refused r) :
    scan L (c.flatMap sides) = some (.refused r) ∨
      scan L (c.flatMap sides) = none := by
  rcases hsc : scan L (c.flatMap sides) with _ | o
  · exact Or.inr rfl
  · left
    unfold resolve at h
    rw [hsc] at h
    simp only at h
    rw [h]

/-! ## §5  What the operation guarantees -/

/-- **The name it binds is licensed.**  Nothing is bound that leaves the
question unanswered. -/
theorem resolve_bound_licensed {L : Licence} {c : Script} {x : String}
    (h : resolve L c = .bound x) : L x = true := by
  obtain ⟨_, _, hx⟩ := scan_bound (resolve_bound_scan h)
  exact (mem_licensed.1 hx).2

/-- **The name it binds is one the conversation named.**  The antecedent comes
from the conversation, never from anywhere else. -/
theorem resolve_bound_mem {L : Licence} {c : Script} {x : String}
    (h : resolve L c = .bound x) : x ∈ mentions c := by
  obtain ⟨s, hs, hx⟩ := scan_bound (resolve_bound_scan h)
  exact mem_sides_mem_mentions hs (mem_licensed.1 hx).1

/-- **`.noAntecedent` is exactly the conversation that named nothing.**  The
refusal states a fact about the conversation rather than reporting a failed
search. -/
theorem resolve_noAntecedent_iff {L : Licence} {c : Script} :
    resolve L c = .refused .noAntecedent ↔ mentions c = [] := by
  constructor
  · intro h
    rcases resolve_refused_scan h with hsc | hsc
    · exact absurd hsc scan_not_noAntecedent
    · unfold resolve at h
      rw [hsc] at h
      by_cases hm : mentions c = []
      · exact hm
      · rw [if_neg hm] at h
        exact absurd h (by simp)
  · intro h
    have hsc : scan L (c.flatMap sides) = none :=
      scan_of_all_unlicensed fun s hs => by
        rw [sides_empty_of_mentions_empty h s hs]; rfl
    unfold resolve
    rw [hsc, if_pos h]

/-- **`.unlicensed` says every candidate was tried and none answered.** -/
theorem resolve_unlicensed_all_refused {L : Licence} {c : Script}
    (h : resolve L c = .refused .unlicensed) :
    ∀ x ∈ mentions c, L x = false := by
  rcases resolve_refused_scan h with hsc | hsc
  · exact absurd hsc scan_not_unlicensed
  · intro x hx
    obtain ⟨s, hs, hxs⟩ := mem_mentions_mem_sides hx
    have hempty : licensed L s = [] := scan_none hsc s hs
    by_contra hL
    have hmem : x ∈ licensed L s := mem_licensed.2 ⟨hxs, by simpa using hL⟩
    rw [hempty] at hmem
    exact absurd hmem (by simp)

/-- **`.ambiguous` says the side that decided held at least two licensed
candidates.**  This is the refusal the operation exists for: several equally
good referents, and the conversation does not say which is meant. -/
theorem resolve_ambiguous_two_licensed {L : Licence} {c : Script}
    (h : resolve L c = .refused .ambiguous) :
    ∃ s ∈ c.flatMap sides, 2 ≤ (licensed L s).length := by
  rcases resolve_refused_scan h with hsc | hsc
  · exact scan_ambiguous hsc
  · unfold resolve at h
    rw [hsc] at h
    by_cases hm : mentions c = []
    · rw [if_pos hm] at h; exact absurd h (by simp)
    · rw [if_neg hm] at h; exact absurd h (by simp)

/-- **A turn that names nothing usable cannot move a binding.**  Interposing a
newer turn whose every name fails the licence leaves the antecedent where it
was: the operation walks past it rather than being distracted by it. -/
theorem resolve_stable_under_unlicensed_turn {L : Licence} {c : Script}
    {t : Turn} {x : String}
    (hdead : ∀ y ∈ t.answers ++ t.subjects, L y = false)
    (h : resolve L c = .bound x) : resolve L (t :: c) = .bound x := by
  have hans : licensed L t.answers = [] := by
    rw [List.eq_nil_iff_forall_not_mem]
    intro y hy
    obtain ⟨hmem, hL⟩ := mem_licensed.1 hy
    have := hdead y (List.mem_append_left _ hmem)
    rw [this] at hL
    exact absurd hL (by simp)
  have hsub : licensed L t.subjects = [] := by
    rw [List.eq_nil_iff_forall_not_mem]
    intro y hy
    obtain ⟨hmem, hL⟩ := mem_licensed.1 hy
    have := hdead y (List.mem_append_right _ hmem)
    rw [this] at hL
    exact absurd hL (by simp)
  have h0 : decideSide L t.answers = none := by unfold decideSide; rw [hans]
  have h1 : decideSide L t.subjects = none := by unfold decideSide; rw [hsub]
  have hsc : scan L (c.flatMap sides) = some (.bound x) :=
    resolve_bound_scan h
  unfold resolve
  have hflat : (t :: c).flatMap sides = sides t ++ c.flatMap sides := by
    simp [List.flatMap_cons]
  rw [hflat]
  have hscan : scan L (sides t ++ c.flatMap sides)
      = scan L (c.flatMap sides) := by
    simp [sides, scan, h0, h1]
  rw [hscan, hsc]

/-! ## §6  The cheap rule, refuted -/

/-- The control the shipped operation is measured against: bind the pronoun to
the most recently mentioned name, with no licensing test. -/
def naive (c : Script) : Option String := (mentions c).head?

/-- **The most recent mention is not the antecedent.**

The conversation below is the shipped case: *describe carbon*, then *describe
water*, then a question only an element answers.  `naive` returns `water`,
which the licence refuses; the operation walks past it and binds `carbon`.  A
recency rule is therefore not merely less careful than this one — it returns a
different name, and the name it returns has no answer. -/
theorem most_recent_mention_is_not_the_antecedent :
    ∃ (L : Licence) (c : Script) (x y : String),
      resolve L c = .bound x ∧ naive c = some y ∧ y ≠ x ∧ L y = false := by
  refine ⟨fun s => s == "carbon",
          [⟨[], ["water"]⟩, ⟨[], ["carbon"]⟩], "carbon", "water",
          by decide, by decide, by decide, by decide⟩

/-- **A tie is refused rather than resolved.**  A turn whose answer side holds
two licensed names — the shipped case is fourteen — comes to `.ambiguous`, not
to either of them. -/
theorem tie_is_refused :
    resolve (fun _ => true) [⟨["atom", "bond"], []⟩]
      = .refused .ambiguous := by
  decide

/-- And the conversation that has said nothing refuses for the other reason. -/
theorem nothing_said_yet_is_no_antecedent (L : Licence) :
    resolve L [] = .refused .noAntecedent := by
  simp [resolve, scan, mentions]

end GLM.Conversation
