# Cent wheels — follow-ups

*Written 17 November 2026, after the transcription-drift fix and the absorption
of W26, W27 and W36–W42. Ordered by value; item 1 is the owner's to run.*

## 1. Confirm the Lean build (owner's machine) — the highest-value gap

Everything so far is a static text check (`python3 -m glm_universal.lean_check`).
No theorem in `Wheels/CentWheels.lean` has been type-checked by Lean since the
drift fix, the `sign_of` change and the nine new wheels. Run the build exactly
as follows and send back the two log files.

**On the owner's machine, from the repository root:**

1. Make sure the checkout is current:
   ```
   git fetch origin
   git checkout freebuff/ecbd4afeb79963a999b7ef9f
   git pull --ff-only
   ```
2. Check the toolchain is the pinned one (the file says `leanprover/lean4:v4.28.0`):
   ```
   cat lean-toolchain
   elan --version
   ```
3. Run the rebuild script (it fetches the Mathlib cache, builds everything,
   scans for `sorry`/`admit`, re-takes the citation graph and writes the build
   record):
   ```
   scripts/rebuild_lean.sh
   ```
   Use `scripts/rebuild_lean.sh --clean` only if the previous `.lake` folder
   looks stale.
4. Confirm the exit status is 0:
   ```
   echo "exit=$?"
   ```
   The script exits 1 if the static check, `lake build` or the `sorry` scan
   fails; the last lines of the log name the failing step.
5. Send back these two files (they are the evidence the intake gate needs):
   ```
   scripts/logs/lean_build_latest.log
   scripts/logs/lean_build_evidence.json
   ```
6. Only once step 4 is 0, record the confirmation:
   ```
   PYTHONPATH=src python3 -m glm_universal.intake confirm-build cent_compiler_v12
   ```
   That removes the item's entry from `src/glm_universal/wheels/_data/provisional.json`
   and clears the provisional note on cent-wheel answers.

**If the build fails:** send the log. The first error line names the file and
the theorem; fix the Python generator (`cent_wheels_study.lean_source`), not the
generated `.lean` by hand, then regenerate and rebuild.

## 2. Evaluate more supplied wheels for absorption

W26, W27 and W36–W42 are now absorbed (24 cent wheels). What remains is a
standing question: should a wheel outside the W16–W35 cent family be absorbed
on the same rule (at least one axiom, every axiom balanced at SI7, S2 and S5
hold, every case's flag equals span membership)? The rule is mechanical;
running it on each new delivery would replace a growing `NOT_ABSORBED` list
with per-wheel evidence. W42's `sign_of` case is the first one to exercise.

## 3. Replace the `sign_of` opaque-key hack with a primitive

`parse_monomial_q` turns `sign_of(...)` into an opaque key and `residual` skips
any key starting with `sign_of`, so W42's `snap_through_state` dimension is
never checked. A proper treatment: `sign_of` is a dimensionless wrapper whose
argument must be dimensionally consistent and whose result is dimensionless.
This would also let the Lean encoding state the fact instead of skipping it.

## 4. Recover W35's dropped axioms via corrections

W35 (electrophysiology) is the only wheel still in `NOT_ABSORBED`: both axioms
are dropped "under rule R" with no further explanation. Either name the
specific rule-R violation in `DROPPED`, or attempt a corrected absorbed form
(as was done for W21). Dropping is a loss of coverage.

## 5. Harden the absorption accounting

`test_marks_d1_d2_s1_s2_s3_s5_absorption` fails if a new supplied wheel is not
in `NOT_ABSORBED`, which is the intended forcing function but noisy during
exploration. A soft-warning mode, or an automatic classification that separates
"new domain, out of scope" from "should have been absorbed but wasn't", would
keep the check honest without blocking a round.

## 6. Keep the study and the whiteboard current

`studies/CENT_WHEELS_STUDY.md` and `WHITEBOARD.md` still describe the
15-wheel family in their prose. The numbers in
`source_material/INTAKE.yaml` were corrected this round (24 wheels, 220
theorems, 33 supplied controls, 5 supplied axioms failing at SI7); the two
documents should follow.
