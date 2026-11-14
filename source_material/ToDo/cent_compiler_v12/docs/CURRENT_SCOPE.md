# Current capability and gap ledger

**Last reviewed:** 2026-11-13  
**Canonical gate:** `python3 tests/run_all.py`; the README statistics row owns the live count  
**Work-order authority:** [`DIRECTIVE.md`](../DIRECTIVE.md)

> **Document role:** this is the capability boundary and open-gap ledger. It
> answers *what works now, what is only declared, and what is blocked*. The
> [`DIRECTIVE`](../DIRECTIVE.md) owns the objective, binding rules, work order
> and scoreboard; this file must not declare priority or “what comes next.” The
> [`PHYSICAL_COMPILER_ROADMAP`](../PHYSICAL_COMPILER_ROADMAP.md) is the
> completed workstream ledger and blocked-item register; it is historical, not
> an active roadmap. The
> [`TRANSFER_COMPILER_OBJECTIVE`](TRANSFER_COMPILER_OBJECTIVE.md) owns schemas,
> contracts and the historical phase record.

This is the current capability audit. It is deliberately narrower than the
project vision: it records what the code and fixed tests support now, what is
only declared, and what would close each remaining gap. It does not promote a
mechanism, proposal or example above its evidence level.

## 1. Current capability boundary

| Layer | Implemented now | Evidence / limit |
|---|---|---|
| Physical backend | £ parsing, ¢ DAG decomposition, declared ∆ enumeration and ranking, 39 wheels, nine exact route modes, three physical bindings, reference netlists and dynamic checks | Exact or declared structural results; no fabricated or measured device |
| Operation contracts | Ten contracts: `sqrt`, `sum`, `difference`, `quantized_carry`, `mult`, `div`, `exp`, `log`, `reciprocal`, `sign` | Each has semantics, a reference, a fixed test and a declared mechanism; `sign` uses the threshold comparator |
| Mechanism registry | Ten live cards: seven authored route cards plus three generated Δ cards. Delta-sigma, log-domain sqrt, KCL, cam, orifice, PLL and threshold comparator are live authored cards; fluid continuity, op-amp summing and log-domain arithmetic are generated; the eighth authored principle, `transcendental-identity`, is abstract and seeds arithmetic rather than appearing as a live card | **D2/D3/D7 implemented.** `fluid-continuity` uses `effort-flow-duality + composition`; `opamp-summing` uses `scale-offset + composition`; `log-domain-arithmetic` uses `composition` over `transcendental-identity` and supports `exp`, `log`, `mult`, `div`, `reciprocal`; `threshold-comparator` supports exact `sign` |
| Retrieval | Every card is scored; the top three structural candidates are returned for every operation | **D1/D3 implemented.** `supported_operations` no longer filters retrieval; a declaration adds a weak `+2` ranking signal, never a gate. Labels remain authored independently. Unlabelled candidates are hypotheses, not accepted support |
| Evaluation | `cent evaluate` runs ten provenance-labelled positives, six negative controls, no unadapted operations and three refused names | **D7 result: 15/16 candidate recall, 9/10 case recall, 2/6 negative-control failures, 14/14 target pairs, 14 artifacts and 15 triaged candidates.** `certified: false`; this is honest but not independent external truth |
| Reference target | Fourteen executable `glm-reference` pairs over 42 fixed vectors | `target-simulated`; no real GLM, measured-device or external budget |
| Live target | `glm-live` exact KCL sum and difference through the external CLI | `target-integrated` for those two operations only; no latency or bit-budget measurement |
| Proposal handoff | `cent propose` bundles, readiness, review ledger and executable handoffs | Current bundles below; a proposal remains unvalidated until target tests run |
| Hypothesis promotion (experimental) | `cent hypothesis --promote` admits a retained lead to a proposal only after a declared card, operation contract, structural overlap, target adapter/vectors, passing target certificate and digest-pinned promotion review | The gate creates a filtered proposal bundle; it does not add `supported_operations`, validate a physical device or authenticate reviewer identity |
| Workflow orchestration (experimental) | `cent workflow` chains a discovered method or compiled formula through hypotheses, proposals, fixed-vector trials, an exact pipeline and a declared machine wrapper; `--out` writes a manifest and every stage artifact | The workflow preserves each stage's evidence level; hypothesis leads stay pre-admission, unsupported stages remain explicit gaps, and no new physical or target evidence is created |
| Machine composer (experimental side-arm) | `cent machine` composes a complete staged function tree, selects compatible core parts from the transfer rankings and executes the declared branch; assembled routes can be wrapped with a declared `analog`, `mechanical` or `fluid` load | First machine `sigma-delta-sqrt`: 12/12 roles present, three compiler-selected parts, four executable checks, decimated error `4.573e-06`; analog, clock-jitter and supply stages remain explicit gaps. Route wrappers keep the route's typed graph and remain exact-core evidence. Not a D-item |
| Self-target | `cent-self` emits two adopted `cent-utility/1` records with independent-oracle certificates and exercised rollback | **D4 implemented.** One-tick floor contract beats the two-tick target `32/152` → `152/152`; runtime invariants beat static audit `4/12` → `12/12`; both deltas measured, not asserted |
| Refutation | `cent refute` generates Tier-D negatives with witness pairs and derived test obligations | **D5 implemented.** 8 generated negatives exceed 6 hand-declared controls; the Q-tensor retirement is reproduced; 10/10 obligations are derived, not authored |
| Retrodictive holdout | `cent holdout` freezes a pre-1940 mechanism library and retrieves dated post-cutoff targets | **D6 implemented, bounded.** 5/5 positive rank-one recall, zero positive-case misses, one declared false-positive candidate (`1/15` retrieved), one excluded candidate, and a strict RSA negative control reporting `no_licensed_source` and one coverage miss; the corpus is small and hand-declared |

### Usable now

- Exact rational arithmetic, certified interval sqrt/exp/log, exact route
  assembly and fixed-vector target validation.
- `cent transfer` for every operation contract, returning the top three
  structural hypotheses with explicit declared-support metadata.
- `cent discover` now adds an executable transfer handoff for `exp`, `log`,
  `mult`, `div` and `recip`: the `log-domain-arithmetic` route is run over each
  adapter's fixed source and target vectors and appears as a separate method
  beside the existing expansion/substrate candidates. The handoff command and
  vector count are in the discovery payload and terminal view. The operation
  matrix carries the four matrix-visible handoffs as `validated-transfer` rows,
  not as exact route graphs.
- `cent compile` now attaches that same handoff to a single arithmetic formula:
  `y = 1/x` resolves to the reciprocal adapter, while `y = exp(x)`, `y = log(x)`,
  `z = x*y` and `z = x/y` use their matching adapters. The JSON and terminal
  report carry the mechanism, target certificate, fixed-vector result and
  handoff command. Multi-primitive formulas get per-stage handoffs and typed
  stage-interface boundaries: producer/consumer kinds, domains and ports are
  checked for compatibility, while stage-to-stage execution remains unrun. The
  declared `mult -> div` chain `(a*b)/c`, `mult -> reciprocal` chain `1/(a*b)`
  and `div -> mult` chain `(a/b)*c` are certified end to end by composed
  `glm-reference` adapters over three fixed vectors each; their composition
  certificates include the boundary checks. Other compositions remain
  `validated: false` with no composition certificate, and unsupported stages
  remain explicit gaps.
- `cent propose --trial` and `cent trial DIR [ID]` add a computational
  side-loop: ready proposals run their declared adapters over fixed vectors and
  report a plain-language proposal summary, concrete inputs, expected/actual
  values, failed checks and an adjustment note. Non-ready proposals stay
  `not-run` with their readiness reason. `cent trial --wheel` enumerates every
  declared operation contract and trials each executable proposal, reporting
  testable operations and explicit missing-adapter gaps. Current wheel: 10
  declared operations, all 10 testable. The wheel is not
  an exhaustive search over all computational operations. A trial is
  target-simulated fixed-vector evidence; it does not change review state or
  validate the analogy.
- `cent machine` composes a complete staged machine from compiler-ranked
  parts. The first machine, `sigma-delta-sqrt`, is a one-bit ∆Σ √2 carrier with
  input conditioning, a first-order loop, digital decimation and a declared
  analog branch. It validates the digital branch, not the physical machine; the
  analog reconstruction, clock jitter and supply rejection remain gaps. The
  same side-arm wraps `delta-sigma`, `sqrt-log`, `sqrt-feedback`, `sum-kcl`,
  `sum-fluid` and `sum-opamp` without inventing a new route simulation, and
  `--load mechanical|fluid` selects a declared TIER 3 transducer branch. This is
  an experimental side-arm, not a D-work-order item and not a scoreboard
  improvement.
- `cent evaluate` for the provenance-labelled corpus, with an honest uncertified
  baseline and a permanent constant-score sabotage gate.
- `cent mechanism` now exposes ten live cards: seven authored route cards and
  three generated Δ cards, seeded by the abstract `transcendental-identity`
  principle; each generated card names its `principle_id` and executable operator
  chain, `tests/test_ablation.py` proves the KCL cards can be deleted and
  rebuilt, and `tests/test_log_domain.py` does the same for the arithmetic card.
- `cent-self` for the two adopted self-transfers, including portable
  `examples/self/utility.json`, independent oracle certificates and a rollback
  command for each record.
- `cent refute` for eight witness-backed generated negatives and ten derived
  test obligations, with a portable `examples/refutation/negatives.json`.
- `cent holdout` for the bounded D6 retrodictive corpus: five frozen pre-1940
  mechanisms, five dated post-cutoff targets, explicit false-positive
  constraints and the portable `examples/holdout/ledger.json`.
- `cent propose` for all ten operations with generated bundles. The review
  ledger accepts `adopted` / `reverted`.
- `target-simulated` reference adapters for fourteen pairs and
  `target-integrated` live KCL sum/difference.

### Declared but not target-validated

- `cam-profile` and `orifice-pressure-flow` for `sqrt`: structural mechanisms
  with no exact model, adapter or fixed target vectors. T1 records both as
  refusals until those laws and vectors exist.
- The physical KCL artifact: the normalized route and binding exist; component
  values, source/load and a reference netlist do not.
- The 22 `.cir` examples and physical routes: useful declared/reference
  artifacts, not measured devices.

### Machine-specific gaps

- `sigma-delta-sqrt` executes only its digital branch. The analog
  reconstruction filter, power buffer, clock-jitter model and supply-rejection
  model are declared but not simulated; `machine.cir` is the behavioral
  electrical core only.
- The executed loop is the first-order error-feedback baseline. The sketch's
  leaky second-order loop is recorded as an alternative gap, not claimed as
  executed.

### Not usable as a transfer claim

- `sign` now has a threshold-comparator mapping and a passing reference-target
  certificate, but no measured comparator, offset model or hysteresis model.
  `exp`, `log`, `mult`, `div` and `reciprocal` likewise have generated mappings
  and passing reference-target certificates, but no measured junction.
- PLL phase tracking has a source-simulated mechanism card but no production
  operation contract, so `cent transfer track_phase` refuses.
- Bresenham is no longer only a lead: the exact one-tick law is promoted to
  the declared `quantized_carry_floor` contract. It is not registered as a
  retrieval mechanism card, and the existing two-tick target is still a
  different timing.
- Q-tensor is retired; scalar invariants cannot select a director.
- D6 supplies a dated, provenance-labelled held-out corpus, but it is
  hand-declared and small; no external measured corpus, physical measurement,
  fabrication result or benchmark score is claimed.

## 2. Loose ends

These are the known open gaps. “Closed here” means this tidy-up added a concrete
artifact or statement, not that the underlying evidence exists.

| ID | Loose end | Status now | What would close it |
|---|---|---|---|
| L1 | One operation contract (`sign`) had no mechanism or target adapter | **Closed by D7:** threshold-comparator card and exact reference adapter pass negative, zero and positive vectors; `cent transfer sign --validate` passes | Keep the zero branch and the no-measured-comparator boundary explicit |
| L2 | Two supported candidates are unadapted (`cam-profile`, `orifice-pressure-flow`) | Closed for T1 by recorded refusal; they remain unadapted records, not capabilities | Declared model, fixed vectors and target adapter, or a stated refusal |
| L3 | Retrieval/evaluation was whitelist-circular and the labels came from card support | **D1/D3 implemented; uncertified. D6 adds a bounded dated holdout** | Current result is 15/16 recall, 9/10 cases and 2/6 negative-control failures; D6 is 5/5 positive rank-one with one declared false positive, one excluded candidate, and a strict RSA negative control reporting `no_licensed_source` and one coverage miss; its corpus is hand-declared and not external truth |
| L4 | Live target covers only exact KCL sum/difference | Closed for T3 by recorded refusal; reference-only for sqrt/carry | Additional live operation with reproducible vectors and declared budgets |
| L5 | Physical KCL artifact is missing | Blocked | Declared component values, source/load, compliance and error budget |
| L6 | PLL supports `track_phase`/`synthesize_frequency` but no operation contract exists | Open | Contract with semantics, reference, fixed test, then adapter |
| L7 | Cam and orifice are structural only | Open | Exact profile/restriction law and an adapter with vectors |
| L8 | Bresenham is a lead, not a card | **Closed by D4 as a declared contract, not a card:** `quantized_carry_floor` agrees with all 152 fixed walks; the old two-tick target agrees on 32 | Keep the timing distinction explicit; no retrieval-card claim |
| L9 | 22 legacy `.cir` examples and current transfer proposals were not separated | Closed here: current bundles are under `examples/transfer/`; the 22 `.cir` files remain pinned physical show-work | Keep both classes labelled |
| L10 | External math evidence (EXT-D5, EXT-D10b–e, Lean) and Rule30/ARC adapters are absent | Blocked | Declared structure, tensor/action data, build or benchmark adapter with scoring |
| L11 | Documentation counts are automated, but semantic claims are not | Mitigated here; counts/tree are checked by the gate | Review this ledger and the directive whenever evidence changes |
| L12 | Discovery has overbroad matches for “Griess product” and “matrix-vector product” | Known; generic multiplier methods are not accepted as those operations | Narrow the match or retain the refusal; do not count a text match as a proof |
| L13 | No measured-device or fabrication evidence | Blocked | Fabrication and measurement, not a netlist or simulation |
| L14 | W30/W31 have no declared domain content | Blocked | Reviewed wheels with axioms and tests; do not guess a table |

## 3. Updated examples and proposals

The current proposal bundles are in
[`../examples/transfer/`](../examples/transfer/). They were generated from the
current CLI on 2026-11-12:

| Operation | Proposals | `ready-for-execution` | `needs-target-adapter` |
|---|---:|---:|---:|
| `sqrt` | 3 | 1 (`log-domain-sqrt`) | 2 (`cam-profile`, `fluid-continuity`) |
| `sum` | 3 | 3 (`kcl-conservation`, `fluid-continuity`, `opamp-summing`) | 0 |
| `difference` | 3 | 3 (`kcl-conservation`, `fluid-continuity`, `opamp-summing`) | 0 |
| `quantized_carry` | 3 | 1 (`delta-sigma-error-feedback`) | 2 (`pll-phase-tracking`, `orifice-pressure-flow`) |
| `exp` | 3 | 1 (`log-domain-arithmetic`) | 2 (`log-domain-sqrt`, `fluid-continuity`) |
| `log` | 3 | 1 (`log-domain-arithmetic`) | 2 (`log-domain-sqrt`, `fluid-continuity`) |
| `mult` | 3 | 1 (`log-domain-arithmetic`) | 2 (`fluid-continuity`, `kcl-conservation`) |
| `div` | 3 | 1 (`log-domain-arithmetic`) | 2 (`fluid-continuity`, `kcl-conservation`) |
| `reciprocal` | 3 | 1 (`log-domain-arithmetic`) | 2 (`fluid-continuity`, `kcl-conservation`) |
| `sign` | 3 | 1 (`threshold-comparator`) | 2 (`fluid-continuity`, `kcl-conservation`) |
| **Total** | **30** | **14** | **16** |

These are D1's top-three structural proposals. Candidates without an executable
adapter are reviewable gaps, not validated transfers. `examples/transfer/evaluation.json`
is the current `cent evaluate --json` payload: `ok: true`, `certified: false`,
15/16 candidate recall, 9/10 cases and 15 triaged candidates; target pass rate is 14/14.

These proposals are different from the 22 `examples/proposal_*.cir` files:

- the `.cir` files are physical-backend show-work examples, pinned by
  `tests/test_proposals.py`;
- the `examples/transfer/` bundles are transfer handoffs with mechanism,
  mapping, readiness, review state, target vectors and handoff commands;
- neither class is a validation result without its declared target tests.

### Can any proposed method be executed against a target?

These are target-execution results, not benefit claims. No utility delta against
a named non-analogical baseline has been measured (directive R4), so none of
these rows may be presented as a useful transfer yet.

| Method | Current evidence | Can it be executed now? | Utility / limitation |
|---|---|---|---|
| Delta-sigma error feedback → `quantized_carry` | `source-simulated`; `target-simulated` reference certificate | **Yes**, reference target | Exact carry/mean test, bounded-state and baseline checks; no live GLM or measured hardware |
| Log-domain sqrt → `sqrt` | `source-simulated`; `target-simulated` reference certificate | **Yes**, reference target | Certified rational enclosure with independent `sqrt_q`; no measured junction |
| KCL conservation → `sum` / `difference` | `source-simulated`; `target-simulated` reference; live exact KCL | **Yes**, reference and live KCL | Exact normalized arithmetic; no physical units or measured junction |
| Fluid continuity → `sum` / `difference` | `source-simulated`; `target-simulated` reference certificates | **Yes**, reference target | Exact normalized-flow parity, commutativity and reversed-port difference; no pressure/flow scaling or measured junction |
| Op-amp summing → `sum` / `difference` | `source-simulated`; `target-simulated` reference certificates | **Yes**, reference target | Ideal matched-resistor summing block and inverting-buffer difference; no device values or measured amplifier |
| Cam profile → `sqrt` | `structural` | **No target use** | Design lead; no exact cam solver or adapter |
| Orifice pressure/flow → `sqrt` | `structural` | **No target use** | Design lead; no calibrated law or adapter |
| PLL → phase/frequency | `source-simulated` card | **No transfer use** | No production operation contract; numerical, not exact |
| Bresenham one-tick carry | Hypothesis evidence only | **No** | Narrow lead; not a card and not equivalent to the two-tick target |
| Orientation envelope | Exact finite-direction algorithm | **Yes, separately** | Useful exact geometry method via `cent envelope`; not a mechanism transfer |
| Q-tensor | Retired by invariant proof | **No** | Scalar invariants are orientation-blind |

The only methods that currently execute against a reference target are the
fourteen reference-backed pairs above. Execution is not benefit: no utility
delta has been measured. The structural methods are design leads only; the fluid route is an
independent normalized-flow reference check, not a measured physical transfer.

## 4. Disposition of earlier track items

Work order is owned by [`DIRECTIVE.md`](../DIRECTIVE.md). This table records
where the earlier T0–T6 items landed; it is not a priority order and does not
set the next task.

| Earlier item | Disposition now | Evidence / limit |
|---|---|---|
| **T0 — documentation and examples** | Complete, then superseded by directive adoption | The three documents are ledgers; counts, examples and links are synchronized |
| **T1 — close unadapted candidates** | Closed by recorded refusal for `cam-profile` and `orifice-pressure-flow` | No model, vectors or adapter was invented; the fluid and op-amp additions were separate promotions |
| **T2 — external/held-out evaluation** | Superseded by D1 then D6 | G5b is not external truth; D1 replaced it with an uncertified honest baseline, and D6 supplies the dated holdout |
| **T3 — current-interface live boundary** | Closed by recorded refusal | Live coverage remains KCL sum/difference; no latency or bit-budget claim |
| **T4 — physical KCL artifact** | Blocked | Needs declared component values, source/load, compliance and error budget |
| **T5 — operation/mechanism expansion** | Folded into D2 and D3 | No card is added to fill a row; regenerate Μ/∆ or record the missing operator |
| **T6 — blocked external layers** | Blocked | EXT-D5, EXT-D10b–e, W30/W31 and Rule30/ARC still need their declared data, build or adapter |

### Evidence limits carried into the directive

- A reference adapter is not a live integration.
- A structural card is not target-validated.
- A whitelisted candidate is not structural retrieval.
- G5b declared support is not external ground truth.
- 10/10 is a historical artifact of the old evaluation, not a capability result.
- No calibration, component value, latency or bit budget is invented.

## 5. Review history

### 2026-11-13 — D10 implemented

- New wheel W42 (Elastic Buckling and Bistable Snap-Through) declares the
  three-level law the sign family was missing; `sign_of(a - b)` is now a
  parsed dimensionless projection at the wheels layer.
- The sign family is licensed by computed acceptance (one pairing
  originated, oracle-passed); the speculative ring drains and a
  certification queue names reachable paths for the still-blocked
  candidates. W13/W14 still refuse — the license is per-wheel.
- W37 rheology — discovered by the D9 dimensional scan — is promoted to a
  production pairing: 13 cards, both sum and difference certify
  `target-simulated`, and the scoreboard denominator grows to 10.
- Metric 1 reports 18/10 (D4 1 + D8 3 + D9 13 + D10 1). The origination
  gate is 56 checks (D8 17 + D9 24 + D10 15).

### 2026-11-13 — D9 implemented

### 2026-11-13 — D9 implemented (earlier)

- Added `cent_compiler/origination_scale.py` and `cent originate --search
  scale`: a declared-data search over the wheel corpus whose family
  acceptance is computed from 8-axis dimension vectors, not curated lists.
- Fourteen new pairings originated across three families (8 junction, 3
  noise-shaping, 5 sqrt-inversion), every one oracle-passed; W37 rheology
  was discovered by dimensional scan — no TIER-3 analogy had declared it.
- Two noise-shapers (W4 flywheel, W5 escapement) were promoted into the
  production registry with executable adapters and target-simulated
  certificates; the registry now has 12 cards, 5 of them generated.
- The sign family is refused at zero: no wheel declares a three-level law.
  Its physical candidates are speculative proposals with named unblocks,
  never counted.
- Metric 1 reports `4/9 -> 18/9` (search-originated total 18 vs corpus 9);
  the production denominator stays 9 under the D6 reported-separately
  precedent. The gate adds 24 D9 checks (41 with D8).

### 2026-11-13 — D8 implemented (earlier today)

### 2026-11-13 — D8 implemented

- Added `cent_compiler/origination.py` and `cent originate`: a search over the
  7 declared TIER-3 analogies that composes each with the `kcl-conservation`
  principle through the executable `effort-flow-duality` + `composition`
  operator chain.
- Three junction-continuity interpretations originate (acoustic via Paynter
  W1-W7, rotational via rotational-linear W4-W5, electromechanical via
  piezo/Lorentz W1-W5); each generates a valid card and passes an independent
  exact oracle on 8 fixed vectors. The capacitor-inductor, thermoelectric and
  optoelectronic analogies are refused with recorded reasons (no
  power-conjugate junction flow).
- The search re-derives the hand-authored `fluid-continuity` record from the
  W1-W6 analogy (derivation parity), and a sabotage check shows an
  always-accept predicate would accept 7/7 while the real predicate refuses 3.
- Scoreboard metric 1 (origination rate) moves from `1/9` to `4/9`; the `≥3`
  target is met without inventing any non-declared analogy. The gate adds
  `tests/test_origination.py` (17 checks).
- Also repaired in passing: `test_question_corpus.py` now tolerates argparse's
  Python-3.12 unquoted choice list, and the sibling `glm-study` CLI's
  `evidence.py` shipped with 21 unresolved merge-conflict markers (resolved to
  the upstream side; the CLI answers exact queries again).
- The originated interpretations remain normalized-flow software only; no
  measured junction, device binding or netlist. Origination currently covers
  junction-conservation pairings only; other principles (noise shaping,
  transcendental identity) are not yet searched.

### 2026-11-12 — D7 implemented

- Added the `threshold-comparator` mechanism card with an exact three-level
  law, bounds and explicit offset/hysteresis/metastability gaps.
- Added `exact_sign_reference` and three fixed vectors (negative, zero,
  positive) to the `glm-reference` target; `cent transfer sign --validate`
  emits a passing `target-simulated` certificate.
- Extended the evaluation corpus to ten positives and zero unadapted
  operations; added sign to the proposal wheel and regenerated its bundle.
- The operation wheel now reports 10/10 testable operations. D7 is hand-authored,
  so it does not improve the scoreboard's origination-rate metric.

### 2026-11-12 — D6 implemented (bounded)

- Added `cent_compiler/holdout.py` and `cent holdout`. Five mechanisms are
  frozen before 1940: metallurgical annealing, Pearson random walk (1905),
  Ising spins (1925), Boltzmann kinetic theory (1872) and Plateau soap films
  (1873).
- Five dated post-cutoff targets retrieve the expected source at rank one:
  simulated annealing (1983), resistor networks (1984), Hopfield associative
  memory (1982), lattice Boltzmann (1988) and Steiner-tree computation (1941). The
  measured positive report is 5/5 recall, zero positive-case misses, one declared
  false-positive candidate and one excluded candidate. A strict RSA negative
  control reports `no_licensed_source` and a coverage miss.
- Excluded Bresenham ↔ delta-sigma because Bresenham (1965) postdates the 1940
  cutoff and the D4 correspondence is internal evidence.
- Added `examples/holdout/ledger.json`, `examples/holdout/README.md` and
  `tests/test_holdout.py` (27 checks). The gate at D6 was 23 suites and 938
  checks.

### 2026-11-12 — D5 implemented

- Added `cent_compiler/refutation.py` and the `cent refute` command. Thirteen
  declared instances produce 8 generated negatives against 6 hand-declared
  controls; every negative has a shared signature and a named observable
  separation.
- Reproduced the Q-tensor retirement from identical scalar invariants and
  different envelope areas (`2/1` versus `66/25`), and preserved the D4
  two-tick/one-tick carry witness.
- Derived ten test obligations with `authored: false`: two from the
  `quantized_carry` contract outputs and one per witness.
- Added `review/refuter_demo.py` and `examples/refutation/negatives.json`;
  `tests/test_refutation.py` is 19 checks. The full gate is now 22 suites and
  911 checks.

### 2026-11-12 — D4 implemented

- Added `cent-self` / `cent self`, `cent-utility/1` records, a portable ledger
  (`examples/self/utility.json`) and `adopted`/`reverted` review states.
- Promoted the Bresenham one-tick proof to the declared
  `quantized_carry_floor` contract: `152/152` integer walks agree, against
  `32/152` for the existing two-tick target (`delta +120/152`).
- Added exact runtime junction invariants for `cent-program/1`: `12/12`
  injected faults detected, against `4/12` for static `topology_audit`
  (`delta +8/12`).
- Added `self_oracle.py`; both certificates are oracle-issued with
  `candidate_on_certificate_path: false` (R5). Both records are adopted and
  their rollbacks restore the named baselines.
- Added `tests/test_self_target.py` (21 checks). The gate at that point was 21
  suites and 892 checks; D5 later raised it to 22 suites and 911 checks.

### 2026-11-12 — D3 implemented

- Added a `transcendental-identity` principle and generated
  `log-domain-arithmetic` from `composition`; the sqrt card remains
  sqrt-specific, so the cam negative controls still refuse the wrong Δ.
- Added source routes and independent target adapters for `exp`, `log`, `mult`,
  `div` and `reciprocal`, with fifteen fixed vectors and operation-local budgets.
- Added `tests/test_log_domain.py` (25 checks), D3 positive cases and corrected
  negative-control rationales; removed the five operations from the unadapted
  corpus. Declared support contributes a weak `+2` retrieval signal so the
  generated card can rank, but it remains a signal, not a candidate filter.
- Regenerated all nine proposal bundles (27 proposals: 13 ready, 14 needing a
  target adapter) and `examples/transfer/evaluation.json`.
- Current evaluation: 14/15 candidate recall, 8/9 case recall, 2/6
  negative-control failures, 13/13 target pairs, 13 artifacts, 13 triaged.
- The gate at the D3 review point was 20 suites and 871 checks; D4 later raised it to 21 suites and 892 checks.

### 2026-11-12 — D2 implemented

- Split the registry into six hand-authored principle cards and two generated
  Δ interpretations. `fluid-continuity` and `opamp-summing` are derived from
  `kcl-conservation` by executable operator chains.
- Added `check`/`apply` to all seven mapping operators; an unmet precondition is
  refused, and the operator payload now marks each operator executable.
- Added `tests/test_ablation.py`: it deletes both generated cards, rebuilds them,
  swaps the rebuilt registry into retrieval/validation, and gets identical
  certificates for fluid and op-amp sum/difference (11/11).
- Regenerated all twelve proposal bundles and `examples/transfer/evaluation.json`;
  proposals carry `principle_id` and the operator chain.
- The full gate is now 19 suites and 846 checks.

### 2026-11-12 — D1 implemented

- Removed the `supported_operations` retrieval filter; every card is scored and
  the top three structural candidates are returned.
- Rebuilt labels from written provenance and stopped treating unlabelled
  candidates as false positives; they enter an explicit triage queue.
- Added the constant-score sabotage suite. Recall drops from 8/10 to 4/10,
  case recall from 3/4 to 1/4, target candidates from 8/8 to 3/8 and
  negative-control failures rise from 2/6 to 4/6.
- Published the honest D1 baseline: 8/10 candidate recall, 3/4 cases, 2/6
  negative-control failures, 13 triaged candidates and `certified: false`.
- The full gate is now 19 suites and 846 checks.

### 2026-11-12 — directive adoption

- Adopted [`DIRECTIVE.md`](../DIRECTIVE.md) as the sole owner of objective,
  binding rules, work order and scoreboard.
- Withdrew the G5b 10/10 result as capability evidence: the retrieval filter and
  the expected labels both read `supported_operations`, making the metric
  sabotage-invariant. D1 repaired it.
- Replaced the old T1–T6 priority table with a disposition ledger; the earlier
  items no longer declare what comes next.
- Recorded D1 as the immediate unblocked task and D3 as in scope per the owner's
  test-and-follow-results direction.

### 2026-11-12 — documentation reconciliation

- Assigned the three documents ledger jobs: capability boundary here,
  workstream history in the completed ledger, objective/schema/history in the transfer
  document. Priority and sequencing later moved to the directive.
- Updated the capability tables to eight mechanism cards, 32 matrix rows,
  nine exact route modes, eight reference adapters over 24 fixed vectors, and
  the 10/10 evaluation result. The 10/10 row is retained only as a historical
  record and is withdrawn as capability evidence.
- Recorded the op-amp sum/difference promotion and the separate computational
  addition laboratory.
- Clarified that T1 is closed by refusal for cam/orifice and T3 is closed for
  the current live interface. “Closed” means the refusal condition is recorded;
  it does not mean the missing evidence now exists.
- Removed the implication that the whole roadmap was complete through G5b while
  G4b and T2 were still being described as open in different places.

### 2026-11-11 — previous tidy-up

- Added the first capability, loose-end and planning record.
- Generated transfer proposal bundles and the evaluation payload under
  `examples/transfer/`.
- Separated the 22 legacy physical `.cir` examples from current transfer
  proposals.
- Added T1 refusal records for cam and orifice to `cent evaluate`.
- Added the T3 live-breadth probe and refusal record under `docs/evidence/`.
- Linked this audit from the documentation index, README and roadmap.
