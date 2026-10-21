# Adversarial replies at the `nearest` ties — what dialogue may and may not do when the informant is not truthful

## Tier 0 — the coarse read

**Question.** When the replies to the question at a `nearest` tie are false, contradictory, repeated, unanswered, malformed or close to two options, does the conversation ever promote a carrier the ranking excluded, and where does it confirm a member the replies did not honestly single out?

**Verdict.** No reply of any kind ever made a carrier outside the ranking's head live, over 560 adversarial runs through the conversation, and Lean proves this for any replies. A consistent liar cannot be told from a truthful informant, and Lean proves that limit too. One defect was found and fixed: a number repeated from the turn before was read as an option number of the confirming question, so a confirmation nobody gave was recorded (10 wrong confirmations after a first false reply). A yes-or-no question is now answered by its words only.

**Deciding figure.** 13 of 13 marks; 0 members outside the head ever live over 560 runs; echoes read as a confirmation by number 10 → 0, wrong confirmations after a false reply and an echo 10 → 1 (the remaining one within the proved limit); 118 of 118 consistent liars confirmed on the member impersonated; 223 of 223 evaluation cases unchanged.

**Recomputed by.** `glm_universal.reasoning.adversarial_dialogue_study.adversarial_dialogue_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 20 October 2026 (drafted and measured 20 October 2026, in one session; §5 says which marks were restated after the first run, and why).*

*Last altered 20 October 2026 (Phase 172: §7.4 says which of its lines that round took).*

## 0. What this document is

A study for Phase 167. It takes Part II.5 of the owner's plan of 19 October
2026 ([`source_material/GLM_19OCT26_1.md`](../source_material/GLM_19OCT26_1.md),
*expand adversarial interactive testing*), which extends
[`NEAREST_QUESTION_STUDY.md`](NEAREST_QUESTION_STUDY.md). Phase 150 measured
the question at the `nearest` ties under true replies and under one false
reply. The plan asks for more realistic conversations: false replies at every
turn, contradictory replies, unanswered questions, stale replies to an earlier
turn, intended carriers outside the candidate head, ambiguous or malformed
replies, and replies semantically close to more than one option. Its central
principle is stated there and adopted here: **dialogue may resolve uncertainty
inside an evidence-backed candidate set, but should not promote a candidate
that the underlying measurement excluded.**

## 1. What is proved

`overlay/glm_lean/RequestProject/GLM/AdversarialDialogue.lean` (namespace
`GLM.AdversarialDialogue`, on top of `GLM.NearestQuestion`; 0 `sorry`; axioms
`propext`, `Classical.choice`, `Quot.sound`). Phase 150's theorems speak of the
carrier meant under true replies; these drop the assumption.

* `adversary_live_subset`, `adversary_least`, `adversary_resolved_mem` —
  **whatever the replies**, every live member is a member of the head, at the
  scan's least distance, and a resolved tie names a member of the head.
* `contradicted_iff_inconsistent` — the live set is empty exactly when every
  member of the head contradicts some reply: a lie is caught exactly when it
  is a lie about every member.
* `conflicting_replies_contradict` — two different answers to one question
  leave no member.
* `repeat_reply_idem` — the same reply given twice prunes no more than once.
* `consistent_lie_live`, `consistent_lie_resolves`, `consistent_lie_confirmed`
  — **the limit**: replies all true of another member keep that member live,
  resolve the tie to it if they resolve it, and the confirming question keeps
  it. No reading of the replies can tell such a liar from a truthful
  informant about the member impersonated.

## 2. The mechanism

Since Phase 146 a reply could be given as an option's number (`1`, `2`).
The first run of this study (§7.2) found that a number repeated from the turn
before is read against the *new* question's option list: the `1` that
answered *what is its cols?* became option 1 of *is it exactly X?* — *yes*.
The rule is now: **a question whose options are *yes* and *no* — the
confirming question and the gloss-word questions — is answered by those words
only, never by an option number** (`timed_question.YES_NO_BY_NUMBER`, off;
`timed_question.is_yes_no`). Numbers are still read as option positions for
every other question. The switch on restores the old reading, and the
measurement takes the affected policies both ways in one run.

## 3. The informants

The 18 distinct tied heads of Phase 148's six sets (48 members) are those of
Phase 150, each asked at one of its points, `nearest to <point>`, through the
conversation (`runtime/conversation.Conversation`), so every reply is read as
the next turn exactly as a user's would be.

| policy | what the informant says |
|---|---|
| **A0** truthful | the reply of the member meant, to every question (the control) |
| **A1** consistent liar | the reply *another* member would give, to every question: every ordered pair of distinct members of a head (118) |
| **A2** every reply false | the first offered option that does not keep the member meant; to the confirming question, the false word |
| **A2b** first reply false | Phase 150's D2 through the conversation: one false reply, then true ones (a removed member's true answer is still given and read) |
| **A3** contradictory | in the `given` form, two different answers to the first question; as the next turn, the true first reply and then another option of the same question |
| **A4** unanswered | the question left unanswered: an unrelated turn (`nearest to C moved 8 by 1/2`, a single-carrier head), then the true reply |
| **A5** echo | the true reply, then the same text again at the next turn |
| **A6** false then echo | a false first reply, then the same text again |
| **A7** outside the head | the 10 tied points whose origin is not in the head; true replies about the origin |
| **A8** malformed | 14 texts (`maybe`, `both`, `2;4`, `99`, the empty text, …) after the first question; and `given` replies without an answer |
| **A9** near two options | two options joined (`a or b`, `a and b`, `a b`, `a/b`), their common prefix, and the register prefix they share; the control is each option's token in capitals |

## 4. Faculties

**Refusal.** The round removes wrong confirmations at a counted cost: an echo
is no longer read as a confirmation, and a reply that used to be read by its
position is now not read (the text is passed to the session as a whole query,
which refuses it). **Not derivation, not addressing.**

## 5. The marks

The marks were written with the measuring module, before the first run; the
first run (§7.2) showed four of them were stated wrongly, and they were
restated before the final run, as recorded here.

| mark | met when |
|---|---|
| **L1** | `AdversarialDialogue.lean` states the nine theorems of §1 with no `sorry`, and builds |
| **A0** | truthful: every run confirmed on the member meant, 0 wrong |
| **A1** | consistent liar: every run confirmed on the member impersonated (the proved limit, measured) |
| **A2** | every reply false: no run confirmed on the member meant, and every confirmation reached is on a member every reply read was true of |
| **A2b** | first reply false: every run contradicted, 0 on a wrong member |
| **A3** | the `given` form always contradicted; as the next turn, 0 confirmed on a wrong member and 0 runs ending on a wrong member through a number read on a yes-or-no question |
| **A4** | 0 replies read after an unrelated turn |
| **A5** | 0 echoes read as a confirmation by number |
| **A6** | 0 runs ending on a wrong member through a number read on a yes-or-no question, and every wrong confirmation left is on a member every reply read was true of (within the limit of A1) |
| **A7** | 0 of the outside-head points confirmed |
| **A8** | 0 malformed texts read; every `given` reply without an answer refused `malformed-reply` |
| **A9** | 0 near texts read; every control read |
| **P** | over every run, 0 members outside the head ever live and 0 values outside the head |

**Restated after the first run.** A2b first said only *contradicted*: two
runs stopped open because the driver gave no reply once the member meant had
been removed; the driver now gives that member's own answer, which Phase 150's
loop also gives. A3 first said *0 wrong*: three runs ended *resolved* (not
confirmed) on a wrong member, because the contradicting text was a number read
by position on the next question — the defect of §2; the mark now counts
confirmations and position readings. A6 first said *0 confirmed wrong*: one
wrong confirmation is left that no reading of the words can remove (a false
*yes* to a gloss-word question, then *yes* again: both replies are true of the
other member, so it is A1's limit); the mark now asks that every wrong
confirmation be inside that limit. A8's second `given` probe was first
`… given ` (a trailing space), which the request reader strips; it is now
`… given <key> is`.

A further gate, outside the marks: the end-to-end evaluation keeps every
answer and refusal (223 of 223).

## 6. What is not claimed

The informants are declared policies, not users. The questions are still
chosen by what splits, as in Phases 145–150. A reply carried across an
unrelated turn is still not read — measured here (A4) as a refusal, not
repaired. The other three ties of To-Do item 1 still have no question. The
remaining wrong confirmation of A6 is not fixable by reading replies
(`consistent_lie_confirmed`); only evidence from outside the dialogue could
catch it.

## 7. What came out

`PYTHONPATH=. python3 -m glm_universal.tools adversarial-dialogue` (stored in
`reasoning/_data/adversarial_dialogue_study.json`, digest-guarded;
`--write` re-takes it in about two minutes on eight cores).

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **L1** | 9 of 9 theorems, 0 `sorry`; `lake build RequestProject.GLM.AdversarialDialogue` passes | yes |
| **A0** | 48 of 48 confirmed on the member meant, 0 wrong | yes |
| **A1** | 118 of 118 confirmed on the member impersonated, 0 contradicted | yes |
| **A2** | 48 of 48 confirmed, every one on a member every reply read was true of; 0 on the member meant | yes |
| **A2b** | 48 of 48 contradicted, 0 wrong | yes |
| **A3** | `given` form 18 of 18 contradicted; next turn, with the old reading 3 runs ended on a wrong member through a number read on a yes-or-no question, now 0; 0 confirmed wrong either way | yes |
| **A4** | 0 of 48 replies read after the unrelated turn | yes |
| **A5** | echoes read as the confirmation: 9 with the old reading (7 of them by number), 2 now (both words, `yes` and `no`, given twice); 0 by number | yes |
| **A6** | echoes read as the confirmation by number 10 → 0; wrong confirmations 10 → 1, the one left a word echo inside A1's limit | yes |
| **A7** | 0 of 10 confirmed (5 contradicted, 5 refused) | yes |
| **A8** | 0 of 252 malformed texts read; 36 of 36 `given` probes refused `malformed-reply` | yes |
| **A9** | 0 of 74 near texts read; 45 of 45 controls read | yes |
| **P** | 0 members outside the head ever live, 0 values outside it, over 560 runs | yes |

The gate: the end-to-end evaluation, run with the new reading, has no failure
(223 of 223). The new reading changes only how a conversation turn is
matched to the question put; a `given` reply is matched by its token, as
before.

### 7.2 What the first run found

With the old reading, 9 of the 48 true replies repeated at the next turn were
read as replies to the confirming question: 6 confirmed (a `1` read as option
1, *yes*) and 3 contradicted (a `2` read as option 2, *no*). None of these
named a wrong member, because the first reply was true. After a false first
reply the same reading confirmed a wrong member 10 times out of 48: the
confirming question, whose purpose is to turn a false resolution into a
contradiction (`GLM.AnsweringQuestion.confirm_catches`), was answered by a
text the informant had given to a different question. The same position
reading made a contradicting text resolve a tie to a wrong member three times
(A3). A gloss-word question offers *yes* and *no* too, and a position read on
it has the same fault, so the rule covers every yes-or-no question rather than
the confirming question only. The one test that pinned the old reading
(`test_answering_question.test_match_reply`, `2` read as *no*) now pins the
new one, and the old one under the switch.

### 7.3 What this answers

The principle holds under every informant measured, and is now a theorem for
any replies (`adversary_least`): dialogue resolves inside the head and never
outside it. What dialogue cannot do is also exact: a lie is caught only when
no member of the head is consistent with every reply
(`contradicted_iff_inconsistent`), so a liar who answers as another member
would is confirmed on that member (A1, 118 of 118; A2, 48 of 48, because
every-reply-false at a two-member head *is* impersonation). The confirming
question protects against a single false reply followed by true ones (A2b, 48
of 48 contradicted), and, since this round, against a reply echoed from an
earlier question.

### 7.4 What is left

* A reply to an earlier question is still not read once an unrelated turn
  intervenes (A4): the dialogue is dropped, not resumed. Resuming it would
  need the conversation to keep an open tie across turns.
* A word echo (`yes`, then `yes`) to a gloss-word question and then the
  confirming question is still read as a confirmation; it is inside the
  proved limit, and only evidence from outside the dialogue could catch it.
* Where the carrier meant lies outside the head, a true reply that is no
  option of the question is refused `not-an-option` (A7, 5 points); the answer
  still does not say that the reply is evidence the carrier meant is not in
  the head (left by Phase 150).
* The same adversarial battery has not been run at the `locate` junction
  (Phase 146), which reads its replies by the same code.

The first and the last of these were taken by Phase 172
([`RESUMED_DIALOGUE_STUDY.md`](RESUMED_DIALOGUE_STUDY.md)): a question now
stays open across unrelated turns, and the battery has been run at the
`locate` junctions. A4 above is still taken with the conversation's
`RESUME_OPEN_TIE` off, the reading this study measured.

## In one paragraph

No reply of any kind ever made a carrier outside the ranking's head live, over 560 adversarial runs through the conversation, and Lean proves this for any replies. A consistent liar cannot be told from a truthful informant, and Lean proves that limit too. One defect was found and fixed: a number repeated from the turn before was read as an option number of the confirming question, so a confirmation nobody gave was recorded (10 wrong confirmations after a first false reply). A yes-or-no question is now answered by its words only.

The figures: 13 of 13 marks; 0 members outside the head ever live over 560 runs; echoes read as a confirmation by number 10 → 0, wrong confirmations after a false reply and an echo 10 → 1 (the remaining one within the proved limit); 118 of 118 consistent liars confirmed on the member impersonated; 223 of 223 evaluation cases unchanged.
