# The open tie kept across turns — a reply read after the conversation has moved on

## Tier 0 — the coarse read

**Question.** When the question at a tie is left unanswered for a turn or three and then answered, can the conversation read the reply against the question it answers, without ever reading a reply against the wrong question or taking a whole query for one?

**Verdict.** Yes. A question now stays open across turns that leave it alone, and a reply after one, two or three unrelated turns ends every dialogue exactly as the uninterrupted dialogue ends, for truthful informants and for adversarial ones. A question is answered once, the newest question supersedes an older one, and no question of the evaluation set is taken for a reply. Lean proves that an unrelated turn is invisible to the replies read. The same round ran Phase 167's adversarial battery at the `locate` junctions for the first time, and pinned `report anonymous` on its claim, which showed that one sentence of that report had asserted more than its measurement holds.

**Deciding figure.** 9 of 9 marks; replies read after an unrelated turn 0 of 61 → 183 of 183, every one ending as the uninterrupted run; 243 of 243 adversarial runs unchanged by the interruption; 0 of 4,683 evaluation questions read as a reply; 0 members outside the head ever live over 791 runs.

**Recomputed by.** `glm_universal.reasoning.resumed_dialogue_study.resumed_dialogue_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 20 October 2026 (pre-registered and measured 20 October 2026, in one session; the marks were written with the measuring module before its first run, and none was restated). Last altered 20 October 2026 (Phase 173: §7.4 notes the lines taken).*

## 0. What this document is

A study for Phase 172. It takes To-Do item 8 of [`STATUS.md`](../STATUS.md)
§2.1, *adversarial dialogue, the rest*, left by Phase 167
([`ADVERSARIAL_DIALOGUE_STUDY.md`](ADVERSARIAL_DIALOGUE_STUDY.md) §7.4). Two
of its four lines are taken here:

* *A reply to an earlier question is not read once an unrelated turn
  intervenes: the dialogue is dropped, not resumed.* Phase 167 measured this
  as informant A4: 0 of 48 replies read after one unrelated turn. Resuming
  needs the conversation to keep an open tie across turns.
* *The battery has not been run at the `locate` junction*, which reads its
  replies by the same code (Phase 146,
  [`ANSWERING_QUESTION_STUDY.md`](ANSWERING_QUESTION_STUDY.md)).

It is also the first step towards the loop reasoning the owner asked for at
the outset: a dialogue that can be put down and picked up again, rather than
one that has to be finished in consecutive turns.

## 1. What is proved

`glm_lean/RequestProject/GLM/ResumedDialogue.lean` (namespace
`GLM.ResumedDialogue`, on top of `GLM.AdversarialDialogue`; 0 `sorry`; axioms
`propext`, `Classical.choice`, `Quot.sound` at most). A conversation is reduced
to what matters for an open question: each turn put a question (`ask q`), was
read as a reply (`reply b`), or was neither (`unrelated`). `run` folds the
rule of Phase 172 over the turns; `runOld` folds the reading before it.

* `run_unrelated`, `run_strip`, `foldl_strip` — **an unrelated turn is
  invisible**: the replies read, and the question left open, are those of the
  same conversation with every unrelated turn removed.
* `resumed_live_eq` — so a resumed dialogue leaves exactly the live set the
  uninterrupted one leaves; and `resumed_least` — whatever the turns and the
  replies, every live member is at the scan's least distance (Phase 167's
  `adversary_least`, carried over to interrupted dialogues).
* `old_rule_drops`, `resumed_reads` — a question, an unrelated turn, a reply:
  the older reading reads nothing, the new rule reads the reply against the
  question.
* `reply_closes` — a question is answered once: a second reply, after any
  number of unrelated turns, is not read against it.
* `newest_supersedes` — a reply after two questions is read against the
  second only.
* `agrees_without_unrelated` — on a conversation with no unrelated turn the
  two readings agree: the rule changes nothing the earlier phases measured.

## 2. The mechanism

`runtime/conversation.py`, `Conversation.open_tie`, switch
`RESUME_OPEN_TIE` (on since this round). The turns are read newest first:

* a turn that put a question holds the open question — the newest question
  supersedes every older one;
* a turn that *replied* and put no question of its own closes the tie — a
  question is answered once, and an echo of the reply cannot re-open it;
* any other turn — a whole query that put no question, a refusal, a
  follow-up — is unrelated and is passed over.

A text is a reply when it is one of the open question's options, read by the
rules Phases 146 and 167 left (`timed_question.match_reply`). The reply is
bound to the turn that put the question, and the query it rewrites to is that
turn's query with the reply added — exactly the query an immediate reply
would have produced. So resumption can add an answer (a reply that used to be
passed to the session as a whole query, and refused, is now read) but it
cannot change one. With the switch off, only the previous turn's question can
be replied to, as before.

## 3. What is measured

The 18 distinct tied heads of Phase 148's sets (48 members), each asked at
one of its points (`nearest to <point>`), and the 3 junctions of the
142-carrier sample that `locate` answers (13 members), each asked as
`locate <member>`. Every reply goes through the conversation as the next
turn. The unrelated turns are declared, in the order they are interposed: a
`nearest` answer that puts no question (Phase 167's A4 turn), `describe
carbon`, and a refusal (`describe no_such_carrier_here`).

| reading | what is done |
|---|---|
| **R0** | the control: Phase 167's A4 with the switch off — one unrelated turn, then the true first reply |
| **R1** | the switch on: the true first reply after 1, 2 and 3 unrelated turns, against the uninterrupted truthful run |
| **R2** | the consistent liar (every ordered pair of members) and the first-false informant of Phase 167, one unrelated turn before the first reply, against the same informant uninterrupted |
| **R3** | a truthful dialogue run to its end, an unrelated turn, then each of its replies said again |
| **R4** | a `nearest` tie's question, an unrelated turn, the next head's question, then the first tie's true first reply |
| **R5** | a question open behind an unrelated turn, then every question of the end-to-end evaluation set tried as the next text |
| **R6** | at the `locate` junctions: truthful, consistent-liar and first-false informants, and Phase 167's 14 malformed texts |

## 4. Faculties

**Addressing.** A reply that used to be refused is now answered, its key
supplied by a turn that is no longer the last one; the answer is the one an
immediate reply gets. **Refusal**, kept: a reply against a closed or
superseded question, and a whole query, are still not read. Not derivation.

## 5. The marks

Written with the measuring module, before its first run; none was restated.

| mark | met when |
|---|---|
| **L1** | `ResumedDialogue.lean` states its 10 theorems with no `sorry`, and builds |
| **R0** | with the switch off, 0 replies read after an unrelated turn, at both kinds of tie |
| **R1** | with it on, every reply read, and every run ending as the uninterrupted run — same status, same member — at both kinds of tie |
| **R2** | every adversarial run ending as its uninterrupted counterpart, at both kinds of tie |
| **R3** | 0 repeated replies read once the dialogue has ended |
| **R4** | 0 replies bound to the superseded question |
| **R5** | 0 evaluation questions read as a reply |
| **R6** | at the junctions: every truthful run confirmed on the member meant, every liar on the member impersonated, every first false reply contradicted, 0 malformed texts read |
| **P** | over every run, 0 members outside the head ever live and 0 values outside it |

A further gate, outside the marks: the end-to-end evaluation keeps every
answer and refusal.

## 6. What is not claimed

The informants are declared policies, not users, and the unrelated turns are
three declared texts. Resumption is by the rule of §2 only: there is no
window, so a question stays open however many unrelated turns pass, until it
is answered or superseded; whether a long gap should close it is not
measured. Only the newest question can be resumed — a reply meant for an
older, superseded question is read against the newest if it is one of its
options (R4: 19 of 48 were), which is the rule, not a repair. The consistent
liar is still confirmed on the member impersonated (Phase 167's proved limit);
an interruption neither helps nor hurts it.

## 7. What came out

`PYTHONPATH=. python3 -m glm_universal.tools resumed-dialogue` (stored in
`reasoning/_data/resumed_dialogue_study.json`, digest-guarded; `--write`
re-takes it in about two minutes on eight cores).

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **L1** | 10 of 10 theorems, 0 `sorry`; `lake build RequestProject.GLM.ResumedDialogue` passes | yes |
| **R0** | 0 of 48 (`nearest`) and 0 of 13 (`locate`) replies read with the switch off | yes |
| **R1** | 144 of 144 and 39 of 39 read; every one ending as the uninterrupted run | yes |
| **R2** | 166 of 166 and 77 of 77 adversarial runs ending as the uninterrupted run | yes |
| **R3** | 0 of 130 repeated replies read after the dialogue ended | yes |
| **R4** | 0 of 48 bound to the superseded question (19 read against the newest) | yes |
| **R5** | 0 of 4,683 tries (223 questions at each of 21 ties) read as a reply | yes |
| **R6** | truthful 13 of 13 confirmed; liars 64 of 64 on the member impersonated; first false 13 of 13 contradicted; 0 of 182 malformed texts read | yes |
| **P** | 0 members outside the head ever live, 0 values outside it, over 791 runs | yes |

Phase 167's own measurement was re-taken with its A4 under the switch off,
the reading it measured (13 of 13 marks, unchanged), and Phase 150's
(`nearest-question`, 8 of 8, unchanged).

### 7.2 `report anonymous`, pinned on its claim

To-Do item 7 noted that every new Lean file moved the `report anonymous`
evaluation pin, because the pin quoted the Lean corpus's counts, and that the
report would have to read its standing off the measurement, as `report relay`
does since Phase 171, before its pin could ask for the claim. This round's
Lean file would have moved it again, so it was done here: the report now
ends *Standing, read off the measurement:* and either says that every check
of the measurement's verdict holds or names the checks that fail; the pin
forbids a failure of the four checks the claim rests on (the text search
collapses without the names, the structural address holds, it is the clear
leader, the gate hands over).

Reading the verdict found one check that the sentence had been asserting
without checking: `text_is_within_twice_chance` fails — the text search
falls 685 → 57 of 820 (the corpus refreshed with this round's Lean file), more than twice the 23 hits chance gives. The answer
said *both to the 23 hits chance gives*; it now says *against*, and its
standing names the failing check. The claim the case pins is unaffected. This
is a sentence corrected, not a capability moved.

### 7.3 What this answers

A dialogue at a tie no longer has to be finished in consecutive turns. A
reply after an interruption reaches the question it answers, and the proof
that the interruption is invisible (`run_strip`) is why every resumed run
ended where its uninterrupted run ended: the replies read are the same list.
Everything Phase 167 proved about adversarial replies therefore holds for
interrupted dialogues too (`resumed_least`). At the `locate` junctions the
adversarial battery behaves as at the `nearest` ties: the truthful informant
is confirmed, the consistent liar is confirmed on the member impersonated
(the proved limit), and a single false reply is caught by the confirming
question.

### 7.4 What is left

* Only the newest open question can be resumed. Keeping several open ties
  (a stack), and saying which one a reply answers when it fits more than
  one, is the next step of the same line. *(Taken by Phase 173,
  [`STACKED_DIALOGUE_STUDY.md`](STACKED_DIALOGUE_STUDY.md); this study's
  measurement is now taken with the stack off, the reading it measured.)*
* No window: a question stays open however many unrelated turns pass.
  *(Taken by Phase 173: five unrelated turns.)*
* A word echo (`yes`, then `yes`) to a gloss-word question is still read as
  a confirmation, inside the proved limit (left by Phase 167).
* A true reply that is no option of the question (the carrier meant outside
  the head) is still refused `not-an-option` without saying it is evidence
  that the carrier meant is not in the head (left by Phases 150 and 167).

## In one paragraph

Yes. A question now stays open across turns that leave it alone, and a reply after one, two or three unrelated turns ends every dialogue exactly as the uninterrupted dialogue ends, for truthful informants and for adversarial ones. A question is answered once, the newest question supersedes an older one, and no question of the evaluation set is taken for a reply. Lean proves that an unrelated turn is invisible to the replies read. The same round ran Phase 167's adversarial battery at the `locate` junctions for the first time, and pinned `report anonymous` on its claim, which showed that one sentence of that report had asserted more than its measurement holds.

The figures: 9 of 9 marks; replies read after an unrelated turn 0 of 61 → 183 of 183, every one ending as the uninterrupted run; 243 of 243 adversarial runs unchanged by the interruption; 0 of 4,683 evaluation questions read as a reply; 0 members outside the head ever live over 791 runs.
