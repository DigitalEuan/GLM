# The Lorentzian evidence space — what the lift gives reasoning beyond the Golay tie

## Tier 0 — the coarse read

**Question.** Phase 182 lifted the Golay tie space to II_25,1 and found that the lift certifies a tie but cannot break one. Can the ambiguous space, read in the lift, be of use for reasoning in general, not only for decoding puzzles, and what does it settle of the three lines Phase 182 left?

**Verdict.** The lift is an evidence space: any finite set of weighted cues, in any dimension, sums to one vector that is the lifted consensus plus the Weyl vector times the cues' disagreement, so cues add, a tie is the consensus on a mirror, disagreement is minus the Lorentzian norm, and analogy is evidence with weights 1, −1, 1; in use it refuses what it should — answers outside the tie's certificate, examples that do not state one relation, a name the dimension layer cannot choose — at no cost in right answers, and a tie asks the one question that settles it, but where relations are not displacements it helps little, and the decoy readings it still answers wrongly carry no information that could tell them from honest ones.

**Deciding figure.** 13 of 15 marks; Golay decoy 61 wrong → 27 under the certificate guard with 0 right answers lost on any condition, and all 27 indistinguishable from honest readings; the settling question 600 of 600 with five bits (random five 391); physics relations with a decoy example 0 wrong against 87 and 38 for the first example alone; names 10 wrong of 13 → class certificates holding the expected name 12 times; semantic relations 6.7 % precise.

**Recomputed by.** `glm_universal.reasoning.lorentzian_evidence_study.lorentzian_evidence_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

*Created 23 October 2026. Pre-registered 23 October 2026: the marks (§6) were
written into `reasoning/lorentzian_evidence_study.py` before the full
measurement. G2 and G3 were written after a prototype run of the Golay decoy
census, and G5b after a trial run showed that G5 mis-states the theorem it
was meant to test; all three are labelled so. Measured 23 October 2026, one
take.*

## 0. What this document is

**In one paragraph.** The lift is an evidence space: any finite set of weighted cues, in any dimension, sums to one vector that is the lifted consensus plus the Weyl vector times the cues' disagreement, so cues add, a tie is the consensus on a mirror, disagreement is minus the Lorentzian norm, and analogy is evidence with weights 1, −1, 1; in use it refuses what it should — answers outside the tie's certificate, examples that do not state one relation, a name the dimension layer cannot choose — at no cost in right answers, and a tie asks the one question that settles it, but where relations are not displacements it helps little, and the decoy readings it still answers wrongly carry no information that could tell them from honest ones.

Phase 183, at the owner's request of 23 October 2026: take
[`STATUS.md`](../STATUS.md) §2.1 item 11, *the Lorentzian lift, the next
layer*, further, and ask whether the ambiguous space can be of use for general
reasoning rather than puzzle solving. Phase 182
([`LORENTZIAN_LIFT_STUDY.md`](LORENTZIAN_LIFT_STUDY.md)) left three lines:

1. a guard that keeps a reading of a different message from misleading the
   summed score (its mark M11 was not met: 61 wrong on the decoy);
2. the same certificate and summed scores beyond the Golay layer;
3. a surface that collects the further readings a tie needs.

This study answers the general question first (§1–§2, a theorem file in any
dimension), then measures it on three surfaces: the Golay tie space Phase 182
left (§3), relations over the physics register (§4), and relations over the
semantic lexicon (§5).

## 1. The idea, by analogy: evidence as momentum

The owner's method for a stuck design question
([`ITERATE.md`](../ITERATE.md) §1) is to name a well-established system the
problem resembles. Here it is special relativity's **energy–momentum of a
system of photons**:

| relativity | the lift | maps? |
|---|---|---|
| a photon's four-momentum is null | the lift `L(x) = (x, (1 − |x|²)/2, (1 + |x|²)/2)` is null (`lift_null`) | yes |
| the momenta of several particles add | the evidence `V = Σ wᵢ L(xᵢ)` is linear, and so are its scores (`inner_evid`) | yes |
| a system of photons has a rest frame, where its momentum is at rest | `V = W · L(x̄) + (D/2) · w`: the consensus `x̄` is the "rest frame" (`evidence_decomp`) | yes |
| its invariant mass² is the sum over pairs of the photons' spread | `⟨V, V⟩ = −W · D` (`evid_norm`); for unit weights `−Σ_{i<j} |xᵢ − xⱼ|²` | yes |
| photons moving together are massless together | the evidence is null exactly when every cue agrees (`evid_null_iff`) | yes |
| energy is positive | a negative weight is allowed (analogy uses `−1`), and then `D` can be negative | **no** — the analogy breaks for negative weights, and the theorems that need it say so (`disp_nonneg`, `disp_le`, `evid_null_iff` assume non-negative or positive weights) |

So the ambiguous space is not a defect to be removed: in the lift it is the
place where several pieces of evidence meet, and the geometry says how they
combine (linearly), where they agree (null), how much they disagree (the
norm), and when no amount of combining can choose (a mirror).

## 2. What is proved

**[`glm_lean/RequestProject/GLM/LorentzianEvidence.lean`](../glm_lean/RequestProject/GLM/LorentzianEvidence.lean)**
— over `ℚ`, for any dimension `n`, any finite index set and any weights, built
on Phase 182's `LorentzianLift.lean`.

* `inner_evid`, `evid_score` — cues add: `⟨V, r_λ⟩ = W − ½ Σ wᵢ |xᵢ − λ|²`;
* `steiner` — the parallel-axis theorem `Σ wᵢ |xᵢ − λ|² = D + W |x̄ − λ|²`;
* `evidence_decomp` — **the decomposition** `V = W · L(x̄) + (D/2) · w`;
* `evid_score_cent`, `evid_rank`, `evid_tie` — the evidence prefers the
  candidate nearer the consensus (`W > 0`) and ties exactly on the
  consensus's mirrors;
* `evid_norm` — **`⟨V, V⟩ = −W · D`**;
* `disp_nonneg`, `disp_le` — with non-negative weights the consensus
  minimises the weighted spread;
* `dispersion_guard_sound` — cues within budgets `ρᵢ` of one common point
  have `D ≤ Σ wᵢ ρᵢ`: a guard that refuses above that never refuses an honest
  set;
* `disp_eq_zero_iff`, `evid_null_iff` — with positive weights, no
  disagreement and a null evidence vector each happen exactly when every cue
  agrees;
* `analogy_evidence`, `analogy_score` — `A : B :: C : ?` is
  `L B − L A + L C = L(C + B − A) + (−(A − B)·(A − C)) · w`: the displacement
  solver's target is the consensus of an evidence vector with weights
  `1, −1, 1`, and several examples of one relation are several such vectors
  summed;
* `agree_on_iff`, `separates_iff`, `card_ge_of_separates` — **the question a
  tie asks**: when the tied candidates are a word flipped on pairwise
  disjoint blocks (a Golay sextet: six disjoint tetrads), revealing positions
  `Q` tells two candidates apart exactly when `Q` meets one of their blocks;
  `Q` separates them all exactly when at most one block misses it; and such a
  `Q` has at least `m − 1` positions — five for a sextet.

The file is in `AxiomAuditAll.lean`; the whole-development audit reports
10038 theorems on the standard axioms.

## 3. The Golay tie space, again

Phase 182's own queries, same seed, 600 per condition. Three rules beside
Phase 182's guarded summed score (`guarded`, the 6-bit guard):

* `certificate` — the answer must also be one of the first reading's tied
  candidates (`lorentzian_evidence.certificate_resolve`): further readings
  choose *within* the tie's certificate and do not overrule it;
* `dispersion` — `guarded`, refused when the readings' dispersion in the
  Leech scale exceeds the channel budget `(4 + 6 (k − 1)) / 2` (the first
  reading at most 4 errors, the others at most 6), which
  `dispersion_guard_sound` says no honest set exceeds.

| readings | `guarded` right / wrong / refused | `certificate` | `dispersion` |
|---|---|---|---|
| 4+0, 4+1, 4+2, 4+3 | 600 / 0 / 0 each | 600 / 0 / 0 each | 600 / 0 / 0 each |
| 4+4 | 586 / 0 / 14 | 586 / 0 / 14 | 586 / 0 / 14 |
| 4+5 | 495 / 3 / 102 | 495 / 3 / 102 | 495 / 3 / 102 |
| 4+6 | 318 / 24 / 258 | 318 / 17 / 265 | 318 / 24 / 258 |
| 4+4+4 | 600 / 0 / 0 | 600 / 0 / 0 | 600 / 0 / 0 |
| 4+4+6 | 594 / 0 / 6 | 594 / 0 / 6 | 594 / 0 / 6 |
| decoy | 10 / 61 / 529 | 10 / 27 / 563 | 10 / 61 / 529 |

**The certificate guard.** It removes 34 of the 61 wrong decoy answers and 7
of the 24 wrong answers on 4+6, and it loses no right answer on any
condition. That is what soundness predicts: in every condition the first
reading's tied set holds the sent codeword, so a right answer is always
inside it.

**What it leaves, and why no guard can remove it.** Each of the 27 wrong
decoy answers that remain is one of the first reading's tied candidates, and
the second reading lies within 6 bits of it (27 of 27). So the same two
readings could be an honest 4+k reading of that answer, with `k ≤ 6`. A rule
that sees only the readings gives the same reply on both; if it answered the
honest set right, it answers the decoy wrong. Removing these 27 needs
information the readings do not carry — which message each reading is of.
Phase 182's mark M11 (0 wrong on the decoy while keeping 90 % of the right
answers) asked the readings for exactly that.

**The dispersion guard.** Sound (no right answer lost anywhere), and it never
fires: 0 triggers on every condition, the decoy included. For two readings
the dispersion is a quarter of their Hamming distance, so the budget of 5
allows readings up to 20 bits apart, and the decoy's readings are nearer than
that. The consensus of two Golay readings is not a codeword, so the
dispersion bound — which holds for *any* common point — is far looser than a
bound per reading. A negative result: on this surface the per-reading budget
(the certificate guard) is the one that works.

**The settling question.** For a single tied reading the certificate names
the six candidates and their six tetrads; `separates_iff` says which sent bits
settle the tie. `tool lorentz` now asks for the sent bits at five positions,
the least position of each of five tetrads.

| question | right | wrong | still tied |
|---|---|---|---|
| the five asked positions | 600 | 0 | 0 |
| five random positions | 391 | 0 | 209 |

On all 600, every four of the five asked positions leave some candidate
unsettled (G5b) — the worst case `card_ge_of_separates` is about. Four
positions do settle the *sent* codeword whenever one of them falls in that
codeword's own tetrad (86 of 600 tied readings had no four-subset that failed
on the sent codeword), which is why the mark first declared (G5: "no four
positions settle the sent codeword") is not met: it mis-stated the theorem.

## 4. Relations over the physics register

A relation is a displacement of EXT10 exponents, taken from the thirteen
curated physics analogies of `benchmarks/suites.py` (8 distinct relations
with at least four example pairs in the register); its examples are register
pairs `(a, b)` with `exps(b) − exps(a)` equal to it; a query applies it to a
register quantity `c`. 300 queries per condition. A query is right when the
answer is the dimension class `exps(c) + d`, and a query whose class is not in
the register should be refused.

| condition | `first` (first example alone) | `lorentz` (consensus, nearest class) | `guarded` (refuse if `D ≠ 0`) | `vote` (majority target) |
|---|---|---|---|---|
| clean1 | 148 / 0 / 152 | 148 / 53 / 99 | 148 / 0 / 152 | 148 / 0 / 152 |
| clean2 | 166 / 0 / 134 | 166 / 58 / 76 | 166 / 0 / 134 | 166 / 0 / 134 |
| clean3 | 146 / 0 / 154 | 146 / 77 / 77 | 146 / 0 / 154 | 146 / 0 / 154 |
| decoy2 (one example and one decoy) | 80 / 87 / 133 | 2 / 137 / 161 | 0 / 0 / 300 | 0 / 0 / 300 |
| decoy3 (two examples and one decoy) | 113 / 38 / 149 | 73 / 215 / 12 | 0 / 0 / 300 | 155 / 0 / 145 |

(right / wrong / refused.) On the clean conditions every query whose target
class is in the register is answered right and the rest refused; the
unguarded `lorentz` answers the absent ones with the nearest class, which is
wrong 53 to 77 times. With a decoy example, `guarded` refuses every query —
`evid_null_iff` says the targets' dispersion is zero exactly when the
examples agree — where the first example alone is wrong 87 and 38 times and
the consensus 137 and 215 times.

**Where the guard is not the best rule.** With two good examples and one
decoy, the majority vote answers 155 right and 0 wrong, where `guarded`
refuses all 300. The dispersion detects the conflict; it does not say which
examples to believe. Splitting the cues into agreeing groups (each with
`D = 0`) and keeping a strict majority is the vote, and on this surface it is
better. Recorded as it is.

**A conflict between examples catches a relation that is not a
displacement.** `length : wavenumber :: time : ?` is a reciprocal, not a
displacement, and with one example the displacement lands on
`chromatic_dispersion` (L^-2 T), a register quantity of the wrong dimension.
Given two examples of the same reciprocal relation —
`tool evidence length : wavenumber, time : frequency :: mass` — their targets
disagree and the tool refuses. One example can never show this.

**The name layer.** On the thirteen curated analogies the shipped physics
analogy names a quantity: right by name 3 times, wrong 10 times (its class is
right 12 times). The lifted answer names the class and refuses to choose a
name inside it — by `evid_tie` every member of a class is equidistant from
the target, so the dimension layer cannot choose — and the expected name is
in the certified class on 12 of 13. The thirteenth is the reciprocal case
above, so the declared mark P4 (every class answer holds the expected name)
is not met.

## 5. Relations over the semantic lexicon

The 149-word semantic lexicon, its ten primitive coordinates, and every
relation it states between two of its own words with at least five pairs (14
relations); `k` examples of the relation applied to `c`, at most 12 example
sets per query and `k`.

| `k` | queries | `lorentz` right / wrong / refused | `vote` right / wrong / refused |
|---|---|---|---|
| 1 | 3143 | 172 / 2572 / 399 | 172 / 2572 / 399 |
| 2 | 3346 | 191 / 2634 / 521 | 91 / 955 / 2300 |
| 3 | 3346 | 207 / 2936 / 203 | 94 / 755 / 2497 |

More examples help a little: right per query 5.5 % at `k = 1`, 6.2 % at
`k = 3` (S1). The dispersion is a confidence signal, weakly: the answers in
the low-dispersion half are right 8.4 % of the time (125 of 1492), all
answers 6.7 % (199 of 2984) (S2). But the surface is mostly out of reach:
these relations are not displacements of the primitives
([`ANALOGY_LAYER_STUDY.md`](ANALOGY_LAYER_STUDY.md) found the same), and
summing examples of a relation that is not a displacement cannot make it one.

## 6. Marks

| mark | declared | result |
|---|---|---|
| E1 | identities exact on 200 sampled evidence sets (Golay, register, analogy cues) | met (200, 200, 200) |
| G1 | certificate guard right exactly as often as `guarded`, every Golay condition | met |
| G2 | *(after the prototype)* certificate guard fewer wrong on the decoy | met (27 against 61) |
| G3 | *(after the prototype)* every remaining decoy error indistinguishable from an honest set | met (27 of 27) |
| G4 | dispersion guard right exactly as often as `guarded` on every honest condition | met |
| G5 | the settling question settles every tied reading, and no four of its positions settle the sent codeword | **not met**: the first half holds (600 of 600), the second mis-states the theorem (86 of 600) |
| G5b | *(after the trial)* every four of the five asked positions leave some candidate unsettled | met (600 of 600) |
| G6 | five random positions settle fewer | met (391 against 600) |
| P1 | `guarded` 0 wrong on every physics condition | met |
| P2 | clean conditions: `guarded` right on every present target, refusing the rest | met |
| P3 | decoy conditions: `guarded` refuses all; `first` and `lorentz` wrong at least once | met |
| P4 | name layer: every class answer holds the expected name | **not met**: 12 of 13, the reciprocal relation |
| S1 | semantic `lorentz` at `k = 3` right at least as often per query as at `k = 1` | met |
| S2 | low-dispersion half more precise than all answers | met |
| L | the Lean file, no `sorry`, audited | met |

13 of 15 marks.

## 7. What it gives the GLM's reasoning

Under the standing target ([`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md)),
assigned as [`BLOCKERS_STUDY.md`](BLOCKERS_STUDY.md) §1 asks:

* **Refuse.** Three refusals that cost no right answer: the certificate guard
  (34 wrong decoy answers and 7 wrong 4+6 answers removed, `tool lorentz`
  uses it); a conflict between examples (`tool evidence`, 0 wrong on both
  decoy conditions where the first example alone is wrong 87 and 38 times);
  and the name a dimension layer cannot choose (10 wrong names of 13 become
  class answers).
* **Address.** The settling question: a single tie is now answered after
  five revealed bits, 600 of 600, and `tool lorentz` asks for exactly those
  five. On the semantic lexicon more examples address slightly better (5.5 %
  to 6.2 % right per query).
* **Derive.** Nothing: every answer here is a register entry or a codeword.

What the round says about the owner's question — whether the ambiguous space
is of use beyond puzzles — is that the lift turns ambiguity into three
operations that are not about codes at all: combine (cues add, in any
dimension, over any register), measure conflict (the norm), and ask (the
mirror says which information is missing). Their value depends on whether the
domain's relations are displacements: exactly so in the physics dimension
layer, hardly at all among the semantic primitives.

## 8. What this does not do, and what is next

* **The 27.** No reading-only rule removes the remaining decoy errors without
  refusing honest readings (§3). A sender tag or any other record of which
  message a reading belongs to would; Phase 133's seven-bit tag is the
  measured instrument of that kind.
* **Majorities.** Where the examples conflict, splitting them into agreeing
  groups and keeping a strict majority beat refusing (155 against 0 on
  decoy3). A declared rule for it, with its own soundness condition, is the
  obvious next mechanism.
* **Leech-level ties and the other 22 deep-hole types.** The theorems are in
  any dimension and for any candidate points; the evidence space applies
  unchanged to `reasoning/tie_break.py`'s address ties. Not measured here.
* **A conversation turn that asks.** `tool lorentz` now asks for five bits
  and reads them back in the same command; holding the ask open across turns
  (as Phase 173 does) is still open.
* **Relations that are not displacements.** The lift adds nothing to a
  relation the coordinates do not carry. The named-relation layer
  ([`ANALOGY_LAYER_STUDY.md`](ANALOGY_LAYER_STUDY.md)) is where those live.

## 9. Reproduce

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.tools lorentzian-evidence          # the stored marks
PYTHONPATH=. python3 -m glm_universal.tools lorentzian-evidence --write  # re-take (~10 minutes)
python3 GLM.py -q "tool lorentz 15"                                       # a tie, with the five positions it asks for
python3 GLM.py -q "tool lorentz 15; @0=0 5=0 6=0 7=0 11=0"                # settled by those bits
python3 GLM.py -q "tool evidence velocity : acceleration, mass : density :: momentum"   # refused: no one relation
lake build RequestProject.GLM.LorentzianEvidence
```

The mechanism is `glm_universal/reasoning/lorentzian_evidence.py`,
the measurement `glm_universal/reasoning/lorentzian_evidence_study.py`,
the tests `glm_universal/tests/test_lorentzian_evidence.py`.
