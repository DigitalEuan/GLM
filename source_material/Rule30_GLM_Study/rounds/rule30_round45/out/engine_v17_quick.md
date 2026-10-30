# GLM Hypothesis Engine v17 (TCT gate cascade, honest layers, typed rollback)

quick = True, ledger gate = True

| id | key | class | stage status | final status | arrow | backing |
|---|---|---|---|---|---|---|
| H01 | `LD.period.divides.8` | Pi1 | refuted-heldout | **refuted-heldout** | — | CERT LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_eight |
| H02 | `LD.preperiod.gt.D` | Pi1 | survives | **survives-to** | universal (converging) | escalation: survives every scale read, up to 5000; CERT LeftDiagonalPeriodsData.centerCol_read_in_transient (20 ≤ D < 20000 only) |
| H03 | `LD.preperiod.envelope` | Pi1 | survives | **survives-to** | universal (converging) | escalation: survives every scale read, up to 5000 |
| H04 | `LD.white.finite` | Pi1 | refuted-heldout | **refuted-heldout** | — | FORMAL WhiteDiagonals.ldiag_infinitely_many_white; LeftDiagonalPeriodsData.leftDiag_white_below_87868 |
| H05 | `LD.period.divides.8.below` | finite | survives | **proved** | — | CERT LeftDiagonalPeriodsData.leftDiag_period_eight_below_400 |
| H06 | `LD.period.divides.16` | Pi1 | refuted-by-prediction | **refuted-by-prediction** | — | CERT LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_sixteen |
| H07 | `LD.period.law.simple` | Pi1 | refuted-heldout | **refuted-heldout** | — | stage test: separating observation: diagonal 53207 is eventually white with even parity outside it; the law predicts a jump at 53208 = True, actual =  |
| H08 | `LD.period.law` | Pi1 | law-holds | **proved** | — | FORMAL LeftDiagonalPeriods.ldiag_evPer_of_not_white, ldiag_doubles, ldiag_keeps_of_even |
| H09 | `LD.first.period.32` | finite | prediction-confirmed | **proved** | — | CERT LeftDiagonalPeriodsData.ldiag_87867_not_evPer_sixteen + leftDiag_period_sixteen_below_87867 |
| H10 | `LD.period.divides.16.below` | finite | survives | **proved** | — | CERT LeftDiagonalPeriodsData.leftDiag_period_sixteen_below_87867 |
| H11 | `LD.periods.unbounded` | Pi2 | open | **open** | — | FORMAL open (ledger C359); proved reduction WhiteDiagonals.ldiag_periods_unbounded_iff |
| H12 | `RD.lp.closed.D - floor((D + 1) / 3)` | Pi1 | refuted-heldout | **refuted-heldout** | — | stage test: held-out D≤13: fails at D=10: exponent 6, form gives 7 |
| H13 | `RD.lp.le.2^D` | Pi1 | survives | **proved** | — | FORMAL Diagonals.rdiag_periodic |
| H14 | `RD.lp.gt.half` | Pi1 | survives | **proved** | — | FORMAL Diagonals.rdiag_not_periodic |
| H15 | `RD.periodic.or.anti` | Pi1 | survives | **proved** | — | FORMAL RightDiagonalBalance.runningXor_periodic_or_antiPeriodic |
| H16 | `CC.no.short.period` | finite | survives | **proved** | — | CERT GLM.HypothesisEngine.WheelChecks.wheel_H16_true |
| H17 | `CC.balance.sqrt` | Pi1 | survives | **survives-to** | universal (converging) | escalation: survives every scale read, up to 20000; CERT GLM.Rule30 WobbleCertificate.wobble_sq_ratio_cert (max D(N)²/N on N ≤ 10^6 is 175561/24979, s |
| H18 | `CC.lc.half` | Pi1 | refuted-heldout | **refuted-heldout** | substrate (converging) | CERT GLM.HypothesisEngine.WheelChecks.wheel_H19_false (2·L(11101) − 11101 ≥ 11) |
| H19 | `CC.lc.half.2` | Pi1 | survives | **refuted-on-escalation** | universal (escalation flipped at universal) | escalation: n = 11101: /2·L(n) − n/ = 11 > 10 (scale 12000); CERT GLM.HypothesisEngine.WheelChecks.wheel_H19_false (2·L(11101) − 11101 ≥ 11) |
| H20 | `CC.words.early` | Pi1 | refuted-heldout | **survives-to** | universal (converging) | stage said refuted-heldout, but the refutation not reproduced: no counterexample on scales up to 12 |
| H21 | `LD.seed.independent` | Pi1 | refuted-heldout | **refuted-heldout** | — | stage test: all 128 seeds of width ≤ 8: first eventual differences at D ∈ [3, 8, 29, 400]; 14 seeds agree on every D < 450 |
| H22 | `LD.seed.forgetting` | Pi1 | law-holds | **proved** | — | FORMAL LeftDiagonalPeriods.first_difference_after_white; LeftDiagonalPeriodsData.seed_first_difference |
| H23 | `APP.lattice.addressing` | analogy | survives | **untested** | — | class 'analogy': no executable test was given |
| H24 | `APP.rcalculus.model` | proposal | survives | **untested** | — | class 'proposal': no executable test was given |
| H25 | `APP.evidence.prediction` | meta | survives | **untested** | — | class 'meta': no executable test was given |
| H26 | `APP.deephole.ladder` | analogy | survives | **untested** | — | class 'analogy': no executable test was given |
| H27 | `APP.retrieval.uniformity` | proposal | survives | **untested** | — | class 'proposal': no executable test was given |
| H28 | `APP.conversation.reset` | analogy | survives | **untested** | — | class 'analogy': no executable test was given |
| H29 | `GAP.ratio.growing` | trend | survives | **untested** | — | class 'trend': no executable test was given |
| H30 | `GAP.next.estimate` | estimate | survives | **estimate** | — | an extrapolation; not checked |
| H31 | `GAP.chain.explanation` | meta | survives | **untested** | — | class 'meta': no executable test was given |
| H32 | `GAP.centre.diagonal.connection` | implication | survives | **refuted-by-ledger** | — | FORMAL DialogueChecks.transient_read_does_not_imply_aperiodic |
| H33 | `GAP.unbounded.undecidable` | implication | survives | **refuted-by-ledger** | — | FORMAL NeedsWheel.finite_data_never_forces_infinitely_many |
| H34 | `APPTEST.ladder.spacing` | analogy | survives | **untested** | — | class 'analogy': no executable test was given |
| H35 | `APPTEST.rcalculus.match` | measurement | survives | **measured** | — | a reported measurement, not a claim about all cases |
| H36 | `APPTEST.uniformity.benchmark` | comparison | survives | **refuted-by-recompute** | — | recomputed on 60000 bits: centre 2-bit gap = 185, Thue–Morse 2-bit gap = 10000; a smaller gap is more uniform, so the centre column is more uniform th |
| H37 | `NRCI.clustered.equals.jumps` | Pi1 | refuted-heldout | **refuted-heldout** | — | stage test: NRCI vs jumps: Jumps not clustered: [3, 29, 400]. The hypothesis fails. |
| H38 | `TAX.defect.contains.jumps` | Pi1 | refuted-by-guard | **refuted-by-guard** | universal (converging) | FORMAL TaxChecks.docstring_criterion_wrong |
| H39 | `WOBBLE.transportable` | Pi1 | survives | **refuted-on-escalation** | integer (escalation flipped at integer) | escalation: seed 0b111: max D(N)²/N = 2738/665 ≠ 3200/731 (seed 1), N ≤ 5000; 2 distinct centre columns among the seeds read (scale 8 seeds (width ≤ 4 |
| H40 | `DS.accumulator.growing` | trend | survives | **untested** | — | class 'trend': no executable test was given |
| H41 | `TAX.mechanism.cluster` | mechanism | refuted-by-guard | **refuted-by-guard** | universal (converging) | FORMAL the law is proved from the left step alone: LeftDiagonalPeriods.ldiag_doubles, ldiag_keeps_of_even |
| H42 | `TAX.substrate.model` | analogy | refuted-heldout | **refuted-heldout** | — | depends on H41, already refuted (inherited at construction) |
| H43 | `TAX.mechanism.predictive` | estimate | open | **retracted** | — | depends on H41 (refuted-heldout) |
| H44 | `TAX.conserved.at.jumps` | finite | law-holds | **proved** | universal (converging) | FORMAL TaxChecks.tax_conserved_at_doubling |
| H45 | `TAX.substrate.model.qualified` | Pi1 | refuted-by-guard | **refuted-by-guard** | universal (converging) | CERT TaxChecksData.tax_conserved_not_only_white |
| H46 | `WOBBLE.balanced.density` | Pi1 | refuted-by-guard | **refuted-by-guard** | universal (converging) | identity fails; first failure at substrate (box<2), counterexample (1, 0, 0) |
| H47 | `WOBBLE.transportable` | Pi1 | survives | **refuted-on-escalation** | integer (escalation flipped at integer) | escalation: seed 0b111: max D(N)²/N = 2738/665 ≠ 3200/731 (seed 1), N ≤ 5000; 2 distinct centre columns among the seeds read (scale 8 seeds (width ≤ 4 |
| H48 | `WOBBLE.sturmian` | Pi1 | refuted-heldout | **refuted-heldout** | — | stage test: sturmian test: balanced=False, aperiodic=False |
| H49 | `BROKEN.tax.criterion` | Pi1 | refuted-by-guard | **refuted-by-guard** | universal (converging) | identity fails; first failure at substrate (box<2), counterexample (1, 1, 0) |
| H50 | `BROKEN.balance.criterion` | Pi1 | refuted-by-guard | **refuted-by-guard** | universal (converging) | identity fails; first failure at rational (box<4), counterexample (2, 0, 0) |
| H51 | `APPTEST.uniformity.benchmark.corrected` | finite | verified-exact | **verified-exact** | — | exact recomputation: recomputed on 60000 bits: centre 2-bit gap = 185, Thue–Morse 2-bit gap = 10000; a smaller gap is more uniform, so the centre colu |

## Layer profiles

* H02: escalation [universal] preperiod(D) > D for 20 ≤ D < scale: verdict=True; layers substrate=1000:T, integer=2000:T, rational=3000:T, griess=4000:T, universal=5000:T
* H03: escalation [universal] 30/29 ≤ pre(D)/D ≤ 71/48 for 20 ≤ D < scale: verdict=True; layers substrate=1000:T, integer=2000:T, rational=3000:T, griess=4000:T, universal=5000:T
* H17: escalation [universal] |D(N)| ≤ 3·√N on N ≤ scale: verdict=True; layers substrate=4000:T, integer=8000:T, rational=12000:T, griess=16000:T, universal=20000:T
* H18: escalation [universal] |2·L(n) − n| ≤ 9 on n ≤ scale: verdict=False; layers substrate=3000:F, integer=4500:-, rational=6000:-, griess=9000:-, universal=12000:-; first failure at substrate (scale 3000)
* H19: escalation [universal] |2·L(n) − n| ≤ 10 on n ≤ scale: verdict=False; layers substrate=3000:T, integer=4500:T, rational=6000:T, griess=9000:T, universal=12000:F; first failure at universal (scale 12000)
* H20: escalation [universal] every word of length k occurs in the first ⌈3/2·k·2^k⌉ bits, k = scale: verdict=True; layers substrate=9:T, integer=10:T, rational=11:T, griess=12:T, universal=12:T
* H38: identity [universal] TAX criterion 'conserved iff c in {0,a,b}': verdict=False; layers substrate=box<2:F, integer=box<4:F, rational=box<7:F, griess=box<8:F, universal=box<13:F; first failure at substrate (scale box<2)
* H39: escalation [universal] wobble maximum equal to seed 1's on N ≤ 5000: verdict=False; layers substrate=3 seeds (width ≤ 3):T, integer=8 seeds (width ≤ 4):F, rational=16 seeds (width ≤ 5):-, griess=32 seeds (width ≤ 6):-, universal=64 seeds (width ≤ 7):-; first failure at integer (scale 8 seeds (width ≤ 4))
* H41: identity [universal] TAX criterion 'conserved iff c in {0,a,b}': verdict=False; layers substrate=box<2:F, integer=box<4:F, rational=box<7:F, griess=box<8:F, universal=box<13:F; first failure at substrate (scale box<2)
* H44: explained-away [largest] 'TAX conserved at every period doubling' (v13 POSITIVE FINDING): verdict=True; layers substrate=D<10:T, integer=D<50:T, rational=D<200:T, griess=D<2000:T, universal=D<6000:T
* H44: coincidence [largest] hits concentrated on the feature: verdict=True; layers substrate=N=10:F, integer=N=50:T, rational=N=200:T, griess=N=2000:T, universal=N=5998:T
* H45: exclusivity [stated] TAX conserved only at white diagonals: verdict=False; layers substrate=±0:F, integer=±1:F, rational=±5:F, griess=±20:F, universal=±100:F
* H46: identity [universal] balance criterion 'balanced iff density = 1/2' (WRONG): verdict=False; layers substrate=box<2:F, integer=box<4:F, rational=box<5:F, griess=box<8:F, universal=box<9:F; first failure at substrate (scale box<2)
* H47: escalation [universal] wobble maximum equal to seed 1's on N ≤ 5000: verdict=False; layers substrate=3 seeds (width ≤ 3):T, integer=8 seeds (width ≤ 4):F, rational=16 seeds (width ≤ 5):-, griess=32 seeds (width ≤ 6):-, universal=64 seeds (width ≤ 7):-; first failure at integer (scale 8 seeds (width ≤ 4))
* H49: identity [universal] BROKEN criterion 'TAX conserved iff c = 0' (only disjoint): verdict=False; layers substrate=box<2:F, integer=box<4:F, rational=box<5:F, griess=box<8:F, universal=box<9:F; first failure at substrate (scale box<2)
* H50: identity [universal] BROKEN criterion 'balanced iff all bits equal': verdict=False; layers substrate=box<2:T, integer=box<2:T, rational=box<4:F, griess=box<7:F, universal=box<8:F; first failure at rational (scale box<4)

## Rollback log

* H42 ← H41 (was never-tested)
* H43 ← H41 (was never-tested)

Conflicts (gate vs Lean): none
Layer-shape violations: none
Stage refutations not reproduced: [('H20', 'refuted-heldout', 'refutation not reproduced: no counterexample on scales up to 12')]
Dialogue consistency: {'spoken': 18, 'spoken_not_speakable': [], 'spoken_without_backing': [], 'ok': True}

## Dialogue

> I generated 51 hypotheses. Backed and spoken: 18. Refuted: 22. Retracted (depend on a refuted claim): 1. Untested: 10. Unchecked implications: 0.
> The GLM has a Wobble tool. Running it on the centre column.
> Wobble: max D(N)^2/N = 3200/731 (4.3776) at N = 1462. Balanced = False.
> Running NRCI on the centre column.
> NRCI: 251575/249989 (1.006344). random-like (NRCI ≈ 1).
> Running NRCI on the left diagonals.
> Diagonal NRCI: 18 clustered, 42 total.
> Running TAX conservation check on consecutive diagonals.
> TAX: 10/48 conserved, 38 defects.
> Running delta-sigma analysis.
> Delta-sigma: accumulator range = 107 (107.0), converging = False.
> TAX-period-doubling correlation (3-way test):
>   Full-range: 5882 defects, ratio 1.0055, No clustering: empirical mean distance 15492179/5882 is 1.005× the null expectat
>   Magnitude: M_jump=0.0, M_other=33.6, ratio=0.0000
>   Small-range: ratio=1.1936
>   COMBINED: NONE of the three tests support the mechanism. TAX defects are uniform in space and magnitude. The period-doubling law H08 (white ∧ odd-parity) remains the explanation; TAX neither marks nor explains the doublings.
> Proved in Lean (10):
>   H05: every left diagonal D < 400 has eventual period dividing 8 — CERT LeftDiagonalPeriodsData.leftDiag_period_eight_below_400
>   H08: a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D-1) ∧ odd-parity(D-2) — FORMAL LeftDiagonalPeriods.ldiag_evPer_of_not_white, ldiag_doubles, ldiag_keeps_of_even
>   H09: the first left diagonal with least eventual period 32 is D = 87867 — CERT LeftDiagonalPeriodsData.ldiag_87867_not_evPer_sixteen + leftDiag_period_sixteen_below_87867
>   H10: every left diagonal D < 87867 has eventual period dividing 16 — CERT LeftDiagonalPeriodsData.leftDiag_period_sixteen_below_87867
>   H13: the least period of right diagonal D divides 2^D — FORMAL Diagonals.rdiag_periodic
>   H14: the least period of right diagonal D exceeds ceil(D/2) — FORMAL Diagonals.rdiag_not_periodic
>   H15: (transported from the left-diagonal law) every right diagonal is periodic or anti-periodic with the common period of the two diagonals outsi — FORMAL RightDiagonalBalance.runningXor_periodic_or_antiPeriodic
>   H16: the centre column is not eventually periodic with period p ≤ 64 and preperiod ≤ 10000 — CERT GLM.HypothesisEngine.WheelChecks.wheel_H16_true
>   H22: a left-white row can first differ from the seed only one diagonal past an eventually white diagonal of the seed (a reset erases the seed) — FORMAL LeftDiagonalPeriods.first_difference_after_white; LeftDiagonalPeriodsData.seed_first_difference
>   H44: v13 POSITIVE FINDING: at every confirmed period-doubling diagonal D ∈ {3, 8, 29, 400}, TAX is CONSERVED (|defect| = 0), not violated. The re — FORMAL TaxChecks.tax_conserved_at_doubling
> Verified exactly (finite claim, whole range) (1):
>   H51: the centre column's 2-bit block counts on its first 60000 bits are more uniform than Thue–Morse's: max−min count gap 185 vs 10000 (exact) — exact recomputation: recomputed on 60000 bits: centre 2-bit gap = 185, Thue–Morse 2-bit gap = 10000; a smaller gap is more uniform, so the centre column is more
> Survives every scale read (a universal claim: open beyond that scale) (4):
>   H02: for D ≥ 20 the transient of left diagonal D is longer than D (the centre column, which reads diagonal D at time D, always reads it inside it — escalation: survives every scale read, up to 5000; CERT LeftDiagonalPeriodsData.centerCol_read_in_transient (20 ≤ D < 20000 only)
>   H03: for D ≥ 20 the transient satisfies 30/29 ≤ pre(D)/D ≤ 71/48 (the exact extremes on the development range) — escalation: survives every scale read, up to 5000
>   H17: |#black − #white| ≤ 3·√N for every prefix length N (sharpest integer constant on N ≤ 4000) — escalation: survives every scale read, up to 20000; CERT GLM.Rule30 WobbleCertificate.wobble_sq_ratio_cert (max D(N)²/N on N ≤ 10^6 is 175561/24979, so the boun
>   H20: every binary word of length k occurs in the first ⌈3/2·k·2^k⌉ centre bits (sharpest on k ≤ 8) — stage said refuted-heldout, but the refutation not reproduced: no counterexample on scales up to 12
> Measured (not a claim about all cases) (1):
>   H35: R-calculus pipeline (T=0, rho=1, C=0) lag-k biases: [100, 99, 99, 98, 96, 92, 84]. Centre column (scaled): [-1, 0, 0, 0, -1, 0, -1]. Match:  — a reported measurement, not a claim about all cases
> Open (1):
>   H11: the least periods of the left diagonals are unbounded (equivalently, by the law, infinitely many eventually white diagonals meet odd parity) — FORMAL open (ledger C359); proved reduction WhiteDiagonals.ldiag_periods_unbounded_iff
> Estimates (unchecked extrapolations) (1):
>   H30: the next period-doubling diagonal (period 64) is estimated at D >= 2008133563622280/7294973 (~275276353), based on the super-exponential gap — an extrapolation; not checked
> Not asserted — refuted (22), with the gate that decided:
>   H01 [LD.period.divides.8] refuted-heldout: CERT LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_eight
>   H04 [LD.white.finite] refuted-heldout: FORMAL WhiteDiagonals.ldiag_infinitely_many_white; LeftDiagonalPeriodsData.leftDiag_white_below_87868
>   H06 [LD.period.divides.16] refuted-by-prediction: CERT LeftDiagonalPeriodsData.not_leftDiagPeriodDivides_sixteen
>   H07 [LD.period.law.simple] refuted-heldout: stage test: separating observation: diagonal 53207 is eventually white with even parity outside it; the law predicts a jump at 53208 = True, actual = False
>   H12 [RD.lp.closed.D - floor((D + 1) / 3)] refuted-heldout: stage test: held-out D≤13: fails at D=10: exponent 6, form gives 7
>   H18 [CC.lc.half] refuted-heldout: CERT GLM.HypothesisEngine.WheelChecks.wheel_H19_false (2·L(11101) − 11101 ≥ 11)
>   H19 [CC.lc.half.2] refuted-on-escalation: escalation: n = 11101: |2·L(n) − n| = 11 > 10 (scale 12000); CERT GLM.HypothesisEngine.WheelChecks.wheel_H19_false (2·L(11101) − 11101 ≥ 11)
>   H21 [LD.seed.independent] refuted-heldout: stage test: all 128 seeds of width ≤ 8: first eventual differences at D ∈ [3, 8, 29, 400]; 14 seeds agree on every D < 450
>   H32 [GAP.centre.diagonal.connection] refuted-by-ledger: FORMAL DialogueChecks.transient_read_does_not_imply_aperiodic
>   H33 [GAP.unbounded.undecidable] refuted-by-ledger: FORMAL NeedsWheel.finite_data_never_forces_infinitely_many
>   H36 [APPTEST.uniformity.benchmark] refuted-by-recompute: recomputed on 60000 bits: centre 2-bit gap = 185, Thue–Morse 2-bit gap = 10000; a smaller gap is more uniform, so the centre column is more uniform than Thue–Mo
>   H37 [NRCI.clustered.equals.jumps] refuted-heldout: stage test: NRCI vs jumps: Jumps not clustered: [3, 29, 400]. The hypothesis fails.
>   H38 [TAX.defect.contains.jumps] refuted-by-guard: FORMAL TaxChecks.docstring_criterion_wrong
>   H39 [WOBBLE.transportable] refuted-on-escalation: escalation: seed 0b111: max D(N)²/N = 2738/665 ≠ 3200/731 (seed 1), N ≤ 5000; 2 distinct centre columns among the seeds read (scale 8 seeds (width ≤ 4))
>   H41 [TAX.mechanism.cluster] refuted-by-guard: FORMAL the law is proved from the left step alone: LeftDiagonalPeriods.ldiag_doubles, ldiag_keeps_of_even
>   H42 [TAX.substrate.model] refuted-heldout: depends on H41, already refuted (inherited at construction)
>   H45 [TAX.substrate.model.qualified] refuted-by-guard: CERT TaxChecksData.tax_conserved_not_only_white
>   H46 [WOBBLE.balanced.density] refuted-by-guard: identity fails; first failure at substrate (box<2), counterexample (1, 0, 0)
>   H47 [WOBBLE.transportable] refuted-on-escalation: escalation: seed 0b111: max D(N)²/N = 2738/665 ≠ 3200/731 (seed 1), N ≤ 5000; 2 distinct centre columns among the seeds read (scale 8 seeds (width ≤ 4))
>   H48 [WOBBLE.sturmian] refuted-heldout: stage test: sturmian test: balanced=False, aperiodic=False
>   H49 [BROKEN.tax.criterion] refuted-by-guard: identity fails; first failure at substrate (box<2), counterexample (1, 1, 0)
>   H50 [BROKEN.balance.criterion] refuted-by-guard: identity fails; first failure at rational (box<4), counterexample (2, 0, 0)
> Not asserted — retracted: H43.
> Not asserted — untested: H23, H24, H25, H26, H27, H28, H29, H31, H34, H40.
> Arrow: 15 hypotheses were read at layers; the read layer never decreased. Verdict flipped on the last read for ['H19', 'H39', 'H47']; all others converged.
