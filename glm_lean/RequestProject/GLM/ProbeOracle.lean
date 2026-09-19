/-
# What a refusal is evidence of

`glm_universal/reasoning/probe_oracle.py` runs the experiment blocker 1
declares: each of the twenty pre-registered probe questions is hand-written
into the system's own query grammar, and the translation is asked instead of
the English.  Every question then lands in one of three classes -- the query
grammar answers it (`parsed`), a register or a shipped function holds the
answer and no query kind returns it (`surface`), or nothing holds it at all
(`absent`).

The study's arithmetic depends on that classification being a *partition*: the
sentence "6 are parsed, 10 are surface and 4 are absent, of 20" is only a
reading of the same twenty questions if no question is counted twice and none
is missed.  This file is that dependency, discharged.

* `Verdict` is the three classes;
* `classify` is the classification, as the implementation performs it: two
  Booleans -- was it answered at its declared locus, does a witness hold it --
  decide the class, and nothing else does.

What is proved:

* `classify_parsed_iff`, `classify_surface_iff`, `classify_absent_iff` -- each
  class is exactly the condition on the two facts that the study states for
  it, so the class names carry no content the measurement does not;
* `classify_exhaustive` and `classify_exclusive` -- every question receives
  one class and no question receives two;
* `not_parsed_of_not_answered` -- a question with no expressible query is
  never counted as answered.  This is the claim that keeps the experiment from
  flattering the grammar, and it is the Lean form of the test that refuses a
  translation which smuggles the expected fragment into the query;
* `witness_irrelevant_when_answered` -- the witness is only ever consulted for
  a question the grammar failed, so no question is counted `parsed` *because*
  a register holds its answer;
* `counts_partition` -- the three counts over any list of questions sum to the
  number of questions, which is the arithmetic the study's headline performs;
* `parsed_add_surface_le` and `absent_eq_sub` -- the two corollaries the prose
  uses: the answerable classes never exceed the sample, and the absent count
  is what the other two leave.
-/
import Mathlib.Tactic

namespace GLM.ProbeOracle

/-- The three classes a translated question can land in. -/
inductive Verdict
  | parsed
  | surface
  | absent
  deriving DecidableEq, Repr

/-- One question, reduced to the two facts that decide its class: whether the
translation was answered with the declared fragment in the declared field, and
whether a witness holds the answer independently of any query. -/
structure Question where
  /-- The translation exists and the session answered it at its locus. -/
  answered : Bool
  /-- A register row, a shipped function or the source holds the answer. -/
  held : Bool
  deriving DecidableEq, Repr

/-- The classification, exactly as `probe_oracle.class_of` performs it. -/
def classify (q : Question) : Verdict :=
  if q.answered then Verdict.parsed
  else if q.held then Verdict.surface else Verdict.absent

@[simp] theorem classify_parsed_iff (q : Question) :
    classify q = Verdict.parsed ↔ q.answered = true := by
  cases hq : q.answered <;> cases hh : q.held <;>
    simp [classify, hq, hh]

@[simp] theorem classify_surface_iff (q : Question) :
    classify q = Verdict.surface ↔ q.answered = false ∧ q.held = true := by
  cases hq : q.answered <;> cases hh : q.held <;>
    simp [classify, hq, hh]

@[simp] theorem classify_absent_iff (q : Question) :
    classify q = Verdict.absent ↔ q.answered = false ∧ q.held = false := by
  cases hq : q.answered <;> cases hh : q.held <;>
    simp [classify, hq, hh]

/-- Every question receives one of the three classes. -/
theorem classify_exhaustive (q : Question) :
    classify q = Verdict.parsed ∨ classify q = Verdict.surface
      ∨ classify q = Verdict.absent := by
  cases hq : q.answered <;> cases hh : q.held <;>
    simp [classify, hq, hh]

/-- No question receives two of them. -/
theorem classify_exclusive (q : Question) (v w : Verdict)
    (hv : classify q = v) (hw : classify q = w) : v = w := by
  rw [← hv, ← hw]

/-- A question with no expressible query -- so nothing answered -- is never
counted as one the grammar handles. -/
theorem not_parsed_of_not_answered {q : Question} (h : q.answered = false) :
    classify q ≠ Verdict.parsed := by
  simp [classify_parsed_iff, h]

/-- The witness never makes a question `parsed`: for an answered question the
class does not depend on what any register holds. -/
theorem witness_irrelevant_when_answered {b c : Bool}
    (h : b = true) :
    classify ⟨b, c⟩ = classify ⟨b, !c⟩ := by
  simp [classify, h]

/-- How many questions of a list fall in one class. -/
def count (v : Verdict) (qs : List Question) : ℕ :=
  (qs.filter (fun q => classify q = v)).length

@[simp] theorem count_nil (v : Verdict) : count v [] = 0 := rfl

theorem count_cons (v : Verdict) (q : Question) (qs : List Question) :
    count v (q :: qs) = (if classify q = v then 1 else 0) + count v qs := by
  by_cases h : classify q = v <;>
    simp [count, h, Nat.add_comm]

/-- The three counts partition the sample: the study's headline reads the same
twenty questions three ways rather than counting three things. -/
theorem counts_partition (qs : List Question) :
    count Verdict.parsed qs + count Verdict.surface qs
      + count Verdict.absent qs = qs.length := by
  induction qs with
  | nil => simp
  | cons q qs ih =>
      have hq := classify_exhaustive q
      rcases hq with h | h | h <;>
        simp [count_cons, h, List.length_cons] <;> omega

/-- The classes that report an answer as reachable never exceed the sample. -/
theorem parsed_add_surface_le (qs : List Question) :
    count Verdict.parsed qs + count Verdict.surface qs ≤ qs.length := by
  have := counts_partition qs
  omega

/-- What is held nowhere is what the other two classes leave. -/
theorem absent_eq_sub (qs : List Question) :
    count Verdict.absent qs
      = qs.length - (count Verdict.parsed qs + count Verdict.surface qs) := by
  have := counts_partition qs
  omega

end GLM.ProbeOracle
