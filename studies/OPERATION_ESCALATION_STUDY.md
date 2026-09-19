# Escalating something other than retrieval — six operations, their controls, and the one that is not safe

## Tier 0 — the coarse read

**Question.** The construction ladder improves geometric addressing: given a perturbed carrier it names the carrier. Does the same escalation discipline improve any *other* faculty — meaning, dimensional reasoning, the chemistry and physics registers, small-integer structure, program text, and equation checking — or is addressing the only thing it buys?

**Verdict.** All seven operations gain from escalation over their best single rung, and one of them loses the refusal contract while doing it: the program-text operation answers 503 of 576 queries correctly and 13 wrongly, which is a failure and is reported as one.

**Deciding figure.** Seven operations measured; every one beats its best single rung and its substrate-removed control; one — program text — answers 13 of 576 queries wrongly.

**Recomputed by.** `glm_universal.reasoning.operation_escalation.measure`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. What this document is

[`NORM_FAMILY_STUDY.md`](NORM_FAMILY_STUDY.md) measures one operation very
carefully — *which carrier is this?* — and shows that escalating the reading
over a family of rungs answers more of them than any single rung. That is
addressing, and addressing is one faculty. This document takes the same
discipline to six others and records what each one gains, including where the
answer is *nothing* and where the answer is *worse than nothing*.

Each operation is declared with four things: the question it is asked, what a
rung is supposed to give it that the rung below does not, a refusal contract,
and controls with the substrate removed. Every figure below is emitted by the
code that measures it.

## 1. The protocol

**The ladder.** One ladder for all of them, so that a difference between two
operations is a difference in the operation and not in the reading: the
norm-indexed family of [`NORM_FAMILY_STUDY.md`](NORM_FAMILY_STUDY.md) §2, twelve
rungs, coarsest first, one at every power-of-two minimum norm from 2,048 down
to 1.

**The queries.** The same deterministic perturbations as every other escalation
measurement here: 8 coordinates by `1/8`, `1/4`, `1/2` and `3/4`, with the
support and the signs read off Golay codeword `i mod 4096`. No random source is
imported anywhere.

**The refusal contract.** One contract, shared: *answer only when the rung's
cell is non-empty and every carrier in it carries the same label; otherwise
refuse and try the next rung.* This is deliberately weaker than retrieval's
contract, which needs the cell to hold exactly **one** carrier — and the
difference is the point. A rung that cannot say *which* carrier a query is may
still say what *kind* it is, and that is what an operation other than retrieval
needs.

**The controls.** Two, and they answer different questions.

* *Substrate removed.* The cells are decided by a digest of the exact query
  rather than by a lattice, with the cell count matched to the rung's. Anything
  the reading scores above this is the geometry doing work.
* *The label prior.* Always answer the most common label, never refuse. This is
  what an operation could score with no reading at all, and for a
  classification with few labels it is a high bar.

An oracle allowed to pick the resolving rung after the fact is reported beside
them.

## 2. The operations, and what a rung is supposed to add

| operation | the question | what a rung adds |
|---|---|---|
| `register` | which of the six registers is this carrier from? | a register is a coarse property, so a coarse rung should answer it where a fine rung has already lost the address |
| `dimension` | what are the seven SI exponents of this physics quantity? | the answer is a seven-integer vector, so the prior is nearly useless and a rung has to separate the query from everything of another dimension |
| `chemistry` | which block of the periodic table is this element in? | elements of one block are near each other, so a rung that conflates two elements of one block can still answer the block |
| `physics` | which sub-domain of physics is this quantity from? | a sub-domain is coarser than an identity, so it should survive a perturbation that destroys the address |
| `harmony` | what is the prime limit of this interval? | the answer is nearly a projection of one coordinate, which tests whether escalation helps where the geometry is barely needed |
| `program` | which file of the Lean development is this declaration from? | declarations of one file share structure but not coordinates, so the label is only loosely carried by the geometry |
| `equation` | does `dim(a) = dim(b) + dim(c)` hold, read from three perturbed carriers? | every operand must be read before the arithmetic can start, so the check gains three times over from a rung that reads what the one below cannot |

## 3. What was measured

<!-- generated: opesc-operations -->
| operation | queries | correct | wrong | refused | best single rung | label-prior control | substrate-removed control | gain over the best rung |
|---|---|---|---|---|---|---|---|---|
| `register` | 568 | 541 | 0 | 27 | `4A` at 415 | 96 | 43 | +126 |
| `dimension` | 96 | 80 | 0 | 16 | `Z` at 48 | 32 | 10 | +32 |
| `chemistry` | 96 | 96 | 0 | 0 | `8A` at 94 | 24 | 2 | +2 |
| `physics` | 96 | 82 | 0 | 14 | `Z` at 48 | 24 | 7 | +34 |
| `harmony` | 96 | 95 | 0 | 1 | `4A` at 80 | 40 | 19 | +15 |
| `program` | 576 | 503 | 13 | 60 | `2D` at 344 | 232 | 54 | +159 |
| `equation` | 192 | 136 | 0 | 56 | `Z` at 96 | 96 | 12 | +40 |

The refusal contract is the same for all of them: answer only when the rung's cell is non-empty and every carrier in it carries the same label; otherwise refuse and try the next rung. A query the whole ladder refuses is refused, never guessed.

Operations helped by escalation: `register`, `dimension`, `chemistry`, `physics`, `harmony`, `program`, `equation`.  No operation gained nothing.  Operations that lose the refusal property: `program` — reported as a failure, not a footnote.
<!-- end generated -->

Four readings of that table.

**Escalation helps every operation, and by very different amounts.** The
register question gains most in absolute terms; the chemistry question gains
almost nothing, because its best single rung already answers 94 of 96 — the
operation is saturated before the ladder is applied, and the honest way to say
that is that escalation has nothing left to buy there rather than that it
works particularly well.

**The substrate is doing the work, and the controls say so.** Removing it does
not merely lower the score; it makes the operation *unsafe*. The digest control
answers a large fraction of its queries wrongly on every operation, because a
digest cell that happens to be occupied says nothing about the query that
landed in it. The reading's refusals and the control's wrong answers are the
same queries.

**The label prior is the bar that matters for a classification.** An operation
with six labels can score 96 of 568 by always saying the most common one. Every
operation here is far above its prior, and the two operations whose answer
space is large — `dimension`, with sixteen distinct exponent vectors in the
sample, and `physics`, with fourteen sub-domains — are the ones where the prior
is weakest and the reading is carrying the whole result.

**One operation loses the refusal contract.** The program-text operation
answers 13 of 576 queries wrongly. Its label — the file a declaration is
written in — is not a property of the coordinates at all: the feature vector
holds quantifier counts, statement length, citations and namespace depth, and
nothing that says which file the declaration is in. So a cell can be unanimous
and unanimously wrong, and the unanimity contract is not enough to catch it.
That is a real failure of the contract for this operation, not a footnote, and
what it shows is that the contract's strength depends on whether the label is
carried by the geometry — which is exactly what the operation was built to
test.

## 4. Equation checking — the one that derives

<!-- generated: opesc-equation -->
**equation checking: does dim(a) = dim(b) + dim(c)?**  given three perturbed physics carriers and the claim dim(a) = dim(b) + dim(c), decide whether it holds.

The case set is 48 declared triples — 24 that hold and 24 that do not — each asked at the four declared perturbations, so 192 queries.  every operand must land in a cell carrying a single exponent vector; if any one does not, the whole check is refused

| reading | correct | wrong | refused |
|---|---|---|---|
| escalation over the ladder | 136 | 0 | 56 |
| best single rung (`Z`) | 96 | 0 | 96 |
| answer the majority class, never refuse | 96 | 96 | 0 |
| substrate removed (digest cells) | 12 | 12 | 168 |

The seven integer additions and the comparison are done by this module over the vectors the reading recovered; the register is consulted only to score the answer.  The prior control is the sharp one here: the classes are balanced, so guessing scores 96 of 192 and the escalation's 136 is +40 on it.
<!-- end generated -->

This is the only operation in the round that is not a lookup of any kind. The
register is consulted to *score* the answer and never to produce it: the
system reads three perturbed carriers, recovers three exponent vectors from
the cells they land in, and then does seven integer additions and a comparison
itself. A claim it answers correctly is a claim no table holds.

Its refusal rate is the highest of any operation, and for a structural reason
worth stating: the contract is applied three times, once per operand, so the
check refuses whenever *any* of the three is ambiguous. That is the price of
composing a derivation out of readings, and it is why the escalation's gain
over the best single rung is larger here than for a one-operand operation.

## 5. Limits

The figures are about these samples — the first 24 named objects of each
register, 144 Lean declarations, 48 declared equations — and these four
perturbations. Every operation's label comes from the register that also
supplies the carrier, so a mislabelled register entry would be scored as a
correct answer; what is measured is consistency with the register, not with the
world. The program-text operation's failure is a failure of the contract on
this label, and says nothing about whether a different label over the same
vectors would be safe.

**How to re-run this.**

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools operations           # the stored measurement
PYTHONPATH=. python3 -m glm_universal.tools operations --write   # re-take it (about ten minutes)
PYTHONPATH=. python3 -m pytest glm_universal/tests/test_operation_escalation.py -q
```
