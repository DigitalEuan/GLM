# Hand-translating the probe — separating *cannot parse* from *cannot answer*

## Tier 0 — the coarse read

**Question.** The language probe refuses seventeen of twenty questions. How many of those refusals are the parser, and how many are the system having nothing to say?

**Verdict.** The seventeen refusals are three different failures: written into the system's own query grammar, six of the twenty questions are answered against two asked in English, ten more are held by a register row or a shipped function that no query kind returns, and four are held by nothing at all, where the refusal is right.

**Deciding figure.** The parser is worth <!--figure:oracle-parser-worth-->4<!--/figure--> questions of <!--figure:oracle-questions-->20<!--/figure-->; a surface onto what the registers already hold is worth <!--figure:oracle-surface-->10<!--/figure-->.

**Recomputed by.** `glm_universal.reasoning.probe_oracle.oracle_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 1. What this experiment is

[`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md) §1 names blocker 1 — *there is no
parser from open natural language to a query* — and declares the smallest
experiment that would price it:

> take the twenty probe questions and hand-write the query each one should
> become; measure how many of the twenty the existing solvers then answer.
> That separates *cannot parse* from *cannot answer* without building a
> parser.

That experiment is run here, against the system's own query grammar. Nothing was built, no solver was changed, and no
question was added or reworded: the only thing supplied is a person who knows
the query grammar. The twenty questions are
`glm_universal.reasoning.blockers.PROBE` exactly as they were pre-registered,
and each keeps the fragment a right answer has to contain.

The reason the probe's own score cannot answer this question is that a refusal
is silent about its cause. *Why is the sky blue?* and *what is the atomic
weight of carbon?* are both refused, and they are not the same failure: the
first is a question nothing here holds, and the second is a number sitting in
the element register — `atomic_weight_u = 12011/1000` — that no query kind
returns.

## 2. The three things a translation can find

Each question ends in exactly one class, and the class is computed from two
facts rather than judged:

* **`parsed`** — a query in the existing grammar answers it, with the declared
  fragment in the declared field. The whole gap between the English and the
  answer was the parser.
* **`surface`** — no query answers it, and a **witness** holds the answer: a
  shipped register row, a shipped function's return value, or the package's
  own source read with machinery the package already has. The fact is here;
  no query kind returns it.
* **`absent`** — no query answers it and no witness holds it. The refusal is
  the right behaviour, and a parser would not change it.

`GLM.ProbeOracle` proves what the arithmetic of the next section relies on:
the three classes are exhaustive and mutually exclusive, so the counts
partition the twenty questions rather than merely summing to them, and a
question with no expressible query is never counted `parsed`.

### Two rules that keep it honest

**The locus.** For every translation the field that must carry the fragment is
declared beside the query — `answer`, or a named key of the solution's
`expected` mapping. The probe's own rule scores a fragment anywhere in the
answer or in any value of that mapping, which is loose enough to pass by
accident: `approximate 12/18 to 4 places` returns `0.6667`, and the fragment
for *what is the greatest common divisor of 12 and 18?* is `6`. Under the
probe's rule that scores. Under the locus rule it does not, and it is not
offered as a translation at all.

**No smuggling.** A translation may not contain the fragment it is scored on
unless the question already contains it. Naming the subject is what a
translation is — *what does velocity mean?* becomes `meaning of velocity` —
but `relate velocity position` is **not** a translation of *what is velocity
the derivative of?*, because it supplies the word the question asks for. That
question is therefore recorded as having no expressible query, even though the
lexicon holds the triple that answers it. The rule is enforced by a test, not
by good intentions.

## 3. The split

<!-- generated: oracle-split -->
| class | questions | what it means |
|---|---|---|
| `parsed` | 6 | a query in the existing grammar answers it, with the declared fragment in the declared field |
| `surface` | 10 | no query answers it and a shipped register or function holds it: the fact is here, and no query kind returns it |
| `absent` | 4 | nothing here holds it, and the refusal is the right answer |

6 of 20 are answered by a query written in the existing grammar, against 2 asked in English, so hand-translation is worth 4 questions; 10 more are held by a register or a shipped function with no query kind that returns them, and 4 are held nowhere, where the refusal is the right answer.

The questions the translation moves are `math-ratio`, `nl-meaning`, `phys-derive`, `phys-dimension`.  What holds the `surface` class: 4 `module`, 5 `register`, 1 `source`.

the split is the result, not the score: the parser is worth 4 questions and a surface onto what the registers already hold is worth 10, so the cheaper instrument is the one this repository does not have.  A question is only counted answered when the declared fragment appears in the declared field of the solution, which is stricter than the probe's own scoring rule.
<!-- end generated -->

## 4. Question by question

<!-- generated: oracle-table -->
| domain | question | the query it should become | class | kind returned | what holds the answer |
|---|---|---|---|---|---|
| natural language | *what does velocity mean?* | `meaning of velocity` | `parsed` | `meaning` | -- |
| natural language | *what is velocity the derivative of?* | *not expressible* | `surface` | `not-expressible` | `velocity-derivative-of` (register) |
| natural language | *is energy more abstract than water?* | *not expressible* | `surface` | `not-expressible` | `abstractness-energy-water` (register) |
| natural language | *why is the sky blue?* | *not expressible* | `absent` | `not-expressible` | -- |
| mathematics | *what is 2 + 2?* | `approximate 2+2 to 2 places` | `parsed` | `real` | -- |
| mathematics | *is 91 prime?* | *not expressible* | `absent` | `not-expressible` | -- |
| mathematics | *what is the greatest common divisor of 12 and 18?* | *not expressible* | `absent` | `not-expressible` | -- |
| mathematics | *what is the prime limit of the interval 3/2?* | `derive prime_limit of perfect_fifth in harmonics` | `parsed` | `derive` | -- |
| physics | *describe speed_of_light* | `describe speed_of_light` | `parsed` | `describe` | -- |
| physics | *what are the dimensions of force?* | `meaning of force` | `parsed` | `meaning` | -- |
| physics | *is force equal to mass times acceleration dimensionally?* | `force = mass * acceleration` | `parsed` | `verify` | -- |
| physics | *convert 3 metres to feet* | *not expressible* | `absent` | `not-expressible` | -- |
| chemistry | *describe C* | *not expressible* | `surface` | `not-expressible` | `carbon-name` (register) |
| chemistry | *what is the atomic weight of carbon?* | *not expressible* | `surface` | `not-expressible` | `carbon-atomic-weight` (register) |
| chemistry | *which block of the periodic table is chlorine in?* | *not expressible* | `surface` | `not-expressible` | `chlorine-block` (register) |
| chemistry | *what is the molar mass of water?* | *not expressible* | `surface` | `not-expressible` | `water-molar-mass` (module) |
| program text | *which file is GLM.NormFamily.family_tower in?* | *not expressible* | `surface` | `not-expressible` | `family-tower-file` (module) |
| program text | *which module defines the function rung_audit?* | *not expressible* | `surface` | `not-expressible` | `rung-audit-module` (source) |
| program text | *what does glm_universal.substrate.norm_family.completeness return?* | *not expressible* | `surface` | `not-expressible` | `completeness-returns` (module) |
| program text | *how many rungs does the norm family have?* | *not expressible* | `surface` | `not-expressible` | `norm-family-rungs` (module) |
<!-- end generated -->

## 5. What each class turned out to contain

Three classes, three different failures, and the six questions the system's own grammar answers are not the six a reader of the probe would have guessed.

**The four the parser is worth.** `nl-meaning`, `phys-dimension`,
`math-ratio` and `phys-derive` are refused in English and answered by a query
that already exists: the `meaning` kind returns the dimensional formula of
*force*, the `derive` kind answers the prime limit off the harmonics
description with the rule that computed it beside the value, and the `verify`
kind audits *force = mass × acceleration* across planes. Two of the four are
one word away from the English. That is a coverage failure of the front end
and nothing else, and it is what a parser would buy.

**The ten that are held and unreachable.** They fall into three kinds of
holding:

* **five in a register row.** The element register holds `name = 'Carbon'`
  beside the symbol `C`, `atomic_weight_u = 12011/1000` in the same row, and
  `group_block = 'Halogen'` for chlorine; the lexicon holds the triple
  `('velocity', 'derivative_of', 'position')` as an attribute of its entry,
  and carries `abstract_concrete` as coordinate 0 of every carrier — 1/4 for
  *energy* against 1 for *water*, where 0 is abstract, so the comparison the
  question asks for is a subtraction over data already in the register.
  `describe C` returns the carrier's depth, mask and Griess norm and never the
  row's own fields, which is exactly the wrong answer the probe scored as
  *wrong* rather than *refused*.
* **four in a function.** The molar mass of water is one exact sum over the
  formula the molecule register holds and the atomic weights the element
  register holds; the Lean address book holds the file of every declaration
  and is asked only in aggregate by `report lean`; `norm_family.completeness`
  returns a mapping with a `complete` key; `family_rungs()` has 25 entries.
* **one in the source.** The module that defines `rung_audit` is found by the
  same AST walk `blockers.python_features` already performs — the package's
  own Python is text it ships and holds in no structure, which is blocker 5.

**The four that are absent.** *Why is the sky blue?* is the declared control:
nothing here holds it and the refusal is the right outcome. *Is 91 prime?* and
*what is the gcd of 12 and 18?* are arithmetic the system has no operation
for — blocker 3, composition, not blocker 1 — and a unit conversion needs a
metre-to-foot factor no register holds, though the lexicon holds `foot` as a
word.

## 6. What it decides

The refusal count was reading as one failure and is three, in a ratio that
inverts the obvious conclusion. A parser is the expensive instrument and it is
worth <!--figure:oracle-parser-worth-->4<!--/figure--> of twenty. A *field
surface* — one query kind that returns a named field of a named register row,
and its obvious extension to a named function's named key — is the cheap one,
and it is worth <!--figure:oracle-surface-->10<!--/figure-->.

That is a recommendation about coverage, and it must not be read as a
recommendation about reasoning. Under the standing target of
[`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md) a field surface is
`table`, the weakest of the three faculties: it would answer ten more probe
questions and derive nothing. The honest summary is that this experiment
prices two instruments and recommends neither by itself — it says that if the
next round wants *coverage* it should buy the surface, and that if it wants
*reasoning* it should look at the four absent questions, where two are
arithmetic no operation of this system performs.

What it has already removed is a misreading: the seventeen refusals were not
seventeen things the system cannot do.

## 7. Limits

* Twenty questions is a small sample, and it was pre-registered for a
  different purpose. The split is exact for these twenty and is not a rate.
* A translation is a judgement about what the grammar can express, made by
  reading the grammar. Two rules constrain it — the locus and the no-smuggling
  rule, both tested — but a better translator might find a query for a
  question recorded here as not expressible. Each such row says in its note
  what was tried and why it was refused.
* A witness shows that the answer is *reachable*, not that a query kind could
  be written cheaply: the surface class is a lower bound on what is held, not
  an estimate of the work.

## 8. Re-running it

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools oracle          # the split, in one screen
PYTHONPATH=. python3 -m glm_universal.tools oracle --json   # the same as data
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_probe_oracle.py -q
```

The experiment keeps **no measurement cache**: it asks a live session twenty
times and finishes in seconds, so the generated blocks above always quote what
the solvers do now. That is the whole reason it is cheap enough to re-run on
every documents gate.
