# `glm_universal/sandbox` — worth running, not yet worth relying on

## Tier 0 — the coarse read

**Question.** What is in this directory, and what would it take for any of it to leave?

**Verdict.** Three occupants — the reverse-call planner, the four-register memory split and the Lean-source generator — isolated from everything the system computes with, each carrying a promotion checklist that is computed rather than asserted, and no checklist yet says ready.

**Deciding figure.** 3 modules, 0 of them ready, and 0 modules that compute an answer importing them.

**Recomputed by.** `glm_universal.sandbox.occupancy_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

Three occupants — the reverse-call planner, the four-register memory split and
the Lean-source generator — isolated from everything the system computes with,
each carrying a promotion checklist that is computed rather than asserted:
3 modules, 0 of them ready, and 0 modules that compute an answer importing
them.

Those three numbers are read out of the directory itself by
`glm_universal.sandbox.occupancy_report`, which calls each occupant's
`promotion_checklist()` and walks the package's import graph:

```
cd overlay
PYTHONPATH=. python3 -c "from glm_universal import sandbox; print(sandbox.occupancy_report()['modules'])"
```

A module lives here when it is worth running and not yet worth relying on. The
rule of the directory is short enough to state in full.

* **Nothing the system computes with may import from here.** No runtime,
  reasoning, semantics, evaluation or data module may depend on anything in
  this directory, so deleting it cannot change a single answer the system
  gives. The declared exceptions are the documentation and instrument layers
  and nothing else: `glm_universal.corpus.render` and
  `glm_universal.corpus.cost` import a sandbox module lazily, inside the block
  that reports on it, because a study of the sandbox has to be able to
  recompute what it says, and `glm_universal.tools` runs it as a study
  instrument. Those exceptions are checked in
  `glm_universal/tests/test_sandbox_planner.py`, not trusted, and
  `occupancy_report` reports the exception-free count — the modules that
  compute an answer and import the sandbox — which is zero.
* **The exactness rules apply here anyway.** Integers and `Fraction`; no float,
  no random source, no digest that carries meaning. A sandbox that is allowed
  to cheat teaches nothing.
* **Every module here carries a promotion checklist, computed rather than
  asserted.** It says exactly what would have to hold for the module to move
  into the package proper, and while any line of it is false the module stays
  where it is — the false line being the work that remains, not a caveat to be
  written around.

## The current occupants

| module | what it is | promotion |
|---|---|---|
| `planner.py` | the reverse-call planner: a problem-driven front end that inspects a problem and selects tools by precondition, instead of dispatching on a query kind decided before the problem is read | **not ready** — the safety gate holds, the utility gate does not |
| `memory_split.py` | the supplied four-register memory split — working, episodic, semantic and procedural — run over the conversation layer's own declared follow-ups and scored against licensing | **not ready** — all three lines are false; where it gains an answer it gains it by choosing a member of an `ambiguous-antecedent` refusal |
| `lean_generation.py` | the supplied carrier-to-Lean generator, with the *real* round trip in place of the supplied check: write the source, read it back with `reasoning.lean_address.parse_file`, re-quantise | **not ready** — four of five lines are false; the generated source parses but no declaration survives the round trip |

Run them:

```
python3 -m glm_universal.tools planner
python3 -m glm_universal.sandbox.planner          # the same report, printed directly
python3 -m glm_universal.sandbox.memory_split
python3 -m glm_universal.sandbox.lean_generation
```

Read them: [`studies/REVERSE_CALL_PLANNER_STUDY.md`](../../../studies/REVERSE_CALL_PLANNER_STUDY.md)
for the planner, and [`studies/SUPPLIED_PORTS_STUDY.md`](../../../studies/SUPPLIED_PORTS_STUDY.md)
for the other two.

## What promotion would mean

Moving a module out of `sandbox/` and into the package proper, with the usual
consequences: a row in the pipeline board, a test file, and every claim it
makes recomputed when the corpus is rendered. Promotion is a decision recorded
against a checklist that was declared before the measurement, not a judgement
made after seeing an encouraging number.
