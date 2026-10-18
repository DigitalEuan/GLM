# Friction: what holds when the question moves, and contact over the whole prompt

## Tier 0 — the coarse read

**Question.** Read through the owner's analogy of friction — tiny peaks and valleys that interact when there is movement — which of the GLM's functions hold when the question is moved a little, does a continuation that touches the whole prompt predict the next word better than the two-word patch, and does a reading that sticks until the evidence clearly beats it change its mind less without reading worse?

**Verdict.** The GLM holds still under small surface movements and, when moved further, mostly sticks (refuses) rather than slips (answers wrongly); the survey found two openings that slipped or stuck — doubled spaces and a leading *can you tell me* — and `GLM.py` now settles both, after which no perturbed run slips; contact over the whole prompt carries a real but small signal that helps only when loaded under the two-token count, and static friction removes a reading's flip-flops but not its informative changes of mind.

**Deciding figure.** 5 of 12 marks, 5 of 9 amended marks, 3 of 4 fix marks; after the fix 1,136 of 1,291 perturbed runs hold and 0 slip (938 and 7 before, refusals read as refusals).

**Recomputed by.** `glm_universal.knowledge.friction_study.friction_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 156 (§§0–6 are committed before any stored
measurement is taken; §7 is what came out). The owner asked for a round of
experiments that gives a fuller picture of what does and does not work
functionally in the GLM, and named an analog worth trying: **friction**, where
the tiny peaks and valleys of two surfaces (asperities) interact once there is
movement. Three experiments read the analogy in three places. Each one is
stated as a mechanism, a control and pass marks, and nothing in any of them
samples or uses a float.

1. **The survey — sliding the questions** (F1–F4). Every case of the
   end-to-end evaluation is a question resting in a valley the parser was built
   for. Move it a little — a question mark, a capital, a polite prefix, a
   transposed letter, a dropped *the* — and see whether the answer **holds**
   (static grip), **sticks** (the machine refuses where it answered: the
   motion was stopped), or **slips** (a confident answer that is wrong, or an
   answer where it refused: it slid into the wrong valley). Per kind and per
   perturbation this is the map of what works and what does not.
2. **Contact — the whole prompt touching** (C1–C4). The counted model
   continues a phrase from its last two tokens: a contact patch of two
   asperities, which is why so many phrases slide into the same deep valley
   (*"a table is" → "the same way"*). Bowden and Tabor's observation is that
   friction follows the *real* area of contact — the sum over every asperity
   that touches — not the apparent patch. The contact reading keeps the
   candidates the two-token patch offers and weights each by how many of the
   prompt's content words it is associated with in the corpus.
3. **Stick-slip — a reading that holds** (S1–S4). A reading of a sentence
   word by word commits, at every word, to the folder of the corpus the
   sentence most likely comes from. Without friction the reading jumps at
   every change of the leader; with static friction it holds until another
   folder beats the held one by a declared margin (the Prandtl–Tomlinson
   picture: the tip stays in its well until the drive exceeds the barrier).
   The question is whether the held reading changes its mind much less
   without ending worse.

## 1. What is built

* `overlay/glm_universal/knowledge/friction.py` — the hold-out model, the
  patch and contact predictors, the continuation under both, the folder
  evidence and the two readers.
* `overlay/glm_universal/knowledge/friction_survey.py` — the perturbations
  and the survey over the evaluation's cases.
* `overlay/glm_universal/knowledge/friction_study.py` — the marks and the
  stored measurement (`_data/friction.json` and `_data/friction_survey.json`,
  each beside the digest of the code that took it).
* `python3 -m glm_universal.tools friction [--write] [--survey]` — the
  instrument.
* `RequestProject/GLM/Friction.lean` — what is proved before the measurement
  (§5).

## 2. The rules, fixed before the measurement

### 2.1 The survey

* **The cases.** Every case of `glm_universal.evaluation.CASES`, run through
  `GLM.py` in a fresh interpreter and scored by the evaluation's own harness
  (`evaluation.harness.run_case`), unperturbed (the **base**) and under each
  perturbation that applies.
* **The perturbations**, each a fixed function of the question text:

  | id | class | perturbation | applies when |
  |---|---|---|---|
  | `qmark` | surface | append `?` | the question does not end in `?` |
  | `capital` | surface | capitalise the first letter | the first character is a lower-case letter |
  | `spaces` | surface | every single space doubled | the question has a space |
  | `please` | lexical | prefix `please ` | always |
  | `tellme` | lexical | prefix `can you tell me ` | always |
  | `typo` | lexical | swap the second and third letters of the longest alphabetic word of at least five letters (the first such word on a tie) | such a word exists and the swap changes it |
  | `drop_the` | lexical | delete the first standalone word `the` | the question contains it |

* **The outcomes.** A perturbed run of a case that passes at base is scored
  by the same criteria as the case: **hold** if it passes; **stick** if the
  case expects an answer and the run refuses; **slip** if the run is a wrong
  answer or an error (for a case that expects a refusal, an answer). Cases
  that do not pass at base are reported and excluded from the rates.

| # | mark | pass |
|---|---|---|
| F1 | slips on the cases that expect a refusal | at most 1% of their perturbed runs |
| F2 | the surface perturbations hold | at least 90% of their runs |
| F3 | the lexical perturbations hold | at least 50% of their runs |
| F4 | slips over every perturbed run | at most 2% |

### 2.2 Contact

* **The held-out sentences.** A corpus sentence qualifies when it is not a
  heading, not inside a tier-0 block, has at least 8 tokens of which at least
  6 are alphabetic and at least 4 are content words (`model.is_content`), and
  its token sequence occurs exactly once in the corpus. With `Q` qualifying
  sentences in corpus order, the sample is every `k`-th, `k = max(1, Q //
  1000)`, starting from the first, cut at 1000.
* **The hold-out.** The counts of every sampled sentence (n-gram rows, window
  pairs, unigrams, tokens) are subtracted from the corpus model; both
  predictors read only the subtracted model. Because the sentence occurs once,
  nothing of it survives the subtraction.
* **The patch predictor** (the frictionless reading, today's `predict`): the
  deciding row is the two-token row of the last two tokens if it is non-empty,
  else the one-token row; the answer is the row's unique most frequent
  continuation, and a tie is a refusal.
* **The contact predictor.** The same deciding row; its 32 most frequent
  continuations (ties at the cut by spelling) are the asperities tall enough
  to touch. For candidate `c` with row count `R(c)`, `A(c)` is the number of
  distinct content words `p ≠ c` of the prefix with window count `n(p,c) ≥ 2`
  that are associated with `c` (`model.associated`, both on the subtracted
  model). The score is `R(c)·(1 + A(c))`; the unique maximum answers, a tie
  refuses.
* **The task.** For every sampled sentence and every position `j` from 2 to
  its length minus 1, predict token `j` from tokens `0..j-1`. A prediction is
  **correct** when it equals the token.
* **The mismatched control.** The contact predictor with the prefix's content
  words taken from the next sampled sentence (the last from the first), cut to
  the same number of tokens: the same reweighting toward associated words, but
  by the wrong prompt.
* **The continuation.** For every sampled sentence, the first 3 tokens are the
  prompt; each predictor continues it greedily for at most 12 tokens, stopping
  at the sentence end, a refusal or a recurring two-token context (as
  `answer.continue_text`); the contact continuation's prefix words are the
  prompt's and the continuation's own. Overlap with the truth is the size of
  the multiset intersection with tokens `3..14` of the held-out sentence.

| # | mark | pass |
|---|---|---|
| C1 | contact against patch | more correct predictions in total, and more sentences on which contact is correct more often than on which patch is |
| C2 | contact against the mismatched control | contact's gain over patch is at least twice the control's (or the control gains nothing and contact gains) |
| C3 | contact does not buy its answers by guessing | contact's precision (correct over answered) is at least the patch's |
| C4 | continuation | summed overlap with the held-out truth is larger under contact, and contact gives at least 1.25 times as many distinct continuations |

### 2.3 Stick-slip

* **The sentences.** The sample of §2.2.
* **The folders.** A sentence's folder is the top folder of its document
  (`reader.top_folder`); `F` is the number of folders.
* **The evidence, without the sentence itself.** For a content word `p` and a
  folder `f`, `n(p,f)` is the number of corpus sentences of `f` containing
  `p`, minus one in the sentence's own folder when `p` is in the sentence. A
  word's **height** is `F − (number of folders with n(p,f) > 0)`: a word found
  everywhere touches nothing. After `t` tokens the score of `f` is the summed
  height of the distinct content words read so far with `n(p,f) > 0`.
* **The leader** after `t` tokens is the highest-scoring folder, ties by
  folder name; the reading starts at the first `t` with a positive score.
* **The frictionless reader** reads the leader at every `t`. **The sticking
  reader** holds its reading and moves to the leader only when
  `4·S(leader) > 5·S(held)`: the leader must beat the held folder by a
  quarter. Margins of an eighth and a half are reported beside it as a curve;
  the marks read the quarter.
* **Measured.** A *switch* is a change of reading between consecutive tokens;
  a *return* is a switch back to a folder the reading had held before in the
  same sentence; the *final reading* is the reading after the last token.

| # | mark | pass |
|---|---|---|
| S1 | the sticking reader never switches more than the frictionless one | on every sentence (it is proved, §5; the mark checks the implementation) |
| S2 | fewer switches | the sticking reader's total is at most 70% of the frictionless total |
| S3 | no worse at the end | the sticking reader's final reading is correct on at least as many sentences as the frictionless one's, less 1% of the sentences |
| S4 | fewer returns | at most half the frictionless total |

### 2.4 Amended marks, declared after the first measurement and before the second

The first measurement (§7; kept as `_data/friction_first.json` and
`_data/friction_survey_first.json`) met F2, C4, S1, S3 and S4 and missed F1,
F3, F4, C1, C2, C3 and S2. Every miss is kept as a miss. Three facts read off
the first measurement shape the amendments, and are stated before any of them
is measured:

* **19 of the 26 survey slips are scored `error` by the harness, with an
  empty answer.** The harness reads an `ANSWER` or `UNSOLVED` line; the
  stepwise planner refuses with a `REFUSED …` line, which it does not read.
  Those runs may be refusals the harness cannot see, not wrong answers.
* **The contact weight `1 + A(c)` overturns the row too often**: contact
  answers 1,051 more positions than the patch but is correct on 75 fewer.
* **The folder reader barely moves**: with 5 top folders the frictionless
  reader switches 263 times over 800 read sentences, so there is little for
  static friction to remove.

The amended readings, each reported beside the original and never in its
place:

* **Refusals read as refusals (F1′, F4′).** Every survey run scored `error`
  is run again through `GLM.py` and its output kept; a run whose output has a
  line beginning `REFUSED` and no `ANSWER` line is re-scored as a refusal
  (a stick, or a hold for a case that expects a refusal). Nothing else is
  re-scored. F1′ and F4′ are F1 and F4 on the re-scored runs.
* **Contact as a tie-break (C1′).** The friction picture: the row count is the
  load-bearing contact and the prompt's asperities matter only where the
  surfaces are level. The patch answers wherever it is decided; where its
  deciding row ties at the maximum, the tied candidates are ordered by `A(c)`
  and a unique maximum answers. C1′: the tie-break's gain in correct
  predictions over the patch is positive and at least twice the gain of the
  same tie-break driven by the mismatched prompt.
* **Loaded contact (C2′, C3′).** The score `R(c)·(L + A(c))` with the load
  `L = 8` over the same 32 candidates: the asperities can overturn a lead of
  at most `(L + |P|)/L`. C2′ is C1 and C3′ is C3 for the loaded score.
* **The directory reader (S1′–S4′).** The reader of §2.3 with a sentence's
  folder taken as its directory (`Sentence.folder`, 138 directories) instead
  of its top folder; everything else as declared. S1′–S4′ are S1–S4 for it.

| # | mark | pass |
|---|---|---|
| F1′ | F1, refusals read as refusals | at most 1% |
| F4′ | F4, refusals read as refusals | at most 2% |
| C1′ | contact as a tie-break | positive gain, at least twice the mismatched tie-break's |
| C2′ | loaded contact against patch | as C1 |
| C3′ | loaded contact's precision | as C3 |
| S1′ | directory reader, never more switches | every sentence |
| S2′ | directory reader, fewer switches | at most 70% |
| S3′ | directory reader, no worse at the end | as S3 |
| S4′ | directory reader, fewer returns | at most half |

### 2.5 The fixes the survey points to, declared before they are measured

The second measurement (§7) re-scored all 19 `error` runs as planner
refusals and left 7 slips, every one from the `tellme` prefix: six read the
*me* of *tell me* as the dimension symbol `M` (*"can you tell me meaning of
water" → 'me' denotes dimension M*) and one read *tell* as a carrier of the
`angle` kind. The `spaces` perturbation sticks on 21 of 222 cases and the
`tellme` prefix on 159. Two fixes are declared, both in `GLM.py`, at the one
place a question enters the batch and the interactive loop
(`settle_question`):

* **Runs of spaces and tabs are one space**, and the question is stripped, in
  a question of one line that holds no quotation mark or back-quote (a program
  or quoted text passes untouched, because its spacing can be its meaning).
* **A leading *tell me* is a courtesy**: after any of the courtesy openings
  the parser already strips (*please*, *could you*, *can you*, *would you*,
  *kindly*), the words *tell me* are dropped unless *about*, *whether* or *if*
  follows them (*tell me about X* is the parser's weak describe opening, and
  *tell me whether* is read by the planner).

The marks, against the evaluation run before the edit and the survey run
again after it (`_data/friction_survey_settled.json`):

| # | mark | pass |
|---|---|---|
| X1 | frozen path | every one of the 222 evaluation cases gives the same outcome and the same answer line after the edit as before it |
| X2 | `spaces` after the edit | holds on at least 98% of its runs |
| X3 | `tellme` after the edit | holds on at least 90% of its runs, with no slip |
| X4 | nothing else moves the wrong way | no perturbation has more slips (refusals read as refusals) or fewer holds after the edit than before |

## 3. What would count against

* F1/F4 missed: a small movement of a question can carry the machine into a
  confident wrong answer, which the evaluation's fixed wording never shows.
* F2/F3 missed: the parser's valleys are narrow; questions work only as
  written.
* C1–C3 missed: touching the whole prompt does not help the counted model
  choose its next word, or helps only by answering more and worse.
* C4 missed: the deep valleys of the continuation are not a matter of contact
  area.
* S2/S4 missed: the frictionless reader's changes of mind are not noise a
  margin removes; S3 missed: the margin keeps it in wrong wells.

## 4. What is not claimed

* **The analogy is a lens, not a physical model.** No friction coefficient is
  fitted and no claim is made about tribology; the analogy chooses the
  mechanisms, the controls decide whether they help.
* **The survey's perturbations are a declared seven**, not the space of
  rewordings; a perturbation that does not apply to a question is not run.
* **The prediction task is in-corpus text with the sentence held out**, not
  text from outside the project.

## 5. What is proved before the measurement

`RequestProject/GLM/Friction.lean`:

* a reader that at each step either keeps its reading or moves to the leader
  changes its reading no more often than the leader changes
  (`held_switches_le`) — so S1 is a theorem about any margin;
* the sticking reader's held folder is always within the margin of the
  leader: `q·S(leader) ≤ (q+1)·S(held)` at every step (`held_within_margin`);
* the contact score never overturns a lead in the row larger than the factor
  `1 + |P|`, for `P` the prompt's content words (`contact_keeps_large_lead`),
  and with an empty prompt it ranks exactly as the patch does
  (`contact_empty_prompt`).

## 6. Files

See §1. Tests: `overlay/glm_universal/tests/test_friction.py`.

## 7. What came out

Three measurements were taken, in this order: the first (§§2.1–2.3, kept as
`_data/friction_first.json` and `_data/friction_survey_first.json`); the
second, with the amended readings of §2.4 beside the originals
(`_data/friction.json`, `_data/friction_survey.json`); and, after the edit of
§2.5, the survey again (`_data/friction_survey_settled.json`) with the
frozen-path comparison (`_data/friction_frozen_path.json`). The corpus
figures below are the stored second measurement (2,209 documents, 217,774
sentences; the corpus is the project's own text, so the first measurement's
sample differs from it by a few sentences and its figures by a few counts:
patch 4,281, contact 4,206, mismatched 4,164 there). The survey's figures
were identical in the first and second runs.

**Marks.** 5 of 12 marks: F2, C4, S1, S3, S4 met; F1, F3, F4, C1, C2, C3, S2
missed. 5 of 9 amended marks: F1′, F4′, C2′, S1′, S4′ met; C1′, C3′, S2′, S3′
missed. 3 of 4 fix marks: X2, X3, X4 met; X1 missed as worded (§7.4).

### 7.1 The survey — what holds when the question moves

All 222 evaluation cases pass unperturbed. Of the 1,291 perturbed runs:

| perturbation | runs | hold | stick | slip | after the fix: hold / stick / slip |
|---|---|---|---|---|---|
| `qmark` | 211 | 211 | 0 | 0 | 211 / 0 / 0 |
| `capital` | 217 | 217 | 0 | 0 | 217 / 0 / 0 |
| `spaces` | 222 | 197 | 21 | 4 | 222 / 0 / 0 |
| `please` | 222 | 222 | 0 | 0 | 222 / 0 / 0 |
| `tellme` | 222 | 47 | 159 | 16 | 222 / 0 / 0 |
| `typo` | 196 | 40 | 151 | 5 | 41 / 155 / 0 |
| `drop_the` | 1 | 0 | 0 | 1 | 1 / 0 / 0 |
| **all** | 1,291 | 934 | 331 | 26 | 1,136 / 155 / 0 |

(The last column reads refusals as refusals; before the fix, so read, the
totals are 938 hold, 346 stick and 7 slip.)

* **Surface motion holds** (F2 met: 625 of 650). A question mark, a capital
  and the courtesy *please* never move an answer; doubled spaces did (21
  sticks, 4 slips).
* **Lexical motion mostly sticks** (F3 missed: 309 of 641). The machine's
  failure under motion is a refusal, not a guess: 331 sticks against 26 slips
  as declared.
* **The slips, read.** As declared, 26 slips, 5 of them on cases that expect a
  refusal (F1 missed: 5 of 268; F4 missed: 26 of 1,291, just over 2%). 19 of
  the 26 are runs the harness scores `error` because it reads no `ANSWER` or
  `UNSOLVED` line; re-run (§2.4), every one of the 19 is a `REFUSED` line from
  the stepwise planner — a refusal the harness cannot see. With them read as
  refusals, 7 slips remain (F1′ met: 1 of 268; F4′ met: 7 of 1,291), and all
  7 come from the `tellme` prefix: six answer *'me' denotes dimension M*
  (*"can you tell me meaning of water"*, *"… relate energy work"*, *"… meaning
  of justice"*, which should be refused), and one reads *tell* as a carrier
  (*"can you tell me angle PbCl2 water" → angle tell electron_mass*).
* **By kind**, the `report` subjects stick most (153 of 414 runs: a report
  name with a typo or behind *can you tell me* is not read), and `verify`,
  `meaning` and `compare` held the slips.

### 7.2 Contact — the whole prompt touching

1,000 held-out sentences, 19,533 predicted positions.

| predictor | correct | answered | precision | against patch |
|---|---|---|---|---|
| patch (two-token row) | 4,312 | 16,850 | 25.6% | — |
| contact `R·(1+A)` | 4,201 | 17,821 | 23.6% | −111 (wins 204, losses 239) |
| contact, mismatched prompt | 4,122 | 17,570 | 23.5% | −190 |
| tie-break (§2.4) | 4,509 | 18,196 | 24.8% | +197 |
| tie-break, mismatched prompt | 4,459 | 17,980 | 24.8% | +147 |
| loaded `R·(8+A)` (§2.4) | 4,515 | 18,166 | 24.9% | +203 (wins 194, losses 52) |
| loaded, mismatched prompt | 4,428 | 17,932 | 24.7% | +116 |

* **Full contact hurts** (C1, C2, C3 missed): the factor `1 + A(c)` lets a
  candidate touching many prompt words overturn a much better row answer.
* **The prompt carries a real but small signal.** Every contact variant beats
  its own mismatched control — by 79 positions (full), 50 (tie-break) and 87
  (loaded) — so it is the actual prompt that helps, not only a pull toward
  content words. But most of the gain of the tie-break and the loaded score is
  that generic pull: the mismatched prompt earns 147 of the tie-break's 197
  (C1′ missed).
* **Loaded contact helps at full coverage** (C2′ met: +203, wins 194 against
  losses 52), and buys it by answering more: its precision is below the
  patch's (C3′ missed).
* **The continuation leaves the deep valley** (C4 met): summed overlap with the
  held-out truth 744 against 619, and 628 distinct continuations against 469.
  The patch's four most common non-empty endings are all *"… same way"*
  (*the same way*, *same way*, *of the same way*, *is the same way*: 109 of
  1,000 prompts); contact's most common non-empty ending is *same way*, on 24. But contact finds **new valleys of its own**: its prefix grows with
  the words it generates, so a continuation that touches itself reinforces
  itself — *"the two words agrees with the declared cases of phase 55"* is
  produced 17 times. In the friction picture this is wear debris: the contact
  makes its own third body.

### 7.3 Stick-slip — a reading that holds

| reader | top folders (5; 793 read) switches / returns / final correct | directories (138; 1,000 read) switches / returns / final correct |
|---|---|---|
| frictionless | 264 / 3 / 370 | 766 / 15 / 272 |
| stick 1/8 | 260 / 1 / 368 | 677 / 4 / 260 |
| stick 1/4 (the marks) | 253 / 1 / 365 | 552 / 1 / 232 |
| stick 1/2 | 227 / 0 / 355 | 386 / 1 / 199 |

* **S1 and S1′ hold on every sentence**, as `held_switches_le` says they must.
* **Static friction removes the flip-flops** (S4, S4′ met: returns 3 → 1 and
  15 → 1) **but few of the switches** (S2 missed: 253 of 264; S2′ missed: 552
  of 766, 72%, just past the 70% mark).
* **Where the reading moves, holding costs accuracy** (S3 met for the 5
  folders, 365 against 370; S3′ missed for the directories, 232 against 272).
  The reader's changes of mind are mostly *information* — a later word really
  does point elsewhere — and a margin that holds the earlier reading keeps it
  in the wrong well. A margin earns its place only where the leader's
  fluctuations are noise; on this task, apart from the returns, they are not.

### 7.4 The fixes

`GLM.py` now settles a question before reading it (`settle_question`, §2.5).

* **X1, the frozen path, missed as worded.** `settle_question` returns all 222
  evaluation questions unchanged, the 222 cases pass before and after, and no
  outcome changed; but one answer line differs: `corpus address of seven`
  reports the squared distance to *six* as 2976 where it had been 3040. The
  question is not touched by the edit; the difference is the corpus itself,
  which is the project's own text and gained this study between the two runs.
  The mark asked for identical lines, and it is recorded as missed.
* **X2 met**: `spaces` holds on 222 of 222 (197 before).
* **X3 met**: `tellme` holds on 222 of 222 (47 before), with no slip; the six
  *'me' denotes dimension M* answers are gone.
* **X4 met**: no perturbation has more slips or fewer holds than before.
  Over all perturbed runs, 1,136 of 1,291 hold and 0 slip.

### 7.5 What does and does not work, read through the analogy

The GLM holds still under small surface movements and, when moved further, mostly sticks (refuses) rather than slips (answers wrongly); the survey found two openings that slipped or stuck — doubled spaces and a leading *can you tell me* — and `GLM.py` now settles both, after which no perturbed run slips; contact over the whole prompt carries a real but small signal that helps only when loaded under the two-token count, and static friction removes a reading's flip-flops but not its informative changes of mind.

* **High static friction, little slip** — the machine's design (refuse rather
  than guess) shows under motion: after the fix there is no slip in 1,291
  moved questions, and every remaining failure is a refusal.
* **The remaining friction is lexical**: a transposed letter sticks 155 of
  196 questions. That is the next thing to move (§7.6, item 1).
* **Contact is a load-bearing idea only under load**: the two-token count must
  carry the weight, and the prompt's asperities adjust it. At full strength
  they overturn good answers; loaded, they help at full coverage.
* **Friction against noise, not against information**: the margin is the
  right tool for flip-flops and the wrong one for a reading that is moving for
  a reason.

### 7.6 Left open

1. **Typos** stick 155 of 196 moved questions. A *did you mean* that reads a
   word both by spelling and by use (the word address of Phase 155, words used
   like the unknown one) is the candidate; it changes refusals the evaluation
   pins, so it needs a frozen-path comparison.
2. **The harness cannot read a `REFUSED` line**: 19 runs of the survey were
   planner refusals scored as errors. Teaching the harness the marker changes
   no current case (all pass) but changes how future failures are scored.
3. **Contact's own valleys**: a continuation that reads its own words as
   prompt reinforces itself. Wear — a used asperity counted down as it is
   used — is the next reading to declare.
4. **A margin that knows the noise**: the sticking reader with a margin set
   from how much the leader's score fluctuates, rather than a fixed fraction.

## 8. The method: analogy as a development tool (the owner's note)

*Added in Phase 158 at the owner's request; it records the intent behind this
study, and changes no mark above.*

The friction study was not only a test of the GLM under small movements. It
was a test of a **method**: when a development problem is stuck, borrow a
well-established mathematical or physical system whose behaviour is already
understood, and apply it *in the way that works for the GLM* — not as a
metaphor laid over the machine, but as a source of mechanisms, controls and
pass marks that can be written down before anything is measured. Here the
borrowed system was friction: asperities (the two-token contact patch against
the real area of contact, after Bowden and Tabor), stick and slip (refusal
against a confident wrong answer), static friction (the Prandtl–Tomlinson
margin of a reading that holds), wear. Each part of the analogy became one
experiment with its own control, and the analogy also said in advance what
each failure would *look like* (sticking, slipping, a self-made valley),
which is what made the survey's map readable.

What the method contributes, read from this study and
[`FRICTION_TWO_STUDY.md`](FRICTION_TWO_STUDY.md):

* **Vocabulary for outcomes before they happen.** *Holds / sticks / slips*
  gave every perturbed run one of three declared readings, and the design rule
  (refuse rather than guess) became the measurable claim "high static
  friction, little slip".
* **Candidate mechanisms with known limits.** The established system brings
  its own known failure modes; wear, for instance, was predicted by the
  analogy and then measured not to touch the valley it was meant to wear
  (Phase 157), which located the valley in the two-token row instead.
* **A boundary on what transfers.** An analogy is used where its structure
  matches and stopped where it does not; the margin worked against noise and
  not against information, which is exactly the boundary the analogy draws
  between a jitter and a drive.

**Using it in future rounds.** When a round is stuck on a design question,
name the established system the problem resembles, write down which of its
parts map to which parts of the GLM and which do not, and turn each mapped
part into a declared mechanism with a control and a mark. Phase 158
([`OSCILLATOR_JUNCTION_STUDY.md`](OSCILLATOR_JUNCTION_STUDY.md)) is the first
round to use it deliberately after friction: the reference circle of classical
mechanics decides which angular quantity an oscillator may share across a
junction.
