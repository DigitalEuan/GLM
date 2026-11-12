# Contribution Map

This is the repository extension map. It names the file that owns each kind of
claim, the files that consume it, and the test that must move with it.

The rule is the same everywhere: **declare what is known, name the gap, and do
not invent a measurement, theorem, dimension or route.** A checked box or a
green test is not a fabricated-device claim.

## Before you edit

Start with:

```bash
python3 tests/test_ui.py       # fast console, JSON and docs-link checks
python3 tests/run_all.py       # canonical seventeen-suite gate
```

Read the relevant reference first:

- [`CENT_FRAMEWORK.md`](CENT_FRAMEWORK.md) — compiler architecture.
- [`MATERIAL_CONTRACTS.md`](MATERIAL_CONTRACTS.md) — declared material rows.
- [`GUIDE.md`](GUIDE.md) — £ input and the ¢ → ∆ path.
- [`../PHYSICAL_COMPILER_ROADMAP.md`](../PHYSICAL_COMPILER_ROADMAP.md) — what
  is complete and what is explicitly external.

## 1. Add a wheel

The JSON files are the current data source. The loader in
[`../cent_compiler/wheels.py`](../cent_compiler/wheels.py) reads
[`../wheels/index.json`](../wheels/index.json) first, then each wheel file.

1. Add `wheels/W42.json` (use [`W1.json`](../wheels/W1.json) as the shape).
   Required top-level fields are `id`, `title`, `axioms`, `cases`, `quantities`
   and `dimensions`. Wheel-level `junctions` and `non_identities` are the
   browser-facing mirror; the graph loader reads the declared junction table in
   `wheels/index.json`.
2. A case carries `id`, `equation`, `expected_dimensional`,
   `expected_derivable`, `physical_status`, `expected_dimensional_explicit` and
   `note`. Use `negative_control` for a deliberately false equation; never
   change an expected flag merely to make it pass.
3. Add the wheel metadata and any declared junctions or non-identities to
   `wheels/index.json`. Update `total_wheels`, `total_axioms` and
   `total_cases`; the derived spoke count changes with the axioms.
4. Run the wheel/discovery checks. `tests/test_discovery.py` includes the
   declared-case reconciliation and the graph-spoke regression; the browser
   wheel view is covered by `tests/test_webui.py`.
5. If the counts changed, update the wheel/axiom/case/spoke numbers in the
   README and the relevant reference docs.

Do **not** run `tests/extract_wheels.py` or `tests/generate_new_wheels.py` just
to add one wheel: those are historical bulk generators and can rewrite unrelated
wheel files. The checked-in JSON is the source of truth.

## 2. Add a contract

There are two distinct contract layers:

- **Exact-core primitive contract** — [`../cent_compiler/vocabulary.py`](../cent_compiler/vocabulary.py).
  This defines primitive kind, ports, parameters, state and declared domain.
  Add or change one only when the exact evaluator and grammar also change.
- **Declared material contract** — [`../cent_compiler/material_contracts.py`](../cent_compiler/material_contracts.py).
  This types the ports, parameters, operating range and failure modes of an
  `EXPANSIONS` or `DELTA_SUBSTRATE` row.

For a material contract:

1. If the primitive already has an interface in `_INTERFACES`, its row resolves
   automatically through `row.contract`; do not create a parallel row format.
2. If it is a new primitive, add a `_INTERFACES` entry with typed ports,
   parameters, an operating range and failure modes. The fallback interface is
   not a substitute for a declared interface.
3. Keep ranges qualitative unless a measured/declared value actually exists.
   Missing characterisation belongs in `operating_range` or `failure_modes`.
4. Add the row in the substrate table (next section). The material test checks
   that **every** declared row resolves through a `cent-material-contract/1`
   record with matching primitive, component, law and domain.

## 3. Add a substrate row

Choose the table that matches the claim:

- Composite expansion or a primitive that expands into a subgraph:
  [`../cent_compiler/substrate_library.py`](../cent_compiler/substrate_library.py),
  `EXPANSIONS`.
- Direct atomic implementation:
  [`../cent_compiler/pattern_matcher.py`](../cent_compiler/pattern_matcher.py),
  `DELTA_SUBSTRATE`.

For an `Expansion`, supply `primitive`, `name`, `expands_to`, domain,
component, carrier, delta-sigma flag and description. For a
`DeltaImplementation`, supply primitive, domain, component, law, carrier and
notes. A new component also needs a declared cost in
[`../cent_compiler/cost_function.py`](../cent_compiler/cost_function.py) and,
if its domain cannot be inferred from the existing keywords, a deliberate
domain mapping. Do not rely on the generic cost fallback for a new material.

Verify both the contract and the ranking:

```bash
python3 tests/test_discovery.py   # rows, dimensions, contracts, discovery
python3 tests/test_ui.py          # compile ranking and domain proposal
```

A missing SPICE template is allowed and must stay an explicit gap. It is not a
reason to suppress a non-electrical candidate.

## 4. Add a route

Routes live in [`../cent_compiler/assembly.py`](../cent_compiler/assembly.py).
The existing `delta_sigma_route`, `log_domain_sqrt_route` and
`opamp_multiplier_sqrt_route` factories are the pattern.

A route needs:

- typed component contracts and declared port names;
- an exact program, or an explicit declaration that no exact program exists;
- deterministic `simulate()` behaviour and an `as_dict()` payload under
  `cent-route/1`;
- a topology audit through `audit_route_topology`;
- a typed-graph lowering when the route is intended for `cent graph`.

Wire it into the CLI route choices only after the route can be assembled and
audited. Add declared device/design/physical/dynamics evidence only when those
layers genuinely exist; otherwise leave the route's gaps visible. The focused
checks are `tests/test_assembly.py`, `tests/test_binding.py`,
`tests/test_physical.py`, `tests/test_fabrication.py` and
`tests/test_dynamics.py`, as applicable.

## 5. Add a test

Tests use the small harness in each `tests/test_*.py` file:

```python
@check("group", "what is being proved")
def _():
    expect(condition, "the exact reason the check failed")
```

Add the check to the suite that owns the behaviour. If it needs a new suite,
add the file to `SUITES` in [`../tests/run_all.py`](../tests/run_all.py) and
update the gate wording and counts; otherwise update that suite's count in the
README. Do not weaken an assertion or change a declared expectation just to make
a suite pass.

The canonical gate is:

```bash
python3 tests/run_all.py
```

Every test count in the README and docs is the sum of the suite summaries.
`tests/run_all.py` now checks the README package tree, the total test claim,
the `test_ui` row and the Python-module count against the repository. The local
Markdown link check is already part of `tests/test_ui.py`.

## Review checklist

- [ ] The claim has a source row or an explicit gap; no invented value.
- [ ] A material row resolves through `material_contract`.
- [ ] Cost and domain inference are deliberate for a new component.
- [ ] A route either evaluates exactly or reports where it stops.
- [ ] A focused test names the expected domain, gap or failure.
- [ ] README/docs counts are updated only after the suite passes.
- [ ] The proposal is described as a proposal, not a fabricated device.

The externally blocked work is listed in the
[forward roadmap](../PHYSICAL_COMPILER_ROADMAP.md); do not turn those gaps into
placeholders to make the map look complete.
