# source_material/ToDo — items whose intake is open

*Created 31 October 2026 (repository check; directive D22).*
*Last altered 1 November 2026 (Phase 186): `glm_wheels_bundle` and `Rule30_GLM_Study` absorbed ahead of the owner's build and filed in `done/`; `cent_compiler_v12` absorbed partially ahead of the build and kept here for its open parts; the snapshot re-taken from the ledger. Before that, 31 October 2026: the Lean written stage; the two wheel items back here with their code staged until the owner's Lean build; the snapshot re-taken from the ledger; then the two wheel items' code installed provisionally in the wheels folder by the owner's decision.*

Every item here has a record in [`../INTAKE.yaml`](../INTAKE.yaml) and moves
along received → triaged → study drafted → tested → Lean written → Lean
verified → measured → absorbed, or is closed with a reason; either way it then
moves to [`../done/`](../done/README.md). *Lean verified* needs the owner's
build record (`scripts/rebuild_lean.sh`). See [`../README.md`](../README.md)
for the gates and the commands. The ledger is authoritative:

```
PYTHONPATH=src python3 -m glm_universal.intake status
PYTHONPATH=src python3 -m glm_universal.intake show <id>
```

An item may hold a `staged/` folder: code ported and tested for the package
that waits there until absorption installs it. By the owner's decision such
code can instead be installed ahead of the build, marked *provisional*
(`intake provisional <id>`; see [`../README.md`](../README.md)); the item stays
here, at its stage, until absorption confirms it.  The owner may also decide to absorb an
item ahead of the build (`intake absorb-ahead <id>`): it is then filed in
`done/` unless a part is still open, and `intake confirm-build <id>` records
the build's confirmation later.

Snapshot of 1 November 2026 (8 items):

| item | stage | what is open, and the next step |
|---|---|---|
| `cent_compiler_v12` | Lean written | the fifteen formula wheels and `tool derive` (package tests `test_cent_wheels.py` 36 and `test_derive_query.py` 9; `CENT_WHEELS_STUDY`: 63 of 64 laws, 0 of 51 not-a-laws; `INTAKE_CAPABILITY_STUDY`, mark D1) were **absorbed ahead of the build** by the owner's decision of 1 November 2026; after the owner's build, `confirm-build cent_compiler_v12`; the compiler, SPICE emission, application proposals and notes stay open — measure them or close them |
| `attention` | tested | the simulator and the bench are sandbox modules; `attention_report` re-runs and every agreement check holds; next, Lean for its finite claims |
| `conversation_experiment` | study drafted | all 8 scripts run; tests to be named for the two open parts (the measurements `CONVERSATION_STUDY` declares) |
| `formula_wheel` | study drafted | 02 runs (41 of 41); 06 and 08 need two modules that were not supplied; the blind ranking of the candidate table is open |
| `glm_vision_experiments_v14.py` | triaged | fails against the current package API (`Meaning.calendar_day`); port it, or close it if `reasoning/vision_stack.py` already carries what it offers |
| `hidden_memory` | triaged | a concept note; its study (memory on against memory off, with controls) is to be drafted |
| `GLM_IMPROVEMENT_ROADMAP.md` | triaged | P1–P2 taken; P0 and P3–P7 open |
| `HISTORY_RECORDED_NOW_V4_STUDY.md` | triaged | the differential tax is reproduced; the query-loop integration and the 32D/48D escalation are open |
