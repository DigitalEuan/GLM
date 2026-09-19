# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is open: the sections below are what the next round
fills in as it works.

**Deciding figure.** 0 steps are in flight and 0 remain; the last round to
finish left 98 of 98 test files and 7 of 7 instruments signed.

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

The last round to finish was **Phase 48 — the handover closed, and the query
that had grown too slow to pass**, recorded in
[`MASTER_PLAN.md`](MASTER_PLAN.md); it left the tree with `corpus --check`
**current**, `signoff --verify-release` reporting **98 of 98** test files and
**7 of 7** instruments signed with the exhaustive cases on, the suite at
**3,924 tests across 97 of the 98 test files, 15,326 subtests**, the
end-to-end evaluation at **157 / 157**, and `lake build` clean with no
`sorry`.

No round is open: the sections below are what the next round fills in as it
works. Start it from [`ITERATE.md`](ITERATE.md) and §3.4 of
[`STATUS.md`](STATUS.md). 0 steps are in flight and 0 remain.

## 1. Done, committed, and checked here

*(nothing yet this round)*

## 2. In flight right now

*(nothing running)* — when something is, name the command, where it is
writing its log, and what it will leave behind.

## 3. What remains, in order, with the command for each

*(the next round's plan goes here, one line per step, each with the command
that runs it and roughly what it costs)*

## 4. Known state of the gates

| gate | state |
|---|---|
| `corpus --check` | current, document checks hold |
| `signoff --verify` | signed |
| release | 98 of 98 test files, 7 of 7 instruments |
| evaluation | 157 / 157 |
| `lake build` | clean, no `sorry` |

## 5. Things learned worth not re-learning

* **A round that edits a study after its release hands over a stale tree.**
  Phase 47 did and Phase 48 paid for it: 77 units re-run for prose alone. The
  order in §4 of `ITERATE.md` — documents, refresh, release — is worth the
  discipline.
* **A query whose cost drifts up to the evaluation's 300 s per-case ceiling
  fails the release, and the answer is arithmetic rather than a longer
  ceiling.** `report lean` was doing seventeen million pair distances in
  Python; an identity removed a third of it and exact pruning most of the
  rest, with every published figure unchanged.
* The suite sentence only moves when a release in which **nothing** fails
  records the totals; until then five documents quote a stale count and
  `test_figures.py` fails on them. Close the release before reconciling
  the prose — and note that adding tests moves it, so the order is release,
  `figures --write`, reconcile the two hand-written totals in `STATUS.md`,
  `corpus --write`, release again.
* Editing `evaluation/cases.py` invalidates the planner's stored report, which
  costs about six minutes on the next refresh. Batch such edits.
* `pytest` and `pytest-subtests` are the suite's only external dependencies; a
  fresh sandbox may need `pip install pytest pytest-subtests`.
* The long poles, measured in Phase 48: a release ≈ 11 min of unit runs at 8
  jobs plus 4 min of instruments, a refresh ≈ 1–8 min depending on what moved,
  the documents check 50 s — or about 3 s when nothing it reads has moved.
* A measurement that has moved is a result, not a test to loosen: re-take it,
  write what it *is*, and say in the record what moved it.
