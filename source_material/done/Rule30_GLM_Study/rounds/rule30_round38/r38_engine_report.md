# GLM Hypothesis Engine v5 — run report

Status counts: {'refuted-heldout': 6, 'survives': 11, 'refuted-by-prediction': 1, 'law-holds': 2, 'prediction-confirmed': 1, 'open': 1}

Predictions: [{'predicted': 87867, 'confirmed': True, 'white_diagonals_on_the_way': [53207, 58286, 87866]}]

| id | family | origin | status | statement | novelty | Lean |
|---|---|---|---|---|---|---|
| H01 | left-diagonals | lift | refuted-heldout | every left diagonal has eventual period dividing 8 | rediscovers C133 (EMP: periods ≤ 8 for D ≤ 200) | LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_eight (refuted) |
| H02 | left-diagonals | lift | survives | for D ≥ 20 the transient of left diagonal D is longer than D (the centre column, which reads diagonal D at time D, always reads it inside its transient) | rediscovers C133 (EMP: preperiod > D for 20 ≤ D ≤ 200) | partial: LeftDiagonalPeriodsData.leftDiag_transient_at_read certifies 20 ≤ D < 20000 only |
| H03 | left-diagonals | lift | survives | for D ≥ 20 the transient satisfies 30/29 ≤ pre(D)/D ≤ 71/48 (the exact extremes on the development range) | new to the ledger | not formalised |
| H04 | left-diagonals | lift | refuted-heldout | the eventually white left diagonals are exactly [2, 7, 28] | new to the ledger | LeftDiagonalPeriodsData.leftDiag_white_below_87868 (refutes it) |
| H05 | left-diagonals | cut | survives | every left diagonal D < 400 has eventual period dividing 8 | new to the ledger | LeftDiagonalPeriodsData.leftDiag_period_eight_below_400 |
| H06 | left-diagonals | narrow | refuted-by-prediction | every left diagonal has eventual period dividing 16 | new to the ledger | LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_sixteen (refuted) |
| H07 | left-diagonals | mechanism | refuted-heldout | a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D-1) | new to the ledger | not formalised |
| H08 | left-diagonals | mechanism | law-holds | a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D-1) ∧ odd-parity(D-2) | new to the ledger | LeftDiagonalPeriods.ldiag_evPer_of_not_white, ldiag_doubles, infinitely_many_white_of_unbounded |
| H09 | left-diagonals | prediction | prediction-confirmed | the first left diagonal with least eventual period 32 is D = 87867 | new to the ledger | LeftDiagonalPeriodsData.ldiag_87867_not_evPer_sixteen + leftDiag_period_sixteen_below_87867 |
| H10 | left-diagonals | cut | survives | every left diagonal D < 87867 has eventual period dividing 16 | new to the ledger | LeftDiagonalPeriodsData.leftDiag_period_sixteen_below_87867 |
| H11 | left-diagonals | lift | open | the least periods of the left diagonals are unbounded (equivalently, by the law, infinitely many eventually white diagonals meet odd parity) | new to the ledger | open; LeftDiagonalPeriods.infinitely_many_white_of_unbounded is the proved reduction |
| H12 | right-diagonals | lift | refuted-heldout | the least period of right diagonal D is 2^(D - floor((D + 1) / 3)) | new to the ledger | not formalised |
| H13 | right-diagonals | lift | survives | the least period of right diagonal D divides 2^D | rediscovers C48 (FORMAL: period 2^D) | Diagonals.rdiag_periodic |
| H14 | right-diagonals | lift | survives | the least period of right diagonal D exceeds ceil(D/2) | rediscovers C49 (FORMAL: least period > ceil(D/2)) | Diagonals.rdiag_not_periodic |
| H15 | right-diagonals | analogy | survives | (transported from the left-diagonal law) every right diagonal is periodic or anti-periodic with the common period of the two diagonals outside it | rediscovers C113 (FORMAL: periodic or anti-periodic) | RightDiagonalBalance (C113) |
| H16 | centre | template | survives | the centre column is not eventually periodic with period p ≤ 64 and preperiod ≤ 30000 | rediscovers C235 (CERT: no period with tau + p < 10000) | partial: PowerSeriesLadderData.no_eventual_period_below_10000 (a smaller range) |
| H17 | centre | narrow | survives | |#black − #white| ≤ 3·√N for every prefix length N (sharpest integer constant on N ≤ 4000) | rediscovers C22 (CERT: max D(N)^2/N on N ≤ 10^6 is 175561/24979) | partial: WobbleCertificate.wobble_sq_ratio_cert certifies N ≤ 10^6 only |
| H18 | centre | lift | refuted-heldout | the GF(2) linear complexity L(n) of the centre column satisfies |2·L(n) − n| ≤ 9 for all n (sharpest on n ≤ 2000) | rediscovers C160 (EMP: linear complexity within 6 of n/2 for n ≤ 20000) | not formalised |
| H19 | centre | narrow | survives | |2·L(n) − n| ≤ 10 for all n (narrowed on n ≤ 6000) | rediscovers C160 (EMP: linear complexity within 6 of n/2 for n ≤ 20000) | not formalised |
| H20 | centre | lift | survives | every binary word of length k occurs in the first ⌈3/2·k·2^k⌉ centre bits (sharpest on k ≤ 8) | rediscovers C235 (CERT: every word of length ≤ 10 occurs (partial match: the position bound is new)) | not formalised |
| H21 | left-diagonals | control | refuted-heldout | the eventual left diagonals do not depend on the seed: every finite seed whose leftmost cell is black has the same eventual left diagonals as the single black cell | new to the ledger | refuted by data (seeds of width ≤ 10) |
| H22 | left-diagonals | mechanism | law-holds | a left-white row can first differ from the seed only one diagonal past an eventually white diagonal of the seed (a reset erases the seed) | new to the ledger | LeftDiagonalPeriods.first_difference_after_white; LeftDiagonalPeriodsData.seed_first_difference |

## Evidence per hypothesis

**H01** (refuted-heldout): every left diagonal has eventual period dividing 8
  - dev D<200: ok — passes
  - held-out D<2000: FAIL — fails at D=400

**H02** (survives): for D ≥ 20 the transient of left diagonal D is longer than D (the centre column, which reads diagonal D at time D, always reads it inside its transient)
  - dev D<200: ok — passes
  - held-out D<2000: ok — passes
  - held-out D<20000: ok — passes

**H03** (survives): for D ≥ 20 the transient satisfies 30/29 ≤ pre(D)/D ≤ 71/48 (the exact extremes on the development range)
  - dev D<200: ok — passes
  - held-out D<2000: ok — passes
  - held-out D<20000: ok — passes

**H04** (refuted-heldout): the eventually white left diagonals are exactly [2, 7, 28]
  - dev D<200: ok — passes
  - held-out D<2000: FAIL — fails at D=399

**H05** (survives): every left diagonal D < 400 has eventual period dividing 8
  - cut: ok — holds for every D < 400 (exact repeat certificate)
  - controls: {'rule 30, seed 11': 'holds', 'rule 30, seed 101': 'holds', 'rule 86 (mirror), seed 1': 'no period | 64 within the window', 'rule 90 (linear), seed 1': 'no period | 64 within the window', 'rule 45, seed 1': 'no period | 64 within the window'}
  - scope: Rule-30-specific and robust to the seed changes tested; the other rules do not settle (so the statement is about Rule 30's left side)

**H06** (refuted-by-prediction): every left diagonal has eventual period dividing 16
  - all data D<20000: ok — passes
  - prediction: FAIL — fails at D=87867

**H07** (refuted-heldout): a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D-1)
  - all data D<20000: ok — exact on every D < 20000: 4 jumps, the condition holds at 4 indices
  - junction: ok — not separated by D < 20000 from ['white(D-1)', 'white(D-1) ∧ odd-parity(D-2)']
  - separating observation: FAIL — diagonal 53207 is eventually white with even parity outside it; the law predicts a jump at 53208 = True, actual = False

**H08** (law-holds): a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D-1) ∧ odd-parity(D-2)
  - all data D<20000: ok — exact on every D < 20000: 4 jumps, the condition holds at 4 indices
  - junction: ok — not separated by D < 20000 from ['white(D-1)', 'white(D-1) ∧ odd-parity(D-2)']
  - separating observation: ok — correct at the even-parity white diagonal 53207
  - separating observation: ok — correct at the even-parity white diagonal 58286
  - controls: {'rule 30, seed 11': 'holds (jumps exactly at white ∧ odd)', 'rule 30, seed 101': 'holds (jumps exactly at white ∧ odd)', 'rule 86 (mirror), seed 1': 'no period | 64 within the window', 'rule 90 (linear), seed 1': 'no period | 64 within the window', 'rule 45, seed 1': 'no period | 64 within the window'}
  - scope: Rule-30-specific and robust to the seed changes tested; the other rules do not settle (so the statement is about Rule 30's left side)

**H09** (prediction-confirmed): the first left diagonal with least eventual period 32 is D = 87867
  - direct check: ok — automaton run to D = 87867: lp = 32, all earlier lp ≤ 16: True

**H10** (survives): every left diagonal D < 87867 has eventual period dividing 16
  - cut: ok — holds for every D < 87867 (exact repeat certificate)

**H11** (open): the least periods of the left diagonals are unbounded (equivalently, by the law, infinitely many eventually white diagonals meet odd parity)
  - data: ok — periods 1, 2, 4, 8, 16, 32 first at D = 0, 3, 8, 29, 400, 87867; no finite range decides it

**H12** (refuted-heldout): the least period of right diagonal D is 2^(D - floor((D + 1) / 3))
  - dev D≤8: ok — fits exactly
  - held-out D≤16: FAIL — fails at D=10: exponent 6, form gives 7

**H13** (survives): the least period of right diagonal D divides 2^D
  - all D≤16: ok — passes

**H14** (survives): the least period of right diagonal D exceeds ceil(D/2)
  - all D≤16: ok — passes

**H15** (survives): (transported from the left-diagonal law) every right diagonal is periodic or anti-periodic with the common period of the two diagonals outside it
  - all D≤16: ok — every exponent is at most one more than the larger outer exponent

**H16** (survives): the centre column is not eventually periodic with period p ≤ 64 and preperiod ≤ 30000
  - n<60000: ok — a mismatch after the stated preperiod exists for every p (this is a finite refutation of each rung, CERT-able)

**H17** (survives): |#black − #white| ≤ 3·√N for every prefix length N (sharpest integer constant on N ≤ 4000)
  - dev N≤4000: ok — max (2·ones−N)²/N = 3200/731 ≤ 9
  - held-out N≤60000: ok — max = 175561/24979

**H18** (refuted-heldout): the GF(2) linear complexity L(n) of the centre column satisfies |2·L(n) − n| ≤ 9 for all n (sharpest on n ≤ 2000)
  - dev n≤2000: ok — max |2L−n| = 9
  - held-out n≤6000: FAIL — max |2L−n| = 10

**H19** (survives): |2·L(n) − n| ≤ 10 for all n (narrowed on n ≤ 6000)
  - n≤6000: ok — EMP only; the narrowing never settles from a finite range

**H20** (survives): every binary word of length k occurs in the first ⌈3/2·k·2^k⌉ centre bits (sharpest on k ≤ 8)
  - k≤12: ok — first full coverage at [3, 8, 15, 66, 120, 422, 1229, 1591, 2872, 5649, 23663, 42760]

**H21** (refuted-heldout): the eventual left diagonals do not depend on the seed: every finite seed whose leftmost cell is black has the same eventual left diagonals as the single black cell
  - controls 11, 101: ok — identical eventual patterns on D < 400
  - all 512 seeds of width ≤ 10: FAIL — first eventual differences at D ∈ [3, 8, 29, 400]; 47 seeds agree on every D < 450

**H22** (law-holds): a left-white row can first differ from the seed only one diagonal past an eventually white diagonal of the seed (a reset erases the seed)
  - 512 seeds: ok — first differences [3, 8, 29, 400] vs white diagonals [2, 7, 28, 399]

Wall-clock seconds: {'left-diagonals': 12.84, 'right-diagonals': 0.03, 'centre': 1.57, 'controls': 0.02, 'seed-memory': 2.28, 'total': 16.74}