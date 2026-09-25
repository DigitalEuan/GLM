# The field surface — buying the cheap instrument, and saying what it bought

## Tier 0 — the coarse read

**Question.** The probe oracle found ten of twenty questions *held and unreachable* and priced a field surface at ten. Built, what does it actually answer?

**Verdict.** Nine of the ten, which is exactly the number declared reachable before the run: the tenth asks for a comparison across two rows and needs an operation rather than a surface. The whole probe moves from six parsed to fifteen, and none of it is reasoning — a field surface is `table`, the weakest of the three faculties, and every question it moves is one whose answer the system already held.

**Deciding figure.** <!--figure:fieldsurface-moved-->9<!--/figure--> of the <!--figure:fieldsurface-held-->10<!--/figure--> held-and-unreachable questions, against <!--figure:fieldsurface-predicted-->9<!--/figure--> declared reachable before the run; the split goes <!--figure:fieldsurface-parsed-before-->6<!--/figure--> → <!--figure:fieldsurface-parsed-after-->15<!--/figure--> parsed.

**Recomputed by.** `glm_universal.reasoning.field_surface.surface_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. What this round took, and from where

[`PROBE_ORACLE_STUDY.md`](PROBE_ORACLE_STUDY.md) §6 ends with a recommendation
and a warning. The recommendation: of the twenty pre-registered probe
questions, four are worth a parser and **ten** are held by a shipped register
row or a shipped function that no query kind returns, so the cheap instrument
is a *field surface* — one query kind returning a named field of a named row,
and its extension to a named function's named key. The warning: take it only
with its honest label, because a field surface is `table` under the standing
target of [`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md), and a round
that builds one buys **coverage** and must not report it as reasoning.

Both are taken here. The surface is
`glm_universal.runtime.fields`, reached by the `field` query kind, and this
study is the measurement of what it was worth. The label is kept in the
answer itself: every field answer carries a step saying *faculty = table*, and
that the answer would be the same if every geometric part of the system were
removed.

## 2. What is addressable

A field is addressed by two names — the row and the field — against a fixed
list of declared tables consulted in a fixed order. There are two shapes:

```
field atomic_weight_u of carbon      -- the value, exactly, with its provenance
fields of water                      -- the field names that row answers to
```

<!-- generated: fieldsurface-tables -->
| table | kind | rows | distinct fields | what it is |
|---|---|---|---|---|
| `element` | `source` | 118 | 20 | the 118 element rows the chemistry register is built from |
| `molecule` | `source` | 51 | 10 | the 51 molecule rows, with the register's declared derived properties beside the two fields it stores |
| `carrier:chemistry` | `carrier` | 118 | 7 | the attributes every carrier of the chemistry register keeps |
| `carrier:economics` | `carrier` | 21 | 6 | the attributes every carrier of the economics register keeps |
| `carrier:harmonics` | `carrier` | 28 | 9 | the attributes every carrier of the harmonics register keeps |
| `carrier:lexicon` | `carrier` | 149 | 90 | the attributes every carrier of the lexicon register keeps |
| `carrier:mathematics` | `carrier` | 22 | 13 | the attributes every carrier of the mathematics register keeps |
| `carrier:molecules` | `carrier` | 51 | 6 | the attributes every carrier of the molecules register keeps |
| `carrier:physics` | `carrier` | 726 | 7 | the attributes every carrier of the physics register keeps |
| `carrier:spatial` | `carrier` | 28 | 7 | the attributes every carrier of the spatial register keeps |
| `lean` | `address` | 3,766 | 5 | the Lean address book: one row per declaration of the development |
| `python` | `code` | 4,167 | 6 | the package's own top-level functions and classes, read by an AST walk |
| `function` | `function` | 3 | 26 | the declared zero-argument functions whose returned mapping is addressable by key |

13 tables, 9,248 rows and 55,173 addressable (row, field) pairs over 193 distinct field names.
<!-- end generated -->

Four things about that list are deliberate.

**A row answers only to a name it holds itself.** Its key, and any `name`,
`symbol`, `formula` or `identifier` field it carries. No alias is invented, so
`field group_block of chlorine` resolves through the element register's own
`name` field and answers for the row `Cl`.

**A derived value says that it is derived.** The molecule register stores a
name and a formula and recomputes everything else, so `field molar_mass_u of
water` answers `3603/200 (= 18.015)` and names the rule that produced it —
the sum over the formula of `atomic_weight_u` times count, from the element
register. A surface that let a recomputed value pass as a held one would be
claiming more than it does.

**Only declared functions are reachable.** The `function` table is a registry
of zero-argument functions whose returned mapping is addressable by key. A
field query cannot reach a function that is not in it, never imports a module
the surface was not declared with, and never evaluates a string. That is the
whole safety line, and it is a list rather than a rule about names.

**Exactness is not negotiable.** A rational crosses the boundary as `n/d`, and
an exact decimal is written beside it *only* when the denominator is a product
of twos and fives. No float is constructed anywhere in the module, which is
directive D7 and is checked statically by a test.

## 3. What it refuses

Three boundaries, each named rather than guessed at:

| asked | what happens |
|---|---|
| `field name of unobtainium` | no declared table holds the row; refused with the nearest row names |
| `field boiling_point of carbon` | the row is held and the field is not; refused with the fields the row *does* answer to, which include `boiling_point_K` |
| `field electronegativity_pauling of He` | the register records the field as missing for that row; refused **as missing**, because the missingness mask is a fact about the data and answering `none` as though it were a value would hide it |

All three are evaluation cases, and all three are classified `boundary` rather
than `gap`: the surface is not failing to find something, it is stating what
it holds.

## 4. The measurement

The comparison is run against the reading that bought the instrument, and the
old reading is not edited. `probe_oracle.TRANSLATIONS` is frozen — each of its
ten `surface` rows still carries no query, so re-running it still reports
6/10/4 — and `field_surface.FIELD_TRANSLATIONS` is a *second* table, run
beside it by the same scorer under the same two rules:

* **the locus rule** — the declared fragment must appear in the declared field
  of the solution, not merely somewhere in it;
* **the no-smuggling rule** — a translation may not contain the fragment it is
  scored on unless the question already contains it. `smuggling_audit`
  re-checks it over every row of the new table and a test fails if it breaks.

**One shortfall was declared before the run.** *Is energy more abstract than
water?* is not answerable by a field surface: it compares one coordinate
across two rows and a field query returns one field of one row. Writing
`field abstract_concrete of energy` would carry the fragment `energy` at its
locus and pass without answering anything — the false pass the locus rule
exists to refuse. So the prediction tested here is **nine**, and the tenth is
named as needing an operation rather than a surface.

<!-- generated: fieldsurface-split -->
| class | before the surface | after it | change |
|---|---|---|---|
| `parsed` | 6 | 15 | 9 |
| `surface` | 10 | 1 | -9 |
| `absent` | 4 | 4 | 0 |

the field surface answers 9 of the 10 questions the oracle called held and unreachable, against the 9 declared reachable before the run; 1 remains, and it is the one declared unreachable -- a comparison across two rows, which needs an operation rather than a surface. The whole probe splits 15 parsed, 1 surface, 4 absent, against 6/10/4 before it.

this is coverage, not reasoning: a field surface is `table`, the weakest of the three faculties, and every question it moves is a question whose answer the system already held. Nothing here derives anything, and the four absent questions are untouched.
<!-- end generated -->

Read plainly: the surface moves the probe from six parsed to fifteen parsed,
it answers the number declared reachable before the run and not one question
more, the tenth needs an operation rather than a surface, and of the three
faculties it is the weakest — `table`. Counted by the class the oracle put
them in, the questions it called *held and unreachable* fall from
<!--figure:fieldsurface-surface-before-->10<!--/figure--> to
<!--figure:fieldsurface-surface-after-->1<!--/figure-->, and the surface
reaches them by reading
<!--figure:fieldsurface-fields-->193<!--/figure--> distinct field names across
the tables above — the width of the instrument, and the reason a tenth
question it cannot answer is a question about an operation rather than a
missing field.

### Question by question

<!-- generated: fieldsurface-questions -->
| question | asked in English | the field query it becomes | before | after | kind returned |
|---|---|---|---|---|---|
| `nl-relation` | *what is velocity the derivative of?* | `field derivative_of of velocity` | `surface` | `parsed` | `field` |
| `nl-compare` | *is energy more abstract than water?* | *not expressible* | `surface` | `surface` | `not-expressible` |
| `chem-lookup` | *describe C* | `field name of C` | `surface` | `parsed` | `field` |
| `chem-weight` | *what is the atomic weight of carbon?* | `field atomic_weight_u of carbon` | `surface` | `parsed` | `field` |
| `chem-group` | *which block of the periodic table is chlorine in?* | `field group_block of chlorine` | `surface` | `parsed` | `field` |
| `chem-compose` | *what is the molar mass of water?* | `field molar_mass_u of water` | `surface` | `parsed` | `field` |
| `prog-lean` | *which file is GLM.NormFamily.family_tower in?* | `field file of GLM.NormFamily.family_tower` | `surface` | `parsed` | `field` |
| `prog-python` | *which module defines the function rung_audit?* | `field module of rung_audit` | `surface` | `parsed` | `field` |
| `prog-behaviour` | *what does glm_universal.substrate.norm_family.completeness return?* | `fields of glm_universal.substrate.norm_family.completeness` | `surface` | `parsed` | `field` |
| `prog-count` | *how many rungs does the norm family have?* | `field rungs of glm_universal.substrate.norm_family.completeness` | `surface` | `parsed` | `field` |
<!-- end generated -->

Two of the nine are worth reading twice. *What does
`glm_universal.substrate.norm_family.completeness` return?* is answered by the
**listing** shape rather than the value shape, which is the point of having
one: it asks what a row holds without naming the answer in the question, so
the translation does not smuggle `complete` into the query it is scored on.
And *which module defines the function `rung_audit`?* is answered from the
package's own source, read by the AST walk the package already ships — one
question of blocker 5, closed for the case that asks it.

## 5. What is proved rather than measured

`RequestProject/GLM/FieldSurface.lean` states the surface as a list of tables
of rows of named fields and proves four things about the lookup:

* `lookup_eq_none_iff` — it is silent exactly when every table is. The
  answerable `(row, field)` pairs are exactly the declared ones, so a refusal
  states a fact about the tables rather than the failure of a search. It is
  the field surface's counterpart of `GLM.Recipe.Spec.answer_eq_none_iff`.
* `lookup_sound` — an answer is some table's own value: nothing invents,
  interpolates or defaults a field.
* `lookup_isSome_iff_mem_names` — the two shapes agree. `fields of r` names
  exactly the fields `field n of r` answers, so an advertised index can
  neither promise a field the lookup refuses nor hide one it holds.
* `lookup_cons_of_some` and `lookup_append_of_isSome` — priority is monotone.
  The first table holding the pair decides it, and a table appended behind the
  ones that already answer cannot change an answer, which is what makes
  extending the surface safe rather than a re-measurement.

## 6. What it decides, and what it does not

It decides that the oracle's price was right to one question, and that the one
it was wrong about was wrong for a statable reason rather than an accident:
the tenth question is a comparison, and comparisons are blocker 3.

It decides nothing about reasoning. Under the standing target the three things
that count are derivation, addressing and refusal, and this round moved the
first two by nothing at all. Refusal is touched only in the weak sense that
three new boundaries are stated and witnessed. Fifteen of twenty probe
questions now have a query that answers them, and the four `absent` questions
are exactly where they were — *why is the sky blue?* is still the declared
control, and *is 91 prime?* is still arithmetic this system has no operation
for.

## 7. Limits

* **A translation is still hand-written.** Nothing here parses English. The
  measurement says the *fact* is now reachable by a query, not that the
  question is. Blocker 1 is unmoved, and what the parser is worth is still the
  four questions the oracle priced.
* **The census is of what is addressable, not of what is useful.** Fifty
  thousand `(row, field)` pairs is a count of doors, and most of them nobody
  will open. It is reported because it is the honest size of the surface, not
  because size is evidence.
* **The `python` table reads the package's own text.** It is a table over
  source, which is the weakest witness kind the oracle admits, and it holds
  only top-level definitions. A name defined twice keeps the first module in
  path order and records the second in `also_in`, so the ambiguity is
  reported rather than resolved.
* **One question remains held and unreachable**, and it is named: the
  abstractness comparison. The instrument that would close it is an operation
  over two readings of the same coordinate — the thing this round deliberately
  did not build.

## 8. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools fieldsurface        # the measurement
PYTHONPATH=. python3 -m glm_universal.tools oracle              # the frozen reading
python3 GLM.py -q "field atomic_weight_u of carbon"             # one answer
python3 GLM.py -q "fields of water"                             # the listing shape
python3 -m pytest glm_universal/tests/test_field_surface.py -q
```

and, for the proved half, `lake build RequestProject.GLM.FieldSurface` from
the repository root.
