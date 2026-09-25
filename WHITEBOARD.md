# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is in flight: Phase 63 closed, and the next round starts
from a candidate in `STATUS.md` §3.4.

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

**No round is in flight.** Phase 63 — round two of the substrate-native
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
[`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 63.*

## 2. In flight right now

*Nothing.*

## 3. What remains, in order, with the command for each

*Nothing outstanding: 0 steps. Pick a candidate from
[`STATUS.md`](STATUS.md) §3.4 and start here.*

## 4. Known state of the gates

| gate | state |
|---|---|
| `corpus --check --all` | current at the close of Phase 63 |
| `signoff --verify-release` | released at the close of Phase 63: 109 of 109 test files and 7 of 7 instruments signed with the exhaustive cases run |
| evaluation | 177 / 177 |
| `lake build` | clean over the 133 files of `RequestProject/GLM/`, no `sorry` |

## 5. The wiring audit

*Taken in Phase 56 and written into [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase
56; its figure-registry half was closed by Phase 57 and now reads 135
registered, 135 quoted, 0 never quoted, while its eight unreached reasoning
modules stand as candidate 3 of [`STATUS.md`](STATUS.md) §3.4. Re-run it with
`python3 studies/scripts/wiring_audit.py`.*

## 6. Things learned worth not re-learning

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
* **A string in the package that looks like a Lean name is audited as a
  citation.** A literal split across lines reads as a truncated name; keep a
  cited name on one line, and split a deliberately fake one after `GLM.`.
* **Two registered measurements of the same thing can disagree unnoticed if
  neither is quoted.** `corpus-documents` counted the generated documents and
  the corpus inventory did not, three apart, for as long as no document read
  either.
