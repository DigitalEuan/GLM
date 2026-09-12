# Cumulativity as a shipping condition — a layer arrives with its check

## Tier 0 — the coarse read

**Question.** The information-loss round found a real design flaw by asking
whether a layer refines the one below it, and the flaw was reported rather than
quietly patched. Can that question be turned from an inspection anyone might
run into a condition every layer family has to satisfy before it ships — and
does the rule, once written down, keep a cumulativity failure distinct from a
conflation, whose remedy is different?

**Verdict.** Yes on both counts. Three declared layer families are checked here, seven refinement edges hold on their probe sets, two declared non-edges are witnessed, no shipped family carries a defect, and the conflations each rung inflicts are reported beside the edges as resolutions rather than as defects.

**Deciding figure.** 3 declared families, 2 of them shipped; 7 refinement edges checked and 2 declared non-edges witnessed; 0 defects.

**Recomputed by.** `glm_universal.reasoning.cumulativity.cumulativity_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0a. The reading in one paragraph

Yes on both counts. Three declared layer families are checked here, seven refinement edges hold on their probe sets, two declared non-edges are witnessed, no shipped family carries a defect, and the conflations each rung inflicts are reported beside the edges as resolutions rather than as defects. That is 3 declared families, 2 of them shipped; 7 refinement edges checked and 2 declared non-edges witnessed; 0 defects.

The same reading, recomputed rather than written:

<!-- generated: cumul-tier -->
**The rule holds, and it is checked rather than intended.**  3 declared layer families, 2 of them shipped; 7 declared refinement edges are verified on their probe sets and 2 declared non-edges are witnessed.  0 shipped family carries a defect.  Separately, and not as a defect, the check reports 32 conflated pairs across the rungs: a conflation is what a rung cannot see, and the remedy for it is a joint reading rather than a refinement.
<!-- end generated -->

---

## 0. What this document is

The rule, and the check that enforces it. Everything measured here is measured
by `glm_universal.reasoning.cumulativity`, which is cheap enough to run on
every test pass, so the tables below are recomputed rather than stored.

It is a follow-on from [`INFORMATION_LOSS_STUDY.md`](INFORMATION_LOSS_STUDY.md),
which asked what each perspective layer throws away and found, at scale, one
step in the shipped layer code that was not a refinement of the step below it.
That finding is the argument for making the check a condition: it caught a
genuine design flaw the first time it was run over the whole stack, and a check
that has already found something is not a formality.

---

## 1. The rule

> **A layer family ships only if every declared refinement edge holds on its
> probe set, and every declared non-edge has a witness.**

Three things in that sentence are doing work.

**Declared.** A family names its edges — which rung is supposed to refine which
— *before* the check is run. A check that inferred the edges from the data
could not fail, because whatever relation happened to hold would be the one
reported.

**Holds on its probe set.** The check is a measurement over a declared list of
carriers, not an intention in a docstring. Two carriers that a lower rung
separates must be separated by the higher rung; if some pair is not, the pair
is the defect and it is named.

**Witnessed.** A *non-*edge is also a claim, and it is the more interesting
one: to say that rung B does **not** refine rung A is to say a specific pair
exists that A separates and B does not. The check demands that pair. A declared
non-edge with no witness is a defect exactly as a declared edge with a
violation is: in both cases the family says something about itself that is not
true.

---

## 2. Why refinement is the right property

A reading is a function from carriers to whatever the rung can see. Refinement
of the reading below is precisely the condition under which everything the
lower rung distinguishes remains distinguishable above it — equivalently, under
which the lower reading is a function of the higher one. When it fails, an
operation defined at the lower rung ceases to be a function of what the higher
rung sees, and the tower stops being a tower: an answer computed above cannot
be pushed down to a statement below.

This is not an aesthetic preference. It is what makes an escalation ladder
meaningful at all. If L₂ does not refine L₁, then "escalate to L₂ and read
again" can *lose* the very distinction that motivated the climb, and the least
rung that resolves a query is no longer well defined.

The Lean counterpart is `RequestProject/GLM/CumulativityRule.lean`, where
`GLM.CumulativityRule.RefinementChain` is the chain condition,
`GLM.CumulativityRule.refines_of_le` is its transitive closure — a rung refines
every rung below it, not merely its immediate predecessor — and
`GLM.CumulativityRule.refinementChain_cumulativeTower` connects the chain to
the tower the runtime declares.

---

## 3. What a conflation is, and why it is not a defect

A rung conflates a pair when it maps two carriers the study cares about to the
same reading. Every rung below the finest one conflates something; that is what
being a coarse reading *is*. The check reports conflations, and reports them
separately, because a rule that treated them as defects would be a rule against
having layers.

The two failure modes are different objects and have different remedies:

| | what it is | remedy |
|---|---|---|
| **cumulativity failure** | a higher rung loses a distinction the rung below it made | a constraint on how the higher rung is *constructed*: fix the construction, or do not ship it |
| **conflation** | a rung cannot see some distinction at all | a **joint** reading with a rung that can; refining this rung does not repair it |

The `A_1^24` / `A_2^12` case from the deep-hole rounds is the second and not
the first. The exact rational reading conflates that pair because neither type
emits a stray, so under that reading the two are one atom; there is no finer
version of the same reading that separates them, and the separation comes from
*joining* the rational reading with the share reading. Cumulativity prevents a
new layer from re-inflicting a loss; it does not repair a loss that is
intrinsic to what a rung looks at.

`GLM.CumulativityRule.factored_conflates` and
`GLM.CumulativityRule.join_separates` are these two sentences as theorems, and
`GLM.CumulativityRule.join_needs_a_second_reading` is the statement that the
join is doing the work — a reading joined with itself separates nothing new.

---

## 4. The declared families

<!-- generated: cumul-families -->
| family | ships | rungs | edges | non-edges | verdict |
|---|---|---|---|---|---|
| `dimension-stack` | yes | substrate -> integer -> rational -> griess -> universal | 4 | 0 | passes |
| `dimension-stack-rejected` | no | substrate -> integer_raw | 0 | 1 | passes |
| `deep-hole-ladder` | yes | shares -> widened -> rational -> joint | 3 | 1 | passes |

* `dimension-stack` — the five-layer perspective stack the runtime reads carriers at.  The step that had to be repaired is the first one: the shipped integer layer carries the substrate's bits alongside the exponents precisely because reading the exponents alone does not refine the substrate.
* `dimension-stack-rejected` — the rejected integer reading, kept so its cost stays priced.  This family is registered with no edges and one declared non-edge: the reading is not cumulative over the substrate, the check finds the witness, and the family does not ship.  It is the defect the first run of this check caught, kept on the record rather than deleted.
* `deep-hole-ladder` — the four readings of the deep-hole escalation ladder.  The ladder is a graph and not a chain, and this is where the two failure modes part company: L3 is not above L1, because a reading of distances alone cannot see which vertex a start arrived at.  The declared non-edge carries the witness for that -- two records with the same distance measure and different arrival shares -- and it is the same phenomenon that makes L3 conflate A_1^24 with A_2^12 in the measured round.  The remedy there is the join L4, not a refinement of L3.
<!-- end generated -->

The second of these is the point of the exercise. `dimension-stack-rejected` is
a family with **no** edges and one declared non-edge: the raw integer reading
of the substrate is registered as *not* refining the substrate, the check finds
the witnessing pair, and the family does not ship. It is the defect the first
run of this check caught, kept on the record and priced, rather than deleted
once it had been fixed. The shipped `dimension-stack` carries the substrate's
bits alongside the exponents precisely because of it.

---

## 5. Edge by edge

<!-- generated: cumul-edges -->
| family | edge | pairs checked | refines | metric dominates |
|---|---|---|---|---|
| `dimension-stack` | `substrate` → `integer` | 21 | True | — |
| `dimension-stack` | `integer` → `rational` | 21 | True | — |
| `dimension-stack` | `rational` → `griess` | 21 | True | — |
| `dimension-stack` | `griess` → `universal` | 21 | True | — |
| `deep-hole-ladder` | `shares` → `widened` | 10 | True | True |
| `deep-hole-ladder` | `widened` → `joint` | 10 | True | True |
| `deep-hole-ladder` | `rational` → `joint` | 10 | True | True |

| family | declared non-edge | witnessed | witness |
|---|---|---|---|
| `dimension-stack-rejected` | `substrate` → `integer_raw` | True | the vacuum / a unit on coordinate 10 |
| `deep-hole-ladder` | `shares` → `rational` | True | shares 2:1, no stray / shares 1:1:1, no stray |
<!-- end generated -->

Where the two rungs' readings carry comparable metrics, the check also asks
whether the higher metric dominates the lower — a quantitative strengthening of
refinement, and the property the deep-hole ladder's rungs were built to have.
Where the metrics are not comparable the column is left blank rather than
filled with a number that would mean nothing.

---

## 6. What each rung cannot see

<!-- generated: cumul-conflations -->
| family | rung | pairs conflated |
|---|---|---|
| `dimension-stack` | `substrate` | 10 |
| `dimension-stack` | `integer` | 2 |
| `dimension-stack` | `rational` | 0 |
| `dimension-stack` | `griess` | 0 |
| `dimension-stack` | `universal` | 0 |
| `dimension-stack-rejected` | `substrate` | 10 |
| `dimension-stack-rejected` | `integer_raw` | 4 |
| `deep-hole-ladder` | `shares` | 2 |
| `deep-hole-ladder` | `widened` | 0 |
| `deep-hole-ladder` | `rational` | 4 |
| `deep-hole-ladder` | `joint` | 0 |

A layer family ships only if every declared refinement edge holds on its probe set and every declared non-edge has a witness.  A conflation is reported beside these and is not a defect: it is the rung's resolution, and the remedy is a joint reading rather than a refinement.
<!-- end generated -->

---

## 7. What this study does not do

* It does **not** claim the probe sets are exhaustive. A refinement edge that
  holds on seven probes is not a theorem; it is a check that would have caught
  the one real violation this project has found, and it is run on every test
  pass. The theorem-shaped statements are in the Lean file, over arbitrary
  carriers.
* It does **not** repair any conflation. Conflations are reported; joining is a
  separate act, and where the project performs one it does so explicitly.
* It does **not** cover every layer in the repository — only the families
  registered in the module. Registering a family is how a layer opts into the
  rule, and a layer that has not opted in is visible as absent from the table
  above rather than as silently passing.

---

## 8. How to re-take every number

```
python3 -m glm_universal.tools cumulativity          # the check, as a report
python3 -m pytest glm_universal/tests/test_cumulativity.py
```

Integers and exact readings throughout; no float is constructed and no random
source is consulted. The check is fast enough that it is not cached: every
table above is recomputed when the corpus is rendered.
