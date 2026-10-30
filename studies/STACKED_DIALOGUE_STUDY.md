# Several open ties at once — a reply read against the question it answers

## Tier 0 — the coarse read

**Question.** When a second tie's question is put before the first is answered, can the conversation keep both open and read each reply against the question it answers, say which one when a reply fits more than one, and close a question that has been left alone too long, without ever reading a reply against the wrong question or taking a whole query for one?

**Verdict.** Yes. The open questions now form a stack, newest first: a second question no longer closes the first, a reply is read against the newest open question it fits or against the turn it names (`turn N: <reply>`), it closes that question only, and a question closes after five unrelated turns. Two ties answered one after the other, interleaved, ended exactly as each ends alone in every run, with no reply bound to the wrong question; a reply that fitted both was bound to the newer and named the older every time; no question of the evaluation set was taken for a reply. Lean proves the rule: the bound question is the newest the reply fits, a reply closes exactly one question, the window closes everything after it, and nothing the rule of Phase 172 read is read differently when the newest question fits.

**Deciding figure.** 8 of 8 marks on the first take; first-tie replies read behind a second question 0 of 61 → 61 of 61 dialogues ending as alone, 0 of 258 replies misbound; 23 of 23 replies fitting both bound to the newer and naming the older; 0 of 4,683 evaluation questions read as a reply; 0 members outside the head ever live over 244 runs.

**Recomputed by.** `glm_universal.reasoning.stacked_dialogue_study.stacked_dialogue_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 20 October 2026 (pre-registered and measured 20 October 2026, in one session; the marks were written with the measuring module before its first run, and none was restated).*

## 0. What this document is

A study for Phase 173. It takes two lines of To-Do item 8 of
[`STATUS.md`](../STATUS.md) §2.1, *dialogue, the rest*, left by Phase 172
([`RESUMED_DIALOGUE_STUDY.md`](RESUMED_DIALOGUE_STUDY.md) §7.4):

* *Only the newest open question can be resumed: keeping several open ties (a
  stack) and saying which one a reply answers when it fits more than one is
  the next step.*
* *There is no window — a question stays open however many unrelated turns
  pass.*

It continues the line towards the loop reasoning the owner asked for: a
conversation that can hold more than one unfinished question at once and
return to each, rather than one that must finish a sub-dialogue before
starting another.

## 1. What is proved

`glm_lean/RequestProject/GLM/StackedDialogue.lean` (namespace
`GLM.StackedDialogue`, on top of `GLM.ResumedDialogue`; 16 theorems, 0
`sorry`; axioms `propext`, `Classical.choice`, `Quot.sound` at most). The
conversation is reduced as in Phase 172 — each turn put a question, was read
as a reply, or was neither — with one addition: `fits q b`, whether the text
`b` is one of the options of the question `q`, left abstract. The state holds
the replies read and the open questions, newest first, each with the number of
unrelated turns it has survived; `step fits W` is the rule of this round with
window `W`.

* `bound_fits`, `bound_newest` — **the bound question is the newest the reply
  fits**: it fits the reply, and every question opened after it does not.
* `reply_reads` — a reply is recorded with that question.
* `reply_erases`, `reply_closes_one` — **a reply closes exactly the question
  it answered**: that entry leaves the stack, every other stays, in order.
* `unfit_unread` — a reply that fits no open question changes nothing.
* `newest_fit_agrees` — **when the newest question fits, it wins**: whatever
  the rule of Phase 172 read, the stack reads the same way.
* `unrelated_within_window` — within the window an unrelated turn changes no
  open question; `age_mem`, `age_iter_ge`, `window_closes` — **past the window
  every question is closed**: after `W + 1` unrelated turns none is open,
  whatever was open before.
* `stacked_least` — whatever the turns and the replies, and whichever question
  each reply was read against, every live member is at the scan's least
  distance (Phase 167's `adversary_least`, carried over).
* `older_answered`, `resumed_rule_loses` — a question, a second question, a
  reply that fits only the first: the stack reads it against the first and
  leaves the second open; the rule of Phase 172 had already closed the first.
* `findIdx_bound`, `findIdx_of_bound` — the position the step erases is the
  bound question's (the lemmas the rest stand on).

## 2. The mechanism

`runtime/conversation.py`, `Conversation.open_ties`, switch `OPEN_TIE_STACK`
(on since this round), window `OPEN_TIE_WINDOW = 5`, named reply
`ADDRESSED_REPLY`. The turns are read oldest first, as the Lean `step` reads
them:

* a turn that *replied* closes the question it was read against — that one
  only;
* a turn that put a question pushes it on top of the stack;
* any other turn is unrelated: every open question has survived one more, and
  one that has survived more than five closes.

A text is a reply when it is one of an open question's options
(`timed_question.match_reply`, unchanged). It is read against the newest open
question it fits; when it also fits older open questions, the binding carries
them (`Binding.also`) and its sentence says so — *the reply also fits the open
question of turn 0; read against the newest, turn 1 — say 'turn 0: no' to
answer that one*. A reply written `turn N: <reply>` (or `to turn N, <reply>`)
is read against turn N's question only, and only while it is open. The query a
reply rewrites to is still that turn's query with the reply added, so the
stack adds answers (a reply to an older question that used to be lost is now
read) and changes none whenever the newest question fits.

A reply that would have answered a question the window closed is not read
against it; `Conversation.expired_fit` names that question, and `GLM.py
--converse` says so before reading the text as the whole query it now is
(*'no' would have answered the question of turn 0, closed after 5 unrelated
turns*). This was added after the first take, and is reported beside S4 as an
observation, not a mark.

The window was declared before anything was measured, not fitted: Phase 172
measured replies after one to three unrelated turns, and five keeps that
margin while bounding how long a forgotten question can capture a reply. With
the switch off, the reading of Phase 172 comes back exactly, and Phase 172's
own measurement is now taken that way, the reading it measured.

## 3. What is measured

The 21 ties of Phase 172 — the 18 distinct tied heads of Phase 148's sets (48
members) and the 3 `locate` junctions of the 142-carrier sample (13 members) —
each paired with the next in that list (21 ordered pairs). For each member `m`
of the first tie, the second tie is opened with one of its members `m′`, both
dialogues are driven by truthful informants (Phase 167's), and every reply
goes through the conversation as the next turn. The unrelated turns are Phase
172's three declared texts, cycled.

| reading | what is done |
|---|---|
| **S0** | the control: the switch off — first tie's question, second tie's question, then the first tie's true first reply |
| **S1** | the switch on: both questions open, then the first dialogue answered to its end, then the second; a reply that a newer open question would also take is said `turn N: <reply>`; each compared with the same dialogue alone |
| **S2** | before anything is answered, the first tie's true reply when it is also one of the second tie's options, said plainly |
| **S3** | the first tie's reply named to its turn; named to a turn that put no question; named to the first turn after it was answered |
| **S4** | one tie's question, then 5 unrelated turns, then its true reply; then one more unrelated turn and the reply again |
| **S5** | two questions open behind an unrelated turn, then every question of the end-to-end evaluation set tried as the next text |

## 4. Faculties

**Addressing.** A reply now reaches an older question, chosen by which
question it fits or by the turn it names; when a reply fits more than one, the
answer says which it was read against and how to choose the other.
**Refusal**, kept: a reply that fits no open question, a reply naming a closed
or absent question, a reply after the window, and a whole query are not read.
Not derivation.

## 5. The marks

Written with the measuring module, before its first run; none was restated.

| mark | met when |
|---|---|
| **L1** | `StackedDialogue.lean` states its 16 theorems with no `sorry`, and builds |
| **S0** | with the switch off, 0 first-tie replies read against the first tie behind a second question |
| **S1** | with it on, every run: the first and second dialogues ending as each ends alone (same status, same member), the second still open when the first ends, 0 replies bound to another turn |
| **S2** | every plain reply fitting both bound to the newer question, naming the older |
| **S3** | every named reply bound to the turn named; 0 read when the turn named put no question or was answered |
| **S4** | every reply read after 5 unrelated turns, 0 after 6 |
| **S5** | 0 evaluation questions read as a reply |
| **P** | over every run, 0 members outside the head ever live and 0 values outside it |

A further gate, outside the marks: the end-to-end evaluation keeps every
answer and refusal, and Phase 172's measurement, taken with the switch off,
keeps its marks.

## 6. What is not claimed

The informants are declared policies, not users; the unrelated turns are three
declared texts; the pairs are each tie with the next in a fixed list, not
every pair. The window is a declared constant, not a measured optimum: whether
five is the right length for a person is not measured, and a late reply is
said to be late only on the command line's `--converse` (the conversation
object reports it, the session's answer does not). The newest
question wins a reply that fits several; that is the rule, not a judgement of
which question the speaker meant, and the binding says so rather than
guessing. A named reply must name the turn number the conversation gave the
question; there is no other way to point at an older question.

## 7. What came out

`PYTHONPATH=. python3 -m glm_universal.tools stacked-dialogue` (stored in
`reasoning/_data/stacked_dialogue_study.json`, digest-guarded; `--write`
re-takes it in about two minutes on eight cores). The take reported here is
the second: the first, before the late-reply observation was added, met the
same 8 marks with the same figures.

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **L1** | 16 of 16 theorems, 0 `sorry`; `lake build RequestProject.GLM.StackedDialogue` passes | yes |
| **S0** | 0 of 61 first-tie replies read against the first tie with the switch off | yes |
| **S1** | 61 of 61 runs: first dialogue as alone 61, second as alone 61, second still open 61; 0 of 258 replies misbound (23 said with the turn named) | yes |
| **S2** | 23 of 23 replies fitting both bound to the newer question, 23 naming the older | yes |
| **S3** | 61 of 61 named replies bound to the turn named; 0 of 61 read naming a turn with no question; 0 of 61 read naming an answered question | yes |
| **S4** | 21 of 21 read after 5 unrelated turns; 0 of 21 after 6 (observed, not a mark: 21 of 21 late replies said to be late) | yes |
| **S5** | 0 of 4,683 tries (223 questions at each of 21 pairs) read as a reply | yes |
| **P** | 0 members outside the head ever live, 0 values outside it, over 244 runs | yes |

### 7.2 What this answers

A conversation can now hold two unfinished dialogues and finish them in either
order. The proof says why every interleaved run ended where its lone run ends:
a reply is recorded with the question it answered and closes that question
only (`reply_reads`, `reply_erases`), so each dialogue's replies are the same
list they would have been alone, and everything proved about a dialogue's live
set carries over (`stacked_least`). The 23 replies that fitted both open
questions are where a stack could go wrong; the rule reads them against the
newer question and says so, and naming the turn reached the older one every
time.

The command line reaches the stack through `--converse` (the conversation,
Phase 92). Two `locate` junctions opened one after the other, then *no*, *dB*
and *yes*: *no* fits only the first question and is bound to turn 0 with the
second still open; *dB* is bound to turn 1; *yes* fits both the second
dialogue's new question (turn 3) and the first dialogue's confirming question
(turn 2), is read against the newer, and the answer says so — *the reply also
fits the open question of turn 2; read against the newest, turn 3 — say
'turn 2: yes' to answer that one*:

```bash
cd overlay
python3 GLM.py --converse "locate physics:albedo" \
  --converse "locate physics:acoustic_absorption" \
  --converse "no" --converse "dB" --converse "yes"
```

### 7.3 What is left

* The window's length is declared, not measured, and a late reply is said
  to be late only by `--converse`; the conversation object reports it
  (`expired_fit`) without changing the answer.
* A word echo (`yes`, then `yes`) to a gloss-word question is still read as a
  confirmation, inside the proved limit (left by Phase 167).
* A true reply that is no option of the question (the carrier meant outside
  the head) is still refused `not-an-option` without saying it is evidence
  that the carrier meant is not in the head (left by Phases 150 and 167).

## In one paragraph

Yes. The open questions now form a stack, newest first: a second question no longer closes the first, a reply is read against the newest open question it fits or against the turn it names (`turn N: <reply>`), it closes that question only, and a question closes after five unrelated turns. Two ties answered one after the other, interleaved, ended exactly as each ends alone in every run, with no reply bound to the wrong question; a reply that fitted both was bound to the newer and named the older every time; no question of the evaluation set was taken for a reply. Lean proves the rule: the bound question is the newest the reply fits, a reply closes exactly one question, the window closes everything after it, and nothing the rule of Phase 172 read is read differently when the newest question fits.

The figures: 8 of 8 marks on the first take; first-tie replies read behind a second question 0 of 61 → 61 of 61 dialogues ending as alone, 0 of 258 replies misbound; 23 of 23 replies fitting both bound to the newer and naming the older; 0 of 4,683 evaluation questions read as a reply; 0 members outside the head ever live over 244 runs.
