# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is in flight: Phase 184 (the declared majority rule, `tool majority`), Phase 183 (the Lorentzian evidence space) and Phase 182 (the Lorentzian lift of the ambiguous space, the owner's `iter10_lorentzian.py` audited) are closed, and before them Phases 180 (every Leech shell proved) and 181 (improper Lorentz families with a change of units in `tool frame`), in `MASTER_PLAN.md`. The next round starts from `STATUS.md` §2.1. The test-file sign-off is still owed (no pytest here).

**Deciding figure.** 0 steps outstanding.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict
and the figure above are grounded in the body below, and
`glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Last altered 29 October 2026.*

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

**No round is in flight.** Phase 184 (29 October 2026; the declared majority
rule for conflicting evidence, taken from `STATUS.md` §2.1 item 11's first
line) is closed: `LorentzianMajority.lean` (in `AxiomAuditAll.lean`);
`reasoning/lorentzian_majority.py` (`tool majority`); `tools
lorentzian-majority` (8 of 8 marks); `tests/test_lorentzian_majority.py` run by
hand, all passing. Write-up: `studies/LORENTZIAN_MAJORITY_STUDY.md`.
Phase 183 (owner's request, 29 October 2026; the
Lorentzian evidence space, taken from `STATUS.md` §2.1 item 11) is closed:
`LorentzianEvidence.lean` (in `AxiomAuditAll.lean`);
`reasoning/lorentzian_evidence.py` (`tool evidence`, and the certificate guard
and settling question in `tool lorentz`); `tools lorentzian-evidence` (13 of 15
marks); `tests/test_lorentzian_evidence.py` run by hand, all passing. Write-up:
`studies/LORENTZIAN_EVIDENCE_STUDY.md`.
Phase 182 (owner's request, 22 October 2026; the
Lorentzian lift of the ambiguous space, the owner's `iter10_lorentzian.py`
audited) is closed: `LorentzianLift.lean` and `GolayDeepHole.lean` (in
`AxiomAuditAll.lean`); `reasoning/lorentzian_lift.py` (`tool lorentz`);
`tools lorentzian-lift` (11 of 12 marks); `tests/test_lorentzian_lift.py` run
by hand, all passing. Write-up: `studies/LORENTZIAN_LIFT_STUDY.md`.
Phases 180 and 181 (taken from `STATUS.md` §2.1
items 2 and 10, 22 October 2026) are closed. Phase 180:
`LeechShellCount.lean` (the Leech shell procedure proved for every shell, in
`AxiomAuditAll.lean`); `reasoning/leech_shells.py` (`proved_shells_check`);
`tests/test_leech_shell_count.py` run by hand, all passing. Write-up:
`studies/LEECH_SHELL_COUNT_STUDY.md`. Phase 181: `LorentzUnits.lean` (9
theorems, in `AxiomAuditAll.lean`); `reasoning/frame_plane.py` (three units
families); `tools improper-units` (8 of 8); `tests/test_improper_units.py` run
by hand, all passing. Write-up: `studies/IMPROPER_UNITS_STUDY.md`.

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
`PYTHONPATH=src python3 -m glm_universal.signoff --close --jobs 8`.
