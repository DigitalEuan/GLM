# The carried fork: six Golay candidates carried until a later decision resolves them

## Tier 0 — the coarse read

**Question.** If the six equidistant candidates of a deep-hole Golay read are carried forward instead of refused, can later decisions resolve them without a wrong answer, and does escalating the read to the Leech lattice add anything?

**Verdict.** Partly: carried forward, the six candidates are resolved with 0 wrong by every certified stage — the declared cases, a second reading and an unsure set — and four of the six declared pass marks were met; the declared-case stage missed its 90 % mark at 32 cases, and the escalated Leech-scale estimate missed its 90 % mark.

**Deciding figure.** 0 wrong over 658,812 declared-case reads, 4,224 double reads, 3,840 unsure-set reads and 448 certified cuts; 1,771 of 1,771 weight-4 cosets lift to a certified A₁²⁴ deep hole of 48 vertices; the escalated estimate is right on 512 of 768.

**Recomputed by.** `glm_universal.reasoning.carried_fork.carried_fork_report`

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `glm_universal.corpus.checks.tier_report` fails if they stop being.*

---

## 0. Where this comes from

The owner, on the refusals the Golay layer gives at the deep hole:

> *I think we had a method where all 6 are carried until resolved by a later
> decision, pruned or proven incorrect for that resolution so we can resolve
> more accurately, escalation to the Leech Lattice or other may also be able
> to extend the GLM's ability to work with information.*

The method exists in pieces and none of them is on a path a question can
reach:

* `substrate/superposition.py` (the "Geometric Ambiguity and Conceptual
  Superposition" directive) keeps the six candidates as a `Superposition`
  and filters them with `collapse(context)`, and proves that the rational
  bundle of the six carries the received word without loss
  (`GLM/Superposition.lean`). Nothing downstream calls it.
* Experiment X1 of
  [`SUBSTRATE_NATIVE_COGNITION_STUDY.md`](SUBSTRATE_NATIVE_COGNITION_STUDY.md)
  intersected the forks of two reads of one codeword and answered 4,224 of
  4,224 double reads with 0 wrong. It was recorded as **met, not wired**:
  no runtime path supplies a second reading.
* The Python dialect of Phase 64
  ([`PYTHON_SPEECH_STUDY.md`](PYTHON_SPEECH_STUDY.md)) refuses `classify` at
  coset weight 4 as `AMBIGUOUS` — 10,626 refusals around one declared case
  set — even when only one of the six candidates is a declared case.

This round makes the fork a value that is carried, records *why* each
candidate leaves it, and measures four ways a later decision can resolve it:
a declared context, a second reading, a proof that a candidate is impossible,
and an escalated (Leech-scale) reading.

## 1. The object

A **carried fork** is the received 24-bit word, its six candidates (one per
tetrad of the sextet the coset's leaders form), the candidates still live,
and a **ledger**: every elimination names the stage that made it and the
reason. The rules, which the Lean file of this round states and proves:

1. **Nothing leaves without a reason.** A candidate is removed only by a
   named stage; the ledger and the live set always partition the six.
2. **No order-based choice.** A fork is *resolved* exactly when one
   candidate is live, *open* when more than one is, and *contradicted* when
   none is. Nothing ever picks the first of several.
3. **Soundness is conditional and stated.** If every stage removes only
   candidates that are not the truth, and the truth was in the fork, then a
   resolved fork holds the truth. Which stages have that property, and under
   what assumption, is part of each stage's declaration.

The stages:

| stage | what removes a candidate | assumption that makes it sound |
|---|---|---|
| **context** | a declared predicate is false of it (for `classify`, the candidate is not a declared case) | the truth satisfies the predicate (closed world: the truth is a declared case) |
| **second reading** | it is absent from the fork of another read of the same word | both reads are of one carrier, each within coset weight 4 |
| **unsure set** | its tetrad touches a coordinate the reader marked sure | errors occur only on coordinates marked unsure |
| **escalation** | on a rational (soft) reading lifted to the Leech lattice, it is not under a nearest hole vertex | none: this stage is an **estimate**, and is labelled one |

## 2. Declarations — written before any measuring code

Every probe set is deterministic: no random source, no seed, exact integers
and `Fraction` only (D7). The probe of X1 is reused where named: the 64
codewords at stride 64 through the sorted 4,096, and the 12 weight-4 errors
at a fixed stride through `C(24, 4)`, giving 768 single reads and 4,224
double reads.

**K1 — resolution by the declared cases (context stage).** *Case sets:* for
`k ∈ {2, 4, 8, 16, 32}`, `S_k` is the `k` codewords at indices
`1 + j·⌊4096/k⌋`, `j < k`, of the sorted code. *Reads:* for every case `c ∈
S_k` and every one of the 10,626 weight-4 errors `e`, the subject `c ⊕ e`
(658,812 reads in all). *Run:* Phase 64's `classify` (control), then the
carried fork pruned to `S_k`. *Pass mark:* **0 wrong, required**; at least
**90 %** of the reads answered at every `k`. Faculty: **refusal → derivation**
for `classify`. *Hostile control, reported and not a mark:* for each `k`, the
768 X1 reads of codewords that are **not** in `S_k`; every answer the
carried fork gives there is wrong under an open world, and the count is the
price of the closed-world assumption. Phase 64's `classify` answers none of
them. Wherever the context stage answers, its certificate must name the
closed-world assumption.

**K2 — the second reading, wired.** The X1 probe run through the carried
fork's intersection stage must reproduce X1 exactly: 4,224 of 4,224 double
reads answered, 0 wrong; and the refusal witness (two tetrads splitting one
octad) must leave exactly two live candidates, the truth and the truth plus
that octad. Faculty: **address**, now reachable.

**K3 — proven incorrect by an unsure set.** On the 768 X1 reads, the reader
marks the unsure set `U = e ∪ R_r`, where `R_r` is the first `r` coordinates
in the order `0..23` outside the true error `e`, for `r ∈ {0, 1, 2, 3, 4}`.
A candidate whose tetrad meets a coordinate outside `U` is proven incorrect.
*Pass mark:* **0 wrong, required**; for `r ≤ 3` (`|U| ≤ 7`) **all 768**
answered — declared from the theorem that two tetrads of one sextet are
disjoint, so two cannot fit in fewer than eight coordinates. For `r = 4` the
count is reported, and every refusal must be a `U` that is exactly the union
of two tetrads of the sextet.

**K4 — escalation to the Leech lattice.**

* **K4a, the hard lift.** For each of the 1,771 weight-4 cosets, with the
  representative the smallest leader `y`, the Leech point `2y` (the scale of
  `substrate/leech2.py`, minimal norm 32) is at raw squared distance 16 —
  the covering radius squared — from **exactly 48** Leech points, **8** over
  each of the six candidates `c` (the points `2c + 4z` that the congruences
  admit), and `reasoning/deep_holes.hole_diagram` certifies the 48 as a deep
  hole of type **A₁²⁴**. *Pass mark:* 1,771 of 1,771. (One word, `y =
  0b1111`, was checked while scoping this declaration; it gave 48 vertices
  and a certified A₁²⁴.) The consequence is declared now: the lift of a
  hard word carries 48 points where the Golay layer carried 6, and resolves
  nothing by itself.
* **K4b, a soft reading.** For read `i` of the 768 X1 reads (truth `c`, error
  `e`, hard word `h = c ⊕ e`) and coordinate `j`, the reliability is
  `ρ_j = ((7i + 11j) mod 8 + 1)/8` for `j ∉ e` and
  `ρ_j = ((5i + 3j) mod 4 + 1)/8` for `j ∈ e` (a wrong bit is received
  weakly: `ρ ≤ 1/2`); the soft level is `s_j = (1 + ρ_j)/2` if `h_j = 1` and
  `(1 − ρ_j)/2` otherwise. The escalation keeps the candidates under the hole
  vertices nearest to `2s`, exactly. *Controls:* the retired snap (chance
  `1/6`), the unconstrained soft decoder over all 4,096 codewords
  (`reasoning/fwht_decode.decode_soft`), and the unconstrained Leech decoder
  on `2s` (`reasoning/analogy.nearest_lattice_point`). *Pass mark:* the
  escalated estimate is correct on at least **90 %** of the 768, with its
  wrong count reported beside it; it is an estimate and is never reported as
  a certified answer. *Declared check:* on this ensemble the nearest hole
  vertices and the plain Euclidean ranking of the six candidates agree on
  every read.
* **K4c, a certified cut from the same reading.** The ensemble promises
  that every wrong bit has `ρ ≤ 1/2`, so the unsure-set stage with
  `U = {j : ρ_j ≤ 1/2}` is sound. *Pass mark:* **0 wrong, required**, for
  the answers this stage gives alone; the number it resolves is reported,
  and the escalated estimate is then applied only to what it leaves open.

**What would count as moving the target (D15).** K1 moves **refusal** and
**derivation** for `classify` if it passes and is reachable from the Python
dialect; K2 moves **address** if the intersection is reachable from a
question; K3 and K4c move **refusal** (a refusal becomes a proof); K4a is a
structural finding and moves nothing; K4b moves nothing that is certified.

## 3. Results

Every figure below is recomputed by
`python3 -m glm_universal.tools carried-fork` (`--json` for all of it,
`--quick` to sample the census). The theorems are in
`RequestProject/GLM/CarriedFork.lean`; they build with no `sorry` and depend
only on the standard axioms. **Four of the six declared marks were met (K2,
K3, K4a, K4c) and two were not (K1, K4b)** — so the answer is partly yes. No
certified stage gave a wrong answer anywhere: carried forward, the six
candidates are resolved by the declared-case stage, the second reading and
the unsure set without error.

### 3.1 K1 — the declared cases: 0 wrong, but the 90 % mark is missed at `k = 32`

| `k` | reads | answered | wrong | left open | answered share | open-world misreads (of 768) |
|---|---|---|---|---|---|---|
| 2 | 21,252 | 21,112 | 0 | 140 | 99.3 % | 14 |
| 4 | 42,504 | 41,676 | 0 | 828 | 98.1 % | 28 |
| 8 | 85,008 | 81,256 | 0 | 3,752 | 95.6 % | 56 |
| 16 | 170,016 | 156,512 | 0 | 13,504 | 92.1 % | 112 |
| 32 | 340,032 | 291,712 | 0 | 48,320 | **85.8 %** | 96 |

Phase 64's `classify` answers none of these reads (it refuses every one as
`AMBIGUOUS`, checked on a stride sample of each set), and none of the hostile
reads. The carried fork answers 592,268 of the 658,812 with **0 wrong**, as
`GLM.CarriedFork.resolved_eq_truth` requires: the truth is a declared case and
lies in the fork, so a single declared survivor is the truth. A fork is left
open only when a second declared case is the truth plus an octad containing
the error's tetrad — 70 of the 10,626 errors per such pair — and the strided
sets hold more octad-separated pairs as they grow, which is why the share
falls with `k`. **The declared mark — 90 % at every `k` — is not met**: it
fails at `k = 32`.

**The price of the closed world** is the last column. On reads of codewords
that are *not* declared cases, the context stage answers 14 to 112 of 768,
and every one of those answers is wrong. `classify` refuses all of them. The
stage is therefore exposed only as `resolve`, never as a change to
`classify`, and its column-1 text names the closed-world assumption on every
answer it gives.

**Carrying further (post hoc, not a declared mark).** The 48,320 forks left
open at `k = 32` were carried to a second read of the same carrier (the next
error of the declared list): 35,872 more are resolved, 0 wrong, and 12,448
stay open. With the second reading the share at `k = 32` is 96.3 %. This is
the owner's method working as described — the fork is not refused when one
decision leaves it open, it waits for the next one — but it was not declared
before it was measured, so it is reported and not scored.

### 3.2 K2 — the second reading, wired: met

Through `CarriedFork.intersect`, X1 is reproduced exactly: 4,224 of 4,224
double reads answered, 0 wrong. The witness — two tetrads that split one
octad — leaves exactly two live candidates, the truth and the truth plus the
octad, and is refused as `AMBIGUOUS`. The stage is now reachable from a
question: `agree(r1, r2, ...)` in the Python dialect (§4).

### 3.3 K3 — proven incorrect by an unsure set: met

All 768 reads are answered correctly at every unsure-set size from 4 to 8
coordinates — 3,840 unsure-set reads in all — with 0 wrong. For `|U| ≤ 7` this is the theorem
`GLM.CarriedFork.unsure_resolves`: tetrads of one sextet are pairwise
disjoint, so two cannot fit inside fewer than eight coordinates. At `|U| = 8`
the declared padding (the first four coordinates outside the error) never
completes a second tetrad on this probe, so no refusal occurs; the refusal
case exists in principle and is exercised by the unit tests through the
second-reading witness instead.

### 3.4 K4 — escalation to the Leech lattice

**K4a, the hard lift: met.** All 1,771 weight-4 cosets lift to a point `2y`
at raw squared distance 16 from exactly 48 Leech points, 8 over each of the
six candidates, and `deep_holes.hole_diagram` certifies every one as a deep
hole of type **A₁²⁴** — the barycentre identity holds with Coxeter number 2
and total rank 24, so no further vertex exists. The lower bounds behind
"nothing is nearer" are `GLM.CarriedFork.even_lift_dist` and
`GLM.CarriedFork.odd_lift_dist`. So the Golay tie is not an artefact of the
code: escalated to the Leech lattice without new information, it *is* a deep
hole — of the one Niemeier type whose glue code is the Golay code itself —
and the lattice carries 48 points where the code carried 6. Escalation alone
resolves nothing.

**K4b, a soft reading: not met.** The escalated estimate is right on 512 of
768 (two thirds), wrong on 96, and exactly tied on 160 — the declared mark
was 90 %. The nearest hole vertices and the plain Euclidean ranking of the six
agree on all 768 reads, as declared; `GLM.CarriedFork.soft_cost_sum` is why —
the extra squared distance a candidate pays is the total reliability of its
tetrad. Every wrong estimate had margin exactly `1/2`. For comparison, on the
same reads: the retired snap is right on 154; the unconstrained soft decoder
over all 4,096 codewords is right on 480, and its answer lies in the fork on
736; the unconstrained Leech decoder on `2s` is right on 560, but 64 of those
are among the 160 exact ties, which it breaks lexicographically, so on the
608 untied reads it is right on 496 against the fork estimate's 512. The fork
is therefore not a handicap for the lattice reading — restricting to the six
helps — but on this ensemble the soft reading does not carry enough to
answer at the declared rate.

**K4c, a certified cut from the same reading: met.** Using the ensemble's
promise that a wrong bit is received with reliability at most `1/2`, the
unsure-set stage resolves 448 of the 768 reads by proof, 0 wrong. The
escalated estimate applied to the 320 it leaves open is right on 128 and
wrong on 96 (the rest tied).

## 4. What is wired

* **`reasoning/carried_fork.py`** — the `CarriedFork` object, its ledger and
  its three certified stages; the Leech lift and its certification; the
  escalated estimate, returned beside the fork and never written into its
  ledger; the experiments.
* **The Python dialect** (`GLM.py --python SOURCE`) gains four builtins, each
  answered as a Three Column payload whose column-3 script re-derives it in a
  fresh `python3 -I`, and each refusing by name:
  `nearest(s)` (the carried candidates), `resolve(s, *cases)` (the fork
  pruned to the declared cases, closed world named), `agree(*reads)` (the
  second reading) and `resolve_unsure(s, unsure)` (the unsure-set stage).
  `classify` is unchanged: it still refuses the deep hole, because the
  closed-world assumption is a choice the caller makes by calling `resolve`.
* **`tools carried-fork`** re-takes every figure of §3;
  `tests/test_carried_fork.py` holds them.

## 5. D15, said plainly

* **Refusal → derivation for the deep hole: moved, conditionally.** Where the
  caller declares the cases, 89.9 % of deep-hole reads that `classify`
  refused are answered with 0 wrong. The condition is the closed world, and
  its price is measured (§3.1).
* **Address: moved.** X1's second reading is reachable from a question.
* **Refusal: sharpened.** The unsure-set stage turns a refusal into a proof
  that five candidates are impossible.
* **Not moved:** the soft escalation. It is an estimate, it missed its mark,
  and it is labelled as an estimate everywhere it appears.

## 6. What would earn the next round

1. **A declared composition mark.** §3.1's post-hoc composition (context,
   then a second reading) should be declared and measured on a fresh probe
   before it is scored.
2. **A second view of one carrier at runtime.** The second reading is wired
   in the dialect, but only a caller who holds two reads can use it; a
   runtime path that produces two independent views of one register value
   (two rungs of the deep-hole ladder, or two frames of the migration layer)
   is what would make it routine.
3. **A soft channel worth escalating.** K4b's ensemble made every wrong bit
   weak but let right bits be just as weak; a channel whose reliabilities
   come from the machine's own readings, rather than a declared formula, is
   the honest test of whether the Leech lift adds information.
