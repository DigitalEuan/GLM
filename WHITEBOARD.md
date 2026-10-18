# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is in flight: Phase 158 (the oscillator junction tried
four ways, and the analogy method written down) is closed and recorded in
`MASTER_PLAN.md`. The next round starts from the To-Do list, `STATUS.md`
§2.1. The test-file sign-off is still owed (no pytest here).

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

**No round is in flight.** Phase 158 (the oscillator junction tried four
ways; the analogy method written down) is closed. Done this round: the
pre-registration of `OSCILLATOR_JUNCTION_STUDY.md`, committed before the
variant module; `OscillatorJunction.lean` (0 `sorry`);
`engineering/oscillator_junction.py` and `tools oscjunction`; the four
censuses and the preservation set, stored; variant B shipped in
`engineering/domains.py`; the Phase 157 census re-taken; the evaluation
before and after (222 of 222, nothing moved); `tests/test_oscillator_junction.py`
(6, run by hand with `tests/test_domains.py`: 18 of 18 pass); §7 of the
study, §7.6 of `DOMAIN_WHEELS_STUDY.md`, §8 of `FRICTION_STUDY.md`;
`MASTER_PLAN.md` Phase 158; `STATUS.md`; `SYSTEM.md`; `ITERATE.md`; the paper
(§20.32); the READMEs. 0 steps of the phase are outstanding.

**One step owed: the release sign-off** (owed since Phase 134). pytest is
still not installable here (no package index). Resume with
`python3 -m pip install pytest`, then
`PYTHONPATH=. python3 -m glm_universal.signoff --close --jobs 8`.

Earlier rounds' records are in `MASTER_PLAN.md` (Phases 157, 156, …).
