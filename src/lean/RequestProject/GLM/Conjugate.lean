/-
# Transporting a relation across registers, and when that is allowed

`heat : temperature :: force : ?` stood open for several rounds, and the two
halves of the reason were different in kind.  The lexicon relates `heat` and
`temperature` only by `temperature drives heat` and by `related_to`, neither of
which reaches anything from `force`; and the three terms share no register that
dimensions them, since `heat` is a word and `temperature` and `force` are
physics quantities.

`glm_universal/data_objects/conjugate_pairs.py` supplies a register whose rows
run *across* the domains -- an effort, an extent, and the transfer they make,
`heat = temperature x entropy`, `work = force x length` -- and
`glm_universal/reasoning/conjugate.py` transports a relation along it.  This
file is the part of that arrangement which is not a table lookup: **what makes
a relation transportable, and what follows from it.**

* `Row` is one energy domain and `Role` its three columns; `Register` is a list
  of rows and `RolesUnique` the register's own discipline -- no name occupies
  two columns.
* `Rel R src tgt` is the relation a pair of columns names: `effort_of` is
  `Rel R Role.effort Role.transfer`.
* `forward` and `reverse` are the two ways of using it, and `Answer` is what a
  question may be answered with.

What is proved:

* `rel_functional` and `rel_injective` -- on a register with unique roles a
  named relation is single-valued in *both* directions, which is the
  admissibility criterion the transport rests on: the answer is derived, not
  chosen;
* `forward_spec`, `reverse_spec` -- the computed answer really does stand in
  the relation, in the direction claimed;
* `forward_unique`, `reverse_unique` -- and it is the only name that does;
* `no_answer_of_unplaced` -- when `C` occupies neither column, *no* name stands
  in the relation to it, so a refusal is forced by the register rather than
  chosen by the code.  This is the theorem behind `heat : temperature ::
  entropy : ?` and behind the open-vocabulary boundary, `justice`;
* `not_unique_of_two_values` -- and the negative half: a relation that reaches
  two different names from one term determines no answer at all.  That is
  exactly the shape of `related_to`, which is why it is refused by name rather
  than followed to a guess.

The last section is the concrete table.  Its seven rows are checked by
`decide`, in integer arithmetic on the register's own EXT10 exponents:
`dimensionally_sound` is the statement that an effort times its extent is an
energy, and `answer_heat_temperature_force` is the question this round was
about, answered `work`.
-/
import Mathlib.Tactic

namespace GLM.Conjugate

/-! ## 1.  Rows, roles and registers -/

/-- One energy domain: the intensive effort, the extensive extent it acts
through, and the transfer of energy they make together. -/
structure Row (N : Type) where
  /-- The name of the energy domain, e.g. `thermal`. -/
  domain : N
  /-- The intensive potential, e.g. `temperature`. -/
  effort : N
  /-- The extensive quantity it acts through, e.g. `entropy`. -/
  extent : N
  /-- The energy moved when the effort acts through the extent, e.g. `heat`. -/
  transfer : N
  deriving DecidableEq

/-- The three columns of a row, which are also the three roles a name may
occupy. -/
inductive Role
  | transfer
  | effort
  | extent
  deriving DecidableEq

/-- The name in one column of one row. -/
def Row.column {N : Type} (r : Row N) : Role → N
  | Role.transfer => r.transfer
  | Role.effort => r.effort
  | Role.extent => r.extent

/-- The three roles, as a list, so that a claim about all of them is decidable. -/
def roles : List Role := [Role.transfer, Role.effort, Role.extent]

@[simp] theorem mem_roles (o : Role) : o ∈ roles := by
  cases o <;> simp [roles]

/-- A register is a list of rows. -/
abbrev Register (N : Type) := List (Row N)

/-- The register's discipline: a name occupies one column of one row and no
other.  It is what makes a name determine its role, and it is checked in the
implementation by `conjugate_audit`. -/
def RolesUnique {N : Type} [DecidableEq N] (R : Register N) : Prop :=
  ∀ r₁ ∈ R, ∀ r₂ ∈ R, ∀ o₁ ∈ roles, ∀ o₂ ∈ roles,
    r₁.column o₁ = r₂.column o₂ → r₁ = r₂ ∧ o₁ = o₂

instance {N : Type} [DecidableEq N] (R : Register N) :
    Decidable (RolesUnique R) := by
  unfold RolesUnique; infer_instance

/-- The relation a pair of columns names: `x` stands in it to `y` when one row
carries `x` in the source column and `y` in the target column.  `effort_of` is
`Rel R Role.effort Role.transfer`. -/
def Rel {N : Type} (R : Register N) (src tgt : Role) (x y : N) : Prop :=
  ∃ r ∈ R, r.column src = x ∧ r.column tgt = y

/-! ## 2.  A named relation is a bijection between its two columns -/

variable {N : Type} [DecidableEq N]

/-- Single-valued forwards: from one name the relation reaches at most one. -/
theorem rel_functional {R : Register N} (h : RolesUnique R)
    {src tgt : Role} {x y z : N}
    (hy : Rel R src tgt x y) (hz : Rel R src tgt x z) : y = z := by
  obtain ⟨r₁, hr₁, hx₁, hy₁⟩ := hy
  obtain ⟨r₂, hr₂, hx₂, hz₂⟩ := hz
  obtain ⟨hrow, -⟩ :=
    h r₁ hr₁ r₂ hr₂ src (mem_roles _) src (mem_roles _) (hx₁.trans hx₂.symm)
  subst hrow
  exact hy₁ ▸ hz₂ ▸ rfl

/-- Single-valued backwards: a name is reached from at most one.  This is what
makes the *reverse* transport legitimate -- applying the relation to a term
that occupies the target column is not a guess, because the source is
determined. -/
theorem rel_injective {R : Register N} (h : RolesUnique R)
    {src tgt : Role} {x y z : N}
    (hx : Rel R src tgt x z) (hy : Rel R src tgt y z) : x = y := by
  obtain ⟨r₁, hr₁, hx₁, hz₁⟩ := hx
  obtain ⟨r₂, hr₂, hy₂, hz₂⟩ := hy
  obtain ⟨hrow, -⟩ :=
    h r₁ hr₁ r₂ hr₂ tgt (mem_roles _) tgt (mem_roles _) (hz₁.trans hz₂.symm)
  subst hrow
  exact hx₁ ▸ hy₂ ▸ rfl

/-! ## 3.  The two directions of transport -/

/-- Transport forwards: the target column of the row carrying `c` in the source
column. -/
def forward (R : Register N) (src tgt : Role) (c : N) : Option N :=
  (R.find? fun r => r.column src = c).map fun r => r.column tgt

/-- Transport in reverse: the source column of the row carrying `c` in the
target column. -/
def reverse (R : Register N) (src tgt : Role) (c : N) : Option N :=
  forward R tgt src c

theorem forward_spec {R : Register N} {src tgt : Role} {c d : N}
    (h : forward R src tgt c = some d) : Rel R src tgt c d := by
  unfold forward at h
  cases hf : R.find? (fun r => r.column src = c) with
  | none => rw [hf] at h; simp at h
  | some r =>
      rw [hf] at h
      simp only [Option.map_some] at h
      have hmem := List.mem_of_find?_eq_some hf
      have hcond := List.find?_some hf
      exact ⟨r, hmem, of_decide_eq_true hcond, Option.some.inj h⟩

theorem reverse_spec {R : Register N} {src tgt : Role} {c d : N}
    (h : reverse R src tgt c = some d) : Rel R src tgt d c := by
  obtain ⟨r, hr, h₁, h₂⟩ := forward_spec (src := tgt) (tgt := src) h
  exact ⟨r, hr, h₂, h₁⟩

/-- The forward answer is the only one: any name the relation reaches from `c`
is the computed one. -/
theorem forward_unique {R : Register N} (h : RolesUnique R) {src tgt : Role}
    {c d e : N} (hd : forward R src tgt c = some d) (he : Rel R src tgt c e) :
    e = d :=
  rel_functional h he (forward_spec hd)

/-- And the reverse answer is the only one. -/
theorem reverse_unique {R : Register N} (h : RolesUnique R) {src tgt : Role}
    {c d e : N} (hd : reverse R src tgt c = some d) (he : Rel R src tgt e c) :
    e = d :=
  rel_injective h he (reverse_spec hd)

/-- A term is *placed* for a relation when it occupies one of its two columns.
Only a placed term has a side to enter the relation on. -/
def Placed (R : Register N) (src tgt : Role) (c : N) : Prop :=
  ∃ r ∈ R, r.column src = c ∨ r.column tgt = c

instance (R : Register N) (src tgt : Role) (c : N) :
    Decidable (Placed R src tgt c) := by
  unfold Placed; infer_instance

omit [DecidableEq N] in
/-- The refusal theorem.  If `C` occupies neither column then nothing stands in
the relation to it in either direction: the register *forces* the refusal, and
answering would mean naming something the relation does not reach.  This is
`heat : temperature :: entropy : ?` -- entropy is an extent -- and it is also
the open-vocabulary boundary, where `C` occupies no column because the
register has never heard of it. -/
theorem no_answer_of_unplaced {R : Register N} {src tgt : Role} {c : N}
    (h : ¬ Placed R src tgt c) :
    (∀ d, ¬ Rel R src tgt c d) ∧ (∀ d, ¬ Rel R src tgt d c) := by
  constructor
  · rintro d ⟨r, hr, hc, -⟩
    exact h ⟨r, hr, Or.inl hc⟩
  · rintro d ⟨r, hr, -, hc⟩
    exact h ⟨r, hr, Or.inr hc⟩

/-- An unplaced term is answered by neither direction of the computation, so
the code and the register agree about the refusal. -/
theorem forward_none_of_unplaced {R : Register N} {src tgt : Role} {c : N}
    (h : ¬ Placed R src tgt c) : forward R src tgt c = none := by
  cases hf : forward R src tgt c with
  | none => rfl
  | some d => exact absurd (forward_spec hf) (no_answer_of_unplaced h |>.1 d)

/-! ## 4.  The negative half: a relation that determines nothing -/

/-- A relation that reaches two different names from one term determines no
answer there.  `related_to` is exactly this: the lexicon carries `heat
related_to temperature` and `heat related_to energy`, so from `heat` the
relation reaches two names and transporting it would be a choice, not a
derivation.  A register that refuses it by name is refusing what this theorem
says cannot be answered. -/
theorem not_unique_of_two_values {M : Type} {S : M → M → Prop} {c d e : M}
    (hd : S c d) (he : S c e) (hne : d ≠ e) : ¬ ∃! x, S c x := by
  rintro ⟨x, -, hx⟩
  exact hne ((hx d hd).trans (hx e he).symm)

/-- The positive counterpart, and the criterion the implementation checks: on a
register with unique roles a named relation *does* determine its answer. -/
theorem exists_unique_of_rel {R : Register N} (h : RolesUnique R)
    {src tgt : Role} {c d : N} (hd : Rel R src tgt c d) :
    ∃! x, Rel R src tgt c x :=
  ⟨d, hd, fun _ hx => rel_functional h hx hd⟩

/-! ## 5.  The table itself

The seven rows, with the EXT10 exponent vector of each effort and extent as the
physics register holds it.  The axes are `L M T I H N J A S B`, and a vector is
the list of the ten exponents in that order; the register's entries are
integers on every name used here, so integer lists are faithful and `decide`
can check the arithmetic. -/

/-- A dimension: the ten EXT10 exponents, in register order. -/
abbrev Dim := List ℤ

/-- Coordinatewise sum of two dimensions. -/
def addDim : Dim → Dim → Dim := List.zipWith (· + ·)

/-- The dimension of `energy`: `L² M T⁻²`. -/
def energyDim : Dim := [2, 1, -2, 0, 0, 0, 0, 0, 0, 0]

/-- One row of the concrete register, with the two dimensions its admissibility
turns on. -/
structure Entry where
  /-- The energy domain. -/
  domain : String
  /-- The intensive potential. -/
  effort : String
  /-- Its EXT10 exponents, as the physics register holds them. -/
  effortDim : Dim
  /-- The extensive quantity. -/
  extent : String
  /-- Its EXT10 exponents. -/
  extentDim : Dim
  /-- The energy transfer the row names. -/
  transfer : String
  deriving DecidableEq

/-- The seven rows. -/
def entries : List Entry :=
  [ ⟨"thermal", "temperature", [0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
     "entropy", [2, 1, -2, 0, -1, 0, 0, 0, 0, 0], "heat"⟩,
    ⟨"mechanical", "force", [1, 1, -2, 0, 0, 0, 0, 0, 0, 0],
     "length", [1, 0, 0, 0, 0, 0, 0, 0, 0, 0], "work"⟩,
    ⟨"hydraulic", "pressure", [-1, 1, -2, 0, 0, 0, 0, 0, 0, 0],
     "volume", [3, 0, 0, 0, 0, 0, 0, 0, 0, 0], "flow_work"⟩,
    ⟨"electrical", "voltage", [2, 1, -3, -1, 0, 0, 0, 0, 0, 0],
     "charge", [0, 0, 1, 1, 0, 0, 0, 0, 0, 0], "electrical_work"⟩,
    ⟨"rotational", "torque", [2, 1, -2, 0, 0, 0, 0, 0, 0, 0],
     "angle", [0, 0, 0, 0, 0, 0, 0, 0, 0, 0], "rotational_work"⟩,
    ⟨"chemical", "chemical_potential", [2, 1, -2, 0, 0, -1, 0, 0, 0, 0],
     "amount", [0, 0, 0, 0, 0, 1, 0, 0, 0, 0], "chemical_work"⟩,
    ⟨"surface", "surface_tension", [0, 1, -2, 0, 0, 0, 0, 0, 0, 0],
     "area", [2, 0, 0, 0, 0, 0, 0, 0, 0, 0], "surface_work"⟩ ]

/-- The register the transport runs over: the same seven rows, as names. -/
def table : Register String :=
  entries.map fun e => ⟨e.domain, e.effort, e.extent, e.transfer⟩

/-- **The grounding criterion, checked.**  In every row the effort's exponents
and the extent's exponents sum to those of energy, so `transfer = effort x
extent` is a dimensional identity and not a slogan.  This is what stops
`pressure` from being paired with `area`. -/
theorem dimensionally_sound :
    ∀ e ∈ entries, addDim e.effortDim e.extentDim = energyDim := by
  decide

/-- **The role criterion, checked.**  No name of the table occupies two
columns, so a name determines its role and the three relations are bijections
between their columns. -/
theorem roles_unique_table : RolesUnique table := by
  decide +kernel

/-- `effort_of`: the relation `temperature effort_of heat` belongs to. -/
abbrev effortOf : String → String → Prop := Rel table Role.effort Role.transfer

/-- `conjugate_of`: effort against extent, within one row. -/
abbrev conjugateOf : String → String → Prop := Rel table Role.effort Role.extent

/-- **The question this round was about.**  `heat : temperature :: force : ?`
is `temperature effort_of heat` carried to `force`.  `A` is the transfer and
`B` the effort, and `force` occupies the effort column -- `B`'s side -- so the
analogy is transported *in reverse*, which is to read `effort_of` from its own
source column: the transfer whose effort is `force`. -/
theorem answer_heat_temperature_force :
    forward table Role.effort Role.transfer "force" = some "work" := by
  decide

/-- And it is the only answer: nothing else stands in `effort_of` to `force`. -/
theorem answer_unique_heat_temperature_force (d : String)
    (h : effortOf "force" d) : d = "work" :=
  forward_unique roles_unique_table answer_heat_temperature_force h

/-- `temperature : entropy :: force : ?` is the same table read along its other
relation, and answers `length`. -/
theorem answer_temperature_entropy_force :
    forward table Role.effort Role.extent "force" = some "length" := by
  decide

/-- `heat : temperature :: entropy : ?` is refused, and the refusal is forced:
`entropy` occupies the extent column, so `effort_of` -- which runs between
efforts and transfers -- reaches nothing from it in either direction. -/
theorem entropy_unplaced : ¬ Placed table Role.effort Role.transfer "entropy" := by
  decide

/-- The open-vocabulary boundary, in the same form: a name the register has
never heard of is unplaced, so the refusal is a fact about the register rather
than a failed search. -/
theorem justice_unplaced : ¬ Placed table Role.effort Role.transfer "justice" := by
  decide

/-- Both refusals are refusals of the computation too. -/
theorem no_answer_entropy :
    forward table Role.effort Role.transfer "entropy" = none :=
  forward_none_of_unplaced entropy_unplaced

end GLM.Conjugate
