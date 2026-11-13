# Execution workflow

**Authority:** [`DIRECTIVE.md`](DIRECTIVE.md) owns the objective, binding rules,
work order and scoreboard. This file is the execution tracker: it records
state, gates and completion records. It may not invent, reorder or widen the
directive's work.

**Adopted:** 2026-11-12. **State:** D1–D7 complete and gated; no active D-item.
D6 is reported as a bounded retrodictive measurement, not general capability
evidence.

## 1. Current state

All six directive items are complete. The task board below is the execution
record; the scoreboard is owned by [`DIRECTIVE.md`](DIRECTIVE.md) §6 and is not
copied here. Remaining evidence gaps are in [`docs/CURRENT_SCOPE.md`](docs/CURRENT_SCOPE.md);
they are not authorized work until promoted to a new directive item.

The live gate count is the README statistics row. The canonical command is:

```bash
python3 tests/run_all.py
```

Run the focused suite for the area being changed, then the full gate. A check
count is not a capability result.

## 2. Scoreboard

The authoritative scoreboard is [`DIRECTIVE.md`](DIRECTIVE.md) §6. It is not
copied here. The gate is hygiene, not progress on those six numbers; reference
certificates are adapter tests, not evidence of origination or utility.

## 3. Task board

Order and gates come only from `DIRECTIVE.md` §4.

| Item | Status | Entry condition | Gate | Kill / stop |
|---|---|---|---|---|
| **D1 — falsifiable evaluation** | **Complete, gate green** | none | Constant `_score`: recall 8/10 → 4/10, cases 3/4 → 1/4, targets 8/8 → 3/8; negative failures 2/6 → 4/6; baseline certified false | None. Worse honest numbers are the deliverable |
| **D2 — split Μ from ∆; executable Τ** | **Complete, gate green** | D1 gate green | Deleted both generated cards; rebuilt both from `kcl-conservation` plus operator chains; four certificates byte-identical; 11/11 ablation checks | No kill; `scale-offset` and `effort-flow-duality` acquired executable semantics |
| **D3 — recover suppressed operations** | **Complete, gate green** | D2 gate green | `exp`, `log`, `mult`, `div` and `reciprocal` supported with generated mappings and passing target tests; corrected negative controls still refuse the wrong Δ; 13/13 target pairs pass | No kill; every operation met the declared `1/10000` tolerance |
| **D4 — compiler as target** | **Complete, gate green** | D3 gate green | Two adopted self-transfers with measured non-zero deltas and exercised rollbacks; `32/152` → `152/152` and `4/12` → `12/12` | No kill; both candidates beat their baselines |
| **D5 — refutation and generated negatives** | **Complete, gate green** | D1 gate green | 8 generated negatives exceed the 6 hand-declared controls; every negative has a witness pair; 10/10 test obligations are derived | None; rule is sound by construction |
| **D6 — retrodictive holdout** | **Complete, report includes a negative-control refusal** | D1–D3 complete; D4 nonzero origination | Five frozen pre-1940 mechanisms retrieve five dated post-cutoff targets at rank one (`5/5`), with one declared false-positive candidate, one excluded candidate, and a strict RSA negative control reporting `no_licensed_source` and one coverage miss | Kill did not fire; the negative-control refusal is reported rather than hidden |
| **D7 — recover sign** | **Complete, gate green** | D6 gate green | Added a `threshold-comparator` mechanism and exact `glm-reference` adapter; negative, zero and positive fixed vectors pass; wheel is 10/10 testable | No kill; zero branch is exact by declaration, no measured comparator claimed |

D5's gate is green. D6's stated kill criterion is "if origination is still zero
after D3", and D4 recorded a nonzero self-transfer origination. Its entry
condition was therefore satisfied. The D6 report is complete as a measurement:
5/5 rank-one recall, one declared false-positive candidate, one excluded
candidate, and a strict RSA negative control that returns no candidates and
reports `no_licensed_source` plus one coverage miss. The negative-control refusal
is reported explicitly; it does not inflate the production origination count.

## 4. Section 8 owner resolution

Owner direction: **test and follow the best application based on results.**

- **GLM:** audit-only narrow probe for the current scope. `cent-self` is D4's primary target.
  GLM becomes controlled only if a measured utility delta beats its named
  baseline and the independent oracle confirms it.
- **D3:** in scope and scheduled as D3. The declared log-domain/antilog hardware
  is the highest value-to-cost path; results decide which operations survive
  tolerance.
- **D1 regression:** accepted. The 10/10 headline is withdrawn once D1 lands;
  publish the worse honest baseline instead of defending the old number.

## 5. D1 completion record

1. Removed the `supported_operations` membership filter from `retrieve()`.
2. Every card is scored; `supported_operations` remains validation metadata.
3. Rebuilt expected candidates from written provenance, not card fields.
4. Replaced `retrieved − expected` false-positive accounting with an explicit
   unlabelled-candidate triage queue.
5. Added `tests/test_evaluation_sabotage.py`; constant scoring drops recall
   from 8/10 to 4/10, cases from 3/4 to 1/4 and target candidates from 8/8 to
   3/8.
6. Recorded the honest baseline: 8/10 recall, 3/4 cases, 2/6 negative-control
   failures, 13 triaged candidates, `certified: false`.
7. Updated the README, current-scope ledger and roadmap; 10/10 is historical
   only.

The D1 gate is green.

## 6. D2 completion record

1. Moved the executable mapping operators into `cent_compiler/mapping.py`.
2. Added `check(model) -> bool` and `apply(model) -> dict` to all seven
   operators; apply refuses an unmet precondition.
3. Split the registry into six hand-authored principle cards and two
   `DeltaInterpretation` records whose cards are generated by running their
   operator chains over `kcl-conservation`.
4. Added `principle_id` and `operators` to `cent-mechanism/1` cards; generated
   cards carry `kcl-conservation` and their exact operator sequence.
5. Added `tests/test_ablation.py`: it removes both generated cards, rebuilds
   them from the interpretations, swaps the rebuilt registry into retrieval and
   validation, and compares four sum/difference certificates byte-for-byte.
6. Regenerated the twelve proposal bundles and `examples/transfer/evaluation.json`;
   proposals now carry the generating principle and operator chain.

The D2 gate is green: 11/11 ablation checks, 19/19 suites and 846/846 checks at
that point. D3 later raised the gate to 20 suites and 871 checks.

## 7. D3 completion record

1. Added a `transcendental-identity` principle and generated the
   `log-domain-arithmetic` Δ card from `composition`; the sqrt card remains
   sqrt-specific.
2. Retrieval gives a declared operation support a weak `+2` signal (never a
   filter), so the generated card can rank while labels stay independently
   authored.
3. Added source routes `exp`, `log`, `mult`, `div` and `reciprocal` to
   `assembly.py`, with the declared programs `exp`, `log`,
   `log → log → sum → exp`, `log → log → neg → sum → exp` and
   `log → neg → exp`.
4. Added independent `glm-reference` adapters and fifteen fixed vectors, plus
   operation-local latency and bit budgets in the target profile.
5. Added D3 positive cases, removed the five operations from the unadapted
   corpus, and rewrote the inverted `exp`/`log` controls to refuse the
   sqrt-specific cam Δ while naming `transcendental-identity` as the unblock.
6. Added `tests/test_log_domain.py`: 25 checks over source routes, vectors,
   target adapters, tolerance, regeneration, retrieval, corpus labels and JSON
   safety.
7. Regenerated all nine proposal bundles (27 proposals: 13 ready, 14 needing a
   target adapter) and `examples/transfer/evaluation.json`.
8. Updated the README, directive, workflow, current-scope ledger, roadmap,
   objective and examples README.

**Measured tolerance:** maximum target enclosure widths are `1/92897280`
(`exp`), `1/9814652388` (`log`), about `1.2e-8` (`mult`), about `4.24e-8`
(`div`) and about `2.94e-8` (`reciprocal`), all below the declared `1/10000`.
No operation hit the kill condition.

**Evaluation after D3:** 14/15 candidate recall, 8/9 case recall, 2/6
negative-control failures, 13/13 target pairs and 13 artifacts; 13 unlabelled
candidates triaged; `certified: false`. The remaining miss is
`sqrt/orifice-pressure-flow`; the two explicit negative-control failures are
unchanged from D1. The gate at that point was 20/20 suites and 871/871 checks;
D4 later raised it to 21/21 and 892/892.

## 8. D4 completion record

1. Added `cent-self` (and `cent self`) plus the `cent-utility/1` record schema,
   ledger writer and `examples/self/utility.json`.
2. Promoted the exact Bresenham one-tick proof into
   `cent_compiler/quantized_carry_floor.py`; over 152 integer walks the new
   contract agrees `152/152`, while the existing two-tick target agrees
   `32/152` (`delta +120/152`).
3. Added exact runtime junction invariants over `cent-program/1`; over twelve
   injected structural and semantic faults, static `topology_audit` detects
   `4/12` and the runtime check detects `12/12` (`delta +8/12`).
4. Added `self_oracle.py`: it recomputes the law directly, confirms every
   injected fault, and issues `cent-utility-certificate/1` with
   `candidate_on_certificate_path: false` (R5).
5. Added `--adopt`/`--revert`; rollback is exercised by re-running the named
   baseline path and confirming it restores `32/152` and `4/12` respectively.
6. Extended the durable proposal review ledger with `adopted` and `reverted`
   decisions.
7. Added `tests/test_self_target.py`: 21 checks over the contract, benchmarks,
   oracle, records, rollback, review states and CLI entry points.

The D4 gate is green: both self-transfers are adopted with measured non-zero
utility deltas and working rollbacks. No kill condition fired. The canonical
gate is 21/21 suites and 892/892 checks at that point.

## 9. D5 completion record

1. Added `cent_compiler/refutation.py`: 13 declared witness instances, exact
   signature grouping, and 8 generated negatives against 6 hand-declared
   controls.
2. Each `cent-tier-d-witness/1` names the shared signature, the two instances,
   the differing observable probe and both values; the conclusion is limited to
   a signature-only map.
3. Reproduced the Q-tensor retirement automatically from the identical scalar
   invariants and the `2/1` versus `66/25` envelope areas.
4. Added contract-derived obligations for `quantized_carry`: bounded state from
   `signature.outputs.code = bounded sequence`, and mean reconstruction from
   `signature.outputs.mean`.
5. Derived one observable-separation obligation per witness; all 10 obligations
   have `authored: false`.
6. Added `cent refute`, `review/refuter_demo.py` and the portable
   `examples/refutation/negatives.json` ledger.
7. Added `tests/test_refutation.py`: 19 checks.

The D5 gate is green: 8 > 6, each negative has a witness pair, and every test
obligation is derived. The canonical gate was 22/22 suites and 911/911 checks
at that point.

## 10. D6 completion record

1. Added `cent_compiler/holdout.py`: a five-mechanism library frozen before
   1940, five dated post-cutoff targets, structural ranking and explicit
   false-positive constraints.
2. Dated the sources before the cutoff: metallurgical annealing (undated),
   Pearson random walk (1905), Ising spins (1925), Boltzmann kinetic theory
   (1872) and Plateau soap films (1873). Target publications are 1941–1988.
3. Added the target citations and provenance URLs; retrieval never reads a
   mechanism card's `supported_operations`.
4. Recorded the measured result: `5/5` rank-one recall, zero misses, one
   false-positive candidate (`kinetic-theory` for the resistor-network target,
   `1/15` retrieved), and one excluded candidate.
5. Excluded Bresenham ↔ delta-sigma because the 1965 source is post-cutoff and
   the D4 correspondence is internal evidence.
6. Added the pre-registered `rsa-modular-exponentiation` strict negative
   control. Its required `mod` primitive is absent from every frozen source;
   the control returns `no_licensed_source`, retrieves no candidates and records
   a coverage miss.
7. Added `cent holdout`, `examples/holdout/ledger.json` and
   `examples/holdout/README.md`.
8. Added `tests/test_holdout.py`: 27 checks.

The canonical gate is the current `tests/run_all.py` run. D6 is complete as a
reported, bounded retrodictive measurement with an explicit negative-control
failure; it is not counted as production origination.

## 11. D7 completion record

1. Added the `threshold-comparator` card: an exact three-level law with
   bounded rails, an explicit zero branch and declared offset/hysteresis gaps.
2. Added `exact_sign_reference` and three fixed vectors (negative, zero,
   positive) to the `glm-reference` target. The adapter has no float and no
   hidden state.
3. Added `sign` to the evaluation corpus as a known-valid positive, removed
   the old unadapted case, and kept the exact reference boundary explicit.
4. Generated the `examples/transfer/sign/` bundle and refreshed
   `examples/transfer/evaluation.json`.
5. The operation wheel is now 10/10 testable; the evaluation is 15/16 candidate
   recall, 9/10 case recall, 14/14 target pairs and 2/6 negative-control
   failures. D7 is hand-authored, so the origination score remains 1/9.
6. Updated the gate counts and the sign target interface; no measured
   comparator, offset, hysteresis or metastability claim is made.

### Experimental side-arm: machine composer

The `cent machine` side-arm is **not D8** and does not change the directive or
scoreboard. It composes a complete function tree and executes the branch it can
test. The first machine, `sigma-delta-sqrt`, selects `sum -> kcl-conservation`,
`sign -> threshold-comparator` and `quantized_carry -> delta-sigma-error-feedback`
from the existing rankings, validates a one-bit 100,000-sample digital branch
(error `4.573e-06`, in-band suppression `36.92 dB`, NTF slope `28.02 dB/dec`),
and leaves the analog reconstruction, jitter and supply stages as explicit gaps.
It adds `test_machine.py` (23 checks) to the gate. Assembled routes can also
be wrapped in the same four-stage template; `--load mechanical|fluid` selects a
declared TIER 3 transducer branch without claiming a measured load. See
[`docs/MACHINES.md`](docs/MACHINES.md).

## 12. Repository health

- The directive appendix now names only files that exist. The historical
  `TOP_LEVEL_REVIEW.md`, retrieval probe and read-only source snapshot were not
  retained and no task depends on them.
- `README.md` owns the live gate count; this file and the other ledgers run the
  command instead of copying the number.
- `docs/KNOWLEDGE_ATLAS.md` owns the part/address/stitch rules. Use
  `python3 cent knowledge find` before adding another status document.
- `applications/README.md` owns the shared pipeline, parameters and run commands
  for the 22 legacy show-work proposals.
- Generated output (`cent_out/`, `__pycache__/`) is ignored; do not treat it as
  repository content.

## 13. Reporting rule

Every task closes with:

- the gate command and its exit status;
- the measured before/after values, including regressions;
- which kill criterion fired, if any;
- what remains blocked and the evidence that would unblock it.

No task is reported as complete from a check count alone.
