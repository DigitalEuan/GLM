# The question in the answering path — a reply is the next turn

## Tier 0 — the coarse read

**Question.** Can the question Phase 145 computed for a tie be put into the GLM's own answer, and the reply taken as the conversation's next turn, without moving any answer the evaluation pins?

**Verdict.** Yes. A `locate` junction answer now ends with the question that would split it, and a reply typed as the next turn is read as an answer to it. 13 of 13 dialogues end confirmed on the member meant, with 0 wrong. A false reply always ends in a refused contradiction. Every turn is verified by column 3. The frozen path keeps all 198 statuses. 8 of 10 marks were met. F1 and R1 were missed only because the round's four new evaluation cases moved two evaluation-set counts and one census of earlier texts, causes the pre-registration did not name.

**Deciding figure.** 8 of 10 marks; dialogues 13/13 confirmed on the truth, 0 wrong, 15 replies in all (each run at most `n - 1` and `Nat.clog 2 n + 1`); column 3 41/41 turns verified, 43/43 altered claims rejected; one false reply 13/13 contradicted, 0 wrong; full registers 387/387 resolved, 0 wrong, 1280 questions (Phase 145: 1280); frozen path 198/198 present and same status, 194 same text.

**Recomputed by.** `glm_universal.reasoning.answering_question.answering_question_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 146, the fifth line of `STATUS.md` §2.1
(*the question in the answering path*, left by Phase 145). §§0–6 were
committed with the Lean file and the answering-path code and before the module
that takes the measurement existed; §7 is what came out.

**Where the system stood.** Phase 145
([`TIMED_QUESTION_STUDY.md`](TIMED_QUESTION_STUDY.md)) held a tie open and
resolved it by asking, but only through `tools timed-ask`: `GLM.py -q "locate
albedo"` answered the junction {absorptance, albedo} and stopped. The
conversation layer (`runtime/conversation.py`, `runtime/discourse.py`) already
kept turns, and rewrote a follow-up to a whole query that the session answers
— *the conversation layer can add an answer but can never change one*.

**What this round does.**

1. A `locate` answer that is a junction now **ends with the question** that
   would split it — the minimax question of the declared vocabulary (Phase
   145's), or the direct choice when none splits — with each reply and the
   members it keeps.
2. The request grammar gains **replies**: `locate albedo given
   word:absorbed=no; confirm:physics:albedo=yes`. The session applies them in
   order and answers with the live members and the next question; with one
   member left the next question is the **confirming** question; replies that
   leave no member are refused as `contradicted`, never resolved.
3. The conversation gains a fourth base shape, **`reply`**: right after a turn
   whose answer ended with a question, a text that is one of its options (its
   number, its text, or a member's name for the direct choice) is rewritten to
   that turn's query with the reply added, and the session answers it. The
   same reading is given to `GLM.py --converse` and `GLM.py --interactive`, so
   a user at the terminal answers where the developer answered through
   `tools timed-ask`.
4. Column 3 (the independent script) re-derives each reply from the register
   attributes, apart from the question module, and checks the live set and that
   the question asked splits it.

## 1. What is proved before any code

`RequestProject/GLM/AnsweringQuestion.lean` (namespace
`GLM.AnsweringQuestion`), building on `GLM.TimedQuestion`; no `sorry`,
standard axioms only.

* `after_reply` — a reply taken as the next turn prunes the live set the
  previous turn left: the answer to the whole query with every reply given is
  the answer reached turn by turn.
* `reply_removes`, `dialogue_bound`, `dialogue_length_lt` — every question the
  GLM puts splits the live set it is asked of, so every reply removes at least
  one member; a dialogue over a tie of `n` members has, under true replies,
  fewer than `n` replies, whatever they are.
* `confirm_yes`, `confirm_no`, `confirm_catches` — the confirming question
  keeps a resolved tie on *yes*, empties it on *no*, and if the replies
  resolved to `c` while the truth is another member, the true reply to *is it
  exactly `c`?* leaves no member.

## 2. The rule

* **Where the question appears.** Only in a `locate` answer whose read is a
  junction. Every other answer, and every refusal, is unchanged.
* **The question.** While more than one member is live: the question of the
  declared vocabulary (attributes other than symbol and gloss, then gloss words
  of four letters or more) whose worst reply leaves the fewest members, ties
  broken by vocabulary order; if none splits, the direct choice. With one
  member live and no confirmation yet: *is it exactly X?*. After a confirming
  *yes*: none.
* **Replies.** `key=reply`, separated by `;`. A key not declared for the
  junction is refused (`unknown-question`); a reply that is no member's answer
  is refused (`not-an-option`); a reply on a read that is a single carrier is
  refused (`no-tie`). A reply may be given to any declared question, not only
  the one asked; the order does not change the live set
  (`GLM.TimedQuestion.after_perm`).
* **A reply turn.** Detected first among the follow-up shapes, but only when
  the immediately previous turn put a question and the text is one of its
  options; the text of an option is matched before its number. Anything else
  is read exactly as before. In `Discourse` the reply is the one exception to
  *whole first*, and only in that position.

## 3. The dialogues declared here

The `locate` read answers three junctions of the 142-carrier sample (the
fourth, the zero word's, is refused for crowding, Phase 144):
{absorptance, albedo}, {acoustic_absorption, acoustic_intensity_level,
acoustic_power_level} and the eight `filled_*` matrices — 13 members, so 13
runs with each member as the carrier meant. A run is a `Conversation`: `locate
<member>`, then the truthful reply to every question put, until the answer
puts none.

## 4. The marks, declared before the measurement

| mark | claim |
|---|---|
| **L1** | `AnsweringQuestion.lean` builds with the full `lake build`, no `sorry`, standard axioms only |
| **F1** | frozen path: of the 198 evaluation cases recorded before the answering path moved (`_data/answering_question_baseline.json`), every one is present and keeps its status (answered or refused); every moved text is either a junction answer of `locate` whose text before the round is a prefix of its text after, or a figure the tree measures of itself (the Lean declaration count and what is drawn from it); none other |
| **E1** | the evaluation cases added for this round (a reply, a resolved and confirmed reply, a contradiction, a reply with no tie) come out as declared |
| **C1** | 13 of 13 runs (§3) end confirmed on the member meant, 0 wrong; each run's replies before the confirmation number at most `n - 1` (`dialogue_length_lt`) and at most `Nat.clog 2 n + 1` |
| **C2** | column 3 verifies every turn of the 13 runs |
| **C3** | a replier that gives one false reply (to the first question) and every other reply truthfully, the confirming one included: every such run ends refused as `contradicted`, 0 end on a wrong member |
| **Q1** | on the 387 runs over the full registers' 104 junctions (Phase 145's R2), the answering path's own loop (`pending_question`, `apply_given`) resolves every run to the truth, each within `n - 1` replies, with the same total number of questions as Phase 145's `resolve` (1280) |
| **R1** | a reply is read only where a question was put: the conversation and discourse reports are identical before and after the round, and none of the texts *yes*, *no*, *1*, *2*, *albedo*, *dB* is read as a reply as a first turn or after `describe carbon` |
| **T1** | every C1 turn's claimed live set and claimed question split, altered to another, is rejected by column 3 |
| **D1** | `GLM.py --converse "locate albedo" --converse "no" --converse "yes"` prints the question, binds both replies, and ends on `physics:albedo` with the confirming reply agreeing |

## 5. What this round does not do

* It does not put a question into any answer but the `locate` junction: the
  other ties (the crowded zero cell, `report hole`, the decoder's `classify`)
  still have no declared vocabulary.
* It does not choose questions by what a user can answer or what an answer
  costs; it still treats the replier as truthful except for the one
  confirming question.
* It does not give the escalation reports or `nearest` the guarded read.

## 6. Files

* `glm_lean/RequestProject/GLM/AnsweringQuestion.lean` — §1.
* `glm_universal/reasoning/timed_question.py` §8 — replies, the next
  question, matching a reply.
* `glm_universal/runtime/session.py` — `_locate_question`, the
  `given` replies in `_solve_locate`.
* `glm_universal/runtime/tct_engine.py` — column 3 re-derives the
  replies.
* `glm_universal/runtime/conversation.py`, `discourse.py` — the
  `reply` shape.
* `GLM.py` — the question printed by `--converse` and
  `--interactive`, and replies read by both.
* `glm_universal/reasoning/answering_question.py` — the measurement;
  `tools answering-question`.
* `glm_universal/reasoning/_data/answering_question_baseline.json` —
  the 198 answers before the round.
* `glm_universal/tests/test_answering_question.py`.

## 7. What came out

Measured by `PYTHONPATH=. python3 -m glm_universal.tools answering-question
--write` (about twenty minutes, stored beside the digest of its sources) after
§§0–6 were committed. It was taken twice. §7.1 says why, and both takes are
reported.

| mark | result | |
|---|---|---|
| **L1** | `AnsweringQuestion.lean` builds in the full `lake build`, no `sorry`, axioms `propext`, `Classical.choice`, `Quot.sound` | met |
| **F1** | 198/198 present, 198/198 same status, 194 same text; moved: `locate-junction`, `locate-junction-moved` (the old text a prefix of the new), `report-language` (178 → 182 evaluation questions of the undescribed kinds), `report-query-escalation` (198 → 202 evaluation cases) | missed |
| **E1** | 4/4 new cases as declared | met |
| **C1** | 13/13 confirmed on the member meant, 0 wrong; replies 1, 1, 1, 2, 2 and eight 1s (15 in all); every run within `n - 1` and `Nat.clog 2 n + 1` | met |
| **C2** | 41/41 turns verified by column 3 | met |
| **C3** | 13/13 contradicted, 0 ended on a wrong member | met |
| **Q1** | 387/387 resolved, 0 wrong, 387 within `n - 1`; 1280 questions, as Phase 145 | met |
| **R1** | 0 of 12 control texts read as replies; the reports differ in 5 places (below) | missed |
| **T1** | 43/43 altered claims rejected | met |
| **D1** | as declared | met |

### 7.1 What the frozen path caught: `=` read as an identity

The pre-registered grammar wrote a reply as `key=reply`. The first take found
a real fault. The description layer's infix `verify` shape reads any text with
one `=` as an identity (`<lhs> = <rhs>`). It therefore claimed two of the new
evaluation questions (`locate acoustic_power_level given attr:unit=dB`,
`locate C given attr:unit=dB`) as `verify`, while the shipped parser read them
as `locate`. That made two infix false positives, and `report language`
changed its verdict from *described* to *not described*. Statuses did not move,
so only the text comparison caught it.

The fix was to write replies as `key is reply`:
`locate albedo given word:absorbed is no; confirm:physics:albedo is yes`.
The second take, after the change, gives the table above: no false positives,
and the language report is *described* again. The only remaining change in its
text is the count of evaluation questions (178 → 182).

### 7.2 Why F1 and R1 are missed

F1 claimed that the only moved texts would be the junction answers and the
Lean-derived figures. Two more moved, both for one reason: the four new
evaluation cases are counted by `report language` (the evaluation questions
of the undescribed kinds, 178 → 182) and by `report query escalation` (198 →
202 cases). Earlier rounds declared these same causes in their own frozen-path
comparisons (`reasoning/frozen_path.py`); this pre-registration did not. The
Lean-derived figures did not move, because the baseline was taken after the
Lean file was added and the goal-query count stayed at 822.

R1 claimed the conversation and discourse reports would be identical. They
differ in five places. The first is the conversation report's count of
declared follow-up shapes, 3 → 4: that is this round's `reply` shape. The other
four are in the discourse census of earlier declared texts, which reads the
evaluation cases' notes:
* the notes of the new cases add 38 strings (5129 → 5167);
* one of them (*leaves two of the three acoustic members*) is taken by the
  plural phrasing in two corpora (taken 24 → 26, distinct 16 → 17).

The census's own mark is unchanged: 0 released, and the 2 texts answered alone
are the same as before. No control text was read as a reply.

Neither miss is an answer moving. Both are counts drawn from the evaluation
set, which this round enlarged. They stay recorded as missed rather than
re-declared after the fact.

### 7.3 The dialogues

Every one of the 13 runs is a `Conversation`. It starts with `locate <member>`,
then gives the truthful reply to each question put, then *yes* to the
confirming question. Results by junction:

* {absorptance, albedo}: one reply (*does its description mention
  'absorbed'?*).
* The acoustic three: one reply for `acoustic_absorption` (*what is its
  unit?* — 1), and two for each of the dB pair (the unit, then *'intensity'*).
* The eight `filled_*` matrices: one reply (*what is its cols?*), which
  separates all eight.

Each turn's live set and question split are checked by column 3, apart from the
question module. It re-derives every reply from the register attributes, and
the check rejects all 43 altered claims.

With one false reply to the first question, every run ends refused as
`contradicted`, in one of two ways:
* a junction of two resolves to the wrong member, and the true *no* to the
  confirming question empties it (`confirm_catches`);
* in the larger junctions the truth's own answer to a later question is no
  live member's answer, so the live set empties there.

### 7.4 What the user sees

```
$ python3 GLM.py --converse "locate albedo" --converse "no" --converse "yes"
ANSWER  physics:albedo reads as the junction {physics:absorptance, physics:albedo} ... to separate them, the GLM asks: ...
ASKS    Does its description mention 'absorbed'?
  1. yes  -> physics:absorptance
  2. no  -> physics:albedo
BOUND   reply bound to no, against 2 candidates from turn 0: 'locate albedo given word:absorbed is no'
ASKS    Is it exactly physics:albedo?
BOUND   reply bound to yes, ...: 'locate albedo given word:absorbed is no; confirm:physics:albedo is yes'
ANSWER  ... if the replies are true of the carrier meant, it is physics:albedo (GLM.TimedQuestion.resolved_eq_truth), and the confirming reply agrees
```

`GLM.py --interactive` reads replies the same way, and they may be typed as the
option's number. The `--input PATH` option was declared but never read; it
now is.

### 7.5 Verdict, and what it leaves

The question is in the answering path. A junction answer ends with the
question that would split it. The reply is the conversation's next turn,
rewritten to a whole query that the session answers and column 3 checks. In
the sample, every dialogue ends confirmed on the member meant, and a single
false reply always ends in a refused contradiction. The frozen path keeps
every status. The one fault it found (`=` read as an identity) was fixed
before the second take. 8 of 10 marks were met. The two misses are
evaluation-set counts that the pre-registration failed to declare.

It leaves:
* questions for the other ties (the crowded zero cell, `report hole`, the
  decoder's `classify`);
* the escalation reports and `nearest` reading junctions and putting the
  question;
* a question for the 78-member dimensionless junction that is fewer than 22;
* questions chosen by what a user can answer;
* a reply carried across an unrelated turn. Today a reply is read only
  immediately after the question.
