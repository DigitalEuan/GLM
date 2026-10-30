/-
# The six-facet decomposition is an orthogonal direct sum

The GLM reads a 24-coordinate carrier through six named facets — Dimension,
Scale, Tensor Rank, Context, Nominal Kind and Domain.  The implementation makes
each facet a *strict linear projection*: it zeroes the coordinates the facet
does not own.  This file proves that the six projections behave as the
implementation's report claims:

* `facet_sizes` — the six blocks have sizes `17, 1, 1, 3, 1, 1` and partition
  the 24 coordinates (they partition by construction, because `facet` is a
  function; the content is the sizes);
* `proj_add`, `proj_smul`, `proj_idem` — each projection is linear and
  idempotent;
* `proj_orthogonal` — distinct facets are orthogonal for the coordinate inner
  product;
* `sum_proj` — the six projections reassemble the carrier exactly;
* `pythagoras` — squared length splits across the facets, which is what lets the
  package attribute a discrepancy to a facet and add the pieces back up.

Everything is exact over `ℚ`, matching the package's arithmetic.
-/
import Mathlib

namespace GLM.Facets

open Finset

/-- The six facets, in the package's order. -/
inductive Facet
  | dimension | scale | tensorRank | context | nominalKind | domain
  deriving DecidableEq, Fintype, Repr

open Facet

/-- Which facet owns a coordinate.  Coordinates `0–16` are the dimension
exponents, `17` the decimal scale, `18` the tensor rank, `19–21` the P/T/C
context, `22` the nominal kind and `23` the domain. -/
def facet (i : Fin 24) : Facet :=
  if i.val ≤ 16 then dimension
  else if i.val = 17 then scale
  else if i.val = 18 then tensorRank
  else if i.val ≤ 21 then context
  else if i.val = 22 then nominalKind
  else domain

/-- The coordinates a facet owns. -/
def block (f : Facet) : Finset (Fin 24) := {i | facet i = f}

/-- The six blocks have the sizes the implementation reports. -/
theorem facet_sizes :
    (#(block dimension), #(block scale), #(block tensorRank),
      #(block context), #(block nominalKind), #(block domain))
      = (17, 1, 1, 3, 1, 1) := by
  decide

/-- The blocks cover every coordinate and overlap nowhere: they are a
partition, because `facet` is a function. -/
theorem block_disjoint {f g : Facet} (h : f ≠ g) :
    Disjoint (block f) (block g) := by
  simp only [Finset.disjoint_left, block, Finset.mem_filter]
  rintro i ⟨-, rfl⟩ ⟨-, h'⟩
  exact h h'

theorem mem_block_facet (i : Fin 24) : i ∈ block (facet i) := by
  simp [block]

/-- A carrier: 24 exact rational coordinates. -/
abbrev Carrier : Type := Fin 24 → ℚ

/-- The facet projection: keep the facet's own coordinates, zero the rest. -/
def proj (f : Facet) (v : Carrier) : Carrier :=
  fun i => if facet i = f then v i else 0

/-- The coordinate inner product, which is the Griess form up to the package's
fixed scale factor. -/
def inner (u v : Carrier) : ℚ := ∑ i, u i * v i

/-- Squared length. -/
def normSq (v : Carrier) : ℚ := inner v v

/-! ## Strict linearity -/

theorem proj_add (f : Facet) (u v : Carrier) :
    proj f (u + v) = proj f u + proj f v := by
  funext i; by_cases h : facet i = f <;> simp [proj, h]

theorem proj_smul (f : Facet) (a : ℚ) (v : Carrier) :
    proj f (a • v) = a • proj f v := by
  funext i; by_cases h : facet i = f <;> simp [proj, h]

theorem proj_idem (f : Facet) (v : Carrier) : proj f (proj f v) = proj f v := by
  funext i; by_cases h : facet i = f <;> simp [proj, h]

theorem proj_of_ne {f g : Facet} (h : f ≠ g) (v : Carrier) :
    proj f (proj g v) = 0 := by
  funext i
  by_cases hg : facet i = g <;> simp [proj, hg, Ne.symm h]

/-- The six projections reassemble the carrier. -/
theorem sum_proj (v : Carrier) : ∑ f : Facet, proj f v = v := by
  funext i
  simp only [Finset.sum_apply, proj]
  rw [Finset.sum_eq_single (facet i)]
  · simp
  · intro b _ hb; simp [Ne.symm hb]
  · intro h; exact absurd (Finset.mem_univ _) h

/-! ## Orthogonality and Pythagoras -/

theorem proj_orthogonal {f g : Facet} (h : f ≠ g) (u v : Carrier) :
    inner (proj f u) (proj g v) = 0 := by
  refine Finset.sum_eq_zero fun i _ => ?_
  by_cases hf : facet i = f
  · have : facet i ≠ g := by rw [hf]; exact h
    simp [proj, this]
  · simp [proj, hf]

/-- **Squared length splits across the six facets.**  This is what makes a facet
attribution of a discrepancy exact rather than heuristic: the pieces add up to
the whole. -/
theorem pythagoras (v : Carrier) : normSq v = ∑ f : Facet, normSq (proj f v) := by
  unfold normSq inner
  rw [Finset.sum_comm]
  refine Finset.sum_congr rfl fun i _ => ?_
  rw [Finset.sum_eq_single (facet i)]
  · simp [proj]
  · intro b _ hb; simp [proj, Ne.symm hb]
  · intro h; exact absurd (Finset.mem_univ _) h

/-- The same statement for a pair: the squared distance between two carriers is
the sum of the squared distances of their facet readings. -/
theorem pythagoras_pair (u v : Carrier) :
    normSq (u - v) = ∑ f : Facet, normSq (proj f u - proj f v) := by
  have h : ∀ f : Facet, proj f u - proj f v = proj f (u - v) := by
    intro f
    funext i
    by_cases hf : facet i = f <;> simp [proj, hf]
  simp only [h]
  exact pythagoras (u - v)

end GLM.Facets
