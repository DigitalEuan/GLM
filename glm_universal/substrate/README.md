# `glm_universal.substrate`

**Parent:** [`../README.md`](../README.md) · **Repository root:**
[`../../README.md`](../../README.md)

The algebraic and geometric foundation of GLM-3+. Ten modules, strictly
layered, pure Python standard library, exact arithmetic, no randomness.

```
linalg.py  ──►  mog.py  ──►  leech2.py  ──►  digit_stack.py
                  │
                  ├──►  golay_decode.py  ──►  isomorphism.py
                  │           │
                  │           └──►  superposition.py
                  └──►  leech_construct.py
```

The first four are the original core; `golay_decode`, `leech_construct` and
`isomorphism` were added in v0.8.0 and `superposition` later; all four are
documented in the final sections of this file. `lattice32.py` and
`lattice48.py`, added in v1.5.0, sit *beside* the 24-dimensional layer rather
than under it: `lattice32` uses only `linalg`, `lattice48` uses nothing from
the package at all, and the only reader of either is
`reasoning/higher_lattices.py`. Nothing in the Leech layer changes because
they are there. They are documented in the last two sections.

`digit_stack` imports `leech2` lazily (inside `_leech_coords` and
`class_stack_rebuild`) so that the two can be read and tested independently.
There is no import cycle.

---

## `linalg.py` — exact linear algebra

| Function | Purpose |
|---|---|
| `popcount`, `bits_of`, `mask_of` | 24-bit mask helpers |
| `hermite_normal_form(rows, ncols)` | row-style HNF; used once to turn a generating set of Λ into an upper-triangular Z-basis |
| `det_int(matrix)` | exact determinant over Q with an integrality assertion |
| `solve_upper_triangular(basis, target)` | coordinates in a triangular Z-basis, or `None` — this doubles as the lattice-membership test |
| `f2_independent`, `f2_rank` | Gaussian elimination over F₂ on integers-as-bit-vectors |

No floats. `det_int` works in `Fraction` and asserts the result is integral.

---

## `mog.py` — the Miracle Octad Generator

### The code

`GolayCode` is the extended binary Golay code `[24, 12, 8]` in systematic form
`G = [I₁₂ | B]` with `B` symmetric, hence `H = [B | I₁₂]` and the code is
self-dual. `GOLAY.census()` recomputes:

```
codewords 4096 · octads 759 · min distance 8 · doubly even · self-dual
weight enumerator  1 + 759 z^8 + 2576 z^12 + 759 z^16 + z^24
```

### The alignment

`ALIGNED_BITS[6*row + col]` is the coordinate index in frame cell
`(row, col)`. This particular permutation is the one under which every Golay
codeword's six GF(4) column labels form a **hexacode** word. That is verified
exhaustively over all 4096 codewords by `mog_report()`, and is not assumed
anywhere.

### The trio and the sextet

```python
TRIO    # (O1, O2, O3): three disjoint octads covering all 24 coordinates
SEXTET  # six 4-cell tetrads; any two union to an octad
```

Both are validated at **import time** by `_validate_geometry()`, so an
inconsistent alignment cannot be silently loaded.

### The MOG-cube trio

`cube_coordinates(i) -> (brick, x, y, z)` addresses each coordinate as a vertex
of one of three 2×2×2 cubes; `coordinate_of_cube` is its inverse;
`face_parities(mask, brick)` gives the six face parities of one cube — the
finest facet used for failure attribution.

### Bijective reshaping

`to_grid_4x6` / `from_grid_4x6` and `to_trio_3x8` / `from_trio_3x8` move a
linear 24-vector between its linear, 4×6 and 3×8 presentations. They are pure
position permutations, so they work for any payload type — bits, `int`,
`Fraction`, even strings — and round-trip exactly.

---

## `leech2.py` — the Leech lattice and Λ/2Λ

### Conventions

The **×√8 integer model**: coordinates are integers, minimal norm is 32.
`rational_inner` / `rational_norm2` return the true geometry as exact
`Fraction`s (dividing by `SCALE = 8`).

### What is computed

* `LEECH_BASIS` — a Z-basis in Hermite normal form, built from an explicit
  generating set (276 vectors `4(eᵢ+eⱼ)`, 759 vectors `2·1_O`, and
  `(-3,1,…,1)`) with every generator checked against the defining congruences.
  `basis_determinant() == 2³⁶ == [Z^24 : Λ]` in this model.
* `class_of` / `representative` — the map `Λ → Λ/2Λ` (a 24-bit integer) and a
  section back.
* `q_form`, `b_form` — the F₂ quadratic form and its polar form, from
  coefficient tables, agreeing with the lattice definition (checked).
* `witt_decomposition()` — **12 planes, plus type**, singular count
  `2²³ + 2¹¹ = 8,390,656`.
* `minimal_vectors()` — streams all 196,560 minimal vectors in three shapes.
* `theta_series()` — `E₄³ − 720Δ` computed exactly with integer arithmetic.
* `type_census()` — the census closing at 2²⁴.

### 2A axis detection

```python
type2_class_table()   # 98,280 classes -> one minimal vector each
is_type2_class(cls)   # lookup
is_2a_axis(point)     # class_of + lookup
axis_of_class(cls)    # the {+λ, -λ} pair
```

The table is built by streaming all 196,560 minimal vectors and reducing each
mod 2Λ. It **self-validates**: it asserts that exactly 196,560 vectors were
seen, that every class was hit exactly twice (a class is `{±λ}`), and that
98,280 distinct classes resulted. Because the enumeration is exhaustive, a
negative answer from `is_2a_axis` is as much a proof as a positive one.

Cost: about 5 seconds of exact integer arithmetic, once per process, cached.

`pair_invariant(v, w) = |v·w| / 8` is the complete Co₀ invariant of a pair of
type-2 classes; `pair_census()` returns the classical distribution
`{4: 2, 2: 9200, 1: 94208, 0: 93150}`.

---

## `digit_stack.py` — the 10-plane 2-adic stack

### The stack

```python
stack = class_stack(v)                    # DigitStack: 10 planes, offset 512
assert class_stack_rebuild(stack) == v    # exact, for every v in range
```

`v` is any 24-vector of `int` / `Fraction`. Rational carriers are cleared by
their least common denominator, which travels in `stack.denominator` and is
reapplied on rebuild — so reconstruction returns the original `Fraction`s with
no rounding at any step. Floats raise `TypeError`.

`basis="leech"` expands the coordinates in the Leech Z-basis instead, so that
`stack.planes[0]` is exactly `leech2.class_of(x)`.

### Proposition D1 — why ten planes

> Let `max_abs` bound the absolute value of the integer coordinates. Let the
> offset `O ≥ max_abs` and the depth `D` satisfy `2^D > O + max_abs`. Then
> every shifted coordinate lies in `[0, 2^D)`, its binary expansion has `D`
> digits, and reassembling `Σ 2^k d_k − O` is the identity.

Faithfulness is a statement about the **range of the data**, not about the
number ten. `derive_stack_parameters(max_abs)` returns the least admissible
pair; `class_stack_fitted(v)` uses it; `depth_report(carriers)` checks the
proposition empirically (deeper stacks append only zero planes, lower planes
do not move).

The defaults `STACK_OFFSET = 2⁹`, `STACK_DEPTH = 10` are the least admissible
pair for `max_abs ≤ 511`. The bound is two-sided and therefore conservative:
`−512` encodes fine, but a dataset reaching `|c| = 512` derives depth 11.

### Facets and attribution

A **facet** is a named subset of the 24 coordinates drawn from the MOG
geometry. There are 31:

| Family | Count | Cells each |
|---|---|---|
| `brick0..2` (trio octads) | 3 | 8 |
| `col0..5` (sextet tetrads) | 6 | 4 |
| `row0..3` (frame rows) | 4 | 6 |
| `cube{b}.{x,y,z}{0,1}` (cube faces) | 18 | 4 |

They overlap by design: a discrepancy is attributed to *every* facet
containing it, which makes the attribution a localisation rather than a
partition.

```python
verdict = verify_equation(lhs, rhs)
verdict.holds                # exact: true iff lhs == rhs as rational vectors
verdict.failing_planes       # which of the 10 planes disagree
verdict.difference_masks     # the XOR at each failing plane
verdict.blamed_facets        # e.g. ('brick2', 'col5', 'row1', 'cube2.x1', …)
verdict.as_dict()            # JSON-serialisable
```

`verify_equation` stacks both sides over a **common denominator** before
comparing, so a rational identity like `1/3 == 2/6` is decided correctly.

**Caveat.** Facet names index MOG cells only for `basis="standard"`. For
`basis="leech"` they index Leech *basis vectors*; the partition is
combinatorially valid but is not MOG geometry. The verdict carries
`mog_geometric=False` and says so in `verdict.note`.

---

## Tests

`glm_universal/tests/test_substrate.py` — 73 test functions (96 cases once
parametrics are expanded) in nine groups: purity,
linalg, Golay/alignment, trio/sextet/cube, reshaping, Leech basis, quadratic
form, 2A axis detection, digit stack, facets, reports.

```bash
uv run pytest glm_universal/tests/test_substrate.py -q
```

## Known limits of this layer

* **No Leech decoder.** Type 3 and type 4 of an *arbitrary* class are not
  computed pointwise; only their counts appear, from the theta series.
  `is_2a_axis` is complete and exact, but there is no `type_of_point`.
  Add a decoder here if a later step needs per-class type 3/4 resolution.
* **One alignment.** `ALIGNED_BITS` fixes a single labelling of the 24
  coordinates. Every trio/sextet/facet name is relative to it. M₂₄ is not
  implemented, so there is no way yet to move between alignments.
* **Facet attribution is bit-level, not semantic.** It says *where* two
  carriers differ in the MOG geometry. It does not say why.

---

## v0.6.0 update: the multi-MOG-cube is operational

The `digit_stack` module IS the multi-MOG-cube from
`glm_lean/glm3/glm3_mog.py`.  Verified on a real Leech basis vector:

* plane 0 is constant (all 24 cells equal — the mod-2 parity frame)
* plane 1 is a Golay codeword (a valid member of `GOLAY_SET`)
* the mod-8 sum condition holds (`sum(x) ≡ 4·(x_0 mod 2) mod 8`)

Every `DataObject.stack()` produces this stack of MOG frames, and
`obj.plane_grids()` shows each plane as a 4×6 grid.

The `leech2.theta_series` function computes the Leech theta series
`E_4^3 - 720*Delta`, which is the bridge to the Moonshine layer
(`reasoning/moonshine.py`, added in v0.6.0).  The j-function is
`E_4^3 / Delta + 744`, and its first non-trivial coefficient is
196884 = dim V_2 = the dimension of the Griess algebra that the
substrate's `leech2` module indexes via the 98,280 type-2 classes.

---

# v0.8.0: three new substrate modules

## `golay_decode.py` — complete decoding, and honest failure

The legacy substrate used a *snap* routine: scan the 4,096 codewords, keep the
nearest, break ties arbitrarily.  That is fast and almost always right, and its
two failure modes were silent.  `golay_decode` replaces it with a syndrome/coset
construction that makes both failures explicit.

| Object | Content |
|---|---|
| `coset_table()` | all 4,096 cosets of the code in `F_2^24`, each with its full set of minimum-weight leaders |
| `coset_census()` | `cosets 4096`, leaders by weight `{0:1, 1:24, 2:276, 3:2024, 4:1771}`, `12951` leaders in total |
| `decode_complete(word)` | a `Decoding` record: codeword, error, coset weight, `status` in `corrected` / `ambiguous`, and `guaranteed` |
| `decode_or_detect(word)` | returns `None` rather than a wrong answer whenever the coset weight exceeds the packing radius 3 |
| `is_guaranteed_decodable(word)` | the declared-radius predicate |

The two structural facts the census records:

* **Covering radius 4 > packing radius 3.**  The 1,771 weight-4 cosets each have
  **six** leaders — the six tetrads of a sextet.  Nearest-codeword decoding there
  is a *choice*, not a deduction, so `decode_complete` reports `ambiguous` and
  `decode_or_detect` refuses.  `legacy_snap_decode` silently picked one.
* **Weight-5 miscorrection is not a bug.**  `weight5_miscorrection_report()`
  samples weight-5 errors and finds every one of them at coset weight 3: by
  `S(5,8,24)` each 5-set lies in a unique octad, so the received word sits at
  distance 3 from that octad and 5 from the truth.  The decoding is unique,
  inside the packing radius, and wrong.  The remedy is a declared channel bound,
  not a better decoder — which is exactly what `guaranteed` exposes.

`steiner_system_report()` verifies the `S(5,8,24)` property directly;
`decoder_comparison_report()` runs snap and complete decoding side by side and
counts the divergences.

## `leech_construct.py` — the A/B/C ladder to 196,560

Construction A alone (`2 * Golay + 4 * Z^24`, scaled) is a lattice with minimal
norm² 16 and a kissing number of **48** — the `(±4, 0^23)` shape only.  This
module builds the ladder and measures each rung:

| Level | Conditions | min norm² | kissing | shapes |
|---|---|---|---|---|
| `A` | mod-2 Golay support | 16 | 48 | `(±4, 0^23)`: 48 |
| `B` | + mod-4 even parity | 32 | 98,256 | `(±4², 0^22)`: 1,104; `(±2^8` on an octad`)`: 97,152 |
| `C` | + mod-8 coordinate-sum condition and the odd glue coset | 32 | **196,560** | the two above plus `(∓3, ±1^23)`: 98,304 |

`kissing_of_level('C')` returns 196,560 with `no_duplicates` and `all_in_level`
true, and `agrees_with_leech2()` checks the result against the independently
built `leech2` module.

The multi-mod system the ladder needs is exposed directly:

* `mod_profile(v)` — the residue signature of a vector at moduli 2, 4 and 8;
* `mod_sieve(...)` — filter any vector family by any combination of the moduli;
* `even_parity`, `golay_support`, `golay_condition`, `sum_condition` — the four
  predicates, individually callable;
* `necessity_report()` — drops each condition in turn and shows the packing
  break it causes, so no condition is decoration.

`projection_lattice_basis` and `supported_sublattice_basis` give exact Z-bases
for the sub-lattices used by the facet and multi-resolution layers.

## `isomorphism.py` — the legacy ↔ core bridge

`LEGACY_TO_CORE` is the coordinate permutation between the historical GLM
labelling and the canonical `glm_core` frame; `CORE_TO_LEGACY` is its inverse.
`permute_mask` moves the bit at coordinate `i` to `perm[i]`.

| Group | Functions |
|---|---|
| permutation algebra | `is_permutation`, `invert_permutation`, `compose_permutations`, `permute_mask/vector/indices` |
| frame changes | `to_core_mask`, `to_legacy_mask`, `to_core_vector`, `to_legacy_vector` |
| addresses | `hexcolour_to_mask`, `mask_to_hexcolour`, `migrate_hexcolour` |
| the two codes | `legacy_code`, `shared_codewords`, `weight_distribution`, `is_golay_automorphism`, `code_report` |
| decoding | `decode_legacy`, `legacy_snap_in_legacy_frame`, `legacy_decoder_comparison` |
| migration | `MigrationSpec`, `CONCEPT_SPEC`, `EDGE_SPEC`, `HEXCOLOUR_SPEC`, `migrate_record/records/dataset`, `sample_dataset`, `migration_report` |

Measured facts, all asserted in the tests:

* the permutation is **not** a Golay automorphism — `is_golay_automorphism()`
  returns false with a witness codeword whose image leaves the code (4,088 of
  the 4,096 canonical codewords do);
* the two codes nevertheless share exactly **8** codewords, matching the Step-5
  note in `TopLevel_README.md`, and have identical weight distributions
  `{0:1, 8:759, 12:2576, 16:759, 24:1}` and minimum distance 8;
* the permutation is an **isometry** — `isometry_report()` confirms Hamming
  weight and distance are preserved, so decoding commutes with the frame change
  (proved in Lean as `decoding_commutes`);
* the fixed points are `[0, 1, 2, 3, 4, 5, 8]`;
* running the sample dataset through both decoders turns **24** silent snap ties
  into 24 explicit `"ambiguous"` results, while the weight-5 miscorrection —
  which is mathematical, not implementational — survives in both columns.

`migrate_dataset` is the single entry point for the bulk migration of the
concept, CRG-edge and hexcolour tables; `migration_report()` is what the
runtime's `report migration` query calls.

**Update.** That last sentence used to end "once the `glm_core` data tree is
available". It is available, and the migration has been run on it: see
[`../migration/README.md`](../migration/README.md), which uses this module's
frame machinery to bring 4,282 stored concepts and 4,014 CRG edges into
canonical form (plus 398 carriers minted for names the source referred to but
never defined), writing `arc_agi_17/results/glm_state_canonical.json`. The
first finding of that work was that the stored concept vectors are *already* in
the canonical frame, so `LEGACY_TO_CORE` must **not** be applied to them; the
stored integer addresses, by contrast, are MSB-first and do need the bit
reversal. `report migration` covers the frame bridge described here; `report
state migration` covers the data run.


---

# `superposition.py` — ambiguity as a first-class value

`golay_decode.py` reports a weight-4 coset as `ambiguous` and stops. This
module is what happens if it does not stop: the six equally-near readings are
kept together as one value, carried, combined, and collapsed only when a
context says which one is meant. Everything is `int` and `Fraction`; no float
is constructed.

| Object | Content |
|---|---|
| `superpose(word)` / `Superposition` | the frozen, ordered set of nearest codewords of a received word, with its `dimension` (1 when the reading is unique, 6 at a deep hole) |
| `bundle_f2(words)` | the VSA bundle over F₂ — the XOR of the members |
| `bundle_rational(words)` | the bundle over Q — the coordinatewise mean, an exact 24-tuple of `Fraction` |
| `recover_from_bundle(vec)` | reads the member set back out of a rational bundle |
| `collapse(sup, context)` / `Collapse` | filters the members by a context predicate; `collapsed` (one survivor), `superposed` (several) or `refuted` (none) — it never breaks a tie by member order |
| `sextet_cycle_reading(sup, ticks)` | the time average of a carrier that cycles through the members |
| `sextet_partition_report`, `bundling_report`, `collapse_report`, `alphabet_expansion_report`, `superposition_report` | the measured findings below, recomputed on call |

Measured facts, all asserted in the tests and all matching the Lean statements
in `Golay/Sextet.lean`, `Superposition.lean`, `Wobble.lean` and
`HullExpansion.lean`:

* over **64** tetrads checked, the number of nearest codewords of a weight-4
  coset is always exactly **6**, those six differ pairwise in exactly 8
  coordinates, and their supports relative to the received word partition all
  24 coordinates into six disjoint tetrads — the sextet;
* over **256** superpositions checked, the F₂ bundle takes exactly **one**
  value, `16777215` = all ones. The XOR of a six-fold tie is the all-ones
  vector whatever the tie is, so an F₂ bundle distinguishes **1** of the 256
  inputs: at this arity the binary bundle is information-free;
* the rational bundle of the same six words has coordinates only in
  `{1/6, 5/6}`, is **injective** over all 256 inputs, and `recover_from_bundle`
  returns the members exactly. Ambiguity survives in a rational carrier and
  dies in a binary one;
* collapse is contextual, not positional: on the weight-4 word `15` a context
  naming one member yields `collapsed`, a context naming several yields
  `superposed` with that many survivors, and a context naming none yields
  `refuted` rather than a guess;
* alphabet expansion, not rescaling, is what buys reach: with the functional
  `(7, −1, …, −1)` the target `½·e₀` sits at `7/2` while every one of the
  **4,096** scaled codewords sits at `≤ 0`, so no schedule over that alphabet
  reaches it; admitting the two Leech vectors `±4e₀ ± 4e₁` reaches it exactly
  in a **16**-tick cycle.

---

## `lattice32.py` — the 32-dimensional extremal lattice

Construction A over a binary code cannot beat minimum 2 in any dimension: the
vectors `2 e_i` are always there. The rung above the Leech lattice therefore
needs a **two-level** lift, Construction D, over a nested pair of Reed–Muller
codes:

```
L  =  4 Z^32  +  2 C1  +  C2,    C2 = RM(1,5) ⊂ C1 = RM(3,5),   Λ_32 = L / 2
```

In the unscaled integer model a lattice norm is `|x|²/4`, so minimum 4 means
`|x|² ≥ 16` and evenness means `8 | |x|²`.

| Function | What it returns |
|---|---|
| `outer_basis`, `inner_basis`, `outer_code`, `in_outer`, `in_inner` | the two Reed–Muller codes, built from monomial masks rather than tabulated |
| `code_report()` | outer `[32, 6, 16]` (64 words, weights `{0, 16, 32}`, 62 of weight 16); inner `[32, 26, 4]` (1,240 words of weight 4, 0 lighter); `nested` and `is_dual_pair` both true |
| `mk`, `address`, `from_address`, `in_lattice` | the **three-resolution address** `(fine, middle, coarse)` — a `4Z^32` part, a `C1` bit-mask and a `C2` bit-mask — and its exact inverse |
| `resolution_sieve`, `index_ladder` | which resolution a point is visible at, and the index chain `[Λ : 4Z^32] = 2^32` |
| `minimum_certificate()` | the minimum proved by three disjoint cases on the address, each closed by one code property: `c ≠ 0` by outer weight 16, `c = 0 ≠ b` by inner weight 4, `b = c = 0` by divisibility. All three give `\|x\|² ≥ 16`, so `min = 4` — extremal in dimension 32. The Lean statement is `GLM.HigherLattices.BarnesWall.norm_ge_of_ne_zero` |
| `determinant_report()` | basis determinant `2^32`, Gram determinant `2^64`, scaled determinant `1` — unimodular — with evenness checked on the diagonal and the off-diagonal products |
| `minimal_vectors`, `minimal_shape_census`, `kissing_number` | the minimal vectors enumerated by shape: `126,976` of shape `(±1^16, 0^16)`, `19,840` of `(±2^4, 0^28)`, `64` of `(±4, 0^31)` — **146,880** in total, counted rather than quoted |
| `lattice32_report(verify_all=False)` | all of the above in one dictionary |

## `lattice48.py` — the 48-dimensional extremal lattice

In dimension 48 the extremal minimum is `2 + 2·⌊48/24⌋ = 6`, and the honest
finding of this module is that **no binary code reaches it**.

*The binary route, and where it stops.* `binary_generator`,
`binary_code_report` and `binary_minimum_distance` build the extended quadratic
residue code `QR(47)` from the residues mod 47 and verify that it is a
`[48, 24, 12]` self-dual doubly even code (the distance exhaustively behind a
flag, by walking all `2^24` codewords in Gray-code order). Construction A over
it still contains `2 e_i`, of norm 2 in the `|x|²/2` model, so the binary
lattice is stuck four short of extremal.

*The ternary route, which works.* Over `F_3` the trivial vectors are `3 e_i`,
of norm 3 in the `|x|²/3` model, and there is room.

| Function | What it returns |
|---|---|
| `legendre`, `jacobsthal`, `symmetry_matrix`, `ternary_generator` | the Pless symmetry code `C(23)`, generator `[I_24 \| S]` with `S` the bordered Jacobsthal matrix of 23 — built, not tabulated |
| `ternary_code_report()` | `S Sᵀ = −I (mod 3)`, self-dual, every weight divisible by 3, generator rows of weight 24 and generator pairs of weight 15 |
| `ternary_minimum_distance`, `weight_enumerator` | an information-set search that finds weight 15 and excludes everything up to 8; the MacWilliams weight enumerator, all coefficients non-negative integers summing to `3^24`, minimum weight 15, `A_48 = 96` |
| `construction_a_report()` | `A = {x ∈ Z^48 : x mod 3 ∈ C(23)}`, index `3^24` in `Z^48`, scaled determinant 1 — unimodular but **odd**, because `3 e_i` has norm 3 |
| `even_sublattice_report()` | the index-2 even sublattice, and the minimum closed by two cases: off the code the support is ≥ 15 and `6 \| \|x\|²`, so `\|x\|² ≥ 18`; on the code `9 \| \|x\|²` and `6 \| \|x\|²` force `18 \| \|x\|²`. Minimum norm 18, i.e. **6**, attained by `3e_0 + 3e_1`. The Lean statement is `GLM.HigherLattices.Ternary.even_norm_ge_eighteen` |
| `neighbour_report(exhaustive=False)` | the two glue vectors `h = (3/2, …)` of norm 36 and `h' = (9/2, 3/2, …)` of norm 42, both even, differing by `3 e_0`; the full-weight census of 96 words, cross-checked against `A_48` |
| `lattice48_report(exhaustive=False)` | all of the above in one dictionary |

Both modules are exercised by `tests/test_lattice_high.py` and read by
`reasoning/higher_lattices.py`, which is what `report lattices` answers from.
