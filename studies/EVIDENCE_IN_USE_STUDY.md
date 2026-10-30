# The evidence model in use — every answer as one result on the command line, and column 3 in the evaluation's gate

## Tier 0 — the coarse read

**Question.** Can the command line print any answer as the one result model of Phase 169, without changing what it answers, and can the end-to-end evaluation replay column 3 for every answered case, so that a replay which no longer reproduces its answer fails the gate instead of going unseen?

**Verdict.** Yes. `GLM.py -q … --result` prints every evaluation answer as the ten-field result of Phase 169 with the same status, surface, kind and answer as the census, and changes no answer; `evaluation --replay` replays column 3 for every case expected answered and fails on a replay that does not verify, by a rule proved in Lean. The measurement took five takes: the first four were moved by stored measurements or a corpus that were stale or older than what they described (a corpus not refreshed with the last round's Lean files, a re-pin that staled a measurement, a census holding a stale answer, a refresh that had not read this round's own Lean file), never by the reading.

**Deciding figure.** 7 of 7 marks on the fifth take (4, 6, 6 and 7 of 7 on the first four); `--result` agrees with the census on 223 of 223; the gate replays 171 of 177 cases, 171 verify, 6 without a column 3, in 540 s on eight processes; evaluation 223 of 223; 5 of 5 theorems, 0 `sorry`.

**Recomputed by.** `glm_universal.reasoning.evidence_in_use_study.evidence_in_use_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 20 October 2026 (pre-registered 20 October 2026: §§0–6 were committed before the measurement of §7 was taken; measured 20 October 2026). Last altered 20 October 2026 (Phase 174: §7.5 notes the lines taken).*

## 0. What this document is

A pre-registration for Phase 171. It takes the first two lines of To-Do item
7 of `STATUS.md` §2.1 (*the evidence model, in use*, left by Phase 169;
[`EVIDENCE_MODEL_STUDY.md`](EVIDENCE_MODEL_STUDY.md) §7.5):

* the command line and the conversation still print their own objects; a
  `--json` reading of every answer through `Result` is the next use, and it
  changes no answer;
* the evaluation checks answers, not their replays, so the two column-3
  defects Phase 169 found had gone unseen; replaying column 3 for every
  answered case belongs in the evaluation's gate.

The other two lines of the item (surfaces with no column 3; the evidence kind
read from the computation rather than declared by query kind) are not taken.

**What was known when this was written.** The flag and the gate were written
first and tried on three questions to see that they ran:
`verify force = mass * acceleration` printed a result `answered`,
`certified`, `replayed: true`; `meaning of justice` printed `refused` with its
reason; the gate on the one case `verify-newton` replayed 1 of 1. Nothing of
§4 was run over the evaluation.

## 1. What was built

* **`GLM.py -q QUESTION --result`** — every question read as `-q` reads it
  (settled, routed by `runtime.router.route`, and on a refusal re-read once
  respelt, the respelt reading kept only if it answers) and printed as a JSON
  list of `Result` rows with the ten fields. With `--verify-tct`, column 3 is
  replayed and `replayed` says whether it verified. The function is
  `GLM.routed_result`. Without `--result` nothing the command line prints is
  touched.
* **`python3 -m glm_universal.evaluation --replay`** — after the evaluation,
  every case it expects answered is run again the way the evaluation runs it
  (a fresh interpreter, `GLM.py`), with `--result --verify-tct`
  (`evaluation/replay.py`). The gate fails when a replay that ran does not
  verify, when the result model does not read the case as answered, or when
  the process errs; a case with no column 3 is counted, not failed.

## 2. The formal half

`glm_lean/RequestProject/GLM/EvidenceInUse.lean` states the gate's
rule over a list of replayed rows (status answered or not; replay verified,
failed, or absent) and proves: a passing gate leaves no failed replay and no
unanswered row (`gate_sound`); one failed replay, anywhere, fails the gate
(`gate_fails_of_failed`); the gate on two batches passes exactly when it passes
on each and one of them replayed something (`gate_append`); a row with no
column 3 never fails it (`gate_absent_ok`); and the reading of a routed answer
into a result keeps its answer and its answered flag (`read_keeps_answer`).

## 3. Faculties

**Not derivation; not refusal; not addressing.** The round changes what the
system says about its answers, not the answers. It moves the **gate**: a
replay defect becomes a failure of the evaluation.

## 4. The marks

| mark | met when |
|---|---|
| **L1** | `EvidenceInUse.lean` declares the five theorems of §2 with no `sorry` and builds |
| **U1** | `GLM.routed_result` over all 223 evaluation questions agrees with the Phase 169 census (`reasoning/_data/evidence_model_study.json`) on status, surface, kind and answer for 223 of 223 |
| **U2** | every one of the 223 results printed by `--result` carries the ten fields of `runtime.evidence.FIELDS` |
| **U3** | the end-to-end evaluation, run after the change, has no failure (223 of 223) |
| **U4** | the replay gate over the cases the evaluation expects answered replays at least the 171 answers Phase 169 replayed, every one verifies, no result is read as other than answered, no process errs: the gate passes |
| **U5** | the gate's rule on hand-written rows: one failed replay fails it, one unanswered row fails it, one process error fails it, and a row without a column 3 does not |
| **U6** | the gate's wall time on eight processes is at most 15 minutes |

## 5. What would count against

U1 missed would mean the command line's routed reading and the Phase 169
census see different answers — the census would not describe what a user
gets. U4 missed would mean a replay defect exists now that the evaluation does
not see, which is the gap the gate is for (a defect found is a finding, then a
repair). U6 missed would mean the gate is too slow to be a routine part of a
close.

## 6. What is not claimed

The gate replays column 3 where the surface has one; the frames, reverse,
Python and engineering surfaces have none here, and their answers are counted
as unreplayable, not checked. `--result` covers `-q` (and `--query-file`); the
conversation (`--converse`) and the other entry flags still print their own
objects. The evidence kind is still declared by query kind. The gate is a
flag of the evaluation, not yet a step of `signoff --close`.

## 7. What came out

`PYTHONPATH=. python3 -m glm_universal.tools evidence-in-use` (stored in
`reasoning/_data/evidence_in_use_study.json`, digest-guarded over the study
module, the gate, the evaluation cases, the result model, the router, the
Three Column Thinking engine, `GLM.py` and the Phase 169 census; `--write`
re-takes it in about seventeen minutes on eight processes: the evaluation, the
`--result` reading of 223 questions and the gate).

The measurement was taken five times. The marks of the last take are the
result; the earlier takes are reported because what moved between them is the
finding of the round.

### 7.1 The marks

| mark | take 1 | take 2 | take 3 | take 4 | take 5 | met |
|---|---|---|---|---|---|---|
| **L1** | 5 of 5 theorems, 0 `sorry`; `lake build RequestProject.GLM.EvidenceInUse` passes; standard axioms | same | same | same | same | yes |
| **U1** | 217 of 223 | 223 of 223 | 222 of 223 | 223 of 223 | 223 of 223 | yes |
| **U2** | 223 of 223 | same | same | same | same | yes |
| **U3** | 221 of 223 | 222 of 223 | 223 of 223 | 223 of 223 | 223 of 223 | yes |
| **U4** | 168 replayed, 168 verified, **3 timed out** | 171 of 171 verified | 171 of 171 | 171 of 171 verified, 6 without a column 3 | 171 of 171 verified, 6 without a column 3 | yes |
| **U5** | 5 of 5 hand batches as declared | same | same | same | same | yes |
| **U6** | 405 s | 522 s | 525 s | 526 s | 540 s | yes |

### 7.2 What moved between the takes, and why

**Take 1 — the corpus had not been refreshed with the last round's Lean
files.** Phases 167 and 170 added `AdversarialDialogue.lean` and
`ContextFrames.lean` but the corpus was not refreshed with them before the
run ended; the refresh of this session (with `EvidenceInUse.lean` too) grew
the Lean goal set from 812 to 816 queries. Two evaluation pins that quote the
Lean corpus's figures (`report relay`, `report anonymous`) failed (U3), and
the six answers that quote corpus figures (`report lean`, `report retrieval`,
`report generated`, `report relay`, `report anonymous`, `corpus address`)
differed from the census taken before the refresh (U1). The two pins were
re-pinned for the refreshed corpus, as Phases 161–166 did on each Lean file;
their claims are unchanged (the stack still ahead on every set, carrying 7
and losing 0; the structural address still holding while the text search
falls to chance). The gate's three errors (U4) were **timeouts, not replay
failures**: `report lean`, `report relay` and `report anonymous` recompute
their measurement in column 3; run alone, `report lean` took 5 min 42 s and
`report relay` 7 min 15 s, each with `replayed: true`. The gate had inherited the
evaluation's 300 s per case. It now has its own limit,
`evaluation.replay.REPLAY_TIMEOUT = 1200` s (and `--replay-timeout`), an
amendment written after take 1 and named here as such.

**Take 2 — the re-pin made a stored measurement stale.** The Phase 169
census was re-taken (9 of 9 marks; 171 of 171 replays verified), and U1 and
U4 were met. But the edit to `evaluation/cases.py` for the re-pin made the
query-escalation measurement stale (its digest covers the evaluation file),
and `report query escalation` answered *the stored measurement is stale, so
no figure is reported*, which the evaluation grades wrong (U3, 222 of 223).
Re-taken with `tools queryesc --write`.

**Take 3 — the census still held the stale answer.** With the query
escalation re-taken the evaluation passed (223 of 223), but the census, taken
in take 2 while the measurement was stale, still held the stale text for
that one question, so `--result` and the census differed on one answer (U1,
222 of 223). The census's digest does not cover the stored measurements its
answers read, so it reported itself current. It was re-taken for take 4.

**Take 5 — the corpus refreshed with the round's own Lean file.** The
refresh that grew the goal set to 816 had started before
`EvidenceInUse.lean` was written; the refresh after take 4 read it, and the
goal set became 817, which moved the same two pins again (`report relay`,
`report anonymous`, 221 of 223). Each re-pin edits `evaluation/cases.py`, and
each edit stales the query-escalation measurement and nine others whose
digests cover that file, which is how take 2 failed. To stop the cycle for
the relay case, its pin now asks for the claim instead of the counts: the
report's standing words are read off the measurement (`ahead`, `level` or
`behind`), so the case asks for *ahead* on all three sets and *losing 0*. The
anonymous report's sentence is fixed text around its counts, so it was
re-pinned to the counts once more (text 674 → 57, structure 154 → 153 of
817). The query escalation, the census and this measurement were then
re-taken in that order.

Every difference U1 found across the takes is an answer of a stored
measurement that moved between the census and the reading; none is a
difference between what `--result` reads and what the command line answers.

### 7.3 What this answers

**The command line prints the model.** `GLM.py -q … --result` reads every
evaluation question into the ten-field `Result` (U2), with the same status,
surface, kind and answer as the census taken through the same router (U1),
and without `--result` it prints as before (U3: no answer moved; the two
re-pins are the corpus's, not the reading's).

**Column 3 is in the evaluation's gate.** `python3 -m glm_universal.evaluation
--replay --jobs 8` runs every one of the 177 cases expected answered through
`GLM.py --result --verify-tct` in a fresh interpreter: 171 replay and verify,
6 have no column 3 (the four `describe` answers, the numeral-arithmetic
description and the toolbox's Leech-norm answer), in under nine minutes. The
rule is the one `EvidenceInUse.lean` proves sound: one failed replay fails it
(`gate_fails_of_failed`), a row with no column 3 does not
(`gate_absent_ok`). The two Phase 169 defects would each have failed it.

**What the takes show about the tree.** A stored measurement is a cache of an
answer; four of this round's five takes were moved by a cache or a corpus
that was stale or older than what it described. The evaluation saw one of them (a
stale query-escalation answer graded wrong), the census none (it held a stale
answer and called itself current).

### 7.4 Faculties

**Not derivation; not refusal; not addressing.** The **gate** moved: a replay
that no longer reproduces its answer now fails the evaluation run with
`--replay`.

### 7.5 What is left

* The gate is a flag of the evaluation, not a step of `signoff --close`;
  making it one adds about nine minutes to a close. *(Taken by Phase 174,
  [`QUOTED_MEASUREMENTS_STUDY.md`](QUOTED_MEASUREMENTS_STUDY.md): the
  sign-off instrument `replay`.)*
* *(Taken by Phase 174 for the two answer censuses: their digests cover the
  stored measurements their answers quote.)* The census's digest
  (`reasoning/evidence_model_study.py`) does not cover the stored
  measurements the answers it reads quote, so it can hold a stale
  answer and report itself current (take 3). The same holds for any
  measurement that records answers.
* Adding a Lean file moved two evaluation pins that quote the Lean corpus's
  figures every time (Phases 161–166, and twice in 171). The relay case is
  now pinned on its claim; the anonymous report says its claim in fixed words
  around the counts, so a pin on the claim needs the report to read its
  standing off the measurement first, as the relay report does.
* `--result` covers `-q` and `--query-file`; `--converse`, `--steps`,
  `--ask`, `--python` and `--reverse` still print their own objects.
* The frames, reverse, Python and engineering surfaces have no column 3, and
  the evidence kind is still declared by query kind (To-Do item 7's other
  lines).

## In one paragraph

Yes. `GLM.py -q … --result` prints every evaluation answer as the ten-field result of Phase 169 with the same status, surface, kind and answer as the census, and changes no answer; `evaluation --replay` replays column 3 for every case expected answered and fails on a replay that does not verify, by a rule proved in Lean. The measurement took five takes: the first four were moved by stored measurements or a corpus that were stale or older than what they described (a corpus not refreshed with the last round's Lean files, a re-pin that staled a measurement, a census holding a stale answer, a refresh that had not read this round's own Lean file), never by the reading.

The figures: 7 of 7 marks on the fifth take (4, 6, 6 and 7 of 7 on the first four); `--result` agrees with the census on 223 of 223; the gate replays 171 of 177 cases, 171 verify, 6 without a column 3, in 540 s on eight processes; evaluation 223 of 223; 5 of 5 theorems, 0 `sorry`.
