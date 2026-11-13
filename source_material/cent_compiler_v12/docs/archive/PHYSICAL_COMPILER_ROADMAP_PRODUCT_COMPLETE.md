# Physical Compiler — Product Roadmap Archive

**Archived:** 2026-11-11  
**Status:** all locally actionable workstreams complete; external evidence remains blocked.

> **Archive snapshot.** The completed local product roadmap is preserved here.
> D5/D10 remain external blockers; no placeholder evidence was created. The next
> completed workstream ledger is [`../../PHYSICAL_COMPILER_ROADMAP.md`](../../PHYSICAL_COMPILER_ROADMAP.md); no forward roadmap is active.

The completed build history — including every checked item, exact test count,
route proof and external blocker — is archived at
[`docs/archive/PHYSICAL_COMPILER_ROADMAP_COMPLETED.md`](PHYSICAL_COMPILER_ROADMAP_COMPLETED.md).
This document is historical; no forward roadmap is active.

## Product goal

One user-supplied **£** should enter through a clear, guided interface and come
out as:

```text
£ relation
  -> validated target/expression
  -> typed ¢ DAG
  -> domain-independent ∆ candidates
  -> ranked ∆ proposal with explicit evidence and gaps
  -> optional exact material / netlist / verification artifacts
```

The method may be electrical, mechanical, fluidic, thermal, optical or
mixed-domain. The compiler must not privilege a domain merely because its
catalogue row appears first. It must show why a candidate was selected and
where the candidate stops.

## Current baseline

- `cent guide` documents the accepted £ syntax and the cross-domain path.
- `cent compile "<£>"` emits the ¢ DAG, enumerates ∆ candidates, ranks them and
  shows the rank-1 SPICE template or an explicit template gap.
- `cent report "<£>" --save DIR` emits the full material bundle and exact-core
  program when the relation maps.
- 37 wheels, 90 axioms, 143 cases, 336 derived spokes and 73 typed material
  contracts are loaded from declared data.
- Three exact routes are assembled: delta-sigma, log-domain √x and
  op-amp/multiplier feedback √x.
- The global axiom graph supports direct and bounded substitution derivations;
  discovery separates graph proofs, declared bridges and text-only candidates.
- The canonical eleven-suite gate passes **595/595 checks**.

## Workstream A — £ input and compile experience

- [x] Add `cent guide` with syntax, examples, output stages and troubleshooting.
- [x] Add compile-help epilog pointing to the guide.
- [x] Add a short, tested “first £” walkthrough to the README using one compute
  and one thermal example, with the domain/carrier reading spelled out.
- [x] Improve parse errors with the nearest accepted operator/function and a
  copyable example; never echo a made-up relation.
- [x] Add a `cent compile --json` payload for tooling, with the same certificate
  and gap semantics as the text path. This is an addition, not a second solver.
- [x] Add a documented `--top` guidance note: top-N is a ranking view, not a
  claim that every domain is represented in the first N.

**Acceptance:** a new user can run `cent guide`, paste a valid £, and identify
the ¢ DAG, the ranked ∆ proposal and the first explicit gap without reading
source code.

## Workstream B — domain-independent ∆ proposals

- [x] Add a cross-domain fixture set: electrical, mechanical and fluidic cases
  plus the existing thermal regression, each asserting its expected ranked
  domain and first certificate gap reason.
- [x] Ensure the proposal view names the selected domain/carrier and the reason
  for the rank: the text view prints the six-axis rationale and JSON exposes it
  per proposal.
- [x] Add the thermal-£ domain-diversity regression: the ranked top-N view
  exposes the mechanical spatial candidate, its carrier and rack-and-pinion
  components; this guards against an electrical-only compile.
- [x] Keep the SPICE-template decision structural. A missing template is a
  gap, not a reason to suppress a non-electrical ∆ candidate.
- [x] Require the structural/no-filtering template decision in output
  certificates, so a missing or contradictory `proposal_effect: none` is a
  certificate gap.
- [x] Add a documented “no fabricated device” boundary to every proposal in
  both text and JSON output, with a certificate check for its presence.

**Acceptance:** the same compiler path handles all declared domains, and a
reader can tell whether the winner is electrical for a physical reason or only
because of catalogue/cost ordering.

## Workstream C — documentation and repository

- [x] Move reference documents into `docs/` and add [`docs/README.md`](../README.md).
- [x] Add [`docs/GUIDE.md`](../GUIDE.md) as the user-facing input guide.
- [x] Archive the completed roadmap under `docs/archive/`.
- [x] Add a link checker for local Markdown links and run it in the gate.
- [x] Keep the package-layout, test-count and module-count claims checked
  against the repository by the canonical gate.
- [x] Add a short contribution map: where to add a wheel, a contract, a route,
  a substrate row and a test, including the material-contract and test-count
  invariants.

**Acceptance:** a reader can start at `README.md`, reach every document from
`docs/README.md`, and never find a stale root-file link.

## Workstream D — external evidence (blocked)

These remain outside the current local code:

- **D5 fabricated-device evidence:** requires a real fabricated device.
- **D10 Leech/Griess/Lean/Viazovska:** requires declared 24-D generator/weight
  data, a multiplication tensor, a Lean build/elaborator and a codebook
  objective.

They stay explicit gaps. No placeholder data or theorem label should be
converted into a pass.

## Definition of done for the product goal

A £ input is complete when:

1. the guide makes the required syntax unambiguous;
2. the parser returns either a typed ¢ DAG or a precise, actionable error;
3. ∆ candidates are enumerated without an electrical-only filter;
4. the proposed candidate names its domain, carrier, cost and evidence;
5. the output states the first missing material, netlist or measurement step;
6. the same result is reproducible in a focused exact test.

The external evidence work is explicitly outside this local definition.
