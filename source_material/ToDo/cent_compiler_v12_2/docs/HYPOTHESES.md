# Pre-admission hypotheses

`cent hypothesis` is the discovery layer between a structural lead and a
declared mechanism. It answers “is there an operation-shaped match worth
investigating?” without changing any mechanism card's `supported_operations` or
creating a transfer candidate.

The layer exists because the transfer engine's admission gate is intentionally
strict: a card is retrievable only when it explicitly names the operation. That
is the right gate for production transfer. It is not the right gate for early
structural exploration.

## Commands

```bash
python3 cent hypothesis
python3 cent hypothesis bounding_box
python3 cent hypothesis quantized_carry
python3 cent hypothesis bounding_box --json
python3 cent hypothesis --resolve nematic-q-tensor-bounding-box
python3 cent hypothesis --resolve nematic-q-tensor-bounding-box --json
```

`cent hypothesis` with no operation lists the declared leads and their
knowledge-wheel state. With an operation it reports:

- **admitted** — cards whose `supported_operations` already names the operation;
- **pre-admission** — cards whose primitive-chain overlap and structural score
  clear the declared threshold, but which do not support the operation yet;
- **leads** — explicit hypothesis records, separate from mechanism cards.

Every result states `supported_operations_changed: false`.

## Resolution loop

A lead is not closed by deleting it. `cent hypothesis --resolve <lead-id>` turns
each declared need into one explicit question:

- `proof:` — the exact derivation or a path to it;
- `test:` — the vector set, result or path;
- `negative-control:` — the control result or path;
- `definition:` — the declared definition or source.

The command asks only the missing questions, retries with the supplied answers,
and then requires a decision:

```bash
python3 cent hypothesis --resolve nematic-q-tensor-bounding-box
python3 cent hypothesis --resolve nematic-q-tensor-bounding-box \
  --answer q1=proof/q_tensor_map.md \
  --answer q2=results/q_tensor_areas.json \
  --answer q3=definitions/q_tensor.md \
  --decision keep --json
python3 cent hypothesis --resolve bresenham-quantized-carry \
  --answer q1=proof/bresenham_delta_sigma.md \
  --answer q2=results/bresenham_codes.json \
  --answer q3=negative_controls/non_feedback_raster.json \
  --decision retire --note "Proof missing; negative control failed" --json
```

Question IDs are stable for a lead (`q1`, `q2`, …). The JSON output includes
the questions, answers, next question, status and decision. An interactive run
pauses at each open question and at the keep/retire decision.

Statuses:

| Status | Meaning |
|---|---|
| `needs_input` | At least one declared need has no supplied answer |
| `ready_for_decision` | All needs have answers; no keep/retire decision yet |
| `needs_note` | A retire decision was chosen without the required reason |
| `retained` | Lead remains active at `DOESNT-KNOW`; no promotion |
| `retired` | Lead is recorded as retired with a reason |

The resolver does not verify the answers as proofs. It records them as supplied
evidence, reports `technical_validation: not performed`, and keeps
`supported_operations_changed: false`. A keep is not a mechanism card; a retire
is a recorded decision, not deletion. Save the returned JSON if a durable record
is needed. The static `LEADS` registry is not mutated by the resolver.

## Knowledge states

The layer reuses [`hypothesis_bridge.py`](../cent_compiler/hypothesis_bridge.py):

| State | Use here |
|---|---|
| `KNOWS` | Not assigned by this view |
| `THINKS_TRUE` | Requires declared simulation evidence; not assigned to an untested lead |
| `DOESNT_KNOW` | Default state for a new structural lead |
| `NEEDS` | Available for a lead with a specific unmet evidence step |
| `LANGUAGE` | Not assigned by this view |

Each lead carries machine-readable `needs`, such as `proof:`, `test:` or
`definition:`. The wheel is the existing `CentWheel`; this module does not add a
second knowledge-state system.

## Declared leads

Two review-supplied leads are retained as provenance. They are leads, not claims
of equivalence, physical feasibility or implementation support. Both were
audited against the repository on 2026-11-11. The audit produced a proof for the
Q-tensor obstruction and an exact one-tick result for Bresenham. Their
pre-admission wheel state remains `doesnt_know` and neither lead is deleted.

| Lead | Operation | Candidate structure | Pre-admission state | Recorded resolution |
|---|---|---|---|---|
| `nematic-q-tensor-bounding-box` | `bounding_box` | spatial orientation family ↔ finite-direction envelope | `doesnt_know` | `retired` — scalar Q-tensor invariants are orientation-blind, so the requested invariant-only map cannot exist ([proof](evidence/nematic-q-tensor/README.md), [record](hypothesis-resolutions/nematic-q-tensor-bounding-box.json)) |
| `bresenham-quantized-carry` | `quantized_carry` | integer error accumulation ↔ delta-sigma feedback | `doesnt_know` | `retained` (narrowed) — exact one-tick floor error-feedback equivalence; the existing two-tick target is not equivalent ([proof](evidence/bresenham/README.md), [record](hypothesis-resolutions/bresenham-quantized-carry.json)) |

The Q-tensor lead needed a Q-tensor-to-projection map, an exact corner and area
comparison, and director/normalization definitions. The audit supplies the
definition and exact comparison, but proves that the scalar invariants
`tr(Q^2)=2S^2` and `det(Q)=-S^2` are identical for different directors. No
invariant-only map to finite-direction projections exists. A full Q eigenframe
bridge is orientation-only and does not satisfy the invariant claim, so this
lead is retired. A separate orientation-only lead may be declared if wanted.

The Bresenham lead needed a state/update equivalence proof, a line-walk
reconstruction test and a non-error-feedback raster control. The one-tick floor
variant has all three: the exact induction proof, the range test over
`1 <= dx <= 32, 0 <= dy <= dx`, and a differing stateless control. The existing
two-tick nearest-level target is not equivalent because its feedback history
changes the code sequence. The lead is therefore retained only as the narrowed
one-tick variant, not as an equivalence claim about the current route.

A retirement is recorded, not erased. A keep is not a promotion. Reopening the
Q-tensor lead or widening the Bresenham lead requires new evidence for its
specific needs and a new resolution record; it does not silently reactivate the
old claim. The earlier absence-based records are preserved under
`hypothesis-resolutions/history/`.

## Structural scoring

Pre-admission cards must satisfy both:

1. a score of at least `MIN_STRUCTURAL_SCORE` (6); and
2. at least one overlap in the declared primitive chain.

The score adds declared behavior matches for primitive overlap, statefulness,
feedback, conserved quantities, encoding, nonlinearity and precision. It is a
retrieval aid, not a correctness proof.

For the current examples:

```text
bounding_box:
  pre-admission  cam-profile          overlap spatial
  lead           nematic-q-tensor...  overlap spatial

quantized_carry:
  admitted       delta-sigma...       supported_operations contains quantized_carry
  pre-admission  pll-phase-tracking   overlap accum, sum
  lead           bresenham...         overlap accum, quantize
```

## Promotion boundary

A pre-admission match becomes a production mechanism only through the existing
promotion path:

1. add or revise a declared mechanism card with its operation in
   `supported_operations`;
2. declare operation semantics and a fixed reference test;
3. add an exact probe or target adapter, with negative controls;
4. review the card and its evidence;
5. only then let `transfer_engine.retrieve` return it.

`cent hypothesis` does none of those steps automatically. It does not mutate
the card registry, the transfer candidate registry or the operation matrix.

## Limits

- A lead is not a supported operation, mechanism card, transfer candidate or
  validated target.
- The structural score is not an isomorphism, equivalence proof or error bound.
- The Q-tensor lead is retired by proof; Bresenham is retained only as a
  narrowed one-tick variant. Neither is a mechanism card, exact probe or
  validated target.
- The view is intentionally curated; add a lead only with a source and explicit
  needs. Do not turn a keyword match into a mechanism card.

## Tests

```bash
python3 tests/test_discovery.py  # 133/133, including the hypothesis surface
python3 tests/run_all.py         # 824/824 across the seventeen-suite gate
```
