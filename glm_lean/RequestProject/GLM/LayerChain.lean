/-
# The GLM's own five layers, on the carriers the code actually uses

`Layers.lean` says what a refinement is.  `Cumulative.lean` says how a stack is
*made* into a refinement chain, and exhibits the GLM's situation in miniature on
a two-coordinate carrier space.  This file drops the miniature: the layers here
are the five that `glm_universal/reasoning/dimension_layers.py` ships, over the
carrier type the package really uses — 24 exact rational coordinates.

A layer's `perceive` here is exactly the data its Python `measure` compares, so
that `Indist` in Lean is the same relation as `measure = 0` in the code:

| layer | code | `measure` is zero when | modelled by |
|---|---|---|---|
| substrate | `LAYER_SUBSTRATE` | the 24 parity bits agree | `glmSubstrateLayer` |
| integer | `LAYER_INTEGER` | the parity bits *and* the seven SI7 exponents agree | `glmIntegerLayer` |
| rational | `LAYER_RATIONAL` | the exact carriers agree | `glmRationalLayer` |
| griess | `LAYER_GRIESS` | the carriers agree and the 2A axes agree | `glmGriessLayer` |
| universal | `LAYER_UNIVERSAL` | every lower reading agrees | `glmUniversalLayer` |

The rejected reading is here too: `glmSi7Layer` is `LAYER_INTEGER_RAW`, the
seven exponents on their own.  `glmSi7Layer_not_refines_glmSubstrateLayer` is
the defect the audit found, as a theorem, on the very pair the report printed —
the vacuum against a unit on coordinate 10.  Everything after it is the repair:
the shipped integer layer is `cumulative` of the substrate reading and the SI7
reading, so it refines the substrate by construction, and
`glmChain_refines_of_le` is the statement the audit's `refinement_chain_intact`
field reports — every layer of the shipped stack sees at least as much as every
layer below it.

Two readings are deliberately left abstract, because nothing about the chain
depends on them: the integer part `intOf` of a coordinate, which both the
parity and the exponent readings take, and the 2A axis `axis` a carrier repairs
to.  The theorems hold for every choice, so they hold for the code's; the
witnesses at the end are stated for `intFloor`, the reading the code takes.
-/
import RequestProject.GLM.Cumulative

namespace GLM.Info

open Layer

/-! ## The carrier space and the two readings -/

/-- A GLM carrier: 24 exact rational coordinates.  This is the `Carrier` of
`glm_universal/reasoning/information_loss.py`. -/
abbrev Carrier24 : Type := Fin 24 → ℚ

/-- Coordinates 0–6, the window the SI7 exponents are read from. -/
def si7Index (i : Fin 7) : Fin 24 := Fin.castLE (by norm_num) i

/-- The integer part of a coordinate: the reading `dimension_layers` takes
before it looks at parity or at an exponent. -/
def intFloor (q : ℚ) : ℤ := ⌊q⌋

variable (intOf : ℚ → ℤ)

/-- The substrate's whole reading: one parity bit off each of the 24
coordinates.  This is `dimension_layers.parity_bits`. -/
def parityView (c : Carrier24) : Fin 24 → ZMod 2 := fun i => (intOf (c i) : ZMod 2)

/-- The seven SI7 exponents, read off coordinates 0–6 and nothing else. -/
def si7View (c : Carrier24) : Fin 7 → ℤ := fun i => intOf (c (si7Index i))

/-! ## The five layers, and the reading that was rejected -/

/-- `LAYER_SUBSTRATE`: the 24-bit parity view. -/
def glmSubstrateLayer : Layer Carrier24 where
  View := Fin 24 → ZMod 2
  perceive := parityView intOf

/-- `LAYER_INTEGER_RAW`: the seven SI7 exponents on their own.  This is the
reading the stack does **not** use, kept so the hole can be exhibited. -/
def glmSi7Layer : Layer Carrier24 where
  View := Fin 7 → ℤ
  perceive := si7View intOf

/-- `LAYER_INTEGER`: the SI7 exponents carried **on top of** the substrate's
parity view, which is what makes it cumulative. -/
def glmIntegerLayer : Layer Carrier24 :=
  Layer.cumulative (glmSubstrateLayer intOf) (glmSi7Layer intOf)

/-- `LAYER_RATIONAL`: the exact carrier.  Its measure is the squared distance
between carriers, so its view is the carrier itself. -/
def glmRationalLayer : Layer Carrier24 where
  View := Carrier24
  perceive := id

variable {A : Type} (axis : Carrier24 → A)

/-- The 2A axis a carrier repairs to, as a reading on its own.  Two distinct
carriers can share an axis, which is why the Griess layer carries the carrier
beside it. -/
def axisLayer : Layer Carrier24 where
  View := A
  perceive := axis

/-- `LAYER_GRIESS`: the algebra element carried on top of the carrier, which is
what `_griess_measure` adds the carrier term for. -/
def glmGriessLayer : Layer Carrier24 :=
  Layer.cumulative glmRationalLayer (axisLayer axis)

/-- `LAYER_UNIVERSAL`: every lower reading at once. -/
def glmUniversalLayer : Layer Carrier24 :=
  Layer.cumulative (glmGriessLayer axis) (glmIntegerLayer intOf)

@[simp] theorem glmSubstrateLayer_perceive (c : Carrier24) :
    (glmSubstrateLayer intOf).perceive c = parityView intOf c := rfl

@[simp] theorem glmSi7Layer_perceive (c : Carrier24) :
    (glmSi7Layer intOf).perceive c = si7View intOf c := rfl

@[simp] theorem glmRationalLayer_perceive (c : Carrier24) :
    glmRationalLayer.perceive c = c := rfl

/-! ## The chain is a refinement chain -/

/-- Nothing the substrate saw is given up at the integer layer. -/
theorem glmIntegerLayer_refines_glmSubstrateLayer :
    Refines (glmIntegerLayer intOf) (glmSubstrateLayer intOf) :=
  Layer.cumulative_refines_left _ _

/-- And the exponents it added are kept too. -/
theorem glmIntegerLayer_refines_glmSi7Layer :
    Refines (glmIntegerLayer intOf) (glmSi7Layer intOf) :=
  Layer.cumulative_refines_right _ _

/-- The integer layer is the **coarsest** reading that keeps both: cumulating
repairs the ladder without inventing resolution. -/
theorem glmIntegerLayer_least {N : Layer.{0, 0} Carrier24}
    (h₁ : Refines N (glmSubstrateLayer intOf)) (h₂ : Refines N (glmSi7Layer intOf)) :
    Refines N (glmIntegerLayer intOf) :=
  Layer.cumulative_least h₁ h₂

/-- The rational layer holds the carrier itself, so it loses nothing at all. -/
theorem glmRationalLayer_lossless : glmRationalLayer.Lossless := fun _ _ h => h

/-- Hence it refines every layer, the integer one included. -/
theorem glmRationalLayer_refines (L : Layer Carrier24) : Refines glmRationalLayer L :=
  Layer.Refines.of_lossless glmRationalLayer_lossless L

theorem glmRationalLayer_refines_glmIntegerLayer :
    Refines glmRationalLayer (glmIntegerLayer intOf) := glmRationalLayer_refines _

/-- The Griess layer carries the carrier beside the algebra element, which is
exactly why escalating to it keeps the rational layer's resolution. -/
theorem glmGriessLayer_refines_glmRationalLayer :
    Refines (glmGriessLayer axis) glmRationalLayer :=
  Layer.cumulative_refines_left _ _

theorem glmGriessLayer_lossless : (glmGriessLayer axis).Lossless :=
  Layer.cumulative_lossless_left glmRationalLayer_lossless _

/-- The universal layer holds the Griess view and the integer view at once. -/
theorem glmUniversalLayer_refines_glmGriessLayer :
    Refines (glmUniversalLayer intOf axis) (glmGriessLayer axis) :=
  Layer.cumulative_refines_left _ _

theorem glmUniversalLayer_refines_glmIntegerLayer :
    Refines (glmUniversalLayer intOf axis) (glmIntegerLayer intOf) :=
  Layer.cumulative_refines_right _ _

theorem glmUniversalLayer_lossless : (glmUniversalLayer intOf axis).Lossless :=
  Layer.cumulative_lossless_left (glmGriessLayer_lossless axis) _

/-- The shipped stack, bottom to top: exactly `dimension_layers.LAYERS`, with
every index past the top reading as the top layer. -/
def glmChain : ℕ → Layer Carrier24
  | 0 => glmSubstrateLayer intOf
  | 1 => glmIntegerLayer intOf
  | 2 => glmRationalLayer
  | 3 => glmGriessLayer axis
  | _ => glmUniversalLayer intOf axis

/-- Each step of the shipped stack refines the one below it. -/
theorem glmChain_refines_succ (n : ℕ) :
    Refines (glmChain intOf axis (n + 1)) (glmChain intOf axis n) := by
  match n with
  | 0 => exact glmIntegerLayer_refines_glmSubstrateLayer intOf
  | 1 => exact glmRationalLayer_refines _
  | 2 => exact glmGriessLayer_refines_glmRationalLayer axis
  | 3 => exact glmUniversalLayer_refines_glmGriessLayer intOf axis
  | (k + 4) => exact Layer.refines_refl _

/-- **`refinement_chain_intact`, as a theorem.**  Every layer of the shipped
stack sees at least as much as every layer below it, so escalating never costs
anything.  With `Layer.Visible.mono` this is the cumulative guarantee: a
proposition the substrate can state stays statable all the way up. -/
theorem glmChain_refines_of_le {m n : ℕ} (h : m ≤ n) :
    Refines (glmChain intOf axis n) (glmChain intOf axis m) := by
  induction n with
  | zero =>
      have : m = 0 := Nat.le_zero.1 h
      subst this
      exact Layer.refines_refl _
  | succ k ih =>
      rcases Nat.lt_or_ge m (k + 1) with hm | hm
      · exact (glmChain_refines_succ intOf axis k).trans (ih (Nat.lt_succ_iff.1 hm))
      · have : m = k + 1 := Nat.le_antisymm h hm
        subst this
        exact Layer.refines_refl _

/-- Nothing the substrate can state is lost anywhere up the shipped stack. -/
theorem glmChain_visible_mono {m n : ℕ} (h : m ≤ n) {P : Carrier24 → Prop}
    (hP : Layer.Visible (glmChain intOf axis m) P) :
    Layer.Visible (glmChain intOf axis n) P :=
  Layer.Visible.mono (glmChain_refines_of_le intOf axis h) hP

/-! ## The two carriers that exposed the defect -/

/-- The vacuum: every coordinate zero.  Carrier 0 of
`information_loss.sample_carriers`. -/
def vacuum24 : Carrier24 := fun _ => 0

/-- `v` on coordinate `i`, zero everywhere else. -/
def unitAt (i : Fin 24) (v : ℚ) : Carrier24 := fun j => if j = i then v else 0

@[simp] theorem unitAt_self (i : Fin 24) (v : ℚ) : unitAt i v i = v := by
  simp [unitAt]

theorem unitAt_of_ne {i j : Fin 24} (h : j ≠ i) (v : ℚ) : unitAt i v j = 0 := by
  simp [unitAt, h]

/-- A unit on coordinate 10 — outside the seven-exponent window.  Carrier 4 of
`information_loss.sample_carriers`, and the second half of the pair the audit
reported. -/
def unitOutside : Carrier24 := unitAt 10 1

/-- Two units on coordinate 0: inside the window, and invisible to parity. -/
def twoInside : Carrier24 := unitAt 0 2

/-- The substrate **does** tell the vacuum from a unit on coordinate 10: the
parity bit on that coordinate is the difference. -/
theorem substrate_separates_unitOutside :
    ¬ (glmSubstrateLayer intFloor).Indist vacuum24 unitOutside := by
  intro h
  have hc := congrFun h (10 : Fin 24)
  simp [parityView, intFloor, vacuum24, unitOutside, unitAt] at hc

/-- The SI7 reading alone does **not**: coordinate 10 is outside its window, so
both carriers read as seven zeros. -/
theorem si7_conflates_unitOutside :
    (glmSi7Layer intFloor).Indist vacuum24 unitOutside := by
  show si7View intFloor vacuum24 = si7View intFloor unitOutside
  funext i
  have hz : unitOutside (si7Index i) = 0 := by
    have h7 := i.isLt
    unfold unitOutside unitAt
    rw [if_neg]
    intro hEq
    have hv : (i : ℕ) = 10 := congrArg Fin.val hEq
    omega
  simp [si7View, intFloor, vacuum24, hz]

/-- **The defect, as a theorem on the real carriers.**  A stack whose step
above the substrate reads only the seven exponents is not a refinement chain:
escalating to it destroys the distinction between the vacuum and a unit on
coordinate 10.  This is the pair `information_loss.refinement_violations`
printed, and the reason `refinement_chain_intact` was `False`. -/
theorem glmSi7Layer_not_refines_glmSubstrateLayer :
    ¬ Refines (glmSi7Layer intFloor) (glmSubstrateLayer intFloor) := fun h =>
  substrate_separates_unitOutside (h _ _ si7_conflates_unitOutside)

/-- **The repair, on the same pair.**  The shipped integer layer keeps the
substrate's reading, so it splits the carriers the raw reading conflated. -/
theorem glmIntegerLayer_separates_unitOutside :
    ¬ (glmIntegerLayer intFloor).Indist vacuum24 unitOutside := fun h =>
  substrate_separates_unitOutside (Layer.cumulative_indist_iff.1 h).1

/-- Cumulating did not flatten the stack: the integer layer still gains
strictly over the substrate, on a pair of equal parity and different exponent. -/
theorem boundary_glmIntegerLayer_glmSubstrateLayer_nonempty :
    (Boundary (glmIntegerLayer intFloor) (glmSubstrateLayer intFloor)).Nonempty := by
  refine ⟨(vacuum24, twoInside), ?_, ?_⟩
  · show parityView intFloor vacuum24 = parityView intFloor twoInside
    funext i
    have : twoInside i = if i = 0 then (2 : ℚ) else 0 := rfl
    rw [parityView, parityView, this, vacuum24]
    by_cases hi : i = (0 : Fin 24)
    · rw [if_pos hi]
      norm_num [intFloor]
      decide
    · rw [if_neg hi]
  · intro h
    have h7 : si7View intFloor vacuum24 = si7View intFloor twoInside :=
      (Layer.cumulative_indist_iff.1 h).2
    have h0 := congrFun h7 (0 : Fin 7)
    have hz : twoInside (si7Index 0) = 2 := by
      unfold twoInside unitAt
      rw [if_pos]
      rfl
    simp [si7View, intFloor, vacuum24, hz] at h0

end GLM.Info
