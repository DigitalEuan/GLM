# Wheel turn: `glm_wheel.json` re-gated by engine v18

Every entry of the previous wheel is imported as a sentence, recognised as an executable family where possible, and sent through the same gate cascade.

Movement between rings: {"doesn't-know -> doesn't-know": 4, 'thinks-true -> thinks-true': 3, 'thinks-true -> knows': 8, "thinks-true -> doesn't-know": 12}

| was | ring then | class | status now | ring now | reason |
|---|---|---|---|---|---|
| H11 | doesn't-know | Pi2 | **open** | doesn't-know | FORMAL open; proved reduction WhiteDiagonals.ldiag_periods_unbounded_iff |
| H41 | doesn't-know | meta | **untested** | doesn't-know | [class] new -> untested: class 'meta': no executable test; kept on the wheel |
| H42 | doesn't-know | meta | **untested** | doesn't-know | [class] new -> untested: class 'meta': no executable test; kept on the wheel |
| H11 | doesn't-know | Pi2 | **open** | doesn't-know | FORMAL open; proved reduction WhiteDiagonals.ldiag_periods_unbounded_iff |
| H02 | thinks-true | Pi1 | **survives-to** | thinks-true | CERT LeftDiagonalPeriodsData.centerCol_read_in_transient (20 ≤ D < 20000) |
| H03 | thinks-true | Pi1 | **survives-to** | thinks-true | escalation: survives every read, up to 5000 |
| H16 | thinks-true | finite | **proved** | knows | CERT WheelChecksData.wheel_H16_true |
| H17 | thinks-true | Pi1 | **survives-to** | thinks-true | CERT WobbleCertificate.wobble_sq_ratio_cert (holds for N <= 10^6) |
| H19 | thinks-true | Pi1 | **refuted-on-escalation** | knows | CERT WheelChecksData.wheel_H19_false (2·L(11101) − 11101 ≥ 11) |
| H23 | thinks-true | analogy | **untested** | doesn't-know | [class] new -> untested: class 'analogy': no executable test; kept on the wheel |
| H24 | thinks-true | analogy | **untested** | doesn't-know | [class] new -> untested: class 'analogy': no executable test; kept on the wheel |
| H25 | thinks-true | analogy | **untested** | doesn't-know | [class] new -> untested: class 'analogy': no executable test; kept on the wheel |
| H26 | thinks-true | analogy | **untested** | doesn't-know | [class] new -> untested: class 'analogy': no executable test; kept on the wheel |
| H27 | thinks-true | analogy | **untested** | doesn't-know | [class] new -> untested: class 'analogy': no executable test; kept on the wheel |
| H28 | thinks-true | analogy | **untested** | doesn't-know | [class] new -> untested: class 'analogy': no executable test; kept on the wheel |
| H29 | thinks-true | trend | **untested** | doesn't-know | [class] new -> untested: class 'trend': no executable test; kept on the wheel |
| H30 | thinks-true | estimate | **estimate** | doesn't-know | [class] new -> estimate: an extrapolation: only reaching the predicted range checks it |
| H31 | thinks-true | implication | **unchecked-implication** | doesn't-know | [implication] new -> unchecked-implication: no checked implication edge |
| H32 | thinks-true | implication | **refuted-by-ledger** | knows | FORMAL DialogueChecks.transient_read_does_not_imply_aperiodic |
| H33 | thinks-true | implication | **refuted-by-ledger** | knows | FORMAL NeedsWheel.finite_data_never_forces_infinitely_many |
| H34 | thinks-true | analogy | **untested** | doesn't-know | [class] new -> untested: class 'analogy': no executable test; kept on the wheel |
| H35 | thinks-true | measurement | **untested** | doesn't-know | [final] new -> untested: no executable test was attached (an import the engine could not recognise) |
| H36 | thinks-true | comparison | **refuted-by-recompute** | knows | EXACT recomputation: centre gap = 185, Thue–Morse gap = 10000; a smaller gap is more uniform, so the centre column is more uniform |
| H39 | thinks-true | Pi1 | **refuted-on-escalation** | knows | EXACT counterexample: seed 111: max D(N)²/N = 2738/665 ≠ 3200/731 (seed 1) |
| H40 | thinks-true | trend | **untested** | doesn't-know | [class] new -> untested: class 'trend': no executable test; kept on the wheel |
| H44 | thinks-true | Pi1 | **proved** | knows | FORMAL TaxChecks.tax_conserved_at_doubling |
| H47 | thinks-true | Pi1 | **refuted-on-escalation** | knows | EXACT counterexample: seed 111: max D(N)²/N = 2738/665 ≠ 3200/731 (seed 1) |

## Needs the previous wheel stated

| need | status | met by |
|---|---|---|
| NEEDED-1: find an invariant that is NOT forced by white(D-1) — e.g., the parity of D-2 read two out  | answered (negative for the proposed invariant) | FORMAL DialogueChecks.doubling_law_tie_unsplittable: at a white diagonal the parities of D−1 and D−2 coincide, so the parity read two out is forced and no data  |
| NEEDED-2: a guard-extractor for the R-calculus domain — test whether R-calculus pipelines produce th | unmet | no R-calculus pipeline is available to this engine; the claim stays UNTESTED |
| NEEDED-3: a guard-extractor for the seed-memory domain — test whether the seed-forgetting law (H22)  | met | FORMAL LeftDiagonalPeriods.first_difference_after_white (the seed-memory law is proved, so no guard is needed) |
| NEEDED-4: extend the automaton run past D=87867 to test H43 (TAX defects beyond 87867 cluster around | unmet | beyond this engine's budget; the needed run is stated as a range need |
| NEEDED-5: formalise the TAX defect closed form in Lean: defect = -2(3c^2 - 2c(a+b) + ab). The identi | met | FORMAL TaxChecks.tax_defect_eq, tax_conserved_iff_defect_zero |
| NEEDED-6: test the engine on a fourth domain (e.g., the right-diagonal structure or the centre-colum | met | engine v18: general-reasoning and ARC domains in the same gate loop (see the general and ARC reports) |
| NEEDED-7: automatic guard-input derivation: parse the hypothesis's Lean statement to extract the alg | partly met | engine v18: RECOGNISERS map sentences to executable families; unrecognised sentences are classified and kept with a need |

## Language wheel re-checked

| concept | status now | keep? |
|---|---|---|
| every left diagonal has eventual period dividing 8 | refuted-on-escalation | yes |
| the eventually white left diagonals are exactly [2, 7, 28] | refuted-on-escalation | yes |
| every left diagonal D < 400 has eventual period dividing 8 | proved | yes |
| every left diagonal has eventual period dividing 16 | refuted-by-ledger | yes |
| a left diagonal's period exceeds the periods of the two diagonals outside it exactly when white(D-1) | proved | yes |
| the first left diagonal with least eventual period 32 is D = 87867 | proved | yes |
| every left diagonal D < 87867 has eventual period dividing 16 | proved | yes |
| the least period of right diagonal D divides 2^D | proved | yes |
| the least period of right diagonal D exceeds ceil(D/2) | proved | yes |
| (transported from the left-diagonal law) every right diagonal is periodic or anti-periodic with the  | proved | yes |
| a left-white row can first differ from the seed only one diagonal past an eventually white diagonal  | proved | yes |
| v13 POSITIVE FINDING: at every confirmed period-doubling diagonal D ∈ {3, 8, 29, 400}, TAX is CONSER | proved | yes |
| GAP.next.estimate (the next period-doubling diagonal) | estimate | no |
