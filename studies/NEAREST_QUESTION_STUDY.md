# The question at the `nearest` ties — a reply turn for the ranking's head

## Tier 0 — the coarse read

**Question.** Can a `nearest` answer whose ranking head is a tie end with the question that splits it, and read the replies, as the `locate` junction does, without a reply ever moving the answer off the head, under a frozen-path comparison of the whole evaluation?

**Verdict.** Yes. A `nearest` answer whose ranking head is a tie now ends with the question that splits it, and its `given` replies are read as the next turn. Over the 18 distinct tied heads of Phase 148's six sets, with each of the 48 members as the carrier meant, true replies confirmed the member meant in 48 of 48 runs and never a wrong one, with at most 2 replies; one false reply ended contradicted in 48 of 48. A carrier meant outside the head was never confirmed. Every one of the 212 evaluation cases keeps its status, and the junction answer keeps its old text as a verbatim prefix. No mark was missed.

**Deciding figure.** 8 of 8 measured marks and L1; 321 tied points, 18 distinct heads; 48/48 confirmed on the member meant, 0 wrong, at most 2 replies; 48/48 contradicted after one false reply; 0 of 10 outside-head points confirmed; 150/150 conversation turns verify, 156/156 altered claims rejected; frozen path 212/212 same status, 0 undeclared.

**Recomputed by.** `glm_universal.reasoning.nearest_question_study.nearest_question_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

A **pre-registration** for Phase 150, item 2 of [`STATUS.md`](../STATUS.md)
§2.1 (*the question at the other ties*, left by Phases 145, 146 and 148,
[`ANSWERING_QUESTION_STUDY.md`](ANSWERING_QUESTION_STUDY.md) §7.5). §§0–6
were committed with the Lean file and the answering-path code, before the
stored measurement and the frozen-path comparison were taken; §7 is what came
out.

**What the item asked.** Since Phase 146 only the `locate` junction answer
puts a question and reads a reply. Four refusals at a tie had no vocabulary:
the crowded zero cell of the address read, the `report hole` ties, the
decoder's `classify` refusal, and a `nearest` read whose head is a tie. The
item asks for one of them to be given a vocabulary and the reply its turn.
This round takes the **`nearest` ties**, because the vocabulary already
exists: the declared attribute and gloss questions of Phase 145
(`timed_question.attribute_vocabulary`) are questions about carriers, and
every member of a `nearest` head is a carrier of the address table.

* **A certified junction at the head** — the guarded read certifies a
  junction (carriers at one coordinate vector) and the gap after it. Since
  Phase 148 the answer named the junction and stopped.
* **A tie the scan found** — the guarded read refuses, and two or more
  carriers are at one least distance. Since Phase 148 the answer named them
  and said no margin is certified.

In both cases the head is now held open as a tie over its members
(`timed_question.OpenTie`), the replies given (`nearest to X given key is
reply; …`) are applied in order, and the answer ends with the question that
comes next, or the confirming question once one member is left. A reply is
read as the next turn of a conversation exactly as Phase 146's `locate`
replies are. Column 3 re-derives the live set and the split from the
register attributes, apart from the question module.

**What was known before this was written.** The ties were counted while the
code was built: 321 tied points of Phase 148's six sets (193 under a
certified junction, 128 where the read refuses), 18 distinct heads, 10 tied
points whose origin is not in the head. The answering path's own loop (D1,
D2, D3), the battery (Q1), the controls (R1) and the conversation (C1) were
each run once while building. That first C1 run found **8 of 150 turns
whose column-3 script did not verify**: every first turn of the 8-member
junction of the `filled_*` carriers. Column 2 listed the question's groups in
the junction table's member order, and column 3 in the scan's label order, so
the same split was written two ways. The `asks` claim is now stated as a
partition (groups and members sorted) on both sides, and the run was not
repeated before this was committed. The baseline of the whole evaluation
(`reasoning/_data/ties_ladder_baseline.json`, shared with Phase 151) was
taken before any answering-path file of either round was edited; the two Lean
files were written while it was being taken, so the baseline's Lean
declaration count may already include them. **Neither the stored measurement
nor the frozen-path comparison had been run when this was committed.**

## 1. What is proved before any code

`RequestProject/GLM/NearestQuestion.lean` (namespace `GLM.NearestQuestion`),
on top of `GLM.NearestAddress` and `GLM.AnsweringQuestion`; no `sorry`,
standard axioms only.

* `HeadSet` — the head of a ranking: every carrier at the least distance from
  the point, and only those.
* `head_mem_least`, `after_least` — every member of the head, and so every
  member a history of replies leaves live, is at the least distance: **a
  reply never moves the answer off the scan's head.**
* `resolved_least` — a tie resolved by replies names a carrier no other
  carrier is strictly nearer to.
* `resolved_is_meant` — if the carrier meant is in the head and the replies
  are true of it, the tie resolves to that carrier.
* `outside_never_confirmed` — if the carrier meant is not in the head, true
  replies never confirm a member: the confirming reply empties the live set.
* `head_card_le_one_iff` — the head has at most one member exactly when its
  member is the strict nearest carrier: the question is put only where
  `ranking_head_of_strict` does not already name the head.

## 2. The rule

As §0. The tie is the guarded read's certified junction when the read
certifies, and the scan's least-distance set when it refuses; the head of a
single carrier puts no question, and a `given` reply to it is refused as
`no-tie`. A reply that names no declared question is refused as
`unknown-question`, one that is no option of its question as
`not-an-option`, and replies that leave no member as `contradicted` — the GLM
reports the contradiction rather than choose.

## 3. The questions

**The ties.** Every point of Phase 148's six sets whose ranking head holds
two or more carriers; each distinct head is one tie.

**The battery** (`nearest_question_study.BATTERY`, ten questions): the zero
point (an uncertified tie of `golay_codeword_0` and `hexacode_word_0`) asked,
replied to, confirmed and contradicted; the albedo junction asked and replied
to; and the refusals `no-tie`, `unknown-question`, `not-an-option`, with a
single-carrier head as the control.

**The controls** (R1): `yes`, `no`, `1`, `2`, `4`, `albedo`, each as the
first turn of a conversation and after a `nearest` answer whose head is one
carrier.

**New evaluation cases** (E1): `nearest-tie-question`, `nearest-tie-reply`,
`nearest-tie-confirmed`, `nearest-tie-contradicted`, `nearest-tie-no-tie`.

## 4. The marks, declared before the measurement

| mark | claim |
|---|---|
| **L1** | `NearestQuestion.lean` builds with the full `lake build`, no `sorry`, standard axioms only |
| **D1** | every distinct head, with each member as the carrier meant, through the answering path's own loop: confirmed on that member, 0 wrong, replies at most `n - 1` and at most `⌈log₂ n⌉ + 1` |
| **D2** | the same with the first reply false: every run ends contradicted, 0 on a wrong member |
| **D3** | the tied points whose origin is not in the head: true replies about the origin confirm no member (`outside_never_confirmed`) |
| **C1** | one point of every distinct head, `nearest to <point>`, then the truthful reply to every question put, for each member as the carrier meant, through the conversation: confirmed on the truth, 0 wrong; column 3 verifies every turn and rejects every altered `live` or `asks` claim |
| **Q1** | the battery comes out as declared, every answered turn's column-3 script verifying |
| **R1** | none of the controls is read as a reply |
| **E1** | the five new evaluation cases pass through the CLI |
| **F1** | every evaluation case of the shared baseline is present with the same status; every moved text has a declared cause (`ties_ladder_frozen.DECLARED_CAUSES`); `nearest-address-junction`, which now ends with the question, keeps its old text as a verbatim prefix |

## 5. What would count against

D1 or C1 confirming a wrong member, or D3 confirming any member, would mean
the reply turn names a carrier the replies do not single out. F1 failing on a
status or the prefix would mean the question moved an answer it had no
business moving.

## 6. What is not claimed

The other three ties of the item — the crowded zero cell of the address
read, the `report hole` ties and the decoder's `classify` refusal — are not
given a vocabulary here. The questions are chosen by what splits, as in
Phases 145–146, not by what a user can answer; replies are taken as true
except where D2 makes one false. A reply carried across an unrelated turn is
still not read.

## 7. What came out

`python3 -m glm_universal.tools nearest-question` (stored in
`reasoning/_data/nearest_question_study.json`, digest-guarded); the frozen
path is `python3 -m glm_universal.tools ties-ladder-frozen`
(`reasoning/_data/ties_ladder_frozen.json`, shared with Phase 151).

In short: yes. Every tied head of Phase 148's sets was resolved to the
member meant by true replies, never to a wrong one, and a lie or a carrier
outside the head never produced a confirmation. No mark was missed.

### 7.1 The marks

| mark | result | met |
|---|---|---|
| **L1** | `NearestQuestion.lean` builds with the full `lake build` (8,251 jobs), no `sorry` | yes |
| **D1** | 48 of 48 runs (18 heads, each member as the carrier meant) confirmed on that member, 0 wrong; 54 replies in all, at most 2 in a run; all 48 within `n - 1` and within `⌈log₂ n⌉ + 1` | yes |
| **D2** | the first reply false: 48 of 48 ended contradicted, 0 on a wrong member | yes |
| **D3** | 10 tied points whose origin is not in the head: 0 confirmed (5 contradicted, 5 refused `not-an-option`) | yes |
| **C1** | 48 of 48 conversations confirmed on the truth, 0 wrong; 150 of 150 turns verify in column 3; 156 of 156 altered `live` or `asks` claims rejected | yes |
| **Q1** | the battery's 10 questions as declared; 6 of 6 answered turns verify | yes |
| **R1** | 0 of the 12 controls read as a reply | yes |
| **E1** | the 5 new evaluation cases pass through the CLI | yes |
| **F1** | 212 of 212 baseline cases present with the same status; 204 the same text; the 8 moved texts all declared (the five reports the tree measures of itself, `report language` and `report query escalation`, which count the evaluation's cases, and `nearest-address-junction`, which keeps its old text as a verbatim prefix); 0 undeclared; 5 new cases | yes |

### 7.2 The census

321 points of Phase 148's six sets have a head of two or more carriers: 193
under a certified junction and 128 where the guarded read refuses. They make
18 distinct heads (3 certified, 17 uncertified; two heads occur both ways).
By size: 13 heads of two carriers, two of three, two of four and one of
eight (the junction of the `filled_*` carriers), 48 members in all. No run
needed more than two replies (54 over the 48 runs), the eight-member head
included.

### 7.3 What this answers

The `nearest` tie is the second refusal at a tie that now puts a question
and reads the reply, after Phase 146's `locate` junction. The answer is
never moved off the scan's head: every member a history of replies leaves
live is at the least distance (`after_least`), and a resolved tie names a
carrier no other carrier is strictly nearer to (`resolved_least`). Where the
carrier meant is not in the head at all (D3), the truthful reply is either
no option of the question (refused `not-an-option`, five points of the
acoustic head) or leaves no member (contradicted, five points at the zero
cell); in neither case is a member confirmed (`outside_never_confirmed`).

### 7.4 What is left

* The other three ties of the item — the crowded zero cell of the address
  read, the `report hole` ties and the decoder's `classify` refusal — still
  have no declared vocabulary.
* A reply carried across an unrelated turn is still not read, and replies
  are still taken as true except for D2's single lie.
* Where the carrier meant lies outside the head, a truthful reply that is no
  option of the question is refused `not-an-option`; the answer does not say
  that the reply is evidence the carrier meant is not in the head at all.
