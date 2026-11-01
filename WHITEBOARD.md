# Whiteboard — the round in progress

## Tier 0 — the coarse read

**Question.** If this session stopped now, what would the next one need to
know to carry the round on?

**Verdict.** No round is in flight: Phase 186, the intake items absorbed where they measurably help (1 November 2026), is closed in `MASTER_PLAN.md`, and the next round starts from `STATUS.md` §2.1. Two steps are owed on the owner's machine: the Lean build (`scripts/rebuild_lean.sh`), then `confirm-build` for the three items absorbed ahead of it, and the test-file sign-off (no pytest here).

**Deciding figure.** 2 steps outstanding, both the owner's.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict
and the figure above are grounded in the body below, and
`glm_universal.corpus.checks.tier_report` fails if they stop being.*

*Last altered 31 October 2026 (repository check: the status below; the two steps owed on the owner's machine and the intake promotions that follow the build).*

*Last altered 1 November 2026 (Phase 186: closed; the build now confirms the three items absorbed ahead of it with `confirm-build`).*

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

**No round is in flight.** Phase 186 (1 November 2026; the intake items
absorbed where they measurably help, by the owner's decision of that day,
[`INTAKE_CAPABILITY_STUDY.md`](studies/INTAKE_CAPABILITY_STUDY.md)) is closed:
its record is in `MASTER_PLAN.md`. Phase 185 (31 October 2026; the repository
check after the October 2026 reorganisation, taken from `STATUS.md` §2.1 item
0) is closed: its record is in `MASTER_PLAN.md`, what it left is `STATUS.md`
§1b, and the intake items still in `source_material/ToDo/` are listed with
their next step by `PYTHONPATH=src python3 -m glm_universal.intake status`.
Phases 184 and earlier are closed as recorded there.

**Two steps owed, both on the owner's machine:**

* **The Lean build.** No Lean toolchain here. Resume with
  `scripts/rebuild_lean.sh` from the repository root; it builds, runs the axiom
  audit, writes `scripts/logs/lean_build_latest.log` and, when everything
  passes, the build record `scripts/logs/lean_build_evidence.json` (summary
  line ends `record=0`; the script exits 0 only then, and 1 naming the failed
  steps otherwise). The files it is the first build of:
  `Wheels/IntegerWheel.lean`, `Wheels/SporadicOrders.lean`,
  `Wheels/CentWheels.lean`, the restored `Rule30/SidewaysPeriodTwo.lean`, the
  renamed Rule 30 files, the four standalone checks
  `IntakeChecks/RuleThirtyBits.lean`, `SporadicOrderCheck.lean`,
  `NextTerm.lean` and `Derivability.lean` (built here only on their own, with
  Lean 4.34 and Mathlib) and the regenerated `AxiomAuditAll.lean`. With the
  record written, the three items absorbed ahead of it on 1 November 2026 are
  confirmed by the commands in `STATUS.md` §2.3 (`intake confirm-build
  Rule30_GLM_Study`, `intake confirm-build cent_compiler_v12`, `intake
  confirm-build glm_wheels_bundle`); until then they are listed in
  `wheels/_data/provisional.json` as *absorbed ahead of the build* and every
  answer from them says so.
* **The release sign-off** (owed since Phase 134): the test-file sign-off,
  the gate the evaluation's own runs do not replace. pytest is not installable
  here (no package index). Resume with `python3 -m pip install pytest`, then
  `scripts/check_repository.sh` (every Python gate, with a log) and
  `PYTHONPATH=src python3 -m glm_universal.signoff --close --jobs 8`.

**Standing hazards — read before running anything:** [`ITERATE.md`](ITERATE.md)
§0.1, *Run-order hazards*. The two that cost the most:

* **Don't edit documents while `corpus --refresh` is running.** It rewrites
  them from the copies it read when it started.
* **Re-take order matters after editing `evaluation/cases.py`.** Some saved
  results read others: `nearest-address` and `budget-reading` digest the
  budget-guard frozen path, and `nearest-question` reads the ties-ladder
  frozen path. Re-take `queryesc`, `budget-guard-frozen` and
  `ties-ladder-frozen` first, then the rest, then refresh the corpus last.
