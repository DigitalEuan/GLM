# Rule 30 / GLM — the Lean 4 study package

## Tier 0 — the coarse read

**Question.** What is this package, where does a reader start, and how is it built and carried into the GLM?

**Verdict.** This is the Lean 4 package of the Rule 30 / GLM study: all three Wolfram Rule 30 prize problems are still open, the package holds what the study proved, certified, refuted and measured, and a reader starts with RULE30_STUDY.md.

**Deciding figure.** 3 prize problems, all open; 160 Lean files with no unfinished proof and no added axiom; 428 ledger rows.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `tools/tier0_check.py` (or the GLM's corpus check, after a merge) fails if they stop being.*

**Authors.** E. R. A. Craig — study, concept, GLM/UBP framework (project owner). Aristotle by
Harmonic — Lean 4 formalisation, verification and exact computation.

This is the Lean 4 package of the Rule 30 / GLM study. It asks Wolfram's three Rule 30 prize
questions through the owner's Geometric Language Machine (GLM) and checks every claim in Lean.
All three Wolfram Rule 30 prize problems are still open; nothing here claims otherwise. The
package holds what the study proved, certified, refuted and measured, with the evidence class of
each claim, and it is ready to be carried into the GLM repository. A reader starts with
`RULE30_STUDY.md`. The package has 160 Lean files, none with an unfinished proof or an added axiom,
and its evidence ledger `claims.csv` has 428 rows.

## Start here

| Read | For |
|---|---|
| **[`RULE30_STUDY.md`](RULE30_STUDY.md)** | **the one document to read first**: the journey (Rounds 1–49), the best findings, the map of the package, the merge into the GLM, the YAML preparation, what is open |
| [`MERGE_INTO_GLM.md`](MERGE_INTO_GLM.md) | how to merge the package into the GLM repository, and the gates to run after |
| [`study/`](study/README.md) | the study as YAML, for the GLM to read: findings, rounds, open questions, lessons, every module, the ledger, every document |
| [`tools/STUDY_YAML.md`](tools/STUDY_YAML.md) | the study YAML parser/creator for this and all future study documents |
| [`RequestProject/GLM/Rule30/README.md`](RequestProject/GLM/Rule30/README.md) | the Lean map: every file by topic |
| [`PROJECT_DIRECTIVE.md`](RequestProject/GLM/Rule30/PROJECT_DIRECTIVE.md) | the goal, the rules of evidence, what counts as progress |
| [`AUDIT.md`](RequestProject/GLM/Rule30/AUDIT.md) | the status, the missing theorems (§3), the numbered To Do list (§4) |
| [`DEVELOPMENT.md`](RequestProject/GLM/Rule30/DEVELOPMENT.md) | how to run the next round |
| [`HISTORY.md`](RequestProject/GLM/Rule30/HISTORY.md) | the detailed record of every round |

## The status in brief

* **P1** (is the centre column never eventually periodic?), **P2** (do black cells have frequency
  1/2?) and **P3** (does computing `a(n)` need effort growing with `n`?) are stated in Lean as
  `Prop`s (`Prizes.lean`, `MachineModel.lean`) and remain open.
* Proved on the way, among others: the centre column is not eventually constant; the half-line
  reduction of P1 (`problem1_of_halfLineDies`) with period 1 settled; the drive wheel
  (`halfLineDies_iff_wheel`); P1 is equivalent to the 2-adic irrationality of the centre column
  (`problem1_iff_padic_irrational`); infinitely many eventually white left diagonals; the algebraic
  degree of the centre cell is `deg a(n) = 2n − 1` for every `n ≥ 2` (`center_anfDegree_eq`). The full list with Lean names is
  `RULE30_STUDY.md` §3.
* No finite computation can settle P1 or P2 (`no_finite_certificate_problem1/2`), so every finite
  certificate here is a theorem about its stated range only.

## How the package is laid out

```
README.md                    this front door
RULE30_STUDY.md              the journey, the best findings, the map (GLM study format)
MERGE_INTO_GLM.md            the merge into the GLM repository
study/                       the study as YAML (generated and curated)
tools/                       study YAML parser/creator, YAML builder, tier-0 check, merge tool
RequestProject/GLM/Rule30Study.lean     single root: imports the whole package
RequestProject/GLM/Rule30/              the Rule 30 mathematics, guides, claims.csv, scripts/, glm/
RequestProject/GLM/HypothesisEngine/    the hypothesis engine's contracts and benchmarks
RequestProject/GLM/Escalation/          the escalation-boundaries checks
```

## Build and check

```
lake build RequestProject.GLM.Rule30Study                     # the whole package
python3 RequestProject/GLM/Rule30/scripts/ledger_check.py     # every ledger name exists; axioms match the class
python3 tools/build_study_yaml.py check                       # the YAML copy in study/ is current
python3 tools/tier0_check.py                                  # every document keeps the GLM's tier-0 contract
python3 tools/test_glm_study_yaml.py                          # tests of the study YAML tool
```

Lean 4.28.0 and Mathlib as pinned in `lean-toolchain`, `lakefile.toml` and `lake-manifest.json`.
A build from scratch takes about half an hour, most of it in the certificate files. There is no
unfinished proof and no added axiom. FORMAL results use only the standard axioms (`propext`,
`Classical.choice`, `Quot.sound`); CERT results also trust Lean's compiler (`native_decide`) and are
kept in separate `…Data.lean` files. `lake build RequestProject.GLM` builds the same package.

The round-by-round summaries that used to fill this page are in
[`HISTORY.md`](RequestProject/GLM/Rule30/HISTORY.md), Appendix D, unchanged.
