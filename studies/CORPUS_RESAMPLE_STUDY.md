# The declared resampling: are the native rankings' small leads effects or draws?

## Tier 0 — the coarse read

**Question.** When the Lean corpus loses any one of its files, or the query sample is drawn at any other offset of its stride, which of the native rankings' small leads over the standard ones still hold?

**Verdict.** One lead is an effect: the two-book native ranking ahead of the raw structural vector on the declaration queries; every other resampled reading, the shipped words mark W2 included, is a draw as stated, and the declared control failed.

**Deciding figure.** 1 effect among 18 reading-and-set pairs (`native2` ≥ `features` on the declarations, holding in 99.4 % of 171 file drops and 95.5 % of 22 stride offsets, census discordance 185 : 29); the control `native2` = `features2` holds in 88.3 % and 77.3 %; 6 of 7 marks met (M4 not met).

**Recomputed by.** `glm_universal.reasoning.corpus_resample.corpus_resample_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

Round 9 of the order of work in [`STATUS.md`](../STATUS.md) §3.4, retrieval,
opens with candidate N1: *a declared resampling of the Lean corpus (every
sub-corpus that drops one file), to say whether the single-book figures of
[`NATIVE_PARITY_STUDY.md`](NATIVE_PARITY_STUDY.md) and the post-hoc readings
of [`NATIVE_WORDS_STUDY.md`](NATIVE_WORDS_STUDY.md) §3.3 are draws or
effects.* Both studies re-read their marks at the close of five later phases,
and several of them flipped by one query as the corpus grew. Each re-reading
was one draw. This round takes all the draws at once.

## 1. The objects

* **The census.** Every addressed declaration of the Lean corpus that has a
  relative, asked as a query: once as a *declaration query* (its stored
  structural and lexical addresses, its statement's tokens) and once as a
  *goal query* (the statement read as a free goal, addressed live), exactly as
  `retrieval.declaration_query_report` and `retrieval.goal_query_report` ask
  them. For each query and each ranking the census keeps the ranked
  candidates far enough down (the largest file's size plus ten) that the top
  ten of any sub-corpus that drops one file can be read off it.
* **A sub-corpus.** The corpus without every declaration of one Lean file `F`.
  Its candidates are the declarations outside `F`; its relatives are the
  full relatives with `F` removed; its query sample is drawn the way the
  system draws one, `query_sample`, over the sub-corpus (the stride
  `len // 200` for declarations and `len // 100` for goals, every query with
  at least one relative left).
* **Every ranking here is a sort by a strict total order** (the name is the
  last key), so the ranking of a sub-corpus is the full ranking with `F`'s
  declarations filtered out. That is proved, not assumed (§5), and checked
  against a direct re-ranking (mark M2).
* **What is held fixed.** A declaration's structural address counts how many
  results it cites and how many cite it, over the whole development. When
  `F` is dropped, a declaration outside `F` that cites or is cited by `F`
  would have a different count. The census keeps every address as the full
  development computed it, so a sub-corpus differs from a re-built corpus in
  those addresses only; the count is priced (mark M5) rather than hidden.

## 2. Declarations — written before any measuring code

**The two families of resamples.**

* **File drops (`F`)** — the 170 sub-corpora, one per Lean file, each with its
  query sample re-drawn over it.
* **Stride offsets (`S`)** — on the whole corpus, the query sample drawn at
  every offset `o` of its stride (`names[o::stride]`), `o = 0` being the
  sample the studies read. The offsets are disjoint and together they are
  the census.

**The readings resampled.** Each is a comparison of two rankings on one
query set (declarations, goals), in hits at `k ∈ {1, 3, 5, 10}`:

| id | reading | where it came from |
|---|---|---|
| a | `letters` ≥ `text` at every `k` | native words §3.3, post hoc |
| b | `letters` ≥ `parts` at every `k` | native words §3.3, post hoc |
| c | `words_native` ≥ `text` at every `k` and in MRR@10 | native words W2, the shipped mark |
| d | `words_native` ≥ `text_parts` at every `k` | native words §3.3, post hoc |
| e | `words_native` ≥ `text_leech` at `k = 5` | native words W4 |
| f | `text_leech` ≥ `text` at every `k` | native words W6 |
| g | `native` ≥ `features` at every `k` and in MRR@10 (declarations) | native parity N1 |
| h | `native` ≥ `features` at every `k` (goals) | native parity N2 |
| i | `native2` ≥ `features` at every `k` | native parity N6 |
| j | `native2` = `features2` in hits at every `k` | native parity N7, a control |

**The rule, declared now.** For each reading on each query set, the *share*
of a family is the fraction of its resamples in which the reading holds as
stated. On the census, the *discordance* at `k = 5` is the pair `(b, c)`:
queries the first ranking hits and the second misses, and the reverse; its
exact two-sided sign-test value is `min(1, 2 · Σ_{i ≤ min(b,c)} C(b+c, i) / 2^(b+c))`,
computed as a fraction.

* **effect** — the share is at least 95 % in both families;
* **effect against** — the opposite reading (the second ranking at least the
  first, at every `k` named) has a share of at least 95 % in both families;
* **draw** — anything else.

The sign test is reported beside each verdict and does not change it: the
census queries share a corpus and are not independent draws.

**Marks.**

| mark | what it requires |
|---|---|
| M1 | the engine is faithful: on the whole corpus at offset 0, every ranking's hits at every `k` and MRR@10 equal those of `native_words.lean_report` and of `native_parity.declaration_report` / `goal_report` |
| M2 | the filter is exact: for five declared files (the largest, the smallest, and the files at the first, middle and last position of the sorted list), every query of that sub-corpus's declaration sample ranked directly over the sub-corpus gives the same top ten as the filtered census, for every ranking |
| M3 | every resample is scored: 170 file drops, every stride offset of both query sets, the query count of each recorded, and the census covering every declaration with a relative |
| M4 | a verdict for every reading on every query set under the declared rule; the control `j` holds in every resample |
| M5 | the held-fixed addresses priced: for every file, the number of declarations outside it whose structural feature vector a rebuilt sub-corpus would change, with the largest and the total |
| M6 | the facts the method rests on proved in Lean without `sorry`: a sort by a strict total order commutes with dropping candidates; the stride offsets partition the census; the sign-test values the study prints |
| M7 | nothing earlier moves: the native-words and native-parity measurements and their marks as they were |

**Prediction, written now.** `j` holds everywhere (the two rankings' keys
are equal when the read-back is exact, `GLM.NativeParity.take_map_primary_eq`).
`i` is an effect: the second book carries information about the query, and
its lead was several queries at every re-reading. `g`, `h`, `e` and `f` are
draws: each compares two orders inside exact ties of one key, and each has
already flipped at a re-reading. `c` is likely a draw at `k = 1` and so a draw
as stated, though ahead at most `k`. For `a`, `b` and `d` there is no
prediction: these are the post-hoc readings the round exists to settle.

**What would count as moving the target (D15).** None of the three faculties.
The round decides which of the retrieval figures already recorded are
results and which are draws; it changes no ranking. A reading found to be a
draw un-states a claim, which is refusal of a kind, but at the level of the
record, not of the machine.

**Wiring, declared now.** No default changes whatever the verdicts: the
shipped document ranking rests on the document mark W3, which this round does
not resample (the documents are not a Lean corpus). The verdicts are written
into the two studies they bear on, beside the readings they settle, and a
test pins each verdict that is an effect.

## 3. What was built

* [`reasoning/corpus_resample.py`](../overlay/glm_universal/reasoning/corpus_resample.py):
  the census (every declaration of the pool asked as a declaration query and
  as a goal query under the ten rankings, each kept 108 places down), the two
  families, the declared rule, the sign test, and the marks' own checks. The
  census runs on every core up to eight (`GLM_RESAMPLE_JOBS=1` makes it
  serial; the rows come back in the declared order either way) and takes
  about twenty minutes; the summary is stored in
  `reasoning/_data/corpus_resample.json` beside the digest of the measuring
  code, like the native-words cache.
* The command `python3 -m glm_universal.tools corpus-resample` (`--write`,
  `--json`, `--live`), `tests/test_corpus_resample.py` and
  `RequestProject/GLM/CorpusResample.lean`.
* Nothing in the native-words or native-parity modules, their caches, the
  retrieval module or the address books was changed by this round's code.

## 4. Results

Measured by `PYTHONPATH=. python3 -m glm_universal.tools corpus-resample`
over the tree as it stood when the measurement was taken: 4,572
declarations in 171 Lean files, every one with a relative, so the census is
4,572 declaration queries and 4,572 goal queries. The declaration said 170
files; the 171st is this round's own Lean file, written before the
measurement. The stride is 22 for the declarations (22 offsets of 207 or 208
queries) and 45 for the goals (45 offsets of 101 or 102); the 171 file drops
re-draw samples of 204 to 208 and 101 to 103 queries.

### 4.1 The verdicts

*file drops* and *offsets* are the shares of each family in which the reading
holds as stated; *opposite* is the share in which the second ranking is at
least the first at every cut-off named; *census at 5* is the discordance
(first only : second only) over all 4,572 queries.

| id | reading | set | file drops | offsets | opposite (drops / offsets) | census at 5 | verdict |
|---|---|---|---|---|---|---|---|
| a | `letters` ≥ `text` | declarations | 18.1 % | 40.9 % | 22.8 % / 4.5 % | 161 : 94 | **draw** |
| a | `letters` ≥ `text` | goals | 21.1 % | 33.3 % | 5.3 % / 8.9 % | 140 : 92 | **draw** |
| b | `letters` ≥ `parts` | declarations | 6.4 % | 9.1 % | 11.1 % / 31.8 % | 44 : 59 | **draw** |
| b | `letters` ≥ `parts` | goals | 9.4 % | 13.3 % | 55.6 % / 31.1 % | 49 : 57 | **draw** |
| c | `words_native` ≥ `text` (W2) | declarations | 77.2 % | 77.3 % | 0.0 % / 0.0 % | 129 : 33 | **draw** |
| c | `words_native` ≥ `text` (W2) | goals | 87.1 % | 62.2 % | 0.6 % / 4.4 % | 109 : 30 | **draw** |
| d | `words_native` ≥ `text_parts` | declarations | 35.1 % | 18.2 % | 11.7 % / 36.4 % | 23 : 40 | **draw** |
| d | `words_native` ≥ `text_parts` | goals | 19.9 % | 24.4 % | 12.3 % / 22.2 % | 31 : 34 | **draw** |
| e | `words_native` ≥ `text_leech` at 5 (W4) | declarations | 60.2 % | 59.1 % | 75.4 % / 72.7 % | 42 : 53 | **draw** |
| e | `words_native` ≥ `text_leech` at 5 (W4) | goals | 86.0 % | 64.4 % | 66.1 % / 66.7 % | 47 : 49 | **draw** |
| f | `text_leech` ≥ `text` (W6) | declarations | 46.8 % | 81.8 % | 0.0 % / 0.0 % | 138 : 31 | **draw** |
| f | `text_leech` ≥ `text` (W6) | goals | 50.9 % | 46.7 % | 1.8 % / 2.2 % | 111 : 30 | **draw** |
| g | `native` ≥ `features` (N1) | declarations | 20.5 % | 18.2 % | 1.2 % / 18.2 % | 72 : 50 | **draw** |
| h | `native` ≥ `features` (N2) | goals | 46.8 % | 20.0 % | 9.9 % / 28.9 % | 47 : 60 | **draw** |
| i | `native2` ≥ `features` (N6) | declarations | 99.4 % | 95.5 % | 0.0 % / 0.0 % | 185 : 29 | **effect** |
| i | `native2` ≥ `features` (N6) | goals | 96.5 % | 93.3 % | 0.0 % / 0.0 % | 162 : 28 | **draw** |
| j | `native2` = `features2` (N7) | declarations | 88.3 % | 77.3 % | — | 3 : 0 | **fails** |
| j | `native2` = `features2` (N7) | goals | 83.0 % | 75.6 % | — | 2 : 2 | **fails** |

The census sign-test values, proved by the kernel in
`GLM.CorpusResample.census_signs_small`, `census_sign_d_declarations`,
`census_signs_large` and `census_signs_control`: below `10^-4` for `a` on the
declarations and below `1/500` on the goals; below `10^-13` and `10^-11` for
`c`; below `10^-16` and `10^-11` for `f`; below `10^-28` and `10^-23` for `i`;
between 0.042 and 0.043 for `d` on the declarations (against the native
ranking); above 0.05 for `g` and above 0.1 for `b`, `d` on the goals, `e` and
`h`; 1/4 and 1 for the control.

### 4.2 The marks

| mark | outcome |
|---|---|
| M1 | **met**: offset 0 on the whole corpus gives every ranking's hits at every cut-off and MRR@10 exactly as `native_words.lean_report` and `native_parity.declaration_report` / `goal_report` do — 0 mismatches over 20 ranking-and-set rows |
| M2 | **met**: for `Gen3.lean` (the largest), `RateRepair.lean` (the smallest, first by name among the three-declaration files), `Address.lean`, `MeasurandRegister.lean` and `ZeroStorageV5.lean` (first, middle and last by name), 1,034 queries ranked directly over the sub-corpus under all ten rankings: 0 top tens differ from the filtered census |
| M3 | **met**: 171 file drops, 22 and 45 offsets covering the census exactly once, 4,572 census queries, every resample with its query count recorded and none empty |
| M4 | **not met**: a verdict for every reading on every set, but the control `j` does not hold in every resample (§4.3) |
| M5 | **met**: with nothing dropped the rebuilt feature vectors equal the stored ones (0 differ); 167 of the 171 file drops would change at least one structural feature vector outside the file, 12,541 in all, the largest 1,880 (dropping `Heisenberg.lean`) — §4.4 |
| M6 | **met**: `RequestProject/GLM/CorpusResample.lean` builds without `sorry`, on the standard axioms only |
| M7 | **met**: the native-words and native-parity modules, their stored measurements and the retrieval module are untouched by this round's code |

6 of 7 marks met.

### 4.3 The control that failed, and why the prediction was wrong

The prediction said `j` holds everywhere because `native2` and `features2`
agree on their keys. They agree on their **first two** keys only: when every
read-back is exact, the structural and lexical read-back distances are the
raw distances. The third key differs — the lexical Leech distance for
`native2`, the name for `features2` — so inside a tie of the first two keys
the two rankings may put different candidates at the cut-off, and a hit can
move. `GLM.NativeParity.take_map_primary_eq` says two such rankings carry the
same *costs* in every prefix, not the same *candidates*; the study of Phase 70
read its query-for-query equality at one draw and stated it as if it were the
theorem. Measured, the two differ in at most a few queries: the census
discordance is 3 : 0 and 2 : 2, and at every cut-off `native2` has at least
`features2`'s hits in at least 91 % of each family. The control is a near
identity, not an identity, and M4 is recorded as not met.

### 4.4 What the held-fixed addresses hide: a citation leak

M5 was expected to be small, because a file's citations are local. It is not,
and the reason is a defect in the citation index rather than in this round.
`lean_address.citation_index` resolves a token to a declaration by its short
name when that short name is unique. Ten declarations have a short name of
one letter (`GLM.Heisenberg.a`, `GLM.QuestionSetBMatrix.A`, `B` and `C`,
`GLM.Sakuma.e` and `V`, `GLM.GolayHex.w`, `GLM.QuestionSetBAnswers.H`,
`GLM.Q`, `GLM.Y`), so every bound variable `a`, `A`, `e`, … in any statement
or proof is read as a citation of one of them. On the measured tree 3,231 of
the 15,012 citation edges (21.5 %) point at those ten, and 2,448
declarations carry at least one such edge; `GLM.Heisenberg.a` alone is
"cited" by 1,920. Dropping `Heisenberg.lean` removes that sink, which is why
it moves 1,880 feature vectors. Two things read the citation graph and so
carry the leak: the `cites` and `cited by` coordinates of every structural
address, and the relevance sets themselves (`retrieval.relative_table` counts
a citation in either direction as relevance). So `GLM.Heisenberg.a` is
counted as a relative of every declaration that names a variable `a`. Every
Lean-corpus retrieval figure of the project is taken under that relevance,
this round's included; the comparisons between rankings are fair (both sides
are scored against the same sets), but the absolute hit rates are inflated
by an amount nobody has measured. It is the same kind of leak as item 5 of
`STATUS.md` §3.4 — a name creeping into a reading that is meant to be
structural — and it is named for the next round (§7) rather than repaired
here, because repairing it moves every relevance set and every figure that
rests on one.

### 4.5 Reported beside the rule, post hoc

These per-cut-off shares were added after the first reading of the verdicts,
to say *where* each "every `k`" reading fails. They are not part of the
declared rule. Each cell is the share of file drops / offsets in which the
first ranking has at least the second's hits at that cut-off.

| id | set | k = 1 | k = 3 | k = 5 | k = 10 |
|---|---|---|---|---|---|
| a | declarations | 56.7 % / 54.5 % | 73.1 % / 81.8 % | 42.7 % / 86.4 % | 53.2 % / 86.4 % |
| a | goals | 33.3 % / 57.8 % | 81.9 % / 77.8 % | 91.8 % / 75.6 % | 91.8 % / 77.8 % |
| b | declarations | 81.9 % / 45.5 % | 17.5 % / 36.4 % | 63.7 % / 50.0 % | 35.1 % / 50.0 % |
| b | goals | 41.5 % / 60.0 % | 34.5 % / 51.1 % | 77.2 % / 64.4 % | 75.4 % / 64.4 % |
| c | declarations | 82.5 % / 77.3 % | 99.4 % / 100.0 % | 93.6 % / 100.0 % | 100.0 % / 100.0 % |
| c | goals | 90.1 % / 75.6 % | 97.1 % / 88.9 % | 98.8 % / 93.3 % | 98.2 % / 100.0 % |
| d | declarations | 91.2 % / 63.6 % | 67.3 % / 54.5 % | 81.3 % / 45.5 % | 55.0 % / 68.2 % |
| d | goals | 75.4 % / 77.8 % | 75.4 % / 55.6 % | 44.4 % / 60.0 % | 92.4 % / 84.4 % |
| e | declarations | 90.6 % / 72.7 % | 78.9 % / 54.5 % | 60.2 % / 59.1 % | 19.9 % / 54.5 % |
| e | goals | 85.4 % / 75.6 % | 86.0 % / 48.9 % | 86.0 % / 64.4 % | 90.1 % / 66.7 % |
| f | declarations | 48.5 % / 81.8 % | 99.4 % / 100.0 % | 95.3 % / 100.0 % | 100.0 % / 100.0 % |
| f | goals | 57.9 % / 55.6 % | 98.2 % / 91.1 % | 96.5 % / 95.6 % | 97.1 % / 100.0 % |
| g | declarations | 98.2 % / 77.3 % | 79.5 % / 68.2 % | 32.7 % / 72.7 % | 86.5 % / 59.1 % |
| h | goals | 91.8 % / 68.9 % | 87.7 % / 71.1 % | 83.6 % / 57.8 % | 61.4 % / 62.2 % |
| i | declarations | 99.4 % / 95.5 % | 100.0 % / 100.0 % | 100.0 % / 100.0 % | 100.0 % / 100.0 % |
| i | goals | 100.0 % / 100.0 % | 98.2 % / 95.6 % | 98.8 % / 97.8 % | 99.4 % / 97.8 % |
| j | declarations | 98.2 % / 95.5 % | 100.0 % / 100.0 % | 100.0 % / 100.0 % | 98.2 % / 95.5 % |
| j | goals | 99.4 % / 95.6 % | 97.7 % / 91.1 % | 98.2 % / 95.6 % | 99.4 % / 97.8 % |

Three readings follow, each post hoc:

* **The shipped words mark W2 fails at `k = 1` and holds elsewhere.**
  `words_native` has at least the standard's hits at `k = 3, 5, 10` in at
  least 88.9 % of every family, and the census discordance at 5 is 129 : 33
  and 109 : 30. What moves is the top rank. The live document ranking rests
  on the document mark W3, which this round does not resample, so nothing
  shipped changes.
* **The Leech tie-break W6 is the same shape**: ahead at `k ≥ 3` almost
  everywhere (census 138 : 31), behind at `k = 1` in about half the file
  drops (51.5 % on the declarations, 42.1 % on the goals) — which is what the
  Phase 71 reading saw.
* **The two families disagree where the stride sample is particular.**
  Every file drop re-draws the offset-0 sample shifted by at most one file's
  length, so the 171 file-drop samples overlap heavily and share the
  offset-0 sample's character; the 22 offsets are disjoint. Reading `a` at
  `k = 5` holds in 42.7 % of file drops and 86.4 % of offsets, and the
  census favours `letters` 161 : 94: `letters` gets more hits at 5 than the
  standard over the whole corpus, and fewer on the sample the studies read.
  A future resampling should treat the file-drop family as dependent on its
  base offset (file drops at every offset would be 3,762 resamples, all read
  off the same census).

### 4.6 The verdict, in words

One lead is an effect: the two-book native ranking ahead of the raw structural vector on the declaration queries; every other resampled reading, the shipped words mark W2 included, is a draw as stated, and the declared control failed.

The effect is reading `i` (N6). On the goals the same
lead holds in 96.5 % of file drops and 93.3 % of offsets, just short of the
declared 95 %, so it is a draw by the rule. Every other resampled reading is a
draw as stated, the shipped words mark W2 included — it fails at the top rank
while its lead at 3, 5 and 10 is near-universal. The post-hoc readings of the
native-words study are not effects: `letters` ahead of `text` and of `parts`,
and `words_native` at least `text_parts`, each hold in under half of each
family; `letters` against `parts` and `words_native` against `text_parts` lean
the other way on the census (44 : 59 and 23 : 40). The single-book marks N1
and N2 are draws, as Phase 70 said they were. And the declared control
failed: `native2` and `features2` are a near identity, not an identity.

## 5. The Lean file

`RequestProject/GLM/CorpusResample.lean` proves, on the standard axioms only:

* `sorted_perm_filter_eq`, `take_sorted_perm_filter_eq` — a list sorted by
  an order that admits no pair both ways (a strict order with the name last)
  and holding exactly the candidates of the filtered full ranking *is* the
  filtered full ranking: dropping a file commutes with ranking.
* `length_filter_take_ge`, `take_filter_take` — if at most `m` candidates are
  dropped, the top `k` of the filtered ranking are read off its first `k + m`
  places: the census depth of 108 (largest file 98, plus 10) is enough.
* `stride_slice_iff`, `stride_offsets_card`, `stride_offsets_disjoint` —
  Python's `names[o::s]` is the remainder class `o`, and the offsets
  partition the census.
* `signTest`, `signTest_symm`, `signTest_le_one`, and the printed values
  `census_signs_small`, `census_sign_d_declarations`, `census_signs_large`,
  `census_signs_control`, checked by the kernel.

## 6. Wiring

No default changes, as declared. The verdicts are written beside the
readings they settle, in [`NATIVE_WORDS_STUDY.md`](NATIVE_WORDS_STUDY.md) and
[`NATIVE_PARITY_STUDY.md`](NATIVE_PARITY_STUDY.md), and
`tests/test_corpus_resample.py` pins the one effect, the control's failure,
and that none of the post-hoc readings is an effect.

## 7. What this leaves

* **The citation leak (§4.4).** A citation index that does not resolve a
  bound variable to a one-letter declaration — resolving short names only
  when the token is not bound in the statement, or not at all below some
  length — then every relevance set and every retrieval figure re-taken under
  it, with the old figures kept as a record. It is item 5's kind of leak and
  belongs with it.
* **File drops at every offset**, to separate the two kinds of draw the
  families mix (§4.5); read off the same census, it costs no new ranking.
* **The goal half of N6** sits at 93.3 % of offsets; a resampling of a larger
  goal sample would say whether it is an effect.
* **N2, N5 and I3** of the retrieval round are untouched.
