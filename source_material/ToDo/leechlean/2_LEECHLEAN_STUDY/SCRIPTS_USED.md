# The round's persisted scripts (all under /home/z/my-project/scripts/)
- `gen_leechlean_intake_checks.py` -- emits the Lean literal data (codebook slice, tick stream, codeword list) from the item's bundled data
- `gen_leech_lean_core.py` -- derives reasoning/_data/leech_lean_core.json.gz from the item's library_core.npz (pure JSON so the package needs no numpy)
- `scratch_view_run.py` -- builds the intake scratch view with the staged files and runs a command inside it (how the staged tests were iterated)
- `finalize_leechlean_fast.py` -- finalised the study text, synced the manifest, updated the intake record (the fast durable state)
- `complete_leechlean_intake.py` -- the full closing chain, in order: (0) verify both Lean files compiled standalone, (1) study + manifest, (2) record, (3) `retest leechlean --stale` -> `advance leechlean lean_written --no-run` -> `accept` (criterion/result quoted from the study, marks I1-I3) -> `absorb-ahead` (owner's decision, the two Lean files as standalone checks). Logs to /tmp/leechlean_complete.log.
- `extract_lean_tc.py` -- unpacked the pinned toolchain leanprover/lean4:v4.28.0 (at /home/z/my-project/lean-toolchain/) without zstd

## To continue from the saved files
1. Finish the codec standalone compile (the only open Lean step):
   `lean -o <dir>/RequestProject/GLM/IntakeChecks/LeechLeanGolay.olean <repo>/src/lean/RequestProject/GLM/IntakeChecks/LeechLeanGolay.lean`
   `LEAN_PATH=<dir> lean <repo>/src/lean/RequestProject/GLM/IntakeChecks/LeechLeanCodec.lean`  (run alone; the decide-heavy file needs ~3 GB)
2. Then `cd /home/z/my-project/repo && PYTHONPATH=src python3 /home/z/my-project/scripts/complete_leechlean_intake.py`
   (it re-checks the compile log, re-runs every named test, and drives accept + absorb-ahead to retention).
3. Close the round: `PYTHONPATH=src python3 -m glm_universal.corpus --refresh`, then the touched package tests (test_figures, test_connected_two, the three new test files).
