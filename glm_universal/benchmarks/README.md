# `glm_universal.benchmarks` — task suites and scoring

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

**Status: implemented.** Five suites, 2,390 scored tasks, results written as
data into [`results/`](results/). The contract this directory was reserved
under — evidence tier declared first, results as data, negative results
reported — is now enforced by the harness rather than promised in prose.

```bash
PYTHONPATH=. python3 -m glm_universal.benchmarks             # run and print
PYTHONPATH=. python3 -m glm_universal.benchmarks --write     # write results/
PYTHONPATH=. python3 -m glm_universal.benchmarks --list
PYTHONPATH=. python3 -m glm_universal.benchmarks golay_correction
PYTHONPATH=. python3 GLM.py -q "report benchmarks" -c 1      # through the runtime
```

Exit code 0 when every suite beat its declared baseline, 1 when any suite
returned a null or below-baseline result.

## The contract, enforced

| Rule | How it is enforced |
|---|---|
| A benchmark states its evidence tier **before** it is run | `EvidenceTier` is a required field of `Suite`; `run_suite` refuses a score whose tier differs from the declared one |
| A sampled benchmark carries an explicit seed | `EvidenceTier.__post_init__` raises without one, and refuses a seed on a non-sampled tier |
| Scores are exact | every score is a `Fraction`, serialised as `"n/d"`; the test suite walks the whole report and fails on any float |
| No headline number travels only in prose | `write_results()` writes one JSON file per suite plus `results/claims.json`, and every claim carries its baseline and verdict |
| Negative and null results are reported | `SuiteScore.findings`; a score equal to its baseline is named `"null"`, not rounded up to a pass |
| A suite that scores nothing is broken | `run_suite` refuses an empty suite rather than calling it perfect |
| Re-runs are deterministic | the run id is a SHA-256 of the results themselves, so identical code gives an identical id and a changed number changes the id |

## The suites

| Suite | Tier | Question | Score | Baseline |
|---|---|---|---|---|
| `physics_equations` | curated | Does the verifier accept true dimensional equations **and refuse false ones**? | 29/30 | 20/30 — accept everything |
| `golay_correction` | exhaustive | Does the decoder correct every error the code guarantees? | 2325/2325 | 1/2325 — leave the word alone |
| `analogy_chemistry` | curated | Do periodic-table analogies resolve to the right element? | 9/12 | 3/12 — nearest carrier to C |
| `analogy_semantic` | curated | Do antonym and scale analogies resolve to the right word? | 5/10 | 0/10 — nearest carrier to C |
| `analogy_physics` | curated | Do dimensional analogies land in the right dimension? | 12/13 | 0/13 — nearest carrier to C |

Overall **2,380 of 2,390 tasks**, every suite above its own baseline.

The ground truth is external in every case: standard SI dimensional
analysis, the periodic table, ordinary English, and the minimum distance of
the binary Golay code. No suite asks the system for the right answer.

The baseline for the three analogy suites is the answer a system with the
register and the metric but *no analogy mechanism* would give — the nearest
carrier to C, ignoring the displacement A → B. What the suites score above
it is what the displacement bought.

## What the suites found

Eight findings are reported beside the scores. Four of them are failures
with a reason:

* **`ext10_refuses_angular_momentum`.** The textbook identity
  `angular_momentum = momentum × length` is *refused*. This is the basis
  boundary and not an arithmetic error: EXT10 carries plane angle as a
  dimension, so angular momentum is `L² M T⁻¹ A⁻¹` while momentum times
  length is `L² M T⁻¹`. The identity is true in SI7, where the angle
  exponent does not exist, and false in EXT10 — an instance of exactly the
  layer handoff the information-loss study describes.
* **`scalar_vs_full_semantics`.** Three equations that scalar semantics
  accepts, full tensor semantics refuses (`energy = force * length`,
  `pressure = force / area`, `velocity = length / time`). The suite scores
  the scalar reading and reports the divergence rather than choosing a
  winner.
* **`weight_4_is_ambiguous` and `weight_5_is_confidently_wrong`.** One past
  the packing radius, all 10,626 weight-4 patterns are equidistant from six
  codewords; at weight 5, all 42,504 patterns decode to a unique **wrong**
  codeword. Both counts are exhaustive. The second is a null result for
  correction beyond the radius and is reported as one: the remedy is a
  declared channel radius, not a better decoder.
* **`reciprocal_relations_are_out_of_model`.**
  `length : wavenumber :: time : frequency` fails, because the solver models
  an analogy as a fixed displacement `b − a` added to `c`, and length to
  wavenumber is an inversion rather than a displacement. The task is right
  and the answer is wrong for a structural reason: no tuning inside the
  additive model reaches reciprocal relations.

The others record the analogy misses by name, and the gap between scoring
`analogy_physics` by dimension (12/13) and by name (3/13) — that gap is the
register's dimensional degeneracy, not the analogy.

## Layout

```
harness.py     EvidenceTier, TaskOutcome, Finding, SuiteScore, Suite,
               the registry, run_all, benchmark_report, write_results
suites.py      the five suites and the task lists they score
__main__.py    the command-line runner
results/       one JSON file per suite plus claims.json
```

Every failing outcome is written to `results/`; passing outcomes are sampled
to the first 25 per suite, with the total and a note recorded in the file.
Scores, claims and the run id are always computed from the whole population.

## Depends on

`glm_universal.substrate`, `glm_universal.data_objects`,
`glm_universal.reasoning`, `glm_universal.runtime`.

## Tested by

[`../tests/test_benchmarks.py`](../tests/test_benchmarks.py) — 67 tests: the
registry, the tier discipline (including that a sampled suite without a seed
is refused), exactness, each score against its baseline, that every suite
reports its findings, that the written results keep every failure and are
byte-stable across two runs, that the checked-in `results/` is not stale, and
that the runtime query and its column-3 script agree with the package API.
