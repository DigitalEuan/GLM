# `glm_universal/runtime` — the interactive geometric language runtime

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

Three modules turn the substrate, the carriers and the reasoning kernel
into something a person can hold a conversation with:

```
runtime/
├── parser.py      deterministic semantic query parser (17 answering kinds + `unknown`)
├── session.py     GeometricSession: one solver per kind, registers, history
├── tct_engine.py  Three Column Thinking trace generation + verification
└── __init__.py    public API exports
```

## The registers

`session.DOMAINS` is the authoritative list: **6 registers**, loaded lazily
and cached, holding 1,040 carriers between them — physics 726, chemistry 118,
molecules 51, mathematics 22, lexicon 95, spatial 28.  `molecules` is the
newest: 51 molecules and ions, every coordinate derived from the element
register rather than tabulated.  The counts here are the ones
[`../../FIGURES.md`](../../FIGURES.md) recomputes under *Registers*.

## The query kinds

`parser.KINDS` is the authoritative list: **18 query kinds** — seventeen
answering kinds plus `unknown`, the honest fallback.

| Kind | Surface | What it does | Wired in |
|---|---|---|---|
| `verify` | `force = mass * acceleration` | multi-plane equation audit | v0.4.0 |
| `analogy` | `A : B :: C : ?` | proportional analogy in a named subspace | v0.4.0 |
| `describe` | `describe carbon` | the dossier of one carrier (with lattice projection) | v0.4.0, augmented v0.5.3 |
| `nearest` | `nearest 5 to pressure` | ranking under the Griess metric | v0.4.0 |
| `product` | `sakuma product` | the Norton-Sakuma 2A algebra | v0.4.0 |
| `cluster` | `cluster C, N, O into 2` | exact agglomerative clustering (`linkage = single \| complete`) | v0.4.0 |
| `spatial` | `mog grid of oxygen` | the MOG presentation of a carrier | v0.4.0 |
| `project` | `project carbon oxygen` | walk all five dimension-projection layers | v0.5.3 |
| `trilinear` | `trilinear 127 432 463` | the invariant form ⟨A·B, C⟩ | v0.5.3 |
| `coherence` | `coherence carbon` | the five-shell NRCI breakdown | v0.5.3 |
| `angle` | `angle carbon oxygen` | exact cosine comparison | v0.5.4 |
| `report` | `report <subject>` | on-demand recomputation of a body of facts — see below | v0.5.4 |
| `task` | `task grid` | a worked end-to-end task: `grid`, `physics`, `concepts` | v0.8.0 |
| `pi_groups` | `pi groups force, mass, acceleration, length, time` | Buckingham-Pi: the dimensionless groups of a set of quantities, from the rational nullspace of the EXT10 exponent matrix | v1.0.0 |
| `meaning` | `meaning of water`, `relate energy torque` | what a notation denotes, its 24-coordinate meaning carrier and its round trip; with two terms, every relation derivable between the two meanings, each re-checked from the meanings alone. A term with no determinate referent is refused with its reason | v1.1.0 |
| `real` | `approximate sqrt(2) to 20 places`, `approximate (1+sqrt(5))/2 to 12 places`, `approximate exp(1) to 20 places` | reads the expression as a *process* over `reasoning/real_expr.py` — which since v1.2.0 also reads `exp`, `log`, `sin`, `cos`, `tan` and a non-integer exponent through `reasoning/transcendental.py` — and asks it for enough precision to settle the requested decimal places. No float is constructed, and the answer says plainly that no carrier holds the value: what the machine holds is the rule that converges to it | v1.2.0 |
| `compare` | `is pi less than 355/113`, `compare sqrt(2) and 1.5`, `which is bigger e or pi`, `is 2^pi less than 9` | reads both sides as processes and refines them along the ladder `2⁻⁸, 2⁻¹⁶, …, 2⁻²⁵⁶` until the intervals come apart, reporting the precision that settled it. Inequality is decided; two sides that never separate come back "not distinguished", because equality of processes is not decidable and the machine does not claim it | v1.2.0 |
| `unknown` | (fallback) | diagnostics + suggestions | v0.4.0 |

## The `report` subjects

`session.REPORT_SUBJECTS` is the authoritative list: **25 report subjects**.
Every subject recomputes its facts on demand and has a Three Column Thinking
template that reproduces them in a fresh interpreter.

| Subject | What it recomputes |
|---|---|
| `relations` | the 222 scalar + 71 tensor relation audit, with facet attribution |
| `leech distribution` | the Λ/2Λ class census (98,280 type-2 classes) |
| `theta` | the theta-series coefficients of Λ₂₄: 1, 0, 196560, 16773120, 398034000, 4629381120 |
| `subalgebra` | the Norton-Sakuma 2A subalgebra: closed, commutative, nowhere associative |
| `information loss` | what each layer loses, where the boundaries are, whether addition descends (aliases: `report loss`, `report boundaries`) |
| `golay decoding` | the coset table and complete decoding, including the weight-5 miscorrection theorem |
| `leech construction` | the Construction A/B/C ladder, 48 / 98,256 / 196,560 |
| `facets` | the six-facet partition of the 24 coordinates: strictly linear, orthogonal, no facet redundant |
| `monster stack` | the ten-plane 2-adic Monster stack: 5 planes compose strictly, 8 with pair repair |
| `multiresolution` | the F₂⁴ ↔ GF(4) × Z₄ fibration and the cross-level products |
| `migration` | the legacy → canonical Golay frame bridge: the two codes share 8 of 4,096 codewords, and the bridge is a weight- and distance-preserving isometry |
| `state migration` | the literal migration of the stored state: 4,282 concepts and 4,014 edges into the canonical frame, 398 carriers minted |
| `concept store` | the indexed payload — 4,680 concepts, 4,014 edges — with labelled paths and Hamming neighbourhoods |
| `fusion` | the Ising fusion layer: adjoint action, eigenspaces, both Miyamoto involutions |
| `benchmarks` | every suite score against its published baseline, with the findings |
| `infinite values` | the whole value layer recomputed: `sqrt(2)`, `pi`, `e` and `phi` to 20 places, the tower's stand-ins and the level that exposes each, the `1/N` law at `N = 10, 100, 1000`, the 24-D carrier on a reachable target (deviation 0) and on the ramp target (deviation `19/300`, accumulator `311/24`, separating certificate with gap `13/5760`), and the undecidability of equality |
| `capabilities` | the 33 capability probes of `glm_universal/capabilities/`, run for real: how many hold, how many break, and the exact place each break stops. A probe whose verdict differs from its declared expectation is reported as a *surprise* |
| `superposition` | the six-fold tie at a deep hole of the Golay code, held as one value: the sextet partition, the F₂ bundle that collapses to all-ones against the rational bundle that is injective and invertible, contextual collapse (`collapsed` / `superposed` / `refuted`, never broken by member order), and the separating certificate behind alphabet expansion (aliases: `report ambiguity`, `report tie`, `report sextet`, `report bundling`, `report parallel hypotheses`, `report list decoding`) |
| `semantics` | the audit of the inherited concept graph — how many of its 4,282 concepts denote anything, how its 4,015 edges classify, what its stored carriers turn out to measure — and the grounded graph that replaces it (aliases: `report meaning`, `report grounding`) |
| `analogies` | the named relation models re-solved case by case: which model recognised the relation, what it answered, and whether the mathematics of the case agrees. A refusal is a row like any other (aliases: `report analogy`, `report analogy models`, `report relation models`, `report proportional analogy`) |
| `transform decoder` | the 4,096 Golay coset costs as one Walsh–Hadamard transform, and the tier at which the constant-time lookup can prove its own answer (aliases: `report fwht`, `report walsh`, `report hadamard`, `report transform`, `report o(1) lookup`, `report certificate`, `report llvq`, `report soft decoding`) |
| `deep holes` | classification of a carrier by its nearest Niemeier type as a *process* — walk to a hole, climb to the covering radius, read the vertices off the trajectory, certify the reading — with nothing stored but a derived catalogue (aliases: `report deep hole`, `report holes`, `report niemeier`, `report hole census`, `report covering radius`, `report voronoi`) |
| `units` | every quantity states what it is twice, as a unit string and as EXT10 exponents; this parses the first and checks it against the second, and prices the SI reading of the steradian (aliases: `report unit parser`, `report steradian`, `report unit audit`, `report dimensional audit`) |
| `molecules` | the multi-carrier register: 51 molecules and ions held twice, as the faithful bundle of element carriers with multiplicities and as one composite summary carrier, with the losslessness of each checked rather than asserted (aliases: `report molecule`, `report formulae`, `report multi-carrier`, `report compounds`) |
| `chemistry coverage` | how sparse the element register is (1,257 of 1,652 cells filled) and the three honest repairs — derive, estimate with the error measured, cross-check without merging — each run and labelled with what it is (aliases: `report coverage`, `report element coverage`, `report sparsity`, `report covalent radius`) |

## The session API

```python
from glm_universal.runtime import GeometricSession

sess = GeometricSession()
sol = sess.ask("nearest 5 to pressure")     # parse, then solve
sol2 = sess.solve(sol.query, raw="nearest 3 to pressure")
```

`ask(text)` parses and delegates to `solve(query, raw=None)`.  `solve`
takes an already-parsed `Query`, which is what makes it possible to edit
a query object and re-run it without going back through the surface
string.  Both record an `InferenceRecord` in `sess.history`, whether or
not the query succeeded.

## The `GLM.py` CLI

The CLI entry point lives at the **repo root** (`../../GLM.py`), not in
this folder.  It is a thin shell over this package.  See the root
README's "Quick Start" for usage.

## Design invariants

- **No float anywhere**, in the runtime sources *or* in the scripts
  they generate.  `script_is_exact` checks generated source by AST.
- **No RNG and no wall clock.** A trace must be byte-identical between
  runs.
- **XOR only where it is addition.** On the F₂ module Λ/2Λ.
- **Failures are results.** An unsolved query returns a Solution with
  `ok=False` and is recorded in the history.
