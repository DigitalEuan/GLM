# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is in flight: Phase 175 (the owner's pipeline kit in the GLM: its bridge, its seven Lean files, and `tool induce`) is closed, in `MASTER_PLAN.md`. The next round starts from `STATUS.md` §2.1. The test-file sign-off is still owed (no pytest here).

**Deciding figure.** 0 steps outstanding.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict
and the figure above are grounded in the body below, and
`glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Last altered 21 October 2026.*

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

**No round is in flight.** Phase 175 (the owner's pipeline kit, taken at the
owner's request of 21 October 2026) is closed: the delivered files placed and
split in `source_material/GLM_Pipeline_Kit/`; the kit's bridge run on the
GLM's own substrate (0 failures); the kit's seven Lean files under
`GLM/PipelineKit/` and `PipelineInduction.lean` (17 theorems, 0 `sorry`);
`reasoning/pipeline_kit.py`, `tool induce`, `reasoning/pipeline_kit_study.py`
and `tools pipeline-kit` (12 of 12 marks); `tests/test_pipeline_kit.py` (7 of 7
by hand).

**Standing hazards — read before running anything:** [`ITERATE.md`](ITERATE.md)
§0.1, *Run-order hazards*. The two that cost the most:

* **Don't edit documents while `corpus --refresh` is running.** It rewrites
  them from the copies it read when it started.
* **Re-take order matters after editing `evaluation/cases.py`.** Some saved
  results read others: `nearest-address` and `budget-reading` digest the
  budget-guard frozen path, and `nearest-question` reads the ties-ladder
  frozen path. Re-take `queryesc`, `budget-guard-frozen` and
  `ties-ladder-frozen` first, then the rest, then refresh the corpus last.

**One step owed: the release sign-off** (owed since Phase 134): the test-file
sign-off, the gate the evaluation's own runs do not replace. pytest is still
not installable here (no package index). Resume with
`python3 -m pip install pytest`, then
`PYTHONPATH=. python3 -m glm_universal.signoff --close --jobs 8`.
