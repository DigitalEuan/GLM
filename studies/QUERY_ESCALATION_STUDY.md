# Escalation as a step of the query loop

## Tier 0 — the coarse read

**Question.** The deep-hole rounds are the only place in this repository where
a refusal was answered by raising the resolution of the reading instead of
stopping. Can that be made a step of the ordinary query loop — with a declared
ladder, a stated cost, and a rule that stops it turning a principled refusal
into an answer — without moving any answer the runtime already gives?

**Verdict.** Yes, and at no cost to what the runtime already does: over the whole evaluation set no answer moves and no principled refusal is converted, while four of the declared probes are resolved above the first rung and two refusals become certified absences.

**Deciding figure.** Over 149 evaluation cases, 0 answers moved and 0 principled refusals were converted; of 18 declared probes, 4 resolve above the first rung.

**Recomputed by.** `glm_universal.reasoning.query_escalation.query_escalation_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0a. The reading in one paragraph

Yes, and at no cost to what the runtime already does: over the whole evaluation set no answer moves and no principled refusal is converted, while four of the declared probes are resolved above the first rung and two refusals become certified absences. Over 149 evaluation cases, 0 answers moved and 0 principled refusals were converted; of 18 declared probes, 4 resolve above the first rung.

The same reading, recomputed rather than written:

<!-- generated: queryesc-tier -->
**Both gates hold.**  Over the whole evaluation set of 149 cases, all 135 the runtime answers directly come back identical through the loop, at the first rung and for the first rung's cost — 0 answers moved and 0 principled refusals were converted into answers.  Of the 16 declared refusals, **14** are classified non-escalatable before the ladder is climbed.

The loop buys something: of the 18 declared probes, 8 are answered and 4 of those are reached *above* the first rung — 'nearest to k_B', 'describe energie', 'describe oxigen', 'nearest to velocty' — at a cost of 3, 5, 5, 5 against 1 for a direct answer.  2 refusals are certified absences within the declared radius of 2 edits.
<!-- end generated -->

---

## 0. What this document is

A **pre-registration**, committed before the measurement was taken, of a round
that is mostly architectural: the mathematics is already in
`RequestProject/GLM/Escalation.lean` and `RequestProject/GLM/Layers.lean`, and
what was missing was the plumbing and the discipline that keeps the plumbing
honest.

The deep-hole escalation round showed that a stalled reading can be resolved by
escalating the *layer* rather than the question, and it also showed what makes
such a move honest rather than a search for a favourable answer: the ladder is
declared before it is climbed, every rung tried is counted, and the original
refusal stays on the record beside whatever the escalated reading returns. This
round wires that into
`glm_universal.runtime.escalation_loop` and measures what it costs and buys.

---

## 1. The four commitments, fixed before the loop was written

1. **A refusal carries the layer it was refused at.** *Absent* becomes *absent
   at L1*; a claim that a question is unanswerable becomes *refused at the top
   of the declared tower*, which is stronger and much more falsifiable.
2. **The ladder is finite and fixed per query kind.** It is a table, not a
   thing built at run time from what the query looks like, so the loop
   terminates after at most as many rungs as the kind's ladder is high.
3. **An escalated answer is more expensive than a direct one, and says so.**
   Each rung carries a declared integer cost and the reported cost is the sum
   over the rungs actually run.
4. **Escalation may not convert a principled refusal into an answer.** A
   refusal that is correct at every layer — ill formed, underdetermined, or
   grounded in no register — is classified as such *before* the ladder is
   climbed, and the loop stops at the layer the refusal was made at. Without
   this the loop would grind up the ladder on every such question and *refused
   at the top of the tower* would stop meaning anything.

---

## 2. The tower

Three readings, declared in the module and nowhere else.

| rung | reading | cost | what it does |
|---|---|---|---|
| `L1` | the register reading | 1 | the query answered from the register its surface terms name — what `ask` does today |
| `L2` | the semantics reading | 2 | the operands resolved through the reference layer, and the query re-asked with what they denote |
| `L3` | the neighbourhood reading | 4 | the lookup, **named as one**: the unique alias within the declared radius answers, and an empty shortlist inside that radius is a certified absence |

The declared radius of `L3` is **two edits**, exact integer Levenshtein over an
enumerated index. It has to be stated for an empty shortlist to be an absence
rather than a failure to look far enough, and it has to be small for the rung
to be a reading of the question rather than a search for something to say. A
shortlist with more than one alias inside the radius **refuses**: a lookup that
picks between candidates is guessing.

`L3` is where this round meets the dictionary question. Nearest-neighbour
retrieval was never objectionable for being a lookup; it was objectionable for
carrying an unstated claim that the representation it indexes is adequate to
the question. Naming the layer makes that claim stated and checkable — and
where an index is enumerated rather than sampled, the empty shortlist is a
proof rather than a shrug.

---

## 3. The ladders

One per query kind, declared in `escalation_loop.LADDERS`, and reported in
full in §7.1. Two kinds of one-rung ladder are declared deliberately rather
than by omission:

* `meaning` — its answer *is* a reading of the semantics layer, so escalating
  it would be circular;
* `measure`, `comparative`, `derive`, `real`, `compare` — their refusals are
  decisions of a scale, a description or a process, and no rung of *this* tower
  reads those. A ladder that pretends otherwise would buy nothing and cost
  something.

A kind with no entry gets a one-rung ladder. An undeclared kind does not get an
undeclared ladder.

---

## 4. What counts as a principled refusal

A declared list of markers, each with the reason it is one, matched against the
refusal text: *ill-formed*, *underdetermined*, *ungrounded*. A refusal matching
none of them is read as an **absence**, which is the only kind of refusal a
finer reading can repair.

The failure direction matters and is stated here: a refusal whose wording
changes and no longer matches a marker is re-classified as an absence and gets
escalated. That fails towards **spending work**, not towards answering, and the
gate in §5 is what catches it if it ever fails the other way.

---

## 5. The gates, fixed before the measurement

**Gate 1 — safety.** Over the whole evaluation set:

* every case the runtime answers directly is answered identically through the
  loop, at the first rung, for the first rung's cost; and
* no case whose refusal is classified as principled is answered at any rung.

Nothing about this round is claimed if gate 1 fails.

**Gate 2 — utility.** At least one probe of the declared set of §6 resolves
*above* the first rung. A loop with no instance is machinery, not a faculty,
and would be reported as such.

**Reported, not gated.** The cost of an escalated answer against a direct one;
the number of refusals classified principled; the number of absences certified
within the declared radius.

---

## 6. The probe set

Eighteen queries, declared before the run and reported in full whatever each
does. The set deliberately includes probes expected to stay refused —
underdetermined, ungrounded, ill formed, ambiguous inside the radius — because
a probe set of things that work is not a measurement. The full list, with the
purpose of each, is `query_escalation.PROBES`.

---

## 7. The measurement

*Written by the measurement, not by hand: every table below is a generated
block emitted from a cache guarded by a digest of the modules that produced
it, so when a source moves the block says so and the corpus check fails.*

### 7.1 The tower and the ladders

<!-- generated: queryesc-ladders -->
| rung | reading | cost | what it reads |
|---|---|---|---|
| `L1` | the register reading | 1 | The query answered from the register its surface terms name. |
| `L2` | the semantics reading | 2 | The operands resolved through the reference layer, and the query re-asked with what they denote. |
| `L3` | the neighbourhood reading | 4 | A lookup, named as one: the unique alias within the declared radius answers, and an empty shortlist within it is a certified absence. |

| query kind | ladder | rungs | cost of climbing to the top |
|---|---|---|---|
| `analogy` | L1 -> L2 | 2 | 3 |
| `angle` | L1 -> L2 | 2 | 3 |
| `cluster` | L1 -> L2 | 2 | 3 |
| `coherence` | L1 -> L2 | 2 | 3 |
| `comparative` | L1 | 1 | 1 |
| `compare` | L1 | 1 | 1 |
| `derive` | L1 | 1 | 1 |
| `describe` | L1 -> L2 -> L3 | 3 | 7 |
| `meaning` | L1 | 1 | 1 |
| `measure` | L1 | 1 | 1 |
| `nearest` | L1 -> L2 -> L3 | 3 | 7 |
| `pi_groups` | L1 -> L2 | 2 | 3 |
| `product` | L1 | 1 | 1 |
| `project` | L1 -> L2 | 2 | 3 |
| `real` | L1 | 1 | 1 |
| `report` | L1 | 1 | 1 |
| `spatial` | L1 -> L2 -> L3 | 3 | 7 |
| `task` | L1 | 1 | 1 |
| `trilinear` | L1 | 1 | 1 |
| `unknown` | L1 | 1 | 1 |
| `verify` | L1 -> L2 | 2 | 3 |

10 of 21 declared kinds have a ladder taller than one rung, and the tallest is 3.  A one-rung ladder is a declaration that no rung of this tower reads that kind's refusals, not an omission.
<!-- end generated -->

### 7.2 Gate 1 — safety

<!-- generated: queryesc-safety -->
| check | reading |
|---|---|
| evaluation cases run both ways | 149 |
| answered by the direct path | 135 |
| answers that moved | 0 |
| answers that cost more than the first rung | 0 |
| principled refusals converted into answers | 0 |
| gate 1 | `True` |

A question the register answers is answered exactly as it was — same text, same rung, same cost — and the ladder is recorded in the payload beside the answer rather than written into it.
<!-- end generated -->

### 7.3 Gate 2 — the probes

<!-- generated: queryesc-probes -->
| probe | kind | ladder | outcome | rung | cost | classification |
|---|---|---|---|---|---|---|
| `describe energy` | describe | L1 -> L2 -> L3 | answered | L1 | 1 | — |
| `nearest to c` | nearest | L1 -> L2 -> L3 | answered | L1 | 1 | — |
| `nearest to k_B` | nearest | L1 -> L2 -> L3 | answered | L2 | 3 | — |
| `nearest to N_A` | nearest | L1 -> L2 -> L3 | answered | L1 | 1 | — |
| `describe energie` | describe | L1 -> L2 -> L3 | answered | L3 | 5 | — |
| `describe oxigen` | describe | L1 -> L2 -> L3 | answered | L3 | 5 | — |
| `nearest to velocty` | nearest | L1 -> L2 -> L3 | answered | L3 | 5 | — |
| `describe watter` | describe | L1 -> L2 -> L3 | refused | L3 | 1 | absent |
| `describe unobtainium` | describe | L1 -> L2 -> L3 | refused, absence certified | L3 | 1 | absent |
| `describe justice` | describe | L1 -> L2 -> L3 | refused, absence certified | L3 | 1 | absent |
| `report nonsense subject` | report | L1 | refused | L1 | 1 | absent |
| `Ca : Sc :: Ba : ?` | analogy | L1 -> L2 | refused | L1 | 1 | underdetermined |
| `heat : temperature :: acceleration : ?` | analogy | L1 -> L2 | refused | L1 | 1 | ungrounded |
| `please compute the square root of a banana` | unknown | L1 | refused | L1 | 1 | ill-formed |
| `is 0.1 + 0.2 equal to 0.3` | compare | L1 | answered | L1 | 1 | — |
| `measure large in room` | measure | L1 | refused | L1 | 1 | ungrounded |
| `derive cents of perfect_fifth` | derive | L1 | refused | L1 | 1 | ungrounded |
| `approximate 1/0 to 5 places` | real | L1 | refused | L1 | 1 | ill-formed |

Answered by rung: L1 4, L2 1, L3 3.  Gate 2 asks for at least one probe resolving above the first rung and there are 4: `True`.
<!-- end generated -->

### 7.4 The refusals, classified

<!-- generated: queryesc-classified -->
| case | kind | classification | escalated | outcome |
|---|---|---|---|---|
| analogy-empty-table-position | analogy | underdetermined | no | refused at L1 |
| analogy-conjugate-unplaced | analogy | ungrounded | no | refused at L1 |
| describe-unknown-word | describe | absent | yes | refused at L3 |
| trilinear-nonaxes | trilinear | ill-formed | no | refused at L1 |
| meaning-open-vocabulary | meaning | answered as a refusal in prose | no | answered |
| real-divide-by-zero | real | ill-formed | no | refused at L1 |
| compare-equality | compare | answered as a refusal in prose | no | answered |
| unknown-nonsense | unknown | ill-formed | no | refused at L1 |
| report-unknown-subject | report | absent | yes | refused at L1 |
| measure-large-room | measure | ungrounded | no | refused at L1 |
| measure-expensive-market | measure | ungrounded | no | refused at L1 |
| measure-hot-walking | measure | ungrounded | no | refused at L1 |
| comparative-cross-quantity | comparative | ungrounded | no | refused at L1 |
| comparative-wrong-scale-marker | comparative | ungrounded | no | refused at L1 |
| comparative-midpoint-word | comparative | ungrounded | no | refused at L1 |
| derive-undescribed-coordinate | derive | ungrounded | no | refused at L1 |

14 of 16 declared refusals are non-escalatable, decided by 14 declared markers before any rung above the first is run.  The 2 that were climbed — describe-unknown-word, report-unknown-subject — are absences, and the ladder returned a refusal at the top of the tower for each of them, which is a stronger statement than the refusal at the first rung was.
<!-- end generated -->

### 7.5 What the round establishes

<!-- generated: queryesc-establishes -->
**Escalation is a step of the loop and costs nothing where it is not needed.**  All 135 directly answered evaluation cases come back identical, at the first rung, for the first rung's cost.

**A refusal now carries its layer.**  Every refusal reports the rung it was made at and whether the ladder was climbed; 2 of the probes return an absence certified within 2 edits of an enumerated index, which is a refusal that knows its own radius rather than a shrug.

**The rule against converting a principled refusal holds, and it bites.**  14 of the 16 declared refusals are non-escalatable and are never climbed; none of them is answered at any rung.

**The loop has instances rather than only machinery.**  4 declared probes resolve above the first rung: one by resolving a constant through the reference layer, the rest by a lookup that names its layer.  Each is reported as more expensive than a direct answer, which is the point of charging for rungs.
<!-- end generated -->

---

## 8. The Lean half: what is proved rather than measured

`RequestProject/GLM/EscalationLoop.lean`:

1. **Termination.** `climb` over a finite ladder inspects each declared rung at
   most once, so its cost never exceeds the ladder's own total
   (`climb_total`).
2. **Least, not merely some.** Where it answers at a rung, no earlier rung of
   the ladder answers — so *answered at L3* really does mean *L1 and L2 were
   asked and refused*.
3. **Cost is monotone and honest.** The cost of a climb that stops at a rung is
   the sum of the costs up to it, so an escalated answer is never cheaper than
   a direct one (`climbFrom_cost_ge`), and a direct answer costs exactly the
   first rung (`climb_direct_cost`).
4. **A non-escalatable refusal is preserved.** If a refusal is classified
   non-escalatable, the loop's verdict is a refusal at the layer it was
   classified at, whatever the rest of the ladder would have said.

---

## 9. What this study does not do

* It does **not** change what `ask` does. The loop is
  `ask_escalated`/`escalate`, and the direct path is untouched, which is what
  makes gate 1 checkable at all.
* It does **not** claim the tower is complete. Three rungs, and the kinds whose
  refusals none of them read are declared as one-rung ladders rather than
  escalated for the look of it.
* It does **not** treat a certified absence as an answer. An absence certified
  within two edits is a refusal that knows its own radius.
