# `glm_universal` — GLM-3+, the Universal MOG-Cube Geometric Language Machine

A self-contained, exact, deterministic implementation of the geometric
substrate the Monster group actually acts on, and of the reasoning layers to be
built on top of it.

**Status.** Step 1 (`substrate/`) is implemented and its unit-test suite runs
green. `data_objects/`, `reasoning/` and `benchmarks/` are scaffolded
directories with READMEs stating their contracts; they contain no
implementation yet and nothing in this repository claims otherwise.

---

## 1. Why this package exists

GLM-1 and GLM-2 named the Monster and then did nothing with it: the number
196,884 appeared as arithmetic and the group never acted on anything. The
Monster does not act on the Leech lattice — it acts on structures built on the
quotient **Λ / 2Λ**, and that quotient is where a concept carried by a lattice
point becomes a Monster-theoretic object.

`glm_universal` is a clean re-founding of that idea. Everything above the
substrate is indexed by what `substrate/` builds, and everything `substrate/`
builds is *computed*, not quoted.

---

## 2. Architecture

```
glm_universal/
├── README.md                  ← you are here
├── __init__.py
├── substrate/                 ← Step 1: the algebraic + geometric foundation
│   ├── README.md
│   ├── linalg.py              exact integer / F_2 linear algebra
│   ├── mog.py                 Golay code, hexacode, MOG trio, sextet, cubes
│   ├── leech2.py              Leech lattice, Λ/2Λ, Witt data, 2A axes
│   └── digit_stack.py         10-plane 2-adic stack, facet attribution
├── data_objects/              ← reserved: typed carriers over the substrate
│   └── README.md
├── reasoning/                 ← reserved: inference with facet attribution
│   └── README.md
├── benchmarks/                ← reserved: task suites and scoring
│   └── README.md
└── tests/
    ├── __init__.py
    └── test_substrate.py      73 test functions -> 96 cases with parametrics
```

Dependency direction is strictly downward: `linalg → mog → leech2 →
digit_stack`. `digit_stack` imports `leech2` lazily inside two functions so the
two modules can be read independently; there is no import cycle.

---

## 3. Mathematical principles

### 3.1 The integer model

The Leech lattice is used in the **×√8 integer model**: all coordinates are
integers and the minimal squared norm is `32` rather than `4`. In this model
the true geometric inner product is the integer one divided by `SCALE = 8`, and
`leech2.rational_inner` returns it as an exact `Fraction`. The determinant of
the integral basis is therefore `8^12 = 2^36 = [Z^24 : Λ]`, not 1.

### 3.2 Λ / 2Λ as an F₂ quadratic space

`Λ/2Λ` is a 24-dimensional F₂ vector space (2²⁴ = 16,777,216 classes) carrying

```
q(λ) = (λ·λ)/16  (mod 2)          the quadratic form
B(λ,μ) = (λ·μ)/8 (mod 2)          its polar form
```

Both are well defined on classes — checked, not assumed. The form is
nondegenerate of **plus type**; `leech2.witt_decomposition()` computes an
explicit Witt decomposition into **12 planes** (8 hyperbolic, 4 anisotropic in
the basis this run produced), which puts the singular-class count in closed
form at `2²³ + 2¹¹ = 8,390,656`.

### 3.3 The class census

```
   1   +   98,280   +   8,386,560   +   8,292,375   =  16,777,216  =  2^24
type 0     type 2        type 3          type 4
```

with `98,280 = N(32)/2`, `8,386,560 = N(48)/2` and `8,292,375 = N(64)/48`, the
theta coefficients coming from `E₄³ − 720Δ` computed exactly in
`leech2.theta_series`. Type is a refinement of the quadratic form: the type-3
classes are precisely the non-singular ones.

### 3.4 2A axes

A **type-2 class** is a pair `{±λ}` of minimal vectors — 98,280 of them, the
index set of the middle piece of the Griess ledger and hence of the 2A axes
visible inside the 2B centraliser. Detection is a lookup against the
exhaustively enumerated table, so both answers are proofs.

### 3.5 The MOG trio and sextet

One fixed labelling of the 24 coordinates as a 4×6 frame makes the six columns
a **sextet** of tetrads (any two union to an octad) and the three 4×2 bricks a
**trio** of octads `O₁, O₂, O₃` partitioning the 24. Each brick's eight cells
are the vertices of a 2×2×2 cube, giving every coordinate an address
`(brick, x, y, z)`.

### 3.6 The 10-plane 2-adic digit stack

Reduction mod 2Λ keeps one bit per coordinate and discards the carrier. The
digit stack keeps everything: write each coordinate in binary after a fixed
translation and let plane *k* be the 24-bit mask of the *k*-th binary digit.
A carrier is then not one Monster address but a **stack** of them, and

```python
class_stack_rebuild(class_stack(v)) == v
```

holds exactly. "Ten planes" is a measurement of the data's coordinate range,
not a magic number — see Proposition D1 in `substrate/digit_stack.py`.

---

## 4. Design invariants

These are enforced by unit tests, not merely intended.

| Invariant | Enforced by |
|---|---|
| Exact arithmetic only (`int`, `fractions.Fraction`) | `class_stack` raises `TypeError` on a float; `TestPurity::test_floats_are_rejected_by_the_stack` |
| No randomness anywhere | AST scan of every substrate module for a `random` import |
| Standard library only | AST scan of every substrate module's imports against an allow-list |
| Facts computed, not quoted | `mog_report()`, `leech2_report()` recompute on demand |
| Deterministic | Reports compared for equality across repeated calls |

Test fixtures that need "arbitrary" vectors use an explicit seeded LCG written
out in the test file, so every input is a literal function of its seed.

---

## 5. Quick start

```python
from fractions import Fraction
from glm_universal.substrate import (class_stack, class_stack_rebuild,
                                     is_2a_axis, minimal_vectors,
                                     verify_equation, TRIO, SEXTET)

# a carrier over Q round-trips exactly
v = tuple(Fraction(i, 6) for i in range(24))
assert class_stack_rebuild(class_stack(v)) == v

# 2A axis detection
lam = next(iter(minimal_vectors()))
assert is_2a_axis(lam)                       # a minimal vector is an axis
assert not is_2a_axis([2 * c for c in lam])  # 2λ lies in 2Λ, so type 0

# a false vector equation names where it fails
lhs = tuple(range(-12, 12))
rhs = list(lhs); rhs[10] += 1
verdict = verify_equation(lhs, rhs)
print(verdict.holds, verdict.failing_planes, verdict.blamed_facets)
```

## 6. Running the tests and the verification

```bash
uv run pytest glm_universal/tests/test_substrate.py -q
uv run python workflow/07_step1_substrate_verification.py
```

The second command recomputes every fact, runs the test suite, and writes
`results/step1_substrate_verification.json` plus the Step-1 entries of
`results/claims.json`.

---

## 7. Provenance

Ported and unified from the reference implementation under
`workflow/GLM/glm_lean/`:

| Source | Contributed |
|---|---|
| `glm/glm_substrate.py` | `GolayCode`, `GF4`, `Hexacode`, MOG alignment |
| `glm2/glm2_common.py` | HNF, determinant, triangular solve |
| `glm2/glm2_lattice.py` | Leech congruences, Z-basis, minimal vectors, theta |
| `glm3/glm3_leech2.py` | Λ/2Λ classes, q/B forms, Witt, `class_stack` |
| `glm3/glm3_mog.py` | trio, sextet, cube coordinates, `plane_stack` |

Refinements made during the port, rather than straight copies:

* the substrate is **self-contained** — no `sys.path` shims, no cross-package
  imports, no dependency on `glm_core`;
* type-2 detection is a **table lookup against a self-validating exhaustive
  enumeration** rather than a lattice-decoder call, which removes the decoder
  from the trusted base for axis claims;
* the digit stack is generalised from integer lattice points to **arbitrary
  carriers over Q**, with the cleared denominator travelling in the stack;
* **facet projection and failing-facet attribution** are new: a false equation
  is localised to a plane and to named MOG facets;
* the mislabelled "unimodular" determinant check from the reference is
  corrected to the index `[Z^24 : Λ] = 2³⁶`.
