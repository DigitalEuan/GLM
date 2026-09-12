# `glm_universal.corpus` — the documents held the way the substrate holds data


## Tier 0 — the coarse read

**Question.** How is the project's own prose kept from drifting away from the code it describes?

**Verdict.** The corpus is data: classified by rule, addressed, generated where it can be, and checked.

**Deciding figure.** 7 modules, one command that reports every drift at once and one that repairs it.

**Recomputed by.** `glm_universal.corpus.report.corpus_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

**Status: implemented, current.** 7 modules, one derived data directory, no
third-party dependency, and no float anywhere: every rate is a `Fraction` and
every distance an `int`.

## Why a package for the documents

A document that quotes a number is a cache of that number, and a cache with no
digest goes stale silently. The rest of the package already treats stored
figures that way — `figures.py` regenerates them, `derived.py` guards them by
digest. This package extends the same discipline to the prose itself, so that
the corpus is **classified by rule, addressed, generated where it can be, and
checked** rather than maintained by memory.

| Module | What it holds |
|---|---|
| `inventory.py` | Every document, read once: its sections, its links, its tier-0 block, whether it is generated, and whether it is archive. Archive membership is a rule on the path — a name ending `_ARCHIVE.md`, the session working note, or anything under a directory named `archive` — never a judgement. |
| `render.py` | The generated artefacts: `DIGEST.md`, and every in-document `<!-- generated: … -->` block. Rendering is idempotent, so writing twice changes nothing the second time. |
| `address.py` | A Leech address for every section of the corpus, computed from the same quantiser the Lean declarations use, with the shortlist that certifies absence. |
| `measurements.py` | The expensive figures — the tables of the address study and of the retrieval study — taken once and kept beside the digest of the Lean sources they were taken from. A stale cache is reported, never answered from. |
| `cost.py` | What one iteration of the rebuild chain costs, in exact counts rather than timings: what a one-file change invalidates, how much of the decoding is reused, how often the planner's report is taken, and how many figures are emitted rather than typed. |
| `checks.py` | The tier contract, the archive partition, the coverage claim of `ENTRY.md`, and the freshness of every derived artefact. |
| `report.py` | All of it in one call, including the reading cost at each resolution. |

## Running it

```bash
cd /path/to/GLM                       # repo root, where GLM.py lives
PYTHONPATH=. python3 -m glm_universal.corpus            # the report
PYTHONPATH=. python3 -m glm_universal.corpus --check    # exit 1 on any drift
PYTHONPATH=. python3 -m glm_universal.corpus --refresh  # rebuild everything derived, in order
PYTHONPATH=. python3 -m glm_universal.corpus --write    # regenerate the blocks
PYTHONPATH=. python3 -m glm_universal.corpus --remeasure  # re-take the Lean measurements
PYTHONPATH=. python3 -m glm_universal.corpus --ask "what bears on the Golay code?"
```

`--refresh` is the one command to reach for after a change. It rebuilds the
Lean address book, then the document address book, then the measurement cache,
then the generated documents, blocks and inline figures — in that order, which
is the only order in which one pass converges — repeating until it settles and
finishing with a fixed-point check. Doing it by hand in the wrong order is
refused rather than silently wrong: measuring before the book is rebuilt raises
`measurements.StaleAddressBook`. `--full` decodes every address from nothing
instead of reusing the stored books.

`--check` is the one command that reports every drift at once: a document
without a tier-0 block, a tier-0 verdict the body below it does not support, a
generated block that no longer matches a fresh rendering, a link to a file that
does not exist, a current-state document unreachable from `ENTRY.md`, an
archived document left off its list, an inline `<!--figure:…-->` marker whose
body is not what its figure now says, or a measurement cache taken from a Lean
tree that has since moved.

## What is proved rather than asserted

[`RequestProject/GLM/Corpus.lean`](../../glm_lean/RequestProject/GLM/Corpus.lean)
carries the part of this that is a theorem: that the tiered read is sound (a
tier-0 claim is implied by the body it summarises), that the archive rule
partitions the corpus, that a derived artefact is usable exactly when its
digest matches, and that an empty shortlist is a proof of absence rather than a
failure to look.

## The studies it emits

`studies/CORPUS_ADDRESS_STUDY.md` measures the division of labour between the
two instruments: the address supplies the guarantee — a shortlist complete up
to a stated radius — and lexical search supplies the ranking. Its tables are
generated blocks, so they cannot age. So are those of
`studies/LEAN_ADDRESS_STUDY.md` and `studies/ADDRESS_RETRIEVAL_STUDY.md`, both
emitted from the measurement cache guarded by the digest of the Lean sources.
`studies/ITERATION_COST_STUDY.md` is `cost.py`'s: what one iteration of the
rebuild chain costs, and how much of that cost was work repeated on things that
had not moved.

## Tests

`tests/test_corpus.py` — 55 tests: the tier contract, the archive rule and its
partition, the coverage claim, generation and its idempotence, the inline
figures and the history passages they must leave alone, the incremental address
book and its completeness bound, the ordered refresh, and exactness.
