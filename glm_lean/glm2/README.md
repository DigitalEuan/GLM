# The Geometric Language Machine, second generation (GLM-2)

Exact semantics on a **Leech-lattice carrier**: ten rational dimension
exponents, a decimal scale, tensor rank and three parities, written into
`Λ₂₄`, composed by addition in `ℤ²⁴`, and repaired by nearest-point decoding.
Above it: `Aut(Λ) = Co₀`, constructed rather than quoted, and a verified
commutative non-associative axial algebra layer.

Standard library only — no third-party dependencies, Python 3.8+.
The first generation lives in [`../glm`](../glm) and is **reused, not copied**.

---

## Run it

Everything must be run from inside this directory (the modules import their
siblings by bare name, and `glm2_common` puts `../glm` on the path).

```bash
cd glm2
python3 glm2_paper.py            # the paper's verification run: 58 claims, ~50 s
python3 glm2_paper.py --quick    # skips the exhaustive sweeps, ~14 s
python3 glm2_paper.py --json     # writes results/glm2_results.json only
python3 glm2_reasoner.py         # the companion's demonstration
python3 test_glm2.py             # the test suite: 256 tests, ~25 s
```

Individual modules self-audit when run directly:

```bash
python3 glm2_meaning.py   python3 glm2_library.py   python3 glm2_parse.py
python3 glm2_lattice.py   python3 glm2_codec.py     python3 glm2_conway.py
python3 glm2_axial.py
```

The reasoner is also a command-line tool:

```bash
python3 glm2_reasoner.py check energy "mass*speed^2"
python3 glm2_reasoner.py check energy "mass*speed^4"
python3 glm2_reasoner.py check torque "moment(position, force)"
python3 glm2_reasoner.py name  "cross(electric_field, magnetic_field_h)"
python3 glm2_reasoner.py solve speed energy mass
python3 glm2_reasoner.py pi    force density speed length
python3 glm2_reasoner.py show  energy
python3 glm2_reasoner.py transmit energy 7
python3 glm2_reasoner.py near  torque
python3 glm2_reasoner.py convert kilometre length
python3 glm2_reasoner.py symmetry energy
python3 glm2_reasoner.py list  mechanics
```

---

## Files

| file | what it is |
|---|---|
| `glm2_paper.py` | **the paper**: the whole write-up in the module docstring (abstract, §1–§13), plus an operational run that verifies 58 numbered claims and writes `results/glm2_results.json` |
| `glm2_reasoner.py` | **the companion implementation**: audit, solve, Buckingham Pi, telemetry, transmit/repair, neighbours, symmetry, convert, identify — plus the CLI above |
| `glm2_meaning.py` | the meaning module `M = ℚ¹⁰ ⊕ ℚ ⊕ ℤ ⊕ (ℤ/2)³ ⊕ labels`, the group law, the operator algebra (contraction, cross, moment), the derived T and C gradings, and (§3, appendix) the rejected F₂ carrier |
| `glm2_library.py` | the register: 660 concepts across 26 domains, 222 scalar defining relations, 71 full-meaning tensor relations, six affine scales |
| `glm2_parse.py` | the expression language: recursive descent, rational exponents, powers of ten only, and the named operators `dot cross moment grad div curl rot laplacian ddt integral_dt integral_dV` |
| `glm2_lattice.py` | the Leech lattice in the integer (×√8) model: `in_leech`, the index `2³⁶`, an HNF basis, the theta series from `E₄³ − 720Δ`, the `j`-series, and an exact maximum-likelihood decoder with a slow reference implementation to check it against |
| `glm2_codec.py` | the 24-slot layout, the bijection meaning ↔ lattice point, composition, capacity, and repair |
| `glm2_conway.py` | `Aut(Λ) = Co₀`: monomial generators from M₂₄ and the Golay basis, a sextet element found by search, orbit censuses, the `Λ/2Λ` representation, and a randomised Schreier chain giving a rigorous order lower bound |
| `glm2_axial.py` | exact linear algebra over ℚ, the `Algebra` class, the Jordan algebra of symmetric matrices, and Matsuo algebras of 3-transposition groups with Jordan-type fusion and Miyamoto involutions |
| `glm2_common.py` | the shim that imports the first-generation Golay code and M₂₄ from `../glm` |
| `test_glm2.py` | 256 unit tests across every module |
| `results/glm2_results.json` | the machine-readable output of the last paper run |

The formal companion is [`../RequestProject/GLM2.lean`](../RequestProject/GLM2.lean)
(Lean 4 + Mathlib, no `sorry`, no new axioms): the torsion obstruction, the
mod-2 ceiling and its rational strengthening, the derived gradings as
homomorphisms, the two cross products, unique decoding inside the packing
radius, the lattice and Griess ledgers, and the Matsuo algebra of `S₃`.

---

## What changed from GLM-1

| question | GLM-1 | GLM-2 |
|---|---|---|
| meaning | `ℤ⁷` | `ℚ¹⁰ ⊕ ℚ ⊕ ℤ ⊕ (ℤ/2)³ ⊕ labels` |
| fractional powers | no | yes, exactly |
| angle / solid angle / bit | no | yes |
| decimal scale | no | yes |
| tensor rank, P, T, C | no | yes |
| operations | product only | tensor product, contraction, two cross products, grad/div/curl/rot/laplacian, d/dt, ∫dt, ∫dV |
| carrier (derived in both) | `F₂²⁴` | `Λ₂₄` |
| carrier capacity | `2²⁴` (`9⁷` used) | countably infinite |
| composition in the carrier | not possible: XOR of two words is not the word of the product | addition in `ℤ²⁴` on the torsion-free slots |
| separation of concepts | Hamming, can be 1 | squared distance ≥ 32 |
| repair | snap: changes the concept | decode: restores it |
| symmetry group built | M₂₄, 2.4 × 10⁸ | Co₀, 8.3 × 10¹⁸ |
| algebra above | claimed; was associative | Jordan and Matsuo, verified |

---

## Where mod 2 is, and where it is not

The one thing GLM-2 is strict about. **No exponent is ever reduced modulo
anything**: exponents are rationals compared by exact equality. The system
contains exactly three `ℤ/2`s, and every one of them is a *parity* — a sign —
where `ℤ/2` is the honest answer and not an approximation.

`mod2_shadow` and `mod2_confusable` are still there, but they live in the
**appendix** of `glm2_meaning.py` (§3) and reach the outside world through one
deliberately named entry point, `Reasoner.mod2_ceiling(pairs)`. They are a
measurement of a rejected design, not a second opinion: no audit, no verdict
and no telemetry record carries a mod-2 field, and `Meaning` has no `.mod2()`
method at all. Formally (see `GLM2.lean`), the situation is sharper than in
GLM-1: because `ℚ¹⁰` is divisible, *every* additive map from the GLM-2 meaning
module into a group of exponent 2 is identically zero. An XOR carrier is not
lossy on GLM-2's meanings, it is blind.

---

## Meaning is the state; the lattice point is a view

A concept **is** its meaning — the ten rational exponents, the scale, the rank,
the parities and the two labels. The Leech point is `encode(meaning)` and
nothing else: a pure function of the state, cached by the reasoner and
droppable at any time without changing an answer. There is no API anywhere in
GLM-2 that accepts a lattice point in place of a meaning, so a concept cannot
be given a carrier its meaning does not produce.

```python
REASONER.carrier("energy")            # derived: encode(REASONER.meaning("energy"))
REASONER.carrier_is_derived("energy") # True: encode(m) is the point, and it decodes back to m
REASONER.telemetry("energy")["carrier_is_derived"]
REASONER.mod2_ceiling([("energy", "mass*speed^4")])   # appendix, not a verdict
```

Composition follows the same direction. The product of two quantities is
computed on meanings, `m₁ + m₂`, and its carrier is `encode(m₁ + m₂)` — which
is exactly what `compose(x₁, x₂)` returns, and which agrees with `x₁ + x₂` on
every torsion-free slot (the ten exponents, the scale and the rank). Repair
goes meaning-first too: a corrupted point is decoded and then read as a
meaning, so it either returns the original concept or reports that the point
carries no meaning at all. All of this is checked over the whole register by
[Claim C58] and by `TestCarrierIsDerived` in the test suite.

---

## The derived gradings

Of the three parities only **P** (space inversion) is stored. The
time-reversal and charge-conjugation gradings are computed from the exponents,

```
T(m) = (e_T + e_I + t) mod 2        C(m) = (e_I + c) mod 2
```

with `t`, `c` *anomaly* bits that are almost always zero. Two things follow,
and both are checked on every run:

* T and C are additive over products, quotients and rational powers for free —
  there is no way to tag a concept inconsistently, which is exactly the failure
  a hand-maintained parity column invites;
* they are right: the derived T grading reproduces the textbook behaviour of
  position, velocity, momentum, energy, power, charge, current, E, B,
  resistance, capacitance, action and the rest with no table at all, and `ddt`
  flips it for every concept in the register.

The register uses the anomaly exactly once, for
`particle_electric_dipole_moment`: a permanent EDM is dimensionally
charge × length, which the convention grades T-even, yet the observable is
T-odd — which is precisely why measuring one would signal CP violation. The
reasoner then refuses to equate it with an ordinary dipole moment, and says
`parity mismatch: T`.

---

## The operator algebra

Multiplying quantities is only one of the ways concepts combine. Plain
juxtaposition (`*`) is the **tensor product**, so `force * position` is a
rank-2 tensor. The operations that are not the tensor product have names:

| written | is | rank | parity | angle |
|---|---|---|---|---|
| `dot(a, b)` | full contraction | `rank a + rank b − 2` | adds | — |
| `cross(a, b)` | plain cross product | 1 | adds | — |
| `moment(a, b)` | rotational cross product | 1 | adds | `A⁻¹` |
| `grad(x)` | `∇ ⊗ x` | `+1` | flips | — |
| `div(x)` | `∇ · x` | `−1` | flips | — |
| `curl(x)` | `∇ × x` | 1 | flips | — |
| `rot(x)` | `∇ ×_rot x` | 1 | flips | `A⁻¹` |
| `laplacian(x)` | `div(grad(x))` | unchanged | unchanged | — |
| `ddt(x)` | `d/dt` | unchanged | unchanged | — |
| `integral_dt(x)`, `integral_dV(x)` | `∫ dt`, `∫ dV` | unchanged | unchanged | — |

Every differential operator is built from the single meaning
`nabla = L⁻¹, rank 1, P-odd`, so that the curl of a polar vector is axial and
the Laplacian is neutral because of what `∇` is, not because of a table.

`cross` and `moment` are deliberately different operations. Once the plane
angle is a dimension, the cross product that converts between rotation and
translation consumes a radian — torque is joules per radian, angular momentum
is joule-seconds per radian, `v = ω × r` turns radians back into metres — and
the one that does not (`S = E × H`) does not. Using one operation for both is
the move that makes torque look like energy. The same split appears one level
up as `curl` (Maxwell) versus `rot` (vorticity), and with it all four Maxwell
equations hold in the **full** meaning, rank and parities included.

---

## What is verified, and what is quoted

Verified by execution, every run:

* the register: 660 concepts, 222 scalar relations, 71 full-meaning tensor
  relations, all exact;
* the lattice: `in_leech` from the defining congruences, the index `2³⁶`, an
  HNF basis of determinant `2³⁶`, 196,560 minimal vectors enumerated from the
  Golay code and agreeing with the theta series `E₄³ − 720Δ`;
* the decoder: agreement with a slow reference implementation, the Voronoi
  condition against all 196,560 minimal-vector translates, and exact repair of
  every corruption of squared magnitude ≤ 7;
* Co₀: every generator verified to preserve `Λ`, the sextet signs found by
  search (exactly 32 of 64 patterns work), the monomial orbit census
  `1104 / 97152 / 98304`, transitivity of the full group on the 196,560
  minimal vectors, the type-2 orbit of size 98,280 in `Λ/2Λ`, and a rigorous
  **lower** bound of 8,315,553,613,086,720,000 for the order from a randomised
  Schreier chain;
* the algebras: the Jordan algebra of symmetric matrices and the Matsuo
  algebras of `S₃`, `S₄`, `S₅` — commutative, non-associative, Frobenius form,
  Jordan-type fusion, Miyamoto involutions that are genuine automorphisms, and
  at `η = 1/4` the Norton–Sakuma 2A structure constants.

Quoted as classical and labelled as such in the paper:

* the **upper** bound `|Aut(Λ)| = |Co₀|` (the lower bound is proved here);
* the identification of the 196,884-dimensional Griess algebra with the
  Monster's.

Not built, and the paper says so: the Griess algebra itself, the Ising-type
dihedral algebras 3A/4A/4B/5A/6A, and the Monster.

---

## Corrections carried forward from GLM-1

* GLM-1's "snap-based Griess product" was commutative **and associative**,
  hence not Griess-like. The honest replacements are the Jordan and Matsuo
  algebras of `glm2_axial.py`, both verified non-associative.
* Snapping to the nearest codeword is error *detection* dressed as error
  correction: it replaces the concept it is meant to protect. GLM-2 repairs by
  nearest-point decoding in `Λ`, which returns the original concept unchanged
  whenever the corruption has squared magnitude at most 7, and reports
  `meaning = None` rather than guessing when the received point carries no
  meaning at all.

---

## Invariants for future work

0. Meaning is the state and the carrier is a derived view of it. A lattice
   point is never an input, never settable, and never composed on its own; if
   a question can be answered from the meaning, it is.
1. Meaning is exact. No floats, no tolerances, no reduction of exponents.
2. The encoder is injective with a computable inverse, and a homomorphism on
   the torsion-free part.
3. The carrier is `Λ`; every carrier point satisfies `in_leech`.
4. Distinct meanings stay at squared distance at least 32.
5. Repair is nearest-point decoding; nothing may "repair" a concept into a
   different concept.
6. Every claim in the paper is verified by executing it.
7. Classical facts used but not reproved are labelled in the text.
8. New concepts go in `glm2_library.py` with at least one defining relation.
9. The first-generation modules in `../glm` are reused, not copied.
10. The T and C gradings stay derived. A new concept may set an anomaly bit,
    with a comment saying which physics forces it; it may not be given a
    free-floating parity column.
11. Every operation on meanings that is not the tensor product has a name.
    Contraction, the plain cross product and the rotational cross product are
    three different operations and are never silently identified.
