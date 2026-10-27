# Round 7 — supporting files (outside Lean)

The formal results of this round are in the Lean package
(`RequestProject/GLM/Rule30/NoConstantColumn.lean` and
`RequestProject/GLM/Rule30/OnePeriodicColumn.lean`; see the package README, "Round 7").
This folder holds the GLM wiring notes and the computer runs. Nothing here is a proof.

## 1. Running the full GLM with the added `parser.py`, `session.py`, `tct_engine.py`

With the three files copied into `glm_universal/runtime/`, the GLM still did not import,
because `glm_universal/runtime/reports/` in `glm_repo.zip` has no `__init__.py`, and
`session.py` imports a mixin class `LatticeGeometryReports` that no file in the archive
defines.

* `glm_reports_init_shim.py` is the `__init__.py` used here. It re-exports the eleven report
  mixins found in `reports/*.py` unchanged and defines `LatticeGeometryReports` as an
  **empty placeholder**. The report subjects of that class are therefore unavailable. Replace
  the shim with the real file from your GLM repository.
* With the shim, `GeometricSession` builds and answers queries (`glm_probe.py`,
  output in `glm_probe_output.txt`).
* `python3 -m glm_universal.corpus --refresh` rebuilt the Lean, lexical and document address
  books and the measurement cache, then stopped at the next step on
  `ModuleNotFoundError: glm_universal.evaluation.harness` (another module missing from the
  archive). The rebuilt address books were enough for `--ask` to run
  (`glm_corpus_ask_output.txt`).
* `GLM.py -q ...` (the CLI) still fails: it imports `glm_universal.runtime.respell` and
  `glm_universal.runtime.sinter`, which are not in the archive.

### What the GLM said about Rule 30

* The session has no Rule 30, cellular-automaton or "centre column" concept in any enabled
  domain. It **refuses** these queries ("names no carrier in any enabled domain", or "not
  recognised as any of [verify, analogy, describe, …]"). It does not make anything up.
* Its own substrate reports work. `report golay decoding` confirms the 24-bit Golay decoder
  used in Round 6 (4096 cosets, unique decoding below weight 4). `report lean` confirms the
  Lean address book.
* `corpus --ask` matches by word overlap within the GLM's own documents. For the Rule 30
  questions it returns sections with overlap 1–2 words (for example
  `studies/ENGINEERING_LANGUAGE_STUDY.md#6-delta-sigma` for "cellular automata and
  periodicity"). That is retrieval of GLM prose, not a statement about Rule 30.

**Conclusion for the GLM project.** In its current form the GLM cannot pose or check the Rule 30
questions. Adding a "cellular automaton" register would let it hold the definitions. The
results themselves (`claims.csv`, Lean names) can be put into its Lean address book by copying
the package into `overlay/glm_lean/RequestProject/GLM/` and running `corpus --refresh`, as the
package README describes.

## 2. Constant runs in the centre column (`r7_run_lengths.py`)

The Lean theorem `centerCol_change_in_window` proves that every window `[N, 4N+6]` contains a
colour change, i.e. a constant run starting at time `N` has length at most `3N+6`. Measured to
`T = 20000`, the longest run is 14 (starting at `t = 11109`). The worst ratio
run / (3N+6) is 1/5, attained near the start (the run of length 3 at `N = 3`). The proved bound is linear while the data look
logarithmic, so the bound is far from tight. Output: `r7_run_lengths_output.txt`.
