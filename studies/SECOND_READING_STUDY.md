# A second reading before answering — what agreement buys, and what it costs

## Tier 0 — the coarse read

**Question.** The escalated-operations study left one declared failure: the program-text operation answers 13 of 576 queries *wrongly* rather than refusing, because its unanimity contract is applied to a single reading and a cell can be unanimous and unanimously wrong. Does requiring a **second, independent reading** to agree before answering remove the wrong answers, and what does it cost in refusals?

**Verdict.** Exactly one of the six declared configurations is adopted: the strict guard against the metric second reading removes every wrong answer the program-text operation gave, keeps most of the correct ones, and beats a matched-refusal control that gives up the same number of answers; the veto guard never reaches safety, and the code-layer reading is too silent to guard with.

**Deciding figure.** <!--figure:secondread-adopted-->1<!--/figure--> of <!--figure:secondread-configurations-->6<!--/figure--> declared configurations is adopted — `<!--figure:secondread-shipped-->strict+margin<!--/figure-->`, which answers <!--figure:secondread-program-correct-->366<!--/figure--> of the program operation's queries correctly, <!--figure:secondread-program-wrong-->0<!--/figure--> wrongly, and gives up <!--figure:secondread-given-up-->150<!--/figure--> answers to remove all thirteen wrong ones, where refusing the same number at random removes <!--figure:secondread-matched-removes-->2<!--/figure-->.

**Recomputed by.** `glm_universal.reasoning.second_reading.measure`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is, and what it is not

The round that closed before this one measured seven operations under one
refusal contract — *answer only when the rung's cell is non-empty and every
carrier in it carries the same label* — and reported, as a failure rather than
a footnote, that the program-text operation answers **13 of 576** queries
wrongly. The diagnosis was written down at the time and is the starting point
here: the label of that operation, *which file is this declaration written
in*, is not a property of the 24 structural coordinates at all, so a cell can
be unanimous and unanimously wrong, and unanimity **across rungs of one
reading** is not enough to catch it.

§3.4 of [`STATUS.md`](../STATUS.md) named the smallest experiment that would
move it: *require agreement with a second reading before answering, and
measure what that costs in refusals.* This document is that experiment. It is
declared before it is run, in the discipline of Phases 20–24 and 31–35: the
readings, the guards, the controls and the pass marks are fixed here first,
and every configuration declared is reported afterwards whether it passes or
fails.

**What was known before the protocol was fixed.** Two things, and they are
stated so that the pre-registration is not read as more than it is. First, the
*shape* of both second readings was scouted — a reading that refuses
everything, or answers everything, would test nothing, so each was checked to
be non-degenerate on the carriers before being declared. Second, the primary
reading is frozen: it is exactly the escalated norm-ladder reading of
[`OPERATION_ESCALATION_STUDY.md`](OPERATION_ESCALATION_STUDY.md), not re-tuned
here. What was **not** known when the marks below were written is what any
guard scores; the marks, the controls and the full cross of configurations
were fixed before the measurement this document reports, and all of them are
reported.

## 1. The primary reading, frozen

Unchanged from the previous round, and re-derived rather than re-tuned: the
norm-indexed ladder, coarsest first; at each rung the query is quantised, the
cell's labels are read, and the reading answers when they are unanimous and
goes on to the next rung when they are not. A query the whole ladder refuses
is refused.

The queries are the same four declared deterministic perturbations, over the
same carriers, so every figure below is comparable line for line with the
table in §3 of the previous study.

## 2. The two second readings

A second reading is only worth having if it can fail where the first fails
*independently*. Both readings below are therefore taken at a different layer
from the ladder's quantisation, and neither uses the label.

**`code` — the code layer.** The carrier set fixes, per coordinate, the
**lower median** of that coordinate over the carriers: the ⌈n/2⌉-th value in
sorted order, exactly, as a `Fraction`. A vector becomes a 24-bit word by
setting bit *j* when its *j*-th coordinate is strictly greater than the *j*-th
median. The word is decoded by **complete Golay syndrome decoding**, which
returns a codeword only when one is forced and reports `ambiguous` at
distance 4 rather than breaking the tie. The reading refuses when the
decoding is ambiguous; otherwise its cell is the set of carriers whose own
word decodes to the same codeword, and it answers when their labels are
unanimous. This is the substrate read one layer down from the lattice: the
`[24, 12, 8]` code, where the error correction is the reading.

**`margin` — the metric layer.** The exact `ℓ¹` distance from the query to
every carrier is computed over `Fraction`s. Let `d₁` be the smallest. The
reading's answer set is every carrier at distance `≤ 2·d₁`, and it answers
when their labels are unanimous, refusing otherwise. There is no quantisation
and no code: it is the nearest-neighbour reading with a declared, scale-free
margin, and it refuses exactly when a carrier of another label is within twice
the nearest distance.

## 3. The two guards

Both take the primary answer `p` and a second answer `s`, either of which may
be a refusal.

* **`strict`** — answer `p` only when `s` is an answer and `s = p`; refuse
  otherwise. A second reading that refuses therefore blocks the answer.
* **`veto`** — answer `p` unless `s` is an answer and `s ≠ p`. A second
  reading that refuses therefore stands aside.

Both are measured against both readings, and against the two of them together
(`strict` requires both to agree; `veto` refuses when either contradicts), so
six guarded configurations in all.

What these guards do and do not do is a theorem rather than a hope, and is
proved in `RequestProject/GLM/SecondReading.lean`: a guard never invents an
answer the primary did not give, never turns a correct answer into a wrong
one, and — the point of the round — answers wrongly only where the second
reading is *also* wrong in the same way. The measurement below is therefore
about one question only: how often that happens, and what the guard gives up
to prevent it.

## 4. The controls, and the marks

**Control A — matched refusal.** A guard buys safety by refusing; the question
is whether it refuses *the right queries*. The control gives up exactly as
many primary answers as the guard does, choosing them by a digest of the exact
query rather than by a reading, and counts how many wrong answers that
removes. A guard that does no better than this is refusing at random.

**Control B — the second opinion with the relation destroyed.** The second
reading's index is kept and its labels are reshuffled by a declared seeded
permutation, so the control answers as often as the reading does and its
agreements are accidents. A guard built on it should lose answers without
removing wrongs.

**The marks, declared before the measurement.** A guarded configuration is
**adopted** only if all four hold:

* **M1 — safety.** On the program-text operation, `wrong = 0`.
* **M2 — cost.** On the program-text operation, `correct ≥ 252`, half of the
  503 the unguarded escalation answers correctly, rounded up.
* **M3 — better than refusing more.** On the program-text operation, the guard
  removes strictly more wrong answers than Control A removes when it gives up
  the same number of answers.
* **M4 — no damage elsewhere.** On each of the other six operations, the guard
  introduces no wrong answer and loses at most half of the correct answers the
  unguarded escalation gets.

If no configuration is adopted, that is the result and it is reported as one.
If more than one is adopted, the one adopted for the shipped path is the
cheapest by refusals, and the others are reported beside it.

## 5. What was measured

<!-- generated: secondread-operations -->
| operation | reading | queries | correct | wrong | refused |
|---|---|---|---|---|---|
| `register` | the escalated ladder | 568 | 541 | 0 | 27 |
|  | the code layer | 568 | 178 | 3 | 387 |
|  | the metric layer | 568 | 539 | 0 | 29 |
| `dimension` | the escalated ladder | 96 | 80 | 0 | 16 |
|  | the code layer | 96 | 0 | 0 | 96 |
|  | the metric layer | 96 | 63 | 0 | 33 |
| `chemistry` | the escalated ladder | 96 | 96 | 0 | 0 |
|  | the code layer | 96 | 41 | 0 | 55 |
|  | the metric layer | 96 | 96 | 0 | 0 |
| `physics` | the escalated ladder | 96 | 82 | 0 | 14 |
|  | the code layer | 96 | 0 | 0 | 96 |
|  | the metric layer | 96 | 66 | 0 | 30 |
| `harmony` | the escalated ladder | 96 | 95 | 0 | 1 |
|  | the code layer | 96 | 16 | 0 | 80 |
|  | the metric layer | 96 | 96 | 0 | 0 |
| `program` | the escalated ladder | 576 | 503 | 13 | 60 |
|  | the code layer | 576 | 24 | 16 | 536 |
|  | the metric layer | 576 | 384 | 0 | 192 |

Read alone, before any guard: the primary reading is the one the previous round shipped, and the two second readings are declared in §2.

Operations the primary answers wrongly: `program`.  Second readings that answer wrongly: `register`/code, `program`/code.
<!-- end generated -->

Three readings of that table, before any guard is applied.

**The code-layer reading is silent, and not sound.** It refuses most of what
it is given — on the two operations whose label is an exponent vector or a
sub-domain it answers nothing at all — and where it does answer it is not
always right: it answers 3 of the register operation's queries and 16 of the
program operation's wrongly. So it cannot be adopted as a reading, and
whatever safety a guard built on it has is *joint*: it comes from two readings
having to agree, not from either one being reliable.

**The metric reading is the surprise, and it has to be stated carefully.**
Read alone on the program operation it answers 384 correctly and **nothing**
wrongly, which is more correct answers than the adopted guard keeps. That is a
measurement on this sample and not a property: the margin refuses whenever a
carrier of another label is within twice the nearest distance, and on this
sample that happens to catch every case the ladder gets wrong. It is also not
a candidate to replace the primary reading, because it is *worse* where the
primary is strong — 539 against 541 on the register operation, 63 against 80
on dimension, 66 against 82 on physics — and because it costs a distance to
every carrier rather than a quantisation.

**The premise of the round still holds.** The primary reading answers 13 of
the program operation's 576 queries wrongly and nothing wrongly anywhere else,
which is the failure this study exists to attack. The test suite fails if that
stops being true, so the study cannot quietly become a study of nothing.

## 6. The guards, and the marks

<!-- generated: secondread-marks -->
| configuration | program correct | program wrong | program refused | M1 | M2 | M3 | M4 | verdict |
|---|---|---|---|---|---|---|---|---|
| `strict+both` | 19 | 0 | 557 | yes | no | no | no | not adopted |
| `strict+code` | 21 | 0 | 555 | yes | no | yes | no | not adopted |
| `strict+margin` | 366 | 0 | 210 | yes | yes | yes | yes | **adopted** |
| `veto+both` | 490 | 9 | 77 | no | yes | yes | yes | not adopted |
| `veto+code` | 490 | 13 | 73 | no | yes | no | yes | not adopted |
| `veto+margin` | 503 | 9 | 64 | no | yes | yes | yes | not adopted |

The marks are those of §4, fixed before the measurement: **M1** safety: on the program-text operation the guarded reading answers nothing wrongly; **M2** cost: on the program-text operation the guarded reading keeps at least 252 correct answers, half of the 503 the unguarded escalation gets; **M3** better than refusing more: the guard removes strictly more wrong answers than the matched-refusal control removes for the same number of answers given up; **M4** no damage elsewhere: on each other operation the guard introduces no wrong answer and loses at most half the correct answers.

1 of 6 configurations are adopted; the cheapest by answers given up is strict+margin.

What the configurations that fail M4 cost elsewhere: `strict+both` — register: 541 -> 176 correct, dimension: 80 -> 0 correct, chemistry: 96 -> 41 correct, physics: 82 -> 0 correct, harmony: 95 -> 16 correct; `strict+code` — register: 541 -> 176 correct, dimension: 80 -> 0 correct, chemistry: 96 -> 41 correct, physics: 82 -> 0 correct, harmony: 95 -> 16 correct.
<!-- end generated -->

Exactly one of the six declared configurations is adopted: the strict guard
against the metric second reading removes every wrong answer the program-text
operation gave, keeps most of the correct ones, and beats a matched-refusal
control that gives up the same number of answers; the veto guard never reaches
safety, and the code-layer reading is too silent to guard with. What the table
records, mark by mark:

* **Safety is only reached by the strict guard.** All three strict
  configurations take the program operation's wrong count to zero. Every veto
  configuration fails **M1**: vetoing on the metric reading removes 4 of the
  13 wrong answers and leaves 9, and vetoing on the code layer removes none at
  all. The reason is structural rather than incidental — a veto only fires
  when the second reading *answers and disagrees*, and on exactly those
  queries the second reading is usually refusing.
* **Only one strict configuration survives the cost mark.** `strict+code` and
  `strict+both` are safe and useless: they answer 21 and 19 of 576, far below
  the declared floor of 252, and they fail **M4** catastrophically elsewhere —
  on the code layer the dimension and physics operations fall to zero correct
  answers and the register operation from 541 to 176. `strict+margin` keeps
  366 and damages nothing: no other operation loses a quarter of its answers,
  let alone half.
* **The guard is not just refusing more.** `strict+margin` gives up 150
  answers and removes all 13 wrong ones. Refusing 150 answers chosen by a
  digest instead removes 2. That is **M3**, and it is the mark that
  distinguishes a reading from a coin.

## 7. The controls

<!-- generated: secondread-controls -->
| configuration | answers given up | wrong answers removed | matched refusal removes | matched refusal correct / wrong | reshuffled-label guard correct / wrong |
|---|---|---|---|---|---|
| `strict+both` | 497 | 13 | 13 | 19 / 0 | 6 / 0 |
| `strict+code` | 495 | 13 | 12 | 20 / 1 | 10 / 0 |
| `strict+margin` | 150 | 13 | 2 | 355 / 11 | 46 / 1 |
| `veto+both` | 17 | 4 | 0 | 486 / 13 | 301 / 10 |
| `veto+code` | 13 | 0 | 0 | 490 / 13 | 493 / 13 |
| `veto+margin` | 4 | 4 | 0 | 499 / 13 | 304 / 10 |

Control B read alone on the same operation: the code layer with its labels reshuffled answers 12 correctly and 12 wrongly, and the metric layer reshuffled 50 correctly and 207 wrongly — which is what a second opinion looks like when the relation between the geometry and the label has been destroyed.
<!-- end generated -->

The matched-refusal column is the one that matters, and it separates the
configurations sharply. Where a guard gives up almost everything — the two
built on the code layer give up 495 and 497 of 516 answers — matched refusal
removes nearly as many wrong answers as the guard does, because refusing
almost everything removes almost everything. Where a guard gives up a
minority of the answers, the two come apart: at 150 answers given up the guard
removes 13 and the control removes 2.

The reshuffled-label control says the same thing from the other side. With the
relation between the geometry and the label destroyed, the metric reading
answers 50 of 576 correctly and 207 wrongly on the program operation, and
guarding with it costs 320 correct answers while removing the same wrongs by
sheer attrition. A second opinion has to be *about* the query to be worth
anything, and the control is what shows that this one is.

## 8. What is proved rather than measured

`RequestProject/GLM/SecondReading.lean`, 0 `sorry`, states the guard as a
function on `Option` answers and proves what it does:

* `strictGuard_eq_some` and `vetoGuard_eq_some` — exactly when each guard
  answers, and with what;
* `strictGuard_sound` and `vetoGuard_sound` — a guard's answer is always the
  primary's answer, so no guard invents one;
* `strictGuard_wrong_imp` and `vetoGuard_wrong_imp` — if a guard answers
  wrongly then the primary answered wrongly *and*, for `strict`, the second
  reading answered the same wrong label; for `veto`, the second reading did
  not contradict it;
* `strictGuard_safe_of_sound` and `vetoGuard_safe_of_sound` — if the second
  reading is *sound* on a query, in the sense that when it answers it answers
  the truth, the strict guard never answers wrongly there; the veto guard
  needs the second reading to *answer* as well, which is exactly what its
  weaker contract costs and is why every veto configuration fails M1 above;
* `strictGuard_correct_subset` and `vetoGuard_correct_subset` — the cost
  direction: every query a guard answers correctly is one the primary answered
  correctly, so a guard can only lose correct answers, never gain them;
* `strict_correctCount_le`, `veto_correctCount_le`, `strict_wrongCount_le` and
  `veto_wrongCount_le` — the same two directions carried to counts over a list
  of queries, which is what the table in §6 is: guarding moves both columns of
  the score sheet downwards, so safety has to be *paid for* and cannot be a
  free improvement;
* `strict_correctCount_le_veto` — the two guards are a chain and not two
  unrelated contracts, so the sweep over them is a sweep over one dial;
* `strict_blocks_unless_second_repeats` — the failure the round is about, as a
  statement: an answer survives the strict guard only if the second reading
  independently produced the same one.

Those are exactly the claims the measurement is allowed to lean on; everything
else here is a count on this sample.

Two things are deliberately **not** theorems, and the difference matters. That
the metric reading is sound on this sample is a measurement, not a property:
nothing proves that a carrier of another label cannot sit inside the margin.
And that the guard removes *all thirteen* wrong answers rather than some is a
fact about these 576 queries. What the theorems give is the shape of the
guarantee: a wrong answer now needs two readings at two layers to agree on it.

## 9. What this leaves for the next round

Three things, stated so they are not lost.

**The guard is adopted, and it is not free.** It answers 366 where the
unguarded reading answered 503, so 137 queries that used to get a correct
answer now get a refusal. That is the right trade for an operation that was
answering wrongly, and it is still a loss; what would improve it is a second
reading that refuses less, not a weaker guard, because the weaker guard was
measured here and does not reach safety.

**The metric reading's soundness is unexplained.** It answers nothing wrongly
on any of the six operations and is beaten by the primary on four of them.
A reading that is safe and weak, next to one that is strong and unsafe, is a
decomposition worth understanding rather than a curiosity — the obvious next
measurement is what the margin is *doing* on the queries the ladder gets
wrong, and whether a margin other than twice the nearest distance trades the
two off better.

**Nothing here is wired into the shipped query loop.** This is a measurement
of a contract, not a change of the dispatcher: the operations still answer as
they did, and adopting the guard in the shipped path is a separate step with
its own end-to-end evaluation.

## 10. Limits

The figures are about the same samples and the same four perturbations as the
previous round, and inherit its limits. Two more are specific to this one.
The `margin` reading computes an exact distance to every carrier, so it is
`O(n)` per query where the ladder's reading is a quantisation — it is a second
*reading*, not a second *index*, and nothing here claims it is cheap. And the
medians of the `code` reading are taken over the carriers, so a carrier set
that changes changes the reading; the measurement is recomputed from the
carriers each time rather than stored.

**How to re-run this.**

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools second-reading           # the stored measurement
PYTHONPATH=. python3 -m glm_universal.tools second-reading --write   # re-take it (about fifteen minutes)
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_second_reading.py -q
```
