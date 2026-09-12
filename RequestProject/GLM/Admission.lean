/-
# The door a new name comes in by

"Open vocabulary" stood on the untouched list for several rounds with a note
beside it saying it was *a commitment rather than an oversight*: the vocabulary
is exactly the registers, there is no coordinate for `justice`, and the
semantics layer refuses rather than inventing one.

That commitment is right, and it was never the whole story.  A commitment says
what the machine will not do; what was missing is the other half -- **how a
name gets in** -- and without it "open" was an adjective rather than a door.
`glm_universal/reasoning/admission.py` states the criterion:

> a name is admissible exactly when some **stated** route gives it coordinates
> that are **reproducibly computed** from a register the machine already
> checks, and are therefore **grounded** in a register rather than invented for
> the name.

This file is the part of that criterion which is not a measurement.  Three
things are modelled and each one is a way the door could be wrong.

**The door is a function.**  `route` tries the three admitting routes in a
fixed order and refuses last.  It has to be total (`route_mem`: a refusal is a
decision, not a crash), single-valued (`route_unique`, free because `route` is
a function, and stated because the ledger's counts rest on it) and genuinely
*ordered* (`route_eq_unit_iff` carries `d.held n = none`: a name a register
already holds is never taken by a computing route, even where the computing
route would also reach it).

**Grounding.**  `coordinates` produces something exactly when a route did, and
what it produces is what that route's register produced -- `coordinates_of_unit`
and `coordinates_of_arithmetic` say so, and `no_coordinates_of_refused` is the
clause that refuses.  Nothing in the file can manufacture a coordinate: there
is no constructor for one, only the three register functions.

**What a refusal is a refusal of.**  This is the point of the whole exercise.
`refusal_is_conditional` says that a refused name is admitted -- by the first
route, with the rest of the door unchanged -- the moment a register that
measures it is admitted.  So the claim being made about `justice` is "no
register reaches it", never "it is not the kind of thing that has coordinates".
`refused_mono` is the same fact from the other side: widening any register can
only take names off the refused list, never add one.  Together with
`held_unchanged_of_computed` -- admitting a name by computation writes nothing
back into a register -- these are the properties the Python's audit measures.

The last section is the round's ledger as arithmetic: 11 held, 5 by unit, 4 by
arithmetic and 7 refused over 27 probes, against a held vocabulary of 1093
names in nine registers.
-/
import Mathlib.Tactic

namespace GLM.Admission

/-! ## 1.  The four routes -/

/-- Which route admitted a name, or that none did.  `refused` is a verdict
like the others: the name is turned away *with a stated condition*, not
dropped. -/
inductive Route
  /-- The name is already a carrier in one of the nine registers. -/
  | held
  /-- The name parses as a unit expression, which the unit register
  dimensions exactly. -/
  | unit
  /-- The name is arithmetic over register names, which term arithmetic
  evaluates exactly. -/
  | arithmetic
  /-- No route reaches it. -/
  | refused
  deriving DecidableEq, Repr

/-- The three routes that let a name in. -/
def Route.admits : Route → Bool
  | .refused => false
  | _ => true

/-! ## 2.  The door

`Door` is the machine's registers as the door sees them: three partial
functions from a name to something a register computed.  There is deliberately
no fourth field -- the door cannot make a coordinate, it can only pass one on,
which is the `grounded` clause of the criterion expressed as a type.

`Register` is whatever names the register a held name lives in; `Coord` is
whatever the coordinates are (ten exact rational exponents, in the
implementation).  Neither is constrained here, because neither needs to be:
the properties below are properties of the routing and the grounding, not of
the arithmetic. -/
structure Door (Name Register Coord : Type*) where
  /-- The register a name is already a carrier in, if it is. -/
  held : Name → Option Register
  /-- The coordinates that register carries for it, when it dimensions its
  carriers at all -- an element, a chord and a word are held without being
  dimensioned. -/
  heldCoord : Name → Option Coord
  /-- The unit register's reading of the name, when it parses. -/
  unitParse : Name → Option Coord
  /-- Term arithmetic's evaluation of the name, when it is an expression over
  register names. -/
  arithmetic : Name → Option Coord

variable {Name Register Coord : Type*} (d : Door Name Register Coord)

/-- The routing: the three registers are asked in order, and a name none of
them reaches is refused. -/
def route (n : Name) : Route :=
  if (d.held n).isSome then .held
  else if (d.unitParse n).isSome then .unit
  else if (d.arithmetic n).isSome then .arithmetic
  else .refused

/-- The coordinates the door hands back, which are always some register's own.
There is no branch here that constructs a `Coord`. -/
def coordinates (n : Name) : Option Coord :=
  if (d.held n).isSome then d.heldCoord n
  else if (d.unitParse n).isSome then d.unitParse n
  else if (d.arithmetic n).isSome then d.arithmetic n
  else none

/-- A name is admissible when its route admits it. -/
def Admissible (n : Name) : Prop := (route d n).admits = true

/-! ## 3.  The door is total, single-valued and ordered -/

/-- Every name put to the door gets one of the four routes.  Nothing falls
through: a refusal is a decision. -/
theorem route_mem (n : Name) :
    route d n = .held ∨ route d n = .unit ∨
      route d n = .arithmetic ∨ route d n = .refused := by
  unfold route
  split_ifs <;> simp

/-- Exclusivity.  Free -- `route` is a function -- and stated because the
ledger's counts are a partition. -/
theorem route_unique {n : Name} {a b : Route}
    (ha : route d n = a) (hb : route d n = b) : a = b := by
  rw [← ha, ← hb]

/-- The register the machine already has takes absolute priority: a name it
holds is never admitted by a computing route, even where the computation would
also reach it.  `energy` is held; `energy divided by time` is not. -/
theorem route_eq_held_iff (n : Name) :
    route d n = .held ↔ (d.held n).isSome := by
  unfold route
  split_ifs with h <;> simp_all

/-- The unit route takes exactly the names no register holds and the unit
register reads.  The first conjunct is the priority, made explicit. -/
theorem route_eq_unit_iff (n : Name) :
    route d n = .unit ↔ (d.held n = none ∧ (d.unitParse n).isSome) := by
  unfold route
  split_ifs with h₁ h₂ <;> simp_all [Option.isSome_iff_exists,
    Option.eq_none_iff_forall_ne_some]

/-- Likewise for term arithmetic: it only ever sees what the two register
lookups did not decide. -/
theorem route_eq_arithmetic_iff (n : Name) :
    route d n = .arithmetic ↔
      (d.held n = none ∧ d.unitParse n = none ∧ (d.arithmetic n).isSome) := by
  unfold route
  split_ifs with h₁ h₂ h₃ <;>
    simp_all [Option.isSome_iff_exists, Option.eq_none_iff_forall_ne_some]

/-- A name is refused exactly when all three registers declined it -- so a
refusal certifies what was tried, which is what makes it informative. -/
theorem route_eq_refused_iff (n : Name) :
    route d n = .refused ↔
      (d.held n = none ∧ d.unitParse n = none ∧ d.arithmetic n = none) := by
  unfold route
  split_ifs with h₁ h₂ h₃ <;>
    simp_all [Option.isSome_iff_exists, Option.eq_none_iff_forall_ne_some]

/-- Admissibility is exactly reachability by one of the three stated routes.
This is the criterion's `stated` clause: there is no fourth way in. -/
theorem admissible_iff (n : Name) :
    Admissible d n ↔
      ((d.held n).isSome ∨ (d.unitParse n).isSome ∨ (d.arithmetic n).isSome) := by
  unfold Admissible route Route.admits
  split_ifs with h₁ h₂ h₃ <;> simp_all

/-! ## 4.  Grounding: the coordinates are a register's, or there are none -/

/-- A refused name is given no coordinates.  This is the clause that refuses,
and the one the implementation's audit calls
`no_coordinates_without_a_register`. -/
theorem no_coordinates_of_refused {n : Name} (h : route d n = .refused) :
    coordinates d n = none := by
  obtain ⟨h₁, h₂, h₃⟩ := (route_eq_refused_iff d n).mp h
  simp [coordinates, h₁, h₂, h₃]

/-- A name admitted by the unit route carries the unit register's own reading
-- not a copy, not a rounding, and not a number this file made up. -/
theorem coordinates_of_unit {n : Name} (h : route d n = .unit) :
    coordinates d n = d.unitParse n := by
  obtain ⟨h₁, h₂⟩ := (route_eq_unit_iff d n).mp h
  simp [coordinates, h₁, h₂]

/-- And one admitted by arithmetic carries term arithmetic's evaluation. -/
theorem coordinates_of_arithmetic {n : Name} (h : route d n = .arithmetic) :
    coordinates d n = d.arithmetic n := by
  obtain ⟨h₁, h₂, h₃⟩ := (route_eq_arithmetic_iff d n).mp h
  simp [coordinates, h₁, h₂, h₃]

/-- A held name carries its own register's coordinates, which may be absent:
a register that does not dimension its carriers admits without coordinates
rather than inventing them. -/
theorem coordinates_of_held {n : Name} (h : route d n = .held) :
    coordinates d n = d.heldCoord n := by
  have h₁ := (route_eq_held_iff d n).mp h
  simp [coordinates, h₁]

/-- Grounding, in one statement: every coordinate the door hands back is one
of the three registers' own values at that name. -/
theorem coordinates_grounded (n : Name) :
    coordinates d n = d.heldCoord n ∨ coordinates d n = d.unitParse n ∨
      coordinates d n = d.arithmetic n ∨ coordinates d n = none := by
  unfold coordinates
  split_ifs <;> simp

/-- The two computing routes always produce coordinates; only the held route
can let a name in without them. -/
theorem coordinates_isSome_of_computed {n : Name}
    (h : route d n = .unit ∨ route d n = .arithmetic) :
    (coordinates d n).isSome := by
  rcases h with h | h
  · rw [coordinates_of_unit d h]
    exact ((route_eq_unit_iff d n).mp h).2
  · rw [coordinates_of_arithmetic d h]
    exact ((route_eq_arithmetic_iff d n).mp h).2.2

/-- Determinacy.  The door is a function of the name and of the registers, so
asking twice gives the same route and the same coordinates.  Trivial as
mathematics, and it is exactly what the implementation's `determinate` check
measures, because there the door could have been stateful. -/
theorem determinate (n : Name) :
    route d n = route d n ∧ coordinates d n = coordinates d n :=
  ⟨rfl, rfl⟩

/-! ## 5.  Nothing is written back, and a refusal is conditional -/

/-- Admission by computation writes nothing into a register: a name admitted
by the unit or arithmetic route is *still not* a carrier afterwards.  The
vocabulary of held names is unchanged by having been widened, which is the
same discipline the element-coverage layer follows when it derives a cell and
writes nothing back. -/
theorem held_unchanged_of_computed {n : Name}
    (h : route d n = .unit ∨ route d n = .arithmetic) : d.held n = none := by
  rcases h with h | h
  · exact ((route_eq_unit_iff d n).mp h).1
  · exact ((route_eq_arithmetic_iff d n).mp h).1

/-- **What a refusal is a refusal of.**  Take a refused name `n`.  Admitting a
register that measures it -- that is, any door differing only in holding `n` --
admits it by the *first* route, and every other name is routed exactly as
before.  So the refusal is conditional and the condition is nameable, and
meeting it costs nothing elsewhere; the refusal is never a claim that `n` is
the wrong kind of word.

The statement needs no hypothesis that `n` was refused, which is the strongest
form of the point: whatever the door said about `n` before, a register that
holds it settles the matter. -/
theorem refusal_is_conditional [DecidableEq Name] (n : Name)
    (r : Register) (c : Option Coord) :
    route { d with held := fun m => if m = n then some r else d.held m,
                   heldCoord := fun m => if m = n then c else d.heldCoord m }
        n = .held ∧
      ∀ m : Name, m ≠ n →
        route { d with held := fun m => if m = n then some r else d.held m,
                       heldCoord := fun m => if m = n then c else d.heldCoord m }
            m = route d m := by
  refine ⟨by simp [route], fun m hm => ?_⟩
  simp [route, hm]

/-- The door does not have to change for that to happen: the same statement
with the routes left alone says the mechanism is in the registers, not in the
criterion. -/
theorem refusal_condition_is_a_register [DecidableEq Name] {n : Name}
    (r : Register) :
    ∀ heldCoord unitParse arithmetic : Name → Option Coord,
      route { held := fun m => if m = n then some r else none,
              heldCoord := heldCoord, unitParse := unitParse,
              arithmetic := arithmetic } n = .held := by
  intro _ _ _
  simp [route]

/-- Widening a register can only take names off the refused list.  If every
register of `d` is weaker than the corresponding register of `d'`, then a name
`d'` refuses was already refused by `d`. -/
theorem refused_mono {d' : Door Name Register Coord} {n : Name}
    (hh : ∀ m : Name, (d.held m).isSome → (d'.held m).isSome)
    (hu : ∀ m : Name, (d.unitParse m).isSome → (d'.unitParse m).isSome)
    (ha : ∀ m : Name, (d.arithmetic m).isSome → (d'.arithmetic m).isSome)
    (h : route d' n = .refused) : route d n = .refused := by
  obtain ⟨h₁, h₂, h₃⟩ := (route_eq_refused_iff d' n).mp h
  rw [route_eq_refused_iff]
  refine ⟨?_, ?_, ?_⟩
  · by_contra hne
    exact absurd (hh n (Option.isSome_iff_ne_none.mpr hne)) (by simp [h₁])
  · by_contra hne
    exact absurd (hu n (Option.isSome_iff_ne_none.mpr hne)) (by simp [h₂])
  · by_contra hne
    exact absurd (ha n (Option.isSome_iff_ne_none.mpr hne)) (by simp [h₃])

/-- The same fact stated as the reader would want it: admitting a register
never turns an admitted name away. -/
theorem admissible_mono {d' : Door Name Register Coord} {n : Name}
    (hh : ∀ m : Name, (d.held m).isSome → (d'.held m).isSome)
    (hu : ∀ m : Name, (d.unitParse m).isSome → (d'.unitParse m).isSome)
    (ha : ∀ m : Name, (d.arithmetic m).isSome → (d'.arithmetic m).isSome)
    (h : Admissible d n) : Admissible d' n := by
  rw [admissible_iff] at h ⊢
  rcases h with h | h | h
  · exact Or.inl (hh n h)
  · exact Or.inr (Or.inl (hu n h))
  · exact Or.inr (Or.inr (ha n h))

/-! ## 6.  The ledger of the round

The counts are measured by `admission.admission_report`; what is checked here
is that they are a partition of the probes, and that the nine registers'
carriers add up to the held vocabulary the door reports. -/

/-- The four routes account for every probe put to the door. -/
theorem ledger_routes_every_probe : 11 + 5 + 4 + 7 = 27 := by norm_num

/-- Twenty of the twenty-seven are admitted, nine of them by a route that
computes rather than looks up. -/
theorem ledger_admitted : 11 + 5 + 4 = 20 := by norm_num

/-- Of the seven refusals, one is a gap in a register rather than in the door:
`km/h` is refused because the unit register is SI-coherent and does not hold
the hour, and the other six are the standing ungrounded words. -/
theorem ledger_refusals : 1 + 6 = 7 := by norm_num

/-- The held vocabulary, register by register: physics, chemistry, molecules,
mathematics, harmonics, economics, the comparison classes, the lexicon, the
semantic lexicon and the conjugate register. -/
theorem ledger_vocabulary :
    726 + 118 + 51 + 22 + 28 + 21 + 45 + 9 + 68 + 5 = 1093 := by norm_num

end GLM.Admission
