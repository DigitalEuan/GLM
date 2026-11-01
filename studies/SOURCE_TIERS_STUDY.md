# Corpus source tiers — every corpus experiment read tier by tier, and how the supplied tier should count

## Tier 0 — the coarse read

**Question.** How much does each tier of the corpus contribute to the corpus experiments — and in particular the supplied tier (`source_material/` and the archived `GLM-main.zip`), which the owner's standing rule calls the less reliable — and how, if at all, should the supplied tier count?

**Verdict.** The supplied tier is worth far less than its size for the system's own text but is not noise, and of three declared ways to count it only the confirmed reading — admitting it only as a candidate that written evidence must confirm — raises precision on the system's own text.

**Deciding figure.** 7 of 8 marks and L1, 0 of 1 amended (T2 and T5′ missed); 2,268 documents, 1,036 supplied; leaving the supplied tier out costs the written test 1,971 right tokens, a size-matched pseudo-tier 9,629; the written tier alone 80,274 against 82,245 for the whole corpus; precision on written text under the K3′ guard: whole corpus 56.4%, supplied tier excluded 54.5%, confirmed reading 57.9% keeping 94.5% of the answers.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 31 October 2026. Reconstructed 31 October 2026 from the round records; the original was lost in the October 2026 reorganisation.* The original was written on 18 October 2026 (the date of the Phase 162 record); its pre-registration (§§0–6) was written before the measurement, and one amendment (T5′, §3.1) was declared after the first measurement and before the second. *Last altered 31 October 2026 (repository check): §7.6 rewritten — the module reconstructed, its test back and the measurement re-taken; later the same day re-taken again after a change to the reader's skip list (the stored Lean path made repository-relative), every mark as before.*

> **How this reconstruction was made.** From the Phase 162 record of
> [`MASTER_PLAN.md`](../MASTER_PLAN.md), the "corpus source tiers" row of
> [`SYSTEM.md`](../SYSTEM.md), §20.36 and the study table of
> [`GLM_ACADEMIC_PAPER.md`](GLM_ACADEMIC_PAPER.md), To-Do item 6 of
> [`STATUS.md`](../STATUS.md), the row of `tests/README.md` for
> `test_source_tiers.py` and the handler `_source_tiers` of `tools.py`. The
> records name the subjects of T2, T4, T5, T5′ and T8 and give every mark's
> outcome; the subjects of T1, T3, T6 and T7 and all the thresholds were not
> recorded anywhere that survived. No figure appears that the records do not
> give.

## 0. What this document is

A study for Phase 162, taken from the owner's plan of 19 October 2026
(`source_material/GLM_19OCT26_1.md`, Part II.7, *separate corpus source tiers
more clearly*), with the owner's standing rule that `source_material/` is the
less reliable tier.

A corpus reading is only as good as what it was read from, and nearly half the
corpus is supplied material: the older scripts and studies of `GLM-main.zip`
and the other files under `source_material/`. The corpus experiments of Phases
154 and 155 ([`CORPUS_KNOWLEDGE_STUDY.md`](CORPUS_KNOWLEDGE_STUDY.md),
[`CORPUS_DEFINITIONS_STUDY.md`](CORPUS_DEFINITIONS_STUDY.md)) read the corpus
whole. This round repeats them on five tiers — core documentation, code, Lean,
studies and reports, archived or supplied — and on three slices: the written
tier (everything the system's rounds wrote), the supplied tier, and both.

## 1. What was built

* **`RequestProject/GLM/SourceTiers.lean`** (no `sorry`; standard axioms): the
  model of the documents a predicate keeps plus the model of those it drops is
  the whole model (`train_filter_add`) — because the counted model is additive,
  the three slices are three readings of one model; counting a tier `k` times
  is training on `k` copies (`train_replicate`, `train_downweight`) and a
  positive common factor never changes the guarded prediction
  (`predict_smul`); the confirmed reading answers exactly when the whole corpus
  answers and the written tier has counted the word (`confirm_some_iff`), so
  every confirmed answer has a written witness (`confirm_witness`) and with no
  written evidence it refuses (`confirm_eq_none_of_no_written`).
* **`glm_universal/knowledge/source_tiers.py`**: the five tiers (`tier_of`),
  the census, next-token prediction by slice with each tier left out and a
  size-matched pseudo-tier as control, the four guarded policies, `define`,
  the glossary grade and word use by slice, and `source_tiers_report`.
* **`tools source-tiers [--write] [--json]`**; stored in
  `knowledge/_data/source_tiers.json` (the first measurement kept as
  `source_tiers_first.json`).

## 2. The control

A **size-matched pseudo-tier**: a blind draw of as many documents as the
supplied tier holds, left out in its place. What leaving the supplied tier out
costs is read against what leaving the pseudo-tier out costs.

## 3. The policies, and what is not claimed

Four guarded policies for the supplied tier on the K3′ majority guard of
[`CORPUS_KNOWLEDGE_STUDY.md`](CORPUS_KNOWLEDGE_STUDY.md): the whole corpus as
it is; the supplied tier **excluded**; the supplied tier **down-weighted** by
2 against the written tier (counting a tier `k` times is training on `k`
copies, `train_downweight`); and the **confirmed** reading, which admits the whole corpus's answer only when
the written tier has counted it. Nothing in the answering path changes in this
round: a policy is measured offline, not shipped.

### 3.1 The amendment (T5′)

Declared after the first measurement and before the second. Doubling the
written counts doubles the guard's support too, so down-weighting moved the
guard rather than the weighting. **T5′** re-reads the down-weighted policy with
its support counted unweighted.

## 4. Faculties

None of derivation, addressing or refusal moved for the GLM's answers (T8).
The round measured a refusal policy for the corpus offline — the confirmed
reading refuses 5.5% of the whole corpus's guarded answers and raises their
precision by 1.5 points — and did not ship it.

## 5. The marks

The wording of the marks is lost; the column gives the result each surviving
record attaches to the mark.

| mark | what the records attach to it |
|---|---|
| **L1** | `SourceTiers.lean` builds with no `sorry`, standard axioms |
| **T1** | not recorded |
| **T2** | the written tier alone predicts the written test as well as the whole corpus (predicted to hold) |
| **T3** | not recorded |
| **T4** | leaving the supplied tier out costs the written test less than leaving out a size-matched pseudo-tier |
| **T5** | a declared policy for the supplied tier raises precision on written text under the guard (the confirmed reading) |
| **T6** | not recorded |
| **T7** | not recorded |
| **T8** | no answer of the GLM moves |
| **T5′** | the down-weighted policy, its support counted unweighted (amended) |

The parts of the measurement whose marks are not recorded are the census by
tier, the supplied test, `define`, the glossary grade and word use by slice.

## 6. How it is measured

`python3 -m glm_universal.tools source-tiers` prints the census by tier,
prediction by slice and with each tier left out, the pseudo-tier, the four
policies on the written and the supplied test, `define` and the glossary by
slice, and the marks; `--write` re-takes the measurement. The held-out rule
takes every fifth document of the sorted corpus. Tests:
`tests/test_source_tiers.py` (8), run by hand: 8 of 8 passed (pytest was not
installed).

## 7. What came out

### 7.1 The marks

| mark | recorded result | outcome |
|---|---|---|
| **L1** | built with no `sorry`; standard axioms | met |
| **T1** | (subject not recorded) | met |
| **T2** | written test: the whole corpus 82,245 of 346,777 tokens, the written tier alone 80,274 — the supplied tier helps a little | missed |
| **T3** | (subject not recorded) | met |
| **T4** | the supplied tier out costs 1,971, a size-matched pseudo-tier 9,629 | met |
| **T5** | the confirmed reading 57.9% precision keeping 94.5% of the answers, against 56.4% for the whole corpus | met |
| **T6** | (subject not recorded) | met |
| **T7** | (subject not recorded) | met |
| **T8** | no answer moved | met |
| **T5′** | down-weighted with unweighted support 55.4% | missed |

**7 of 8 marks and L1, 0 of 1 amended.** (The outcomes of T1, T3, T6 and T7
follow from the recorded count: of the eight T marks seven were met and T2 is
the one named as missed.)

### 7.2 The census and the prediction

2,268 documents, 1,036 in the supplied tier (46% of sentences, 39% of tokens).
On the written test the whole corpus predicts 82,245 of 346,777 tokens and the
written tier alone 80,274; leaving the supplied tier out costs 1,971, a
size-matched pseudo-tier 9,629. On the supplied test the supplied tier alone
beats the whole corpus (42,225 against 41,206).

The supplied tier is worth far less than its size for the system's own text but is not noise, and of three declared ways to count it only the confirmed reading — admitting it only as a candidate that written evidence must confirm — raises precision on the system's own text.

### 7.3 The three ways of counting the supplied tier

Under the K3′ guard on written text: whole corpus 56.4% precision; supplied
tier excluded 54.5%; down-weighted by 2 54.6% (and more answers — doubling the
counts doubles the guard's support); down-weighted with unweighted support
55.4% (T5′ missed); confirmed 57.9%, keeping 94.5% of the answers (T5). Every
confirmed answer has a written witness and nothing resting on the supplied tier
alone is confirmed (`confirm_witness`, `confirm_eq_none_of_no_written`).

### 7.4 `define`, the held-out sets, and the owner's instructions

`define` answers 45 of 60 bold terms, 41 of them from written sentences and 4
from supplied sentences — all four where the written rival is a stored
measurement quoting an earlier answer.

The held-out sets of the two measurements differ (written test 290,779 →
346,777 positions) because the held-out rule takes every fifth document of the
sorted corpus, so three new documents re-dealt the folds; every mark had the
same outcome both times.

Two instructions of the owner, given on 18 October 2026 with this round, were
carried out beside it:

* *Keep `source_material/GLM-main.zip` and the two supplied PDFs in the
  project folder, as they are.* They stay there, untouched and out of version
  control; `.gitignore` says so in a comment, and `STATUS.md` §2.0 states it as
  a standing rule. This settled the item Phase 161 left to the owner
  ([`STUDY_LEDGER_STUDY.md`](STUDY_LEDGER_STUDY.md) §7.4).
* *Date files from now on if they are altered or created.* Directive D17 in
  [`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md), a row of the close
  checklist (`ITERATE.md` §4.1), a standing rule in `STATUS.md` §2.0, and an
  instrument: `glm_universal/corpus/dates.py`, `tools dates`, which lists every
  stamp and fails on a stamp that is not a date, lies after today, or says a
  file was altered before it was made.

**What it invalidated.** The new Lean file added two queries to the
Lean-address sets, so the two evaluation cases that pin exact counts
(`report-relay`: 685 → 689 of 853, the gate on 58 of 1706; `report-anonymous`:
685 → 54 and 154 → 153 of 853) were re-pinned, their claims unchanged, and the
measurements that digest the case file were re-taken, every mark as before.
D17 moved the text of `report-directives` (the count of standing rules,
16 → 17); it was declared as a cause in the frozen-path comparisons that read
it, and those were re-taken. The evaluation then ran 222 of 222.

### 7.5 What is left

* Ship the confirmed reading behind a frozen-path comparison: putting it into
  the continuation and the guarded predictor, with a label on every answer that
  rests on the supplied tier, changes answers the evaluation pins.
* `define`'s rank for stored data files (whether a stored measurement should be
  a definition source at all).
* A held-out rule that does not re-deal when the corpus grows (folds by the
  digest of the path).
* The other corpus readers by tier: `similar`, the word address, context sets
  and the respeller's vocabulary.
* A guard read in the units of its decision, so that a down-weighting can keep
  precision.

### 7.6 State of the files at this reconstruction (31 October 2026)

*Rewritten 31 October 2026 (repository check); the earlier text of this
section described the stub that stood here on 29 October.*

`knowledge/source_tiers.py` was lost in the October 2026 reorganisation and
has been **reconstructed** from §1–§6 of this study (its docstring says so):
the five tiers by path, the three slices of one additive model, prediction by
slice on the Phase 154 held-out rule, each tier left out against a
size-matched pseudo-tier, the four policies under the K3′ guard, and `define`
by slice. `tests/test_source_tiers.py` is back (8 tests, passing), and the
stored measurement `knowledge/_data/source_tiers.json` has been **re-taken**
on the corpus as it now stands (2,199 documents, 615 of them in the supplied
tier, against the 2,268 and 1,036 of §7.2 — the reorganisation moved most of
the supplied material). `SourceTiers.lean` is still missing (recorded in
[`_lean_files_needed.md`](_lean_files_needed.md)).

What the re-take shows, beside the record of §7.1:

| re-taken | 31 October 2026 | beside the record |
|---|---|---|
| **L1** | `SourceTiers.lean` not in the tree | open: the record says built |
| **T1, T3, T6, T7** | their subjects were not recorded anywhere that survived (§5), so they cannot be measured | open: the record counts them in its seven |
| **T2** | written test: the whole corpus 91,787 of 447,207 tokens, the written tier alone 91,519 — the supplied tier still helps a little | as recorded (the mark's condition fails) |
| **T4** | the supplied tier out costs 268, a size-matched pseudo-tier 2,766 | as recorded (the condition holds) |
| **T5** | the confirmed reading 55.4% precision keeping 95.3% of the answers, against 53.4% for the whole corpus | as recorded (the condition holds) |
| **T8** | needs the evaluation's frozen-path comparison, not run by the module | open: the record says no answer moved |
| **T5′** | down-weighted with unweighted support against the whole corpus | differs: the condition holds here and failed in the record |

**2 of 9 marks met, 1 of 1 amended** in the stored file
(`python3 -m glm_universal.tools source-tiers` reads it). The three marks the
reconstruction can measure and the record states (T2, T4, T5) come out the
way the record says; the amended T5′, missed in the record, is met in the
re-take; the four unrecorded subjects, L1 and T8 are open, not
failed. The figures of §7.1–§7.5 are the Phase 162 record and are kept as it;
the re-take does not reproduce them digit for digit, because the corpus and
the module are not the ones they were taken on.

## In one paragraph

Phase 162 reads every corpus experiment on five tiers and on the written tier,
the supplied tier and both; because the counted model is additive the split
is exact (`train_filter_add`). The supplied tier holds 1,036 of 2,268
documents and 39% of the tokens, but leaving it out costs the written test
only 1,971 right tokens where a blind draw of as many documents costs 9,629;
it is not noise, though — the written tier alone does slightly worse (80,274
against 82,245; T2 missed). Of three declared ways to count it, excluding and
down-weighting lose precision on written text (54.5%, 54.6%, and 55.4% with
unweighted support; T5′ missed), while the confirmed reading raises it to
57.9% and keeps 94.5% of the answers; every confirmed answer has a written
witness. Nothing in the answering path changed. With this round the owner set
two rules: the supplied zip and PDFs stay as supplied, outside version
control, and every file a round creates or alters carries its date (D17).
7 of 8 marks and L1, 0 of 1 amended.
