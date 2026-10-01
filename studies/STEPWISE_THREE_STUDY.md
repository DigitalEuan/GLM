# The stepwise planner, round three: declared comparatives, further count nouns, tera and pico, and folds over a column

## Tier 0 — the coarse read

**Question.** Can the stepwise planner read the widenings round two named — comparatives such as *heavier* with a declared field, *how many more* over further count nouns, the tera- and pico- prefixes, and sums, means and parity counts over a whole column — without answering anything wrongly?

**Verdict.** Yes: the stepwise planner now reads comparatives through a declared register field, *how many more* electrons and valence electrons, the tera- and pico- prefixes, and sums, means and parity counts over every element or a declared class of them, with every declared case as declared, 0 wrong, and a refusal by name when a comparative has no declared field, a value or a column reading is missing, or a class is not the register's.

**Deciding figure.** 47 of 47 declared questions (18 comparative, 6 count-noun, 6 prefix, 17 fold) and 2 of 2 follow-ups as declared, 0 wrong, where round two's reader answers 0 of the 47 and the whole machine answered 6 of them before the round and 32 after; 34 of 34 chain scripts verified (327 of 327 steps aligned) and every mutation rejected, 13 of 13 member lies and 11 of 11 word lies included; 8 of 8 marks met.

**Recomputed by.** `glm_universal.runtime.stepwise_three.stepwise_three_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round two ([`STEPWISE_TWO_STUDY.md`](STEPWISE_TWO_STUDY.md), Phase 73) closed
with every declared mark met and named, in its §6, the widenings it left:
the tera- and pico- prefixes, *heavier / lighter / older* as comparatives
with a declared field, parity and averages over a whole column (the folds of
candidate 2), and *how many more* over further count nouns. Its §4.1 had
already met two of them in questions written after the module: *600
terahertz* (the prefix table stopped at giga) and *how much heavier is …*
(*heavier* was no comparative of the difference frame). They are item O7 of
candidate O of [`STATUS.md`](../STATUS.md) §3.4, and this round takes them.

Items O1 (a question set written outside the project), O3 (the reverse relay
into the chain) and O5 (measurands rather than units) are left named (§6).

## 1. The objects

Exact throughout (D7); no digest decides a meaning (D3); every reading rests
on a declaration in
[`runtime/declared_frames.py`](../overlay/glm_universal/runtime/declared_frames.py).

* **Declared comparatives.** A comparative word is read only through the
  declared table: *heavier* and *lighter* compare the standard atomic
  weight, *denser* the density, *older* and *newer* the recorded year of
  discovery (older is the earlier year). Three frames: *which is W, A or B*
  (one step, `comparative`, whose value is the row as the question names
  it, or `equal`), *is A W than B* (round one's `compare` step, with the
  declared direction), and *how much W is A than B* (round two's guarded
  difference, the right way round). A comparative that is not declared
  (*stronger*, *harder*) is refused `COMPARATIVE_UNDECLARED`: no column of
  the register measures it, and the planner does not guess one. Round two's
  ordering rule still holds: two looked-up values whose stated precision
  overlaps are refused `PRECISION_OVERLAP`.
* **A value the register records as missing** is refused `VALUE_MISSING`
  in the new frames rather than round one's generic `UNKNOWN_STEP`: the
  element table records, for example, no year of discovery for iron (known
  since antiquity), and saying so is the answer.
* **Further count nouns.** *Electrons* (of the neutral atom, whose electron
  count is its atomic number by definition) and *valence electrons* (the
  register's own column) join round two's *protons*. *Neutrons* would need a
  nuclide register and stay undeclared (`UNKNOWN_STEP`, as in round two).
* **Tera and pico.** The exact SI prefixes 10¹² and 10⁻¹² join the unit
  table; *exa* stays undeclared (`UNKNOWN_UNIT`).
* **Folds over a column.** A sum, a mean, or a count of the odd (or even)
  values of one element-table column, over every element or over one
  declared class — the register's own `group_block` classes under their
  plural names (*the noble gases*, *the halogens*, *the alkali metals* …).
  Three frames: *the sum (average, mean) of the Xs of S*, *the average
  (mean, total) X of S*, and *how many of S have an odd (even) X*. The fold
  is one step, `fold`, over one looked-up step per member. A column with a
  missing reading is refused `COLUMN_HOLE`, with the missing rows named:
  the mean over the rows that are present is a different question, and
  §5 proves it is not the column's mean for any but one value of the
  missing reading. A class the register does not name (*the metals*) is
  refused `SET_UNDECLARED`. A parity count over a column that is not
  integer is refused `NOT_AN_INTEGER`.
* **Where a refusal is the planner's to make, and not this layer's.**
  `COMPARATIVE_UNDECLARED` is a claim about register rows, so it is made
  only when both sides are rows of the element table; `SET_UNDECLARED` is a
  claim about the element table's classes, so it is made only for a fold over
  one of its columns. Any other text is left unread, for the readers that
  own it (§4.2 is why).
* **Three columns.** Every new step has a declared column-1 template and a
  column-2 equation the chain's column-3 script reads back with its own
  readers. For a `comparative` step the script re-reads the declared table
  and checks the word's field and direction and that both inputs are that
  field of the rows named; for a `compare` step with a declared word it
  checks the direction; for a `fold` step it re-derives the membership of
  the class from the register itself and requires the inputs to be exactly
  that column of exactly those rows, in the register's order, before it
  recomputes the fold.

## 2. Declarations — written before any code of the round

The corpus is
[`evaluation/stepwise_three_cases.py`](../overlay/glm_universal/evaluation/stepwise_three_cases.py),
committed with this section and before any code: 18 comparative questions
(13 to be answered, 5 refused by name), 6 count-noun questions (3 answered,
3 refused), 6 prefix questions (4 answered, 2 refused), 17 fold questions
(12 answered, 5 refused) and 2 follow-ups. Every expected answer was worked
by hand from the register values.

| mark | claim | measured by |
|---|---|---|
| **V1** | every comparative case gets its declared verdict; 0 wrong. Control: round two's reader (round three switched off) answers 0 of the 18 | `comparatives` |
| **V2** | every count-noun case gets its declared verdict; 0 wrong. Round two's reader answers 0 of them | `counts` |
| **V3** | every prefix case gets its declared verdict, and every answered one stitches exactly the declared quantities; 0 wrong. Round two's reader answers 0 of them | `prefixes` |
| **V4** | every fold case gets its declared verdict; 0 wrong. Round two's reader answers 0 of them | `folds` |
| **V5** | the hole rule matters and the classes are the column: a *fold the rows that are present* control answers at least 3 of the declared `COLUMN_HOLE` cases; and on every element-table column with no missing reading and a numeric value, the sum over all the elements equals the sum of the sums over the declared classes (the classes partition the column) | `controls` |
| **V6** | every answered chain's column-3 script prints `VERIFIED True` in a fresh `python3 -I`, with one `ALIGNED` line per step; rounds one and two's six mutation kinds are all rejected, and so are two more: `member-lie` (a fold's inputs short of one member, the fold re-rendered to agree) and `word-lie` (a comparative's declared direction reversed, its value and both columns re-rendered to agree) | `scripts` |
| **V7** | non-interference: round one's and round two's corpora keep every verdict (marks S1–S7 and T1–T7 as measured without their scripts), and on the router's declared sets no answered verdict changes and no declared refusal becomes an answer | `interference` |
| **V8** | `RequestProject/GLM/StepwiseWiden.lean` builds with no `sorry` and standard axioms, and proves: the row a declared comparative names is order-free, a comparative and its opposite never name the same row of two distinct rows, and neither is named exactly when the values are equal; a sum over the whole column is the sum of the sums over a partition into classes; a sum of integers is even exactly when an even number of its terms is odd, and the odd and even counts add up to the column; with one reading missing, the mean over the present rows is the column's mean only when the missing reading equals it, and distinct missing readings give distinct means | Lean |

The measurement is `glm_universal.runtime.stepwise_three.stepwise_three_report`.

## 3. What was built

* [`runtime/declared_frames.py`](../overlay/glm_universal/runtime/declared_frames.py)
  — the declarations: `COMPARATIVES` (five words, each a register phrase and
  a direction), `COUNT_NOUNS` (*electrons*, *valence electrons*),
  `DECLARED_SETS` (every element, and the ten `group_block` classes under
  their plural names), `resolve_field` (a phrase to an element-table column,
  through the planner's own synonym table and the column's own name),
  `members`, and the two gates of §1.
* [`runtime/stepwise.py`](../overlay/glm_universal/runtime/stepwise.py) —
  the frames (`_comparative_readings`, `_fold_readings`, the *how many of*
  predicate, the declared comparatives in the difference frame, multi-word
  count nouns), the steps (`_build_comparative`, `_build_fold`), and
  `VALUE_MISSING` read from the planner's own missing-field refusal. Behind
  `ROUND_THREE`, read only while round two is on too.
* [`runtime/quantity_units.py`](../overlay/glm_universal/runtime/quantity_units.py)
  — `WIDE_PREFIXES` (tera, pico) behind `WIDEN`.
* [`reasoning/stepwise_script.py`](../overlay/glm_universal/reasoning/stepwise_script.py)
  — the column-1 templates, column-2 equations, readers and recomputation of
  `comparative` and `fold`; the script's checks of §1 (the declared table for
  every comparative and every `compare` step with a declared word, the row
  named against the row looked up, the class re-derived from the register);
  the mutations `member-lie` and `word-lie`.
* [`runtime/stepwise_three.py`](../overlay/glm_universal/runtime/stepwise_three.py)
  — the measurement (`stepwise_three_report`) and both controls; `tools
  stepwise-three`; `tests/test_stepwise_three.py`.
* **Wiring.** Nothing new: the router already hands a planner refusal to the
  stepwise planner, so every new question is reachable from `GLM.py --ask`
  and `GLM.py --steps`. `mean` in `StepwiseFrames.lean` is now `@[expose]`,
  so the hole theorems can unfold it.
* [`RequestProject/GLM/StepwiseWiden.lean`](../overlay/glm_lean/RequestProject/GLM/StepwiseWiden.lean)
  — §5.

## 4. Results

Measured by `tools stepwise-three` at the close of the round.

**Can it?** Yes: every declared case as declared, 0 wrong, every script verified and every mutation rejected.

| mark | result | figure |
|---|---|---|
| **V1** | met | 18 of 18 comparative cases as declared: 13 answered, 5 refused by the declared name (`VALUE_MISSING`, `COMPARATIVE_UNDECLARED` twice, `UNKNOWN_STEP`, `DIFFERENCE_REVERSED`); 0 wrong. Round two's reader answers 0 of the 18 |
| **V2** | met | 6 of 6 count-noun cases: 3 answered, 3 refused (`DIFFERENCE_REVERSED`, `UNKNOWN_STEP` for neutrons, `VALUE_MISSING`); 0 wrong. Round two's reader answers 0 |
| **V3** | met | 6 of 6 prefix cases, every answered one stitching exactly the declared quantities: 4 answered, 2 refused (`UNKNOWN_UNIT` for exa, `UNIT_MISMATCH`); 0 wrong. Round two's reader answers 0 |
| **V4** | met | 17 of 17 fold cases: 12 answered, 5 refused (`COLUMN_HOLE` three times, `SET_UNDECLARED`, `NOT_AN_INTEGER`); 0 wrong. Round two's reader answers 0 |
| **V5** | met | the present-rows control answers all 3 declared holes (`f06` 14/5, `f12` 131195277/103000, `f17` 1504491/500000 — each a mean over the rows that hold a reading, and none of them the column's); on the 4 numeric element columns with no missing reading (`z`, `atomic_weight_u`, `group_block_code`, `standard_state_code`) the sum over all the elements equals the sum of the class sums, and the ten classes hold 118 of the 118 rows |
| **V6** | met | 34 of 34 answered chains verified in a fresh `python3 -I`, 327 of 327 steps `ALIGNED`; value lie, column 1 alone, reordering, answer and read lie each 34 of 34 rejected, unit lie 4 of 4, member lie 13 of 13, word lie 11 of 11 |
| **V7** | met | round two's corpus through the round-three module: 21 of 21 frame, 18 of 18 unit, 14 of 14 register cases, 2 of 2 narratives and 2 of 2 follow-ups as declared, its controls still met; round one's 30 / 21 / 6 / 4 as declared; on the router's 273 declared questions the stepwise layer still reads 11, every one answered by the planner first, and turns none into an answer |
| **V8** | met | §5 |

**In all.** 47 of 47 declared questions and 2 of 2 follow-ups as declared,
with 0 wrong answers; every declared case was met on the first measurement.
As in rounds one and two, the corpus and the module share an author, so this
is the reach of the declared set, not an independent test (§6).

**What the whole machine gained.** Through `GLM.py --ask`, before this round
the machine answered 6 of the 47: the typed planner's ordering frame already
read *heavier* and *lighter* between two elements (c01–c04, c13, c14) and
gives the same verdicts, so the router never reaches the stepwise planner on
those six. After the round it answers 32 of the 47 and refuses the other 15
by name: *denser*, *older* and *newer*, *how much heavier*, the two count
nouns, tera and pico, and every fold are new.

**What the hole rule withholds.** *The average electronegativity of the noble
gases* is refused `COLUMN_HOLE` naming He, Ne, Ar, Rn and Og: the register
records no Pauling electronegativity for them. The present-rows reading
answers 14/5 — the mean of krypton and xenon — which is a true statement
about two rows and a false one about seven. *The average melting point of all
the elements* is refused naming 15 rows; *the average density of the
halogens* naming tennessine.

**Faculty (D15).** Derive: every answered fold, comparative and difference
computes a value no register row holds, with one looked-up step per input and
every step re-checked in all three columns. Refuse: the four new named
refusals withhold the three present-rows answers, a guess at which column
*stronger* or *harder* means, and an answer about a year the register does not
hold.

### 4.1 Beyond the declaration — not counted

Fourteen further questions, written after the module worked and so **not** a
held-out test, were run once through `GLM.py --ask`'s router. Thirteen were
answered and each was checked by hand: 0 wrong (*which is denser, osmium or
iridium* = osmium; *how much denser is gold than lead* = 397/50; *600
terahertz and 500 nanometres* = 300,000,000 m/s; *how many of the elements
have an odd atomic number* = 59; *how many more valence electrons does
chlorine have than sodium* = 6; *the total valence electrons of the alkaline
earth metals* = 12; *is uranium heavier than plutonium* = no, answered by the
planner's ordering frame). One was refused: *the rare earths* is no class of
the register (they are the lanthanides with scandium and yttrium), so
`SET_UNDECLARED`.

### 4.2 A regression found by the router census, and fixed

The first version refused `COMPARATIVE_UNDECLARED` for any *-er … than*
form. The router census (mark V7) found it reading six more declared
questions than round two — *is hot in tea hotter than fast in walking*, *is
tepid in tea tepider than cold in tea* and four like them — and although none
changed from refused to answered, three of them had been refused by the
vagueness reader with the specific reason (*different quantities are not
comparable*; *tepid names no direction*), which the generic refusal replaced.
The refusal is now made only when both sides are rows of the element table
(and `SET_UNDECLARED` only for a fold over an element column); the census
reads 11 again, the same 11 as round two, and those refusals keep their
reasons.

## 5. Lean

`RequestProject/GLM/StepwiseWiden.lean` builds with no `sorry` and the
standard axioms only (`propext`, `Classical.choice`, `Quot.sound`).

* `winner_swap`, `winner_flip_ne`, `winner_eq_none_iff` — the row a declared
  comparative names does not depend on the order the rows are written; a
  comparative and its opposite never name the same row of two distinct rows
  with distinct values; and no row is named (`equal`) exactly when the values
  are equal.
* `fold_sum_partition` — the sum over the whole column is the sum over the
  classes of the sums over each class: what V5's partition check measures.
* `even_sum_iff_even_odd_count`, `odd_count_add_even_count` — a sum of
  integers is even exactly when an even number of its terms is odd, and the
  two parity counts add up to the column.
* `mean_cons_eq_iff`, `hole_mean_injective` — with one reading missing from a
  nonempty column, the mean over the present rows is the column's mean exactly
  when the missing reading equals it, and distinct missing readings give
  distinct means: `COLUMN_HOLE` withholds nothing the present rows determine.

## 6. What this leaves

* **A held-out set nobody on the project wrote** — still the sharpest item
  of candidate O, and still not something the project can write for itself.
* **The reverse relay into the chain** and **measurands rather than units**
  (O3, O5) — untouched by this round.
* **Wider tables.** Comparatives and folds over the molecule table (*heavier*
  is the molar mass there), neutrons (a nuclide register), further prefixes
  (exa, femto), and classes the register does not hold as one value (*the
  metals*, *the rare earths*) — each needs a declaration argued for, not a
  word added.
* **The narrower question beside `COLUMN_HOLE`.** *Of the rows that are
  filled in, what is the mean?* is a different question with a true answer;
  asked as that question, with the missing rows named in the answer, it could
  be answered. A median or a rank over a column with a hole each need their
  own statement of what the hole does ([`COLUMN_EXTREMUM_STUDY.md`](COLUMN_EXTREMUM_STUDY.md) §7).

