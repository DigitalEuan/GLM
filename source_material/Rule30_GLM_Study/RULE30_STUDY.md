# Rule 30 through the GLM — the journey, the best findings, and the package

## Tier 0 — the coarse read

**Question.** What did the Rule 30 study establish about Wolfram's three prize problems, and what does it hand on to the GLM?

**Verdict.** All three prize problems are still open; the study turned every informal claim into an exact statement, proved the true ones, refuted the false ones, narrowed each problem to named missing theorems, and leaves the GLM a machine-checked reasoning toolkit.

**Deciding figure.** 428 ledger rows (259 FORMAL, 67 CERT, 9 EXH, 79 EMP, 4 DEF, 9 OPEN, 1 GLM) over 160 Lean files with no unfinished proof and no added axiom; 3 of 3 prize problems open.

**Recomputed by.** (hand-written argument; nothing to recompute)

*Tier 0 is a coarse read of what follows, never a claim of its own: the verdict and the figure above are grounded in the body below, and `tools/tier0_check.py` (or the GLM's corpus check, after a merge) fails if they stop being.*

*Last altered 27 October 2026 (Round 49: the journey written up, the package tidied and prepared for the GLM).*

This is the one document to read first. It records how the study went (§2), keeps the best of
what it found (§3), says where everything is (§4), answers whether the package can be merged into
the GLM (§5, details in [`MERGE_INTO_GLM.md`](MERGE_INTO_GLM.md)), prepares the move to YAML
study documents (§6) and lists what is left (§7). A machine-readable copy of all of it is in
[`study/`](study/README.md).

**Authors.** E. R. A. Craig — study, concept, GLM/UBP framework (project owner). The first seven
rounds were computed with Z.ai and translated with Qwen.ai. Aristotle by Harmonic — Lean 4
formalisation, verification and exact computation (Lean Rounds 1–49).

---

## 1. What the study is

**The object.** Rule 30 updates each cell from its left, centre and right neighbours as
`new = L xor (C or R)`. Started from one black cell (the *seed*), its centre column
`a(0), a(1), a(2), …` is OEIS A051023 (`Basic.lean`, checked against OEIS by `centerCol_first_30`).

**The three questions** (Wolfram, 2019), stated in Lean as `Prop`s, never as axioms:

| | Question | Lean statement | Status |
|---|---|---|---|
| P1 | Is the centre column never eventually periodic? | `Problem1` (`Prizes.lean`) | open; period 1 excluded |
| P2 | Does the frequency of black cells tend to 1/2? | `Problem2` (`Prizes.lean`) | open |
| P3 | Does computing `a(n)` need effort growing with `n`? | `Problem3`, `Problem3Eventual` (`MachineModel.lean`, `Problem3Quantifiers.lean`) | open |

**The GLM frame.** The study reads Rule 30 through the GLM's vocabulary: the *wobble*
(delta-sigma accumulator `D(N) = #black − #white` among the first `N` cells), the *observer `Y`*
(where it reads from and which way it faces), the *wheel* (all 256 elementary rules, Rule 30 as one
spoke), the *theorem wheel* (statements, proved implications and proved non-implications), and,
later, the *hypothesis engine*, *gates*, *layers* and *escalation*.

**Evidence classes**, used in every document and in the ledger
[`claims.csv`](RequestProject/GLM/Rule30/claims.csv):

| Class | Meaning |
|---|---|
| FORMAL | Lean proof for all parameters, standard axioms only (`propext`, `Classical.choice`, `Quot.sound`) |
| CERT / EXH | exact finite check in Lean (`native_decide`, which also trusts Lean's compiler); a theorem about the stated range only |
| EMP | computed outside Lean (exact-arithmetic scripts); evidence, not a theorem |
| DEF | definition, diagnostic or informal argument |
| OPEN | stated as a Lean `Prop`, not proved |

**Standing rules** (from [`PROJECT_DIRECTIVE.md`](RequestProject/GLM/Rule30/PROJECT_DIRECTIVE.md)):
every claim carries its class; open status lives in a `Prop`, never an `axiom`; no finite range
decides P1 or P2 (`no_finite_certificate_problem1/2`); facts about the map from *all* rows cannot by
themselves give non-periodicity for every row, because the all-white row shares them (error E2), so a
proof must use the seed; a blocked implication blocks only that implication; GLM benchmarks keep
development and held-out sets apart and report right, wrong and refused; exact arithmetic only (no
floating point, randomness or hashing inside a computation).

---

## 2. The journey

### 2.1 Before Lean: the owner's seven rounds

The study began as a seven-round computational study by the owner (computed with Z.ai, translated
with Qwen.ai): a bit-packed engine verified against OEIS, 10⁶ centre cells, ten statistical lenses,
GLM substrate tests (Golay, hexacode, Leech), and full ANF polynomials up to `n = 6`. It ended with
**three structural invariants, one per problem**, each tied to a "regime of the wobble":
cone separation (Boolean regime, P1), right-cone weight `+2` per step (P3), and wobble boundedness
`|D(n)| = O(√n)` (random-walk regime, P2). The owner's unifying insight was that Boolean, sine and
cosine are not things but *regimes of the wobble*. The three problems were written in Lean as
`axiom`s, and `VERIFICATION_DIRECTIVE.md` (24 October 2026) asked for the targets to be checked:
T1 cone separation preserved, T2 wobble bound ⇒ normality, T3 weight growth "unlocking" P1 and P3.

### 2.2 Lean Rounds 1–3: checking the claims

* Two of the original axioms were **inconsistent** (they prove `False`): the wobble bounds
  quantified over every sequence (`not_forall_sqrt_bound`) and the complexity axiom had an
  unconstrained cost (`unconstrained_cost_refutes`). All three problems became `Prop`s.
* **T1 proved** for every `n`, row and cell (`booleanDerivative_left_edge`). **T2 proved** in the form
  "`|D(n)| ≤ C√n` eventually implies frequency 1/2" (`hasFrequencyHalf_of_sqrt_bound`; the study's
  "normality" means frequency 1/2 here, not full normality of every block), with the exact
  equivalent `D(n) = o(n)` (`hasFrequencyHalf_iff`, `problem2_iff_wobble`).
* The wobble constant `C = 2` was **refuted** at `N = 1462`; the best constant to 10⁶ is `2.651…`, and
  the law of the iterated logarithm predicts that no constant works, so the target was dropped.
* "Degree / cone / weight growth ⇒ P1 and P3" is **not a valid inference**: these are properties of
  the map from all rows, which the all-white row (periodic centre) shares
  (`map_properties_cannot_decide_periodicity`, error E2). "The 32-state window forces `+2` degree"
  is refuted by Rule 180 (`phaseSpace_does_not_determine_growth`, E3).
* First partial result on P1: two adjacent columns are never both eventually periodic
  (`seed_not_both_adjacent_columns_periodic`, the result usually credited to E. Jen, 1986).
* The ledger and the **error record** (E1–E7) were started; they remain the project's memory.

### 2.3 Rounds 4–12: widening the lens

* **Measure theory** (Round 4): Rule 30 preserves the fair-coin measure, and P1 and P2 hold for
  almost every initial row (`evolve_measurePreserving`, `ae_problems_one_and_two`) — but not, by that
  argument, for the seed. Where measure theory stops is made exact (`ColumnInverse.lean`).
* **Finite-state observers** (Round 5): P1 ⟺ every finite-state observer errs infinitely often;
  a seed-typicality target implies P1 and P2. **P3** gets an exact machine model (Turing machines
  reading `n` in binary).
* **Waves, boundaries, rule spaces, the parity count** (Round 6), the owner's feedback made exact.
* **Period 1 is excluded** and **at most one column is eventually periodic** (Round 7:
  `centerCol_not_eventually_constant`, `seed_at_most_one_periodic_column`).
* **The degree formula `deg a(n) = 2n − 1` is proved for every `n ≥ 2`** (Round 8,
  `topMonomialConjecture_holds`, `center_anfDegree_eq`, through an involution behind an odd count;
  at `n = 1` the degree is 2, `anfDegree_one`).
* **The whole light cone is essential** for every `t` (Round 9, `wholeConeDependence_holds`), and
  the 256 elementary rules become the GLM's *wheel* carrier.
* **The GLM reads Rule 30 step by step** (Round 10): inducing a wheel is sound and complete
  (`WheelInduction.lean`); what rows and columns reveal to an observer (`Observer.lean`).
* **The right edge and off-centre observers** (Round 11); **reads of the wobble** (Round 12): the
  strobe lens gives the weakest sufficient target for P1 and P2 found so far, `SeedAPBalanced` (every
  arithmetic progression of the centre column has frequency 1/2,
  `problems_one_and_two_of_seed_apBalanced`); for general sequences it is strictly weaker than
  finite-state typicality (`frontier_weakest_target_strictly_weaker`).

### 2.4 Rounds 13–20: what a proof would take

* **The stack lift** (Round 13): left-white rows are closed under the rule; "no column of any
  left-white row is eventually `p`-periodic, for every `p`" implies P1, and is equivalent to run
  bounds (`problem1_of_leftWhiteAperiodicAll`, `LeftWhiteCompactness.lean`); period 1 is proved.
* The **chemistry lab**: no conserved window quantity of range `≤ 6` in the seed run.
* **Shortcut paths** (Round 14) and **aperiodic-tiling ideas** (Round 15) turned out to be exact
  restatements; the period-2 forcing lemma reduces period 2 to one half-speed sequence.
* **Weight growth closed** (Round 16): the top-degree monomial is unique for `n ≥ 3`, weight
  `2n − 2`. Run-bound certificates for periods 2–6 (Rounds 16–19).
* The owner's geometric questions — spinning triangles and pyramids, spin as multiplication,
  quaternions, the triangle as the side view of a funnel (Rounds 17, 19) — answered exactly; they
  are geometry, and do not touch P1–P3.
* **The `C·R` injector** (Round 18): the study's odd-parity claim for the top monomial is **proved**
  (every `n ≥ 1`), but the seed's diagram is the degree-one slice of the ANF and evolves on its own:
  a family of maps whose ANF coefficients of degree `≥ 2` all equal Rule 30's can have a constant
  seed column, so those coefficients alone cannot imply P1 (error E8,
  `injector_lock_compatible_with_periodicity`). This blocks that one implication; it does not rule
  out a further bridge that also uses the seed's actual evolution.
* **Audit** (Round 20): [`AUDIT.md`](RequestProject/GLM/Rule30/AUDIT.md) and `Frontier.lean`, which
  re-checks the whole frontier in six theorems.

### 2.5 Rounds 21–27: the half-line machine

The decisive reframing of P1. **If a column is periodic, the cells to its left form a deterministic
machine driven by the column, and Rule 30 hands that machine a test at every black time of the
column** (`col_black_forces_left`). "Every such machine eventually fails its test, for every period"
implies P1 (`problem1_of_halfLineDies`); no cell to the right is involved.

* Round 22: the first `d − 1` tests are **exactly independent** — exactly `2^(k − blacks k)` codes
  survive to time `k`, for every drive (`survivors_card`); a sound prefix search certifies further.
* Round 23 (the owner's power-series ladder): two new equivalent forms of P1 — unbounded `GF(2)`
  linear complexity (`problem1_iff_lcUnbounded`) and Morse–Hedlund complexity
  (`problem1_iff_complexity`) — and the exact counting law; the draft's edge cases were false (E9).
* Round 24: how the XOR is computed changes nothing (`implementation_invariance`); replacing the OR
  by a gate that is not of OR type makes the centre column eventually periodic
  (`inner_alternative_periodic`), which leaves the four OR-type wheels 30, 45, 75, 135 open;
  the counting law holds for every left-permutive wheel (`runCountW_law`), and putting AND or OR in
  place of the XOR breaks it (`outer_and_breaks_law`, `outer_or_breaks_law`, single counterexamples);
  Kronecker's converse (`problem1IffHankelInfinitelyOften`).
* Round 25 (the owner's "tuning by ear"): pruned directed search is sound and permanent, a family
  locks in iff the true law is in it, no finite listening confirms (`no_finite_confirmation`), and
  P1 is equivalent to the periodic tuning loop never settling (`problem1_iff_tuneCost_unbounded`).
* Round 26: the **conjecture loop** tunes *statements*: it found that the tuning excess is exactly
  the longest echo, and proposed `AmortizedHalving p c e`, which implies `HalfLineDies p`.
* Round 27: the period-2 machine analysed as a machine: four proof routes each proved to give the
  rung; eight declared progress measures refuted; `AmortizedHalving 2 4 1` is the surviving uniform
  candidate (smallest unresolved case `d = 13`).

### 2.6 Rounds 28–30: the GLM made operational

* The GLM's theorem wheel reads the whole ledger as carriers ([`glm/r28_wheel.json`](RequestProject/GLM/Rule30/glm/README.md)).
* **Local-rule induction** for any grid and any reader is proved sound and complete
  (`LocalRuleInduction.lean`), and runs as the GLM's ARC fallback: it answers only when the
  demonstrations determine the answer.
* **The stepwise planner** (Round 29, `PlanSearch.lean`): merged breadth-first search loses no plan;
  the planner answers only when every cheapest consistent plan agrees; it is correct when the truth
  is a cheapest explanation and can be wrong otherwise (`planner_correct`, `minAgree_needs_occam`);
  disagreeing plans are separated by one observation (`separating_example_refutes`).
* **One pipeline** (Round 30, `Pipeline.lean`): plan → ask → gate → statements, with the honest
  negative `gate_can_drop_truth`; the same planner over Rule 30 statements produced a certified
  frontier of 30 sharp points.
* Measured (EMP): stored ARC tasks 0 → 1 → 10 of 50 right with 0 wrong; held-out multi-step puzzles
  12 → 96 of 132 right with 0 wrong; fresh held-out 56 → 96 of 132 (4 wrong), 106 with at most five
  questions asked.

### 2.7 Rounds 31–37: the observer's viewpoints

* **Sideways** (Round 31): the observer standing on the periodic column and reading outwards;
  `HalfLineDies p` is exactly "no admissible first column reconstructs a finite non-empty row"
  (`halfLineDies_iff_sideways`); finite-window quotients cannot work. Exact arithmetic everywhere.
* **`M₂₄`** (Round 32): orbits of seed patterns; only rotations commute with Rule 30
  (`commutes_iff_rot`), at most 12 symmetries are shared (`shared_card_le_twelve`), and one orbit holds
  seeds with different futures — use `M₂₄` to enumerate, never as evidence.
* **The observer's clock** (Rounds 33–35): count tests, not steps. No uniform slack works
  (`not_testCountBound`), a slack per period gives the rung; per-period statements pass to divisors
  (`halfLineDies_of_dvd`); a slack for the clock started one step later gives a slack larger by 2
  for the original start (`testSlack_of_shift`); a verified checker twice as fast; black runs are
  single window reads.
* **The drive wheel** (Round 36): only the primitive turns (hubs, Lyndon words) matter
  (`halfLineDies_iff_wheel`); 70 hubs replace 502 words up to period 8.
* **The cost of a turn and the best phase** (Round 37): the price of changing the read phase is
  exact (`testSlack_phase_transfer`), and one phase per wheel suffices (`testCountLinear_of_phases`) —
  the owner's perspective idea as an exact rule. The GLM, indexed by hubs, went from 0/11 to 11/11
  on the frozen consultation questions (EMP).

### 2.8 Rounds 38–42: the hypothesis engine

* The owner's v4 engine returned "passed" on every input; the rebuilt engine proposes
  **statements**, refutes them on held-out exact data, mines laws from counterexamples and predicts.
* It found the **period law of the left diagonals** (proved for every diagonal: `ldiag_doubles`,
  `first_difference_after_white`), predicted the refutation of "period ≤ 16" at `D = 87867`
  (then certified in Lean), and proposed the white-diagonal criterion (`white_iff_coincide`).
* From injectivity plus pigeonhole: **Rule 30 has infinitely many eventually white left diagonals**
  (`ldiag_infinitely_many_white`), and the periods are unbounded iff odd-parity white diagonals keep
  occurring (`ldiag_periods_unbounded_iff`). Settling times grow at most linearly in `D`: for the
  diagonals `D < N` there is a common period `2^m` reached by time `1 + D·2^m`
  (`ldiag_perFrom_linear`).
* Off Rule 30, the same core ran on eight problems with known answers; every verdict is checked in
  Lean (`HypothesisEngine/Benchmarks.lean`).
* The owner's v10 dialogue and v13 TAX tool were checked: two fixed sentences were wrong
  (`transient_read_does_not_imply_aperiodic`; Thue–Morse is aperiodic yet automatic,
  `aperiodic_but_automatic`), and the TAX route to the doublings is closed (`tax_conserved_at_doubling`).

### 2.9 Rounds 43–47: the GLM's architecture checked

* The owner's **escalation-boundaries sketch** was checked statement by statement and rebuilt
  ([`Escalation/MASTER_VIEW.md`](RequestProject/GLM/Escalation/MASTER_VIEW.md), corrected edition in
  [`GLM_Escalation_Boundaries_Exploration_CORRECTED.md`](RequestProject/GLM/Escalation/GLM_Escalation_Boundaries_Exploration_CORRECTED.md)):
  the state is (carrier, layer), the snap is the only layer-changer, escalation is a
  least-resolving-layer search (all kept and proved); the 2/4/8/144/256 modulus table, the half-unit
  example, "a fixed syndrome table is stable" and "roll back on failure" are corrected; the
  Niemeier list misses `E₆⁴` (`rank_cox_classification`).
* The **needs wheel** (Round 44), the **gate loop** of engine v17 (Round 45: typed rollback, cascade
  soundness, `rollback_sound`, `cascade_sound`) and the **wheel contract** of engine v18 (Round 46:
  only the KNOWS ring asserts, `merge_sound`). Measured: on 24 statements with fixed answers, v16
  scored 4 right, 5 wrong, 15 overclaims; v17 scored 24 right (EMP; the ledger and the ground truth
  share sources).
* **The 2-adic layer tower** (Round 47, the owner's layered, p-adic-like idea): **P1 is equivalent
  to the 2-adic irrationality of the centre column** (`problem1_iff_padic_irrational`); the
  denominator of a layer relation fixes the period, the numerator bounds the preperiod
  (`period_of_dvd`). The full `M₂₄` census (49 orbits, `census_49`).

### 2.10 Round 48: triangles and lines

From the owner's observations: every white run is the top of a white triangle fixed by its row and
born from a black run in the row before (`white_triangle`, `white_run_parent`); a black line goes
on left-down against one white cell but right-down only against two (`leftDown_continues_iff`,
`rightDown_continues_iff`); infinitely many left-down black lines never end, no right-down line
inside the pattern does (`ldiag_infinitely_many_black`, `rdiag_not_eventuallyBlack`); the pattern
prints from the right side in (`column_from_right`), and the right edge repeats in bands of length
`2^k` with triangles of every size (`arbitrarily_large_right_triangles`).

### 2.11 Round 49: the tidy-up

This document; [`MERGE_INTO_GLM.md`](MERGE_INTO_GLM.md) and the merge tool; a single
non-colliding package root `RequestProject/GLM/Rule30Study.lean`; the machine-readable copy in
[`study/`](study/README.md); the YAML parser/creator for study documents
([`tools/STUDY_YAML.md`](tools/STUDY_YAML.md)); a tier-0 block at the top of every document of the
package, so that each one meets the GLM's corpus contract and reads as a study at its coarsest
level; a short front-door `README.md` (its old round summaries moved, unchanged, to `HISTORY.md`
Appendix D). No mathematical result was added or changed.

### 2.12 Turning points and lessons

**Turning points.** (1) Replacing the axioms by `Prop`s (Round 1): the study stopped assuming what
it wanted. (2) "Seed, not map" (E2): it redirected everything towards facts about the specific seed.
(3) The half-line machine (Round 21): P1 became a one-sided statement with a built-in test.
(4) Making the GLM measurable (Round 28): capability claims became held-out scores. (5) The
hypothesis engine (Round 38): the first new theorems proposed by the machine itself.

**The error record** (institutional memory; full table in
[`HISTORY.md`](RequestProject/GLM/Rule30/HISTORY.md), Round 3, Track 4, and `AUDIT.md` §2.3):

| | Error | Correction |
|---|---|---|
| E1 | inconsistent axioms | `Prop`s; `not_forall_sqrt_bound`, `unconstrained_cost_refutes` |
| E2 | map vs seed | `map_properties_cannot_decide_periodicity` |
| E3 | local-to-global degree | `phaseSpace_does_not_determine_growth` (Rule 180) |
| E4 | combinatorial bulk | reduced to one parity count |
| E5 | `C = 2` wobble constant | refuted at `N = 1462` |
| E6 | finite certificate ⇒ prize | `no_finite_certificate_problem1/2` |
| E7 | two top monomials at `n = 2` | uniqueness holds from `n = 3` |
| E8 | top-to-bottom flow (the ANF coefficients of degree `≥ 2` alone are compatible with a periodic seed column) | `injector_lock_compatible_with_periodicity` |
| E9 | finite data inside an infinite characterisation | `draftComplexityForm_iff`, `runCountTwoLawDraft_false` |

**Lessons for the GLM.** State before you search: a `Prop` with its class is worth more than a
paragraph. Refute on held-out data before asserting, and escalate the range before believing.
Credit honestly: supplied candidates are not generated ones. A blocked implication blocks only
itself. Measure every capability on a held-out set with right, wrong and refused counted. Read
from the side that can refute (for Rule 30, the left). Keep arithmetic exact.

---

## 3. The best findings

### 3.1 The results to remember

| # | Result | Lean | Class |
|---|---|---|---|
| 1 | The three problems as exact `Prop`s; two of the original axioms were inconsistent | `Prizes.lean`, `not_forall_sqrt_bound` | FORMAL |
| 2 | No column of the seed pattern is eventually constant, and at most one column is eventually periodic | `centerCol_not_eventually_constant`, `seed_at_most_one_periodic_column` | FORMAL |
| 3 | P1 needs only the left half-line: if every driven half-line machine fails its test, P1 holds | `problem1_of_halfLineDies` | FORMAL |
| 4 | P1 ⟺ unbounded `GF(2)` linear complexity ⟺ Morse–Hedlund ⟺ 2-adic irrationality of the centre column | `problem1_iff_lcUnbounded`, `problem1_iff_complexity`, `problem1_iff_padic_irrational` | FORMAL |
| 5 | P2 ⟺ `D(n) = o(n)`; a `√n` bound is sufficient but `C = 2` is false | `problem2_iff_wobble`, `hasFrequencyHalf_of_sqrt_bound` | FORMAL (+ CERT) |
| 6 | `SeedAPBalanced` — every arithmetic progression balanced — implies P1 and P2 | `problems_one_and_two_of_seed_apBalanced` | FORMAL |
| 7 | P1 and P2 hold for almost every initial row | `ae_problems_one_and_two` | FORMAL |
| 8 | ANF degree `2n − 1` for every `n ≥ 2` (degree 2 at `n = 1`); the top monomial is unique for every `n ≥ 3` (two at `n = 2`), weight `2n − 2`; the whole light cone matters for every `t` | `center_anfDegree_eq`, `anfDegree_one`, `topMonomial_unique`, `topDegree_weight_growth`, `wholeConeDependence_holds` | FORMAL |
| 9 | A property of the maps alone (degree, weight, cone) cannot imply that every starting row has a non-periodic centre column: the all-white row shares the maps and has a periodic one (map vs seed) | `map_properties_cannot_decide_periodicity` | FORMAL |
| 10 | Infinitely many eventually white left diagonals; the left-diagonal period law | `ldiag_infinitely_many_white`, `ldiag_doubles` | FORMAL |
| 11 | No eventual period `p ≤ 64` with preperiod `≤ 30000`; not a fraction `r/q` with `q ∣ 2^p − 1`, `p ≤ 500`, `|r| < 2^500` | `centre_no_short_period_30000`, `centerCol_not_fraction_500` | CERT |
| 12 | The observer's arrow `−sign D(N)` is exactly the local direction towards 1/2; its sign pattern does not decide frequency 1/2 either way (a balanced sequence can keep `D(N) > 0` for all `N ≥ 1`, and an unbalanced one can change sign infinitely often) | `deviation_decreases_iff`, `arrow_independent_of_frequency` | FORMAL |

### 3.2 Problem 1 — non-periodicity

* **Proved partial results.** Period 1 excluded; at most one periodic column; adjacent columns never
  both periodic; every right diagonal is periodic (period `2^D`) and every left diagonal eventually
  periodic (`rdiag_periodic`, `ldiag_eventually_periodic`); period 1 of the half-line target
  (`halfLineDies_one_sideways`).
* **Exact reformulations** (each `↔`, both directions proved): finite-state observers; echoes;
  strobes; shortcut rules; linear complexity, Hankel determinants infinitely often, Morse–Hedlund;
  the periodic tuning loop never settles; the 2-adic tower; `HalfLineDies p` sideways and on the
  wheel of hubs.
* **Sufficient targets, narrowest first** (`Frontier.lean`, `frontier_sufficient_targets`):
  `HalfLineDies p` for all `p` (one statement, `WheelDies`); for period 2 the narrowest forms are
  `AmortizedHalving 2 4 1` (certified `d ≤ 12`) and, from the best phase, `TestSlack (driveN 2 2) 3`
  (certified `d ≤ 40`); `TuneExcessLog` (certified `n ≤ 131072`, sharp); `SeedAPBalanced`.
* **Certified ranges** (CERT): run bounds and half-line certificates for periods 2–8; least
  observer-clock slacks 5, 8, 7 for periods 2, 3, 4 on `d ≤ 42, 32, 32`; linear complexity
  `≥ 10000` on 19999 bits; no small period or fraction (item 11 above).
* **Blocked routes.** Each item is proved insufficient on its own, or refuted as stated or on the
  stated range. A blocked implication blocks only that implication, not a later bridge from the same
  facts (`AUDIT.md` §5.4):
  * properties of the maps alone (degree, weight, cone growth) do not imply non-periodicity for
    every starting row (E2);
  * the 32-state window does not determine degree growth (E3, Rule 180);
  * the ANF coefficients of degree `≥ 2` alone are compatible with a periodic seed column (E8);
  * no finite prefix decides P1 or P2 (E6);
  * the diagonal structure (white negative diagonals, the triangular recursion, periods `2^D`) also
    holds for right-white rows whose centre column is periodic or has frequency 1/3, so it does not
    imply P1 or P2 by itself (`diagonal_coupling_does_not_decide_problem1/2`);
  * there is no conserved window quantity of range `≤ 6` (checked at those ranges only);
  * rows with infinitely many black cells survive every drive, so a finite-window quotient of the
    half-line machine cannot prove `HalfLineDies p` (`infinite_row_survives`);
  * all 8 declared progress measures are refuted for windows up to 20, and width steps up to 17;
  * the uniform inner-survivor form is refuted (`not_innerFollows`).

### 3.3 Problem 2 — frequency 1/2

* Frequency 1/2 ⟺ `D(n)/n → 0` (`hasFrequencyHalf_iff`); any bound `|D(n)| ≤ g(n)` with
  `g(n)/n → 0` suffices.
* `|D(N)|/√N` reaches `2.651…` at `N = 24979` and stays below it up to 10⁶ (CERT); the √n target is
  probably false for a random-looking sequence (iterated logarithm) and was dropped.
* Holds for almost every row (measure theory), not yet for the seed; `SeedAPBalanced` (every stride
  and every phase) is the weakest sufficient seed statement found so far, and even the balance of a
  single stride's phases is open.
* A right-white row can have centre frequency 1/3, so "right edge white ⇒ balance" is false.

### 3.4 Problem 3 — complexity

* Stated exactly for Turing machines reading `n` in binary (`Problem3`, `Problem3Eventual`,
  `problem3_of_eventual`).
* `a(t)(0)` depends on all `2t + 1` cells and every circuit for that map has at least `t` gates
  (`circuit_size_ge_of_wholeCone`) — but that is a different function from `n ↦ a(n)`.
* P1 alone would not settle P3: an aperiodic sequence can be computed by a two-state automaton
  reading `n` in binary (Thue–Morse, `aperiodic_but_automatic`).
* No sufficient statement is declared: no known method gives such lower bounds for one explicit
  sequence on a uniform machine model.

### 3.5 The observer, the wobble and the arrow (the owner's perspective idea)

The owner asked whether the wobble could define *perspective* — which way the observer `Y` is
looking from and towards, an arrow telling the GLM which way a run is converging. Where it stands:

* **The arrow is exact as a local direction** (`deviation_decreases_iff`), but **its sign pattern
  does not decide the limit** either way (`arrow_independent_of_frequency`): use it to steer, never
  to stop. Rule 30's centre column follows it at 79955 of 159703 steps — no usable bias (EMP).
* **Information flows to the left.** Two adjacent columns determine every column to their left
  (`columns_determine_left`), and each cell is computed from the two cells to its right in the same
  row and the cell below-right in the next row (`column_from_right`): the pattern prints from the
  right side in. Rule 30 is not right-permutive (`not_rightPermutive_thirty`), so this
  reconstruction does not run the other way.
* **The refutation side is the left.** At every black time of a column, the column's next value fixes
  the cell to its left (`col_black_forces_left`); for a proposed periodic column this is where the
  proposal is tested, and it drives the whole half-line programme.
* **The compass.** Rule 30's chirality is visible off the axis, but the centre column cannot tell
  Rule 30 from its mirror Rule 86 (`centre_column_class`).
* **The best read position.** Changing the read phase changes the measured cost by an exact amount,
  and each wheel has a best phase (`testSlack_phase_transfer`, `testCountLinear_of_phases`).
* **An arrow at the layer level.** Escalation-only snaps make the layer non-decreasing and eventually
  constant (`Machine.layer_monotone`); the gate loop reads ranges in increasing order
  (`reads_sorted`); on the 2-adic tower the carry is the observer's state between layers: for a
  rational column it eventually stays in `[−|q|, |q|]` (`rational_carry_bounded`), the finite-state
  machine behind the column's periodicity (Round 47).

### 3.6 For the GLM's reasoning

| Capability | What is proved | Lean |
|---|---|---|
| Wheel induction / local-rule induction | answer iff every needed neighbourhood was seen; a clash refutes the reader | `WheelInduction.lean`, `answer_determined_iff_covered`, `clash_refutes` |
| Stepwise planner | merged search loses nothing; correct under the Occam premise and not without it; the separating example | `layer_complete`, `planner_correct`, `minAgree_needs_occam`, `separating_example_refutes` |
| Pipeline | ask loop correct; the Occam gate can fix and can drop the truth | `askLoop_correct`, `gate_can_drop_truth` |
| Tuning by ear / conjecture loop | sound permanent pruning; lock-in iff the law is in the family; no finite confirmation; analogy is not proof | `TuningByEar.lean`, `ConjectureLoop.lean` |
| Needs wheel | sound provisions never lose a right answer or add a wrong one | `answer_right_of_right` |
| Gate loop (v17) | layered reads, escalate before assert, typed rollback as a least fixpoint, cascade soundness | `cascade_sound`, `rollback_sound` |
| Wheel contract (v18) | only KNOWS asserts; a turn of two sound wheels is sound | `merge_sound` |
| Escalation | escalate is correct and minimal; no complete lattice decoder is continuous | `escalate_spec`, `no_continuous_leader` |

### 3.7 Side results in mathematics

The 23 Niemeier root systems as the ADE systems of rank 24 with equal Coxeter numbers
(`rank_cox_classification`); the GLM's Golay decoder: one codeword within 3 or exactly six at 4
(`golay_decoding_dichotomy`); Leech residues mod 8, 144 and 256 coincide; the 49 `M₂₄` orbits of
24-cell patterns (`census_49`); octad, sextet and trio stabiliser orbits; Kronecker's converse for
`GF(2)` sequences; the counting law of the XOR; the parity law of Rule 30.

### 3.8 What was corrected

| Claim | Outcome |
|---|---|
| The problems as `axiom`s | two inconsistent; replaced by `Prop`s |
| `|D(n)| ≤ 2√n` | false at `N = 1462` |
| Weight growth unlocks P1 and P3 | invalid inference (E2) |
| 32-state window forces degree growth | false (Rule 180) |
| Top monomial unique for every `n` | false at `n = 2`; true from `n = 3` |
| "Read inside the transient ⇒ aperiodic" (v10) | does not follow |
| "Aperiodic ⇒ no finite automaton" (v10) | false for automata reading `n` |
| TAX conservation `c ∈ {0, a, b}`; "a defect is necessary for a jump" (v13) | both false |
| Moduli 2/4/8/144/256 refine each other; mod-8 filter resolves `1/2 + 1/2` | false |
| 23 Niemeier systems listed in the sketch | 22 listed, `E₆⁴` missing |
| Every left-down line is endless; no triangles near the left edge | not every one: infinitely many are endless (`ldiag_infinitely_many_black`), and most observed ones break early (EMP); triangles do occur but stay small there: inside the first 400 left diagonals the longest white run from time 501 on is exactly 10 (CERT) |

---

## 4. How the package is organised

### 4.1 The map

```
README.md                    front door
RULE30_STUDY.md              this document (GLM study format)
MERGE_INTO_GLM.md            how to merge the package into the GLM repository
study/                       machine-readable copy (YAML): findings, rounds, modules, ledger, docs
tools/                       glm_study_yaml.py (study YAML parser/creator), merge_into_glm.py,
                             build_study_yaml.py, tier0_check.py, lean_decls.py
RequestProject/GLM/Rule30Study.lean     the single root of the package
RequestProject/GLM/Rule30.lean          root of the Rule 30 mathematics
RequestProject/GLM/Rule30/              138 Lean modules, guides, claims.csv, scripts/, glm/
RequestProject/GLM/HypothesisEngine/    10 Lean files + guide (portable engine contracts)
RequestProject/GLM/Escalation/          6 Lean files + guides (escalation boundaries)
```

Every Lean file starts with a docstring listing its results; `…Data.lean` files hold the
certificates. [`study/modules.yaml`](study/modules.yaml) lists every file with its topic, evidence
class, round and the ledger rows it backs.

### 4.2 Lean files by topic

| Topic | Files | Guide |
|---|---|---|
| Foundations | `Basic`, `Compute`, `Prizes`, `Problem3Quantifiers`, `MachineModel(Data)`, `ElementaryCA`, `Frontier` | [`Rule30/README.md`](RequestProject/GLM/Rule30/README.md) |
| P1: proved partial results | `NoConstantColumn`, `AdjacentColumns`, `OnePeriodicColumn`, `ChiralLeak`, `Diagonals`, `RightDiagonalBalance`, `ReadAngle`, `SeedBoundary` | same |
| P1: exact reformulations | `FiniteState`, `Spectral`, `RuleSpace`, `WobbleLenses(Data)`, `PowerSeriesLadder(Data)`, `HankelKronecker`, `TuningByEar(Data)`, `EchoBound`, `ShortcutNetwork(Data)`, `AdicTower`, `AdicPeriod`, `AdicTowerData` | same |
| P1: the half-line machine | `LeftWhiteLift`, `LeftWhiteCompactness`, `RunBound*`, `PeriodTwoHalfLine(Data)`, `HalfLineMachine(Data)`, `HalfLineLightCone`, `PrefixSearch(Data)`, `RunCount*`, `XorAlternatives(Data)`, `AmortizedHalving`, `ConjectureLoop(Data)`, `PostEdgeSpec`, `ProofRoutes(Data)`, `InnerSurvivorData`, `SidewaysView`, `BarrierDiagonalsData`, `TileLeads` | [`AUDIT.md`](RequestProject/GLM/Rule30/AUDIT.md) |
| P1: observer's clock, drive wheel | `TestCount*`, `TestHalving(Data)`, `SidewaysPeriodTwo`, `SlackCert*`, `DiagonalSearch(Data)`, `DiagCert*`, `BlackRunWindow`, `DriveWheel(Data)`, `TurnCost(Data)`, `OneRunFamily` | [`TEST_COUNT.md`](RequestProject/GLM/Rule30/TEST_COUNT.md), [`WHEEL.md`](RequestProject/GLM/Rule30/WHEEL.md), [`TURN_COST.md`](RequestProject/GLM/Rule30/TURN_COST.md) |
| The left side, triangles | `LeftDiagonalPeriods(Data)`, `Transients(Data)`, `WhiteDiagonals`, `Triangles(Data)` | [`HYPOTHESIS_ENGINE.md`](RequestProject/GLM/Rule30/HYPOTHESIS_ENGINE.md), [`TRIANGLES.md`](RequestProject/GLM/Rule30/TRIANGLES.md) |
| P2: wobble, arrow, measure | `Wobble`, `WobbleCertificate`, `WobbleNormalized`, `Perspective`, `ArrowIndependence`, `Ergodic`, `Invariance`, `Unpredictability`, `ColumnInverse` | [`Rule30/README.md`](RequestProject/GLM/Rule30/README.md) |
| ANF and P3 background | `ConeSeparation`, `ANF(Data)`, `DegreeData`, `ParityReduction(Data)`, `TopMonomial`, `WeightGrowth`, `PhaseSpace32`, `WholeCone`, `DiagonalCoupling`, `Injector*` | same |
| Geometry | `ConeGeometry`, `LatticeConeFraction`, `SpinSweep`, `SpinLattice`, `SpinQuaternion`, `Funnel`, `ChemistryLab` | [`HISTORY.md`](RequestProject/GLM/Rule30/HISTORY.md) |
| `M₂₄` and Golay | `MathieuOrbits(Data)`, `MathieuRule30Data`, `MathieuCensus`, `MathieuCensusOrbits`, `MathieuMOG` | [`M24_ORBITS.md`](RequestProject/GLM/Rule30/M24_ORBITS.md) |
| GLM reasoning | `Observer`, `WheelInduction`, `LocalRuleInduction`, `PlanSearch`, `Pipeline(Data)` | [`glm/README.md`](RequestProject/GLM/Rule30/glm/README.md) |
| Hypothesis Engine | `HypothesisEngine/*` | [`HypothesisEngine/README.md`](RequestProject/GLM/HypothesisEngine/README.md) |
| Escalation | `Escalation/*` | [`Escalation/README.md`](RequestProject/GLM/Escalation/README.md) |

### 4.3 Which document for what

| Document | For |
|---|---|
| this file | the journey, the best findings, the map |
| [`PROJECT_DIRECTIVE.md`](RequestProject/GLM/Rule30/PROJECT_DIRECTIVE.md) | goal, rules of evidence, focus, what counts as progress |
| [`AUDIT.md`](RequestProject/GLM/Rule30/AUDIT.md) | status, missing theorems (§3), the numbered To Do list (§4) |
| [`DEVELOPMENT.md`](RequestProject/GLM/Rule30/DEVELOPMENT.md) | how to run a round: the loop, the checks, the conventions |
| [`HISTORY.md`](RequestProject/GLM/Rule30/HISTORY.md) | the detailed record of every round |
| topic guides | `TEST_COUNT.md`, `WHEEL.md`, `TURN_COST.md`, `HYPOTHESIS_ENGINE.md`, `TRIANGLES.md`, `M24_ORBITS.md`, `HypothesisEngine/README.md`, `Escalation/README.md`, `Escalation/MASTER_VIEW.md` |
| [`claims.csv`](RequestProject/GLM/Rule30/claims.csv) | the evidence ledger (also as [`study/claims.yaml`](study/claims.yaml)) |

### 4.4 The study folders (GLM-side code)

The Python side of each round lives in the owner's study tree, one folder per round:
`rule30_round6` … `rule30_round16` (probes, overlays, benchmarks of Rounds 6–16),
`rule30_round28`, `rule30_round29`, `rule30_round30`, `rule30_round33`, `rule30_round34`,
`rule30_round37` (GLM overlays with `setup_round*.sh`, benchmarks), `rule30_round38` …
`rule30_round45` (the hypothesis engine v5–v17, guards, escalation checks), and `glm_engine/`
(engine v18). Rounds 17–27 and 31–32, 35–36, 46–49 were Lean-only or kept their scripts in
`RequestProject/GLM/Rule30/scripts/`. [`study/study_folders.yaml`](study/study_folders.yaml)
lists every folder with its round, purpose and entry points. The owner's original material
(Rounds 1–7) is at the root of that tree: `README.md`, `VERIFICATION_DIRECTIVE.md`, `pdfs/`,
`scripts/`, `lean/`, `data/`, `figures/`.

### 4.5 Build and trust

```
lake build RequestProject.GLM.Rule30Study     # the whole package (also: lake build RequestProject.GLM)
python3 RequestProject/GLM/Rule30/scripts/ledger_check.py   # every ledger name exists, axioms match class
python3 tools/build_study_yaml.py check       # the YAML copy is up to date
python3 tools/tier0_check.py                  # every document keeps the GLM's tier-0 contract
```

Lean 4.28.0 and Mathlib as pinned in `lean-toolchain`, `lakefile.toml` and `lake-manifest.json`.
No unfinished proof and no added axiom anywhere. FORMAL results use only the standard axioms;
CERT results additionally trust Lean's compiler (`Lean.ofReduceBool`, `Lean.trustCompiler`), and
are kept in separate files.

---

## 5. Merging into the GLM

**Yes — the package can be merged as it is, and a tool does it.** The details and the manual
recipe are in [`MERGE_INTO_GLM.md`](MERGE_INTO_GLM.md); in short:

* **Same build.** The GLM repository (`glm_repo.zip`, snapshot of 23 October 2026) uses the same Lean
  toolchain (4.28.0), the same Mathlib commit and the same library name `RequestProject`, with its
  sources under `glm_lean/`. The package's folders drop into
  `glm_lean/RequestProject/GLM/` unchanged.
* **No clashes.** The GLM has no `Rule30/`, `HypothesisEngine/` or `Escalation/` folder. The one
  file-name collision, `RequestProject/GLM/Escalation.lean` (the GLM's own file is about escalation
  at register scale), is avoided by the new root `Rule30Study.lean`, which imports the escalation
  modules directly. All the package's declarations live under twelve namespaces
  (`GLM.Rule30`, `GLM.Escalation`, `GLM.HypothesisEngine`, `GLM.Wheel`, `GLM.GateLoop`, `GLM.Spin`,
  `GLM.PlanSearch`, `GLM.Funnel`, `GLM.Pipeline`, `GLM.LocalRule`, `GLM.NeedsWheel`,
  `GLM.LatticeCone`), and the GLM snapshot declares nothing under any of them.
* **Its gates accept it.** The GLM's axiom guard allows exactly the axioms the package uses
  (including the compiler axioms of `native_decide`); its Lean-file test needs every file imported
  by `AxiomAuditAll.lean`, which the tool adds; its hole counter now finds no `sorry` word in the
  package; and its corpus check, which requires a tier-0 block in every document that is not
  archive, is met because every document of the package now has one (`tools/tier0_check.py`
  checks this with the GLM's rules). After a merge the GLM's build, `corpus --refresh`,
  `corpus --check` and `signoff --close` are run once, because the GLM keys its measurements and
  test signatures on the Lean tree.
* **One command.** `python3 tools/merge_into_glm.py /path/to/glm_repo` checks all of this and shows
  the plan; `--apply` copies the Lean package, the documents (to `studies/RULE30_STUDY.md` and
  `studies/rule30/`) and the tools, rewrites relative links, and writes a merge report.

What the GLM gains: 154 checked Lean modules it can cite (158 Lean files with the three roots and
the axiom-footprint script); the ledger as wheel carriers; the planner, pipeline, gate-loop and
wheel contracts as specifications for its Python modules; the error record and the lessons of
§2.12 as standing rules; and the YAML tool of §6.

---

## 6. Preparing the studies for YAML

The next GLM project will turn every study document into a YAML file the GLM can find, read and
use, and will write future studies in YAML. This round prepares it:

* **A schema that matches the GLM's own model.** `glm-study/v1` has the fields of
  `glm_universal.corpus.inventory.Document`: path, title, sections with GitHub-style anchors, the
  four tier-0 fields `question`, `verdict`, `figure`, `recomputed`, links, archive flag — plus a
  lossless layer, so that YAML → Markdown reproduces the original byte for byte.
* **A parser/creator** ([`tools/glm_study_yaml.py`](tools/glm_study_yaml.py), guide
  [`tools/STUDY_YAML.md`](tools/STUDY_YAML.md)): `md2yaml`, `yaml2md` (render), `new` (a study from
  the template), `validate`, `roundtrip`, `index`, `query`, `get`. Standard library only, with its
  own YAML reader and writer; it uses PyYAML only if asked.
* **Applied here first.** Every document of this package is converted in
  [`study/docs/`](study/README.md), indexed in [`study/index.yaml`](study/index.yaml), and
  regenerated by `tools/build_study_yaml.py`. The hand-maintained files `rule30.yaml`,
  `findings.yaml` and `lessons.yaml`, and the generated `rounds.yaml`, `open_questions.yaml` and
  `study_folders.yaml`, show the shape a study's knowledge takes when it is meant to be queried
  rather than read.
* **Tested on the GLM's corpus.** The converter was run over every Markdown document of the GLM
  snapshot: all 211 (the 162 studies, the root documents including the 675 KB `MASTER_PLAN.md`,
  `archive/`, `source_material/` and ``) convert to YAML and render back byte for byte,
  PyYAML reads every emitted file as the same object, and the 2111 sections agree with the GLM's
  own document model on headings, anchors, tier 0 and links. Details in
  [`tools/STUDY_YAML.md`](tools/STUDY_YAML.md); 43 unit tests in `tools/test_glm_study_yaml.py`.

---

## 7. What this leaves open, and how to continue

**The narrowest open targets** (any one would be real progress; `AUDIT.md` §3.1):

| Target | Gives | Where it stands |
|---|---|---|
| `HalfLineDies 2` (period-2 rung), e.g. via `AmortizedHalving 2 4 1` or `TestSlack (driveN 2 2) 3` | P1 for period 2 | certified `d ≤ 12` and `d ≤ 40`; smallest unresolved case `d = 13` (To Do 1, 17, 42) |
| `HalfLineDies p` for every `p` (`WheelDies`) | P1 | `p = 1` proved; `p ≤ 8` certified on ranges (To Do 2, 39) |
| `SeedAPBalanced`: every stride `p` and every phase `r < p` of the centre column has frequency 1/2 | P1 and P2 | open even for a single stride; CERT tables to 10⁶ (To Do 5) |
| `TuneExcessLog` (any `EchoLogBound a b`) | P1 | certified `n ≤ 131072`, sharp (To Do 16) |
| a lower-bound method for one explicit sequence | P3 | none known |

**Open questions the study raised** (To Do numbers of `AUDIT.md` §4): are the left-diagonal periods
unbounded (45)? can the open bit at a white diagonal be decided from finite data (46)? run-up
universality (47) and the period-64 prediction (48); does period 4 have a finite observer-clock slack
(35)? are the white triangles near the left edge bounded (52)? The full list, with status, is
[`study/open_questions.yaml`](study/open_questions.yaml).

**How to continue.** Read [`PROJECT_DIRECTIVE.md`](RequestProject/GLM/Rule30/PROJECT_DIRECTIVE.md)
and [`DEVELOPMENT.md`](RequestProject/GLM/Rule30/DEVELOPMENT.md); pick an item from `AUDIT.md` §4;
state the target as a `Prop` first; record every claim in `claims.csv` with its class; close the
round with the checklist (build, no `sorry`, `ledger_check.py`, `build_study_yaml.py all`, a
`HISTORY.md` section). Inside the GLM, write the round's study in YAML with
`glm_study_yaml.py new` and render it with `yaml2md`.

---

## 8. What is machine-checked

All three prize problems are still open. The study narrowed each problem to named missing theorems
(§7) and leaves the GLM a machine-checked reasoning toolkit (§3.6, §5). The deciding figure of the
tier-0 block is recounted from the files by `python3 tools/build_study_yaml.py figures`: the ledger
`claims.csv` has 428 rows (259 FORMAL, 67 CERT, 9 EXH, 79 EMP, 4 DEF, 9 OPEN, 1 GLM), and the
package has 160 Lean files (`RequestProject/GLM.lean` and everything under `RequestProject/GLM/`),
none with an unfinished proof or an added axiom. (The GLM's tier-0 field `Recomputed by.` names a
Python function inside the GLM; until the figure has one there, it carries the GLM's fixed
phrase.)

Everything marked FORMAL or CERT in this document is a Lean theorem in this package, built by
`lake build RequestProject.GLM.Rule30Study`, with the Lean name given. EMP figures (benchmark
scores, measured statistics, the next white diagonal 1,420,878,968, the period-64 prediction) come
from exact-arithmetic scripts and are evidence, not theorems. Nothing in this package proves or
disproves any of the three prize problems.

## 9. Where it is reachable

* Lean: `RequestProject/GLM/Rule30Study.lean` imports everything; each topic's files are listed in
  §4.2 and in [`study/modules.yaml`](study/modules.yaml).
* Ledger: [`claims.csv`](RequestProject/GLM/Rule30/claims.csv) and
  [`study/claims.yaml`](study/claims.yaml); as GLM wheel carriers in
  [`glm/r28_wheel.json`](RequestProject/GLM/Rule30/glm/README.md).
* Queries: `python3 tools/glm_study_yaml.py query study/index.yaml --text "half-line"`.
