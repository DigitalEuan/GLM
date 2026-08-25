# Master plan: wiring status

This document tracks the plan to fully wire the Geometric Language Machine,
eliminate the architectural simplifications, and implement multi-resolution
addressing. Each item says what was built, where it lives, and how to see it
recompute itself.

Everything below is reachable from the package's public API and from the query
runtime — **18 query kinds**, **25 report subjects** and **6 registers** — is
covered by the test suite (1,677 tests across 37 test files, 8,851 subtests),
and — where it is a report or a task — has a generated column-3 script that
recomputes the claim in a **fresh interpreter** and fails if anything differs.

No count in this document is typed by hand twice: every one of them is
recomputed by `glm_universal/figures.py` into
[`overlay/FIGURES.md`](overlay/FIGURES.md), and
`tests/test_figures.py` fails if a document drifts from it.

```bash
cd overlay
PYTHONPATH=. python3 -m pytest glm_universal/tests -q
PYTHONPATH=. python3 GLM.py -q "report migration"          -c 1
PYTHONPATH=. python3 GLM.py -q "report leech construction" -c 1
PYTHONPATH=. python3 GLM.py -q "task grid"                 -c 1
PYTHONPATH=. python3 GLM.py -q "report infinite values"    -c 1
PYTHONPATH=. python3 GLM.py -q "report capabilities"       -c 1
PYTHONPATH=. python3 GLM.py -q "report superposition"      -c 1
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8
```

---

## Phase 1 — core migration and substrate unification

### 1.1 Retire the legacy decoder — **done**

`glm_universal/substrate/golay_decode.py` replaced the package's `snap`
(scan the 4,096 codewords, keep the first nearest) with complete syndrome
decoding driven by the coset-leader table.

| Fact | Value | Recomputed by |
|---|---|---|
| cosets | 4,096 | `coset_census()` |
| coset-leader distribution | `1 + 24 + 276 + 2024 + 1771` | `coset_census()` |
| leaders below the packing radius | exactly 1 | `coset_census()` |
| leaders at the covering radius | a sextet of 6 | `coset_census()` |
| ties broken silently | **0** | `decoder_comparison_report()` |

Every legacy call site now uses it: `reasoning/analogy.nearest_golay_codeword`,
`data_objects/base.DataObject.golay_alignment` and
`reasoning/dimension_layers._substrate_perceive`, each of which now carries a
`decode_status` and a `decode_guaranteed` flag instead of an unqualified
answer. `nearest_codeword` is `None` when the reading is ambiguous — a tie is
never broken behind the caller's back.

**Weight-5 miscorrection is a theorem, not a bug.** The octads form a Steiner
system `S(5, 8, 24)`, verified here over all 42,504 five-subsets, so a weight-5
error is the complement inside a unique octad of a weight-3 error: the received
word sits at distance 3 from the *wrong* codeword and 5 from the right one, and
*any* nearest-codeword rule is unique, confident and wrong. The remedy is a
declared channel radius, which `decode_complete` supplies as `guaranteed`, and
not a better decoder. See `weight5_miscorrection_report()`.

Query: `report golay decoding`.

### 1.2 The `LEGACY_TO_CORE` bridge and bulk migration — **machinery done, data pending**

`glm_universal/substrate/isomorphism.py` implements the permutation

```
LEGACY_TO_CORE = (0,1,2,3,4,5,7,16,8,19,22,9,13,12,10,18,14,15,21,6,11,20,23,17)
```

as the only sanctioned bridge between the project's legacy Golay frame and the
package's canonical one, and reconstructs the legacy frame from it so that the
whole path can be tested here and now:

* the two codes are **different** — they share exactly **8** of their 4,096
  codewords, the number the project's own Step-5 note records — while their
  weight distributions agree, so the image is an equivalent `[24, 12, 8]` code;
* the bridge is consequently **not an automorphism** of the canonical code, and
  a witness codeword is returned rather than the fact being asserted;
* it **is an isometry**: weight-preserving on all 4,096 codewords and
  distance-preserving, which is exactly the property that lets it be wrapped
  around a decoder. A general linear isomorphism of the two codes exists too
  and scrambles distance; it may not be wrapped around a decoder, and this
  module does not offer one.
* `decode_legacy` therefore routes a legacy word through the canonical frame,
  decodes it with the audited decoder, and brings the answer back. Against
  snapping inside the legacy frame, **every silently broken tie becomes an
  explicit `"ambiguous"`**, and everything inside the packing radius is
  recovered exactly.

Bulk migration is `migrate_dataset(concepts, edges, hexcolours)`, driven by a
`MigrationSpec` that names which fields hold masks, carriers, coordinate
index sets or hexcolour addresses. Everything else — identifiers, labels,
edge endpoints, provenance — is copied through untouched. The call returns the
migrated tables together with its own checks: round trip under the inverse
permutation, weight preservation, mask distinctness and referential integrity
of the edge endpoints.

**What is still outstanding.** The concept, CRG-edge and hexcolour tables
themselves (4,282 concepts, 4,015 edges, 66 persistent addresses) are not part
of this repository, and neither is the `glm_core` tree. The migration is
therefore *exercised* rather than *applied*: `sample_dataset()` builds a
dataset of the same shape from the package's own octads and `migration_report()`
runs the whole path over it. When the real tables arrive, migrating them is one
call to `migrate_dataset` with the right `MigrationSpec` field names, and the
same checks apply unchanged.

Query: `report migration`.

Machine-checked counterpart: `RequestProject/GLM/Permutation.lean` proves that a
coordinate permutation preserves Hamming distance and weight, that
nearest-codeword decoding commutes with it in both directions, and that minimum
distance 8 transports across the migration.

---

## Phase 2 — algebra completion and simplification removal

### 2.1 The full Leech lattice — **done**

`glm_universal/substrate/leech_construct.py` builds the construction ladder and
measures each rung:

| Level | Conditions | Minimum norm² | Kissing |
|---|---|---|---|
| A | Golay mod 2 | 16 | **48** |
| B | + Golay mod 4 and the coordinate sum ≡ 0 mod 8 | 32 | 98,256 |
| C | + the odd coset | 32 | **196,560** |

with the level-C minimal vectors coming out in the three classical shapes,
`1104 + 97152 + 98304 = 196560`.

Each condition is shown to be **necessary**, by exhibiting what breaks without
it: dropping the mod-4 Golay condition admits `(2, −2, 0²²)` and the minimum
falls to 8 (552 vectors); dropping the mod-8 sum readmits `±4·e_i` and the
minimum falls to 16 with kissing 48 — which is precisely Construction A, the
simplification that was in place. The multi-mod sieve (`mod_profile`,
`mod_sieve`) is the membership test written as the three residue conditions it
is, mod 2, mod 4 and mod 8.

The ladder is checked against the package's own Leech predicate on 721 sampled
vectors, with zero disagreements, so it is the same lattice the rest of the
system uses and not a parallel construction.

Query: `report leech construction`.

### 2.2 The 10-plane digit stack and the exact 2A product — **done**

`glm_universal/reasoning/monster_stack.py` types a carrier as ten planes of
`Λ / 2Λ`, repairs each plane to the nearest type-2 class (exhaustively over all
98,280, with exact lattice distance breaking Hamming ties and no tie broken
silently), and composes plane-wise with the **exact Norton–Sakuma product**

```
a · b = (1/8) (a + b − a_ρ)
```

replacing the associative XOR shortcut. What the shortcut cost is measured
rather than asserted:

* the XOR of two labels is the *third axis label* only — one of the product's
  three terms. It discards the other two and the coefficient `−1/8` on the one
  it keeps, changing the norm from `11/256` to `1`;
* on the witness triple of classes `127, 432, 463` the algebra gives
  `(a·b)·c = −3/32·a₄₆₃` against `a·(b·c) = −3/32·a₁₂₇`: **not associative**,
  while the XOR shortcut is. A pipeline that composed addresses by XOR was
  working in a quotient where the Monster's product does not live.

Coverage is reported honestly: 5 of 10 planes compose strictly, 8 of 10 with
pair-aware repair, and every plane that has no product says why.

Query: `report monster stack`. Machine-checked counterpart:
`RequestProject/GLM/Sakuma.lean`.

### 2.3 The six-facet decomposition — **done**

`glm_universal/reasoning/facets.py` cuts the 24 coordinates into Dimension
(0–16), Scale (17), Tensor Rank (18), Context (19–21), Nominal Kind (22) and
Domain (23), as **strict linear projections**: additive, homogeneous,
idempotent, mutually orthogonal and complete, all checked on sampled carriers
rather than asserted. Squared distance therefore splits exactly across the
facets, which is what makes a facet attribution of a discrepancy add back up to
the whole.

The decomposition also measures its own cost. For each facet the index
`[π_F(Λ) : Λ ∩ span(F)]` is computed exactly: **512** for Dimension, **32** for
Context and **8** for each one-dimensional facet. No facet is
lattice-autonomous — reading one facet always loses lattice information, and
the index says how much.

Query: `report facets`. Machine-checked counterpart:
`RequestProject/GLM/Facets.lean`.

---

## Directive — multi-resolution Leech addressing

`glm_universal/reasoning/multires.py` addresses the same 24 coordinates at two
resolutions and compares them.

**Bit level.** A MOG column's `F₂⁴` value maps to `GF(4) × Z₄` fibre
coordinates. The map is a bijection with round trip, verified over all 16
values; its kernel `{0, 1, 14, 15}` is elementary abelian, *not* cyclic of
order 4, so the `Z₄` coordinate indexes a fibre as a set of residues — that is
reported, not glossed. Each column carries a rank-4 local Leech sub-lattice of
index **64** in its projection, so a bit-level reading is a strictly coarser
view.

**Grid level.** A whole 2D grid is carried into the 24 coordinates — losslessly
in *frame* mode for grids up to `4 × 6`, and by 24 exact statistics in *census*
mode for anything larger — and read as a ten-plane Monster address.

**Cross level.** `cross_inner` and `cross_tensor` take the Griess inner product
and the rank-one tensor of a bit-level axis against a grid-level one, and the
contraction of the tensor is the inner product. The scale-invariance sweep then
finds the boundary between the two levels: **the grid signature is invariant
under rescaling and reflection; the census and the Monster address are not.**
A collision witness exhibits the loss directly — `[[0,1],[1,0]]` and
`[[1,0],[0,1]]` share a census, and their frame carriers differ.

Query: `report multiresolution`.

---

## A task for the system

`glm_universal/reasoning/tasks.py` runs two problems through the *whole*
pipeline rather than through one mechanism.

**`task grid` — an ARC-style puzzle.** Three training pairs, five candidate
rules, filtered at three resolutions. The signature prunes nothing (it is blind
to reflection and rotation, as it should be); plane 0 of the Monster address
cuts the field from five to one; the full ten-plane address confirms it. The
rule is `rotate180`, it reproduces every training pair, and the prediction for
the held-out grid changes the address while preserving the signature — the two
resolutions disagree exactly where the theory says they must.

**`task physics` — energy against torque.** SI7 says they are the same quantity
(`L² M T⁻²`); EXT10 separates them. The verifier confirms the split between
scalar and full tensor semantics; the layer stack is escalated and the facet
decomposition attributes the difference to the Dimension, Tensor Rank and
Nominal Kind facets at `1/8` each; the ten-plane addresses first differ at plane
0, and the difference mask is read by the complete Golay decoder rather than
snapped.

---

## Runtime surface added

| Query | Wires |
|---|---|
| `report golay decoding` | `substrate/golay_decode` |
| `report migration` | `substrate/isomorphism` |
| `report leech construction` | `substrate/leech_construct` |
| `report facets` | `reasoning/facets` |
| `report monster stack` | `reasoning/monster_stack` |
| `report multiresolution` | `reasoning/multires` |
| `task grid`, `task physics` | `reasoning/tasks` |
| `report infinite values` | `reasoning/exact_real` |
| `report capabilities` | `capabilities/` |
| `report semantics` | `semantics/audit`, `semantics/graph` |
| `meaning of <term>`, `relate <a> <b>` | `semantics/reference`, `semantics/relations` |
| `approximate <expr> to <n> places` | `reasoning/real_expr` |
| `is <a> less than <b>`, `compare <a> and <b>`, `which is bigger <a> or <b>` | `reasoning/real_expr`, `reasoning/exact_real` |
| `report analogies` | `reasoning/analogy_models` |
| `report transform decoder` | `reasoning/fwht_decode` |
| `report deep holes` | `reasoning/deep_holes`, `reasoning/voronoi_walk` |
| `report units` | `reasoning/units` |
| `report molecules` | `data_objects/molecules` |
| `report chemistry coverage` | `reasoning/element_coverage` |

`task` is a new query kind, with its own parse branch and solver. Each subject
and task has a Three Column Thinking template, so the answer is stated in
language, in exact mathematics, and as a script that reproves it from the public
API in a separate process.

---

## Phase 3 — the value layer, and the map of where the machine stops

The phases above make every *mechanism* reachable. This one asks what happens
to a *value* the mechanisms cannot hold, and then asks the machine to say for
itself where it stops. The write-up is
[`INFINITE_VALUES_STUDY.md`](INFINITE_VALUES_STUDY.md).

### 3.1 Reals as processes — **done**

`glm_universal/reasoning/exact_real.py`. A carrier is 24 exact rationals and no
rational is `sqrt(2)`; the wall is a cardinality theorem, not an engineering
limit (`GLM.Info.no_countable_layer_lossless`). So a real is held as the
**process** that converges to it: `x.at(k)` returns an exact `Fraction` within
`2⁻ᵏ`, for any `k`. No float is constructed anywhere in the module.

| Fact | Value | Recomputed by |
|---|---|---|
| `sqrt(2)`, `pi`, `e`, `phi` to 20 places | `1.41421356237309504880`, `3.14159265358979323846`, `2.71828182845904523536`, `1.61803398874989484820` | `exact_real_report()` |
| the tower's stand-ins for `sqrt(2)` | `1, 1, 5/4, 11/8, 11/8, 45/32, 45/32, 181/128` | `surrogate_sequence` |
| the level that exposes each | `0->2, 1->2, 2->3, 3->5` | `exact_real_report()` |
| modulator error after `N` ticks | `≤ 1/N` at `N = 10, 100, 1000` | `delta_sigma_error` |
| equality of two processes | never claimed | `decide_equal` |

Query: `report infinite values`. Machine-checked counterparts:
`RequestProject/GLM/DeltaSigma.lean` and `Irrational.lean`.

### 3.2 Written arithmetic over them — **done**

`glm_universal/reasoning/real_expr.py` reads `+ - * /`, integer powers,
brackets, `sqrt`, `cbrt`, `root(degree, x)`, the constants `pi`, `e`, `phi`,
and any rational or decimal literal — a decimal being read as the rational it
names, so `0.1+0.2` is exactly `3/10`.

Division is the case with content. `1/x` is computable only from a bound
`|x| ≥ 2⁻ᵐ`, and no algorithm produces that bound for an arbitrary process,
because doing so would decide whether the process is zero
(`GLM.Info.nonzero_iff_witness`). `divide` therefore searches for the witness
to `WITNESS_DEPTH = 96` and refuses beyond it, naming the depth:
`1/(sqrt(3)-sqrt(2))` goes through and equals `sqrt(3)+sqrt(2)`;
`1/(sqrt(2)-sqrt(2))` is refused.

### 3.2a The transcendental functions — **done**

`glm_universal/reasoning/transcendental.py` takes the grammar past the
algebraic operations: `exp`, `log` (natural, or `log(base, x)`), `sin`, `cos`,
`tan` and a non-integer exponent `x^y`. Everything is exact rational
arithmetic — no float is constructed — and every error budget is stated:

| Fact | Value | Recomputed by |
|---|---|---|
| `exp(1)`, `log(2)`, `sin(1)`, `cos(1)`, `tan(1)` to 20 places | `2.71828182845904523536`, `0.69314718055994530941`, `0.84147098480789650665`, `0.54030230586813971740`, `1.55740772465490223050` | `transcendental_report()` |
| `2^pi`, `2^(1/3)` | `8.82497782707628762385`, `1.25992104989487316476` (`= root(3, 2)`) | `transcendental_report()` |
| `exp` inverts `log`; `sin² + cos² = 1`; `log(2, 8) = 3` | all hold to `2⁻⁵⁸` | `transcendental_report()`, `expression_report()` |
| positivity-witness search depth | `96` | `POSITIVE_WITNESS_DEPTH` |

**Where the grammar stops now.** Two places, and they are different in kind.
`log(x)` needs a positivity witness `x ≥ 2⁻ᵐ` for exactly the reason `1/x`
needs a nonzero one, so `log(2)` goes through and `log(sqrt(2)-sqrt(2))` is
refused with its depth named; `x^y` inherits that through
`GLM.Info.rpow_eq_exp_mul_log`. That stop is a theorem
(`GLM.Info.pos_iff_witness`). The other is a work item: the inverse and
hyperbolic family — `asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh`, `erf`,
`gamma`, `zeta` — is refused by an explicit list
(`real_expr.UNBUILT_FUNCTIONS`), so the refusal names the missing function
rather than failing to parse.

Machine-checked counterpart: `RequestProject/GLM/Transcendental.lean`.

### 3.3 The comparison queries — **done**

Two new query kinds, `real` and `compare`, bring the fifteen answering kinds to
seventeen:

| Surface | Answer |
|---|---|
| `approximate sqrt(2) to 20 places` | `1.41421356237309504880`; and plainly, no carrier holds it |
| `is pi less than 355/113` | `true: pi < 355/113`, separated at `2**-32` |
| `compare sqrt(2) and 1.5` | `sqrt(2) < 1.5`, separated at `2**-8` |
| `is sqrt(2)*sqrt(2) equal to 2` | not distinguished at `2**-256`; equality of processes is not decidable, so nothing is claimed |

Both kinds carry the usual third column: a generated script that re-derives the
answer in a fresh interpreter and asserts it key by key.

### 3.4 The 24-D carrier, bounded — **done, with a certificate**

The dynamic carrier of [`DYNAMIC_CARRIER_STUDY.md`](DYNAMIC_CARRIER_STUDY.md)
is implemented exactly and then tested against its own proposal. It survives in
one dimension and fails in twenty-four, and the failure is the more interesting
result:

| target | result |
|---|---|
| all-½ | deviation **0**, two codewords |
| `sqrt(2)-1` in all 24 coordinates | tracked to within `1/N` |
| the ramp, coordinate `i` holds `i/24` | deviation `19/300` after 200 ticks and not shrinking; accumulator `311/24`, growing linearly |

Every emitted state is a Golay codeword, so every reading is a convex
combination of codewords (`GLM.Info.avgVec_mem_hull`) and the reachable set is
the convex hull of the code. `hull_certificate` returns a linear functional
putting the ramp target strictly above all 4,096 codewords, gap **13/5760**;
with `GLM.Info.not_tendsto_avg_of_separating` that is a proof, not an
observation. `GLM.Info.avgVec_periodic` pins the set from the other side.
Only a larger emitted alphabet would move it; nothing about the decoder would.

### 3.5 The capability probes — **done**

`glm_universal/capabilities/` is the eighth sub-package and exists for one
question: *where does it break?* A probe states a capability in a user's words,
declares beforehand whether it is expected to hold, runs the real code, and
reports the exact place the capability stops.

**33 probes: 19 hold, 14 break, 0 errored, 0 surprises.** A break is a located
boundary, not a failure. Twelve of the fourteen are theorems; two are work
items — a vocabulary that is exactly the registers (1,768 named terms, 66 of
them ambiguous and refused), and no query kind that does arithmetic over
register names (`what is energy divided by time`). The third work item, the
transcendental functions, was closed by §3.2a; its probe now reports `holds`
and checks the identities instead of the refusal, which is how a capability
won becomes as visible as a capability lost.

Query: `report capabilities`, or `python3 -m glm_universal.capabilities`
(`--area`, `--probe`).

### 3.6 The Lean development, extended

Five files bring it from thirteen to eighteen, still free of `sorry` and still
depending on nothing beyond `propext`, `Classical.choice` and `Quot.sound`:
`DeltaSigma.lean` (the `1/N` law and its limit), `Irrational.lean` (the
cardinality wall, and a tower that is faithful although no level of it is),
`Reachable.lean` (the hull, the certificate, exact periodic reachability),
`Computable.lean` (what division needs, what it costs, and why equality is
refused while inequality is decided) and `Transcendental.lean` (the error
budget each transcendental function pays, the positivity witness as an
equivalence, and `x^y = exp(y·log x)` for a positive base).

---

## Phase 4 — meaning, not spelling

This phase shipped as `glm_universal` **v1.1.0**, between Phase 2 and Phase 3.
It is recorded here because the rest of the plan wires *mechanisms*, and this
one asks what the mechanisms are mechanisms **about**.

### 4.1 The audit of the inherited concept graph — **done**

`glm_universal/semantics/audit.py` measures the ARC-era graph in
`arc_agi_17/results/glm_state.json` rather than describing it. Its carriers
were `sha256` of a *spelling*, truncated to 24 bits and snapped to a codeword,
and its edges were mostly distances between those carriers:

| Measurement | Result | Recomputed by |
|---|---|---|
| concepts denoting anything determinate | **83 / 4,282** | `concept_grounding()` |
| edges stating a re-derivable relation | **2 / 4,015** | `edge_grounding()` |
| mean legacy Hamming, related pairs | 4547/376 ≈ 12.09 | `carrier_information()` |
| mean legacy Hamming, unrelated pairs | 12077/1009 ≈ 11.97 | `carrier_information()` |
| two random 24-bit words | 12 | — |

The related and unrelated means straddle the random-word expectation, which is
what "no signal" looks like when it is measured. `purge_plan()` writes the
consequence out as a document; it reads the state file and never writes it.

### 4.2 The meaning space and the grounded graph — **done**

`semantics/meaning.py` encodes *what a term denotes* — one of six determinate
kinds (number, dimension, quantity, element, compound, operation) — into 24
exact coordinates. `encode` takes a `Meaning` and nothing else, so "the carrier
does not depend on the notation" is enforced by the signature. The round trip
is exact, the encoding is injective, and at capacity two formulas collide, so
the honest answer there is refusal rather than truncation.

`semantics/reference.py` resolves a notation or refuses with a reason: a term
with two determinate readings (`II` is two, and two iodine atoms) is refused
rather than decided by resolver order. `semantics/relations.py` derives fifteen
binary and four ternary relations from meanings alone, each carrying the
arithmetic that makes it true and each re-checkable by `verify`.

| Quantity | Value | Recomputed by |
|---|---|---|
| notations resolved | 1,705 | `build_graph()` |
| meanings (nodes) | 357 | `build_graph()` |
| binary edges | 6,210 | `build_graph()` |
| ternary edges | 6,649 | `build_graph()` |
| edges re-derived from the meanings they join | all | `graph.verify` |

Queries: `meaning of <term>`, `relate <a> <b>`, and `report semantics` — the
last with the usual column-3 script, which returns `VERIFIED True`.

Machine-checked counterpart: `RequestProject/GLM/Semantics/Meaning.lean` (the
round trip `decode_coords`, injectivity `coords_injective`, and
`capacity_forces_refusal`) and `Grounding.lean` (`semantic_iff_respects`,
`spelling_not_semantic`, the `legacy_threshold_dichotomy` that no proximity
radius recovers synonymy, and `energy_torque_mem_boundary`, the EXT10 → SI7
boundary).

---

## Phase 5 — ambiguity as a value

The runtime already had a place where it stopped without failing: a received
word at distance 4 from the code, which `golay_decode` reports as `ambiguous`.
This phase asks what the machine should do there, and answers it by making the
ambiguity a value it can carry.

### 5.1 The shape of the tie — **done, machine-checked**

`RequestProject/GLM/Golay/Code.lean` builds the extended binary Golay code from
the same parity block `substrate/mog.py` ships, with the syndrome additive over
symmetric difference. `Golay/Sextet.lean` then settles the geometry:

| Statement | Content |
|---|---|
| `golay_min_distance_eight` | minimum distance 8 |
| `unique_nearest_of_le_three` | a reading is unique up to error weight 3 |
| `covering_radius_eq_four` | the covering radius is exactly 4 |
| `ties_card_eq_six` | a weight-4 coset has **exactly six** nearest codewords |
| `sextet_partition` | those six partition the 24 coordinates into six tetrads |
| `ties_pairwise_hdist_eight` | they are pairwise at the minimum distance |
| `coset_dichotomy` | every coset is uniquely readable, or a six-fold tie |

The finite parts are exhaustive checks over all 4,096 syndromes, discharged by
`native_decide`; the rest is coset algebra.

### 5.2 Carrying it: two bundles — **done, machine-checked and measured**

| Statement | Content |
|---|---|
| `bundleF2_eq_one` | the XOR of the six tied readings is the all-ones vector, whatever the tie |
| `bundleF2_constant` | so the F₂ bundle carries no information about which tie it came from |
| `bundleQ_eq` | over Q the bundle is `(1 + 4·vᵢ)/6` coordinatewise |
| `bundleQ_recover`, `bundleQ_injective` | the tie is recoverable from the rational bundle, and distinct ties have distinct bundles |

`substrate/superposition.py` measures the same thing on the running code: over
256 superpositions the F₂ bundle takes one value (`16777215`) and distinguishes
1 input; the rational bundle has coordinates in `{1/6, 5/6}`, distinguishes all
256, and `recover_from_bundle` returns the members exactly.

### 5.3 Collapse, wobble, and the alphabet — **done**

`collapse(sup, context)` filters by a context predicate and reports
`collapsed`, `superposed` or `refuted` — never a tie broken by member order.
`Wobble.lean` shows a carrier cycling through the six readings is read back
exactly as their rational bundle (`sextet_cycle_avgVec`) and that the reading
still determines the tie. `HullExpansion.lean` separates a target from the hull
of the available states with an explicit functional, so no schedule reaches it,
and reaches it in a 16-tick cycle once two Leech vectors are admitted:
`alphabet_expansion_strictly_helps`.

### 5.4 Runtime surface — **done**

| Query | Kind | Notes |
|---|---|---|
| `report superposition` | report | aliases `report ambiguity`, `report tie`, `report sextet`, `report bundling`, `report parallel hypotheses`, `report list decoding`; six steps (sextet, bundling, collapse, census, chain, hull), column-3 template returns `VERIFIED True` |

Tests: `tests/test_superposition.py` (61). Write-up:
[`GEOMETRIC_AMBIGUITY_STUDY.md`](GEOMETRIC_AMBIGUITY_STUDY.md), which also
names what is *not* settled — the VOA state-field map and the Niemeier
deep-hole census.

### 5.5 The coset census — **done**

`Golay/Census.lean` counts how often the tie actually happens, rather than
describing its shape. `cosetWt f` is the distance from a word of syndrome `f`
to the code (`cosetWt_eq_dist`), and the census is exact:

| coset weight | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| syndromes | 1 | 24 | 276 | 2024 | 1771 |

(`coset_census`, with `census_total` checking the five add to the 4,096
syndromes). So `unique_vs_ambiguous`: **2,325** of the cosets are read uniquely
and **1,771** are six-fold ties. The mean distance to the code is exactly
`13732/4096 = 3433/1024 ≈ 3.352` (`mean_coset_weight`), and it sits strictly
between the packing radius 3 and the covering radius 4
(`mean_coset_weight_gt_three`, `mean_coset_weight_lt_four`): the *average* word
is already past the radius inside which the reading is unique. Ambiguity is
the typical case for this code, not a corner case.

`substrate/superposition.py::coset_census_report` recomputes all of it in exact
rational arithmetic from the running decoder, and it is the fifth block of the
`report superposition` subject.

### 5.6 The dynamical half of the criticality question — **answered**

`Golay/Dynamics.lean` turns the self-organised-criticality reading of the
census into a statement about a process and settles it. One tick of "flip a
uniformly chosen coordinate" adds a parity-check column to the carrier's
syndrome, so the carrier performs a random walk on the 4,096 cosets.

| statement | Lean |
|---|---|
| the uniform law is stationary | `step_unif` |
| and it is the only stationary law | `stationary_unique` |
| its mean distance to the code is `3433/1024` | `expect_unif_cosetWt` |
| it puts `3795/4096` at distance 3 or 4 | `prob_unif_critical_band` |
| but `301/4096` below the packing radius, so it does not concentrate | `prob_unif_subcritical_pos` |
| every parity-check column has odd parity | `par_col` |
| so the chain is periodic and has **no** limiting law | `iterate_dirac_ne_unif` |
| and a corrected one-bit error returns the same codeword | `perturb_correct_returns` |

So the claim holds only in its time-averaged form. The remaining piece — a
Lean proof that the Cesàro averages converge to the uniform law — is recorded
as open at the end of the file, with the exact obstruction (a quantitative
mixing argument Mathlib does not supply for a kernel of this shape).
`substrate/superposition.py::coset_chain_report` pushes the law forward in
exact arithmetic and is the fifth block of `report superposition`: from a point
mass the supports run `24, 277, 2048, …`, the parity class alternates, and
after twelve ticks the two-step average distance is `76017479/22674816`, within
`5819/181398528` of `3433/1024`.

### 5.7 The Lean development, extended

Seven files bring it from eighteen to twenty-five, still free of `sorry`:
`Golay/Code.lean`, `Golay/Sextet.lean`, `Golay/Census.lean`,
`Golay/Dynamics.lean`, `Superposition.lean`, `Wobble.lean` and
`HullExpansion.lean`. The exhaustive checks in `Golay/Sextet.lean` use
`native_decide`, so they and the results downstream of them depend on
`Lean.ofReduceBool` and `Lean.trustCompiler` in addition to `propext`,
`Classical.choice` and `Quot.sound`.

---

## Phase 6 — measuring what the machine can actually do

### 6.1 The end-to-end CLI evaluation — **done**

`glm_universal/evaluation/` is the ninth sub-package and the first instrument
that measures the machine from *outside*. `capabilities/` interrogates the
library and `benchmarks/` scores solver functions; neither goes through
`GLM.py`. Each of the 72 cases in `evaluation/cases.py` starts the CLI in a
**fresh interpreter** — one subprocess per question, no shared session, no warm
caches — and scores the `ANSWER` or `UNSOLVED` line it prints.

The question set covers **all 18 query kinds** and **all 19 report subjects**;
`tests/test_evaluation.py` checks that coverage against the runtime's own
tables, so neither table can be extended without a case. Scoring is asymmetric:
`correct` and `refused_as_expected` are `+1`, an `unexpected_refusal` is `0`,
and a `wrong_answer` or a crash is `−1`, because a refusal tells the user where
the machine stops and a confident wrong answer does not. 11 of the 72 questions
are ones the machine should refuse, each labelled `boundary` (a theorem or a
deliberate commitment) or `gap` (missing implementation).

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.evaluation --jobs 8 --json eval.json
```

Exit code 0 only when every case passes, so it is usable as a gate. `--only
<kind>`, `--case <id>` and `--list` narrow it.

### 6.2 The measured result

| instrument | result |
|---|---|
| capability probes | 33 probes: 20 hold, 13 break, 0 errored, 0 surprises |
| benchmark suites | 2,389 / 2,390 tasks across 5 suites; every suite above baseline |
| end-to-end CLI evaluation | 83 cases, **83 passed** — 73 correct, 10 refused as expected, 0 unexpected refusals, 0 confidently wrong, 0 errored |
| test suite | 1,677 tests across 37 test files, 8,851 subtests, zero failures |

The evaluation set opened at 72 cases scoring 67, with every failure in one
query kind — `analogy` at 3/8. That is what Phase 7 was for.
`CAPABILITY_ASSESSMENT.md` carries the current reading case by case.

### 6.3 A gap closed, with before and after

`approximate 1/0 to 5 places` escaped the CLI as an uncaught
`ZeroDivisionError` traceback — outcome `error`, weight `−1`. `_solve_real` and
`_solve_compare` in `runtime/session.py` now catch it and refuse, saying that a
quotient by an exact zero names no value — outcome `refused_as_expected`,
weight `+1`. Evaluation 66 → **67 of 72**, errored cases 1 → **0**, pinned by
`test_division_by_an_exact_zero_refuses_rather_than_crashing`.

---

## Phase 7 — closing what the evaluation found

Phase 6 produced a list of five wrong answers and a list of things not
attempted.  This phase worked through both.  Every item says what recomputes
it.

### 7.1 Analogy by named relation — **done**

Every one of the five wrong answers was an analogy whose relation is **not a
displacement of the coordinates**, so no amount of metric work would have
fixed them.  `reasoning/analogy_models.py` adds the missing layer: four named
models — `periodic_step`, `reciprocal_dimension`, `scale_shift`,
`lexicon_relation` — each of which either says what the relation *is*, in the
register's own terms, or declines.  A model that recognises the pair but finds
nothing at the transported position **refuses and says where it looked**,
which is a better answer than the nearest point to a meaningless target.
Recomputed by `report analogies`; scored by the three `analogy_*` benchmark
suites, now 12/12, 13/13 and 10/10.  The write-up is
[`ANALOGY_LAYER_STUDY.md`](ANALOGY_LAYER_STUDY.md).

### 7.2 The molecules register — **done**

`data_objects/molecules.py` is the sixth register: **51 molecules and ions**,
a formula grammar reading counts, nested brackets, hydrates and charges, and
nothing stored per species but a name and a formula — all 19 coordinates are
derived from the element register at load time, and a gap there stays a gap
here.  A molecule is held twice, as the faithful bundle of element carriers
with multiplicities and as one composite summary carrier, and the summary is
*tested* for collisions rather than trusted: 0 of either kind.  Recomputed by
`report molecules`.

### 7.3 Sparse chemistry data — **done**

`reasoning/element_coverage.py` measures the sparsity (1,257 of 1,652 cells)
and widens it three ways that each invent no measurement: **derive** (4
attributes, 344 new cells), **estimate** (one linear fit, coverage 12/59 →
99/118, mean absolute residual `5825791/450744` pm, worst element Mg) and
**cross-check** (14 comparable elements, 10 agreeing within 20 kJ/mol and 4
not — reported, not merged).  Nothing is written back into the register.
Recomputed by `report chemistry coverage`.

### 7.4 The transform decoder, the deep-hole census, and arithmetic inside a description — **done**

`reasoning/fwht_decode.py` wires the Walsh–Hadamard transform to something:
all 4,096 coset costs in one transform, with the tier at which the
constant-time answer carries its own certificate (`report transform decoder`).
`reasoning/voronoi_walk.py` and `reasoning/deep_holes.py` reach a hole by
walking to it and climbing to the covering radius, so the Niemeier type is
*derived* rather than looked up among 196,560 facets (`report deep holes`).
`reasoning/term_arithmetic.py` reads `energy divided by time` as one question,
which moved the capability probe `runtime_arithmetic_inside_a_describe` from
`breaks` to `holds` — the probes' totals went 19/14 → **20/13**.

### 7.5 The unit strings — **done, and the steradian priced**

`reasoning/units.py` parses every quantity's unit string and checks it against
its EXT10 exponents, so the two independent statements each quantity makes
about itself are compared rather than assumed to agree.  The steradian is not
silently redefined: what an SI reading of it *would cost* is computed and
reported (`report units`).

### 7.6 The inherited concept graph — **decided**

Phase 4 measured it and left the decision open.  It is now recorded, with its
grounds recomputed, in `semantics.audit.retention_decision()`: **demoted to
evidence**.  Neither branch was taken whole — refining it is not possible in
the sense that matters (an edge earns its place by being re-derivable from
what its endpoints mean, and for 4,013 of the 4,015 at least one endpoint
denotes nothing to derive from), and deleting it would delete the evidence for
that very claim.  So it stays as the audit's input and is read by nothing that
answers a question — which `tests/test_inherited_graph.py` enforces by walking
the imports of every module on the answering path.

### 7.7 The figures mechanism — **done**

`glm_universal/figures.py` recomputes every count the documentation quotes and
renders [`overlay/FIGURES.md`](overlay/FIGURES.md);
`tests/test_figures.py` compares the committed file against a fresh
computation and checks each README against the current numbers, so a stale
figure is a test failure rather than something a reader discovers.

### 7.8 The VOA state–field map — **built at the Griess layer, with the obstruction proved**

The one item on the Phase 6 list that was entirely open.  `RequestProject/GLM/VOA.lean`
takes it as far as a finite-dimensional model reaches, and proves that that is
as far as one reaches.

In a vertex operator algebra the Griess product of two weight-two states is a
single mode of the state–field map `Y(u, z) = Σₙ uₙ z⁻ⁿ⁻¹`.  The file builds
that map on the 2A algebra of `Sakuma.lean`: `mode u 1 v = u ⋆ v` and nothing
else, so `mode_truncated` makes the field a genuine formal Laurent series.
What the layer carries is real structure and is proved: `mode_skew` (the
skew-symmetry axiom at this weight — the commutativity of the Griess product),
an invariant bilinear form that is *not chosen* but forced, since
`form_forced_off_diagonal` derives `⟨eᵢ, eⱼ⟩ = (1/8)⟨eᵢ, eᵢ⟩` from invariance
alone, and hence `form_invariant`, `mode_self_adjoint` and
`form_nondegenerate` — the layer is a Frobenius algebra — together with the
vacuum `vac = (4/5)(e₀ + e₁ + e₂)`, a two-sided identity with `form_vac = 12/5`.

What it does not carry is stated just as exactly.  Borcherds' commutator
formula at `m = n = 1` would demand, once every mode but the first is
discarded, `u ⋆ (v ⋆ w) − v ⋆ (u ⋆ w) = (u ⋆ v) ⋆ w`; on the axis triple the
two sides are `(−3/32) e₀ + (3/32) e₁` and `(−3/32) e₂`
(`borcherds_commutator_fails`, with both sides computed).  The discarded modes
are load-bearing, so the infinite-dimensional development is *necessary* rather
than merely traditional.  Building it leaves the finite-dimensional setting,
and that is not done.

### 7.9 Still untouched

Named here so nothing is implicitly claimed:

* **The infinite-dimensional half of the VOA bridge**, past the Griess layer
  §7.8 builds.
* **Multi-domain analogy.** `heat : temperature :: force : ?` still needs all
  four operands in one register.
* **Ranking an unregistered formula.** `nearest to PbCl2` refuses: the codec
  would encode it, but `nearest` resolves its operand against the names a
  register enumerates.  This is the evaluation set's one remaining `gap` case.
* **Open vocabulary.** The vocabulary is exactly the registers; there is no
  coordinate for *justice*, and the semantics layer refuses rather than
  inventing one.
* **Words as projections.** `hot` is a standalone concept, not "temperature at
  high scale".
* **The delta–sigma directions** — cascaded loops, error feedback through a
  symmetry-commuting rational matrix, subtractive dither with an
  equidistributed sequence, sigma–delta on the shells, and the Gibbs-style
  rule — are exploratory and not started.
