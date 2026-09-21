# The ordering operation — one coordinate, two rows, and the refusal that is the point of it

## Tier 0 — the coarse read

**Question.** The field surface answered nine of ten held-and-unreachable probe questions and named the tenth as needing an operation rather than a surface. Built, what does that operation answer, and what must it refuse?

**Verdict.** It answers four of the seven comparisons declared before the run and refuses three, every one of the seven as declared, and the refusals are the result rather than fussiness: two readings of one coordinate are comparable only when they are readings on one scale, and a rescaling of one of them flips the comparison of the bare numbers. It closes the tenth question, so all ten questions the oracle called held and unreachable are now parsed.

**Deciding figure.** <!--figure:ordering-as-declared-->7<!--/figure--> of <!--figure:ordering-declared-count-->7<!--/figure--> comparisons came out as declared, under <!--figure:ordering-reasons-->3<!--/figure--> named refusal reasons; the probe splits <!--figure:ordering-parsed-before-->15<!--/figure--> → <!--figure:ordering-parsed-after-->16<!--/figure--> parsed.

**Recomputed by.** `glm_universal.reasoning.coordinate_order.comparison_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. What this round took, and from where

[`FIELD_SURFACE_STUDY.md`](FIELD_SURFACE_STUDY.md) §6 and §7 end with one
question left and a reason for leaving it. Of the twenty pre-registered probe
questions, ten were *held and unreachable*; the field surface closed nine, and
the tenth — *is energy more abstract than water?* — was declared unreachable
**before** that round ran. Its reason was not coverage but composition: a
field query returns one field of one row, and this question reads one
coordinate off *two* rows and orders them. Writing `field abstract_concrete of
energy` would have carried the fragment `energy` at its locus and passed
without answering anything, which is the false pass the locus rule exists to
refuse.

[`STATUS.md`](../STATUS.md) §3.4 then named the instrument that would close it
as the sharpest candidate for the next round: *an operation over two readings
of the same coordinate, with the refusal it must make when the two rows carry
the coordinate on different scales*. This study is that operation, and the
measurement of what it was worth.

The operation is `glm_universal.reasoning.coordinate_order`, reached by the
`ordering` query kind, and the proved half is
`RequestProject/GLM/CoordinateOrder.lean`.

## 2. What the operation is

Two names and two rows:

```
order abstract_concrete of energy and water      -- the verdict, the gap, the pole
order atomic_weight_u of carbon and oxygen       -- the same operation over a second table
```

Each side is a **reading**: a value, exactly, together with the **scale** it
was read on. The scale is the table and the field the value was read under,
written `table:field`, and it is what makes two readings comparable. That is
not a convention of convenience:

* a field name carries its unit in this system — `atomic_weight_u`,
  `boiling_point_K`, `covalent_radius_pm` — so two readings of one field of
  one table are in one unit by construction;
* and the same field name across two tables is *not* one scale. `line` is
  held both by the Lean address book and by the package's own source walk,
  and the line number of a Lean declaration is not comparable with the line
  number of a Python function.

Three things about a reading are deliberate.

**A coordinate held inside a mapping field is still addressed, not invented.**
The lexicon register keeps its ten semantic primitives as one mapping field,
`primitives`, rather than as ten fields, so `abstract_concrete` is a
coordinate a row *carries* and not a field the surface addresses. It is read
as a coordinate of the field that contains it, and the scale says so:
`carrier:lexicon:primitives.abstract_concrete`, which cannot be confused with
a field of that name. Tables are searched in the surface's own priority order
and, within a row, containing fields in sorted order, so the reading is
determinate.

**A label is not a reading.** A value the surface holds which is not a number
— a name, a formula, a part of speech — has no order to read, and asking for
one is refused rather than answered on the spelling. `True` is excluded with
the labels: it is an `int` in Python and a label in this system.

**Exactness is not negotiable.** Values cross as `Fraction`, the gap is their
exact difference, and the only string shape read as a number is a written
rational (`3`, `-3`, `1/4`). No float is constructed anywhere in the module,
which is directive D7 and is checked statically by a test.

The verdict names a **pole** only where the register declares one. The lexicon
register documents both ends of each of its ten primitives — `0` is
*abstract*, `1` is *concrete* — so the answer to the probe question can say
which row is the more abstract. That the coordinate *means* abstractness is
the register's declaration, not this module's finding, and the answer is
written so as not to blur the two.

## 3. What it refuses, and why the refusal is the result

Three boundaries, each named rather than guessed at:

| asked | reason | what happens |
|---|---|---|
| `order kind of energy and water` | `not-ordered` | `kind` is `semantic_concept` — a label, not a quantity; the refusal says which reading was not a number |
| `order line of GLM.NormFamily.family_tower and rung_audit` | `different-scale` | one reading is on `lean:line` and the other on `python:line`; two readings on different scales have no common order |
| `order atomic_weight_u of carbon and water` | `unreadable` | the row is held and does not carry the coordinate; the field surface's own refusal is restated, with the fields that row *does* answer to |

All three are evaluation cases, and all three are classified `boundary`
rather than `gap`: the operation is not failing to find something, it is
stating what it can read.

The middle one is the operation's reason for existing. Comparing the raw
numbers of two readings that are not on one scale is not a scale-free
question: `GLM.CoordinateOrder.naive_order_is_not_scale_free` exhibits a
positive factor that flips the verdict — a hundred centimetres is one metre,
one metre is less than two metres, and a hundred is more than two — while
`order_scale_invariant` shows that no rescaling of a *shared* scale can change
a verdict at all. Same scale is exactly the condition under which the answer
is a fact about the rows rather than about the units they happen to be written
in.

## 4. The declared set

Seven comparisons were written down before they were run: the probe question,
three more answerable ones over three different tables, and the three refusals
the operation must make. Each row states the outcome expected of it, and the
measurement is whether the outcome is that one.

<!-- generated: ordering-declared -->
| comparison | coordinate | rows | declared | outcome | as declared |
|---|---|---|---|---|---|
| `probe` | `abstract_concrete` | `energy` / `water` | `lt` | `lt` | yes |
| `lexicon-equal` | `animate_inanimate` | `energy` / `water` | `eq` | `eq` | yes |
| `element` | `atomic_weight_u` | `carbon` / `oxygen` | `lt` | `lt` | yes |
| `molecule-derived` | `molar_mass_u` | `water` / `ethanol` | `lt` | `lt` | yes |
| `nominal` | `kind` | `energy` / `water` | `not-ordered` | `not-ordered` | yes |
| `across-tables` | `line` | `GLM.NormFamily.family_tower` / `rung_audit` | `different-scale` | `different-scale` | yes |
| `unheld` | `atomic_weight_u` | `carbon` / `water` | `unreadable` | `unreadable` | yes |

the ordering operation answers 4 of the 7 declared comparisons and refuses 3, every one of them as declared before the run, with the three refusals falling under different-scale, not-ordered, unreadable. It closes the one question the field surface declared unreachable: 10 of the 10 held-and-unreachable questions are now parsed, and the whole probe splits 16 parsed, 0 surface, 4 absent against 15/1/4 before it.

one exact subtraction over two addressed readings is the whole of the derivation here, and the coordinate's meaning is the register's declaration rather than this module's finding. The four absent probe questions are untouched, and nothing here parses English: the question is still hand-translated into the system's own grammar.
<!-- end generated -->

Four of the seven are answered and three refused, which is what was declared;
the two worth reading twice are `lexicon-equal`, where two readings are equal
and the answer is *level with* and names no pole — the register declares an
end, not a winner — and `molecule-derived`, where both readings are recomputed
from the element register rather than stored, and are orderable on exactly the
same terms so long as both rows are read on one scale.

## 5. The probe question it closes

The comparison is run against the reading that bought the instrument, and the
old readings are not edited. `probe_oracle.TRANSLATIONS` is frozen, the field
surface's `FIELD_TRANSLATIONS` beside it is frozen, and this round's table is
`coordinate_order.order_translations()` — the field surface's table with one
row replaced, so the other nineteen questions are scored on exactly the
queries the previous round measured them on. The replaced row is scored at
`pole_row`, the row the answer puts at the named end, rather than at the
sentence: a fragment can only be matched by an answer that actually picks a
row. The no-smuggling rule is re-checked over the whole table and a test fails
if it breaks.

<!-- generated: ordering-split -->
| class | before the operation | after it | change |
|---|---|---|---|
| `parsed` | 15 | 16 | 1 |
| `surface` | 1 | 0 | -1 |
| `absent` | 4 | 4 | 0 |

10 of the 10 questions the oracle called held and unreachable are now parsed; the one the field surface declared unreachable is the one this operation closes.
<!-- end generated -->

Read plainly: the operation moves one question, which is the one it was built
for; the four `absent` questions are exactly where they were; and the ten the
oracle called held and unreachable are now all parsed.

## 6. What is proved rather than measured

`RequestProject/GLM/CoordinateOrder.lean` states the operation over readings
carrying an opaque scale tag and an exact rational, and proves what it is
worth:

* `order_eq_none_iff` and `order_isSome_iff` — it is silent **exactly** when a
  reading is missing or the two scales differ, so a refusal states a fact
  about the readings rather than reporting the failure of a search. It is the
  ordering operation's counterpart of `GLM.FieldSurface.lookup_eq_none_iff`.
* `order_lt_iff`, `order_gt_iff`, `order_eq_iff` and `order_sound` — when it
  answers, the answer is the order of the two values it was given, and nothing
  else.
* `order_swap` and `order_trans` — the verdict does not depend on which way
  round the question was asked, and strictly-below is transitive on a common
  scale.
* `order_scale_invariant` — rescaling a whole scale by a positive factor
  leaves every verdict on it unchanged, which is what makes *same scale* the
  right side condition.
* `naive_order_is_not_scale_free` — and the refusal is not fussiness: across
  two scales, the comparison of the bare numbers is not scale-free.
* `energy_below_water_on_abstract_concrete` and `across_scales_is_refused` —
  the probe question, decided on the register's own values and its own
  declared poles, and the boundary beside it.

## 7. What it decides, and what it does not

It decides the question the field surface left: *is energy more abstract than
water?* is answered, on the lexicon register's own scale and its own declared
poles, and the answer is *energy*, by an exact `3/4`.

Under the standing target of [`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md)
this round moves two of the three faculties, and both should be read at their
true size:

* **Derivation**, of the weakest interesting kind. One exact subtraction over
  two addressed readings is the whole of it. It is derivation rather than
  coverage because no register holds the answer — no row carries *energy is
  below water* — but nobody should mistake a subtraction for an inference.
* **Refusal**, on a declared task set. Three refusal reasons, each stating a
  fact about the readings, and one of them — `different-scale` — is a refusal
  the system did not previously have any way to make, with a proved statement
  of why the comparison it refuses is not a question.

It decides nothing about **addressing**: both readings are found by the names
the question already gives.

## 8. Limits

* **Nothing here parses English.** The question is still hand-translated into
  the system's own grammar, and blocker 1 is unmoved. What the measurement
  says is that the *fact* is now reachable by a query, not that the question
  is.
* **The pole is transcribed, not derived.** `POLES` restates the ten
  primitives' declared ends from the lexicon register; a test checks that its
  keys are exactly the register's ten, and nothing checks that the register is
  right about what the coordinate means.
* **One coordinate, two rows.** The operation composes exactly two readings.
  An ordering over a whole column — *which element is the most electronegative?*
  — is a different shape, and it was the round after this one that built it:
  [`COLUMN_EXTREMUM_STUDY.md`](COLUMN_EXTREMUM_STUDY.md). This operation is
  unchanged by it.
* **`different-scale` is conservative by construction.** Two readings of the
  same quantity in two tables under two field names are refused even when a
  conversion between them exists, because the operation holds no conversions.
  What would relax it is a declared table of conversions between scales, and
  that is a round with its own pre-registration.
* **The four `absent` probe questions are untouched.** *Why is the sky blue?*
  is still the declared control, and *is 91 prime?* is still arithmetic this
  system has no operation for.

## 9. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools ordering          # the measurement
PYTHONPATH=. python3 -m glm_universal.tools fieldsurface      # the reading before it
python3 GLM.py -q "order abstract_concrete of energy and water"
python3 GLM.py -q "order line of GLM.NormFamily.family_tower and rung_audit"
python3 -m pytest glm_universal/tests/test_coordinate_order.py -q
```

and, for the proved half, `lake build RequestProject.GLM.CoordinateOrder` from
the repository root.
