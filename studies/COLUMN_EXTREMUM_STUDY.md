# The extremum of a column — the operation the ordering round stopped short of, and the two refusals that are the point of it

## Tier 0 — the coarse read

**Question.** The ordering operation composes exactly two readings and says so in its own limits. Built, what does the operation over a whole column answer, and what must it refuse?

**Verdict.** It folds four of the eight columns declared before the run and refuses four, every one of the eight as declared, under all four of its named reasons. The two refusals it was built for are the result rather than fussiness: a column with a hole in it has no extremum, because the largest of the rows that happen to be filled in is a wrong answer rather than a partial one, and a column gathered from two scales is not one column. Where more than one row is at the end, every row attaining it is named.

**Deciding figure.** <!--figure:extremum-as-declared-->8<!--/figure--> of <!--figure:extremum-declared-count-->8<!--/figure--> declared columns came out as declared, <!--figure:extremum-answered-->4<!--/figure--> folded and <!--figure:extremum-refused-->4<!--/figure--> refused under all <!--figure:extremum-reasons-->4<!--/figure--> named reasons.

**Recomputed by.** `glm_universal.reasoning.column_extremum.extremum_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. What this round took, and from where

[`ORDERING_STUDY.md`](ORDERING_STUDY.md) §8 names this operation as the first
thing the ordering round could not do:

> **One coordinate, two rows.** The operation composes exactly two readings.
> An ordering over a whole column — *which element is the most
> electronegative?* — is a different shape and is not built.

[`STATUS.md`](../STATUS.md) §3.4 then carried it as candidate 1, the sharpest
of the ten, with the shape of the work already stated: a declared column
rather than two named rows, a refusal for a column whose rows are not all on
one scale, and a second refusal for a column with holes in it, because a
missingness mask is a fact about the register and an extremum taken over the
rows that happen to be present is a wrong answer rather than a partial one.

This study is that operation and the measurement of what it was worth. The
shipped half is `glm_universal.reasoning.column_extremum`, reached by the
`extremum` query kind; the proved half is
`RequestProject/GLM/ColumnExtremum.lean`.

## 2. What the operation is

An end, a coordinate, and a table:

```
largest atomic_weight_u in element             -- the heaviest element, exactly
smallest atomic_weight_u in element            -- and the lightest
largest molar_mass_u in molecule               -- a column recomputed rather than stored
largest abstract_concrete in carrier:lexicon   -- a fourteen-row tie, reported as one
```

The end is read off the word that opens the question — `largest`, `highest`
and `maximum` ask for one end, `smallest`, `lowest` and `minimum` for the
other — so it is a fact about the question rather than a further operand. All
six are **start-only** keywords, for the reason `field` and `order` are:
*the smallest vector of the Leech lattice* is an ordinary noun phrase of these
registers and asks for no column of any table, so the word governs a question
only when it opens one.

A **column** is every reading of one coordinate down one declared table. It is
gathered through the same field surface a single row is read through, so four
things it inherits are already settled:

* a coordinate held inside a mapping field is read as a coordinate of that
  field, which is how the lexicon register's ten semantic primitives are
  reachable at all, and the scale records the containing field;
* a derived coordinate is recomputed rather than stored, and folds on exactly
  the same terms as a held one;
* the values cross as `Fraction` and the fold compares them exactly — no float
  is constructed anywhere in the module, which is directive D7 and is checked
  statically by a test;
* the **scale** is the table and the field the value was read under, and a
  column is required to be on one of them.

Two things about the answer are deliberate. The gap to the next distinct value
is reported, exactly, so the answer says how far clear the extremum is: the
heaviest element wins by an exact `201/200`, while the concrete end of the
lexicon's `abstract_concrete` is a flat tie. And **every** row attaining
the end is named. Fourteen of the lexicon register's 149 rows sit at `1` on
`abstract_concrete`, and naming one of them would be a choice the register
does not make.

## 3. What it refuses, and why two of the four refusals are the result

| asked | reason | what happens |
|---|---|---|
| `largest electronegativity_pauling in element` | `incomplete` | 23 of the 118 rows record the coordinate as missing; the refusal names them and stops |
| `largest line` | `mixed-scale` | with no table named the column is two columns — `lean:line` and `python:line` |
| `largest name in element` | `not-ordered` | the column holds labels, and a column of labels has no extremum |
| `largest boiling_point in element` | `no-such-column` | no row of the table answers for the coordinate; `boiling_point_K` is the name it holds |

The last two restate boundaries the field surface already had. The first two
are the operation's reason for existing, and both have a proved statement
underneath them.

**A column with a hole in it has no extremum.** The element register records
`electronegativity_pauling` for 95 of its 118 rows, and the largest of those
95 values is not the largest of the column: it is the largest of the rows that
happen to be filled in. `GLM.ColumnExtremum.extremum_over_present_is_not_the_extremum`
exhibits a column where the two differ — the rows present peak at `1`, and
filling the one hole with `3` moves both the value and the row that attains it
— so an answer taken over the present rows is a wrong answer rather than a
partial one. The operation therefore refuses the whole column and names what
is missing. The missingness mask is a fact about the register, and the field
surface already refuses a missing cell rather than answering it blank; this is
that refusal carried up from the cell to the column.

**A column gathered from two scales is not one column.** This is the ordering
operation's `different-scale`, one level up. `line` is held by the Lean
address book and by the package's own source walk, and the largest of those
numbers jointly is a fact about neither table.
`GLM.ColumnExtremum.extremum_not_invariant_under_one_row_rescaling` exhibits a
positive rescaling of a single row — which is exactly what a second scale
permits — that moves the extremum to a different row, while
`extremum_scale_invariant` shows that rescaling the *shared* scale moves the
value by the factor and leaves the winners alone. Naming one table asks for
one of the two columns, and is answered.

All four are evaluation cases, and all four are classified `boundary` rather
than `gap`: the operation is not failing to find something, it is stating what
it can read.

## 4. The declared set

Eight columns were written down before they were run: four the operation must
fold — a stored column at both ends, a derived column, and a column whose end
is a fourteen-row tie held inside a mapping field — and one for each of the
four ways it may refuse. Each row states the outcome expected of it, and the
measurement is whether the outcome is that one.

<!-- generated: extremum-declared -->
| column | end | coordinate | table | declared | outcome | rows at the end | as declared |
|---|---|---|---|---|---|---|---|
| `heaviest` | `largest` | `atomic_weight_u` | `element` | `answer` | `answer` | `Og` | yes |
| `lightest` | `smallest` | `atomic_weight_u` | `element` | `answer` | `answer` | `H` | yes |
| `derived-column` | `largest` | `molar_mass_u` | `molecule` | `answer` | `answer` | `iron(III) sulfate` | yes |
| `tie` | `largest` | `abstract_concrete` | `carrier:lexicon` | `answer` | `answer` | 14 rows | yes |
| `holes` | `largest` | `electronegativity_pauling` | `element` | `incomplete` | `incomplete` | -- | yes |
| `nominal` | `largest` | `name` | `element` | `not-ordered` | `not-ordered` | -- | yes |
| `two-tables` | `largest` | `line` | `(unnamed)` | `mixed-scale` | `mixed-scale` | -- | yes |
| `absent` | `largest` | `boiling_point` | `element` | `no-such-column` | `no-such-column` | -- | yes |

the extremum operation answers 4 of the 8 declared columns and refuses 4, every one of them as declared before the run, with the refusals falling under all 4 of its named reasons (incomplete, mixed-scale, no-such-column, not-ordered). 1 of the answers is a tie reported as a tie rather than resolved.

a fold over addressed readings is the whole of the derivation here: the operation reads every row of one table through the field surface, compares exactly, and names every row that attains the end. It invents no value for a hole and bridges no scale, which is why 4 of the 8 declared columns are refusals rather than answers, and nothing here parses English.
<!-- end generated -->

<!--figure:extremum-ties-->1<!--/figure--> of the four answers is a tie, and
it is reported as a tie rather than resolved. The four refusals fall under
<!--figure:extremum-reasons-declared-->4<!--/figure--> named reasons, which is
all of them: the declared set was chosen so that no refusal reason ships
unexercised.

## 5. What is proved rather than measured

`RequestProject/GLM/ColumnExtremum.lean` states the operation over a column of
cells — a row name, a scale tag, and either an exact rational or nothing, the
`nothing` being the register's own missingness mask — and proves what it is
worth:

* `extremum_eq_none_iff` and `extremum_isSome_iff` — it is silent **exactly**
  when the column was gathered from more than one scale, when it has a hole in
  it, or when it has no rows. A refusal states a fact about the column rather
  than reporting a failed search, which is the ordering operation's
  `order_eq_none_iff` one level up.
* `extremum_value_mem` and `le_extremum` — when it answers, the value returned
  is one of the column's own and no reading of the column exceeds it.
* `mem_extremum_winners_iff` and `extremum_winners_ne_nil` — it names every
  row that attains the end and only those, and it always names at least one.
* `extremum_scale_invariant` — carrying the whole column by a positive factor
  moves the value by that factor and leaves the winners exactly alone, which
  is what makes *one scale* the right side condition.
* `extremum_not_invariant_under_one_row_rescaling` — and the refusal is not
  fussiness: carry one row alone and the extremum is a different row.
* `extremum_over_present_is_not_the_extremum` — the hole, likewise: the
  extremum over the rows that are filled in is not the extremum of the column.
* `trough_eq_none_iff` and `trough_names_the_smallest` — the two ends are one
  operation. The smallest is the largest of the negated column, it refuses in
  the same three situations, and on the witness column the two ends are two
  different rows.

The Python tests mirror §5 and §6 of that file on the shipped arithmetic
rather than restating them: a whole-column rescaling keeps every winner, a
one-row rescaling moves it, and the rows that are filled in do have a maximum
which the operation declines to return.

## 6. What it decides, and what it does not

Under the standing target of [`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md),
and the assignment directive **D15** requires, this round moves two of the
three faculties:

* **Derivation.** A fold over addressed readings, which is more than the
  ordering operation's single subtraction and still at the weak end: 118 exact
  comparisons and a set of maximisers. It is derivation rather than coverage
  because no register holds the answer — no row of the element table carries
  *this is the heaviest* — and the answer is recomputed from the rows each
  time it is asked for.
* **Refusal**, on a declared task set: four reasons, each stating a fact about
  the column, two of them refusals the system had no way to make before, and
  both with a proved statement of why what they refuse is not a question.

It decides nothing about **addressing**: the table and the coordinate are the
names the question already gives, and the rows are read in the table's own
order.

## 7. Limits

* **Nothing here parses English.** *Which element is the most
  electronegative?* is still hand-translated into the system's own grammar —
  and in this case the honest answer to the English question is the refusal,
  because that column has holes in it.
* **A column is one table.** Gathering the same quantity from two tables is
  refused rather than converted, exactly as the ordering operation refuses two
  readings on two scales, and for the same reason: the operation holds no
  conversions. The declared table of conversions that would relax both is
  candidate 2 of [`STATUS.md`](../STATUS.md) §3.4 and is a round with its own
  pre-registration.
* **The fold is a maximum.** A rank, a median or a top-*k* over the same
  column would each need their own statement of what a hole does to them, and
  none is built.
* **The refusal on holes is total.** *Of the rows that are filled in, which is
  the largest?* is a different, answerable question, and the operation does
  not answer it either: it would need to be asked as one, with the missing
  rows named in the answer rather than in the refusal.

## 8. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools extremum         # the measurement
python3 GLM.py -q "largest atomic_weight_u in element"
python3 GLM.py -q "largest abstract_concrete in carrier:lexicon"
python3 GLM.py -q "largest electronegativity_pauling in element"
python3 GLM.py -q "largest line"
python3 -m pytest glm_universal/tests/test_column_extremum.py -q
```

and, for the proved half, `lake build RequestProject.GLM.ColumnExtremum` from
the repository root.
