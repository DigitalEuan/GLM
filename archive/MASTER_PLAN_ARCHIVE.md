# Master plan — archive

*Moved into `archive/` from the repository root, where it was
`MASTER_PLAN_ARCHIVE.md`. Only the relative link prefixes were adjusted for the
new depth; no sentence and no figure was touched.*

The closed phases of [`MASTER_PLAN.md`](../MASTER_PLAN.md), kept exactly as they
were written.  Section numbers referred to elsewhere (for example
`MASTER_PLAN_ARCHIVE.md` §7.9) are the ones in this file.

<!-- figures:history -->

*Everything in this file is an archive: each phase records what was measured
when it was closed, and those counts are deliberately left alone.  For the
project as it is now, see [`MASTER_PLAN.md`](../MASTER_PLAN.md) and
[`overlay/FIGURES.md`](../overlay/FIGURES.md), which is regenerated from the code.*

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
[`INFINITE_VALUES_STUDY.md`](../studies/INFINITE_VALUES_STUDY.md).

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

The dynamic carrier of [`DYNAMIC_CARRIER_STUDY.md`](../source_material/DYNAMIC_CARRIER_STUDY.md)
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
[`GEOMETRIC_AMBIGUITY_STUDY.md`](../studies/GEOMETRIC_AMBIGUITY_STUDY.md), which also
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
[`ANALOGY_LAYER_STUDY.md`](../studies/ANALOGY_LAYER_STUDY.md).

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
renders [`overlay/FIGURES.md`](../overlay/FIGURES.md);
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
[`HARMONY_STUDY.md`](../studies/HARMONY_STUDY.md).

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

---

## Phase 14 — the layer chain made a real refinement, and the repository tidied

**Status: closed.**

### 14.1 The organisation pass

The repository root held eleven study write-ups, the supplied source material
and the documents that describe the project, all mixed together. The study
write-ups now live in `studies/`, the supplied material — archives, PDFs, the
original brief — in `source_material/`, and only `README.md`, `STATUS.md`,
`MASTER_PLAN.md`, `CAPABILITY_ASSESSMENT.md`, `PROJECT_DIRECTIVES.md` and the
new index `DOCUMENTS.md` remain at the root. Every link that moved was
repointed, including the ones the Python modules and tests quote:
`reasoning/pipeline.py` and `reasoning/directives.py` now look for a document
in `studies/` and `source_material/` as well as at the root, and
`tests/test_lean_address.py` names `studies/LEAN_ADDRESS_STUDY.md`. Compiled
bytecode was removed from the index and ignored. Two over-long documents were
split at the `<!-- figures:history -->` marker into companions that keep the
archive as written: `overlay/README_ARCHIVE.md` and `MASTER_PLAN_ARCHIVE.md`.
No module name, package structure, query surface or Lean file changed.

*What recomputes it:* the whole suite, `python3 -m glm_universal.tools
pipeline` (21 of 21 rows complete) and `tests/test_figures.py`, which reads
only the current-state half of each split document.

### 14.2 The refinement chain, decided and closed

`INFORMATION_LOSS_STUDY.md` had carried an open audit finding for several
rounds: run against the shipped layer definitions rather than an idealisation
of them, `refinement_chain_intact` was `False`, because the substrate's 24-bit
parity view separates a unit on coordinate 10 from the vacuum while an integer
layer reading only the seven SI7 exponents conflates them.

Two fixes were possible — widen the integer layer's view, or narrow the
substrate's. The project's own account of a layer is a cumulative ascent in
which no step loses anything earlier, so **widening** is what it commits to;
narrowing would buy the invariant by making the machine less able. The
reasoning is recorded in the study (§3.1), not in a commit message.

Carried through: `dimension_layers.LAYER_INTEGER` is cumulative over the
substrate, the Griess view carries the carrier beside the algebra element, and
the rejected narrow reading is kept beside the stack as `LAYER_INTEGER_RAW`
with its cost still measured. `RequestProject/GLM/LayerChain.lean` states and
proves the chain on the real 24-coordinate carriers, with no `sorry`:
`GLM.Info.glmChain_refines_of_le` is `refinement_chain_intact` as a theorem,
`GLM.Info.glmSi7Layer_not_refines_glmSubstrateLayer` is the defect as a
theorem, and `GLM.Info.glmIntegerLayer_separates_unitOutside` is the exact
carrier pair that exposed it. `tests/test_information_loss.py` grew a
`TestTheClosedRefinementDefect` class that fails if any part of this regresses.

**Measured after the change** (`report information loss`, 7 carriers):

| Layer | resolves | loses | addition descends |
|---|---|---|---|
| substrate | 3 / 7 | 4 | no |
| integer | 5 / 7 | 2 | no |
| rational | 7 / 7 | 0 | yes |
| griess | 7 / 7 | 0 | yes |
| universal | 7 / 7 | 0 | yes |

| Boundary | pairs gained | is a refinement |
|---|---|---|
| substrate → integer | 8 | yes |
| integer → rational | 2 | yes |
| rational → griess | 0 | yes |
| griess → universal | 0 | yes |

`refinement_chain_intact : True`. The rejected reading, measured beside it:
`LAYER_INTEGER_RAW` resolves 4 / 7, loses 3, and violates refinement on the
two pairs `(0,4)` and `(1,4)`.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report information
loss" -c 1`, `tests/test_information_loss.py`, and `lake build`.

---

## Phase 15 — the layer chain audited at register scale

**Status: step 1 of five closed; steps 2–5 open.**

### 15.1 Seven carriers were not a measurement

Phase 14 closed the refinement chain on the seven carriers of `report
information loss`, and each of those seven was chosen *because* it exhibited a
boundary. A stack that refines on carriers picked to make it refine has not
been tested. [`studies/RELATIVE_MEASURE_PROPOSAL.md`](../studies/RELATIVE_MEASURE_PROPOSAL.md)
§4 names running the audit on the registers themselves as the single
highest-value next step, and that is what `reasoning/escalation.py` does: one
carrier per named object of every register the package ships — physics 726,
chemistry 118, molecules 51, mathematics 22, harmonics 28, lexicon 95, **1,040
in all** — with nothing sampled.

The naive audit is quadratic in the carriers for resolution and quartic for
congruence, which at a thousand carriers is not affordable. It is not needed.
Every layer's measure here is a sum of non-negative exact terms that vanishes
exactly when a small reading of the two carriers agrees — parity bits at the
substrate, the SI7 exponents beside them at the integer layer, the exact
carrier at the three above. Grouping carriers by that **class key** replaces
both scans with one pass. The key is checked rather than trusted:
`key_agreement` re-derives every verdict from the layers' own `perceive` and
`measure` on an 18-carrier sample — 918 pairs, zero disagreements — and a test
deliberately breaks a key to confirm the check would notice.

### 15.2 What the registers said

| Layer | resolves (of 1,040) |
|---|---|
| substrate | 415 |
| integer | 544 |
| rational | 757 |
| griess | 757 |
| universal | 757 |
| *integer_raw (rejected reading)* | *359* |

| Boundary | pairs gained | is a refinement |
|---|---|---|
| substrate → integer | 5,883 | yes |
| integer → rational | 5,475 | yes |
| rational → griess | 0 | yes |
| griess → universal | 0 | yes |

**Zero refinement violations; `chain intact : True`** — the Phase 14 result
survives being asked a hundred and fifty times as many questions, and it was
not arranged to.

The scale-up also produced a result the seven carriers could not: a
**resolution ceiling**. 757 distinct carriers means **283 of the 1,040 named
entries share a carrier with another entry**, in **104 collision classes,
every one of them inside a single register** (275 physics, 8 mathematics); the
largest class is 78 dimensionless physics quantities (absorptance, albedo,
archimedes_number, …). No layer sees anything but the carrier, so no layer
separates them. What the machine is missing there is not resolution but a
coordinate for the name — which is what steps 2–5 of the proposal are about.
Addition still descends only to the three layers whose view is the carrier
itself, and the rejected `LAYER_INTEGER_RAW` reading, which cost one pair on
seven carriers, conflates **11,176** pairs the substrate already separates.

### 15.3 What holds however the registers grow

`RequestProject/GLM/Escalation.lean` proves the parts that are not
measurements, with no `sorry`: `GLM.Info.entryResolution_le_distinct` is the
ceiling (no layer resolves more entries than there are distinct carriers),
`GLM.Info.entryResolution_mono` is the order of the stack (a finer layer never
resolves fewer), `GLM.Info.glmRationalLayer_congruentOn` and its two
companions are addition descending on a lossless view, and
`GLM.Info.substrate_addition_not_congruent` is the half-unit witness for why
it does not descend below.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report escalation"
-c 1` (aliases: `report scale`, `report registers`, `report ceiling`),
`tests/test_escalation.py`, `lake build`, and the write-up
[`studies/ESCALATION_STUDY.md`](../studies/ESCALATION_STUDY.md).

### 15.4 What it left open, and where that went

Steps 2–5 of `RELATIVE_MEASURE_PROPOSAL.md` were left open by this phase and
are closed in Phase 16 below.

---

## Phase 16 — measure words as relative measures

**Status: closed.**

Steps 2–5 of
[`studies/RELATIVE_MEASURE_PROPOSAL.md`](../studies/RELATIVE_MEASURE_PROPOSAL.md),
of which Phase 15 was step 1. The write-up is
[`studies/RELATIVE_MEASURE_STUDY.md`](../studies/RELATIVE_MEASURE_STUDY.md).

### 16.1 The comparison-class register (step 3)

`data_objects/comparison_classes.py`: **45 comparison classes over 11
quantities** (temperature 6, length 5, mass 5, velocity 5, volume 5, density 4,
illuminance 4, force 3, luminous intensity 3, pressure 3, frequency 2), each an
exact bracket `[low, high]` in the SI base unit of its quantity with a typical
magnitude inside it, and **11 measure scales carrying 64 degree words** at exact
positions in `[0, 1]`. (The register was closed at 33 classes over 8 quantities
and grown to these in Phase 18; the figures here are the current ones, as the
head of this document requires.) Nothing dimensional is typed twice: the unit,
the dimension and the ten EXT10 exponents of a class carrier are read out of
the physics register at load time, and a class naming a quantity the register
does not hold fails to load. `ComparisonClassCodec` round-trips all 45.
`lexicon_agreement()` checks the 12 words the scales share with the semantic
lexicon — quantity, polarity side and opposite-pole sum — and reports
`agrees: True`, with `heavy` flagged as the one word whose polarity is the
neutral `1/2`.

### 16.2 The widening, measured (step 4)

`reasoning/measure_view.py` reads a word against a class as an exact rational —
*hot* in tea is **363 K**, *hot* for a stellar surface **44 000 K** — and
audits three views over the **56 uses** the registers admit (each of 12 words
against each of the 32 classes of its quantity):

| view | resolves | refines the static reading |
|---|---|---|
| `static` — the concept carrier | 12 / 56 | — |
| `measure` — the concept and the measurement | **56 / 56** | **yes**, gaining 108 pairs, 0 violations |
| `measure_only` — the measurement alone | 56 / 56 | **not in general** — see §18.1 |

The static view is checked against `dimension_layers`' rational layer on the
concept carrier over all 1,540 pairs rather than idealised.
`RequestProject/GLM/MeasureView.lean` states the same on `Cumulative.lean`:
`GLM.Info.measureLayer_refines_staticLayer`, `GLM.Info.measureLayer_least`,
`GLM.Info.boundary_measureLayer_staticLayer` with
`GLM.Info.hot_tea_star_mem_boundary` for non-emptiness,
`GLM.Info.measureReading_not_refines_staticLayer` for the rejected
replacement, and `GLM.Info.magnitude_strictMono` for the scale order.

### 16.3 The `related_to` residue (step 2)

**27 of the 66 `related_to` triples** are converted by the physics register
alone — 6 `same_dimension_as` and 21 `differs_by`, each naming the basis
quantity that carries one dimension to the other — and the remaining **39**
are reported with the reason each was declined. An attribution that could be
made in more than one way is refused rather than guessed. (15 and 51 when the
phase closed, over a 13-quantity factor basis; `basis_sweep` then measured what
every other candidate would do and grew the basis to 16 — §18.2.)

### 16.4 The query, and its tested refusal (step 5)

`measure` is a query kind of its own: `measure hot in tea` (an exact
magnitude), `measure hot` (the same word against every class of its quantity)
and `measure 300 in tea` (the inverse reading). It **refuses** at the
boundary — `measure large in room`, `measure dark in room`,
`measure hot in walking`, `measure expensive in market` — and
`GLM.Info.boundary_empty_of_unmeasured` says the refusal is forced by the
registers rather than missing from the code. All four refusals are exercised,
as unit tests and as `boundary` cases in the end-to-end evaluation.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report measure" -c 1`
(aliases: `report measure words`, `report measure view`,
`report relative measure`, `report comparison classes`, `report scales`),
`tests/test_comparison_classes.py`, `tests/test_measure_words.py`,
`python3 -m glm_universal.evaluation --only measure`, and `lake build`.

### 16.5 What it left open

Two items, both closed in Phase 18: `large`, `small` and `dark` named
quantities — *size*, *light* — the physics register did not hold, so 3 of the 12
lexicon adjectives had no measurement; and there was no comparative query
(`hotter_than`, `as_hot_as`), although `GLM.Info.above_on_magnitude_lt` already
proved the scale order survives into magnitudes.

---

## Phase 17 — the last third of the universality claim, the address layer
## audited, and the infinite-dimensional half of the VOA bridge

**Status: closed.**

Three items that had each been named as untouched, and one gap found while
auditing.

### 17.1 An economic register (`report economics`)

`data_objects/economics_register.py` is the eighth register: **21 quoted
prices** as exact rationals — seven instruments over three consecutive
quarters, four sectors, six currency pairs — every price stored as a fraction
of integers in the shipped CSV and read as a `Fraction`, never as a float, and
every non-currency instrument naming a physical denominator.

The magnitude a price is read through is `⌊log_b x⌋` computed **without a
logarithm**: `k` is the unique integer with `b ^ k ≤ x < b ^ (k + 1)`, decided
for `x = p / q` by integer multiplication alone.
`RequestProject/GLM/LogBucket.lean` is the specification of that function —
`bucket_spec` and `bucket_unique` (hence `exists_unique_bucket`),
`le_iff_num_le` for the comparisons the code performs, `bucket_mono`,
`mantissa_mem_Ico`, `bucket_zpow` and `mantissa_zpow_eq_one` — together with
`distSq_smul` and `order_preserved_by_scaling`, which are what make the study's
control a single set of numbers rather than one per scale.

`reasoning/economics.py` (`report economics`) then measures the catalogue's
§6.2 sentence for markets. Decoded through buckets, mantissas, EXT10 exponents
and a currency flag, the lattice first separates **all 21 records at scale
1024**, orders them by magnitude at an exact tau of `39/70`, and **every
record's nearest neighbour is another quarter of the same instrument — 21 of
21 against a chance rate of `1/10`**. The verdict is nevertheless
**`not reproduced`**, because the undecoded control scores 21 of 21 as well:
what is measured is the price vector, not the geometry of the lattice. That is
the same answer the musical third reached by the same instrument, and the
agreement across two unrelated domains is itself the finding.

Section 6.2 of the catalogue ledger now reads **both** halves off their studies
at call time; neither is carried as `not implemented`. The write-up is
[`studies/ECONOMICS_STUDY.md`](../studies/ECONOMICS_STUDY.md), and both the
economic and the harmonic registers are describable through the CLI, which
closed a pre-existing gap where the harmonic register could not be described
at all.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report economics" -c 1`
and `--verify-tct`, `tests/test_economics.py` (28 tests),
`python3 -m glm_universal.evaluation --only report`, and `lake build`.

### 17.2 The hexcolour address layer, audited (`report state migration`)

A hexcolour is the six-hex-digit rendering of a 24-bit carrier, one digit per
four coordinates: an address in the sense of directive D3 and nothing more.
The layer existed and was displayed; what it lacked was a measurement that it
does its job on the shipped data. `report state migration` now carries a sixth
step that supplies one: **4,680 concepts carry an address, all 4,680 distinct
(zero collisions), zero fail to read back to their own mask, zero disagree
with the mask stored beside them, zero fail to commute with the
legacy-to-core relabelling**, and the **15** legacy per-task addresses the
supplied ARC pipeline left behind are all Golay codewords and all round-trip.

The audit also found a real gap: nothing ever looked anything *up* by an
address, which is weaker than the word claims. The concept store now has
lookup by address, and every one of the 4,680 concepts is tested to round-trip
through it. One stale figure was annotated rather than deleted — the legacy
ARC-AGI results block says "66 hexcolour addresses" where the shipped table
holds 15, so it is kept as the upstream run's own count with a correction
beside it. The write-up is
[`studies/HEXCOLOUR_STUDY.md`](../studies/HEXCOLOUR_STUDY.md).

*What recomputes it:*
`PYTHONPATH=. python3 GLM.py -q "report state migration" --verify-tct`
(`VERIFIED True`) and `tests/test_state_migration.py`.

### 17.3 The infinite-dimensional half of the VOA bridge

`VOA.lean` had proved what the finite Griess layer carries and, in
`borcherds_commutator_fails`, exactly where it stops. `Heisenberg.lean` builds
the half past it: the Fock space of one free boson over the exact rationals,
`V = MvPolynomial ℕ ℚ`, with creation, annihilation and mode operators, and
proves

* `mode_commutator` — `⁅aₘ, aₙ⁆ = m δ_{m+n,0} · id`, for all integers at once;
* `mode_truncated` — every state is annihilated by all sufficiently high
  modes, so the field is a genuine formal Laurent series;
* `borcherds_commutator` — the same bracket in Borcherds' own form, its tail
  vanishing by `alpha_mode_eq_zero_of_two_le`;
* `no_finite_dimensional_model` — the obstruction, in general: in
  characteristic zero no pair of endomorphisms of a nonzero
  finite-dimensional space satisfies `⁅A, B⁆ = c · id` with `c ≠ 0`, because
  the trace of a commutator is `0`; hence `fock_infinite_dimensional`, and
  `griess_layer_discards_nonzero_modes` names the discarded modes that do the
  damage.

That is the precise sense in which the finite layer cannot be the whole story:
stated and proved rather than asserted. The file is `sorry`-free and depends
only on the standard axioms.

*What recomputes it:* `lake build`.

### 17.4 What it left open

Nothing new. The remaining open items are the ones §3.2 and §3.3 of
[`STATUS.md`](../STATUS.md) name: the `O(1)` LLVQ table, the Niemeier deep-hole
census, the two lexicon quantities the physics register does not hold and the
comparative query (both closed since, in Phase 18), open vocabulary as a stated
commitment, and the two ongoing residues (`related_to`, sparse chemistry).

---

## Phase 18 — the two items Phase 16 left open, and a factor basis measured
## instead of asserted

**Status: closed.**

Phase 16 closed with two open items — three lexicon adjectives naming
quantities the physics register did not hold, and no comparative query. Both
are closed here, and closing the first one exposed a third thing worth doing.

### 18.1 The register grown, and the replacement's cost kept measurable

`data_objects/comparison_classes.py` gained **volume**, **illuminance** and
**luminous intensity**: 33 classes over 8 quantities → **45 over 11**, 8 scales
carrying 47 degree words → **11 carrying 64**, and the lexicon overlap 9 words
→ **12**. All **12** of the lexicon's adjectives are now measurable, `large`,
`small` and `dark` among them, and the audit runs over **56 uses** instead of
45: the static reading resolves 12 of them, the widened reading all 56, gaining
**108 pairs** with **0** refinement violations.

That growth removed the shipped data's own refutation of the *replacement*
reading — keep the measurement, drop the concept — which used to fail on
exactly the three unmeasurable words. Rather than let the argument lapse into
an assertion, `replacement_witness()` re-runs the audit over the 56 uses plus
**one unmeasured use of each of the 12 words**, which is the case that arises
the moment a word's quantity is not in a register. Over those **68 uses** the
widening gains **164 pairs** with **0** violations and the replacement gains
the same 164 while **violating refinement on 66**. The general statement is a
theorem, not a measurement: `GLM.Info.measureReading_not_refines_staticLayer`.

### 18.2 The factor basis, swept rather than asserted

`measure_view.FACTOR_BASIS` carried a comment claiming that widening it
converts nothing and only adds ambiguity. `basis_sweep()` tests that claim by
offering **every** quantity the physics register holds as a candidate: of
**713**, **571** change nothing, **125** would make some attribution ambiguous
and are refused, and **17** strictly convert more. Those 17 occupy only **four
dimensions** — the ohm, its reciprocal the siemens, the joule per kelvin and
the radian per metre — and the first two decide the same triple, so the data
decides **three** factors. The basis is 13 → **16** (`resistance`, `entropy`,
`angular_wavenumber`), kept in a separate tuple so the sweep can put it back
and measure the growth rather than assert it, and the comment now states what
was measured. `related_to` conversion moves 15 → **27** of 66 (6
`same_dimension_as`, 21 `differs_by`), residue 51 → **39**, of which exactly
one is declined for having no single basis factor and the rest for an endpoint
that reaches no dimension at all. A dimension is what decides a triple; the
*name* is a choice, and the sweep reports the whole class of names beside each
so the choice stays visible.

### 18.3 The comparative (`hotter than`, `as hot as`)

A comparative is a relation between two **uses**, not between two words, which
is why the static reading cannot answer one and why Phase 16 left it out. It is
now a query kind of its own, `comparative`, recognised structurally in
`runtime/parser.py` — `is <word> in <class> hotter than <word> in <class>`, and
the equative `as <word> as` — with the direction read off the degree word's
position relative to the midpoint of its scale, and a word *at* the midpoint
refused rather than guessed at.

**Measured** by `comparative_audit()`: of the 56 uses, **228 pairs** are
comparable; within one class the word order decides **24 of 24**, and across
classes it gets **151 of 204** backwards — so the comparison class is what
decides the majority of comparable pairs. `is cold in stellar_surface hotter
than hot in tea` is **yes**, `8000 K` against `363 K`, with the two words in the
opposite order on the scale.

`RequestProject/GLM/Comparative.lean` proves the part that is not a
measurement: `hotterThan_trichotomy` (a strict order, trichotomous where
defined), `hotterThan_iff_position_lt` (within one class the word order decides
it exactly), `comparative_not_determined_by_word_order` (across classes it does
not), `comparative_not_static` (no widening-free reading can answer it),
`hotterThan_congr` (the widened view can), and
`not_comparable_left_of_unmeasured` with `hotTea_not_comparable_fastWalking`
(the two refusals are forced by the registers).

*What recomputes it:*
`PYTHONPATH=. python3 GLM.py -q "report measure" --verify-tct`,
`PYTHONPATH=. python3 GLM.py -q "is cold in stellar_surface hotter than hot in tea" -c 1`,
`tests/test_comparison_classes.py`, `tests/test_measure_words.py`,
`tests/test_comparative.py`, `python3 -m glm_universal.evaluation`, and
`lake build`.

### 18.4 What it leaves open

The measurable vocabulary is still a register: a thirteenth adjective naming a
twelfth quantity would be unmeasurable again, which is the case
`replacement_witness()` keeps measured. The comparative relates two uses of
degree words the register holds and nothing wider. Otherwise the open list is
unchanged — §3.2 and §3.3 of [`STATUS.md`](../STATUS.md).

---

## Phase 19 — the residue finished as a vocabulary decision

**Status: closed.**

The first of the two items [`STATUS.md`](../STATUS.md) §3.4 named. The write-up is
[`studies/DENOTATION_STUDY.md`](../studies/DENOTATION_STUDY.md).

### 19.1 The search, exhausted before any word was decided

The residue was already split — 27 of the 66 `related_to` triples convert from
the physics register alone (6 `same_dimension_as`, 21 `differs_by`), and each
of the 39 that remain reports why. **38 of those 39 declined for the same
reason**: an endpoint reaches no dimension the register holds. Before deciding
any word by hand, `basis_sweep()` establishes that the automatic half is
finished: every one of the **713** quantities the register holds and the factor
basis did not is offered in turn, **571** change nothing, **125** would make an
attribution ambiguous and are refused, and the **17** that strictly convert
more occupy only **four dimensions**, two of which decide the same triple — so
the data decides three factors, and the basis stands at 16. What is left is a
vocabulary question, and the lexicon's own part of speech says so: of the 38,
**11 are verbs, 21 nouns and 6 absent from the lexicon**.

### 19.2 The register of decisions, and what the decisions changed

`data_objects/denotation.py` decides the residue's **36** undimensioned
endpoints one name at a time, each with its written justification, under six
verdicts: **1 `quantity`, 3 `ambiguous`, 4 `polymorphic`, 9 `carrier`, 11
`process`, 8 `abstraction`**. Only `quantity` makes a name dimensional, and it
supplies no coordinate — *gravity* is the register's own `gravitational_field`
under an ordinary-language spelling, exactly as an alias is, and
`denotation_audit()` refuses an entry that names a quantity the register does
not hold, shadows one that it does, or carries no justification (`sound:
True`).

`reasoning/denotation_view.py` is the second pass, and measures what the
decisions change:

| outcome | triples |
|---|---|
| converted to a dimensional relation | **0** |
| repaired to `names_process_of` | 6 |
| declined, now by what the endpoint *is* | 33 |

Zero conversions is the result rather than a disappointment: deciding what a
word denotes is not a way of manufacturing relations, and *gravity*'s own
triple still declines — now for the other reason, no single basis factor
between a gravitational field and a mass. Coverage is exact in both directions
(36 needed, 36 decided, **0 undecided, 0 idle**), and what is earned is
`closure`: **39 of 39 accounted for, 0 triples waiting on a lookup**. A
`carrier` beside a dimensioned endpoint is deliberately *not* repaired the way
a `process` is — a magnet bears a flux density and a photon does not bear an
illuminance — because a rule that is right half the time is a guess.

The conversions carry: of the **22** analogies the 27 repaired triples license,
**12** are answered and 10 refused, where the unrepaired control answers **1**.

`RequestProject/GLM/Denotation.lean` states the part that is not a measurement,
with no `sorry`: `reach_invents_nothing` (a decision cannot extend the
register), `secondPass_eq_firstPass_of_decided` (a decision never revises a
measurement), `secondPass_eq_firstPass_of_no_quantity_verdict` (the measured
`converted = 0`), `undecided_is_decided` (the closure claim) and
`repaired_not_converted` (the three outcomes partition the residue), with the
*gravity*, *motion* and *move* cases instantiated at the end.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report denotations"
-c 1` (aliases: `report denotation`, `report residue`, `report related_to`,
`report vocabulary`), `tests/test_denotation.py`, and `lake build`.

### 19.3 What it leaves open

The verdicts are judgements, and a lexicon that grows a new vague triple grows
a new one to make; the audit checks their form, never their content. The
second item §3.4 named — the recipe made into an object — is Phase 20 below.

---

## Phase 20 — the recipe made into an object

**Status: closed.**

The second of the two items [`STATUS.md`](../STATUS.md) §3.4 named. The write-up
is [`studies/RECIPE_STUDY.md`](../studies/RECIPE_STUDY.md).

Every capability in this plan was built by hand from one recipe: a **register**
of carriers whose coordinates derive from something already held; a **reading**
— a layer — over them; an **audit** of what the reading gains and whether it
gives anything up; a **query kind** that answers where the registers decide and
refuses where they do not; and a **machine-checked statement** of the part that
is not a measurement. Comparison classes (Phase 16), harmonics (Phase 13),
prices (Phase 17) and the comparative (Phase 18) are all that recipe, and each
application paid for its own carrier method, codec, audit, report subject and
parsing rule.

This phase makes the recipe's *input* an object, and is therefore
**subtractive**: what it produces is one declarative description of a domain
and a single generic path from such a description to everything the recipe used
to build by hand.

### 20.1 The description, and what it is written in

`recipe/spec.py` holds a `DomainSpec`: what the domain's objects hold, one
derivation rule per coordinate, which coordinates recover the object, the named
selections that make up the layer chain, and what must be refused. A
coordinate is either a **derivation** — one of **25 shared primitives**, which
compose, so `log_bucket(quotient("high", "low"), base=10)` is an ordinary
coordinate — or a **judgement** the domain has to state for itself, marked as
one so that it can be counted rather than hidden. Every value is an `int` or a
`Fraction`; no float is constructed anywhere on the path.

`recipe/descriptions.py` writes down three domains built by hand in earlier
rounds and nothing else — no carrier, no codec, no audit:

| domain | objects | coordinates | derivations | judgements | readings |
|---|---|---|---|---|---|
| comparison | 45 | 24 | 24 | 0 | `bracket` (2) → `measured` (9) → `full` (24) |
| harmonics | 28 | 24 | 18 | **6** | `ratio` (2) → `arithmetic` (14) → `full` (24) |
| economics | 21 | 24 | 24 | 0 | `price` (2) → `magnitude` (7) → `full` (24) |

**72 coordinates, 66 derivations, 6 judgements** — and the six are exactly the
musical conventions: Euler's gradus weighting a prime by `p − 1`, twelve-tone
equal temperament as the tuning a step is measured against, the error against
it, the harmonic and subharmonic readings of a power of two, and what counts as
a comma. That is the shape this plan predicted: what does not generalise is the
judgements, and a description makes them countable instead of invisible. Of
the 25 primitives, 23 are used — `held` by every domain, 7 by two or more, 16
by one, and `collection_size` and `minimum` by none, reported as unused rather
than deleted.

### 20.2 The one path, and the audit it runs

`recipe/build.py` knows nothing about any domain. From a description it
produces the carrier encoding (24 coordinates, each derived), the read-back,
the readings as layers in the sense of `Layers.lean`, the widening audit and
the query surface with its refusal boundary.

| domain | chain | classes | pairs gained | read-back | named refusals refused |
|---|---|---|---|---|---|
| comparison | refinement chain | 42 → 43 → 45 | 1, then 2 | 45 / 45 | 3 / 3 |
| harmonics | refinement chain | 28 → 28 → 28 | 0, then 0 | 28 / 28 | 3 / 3 |
| economics | refinement chain | 21 → 21 → 21 | 0, then 0 | 21 / 21 | 3 / 3 |

The comparison chain is the one that does work — the bracket alone conflates
`room_volume` with `household_lamp`, and two further pairs, `ship` against
`ocean_depth` among them, are split only by the full reading. The other two
gain nothing because their narrowest reading already separates every object,
which the audit *reports* rather than assumes.

### 20.3 The measured result — three domains regenerated

`build.regeneration` deletes each domain and rebuilds it from its description,
comparing the carriers against the shipped ones coordinate by coordinate, the
objects rebuilt through the read-back against the register's own, and the
figures the reasoning modules measure with the regenerated register installed
in the shipped one's place:

| | carriers identical | objects agree | figures unchanged |
|---|---|---|---|
| comparison | 45 / 45 | yes | 4 (+1 exhaustive) |
| harmonics | 28 / 28 | yes | 3 (+1 exhaustive) |
| economics | 21 / 21 | yes | 2 |
| **total** | **94 / 94** | **yes** | **9, and 11 with the exhaustive two** |

Verdict: `regenerated`, 3 of 3 domains, which is the test this phase set — not
that the path works on something new, but that domains built by hand can be
deleted and come back with their measured figures unchanged.

### 20.4 The query surface, and the part that is not a measurement

`derive <coordinate> of <object>` is the twenty-first query kind and is
answered off whichever description derives the coordinate, so a fourth
description costs no new parsing rule: `derive span_ratio of tea` is `373/293`
by the shared `quotient` primitive, `derive numerator of perfect_fifth` reaches
a second domain, `derive euler_gradus of perfect_fifth` is `4` and is reported
as a **judgement**, and `derive cents of perfect_fifth` is refused — a cent is
a logarithm, so no description derives it.

`RequestProject/GLM/Recipe.lean` states the path itself, with no `sorry`:
`readingOn_mono` (widening gives nothing up) with `readingOn_append_least` (it
adds nothing beyond keeping both), `boundary_readingOn_nonempty_iff` (what a
widening gains is exactly the pairs it splits), `lossless_full_of_keys` and
`rebuild_encode` (keys give a lossless carrier with an exact inverse),
`answer_eq_none_iff` (the refusal boundary, decidable and read off the
description) and `encode_congr` / `indist_congr` / `answer_congr` —
regeneration stated formally: two descriptions agreeing on the coordinates
agree on the carriers, on the reading and on every answer. `ratioSpec`
instantiates all of it on an interval as an exact ratio, where the Tenney
height alone is shown *not* to be a reading of the domain and `cents` is
refused.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report recipe" -c 1`
(aliases: `report recipes`, `report descriptions`), the four `derive` cases of
the CLI evaluation, `tests/test_recipe.py`, and `lake build`.

### 20.5 What it leaves open

Three domains are described, not eight: physics, chemistry, molecules,
mathematics and the lexicon are still hand-written, and nothing measured here
says they can be described. The judgements are counted, not removed — and
should not be. A description is trusted about its own facts, since `facts()`
reads the shipped register, so what is re-derivable is the coordinates rather
than the data. The limit this phase named for itself — the surface language
still being a hand-written phrase — is what Phase 21 below closed.

---

## Phase 21 — the surface language driven off the descriptions

**Status: closed.**

The remaining item of [`STATUS.md`](../STATUS.md) §3.4, and the limit Phase 20 ran
into head-on. The write-up is
[`studies/LANGUAGE_STUDY.md`](../studies/LANGUAGE_STUDY.md).

Phase 20 made the *domain* declarative: a description yields the carriers, the
readings, the audit, the query surface and the refusal boundary with no code of
its own. What it did not make declarative is the **way a question is asked**.
`derive <coordinate> of <object>` is generic in the coordinate and in the
object, but it was still one hand-written phrase in `runtime/parser.py`, and so
are `measure`, `comparative`, `meaning` and every `report <subject>` alias. A
new domain therefore arrived with its carriers, its readings and its refusals,
and then waited for a branch of the parser before anyone could ask it anything.

This phase writes the question down. Its input is a **question description**
beside the domain description; its output is one generic matcher from such a
description to a query kind and its options. Like Phase 20 it is
**subtractive** in intent and comparative in method: the shapes restate surface
the parser already accepts, and the measurement is whether the two agree.

### 21.1 The description, and what a shape is made of

`language/question.py` holds a `QuestionSpec`: the `kind` a match produces, a
`gloss`, a `shape` and the named `refusals`. A shape is an **opening**, then
named **slots** separated by literal **phrasings**, with an optional tail.

A `Phrasing` is a set of surface forms that count as the same thing here, held
longest-first so `derivation of` cannot be shadowed by `derive`, and it cannot
be constructed without a `why` — the sentence that justifies treating those
forms as one set. A `Slot` is a named hole with a role (`coordinate`, `object`,
`domain`, `subject`, `class`, `task`), a flag for whether it may be left out and
a flag for whether leading articles are kept; slots are named after the option
keys the runtime already uses, so a match becomes a query's options by a
dictionary comprehension rather than by a per-kind rule. That is what makes the
matcher generic rather than a switch with three arms.

A shape must **open with a phrasing**, at the head of the string, never on a
keyword found somewhere in the middle: `__post_init__` refuses a shape that does
not, one with a duplicate slot name, and one with no slot at all.

### 21.2 The three descriptions, and why not the other seventeen

`language/descriptions.py` holds them and nothing else — no matching, no kind
special-cased:

| kind | slots | openings | separators | judgements | boundaries |
|---|---|---|---|---|---|
| `derive` | coordinate, object, domain? | 5 | 3, then 1 | 3 | 3 |
| `measure` | subject, class? | 5 | 5 | 2 | 1 |
| `task` | task | 4 | — | 1 | 1 |

**6 slots, 44 surface forms, 6 judgements, 5 named boundaries, 14 openings.**
Each opening is exactly the set of forms `runtime/parser.VERBS` maps to that
kind and each separator exactly the set that branch of `parse_query` splits on,
so the descriptions restate the shipped surface rather than extending it —
which is what makes §21.3 a comparison rather than a demonstration.

Three of the runtime's twenty answerable kinds are *an opening then slots
separated by literal words*. The rest are not, and are left hand-written rather
than forced: `analogy` is an infix operator, `verify` a top-level `=`,
`comparative` a suffix whose two sides must each resolve to a measured use,
`compare` a keyword splitting the original string rather than a remainder, and
`describe` a bare concept name resolved in the register index. A description
language able to express those would be a parser generator; this one describes
one shape, and saying so makes **3 of 20** a measurement of that shape's reach
rather than an apology.

What does **not** generalise is counted, as in Phase 20: the six judgements are
the decisions about English — that the five `derive` openings are one opening,
that `of`, `for` and `on` all attach a coordinate to its object, that the domain
tail admits `in` and nothing else, that the five `measure` openings are one, the
five ways of naming what a measure word is read against, and `puzzle` counting
as `task`.

### 21.3 The measured result — agreement, and the false-positive half

`build.corpus()` generates a question for every opening crossed with every
separator over the coordinates, objects, measure words and tasks the registers
actually hold, and `build.agreement()` puts each to *both* parsers. Agreement
means the same kind **and** the same options.

| what is compared | result |
|---|---|
| generated questions, described matcher against `parse_query` | **692 / 692 agreed** |
| by kind | derive 360, measure 320, task 12 |
| declined by the matcher where the parser answered | **0** |
| answered with a different kind or different options | **0** |
| verdict | `exact` |

A matcher that answered everything would agree on that corpus and be useless,
so the other half is measured too. `build.other_kind_questions()` takes the
question string of every evaluation case whose kind is not described — 114 of
them across the seventeen undescribed kinds — and puts each to the matcher:

| what is measured | result |
|---|---|
| questions of undescribed kinds put to the matcher | 114 |
| matched anyway | **0 false positives** |

Every named boundary is given a witness, so a limit is reachable rather than
claimed (`derive`: `no_separator`, `empty_coordinate`, `empty_object`;
`measure`: `empty_subject`; `task`: `empty_task` — **5 of 5** reached, none
undescribed and none unreachable), and writing is checked to be inverse to
matching: `build.round_trip()` writes every question of the corpus back from
the slots it filled and re-matches it, **692 / 692 returning the same filling**.
The three shapes are a set rather than a priority list because
`build.openings_disjoint()` finds **0 clashes among the 14 openings**.

One caveat is stated rather than buried: the matcher requires its opening at the
**head** of the question, where the shipped parser will find a verb anywhere in
the token stream. That is a difference in surface reach, not in reading, and it
is the thing Phase 22 has to settle first.

### 21.4 The part that is not a measurement

`RequestProject/GLM/Question.lean` models the shape at the level of tokens —
`Phrasing`, `Slot`, `Piece`, `Spec` and `matchPieces`, the same five rules the
Python matcher runs — and proves what the audits above can only sample:
`matchPieces_rendered` (the round trip, for all questions rather than 692 of
them), `matchPieces_required_nonempty` (no silent empty slot, so a refusal is
the only way an unnamed thing leaves the matcher), `matchPieces_adjacent_holes`,
`matchPieces_no_separator` (the `no_separator` boundary as a theorem),
`matchPieces_lit_none` and `matchPieces_not_both` with
`Phrasing.not_both_matchAt` — disjoint openings decide the shape, which is what
makes the descriptions a set. `deriveShape` instantiates all of it on the
shipped `derive` description and four theorems are settled by `decide`. The
file carries no `sorry` and no non-standard axiom.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report language" -c 1`
(aliases: `report question shape`, `report surface language`), the
`report-language` case of the CLI evaluation, `tests/test_language.py`, and
`lake build`.

### 21.5 What it leaves open

Three kinds are described, not twenty, and nothing measured here says the other
seventeen can be described by *this* shape — for four of them the way they are
actually recognised shows they cannot. The shipped parser is still the one that
runs: the descriptions are measured *against* `parse_query`, not in place of it.
The judgements are counted, not removed. The opening must lead. And a
description is trusted about its own vocabulary, since the openings come from
`VERBS` and the separators from the branch they restate — so what is shown
describable is the *shape*, not the word list. The first two of those are
Phase 22, closed below.

---

## Phase 22 — the branches deleted, and a second shape family

**Status: closed.**

The two items of [`STATUS.md`](../STATUS.md) §3.4 as it stood after Phase 21, both
settled.

### 22.1 The leading remainder, described rather than allowed

Phase 21 could not delete the branches because of one measured difference: the
described matcher wanted its opening at the **head** of the question, and the
shipped parser found its verb anywhere in the token stream, so
`please measure hot in tea` was answered there and declined here.

Phase 21 named the two honest ways out — describe the leading remainder, or
narrow the surface and record the narrowing. This phase does **both**, because
they turn out to be the same act done carefully. A `Preamble` is an ordered
list of word families that may be skipped before the opening, each a `Phrasing`
carrying its own justification:

```
(i would like to know | i want to know | can you | could you |
 would you | kindly | please)*      ← repeatable: the parser stripped these in a loop
(tell me about | what is | address | explain | profile)?
                                    ← once: the parser stripped one opener
```

`repeatable` reproduces the shipped behaviour exactly — a loop for the fillers,
one strip for the opener — and the *order* is part of the description, so
`what is please derive …` stops at `please` and is refused.

Letting the opening float free instead would have accepted anything before it,
and the hand-written parser demonstrably mis-read such questions.
`build.narrowing()` measures the trade with five stray openings the preamble
does not admit (`the tea`, `give me`, `run`, `in tea`, `what is please`)
written in front of a question of each shape:

| what is measured | result |
|---|---|
| stray openings × shapes | **15 witnesses** |
| declined by the descriptions, at `unrecognised_opening` | **15 / 15** |
| answered by the branches | **15 / 15** |
| …with the stray words coming back *inside an option* | **15 / 15** |

So the narrowing gives up exactly the questions the branch got wrong. The two
preamble pieces are two more judgements on every shape that uses them, which
takes the reported figure from **6 to 12**.

### 22.2 The branches, deleted

The three `if kind == "derive" / "measure" / "task"` blocks are gone from
`runtime/parser.py`, replaced by

```python
if kind in DESCRIBED_KINDS:
    return _described_query(kind, remainder, question)
```

`_described_query` matches the remainder against the shape, turns the filling
into the query's options, maps a boundary the description marks `raises` to a
`QueryError` and any other boundary to empty slots, and answers
`kind="unknown"` where the opening is not recognised. No per-kind code remains
in that path.

That creates a measurement problem, and it is solved rather than ignored: the
descriptions can no longer be measured against the parser, because for these
kinds the parser *is* the descriptions. The deleted code is kept verbatim in
`language/legacy.py` — imported by the measurement and by nothing in the
runtime — and the corpus is widened with fourteen admitted decorations so the
preamble is exercised too:

| what is compared | result |
|---|---|
| generated questions, descriptions against the **deleted branches** | **846 / 846 agreed** |
| by kind | derive 416, measure 362, task 68 |
| declined, or answered with a different kind or different options | **0, 0** |
| questions written back and re-matched | **846 / 846 return the same filling** |
| evaluation questions of the kinds the slot shapes do not cover | **114 put, 0 matched** |

The subtractive test Phase 22 set itself is met: the end-to-end evaluation
returns **130 / 130** with the same 16 expected boundary refusals and no gap.

### 22.3 Is a second shape worth having?

Phase 21's other item was deliberately falsifiable: *if two shapes cover seven
kinds, the description language is worth extending; if a second shape covers
one kind, it is a parser generator being written one kind at a time.*

The second shape covers **three** — `verify`, `analogy` and the relational half
of `compare`. `language/infix.py` describes an operator that cuts a *string*,
which is a genuinely second primitive rather than the first one rearranged: a
slot shape walks tokens, and an infix operand is a notation (`sqrt(2)`,
`mass * acceleration`), which is not a run of words.

| kind | shape | operands | judgements |
|---|---|---|---|
| `verify` | `(does it hold that \| is it true that \| audit \| check \| verify)? <lhs> = <rhs>` | lhs, rhs | 3 |
| `analogy` | `<a> : <b> :: <c> : <d>?` | a, b, c, d | 3 |
| `compare` | `(are \| do \| does \| is)? <left> (…seven relations…) <right>` | left, right | 3 |

Three things a slot shape cannot say are said here: an operator alternative may
carry a **meaning** (`bigger than` and `smaller than` are the same shape asking
opposite questions); an **inner** operator cuts each side again, which holds
the analogy's four terms in one description; and an operand may be **described
but not carried**, the analogy's fourth term being the hole the answer fills.

| what is compared | result |
|---|---|
| generated infix questions, descriptions against the shipped parser | **174 / 174 agreed** |
| by kind | verify 38, analogy 17, compare 119 |
| declined, or answered with different operands | **0, 0** |
| evaluation questions the infix shapes must not cut | **110 put, 0 matched** |

Two shapes cover six kinds, so the description language was worth extending.

### 22.4 The part that is not a measurement

`RequestProject/GLM/Question.lean` gains the preamble: `runPre_of_skipped`
(where the preamble consumes exactly the leading remainder, the shape sees the
bare question and answers it unchanged — skipping is a described act, not a
second parser), `runPre_refuses_undescribed` (where it consumes nothing the
opening must stand at the head, which is §22.1's fifteen witnesses as a
theorem), `skipPiece_once` and `skipPiece_twice` (a piece consumes exactly the
forms written, once or in a loop), and `skipMany_of_le` (the bound that keeps
the repeatable skip structural decides nothing: past the last match, more of it
changes nothing). Five further theorems settle the shipped preamble on the
shipped `derive` shape by `decide`. The file still carries no `sorry` and no
non-standard axiom.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report language"
--verify-tct`, the `report-language` case of the CLI evaluation,
`tests/test_language.py` (90 tests), and `lake build`.

### 22.5 What it leaves open

Six kinds are described and only three are *read* by the runtime. The infix
family is measured but not wired in, and the reason is named rather than
implied: four parts of the six described kinds still need a piece of
description language that does not exist — a **modifier** (`verify`'s semantics
qualifier), a **list** (`compare a and b`), described **trailing options**
(`analogy`'s subspace and limit), and a **nested** shape (`comparative`, an
operator between two measured uses). Those four are Phase 23.

---

## Phase 23 — the four undescribed parts, and the four branches they were blocking

**Status: closed.**

[`STATUS.md`](../STATUS.md) §3.4 as it stood after Phase 22, written here as work
and now settled. The study is [`studies/LANGUAGE_STUDY.md`](../studies/LANGUAGE_STUDY.md) §13.

Phase 22 left the infix family agreeing with a parser it had not replaced, and
named the reason as a list rather than a feeling: four parts of the six
described kinds needed a piece of description language that did not exist.
All four are now described, and the branches they were the obstacle to are
gone from `runtime/parser.py` and frozen beside the first three in
`language/legacy.py`.

| part | what it needed | branch deleted |
|---|---|---|
| `verify`: the semantics qualifier (`check tensor force = …`) | a **modifier** — a word that directs how the operands are read without naming one | the equation branch |
| `analogy`: the subspace and limit options | **trailing options** — a value written after the operands that narrows the answer | the analogy operator |
| `compare`: the list form (`compare a and b`) | a **list** — a hole whose filling is a sequence | both comparison branches |
| `comparative`: an operator between two *measured uses* | a **nested** shape — an operand that is itself a shape | the comparative |

### 23.1 The three that are not slots

A **list** is a hole that holds more than one value, and which words separate
the items is a decision about English exactly as a shape's separators are. A
`ListSlot` therefore carries its separator phrasing, a second **rank** tried
only when the first leaves too few items — `a or b and c` is two items, not
three, because `and` is cut first — the names its items fill, the minimum that
makes the question well formed, and the one admitted mark. It also keeps the
case of its items, because both sides go to the exact-real grammar unresolved
and `Pb` is an element where `pb` is nothing. That turned `compare` into a
**fourth slot shape**, which is the result this part was not expected to give:
the keyword form needed no new shape family at all.

A **modifier** is the third thing a shape can hold, being neither operand nor
operator. `check tensor force = mass * acceleration` asks the same question of
the same equation under a stricter reading, and the word has to come *out* of
the operands or the equation being audited would carry it. Where it may be
written and where it may be *removed* are two different questions: it is read
off the whole question wherever it stands, and removed only at the head and in
the trailing frame (`… under tensor semantics`). A `tensor` in the middle of
an equation stays exactly where it is.

A **trailing option** is a value written after the operands — the analogy's
subspace and its limit — read by the description rather than by the parser's
own option scanners.

### 23.2 The nested shape, and the price of reuse

`is cold in stellar_surface hotter than hot in tea` is infix, but its operands
are not text: each side has to be a *measured use*, which is the `measure`
shape itself. The nested description therefore holds an operator and **the
shape its sides nest**, tightened — the opening dropped, the class made
required, both slots narrowed to a single name. The last of those is what
keeps an exact-real comparison out of the shape, and it is a consequence rather
than a special case: `is sqrt(2) greater than 7/5` forms the operator and is
still refused, because `sqrt(2)` names no class.

The operator is **formed** rather than listed: any `-er than` word, or any word
inside `as … as`. Which degree words mean anything is the register's decision,
and enumerating them in the shape would put that decision in two places.

Reuse has a measured price, and it is the finding of the phase. A side of a
comparative is the measure shape, and the measure shape admits **five**
separators; the branch this replaces spelled its sides out with a regular
expression of its own, which listed four of them and not `relative to`. So
**148** corpus questions written with `relative to` on a side are read here and
were unknown to the branch. That is declared as a **widening** rather than
counted as agreement, and every widened question is accounted for by it with
**0 left over**. A side spelled out a second time is a side that drifts from
the shape it copies, and the two-word separator being the one that drifted is
the tell.

### 23.3 Measured the same way

| what is compared | result |
|---|---|
| slot corpus, descriptions against the frozen branches | **947 / 947 agreed**, 0 declined, 0 disagreed |
| by kind | derive 416, measure 362, compare 101, task 68 |
| infix corpus | **201 / 201 agreed**, 0 disagreed |
| nested corpus | **480 / 628 agreed**, **148 widened** (0 unexplained), 0 disagreed |
| round trips, slot shapes | **947 checked, 0 broken** |
| questions of undescribed kinds put to the shapes | 110, 110 and 123 put; **0 matched** |
| narrowing witnesses | **20 declined here, 20 misread by the branches** |
| boundary witnesses | 6 slot, 11 infix, 2 nested — every named boundary reached |
| judgements about English | **15** across 4 slot shapes, **13** across 3 infix, **4** across 1 nested |
| coverage | **7 of 20** answerable kinds, across **3** shape families, **all seven read off by the runtime** |
| verdict | `described` |

The subtractive test is met: the end-to-end evaluation returns **130 / 130**
with the same 16 expected boundary refusals and no gap, with `derive`,
`measure`, `task`, `compare`, `verify`, `analogy` and `comparative` all
answered off their descriptions and no branch left for any of them.

### 23.4 The part that is not a measurement

`RequestProject/GLM/QuestionNested.lean` carries the theorems: `ListCut.cut_two`
(the round trip for a list, with `sepAt_shorter` as the termination argument and
`cut_ne_nil`/`cut_append` as the two facts it rests on),
`ModifierFrame.strip_head`, `strip_frame` and `strip_middle` (the modifier is
removed exactly twice, and a word written inside an operand is returned
unchanged — the difference between a directive and a deletion),
`NestedSpec.run_rendered` (the round trip for a nested shape) and
`NestedSpec.run_no_operator` / `run_side_refused` (the two refusals, the second
being the boundary where the operator is formed and the question still
declined). `compareCut`, `tensorModifier` and `comparativeShape` instantiate
all of it on the shipped surfaces, decided by computation. The file carries no
`sorry` and no non-standard axiom.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report language"
--verify-tct`, the `report-language` case of the CLI evaluation,
`tests/test_language.py` (122 tests), and `lake build`.

### 23.5 What it leaves open

`build.UNDESCRIBED_PARTS` no longer lists a missing piece of description
language. What it lists now are **3 limits**, which is a different kind of
entry: thirteen kinds have no description at all; the described kinds fold the
case of their operands except where a description says otherwise; and a verb
*inside* an operand is not removed, because a described opening is read at the
head and a described closing at the tail and nowhere else.

Two of the thirteen are worth naming as *kinds a shape should not be bent to
fit*: `describe` is a bare concept name resolving in the register index, and
`report` is a subject table. A count of 20 with two descriptions bent to fit
would be a worse result than a count of 7 with the reason written down.

One smaller thing is left honest rather than fixed: a shape's judgement count
is the phrasings held in the shape plus the preamble's two, so the two
separator ranks a list slot carries are counted with the slot and not in the
15. Both `why`s are written and checked; only the arithmetic does not reach
them.

---

## Phase 24 — the quantiser's search, replaced by a lookup

**Status: closed.**

The first of the four candidates the described-surface rounds left standing,
and the oldest item on the supplied brief: *the `O(1)` LLVQ lookup table*. The
study is [`studies/LLVQ_TABLE_STUDY.md`](../studies/LLVQ_TABLE_STUDY.md).

### 24.1 What was wrong with the old answer

The Leech quantiser is the hot path of every address, and it was a scan: for
each of the two congruence classes of Λ, form the cost of all 4,096 Golay
codewords and keep the cheapest — 8,192 codeword costs and 98,304 additions per
call, a constant of the code rather than of the input.

Two earlier rounds had reached the same wall from other sides.
`reasoning/fwht_decode.py` showed that the 4,096 coset costs are one
Walsh–Hadamard transform and measured that this is *not* a speed-up for this
code, because `n = 2k` makes the transform cost exactly what the direct
summation costs. Its constant-time tier, `certified_lookup`, is a genuine
`O(1)` route but a conditional one, and on the reliability profiles the Leech
step actually produces it fires on **0 of 200** sampled vectors. A tier that
never fires on the real input is not the table.

### 24.2 The table

Under the MOG alignment the package already carries, a 24-bit word is a 4 × 6
grid, and each column has three readings: its GF(4) label, its parity and its
top bit. Three facts, each checked over all **4,096** codewords with 0
failures: the six column labels form a **hexacode word**; the six column
parities are all equal to one bit `p`; the top row's parity is that same `p`.
The count is what turns three necessary conditions into a characterisation —
64 hexacode words × 2 parities = **128 classes** of **32** codewords, and
128 × 32 = 4,096 with nothing left over. Inside a column `(label, parity, top
bit)` determines the 4-bit pattern uniquely, so the lookup table is 16 entries,
and a class is six of them plus one parity constraint on the top bits. That is
the "first few binary digits" the brief asked for, made precise.

### 24.3 What is proved rather than measured

`RequestProject/GLM/LLVQTable.lean`, `sorry`-free and on the standard axioms:

| theorem | what it says |
|---|---|
| `cost_eq` | a choice costs the greedy choice plus the gaps of exactly the columns where the two differ |
| `isLeast_cost_of_parity_eq` | greedy parity right: the class minimum is `∑ lo`, attained by the greedy choice |
| `isLeast_cost_of_parity_ne` | greedy parity wrong: the class minimum is `∑ lo + gap i₀` at a least-gap column |
| `card_parity_class` | the choices of `n` top bits with a fixed parity number `2^(n−1)` — 32 at `n = 6` |
| `isLeast_of_bounded_search` | branch and bound is exact, which is why an unopened class holds nothing better |

Both minimum statements are `IsLeast`, so each carries the attainment and the
bound at once.

### 24.4 The subtractive test, and the claim narrowed

`reasoning/lean_address.py::quantise` decodes through the table now; the scan
is **not** deleted — it stays in `analogy.py` as the thing to agree with, which
is what makes the agreement a comparison rather than a tautology.

| figure | value |
|---|---|
| declarations decoded both ways | **1,270** |
| addresses unchanged | **1,270** — 0 changed |
| vectors compared point for point (sweep, register carriers, boundaries) | **107**, 0 mismatches |
| codeword costs per call, table route (40 deterministic vectors) | `484/5` = **96.8** against the scan's 8,192 |
| classes opened per call | `121/40` ≈ **3.03** of 256; worst call 448 words, 14 classes |

The agreement test earned its keep: the first version of the table route
disagreed with the scan on exactly one vector, the physics carrier
`bekenstein_hawking_entropy`, where two Leech points sit at the same squared
distance and the tie is broken by the `±4` repair — the scan picks by
`(penalty, coordinate index)` and the column-wise version was picking by
penalty alone. Both answers are nearest points; only one is the answer the
address book already contains.

What is **not** claimed is `O(1)`. The table work is fixed and the expansion is
data-dependent with a worst case of the whole code, so the module, the report
and the study all say the same thing: **constant-bounded, not constant**, with
the measured figure quoted and the worst case named. Quoting `O(1)` without the
measurement is what directive D6 exists to prevent.

*What recomputes it:* `PYTHONPATH=. python3 GLM.py -q "report llvq"
--verify-tct`, `tests/test_llvq_table.py`, `corpus_report()` and
`search_cost_report(samples=40)` in `reasoning/llvq_table.py`, and `lake build
RequestProject.GLM.LLVQTable`.

---

## Phase 25 — the archive, read to the end

**Status: closed.**

The supplied archive `source_material/GLM-main.zip` had never been read all the
way down. Phases 1–24 took what the running system needed from it; this phase
went through the parts the brief named — `glm_machine`, the two `light/`
calibration rounds, `leech_lattice`, the two `data_object/` encoding attempts,
`FirstPrinciples`, `mog_cube_1`, `Projection`, `GMHGL`, the earlier `glm_lean`
iterations and `arc_agi_15` — and asked one question of each: **is there a
claim here that can be stated as a theorem and checked?**

### 25.1 What came back

**25 files of Lean, 7,170 lines, 848 declarations**, all building against the
pinned Mathlib with no `sorry` and all mirrored in `overlay/glm_lean/`. The
per-file account is
[`studies/RETRIEVED_LEAN_STUDY.md`](../studies/RETRIEVED_LEAN_STUDY.md) §2; the
groups are the MOG cube (`Cube/`, five files: the surface identification, the
hexacode tiling, the stabiliser test, the price list and the three-cube
proposal), the lattice shortcut (`Shortcut/`, eight files: the Golay code, its
weight enumerator, a complete decoder, the Gray layer, the Leech step, the
corrected pipeline and two audits of the published directory), the three
generations of the paper's formal companion (`Foundations.lean`, `Gen2.lean`,
`Gen3.lean`), the electromagnetic calibration (`Calibration.lean`,
`AlignmentPoints.lean`), the first-principles sub-study (`FitCapacity.lean`,
`Packing.lean`, `Triad.lean`), the projection sub-study (`SeedLayers.lean`),
the graded cost model (`StepCost.lean`), spatial arithmetic
(`SpatialArithmetic.lean`) and the ARC-era reasoning loop
(`ReasoningLoop.lean`).

### 25.2 Nine of the twenty-five are negative results

That is the part of the retrieval that could not have been had by leaving the
material in the archive, because a refuted claim in a script is
indistinguishable from an unexamined one. The calibration chain returns the `c`
it was given; `3, 6, 9` is produced by any three-element set; what a binary
substrate forces is 23 and not 24; the three-cube rules give a `[24,12,4]`
code that no relabelling repairs; the published directory's "even
quantisation" is true by construction; the substrate's `snap_to_codeword` is
not a decoder; consecutive integers are never a "geodesic jump"; the electron
mass point's error is 0.0090–0.0093 % and not the quoted 0.007 %; and
`FitCapacity.lean` is the instrument that says how much a numerical agreement
could have been worth in the first place.

### 25.3 What it moved, and what it did not

The end-to-end evaluation returns the same **131 / 131** with the same 16
boundary refusals, and the benchmarks and probes are unmoved: the retrieval is
additive to what is *proved*, not to what is answered. The Lean corpus went
from 1,270 declarations across 48 files to **2,118 across 73**, so
`studies/LEAN_ADDRESS_STUDY.md` was re-measured against the code rather than
patched — and the separation signal rose, to 13.2 times chance on the file test
(from 12.3) and 15.0 on the citation test (from 9.6), on a corpus two thirds
larger.

*What recomputes it:* `lake build`, the sorry scan, the two-copy diff,
`tests/test_retrieved_lean.py` (which re-derives every line count and
declaration count the study states, and fails if a cited theorem is renamed),
`PYTHONPATH=. python3 -m glm_universal.tools lean-address` and
`PYTHONPATH=. python3 GLM.py -q "report lean" --verify-tct`.

---

## Phase 26 — the dropped work, restored, and the archive's second reading
## closed

**Status: closed.**

The tree handed over at the end of Phase 25 was missing part of what that phase
had produced: Lean files, their test files and several study documents had not
survived the handover. `dropped.zip` at the repository root is what came back,
and nothing in it was taken on trust — every Lean file was rebuilt against the
pinned Mathlib, every figure its tests pin was recomputed from the substrate,
and the two copies of the Lean tree were diffed.

### 26.1 Where the development stands

**95 files of Lean, 27,548 lines, 2,764 parsed declarations**, no `sorry`, both
copies byte-identical — against 73 files and 2,118 declarations at the close of
Phase 25. The suite was **72 files of tests** at the close of this phase; for
the project as it is now see [`overlay/FIGURES.md`](../overlay/FIGURES.md).

### 26.2 The archive's second reading

Eight further results, written up in
[`studies/SOURCE_SALVAGE_SECOND_PASS.md`](../studies/SOURCE_SALVAGE_SECOND_PASS.md):
the cube surface as the MOG grid, the read quantum as an operator, the Gray
jump norm, the ARC grid metrics as interval bounds (`GridTension.lean`), the
conditional lobe, the mode algebra, the free cube symmetries
(`Cube/Stabiliser.lean`) and the parity count that caps them at 24
(`Golay/CubeMirror.lean` — the one Lean file of this phase written new rather
than restored). The two questions the first reading left open are answered
**no** in
[`studies/ARCHIVE_DEEP_DIVE_STUDY.md`](../studies/ARCHIVE_DEEP_DIVE_STUDY.md): the
archive's 44 balanced octads barely exceed what a null census of all 735,471
eight-subsets predicts, and are not even invariant under relabelling; and its
relaxation reaches the code but not the nearest codeword, so it is not a
decoder. [`studies/SOURCE_SALVAGE_AUDIT.md`](../studies/SOURCE_SALVAGE_AUDIT.md)
is the first reading's own write-up, restored in the same way.

### 26.3 The stability measurement, which closes one Phase 27 candidate

`reasoning/stability.py` against `RequestProject/GLM/Stability.lean`: the two
certificates checked in exact rational arithmetic with no square root, the
sharp radius as the least distance to a bisector, and past it a perturbation
*built* rather than asserted. The addresses at radius zero are exactly the
nearest-point ties, and what breaking them by index costs is
[`studies/TIE_BREAK_STUDY.md`](../studies/TIE_BREAK_STUDY.md).

### 26.4 The rules made checkable

`reasoning/exactness.py` and `tests/test_exactness.py` turn D7 and D9 into a
machine-checked inventory: every site in the package where a float could be
constructed, every cryptographic digest, and every XOR use is declared, and the
suite fails both when an undeclared site appears and when a declared one stops
existing. `tests/test_number_theory_evidence.py` does the same for
[`studies/GLM_Complete_Number_Theory_Evidence.md`](../studies/GLM_Complete_Number_Theory_Evidence.md),
re-running the generators the paper names and comparing its tables and its
worked transcript cell by cell.

### 26.5 What moved in the runtime

`report searchloop` is the **49th report subject** and the evaluation's
**132nd** case; the end-to-end set was **132 / 132** with the same 16 boundary
refusals. The reasoning package went from 49 modules to **57**. The address
book was regenerated over the larger corpus and
[`studies/LEAN_ADDRESS_STUDY.md`](../studies/LEAN_ADDRESS_STUDY.md) re-measured
rather than patched: **2,764 / 2,764 read back exactly, 0 coordinate errors**,
2,426 distinct addresses, nearest-by-address sharing a file **560 / 2,764**
against 37 for the digest control and 23 for the seeded reshuffle, with chance
at `8878/636411`. Phase 27 re-measured all of it again over the larger corpus.

---

## Phase 27 — the address book made to do work, and the first loop

**Status: closed.**

Two faculties the substrate had never been asked for, each measured against
controls and each answered in a way that constrains the claim rather than
flattering it.

### 27.1 Retrieval, against six controls

`reasoning/retrieval.py` turns the address book into an index and measures it
over **204** stride-selected queries of the **2,850**-declaration corpus, with
chance computed in closed form. A hit is a *relative* — same file, or joined by
a citation — and neither relation appears in any feature map, so "the
neighbours are relatives" is a prediction that can fail.

* The address is a real index: hit@5 **51.0 %** against **6.8 %** chance
  (**7.4×**), beating the digest (3.5 %), the seeded reshuffle (6.9 %), the
  random ranking (5.9 %) and name-substring search (34.2 %).
* And it is beaten decisively by plain text: Jaccard overlap of identifier
  tokens reaches **85.8 %** at **57.7 %** precision@5, against the address's
  15.5 %.
* The lattice is not what carries the signal: the same features with **no
  quantisation at all** score **51.0 %**, and a lexical address built from
  identifiers reaches **65.2 %** — better than the structural address, still
  twenty one points behind the text control. The limit is the projection to 24
  capped integers, not the choice of what to put in them.
* An address shortlist does not make the text search cheaper for free: 800
  candidates (28.3 % of the corpus) give 85.1 %, and 1.8 % of the corpus gives
  69.8 %.

### 27.2 What the geometry does earn: an exact guarantee

`RequestProject/GLM/Retrieval.lean` proves the completeness bound behind the
shortlist, and `filterRadius_eq_nil_certifies_absence` is why an empty
shortlist is a *proof* of absence. Measured: **142,450** pairs, **0**
violations; at feature radius 2 the guaranteed-complete shortlist is **80.2**
declarations — **2.5 %** of the corpus — containing all **16.8** feature-close
declarations on average.

### 27.3 The loop: propose, check, refuse

`reasoning/controller.py` builds a physical quantity out of the ten EXT10
generators one factor at a time — twenty moves, a stated tie-break order, the
state compared to the target exactly. Every plan any scorer returned was
re-verified end to end by `verifier.verify_expression_pair` through the digit
stack: **100 %**, under every scorer, by an instrument that did not build it.

Two refusals, and only one is a budget. `Controller.unreachable_of_invariant`
refuses **127 of the register's 726** quantities *with a proof* — an invariant
no move can change — with no node expanded; and `Controller.beam_can_miss` is a
kernel-decided witness that a width-one loop steered by an inexact heuristic
can miss a plan that exists, which is why a failed search is a refusal and
never an answer. `Controller.exists_descent` is the complement: steered by the
exact distance the loop never backtracks.

### 27.4 Can the substrate steer? Yes, and no better than the features

On the 24 reachable tasks the Leech-address scorer solves **18**, against **8**
for no guidance and **12** for a scorer that knows nothing about the target —
so the geometry does real work here, which is more than it managed in the
retrieval experiment. The same distance measured **without** the lattice solves
**17**, one behind and with a better minimality record; and decoded at the
register's own resolution (scale 1 rather than 9) the address scorer falls to
exactly the no-guidance **8**, proposal for proposal, which is what the
read-back bound of `Address.lean` predicts. Scoring by address costs about
twenty milliseconds a state against microseconds for counting exponents.

### 27.5 What moved in the runtime

`report retrieval` and `report controller` are the **50th** and **51st** report
subjects and the evaluation's 133rd and 134th cases; the end-to-end set is
**134 / 134** with the same 16 boundary refusals. Two Lean files
(`Retrieval.lean`, `Controller.lean`) and two test files
(`test_retrieval.py`, `test_controller.py`) came with them.

*What recomputes it:* `lake build`, the sorry scan, the two-copy diff,
`tests/test_retrieval.py`, `tests/test_controller.py`, and
`PYTHONPATH=. python3 GLM.py -q "report retrieval" --verify-tct` and
`"report controller" --verify-tct`, whose third column re-derives every figure
in a fresh interpreter. Write-ups:
[`studies/ADDRESS_RETRIEVAL_STUDY.md`](../studies/ADDRESS_RETRIEVAL_STUDY.md) and
[`studies/CONTROLLER_STUDY.md`](../studies/CONTROLLER_STUDY.md).

---

## Phase 28 — generated rather than stored, and the generators checked

**Status: closed.**

A supplied script, `glm_zero_storage_substrate_v3.txt`, proposes that the
substrate stop storing its tables and regenerate them from the congruences that
define them. The round took the perspective seriously and did to it what the
project does to every other supplied claim: measured it.

### 28.1 The perspective is right, and now has a number

`reasoning/generative.py` puts the two costs side by side and — the part that
makes the row worth anything — **regenerates each object and compares it with
the stored one before emitting the row**. The Golay code, the 759 octads, the
196,560 minimal vectors and the membership decision cost **9,449,445 bytes**
stored against **24,648 bytes** of generators: **3,149,815 : 8,216**, about
**383 to one**, all four verified identical.

Asked of this repository, the same audit finds the discipline mostly already in
place: of **7,316,334** bytes the overlay keeps on disk, **7,296,569** are
caches of recomputable objects stored beside the digest of their inputs, and
only **19,765** bytes are primary. **99.7 %** of what looks like storage here
is generation with a cache in front of it.

### 28.2 The proposed Leech sieve: sound, and 99.4 % incomplete

The script's membership test keeps **1,152 of the 196,560** minimal vectors —
all 1,104 of the `(±4², 0²²)` shape, 48 of the 98,304 `(∓3, ±1²³)`, and **none**
of the 97,152 `(±2⁸, 0¹⁶)` — with **0** unsound acceptances.

* `GLM.ZeroStorage.v3Sieve_sound` proves the soundness in general rather than
  sampling it.
* `v3Sieve_iff` says exactly what the sieve generates: `IsLeech x ∧
  UniformMod4 x`. Its "Construction B" step asks all 24 coordinates to agree
  mod 4, where Construction C asks the *disagreeing* coordinates to form a
  Golay codeword; only the empty and all-ones words satisfy the stronger
  reading, which is the whole of the loss.
* `v3Sieve_zero/add/neg`: the survivors are a genuine sublattice of Λ₂₄, so the
  script does generate a lattice — the same failure mode Construction A has at
  the rung below.
* `octadVec_not_v3Sieve` is a kernel-decided witness: twice the indicator of the
  octad `{0,1,2,3,4,17,21,23}`, norm² 32, in Λ and rejected.
* The repair is one line. `corrected_sieve` agreed with the package's own
  `leech2.in_leech` on **196,656** vectors — the shell plus probes, **96** of
  them outside Λ — at the same cost.

### 28.3 The snap does not snap, and an exact decoder that does

The script's fallback, "round every coordinate to the nearest even integer", is
called trivially a Leech point and is not: `fallbackVec_not_isLeech` refutes it
at `(2, 2, 0²²)`, since the Golay code has no word of weight 22. Measured, the
snap returned a point outside Λ on **4 of 4** general-position probes (excess
squared distance up to **138**) and **3 of 4** near-lattice probes. `exact_snap`
— a coset decoder over the 4096 codewords and both parities, exact throughout —
is inside Λ on every probe and within the squared covering radius **16** every
time, returning exactly `1/2` on targets half a step from a minimal vector.

### 28.4 A generated number is only as good as its cost bound

Against the package's certified `ExactReal` processes at 200 bits: π (Machin, 20
terms) gives 96 bits and e gives 61, both as advertised; √2 by Babylonian
iteration gives **202** bits where the docstring's doubling rule claims 1024,
ln 2 at "precision 64" gives **9** bits where 256 are claimed, and γ gives
**3** — its generator approximates `ln n` by `ln 2 · bit_length(n)`, so it is
wrong rather than slow. **0 of the 3 stated accuracy claims hold.** The
Babylonian denominator's bit length runs `2, 4, 9, 19, 40, 80, 162, 325, 650,
1301, 2603, 5207`, doubling every step, so the module's default of 64 iterations
cannot be run at all: a process is a number only when it is parameterised by
the precision asked of it, which is the contract `ExactReal.at(k)` already
keeps.

The dyadic tower is that contract in the layer vocabulary, and it is now
proved: `dyadic_surrogate_error` (level `n` pins a rational to a half-open
window of width `2⁻ⁿ`), `dyadic_exact_iff_den_pow_two` (the ladder terminates
exactly on the dyadic rationals) and `dyadic_value_not_strictMono`, which
refutes the script's "strictly increasing ladder" for *readings* — at `q = 1/3`
levels 0 and 1 both read 0. What is strictly increasing is the resolution.

### 28.5 The Niemeier portal, and what moved in the runtime

The sextet the portal detector finds is real — at all **200** weight-4 words
checked there are exactly six codewords at distance 4, none closer, pairwise
distance 8 — but the detector's output takes **1** distinct value over those
words, so the printed `A₁²⁴` label separates nothing. `reasoning/deep_holes.py`
remains the instrument that reads a hole diagram.

`report generated` is the **52nd** report subject, column-3 verified in a fresh
interpreter; `RequestProject/GLM/ZeroStorage.lean` and
`tests/test_generative.py` (16 cases) came with it, and the pipeline row
`zero-storage` makes **22 of 22** rows complete through all six stages. It is
also the evaluation's **135th case**, `report-generated`, so the subject is
driven through the CLI the way a user drives it and not only through the
package: the end-to-end set is **135 / 135**.

Nothing in the module reads a clock. The audit is emitted through the runtime,
whose traces are required to be byte-identical between runs, so the storage
rows carry bytes and verification verdicts and no wall-clock reading at all.

*What recomputes it:* `lake build`, the sorry scan, the two-copy diff,
`tests/test_generative.py`, the evaluation case `report-generated`, and
`PYTHONPATH=. python3 GLM.py -q "report generated" --verify-tct`. Write-up:
[`studies/ZERO_STORAGE_STUDY.md`](../studies/ZERO_STORAGE_STUDY.md).

---

## Phase 29 — the last stored table removed, and the cost of generating measured

**Status: closed.**

Phase 28 left one corner of "generate, don't store" unfinished: membership in
the Golay code still consulted a 4096-word set, about 12 KB held in memory.
This round removes it, and — the part that makes the removal a trade rather
than a slogan — attaches an exact integer cost to every generated answer.
The work is `glm_zero_storage_substrate_v5.py` (standalone, standard library
only, no float, no RNG) and `RequestProject/GLM/ZeroStorageV5.lean`.

### 29.1 Membership is twelve parities

The extended binary Golay code is self-dual, so its 12 generator rows are also
a parity-check matrix: `mask ∈ G₂₄` exactly when the 12 parities
`popcount(mask & row_j) mod 2` all vanish — **36 bytes**, twelve word
operations, and when the word is not a codeword the same operations produce its
**12-bit syndrome** rather than a bare `False`, which is the language
`Golay/Census.lean` and `Cube/Tax.lean` already use.

* `GLM.ZeroStorageV5.syndromeZero_iff_isGolay` — the equivalence, proved:
  linearity of the checks (`check_xor`), a 144-case kernel decision for the
  rows, and the systematic-encoder argument with a 4096-case kernel decision
  for the twelve-bit block.
* `syndromeSieve_iff_isLeech` — the whole membership test of the script
  decides exactly `IsLeech`.
* Checked before anything was removed: **196,560** shell vectors compared on
  both routes with **0** disagreements, 1,536 deliberate non-codewords, the
  whole **2²⁴**-word space swept (4096 accepted) *and* the same set obtained
  exactly by null-space elimination, and the same checks against the Lean
  development's own, differently generated rows.

### 29.2 The cost ledger

Thirteen primitives are counted — parity checks, popcounts, Gray-code XORs,
coordinate passes, coset trials and prunes, ±4 repairs, table lookups, integer
square roots, series terms, big divisions, Δ-Σ ticks, rational operations —
as **exact integers, never wall-clock**, so a second run reproduces the ledger
byte for byte. The storage audit becomes three columns: one membership
decision is 12 parity checks against 36 bytes, one codeword about one XOR, one
nearest-point decode **50,705** primitives (pruned) against **217,272**
(exhaustive), with the pruned search checked to return the same point at the
same distance. The optional cache is priced beside them, with its digest and a
regenerate-and-compare check.

### 29.3 NRCI, defined rather than invoked

`NRCI(r ; x) = 1 − √(Σrᵢ²/Σxᵢ²)`, reported as an exact dyadic enclosure of
width `2⁻ᵏ` and as the exact rational squared form, on three named streams:
the Δ-Σ running-average residual, the residual of a decode, and the per-level
dyadic residuals. For the Δ-Σ stream the proved bound `|rₙ| < 1/n` is checked
at every `n` and printed beside the figure.

### 29.4 The register tracks, and higher order is measured

Retargeting keeps the accumulator, and the bound survives: `ds_track_bound`
(`|average − mean target| < 1/N` for a moving target) and
`ds_track_moving_target` (against a fixed target, plus exactly the mean
deviation). Second- and third-order noise shaping is implemented in exact
rationals and *measured*: through a triangular read-out window the guaranteed
bound improves from `1.9 × 10⁻³` to `1.3 × 10⁻⁵` at N = 1024 between orders 1
and 2, while order 3 at these coefficients is unstable (`max|e|` reaching
`1.4 × 10⁷`) and nothing is claimed for it.

### 29.5 The decode is proved optimal

`quad_step_bound`, `quad_zero_bound`, `coset_cost_ge` and
`coset_repair_attained`: inside a Construction-C coset the cheapest single ±4
move is exactly the minimum when the mod-8 sum forces an odd repair. The
surrounding claim is proved in the same file rather than left measured:
`coset_min_cost` and `coset_min_attained` state the coset minimum for a
*rational* target, `leech_in_coset` shows every Leech point lies in one of the
8,192 cosets and `lattice_dist_ge` concludes that a bound holding on every
coset holds on `Λ₂₄` — so the minimum the decoder searches for is the
distance to the nearest lattice point. `allTwos_inCoset` keeps the hypotheses
from being vacuous. What is still checked rather than proved is the
transcription: that the script computes the quantities the theorems describe,
which the self-test verifies against an unpruned exhaustive search.

### 29.6 What Mathlib has, checked first

Before any claim about where this work might belong upstream, the pinned
Mathlib was searched: no Golay code, no Leech lattice, no Niemeier
classification, no linear-code layer and nothing on sphere packing or
quantisation; the ambient `ZLattice`, quadratic-form, root-system and
modular-form theory is all present. §10 of the study records the counts and
what follows — the missing prerequisite is a general self-dual-code layer, not
the sieve equivalence.

Reproduce: `python3 glm_zero_storage_substrate_v5.py --test`,
`--test --full`, `--ledger`, `--report`; `lake build`. Write-up:
[`studies/ZERO_STORAGE_V5_STUDY.md`](../studies/ZERO_STORAGE_V5_STUDY.md).

---

## Phase 30 — the corpus itself made data

**Status: closed.**

The prose of the project is now held the way the substrate holds data.
`glm_universal/corpus/` classifies every document by rule — archive membership
is decided by the path, never by judgement — emits `DIGEST.md` and every
in-document generated block, addresses all **688** sections of the corpus on
the same lattice the Lean declarations use, and keeps the two address studies'
expensive measurements beside the digest of the Lean sources they were taken
from, failing when any of that drifts. Every current-state document opens with
a tier-0 block, so a coarse read of the whole project costs about **2,400**
words against roughly **189,000** for the full current state, and
[`ENTRY.md`](../ENTRY.md) states a reading order whose coverage claim is tested
rather than asserted. `RequestProject/GLM/Corpus.lean` is the part of it that
is a theorem — the soundness of the tiered read, the archive partition, the
freshness rule and certified absence — and **D10, *a document is data***, is
the standing rule it leaves behind, with
`python3 -m glm_universal.corpus --check` as its instrument.

Reproduce: `python3 -m glm_universal.corpus --check`, `--write`, `--remeasure`;
`lake build`.

---

## Phase 31 — the wobble landscape, pre-registered and measured

**Status: closed.**

The question was whether the fine-structure constant's arithmetic signature is
*distinctive* within the space the Golay–Leech substrate permits. The
discipline that makes an answer worth anything here is pre-registration: the
statistic, the nulls, the multiplicity correction, the gate and the decision
tree were written into
[`studies/WOBBLE_LANDSCAPE_STUDY.md`](../studies/WOBBLE_LANDSCAPE_STUDY.md) and
committed **before** the measuring module existed.

### 31.1 The structure is known, so it is used rather than simulated

The delta–sigma loop chasing a constant `t` emits the Sturmian word of slope
`t`, and its gap structure is fixed by the continued fraction of `t`: the gaps
between ones take at most two lengths, `floor(1/t)` and `floor(1/t) + 1`, with
`long(K) = ceil((K + 1) * frac(1/t)) - 1` long gaps among the first `K`.
`reasoning/wobble_landscape.py` implements that closed form in exact integers
and checks it against a finite run — over 20,000 emitted bits, 144 gaps of
lengths {137, 138} and 5 long gaps predicted against 5 observed — and the test
perturbs the closed form to confirm the check can fail.
`GLM.Landscape.gap_mem_pair` and `gap_image_card_le_two` are the bound as a
theorem.

### 31.2 The statistic, and the two figures it corrects

The primary statistic is the stage-0 long-gap frequency `S(x) =
frac(1/frac(x))`, **not** the bit entropy: the density of ones is exactly the
slope, so the Shannon entropy of the raw stream is `H2(t)` and carries only the
magnitude. That is the corrected reading of the older "wobble entropy 0.062"
row, which the module reproduces and then refuses as a statistic. The run
length 137 is `a₀` of the continued fraction of `1/alpha` and nothing more —
and that expansion, computed from the exact CODATA 2022 value, is
`[137, 27, 1, 3, 1, 1, 18, 1, 8, 1]` rather than the `[137; 28, 1, 1, 2, …]`
the commissioning brief quoted.

### 31.3 The verdict, against a named null

**B = 1.79 bits** against the magnitude-matched stride null: of the 1,066 exact
rationals `j/10⁷` in `(1/138, 1/136)`, **77** deviate at least as much as
alpha, a tail of `77/1066` — 3.79 bits raw, 1.79 after correcting for the 4
statistics tried. The pre-registered gate (`B < 1` not evidence, `1 ≤ B < 3`
weak, `B ≥ 3` continue) calls that **weak**, so the landscape enumeration was
**not** run. Under the secondary `k`-sweep null (`1/(137 + 1/k)`, `k = 1..100`)
the same statistic scores −1.57 bits; the disagreement is a fact about the
measure a `k`-sweep puts on `k`. Both chances are exhaustive enumerations, not
samples.

### 31.4 The Golay null, computed before it is read

The number of 24-bit words within Hamming distance 3 of a Golay codeword is
`4096 * (1 + 24 + 276 + 2024) = 9,523,200` of `16,777,216`, so `d_min ≤ 3` has
probability exactly `2325/4096` — the **majority case**, worth about 0.82 bits
and not a structural coincidence. Alpha's `d_min` is 0 at depths 24, 48 and 72,
and against the magnitude-matched null that is worth **0.00 bits**: all 1,066
members reproduce it. `GLM.Landscape.golay_code_ball_count` proves the sphere
count on the substrate's own code and `golay_ball_majority` that the fraction
exceeds a half.

### 31.5 What it is not

Not a derivation of alpha, not a claim that the substrate selects it, and not a
statistic chosen after seeing the data. The frameworks that were *not* searched
for something near 1/137.036 — Adinkras, 2-adic amplitudes, modular forms at CM
points — are carried in the study as "bridges not yet tested", each with the
falsifiable test it would need, and are marked unimplemented.

Reproduce: `PYTHONPATH=. python3 GLM.py -q "report landscape"`,
`python3 -m glm_universal.tools landscape`,
`python3 -m pytest glm_universal/tests/test_wobble_landscape.py`;
`lake build RequestProject.GLM.WobbleLandscape`. Write-up:
[`studies/WOBBLE_LANDSCAPE_STUDY.md`](../studies/WOBBLE_LANDSCAPE_STUDY.md).

---

## Phase 32 — the four things the untouched list had been carrying

**Status: closed.**

Four items had stood on §3.2 and §3.3 of [`STATUS.md`](../STATUS.md) as stated
limitations rather than mechanisms: an analogy the machine refused, a register
that was sparse, a class of lexicon triples that said *that* rather than *how*,
and a commitment to an open vocabulary with no door in it. Each is closed in
the shape directive **D5** requires — implemented, wired, tested, formalised,
verified — so each is a report subject, a test file, a study and a Lean file.

### 32.1 The cross-register analogy

`heat : temperature :: force : ?` was refused because the lexicon carries
`temperature drives heat` and reaches nothing from `force`. The missing
relation is supplied as a **register**, not as a special case:
`reasoning/conjugate.py` holds 7 energy domains — an intensive effort, the
extensive extent it acts through, and the transfer of energy they make, 21
names over `effort_of`, `extent_of` and `conjugate_of`. Every row is checked
against the physics register in exact integer arithmetic: the effort's and the
extent's EXT10 exponents sum to those of energy and their decimal scales sum to
its scale, which is what pairs pressure with volume and not with area. No name
occupies two columns, so each relation is a bijection and the answer is derived
in either direction: `force` is in the effort column, so the question is
`effort_of` read backwards and the answer is `work`. 11 transport questions were
put through it — 8 answered, 3 refused, each refusal naming which of
`determinate`, `role_typed`, `functional`, `grounded` failed.
`RequestProject/GLM/Conjugate.lean`: `rel_functional`, `rel_injective`,
`forward_unique`, `reverse_unique`, `no_answer_of_unplaced`,
`dimensionally_sound`, `roles_unique_table`.

### 32.2 Sparse chemistry, decided rather than blank

The element register measures 1,257 of its 1,652 cells.
`reasoning/element_completion.py` gives every one of the other 395 a
disposition. A rule is admitted only when its leave-one-out mean absolute error
is at most half that of predicting the field's own mean, scored on at least 20
elements — the control is the constant rule, so admission is a claim that the
rule found something rather than that it fits closely. 9 of the 14 fields take
one; 185 cells are filled by estimate, taking the completed view to 1,442 of
1,652; the 210 that stay empty are 100 inputs absent, 97 no admitted rule and
13 not derivable from this register. Nothing is written back: read at the
measured provenance the completed view is the register, cell for cell.
`RequestProject/GLM/Completion.lean`: `dispositions_exhaustive`,
`dispositions_exclusive`, `readMeasured_eq_base`, `coverage_monotone`,
`admitted_halves_the_baseline`, `ledger_accounts_for_every_empty_cell`.

### 32.3 A standing rule for a vague `related_to` triple

The problem was never the 66 triples the lexicon holds — two rounds had decided
those, the second by hand — but that every new one brought the hand work back.
`reasoning/vagueness.py` is a router of four routes tried in order: the
dimensional rules, the energy-conjugate register, the admitted proposer rules,
and only then a person, who is handed the evidence rather than the failure. 34
of the 66 are decided without a person (27 dimensionally, 1 by the conjugate
register, 6 by the proposer) and 32 are referred. A proposer rule is admitted
only if it fires on at least 5 of the 36 hand-decided names and agrees with the
hand decision on every one: 1 of 4 passed, and the three refused are kept with
the disagreement that refused them, because a rule refused on a named
disagreement is a finding. `RequestProject/GLM/Vagueness.lean`: `route_mem`,
`route_unique`, the four `route_eq_*_iff`, `all_declined_of_referred`,
`proposal_correct_of_admitted`, `not_admitted_of_disagreement`.

### 32.4 Open vocabulary, made a door

A name is admissible exactly when some **stated** route gives it coordinates
**computed** from a register the machine already checks; **grounded** is the
clause that refuses. Three routes admit — a name held by one of the nine
registers, a unit expression dimensioned by the unit register, an expression
over register names evaluated by term arithmetic — and the fourth refuses. Over
27 probes the door admits 20 (11 held, 5 by unit, 4 by arithmetic) and refuses
7, conditionally and with the condition named: `justice` is refused until a
register that measures it exists, and `km/h` because the SI-coherent unit
register cannot finish reading `h`, which is a gap in the register rather than
in the door. Nothing is typed in at admission time and nothing is written back,
so the held vocabulary of 1,093 names is unchanged.
`RequestProject/GLM/Admission.lean`: `route_mem`, `route_unique`,
`admissible_iff`, `no_coordinates_of_refused`, `coordinates_grounded`.

### 32.5 The figures the growth moved

The four Lean files and four test files moved every derived figure, so they
were re-measured rather than patched: 105 Lean files, 30,853 lines, 3,049
parsed declarations, no `sorry`; 81 test files; the address book and the
retrieval measurement cache re-taken against the new tree digest — read back
3,049 / 3,049 with 0 coordinate errors, 2,688 distinct addresses,
nearest-by-address sharing a file 609 / 3,049 against 37 for the digest control
and 26 for the reshuffle — and retrieval over 204 queries at hit@5 48.5 %
against 6.4 % closed-form chance, the text control still ahead at 80.9 %, the
completeness bound holding on 155,448 pairs with 0 violations. The hand-written
passages of `STATUS.md` and the overlay README were brought to those figures,
`overlay/FIGURES.md` regenerated, and `glm_universal.corpus --check` reports
`current`.

### 32.6 What was deliberately not done

No estimate was written back into the element register; the 32 referred
`related_to` triples were not decided by hand to shrink the residue; the three
refused proposer rules were kept with their disagreements rather than tuned
until they passed; nothing was written into the held vocabulary by admission;
and the round's other candidate — the Niemeier deep holes — was not attempted
and stands alone as Phase 33.

Reproduce: `PYTHONPATH=. python3 GLM.py -q "report conjugates"`,
`"report completion"`, `"report vagueness"`, `"report admission"`;
`python3 -m unittest glm_universal.tests.test_conjugate`
`glm_universal.tests.test_element_completion`
`glm_universal.tests.test_vagueness` `glm_universal.tests.test_admission`;
`lake build`. Write-ups:
[`studies/CONJUGATE_STUDY.md`](../studies/CONJUGATE_STUDY.md),
[`studies/ELEMENT_COMPLETION_STUDY.md`](../studies/ELEMENT_COMPLETION_STUDY.md),
[`studies/VAGUENESS_STUDY.md`](../studies/VAGUENESS_STUDY.md),
[`studies/ADMISSION_STUDY.md`](../studies/ADMISSION_STUDY.md).

---
## Phase 33 — the Niemeier deep holes, classified from trajectories

**Status: closed, with a negative verdict its own decision tree forced.**

The last purely geometric item on §3.4 of [`STATUS.md`](../STATUS.md), and the
supplied brief's third experiment: can the *distribution of trajectories* that
arrive at a deep hole of the Leech lattice name the hole's Coxeter–Dynkin type,
instead of the type being read out of a table?

### 33.1 Pre-registered before any measuring code existed

[`studies/DEEP_HOLE_STUDY.md`](../studies/DEEP_HOLE_STUDY.md) was written and
committed first, and it fixes: the trajectory ensemble (14 declared centres,
240 nested starts per centre, the exact `voronoi_walk` slide), the primary
statistic `S₁` — the sorted arrival shares over the hole's vertices, compared
by `L₁` — the named secondaries, the statistic-to-label rule with its refusal,
four nulls (a digest control, a seeded reshuffle, a uniform-profile ablation
and the plain vertex count `24 + k`, named in the brief as the cheap
competitor), the gate of 3 bits, the multiplicity correction for the 4
statistics tried, the decision tree, and the caution that the ensemble is a
projection rather than the hole.

### 33.2 What came out

The ensemble reaches **10** of the 23 Niemeier root systems over 44 queries.
The method names **15 of 44** against **11** for the vertex count, **12** for
the uniform ablation, **4** for the digest control and **3** for the reshuffle
— so it beats every control, including the one that mattered. And the round
stops anyway: the pre-registered sanity query fails, because changing only the
ensemble seed keeps just **3 of 10** labels. Under the decision tree the bit
score is reported and disqualified. Separately, the separation radius the
census permits and the radius faithfulness needs are incompatible, so at the
certified radius every present hole is called absent. That is the finding, and
tier 0 of the study says it.

### 33.3 The Lean half

`RequestProject/GLM/DeepHoleClassifier.lean` (namespace `GLM.DeepHole`),
mirrored byte-identically into the second copy of the tree:
`l1_reindex`, `arrivalMultiset_reindex`, `sortedProfile_reindex` and
`classify_reindex` — the statistic, and therefore the label, is invariant under
the relabelling the walk is allowed, so it is a function of the hole rather
than of the walk's arbitrary choices; `classify_total` — totality and
single-valuedness, with an explicit refusal verdict rather than a guess;
`absent_certifies` — if no hole's statistic lies within the stated radius, no
hole of that type is present; and `classify_named_of_separated`, the separation
condition under which the classifier names a hole. Standard axioms only.

### 33.4 Wiring

`reasoning/deep_hole_classifier.py` with its cache, the report subject
`report hole classifier`, the `deepholes` CLI subcommand, a pipeline row,
generated render blocks, an evaluation case and a 25-test file that includes a
test which fails if any control ever rises to the method's rate.

---

## Phase 34 — the deep-hole ladder: escalating the reading until the law descends

**Status: closed.**

Phase 33 stopped at a sanity check. Phase 34 asks the question that
[`studies/INFORMATION_LOSS_STUDY.md`](../studies/INFORMATION_LOSS_STUDY.md)
exists to make answerable: was that the *geometry*, or the **layer it was read
at**? The law being asked for — *a hole's label is invariant under a change of
ensemble seed* — is a law that must **descend** to the layer, and Phase 33's
reading is not a congruence for the seed sweep.

### 34.1 Pre-registered, again before any measuring code

[`studies/DEEP_HOLE_ESCALATION_STUDY.md`](../studies/DEEP_HOLE_ESCALATION_STUDY.md)
declares a ladder of cells, layer × budget, and the rule for reading it, before
the module exists. Four layers: `L₁`, Phase 33's arrival shares; `L₂`, those
shares **widened by the strays Phase 33 discarded** — the exact defect the
information-loss audit names, a narrow view of a layer that throws away what
the layer below carries; `L₃`, the exact rational measure of emission
distances, compared by an exact 1-Wasserstein integral over `Fraction`; and
`L₄`, the two joined. Three declared budgets — 240, 480, 960 nested starts, so
one ensemble per centre and seed supplies every cell — and §14, committed
before it was run, declares a single **extension** rung at 1920.

### 34.2 What came out

The sanity count, of the ten reference holes, by layer and budget:

| layer | 240 | 480 | 960 | 1920 (extension) |
|---|---|---|---|---|
| `L₁` shares | 3 | 5 | 8 | 8 |
| `L₂` widened | 4 | 8 | 9 | 9 |
| `L₃` rational | 5 | 6 | 7 | 8 |
| `L₄` joint | 6 | 9 | 9 | **10** |

It climbs `3 → 5 → 8` on budget alone and `3 → 4 → 6` on width alone, reaches
**9 of 10** at the best pre-registered cell (`L₄` at 960) and **10 of 10** —
the gate — at `L₄` with 1920 starts. The bottom rung reproduces Phase 33
exactly, 3 of 10, which is the check that the ladder is measuring the same
thing. At the winning cell the full query set is **40 of 44** (90.9 %) against
**12** for the vertex count, **12** for the uniform ablation, **7** for the
digest control and **0** for the reshuffle, with the mean rank of a query's own
reference **1.09**. The passing cell is the extension rung: it is labelled as
one in every table and counted in the multiplicity correction, which is why
`m = 20`. Cost: 38,400 decoder calls over 20 ensembles at 1920 starts, declared
rather than estimated.

Two boundaries are recorded against it. The rational reading **alone**
conflates `A_1^24` with `A_2^12` — neither emits a stray, so its whole distance
measure is one atom — a capacity boundary that appears as a pair of names
rather than as a bound. And the separation criterion `ρ = 2W/B < 1` fails at
every rung, best **2.59**, so the classifier now names holes and still cannot
certify an **absence**: faithfulness needs `r ≥ 0.0659` where separation
permits `r < 0.0179`.

### 34.3 The Lean half

`RequestProject/GLM/DeepHoleEscalation.lean` (namespace `GLM.DeepHoleLadder`),
mirrored byte-identically: `Reading` and `ofMap`; `cumulative` with
`cumulative_ge_left`, `cumulative_ge_right` and `indist_cumulative_iff` — a
widened reading distinguishes everything either half distinguishes, which is
what "cumulative" means here; `nearest_correct` and
`resolves_of_ratio_lt_one` — the separation criterion `2W < B` is *sufficient*
for the nearest-reference rule to be right; `label_descends`; and
`cumulative_can_break_criterion`, a witness that widening a reading can
**break** that criterion even though it refines the reading, which is why the
ladder is measured rather than assumed monotone. The ladder itself is
`firstResolving` with `firstResolving_holds`, `_lt`, `_least` and
`_eq_none_iff`: the least rung that resolves, or a proof that no rung does.

### 34.4 Wiring and directives

`reasoning/deep_hole_escalation.py` with its cache, the report subject
`report hole ladder`, the `escalation` CLI subcommand, a pipeline row, six
generated render blocks, an evaluation case and a 32-test file. The round is
also the first use of **D11**, added to
[`PROJECT_DIRECTIVES.md`](../PROJECT_DIRECTIVES.md) in the same round: a
forbidden operation never cancels an experiment — the site is declared, the
cost is carried, and the round runs. The digest control D3 requires is a
declared SHA-256 site, and the experiment needs it precisely because a digest
carries no meaning. D9 was restated in the same pass: the claim is about the
substrate **and** the machinery used to read it.

### 34.5 What was deliberately not done

The hole set was not enlarged — the same 14 centres and 10 of the 23 types,
with the **13** unreached types reported as unreached and nothing claimed about
them. No secondary statistic was promoted after the numbers were seen; no
pairwise vertex distance, diagram shape or component-size vector was read at
any rung, because those are the label source. Nothing was extrapolated past the
top rung, so `N = 3840` is not guessed at. And the certified-absence theorem
was left un-instantiated rather than run at a radius the data does not support.

Reproduce: `PYTHONPATH=. python3 GLM.py -q "report hole classifier"`,
`"report hole ladder"`;
`python3 -m unittest glm_universal.tests.test_deep_hole_classifier`
`glm_universal.tests.test_deep_hole_escalation`; `lake build`. Write-ups:
[`studies/DEEP_HOLE_STUDY.md`](../studies/DEEP_HOLE_STUDY.md),
[`studies/DEEP_HOLE_ESCALATION_STUDY.md`](../studies/DEEP_HOLE_ESCALATION_STUDY.md).

---

## Phase 35 — what the deep-hole rounds left behind, taken as architecture

**Status: closed.** Four of the items §3.4 was carrying are closed as
mechanisms rather than as stated limitations, and each is in the shape
directive **D5** requires: a module, a study whose every table is generated, a
test file, a pipeline row, and — where there is something to prove — a Lean
file in both copies of the tree.

### 35.1 Escalation as a step of the ordinary query loop

The largest of the four, and the architectural one. A ladder of three rungs
with declared integer costs — `L1` the register reading at 1, `L2` the
semantics reading at 2, `L3` the neighbourhood reading at 4 — declared per
query kind rather than as one tower for everything, with the classification of
a refusal happening before the climb rather than after it. Both gates are
measured over the whole evaluation set: no answer the runtime already gives
moves, none becomes more expensive, and no refusal classified as principled is
converted into an answer. The loop buys something — of 18 declared probes, 4
resolve above the first rung at costs of 3, 5, 5 and 5 against 1 for a direct
answer, and 2 refusals come back as certified absences within a radius of 2
edits.

`RequestProject/GLM/EscalationLoop.lean` proves the loop rather than exercising
it: `climb_principled` (a principled refusal is preserved whatever the rungs
above would have said), `climb_answers_least` (an answer at a rung is a
statement about the rungs below it), `climbFrom_refused_all` (a refusal from a
fully climbed ladder is a statement about every rung), `climb_direct_cost` (a
direct answer costs exactly the first rung) and `climbFrom_cost_ge` /
`climb_total` (a climb costs at least the first rung and never more than the
whole ladder — which is also the termination statement).

`reasoning/query_escalation.py`, `runtime/escalation_loop.py`,
`report query escalation`. Write-up:
[`studies/QUERY_ESCALATION_STUDY.md`](../studies/QUERY_ESCALATION_STUDY.md).

### 35.2 The four failures, and the spread that gates the certificate

The escalated reading names 40 of 44 and certifies nothing. All four failures
are rank-2 near misses sitting on a closest reference pair — which
`GLM.DeepHoleFailure.failure_pair_close` says they had to be — and the type
whose within-type spread stalls the separation ratio, `D_6^4` at `W = 0.0659`
against `B = 0.0358`, is the type the failures belong to. So the two open
questions are one mechanism. The global negative stands (`ρ = 2.5943`, and no
lower than `1.4784` over 55 declared deletions, by `resolves_of_subset` and
`separation_mono`), while read type by type `per_type_correct` certifies 3 of
the 10 types, and `per_type_absent` states the absence the rounds have been
short of under a faithfulness hypothesis the data does not support.

`reasoning/deep_hole_failures.py`, `RequestProject/GLM/DeepHoleFailure.lean`,
`report hole failures`. Write-up:
[`studies/DEEP_HOLE_FAILURE_STUDY.md`](../studies/DEEP_HOLE_FAILURE_STUDY.md).

### 35.3 Cumulativity as a shipping condition

The question that found a real design flaw in the information-loss round is now
a rule with an instrument: 3 declared layer families, 2 of them shipped, 7
declared refinement edges verified on their probe sets, 2 declared non-edges
witnessed, and 0 defects in a shipped family — with the rejected integer
reading kept in the registry so that the check has a defect to catch. The rule
keeps a *conflation* distinct from a cumulativity failure: 32 conflated pairs
are reported beside the edges as resolutions rather than as defects, because
`RequestProject/GLM/CumulativityRule.lean` says reading a layer's view again
cannot repair one (`factored_conflates`, `factor_refined_by`) while reading the
carrier again can, and only if the second reading sees the pair
(`join_separates`, `join_needs_a_second_reading`). `refines_of_le` is why a
chain checked pairwise refines across any gap, and
`refinementChain_cumulativeTower` why a cumulative construction obeys the rule
by construction.

`reasoning/cumulativity.py`, `report cumulativity`. Write-up:
[`studies/CUMULATIVITY_STUDY.md`](../studies/CUMULATIVITY_STUDY.md).

### 35.4 The reverse-call planner, built and not promoted

A problem-driven front end taken from the source material: parse the string
into a problem, then select every tool whose declared precondition it
satisfies. The safety gate holds — 10 of 15 declared tasks answered, all 10
independently checked, 5 of them beyond the plain runtime, no principled
refusal ever reaching it — and the utility gate does not, since it correctly
refuses every evaluation refusal it is offered and would therefore add nothing
to the shipped system today. It stays in `glm_universal/sandbox/` under
directive **D14**, imported by nothing the system computes with, and its
pipeline row declares that wiring is forbidden rather than missing.

Write-up:
[`studies/REVERSE_CALL_PLANNER_STUDY.md`](../studies/REVERSE_CALL_PLANNER_STUDY.md).

### 35.5 The review sweep

Directive **D13**'s unimplemented clause: rank a stalled result for re-reading
by whether the coarse reading discarded an identifiable quantity, not by how
disappointing it was. 8 stalled results are registered — 1 licensed for a
re-reading, 2 already recovered that way, 1 needing a theorem, 4 with nothing
discarded — with 0 entry defects, and the register is written before the next
re-reading, which is the only time it can constrain one.

`reasoning/review_sweep.py`, `report review sweep`. Write-up:
[`studies/REVIEW_SWEEP_STUDY.md`](../studies/REVIEW_SWEEP_STUDY.md).

### 35.6 What was deliberately not done

The planner was not promoted, and the utility gate that would license it is
reported as false rather than relaxed. The separation criterion was not
declared met: 3 of 10 types certified is a per-type reading, and the global
`ρ < 1` is still unreached. The hole set was not enlarged, so the 13 unreached
Niemeier types are still unreached. And no new escalation rung was added to
make a refusal go away: the ladder is three rungs, declared, and a kind with a
one-rung ladder is declared as such.

Reproduce: `PYTHONPATH=. python3 GLM.py -q "report query escalation"`,
`"report hole failures"`, `"report cumulativity"`, `"report review sweep"`;
`python3 -m glm_universal.tools planner`;
`python3 -m unittest glm_universal.tests.test_query_escalation`
`glm_universal.tests.test_deep_hole_failures`
`glm_universal.tests.test_cumulativity`
`glm_universal.tests.test_review_sweep`
`glm_universal.tests.test_sandbox_planner`; `lake build`.

---
