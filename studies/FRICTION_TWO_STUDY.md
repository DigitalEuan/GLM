# Friction, the rest: a did-you-mean read by spelling and by use, the harness reading refusals, wear, and a margin that knows the noise

## Tier 0 — the coarse read

**Question.** Can a transposed letter be read back by the word's spelling and its use in the question, so that the machine answers what it refused without answering what it should refuse; does the evaluation harness read every refusal the machine prints; does wearing the prompt's asperities stop a continuation from reinforcing itself; and does a sticking margin set from how often the leader has changed keep the reader's informative changes of mind while removing its flip-flops?

**Verdict.** A transposed letter is now read back: the respelling, count first and use under load, restores 194 of the 196 typo questions with none turned into a different question, and after the round 193 of 194 typo runs hold with no slip where 41 of 196 held before, with no evaluation outcome moved; the harness reads every refusal the machine prints; but use on its own does not beat spelling, wear does not remove the self-made valley, which the two-token row carves rather than the touches, and the noise-set margin removes the flip-flops at a cost of 27 final readings.

**Deciding figure.** 7 of 14 marks (T3, T4, H1, H2, N1, N3, N4 met; T1, T2, T5, W1, W2, W3, N2 missed), 1 of 2 amended (T1′ met, T2′ missed) and 2 of 2 shipped marks (T1″, T2″); typo runs 193 of 194 hold after the round, 0 slip.

**Recomputed by.** `glm_universal.knowledge.friction_two_study.friction_two_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for the friction half of Phase 157 (§§0–6 are committed
before any code of the round is written, and the evaluation run that the
frozen path compares against was taken before that commit; §7 is what came
out). It takes the four lines Phase 156 left
([`FRICTION_STUDY.md`](FRICTION_STUDY.md) §7.6), in the owner's order:

1. **Typos** stick 155 of 196 moved questions. A *did you mean* that reads a
   word by its spelling and by its use is the candidate (§2.1).
2. **The harness** does not read a stepwise-planner `REFUSED` line (§2.2).
3. **Wear**: a contact continuation that reads its own words as prompt
   reinforces itself (§2.3).
4. **A margin that knows the noise** (§2.4).

## 1. What is built

* `overlay/glm_universal/runtime/respell.py` — the respelling of §2.1: the
  vocabulary table, the candidates, the reading by use, and the re-read.
* `GLM.py` — a batch question that the routed path refuses is respelt and
  asked again; the respelt reading is printed only if it answers.
* `overlay/glm_universal/evaluation/harness.py` — the `REFUSED` line read as a
  refusal (§2.2).
* `overlay/glm_universal/knowledge/friction_two.py` — worn contact (§2.3) and
  the noise-set margin (§2.4), over Phase 156's held-out sample and readers,
  which it imports and does not modify.
* `overlay/glm_universal/knowledge/friction_two_study.py` and
  `python3 -m glm_universal.tools friction-two [--write] [--survey]` — the
  marks and the stored measurements.
* `RequestProject/GLM/FrictionTwo.lean` — what is proved (§5).

## 2. The rules, fixed before the measurement

### 2.1 The did-you-mean

**The vocabulary.** The corpus of `glm_universal.knowledge` (the project's
own text), with the documents whose path names `friction` left out: those are
the stored surveys and these studies, whose text *is* the perturbed questions,
and reading them would teach the respeller the typos as words. A word is
**known** when it occurs in at least 3 documents of that corpus. The table
(each known word's document count, and for each known alphabetic word of at
least four letters with a word address, its 24 window coordinates of
Phase 155) is stored in `runtime/_data/respell_table.json` beside the digest of
the corpus and of the code that took it.

**The unknown words.** A question's tokens are its maximal runs of letters,
digits and underscores; a token is a candidate for respelling when it is at
least 4 characters long, holds a letter, and is not known (compared
lower-cased).

**By spelling.** The candidates for an unknown token are the known words at
one edit from it in the optimal-string-alignment sense: one adjacent
transposition, one deletion, one insertion or one substitution.

**By use.** For each candidate `c`, `U(c)` is the sum over the question's
other known words `p` that have coordinates of the inner product of `c`'s 24
window coordinates with `p`'s — how much `c` keeps the company the question
keeps, read on the lattice coordinates of Phase 155. The candidate with the
largest `U` is taken; a tie at the top is broken by the larger document
count; a tie that remains leaves the token unchanged. With no other known
word in the question, `U` is zero for every candidate and the document count
decides.

**The re-read.** The respelt question replaces every unknown token that has a
candidate and keeps the case of the original's first letter. In `GLM.py`, a
batch question read by the routed path (the default) is asked as written
first; only if that run **refuses** (a non-zero exit) and the respelt question
differs is the respelt question asked, and its output is printed in place of
the refusal only if it **answers** (exit zero), preceded by a line
`RESPELT  'dsecribe' read as 'describe'`. Otherwise the original refusal is
printed unchanged. So no question that answers today can change, by
construction (D13: the re-read is declared, costed by one more run, and the
original refusal stands when it fails). `GLM_RESPELL=0` turns it off.

**The controls**, read offline on the 196 typo questions of the survey (each
paired with its unperturbed original, which is the truth):

* **spelling only** — the candidate with the largest document count;
* **mismatched use** — `U` computed from the other words of the *next*
  case's question (the last from the first): the same reweighting by company,
  but the wrong company.

| # | mark | pass |
|---|---|---|
| T1 | read back | the respelling restores the unperturbed question on at least 85% of the 196 typo questions, and turns it into a different question on at most 2% |
| T2 | use earns its place | spelling and use restore at least as many as spelling only, and more than mismatched use |
| T3 | the survey's typos | at least 150 of the 196 typo runs hold after the round, with no slip |
| T4 | frozen path | every one of the 222 evaluation cases gives the same outcome after the round as before it, and every case that answered gives the same answer line, except for lines whose difference is traced to the corpus the answer reads |
| T5 | nothing else moves the wrong way | in the full survey after the round no perturbation has more slips or fewer holds than in the settled survey of Phase 156 |

### 2.2 The harness reads a refusal

`evaluation/harness.py` reads an `ANSWER` or `UNSOLVED` line as before; when
the output has neither, a line beginning `REFUSED` is read as a refusal, with
the rest of the line as the answer text.

| # | mark | pass |
|---|---|---|
| H1 | the survey after the round | no run is scored `error` for want of a line the harness reads: every run Phase 156 had to re-score by hand is scored by the harness itself |
| H2 | no current case moves | every evaluation case passes before and after (part of T4) |

### 2.3 Wear

Phase 156's contact continuation adds every word it produces to the prompt,
and a word that touches the candidates goes on touching them: *"the two words
agrees with the declared cases of phase 55"* came out 17 times. **Worn
contact** gives each content word in the touch set (prompt or produced) a
budget of 2: `A(c)` counts only words with budget left, and after a word `c`
is chosen, every word that counted in its `A(c)` loses one. Everything else is
Phase 156's continuation (§2.2 there: the same 1,000 held-out sentences, the
same 3-token prompts, at most 12 tokens, the same stops). The worn reading is
reported for the full contact score `R(c)·(1 + A(c))` (the marks) and for the
loaded score `R(c)·(8 + A(c))` beside it.

| # | mark | pass |
|---|---|---|
| W1 | the self-made valley | the most frequent non-empty continuation under worn contact occurs at most half as often as under contact |
| W2 | no worse against the truth | worn contact's summed overlap with the held-out truth is at least contact's |
| W3 | no narrower | worn contact gives at least as many distinct continuations as contact |

### 2.4 A margin that knows the noise

Phase 156's directory reader (138 directories), where a fixed margin of a
quarter cost 40 correct final readings. The **noise-set reader** holds its
reading and moves to the leader at a step only when
`8·S(leader) > (8 + r)·S(held)`, where `r` is the number of times the
frictionless leader has changed so far in the sentence: no margin while the
leader has been steady, and an eighth more for every change it has made. The
curve beside it reads `4` and `16` in place of `8`.

| # | mark | pass |
|---|---|---|
| N1 | never more switches | on every sentence (it is proved, §5; the mark checks the implementation) |
| N2 | no worse at the end | final readings correct on at least as many sentences as the frictionless reader's, less 1% of the sentences read |
| N3 | fewer returns | at most half the frictionless reader's |
| N4 | fewer switches | at most 90% of the frictionless reader's |

### 2.5 Amended readings of the did-you-mean, declared after the first offline measurement and before the second

The first offline measurement (§7; kept as
`_data/friction_two_respell_first.json`) restored 183 of the 196 typo
questions and turned 12 into a different question: T1 missed (6.1% against
2%), and T2 missed because use, spelling and mismatched use chose identically
on every question. Both misses stand. Three facts read off it shape the
amendments, and are stated before any of them is measured:

* **10 of the 12 are a hexadecimal literal respelt** (`0x8ad5a3` read as
  `x8ad5a3`, one deletion from a word the corpus knows): a token with a digit
  is a number, a code or a formula, never a misspelt word.
* **The other 2, and one restored-but-recased case, lose the original's
  capitals**: the vocabulary is lower-cased, so `GLM.NromFamily` came back as
  `GLM.Normfamily` and `mleting_point_K` as `melting_point_k`.
* **Use had nothing to decide**: of 207 tokens with a candidate, 3 had more
  than one, and on none of them did use and count disagree. A long word one
  edit from a known word almost always has one neighbour.

The amended readings, each reported beside the original and never in its
place:

* **T1′** — T1 for the respelling with two changes: a token holding a digit
  is never respelt; and the respelt token is the original with the one edit
  replayed on it (a transposition swaps the original's two characters, a
  deletion drops the original's character, an inserted or substituted letter
  takes the case of its neighbour on the left), so every other character keeps
  its case. This is the respelling `GLM.py` ships.
* **T2′, a perturbation where spelling is ambiguous** — every alphabetic word
  of 4 to 6 letters of every evaluation question, its second and third letters
  swapped (one moved question per word whose swap changes it and leaves it
  unknown), read offline with the amended respelling under use, spelling only
  and mismatched use. T2′: use restores at least as many words as spelling
  only, and more than mismatched use; the count of moved words with more than
  one candidate is reported beside it.

| # | mark | pass |
|---|---|---|
| T1′ | read back, amended | restores at least 85% of the 196, and turns at most 2% into a different question |
| T2′ | use where spelling is ambiguous | as T2, on the short-word perturbation |

### 2.6 The reading the round ships, declared after the amended measurement and before the survey

The amended offline measurement (§7) met T1′ (194 of 196 restored, none
turned into a different question) and missed T2′: on the 338 short-word
questions use restored 328, spelling only 334 and mismatched use 323. Use
carries a real signal (it beats the wrong company by 5) but, given the whole
weight, it overturns a much more frequent word 10 times — the lesson of Phase
156's contact (C1 against C2′) read again in spelling. So the round ships the
*loaded* reading, declared here before it is measured and before the CLI
survey:

* **count first, use under load** — among the candidates, the largest
  document count wins; only where the count ties at the top does `U` decide;
  a tie that remains leaves the token alone. It is the mode `loaded` of
  `runtime/respell.py`, and it is the mode `GLM.py` uses.

| # | mark | pass |
|---|---|---|
| T1″ | the shipped reading on the 196 | as T1′ |
| T2″ | the shipped reading where spelling is ambiguous | restores at least as many of the 338 short-word questions as spelling only, and more than mismatched use |

T3, T4 and T5 are read with the shipped reading.

## 3. What would count against

* T1/T2 missed: a word cannot be read back from one edit and the company it
  keeps; T3 missed while T1 met: the typos are not where the refusals are.
* T4/T5 missed: the re-read answers a question it should refuse.
* W1–W3 missed: the self-made valley is not a matter of an asperity used over
  and over.
* N2–N4 missed: the leader's changes do not say how noisy it is.

## 4. What is not claimed

* The typo is one declared perturbation (two adjacent letters swapped in the
  longest word); the respelling reads any one edit, but only the declared
  perturbation is measured.
* The usage reading uses the corpus's window coordinates; a word the corpus
  uses too little has none, and then spelling and count decide.

## 5. What is proved before the measurement

`RequestProject/GLM/FrictionTwo.lean`:

* **the re-read never takes an answer away** — a reading that keeps the
  first verdict when it answers, and takes a second reading's verdict only
  when the first refuses and the second answers, gives the first answer
  whenever there is one, and refuses only when both refuse
  (`reread_keeps_answer`, `reread_refuses_iff`);
* **the noise-set reader is a keep-or-move reader**, so it switches no more
  often than the leader for any margin rule at all (`noise_switches_le`, by
  `held_switches_le` of `Friction.lean`), and with a steady leader it moves
  exactly when the leader strictly beats the held reading;
* **wear bounds the pull** — under a budget of `b` per word, the total
  number of touches a continuation's words can give is at most `b` times the
  number of words in the touch set (`worn_touches_le`).

## 6. Files

See §1. Tests: `overlay/glm_universal/tests/test_friction_two.py`.

## 7. What came out

Taken in this order: the evaluation run before the round
(`_data/friction_two_eval_before.json`, before the pre-registration was
committed); the first offline respelling (`_data/friction_two_respell_first.json`);
the amendment of §2.5 and the amended offline measurement; the declaration of
§2.6; the corpus measurements, wear and the margin (`_data/friction_two.json`,
`python3 -m glm_universal.tools friction-two --write`); the survey after the
round (`_data/friction_two_survey.json`, `--survey`); and the evaluation after
the round compared with the one before (`_data/friction_two_frozen.json`,
shared with [`DOMAIN_WHEELS_STUDY.md`](DOMAIN_WHEELS_STUDY.md)). The corpus
figures read 220,669 sentences.

**Verdict.** A transposed letter is now read back: the respelling, count first and use under load, restores 194 of the 196 typo questions with none turned into a different question, and after the round 193 of 194 typo runs hold with no slip where 41 of 196 held before, with no evaluation outcome moved; the harness reads every refusal the machine prints; but use on its own does not beat spelling, wear does not remove the self-made valley, which the two-token row carves rather than the touches, and the noise-set margin removes the flip-flops at a cost of 27 final readings.

**Marks.** 7 of 14 marks (T3, T4, H1, H2, N1, N3, N4 met; T1, T2, T5, W1, W2, W3, N2 missed), 1 of 2 amended (T1′ met, T2′ missed) and 2 of 2 shipped marks (T1″, T2″); typo runs 193 of 194 hold after the round, 0 slip.

### 7.1 The did-you-mean (T1, T2 missed; T1′, T1″, T2″ met; T2′ missed)

| reading | 196 typo questions: restored / different / unchanged | 338 short-word questions: restored / different |
|---|---|---|
| first measurement (§2.1), every mode | 183 / 12 / 1 | — |
| spelling and use (amended) | 194 / 0 / 2 | 328 / 10 |
| spelling only | 194 / 0 / 2 | 334 / 4 |
| mismatched use | 194 / 0 / 2 | 323 / 15 |
| **loaded: count first, use under load (shipped)** | **194 / 0 / 2** | **334 / 4** |

* **T1 missed as declared** (12 of 196 turned into a different question,
  6.1%): 10 were hexadecimal literals respelt and 2 lost their capitals, as
  §2.5 records. Amended (no token with a digit, the edit replayed on the
  original's case) the respelling restores 194 and changes none (T1′ met).
  The two left unchanged are words the vocabulary does not know as words —
  *millisecond* in *gram : mass :: mlilisecond : ?* is in fewer than 3
  documents — and there the parser's own *did you mean* still lists it.
* **Use does not earn its place on its own** (T2, T2′ missed). On the 196 a
  long word one edit from a known word has one neighbour, so every mode
  chooses alike. On the short-word perturbation, where 73 of the 338 moved
  words have more than one candidate, use beats the wrong company (328
  against 323) — the signal is real — but given the whole weight it
  overturns a far more frequent word: *waht* read as something other than
  *what*, *haet* as something other than *heat*, *ruotes* as something other
  than *routes*. This is Phase 156's contact lesson (C1 against C2′) read
  again in spelling.
* **Loaded, it is never worse** (T2″ met: 334, equal to spelling and 11 more
  than mismatched use). Where the count ties, use decides; it is the reading
  `GLM.py` ships, and one more run of the question is all it costs.

### 7.2 The survey after the round (T3, H1 met; T5 missed as worded)

| perturbation | settled survey of Phase 156: hold / stick / slip | after the round: hold / stick / slip |
|---|---|---|
| `qmark` | 211 / 0 / 0 | 209 / 0 / 0 |
| `capital` | 217 / 0 / 0 | 215 / 0 / 0 |
| `spaces` | 222 / 0 / 0 | 220 / 0 / 0 |
| `please` | 222 / 0 / 0 | 220 / 0 / 0 |
| `tellme` | 222 / 0 / 0 | 220 / 0 / 0 |
| `typo` | 41 / 155 / 0 | **193 / 1 / 0** |
| `drop_the` | 1 / 0 / 0 | 1 / 0 / 0 |
| **all** | 1,136 / 155 / 0 | 1,278 / 1 / 0 |

* **The typos hold** (T3 met): 193 of 194 typo runs, no slip. The one stick
  is the *mlilisecond* question above.
* **The harness reads every refusal** (H1 met): no run of the survey is
  scored `error`; the 19 runs Phase 156 re-scored by hand are scored by the
  harness itself.
* **T5 missed as worded, and why.** When the survey was taken two cases,
  `report-relay` and `report-anonymous`, failed *unperturbed*: their pinned
  goal-query counts had moved with the round's Lean files (837 → 843
  queries). A case that fails unperturbed is not perturbed, so every
  perturbation has two fewer runs and two fewer holds than in Phase 156's
  survey, and the mark, which compares the counts, is missed. Read over the
  220 cases that pass unperturbed in both surveys, no perturbation has fewer
  holds or more slips. The two cases have since been re-pinned
  (`evaluation/cases.py`) and pass.

### 7.3 The frozen path (T4, H2 met)

All 222 evaluation cases give the same outcome after the round as before it
(220 of 222 pass both times; the two that fail both times are the two
re-pinned cases of §7.2). Two answer lines differ, both traced to the corpus
the answer reads, which is the project's own text and gained this round's
studies and stored surveys: `corpus-continue` continues *integrity never
meaning* one phrase further and counts more witnesses, and
`corpus-unmentioned` finds *zyxwv* in 31 sentences of 8 documents where it
had found 23 of 6. No refusal the evaluation pins changed, because the re-read
runs only after a refusal and is printed only when it answers
(`reread_keeps_answer`).

### 7.4 Wear (W1, W2, W3 missed)

1,000 held-out sentences, 3-token prompts, at most 12 tokens.

| continuation | most frequent non-empty | summed overlap with the truth | distinct |
|---|---|---|---|
| patch (two-token row) | *the same way*, 40 | 681 | 499 |
| contact `R·(1+A)` | *same way*, 14 | 712 | 644 |
| **worn contact, budget 2** | *same way*, 14 | 697 | 639 |
| loaded `R·(8+A)` | *the same way*, 24 | 759 | 571 |
| loaded, worn | *the same way*, 24 | 753 | 571 |

* **The self-made valley survives wear.** *"… the two words agrees with the
  declared cases of phase 55"* is produced 10 times under worn contact as
  under contact, although worn contact spends 5,434 touches and every word
  has only 2 to give. So the valley is not an asperity used over and over: it
  is carved by the two-token row itself, which, once *the two words* is
  produced, has one continuation it prefers whatever the touches say. Wear
  bounds the pull (`worn_touches_le`), and the pull was not what made it.
* **Wear costs a little** (overlap 697 against 712, distinct 639 against
  644): with the touches spent, the continuation falls back on the row
  sooner.
* What would move the valley is a reading of the row, not the touches: a
  continuation that refuses to re-enter a two-token state it has already
  left (the cycle stop of Phase 156 catches only an exact repeat).

### 7.5 A margin that knows the noise (N1, N3, N4 met; N2 missed)

Phase 156's directory reader, 1,000 sentences, 138 directories.

| reader | switches | returns | final correct |
|---|---|---|---|
| frictionless | 785 | 24 | 258 |
| fixed margin 1/4 (Phase 156) | 557 | 1 | 224 |
| noise-set, `r/16` | 693 | 2 | 244 |
| **noise-set, `r/8` (the marks)** | 602 | 1 | 231 |
| noise-set, `r/4` | 478 | 0 | 204 |

* **N1 holds on every sentence** (0 violations), as `noise_switches_le`
  says it must.
* **The flip-flops go** (N3 met: 24 returns to 1) **and a quarter of the
  switches** (N4 met: 602 of 785, 77%).
* **It still costs final readings** (N2 missed: 231 against 258, where 248
  was the bar). Against the fixed quarter it is better on both counts it
  trades — 7 more final readings correct for 45 more switches, with the same
  single return — and `r/16` keeps 244 with 2 returns. Every point of the
  curve trades accuracy for steadiness; none is free. Phase 156's finding
  stands: on this task most of the leader's changes are information, and a
  count of its changes is not a measure of its noise.

### 7.6 What does and does not work

* **Works and ships**: the did-you-mean (194 of 196 read back, 0 changed into
  another question, typo holds 41 → 193), and the harness reading `REFUSED`.
* **Works, and is a trade, not a gain**: the noise-set margin — it removes the
  flip-flops at a cost a fixed margin also pays, a little less of it.
* **Does not work**: use on its own as the respelling's decider, and wear as
  the cure for the self-made valley.

### 7.7 Left open

1. **The valley is in the row.** A continuation that will not re-enter a
   two-token state it has left, declared and measured against the patch and
   contact, is the next reading.
2. **A margin from the scores, not the count.** The noise-set margin reads
   how often the leader has changed; reading how much its score has moved
   (its variance over the sentence) is the untested alternative.
3. **Words the vocabulary does not know.** *millisecond* is a carrier name
   the registers hold but the corpus barely uses; the respelling's vocabulary
   could take the register names as known words beside the corpus.
4. **Use where it decides.** Use carries a real signal (it beats the wrong
   company) but loses to count; a declared share of the weight, between
   *loaded* and *use*, is not measured.
