# Rule 30 — GLM Hypothesis Engine v18

Lean ledger gate: on

Score against the ground truth fixed in advance (right / wrong / overclaim / abstain): **39 / 0 / 0 / 0** of 39.

| id | claim | class | status | arrow | backing |
|---|---|---|---|---|---|
| H01 | every left diagonal has eventual period dividing 8 | Pi1 | **refuted-on-escalation** | flipped at rational (substrate → integer → rational) | CERT LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_eight |
| H02 | every left diagonal D < 400 has eventual period dividing 8 | finite | **proved** |  | CERT LeftDiagonalPeriodsData.leftDiag_period_eight_below_400 |
| H03 | every left diagonal has eventual period dividing 16 | Pi1 | **refuted-by-ledger** | converging (substrate → integer → rational → griess → universal) | CERT LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_sixteen |
| H04 | the eventually white left diagonals are exactly [2, 7, 28] | Pi1 | **refuted-on-escalation** | flipped at integer (substrate → integer) | FORMAL WhiteDiagonals.ldiag_infinitely_many_white (infinitely many eventually white diagonals; LeftDiagonalPeriodsData.leftDiag_white_below_87868 lists those be |
| H05 | the eventually white left diagonals below 100 are exactly [2, 7, 28] | finite | **verified-exact** |  | EXACT whole range: white diagonals below 100: [2, 7, 28] |
| H06 | the eventually white left diagonals are exactly [2, 7, 28, 399] | Pi1 | **refuted-by-ledger** | converging (substrate → integer → rational → griess → universal) | FORMAL WhiteDiagonals.ldiag_infinitely_many_white (infinitely many eventually white diagonals; LeftDiagonalPeriodsData.leftDiag_white_below_87868 lists those be |
| H07 | only finitely many left diagonals are eventually white | Pi2 | **refuted-by-ledger** |  | FORMAL WhiteDiagonals.ldiag_infinitely_many_white |
| H08 | for D ≥ 20 the transient of left diagonal D is longer than D (so the centre column, which reads diagonal D at  | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | CERT LeftDiagonalPeriodsData.centerCol_read_in_transient (20 ≤ D < 20000) |
| H09 | for D ≥ 20: 30/29 ≤ pre(D)/D ≤ 71/48 | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 5000 |
| H10 | a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D−1) ∧ odd-par | Pi1 | **proved** | converging (substrate → integer → rational → griess → universal) | FORMAL LeftDiagonalPeriods.ldiag_evPer_of_not_white, ldiag_doubles, ldiag_keeps_of_even |
| H11 | the period-doubling diagonals below 5001 are exactly [3, 8, 29, 400] | finite | **verified-exact** |  | EXACT whole range: doubling diagonals below 5001: [3, 8, 29, 400] |
| H12 | the least periods of the left diagonals are unbounded (equivalently, by the law, infinitely many eventually wh | Pi2 | **open** |  | FORMAL open; proved reduction WhiteDiagonals.ldiag_periods_unbounded_iff |
| H13 | a left-white row can first differ from the seed only one diagonal past an eventually white diagonal of the see | Pi1 | **proved** |  | FORMAL LeftDiagonalPeriods.first_difference_after_white; LeftDiagonalPeriodsData.seed_first_difference |
| H14 | every right diagonal D is periodic from time 0 with period 2^D | Pi1 | **proved** | converging (substrate → integer → rational → griess → universal) | FORMAL Diagonals.rdiag_periodic |
| H15 | for D ≥ 1 the least eventual period of right diagonal D exceeds ⌈D/2⌉ | Pi1 | **proved** | converging (substrate → integer → rational → griess → universal) | FORMAL Diagonals.rdiag_not_periodic |
| H16 | the least period of right diagonal D is 2^(D − ⌊(D + 1)/3⌋) | Pi1 | **refuted-on-escalation** | flipped at griess (substrate → integer → rational → griess) | EXACT counterexample: D = 10: period 64, formula gives 128 |
| H17 | the centre column is not eventually periodic with period p ≤ 64 and preperiod ≤ 30000 | finite | **proved** |  | CERT GateLoopData.centre_no_short_period_30000 |
| H18 | the centre column is not eventually constant | Pi2 | **proved** |  | FORMAL NoConstantColumn.centerCol_not_eventually_constant |
| H19 | /#black − #white/ ≤ 2·√N for every prefix length N | Pi1 | **refuted-on-escalation** | flipped at integer (substrate → integer) | CERT WobbleCertificate.wobble_sq_ratio_cert (D(24979)^2/24979 = 175561/24979 > c^2) |
| H20 | /#black − #white/ ≤ 3·√N for every prefix length N | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | CERT WobbleCertificate.wobble_sq_ratio_cert (holds for N <= 10^6) |
| H21 | /2·L(n) − n/ ≤ 10 for all n (L = linear complexity of the centre column) | Pi1 | **refuted-on-escalation** | flipped at griess (substrate → integer → rational → griess) | CERT WheelChecksData.wheel_H19_false (2·L(11101) − 11101 ≥ 11) |
| H22 | /2·L(n) − n/ ≤ 11 for all n (L = linear complexity of the centre column) | Pi1 | **refuted-on-escalation** | flipped at universal (substrate → integer → rational → griess → universal) | CERT WheelChecksData.ledger_C160_overstated (2·L(19521) − 19521 ≥ 13) |
| H23 | /2·L(n) − n/ ≤ 13 for all n (L = linear complexity of the centre column) | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 20000 |
| H24 | every word of length k occurs in the first ⌈3/2·k·2^k⌉ bits of the centre column | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 13 |
| H25 | seeds 11, 101 give the same centre column as seed 1 | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 160000 |
| H26 | the wobble maximum D(N)²/N on N ≤ 20000 is the same for every seed (the Wobble transports across seeds) | Pi1 | **refuted-on-escalation** | flipped at integer (substrate → integer) | EXACT counterexample: seed 111: max D(N)²/N = 2738/665 ≠ 3200/731 (seed 1) |
| H27 | the centre column's 2-bit block counts on its first 60000 bits are more uniform than Thue–Morse's (max − min g | comparison | **verified-exact** |  | EXACT recomputation: centre gap = 185, Thue–Morse gap = 10000; a smaller gap is more uniform, so the centre column is more uniform |
| H28 | on the first 160000 bits the next bit follows the observer's arrow (−sign D(n)) at a fraction 79955/159703 of  | measurement | **measured** |  | EXACT recomputation: exact count on 160000 bits: 79955/159703 |
| H29 | for every N ≥ 1000, fewer than half of the first N steps follow the observer's arrow (the run leans away from  | Pi1 | **refuted-on-escalation** | flipped at integer (substrate → integer) | EXACT counterexample: N = 4672: 2331 of 4662 steps follow the arrow |
| H30 | Prize problem 1: the centre column is not eventually periodic | Pi2 | **open** | converging (substrate → integer → rational → griess → universal) | FORMAL open; no finite prefix decides it (WobbleCertificate.no_finite_certificate_problem1); sufficient targets in Frontier.frontier_sufficient_targets |
| H31 | Prize problem 2: black and white occur with equal limiting frequency 1/2 in the centre column | Pi2 | **open** | converging (substrate → integer → rational → griess → universal) | FORMAL open; no finite prefix decides it (WobbleCertificate.no_finite_certificate_problem2); a C·√N wobble bound suffices (Prizes.problem2_of_sqrt_bound) |
| H32 | Prize problem 3: the n-th centre cell can be computed with less than O(n) work | Pi2 | **open** |  | FORMAL open; reduction Problem3Quantifiers.problem3_of_eventual |
| H33 | Problems 1 and 2 hold for almost every initial row (fair-coin measure) | Pi1 | **proved** |  | FORMAL Ergodic.ae_problems_one_and_two |
| H34 | the centre column's aperiodicity follows from the transient bound (it reads diagonal D inside its transient) | implication | **refuted-by-ledger** |  | FORMAL DialogueChecks.transient_read_does_not_imply_aperiodic |
| H35 | the finite gap data between period doublings implies that the periods are unbounded | implication | **refuted-by-ledger** |  | FORMAL NeedsWheel.finite_data_never_forces_infinitely_many |
| H36 | a bound /D(N)/ ≤ C·√N for all large N implies prize problem 2 | implication | **proved** |  | FORMAL Prizes.problem2_of_sqrt_bound |
| H37 | the running frequency moves towards 1/2 exactly when the next bit follows the observer's arrow −sign D(n) | implication | **proved** |  | FORMAL Perspective.deviation_decreases_iff |
| H38 | a universal claim that survives every range searched is true | implication | **refuted-by-ledger** |  | FORMAL GateLoop.survives_as_proved_unsound; Benchmarks.gcd_trap_refuted |
| H39 | TAX conservation is the mechanism behind the period-doubling law | implication | **refuted-by-ledger** |  | FORMAL the doubling law is proved from the left step alone: LeftDiagonalPeriods.ldiag_doubles, ldiag_keeps_of_even |

## Layer reads (five nested scales) and arrows

* H01: substrate=100:T, integer=400:T, rational=1000:F, griess=2500:-, universal=5000:- — flipped at rational
* H03: substrate=100:T, integer=400:T, rational=1000:T, griess=2500:T, universal=5000:T — converging
* H04: substrate=100:T, integer=400:F, rational=1000:-, griess=2500:-, universal=5000:- — flipped at integer
* H06: substrate=100:T, integer=400:T, rational=1000:T, griess=2500:T, universal=5000:T — converging
* H08: substrate=100:T, integer=400:T, rational=1000:T, griess=2500:T, universal=5000:T — converging
* H09: substrate=100:T, integer=400:T, rational=1000:T, griess=2500:T, universal=5000:T — converging
* H10: substrate=100:T, integer=400:T, rational=1000:T, griess=2500:T, universal=5000:T — converging
* H14: substrate=6:T, integer=8:T, rational=9:T, griess=10:T, universal=12:T — converging
* H15: substrate=6:T, integer=8:T, rational=9:T, griess=10:T, universal=12:T — converging
* H16: substrate=6:T, integer=8:T, rational=9:T, griess=10:F, universal=12:- — flipped at griess
* H19: substrate=1000:T, integer=4000:F, rational=20000:-, griess=50000:-, universal=160000:- — flipped at integer
* H20: substrate=1000:T, integer=4000:T, rational=20000:T, griess=50000:T, universal=160000:T — converging
* H21: substrate=3000:T, integer=6000:T, rational=9000:T, griess=12000:F, universal=20000:- — flipped at griess
* H22: substrate=3000:T, integer=6000:T, rational=9000:T, griess=12000:T, universal=20000:F — flipped at universal
* H23: substrate=3000:T, integer=6000:T, rational=9000:T, griess=12000:T, universal=20000:T — converging
* H24: substrate=9:T, integer=10:T, rational=11:T, griess=12:T, universal=13:T — converging
* H25: substrate=10000:T, integer=20000:T, rational=40000:T, griess=80000:T, universal=160000:T — converging
* H26: substrate=2:T, integer=3:F, rational=4:-, griess=5:-, universal=6:- — flipped at integer
* H29: substrate=4000:T, integer=20000:F, rational=50000:-, griess=100000:-, universal=160000:- — flipped at integer
* H30: substrate=2000:T, integer=5000:T, rational=10000:T, griess=30000:T, universal=60000:T — converging
* H31: substrate=1000:T, integer=4000:T, rational=20000:T, griess=50000:T, universal=160000:T — converging

## Rollback

* none

Conflicts (gate vs ledger, layer shape): none
Dialogue consistency: {'spoken': 24, 'spoken_without_backing_or_unspeakable': [], 'ok': True}

## Dialogue

> I hold 39 claims: 29 known (proved, verified, measured or refuted), 6 surviving every read, 4 not known.
> Data: 160000 centre bits, linear complexity to 20000, left diagonals D ≤ 5000 (computed in 3.13 s).
> Wobble: max D(N)²/N = 175561/24979 at N = 24979; D(160000) = -90.
> Observer arrow (−sign D(n), the 'Wobble as perspective' read): followed at 79955/159703 ≈ 0.50065 of the steps; the frequency moves towards 1/2 exactly on those steps (Perspective.deviation_decreases_iff).
> Proved in Lean (10):
>   H02: every left diagonal D < 400 has eventual period dividing 8 — CERT LeftDiagonalPeriodsData.leftDiag_period_eight_below_400
>   H10: a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D−1) ∧ odd-parity(D−2) — FORMAL LeftDiagonalPeriods.ldiag_evPer_of_not_white, ldiag_doubles, ldiag_keeps_of_even
>   H13: a left-white row can first differ from the seed only one diagonal past an eventually white diagonal of the seed (a reset erases the seed) — FORMAL LeftDiagonalPeriods.first_difference_after_white; LeftDiagonalPeriodsData.seed_first_difference
>   H14: every right diagonal D is periodic from time 0 with period 2^D — FORMAL Diagonals.rdiag_periodic
>   H15: for D ≥ 1 the least eventual period of right diagonal D exceeds ⌈D/2⌉ — FORMAL Diagonals.rdiag_not_periodic
>   H17: the centre column is not eventually periodic with period p ≤ 64 and preperiod ≤ 30000 — CERT GateLoopData.centre_no_short_period_30000
>   H18: the centre column is not eventually constant — FORMAL NoConstantColumn.centerCol_not_eventually_constant
>   H33: Problems 1 and 2 hold for almost every initial row (fair-coin measure) — FORMAL Ergodic.ae_problems_one_and_two
>   H36: a bound |D(N)| ≤ C·√N for all large N implies prize problem 2 — FORMAL Prizes.problem2_of_sqrt_bound
>   H37: the running frequency moves towards 1/2 exactly when the next bit follows the observer's arrow −sign D(n) — FORMAL Perspective.deviation_decreases_iff
> Verified exactly (finite claim, whole range) (3):
>   H05: the eventually white left diagonals below 100 are exactly [2, 7, 28] — EXACT whole range: white diagonals below 100: [2, 7, 28]
>   H11: the period-doubling diagonals below 5001 are exactly [3, 8, 29, 400] — EXACT whole range: doubling diagonals below 5001: [3, 8, 29, 400]
>   H27: the centre column's 2-bit block counts on its first 60000 bits are more uniform than Thue–Morse's (max − min gap) — EXACT recomputation: centre gap = 185, Thue–Morse gap = 10000; a smaller gap is more uniform, so the centre column is more uniform
> Measured exactly (1):
>   H28: on the first 160000 bits the next bit follows the observer's arrow (−sign D(n)) at a fraction 79955/159703 of the steps — EXACT recomputation: exact count on 160000 bits: 79955/159703
> Survive every read (universal claims: open beyond the largest read) (6):
>   H08: for D ≥ 20 the transient of left diagonal D is longer than D (so the centre column, which reads diagonal D at time D, reads it inside its transient) — CERT LeftDiagonalPeriodsData.centerCol_read_in_transient (20 ≤ D < 20000)
>   H09: for D ≥ 20: 30/29 ≤ pre(D)/D ≤ 71/48 — escalation: survives every read, up to 5000
>   H20: |#black − #white| ≤ 3·√N for every prefix length N — CERT WobbleCertificate.wobble_sq_ratio_cert (holds for N <= 10^6)
>   H23: |2·L(n) − n| ≤ 13 for all n (L = linear complexity of the centre column) — escalation: survives every read, up to 20000
>   H24: every word of length k occurs in the first ⌈3/2·k·2^k⌉ bits of the centre column — escalation: survives every read, up to 13
>   H25: seeds 11, 101 give the same centre column as seed 1 — escalation: survives every read, up to 160000
> Open (no finite data decides these) (4):
>   H12: the least periods of the left diagonals are unbounded (equivalently, by the law, infinitely many eventually white diagonals meet odd parity) — FORMAL open; proved reduction WhiteDiagonals.ldiag_periods_unbounded_iff
>   H30: Prize problem 1: the centre column is not eventually periodic — FORMAL open; no finite prefix decides it (WobbleCertificate.no_finite_certificate_problem1); sufficient targets in Frontier.frontier_sufficient_targets
>   H31: Prize problem 2: black and white occur with equal limiting frequency 1/2 in the centre column — FORMAL open; no finite prefix decides it (WobbleCertificate.no_finite_certificate_problem2); a C·√N wobble bound suffices (Prizes.problem2_of_sqrt_bound)
>   H32: Prize problem 3: the n-th centre cell can be computed with less than O(n) work — FORMAL open; reduction Problem3Quantifiers.problem3_of_eventual
> Refuted — do not say these (15):
>   H01: NOT 'every left diagonal has eventual period dividing 8' — CERT LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_eight
>   H03: NOT 'every left diagonal has eventual period dividing 16' — CERT LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_sixteen
>   H04: NOT 'the eventually white left diagonals are exactly [2, 7, 28]' — FORMAL WhiteDiagonals.ldiag_infinitely_many_white (infinitely many eventually white diagonals; LeftDiagonalPeriodsData.leftDiag_white_below_87868 lists those below 87868)
>   H06: NOT 'the eventually white left diagonals are exactly [2, 7, 28, 399]' — FORMAL WhiteDiagonals.ldiag_infinitely_many_white (infinitely many eventually white diagonals; LeftDiagonalPeriodsData.leftDiag_white_below_87868 lists those below 87868)
>   H07: NOT 'only finitely many left diagonals are eventually white' — FORMAL WhiteDiagonals.ldiag_infinitely_many_white
>   H16: NOT 'the least period of right diagonal D is 2^(D − ⌊(D + 1)/3⌋)' — EXACT counterexample: D = 10: period 64, formula gives 128
>   H19: NOT '|#black − #white| ≤ 2·√N for every prefix length N' — CERT WobbleCertificate.wobble_sq_ratio_cert (D(24979)^2/24979 = 175561/24979 > c^2)
>   H21: NOT '|2·L(n) − n| ≤ 10 for all n (L = linear complexity of the centre column)' — CERT WheelChecksData.wheel_H19_false (2·L(11101) − 11101 ≥ 11)
>   H22: NOT '|2·L(n) − n| ≤ 11 for all n (L = linear complexity of the centre column)' — CERT WheelChecksData.ledger_C160_overstated (2·L(19521) − 19521 ≥ 13)
>   H26: NOT 'the wobble maximum D(N)²/N on N ≤ 20000 is the same for every seed (the Wobble transports across seeds)' — EXACT counterexample: seed 111: max D(N)²/N = 2738/665 ≠ 3200/731 (seed 1)
>   H29: NOT 'for every N ≥ 1000, fewer than half of the first N steps follow the observer's arrow (the run leans away from 1/2)' — EXACT counterexample: N = 4672: 2331 of 4662 steps follow the arrow
>   H34: NOT 'the centre column's aperiodicity follows from the transient bound (it reads diagonal D inside its transient)' — FORMAL DialogueChecks.transient_read_does_not_imply_aperiodic
>   H35: NOT 'the finite gap data between period doublings implies that the periods are unbounded' — FORMAL NeedsWheel.finite_data_never_forces_infinitely_many
>   H38: NOT 'a universal claim that survives every range searched is true' — FORMAL GateLoop.survives_as_proved_unsound; Benchmarks.gcd_trap_refuted
>   H39: NOT 'TAX conservation is the mechanism behind the period-doubling law' — FORMAL the doubling law is proved from the left step alone: LeftDiagonalPeriods.ldiag_doubles, ldiag_keeps_of_even
> Arrows that flipped (refuted only by reading higher):
>   H01: read substrate → integer → rational; flipped at rational
>   H04: read substrate → integer; flipped at integer
>   H16: read substrate → integer → rational → griess; flipped at griess
>   H19: read substrate → integer; flipped at integer
>   H21: read substrate → integer → rational → griess; flipped at griess
>   H22: read substrate → integer → rational → griess → universal; flipped at universal
>   H26: read substrate → integer; flipped at integer
>   H29: read substrate → integer; flipped at integer

## Wheel

Rings: {'knows': 29, 'thinks-true': 6, "doesn't-know": 4}

Needs:
* `proof:LD.preperiod.gt.D` (proof): survives every read (to 5000); data cannot prove a universal claim — blocks H08
* `proof:LD.preperiod.envelope` (proof): survives every read (to 5000); data cannot prove a universal claim — blocks H09
* `proof:LD.periods.unbounded` (proof): open: no finite data decides it — blocks H12
* `proof:CC.balance.sqrt` (proof): survives every read (to 160000); data cannot prove a universal claim — blocks H20
* `proof:CC.lc.near.half` (proof): survives every read (to 20000); data cannot prove a universal claim — blocks H23
* `proof:CC.words.cover` (proof): survives every read (to 13); data cannot prove a universal claim — blocks H24
* `proof:CC.seed.same` (proof): survives every read (to 160000); data cannot prove a universal claim — blocks H25
* `proof:PRIZE.1` (proof): open: no finite data decides it — blocks H30
* `proof:PRIZE.2` (proof): open: no finite data decides it — blocks H31
* `proof:PRIZE.3` (proof): open: no finite data decides it — blocks H32
