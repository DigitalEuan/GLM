# The corpus confidence curve, declared — three operating modes chosen before they are measured, and definitions that say how good they are

## Tier 0 — the coarse read

**Question.** Can the counted corpus model declare operating points on its precision/coverage curve — a sure mode, a balanced mode and a candidate mode — chosen on a calibration fold by rules written before the held-out measurement, and do they hold on held-out text; and can a definition carry a description of its own quality that tells a good one from a weak one?

**Verdict.** Partly. The balanced mode chosen on the calibration fold meets the bar Phase 154 missed on held-out text — 33.7% precision, 1.6 times the unguarded accuracy, at 42.4% coverage — and the order control falls to 3.3% under the same guard. The sure mode holds 62.0% precision at 7.3% coverage but misses its declared three-times bar narrowly, and the balanced mode's coverage moved by just over the declared tolerance between folds. Strong definitions agree with the held-out gloss only slightly more often than weak ones (4 of 15 against 2 of 8).

**Deciding figure.** 6 of 8 marks; balanced guard `(1, 1/5)`: 33.7% at 42.4% held out (31.7% at 37.3% calibrated); sure guard `(2, 2/3)`: 62.0% at 7.3% held out, 2.95 times the unguarded 21.0%; candidate top three: 32.7% hit at 98.4%; C1 and C3 missed.

**Recomputed by.** `glm_universal.knowledge.confidence_curve.confidence_curve_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 20 October 2026 (pre-registered 20 October 2026: §§0–6 were committed before any figure of the calibration or held-out fold was read; measured 20 October 2026, §7).*

## 0. What this document is

A pre-registration for Phase 168. It takes Part II.4 of the owner's plan of
19 October 2026 ([`source_material/GLM_19OCT26_1.md`](../source_material/GLM_19OCT26_1.md),
*develop an explicit corpus confidence curve*), which is To-Do item 3 of
`STATUS.md` §2.1: *the counted model knows when it is right only at low
coverage (K3′: 54% precision at 10.7%); declare a point on that curve before
measuring it* ([`CORPUS_KNOWLEDGE_STUDY.md`](CORPUS_KNOWLEDGE_STUDY.md) §7.5).
The plan asks for declared operating modes — high confidence and low
coverage, balanced, high coverage as candidates — and for definitions
returned with a description of their quality rather than every pattern match
treated as a definition.

**What was known when this was written.** The positions of both folds were
computed once while the measuring code was written (633,406 calibration
positions, 407,095 held-out positions); no precision, coverage or accuracy of
either fold was read before this section was committed.

## 1. The folds

**By the digest of the path, not by position in the sorted corpus.** A
document's fold is `sha256(path) mod 5`. Fold 4 is held out; fold 3 is the
calibration fold; folds 0–2 are the calibration model's training documents;
folds 0–3 train the held-out model. A document added to the corpus does not
re-deal any other document's fold, which answers one line of To-Do item 6
(*the held-out rule … re-deals every later fold*) for this study's own
split. Positions are every token of every novel sentence of the test fold
(a sentence whose tokens occur in the training documents is skipped, as in
Phase 154), the end-of-sentence marker included.

## 2. The curve and the modes

**The guard family.** A guard `(c, s)` answers a position when the deciding
context is the two-token one, its maximum is unique, the context was seen at
least `c` times, and the winning continuation is more than the share `s` of
what followed it. The grid: `c ∈ {1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 25,
32}`, `s ∈ {0, 1/5, 1/4, 1/3, 2/5, 1/2, 3/5, 2/3, 3/4, 4/5, 9/10}` — 143
guards. Phase 154's guarded reading is `(2, 0)`; its majority guard is
`(3, 1/2)`.

**The modes, chosen on the calibration fold only.** Let `u` be the
calibration fold's unguarded accuracy (the backed-off model answering every
position).

* **sure** — the guard of greatest calibration coverage whose calibration
  precision is at least `3u`;
* **balanced** — the guard of greatest calibration coverage whose calibration
  precision is at least `3u/2` (the bar of K3 and K3′);
* **candidate** — not a guard: whenever the deciding context is the two- or
  one-token one, the three most frequent continuations (count, then
  spelling), offered as candidates; a position counts as hit when the token
  that follows is among them.

Ties in coverage go to the higher precision, then to the smaller `c`, then
the smaller `s`. The chosen guards are then applied, unchanged, to the
held-out fold, read by the held-out model.

## 3. The definitions' quality

Every answer of `define` (context-ranked, as since Phase 155) now carries a
**quality description**: the witness sentence and its address; the pattern
that matched and its strength (0 strongest); the source (written, supplied
or stored); and the **context support** — how many of the term's twelve
sentence-scale context words the sentence contains. Its grade:

* **strong** — pattern strength at most 2 and context support at least 2;
* **weak** — otherwise.

Measured on the 28 glossary terms of the paper held out of the corpus
(Phase 155's protocol, `knowledge/glossary.py`): an answer *agrees* when it
shares at least two content words with the held-out gloss.

## 4. The marks

| mark | met when |
|---|---|
| **C1** | the mode transfers: for sure and balanced, the held-out precision and the held-out coverage are each within 5 percentage points of the calibration figures |
| **C2** | the balanced mode meets K3′'s bar on held-out text: precision at least 1.5 times the held-out unguarded accuracy, at a coverage of at least 20% |
| **C3** | the sure mode's held-out precision is at least three times the held-out unguarded accuracy |
| **C4** | the candidate mode: held-out hit rate at least the unguarded accuracy plus 10 points, at a coverage of at least 80% |
| **C5** | the modes are ordered on held-out text: precision sure > balanced > unguarded accuracy, and coverage sure < balanced < candidate |
| **C6** | the order control — the same held-out positions read by the model of the same training documents with every sentence's tokens sorted, under the same chosen guards — has a precision at least 10 points below the balanced mode's |
| **D1** | every answered glossary term carries the quality description of §3 |
| **D2** | the grade informs: strong answers agree with the held-out gloss at a higher rate than weak ones, with at least three of each |

## 5. What would count against

C1 missed would mean the curve does not transfer between folds: a declared
point is then not a promise about text the model has not seen. C2 missed
would mean K3′'s bar is not reachable by any declared guard of the grid at
20% coverage, on this corpus. D2 missed would mean the grade describes the
answer but does not predict whether it is right.

## 6. What is not claimed

The modes are reading modes of the measured predictor; this round does not
wire them into `continue` or the evaluation (that would change pinned
answers and needs a frozen-path comparison). The quality description is
attached to `define`'s answers but does not change which answer is first.
The 28 glossary terms are few: D2 is a small-sample reading and is reported
with its counts.

## 7. What came out

`PYTHONPATH=. python3 -m glm_universal.tools confidence-curve` (stored in
`knowledge/_data/confidence_curve.json`, digest-guarded; `--write` re-takes it
in about five minutes). The corpus read had 2,294 documents, dealt by path
digest into folds of 439, 506, 481, 443 and 425.

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **C1** | sure: precision 57.7% → 62.0% (4.3 points), coverage 6.6% → 7.3%; balanced: precision 31.7% → 33.7% (2.1 points), coverage 37.3% → 42.4% (**5.2 points**) | **missed** (the balanced coverage) |
| **C2** | balanced `(1, 1/5)`: 33.7% precision, 1.60 times the held-out unguarded 21.0%, at 42.4% coverage | met |
| **C3** | sure `(2, 2/3)`: 62.0%, **2.95 times** the held-out unguarded 21.0% (3.07 times on the calibration fold) | **missed** |
| **C4** | candidate (top three): 32.7% hit at 98.4% coverage, against 21.0% + 10 points | met |
| **C5** | precision 62.0% > 33.7% > 21.0%; coverage 7.3% < 42.4% < 98.4% | met |
| **C6** | the order control under the balanced guard: 3.3% precision (at 17.1% coverage), 30.4 points below | met |
| **D1** | 23 of 23 answered glossary terms carry the description (27 terms; 4 refused) | met |
| **D2** | strong 4 of 15 agree (26.7%), weak 2 of 8 (25.0%) | met (narrowly) |

**6 of 8 marks.** Both misses are kept as misses.

### 7.2 What this answers

**A declared point on the curve meets K3′'s bar.** Phase 154 found that the
counted model knew when it was right only at low coverage (54% at 10.7%), and
left the curve between its two guards undeclared. Declared on the calibration
fold before the held-out fold was read, the balanced rule picked the guard
`(1, 1/5)` — answer a two-token context whenever its unique winner holds more
than a fifth of what followed it — and on held-out text that guard answers
42.4% of positions at 1.6 times the unguarded accuracy. Of the 143 guards of
the grid, 14 meet the bar on held-out text; the declared rule found one of
them without seeing held-out text. Phase 154's own guards, read on these
folds, are where Phase 154 put them: `(2, 0)` 23.2% at 62.7%, `(3, 1/2)` 50.8%
at 11.0%.

**The confidence is in the word order.** The same guards applied to the model
whose sentences were sorted keep a sixth of the positions and are right on 3%
of them (C6): what the guard selects is a context whose order predicts, not
a frequent word.

**Why the two misses.** The held-out fold is easier than the calibration
fold: its unguarded accuracy is 21.0% against 18.8%. Every guard's precision
rose with it, but a bar stated as a multiple of the unguarded accuracy rose
too, and the sure guard's ratio fell from 3.07 to 2.95 (C3). The balanced
guard's coverage rose by 5.2 points (C1), probably for a related reason —
more of the held-out fold's contexts were seen in training (its model is trained on four
folds, the calibration model on three). A declared point transfers in
precision to within 4.3 points; coverage transfers less well when the
training set grows, which a calibration fold the same size as the held-out
model's training set would remove.

**The definitions' grade describes more than it predicts.** Every answer now
says which pattern matched and how strongly, where the sentence comes from,
and how much of what the corpus says around the term it repeats. On the 27
glossary terms (the glossary parses to 27, not the 28 §3 named when it was
pre-registered), strong answers agree with the held-out gloss at 26.7% and
weak ones at 25.0%: the order is the declared one, but the margin is one
answer in a small sample, and agreement is low under both grades. The
description is useful for a reader to judge a definition; it is not yet a
predictor of a correct one.

### 7.3 Faculties

**Refusal — moved, as a declared mode.** The sure and balanced modes are
refusal rules with stated operating points; neither is wired into an answer
yet. **Not derivation; not addressing.**

### 7.4 What is left

* Wire the modes into `continue` and the guarded predictor, with a label on
  each answer saying which mode gave it; that changes answers the evaluation
  pins and needs a frozen-path comparison.
* A calibration fold whose model is trained on as many documents as the
  held-out model's, so that coverage transfers (C1).
* State the sure bar as an absolute precision rather than a multiple of an
  accuracy that moves between folds (C3) — declared before it is measured.
* A definition grade that predicts agreement: the context support alone, the
  source tier, or the squared cosine of context sets (To-Do item 3).
* The quality description is computed beside `define`'s answers
  (`confidence_curve.quality`); `corpus --ask` does not print it yet.
* Folds by path digest are used here only; `corpus-knowledge` and the studies
  that read the old split still deal by position (To-Do item 6).

## In one paragraph

Partly. The balanced mode chosen on the calibration fold meets the bar Phase 154 missed on held-out text — 33.7% precision, 1.6 times the unguarded accuracy, at 42.4% coverage — and the order control falls to 3.3% under the same guard. The sure mode holds 62.0% precision at 7.3% coverage but misses its declared three-times bar narrowly, and the balanced mode's coverage moved by just over the declared tolerance between folds. Strong definitions agree with the held-out gloss only slightly more often than weak ones (4 of 15 against 2 of 8).

The figures: 6 of 8 marks; balanced guard `(1, 1/5)`: 33.7% at 42.4% held out (31.7% at 37.3% calibrated); sure guard `(2, 2/3)`: 62.0% at 7.3% held out, 2.95 times the unguarded 21.0%; candidate top three: 32.7% hit at 98.4%; C1 and C3 missed.
