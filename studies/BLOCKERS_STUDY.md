# What is holding the GLM back — six blockers, each with its measurement and the smallest experiment that would remove it

## Tier 0 — the coarse read

**Question.** Between what this system does now and reasoning over natural language, mathematics, physics, chemistry and Python script, what is actually in the way — and can each obstacle be demonstrated with a measurement rather than described with an adjective?

**Verdict.** Every blocker names a measurement: the pre-registered language probe scores 2 correct, 1 wrong and 17 refused of 20 against a declared pass mark, so it fails; the lexicon now holds 57 of the 69 words the probe uses and widening it moved the score by nothing, so the binding blocker is the parser rather than the vocabulary; and of this round's measured results only 2 derive an answer rather than look one up.

**Deciding figure.** <!--figure:probe-correct-->2<!--/figure--> correct, <!--figure:probe-wrong-->1<!--/figure--> wrong and <!--figure:probe-refused-->17<!--/figure--> refused of <!--figure:probe-questions-->20<!--/figure--> pre-registered questions, against a declared pass mark of <!--figure:probe-pass-mark-->10<!--/figure--> correct and at most 1 wrong.

**Recomputed by.** `glm_universal.reasoning.blockers.measure`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

The rest of this round is about improving something the system already does.
This document is about the distance between that and what a reader would call
reasoning. It is deliberately unflattering, and it is written to be checkable:
every blocker names the measurement that demonstrates it and the smallest
experiment that would remove it, and the language probe was declared — its
questions, its scoring and its pass mark — before it was run.

## 1. Three things that are not the same

Almost every misunderstanding of a system like this one comes from running
three different mechanisms together. They are kept apart here, and every
measured result of the round is assigned to exactly one of them:

<!-- generated: blockers-ledger -->
| measured result | what it is | why it is that | measured in |
|---|---|---|---|
| register lookup by exact name (the describe solver) | `table` | the name is matched against the register index; no quantisation happens and no geometry is consulted | `glm_universal.runtime.session` |
| retrieval of a perturbed carrier over the norm ladder | `addressed` | the query is not the stored key -- it is the key plus a declared offset -- and the lattice cell is what recovers the identity | `glm_universal.reasoning.norm_escalation` |
| register, chemistry, physics, harmony and program-text classification of a perturbed carrier | `addressed` | the same mechanism answering a coarser question; the answer is still a label the register holds | `glm_universal.reasoning.operation_escalation` |
| dimensional exponent recovery | `addressed` | the exponents are read out of the cell, not computed; what the geometry supplies is the reading | `glm_universal.reasoning.operation_escalation` |
| equation checking over recovered exponent vectors | `derived` | the seven integer additions and the comparison are done by the system over values it recovered; no register holds the answer to the claim being checked | `glm_universal.reasoning.operation_escalation` |
| the containment order of the norm family | `derived` | every containment is composed from a handful of relative rules and then checked on generated points; none is stored | `glm_universal.substrate.norm_family` |

Of the measured results of this round, 3 are `addressed`, 2 are `derived`, 1 are `table`.  what is demonstrated here is coverage and mechanism, not reasoning: the probe measures how much open natural language the system takes at all, the ledger says which of table lookup, geometric addressing and derivation each measured result actually is, and the blockers name what stands between the two.
<!-- end generated -->

The distinction is mechanical, not rhetorical. *Table* means a name was matched
against an index. *Addressed* means the query was **not** the stored key — it
was the key plus a declared offset — and the lattice cell is what recovered the
answer; the geometry is doing work, but the answer is still something a
register holds. *Derived* means no register holds the answer to the question
asked: the system computed it.

Read that way, most of what this project measures is in the middle class. That
is a real capability and a narrow one, and it is the honest description of what
the escalation rounds have bought.

## 2. The pre-registered language probe

**Declared before the run**, in `glm_universal.reasoning.blockers`: twenty
questions, four from each of five domains; each asked in a canonical phrasing
and again in a declared paraphrase; an asking scores *correct* when the session
answers and the declared fragment appears in the answer or in the solution's
checkable `expected` mapping, *wrong* when it answers and the fragment does
not, and *refused* when it does not answer; the probe passes if at least 10 of
the 20 canonical askings are correct with at most 1 wrong.

<!-- generated: blockers-probe -->
| domain | question | a right answer contains | canonical | paraphrased | query kind |
|---|---|---|---|---|---|
| natural language | *what does velocity mean?* | `velocity` | `refused` | `correct` | `unknown` |
| natural language | *what is velocity the derivative of?* | `position` | `refused` | `refused` | `describe` |
| natural language | *is energy more abstract than water?* | `energy` | `refused` | `refused` | `unknown` |
| natural language | *why is the sky blue?* | `rayleigh` | `refused` | `refused` | `unknown` |
| mathematics | *what is 2 + 2?* | `4` | `correct` | `refused` | `describe` |
| mathematics | *is 91 prime?* | `no` | `refused` | `refused` | `unknown` |
| mathematics | *what is the greatest common divisor of 12 and 18?* | `6` | `refused` | `refused` | `describe` |
| mathematics | *what is the prime limit of the interval 3/2?* | `3` | `refused` | `refused` | `describe` |
| physics | *describe speed_of_light* | `speed_of_light` | `correct` | `correct` | `describe` |
| physics | *what are the dimensions of force?* | `M` | `refused` | `refused` | `unknown` |
| physics | *is force equal to mass times acceleration dimensionally?* | `true` | `refused` | `refused` | `compare` |
| physics | *convert 3 metres to feet* | `9.84` | `refused` | `refused` | `unknown` |
| chemistry | *describe C* | `carbon` | `wrong` | `refused` | `describe` |
| chemistry | *what is the atomic weight of carbon?* | `12.011` | `refused` | `refused` | `describe` |
| chemistry | *which block of the periodic table is chlorine in?* | `halogen` | `refused` | `refused` | `unknown` |
| chemistry | *what is the molar mass of water?* | `18` | `refused` | `refused` | `describe` |
| program text | *which file is GLM.NormFamily.family_tower in?* | `NormFamily.lean` | `refused` | `refused` | `unknown` |
| program text | *which module defines the function rung_audit?* | `norm_escalation` | `refused` | `refused` | `unknown` |
| program text | *what does glm_universal.substrate.norm_family.completeness return?* | `complete` | `refused` | `refused` | `unknown` |
| program text | *how many rungs does the norm family have?* | `25` | `refused` | `refused` | `unknown` |

**Declared before the run:** the probe passes if at least 10 of 20 canonical askings are correct with at most 1 wrong.

**What happened:** 2 correct, 1 wrong, 17 refused — **passed = `False`**.  In paraphrase: 2 correct, 0 wrong, 18 refused, with 17 of 20 questions scoring the same both ways.  11 of the canonical askings were not recognised as any query kind at all.

a refusal costs the probe a point and is not a failure of the refusal contract; a wrong answer is both. The probe measures coverage of natural language, and the pass mark was declared before the run.
<!-- end generated -->

The probe scores <!--figure:probe-correct-->2<!--/figure--> correct,
<!--figure:probe-wrong-->1<!--/figure--> wrong and
<!--figure:probe-refused-->17<!--/figure--> refused of
<!--figure:probe-questions-->20<!--/figure-->; the lexicon holds
<!--figure:probe-lexicon-held-->57<!--/figure--> of the
<!--figure:probe-lexicon-words-->69<!--/figure--> words it uses, and
<!--figure:probe-derived-->2<!--/figure--> of this round's measured results
derive an answer rather than look one up.

**What that shows, carefully.** The probe fails its declared mark, and it fails
it in a particular way: almost every miss is a *refusal*, and most refusals are
the query not being recognised as any kind of query at all. That is a coverage
failure, not a safety failure — the system does not invent answers it does not
have — and the one wrong answer is instructive: asked to describe the element
`C`, it answers with the carrier's geometry rather than with anything a person
asking about carbon wanted. The answer is true and it is not responsive, which
is a third failure mode the scoring rule deliberately counts as wrong.

**The experiment blocker 1 declares has now been run**, and it changes how
this section should be read. Hand-written into the system's own query grammar,
six of the twenty questions are answered rather than two; ten more are held by
a register row or a shipped function that no query kind returns; four are held
nowhere. So the seventeen refusals are three different failures, and the
parser — the instrument this blocker names — is worth four of them.
[`PROBE_ORACLE_STUDY.md`](PROBE_ORACLE_STUDY.md) is the measurement, its
declared translations and its two scoring rules.

Paraphrase matters more than it should. One question scores differently in its
two phrasings, which for a system with a fixed query grammar is expected, and
is the measurement behind blocker 4.

## 3. The blockers

<!-- generated: blockers-table -->
| blocker | what it means | the measurement that demonstrates it | the smallest experiment that would remove it |
|---|---|---|---|
| **there is no parser from open natural language to a query** | the session recognises a fixed grammar of query kinds; a question outside it is not misunderstood, it is not understood at all | `probe.canonical.refused` = 17 and `probe.unrecognised` = 11 | take the twenty probe questions and hand-write the query each one should become; measure how many of the twenty the existing solvers then answer. That separates 'cannot parse' from 'cannot answer' without building a parser -- run in reasoning/probe_oracle.py, which finds the parser worth 4 of the 20 and a surface onto what the registers already hold worth 10 |
| **the lexicon is small and closed** | words the lexicon does not hold cannot be grounded, and most words of an ordinary question are not in it | `lexicon.coverage` = 19/23 | add the missing content words of the probe to the lexicon with their primitives, and re-run the probe; if the score does not move, the blocker is the parser and not the vocabulary |
| **answers are fields, not compositions** | the registers hold values; the system has one measured operation that composes two of them into a third, and it composes exponents only | `faculty.derived_count` = 2 | extend the equation operation from checking a claim to solving one -- given two operands and the claim, emit the third exponent vector -- and measure exactness against the register |
| **surface form decides whether a question is answered** | the same question in two phrasings is not the same query to the system | `probe.stable` = 17 | paraphrase each probe question three ways rather than one and report the spread; a faculty that is stable under paraphrase would show equal scores |
| **program text is a register the system does not have** | the Lean development is addressed; this package's own Python is not addressed by anything, and nothing reads a script as a carrier | `python.nearest_shares_module` = 112 | the experiment in python_addressing is that smallest experiment, run here: address 240 functions by 24 syntax counts and measure nearest-neighbour module agreement against a digest control and chance |
| **the refusal contract buys safety at the cost of coverage** | the ladder refuses rather than answering wrongly, and the price is the refused queries; nothing in the system reduces that price except a better reading | `escalation.refused` = 101 | measure whether a second, independent reading -- the lexical address book -- answers any of the queries the ladder refuses, which would show refusals are a single-channel limit rather than an information limit |
<!-- end generated -->

## 4. The program-text experiment, run rather than proposed

Blocker 5 says program text is a register the system does not have. The
smallest experiment that would show whether the substrate reaches it at all is
small enough to run here, so it was: address this package's own Python
functions by 24 counts of syntax — arguments, branches, calls, comprehensions,
depth, and nothing else — quantise each to the nearest point of rung `A`, and
ask how often a function's nearest neighbour comes from the same module.

<!-- generated: blockers-python -->
| reading | nearest neighbour shares a module | of | rate |
|---|---|---|---|
| 24 syntax counts, quantised to the nearest point of rung `A` | 112 | 240 | 46.7 % |
| a digest of the function's own name, quantised the same way | 34 | 240 | 14.2 % |
| chance — two functions drawn at random | — | 240 | 17.6 % |

240 functions over 12 modules, addressed by 24 counts of syntax and nothing else — no name, no module, no path.  the vector holds syntax counts only -- no name, no module, no path -- so a rate above chance is the geometry carrying something about the code.

Beside it, the vocabulary measurement: of the 69 content words the probe uses, the lexicon holds 57 and does not hold 12 — a coverage of 82.6 % against a lexicon of 149 words.
<!-- end generated -->

The reading beats both controls. That is not "the system understands Python":
the vector holds no semantics, the experiment answers one question about
locality, and nothing in the running system consults it. What it does show is
that the blocker is an absence of machinery rather than an absence of signal —
the geometry has something to grip on, and building the register is the
follow-up rather than a gamble.

## 4a. The vocabulary experiment, run rather than proposed

Blocker 2 named its own smallest experiment: *add the missing content words of
the probe to the lexicon with their primitives, and re-run the probe; if the
score does not move, the blocker is the parser and not the vocabulary.* That
experiment has now been run. Fifty-four concepts were written into
`glm_universal.data_objects.semantic_lexicon` — the probe's chemistry,
mathematical, program-text and verb vocabulary — each with all ten semantic
primitives and up to four relations, and beside them a declared morphology:
a finite, hand-written table of surface forms (`defines` → `define`,
`metres` → `metre`, `rungs` → `rung`), with no stemming rule and no guessing.

The prediction and the rule for reading the outcome were both recorded in
`glm_universal.reasoning.blockers.VOCABULARY_EXPERIMENT` before the words were
written.

<!-- generated: blockers-vocabulary -->
| measurement | before the words were added | after | change |
|---|---|---|---|
| content words of the probe the register holds | 10 of 69 | 57 of 69 | 82.6 % |
| the same, after the declared surface forms | 10 of 69 | 69 of 69 | 100.0 % |
| concepts in the register | 95 | 149 | +54 |
| the probe, canonical askings: correct | 2 | 2 | — |
| the probe, canonical askings: wrong | 1 | 1 | — |
| the probe, canonical askings: refused | 17 | 17 | — |

**Declared before the words were written:** the probe's canonical score does not move by more than one asking: the refusals are the session failing to recognise a query kind, not the lexicon failing to hold a word.

**How the outcome is read, also declared first:** coverage must rise by at least half of the words that were missing for the experiment to have been carried out at all; if it does and the canonical score moves by at most one asking, the vocabulary is not the binding constraint and blocker `parse` is.

**What happened:** 54 concepts and 93 declared surface forms were added; the strict coverage of the probe's content words rose from 10 of 69 to 57 of 69, and every remaining word is an inflection the declared forms resolve. The probe's canonical score moved by 0 askings — **prediction held = `True`**.

the vocabulary is not the binding constraint: the register now holds the probe's words and the probe scores the same.
<!-- end generated -->

**What that shows.** The register now holds the probe's vocabulary — 57 of the
69 content words the probe uses outright, and the remaining twelve through the
declared surface forms — and widening it moved the probe's score by nothing:
the probe scores exactly what it scored without it. The vocabulary was not what
the probe was measuring: blocker 1, the absence of a parser from open natural
language to a query, is the binding one, and blocker 2 is settled — as a
negative result about itself. The words are worth keeping anyway, because the
register they are in is the one a parser would have to read, but nothing in
this round's score is bought by them, and the study says so rather than
reporting the coverage rise as progress.

## 5. What this does and does not claim

It claims exactly the faculty measured, under the perturbation declared:

* **Not claimed:** general reasoning, understanding, or competence in any of
  the five domains. The probe is the measurement of how much open natural
  language the system takes at all, and it is 2 of 20.
* **Not claimed:** that the escalation results elsewhere in this round are
  reasoning. They are geometric addressing of perturbed carriers, which is the
  middle class of §1, and one operation — dimensional equation checking — that
  reaches the third.
* **Claimed:** that each blocker above is demonstrated by the measurement
  beside it, on the sample and the perturbation declared, and that the
  experiments named would settle the corresponding question.

## 6. How to re-run this

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools blockers           # the stored measurement
PYTHONPATH=. python3 -m glm_universal.tools blockers --write   # re-take it (about a minute)
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_blockers.py -q
```
