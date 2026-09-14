/-
# The anonymous register: where a structural address is the only reader

`Retrieval.lean` proves what an index built on the lattice can promise, and the
measurement beside it records a negative result: asked to retrieve a relevant
declaration, the geometric address beats chance several times over and is
beaten decisively by a plain lexical overlap of the statement text.
`Relay.lean` then shows the arrangement in which the address still earns its
place — gated on the text layer's own confidence, it *carries* the queries the
text layer cannot read — but the carry set measured there is a residue: a
handful of queries out of sixteen hundred.

This file is about the register in which the carry set is not a residue but a
**class**.  A query is *anonymous* when its identifiers are not the corpus's
identifiers: a goal from another formalisation, a generated goal with no names
yet, a statement autoformalised in the vocabulary of its source.  Renaming is
the exactly reproducible form of that situation, and
`overlay/glm_universal/reasoning/anonymous.py` measures retrieval over it.

What is proved here is why the measurement comes out as it does, and it is
three statements about renaming rather than three observations about a table.

## 1.  A renaming does not disturb the structure

A statement is a list of tokens, each either a word of the declared vocabulary
— Lean's own syntax and the type names the feature map counts — or an
identifier of the development.  `anonymise` replaces every identifier and
leaves every kept word where it is.  `skeleton_anonymise` says the kept
skeleton is untouched, so **any** reading that is a function of the skeleton is
untouched with it (`features_anonymise`).  The structural address is such a
reading, and that is the whole reason the geometry survives anonymisation.

## 2.  A renaming destroys the overlap

`idents_anonymise` says the identifiers of an anonymised statement are exactly
the renamed ones, so if the placeholder alphabet is fresh — no placeholder is a
word of the corpus — no anonymised query shares an identifier with any
statement of the corpus (`shares_anonymise_eq_false`), and the exact Jaccard
overlap the text faculty scores with is zero (`overlap_anonymise_eq_zero`).
That is a theorem about the faculty, not a measurement of it: in this register
the text layer has no evidence *by construction*.

## 3.  Therefore the stack hands the register over

Putting the two together with `Relay.relay_abstain`: a leader whose confidence
is the overlap has confidence `0` on every anonymous query, so for any positive
gate the relay of `Relay.lean` is the interleave of the remaining faculties
(`relay_hands_over`).  The stack does not have to be re-tuned, or told about
the register, or given a new rule: the gate it already carries fires, and the
geometric books answer.  `address_is_the_only_reader` states the pair of facts
the register turns on — the structural reading is unchanged and the overlap is
zero — as one theorem.

The measured half is in `studies/ANONYMOUS_REGISTER_STUDY.md`: over 813 queries
the text faculty falls from 710 hits at `k = 5` to 84 and the identifier
address book from 388 to 48, which is exactly the 48 that chance gives, while
the structural address keeps 171 of its 232 and leads every other faculty in
the register by more than a factor of two.
-/
import Mathlib
import RequestProject.GLM.Relay

namespace GLM.Anonymous

/-! ## 1.  Statements, and what a renaming does to them -/

/-- A token of a statement: either a word of the declared vocabulary — Lean's
own syntax, and the type names the structural feature map counts — or an
identifier of the development. -/
inductive Tok where
  /-- A word of the declared vocabulary, which a renaming leaves alone. -/
  | kept : String → Tok
  /-- An identifier of the development, which a renaming replaces. -/
  | name : String → Tok
  deriving DecidableEq, Repr

/-- Rename every identifier by `f`, leaving the declared vocabulary alone.

`f` is any renaming at all: the Python side uses position of first appearance,
but nothing below depends on that choice, which is what makes the results
statements about *renaming* rather than about one particular anonymiser. -/
def anonymise (f : String → String) : List Tok → List Tok
  | [] => []
  | Tok.kept s :: ts => Tok.kept s :: anonymise f ts
  | Tok.name s :: ts => Tok.name (f s) :: anonymise f ts

/-- The kept skeleton of a statement: the declared vocabulary, in order.

Everything the structural feature map reads — the quantifiers, the arrows, the
equalities, the numerals, the bracket depth, the type words, the length — is a
function of this list. -/
def skeleton : List Tok → List String
  | [] => []
  | Tok.kept s :: ts => s :: skeleton ts
  | Tok.name _ :: ts => skeleton ts

/-- The identifiers of a statement, in order. -/
def idents : List Tok → List String
  | [] => []
  | Tok.kept _ :: ts => idents ts
  | Tok.name s :: ts => s :: idents ts

@[simp] theorem anonymise_nil (f : String → String) :
    anonymise f [] = [] := rfl

@[simp] theorem skeleton_nil : skeleton [] = [] := rfl

@[simp] theorem idents_nil : idents [] = [] := rfl

/-- **The structure survives a renaming.**  Replacing identifiers leaves the
kept skeleton exactly as it was. -/
@[simp] theorem skeleton_anonymise (f : String → String) :
    ∀ t : List Tok, skeleton (anonymise f t) = skeleton t
  | [] => rfl
  | Tok.kept s :: ts => by
      simp [anonymise, skeleton, skeleton_anonymise f ts]
  | Tok.name s :: ts => by
      simp [anonymise, skeleton, skeleton_anonymise f ts]

/-- **Any structural reading is invariant.**  A feature map that is a function
of the skeleton — which is what the 24 structural counts are — reads an
anonymised statement exactly as it reads the original.  This is why the
geometric address is still pointing at the same place when the names are
gone. -/
theorem features_anonymise {α : Type*} (read : List String → α)
    (f : String → String) (t : List Tok) :
    read (skeleton (anonymise f t)) = read (skeleton t) := by
  rw [skeleton_anonymise]

/-- The identifiers of an anonymised statement are the renamed ones. -/
@[simp] theorem idents_anonymise (f : String → String) :
    ∀ t : List Tok, idents (anonymise f t) = (idents t).map f
  | [] => rfl
  | Tok.kept s :: ts => by
      simp [anonymise, idents, idents_anonymise f ts]
  | Tok.name s :: ts => by
      simp [anonymise, idents, idents_anonymise f ts]

/-! ## 2.  The overlap the text faculty scores with -/

/-- Do two statements share an identifier?  The text faculty's evidence: its
exact Jaccard overlap is positive exactly when this is true. -/
def shares (a b : List Tok) : Prop := ∃ x ∈ idents a, x ∈ idents b

instance (a b : List Tok) : Decidable (shares a b) := by
  unfold shares; infer_instance

/-- The exact overlap of two statements: how many identifiers they share over
how many they have between them, as a rational.  The same quantity
`retrieval.rank_by_text` ranks with, and the confidence `stack.confidence_of`
reports. -/
noncomputable def overlap (a b : List Tok) : ℚ :=
  let shared := ((idents a).filter (fun x => x ∈ idents b)).eraseDups
  let union := ((idents a) ++ (idents b)).eraseDups
  if union.length = 0 then 0 else (shared.length : ℚ) / (union.length : ℚ)

/-- A renaming is **fresh** for a corpus when no name it produces is a word of
the corpus.  Checked against the corpus rather than assumed: the Python side's
`placeholders_are_fresh` runs exactly this test over every identifier of every
statement. -/
def Fresh (f : String → String) (corpus : List (List Tok)) : Prop :=
  ∀ s : String, ∀ b ∈ corpus, f s ∉ idents b

/-- **A fresh renaming destroys the overlap.**  An anonymised query shares no
identifier with any statement of the corpus. -/
theorem shares_anonymise_eq_false {f : String → String}
    {corpus : List (List Tok)} (hf : Fresh f corpus)
    (t : List Tok) {b : List Tok} (hb : b ∈ corpus) :
    ¬ shares (anonymise f t) b := by
  rintro ⟨x, hx, hxb⟩
  rw [idents_anonymise] at hx
  obtain ⟨s, _, rfl⟩ := List.mem_map.mp hx
  exact hf s b hb hxb

/-- **Therefore the overlap is exactly zero**, the number the text faculty
reports as its confidence. -/
theorem overlap_anonymise_eq_zero {f : String → String}
    {corpus : List (List Tok)} (hf : Fresh f corpus)
    (t : List Tok) {b : List Tok} (hb : b ∈ corpus) :
    overlap (anonymise f t) b = 0 := by
  have hfilter :
      (idents (anonymise f t)).filter (fun x => x ∈ idents b) = [] := by
    rw [List.filter_eq_nil_iff]
    intro x hx hxb
    exact shares_anonymise_eq_false hf t hb ⟨x, hx, by simpa using hxb⟩
  have hshared :
      ((idents (anonymise f t)).filter
        (fun x => x ∈ idents b)).eraseDups = [] := by
    rw [hfilter]; rfl
  unfold overlap
  simp only [hshared, List.length_nil, Nat.cast_zero, zero_div]
  split <;> rfl

/-! ## 3.  The stack hands the register over -/

open GLM.Relay

/-- **The register is handed to the geometry, by theorem.**  A leader whose
confidence is the overlap it achieves has confidence zero on an anonymous
query, so for any positive gate `Relay.relay` returns the interleave of the
other faculties.  Nothing is re-tuned and no new rule is added: the gate the
stack already carries is enough. -/
theorem relay_hands_over {α : Type*} [DecidableEq α]
    {f : String → String} {corpus : List (List Tok)} (hf : Fresh f corpus)
    (t : List Tok) {b : List Tok} (hb : b ∈ corpus)
    (lead : Answer α) (plan : Plan α) (gate : ℚ) (hgate : 0 < gate)
    (hconf : lead.confidence = overlap (anonymise f t) b) :
    relay lead plan gate = interleave plan := by
  refine relay_abstain ?_
  rw [hconf, overlap_anonymise_eq_zero hf t hb]
  exact hgate

/-- **The register in one statement.**  Against a fresh renaming, a structural
reading of the query is unchanged and the text faculty's overlap is zero: the
address is the only faculty of the stack still reading anything. -/
theorem address_is_the_only_reader {α : Type*} (read : List String → α)
    {f : String → String} {corpus : List (List Tok)} (hf : Fresh f corpus)
    (t : List Tok) {b : List Tok} (hb : b ∈ corpus) :
    read (skeleton (anonymise f t)) = read (skeleton t)
      ∧ overlap (anonymise f t) b = 0 :=
  ⟨features_anonymise read f t, overlap_anonymise_eq_zero hf t hb⟩

/-! ## 4.  A worked example, checked by the kernel -/

/-- The statement `∀ n : Nat, f n = n` as a token list: three kept words and
two identifiers. -/
def example_statement : List Tok :=
  [Tok.kept "forall", Tok.name "n", Tok.kept "Nat", Tok.name "f",
   Tok.name "n"]

/-- The anonymiser of the example: every identifier goes to `v0`.  Even this
crude renaming leaves the skeleton alone.  The string it uses is not the
placeholder the Python side uses, because a placeholder written into a Lean
file would become a word of the corpus and break the freshness check the
measurement runs. -/
def example_rename (_ : String) : String := "w"

example : skeleton (anonymise example_rename example_statement)
    = skeleton example_statement := by decide

example : idents (anonymise example_rename example_statement)
    = ["w", "w", "w"] := by decide

example : ¬ shares (anonymise example_rename example_statement)
    [Tok.name "n", Tok.name "f"] := by decide

end GLM.Anonymous
