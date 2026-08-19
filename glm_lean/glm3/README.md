# The Geometric Language Machine, third generation (GLM-3)

**Reasoning inside the Monster.** The two earlier generations named the Monster
group and did not use it. GLM-3 removes the proxy layers and builds the chain

```
meaning  →  Leech point  →  the 2-adic stack of Λ/2Λ  →  Q = 2^(1+24)
         →  the Griess algebra, all 196,884 dimensions of it
```

end to end, exactly, in integers and `Fraction`s, and carries the GLM-2 register
of 660 concepts all the way along it. Nothing on the way is quoted from the
literature: the quadratic form, its Witt type, the class census, the cocycle of
the extraspecial group, its 4096-dimensional representation, the structure
constants of both halves of the algebra, the axis spectrum, the fusion law, the
Miyamoto involutions and the Norton–Sakuma types are all **computed here** and
checked against each other.

Standard library only — no third-party dependencies, Python 3.8+.
GLM-1 ([`../glm`](../glm)) and GLM-2 ([`../glm2`](../glm2)) are **reused, not
copied**: `glm3_common` puts them on the path and the GLM-3 reasoner holds a
GLM-2 reasoner as its base.

---

## Run it

Everything must be run from inside this directory.

```bash
cd glm3
python3 glm3_paper.py            # the paper's verification run: 64 claims, ~2 min
python3 glm3_paper.py --quick    # skips the heavy sweeps, ~95 s
python3 glm3_paper.py --json     # writes results/glm3_results.json only
python3 glm3_reasoner.py         # the companion's fourteen-section demonstration
python3 glm3_bench.py            # the benchmark: pass rates in four sections
python3 test_glm3.py             # the test suite: 145 tests, ~37 s
```

Individual modules self-audit when run directly:

```bash
python3 glm3_leech2.py    python3 glm3_griess.py    python3 glm3_sign.py
python3 glm3_extraspecial.py    python3 glm3_mog.py    python3 glm3_odd.py
python3 glm3_metric.py
```

The reasoner is also a command-line tool:

```bash
python3 glm3_reasoner.py address energy       # the ten Monster addresses
python3 glm3_reasoner.py stack energy         # plane by plane, with types
python3 glm3_reasoner.py relation energy torque   # the ten-letter relation word
python3 glm3_reasoner.py similar energy       # ranking by the Griess form
python3 glm3_reasoner.py distance energy work # the exact metric distance
python3 glm3_reasoner.py nearest energy       # true nearest neighbours
python3 glm3_reasoner.py cluster 0.05         # single-linkage clusters
python3 glm3_reasoner.py ledger               # the 196,884 eigenvalue ledger
python3 glm3_reasoner.py odd energy           # what the odd part sees
python3 glm3_reasoner.py triangle             # a 2A triangle in the register
python3 glm3_reasoner.py fusion energy        # the Monster fusion law, for a concept
python3 glm3_reasoner.py orbit energy         # the involution's two-colouring
python3 glm3_reasoner.py frame energy         # the coordinate frame of a type-4 plane
python3 glm3_reasoner.py mog energy           # both multi-MOG-cube readings
python3 glm3_reasoner.py census               # where the register sits in the Monster
python3 glm3_reasoner.py facets energy        # the six facets of a meaning
python3 glm3_reasoner.py check "mass*speed^2" "mass*speed^4"
python3 glm3_reasoner.py analogy mass force time
python3 glm3_reasoner.py audit energy "mass*speed^2"
python3 glm3_reasoner.py solve energy mass speed
```

The benchmark also runs one section at a time:

```bash
python3 glm3_bench.py laws       python3 glm3_bench.py mutants
python3 glm3_bench.py numbers    python3 glm3_bench.py sweep
```

---

## Files

| file | what it is |
|---|---|
| `glm3_paper.py` | **the paper**: the whole write-up in the module docstring (abstract, §1–§15), plus an operational run that verifies 64 numbered claims and writes `results/glm3_results.json` |
| `glm3_reasoner.py` | **the companion implementation**: the GLM-2 questions (audit, solve, convert, identify, repair) plus the Monster ones (address, stack, relation word, similarity, metric distance, nearest neighbours, clustering, triangle, fusion, involution orbit, frame, MOG views, facets, analogy, the 196,884 ledger, the odd-part view) — and the CLI above |
| `glm3_leech2.py` | Λ/2Λ as an F₂ quadratic space: `q`, `B`, the Witt decomposition, the class types and censuses, frames, the pair invariant, and the 2-adic **stack** with **derived** depth and offset (`coordinate_range`, `derive_stack_parameters`, `class_stack`, `class_stack_rebuild`, `depth_report`) |
| `glm3_extraspecial.py` | `Q = 2^(1+24)₊` built from the form alone: symplectic singular basis, explicit cocycle, group relations, involution count, and the 4096-dimensional Schrödinger representation |
| `glm3_griess.py` | the **even part** of the Griess algebra, 300 + 98,280 = 98,580 dimensional, exact: derived structure constants, Majorana axes, the eigenspace dimensions, the fusion law, the Miyamoto map, subalgebra closure and the Norton–Sakuma report |
| `glm3_odd.py` | the **odd part**, `V⁻ = 24 ⊗ 4096 = 98,304`, with both multiplications `V⁺ ⊗ V⁻ → V⁻` and `V⁻ ⊗ V⁻ → V⁺`, constants derived from the identity condition and Miyamoto, the whole 196,884 ledger, Q-equivariance, the fusion rules, and the separation of the two axis signs |
| `glm3_sign.py` | the **canonical sign convention**: the Golay theta function, `q([2·1_C]) = θ(C)` over all 4,096 codewords, the lattice cocycle, the Sakuma rule `s(λ+μ) = −s(λ)s(μ)`, and the count of coherent conventions |
| `glm3_metric.py` | the **metric**: positive definiteness of the invariant form, the pseudometric and its quotient, the injective plane-graded embedding, nearest neighbours and single-linkage clustering with guarantees |
| `glm3_bench.py` | the **benchmark**: the exhaustive pairwise sweep, a corpus of 64 physical laws, 224 corrupted mutants with facet attribution, and 40 dimensionless groups, reported as pass rates |
| `glm3_mog.py` | the **multi-MOG-cube**: the trio of 8-bit cubes, the sextet of columns, the Golay trace on a cube (and the refutation of the RM(1,3) claim), the AG(4,2) on a cube's complement, the design censuses, and the ambient digit-plane stack |
| `glm3_common.py` | the path shim to `../glm2` and `../glm`, plus small printing helpers |
| `test_glm3.py` | the test suite: 145 tests over every module, including the edge cases the paper has no reason to mention |
| `results/glm3_results.json` | the machine-readable record of the last verification run |

---

## What is new, in one paragraph each

**Λ/2Λ is the index set of meaning, not Λ.** The Monster acts on structures
indexed by the 2²⁴ classes of Λ/2Λ, on which the Leech norm descends to an F₂
quadratic form `q(λ) = (λ·λ)/16 mod 2` with polarisation `B(λ,μ) = (λ·μ)/8 mod
2`. The computed Witt decomposition is twelve hyperbolic planes with no
anisotropic part, so the form is of **plus type** and the singular classes
number 2²³ + 2¹¹ = 8,390,656. The class census 1 + 98,280 + 8,386,560 +
8,292,375 = 2²⁴ closes, and the type-3 classes are exactly the non-singular
ones — which turns the type test into an O(1) lookup where GLM-2 needed a
lattice decoder.

**A concept is a stack of Monster addresses.** One reduction mod 2 is far too
coarse: the 660 concepts land on nine classes. That is GLM-1's mod-2 ceiling met
one level up, and the fix is GLM-1's fix — *expand, do not reduce*. The k-th
binary digit plane of the 24 Leech-basis coordinates is a class of Λ/2Λ, hence a
Monster address; ten planes rebuild the carrier exactly. A concept is a **word
of ten Monster addresses**, and every question about a concept becomes ten
questions inside the Monster.

**The depth is derived.** Ten is no longer a magic number. The stack depth and
offset are parameters computed from the coordinate range of the data (180 over
the register: least admissible pair offset 256 with depth 9, and the
conventional offset 512 forcing depth 10), the rebuild identity is proved for
arbitrary admissible depth, planes above the threshold are identically zero, and
two reasoners at different admissible parameters return the same verdict on
every pair.

**Composition of meanings is multiplication in an extraspecial group.** From the
form alone, `Q = 2^(1+24)₊` of order 2²⁵ is built with an explicit cocycle
`f(u,v) = ⟨b_u, a_v⟩` in a symplectic singular basis, and the relations
`x_u² = z^q(u)`, `[x_u,x_v] = z^B(u,v)` are verified along with the involution
count 2²⁴ + 2¹². Because GLM composition adds carriers and plane 0 is additive,
`x_[a] x_[b] = z^f x_[a·b]`: the GLM product law and the group law of the
Monster's 2B centraliser are the same law.

**The Griess algebra is built, both halves, with its constants derived.** The
98,580-dimensional even part is constructed exactly, its four structure
constants and two form constants pinned down by N-equivariance, by the identity
acting as the identity, by the Frobenius property and by the fusion law. The
98,304-dimensional odd part `V⁻ = 24 ⊗ 4096` is then built with both of its
multiplications, its four constants forced by the identity condition together
with the requirement that the Miyamoto involution be the extraspecial sign
automorphism the even part already produces — an over-determined system that
closes. The payoff is the eigenvalue ledger of a 2A axis on the whole algebra:
**1 / 96,256 / 4,371 / 96,256 = 196,884**, the classical numbers, none of which
the even part alone can produce.

**The sign of an axis is settled.** A theta function on the Golay code gives a
canonical global convention, and the Sakuma identity *forces*
`s(λ+μ) = −s(λ)s(μ)`, so the naive all-plus convention is incoherent and the
canonical constant one is `s = −1`. The odd part then settles it as mathematics
rather than convention: `a_λ⁻` and `a_λ⁺` have the **different** Miyamoto
involutions `x_λ` and `x_λ z`, which agree on the even part and differ on `V⁻`.

**The similarity is now a metric.** The invariant form is positive definite on
the even part (it is twice a sum of squares), so the triangle inequality is
free; injectivity is restored by grading the embedding over the planes and
letting non-axis planes contribute a rank-one projector. The result separates
the register — distance zero exactly for concepts sharing a carrier — so
nearest-neighbour queries and single-linkage clustering come with guarantees
instead of being ranking heuristics.

**The Monster does the reasoning, and it is measured.** Two concepts have a
ten-letter **relation word** over {1A, 2A, 4A, 2B}, each letter checked against
the inner product of the two axes; a pair in 2A position generates a
3-dimensional Norton–Sakuma algebra whose third axis is the axis of their
**product**. A concept splits into six **facets**, each again a word of Monster
addresses, which is what lets an equation be decided inside the Monster with the
failing facet named. The benchmark turns that from an anecdote into pass rates:
all **217,470** pairs of the register agree with the GLM verdict, **64/64**
physical laws are admissible, **224/224** deliberately corrupted mutants are
caught with the right facet blamed, and **40/40** dimensionless groups come out
as expected.

**A correction to the archive.** The material accompanying this project claims
the Golay code restricted to one 8-cell cube is the Reed–Muller code RM(1,3).
It is not. Computed exhaustively over all 4,096 codewords, the trace is the
128-element even-weight code [8,7,2] and the shortened code is just
{0, the cube}. What *does* live on a cube is an AG(4,2) on the complementary 16
cells, with stabiliser AGL(4,2) of order 322,560.

---

## What is **not** built

Stated as plainly as GLM-2 stated its own limits (paper §14):

* **The Monster itself.** Only N-side symmetries are constructed: `Q` by
  generators and relations, and its action by automorphisms. The extra
  generator that with `N` generates the Monster is not built, so no claim in
  the paper is a claim about the full group of order ≈ 8 × 10⁵³. What *is*
  constructed is a genuine subgroup acting genuinely on a genuine
  196,884-dimensional algebra.
* **The odd part is verified, not symbolically proved.** Its products are
  checked on explicit block eigenvectors and on sampled vectors, not by a
  symbolic argument over all 196,884 dimensions, and no identity beyond
  commutativity, Frobenius, Q-equivariance and the fusion law is asserted.
* **The count of coherent sign conventions** is 2²⁴ on the evidence of four
  closed subsystems, not of an elimination over all 98,280 unknowns.
* **Depth-independence** is measured over the register's pairs, not proved for
  all possible inputs.
* **The metric is not canonical.** The grading weights 2⁻ᵏ and the weight η on
  a non-axis plane are choices, stated as choices; any positive values give a
  metric, and no verdict depends on which.

---

## Invariants a future change must preserve

1. The meaning is the state; the carrier is `encode(meaning)`; the Monster layer
   **reads** the carrier and never writes to it. (claim C45)
2. No verdict is reached by reducing an exponent mod 2. Reduction mod 2 appears
   only where the mathematics is genuinely over F₂ — the class group Λ/2Λ — and
   there it is an index, never a verdict.
3. `class_stack_rebuild ∘ class_stack = id` on every carrier. (C35)
4. The O(1) type test agrees with the decoder. (C10)
5. The structure constants stay derived, in both halves: change any one and
   C20–C23 or C56–C58 fail.
6. All arithmetic above the lattice is in `Fraction`, never `float`.
7. The stack depth stays derived from the coordinate range, and the reasoning
   stays depth-independent above the threshold. (C50–C53)
8. The axis sign convention stays coherent — the Sakuma identity must hold with
   no ad-hoc sign. (C55)
9. The distance stays a metric on the register. (C59, C60)
10. The benchmark stays at full pass rates in all four sections. (C61–C64)
