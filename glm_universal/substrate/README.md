# `glm_universal.substrate`

The algebraic and geometric foundation of GLM-3+. Four modules, strictly
layered, pure Python standard library, exact arithmetic, no randomness.

```
linalg.py  ──►  mog.py  ──►  leech2.py  ──►  digit_stack.py
```

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
