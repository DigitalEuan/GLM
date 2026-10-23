# `glm_universal.knowledge` — the corpus as what the GLM knows

## Tier 0 — the coarse read

**Question.** How does the GLM use everything the project has written as its corpus, without training and without chance?

**Verdict.** The corpus is counted, not trained: every figure is an integer with a witness sentence, and the counts grow with the corpus.

**Deciding figure.** 8 modules, one query kind (`corpus`), two measurements against pre-registered marks (nine in Phase 154, eight in Phase 155).

**Recomputed by.** `glm_universal.knowledge.study.corpus_knowledge_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../../README.md`](../../../README.md) · **Study:**
[`studies/CORPUS_KNOWLEDGE_STUDY.md`](../../../studies/CORPUS_KNOWLEDGE_STUDY.md)

## What it is

An LLM learns from a corpus by adjusting floating-point weights from a random
start in a random order. The GLM's corpus — the studies, the state documents,
the Lean development, the Python package, the JSON and CSV the instruments
emit, and the supplied material in `source_material/` including the members of
its zip archives — is used here directly, and the whole of the "training" is
counting. The corpus is counted, not trained: every figure is an integer with
a witness sentence, and the counts grow with the corpus. The package is 8
modules, one query kind (`corpus`), and two measurements against
pre-registered marks (nine in Phase 154, eight in Phase 155).

| module | what it holds |
|---|---|
| `reader.py` | the walk, by rule: every file read into folder → document → paragraph → sentence → token, each sentence with its address (`document#pN.sM`) and its tier-0 mark. Prose only: Markdown without fenced code, docstrings and comments, Lean doc comments, JSON strings and CSV cells of at least five words. |
| `model.py` | the counts (tokens, one- and two-token continuations, document and folder frequency, content-word co-occurrence in a four-token window), the integer association rule, the associated-context sets, and the cache — re-read per file digest, so a new or changed file is the only file read again. |
| `answer.py` | the readings: `define`, `context`, `similar`, `related`, `continue_text`, `spread`, and `predict`. |
| `ask.py` | the `corpus` query kind's request grammar, and the brute-force recheck column 3 runs. |
| `study.py` | the measurement of `CORPUS_KNOWLEDGE_STUDY.md`. |
| `glossary.py` | Phase 155: the paper's glossary held out of the corpus, `define` graded against it by shared content words, and the **context ranking** `corpus define` now uses (of the sentences that define X, the one holding most of X's corpus context first). |
| `word_address.py` | Phase 155: a word's **Leech address** — 24 coordinates from its company beside the corpus's most frequent tokens (exact floor-log of an integer lift), quantised by the decoder the Lean declarations use, read back exactly; its nearest words on the lattice. |
| `definitions_study.py` | the measurement of [`CORPUS_DEFINITIONS_STUDY.md`](../../../studies/CORPUS_DEFINITIONS_STUDY.md). |
| `friction.py` | Phase 156: the hold-out model, the patch, contact, tie-break and loaded predictors, the continuation under each, and the frictionless and sticking folder readers. |
| `friction_survey.py` | Phase 156: the seven declared perturbations of the evaluation's questions, scored hold / stick / slip, and the re-scoring of planner refusals. |
| `friction_study.py` | the measurement of [`FRICTION_STUDY.md`](../../../studies/FRICTION_STUDY.md), with the frozen-path comparison of `settle_question`. |
| `friction_two.py` | Phase 157: worn contact (each touch-set word has a budget of 2) and the noise-set sticking reader (a margin of `r/8`, `r` the leader's changes so far), over Phase 156's sample and readers. |
| `friction_two_study.py` | the measurement of [`FRICTION_TWO_STUDY.md`](../../../studies/FRICTION_TWO_STUDY.md): wear, the margin, the offline respelling, the survey after the round and the frozen-path comparison. |

## Using it

```bash
cd overlay
python3 GLM.py -q "corpus define golay code"
python3 GLM.py -q "corpus context of nrci at paragraph scale"
python3 GLM.py -q "corpus words like decoder" --verify-tct
python3 GLM.py -q "corpus continue a digest addresses"
python3 GLM.py -q "corpus address of seven" --verify-tct
PYTHONPATH=. python3 -m glm_universal.tools corpus-ask what is a syndrome
PYTHONPATH=. python3 -m glm_universal.tools corpus-knowledge          # the stored marks
PYTHONPATH=. python3 -m glm_universal.tools corpus-knowledge --write  # re-take them
PYTHONPATH=. python3 -m glm_universal.tools corpus-definitions        # Phase 155's marks
PYTHONPATH=. python3 -m glm_universal.tools friction                  # Phase 156's marks
PYTHONPATH=. python3 -m glm_universal.tools friction-two              # Phase 157's marks
```

The first call after the corpus moves re-reads the changed files and recounts
(about half a minute); after that a reading costs the cache load.

The cache (`_knowledge_cache/`, about 135 MB) is derived and is **not version
controlled**: tracked, its rewritten copies made pushes too large for the git
server, so the directory is listed in the repository's `.gitignore`. A fresh
clone has no cache; the first reading counts the whole corpus and writes it
(about a minute, announced on a terminal), as does `corpus --refresh`. Set
`GLM_KNOWLEDGE_CACHE` to keep it somewhere else. `model.cache_state()` reports
whether it is present and how large; `tests/test_repository_hygiene.py` holds
all of this.

## The rules that keep it exact

* **Counts, not weights.** Every table entry is an `int`; every ratio is a
  `Fraction`; association is the integer comparison `n(a,b)·T² > n(a)·n(b)·P`
  (positive pointwise mutual information without a logarithm).
* **Additive.** The model of two disjoint collections is the sum of their
  models, and the order documents arrive in cannot change it — proved in
  [`CorpusKnowledge.lean`](../../glm_lean/RequestProject/GLM/CorpusKnowledge.lean)
  (`train_append`, `train_perm`) and checked on the real corpus by the study.
* **Witnessed.** A count is positive exactly when some sentence carries the
  feature (`train_pos_iff`); `define` and `continue_text` name the sentence.
* **Ties are refused.** `predict` returns no word when two continuations are
  equally frequent (`predict_eq_none_of_tie`), and `continue_text` stops and
  names the tie.
* **Ranked by where a sentence stands.** `define` prefers a tier-0 sentence
  and the state documents over the archive and the supplied material, which
  can be out of date; every answer says which it came from.

## What it is not

Not a generator of new claims: everything it says is a sentence of the corpus
or a count over the corpus. It is classed `table` and `address` under the
faculties of [`BLOCKERS_STUDY.md`](../../../studies/BLOCKERS_STUDY.md), with
`refuse` for the terms it declines, and never `derive`.
