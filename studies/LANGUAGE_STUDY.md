# The question shape made an object

*What `glm_universal/language/`, `RequestProject/GLM/Question.lean` and
`report language` are for, and what they measured.*

Every figure below is recomputed by the code that reports it. Run

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report language" --verify-tct
```

and the third column re-derives the whole study in a fresh interpreter — both
matchers re-run over both generated corpora, against the branches the parser
used to have and the branches it still has — and checks it key by key
(`VERIFIED True`).

This study covers three rounds. The first described three query kinds by
**slot shape** and measured them against the hand-written parser; the second
put the descriptions *in place of* the three branches, described the leading
remainder that made that possible, and asked whether a **second** shape
family was worth having; the third described the four parts that were still
hand-written — a list, a modifier, a trailing option and a nested side — and
deleted the branches they were the obstacle to. Sections 1–9 are the first
round brought up to date; §10 is the second and §13 is the third, and where
an earlier section names something as open, §13 says whether it is still.

---

## 1. The thing this round was trying to remove

The round before made a **domain** declarative. A `DomainSpec` says what its
objects hold, how each coordinate is derived, which coordinates recover the
object, what a reading is and what must be refused, and one generic path turns
any such description into the carriers, the layer chain, the widening audit,
the query surface and the refusal boundary. Three registers built by hand were
deleted and regenerated from their descriptions alone with every measured
figure unchanged, and the round closed by naming its own limit:

> **The surface language is still a keyword.** `derive <coordinate> of
> <object>` is generic in the coordinate and the object but is itself a
> hand-written phrase.
>
> — [`RECIPE_STUDY.md`](RECIPE_STUDY.md) §9

So a new domain arrived with its carriers, its readings and its refusals, and
then waited for someone to write a branch of `runtime/parser.py` before anyone
could ask it anything. The recipe had been written down; the *question* had
not.

This round writes the question down. The input is a **question description**;
the output is one generic matcher from a description to a query kind and its
options. The test is subtractive in the same way as the last one: kinds that
are recognised by hand today are matched by shape instead, and both parsers are
put to the same corpus and required to agree.

## 2. What a description says

A `QuestionSpec` (`language/question.py`) is four things and no code:

| part | what it says |
|---|---|
| `kind` | the query kind a match produces — the same string `parser.KINDS` uses |
| `gloss` | what a question of this shape asks for |
| `shape` | an **opening**, then named **slots** separated by literal **phrasings**, with an optional tail |
| `preamble` | an ordered list of word families that may be skipped **before** the opening — see §3.1 |
| `refusals` | the named boundaries a question of this shape can hit, each with the sentence it prints |

Two pieces make up a shape.

A **`Phrasing`** is a set of surface words that count as the same thing here —
`of`, `for` and `on`; `measure`, `how much`, `relative measure`, `measure
word`, `how far up`. Its alternatives are held longest-first, so `derivation
of` cannot be shadowed by `derive`. Every phrasing carries a `why`: the
sentence that justifies treating those forms as one set. That is not
decoration — see §4.

A **`Slot`** is a named hole with a role (`coordinate`, `object`, `domain`,
`subject`, `class`, `task`), a flag for whether it may be left out, and a flag
for whether the leading articles are kept. Slots are named after the option
keys the runtime uses, so a match becomes a query's options by a dictionary
comprehension rather than by a per-kind rule — which is what makes the matcher
generic rather than a switch with three arms.

A shape must **open with a phrasing**. A question is recognised by its
opening, and never by a keyword found somewhere in the middle;
`QuestionSpec.__post_init__` refuses a shape that does not, and refuses one
with a duplicate slot name or with no slot at all. What may stand before the
opening is the **preamble**, and it is described rather than skipped blindly:
§3.1.

## 3. The four descriptions

`language/descriptions.py` holds them and nothing else: no matching is done
there, no kind is special-cased there.

| kind | shape | slots | openings | separators | judgements | boundaries |
|---|---|---|---|---|---|---|
| `derive` | `(derivation of \| what derives \| which coordinate \| coordinate \| derive) <coordinate> (for \| of \| on) <object> in <domain>?` | coordinate, object, domain? | 5 | 3, then 1 | 5 | 3 |
| `measure` | `(how far up \| how much \| measure word \| relative measure \| measure) <subject> (relative to \| against \| for \| in \| within) <class>?` | subject, class? | 5 | 5 | 4 | 1 |
| `task` | `(solve task \| worked example \| puzzle \| task) <task>` | task | 4 | — | 3 | 1 |
| `compare` | `(which is bigger \| which is larger \| compare) <left and right>` | values (a **list** slot) | 3 | `and`, then `versus \| vs \| or` | 3 | 1 |

**7 slots, 47 surface forms, 15 judgements, 6 named boundaries, 17
openings.** Two of each shape's judgements are the preamble's, which every
shape shares (§3.1); the remaining seven — three for `derive`, two for
`measure`, one each for `task` and `compare` — are the shapes' own.

The fourth row arrived in the third round (§13) and is the reason the first
three rows are worth re-reading: `compare` needed no new shape *form*, only a
slot whose filling is a **sequence** rather than a run of words. A `ListSlot`
carries its own separator phrasing, a second **rank** of separators tried only
when the first leaves too few items — `a or b and c` is two items, not three,
because `and` is cut first — the names its items fill (`left`, `right`), the
smallest number of items that makes the question well formed, and a `comma`
declared as the one admitted mark. It also keeps the case of its items, since
both sides go to the exact-real grammar unresolved and `Pb` is an element where
`pb` is nothing. Counted the way the shapes count, its two separator ranks are
held with the slot rather than with the shape, so the 15 above counts the four
openings and the three shape separators and not those two; that is a gap in the
count rather than in the description, and §13.5 names it.

Nothing here is new language. Each opening is exactly the set of surface forms
`runtime/parser.VERBS` maps to that kind, and each separator is exactly the set
the corresponding branch of `parse_query` splits on. The descriptions restate
the shipped surface; they do not extend it. That is what makes §5 a comparison
rather than a demonstration.

### Which four, and why not the other sixteen

A shape is *an opening, then slots separated by literal words*. Four of the
runtime's twenty answerable kinds are exactly that. The rest are not, and were
left hand-written rather than forced:

| kind | how it is actually recognised |
|---|---|
| `analogy` | an infix operator — `a : b :: c : ?` |
| `verify` | a top-level `=` |
| `comparative` | a suffix, `-er than`, whose two sides must each resolve to a measured use |
| `describe` | a bare concept name that resolves in the register index |

A description language able to express those would be a parser generator. This
one describes one shape, and the point of saying so is that the coverage
figure — 4 of 20 by slots, 7 of 20 across all three families — is then a
measurement of the shapes' reach rather than an apology.

`compare` began in that list and left it: it *is* an opening followed by a
hole, and the only thing that had kept it out was that the hole holds two
values. Three of the remaining four turned out to be one *other* shape rather
than four separate ones — `verify`, `analogy` and, by a second reading,
`compare`, which is §10 — and `comparative` turned out to be the *measure*
shape nested inside an operator, which is §13. `describe` is still none of
them.

### 3.1  The preamble: what may come before the opening

The first version of this description language required the opening at the
head of the string. That was too narrow for the surface the project already
ships — `please measure hot in tea` and `what is measure hot in tea` are
answered today, because the hand-written parser looked for its verb anywhere
in the token stream — and §6 of the first round recorded the gap as a caveat.

Closing it by letting the opening *float free* would have been the wrong
repair: it accepts anything before the opening, and the hand-written parser
demonstrably mis-reads such questions, keeping the stray words inside a slot.
So the description says exactly what it admits, in order:

```
(i would like to know | i want to know | can you | could you |
 would you | kindly | please)*      ← repeatable: the parser stripped these in a loop
(tell me about | what is | address | explain | profile)?
                                    ← once: the parser stripped one opener
```

`repeatable` is not a stylistic flag. The shipped parser strips its courtesy
fillers in a loop and its interrogative opener once, so a description that
reproduces the shipped surface has to say which is which — and the order is
part of the description too: `what is please derive …` stops at `please` and
is refused, because the interrogative has already been taken.

Each piece is a `Phrasing` and carries its own `why`, so the two pieces are
two more judgements on every shape that uses them. That is the whole of the
distance between the seven judgements the four shapes make on their own and the
fifteen the count reports.

**The narrowing is measured.** `build.narrowing()` takes five leading
remainders the preamble does not admit — `the tea`, `give me`, `run`, `in
tea`, `what is please` — writes each in front of a question of each shape,
and puts all twenty to both readers:

| what is measured | result |
|---|---|
| stray openings × shapes | **20 witnesses** (5 × 4) |
| declined by the descriptions, at `unrecognised_opening` | **20 / 20** |
| answered by the deleted branches | **20 / 20** |
| …with the stray words coming back *inside an option* | **20 / 20** |

So the description is strictly narrower than the branch, and every question it
gives up is one the branch got wrong. That is a repair reported as a
narrowing, not a regression hidden as one.

## 4. What does not generalise is counted

Which phrasings count as the same question is a decision about English, and no
description derives one. `Phrasing` therefore cannot be constructed without a
`why`, and the count of those sentences is a reported figure — exactly the
discipline the recipe applies to the coordinates a domain cannot derive.

The fifteen, in full — seven belonging to the shapes, and two more (the
courtesies and the interrogatives of §3.1) counted once for each of the four
shapes that share them:

1. the five `derive` openings are one opening — and `derivation of` and `which
   coordinate` are whole openings rather than a word plus a separator, because
   `derivation of tea` asks nothing and which reading it is cannot be decided
   by counting words;
2. `of`, `for` and `on` all attach a coordinate to the object it is a
   coordinate of;
3. the domain tail admits `in` and nothing else — `within` and `under` would be
   defensible and are deliberately refused, because the tail is optional and
   every word admitted there is a word that can no longer appear inside an
   object's name;
4. the five `measure` openings are one opening, though `how much` and `how far
   up` are questions where the others are imperatives, because the reading
   asked for is the same;
5. `in`, `for`, `against`, `within` and `relative to` all name what a measure
   word is read against — `against` is a stretch in isolation and is admitted
   because the register's own wording uses it;
6. the four `task` openings are one opening, `puzzle` included, because the
   shipped surface has always accepted it;
7. the three `compare` openings are one opening, because each of them asks for
   the order of the values that follow and none of them asserts one — which is
   exactly what makes the relation they carry `compare` rather than `greater`
   or `less`;
8. the seven courtesies are one family, and admitting them is admitting that
   politeness carries no content here;
9. the five interrogative openers are one family, and one is allowed at most
   once, because a question that says `what is what is` is not a question the
   shipped parser reads either.

Judgements 8 and 9 are counted once *per shape that uses them*, which is why
the reported figure is 15 rather than 9: a description that shares a
judgement still pays for it, and a count that hid the sharing would understate
what the descriptions assume about English.

A universal method should make such rules cheap to state and impossible to
state twice. It should not pretend to eliminate them.

## 5. Agreement — the subtractive test

`build.corpus()` generates a question for every opening crossed with every
separator, over the coordinates, objects, measure words and tasks the registers
actually hold, then writes the first question of each kind again behind each of
fourteen admitted decorations (`please`, `please kindly`, `what is`, `please
profile`, …), four to a kind. `build.agreement()` puts each one to *both*
readers. Agreement means the same kind **and** the same options, not merely
the same kind.

| what is compared | result |
|---|---|
| generated questions, described matcher against the branches | **947 / 947 agreed** |
| by kind | derive 416, measure 362, compare 101, task 68 |
| declined by the matcher where the branch answered | **0** |
| answered by the matcher with a different kind or different options | **0** |
| verdict | `exact` |

**Which branches.** The shipped parser no longer *has* a branch for these
four kinds: it reads the descriptions (§10.1). Measuring the descriptions
against that parser would be a tautology, so the deleted code is kept verbatim
in `language/legacy.py` and the agreement above is measured against it.
`legacy.py` is imported by the measurement and by nothing in the runtime, and
`test_language.py` checks both halves of that.

The corpus is generated from the registers rather than written out, so it
cannot quietly avoid the cases the descriptions are bad at; and it is built
from the descriptions' *own* openings, separators and preamble forms, so every
phrasing the descriptions admit is exercised at least once.

## 6. The false-positive half, which is the harder one

A matcher that answered everything would agree with the parser on the corpus
and be useless. The other half of the measurement is that a question of a kind
the descriptions do **not** cover must be declined rather than misread.

`build.other_kind_questions()` takes the question string of every evaluation
case whose kind is not a slot shape — 110 of them, across the sixteen kinds
the slot shapes do not cover and one string the shipped parser does not
recognise either
(`report` 49, `analogy` 10, `describe` 8, `comparative` 7, `verify` 6,
`meaning` 6, `real` 5, and ten others) — and puts each to the matcher.

| what is measured | result |
|---|---|
| questions of undescribed kinds put to the matcher | 110 |
| matched anyway | **0 false positives** |

The caveat this section used to carry — that the matcher required its opening
at the **head** of the question, where the shipped parser would find a verb
anywhere in the token stream — is now §3.1. The described preamble covers the
leading remainders the shipped surface actually accepts, and the twenty
narrowing witnesses measure exactly what is given up: questions the branch
answered by putting the stray words inside a slot.

## 7. Refusals, each with a witness

Every boundary a description names must be **reachable**, or it is a claim
rather than a limit. `build.refusal_audit()` constructs a witness for each and
checks that the matcher declines at exactly that boundary:

| kind | boundary | witness | reached |
|---|---|---|---|
| `derive` | `no_separator` | `derivation of x` | yes |
| `derive` | `empty_coordinate` | `derivation of for x` | yes |
| `derive` | `empty_object` | `derivation of x for` | yes |
| `measure` | `empty_subject` | `how far up` | yes |
| `task` | `empty_task` | `solve task` | yes |
| `compare` | `short_values` | `which is bigger x` | yes |

**6 of 6**, none undescribed and none unreachable. The `measure` description
deliberately names *no* `empty_class` boundary: the class is optional,
`measure hot` is a real question answered across classes, and a boundary that
can never be reached would fail this audit — which is the point of running it.

## 8. The round trip, and why the openings must be disjoint

Writing and matching should be inverse. `QuestionSpec.render_question` writes a
question from the values of its slots, choosing an alternative for each
phrasing; `build.round_trip()` writes every question of the corpus back from
the slots it filled and matches it again.

| what is checked | result |
|---|---|
| questions written back and re-matched | **947 / 947 return the same filling** |

And the four shapes must be a *set*, not a priority list, or the order they
are tried in would be part of the answer. `build.openings_disjoint()` checks
all 17 openings pairwise across different kinds:

| what is checked | result |
|---|---|
| opening pairs where one is a prefix of the other | **0 clashes of 17 openings** |

## 9. The part that is not a measurement

`RequestProject/GLM/Question.lean` models the shape at the level of tokens —
`Phrasing`, `Slot`, `Piece`, `Spec`, and `matchPieces`, the same five rules the
Python matcher runs — and proves what the audits above can only sample.

* `matchPieces_rendered` — **the round trip**. A question written from a shape
  matches back to the slots it was written from, given that each slot's text
  avoids the separator that follows it. §8 checks 947 cases; this is the
  statement for all of them.
* `matchPieces_required_nonempty` — **no silent empty slot**. Whenever the
  matcher answers, every required slot came back with at least one token. A
  refusal is therefore the only way an unnamed thing can leave the matcher.
* `matchPieces_adjacent_holes` — two slots with no word between them match
  nothing, so a shape cannot be written that splits a question arbitrarily.
* `matchPieces_no_separator` — a missing separator is a refusal when something
  after it is required, which is the `no_separator` boundary of §7.
* `matchPieces_lit_none` — a question that does not open the shape is not
  matched: there is no reading in which the opening is skipped.
* `matchPieces_not_both` (with `Phrasing.not_both_matchAt`) — **openings decide
  the shape**. If no alternative of one opening is a prefix of an alternative
  of the other, at most one of the two shapes can be entered. That is §8's
  disjointness check as a theorem, and it is what makes the descriptions a set.

* `runPre_of_skipped` — **the preamble changes nothing.** Where the preamble
  consumes exactly the leading remainder, the shape sees the bare question and
  answers it exactly as if the remainder had never been written. Skipping is a
  described act, not a second parser.
* `runPre_refuses_undescribed` — **and it is still a narrowing.** Where the
  preamble consumes nothing, the opening has to stand at the head, so a
  question that puts anything else there is refused. That is §3.1's twenty
  witnesses as a theorem.
* `skipMany_of_le` — **the fuel decides nothing.** The repeatable skip is
  bounded by the token count so that it is structural and so decidable; past
  the last match, more of the bound changes nothing, which is what makes the
  bound an implementation detail rather than part of the description.

`deriveShape` instantiates all of it on one real description — the shipped
`derive` shape, its five openings and three separators — and nine theorems are
settled by `decide`: `deriveShape_span_ratio_of_tea`,
`deriveShape_what_derives_in_harmonics` (a second opening, a second separator
and the domain tail written out), `deriveShape_refuses_missing_object`,
`deriveShape_refuses_other_opening`, and — against the shipped preamble —
`deriveShape_please`, `deriveShape_please_kindly_what_is`,
`deriveShape_no_preamble`, `deriveShape_refuses_stray_opening` and
`deriveShape_refuses_interrogative_before_courtesy`. The file carries no
`sorry` and no non-standard axiom.

## 10. The second round: the branches deleted, and a second shape family

### 10.1  The descriptions put in place of the branches

The first round closed by naming the next subtractive step: *the shipped
parser is still the one that runs*. It no longer is. The three
`if kind == "derive" / "measure" / "task"` blocks are gone from
`runtime/parser.py`, replaced by

```python
if kind in DESCRIBED_KINDS:
    return _described_query(kind, remainder, question)
```

`_described_query` matches the remainder against the shape, turns the filling
into the query's options, maps a boundary the description marks `raises` to a
`QueryError` and any other boundary to empty slots, and answers
`kind="unknown"` where the opening is not recognised. There is no per-kind
code in that path.

Deleting the branches raises a measurement problem: the descriptions can no
longer be measured against the parser, because for these kinds the parser *is*
the descriptions. So the deleted code is kept verbatim in `language/legacy.py`
and §5's 947 comparisons are made against it. Two tests keep that arrangement
honest — the branches are absent from `runtime/parser.py`, and nothing under
`runtime/` imports `legacy_parse`.

The end-to-end evaluation is unchanged: **130 / 130, 16 expected boundary
refusals, 0 gap**, with those kinds now answered off their descriptions.

### 10.2  Is a second shape worth having?

The first round's closing question was deliberately falsifiable:

> …the honest next step is to ask whether a **second** described shape — an
> infix shape, say, with two operand slots and a described operator — covers
> `analogy` and `verify` together, and to count the judgements it costs. If
> two shapes cover seven kinds, the description language is worth extending;
> if a second shape covers one kind, it is a parser generator being written
> one kind at a time.

It covers **three**: `verify`, `analogy` and the relational half of `compare`.

`language/infix.py` is the second description form. It differs from the first
in a way that is the finding rather than an inconvenience: a slot shape walks
*tokens*, and an infix shape cuts a *string*. Its operands are notations —
`sqrt(2)`, `mass * acceleration` — and a notation is not a run of words. The
second family is therefore a genuinely second primitive, not the first one
rearranged.

| kind | shape | operands | judgements | boundaries |
|---|---|---|---|---|
| `verify` | `(does it hold that \| is it true that \| audit \| check \| verify)? <lhs> = <rhs>` | lhs, rhs | 3 | 3 |
| `analogy` | `<a> : <b> :: <c> : <d>?` | a, b, c, d | 3 | 5 |
| `compare` | `(are \| do \| does \| is)? <left> (the same as \| bigger than \| equal to \| greater than \| larger than \| less than \| smaller than) <right>` | left, right | 3 | 3 |

**8 operands, 34 surface forms, 9 judgements, 11 named boundaries.**

Three things a slot shape cannot say are said here:

* an operator alternative may carry a **meaning**, because `bigger than` and
  `smaller than` are the same shape asking opposite questions;
* an **inner** operator cuts each side again, which is what lets one
  description hold the analogy's four terms;
* an operand may be **described but not carried** — the analogy's fourth term
  is required for the question to be well formed and is the hole the answer
  fills, so the runtime never receives it.

The `=` operator carries `not_adjacent_to`, so `==`, `<=` and `>=` do not
enter the shape, and case is *preserved*, because an operand of an equation is
a notation and the shipped parser preserves it too.

### 10.3  Measured the same way

`build.infix_corpus()` crosses every operator alternative with every operand
tuple drawn from the registers, with the opening written and left out, and
writes the first question of each kind again behind every admitted preamble.

| what is compared | result |
|---|---|
| generated infix questions, descriptions against the shipped parser | **174 / 174 agreed** |
| by kind | verify 38, analogy 17, compare 119 |
| declined, or answered with different operands | **0, 0** |
| evaluation questions the infix shapes must not cut | **110 put, 0 matched** |
| verdict | `exact` |

### 10.4  What the second family does not cover, named

The infix shapes are **measured, not yet wired in**: the parser still has its
`verify`, `analogy` and `compare` branches. That is not caution, it is a
missing piece of description language, and `build.UNDESCRIBED_PARTS` names
each one:

| part | what describing it would need |
|---|---|
| `verify`: the semantics qualifier (`check tensor force = …`) | a described **modifier** — a third thing a shape can hold, being neither operand nor operator |
| `analogy`: the subspace and limit options | described **trailing options**, read today by the parser's own option scanners |
| `compare`: the list form (`compare a and b`) | a described **list** — a slot whose filling is a sequence |
| `comparative`: an operator between two *measured uses* | a **nested** shape: an operand that is itself a shape |

So the coverage figure at the close of the second round was **6 of 20
answerable kinds across 2 shape families**, 3 of them read off by the runtime,
and the next round's work was those four parts rather than a fourth family.
§13 is that round: all four parts are now described, all four branches are
gone, and the figure is 7 of 20 across 3 families with all seven read off by
the runtime.

## 11. What it does not do

*Brought up to date at the end of the third round; §13 is where each of these
was measured.*

* **Seven kinds are described, not twenty.** All seven are read by the
  runtime, and the other thirteen have a branch apiece. `describe` and
  `report` are not shapes of any family, and nothing measured here says they
  can be described by one.
* **The nested family reads more than the branch it replaced**, by 148
  questions of the 628-question corpus. That is declared as a widening and
  accounted for question by question rather than counted as agreement — but it
  is still a difference, and it exists because the branch had spelled out a
  copy of the shape it should have nested.
* **The judgements are counted, not removed**, and they should not be.
* **The preamble is a narrowing.** §3.1 gives up twenty questions the branch
  answered. Every one of them was answered wrongly, which is why the trade is
  reported as a repair — but it is still a trade, and a leading remainder
  outside the described families is refused.
* **A description is trusted about its own vocabulary.** The openings are taken
  from `VERBS` and the separators from the branch they replace, so the round
  shows the *shape* is describable — not that the word list is right.

## 12. Where the code is

| piece | file |
|---|---|
| the slot shape, its slots and its preamble | `overlay/glm_universal/language/question.py` |
| the list slot, the second shape family and its matcher | `overlay/glm_universal/language/infix.py` |
| the nested shape — an operator whose sides are a tightened shape | `overlay/glm_universal/language/nested.py` |
| the eight descriptions | `overlay/glm_universal/language/descriptions.py` |
| the three generic matchers, the corpora and the audits | `overlay/glm_universal/language/build.py` |
| the seven deleted parser branches, frozen | `overlay/glm_universal/language/legacy.py` |
| the measured result, and `ask` | `overlay/glm_universal/language/report.py` |
| the report subject | `report language` (`runtime/reports/language.py`, column 3 in `runtime/tct_engine.py`) |
| the machine-checked half | `RequestProject/GLM/Question.lean` (the slot shape) and `RequestProject/GLM/QuestionNested.lean` (the nested shape) |
| the tests | `overlay/glm_universal/tests/test_language.py` (122 tests) |
| the CLI case | `report-language` |

---

## 13. The third round: the four undescribed parts, and the four branches they were blocking

§10.4 ended with a list rather than a feeling: four parts of the described
kinds that no description could yet say, each naming the piece of description
language it needed. All four are now described, and the branches they were
the obstacle to are gone from `runtime/parser.py` and frozen beside the first
three in `language/legacy.py`.

| part | what it needed | branch deleted |
|---|---|---|
| `verify`: the semantics qualifier (`check tensor force = …`) | a **modifier** — a word that directs how the operands are read without naming one | the equation branch |
| `analogy`: the subspace and limit options | **trailing options** — a value written after the operands that narrows the answer | the analogy operator |
| `compare`: the list form (`compare a and b`) | a **list** — a hole whose filling is a sequence | both comparison branches |
| `comparative`: an operator between two *measured uses* | a **nested** shape — an operand that is itself a shape | the comparative |

### 13.1  The three that are not slots

A **list** is a hole that holds more than one value. Which words separate the
items — `and`, `versus`, `vs`, a comma, and `with` at a second rank — is a
decision about English exactly as a shape's separators are, so it is written
down and counted rather than scanned for. The `compare` slot shape now holds
one, and its filling is a sequence.

A **modifier** is the third thing a shape can hold, being neither operand nor
operator. `check tensor force = mass * acceleration` asks the same question of
the same equation under a stricter reading, and the word has to come *out* of
the operands or the equation being audited would carry it. Where it may be
written and where it may be *removed* are two different questions, and the
answer is the point: it is read off the whole question wherever it stands, and
removed only at the head and in the trailing frame (`… under tensor
semantics`). A `tensor` in the middle of an equation stays exactly where it
is.

A **trailing option** is a value written after the operands — the analogy's
subspace and its limit — read by the description rather than by the parser's
own option scanners.

### 13.2  The nested shape, and the price of reuse

`is cold in stellar_surface hotter than hot in tea` is infix, but its operands
are not text: each side has to be a *measured use*, which is the `measure`
shape itself. So the nested description holds an operator and **the shape its
sides nest**, tightened — the opening dropped, because inside a comparative a
use is recognised by its position rather than by the word `measure`; the class
made required, because `hot hotter than cold in tea` compares a reading
against nothing; and both slots narrowed to a single name. That last
restriction is what keeps an exact-real comparison out of the shape, and it is
a theorem rather than a special case: `is sqrt(2) greater than 7/5` forms the
operator and is still refused, because `sqrt(2)` names no class.

The operator is **formed** rather than listed: any `-er than` word, or any
word inside `as … as`. Which degree words mean anything is the register's
decision, and enumerating them in the shape would put that decision in two
places. Which word was written is carried, because the direction the
comparison asserts is read off the register from it.

Reuse has a measured price, and it is the finding of this section. A side of a
comparative is the measure shape, and the measure shape admits **five**
separators. The branch this replaces spelled its sides out with a regular
expression of its own, which listed four of them — `in`, `for`, `against`,
`within` — and not `relative to`. So **148** corpus questions written with
`relative to` on a side are read here and were unknown to the branch. That is
declared as a **widening** rather than counted as agreement, every widened
question is accounted for by it with **0 left over**, and the two-word
separator being the one that drifted is the tell: a side spelled out a second
time is a side that drifts from the shape it copies.

### 13.3  Measured the same way

| what is compared | result |
|---|---|
| slot corpus, descriptions against the frozen branches | **947 / 947 agreed**, 0 declined, 0 disagreed |
| infix corpus | **201 / 201 agreed**, 0 disagreed |
| nested corpus | **480 / 628 agreed**, **148 widened** (0 unexplained), 0 disagreed |
| round trips, slot shapes | **947 checked, 0 broken** |
| questions of undescribed kinds put to the shapes | 110, 110 and 123 put; **0 matched** |
| narrowing witnesses | **20 declined here, 20 misread by the branches** |
| boundary witnesses | 6 slot, 11 infix, 2 nested — every named boundary reached |
| judgements about English | **15** across 4 slot shapes, **13** across 3 infix shapes, **4** across 1 nested shape |
| verdict | `described` |

Every kind any of the three families describes — `derive`, `measure`, `task`,
`compare`, `verify`, `analogy`, `comparative` — is read off its description by
the runtime, with no branch left for any of them. The end-to-end evaluation is
unchanged at **130 / 130** with the same 16 boundary refusals.

### 13.4  What is not a measurement

`RequestProject/GLM/QuestionNested.lean` carries the part that is a theorem,
as `Question.lean` does for the slot family:

* `ListCut.cut_two` — the **round trip for a list**: a list written as one
  item, a separator and another, where neither item holds a separator, cuts
  back to exactly those two items, whichever admitted separator was used.
  `ListCut.sepAt_shorter` is why the cut terminates — an empty separator form
  is not admitted, so every cut consumes at least one token — and
  `cut_ne_nil` and `cut_append` are the two facts the round trip rests on.
* `ModifierFrame.strip_head`, `strip_frame`, `strip_middle` — the modifier is
  removed **exactly twice**. The third of those is the one worth having: a
  word written inside an operand is returned unchanged, which is the
  difference between a directive and a deletion.
* `NestedSpec.run_rendered` — the **round trip for a nested shape**: a
  question written from two fillings of the side shape, with an operator
  between them, reads back as exactly those two fillings and the degree word
  it was written with.
* `NestedSpec.run_no_operator` and `NestedSpec.run_side_refused` — the two
  refusals as theorems. The second is the boundary: the operator may be formed
  and the question still declined.

`compareCut`, `tensorModifier` and `comparativeShape` instantiate all of it on
the shipped surfaces, with the shipped behaviour decided by computation.

### 13.5  Coverage, and the thirteen kinds that are not described

**7 of 20** answerable query kinds are described, across **3** shape families,
and all seven are read off their descriptions by the runtime. What is *not*
claimed is that the three families cover the surface, and the measurement of
that is the other thirteen: `describe`, `nearest`, `product`, `cluster`,
`spatial`, `project`, `trilinear`, `coherence`, `report`, `angle`,
`pi_groups`, `meaning` and `real` each still have a branch apiece.

Two of them are worth naming as *kinds a shape should not be bent to fit*:
`describe` is a bare concept name resolving in the register index, and
`report` is a subject table. Neither is a shape of any family, and a count of
20 with two descriptions bent to fit would be a worse result than a count of 7
with the reason written down.

One further limit is a limit of the *count* rather than of the description.
A shape's judgement figure is the phrasings held in the shape plus the
preamble's two, and the comparison list's two separator ranks are held with
the slot, so they carry a `why` apiece that the 15 does not include. Nothing
about them is unstated — both `why`s are in `descriptions.py` and both are
checked — but a later round that wants the judgement count to be exactly the
number of `why`s in the file will have to reach inside the slots for them.

`build.UNDESCRIBED_PARTS` no longer lists a missing piece of description
language. What it lists now are **3 limits**, which is a different kind of
entry: the thirteen undescribed kinds, the folding of case in a described
kind's operands, and the one narrowing this family adds — a verb *inside* an
operand is not removed, because a described opening is read at the head and a
described closing at the tail and nowhere else.
