# Measure words as relative measures — the widening, measured

*What `data_objects/comparison_classes.py`, `reasoning/measure_view.py`,
`RequestProject/GLM/MeasureView.lean` and the `measure` query are for, and what
they measured.*

This is the result document for steps 2–5 of
[`RELATIVE_MEASURE_PROPOSAL.md`](RELATIVE_MEASURE_PROPOSAL.md). That document
is a proposal and says so; this one reports what was built and what it
measures. Every figure below is recomputed by the code that reports it. Run

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report measure" --verify-tct
```

and the third column re-derives the whole study in a fresh interpreter and
checks it key by key (`VERIFIED True`).

---

## 1. The question

`hot` is a `SemanticConcept`: ten primitives, a part of speech, and four
relations, one of which is `property_of temperature`. That reading says which
quantity the word is about and which pole of it the word names. It cannot say
**how hot** — and no amount of resolution in the carrier would let it, because
*hot* is not a temperature. Hot for a cup of tea is 363 K; hot for a stellar
surface is 44 000 K. What the static reading is missing is not precision but a
**comparison class**.

`STATUS.md` §3.2 recorded this as an open limitation: "`hot` is a standalone
concept, not 'temperature at high scale'". The proposal's §2 argued that the
fix must be a **widening** — the relative reading added *beside* the static one
and never in place of it — reusing the decision the layer chain had already
forced. This study is that argument carried out, and the widening is now a
number rather than a preference.

## 2. The comparison-class register (step 3)

`data_objects/comparison_classes.py` holds **45 comparison classes over 11
quantities**:

| quantity | classes |
|---|---|
| temperature | 6 |
| length | 5 |
| mass | 5 |
| velocity | 5 |
| volume | 5 |
| density | 4 |
| illuminance | 4 |
| force | 3 |
| luminous_intensity | 3 |
| pressure | 3 |
| frequency | 2 |

The last three quantities — volume, illuminance and luminous intensity — were
added after the first round of this study, which is why §3 below no longer has
any unmeasurable adjective to report. Seven further names are **aliases** that
resolve to one of the eleven (`size` → `volume`, `light` → `illuminance`,
`distance` → `length`, `weight` → `force`, and so on) and supply no coordinate
of their own; `alias_audit()` checks that each one resolves to a quantity the
register holds.

A class is a name, a quantity, and an exact bracket `[low, high]` in the SI
base unit of that quantity, with a typical magnitude inside it. Every number
is a `Fraction`; no float is constructed anywhere in the module.

The register is **derived, not typed twice**. A class names a quantity, and
the dimension, the unit and the ten EXT10 exponents that go into its 24-
coordinate carrier are read out of the physics register at load time — a class
naming a quantity the register does not hold fails to load, which
`test_comparison_classes.py` exercises. This is the same rule the molecules
register already follows.

Beside the classes are **11 measure scales carrying 64 degree words**, each word
at an exact position in `[0, 1]`: *freezing, cold, cool, tepid, warm, hot,
scalding* on the temperature scale, and so on. A word's magnitude in a class is

```
magnitude = low + position * (high - low)
```

evaluated in exact rationals. `ComparisonClassCodec` encodes a class to its
24-coordinate carrier and reads it back; the round trip is checked for all 45.

### 2.1 The scales are checked against the lexicon

Twelve of the 64 degree words are also lexicon concepts, and where the two
registers overlap they must agree. `lexicon_agreement()` checks three things
and reports `agrees: True`:

* a shared word carries the quantity its concept's `property_of` relation
  names;
* it sits on the side of the scale midpoint its `positive_negative` primitive
  says;
* an `opposite_of` pair has positions summing to 1 — six pairs do
  (`hot`/`cold`, `fast`/`slow`, `heavy`/`light_adj`, `strong`/`weak`,
  `dense`/`sparse`, `large`/`small`).

One word is reported rather than passed silently: `heavy` has the **neutral**
polarity `1/2`, so the static reading cannot say it is the high pole of mass —
and the scale can, at `7/8`. That is a small, concrete instance of the gain the
whole exercise is about. A test breaks a scale position deliberately and
confirms the agreement check would notice.

## 3. What the widening gains (step 4)

`reasoning/measure_view.py` classifies the lexicon's **12 adjectives**: since
volume, illuminance and luminous intensity entered the register, **all 12 are
scaled** and none is left unmeasurable. That is a change from the first round,
when `large`, `small` and `dark` had no quantity to be measured against, and it
matters for the argument below — see §3.1.

The audit runs over the **56 uses** the registers admit — each of the 12 words
against each of the 32 classes of its quantity — and compares three views:

| view | what it sees | resolves |
|---|---|---|
| `static` | the concept carrier: ten primitives, the part of speech, four relation slots | **12 / 56** |
| `measure` | the concept carrier, and the measurement beside it | **56 / 56** |
| `measure_only` | the measurement alone — the design that was rejected | **56 / 56** |

**Measured:** the widening gains **108 pairs** and violates refinement **0**
times — the static view's largest conflated class holds 6 uses, and the measure
view's holds 1.

The audit's static view is not an idealisation of the layer stack: it is
checked against `dimension_layers`' rational layer on the concept carrier, pair
by pair, over all **1,540** pairs, and they agree.

### 3.1 What the rejected replacement costs, now that the data no longer shows it

On the shipped data the replacement reading — keep the measurement, drop the
concept — now also gains 108 pairs and violates refinement **0** times. That is
not a vindication of it: it is the register having stopped holding a word the
reading fails on. The first round's refutation was three unmeasurable words all
reading `none`, and supplying the *volume* and *illuminance* classes removed
exactly those three uses.

`replacement_witness()` keeps the cost measurable rather than letting it lapse.
It re-runs the same audit over the 56 uses **plus one unmeasured use of each of
the 12 words** — the case that arises the moment a word's quantity is not yet in
a register, which is where `large`, `small` and `dark` stood one round ago. Over
those **68 uses** the widening gains **164 pairs** with **0** violations, and
the replacement gains the same 164 and **violates refinement on 66 pairs**: it
conflates `heavy@-` with `fast@-` and every other pair of unmeasured uses, which
the lexicon tells apart. That is `LAYER_INTEGER_RAW`'s situation exactly, and it
is why the reading is added rather than substituted. The general statement is
not a measurement at all but a theorem —
`GLM.Info.measureReading_not_refines_staticLayer`.

### 3.2 The same statements, machine-checked

`RequestProject/GLM/MeasureView.lean` builds the three views on
`Cumulative.lean`'s `Layer` machinery — `measureLayer = cumulative staticLayer
measureReading` — and proves:

| theorem | what it says |
|---|---|
| `measureLayer_refines_staticLayer` | the widening gives up nothing |
| `measureLayer_least` | and adds no resolution beyond what keeping both readings forces |
| `boundary_measureLayer_staticLayer` | what it gains is exactly the pairs the static view conflates and the measurement splits |
| `hot_tea_star_mem_boundary` | the gain is not empty — *hot* in tea and *hot* for a star is such a pair |
| `staticLayer_conflates_hot_uses` | and the static view really does conflate it |
| `measureReading_not_refines_staticLayer` | the replacement reading loses information |
| `boundary_empty_of_unmeasured` | where there is no measurement the widening gains nothing |
| `magnitude_strictMono`, `above_on_magnitude_lt` | the scale order is an order on magnitudes, in every class at once |
| `measureLayer_separates_classes` | two classes of one word are separated, because the class travels in the reading |

`hot_tea_magnitude : tea.magnitude hot.position = 363` and
`hot_star_magnitude : ... = 44000` are the Python examples, checked by the
kernel.

## 4. The `related_to` residue (step 2)

`related_to` was the largest unspecific predicate in the lexicon: **66 of the
380 triples**, and the residue the analogy layer deliberately refuses to
transport. Two rules convert the ones the physics register can *decide*:

`same_dimension_as`
: both endpoints reach the same EXT10 exponent vector;

`differs_by`
: exactly one quantity of the 16-quantity factor basis carries one exponent
  vector to the other, and the triple records which and in which direction.

**Measured: 27 of the 66 convert** — 6 `same_dimension_as` and 21 `differs_by`
— and **39 remain**, each reported with the reason it was declined. Almost all
of those reasons are that one endpoint (`motion`, `magnitude`, `photon`, …)
reaches no dimension the physics register holds; one is that no single basis
quantity carries one dimension to the other. An attribution that could be made
in more than one way is refused rather than guessed. The point of the exercise
is to remove guesses from the register, not to add better ones.

## 5. The query, and its tested refusal (step 5)

`measure` is a query kind of its own — one of the runtime's 20, with
`comparative` (§5.1) added beside it afterwards. It has three shapes that
answer:

| query | answer |
|---|---|
| `measure hot in tea` | `363/1 K`, with the bracket, the position and the arithmetic |
| `measure hot` | the same word against all six temperature classes, from `70001/800 K` in a cryostat to `44000/1 K` on a stellar surface |
| `measure 300 in tea` | the other direction: `cold`, at `7/80` of the bracket |

and, at the boundary, refuses:

| query | why it refuses |
|---|---|
| `measure large in room` | `large` measures volume and `room` is a class of length |
| `measure dark in room` | `dark` measures illuminance; likewise |
| `measure hot in walking` | a temperature word against a velocity class |
| `measure expensive in market` | `expensive` is on no measure scale at all |

The refusal is not an omission. `boundary_empty_of_unmeasured` says the
widened view sees exactly what the static view sees between two unmeasured
uses, so there is nothing the query could add; answering would mean inventing a
coordinate. All four refusals are exercised — as unit tests in
`test_measure_words.py` and as `boundary` cases in the end-to-end CLI
evaluation, which drives them through a fresh interpreter.

`report measure` recomputes the whole study, and its Three Column Thinking
script re-derives every figure above and reports `VERIFIED True`.

### 5.1 The comparative, and why the class is load-bearing

The first round of this study recorded *hotter than* and *as hot as* as a gap:
`above_on` orders words on a scale, but a comparative is a relation between two
**uses**, not between two words, so nothing in the static reading could answer
one. It is now a query kind, `comparative`, recognised structurally rather than
by keyword — the marker is any comparative or equative built from a degree word
the register holds (`hotter than`, `warmer than`, `as hot as`, …), and the
direction is read off the word's position relative to the midpoint of its scale:

| query | answer |
|---|---|
| `is cold in stellar_surface hotter than hot in tea` | **yes** — `8000/1 K` against `363/1 K` |
| `is hot in tea warmer than cold in oven` | **yes** — `363/1 K` against `1325/4 K` |
| `is hot in tea as hot as hot in tea` | **yes**, the equative on one use |
| `is hot in tea hotter than fast in walking` | **refused** — temperature against velocity |
| `is hot in tea hotter than large in room` | **refused** — `large` measures volume, `room` brackets a length |

The first row is the point of the exercise: on the scale `cold` sits at `1/8`
and `hot` at `7/8`, so the word order says *no* and the magnitudes say *yes*.
**Measured** by `comparative_audit()`: of the 56 uses, **228 pairs** share a
quantity and are comparable; within one class the word order decides **24 of
24**, and across classes it gets **151 of 204** backwards. So the comparison
class is not a refinement of the answer — it is what decides it in the majority
of comparable pairs.

`RequestProject/GLM/Comparative.lean` is the machine-checked half:

| theorem | what it says |
|---|---|
| `hotterThan_irrefl`, `HotterThan.asymm`, `HotterThan.trans`, `hotterThan_trichotomy` | the comparative is a strict order where it is defined, and trichotomous on any comparable pair |
| `AsHotAs.symm`, `AsHotAs.trans`, `asHotAs_refl_iff` | the equative is an equivalence on measured uses |
| `hotterThan_iff_position_lt` | within one class the word order decides it, and exactly |
| `coldStar_hotterThan_hotTea`, `comparative_not_determined_by_word_order` | across classes it does not — *cold* for a star is hotter than *hot* for a cup of tea |
| `comparative_not_static` | the static reading cannot answer it: it conflates a pair the comparative separates |
| `hotterThan_congr` | the widened view can — the comparative is a function of `measureLayer` |
| `not_comparable_left_of_unmeasured`, `hotTea_not_comparable_fastWalking` | the two refusals are forced by the registers, not left undone |

## 6. What this does not do

* **Twelve adjectives, and no more.** All 12 of the lexicon's adjectives are
  now measurable, but only because the register grew to eleven quantities; a
  thirteenth adjective naming a twelfth quantity would be unmeasurable again,
  and `replacement_witness()` (§3.1) is what keeps that case measured rather
  than assumed away.
* **Two words, one class — not a general comparison.** The comparative of §5.1
  relates two *uses* of degree words the register holds. It does not compare
  arbitrary concepts, and it refuses across quantities rather than converting
  between them.
* **No new economic or ethical coordinate.** `measure expensive in market`
  refuses, and should keep refusing; the proposal's §3 scope table is unchanged
  by this work.
* **The classes are a register, and registers are judgements about ordinary
  cases.** A magnitude outside a class's bracket is reported as outside rather
  than clamped, because the class is a claim about ordinary cases and a value
  beyond it is a case the class does not cover.

## 7. Where to look

| file | what it holds |
|---|---|
| `overlay/glm_universal/data_objects/comparison_classes.py` | the 45 classes, the 11 scales, the codec, the lexicon agreement |
| `overlay/glm_universal/reasoning/measure_view.py` | the reading, the widening audit, the relation repair, the report |
| `overlay/glm_universal/runtime/session.py` | `_solve_measure` and the `report measure` subject |
| `overlay/glm_universal/tests/test_comparison_classes.py` | the register: derivation, exact arithmetic, codec round trip, agreement |
| `overlay/glm_universal/tests/test_measure_words.py` | the view: the reading, the audit figures, the repair, the refusals |
| `overlay/glm_universal/tests/test_comparative.py` | the comparative: the parse, the verdicts, the audit, the two refusals |
| `RequestProject/GLM/MeasureView.lean` | the widening, proved on `Cumulative.lean` |
| `RequestProject/GLM/Comparative.lean` | the comparative as a strict order, and what the word order cannot decide |
| [`RELATIVE_MEASURE_PROPOSAL.md`](RELATIVE_MEASURE_PROPOSAL.md) | the proposal these five steps come from |
| [`INFORMATION_LOSS_STUDY.md`](INFORMATION_LOSS_STUDY.md) §3.1 | the widen-rather-than-narrow decision reused here |
