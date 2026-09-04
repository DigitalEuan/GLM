/-
# A measure word as a measurement: the relative reading as a widening

`hot` is, in the semantic lexicon, a concept: ten primitives, a part of speech
and four relations, one of which is `property_of temperature`.  That static
reading says *which quantity* the word is about and *which pole* of it the word
names.  It cannot say **how hot**, and no amount of resolution in the carrier
would let it, because *hot* is not a temperature: hot for a cup of tea is 363 K
and hot for a star is 44 000 K.  What the static reading is missing is the
**comparison class** the word is measured against.

`glm_universal/data_objects/comparison_classes.py` supplies the classes and the
scales; `glm_universal/reasoning/measure_view.py` reads them.  The design
question the code had to settle was whether the relative reading *replaces* the
static one or is *added beside* it, and the project had already answered the
same question once, for the layer chain: widen, never narrow.  This file is
that decision, stated and proved, on the machinery `Cumulative.lean` provides.

* `Use` is a word together with the class it is measured against -- or with
  nothing, when the registers hold no quantity for the word (`large` is
  `property_of size`, and there is no *size* in the physics register).
* `staticLayer` sees exactly what the lexicon carries today.
* `measureReading` sees only the measurement.
* `measureLayer` is the cumulative layer: both.

What is proved:

* `measureLayer_refines_staticLayer` -- the widening gives up nothing;
* `measureLayer_least` -- and adds no resolution beyond what keeping both
  readings forces;
* `boundary_measureLayer_staticLayer` -- what it gains is exactly the pairs
  the static reading conflates and the measurement splits, and
  `hot_tea_star_mem_boundary` is such a pair, so the gain is not empty;
* `measureReading_not_refines_staticLayer` -- the *replacement* reading, the
  one the design rejected, loses information: two words with no measurement
  are the same thing to it while the lexicon tells them apart.  This is the
  `violations = 3` the Python audit reports for `measure_only`;
* `boundary_empty_of_unmeasured` -- where the new reading is undefined the
  widening gains nothing at all, which is why the runtime must **refuse**
  there rather than answer: the refusal is forced by the registers, not by an
  omission in the code;
* `magnitude_strictMono` and `above_on_magnitude_lt` -- the scale order is a
  real order on magnitudes, in every class at once, which is what makes
  *warm < hot < scalding* transportable rather than decorative.
-/
import RequestProject.GLM.Cumulative

namespace GLM.Info

open Layer

/-! ## The objects -/

/-- A measure word, as the static reading has it: a name, the quantity its
`property_of` relation names when the physics register holds one, and its
position on that quantity's scale.  A word with `quantity = none` -- `large`,
whose quantity is *size* -- has no measurement, and its position is not
meaningful. -/
structure MeasureWord where
  /-- The word itself. -/
  name : String
  /-- The quantity the physics register holds for it, if any. -/
  quantity : Option String
  /-- Where the word sits on its scale, in `[0, 1]`. -/
  position : ℚ
  deriving DecidableEq, Repr

/-- A comparison class: an exact bracket on one quantity. -/
structure CompClass where
  /-- The class's name. -/
  name : String
  /-- The quantity it brackets. -/
  quantity : String
  /-- The bottom of the bracket. -/
  low : ℚ
  /-- The top of the bracket. -/
  high : ℚ
  deriving DecidableEq, Repr

/-- The magnitude a position names in a class: `low + p (high - low)`. -/
def CompClass.magnitude (c : CompClass) (p : ℚ) : ℚ :=
  c.low + p * (c.high - c.low)

/-- One *use* of a word: the word, measured against a class, or against
nothing at all. -/
structure Use where
  /-- The word being used. -/
  word : MeasureWord
  /-- The class it is measured against, when there is one. -/
  klass : Option CompClass
  deriving DecidableEq, Repr

/-- The measurement a use names: the quantity, the class and the exact
magnitude -- and `none` exactly where the registers do not reach, either
because the word has no quantity or because the class is a class of a
different quantity. -/
def measurement : Use → Option (String × String × ℚ)
  | ⟨w, some c⟩ =>
      match w.quantity with
      | some q => if c.quantity = q then some (q, c.name, c.magnitude w.position)
                  else none
      | none => none
  | ⟨_, none⟩ => none

/-! ## The three layers -/

/-- What the machine sees of a use **today**: the concept, and no more.  Two
uses of the same word are the same thing to it, whatever they are measured
against -- which is the whole of the complaint that `hot` is a standalone
concept. -/
def staticLayer : Layer Use where
  View := MeasureWord
  perceive u := u.word

/-- The new reading alone: the measurement, and nothing of the concept. -/
def measureReading : Layer Use where
  View := Option (String × String × ℚ)
  perceive := measurement

/-- The measure view as the code has it: the static reading with the
measurement carried beside it. -/
def measureLayer : Layer Use := cumulative staticLayer measureReading

@[simp] lemma staticLayer_perceive (u : Use) : staticLayer.perceive u = u.word := rfl

@[simp] lemma measureReading_perceive (u : Use) :
    measureReading.perceive u = measurement u := rfl

/-! ## The widening -/

/-- **Nothing the lexicon says is given up.**  The measure view refines the
static one. -/
theorem measureLayer_refines_staticLayer : Refines measureLayer staticLayer :=
  cumulative_refines_left _ _

/-- It refines the measurement it adds as well. -/
theorem measureLayer_refines_measureReading : Refines measureLayer measureReading :=
  cumulative_refines_right _ _

/-- **And it is the coarsest layer that keeps both.**  Widening adds no
resolution beyond what keeping the two readings forces. -/
theorem measureLayer_least {N : Layer.{0, 0} Use} (h₁ : Refines N staticLayer)
    (h₂ : Refines N measureReading) : Refines N measureLayer :=
  cumulative_least h₁ h₂

/-- Two uses are the same to the measure view exactly when the word and the
measurement both agree. -/
theorem measureLayer_indist_iff {a b : Use} :
    measureLayer.Indist a b ↔ a.word = b.word ∧ measurement a = measurement b :=
  cumulative_indist_iff

/-- **What the widening gains is exactly what the measurement sees**: the pairs
the static reading conflates and the measurement splits.  No resolution is
invented. -/
theorem boundary_measureLayer_staticLayer :
    Boundary measureLayer staticLayer =
      {p | p.1.word = p.2.word ∧ measurement p.1 ≠ measurement p.2} :=
  boundary_cumulative_left _ _

/-! ## The three registers, in miniature

`hot` on the temperature scale at position `7/8`, against two of the classes
the register holds; and `large`, whose quantity the physics register does not
hold, beside `small`.  These are the objects the Python report prints. -/

/-- `hot`: `property_of temperature`, at `7/8` of its scale. -/
def hot : MeasureWord := ⟨"hot", some "temperature", 7/8⟩

/-- `cold`: the opposite pole, at `1/8`. -/
def cold : MeasureWord := ⟨"cold", some "temperature", 1/8⟩

/-- `large`: `property_of size`, and the physics register holds no *size*. -/
def large : MeasureWord := ⟨"large", none, 7/8⟩

/-- `small`: likewise unmeasurable, and a different word. -/
def small : MeasureWord := ⟨"small", none, 1/8⟩

/-- The comparison class *tea*: 293 K to 373 K. -/
def tea : CompClass := ⟨"tea", "temperature", 293, 373⟩

/-- The comparison class *stellar_surface*: 2000 K to 50000 K. -/
def stellarSurface : CompClass := ⟨"stellar_surface", "temperature", 2000, 50000⟩

/-- *Hot*, for a cup of tea, is 363 K -- exactly. -/
theorem hot_tea_magnitude : tea.magnitude hot.position = 363 := by
  norm_num [CompClass.magnitude, tea, hot]

/-- *Hot*, for a star, is 44000 K.  The same word, and not the same
measurement: this is what the static reading cannot say. -/
theorem hot_star_magnitude : stellarSurface.magnitude hot.position = 44000 := by
  norm_num [CompClass.magnitude, stellarSurface, hot]

/-- *Cold*, for a star, is 8000 K -- hotter than anything the tea class can
name, which is the point of a comparison class. -/
theorem cold_star_magnitude : stellarSurface.magnitude cold.position = 8000 := by
  norm_num [CompClass.magnitude, stellarSurface, cold]

/-- **The gain is not empty.**  Two uses of `hot` that the lexicon cannot tell
apart, and the measure view can. -/
theorem hot_tea_star_mem_boundary :
    (⟨hot, some tea⟩, ⟨hot, some stellarSurface⟩) ∈
      Boundary measureLayer staticLayer := by
  rw [boundary_measureLayer_staticLayer]
  refine ⟨rfl, ?_⟩
  intro h
  have h2 := congrArg (fun o => (o.getD ("", "", 0)).2.2) h
  norm_num [measurement, hot, tea, stellarSurface, CompClass.magnitude] at h2

/-- The measure view therefore splits the pair the static reading conflates. -/
theorem measureLayer_separates_hot_uses :
    ¬ measureLayer.Indist ⟨hot, some tea⟩ ⟨hot, some stellarSurface⟩ :=
  hot_tea_star_mem_boundary.2

/-- And the static reading really does conflate it: the two uses are one thing
to the lexicon. -/
theorem staticLayer_conflates_hot_uses :
    staticLayer.Indist ⟨hot, some tea⟩ ⟨hot, some stellarSurface⟩ := rfl

/-! ## Why the reading is added rather than substituted

The rejected design keeps only the measurement.  It is *not* a refinement of
the static reading: two words the registers cannot measure read the same
`none`, while the lexicon tells them apart.  This is `LAYER_INTEGER_RAW`'s
situation exactly, and the Python audit reports it as three violated pairs. -/

/-- The two unmeasurable words are the same thing to the measurement alone. -/
theorem measureReading_conflates_unmeasured :
    measureReading.Indist ⟨large, none⟩ ⟨small, none⟩ := rfl

/-- The lexicon tells them apart. -/
theorem staticLayer_separates_unmeasured :
    ¬ staticLayer.Indist ⟨large, none⟩ ⟨small, none⟩ := by
  intro h
  have : large = small := h
  simp [large, small] at this

/-- **The replacement reading loses information.**  Keeping only the
measurement is not a refinement of the static reading, so the relative reading
has to be a widening -- which is what the code does and what
`measureLayer` is. -/
theorem measureReading_not_refines_staticLayer :
    ¬ Refines measureReading staticLayer := fun h =>
  staticLayer_separates_unmeasured (h _ _ measureReading_conflates_unmeasured)

/-- The widening keeps them apart, of course. -/
theorem measureLayer_separates_unmeasured :
    ¬ measureLayer.Indist ⟨large, none⟩ ⟨small, none⟩ := fun h =>
  staticLayer_separates_unmeasured (measureLayer_refines_staticLayer _ _ h)

/-! ## Where there is no measurement, there is nothing to say -/

/-- **The refusal is forced.**  Between two uses the registers cannot measure,
the widened view sees exactly what the static view sees: the boundary is empty
there, so the measure query has nothing to add and must refuse rather than
answer.  A refusal at this boundary is a property of the registers, not a gap
in the code. -/
theorem indist_of_unmeasured {a b : Use} (ha : measurement a = none)
    (hb : measurement b = none) :
    measureLayer.Indist a b ↔ staticLayer.Indist a b := by
  rw [measureLayer_indist_iff]
  constructor
  · exact fun h => h.1
  · exact fun h => ⟨h, by rw [ha, hb]⟩

/-- The same statement as a boundary: no pair of unmeasured uses is in the gain. -/
theorem boundary_empty_of_unmeasured {a b : Use} (ha : measurement a = none)
    (hb : measurement b = none) :
    (a, b) ∉ Boundary measureLayer staticLayer := by
  intro h
  rw [boundary_measureLayer_staticLayer] at h
  exact h.2 (by rw [ha, hb])

/-- A use whose word has no quantity has no measurement, whatever class it is
put against.  This is `large`, in general. -/
theorem measurement_eq_none_of_no_quantity {u : Use} (h : u.word.quantity = none) :
    measurement u = none := by
  obtain ⟨w, c⟩ := u
  cases c with
  | none => rfl
  | some c =>
      have hw : w.quantity = none := h
      simp only [measurement, hw]

/-- A word measured against a class of another quantity has no measurement
either: *hot* is not measurable against *walking*. -/
theorem measurement_eq_none_of_mismatch {w : MeasureWord} {c : CompClass}
    {q : String} (hq : w.quantity = some q) (hc : c.quantity ≠ q) :
    measurement ⟨w, some c⟩ = none := by
  simp [measurement, hq, hc]

/-! ## The scale is an order, in every class at once -/

/-- **A class orders positions faithfully.**  When the bracket is nondegenerate
the magnitude is strictly increasing in the position, so a scale order
`warm < hot < scalding` is an order on measurements too -- and it is the same
order in every class, which is what makes the chain transportable. -/
theorem magnitude_strictMono {c : CompClass} (h : c.low < c.high) :
    StrictMono c.magnitude := by
  intro p q hpq
  have hpos : 0 < c.high - c.low := sub_pos.2 h
  have := mul_lt_mul_of_pos_right hpq hpos
  simpa [CompClass.magnitude] using add_lt_add_left this c.low

/-- The ordering, in the form the `above_on` relation states it: a word above
another on its scale names the greater magnitude, in every class of the
quantity. -/
theorem above_on_magnitude_lt {c : CompClass} (h : c.low < c.high)
    {v w : MeasureWord} (hvw : v.position < w.position) :
    c.magnitude v.position < c.magnitude w.position :=
  magnitude_strictMono h hvw

/-- Distinct positions therefore name distinct magnitudes: within one class, a
scale word is a measurement. -/
theorem magnitude_injective {c : CompClass} (h : c.low < c.high) :
    Function.Injective c.magnitude :=
  (magnitude_strictMono h).injective

/-- `hot` outranks `cold`, and hence measures greater in the tea class. -/
theorem cold_below_hot_in_tea :
    tea.magnitude cold.position < tea.magnitude hot.position := by
  norm_num [CompClass.magnitude, tea, hot, cold]

/-- The measure view is lossless on uses with distinct measurements or
distinct words: two different classes of the same word are separated because
the class travels in the reading. -/
theorem measureLayer_separates_classes {w : MeasureWord} {c d : CompClass}
    {q : String} (hq : w.quantity = some q) (hcq : c.quantity = q)
    (hdq : d.quantity = q) (hcd : c.name ≠ d.name) :
    ¬ measureLayer.Indist ⟨w, some c⟩ ⟨w, some d⟩ := by
  intro h
  have h2 := (measureLayer_indist_iff.1 h).2
  simp only [measurement, hq, hcq, hdq] at h2
  exact hcd (congrArg (fun o => (o.getD ("", "", 0)).2.1) h2)

end GLM.Info
