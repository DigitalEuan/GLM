# How much of the GLM in `glm_repo.zip` can run here

`ENTRY.md` and `SYSTEM.md` describe a GLM with a connected command line (`GLM.py --ask`), a
toolbox (`tool induce`, `tool arc`, `tool frame`, …), domain wheels, an evaluation harness and a
test suite of about 5,400 tests. The archive supplied with this project holds an older or partial
tree.

Setup used for this count:
* your `parser.py`, `session.py`, `tct_engine.py`, `__init__.py` and `lattice_geometry.py`;
* the Round 9 stand-in for `reasoning/frozen_path.py`;
* the Round 9 and Round 10 overlays.

With all of that in place, **22 modules that the code imports are not in the archive**.
`find_missing_modules.py` lists them by a static scan; run it on your full checkout to confirm that
it reports 0 there.

| Missing module | Imported by (count) | What stops without it |
|---|---|---|
| `runtime/respell`, `runtime/sinter` | `GLM.py` | `GLM.py -q …` (batch mode) fails on import |
| `engineering/speak` | 6 files, incl. `engineering/__init__.py`, `runtime/router.py` | `GLM.py --ask …` (the connected path) fails on import |
| `runtime/stepwise` | 30 files, incl. `GLM.py` | the stepwise planner, the certificate and tool-value evaluations |
| `runtime/semantic_plan` | 9 | typed plans, declared frames, quantity units |
| `runtime/evidence` | 4, incl. `GLM.py` | the common result model (`--result`) |
| `reasoning/colour_induction` | `runtime/toolbox.py` | **`tool induce` and `tool arc`**: `_induce` imports it before anything else |
| `reasoning/llvq` | 3, incl. `runtime/toolbox.py` | the LLVQ tools |
| `reasoning/nearest_address`, `nearest_address_study`, `nearest_question_study` | 5 | nearest-address reading |
| `reasoning/batch_machine` | 14 | the batch machine and its studies |
| `reasoning/timed_question` | 7, incl. `GLM.py` | `--converse` timing |
| `reasoning/planner_ladder` | 2, incl. `GLM.py` | the planner ladder |
| `reasoning/budget_guard_frozen`, `carried_read`, `combiner`, `frame_plane_study`, `adversarial_dialogue_study` | 1–3 each | the corresponding studies and tests |
| `evaluation/harness` | 7 | `python3 -m glm_universal.evaluation` |
| `glm_universal.knowledge` (package) | 4 | the knowledge model |
| `glm_universal.tools` (package) | 4 tests | `python3 -m glm_universal.tools …` (every instrument command in `SYSTEM.md` §1) |

The in-process session (`glm_universal.runtime.session.GeometricSession`) **does run**. So do
`describe`, `compare`, `real`, `report`, all registers (including `automata`) and the
reports. Everything in Rounds 9 and 10 is reached through it. `pytest` is not installed in this
environment, so the GLM test suite was not run.

What would bring the full machine online: copy the 22 modules above from your working GLM tree
into this checkout (or send a complete archive), then run your gates as `ENTRY.md` describes:
`corpus --check`, `signoff --verify` and the test suite. Then apply `toolbox_wheel_induction.patch`
so that `tool induce` also reads the wheel family.
