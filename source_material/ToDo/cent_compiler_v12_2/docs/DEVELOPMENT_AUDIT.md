# Development audit — operation coverage

**Date:** 2026-11-11  
**Scope:** canonical local gate and CLI smoke checks; no external fabrication
or Lean evidence. The Leech class audit uses a caller-declared external basis
and corpus, and labels that provenance explicitly.

## Gate result

```text
GATE SUMMARY: 17/17 suites passed
README CONSISTENCY: OK
```

The gate passed **824/824 checks**. The checks cover the existing declared
routes, templates, gaps and certificates. The 11 Phase 1 registry checks cover
the seven seeded mechanism cards, their provenance, first gaps and evidence
levels; two console checks exercise the `cent mechanism` list and card lookup;
the transfer-contract, registry and engine checks cover ten operation
contracts, feature-based retrieval, candidate-only output, the six new
reference-backed contracts and their explicit adapter gaps, and CLI refusal;
fourteen evaluation checks cover known-valid recall, five negative controls,
six unadapted operations, three refused names, two T1 refusal records, target
pass rate and evidence completeness; twenty proposal checks cover
bundle construction, readiness, explicit analogy/isomorphism boundaries, export,
CLI refusal and the append-only review ledger with accepted, rejected and
tested states, notes and certificate evidence; and forty-five target checks
execute the eight `glm-reference` adapters over twenty-four fixed vectors,
compare the exact source and target, check the uniform-quantizer baseline,
log-domain sqrt enclosures, KCL, fluid and op-amp commutativity, and
difference anti-commutativity, and enforce declared reference-operation
latency/bit budgets, emitting
target-simulated certificates. A separate live `glm-live` target executes
the external GLM CLI for exact KCL sum/difference and reports
`target-integrated`; it is outside those reference-target checks and makes no
performance, latency or bit-budget claim. The T3 breadth probe records that the
current GLM CLI refuses `sqrt`/`exp` and offers exact `mult`/`div` without
mechanism cards; the live target therefore remains KCL sum/difference only. See
[`evidence/live-glm-breadth/README.md`](evidence/live-glm-breadth/README.md).
They do not prove that every operation or alternative method is covered.

## Observed operation matrix

These observations come from `cent compile`, `cent report` and `cent discover`.
“Exact program” means the exact-core program was generated; it does not mean an
assembled exact route exists.

| £ form | Parser | Ranked ∆ | SPICE template | Exact program | Exact route |
|---|---|---|---|---|---|
| `y = x + z` | yes | 2 domains | `kcl_summer` | yes | yes (KCL) |
| `y = x - z` | yes | 2 domains | `kcl_summer` | yes | yes (KCL) |
| `y = x * z` | yes | 3 domains | `multiplier` | yes | no |
| `y = x / z` | yes | 2 domains | `divider` | yes | no |
| `y = exp(x)` | yes | 2 domains | `diode_exp` | yes | no |
| `y = log(x)` | yes | 1 domain | `log_amp` | yes | no |
| `y = tanh(x)` | yes | 1 domain | `clipper` | no: missing `lo`, `hi` | no |
| `y = sqrt(5)` | yes | declared candidates | `opamp_sqrt`/gap by DAG | yes | 3 declared route models |
| delta-sigma | yes | carrier candidates | `delta_sigma` | yes | carry route, not a compute algorithm |

`cent discover "compute an irrational value with an analog method"` returns 12
candidate methods across five domain labels, with 3 exact route models and 3
physical device bindings. That is the problem-oriented view. `cent matrix` now
provides the general operation × method report: it derives rows from the route
constructors, structural template table and discovery's bridge/text evidence.
Every row names its evidence class, role, domain, carrier, route and first gap.
Nine rows also carry an explicit mechanism id: the KCL sum/difference routes,
the fluid sum/difference routes, the op-amp sum/difference routes, the
log-domain route, the delta-sigma route and the W24 log-domain bridge. Templates, text candidates, packing and gap rows remain
unlinked.
The current matrix has 32 rows across 12 operations: 9 exact routes, 1 exact
algorithm, 7 structural templates, 1 declared bridge, 1 declared analogy,
12 inherited wheel candidates and 1 gap. The exact algorithm is the
`bounding_box` orientation envelope, over a finite declared direction set. It is
still a catalogue of declared evidence, not a fabricated-device report.

The four assembled operations now also expose a micro-pipeline through
`cent pipeline`: stages and handoffs are read from the route's actual
`cent-program/1` instructions. The delta-sigma pipeline has six stages and one
explicit feedback edge; `difference` is `neg → sum`, and `sqrt` is
`log → scale → exp`.

`cent hypothesis` adds a separate pre-admission view. It scores unsupported
mechanism cards against an operation's declared behavior and requires a real
primitive-chain overlap, then records review leads in the existing `CentWheel`
states with explicit `needs`. The Q-tensor/`bounding_box` and
Bresenham/`quantized_carry` examples retain `DOESNT-KNOW` provenance but are not
mechanism cards. Both were audited on 2026-11-11. Q-tensor was retired after an
exact proof that its scalar invariants are orientation-blind; Bresenham was
retained only as the one-tick floor variant, with the existing two-tick target
explicitly not equivalent. Their records are in `docs/hypothesis-resolutions/`;
initial absence-based records are under `history/`. The command reports
`supported_operations_changed: false` and does not create transfer candidates.
`cent hypothesis --resolve` asks each declared need one at a time, retries with
supplied answers, and records keep/retire; retire requires a reason, and keep
does not promote the lead.

`tests/test_assembly.py` now carries the focused operation fixture matrix for
`mult`, `div`, `exp`, `log`, `sqrt` and `tanh`. It records each structural
template, whether an exact program exists, and the first gap: no assembled
route for the first four, no fabrication evidence for `sqrt`, and the missing
`lo`/`hi` parameters for `tanh`.

## Proposal handoff

`cent propose "sqrt" --target glm-reference --json` builds reviewable
`cent-proposal/1` records without validating a target. `--out DIR` writes
`index.json`, `index.md` and one JSON per proposal. The bundle separates
`ready-for-execution`, `needs-target-adapter`, `needs-target-vectors` and
`needs-environment`; only the first carries an executable handoff command. The
11 proposal checks do not invent an adapter and do not claim an isomorphism.
See [`TRANSFER_PROPOSALS.md`](TRANSFER_PROPOSALS.md).

## Wheel and proposal audit

The wheel index contains 39 built wheels and 39 built IDs across W1–W41.
W26/W27 are now sourced astrophysics/cosmology wheels: four axioms, five cases
and one negative control each, with exact dimensions and ten declared
cross-domain junctions. W30/W31 remain reserved and absent; they have no
declared domain content in the repository. Those two omissions are not filled
here.

`python3 tests/show_work.py` passes **22/22** proposals and regenerates 22
`.cir` files. The original comparison suite is **6/7**, with proposal 07
reported as a dimensional check rather than a pass. `tests/test_proposals.py`
now runs that audit in the canonical gate, pins the 22 proposal IDs and
netlist filenames, and checks the separate 6/7 comparison.

The fixed corpus at `tests/fixtures/glm_cent_questions.json` is run by
`tests/test_question_corpus.py`: 13 stable CLI questions, exact JSON fields,
two refusals and explicit gaps. It is evidence/reproducibility coverage, not a
benchmark score.

The GLM application audit at
`tests/test_glm_application_audit.py` records eight sourced GLM gaps and tests
six scalar application probes through the exact core, plus the exact KCL
residual route. It records five gap queries, one parser refusal, the `tanh`
missing-parameter gap and two discovery false matches (Griess product and
matrix-vector product both overmatch generic multiplication). The same suite
checks the six-method addition lab as `cent-computational-evidence/1`: six
declared methods, eight port contracts covering the six lab methods plus the production KCL and rotational rows, and `physical_transfer: false`. The false
matches are findings, not accepted equivalence. See
[`GLM_CENT_APPLICATION_AUDIT.md`](GLM_CENT_APPLICATION_AUDIT.md).

The direct-question audit at `tests/test_glm_direct_questions.py` runs **12/12**
checks. Packing now proposes the W36/W37 Pressure Settling Engine after scanning all
39 wheels; its exact fixed-container probe resolves overlap without claiming
optimality. The audit
tests the lexical move tie-break, 24D net-displacement accounting and exact 24D
class-word XOR separately; the operation matrix keeps XOR, tie, path and Rule30
out and records packing as a declared analogy. See
[`GLM_DIRECT_QUESTIONS_AUDIT.md`](GLM_DIRECT_QUESTIONS_AUDIT.md).

The cent compiler has no Rule30 or ARC-AGI adapter. Related GLM/Hypothesis Engine
material exists beside the project, but no declared input/scoring adapter means
no Rule30 or ARC result is claimed here.

`cent leech-class` adds the compiler-side class-index audit without adding an
operation row. On the external 24x24 row-HNF basis and the 80,361-move corpus
it re-derives 63,257 distinct class words, rank 24, one zero-class move and
5,000/5,000 sampled XOR compositions. The audit is exact integer arithmetic,
uses no floats, and keeps the lattice metric/q-form, Griess product and
Monster action as explicit gaps.

## Concrete development areas

1. **Sum and difference now have an exact KCL route.** The route has a declared
   junction contract, structural audit, exact two-input simulation and typed
   graph. A normalized `cent bind sum-kcl` binding preserves both inputs and
   audits the exact total. It still has no physical voltage/current mapping,
   source/load compliance, error budget or fabrication evidence.
2. **Exact route coverage remains sparse.** Multiplication, division,
   exponential, logarithm and saturation have structural SPICE templates and
   exact programs, but no assembled route with the same route-level evidence as
   the KCL and square-root/delta-sigma routes.
3. **Templates are not routes.** `kcl_summer`, `multiplier`, `divider`,
   `diode_exp`, `log_amp` and `clipper` are declared structural templates. They
   must not be described as exact physical methods or fabricated devices. This
   classification is regression-covered by `tests/test_discovery.py` and the
   assembly fixture matrix.
4. **`tanh` needs declared parameters.** Its exact program is rejected because
   `lo` and `hi` are missing. The gap is explicit and should be resolved only
   with declared values.
5. **Operation-level discovery is covered.** `cent discover` resolves reviewed
   operation verbs and nouns — multiply/product/times, divide/quotient/ratio,
   exponentiate/antilog, logarithm/ln and add/sum — to their declared
   contracts. `cent matrix` remains the broader evidence catalogue; discovery
   stays scoped to the requested operation and does not promote a matrix row or
   template into an assembled route.
6. **Ordered composition lacks a handoff.** The discovery parser records ordered
   goals, but no declared handoff maps a computed result into a carrier; the
   missing handoff remains a gap.
7. **External evidence is layered.** D5 still requires a real fabricated
   device. D10a is complete: `cent leech-class` re-derives the 24-bit class
   index from a declared basis and the exported corpus. D10b-e remain blocked on
   the lattice metric/q-form, a Griess multiplication tensor, a Monster
   representation/action and Lean/Viazovska tooling. The class index is not an
   operation-matrix row or a Griess/Monster computation.

## What this means for the goal

Delta-sigma is visible as a **carry** route for irrational values. The compiler
also exposes several alternative square-root methods (diode, feedback, fluidic,
mechanical, digital delta-sigma and translinear candidates), and now provides an exact
KCL route for sum and difference. It does not yet provide the same exact-route
breadth for multiplication, division, exponential, logarithm or saturation. The
operation × method matrix is published with explicit evidence classes and gaps.
The forward sequence is now maintained in
[`../PHYSICAL_COMPILER_ROADMAP.md`](../PHYSICAL_COMPILER_ROADMAP.md); the
remaining items are evidence/evaluation steps, not a single “add more routes”
task.

The 2026-11-11 audit also found that the parser diagnostics and guide had
advertised binary `+`/`-` before they were implemented. That mismatch was
resolved: binary addition and subtraction now decompose to `sum`/`neg`, and the
regression is in `tests/test_ui.py`.

## Roadmap stocktake

The canonical gate is **17/17 suites and 824/824 checks**. The matrix has
**32 rows across 12 operations**: 9 exact routes, 1 exact algorithm, 7
structural templates, 1 declared bridge, 1 declared analogy, 12 inherited
candidates and 1 gap. The ten operation contracts are `sqrt`, `sum`, `difference`,
`quantized_carry`, `mult`, `div`, `exp`, `log`, `reciprocal` and `sign`. The
first four retrieve 3, 3, 3 and 1 transfer candidates respectively; the six new
contracts retrieve zero candidates and carry explicit target-adapter gaps.
`cent evaluate` measures four known-valid cases, five negative controls, six
unadapted operations and three refused names: 10/10 expected candidates, 4/4
cases, 0/5 negative-control false positives, 8/8 target pairs, 8 artifacts, 2
supported-but-unadapted candidates, and 10/10 retrieval / 8/8 target evidence
completeness. Eight reference adapters and the live KCL target are implemented.
The two remaining supported candidates, cam and orifice, carry explicit T1
refusal records with required evidence; they remain unadapted.
`cent hypothesis` adds two pre-admission leads without changing any
`supported_operations`. Every transfer candidate now carries a
  `cent-relaxation/1` record; retrieval defaults to `unclassified`, and the
target-backed exact KCL, fluid and op-amp sum/difference routes receive `exact`.

The post-G5b scope boundary, loose ends and development track are recorded in
[`CURRENT_SCOPE_AND_NEXT_TRACK.md`](CURRENT_SCOPE_AND_NEXT_TRACK.md). The
roadmap gives the order and the reason for each next step. In short:

1. Q is retired by proof and Bresenham is retained narrowly;
2. the relaxation record is implemented; retrieval defaults to `unclassified`
   and target-backed exact KCL/fluid sums and KCL difference are classified `exact`;
3. measure the declared ten-operation corpus instead of inferring breadth from
   the original four contracts; G5a intake and G5b evaluation are complete for
   the declared corpus, while external expansion remains open;
4. broaden the live target and external budgets only with reproducible evidence;
5. leave physical KCL values, D5, D10b–e, W30/W31 and Rule30/ARC blocked until
   their required data exists.

## Capability gaps that remain

8. **Domain coverage remains partial.** W26/W27 add sourced astrophysics and
   cosmology coverage, but W30/W31 still need a declared domain first. Adding an
   empty or invented table is not coverage.
9. **Rule30 and ARC-AGI remain unsupported.** The fixed question corpus covers
   declared CLI evidence only; no adapter, input data or scoring rule is
   declared for those benchmarks, so no score is claimed.
10. **Discovery has two overbroad matches.** `compute a Griess product` and
    `compute a matrix-vector product` currently resolve to generic multiplier
    methods. The application audit records this as a finding; those methods are
    not accepted as Griess or matrix-vector implementations. Vector softmax
    reduction is refused because `sum()` is not an accepted cent function.
11. **Direct Leech/geometry/Rule30 questions have no methods; packing now has
    a declared candidate.** The pressure-settling engine combines W36 squared
    penetration/wall energy with W37 Maxwell relaxation and passes a fixed-
    container exact probe. It has no global optimality certificate, rotation or
    arbitrary square-size support. The lexical move tie-break is not a Leech
    tie resolver, net displacement is not an efficient path planner, the 24D
    class-word XOR is an index utility rather than an operation row, and Rule 30
    needs a declared adapter, data and score.

No method, parameter or measurement was invented in this audit. The gate is
green; the development areas are capability gaps, not hidden test failures.
