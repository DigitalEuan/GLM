# How to run a round — pick the work up, move it, put it down again

## Tier 0 — the coarse read

**Question.** How does a session pick this repository up, make a change that holds, and close the round without re-running everything?

**Verdict.** Orient from four short reads, run the cheapest gate that could fail, and close the round with one incremental command: write the finding down, refresh, check, `signoff --close`.

**Deciding figure.** The suite is <!--figure:test-files-->226 test files<!--/figure--> and 7 instruments, each signed against a digest of everything it depended on, so a change re-runs what it touched rather than all of it.

**Recomputed by.** `glm_universal.signoff.ledger.plan`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Last altered 20 October 2026.*

---

This is the operating manual. [`ENTRY.md`](ENTRY.md) says what to *read*;
this says what to *do*, in the order to do it, and which of the three gates to
run at each point. It exists because the expensive failure mode of this
project is not a wrong answer — it is a session that re-runs everything it
could have skipped, or writes a finding nowhere and loses it.

## 0. The five-minute pick-up

**Before running anything, read §0.1, *Run-order hazards*.** Eight short
rules — the first two are *don't edit documents while `corpus --refresh` is
running* and *after editing `evaluation/cases.py`, re-take `queryesc`,
`budget-guard-frozen` and `ties-ladder-frozen` first, then the rest, then
refresh the corpus last*.

**First, read [`WHITEBOARD.md`](WHITEBOARD.md).** It is the round in progress
written down as it happens: what the last session finished, what it had
running when it stopped, and the command that resumes each thing that remains.
Keep it current while you work — a step finished is a whiteboard line changed,
not a note to write up later — and fold it into `STATUS.md` (the To-Do
list) and `MASTER_PLAN.md` when the round closes.

**pytest is not installed in this environment by default.** Every test file
runs under `python3 -m pytest`, so install it before running any test gate —
`python3 -m pip install pytest` (pytest 9 or later; the suite's subtest
count relies on it). Without it every unit fails and the failure reads as a
broken suite, which is how Phase 107's first close failed. The sign-off
commands that run tests now check for it first and stop with the install
line instead of failing every unit.

Then run this and follow what it says.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --check     # is the tree as the last round left it?  ~3 s if nothing moved
PYTHONPATH=. python3 -m glm_universal.signoff --verify    # which units and instruments are still signed
PYTHONPATH=. python3 -m glm_universal.signoff --why       # if anything is stale: which kind of file moved
```

* **Both clean** — the last round closed. Read `STATUS.md` §2 (the To-Do
  list), take a line, and work.
* **`--check` names a stale derivation** — run the command it names (normally
  `corpus --refresh`), then re-check.
* **`--verify` reports unsigned units** — the last round did not close. Fix
  that first: `signoff --run-everything --jobs 8`, and record it. An unclosed
  round is the one thing that makes the next three rounds slower.
* **`--verify-release` reports `partial` units, or a close ran out of
  time** — run `signoff --close --jobs 8` again. It runs only the units the
  release question still calls stale, because every signature is written as
  it is earned, not at the end, and it ends with `--verify-release`, which
  decides the round.

Before a wide edit, price it: `signoff --impact ../PROJECT_DIRECTIVES.md`
names the units that edit would make stale and what they last cost. After the
edit, run the cheapest gate that could fail (§2). To close, §4 — write the
finding down, then refresh, check, close, commit.

**Using the system itself**, rather than maintaining it:

```bash
cd overlay
python3 GLM.py -q "address of golay"                    # one query, 23 kinds
python3 GLM.py -q "report lean"                         # 66 report subjects ('report routes' lists the route choices)
PYTHONPATH=. python3 -m glm_universal.corpus --ask "what bears on the Leech lattice?"
PYTHONPATH=. python3 -m glm_universal.tools --help      # the study instruments
```

### 0.1 Run-order hazards — read these before running anything

*Added 20 October 2026 (Phase 172), at the owner's request. Each line was
learned by losing time or work to it; keep the list, and add to it.*

1. **Don't edit documents while `corpus --refresh` is running.** It rewrites
   the documents that carry generated figures from the copies it read when it
   started, so an edit made meanwhile is silently overwritten. Commit before
   starting a refresh; if an edit was lost, restore it from the commit
   (`git diff`, then re-apply). Draft prose outside the tree while a refresh
   runs, and copy it in after.
2. **Re-take order matters after editing `evaluation/cases.py`.** Some saved
   results read others: `nearest-address` and `budget-reading` digest the
   budget-guard frozen path, and `nearest-question` reads the ties-ladder
   frozen path. Re-take `queryesc`, `budget-guard-frozen` and
   `ties-ladder-frozen` first, then the rest, then refresh the corpus last:

   ```bash
   cd overlay; export PYTHONPATH=.
   for t in queryesc budget-guard-frozen ties-ladder-frozen; do python3 -m glm_universal.tools $t --write; done
   python3 -c "from glm_universal.corpus import caches; print('\n'.join(caches.describe()))"   # the rest, with their commands
   # ... re-take each one it names ...
   python3 -m glm_universal.corpus --refresh                                              # last
   ```

   The three frozen paths take about fifteen minutes each.
3. **A new Lean file changes the Lean-corpus reports** once the corpus is
   refreshed with it (`report lean`, `report retrieval`, the relay and
   anonymous registers). Since Phases 171 and 172 `report relay` and
   `report anonymous` are pinned on their claims, read off the measurement,
   so their pins no longer move with the counts; any other case that quotes
   a Lean-corpus count will. Refresh once after adding a Lean file, *before*
   running the evaluation, or the evaluation checks a corpus that is not the
   tree's.
4. **A stored measurement can call itself current and still hold a stale
   answer.** A cache is guarded by the digest of its *sources*. Since Phase
   174 the two answer censuses (`evidence-model`, `evidence-in-use`) also
   digest the stored measurements their answers quote, so re-taking one of
   those turns them stale, and `signoff --close` re-takes them last. Other
   measurements that record answers (the frozen paths, `queryesc`) are still
   guarded by their sources only: after a code change, re-take the
   measurements a census reads before the census itself. The censuses also
   quote the document address book (`corpus/_data/document_addresses.json`),
   which `corpus --refresh` rebuilds whenever a document has changed, so a
   round that edits documents ends: documents, `corpus --refresh`, the two
   censuses (`evidence-model` then `evidence-in-use`), `corpus --refresh`
   again.
5. **Editing a module a study lists in its `_SOURCES` stales that study's
   cache.** `runtime/conversation.py`, `runtime/session.py`,
   `runtime/parser.py` and `evaluation/cases.py` are in many. `corpus
   --check` (or the `caches.describe()` line above) names every stale cache
   and the command that re-takes it; do that before the evaluation and
   before the close.
6. **pytest cannot be installed here** (no package index). The test-file
   sign-off of `signoff --close` therefore stays owed (since Phase 134).
   Test files that do not import pytest can be run by calling their
   `test_*` functions; record a hand run as a hand run, never as the
   sign-off.
7. **Run anything longer than a minute in the background, with a log**
   (`nohup … > /tmp/x.log 2>&1 &`) and write the resume command on
   [`WHITEBOARD.md`](WHITEBOARD.md). Measured costs on eight cores: `corpus
   --refresh` about 5–10 minutes after a code or Lean change; each frozen
   path about 15 minutes; `evaluation --jobs 8` about 10 minutes;
   `evaluation --replay` about 9 minutes more; `lake build` of one new Lean
   file seconds once Mathlib is built.
8. **Order of a round's close**: code and Lean first; `corpus --refresh`
   once (so the corpus has the new Lean files); re-take stale measurements
   in the order of hazard 2; run the evaluation; write every document; then
   `corpus --refresh` **last**, `corpus --check`, commit. Never touch a
   document after the last refresh without refreshing again.

## 1. Orient — four short reads, in this order

1. [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) — the Positioning section
   (what is claimed and what is not), the standing target, and the
   <!--figure:directives-->17 standing rules<!--/figure-->. Everything else assumes these have been read.
2. [`STATUS.md`](STATUS.md) §1 — where the work stands in one screen (the
   full instrument table is [`SYSTEM.md`](SYSTEM.md) §1).
3. [`STATUS.md`](STATUS.md) §2, the To-Do list — §2.1 is the next round,
   sharpest first. **Start the round from one of these**, or say in the round
   record why not.
4. [`DIGEST.md`](DIGEST.md) — every document at tier 0, generated. Use it to
   find the two or three studies that bear on the candidate, and descend into
   those only.

Then confirm the tree is where the last round left it:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --check       # documents, ~30 s
PYTHONPATH=. python3 -m glm_universal.signoff --verify     # what is still signed
```

If either reports drift before you have changed anything, the previous round
did not close. Fix that first, and record it: an unclosed round is the one
thing that makes the next three rounds slower.

**When a design question is stuck, try an analogy.** The owner's method,
first used in the friction study and written down in
[`studies/FRICTION_STUDY.md`](studies/FRICTION_STUDY.md) §8: name a
well-established mathematical or physical system the problem resembles, write
down which of its parts map onto the GLM and which do not, and turn each
mapped part into a declared mechanism with a control and a mark before
anything is measured. Phase 158 used it for the oscillator junction (the
reference circle; [`studies/OSCILLATOR_JUNCTION_STUDY.md`](studies/OSCILLATOR_JUNCTION_STUDY.md)).

## 2. Work — the three gates

Run the **cheapest gate that could fail on what you just did**. That is the
whole of the speed discipline; everything below is which gate that is.

| gate | command | what it covers | when |
|---|---|---|---|
| **documents** | `python3 -m glm_universal.corpus --check` | tier-0 contract, links, coverage, generated blocks, inline figures | after any prose edit |
| **documents, unchanged** | the same command | answers from the stored verdict in about three seconds when nothing it reads has moved; `--check --all` forces the full pass | picking the round up |
| **changed** | `python3 -m glm_universal.signoff --run-everything --jobs 8` | every test unit and instrument whose closure moved, and nothing else | after any code, data or Lean edit |
| **close** | `python3 -m glm_universal.signoff --close --jobs 8` | the release question -- every unit and instrument signed with the exhaustive cases on -- paying only what is owed: unsigned, changed, failed, or signed fast; then `--verify-release` | once, closing the round, and again if it was interrupted |
| **release, from scratch** | `python3 -m glm_universal.signoff --release --jobs 8` | all <!--figure:test-files-->226 test files<!--/figure--> and all 7 instruments, ledger ignored | only when the rule itself changed (`signoff/rules.py`), or on purpose; never as a routine close |

All three are run from `overlay/` with `PYTHONPATH=.`.

**The documents gate skips a question it has already answered.** The verdict
is stored beside a digest of everything the check can read — the documents,
the rendering code, the data it reads and the Lean sources the blocks quote.
If nothing in that closure has moved since the check last *passed*, it says
so and stops: 3 seconds instead of 50, which is what the pick-up read costs
now. Only a pass is recorded, so a failure is never skipped, and
`--check --all` ignores the record entirely.
[`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5f.

**The documents gate also takes the cache census.** Ten study modules keep a
measurement cache keyed on the digest of their sources; `corpus --check` says
which are stale and prints the `tools ... --write` command that re-takes each
one. It never re-takes one itself — that is minutes of work, and it belongs to
the session.

**The documents gate never recomputes.** A handful of derivations are kept
beside the digest of the code they came from — the planner's reading of the
whole evaluation set, the type-2 class table, the economic lattice points —
and `--check` runs with recomputation *forbidden*. If one of them is stale the
check names it and the command that rebuilds it and stops, in half a minute,
instead of quietly spending a quarter of an hour rebuilding it. So:

* after a **prose** edit, `corpus --check` is the whole cost;
* after a **code** edit, expect `corpus --check` to report a stale derivation,
  and run `corpus --refresh` once — it rebuilds the caches, the address books,
  the generated documents and the figures, in the only order that converges.
  The expensive half of it, the planner's reading, runs on every core; set
  `GLM_PLANNER_JOBS=1` to make it serial.

Four commands answer "what would that cost?" without paying it:

```bash
PYTHONPATH=. python3 -m glm_universal.signoff --plan              # what is stale, and what it costs
PYTHONPATH=. python3 -m glm_universal.signoff --why               # *why* each stale unit is stale
PYTHONPATH=. python3 -m glm_universal.signoff --impact ../STATUS.md  # what an edit would cost, before it
PYTHONPATH=. python3 -m glm_universal.signoff --closure test_x.py # what one unit depends on
```

**Why the middle gate is worth trusting.** Each unit is signed against the
SHA-256 of its whole closure: the file, every module it imports transitively,
the frozen data those modules read, the documents and Lean files they name,
the harness and the interpreter. If that digest holds, re-running proves
nothing. Nothing is skipped silently — `--plan` says what will be skipped and
why, and `--verify` re-checks every signature without running anything.

**What makes a lot of units stale, and how to pay it once.**

* Editing `PROJECT_DIRECTIVES.md` makes 32 of the 123 units stale (it was
  120 before Phase 78: the file was named in the prose of modules nearly
  everything imports, and prose no longer counts). Still batch directive
  edits into one pass rather than trickling them through the round. `--impact` says this before the edit; ask
  it of anything you are about to touch widely.
* `--why` is the other half: after the edit it names the *kind* of file that
  moved for each stale unit — `changed: documents` is prose and will pass,
  `changed: code` may not — so a long plan can be read rather than guessed at.
* Editing the sign-off machinery is now cheap unless it is the **rule**:
  `signoff/rules.py` (what a closure is, what a digest covers, how a unit is
  run) is in every closure and costs the whole suite, while `signoff/ledger.py`
  (the plan, the record, the runner, the reporting) costs 6 units.
  [`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5c is
  the measurement.
* Editing one Lean file makes the units that *name that file* stale, plus the
  26 that read the whole development with a glob — not the whole suite. That
  used to be 84 of 97; [`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md)
  §5a is the measurement and the fix.
* Editing a study makes the units that name that study stale, and usually
  nothing else.
* So: **make the edits, then run the gate once.** Running it between edits is
  the single most common way a round loses an hour.

**What no longer makes anything stale** (Phase 78,
[`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5g):

* **A refreshed figure or generated block.** A unit is signed against the
  *written* part of each document: the value between
  `<!--figure:NAME-->` and `<!--/figure-->`, and a generated block's body, are
  left out of its digest. Only the units that read rendered regions (their
  closure holds `corpus/render.py`, `corpus/checks.py` or `figures.py`) are
  signed against raw bytes. So `corpus --refresh` moving a number in twenty
  documents re-runs the document checks, not the suite.
* **A document or Lean file named only in a docstring.** Prose is not a read;
  code that opens a file names it outside a docstring.
* **A data file no module names.** A `_data/` file is in a closure only when
  a module of that closure names it, so re-taking one measurement cache
  re-runs the units that read it (about 22) instead of every unit that
  reaches any reasoning module (117).
* **The corpus moving under a self-measurement.** The native-parity and
  native-words figures are taken over the repository's own documents and
  Lean files. They are current while their *code* is unchanged; a moved
  corpus is printed as a `note:` by `corpus --check`, never as a failure.
  Re-take them (`tools native-parity --write`, `tools native-words --write`)
  at the *start* of a round if the round wants fresh figures -- never during
  the close, because the close is what writes the documents they read.

## 3. Keep the generated layer generated

Never hand-edit a number that a generator emits. One command puts the derived
layer back, in the only order that converges in one pass:

```bash
PYTHONPATH=. python3 -m glm_universal.corpus --refresh           # address books, caches, documents, blocks, figures, FIGURES.md
```

(`figures --write` still rewrites `FIGURES.md` on its own; since Phase 78 the
refresh does it too, so it is not a second step. A measurement cache such as
`tools native-parity --write` refuses to store a reading taken while the
document address book is stale — run the refresh first.)

The Lean development has **one copy**, `overlay/glm_lean/RequestProject/GLM/`.
The repository's `lakefile.toml` builds it in place (`srcDir =
"overlay/glm_lean"`), so `lake build` at the repository root compiles exactly
the files the package reads. There is no mirror to regenerate and no second
copy to compare.

Order matters at the end of a round: **edit the documents first, refresh
last.** A refresh taken before the final edit is stale again the moment the
edit lands, and the round closes on a document check that fails for no
reason.

If a count appears in prose and moves every round, it should be an inline
figure: an HTML comment naming a registered figure, the value, and a closing
comment, all on one line. The registry is `glm_universal/corpus/render.py`,
the existing documents are full of examples to copy, and a marker naming a
figure that is not registered is reported as `unknown figure` by the refresh.
That is directive D6, and it is why the hand-reconciliation sweep no longer
exists.

## 4. Close the round — the exact checklist

A round is not finished when the code works. It is finished when someone who
was not here can find out what happened and check it, and the tree is signed.
The close below is the shortest sequence that gets there in one pass; every
step is in it because skipping it has cost an earlier round a second or third
pass (the record is
[`studies/ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5g–§5i).

### 4.1 Write it down — every edit, in one batch, before any gate

| what | where | why it is on the list |
|---|---|---|
| the finding, with its controls and negative results | a study in `studies/`, named `*_STUDY.md`, with a tier-0 block | the tier contract fails a study without one |
| the round itself | [`MASTER_PLAN.md`](MASTER_PLAN.md): a new `## Phase N` section at the head of the phases, and the tier-0 verdict naming Phase N+1 | the plan holds the past tense |
| the To-Do lines taken and left | [`STATUS.md`](STATUS.md) §2: delete what was taken, add what the round left, replace the "Just closed" paragraph | the status document is a To-Do list, not a stack |
| what the system now is | [`SYSTEM.md`](SYSTEM.md): a row in the §1 table for a new instrument, a paragraph in §2 for a new capability | only if the system changed |
| a new test file | a row in `overlay/glm_universal/tests/README.md` | `test_figures` fails a test file with no row |
| a new evaluation case file | the skip list of `tests/test_question_frames.py` | Phase 108's close failed on it |
| a new Lean file | `lake build` from the repository root, and no `sorry` | the `lean-build` and `lean-sorry-free` instruments |
| the GLM as a whole | [`studies/GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md): a subsection for what the round built, the date line, and Part VII and the appendices brought level with it | the owner's standing instruction (Phase 119): the paper is the record of the whole system and is kept up to date in every development run |
| the round in flight | [`WHITEBOARD.md`](WHITEBOARD.md) back to "no round in flight" | the next session reads it first |
| every file created or altered | a date stamp in the file itself: `Created <day Month year>` or `Last altered <day Month year>`; `python3 -m glm_universal.tools dates` lists them and fails on a bad one | the owner's instruction of 18 October 2026, directive D17; nothing under `source_material/` is touched |
| a new document | a state document: a tier-0 block whose verdict is also written, word for word, as a sentence of the body, and a link from a state document; a record: a place under `archive/` and a line in the archive list of [`ENTRY.md`](ENTRY.md) | the coverage claim, and `test_corpus` wants more than half of all verdicts quoted verbatim |

**Never hand-type a count that moves.** Every count of report subjects,
registers, query kinds, Lean files, test files, CLI cases and Lean
declarations in a state document is an inline figure
(`<!--figure:KEY-->value<!--/figure-->`), and `corpus --refresh` rewrites it.
If a test reports a count that moved, the count was hand-typed: make it a
figure (registry: `glm_universal/corpus/render.py`) rather than editing the
number. Anything inside a `<!-- figures:history -->` region is a record: plain
numbers, no figure markers (`corpus --check` fails a figure in a record).

### 4.2 Run it — three commands, once

```bash
python3 -m pip install pytest                                 # once per session, if missing
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --refresh        # derived layer, in the one order that converges
PYTHONPATH=. python3 -m glm_universal.corpus --check          # documents gate; fix anything it names before closing
PYTHONPATH=. python3 -m glm_universal.signoff --close --jobs 8
cd .. && git add -A && git commit -m "Phase N: ..."
```

`--close` works in four stages (Phase 109): (0) re-take every stale
measurement cache; (1) run every stale counted unit and instrument, the
document checks held back; (2) run `corpus --refresh` itself when a document
check is owed, so the totals just recorded reach the documents; (3) run the
document checks; then `--verify-release`, which decides the round. It is
resumable — signatures are written unit by unit — so if it fails or is
interrupted, fix what it names and run the same command again: it pays only
for what is still owed.

**After the close, touch nothing that is a document**: the close signs the
tree it ran on, and every document is in the corpus digest. If a document
must change afterwards, make the edit and run the three commands again — and
know that it is not cheap: any document edit rewrites the document address
book, which 11 units hold since Phase 114 (54 before; §4.3). Measured in Phase 111, a one-line edit to
`WHITEBOARD.md` after a finished close cost `corpus --refresh` 176 s,
`corpus --check` 123 s and `signoff --close` 1,636 s — 32 minutes. So get
every document right *before* the close, and re-check the To-Do list and the
phase record once more before running it. `ARISTOTLE_SUMMARY.md` is the one exception: it is
written after the session and, since Phase 111, is outside the corpus and
every closure, so it never reopens a closed round.

### 4.3 What it costs, by what the round edited

Serial seconds, as last measured by the ledger (`signoff --impact FILE` gives
the current figure for any file before you touch it); `--jobs 8` divides the
test time by roughly six on this machine.

| the round edited | units re-run | serial cost |
|---|---|---|
| **any document at all** | the 11 that hold the document address book (`corpus/_data/document_addresses.json`), which every refresh after a document edit rewrites — 54 until Phase 114 cut the toolbox's reach ([`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) §5j) | about 1,600 s, measured |
| `STATUS.md`, `MASTER_PLAN.md` and a study (a usual round) | the 11 above, the 5 that name `STATUS.md` and the 16 that name `MASTER_PLAN.md`; the three sets overlap | at most about 4,900 s (the three figures summed) |
| `STATUS.md` alone, by name | 5 | about 1,450 s |
| `MASTER_PLAN.md` alone, by name | 16 | about 1,900 s |
| `SYSTEM.md` alone, by name | 3 | about 600 s |
| one Lean file | the units naming it, plus the glob readers | see `--impact` |
| `PROJECT_DIRECTIVES.md` | 63 | about 5,600 s — batch directive edits |
| `signoff/rules.py` (the rule) | all 158 and the 7 instruments | about 8,400 s — the whole suite |

Fixed costs, measured in Phase 111: the whole suite under `--close --jobs 8`
(what a change to the rule costs) 67 minutes wall-clock; `corpus --refresh` 8 min after a large
document change (most of it the document address book; seconds when only a
few sections moved), `corpus --check` about 2 min when anything moved and
3 s when nothing did, `signoff --verify` about 40 s. So the floor of a
round's close is the address book: about half an hour on 8 jobs for any
round that writes anything down, whatever else it touched. Cutting that
coupling is a To-Do line of its own ([`STATUS.md`](STATUS.md) §2.2). What
Phase 111 did cut is the session note, which made every pick-up start stale,
and the false docstring reader, which put the status document and the plan
into about sixty closures by name (§5i of the iteration-cost study).

### 4.4 The pick-up that proves the last close

The next session's first two commands are the check on this one:
`corpus --check` should answer from its stored verdict in seconds, and
`signoff --verify` should report every test file and instrument signed. If
either does not, the close was not finished, and finishing it is the first
step of the new round (§0).

## 5. The standing target

Every round is judged against one target: **does the system reason better than
it did?** — where "reason" is only ever the faculty that was measured, under
the perturbation that was declared before the measurement. The three things
that count as progress, in order:

1. **Derivation.** An answer no register holds, computed by the system.
   [`studies/BLOCKERS_STUDY.md`](studies/BLOCKERS_STUDY.md) §1 separates this
   from the two below, mechanically, and most of what this repository measures
   is still in the middle class.
2. **Addressing.** An answer recovered from the geometry when the query is not
   the stored key. Real, and narrower than it sounds.
3. **Refusal.** An answer not given when it would have been wrong. A round
   that removes wrong answers at a counted cost in refusals is a round that
   moved the target.

A round that does none of the three is a round that cleaned up, and the
record should say so in those words rather than dressing it as progress.

## 6. When something fails

| symptom | what it means | what to run |
|---|---|---|
| `corpus --check` says *stale blocks* | a generated block or figure is behind the code | `corpus --refresh` |
| `corpus --check` says *the tier-0 verdict says what the document does not* | the verdict uses a word the body never uses; the body is the ground | write the claim into the body, or narrow the verdict |
| `corpus --check` says *address book: stale* | the corpus moved | `corpus --refresh` |
| `corpus --check` says *derived cache: … is stale* | code in a derivation's closure moved; the check refuses to pay for the rebuild | `corpus --refresh`, once |
| a test quotes a count that has moved | the document and the code disagree (D6) | `figures --write`, then fix any hand-typed count it names |
| `signoff --plan` says almost everything is stale | a directive, a widely named document or the harness moved | expected; run the gate once and move on |
| `lake build` is slow after one Lean edit | it is incremental; the first build of a session is not | let it run, and use the time on the documents |
| a measurement in a test no longer holds | the corpus grew and the measurement moved with it | re-take it, write what it *is*, and say in the record that it moved |
| the close did not finish | it is resumable: signatures are written unit by unit | `signoff --close --jobs 8` again |
| `corpus --check` names a stale *measurement cache* | a study module's sources moved under its stored figures | the `tools ... --write` command it names; a check never re-takes one itself |

The last row is the important one. A measurement that has moved is not a test
to be loosened: it is a result. Record the new value and what moved it.
