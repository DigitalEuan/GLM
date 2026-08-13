import Mathlib
import RequestProject.IntegerCube
import RequestProject.WideInteger
import RequestProject.Grounding

/-!
# Continuous quantities: readings that are not a six-point scale

`FINAL_REPORT.md` §8 item 3:

> **Continuous quantities.**  Temperatures are four steps and masses two.  Real
> ranges would change the Zipf head, and would make the dimensional layer do
> work it currently only stands ready to do.

Here the readings are arbitrary integers — a thermometer with no top and no
bottom, and a scale with no ceiling — so a world is a point of `ℤ²ⁿ` rather
than of an 18-point grid.  Two things follow immediately, and they are the two
halves of this file.

## 1. The old vocabulary cannot see a continuum

`thresholds_depend_only_on_band` — the four temperature words together take only
**four** distinct truth-patterns over the whole of `ℤ`: whatever the reading,
the language sees which of `(−∞, 0]`, `(0, 60)`, `[60, 100)`, `[100, ∞)` it lies
in and nothing more.  `twenty_and_twentyone_agree` is the concrete casualty:
20 °C and 21 °C satisfy exactly the same words.  A finer scale buys the old
lexicon nothing at all, which is why the six-point scale of `WideWorld.lean` was
not the limitation it looked like.

## 2. So the language has to grade, and then the arithmetic layer does real work

`CAtom.hotterBy e f k` is *"`e` is at least `k` degrees hotter than `f`"* — a
word with a number in it.  With it:

* `graded_separates` — any two distinct differences are told apart, so the
  graded language distinguishes infinitely many states where the thresholds
  distinguish four;
* `strongest_grade_is_exact` — the strongest true grade is exactly the
  difference of the two readings, so one graded sentence *determines* what the
  thermometers said, and `strongest_grade_determines_difference` says the hearer
  can recover it;
* `claws_sound` — the law schemas (*boiling ⇒ hot*, *frozen ⇒ not warm*,
  *massive ⇒ heavy*, and the graded monotonicity laws) hold for **every**
  integer reading, proved by arithmetic.  There is no 18-state reduction here
  and none is needed: `WideWorld.checkAll` cannot be used on a continuum, and
  the schematic method is what survives.

## 3. What the substrate now has to pay for

A graded sentence carries a magnitude, and a magnitude has to be stored.  On one
MOG column — four cells, one face of the cube — an integer round-trips exactly
when it lies in `[−8, 7]` (`difference_roundtrip_iff_window`), and outside that
window the cube does not fail loudly: it reports a *different* difference
(`twenty_reads_as_four`).  A pair of records widens the window to `[−128, 127]`
and no further (`difference_roundtrip2_iff_window`, `window_is_sharp`), and no
encoding into a fixed number of cells is faithful on all of `ℤ`
(`WideInteger.no_faithful_pair`).  The language below takes the pair window as
its budget.

**This is the honest cost of continuity**: the meaning layer is now unbounded
while the substrate is not, so a graded claim is exact only inside a stated
window, and the system must either keep the claim in the window or say nothing.
`sayGrade` does the second: it states the exact gap when the pair of records can
hold it (`sayGrade_sound`) and returns nothing when it cannot
(`sayGrade_none_iff`), which `demoC_facts` exercises on a furnace 479 degrees
above the room.  `sayable` and `sayable_is_exact` make that discipline part of
the language rather than a caveat about it.

The dimensional layer finally does work rather than standing ready: a difference
of temperatures is a temperature (`difference_is_well_typed`), and comparing it
with a difference of masses is a category error the cube charges at least `8·Q`
for (`Grounding.category_error_is_rejected`).
-/

namespace Continuous

open Grounding IntegerCube CubeMOG

set_option maxRecDepth 100000

/-! ## 1. Worlds with real ranges -/

/-- A world of `n` things, each with an integer temperature (°C) and an integer
mass (kg).  No scale, no grid: the state space is `ℤ^(2n)`. -/
abbrev CWorld (n : ℕ) := Fin n → ℤ × ℤ

/-- The measured temperature. -/
def ctemp {n} (w : CWorld n) (e : Fin n) : ℤ := (w e).1

/-- The measured mass. -/
def cmass {n} (w : CWorld n) (e : Fin n) : ℤ := (w e).2

/-- The vocabulary: the old thresholds and comparisons, plus **graded**
comparatives that carry a number. -/
inductive CAtom (n : ℕ)
  | frozen (e : Fin n)
  | warm (e : Fin n)
  | hot (e : Fin n)
  | boiling (e : Fin n)
  | heavy (e : Fin n)
  | massive (e : Fin n)
  | hotter (e f : Fin n)
  | heavier (e f : Fin n)
  | hotterBy (e f : Fin n) (k : ℤ)
  | heavierBy (e f : Fin n) (k : ℤ)

/-- Truth is still measurement. -/
def evalCA {n} : CAtom n → CWorld n → Bool
  | .frozen e, w => decide (ctemp w e ≤ 0)
  | .warm e, w => decide (0 < ctemp w e ∧ ctemp w e < 100)
  | .hot e, w => decide (60 ≤ ctemp w e)
  | .boiling e, w => decide (100 ≤ ctemp w e)
  | .heavy e, w => decide (10 ≤ cmass w e)
  | .massive e, w => decide (100 ≤ cmass w e)
  | .hotter e f, w => decide (ctemp w f < ctemp w e)
  | .heavier e f, w => decide (cmass w f < cmass w e)
  | .hotterBy e f k, w => decide (k ≤ ctemp w e - ctemp w f)
  | .heavierBy e f k, w => decide (k ≤ cmass w e - cmass w f)

/-! ## 2. The threshold vocabulary sees four bands and no more -/

/-- Which of the four temperature bands a reading lies in. -/
def band (t : ℤ) : Fin 4 := if t ≤ 0 then 0 else if t < 60 then 1 else if t < 100 then 2 else 3

/-- **Resolution.**  The four temperature words depend on the reading only
through its band: over the whole of `ℤ` they take four truth-patterns.  A
continuum of readings is invisible to them. -/
theorem thresholds_depend_only_on_band {n} (w w' : CWorld n) (e : Fin n)
    (h : band (ctemp w e) = band (ctemp w' e)) :
    evalCA (.frozen e) w = evalCA (.frozen e) w' ∧
    evalCA (.warm e) w = evalCA (.warm e) w' ∧
    evalCA (.hot e) w = evalCA (.hot e) w' ∧
    evalCA (.boiling e) w = evalCA (.boiling e) w' := by
  simp only [band] at h
  split_ifs at h with h1 h2 h3 h4 h5 h6 h7 h8 h9 h10 h11 h12 <;>
    simp only [evalCA, decide_eq_decide] <;>
      refine ⟨by omega, by omega, by omega, by omega⟩

/-- The concrete casualty: 20 °C and 21 °C satisfy exactly the same words of the
old lexicon. -/
theorem twenty_and_twentyone_agree :
    let w : CWorld 1 := fun _ => (20, 0)
    let w' : CWorld 1 := fun _ => (21, 0)
    evalCA (.frozen 0) w = evalCA (.frozen 0) w' ∧
    evalCA (.warm 0) w = evalCA (.warm 0) w' ∧
    evalCA (.hot 0) w = evalCA (.hot 0) w' ∧
    evalCA (.boiling 0) w = evalCA (.boiling 0) w' := by
  refine ⟨by decide, by decide, by decide, by decide⟩

/-! ## 3. Grading, and what it buys -/

/-- **Grading separates the continuum.**  Any two distinct differences are told
apart by some graded word, so the graded language distinguishes infinitely many
states where the thresholds distinguish four. -/
theorem graded_separates {n} (w w' : CWorld n) (e f : Fin n)
    (h : ctemp w e - ctemp w f ≠ ctemp w' e - ctemp w' f) :
    ∃ k : ℤ, evalCA (.hotterBy e f k) w ≠ evalCA (.hotterBy e f k) w' := by
  rcases lt_or_gt_of_ne h with hlt | hgt
  · exact ⟨ctemp w' e - ctemp w' f, by simp only [evalCA, ne_eq, decide_eq_decide]; omega⟩
  · exact ⟨ctemp w e - ctemp w f, by simp only [evalCA, ne_eq, decide_eq_decide]; omega⟩

/-- The true grades are exactly the ones at or below the difference. -/
theorem graded_iff {n} (w : CWorld n) (e f : Fin n) (k : ℤ) :
    evalCA (.hotterBy e f k) w = true ↔ k ≤ ctemp w e - ctemp w f := by
  simp [evalCA]

/-- **The strongest true grade is the difference itself** — so a graded sentence
does not approximate the reading, it pins it. -/
theorem strongest_grade_is_exact {n} (w : CWorld n) (e f : Fin n) :
    evalCA (.hotterBy e f (ctemp w e - ctemp w f)) w = true ∧
    ∀ k : ℤ, evalCA (.hotterBy e f k) w = true → k ≤ ctemp w e - ctemp w f := by
  refine ⟨by simp [evalCA], fun k hk => (graded_iff w e f k).mp hk⟩

/-- …and the hearer can recover the difference from it: the strongest true grade
determines the two readings' gap exactly. -/
theorem strongest_grade_determines_difference {n} (w w' : CWorld n) (e f : Fin n)
    (h : ∀ k : ℤ, evalCA (.hotterBy e f k) w = evalCA (.hotterBy e f k) w') :
    ctemp w e - ctemp w f = ctemp w' e - ctemp w' f := by
  by_contra hne
  obtain ⟨k, hk⟩ := graded_separates w w' e f hne
  exact hk (h k)

/-! ## 4. The laws, for every reading -/

/-- **The law schemas hold on the continuum**, proved by arithmetic rather than
by checking states — there are infinitely many states to check. -/
theorem claws_sound {n} (w : CWorld n) (e f g : Fin n) :
    (evalCA (.boiling e) w = true → evalCA (.hot e) w = true) ∧
    (evalCA (.boiling e) w = true → evalCA (.warm e) w = false) ∧
    (evalCA (.frozen e) w = true → evalCA (.warm e) w = false) ∧
    (evalCA (.frozen e) w = true → evalCA (.hot e) w = false) ∧
    (evalCA (.massive e) w = true → evalCA (.heavy e) w = true) ∧
    (evalCA (.hotter e f) w = true → evalCA (.hotter f g) w = true →
      evalCA (.hotter e g) w = true) ∧
    (evalCA (.hotter e f) w = true → evalCA (.hotter f e) w = false) := by
  simp only [evalCA, decide_eq_true_eq, decide_eq_false_iff_not]
  refine ⟨by omega, by omega, by omega, by omega, by omega, by omega, by omega⟩

/-- The graded laws: a stronger grade implies a weaker one, and a positive grade
implies the plain comparative. -/
theorem graded_laws {n} (w : CWorld n) (e f : Fin n) (j k : ℤ) :
    (j ≤ k → evalCA (.hotterBy e f k) w = true → evalCA (.hotterBy e f j) w = true) ∧
    (0 < k → evalCA (.hotterBy e f k) w = true → evalCA (.hotter e f) w = true) := by
  simp only [evalCA, decide_eq_true_eq]
  exact ⟨fun hjk hk => by omega, fun hk h => by omega⟩

/-! ## 5. What the substrate can store -/

/-- A magnitude, written on one MOG column: four cells, one face of the cube. -/
def storeDiff (d : ℤ) : Col := colOfInt d

/-- Reading it back. -/
def readDiff (c : Col) : ℤ := intOfCol c

/-- **The substrate has a window.**  A difference round-trips through one column
exactly when it lies in `[−8, 7]`; the cube's arithmetic is exact there and
modular outside. -/
theorem difference_roundtrip_iff_window (d : ℤ) :
    readDiff (storeDiff d) = d ↔ InWindow d := by
  constructor
  · intro h
    have hr := intOfCol_range (storeDiff d)
    rw [readDiff] at h
    exact ⟨by omega, by omega⟩
  · intro h
    exact intOfCol_colOfInt_of_window h

/-- **And it does not fail loudly.**  A gap of 20 degrees is stored and read
back as a gap of 4: the cube reports a different difference rather than an
error.  This is the `Int.bmod` of `IntegerCube.intOfCol_colOfInt`, now visible
as a semantic fact about what the system can say. -/
theorem twenty_reads_as_four : readDiff (storeDiff 20) = 4 := by
  rw [readDiff, storeDiff, intOfCol_colOfInt]; decide

/-- The same magnitude written across *two* faces, as in `WideInteger.lean`. -/
def storeDiff2 (d : ℤ) : CubeMOG.Col × CubeMOG.Col := WideInteger.pack (BitVec.ofInt 8 d)

/-- Reading it back. -/
def readDiff2 (p : CubeMOG.Col × CubeMOG.Col) : ℤ := (WideInteger.unpack p.1 p.2).toInt

theorem readDiff2_storeDiff2 (d : ℤ) : readDiff2 (storeDiff2 d) = Int.bmod d 256 := by
  rw [readDiff2, storeDiff2, WideInteger.unpack_pack, BitVec.toInt_ofInt]

theorem readDiff2_range (p : CubeMOG.Col × CubeMOG.Col) :
    -128 ≤ readDiff2 p ∧ readDiff2 p ≤ 127 := by
  revert p; decide

/-- **Two faces widen the window to `[−128, 127]`, and no further.** -/
theorem difference_roundtrip2_iff_window (d : ℤ) :
    readDiff2 (storeDiff2 d) = d ↔ WideInteger.InWindow8 d := by
  constructor
  · intro h
    have hr := readDiff2_range (storeDiff2 d)
    exact ⟨by omega, by omega⟩
  · intro h
    rw [readDiff2_storeDiff2, WideInteger.bmod_self_of_window8 h]

/-- A graded claim the system is entitled to make: one whose magnitude the
substrate can hold exactly on a pair of records. -/
def sayable (d : ℤ) : Bool := decide (-128 ≤ d ∧ d ≤ 127)

/-- **The discipline, stated rather than assumed**: every claim the system calls
sayable round-trips exactly, so a hearer decoding the cube recovers the number
that was meant. -/
theorem sayable_is_exact (d : ℤ) (h : sayable d = true) : readDiff2 (storeDiff2 d) = d := by
  rw [difference_roundtrip2_iff_window]
  simp only [sayable, decide_eq_true_eq] at h
  exact ⟨h.1, h.2⟩

/-- The window is sharp at both widths: one face reads 8 back as −8, and a pair
of faces reads 128 back as −128. -/
theorem window_is_sharp :
    readDiff (storeDiff 8) = -8 ∧ sayable 128 = false ∧ readDiff2 (storeDiff2 128) = -128 := by
  refine ⟨?_, by decide, ?_⟩
  · rw [readDiff, storeDiff, intOfCol_colOfInt]; decide
  · rw [readDiff2_storeDiff2]; decide

/-- **A pair of records widens the window and does not remove it.**  With two
columns the exact range is `[−128, 127]` (`WideInteger.pair_window_is_256`), and
no encoding of `ℤ⁶` into a pair of records is injective — so on a continuum the
substrate always has a blind spot, whatever the layout. -/
theorem substrate_always_has_a_blind_spot (F : MeasuredWords.Dim → WideInteger.Pair) :
    ¬ Function.Injective F := WideInteger.no_faithful_pair F

/-! ## 6. The dimensional layer, doing work -/

/-- A comparison of two dimensioned readings of a continuous world, in the
style of `Grounding.Comparison`. -/
structure CComparison (n : ℕ) where
  /-- The larger side. -/
  left : CWorld n → ℤ
  /-- Its dimension. -/
  leftDim : MeasuredWords.Dim
  /-- The smaller side. -/
  right : CWorld n → ℤ
  /-- Its dimension. -/
  rightDim : MeasuredWords.Dim
  /-- Whether the comparison is strict. -/
  strict : Bool

/-- Its truth. -/
def evalCComp {n} (c : CComparison n) (w : CWorld n) : Bool :=
  if c.strict then decide (c.right w < c.left w) else decide (c.right w ≤ c.left w)

/-- **What each word of the continuous language actually measures.**  The graded
words compare a *difference* of readings with the number they carry. -/
def compsOfCA {n} : CAtom n → List (CComparison n)
  | .frozen e => [⟨fun _ => 0, temperatureDim, fun w => ctemp w e, temperatureDim, false⟩]
  | .warm e => [⟨fun w => ctemp w e, temperatureDim, fun _ => 0, temperatureDim, true⟩,
      ⟨fun _ => 100, temperatureDim, fun w => ctemp w e, temperatureDim, true⟩]
  | .hot e => [⟨fun w => ctemp w e, temperatureDim, fun _ => 60, temperatureDim, false⟩]
  | .boiling e => [⟨fun w => ctemp w e, temperatureDim, fun _ => 100, temperatureDim, false⟩]
  | .heavy e => [⟨fun w => cmass w e, massDim, fun _ => 10, massDim, false⟩]
  | .massive e => [⟨fun w => cmass w e, massDim, fun _ => 100, massDim, false⟩]
  | .hotter e f => [⟨fun w => ctemp w e, temperatureDim, fun w => ctemp w f,
      temperatureDim, true⟩]
  | .heavier e f => [⟨fun w => cmass w e, massDim, fun w => cmass w f, massDim, true⟩]
  | .hotterBy e f k => [⟨fun w => ctemp w e - ctemp w f, temperatureDim, fun _ => k,
      temperatureDim, false⟩]
  | .heavierBy e f k => [⟨fun w => cmass w e - cmass w f, massDim, fun _ => k, massDim, false⟩]

/-- **The unpacking is faithful**: a word is true exactly when the comparisons it
performs hold. -/
theorem compsOfCA_correct {n} (a : CAtom n) (w : CWorld n) :
    evalCA a w = (compsOfCA a).all fun c => evalCComp c w := by
  cases a <;> simp [evalCA, compsOfCA, evalCComp, Bool.decide_and]

/-- **A difference of temperatures is a temperature**, and every comparison the
continuous language performs — including the graded ones, which compare a
difference with a number — is between like and like. -/
theorem difference_is_well_typed {n} (a : CAtom n) :
    ∀ c ∈ compsOfCA a, c.leftDim = c.rightDim := by
  cases a <;> intro c hc <;> simp [compsOfCA] at hc <;>
    rcases hc with rfl | rfl <;> rfl

/-- …so the cube accepts every one of them for nothing. -/
theorem continuous_comparisons_are_free {n} (a : CAtom n) :
    ∀ c ∈ compsOfCA a, MeasuredWords.taxOf c.leftDim c.rightDim = 0 := fun c hc => by
  rw [difference_is_well_typed a c hc]
  exact MeasuredWords.taxOf_accepted _ _ rfl

/-- …while grading a temperature against a mass is the category error the cube
charges for.  With a six-point scale this discipline never had to do anything;
on a continuum it is what stops *"the water is 20 kilograms hotter than the
stone"*. -/
theorem grading_across_dimensions_is_rejected :
    IntegerCube.encG temperatureDim ≠ IntegerCube.encG massDim ∧
      8 * GolayHex.Q ≤ MeasuredWords.taxOf temperatureDim massDim :=
  Grounding.category_error_is_rejected

/-! ## 7. Speaking about a continuum, and refusing when it cannot -/

/-- The graded claim the system is willing to make about a pair: the exact
difference when the substrate can hold it, and *nothing* when it cannot.  The
system never states a magnitude it would store wrongly. -/
def sayGrade {n} (w : CWorld n) (e f : Fin n) : Option ℤ :=
  let d := ctemp w e - ctemp w f
  if sayable d then some d else none

/-- **Whatever it says is true and survives the cube.** -/
theorem sayGrade_sound {n} (w : CWorld n) (e f : Fin n) {d : ℤ}
    (h : sayGrade w e f = some d) :
    evalCA (.hotterBy e f d) w = true ∧ readDiff2 (storeDiff2 d) = d := by
  simp only [sayGrade] at h
  split_ifs at h with hs
  · cases h
    exact ⟨by simp [evalCA], sayable_is_exact _ hs⟩

/-- **And when it says nothing, that is because the gap is outside the window**
— a refusal, not a mistake. -/
theorem sayGrade_none_iff {n} (w : CWorld n) (e f : Fin n) :
    sayGrade w e f = none ↔ ¬ WideInteger.InWindow8 (ctemp w e - ctemp w f) := by
  simp only [sayGrade, sayable, WideInteger.InWindow8]
  split_ifs with hs <;> simp_all [decide_eq_true_eq]

/-- A world with a real range in it: a furnace at 500 °C, a room at 21 °C and
ice at −5 °C. -/
def demoC : CWorld 3 := ![(500, 300), (21, 2), (-5, 1)]

/-- **The demonstration.**  The furnace is boiling and hot, the ice is frozen;
the room is 26 degrees warmer than the ice and the system says so exactly; the
gap between the furnace and the room is 479 degrees, which even a pair of
records cannot hold, so the system declines to state it rather than storing a
number that would read back wrong. -/
theorem demoC_facts :
    evalCA (.boiling 0) demoC = true ∧
    evalCA (.frozen 2) demoC = true ∧
    evalCA (.warm 1) demoC = true ∧
    sayGrade demoC 1 2 = some 26 ∧
    sayGrade demoC 0 1 = none ∧
    ctemp demoC 0 - ctemp demoC 1 = 479 := by
  refine ⟨by decide, by decide, by decide, ?_, ?_, by decide⟩
  · decide
  · decide

end Continuous
