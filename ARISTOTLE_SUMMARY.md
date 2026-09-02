# Summary of changes for run a8eb1ba5-cd98-4fb7-8a9f-769aa2848b27
I finished the round that had been left open (the LLVQ lookup-table work) and brought the whole project back to a fully signed-off, self-consistent state.

**What was outstanding and is now done**

1. *Sign-off run.* The release runner could not previously record new suite totals — the ledger only recorded them when *every* unit passed, including the document check, which by construction fails whenever a round adds a test file. That deadlock was fixed (the condition is now over the counted units, i.e. the suite minus the document check, with a docstring explaining why), and a new `TestTheRecordedTotals` class in `overlay/glm_universal/tests/test_signoff.py` pins the behaviour.

2. *Figures regenerated and propagated.* `overlay/FIGURES.md` was regenerated; the new suite sentence — **2,872 tests across 61 of the 62 test files, 11,665 subtests, outside the document check** — and version **v1.14.0** were propagated into `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, `overlay/README.md`, `overlay/glm_universal/README.md` and `overlay/glm_universal/tests/README.md`. Residual stale numbers (a `2,746` paragraph in `STATUS.md`, three `v1.13.0` headers) were corrected.

3. *Drift guard extended.* The retired phrases of this round (`47 report subjects`, `61 test files`, `46`/`47 Lean files`, `130 cases`/`130 CLI cases`/`130-case`, `2,847 tests`, `10,985 subtests`, `96 modules`, `48 reasoning modules`) were added to the superseded list in `overlay/glm_universal/tests/test_figures.py`, after confirming no document still contains them.

**Verification performed (all green)**

- Full suite in one process: **2,874 passed, 26 skipped, 13,523 subtests, zero failures**.
- Release sign-off: **62 of 62 test units and 7 of 7 instruments signed off** — `lake build`, the sorry scan, the two-copy Lean diff, the capability probes, the benchmarks, the end-to-end evaluation and the figures check.
- End-to-end CLI evaluation **131 / 131** (115 answered, 16 expected boundary refusals).
- `lake build` clean; no `sorry` or `admit` anywhere in `RequestProject`; repository and overlay Lean copies identical.
- `report llvq --verify-tct` returns `VERIFIED True`.
- The five Lean results of `RequestProject/GLM/LLVQTable.lean` registered in the properties table (the cost identity, the two class-minimum theorems, the class-size count and the branch-and-bound exactness lemma) were checked with `#print axioms` and depend only on `propext`, `Classical.choice` and `Quot.sound`; they are now marked proved.

All work is committed and pushed. `ARISTOTLE_SUMMARY.md` was read but not modified.


# Summary of changes for run 2865a776-df6d-4d42-b4ef-b902a5ce2e1f
The remaining documentation-reconciliation and verification tail is finished, and everything below was checked by running it here. All work is committed and pushed.

**1. Test-count figures propagated.** The per-file table and totals in the test-suite README were already current at 54 files / 2,424 tests; the same counts now appear in `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, the package README (`overlay/glm_universal/README.md`) and the overlay README (`overlay/README.md`). Two evaluation-set figures that had been left behind were corrected with them: the "104 CLI cases" comment in `STATUS.md` and the `test_evaluation.py` row in the tests README, both now 112.

**2. The staleness guard widened.** `overlay/glm_universal/tests/test_figures.py` now also refuses `42 report subjects`, `38 Lean files`, `52 test files`, `104 cases`, `104 CLI cases`, `104-case`, `2,350 tests`, `2,350 collected tests` and the retired subtest totals (`9,088`, `9,165`, `9,170`, `9,232`). Each phrase names the unit it counts, so the still-true `104 collision classes` is untouched — I checked that the guard passes with that phrase in place.

**3. A drift the full run exposed, and fixed.** The suite's corpus check failed: the Lean development has grown to **966 declarations across 39 files** (`MeasureView.lean` contributed 40 of its own), while four documents still described the 926-declaration corpus. `studies/LEAN_ADDRESS_STUDY.md` was re-measured against the code, not patched by hand — the kind table (623 theorems, 233 defs, 84 lemmas, 8 abbrevs, 8 structures, 5 inductives, 5 instances), `966 parsed, 0 duplicates`, read-back 966/966 with 0 coordinate errors out of 23,184 and worst residual 3 at `GLM.CoherenceRegime`, 899 distinct addresses in 57 collision classes (48 pairs, 8 triples, one class of four) covering 124 declarations, and the separation tests: nearest-by-address shares a file 343/966 (35.5 %) against 28 for the digest control and 21 for the seeded reshuffle, chance `1996/66585 ≈ 3.00 %`; cited either way 76/966 (7.87 %) against 11 and 1, chance ≈ 0.57 %; mean squared distances 5,399.2 within a file against 6,534.3 across, ratio 0.826. The scale sweep and all four §8 examples were recomputed and were unchanged. `STATUS.md`, both READMEs and the tests README now quote the same corpus.

**4. A v5.12 changelog row** was added to `overlay/README_ARCHIVE.md`, following the established practice: the measure-word round (comparison-class register, the measured widening, the `measure` query and its forced refusals, `MeasureView.lean`) together with this reconciliation and the figures it was checked against.

**5. Full verification.**

| instrument | result |
|---|---|
| test suite | **2,424 tests across 54 test files, 10,782 subtests, zero failures** |
| end-to-end CLI evaluation | **112 / 112** — 100 answered, 12 refused as expected (all boundary, 0 gap), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| Lean development | `lake build` completes cleanly; **no `sorry`**, and the repository tree and its overlay mirror are byte-identical |
| figures | `figures --write` is a no-op — `FIGURES.md` already matches a fresh computation |
| reports | `report lean`, `report measure`, `report escalation` each `VERIFIED True` under `--verify-tct` |

The subtest total moved from the 9,232 the documents quoted to 10,782; the earlier figure predated the two test files added last round, and the guard now blocks its return.

**Properties table.** The five `MeasureView.lean` properties left open last round are now marked proved — each was re-checked against a clean, `sorry`-free build and depends only on Lean's standard axioms (`propext`, `Classical.choice`, `Quot.sound`). The definition they are stated in terms of remains a definition entry.


# Summary of changes for run bba72c13-d2ef-4e24-be71-f1d7407c1ed8
All the outstanding items are done, verified by running them, and committed and pushed.

**1. The three stale "849-declaration" statements, corrected.** Each now quotes the corpus as it actually is, measured here (861 declarations across 36 files, after `RequestProject/GLM/Harmony.lean` joined the development):

- `STATUS.md` — the "Lean development, addressed" paragraph: 861 declarations, read back 861/861 with 0 coordinate errors, 806 distinct addresses, nearest-by-address shares a file 330 times against 26 for the digest control and 20 for the seeded reshuffle, chance `288/8815`.
- `overlay/glm_universal/README.md` — the `report lean` bullet: the same figures, with 330/861 on the file test.
- `overlay/README.md` — the one-line description of the study in the document index: 861.

`MASTER_PLAN.md`'s phase record was left exactly as it was, as a historical entry.

**2. Everything in the study re-checked against the code, not just the three edits.** Every figure in `LEAN_ADDRESS_STUDY.md` was recomputed and matched: the kind table (557 theorems, 201 defs, 82 lemmas, 6 abbrevs, 5 each of inductive/instance/structure = 861), `861 parsed, 0 duplicates`, largest file `Stack.lean` at 47, the scale sweep row by row, the read-back table (20,664 coordinates, 0 errors, worst residual 3 at `GLM.CoherenceRegime`, all 861 moved by the decoder), the 47 collision classes as 40 pairs / 6 triples / one class of four together with all four example classes quoted in §6, the §7 rates and mean squared distances, and all three §8 examples down to the individual neighbour distances. Two small corrections fell out: the per-file test count in the header, and a missing line number in one §8 example.

**3. The drift is now caught rather than noticed.** `test_lean_address.py::TestDocumentsQuoteTheCurrentCorpus` parses the Lean tree and requires the four documents that state the corpus size to state the size the parser finds, so the next Lean file added fails the suite instead of quietly ageing the prose. The test-count figures that moved as a result (2,308 → 2,309 collected, 9,165 → 9,170 subtests) were regenerated with `figures --write` and propagated to `STATUS.md`, `CAPABILITY_ASSESSMENT.md`, the overlay README, the package README and the tests README, and a change-log row 5.9 (with the version header) records the round.

**4. Full re-verification after the documentation edits.**

| instrument | result |
|---|---|
| test suite | **2,309 tests across 51 test files, 9,170 subtests, zero failures** |
| end-to-end CLI evaluation | **103 / 103** — 94 answered, 9 refused as expected (all boundary, 0 gap), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| verified reports (`--verify-tct`) | `lean`, `harmony`, `directives`, `pipeline`, `containers`, `companion`, `lattices`, `shells`, `semantics`, `noise`, `catalog`, `drift`, `signature` — all **VERIFIED True** |
| Lean development | `lake build` completes cleanly; 36 files, 9,410 lines, **no `sorry`**, and the repository and overlay copies of the sources are identical |
| figures | `FIGURES.md` regenerated and matching a fresh computation |

**5. Properties table.** No registered declaration changed this session — the work was in documentation and one new test — so the table still matches the sources; the Lean entries it records were re-checked against a clean, `sorry`-free build.


# Summary of changes for run 7ff21c97-e32b-44f1-aa8b-c56599e364b5
I picked up the unfinished v1.4.0 round and closed it out — no new features were started; everything begun earlier is now wired, tested and documented.

**Documentation finished (the main remaining gap)**

- `MASTER_PLAN.md`: header figures corrected (18 query kinds, **35 report subjects**, 6 registers, **44 test files**); `report containers` and `report companion` added to the runtime-surface table; §7.9 "still untouched" updated — the "carrier in every solver" item is retired and the 32-/48-dimensional lattices are named as the open geometric direction; and a full **Phase 10** section added covering the three containers, the companion claim ledger, the formula fall-through, and the measured result.
- `overlay/README.md`: current-state part brought to v1.4.0 (35 report subjects, 37 reasoning modules, 44 test files, 97 evaluation cases, 1,991 tests), `GLM_COMPANION_STUDIES_AUDIT.md` added to the document index, and a new **change-log row 5.5** written into the archive section (the historical rows below the archive marker were left untouched, as intended).
- `CAPABILITY_ASSESSMENT.md` §6 refreshed: 35 report subjects / 36 report cases, 9 refusals across 97 cases, a new bullet for unregistered-formula carriers, "demonstrably not working" now correctly reports **no** failing case, and the untouched list realigned with the master plan.
- `overlay/glm_universal/tests/test_figures.py`: three more superseded phrases (`33 report subjects`, `35 reasoning modules`, `92-case`) added to the drift guard, so those counts cannot silently return; the subtest total the documents quote was updated accordingly (8,935) in the five places that state it.

**Full verification, all re-run from scratch and all clean**

| instrument | result |
|---|---|
| test suite | **1,991 tests across 44 test files, 8,935 subtests, zero failures** |
| end-to-end CLI evaluation | **97 / 97** — 88 answered, 9 refused as expected (all `boundary`, **0 gap**), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| capability probes | 33 probes: 20 hold, 13 break, 0 errored |
| benchmark suites | 2,389 / 2,390 across 5 suites; every suite beat its baseline |
| `figures --write` | no-op — `overlay/FIGURES.md` already matched a fresh computation |
| `report containers` / `report companion` under `--verify-tct` | both `VERIFIED True` |
| Lean development | `lake build` completed successfully; 32 GLM files, 8,157 lines, **no `sorry`** |

Every documentation figure quoted above is now the figure the code produces, and the figures test enforces that.

All work is committed and pushed. No new Lean declarations were added this session, so the properties table is unchanged and still matches the sources.

# Summary of changes for run 79fd272a-e622-48eb-930d-e2ab65130a19
I picked the project up where it stood, finished the one piece of work that had been left half-wired, and brought the documentation and README chain back into line with the code so the next iteration can start from an accurate picture.

**What I found unfinished.** The previous round had landed the study-catalogue work (`reasoning/catalog.py`, `wobble.py`, `drift.py`, the `report catalog` / `report signature` / `report drift` subjects, `RequestProject/GLM/Sturmian.lean`) and `RequestProject/GLM/Feedback.lean`, but almost none of it had reached the documents: `MASTER_PLAN.md` stopped at Phase 8, `STATUS.md` still listed error feedback as not started, the Lean README claimed 32 files while its table listed 30, the top-level overlay README's version header had moved to 5.3 with no matching change-log row, and several counts were off. Worse, the error-feedback code was reachable from nothing: `feedback_experiment` was not in `noise_report`, no test touched it, and no report surfaced it.

**Code completed.** The vector error-feedback loop is now the sixth step of `report noise` — every coordinate tracked to `1/(2N)`, the dead zone at `A = 1/2` where the quantiser never fires, and exact equivariance under a permutation the feedback matrix respects, with a non-invariant matrix run beside it so the hypothesis is seen to do work. Its column-3 script re-derives all of it in a fresh interpreter (`VERIFIED True`), and ten new tests in `glm_universal/tests/test_noise_lab.py` (40 → 50) pin the quantiser, the bound, the dead zone, the equivariance and the absence of any float.

**Documentation reconciled.** `MASTER_PLAN.md` gains Phase 9 (the catalogue ledger, the spectral signature, the drift study, error feedback) plus eight missing runtime-surface rows, and its stale "not started" bullet is corrected; `STATUS.md` records the catalogue round, the two new Lean files and the new open item, and its document map now lists both audit write-ups, the Lean README and the supplied source material; the repository `README.md` gains a section on the two claim ledgers and the missing `Feedback.lean` entry; `NOISE_EXPERIMENT_STUDY.md` gains §6 on error feedback; the Lean README gains `Sturmian.lean` and `Feedback.lean`; the reasoning, runtime, package and tests READMEs gain `wobble.py` / `drift.py` / `catalog.py`, the three report subjects and corrected counts; and the overlay README gains change-log rows 5.3 and 5.4 with the header at 5.4. `tests/test_figures.py` now also holds `STATUS.md` to the generated figures, so the status document cannot silently drift again.

**Verified here, by running it.** `lake build` completes cleanly over the 32 Lean files with no `sorry` (the repository and overlay copies are identical); the full Python suite is 1,894 tests across 42 test files, 8,896 subtests, zero failures; the end-to-end CLI evaluation is 92/92 (82 answered, 10 refused as expected — 9 boundary, 1 gap — 0 confidently wrong, 0 errored); benchmarks 2,389/2,390 with every suite above its baseline; 33 capability probes (20 hold, 13 break, 0 errored, 0 surprises); `FIGURES.md` regenerated; and `report noise`, `report catalog`, `report drift`, `report signature`, `report analogies`, `report molecules`, `report chemistry coverage` and `report semantics` each return `VERIFIED True`. The four `Feedback.lean` theorems now recorded in the properties table depend only on Lean's standard axioms.


# Summary of changes for run 1c2d31a1-2424-4b7b-bccf-398ccedefc0e
Everything you listed is done, checked by running it, and committed and pushed.

**1. The figures, regenerated.** `python -m glm_universal.figures --write` was re-run from `overlay/`. Every row of `overlay/FIGURES.md` came back unchanged except the collected test count, which moved 1,669 → **1,677** once the two new regression checks below were added. The whole suite was then run in full: **1,677 passed, 8,851 subtests, zero failures**.

**2. A changelog note about the theta template fix.** `overlay/README.md` gains row **5.1**, and its version header — which still read 4.9 while the change log had already reached 5.0 — is corrected to 5.1. The row records what the fix was and why it mattered: `report theta` claims six coefficients (`theta_series(order=5)` returns `[1, 0, 196560, 16773120, 398034000, 4629381120]`, and the solver puts all six into `expected`), but the column-3 template hand-wrote the keys `coeff_0` .. `coeff_4`, so the sixth was stated in column 2 and never re-derived in a fresh interpreter. The template now builds its `observed` map by enumerating whatever the series returns, and `report theta --verify-tct` returns `VERIFIED True` over all six. I also pinned it, since nothing was testing it: `test_runtime.py::TestReportThetaTemplate` (3 tests) checks that `expected` holds one key per returned coefficient, that the generated script enumerates rather than lists, and that a subprocess reproduces all six with no missing keys. All three fail if the old hand-written template is put back — I checked that by restoring it temporarily — so the regression cannot return silently.

**3. The session module's stale quantity count, confirmed and now verified.** `runtime/session.py` described its registers as `physics (660 quantities)`; it now says 726, which is what `len(session.register("physics"))` returns and what `FIGURES.md` reports under *Registers*. That was only asserted, not checked, so I added `test_figures.py::TestModuleDocstringsQuoteCurrentFigures` (5 tests): it reads the physics, chemistry and molecule counts out of the session docstring and out of `data_objects/physics.py`'s, compares each against the live register, and checks all six registers are named. Reverting the docstring to 660 makes it fail, which I verified.

**4. The documentation check before committing.** The counts quoted in `STATUS.md`, `MASTER_PLAN.md`, `CAPABILITY_ASSESSMENT.md`, `overlay/README.md` and the package and tests READMEs were brought to 1,677 tests / 8,851 subtests, the per-file rows for `test_runtime.py` (181 → 184) and `test_figures.py` (14 → 19) were updated with what they now cover, and `1,669 tests` / `8,818 subtests` were added to the superseded-phrase guard in `test_figures.py`. One genuine drift turned up beyond the test counts: `STATUS.md` said the Lean development was 26 files in two places while its own table and `FIGURES.md` said 27 — corrected. Historical change-log rows were left as they are, since they record what was true at the time.

**Re-verified alongside the docs:** `lake build` completes cleanly over the 27 Lean files with no `sorry` (the only `sorry`/`admit` matches in the tree are the English words "admitted"/"admits" in prose), and the repository and overlay copies of the Lean sources are identical; the end-to-end CLI evaluation is **83/83** (73 answered, 10 refused as expected, 0 unexpected refusals, 0 confidently wrong, 0 errored); benchmarks **2,389/2,390** with every suite above its baseline; **33 probes, 20 hold, 13 break, 0 errored**; all six example scripts run end to end; and `report analogies`, `report molecules`, `report chemistry coverage`, `report semantics` and `report theta` each return `VERIFIED True`. No behaviour changed in this round beyond the theta template already being fixed — the work was recording it, pinning both fixes with tests, and reconciling the numbers.

# Summary of changes for run 7260ede7-8270-4873-a880-a86f69da3294
I finished the outstanding items rather than extending the project, and re-verified everything I state below by running it here.

**Verification pass (no code changed).**
- The whole Python suite was run: **1,324 tests, 6,331 subtests, zero failures**.
- The Lean 4 development (`RequestProject/GLM/`, 18 files) was rebuilt with `lake build` — a clean build — and re-checked for `sorry`: none, in either the main tree or the overlay's copy under `overlay/glm_lean/`, and the two copies are identical.
- All six example scripts under `overlay/glm_universal/examples/` run end to end.
- The CLI answers `report information loss`, `report infinite values`, `report capabilities`, `report semantics`, `meaning of water` and `relate energy torque`, all exit 0; `report semantics --verify-tct` returns `VERIFIED True`.
- The 33 capability probes were re-run: 19 hold, 14 break, 0 errored, 0 surprises.
- The semantic graph was rebuilt from scratch: 357 meanings, 1,705 notations, 6,210 binary and 6,649 ternary edges; the inherited-graph audit still reports 83 of 4,282 concepts grounded and 2 of 4,015 edges re-derivable.

**Gaps closed.**
1. **`MASTER_PLAN.md` was missing the semantics phase.** The meaning work was built, wired and tested, but the plan — which is the document that tracks what was built and how to see it recompute itself — never recorded it. Added **Phase 4 — meaning, not spelling**: the audit of the inherited concept graph with the function that recomputes each figure, the meaning space and grounded graph with their counts, the queries, and the Lean counterparts (`Meaning.lean`, `Grounding.lean`, theorem names checked to exist). Added the two missing rows (`report semantics`, `meaning of <term>` / `relate <a> <b>`) to the runtime-surface table.
2. **Stale figures from the last round.** The repository `README.md` and `MASTER_PLAN.md` quoted an earlier test count, and the repository README plus the overlay README still said the Lean development was seventeen files. All now say 1,324 tests and 18 files, matching the runs above; the reasoning README's pointer was likewise out of date and is corrected. Historical changelog rows were left as they are, since they record what was true at the time.
3. **`Transcendental.lean` was absent from the repository README's file listing** although it is part of the development; it is now listed.
4. Added a changelog row (overlay README 4.5 → 4.6) recording this reconciliation and the figures it was checked against.

Nothing in the Python package or the Lean development needed changing — the code was already complete and passing; the remaining work was in the documentation that describes it. All work is committed and pushed.


# Summary of changes for run 712f237d-e93d-4e44-92f7-e495abe022b0
Completed the four outstanding items. Everything below was checked by running it; the work is committed and pushed.

**1. The version bump, finished.** The package declared `glm_universal.__version__ = "1.1.0"` and exported the new `semantics` sub-package, but the test that pins the package surface still asserted `1.0.0` and listed only six sub-packages — so the suite was failing one test. `glm_universal/tests/test_wiring.py::TestPackageSurface` now pins the current version and all seven exported sub-packages (`substrate`, `data_objects`, `reasoning`, `semantics`, `runtime`, `migration`, `benchmarks`), which is what makes a future bump self-checking. The suite is now **1,094 tests, 6,331 subtests, zero failures** (about four minutes). Stale counts elsewhere in the package and reasoning READMEs were corrected to match.

**2. `glm_universal/tests/README.md`.** Repaired the file-by-file table (the `test_semantics.py` row had been left outside it, breaking the table), corrected the per-file and total counts against a real collection run, listed `test_semantics.py` among the substantive tests, and added a short section on the package-surface test and on the slowest fixtures.

**3. `glm_universal/examples/README.md`.** Rewritten. It now covers all six scripts — `reasoning_showcase.py` was missing entirely — plus the generated transcript and how to regenerate it, each script's flags, what each one prints when it succeeds, and its known limitations. Writing it truthfully turned up three real defects, which I fixed rather than documented around: `encoding_poc.py` and `scaled_carriers.py` looked for `data_objects/_data/elements_118.json` under `examples/` and could not start at all, and `scaled_carriers.py` formatted an exact `Fraction` with a float format spec, which raises on Python 3.11 — it now renders through the package's exact `decimal_str`, so no float is constructed. All six scripts run end to end; `demo_tct.py` reports `ALL DEMOS VERIFIED` and the showcase 29 probes, 29 as expected.

**4. The overlay top-level README.** Version 4.2 → 4.3, a changelog row for the v1.1.0 work, the README chain and the `glm_universal/` entry brought up to date (seven sub-packages, 15 query kinds, 16 report subjects, 1,094 tests, thirteen Lean files), and a new "GLM-3+ v1.1.0" section at the bottom: the audit of the inherited concept graph (83 of 4,282 concepts denote anything determinate; 2 of 4,015 edges state a re-derivable relation; the stored carriers put related pairs at mean Hamming 4547/376 and unrelated pairs at 12077/1009, either side of the 12 that two random 24-bit words average), the grounded graph that replaces it (357 meanings, 1,705 notations, 12,859 edges, all re-derived), the `meaning` query and `report semantics` subject, the Lean files, and the test count. Every figure in that section was recomputed here before being written, and `report semantics --verify-tct` returns `VERIFIED True`.

One consistency gap I closed along the way: the overlay's copy of the Lean development was missing `RequestProject/GLM/Semantics/Meaning.lean` and `Grounding.lean`. Both are now in the overlay and documented in its Lean README (eleven files → thirteen). `lake build` completes successfully and the development remains free of `sorry`.


# Summary of changes for run 49a39c3c-68b2-4fde-b6e9-f434bec3e479
Both halves of the request are complete, committed and pushed.

## 1. The GLM system implementation, completed

`glm_universal_v0.6.0/` is the supplied package, unpacked and finished.

- **`GLM.py` was missing from the archive.** The READMEs document it and two test files import it by path, so 30 CLI tests errored on collection. I wrote it from scratch against the behaviour those tests specify: batch mode (`-q`, `--query-file`, stdin) and `--interactive`; the flags `-d/--domain`, `-c/--columns`, `-f/--format`, `--list-domains`, `--export-trace`, `--check-script-exactness`, `--verify-tct`, `--no-banner`; the meta-commands `:help :domains :basis :columns :verify :history :snapshot :export :quit`; and the 0/1/2 exit-code contract.
- **New module `glm_universal/reasoning/information_loss.py`**, exported from the reasoning package and wired into the runtime as the query **`report information loss`** (aliases `report loss`, `report boundaries`), with a generated column-3 script that recomputes the whole study in a fresh interpreter and checks it key by key. Exact `Fraction` arithmetic throughout; no float is constructed anywhere. Views are memoised because the rational layer's `perceive` runs a Leech nearest-point decode, and the cache is tested to be an optimisation only.
- **Full suite: 652 tests, 5,877 subtests, zero failures** (610 before, plus 42 new in `test_information_loss.py`). Verified by running it, not by report.
- READMEs updated: `TopLevel_README.md` (v4.1 changelog + a full v0.7.0 section), the package, reasoning, runtime and tests READMEs, plus a new repository `README.md`.

## 2. The information-loss study

The write-up is **`INFORMATION_LOSS_STUDY.md`**. The formal development is in `RequestProject/GLM/` — six Lean files, building cleanly with no `sorry`, and the key theorems depend only on Lean's standard axioms.

Your idea, made precise: a layer is a *resolution*, not a set of claims. On that reading all three parts of it are theorems.

- **Loss and gain are the same event.** `boundary_nonempty_iff_new_visible`: the pairs a layer conflates are non-empty exactly when the layer above can state something it cannot.
- **Nothing true below becomes false above** (`Visible.mono`), so "becomes untrue" is located precisely — not in propositions flipping, but in an operation ceasing to be a function of what a layer sees (`descends_iff_congruent`, the exact content of the code's `can_multiply` flag).
- **The ascent is forced** by capacity below the carrier count, and computable: `escalate` returns the least layer separating two carriers, proved correct and minimal.
- **It continues without end** (`Tower.lean`): an explicit infinite ladder — layer *n* sees a rational to resolution 2⁻ⁿ — that is cumulative, gains strictly new expressive power at *every* step, has no final layer, and still eventually tells any two distinct carriers apart. Set against `boundary_above_rational_empty`, which shows a tower *can* terminate: whether it does is a property of the carriers, not of layering itself.

Four concrete boundaries are pinned exactly, not estimated: the layer stack over ℚ (resolutions 2/3/4, losses 2/1/0); addition, which is exactly right at the substrate on integer carriers and *ill-defined* there on rationals; the TAX conservation law, exact on bits and above them repairable only if `Y = 1/2`, which is false since `1/4 < Y < 1/2`; and Golay repair, unique at Hamming weight 3 and genuinely two-valued at 4.

## Audit finding

Running the same definitions against the shipped `dimension_layers.py` rather than an idealisation of it reports `refinement_chain_intact = False`. The substrate → integer step is **not** a refinement on real carriers: the substrate's 24-bit parity view separates a unit on coordinate 10 from the vacuum, while the integer layer reads only the seven SI7 exponents and conflates them — so escalating destroys a distinction the layer below already had. It is reported and tested rather than silently patched, since fixing it (widen the integer view, or narrow the substrate's) is a design decision about what the integer layer is for.
