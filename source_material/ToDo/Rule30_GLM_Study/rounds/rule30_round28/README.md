# Rule 30 / GLM — Round 28 GLM overlay

This folder carries the Round 28 work into the GLM: a **local-rule induction** reasoner for
grid puzzles (ARC-style), built on the Lean results in `GLM.LocalRule`
(`RequestProject/GLM/Rule30/LocalRuleInduction.lean` in the Lean package). The project brief
is `PROJECT_DIRECTIVE.md` in the Lean package; this folder is the GLM-side code only.

## What it does

`local_rule_induction.py` learns a table "neighbourhood → output colour" from the training
pairs of a task, for each of 21 readers (neighbourhood shapes), in order from simplest. It
answers only when the learned table reproduces every training pair and covers every
neighbourhood in the test input — the exact conditions proved in Lean
(`reproduces_iff_keyOK`, `answer_determined_iff_covered`). A clash in the examples refutes a
reader (`clash_refutes`). Otherwise it refuses rather than guessing.

## Files

| File | Purpose |
|---|---|
| `glm_glm_universal/reasoning/local_rule_induction.py` | The reader ladder |
| `glm_glm_universal/reasoning/theorem_wheel_round28.py`, `_data/r28_wheel_sample.json` | Round 28 theorem-wheel facts for the GLM |
| `apply_round28.py`, `setup_round28.sh` | Install the overlay into a GLM checkout (`STUDY=… PKG=…` optional) |
| `test_round28.py` | Self-test (all checks pass on a fresh unzip) |
| `local_rule_arc.py` (+ output) | Runs the ladder on the stored ARC tasks |
| `r28_benchmark.py` (+ output) | Before/after benchmark of the GLM |
| `inner_survivors.py`, `word_lifetimes.c` (+ outputs) | Empirical checks for To Do 19 and To Do 2 |

## Measured effect (empirical, from `r28_benchmark_output.txt`)

| Measure | Before | After |
|---|---|---|
| Stored ARC tasks (50) | 0 right | 1 right (`a85d4709`), 0 wrong |
| Development local-rule puzzles (108) | 0 right | 44 right, 1 wrong |
| Held-out local-rule puzzles (84) | 0 right | 24 right, 0 wrong (all controls refused) |
| Rule 30 knowledge alignment | 0/10 | 10/10 |
| Round 11 claim suite | 23/23, 2/5, 2/2 | unchanged |

An unsound guessing variant gets 1 right and 16 wrong on the same ARC tasks, so the refusal
rule is what keeps the error count at zero. The ARC gain is small: most ARC tasks are not
single local rules and need object-level readers (To Do 21 in `AUDIT.md`).

## Empirical findings (not proved)

* To Do 19: the inner-survivor recursion is not supported (minimum inner alternation 7–14
  while post-edge lifetime reaches 20; witness d = 14, S = 11083).
* To Do 2: for words `1110`, `11110`, `111110`, `Lmax − d ≤ 10` up to d = 24, but growing.

## Use

Run from the GLM directory holding `GLM.py` (unpacked from `glm_repo.zip`), with `STUDY`
set to the study folder (the parent of this folder) and, optionally, `PKG` set to the Lean
package folder `RequestProject/GLM/Rule30` (installs the full 282-row ledger wheel):

```
STUDY=/path/to/study PKG=/path/to/RequestProject/GLM/Rule30 sh $STUDY/rule30_round28/setup_round28.sh
```

It runs the earlier round setups, installs the Round 28 overlay and hooks, and ends with
`round 28: all checks pass`. The benchmark is `python3 rule30_round28/r28_benchmark.py`.
