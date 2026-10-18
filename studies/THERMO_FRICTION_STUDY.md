# Thermomechanical friction: a governor that heats, an anchor across a gradient, and a vocabulary that sinters

## Tier 0 — the coarse read

**Question.** Can measured friction be used as a signal for recovery: does a heat-gated taboo on repeated bigrams move the continuation out of its self-made valley, does a prompt/generated-context gradient tell signal dilution from a change of subject well enough to anchor the directory reader to its prompt, and does a bounded fallback to a register lexicon read back a technical word the corpus barely uses without loosening ordinary correction?

**Verdict.** Friction is a useful sensor in all three experiments but an actionable one in only one: sintering the register vocabulary ships, reading back 727 of 735 misspelt register words and the survey's *mlilisecond* question, with ordinary misspellings no worse, no register word respelt where the shipped respelling changed 45, and no evaluation outcome moved; the heat-gated governor almost never acts, because the self-made valley is a basin many prompts fall into once each, not a phrase one continuation re-enters; and the prompt anchor costs a little where it acts, because at a hot step the words read after the prompt name the right directory more often than the prompt does.

**Deciding figure.** 13 of 19 marks (A3, A5, A7, B2, B3, B4, B5, C1, C2, C3, C4, C5, C6 met; A1, A2, A4, A6, B1, B6 missed) and 1 of 1 amended (B6′ met); sintering ships.

**Recomputed by.** `glm_universal.knowledge.thermo_friction_study.thermo_friction_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 159 (§§0–6 are committed before any code of
the round is written; the evaluation run the frozen path compares against,
`_data/thermo_friction_eval_before.json`, was taken before that commit; §7 is
what came out). It takes Part I of the owner's plan of 19 October 2026
([`source_material/GLM_19OCT26_1.md`](../source_material/GLM_19OCT26_1.md)),
which `STATUS.md` §2.0 maps onto To-Do item 4 (friction, the third pass): the
three lines Phase 157 left ([`FRICTION_TWO_STUDY.md`](FRICTION_TWO_STUDY.md)
§7.7, items 1–3).

**The method, by analogy** ([`FRICTION_STUDY.md`](FRICTION_STUDY.md) §8). The
established system is **thermomechanics**: a body under friction heats, and
heat does work — a bimetallic strip bends and opens a contact, a temperature
difference across a junction drives a current, and a powder held hot enough
fuses into a solid. The analogy is used to design measurable mechanisms, not
as a claim that the GLM holds energy. What maps:

| thermomechanics | the GLM | experiment |
|---|---|---|
| temperature of a body | concentration of the continuation row: the top count against the five tallest | A |
| bimetallic strip: bends when hot, rests when cold | a taboo on re-entering a recent bigram, applied only when the row is hot, harder the longer it has been hot | A |
| thermocouple: a current from a temperature *difference* | the disagreement between the folder evidence of the prompt and of the words read after it | B |
| the current closes a relay for the next reading | the prompt's evidence counted twice at a step where the gradient is high | B |
| sintering: a temporary liquid phase fuses grains, then the body is solid again | a respelling that refuses opens, once, a curated register lexicon, and closes again | C |

What does not map: nothing is conserved (no energy balance), nothing is
continuous, and nothing samples; every quantity is a count compared by
integer or exact rational arithmetic.

The three experiments are judged **independently**: a miss in one says
nothing about the others, and each ships or does not on its own marks.

## 1. What is built

* `overlay/glm_universal/knowledge/thermo_friction.py` — the governor (A) and
  the anchor reader (B), over Phase 156's held-out sample, hold-out model,
  continuation and directory evidence
  (`overlay/glm_universal/knowledge/friction.py`), imported and not modified.
* `overlay/glm_universal/runtime/respell.py` — the sintered reading (C): a
  new mode beside the four of Phase 157, and the register lexicon it opens
  (`runtime/_data/register_lexicon.json`, built from the registers).
* `overlay/glm_universal/knowledge/thermo_friction_study.py` and
  `python3 -m glm_universal.tools thermo-friction [--write]` — the marks and
  the stored measurement (`knowledge/_data/thermo_friction.json`).
* `RequestProject/GLM/ThermoFriction.lean` — what is proved (§5).
* `GLM.py` — the re-read uses the sintered reading **only if** C1–C4 are met
  (§2.3); otherwise it keeps Phase 157's `loaded` reading.

## 2. The rules, fixed before the measurement

Every experiment reads Phase 156's sample (the 1,000 held-out sentences of
`friction.sample`) on the corpus model with their counts subtracted; the
corpus is the one current when the measurement is taken, and its digest is
stored beside it.

### 2.1 Experiment A — the bimetallic governor

**The row and its heat.** At each step of a continuation the deciding row is
Phase 156's (the two-token row if non-empty, else the one-token row), and its
candidates are its 32 tallest continuations with their counts `R(c)`
(`friction.tallest`). Let `R₁ ≥ R₂ ≥ …` be those counts. The row is **hot**
when `2·R₁ ≥ R₁ + R₂ + R₃ + R₄ + R₅` (the top candidate holds at least half of
the five tallest; with fewer than five candidates, of those there are), and
**cold** otherwise. The **heat level** `h` of a step is the number of hot rows
met so far in the continuation, this one included.

**The recent bigrams.** The history is the prompt followed by the produced
words (no sentence-start padding); its **recent window** is its last 8 tokens.
A candidate `c` **repeats** when the bigram `(b, c)`, `b` the last token of
the history, already occurs as two adjacent tokens of the recent window.

**The governor.** Over the patch score `R(c)`: at a cold row, or for a
candidate that does not repeat, the score is `R(c)`; at a hot row, a repeating
candidate scores `R(c) / (1 + h)` (exact rationals). The unique maximum
answers; a tie refuses. The continuation is otherwise Phase 156's
(`friction.continuation`): 3-token prompts, at most 12 tokens, and the stops
*cycle* (an exact two-token state met again), *refusal*, *end* and *limit*.

**The comparisons** (all on the same 1,000 prompts):

* **patch** — the two-token row's unique maximum (`friction.patch_predict`);
* **contact** — Phase 156's `R(c)·(1 + A(c))`;
* **static taboo** (the control) — every repeating candidate scores
  `R(c) / 2`, hot or cold;
* **governor** — as above;
* **contact governor**, reported beside and never marked — the governor's
  penalty over the contact score instead of the patch score.

**What is measured.** For each: the most frequent non-empty continuation and
its count; the summed overlap with the held-out truth (the multiset
intersection with the sentence's next 12 tokens, `friction.overlap`); the
number of distinct continuations; the stops. On the sentences where the
governor's continuation differs from the patch's, the overlap of each there
(the quality of what changed). And, at every position of every held-out
sentence (`friction.predict_positions`, the history being the sentence's own
tokens), the number of positions answered and answered correctly: precision
(correct / answered) and coverage (answered / positions).

| # | mark | pass |
|---|---|---|
| A1 | the valley | the governor's most frequent non-empty continuation occurs at most half as often as the patch's |
| A2 | not traded for wrong text | the governor's summed overlap with the truth is at least the patch's |
| A3 | no narrower | the governor gives at least as many distinct continuations as the patch |
| A4 | heat earns its place | the governor's summed overlap and its position precision are each at least the static taboo's |
| A5 | cold rows untouched | at every cold row met in any continuation, the governor's choice is the patch's (the implementation checked against §5) |
| A6 | precision kept | the governor's position precision is at least the patch's |
| A7 | terminates cleanly | every governor continuation ends within 12 tokens on one of the four declared stops |

### 2.2 Experiment B — the thermoelectric prompt anchor

Phase 156's directory reader (the 138 directories,
`friction.FolderEvidence(…, "directory")`, `friction.leaders`): a content word
read for the first time adds its height (the number of directories it is
absent from) to every directory holding it, the sentence itself not counted.

**Cold side and hot side.** The **prompt words** of a sentence are its first
3 distinct content words in reading order; every content word read after them
is a **generated** word. `P(f)` is the score directory `f` has from the prompt
words, `G(f)` from the generated words, so the frictionless score is
`S(f) = P(f) + G(f)`.

**The gradient.** At a step (a token after which some `S` is positive), the
prompt leader `p` is the directory of largest `P` and the generated leader `g`
the directory of largest `G` (the first by name on a tie; each only when its
score is positive somewhere). When both exist and differ, the **gradient** is
`Γ = (P(p) − P(g)) + (G(g) − G(p))` — how much each side prefers its own
leader over the other's; otherwise `Γ = 0`. The step is **hot** when `Γ > 0`
and `4·Γ ≥ S(ℓ)`, `ℓ` the frictionless leader.

**The anchor reader.** At a cold step it reads the frictionless leader; at a
hot step it reads the directory of largest `2·P(f) + G(f)` (the first by name
on a tie): the prompt counted twice, for that reading only.

**The comparisons**: the frictionless reader; the fixed quarter margin of
Phase 156 (`stick 1/4`); the noise-set reader `r/8` of Phase 157; the anchor
reader; and the **mismatched anchor** (the control) — the same reader, hot at
the same steps, but at a hot step reading the largest `P'(f) + P(f) + G(f)`,
where `P'` is the score the *next* sample sentence's prompt words give: the
same extra weight, on the wrong prompt.

A **hot sentence** is one with at least one hot step. A switch **into the
truth** is a switch whose new reading is the sentence's own directory.

| # | mark | pass |
|---|---|---|
| B1 | recovery where it is hot | on the hot sentences, the anchor reader's final reading is correct on more sentences than the frictionless reader's |
| B2 | no worse overall | the anchor reader's final readings are correct on at least as many sentences as the frictionless reader's, less 1% of the sentences read (N2's bar) |
| B3 | fewer noise switches | the anchor reader makes no more switches and no more returns than the frictionless reader |
| B4 | informative changes kept | the anchor reader's switches into the truth are at least 90% of the frictionless reader's |
| B5 | inactive when they agree | at every cold step the anchor reader reads the frictionless leader, and no step whose prompt and generated leaders agree is hot (the implementation checked against §5) |
| B6 | the wrong prompt is weaker | on the hot sentences, the mismatched anchor's final reading is correct on fewer sentences than the anchor reader's |

### 2.3 Experiment C — sintering the register vocabulary

**The solid state** is Phase 157's shipped respelling (`loaded`: spelling,
then document count, then use where the count ties), over the corpus
vocabulary (a word in at least 3 documents).

**The register lexicon.** Every carrier name of the physics register (660
quantities), the element register (118 names), the interval register (28) and
the comparison classes (45), lower-cased, each whole name and each of its
underscore-separated parts of at least 4 letters, keeping only entries made of
lower-case letters and underscores. It is stored in
`runtime/_data/register_lexicon.json` beside the digest of the code and the
registers it was read from.

**The protected class.** A token is **protected** — never respelt by
sintering — when it holds a digit, or a capital letter after its first
character (an identifier, a literal, a formula). A token **has a word's
shape** when it is not protected and is made of letters and underscores only.

**The sintered reading.** As `loaded`, with two changes:

1. a lexicon entry is a known word (it is never respelt);
2. when `loaded` leaves an unknown token unchanged (no corpus candidate, or a
   tie that remains), and the token has a word's shape, the lexicon entries
   one optimal-string-alignment edit from it (lower-cased) are its
   candidates; a unique candidate is taken, replayed on the original's case
   as in Phase 157 (`respell.replay`); several, or none, leave it unchanged.

So sintering can act only on a token the solid state refused, and returns to
the solid state for the next token.

**The recovery set.** Every lexicon entry that the corpus vocabulary does not
know, perturbed by the survey's typo (`friction_survey._typo`: its second and
third letters swapped, entries of at least 5 characters), where the swap
changes it and leaves it unknown to both vocabularies; each read as a
one-token question.

| # | mark | pass |
|---|---|---|
| C1 | recovery | the sintered reading restores at least 80% of the recovery set and turns at most 2% into a different word |
| C2 | ordinary misspellings kept | on the 196 typo questions and on the 338 short-word questions of Phase 157, the sintered reading restores at least as many as `loaded` and turns no more into a different question |
| C3 | register words left alone | no lexicon entry, written correctly as a one-token question, is changed by the sintered reading |
| C4 | the protected class | on every protected token of every evaluation question, and on each such token perturbed by the survey's typo, the sintered reading gives the same token as `loaded` |
| C5 | the survey's blind spot | `gram : mass :: mlilisecond : ?` is answered by `GLM.py` after the round |
| C6 | frozen path | every one of the evaluation cases gives the same outcome after the round as before it, and every answer line is the same except for lines whose difference is traced to the corpus the answer reads |

**Shipping.** `GLM.py`'s re-read takes the sintered reading if and only if
C1–C4 are met; C5 and C6 are read after that decision.

### 2.4 The amended control of experiment B, declared after the first measurement and before the second

The first measurement of experiment B (§7; kept as
`_data/thermo_friction_first.json`) met B1–B5 and missed B6: the mismatched
anchor's final reading was correct on *more* hot sentences than the anchor's
(198 against 184 on 441 hot sentences in the stored first measurement; the
197 first written here was read off an unstored run of the same code on the
corpus before this round's modules had entered it). B6 stands missed. One fact read off the sample, stated
before the amended control is measured: Phase 156's sample takes every k-th
qualifying sentence in corpus order, so neighbours in the sample are
neighbours in the corpus, and **880 of the 1,000 sentences share their
directory with the next sample sentence** (886 in the measurement of record). The control as declared therefore
adds, nine times in ten, the prompt of another sentence of the *same*
directory: it is not the wrong prompt but a second right one, and it leaks
the answer.

* **B6′** — B6 with the mismatched prompt taken from the first sample
  sentence after it (cyclically) whose directory differs from its own; the
  anchor reader, the hot steps and every other mark are unchanged. Reported
  beside B6, never in its place.

| # | mark | pass |
|---|---|---|
| B6′ | the wrong prompt is weaker, amended | on the hot sentences, the mismatched anchor (a prompt from another directory) is correct at the end on fewer sentences than the anchor reader |

## 3. What would count against

* A1 missed with A5 met: the valley is not a matter of re-entering a recent
  bigram — the continuation is drawn into it from many prompts, not trapped
  in it from one. A2 or A4 missed: the governor buys diversity with wrong
  text, or heat does not tell the rows where a taboo helps.
* B1 missed: the gradient does not mark signal dilution; B4 missed: anchoring
  suppresses the informative changes; B6 missed: the extra weight helps
  whatever prompt it comes from, so it is the weight, not the anchor.
* C1 missed: register words are not misspelt one edit away from a unique
  entry; C2–C4 missed: the fallback loosens correction.

## 4. What is not claimed

* No energy, temperature or conservation law is claimed of the GLM; the names
  are the analogy's, the quantities are counts.
* A and B are measured on one sample of held-out corpus sentences; C on the
  declared perturbation only. A mechanism that misses here is not shown
  useless elsewhere, only not adopted on this evidence.
* The register lexicon is read from the registers; a technical word no
  register names is outside it.

## 5. What is proved before the measurement

`RequestProject/GLM/ThermoFriction.lean`:

* **the governor rests when cold** — at a cold row the governor's scores are
  the base scores (`governor_cold`), so its choice is the base's; and the
  taboo never raises a score (`taboo_le`);
* **a leader that does not repeat is kept** — if the base's unique maximum is
  not a repeating candidate, it is the governor's unique maximum at any heat
  (`governor_keeps_unrepeated_leader`);
* **the anchor is inactive when the two sides agree** — if one directory leads
  both the prompt scores and the generated scores (first by name on ties), it
  leads every positive mixture `w·P + v·G`, so the anchored reading and the
  frictionless reading are the same directory (`anchor_agree_leader`), and the
  gradient there is zero (`gradient_agree`);
* **sintering never takes the solid reading away** — the fallback is consulted
  only when the solid state refuses, and a solid answer is kept whatever the
  lexicon holds (`sinter_keeps_solid`, `sinter_refuses_iff`).

## 6. Files

See §1. Tests: `overlay/glm_universal/tests/test_thermo_friction.py`.

## 7. What came out

Taken in this order: the evaluation run before the round
(`_data/thermo_friction_eval_before.json`, before the pre-registration was
committed; 222 of 222 pass); the Lean file (§5, 0 `sorry`); the first
measurement (`_data/thermo_friction_first.json`); the amendment of §2.4; the
measurement of record (`_data/thermo_friction.json`,
`python3 -m glm_universal.tools thermo-friction --write`), on a corpus of
226,240 sentences; the decision to ship sintering (C1–C4 met); the blind-spot
question asked of `GLM.py` (`_data/thermo_friction_blind_spot.json`,
`--blind-spot`); and the evaluation after the round compared with the one
before (`_data/thermo_friction_frozen.json`, `--frozen`).

Two departures from §1, neither a change of rule: the sintered reading lives
in its own module, `overlay/glm_universal/runtime/sinter.py`, which imports
`runtime/respell.py` and leaves it unchanged (so Phase 157's stored
measurement, which digests `respell.py`, stays current); and the physics
register as held has 726 quantities, not the 660 §2.3 quoted — the rule was
every carrier name of the register, and the lexicon reads all 726 (1,393
entries in all).

**The corpus moves under the measurement.** The corpus is the project's own
text, so writing this round's modules and this study changed it, and Phase
156's sample (every k-th qualifying sentence) shifted with it. The first
measurement (226,072 sentences) and the measurement of record (226,240) read
different samples; the marks are read from the measurement of record, and
where a mark differs between the two it is said below.

**Verdict.** Friction is a useful sensor in all three experiments but an actionable one in only one: sintering the register vocabulary ships, reading back 727 of 735 misspelt register words and the survey's *mlilisecond* question, with ordinary misspellings no worse, no register word respelt where the shipped respelling changed 45, and no evaluation outcome moved; the heat-gated governor almost never acts, because the self-made valley is a basin many prompts fall into once each, not a phrase one continuation re-enters; and the prompt anchor costs a little where it acts, because at a hot step the words read after the prompt name the right directory more often than the prompt does.

**Marks.** 13 of 19 marks (A3, A5, A7, B2, B3, B4, B5, C1, C2, C3, C4, C5, C6 met; A1, A2, A4, A6, B1, B6 missed) and 1 of 1 amended (B6′ met); sintering ships.

### 7.1 Experiment A — the governor (A3, A5, A7 met; A1, A2, A4, A6 missed)

1,000 held-out sentences, 3-token prompts, at most 12 tokens; 19,997
positions.

| continuation | most frequent non-empty | summed overlap with the truth | distinct | position precision |
|---|---|---|---|---|
| patch (two-token row) | *the same way*, 37 | 695 | 533 | 4,332 / 17,241 |
| contact `R·(1+A)` | *same way*, 25 | 754 | 660 | 4,224 / 18,331 |
| static taboo (control) | *the same way*, 37 | 693 | 533 | 4,314 / 17,243 |
| **governor** | *the same way*, 37 | 694 | 533 | 4,308 / 17,238 |
| contact governor (beside) | *same way*, 25 | 751 | 660 | 4,205 / 18,329 |

* **The governor rests when it should** (A5 met: 0 of 2,205 cold rows
  disagree with the patch, as `governor_cold` says they cannot) and stops
  cleanly (A7 met: every continuation ends on a declared stop within 12
  tokens).
* **It almost never acts.** The heat is a working sensor — 2,335 of the 4,540
  rows met in the continuations are hot — but only 12 hot rows had a
  repeating candidate at all, and on 1 the choice moved: one continuation of
  1,000 changed (its overlap fell from 1 to 0, so A2 missed), and the valley
  is untouched (A1 missed: 37 and 37).
* **The valley is a basin, not a loop.** *the same way* is the continuation
  of 37 different prompts, each of which enters it once and ends; no
  continuation re-enters it, so a taboo on re-entering a recent bigram has
  nothing to bend against. Phase 157's reading (§7.4 there: "a continuation
  that will not re-enter a two-token state it has left") was the right
  reading of the *wear* result and the wrong reading of the valley: the
  cycle stop already ends every re-entry, and the dominance is across
  prompts.
* **On running text the taboo costs a little** (A6 missed: precision 24.99%
  against the patch's 25.13%; A4 missed, the static taboo keeps 6 more
  correct): language repeats bigrams such as *of the*, and penalising a
  repeat on the sentence's own history penalises a true continuation.
* What would move the basin is a reading across prompts — a continuation
  scored against how many *other* prompts the corpus sends into it — which is
  not a property of one continuation's row and is left open (§7.5).

### 7.2 Experiment B — the anchor (B2, B3, B4, B5, B6′ met; B1, B6 missed)

Phase 156's directory reader, 1,000 sentences, 139 directories. 468 sentences
are hot at least once; 3,791 of 21,248 steps are hot.

| reader | switches | returns | final correct | final correct on the 468 hot | switches into the truth |
|---|---|---|---|---|---|
| frictionless | 838 | 41 | 271 | 203 | 246 |
| fixed margin 1/4 (Phase 156) | 567 | 3 | 230 | 173 | 168 |
| noise-set `r/8` (Phase 157) | 614 | 2 | 235 | 172 | 174 |
| **anchor** | 810 | 36 | 265 | 197 | 235 |
| mismatched anchor (B6, next sample sentence) | 961 | 103 | 279 | 211 | 291 |
| other-directory anchor (B6′) | 971 | 120 | 257 | 189 | 264 |

* **It is inactive where the sides agree** (B5 met: 0 cold steps read other
  than the frictionless leader, 0 agreeing steps hot — `anchor_agree_leader`,
  `gradient_agree`), and **it is the gentlest of the four readers**: fewer
  switches and returns than the frictionless reader (B3 met), 95.5% of its
  switches into the truth kept (B4 met: 235 of 246, where the two margins kept
  68% and 71%), and 265 final readings correct against 271 (B2 met, the bar
  was 261), where the margins lost 41 and 36.
* **But it does not recover where it is hot** (B1 missed: 197 against 203).
  In the first measurement, on the earlier sample, it was 184 against 182 (B1
  met there): across the two samples the anchor's effect on the hot sentences
  is between +2 and −6, which is no effect that this sample can tell from the
  sample's own shift.
* **Why: at a hot step the prompt is not the reliable side.** Of the 244
  sentences whose last step is hot, the prompt leader is the true directory
  on 39, the generated leader on 68, and the frictionless leader on 113. A
  high gradient marks a change of subject (or a misleading start) at least as
  often as it marks dilution, so counting the prompt twice there helps as
  often as it hurts.
* **The control as declared leaked the answer** (B6 missed: the mismatched
  anchor did *better*, 211, because 886 of its 1,000 prompts come from the
  same directory, §2.4). **With a prompt from another directory it is
  weaker** (B6′ met: 189 against 197): the extra weight carries the right
  prompt's directory signal more than a wrong prompt's, but not more than
  reading without it.
* So the anchor is a **steadier reader at almost no cost**, and not a
  **recovery** mechanism. It remains experimental: it is not wired into any
  answering path.

### 7.3 Experiment C — sintering (C1–C6 met; ships)

| reading | recovery set: restored / different / unchanged (735) | 196 typo questions: restored / different | 338 short-word questions: restored / different | lexicon entries changed (1,393) |
|---|---|---|---|---|
| `loaded` (Phase 157, solid) | 0 / 8 / 727 | 194 / 0 | 334 / 4 | 45 |
| **sintered** | **727 / 8 / 0** | **195 / 0** | **335 / 3** | **0** |

* **Recovery** (C1 met: 98.9% restored, 1.1% different). The 8 turned into
  another word are tokens the corpus already reads at one edit — *burnt* for
  *brunt* is read as *burst*, *tnone* for *tonne* as *none* — so the solid
  state answers and the lexicon is never consulted (`sinter_keeps_solid`);
  `loaded` gives the same 8.
* **Ordinary misspellings are no worse** (C2 met): one more typo question
  restored (the *mlilisecond* question), one fewer short-word question turned
  into another (a lexicon word no longer respelt).
* **A hazard in the shipped respelling, found and removed** (C3 met). Read
  as one-token questions, `loaded` changes 45 correctly spelt register words
  into commoner corpus words — *abbe* to *able*, *bohm* to *ohm*, *dose* to
  *does*, *femtosecond* to *femtoseconds*. The sintered reading treats every
  lexicon entry as known and changes none. (The re-read runs only after a
  refusal, so this hazard could only ever reach a question that was already
  refused.)
* **The protected class holds** (C4 met: 255 protected tokens and their
  perturbations, 0 read differently from `loaded`).
* **The blind spot answers** (C5 met): `gram : mass :: mlilisecond : ?` is
  now answered, after `RESPELT 'mlilisecond' read as 'millisecond'`, as
  `gram : mass :: millisecond : time`.
* **The frozen path** (C6 met): 222 of 222 cases pass before and after, no
  outcome moved; two answer lines differ, both traced to the corpus the answer
  reads (`corpus-continue` counts more witnesses for each word;
  `corpus-unmentioned` finds *zyxwv* in 42 sentences of 12 documents where it
  had found 41 of 11 — this study's text names it).

### 7.4 The map the plan asked for

* **Where friction indicates a recoverable failure**: a refusal of the
  corpus respelling on a token of a word's shape one edit from a unique
  register name (C). The recovery is adopted.
* **Where friction indicates genuine uncertainty**: a high prompt/generated
  gradient (B). The prompt and the later words disagree, and neither is
  reliably the truth; a reader that holds less firmly (the anchor) is
  steadier but not more accurate.
* **Which friction signals are useful sensors**: all three fire, and fire
  where they say — the row heat on half the rows, the gradient on 18% of the
  steps, the refusal on the tokens it should. A sensor is not an actuator: the
  heat has nothing to actuate on, because the failure it was aimed at is not
  where it looked.
* **Which actions improve correctness**: sintering. **Which merely change
  readings**: the anchor (fewer switches, a few fewer correct). **Which do
  nothing**: the governor.

### 7.5 Left open

1. **The basin.** The self-made valley is the corpus's most frequent
   continuation reached from many prompts. A reading that scores a
   continuation by how many distinct prompts the corpus sends into it (an
   attractor census over the held-out prompts), and discounts a continuation
   that is everyone's, is the next candidate; it is a property of the corpus,
   not of one row.
2. **The anchor as a steadier reader.** It keeps 95.5% of the informative
   switches where the margins keep about 70%; whether it is the better
   *steadiness* trade (against `r/16` of Phase 157) on a sample that does not
   shift with the corpus is not measured. A sample frozen by address, not by
   position in the corpus, would make every friction measurement
   reproducible across rounds.
3. **The lexicon beyond the four registers.** Units the parser reads but no
   register names, and the structural words of the parser, are outside the
   lexicon; and the same 45-word hazard of §7.3 applies to any word the
   corpus barely uses, not only register names.
