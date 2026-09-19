# How to run a round — pick the work up, move it, put it down again

## Tier 0 — the coarse read

**Question.** How does a session pick this repository up, make a change that holds, and close the round without re-running everything?

**Verdict.** Orient from four short reads, run the cheapest gate that could fail, and close the round: write the finding down where it belongs.

**Deciding figure.** The suite is <!--figure:test-files-->98 test files<!--/figure--> and 7 instruments, each signed against a digest of everything it depended on, so a change re-runs what it touched rather than all of it.

**Recomputed by.** `glm_universal.signoff.ledger.plan`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

This is the operating manual. [`ENTRY.md`](ENTRY.md) says what to *read*;
this says what to *do*, in the order to do it, and which of the three gates to
run at each point. It exists because the expensive failure mode of this
project is not a wrong answer — it is a session that re-runs everything it
could have skipped, or writes a finding nowhere and loses it.

## 0. The five-minute pick-up

**First, read [`WHITEBOARD.md`](WHITEBOARD.md).** It is the round in progress
written down as it happens: what the last session finished, what it had
running when it stopped, and the command that resumes each thing that remains.
Keep it current while you work — a step finished is a whiteboard line changed,
not a note to write up later — and fold it into `STATUS.md` and
`MASTER_PLAN.md` when the round closes.

Then run this and follow what it says.

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --check     # is the tree as the last round left it?  ~3 s if nothing moved
PYTHONPATH=. python3 -m glm_universal.signoff --verify    # which units and instruments are still signed
PYTHONPATH=. python3 -m glm_universal.signoff --why       # if anything is stale: which kind of file moved
```

* **Both clean** — the last round closed. Read `STATUS.md` §3.4, take a
  candidate, and work.
* **`--check` names a stale derivation** — run the command it names (normally
  `corpus --refresh`), then re-check.
* **`--verify` reports unsigned units** — the last round did not close. Fix
  that first: `signoff --run-everything --jobs 8`, and record it. An unclosed
  round is the one thing that makes the next three rounds slower.
* **`--verify-release` reports `partial` units, or a release ran out of
  time** — resume it rather than restarting it:
  `signoff --release --resume --jobs 8` runs only the units the release
  question still calls stale, because every signature is written as it is
  earned, not at the end. `--verify-release` still decides the round.

Before a wide edit, price it: `signoff --impact ../PROJECT_DIRECTIVES.md`
names the units that edit would make stale and what they last cost. After the
edit, run the cheapest gate that could fail (§2). To close, §4 — write the
finding down, then refresh, check, release, commit.

**Using the system itself**, rather than maintaining it:

```bash
cd overlay
python3 GLM.py -q "address of golay"                    # one query, 21 kinds
python3 GLM.py -q "report lean"                         # 65 report subjects
PYTHONPATH=. python3 -m glm_universal.corpus --ask "what bears on the Leech lattice?"
PYTHONPATH=. python3 -m glm_universal.tools --help      # the study instruments
```

## 1. Orient — four short reads, in this order

1. [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) — the Positioning section
   (what is claimed and what is not), the standing target, and the
   <!--figure:directives-->16 standing rules<!--/figure-->. Everything else assumes these have been read.
2. [`STATUS.md`](STATUS.md) §1, the instrument table — where the work stands
   in one screen.
3. [`STATUS.md`](STATUS.md) §3.4, *Named for the next round* — the candidates,
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

## 2. Work — the three gates

Run the **cheapest gate that could fail on what you just did**. That is the
whole of the speed discipline; everything below is which gate that is.

| gate | command | what it covers | when |
|---|---|---|---|
| **documents** | `python3 -m glm_universal.corpus --check` | tier-0 contract, links, coverage, generated blocks, inline figures | after any prose edit |
| **documents, unchanged** | the same command | answers from the stored verdict in about three seconds when nothing it reads has moved; `--check --all` forces the full pass | picking the round up |
| **changed** | `python3 -m glm_universal.signoff --run-everything --jobs 8` | every test unit and instrument whose closure moved, and nothing else | after any code, data or Lean edit |
| **release** | `python3 -m glm_universal.signoff --release --jobs 8` | all <!--figure:test-files-->98 test files<!--/figure--> and all 7 instruments, exhaustive cases on, ledger ignored | once, closing the round |
| **release, resumed** | `python3 -m glm_universal.signoff --release --resume --jobs 8` | the same question, paying only what is still owed: unsigned, changed, failed, or signed with the exhaustive cases off | after a release that was interrupted |

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

* Editing `PROJECT_DIRECTIVES.md` makes almost every unit stale — 93 of 96,
  about 66 minutes of work: the rules are cited in the prose of a module
  nearly everything imports. Batch directive edits into one pass rather than
  trickling them through the round. `--impact` says this before the edit; ask
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

## 3. Keep the generated layer generated

Never hand-edit a number that a generator emits, and never edit the Lean
mirror. One command puts the derived layer back, in the only order that
converges in one pass:

```bash
PYTHONPATH=. python3 -m glm_universal.corpus --refresh           # address books, caches, documents, blocks, figures
PYTHONPATH=. python3 -m glm_universal.tools lean-mirror --write  # overlay/glm_lean/ from RequestProject/GLM/
PYTHONPATH=. python3 -m glm_universal.figures --write            # FIGURES.md
```

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

## 4. Close the round — write it down where it belongs

A round is not finished when the code works. It is finished when someone who
was not here can find out what happened and check it.

| what | where |
|---|---|
| the finding itself, with its controls and its negative results | a study in `studies/`, named `*_STUDY.md`, with a tier-0 block |
| what the system *is* now | [`STATUS.md`](STATUS.md) §2, replacing the previous round's entries |
| what is open, and what the next round should take | [`STATUS.md`](STATUS.md) §3.2–§3.4 |
| the record of the round, and of every round before it | [`MASTER_PLAN.md`](MASTER_PLAN.md) — a new phase, and the delivered record |
| a statement proved rather than measured | `RequestProject/GLM/`, mirrored into `overlay/glm_lean/` |

**`STATUS.md` holds the present tense and `MASTER_PLAN.md` holds the past
tense.** When a round closes, move the round record out of the status document
into the plan rather than letting the stack grow: that stack is what made the
status document unreadable once already. Anything written inside a
`<!-- figures:history -->` region is a record and its figures are frozen —
that is how an old measurement stays true.

Then, in order:

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --refresh
PYTHONPATH=. python3 -m glm_universal.corpus --check
PYTHONPATH=. python3 -m glm_universal.signoff --release --jobs 8
```

and commit. Commit **after each completed step**, not once at the end (D1): a
step is anything that leaves the tree working, and an interrupted session that
has been committing hands over something that runs.

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
| the release did not finish | it is resumable: signatures are written unit by unit | `signoff --release --resume --jobs 8`, then `--verify-release` |
| `corpus --check` names a stale *measurement cache* | a study module's sources moved under its stored figures | the `tools ... --write` command it names; a check never re-takes one itself |

The last row is the important one. A measurement that has moved is not a test
to be loosened: it is a result. Record the new value and what moved it.
