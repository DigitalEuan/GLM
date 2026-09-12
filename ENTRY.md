# Entry — what to read, in what order, and what may safely be skipped

## Tier 0 — the coarse read

**Question.** Which documents describe this system as it is now, and what may a session leave unread without missing anything?

**Verdict.** These documents describe the system as it is; everything else is a record of a round, or a study detail reachable from them.

**Deciding figure.** Every current-state document is reachable from here, no archive document is reachable through them, and every archive document is listed below.

**Recomputed by.** `glm_universal.corpus.checks.reachability_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

This file is the one hand-written entry point. It makes a claim about
**coverage**, and the claim is tested rather than asserted: these documents
describe the system as it is; everything else is a record of a round, or a
study detail reachable from them. `glm_universal.corpus.checks` walks the links
from here and fails if a current-state document cannot be reached, if a link
points at a file that does not exist, or if an archived document has been left
off the list at the end.

Three rules make a large corpus safe to read in part.

**Tier 0 first.** Every current-state document opens with a tier-0 block: the
question, the verdict, the one figure that decides it, and the function that
recomputes that figure. [`DIGEST.md`](DIGEST.md) is all of them on one page,
generated, so it cannot drift from the documents it summarises. Reading the
digest and stopping is a *coarse* reading of the whole project, not a wrong
one: nothing below a tier 0 may contradict it, and a test enforces that.

**Descend only where the task lives.** Below tier 0 a document states its
claims and the measurements behind them; below that it gives the argument, the
controls and the negative results. Buying resolution is reading further down
one document, not reading more documents.

**Archive by rule, not by judgement.** A document is a record of a round
exactly when its name ends `_ARCHIVE.md`, when it is the session working note,
or when it lives under a directory named `archive`. Nothing in the archive is
needed to understand the state now, and nothing in it has been deleted.

## Read in this order

1. [`PROJECT_DIRECTIVES.md`](PROJECT_DIRECTIVES.md) — the standing rules,
   the instrument that enforces each, and the Positioning section that opens
   it: what is being claimed and what is not. Read the positioning first;
   everything else assumes it has been read.
2. [`DIGEST.md`](DIGEST.md) — the whole corpus at tier 0, one row per document.
3. [`README.md`](README.md) — the repository's front door: what the system is,
   and what has been built.
4. [`STATUS.md`](STATUS.md) — where the work stands, what is open, and how to
   re-verify it.
5. [`CAPABILITY_ASSESSMENT.md`](CAPABILITY_ASSESSMENT.md) — what the machine
   can do, measured rather than described.
6. [`MASTER_PLAN.md`](MASTER_PLAN.md) — the phases, what each delivered, and
   where the next round starts.

Then, as the task requires:

* the package — [`overlay/README.md`](overlay/README.md) and
  [`overlay/glm_universal/README.md`](overlay/glm_universal/README.md), which
  reach every sub-package README;
* the formal development —
  [`overlay/glm_lean/RequestProject/GLM/README.md`](overlay/glm_lean/RequestProject/GLM/README.md);
* the generated figures — [`overlay/FIGURES.md`](overlay/FIGURES.md);
* whether the machine reasons —
  [`overlay/REASONING_CAPABILITY.md`](overlay/REASONING_CAPABILITY.md);
* the studies, listed below.

## Finding the part that bears on a question

Two instruments, and the division of labour between them is measured rather
than assumed (`studies/CORPUS_ADDRESS_STUDY.md`).

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --ask "what bears on the Golay code?"
```

returns a shortlist of sections that is **complete up to a stated radius** —
every section whose feature vector is within that radius of the question is in
the list, by `GLM.Retrieval.complete_shortlist` — with the ranking inside the
list done lexically, because that is what retrieves. An empty shortlist is a
proof that the corpus holds nothing within the radius, which is the property
that makes it safe not to read the rest.

## The studies

Each one is a question, a verdict and the measurements behind it. The one-line
form of every row here is generated into [`DIGEST.md`](DIGEST.md); read that
first and descend into the few that bear on the task.

**The substrate, and what it costs.**
[`ZERO_STORAGE_STUDY.md`](studies/ZERO_STORAGE_STUDY.md) ·
[`ZERO_STORAGE_V5_STUDY.md`](studies/ZERO_STORAGE_V5_STUDY.md) ·
[`PCGS_STUDY.md`](studies/PCGS_STUDY.md) ·
[`COMBINER_STUDY.md`](studies/COMBINER_STUDY.md) ·
[`LLVQ_TABLE_STUDY.md`](studies/LLVQ_TABLE_STUDY.md) ·
[`TIE_BREAK_STUDY.md`](studies/TIE_BREAK_STUDY.md) ·
[`HIGHER_LATTICE_STUDY.md`](studies/HIGHER_LATTICE_STUDY.md) ·
[`GEOMETRIC_AMBIGUITY_STUDY.md`](studies/GEOMETRIC_AMBIGUITY_STUDY.md) ·
[`NOISE_EXPERIMENT_STUDY.md`](studies/NOISE_EXPERIMENT_STUDY.md)

**Layers, loss and escalation.**
[`INFORMATION_LOSS_STUDY.md`](studies/INFORMATION_LOSS_STUDY.md) ·
[`ESCALATION_STUDY.md`](studies/ESCALATION_STUDY.md) ·
[`CUMULATIVITY_STUDY.md`](studies/CUMULATIVITY_STUDY.md) ·
[`QUERY_ESCALATION_STUDY.md`](studies/QUERY_ESCALATION_STUDY.md) ·
[`REVIEW_SWEEP_STUDY.md`](studies/REVIEW_SWEEP_STUDY.md) ·
[`NAME_COORDINATE_STUDY.md`](studies/NAME_COORDINATE_STUDY.md) ·
[`INFINITE_VALUES_STUDY.md`](studies/INFINITE_VALUES_STUDY.md)

**Addressing, retrieval and the corpus itself.**
[`LEAN_ADDRESS_STUDY.md`](studies/LEAN_ADDRESS_STUDY.md) ·
[`ADDRESS_RETRIEVAL_STUDY.md`](studies/ADDRESS_RETRIEVAL_STUDY.md) ·
[`CORPUS_ADDRESS_STUDY.md`](studies/CORPUS_ADDRESS_STUDY.md) ·
[`ITERATION_COST_STUDY.md`](studies/ITERATION_COST_STUDY.md) ·
[`HEXCOLOUR_STUDY.md`](studies/HEXCOLOUR_STUDY.md) ·
[`SEARCH_LOOP_STUDY.md`](studies/SEARCH_LOOP_STUDY.md) ·
[`CONTROLLER_STUDY.md`](studies/CONTROLLER_STUDY.md)

**Meaning, measure and language.**
[`DENOTATION_STUDY.md`](studies/DENOTATION_STUDY.md) ·
[`VAGUENESS_STUDY.md`](studies/VAGUENESS_STUDY.md) ·
[`CONJUGATE_STUDY.md`](studies/CONJUGATE_STUDY.md) ·
[`ADMISSION_STUDY.md`](studies/ADMISSION_STUDY.md) ·
[`RELATIVE_MEASURE_PROPOSAL.md`](studies/RELATIVE_MEASURE_PROPOSAL.md) ·
[`RELATIVE_MEASURE_STUDY.md`](studies/RELATIVE_MEASURE_STUDY.md) ·
[`ANALOGY_LAYER_STUDY.md`](studies/ANALOGY_LAYER_STUDY.md) ·
[`LANGUAGE_STUDY.md`](studies/LANGUAGE_STUDY.md) ·
[`RECIPE_STUDY.md`](studies/RECIPE_STUDY.md)

**Registers and the universality claim.**
[`HARMONY_STUDY.md`](studies/HARMONY_STUDY.md) ·
[`ECONOMICS_STUDY.md`](studies/ECONOMICS_STUDY.md) ·
[`ELEMENT_COMPLETION_STUDY.md`](studies/ELEMENT_COMPLETION_STUDY.md)

**Constants, and what a signature is worth.**
[`WOBBLE_LANDSCAPE_STUDY.md`](studies/WOBBLE_LANDSCAPE_STUDY.md)

**Geometry classified rather than looked up.**
[`DEEP_HOLE_STUDY.md`](studies/DEEP_HOLE_STUDY.md) ·
[`DEEP_HOLE_ESCALATION_STUDY.md`](studies/DEEP_HOLE_ESCALATION_STUDY.md) ·
[`DEEP_HOLE_FAILURE_STUDY.md`](studies/DEEP_HOLE_FAILURE_STUDY.md)

**Tried in the sandbox, not shipped.**
[`REVERSE_CALL_PLANNER_STUDY.md`](studies/REVERSE_CALL_PLANNER_STUDY.md)

**The supplied material, audited.**
[`GLM_STUDY_CATALOG_AUDIT.md`](studies/GLM_STUDY_CATALOG_AUDIT.md) ·
[`GLM_UNIFICATION_BLUEPRINT_AUDIT.md`](studies/GLM_UNIFICATION_BLUEPRINT_AUDIT.md) ·
[`GLM_COMPANION_STUDIES_AUDIT.md`](studies/GLM_COMPANION_STUDIES_AUDIT.md) ·
[`RETRIEVED_LEAN_STUDY.md`](studies/RETRIEVED_LEAN_STUDY.md) ·
[`SOURCE_SALVAGE_AUDIT.md`](studies/SOURCE_SALVAGE_AUDIT.md) ·
[`SOURCE_SALVAGE_SECOND_PASS.md`](studies/SOURCE_SALVAGE_SECOND_PASS.md) ·
[`ARCHIVE_DEEP_DIVE_STUDY.md`](studies/ARCHIVE_DEEP_DIVE_STUDY.md)

**Written up as papers.**
[`GLM_ACADEMIC_PAPER.md`](studies/GLM_ACADEMIC_PAPER.md) ·
[`GLM_Complete_Number_Theory_Evidence.md`](studies/GLM_Complete_Number_Theory_Evidence.md)

## Archive — records of a round, not the state now

Nothing here is needed to understand the system as it is, and nothing here has
been deleted. Each file is listed so that "I need not read it" is a decision
made against a list rather than a hope.

* [`archive/MASTER_PLAN_ARCHIVE.md`](archive/MASTER_PLAN_ARCHIVE.md) — the
  closed phases, as they were written.
* [`archive/PACKAGE_README_ARCHIVE.md`](archive/PACKAGE_README_ARCHIVE.md) —
  the package change log, row by row.
* [`ARISTOTLE_SUMMARY.md`](ARISTOTLE_SUMMARY.md) — the working notes left by
  the sessions that built this repository.
* `source_material/` — what was supplied rather than written here, kept exactly
  as received.

The first two now sit under `archive/`, which is one of the three ways the
archive rule recognises a record of a round; they were `MASTER_PLAN_ARCHIVE.md`
at the root and `overlay/README_ARCHIVE.md` beside the package README until
they were gathered here.

Two compressed archives that used to sit at the repository root have been
removed, each after checking file by file that it held nothing the tree does
not. `dropped.zip` was the recovery bundle of Phase 26: all 33 of its files are
present here, 23 byte-identical and 10 in the re-verified or extended form the
restoring round left (`CubeStabiliser.lean` and `CubeSurface.lean` as
`RequestProject/GLM/Cube/Stabiliser.lean` and `Surface.lean`).
`output-final_aristotle.zip` was a 31 MB snapshot of this same repository taken
at the end of an earlier round: all 392 of its source files exist here, bar
`PROJECT_README.md`, which was a byte-identical copy of
[`README.md`](README.md), and `DOCUMENTS.md`, which this file and
[`DIGEST.md`](DIGEST.md) replace. Both remain in the git history and in the
backups the archives were kept against. Archive material is kept unpacked from
now on: a compressed archive is material a reader cannot search.

## What keeps this file honest

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.corpus --check
```

fails if a current-state document is unreachable from here, if an archive
document is missing from the list above, if a link points at nothing, if a
tier-0 verdict says something its document does not, or if a generated
document or a generated block has drifted from a fresh rendering.
