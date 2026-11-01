# source_material/done — items whose intake is finished

*Created 31 October 2026 (repository check; directive D22).*
*Last altered 1 November 2026 (Phase 186): `glm_wheels_bundle` and `Rule30_GLM_Study` filed here, absorbed ahead of the owner's build by the owner's decision; the snapshot re-taken. Before that, 31 October 2026: the snapshot re-taken (`R_Calculus` closed); the absorbed items' build record explained.*

An item is filed here when its intake is finished: **absorbed** (every gate's
evidence exists — a study, tests that pass, Lean files in the build and the
axiom audit verified by a passing build, a measured deciding figure, and the
modules it became, with tests) or **closed** with a recorded reason and evidence that exists. Each has
a record in [`../INTAKE.yaml`](../INTAKE.yaml) naming the studies, tests, Lean
files and modules; `python3 -m glm_universal.intake check` re-checks that the
evidence still exists. Items keep their layout byte-identical; code that still
reads one (the ARC-era state, the Question Set B texts, the pipeline kit, the
law register's sources) finds it through
`glm_universal.constants.source_material_item`.

Snapshot of 1 November 2026: 36 records, 23 absorbed and 13 closed. Two of
the absorbed items, `glm_wheels_bundle` and `Rule30_GLM_Study`, were
**absorbed ahead of the build** on 1 November 2026 by the owner's decision,
on the measurements of `INTAKE_CAPABILITY_STUDY` (and `INTEGER_WHEEL_STUDY`)
and a standalone Lean check: every answer that rests on them says that the
owner's `scripts/rebuild_lean.sh` has still to confirm their Lean files, and
`intake confirm-build <id>` records that confirmation. The other 21
absorbed items were absorbed by earlier rounds whose Lean was built then,
before the intake's build record existed; each record's `lean_build` says so.
The reorganised tree has not been rebuilt since, so the first passing
`scripts/rebuild_lean.sh` re-checks them, and `intake check` then warns on any
of their Lean files that no longer matches the record.

* **Absorbed ahead of the build** — `glm_wheels_bundle` (INTEGER_WHEEL_STUDY
  and INTAKE_CAPABILITY_STUDY: the Integer and Monster wheels and the sequence
  wheel's `next` reading) and `Rule30_GLM_Study` (INTAKE_CAPABILITY_STUDY and
  RULE30_HYPOTHESIS_ENGINE: the hypothesis engine, `tool rule30`, `tool
  conjecture` and the plan search behind `tool arc`).
* **Absorbed** — `devops_ladder` (OPERATIONS_LADDER_STUDY), `GLM_Pipeline_Kit`
  (PIPELINE_KIT_STUDY), the four history-in-the-now files (NOW_RECEIPT_STUDY),
  the three PCGS files (PCGS_STUDY), `substrate_study`
  (DESIGNED_SUBSTRATE_STUDY), `Golay codes and Hadamard matrices.txt`
  (CONSTRUCTION_LADDER_STUDY), `UBP_LAW_GLM_REVIEW.md` and
  `retained_laws_verified_65.csv` (LAW_REGISTER, LAW_TRIAGE and
  LAW_ABSORPTION studies), the two Question Set B texts (QUESTION_SET_B_STUDY),
  `substrate_native_cognitive_1.txt` (SUBSTRATE_NATIVE_COGNITION_STUDY),
  `iter10_lorentzian.py` (LORENTZIAN_LIFT_STUDY), the three infinite-values
  notes (INFINITE_VALUES_STUDY) and `glm_zero_storage_substrate_v3.txt`
  (ZERO_STORAGE and ZERO_STORAGE_V5 studies).
* **Closed** — `R_Calculus` (continued as the hypothesis engine of
  `Rule30_GLM_Study`), `GLM_19OCT26_1.md` and `ToDo_01.txt` (plans whose every part
  was taken), the reverse-call planner pair (studied, not promoted),
  `arc_agi_17` (data read in place), the three `*_condensed.txt` files
  (byte-identical copies of the kit's own), the study-findings catalogue and
  the unification blueprint (audited), and the local-only `GLM-main.zip` and
  `Lorentz boosts.pdf`, which are not in this checkout.
