# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is in flight: Phase 53 is closed, and the next round
starts from §3.4 of `STATUS.md`.

**Deciding figure.** 0 steps remain in the list below.

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

**No round is in flight.** Phase 53 — the column, not the pair — is closed:
the `extremum` operation is wired, measured, proved, written up and released,
and [`MASTER_PLAN.md`](MASTER_PLAN.md) Phase 53 is its record. The next round
starts from §3.4 of [`STATUS.md`](STATUS.md), whose first candidate is the
declared table of conversions between scales that both the ordering operation
and the extremum operation refuse for want of.

## 1. Done, committed, and checked here

* Nothing is pending from Phase 53. The last things it needed were the three
  measurements a new query kind moves — the sandbox planner's fallback
  reading (now taken over 14 refusals, all refused), the iteration-cost
  ledger's blast radius, and the suite and end-to-end sentences — each
  re-taken rather than loosened, and two stale Lean citations repaired so
  that every name the package cites resolves in the development.

## 2. In flight right now

* Nothing.

## 3. What remains, in order, with the command for each

1. Nothing for this round. Start the next one from
   [`ITERATE.md`](ITERATE.md) §0 and [`STATUS.md`](STATUS.md) §3.4.

## 4. Known state of the gates

| gate | state |
|---|---|
| `corpus --check --all` | **current** |
| `signoff --verify-release` | **101 of 101 test files, 7 of 7 instruments** |
| evaluation | **172 / 172** |
| `lake build` | clean, 122 Lean files, no `sorry` |

## 5. Things learned worth not re-learning

* **A round that stops before its release hands over more than a release.**
  Phase 49 did, and the release Phase 50 ran turned up six failing units;
  Phase 51 did, and the release Phase 52 ran turned up eight drifted counts
  and one brittle unit. Phase 52 stopped after committing two files that
  nothing referred to, which is how Phase 53 began with a stale cache.
* **A new Lean file is a change to two measurements.** The relay and the
  anonymous register read the Lean corpus, so adding one file moves both. They
  are re-taken (`tools relay`, `tools anonymous` are read through
  `report relay` / `report anonymous`) and the evaluation phrases that quote
  them are updated — the measurement is a result, not a test to loosen.
* **A test that pins a measurement must pin the shape, not a coincidence.** A
  unit asserted that the value 99 never reaches the recorded totals, which was
  true only while the suite had fewer than 99 counted test files. A sentinel
  that no legitimate total can take says the same thing and keeps saying it.
* **Adding a query kind moves more than the language figures.** `parser.KINDS`
  feeds the `query-kinds` figure and the described-coverage sentence, and the
  new kind's refusals also move the sandbox planner's fallback reading and the
  capability assessment's per-kind and refusal tables.
* **A cited Lean name must be written as one token.** A theorem name split
  across two adjacent f-string fragments reads as a truncated name to the
  citation check, and a name ending in `?` is not the name the check resolves:
  cite the theorem, not the definition.
* **A closure is computed from string constants.** Writing a Lean-file glob
  pattern inside a docstring is enough to re-create the whole-development
  dependency the selectivity test guards against; say "the whole Lean tree"
  in prose instead.
* **A tier-0 verdict may not carry inline figure markers**, and every word of
  it has to appear in the body below it — a near synonym is not enough, so
  either write the verdict in the body's own words or put the words in the
  body.
* Editing `evaluation/cases.py` invalidates the query-escalation cache
  (`tools queryesc --write`) as well as the planner's stored report. Batch
  such edits.
* Two generated blocks read the corpus digest they are written into, so
  `corpus --write` can need a second pass before `corpus --check` is current.
* **The suite sentence converges in two releases, not one.** A release records
  the totals it measured, so the sentence that quotes them is a release behind:
  run the release, `figures --write`, refresh, then release again.
* `pytest` and `pytest-subtests` are the suite's only external dependencies; a
  fresh sandbox may need `pip install pytest pytest-subtests`.
* The long poles: a full release ≈ 12 min of unit runs at 8 jobs plus 4 min of
  instruments, a refresh ≈ 1–8 min depending on what moved, the documents
  check 50 s — or about 3 s when nothing it reads has moved.
