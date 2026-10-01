# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is in flight: Phase 87 closed, and the next round starts
from round 2 of the order of work at the head of `STATUS.md` §3.4.

**Deciding figure.** 0 steps outstanding.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict
and the figure above are grounded in the body below, and
`glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## How to use this file

**Write it while the round runs, not after it.** If a session ends here, this
is what the next one reads first: what is done, what is half-done, and the
exact command that resumes it. A step finished is a line changed here, before
the next step starts — not a note to write up later.

When the round closes, its content moves into [`STATUS.md`](STATUS.md) (the
present tense) and [`MASTER_PLAN.md`](MASTER_PLAN.md) (the past tense), and
this file goes back to the shape below. That is the same rule the rest of the
repository keeps: the state document holds what *is*, the plan holds what
*happened*, and this holds only what is *in flight*.

Two habits earn their keep, and both were learned by losing work to their
absence:

* **Record the command, not the intention.** "Re-take the escalation cache" is
  not resumable; `python3 -m glm_universal.tools queryesc --write` is.
* **Record what a step will invalidate.** A release signs the tree it ran on;
  editing a document afterwards makes the units that read it stale again, so
  the order is documents first, refresh, then release.

## Status

**No round is in flight.** Phase 87 — the open candidates merged into
seven tracks and ordered ([`studies/ROADMAP_STUDY.md`](studies/ROADMAP_STUDY.md)),
then round 1 of that order, the measurand register: register values read
through what they measure, conversions through a stated efficiency in (0, 1]
(`EFFICIENCY_OUT_OF_RANGE`, `EFFICIENCY_UNDECLARED`), and the elementary charge
as an exact unit — is closed: the study is
[`studies/MEASURAND_REGISTER_STUDY.md`](studies/MEASURAND_REGISTER_STUDY.md),
the record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 87, and the next round
is round 2 of the order (the loop through the planner).
Phase 86 — measurands: kinds of quantity
checked beside dimensions (`KIND_MISMATCH`), Celsius and Fahrenheit
temperatures read as a level or a difference with the conflations refused by
name, and the SI's defining constants `h` and `c` supplied when the givens
alone derive nothing; five earlier verdicts amended; begun with a quick
measurement of the soft floor's named repairs (candidate P) — is closed: the
study is [`studies/MEASURANDS_STUDY.md`](studies/MEASURANDS_STUDY.md) (and
§4 of [`studies/RATE_POSTERIOR_STUDY.md`](studies/RATE_POSTERIOR_STUDY.md)),
the record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 86, and what it left is
the study's §6, named under candidate O5 of [`STATUS.md`](STATUS.md) §3.4.
Phase 85 — folds with a hole: the median, the
largest and the smallest value and the rank of a row over a declared set, a
median or a rank over a column with holes answered as the exact interval over
every completion (one value when it closes, `COLUMN_HOLE` when a side is
open), and the present-rows question asked as its own with the missing rows
named, with `NOT_A_MEMBER` and `COLUMN_EMPTY` — is closed: the study is
[`studies/HOLE_FOLDS_STUDY.md`](studies/HOLE_FOLDS_STUDY.md), the record is
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 85, and what it left is the study's
§6, named under candidates 2 and O of [`STATUS.md`](STATUS.md) §3.4.
Phase 84 — the stepwise planner, round three:
comparatives through a declared register field, *how many more* electrons and
valence electrons, tera and pico, and sums, means and parity counts over every
element or a declared class, with `COMPARATIVE_UNDECLARED`, `VALUE_MISSING`,
`COLUMN_HOLE` and `SET_UNDECLARED` — is closed: the study is
[`studies/STEPWISE_THREE_STUDY.md`](studies/STEPWISE_THREE_STUDY.md), the
record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 84, and what it left is
candidate O of [`STATUS.md`](STATUS.md) §3.4, narrowed. It began by signing
Phases 81–83's release, which had been written up but not closed.
Phases 81–83 — the second reading's exact
channel measure and its place in the hunt, the rate estimated from the
machine's own reads, and the 106 unresolved knowledge-base laws triaged under
a service rule — are closed: the studies are
[`studies/AGREE_CHANNEL_STUDY.md`](studies/AGREE_CHANNEL_STUDY.md),
[`studies/RATE_POSTERIOR_STUDY.md`](studies/RATE_POSTERIOR_STUDY.md) and
[`studies/LAW_TRIAGE_STUDY.md`](studies/LAW_TRIAGE_STUDY.md), the record is
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phases 81–83, and candidate P of
[`STATUS.md`](STATUS.md) §3.4 is closed with what it leaves named there.
Phase 80 — the confidence floor, hunted: a
declared grid of thresholds measured at five rates over an exact channel
census against a declared meaning of *working*, the working threshold named
per rate, and a graded answer (the value with its confidence) where no
threshold works — is closed: the study is
[`studies/CONFIDENCE_FLOOR_STUDY.md`](studies/CONFIDENCE_FLOOR_STUDY.md), the
record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 80, and what it left is
candidate P of [`STATUS.md`](STATUS.md) §3.4, narrowed. It also removed a
`copy` import Phase 79 had put into `integer_decision.py`, which the
standard-library rule of `test_reasoning.py` refuses.
Phase 79 — the integer decision, completed: the
Omega test behind round three's `INTEGER_UNDECIDED`, every refutation a tree
of combinations, fresh-variable substitutions and splits that the column-3
script checks — is closed: the study is
[`studies/INTEGER_DECISION_STUDY.md`](studies/INTEGER_DECISION_STUDY.md), the
record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 79, and what it left is
candidate M of [`STATUS.md`](STATUS.md) §3.4, narrowed. It began by
completing Phase 78's release, which had been written up but not signed.
Phase 78 — the cost of an iteration: one Lean copy
(`overlay/glm_lean`, built in place), closures that follow what a unit reads
with generated figure regions masked, derivations keyed on code, and
`signoff --close` as the one closing command — is closed: the study is
[`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5g and
the record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 78. It began by closing
Phase 77, whose release had not been completed. Phase 77 — decoder confidence: the confidence law
Phase 75 absorbed attached to the decoder's own readings (the complete decoder,
the carried fork's context stage, the second reading), at a declared bit-flip
rate, with two dialect builtins — is closed: the study is
[`studies/DECODER_CONFIDENCE_STUDY.md`](studies/DECODER_CONFIDENCE_STUDY.md),
the record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 77, and what it left is
candidate P of [`STATUS.md`](STATUS.md) §3.4, narrowed. It began by closing
Phase 76, whose release had never been completed. Phase 76 — held precision: a register value's
stated precision carried through a goal or narrative derivation as the exact
interval of its answer — is closed: the study is
[`studies/HELD_PRECISION_STUDY.md`](studies/HELD_PRECISION_STUDY.md), the
record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 76, and what it left is
candidate O of [`STATUS.md`](STATUS.md) §3.4, narrowed. Phase 75 — the laws
absorbed: each of the 65 retained laws tested, improved where it could be,
and the eleven of use absorbed as computed substrate facts the typed planner
answers from — is closed: the study is
[`studies/LAW_ABSORPTION_STUDY.md`](studies/LAW_ABSORPTION_STUDY.md), the
record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 75, and what it left is
candidate P of [`STATUS.md`](STATUS.md) §3.4, reworded. Phase 74 — the law register: the owner's two
supplied files (`source_material/UBP_LAW_GLM_REVIEW.md`,
`source_material/retained_laws_verified_65.csv`) re-read row by row, the exact
rows re-graded, the decoder's outcomes and the refusal priced, the numeric
rows run through a look-elsewhere test — is closed: the study is
[`studies/LAW_REGISTER_STUDY.md`](studies/LAW_REGISTER_STUDY.md), the record is
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 74, and what it left is candidate P
of [`STATUS.md`](STATUS.md) §3.4. Phase 73 — stepwise planner round two: the
frames *how many more*, parity and averages, givens and targets written with
units (a declared unit table, dimension checks, SI scaling and refusals), and
register values feeding a wheel derivation, every step still in three columns
with one fresh-interpreter script — is closed: the study is
[`studies/STEPWISE_TWO_STUDY.md`](studies/STEPWISE_TWO_STUDY.md), the record
is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 73, and what it left is candidate
O of [`STATUS.md`](STATUS.md) §3.4, narrowed. Phase 72 — the stepwise planner: the typed
planner as the executive of a chain of steps (composition of its own answers,
unasked steps found over the wheels and stitched, every step in three columns
with a per-step alignment check and one fresh-interpreter script) — is closed:
the study is
[`studies/STEPWISE_PLANNER_STUDY.md`](studies/STEPWISE_PLANNER_STUDY.md), the
record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 72, and what it left is
candidate O of [`STATUS.md`](STATUS.md) §3.4. Phase 71 — native words: the word-overlap ranking
computed on Golay words of the tokens (Golay names that carry the token
overlap exactly, then the parts' letter words and their Golay classes inside
the ties), shipped as the live document ranking — is closed: the study is
[`studies/NATIVE_WORDS_STUDY.md`](studies/NATIVE_WORDS_STUDY.md), the record
is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 71, and what it left is candidate
N of [`STATUS.md`](STATUS.md) §3.4, narrowed. Phase 70 — native parity: every place a standard
method tied or narrowly beat a Golay/Leech-native one re-measured, and the
native method kept and refined (two native Leech books read in two layers for
retrieval, the read-back scorer for the controller) — is closed: the study is
[`studies/NATIVE_PARITY_STUDY.md`](studies/NATIVE_PARITY_STUDY.md), the record
is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 70, and what it left is candidate
N of [`STATUS.md`](STATUS.md) §3.4. Phase 69 — reverse Three Column Thinking, round
three: an integer sort, asked for by `entails over the integers:` and `bounds
over the integers of x:`, with floor quotient and remainder split into residue
cases and each case decided by elimination tightened over ℤ, the refutation
certified by its derivation — is closed: the study is
[`studies/REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md) §10–§12, the
record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 69, and what it left is
candidate M of [`STATUS.md`](STATUS.md) §3.4, narrowed. Phase 68 — reverse Three Column Thinking, round
two: the grammar widened to the integer layer, the bitwise operators and Golay
masks, disjunction so that negation is closed under De Morgan, and `relay:`
handing the mathematics to the planner as questions and reading the answers
back — is closed: the study is
[`studies/REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md) §7–§9, the
record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 68, and what it left was
candidate M, partly taken by Phase 69. Phase 67 — reverse Three Column Thinking: the
mathematics and the script generate the language column through a declared,
uniquely readable grammar, and seven semantic operations (`say`,
`equivalent`, `paraphrase`, `negate`, `solve`, `entails`, `bounds`) are taken
on the mathematics and realised back into checked sentences — is closed: the
study is [`studies/REVERSE_TCT_STUDY.md`](studies/REVERSE_TCT_STUDY.md), the
record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 67, and what it left was
candidate L, taken by Phase 68. Phase 66 — the connected machine: one question
path (`GLM.py --ask`) to every surface, the eight unreached modules as tools,
and derivation across a declared union of formula wheels — is closed: the
study is [`studies/CONNECTED_MACHINE_STUDY.md`](studies/CONNECTED_MACHINE_STUDY.md),
the record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 66, and what it left is
candidate K of [`STATUS.md`](STATUS.md) §3.4. Phase 65 — the six deep-hole Golay candidates
carried as a fork until a later decision resolves them, and the tie escalated
to the Leech lattice — is closed: the study is
[`studies/CARRIED_FORK_STUDY.md`](studies/CARRIED_FORK_STUDY.md), the record
is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 65, and what it left is candidate J
of [`STATUS.md`](STATUS.md) §3.4. Phase 64 — the GLM speaking Python, evaluated
exactly on the substrate with Three Column payloads and named refusals — is
closed: the study is
[`studies/PYTHON_SPEECH_STUDY.md`](studies/PYTHON_SPEECH_STUDY.md), the record
is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 64, and what it left is candidate I
of [`STATUS.md`](STATUS.md) §3.4. Phase 63 — round two of the substrate-native
cognition study, which refined three near misses into planner frames and made
the planner the default path — is closed: the study is
[`studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md`](studies/SUBSTRATE_NATIVE_COGNITION_STUDY.md)
(§6–§8), the record is [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 63, and what it
left is candidate H of [`STATUS.md`](STATUS.md) §3.4. Phase 62 ran the
supplied list as nine declared experiments (study §1–§5). Before it, Phase 61 — a second
documentation round taken at the owner's request — closed:
[`studies/GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md) and
[`studies/GLM_Complete_Number_Theory_Evidence.md`](studies/GLM_Complete_Number_Theory_Evidence.md)
are current with the whole system, and the small archive Lean the Phase 60
ledger named is rebuilt (`Distinction.lean`, `SeedRoles.lean`,
`GolayMOG.lean`). The round is recorded in [`MASTER_PLAN.md`](MASTER_PLAN.md)
Phase 61, with the remaining candidates in [`STATUS.md`](STATUS.md) §3.4
(candidate G is now the MOG cube's language half and the rest of
`ObserverY.lean`). The next round starts from a candidate there, or says in its
record why not.

## 1. Done, committed, and checked here

*Nothing in flight. The last round's record is in
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 85.*

## 2. In flight right now

*Nothing.*

## 3. What remains, in order, with the command for each

*Nothing outstanding: 0 steps. Pick a candidate from
[`STATUS.md`](STATUS.md) §3.4 and start here.*

## 4. Known state of the gates

| gate | state |
|---|---|
| `corpus --check --all` | current at the close of Phase 85 |
| `signoff --verify-release` | released at the close of Phase 85 (`signoff --close`): every test file and all 6 instruments signed with the exhaustive cases run |
| evaluation | 177 / 177 |
| `lake build` | clean over the 156 files of `overlay/glm_lean/RequestProject/GLM/` (the only copy), no `sorry` |

## 5. The wiring audit

*Taken in Phase 56 and written into [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase
56; its figure-registry half was closed by Phase 57, and its eight unreached
reasoning modules by Phase 66, which made each a tool: the audit now reads 96
of 96 reasoning modules reached. Re-run it with
`python3 studies/scripts/wiring_audit.py`.*

## 6. Things learned worth not re-learning

* **A frame reads the text after the planner has normalised it.** Phase 85's
  *the noble gases that have one* reached the frame as *… that have 1*: the
  planner writes number words as numerals before any reader sees them. Test a
  new phrase through `sw.split_then` first, not as typed.
* **A fallback that refuses can still do harm.** Phase 84's first
  `COMPARATIVE_UNDECLARED` turned no refusal into an answer, yet it replaced
  the vagueness reader's specific refusal (*different quantities are not
  comparable*) with a generic one on three declared questions. The router
  census (how many declared questions the stepwise layer *reads*) caught it
  when the verdict counts did not: a new refusal belongs only where the claim
  it makes is this layer's to make.
* **pytest is not always installed.** A fresh environment lacked it, and
  `signoff --close` recorded every unit it ran as *failed* in 0.1 s; install
  it (`pip install pytest`) before closing, and read a wall of 0-test
  failures as an environment fault, not a regression.

* **A declared outcome must be computed for the reading it names.** Phase 80
  declared a two-case `resolve_floor` at 1/10 to refuse, reasoning from the
  decoder's 78 % at weight 3; with two cases the rival lies further away and
  the read is 6561/6562 sure. Work the declared value out for the program as
  written before committing it.
* **A release written up is not a release signed.** Phase 78's documents said
  the round had closed; `signoff --verify` said 22 of 123. Believe the ledger,
  and run `signoff --close` before writing the word *closed*.
* **A headline check wants its phrase inside one span.** `test_figures.py`
  looks for the literal phrase `N test files`; a sentence that splits the
  number from its noun with a figure marker passes the figure registry and
  fails the headline check. Quote the `test-files` figure, whose value carries
  the noun.

* **An import can leak the development as surely as a glob.** Phase 75 put
  `law_absorption.py` on the planner's path; three imports down, `salvage.py`
  named archive Lean files the development does not hold, and an unresolved
  Lean name is hashed as the whole development. Every session unit carried all
  of it until Phase 77 rewrote the labels. After adding an import to the
  answering path, run `test_corpus.py -k IterationCost`.
* **A declared posterior must say what it is conditioned on.** Phase 77
  declared the second reading's witness at exactly 1/2 each; over all 4096
  codewords each survivor is just below 1/2. Conditioned on the fork, 1/2.
* **A supplied "round-trip check" may never read what it generated.** The
  generator's own check re-quantises the *carrier* and compares it with
  itself; the comment above it says it cannot parse the generated source. A
  check that passes for a generator emitting the empty string is not a check.
* **Storing only successes forgets the expensive case.** The supplied
  procedure store keeps successful plans, and the follow-up that costs
  fourteen licensing trials is the one that refuses — so the store saves
  nothing on the only case worth saving.
* **A cache key has to cover the conversation, not the sentence.** Six of the
  fifteen declared follow-ups are the words *describe it* and they have four
  different antecedents; keyed by those words, eight of the fifteen come back
  with another conversation's answer.
* **Two supplied bindings, one theorem and one refutation.** Exclusive-or over
  parity readings is a group operation and inverts unconditionally;
  elementwise product inverts only where nothing reads zero, and 1,133 of
  1,143 carriers read zero somewhere.
* **English can parse as Python.** *what is 2 + 2* is a comparison of a name
  `what` with `2 + 2`; a reader that asks only for a parse would take two
  contract questions from the planner. Ask for bound names as well.
* **A union of true axioms can derive a false law.** Naive composition of
  the ten formula wheels gives `energy = 2 * mass * speed_of_light^2`; the
  algebra is exact and the identification of a shared name is what is wrong.
* **A round that ends without its release hands the next session a puzzle,
  not a state.** Run `signoff --verify` first, and believe it over the prose.
* **A drift guard can collide with the truth.** `test_figures.py` forbids
  counts that were retired in an earlier round; a guard has to name the unit
  it counts rather than the bare number.
* **A new module moves four measurements, not one.** The module count and the
  version, the blast-radius table in `ITERATION_COST_STUDY.md`, the corpus
  digest, and — through its new test file — every sentence that quotes the
  suite.
* **The suite sentence converges in two releases, not one.** Run the release,
  `figures --write`, refresh, then release again.
* **Supplied material is tested before it is believed, and the test is cheap.**
* **A tier-0 verdict may use only the body's own words, and the check names
  the offenders.**
* **A new Lean file is a change to two measurements.** The relay and the
  anonymous register read the Lean corpus, so adding one file moves both.
* **A cited Lean name must be written as one token**, and a name ending in `?`
  is not the name the citation check resolves: cite the theorem, not the
  definition.
* **A closure is computed from string constants.** Say "the whole Lean tree"
  in prose rather than writing a Lean-file glob pattern in a docstring.
* Editing `evaluation/cases.py` invalidates the query-escalation cache
  (`tools queryesc --write`) as well as the planner's stored report.
* Two generated blocks read the corpus digest they are written into, so
  `corpus --write` can need a second pass before `corpus --check` is current.
* `pytest` and `pytest-subtests` are the suite's only external dependencies; a
  fresh sandbox may need `pip install pytest pytest-subtests`.
* **Ship the code, then run the whole suite before the documents.** Phase 56
  shipped two modules and stopped; the suite it never ran found a directive
  violation (`hashlib` in the core) and an unclassified exclusive-or site. Both
  were one-line fixes and neither would have survived a single full run.
* **Two new Lean files move three measurements outside the Lean gate.** The
  anonymous register, the stack relay and the blast-radius table all read the
  development, so the evaluation cases that quote them go stale with it.
* **A prose edit made after the refresh costs a second refresh.** Editing a
  study after `corpus --refresh` leaves the document address book stale
  against the corpus digest, and `test_corpus.py` fails on it rather than the
  document check — the order really is documents, refresh, release.
* **A figure marker inside a tier-0 verdict is not a word anyone wrote.** The
  verdict rule compared raw text against a body whose markers are blanked, so
  quoting a generated figure in a verdict failed the tier contract; the check
  now strips the marker and its value from the verdict first, for the same
  reason the deciding figure's emitted numbers were already exempt.
* **A new Lean file moves hand-typed counts in three documents.** The
  number-theory paper states the `RequestProject/GLM/` file count in three
  forms, and `README.md` and `STATUS.md` quote it too; `figures --write` fixes
  only `FIGURES.md`.
* **A new Lean file also moves the declaration count and the anonymous
  register.** The count is hand-typed in `STATUS.md`, `overlay/README.md` and
  `overlay/glm_universal/README.md`; the anonymous register's query set is a
  stride over the corpus, so its figures move in the study's own prose and in
  the `report-anonymous` case of `evaluation/cases.py` — which in turn needs
  `tools queryesc --write` (over ten minutes; run it in the background).
* **Never edit a document while `corpus --refresh` or `--write` runs.** The
  refresh reads every document when it starts and writes each one back with
  its blocks regenerated, so a hand edit made in between is silently
  overwritten. Phase 66 lost its `MASTER_PLAN.md`, `STATUS.md` and paper
  edits that way and restored them from the commit. Edit, commit, then
  refresh.
* **A relay figure quoted as unchanged must be re-taken after the refresh.**
  The measurement caches are rebuilt by `corpus --refresh`; before it, the
  relay and anonymous register still read the old corpus.
* **A new pass-mark study needs its tier-0 words in its body.** The verdict
  check compares words, not meaning: write the verdict last, from the body's
  own phrases, and quote every deciding figure in the body too.
* **A string in the package that looks like a Lean name is audited as a
  citation.** A literal split across lines reads as a truncated name; keep a
  cited name on one line, and split a deliberately fake one after `GLM.`.
* **Two registered measurements of the same thing can disagree unnoticed if
  neither is quoted.** `corpus-documents` counted the generated documents and
  the corpus inventory did not, three apart, for as long as no document read
  either.
