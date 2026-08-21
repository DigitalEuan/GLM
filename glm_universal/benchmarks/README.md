# `glm_universal.benchmarks` — RESERVED (not yet implemented)

**Status: empty scaffold.** This directory contains no implementation and no
results. It is created in Step 1 so that the package hierarchy and the
contract below are fixed before any code depends on them.

## Intended contract

Task suites and scoring for GLM-3+.

* A benchmark must state its **evidence tier** before it is run: what counts as
  a pass, what the baseline is, and what a null result would look like.
* Scores are written to `results/` as data, with the source script and run id
  recorded, and mirrored into `results/claims.json`. No headline number travels
  only in prose.
* Negative and null results are reported alongside positive ones. A suite that
  reports only its wins is a broken suite.
* No third-party LLM inference. Any benchmark design that requires calls to an
  external model provider must be flagged and left pending a user-supplied key
  rather than simulated.

## Invariants inherited from the substrate

Exact arithmetic, no randomness in the substrate path, deterministic re-runs.
Where a benchmark needs sampling, it must carry an explicit seed in its
recorded parameters.

## Depends on

`glm_universal.substrate`, `glm_universal.data_objects`,
`glm_universal.reasoning`.
