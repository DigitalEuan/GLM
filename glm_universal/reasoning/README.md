# `glm_universal.reasoning` — the algebraic and geometric reasoning kernel

**Status: implemented (GLM-3+ Step 3).** Four modules, one frozen data file, a
62-test suite, and a runnable audit. Everything is exact `int` /
`fractions.Fraction` / `F_2`; nothing here imports `random`; nothing here
imports a third-party package.

| module | what it provides |
| --- | --- |
| `product.py` | the Norton–Sakuma `2A` algebra over the substrate's type-2 classes |
| `metric.py` | the positive-definite Griess form on `Q^24`, exact distances and exact clustering |
| `analogy.py` | `A : B :: C : D` by displacement, then projection onto candidates, the Golay code, or `Λ` |
| `verifier.py` | the 222 + 71 physical relations audited plane by plane, with 31-facet attribution |
| `_data/physics_relations.json` | frozen relation *statements* (data, not an oracle) |

---

## 1. `product.py` — the `2A` product algebra

Axes are indexed by the 98,280 **type-2 classes** of `Λ / 2Λ` that
`substrate.leech2` enumerates exhaustively. Two axes sit in one of four mutual
positions, decided by the `Co_0` pair invariant `|⟨λ, μ⟩| / 8`:

| invariant | position | product | count against a fixed axis |
| --- | --- | --- | --- |
| 4 | `1A` (same axis) | `a · a = a` | 2 |
| 2 | `2A` | `(1/8)(a + b − a_ab)` | 9,200 |
| 1 | **not modelled** | raises `PositionError` | 94,208 |
| 0 | `2B` | `0` | 93,150 |

The counts are the full census of the 196,560 minimal vectors, recomputed by
`leech2.pair_census`, not quoted.

**Why invariant 2 is the `2A` position.** It is the only position in which the
third axis exists inside the substrate: `a_ab` is the axis of the class
`u XOR v`, and `u XOR v` is of type 2 exactly when the invariant is 2 — because
`norm(λ ± μ) = 64 ± 2⟨λ, μ⟩` hits the minimum 32 precisely at `|⟨λ, μ⟩| = 16`.
This is an *operational* definition grounded in the substrate. The module
verifies that the Sakuma `2A` relations close there; it does not claim a proved
correspondence with the Monster's `2A` conjugacy class.

**What `two_a_subalgebra(u, v)` checks, per pair, from scratch:**

- closure in exactly three dimensions — `span{a_u, a_v, a_{u^v}}`;
- commutativity;
- **non-associativity**, with an explicit witness: `(a·a)·b ≠ a·(a·b)`;
- the Gram matrix is `1` on the diagonal and `1/8` off it.

**The Miyamoto maps are derived, not tabulated.** `fusion_spectrum` solves
`(ad_a − λI)x = 0` exactly over `Q^3` at the four Ising eigenvalues and finds
dimensions `1, 1, 1, 0` for `1, 0, 1/4, 1/32`. Since `τ_a` is by definition
`−1` on the `1/32`-eigenspace and that eigenspace is **empty**, `τ_a` comes out
as the **identity** on the `2A` subalgebra — which is the correct classical
answer (`⟨τ_0, τ_1⟩` is a Klein four-group, and conjugation in an abelian group
is trivial), and it is computed rather than assumed. The nontrivial
automorphism that fixes `a_u` and swaps `a_v ↔ a_{u^v}` is `σ_a`, `−1` on the
`1/4`-eigenspace; the module checks it is an algebra automorphism and an
isometry of the form.

Anyone expecting `τ_a` to permute the axes should read that paragraph twice:
the swap is real, but it belongs to `σ`, not `τ`.

## 2. `metric.py` — the Griess metric

`⟨u, v⟩ = (1/8) Σ u_i v_i`, extending `leech2.rational_inner` from the lattice
to all of `Q^24`; `d(u,v)² = ⟨u−v, u−v⟩`.

Positive definiteness is established **twice**, both exactly: the diagonal of
the form on the standard basis, and Sylvester's criterion on all 24 leading
principal minors of the Leech Gram matrix in integer arithmetic (its
determinant comes out `1` — `Λ` is unimodular).

Because `d` itself is usually irrational, **squared** distances are the primary
object and every ordering, merge height and comparison uses them. Two places
need care, and both are handled algebraically rather than numerically:

- **the triangle inequality** is genuinely a statement about `d`, not `d²`. With
  `s = d(u,v)² − d(u,w)² − d(w,v)²`, the claim is `s ≤ 2√(ab)`, decided by
  `s ≤ 0 or s² ≤ 4ab` — exact rationals throughout;
- **angles**: `signed_cosine_squared` returns `sign(⟨u,v⟩)·cos²`, a strictly
  increasing function of the cosine and always rational, so `compare_cosines`
  orders by angle exactly with no `arccos`.

`single_linkage` and `complete_linkage` are exact agglomerative clustering with
`Fraction` merge heights and deterministic tie-breaking by cluster id.

## 3. `analogy.py` — proportional analogy

`D* = C + (B − A)` exactly, then projection.

**Subspaces matter.** A raw 24-coordinate difference lets bookkeeping outvote
content, so `SUBSPACES` names the coordinate sets that make a question
well-posed — `physics.dimension` (the ten EXT10 exponents plus the SI7
projection), `chemistry.position` (`z`, period, group), and others. Projection
zeroes the other coordinates rather than slicing, so the result stays a point
of `Q^24`.

**Answers are tie classes, not single names.** Several register concepts share
a dimension vector exactly, so `AnalogyResult` reports `tied` and `unique`
alongside `answer`. Reporting just `answer` would overclaim.

**`nearest_lattice_point` is exact and provably optimal**, not a heuristic. `Λ`
is the disjoint union over a parity `m ∈ {0,1}` and a Golay codeword `c` of the
congruence cosets that `leech2.in_leech` tests. Inside one coset each
coordinate ranges over a step-4 progression, so the unconstrained nearest point
is coordinatewise rounding; the `sum ≡ 4m (mod 8)` condition is either met, or
flipped at minimum cost by moving one coordinate by `±4`. Enumerating the
`2 × 4096` cosets therefore searches all of `Λ`. The decoded point is checked
with `in_leech` before it is returned.

**A known boundary of the model:** `D* = C + (B − A)` expresses *translations
of the exponent vector and nothing else*. `time : frequency :: length : ?` is an
inversion, not a translation, so the model answers `L T^-2` (acceleration) and
not the reciprocal `L^-1` a reader expects. The audit records this case rather
than hiding it.

## 4. `verifier.py` — the multi-plane equation audit

Three layers, deliberately separate:

1. **the operator algebra** (`Sense`) — ten exact rational EXT10 exponents, a
   decimal scale, tensor rank, and `P` / `T` / `C` gradings. `dot` contracts two
   ranks away; `moment` is the cross product with one radian consumed (torque is
   an energy *per radian*, `E × H` is not); every differential operator is built
   from one `NABLA` with `L^-1`, rank 1, `P`-odd, so rank and parity bookkeeping
   is forced rather than tabulated;
2. **the parser** — recursive descent over `* / ^ ( ) ,` with exact rational
   exponents; numeric literals must be exact powers of ten, because the register
   tracks the decimal scale exactly and refuses to absorb other constants;
3. **the substrate audit** — both sides become 24-coordinate carriers,
   `digit_stack.verify_equation` compares them plane by plane, and every
   differing bit is attributed to each of the 31 named MOG facets containing it
   (3 trio bricks, 6 sextet columns, 4 frame rows, 18 cube faces).

Layer 3 is the point. A boolean says an equation is wrong; a facet attribution
says *where*.

| table | semantics | checked | held |
| --- | --- | --- | --- |
| scalar relations | scalar (exponents + scale) | 222 | 222 |
| scalar relations | full (+ rank, P, T, C) | 222 | 186 |
| tensor relations | full | 71 | 71 |

The middle row is the interesting one: 36 statements that a table of units gets
right are wrong once tensor character is included — `acceleration = speed / time`
fails because the left side is a rank-1 vector and the right side a scalar. The
discrepancy lands in coordinates `rank` (18) and `p` (19), which live in
`brick2/col5/row3/cube2.*` and `brick1/col3/row0/cube1.*` respectively, and
those are exactly the facets the verdict blames.

## Data provenance

`_data/physics_relations.json` holds the relation **statements** only, frozen
from the upstream register by `workflow/09_extract_physics_relations.py`, the
same way Step 2 froze the 660 concepts. Every verdict is recomputed here by this
module's own parser against `glm_universal`'s own frozen register. The upstream
tree is never imported at runtime.

That separation is what makes the tally a cross-validation: this kernel reports
222 / 71 / 186, and the upstream `glm2_library.library_audit()` — a separate
implementation over a separate copy of the register — reports the same three
numbers.

## Running it

```bash
uv run pytest glm_universal/tests/test_reasoning.py -q     # 62 tests
uv run pytest glm_universal/tests/ -q                      # full package
uv run python workflow/10_reasoning_audit.py               # regenerate results
```

The first test that touches the `2A` algebra builds the exhaustive
98,280-class type-2 table (about six seconds); it is cached for the process and
the fixture is module-scoped, so the cost is paid once.

## Depends on

`glm_universal.substrate`, `glm_universal.data_objects`. Nothing else.
