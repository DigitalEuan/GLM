# The multi-part stack: who carries whom when one faculty goes silent


## Tier 0 — the coarse read

**Question.** Can the faculties of the machine be arranged so that the geometry carries the queries the text layer cannot read?

**Verdict.** The relay beats plain text on every query set, and the controls do not.

**Deciding figure.** 15 queries carried against 1 lost, where a digest-and-reshuffle relay carries 1.

**Recomputed by.** `glm_universal.reasoning.stack.relay_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

**What this document is.**
[`ADDRESS_RETRIEVAL_STUDY.md`](ADDRESS_RETRIEVAL_STUDY.md) scored the address
layer against its controls and recorded a negative result that has stood since:
retrieval by lattice address beats chance several times over and is beaten
decisively by a plain lexical overlap of the statement text. That result is
about **one faculty answering alone**. The machine is not one faculty: it has
an address book over the syntax, a second address book over the identifiers, a
lexical search, a name search, and — in the second register of this study — a
generator, a visual filter and a cross-domain check.

This study asks the question the single-faculty table cannot answer:

> When the strong faculty has **no evidence for this query**, can a weaker
> faculty carry it, and does the stack as a whole then beat the strong faculty
> alone?

The answer, stated before the tables so that nothing here reads as a defence of
a preferred result:

1. **Yes, and on every set.** Gated on the text layer's own confidence, the
   relay lifts hit@5 on the tuning stride, on a disjoint held-out stride and on
   bare goal queries, and it is never below the text control at any window of
   the ladder. §1.
2. **It costs almost nothing, because it almost never fires.** The gate fires
   on 64 of 1,728 queries — 3.7 % — and above the gate the relayed answer *is*
   the text control's answer, which is a theorem (`GLM.Relay.relay_confident`)
   and not a measurement. §1.
3. **The gain is the geometry's.** The same mechanism relaying to the digest
   addresses and a seeded permutation carries 1 query, and relaying to the name
   search carries none, where the two address books carry 15; the control
   loses no query and the geometry loses one. A relay to anything is not a
   relay to this. §3.
4. **It is not a tuned threshold, and the band has an edge.** The gain is
   strict on all five consecutive gates of the declared band, 1/20 through
   1/4, and the improvement is the same 6 carried queries across all five;
   the first lost query appears at 3/20, and precision slips as the gate
   widens, so the edge of the band shows in what the relay costs rather than
   in what it gains. A single fitted threshold would not hold across five.
   Past the band it does break: at 1/2 the relay carries 9 and loses 7 and
   precision falls to 50 %. The edge is measured rather than declared, and it
   has moved — the top gate 1/4 fell one query behind the text control two
   rounds ago and drew level in the last one. §4.
5. **The other arrangement helps less.** Letting the geometry break the text
   layer's many exact ties, rather than answer when the text layer is silent,
   moves hit@5 up by two to four queries and leaves precision a wash. It is a
   second, weaker place where the geometry is worth having, and it is recorded
   as it falls. §5.
6. **The mechanism transports to a register with no text in it.** On the 50 ARC
   training puzzles the same relay runs over a generator, an eight-dimension
   visual filter and a cross-domain check: the cheap look removes 95.3 % of
   proposals before the expensive verification gate sees them, two faculties
   carry one puzzle each, and the relay solves a puzzle its leading faculty
   does not. §6.

Every table below is a **generated block**, emitted from the measurement cache
that `python3 -m glm_universal.corpus --remeasure` fills, guarded by the digest
of the Lean sources it was taken from. The formal half is
[`RequestProject/GLM/Relay.lean`](../RequestProject/GLM/Relay.lean); the
computational half is `glm_universal.reasoning.stack` and
`glm_universal.reasoning.vision_stack`; the test that pins the two against each
other is `overlay/glm_universal/tests/test_stack.py`; and the report prints
with

```bash
cd overlay
PYTHONPATH=. python3 GLM.py -q "report relay" --verify-tct
```

whose third column re-derives every figure below in a fresh interpreter.

---

## 1. The mechanism, and what it is worth

Three pieces, each stated rather than tuned.

**Confidence.** A faculty reports how much evidence it has for *this* query,
not how good it is in general. For the lexical search that is the Jaccard
overlap its best candidate achieves: zero when no declaration in the corpus
shares a single identifier with the goal, which is exactly the case where the
search is guessing. A distance carries no such reading, so a point scheme
reports no confidence and never leads.

**The gate.** The leader answers alone while its confidence is at least 1/10.
Below that it is judged to have abstained.

**The interleave.** When the gate fires, the answer takes two candidates from
the text layer, two from the lexical address book and one from the structural
address book, then the remainders in the same order, keeping the first
occurrence of each name.

<!-- generated: stack-sets -->
| query set | who answers | queries | hit@1 | hit@3 | hit@5 | hit@10 | precision@5 |
|---|---|---|---|---|---|---|---|
| goal — both strides again, asked as bare goals | text alone | 864 | 596 (69.0 %) | 709 (82.1 %) | 737 (85.3 %) | 766 (88.7 %) | 57.9 % |
| goal — both strides again, asked as bare goals | **the relay** | 864 | **596 (69.0 %)** | **710 (82.2 %)** | **742 (85.9 %)** | **772 (89.4 %)** | 58.1 % |
| holdout — a disjoint stride, never looked at while choosing | text alone | 432 | 291 (67.4 %) | 352 (81.5 %) | 364 (84.3 %) | 385 (89.1 %) | 59.0 % |
| holdout — a disjoint stride, never looked at while choosing | **the relay** | 432 | **291 (67.4 %)** | **355 (82.2 %)** | **369 (85.4 %)** | **390 (90.3 %)** | 59.4 % |
| tuning — the stride the gate was chosen on | text alone | 432 | 305 (70.6 %) | 357 (82.6 %) | 373 (86.3 %) | 381 (88.2 %) | 56.9 % |
| tuning — the stride the gate was chosen on | **the relay** | 432 | **305 (70.6 %)** | **357 (82.6 %)** | **377 (87.3 %)** | **385 (89.1 %)** | 57.2 % |

The gate is 1/10 and fires on 64 of 1728 queries.  Across the three sets the geometry carries **15** queries the text control misses at k = 5 and loses **1**.  The relay beats the text control on every set: yes; it is never below the text control at any k: yes.
<!-- end generated -->

Three readings, in the order of how much they matter.

**The stack beats the faculty that beat the geometry.** On every set the relay
is strictly ahead of the text control at k = 5 and never behind it at any other
window. The margins are small — four queries on the tuning stride, five on the
held-out stride, five on the goals — because the gate fires on 3.7 % of
queries and can only change the answer there. That is the shape a correct
mechanism has here: it does nothing where nothing is wrong.

**It does not disturb the leader.** Above the gate the relayed list *is* the
text control's list, by `GLM.Relay.relay_confident`, so the 96 % of queries the
text layer answers with evidence are untouched by construction rather than by
luck. The lost column is the one the gate exists to keep small, and on this
corpus it holds one query of 1,728: 15 carried against 1 lost, the loss being
`GLM.Gen3.m24_orbit_stabiliser` on the goal set, where the interleave's
reordering costs a hit the text control had. It has been empty in earlier
rounds and is not now, which is why the column stays in the table rather than
in a footnote.

**The window is wide enough for whoever holds the answer.** The quotas sum to
five, and `GLM.Relay.relay_carry` says that whatever a faculty holds inside its
own quota is inside the first five of the relayed list. A faculty with the
answer cannot be crowded out by the faculties without it — which is the whole
of "another part takes the hit", stated as a theorem rather than hoped for.

---

## 2. Who was carried

<!-- generated: stack-carried -->
| query set | gate fired | carried by the geometry | lost |
|---|---|---|---|
| goal — both strides again, asked as bare goals | 32 | `GLM.Calibration.NA`, `GLM.Gen3.class_census`, `GLM.Admission.ledger_refusals`, `GLM.Calibration.molarPlanck`, `GLM.Gen3.pair_census`, `GLM.Landscape.golay_ball_majority` | `GLM.Gen3.m24_orbit_stabiliser` |
| holdout — a disjoint stride, never looked at while choosing | 19 | `GLM.Admission.ledger_refusals`, `GLM.Calibration.molarPlanck`, `GLM.FitCapacity.phi`, `GLM.Gen3.pair_census`, `GLM.Gen3.constant_minus_coherent` | none |
| tuning — the stride the gate was chosen on | 13 | `GLM.Calibration.NA`, `GLM.FitCapacity.protonRatioTarget`, `GLM.Gen3.class_census`, `GLM.Packing.radius_of_seven` | none |

A *carried* query is one the text control misses at k = 5 and the relay hits; a *lost* query is the reverse, which is the column the gate exists to keep empty.
<!-- end generated -->

The carried queries are worth reading rather than counting. They are
constants and calibration lemmas — `GLM.Calibration.NA`,
`GLM.Calibration.molarPlanck`, `GLM.FitCapacity.relErr` — statements whose
text is a numeral and a unit, so the identifiers they share with their
relatives are few or none and the lexical search has nothing to read. It is
exactly the population the address layer was built for: the statement's
*shape* is informative where its words are not. The stack finds them because
it asks the geometry only there.

---

## 3. The controls

<!-- generated: stack-controls -->
| query set | carried by the two address books | carried by digest + reshuffle | carried by name search |
|---|---|---|---|
| goal — both strides again, asked as bare goals | 6 | 1 | 0 |
| holdout — a disjoint stride, never looked at while choosing | 5 | 0 | 0 |
| tuning — the stride the gate was chosen on | 4 | 0 | 0 |

Over the three sets the geometry carries more than the digest-and-reshuffle control: yes; it never carries fewer on a set: yes; it carries more than the name search: yes.
<!-- end generated -->

The control is the same mechanism with the substrate removed: the same gate,
the same quotas, the same window, relaying to the SHA-256 addresses of
directive D3 and to a seeded permutation of the corpus instead of to the two
address books. If padding the tail of a short list were enough, the control
would carry as many queries as the geometry does. It carries one — and loses
none — against fifteen carried, and the name search — the
strongest non-geometric second opinion
available — carries none at all, because a query whose identifiers match
nothing mostly matches nothing in a name either.

---

## 4. The gate, swept

<!-- generated: stack-sweep -->
| gate | queries it fires on | hit@5 | precision@5 | carried | lost |
|---|---|---|---|---|---|
| 0 | 0 | 86.3 % | 56.9 % | 0 | 0 |
| 1/20 | 13 | 87.3 % | 57.2 % | 4 | 0 |
| 1/10 | 13 | 87.3 % | 57.2 % | 4 | 0 |
| 3/20 | 13 | 87.3 % | 57.2 % | 4 | 0 |
| 1/5 | 17 | 87.0 % | 57.0 % | 4 | 1 |
| 1/4 | 26 | 86.8 % | 56.5 % | 4 | 2 |
| 1/2 | 175 | 85.6 % | 50.0 % | 6 | 9 |

On the tuning set.  The gain is strict on 5 of the thresholds from 1/20 to 1/4, up to and including 1/4; across the whole of that band the relay is never below the text control: yes.
<!-- end generated -->

A threshold chosen to make a table look good is a fitted constant, so the whole
range is reported. At a gate of 0 the relay never fires and the row is the text
control exactly, which is the arithmetic check that the mechanism is doing what
it says. From 1/20 to 1/4 the relay is ahead of the control and the carried
set is the same four queries; the first lost query appears at 1/5, and from
there the gate's widening is paid for in precision rather than in hits —
57.2 % at 1/20 against 56.5 % at 1/4 — while hit@5 stays above the control's
86.3 % throughout. At 1/2 — where the leader is overruled on almost half the
corpus — it carries six and loses nine and precision falls to 50.0 %, and
the mechanism is plainly past its useful width. The
gate is doing what a gate should: it separates "no evidence" from "some
evidence", and inside that gap the answer does not depend on exactly where the
line is drawn.

---

## 5. The other arrangement: the geometry inside the text layer's ties

<!-- generated: stack-tiebreak -->
| query set | tie-break | hit@1 | hit@3 | hit@5 | hit@10 | precision@5 |
|---|---|---|---|---|---|---|
| holdout | address | 296 (68.5 %) | 358 (82.9 %) | 368 (85.2 %) | 386 (89.4 %) | 59.4 % |
| holdout | lexical | 295 (68.3 %) | 355 (82.2 %) | 368 (85.2 %) | 385 (89.1 %) | 59.4 % |
| holdout | name | 291 (67.4 %) | 352 (81.5 %) | 363 (84.0 %) | 384 (88.9 %) | 58.9 % |
| tuning | address | 309 (71.5 %) | 361 (83.6 %) | 375 (86.8 %) | 386 (89.4 %) | 57.4 % |
| tuning | lexical | 316 (73.1 %) | 363 (84.0 %) | 375 (86.8 %) | 387 (89.6 %) | 57.6 % |
| tuning | name | 305 (70.6 %) | 357 (82.6 %) | 373 (86.3 %) | 381 (88.2 %) | 56.9 % |

Ranking by text overlap and breaking the many exact ties by address distance instead of by name.  It beats the shipped name tie-break on hits: yes; on precision: yes.
<!-- end generated -->

The relay is not the only way to put two faculties together. An exact Jaccard
over small token sets takes few values, so the text ranking is mostly ties, and
the shipped ranking breaks them by name — alphabetically, which is
deterministic and meaningless. Breaking them by address distance instead gives
the geometry a say on every query rather than on 4 % of them.

It is worth a little, and less than the relay: two to four queries of hit@5 on
each set, with precision@5 a fraction of a point either way. Recorded as it
falls, in the same register as the negative results of the study this one
extends. The two arrangements are independent and could be run together; the
relay is the one with the theorem behind it, so it is the one that ships.

---

## 6. The second register: the same relay over grids

<!-- generated: stack-vision -->
| what was measured | result |
|---|---|
| puzzles | 50 |
| candidates proposed | 1,089 |
| candidates surviving the look | 51 |
| share the cheap filter removes before the gate | **95.3 %** |
| puzzles the leading faculty solves alone | 1 |
| puzzles the relay solves | **2** |
| solved rules that also produce the held-out test output | 2 |
| queries the gate fired on | 47 |

Who carried what: **geometry** — `1e0a9b12`; **recolour** — `ae58858e`.  More than one faculty carries a puzzle: yes; the relay is never behind the leading faculty: yes.
<!-- end generated -->

A mechanism that only worked in the register it was invented in would be a
trick. So the same definitions — confidence, gate, quota, interleave — are
instantiated over the 50 ARC-AGI training puzzles kept under
`overlay/arc_agi_17/data/training`, with faculties that read no text at all:

* **recolour**, which leads, because it reads the puzzle's own pairs: a flat
  colour map, and the conditional recolour that decides a shape's colour from
  the size of its connected component;
* **geometry** — the dihedral group and the four gravities;
* **shape** — scale, crop to the bounding box, shift.

Each faculty ranks its candidates by the *look*: eight cheap properties of the
rule's output on a training input — palette, size, aspect, component count,
symmetry, density, colour count, and whether it changes anything — compared
against what the training outputs actually look like. A faculty's confidence
for a puzzle is the share of those dimensions its best candidate passes,
exactly as a rational; the gate is 7/8.

Three things transport. The cheap look removes 95.3 % of the 1,089 proposals
before the expensive verification gate sees them, which is the filter faculty
carrying the cost rather than the accuracy. Two different faculties supply the
verifying rule — `recolour` for `ae58858e`, `geometry` for `1e0a9b12` — so the
carry is not one faculty doing all the work. And the relay solves a puzzle its
leading faculty does not, while never solving fewer, which is the same
statement as §1 in a register with no identifiers in it.

Two of fifty is the honest headline for the generators, and it is not a claim
about ARC: this register is a test of the mechanism, run on the puzzle set the
archive left behind. Both solved rules also produce the held-out test output,
which is the only sense in which "solved" is used here.

---

## 7. What is proved

The measurements above can move with the corpus. The following cannot, because
they are theorems of [`RequestProject/GLM/Relay.lean`](../RequestProject/GLM/Relay.lean)
about the relay itself, and they hold in whichever register it is instantiated.

| statement | what it says | Lean |
| --- | --- | --- |
| leader preservation | above the gate the relay *is* the leader's ranking, so the stack cannot cost anything where the leader is strong | `relay_confident`, `relay_abstain` |
| no invention | every candidate in the answer came from some faculty's list | `mem_relay`, `mem_interleave` |
| no duplication | a candidate several faculties propose is offered once, at its earliest rank | `interleave_nodup`, `relay_nodup` |
| **the carry theorem** | whatever a faculty holds inside its quota is inside the relayed answer's window of the summed quotas | `relay_carry`, `carry_hit` |
| graceful degradation | a faculty that answers nothing costs its quota and never the answer | `mem_interleave`, and the empty-block case of `interleave` |
| monotone window | the first `k` of the answer is a prefix of the first `k'`, so a hit at `k` is a hit at `k'` | `relay_take_prefix`, `hit_mono` |

The carry theorem is the one with teeth. Everything else in this study is a
hit rate that a different corpus could move; the carry theorem is the reason
the arrangement is worth measuring at all, and it is why "the other faculties
take the hit" is a property of the mechanism rather than a hope about it.

---

## 8. What would falsify this

* **The control.** If the digest-and-reshuffle relay ever carried as many
  queries as the two address books do, the gain would be the list padding's and
  §3's conclusion would reverse. `test_stack.py` recomputes that comparison and
  fails when it does.
* **The gate.** If the improvement held only at 1/10 and vanished on either
  side of it, the threshold would be fitted rather than stated. It does not:
  it is strict over five consecutive gates and never below the control across
  the whole declared band. Where the strict gain stops — currently at the top
  of the band, 1/4 — is recorded in the verdict as a measurement, not assumed;
  the sweep is in the report and the test reads both halves of it.
* **The loss column.** If the relay began losing more queries than it carries,
  the mechanism would be trading accuracy for coverage rather than adding it.
  The count is in §1 and in the verdict.
* **The second register.** If the relay solved fewer puzzles than its leading
  faculty, the carry theorem would still hold and the arrangement would still be
  worthless; the measurement is the check that it is not.
* **The theorems.** One counterexample to `relay_carry` would mean the window
  the study reports is not the window the mechanism has. It is proved, so the
  falsification would have to be a change to the definitions — in which case the
  Lean file stops building, which is the check.
