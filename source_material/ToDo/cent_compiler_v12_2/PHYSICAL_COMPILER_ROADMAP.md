# Physical Compiler — Forward Roadmap

**Status:** stocktake and forward plan under the transfer-compiler objective  
**Last reviewed:** 2026-11-12  
**Canonical gate:** 17/17 suites, **824/824 checks**, README consistency **OK**

> **Document role:** this is the forward plan and priority order. The
> [`CURRENT_SCOPE_AND_NEXT_TRACK`](docs/CURRENT_SCOPE_AND_NEXT_TRACK.md) owns the
> capability boundary and open-gap ledger; the
> [`TRANSFER_COMPILER_OBJECTIVE`](docs/TRANSFER_COMPILER_OBJECTIVE.md) owns the
> objective, schemas and historical phase record. The executive stocktake below
> is current; “Completed since” is a change log, not a second status page.

**Primary objective:** cross-domain computational method transfer. Given an
operation and a target, find mechanisms from any domain, declare a mapping and
validate an artifact. The physical backend is one target backend, not the
definition of the compiler. See
[`docs/TRANSFER_COMPILER_OBJECTIVE.md`](docs/TRANSFER_COMPILER_OBJECTIVE.md) for
the objective and [`docs/CURRENT_SCOPE_AND_NEXT_TRACK.md`](docs/CURRENT_SCOPE_AND_NEXT_TRACK.md)
for the current scope, loose ends and post-G5b track.

This roadmap replaces the earlier checklist. It records what is actually
complete, what is only declared, what is blocked, and why each future step
exists. It does not promote a candidate by changing a label.

**Evidence tiers, from weakest to strongest:** computational laboratory
(declared math only) → production exact route (source-simulated) →
`glm-reference` adapter (`target-simulated`) → live `glm-live`
(`target-integrated`) → physical binding/measurement. A method can appear in
more than one tier only when the higher-tier artifact actually exists.

## 1. Executive stocktake

| Area | State | Current evidence | Remaining work |
|---|---|---|---|
| Operation coverage | Complete for declared operations | 12 matrix operations; 32 rows | More operation contracts only with semantics and tests |
| Alternative catalogue | Complete | 9 exact routes, 1 exact algorithm, 7 structural templates, 1 bridge, 1 analogy, 12 inherited candidates, 1 gap | Keep weak evidence separate |
| Exact routes | Complete for current scope | KCL sum/difference, fluid sum/difference, op-amp sum/difference, log-domain sqrt, op-amp sqrt, delta-sigma carry | More routes are not automatically better; add with evidence |
| Exact algorithm | Complete for current scope | `bounding_box` / `orientation-envelope` with exact finite-direction probe | No global-orientation or physical claim |
| Micro-pipelines | Complete for four operations | `sqrt`, `sum`, `difference`, `quantized_carry`; stage and handoff data from route programs; `difference` has KCL, fluid and op-amp mechanisms | Execution/composition of arbitrary sub-operations remains open |
| Pre-admission hypotheses | Complete; Q retired, Bresenham retained narrowly | `cent hypothesis`; 2 leads with `DOESNT-KNOW` provenance; Q proof and Bresenham one-tick evidence recorded | Reopening Q or widening Bresenham requires new evidence, not silent reactivation |
| Transfer contracts | Complete; ten-operation intake and relaxation records implemented | 10 operation contracts; 8 mechanism cards; behavior signatures; `cent-relaxation/1` default `unclassified`; six new contracts carry explicit no-adapter gaps | Broader mechanism coverage; live only on a new interface |
| Target validation | Complete for four reference operations (eight mechanism pairs) | 8 `glm-reference` adapters over 24 fixed vectors; live `glm-live` KCL sum/difference | Broader live coverage only after a new interface |
| Proposal handoff | Complete | `cent propose` bundles, index, review ledger, readiness states; current bundles in `examples/transfer/` | Review-to-validation remains manual; no proposal is auto-validated |
| Physical KCL artifact | Blocked | normalized KCL route and binding exist | Requires declared values, source/load model, error budget and reference netlist |
| External evidence | Partly blocked | D10a class-index audit complete | D5 and D10b–D10e remain blocked |
| Domain coverage | Complete for current declared wheels | 39 wheels; W30/W31 reserved | W30/W31 need a declared domain, not a guessed table |
| Documentation | Current | Gate count, tree, module and test counts synchronized | Keep roadmap and audit reviewed with each capability change |

### Current command baseline

```bash
python3 tests/run_all.py                  # 17/17, 824/824
python3 cent evaluate --json              # G5b retrieval metrics
python3 cent propose sqrt --target glm-reference --json  # 3 proposals
python3 cent matrix --json                # 32 rows, 12 operations
python3 cent pipeline quantized_carry     # six stages, one feedback edge
python3 cent hypothesis                    # two pre-admission leads
python3 cent explore addition --declarations examples/addition_declarations.json --glm --json
python3 cent transfer sqrt --json          # 3 candidates
python3 cent transfer sum --json           # 3 candidates
python3 cent transfer difference --json    # 3 candidates
python3 cent transfer quantized_carry --json  # 1 candidate
```

### Completed since the previous roadmap review

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
evidence the artifact is supposed to carry. The correct next action is to supply
a declared KCL design point, then add the artifact path.

### D — Evidence and repository

**Complete.**

- README, docs, package tree, module count and test counts are checked by the
  canonical gate.
- Parser/guide mismatches are recorded and regression-covered.
- Unsupported operations and missing links remain explicit gaps.

**Why this is complete:** the repository can be audited without trusting prose;
the gate and consistency preflight fail on drift.

### E — External evidence and blocked layers

**D5 and D10b–D10e remain blocked; D10a is complete.**

- **D5 fabricated-device evidence:** requires a real fabricated device.
- **D10a class-index audit:** complete. `cent leech-class` re-derives 63,257
  class words and 5,000/5,000 sampled XOR compositions from a declared row-HNF
  basis and corpus.
- **D10b lattice metric/q-form:** blocked on declared metric data.
- **D10c Griess product:** blocked on a declared multiplication tensor and exact
  product check.
- **D10d Monster action:** blocked on a representation, generators and action
  table.
- **D10e Lean/Viazovska:** blocked on a Lean build/elaborator and a declared
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

**G1–G5b are complete for their declared scope; G4b/T3 is closed for the current interface; external expansion is open.**

- **G1 — contracts:** complete.
- **G2 — mechanism cards:** complete; eight cards with provenance and gaps.
- **G3 — transfer v0:** complete; candidate-only retrieval by behavior.
- **G4 — GLM reference and live adapter:** complete for the declared scope. Four
  reference operations run over twenty-four fixed vectors across eight mechanism
  pairs; live `glm-live` covers
  exact KCL sum/difference and is `target-integrated`.
- **G4.5 — proposal handoff:** complete; reviewable bundles, readiness,
  executable handoff and append-only review ledger.
- **G4b/T3 — current-interface live boundary: closed by recorded refusal.**
  Only KCL sum/difference are live. The T3 breadth probe records why `sqrt`,
  `exp` and mechanism-less `mult`/`div` do not add an honest live transfer on
  this interface. Reopen only with a new reproducible interface and a declared
  mechanism; no external latency, bit-budget, model or performance claim exists.
- **G5 — evaluation:** complete for the declared ten-operation corpus.
  `cent evaluate` reports 10/10 expected-candidate recall, 4/4 case recall, 0/5
  negative-control false positives, 8/8 reference target pairs, 8 artifacts,
  2 supported-but-unadapted candidates and 10/10 retrieval / 8/8 target evidence
  completeness. Known-valid means declared card support, not external ground
  truth; no live or measured target is claimed.

**Why G4 is complete despite G4b:** the original G4 acceptance was reference
artifacts plus a live KCL target. That threshold was met; the current scope now
has eight reference pairs. The additional op-amp and fluid routes are separate
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

## 3. Future sequence and why

The order below is deliberate. It moves from evidence discipline to evaluation,
then to broader targets and blocked external layers. The sequence is not a
promise that every step will produce a positive result.

| Order | Step | Why this step | Prerequisite | Done when |
|---|---|---|---|---|
| 1 | **H1 — resolve each hypothesis lead (complete)** | The hypothesis layer is only useful if leads have a closure path; a permanent lead backlog becomes a second unsupported catalogue | The resolution loop and two evidence audits are complete | Q has a recorded retirement proof; Bresenham has a narrowed retention record; only separately proven leads become mechanism cards |
| 2 | **R1 — relaxation classification (complete)** | A mapping that cannot say what it loses is not a usable transfer, and a structural match cannot establish a relaxation class | Declared classes, basis and target-evidence guard | Every candidate has a `cent-relaxation/1` record; retrieval defaults to `unclassified`; non-`unclassified` needs target artifact/tests |
| 3 | **G5a — ten-operation corpus intake (complete)** | Four operations and seven cards were too narrow to measure retrieval or overfitting; proposal bundles already provided the intake shape | Six additional operation contracts with semantics, reference and at least one fixed test; target adapter or explicit gap | Ten operation entries and at least six mechanisms are declared; every missing adapter is explicit |
| 4 | **G5b — evaluation metrics (complete)** | A corpus without known-valid and known-invalid cases cannot measure recall or false positives | Declared ground truth, negative controls and target tests | Recall, false-positive rate, target pass rate and evidence completeness are reported; no unlabelled false positives |
| 5 | **T2/G6 — independent held-out evaluation** | G5b is a declared-support regression corpus, not external truth; this is the remaining evidence priority | A declared external corpus with provenance, held-out labels and negative controls | Held-out recall/false-positive behaviour is reported, or the corpus remains an explicit gap |
| 6 | **C1 — physical KCL artifact** | The physical backend has a normalized KCL route but no artifact path for its own sum/difference operation | Declared voltage/current map, source/load model, values and error budget | A physical artifact and its limits are emitted; no values are invented |
| 7 | **E1 — external mathematical layers** | D10a proves a group isomorphism, not a metric, Griess product, Monster action or Lean result | Declared metric/q-form, multiplication tensor, representation/action table, or Lean/Viazovska tooling | Each layer passes or remains an explicit gap; no cross-layer substitution |
| 8 | **F1 — external adapters for Rule30/ARC** | These names currently describe material, not executable compiler capabilities | Declared adapter, input data, answer key and scoring rule | A reproducible adapter result or a refusal; no benchmark score before then |

### Step details

#### 1. H1 — close the hypothesis loop (complete for current leads)

**Why:** `cent hypothesis` is intentionally pre-admission. Keeping leads there
forever would make “discovered” mean “listed.” The resolution loop now asks for
missing proof/test/definition answers and records a decision.

The loop was run on 2026-11-11. Q-tensor was retired after an exact proof that
scalar invariants cannot select a director: the same invariants produce
envelopes with areas `2/1` and `66/25`. Bresenham was retained narrowly after an
exact one-tick floor proof and range test; the existing two-tick nearest-level
target mismatches and is not claimed equivalent. Records are in
`docs/hypothesis-resolutions/`; initial absence-based records are under
`history/`. Reopening Q or widening Bresenham requires new evidence.

**Do not:** add a `supported_operations` entry because a lead exists. The
promotion gate still requires a card, semantics, a reference test, exact/target
evidence and review. The resolver explicitly reports that answers are supplied
evidence, not automatically verified proofs.

#### 2. R1 — make loss explicit (complete for current candidates)

**Why:** the transfer objective is about what survives the move. The old
candidate schema had only a free-text `relaxed` list, so a reader could not tell
whether a mapping was exact, asymptotic, parameter-dependent or unknown.

The schema now carries a `cent-relaxation/1` record. Retrieval defaults every
candidate to `unclassified` with a basis. A non-`unclassified` class requires a
matching target, target-level evidence, an artifact and at least one target
test. The exact KCL, fluid and op-amp sum/difference targets are
recorded `exact`; delta-sigma and
sqrt target certificates remain explicitly `unclassified` because fixed-vector
passes do not establish a general relaxation class. Missing basis, missing
target, source-only evidence, missing artifact/tests and unknown classes are
refused.

#### 3. G5a — build the actual corpus (complete)

**Why:** the original registry supported four operations. A retrieval system
that is only tested on those four cannot show recall, domain breadth or
resistance to false positives. The corpus is also the only way to make “ten
operations” an evidence claim rather than a target.

**Done:** ten operation contracts are declared. The six additions — `mult`,
`div`, `exp`, `log`, `reciprocal` and `sign` — each name an exact or certified
reference and a fixed test. None has a production mechanism or target adapter;
`cent transfer` returns zero candidates with an explicit adapter gap rather
than a fabricated match. Every operation contract still has semantics, a
reference and a fixed test; G5b measures the resulting zero-candidate gaps
separately.

#### 4. G5b — measure, don’t assert (complete)

**Why:** counts of candidates are not evaluation. The corpus must separate
known-valid, known-invalid, unadapted and refused cases, then report recall,
false positives, pass rate and evidence completeness.

**Done:** `cent evaluate` implements four known-valid cases, five negative
controls, six zero-mechanism operations and three refused names. It reports
10/10 expected-candidate recall, 4/4 case recall, 0/5 negative-control false
positives, 8/8 reference target pairs, 8 artifacts, 2 supported-but-unadapted
candidates, 10/10 retrieval evidence and 8/8 target evidence. Known-valid means
explicit mechanism-card support, not independent external ground truth.

**Do not:** call a reference adapter a live integration. `target-simulated` and
`target-integrated` remain separate evidence levels.

#### 5. T2/G6 — evaluate beyond declared support

**Why:** G5b measures whether the compiler retrieves the mechanisms its own
cards declare. It cannot show independent recall or false-positive behaviour on
an external corpus. This is the next evidence priority, not another route count.

**Current state:** no independent held-out corpus with provenance, labels and
negative controls is declared. The existing `cent evaluate` result is therefore
reported as declared-support evidence only. Do not re-label it as external truth.

**Done when:** a held-out corpus exists and its recall/false-positive results are
reported, or the corpus remains an explicit gap.

**Live boundary note:** the current-interface T3 probe is separate and already
closed by refusal. It refuses `sqrt`/`exp` and has no production card for exact
`mult`/`div`; see
[`docs/evidence/live-glm-breadth/README.md`](docs/evidence/live-glm-breadth/README.md).
Reopen only with a new interface.

#### 6. C1 — physical KCL artifact

**Why:** the normalized KCL route is exact but not a physical artifact. The
physical backend should eventually emit a real KCL sum/difference path with
source/load and error budget. The blocker is declared values, not code
structure.

**Do not:** choose component values by convention or copy another route’s
numbers.

#### 7. E1 — external mathematical evidence

**Why:** D10a’s class index is genuinely complete, but a group isomorphism does
not define the Leech metric, Griess product, Monster action or a Lean proof.
Each requires its own declared structure and test.

#### 8. F1 — benchmark adapters

**Why:** Rule30 and ARC-AGI are currently names in the audit, not compiler
capabilities. Adding a label without input, answer key and scoring would be the
kind of unsupported claim the rest of the project rejects.

## 4. Blocked items and what would unblock them

| Item | Blocked on | Unblock condition | What must not happen |
|---|---|---|---|
| C1 physical KCL artifact | Declared component values, source/load, compliance and error budget | A reviewed KCL design point with physical assumptions | Values copied from another route or invented |
| D5 fabricated device | Real fabrication and measurement | Fabricated device and measured evidence | A netlist or simulation called fabricated |
| D10b metric/q-form | Declared metric data | Exact metric and q-form with checks | Transplanting a 24-bit group coordinate |
| D10c Griess product | Declared multiplication tensor | Exact product check | Treating XOR as Griess multiplication |
| D10d Monster action | Representation, generators, action table | Action check | Inferring an action from class words |
| D10e Lean/Viazovska | Lean build/elaborator and codebook objective | Reproducible build/check | A theorem label without a build |
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
python3 tests/run_all.py                  # 17 suites, 824/824, README consistency
python3 tests/test_discovery.py           # 133/133, including hypotheses and pipelines
python3 cent matrix --json                # 32 rows / 12 operations
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
- **`supported_operations` remains the admission gate.** Pre-admission discovery
  is separate by design.
- **No operation-level branches in `discovery` just to claim breadth.** New
  capacity enters through contracts, cards, references and tests.
- **Blocked means blocked.** D5, D10b–e, W30/W31, Rule30/ARC and the physical KCL
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

The next implementation choice should follow the post-G5b track in
[`docs/CURRENT_SCOPE_AND_NEXT_TRACK.md`](docs/CURRENT_SCOPE_AND_NEXT_TRACK.md):
T1 is closed for its declared scope and T3 has a current-interface refusal, so
the remaining evidence priority is T2's independent held-out evaluation. It
should not begin by adding another operation alias or another unverified
mechanism card.
