# Cross-domain transfer proposals

`cent propose` turns the ranked transfer retrieval into reviewable proposal
records.  A proposal is a handoff artifact, not a validation result.

## Usage

```bash
python3 cent propose "sqrt" --target glm-reference --json
python3 cent propose "sum" --target glm-reference
python3 cent propose "sqrt" --target glm-reference --out proposals/sqrt
python3 cent propose "sqrt" --target glm-reference --trial
python3 cent trial proposals/sqrt
python3 cent trial proposals/sqrt <proposal-id>
python3 cent trial --wheel
python3 cent trial --wheel --json
```

`--out DIR` writes:

```text
DIR/
├── index.json          # bundle index, readiness and review summary
├── index.md            # human review table
├── proposal-*.json     # one cent-proposal/1 record per candidate
├── reviews.json        # append-only review ledger (after cent review)
└── evidence/           # copied tested certificates (after tested reviews)
```

## Readiness

Each proposal has exactly one readiness state:

| State | Meaning |
|---|---|
| `ready-for-execution` | A declared target adapter and fixed vectors exist; run the named handoff command. |
| `needs-target-adapter` | No executable adapter is declared for this operation/mechanism. |
| `needs-target-vectors` | An adapter exists but declares no fixed vectors. |
| `needs-environment` | A live external target exists but its runtime is unavailable. |

Only `ready-for-execution` proposals carry an executable `handoff.command`.
Every proposal still has `status: unvalidated`; the command produces the actual
certificate. Review state is deliberately separate from that validation status.

## Computational trial side-loop

`--trial` executes every `ready-for-execution` proposal's declared adapter over
its fixed vectors and attaches a `cent-proposal-trial/1` block. `cent trial DIR`
does the same for a saved bundle, and `cent trial DIR <proposal-id>` selects one
proposal. The trial is a reviewer check of concrete behavior, not a new review
decision and not a validation.

Each trial states what is being applied and what is executed:

```text
proposal: square root — root is the nonnegative value whose square is x.
mechanism: logarithm-domain square root [transcendental-identity] from electrical
target: glm-reference — log_domain_sqrt(x, precision=..., tolerance=...)
what: Apply log-domain square root to square root on glm-reference; execute 3 declared fixed vector(s) and compare the adapter output with the reference result.
trial: pass; 3/3 fixed vector(s) pass
verdict: works on the declared fixed vectors; target-simulated evidence only
adjustment: No adjustment is indicated by these fixed vectors. Keep the declared target boundary.
  sqrt-two: input=2/1 expected=[~1.4142136, ~1.4142136] actual=[~1.4142136, ~1.4142136] passed=True
```

The proposal summary is descriptive only: it names the operation semantics,
mechanism/principle, source domains, analogy basis and target adapter.

## Operation wheel

`cent trial --wheel` spins through every declared operation contract, builds its
proposal set, and executes every `ready-for-execution` proposal. It is the
inventory view: which applications can be tested now, which mechanisms pass,
and which operations have no adapter yet.

Current declared wheel: **10 operations, 10 testable, 0 without an adapter**
(`sign`). The selectable limit controls proposals per operation (default 3).

The wheel is deliberately bounded by the operation registry and target
adapters. It is not a claim that millions of operations were searched, and an
`NO ADAPTER` row is a declared gap, not evidence that the operation is
impossible.

Non-ready proposals return `status: not-run` with the readiness state and the
next action. A failing vector set returns `status: fail` and names the failed
checks, so the reviewer can see whether the mapping or adapter needs adjustment.
The JSON retains exact values; the terminal shortens very long rationals with
`~` for readability.

A passing trial is `target-simulated` fixed-vector evidence. It does not prove
the behavioral analogy, establish a general capability, make a measured-device
claim or record a review decision.

## Review states and durable ledger

Every proposal starts with `review.state: unreviewed` and an empty history.
Record a decision with:

```bash
python3 cent review proposals <proposal-id> --state accepted \
  --reviewer alice --note "Handoff reviewed"
python3 cent review proposals <proposal-id> --state rejected \
  --reviewer bob --note "Missing independent evidence"
python3 cent review proposals <proposal-id> --state tested \
  --reviewer carol --note "Certificate attached" \
  --certificate sqrt-certificate.json
python3 cent review proposals --list
```

| State | Meaning |
|---|---|
| `unreviewed` | No reviewer decision has been recorded. |
| `accepted` | The handoff is accepted for execution; this is not a validation result. |
| `rejected` | The handoff is declined; a reason is required. |
| `tested` | A passing `cent-transfer-certificate/1` is attached as evidence. |

`tested` requires `--certificate`; the command checks the certificate schema,
`status: pass`, operation and target, copies it to `evidence/<sha256>.json`, and
records the hash. The ledger appends one event with sequence, prior state, new
state, reviewer, note and UTC timestamp. `reviews.json` is the source of truth;
`index.json` and the proposal file carry the current state and full history.
Re-exporting the bundle preserves the ledger. A review decision never changes
`status: unvalidated` and never claims an isomorphism or a target result.

For the current `sqrt` bundle, `log-domain-sqrt` is `ready-for-execution`; the
`cam-profile` and `orifice-pressure-flow` alternatives remain
`needs-target-adapter` and have recorded T1 refusal conditions. The `sum`, `difference` and `quantized_carry` bundles
are ready against their declared reference adapters.

## What a proposal contains

- operation contract, source reference and source tests;
- mechanism card, source domains, laws, invariants and failure modes;
- declared mapping steps and preserved/relaxed properties;
- behavioral analogy basis and `isomorphism_claimed: false`;
- target adapter, fixed vector ids and readiness;
- source and target provenance, checks and explicit gaps.

The analogy is deliberately not promoted to an isomorphism.  An exact
structure-preserving claim needs its own law, proof or certificate.

## Review loop

1. Run `cent propose "<operation>" --out DIR`.
2. Pick a `ready-for-execution` row from `index.md`.
3. Run `cent trial DIR <proposal-id>` (or `cent propose ... --trial`) to see
   the declared fixed-vector behavior and its adjustment note.
4. Record `accepted` or `rejected` with a reviewer and note.
5. Run the accepted handoff command and keep its certificate.
6. Record `tested` with `--certificate`; this copies evidence and appends the
   review event without marking the proposal validated.
7. For `needs-target-adapter`, declare the adapter and fixed vectors first.
8. Add the proposal's operation, mechanism, target and review record to the
   evaluation corpus; do not mark the analogy validated without target evidence.

The proposal layer makes the next action explicit; it does not make an
unimplemented mechanism executable.  `cent transfer ... --validate` remains the
only executable certificate path.  Reviews are decisions and audit evidence,
not certificates.

## Current example bundle

[`../examples/transfer/`](../examples/transfer/) contains the current bundles for
`sqrt`, `sum`, `difference` and `quantized_carry`: seven proposals, five
`ready-for-execution` and two `needs-target-adapter`. The directory also holds
the current `cent evaluate --json` payload. These are transfer handoffs; the 22
`examples/proposal_*.cir` files are a separate physical-backend show-work suite.
