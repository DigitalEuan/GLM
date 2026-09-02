/-
# Deciding what a name denotes, and what a decision may change

`MeasureView.lean` reads a measure word as a measurement.  Beside that
reading, `glm_universal/reasoning/measure_view.py` repairs the lexicon's
`related_to` triples wherever the physics register can decide them: 27 of the
66 convert, and 39 do not.  Thirty-eight of the 39 are declined for one
reason -- an endpoint *reaches no dimension the register holds* -- and that
sentence records a failed lookup rather than a fact about the word.  It cannot
tell a name the register merely spells differently from a name that denotes no
magnitude at all.

`glm_universal/data_objects/denotation.py` settles the difference by hand: one
verdict per name, each with its written reason, and only one of the six
verdicts -- `quantity` -- makes a name dimensional, by naming an entry the
physics register already holds.  This file is the part of that arrangement
which is not a measurement: what a vocabulary decision *can* and *cannot* do
to the repair.

* `Vocabulary` is the arrangement in the abstract: what the register
  dimensions on its own (`base`), what has been decided about the rest
  (`verdict`), what a quantity name's dimension is (`dimOf`), and which basis
  quantities carry one dimension to another (`factors`).
* `reach` is the lookup with the decisions in hand, `firstPass` the
  classification of a triple without them and `secondPass` the one with them.

What is proved:

* `reach_invents_nothing` -- a decided name reaches a dimension only by
  naming an entry the register already holds, so a denotation can no more
  extend the register than an alias can;
* `secondPass_eq_firstPass_of_decided` -- the second pass never *revises* the
  first.  Where the register could already decide a triple, the decision is
  the one it made, whatever the vocabulary says;
* `secondPass_eq_firstPass_of_no_quantity_verdict` -- and where no name is
  decided to *be* a quantity, the second pass converts nothing new.  Deciding
  what words denote is not a way of manufacturing relations, which is the
  content of the measured `converted = 0`;
* `undecided_is_decided` -- the closure claim.  Once every endpoint carries a
  verdict, a triple left unclassified is one whose endpoint was decided not to
  be a quantity: no triple waits on a lookup any longer;
* `repaired_not_converted` -- the one extra repair rule (a process beside a
  quantity) applies only where the dimensional rules declined, so the three
  outcomes partition the residue.

The last section instantiates all of it on the three cases the measurement
turns on: *gravity*, decided to be the register's `gravitational_field` and
still declined against *mass* for want of a factor; *motion*, decided to be
ambiguous and therefore left alone; and *move*, a process beside a velocity,
which is repaired.
-/
import Mathlib.Tactic

namespace GLM.Info

/-! ## The six verdicts -/

/-- What a name that the physics register does not dimension may be decided to
denote.  Only `quantity` reaches a dimension, and it reaches one the register
already holds rather than supplying a new one. -/
inductive Verdict where
  /-- an entry of the physics register, under an ordinary-language name -/
  | quantity (name : String)
  /-- several registered quantities, with nothing in the word to choose -/
  | ambiguous
  /-- the dimension of whatever the word is applied to -/
  | polymorphic
  /-- a thing that bears quantities -/
  | carrier
  /-- something that happens -/
  | process
  /-- no magnitude at all -/
  | abstraction
  deriving DecidableEq, Repr

/-- Whether a verdict makes its name dimensional. -/
def Verdict.isQuantity : Verdict → Bool
  | .quantity _ => true
  | _ => false

/-! ## The arrangement -/

/-- The registers a repair runs against.

`base` is what the physics register and its aliases reach on their own,
`verdict` the decided vocabulary, `dimOf` a quantity name's dimension, and
`factors a b` the basis quantities that carry `a` to `b` -- a singleton is an
attribution, and anything longer is an ambiguity the repair refuses. -/
structure Vocabulary (Dim : Type) where
  base : String → Option Dim
  verdict : String → Option Verdict
  dimOf : String → Option Dim
  factors : Dim → Dim → List String

variable {Dim : Type}

namespace Vocabulary

/-- The dimension a decision reaches: only a `quantity` verdict reaches one,
and only through the register's own entry for the quantity it names. -/
def denoted (V : Vocabulary Dim) (n : String) : Option Dim :=
  match V.verdict n with
  | some (.quantity q) => V.dimOf q
  | _ => none

/-- The lookup with the decisions in hand.  The register keeps precedence: a
name it already dimensions is never re-decided. -/
def reach (V : Vocabulary Dim) (n : String) : Option Dim :=
  match V.base n with
  | some d => some d
  | none => V.denoted n

@[simp] theorem reach_of_base {V : Vocabulary Dim} {n : String} {d : Dim}
    (h : V.base n = some d) : V.reach n = some d := by
  simp [reach, h]

theorem reach_eq_base_of_undenoted {V : Vocabulary Dim} {n : String}
    (h : V.denoted n = none) : V.reach n = V.base n := by
  unfold reach
  cases hb : V.base n with
  | none => simpa using h
  | some _ => rfl

theorem denoted_eq_none_of_not_quantity {V : Vocabulary Dim} {n : String}
    (h : ∀ q, V.verdict n ≠ some (.quantity q)) : V.denoted n = none := by
  unfold denoted
  cases hv : V.verdict n with
  | none => rfl
  | some v =>
      cases v with
      | quantity q => exact absurd hv (h q)
      | _ => rfl

/-- **A decision invents nothing.**  Whatever a decided name reaches, it
reaches because the physics register holds it: either directly, or as the
dimension of the quantity the verdict names. -/
theorem reach_invents_nothing {V : Vocabulary Dim} {n : String} {d : Dim}
    (h : V.reach n = some d) :
    V.base n = some d ∨ ∃ q, V.verdict n = some (.quantity q) ∧
      V.dimOf q = some d := by
  unfold reach at h
  cases hb : V.base n with
  | some e => rw [hb] at h; exact Or.inl (by simpa using h)
  | none =>
      rw [hb] at h
      refine Or.inr ?_
      unfold denoted at h
      cases hv : V.verdict n with
      | none => rw [hv] at h; exact absurd h (by simp)
      | some v =>
          cases v with
          | quantity q =>
              rw [hv] at h
              exact ⟨q, by simp, by simpa using h⟩
          | _ => rw [hv] at h; exact absurd h (by simp)

/-! ## Classifying a triple -/

/-- What the repair decides about one `related_to` triple. -/
inductive Outcome where
  /-- the endpoints reach the same dimension -/
  | same
  /-- exactly one basis quantity carries one dimension to the other -/
  | differsBy (factor : String)
  /-- more than one does, so the attribution would be a guess -/
  | ambiguousFactor
  /-- none does -/
  | noFactor
  /-- an endpoint reaches no dimension at all -/
  | undecided
  deriving DecidableEq, Repr

variable [DecidableEq Dim]

/-- The repair's two rules, run against a given lookup. -/
def classifyWith (V : Vocabulary Dim) (look : String → Option Dim)
    (s o : String) : Outcome :=
  match look s, look o with
  | some a, some b =>
      if a = b then .same
      else
        match V.factors a b with
        | [f] => .differsBy f
        | [] => .noFactor
        | _ => .ambiguousFactor
  | _, _ => .undecided

/-- The repair as `relation_repair` runs it: the register alone. -/
def firstPass (V : Vocabulary Dim) (s o : String) : Outcome :=
  V.classifyWith V.base s o

/-- The repair with the decided vocabulary in hand. -/
def secondPass (V : Vocabulary Dim) (s o : String) : Outcome :=
  V.classifyWith V.reach s o

theorem classifyWith_undecided_iff {V : Vocabulary Dim}
    {look : String → Option Dim} {s o : String} :
    V.classifyWith look s o = .undecided ↔ look s = none ∨ look o = none := by
  unfold classifyWith
  cases hs : look s with
  | none => simp
  | some a =>
      cases ho : look o with
      | none => simp
      | some b =>
          simp only [or_false, reduceCtorEq, iff_false]
          by_cases hab : a = b
          · simp [hab]
          · simp only [hab, if_false]
            cases V.factors a b with
            | nil => simp
            | cons f rest =>
                cases rest with
                | nil => simp
                | cons _ _ => simp

/-- **The second pass never revises the first.**  Where the register could
decide a triple on its own, the vocabulary changes nothing about it -- not the
predicate, and not the factor. -/
theorem secondPass_eq_firstPass_of_decided {V : Vocabulary Dim} {s o : String}
    (h : V.firstPass s o ≠ .undecided) :
    V.secondPass s o = V.firstPass s o := by
  have hs : V.base s ≠ none := by
    intro hc; exact h (classifyWith_undecided_iff.mpr (Or.inl hc))
  have ho : V.base o ≠ none := by
    intro hc; exact h (classifyWith_undecided_iff.mpr (Or.inr hc))
  obtain ⟨a, ha⟩ := Option.ne_none_iff_exists'.mp hs
  obtain ⟨b, hb⟩ := Option.ne_none_iff_exists'.mp ho
  unfold secondPass firstPass classifyWith
  rw [ha, hb, reach_of_base ha, reach_of_base hb]

/-- **A vocabulary that dimensions nothing converts nothing.**  If no name is
decided to *be* a quantity, the second pass is the first, triple by triple.
Deciding what words denote is not a way of manufacturing relations. -/
theorem secondPass_eq_firstPass_of_no_quantity_verdict {V : Vocabulary Dim}
    (h : ∀ n q, V.verdict n ≠ some (.quantity q)) (s o : String) :
    V.secondPass s o = V.firstPass s o := by
  have hreach : ∀ n, V.reach n = V.base n := fun n =>
    reach_eq_base_of_undenoted (denoted_eq_none_of_not_quantity (h n))
  unfold secondPass firstPass classifyWith
  rw [hreach s, hreach o]

/-- **The closure claim.**  Once every endpoint carries a verdict -- and every
`quantity` verdict names an entry the register holds, which is what the
register's audit requires -- a triple the second pass leaves unclassified has
an endpoint that was *decided* not to be a quantity.  Nothing is waiting on a
lookup. -/
theorem undecided_is_decided {V : Vocabulary Dim} {s o : String}
    (hs : (V.verdict s).isSome ∨ (V.base s).isSome)
    (ho : (V.verdict o).isSome ∨ (V.base o).isSome)
    (hauditS : ∀ q, V.verdict s = some (.quantity q) → (V.dimOf q).isSome)
    (hauditO : ∀ q, V.verdict o = some (.quantity q) → (V.dimOf q).isSome)
    (h : V.secondPass s o = .undecided) :
    (∃ v, V.verdict s = some v ∧ v.isQuantity = false) ∨
      ∃ v, V.verdict o = some v ∧ v.isQuantity = false := by
  have key : ∀ n, ((V.verdict n).isSome ∨ (V.base n).isSome) →
      (∀ q, V.verdict n = some (.quantity q) → (V.dimOf q).isSome) →
      V.reach n = none → ∃ v, V.verdict n = some v ∧ v.isQuantity = false := by
    intro n hn haudit hreach
    have hbase : V.base n = none := by
      unfold reach at hreach
      cases hb : V.base n with
      | none => rfl
      | some d => rw [hb] at hreach; exact absurd hreach (by simp)
    have hverdict : (V.verdict n).isSome := by
      rcases hn with hv | hb
      · exact hv
      · rw [hbase] at hb; exact absurd hb (by simp)
    obtain ⟨v, hv⟩ := Option.isSome_iff_exists.mp hverdict
    refine ⟨v, hv, ?_⟩
    cases v with
    | quantity q =>
        exfalso
        obtain ⟨d, hd⟩ := Option.isSome_iff_exists.mp (haudit q hv)
        have : V.reach n = some d := by
          simp [reach, denoted, hbase, hv, hd]
        rw [this] at hreach
        exact absurd hreach (by simp)
    | _ => rfl
  rcases classifyWith_undecided_iff.mp h with hr | hr
  · exact Or.inl (key s hs hauditS hr)
  · exact Or.inr (key o ho hauditO hr)

/-! ## The one extra repair rule -/

/-- A triple where one endpoint is a process the register cannot dimension and
the other reaches a dimension: the triple links something that happens to a
quantity that quantifies it.  This is the only repair the verdicts license
beyond the two dimensional rules -- a *carrier* beside a quantity has the same
shape and is deliberately left alone, because a magnet bears a flux density
and a photon bears no illuminance, and a rule that is right half the time is a
guess. -/
def processRepair (V : Vocabulary Dim) (s o : String) : Prop :=
  (V.reach s = none ∧ V.verdict s = some .process ∧ (V.reach o).isSome) ∨
    (V.reach o = none ∧ V.verdict o = some .process ∧ (V.reach s).isSome)

/-- A triple the repair converts. -/
def converted (V : Vocabulary Dim) (s o : String) : Prop :=
  V.secondPass s o = .same ∨ ∃ f, V.secondPass s o = .differsBy f

/-- **The repair rule never overwrites a conversion.**  It applies only where
the dimensional rules found nothing to say, so converting, repairing and
declining partition the residue. -/
theorem repaired_not_converted {V : Vocabulary Dim} {s o : String}
    (h : V.processRepair s o) : ¬ V.converted s o := by
  have hund : V.secondPass s o = .undecided := by
    rcases h with ⟨hs, _, _⟩ | ⟨ho, _, _⟩
    · exact classifyWith_undecided_iff.mpr (Or.inl hs)
    · exact classifyWith_undecided_iff.mpr (Or.inr ho)
  rintro (hc | ⟨f, hc⟩) <;> rw [hund] at hc <;> exact absurd hc (by simp)

end Vocabulary

/-! ## The three cases the measurement turns on

A dimension here is a triple of exponents -- mass, length, time -- which is
enough to carry the example.  The vocabulary holds the three decisions the
Python register makes about *gravity*, *motion* and *move*, and the factor
basis is the handful of quantities the example needs. -/

namespace DenotationExample

/-- Mass, length and time exponents. -/
abbrev ExDim := ℤ × ℤ × ℤ

/-- The quantities the example's register holds. -/
def dimOf : String → Option ExDim
  | "mass" => some (1, 0, 0)
  | "length" => some (0, 1, 0)
  | "time" => some (0, 0, 1)
  | "velocity" => some (0, 1, -1)
  | "acceleration" => some (0, 1, -2)
  | "force" => some (1, 1, -2)
  | "gravitational_field" => some (0, 1, -2)
  | _ => none

/-- The physics register on its own: it holds the quantities and nothing that
is not one. -/
def base (n : String) : Option ExDim :=
  match n with
  | "gravity" => none
  | "motion" => none
  | "move" => none
  | _ => dimOf n

/-- The three decisions, exactly as `data_objects/denotation.py` records
them. -/
def verdict : String → Option Verdict
  | "gravity" => some (.quantity "gravitational_field")
  | "motion" => some .ambiguous
  | "move" => some .process
  | _ => none

/-- A single basis quantity carrying `a` to `b`, in either direction. -/
def factors (a b : ExDim) : List String :=
  (["mass", "length", "time", "velocity", "acceleration", "force"].filter
    fun q =>
      match dimOf q with
      | some d => decide (a + d = b) || decide (a - d = b)
      | none => false)

/-- The example arrangement. -/
def V : Vocabulary ExDim := ⟨base, verdict, dimOf, factors⟩

/-- *gravity* reaches nothing on its own. -/
example : V.base "gravity" = none := rfl

/-- The decision gives it the register's own `gravitational_field`, and
supplies no coordinate of its own. -/
theorem gravity_reaches_the_register :
    V.reach "gravity" = V.dimOf "gravitational_field" := rfl

/-- `gravity related_to mass` was declined because *gravity* reached no
dimension.  Now it reaches one -- and the triple is still declined, because no
single basis quantity carries a field to a mass.  The decision changed the
reason and not the answer, which is what the measurement reports. -/
theorem gravity_mass_first_pass : V.firstPass "gravity" "mass" = .undecided :=
  rfl

theorem gravity_mass_second_pass : V.secondPass "gravity" "mass" = .noFactor :=
  rfl

/-- *motion* was decided to be ambiguous between three registered quantities,
so it reaches nothing and its triple stays unclassified -- by decision. -/
theorem motion_velocity_undecided :
    V.secondPass "motion" "velocity" = .undecided := rfl

theorem motion_is_decided_not_missing :
    (∃ v, V.verdict "motion" = some v ∧ v.isQuantity = false) ∨
      ∃ v, V.verdict "velocity" = some v ∧ v.isQuantity = false :=
  Vocabulary.undecided_is_decided (by decide) (by decide)
    (by intro q hq; simp [V, verdict] at hq)
    (by intro q hq; simp [V, verdict] at hq)
    motion_velocity_undecided

/-- *move* is a process beside a velocity: the one triple shape the verdicts
repair. -/
theorem move_velocity_repaired : V.processRepair "move" "velocity" :=
  Or.inl ⟨rfl, rfl, rfl⟩

/-- And the repair does not overwrite a conversion. -/
theorem move_velocity_not_converted : ¬ V.converted "move" "velocity" :=
  Vocabulary.repaired_not_converted move_velocity_repaired

/-- A triple the register could already decide is untouched by all of this:
*force* and *mass* differ by exactly one basis quantity, before the decisions
and after them. -/
theorem force_mass_unchanged :
    V.secondPass "force" "mass" = V.firstPass "force" "mass" :=
  Vocabulary.secondPass_eq_firstPass_of_decided (by decide)

end DenotationExample

end GLM.Info
