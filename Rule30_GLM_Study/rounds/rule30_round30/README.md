# Rule 30 / GLM — Round 30: one pipeline for the investigation

Rounds 26–29 left four related open items (AUDIT To Do 23–26) plus two partly-done ones (18, 21).
This round joins them into **one pipeline** with four stages that share the same search, the same
hard gate and the same refusal rule, and runs it on puzzles *and* on candidate Rule 30 statements:

| Stage | To Do | What it does | Lean guarantee (`RequestProject/GLM/Rule30/Pipeline.lean`, namespace `GLM.Pipeline`) |
|---|---|---|---|
| 1. plan | 21, 23 | breadth-first plans of grid steps; **13 new fitted middle steps** (recolour by object property, scale by a number read from the grid, draw lines between objects, objects fall, …); **goal regression**: a plan prefix whose output shape cannot reach the target shape is skipped | `run_append_eq_some_iff_runBack`, `semMid_eq_some_iff` (fitted middle step = its fitted map), `shapePrune_sound`, `shapePrune_skip` (pruning never removes a consistent plan) |
| 2. ask | 21, 24 | when surviving plans disagree, ask the oracle for the cell they disagree on, keep the plans that match, re-plan; stop at a question budget | `truth_mem_askFilter`, `askFilter_card_lt` (each answer removes a plan, keeps the truth), `askLoop_questions_lt` (fewer questions than plans), `askLoop_correct` (if it stops answering, the answer is the truth's) |
| 3. gate | 26 | Occam check: leave-one-out from plan depth 1 when there are ≤ 2 demonstrations, from depth 2 otherwise | `minAgree_wrong_imp` (a wrong answer means a cheaper consistent rival), `gated_correct`, `gate_can_fix`, and the honest negative `gate_can_drop_truth` |
| 4. statements | 18, 25 | the same planner over candidate **statements** about the period-2/3/4 half-line problem (families LIN and AMORT, steps *steeper*, *analogy*, *implies*); hard gate = the level data; every frontier statement is certified sharp in Lean | `RequestProject/GLM/Rule30/PipelineData.lean`: 30 `sharp_*` theorems and `frontier_round30` (CERT) |

## Files

| File | Purpose |
|---|---|
| `glm_overlay/glm_universal/reasoning/glm_pipeline.py` | stages 1–3 (steps, shape pruning, fitted readers incl. asked cells, `decide`, `ask_loop`, AUTO gate) |
| `glm_overlay/glm_universal/reasoning/statement_planner.py` | stage 4 (planner over statements, Occam for statements, comparison with Round 27) |
| `glm_overlay/glm_universal/reasoning/candidate_benchmark.py` | the Round 27 candidate benchmark (oracle, enumerate/repair strategies, `--glm` plug-in) |
| `glm_overlay/glm_universal/reasoning/pipeline_tool.py`, `_data/r30_frontier.json` | `tool pipeline …` in the GLM toolbox; the 30 certified frontier rows |
| `pipeline.py` | **one command** for the whole pipeline: `python3 pipeline.py [ARC_DIR] [statements\|grids\|all]` |
| `pipeline_bench.py` | stages 1–3 measured (A,B: development and old held-out sets; C: Occam on development families; D: fresh held-out set) |
| `r30_heldout.py` | the fresh Round 30 held-out set (11 families × 12, incl. 2 controls), frozen before scoring |
| `apply_round30.py`, `setup_round30.sh` | install into a GLM checkout (runs the Round 29 setup first) |
| `test_round30.py` | self-test; a fresh unzip of `glm_repo.zip` + `setup_round30.sh` ends with `round 30: all checks pass` |
| `*_output.txt`, `statement_frontier.json`, `proposals.json` | the stored outputs of this round's run |

Install: from the directory holding `GLM.py`,
`STUDY=/path/to/study PKG=/path/to/RequestProject/GLM/Rule30 sh $STUDY/rule30_round30/setup_round30.sh`.

## Measured effect (EMP: measured, not proved)

Pipeline sha256 `031c6eb5…` (printed in every output); held-out file sha256 `88b2843e…`.

**Fresh held-out set (132 puzzles, scored once, `pipeline_bench_D_output.txt`):**

| | right | wrong | refused |
|---|---|---|---|
| Round 29 planner (depth ≤ 2) | 56 | 6 | 70 |
| pipeline without fitted middle steps | 90 | 4 | 38 |
| pipeline, stage 1 | **96** | **4** | 32 |
| + ask, ≤ 1 / 2 / 3 / 5 questions | 101 / 103 / 104 / **106** | 4 / 5 / 5 / 5 | 27 / 24 / 23 / 21 |

Both controls refused 24 of 24. The 4 stage-1 wrongs are Occam failures (a cheaper plan fits all
demonstrations): `objsize-recolour-rot90` 2, `scale-by-objects` 1, `flip-scale-by-objects` 1.
Asking adds one wrong answer (after the oracle's answers a cheaper wrong plan is left alone), which
`askLoop_correct` permits: the loop is correct only when the truth is among the cheapest plans.

**Ask loop on the older sets** (`pipeline_bench_AB_output.txt`), right answers at ≤ 1/2/3/5
questions: Round 28 development 79/83/88/91, Round 28 held-out 60/66/69/77, Round 29 held-out
97/100/102/106 (from 65, 48 and 95 without asking); wrong answers 2 → 3/2/2/2, 0 → 1/1/1/1 and
1 → 1/1/1/1. Round 29 development: 100 → 101. Mean 2–2.7 questions per
answered puzzle, 2–7 % of output cells. Stored ARC: no gain (10 right, 0 wrong).

**Stage 1 on the older sets:** no change in decisions (ARC 10/0, Round 28 dev 65/2, Round 28
held-out 48/0, Round 29 held-out 95/1). **Shape pruning** gives identical decisions with fewer
expansions, e.g. 356k → 235k and 20.5 s → 14.5 s on the Round 29 held-out set.

**Occam vs. number of demonstrations k** (`pipeline_bench_C_output.txt`, `…_D_output.txt`):
development families, k = 1: gate off 62 right / 13 wrong, gate from depth 1 42 / 2; k = 2: 94 / 2
vs 75 / 1; k ≥ 3: zero wrong without a gate. Fresh families: k = 1 25 / 9 → 25 / 5 with the AUTO
gate; one wrong persists up to k ≥ 3 (`objsize-recolour-rot90`). So the gate buys safety at the
cost of right answers for k = 1, 2 only, and the AUTO setting applies it exactly there.

**Statements** (`statement_planner_output.txt`): the planner generates the LIN / AMORT frontier for
periods 2–4 (e.g. LIN p = 2: \((a, b)\) = (1,20) (2,9) (3,5) (4,4) (5,3) (6,2) on \(d \le 20\)), every
row certified sharp in Lean. Occam for statements: offsets fitted on few levels fail later
(LIN p = 2: 2/6 fail for training depth ≤ 10, none from 12; p = 3 stable only from 18; p = 4 from 16).
Against Round 27 at the same budget of 60 oracle calls: planner 42 calls, 16 survivors, 8
non-dominated (enumeration 5, repair 4), transfer to held-out levels 0/16 — the fitted statements
are tight on the data and so are as fragile as the Occam measurement predicts. `proposals.json`
feeds them to the Round 27 `--glm` plug-in.

**GLM regression** (`r30_glm_benchmark_output.txt`, after `setup_round30.sh`): unchanged (ARC
10/0, Round 28 dev 65/2, held-out 48/0, knowledge 10/10, Round 11 suite 23/23, 2/5, 2/2).

## What this does and does not say about Rule 30

Nothing here proves a prize problem. Stage 4 makes the conjecture loop a generator: it proposes
the statements that would bound the half-line runs (period-2 rung, AUDIT To Do 1) and Lean certifies
each proposed offset is the smallest one true on the computed range. A uniform proof of any LIN or
AMORT statement is still open.
