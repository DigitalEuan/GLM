# Summary of changes for run fef50c6a-9f92-431f-aba8-6b1139c2a1bd
**The intake items that measurably help the GLM are now part of it, absorbed ahead of your Lean build as you decided.** Your own `scripts/rebuild_lean.sh` run still has to confirm their Lean files. The project's full Lean build could not be run here: this environment has no Lean toolchain or pytest where the repository runs, and no network.

**Standalone Lean check.** The four new files in `src/lean/RequestProject/GLM/IntakeChecks/` were each built on their own with Lean 4.34 and Mathlib, using the exact files in the repository. They are `RuleThirtyBits`, `SporadicOrderCheck`, `NextTerm` and `Derivability`. They contain no `sorry` and use only Lean's standard axioms. These check mathematical facts the new answers cite; they are not proofs about the Python code itself. They have not yet been built inside your project.

**What was absorbed**
- **`Rule30_GLM_Study`:** its hypothesis engine now answers as `tool rule30`, `tool conjecture`, and as the plan search behind `tool arc`.
- **`glm_wheels_bundle`:** its formula wheels answer as `tool derive`, and the sequence wheel now answers *what comes next in …*.
- **`cent_compiler_v12`:** its cent wheels are absorbed.

All three items are recorded as "absorbed ahead of the build", and every answer that rests on them says so.

**Measured effect** (full details in `studies/INTAKE_CAPABILITY_STUDY.md` and `CAPABILITY_ASSESSMENT.md`). There were 0 wrong answers throughout, and 12 of the 14 pre-registered marks were met.

| Area | With the intake items | Without |
|---|---|---|
| ARC tasks (development set, not held-out) | 9 of 50 | 2 |
| Rule 30 battery, on the answering path | 16 of 39 | 0 |
| Next-term questions | 27 of 45 | 5 |
| Mixed questions across five domains | 23 of 30 | 4 |
| Formula laws derived | 63 of 64 | — |
| Non-laws wrongly accepted | 0 of 51 | — |

- **Missed mark R2 (Rule 30):** fewer than the target of 20 battery sentences were answered on the answering path.
- **Missed mark S2 (next terms):** 1 of 13 negative controls was answered; `1, 2, 4, 8, 16` was continued with 32.
- **Evaluation:** all 237 questions pass (187 answered, 50 refused as expected).

**Fixes made along the way**
- The engine had used Python's `random`, which the blueprint's Universal Binary Principle bans. It now uses its own exact generator, `ExactDraw`, and `report blueprint` is back to 26 confirmed claims.
- The Rule 30 `^` operation is now classified as a permitted operation.
- Recorded figures were brought up to date with the larger evaluation set and corpus: the sandbox-planner counts, the anonymous-register control bound, the iteration-cost table, and study links into `source_material/done/`.
- Every affected measurement was re-taken. The corpus check, figures check and intake check all pass.

**Tests.** pytest is not installed here, so all 260 test files were run by hand with a substitute runner. 6,521 passed, 76 were skipped and 6 fail. The six failures read the Lean citation graph, which only a passing Lean build re-creates. This hand run is not your sign-off.

**What you need to run**
1. Copy the delivered files over your checkout, then run `scripts/apply_reorganisation.sh` to clear the old copies of the two items now in `source_material/done/`.
2. Run `scripts/rebuild_lean.sh`. This also re-creates the citation graph.
3. Run `PYTHONPATH=src python3 -m glm_universal.intake confirm-build` once each for `Rule30_GLM_Study`, `cent_compiler_v12` and `glm_wheels_bundle`.
4. Run the pytest sign-off: `scripts/check_repository.sh`, then `python3 -m glm_universal.signoff --close --jobs 8`.

All changed files have been delivered, including the two items' full folders under `source_material/done/`. The work is on branch `intake-absorption`.