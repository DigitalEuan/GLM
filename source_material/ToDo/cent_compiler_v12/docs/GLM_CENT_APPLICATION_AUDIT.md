# GLM-to-cent application audit

This is a usage audit of the cent compiler against the GLM material in this
repository. The source evidence is:

- [`archive/expansion/hypothesis_engine_README.md`](archive/expansion/hypothesis_engine_README.md)
  for ARC unmet needs, Rule 30 prize status and the wheel-turn needs;
- [`LEECH_STUDY_AUDIT.md`](LEECH_STUDY_AUDIT.md) for the Griess/Monster limits;
- [`GLM_LEAN_REVIEW.md`](GLM_LEAN_REVIEW.md) for the unbuilt Lean tree and the
  missing cross-check.

No GLM model or Lean build was run for this audit. The GLM issues below are
declared gaps in those sources, not claims about a measured model failure.

## What was done

1. Extracted eight concrete GLM gaps from the source material.
2. Tried to express each as a cent problem or formula.
3. Ran `cent compile`, `cent report`/`cent eval` and `cent discover`.
4. Tested six scalar application probes through the exact core and the residual
   add through the exact KCL route.
5. Kept unsupported structures and overbroad name matches as findings. A
   generic multiplier was **not** accepted as a Griess or matrix-vector product.

The reproducible checks are in
[`tests/test_glm_application_audit.py`](../tests/test_glm_application_audit.py):
**19/19 checks** covering the issue list, six exact probes, one KCL route,
five gaps, one parser refusal, one exact-program gap, two false-match findings
and the six-method addition lab exposed as GLM computational evidence. The lab
profile is separate from physical-transfer evidence: it makes no GLM call,
model-score or physical-device claim.

## Evidenced GLM issues

| ID | GLM issue | Source | Cent result |
|---|---|---|---|
| `arc-fill` | ARC's most frequent unmet need is `primitive:fill` (19 tasks) | Hypothesis Engine README | no fill primitive; `cent discover "fill a region"` returns a gap |
| `arc-recolour` | Next unmet need is `primitive:recolour` (13 tasks) | Hypothesis Engine README | no recolour primitive; discovery returns a gap |
| `arc-unknown` | `primitive:unknown` is an unmet need (10 tasks) | Hypothesis Engine README | no autonomous primitive selector; discovery returns a gap |
| `rule30-prizes` | All three Rule 30 prize problems remain open; no finite certificate | Hypothesis Engine README | no proof or finite-certificate primitive; no claim generated |
| `griess-product` | No Griess multiplication tensor; move-class XOR is not a product | Leech study audit | current discovery **overmatches** generic multiplication; finding only, not accepted |
| `monster-action` | No Monster representation, generators or action table | Leech study audit | no action primitive; discovery returns a gap |
| `lean-build` | GLM Lean tree unbuilt; claimed wheel cross-check test absent | GLM Lean review | no Lean build/elaboration primitive; external gap |
| `r-calculus-range` | R-calculus and the range past `D=87867` remain unmet wheel needs | Hypothesis Engine README | no declared R-calculus or range primitive; gap |

## Scalar application probes

These are **free-license scalar probes**, not claims about the actual GLM
architecture. They exercise cent's physical-primitive catalogue and exact core
on operations that resemble GLM-style building blocks.

| ID | Formula | Primitives | Proposals observed | SPICE | Exact result |
|---|---|---|---:|---|---|
| `attention-score` | `score = query * key / sqrt(d)` | `mult`, `sqrt`, `div` | 32 | gap | `3` for `(3,2,4)` |
| `softmax-cell` | `weight = exp(score) / total` | `exp`, `div` | 4 | gap | `1/2` for `(0,2)` |
| `layer-norm` | `normalized = (x - mean) / sqrt(variance)` | `neg`, `sum`, `sqrt`, `div` | 40 | gap | `1` for `(5,3,4)` |
| `affine-cell` | `y = weight * x + bias` | `mult`, `sum` | 20 | gap | `10` for `(2,3,4)` |
| `residual-add` | `next = x + update` | `sum` | 5 | `kcl_summer` | `1` for `(5/7,2/7)` |
| `exp-denominator` | `denominator = exp(score1) + exp(score2)` | `exp`, `sum` | 20 | gap | `2` for `(0,0)` |

Every probe's proposals carry the `not-fabricated` boundary. The exact values
come from the exact-core program, not from a physical device simulation. Only
the residual-add probe has an assembled exact route: KCL returns `5/7 + 2/7 =
1` with `simulation.passed = true`.

The observed physical candidates include KCL junctions, diode/BJT exponential
stages, Gilbert-cell or AD633 multipliers, op-amp feedback dividers and
delta-sigma carriers. Those are declared proposals; they are not a claim that a
GLM can be run on them.

## Explicit gaps and refusals

- `fill`, `recolour`, unknown ARC primitive selection, `XOR` and Monster-action
  queries all return `matched=false`, no methods and a `gap` certificate.
- Full vector softmax, `exp(score) / sum(exp(score))`, is refused by the parser:
  `sum()` is not an accepted cent function. The scalar softmax cell above is not
  a substitute for vector reduction.
- `tanh` compiles to the `clipper` structural template and one proposal, but its
  exact program is unavailable because `lo` and `hi` are undeclared.
- Matrix-vector product is not a declared vector/shape contract; current
  discovery overmatches it to five generic multiplier methods.
- The Griess product is not a scalar multiplier. Current discovery overmatches
  it in the same way. These are recorded as findings and must not be counted as
  successful GLM applications.

## What this sharpens

The audit separates four levels that were easy to conflate:

1. **Declared gap** — no accepted cent primitive (fill, recolour, XOR, Monster,
   Lean, R-calculus).
2. **Scalar proposal** — the compiler generatively ranks physical candidates
   for a scalar relation, but no exact route or SPICE template exists for the
   composite.
3. **Exact-core application** — the scalar relation evaluates exactly, which is
   a logical test only.
4. **Exact physical route** — the KCL residual add is assembled and simulated;
   that is still not fabrication or device evidence.

## Executable target certificates

`cent transfer "quantized_carry" --validate --json`, `cent transfer "sqrt"
--validate --json`, `cent transfer "sum" --mechanism "kcl-conservation"
--validate --json`, `cent transfer "sum" --mechanism "fluid-continuity"
--validate --json`, `cent transfer "sum" --mechanism "opamp-summing"
--validate --json` and `cent transfer "difference" --mechanism "opamp-summing"
--validate --json`, `cent transfer "exp" --validate --json`, `cent transfer "log"
--validate --json`, `cent transfer "mult" --validate --json`, `cent transfer "div" --validate --json`, `cent transfer "reciprocal"
--validate --json` and `cent transfer "sign" --validate --json` now
execute fourteen pure-Python `glm-reference` adapters over forty-two fixed
exact vectors. The delta-sigma adapter reproduces source code and mean, checks bounded
state and a stateless uniform quantizer baseline; the log-domain sqrt adapter
checks its certified enclosure against the source route and an independent
`sqrt_q` baseline; the KCL adapters check exact source parity, sum commutativity
and difference anti-commutativity; the fluid-continuity and op-amp adapters check the same
normalized-flow sum law independently; and the D3 log-domain arithmetic
adapters check exp/log enclosures and exact product/quotient/reciprocal
containment. All emit `cent-transfer-certificate/1`
and declare reference-operation latency and bit budgets. Those reference certificates are `target-simulated` only: no GLM
model, external latency or performance result is claimed. A separate `glm-live`
target now executes the real external `GLM.py` CLI for exact KCL sum and
difference, parses its exact witness and reports `target-integrated`; it makes no
latency, bit-budget, model or performance claim. The focused transfer suite is
102/102 and the canonical gate is the current `tests/run_all.py` run.

The live-breadth probe in
[`evidence/live-glm-breadth/`](evidence/live-glm-breadth/README.md) sends exact
queries to the same CLI. It observes refusals for `sqrt(2)`, `sqrt(9)` and
`exp(0)`, and exact answers for `(1/2)*(1/3) = 1/6` and `(1/2)/(1/3) = 3/2`.
The latter do not create a live transfer because `mult` and `div` have no
production mechanism cards. T3 therefore records a current-interface refusal;
it does not claim that additional live operations are impossible.

## Next development targets

- Add explicit vector/reduction contracts before claiming softmax or
  matrix-vector support; do not let `mult` stand in for either.
- Add a narrow unsupported-structure guard so Griess/Monster names cannot match
  generic multiplication. The current audit records the false match; it does not
  accept it.
- Declare `lo`/`hi` for `tanh` or keep the exact-program gap explicit.
- Keep ARC fill/recolour/unknown, Rule 30 prizes, Lean build, Griess/Monster and
  R-calculus as gaps until their own data, proofs or adapters exist.

## Limits

This audit does not execute a GLM, run Lean, simulate a physical device, measure
a circuit or produce a fabrication netlist. The scalar probes are an application
experiment; they are not evidence that the GLM’s operations are physically
implementable. The exact results are rational/interval arithmetic checks, and
the KCL result is a declared exact route model.
