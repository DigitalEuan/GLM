import Mathlib
import RequestProject.MeasuredWords

/-!
# Generating sentences that make sense — and measuring how often the cube agrees

`MeasuredWords` put the measurable content of a word (its dimension) on the
cube surface and showed what the substrate can decide about it.  This file uses
that to *generate* sentences, and then measures — honestly, by counting — how
good the cube's verdict actually is.

## The experiment

* `phrases` — a vocabulary of 12 measurable words plus all 144 two-word
  products: **156 phrases** (`phrases_count`).
* `equations` — all ordered pairs of differently-named phrases with **equal
  dimension**.  These are the sentences that make sense; there are **356** of
  them (`equations_count`), and each one is dimensionally true by construction
  (`equations_true`).
* `substrateAccepts` — the pairs the cube itself passes, i.e. those whose
  codewords are equal.  There are **1758** (`substrate_count`).

## The measurement

* `equations_are_accepted` — the generator is *sound for the substrate*: every
  sentence that makes sense is accepted, so a true sentence never pays tax.
* `substrate_false_positive_count` — and the honest failure: **1402** of the
  1758 pairs the cube accepts are dimensionally false.  The cube's own filter
  has precision `356/1758 ≈ 20%`.

That number is the exact cost of the characteristic-2 ceiling proved in
`MeasuredWords.xor_encoding_is_mod_two`: the cube sees exponents mod 2, so it
cannot tell `length` from `acceleration`.  To generate sentences that make
sense one must keep the integer dimension alongside the codeword; the cube's
contribution is the *free, error-corrected* carrier for it, not the semantic
decision itself.
-/

namespace MeasuredSentences

open MeasuredWords CubeMOG

/-- A phrase: a name and the measurable content it denotes. -/
abbrev Phrase := String × Dim

/-- The vocabulary of single measurable words. -/
def base : List Phrase :=
  [("length", length), ("mass", mass), ("time", time), ("current", current),
   ("velocity", velocity), ("acceleration", acceleration), ("force", force),
   ("energy", energy), ("action", action), ("momentum", momentum),
   ("power", power), ("charge", charge)]

/-- All two-word products. -/
def products : List Phrase :=
  base.flatMap fun p => base.map fun q => (p.1 ++ "*" ++ q.1, p.2 + q.2)

/-- The 156 phrases the generator works with. -/
def phrases : List Phrase := base ++ products

theorem phrases_count : phrases.length = 156 := by native_decide

/-- All ordered pairs of phrases with different names. -/
def candidates : List (Phrase × Phrase) :=
  (phrases.flatMap fun p => phrases.map fun q => (p, q)).filter
    fun pq => decide (pq.1.1 ≠ pq.2.1)

/-- **The sentences that make sense**: pairs whose dimensions are genuinely
equal. -/
def equations : List (Phrase × Phrase) :=
  candidates.filter fun pq => decide (pq.1.2 = pq.2.2)

/-- **The sentences the cube accepts**: pairs whose codewords are equal. -/
def substrateAccepts : List (Phrase × Phrase) :=
  candidates.filter fun pq => decide (dimWord pq.1.2 = dimWord pq.2.2)

theorem equations_count : equations.length = 356 := by native_decide

theorem substrate_count : substrateAccepts.length = 1758 := by native_decide

/-- Every generated sentence is dimensionally true. -/
theorem equations_true (e : Phrase × Phrase) (he : e ∈ equations) : e.1.2 = e.2.2 := by
  have h := (List.mem_filter.mp he).2
  simpa using h

/-- **Soundness for the substrate**: every sentence that makes sense is
accepted by the cube, hence costs no tax. -/
theorem equations_are_accepted (e : Phrase × Phrase) (he : e ∈ equations) :
    dimWord e.1.2 = dimWord e.2.2 := by
  rw [equations_true e he]

theorem equations_tax_zero (e : Phrase × Phrase) (he : e ∈ equations) :
    taxOf e.1.2 e.2.2 = 0 :=
  taxOf_accepted _ _ (equations_are_accepted e he)

/-- **The honest failure, counted.**  1402 of the 1758 pairs the cube accepts
are dimensionally false: the cube's filter is sound but far from complete, and
its precision on this vocabulary is `356/1758`. -/
theorem substrate_false_positive_count :
    (substrateAccepts.filter fun pq => decide (pq.1.2 ≠ pq.2.2)).length = 1402 := by
  native_decide

/-- A concrete false positive: the cube cannot tell a length from an
acceleration. -/
theorem length_vs_acceleration :
    length ≠ acceleration ∧ dimWord length = dimWord acceleration := by
  constructor
  · intro h
    have := congrFun h 2
    revert this
    decide
  · rw [dimWord_eq_iff]
    decide

end MeasuredSentences
