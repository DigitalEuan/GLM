# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is in flight: Phase 138 (tool verdicts, conditionals
and the unrolled search in the stepwise planner; the classical
closest-fraction theorem in `NearestFraction.lean`, so the nearest-fraction
tool has no bound; 6 of 6 marks) is closed and recorded in
`MASTER_PLAN.md`. The next round starts from the To-Do list,
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

**No round is in flight.** Phase 138 is closed (tool verdicts and the
nearest fraction): the Lean file (`RequestProject/GLM/NearestFraction.lean`,
proved), the Farey certificate (`reasoning/rational_approx.py`,
`runtime/toolbox.py`), the verdict reader (`runtime/tool_values.py`), the
verdict steps, conditionals and the search (`runtime/stepwise.py`,
`reasoning/stepwise_script.py`), then the held-out sets and the measurement
(`evaluation/tool_verdicts_cases.py`, `tools tool-verdicts`, 6 of 6 marks).
The study is
[`studies/TOOL_VERDICTS_STUDY.md`](studies/TOOL_VERDICTS_STUDY.md); the record
is [`MASTER_PLAN.md`](MASTER_PLAN.md), "Phase 138". The next round starts from
the To-Do list, `STATUS.md` §2.1; 0 steps of the phase are outstanding.
In one line: a tool's yes/no answer now steers a chain, and the nearest
fraction is proved for every bound.

**One step owed: the release sign-off** (owed since Phase 134, now for
Phases 135–138's new and changed test files too). pytest could not be
installed in this session either (no package index reachable), so the
test-file units could not be re-signed. The new and changed test files
(`test_tool_values.py`, `test_connected_machine.py`, `test_connected_two.py`,
`test_wiring.py`, and in Phase 138 `test_tool_verdicts.py` and the five
`test_stepwise*.py` files) were run under `unittest` with a local stand-in
for the pytest import, kept outside the repository, and passed. Resume with
`python3 -m pip install pytest`, then
`PYTHONPATH=. python3 -m glm_universal.signoff --close --jobs 8`.
