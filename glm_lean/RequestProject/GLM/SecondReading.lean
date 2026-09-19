/-
# A second reading before answering: what a guard can promise

`studies/OPERATION_ESCALATION_STUDY.md` measures seven operations under one
refusal contract — *answer only when the rung's cell is non-empty and every
carrier in it carries the same label* — and reports one failure: the
program-text operation answers 13 of 576 queries **wrongly** rather than
refusing.  The diagnosis is that its label is not carried by the coordinates,
so a cell can be unanimous and unanimously wrong; unanimity across the rungs
of *one* reading cannot catch that.

`studies/SECOND_READING_STUDY.md` asks the next question: require a **second,
independent reading** to agree before answering.  This file is the part of
that question that is a theorem rather than a count.  A guard takes two
answers — the primary reading's and the second reading's, either of which may
be a refusal — and returns an answer or a refusal.

## 1.  The two guards

`strictGuard` answers only when both readings answer and they agree.
`vetoGuard` answers whenever the primary answers and the second reading does
not contradict it — so a second reading that refuses stands aside rather than
blocking.  `strictGuard_eq_some` and `vetoGuard_eq_some` characterise exactly
when each one answers, and with what.

## 2.  A guard invents nothing

`strictGuard_sound` and `vetoGuard_sound`: a guard's answer is always the
primary's answer.  Everything else here follows from those two, and they are
what makes a guard a *filter* on the shipped reading rather than a new reading
with its own failure modes.

## 3.  A wrong answer needs both readings to be wrong

`strictGuard_wrong_imp`: if the strict guard answers wrongly then the primary
answered wrongly **and the second reading answered the same wrong label**.
`vetoGuard_wrong_imp` is the weaker statement its weaker contract earns: the
primary answered wrongly and the second reading did not contradict it.
`strictGuard_safe_of_sound` and `vetoGuard_safe_of_sound` turn those round:
a second reading that is sound on a query — when it answers, it answers the
truth — makes the strict guard safe there, and makes the veto guard safe there
provided it does answer.

## 4.  The cost direction

`strictGuard_correct_subset` and `vetoGuard_correct_subset`: a query a guard
answers correctly is a query the primary answered correctly.  So a guard can
only give correct answers up, never gain them, and the measurement's job is to
count how many.  §5 carries both directions to counts over a list of queries:
`strict_correctCount_le`, `strict_wrongCount_le` and their veto counterparts
say that guarding moves both columns of the score sheet downwards, which is
why safety has to be paid for and the study's marks M2 and M4 exist.

## 5.  The two guards compared

`strictGuard_le_vetoGuard`: wherever the strict guard answers, the veto guard
answers the same thing.  The strict guard is therefore the more conservative
of the two by theorem, and a sweep over the two of them is a sweep over a
chain and not over two unrelated contracts.
-/
import Mathlib

namespace GLM.SecondReading

variable {α : Type*} [DecidableEq α]

/-! ## 1.  The two guards -/

/-- Answer only when both readings answer and they agree. -/
def strictGuard (p s : Option α) : Option α :=
  match p, s with
  | some a, some b => if a = b then some a else none
  | _, _ => none

/-- Answer whenever the primary answers and the second reading does not
contradict it. -/
def vetoGuard (p s : Option α) : Option α :=
  match p, s with
  | some a, some b => if a = b then some a else none
  | some a, none => some a
  | none, _ => none

@[simp] theorem strictGuard_none_left (s : Option α) :
    strictGuard (none : Option α) s = none := by
  cases s <;> rfl

@[simp] theorem strictGuard_none_right (p : Option α) :
    strictGuard p (none : Option α) = none := by
  cases p <;> rfl

@[simp] theorem vetoGuard_none_left (s : Option α) :
    vetoGuard (none : Option α) s = none := by
  cases s <;> rfl

@[simp] theorem vetoGuard_none_right (p : Option α) :
    vetoGuard p (none : Option α) = p := by
  cases p <;> rfl

/-- Exactly when the strict guard answers, and with what. -/
theorem strictGuard_eq_some {p s : Option α} {a : α} :
    strictGuard p s = some a ↔ p = some a ∧ s = some a := by
  cases p with
  | none => simp
  | some x =>
    cases s with
    | none => simp
    | some y =>
      by_cases h : x = y
      · subst h; simp [strictGuard]
      · simp [strictGuard, h]
        intro hx
        subst hx
        exact fun hy => h hy.symm

/-- Exactly when the veto guard answers, and with what. -/
theorem vetoGuard_eq_some {p s : Option α} {a : α} :
    vetoGuard p s = some a ↔ p = some a ∧ (s = none ∨ s = some a) := by
  cases p with
  | none => simp
  | some x =>
    cases s with
    | none => simp [vetoGuard, eq_comm]
    | some y =>
      by_cases h : x = y
      · subst h; simp [vetoGuard]
      · simp [vetoGuard, h]
        intro hx
        subst hx
        exact fun hy => h hy.symm

/-! ## 2.  A guard invents nothing -/

/-- The strict guard's answer is the primary's answer. -/
theorem strictGuard_sound {p s : Option α} {a : α}
    (h : strictGuard p s = some a) : p = some a :=
  (strictGuard_eq_some.mp h).1

/-- The veto guard's answer is the primary's answer. -/
theorem vetoGuard_sound {p s : Option α} {a : α}
    (h : vetoGuard p s = some a) : p = some a :=
  (vetoGuard_eq_some.mp h).1

/-- The strict guard is the more conservative of the two: wherever it answers,
the veto guard answers the same thing. -/
theorem strictGuard_le_vetoGuard {p s : Option α} {a : α}
    (h : strictGuard p s = some a) : vetoGuard p s = some a := by
  obtain ⟨hp, hs⟩ := strictGuard_eq_some.mp h
  exact vetoGuard_eq_some.mpr ⟨hp, Or.inr hs⟩

/-! ## 3.  A wrong answer needs both readings to be wrong -/

/-- If the strict guard answers wrongly, both readings answered that same
wrong label. -/
theorem strictGuard_wrong_imp {p s : Option α} {a t : α}
    (h : strictGuard p s = some a) (hne : a ≠ t) :
    p = some a ∧ s = some a ∧ a ≠ t :=
  ⟨(strictGuard_eq_some.mp h).1, (strictGuard_eq_some.mp h).2, hne⟩

/-- If the veto guard answers wrongly, the primary answered wrongly and the
second reading did not contradict it. -/
theorem vetoGuard_wrong_imp {p s : Option α} {a t : α}
    (h : vetoGuard p s = some a) (hne : a ≠ t) :
    p = some a ∧ (s = none ∨ s = some a) ∧ a ≠ t :=
  ⟨(vetoGuard_eq_some.mp h).1, (vetoGuard_eq_some.mp h).2, hne⟩

/-- A second reading that is sound on a query — when it answers, it answers the
truth — makes the strict guard safe there. -/
theorem strictGuard_safe_of_sound {p s : Option α} {t : α}
    (hs : ∀ b, s = some b → b = t) {a : α} (h : strictGuard p s = some a) :
    a = t :=
  hs a (strictGuard_eq_some.mp h).2

/-- A second reading that is sound **and answers** makes the veto guard safe
there.  The extra hypothesis is exactly what the weaker contract costs: a
second reading that refuses lets the primary through. -/
theorem vetoGuard_safe_of_sound {p s : Option α} {t : α}
    (hs : ∀ b, s = some b → b = t) (hanswers : s ≠ none)
    {a : α} (h : vetoGuard p s = some a) : a = t := by
  rcases (vetoGuard_eq_some.mp h).2 with hnone | hsome
  · exact absurd hnone hanswers
  · exact hs a hsome

/-! ## 4.  The cost direction -/

/-- Every query the strict guard answers correctly is one the primary answered
correctly. -/
theorem strictGuard_correct_subset {p s : Option α} {t : α}
    (h : strictGuard p s = some t) : p = some t :=
  strictGuard_sound h

/-- Every query the veto guard answers correctly is one the primary answered
correctly. -/
theorem vetoGuard_correct_subset {p s : Option α} {t : α}
    (h : vetoGuard p s = some t) : p = some t :=
  vetoGuard_sound h

/-! ## 5.  Both columns of the score sheet move downwards -/

/-- A query: what the primary read, what the second reading read, and the
truth. -/
abbrev Row (α : Type*) := Option α × Option α × α

/-- How many queries a guard answers correctly. -/
def correctCount (g : Option α → Option α → Option α) (rows : List (Row α)) : Nat :=
  rows.countP (fun r => decide (g r.1 r.2.1 = some r.2.2))

/-- Whether an answer is a wrong answer: given, and not the truth. -/
def isWrong (a : Option α) (t : α) : Bool :=
  match a with
  | none => false
  | some b => !decide (b = t)

theorem isWrong_eq_true {a : Option α} {t : α} :
    isWrong a t = true ↔ ∃ b, a = some b ∧ b ≠ t := by
  cases a <;> simp [isWrong]

/-- How many queries a guard answers wrongly. -/
def wrongCount (g : Option α → Option α → Option α) (rows : List (Row α)) : Nat :=
  rows.countP (fun r => isWrong (g r.1 r.2.1) r.2.2)

/-- The unguarded reading, as a guard that ignores the second reading. -/
def bare (p : Option α) (_ : Option α) : Option α := p

theorem strict_correctCount_le (rows : List (Row α)) :
    correctCount (strictGuard (α := α)) rows ≤ correctCount (bare (α := α)) rows := by
  refine List.countP_mono_left ?_
  intro r _ hr
  simpa [bare] using decide_eq_true (strictGuard_sound (of_decide_eq_true hr))

theorem veto_correctCount_le (rows : List (Row α)) :
    correctCount (vetoGuard (α := α)) rows ≤ correctCount (bare (α := α)) rows := by
  refine List.countP_mono_left ?_
  intro r _ hr
  simpa [bare] using decide_eq_true (vetoGuard_sound (of_decide_eq_true hr))

theorem strict_wrongCount_le (rows : List (Row α)) :
    wrongCount (strictGuard (α := α)) rows ≤ wrongCount (bare (α := α)) rows := by
  refine List.countP_mono_left ?_
  intro r _ hr
  obtain ⟨a, ha, hne⟩ := isWrong_eq_true.mp hr
  exact isWrong_eq_true.mpr ⟨a, by simpa [bare] using strictGuard_sound ha, hne⟩

theorem veto_wrongCount_le (rows : List (Row α)) :
    wrongCount (vetoGuard (α := α)) rows ≤ wrongCount (bare (α := α)) rows := by
  refine List.countP_mono_left ?_
  intro r _ hr
  obtain ⟨a, ha, hne⟩ := isWrong_eq_true.mp hr
  exact isWrong_eq_true.mpr ⟨a, by simpa [bare] using vetoGuard_sound ha, hne⟩

/-- The strict guard's correct answers are a sub-multiset of the veto guard's:
guarding harder can only cost more. -/
theorem strict_correctCount_le_veto (rows : List (Row α)) :
    correctCount (strictGuard (α := α)) rows ≤ correctCount (vetoGuard (α := α)) rows := by
  refine List.countP_mono_left ?_
  intro r _ hr
  exact decide_eq_true (strictGuard_le_vetoGuard (of_decide_eq_true hr))

/-! ## 6.  The contract on a worked example

The four shapes a query can take, checked by the kernel: both readings agree
(both guards answer), they disagree (both refuse), the second reading refuses
(`strict` blocks, `veto` lets it through), and the primary refuses (neither
invents an answer). -/

example : strictGuard (some 3) (some 3) = some 3 := by decide
example : strictGuard (some 3) (some 4) = (none : Option ℕ) := by decide
example : strictGuard (some 3) none = (none : Option ℕ) := by decide
example : strictGuard none (some 3) = (none : Option ℕ) := by decide
example : vetoGuard (some 3) (some 3) = some 3 := by decide
example : vetoGuard (some 3) (some 4) = (none : Option ℕ) := by decide
example : vetoGuard (some 3) none = some 3 := by decide
example : vetoGuard none (some 3) = (none : Option ℕ) := by decide

/-- The failure the round is about, as a statement rather than a count: a wrong
answer `a` survives the strict guard **only if** the second reading
independently said `a` too.  No hypothesis about the primary or about the truth
is needed, which is the point — the block depends on the second reading alone. -/
theorem strict_blocks_unless_second_repeats {p s : Option α} {a : α}
    (hs : s ≠ some a) :
    strictGuard p s ≠ some a := by
  intro h
  exact hs (strictGuard_eq_some.mp h).2

end GLM.SecondReading
