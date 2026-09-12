# `glm_universal/sandbox` — worth running, not yet worth relying on

## Tier 0 — the coarse read

**Question.** What is in this directory, and what would it take for any of it to leave?

**Verdict.** One occupant, the reverse-call planner, isolated from everything the system computes with and carrying a promotion checklist that is computed rather than asserted.

**Deciding figure.** 1 module, and 0 shipped modules importing it.

**Recomputed by.** `glm_universal.sandbox.planner.promotion_checklist`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

One occupant, the reverse-call planner, isolated from everything the system
computes with and carrying a promotion checklist that is computed rather than
asserted: 1 module, and 0 shipped modules importing it.

A module lives here when it is worth running and not yet worth relying on. The
rule of the directory is short enough to state in full.

* **Nothing the system computes with may import from here.** No runtime,
  reasoning, semantics, evaluation or data module may depend on anything in
  this directory, so deleting it cannot change a single answer the system
  gives. The one declared exception is the documentation layer:
  `glm_universal.corpus.render` imports a sandbox module lazily, inside the
  block that reports on it, because a study of the sandbox has to be able to
  recompute what it says. That exception is checked in
  `glm_universal/tests/test_sandbox_planner.py`, not trusted.
* **The exactness rules apply here anyway.** Integers and `Fraction`; no float,
  no random source, no digest that carries meaning. A sandbox that is allowed
  to cheat teaches nothing.
* **Every module here carries a promotion checklist, computed rather than
  asserted.** It says exactly what would have to hold for the module to move
  into the package proper, and while any line of it is false the module stays
  where it is — the false line being the work that remains, not a caveat to be
  written around.

## The current occupant

| module | what it is | promotion |
|---|---|---|
| `planner.py` | the reverse-call planner: a problem-driven front end that inspects a problem and selects tools by precondition, instead of dispatching on a query kind decided before the problem is read | **not ready** — the safety gate holds, the utility gate does not |

Run it:

```
python3 -m glm_universal.tools planner
python3 -m glm_universal.sandbox.planner      # the same report, printed directly
```

Read it: [`studies/REVERSE_CALL_PLANNER_STUDY.md`](../../../studies/REVERSE_CALL_PLANNER_STUDY.md).

## What promotion would mean

Moving a module out of `sandbox/` and into the package proper, with the usual
consequences: a row in the pipeline board, a test file, and every claim it
makes recomputed when the corpus is rendered. Promotion is a decision recorded
against a checklist that was declared before the measurement, not a judgement
made after seeing an encouraging number.
