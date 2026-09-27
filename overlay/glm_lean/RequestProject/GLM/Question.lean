/-
# The question shape as an object: matching by shape, and what it refuses

`Recipe.lean` made a *domain* declarative: a description yields the carriers,
the reading, the audit and the query surface, and nothing about any particular
domain appears in the path that produces them.  What it did not make
declarative is the **way a question is asked**.  `derive <coordinate> of
<object>` is generic in the coordinate and in the object, but in the shipped
runtime it is still one hand-written phrase, and so is every other query kind:
a new domain arrives without its questions.

This file makes the *shape of a question* the object.  A `Spec` is a list of
`Piece`s — literal `Phrasing`s (a set of surface words that count as the same
thing here) and named `Slot`s (holes filled by the run of tokens between the
literals around them) — and `matchPieces` is the one matcher.  It knows
nothing about coordinates, measure words or tasks: it walks the tokens left to
right, fills each slot up to the earliest occurrence of the phrasing that
follows it, and returns `none` where the description does not decide.

What is proved here, and what is measured elsewhere
---------------------------------------------------
The Python side (`glm_universal.language`) measures the part that is a
measurement: that the described shapes and the hand-written parser make the
same query out of the same question, over a corpus generated from the
registers.  What is *not* a measurement is proved here:

* `matchPieces_rendered` — **the round trip.**  A question written from a
  shape and a filling matches back to exactly that filling.  This is what
  makes a shape a description of a language rather than a heuristic: writing
  and reading are inverse on the questions the shape can write.
* `matchPieces_required_nonempty` — **no silent empty slot.**  Whenever the
  matcher answers, every required slot of the shape came back with at least
  one token in it.  A question that would leave one empty is refused instead,
  which is the difference between a stated limit and a guess.
* `matchPieces_lit_none`, `matchPieces_no_separator` — **the two refusals**,
  stated as theorems: a question that does not open the shape is not matched,
  and neither is one whose separator is missing while a slot after it is
  required.
* `Phrasing.not_both_matchAt` — **openings decide the shape.**  If no
  alternative of one opening is a prefix of an alternative of another, no
  question can enter both shapes, so the order the shapes are tried in cannot
  change the answer.  That is what lets the descriptions be a *set* rather
  than a priority list.

* `runPre_of_skipped`, `runPre_refuses_undescribed` — **the preamble.**  What
  a question may carry before its opening is described too, as an ordered list
  of families that may be skipped.  Skipping one changes nothing about what is
  then matched; anything the preamble does not name still leaves the opening
  out of place, and the question is refused rather than read with the stray
  words inside a slot.  `skipMany_of_le` says the bound that keeps the
  repeatable skip structural does not decide anything: past the last match,
  more of it changes nothing.

`deriveShape` at the end instantiates all of it on the shipped `derive`
question — the five openings, the three separators, the optional domain tail —
and the examples beside it are the shipped behaviour, checked by computation:
`derive span_ratio of tea` fills the coordinate and the object and leaves the
domain empty, and `derive span_ratio` is refused.
-/
import Mathlib

namespace GLM.Question

/-! ## 1.  The pieces a shape is written in -/

/-- A token: one lower-case word of a question. -/
abbrev Token := String

/-- A set of surface words that count as the same thing here — the openings
`derive` / `derivation of` / `what derives`, or the separators `of` / `for` /
`on`.  Which forms belong to one set is a decision about English; that it is a
decision is why it is data here and not a rule. -/
structure Phrasing where
  /-- The alternative surface forms, each a list of tokens. -/
  alts : List (List Token)
  deriving Repr, DecidableEq

/-- A named hole in a shape.  An `optional` slot may be left out of a
question; a required one that comes out empty is a refusal. -/
structure Slot where
  /-- The slot's name, which is also the option it fills. -/
  name : String
  /-- Whether a question may leave this slot out. -/
  optional : Bool := false
  deriving Repr, DecidableEq

/-- A shape is a list of these. -/
inductive Piece
  | lit : Phrasing → Piece
  | hole : Slot → Piece
  deriving Repr, DecidableEq

/-- A described question: the query kind a match produces, and the shape. -/
structure Spec where
  /-- The query kind a match of this shape produces. -/
  kind : String
  /-- The shape: literal phrasings and named holes. -/
  shape : List Piece
  deriving Repr, DecidableEq

/-! ## 2.  Matching -/

/-- Match one alternative of `p` at the head of `ts`, and return what is left
after it.  The first alternative that fits wins, which is why the alternatives
are held longest-first. -/
def Phrasing.matchAt (p : Phrasing) (ts : List Token) : Option (List Token) :=
  match p.alts.find? (fun a => a.isPrefixOf ts) with
  | some a => some (ts.drop a.length)
  | none => none

/-- The alternative a shape is *written* with when a question is generated
from it: the first one. -/
def Phrasing.head (p : Phrasing) : List Token := p.alts.headD []

/-- Find the earliest occurrence of `p` in `ts`: the tokens before it, and the
tokens after it.  This is what fills a slot — everything up to the next
literal, and no scoring anywhere. -/
def Phrasing.fill (p : Phrasing) : List Token → Option (List Token × List Token)
  | [] =>
    match p.matchAt [] with
    | some after => some ([], after)
    | none => none
  | t :: rest =>
    match p.matchAt (t :: rest) with
    | some after => some ([], after)
    | none => (p.fill rest).map (fun r => (t :: r.1, r.2))

/-- Whether every slot from here on may be left out.  A separator that is
absent is only forgivable when nothing required follows it. -/
def optionalTail : List Piece → Bool
  | [] => true
  | Piece.lit _ :: rest => optionalTail rest
  | Piece.hole s :: rest => s.optional && optionalTail rest

/-- The slots of a tail, all left empty. -/
def emptyFills : List Piece → List (String × List Token)
  | [] => []
  | Piece.lit _ :: rest => emptyFills rest
  | Piece.hole s :: rest => (s.name, []) :: emptyFills rest

/-- **The matcher.**  One function, no domain knowledge, five rules:

* a literal must match where it stands;
* a slot followed by a literal takes the tokens up to the literal's earliest
  occurrence, and the walk resumes after it;
* a slot at the end takes what is left;
* if the literal after a slot is absent and every slot from there on is
  optional, the slot takes what is left and those slots stay empty —
  otherwise the question is refused;
* a required slot that comes out empty is a refusal.

Two adjacent holes are refused outright: no word separates them, so any split
would be a guess. -/
def matchPieces : List Piece → List Token → Option (List (String × List Token))
  | [], _ => some []
  | Piece.lit p :: rest, ts =>
    match p.matchAt ts with
    | some after => matchPieces rest after
    | none => none
  | Piece.hole s :: [], ts =>
    if ts.isEmpty && !s.optional then none else some [(s.name, ts)]
  | Piece.hole _ :: Piece.hole _ :: _, _ => none
  | Piece.hole s :: Piece.lit p :: rest, ts =>
    match p.fill ts with
    | some (before, after) =>
      if before.isEmpty && !s.optional then none
      else (matchPieces rest after).map (fun out => (s.name, before) :: out)
    | none =>
      if ts.isEmpty && !s.optional then none
      else if optionalTail rest then some ((s.name, ts) :: emptyFills rest)
      else none

/-- A whole description, matched. -/
def Spec.run (sp : Spec) (ts : List Token) : Option (List (String × List Token)) :=
  matchPieces sp.shape ts

/-! ## 3.  Writing a question, and reading it back -/

/-- Write a question of this shape: each literal in its first form, each slot
filled by `f`.  This is the inverse of matching, and the round trip between
them is `matchPieces_rendered`. -/
def rendered : List Piece → (String → List Token) → List Token
  | [], _ => []
  | Piece.lit p :: rest, f => p.head ++ rendered rest f
  | Piece.hole s :: rest, f => f s.name ++ rendered rest f

/-- The filling a written question should read back to. -/
def written : List Piece → (String → List Token) → List (String × List Token)
  | [], _ => []
  | Piece.lit _ :: rest, f => written rest f
  | Piece.hole s :: rest, f => (s.name, f s.name) :: written rest f

/-- `p` does not occur inside `before` when `before` is followed by `rest`.
Stated over the concatenation because an occurrence may straddle the join. -/
def Avoids (p : Phrasing) (before rest : List Token) : Prop :=
  ∀ i, i < before.length → p.matchAt (before.drop i ++ rest) = none

/-- `p`, written in its first form, reads back as itself: what follows the
written form is exactly `rest`.  This can fail for a phrasing one of whose
alternatives extends another *into the text that follows* — `measure` written
before the subject `word` — and where it fails the shipped parser reads the
longer form too, so it is a hypothesis and not an oversight. -/
def Reads (p : Phrasing) (rest : List Token) : Prop :=
  p.matchAt (p.head ++ rest) = some rest

/-- A written question is **clean** when every slot is written with something,
no separator occurs inside a slot's filling, and every literal reads back as
itself.  These are exactly the conditions under which writing and matching are
inverse; `Clean` states them once, by recursion on the shape. -/
def Clean : List Piece → (String → List Token) → Prop
  | [], _ => True
  | Piece.lit p :: rest, f => Reads p (rendered rest f) ∧ Clean rest f
  | Piece.hole s :: [], f => f s.name ≠ []
  | Piece.hole _ :: Piece.hole _ :: _, _ => False
  | Piece.hole s :: Piece.lit p :: rest, f =>
      f s.name ≠ [] ∧ Avoids p (f s.name) (p.head ++ rendered rest f)
        ∧ Reads p (rendered rest f) ∧ Clean rest f

/-! ## 4.  The lemmas the round trip rests on -/

theorem Phrasing.fill_append (p : Phrasing) :
    ∀ (before rest after : List Token), Avoids p before rest →
      p.matchAt rest = some after → p.fill (before ++ rest) = some (before, after) := by
  intro before
  induction before with
  | nil =>
    intro rest after _ hread
    cases rest with
    | nil => simp [Phrasing.fill, hread]
    | cons t rest' => simp [Phrasing.fill, hread]
  | cons t before' ih =>
    intro rest after havoid hread
    have h0 : p.matchAt (t :: (before' ++ rest)) = none := havoid 0 (by simp)
    have hrec : p.fill (before' ++ rest) = some (before', after) := by
      refine ih rest after ?_ hread
      intro i hi
      have := havoid (i + 1) (by simpa using hi)
      simpa using this
    show p.fill (t :: (before' ++ rest)) = _
    simp only [Phrasing.fill, h0, hrec, Option.map_some]

/-- **The round trip.**  A question written from a shape matches back to
exactly the filling it was written from. -/
theorem matchPieces_rendered :
    ∀ (shape : List Piece) (f : String → List Token), Clean shape f →
      matchPieces shape (rendered shape f) = some (written shape f) := by
  intro shape
  induction shape with
  | nil => intro f _; rfl
  | cons piece rest ih =>
    cases piece with
    | lit p =>
      intro f h
      obtain ⟨hread, hclean⟩ := h
      have hr : p.matchAt (p.head ++ rendered rest f) = some (rendered rest f) := hread
      show matchPieces (Piece.lit p :: rest) (p.head ++ rendered rest f) = _
      simp only [matchPieces, written, hr]
      exact ih f hclean
    | hole s =>
      cases rest with
      | nil =>
        intro f h
        have hne : f s.name ≠ [] := h
        simp [matchPieces, rendered, written, List.isEmpty_iff, hne]
      | cons piece2 rest2 =>
        cases piece2 with
        | hole t => intro f h; exact absurd h (by simp [Clean])
        | lit p =>
          intro f h
          obtain ⟨hne, havoid, hread, hclean⟩ := h
          have hfill : p.fill (f s.name ++ (p.head ++ rendered rest2 f))
              = some (f s.name, rendered rest2 f) :=
            Phrasing.fill_append p _ _ _ havoid hread
          have hr : p.matchAt (p.head ++ rendered rest2 f) = some (rendered rest2 f) :=
            hread
          have htail : matchPieces rest2 (rendered rest2 f) = some (written rest2 f) := by
            have hstep := ih f ⟨hread, hclean⟩
            rw [show rendered (Piece.lit p :: rest2) f = p.head ++ rendered rest2 f from rfl]
              at hstep
            simpa only [matchPieces, written, hr] using hstep
          have hemp : (f s.name).isEmpty = false := by
            simpa [List.isEmpty_iff] using hne
          show matchPieces (Piece.hole s :: Piece.lit p :: rest2)
              (f s.name ++ (p.head ++ rendered rest2 f)) = _
          simp only [matchPieces, written, hfill, hemp, Bool.false_and,
            htail, Option.map_some]
          simp

/-! ## 5.  The two refusals, as theorems -/

/-- **A question that does not open the shape is not matched.**  There is no
fall-back and no nearest guess: the opening is where a shape is entered. -/
theorem matchPieces_lit_none (p : Phrasing) (rest : List Piece) (ts : List Token)
    (h : p.matchAt ts = none) : matchPieces (Piece.lit p :: rest) ts = none := by
  simp [matchPieces, h]

/-- **A missing separator is a refusal when something after it is required.**
Where everything after it is optional the slot simply takes the rest, which is
why the hypothesis is on `optionalTail` and not on the separator. -/
theorem matchPieces_no_separator (s : Slot) (p : Phrasing) (rest : List Piece)
    (ts : List Token) (hfill : p.fill ts = none) (hopt : optionalTail rest = false) :
    matchPieces (Piece.hole s :: Piece.lit p :: rest) ts = none := by
  simp [matchPieces, hfill, hopt]

/-- Two adjacent holes are refused: no word separates them, so any split
between them would be a guess rather than a reading. -/
theorem matchPieces_adjacent_holes (s t : Slot) (rest : List Piece)
    (ts : List Token) : matchPieces (Piece.hole s :: Piece.hole t :: rest) ts = none :=
  rfl

/-- A tail all of whose slots may be left out has no required slot in it. -/
theorem optional_of_optionalTail :
    ∀ (shape : List Piece), optionalTail shape = true →
      ∀ s : Slot, Piece.hole s ∈ shape → s.optional = true := by
  intro shape
  induction shape with
  | nil => intro _ s hs; cases hs
  | cons piece rest ih =>
    cases piece with
    | lit q =>
      intro h s hs
      rcases List.mem_cons.1 hs with h' | h'
      · exact absurd h' (by simp)
      · exact ih (by simpa [optionalTail] using h) s h'
    | hole t =>
      intro h s hs
      have hboth : t.optional = true ∧ optionalTail rest = true := by
        simpa [optionalTail, Bool.and_eq_true] using h
      rcases List.mem_cons.1 hs with h' | h'
      · have hst : s = t := by injection h'
        subst hst; exact hboth.1
      · exact ih hboth.2 s h'

/-- **No silent empty slot.**  Whenever the matcher answers, every required
slot of the shape came back with at least one token in it.  This is the
property that makes a refusal informative: the matcher never fills a required
slot with nothing and carries on. -/
theorem matchPieces_required_nonempty :
    ∀ (shape : List Piece) (ts : List Token) (out : List (String × List Token)),
      matchPieces shape ts = some out →
      ∀ s : Slot, Piece.hole s ∈ shape → s.optional = false →
        ∃ v, (s.name, v) ∈ out ∧ v ≠ [] := by
  intro shape ts
  induction shape, ts using matchPieces.induct with
  | case1 ts => intro out _ s hs _; cases hs
  | case2 p rest ts a hat ih =>
    intro out hmatch s hs hreq
    rw [matchPieces, hat] at hmatch
    rcases List.mem_cons.1 hs with h' | h'
    · exact absurd h' (by simp)
    · exact ih out hmatch s h' hreq
  | case3 p rest ts hat =>
    intro out hmatch s hs hreq
    rw [matchPieces, hat] at hmatch
    exact absurd hmatch (by simp)
  | case4 t ts hcond =>
    intro out hmatch s hs hreq
    rw [matchPieces, if_pos hcond] at hmatch
    exact absurd hmatch (by simp)
  | case5 t ts hcond =>
    intro out hmatch s hs hreq
    rw [matchPieces, if_neg hcond] at hmatch
    have hout : out = [(t.name, ts)] := by
      simpa using hmatch.symm
    rcases List.mem_cons.1 hs with h' | h'
    · have hst : s = t := by injection h'
      subst hst
      refine ⟨ts, by simp [hout], ?_⟩
      intro hts
      exact hcond (by simp [hts, hreq])
    · cases h'
  | case6 s1 s2 tail ts =>
    intro out hmatch s _ _
    rw [matchPieces] at hmatch
    exact absurd hmatch (by simp)
  | case7 t p rest ts before after hfill hcond =>
    intro out hmatch s hs hreq
    rw [matchPieces, hfill] at hmatch
    dsimp only at hmatch
    rw [if_pos hcond] at hmatch
    exact absurd hmatch (by simp)
  | case8 t p rest ts before after hfill hcond ih =>
    intro out hmatch s hs hreq
    rw [matchPieces, hfill] at hmatch
    dsimp only at hmatch
    rw [if_neg hcond] at hmatch
    obtain ⟨out', hout', heq⟩ := Option.map_eq_some_iff.1 hmatch
    rcases List.mem_cons.1 hs with h' | h'
    · have hst : s = t := by injection h'
      subst hst
      refine ⟨before, by rw [← heq]; simp, ?_⟩
      intro hb
      exact hcond (by simp [hb, hreq])
    · rcases List.mem_cons.1 h' with h'' | h''
      · exact absurd h'' (by simp)
      · obtain ⟨v, hv, hvne⟩ := ih out' hout' s h'' hreq
        exact ⟨v, by rw [← heq]; exact List.mem_cons_of_mem _ hv, hvne⟩
  | case9 t p rest ts hfill hcond =>
    intro out hmatch s hs hreq
    rw [matchPieces, hfill] at hmatch
    dsimp only at hmatch
    rw [if_pos hcond] at hmatch
    exact absurd hmatch (by simp)
  | case10 t p rest ts hfill hcond hopt =>
    intro out hmatch s hs hreq
    rw [matchPieces, hfill] at hmatch
    dsimp only at hmatch
    rw [if_neg hcond, if_pos hopt] at hmatch
    have hout : out = (t.name, ts) :: emptyFills rest := by
      simpa using hmatch.symm
    rcases List.mem_cons.1 hs with h' | h'
    · have hst : s = t := by injection h'
      subst hst
      refine ⟨ts, by simp [hout], ?_⟩
      intro hts
      exact hcond (by simp [hts, hreq])
    · rcases List.mem_cons.1 h' with h'' | h''
      · exact absurd h'' (by simp)
      · have hopts := optional_of_optionalTail rest hopt s h''
        rw [hopts] at hreq
        exact absurd hreq (by simp)
  | case11 t p rest ts hfill hcond hopt =>
    intro out hmatch s hs hreq
    rw [matchPieces, hfill] at hmatch
    dsimp only at hmatch
    rw [if_neg hcond, if_neg hopt] at hmatch
    exact absurd hmatch (by simp)

/-! ## 6.  Openings decide the shape -/

theorem Phrasing.matchAt_ne_none_iff (p : Phrasing) (ts : List Token) :
    p.matchAt ts ≠ none ↔ ∃ a ∈ p.alts, a <+: ts := by
  unfold Phrasing.matchAt
  cases hf : p.alts.find? (fun a => a.isPrefixOf ts) with
  | some a =>
    constructor
    · intro _
      exact ⟨a, List.mem_of_find?_eq_some hf,
        List.isPrefixOf_iff_prefix.1 (by simpa using List.find?_some hf)⟩
    · intro _
      simp
  | none =>
    constructor
    · intro h
      exact absurd rfl h
    · rintro ⟨a, ha, hpre⟩
      exact absurd ((List.find?_eq_none.1 hf) a ha)
        (by simpa using List.isPrefixOf_iff_prefix.2 hpre)

/-- **Openings decide the shape.**  If no alternative of one opening is a
prefix of an alternative of another, no question can enter both shapes -- so
the described shapes are a *set*, and the order they are tried in cannot
change the answer. -/
theorem Phrasing.not_both_matchAt {p q : Phrasing} (ts : List Token)
    (hdisj : ∀ a ∈ p.alts, ∀ b ∈ q.alts, ¬ a <+: b ∧ ¬ b <+: a) :
    p.matchAt ts = none ∨ q.matchAt ts = none := by
  by_contra h
  push_neg at h
  obtain ⟨a, ha, hap⟩ := (Phrasing.matchAt_ne_none_iff p ts).1 h.1
  obtain ⟨b, hb, hbp⟩ := (Phrasing.matchAt_ne_none_iff q ts).1 h.2
  rcases List.prefix_or_prefix_of_prefix hap hbp with h1 | h1
  · exact (hdisj a ha b hb).1 h1
  · exact (hdisj a ha b hb).2 h1

/-- The same statement where it is used: two shapes with disjoint openings
never both match. -/
theorem matchPieces_not_both {p q : Phrasing} (rest rest' : List Piece)
    (ts : List Token)
    (hdisj : ∀ a ∈ p.alts, ∀ b ∈ q.alts, ¬ a <+: b ∧ ¬ b <+: a) :
    matchPieces (Piece.lit p :: rest) ts = none ∨
      matchPieces (Piece.lit q :: rest') ts = none := by
  rcases Phrasing.not_both_matchAt (p := p) (q := q) ts hdisj with h | h
  · exact Or.inl (matchPieces_lit_none p rest ts h)
  · exact Or.inr (matchPieces_lit_none q rest' ts h)

/-! ## 7.  The shipped `derive` question -/

/-- The five openings the runtime maps to `derive`, longest first. -/
def deriveOpening : Phrasing :=
  ⟨[["derivation", "of"], ["which", "coordinate"], ["what", "derives"],
    ["coordinate"], ["derive"]]⟩

/-- The three prepositions that attach a coordinate to its object. -/
def deriveSeparator : Phrasing := ⟨[["of"], ["for"], ["on"]]⟩

/-- The one word that names the domain. -/
def deriveDomainWord : Phrasing := ⟨[["in"]]⟩

/-- `derive <coordinate> (of|for|on) <object> [in <domain>]` -- the shipped
question, written down. -/
def deriveShape : Spec :=
  { kind := "derive"
    shape :=
      [Piece.lit deriveOpening,
       Piece.hole ⟨"coordinate", false⟩,
       Piece.lit deriveSeparator,
       Piece.hole ⟨"object", false⟩,
       Piece.lit deriveDomainWord,
       Piece.hole ⟨"domain", true⟩] }

/-- The shipped question, read by the description: the coordinate and the
object are filled and the optional domain is left empty. -/
theorem deriveShape_span_ratio_of_tea :
    deriveShape.run ["derive", "span_ratio", "of", "tea"] =
      some [("coordinate", ["span_ratio"]), ("object", ["tea"]), ("domain", [])] := by
  decide

/-- Another opening, another separator, and the domain tail written out. -/
theorem deriveShape_what_derives_in_harmonics :
    deriveShape.run
        ["what", "derives", "numerator", "for", "perfect_fifth", "in", "harmonics"] =
      some [("coordinate", ["numerator"]), ("object", ["perfect_fifth"]),
            ("domain", ["harmonics"])] := by
  decide

/-- A derivation that names no object is refused, not guessed at. -/
theorem deriveShape_refuses_missing_object :
    deriveShape.run ["derive", "span_ratio"] = none := by decide

/-- A question that does not open the shape is refused. -/
theorem deriveShape_refuses_other_opening :
    deriveShape.run ["report", "language"] = none := by decide

/-! ## 8.  The preamble: what a question may carry before its opening -/

/-- One family of words a question may carry *before* the opening that decides
its shape.  `repeatable` says whether the family may be skipped more than once
in a row: the shipped parser strips its courtesies in a loop and its
interrogative opener once, so a description that reproduces the shipped
surface has to say which is which. -/
structure PreamblePiece where
  /-- The words this piece admits. -/
  phrasing : Phrasing
  /-- Whether the piece may be skipped more than once in a row. -/
  repeatable : Bool := false
  deriving Repr, DecidableEq

/-- A described *leading remainder*: an ordered list of pieces, each of which
may be skipped before the opening.  Everything a preamble does not name is
still refused, which is the whole point of describing it rather than letting
the opening float free. -/
abbrev Preamble := List PreamblePiece

/-- Skip `p` as often as it matches, with the token list as fuel.  The fuel is
not a heuristic: every alternative that matches and is non-empty shortens the
list, so `ts.length` steps are more than the description can ever take, and
counting them keeps the definition structural and so decidable. -/
def skipMany (p : Phrasing) : Nat → List Token → List Token
  | 0, ts => ts
  | n + 1, ts =>
    match p.matchAt ts with
    | some after => skipMany p n after
    | none => ts

/-- Skip one piece at the head: a repeatable piece as often as it matches, a
non-repeatable one at most once. -/
def skipPiece (pc : PreamblePiece) (ts : List Token) : List Token :=
  if pc.repeatable then skipMany pc.phrasing ts.length ts
  else
    match pc.phrasing.matchAt ts with
    | some after => after
    | none => ts

/-- Skip the whole preamble, each piece in the order the description gives.
Nothing back-tracks, so where the preamble ends is a function of the tokens. -/
def skipPreamble : Preamble → List Token → List Token
  | [], ts => ts
  | pc :: rest, ts => skipPreamble rest (skipPiece pc ts)

/-- A description matched behind its preamble. -/
def Spec.runPre (sp : Spec) (pre : Preamble) (ts : List Token) :
    Option (List (String × List Token)) :=
  matchPieces sp.shape (skipPreamble pre ts)

/-- No fuel, no skipping. -/
@[simp] theorem skipMany_zero (p : Phrasing) (ts : List Token) :
    skipMany p 0 ts = ts := rfl

/-- Where the piece does not match, skipping stops however much fuel is
left -- so the end position does not depend on the amount of fuel. -/
theorem skipMany_none (p : Phrasing) (n : Nat) (ts : List Token)
    (h : p.matchAt ts = none) : skipMany p n ts = ts := by
  cases n with
  | zero => rfl
  | succ n => simp [skipMany, h]

/-- One step of skipping. -/
theorem skipMany_step (p : Phrasing) (n : Nat) (ts after : List Token)
    (h : p.matchAt ts = some after) :
    skipMany p (n + 1) ts = skipMany p n after := by
  simp [skipMany, h]

/-- **Fuel does not decide anything.**  Once the piece no longer matches, more
fuel changes nothing, so `skipPiece` would give the same answer for any bound
at least as large as the number of steps actually taken. -/
theorem skipMany_of_le (p : Phrasing) :
    ∀ (k : Nat) (ts r : List Token), skipMany p k ts = r →
      p.matchAt r = none → ∀ n, k ≤ n → skipMany p n ts = r := by
  intro k
  induction k with
  | zero =>
    intro ts r hk hr n _
    simp only [skipMany_zero] at hk
    subst hk
    exact skipMany_none p n ts hr
  | succ k ih =>
    intro ts r hk hr n hn
    cases hm : p.matchAt ts with
    | none =>
      rw [skipMany_none p (k + 1) ts hm] at hk
      subst hk
      exact skipMany_none p n ts hm
    | some after =>
      rw [skipMany_step p k ts after hm] at hk
      cases n with
      | zero => omega
      | succ n =>
        rw [skipMany_step p n ts after hm]
        exact ih after r hk hr n (by omega)

/-- **Skipping a described preamble changes nothing about what is matched.**
Where the preamble consumes exactly the leading remainder, the shape sees the
bare question and answers it exactly as if the remainder had never been
written.  This is what makes the courtesies a *description* and not a second
parser: they are skipped, and matching resumes unchanged. -/
theorem runPre_of_skipped (sp : Spec) (pre : Preamble) (lead ts : List Token)
    (h : skipPreamble pre (lead ++ ts) = ts) :
    sp.runPre pre (lead ++ ts) = sp.run ts := by
  simp [Spec.runPre, Spec.run, h]

/-- A non-repeatable piece consumes the form it reads, and no more. -/
theorem skipPiece_once (p : Phrasing) (a ts : List Token)
    (h : p.matchAt (a ++ ts) = some ts) :
    skipPiece ⟨p, false⟩ (a ++ ts) = ts := by
  simp [skipPiece, h]

/-- A repeatable piece consumes as many copies as are written.  Two are stated
because two is where a loop differs from a single skip; the fuel is enough
because each copy is at least one token long. -/
theorem skipPiece_twice (p : Phrasing) (a b ts : List Token)
    (ha : a ≠ []) (hb : b ≠ [])
    (h1 : p.matchAt (a ++ (b ++ ts)) = some (b ++ ts))
    (h2 : p.matchAt (b ++ ts) = some ts)
    (h3 : p.matchAt ts = none) :
    skipPiece ⟨p, true⟩ (a ++ (b ++ ts)) = ts := by
  have htwo : skipMany p 2 (a ++ (b ++ ts)) = ts := by
    rw [skipMany_step p 1 _ _ h1, skipMany_step p 0 _ _ h2, skipMany_zero]
  have hlen : 2 ≤ (a ++ (b ++ ts)).length := by
    have ha' : 1 ≤ a.length := List.length_pos_iff.2 ha
    have hb' : 1 ≤ b.length := List.length_pos_iff.2 hb
    simp only [List.length_append]
    omega
  simpa [skipPiece] using
    skipMany_of_le p 2 (a ++ (b ++ ts)) ts htwo h3 _ hlen

/-- **An undescribed leading remainder is still refused.**  Describing the
preamble is a narrowing, not a licence: where the preamble consumes nothing,
the opening has to stand at the head, and a question that puts anything else
there is declined rather than read with the stray words inside a slot. -/
theorem runPre_refuses_undescribed (sp : Spec) (pre : Preamble) (p : Phrasing)
    (rest : List Piece) (ts : List Token) (hshape : sp.shape = Piece.lit p :: rest)
    (hpre : skipPreamble pre ts = ts) (hop : p.matchAt ts = none) :
    sp.runPre pre ts = none := by
  rw [Spec.runPre, hshape, hpre]
  exact matchPieces_lit_none p rest ts hop

/-! ### The shipped preamble, on the shipped `derive` question -/

/-- The courtesies the shipped parser strips, in a loop. -/
def courtesyWords : Phrasing :=
  ⟨[["i", "would", "like", "to", "know"], ["i", "want", "to", "know"],
    ["can", "you"], ["could", "you"], ["would", "you"], ["kindly"],
    ["please"]]⟩

/-- The interrogative openers it strips once. -/
def interrogativeWords : Phrasing :=
  ⟨[["tell", "me", "about"], ["what", "is"], ["address"], ["explain"],
    ["profile"]]⟩

/-- Courtesies, then at most one interrogative: the shipped leading
remainder, written down. -/
def standardPreamble : Preamble :=
  [⟨courtesyWords, true⟩, ⟨interrogativeWords, false⟩]

/-- One courtesy, skipped, and the question answered as if it were bare. -/
theorem deriveShape_please :
    deriveShape.runPre standardPreamble
        ["please", "derive", "span_ratio", "of", "tea"] =
      deriveShape.run ["derive", "span_ratio", "of", "tea"] := by
  decide

/-- Two courtesies and an interrogative, in the order the description gives. -/
theorem deriveShape_please_kindly_what_is :
    deriveShape.runPre standardPreamble
        ["please", "kindly", "what", "is", "derive", "span_ratio", "of", "tea"] =
      deriveShape.run ["derive", "span_ratio", "of", "tea"] := by
  decide

/-- The order is part of the description: an interrogative before a courtesy
stops the skipping, and the question is refused rather than re-ordered. -/
theorem deriveShape_refuses_interrogative_before_courtesy :
    deriveShape.runPre standardPreamble
        ["what", "is", "please", "derive", "span_ratio", "of", "tea"] = none := by
  decide

/-- A bare noun phrase is not a courtesy, so it is refused -- where the
hand-written parser answered, with `the tea` left inside the coordinate. -/
theorem deriveShape_refuses_stray_opening :
    deriveShape.runPre standardPreamble
        ["the", "tea", "derive", "span_ratio", "of", "tea"] = none := by
  decide

/-- A question with no preamble at all is unaffected by having one described. -/
theorem deriveShape_no_preamble :
    deriveShape.runPre standardPreamble ["derive", "span_ratio", "of", "tea"] =
      deriveShape.run ["derive", "span_ratio", "of", "tea"] := by
  decide

end GLM.Question
