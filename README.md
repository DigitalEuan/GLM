The Geometric Language Machine (GLM)

```
Authored-by: E R A Craig (DigitalEuan), New Zealand <info@digitaleuan.com>
https://github.com/DigitalEuan/GLM
30.10.26
```

# The Geometric Language Machine (GLM)

## Tier 0 — the coarse read

**Question.** What is in this repository, and where should a reader start?

**Verdict.** This repository holds the Geometric Language Machine system and many studies that came out of developing it so far.

**Deciding figure.** <!--figure:registers-->8 registers<!--/figure--> of carriers, reached through <!--figure:query-kinds-->31 query kinds<!--/figure--> one of which dispatches <!--figure:report-subjects-->67 report subjects<!--/figure-->.

**Recomputed by.** `glm_universal.figures.figures`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Last altered 31 October 2026 (repository check: directives D17–D22 — date stamps restored as D17, Wobble/Reversibility/Generate-don't-store renumbered D18–D20, constants single source D21, the intake of new material D22; `source_material/` filed into `ToDo/` and `done/`; lost modules reconstructed and marked; study manifests read as data; later the same day absorption tied to the owner's Lean build record, and the two wheel items installed in the wheels folder marked provisional until it confirms them). Earlier: 29 October 2026 reorganisation: the repository restructured under src/, studies as YAML+MD pairs, wheels centralized, Rule30 Lean absorbed.*

This repository holds the Geometric Language Machine system and many studies that came out of developing it so far.

*Rewritten in Phase 133.* The supplied files of the owner's substrate study
had been unpacked over the repository root and had replaced this front door;
they now live with the rest of the supplied material in
[`source_material/`](source_material/README.md), and this file was written again
from the current state documents.

## Where to start

1. [`ENTRY.md`](ENTRY.md) — what to read, in what order, and what may be
   skipped.
2. [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) — the Positioning section
   (what is claimed and what is not) and the standing rules.
3. [`STATUS.md`](STATUS.md) — the To-Do list; [`SYSTEM.md`](SYSTEM.md) — what
   the system is now and every instrument with its current figure.
4. [`DIGEST.md`](DIGEST.md) — every document at tier 0, on one page.
5. [`ITERATE.md`](ITERATE.md) — how a round is picked up, worked and closed.

> **Before running anything** — two notes that have cost work before (all
> nine are in [`ITERATE.md`](ITERATE.md) §0.1, *Run-order hazards*):
>
> * **Don't edit documents while `corpus --refresh` is running.** It
>   rewrites them from the copies it read when it started.
> * **Re-take order matters after editing `evaluation/cases.py`.** Some saved
>   results read others. Re-take `queryesc`, `budget-guard-frozen` and
>   `ties-ladder-frozen` first, then the rest, then refresh the corpus last.
>
> **Standing rule (directive D21):** every fundamental constant, shared path
> and pinned value is defined once, in
> [`src/glm_universal/constants.py`](src/glm_universal/constants.py), and
> imported from there ([`ITERATE.md`](ITERATE.md) §0.2).

## 1. The GLM system

The GLM is a substrate-native reasoning system built on an exact substrate:
the extended binary Golay code, the Leech lattice, and exact integer and
rational arithmetic on them — no floating point on any path that feeds a
result. The package lives in [`src/glm_universal/`](src/glm_universal/README.md) as
`glm_universal`, and holds <!--figure:registers-->8 registers<!--/figure-->
of carriers reached through <!--figure:query-kinds-->31 query kinds<!--/figure-->,
one of which dispatches <!--figure:report-subjects-->67 report subjects<!--/figure-->.
The formal development is
[`src/lean/RequestProject/GLM/`](src/lean/RequestProject/GLM/README.md),
<!--figure:lean-files-->414 Lean files<!--/figure--> with no `sorry`, built
from the repository root with `lake build`.

```bash
python3 src/GLM.py -q "address of golay"                    # one query
PYTHONPATH=src python3 -m glm_universal.tools --help      # the study instruments
```

## 1b. What this round closed

The repository check of 31 October 2026 put the repository back together after the October
reorganisation and the arrival of new supplied material (the full record is in
[`STATUS.md`](STATUS.md) §1b and [`MASTER_PLAN.md`](MASTER_PLAN.md)):

* **Lost parts reconstructed or recorded.** Python modules lost in the reorganisation
  (for example `runtime/respell.py`, `runtime/sinter.py`, `reasoning/carried_read.py`,
  `reasoning/planner_ladder.py`, `reasoning/hole_reports_l5.py`, `corpus/dates.py`) were
  rebuilt from their studies and tests; each says *Reconstructed 31 October 2026* in its
  docstring. Lean files that existed only as placeholders are recorded as missing in
  [`studies/_lean_files_needed.md`](studies/_lean_files_needed.md), and the files that
  import them wait in `src/lean/awaiting_recovery/`, out of the build.
* **Studies as data.** Every study has a validated YAML manifest; the GLM answers `study`
  questions from them, and `glm_universal.corpus.study_manifest`, `study_index` and
  `study_links` keep the manifests, the index and the links honest.
* **New material has a way in.** The owner's material goes into `source_material/ToDo/`
  and is taken through the intake (directive D22,
  [`source_material/README.md`](source_material/README.md)) to a Lean-verified, measured
  stage before anything is absorbed — Lean verified meaning that the owner's build record
  matches the item's Lean files — and finished items are filed in `source_material/done/`.
* **Two owner-run scripts** — `scripts/rebuild_lean.sh` (rebuilds `.lake` and runs the
  axiom audit) and `scripts/check_repository.sh` (every Python gate) — write their logs to
  `scripts/logs/` for the next round to read, since `lake build` could not be run here; each
  exits 1 when a required step fails and 0 only when every step passes.

## 2. What the machine can actually do so far, measured

[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md) reports what happened
when the machine was run, and [`REASONING_CAPABILITY.md`](REASONING_CAPABILITY.md)
asks whether it reasons. The end-to-end evaluation, the benchmark suites, the
capability probes and the test suite are listed with their commands and
current figures in [`SYSTEM.md`](SYSTEM.md) §1; refusals are stated as
boundaries, never hidden.

## 3. The supplied material, and the intake

The material the owner supplies goes into [`source_material/`](source_material/README.md):
`ToDo/` holds what is still being taken in, `done/` what has been absorbed or closed, and
`INTAKE.yaml` is the ledger of every item and its stage. An item is absorbed into the
package only after it has a study, has been tested, has its Lean written and then verified
by a passing build (the record `scripts/rebuild_lean.sh` writes, matched against the item's
Lean files and everything they import) and has been measured to help the GLM (directive D22;
the pipeline itself is [`studies/INTAKE_PIPELINE_STUDY.md`](studies/INTAKE_PIPELINE_STUDY.md)).
The two wheel items of the repository check — the Integer and Monster wheels
(`glm_wheels_bundle`) and fifteen cent formula wheels (`cent_compiler_v12`) — are tested and
measured, and by the owner's decision are already in the one wheels folder,
`src/glm_universal/wheels/`, **marked provisional** until that build confirms them: the GLM
answers from them, and every such answer says it rests on a provisional wheel.

```bash
PYTHONPATH=src python3 -m glm_universal.intake status
```

Each supplied document that makes claims is restated sentence by sentence and given
verdicts — for example
[`studies/GLM_UNIFICATION_BLUEPRINT_AUDIT.md`](studies/GLM_UNIFICATION_BLUEPRINT_AUDIT.md)
and [`studies/GLM_STUDY_CATALOG_AUDIT.md`](studies/GLM_STUDY_CATALOG_AUDIT.md)
— and Appendix C of
[`studies/GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md) says, part by
part, what has been brought in and what is still left.

## 4. Checking it without checking it twice

Every test file and instrument is signed against a digest of everything it
reads; `signoff --verify` re-checks the signatures without running anything,
and a round's close runs only what moved.

```bash
PYTHONPATH=src python3 -m glm_universal.corpus --check
PYTHONPATH=src python3 -m glm_universal.signoff --verify
```

## 5. The documents are data too

Every current-state document opens with a tier-0 block, the generated
[`DIGEST.md`](DIGEST.md) collects them, and `corpus --check` fails if a verdict
stops being grounded in its document or a link breaks.
`corpus --ask "…"` returns the sections that bear on a question.

## Layout

| path | what |
|---|---|
| `src/` | the package `glm_universal` (`src/glm_universal/`), the CLI `src/GLM.py` and the Lean development `src/lean/` |
| `src/glm_universal/wheels/` | the one wheels folder: every wheel the GLM uses, once it has passed the intake |
| `studies/` | one study per question (`.md`) with its manifest (`.yaml`), its pre-registered marks and what came out |
| `source_material/` | the material the owner supplied: `ToDo/`, `done/` and the `INTAKE.yaml` ledger |
| `scripts/` | the two owner-run scripts and their logs (`scripts/logs/`) |
| `archive/` | records of earlier rounds |

Every command in these documents is run from the repository root, with `PYTHONPATH=src`
for the package (`src/GLM.py` adds it itself).

## The layout in one paragraph

The state documents at the root say what the system is and what is still to
do; the studies say what each round asked and found; the package and the Lean
development are what the studies measure and prove; the supplied material is
what the rounds were drawn from.

## The figures, and why none of them is typed in

Every count in a state document that can move — registers, query kinds,
report subjects, Lean files, test files — is an inline figure rewritten by
`corpus --refresh` from the code that computes it (`src/glm_universal/figures.py`,
[`FIGURES.md`](FIGURES.md)), and `src/glm_universal/tests/test_figures.py`
fails if a document drifts from it.
