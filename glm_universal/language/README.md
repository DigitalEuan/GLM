# `glm_universal/language` — the question shape made an object

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

```
language/
├── question.py      a QuestionSpec — the declarative description of one
│                    slot-shaped question — built from Phrasings (sets of
│                    surface words that count as the same thing, each
│                    carrying the judgement that makes them one set), Slots
│                    (named holes with a role), a Preamble (what may precede
│                    the opening) and named Refusals
├── infix.py         the second shape family: an InfixSpec cuts a *string* at
│                    a described operator, for questions whose operands are
│                    notations rather than runs of words
├── descriptions.py  six of the runtime's query kinds written down and
│                    nothing else — derive, measure, task as slot shapes and
│                    verify, analogy, compare as infix shapes — with the
│                    kinds that are neither named and left alone
├── build.py         the two generic matchers: question → Match or Decline.
│                    Neither knows anything about any kind.  Also the
│                    generated corpora, the agreement audits, the narrowing
│                    witnesses, the round trip and the refusal audit
├── legacy.py        the three hand-written parser branches as they were on
│                    the day they were deleted, kept *only* so the agreement
│                    audit has something to measure against.  Nothing in the
│                    runtime imports it
├── report.py        the measured result (`language_report`) and the query
│                    surface (`ask`)
└── __init__.py      public API exports
```

## The problem this package solves

[`../recipe/`](../recipe/README.md) made a *domain* declarative: what its
objects hold, how each coordinate is derived, what a reading is and what must
be refused. The way a question about that domain is **asked** stayed
hand-written. `derive <coordinate> of <object>` is generic in the coordinate
and in the object, but the phrase itself was a branch of
`runtime/parser.py`, and so were `measure`, `task` and every alias each of
them accepts. A new domain arrived with its carriers and then waited for
someone to write its questions.

This package makes the question's *shape* an object, and — for the three slot
shapes — the runtime now **reads the description instead of the branch**.

## Family one: an opening, named slots, and the words between them

A `QuestionSpec` is an **opening**, then **named slots** separated by
**literal words**, with an optional tail, an optional **preamble** and a set
of named boundaries it must refuse at.

| kind | shape | slots | openings | separators | judgements |
|---|---|---|---|---|---|
| `derive` | `(derivation of \| what derives \| which coordinate \| coordinate \| derive) <coordinate> (for \| of \| on) <object> in <domain>?` | coordinate, object, domain? | 5 | 3, then 1 | 5 |
| `measure` | `(how far up \| how much \| measure word \| relative measure \| measure) <subject> (relative to \| against \| for \| in \| within) <class>?` | subject, class? | 5 | 5 | 4 |
| `task` | `(solve task \| worked example \| puzzle \| task) <task>` | task | 4 | — | 3 |

That is **6 slots and 44 surface forms at 12 judgements** — 14 openings, no
one of which is a prefix of an opening of another shape, so the three
descriptions are a *set* rather than a priority list and the order they are
tried in cannot change an answer.

### The preamble: what may come *before* the opening

The first version of this description language required the opening at the
head of the string. That was too narrow for the surface the project already
ships: `please measure hot in tea` and `what is measure hot in tea` are
answered today, because the hand-written parser looked for its verb anywhere
in the token stream.

Letting the opening float free would accept *anything* before it. Instead the
description says exactly what it admits, as an ordered `Preamble`:

```
(i would like to know | i want to know | can you | could you |
 would you | kindly | please)*      ← repeatable: the parser stripped these in a loop
(tell me about | what is | address | explain | profile)?
                                    ← once: the parser stripped one opener
```

Each piece is a `Phrasing` and so carries its own justification; admitting a
word here is a decision about English exactly as admitting a separator is,
and the audit counts it the same way. That is why the per-shape judgement
counts above went from 3/2/1 to 5/4/3.

**Describing it is a narrowing, and the narrowing is measured.**
`build.narrowing()` takes five stray openings the preamble does not admit —
`the tea`, `give me`, `run`, `in tea` and `what is please` — writes each in
front of a question of each shape, and puts the result to both readers:

| | |
|---|---|
| stray openings × shapes | **15 witnesses** |
| declined by the descriptions, at `unrecognised_opening` | **15 / 15** |
| answered by the deleted branches, with the stray words *inside an option* | **15 / 15** |

So the description refuses exactly where the branch guessed, and every
witness says which option the guess polluted.

## Family two: an operator that cuts the question in two

The round that closed the first family named the honest next question rather
than answering it: does a **second** described shape cover more than one
kind, or is this a parser generator being written one kind at a time?

It covers three. An `InfixSpec` cuts a *string* at a described operator — its
operands are notations (`sqrt(2)`, `mass * acceleration`), and a notation is
not a run of words, which is why this is a genuinely second primitive rather
than the first one rearranged.

| kind | shape | operands | judgements |
|---|---|---|---|
| `verify` | `(does it hold that \| is it true that \| audit \| check \| verify)? <lhs> = <rhs>` | lhs, rhs | 3 |
| `analogy` | `<a> : <b> :: <c> : <d>?` | a, b, c, d | 3 |
| `compare` | `(are \| do \| does \| is)? <left> (the same as \| bigger than \| equal to \| greater than \| larger than \| less than \| smaller than) <right>` | left, right | 3 |

Three things a slot shape has no way to say are stated here:

* an operator alternative may carry a **meaning** — `bigger than` and
  `smaller than` are the same shape asking opposite questions, so the surface
  form that matched is part of the answer;
* an **inner** operator cuts each side again, which is what lets one
  description hold the analogy's four terms;
* an operand may be **described but not carried** — the analogy's fourth term
  is required for the question to be well formed and is the hole the answer
  fills, so it is never passed to the runtime.

The `=` operator is guarded by `not_adjacent_to`, so `==`, `<=` and `>=` do
not enter the shape, and case is *preserved*, because an operand of an
equation is a notation and the shipped parser preserves it too.

## What is deliberately still hand-written

Fourteen of the twenty answerable kinds are neither shape, and are left alone
rather than forced: `describe` is a bare concept name resolving in the
register index, `report` is a subject table, and `comparative` needs an
operator between two *measured uses* rather than between two notations.

Four **parts** of the six kinds that *are* described are also still
hand-written, and are named in `build.UNDESCRIBED_PARTS` rather than left
implicit:

| part | what describing it would need |
|---|---|
| `verify`: the semantics qualifier | a described **modifier** — a third thing a shape can hold |
| `analogy`: the subspace and limit options | described trailing options, read today by the parser's option scanners |
| `compare`: the list form (`compare a and b`) | a described **list** |
| `comparative`: an operator between two measured uses | a **nested** shape — an operand that is itself a shape |

Those four are the next round's work, and until they are done the infix family
is *measured* rather than wired in.

## The test, and it is run rather than asserted

`build.corpus()` writes a question for every opening crossed with every
separator, over the coordinates, objects, measure words and tasks the
registers actually hold, then writes the first question of each kind again
behind each of fourteen admitted decorations. `build.infix_corpus()` does the
same for the operators and their operands. Each question goes to *both*
readers. Agreement means the same kind **and** the same options, not merely
the same kind.

| what is compared | result |
|---|---|
| generated slot questions, descriptions against the deleted branches | **846 / 846 agreed** (derive 416, measure 362, task 68) |
| of those, declined by the matcher or answered with different options | **0 declined, 0 disagreed** |
| evaluation questions of the fourteen *undescribed* kinds | **114 put, 0 matched** — every one declined, not misread |
| each question written back from the slots it filled and matched again | **846 / 846 round-tripped** |
| named refusal boundaries, each given a witness that reaches it | **5 / 5**, none undescribed and none unreachable |
| openings of different shapes, pairwise | 14 openings, **0 prefix clashes** |
| stray openings the preamble does not admit | **15 declined here, 15 misread there** |
| generated infix questions, descriptions against the shipped parser | **174 / 174 agreed** (verify 38, analogy 17, compare 119) |
| evaluation questions the infix shapes must not cut | **110 put, 0 matched** |
| verdict | `described`, 6 of the 20 answerable query kinds across 2 shape families, 3 of them read off by the runtime |

The false-positive half is the one that is easy to skip and is the point: a
question of a kind the descriptions do not cover has to be **declined with the
boundary named**, which is the difference between a stated limit and a gap.

### Why `legacy.py` exists

The parser no longer holds a branch for `derive`, `measure` or `task`: it
calls the descriptions. Measuring the descriptions against *that* parser would
be a tautology, so the deleted branches are kept verbatim in `legacy.py` and
the agreement above is measured against them. `test_language.py` checks both
halves of that arrangement — the branches are gone from
`runtime/parser.py`, and nothing under `runtime/` imports `legacy_parse`.

## Judgements, counted rather than hidden

Which phrasings count as the same question is a decision about English, and no
description derives one. Every `Phrasing` therefore carries the sentence that
justifies treating its alternatives as one set, and the count of those
sentences is a reported figure — the same discipline
[`../recipe/`](../recipe/README.md) applies to the coordinates a domain cannot
derive. **Twelve** across the slot shapes and **nine** across the infix
shapes: that `of`, `for` and `on` attach a coordinate to its object alike;
that `in`, `for`, `against`, `within` and `relative to` all name what a
measure word is read against; that the five `derive`, five `measure` and four
`task` openings are each one opening; that the domain tail admits `in` and
nothing else, because every word admitted there is a word that can no longer
appear inside an object's name; that the seven courtesies are one family and
the five interrogatives another; and, on the infix side, which operator forms
are one operator, which of them mean the same comparison, and which verbs are
an optional way of saying the equation out loud.

## Reachable as

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report language" --verify-tct
PYTHONPATH=. python3 GLM.py -q "derive span_ratio of tea"
PYTHONPATH=. python3 GLM.py -q "please measure hot in tea"
```

## Where the rest of it is

* `RequestProject/GLM/Question.lean` — the part that is not a measurement:
  writing and matching are inverse on the questions a shape can write
  (`matchPieces_rendered`), a required slot never comes back empty
  (`matchPieces_required_nonempty`), a shape with no separator between two
  holes matches nothing (`matchPieces_adjacent_holes`), two shapes whose
  openings are not prefixes of one another cannot both be entered
  (`matchPieces_not_both`), and — for the preamble — skipping a described
  leading remainder leaves the match exactly what the bare question gives
  (`runPre_of_skipped`) while an undescribed one is still refused
  (`runPre_refuses_undescribed`).
* `../tests/test_language.py` — 90 tests over the descriptions, the matcher,
  the refusal boundary, the round trip, agreement with the deleted branches,
  the preamble, the narrowing, the second shape family, exactness and the
  runtime.
* [`../../../studies/LANGUAGE_STUDY.md`](../../../studies/LANGUAGE_STUDY.md) —
  the write-up, with every figure above and what the round does *not* do.
