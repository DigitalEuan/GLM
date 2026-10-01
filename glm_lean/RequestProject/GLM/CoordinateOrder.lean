import Mathlib

/-!
# The ordering operation — two readings of one coordinate, and when it refuses

The field surface (`GLM.FieldSurface`) makes one named field of one named row
reachable.  It is a *table*: it answers about a single row and composes
nothing.  The question the probe oracle left held and unreachable — *is energy
more abstract than water?* — is not a lookup but an **operation over two
readings of the same coordinate**, and the thing that makes it an operation
rather than a second lookup is that it can be wrong: two numbers read off two
rows are only comparable when they are readings *on one scale*.

This file states that operation and proves what it is worth.

A `Reading` is a value together with the scale it was read on; the scale is an
opaque tag (in the shipped system, the table and the field name a value came
from).  `order?` takes two readings that may be absent and returns a verdict
or nothing:

* it is silent exactly when a reading is missing or the two scales differ
  (`order_eq_none_iff`), so a refusal states a fact about the readings rather
  than reporting the failure of a search;
* when it answers, the answer is the true order of the two values
  (`order_lt_iff`, `order_gt_iff`, `order_eq_iff`);
* the answer does not depend on which way round the question was asked
  (`order_swap`), and it is transitive on a common scale (`order_trans`);
* rescaling a whole scale by a positive factor leaves every verdict on it
  unchanged (`order_scale_invariant`), which is what makes *same scale* the
  right side condition;
* and the refusal is not fussiness: across two scales the naive comparison of
  the raw numbers is not scale-free, and `naive_order_is_not_scale_free`
  exhibits a rescaling that flips it.

The shipped counterpart is `glm_universal.reasoning.coordinate_order`, whose
tests pin these same five properties on the real field surface.
-/

namespace GLM.CoordinateOrder

/-- One reading of one coordinate: the scale it was read on, and its value.

In the shipped system the scale tag is the table and the field a value was
read from, so `carrier:lexicon:abstract_concrete` and `lean:line` are two
different scales and two rows read on either of them are comparable. -/
structure Reading where
  /-- The scale the value was read on. -/
  scale : String
  /-- The value, exactly. -/
  value : ℚ
deriving DecidableEq, Repr

/-- Comparison of two rationals as an `Ordering`.

Written out rather than taken from `compare` because `ℚ` carries more than one
`Ord` instance, and the statements below are about the order of the field. -/
def cmpQ (a b : ℚ) : Ordering :=
  if a < b then .lt else if b < a then .gt else .eq

@[simp] lemma cmpQ_eq_lt {a b : ℚ} : cmpQ a b = .lt ↔ a < b := by
  unfold cmpQ
  split_ifs with h₁ h₂ <;> simp_all

@[simp] lemma cmpQ_eq_gt {a b : ℚ} : cmpQ a b = .gt ↔ b < a := by
  unfold cmpQ
  split_ifs with h₁ h₂
  · simp [asymm h₁]
  · simp [h₂]
  · simp [h₂]

@[simp] lemma cmpQ_eq_eq {a b : ℚ} : cmpQ a b = .eq ↔ a = b := by
  unfold cmpQ
  split_ifs with h₁ h₂
  · simp [h₁.ne]
  · simp [h₂.ne']
  · simp [le_antisymm (not_lt.mp h₂) (not_lt.mp h₁)]

/-- Swapping the arguments swaps the verdict. -/
lemma cmpQ_swap (a b : ℚ) : cmpQ b a = (cmpQ a b).swap := by
  unfold cmpQ
  by_cases h : a < b
  · simp [h, asymm h]
  · by_cases h₂ : b < a
    · simp [h, h₂]
    · simp [h, h₂]

/-- Carrying both values by the same positive factor leaves the comparison
alone: that is what it is for two values to be *on one scale*. -/
lemma cmpQ_mul_left {c : ℚ} (hc : 0 < c) (a b : ℚ) :
    cmpQ (c * a) (c * b) = cmpQ a b := by
  unfold cmpQ
  simp [Rat.mul_lt_mul_left hc]

/-- **The operation.**  Order two readings of the same coordinate, or refuse.

It refuses in exactly two situations: a reading it was not given, and two
readings taken on different scales. -/
def order? : Option Reading → Option Reading → Option Ordering
  | some x, some y => if x.scale = y.scale then some (cmpQ x.value y.value) else none
  | _, _ => none

/-! ## §1  The refusal states a fact -/

/-- **Silent exactly when a reading is missing or the scales differ.**

This is the ordering operation's counterpart of
`GLM.FieldSurface.lookup_eq_none_iff`: nothing is refused because a search ran
out, and nothing that satisfies the side condition is refused at all. -/
theorem order_eq_none_iff (a b : Option Reading) :
    order? a b = none ↔
      a = none ∨ b = none ∨
        ∃ x y, a = some x ∧ b = some y ∧ x.scale ≠ y.scale := by
  cases a with
  | none => simp [order?]
  | some x =>
    cases b with
    | none => simp [order?]
    | some y =>
      by_cases h : x.scale = y.scale <;> simp [order?, h]

/-- Read the other way: it answers exactly when both readings are present and
share a scale. -/
theorem order_isSome_iff (x y : Reading) :
    (order? (some x) (some y)).isSome ↔ x.scale = y.scale := by
  by_cases h : x.scale = y.scale <;> simp [order?, h]

/-! ## §2  When it answers, the answer is the order of the values -/

theorem order_lt_iff (x y : Reading) (h : x.scale = y.scale) :
    order? (some x) (some y) = some .lt ↔ x.value < y.value := by
  simp [order?, h]

theorem order_gt_iff (x y : Reading) (h : x.scale = y.scale) :
    order? (some x) (some y) = some .gt ↔ y.value < x.value := by
  simp [order?, h]

theorem order_eq_iff (x y : Reading) (h : x.scale = y.scale) :
    order? (some x) (some y) = some .eq ↔ x.value = y.value := by
  simp [order?, h]

/-- **Nothing is invented.**  Every verdict it returns is the comparison of the
two values it was given. -/
theorem order_sound {x y : Reading} {o : Ordering}
    (h : order? (some x) (some y) = some o) : o = cmpQ x.value y.value := by
  by_cases hs : x.scale = y.scale
  · simpa [order?, hs, eq_comm] using h
  · simp [order?, hs] at h

/-! ## §3  The verdict does not depend on how the question was asked -/

/-- Swapping the two readings swaps the verdict, refusals included. -/
theorem order_swap (a b : Option Reading) :
    order? b a = (order? a b).map Ordering.swap := by
  cases a with
  | none => cases b <;> simp [order?]
  | some x =>
    cases b with
    | none => simp [order?]
    | some y =>
      by_cases h : x.scale = y.scale
      · rw [order?, order?, if_pos h, if_pos h.symm, cmpQ_swap x.value y.value,
          Option.map_some]
      · simp [order?, h, Ne.symm h]

/-- Strictly below is transitive on a common scale. -/
theorem order_trans {x y z : Reading}
    (hxy : order? (some x) (some y) = some .lt)
    (hyz : order? (some y) (some z) = some .lt) :
    order? (some x) (some z) = some .lt := by
  by_cases hs : x.scale = y.scale
  · by_cases ht : y.scale = z.scale
    · have h1 : x.value < y.value := (order_lt_iff x y hs).1 hxy
      have h2 : y.value < z.value := (order_lt_iff y z ht).1 hyz
      exact (order_lt_iff x z (hs.trans ht)).2 (h1.trans h2)
    · simp [order?, ht] at hyz
  · simp [order?, hs] at hxy

/-! ## §4  Why the side condition is *same scale* -/

/-- **A scale may be rescaled without disturbing anything read on it.**  If
both readings are carried by the same positive factor — the same coordinate
reported in a different unit — the verdict is unchanged. -/
theorem order_scale_invariant (x y : Reading) {c : ℚ} (hc : 0 < c) :
    order? (some ⟨x.scale, c * x.value⟩) (some ⟨y.scale, c * y.value⟩)
      = order? (some x) (some y) := by
  by_cases h : x.scale = y.scale
  · simp [order?, h, cmpQ_mul_left hc]
  · simp [order?, h]

/-- **And the refusal is not fussiness.**  Comparing the raw numbers of two
readings that are *not* on one scale is not a scale-free question: one of them
can be carried into the other's unit by a positive factor, and the verdict
flips.  A hundred centimetres is one metre, and one metre is less than two
metres, while a hundred is more than two. -/
theorem naive_order_is_not_scale_free :
    ∃ a b c : ℚ, 0 < c ∧ cmpQ a b ≠ cmpQ (c * a) b := by
  refine ⟨100, 2, 1 / 100, by norm_num, ?_⟩
  norm_num [cmpQ]
  decide

/-! ## §5  The probe question, as the operation settles it

`abstract_concrete` is one of the lexicon register's ten declared semantic
primitives, and the register declares its poles: `0` is abstract and `1` is
concrete.  The shipped carriers hold `1/4` for *energy* and `1` for *water*,
both on the `carrier:lexicon:abstract_concrete` scale, so the operation
answers — and the answer is the one the probe expected. -/

/-- The reading the lexicon register holds for *energy*. -/
def energyAbstractConcrete : Reading :=
  ⟨"carrier:lexicon:abstract_concrete", 1 / 4⟩

/-- The reading the lexicon register holds for *water*. -/
def waterAbstractConcrete : Reading :=
  ⟨"carrier:lexicon:abstract_concrete", 1⟩

/-- **Energy is the more abstract of the two**, on the register's own scale
and its own declared poles. -/
theorem energy_below_water_on_abstract_concrete :
    order? (some energyAbstractConcrete) (some waterAbstractConcrete)
      = some .lt := by
  norm_num [order?, cmpQ, energyAbstractConcrete, waterAbstractConcrete]

/-- The same pair read on two different scales is refused rather than
answered, which is the boundary the operation is built around. -/
theorem across_scales_is_refused :
    order? (some ⟨"lean:line", 100⟩) (some ⟨"python:line", 2⟩) = none := by
  simp [order?]

end GLM.CoordinateOrder
