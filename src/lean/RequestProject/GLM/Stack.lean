/-
# The concrete GLM layer stack, and its measured information loss

`Layers.lean` develops the abstract theory.  This file instantiates it on the
GLM's own carriers and reproduces, as theorems, the three lowest layers of
`glm_universal/reasoning/dimension_layers.py`:

| layer | GLM name | what it perceives | failure mode (proved here) |
|---|---|---|---|
| 0 | substrate (GLM-0) | the parity bit of each coordinate | conflates carriers of equal parity; addition descends only on integer carriers |
| 1 | integer (GLM-1) | the integer part of each coordinate | conflates carriers with equal integer parts; addition descends only on integer carriers |
| 2 | rational (GLM-2) | the exact rational coordinates | lossless: no further resolution boundary exists above it |

The results are of three kinds.

* **Resolution boundaries.**  Each layer conflates pairs the next one splits;
  the boundary sets are explicitly inhabited, and empty above the rational layer.
* **Operational boundaries.**  Adding dimension exponents — the GLM's
  composition of concepts — descends to the substrate and integer layers *on
  integer carriers only*.  Once fractional exponents appear the same law fails,
  which is exactly the documented failure mode of GLM-1
  ("integer-only: cannot represent fractional dimensions").
* **A measurement.**  On an explicit four-carrier region the three layers
  resolve 2, 3 and 4 classes, so the loss counts are 2, 1 and 0.
-/
import RequestProject.GLM.Layers

namespace GLM.Info

open Layer

/-! ## The three layers -/

/-- Layer 0, the substrate (GLM-0): each coordinate is seen as a single bit,
the parity of its integer part.  This is `_substrate_perceive`. -/
def substrateLayer : Layer ℚ where
  View := ZMod 2
  perceive q := (⌊q⌋ : ZMod 2)

/-- Layer 1, the integer layer (GLM-1): each coordinate is seen as an integer
dimension exponent.  This is `_integer_perceive`. -/
def integerLayer : Layer ℚ where
  View := ℤ
  perceive q := ⌊q⌋

/-- Layer 2, the rational layer (GLM-2): the exact rational coordinate, with
fractional exponents and scale.  This is `_rational_perceive`. -/
def rationalLayer : Layer ℚ where
  View := ℚ
  perceive q := q

instance : Fintype substrateLayer.View := inferInstanceAs (Fintype (ZMod 2))
instance : DecidableEq substrateLayer.View := inferInstanceAs (DecidableEq (ZMod 2))
instance : DecidableEq integerLayer.View := inferInstanceAs (DecidableEq ℤ)
instance : DecidableEq rationalLayer.View := inferInstanceAs (DecidableEq ℚ)

@[simp] lemma substrate_perceive (q : ℚ) : substrateLayer.perceive q = (⌊q⌋ : ZMod 2) := rfl
@[simp] lemma integer_perceive (q : ℚ) : integerLayer.perceive q = ⌊q⌋ := rfl
@[simp] lemma rational_perceive (q : ℚ) : rationalLayer.perceive q = q := rfl

lemma floor_half : ⌊(1/2 : ℚ)⌋ = 0 := by norm_num [Int.floor_eq_iff]

/-! ## Refinement: the stack is genuinely layered -/

theorem integer_refines_substrate : Refines integerLayer substrateLayer := by
  intro a b h
  show ((⌊a⌋ : ZMod 2)) = (⌊b⌋ : ZMod 2)
  rw [show ⌊a⌋ = ⌊b⌋ from h]

theorem rational_refines_integer : Refines rationalLayer integerLayer := by
  intro a b h
  show ⌊a⌋ = ⌊b⌋
  rw [show a = b from h]

theorem rational_refines_substrate : Refines rationalLayer substrateLayer :=
  Refines.trans rational_refines_integer integer_refines_substrate

/-- The rational layer is lossless: it is the exact carrier. -/
theorem rational_lossless : rationalLayer.Lossless := fun _ _ h => h

/-! ## Resolution boundaries -/

/-- `0` and `2` have the same parity but different integer parts: the substrate
layer cannot see the difference and the integer layer can. -/
theorem boundary_integer_substrate_nonempty :
    (Boundary integerLayer substrateLayer).Nonempty := by
  refine ⟨(0, 2), ?_, ?_⟩
  · show ((⌊(0 : ℚ)⌋ : ZMod 2)) = (⌊(2 : ℚ)⌋ : ZMod 2)
    rw [Int.floor_zero, show ⌊(2 : ℚ)⌋ = 2 by norm_num]
    decide
  · show ¬ (⌊(0 : ℚ)⌋ = ⌊(2 : ℚ)⌋)
    norm_num

/-- `0` and `1/2` have the same integer part: the integer layer cannot see the
difference and the rational layer can.  This is GLM-1's documented failure —
"a concept like `sqrt(energy/mass)` has no integer encoding". -/
theorem boundary_rational_integer_nonempty :
    (Boundary rationalLayer integerLayer).Nonempty := by
  refine ⟨(0, 1/2), ?_, ?_⟩
  · show ⌊(0 : ℚ)⌋ = ⌊(1/2 : ℚ)⌋
    rw [Int.floor_zero, floor_half]
  · show ¬ ((0 : ℚ) = 1/2)
    norm_num

/-- **No resolution boundary above the rational layer.**  Whatever the Griess and
universal layers add, it is not the power to tell two carriers apart. -/
theorem boundary_above_rational_empty (L : Layer ℚ) :
    Boundary L rationalLayer = ∅ :=
  boundary_eq_empty_of_lossless rational_lossless L

/-- Each resolution boundary is new expressive power, by the abstract theorem. -/
theorem integer_sees_more_than_substrate :
    ∃ P : ℚ → Prop, Visible integerLayer P ∧ ¬ Visible substrateLayer P :=
  (boundary_nonempty_iff_new_visible integer_refines_substrate).1
    boundary_integer_substrate_nonempty

theorem rational_sees_more_than_integer :
    ∃ P : ℚ → Prop, Visible rationalLayer P ∧ ¬ Visible integerLayer P :=
  (boundary_nonempty_iff_new_visible rational_refines_integer).1
    boundary_rational_integer_nonempty

/-! ## Operational boundaries: where a law stops being true

Composing two physical concepts adds their dimension exponents, so the
operation to watch is addition of carriers. -/

/-- The region of integer-valued carriers: the reach of the lower two layers. -/
def integerCarriers : Set ℚ := {q | ∃ k : ℤ, q = (k : ℚ)}

/-- **The addition law is true at the substrate layer, on integer carriers.** -/
theorem substrate_congruent_on_integerCarriers :
    CongruentOn substrateLayer integerCarriers (· + ·) := by
  rintro a b a' b' ⟨ka, rfl⟩ ⟨kb, rfl⟩ ⟨ka', rfl⟩ ⟨kb', rfl⟩ ha hb
  have ha' : ((ka : ZMod 2)) = (ka' : ZMod 2) := by simpa using ha
  have hb' : ((kb : ZMod 2)) = (kb' : ZMod 2) := by simpa using hb
  show ((⌊(ka : ℚ) + (kb : ℚ)⌋ : ZMod 2)) = (⌊(ka' : ℚ) + (kb' : ℚ)⌋ : ZMod 2)
  rw [show ⌊(ka : ℚ) + (kb : ℚ)⌋ = ka + kb by rw [← Int.cast_add, Int.floor_intCast],
    show ⌊(ka' : ℚ) + (kb' : ℚ)⌋ = ka' + kb' by rw [← Int.cast_add, Int.floor_intCast]]
  push_cast
  rw [ha', hb']

/-- **The addition law is true at the integer layer, on integer carriers.** -/
theorem integer_congruent_on_integerCarriers :
    CongruentOn integerLayer integerCarriers (· + ·) := by
  rintro a b a' b' ⟨ka, rfl⟩ ⟨kb, rfl⟩ ⟨ka', rfl⟩ ⟨kb', rfl⟩ ha hb
  have ha' : ka = ka' := by simpa using ha
  have hb' : kb = kb' := by simpa using hb
  show ⌊(ka : ℚ) + (kb : ℚ)⌋ = ⌊(ka' : ℚ) + (kb' : ℚ)⌋
  rw [ha', hb']

/-- **and it stops being true exactly when fractional exponents appear.**
`1/2` and `0` are indistinguishable to the integer layer, but their sums are not:
`1/2 + 1/2 = 1` while `0 + 0 = 0`. -/
theorem integer_not_congruent_on_univ :
    ¬ CongruentOn integerLayer Set.univ (· + ·) := by
  intro h
  have hhalf : integerLayer.Indist (1/2 : ℚ) 0 := by
    show ⌊(1/2 : ℚ)⌋ = ⌊(0 : ℚ)⌋
    rw [Int.floor_zero, floor_half]
  have := h (1/2 : ℚ) (1/2 : ℚ) 0 0 trivial trivial trivial trivial hhalf hhalf
  have hcontra : ⌊(1/2 + 1/2 : ℚ)⌋ = ⌊(0 + 0 : ℚ)⌋ := this
  norm_num at hcontra

/-- The same failure at the substrate layer. -/
theorem substrate_not_congruent_on_univ :
    ¬ CongruentOn substrateLayer Set.univ (· + ·) := by
  intro h
  have hhalf : substrateLayer.Indist (1/2 : ℚ) 0 := by
    show ((⌊(1/2 : ℚ)⌋ : ZMod 2)) = (⌊(0 : ℚ)⌋ : ZMod 2)
    rw [floor_half, Int.floor_zero]
  have := h (1/2 : ℚ) (1/2 : ℚ) 0 0 trivial trivial trivial trivial hhalf hhalf
  have hcontra : ((⌊(1/2 + 1/2 : ℚ)⌋ : ZMod 2)) = (⌊(0 + 0 : ℚ)⌋ : ZMod 2) := this
  rw [show (1/2 + 1/2 : ℚ) = 1 by norm_num, show (0 + 0 : ℚ) = 0 by norm_num,
    Int.floor_one, Int.floor_zero] at hcontra
  exact absurd hcontra (by decide)

/-- **The rational layer takes over**: at its resolution the law holds everywhere,
and it can carry the operation out in its own view space. -/
theorem rational_congruent_on_univ : CongruentOn rationalLayer Set.univ (· + ·) := by
  rintro a b a' b' - - - - ha hb
  show a + b = a' + b'
  rw [show a = a' from ha, show b = b' from hb]

theorem rational_addition_descends :
    ∃ f : rationalLayer.View → rationalLayer.View → rationalLayer.View,
      ∀ a b, rationalLayer.perceive (a + b) = f (rationalLayer.perceive a)
        (rationalLayer.perceive b) :=
  (descends_iff_congruent (L := rationalLayer) (· + ·)).2 rational_congruent_on_univ

/-- and the integer layer provably *cannot*: no operation on integer views can
reproduce addition of rational carriers. -/
theorem integer_addition_does_not_descend :
    ¬ ∃ f : integerLayer.View → integerLayer.View → integerLayer.View,
      ∀ a b, integerLayer.perceive (a + b) = f (integerLayer.perceive a)
        (integerLayer.perceive b) :=
  fun h => integer_not_congruent_on_univ
    ((descends_iff_congruent (L := integerLayer) (· + ·)).1 h)

/-! ## A measurement of the loss

The region `{0, 1/2, 1, 2}`: four carriers, seen as 2, 3 and 4 distinct things
by the three layers. -/

/-- The measured region. -/
def region : Finset ℚ := {0, 1/2, 1, 2}

@[simp] lemma card_region : region.card = 4 := by norm_num [region]

/-- The substrate layer resolves two classes on the region: even and odd. -/
theorem resolution_substrate : resolution substrateLayer region = 2 := by
  have himg : region.image substrateLayer.perceive = (Finset.univ : Finset (ZMod 2)) := by
    apply Finset.eq_univ_of_forall
    intro u
    fin_cases u
    · exact Finset.mem_image.2 ⟨0, by simp [region], by simp⟩
    · refine Finset.mem_image.2 ⟨1, by simp [region], ?_⟩
      simp
  unfold resolution
  rw [himg, Finset.card_univ]
  rfl

/-- The integer layer resolves three classes: the integer parts `0, 1, 2`. -/
theorem resolution_integer : resolution integerLayer region = 3 := by
  have himg : region.image integerLayer.perceive = ({0, 1, 2} : Finset ℤ) := by
    ext u
    simp only [Finset.mem_image, integer_perceive, region, Finset.mem_insert,
      Finset.mem_singleton]
    constructor
    · rintro ⟨x, hx, rfl⟩
      rcases hx with rfl | rfl | rfl | rfl
      · simp
      · rw [floor_half]; simp
      · simp
      · right; right; norm_num
    · rintro (rfl | rfl | rfl)
      · exact ⟨0, by tauto, by simp⟩
      · exact ⟨1, by tauto, by simp⟩
      · exact ⟨2, by tauto, by norm_num⟩
  unfold resolution
  rw [himg]
  norm_num

/-- The rational layer resolves all four carriers: it loses nothing. -/
theorem resolution_rational : resolution rationalLayer region = 4 := by
  have himg : region.image rationalLayer.perceive = region := Finset.image_id
  unfold resolution
  rw [himg, card_region]

theorem lossCount_substrate : lossCount substrateLayer region = 2 := by
  unfold lossCount
  rw [resolution_substrate, card_region]

theorem lossCount_integer : lossCount integerLayer region = 1 := by
  unfold lossCount
  rw [resolution_integer, card_region]

theorem lossCount_rational : lossCount rationalLayer region = 0 := by
  unfold lossCount
  rw [resolution_rational, card_region]

/-! ## The stack and its escalation -/

/-- The GLM stack: substrate below integer below rational. -/
def glmStack : Stack ℚ where
  steps := 2
  layer := ![substrateLayer, integerLayer, rationalLayer]
  refines := by
    intro i j hij
    fin_cases i <;> fin_cases j <;>
      simp_all [Matrix.cons_val_zero, Matrix.cons_val_one] <;>
      first
        | exact refines_refl _
        | exact integer_refines_substrate
        | exact rational_refines_integer
        | exact rational_refines_substrate

@[simp] lemma glmStack_steps : glmStack.steps = 2 := rfl

lemma glmStack_val_zero : ((0 : Fin (glmStack.steps + 1)) : ℕ) = 0 := rfl
lemma glmStack_val_one : ((1 : Fin (glmStack.steps + 1)) : ℕ) = 1 := rfl
lemma glmStack_val_two : ((2 : Fin (glmStack.steps + 1)) : ℕ) = 2 := rfl

@[simp] lemma glmStack_layer_zero : glmStack.layer 0 = substrateLayer := rfl
@[simp] lemma glmStack_layer_one : glmStack.layer 1 = integerLayer := rfl
@[simp] lemma glmStack_layer_two : glmStack.layer 2 = rationalLayer := rfl

/-- `0` and `1` are already told apart by the substrate: no escalation needed. -/
theorem escalate_zero_one : glmStack.escalate 0 1 = some 0 := by
  refine Stack.escalate_eq_some_of _ ?_ ?_
  · show ¬ ((⌊(0 : ℚ)⌋ : ZMod 2) = (⌊(1 : ℚ)⌋ : ZMod 2))
    rw [Int.floor_zero, Int.floor_one]
    decide
  · intro j hj
    have hv : (j : ℕ) < 0 := by
      have := Fin.lt_def.1 hj
      rwa [glmStack_val_zero] at this
    omega

/-- `0` and `2` need the integer layer: the substrate sees the same parity. -/
theorem escalate_zero_two : glmStack.escalate 0 2 = some 1 := by
  refine Stack.escalate_eq_some_of _ ?_ ?_
  · show ¬ (⌊(0 : ℚ)⌋ = ⌊(2 : ℚ)⌋)
    norm_num
  · intro j hj
    have hv : (j : ℕ) < 1 := by
      have := Fin.lt_def.1 hj
      rwa [glmStack_val_one] at this
    have hj0 : j = 0 := Fin.ext (by rw [glmStack_val_zero]; omega)
    subst hj0
    show ¬ ¬ ((⌊(0 : ℚ)⌋ : ZMod 2) = (⌊(2 : ℚ)⌋ : ZMod 2))
    rw [Int.floor_zero, show ⌊(2 : ℚ)⌋ = 2 by norm_num]
    decide

/-- `0` and `1/2` need the rational layer: both lower layers are blind to the
fractional part.  This is escalation to the layer whose reach suffices. -/
theorem escalate_zero_half : glmStack.escalate 0 (1/2) = some 2 := by
  refine Stack.escalate_eq_some_of _ ?_ ?_
  · show ¬ ((0 : ℚ) = 1/2)
    norm_num
  · intro j hj
    have hv : (j : ℕ) < 2 := by
      have := Fin.lt_def.1 hj
      rwa [glmStack_val_two] at this
    rcases (by omega : (j : ℕ) = 0 ∨ (j : ℕ) = 1) with h | h
    · have hj0 : j = 0 := Fin.ext (by rw [glmStack_val_zero]; omega)
      subst hj0
      show ¬ ¬ ((⌊(0 : ℚ)⌋ : ZMod 2) = (⌊(1/2 : ℚ)⌋ : ZMod 2))
      rw [Int.floor_zero, floor_half]
      simp
    · have hj1 : j = 1 := Fin.ext (by rw [glmStack_val_one]; omega)
      subst hj1
      show ¬ ¬ (⌊(0 : ℚ)⌋ = ⌊(1/2 : ℚ)⌋)
      rw [Int.floor_zero, floor_half]
      simp

end GLM.Info
