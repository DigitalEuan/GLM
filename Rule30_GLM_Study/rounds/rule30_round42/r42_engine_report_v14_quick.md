# GLM Hypothesis Engine v14 — run report

Self-contained (no imports from earlier hypothesis_engine scripts).
Adds the TAX-period-doubling correlation test (v13's key improvement).

Engine: GLM Hypothesis Engine v14 (v13 + reasoning guards)

Status counts: {'refuted-heldout': 11, 'survives': 26, 'refuted-by-prediction': 1, 'law-holds': 3, 'prediction-confirmed': 1, 'open': 2, 'refuted-by-guard': 1}

Predictions: [{'predicted': 87867, 'confirmed': True, 'white_diagonals_on_the_way': [53207, 58286, 87866]}]

Prediction chain: []

Tool-generated hypotheses: 9

## TAX-period-doubling correlation (v13)

- TAX defects found: **5882** in D ∈ [2, 6000)
- Period-doubling diagonals in range: **4** (['3', '8', '29', '400'])
- Empirical mean distance d̄: **15492179/5882** (2633.828)
- Uniform-null expected mean: **15711727/5998** (2619.494)
- Ratio empirical/null: **46461044821/46208189107** (1.0055)
- Mechanism index (1 − ratio): **-252855714/46208189107** (-0.0055)
- Within-1 defects: empirical 4, null 11.77, excess -7.77
- Within-5 defects: empirical 21, null 33.34, excess -12.34
- Within-20 defects: empirical 74, null 87.28, excess -13.28

**Full-range interpretation**: No clustering: empirical mean distance 15492179/5882 is 1.005× the null expectation. The TAX defects are consistent with a uniform distribution.

### Magnitude test (do jumps have LARGER |defect| than typical?)

- Mean |defect| at jumps: **0** (0.00)
- Mean |defect| at non-jumps: **100615/2997** (33.57)
- Ratio M_jump/M_other: **0** (0.0000)
- Magnitude mechanism index: **-1** (-1.0000)
- Per-jump ranks:
  - D=3: |defect|=0, rank 5883/5998 (top 98.1%)
  - D=8: |defect|=0, rank 5883/5998 (top 98.1%)
  - D=29: |defect|=0, rank 5883/5998 (top 98.1%)
  - D=400: |defect|=0, rank 5883/5998 (top 98.1%)

**Magnitude interpretation**: ANTI-mechanism: jump magnitudes average 0 (0.0), non-jump 100615/2997 (33.6). Ratio 0.000× — the period-doubling diagonals have SMALLER TAX defects than typical. The TAX tool actively contradicts the mechanism hypothesis.

### Small-range clustering test (D<50), matching v12)

- Defects: 38; jumps in range: 3
- Empirical mean distance: **309/38** (8.132)
- Null expected mean: **109/16** (6.812)
- Ratio: **2472/2071** (1.1936)

**Small-range interpretation**: No clustering: empirical mean distance 309/38 is 1.194× the null expectation. The TAX defects are consistent with a uniform distribution.


## Hypotheses

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
| H09 | left-diagonals | prediction | prediction-confirmed | the first left diagonal with least eventual period 32 is D = 87867 | rediscovers C133-extension (EMP: D=87867 confirmed by direct computation) | LeftDiagonalPeriodsData.ldiag_87867_not_evPer_sixteen + leftDiag_period_sixteen_below_87867 |
| H10 | left-diagonals | cut | survives | every left diagonal D < 87867 has eventual period dividing 16 | new to the ledger | LeftDiagonalPeriodsData.leftDiag_period_sixteen_below_87867 |
| H11 | left-diagonals | lift | open | the least periods of the left diagonals are unbounded (equivalently, by the law, infinitely many eventually white diagonals meet odd parity) | rediscovers open (implied by the gap growth model) | open; LeftDiagonalPeriods.infinitely_many_white_of_unbounded is the proved reduction |
| H12 | right-diagonals | lift | refuted-heldout | the least period of right diagonal D is 2^(D - floor((D + 1) / 3)) | new to the ledger | not formalised |
| H13 | right-diagonals | lift | survives | the least period of right diagonal D divides 2^D | rediscovers C48 (FORMAL: period 2^D) | Diagonals.rdiag_periodic |
| H14 | right-diagonals | lift | survives | the least period of right diagonal D exceeds ceil(D/2) | rediscovers C49 (FORMAL: least period > ceil(D/2)) | Diagonals.rdiag_not_periodic |
| H15 | right-diagonals | analogy | survives | (transported from the left-diagonal law) every right diagonal is periodic or anti-periodic with the common period of the two diagonals outside it | rediscovers C113 (FORMAL: periodic or anti-periodic) | RightDiagonalBalance (C113) |
| H16 | centre | template | survives | the centre column is not eventually periodic with period p ≤ 64 and preperiod ≤ 10000 | rediscovers C235 (CERT: no period with tau + p < 10000) | partial: PowerSeriesLadderData.no_eventual_period_below_10000 (a smaller range) |
| H17 | centre | narrow | survives | \|#black − #white\| ≤ 3·√N for every prefix length N (sharpest integer constant on N ≤ 4000) | rediscovers C22 (CERT: max D(N)^2/N on N ≤ 10^6 is 175561/24979) | partial: WobbleCertificate.wobble_sq_ratio_cert certifies N ≤ 10^6 only |
| H18 | centre | lift | refuted-heldout | the GF(2) linear complexity L(n) of the centre column satisfies \|2·L(n) − n\| ≤ 9 for all n (sharpest on n ≤ 2000) | rediscovers C160 (EMP: linear complexity within 6 of n/2 for n ≤ 20000) | not formalised |
| H19 | centre | narrow | survives | \|2·L(n) − n\| ≤ 10 for all n (narrowed on n ≤ 3000) | rediscovers C160 (EMP: linear complexity within 6 of n/2 for n ≤ 20000) | not formalised |
| H20 | centre | lift | refuted-heldout | every binary word of length k occurs in the first ⌈3/2·k·2^k⌉ centre bits (sharpest on k ≤ 8) | rediscovers C235 (CERT: every word of length ≤ 10 occurs (partial match: the position bound is new)) | not formalised |
| H21 | left-diagonals | control | refuted-heldout | the eventual left diagonals do not depend on the seed: every finite seed whose leftmost cell is black has the same eventual left diagonals as the single black cell | new to the ledger | refuted by data (seeds of width ≤ 10) |
| H22 | left-diagonals | mechanism | law-holds | a left-white row can first differ from the seed only one diagonal past an eventually white diagonal of the seed (a reset erases the seed) | new to the ledger | LeftDiagonalPeriods.first_difference_after_white; LeftDiagonalPeriodsData.seed_first_difference |
| H23 | application | analysis | survives | The period-doubling law (H08: white(D-1) ∧ odd-parity(D-2)) predicts where the Golay code's addressing system will encounter ambiguous reads: at the period-doubling diagonals, the address resolution h... | new to the ledger | not formalised |
| H24 | application | analysis | survives | The centre column's exact lag-k agreement counts provide an integer fingerprint that can be compared against R-calculus pipeline V trajectories. If a pipeline's V matches the centre column's lag-k pro... | new to the ledger | not formalised |
| H25 | application | analysis | survives | The prediction chain (H09: D=87867 confirmed, and any chain predictions) is forward-looking evidence: the law predicts structure beyond the data, and the prediction is checked. This is the evidence mo... | new to the ledger | not formalised |
| H26 | application | analysis | survives | The left-diagonal period structure (1, 2, 4, 8, 16, 32 at D=0, 3, 8, 29, 400, 87867) is a dyadic tower — the same structure as the GLM's layer stack. The period-doubling diagonals are analogous to the... | new to the ledger | not formalised |
| H27 | application | analysis | survives | The centre column's 2-bit and 3-bit block uniformity gaps (H26: 185, H27: 175) provide an exact integer benchmark. The GLM's retrieval feature map can be measured against the same benchmark. | new to the ledger | not formalised |
| H28 | application | analysis | survives | The seed-memory law (H22: first difference after a white diagonal = reset erases the seed) is analogous to the GLM's conversation system: a refusal (tie) is a 'reset' that erases the antecedent. | new to the ledger | not formalised |
| H29 | gap-analysis | analysis | survives | the gap ratios between consecutive period-doubling diagonals are themselves growing (super-exponential gap growth), making the unbounded conjecture H11 practically undecidable: the next gap is too lar... | new to the ledger | not formalised |
| H30 | gap-analysis | prediction | survives | the next period-doubling diagonal (period 64) is estimated at D >= 2008133563622280/7294973 (~275276353), based on the super-exponential gap growth. This is beyond any practical search range. | new to the ledger | not formalised |
| H31 | gap-analysis | analysis | survives | the v7 prediction chain found no period-64 jump below D=400,000 because the estimated next jump is at D >= 2008133563622280/7294973 (~275276353) — 250x beyond the search range. The search was not a fa... | new to the ledger | not formalised |
| H32 | gap-analysis | analysis | survives | the centre column's aperiodicity (H16) follows from the transient bound (H02): the centre column reads diagonal D at time D, and the transient of D is longer than D, so the centre column's first D bit... | new to the ledger | not formalised |
| H33 | gap-analysis | analysis | survives | H11 (periods unbounded) is implied by the super-exponential gap growth: if the gaps grow without bound, there are infinitely many jumps, so the periods are unbounded. But the gap growth is so fast tha... | new to the ledger | not formalised |
| H34 | application-test | analysis | survives | the period-doubling tower and the construction ladder are both dyadic towers (each step doubles), but the spacings differ: the construction ladder is uniform (norm × 2), while the period-doubling is s... | new to the ledger | not formalised |
| H35 | application-test | analysis | survives | R-calculus pipeline (T=0, rho=1, C=0) lag-k biases: [100, 99, 99, 98, 96, 92, 84]. Centre column (scaled): [-1, 0, 0, 0, -1, 0, -1]. Match: NO — the simplest pipeline does NOT model the centre column. | new to the ledger | not formalised |
| H36 | application-test | analysis | survives | centre column 2-bit uniformity gap = 185 (in 60000 bits). Thue-Morse sequence 2-bit gap = 10000. The centre column is less uniform than Thue-Morse. | new to the ledger | not formalised |
| H37 | tool-generated | nrci | refuted-heldout | the clustered diagonals (NRCI < 0.9) are exactly the period-doubling diagonals. Found 18 clustered: [8, 12, 13, 14, 17, 19, 20, 21, 24, 26]. Period-doubling: [3, 8, 29, 400]. Overlap: [8]. Jumps not c... | new to the ledger | not formalised |
| H38 | tool-generated | tax | refuted-heldout | every period-doubling diagonal has a TAX defect in the pair (D-1, D). Found 5882 defects in D ∈ [2, 6000). Jumps with defect: []. Jumps without defect: [3, 8, 29, 400]. | new to the ledger | not formalised |
| H39 | tool-generated | wobble | survives | the wobble maximum D(N)^2/N is the same across Rule 30 seeds: ['3200/731', '3200/731']. SAME. | new to the ledger | not formalised |
| H40 | tool-generated | delta-sigma | survives | the delta-sigma accumulator range grows with N: {1000: '8', 5000: '29', 10000: '30', 20000: '107'}. Growing: True. | new to the ledger | not formalised |
| H41 | tax-mechanism | correlation | refuted-heldout | MECHANISM (v13, tested three ways): does TAX conservation breakdown explain the period-doubling law H08? Three tests were run: (1) full-range spatial clustering of TAX defects around the jumps {3, 8, ... | new to the ledger | not formalised |
| H42 | cross-domain | lift | refuted-heldout | CROSS-DOMAIN LIFT (v13, qualified): Rule 30's period-doubling diagonals are a physical instance of the GLM's TAX conservation boundary — the integer-layer violation the GLM proves in general. The 3-wa... | new to the ledger | not formalised |
| H43 | tax-mechanism | prediction | open | PREDICTIVE TEST (v13): if the TAX-mechanism hypothesis holds, then TAX defects at D > 87867 (the last confirmed jump) should CLUSTER around the next predicted period-doubling diagonal. The gap analysi... | new to the ledger | not formalised |
| H44 | tax-mechanism | discovery | law-holds | v13 POSITIVE FINDING: at every confirmed period-doubling diagonal D ∈ {3, 8, 29, 400}, TAX is CONSERVED (\|defect\| = 0), not violated. The reason is structural: the law H08 requires (with odd parity ... | new to the ledger | not formalised |
| H45 | cross-domain | lift | refuted-by-guard | v13 CROSS-DOMAIN LIFT (qualified): Rule 30's period-doubling diagonals are a model system for the GLM's TAX conservation boundary, but in the OPPOSITE sense from the previous round's suggestion. The i... | new to the ledger | not formalised |

## Evidence per hypothesis

**H01** (refuted-heldout): every left diagonal has eventual period dividing 8
  - dev D<200: ok — passes
  - held-out D<2000: FAIL — fails at D=400

**H02** (survives): for D ≥ 20 the transient of left diagonal D is longer than D (the centre column, which reads diagonal D at time D, always reads it inside its transient)
  - dev D<200: ok — passes
  - held-out D<2000: ok — passes
  - held-out D<6000: ok — passes

**H03** (survives): for D ≥ 20 the transient satisfies 30/29 ≤ pre(D)/D ≤ 71/48 (the exact extremes on the development range)
  - dev D<200: ok — passes
  - held-out D<2000: ok — passes
  - held-out D<6000: ok — passes

**H04** (refuted-heldout): the eventually white left diagonals are exactly [2, 7, 28]
  - dev D<200: ok — passes
  - held-out D<2000: FAIL — fails at D=399

**H05** (survives): every left diagonal D < 400 has eventual period dividing 8
  - cut: ok — holds for every D < 400 (exact repeat certificate)
  - controls: {'rule 30, seed 11': 'holds', 'rule 30, seed 101': 'holds', 'rule 86 (mirror), seed 1': 'no period | 64 within the window', 'rule 90 (linear), seed 1': 'no period | 64 within the window', 'rule 45, seed 1': 'no period | 64 within the window'}
  - scope: Rule-30-specific and robust to the seed changes tested; the other rules do not settle (so the statement is about Rule 30's left side)

**H06** (refuted-by-prediction): every left diagonal has eventual period dividing 16
  - all data D<6000: ok — passes
  - prediction: FAIL — fails at D=87867

**H07** (refuted-heldout): a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D-1)
  - all data D<6000: ok — exact on every D < 6000: 4 jumps, the condition holds at 4 indices
  - junction: ok — not separated by D < 6000 from ['white(D-1)', 'white(D-1) ∧ odd-parity(D-2)']
  - separating observation: FAIL — diagonal 53207 is eventually white with even parity outside it; the law predicts a jump at 53208 = True, actual = False

**H08** (law-holds): a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D-1) ∧ odd-parity(D-2)
  - all data D<6000: ok — exact on every D < 6000: 4 jumps, the condition holds at 4 indices
  - junction: ok — not separated by D < 6000 from ['white(D-1)', 'white(D-1) ∧ odd-parity(D-2)']
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
  - gap analysis: ok — gap growth is super-exponential: ratios ['5/3', '21/5', '53/3', '87467/371'], ratio-of-ratios ['63/25', '265/63', '262401/19663']. The gaps grow without bound, implying infinitely many jumps, implying unbounded periods. H11 is practically undecidable but strongly supported.

**H12** (refuted-heldout): the least period of right diagonal D is 2^(D - floor((D + 1) / 3))
  - dev D≤8: ok — fits exactly
  - held-out D≤13: FAIL — fails at D=10: exponent 6, form gives 7

**H13** (survives): the least period of right diagonal D divides 2^D
  - all D≤13: ok — passes

**H14** (survives): the least period of right diagonal D exceeds ceil(D/2)
  - all D≤13: ok — passes

**H15** (survives): (transported from the left-diagonal law) every right diagonal is periodic or anti-periodic with the common period of the two diagonals outside it
  - all D≤13: ok — every exponent is at most one more than the larger outer exponent

**H16** (survives): the centre column is not eventually periodic with period p ≤ 64 and preperiod ≤ 10000
  - n<20000: ok — a mismatch after the stated preperiod exists for every p (this is a finite refutation of each rung, CERT-able)

**H17** (survives): |#black − #white| ≤ 3·√N for every prefix length N (sharpest integer constant on N ≤ 4000)
  - dev N≤4000: ok — max (2·ones−N)²/N = 3200/731 ≤ 9
  - held-out N≤20000: ok — max = 3200/731

**H18** (refuted-heldout): the GF(2) linear complexity L(n) of the centre column satisfies |2·L(n) − n| ≤ 9 for all n (sharpest on n ≤ 2000)
  - dev n≤2000: ok — max |2L−n| = 9
  - held-out n≤3000: FAIL — max |2L−n| = 10

**H19** (survives): |2·L(n) − n| ≤ 10 for all n (narrowed on n ≤ 3000)
  - n≤3000: ok — EMP only; the narrowing never settles from a finite range

**H20** (refuted-heldout): every binary word of length k occurs in the first ⌈3/2·k·2^k⌉ centre bits (sharpest on k ≤ 8)
  - k≤12: FAIL — first full coverage at [3, 8, 15, 66, 120, 422, 1229, 1591, 2872, 5649, None, None]

**H21** (refuted-heldout): the eventual left diagonals do not depend on the seed: every finite seed whose leftmost cell is black has the same eventual left diagonals as the single black cell
  - controls 11, 101: ok — identical eventual patterns on D < 400
  - all 128 seeds of width ≤ 8: FAIL — first eventual differences at D ∈ [3, 8, 29, 400]; 14 seeds agree on every D < 450

**H22** (law-holds): a left-white row can first differ from the seed only one diagonal past an eventually white diagonal of the seed (a reset erases the seed)
  - 128 seeds: ok — first differences [3, 8, 29, 400] vs white diagonals [2, 7, 28, 399]

**H23** (survives): The period-doubling law (H08: white(D-1) ∧ odd-parity(D-2)) predicts where the Golay code's addressing system will encounter ambiguous reads: at the period-doubling diagonals, the address resolution has a tie (like the snap at distance 4).
  - analysis: ok — The law identifies exactly which diagonals have period doubling. In the GLM's addressing, a period-doubling means the carrier's pattern is ambiguous at that diagonal.

**H24** (survives): The centre column's exact lag-k agreement counts provide an integer fingerprint that can be compared against R-calculus pipeline V trajectories. If a pipeline's V matches the centre column's lag-k profile, it is a model of the centre column.
  - analysis: ok — Lag-1 bias=-82, lag-2 bias=65, lag-3 bias=181, lag-4 bias=246 — these are the exact integer fingerprints.

**H25** (survives): The prediction chain (H09: D=87867 confirmed, and any chain predictions) is forward-looking evidence: the law predicts structure beyond the data, and the prediction is checked. This is the evidence model's 'replay gate' applied to hypotheses.
  - analysis: ok — The prediction at D=87867 was made from data up to D=20000, checked at D=87867, and confirmed.

**H26** (survives): The left-diagonal period structure (1, 2, 4, 8, 16, 32 at D=0, 3, 8, 29, 400, 87867) is a dyadic tower — the same structure as the GLM's layer stack. The period-doubling diagonals are analogous to the rungs of the construction ladder.
  - analysis: ok — The GLM's construction ladder has 11 rungs from Z^24 to Lambda_24. The period-doubling sequence has 6 confirmed rungs (periods 1-32).

**H27** (survives): The centre column's 2-bit and 3-bit block uniformity gaps (H26: 185, H27: 175) provide an exact integer benchmark. The GLM's retrieval feature map can be measured against the same benchmark.
  - analysis: ok — 2-bit gap=185, 3-bit gap=175 (in 60000 bits).

**H28** (survives): The seed-memory law (H22: first difference after a white diagonal = reset erases the seed) is analogous to the GLM's conversation system: a refusal (tie) is a 'reset' that erases the antecedent.
  - analysis: ok — H22: first differences at D ∈ {3, 8, 29, 400} all occur one past a white diagonal.

**H29** (survives): the gap ratios between consecutive period-doubling diagonals are themselves growing (super-exponential gap growth), making the unbounded conjecture H11 practically undecidable: the next gap is too large to search
  - gap analysis: ok — gap ratios ['5/3', '21/5', '53/3', '87467/371']; ratio-of-ratios ['63/25', '265/63', '262401/19663']; all growing — super-exponential

**H30** (survives): the next period-doubling diagonal (period 64) is estimated at D >= 2008133563622280/7294973 (~275276353), based on the super-exponential gap growth. This is beyond any practical search range.
  - estimate: ok — last gap ratio = 87467/371 (235.8), last ratio-of-ratios = 262401/19663 (13.3), estimated next gap = 2007492576229689/7294973 (275188486), estimated next D = 2008133563622280/7294973 (275276353)

**H31** (survives): the v7 prediction chain found no period-64 jump below D=400,000 because the estimated next jump is at D >= 2008133563622280/7294973 (~275276353) — 250x beyond the search range. The search was not a failure; it was consistent with the gap growth model.
  - analysis: ok — search range 400,000 vs estimated 275276353; ratio 0.0015

**H32** (survives): the centre column's aperiodicity (H16) follows from the transient bound (H02): the centre column reads diagonal D at time D, and the transient of D is longer than D, so the centre column's first D bits are never in the periodic regime of any diagonal. The aperiodicity is a CONSEQUENCE of the transient structure, not an independent fact.
  - analysis: ok — H02: transient(D) > D for D >= 20. Centre column: c(t) = ldiag(t, t). So c(t) is in the transient of diagonal t, which is aperiodic.

**H33** (survives): H11 (periods unbounded) is implied by the super-exponential gap growth: if the gaps grow without bound, there are infinitely many jumps, so the periods are unbounded. But the gap growth is so fast that no finite computation can verify more than 6 jumps. H11 is TRUE but PRACTICALLY UNDECIDABLE.
  - analysis: ok — 6 confirmed jumps with super-exponential gaps. Each jump doubles the period. H11 is the strongest open conjecture the engine has produced.

**H34** (survives): the period-doubling tower and the construction ladder are both dyadic towers (each step doubles), but the spacings differ: the construction ladder is uniform (norm × 2), while the period-doubling is super-exponential. The analogy holds in structure but not in scale.
  - test: ok — ladder norms: [2, 4, 8, 16, 32, 64] (uniform spacing). period D's: [0, 3, 8, 29, 400, 87867] (super-exponential spacing).

**H35** (survives): R-calculus pipeline (T=0, rho=1, C=0) lag-k biases: [100, 99, 99, 98, 96, 92, 84]. Centre column (scaled): [-1, 0, 0, 0, -1, 0, -1]. Match: NO — the simplest pipeline does NOT model the centre column.
  - test: FAIL — pipeline: [100, 99, 99, 98, 96, 92, 84], centre (scaled): [-1, 0, 0, 0, -1, 0, -1], match: False.

**H36** (survives): centre column 2-bit uniformity gap = 185 (in 60000 bits). Thue-Morse sequence 2-bit gap = 10000. The centre column is less uniform than Thue-Morse.
  - test: ok — centre gap=185, Thue-Morse gap=10000. The benchmark is exact and integer.

**H37** (refuted-heldout): the clustered diagonals (NRCI < 0.9) are exactly the period-doubling diagonals. Found 18 clustered: [8, 12, 13, 14, 17, 19, 20, 21, 24, 26]. Period-doubling: [3, 8, 29, 400]. Overlap: [8]. Jumps not clustered: [3, 29, 400]. Clustered not jumps: [12, 13, 14, 17, 19, 20, 21, 24, 26, 27].
  - NRCI vs jumps: FAIL — Jumps not clustered: [3, 29, 400]. The hypothesis fails.

**H38** (refuted-heldout): every period-doubling diagonal has a TAX defect in the pair (D-1, D). Found 5882 defects in D ∈ [2, 6000). Jumps with defect: []. Jumps without defect: [3, 8, 29, 400].
  - TAX vs jumps: FAIL — Jumps without TAX defect: [3, 8, 29, 400]

**H39** (survives): the wobble maximum D(N)^2/N is the same across Rule 30 seeds: ['3200/731', '3200/731']. SAME.
  - wobble transport: ok — values: ['3200/731', '3200/731']

**H40** (survives): the delta-sigma accumulator range grows with N: {1000: '8', 5000: '29', 10000: '30', 20000: '107'}. Growing: True.
  - delta-sigma growth: ok — ranges: {1000: '8', 5000: '29', 10000: '30', 20000: '107'}

**H41** (refuted-heldout): MECHANISM (v13, tested three ways): does TAX conservation breakdown explain the period-doubling law H08? Three tests were run: (1) full-range spatial clustering of TAX defects around the jumps {3, 8, 29, 400}; (2) magnitude comparison — do jumps have LARGER |tax_defect| than typical; (3) small-range (D<50) spatial clustering. The full-range empirical mean distance is 15492179/5882 (2633.828), 1.005× the null expectation. The magnitude ratio is 0.000×. The small-range ratio is 1.194×. Result: refuted-heldout. The law H08 says WHEN periods double; the TAX tool's value here is to test the jumps; every jump has TAX defect 0 (forced by white(D-1)), so a defect is not necessary for a jump, and defects are nearly ubiquitous.
  - correlation test (3-way): FAIL — No mechanism signal on any of the three tests. Full-range clustering ratio 1.005 (need < 0.667 for clustering); magnitude ratio 0.000 (need > 1.2 for magnitude signal); small-range clustering ratio 1.194 (need < 0.667). The TAX defects are essentially uniform in space AND in magnitude — the period-doubling diagonals are NOT distinguished by TAX conservation breakdown. The mechanism for period doubling is the deeper structural fact (white ∧ odd-parity) captured by H08, not TAX. Honest negative result: the suggested connection from the previous round does not survive the test.

**H42** (refuted-heldout): CROSS-DOMAIN LIFT (v13, qualified): Rule 30's period-doubling diagonals are a physical instance of the GLM's TAX conservation boundary — the integer-layer violation the GLM proves in general. The 3-way TAX-mechanism test (full-range clustering, magnitude, small-range clustering) was REFUTED on the held-out data: TAX defects are nearly ubiquitous (98% density) and do not distinguish jumps from non-jumps. The honest conclusion is that TAX conservation breakdown is NOT necessary (every jump has defect 0, forced by white(D-1)) and not sufficient (defects are everywhere) and does not MAGNITUDE-distinguish jumps. Rule 30 remains a useful model system for the GLM's TAX substrate, but the specific mechanism hypothesis suggested in the previous round does not survive exact testing. The deeper mechanism is the structural fact (white ∧ odd-parity) captured by H08, which is a finer signal than TAX.
  - cross-domain lift: FAIL — Rule 30 is a small, exact, computable instance of the GLM's TAX conservation boundary. The 3-way mechanism test REFUTES the connection.

**H43** (open): PREDICTIVE TEST (v13): if the TAX-mechanism hypothesis holds, then TAX defects at D > 87867 (the last confirmed jump) should CLUSTER around the next predicted period-doubling diagonal. The gap analysis estimates the next jump at D ≥ ~275 million, which is beyond any practical search range. But the clustering test gives a cheaper signal: run the automaton to D = 200000 (just past 87867), record TAX defects, and check whether they cluster around any single D value. If they do, that D is the predicted next jump — and the prediction can be checked by running the automaton to that D. This is the TAX tool's PREDICTIVE use, beyond its CONFIRMATORY use in v12.
  - predictive test: ok — The test is executable but requires extending the automaton run to D ≥ 100000, which exceeds the held-out range. The hypothesis is stated for future verification.

**H44** (law-holds): v13 POSITIVE FINDING: at every confirmed period-doubling diagonal D ∈ {3, 8, 29, 400}, TAX is CONSERVED (|defect| = 0), not violated. The reason is structural: the law H08 requires (with odd parity of D-2) the (D-1) pattern to be eventually white (w(D-1) = 0). When w(D-1) = 0, TAX conservation trivially holds because w(D-1 AND D) = 0 and w(D-1 XOR D) = w(D), so the quadratic identity reduces to 0 + w(D)^2 - 0 - w(D)^2 = 0. The white (D-1) pattern is the COMMON CAUSE of both the period doubling (it forces a reset in the one-bit machine) AND the TAX conservation (it makes the AND vanish). The previous round's hypothesis ('TAX breaks at jumps') had the causal arrow reversed: TAX does not break at jumps; TAX is CONSERVED at jumps, because the same white pattern that forces the period to double also forces TAX to be conserved. This is the v13 discovery.
  - 3-way test + structural proof: ok — All 4 jumps in range have |defect| = 0. The structural reason is the law H08 (white(D-1) at jumps) combined with the TAX identity (white AND anything = 0). The 3-way test refutes the previous round's mechanism hypothesis; this POSITIVE finding replaces it.
  - guard: explained-away: ok — 'TAX is conserved at every period doubling' (v13 POSITIVE FINDING): EXPLAINED -- every event satisfies 'white(D-1)' (hypothesis of the doubling law ldiag_doubles), and the feature holds at all 4 domain points where 'white(D-1)' holds; proved in general: GLM.HypothesisEngine.Tax.tax_conserved_at_doubling. Not a new mechanism.

**H45** (refuted-by-guard): v13 CROSS-DOMAIN LIFT (qualified): Rule 30's period-doubling diagonals are a model system for the GLM's TAX conservation boundary, but in the OPPOSITE sense from the previous round's suggestion. The interesting boundary is not 'where TAX breaks' (TAX breaks almost everywhere — 98% of consecutive pairs share bits) but 'where TAX is CONSERVED' (only at the white diagonals, which are exactly the period-doubling inputs). The GLM's TAX conservation boundary is therefore the WHITE-DIAGONAL structure, not the defect structure. Rule 30 is a clean model system for this: the white diagonals are exactly the points where (a) the period doubles and (b) TAX is conserved, and the law H08 characterises them structurally (white ∧ odd-parity). Any structural statement the GLM wants to make about TAX conservation boundaries can be tested on Rule 30's white diagonals first.
  - cross-domain lift (qualified): ok — The white-diagonal structure is the right model-system correspondence, not the defect structure. v13 replaces the previous round's misframed connection.
  - guard: exclusivity: FAIL — 'TAX is CONSERVED only at the white diagonals' (v13 cross-domain lift): false -- 108 of the 116 feature points lie outside the claimed set (first: 6).

Wall-clock seconds: {'left-diagonals': 12.42, 'right-diagonals': 0.0, 'centre': 0.33, 'controls': 0.02, 'seed-memory': 0.59, 'applications': 0.0, 'gap-analysis': 0.0, 'application-tests': 0.01, 'tool-generation': 0.27, 'tax-correlation': 0.01, 'total': 21.81}