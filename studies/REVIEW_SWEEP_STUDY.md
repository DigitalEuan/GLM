# The review sweep — which stalled results are worth re-reading, decided first

## Tier 0 — the coarse read

**Question.** Directive D13 lets a stalled result be re-read at a finer layer,
and then constrains the practice: rank candidates by whether there is an
**identifiable discarded quantity** at the coarse reading, not by how
disappointing the original result was. Nothing implemented that clause. Can the
whole standing set of stalled results be ranked by it, *before* the next
re-reading, and does the ranking then say anything a list sorted by
disappointment would not?

**Verdict.** Yes, and it changes the order. Eight stalled results are registered; one names a quantity the reading discarded and is licensed for a re-reading, two have already been recovered that way, one is a statement no reading settles, and four discarded nothing — so escalation is not licensed for them and each names what is needed instead.

**Deciding figure.** 8 stalled results registered; 1 licensed for a re-reading, 2 already recovered, 1 needing a theorem, 4 with nothing discarded; 0 entry defects.

**Recomputed by.** `glm_universal.reasoning.review_sweep.review_sweep_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0a. The reading in one paragraph

Yes, and it changes the order. Eight stalled results are registered; one names a quantity the reading discarded and is licensed for a re-reading, two have already been recovered that way, one is a statement no reading settles, and four discarded nothing — so escalation is not licensed for them and each names what is needed instead. That is 8 stalled results registered; 1 licensed for a re-reading, 2 already recovered, 1 needing a theorem, 4 with nothing discarded; 0 entry defects.

The same reading, recomputed rather than written:

<!-- generated: review-tier -->
**The register is written before the next re-reading, and it sorts by what the coarse reading threw away.**  8 stalled results: 1 recoverable, 2 recovered, 1 needs-a-theorem, 4 no-discard.  A re-reading is licensed for `retrieval-hit-at-5`, and 0 entries carry a defect.
<!-- end generated -->

---

## 0. What this document is

The register directive D13 asks for, and the module that keeps it:
`glm_universal.reasoning.review_sweep`. It is cheap enough to run on every test
pass, so every table below is recomputed rather than stored.

It exists because the escalation rule has a quiet failure mode of its own. D13
stops a re-reading from being *unbounded* — the ladder is declared, every cell
is counted, the original negative stays on the record — but a project can obey
all of that and still spend every round re-reading whichever negative annoyed
it most. The clause that stops *that* is the second practice item: re-read what
threw something away. This register is that clause applied to the standing set,
written down before the next round chooses.

---

## 1. The rule

> **A stalled result is ranked for re-reading by whether a quantity
> identifiable at the coarse reading was discarded — not by how disappointing
> the result was. Where nothing was discarded, escalation has nothing to
> recover.**

Two things in that sentence do the work.

**Identifiable.** Not "there might be more signal somewhere", which is true of
every measurement ever taken, but a named quantity, at the reading that was
actually used, with somewhere it is or would be reported. The register requires
each entry claiming a discard to point at a module attribute, and an entry that
cannot is reported as **unsupported** and ranked *below* an entry that honestly
names nothing. An unsupported claim of a discarded quantity is exactly the move
this clause exists to stop.

**At the coarse reading.** A quantity that the experiment never produced —
because no walk reached that type, because no case of that shape is in the
evaluation set — is not discarded. It is absent, and no rung recovers it. Those
entries are the ones the register is most useful for, because they are the ones
where the temptation to climb is strongest and the climb is guaranteed to be
wasted.

---

## 2. The four classes

| class | what it means | what it licenses |
|---|---|---|
| `recoverable` | a quantity was discarded at the coarse reading, and the register can point at where it is reported | a declared re-reading: a ladder, costed, with the original negative kept |
| `recovered` | the same, and the re-reading has been taken | nothing further; kept as evidence that the rule works |
| `needs-a-theorem` | the stall is a statement no resolution settles | a proof |
| `no-discard` | nothing identifiable was discarded: the stall is in the signal | **not** a re-reading; the entry names what is needed instead |

The order of that table is the order the register sorts in, and the sort is
computed from the class and the support check rather than written by hand.

---

## 3. The register

<!-- generated: review-register -->
| rank | entry | class | read at | discarded quantity |
|---|---|---|---|---|
| 1 | `retrieval-hit-at-5` | recoverable | the 24-count feature map, quantised to a Leech point | the identity of the terms.  The feature map reduces a declaration to twenty four structural counts, and two declarations with the same counts and disjoint vocabularies are one address -- which is exactly what the text control keeps and what the lexical address recovers part of (66.7 %) |
| 2 | `deep-hole-per-type` | recovered | the same single cell, read type by type instead of globally | the per-type spreads, which the global maximum discards by construction.  Recovered by reporting the criterion type by type: three of the ten types satisfy it, and `GLM.DeepHoleFailure.per_type_correct` makes that a certificate for those types |
| 3 | `rational-conflation` | recovered | L3, the exact measure of distances, read alone | the arrival shares -- which vertex each start arrived at. Recovered by the join rather than by refining L3, which is the declared non-edge of the deep-hole family and, in general form, `GLM.Info.Layer.factored_conflates` with `join_separates` |
| 4 | `faithfulness-radius` | needs-a-theorem | the joint rung at 1920 starts | nothing at the reading.  The two radii are measured from the same table, and the shortfall is a fact about the table rather than about what the reading kept |
| 5 | `deep-hole-separation` | no-discard | the joint rung at 1920 starts -- the top of the declared ladder | nothing identifiable.  The joint rung already carries both the stray spectrum and the exact measure, and the failure round located the stall in the within-type spread of D_6^4 (W = 0.0659 against B = 0.0358), which is a property of the ensemble rather than of what the reading throws away.  The declared 55-subset deletion sweep gets no lower than 1.4784, and a deletion cannot certify the types it deleted |
| 6 | `describable-coverage` | no-discard | the three declared shape families | nothing.  The thirteen remaining query kinds are not shapes of any family; forcing them would make the coverage figure meaningless, which is the language layer's own stopping rule |
| 7 | `niemeier-unreached-types` | no-discard | the declared centre set of the first deep-hole round | nothing.  A type no walk arrives at is absent from the record at every rung: there is no quantity in the measurement for a finer reading to recover |
| 8 | `planner-utility` | no-discard | the whole evaluation set under the declared fallback rule | nothing.  Every question in the evaluation set that the runtime refuses is a question that ought to be refused, so the set contains no headroom for the planner; the five gains on the declared task set are all off-set |
<!-- end generated -->

---

## 4. What each entry needs

Reading the third column is the point of the exercise: five of the eight
entries need something that is not a finer reading, and saying so is what stops
the next round from climbing a ladder that cannot reach.

<!-- generated: review-next -->
| entry | stall | what it needs |
|---|---|---|
| `retrieval-hit-at-5` | retrieval by lattice address reaches hit@5 39.1 % against 6.3 % chance, and the plain text control reaches 85.0 % on the same 207 queries | a declared joint reading of the lattice address with a term reading, priced as a rung and measured on the same 207 queries against both controls |
| `deep-hole-per-type` | the global criterion is a worst case over ten types, so it says nothing about a type that is well separated from its own neighbours | done, and labelled in the study as added after the numbers were seen |
| `rational-conflation` | read alone, the exact rational rung conflates A_1^24 with A_2^12: neither hole emits a stray, so the whole measure is one atom | the reading is repaired; what is still wanted is the characterisation -- which pairs *any* stray-blind reading must conflate -- and that is a theorem, not a rung |
| `faithfulness-radius` | faithfulness and the certified radius are incompatible: a query needs a radius of 0.0659 where separation permits only 0.0179, so `absent_certifies` cannot be instantiated | either the per-type certificate extended to more types, or a proof that no reading of this family separates the table by more than its within-type spread |
| `deep-hole-separation` | the separation criterion rho = 2W/B < 1 is unmet: rho falls from 3.90 to 2.5943 across the declared ladder and never crosses 1, so the reading that names 40 of 44 holes still certifies no absence | not a re-reading.  Either a bound proved for every reading of this family, or a different ensemble -- which is new data and a new pre-registration, not a rung |
| `describable-coverage` | three of the eight registers are described, and seven of the twenty answerable query kinds | a fourth shape family would be new work with its own pre-registration; the measured verdict is that the layer has reached where it should stop |
| `niemeier-unreached-types` | the ensemble reaches 10 of the 23 Niemeier root systems from the 14 declared centres; 13 are reported as unreached and nothing is claimed about them | new centres, and therefore a new pre-registration: the centre set is part of what the first study fixed |
| `planner-utility` | the reverse-call planner's utility gate is false: of the four refusals the fallback rule offers it, it correctly refuses all four, so it would add nothing to the shipped system | evaluation cases of the shapes the planner answers and the runtime does not -- new cases, declared before they are run, not a finer reading of the present ones |
<!-- end generated -->

---

## 5. What the ranking changed

Sorted by disappointment, the top of this list would be the **separation
criterion**: the sharpest open question in the repository, a ratio of 2.5943
against a criterion of 1, and the one thing standing between a classifier that
names 40 of 44 holes and a classifier that can certify an absence. It is also
the entry with nothing to recover. The joint rung already carries both the
stray spectrum and the exact measure; the failure round located the stall in
the within-type spread of one type, `D_6^4`, which is a property of the
ensemble and not of what the reading throws away; and the declared 55-subset
deletion sweep gets no lower than 1.4784, with
`GLM.DeepHoleFailure.resolves_of_subset` explaining why a deletion could never
have certified the types it deleted. A round spent climbing there would have
been a round spent well only by accident.

What the rule puts first instead is **retrieval by lattice address**, which is
not the most disappointing result in the project — it beats chance by 6.2× —
but is the one whose coarse reading demonstrably discards something nameable:
the identity of the terms. The feature map takes a declaration to twenty four
structural counts, so two declarations with the same counts and disjoint
vocabularies are one address. That is not a suspicion; it is what the two
controls already measure. The text control keeps exactly what the map discards
and reaches 85.0 % against the address's 39.1 %, and the lexical address, which
keeps part of it, reaches 66.7 %. A declared joint reading of the two is a
ladder with something to climb for.

The two `recovered` entries are kept because they are the register's own
evidence. The rational reading's `A_1^24` / `A_2^12` conflation named a
discarded quantity — which vertex each start arrived at — and was repaired by a
join rather than by a refinement, which is now
`GLM.Info.Layer.factored_conflates` with `join_separates`. The global
separation criterion discards the per-type spreads by taking a maximum, and
reading it type by type recovered three certified types out of ten. Both are
cases where the rule pointed at something and the something was there.

---

## 6. What this study does not do

* It does **not** claim the classes are right. Which class an entry is in is a
  judgement, declared here and open to being wrong; what is measured is that
  the document exists and is not a stub, that a claimed discarded quantity has
  somewhere it is reported, and that the order follows the rule.
* It does **not** re-read anything. The register is written before the next
  re-reading, which is the only time it can constrain one, and no entry here
  has been escalated on the strength of it.
* It does **not** close any entry. A `no-discard` verdict is not a verdict that
  the question is uninteresting — three of the four name new data or a new
  pre-registration as the way in.
* It is **not** a substitute for the open list. `STATUS.md` §3 says what is
  open; this register says which of it a finer reading could possibly help.

---

## 7. How to re-take every number

```
python3 -m glm_universal.tools review                 # the register, ranked
PYTHONPATH=. python3 GLM.py -q "report review sweep"
python3 -m pytest glm_universal/tests/test_review_sweep.py
```

Integers and strings only: the register counts entries and reads the tree. No
float, no random source and no digest, so nothing above is cached and every
table is recomputed when the corpus is rendered.

**Parent:** [`../ENTRY.md`](../ENTRY.md) · **Directive:**
[`../PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md) D13
