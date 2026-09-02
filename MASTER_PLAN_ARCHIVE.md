# Master plan — archive

The closed phases of [`MASTER_PLAN.md`](MASTER_PLAN.md), kept exactly as they
were written.  Section numbers referred to elsewhere (for example
`MASTER_PLAN_ARCHIVE.md` §7.9) are the ones in this file.

<!-- figures:history -->

*Everything in this file is an archive: each phase records what was measured
when it was closed, and those counts are deliberately left alone.  For the
project as it is now, see [`MASTER_PLAN.md`](MASTER_PLAN.md) and
[`overlay/FIGURES.md`](overlay/FIGURES.md), which is regenerated from the code.*

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
| `report blueprint` | `reasoning/blueprint` |
| `report engine` | `reasoning/engine` |
| `report mantissa` | `reasoning/mantissa` |
| `report reversible` | `reasoning/reversible` |
| `report noise` | `reasoning/noise_lab` |
| `report signature` | `reasoning/wobble` |
| `report drift` | `reasoning/drift` |
| `report catalog` | `reasoning/catalog` |
| `report containers` | `reasoning/containers` |
| `report companion` | `reasoning/companion` |
| `report lattices` | `substrate/lattice32`, `substrate/lattice48`, `reasoning/higher_lattices` |
| `report shells` | `reasoning/shell_sigma` |
| `report lean` | `reasoning/lean_address` |
| `report harmony` | `data_objects/harmonics`, `reasoning/harmony` |
| `report directives` | `reasoning/directives` |
| `report pipeline` | `reasoning/pipeline` |

`task` is a new query kind, with its own parse branch and solver. Each subject
and task has a Three Column Thinking template, so the answer is stated in
language, in exact mathematics, and as a script that reproves it from the public
API in a separate process.

---

## Phase 3 — the value layer, and the map of where the machine stops

The phases above make every *mechanism* reachable. This one asks what happens
to a *value* the mechanisms cannot hold, and then asks the machine to say for
itself where it stops. The write-up is
[`INFINITE_VALUES_STUDY.md`](studies/INFINITE_VALUES_STUDY.md).

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

The dynamic carrier of [`DYNAMIC_CARRIER_STUDY.md`](source_material/DYNAMIC_CARRIER_STUDY.md)
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
[`GEOMETRIC_AMBIGUITY_STUDY.md`](studies/GEOMETRIC_AMBIGUITY_STUDY.md), which also
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
| end-to-end CLI evaluation | 92 cases, **92 passed** — 82 correct, 10 refused as expected, 0 unexpected refusals, 0 confidently wrong, 0 errored |
| test suite | 42 test files, zero failures |

(The same figures are restated, with what moved, in §9.4.)

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
[`ANALOGY_LAYER_STUDY.md`](studies/ANALOGY_LAYER_STUDY.md).

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

Named here so nothing is implicitly claimed.  Phase 8 closed three of the
items this list carried; what is left is below.

* **The infinite-dimensional half of the VOA bridge**, past the Griess layer
  §7.8 builds.
* **`heat : temperature :: force : ?`** is still refused.  Cross-register
  analogy itself is *not* the obstacle — `hot : temperature :: fast : velocity`
  is answered — so what is missing is the relation: the lexicon carries
  `temperature drives heat`, which reaches nothing when looked up from `force`.
* **Open vocabulary.** The vocabulary is exactly the registers; there is no
  coordinate for *justice*, and the semantics layer refuses rather than
  inventing one.
* **Words as projections.** `hot` is a standalone concept, not "temperature at
  high scale".
* **The rest of the delta–sigma directions.** Cascaded loops, subtractive
  dither with an equidistributed sequence and interacting tones are built
  (§8.2), and error feedback through a symmetry-commuting rational matrix is
  built and proved (§9.4).

Two items left this list in Phase 11: the **32- and 48-dimensional lattices**
are built (§11.1), and **sigma–delta on the Leech shells** with the
Gibbs-style rule is built and measured (§11.2).

One item left this list in Phase 13: **a harmonic register** is built, and the
musical third of the catalogue's universality claim is measured rather than
recorded as missing (§13.1–§13.4).  What replaces it on the list is narrower:
**an economic register**, the one third of that claim still untestable here.

One item left this list in Phase 10: **building a carrier in every solver that
takes one** is now done — `coherence`, `spatial`, `angle` and `cluster` fall
through to the formula parser exactly as `nearest` and `describe` already did,
so `coherence PbCl2` answers instead of refusing (§10.3).  With it went the
evaluation set's last `gap` case.

---

## Phase 8 — the blueprint tested, and noise used as the computation

### 8.1 The unification blueprint as a live claim ledger — **done**

`glm_unification_blueprint.md` is a specification document, and a specification
that is only read can drift from the code without anybody noticing.
`reasoning/blueprint.py` recomputes every testable sentence of it against the
package and gives each one of four verdicts — confirmed, refuted with what
holds instead, unsupported by the measurement it names, or describing a
subsystem that does not exist.  Reaching a verdict needed three subjects the
package did not have, and each is a module in its own right:

* `reasoning/engine.py` — Part III's thermo-dynamic carrier engine, assembled
  from parts that already existed (cam, accumulator, escapement, lattice snap,
  radiator, two fuels, turbocharger, gearbox), so the section's headline
  precision figure is *measured* against the three baselines it could mean
  rather than quoted.
* `reasoning/mantissa.py` — section 5.1's bit-spectrum tracker, built so that
  **no float is ever constructed**: IEEE-754 binary64 is modelled exactly in
  integers and `Fraction`, so everything the module says about doubles is a
  theorem about that model rather than a measurement of the interpreter.
* `reasoning/reversible.py` — Part V: binary counting against the binary
  reflected Gray code, Toffoli and Fredkin on the 24 coordinates, and
  information carried as kinks in a circular string.

Wired as `report blueprint`, `report engine`, `report mantissa` and
`report reversible`, each with a column-3 script, and pinned by
`tests/test_blueprint.py` (77 tests).  The machine-checked counterparts are
`RequestProject/GLM/Mantissa.lean` and `RequestProject/GLM/Reversible.lean`:
the dyadic orbit of a float always collapses while the exact orbit of `1/p`
never does, and Gray coding does **not** dissipate exactly half at any finite
width — the sharp statement is `2·grayCycleFlips w = binaryCycleFlips w + 2`.

### 8.2 Noise as the computation — **done**

`ToDo_01.txt` asks for the next thing after holding a value in a moving
carrier: to stop treating the wobble as a representation and start computing
with it.  `reasoning/noise_lab.py` is that laboratory, in exact `Fraction`
arithmetic with nothing random anywhere, and `RequestProject/GLM/Cascade.lean`
proves what it measures.

* **A signal, not a constant.** `mState_mem_Ico` and `mAverage_error_le`: the
  bits of a modulator driven by a time-varying input track that input's running
  mean to `1/N`, with `mState_const` and `mBit_const` recovering
  `DeltaSigma.lean`'s constant-target case.
* **Closed orbits.** `mState_period_eq_zero`, `mState_periodic`,
  `mBit_periodic`: a `P`-periodic input whose period sums to an integer gives
  an exactly periodic trajectory — the wobble is a cycle rather than a drift.
* **Cascaded loops.** The MASH 1-1 cascade is built and measured:
  `casOut_mem` (four output values, `−1 … 2`), `casOut_error` (the error is a
  *second* difference) and `casTriangular_error_lt` — under a triangular window
  the cascade's error is below `2/(M(M−1))`, against
  `firstOrder_triangular_error_ge`'s `1/(2M)` for a single loop on the same
  target.  `O(1/M²)` against `O(1/M)`, proved and then reproduced exactly.
* **Interacting tones and dither.** An exact Walsh spectrum reads the strength
  of each tone in a mixed input, and a subtractive-dither sweep trades the idle
  tone down monotonically for a bias it states rather than hides.

Wired as `report noise` (aliases `wobble`, `wiggle`, `dither`, `cascade`) with
a column-3 script that returns `VERIFIED True`, and pinned by
`tests/test_noise_lab.py` (50 tests, ten of them the vector loop of §9.4).  The write-up is
`NOISE_EXPERIMENT_STUDY.md`.

### 8.3 The evaluation set widened, and one gap closed — **done**

The four subjects of §8.1 and the one of §8.2 are report subjects, and
`tests/test_evaluation.py` checks the case set against the runtime's own
tables, so each needed a case: 83 → **89 cases**, all 30 report subjects
exercised.  `nearest to PbCl2` — the previous round's single `gap` — is closed:
an operand no register enumerates is handed to the formula parser and the
carrier it builds is ranked, with nothing guessed, so the case now expects an
answer.  Closing it exposed the next one, which is where the gap label moved:
`coherence PbCl2` refuses, because the coherence solver still resolves register
names only.

### 8.4 The measured result

| instrument | result |
|---|---|
| capability probes | 33 probes: 20 hold, 13 break, 0 errored, 0 surprises |
| benchmark suites | 2,389 / 2,390 tasks across 5 suites; every suite above baseline |
| end-to-end CLI evaluation | 89 cases, **89 passed** — 79 correct, 10 refused as expected (9 boundary, 1 gap), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| test suite | 1,799 tests across 39 test files, 8,851 subtests, zero failures |
| Lean development | 30 files, 7,388 lines, `lake build` clean, **0 `sorry`** |

(Those are the figures of the round that closed Phase 8. The current ones are
in §9.5 and, generated, in `overlay/FIGURES.md`.)

---

## Phase 9 — the external study catalogue, tested

### 9.1 The catalogue as a live claim ledger — **done**

`glm_study_findings_catalog.md` is the second supplied document that records
measurements rather than code: iteration drift over the odd primes, the
code-to-lattice ladder, the generators and containers of irrational numbers,
the 53-bit mantissa question, the physical-mechanical engine family,
substrate-native bit dynamics, and a landscape study of domain applications.
`reasoning/catalog.py` treats it the way §8.1 treats the unification
blueprint: every testable sentence is restated as a claim, recomputed against
the package, and given one of four verdicts — `confirmed`, `refuted`,
`not reproduced`, `not implemented`.

**57 testable claims: 32 confirmed, 14 refuted, 7 not reproduced, 4 not
implemented**, recomputed by `catalog_report()` and reachable as
`report catalog`. The pattern in the refutations is worth keeping: where the
catalogue reports a number produced by running a loop, the package reproduces
it to the digit; where it reports that a measured column *is* a property of
the thing measured, the column is usually a closed form of the input. The
write-up is `GLM_STUDY_CATALOG_AUDIT.md`. Pinned by `tests/test_catalog.py`
(26 tests).

### 9.2 The spectral signature, and why it is not a measurement — **done, machine-checked**

`reasoning/wobble.py` runs the catalogue's §2.3 experiment — ten thousand
ticks of the modulator against a constant, then entropy, run lengths,
transition rate and one-density — and prints the *law* beside every measured
column. `RequestProject/GLM/Sturmian.lean` proves the laws:
`dsState_eq_fract` (the accumulator is exactly `Int.fract (n·t)`, so the loop
is an irrational rotation), `dsBit_eq_floor_diff` (the stream is the Sturmian
word of slope `t`), `dsOnes_eq_floor`, `ds_zero_run_length_lt` and
`ds_one_run_length_lt` (runs below `1/t` and `1/(1−t)`), `dsTransitions_eq`
with `dsTransitions_rate_tendsto`, `dsMeanRunLength_tendsto`, and
`ds_wobbleEntropy_tendsto` with `ds_wobbleEntropy_zero_iff_silent`. Running
the loop therefore tests nothing the target did not already determine.
`ds_resonance_lock` and `ds_resonance_entropy` pin the locked loop at entropy
exactly zero, and the exact resonance sweep shows the entropy dip is *local*:
a far-detuned circuit is nearly as quiet as a locked one. Wired as
`report signature` (aliases `spectral`, `sturmian`, `resonance`), pinned by
`tests/test_wobble.py` (33 tests).

### 9.3 Iteration drift, in three regimes and no floats — **done**

`reasoning/drift.py` runs `X_{n+1} = r X_n − 1/p` for 200 steps from
`X_0 = 1/p` over the odd primes in exact rational arithmetic, in binary64 —
modelled exactly by `reasoning/mantissa.to_double`, so no float is ever
constructed — and in binary64 truncated to a fixed number of significant
decimal digits, which is the study's model of a number that leaves the machine
as printed text and comes back parsed. The contractive rule damps its own
rounding error and stays inside every regime's ceiling; the accumulative rule
amplifies the first rounding into a drift of `7.49e+10` at `p = 3` in plain
binary64 and `2.22e+22` at four displayed digits, and truncation never helps.
Wired as `report drift`, pinned by `tests/test_drift.py` (26 tests).

### 9.4 Error feedback through a symmetry-commuting matrix — **done, machine-checked**

The last of §7.9's delta–sigma directions that was reachable from a finite
model. `RequestProject/GLM/Feedback.lean` builds a modulator on `n`
coordinates whose past quantisation error returns through a rational matrix
`A` and proves three things: `efErr_abs_le_half` (the instantaneous error
never leaves `[−1/2, 1/2]`, whatever `A` is), `efSum_eq` with
`efAverage_error_le_identity` (at `A = 1` every coordinate tracks its input's
running mean to `1/(2N)` — the vector form of the `1/N` law, and sharper than
the scalar accumulator's) and `efOut_equivariant` (a permutation leaving `A`
invariant permutes the whole trajectory tick for tick). `halfFeedback_dead_zone`
is the negative half: contracting the feedback to `A = 1/2` on the constant
`1/4` does not slow the loop, it silences it. `reasoning/noise_lab.py`
measures all four — `feedback_run`, `feedback_tracking`, `equivariance_check`
and `dead_zone`, with a non-invariant matrix run beside the invariant one so
the hypothesis is seen to be load-bearing — and they are the sixth step of
`report noise`, re-derived by its column-3 script. The write-up is
`NOISE_EXPERIMENT_STUDY.md` §6.

### 9.5 The measured result

| instrument | result |
|---|---|
| capability probes | 33 probes: 20 hold, 13 break, 0 errored, 0 surprises |
| benchmark suites | 2,389 / 2,390 tasks across 5 suites; every suite above baseline |
| end-to-end CLI evaluation | 92 cases, **92 passed** — 82 correct, 10 refused as expected (9 boundary, 1 gap), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| test suite | 1,894 tests across 42 test files, 8,896 subtests, zero failures |
| Lean development | 32 files, 8,157 lines, `lake build` clean, **0 `sorry`** |

---

## Phase 10 — the two companion preprints, and the last carrier gap

### 10.1 Three containers, as an instrument — **done**

`reasoning/containers.py` is the instrument the first companion preprint,
*The Generators and Containers of Real Processes*, describes but does not
supply: eight constants — `1/3`, `sqrt(2)`, the golden ratio, `pi` by Machin,
`e` by its series, Liouville's constant, Champernowne's constant and an
`Omega` surrogate — carried through three containers.

* **The algorithmic container.** Every generator is an exact `Fraction`
  recurrence, and `precision_bits` returns the largest `b` with
  `|x − x*| / |x*| <= 2**-b`, decided by integer comparison against a 200-bit
  reference. No logarithm is taken and **no float is constructed anywhere in
  the module**. Steps are counted from zero, which is the indexing that
  reproduces the study's own Heron, Machin and exponential tables.
* **The temporal container.** `stream_of` is the delta–sigma stream of the
  target, so `stream_period` does not search a window for a repeat: the stream
  is the mechanical word of a rational target and its least period is that
  target's denominator, which the function *decides*. `apparent_period` and
  `near_period_coincidence` are the counterweight — a window can show a period
  the stream does not have. `sqrt(2)`'s stream agrees with its own 169-shift
  for 400 places, 169 being the denominator of the convergent `70/169`, and
  first disagrees at index **407**.
* **The geometric container.** A hull verdict is a certificate or it is
  nothing. `outside_certificate` exhibits a direction `u` with `<u, x>` above
  `max_p <u, p>` over all 196,560 minimal vectors; `inside_certificate` places
  the target in `{x : |x|_1 <= 8, |x|_inf <= 4}`, whose extreme points are
  exactly the 1,104 minimal vectors of shape `(±4, ±4, 0^22)`. Sampling proves
  membership and can never prove exclusion, so it is not used for exclusion.
  What neither test settles is reported `undetermined`.

Wired as `report containers`, pinned by `tests/test_containers.py` (52 tests).

### 10.2 The preprints as a claim ledger — **done**

`reasoning/companion.py` audits both companion preprints the way §9.1 audits
the findings catalogue: every testable sentence becomes a claim, recomputed
against the package and given one of `confirmed`, `refuted`, `not reproduced`
or `not implemented`. It recomputes from `containers`, `drift`,
`leech_construct`, `golay_decode`, `niemeier` and `wobble`; nothing is quoted.

**49 testable claims: 26 confirmed, 17 refuted, 5 not reproduced, 1 not
implemented** — 28 from the first study, 21 from the second. The write-up is
`GLM_COMPANION_STUDIES_AUDIT.md`. Wired as `report companion`, pinned by
`tests/test_companion.py` (27 tests). Both subjects return `VERIFIED True`
under `--verify-tct`, so column 3 re-derives every printed figure in a fresh
interpreter.

The finer ledger was worth building: several of §9.1's open verdicts were open
only because the summary never stated the projection, the indexing or the
alphabet. Given the definitions, they resolve — mostly to `refuted`, which is
why the refutation count is higher here than in the catalogue audit.

### 10.3 A carrier in every solver that takes one — **done**

`nearest` and `describe` already fell through to the formula parser when a
name was not in a register. `coherence`, `spatial`, `angle` and `cluster` now
do the same, so `coherence PbCl2` answers `NRCI = 0.0000 (Subcoherent)`
instead of refusing, and `cluster PbCl2, NaCl, H2O` builds the unregistered
carrier before clustering. This removed §7.9's carrier item and the evaluation
set's last `gap` case: the 97-case set now expects **0 gap refusals**.

### 10.4 The measured result

| instrument | result |
|---|---|
| capability probes | 33 probes: 20 hold, 13 break, 0 errored, 0 surprises |
| benchmark suites | 2,389 / 2,390 tasks across 5 suites; every suite above baseline |
| end-to-end CLI evaluation | 97 cases, **97 passed** — 88 correct, 9 refused as expected (9 boundary, **0 gap**), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| test suite | 1,991 tests across 44 test files, 8,935 subtests, zero failures |
| Lean development | 32 files, 8,157 lines, `lake build` clean, **0 `sorry`** |

---

## Phase 11 — above 24 dimensions, addressing the Lean development, and the standing rules made into instruments

Four things came together in this phase: the two open geometric directions
§7.9 had been carrying since Phase 7, the question of whether the substrate can
hold a *Lean result* the way it holds a physical quantity, and — because three
consecutive rounds had ended with an account that lagged the code — the
process rules turned into instruments that read the tree.

### 11.1 The two rungs above the Leech lattice — **done**

`substrate/lattice32.py` builds the 32-dimensional Barnes–Wall lattice by
Construction D over the nested Reed–Muller pair `RM(1,5) ⊂ RM(3,5)`, and
`substrate/lattice48.py` builds a 48-dimensional extremal lattice from a
self-dual ternary code plus a neighbour step. `reasoning/higher_lattices.py`
recomputes the ladder rather than quoting it — centre density from
`δ = (minimum/4)^(n/2)`, valid because every rung is unimodular:

| dim | minimum | centre density | kissing |
|---|---|---|---|
| 8 | 2 | `1/16` | 240 |
| 16 | 2 | `1/256` | 480 |
| 24 | 4 | `1` | 196,560 |
| 32 | 4 | `1` | 146,880 |
| 48 | 6 | `(3/2)^24 = 282429536481/16777216` | not computed |

Every rung is extremal for its dimension. The 48-dimensional rung packs about
**16,834 times** more densely per unit cell than Λ₂₄, and costs the whole
binary picture: no Golay code, no MOG, no octads. The 32-dimensional rung buys
something else — the three Construction D levels are genuinely nested lattices,
of index `2^26` and `2^6` (product `2^32`, checked), so a 32-dimensional
address has **three usable resolutions** where a Leech address has one, and
truncating to the first *k* levels lands exactly on the nearest point of the
*k*-th nested lattice. Wired as `report lattices`; the Lean counterpart is
`RequestProject/GLM/HigherLattices.lean`.

### 11.2 Delta–sigma against a Leech shell — **done**

`reasoning/shell_sigma.py` runs the modulator with its alphabet widened from a
small set to a *sphere* — 196,560 minimal vectors — so the alphabet no longer
covers its own hull. Two rules are run side by side: nearest-over-the-lattice,
and matched-over-one-shell with the `B/N` error law. A target inside the hull
is tracked to that bound; a target outside it is certified unreachable by a
separating functional rather than by a failed search. The Gibbs-style rule is
realised **without randomness**: greedy error feedback drives the visit
frequencies to the Boltzmann weights, deterministically, inside the proved
bound `(m−1)/N` at every temperature. Wired as `report shells`; the Lean
counterpart is `RequestProject/GLM/ShellSigma.lean`. The write-up for §11.1 and
§11.2 together is `HIGHER_LATTICE_STUDY.md`.

### 11.3 A Leech address for every Lean declaration — **done**

`reasoning/lean_address.py` reduces each of the **849** declarations of the
formal development (35 files) to 24 integer counts of its *statement* —
quantifiers, connectives, carrier types, size, citation degree, namespace
depth, kind — multiplies by scale 9 and decodes to the nearest Leech point.
Three schemes are computed so the interesting one can be scored: the
structural encoding, a SHA-256-of-the-name **control**, and a seeded reshuffle
of the same addresses.

* **Lossless.** Read back exactly **849/849**, 0 coordinate errors out of
  20,376, worst residual 3 against a covering radius of 4 and a half-step of
  `9/2`.
* **The conflation is the feature map's.** 795 distinct addresses for 849
  declarations — exactly the number of distinct feature vectors, so the
  quantiser adds none of its own; 46 classes conflating 100 declarations.
* **Distance tracks something, weakly.** Nearest-by-address shares a file
  **325/849 ≈ 38.3 %** against a chance rate of `2005/59996 ≈ 3.34 %`, the
  digest control at 27 and the shuffle at 20.

Scale 9 rather than 8 because `8ℤ²⁴ ⊆ Λ` (`eightZ_mem_leech`), so at scale 8
the decoder returns its input. `Address.lean` carries the abstract part — a
quantiser is a resolution, `readback_unique` makes read-back well defined, and
`address_congr` says the address can carry no distinction the features have
already discarded. Wired as `report lean`; the write-up is
`LEAN_ADDRESS_STUDY.md`.

### 11.4 The standing rules, and the instruments that read the tree — **done**

`PROJECT_DIRECTIVES.md` states eight standing rules, each naming the instrument
that enforces it. `reasoning/directives.py` parses that file rather than
paraphrasing it and gives each instrument a live verdict (`report directives`);
`tests/test_project_directives.py` fails if a directive loses its instrument or
if the file and the module disagree.

* **D5, and `reasoning/pipeline.py`.** A study is not finished until it is
  implemented, wired, tested, formalised and verified. The board declares only
  the *association* between a document, its modules, its report subject and its
  Lean files; every stage is read off the tree at call time, so a row cannot
  claim a stage it has not reached. **14 of 14 rows** now pass all six stages.
  Wired as `report pipeline`.
* **D3, and `glm_universal/integrity.py`.** A digest addresses integrity, never
  meaning. All SHA-256 use was moved out of the six core sub-packages into one
  module a level above them, so the rule is enforced by the code layout and the
  purity audit; the single digest that touches meaning is the labelled control
  of §11.3, which is measured to be chance-like.
* **D4, and `glm_universal/signoff/`.** Reuse a result only against a recorded
  digest of everything it depended on: the ledger computes a module's
  dependency closure from the source with `ast` (so hashing a module cannot
  execute it), digests it, and plans a run that re-executes only what changed.
* **`glm_universal/tools.py`.** Argument parsing, exit codes and the standard
  streams for these instruments live one module above the core, next to
  `figures.py`, so the core sub-packages stay free of process-level concerns
  and the purity audit stays easy to trust.

An audit added with §11.3 checks something nothing else could: every `GLM.…`
Lean name cited anywhere in the Python package must resolve to a real
declaration or namespace of the corpus. It found two stale citations, both
corrected.

### 11.5 The measured result

| instrument | result |
|---|---|
| capability probes | 33 probes: 20 hold, 13 break, 0 errored, 0 surprises |
| benchmark suites | 2,389 / 2,390 tasks across 5 suites; every suite above baseline |
| end-to-end CLI evaluation | 102 cases, **102 passed** — 93 correct, 9 refused as expected (9 boundary, **0 gap**), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| pipeline board | 14 of 14 rows complete |
| test suite | 2,183 tests across 50 test files, 9,088 subtests, zero failures |
| Lean development | 35 files, 9,213 lines, `lake build` clean, **0 `sorry`** |

---

## Phase 12 — the sign-off ledger made sound, and every instrument in it

The previous phase built `glm_universal/signoff/`: a test file is *signed off*
when it has passed and nothing it depends on has changed since, where the
dependency set is computed with `ast` rather than declared. The saving is real
— the suite is about a quarter of an hour and a typical iteration touches one
module — but as first built the ledger had a hole and a gap, and this phase
closes both. Neither is a matter of speed: the hole was a **wrong answer**
waiting to happen.

### 12.1 The hole: a closure of imports only — **closed**

`unit_closure` walked imports through the package, added the `_data`
directories and the test scaffolding, and stopped. But several of the units
whose whole purpose is to catch drift do not *import* the thing they check:

* `tests/test_figures.py` reads `STATUS.md`, `MASTER_PLAN.md`,
  `CAPABILITY_ASSESSMENT.md` and the READMEs and fails when a count in them
  has gone stale;
* `reasoning/pipeline.py` reads the study documents and the Lean sources to
  decide which of the six stages each study has reached;
* `reasoning/lean_address.py` reads every `.lean` file of the development.

None of that is an import, so none of it was in any digest — and the
consequence is exactly the failure mode a ledger must not have: **edit
`STATUS.md`, and the ledger would keep the document-drift test signed off.**
The saving would have been bought with a false statement.

The closure now also carries the documents and Lean sources a unit's modules
*name*. It is computed the same way everything else here is — each module in
the closure is parsed, its string constants are read, a constant naming a
document (`"MASTER_PLAN.md"`) pulls that document in, and a constant naming a
`.lean` file pulls in the whole Lean development together with `lakefile.toml`,
`lean-toolchain` and `lake-manifest.json`. A docstring that merely *mentions* a
document counts the same as a line that opens one, and a name that occurs more
than once (there are several `README.md`) pulls in every copy: over-hashing is
the safe direction (**D4**), because its cost is a needless re-run and the cost
of under-hashing is a wrong answer.

Measured on the real tree: `test_figures.py`'s closure is 200 files and holds
every document it checks; `test_substrate.py`'s holds no document at all, so
writing documents does not make the substrate tests stale. Six tests in
`tests/test_signoff.py` pin that, including the one that states the property
directly — editing `STATUS.md` makes `test_figures.py` stale and leaves
`test_substrate.py` signed.

The schema is bumped 1 → 2, which discards every signature written under the
old rule rather than trusting it. That is the rule's own consequence: the
sign-off package's sources are inside every closure, so changing what counts as
a dependency invalidates everything.

### 12.2 The gap: the ledger only covered pytest — **closed**

The suite is not the only thing the project re-ran from scratch every session.
`glm_universal/signoff/checks.py` makes the other instruments units of the same
kind — a name, a command, the directory it runs in, and a closure computed the
same way — sharing one ledger file under a separate key:

| instrument | what it runs | closure |
|---|---|---|
| `lean-build` | `lake build` | the Lean sources and the build files |
| `lean-sorry-free` | no `sorry` or `admit` in `RequestProject/GLM` | the Lean sources |
| `lean-copies-identical` | `diff -r` of the repository and overlay Lean trees | the Lean sources |
| `capabilities` | the 33 probes | the import closure of `capabilities/__main__.py` |
| `benchmarks` | the 5 benchmark suites | the import closure of `benchmarks/__main__.py` |
| `evaluation` | the end-to-end CLI evaluation | that of `evaluation/__main__.py`, plus `GLM.py` |
| `figures` | `figures --check` | that of `figures.py`, plus `FIGURES.md` |

The command itself is part of an instrument's digest, so changing what a check
runs invalidates its signature; a return code that counts as success is
declared per instrument, because `grep` reports 1 when it finds nothing, which
is the outcome `lean-sorry-free` wants. `--check` is new in `figures.py`: it
compares `FIGURES.md` with a fresh computation, prints a unified diff and exits
1 if they differ, so the check the suite performs is also available as a
command.

### 12.3 What it looks like from the outside

```bash
cd overlay
PYTHONPATH=. python3 -m glm_universal.signoff --plan            # both kinds
PYTHONPATH=. python3 -m glm_universal.signoff --run             # stale tests
PYTHONPATH=. python3 -m glm_universal.signoff --run-checks      # stale instruments
PYTHONPATH=. python3 -m glm_universal.signoff --run-everything
PYTHONPATH=. python3 -m glm_universal.signoff --verify          # no run at all
PYTHONPATH=. python3 -m glm_universal.signoff --closure test_figures.py
PYTHONPATH=. python3 -m glm_universal.tools signoff             # the summary
```

`--closure` now resolves an instrument's name as well as a test file's, and
prints repository-relative paths. `--run-all` and `--run-checks-all` ignore the
ledger entirely and remain what a release check runs. `python -m
glm_universal.tools signoff` is the read-only summary beside the other study
instruments: how much of the work is covered by a signature that still holds,
and how much would have to run.


---

## Phase 13 — a harmonic register, and the third of a claim it makes testable

`glm_study_findings_catalog.md` §6.2 claims that chemical equilibria, musical
harmony and market price discovery all map to proximity in the Leech lattice.
`reasoning/catalog.py` had carried that sentence as **not implemented** for
several rounds, for an honest reason: there was nothing musical or economic in
the package to run it against.  Of the three domains, music is the only one
that needs no measurement at all — an interval *is* a ratio of two integers —
so this phase builds it and puts the sentence to the test.  The write-up is
[`HARMONY_STUDY.md`](studies/HARMONY_STUDY.md).

### 13.1 The harmonic register — **done**

`data_objects/harmonics.py` is the seventh register: **28 intervals** as exact
rational frequency ratios — 18 just, 5 septimal, 5 commas, over prime limits 2,
3, 5 and 7.  All 24 coordinates of `HARMONIC_LAYOUT` are computed from the pair
`(n, d)` in lowest terms — the prime exponents, Tenney height `n · d`, Euler's
gradus suavitatis, the nearest equal-tempered step and the exact rational by
which it misses — and only `n` and `d` are needed to read the interval back, so
`IntervalCodec`'s round trip is exact and corrupting a derived coordinate
cannot change what is decoded.  Loaded by the runtime as `harmonics`; no float
is constructed anywhere in the register or in what reads it.

### 13.2 The study, and the control it has to beat — **done**

`reasoning/harmony.py`, wired as `report harmony`, computes five things
exactly.  The nearest equal step is decided by comparing `r^24` against powers
of two — integers, not logarithms — so the tempering error is the exact
rational `(n/d)^12 / 2^k`: `1` at the unison and the octave and nowhere else,
`531441/524288` at the fifth (the Pythagorean comma), `244140625/268435456` at
the just major third.  No stack of fifths is a stack of octaves, searched to
`n = 200`.  Tenney height and Euler's gradus are compared at an exact Kendall
tau of `313/378`.

Then the claim itself.  Each interval is decoded to its nearest Leech point
through a **tuning vector** — its exponents over 2, 3, 5 and 7 — deliberately
*not* through its register carrier, which holds `n · d` and the gradus outright
and would make the claim true by construction.  Swept over scales 1 to 32: at
scale 1 the lattice conflates fifteen of the 28 intervals onto the unison's own
point; from scale 4 every interval has its own point; and from scale 8 distance
from the unison orders them at tau `53/63` against Tenney height.

The verdict is decided by a third condition rather than by taste: the same
distance taken **before** the decoder runs.  That control scores `53/63` too,
and the decoder reorders **no pair at all**, so the claim is recorded as **not
reproduced** — what is measured is the prime-exponent vector, not the geometry
of the Leech lattice.  The confirming branch of the verdict is reachable, and a
test exhibits an input that takes it, so this is a measurement rather than a
foregone conclusion.

### 13.3 The claim ledger's §6.2, split — **done**

One sentence naming three domains cannot carry one verdict once two of them are
measurable and one is not: it would be either a pass the markets have not
earned or a gap the music does not deserve.  `reasoning/catalog.py` now carries
§6.2 as two claims — the musical half, whose verdict is read off
`harmony_report()` at call time rather than written down, and the economic
half, still `not implemented` because there is no register of prices.  The
ledger is **58 claims: 33 confirmed, 14 refuted, 7 not reproduced, 4 not
implemented**.

### 13.4 Why no tempering error can be zero — **done, machine-checked**

`RequestProject/GLM/Harmony.lean`.  A test pins 28 non-zero errors; this file
says why none ever could be zero.  `three_pow_ne_two_pow` is the kernel;
`fifth_never_closes` makes the circle of fifths not a circle for every `n`,
where the Python side only counts to 200; and
`odd_prime_ratio_ne_two_zpow` is the general obstruction — a ratio in lowest
terms carrying any odd prime is not a step of *any* equal division of the
octave, for every number of divisions at once.  `fifth_not_tempered`,
`major_third_not_tempered` and `harmonic_seventh_not_tempered` are the three
named corollaries; `pythagorean_comma_eq`, `syntonic_comma_eq` and
`fifth_tet_error` pin the exact residues the report quotes.

### 13.5 The measured result

| instrument | result |
|---|---|
| capability probes | 33 probes: 20 hold, 13 break, 0 errored, 0 surprises |
| benchmark suites | 2,389 / 2,390 tasks across 5 suites; every suite above baseline |
| end-to-end CLI evaluation | 103 cases, **103 passed** — 94 correct, 9 refused as expected (9 boundary, **0 gap**), 0 unexpected refusals, 0 confidently wrong, 0 errored |
| pipeline board | 15 of 15 rows complete |
| test suite | 2,308 tests across 51 test files, 9,165 subtests, zero failures |
| Lean development | 36 files, 9,410 lines, `lake build` clean, **0 `sorry`** |
