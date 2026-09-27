/-
# The meaning space

The formal counterpart of `overlay/glm_universal/semantics/meaning.py`.

The GLM's older lexical layers encode a *word*: the ARC-era concept graph
hashed a spelling with SHA-256 and snapped the result near a Golay codeword.
That is a stable identifier of a **string**.  This file is about the other
thing: a carrier built only from what a term **denotes**.

A `Meaning` is a canonical, notation-free record of determinate content --
an exact rational, an EXT10 dimension vector, an exact magnitude, a chemical
formula as a multiset of `(Z, count)` pairs, or one of eight operations.  It
is laid out in 24 exact rationals, coordinate for coordinate as the Python
codec lays it out:

```
0       kind        1..6
1..10   ext10       L M T I H N J A S B exponents
11      magnitude
12..21  formula     five (Z, count) slots
22      operation   0..8
23      checksum    sum (i+1) * c_i over coordinates 0..22
```

What is proved here.

* `coords_length` -- the carrier is 24 coordinates, always.
* `decode_coords` -- the round trip: every well-formed meaning is recovered
  from its carrier exactly.  Nothing about the subject is lost by encoding.
* `coords_injective` -- distinct well-formed meanings have distinct carriers,
  so carrier equality *is* meaning equality and may be used as such.
* `encode_indep_of_notation` -- `coords` has no notation argument, so any two
  notations for the same meaning have the same carrier.  This is the formal
  content of "we encode the meaning, not the name".
* `formula_capacity_collision` and `capacity_forces_refusal` -- the boundary.
  Five formula slots hold five distinct elements; a sixth is not encodable,
  two six-element formulas collide, and the honest response of a layer at its
  capacity is refusal rather than a silently truncated carrier.
-/
import Mathlib

namespace GLM.Semantics

/-! ## Kinds and operations -/

/-- The six kinds of determinate content the meaning space admits. -/
inductive Kind
  | number | dimension | quantity | element | compound | operation
  deriving DecidableEq, Repr

/-- The kind's carrier index, `1..6`. -/
def Kind.index : Kind → ℚ
  | .number => 1 | .dimension => 2 | .quantity => 3
  | .element => 4 | .compound => 5 | .operation => 6

/-- The eight determinate operations on meanings. -/
inductive Op
  | add | subtract | multiply | divide | negate | reciprocal | power | identity
  deriving DecidableEq, Repr

/-- The operation's carrier index, `1..8`. -/
def Op.index : Op → ℚ
  | .add => 1 | .subtract => 2 | .multiply => 3 | .divide => 4
  | .negate => 5 | .reciprocal => 6 | .power => 7 | .identity => 8

/-- Coordinate 22: `0` when the meaning carries no operation. -/
def opIndex : Option Op → ℚ
  | none => 0
  | some o => o.index

/-! ## Meanings -/

/-- What a term denotes.  The fields mirror the Python dataclass exactly. -/
structure Meaning where
  /-- Which of the six kinds of determinate content this is. -/
  kind : Kind
  /-- The EXT10 exponent vector `L M T I H N J A S B`, exact rationals. -/
  exponents : Fin 10 → ℚ
  /-- The exact rational a number is, or a quantity's coherent-SI magnitude. -/
  magnitude : ℚ
  /-- A chemical formula: `(Z, count)` pairs, ascending in `Z`. -/
  formula : List (ℕ × ℕ)
  /-- The operation, for the `operation` kind. -/
  operation : Option Op

/-- How many `(Z, count)` slots the carrier has. -/
def maxFormulaSlots : ℕ := 5

/-- A meaning is well formed when its formula fits the carrier's slots and
every slot is a real atom: a positive atomic number with a positive count.
These are exactly the conditions the carrier needs in order to be read back;
`(0, 0)` is the padding, so no atom may look like padding. -/
def Meaning.WellFormed (m : Meaning) : Prop :=
  m.formula.length ≤ maxFormulaSlots ∧ ∀ p ∈ m.formula, 1 ≤ p.1 ∧ 1 ≤ p.2

/-! ## The carrier -/

/-- Coordinate `12 + 2i`: the atomic number in slot `i`, `0` when unused. -/
def slotZ (f : List (ℕ × ℕ)) (i : ℕ) : ℚ := ((f.getD i (0, 0)).1 : ℚ)

/-- Coordinate `13 + 2i`: the atom count in slot `i`, `0` when unused. -/
def slotN (f : List (ℕ × ℕ)) (i : ℕ) : ℚ := ((f.getD i (0, 0)).2 : ℚ)

/-- The deterministic linear integrity coordinate `sum (i+1) * c_i`, counting
positions from `i`. -/
def checksumFrom : ℕ → List ℚ → ℚ
  | _, [] => 0
  | i, c :: cs => (i + 1 : ℚ) * c + checksumFrom (i + 1) cs

/-- Coordinate 23, computed over coordinates `0..22`. -/
def checksum (l : List ℚ) : ℚ := checksumFrom 0 l

/-- Coordinates `0..22` of a meaning: everything but the checksum. -/
def Meaning.body (m : Meaning) : List ℚ :=
  [m.kind.index,
   m.exponents 0, m.exponents 1, m.exponents 2, m.exponents 3, m.exponents 4,
   m.exponents 5, m.exponents 6, m.exponents 7, m.exponents 8, m.exponents 9,
   m.magnitude,
   slotZ m.formula 0, slotN m.formula 0, slotZ m.formula 1, slotN m.formula 1,
   slotZ m.formula 2, slotN m.formula 2, slotZ m.formula 3, slotN m.formula 3,
   slotZ m.formula 4, slotN m.formula 4,
   opIndex m.operation]

/-- The 24 exact coordinates of a meaning.

The function takes a meaning and nothing else: there is no argument through
which a spelling, a name or a language could reach the carrier. -/
def Meaning.coords (m : Meaning) : List ℚ := m.body ++ [checksum m.body]

theorem body_length (m : Meaning) : m.body.length = 23 := rfl

/-- The carrier is always 24 coordinates. -/
theorem coords_length (m : Meaning) : m.coords.length = 24 := rfl

/-! ## Decoding -/

/-- Read a coordinate as a natural number, or refuse. -/
def natOf (q : ℚ) : Option ℕ :=
  if q.den = 1 ∧ 0 ≤ q.num then some q.num.toNat else none

@[simp] theorem natOf_natCast (n : ℕ) : natOf (n : ℚ) = some n := by
  simp [natOf]

/-- Read coordinate 0 as a kind, or refuse. -/
def parseKind (q : ℚ) : Option Kind :=
  if q = 1 then some .number else
  if q = 2 then some .dimension else
  if q = 3 then some .quantity else
  if q = 4 then some .element else
  if q = 5 then some .compound else
  if q = 6 then some .operation else none

/-- Read coordinate 22 as an operation slot, or refuse. -/
def parseOp (q : ℚ) : Option (Option Op) :=
  if q = 0 then some none else
  if q = 1 then some (some .add) else
  if q = 2 then some (some .subtract) else
  if q = 3 then some (some .multiply) else
  if q = 4 then some (some .divide) else
  if q = 5 then some (some .negate) else
  if q = 6 then some (some .reciprocal) else
  if q = 7 then some (some .power) else
  if q = 8 then some (some .identity) else none

/-- Read the ten formula coordinates as a formula: `(0, 0)` is padding and is
dropped, anything else must be a genuine `(Z, count)` pair. -/
def parseSlots : List ℚ → Option (List (ℕ × ℕ))
  | [] => some []
  | z :: n :: rest =>
      if z = 0 ∧ n = 0 then parseSlots rest
      else
        match natOf z, natOf n, parseSlots rest with
        | some zz, some nn, some r => some ((zz, nn) :: r)
        | _, _, _ => none
  | _ => none

/-- The meaning of a carrier, or `none`.

The checksum is checked first, so a perturbed carrier is refused rather than
resolving quietly to a different meaning. -/
def decode (c : List ℚ) : Option Meaning :=
  match c with
  | [k, e0, e1, e2, e3, e4, e5, e6, e7, e8, e9, mag,
     z0, n0, z1, n1, z2, n2, z3, n3, z4, n4, op, chk] =>
      if checksum [k, e0, e1, e2, e3, e4, e5, e6, e7, e8, e9, mag,
                   z0, n0, z1, n1, z2, n2, z3, n3, z4, n4, op] = chk then
        match parseKind k, parseOp op,
              parseSlots [z0, n0, z1, n1, z2, n2, z3, n3, z4, n4] with
        | some kd, some o, some f =>
            some { kind := kd
                   exponents := ![e0, e1, e2, e3, e4, e5, e6, e7, e8, e9]
                   magnitude := mag
                   formula := f
                   operation := o }
        | _, _, _ => none
      else none
  | _ => none

/-! ## The round trip -/

theorem parseKind_index (k : Kind) : parseKind k.index = some k := by
  cases k <;> norm_num [parseKind, Kind.index]

theorem parseOp_index (o : Option Op) : parseOp (opIndex o) = some o := by
  rcases o with _ | o
  · norm_num [parseOp, opIndex]
  · cases o <;> norm_num [parseOp, opIndex, Op.index]

theorem parseSlots_of_wellFormed (f : List (ℕ × ℕ))
    (hlen : f.length ≤ maxFormulaSlots)
    (hpos : ∀ p ∈ f, 1 ≤ p.1 ∧ 1 ≤ p.2) :
    parseSlots [slotZ f 0, slotN f 0, slotZ f 1, slotN f 1, slotZ f 2,
                slotN f 2, slotZ f 3, slotN f 3, slotZ f 4, slotN f 4]
      = some f := by
  rcases f with _ | ⟨a, f⟩
  · simp [parseSlots, slotZ, slotN]
  have ha : a.1 ≠ 0 := by have := hpos a (by simp); omega
  rcases f with _ | ⟨b, f⟩
  · simp [parseSlots, slotZ, slotN, ha]
  have hb : b.1 ≠ 0 := by have := hpos b (by simp); omega
  rcases f with _ | ⟨c, f⟩
  · simp [parseSlots, slotZ, slotN, ha, hb]
  have hc : c.1 ≠ 0 := by have := hpos c (by simp); omega
  rcases f with _ | ⟨d, f⟩
  · simp [parseSlots, slotZ, slotN, ha, hb, hc]
  have hd : d.1 ≠ 0 := by have := hpos d (by simp); omega
  rcases f with _ | ⟨e, f⟩
  · simp [parseSlots, slotZ, slotN, ha, hb, hc, hd]
  have he : e.1 ≠ 0 := by have := hpos e (by simp); omega
  rcases f with _ | ⟨g, f⟩
  · simp [parseSlots, slotZ, slotN, ha, hb, hc, hd, he]
  · simp only [List.length_cons, maxFormulaSlots] at hlen
    omega

/-- **The round trip.**  A well-formed meaning is recovered from its carrier
exactly: encoding loses nothing about the subject. -/
theorem decode_coords (m : Meaning) (h : m.WellFormed) : decode m.coords = some m := by
  obtain ⟨hlen, hpos⟩ := h
  obtain ⟨k, e, mag, f, o⟩ := m
  simp only [Meaning.coords, Meaning.body, decode, List.cons_append, List.nil_append]
  rw [if_pos trivial, parseKind_index, parseOp_index,
    parseSlots_of_wellFormed f hlen hpos]
  simp only [Option.some.injEq, Meaning.mk.injEq, and_true, true_and]
  funext i
  fin_cases i <;> rfl

/-- **Injectivity.**  Distinct well-formed meanings have distinct carriers, so
comparing 24 rationals decides whether two terms denote the same thing. -/
theorem coords_injective {m m' : Meaning} (h : m.WellFormed) (h' : m'.WellFormed)
    (he : m.coords = m'.coords) : m = m' := by
  have hd := decode_coords m h
  rw [he, decode_coords m' h'] at hd
  exact (Option.some_inj.mp hd).symm

/-- **Notation independence.**  Two notations for the same meaning have the
same carrier -- and this is not a claim about the implementation, it is forced
by the type of `coords`, which has no notation argument.  `denote` here is any
resolution of notations to meanings. -/
theorem encode_indep_of_notation {N : Type*} (denote : N → Meaning) (a b : N)
    (h : denote a = denote b) : (denote a).coords = (denote b).coords := by
  rw [h]

/-! ## The capacity boundary

Five slots hold five distinct elements.  A sixth has nowhere to go, and any
layer that answers anyway must conflate.  The Python codec refuses such a
formula; the two theorems below are why refusal is the only honest option. -/

/-- Two distinct six-element formulas that the five slots cannot separate:
the carrier sees only the first five pairs. -/
theorem formula_capacity_collision :
    ∃ f g : List (ℕ × ℕ), f ≠ g ∧ f.length = 6 ∧ g.length = 6 ∧
      (∀ p ∈ f, 1 ≤ p.1 ∧ 1 ≤ p.2) ∧ (∀ p ∈ g, 1 ≤ p.1 ∧ 1 ≤ p.2) ∧
      ∀ i < maxFormulaSlots, slotZ f i = slotZ g i ∧ slotN f i = slotN g i := by
  refine ⟨[(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)],
          [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (7, 1)],
          by decide, rfl, rfl, by decide, by decide, ?_⟩
  intro i hi
  simp only [maxFormulaSlots] at hi
  interval_cases i <;> exact ⟨rfl, rfl⟩

/-- **Capacity forces refusal.**  There are distinct meanings, each with a
formula of legitimate atoms, whose carriers are equal.  A layer at its
capacity therefore cannot both answer and stay truthful: `decode` of the
common carrier is at most one of them, so the other must be refused. -/
theorem capacity_forces_refusal :
    ∃ m m' : Meaning, m ≠ m' ∧
      (∀ p ∈ m.formula, 1 ≤ p.1 ∧ 1 ≤ p.2) ∧
      (∀ p ∈ m'.formula, 1 ≤ p.1 ∧ 1 ≤ p.2) ∧
      m.coords = m'.coords ∧
      ¬ (decode m.coords = some m ∧ decode m'.coords = some m') := by
  refine ⟨⟨Kind.compound, fun _ => 0, 0,
          [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)], none⟩,
          ⟨Kind.compound, fun _ => 0, 0,
          [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (7, 1)], none⟩,
          ?_, by decide, by decide, ?_, ?_⟩
  · simp only [ne_eq, Meaning.mk.injEq, not_and]
    intro _ _ _
    decide
  · rfl
  · rintro ⟨h1, h2⟩
    rw [show (⟨Kind.compound, fun _ => 0, 0,
        [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1)], none⟩ : Meaning).coords
        = (⟨Kind.compound, fun _ => 0, 0,
        [(1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (7, 1)], none⟩ : Meaning).coords from rfl] at h1
    have := h1.symm.trans h2
    simp only [Option.some.injEq, Meaning.mk.injEq] at this
    exact absurd this.2.2.2.1 (by decide)

end GLM.Semantics
