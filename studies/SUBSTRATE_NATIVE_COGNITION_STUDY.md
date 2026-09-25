# Substrate-native cognition: the supplied list, as experiments

## Tier 0 — the coarse read

**Question.** Which concepts of the supplied substrate-native-cognition list move derivation, addressing or refusal when they are run, and which do not?

**Verdict.** Round two wired three more frames into the typed planner, which is now the default path: interval consistency, rational recognition and dimensional derivation answered 26 of 33 declared questions and refused the other 7 as declared, with 0 wrong where the grammar answered none.

**Deciding figure.** 26 of 33 declared round-two questions answered correctly and 7 refused correctly, with 0 wrong, against 0 answered by the grammar alone.

**Recomputed by.** `glm_universal.reasoning.substrate_cognition.cognition_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

`source_material/substrate_native_cognitive_1.txt` lists things to try in
order to push the GLM towards a *substrate-native cognitive* architecture:
that is, getting the 24-dimensional substrate to **derive** answers, not only
route or store them. The list has three parts: a refine/consolidate/grow
section, eight engineering items, and nine "generative" concepts. This study
turns every item into one line of a ToDo/Experiment list (§1). For each item
it says what already exists in the tree, what this round did with it, and
what the item would have to measure to earn a later round.

The standing target is unchanged
([`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md), *The target*): an item
moves the target only if the system derives, addresses or refuses better
than before, measured against a control that was declared before the
measurement. §2 holds the declarations. They were committed before the
measuring module existed.

## 1. The list, one line per concept

*The status column was filled in after the measurement, and updated after round two (§7). "Met" and "not met"
refer to the pass mark declared in §2. "Wired" means a question put to the
machine can reach it.*

**Summary.** Round two wired three more frames into the typed planner, which is now the default path: interval consistency, rational recognition and dimensional derivation answered 26 of 33 declared questions and refused the other 7 as declared, with 0 wrong where the grammar answered none. In the first round five of the nine experiments met the pass mark declared before they ran, four did not, and only the certificate frame was wired: it moved derivation, answering 13 of 16 declared questions with a checkable certificate and 0 wrong where the grammar answered none.

| # | concept, in one line | already in the tree | this round | status |
|---|---|---|---|---|
| **Refine** | | | | |
| R1 | Make the typed planner the default reasoning loop | `runtime/semantic_plan.py`, opt-in (`GLM.py --plan`); candidate A of `STATUS.md` §3.4 | Y8: the 177 contract cases give the same outcomes through the planner as through the grammar (149 correct, 28 refused as expected), so the planner now reads first; `GLM.py --grammar` asks the grammar alone | **done (round two)** |
| R2 | Exact homographic (Möbius) arithmetic beside the delta-sigma loop | exact reals as processes (`reasoning/exact_real.py`); convergents as the engine's second fuel | X8: a streaming Möbius transform on continued fractions, checked against the exact-real layer | **built, met, not wired** |
| **Consolidate** | | | | |
| C1 | The five-layer stack as adjoint functors | the refinement chain and its losslessness theorems (`LayerChain.lean`, `Cumulative.lean`) | Y7: layer refinement is proved equivalent to factoring (`refines_iff_factors`), the kernel of the paired projection is the meet (`ker_pair_eq_inf`), and image ⊣ preimage is a Galois connection (`map_comap_gc`) | **first step proved** — the functors between the layers' categories remain |
| C2 | Infinite structures as coinductive types | exact reals and q-series are already lazy functions of the precision asked for | Y6: the delta-sigma stream as a `Stream'` (`dsStream`), with its ones-count and period proved | **done (round two)** |
| **Grow** | | | | |
| G1 | A small language model as semantic parser, with Three Column Thinking as the veto | the veto half exists: the planner answers only when every licensed reading agrees (`SemanticPlan.lean`) | declined permanently at the owner's instruction: the GLM learns from what language models do and translates the method into its own terms (the typed planner, the certificate frames); it does not embed one | **declined permanently** |
| G2 | Embed `Λ₂₄` in the Lorentzian lattice `II₂₅,₁` | the Leech lattice and its Niemeier neighbours | X9: the Weyl vector is null, proved | **first step proved; no dynamics claimed** |
| **Engineering items** | | | | |
| E1 | Rational intervals, and a refusal contract when they overlap | exact point values only | X6, then Y1: consistency with a quoted value and with the declared standard, and an ordering guard, all reached by a question | **built, met, wired (round two)** |
| E2 | Call the runtime a partial Norton–Sakuma 2A axial algebra, not the Griess algebra | the 2A Sakuma product (`Sakuma.lean`); "Griess metric" and "Griess layer" wording in the READMEs and the papers | the sweep is done in prose: every directive-cited document that said "Griess algebra" of the runtime now says the partial Norton–Sakuma 2A axial algebra on axes; identifiers such as `glmGriessLayer` keep their names | **done in prose (round two)** |
| E3 | Nested holdouts for the chemistry completion estimates | `reasoning/element_completion.py` | Y5: nested holdouts over the nine admitted completion rules; seven survive selection, two do not | **measured (round two)** — the two that fail are candidates for demotion |
| E4 | Semantic judgements as annotated provenance | a `Phrasing` cannot be built without the sentence that justifies it | not taken | **ToDo** — add annotator, date, alternatives and adjudication rule, and keep disputed readings |
| E5 | Derive what no register holds: Bézout, factorisation, finite search with impossibility certificates, dimensional equations | gcd and lcm (planner); dimensional derivation inside one formula wheel (Phase 59) | X7: Bézout, linear Diophantine equations and bounded factorisation, each with a certificate, reached through the planner | **built, met, wired — moved derivation** |
| E6 | A controlled language generated from a domain specification | the planner accepts only when one typed value survives | not taken | **ToDo** — generate the frames from a declaration instead of writing them by hand |
| E7 | Deepen the PCGS proofs: radix-2 NTT, sparse stencil, transducer prefix property | `PCGS.lean`, `reasoning/pcgs.py` | not taken | **ToDo** |
| E8 | Engine: prove impossibility first, use the lattice only for a certificate | the engine's snap and escalation | X4: an orbit certificate against exhaustive search in a toy gate space | **built, met, not wired** |
| **The nine generative concepts** | | | | |
| 1 | Invert the engine: TAX as a loss to minimise | `TAX = d²/32` in `reasoning/engine.py` | X3, then Y4: descent inside the coset of the word read | **refuted as stated; refined** — the constrained version is exactly the complete decoder (Y4) |
| 2 | Reversible inference trees that backtrack with no residue | Toffoli and Fredkin proved involutive (`Reversible.lean`) | X4 | **met** for exact undo; the path record is the price (§3.4) |
| 3 | Couple the infinite anchors to predict the mass residual | the wobble landscape was pre-registered and found not distinctive | not taken | **declined** — no mechanism was proposed that could be run without fitting |
| 4 | Drive generation through Three Column Thinking, mathematics first | the TCT engine as a verifier | Y3: dimensional equations solved exactly, with a certificate for each of unique, impossible and undetermined | **partly done (round two)** — generation by dimensional analysis is wired; a general enumerator of candidate equations is not |
| 5 | Branch at the deep hole: six hypotheses instead of a refusal | the complete decoder refuses at coset weight 4 | X1 | **met, not wired** — the second independent reading is still open |
| 6 | Climb the non-associative Griess tower when a derivation stalls | the 2A Sakuma product on axes | not taken | **ToDo** — E2 is done in prose, but the runtime still holds the product on axes, not the algebra, so there is no trilinear object to climb to |
| 7 | Wobble-signature matching as analogy | wobble signatures and their laws (`reasoning/wobble.py`) | X5, then Y2: rational recognition from a window, with a uniqueness certificate | **refuted as stated; refined into rational recognition, wired (round two)** |
| 8 | Abstraction by sliding down the dyadic tower | the tower's refinement theorems (`Tower.lean`) | X2 | **not met for one tower; two offset towers repair it** (theorem) |
| 9 | Vacuum-seeking inference | the coherence TAX, zero exactly at the zero vector (`GLM.tax_eq_zero_iff`) | X3, then Y4 | **refuted as stated; refined** — vacuum seeking inside a coset is decoding (Y4) |

## 2. Declarations — written before any measuring code

Each experiment below states its probe set, its control, its pass mark and
the faculty it would move. Every probe set is deterministic: no random
source, no seed, exact integers and `Fraction` only (D7).

**X1 — the deep-hole fork (concept 5).** *Probe set:* 64 codewords taken at a
fixed stride through the 4,096 Golay codewords. For each codeword, 12
weight-4 errors taken at a fixed stride through `C(24, 4)`, giving every
unordered pair of distinct errors for that codeword (66 pairs × 64 = 4,224
double reads). *What is run:* the complete decoder on each read alone (it
refuses: six equidistant candidates); then the **fork**: keep all six
candidates of each read, and intersect the two forks. *Controls:* the
retired first-in-scan-order snap on the first read, and the chance rate of
picking one of the six at random (1/6). *Pass mark:* 0 wrong answers,
required. The fork counts as having moved addressing if it answers at least
half of the double reads. *Declared structural checks:* in all 1,771
weight-4 cosets, the six leaders are pairwise disjoint and cover all 24
coordinates, so they form a sextet; and the true codeword lies in every fork.

**X2 — dyadic abstraction (concept 8).** *Probe set:* the Farey fractions of
order 16 strictly inside `(0, 1)`. *Quantity:* the conflation level of a
pair, i.e. the deepest level `n` at which `floor(x 2^n) = floor(y 2^n)`, with
−1 when they differ already at level 0. *The claim under test:* the shared
coarse window is a parent category, so nearer concepts should share a
deeper parent. *Measured:* the number of pairs that lie within `2^-n / 3` of
each other and still fail to share a level-`n` cell, for `n = 0..6`, in one
tower and in two towers (the second offset by `1/3`). *Pass mark:* one
tower is distance-faithful only if that count is 0. *Prediction, stated
now:* the count is not 0 for one tower and is 0 for two towers, because of a
theorem to be proved (`two_towers` below).

**X3 — TAX as a loss (concepts 1 and 9).** The tree has two quantities that
are both called TAX. The engine's is `d(v, Λ)² / 32`, the squared distance to
the nearest Leech point. The coherence module's is `HW(v)·Y + ‖v‖²/8`. *The
claim under test:* minimising TAX generates derivations. *Measured:* for
each TAX, what exact descent from a declared set of starts converges to,
compared with what the existing snap (for the engine's TAX) or the zero
vector (for the coherence TAX) already gives. *Pass mark:* the concept is
generative only if the minimiser carries information about the start beyond
its nearest-point decode (engine TAX), or beyond nothing at all (coherence
TAX). *Prediction:* neither does, for reasons that are theorems: the engine's
TAX is invariant under every lattice translation, and the coherence TAX has
the zero vector as its unique zero.

**X4 — reversible backtracking and impossibility first (concept 2 and the
"exact heuristics" item).** *Search space:* 24-bit states. A move is a
Toffoli or a Fredkin gate on one of the eight fixed coordinate triples of
`reasoning/reversible.py` (16 moves). *Probe set:* 32 (source, target)
pairs built at a fixed stride. *Run:* depth-first search to depth 4 that
backtracks by re-applying the gate it came through, with no state snapshot
stored; and an invariant certificate (the orbit of each triple under the
group the two gates generate), checked before any search. *Measured:*
whether every backtrack restores the state exactly, the memory each search
holds, how many nodes the search expands, and whether the certificate
agrees with exhaustive search. *Pass mark:* 0 disagreements between
certificate and search, and 0 restorations that are not exact.

**X5 — wobble-signature analogy (concept 7).** *Probe set:* the targets of
`reasoning/wobble.signature_targets`. *Control:* for each target `t`, a decoy
`floor(t · 2^40) / 2^40`, which is a dyadic rational with no structure.
*Measured:* how many targets share every column of their signature (ones,
transitions, longest runs, mean run length) with their decoy over the
shipped stream length. *Pass mark:* signature matching carries structure
beyond magnitude only if most decoys are separated. *Prediction:* none is
separated.

**X6 — rational intervals and the refusal contract (engineering item 1).**
*Probe set:* a declared table of standard atomic weights, transcribed from the
IUPAC/CIAAW table as intervals (either the interval notation or value ±
uncertainty), set against the element register. The register's own
precision is read from its decimal string, so `55.84` means
`[55.835, 55.845]`. *Measured:* (a) how many register values a point
comparison calls different from the standard value; (b) how many the interval
comparison calls inconsistent, how many consistent, and how many compatible
only at the register's stated precision; (c) on the declared ordering
questions, how many interval comparisons are refused because the intervals
overlap. *Pass mark:* the interval layer is worth shipping if it turns at
least one point-comparison "wrong" into a stated-precision verdict without
introducing a wrong ordering.

**X7 — absent derivations with certificates (engineering item 5).** A new
planner frame for linear Diophantine equations in two unknowns, Bézout
coefficients and factorisation within a stated bound. Every answer carries a
certificate that can be checked independently, and every "no" carries an
impossibility certificate. *Probe set:* the 16 questions in
`evaluation/certificates_heldout.py`, committed before the frame.
*Pass mark:* 0 wrong answers, and every declared refusal refused.

**X8 — homographic (Möbius) arithmetic beside the delta-sigma loop
(refine item 2).** A streaming Möbius transform on continued-fraction terms
that emits an output term only when every value still possible agrees on
it. *Measured:* the output of the transform checked against the exact-real
layer; and the precision in bits after 64 steps of the continued-fraction
fuel and after 64 steps of the delta-sigma loop, for `phi`, `sqrt 2`, `e` and
`pi`. *Pass mark:* the transform's output agrees with the exact-real value at
every emitted convergent.

**X9 — the Lorentzian lattice `II_{25,1}` (grow item 2).** *Measured:* one
concrete first step: the Weyl vector `(0, 1, …, 24 | 70)` is a null vector,
proved in Lean. *What is not claimed:* that a time-like direction supplies
any dynamics.

*A note on the record.* The ordering questions of X6(c) were not listed when
§2 was committed. They were fixed as "every consecutive pair of the standard
table" before `interval_experiment` first ran. Two predictions in §2 were
wrong, and they are left as written: X5 predicted that no decoy would be
separated, and one was (§3.5); X1 declared a fork pass mark of one half and
measured every pair (§3.1).

## 3. What each experiment measured

Every figure below is recomputed by `python3 -m glm_universal.tools cognition`
(`--json` for all of it). The theorems are in
`RequestProject/GLM/SubstrateCognition.lean`. All of them build with no
`sorry` and depend only on the standard axioms.

### 3.1 X1 — the deep-hole fork (concept 5): met, not wired

All 1,771 weight-4 cosets have six leaders that are pairwise disjoint and
cover the 24 coordinates, so every deep-hole ambiguity is a sextet. On the
768 single reads (64 codewords × 12 weight-4 errors), the complete decoder
refuses all 768. The true codeword is in the six-way fork of every one of
them. The retired first-in-scan-order snap is right on 154 of them and wrong
on 614, near the chance rate of 1/6.

Intersecting the forks of two reads of the same codeword answered all 4,224
double reads, correctly, with 0 wrong. That is the declared pass mark and
more: the declaration asked for half. `GLM.SubstrateCognition.fork_answer_correct`
is why a wrong answer is impossible. The truth lies in every fork, so a
one-point intersection *is* the truth. The refusal case exists and is
exhibited: two tetrads that split one octad leave both forks holding the
codeword and the codeword plus that octad. The intersection then has 2
points, and the fork refuses.

*What it does not claim.* The gain needs a **second independent reading** of
the same word. That is a repetition code on top of the Golay code, and it is
available only where the system has two views of one carrier. No runtime path
supplies one yet. Under D15 this is a candidate for **addressing**, not a
faculty moved.

### 3.2 X2 — dyadic abstraction (concept 8): not met; the repair is proved

Over the 79 Farey fractions of order 16, the single tower misses 204 near
pairs across levels 0–6: pairs closer than `2^-n / 3` that still share no
level-`n` cell. At level 1 alone it misses 80 of 960. So "coarsen until two
concepts conflate" is not a similarity: two concepts either side of a dyadic
boundary never conflate, however close they are
(`GLM.SubstrateCognition.one_tower_not_faithful`). The supplied example,
`1/7` against `4/27`, conflates down to level 7 of the dyadic tower. The
figure "separate at tick 27" in the supplied text belongs to the delta-sigma
stream (`GLM_Complete_Number_Theory_Evidence.md` §8), not to the tower.

The repair is a second tower offset by `1/3`. With both towers the miss count
is 0, and `GLM.SubstrateCognition.two_towers_level` proves it always is:
points closer than `1 / (3 · 2^n)` share a level-`n` cell in one of the two.
An abstraction built on the pair of towers is distance-faithful. One built
on a single tower is not. This is the one constructive thing concept 8
yields. It is not wired to anything, and it would be a change to the digit
stack, not an addition.

### 3.3 X3 — TAX as a loss, and vacuum seeking (concepts 1 and 9): not met

The engine's TAX was checked on 9 lattice translates of 3 declared points,
and all 9 have the same TAX as their point. It is zero on the lattice points
tried. `GLM.SubstrateCognition.infDist_translate` proves the invariance for
any subgroup, and `GLM.SubstrateCognition.periodic_argmin_translate` proves
the consequence. Minimising a lattice-periodic loss cannot prefer one lattice
point to another, so "accept the derivation that minimises TAX" returns
whichever lattice point is nearest, and the snap already computes that.

The coherence TAX `HW·Y + ‖v‖²/8` has the zero vector as its unique zero
(`GLM.tax_eq_zero_iff`). Exact greedy descent took all 6 declared starts to
the zero vector, in 8 to 144 steps. Vacuum seeking reaches the vacuum by
forgetting both concepts. The bridge the concept asks for would have to be a
constraint that stops the descent short of zero, and the concept does not
supply one.

### 3.4 X4 — reversible backtracking and impossibility first (concept 2, item E8): met, not wired

The search space is 24-bit states, with 16 moves (Toffoli or Fredkin on one
of 8 triples) and depth 4. Across 32 declared pairs, the search expanded
1,193,001 nodes. Every backtrack re-applied the gate it came through, and
every one restored the state exactly: 1,192,995 undos, 0 not exact. The
search holds the path (4 bits a move) and one state, which is 40 bits at
depth 4, where a snapshot search holds 120.

The orbit certificate, computed by breadth-first search over the 8 values of
one triple, agreed with the exhaustive search on all 32 pairs. It gives the
exact least depth where the target is reachable, and an obstruction where it
is not. It proved 16 targets unreachable at a cost of 8 table reads each.
The search had to exhaust 16⁰ + 16¹ + ⋯ + 16⁴ nodes to fail on each of them.
`GLM.SubstrateCognition.applyWord_control` is the obstruction: no word of the
two gates changes the control bit.

*What it does not claim.* Undo is exact because the gates are involutions,
but the search is not "zero-entropy". The path it keeps is the history that
makes the undo possible. Keeping it costs memory, and erasing it is where
Landauer's bound applies. That is the ordinary accounting for reversible
computation, not a loophole in it. The gate space is a toy. The certificate's
value lies in the pattern: an invariant checked before the search.

### 3.5 X5 — wobble-signature analogy (concept 7): not met

Each of the 9 signature targets was set against a structureless decoy within
`2^-40` of it. 8 of the 9 decoys produce identical signature columns over the
10,000-step stream. The one separated is `1/3`, a rational whose stream hits
an exact boundary that its decoy misses by `2^-40`. So the signature sees
magnitude and exact rational hits, and nothing else.
[`WOBBLE_LANDSCAPE_STUDY.md`](WOBBLE_LANDSCAPE_STUDY.md) found the same thing
for alpha from the other side. An associative generator over signatures
would propose analogies between numbers that are close, which the register
can already do by subtraction.

### 3.6 X6 — rational intervals (item E1): met, not wired

30 standard atomic weights were declared as intervals. They are transcribed
by hand, so they are an input to be checked against the CIAAW table before
anything else relies on them. Each register value was read at the precision
it was quoted to. A point comparison against the standard's central value
calls 14 register values different. Read as intervals, 23 register values
lie inside the standard interval, 7 are consistent only at the register's
stated precision (Li, O, Al, Fe, Co, Cu, Br), and 0 are inconsistent. Iron's
`55.84`, the planner's one "wrong" answer in Phase 58, is one of the seven:
the register holds `55.84` to two places, and `[55.835, 55.845]` meets
IUPAC's `55.845(2)`. On the 29 consecutive-pair ordering questions, the
interval comparison agrees with the point comparison every time and refuses
none. Atomic weights of different elements are far apart.

`GLM.SubstrateCognition.interval_lt_sound` and
`GLM.SubstrateCognition.interval_overlap_undecided` are the contract.
Disjoint intervals decide the order, and overlapping ones admit both orders,
so the comparison must refuse. This is the discrepancy report of candidate C
in miniature. It turns a point mismatch into a verdict with a stated
precision rather than an error.

### 3.7 X7 — derivations that carry their certificate (item E5): met, wired

The planner gains a frame for linear Diophantine equations in two unknowns,
Bézout coefficients and factorisation within a trial-division bound of
10⁶. On the 16 questions committed before the frame, it answers 13
correctly and refuses 3 correctly (a cofactor past the bound, a quadratic
and a non-integer coefficient), with 0 wrong. The bare grammar answers none
of the 13 and refuses all 16. Every answer carries a certificate that is
checked again before it leaves the module:
`GLM.SubstrateCognition.bezout_certificate_sound`,
`GLM.SubstrateCognition.no_solution_of_not_dvd` and
`GLM.SubstrateCognition.linear_solutions_complete` prove the certificates
sound and the family complete. A question past the bound is refused with the
bound named. No probabilistic primality test is used.

This is the only experiment of the round that a question put to the machine
can reach (`GLM.py --plan`). It moved **derivation**: the answers are
computed and held by no register. It is also the weakest interesting kind of
derivation, elementary number theory with a certificate, and it is reported
as that.

### 3.8 X8 — homographic transforms (refine item R2): met, not wired

A streaming Möbius transform on continued-fraction terms emits a term only
when every value still possible agrees on it. It was run on `(2x + 1)/(x + 3)`
for `phi`, `sqrt 2`, `e` and `pi`. All 82 emitted convergents agree with the
exact-real layer, and the input terms are themselves certified from interval
ends. After 64 steps, the continued-fraction fuel holds 87 to 219 bits of
the target, while the delta-sigma running average holds 6 to 10. That is the
engine's two-fuel comparison, restated at equal step counts. The transform is
a new exact operation on the value layer, and nothing asks for it yet.

### 3.9 X9 — the Lorentzian lattice (grow item G2): a first step

`0² + 1² + ⋯ + 24² = 4900 = 70²`, so the Weyl vector `(0, 1, …, 24 | 70)` of
`II₂₅,₁` is null (`GLM.SubstrateCognition.weyl_vector_null`). In Conway's
construction, the Leech lattice is the orthogonal complement of that vector,
modulo the vector. The time-like direction is a device of the construction,
and nothing measured here gives it a dynamics or a timescale. The concept's
suggestion that it grounds the TAX thresholds is not supported by anything
that was run.

## 4. Which faculty moved (D15)

* **Derivation — moved**, by X7 alone: 13 answers no register holds, each
  with a certificate, 0 wrong, on a set declared in advance.
* **Addressing — not moved.** X1 met its mark and is a candidate, since it
  recovers the codeword from two refused reads, but no runtime path supplies
  the second reading.
* **Refusal — not moved.** X4 and X6 met their marks and are candidates,
  since both turn a would-be answer into a certified "no" or a stated
  precision, but neither is reached by a question yet.
* **Refuted as stated:** concepts 1, 7 and 9, and concept 8 for a single
  tower. **Declined:** concept 3 and grow item G1. **Taken as ToDo:** the
  rest of §1.

## 5. What would earn the next round

In the order they bear on the target:

1. **Wire the interval layer into register answers** (X6 with candidate C),
   so that a field answer quotes the precision it holds and an ordering
   between overlapping readings refuses.
2. **Give the fork a second reading** (X1). The deep-hole escalation ladder
   already reads one carrier at several layers, so the question is whether
   two of its rungs are independent enough to intersect.
3. **Make the planner the default** (R1, candidate A), which now carries the
   certificate frame with it.
4. **The terminology sweep** (E2), in one batch, before anything is built on
   concept 6.

## 6. Round two (Phase 63) — declarations, written before any measuring code

The second round takes the open lines of §1 and §5, and follows one standing
instruction from the owner: **where a concept came close and missed, look
at the function again before discarding it.** Either it can be refined
into something that works, or it can be kept for the narrower job it does
do. G1 (a language model as parser) is **declined for good**. The GLM learns
from what such models do and translates the method into its own terms. It
does not embed one. Every probe set below is deterministic and exact (D7).
The question set is `evaluation/cognition_heldout.py`, committed with this
section and before the frames it tests.

**Y1 — the interval layer, reached by a question (E1, §5 item 1, candidate
C).** Two new readings in the typed planner.
*(a) Consistency with a quoted value:* *is the atomic weight of iron
consistent with 55.845?* The register value is read at the precision it is
held to (`Interval.as_held`), and the quoted decimal at the precision it is
written to. The answer is **yes** when the intervals meet and **no** when
they are disjoint, and it names both intervals.
*(b) Consistency with the declared standard:* *is the atomic weight of iron
consistent with the standard value?* reads against the 30-row
`IUPAC_WEIGHTS` table of X6. An element the table does not hold is refused,
with that reason.
*(c) Ordering:* a *heavier / lighter* comparison whose two held intervals
overlap is refused rather than answered.
*Pass mark:* 0 wrong on the declared Y1 questions, every declared refusal
refused, and no answer of the existing held-out sets changes.
*Prediction:* (c) changes no existing answer, because no two rows the
comparison reads overlap at their held precision. It is a guard, and the
round counts how often it fires.

**Y2 — rational recognition (concept 7, refined).** X5 found that the
wobble signature sees magnitude and **exact rational hits** and nothing else:
the one decoy it separated was `1/3`. The refinement keeps that and drops
the rest. A window of a signal pins the value to an interval: `N` ticks of
the delta-sigma stream give `floor(n t)` for every `n ≤ N`, and a decimal
quoted to `d` places gives a width of `10^-d`. The **simplest fraction** in
that interval is then recognised, and a certificate says how far it is
unique. If `p/q` is the least-denominator fraction in an interval of width
`w`, every other fraction in the interval has a denominator of at least
`1/(q w)`.
*(a) Wired:* *what fraction rounds to 0.142857?* The frame answers only when
the nearest rival's denominator is at least twice the answer's, that is
`2 q² w ≤ 1`, and refuses otherwise, naming the rivals' bound.
*(b) Measured:* every Farey fraction of order 16 inside `(0, 1)` (79 of
them), and the eight X5 targets other than `1/3`, each read from 512 ticks
of its own stream, with the X5 decoys as controls.
*Pass mark:* every one of the 79 rationals recognised exactly, 0 wrong, and
every non-rational target certified **not** a fraction of denominator at
most 16. *Control:* X5's signature match, which separated 1 target of 9.

**Y3 — dimensional derivation (concept 4, "mathematics first", and the
dimensional-equation half of E5).** *How does period depend on length and
acceleration?* Solve `M e = t` exactly over the rationals, where the columns
of `M` are the given quantities' dimension vectors and `t` is the target's.
There are three outcomes, each with a certificate.
* **Unique:** the answer is `target = k · Π given^e` for a dimensionless
  `k`, which dimensions cannot fix. The certificate is the exact check
  `M e = t` and the independence of the columns.
* **Impossible:** a certified **no**. The certificate is a rational `y`
  with `yᵀ M = 0` and `yᵀ t ≠ 0`.
* **Undetermined:** a refusal that names the dimensionless group left free.

The reading is made twice, with the extended ten-dimension vector (which
keeps the plane angle) and with the SI projection. Where the two disagree,
the planner's own rule refuses, as it does for torque against energy.
*Pass mark:* 0 wrong on the declared Y3 questions, and every declared
refusal refused.

**Y4 — vacuum seeking under a constraint (concepts 1 and 9, refined).** X3
refuted unconstrained descent, because the coherence TAX has the empty word
as its unique zero. §3.3 named the missing piece: a constraint that stops
the descent short of zero. The refinement is **descent inside the coset** of
the word read. For a 0/1 word, `HW·Y + ‖v‖²/8 = HW · (Y + 1/8)`, so the
minimum over `r ⊕ C` is the minimum-weight coset member.
*Measured:* 64 codewords at a fixed stride, each with 12 errors at a fixed
stride of every weight from 0 to 4 (3,840 reads). For each read, the exact
TAX-minimiser over its coset is set against the complete decoder.
*Pass mark:* the two agree on every read. A unique minimiser should give the
decoded codeword, and a tie should give the decoder's refusal with the same
candidate set.
*Also measured:* greedy descent inside the coset, which adds one of the 12
generators whenever that lowers TAX, and how often it reaches the true
minimum.
*Prediction:* agreement is total. That makes the refined concept **the
decoder itself**, not a new faculty. Greedy descent falls short.

**Y5 — nested holdouts for the chemistry estimates (E3).** Each admitted
completion rule was picked as the best of about fourteen candidates *on the
same leave-one-out errors that are then reported*, so the reported skill is
optimistic. *Measured:* for every field with an admitted rule, each
element is held out in turn. The rule is chosen again on the remaining
elements alone, by the same gate, and then scored on the held-out element.
*Pass mark:* none. This is a measurement of how much selection flattered
each rule. A field whose nested skill fails the gate (above one half) is
reported as not surviving selection.

**Y6 — C2, streams.** The delta-sigma bit stream, restated as a Lean
`Stream'`. The ones-count after `N` ticks is `⌊N t⌋`, and a rational `p/q`
gives a stream with period `q`.

**Y7 — C1, the stack as a Galois connection.** Refinement between layers is
the order of the partition lattice. The cumulative layer is the meet of two
layers (`glmIntegerLayer_least` is one half of that). Each layer's
projection gives an adjoint pair, image ⊣ preimage, between partition
lattices.

**Y8 — R1, the planner as the default path.** The number to take: on the
contract cases, how many answers change when the planner reads first, and
whether any of them becomes wrong. The switch is made only if none does.

## 7. Round two — what was measured

*Recomputed by `glm_universal.reasoning.substrate_cognition.round_two_report`
(Y1–Y5) and `planner_default_experiment` (Y8, through `tools cognition
--contract`). The Lean statements are in
`RequestProject/GLM/CognitionRoundTwo.lean`, which builds with the standard
axioms only and no `sorry`.*

**In one line.** Round two wired three more frames into the typed planner, which is now the default path: interval consistency, rational recognition and dimensional derivation answered 26 of 33 declared questions and refused the other 7 as declared, with 0 wrong where the grammar answered none.

The 33 questions are the three sets of `evaluation/cognition_heldout.py`:
26 answered correctly (7 interval, 7 recognition, 12 dimensional) and 7
refused correctly (1, 3 and 3), with 0 wrong. The grammar answered none of
the 33; it refused all of them, which is correct only for the 7 declared
refusals.

| item | pass mark met? | wired? | what it measured |
|---|---|---|---|
| Y1 interval layer (E1) | yes | yes | 7 correct, 1 correct refusal, 0 wrong; the grammar answered 0 of 8. The ordering guard fires on 0 of 6,903 element pairs and 0 of 1,275 molecule pairs, as predicted, and none of the 350 other held-out planner answers changed. |
| Y2 rational recognition (concept 7) | yes | yes | All 79 Farey fractions of order 16 recognised exactly from 512 ticks, 0 wrong. All 8 non-rational targets certified not a fraction of denominator at most 16, and every decoy got the same verdict as its target. Decimal questions: 7 correct and 3 correct refusals (2.71828, 1.41421 and 0.1, where a rival of small denominator sits in the quoted interval). |
| Y3 dimensional derivation (concept 4) | yes | yes | 12 correct, 3 correct refusals, 0 wrong; the grammar answered 0. The angular-frequency question is refused as ambiguous, because the extended reading (which keeps the plane angle) and the SI reading disagree. |
| Y4 vacuum seeking in a coset (concepts 1, 9) | yes | — | TAX is monotone in weight. The coset minimiser agrees with the complete decoder on 3,136 of 3,136 reads, including 768 ties refused with the same candidate set. Greedy descent reaches the minimum on 429. |
| Y5 nested holdouts (E3) | no mark declared | — | 7 of 9 rules survive selection; 2 do not (below). |
| Y6 streams (C2) | proved | — | `dsStream_sum`, `dsStream_bit`, `dsStream_drop_period`. |
| Y7 Galois connection (C1) | proved | — | `refines_iff_factors`, `ker_pair_eq_inf`, `ker_le_pair_iff`, `map_comap_gc`. |
| Y8 planner as default (R1) | yes | yes | Through the command line in fresh interpreters, the 177 contract cases score 149 correct and 28 refused as expected, both through the grammar and through the planner. Two answer texts differ and both still pass. The in-process run gives the same result. |

**Two corrections to the declarations.** The Y4 declaration said 3,840
reads. The run has 3,136, because weight 0 contributes one read per codeword,
not twelve: 64 × (1 + 4 × 12) = 3,136. The pass mark is unchanged and is met.
And X1's second reading is still open: nothing in round two supplied it.

**Nested holdouts, reported → nested skill** (a rule survives when its nested skill is at most one half; lower is
better):

| field | reported | nested | survives |
|---|---|---|---|
| `atomic_radius_pm` | 0.451 | 0.388 | yes |
| `boiling_point_K` | 0.359 | 0.358 | yes |
| `density_g_per_cm3` | 0.460 | 0.493 | yes |
| `electronegativity_pauling` | 0.421 | 0.425 | yes |
| `ionization_energy_eV` | 0.384 | 0.422 | yes |
| `melting_point_K` | 0.288 | 0.263 | yes |
| `valence_electrons` | 0.197 | 0.184 | yes |
| `covalent_radius_pm` | 0.457 | 0.631 | **no** |
| `electron_affinity_eV` | 0.489 | 0.823 | **no** |

**The "slight margin" cases, looked at again.** Three concepts from the first
round missed their marks narrowly. Round two did not discard them; it
examined each function and kept the part that works.
* **Concept 7** (wobble-signature analogy) missed as analogy, but it did
  separate exact rational hits. That part is now rational recognition, with
  a certificate: if `p/q` is the least-denominator fraction in an interval of
  width `w`, every rival has a denominator of at least `1/(q w)`
  (`farey_rival_bound`). It is wired as a planner frame.
* **Concepts 1 and 9** (TAX as a loss, vacuum seeking) failed because
  unconstrained descent reaches the empty word. Constrained to the coset of
  the word read, the minimiser is exactly the complete decoder
  (`coset_argmin_iff_nearest`), so the concept is kept as a second
  description of decoding, not a new faculty.
* **E1** (rational intervals) met its mark but no question reached it. It is
  now wired, and its ordering guard is kept as a guard: it fires on no
  current pair, and it will refuse if a later register row overlaps.

**Which faculty moved.** Derivation moved again, through Y1 (consistency
answers) and Y3 (dimensional equations). Addressing moved through Y2: a
quoted decimal is addressed to its simplest fraction, with a certificate.
Refusal is sharper: all 7 declared refusals are refused with a stated
reason (an overlapping rival, an ambiguous dimension reading, or an element
the standard table does not hold).

## 8. What would earn the next round

In the order they bear on the target:

1. **Demote the two rules that fail nested holdouts** (`covalent_radius_pm`,
   `electron_affinity_eV`), or keep them for the narrower subset on which
   they survive, and quote the nested skill beside the reported one.
2. **E4, semantic judgements as annotated provenance.**
3. **E6, generate the frames from a declaration.** Round two added three
   frames by hand; the declaration they share is now visible.
4. **E7, deepen the PCGS proofs.**
5. **X1's second reading**, so that the fork can be wired.
6. **Candidate E** of `STATUS.md` §3.4.
7. **Concept 6** stays open until the runtime holds a trilinear object.
