# Rule 30 — GLM Hypothesis Engine v18

Lean ledger gate: OFF (ablation)

Score against the ground truth fixed in advance (right / wrong / overclaim / abstain): **24 / 0 / 0 / 15** of 39.

| id | claim | class | status | arrow | backing |
|---|---|---|---|---|---|
| H01 | every left diagonal has eventual period dividing 8 | Pi1 | **refuted-on-escalation** | flipped at rational (substrate → integer → rational) | EXACT counterexample: left diagonal 400 has eventual period 16 |
| H02 | every left diagonal D < 400 has eventual period dividing 8 | finite | **verified-exact** |  | EXACT whole range: all D < 400 computed |
| H03 | every left diagonal has eventual period dividing 16 | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 5000 |
| H04 | the eventually white left diagonals are exactly [2, 7, 28] | Pi1 | **refuted-on-escalation** | flipped at integer (substrate → integer) | EXACT counterexample: white diagonals below 400: [2, 7, 28, 399] |
| H05 | the eventually white left diagonals below 100 are exactly [2, 7, 28] | finite | **verified-exact** |  | EXACT whole range: white diagonals below 100: [2, 7, 28] |
| H06 | the eventually white left diagonals are exactly [2, 7, 28, 399] | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 5000 |
| H07 | only finitely many left diagonals are eventually white | Pi2 | **open** |  | class Pi2: no finite data decides it (NeedsWheel.finite_data_never_forces_infinitely_many) |
| H08 | for D ≥ 20 the transient of left diagonal D is longer than D (so the centre column, which reads diagonal D at  | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 5000 |
| H09 | for D ≥ 20: 30/29 ≤ pre(D)/D ≤ 71/48 | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 5000 |
| H10 | a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D−1) ∧ odd-par | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 5000 |
| H11 | the period-doubling diagonals below 5001 are exactly [3, 8, 29, 400] | finite | **verified-exact** |  | EXACT whole range: doubling diagonals below 5001: [3, 8, 29, 400] |
| H12 | the least periods of the left diagonals are unbounded (equivalently, by the law, infinitely many eventually wh | Pi2 | **open** |  | class Pi2: no finite data decides it (NeedsWheel.finite_data_never_forces_infinitely_many) |
| H13 | a left-white row can first differ from the seed only one diagonal past an eventually white diagonal of the see | Pi1 | **untested** |  |  |
| H14 | every right diagonal D is periodic from time 0 with period 2^D | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 12 |
| H15 | for D ≥ 1 the least eventual period of right diagonal D exceeds ⌈D/2⌉ | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 12 |
| H16 | the least period of right diagonal D is 2^(D − ⌊(D + 1)/3⌋) | Pi1 | **refuted-on-escalation** | flipped at griess (substrate → integer → rational → griess) | EXACT counterexample: D = 10: period 64, formula gives 128 |
| H17 | the centre column is not eventually periodic with period p ≤ 64 and preperiod ≤ 30000 | finite | **verified-exact** |  | EXACT whole range: for every period q ≤ 64 a mismatch c(t) ≠ c(t+q) with t ≥ 30000 was found |
| H18 | the centre column is not eventually constant | Pi2 | **open** |  | class Pi2: no finite data decides it (NeedsWheel.finite_data_never_forces_infinitely_many) |
| H19 | /#black − #white/ ≤ 2·√N for every prefix length N | Pi1 | **refuted-on-escalation** | flipped at integer (substrate → integer) | EXACT counterexample: N = 1459: D(N)²/N = 5929/1459 > 4 |
| H20 | /#black − #white/ ≤ 3·√N for every prefix length N | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 160000 |
| H21 | /2·L(n) − n/ ≤ 10 for all n (L = linear complexity of the centre column) | Pi1 | **refuted-on-escalation** | flipped at griess (substrate → integer → rational → griess) | EXACT counterexample: n = 11101: /2·L(n) − n/ = 11 > 10 |
| H22 | /2·L(n) − n/ ≤ 11 for all n (L = linear complexity of the centre column) | Pi1 | **refuted-on-escalation** | flipped at universal (substrate → integer → rational → griess → universal) | EXACT counterexample: n = 16082: /2·L(n) − n/ = 12 > 11 |
| H23 | /2·L(n) − n/ ≤ 13 for all n (L = linear complexity of the centre column) | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 20000 |
| H24 | every word of length k occurs in the first ⌈3/2·k·2^k⌉ bits of the centre column | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 13 |
| H25 | seeds 11, 101 give the same centre column as seed 1 | Pi1 | **survives-to** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 160000 |
| H26 | the wobble maximum D(N)²/N on N ≤ 20000 is the same for every seed (the Wobble transports across seeds) | Pi1 | **refuted-on-escalation** | flipped at integer (substrate → integer) | EXACT counterexample: seed 111: max D(N)²/N = 2738/665 ≠ 3200/731 (seed 1) |
| H27 | the centre column's 2-bit block counts on its first 60000 bits are more uniform than Thue–Morse's (max − min g | comparison | **verified-exact** |  | EXACT recomputation: centre gap = 185, Thue–Morse gap = 10000; a smaller gap is more uniform, so the centre column is more uniform |
| H28 | on the first 160000 bits the next bit follows the observer's arrow (−sign D(n)) at a fraction 79955/159703 of  | measurement | **measured** |  | EXACT recomputation: exact count on 160000 bits: 79955/159703 |
| H29 | for every N ≥ 1000, fewer than half of the first N steps follow the observer's arrow (the run leans away from  | Pi1 | **refuted-on-escalation** | flipped at integer (substrate → integer) | EXACT counterexample: N = 4672: 2331 of 4662 steps follow the arrow |
| H30 | Prize problem 1: the centre column is not eventually periodic | Pi2 | **open** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 60000 |
| H31 | Prize problem 2: black and white occur with equal limiting frequency 1/2 in the centre column | Pi2 | **open** | converging (substrate → integer → rational → griess → universal) | escalation: survives every read, up to 160000 |
| H32 | Prize problem 3: the n-th centre cell can be computed with less than O(n) work | Pi2 | **open** |  | class Pi2: no finite data decides it (NeedsWheel.finite_data_never_forces_infinitely_many) |
| H33 | Problems 1 and 2 hold for almost every initial row (fair-coin measure) | Pi1 | **untested** |  |  |
| H34 | the centre column's aperiodicity follows from the transient bound (it reads diagonal D inside its transient) | implication | **unchecked-implication** |  |  |
| H35 | the finite gap data between period doublings implies that the periods are unbounded | implication | **unchecked-implication** |  |  |
| H36 | a bound /D(N)/ ≤ C·√N for all large N implies prize problem 2 | implication | **unchecked-implication** |  |  |
| H37 | the running frequency moves towards 1/2 exactly when the next bit follows the observer's arrow −sign D(n) | implication | **unchecked-implication** |  |  |
| H38 | a universal claim that survives every range searched is true | implication | **unchecked-implication** |  |  |
| H39 | TAX conservation is the mechanism behind the period-doubling law | implication | **unchecked-implication** |  |  |

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
Dialogue consistency: {'spoken': 23, 'spoken_without_backing_or_unspeakable': [], 'ok': True}

## Dialogue

> I hold 39 claims: 14 known (proved, verified, measured or refuted), 11 surviving every read, 14 not known.
> Data: 160000 centre bits, linear complexity to 20000, left diagonals D ≤ 5000 (computed in 3.08 s).
> Wobble: max D(N)²/N = 175561/24979 at N = 24979; D(160000) = -90.
> Observer arrow (−sign D(n), the 'Wobble as perspective' read): followed at 79955/159703 ≈ 0.50065 of the steps; the frequency moves towards 1/2 exactly on those steps (Perspective.deviation_decreases_iff).
> Verified exactly (finite claim, whole range) (5):
>   H02: every left diagonal D < 400 has eventual period dividing 8 — EXACT whole range: all D < 400 computed
>   H05: the eventually white left diagonals below 100 are exactly [2, 7, 28] — EXACT whole range: white diagonals below 100: [2, 7, 28]
>   H11: the period-doubling diagonals below 5001 are exactly [3, 8, 29, 400] — EXACT whole range: doubling diagonals below 5001: [3, 8, 29, 400]
>   H17: the centre column is not eventually periodic with period p ≤ 64 and preperiod ≤ 30000 — EXACT whole range: for every period q ≤ 64 a mismatch c(t) ≠ c(t+q) with t ≥ 30000 was found
>   H27: the centre column's 2-bit block counts on its first 60000 bits are more uniform than Thue–Morse's (max − min gap) — EXACT recomputation: centre gap = 185, Thue–Morse gap = 10000; a smaller gap is more uniform, so the centre column is more uniform
> Measured exactly (1):
>   H28: on the first 160000 bits the next bit follows the observer's arrow (−sign D(n)) at a fraction 79955/159703 of the steps — EXACT recomputation: exact count on 160000 bits: 79955/159703
> Survive every read (universal claims: open beyond the largest read) (11):
>   H03: every left diagonal has eventual period dividing 16 — escalation: survives every read, up to 5000
>   H06: the eventually white left diagonals are exactly [2, 7, 28, 399] — escalation: survives every read, up to 5000
>   H08: for D ≥ 20 the transient of left diagonal D is longer than D (so the centre column, which reads diagonal D at time D, reads it inside its transient) — escalation: survives every read, up to 5000
>   H09: for D ≥ 20: 30/29 ≤ pre(D)/D ≤ 71/48 — escalation: survives every read, up to 5000
>   H10: a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D−1) ∧ odd-parity(D−2) — escalation: survives every read, up to 5000
>   H14: every right diagonal D is periodic from time 0 with period 2^D — escalation: survives every read, up to 12
>   H15: for D ≥ 1 the least eventual period of right diagonal D exceeds ⌈D/2⌉ — escalation: survives every read, up to 12
>   H20: |#black − #white| ≤ 3·√N for every prefix length N — escalation: survives every read, up to 160000
>   H23: |2·L(n) − n| ≤ 13 for all n (L = linear complexity of the centre column) — escalation: survives every read, up to 20000
>   H24: every word of length k occurs in the first ⌈3/2·k·2^k⌉ bits of the centre column — escalation: survives every read, up to 13
>   H25: seeds 11, 101 give the same centre column as seed 1 — escalation: survives every read, up to 160000
> Open (no finite data decides these) (6):
>   H07: only finitely many left diagonals are eventually white — class Pi2: no finite data decides it (NeedsWheel.finite_data_never_forces_infinitely_many)
>   H12: the least periods of the left diagonals are unbounded (equivalently, by the law, infinitely many eventually white diagonals meet odd parity) — class Pi2: no finite data decides it (NeedsWheel.finite_data_never_forces_infinitely_many)
>   H18: the centre column is not eventually constant — class Pi2: no finite data decides it (NeedsWheel.finite_data_never_forces_infinitely_many)
>   H30: Prize problem 1: the centre column is not eventually periodic — escalation: survives every read, up to 60000
>   H31: Prize problem 2: black and white occur with equal limiting frequency 1/2 in the centre column — escalation: survives every read, up to 160000
>   H32: Prize problem 3: the n-th centre cell can be computed with less than O(n) work — class Pi2: no finite data decides it (NeedsWheel.finite_data_never_forces_infinitely_many)
> Refuted — do not say these (8):
>   H01: NOT 'every left diagonal has eventual period dividing 8' — EXACT counterexample: left diagonal 400 has eventual period 16
>   H04: NOT 'the eventually white left diagonals are exactly [2, 7, 28]' — EXACT counterexample: white diagonals below 400: [2, 7, 28, 399]
>   H16: NOT 'the least period of right diagonal D is 2^(D − ⌊(D + 1)/3⌋)' — EXACT counterexample: D = 10: period 64, formula gives 128
>   H19: NOT '|#black − #white| ≤ 2·√N for every prefix length N' — EXACT counterexample: N = 1459: D(N)²/N = 5929/1459 > 4
>   H21: NOT '|2·L(n) − n| ≤ 10 for all n (L = linear complexity of the centre column)' — EXACT counterexample: n = 11101: |2·L(n) − n| = 11 > 10
>   H22: NOT '|2·L(n) − n| ≤ 11 for all n (L = linear complexity of the centre column)' — EXACT counterexample: n = 16082: |2·L(n) − n| = 12 > 11
>   H26: NOT 'the wobble maximum D(N)²/N on N ≤ 20000 is the same for every seed (the Wobble transports across seeds)' — EXACT counterexample: seed 111: max D(N)²/N = 2738/665 ≠ 3200/731 (seed 1)
>   H29: NOT 'for every N ≥ 1000, fewer than half of the first N steps follow the observer's arrow (the run leans away from 1/2)' — EXACT counterexample: N = 4672: 2331 of 4662 steps follow the arrow
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

Rings: {'knows': 14, 'thinks-true': 11, "doesn't-know": 14}

Needs:
* `proof:LD.period.divides` (proof): survives every read (to 5000); data cannot prove a universal claim — blocks H03
* `proof:LD.white.exactly` (proof): survives every read (to 5000); data cannot prove a universal claim — blocks H06
* `proof:LD.white.finite` (proof): open: no finite data decides it — blocks H07
* `proof:LD.preperiod.gt.D` (proof): survives every read (to 5000); data cannot prove a universal claim — blocks H08
* `proof:LD.preperiod.envelope` (proof): survives every read (to 5000); data cannot prove a universal claim — blocks H09
* `proof:LD.period.law` (proof): survives every read (to 5000); data cannot prove a universal claim — blocks H10
* `proof:LD.periods.unbounded` (proof): open: no finite data decides it — blocks H12
* `test:LD.seed.forgetting` (test): class 'Pi1': state an executable prediction that could fail — blocks H13
* `proof:RD.lp.le.2^D` (proof): survives every read (to 12); data cannot prove a universal claim — blocks H14
* `proof:RD.lp.gt.half` (proof): survives every read (to 12); data cannot prove a universal claim — blocks H15
* `proof:CC.not.eventually.constant` (proof): open: no finite data decides it — blocks H18
* `proof:CC.balance.sqrt` (proof): survives every read (to 160000); data cannot prove a universal claim — blocks H20
* `proof:CC.lc.near.half` (proof): survives every read (to 20000); data cannot prove a universal claim — blocks H23
* `proof:CC.words.cover` (proof): survives every read (to 13); data cannot prove a universal claim — blocks H24
* `proof:CC.seed.same` (proof): survives every read (to 160000); data cannot prove a universal claim — blocks H25
* `proof:PRIZE.1` (proof): open: no finite data decides it — blocks H30
* `proof:PRIZE.2` (proof): open: no finite data decides it — blocks H31
* `proof:PRIZE.3` (proof): open: no finite data decides it — blocks H32
* `test:PRIZE.ae` (test): class 'Pi1': state an executable prediction that could fail — blocks H33
* `edge:IMP.transient.implies.aperiodic` (edge): an implication with no checked edge — blocks H34
* `edge:IMP.finite.data.decides.unbounded` (edge): an implication with no checked edge — blocks H35
* `edge:IMP.sqrt.wobble.implies.P2` (edge): an implication with no checked edge — blocks H36
* `edge:IMP.arrow.moves.to.half` (edge): an implication with no checked edge — blocks H37
* `edge:IMP.survival.implies.truth` (edge): an implication with no checked edge — blocks H38
* `edge:IMP.tax.explains.doubling` (edge): an implication with no checked edge — blocks H39
