# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is in flight: Phases 147 and 148 (the budget rule in
the answering path, a deep hole read to its certificate by the `hole` kind,
proved in `BudgetReading.lean`, 8 of 8 measured marks; and the guarded read in
`nearest`, proved in `NearestAddress.lean`, 7 of 7 measured marks) are closed
and recorded in `MASTER_PLAN.md`. The next round starts from the To-Do list,
`STATUS.md` §2.1. The test-file sign-off is still owed (no pytest here).

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

**No round is in flight.** Phases 147 and 148 are closed. In order: the Lean
files (`RequestProject/GLM/BudgetReading.lean`,
`RequestProject/GLM/NearestAddress.lean`, proved), the frozen-path baseline
(`reasoning/_data/budget_guard_baseline.json`, 202 cases), then the answering
path (`reasoning/hole_reading.py` and the `hole` kind;
`reasoning/nearest_address.py` and the address path of `nearest`; the column-3
templates `hole` and `nearest_address`), the measurement modules, the tests
(`tests/test_budget_reading.py`, `tests/test_nearest_address.py`) and the
pre-registrations; then the measurements, in this order:
`tools budget-guard-frozen --write`, `tools budget-reading --write --jobs 8`,
`tools nearest-address --write`. The studies are
[`studies/BUDGET_READING_STUDY.md`](studies/BUDGET_READING_STUDY.md) and
[`studies/NEAREST_ADDRESS_STUDY.md`](studies/NEAREST_ADDRESS_STUDY.md); the
record is [`MASTER_PLAN.md`](MASTER_PLAN.md), "Phase 147" and "Phase 148". 0
steps of the phases are outstanding. Phase 148's predicted count of certified
points was wrong (copied from a mis-summed Phase 143 figure); it is recorded
in its study §7.2.

**What this round invalidated, and re-took.** `runtime/` and
`evaluation/cases.py` changed, so the query-escalation cache (`tools queryesc
--write`), the frozen-path comparison (`tools frozen-path --write`), the
address read (`tools address-read --write`), the junction read (`tools
junction-read --write`) and the typed plans (`tools plans --write`) were
re-taken, then `corpus --refresh`.

**One step owed: the release sign-off** (owed since Phase 134, now for
Phases 135–148's new and changed test files too). pytest could not be
installed in this session either (no package index reachable). The two new
test files were run with a small runner calling each test function. Resume
with `python3 -m pip install pytest`, then
`PYTHONPATH=. python3 -m glm_universal.signoff --close --jobs 8`.
