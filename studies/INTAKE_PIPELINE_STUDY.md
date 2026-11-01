# The intake pipeline — supplied material, filed and gated

## Tier 0 — the coarse read

**Question.** Can everything the owner supplies in `source_material/` be filed as open (`ToDo/`) or finished (`done/`) from the records, with one ledger record per item, and moved towards absorption only when each stage's evidence exists — a study whose manifest is in step with it, tests that pass against the code as it now stands, Lean files in the audited build, the owner's passing build record for those files and everything they import, a finished measurement accepted against the study's own declared criterion, tested modules — so that a check fails whenever a record claims more than the tree holds?

**Verdict.** Yes. All 42 supplied items and 2 local-only files have one record each: 10 are open in `ToDo/` and 34 are finished in `done/`, 21 absorbed and 13 closed with a reason and evidence; the check passes with 0 errors, and each gate refuses a scratch record that lacks its evidence, including a promotion to Lean verified without a matching build record, a draft or unaccepted measurement, a stale test pass and a study without its manifest in step. No item reaches Lean verified in this checkout, because the owner's build has not yet written that record; the two wheel items wait at Lean written with their acceptance decisions recorded against their studies' declared criteria, and by the owner's decision their 6 parts are installed in the package provisionally (16 files, listed in the register of provisional wheels, every answer from them marked), not absorbed; the 21 earlier absorptions are marked as predating acceptance decisions. Of 24 in-place runs of the supplied items' scripts at filing, 18 pass and 6 fail; the failures are five missing or changed dependencies and one tautology the item's own suite flags, not wrong answers.

**Deciding figure.** 44 records over 42 filed items and 2 local-only files; 10 open (4 triaged, 2 study drafted, 1 tested, 3 Lean written) and 34 finished (21 absorbed, 13 closed); 0 check errors; 6 parts installed provisionally in 16 files, 0 absorbed without a build record; 2 acceptance decisions recorded and 21 absorptions predating them; 0 items Lean verified (no build record yet); 24 in-place runs, 18 pass and 6 fail; 8 wheels surveyed with 25 Lean obligations.

**Recomputed by.** `glm_universal.intake.actions.intake_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026 (repository check; directive D22).  Last altered 31 October 2026: the Lean written / Lean verified split, the build-record gate, staged code, and the two wheel items held back from absorption until the owner's build; then the study gate's manifest check, fingerprinted test results, the finished-measurement and acceptance gate, `accept` and `retest`; the package's own test runner where pytest is absent, and the owner's two scripts' exit status; then the two wheel items installed provisionally by the owner's decision (§1, §2, N9 amended, §7.3); the fallback runner's teardown hooks (§7.3, N6); test-result details written in the intake's own words, never copied output (§7.3).*

## 0. What this document is

The record of the round that built the intake pipeline and filed the supplied
material through it. It is **not** a pre-registration in the strict sense: the
pipeline, its gates and the ledger were written in the same round. The order
of work is stated so the reader can weigh that.

1. *What existed before.* Forty-two items lay flat in `source_material/`
   (folders and loose files), with no record of which had been taken. The
   records that say so were read first: `MASTER_PLAN.md`, `STATUS.md` (§2.0 and
   §2.1, item 0), the studies that cite each item, the paper's appendix of
   supplied material and the code that reads an item.
   `glm_universal.constants` already named `SOURCE_TODO_DIR`, `SOURCE_DONE_DIR`,
   `INTAKE_LEDGER` and `source_material_item(name)`.
2. *Then the gates* (`glm_universal/intake/gates.py`), with the rule that a
   stage is reached only with its evidence and that the evidence accumulates.
3. *Then the filing and the ledger.* Each item was filed from the records,
   its record written, and the check run against the tree until it passed.
   Where a record would claim *absorbed* the named tests were run that day;
   where an item is open, its scripts were run in place on scratch copies.

## 1. What the owner asked for

The owner's words of 31 October 2026: new material goes into
`source_material/`, "then I run a study through to a lean verified stage and
if it works/tests to help the GLM it then is absorbed"; the material may be "quite
full studies like the cent_compiler one or quite rough concepts"; it "should be
organized into done/Todo folders inside the source_material folder"; new
wheels "should be in the one wheels folder when they have been properly
checked"; and "a pipeline ready for this would help". For the Python items the
earlier instruction stands: "Test and fix them where they are; leave
absorption until a later round adds Lean verification." The rule this round
gives the repository is directive D22: new material enters through
`source_material/ToDo` and is absorbed only through the intake pipeline's
gates — study, tests, Lean verification, measured help.

Absorption therefore follows a *build*, not a static reading of the Lean
files. This repository check cannot run `lake build`; the owner does, with
`scripts/rebuild_lean.sh`. The pipeline is built so that nothing reaches the
package on the strength of Lean that has not been built: code waits, staged,
inside its item. The one exception is the owner's: on 31 October 2026 the
owner decided that the code of the two wheel items this round tested and
measured (`glm_wheels_bundle` and the 15 cent wheels of `cent_compiler_v12`)
should serve now — "keep them in the wheels folder now, clearly marked
provisional until my Lean build log confirms them" — so it is installed
*provisionally*: in the package, listed in a register, its answers marked,
and confirmed only by absorption on the build record (§2, *Provisional
install*).

## 2. The objects

**The ledger**, `source_material/INTAKE.yaml` (schema `glm-intake-ledger/v1`):
one record per item, with its id, path (`ToDo/…` or `done/…`), kind (full
study, code, concept note, data, Lean, plan), what it claims or offers, its
stage, the studies, tests, test results, Lean files, measurement and modules
that are its evidence, its parts (what was taken earlier and where it went),
a wheel survey where it supplies wheels, a closing reason where it is closed,
the date of the last action and the next step.

**The line.** received → triaged → study drafted → tested → Lean written →
Lean verified → measured → absorbed, or closed with a reason. A record's stage
is the stage of the item's *open* work: an item whose first parts are absorbed
but whose others are untouched stays in `ToDo/` at the stage of the rest.

**The gates** (`glm_universal.intake.gates`), each reading files only:

| stage | evidence |
|---|---|
| received | the item is where its path says (or is a local-only file) |
| triaged | a kind, what it offers, and a next step |
| study drafted | every named study is a pair: `studies/<id>.md` with a Tier-0 block, and `studies/<id>.yaml`, which validates against `glm-study-manifest/v1`, names the same id and states the same question, verdict and deciding figure |
| tested | every named test exists and its last recorded result is a pass (a package test runs under pytest, or where it is absent under the package's fallback runner, which never passes a file in which no test ran); on promotion the pass must carry the fingerprint of the code as it now stands (the package without its generated-data folders, the item's staged files in place, the item's own files) |
| Lean written | every named Lean file is in the build tree and imported by `AxiomAuditAll.lean` (and, on promotion, `python3 -m glm_universal.lean_check` passes) |
| Lean verified | on promotion: the build record `scripts/logs/lean_build_evidence.json` is a passing build (static check, `lake build` with the axiom audit, `sorry` scan), under the same toolchain and Mathlib pins, whose audit imported each named file, and each named file *and every file it imports* is byte for byte the file that was built; the record's date is then written into the item's `lean_build` |
| measured | the study named first in `measured` passes the study gate and is finished — no draft text (`TO WRITE`, the scaffold's draft verdict or figure; a marker quoted as code does not count), a deciding figure that is a measurement, manifest status `closed` — and the record's `acceptance` decides it against the study's declared criterion: `criterion` and `result` quoted from the study, `marks` that are declared and met there (required when the study declares marks; none missed), `decision: accept` |
| absorbed | no file left in `staged/`, and every named module exists and has a test; every named test has just been run again |
| closed | a reason, and evidence (a study or a repository path) that exists |

Promotion to Lean verified *or any later stage* re-reads the build record at
that moment, so an item measured or absorbed later is still checked against
the files as they then stand. Only `scripts/rebuild_lean.sh` writes the
record, and only when all three of its checks exit 0; a failing run leaves the
previous record, which then no longer matches the changed files. A ledger
check after promotion warns (it does not fail) when a verified item's Lean
file has changed since its build.

**Current results.** Every recorded test result carries the fingerprint of the
code it ran against. A promotion counts only passes with the fingerprint of
the code as it then stands: passing *tested* runs every named test, absorption
(`advance <id> absorbed`, `absorb-staged <id>`) runs them all again before
installing anything, and any other promotion runs again each test whose last
result is not a current pass. With `--no-run` nothing runs and stale passes
refuse. The ledger check notes an open item whose results are not current.

**Acceptance.** The *measured* gate needs a decision, not only a figure:
`accept <id> --criterion … --result … --mark …` writes the record's
`acceptance` block and is refused unless it would pass the gate (quotations
the study does not contain, a mark it does not meet, a draft, open or negative
study). An item whose measurement fails its criterion is closed instead. The
21 records absorbed by earlier rounds, before decisions were recorded, carry
`legacy_absorption`; the ledger check accepts it only for a finished record in
`done/` and notes it, and no promotion accepts it.

**Staged code.** Code prepared for the package before its item is absorbed
waits in the item's own folder, at `<item>/staged/<repository path>` (only
below `src/glm_universal/`). Nothing in the package imports it. A
`staged:<path>` test runs it in a scratch view of the repository — every
package `.py` file copied, everything else linked, the staged files put in
place — so the repository is never written. Absorption installs the staged
files, after every gate up to *measured* holds with a current build record,
then holds the *absorbed* gate against the installed package and undoes the
install if anything fails. A part whose code is staged has status `staged`;
installing it makes it `absorbed`. `check` fails if a staged file would
overwrite a different file in the package, and if `done/` holds an open or
staged part.

**Provisional install.** By the owner's decision only, `intake provisional
<id> --decision "..."` installs an item's staged parts into the package
ahead of its build. The parts get status `provisional`, the decision is
quoted in the ledger, and the item is listed in the register
`src/glm_universal/wheels/_data/provisional.json` (its wheels, modules, Lean
files, decision and date). The item keeps its stage: nothing is promoted.
Every answer resting on a provisional wheel carries a `provisional:` note
(`glm_universal.wheels.provisional_status`). Absorption (`advance <id>
absorbed`, `absorb-staged <id>`), on a build record verifying the item's Lean
files and a fresh pass of every named test, turns the parts `absorbed` and
removes the register entry. `check` fails when the register and the ledger
disagree, a provisional module is missing from the package or untested, a
provisional part stands below *Lean written*, or one stands in `done/`.

`check` adds the ledger-wide rules: one record per filed item, nothing loose in
`source_material/`, `done/` holds only absorbed or closed items with no open
part and `ToDo/` none, and every Lean file a record cites is audited, held in
`src/lean/awaiting_recovery/` or recorded missing in
`studies/_lean_files_needed.md`.

**The command line**, `python3 -m glm_universal.intake`: `status`, `check`,
`show <id>`, `register <path>`, `scaffold <id>` (a draft study pair in the house
shape: Tier 0, questions, marks declared before the code, Lean obligations;
it never overwrites), `advance <id> <stage>` (passing *tested* runs the named
tests and records dated results, a failed run included; passing *Lean
written* runs `python3 -m glm_universal.lean_check`; promotion to *Lean
verified* and beyond reads the owner's build record; reaching *absorbed*
installs `staged/` and files the item in `done/`), `absorb-staged <id>` (the
staged parts of an item whose other parts stay open, on the same evidence),
`provisional <id> --decision … [--wheel …]` (the owner's provisional install,
above), `retest <id> [--stale]` (run the named tests and record fingerprinted results
without moving the item), `accept <id> …` (the acceptance decision, above)
and `close <id> --reason … --evidence …`. Named item tests run on a scratch
copy of the item, so a supplied item stays byte-identical.

## 3. The marks

| Mark | What is measured | Met when |
|---|---|---|
| N1 | the filing | every item has exactly one record and nothing is loose |
| N2 | the folders | `done/` holds only absorbed or closed items, `ToDo/` only open ones |
| N3 | the evidence | `check` reports 0 errors over every record |
| N4 | the Lean citations | every cited Lean file is audited, held or recorded missing |
| N5 | the readers | every code path that opens a supplied item goes through `constants.source_material_item` |
| N6 | the refusals | each gate refuses a scratch record that lacks its evidence (tested in `tests/test_intake.py`), Lean verified included: no build record, a failed build, a changed named file and a changed imported file are each refused |
| N7 | the wheels | every supplied wheel has a test result, its overlap and the Lean obligations stated |
| N8 | the items in place | every open item's scripts are run where they stand and the results recorded |
| N9 | nothing unbuilt in the package | no item is absorbed in this round without a build record; code tested here waits in `staged/` |
| N10 | decisions, not drafts | the *measured* gate refuses a scaffolded draft, a missing, misquoted or non-`accept` acceptance and a missed mark; a promotion refuses a stale pass and absorption re-runs every test; *study drafted* refuses a missing, invalid or out-of-step manifest (each tested in `tests/test_intake.py`); the two staged wheel items carry acceptance decisions that pass the gate |

*N9 amended 31 October 2026, after the measurement, by the owner's decision:
code tested here waits in `staged/` **or, where the owner so decides, is
installed provisionally, marked as such and not absorbed**. The declared
wording is kept in the table.*

## 4. Controls

The refusals are the control: `tests/test_intake.py` builds a scratch
repository and shows that a record claiming *tested* without a study or a test
fails the check; that *advance* refuses a failing test run (and records it),
a held Lean file, a failing `lean_check`, a promotion to *Lean verified* with
no build record, with a record of a different file, or with a record that
predates a change to a file the named one imports, a missing measurement and
an absent module; that a failed build writes no record; that a staged file
that would overwrite a different package file is an error and is not
installed; that absorption without a build record installs nothing, and a
failing *absorbed* gate after the install removes it again; that
`absorb-staged` takes the staged parts and leaves the open ones; that a
`staged:` test runs against the staged code in a scratch view; that *close*
refuses an empty reason, missing or non-existent evidence and an open part;
that an item script that writes a file leaves the item unchanged; that
*study drafted* refuses a missing manifest, one that does not parse or
validate, names another id or states another verdict, and a study without a
Tier-0 block; that *measured* refuses the scaffold's draft study, a missing
acceptance, a decision other than `accept`, a criterion the study does not
state, a placeholder result, another study, a missing or missed mark, and an
open or negative study, and that `accept` writes nothing it would refuse; that
a pass taken before a change to the package or to the staged code is stale,
that a promotion with `--no-run` refuses it, that absorption and
`absorb-staged` run every test again and install nothing when the run fails,
and that a later promotion re-runs exactly the tests without a current pass;
that `legacy_absorption` stands in for no decision outside a finished
record in `done/`; that without pytest a failing plain test function fails,
and an empty, all-skipped or fixture-needing file never passes, so a
promotion on it is refused; and that the owner's two scripts, run on a
scratch tree with stand-in commands, exit 1 when a required step fails.

## 5. What this round does not do

* It runs no `lake build`. Lean files for the wheel obligations were written
  (`Wheels/IntegerWheel.lean`, `Wheels/SporadicOrders.lean`,
  `Wheels/CentWheels.lean`) and pass the static check, but no item is promoted
  to *Lean verified* until the owner's build record matches them.
* So it absorbs no wheel: the Integer and Monster Wheels and the 15 cent
  wheels are tested and measured (`INTEGER_WHEEL_STUDY`, `CENT_WHEELS_STUDY`)
  and, by the owner's decision, installed provisionally in
  `src/glm_universal/wheels/`: the live GLM answers from them, and says each
  time that the answer rests on a provisional wheel.
* It does not move `GLM-main.zip` or the supplied PDFs, which are not in this
  checkout; their records name where they go.

## 6. Files

* `src/glm_universal/intake/` — `ledger.py`, `gates.py`, `actions.py`,
  `staged_reports.py`, `fallback_tests.py`, `__main__.py`, `__init__.py`.
* `src/glm_universal/wheels/_data/provisional.json` (the register of
  provisional wheels) and `wheels/__init__.py` (`provisional_items`,
  `provisional_status`).
* `src/glm_universal/lean_check.py` (`write_build_evidence`,
  `verification_problems`, `import_closure`) and `scripts/rebuild_lean.sh`
  step 7, which writes `scripts/logs/lean_build_evidence.json`.
* `src/glm_universal/tests/test_intake.py`.
* `source_material/INTAKE.yaml`, `source_material/README.md`,
  `source_material/ToDo/README.md`, `source_material/done/README.md`.

## 7. The measurement

### 7.1 The verdict

Yes. All 42 supplied items and 2 local-only files have one record each: 10 are open in `ToDo/` and 34 are finished in `done/`, 21 absorbed and 13 closed with a reason and evidence; the check passes with 0 errors, and each gate refuses a scratch record that lacks its evidence, including a promotion to Lean verified without a matching build record, a draft or unaccepted measurement, a stale test pass and a study without its manifest in step. No item reaches Lean verified in this checkout, because the owner's build has not yet written that record; the two wheel items wait at Lean written with their acceptance decisions recorded against their studies' declared criteria, and by the owner's decision their 6 parts are installed in the package provisionally (16 files, listed in the register of provisional wheels, every answer from them marked), not absorbed; the 21 earlier absorptions are marked as predating acceptance decisions. Of 24 in-place runs of the supplied items' scripts at filing, 18 pass and 6 fail; the failures are five missing or changed dependencies and one tautology the item's own suite flags, not wrong answers.

### 7.2 The marks

| Mark | Result | Met |
|---|---|---|
| N1 | 44 records over 42 filed items and 2 local-only files; 0 loose | yes |
| N2 | 34 finished in `done/` (21 absorbed, 13 closed), 10 open in `ToDo/` (4 triaged, 2 study drafted, 1 tested, 3 Lean written) | yes |
| N3 | 0 check errors; 5 notes (one held Lean file, two local-only files, the two items installed provisionally, and the 21 absorptions predating acceptance decisions) | yes |
| N4 | every cited Lean file audited except `GolayDeepHole.lean`, held | yes |
| N5 | the readers in `migration/state.py`, `semantics/export.py`, `reasoning/vision_stack.py`, `reasoning/ops_ladder.py`, `reasoning/pipeline_kit_crosscheck.py`, `evaluation/question_set_b_cases.py`, `corpus/yaml.py`, `tools.py` and three tests go through it | yes |
| N6 | 69 of 69 intake tests pass, the build-record, staged-code, provisional-install, manifest, acceptance, current-result and fallback-runner refusals (a failing class teardown among them) among them | yes |
| N7 | 8 wheels surveyed, 25 Lean obligations | yes |
| N8 | 24 runs at filing, 18 pass and 6 fail; 2 scripts not run (they need matplotlib) | yes |
| N9 | 0 items Lean verified (no build record yet) and 0 absorbed without one; the 6 parts first staged in 17 files, 0 of them in the package; then, by the owner's decision, installed provisionally (16 files; the staging helper `provision.py` deleted), marked and not absorbed | yes, as amended (§3) |
| N10 | the refusals of §4 pass in `tests/test_intake.py`; `cent_compiler_v12` accepted against `CENT_WHEELS_STUDY`'s absorption rule with marks I1, D1, D2, E1, S1–S5, L1, M1–M3 and I4 (E2, missed, not among them), `glm_wheels_bundle` against `INTEGER_WHEEL_STUDY`'s bar S3 with marks A, S1–S4, L and T (C and R are reported, not passed) | yes |

The 21 absorbed records were absorbed by earlier rounds, before the build
record existed; each says so in its `lean_build` entry, and their Lean was
built in those rounds. The reorganised tree has not been rebuilt since, so
the first passing `scripts/rebuild_lean.sh` is also their re-check:
`intake check` then warns wherever one of their Lean files no longer matches
the record.

### 7.3 What was seen

**The filing.** Moving the items kept all 799 of their files byte-identical
(compared by digest before and after). The *absorbed* records rest on 17
package test files, every one run the same day and passing. Open, in `ToDo/`:
`Rule30_GLM_Study` (Lean written: its Lean is in the build tree and audited
and its hypothesis-engine test passes 16 of 16; Lean verified waits for the
build record, and the engine itself has no package module yet),
`glm_wheels_bundle` and `cent_compiler_v12` (Lean written, their wheel code
staged; see below), `attention` (tested: the study's recompute function re-runs and
every agreement check holds), `conversation_experiment` and `formula_wheel`
(study drafted: parts are taken, others are open), and four items triaged.

**The items in place.** `cent_compiler_v12`: `cent test` 7 of 7; its
show-work script runs; its full test script passes 14 of 15, the miss being
the proposal its own suite labels a tautology. `glm_wheels_bundle` failed at first
because `sympy` is not installed; it was repaired in place with a small exact
fallback for `factorint`, after which the Integer Wheel tests pass 102 of 102,
the Monster Wheel tests 110 of 110 and all 26 sporadic orders verify.
`conversation_experiment`: all 8 scripts exit 0. `formula_wheel`: 02 runs; 06
and 08 import modules that were not supplied. `R_Calculus`: v2 runs and
reproduces its supplied output; v1 imports a module that was not supplied.
`Rule30_GLM_Study`: its study-YAML test imports a module that was not supplied.
`glm_vision_experiments_v14.py` fails against the current package API.

**The wheels.** The 31 wheels of `cent_compiler_v12`, read by the GLM's own
exact engine: W1–W10 agree with `engineering/wheels.py` (W4 and W6 each add one
axiom); W11–W15 have the axioms of `src/glm_universal/wheels/w11`–`w15` and
supply the cases those wheels lack; W16–W35 are new. Over all 119 cases the
engine agrees with the stated derivability on 104, disagrees on 1 and cannot
parse 18 (fractional powers). Ten axioms fail the dimension check on the
wheels' own tables — three in W13/W14 only on the angle axis, seven in the new
wheels outright — and five of the compiler's application proposals rest on
the seven. The Integer and Monster Wheels have no counterpart among the
existing wheels; their obligations instantiate the provision contract of
`HypothesisEngine/NeedsWheel.lean`. Every obligation is written into the
ledger beside its wheel.

**The two wheel items, held back.** After the survey both items were taken
further: tested, Lean written and measured (`INTEGER_WHEEL_STUDY` §7: 89 of
102 sequence questions right and 0 wrong; `CENT_WHEELS_STUDY` §8: 63 of 64
law questions licensed and 0 of 51 not-a-law questions). Their code was then
moved out of the package into the items' `staged/` folders (13 files for
`glm_wheels_bundle`, 4 for `cent_compiler_v12`), because their Lean has not
been built. The staged tests pass against the staged code (46, 24 and 36
cases). The GLM answers a sequence lookup with a staged refusal until the
wheels are absorbed. When the owner's build passes, `intake advance
glm_wheels_bundle absorbed` installs the first item, and `intake advance
cent_compiler_v12 measured` followed by `intake absorb-staged
cent_compiler_v12` installs the cent wheels while the compiler parts stay open.

**Then installed provisionally, by the owner's decision.** Asked whether the
wheels should stay staged or go into the wheels folder now, the owner
answered "keep them in the wheels folder now, clearly marked provisional
until my Lean build log confirms them". The 16 files (12 for
`glm_wheels_bundle`, the staging helper `provision.py` dropped; 4 for
`cent_compiler_v12`) went back to `src/glm_universal/wheels/` and
`src/glm_universal/tests/`; the six parts are `provisional`, the register
lists both items, and `intake check` holds the two together (0 errors). The
GLM answers sequence and sporadic-order questions from the Integer and
Monster wheels again — `python3 src/GLM.py -q "which sequence is 0, 1, 1, 2,
3, 5, 8, 13"` answers A000045 and ends with the provisional note — and the
cent wheels' derivability answers carry the same note. The tests pass in
place (`test_integer_wheel` 47, `test_monster_wheel` 24, `test_cent_wheels`
36, `test_wheels` 34, `test_lookup_kinds` 18). Absorption after the owner's
build turns the parts `absorbed` and drops the register entries and the
notes.

**The owner's promotion, rehearsed on a scratch copy.** On a copy of the
repository, outside version control, a build record was written as a passing
build would write it (a simulation: no `lake build` ran). Before it, `advance
glm_wheels_bundle absorbed` was refused (no record; 13 staged files not
installed). After it, the same command installed the 13 files and filed the
item in `done/`; `advance cent_compiler_v12 measured` and `absorb-staged
cent_compiler_v12` installed the 4 cent files and left the compiler parts
open; `advance Rule30_GLM_Study lean_verified` passed; `check` reported 0
errors. On that copy `src/GLM.py -q "what sequence is 1, 1, 2, 3, 5, 8"`
answered A000045 from position 1, and the wheel tests passed against the
installed package (`test_integer_wheel` 46, `test_monster_wheel` 24,
`test_cent_wheels` 36, `test_wheels` 34, `test_lookup_kinds` 18 with its 2
staged-kind cases skipped). The repository itself was not touched.

**The gates tightened.** A review of the first version found three gaps,
each closed the same day: the *measured* gate took any deciding figure, so the
scaffold's draft "None yet" passed and nothing recorded a decision; a recorded
pass counted however old it was, and absorption did not run the tests again;
and *study drafted* asked only that the `.md` exist. The study gate now holds
the `.yaml` to the `.md`, every result carries its fingerprint, absorption
re-runs every test, and *measured* needs a finished study and an acceptance
decision (§2). A second review found two more: where pytest is not installed
the runner fell back to `python3 -m unittest`, which collects no plain test
function and so passed such a file having run nothing (most of the package's
test files are written that way); and the owner's two scripts reported each
step's status in their logs but always exited 0. The fallback is now the
package's own runner (`intake/fallback_tests.py`), which runs `TestCase`
tests and plain functions, refuses a test that needs a pytest fixture and
fails a file in which nothing ran; the scripts exit 1 when a required step
fails. A third review found that the runner called `setup_class` but never
`teardown_class`, so a check placed in a class teardown was never run; it now
runs pytest's setup and teardown hooks in pytest's order (class, method,
module and function) and a failing hook fails the file. A fourth review found
that a test result's `detail` copied the last line the test had printed (a
banner, a saved-file path, an error message) into the ledger; a detail is now
written by the intake itself from the exit code, what that code means for the
kind of test, and for a package test the counts of its closing tally, and the
152 details already in the ledger were rewritten the same way (the results,
dates and fingerprints unchanged). The two staged wheel items were given theirs with `accept`,
which quotes their studies and lists only met marks; the 21 earlier
absorptions were marked `legacy_absorption`. The test results of the four open
items at *tested* or beyond predated fingerprints; `retest <id> --stale` ran
all 13 of their named tests again against the code as it now stands, and all
13 pass (`Rule30_GLM_Study` 1, `attention` 1, `cent_compiler_v12` 4,
`glm_wheels_bundle` 7, the staged tests among them), so their recorded passes
are current until the package or the items change.

### 7.4 What is left

* The owner's `scripts/rebuild_lean.sh`: its build record promotes
  `Rule30_GLM_Study`, `glm_wheels_bundle` and `cent_compiler_v12` to Lean
  verified (or names the files that fail), and the two wheel items can then
  be absorbed as above, which confirms their provisional install.
* Lean files for the attention simulator's finite claims.
* Studies for the four triaged items (`scaffold` drafts them).
* `GLM-main.zip` and the supplied PDFs moved to the paths their records name, on
  the owner's machine.
