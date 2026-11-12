# Operation × method matrix

`cent matrix` is the operation-first view over the declared compiler evidence.
It answers “what methods are declared for this operation?” without promoting a
structural netlist template, a dimensional bridge or a text match into an exact
physical route.

## Command

```bash
python3 cent matrix
python3 cent matrix --operation mult
python3 cent matrix --operation sqrt --json
```

The default is a human-readable report. `--json` emits the full
`cent-operation-matrix/1` payload with its output certificate.

## Evidence classes

Every row names exactly one class:

| Class | Meaning | What it is not |
|---|---|---|
| `exact-route` | An actual route constructor with a typed graph and exact simulation or solve | Not a fabricated or measured device |
| `exact-algorithm` | A declared exact computational method over a finite domain, with an exact probe and no physical-route claim | Not a physical route or an unrestricted global optimum |
| `structural-template` | A declared SPICE topology envelope | Not an assembled route |
| `declared-bridge` | A declared port/quantity mapping with a law, such as W24 | Not an axiom proof or a route |
| `declared-analogy` | A declared cross-domain analogy with source wheel laws and an exact application probe | Not a global proof, physical device or fabrication netlist |
| `inherited-wheel-candidate` | A text match inherited from the wheel material | Not graph grounding |
| `gap` | No declared method for the operation | Not silently filled |

Rows also carry:

- `operation` — the ¢ operation or route operation;
- `role` — `compute`, `carry` or `grounding`;
- `domain` and `carrier` — taken from the method, or explicitly
  `not declared`;
- `source` and `route` — the constructor, template table or wheel evidence;
- `mechanism` — a seeded mechanism id when an explicit source-to-card mapping is
  declared, otherwise `null`;
- `first_gap` — the first missing physical model or evidence step.

Compute, carry and grounding rows are rendered in separate groups. Delta-sigma
therefore appears only as a carrier; it is never presented as a compute
algorithm.

## Mechanism links

Rows link to the seeded mechanism registry only where the source-to-card mapping
is explicit:

| Evidence | Route | Mechanism |
|---|---|---|
| `exact-route` | `sum-kcl` | `kcl-conservation` |
| `exact-route` | `sum-fluid` | `fluid-continuity` |
| `exact-route` | `sum-opamp` | `opamp-summing` |
| `exact-route` | `sqrt-log-domain` | `log-domain-sqrt` |
| `exact-route` | `delta-sigma-first-order` | `delta-sigma-error-feedback` |
| `declared-bridge` | `W24` | `log-domain-sqrt` |

A linked row still keeps its own evidence class, domain, carrier and first gap.
Structural templates, inherited wheel candidates, declared analogies and gap rows
remain `null`; text matching is never promoted into a mechanism link. The
op-amp square-root route is also `null` because no seeded card covers that
operation; the `opamp-summing` card covers only `sum` and `difference`.

## Operation-level discovery

The same operation wording is available through `cent discover`, not only the
matrix command:

```bash
python3 cent discover "how do I multiply two signals"
python3 cent discover "compute a ratio"
python3 cent discover "exponentiate a signal"
python3 cent discover "take the logarithm of a signal"
python3 cent discover "sum two signals"
```

These queries resolve to `mult`, `div`, `exp`, `log` and `sum` respectively.
Discovery stays scoped to the requested exact contract; the matrix remains the
place to compare all declared evidence classes side by side.

## Current coverage

The matrix currently covers `sum`, `difference`, `neg`, `mult`, `div`, `exp`,
`log`, `sqrt`, `sat`, `packing`, `bounding_box` and `delta_sigma_modulator`.
It records:

- the KCL sum and difference routes;
- the independent fluid pipe-junction sum/difference route;
- the independent op-amp summing/difference route;
- the log-domain and op-amp feedback square-root routes;
- the first-order delta-sigma carry route;
- structural templates for multiplication, division, exponential, logarithm,
  saturation and the declared square-root/sum topologies;
- the W36/W37 pressure-settling packing analogy, with an exact fixed-container
  probe;
- the W24 declared bridge and inherited text-only wheel candidates;
- the `bounding_box` row built from the exact finite-direction orientation
  envelope; it is an exact algorithm over a declared direction set, not a
  physical route;
- explicit gaps where no declared method exists.

Exact route IDs come from the constructors (`sum-kcl`, `sum-fluid`, `sum-opamp`,
`sqrt-log-domain`, `sqrt-opamp-multiplier`, `delta-sigma-first-order`). The
envelope's route identifier is `orientation-envelope`, but its evidence class
is `exact-algorithm`; it is never counted as an assembled physical route. A
template name such as `multiplier` remains a template name, not a route ID.

## Limits

- The matrix is a catalogue of declared evidence, not a proof of physical
  completeness.
- It does not add device values, component models, fabrication geometry or
  measured results.
- `structural-template` and `inherited-wheel-candidate` rows are deliberately
  weaker than `exact-route`.
- `exact-algorithm` is exact over its declared finite domain, not a global
  optimum over every real orientation. Its pipeline is a structural
  decomposition, not a target adapter.
- `declared-bridge` rows ground dimensions and laws; they do not compose an
  operation. `declared-analogy` rows expose a declared cross-domain mechanism,
  but the packing row still has no optimality certificate.
- Missing rows stay gaps, including the unresolved `tanh` parameter gap recorded
  by the assembly fixture matrix.

## Leech navigation boundary

The 24-bit class isomorphism in
[`LEECH_ISOMORPHISM.md`](LEECH_ISOMORPHISM.md) is now compiler-audited, but it
is **not an operation-method row**. `cent leech-class` re-derives 63,257 class
words of rank 24 from a declared row-HNF basis and the exported move corpus. It
maps `Λ/2Λ` to `F₂²⁴` and composes class words by XOR. It does not compute a
`¢` operation, carry a signal, or define a physical method.

| Navigation layer | Current evidence | Matrix status |
|---|---|---|
| Class word and XOR composition | `cent leech-class` re-derives the class words and sampled XOR composition | Not a row; no compute/carry operation |
| Lattice metric and quadratic form | The isomorphism is a group isomorphism, not an isometry | Gap |
| Griess algebra product | No declared multiplication tensor | Gap |
| Monster action | No declared representation, generators or action table | Gap |
| Lean / Viazovska certificate | No imported Lean build or codebook objective | Gap |

Adding this as `declared-bridge` would overload a class reserved for declared
port/quantity mappings. Adding it as `exact-route` or `compute` would claim an
operation method that does not exist. The matrix therefore keeps it outside the
rows until a compiler-side navigation capability exists.

### Admission sequence

1. [done] Add a declared class-word audit over a supplied `leech_basis()` and
   move set, and re-derive composition and class counts in `cent`.
2. Declare the lattice metric/quadratic form separately; do not transplant it
   from the 24-bit group coordinate.
3. Add a Griess multiplication tensor and an exact product check.
4. Add a Monster representation/generator set and an action check.
5. Only then add a distinct navigation/grounding row, with its own evidence
   class rather than reusing `declared-bridge`.

The compiler-side audit is complete; the later steps remain blocked on declared
mathematical structure.

## Tests

```bash
python3 tests/test_discovery.py  # 133/133, including matrix evidence and CLI
python3 tests/run_all.py         # 824/824 across the seventeen-suite gate
```
