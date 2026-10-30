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

**Deciding figure.** <!--figure:registers-->8 registers<!--/figure--> of carriers, reached through <!--figure:query-kinds-->27 query kinds<!--/figure--> one of which dispatches <!--figure:report-subjects-->67 report subjects<!--/figure-->.

**Recomputed by.** `glm_universal.figures.figures`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Last altered 30 October 2026 (repository check: directives D17–D21 renumbered, constants single-source rule D21; earlier 29 October 2026 reorganisation: the repository restructured under src/, studies as YAML+MD pairs, wheels centralized, Rule30 Lean absorbed).*

This repository holds the Geometric Language Machine system and many studies that came out of developing it so far.

*Rewritten in Phase 133.* The supplied files of the owner's substrate study
had been unpacked over the repository root and had replaced this front door;
they now live in [`source_material/substrate_study/`](source_material/substrate_study/README.md),
and this file was written again from the current state documents.

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
> eight are in [`ITERATE.md`](ITERATE.md) §0.1, *Run-order hazards*):
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
of carriers reached through <!--figure:query-kinds-->27 query kinds<!--/figure-->,
one of which dispatches <!--figure:report-subjects-->67 report subjects<!--/figure-->.
The formal development is
[`src/lean/RequestProject/GLM/`](src/lean/RequestProject/GLM/README.md),
<!--figure:lean-files-->425 Lean files<!--/figure--> with no `sorry`, built
from the repository root with `lake build`.

```bash
python3 src/GLM.py -q "address of golay"                    # one query
PYTHONPATH=src python3 -m glm_universal.tools --help      # the study instruments
```

## 1b. What this round closed

Phase 160 ([`studies/FOLD_MACHINE_STUDY.md`](studies/FOLD_MACHINE_STUDY.md)),
Part II.2 of the owner's plan of 19 October 2026: the remaining carried folds.
When the planner answers *the median atomic number of the halogens*, *the rank
of iron by atomic weight among the transition metals* or *the heaviest of the
noble gases*, the batch machine GLM-BAT now recomputes the answer itself from the
readings it finds in its own copy of the register, instead of taking the
planner's value as data. It has no sort, so it counts: a reading is at a
position of the sorted column exactly when the readings below it and the
readings at most it bracket that position (proved in `FoldMachine.lean`). The
program offers a witness for each position, and the machine checks it by
counting, so a wrong witness stops the run and can never change the value.
Declared holes are checked as absences from the register. All 48 such folds
are now computed (carried steps 92 → 44), a lie at each is caught at its own
step, and no answer moved. The record of every round is
[`MASTER_PLAN.md`](MASTER_PLAN.md).

## 2. What the machine can actually do so far, measured

[`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md) reports what happened
when the machine was run, and [`REASONING_CAPABILITY.md`](REASONING_CAPABILITY.md)
asks whether it reasons. The end-to-end evaluation, the benchmark suites, the
capability probes and the test suite are listed with their commands and
current figures in [`SYSTEM.md`](SYSTEM.md) §1; refusals are stated as
boundaries, never hidden.

## 3. The supplied documents, read as claim ledgers

The material the owner supplied is in [`source_material/`](source_material/).
Each document that makes claims is restated sentence by sentence and given
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
| `` | the package `glm_universal`, the CLI `GLM.py` and the Lean development `src/lean/` |
| `studies/` | one study per question, each with its pre-registered marks and what came out |
| `source_material/` | the material the owner supplied, kept as supplied |
| `archive/` | records of earlier rounds |

## The layout in one paragraph

The state documents at the root say what the system is and what is still to
do; the studies say what each round asked and found; the package and the Lean
development are what the studies measure and prove; the supplied material is
what the rounds were drawn from.

## The figures, and why none of them is typed in

Every count in a state document that can move — registers, query kinds,
report subjects, Lean files, test files — is an inline figure rewritten by
`corpus --refresh` from the code that computes it (`glm_universal/figures.py`,
[`FIGURES.md`](FIGURES.md)), and `tests/test_figures.py`
fails if a document drifts from it.
