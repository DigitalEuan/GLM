# Physical Compiler — Completed Workstream Ledger

**Status:** completed local ledger; historical workstream and blocked-item register  
**Not an active roadmap.** The locally actionable scope was completed through D1–D7; the remaining rows are externally blocked or unbudgeted. New work must enter as a D8 in [`DIRECTIVE.md`](DIRECTIVE.md).  
**Last reviewed:** 2026-11-13  
**Canonical gate:** `python3 tests/run_all.py`; the README statistics row owns the live count  
**Work-order authority:** [`DIRECTIVE.md`](DIRECTIVE.md)

> **Document role:** this is the completed workstream ledger and blocked-item
> register. It records what was built, what failed, and what remains blocked;
> it is retained for traceability and is not an active roadmap. The
> [`DIRECTIVE`](DIRECTIVE.md) owns the objective, binding rules, work order and
> scoreboard; this file must not declare priority or “what comes next.” The
> [`CURRENT_SCOPE`](docs/CURRENT_SCOPE.md) owns the
> current capability boundary and gap ledger; the
> [`TRANSFER_COMPILER_OBJECTIVE`](docs/TRANSFER_COMPILER_OBJECTIVE.md) owns
> schemas, contracts and the historical phase record.

**Primary objective:** cross-domain computational method transfer, defined by
[`DIRECTIVE.md`](DIRECTIVE.md): originate → bound → benefit. The physical
backend is one downstream target, not the definition of the compiler.

This ledger does not promote a candidate by changing a label. The executive
stocktake and “Completed since” are history, not a second status page. The file
is retained for traceability because the blocked items and the evidence behind
them remain useful; it is not a queue and does not name a next task.

**Evidence tiers, from weakest to strongest:** computational laboratory
(declared math only) → production exact route (source-simulated) →
`glm-reference` adapter (`target-simulated`) → live `glm-live`
(`target-integrated`) → physical binding/measurement. A method can appear in
more than one tier only when the higher-tier artifact actually exists.

## 1. Executive stocktake

| Area | State | Current evidence | Boundary / unblock (not a queue) |
|---|---|---|---|
| Operation coverage | Complete for declared operations | 12 matrix operations; 36 rows | More operation contracts only with semantics and tests |
| Alternative catalogue | Complete | 9 exact routes, 4 validated transfers, 1 exact algorithm, 7 structural templates, 1 bridge, 1 analogy, 12 inherited candidates, 1 gap | Keep weak evidence separate |
| Exact routes | Complete for current scope | KCL sum/difference, fluid sum/difference, op-amp sum/difference, log-domain sqrt, op-amp sqrt, delta-sigma carry | More routes are not automatically better; add with evidence |
| Exact algorithm | Complete for current scope | `bounding_box` / `orientation-envelope` with exact finite-direction probe | No global-orientation or physical claim |
| Micro-pipelines | Complete for four operations | `sqrt`, `sum`, `difference`, `quantized_carry`; stage and handoff data from route programs; `difference` has KCL, fluid and op-amp mechanisms | Execution/composition of arbitrary sub-operations remains open |
| Pre-admission hypotheses | Complete; Q retired, Bresenham retained narrowly | `cent hypothesis`; 2 leads with `DOESNT-KNOW` provenance; Q proof and Bresenham one-tick evidence recorded | Reopening Q or widening Bresenham requires new evidence, not silent reactivation |
| Transfer contracts | Implemented; D1 evaluation and D2/D3/D7 generation complete | 10 operation contracts; 10 live cards (7 authored route cards including the threshold comparator, plus 3 generated Δ cards) and an abstract transcendental principle; executable mapping operators; behavior signatures; `cent-relaxation/1` default `unclassified`; two supported candidates (`cam-profile`, `orifice-pressure-flow`) still have no adapter, and `sign` is covered by the threshold comparator | Broader mechanism coverage and live coverage remain separate |
| Target validation | Complete for ten reference operations (fourteen mechanism pairs) | 14 `glm-reference` adapters over 42 fixed vectors; live `glm-live` KCL sum/difference | Broader live coverage only after a new interface |
| Proposal handoff | Complete | `cent propose` bundles, index, review ledger, readiness states; current bundles in `examples/transfer/` | Review-to-validation remains manual; no proposal is auto-validated |
| Self-target utility | Complete under D4 | `cent-self`; two adopted `cent-utility/1` records; independent-oracle certificates; exercised rollback | More subsystems need a measured baseline before they can enter the ledger |
| Refutation | Complete under D5 | `cent refute`; 8 witness-backed generated negatives against 6 hand-declared controls; 10 derived obligations | Richer witnesses and more declared instance families |
| Retrodictive holdout | Complete under D6, bounded | `cent holdout`; five pre-1940 mechanisms, five dated post-cutoff targets, 5/5 positive rank-one recall, one declared false-positive candidate, one excluded candidate, and a strict RSA control reporting `no_licensed_source` and one coverage miss | Larger independent corpus; current corpus is hand-declared |
| Physical KCL artifact | Blocked | normalized KCL route and binding exist | Requires declared values, source/load model, error budget and reference netlist |
| External evidence | Partly blocked | EXT-D10a class-index audit complete | EXT-D5 and EXT-D10b–EXT-D10e remain blocked |
| Domain coverage | Complete for current declared wheels | 39 wheels; W30/W31 reserved | W30/W31 need a declared domain, not a guessed table |
| Documentation | Ledgers synchronized | Gate count, tree, module and test counts synchronized; objective and order live in `DIRECTIVE.md` | Keep the ledgers subordinate to the directive |

### Current command baseline

```bash
python3 tests/run_all.py                  # canonical gate
python3 cent self --json                  # D4 adopted self-transfer utility ledger
python3 cent refute --json                # D5 Tier-D negatives with witness pairs
python3 cent holdout --json               # D6 frozen retrodictive holdout
python3 cent-self --revert junction-runtime-invariants --json  # exercised rollback
python3 cent evaluate --json              # honest D1 baseline; uncertified
python3 cent propose sqrt --target glm-reference --json  # 3 proposals
python3 cent matrix --json                # 36 rows, 12 operations
python3 cent pipeline quantized_carry     # six stages, one feedback edge
python3 cent machine list                  # hand-authored machine + six route wrappers
python3 cent hypothesis                    # two pre-admission leads
python3 cent explore addition --declarations examples/addition_declarations.json --glm --json
python3 cent transfer sqrt --json          # 3 candidates
python3 cent transfer sum --json           # 3 candidates
python3 cent transfer difference --json    # 3 candidates
python3 cent transfer quantized_carry --json  # top 3 structural candidates
```

### Completed since the previous roadmap review

- [x] D2: generated `fluid-continuity` and `opamp-summing` from
  `kcl-conservation` with executable operators; ablation rebuilds both cards and
  reproduces four certificates exactly.
- [x] D3: generated `log-domain-arithmetic` from `transcendental-identity`;
  `exp`, `log`, `mult`, `div` and `reciprocal` pass source, target and tolerance
  certificates.
- [x] D4: promoted the Bresenham one-tick proof to `quantized_carry_floor`
  (`32/152` → `152/152` walk agreement) and added runtime junction invariants
  (`4/12` → `12/12` injected-fault detection), each with an independent-oracle
  `cent-utility/1` certificate and an exercised rollback. `cent-self` writes
  `examples/self/utility.json`; the review ledger accepts `adopted`/`reverted`.
- [x] D5: added the Tier-D witness search. Eight generated negatives exceed the
  six hand-declared controls; the Q-tensor retirement is reproduced, and ten
  test obligations are derived from contracts and witnesses. `cent refute`
  writes `examples/refutation/negatives.json`; `review/refuter_demo.py` runs the
  same search.
- [x] D6: froze five pre-1940 mechanisms and measured five dated post-cutoff
  targets. The holdout retrieves the expected source at rank one in 5/5 cases,
  records one declared false-positive candidate and excludes Bresenham ↔
  delta-sigma because the source postdates the cutoff. `cent holdout` writes
  `examples/holdout/ledger.json`.
- [x] D7: added the `threshold-comparator` card and exact three-level
  `sign` reference adapter. The operation wheel is 10/10 testable, with no
  measured comparator, offset, hysteresis or metastability claim.
- [x] Added `cent envelope` and the `bounding_box` exact-algorithm row.
- [x] Made the envelope discoverable and matrix-visible without calling it a
  physical route.
- [x] Added `cent pipeline` for route-derived micro-pipelines and feedback
  handoffs.
- [x] Added `cent hypothesis` with `CentWheel`/`KnowledgeState`, pre-admission
  scoring and explicit leads.
- [x] Added `resolve_lead` and `cent hypothesis --resolve`: one question per
  declared need, retry with supplied answers, then recorded keep/retire.
- [x] Kept `supported_operations` as the hard admission gate; no lead changed it.
- [x] Synchronized the gate, matrix, README, module tree and docs.
- [x] Added the computational addition laboratory, its declaration profile and
  eight explicit port contracts, with a GLM-facing `cent-computational-evidence/1`
  envelope that is separate from physical-transfer evidence.
- [x] Promoted the first lab method into the production exact-route path: the
  fluid reversed-port difference route, its `fluid-continuity` mechanism card
  support and its independent `exact_fluid_difference` target adapter.
- [x] Promoted the second lab method: the ideal op-amp summing/difference route,
  its `opamp-summing` mechanism card and independent `exact_opamp_sum` /
  `exact_opamp_difference` target adapters. The route adds both operations to
  the matrix, pipeline and transfer layers without claiming device values.
- [x] Recorded the declaration fields as **forcing conditions** in the
  computational tier: junction/constraint, gauge/reference, drive/gain-offset,
  boundary/range and perturbation/nonideality. They make the model well-posed;
  they are not physical-force or measured-parameter claims.

## 2. Workstream status

### A — Operation coverage

**Complete for the declared scope.**

- Binary `+` and `-` decompose into `sum`/`neg`, with exact programs and the KCL
  template.
- The operation fixture matrix records the first gap for `mult`, `div`, `exp`,
  `log`, `sqrt` and `tanh`.
- `tanh` remains an explicit missing-parameter gap; no limiting values were
  invented.
- Ordered-goal composition is parsed and kept separate; no invented step-to-step
  handoff is claimed.

**Why this is complete:** the compiler can express the requested operations
without pretending that a parser branch, template or ordered goal is an
assembled route.

### B — Alternative method catalogue

**Complete for the declared evidence.**

- `cent matrix` keeps exact routes, exact algorithms, structural templates,
  declared bridges, analogies, inherited candidates and gaps separate.
- Every row carries role, domain, carrier, route and first gap.
- `cent discover` resolves reviewed operation-level queries.
- `cent hypothesis` now exposes structural leads *before* admission without
  changing the matrix or `supported_operations`.

**Why this is complete:** users can distinguish “declared method,” “structural
lead,” “template” and “gap” without a keyword match being promoted to a method.

### C — Route coverage

**Complete for the current declared routes; one physical artifact remains
blocked.**

- KCL sum and difference are exact assembled routes.
- The normalized KCL binding preserves both inputs and audits the exact total.
- `sum-fluid` is the second independent non-`sqrt` route.
- `sum-fluid` now has both exact sum and reversed-port difference modes.
- The production route has a declared reversed-port component contract, a
  `fluid-continuity` mechanism card that supports both sum and difference, and
  an independent `exact_fluid_difference` target adapter over three fixed
  normalized-flow vectors.

**Second promotion — op-amp route.** `sum-opamp` is an ideal normalized-voltage
non-inverting summing amplifier with a matched input network (1/2 attenuation
per input) and closed-loop gain 2. Difference adds an ideal inverting buffer on
the second input; both then use the same exact `sum` block. The `opamp-summing`
card declares both operations, and `exact_opamp_sum` / `exact_opamp_difference`
are independent target adapters over three fixed vectors each. The route has no
device values, reference netlist or measured amplifier evidence.

**Computational tier — separate from production promotion.** The six-method
addition laboratory (`opamp-summing`, `kvl-series`, `switched-capacitor`,
`current-mode`, `mechanical-force`, `fluid-reversed`) runs 12 sum/difference
routes over 36 fixed rational vectors. It is exposed as
`cent explore addition --declarations examples/addition_declarations.json --glm`,
which emits `cent-computational-evidence/1` with `physical_transfer: false`,
`glm_call: false` and `model_score: false`. The canonical gate checks the
profile and the envelope. Eight explicit port contracts cover the six lab
methods plus the production KCL and rotational rows, and the coverage report
is complete with no missing lab method. The declaration fields are treated as
**forcing conditions**: junction type is the constraint, effort/flow are the
conjugate variables, sign/reference is the gauge, gain/offset is the drive,
range/resolution and source/load are the boundary, and nonidealities are
perturbations. They make the computational model well-posed; they are not
measured physical forces.

A physical KCL artifact path is still missing: no declared voltage/current
  mapping, source/load model, compliance range, error budget or reference
  netlist.

**Why the remaining item is blocked:** producing a physical KCL artifact without
declared component values and source/load assumptions would invent the very
evidence the artifact is supposed to carry. The unblock condition is a declared
KCL design point; no priority is assigned here.

### D — Evidence and repository

**Complete.**

- README, docs, package tree, module count and test counts are checked by the
  canonical gate.
- Parser/guide mismatches are recorded and regression-covered.
- Unsupported operations and missing links remain explicit gaps.

**Why this is complete:** the repository can be audited without trusting prose;
the gate and consistency preflight fail on drift.

### E — External evidence and blocked layers

**EXT-D5 and EXT-D10b–EXT-D10e remain blocked; EXT-D10a is complete.**

- **EXT-D5 fabricated-device evidence:** requires a real fabricated device.
- **EXT-D10a class-index audit:** complete. `cent leech-class` re-derives 63,257
  class words and 5,000/5,000 sampled XOR compositions from a declared row-HNF
  basis and corpus.
- **EXT-D10b lattice metric/q-form:** blocked on declared metric data.
- **EXT-D10c Griess product:** blocked on a declared multiplication tensor and exact
  product check.
- **EXT-D10d Monster action:** blocked on a representation, generators and action
  table.
- **EXT-D10e Lean/Viazovska:** blocked on a Lean build/elaborator and a declared
  codebook objective.

**Why these stay blocked:** a group isomorphism does not supply a metric,
quadratic form, Griess product, Monster action or Lean proof. Converting a label
or sampled XOR result into any of those would be a false claim.

### F — Domain and cross-system coverage

**Current declared scope is complete; external adapters are not.**

- 39 wheels are built; W26/W27 have sourced astrophysics/cosmology content.
- W30/W31 remain reserved with no declared domain content.
- 22/22 legacy physical proposal generation and 22 pinned `.cir` files pass; current transfer proposals are separate under `examples/transfer/`.
- The fixed GLM/cent corpus and the direct-question audit pass at their declared
  scope.
- Rule30 and ARC-AGI have no declared adapter, input data or scoring rule.

**Why W30/W31 are not filled:** an empty wheel is more honest than an invented
domain. **Why Rule30/ARC are not added:** a benchmark name is not an adapter, and
no score may be claimed without reproducible input and scoring.

### G — Transfer compiler

**G1–G4.5 are complete for their declared scope; G5 is implemented by D1 but is
not certified; G4b/T3 is closed for the current interface.**

- **G1 — contracts:** complete.
- **G2 — mechanism cards:** complete; ten live cards with provenance and gaps.
- **G3 — transfer v0:** D1 now scores every card and returns the top three
  structural candidates. `supported_operations` is validation metadata only;
  unlabelled candidates are hypotheses in triage.
- **G4 — GLM reference and live adapter:** complete for the declared adapter
  scope. Ten reference operations run over forty-two fixed vectors across
  fourteen mechanism pairs; live `glm-live` covers exact KCL sum/difference and
  is `target-integrated`. This says the adapters execute, not that retrieval
  originated the pairing.
- **G4.5 — proposal handoff:** complete; reviewable bundles, readiness,
  executable handoff and append-only review ledger.
- **G4b/T3 — current-interface live boundary: closed by recorded refusal.**
  Only KCL sum/difference are live. The T3 breadth probe records why `sqrt`,
  `exp` and mechanism-less `mult`/`div` do not add an honest live transfer on
  this interface. Reopen only with a new reproducible interface and a declared
  mechanism; no external latency, bit-budget, model or performance claim exists.
- **G5 — evaluation:** D1/D3/D7 implemented, **uncertified**. The provenance-labelled
  top-three result is 15/16 candidate recall, 9/10 case recall, 2/6
  negative-control failures, 14/14 target pairs and 15 triaged candidates. The
  constant-score sabotage drops recall to 4/16 and target candidates to 3/14;
  the 10/10 declared-support figure is withdrawn. D6 now supplies a bounded
  dated holdout: 5/5 positive rank-one recall, one declared false-positive candidate,
  one excluded candidate, and a strict RSA negative control reporting
  `no_licensed_source` and one coverage miss; it does not make the D1 baseline certified.

**Why G4 is complete despite G4b:** the original G4 acceptance was reference
artifacts plus a live KCL target. That threshold was met; the current scope now
has thirteen reference pairs. The additional op-amp and fluid routes are separate
promotions under the same rule, not a redefinition of G4. G4b is closed for this
interface by refusal, not by claiming broader live coverage.

### H — Pre-admission hypotheses

**Core complete; Q retired, Bresenham retained narrowly; promotion workflow open.**

- `cent hypothesis` uses the existing `CentWheel` and `KnowledgeState`.
- Unsupported cards are scored only when they clear a declared threshold and
  have a real primitive-chain overlap.
- Two review leads retain `DOESNT-KNOW` pre-admission provenance:
  - `nematic-q-tensor-bounding-box` (`bounding_box`), retired by the invariant
    obstruction;
  - `bresenham-quantized-carry` (`quantized_carry`), retained only as the
    one-tick floor error-feedback variant.
- Each lead has explicit proof, test and definition needs.
- `resolve_lead` asks only the missing needs, retries after supplied answers and
  records a keep/retire decision. Retirement requires a note; keep remains
  `DOESNT-KNOW` and does not promote.
- Q-tensor evidence proves `tr(Q^2)=2S^2` and `det(Q)=-S^2` are orientation-blind.
  Bresenham evidence proves the one-tick equivalence and shows the existing
  two-tick target is a different timing.
- Records are in `docs/hypothesis-resolutions/`; initial absence-based records
  are preserved under `history/`.
- No lead changes `supported_operations`, creates a transfer candidate or adds a
  matrix row.

**Why this layer exists:** without it, a structural lead is either invisible or
prematurely promoted. With it, the compiler can show the lead and run an explicit
resolution loop while preserving the admission gate.

## 3. Workstream history (completed)

This ledger records how the current scope was reached. It does not set order;
the only work order is in [`DIRECTIVE.md`](DIRECTIVE.md).

- **H1 — hypothesis resolution:** Q-tensor retired by an invariant proof;
  Bresenham retained narrowly as a one-tick hypothesis, not a card. The
  resolution loop records keep/retire and never changes `supported_operations`.
- **R1 — relaxation classification:** candidates carry `cent-relaxation/1`;
  non-`unclassified` classes require target evidence, an artifact and tests.
- **G5a — ten-operation intake:** ten contracts have semantics, a reference and
  a fixed test. At this milestone `sign` had no production mechanism or target
  adapter; D3 recovered the other five and D7 later closed `sign` with the
  threshold comparator.
- **G5b — evaluation:** the original corpus and metrics were implemented, but
  the certification was withdrawn. D1 replaced the whitelist with top-three
  structural ranking, moved labels to written provenance, added triage and a
  permanent sabotage suite. The current honest result is 15/16 recall and
  uncertified.

## 4. Blocked items and what would unblock them

| Item | Blocked on | Unblock condition | What must not happen |
|---|---|---|---|
| C1 physical KCL artifact | Declared component values, source/load, compliance and error budget | A reviewed KCL design point with physical assumptions | Values copied from another route or invented |
| EXT-D5 fabricated device | Real fabrication and measurement | Fabricated device and measured evidence | A netlist or simulation called fabricated |
| EXT-D10b metric/q-form | Declared metric data | Exact metric and q-form with checks | Transplanting a 24-bit group coordinate |
| EXT-D10c Griess product | Declared multiplication tensor | Exact product check | Treating XOR as Griess multiplication |
| EXT-D10d Monster action | Representation, generators, action table | Action check | Inferring an action from class words |
| EXT-D10e Lean/Viazovska | Lean build/elaborator and codebook objective | Reproducible build/check | A theorem label without a build |
| G4b live breadth | Closed for the current interface by T3 refusal; only a new interface reopens it | Reproducible live vectors and declared budgets | Calling a reference adapter live |
| G6 external corpus | Independent held-out data and labels | A declared external corpus with provenance and negative controls | Treating declared card support as external truth |
| F1 Rule30/ARC | Adapter, input data, answer key, scoring rule | Reproducible scored result | Claiming a score from prose |
| W30/W31 | Declared domain content | Reviewed wheels with axioms and tests | Guessing a domain |

## 5. Definition of done

### Physical-backend phase

A user can ask for an operation and see:

1. whether the operation is accepted, or a precise gap;
2. every declared method that claims to compute it;
3. every declared method that only carries or represents a value;
4. the evidence class and first missing physical step for each candidate;
5. no claim that a template, proposal or carrier is a fabricated device.

### Transfer phase

A user can ask for an operation and a target and see:

1. an accepted operation contract, or a precise gap;
2. mechanisms from at least two domains, with source evidence and mapping laws;
3. what is preserved, what is relaxed and where the mapping stops being valid;
4. an artifact and target test plan, or an explicit statement that only a
   candidate exists;
5. the evidence level, passed tests and first missing step;
6. no claim that an analogy, bridge or mechanism name is a validated transfer.

### Pre-admission phase

A user can ask for a structural lead and see:

1. the operation and candidate structure;
2. whether a card is admitted, pre-admission or absent;
3. the knowledge state and explicit needs;
4. `supported_operations_changed: false`;
5. a named promotion path and reviewer action.

## 6. Guardrails

- A text match is not a graph proof.
- A structural score is not an isomorphism.
- A lead is not a supported operation or mechanism card.
- A template is not an exact route.
- A route is not a fabricated device.
- A reference adapter is not a live integration.
- A candidate is not a validation.
- A class-index isomorphism does not supply a metric, product, action or proof.
- A benchmark name is not an adapter or a score.
- No mechanism, parameter, mapping, measurement or external result is invented
  to fill a row.

## 7. Verification and evidence index

```bash
python3 tests/run_all.py                  # canonical gate
python3 tests/test_discovery.py           # 136/136, including hypotheses and pipelines
python3 cent matrix --json                # 36 rows / 12 operations
python3 cent hypothesis                   # 2 pre-admission leads
python3 cent pipeline quantized_carry     # 6 stages / 1 feedback edge
python3 cent envelope --point 0,1 --point 1,0 --point 0,-1 --point=-1,0 --json
python3 cent transfer quantized_carry --json
python3 cent propose "sqrt" --target glm-reference --json
python3 tests/show_work.py                # 22/22 proposals
```

Key references:

- [`docs/DEVELOPMENT_AUDIT.md`](docs/DEVELOPMENT_AUDIT.md) — observed coverage,
  matrix counts and capability gaps.
- [`docs/OPERATION_MATRIX.md`](docs/OPERATION_MATRIX.md) — evidence classes and
  row semantics.
- [`docs/PIPELINES.md`](docs/PIPELINES.md) — route decomposition and handoffs.
- [`docs/HYPOTHESES.md`](docs/HYPOTHESES.md) — pre-admission leads and the
  promotion boundary.
- [`docs/TRANSFER_COMPILER_OBJECTIVE.md`](docs/TRANSFER_COMPILER_OBJECTIVE.md) —
  transfer contracts, phases and success criteria.
- [`docs/REFINEMENT_DIVE.md`](docs/REFINEMENT_DIVE.md) — review triage, P1/P2
  backlog and guardrails.
- [`docs/README.md`](docs/README.md) — documentation index.

## 8. Decision log

- **Delta-sigma is one benchmark mechanism, not the objective.** The transfer
  layer must work for non-delta-sigma operations too.
- **The physical backend is a backend.** A transfer can target software,
  information or a physical route; a netlist is not the definition of success.
- **`supported_operations` was the admission gate; it is now a validation
  field only.** Directive D1 removes it from `retrieve()`. Pre-admission
  discovery remains separate; a whitelist membership test is not structural
  retrieval.
- **No operation-level branches in `discovery` just to claim breadth.** New
  capacity enters through contracts, cards, references and tests.
- **Blocked means blocked.** EXT-D5, EXT-D10b–e, W30/W31, Rule30/ARC and the physical KCL
  artifact stay explicit until their required evidence exists.
- **Computational evidence is a separate tier.** The six-method addition lab,
  its declaration profile and eight port contracts are evidence that the
  declared computations are correct. They do not satisfy the physical-transfer
  gate, and they do not become production methods merely because they pass.
  Promotion requires an exact route, a mechanism card and a target adapter; the
  fluid reversed-port difference is the first method promoted under that rule.
- **Declaration fields are forcing conditions.** Effort/flow, junction type,
  sign/reference, gain/offset, range/resolution, source/load boundary and
  nonidealities select and constrain the model. They are not measured physical
  forces, and no nonideality is turned into a parameter without evidence.

Work order and priority belong only to [`DIRECTIVE.md`](DIRECTIVE.md). The
immediate execution state, including the D1 gate, is tracked in
[`WORKFLOW.md`](WORKFLOW.md). This ledger does not name a next task.
