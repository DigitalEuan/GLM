# source_material — the GLM's intake

*Created 31 October 2026 (repository check; directive D22).*
*Last altered 1 November 2026: absorption ahead of the build (`absorb-ahead`, `confirm-build`) by the owner's decision, and where things stand after three items were absorbed that way. Before that, 31 October 2026: the Lean written / Lean verified stages, the build-record gate, staged code and `absorb-staged`; the study gate's synchronised manifest, current test results (fingerprints, `retest`), the finished measurement and its acceptance decision (`accept`), the test runner where pytest is absent; the snapshot re-taken; then the provisional install by the owner's decision (`provisional`, the register of provisional wheels), and the fallback runner's setup and teardown hooks; test-result details written in the intake's own words.*

New material for the GLM — a full study, a rough concept note, code, data, a
Lean development or a plan — enters here. It is absorbed into the GLM only
through the intake pipeline's gates: **a study, tests, Lean written and then
verified by a passing build, and measured help** (directive D22 in
[`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md)).

```
source_material/
  README.md      this file
  INTAKE.yaml    the intake ledger: one record per item, read and written by the pipeline
  ToDo/          items whose intake is open
  done/          items whose intake is finished: absorbed, or closed with a recorded reason
```

Every command below runs from the repository root with `PYTHONPATH=src`.

## Adding new material

1. Put the item (a folder or a single file) directly in `source_material/`.
2. Register it — this moves it into `ToDo/` and adds a stub record at *received*:

   ```
   PYTHONPATH=src python3 -m glm_universal.intake register source_material/<item> --kind "concept note" --offers "..."
   ```

3. Follow the item along its line with the commands below. `python3 -m
   glm_universal.intake status` shows where everything stands, and `python3 -m
   glm_universal.intake show <id>` shows one record, its gaps and what its next
   gate still lacks.

## The line, and the gate at each stage

| stage | the gate (evidence that must exist) | how it is reached |
|---|---|---|
| received | the item is in `ToDo/` and has a record | `register <path>` |
| triaged | its kind, what it claims or offers, and a next step are written | edit the record, then `advance <id> triaged` |
| study drafted | every named study is a usable pair: `studies/<ID>.md` with a Tier-0 block, and `studies/<ID>.yaml`, a manifest that validates against `glm-study-manifest/v1`, names the same id and states the same question, verdict and deciding figure as the `.md` | `scaffold <id>` drafts one in the house shape (Tier 0, questions, marks declared before the code, Lean obligations); after editing the `.md`, `python3 -m glm_universal.corpus.study_manifest --sync` brings the `.yaml` back in step |
| tested | every named test exists and its last recorded result is a pass; on any promotion the pass must also have been taken against the code as it now stands (see *Current test results*) | `advance <id> tested` runs the named tests and records dated, fingerprinted results |
| Lean written | every named Lean file is in the build tree and imported by `AxiomAuditAll.lean`, and `python3 -m glm_universal.lean_check` passes (a static check, not a build) | `advance <id> lean_written` |
| Lean verified | the owner's build record `scripts/logs/lean_build_evidence.json` — written by `scripts/rebuild_lean.sh` only when its static check, `lake build` (with the axiom audit) and `sorry` scan all pass — has the same toolchain and Mathlib pins, its audit imported each named file, and each named file **and every file it imports** is byte for byte the file that was built | `advance <id> lean_verified` after `scripts/rebuild_lean.sh` passes; the record's date is written into the item's `lean_build` |
| measured | the study named first in `measured` passes the study gate and is **finished** — no draft text left (`TO WRITE`, the scaffold's draft verdict or figure), a deciding figure that is a measurement, manifest status `closed` (`open` is unanswered; `negative` means close the item instead) — and the record's `acceptance` decides it against the study's own declared criterion: `criterion` and `result` each quoted from the study, `marks` naming met marks that carry the help (required when the study declares marks; a missed mark refuses), and `decision: accept` | `accept <id> --criterion "..." --result "..." --mark M1 ...` writes the acceptance (refused unless it would pass this gate), then `advance <id> measured` (the build record is read again) |
| absorbed | no file left in `staged/` and no part left `provisional`; the modules it became exist and have tests; filed in `done/` | `advance <id> absorbed` (every named test is run again first, the build record is read again, the staged files installed, provisional parts confirmed and their register entry removed, the gate held against the installed package and the install undone if it fails) |
| closed | finished without absorption: a reason, and evidence that exists; filed in `done/` | `close <id> --reason "..." --evidence <STUDY or path>` |

The evidence accumulates: an item at *tested* must also satisfy *triaged* and
*study drafted*. Promotion to *Lean verified* or any later stage reads the
build record at that moment, so a Lean file changed since the last passing
build is no longer verified; `check` warns when a verified item's Lean file
has changed since its build. A record's `stage` is the stage of the item's
**open** work; parts taken earlier are listed under `parts` with where they
went, so an item whose first parts are absorbed but whose others are untouched
stays in `ToDo/` at the stage of the rest.

### Current test results

Every test result is recorded with the fingerprint of the code it ran against:
the package (generated-data folders left out), the item's staged files in
place and the item's own files. A promotion accepts only a pass with the
fingerprint of the code as it now stands, so a pass taken before the package,
the item or its staged code changed does not count. A result's `detail` is
written by the intake (the exit code, what it means for that kind of test and,
for a package test, how many tests passed, failed and were skipped); it never
copies what the test printed (run the test again to read its output). The
tests are run as follows:

* `advance` runs every named test when passing *tested*, runs them all again
  before anything is absorbed, and on any other promotion runs again each test
  whose last result is not a current pass;
* `absorb-staged <id>` runs every named test again before installing;
  `--no-run` on either command runs nothing, and the recorded passes must then
  already be current;
* `retest <id>` (or `retest <id> --stale`) runs the tests and records the
  results without moving the item; `check` notes an open item whose results are
  no longer current;
* a package test runs under pytest; where pytest is not installed it runs
  under the package's own fallback runner (`python3 -m
  glm_universal.intake.fallback_tests <file>`), which runs `TestCase` tests
  and plain test functions and classes with their setup and teardown hooks (a
  failing `teardown_class` or `teardown_module` fails the file), refuses a
  test that needs a pytest fixture, and never passes a file in which no test
  ran (`python3 -m unittest` would pass a file of plain test functions having
  run none of them).

### Staged code

Code ported and tested for the package before its item's Lean is built does
not go into the package. It waits in the item's own folder at
`<item>/staged/<path in the repository>` (only below `src/glm_universal/`),
and the parts it belongs to have status `staged`:

* a test named `staged:src/glm_universal/tests/test_x.py` runs against the
  staged code in a scratch view of the repository (the package's `.py` files
  copied, everything else linked, the staged files put in place); the
  repository is never written;
* `advance <id> absorbed` installs the staged files once every gate up to
  *measured* holds with a current build record; the staged parts become
  `absorbed` and the installed paths are recorded under `installed`;
* `absorb-staged <id>` does the same for the staged parts of an item whose
  other parts stay open (the item stays in `ToDo/`), on the same evidence:
  a fresh run of every named test, the build record, and the measured gate
  with its acceptance decision;
* `check` fails when a staged file would overwrite a different file already
  in the package.

### Provisional install (the owner's decision only)

The owner may decide that staged code which has passed its tests, has its
Lean written and has been measured should serve **before** its build — as on
31 October 2026 for the two wheel items: "keep them in the wheels folder now,
clearly marked provisional until my Lean build log confirms them". Then:

```
PYTHONPATH=src python3 -m glm_universal.intake provisional <id> \
    --decision "<the owner's words>" --wheel <wheel id> ...
```

installs the staged files into the package, records the parts `provisional`
with the decision, and lists the item in the register
`src/glm_universal/wheels/_data/provisional.json` (its wheels, modules, Lean
files, decision and date). Nothing is promoted: the item stays at its stage
(*Lean written* or beyond) in `ToDo/`. Every answer that rests on a
provisional wheel carries a `provisional:` note naming the item and its
Lean files (`glm_universal.wheels.provisional_status`). When the owner's build
record verifies the item's Lean files, `advance <id> absorbed` (or
`absorb-staged <id>`) runs every named test again, turns the provisional
parts `absorbed` and removes the register entry, and the note goes. `check`
fails when the register and the ledger disagree, a provisional module is
missing from the package or has no test, or a provisional part stands in
`done/`.

### Absorption ahead of the build (the owner's decision only)

The owner may also decide that an item whose help is measured should be
**absorbed** before the build — as on 1 November 2026 for three items:
"Absorb the ones that measurably help now, based on your measurements and
standalone Lean check; record that my own rebuild_lean.sh run still has to
confirm them". Then:

```
PYTHONPATH=src python3 -m glm_universal.intake absorb-ahead <id> \
    --decision "<the owner's words>" --standalone <Lean file> ... \
    --check "<how the standalone Lean check was made>"
```

runs every named test again, installs the staged code, turns the item's
staged and provisional parts `absorbed`, records the decision and the
standalone check, and files the item in `done/` when no part is left open
(an item with open parts is absorbed partially and stays in `ToDo/`). The
register keeps the item, now as *absorbed ahead of the build*, so every
answer that rests on it still says that the owner's build has to confirm its
Lean files. When the owner's `scripts/rebuild_lean.sh` writes a build record
that verifies them, `PYTHONPATH=src python3 -m glm_universal.intake
confirm-build <id>` records the confirmation and removes the register entry,
and the note goes. `check` holds the ahead record and the register together.

`python3 -m glm_universal.intake check` fails when the ledger and the folders
disagree (an item without a record, a record without its item, anything loose
in `source_material/`, an unfinished item in `done/` or a finished one in
`ToDo/`, an open, staged or provisional part in `done/`) or when a record claims a stage
without its evidence, and when a cited Lean file is neither audited, held in
`src/lean/awaiting_recovery/`, nor recorded missing in
[`studies/_lean_files_needed.md`](../studies/_lean_files_needed.md).
Records absorbed by earlier rounds, before acceptance decisions were recorded,
carry `legacy_absorption` instead of an `acceptance` block; `check` accepts
that only for a record filed in `done/` at *absorbed* (and notes it), and no
promotion ever accepts it.
The pipeline itself is described and measured in
[`studies/INTAKE_PIPELINE_STUDY.md`](../studies/INTAKE_PIPELINE_STUDY.md).

## Standing rules

* **Items stay as supplied.** Moving an item between `ToDo/` and `done/` keeps
  its internal layout byte-identical. Named item tests run on a scratch copy,
  so a script that writes files never changes the item. A repair made in place
  (allowed by the owner for the supplied Python items) is recorded in the
  item's `last_action`. A round may add a `staged/` folder to an item; it
  never edits the supplied files. Nothing under `source_material/` is dated
  except this README, the two folder READMEs and the ledger.
* **New wheels.** A wheel supplied here is surveyed in its item's record
  (`wheels`: what it is, its test result, its overlap with the existing wheels
  and the finite claims a Lean file must prove). It moves into the one wheels
  folder, `src/glm_universal/wheels/`, only when its item passes the gates —
  its Lean obligations built and audited (the build record), its help
  measured. Until then it waits in the item's `staged/` folder, or, by the
  owner's decision, is installed there marked provisional (above).
* **Code finds items through constants.** Code that reads an item uses
  `glm_universal.constants.source_material_item(name)`, which looks in `done/`,
  then `ToDo/`, then the old flat location, so filing an item never breaks a
  reader.
* **Local-only files.** `GLM-main.zip` and the supplied PDFs are kept on the
  owner's machine and out of version control (`.gitignore`). Their records
  carry `local_only: true`; `check` notes, without failing, when one still sits
  at the flat location, and on the owner's machine it should be moved to the
  path its record names.

## Where things stand

The ledger is authoritative; run `python3 -m glm_universal.intake status`.
On 1 November 2026 it holds 44 records: 8 items in `ToDo/` (4 triaged, 2 with
a study drafted, 1 tested, 1 Lean written) and 36 in `done/` (23 absorbed, 13
closed, two of them local-only files not in this checkout). No item is *Lean
verified*: the owner's build has not yet written a build record. Three items
were **absorbed ahead of the build** by the owner's decision of 1 November
2026, on the measurements of
[`studies/INTAKE_CAPABILITY_STUDY.md`](../studies/INTAKE_CAPABILITY_STUDY.md)
and a standalone Lean check of `src/lean/RequestProject/GLM/IntakeChecks/`:
`glm_wheels_bundle` (the Integer and Monster wheels and the sequence wheel's
`next` reading; filed in `done/`), `Rule30_GLM_Study` (the hypothesis engine:
`tool rule30`, `tool conjecture` and the plan search behind `tool arc`; filed
in `done/`) and `cent_compiler_v12` (the fifteen formula wheels and `tool
derive`; its compiler, SPICE emission, application proposals and notes are
still open, so it stays in `ToDo/` at *Lean written*). For all three the next
step is the owner's: run `scripts/rebuild_lean.sh`, then `confirm-build <id>`.
The 21 items absorbed by earlier rounds were absorbed before the build
record and acceptance decisions existed; each record's `lean_build` and
`legacy_absorption` say so, and the first passing build re-checks them
(`check` then warns on any Lean file that no longer matches).
