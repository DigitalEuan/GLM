/-
# Stage 0 — what a single distinction forces

The UBP framework announces itself as a *binary* principle: reality is a field
of cells, each in one of two states, and the only dynamics is toggling.  The
archive's first-principles sub-study (`data_object/FirstPrinciples/`) started
from that and nothing else and asked what is *forced*.  `Packing.lean` already
carries its later stages (why 23, and why only then 24); this file retrieves the
first one, the chain from a distinction to the field `𝔽₂`, which the rest of the
development takes as its starting point without saying why.

* `no_information_without_distinction` — a carrier with at most one state
  carries no information: every observable on it is constant.
* `bool_card`, `surjects_onto_bool` — two states is the minimum, and every
  carrier with two distinguishable states maps onto the two-state carrier.
* `bitfield_card` — a field of `n` two-state cells has exactly `2 ^ n` states.
* `perm_bool_card`, `perm_bool_eq` — there are exactly two reversible
  operations on one cell, the identity and the toggle, so "toggle" is not a
  modelling choice.
* `two_element_ring_is_zmod_two` — every ring with two elements is `ZMod 2`:
  binary arithmetic on the substrate is forced by the carrier, not chosen.
* `self_inverse`, `reachable` — cellwise toggling makes the state space the
  elementary abelian group `(ZMod 2)ⁿ`, every state its own inverse and every
  state reachable from any other by exactly one toggle pattern.
* `self_inverse_forces_comm` — and commutativity is derived, not assumed: a
  group in which every element is its own inverse is abelian.

Nothing beyond "there is a distinction, and it can be flipped reversibly" is
used.  What this does *not* force is the number of cells; that is
`Packing.lean`'s question.
-/
import Mathlib

namespace GLM.Distinction

/-! ## No distinction, no information -/

/-- If a carrier has at most one state, every observable defined on it is
constant: a substrate with no distinction carries no information. -/
theorem no_information_without_distinction {α β : Type*} [Subsingleton α]
    (f : α → β) (a b : α) : f a = f b := by
  rw [Subsingleton.elim a b]

/-! ## Two states is the minimum -/

theorem bool_card : Fintype.card Bool = 2 := rfl

/-- Any carrier with two distinguishable states maps onto the two-state
carrier: `Bool` is the universal minimal distinction. -/
theorem surjects_onto_bool {α : Type*} {a b : α} (hab : a ≠ b) :
    ∃ f : α → Bool, Function.Surjective f := by
  classical
  refine ⟨fun x => decide (x = a), fun t => ?_⟩
  cases t with
  | true => exact ⟨a, by simp⟩
  | false => exact ⟨b, by simp [Ne.symm hab]⟩

/-! ## The substrate: `n` binary cells -/

/-- A bitfield of `n` cells, with `ZMod 2` as the state of a cell: by
`two_element_ring_is_zmod_two` the two-state carrier and the two-element field
are the same object, and `ZMod 2` carries the forced arithmetic. -/
abbrev Bits (n : ℕ) := Fin n → ZMod 2

theorem bitfield_card (n : ℕ) : Fintype.card (Bits n) = 2 ^ n := by
  simp [Bits]

theorem bitfield_card_bool (n : ℕ) : Fintype.card (Fin n → Bool) = 2 ^ n := by
  simp

/-! ## The toggle is the only non-trivial reversible unary operation -/

/-- There are exactly two reversible operations on a single cell. -/
theorem perm_bool_card : Fintype.card (Equiv.Perm Bool) = 2 := by
  rw [Fintype.card_perm]; decide

theorem toggle_involutive : ∀ b : Bool, !(!b) = b := by decide

/-- Every reversible operation on one cell is either the identity or the
toggle. -/
theorem perm_bool_eq (σ : Equiv.Perm Bool) :
    (∀ b, σ b = b) ∨ (∀ b, σ b = !b) := by
  revert σ; decide

/-! ## The two-element carrier is a field, uniquely -/

theorem bit_field_card : Fintype.card (ZMod 2) = 2 := by simp

/-- Every ring with two elements is the two-element field `ZMod 2`: the
substrate's arithmetic is forced by its carrier. -/
theorem two_element_ring_is_zmod_two (R : Type) [Ring R] [Fintype R]
    (h : Fintype.card R = 2) : Nonempty (ZMod 2 ≃+* R) :=
  ⟨ZMod.ringEquivOfPrime R (by norm_num) h⟩

/-- The two-state carrier and the two-element field are the same object. -/
def boolEquivZMod2 : Bool ≃ ZMod 2 where
  toFun b := if b then 1 else 0
  invFun x := x ≠ 0
  left_inv := by decide
  right_inv := by decide

/-! ## Toggling generates the state space -/

/-- Toggling twice restores the state: every state is its own inverse. -/
theorem self_inverse {n : ℕ} (x : Bits n) : x + x = 0 := by
  funext i
  have : (2 : ZMod 2) = 0 := rfl
  simpa [two_mul] using congrArg (fun c : ZMod 2 => c * x i) this

/-- Every state is reachable from any other by exactly one toggle pattern. -/
theorem reachable {n : ℕ} (x y : Bits n) : ∃! t : Bits n, x + t = y :=
  ⟨y - x, by ring, fun t ht => by rw [← ht]; ring⟩

/-! ## Reversibility forces commutativity -/

/-- A group in which every element is its own inverse is abelian.  Applied to
the substrate: the commutativity of toggle composition is a theorem, not a
postulate. -/
theorem self_inverse_forces_comm {G : Type*} [Group G] (h : ∀ x : G, x * x = 1)
    (a b : G) : a * b = b * a := by
  have hinv : ∀ x : G, x⁻¹ = x := fun x => by
    rw [eq_comm, ← mul_eq_one_iff_eq_inv]; exact h x
  calc a * b = (a * b)⁻¹ := (hinv _).symm
    _ = b⁻¹ * a⁻¹ := mul_inv_rev a b
    _ = b * a := by rw [hinv, hinv]

end GLM.Distinction
