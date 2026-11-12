# Cross-domain transfer proposals

`cent propose` turns the ranked transfer retrieval into reviewable proposal
records.  A proposal is a handoff artifact, not a validation result.

## Usage

```bash
python3 cent propose "sqrt" --target glm-reference --json
python3 cent propose "sum" --target glm-reference
python3 cent propose "sqrt" --target glm-reference --out proposals/sqrt
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
3. Record `accepted` or `rejected` with a reviewer and note.
4. Run the accepted handoff command and keep its certificate.
5. Record `tested` with `--certificate`; this copies evidence and appends the
   review event without marking the proposal validated.
6. For `needs-target-adapter`, declare the adapter and fixed vectors first.
7. Add the proposal's operation, mechanism, target and review record to the
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
