# Rule 30 / GLM — Round 29: a stepwise planner for puzzles

Round 28 gave the GLM a **one-step** puzzle solver (the local-rule ladder). One step rarely
solves a puzzle: a typical ARC task is *crop the object, then mirror it, then recolour it*. This
round gives the GLM a **pipeline of steps**. It is built from methods the GLM already uses and
that are known to work, not from scratch:

| Method | Where it already lives | How it is used here |
|---|---|---|
| Stepwise planner: a chain is licensed when every step is; answer only when every licensed reading agrees | GLM `runtime/stepwise.py` (text questions) | the same rule, over chains of grid steps |
| Search loop: hard gate (D1) and Occam (C5) | GLM `reasoning/search_loop.py`, `SearchLoop.lean` | keep a plan only if it reproduces every demonstration exactly; cheapest tier first |
| Breadth-first state-space search with merging of equal states | standard planning / program-search method | plans that leave every grid in the same state are merged, so the search runs over states |
| Fitted final step (version space) | Round 28 `LocalRuleInduction.lean` | the last step is a colour map, a tiling, or a local rule fitted from the data, answered only on seen keys |
| Leave-one-out ("tuning by ear") | Round 25/28 | long plans with a fitted last step must also predict each demonstration from the others |
| Ask for the separating example | To Do 21 | when plans disagree, the refusal names the query cell whose value refutes one of them |

The Lean side is `RequestProject/GLM/Rule30/PlanSearch.lean` (namespace `GLM.PlanSearch`) in the
Lean package. It proves what the planner guarantees: that merging loses no plan
(`layer_complete`), that agreement can be checked on the merged layer (`agree_iff_layer`),
that the answer is that of every consistent plan of the answering depth (`planner_agree_all`),
and that the answer is correct when the true transformation is a cheapest explanation
(`planner_correct`, `minAgree_correct`). It also proves that it can be wrong without that premise
(`minAgree_needs_occam`), that merging on the demonstrations alone, without the queries, is
unsound (`train_only_signature_unsound`), and that the separating example always refutes one of
two disagreeing plans (`separating_example_refutes`).

## Files

| File | Purpose |
|---|---|
| `glm_overlay/glm_universal/reasoning/grid_planner.py` | The planner: 63 grid steps, 30 finishers (identity, tiling, the 21 Round 28 readers, 7 new readers: colour rank and 6 object-level), tiers, refusal, separating question |
| `apply_round29.py`, `setup_round29.sh` | Install into a GLM checkout (runs the Round 28 setup first) |
| `test_round29.py` | Self-test; a fresh unzip of `glm_repo.zip` ends with `round 29: all checks pass` |
| `planner_arc.py` (+ `planner_arc_output.txt`) | The planner on the 50 stored ARC tasks, plan by plan |
| `r29_benchmark.py` (+ `r29_benchmark_output.txt`) | Stand-alone benchmark by plan depth 0–3 |
| `r29_glm_benchmark_output.txt` | The Round 28 GLM benchmark (`rule30_round28/r28_benchmark.py`) rerun after `setup_round29.sh` |

## Measured effect (EMP: measured, not proved)

**Through the GLM's own tool entry point** (`r29_glm_benchmark_output.txt`; "before" is the Round 28
result in `rule30_round28/r28_benchmark_output.txt`):

| Measure | Round 28 | Round 29 |
|---|---|---|
| Stored ARC tasks (50) | 1 right, 0 wrong | **10 right, 0 wrong** |
| Round 28 development puzzles (108) | 44 right, 1 wrong | 65 right, 2 wrong |
| Round 28 held-out puzzles (84) | 24 right, 0 wrong | **48 right, 0 wrong** |
| Rule 30 knowledge alignment | 10/10 | 10/10 |
| Round 11 claim suite | 23/23, 2/5, 2/2 | unchanged |

The Round 28 "controls" mirror, rotate-180 and flip-rows were controls for *local* rules. They
are one geometric step, so the planner now solves them, and they are no longer controls.

**By plan depth** (`r29_benchmark_output.txt`; depth 0 = one fitted step, i.e. Round 28 plus the
new finishers):

| Set | depth 0 | depth 1 | depth 2 | depth 3 |
|---|---|---|---|---|
| Stored ARC (50, development) | 5 / 0 wrong | 10 / 0 | 10 / 0 | 10 / 0 |
| Round 29 development multi-step (132) | 12 / 0 | 57 / 3 | 98 / 3 | 98 / 3 |
| **Round 29 held-out multi-step (132)** | 12 / 0 | 47 / 0 | **96 / 0** | 96 / 0 |

The held-out set has 11 families: 9 compositions of 2 or 3 steps and 2 controls that no plan can
express. It was written after the planner was frozen (sha256 `a07403e2…`, printed in the output)
and scored once. Both controls were refused 24 of 24 times. One family (`transpose-erase`,
transpose and then a local rule) was refused 12 of 12 times, for the same unseen-key reason
Round 28 refuses `erase-isolated`. The later version of the planner (sha256 `8739a24c…`) only adds
the separating question to refusals; it gives the same answers on the stored ARC tasks.

**Where it goes wrong (development sets).** Every wrong answer we saw is a violation of the Occam
premise. A *cheaper* hypothesis fits all three demonstrations, but the truth is more expensive.
For example, in `objsize-flip`, when no demonstration contains a large object, "flip" alone fits.
`minAgree_needs_occam` says this cannot be excluded by the rule itself. What helps is more
demonstrations, or asking for the separating example.

**ARC tasks solved** (plan, then finisher): `1e0a9b12` gravity; `662c240a` the asymmetric block;
`b91ae062` upscale by number of colours; `d631b094` count row; `00dbd492` fill enclosed, then the
object-size reader; `7953d61e`, `bc4146bd` tiling finisher; `9caf5b84` colour-rank reader;
`ae58858e` object-size reader; `a85d4709` the Rule 30 row reader. The stored tasks were looked at
while the alphabet was chosen, so the ARC score is a development score.

## Use

From the GLM directory holding `GLM.py`:

```
STUDY=/path/to/study sh $STUDY/rule30_round29/setup_round29.sh
python3 $STUDY/rule30_round29/r29_benchmark.py arc_agi_17/data/training      # stand-alone
PYTHONPATH=. python3 rule30_round28/r28_benchmark.py                        # through the GLM
```

The planner is also usable on its own:
`grid_planner.solve(train_pairs, queries, max_depth=3)` returns the answer, the plan, the cost
tier, or a refusal with its reason (and, on disagreement, the cell to ask about).
