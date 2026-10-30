/-
# The conditional lobe of the ARC generation: sound, incomplete, and a tie-break

**Retrieved from the archive.**  `source_material/GLM-main.zip/arc_agi_15`
carries `conditional_lobe.py`, the part of that generation that *induces a rule*
rather than searching for a program: it looks at every object of every training
pair, records whether the object changed or was preserved, and then asks which
condition separates the two groups.  It tries them in a fixed order — a size
threshold first, then a colour match, then a shape test — and returns the first
that fits.

`SearchLoop.lean` retrieved the archive's *search* discipline (the hard gate,
Occam, and what the gate leaves undetermined).  This file retrieves its
*induction* discipline, and measures it, because the two failure modes it has
are exactly the ones a loop-reasoning system has to know about.

## The model

An object is described by the three features the lobe actually branches on —
its colour, whether it is big, whether it is linear — so a description is a
`Desc = Bool × Bool × Bool` and there are eight of them.  An **observation**
`Obs = Desc → Option Bool` records, for each description, whether objects of
that description were seen to change (`some true`), were seen to be preserved
(`some false`), or were not seen at all (`none`); there are `3⁸ = 6561` of
them.  The conditions the lobe can express are the six of `Cond`, and `induce`
is its procedure, transcribed: no changed objects → give up; nothing preserved
→ `always`; else the size test, then the two colour tests, then the two shape
tests, then give up.

## What is proved

**Soundness** (`induce_sound`, `induce_mem_survivors`).  Whenever the lobe
returns a rule, that rule really does reproduce every observation it was given.
This is the property the archive's own ledger insists on, and it holds.

**Blindness** (`survivors_agree_on_observed`).  Any two rules that survive the
observations agree on every *observed* description — so nothing computed from
the training data can separate them.  This is the induction-side twin of
`SearchLoop.gate_blind`.

**Incompleteness** (`induce_incomplete`, `census_missed`).  In `56` of the
`6561` observations the lobe returns nothing although a rule *in its own
family* separates the data: the fixed order is not a search.  The witness
`missedObs` is one of them — nothing is seen to change, so the lobe gives up at
its first line, while `colourFalse` fits the data perfectly.

**The order is a tie-break** (`census_survivors`, `census_ambiguous`,
`census_committed`, `twoSurvivorObs_ambiguous`).  Over the `6561` observations
the number of surviving rules is `0` for `5193`, `1` for `1232`, `2` for `111`,
`3` for `20`, `4` for `4`, and all `6` for the empty observation — never
exactly `5`.  In `136` observations two survivors genuinely disagree somewhere,
and in `119` of those the lobe answers anyway: its answer is one of several
rules the data cannot choose between, and a different survivor predicts a
different outcome on an object that was never observed.  Nothing marks that
answer as a guess.

**The consequence for the system.**  A loop-reasoning runtime must carry the
*set* of surviving rules and report the disagreement, not the first rule an
ordered list happens to reach — which is what `SearchLoop.occam_unique` says
from the search side and what the census here measures from the induction side.
-/
import Mathlib

namespace GLM.ConditionalInduction

/-! ## 1. Objects, conditions, observations -/

/-- An object description: its colour, whether it is big, whether it is linear.
These are the three features the archive's lobe branches on. -/
abbrev Desc := Bool × Bool × Bool

def colourOf (d : Desc) : Bool := d.1
def bigOf (d : Desc) : Bool := d.2.1
def linearOf (d : Desc) : Bool := d.2.2

/-- The conditions the lobe can express: unconditional, a size threshold, a
colour match either way, and a shape test either way. -/
inductive Cond
  | always | bigOnly | colourFalse | colourTrue | linearOnly | nonlinearOnly
  deriving DecidableEq, Repr, Fintype

/-- What a condition predicts for an object: `true` = "this object changes". -/
def eval : Cond → Desc → Bool
  | .always, _ => true
  | .bigOnly, d => bigOf d
  | .colourFalse, d => !colourOf d
  | .colourTrue, d => colourOf d
  | .linearOnly, d => linearOf d
  | .nonlinearOnly, d => !linearOf d

/-- An observation: for each description, changed, preserved, or unseen. -/
abbrev Obs := Desc → Option Bool

/-- The eight descriptions. -/
def descList : List Desc :=
  [(false, false, false), (false, false, true), (false, true, false), (false, true, true),
   (true, false, false), (true, false, true), (true, true, false), (true, true, true)]

theorem mem_descList (d : Desc) : d ∈ descList := by
  revert d; decide

/-- The six conditions, in the order the lobe tries them. -/
def condList : List Cond :=
  [.always, .bigOnly, .colourFalse, .colourTrue, .linearOnly, .nonlinearOnly]

/-! ## 2. The gate: which rules survive the observations -/

/-- A condition *separates* an observation when it reproduces every observed
fate. -/
def separatesB (c : Cond) (o : Obs) : Bool :=
  descList.all fun d => match o d with | none => true | some b => eval c d == b

theorem separatesB_iff {c : Cond} {o : Obs} :
    separatesB c o = true ↔ ∀ d b, o d = some b → eval c d = b := by
  constructor
  · intro h d b hd
    have hall := List.all_eq_true.mp h d (mem_descList d)
    rw [hd] at hall
    simpa using hall
  · intro h
    refine List.all_eq_true.mpr fun d _ => ?_
    cases hd : o d with
    | none => rfl
    | some b => simpa using h d b hd

/-- The rules that survive the observations. -/
def survivors (o : Obs) : List Cond := condList.filter (separatesB · o)

theorem mem_condList (c : Cond) : c ∈ condList := by
  revert c; decide

theorem mem_survivors {c : Cond} {o : Obs} :
    c ∈ survivors o ↔ separatesB c o = true := by
  rw [survivors, List.mem_filter]
  constructor
  · rintro ⟨-, h⟩; simpa using h
  · intro h
    exact ⟨mem_condList c, by simpa using h⟩

/-- **The gate is blind to its own residue.**  Two surviving rules agree on
every observed description, so no quantity computed from the training data can
separate them. -/
theorem survivors_agree_on_observed {o : Obs} {c₁ c₂ : Cond} {d : Desc} {b : Bool}
    (h₁ : c₁ ∈ survivors o) (h₂ : c₂ ∈ survivors o) (hd : o d = some b) :
    eval c₁ d = eval c₂ d := by
  rw [mem_survivors, separatesB_iff] at h₁ h₂
  rw [h₁ d b hd, h₂ d b hd]

/-! ## 3. The lobe's procedure -/

def changedList (o : Obs) : List Desc := descList.filter fun d => o d == some true
def preservedList (o : Obs) : List Desc := descList.filter fun d => o d == some false

/-- `conditional_lobe.py`, transcribed: give up if nothing changed; return
`always` if nothing was preserved; then the size test, then the two colour
tests, then the two shape tests; then give up. -/
def induce (o : Obs) : Option Cond :=
  let ch := changedList o
  let pr := preservedList o
  if ch.isEmpty then none
  else if pr.isEmpty then some .always
  else if (ch.all bigOf) && (pr.all fun d => !bigOf d) then some .bigOnly
  else if (ch.all fun d => !colourOf d) && (pr.all colourOf) then some .colourFalse
  else if (ch.all colourOf) && (pr.all fun d => !colourOf d) then some .colourTrue
  else if (ch.all linearOf) && (pr.all fun d => !linearOf d) then some .linearOnly
  else if (ch.all fun d => !linearOf d) && (pr.all linearOf) then some .nonlinearOnly
  else none

/-- **Soundness.**  Whenever the lobe answers, its answer reproduces every
observation it was given. -/
theorem induce_sound : ∀ (o : Obs) (c : Cond), induce o = some c → separatesB c o = true := by
  native_decide

theorem induce_mem_survivors {o : Obs} {c : Cond} (h : induce o = some c) :
    c ∈ survivors o :=
  mem_survivors.mpr (induce_sound o c h)

/-! ## 4. Incompleteness -/

/-- An observation on which nothing is seen to change, so the lobe gives up at
its first line — while the rule "the objects of colour `false` change" fits the
data exactly. -/
def missedObs : Obs := fun d => if colourOf d then some false else none

/-- **The fixed order is not a search.**  The lobe returns nothing although a
rule in its own family separates the observation. -/
theorem induce_incomplete :
    induce missedObs = none ∧ Cond.colourFalse ∈ survivors missedObs := by
  constructor
  · native_decide
  · native_decide

/-- Over all `6561` observations, the lobe gives up on `56` that a rule of its
own family separates. -/
theorem census_missed :
    ((Finset.univ : Finset Obs).filter fun o => induce o = none ∧ survivors o ≠ []).card = 56 := by
  native_decide

/-! ## 5. The census: how much the data leaves undetermined -/

/-- Two surviving rules disagree somewhere. -/
def ambiguousB (o : Obs) : Bool :=
  (survivors o).any fun c₁ =>
    (survivors o).any fun c₂ => descList.any fun d => eval c₁ d != eval c₂ d

/-- **How many rules survive.**  Over the `6561` observations: none for `5193`,
one for `1232`, two for `111`, three for `20`, four for `4`, exactly five for
none at all, and all six for the empty observation. -/
theorem census_survivors :
    [0, 1, 2, 3, 4, 5, 6].map
        (fun k => ((Finset.univ : Finset Obs).filter fun o => (survivors o).length = k).card)
      = [5193, 1232, 111, 20, 4, 0, 1] := by
  native_decide

/-- In `136` observations the survivors genuinely disagree. -/
theorem census_ambiguous :
    ((Finset.univ : Finset Obs).filter fun o => ambiguousB o = true).card = 136 := by
  native_decide

/-- **And in `119` of them the lobe answers anyway**: its answer is one of
several rules the data cannot choose between, and nothing marks it as a
guess. -/
theorem census_committed :
    ((Finset.univ : Finset Obs).filter fun o => ambiguousB o = true ∧ induce o ≠ none).card
      = 119 := by
  native_decide

/-- A concrete instance: one big linear object of colour `true` changed, one
small non-linear object of colour `false` was preserved.  Both "the big objects
change" and "the linear objects change" fit — and they disagree about a big
non-linear object, which was never observed. -/
def twoSurvivorObs : Obs := fun d =>
  if d = (true, true, true) then some true
  else if d = (false, false, false) then some false
  else none

theorem twoSurvivorObs_ambiguous :
    Cond.bigOnly ∈ survivors twoSurvivorObs ∧
    Cond.linearOnly ∈ survivors twoSurvivorObs ∧
    eval Cond.bigOnly (true, true, false) ≠ eval Cond.linearOnly (true, true, false) ∧
    twoSurvivorObs (true, true, false) = none := by
  refine ⟨?_, ?_, ?_, ?_⟩ <;> native_decide

/-- The lobe answers `bigOnly` there, because the size test comes first: the
answer is the order of the tests, not a consequence of the data. -/
theorem twoSurvivorObs_induce : induce twoSurvivorObs = some Cond.bigOnly := by
  native_decide

end GLM.ConditionalInduction
