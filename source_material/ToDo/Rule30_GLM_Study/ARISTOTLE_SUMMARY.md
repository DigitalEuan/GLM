# Summary of changes for run 3a111adb-7c50-4dbc-af25-85f13c5b3267
**Outcome of this round: tidy-up, journey document, GLM merge, YAML preparation.** None of the three Rule 30 prize problems is solved. This round added no new theorems. It packaged, checked and corrected what earlier rounds built.

**The journey document.** `RULE30_STUDY.md` is the single entry point. It tells the story round by round, gives the best findings with their evidence class (proved, or certified on a stated range), lists the errors made and the lessons drawn from them, says what blocks each prize problem, lists the open targets, and explains how to take the next round. `README.md` maps the package. After a review, several statements were narrowed to what is actually proved:
- the degree formula \(\deg a(n)(0) = 2n-1\) holds for \(n \ge 2\); the degree is 2 at \(n = 1\);
- the top monomial is unique only for \(n \ge 3\);
- the "map-only" and "diagonal coupling" barriers show only that those facts *alone* cannot settle Problem 1;
- `SeedAPBalanced` requires every stride and every phase, and it is open even for a single stride;
- the wobble arrow's sign pattern does not decide frequency 1/2 either way;
- "weakest" became "weakest found so far".

The same corrections were made in the YAML records and the companion documents.

**Can it merge into the GLM? Yes, but so far only tested on mock copies of the GLM layout, not on your real repository.**
- The package uses the same Lean toolchain, the same Mathlib commit and the same library name as your `glm_repo.zip` snapshot.
- It has 158 Lean files and 3174 declarations, with 0 declaration clashes. The one file-name clash (`GLM/Escalation.lean`) is avoided by importing everything through `Rule30Study.lean`.
- The GLM's Lean folder would grow from 255 to 413 files.
- `tools/merge_into_glm.py` does a dry run by default and refuses to merge if any check fails. With `--apply` it copies the files and adds the import lines the GLM's axiom guard needs.
- You then run the GLM's own build, corpus refresh and sign-off gates once (`MERGE_INTO_GLM.md` §6).
- Your snapshot's `README.md`, `STATUS.md` and `SYSTEM.md` say 268 Lean files where the folder holds 255; the corpus refresh corrects this.

**YAML preparation for the next GLM project.**
- `tools/glm_study_yaml.py` converts any study document to YAML and back. Round trips are exact on 211 of your GLM documents and on 22 package documents.
- It also has validate, query and new-study commands, a study template, and 43 passing unit tests.
- The study is also stored as structured YAML in `study/` (findings, lessons, open questions, rounds, modules, claims and an index).
- Every document opens with a tier-0 summary block (21 of 21 pass the check).

**Checks.** A full build of `RequestProject` succeeds (8187 jobs) with no `sorry`. Proved files use only the standard axioms; the finite-range certificates also rely on Lean's trusted compiler. The claims ledger has 428 rows and every Lean name in it exists. The Properties table has 386 rows: 318 proved, 62 open and 6 refuted.

**Some files could not be delivered.** All work is committed in the project repository, but a fault in the file-delivery step repeatedly refused some files, even though they contain only Rule 30 mathematics, documentation and tools. Retries succeeded for some files and not others.
- **Delivered**, among others: `RULE30_STUDY.md`, `README.md`, `Rule30/README.md`, `PROJECT_DIRECTIVE.md`, `HISTORY.md`, `TEST_COUNT.md`, `HYPOTHESIS_ENGINE.md`, the three Escalation documents, 157 of 160 Lean files, all scripts, `claims.csv`, `r28_wheel.json`, `study/rule30.yaml`, `study/index.yaml`, `study/rounds.yaml`, most per-document YAML files, the study template and the unit tests.
- **Still undelivered:**
  - `MERGE_INTO_GLM.md`;
  - the tools: `glm_study_yaml.py`, `merge_into_glm.py`, `build_study_yaml.py`, `tier0_check.py`, `lean_decls.py` and `STUDY_YAML.md`;
  - the documents `AUDIT.md`, `DEVELOPMENT.md`, `TURN_COST.md`, `glm/README.md`, `HypothesisEngine/README.md` and `study/README.md`;
  - the study files `study/findings.yaml`, `lessons.yaml`, `claims.yaml`, `modules.yaml`, `open_questions.yaml` and `study_folders.yaml`, plus nine per-document YAML files;
  - the Lean files `TopMonomial.lean`, `SidewaysPeriodTwo.lean` and the standalone root `GLM.lean`. The four top-monomial results do show their statements in the Properties table.

The fault has been reported to the Harmonic team.