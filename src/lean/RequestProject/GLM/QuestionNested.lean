/-
# Three more pieces of description language: a list, a modifier, a nested side

`Question.lean` made the *shape of a question* an object: a list of literal
`Phrasing`s and named `Slot`s, one matcher, and the round trip between writing
a question and reading it back.  The round that followed it took four parts of
the shipped parser that no shape could yet say, described them, and deleted
the hand-written branches.  Three of those parts are not slots at all, and
this file is what they are:

* **a list** — `compare sqrt(2) and 1.5` puts *two* values in one hole, and
  which words separate them (`and`, `versus`, a comma, `with`) is a decision
  about English exactly as a shape's separators are.  A `ListCut` carries the
  separator forms and the one admitted mark, and `ListCut.cut` cuts a run of
  tokens at the earliest of them.
* **a modifier** — `check tensor force = ...` asks the same question of the
  same equation under a stricter reading.  The word directs the reading rather
  than naming an operand, so it is removed from the operands *only* where it
  is unambiguously a directive: at the head, and in the trailing frame
  (`... under tensor semantics`).  A `tensor` in the middle of an equation is
  left exactly where it stands, because deleting it there would change the
  equation being audited.
* **a nested side** — `cold in stellar_surface hotter than hot in tea` is an
  operator between two *readings*: each side must itself match a described
  shape, and a side that does not is not an operand at all.  The operator is
  not a listed set of forms either; it is *formed* from a degree word, either
  `<word>er than` or the frame `as <word> as`.

What is proved here, and what is measured elsewhere
---------------------------------------------------
As in `Question.lean`, the Python side measures the agreement between the
descriptions and the shipped parser over a generated corpus.  What is not a
measurement is proved here:

* `ListCut.cut_two` — **the round trip for a list.**  A list written as
  `left <separator> right`, where neither item holds a separator, cuts back to
  exactly those two items.  `ListCut.cut_ne_nil` and `ListCut.cut_append` are
  the two facts it rests on, and `ListCut.sepAt_shorter` is why the cut
  terminates: every cut consumes at least one token, because an empty
  separator form is not admitted.
* `ModifierFrame.strip_head`, `ModifierFrame.strip_frame`,
  `ModifierFrame.strip_middle` — **the modifier is removed exactly twice.**
  At the head and in the trailing frame the word comes out and the operands
  are what is left; anywhere else the tokens are returned unchanged, which is
  the difference between a directive and a deletion.
* `NestedSpec.run_rendered` — **the round trip for a nested shape.**  A
  question written from two fillings of the side shape, with an operator
  between them, reads back as exactly those two fillings and the degree word
  it was written with.
* `NestedSpec.run_no_operator`, `NestedSpec.run_side_refused` — **the two
  refusals of the nested family**, stated as theorems: a question that forms
  no operator is not a comparative, and neither is one whose side is not a
  use of the nested shape.  `is sqrt(2) greater than 7/5` forms the operator
  and is still refused, because `sqrt(2)` is not a measured use — that is the
  boundary between this shape and the exact-real comparison, and it is a
  theorem rather than a regular expression.

The last section instantiates all of it on the shipped surfaces: the `compare`
list, the `tensor` modifier of the audit question, and the comparative shape,
with the shipped behaviour checked by computation.
-/
import Mathlib
import RequestProject.GLM.Question

namespace GLM.QuestionNested

open GLM.Question

/-! ## 1.  A hole that holds a list -/

/-- A described list: the separator phrasings, in rank order, and the one
piece of punctuation admitted beside them.  The mark is declared rather than
assumed, because admitting it means tokenising the question differently, and a
shape with no list in it is still read exactly as it was. -/
structure ListCut where
  /-- The separator phrasings, in the order the description ranks them. -/
  seps : List Phrasing
  /-- The one admitted mark, a comma in every shipped list. -/
  mark : Token
  deriving Repr, DecidableEq

/-- Every surface that separates two items, all ranks together. -/
def ListCut.forms (c : ListCut) : List (List Token) :=
  c.seps.flatMap (fun p => p.alts)

/-- Whether a cut is made at the head of `ts`, and what follows it.  The mark
is looked for first, then the separator forms in rank order.  An *empty* form
is not admitted: a separator that consumes nothing would cut for ever, and
refusing it here is what keeps the cut a function of the tokens. -/
def ListCut.sepAt (c : ListCut) : List Token → Option (List Token)
  | [] => none
  | t :: rest =>
    if t = c.mark then some rest
    else
      match c.forms.find? (fun a => !a.isEmpty && a.isPrefixOf (t :: rest)) with
      | some a => some ((t :: rest).drop a.length)
      | none => none

/-- **A cut consumes something.**  This is why `ListCut.cut` is a total
function and not a loop with a bound on it. -/
theorem ListCut.sepAt_shorter (c : ListCut) :
    ∀ (ts after : List Token), c.sepAt ts = some after → after.length < ts.length := by
  intro ts after h
  cases ts with
  | nil => simp [ListCut.sepAt] at h
  | cons t rest =>
    by_cases hm : t = c.mark
    · simp only [ListCut.sepAt, if_pos hm, Option.some.injEq] at h
      subst h; simp
    · rw [ListCut.sepAt, if_neg hm] at h
      cases hf : c.forms.find? (fun a => !a.isEmpty && a.isPrefixOf (t :: rest)) with
      | none => rw [hf] at h; simp at h
      | some a =>
        rw [hf] at h
        have hp := List.find?_some hf
        simp only [Bool.and_eq_true, Bool.not_eq_true'] at hp
        have hane : a ≠ [] := by
          intro hh; simp [hh] at hp
        have hlen : 1 ≤ a.length := List.length_pos_iff.2 hane
        simp only [Option.some.injEq] at h
        subst h
        simp only [List.length_drop, List.length_cons]
        omega

/-- **The cut.**  Walk the tokens left to right; where a separator stands,
close the current item and open the next; otherwise the token joins the item
being built.  No scoring, no back-tracking, and the items come out in the
order they were written. -/
def ListCut.cut (c : ListCut) : List Token → List (List Token)
  | [] => [[]]
  | t :: rest =>
    match _h : c.sepAt (t :: rest) with
    | some after => [] :: c.cut after
    | none =>
      match c.cut rest with
      | item :: items => (t :: item) :: items
      | [] => [[t]]
  termination_by ts => ts.length
  decreasing_by
    · exact c.sepAt_shorter _ _ _h
    · simp

@[simp] theorem ListCut.cut_nil (c : ListCut) : c.cut [] = [[]] := by
  rw [ListCut.cut]

/-- Where a separator stands, the item before it is closed. -/
theorem ListCut.cut_sep (c : ListCut) (t : Token) (rest after : List Token)
    (h : c.sepAt (t :: rest) = some after) : c.cut (t :: rest) = [] :: c.cut after := by
  rw [ListCut.cut]
  split
  · next after' heq => rw [h] at heq; injection heq with heq; subst heq; rfl
  · next heq => rw [h] at heq; exact absurd heq (by simp)

/-- Where none stands, the token joins the item being built. -/
theorem ListCut.cut_word (c : ListCut) (t : Token) (rest : List Token)
    (h : c.sepAt (t :: rest) = none) :
    c.cut (t :: rest) = (t :: (c.cut rest).headD []) :: (c.cut rest).tail := by
  rw [ListCut.cut]
  split
  · next after' heq => rw [h] at heq; exact absurd heq (by simp)
  · next heq =>
    cases hc : c.cut rest with
    | nil => simp
    | cons a as => simp

/-- A cut always yields at least one item, even of nothing. -/
theorem ListCut.cut_ne_nil (c : ListCut) : ∀ ts : List Token, c.cut ts ≠ [] := by
  intro ts
  cases ts with
  | nil => simp
  | cons t rest =>
    cases h : c.sepAt (t :: rest) with
    | some after => rw [c.cut_sep t rest after h]; simp
    | none => rw [c.cut_word t rest h]; simp

/-- No separator occurs inside `before` when `rest` follows it.  Stated over
the concatenation because a separator may straddle the join, exactly as
`GLM.Question.Avoids` is. -/
def CutAvoids (c : ListCut) (before rest : List Token) : Prop :=
  ∀ i, i < before.length → c.sepAt (before.drop i ++ rest) = none

/-- A run of tokens holding no separator is carried whole into the first item
of whatever follows it. -/
theorem ListCut.cut_append (c : ListCut) :
    ∀ (before rest : List Token), CutAvoids c before rest →
      c.cut (before ++ rest) = (before ++ (c.cut rest).headD []) :: (c.cut rest).tail := by
  intro before
  induction before with
  | nil =>
    intro rest _
    cases h : c.cut rest with
    | nil => exact absurd h (c.cut_ne_nil rest)
    | cons a as => simp [h]
  | cons t before' ih =>
    intro rest havoid
    have h0 : c.sepAt (t :: (before' ++ rest)) = none := havoid 0 (by simp)
    have hrec : c.cut (before' ++ rest)
        = (before' ++ (c.cut rest).headD []) :: (c.cut rest).tail := by
      refine ih rest ?_
      intro i hi
      have := havoid (i + 1) (by simpa using hi)
      simpa using this
    show c.cut (t :: (before' ++ rest)) = _
    rw [c.cut_word t (before' ++ rest) h0, hrec]
    simp

/-- **The round trip for a list.**  A list written as one item, a separator
and another item — where neither item holds a separator — cuts back to exactly
those two items.  This is what makes a described list a description of a
language rather than a rule of thumb: writing and cutting are inverse on the
lists the description can write, whichever admitted separator was used. -/
theorem ListCut.cut_two (c : ListCut) (left sep right : List Token)
    (hleft : CutAvoids c left (sep ++ right))
    (hright : CutAvoids c right [])
    (hsep : c.sepAt (sep ++ right) = some right) (hsepne : sep ≠ []) :
    c.cut (left ++ sep ++ right) = [left, right] := by
  have hr : c.cut right = [right] := by
    have := c.cut_append right [] hright
    simpa using this
  have hmid : c.cut (sep ++ right) = [] :: c.cut right := by
    cases sep with
    | nil => exact absurd rfl hsepne
    | cons s ss => exact c.cut_sep s (ss ++ right) right (by simpa using hsep)
  have hcut := c.cut_append left (sep ++ right) hleft
  rw [List.append_assoc, hcut, hmid, hr]
  simp

/-- The items a described list yields: the empty runs dropped, because a
question written with a trailing separator names no further value. -/
def ListCut.items (c : ListCut) (ts : List Token) : List (List Token) :=
  (c.cut ts).filter (fun item => !item.isEmpty)

/-- A list is *read* only where it names at least the number of items the
description requires; anything shorter is refused rather than padded. -/
def ListCut.read (c : ListCut) (minimum : Nat) (ts : List Token) :
    Option (List (List Token)) :=
  if minimum ≤ (c.items ts).length then some (c.items ts) else none

/-! ## 2.  A word that directs the reading -/

/-- A described modifier: the word, the prepositions that may introduce it in
a trailing frame, and the noun that closes that frame — `under tensor
semantics`.  Where the word may be *written* and where it may be *removed* are
two different questions: it is read off the whole question wherever it stands,
and it is taken out of the operands only in the two positions where it cannot
be part of one. -/
structure ModifierFrame where
  /-- The word that directs the reading. -/
  word : Token
  /-- The prepositions that may open the trailing frame. -/
  prepositions : Phrasing
  /-- The noun that closes the trailing frame. -/
  noun : Token
  deriving Repr, DecidableEq

/-- Whether `suf` is written at the end of `ts`. -/
def hasSuffix (suf ts : List Token) : Bool :=
  ts.drop (ts.length - suf.length) == suf

/-- Writing a suffix puts it at the end. -/
@[simp] theorem hasSuffix_append (suf body : List Token) :
    hasSuffix suf (body ++ suf) = true := by
  simp [hasSuffix]

/-- The trailing frames this modifier may be written in, one per preposition. -/
def ModifierFrame.tails (m : ModifierFrame) : List (List Token) :=
  m.prepositions.alts.map (fun a => a ++ [m.word, m.noun])

/-- Remove the trailing frame where one is written. -/
def ModifierFrame.stripTail (m : ModifierFrame) (ts : List Token) : List Token :=
  match m.tails.find? (fun s => hasSuffix s ts) with
  | some s => ts.take (ts.length - s.length)
  | none => ts

/-- Remove the word at the head, with the noun after it where it is written. -/
def ModifierFrame.stripHead (m : ModifierFrame) : List Token → List Token
  | [] => []
  | [t] => if t = m.word then [] else [t]
  | t :: n :: rest =>
    if t = m.word then (if n = m.noun then rest else n :: rest) else t :: n :: rest

/-- The operands, with the modifier taken out of the two positions where it is
unambiguously a directive. -/
def ModifierFrame.strip (m : ModifierFrame) (ts : List Token) : List Token :=
  m.stripHead (m.stripTail ts)

/-- The trailing frame comes off where it is the first frame that fits. -/
theorem ModifierFrame.stripTail_of_find (m : ModifierFrame) (body s : List Token)
    (hfind : m.tails.find? (fun t => hasSuffix t (body ++ s)) = some s) :
    m.stripTail (body ++ s) = body := by
  simp [ModifierFrame.stripTail, hfind]

/-- **The word comes off the head.**  Where no trailing frame is written, a
question opening with the modifier hands on exactly the operands after it. -/
theorem ModifierFrame.strip_head (m : ModifierFrame) (body : List Token)
    (htail : m.stripTail (m.word :: body) = m.word :: body)
    (hnoun : body.head? ≠ some m.noun) :
    m.strip (m.word :: body) = body := by
  rw [ModifierFrame.strip, htail]
  cases body with
  | nil => simp [ModifierFrame.stripHead]
  | cons n rest =>
    have hn : n ≠ m.noun := by
      intro h; exact hnoun (by simp [h])
    simp [ModifierFrame.stripHead, hn]

/-- **The trailing frame comes off the end.**  Where the operands do not
themselves open with the word, a question closing with `<preposition> <word>
<noun>` hands on exactly the operands before it. -/
theorem ModifierFrame.strip_frame (m : ModifierFrame) (body s : List Token)
    (hfind : m.tails.find? (fun t => hasSuffix t (body ++ s)) = some s)
    (hhead : body.head? ≠ some m.word) :
    m.strip (body ++ s) = body := by
  rw [ModifierFrame.strip, m.stripTail_of_find body s hfind]
  cases body with
  | nil => simp [ModifierFrame.stripHead]
  | cons t rest =>
    have ht : t ≠ m.word := by
      intro h; exact hhead (by simp [h])
    cases rest with
    | nil => simp [ModifierFrame.stripHead, ht]
    | cons n rest' => simp [ModifierFrame.stripHead, ht]

/-- **Anywhere else the word stays.**  A modifier written inside an operand is
left exactly where it stands: removing it there would change the thing being
asked about, so the description removes it in two positions and nowhere
else. -/
theorem ModifierFrame.strip_middle (m : ModifierFrame) (ts : List Token)
    (htail : m.stripTail ts = ts) (hhead : ts.head? ≠ some m.word) :
    m.strip ts = ts := by
  rw [ModifierFrame.strip, htail]
  cases ts with
  | nil => simp [ModifierFrame.stripHead]
  | cons t rest =>
    have ht : t ≠ m.word := by
      intro h; exact hhead (by simp [h])
    cases rest with
    | nil => simp [ModifierFrame.stripHead, ht]
    | cons n rest' => simp [ModifierFrame.stripHead, ht]

/-! ## 3.  An operator formed from a word, between two readings -/

/-- An operator that is *formed* rather than listed: a degree word with the
declared suffix and then the tail (`hotter than`), or the frame around a bare
degree word (`as hot as`).  The set of operators is therefore open — a degree
word is any name — and which word was written is part of the answer, because
the direction the marker asserts is read off the register from it. -/
structure DegreeOperator where
  /-- The suffix a comparative degree word carries. -/
  suffix : String
  /-- The word that closes the comparative form. -/
  tail : Phrasing
  /-- The word that opens and closes the equative frame. -/
  frame : Phrasing
  deriving Repr, DecidableEq

/-- Whether a token is a degree word: the suffix, and something before it.
The bare suffix is not a degree word, which is why the length is checked. -/
def DegreeOperator.isDegreeWord (o : DegreeOperator) (t : Token) : Bool :=
  o.suffix.toList.reverse.isPrefixOf t.toList.reverse && o.suffix.length < t.length

/-- The equative frame read at the head: `as <word> as`, and what follows. -/
def DegreeOperator.frameAt (o : DegreeOperator) (ts : List Token) :
    Option (Token × Bool × List Token) :=
  match o.frame.matchAt ts with
  | some (w :: after') =>
    match o.frame.matchAt after' with
    | some after => some (w, true, after)
    | none => none
  | _ => none

/-- The operator read at the head, in either of its two forms: the degree word
and its tail, or the equative frame.  `true` in the answer is the equative,
which asserts that the two readings are the same where the other asserts an
order. -/
def DegreeOperator.at? (o : DegreeOperator) :
    List Token → Option (Token × Bool × List Token)
  | [] => none
  | t :: rest =>
    if o.isDegreeWord t then
      match o.tail.matchAt rest with
      | some after => some (t, false, after)
      | none => o.frameAt (t :: rest)
    else o.frameAt (t :: rest)

/-- The **earliest** operator in a question: the tokens before it, the degree
word, whether the equative frame was written, and the tokens after it.  The
earliest position wins, which is what makes the left operand the shortest run
that can be one. -/
def DegreeOperator.find (o : DegreeOperator) :
    List Token → Option (List Token × Token × Bool × List Token)
  | [] => none
  | t :: rest =>
    match o.at? (t :: rest) with
    | some (w, eq, after) => some ([], w, eq, after)
    | none => (o.find rest).map (fun r => (t :: r.1, r.2))

/-- No operator is formed inside `before` when `rest` follows it. -/
def OpAvoids (o : DegreeOperator) (before rest : List Token) : Prop :=
  ∀ i, i < before.length → o.at? (before.drop i ++ rest) = none

/-- A run of tokens forming no operator is passed over, and the operator after
it is the one that is found. -/
theorem DegreeOperator.find_append (o : DegreeOperator) :
    ∀ (before rest : List Token) (w : Token) (eq : Bool) (after : List Token),
      OpAvoids o before rest → o.at? rest = some (w, eq, after) →
      o.find (before ++ rest) = some (before, w, eq, after) := by
  intro before
  induction before with
  | nil =>
    intro rest w eq after _ hat
    cases rest with
    | nil => simp [DegreeOperator.at?] at hat
    | cons t rest' => simp [DegreeOperator.find, hat]
  | cons t before' ih =>
    intro rest w eq after havoid hat
    have h0 : o.at? (t :: (before' ++ rest)) = none := havoid 0 (by simp)
    have hrec : o.find (before' ++ rest) = some (before', w, eq, after) := by
      refine ih rest w eq after ?_ hat
      intro i hi
      have := havoid (i + 1) (by simpa using hi)
      simpa using this
    show o.find (t :: (before' ++ rest)) = _
    simp only [DegreeOperator.find, h0, hrec, Option.map_some]

/-! ## 4.  A shape whose operands are readings -/

/-- A described nested shape: an operator, and the shape *each side must
match*.  The side is the shape itself and not a second copy of it, which is
what keeps the nesting from becoming a surface with a life of its own. -/
structure NestedSpec where
  /-- The query kind a match of this shape produces. -/
  kind : String
  /-- The operator between the two readings. -/
  op : DegreeOperator
  /-- The shape each side must match. -/
  side : List Piece
  deriving Repr, DecidableEq

/-- What a nested shape answers with: the degree word that formed the
operator, whether it was the equative frame, and the filling of each side.
The fillings are the ones a single shape produces, so a nested match is
literally two matches of the side shape and the word between them. -/
abbrev NestedMatch :=
  Token × Bool × List (String × List Token) × List (String × List Token)

/-- **The nested matcher.**  Find the earliest operator, match the shape
against each side, and answer with the degree word, its form and the two
fillings.  A side that is not a use of the shape is not an operand, and the
question is refused rather than read with the stray words inside a slot. -/
def NestedSpec.run (n : NestedSpec) (ts : List Token) : Option NestedMatch :=
  match n.op.find ts with
  | none => none
  | some (left, w, eq, right) =>
    match matchPieces n.side left with
    | none => none
    | some l =>
      match matchPieces n.side right with
      | none => none
      | some r => some ⟨w, eq, l, r⟩

/-- **The round trip for a nested shape.**  A question written as two fillings
of the side shape with an operator between them reads back as exactly those
two fillings and the word it was written with.  The hypotheses are the ones
`Question.lean` already needs for a single shape — each side written cleanly —
together with the one the nesting adds: no operator is formed inside the left
side, so the earliest operator is the one that was written. -/
theorem NestedSpec.run_rendered (n : NestedSpec) (fl fr : String → List Token)
    (w : Token) (hword : n.op.isDegreeWord w = true)
    (hcl : Clean n.side fl) (hcr : Clean n.side fr)
    (htail : n.op.tail.matchAt (n.op.tail.head ++ rendered n.side fr)
      = some (rendered n.side fr))
    (havoid : OpAvoids n.op (rendered n.side fl)
      (w :: (n.op.tail.head ++ rendered n.side fr))) :
    n.run (rendered n.side fl ++ (w :: (n.op.tail.head ++ rendered n.side fr)))
      = some (w, false, written n.side fl, written n.side fr) := by
  have hat : n.op.at? (w :: (n.op.tail.head ++ rendered n.side fr))
      = some (w, false, rendered n.side fr) := by
    simp [DegreeOperator.at?, hword, htail]
  have hfind := n.op.find_append (rendered n.side fl)
    (w :: (n.op.tail.head ++ rendered n.side fr)) w false (rendered n.side fr) havoid hat
  rw [NestedSpec.run, hfind]
  dsimp only
  rw [matchPieces_rendered n.side fl hcl, matchPieces_rendered n.side fr hcr]

/-- **A question that forms no operator is not of this shape.**  There is no
nearest guess and no partial reading: the operator is where a nested shape is
entered. -/
theorem NestedSpec.run_no_operator (n : NestedSpec) (ts : List Token)
    (h : n.op.find ts = none) : n.run ts = none := by
  rw [NestedSpec.run, h]

/-- **A side that is not a use is refused.**  The operator may be formed and
the question still declined, which is exactly the boundary between this shape
and the comparison of two exact reals: `sqrt(2) greater than 7/5` forms the
operator, and `sqrt(2)` is not a measured use. -/
theorem NestedSpec.run_side_refused (n : NestedSpec) (ts left right : List Token)
    (w : Token) (eq : Bool) (h : n.op.find ts = some (left, w, eq, right))
    (hside : matchPieces n.side left = none ∨ matchPieces n.side right = none) :
    n.run ts = none := by
  rw [NestedSpec.run, h]
  dsimp only
  rcases hside with hl | hr
  · rw [hl]
  · rw [hr]
    cases matchPieces n.side left <;> rfl

/-! ## 5.  The shipped surfaces -/

/-- The shipped `compare` list: `and` / `versus` / `vs`, a comma, and the
second rank `with`. -/
def compareCut : ListCut :=
  ⟨[⟨[["and"], ["versus"], ["vs"]]⟩, ⟨[["with"]]⟩], ","⟩

/-- The first rank, read. -/
theorem compareCut_and :
    compareCut.cut ["sqrt(2)", "and", "1.5"] = [["sqrt(2)"], ["1.5"]] := by
  rw [compareCut.cut_word "sqrt(2)" ["and", "1.5"] (by decide),
      compareCut.cut_sep "and" ["1.5"] ["1.5"] (by decide),
      compareCut.cut_word "1.5" [] (by decide)]
  simp

/-- The mark, read the same way — and the second rank after it, so the two
ranks are not merged into one and a list written with either is one list. -/
theorem compareCut_mark_and_second_rank :
    compareCut.cut ["sqrt(2)", ",", "1.5", "with", "2"]
      = [["sqrt(2)"], ["1.5"], ["2"]] := by
  rw [compareCut.cut_word "sqrt(2)" [",", "1.5", "with", "2"] (by decide),
      compareCut.cut_sep "," ["1.5", "with", "2"] ["1.5", "with", "2"] (by decide),
      compareCut.cut_word "1.5" ["with", "2"] (by decide),
      compareCut.cut_sep "with" ["2"] ["2"] (by decide),
      compareCut.cut_word "2" [] (by decide)]
  simp

/-- A comparison that names one value only is refused, not completed. -/
theorem compareCut_refuses_one_value :
    compareCut.read 2 ["sqrt(2)"] = none := by
  rw [ListCut.read, ListCut.items,
      compareCut.cut_word "sqrt(2)" [] (by decide)]
  simp

/-- The shipped `tensor` modifier of the audit question: at the head, or in
the trailing frame `under tensor semantics`. -/
def tensorModifier : ModifierFrame :=
  ⟨"tensor", ⟨[["under"], ["with"], ["in"]]⟩, "semantics"⟩

/-- Written at the head, the word comes off and the equation is what is
left. -/
theorem tensorModifier_head :
    tensorModifier.strip ["tensor", "force", "=", "mass", "acceleration"]
      = ["force", "=", "mass", "acceleration"] := by
  refine tensorModifier.strip_head ["force", "=", "mass", "acceleration"] ?_ (by decide)
  decide

/-- Written in the trailing frame, it comes off the end. -/
theorem tensorModifier_frame :
    tensorModifier.strip ["force", "=", "mass", "acceleration", "under", "tensor",
      "semantics"] = ["force", "=", "mass", "acceleration"] := by
  have h : (["force", "=", "mass", "acceleration"] : List Token)
      ++ ["under", "tensor", "semantics"]
      = ["force", "=", "mass", "acceleration", "under", "tensor", "semantics"] := by
    simp
  rw [← h]
  refine tensorModifier.strip_frame ["force", "=", "mass", "acceleration"]
    ["under", "tensor", "semantics"] ?_ (by decide)
  decide

/-- Written inside the equation, it stays: the audit is of the equation as it
was asked about, and deleting a qualifier there would change it. -/
theorem tensorModifier_middle :
    tensorModifier.strip ["force", "=", "tensor", "charge"]
      = ["force", "=", "tensor", "charge"] := by
  refine tensorModifier.strip_middle ["force", "=", "tensor", "charge"] ?_ (by decide)
  decide

/-- The shipped comparative operator: `<word>er than`, or `as <word> as`. -/
def comparativeOperator : DegreeOperator :=
  ⟨"er", ⟨[["than"]]⟩, ⟨[["as"]]⟩⟩

/-- One side of the shipped comparative: a measured use with its opening
dropped — inside a comparative a use is recognised by its position, not by the
word `measure` — and both of its slots required. -/
def measureSide : List Piece :=
  [Piece.hole ⟨"word", false⟩,
   Piece.lit ⟨[["in"], ["of"], ["for"]]⟩,
   Piece.hole ⟨"object", false⟩]

/-- `<use> <word>er than <use>` — the shipped comparative, written down. -/
def comparativeShape : NestedSpec :=
  { kind := "comparative", op := comparativeOperator, side := measureSide }

/-- The shipped question, read by the description: the degree word, the form,
and a filling for each side. -/
theorem comparativeShape_cold_hotter_than_hot :
    comparativeShape.run
        ["cold", "in", "stellar_surface", "hotter", "than", "hot", "in", "tea"] =
      some ("hotter", false,
        [("word", ["cold"]), ("object", ["stellar_surface"])],
        [("word", ["hot"]), ("object", ["tea"])]) := by
  rfl

/-- The equative frame, read as the same shape asking the other question. -/
theorem comparativeShape_as_hot_as :
    comparativeShape.run
        ["cold", "in", "tea", "as", "hot", "as", "hot", "in", "kettle"] =
      some ("hot", true,
        [("word", ["cold"]), ("object", ["tea"])],
        [("word", ["hot"]), ("object", ["kettle"])]) := by
  rfl

/-- A question with no operator in it is not a comparative. -/
theorem comparativeShape_refuses_no_operator :
    comparativeShape.run ["derive", "span_ratio", "of", "tea"] = none := by
  decide

/-- **The boundary.**  `sqrt(2) greater than 7/5` forms the operator and is
still refused, because `sqrt(2)` is not a measured use — which is what keeps
the exact-real comparison out of this shape. -/
theorem comparativeShape_refuses_exact_real :
    comparativeShape.run ["sqrt(2)", "greater", "than", "7/5"] = none := by
  decide

end GLM.QuestionNested
