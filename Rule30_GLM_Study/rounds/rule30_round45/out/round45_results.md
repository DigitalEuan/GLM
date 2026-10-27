# Round 45 — engines v15, v16, v17 scored against the Round 44 ground truth

quick = False; 24 statements with a ground truth fixed before v17 existed (Round 44 `TRUTH`); ids aligned across engines: True

| engine | right | wrong | overclaim | abstain | seconds |
|---|---|---|---|---|---|
| v15 | 4 | 5 | 15 | 0 | 26.6 |
| v16 | 4 | 5 | 15 | 0 | 26.6 |
| v17 without ledger gate | 20 | 0 | 0 | 4 | 35.1 |
| v17 automatic claim classes | 24 | 0 | 0 | 0 | 27.4 |
| v17 | 24 | 0 | 0 | 0 | 27.9 |

| id | key | truth (source) | v15 | v16 | v17 without ledger gate | v17 automatic claim classes | v17 |
|---|---|---|---|---|---|---|---|
| H02 | `LD.preperiod.gt.D` | None (OPEN beyond the CERT range: 20 <= D < 20000 is `centerCol_read_in_tran) | survives (overclaim) | survives (overclaim) | survives-to (right) | survives-to (right) | survives-to (right) |
| H03 | `LD.preperiod.envelope` | None (OPEN: holds for 20 <= D < 20000 (exact, this round), not proved) | survives (overclaim) | survives (overclaim) | survives-to (right) | survives-to (right) | survives-to (right) |
| H11 | `LD.periods.unbounded` | None (OPEN (ledger C359); equivalent to infinitely many white diagonals meet) | open (right) | open (right) | open (right) | open (right) | open (right) |
| H16 | `CC.no.short.period` | True (CERT `WheelChecksData.wheel_H16_true`) | survives (right) | survives (right) | survives-to (abstain) | proved (right) | proved (right) |
| H17 | `CC.balance.sqrt` | None (OPEN: holds to N = 10^6 (exact, this round); iterated-logarithm heuris) | survives (overclaim) | survives (overclaim) | survives-to (right) | survives-to (right) | survives-to (right) |
| H19 | `CC.lc.half.2` | False (CERT `WheelChecksData.wheel_H19_false` (fails at n = 11101)) | survives (wrong) | survives (wrong) | refuted-on-escalation (right) | refuted-on-escalation (right) | refuted-on-escalation (right) |
| H23 | `APP.lattice.addressing` | None (analogy, no test given) | survives (overclaim) | survives (overclaim) | untested (right) | untested (right) | untested (right) |
| H24 | `APP.rcalculus.model` | None (proposal, not a claim) | survives (overclaim) | survives (overclaim) | untested (right) | untested (right) | untested (right) |
| H25 | `APP.evidence.prediction` | None (meta statement) | survives (overclaim) | survives (overclaim) | untested (right) | untested (right) | untested (right) |
| H26 | `APP.deephole.ladder` | None (analogy, no test given) | survives (overclaim) | survives (overclaim) | untested (right) | untested (right) | untested (right) |
| H27 | `APP.retrieval.uniformity` | None (proposal, not a claim) | survives (overclaim) | survives (overclaim) | untested (right) | untested (right) | untested (right) |
| H28 | `APP.conversation.reset` | None (analogy, no test given) | survives (overclaim) | survives (overclaim) | untested (right) | untested (right) | untested (right) |
| H29 | `GAP.ratio.growing` | None (meta statement) | survives (overclaim) | survives (overclaim) | untested (right) | open (right) | untested (right) |
| H30 | `GAP.next.estimate` | None (OPEN extrapolation; conflicts with the EMP run-up prediction 2,107,985) | survives (overclaim) | survives (overclaim) | estimate (right) | estimate (right) | estimate (right) |
| H31 | `GAP.chain.explanation` | None (causal reading of a search result; not a mathematical claim) | survives (overclaim) | survives (overclaim) | untested (right) | unchecked-implication (right) | untested (right) |
| H32 | `GAP.centre.diagonal.connection` | False (FORMAL `DialogueChecks.transient_read_does_not_imply_aperiodic` (the i) | survives (wrong) | survives (wrong) | unchecked-implication (abstain) | refuted-by-ledger (right) | refuted-by-ledger (right) |
| H33 | `GAP.unbounded.undecidable` | False (FORMAL `NeedsWheel.finite_data_never_forces_infinitely_many` (no finit) | survives (wrong) | survives (wrong) | unchecked-implication (abstain) | refuted-by-ledger (right) | refuted-by-ledger (right) |
| H34 | `APPTEST.ladder.spacing` | None (analogy, no test given) | survives (overclaim) | survives (overclaim) | untested (right) | untested (right) | untested (right) |
| H35 | `APPTEST.rcalculus.match` | None (not checkable in this package (R-calculus pipeline not available)) | survives (overclaim) | survives (overclaim) | measured (right) | measured (right) | measured (right) |
| H36 | `APPTEST.uniformity.benchmark` | False (EXACT: the centre column's 2-bit gap 185 is SMALLER than Thue-Morse's ) | survives (wrong) | survives (wrong) | refuted-by-recompute (right) | refuted-by-recompute (right) | refuted-by-recompute (right) |
| H39 | `WOBBLE.transportable` | False (EXACT: seeds 0b1001, 0b10001, 0b100001 give 81/25, 441/124, 8/3 (the u) | survives (wrong) | survives (wrong) | refuted-on-escalation (right) | refuted-on-escalation (right) | refuted-on-escalation (right) |
| H40 | `DS.accumulator.growing` | None (trend on four sample points; no statement to prove) | survives (overclaim) | survives (overclaim) | untested (right) | untested (right) | untested (right) |
| H41 | `TAX.mechanism.cluster` | False (FORMAL: the law is proved (`ldiag_doubles`, `ldiag_keeps_of_even`); it) | refuted-by-guard (right) | refuted-by-guard (right) | refuted-by-guard (right) | refuted-by-guard (right) | refuted-by-guard (right) |
| H44 | `TAX.conserved.at.jumps` | True (FORMAL `TaxChecks.tax_conserved_at_doubling`) | law-holds (right) | law-holds (right) | survives-to (abstain) | proved (right) | proved (right) |

v17 dialogue consistency: {'spoken': 18, 'spoken_not_speakable': [], 'spoken_without_backing': [], 'ok': True}
v17 conflicts with Lean: none
v17 layer-shape violations: none
