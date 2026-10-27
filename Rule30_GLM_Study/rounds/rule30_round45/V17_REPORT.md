# GLM Hypothesis Engine v17 — report (Round 45)

v17 is the owner's v16 engine with the gate loop fixed. Its architecture is the one described in
`v16_implementation_report.md` and the Master Equation sketch (`GLM_Escalation_Boundaries_Exploration.md`):

* TCT as the gate inside the loop;
* five layer-aware guards;
* transitive rollback;
* a clean dialogue.

Each of these mechanisms now does what its name says, and the Lean file
`RequestProject/GLM/HypothesisEngine/GateLoop.lean` proves what each one guarantees.

Everything here is pure Python 3 (standard library) with exact integer and `Fraction` arithmetic.
All files are in this folder:

    python3 hypothesis_engine_v17.py [--quick] [--no-ledger] [--out DIR]   # about 25 s
    python3 run_round45.py [--quick]      # v15, v16, v17 side by side, scored (about 2.5 min)
    python3 test_round45.py               # 28 checks, including one quick engine run

## 1. What was wrong in v15/v16

We found these defects by running the uploaded code.

| # | Defect | Where | Effect |
|---|---|---|---|
| 1 | v15/v16 import `hypothesis_engine_v14`, `glm_guards` and `tax_guards`, which are only in `rule30_round42/` | imports | Run from the project folder, `hypothesis_engine_v16.py` stops with `ModuleNotFoundError: hypothesis_engine_v14` |
| 2 | The layers are labelled "mod 2/4/8/144/256", but they are box sizes (identity), domain cut-offs (explained-away) and sample sizes (coincidence) | layered guards | The labels claim residue arithmetic that is never computed |
| 3 | Explained-away is aggregated as "explained at ANY layer" | `explained_away_guard_layered` | A layer with no events is vacuously explained; the verdict can contradict the largest layer (Lean `anyScale_vacuous`, `anyScale_ne_largest`) |
| 4 | Layered coincidence shrinks N and scales K, but keeps the number of events and of hits fixed | `coincidence_test_layered` | The small layers mix two different samples |
| 5 | Rollback fires only on guard refutations, and along every parent edge whatever its type | `_rollback_children` | Narrowed and cut claims are children of refuted parents. H05 and H10 are proved in Lean, but they would be retracted if their parents had been refuted by a guard (Lean `derived_edge_unsound`). Later stages also overwrite a retracted status |
| 6 | Analogies, proposals, meta statements and trends get the status `survives`, and the clean dialogue speaks every claim that is not refuted | stages + `CleanDialogue` | 10 statements with no executable test are spoken as surviving claims |
| 7 | H36 prints its comparison the wrong way round (`'more' if 185 > gap_tm else 'less'`), with the centre's gap hard-coded as 185 | `run_application_tests` | The engine states that the centre column is *less* uniform than Thue–Morse. Its 2-bit gap is 185 against 10000, so it is *more* uniform |
| 8 | H19 narrows its constant on n ≤ 3000 and speaks it without reading further | `run_centre` | False at n = 11101 (Lean `wheel_H19_false`) |
| 9 | H39/H47 test "same wobble across seeds" on seeds 1, 11 and 101 | wobble domain | These three seeds give the **same** centre column (checked exactly to 30000 bits), so the test has one sample, not three. Seed 111 refutes the claim |
| 10 | H32 and H33 are implications, spoken as surviving | gap analysis | Both are refuted in Lean (`transient_read_does_not_imply_aperiodic`, `finite_data_never_forces_infinitely_many`) |
| 11 | Quick mode: H20 is "refuted" because the 20000-bit prefix ran out before every 12-bit word appeared | `run_centre` | A refutation with no counterexample. Read to k = 13 (about 160000 bits), the claim survives |
| 12 | H16's statement depends on the run mode: preperiod ≤ 10000 in quick mode, ≤ 30000 in full mode | `run_centre` | No Lean result covered 30000. This round adds one (`GateLoopData.centre_no_short_period_30000`) |

## 2. What v17 does

**The TCT gate cascade, inside the loop.** After every stage, each hypothesis the stage created
or changed goes through the gates in this order:

1. **claim class** — what kind of evidence could settle the claim?
   * finite statement;
   * universal "for every n" (Π₁);
   * "infinitely many / unbounded" (Π₂);
   * implication, comparison, measurement or estimate;
   * analogy, proposal, meta statement or trend (no executable test).

   A claim with no test becomes `untested`. A Π₂ claim becomes `open`.
2. **recompute** — re-derive a reported comparison from the data. H36 is refuted this way, and
   the corrected statement is emitted as a new hypothesis, `verified-exact`.
3. **refutation audit** — a stage refutation of a claim we can re-read must come with a
   counterexample. This catches defect 11.
4. **escalation** (escalate before assert) — a surviving universal claim is read at five growing
   scales. The first failure refutes it, with the counterexample. If no scale fails, the claim
   becomes `survives-to <scale>`, which says nothing beyond that scale.
5. **implication** — an "A implies B" claim needs a checked edge. Without one it becomes
   `unchecked-implication`.
6. **ledger** — the Lean results (FORMAL or CERT, each cited by its theorem name) decide. This
   is the only gate that can raise a claim to `proved`. A disagreement between the ledger and the
   other gates is reported as a conflict; there were none.

Soundness (Lean `cascade_sound`, `cascade_no_wrong`): if every gate is sound, the cascade never
refutes a true claim and never proves a false one. v16's rule "survived the data, so true" is
not a sound gate for any amount of data (`survives_as_proved_unsound`).

**Honest layers** (`glm_layers.py`). The five GLM names are kept, each with its real scale. The
verdict depends on the kind of claim:

* **universal** — refuted at the first failing layer. The passing layers must form a prefix
  (Lean `holdsAt_anti`, `firstFail_spec`). This is checked at run time and reported as
  "layer-shape violations"; there were none.
* **statistic or explanation** — the verdict at the *largest* layer.
* **"only at S"** — the verdict as stated. The looser radii measure the distance from true;
  the passing radii form a suffix (`exclusive_mono`).

**Typed rollback, computed as a fixpoint.** A refutation propagates only along dependency
edges: prediction, lift, analogy and transport. It does not propagate along derived edges:
cut, narrow, a mechanism read off a counterexample, or a control. Lean proves four things:

* the retracted set is the least closed set (`retracted_least`);
* the set of claims no longer asserted does not depend on the order of refutations
  (`retracted_union`; also tested on 200 random dependency forests);
* rollback is sound when the edges are truthful (`rollback_sound`);
* the engine's loop terminates and computes exactly that set (`loop_terminates`,
  `loop_eq_retracted`).

**The arrow** (the owner's Wobble/Observer proposal). Every hypothesis carries the layers that
were read and the verdict at each. The read layer only goes up: escalation reads an initial
segment of an increasing ladder (Lean `reads_prefix`, `reads_sorted`). A refutation is never
undone by reading higher (`refuted_stable`, `escalate_append`). The direction is either
"converging" (the verdict was stable over the last two reads) or "flipped at <layer>". In the full
run three hypotheses flip, and each flip is a refutation found by reading higher:

* H19 flips at the 4th layer (n ≤ 12000, failure at 11101);
* H39 and H47 flip at the 2nd layer (seeds of width ≤ 4, failure at seed 111).

All other reads converge. So the arrow tells the GLM which claims are still converging and where
a run turned.

**The trajectory dialogue.** Only backed claims are spoken, each with its backing:

* `proved` (with the Lean name);
* `verified-exact`;
* `survives-to` (with the scale);
* `measured`;
* `open`;
* `estimate`.

Refuted claims are summarised with the gate that decided them. Retracted, untested and unchecked
claims are listed and never asserted. The consistency check confirms that no spoken claim has a
non-speakable status and that every spoken claim has a backing.

## 3. Results

The ground truth is the `TRUTH` table of Round 44 (`needs_rule30.py`), fixed before v17 was
written. It covers the 24 engine statements that have a settled answer or are known to be open.
The hypothesis ids name the same statements in every engine; the run checks this.

**Full run** (`out/round45_results.md`):

| engine | right | wrong | overclaim | abstain |
|---|---|---|---|---|
| v15 | 4 | 5 | 15 | 0 |
| v16 | 4 | 5 | 15 | 0 |
| v17 without the ledger gate | 20 | 0 | 0 | 4 |
| v17 with automatic claim classes | 24 | 0 | 0 | 0 |
| v17 | 24 | 0 | 0 | 0 |

The quick run gives the same numbers (`out/round45_results_quick.md`).

**Full run of v17, over its 51 hypotheses** (`out/engine_v17.md`):

| status | count | which |
|---|---|---|
| proved in Lean | 10 | H05, H08, H09, H10, H13, H14, H15, H16, H22, H44 |
| verified exactly | 1 | H51, the corrected H36 |
| survives to a stated scale | 4 | H02, H03 (D < 20000); H17 (N ≤ 100000; certified to 10⁶); H20 (k ≤ 13) |
| open | 1 | H11 |
| refuted | 22 | — |
| retracted | 1 | — |
| untested | 10 | — |
| other | 2 | one estimate, one measurement |

The run found:

* no conflicts with Lean;
* no layer-shape violations;
* a clean dialogue (18 claims spoken, all backed).

**What the numbers mean, and what they do not.**

* *Without the ledger gate*, v17's own gates turn v16's 5 wrong answers and 15 overclaims into
  20 right answers and 4 abstentions. Each of these four (H16, H32, H33, H44) needs a proof, and
  without the ledger v17 says it cannot decide.
  * H19 and H39 are refuted by escalation alone, and H36 by recomputation.
  * These are independent of the ledger and of the ground-truth sources.
* *With the ledger gate* the remaining four are settled by Lean results. The ledger and the
  ground truth draw on the same Lean files, so this part measures that each question is routed
  to the checked result. It is not discovery.
* The per-statement claim classes were written by reading these same 50 statements, and so was
  the automatic classifier (`auto_claim_class`, which uses only the sentence). Neither is a
  held-out test. The automatic classifier agrees with the registry on 39 of 51 statements.
  * Most disagreements are within the no-test classes, which all lead to `untested`.
  * Its final statuses differ on 3 statements, H29, H31 and H47, and the final answer changes
    only for H47 (not in the ground truth). The classifier reads H47 as a meta statement,
    leaves it `untested`, and so misses the seed refutation that the registry's class finds.
* The real test of the gates is a new domain. As the v16 report already proposes, that is the
  next step.

## 4. The Master Equation correspondence

| Master Equation component | v17 |
|---|---|
| TCT as gate inside the loop | `EngineV17._stage` runs `tct_gate` on every hypothesis a stage touched, then the rollback fixpoint |
| the 5-layer filter cascade | five reads per guard with real scales (`glm_layers.py`); verdict rule per kind of claim |
| snap = the only place a layer changes | statuses change only in `tct_gate`, the guards and the rollback; the ledger is the only gate that raises a claim to `proved` |
| escalation on rejection (Round 43 correction: never roll back into a deadlock) | escalate before assert, refutation audit |
| transitive rollback | typed edges, least fixpoint, order independent |
| arrow / observer read position | the per-hypothesis read trajectory; monotone read layer; converging or flipped |
| clean trajectory | `TrajectoryDialogue` plus its consistency check |

## 5. Using v17 in the GLM

1. Keep the registries separate from the engine: `CLAIM_CLASS`, `ESCALATIONS`, `RECOMPUTE`,
   `IMPLICATIONS` and `LEDGER`. A new domain adds entries; the gates do not change.
2. Put only checked provisions in `LEDGER` and `IMPLICATIONS` (Lean `NeedsWheel.unsound_can_hurt`).
   Index each entry by the statement's parameters, not only its key. H16's preperiod and H19's
   constant change with the run mode.
3. Treat `survives-to` as "no verdict". Score overclaim separately.
4. Read the arrow. A claim whose verdict flips on the last read should not be reused until it has
   been read again higher.
5. Open item: one Rule 30 observation worth a proof. Seeds 1, 11 and 101 give the same centre
   column (checked exactly to 30000 bits; not proved), while seed 111 differs at the 4th bit.
   Black cells to the right of the seed cell seem not to reach the centre column in some cases.
