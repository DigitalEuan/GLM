# Rule 30 / GLM study — Audit (Round 20, updated in Rounds 21–42)

**Read `PROJECT_DIRECTIVE.md` first** for the goal, the rules and the current focus; this file is
the status. It defines what the project is, what has been tried and what came of
it, what is still missing (in the GLM's own terms), and what is left to do. The detailed results
are in `HISTORY.md` (organised by round) and the evidence ledger is `claims.csv`. The checked
summary of the frontier is the Lean file `Frontier.lean`.

**Bottom line.** All three Wolfram Rule 30 prize problems are **still open**. The project has
not solved any of them, and nothing in it claims to. What it has done is
1. turn the study's informal claims into exact statements and check them,
2. prove a set of partial results and exact reformulations,
3. prove that several proposed routes **cannot** work, and
4. narrow each problem down to a short list of precisely stated missing theorems.

**Round 21 in one line.** Problem 1 now needs only the **left half-line**: if a column is periodic,
the cells to its left form a deterministic machine driven by the column, with a built-in test, and
`problem1_of_halfLineDies` proves that "every such machine eventually fails its test, for every
period" implies Problem 1. Period 1 is proved in this frame; periods 2–6 are certified further out.
How to run the next round: `DEVELOPMENT.md`.

**Round 22 in one line.** The first `d − 1` tests of the half-line machine are **exactly**
independent: for every drive, exactly `2^(k − blacks k)` codes survive the checks before time `k`
(`survivors_card`). The open core is now precisely the tests after the edge. The same fact gives a
sound prefix search that certifies the period-2 linear target to `d = 36` (was 24).

**Round 24 in one line.** Alternatives to XOR: changing *how* the XOR is computed changes nothing
(`implementation_invariance`); changing the XOR or the OR into another gate settles the centre
column in every case except the four OR-type left-permutive wheels 30, 45, 75, 135; the counting
law is a property of the XOR alone (`runCountW_law`, `outer_runCount_law_iff`) and holds for all
times for the mirror rule 86 (`runCountW_law_right`). To Do 11 (Kronecker's converse) is done:
`problem1IffHankelInfinitelyOften`.

**Round 25 in one line.** Your "tuning by ear" loop is made exact: pruning is sound and permanent,
a finite or graded family of candidate laws locks in iff the true law is in it, and no finite
listening ever confirms a candidate (`TuningByEar.lean`). For Rule 30, Problem 1 is exactly "the
periodic tuning loop never settles" (`problem1_iff_tuneCost_unbounded`); a new sufficient target
`TuneExcessLog` is certified for `n ≤ 2000`.

**Round 26 in one line.** The loop now tunes *statements*: candidate lemmas are proposed (seeds,
analogy, junction meets, repairs of refuted shapes), tested, narrowed and looped
(`ConjectureLoop.lean`, `scripts/conjecture_loop.py`). It found that the tuning excess is exactly the
longest echo (`excess_le_iff_not_echo`), certified `TuneExcessLog` to `n ≤ 131072` and proved it sharp
(`¬ EchoLogBound 2 1`), refuted the To Do "window halving" form and two analogies, and proposed the
amortised form `AmortizedHalving p c e` (⇒ `HalfLineDies p`, certified for `(c, e) = (4, 1)`, `d ≤ 12`,
sharp slack). Periods 2 and 3 of `HalfLineDies` need only one and two drive words
(`halfLineDies_two_iff`, `halfLineDies_three_iff`).

**Round 27 in one line.** The period-2 machine, analysed as a machine (`PostEdgeSpec.lean`,
`ProofRoutes.lean`, `ProofRoutesData.lean`): its state grows by one cell per step, so no state ever
repeats and no fixed window determines the next step (cycle certificates are vacuous; the prefix
tree is the sound finite object); an inner column driven like the boundary is itself a half-line
problem whose machine never fails (`inner_alternation_bound`). Four proof routes are each proved
to give the rung; all 8 declared progress measures are refuted for windows up to 20, width steps
up to 17 are refuted, exact longest lives are certified for `d ≤ 32`, and two longest survivors
(lengths 11 and 19) are shown to share one inner survivor. `AmortizedHalving 2 4 1` remains the one
surviving uniform candidate (`Round27Open`, smallest unresolved case `d = 13`). A measured
candidate-generation harness separates supplied from generated candidates.

**Round 28 in one line.** Round 28 made the GLM operational on the package and measured the
result. The GLM's theorem wheel now reads the whole ledger as carriers and knows the Round 21–28
frontier and a Problem 3 vocabulary (To Do 6 and 8 done). Local-rule induction is proved sound and
complete for any grid and any reader (`LocalRuleInduction.lean`) and runs as the GLM's ARC
fallback. On held-out local-rule puzzles it went from 0 to 24 of 84 right, with 0 wrong; on the
50 stored ARC tasks from 0 to 1 right. Its refusal rule prevents 16 wrong ARC answers that
guessing would give. The data do not support the natural inner-survivor recursion (To Do 19) or a
constant-time forcing proof for words with long black runs (To Do 2); both findings are EMP. The
documents were reorganised (`PROJECT_DIRECTIVE.md`, a short `README.md`, `HISTORY.md`).

**Round 29 in one line.** Puzzles are now solved by a **pipeline of steps**, not one step. The GLM's
own stepwise-planner rule (a chain is licensed when every step is; answer only when every
licensed reading agrees) and its search loop (hard gate, Occam) are lifted to chains of grid steps,
run as a breadth-first search that merges equal states. `PlanSearch.lean` proves that merging loses
nothing, that agreement can be decided on the merged layer, that the answer is correct when the
truth is a cheapest explanation and can be wrong otherwise, and that the separating example always
refutes one of two disagreeing plans. Measured (EMP): held-out multi-step puzzles 12 → 96 of 132
right (one step → plans of length ≤ 2), 0 wrong; stored ARC 1 → 10 of 50 right, 0 wrong; Round 28
held-out puzzles 24 → 48 of 84 right, 0 wrong. To Do 22 is done: the uniform inner-survivor form
is refuted by a certified witness (`not_innerFollows`).


**Round 31 in one line.** The half-line machine read **sideways** (the observer standing on the
column and reading outwards): `HalfLineDies p` is exactly "no admissible first column
reconstructs a finite non-empty row" (`halfLineDies_iff_sideways`); period 1 follows in one line
(`halfLineDies_one_sideways`); infinite rows survive every drive forever, so finite-window
quotients cannot work (`infinite_row_survives`, To Do 20). To Do 3 is answered: the barrier
diagonal depends on the drive word (`barrier_depends_on_word`, exact `Lmax` for five more words to
`d = 20`). All package scripts now use exact arithmetic only.

**Round 32 in one line.** `M₂₄` applied to seed patterns (`M24_ORBITS.md`): a checked orbit tool
and the symmetry types of defect arrangements (`MathieuOrbitsData`); only rotations commute with
Rule 30 (`commutes_iff_rot`), `M₂₄` contains the one-cell turn under no labelling (`no_rot_one`),
so at most 12 symmetries are shared (`shared_card_le_twelve`, attained by `shared_card_tau0`; 2 in
the GLM labelling), and one orbit holds seeds with different futures (`octad_cycles`). No prize
problem is affected.

**Round 33 in one line.** The half-line machine on the **observer's clock** (`TEST_COUNT.md`):
count the column's reads (tests), not steps. The uniform test-count law is false
(`not_testCountBound`). The per-period law, or its counting form *halving*
(`testCountLinear_of_testHalving`), gives the rung, and for all periods it gives P1. Least slacks
on `d ≤ 22` are 5, 8, 5 for `p = 2, 3, 4`, but period 4 needs at least 7: a code of length 30
(`not_testCountLinear_four_six`), flagged first by the GLM's Occam check. Halving excess 6 is
certified for period 2 on `d ≤ 18`. Period 2 read sideways gives columns 2–5 in closed form
(`survivor_bits_period_two`). No prize problem is settled.

**Round 34 in one line.** To Do 35, taken as the GLM's `tool next` named it: an exact search finds
no period-4 word above slack 7 on `d ≤ 37` (three-black words to `d ≥ 102`, drifting down), and
Lean certifies that the least period-4 slack on `d ≤ 30` is exactly 7 (`frontier_round34`). New
FORMAL structure: per-period statements pass to divisors and refutations to multiples
(`testCountLinear_of_dvd`, `halfLineDies_of_dvd`), and starting the observer's clock later moves the
slack by at most 2 per step (`testSlack_of_shift`, the perspective reading). The GLM gained
`tool slack` and the divisor rule (consultation 1/7 → 7/7). No prize problem is settled.

**Round 35 in one line.** To Do 37 is done: a verified *diagonal search* (one anti-diagonal of the
half-line machine per node, `DiagonalSearch.lean`) replaces the prefix search, about 2–2.5× faster.
With it the observer-clock slacks are certified further (period 2: slack 5 on `d ≤ 42`; period 3:
8 on `d ≤ 32`; period 4: 7 on `d ≤ 32`, each exactly least) and turned back into run bounds for
periodic columns in **every** left-white row (`frontier_round35`). To Do 36: a black run of `r`
drive times is proved to be **one window read** — the run's `r` tests pass iff the `r` cells next
to the column show one explicit word (`blackRun_word`), so long black runs kill every code
(`dDiesBy_of_long_blackRun`). No prize problem is settled.

**Round 36 in one line.** The **drive wheel** (`WHEEL.md`): the periodic drives form one wheel —
turns (reading the column from another phase), inner wheels (divisor periods) and their
composition — and only the primitive least turns (hubs, the Lyndon words) matter:
`HalfLineDies p` ⟺ the hubs of the divisors of `p` kill (`halfLineDies_iff_wheel`), and the single
statement `WheelDies` is equivalent to all `HalfLineDies p` and implies Problem 1 (FORMAL,
`DriveWheel.lean`). Up to period 8, 70 hubs replace 502 words; one certificate covers all of them on
`d ≤ 24` and gives the per-period law for every period `≤ 8` and the first run bounds for periods 7
and 8 (`frontier_round36`). Turns are exact for dying but can raise the slack by `2(p − 1)`; the
wheel does not make anything uniform in `d`. No prize problem is settled.

**Round 38 in one line.** (`HYPOTHESIS_ENGINE.md`)
* **Hypothesis engine.** The user's v4 engine returned "passed" on all 5 known inputs; the v5 engine
  (study folder `rule30_round38/`) generates 22 hypotheses, refutes 4 on held-out data, rediscovers 7
  known facts and made one new prediction (a period-16 left diagonal fails at `D = 87867`), which Lean
  then confirmed.
* **Left-diagonal period law (FORMAL).** A left diagonal's eventual period doubles just past an
  eventually white diagonal whose outer neighbour has odd parity, and is kept when that parity is
  even (`ldiag_doubles`, `ldiag_keeps_of_even`); finitely many white diagonals force bounded periods
  (`leftDiag_periods_bounded_of_finitely_many_white`), so unbounded periods force infinitely many
  (`infinitely_many_white_of_unbounded`); seeds are forgotten except right after a white diagonal
  (`first_difference_after_white`). *(Round 39 correction: this line used to say "and conversely";
  the converse is not known. Round 39 proved infinitely many white diagonals outright, while
  unboundedness is open.)*
* **Data (CERT).** Period 8 holds below 400 and fails at 400; period 16 holds below 87867 and fails
  there; the white left diagonals below 87868 are exactly {2, 7, 28, 399, 53207, 58286, 87866}; the
  centre column reads left diagonals only inside their transients for `20 ≤ D < 20000`.

**Round 39 in one line.** (`HYPOTHESIS_ENGINE.md` §7–9, `../HypothesisEngine/README.md`)
* **New theorems the engine proposed (FORMAL).**
  * A left diagonal is eventually white iff the two diagonals outside it eventually coincide.
  * No two adjacent left diagonals are white.
  * A finite check of `4^Q + 1` diagonals closes a regime; finitely many white diagonals would make
    the left side periodic in `D`.
  * **Rule 30 has infinitely many eventually white left diagonals** (`ldiag_infinitely_many_white`).
  * The periods are unbounded iff odd-parity white diagonals keep occurring
    (`ldiag_periods_unbounded_iff`).
* **Measured (EMP).** The next white left diagonal after 87866 is 1,420,878,968 (even parity).
  Beyond it, one transient bit chooses between a first period-64 diagonal at 2,107,985,255 and
  further even whites.
* **Models refuted by the engine itself (EMP).** The random-permutation model of the regimes fails
  at `Q = 8`. "A doubling is always followed by a doubling" fails at `Q = 16`.
* **Beyond Rule 30.** On 8 problems with known answers the core caught 9 false statements, ended
  correct on 8/8 and was honest on 8/8; Lean checks every verdict. Its resultant step finds the
  52-digit counterexample of the gcd trap that no sampling reaches.
* No prize problem is settled.

**Round 37 in one line.** (`TURN_COST.md`)
* **To Do 40.** The exact cost of a turn is `m` + (tests skipped) (`testSlack_phase_transfer`).
  Some pair of phases attains it in 66 of 69 wheels.
* **The observer's best phase.** A slack at one phase per wheel suffices
  (`testCountLinear_of_phases`). Period 2 from the phase `01` with slack 3 gives the optimal
  `TestCountLinear 2 5` (`testCountLinear_two_of_phase`); this slack is certified on `d ≤ 40`.
* **To Do 39 (partly).** Every `1^(q−1)0` is a hub. Codes of length `d ≤ q − 4` fail within
  `d + 2` tests, uniformly in `q` and `d` (`oneRun_band`). The family contains period 2.
* **To Do 41.** The GLM is indexed by hubs (`tool hub`, `tool hubs`, `tool requirements`, hub-first
  `tool next`). Consultation went from 0/11 to 11/11, and the hub index is exact on 8178 words.
* No prize problem is settled.
---

## 1. What we are doing

**Goal.** Use the Geometric Language Machine (GLM) as an instrument and a reasoning frame to
study Wolfram's three Rule 30 questions, and use Lean 4 to check every claim the study makes.

**The object.** Rule 30 is `new = L xor (C or R)`, started from one black cell (`seed`). The
centre column `a(0), a(1), …` is OEIS A051023 (`centerCol`, checked against OEIS in
`Compute.lean`).

**The three questions, as they are stated in Lean** (as `Prop`s, never as axioms):

| | Question | Lean statement |
|---|---|---|
| P1 | Is the centre column never eventually periodic? | `Problem1 := ¬ EventuallyPeriodic centerCol` (`Prizes.lean`) |
| P2 | Does the frequency of black cells tend to 1/2? | `Problem2 := HasFrequencyHalf centerCol` (`Prizes.lean`) |
| P3 | Does computing `a(n)` need time growing linearly with `n`? | `Problem3` (Turing machines with binary input, `MachineModel.lean`); `Problem3Eventual` is the stronger eventual-`Ω(n)` form |

**The GLM frame.** The study reads Rule 30 through the GLM's vocabulary:
* the **wobble** (delta-sigma accumulator) `D(N) = #black − #white` among the first `N` cells;
* the **observer `Y`**: where it reads from (column, diagonal, strobe phase, moving frame) and in
  which direction (left/right, forwards/backwards);
* the **wheel**: the family of all 256 elementary rules, with Rule 30 as one spoke;
* **regimes**: bounded, random-walk and Boolean (ANF) views of the same process;
* the **theorem wheel** (GLM side, Python): statements, proved implications (spokes) and proved
  non-implications (negative controls).

**Evidence classes** (used everywhere; see `claims.csv`):
`FORMAL` (Lean proof for all parameters), `EXH` and `CERT` (finite checks in Lean, valid for the
stated range only), `EMP` (computed outside Lean, not a theorem), `DEF`, `OPEN`.

**The package** (Round 28). 86 Lean files in `RequestProject/GLM/Rule30/`, root
`RequestProject/GLM/Rule30.lean`, about 19,800 lines. It builds with **no `sorry` and no added
axioms**. Finite checks use `native_decide` and so also trust Lean's compiler. `claims.csv` has 282
rows: 186 `FORMAL`, 33 `CERT`, 9 `EXH`, 43 `EMP`, 4 `DEF`, 7 `OPEN`. `scripts/ledger_check.py`
confirms that all 628 Lean names cited in the ledger exist and that their axiom footprints match
their evidence classes.

---

## 2. What we have tried, and what came of it

### 2.1 The study's original claims (user Rounds 1–7)

| Original claim | Outcome | Where |
|---|---|---|
| Cone separation `∂a(n)(0)/∂x_{−n} = 1` | **Proved** for every `n`, row and cell | `ConeSeparation.lean` |
| Right-cone weight grows by 2 per step | **Proved** for every `n ≥ 3` (unique top monomial, weight `2n − 2`) | `WeightGrowth.lean` |
| ANF degree `deg a(n) = 2n − 1` | **Proved** for every `n ≥ 2` | `TopMonomial.lean` |
| Wobble bound ⇒ normality (`|D| ≤ C√n` ⇒ frequency 1/2) | **Proved**; the exact equivalent is `D(n) = o(n)` | `Wobble.lean`, `Prizes.lean` |
| `|D(n)| = O(√n)` for Rule 30 (with `C = 2`) | `C = 2` **refuted** at `N = 1462`; best constant to `10⁶` is `2.651…` (`N = 24979`). For a random-like sequence the law of the iterated logarithm predicts no constant works, so this target was dropped | `WobbleCertificate.lean` |
| Degree / weight / cone growth ⇒ P1 and P3 | **Not a valid inference** (error E2): these are properties of the map from *all* rows, which the all-white row (periodic centre) shares | `map_properties_cannot_decide_periodicity` |
| 32-state window forces `+2` degree per step | **Refuted**: Rule 180 has the same 32-state profile and different degree growth | `phaseSpace_does_not_determine_growth` |
| The three problems as Lean `axiom`s | Replaced by `Prop`s; two of the original axioms were **inconsistent** (proved `False`) | `Prizes.lean`, `Wobble.lean` |

### 2.2 Approaches tried in the Lean rounds, grouped by idea

Status key: **P** = gave a proved partial result, **R** = proved to be a restatement (same
difficulty), **S** = proved sufficient but open, **B** = proved blocked, **G** = geometry /
viewpoint only (exact, but does not touch P1–P3).

| Idea | What it gave | Status | Files |
|---|---|---|---|
| Measure / ergodic theory | P1 and P2 hold for almost every initial row; Rule 30 preserves the fair-coin measure | P (not for the seed) | `Ergodic`, `Invariance`, `FiniteState` |
| Finite-state observers | P1 ⟺ every finite-state observer errs infinitely often; `SeedFSTypical` ⇒ P1 ∧ P2 | R, S | `FiniteState` |
| Strobe (clock) lens | P1 ⟺ every stride has a phase that keeps changing; `SeedAPBalanced` ⇒ P1 ∧ P2, and it is strictly weaker than `SeedFSTypical` | R, S | `WobbleLenses` |
| Echo / radar lens | P1 ⟺ unbounded lag mismatches; P2 ⟺ total echo `o(N²)` | R | `Spectral` |
| Jump rules / shortcut paths, Golay network lens | P1 ⟺ no shortcut rule ever takes over; lossless lenses are equivalent to P1; no short linear/tap rules on stated ranges (CERT) | R, CERT | `ShortcutNetwork(Data)` |
| Neighbouring columns | No two distinct columns of the seed pattern are both eventually periodic; the centre column is not eventually constant | **P** | `AdjacentColumns`, `OnePeriodicColumn`, `NoConstantColumn` |
| Stack lift (every left-white row) | The lifted statement for all periods implies P1; it is equivalent to run bounds; period 1 proved | **P**, S | `LeftWhiteLift`, `LeftWhiteCompactness` |
| Period-2 forcing | An alternating column determines everything to its left from one half-speed sequence | P (reduction) | `TileLeads` |
| Run-bound certificates | Exact run bounds: period 2 to `d = 18`; periods 3–6 to `d = 12–14`; all fit linear bounds (`2d + 7`, `2d + 12`) | CERT | `RunBound*` |
| **Half-line machine (Round 21)** | A periodic column drives the half-line on its left, which must pass a test at every black time; `HalfLineDies p → LeftWhiteAperiodic p`, all `p` → P1; `HalfLineDies 1` proved; black constant runs `≤ d + 1`; machine certificates: period 2 to `d = 24`, period 3 to 20, 4 to 18, 5–6 to 16 | **P**, S, CERT | `PeriodTwoHalfLine(Data)`, `HalfLineMachine(Data)` |
| **Light cone and prefix search (Round 22)** | The machine's light cone and left-permutivity: the first `d − 1` tests read fresh code bits, so exactly `2^(k − blacks k)` codes survive to time `k` (every drive); a sound prefix search built on it; period-2 linear target certified to `d = 36`, periods 3–6 to `26 / 23 / 21 / 19` | **P**, CERT | `HalfLineLightCone`, `PrefixSearch(Data)` |
| **Power-series ladder (Round 23, your concept file)** | Two new equivalent forms of P1 for every Boolean sequence: unbounded `GF(2)` linear complexity (`problem1_iff_lcUnbounded`) and `p(n) ≥ n + 1` (Morse–Hedlund, `problem1_iff_complexity`); sufficient targets `CentreNotTwoAutomatic` and infinitely many non-zero Hankel determinants; certificates: linear complexity `≥ 10000` on 19999 bits, no eventual period with `τ + p < 10000`, 2-kernel `≥ 1023`, `p(n) = 2ⁿ` for `n ≤ 10` | R, S, CERT | `PowerSeriesLadder(Data)` |
| **Counting law (Round 23)** | Exactly `2^(d+p−1)` contexts keep the column `p`-periodic through time `T`, for `p − 1 ≤ T < d` (two-sided analogue of `survivors_card`); the draft's `T = d` endpoint and deficit monotonicity are false | **P**, CERT (refutations) | `RunCountLaw`, `PowerSeriesLadderData` |
| Diagonals (read angle) | Every right diagonal is periodic (period `2^D`); every left diagonal is eventually periodic; infinitely many right diagonals are exactly balanced | P (not the centre) | `Diagonals`, `ReadAngle`, `RightDiagonalBalance` |
| ANF injector `C·R` | Odd number of surviving pairs for the top monomial, every `n` (the study's claim, proved). But the seed's diagram is the degree-one ANF slice, which evolves on its own: no top-degree fact can reach P1 | P, **B** | `Injector`, `InjectorAnalogies` |
| Whole light cone | `a(t)(0)` depends on all `2t + 1` cells; every circuit for that map has `≥ t` gates | P (wrong function for P3) | `WholeCone` |
| Finite certificates | No finite prefix can decide P1 or P2 | **B** | `WobbleCertificate` |
| Right edge white ⇒ balance | False: there is a right-white row whose centre column has frequency 1/3 | **B** | `Unpredictability`, `RightDiagonalBalance` |
| Diagonal coupling bridge | The `2^D` periods hold for rows with periodic or biased centre columns too | **B** | `DiagonalCoupling` |
| Conservation laws ("chemistry lab") | No conserved window quantity of range `≤ 6` in the seed run | B (at those ranges) | `ChemistryLab` |
| Wheel family, inducing the rule | P1–P3 for any of the 256 rules; settled for rules 0, 90, 204; rows `0..4` identify Rule 30 | P (family) | `ElementaryCA`, `WheelInduction`, `Observer` |
| **Tuning by ear (Round 25, your idea)** | Pruned, directed search over candidate laws: sound, permanent pruning; finite/graded families lock in iff the law is in the family (`finite_lockIn`, `graded_settles_iff`, `tuneIndex_eventually`); no finite confirmation (`no_finite_confirmation`). P1 ⟺ the periodic tuning loop never settles (`problem1_iff_tuneCost_unbounded`); `TuneExcessLog` ⇒ P1, certified to `n = 2000`; excess `≤ 16` to `n = 1000`, sharp | R, S, CERT | `TuningByEar(Data)` |
| **Conjecture loop (Round 26, your idea)** | Candidate *statements* tuned like notes: sound pruning; loops prune every false candidate; graded families narrow exactly to the least true parameter (`narrow_eventually_eq`); junctions split by a finite read iff truth differs (`junction_split`), meets as a construction step; analogy is not a proof (`analogy_transport_unsound`). Run on Rule 30: excess = longest echo (`excess_le_iff_not_echo`); `TuneExcessLog` to `n = 131072`, sharp; window halving refuted (`not_windowHalving_two`); amortised halving ⇒ `HalfLineDies p`, certified `(4, 1)` to `d = 12`; two analogies refuted; periods 2/3 reduced to 1/2 drive words | R, S, CERT, **B** (refutations) | `ConjectureLoop`, `EchoBound`, `AmortizedHalving`, `ConjectureLoopData` |
| Observer / perspective (your idea) | The arrow `−sign D(N)` is exactly the direction of convergence; mirror-invariant, colour-reversed; the centre column cannot tell 30 from 86; the read angle is recoverable off-axis from row 2. **New this round:** the arrow is logically independent of P2 (see §5) | P (frame), **B** (as evidence) | `Perspective`, `Observer`, `ChiralLeak`, `SpinLattice`, `ArrowIndependence` |
| Spin, pyramid, cone, hole | Exact geometry of the triangle: spun cones, lattice spins, quaternion double rotations, side views, the rolled-up cone with its seam | G | `SpinSweep`, `SpinLattice`, `SpinQuaternion`, `ConeGeometry`, `Funnel`, `LatticeConeFraction` |

### 2.3 Institutional memory: error record

E1 inconsistent axioms; E2 map vs. seed; E3 local-to-global degree; E4 combinatorial bulk; E5
`C = 2`; E6 finite certificate ⇒ prize; E7 two top monomials at `n = 2`. Full table in
`HISTORY.md` ("Round 3", Track 4). One more lesson from later rounds:

* **E8 top-to-bottom flow.** Facts about high-degree ANF coefficients (parity locks, filtration,
  weight) cannot reach the seed column, which is the degree-one slice
  (`injector_lock_compatible_with_periodicity`).
* **E9 finite data inside an infinite characterisation** (Round 23, from the Round 21 draft).
  Counting blocks inside a fixed prefix turns Morse–Hedlund into a statement equivalent to
  `¬ Problem1` (`draftComplexityForm_iff`); extending the exact counting law to the edge `T = d`
  is false (`runCountTwoLawDraft_false`), and so is the deficit monotonicity after the edge
  (`deficitIncreasingAfterD_false`).

---

## 3. What is missing (as the GLM defines it)

The GLM's theorem wheel (Rounds 12–16, `rule30_round13/r13_glm_vocabulary_output.txt`) asks two
questions of each problem: can the GLM *state* it, and can it *answer* it? For all three the answer
is "state: yes; answer: no — the proved facts do not reach the problem through the declared
spokes". The missing pieces it names are below, checked against Lean.

### 3.1 Missing theorems (any one would answer the problem)

| Problem | Missing piece (weakest first) | Shape of what is needed | Lean |
|---|---|---|---|
| P1, P2 | `SeedAPBalanced`: every arithmetic progression `a(p·t + r)` has frequency 1/2 | one theorem about the seed, for every `(p, r)` | `problems_one_and_two_of_seed_apBalanced` |
| P1 | `LeftWhiteAperiodicAll` ⟺ `RunBoundsAll`: no column of any left-white row is eventually `p`-periodic, for every `p` | a uniform argument (induction on `p`, or one invariant); `p = 1` is proved | `problem1_of_leftWhiteAperiodicAll` |
| P1 | `HalfLineDies p` for every `p ≥ 1`: no non-white periodic drive keeps a finite half-line consistent forever (Round 21) | a statement about the left half-line only; `p = 1` is proved | `problem1_of_halfLineDies` |
| P1 (period 2 only) | `PeriodTwoHalfLineLinear`: every half-line word of `d` cells fails the alternating test by time `2d + 8` (Round 21) | the narrowest open rung now; one-sided; certified to `d = 36` (Round 22), EMP to `d = 46`; its first `d − 1` tests are exactly independent (`survivors_card`), the open part is the tests after the edge | `leftWhiteAperiodic_two_of_halfLineLinear` |
| P1 (period 2 only) | `PeriodTwoLinearBound`: a 2-periodic run at distance `d` lasts at most `2d + 7` steps | certified to `d = 18` (exact real values) | `leftWhiteAperiodic_two_of_linearBound` |
| P1 | `TuneExcessLog` = `EchoLogBound 2 2`: the longest echo (= the tuning excess, Round 26) after `n` notes is at most `2 log₂ n + 2` (Round 25) | one quantitative statement about the seed; certified for `n ≤ 131072` and sharp in the offset (Round 26), EMP to `10⁶`; any `EchoLogBound a b` suffices | `problem1_of_tuneExcessLog`, `problem1_of_echoLogBound` |
| P1 (period `p`) | `AmortizedHalving p c e`: `m` steps after the edge at most `2^(d−1+e)/2^⌊m/c⌋` half-line codes are alive (Round 26) | proposed by the loop as the repair of the refuted window form; `(4, 1)` certified to `d = 12` for `p = 2, 3` (EMP stable to `d = 17`) | `halfLineDies_of_amortized` |
| P1 (period 2 only) | a `Ranking (driveN 2 1) P c f` with `P` local to the state, or a `WidthStep (driveN 2 1) b` (Round 27) | ranking: a bounded measure that drops over every surviving window; width step: a wider code dies within `b` steps of a narrower one. 8 declared measures refuted (`no_declared_ranking`), `b ≤ 17` refuted | `wordDies_of_ranking`, `wordDies_of_widthStep` |
| P1 | No lag `p` has full echo resonance | one theorem about the seed, for every lag | `problem1_of_no_resonance` |
| P1 | Some column `c ≠ 0` is eventually periodic | expected to be false (all data look irregular) | `problem1_of_other_periodic_column` |
| P2 | `SeedFSTypical`: every finite-state observer is right half the time | stronger than `SeedAPBalanced` | `problems_one_and_two_of_seed_fsTypical` |
| P2 | `|D(N)| ≤ C√N` | probably false (iterated logarithm) | `problem2_of_sqrt_bound` |
| P3 | **No sufficient statement is declared** | a lower-bound technique for one explicit sequence on a uniform machine model; we know of no method that gives such bounds for a sequence like this | `Problem3`, `Problem3Eventual` |

All of these implications are collected and re-checked in `Frontier.lean`
(`frontier_sufficient_targets`), together with the restatements (`frontier_restatements`) and the
blocked routes (`frontier_blocked_routes`).

### 3.2 Missing GLM machinery (outside Lean)

* **Modules.** As of Round 11, 11 modules imported by the GLM were still missing from
  `glm_repo.zip`: `runtime/evidence` (blocks `--result`), `reasoning/planner_ladder`,
  `reasoning/combiner`, `reasoning/carried_read`, `reasoning/budget_guard_frozen`,
  `reasoning/frame_plane_study`, `reasoning/adversarial_dialogue_study`,
  `reasoning/nearest_address_study`, `reasoning/nearest_question_study`, and the packages
  `glm_universal.tools` and `glm_universal.knowledge` (the latter has files but no `__init__.py`).
* **Stand-ins.** Four labelled stand-ins are in use (`evaluation/harness`, `runtime/respell`,
  `runtime/sinter`, `reasoning/colour_induction`); none supplies answers, but colour tasks and
  `tool arc` refuse.
* **Gates not run here.** The GLM test suite (`pytest` was not available), `corpus --check` and
  `signoff --verify` have not been run on the Rule 30 overlays.
* **Theorem wheel.** *Resolved in Round 28:* `theorem_wheel_round28.py` (study folder) adds the
  Round 21–28 statements and spokes, the Problem 3 vocabulary and the narrowest open rungs. It
  also reads the whole ledger as carriers (`glm/r28_wheel.json`). The Rounds 17–20 geometry
  results can be looked up as ledger carriers but are not spokes, because they imply no target.
* **Stand-in note (Round 28).** Because the colour solver is missing, `tool arc` and colour tasks
  now fall back to local-rule induction. The fallback answers only when the demonstrations
  determine the answer. With the real colour solver installed, it runs only on that solver's
  refusals.
* **The wheel cannot invent a spoke.** By design it chains only declared implications. The
  missing theorems of §3.1 are exactly the spokes it lacks.

### 3.3 Missing in the Lean package itself

* No `sorry`, no added axioms. The open problems and targets are `Prop`s: `Problem1`, `Problem2`,
  `Problem3`, `Problem3Eventual`, `SeedFSTypical`, `SeedAPBalanced`, `LeftWhiteAperiodicAll`,
  `RunBoundsAll`, `PeriodTwoLinearBound`, `HalfLineDies p`, `PeriodTwoHalfLineDies`,
  `PeriodTwoHalfLineLinear`, `HalfLineLinear p a b`, `EchoLogBound a b`, `AmortizedHalving p c e`,
  `WordDies bd`, `Ranking bd P c f`, `WidthStep bd b`, `Round27Open`.
* Some older ledger rows record early finite results that were later superseded by general
  proofs (for example `C62` → `C96`, `C78`/`C79` → `C93`); their notes now say so.
* Not formalised (stated in `HISTORY.md` as such): the shell-fraction formula for the spinning
  pyramid; the random-tumbling `1/6` average; Golay/Leech hit rates (`DEF`).

---

## 4. To Do

Ordered by how directly each item bears on a prize problem. Items marked **(Lean)** are proof work
in this package; **(GLM)** are on the GLM side; **(EMP)** are computations to guide the proofs.
Status marks: **[done RN]**, **[partly RN]**, **[open]** (N = round).

1. **(Lean) Period-2 rung, uniformly in `d`. [open; reformulated R21; sharpened R22]** Prove
   `PeriodTwoHalfLineDies` (or the linear form `PeriodTwoHalfLineLinear`). It is now a statement
   about the left half-line only (`PeriodTwoHalfLine.lean`): `d` free cells, one test every two
   steps. The half-speed reduction (`alt_left_determined`) says the free data is one bit of column
   `c − 2` per two steps. Suggested attack: show that, after the edge, each new half-speed bit is
   forced and each pair of new cells gives one test (counting heuristic, HISTORY.md Round 21), then find
   an invariant that makes the tests fail within a bounded number of pairs.
   *R22:* the pre-edge half of the counting argument is proved (`survivors_card`: tests before
   time `d − 1` are exactly independent). What is missing is a statement about the tests after the
   edge, e.g. "among the codes alive at time `k ≥ d − 1`, at most a fixed fraction `θ < 1` survive
   the next `m` black times" (`EMP`: about one half per black time, `scripts/post_edge_halving.c`).
   Stating this as a `Prop` about `survivors`-like counts of codes of length `d` is the next step.
   *R26:* stated and tested. The window form (`WindowHalving`) is **refuted** for every window
   `m ≤ 12` (`not_windowHalving_two`: plateaus); the amortised form `AmortizedHalving 2 4 1`
   implies the rung (`halfLineDies_of_amortized`) and is certified to `d = 12`. By
   `halfLineDies_two_iff` only the drive `1, 0` needs to be treated. Next: prove
   `AmortizedHalving 2 c e` for some `c, e`.
   *R27:* the four routes are stated and each is proved to give the rung
   (`halfLineDies_two_of_routes`); ranking candidates (8 declared measures) and width steps
   `≤ 17` are refuted; the population route `AmortizedHalving 2 4 1` (`Round27Open`) is the one
   surviving uniform candidate. Exact `Lmax d` for `d ≤ 32` (`lmaxTwo_spec`).
2. **(Lean) `HalfLineDies p` for `p ≥ 2`. [open; new R21]** `p = 1` is proved by a forced fixed
   pattern (`constDrive_pattern`). Try the same for drive words with many black cells (e.g. `110`,
   `1110`), where most steps carry a test; a proof for a class of words would be new.
   *R26 [partly]:* all rotations of a drive word are equivalent (`wordDies_shift_iff_of_periodic`):
   period 2 needs one word, period 3 two words (`halfLineDies_two_iff`, `halfLineDies_three_iff`).
   EMP: for `110` the machine bound grows slowly (`d + 11` at `d = 22`), so no constant-time forcing
   argument of the period-1 kind exists for it.
   *R28 (EMP):* the same holds for the words `1^(p−1)0`, `p = 4, 5, 6`: `Lmax(d) − d ≤ 10` for
   `d ≤ 24` but growing (`rule30_round28/word_lifetimes.c`; C282).
   *R31:* in the sideways view (`SidewaysView.lean`) a drive word fixes the first column at its
   black times and leaves one free bit at each white time. Only the constant word has no free bit,
   which is why period 1 has a one-line proof (`halfLineDies_one_sideways`). Exact `Lmax` for the
   words `100, 110, 1000, 1100, 1110` to `d = 20` (`lmaxWord_spec`).
3. **(EMP → Lean) Barrier diagonals. [partly R21]** The plateau pattern of `d + B(d)` also appears
   in the machine (C220). Next: record, for each `d`, which left diagonal ends the longest machine run
   and whether it depends on the word; if not, state the barrier lemma as a `Prop` about the machine.
   *R31 [done, negative]:* it depends on the word. `barrier_depends_on_word` (CERT): at `d = 8` the
   words `10, 100, 110, 1000, 1100, 1110` end their longest lives on the diagonals
   `18, 32, 20, 36, 20, 24`; for `10` the diagonal `d + Lmax d` takes 28 distinct values for
   `d ≤ 32` (`barrier_set_not_small_two`). The small barrier set of the two-sided run bound is not a
   property of the machine (`BarrierDiagonalsData.lean`, `scripts/barrier_diagonals.c`).
4. **(Lean) Certificates further out. [done R22]** The prefix search (`PrefixSearch.lean`, sound,
   about `2^(d/2)` nodes for period 2) certifies the period-2 linear target to `d = 36` and the
   linear targets of periods 3–6 to `d = 26/23/21/19`. Further range now costs build time
   (the checks run in the interpreter; each `+2` in `d` doubles the period-2 time, `d = 36` takes
   about a minute); a diagonal-incremental search would save at most a constant factor.
5. **(Lean) The strobe lens, one stride at a time. [open]** `SeedAPBalanced` for a single stride
   `p` is open. Weaker still: even "the centre column is not eventually 2-periodic" (stride 2: some
   phase keeps changing) is not proved here; it is the strobe form of the period-2 rung.
6. **(GLM) Bring the theorem wheel up to date. [done R28]** *R28:* the wheel reads the ledger
   carriers (`glm/r28_wheel.json`; `tool theorem ledger …`), and the Round 21–28 spokes and negative
   controls are declared (`theorem_wheel_round28.py`; C280). *Earlier:* [partly R21] `scripts/ledger_check.py --wheel`
   now writes the ledger as JSON carriers (id, claim, class, status, Lean names, axioms). Remaining:
   import these carriers into the wheel and mark spokes (proved implications such as
   `problem1_of_halfLineDies`) and negative controls (refuted/blocked rows).
7. **(GLM) Restore the 11 missing modules**, run the test suite and the gates, retire the
   stand-ins. **[open; needs the GLM repository]** *R28:* 11 modules are still missing from
   `glm_repo.zip`. The Round 28 overlay installs on a fresh unzip anyway and passes its checks.
8. **(GLM) Declare a P3 vocabulary.** Add `Problem3` / `Problem3Eventual` and the whole-cone
   facts as statements, with the negative control "the light-cone map is a different function".
   **[done R28]** (`P3Eventual => P3`, `LightConeCircuitBound =/=> P3` in `theorem_wheel_round28.py`).
9. **(Docs) Keep `claims.csv`, `HISTORY.md`, `README.md` (file map) and this file in step** with every new Lean file, and run
   `scripts/ledger_check.py` before closing a round. **[ongoing; see `DEVELOPMENT.md`]**
10. **(Lean) The post-edge tests. [open; new R22]** Formalise the population view: for codes of
   length `d`, count those alive at time `k ≥ d − 1` and try to prove a halving inequality for
   some class of drives (first candidates: words with two black cells in a row, where consecutive
   tests read neighbouring cells, cf. `constDrive_pattern`).
   *R26 [partly]:* the population view is `aliveCodes`; a per-window halving inequality is false
   (plateaus), an amortised one is the right shape (`AmortizedHalving`, see item 1).
   *R27:* plateaus and the events ending them are recorded with all longest witnesses
   (`scripts/post_edge_witnesses_output.txt`); longest witnesses often merge into one trajectory
   (`witnesses_merge`), so counting codes over-counts mechanisms.

11. **(Lean) Kronecker's converse. [done R24]** `problem1IffHankelInfinitelyOften`
   (`HankelKronecker.lean`): the Hankel form is now a proved equivalent form of P1.
   *Original item (R23):* Prove `Problem1IffHankelInfinitelyOften`, i.e.
   that unbounded linear complexity forces infinitely many non-zero Hankel determinants (the
   classical route is Berlekamp–Massey theory: every value taken by the linear-complexity profile
   is an index with non-zero Hankel determinant). It would make the Hankel form a third equivalent
   form of P1.
12. **(Lean) The counting law after the edge. [open; new R23]** `runCount_law` is exact for `T < d`.
   For `T ≥ d` the counts are irregular (`scripts/run_count_output.txt`); a bound of the form
   `RunCount 2 d (d + m) ≤ θ^m · 2^(d+1)` for some `θ < 1` would give the period-2 run bound for all
   left-white rows (the two-sided form of item 10). It is the same open core as items 1 and 10, now
   in the original (two-sided) setting.
13. **(Lean, CERT) The automaticity rung. [partly R23]** `CentreNotTwoAutomatic` is open; the
   kernel has `≥ 1023` elements (`twoKernel_centerCol_ge`). A proof would need the kernel to be
   infinite, e.g. a `KernelPath` for the centre column.

14. **(Lean) The OR-type class. [open; new R24]** Among the 32 one-gate variants of
   `L xor (C or R)`, the only unsettled centre columns are those of the four OR-type left-permutive
   wheels 30, 45, 75, 135 (`outer_alternative_periodic`, `inner_alternative_periodic`,
   `orType_no_small_period`). Wheels 45 and 75 are a different symmetry class from 30/135; a proof
   for any one of them (even non-periodicity of a single column) would be new. The same machinery
   (`RunCountW`, `runCountW_law`) applies to all four.
15. **(Lean) Post-edge counts versus the mirror. [open; new R24]** For Rule 86 (the mirror of 30) the
   counting law is exact for all `T` (`runCountW_eightySix`); for Rule 30 it breaks at `T = d`. A
   statement comparing `RunCountW 30 2 d T` with the exact value `2^(d+1)` after the edge (e.g. an
   upper bound by a decreasing function of `T - d`) is the same open core as items 1, 10, 12, now
   with an exact control rule to compare against.
16. **(Lean) The tuning excess. [open; new R25]** `TuneExcessLog` (or any sublinear
   `TuneExcessBound g`) implies P1 (`problem1_of_tuneExcessBound`). Since `lcProfile ≤ tuneCost`,
   a linear-complexity lower bound of the form `lcProfile centerCol n ≥ n − o(n)` would also give it,
   but for a random-like sequence the linear complexity is only about `n/2` (Round 23 certifies
   `≥ 10000` at 19999 bits), so that route is not expected to work; the excess has to be
   bounded through the periodic structure itself (e.g. via the half-line machine of Round 21:
   a periodic tune of size `c` that fits `c + k` notes is a run of length `k` of a periodic column).
   Also: extend the certificate beyond `n = 2000` (it is quadratic; `n = 2000` takes seconds).
   *R26 [partly]:* the excess is exactly the longest echo (`excess_le_iff_not_echo`); the
   certificate is now a sort (`repeatFree_of_check`) and reaches `n ≤ 131072`
   (`tuneExcessLog_upto_131072`); the offset 2 is sharp (`not_echoLogBound_2_1`). Sharp frontiers
   for slopes 0, 1, 3 are certified too. Still open: any `EchoLogBound a b` for all `n`.
17. **(Lean) Amortised halving. [open; new R26]** Prove `AmortizedHalving p c e` for some `c, e`
   and `p = 2` (it implies the period-2 rung). Certified `(4, 1)` for `d ≤ 12`; EMP stable to
   `d = 17` (`scripts/conjecture_loop_output.txt`). A proof would need a reason why the deterministic
   tests after the edge keep halving *on average*.
   *R27 [open]:* still the one surviving uniform candidate (`Round27Open`); smallest unresolved
   case `d = 13`. Not extended: no competing explanation would be separated by more range.
18. **(GLM) Run the conjecture loop inside the GLM. [mostly done R30; new R26]** `scripts/conjecture_loop.py`
   is a stand-alone prototype of the propose / test / narrow / loop cycle with SEED, ANALOGY,
   NARROW, JUNCTION (meet) and REPAIR operators; `ConjectureLoop.lean` states what each step
   guarantees. Port it to the GLM's analogy and junction machinery, with the Lean families as the
   candidate grammar and `ConjectureLoopData.lean` as the pattern for turning verdicts into
   theorems.
   *R27 [partly]:* `scripts/candidate_benchmark.py` makes the contribution measurable: candidate
   records with origin (supplied / generated / repaired / analogy), target implication, smallest
   counterexample, range, formal status and cost; a frozen grammar (LIN, AMORT, WS, RANK);
   enumeration vs counterexample-guided repair under one budget and oracle; held-out drive words of
   periods 3 and 4. GLM-guided selection has a plug-in (`--glm proposals.json`) and remains to be
   run from the GLM side.
   *R28 [partly]:* the GLM side is now operational and measured (`rule30_round28/r28_benchmark.py`:
   ARC, held-out local-rule puzzles, knowledge alignment, the Round 11 regression suite). The GLM
   still cannot *generate* candidate statements (its wheel chains declared spokes only), so the
   `--glm` plug-in has nothing to run yet.
   *R29 [partly]:* the propose / test / narrow loop now runs inside the GLM for puzzles
   (`grid_planner.py`: candidates = chains of steps, test = the hard gate, narrow = cost tiers and
   leave-one-out, refuse = disagreement with the separating question). Porting the same planner
   to candidate *statements* (the Lean families as the step alphabet) is To Do 25.
   *R30 [mostly done]:* stage 4 of the Round 30 pipeline (`rule30_round30/statement_planner.py`)
   generates candidate statements inside the GLM (`tool pipeline frontier`), the Lean certificates
   (`PipelineData.lean`) certify each frontier point sharp, and `proposals.json` runs through the
   Round 27 `--glm` plug-in (C292, C296). Open: candidates beyond the LIN / AMORT grammar.
19. **(Lean) Inner survivors, uniformly. [open; new R27]** `inner_alternation_bound` is the sound
   form of width reduction: an inner column that follows the drive is a half-line problem of its
   own. The longest survivors of lengths 11, 13, 15, 19, 21 share the inner code `1601`
   (`shared_inner_survivor`, EMP). State and test a uniform version, e.g. "every code alive `K`
   steps past its edge has an inner column alternating for at least `f(K)` of those steps", which
   with a bound on inner lives would give a recursion for the run bound.
   *R28 (EMP, C281):* not supported. For `d ≤ 22` the longest inner alternation of a surviving code
   is 7–14 steps, while its post-edge life grows to 20, and the slack grows
   (`rule30_round28/inner_survivors.py`). A recursion would need several inner stretches, not one.
   *R29:* the uniform form `InnerFollows a` is refuted for every `a ≤ 7` (`not_innerFollows`, CERT;
   To Do 22).
20. **(Lean) A useful finite quotient. [open; new R27]** `colHistory_determines` shows a quotient
   that keeps the whole column history is trivial, and `halfStateD_strictMono` shows the raw state
   graph has no cycles. Look for a quotient that forgets the untested odd-time values (period 2),
   or a measure on the prefix tree (not on single states), and test it against the declared
   counterexamples in `ProofRoutesData.lean`.
   *R31 [done for window quotients, negative]:* `infinite_row_survives`: if the far cells are free
   (infinite rows), the machine survives forever under every drive, so no quotient that keeps a
   bounded window and treats the rest as free can prove `HalfLineDies p`. Any working argument must
   use the finiteness of the row. The exact form of what remains is the sideways statement
   `halfLineDies_iff_sideways` (`SidewaysView.lean`). A measure on the prefix tree is still untested.
21. **(GLM, ARC) Object-level readers under the same refusal rule. [done R30; new R28]** The local-rule
   ladder (`LocalRuleInduction.lean`, `local_rule_induction.py`) never answered a held-out puzzle
   wrongly. It refuses most puzzles, though, because their query keys are unseen. Add readers that
   see objects (the connected component of a cell: its size, colour, bounding box and the cell's
   position in it) and measure them on a fresh held-out set. When keys are unseen, ask for the
   separating example instead of refusing.
   *R29 [mostly done]:* six object readers (size, rank, shape, colour-blind size and shape, box
   edge) and a colour-rank reader are finishers of the Round 29 planner; with plans, the stored ARC
   score went 1 → 10 right, 0 wrong. A refusal for disagreement now names the cell to ask about
   (`separating_example_refutes`). Open: an oracle loop that actually asks and is measured
   (To Do 24).
   *R30 [done]:* the ask loop is built and measured (To Do 24); fitted middle steps read object
   properties (To Do 23).
22. **(Lean, CERT) Certify the To Do 19 finding. [done R29: `not_innerFollows`]** State the uniform inner-survivor
   form as a `Prop` and refute it with a certified witness, in the style of
   `not_windowHalving_two`. The EMP witness is `d = 14`, code `11083`, post-edge life 19, longest
   inner alternation 11.

23. **(GLM, ARC) Parameterised and backward steps. [done R30; new R29]** The planner's fitted steps
   are only the *last* step (colour map, tiling, local rule). Add fitted *middle* steps (recolour by
   an object property, scale to a size read from the grid, draw a line between two objects) and use
   goal regression (`run_concat_eq_some`) to prune by the output's shape from the back. The
   stored ARC failures are mostly of these kinds (frames scaled to fit, per-object moves).
   *R30 [done]:* 13 fitted middle steps and goal-shape pruning (`Pipeline.lean`: `semMid_eq_some_iff`,
   `shapePrune_skip`, C289). Fresh held-out 56 → 96 of 132 right (6 → 4 wrong; C293). The stored
   ARC score is unchanged (10/0): the remaining ARC failures need steps outside this alphabet.
24. **(GLM) Ask and measure. [done R30; new R29]** Simulate the oracle: when the planner refuses for
   disagreement, give it the true value of the cell it names (`ask`) and re-plan. Measure how many
   questions are needed per held-out puzzle; `separating_example_refutes` guarantees each answer
   removes at least one surviving plan.
   *R30 [done]:* `askLoop_correct`, `askLoop_questions_lt` (C290); measured: about 2–2.7 questions per
   answered puzzle; fresh held-out 96 → 106 right at ≤ 5 questions (wrong 4 → 5); Round 28 held-out
   48 → 77 (C293, C294).
25. **(GLM, Lean) The planner over statements. [done R30; new R29]** Use the same planner, with the
   `PlanSearch` guarantees, for candidate *statements* in the conjecture loop (To Do 18): steps =
   the declared Lean families and their repairs; hard gate = the Lean certificates; tiers = the
   candidate's cost. This is the route by which the GLM could *generate* candidates.
   *R30 [done]:* stage 4 of the pipeline; 30 frontier statements certified sharp
   (`frontier_round30`, C292); measured against Round 27 (C296). The fitted statements transfer
   0/16 to held-out levels: they are tight on the data, as the Occam measurement predicts.
26. **(EMP → GLM) The Occam failures. [done R30; new R29]** Every wrong planner answer seen so far is a
   cheaper hypothesis that fits all demonstrations (C288; `minAgree_needs_occam`). Measure how
   often this happens as a function of the number of demonstrations, and whether leave-one-out at
   depth 1 removes them without losing right answers (on a fresh held-out set).
   *R30 [done]:* `minAgree_wrong_imp`, `gate_can_fix`, `gate_can_drop_truth` (C291). Measured (C295):
   wrong answers occur almost only for k ≤ 2 demonstrations; a depth-1 gate removes most of them
   but also right answers (k = 1: 62/13 → 42/2), so the pipeline gates from depth 1 only when
   k ≤ 2. One fresh family stays wrong at k ≥ 3 (`objsize-recolour-rot90`).
27. **(GLM) Beyond Occam. [open; new R30]** The remaining wrong answers are a cheaper plan fitting
   all demonstrations. Options to test on a fresh set: prefer plans whose fitted maps are total on
   the query keys; ask a question also when the cheapest tier is unique but a next tier disagrees.
28. **(Lean) Uniform statement frontier. [open; new R30]** Every `SharpLinear` point in
   `PipelineData.lean` is sharp on a finite range only. A proof of any `HalfLineLinear 2 a b` for all
   `d` is the period-2 rung of To Do 1.
29. **(Lean) The sideways reader for period 2. [partly R33; new R31]** *R33:* columns 2–5 in
   closed form and three forced bits of a survivor (`SidewaysPeriodTwo.lean`). From column 4 on,
   the columns grow in GF(2) degree (C319), so a low-degree invariant has to mix columns. By `halfLineDies_iff_sideways`
   the period-2 rung says: for `u` with `u t = 1` at even `t` and free at odd `t`, the
   reconstructed row `recon (driveN 2 1) u (i+1) 0` is never a finite non-empty row. Column 2 of the
   reconstruction repeats each free bit twice (cf. the half-speed reduction `alt_left_determined`). Look for an invariant of the
   sideways map `(K k, K (k+1)) ↦ (K (k+1), K (k+2))` that is preserved for admissible inputs and
   excludes rows that become white.
30. **(EMP → Lean) Word families with long lives. [done R33; new R31]** *R33:* on the wall
   clock `Lmax d / d` is close to `p / b` (`b` = black cells). On the observer's clock every word
   dies after about `d` tests (`TestCountLaw.lean`, `TEST_COUNT.md`), and the worst cases are
   certified (`frontier_round33`, `not_testCountLinear_four_six`). The words with few tests per
   period live longest (`1000`: `Lmax 28 = 96`; `100`: `Lmax 22 = 87`, EMP). Measure whether
   `Lmax d / d` stays bounded for each word (a linear bound per word would be the `HalfLineLinear`
   target) and certify the worst cases.

31. **(Lean) Eight to twelve defects. [done R47; new R32]** *R47:* certified for every weight and
   all `2^24` patterns (`MathieuCensus.lean`, `MathieuCensusOrbits.lean`, `census_49`; C417, C418).
   *Original item:* The census (`scripts/m24_orbit_census_output.txt`,
   EMP) has 3 orbits for 8–11 cells and 5 for 12. Certify them in Lean as for 6 and 7 cells; this
   needs a separating invariant for each orbit (for example the number of octads meeting the set in
   6 or more cells) and a faster enumeration than sublists for 12 cells.
32. **(Lean/GLM) The geometry side of the `M₂₄` idea. [open; new R32]** For a concrete target
   geometry (a diamond supercell, a lattice, the ARC grid), write its site-permutation group as
   permutations of the 24 sites and compute its intersection with the laid-out `M₂₄`
   (`Shared`, `transport_iterate`). Only that intersection transports. For the Rule 30 ring it is at
   most 12 (`shared_card_le_twelve`).
33. **(Lean) MOG subgroups. [partly R47; new R32]** *R47:* generators and their orbits on cells and
   octads certified (`MathieuMOG.lean`, C419). Still open: that the generators give the full
   stabilisers, and `|M₂₄| = 244823040` itself. *Original item:* Give generators of the sextet, octad and trio
   stabilisers in the GLM labelling and certify their orbits with the same tool (`certOK`,
   `orbit_eq_of_checkL`). The classical orders (from `|M₂₄| = 244823040`) would then give the
   stabiliser orders in the census table formally, once `|M₂₄|` itself is certified.
34. **(EMP → Lean) Halving on the observer's clock. [partly R33; new R33]** `TestHalving p e`
   (after `n` tests at most `2^(d−1+e)/2^n` codes alive) gives `TestCountLinear p e`
   (`TestHalving.lean`). Certified: excess 6 for period 2 on `d ≤ 18` and for period 4 on `d ≤ 16`.
   Excess 5 is false for period 2; excess 6 is false for period 4. Measured excesses on `d ≤ 24`:
   2, 6, 11, 6 (C324). Next: a per-test mechanism for the halving, starting from the exact
   pre-edge independence (`survivors_card`).
35. **(EMP → Lean) Does period 4 have a finite slack? [open; new R33]** The three-black words
   `0111`, `1110`, `1101` keep raising the excess (7 at `d = 30`, `not_testCountLinear_four_six`).
   Either find a family of codes refuting every slack (then `TestCountLinear 4 c` is false for all
   `c`, and P1 for period 4 must go through `HalfLineDies` directly), or certify a bound.
   `scripts/word_lifetimes33.c` with `4 40 4 1`. This is the GLM's current first pick (`tool next`).
   *R34 [partly]:* no refuting family found. Exact search (`rule30_round34/test_slack34.c`): no
   period-4 word exceeds slack 7 on `d ≤ 37`; the three-black words stay within 7 to `d ≥ 102`
   and drift down (C328, C329). CERT: least period-4 slack on `d ≤ 30` is exactly 7
   (`testCountLinearUpTo_four_seven`, `frontier_round34`). By the divisor rule
   (`testCountLinear_of_dvd`) `TestCountLinear 4 7` for all `d` would also give period 2's slack.
   Open: `TestCountLinear 4 7` for all `d` (needs an idea; the GLM now refuses more search here).
   *R35:* with the faster checker (To Do 37) the certificate reaches `d ≤ 32`
   (`testCountLinearUpTo_four_seven_32`); still exactly 7 there. Periods 2 and 3 to `d ≤ 42`, `32`.
36. **(EMP → Lean) Why the excess drifts down. [partly R34; new R34]** For words with many tests
   per period the excess falls below 0 for large `d`. Exactly (from `survivors_card`):
   excess = (tests after the edge until the last code dies) − (free bits left at the edge) − 1,
   so a negative excess means the post-edge tests remove more than half on average.
   *R34:* exact alive counts for `d ≤ 25` (`rule30_round34/alive_decay34.c`, C331): on this range
   the post-edge rate is close to one bit per test for every word tried; the drift is a
   large-`d` effect. Next: a per-test statement for words with two adjacent black cells.
   *R35 [partly]:* done for every black run (`BlackRunWindow.lean`, C336): the `r` tests of a run
   of `r` black times pass iff the `r` cells next to the column show `runWord r b` (the pattern
   `0101…`, last cell flipped iff the run is followed by white). So after the edge the question is
   only how these windows are distributed among the surviving codes (To Do 38). Consequence for
   every drive: a black run of length `≥ d + t + 3` from time `t` kills every code of length `d`.
37. **(Lean) A faster verified checker. [done R35; new R34]** The certificates use the Round 22 prefix
   search, which re-simulates every prefix. A verified version of the incremental light-cone
   search (`rule30_round34/test_slack34.c`) would push the slack certificates to about `d = 40`
   (period 4) and `d = 44` (period 2).
   *R35 [done]:* `DiagonalSearch.lean` (FORMAL soundness, C332): the incremental light-cone
   search, one anti-diagonal per node by a logarithmic prefix xor. Measured gain about 2–2.5× under
   Lean's evaluator (C337), less than the C program's; reached `d = 42` (period 2) and `d = 32`
   (periods 3, 4) within minutes per word (`DiagonalSearchData.lean`, C333). Further gains need a
   smaller search tree, not a cheaper node.
38. **(Lean) Window distribution after the edge. [open; new R35]** By `blackRun_word` the tests of a
   black run ask one question: is the window of width `r` next to the column the run's word? Before
   the edge the windows of the surviving codes are exactly uniform (`survivors_card`). A statement
   that they stay *nearly* uniform after the edge — e.g. at most a fixed fraction `θ < 1` of the
   survivors show the run's word, amortised over runs — is the shape of the halving mechanism
   (To Do 34); made precise as `TestHalving p e` it gives `TestCountLinear p e`
   (`testCountLinear_of_testHalving`). First case: words `1^(p−1)0`, one run per period.
39. **(Lean) A uniform proof for an infinite family of hubs. [partly R37; new R36]** By
   `halfLineDies_iff_wheel` every proof or certificate is needed only for hubs (`WheelRep`).
   A proof of `WordDies (driveN q j)` for an infinite family of hubs — the first candidate is the
   hubs `1^(q−1)0` (one black run per period, each run one window read by `blackRun_word`) — would
   be the first result that skips iteration along `d` as well as along the period.
   *R37 [partly]:* `OneRunFamily.lean` (C347).
   * Every `1^(q−1)0` is a hub (`wheelRep_oneRun`).
   * For every `q` and every `d ≤ q − 4`, every code fails within `d + 2` tests (`oneRun_band`,
     from `failsWithinTests_of_initial_blackRun`).
   * The hub kills iff it kills the codes of length `d ≥ q − 3` (`oneRunDies_iff_long`).
   * The whole family contains `HalfLineDies 2` (`halfLineDies_two_of_oneRunFamily`). So the
     honest target is `OneRunFamilyDiesFrom q₀`.
   * EMP: slack `≤ 7` for `q ≤ 20` on `d ≤ 30` (C348). The next step is To Do 43.
40. **(EMP → Lean) The cost of a turn. [done R37; new R36]** `testSlack_wheelTurn` bounds the slack of a
   turn by the hub's slack `+ 2(p − 1)`; the sharper bound `+ (p − s) +` (tests skipped) follows
   from `testSlack_of_shift_white`. Measure on which phase each wheel attains its least slack (the
   period-4 slack 7 at `d = 30` is attained in the phase `0111`, while the hub `1110` stays within 5
   on `d ≤ 24`), and whether a per-wheel slack law is more natural than a per-period one.
   *R37 [done]:* `TurnCost.lean`, `TurnCostData.lean` (C343–C346).
   * The exact cost is `m + testsBefore (phase a) m` (`testSlack_phase_transfer`).
   * It has no violation on 2876 phase pairs, and some pair attains it in 66 of 69 wheels.
   * The per-wheel law is the natural one: a slack at the **best phase** of each wheel suffices
     (`testCountLinear_of_phases`). Measured best-phase slacks are `≤ 6` up to period 8, against
     per-period slacks of up to 14.
   * Period 2: the phase `01` needs exactly 3 (CERT `d ≤ 40`) and gives `TestCountLinear 2 5`.
   * Period 3: the phases `010` and `101` need 5 and 2 (CERT `d ≤ 32`) and give
     `TestCountLinear 3 8`.
41. **(GLM) Index the half-line family by hubs. [done R37; new R36]** The theorem wheel should read
   `halfLineDies_iff_wheel` as an instantiation rule (a hub fills in its whole orbit and every
   multiple period), and `tool next` should propose hubs, not periods or words (ledger C338–C342).
   *R37 [done]:* the study folder `rule30_round37/` (C350).
   * New tools: `tool hub P K`, `tool hubs P` and `tool requirements`.
   * `tool next` proposes hubs first, and the theorem wheel has the hub rule
     `HubsOfDivisors<p> ⇔ HalfLineDies<p>`.
   * Measured: consultation went from 0/11 to 11/11 (frozen development questions), and the hub
     index is exact on 8178/8178 words.
   * The exact search over periods 1–7 took 5.19 s for all words and 0.64 s for the hubs. All
     earlier self-tests pass.
42. **(Lean) Period 2 from its best phase. [open; new R37]**
   * Target: `TestSlack (driveN 2 2) 3` for all `d`, i.e. the phase `01`, black at odd times.
     It gives the optimal `TestCountLinear 2 5` (`testCountLinear_two_of_phase`), hence
     `HalfLineDies 2`.
   * At this phase every test is preceded by a white step, and each test is one window read of
     width 1 (`blackRun_word`).
   * First step: measure how the surviving codes' windows are distributed at each test (To Do 38
     at the best phase).
43. **(EMP → Lean) The one-run family beyond the band. [open; new R37]**
   * Target: a fixed slack `c` such that for every `q`, the codes of length `q − 3 ≤ d ≤ 2q` fail
     within `d + c` tests of `1^(q−1)0`. Measured: `c = 7` suffices for `q ≤ 20`, `d ≤ 30`.
   * First step: the exact survivor sets after the first two runs, for `q ≤ 24`.
44. **(GLM) The GLM proposes spokes. [partly done R38, R39; new R37]** Round 38: the hypothesis engine
   (`HYPOTHESIS_ENGINE.md`) proposed the period law and the `D = 87867` prediction before Lean checked them.
   Round 39: it proposed the white-diagonal criterion and the regime statistics that led to
   `ldiag_infinitely_many_white`, and ran unchanged on 8 non-Rule-30 problems (`../HypothesisEngine/`). The GLM reads and chains proved spokes but
   proposes none. The next step is to measure how many of a round's new spokes it could have
   stated beforehand. `tool next` asks which kind of proposal should count.
   *R41:* the v11 self-dialogue (`rule30_round41/`, C388) chooses its own next checks. From
   `D < 400` it refuted the white list and the period bounds and re-mined both proved laws without
   a script telling it where to look. Its "what does it imply?" step uses only checked edges
   (To Do 50).
45. **(Lean) Are left-diagonal periods unbounded? [open, sharpened R39; new R38]**
   * Round 39: white left diagonals never stop (`ldiag_infinitely_many_white`). Unboundedness is
     exactly "odd-parity white diagonals for every period `2^m`" (`ldiag_periods_unbounded_iff`).
     *(The R38 wording "equivalent to infinitely many white diagonals" was too strong.)*
   * Measured whites: 2, 7, 28, 399, 53207, 58286, 87866 (CERT) and 1,420,878,968 (EMP).
   * The parity at each white diagonal depends on one transient bit (C368–C370).
   * *R40:* the doubling after a white diagonal is read two diagonals further out
     (`doubling_read_two_out`); the run-up prediction gives the next doubling (period 64) at
     `2107985255` (EMP, To Do 46).
46. **(Lean / EMP) Decide the open bit at a white diagonal from finite data. [partly R40; new R39]**
   * After the white diagonal `w`, diagonal `w + 1`'s eventual pattern is `u` or not-`u`. Which one
     is fixed by the last black cell of diagonal `w`, i.e. by the transient.
   * *R40, proved:* the bit is a finite computation of explicit size — every diagonal `D < N` is
     `2^m`-periodic from time `1 + D·2^m` (`ldiag_perFrom_linear`); at **odd** white diagonals
     the bit does not matter at all (`next_white_independent_of_odd_bit`); every row with a left
     edge has the seed's left side up to a time shift through `53207`
     (`left_edge_rows_agree_up_to_shift`, CERT).
   * *R40, EMP:* the bit is **not** row-dependent in practice (H2 refuted on 321 rows), and a
     short driven stretch reproduces it (run-up universality H9, validated at `53207`, `58286`).
     Prediction at `1420878968`: bit 1, next white `2107985254` (odd), **period 64** from
     `2107985255` (`rule30_round40/r40_bit_prediction.txt`).
   * Next: prove H9, or at least a version of it (To Do 47).
47. **(Lean) Run-up universality. [open; new R40]**
   * Target: for a stretch of left diagonals driven at its outer edge by eventually periodic
     inputs, the eventual pattern after an even white diagonal does not depend on the stretch's
     initial filling once the run-up is long enough.
   * What is known: false for short run-ups (EMP: run-up 300 at `53207` gives 3/8); at odd white
     diagonals only true up to the time shift (proved symmetry, `odd_white_complement_is_shift`).
   * A proof would turn the period-64 prediction into a theorem and make the Round 39 scan a
     complete algorithm for the white diagonals.
48. **(EMP → Lean) Beyond period 64. [open; new R40]**
   * If the prediction holds, the next white diagonal after `2107985254` is fixed by the pattern
     law alone (odd white: no branch). The law at period 64 finds none in
     `2107985255 … 32107985254` (`rule30_round40/fscan_q64.txt`, 3·10¹⁰ diagonals). A faster scan (several diagonals per step, or the
     regime's cycle structure) is the next step.
49. **(Lean) Universality of the left side. [open; new R40]**
   * Conjecture (EMP, H2): every row with a left edge has the seed's eventual left diagonals up to
     a time shift, for **all** `D`. Proved through `D = 53207`. It would make the white
     diagonals, their parities and the left-diagonal periods properties of Rule 30 itself, not of
     the seed.

50. **(GLM) Checked implication graph for the dialogue. [new R41]**
   * The owner's v10 dialogue states implications by keyword; two were wrong (C384, C385). v11
     answers only from `rule30_round41/knowledge.json`, whose edges each cite a Lean theorem or a
     ledger claim.
   * Next: generate the edges from `claims.csv` and the Lean statements themselves, rather than
     writing them by hand, so that every new proved spoke becomes an edge automatically. The
     ledger check (`scripts/ledger_check.py`) already resolves the names.

51. **(Lean) The 2-adic layer tower. [new R47]**
   * Done: Problem 1 ⇔ the centre column's 2-adic integer is irrational
     (`problem1_iff_padic_irrational`, C415); no small fraction `r/q` on layer 256 (C416, CERT).
   * Done (R47): the *layer ↔ period* dictionary (`AdicPeriod.period_of_dvd`,
     `periodic_presentation`, C420): `q ∣ 2^p − 1` gives period `p` from `log₂|r| + 1 + p`. Through
     it the period certificate excludes every `r/q` with `q ∣ 2^p − 1`, `p ≤ 500`, `|r| < 2^500`
     (C421).
   * Also done: the longer certificate C410 gives no `r/q` with `q ∣ 2^p − 1`, `p ≤ 64`,
     `|r| < 2^29936` (`centerCol_not_fraction_64`).
   * Next: ask which *layer* statements are not period statements in
     disguise — e.g. bounds on the carry `t(n)` along the centre column itself (it is unbounded for
     every `r/q` iff Problem 1).
   * The escalation reading: the tower is the one *chain* of layers in the package (each layer
     refines the one below), which the moduli `2, 4, 8, 144, 256` of the sketch are not.

52. **(Lean / EMP) Are the triangles near the left edge bounded? [new R48]**
   * Done (R48): the settled longest white run in the first `N` left diagonals is exactly `10` for
     `N = 400` and `16` for `N = 20000` (`TrianglesData.lean`, C427); at the right edge triangles of
     every size occur (`arbitrarily_large_right_triangles`, C426).
   * Open: is the settled longest white run in the first `N` left diagonals bounded as `N → ∞`?
     Since the strip is a chain of one-bit machines (`ldiag_succ`), a run of length `L` needs `L`
     consecutive diagonals white at one time; the regime machinery of `WhiteDiagonals.lean`
     (`regime_periodic`) is the natural tool.
   * Next (EMP): the record right-edge tops at `2^k` grow like `2.6k`; prove a sharper lower bound
     than `k` from the least periods of the right diagonals.

## 5. Analysis directions (Aristotle's suggestions)

### 5.1 The period-2 rung: barrier diagonals and transients

Two observations from the data line up in a way that may be worth testing:

* **Run bounds come in blocks.** For period 2, `d + B(d)` (where a longest run ends, measured from
  the moving left edge) takes only the values `8, 24, 41, 54, 55, 60, 61` for `d ≤ 28` (`EMP`
  beyond `d = 18`). So longest runs end on a few fixed **left diagonals**.
* **Left diagonals settle late.** Every left diagonal is eventually periodic with a small
  power-of-two period (`ldiag_eventually_periodic`), but (`EMP`) only after a transient of about
  `1.3·D` steps, and `B(d)` is also about `1.3·d` in the data.

**Hypothesis to test (EMP, not a claim):** a 2-periodic run starting at distance `d` is killed when
the column reaches a diagonal that is still in its transient, and the killing diagonals depend
only on `d`, not on the row. If so, a "barrier lemma" (every alternation breaks before the next
barrier diagonal) gives `B(d) ≤ (next barrier) − d`, and the uniform statement becomes a statement
about the barriers having bounded relative gaps. This is a structured target that a finite search
can probe and that Lean can state.

**Round 21 update.** The same plateaus appear for the one-sided machine (`d + B(d)` = 8, 8, 8 /
41, 41, 41 / 46, 46, 46 / 57, 57, 57 / …; C220), so the barrier effect lives in the left half-line
alone and can be studied there without the right side.

### 5.2 Your idea: the wobble as the observer's perspective `Y`

What is now proved gives the arrow a precise place in the GLM:

* **It is exact as a local direction.** `−sign D(N)` is exactly the direction that moves the
  running frequency towards 1/2 (`deviation_decreases_iff`).
* **It carries no information about the limit.** New this round
  (`ArrowIndependence.lean`, `arrow_independent_of_frequency`): an arrow that never flips is
  compatible with frequency exactly 1/2 (Round 12), **and** an arrow that flips forever is
  compatible with a frequency that does not tend to 1/2 (`exists_flipping_arrow_unbalanced`:
  ones on the dyadic blocks `[2^k − 1, 2^{k+1} − 1)` with `k` even; its wobble at the block ends is
  exactly `(1 − (−2)^k)/3`).
* **Space has a compass, the centre has none.** Rule 30's chirality fixes the read angle from row 2
  on, off the axis (`rule30_spin_readable`, `rolled_seam_visible`), but the centre column cannot
  tell 30 from its mirror 86 (`centre_column_class`).

**Suggested GLM design.** Treat `Y` as a pair (arrow, compass): the arrow `−sign D(N)` and the scale
`z = D/√N` (`WobbleNormalized.lean`) for "which way the run is heading now", and the chirality seam
for "which way we are facing". Use it to steer a run (which reading to make next) and never as a
stopping or success criterion: `arrow_independent_of_frequency` proves it cannot certify convergence, and
`no_finite_certificate_problem2` proves that no finite reading can.

**Round 21: which way the observer faces matters.** Put `Y` on a column that is proposed to be
periodic. Facing **left**, `Y` sees a deterministic machine (the half-line driven by the column) and
receives a test at every black time of the column, because then the column's update involves only
its left neighbour (`col_black_forces_left`). Facing **right**, `Y` never receives a test on its own:
at white times the update couples both neighbours, and any column sequence is realised by some row
(`column_inverse_exists`). So the direction that can *refute* a periodicity proposal is the left one,
and it is the finite left edge that makes the test bite. For the GLM this suggests a second
component of the frame: besides the arrow (which way the run is heading) and the compass (which way
the pattern faces), a **refutation side** (from which side a proposal can be checked).

### 5.3 Make the GLM read its knowledge from the checked package

The theorem wheel's statements, spokes and negative controls were entered by hand in each round.
`Frontier.lean` now holds the whole frontier as six checked theorems, and `claims.csv` gives every
claim an evidence class and a Lean name. A small generator (claims.csv → wheel carriers, with a
check that every cited Lean name exists and a recorded `#print axioms` footprint) would keep the
GLM's "missing pieces" report correct automatically as the package grows.

### 5.4 Where a proof of P1 would have to live

Taken together, the blocked routes say that a proof of P1 must
* use the specific seed (E2: map properties are shared with the all-white row);
* not rely on high-degree ANF facts *alone* (E8: they do not establish the seed result by
  themselves). *Softened in R27:* this does not exclude a proof that connects high-degree structure
  to seed-specific behaviour through an additional theorem; it blocks that one implication only;
* be infinite in character (E6: no finite prefix decides it);
* give a truth that transports correctly under the mirror (the centre column cannot tell 30 from
  86). *Softened in R27:* the proof itself need not be mirror-symmetric; it may use Rule 30's
  left-permutive orientation (as the half-line machine does) and then transport to Rule 86.

A blocked implication prevents repeating that implication; it does not prohibit later bridges
from the same source facts. The conjecture loop should treat blocked routes this way.

The two lines that satisfy all four are the stack lift with run bounds and AP-balance of the
seed. Round 21 sharpened the first: the stack lift needs only the left half-line
(`problem1_of_halfLineDies`). We recommend concentrating on §4 items 1–2.

---

## 6⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺. What Rounds 43–48 added

| Round | File | Content | Class |
|---|---|---|---|
| 43 | `../Escalation/LayerStack.lean`, `MasterStep.lean`, `GolayTies.lean`, `Rule30Parity.lean` | the escalation sketch checked (C393–C399) | FORMAL / CERT |
| 44 | `../Escalation/Niemeier.lean`, `LeechResidue.lean`; `../HypothesisEngine/WheelChecksData.lean`, `NeedsWheel.lean` | 23 Niemeier root systems; syndromes mod 8/144/256 coincide; wheel H16/H19; sound provisions (C400–C405) | FORMAL / CERT |
| 45 | `../HypothesisEngine/GateLoop.lean`, `GateLoopData.lean` | gate loop, typed rollback, cascade soundness; no period `≤ 64` with preperiod `≤ 30000` (C406–C410) | FORMAL / CERT |
| 46 | `../HypothesisEngine/Wheel.lean` | the wheel contract: only KNOWS asserts, sound turns, strict lifts (C411–C413) | FORMAL |
| 47 | `AdicTower.lean`, `AdicTowerData.lean` | P1 ⇔ the centre column is 2-adically irrational; no small fraction on layer 256 (C415, C416) | FORMAL / CERT |
| 47 | `AdicPeriod.lean` (+ `AdicTowerData.lean`) | the layer ↔ period dictionary; no `r/q` with `q ∣ 2^p − 1`, `p ≤ 500`, `|r| < 2^500` (C420, C421) | FORMAL / CERT |
| 47 | `MathieuCensus.lean`, `MathieuCensusOrbits.lean` | all 49 `M₂₄` orbits of 24-cell patterns, with tests and sizes (C417, C418; To Do 31) | CERT |
| 47 | `MathieuMOG.lean` | octad / sextet / trio stabiliser generators and their orbits (C419; To Do 33 partly) | CERT |
| 47 | `../../GLM.lean`, `../HypothesisEngine.lean` | one root for the whole package (`lake build RequestProject.GLM`) | DOC |
| 48 | `Triangles.lean` | the triangle law and its birth from black runs; left-down vs right-down lines; infinitely many endless left-down lines, no endless right-down line; right-edge bands with triangles of every size (C422–C426) | FORMAL |
| 48 | `TrianglesData.lean` | no white run `≥ 16` in the first 400 left diagonals ever; settled maxima `10` (400) and `16` (20000) (C427) | CERT |

## 6⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺. What Round 42 added

| File | Content | Class |
|---|---|---|
| `../HypothesisEngine/TaxChecks.lean` | `tax`, `TaxConserved`, `taxDefect`; `card_symmDiff_add_two_inter`, **`tax_defect_eq`**, **`tax_conserved_iff_defect_zero`**, `tax_conserved_of_right_empty`/`_left_empty`/`_of_eq`; `DocstringCriterion`, `docstring_iff_fails_disjoint`, `docstring_iff_fails_partial`, **`docstring_criterion_wrong`**; `windowPattern`, `windowPattern_eq_empty`, **`tax_conserved_at_doubling`** | FORMAL (C389, C390) |
| `../HypothesisEngine/TaxChecksData.lean` | `evPattern400`, **`tax_conserved_pairs_below_400`**, `tax_conserved_nontrivial_below_400`, `not_eventuallyWhite_of_window`, **`tax_conserved_not_only_white`** | CERT (C391) |
| study folder `rule30_round42/` | audit of `hypothesis_engine_v13.py` (run); portable reasoning guards; v14 built from v13 by named patches | EMP (C392) |
| `claims.csv` | C374's notes field quoted (it had split into extra columns) | DOC |
| — | generate the implication graph from the ledger | still OPEN (To Do 50) |


## 6⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺. What Round 41 added

| File | Content | Class |
|---|---|---|
| `../HypothesisEngine/DialogueChecks.lean` | `lateBlip`, **`transient_read_does_not_imply_aperiodic`**; Thue–Morse (`thueMorse`, `thueMorse_double`, `thueMorse_double_add_one`, `tmStep`, `thueMorse_eq_dfa`, `thueMorse_not_eventuallyPeriodic`, **`aperiodic_but_automatic`**); `parityOn_congr`, **`doubling_law_tie_unsplittable`** | FORMAL (C384–C386) |
| study folder `rule30_round41/` | audit of `hypothesis_engine_v10.py`; the v11 self-dialogue (`glm_dialogue.py`, `knowledge.json`, `run_round41.py`); transcripts on Rule 30 and the eight benchmarks | EMP (C387, C388) |
| `HYPOTHESIS_ENGINE.md` §11, `../HypothesisEngine/README.md` | the Round 41 account | DOC |
| — | generate the implication graph from the ledger | OPEN (To Do 50) |

## 6⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺. What Round 40 added

| File | Content | Class |
|---|---|---|
| `Transients.lean` | `PerFrom`; settling (`white_of_window`, `perFrom_step`, `perFrom_linear`, `ldiagOf_perFrom_linear`, `ldiag_perFrom_linear`); odd white diagonals (`LeftMachine.shift`, `sync_two`, `eventuallyWhite_shift_iff`, `shift_sync`, `odd_white_complement_is_shift`, `next_white_independent_of_odd_bit`, `ldiagOf_shift_sync_after_odd_white`); the doubling read two out (`evenParityOn`, `parityOn_eq_evenParityOn`, `doubling_read_two_out`, `ldiag_doubling_read_two_out`); shift-equivalence (`parityOn_shift_arg`, `shift_equiv_extend`, `shift_equiv_extend_odd`) | FORMAL (C374–C377) |
| `TransientsData.lean` | `odd_white_bundle`; certificates for the odd white diagonals `2, 7, 28`; **`left_edge_rows_agree_up_to_shift`** | CERT (C378) |
| study folder `rule30_round40/` | bit-packed band with an exact settling certificate; random-row scans (H1–H4); run-up universality (H9) and its validation; the prediction at `1420878968`; refuted H7, H8 | EMP (C379–C383) |
| — | run-up universality; universality of the left side beyond `53207`; are the periods unbounded? | OPEN (To Do 45, 47–49) |

## 6⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺. What Round 39 added

| File | Content | Class |
|---|---|---|
| `WhiteDiagonals.lean` | `LeftMachine`; the white-diagonal criterion (`white_iff_coincide`, `ldiagOf_white_iff_coincide`, `ldiag_white_iff_coincide`); `no_two_consecutive_white`; forward/backward synchronisation (`sync_forward`, `sync_backward`); eventual keys (`evKey`, `eventuallyEq_of_evKey`); the regime dichotomy (`regime_finite_check`, `regime_periodic`, `ldiag_periodic_in_D_of_finitely_many_white`); **no last white diagonal** (`white_after_white`, `ldiag_white_after_white`, `ldiag_infinitely_many_white`); `OddWhiteAt`, `ldiag_periods_unbounded_iff` | FORMAL (C362–C367) |
| `../HypothesisEngine/Benchmarks.lean` | the engine's verdicts on 8 non-Rule-30 problems: `euler_dvd_iff`, `euler_composite_of_mod`, `fermat_five_not_prime`, `two_squares_law`, `moser_junction`, `moser_split`, `josephus_closed_form`, `josephus_eq_sim`, `gcd_trap_refuted` | FORMAL (C372) |
| `../HypothesisEngine/BenchmarksData.lean` | `euler_prime_below_40`, `collatz_reaches_one_below`, `gcd_trap_survives`, `midpoint_bug_iff_overflow`, `midpoint_fixed_correct` | CERT (C373) |
| study folder `rule30_round39/` | core v6 (residue and closed-form miners, junction resolution, evidence classes); the eight benchmarks; regime statistics for `Q ≤ 16`; the law-driven scan past 87867 (C program) | EMP (C368–C371) |
| `HYPOTHESIS_ENGINE.md` §7–9, `../HypothesisEngine/README.md` | the Round 39 account; the portable module and a playbook for GLM bottlenecks | DOC |
| — | the parities of the white diagonals (To Do 45, sharpened) | OPEN (C359, C367) |

## 6⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺. What Round 38 added

| File | Content | Class |
|---|---|---|
| `LeftDiagonalPeriods.lean` | `EvPer`, `EventuallyWhite`, `LeftDiagPeriodDivides`; the one-bit machine (`one_bit_reset`, `one_bit_doubles`, `one_bit_sync`); the period law (`ldiag_doubles`, `ldiag_keeps_of_even`, `ldiag_common_period`, `leftDiag_periods_bounded_of_finitely_many_white`, `infinitely_many_white_of_unbounded`); seed-forgetting (`ldiagOf_sync`, `first_difference_after_white`) | FORMAL (C351–C353) |
| `LeftDiagonalPeriodsData.lean` | `leftDiag_period_eight_below_400`, `not_leftDiagPeriodDivides_eight`, `leftDiag_period_sixteen_below_87867`, `not_leftDiagPeriodDivides_sixteen`, `leftDiag_white_below_87868`, `seed_first_difference`, `centerCol_read_in_transient` | CERT (C354–C358) |
| study folder `rule30_round38/` | the v5 hypothesis engine, the generic core, the v4/v5 benchmark | EMP (C360–C361) |
| `HYPOTHESIS_ENGINE.md` | the engine design, the benchmark and the results | DOC |
| — | are left-diagonal periods unbounded? | OPEN (C359) |

## 6⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺. What Round 37 added

| File | Content | Class |
|---|---|---|
| `TurnCost.lean` | the exact cost of a turn (`testSlack_of_shift_exact`, `testSlack_of_shift_count`, `testSlack_phase_transfer`, `testSlack_wheelTurn_transfer` and their `…UpTo…` forms); the observer's best phase (`wordDies_of_phase`, `testCountLinear_of_phases`, `wheelDies_of_phases`); periods 2 and 3 from their best phases (`testCountLinear_two_of_phase`, `testCountLinear_three_of_phases`) | FORMAL (C343–C344) |
| `OneRunFamily.lean` | the hub family `1^(q−1)0`: `wheelRep_oneRun`, `failsWithinTests_of_initial_blackRun`, `oneRun_band`, `oneRunDies_iff_long`, `OneRunFamilyDies`, `OneRunFamilyDiesFrom`, `halfLineDies_two_of_oneRunFamily`, `oneRunFamilyDiesFrom_of_wheelDies` | FORMAL (C347), OPEN (C349) |
| `TurnCostData.lean` | best phases of periods 2 and 3 with their exact least slacks on `d ≤ 40`, `d ≤ 32`; the attained turn costs; `frontier_round37` | CERT (C345) |
| `scripts/wheel_phases37.py`, `scripts/one_run_family37.py` | the per-phase measurement and the family measurement (outputs in the study folder `rule30_round37/`) | EMP (C346, C348) |
| `TURN_COST.md` | the plain-language account, the measured tables and the exact improvement requirements | DOC |

## 6⁺⁺⁺⁺⁺⁺⁺⁺⁺⁺. What Round 36 added

| File | Content | Class |
|---|---|---|
| `DriveWheel.lean` | the drive wheel: turns (`wheelTurn`, `driveN_wheelTurn`, `wheelTurn_add`, `wheelTurn_mod`), inner wheels (`period_gcd`, `driveN_eq_of_period`), hubs (`WheelRep`, `exists_wheelRep`), `halfLineDies_iff_wheel`, `WheelDies`, `wheelDies_iff`, `problem1_of_wheelDies`, `wheelDies_iff_periodic`; on the observer's clock `testSlack_wheelTurn`, `testCountLinear_of_wheel`, finite-range `testSlackUpTo_of_wheel` | FORMAL (C338–C340) |
| `DriveWheelData.lean` | hub counts to period 12 (`wheelReps_count`); one table for all 70 hubs of period `≤ 8` on `d ≤ 24` (`wheelTable_check`, `wheelTable_complete`); per-period laws for every `p ≤ 8` (`testCountLinearUpTo_wheel`); run bounds for periods 7 and 8 (`runBound_wheel_seven`, `runBound_wheel_eight`); `frontier_round36` | CERT (C341–C342) |
| `WHEEL.md` | the plain-language account: what the wheel is, what it saves, what it cannot do | DOC |

## 6⁺⁺⁺⁺⁺⁺⁺⁺⁺. What Round 35 added

| Item | Result | Class |
|---|---|---|
| `DiagonalSearch.lean` | verified diagonal search: prefix xor in logarithmic rounds (`pxor`), exact new diagonal (`nextDiag_spec`), soundness (`diagSearch_sound`, `dDiesBy_of_diagSearch`), drop-in checks (`drivenCheck_of_diagCheck`, `halfLineLinear_upTo_of_diagCheck`) — To Do 37 | FORMAL (C332) |
| `DiagCert.lean`, `DiagCertTwo.lean`, `DiagCertThree.lean`, `DiagCertFour{1,2,4,8,Rest}.lean`, `DiagonalSearchData.lean` | least observer-clock slacks exactly 5 (p = 2, `d ≤ 42`), 8 (p = 3, `d ≤ 32`), 7 (p = 4, `d ≤ 32`); bridge to run bounds in every left-white row (`drivenRunBoundUpTo_of_testCountLinearUpTo`) and the bounds `2(d+5)`, `3(d+8)`, `4(d+7)` (`frontier_round35`) | CERT (C333, C335), FORMAL (C334) |
| `BlackRunWindow.lean` | a black run is one window read (`blackRun_window`, `blackRun_word`, `blackPair_window`); long black runs kill every code, for every drive (`dDiesBy_of_long_blackRun`) — To Do 36 | FORMAL (C336) |
| timings | diagonal vs prefix search (C337) | EMP |

## 6⁺⁺⁺⁺⁺⁺⁺⁺. What Round 34 added

| Item | Result | Class |
|---|---|---|
| `TestCountPeriods.lean` | divisor rule (`driveN_repeat`, `testCountLinear_of_dvd`, `halfLineDies_of_dvd`, `not_testCountLinear_of_dvd`, `testCountLinear_slack_ge_of_dvd`); the observer's phase (`TestSlack`, `halfStep_length`, `testSlack_of_shift`, `testSlack_of_shift_white`, `testSlack_of_shift_iter`) | FORMAL (C325, C326) |
| `SlackCert.lean`, `SlackCertFour{1,2,4,8,Rest}.lean`, `SlackCertThreeTwo.lean`, `TestCountPeriodsData.lean` | least period-4 slack on `d ≤ 30` is exactly 7; slack 8 (p = 3) on `d ≤ 28`; slack 5 (p = 2) on `d ≤ 34`; refutations lifted to all multiples (`frontier_round34`) | CERT (C327) |
| study folder `rule30_round34/` | exact excess search `test_slack34.c` (C328, C329); alive counts `alive_decay34.c` (C331) | EMP |
| GLM (`rule30_round34/`) | `tool slack`; the divisor rule and lifted refutations in the wheel; `tool clock`, `tool next` on the Round 34 frontier; consultation 1/7 → 7/7 (development set) | GLM (C330) |
| `TEST_COUNT.md` | guide to the observer's clock (Rounds 33–34) | docs |

## 6⁺⁺⁺⁺⁺⁺⁺. What Round 33 added

| Item | Result | Class |
|---|---|---|
| `TestCountLaw.lean` | observer clock (`testsBefore`, `FailsWithinTests`); the uniform law refuted (`not_testCountBound`); the per-period law gives the rung and, for all periods, P1; slack must grow with the period | FORMAL (C313–C315) |
| `TestCountLawData.lean` | least slack 5, 8, 5 on `d ≤ 22` for `p = 2, 3, 4`, one smaller refuted for all `d` (`frontier_round33`); period 4 needs slack ≥ 7 (`not_testCountLinear_four_six`) | CERT (C316, C323) |
| `TestHalving.lean`, `TestHalvingData.lean` | halving gives the test-count law; excess 6 on `d ≤ 18` (p = 2), `d ≤ 16` (p = 4); excess 5 (p = 2) and 6 (p = 4) refuted (`frontier_round33_halving`) | FORMAL (C321), CERT (C322) |
| `SidewaysPeriodTwo.lean` | period 2 sideways: columns 2–5 in closed form, three forced survivor bits | FORMAL (C318) |
| scripts | `word_lifetimes33.c`, `test_halving34.c`, `sideways_period_two.py`; `ledger_check.py` now runs Lean in chunks (a single run overflowed Lean's stack and silently dropped names) | EMP (C317, C319, C324) |
| GLM (`rule30_round33/`) | wheel to Round 33 with the instantiation rule; lens reader; `tool clock`; `tool next`; consultation 9/9 (development set) | EMP (C320) |

## 6⁺⁺⁺⁺⁺⁺. What Round 32 added

| Item | Result | Class |
|---|---|---|
| `MathieuOrbits.lean` | the `M₂₄` action on 24-cell patterns; the 12-row test; the orbit tool with checkable certificates (`certOK_reach`); only rotations commute with Rule 30 (`commutes_iff_rot`); the pigeonhole bound (`shared_card_le_of_not_one`) | FORMAL (C304–C307) |
| `MathieuOrbitsData.lean` | generators `gM0`, `gM1`; orbits for 1–7 cells, octads, dodecads, each equal to an explicit set | CERT (C308–C309) |
| `MathieuRule30Data.lean` | no 24-cycle in any labelling (`no_rot_one`); at most 12 shared symmetries, 12 attained, 2 in the GLM labelling; symmetric seeds with different futures | CERT (C310–C311) |
| scripts | `m24_search.py`, `m24_orbit_census.c` (49 orbits), `m24_rule30_octads.c` (exact integer arithmetic) | EMP (C312) |

## 6⁺⁺⁺⁺⁺. What Round 31 added

| Item | Result | Class |
|---|---|---|
| `SidewaysView.lean` | the sideways reconstruction `recon`; survival ⟺ an admissible first column reconstructs the row (`survives_iff_sideways`, `halfLineDies_iff_sideways`); period 1 in one line (`halfLineDies_one_sideways`); infinite rows survive every drive (`infinite_row_survives`, To Do 20); no uniform death time (`survivor_for_every_horizon`) | FORMAL (C297–C300) |
| `BarrierDiagonalsData.lean` | exact `Lmax` for `100, 110, 1000, 1100, 1110`, `d ≤ 20` (`lmaxWord_spec`); the barrier diagonal depends on the word (`barrier_depends_on_word`); 28 distinct diagonals for `10`, `d ≤ 32` (`barrier_set_not_small_two`); `frontier_round31` — To Do 3 | CERT (C301–C302) |
| scripts | exact arithmetic only: `post_edge_halving.c` prints exact fractions, `tuning_by_ear.py` uses `bit_length`; new `barrier_diagonals.c` (integer only) | EMP / housekeeping (C303) |

## 6⁺⁺⁺⁺. What Round 30 added

| Item | Result | Class |
|---|---|---|
| `Pipeline.lean` | one pipeline: goal regression and fitted middle steps (`run_append_eq_some_iff_runBack`, `semMid_eq_some_iff`, `shapePrune_skip`), ask loop (`askFilter_card_lt`, `askLoop_questions_lt`, `askLoop_correct`), Occam gate (`minAgree_wrong_imp`, `gated_correct`, `gate_can_fix`, `gate_can_drop_truth`) | FORMAL (C289–C291) |
| `PipelineData.lean` | the statement frontier generated by the pipeline, 30 points certified sharp (`frontier_round30`) | CERT (C292) |
| GLM pipeline (`rule30_round30/`) | fresh held-out 56 → 96 of 132 right (stage 1), 106 with ≤ 5 questions; ask loop 48 → 77 on Round 28 held-out; Occam gate for k ≤ 2; planner over statements vs Round 27; GLM regression unchanged | EMP (C293–C296) |

## 6⁺⁺⁺. What Round 29 added

| Item | Result | Class |
|---|---|---|
| `PlanSearch.lean` | multi-step plans: composition and goal regression; merged breadth-first layers lose nothing (`layer_complete`) and decide consistency and agreement (`agree_iff_layer`); the planner never answers above the shortest explanation and is correct under the Occam premise (`planner_correct`, `minAgree_correct`); the separating example (`separating_example_refutes`) | FORMAL (C283) |
| negative controls | the rule can be wrong without the Occam premise (`minAgree_needs_occam`); merging on demonstrations alone is unsound (`train_only_signature_unsound`) | FORMAL (C284) |
| `InnerSurvivorData.lean` | `InnerFollows a` refuted for `a ≤ 7` (witness `d = 14`, code `11083`) — To Do 22 | CERT (C285) |
| GLM planner (`rule30_round29/`) | stored ARC 1 → 10 right, 0 wrong; held-out multi-step 12 → 96 of 132 right, 0 wrong; Round 28 held-out 24 → 48 of 84, 0 wrong; regression suites unchanged | EMP (C286–C288) |

## 6⁺⁺. What Round 28 added

| File | Content | Class |
|---|---|---|
| `LocalRuleInduction.lean` | `Reading`, `Reproduces`, `KeyOK`, `Seen`; **`reproduces_iff_keyOK`**, **`consistent_iff`**, `reproduces_update`, **`determined_iff_keyDetermined`**, `keyOK_antitone`, `not_consistent_mono`, `plain`, **`determined_iff_seen`**, **`answer_determined_iff_covered`**, **`survivor_correct`**, **`clash_refutes`**, `plain_consistent_iff` | FORMAL (new) |
| `glm/r28_wheel.json`, `glm/README.md` | the ledger as GLM carriers, and how to install them | hand-off |
| study folder `rule30_round28/` | `setup_round28.sh`, `apply_round28.py`, `test_round28.py`; `local_rule_induction.py` and `theorem_wheel_round28.py` (GLM overlay); `local_rule_arc.py`, `r28_benchmark.py`, `inner_survivors.py`, `word_lifetimes.c`, with outputs | GLM code / EMP |
| `PROJECT_DIRECTIVE.md`, `README.md` (rewritten as a map), `HISTORY.md` (the round record, re-ordered), `DEVELOPMENT.md` (revised) | documentation | — |
| `claims.csv` C277–C282, `HISTORY.md` (Round 28), this file | documentation | — |

## 6⁺. What Round 27 added

| File | Content | Class |
|---|---|---|
| `PostEdgeSpec.lean` | `halfStateD_width`, **`halfStateD_strictMono`**, `halfStateD_ne`, `halfStateD_phase_ne`, **`window_not_closed`**, `halfStep_mod`, **`colHistory_determines`**, `innerCol`, `halfStateD_shiftRight`, **`inner_never_fails`**, **`inner_alternation_bound`**, `innerCol_breaks` | FORMAL (new) |
| `ProofRoutes.lean` | `Ranking`, `ranking_dies_by`, **`wordDies_of_ranking`**, `not_ranking_of_window`, `WidthStep`, **`wordDies_of_widthStep`**, `not_widthStep_of_witness`, `halfLineDies_two_of_routes` | FORMAL (new) |
| `ProofRoutesData.lean` | **`lmaxTwo_spec`** (exact `Lmax d`, `d ≤ 32`), `rankPot`, **`no_declared_ranking`**, **`not_widthStep_two`**, **`shared_inner_survivor`**, `witnesses_merge`, `Round27Open` (OPEN), `frontier_round27` | CERT / refutations |
| `scripts/post_edge_witnesses.py`, `scripts/progress_measures.py`, `scripts/candidate_benchmark.py` (+ outputs, candidate records) | witness dataset and plateaus; declared progress measures and their smallest counterexamples; measured candidate generation | EMP / GLM prototype |
| `claims.csv` C269–C276, `HISTORY.md` (Round 27), this file | documentation | — |

## 6. What Round 26 added

| File | Content | Class |
|---|---|---|
| `ConjectureLoop.lean` | the loop for candidate statements: `refuted_of_fail`, `loop_prunes_false`, `narrow_mono`, `narrow_le_of_holds`, `narrow_bounded_iff`, **`narrow_eventually_eq`**, `Junction`, **`junction_split`**, `junction_forever_iff`, `meet`, `survivesTo_meet_of_junction`, `analogy_transport_unsound` | FORMAL (new) |
| `EchoBound.lean` | **`excess_le_iff_not_echo`**, `tuneExcessBound_iff_noEcho`, `EchoLogBound`, `echoLogBound_mono`, `problem1_of_echoLogBound`, `excess_succ_le`, sorting certificates (`repeatFree_of_check`, `echoLogBound_upto_of_check`, `not_echoLogBound_of_echo`) | FORMAL (new) |
| `AmortizedHalving.lean` | `aliveCodes`, `WindowHalving`, `not_windowHalving_of_plateau`, `AmortizedHalving`, **`halfLineDies_of_amortized`**, `amortizedHalvingUpTo_of_check`; `WordDies`, `wordDies_shift_iff_of_periodic`, **`halfLineDies_two_iff`**, **`halfLineDies_three_iff`** | FORMAL (new) |
| `ConjectureLoopData.lean` | `tuneExcessLog_upto_131072`, sharp echo frontiers and refutations, `not_windowHalving_two`, `amortizedHalvingUpTo_2_4_1`, `amortizedHalvingUpTo_3_4_1`, `not_amortizedHalving_2_4_0`, `not_amortizedHalving_3_4_0`, `not_halfLineLinear_two_one_two`, `not_halfLineLinear_three_one_two`, `analogy_rule86_rule30`, `frontier_round26` | CERT / refutations |
| `scripts/conjecture_loop.py`, `scripts/echo_profile.c` | the loop run (4 rounds); echo profile to `10⁶` | EMP |
| `claims.csv` C258–C268, `HISTORY.md` (Round 26), this file | documentation | — |

## 6⁰. What Round 25 added

| File | Content | Class |
|---|---|---|
| `TuningByEar.lean` | the general loop: `pruned_forever`, `survives_of_eq`, `eq_of_survives_all`, `finite_lockIn`, `graded_settles_iff`, `tuneIndex_eventually`, `tuneIndex_diverges`, `no_finite_confirmation`; the periodic instrument: `tuneCost`, `periodic_of_tuneCost_bounded`, `resolution_iff`, `eventuallyPeriodic_iff_tuneCostBounded`, **`problem1_iff_tuneCost_unbounded`**, `lcProfile_le_tuneCost`, `TuneExcessBound`, `TuneExcessLog`, `problem1_of_tuneExcessLog` | FORMAL (new) |
| `TuningByEarData.lean` | `tuneExcess_le_16`, `tuneExcess_16_sharp`, `tuneExcessLog_upto`, `tuneCost_centerCol_19999`, `frontier_round25` | CERT |
| `scripts/tuning_by_ear.py` | tuning profile to `n = 3000` | EMP |
| `claims.csv` C250–C257, `HISTORY.md` (Round 25), this file | documentation | — |

## 6′. What Round 23 added

| File | Content | Class |
|---|---|---|
| `PowerSeriesLadder.lean` | 2-kernel and automaticity (`isTwoAutomatic_of_eventuallyPeriodic`, `problem1_of_centreNotTwoAutomatic`, kernel criterion); linear complexity (`eventuallyPeriodic_iff_lcBounded`, **`problem1_iff_lcUnbounded`**); Hankel (`le_lcProfile_of_hankel_det`, checked-inverse certificate `hankel_det_ne_zero_of_check`); Morse–Hedlund (**`problem1_iff_complexity`**); `draftComplexityForm_iff` | FORMAL (new) |
| `RunCountLaw.lean` | `evolve_flip_left` (left-permutivity on the whole line); **`runCount_law`** | FORMAL (new) |
| `PowerSeriesLadderData.lean` | `det (hankel centerCol 10000) ≠ 0`; `lcProfile_centerCol_19999`; `no_eventual_period_below_10000`; `complexity_centerCol_eq`; `twoKernel_centerCol_ge`; refutations of the draft's counting-law endpoint and deficit monotonicity; `frontier_powerSeries` | CERT |
| `scripts/run_count.py`, `scripts/hankel_rank.c` | counting-law table; Hankel ranks | EMP |
| `claims.csv` C230–C239, `HISTORY.md` (Round 23), this file, `DEVELOPMENT.md` §6 | documentation | — |

## 6a. What Round 22 added

| File | Content | Class |
|---|---|---|
| `HalfLineLightCone.lean` | light cone, left-permutivity, `dDiesBy_congr`; **`survivors_card`** (exact count of codes passing the checks before time `k`, every drive) | FORMAL (new) |
| `PrefixSearch.lean` | sound prefix search; `drivenCheck_of_prefixCheck`; `halfDiesBy_eq_dDiesBy`; `HalfLineLinear p a b` and `halfLineDies_of_linear` | FORMAL (new) |
| `PrefixSearchData.lean` | period-2 linear target to `d = 36`; periods 3–6 linear targets and run bounds to `26/23/21/19`; `frontier_prefixSearch` | CERT |
| `scripts/prefix_search.c` | exact machine bounds (period 2 to `d = 46`, periods 3–6 to `39/35/33/31`) | EMP |
| `scripts/post_edge_halving.c` | survivors after the edge: approximate halving continues | EMP |
| `claims.csv` C222–C229, `HISTORY.md` (Round 22), this file, `DEVELOPMENT.md` §6 | documentation | — |

## 6b. What Round 21 added

| File | Content | Class |
|---|---|---|
| `PeriodTwoHalfLine.lean` | the half-line machine for an alternating column; exactness, soundness; `PeriodTwoHalfLineDies → LeftWhiteAperiodic 2` | FORMAL (new) |
| `PeriodTwoHalfLineData.lean` | alternating period-2 runs certified to `d = 24`; machine bounds exact and `≤ 2d + 8`; `PeriodTwoHalfLineLinear` | CERT |
| `HalfLineMachine.lean` | the driven machine for every period; `HalfLineDies p → LeftWhiteAperiodic p`; all `p` → P1; `HalfLineDies 1` proved; `blackRun_bound` (`≤ d + 1`) | FORMAL (new) |
| `HalfLineMachineData.lean` | driven run bounds, periods 3–6, further out than before; `frontier_halfLine` | CERT |
| `scripts/half_line_search.py` | the machine bound by the half-speed search, to `d = 42` | EMP |
| `scripts/ledger_check.py` | ledger check (names, axioms, classes) and wheel-carrier export | tool |
| `DEVELOPMENT.md` | how to iterate development rounds | docs |
| `claims.csv` C213–C221, `HISTORY.md` (Round 21), this file (§1, §2.2, §3.1, §4, §5.1) | documentation | — |

## 6c. What Round 20 added

| File | Content | Class |
|---|---|---|
| `Frontier.lean` | the frontier as six checked theorems: proved partial results, sufficient targets, restatements, blocked routes, the strict weakening `SeedAPBalanced` vs `SeedFSTypical`, the observer frame | FORMAL (re-packaging) |
| `ArrowIndependence.lean` | the arrow can flip forever with frequency not tending to 1/2; with Round 12, the arrow is logically independent of P2 | FORMAL (new) |
| `ShortcutNetworkData.lean` | two linter warnings fixed (no change to statements) | — |
| `AUDIT.md`, `claims.csv` (C211–C212, superseded notes), `README.md` | documentation | — |
