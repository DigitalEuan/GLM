/-
# The comparative: *hotter than*, *as hot as*

`MeasureView.lean` reads a **use** -- a measure word together with the
comparison class it is measured against -- as an exact magnitude, and proves
that reading is a *widening* of the static lexicon concept.  What it stops
short of is the comparative form.  The study that accompanies it
(`studies/RELATIVE_MEASURE_STUDY.md` §6) records the gap in those words:
`above_on` orders words on a scale and `above_on_magnitude_lt` shows the order
survives into magnitudes, but *hotter than* and *as hot as* were not askable,
because they are relations between **uses**, not between words.

This file is that relation, and the reason it cannot be read off the words.

* `reading` is the quantity and the magnitude a use names, `none` exactly
  where `measurement` is `none`.
* `Comparable a b` says the two uses name magnitudes of the *same* quantity.
* `HotterThan a b` and `AsHotAs a b` are the comparative and the equative.

What is proved:

* the comparative is a **strict order** where it is defined -- irreflexive,
  asymmetric, transitive -- and trichotomous on any comparable pair
  (`hotterThan_trichotomy`), while `AsHotAs` is an equivalence on measured
  uses;
* **the word order does not decide it.**  `cold` sits below `hot` on the
  temperature scale, yet *cold, for a star* (8000 K) is hotter than *hot, for
  a cup of tea* (363 K): `coldStar_hotterThan_hotTea`, and hence
  `comparative_not_determined_by_word_order`.  Within one class the two orders
  do agree, and exactly agree: `hotterThan_iff_position_lt`;
* **the comparative is invisible to the static reading and visible to the
  measure view.**  `comparative_not_static` exhibits a pair the lexicon
  conflates and the comparative separates, so no widening-free reading of the
  concept could answer the question; `hotterThan_congr` shows the comparative
  *is* a function of `measureLayer`, so the widening is enough to answer it;
* **the refusals are forced.**  An unmeasured use is comparable with nothing
  (`not_comparable_left_of_unmeasured`), and two uses of different quantities
  are incomparable however well measured they are
  (`hotTea_not_comparable_fastWalking`) -- the runtime must decline, and the
  decline is a property of the registers rather than a hole in the code.
-/
import RequestProject.GLM.MeasureView

namespace GLM.Info

open Layer

/-! ## The reading a comparison needs -/

/-- The quantity and the magnitude a use names.  The class name, which
`measurement` also carries, is deliberately dropped: a comparison is between
magnitudes, and two uses of *different* classes are compared exactly as two
uses of the same one. -/
def reading (u : Use) : Option (String × ℚ) :=
  (measurement u).map (fun t => (t.1, t.2.2))

@[simp] theorem reading_none_iff {u : Use} : reading u = none ↔ measurement u = none := by
  unfold reading
  cases measurement u <;> simp

/-- The reading of a measured use, spelled out. -/
@[simp] theorem reading_of_match {w : MeasureWord} {c : CompClass} {q : String}
    (hq : w.quantity = some q) (hc : c.quantity = q) :
    reading ⟨w, some c⟩ = some (q, c.magnitude w.position) := by
  simp [reading, measurement, hq, hc]

/-! ## The three relations -/

/-- Two uses are **comparable** when both are measured and both measure the
same quantity.  Nothing else is: a temperature and a velocity name no common
scale, and neither does a use the registers cannot measure at all. -/
def Comparable (a b : Use) : Prop :=
  ∃ q x y, reading a = some (q, x) ∧ reading b = some (q, y)

/-- *a is hotter than b*: both name a magnitude of one quantity, and `a`'s is
the greater.  Read on any quantity at all -- *heavier*, *faster*, *brighter*
are the same relation on another register. -/
def HotterThan (a b : Use) : Prop :=
  ∃ q x y, reading a = some (q, x) ∧ reading b = some (q, y) ∧ y < x

/-- *a is as hot as b*: both name the *same* magnitude of one quantity. -/
def AsHotAs (a b : Use) : Prop :=
  ∃ q x, reading a = some (q, x) ∧ reading b = some (q, x)

theorem Comparable.symm {a b : Use} (h : Comparable a b) : Comparable b a := by
  obtain ⟨q, x, y, ha, hb⟩ := h
  exact ⟨q, y, x, hb, ha⟩

theorem HotterThan.comparable {a b : Use} (h : HotterThan a b) : Comparable a b := by
  obtain ⟨q, x, y, ha, hb, _⟩ := h
  exact ⟨q, x, y, ha, hb⟩

theorem AsHotAs.comparable {a b : Use} (h : AsHotAs a b) : Comparable a b := by
  obtain ⟨q, x, ha, hb⟩ := h
  exact ⟨q, x, x, ha, hb⟩

theorem AsHotAs.symm {a b : Use} (h : AsHotAs a b) : AsHotAs b a := by
  obtain ⟨q, x, ha, hb⟩ := h
  exact ⟨q, x, hb, ha⟩

theorem AsHotAs.trans {a b c : Use} (h : AsHotAs a b) (h' : AsHotAs b c) :
    AsHotAs a c := by
  obtain ⟨q, x, ha, hb⟩ := h
  obtain ⟨q', y, hb', hc⟩ := h'
  rw [hb] at hb'
  cases hb'
  exact ⟨q, x, ha, hc⟩

/-- The equative is reflexive exactly on the uses that are measured at all --
which is the same boundary the comparative has. -/
theorem asHotAs_refl_iff {a : Use} : AsHotAs a a ↔ ∃ r, reading a = some r := by
  constructor
  · rintro ⟨q, x, ha, -⟩; exact ⟨(q, x), ha⟩
  · rintro ⟨⟨q, x⟩, ha⟩; exact ⟨q, x, ha, ha⟩

/-! ## The comparative is a strict order where it is defined -/

theorem hotterThan_irrefl (a : Use) : ¬ HotterThan a a := by
  rintro ⟨q, x, y, ha, ha', hlt⟩
  rw [ha] at ha'
  cases ha'
  exact lt_irrefl _ hlt

theorem HotterThan.asymm {a b : Use} (h : HotterThan a b) : ¬ HotterThan b a := by
  obtain ⟨q, x, y, ha, hb, hlt⟩ := h
  rintro ⟨q', y', x', hb', ha', hlt'⟩
  rw [ha] at ha'; rw [hb] at hb'
  cases ha'; cases hb'
  exact absurd hlt (not_lt.2 hlt'.le)

theorem HotterThan.trans {a b c : Use} (h : HotterThan a b) (h' : HotterThan b c) :
    HotterThan a c := by
  obtain ⟨q, x, y, ha, hb, hxy⟩ := h
  obtain ⟨q', y', z, hb', hc, hyz⟩ := h'
  rw [hb] at hb'
  cases hb'
  exact ⟨q, x, z, ha, hc, hyz.trans hxy⟩

/-- With both readings in hand the comparative is just a comparison of exact
rationals. -/
theorem hotterThan_iff_of_readings {a b : Use} {q : String} {x y : ℚ}
    (ha : reading a = some (q, x)) (hb : reading b = some (q, y)) :
    HotterThan a b ↔ y < x := by
  constructor
  · rintro ⟨q', u, v, hu, hv, hlt⟩
    rw [ha] at hu; rw [hb] at hv
    cases hu; cases hv
    exact hlt
  · intro hlt; exact ⟨q, x, y, ha, hb, hlt⟩

/-- And the equative is equality of them. -/
theorem asHotAs_iff_of_readings {a b : Use} {q : String} {x y : ℚ}
    (ha : reading a = some (q, x)) (hb : reading b = some (q, y)) :
    AsHotAs a b ↔ x = y := by
  constructor
  · rintro ⟨q', u, hu, hv⟩
    rw [ha] at hu; rw [hb] at hv
    cases hu; cases hv
    rfl
  · rintro rfl; exact ⟨q, x, ha, hb⟩

/-- **Trichotomy.**  A comparable pair stands in exactly one of the three
relations, so a comparative question about two measured uses of one quantity
always has an answer -- and the machine never has to guess which. -/
theorem hotterThan_trichotomy {a b : Use} (h : Comparable a b) :
    (HotterThan a b ∧ ¬ AsHotAs a b ∧ ¬ HotterThan b a) ∨
    (AsHotAs a b ∧ ¬ HotterThan a b ∧ ¬ HotterThan b a) ∨
    (HotterThan b a ∧ ¬ AsHotAs a b ∧ ¬ HotterThan a b) := by
  obtain ⟨q, x, y, ha, hb⟩ := h
  have hab := hotterThan_iff_of_readings ha hb
  have hba := hotterThan_iff_of_readings hb ha
  have heq := asHotAs_iff_of_readings ha hb
  rcases lt_trichotomy x y with hxy | hxy | hxy
  · exact Or.inr (Or.inr ⟨hba.2 hxy, fun h => absurd (heq.1 h) (ne_of_lt hxy),
      fun h => absurd (hab.1 h) (not_lt.2 hxy.le)⟩)
  · exact Or.inr (Or.inl ⟨heq.2 hxy, fun h => absurd (hab.1 h) (by rw [hxy]; exact lt_irrefl _),
      fun h => absurd (hba.1 h) (by rw [hxy]; exact lt_irrefl _)⟩)
  · exact Or.inl ⟨hab.2 hxy, fun h => absurd (heq.1 h) (ne_of_gt hxy),
      fun h => absurd (hba.1 h) (not_lt.2 hxy.le)⟩

/-! ## What the word order does and does not decide -/

/-- **Inside one class the two orders agree, and exactly agree.**  For a
nondegenerate bracket, one use of a class is hotter than another exactly when
its word is higher on the scale.  This is `above_on_magnitude_lt`, promoted to
the comparative. -/
theorem hotterThan_iff_position_lt {v w : MeasureWord} {c : CompClass} {q : String}
    (hv : v.quantity = some q) (hw : w.quantity = some q) (hc : c.quantity = q)
    (hlow : c.low < c.high) :
    HotterThan ⟨v, some c⟩ ⟨w, some c⟩ ↔ w.position < v.position := by
  rw [hotterThan_iff_of_readings (reading_of_match hv hc) (reading_of_match hw hc)]
  exact (magnitude_strictMono hlow).lt_iff_lt

/-- The use *cold, for a stellar surface*. -/
def coldStar : Use := ⟨cold, some stellarSurface⟩

/-- The use *hot, for a cup of tea*. -/
def hotTea : Use := ⟨hot, some tea⟩

/-- The use *hot, for a stellar surface*. -/
def hotStar : Use := ⟨hot, some stellarSurface⟩

/-- **The comparative reverses the scale order across classes.**  *Cold*, for a
star, is 8000 K; *hot*, for a cup of tea, is 363 K. -/
theorem coldStar_hotterThan_hotTea : HotterThan coldStar hotTea := by
  refine ⟨"temperature", 8000, 363, ?_, ?_, by norm_num⟩
  · simp [coldStar, reading, measurement, cold, stellarSurface, CompClass.magnitude]
    norm_num
  · simp [hotTea, reading, measurement, hot, tea, CompClass.magnitude]
    norm_num

/-- And `cold` is below `hot` on the scale, so the comparative between uses is
**not** a function of the two words: the class is load-bearing, and a machine
that read only the concepts would get this pair backwards. -/
theorem comparative_not_determined_by_word_order :
    ∃ a b : Use, a.word.position < b.word.position ∧ HotterThan a b :=
  ⟨coldStar, hotTea, by norm_num [coldStar, hotTea, cold, hot],
    coldStar_hotterThan_hotTea⟩

/-- Beside it, the pair that does obey the scale: within the tea class, `hot`
is hotter than `cold`. -/
theorem hotTea_hotterThan_coldTea : HotterThan hotTea ⟨cold, some tea⟩ := by
  refine (hotterThan_iff_position_lt (v := hot) (w := cold) (c := tea)
    rfl rfl rfl (by norm_num [tea])).2 ?_
  norm_num [hot, cold]

/-! ## The static reading cannot answer, and the measure view can -/

/-- The lexicon conflates the two uses of `hot`: to the static layer they are
one thing. -/
theorem staticLayer_indist_hot_uses : staticLayer.Indist hotTea hotStar := rfl

/-- Yet one is hotter than the other -- 44 000 K against 363 K. -/
theorem hotStar_hotterThan_hotTea : HotterThan hotStar hotTea := by
  refine ⟨"temperature", 44000, 363, ?_, ?_, by norm_num⟩
  · simp [hotStar, reading, measurement, hot, stellarSurface, CompClass.magnitude]
    norm_num
  · simp [hotTea, reading, measurement, hot, tea, CompClass.magnitude]
    norm_num

/-- **So the comparative is not a function of the static reading.**  There are
uses the lexicon cannot tell apart that stand on opposite sides of the
comparative: the question *which is hotter?* is unanswerable at the static
layer, whatever else is done there. -/
theorem comparative_not_static :
    ∃ a b c : Use, staticLayer.Indist a b ∧ HotterThan a c ∧ ¬ HotterThan b c :=
  ⟨hotStar, hotTea, hotTea, rfl, hotStar_hotterThan_hotTea, hotterThan_irrefl hotTea⟩

/-- **The measure view is enough.**  The comparative respects
indistinguishability at `measureLayer`, so the widening -- and no more than it
-- supplies exactly what the comparative needs. -/
theorem hotterThan_congr {a a' b b' : Use} (ha : measureLayer.Indist a a')
    (hb : measureLayer.Indist b b') : HotterThan a b ↔ HotterThan a' b' := by
  have ha' : measurement a = measurement a' := (measureLayer_indist_iff.1 ha).2
  have hb' : measurement b = measurement b' := (measureLayer_indist_iff.1 hb).2
  have hra : reading a = reading a' := by unfold reading; rw [ha']
  have hrb : reading b = reading b' := by unfold reading; rw [hb']
  unfold HotterThan
  rw [hra, hrb]

/-- The same for the equative. -/
theorem asHotAs_congr {a a' b b' : Use} (ha : measureLayer.Indist a a')
    (hb : measureLayer.Indist b b') : AsHotAs a b ↔ AsHotAs a' b' := by
  have ha' : measurement a = measurement a' := (measureLayer_indist_iff.1 ha).2
  have hb' : measurement b = measurement b' := (measureLayer_indist_iff.1 hb).2
  have hra : reading a = reading a' := by unfold reading; rw [ha']
  have hrb : reading b = reading b' := by unfold reading; rw [hb']
  unfold AsHotAs
  rw [hra, hrb]

/-! ## The refusals, and why they are forced -/

/-- An unmeasured use is comparable with nothing at all. -/
theorem not_comparable_left_of_unmeasured {a b : Use} (ha : measurement a = none) :
    ¬ Comparable a b := by
  rintro ⟨q, x, y, ha', -⟩
  rw [reading_none_iff.2 ha] at ha'
  simp at ha'

theorem not_comparable_right_of_unmeasured {a b : Use} (hb : measurement b = none) :
    ¬ Comparable a b := fun h => not_comparable_left_of_unmeasured hb h.symm

/-- Hence no comparative and no equative there either: *is large hotter than
hot?* has no answer, and the runtime declines. -/
theorem not_hotterThan_of_unmeasured {a b : Use} (ha : measurement a = none) :
    ¬ HotterThan a b := fun h => not_comparable_left_of_unmeasured ha h.comparable

/-- A word whose quantity the registers do not hold is such a use, whatever
class it is put against: `large` again. -/
theorem not_comparable_of_no_quantity {a b : Use} (ha : a.word.quantity = none) :
    ¬ Comparable a b :=
  not_comparable_left_of_unmeasured (measurement_eq_none_of_no_quantity ha)

/-- The word `fast`, on the velocity scale. -/
def fast : MeasureWord := ⟨"fast", some "velocity", 7/8⟩

/-- The comparison class *walking*: 0 to 2 m/s. -/
def walking : CompClass := ⟨"walking", "velocity", 0, 2⟩

/-- The use *fast, for walking*: perfectly well measured -- 7/4 m/s. -/
def fastWalking : Use := ⟨fast, some walking⟩

theorem fastWalking_reading : reading fastWalking = some ("velocity", 7/4) := by
  simp [fastWalking, reading, measurement, fast, walking, CompClass.magnitude]
  norm_num

/-- The general statement: readings of different quantities never compare. -/
theorem not_comparable_of_quantity_ne {a b : Use} {q r : String} {x y : ℚ}
    (ha : reading a = some (q, x)) (hb : reading b = some (r, y)) (hqr : q ≠ r) :
    ¬ Comparable a b := by
  rintro ⟨s, u, v, ha', hb'⟩
  rw [ha] at ha'; rw [hb] at hb'
  have h1 : q = s := congrArg (fun o => (o.getD ("", 0)).1) ha'
  have h2 : r = s := congrArg (fun o => (o.getD ("", 0)).1) hb'
  exact hqr (h1.trans h2.symm)

theorem hotTea_reading : reading hotTea = some ("temperature", 363) := by
  simp [hotTea, reading, measurement, hot, tea, CompClass.magnitude]
  norm_num

/-- **Two measured uses of different quantities are still incomparable.**  Both
sides name an exact magnitude and the comparative still has no answer, because
there is no scale the two magnitudes are on.  This refusal is not a missing
measurement; it is what *comparable* means. -/
theorem hotTea_not_comparable_fastWalking : ¬ Comparable hotTea fastWalking :=
  not_comparable_of_quantity_ne hotTea_reading fastWalking_reading (by decide)

end GLM.Info
