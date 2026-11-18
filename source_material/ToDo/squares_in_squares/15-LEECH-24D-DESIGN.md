# 15 — The 24D design, and what a 2D map can keep

**Run 44, 2026-11-18.** Instrument `scripts/leech24_design.py`; ledger
`workspace/push/leech24_design.json` (23/23 checks). Read-only.

The question: Λ₂₄ is the optimal packing in 24D and it can be brought to 2D, so
there must be a *design* to that 24D environment; what 2D maps pair to a 24D
address losslessly and reversibly; can the address be defined exactly when the
2D map is optimal; and is there anything in the 24D definitions worth
exploiting.

The answer, in one paragraph: the design is real and is the Witt design
S(5,8,24) acting on the 24 coordinates; the lossless maps are exactly four, and
only one of them is geometric; "optimal in 24D" does **not** project to
"optimal in 2D" — projection makes a *finer* 2D lattice, not a better-packed one
— and what actually descends is the A2 *section*, which is the 2D optimum
already. The score of this project is not a function of any of it: that was
measured in `10-LEECH-ADDRESS.md` and is not overturned here.

---

## 1. The premise, stated precisely

| fact | value | status |
| --- | --- | --- |
| densest packing in 24D | yes, among **all** packings | Cohn–Kumar–Miller–Radchenko–Viazovska, *Annals* 185 (2017); unique optimal *periodic* packing |
| universal optimality | yes | Cohn–Kumar–Miller–Radchenko–Viazovska (2022) |
| determinant | 1 | normalisation used throughout |
| minimum norm | 4 (minimum distance 2) | |
| kissing number | 196 560 | maximum possible in any packing |
| centre density / density | 1 / π¹²/12! ≈ 0.001 929 6 | |
| covering radius | √2 | Conway–Parker–Sloane 1982 |
| deep holes | 23 classes ↔ the 23 Niemeier lattices ≠ Λ₂₄ | Conway–Parker–Sloane; Borcherds Cor. 7.2 |
| automorphism group | Co₀, order 2²²·3⁹·5⁴·7²·11·13·23 | |

Two of these are load-bearing below: **det = 1** (so every covolume formula
collapses to a single determinant) and **covering radius √2** (so Λ₂₄ is also an
optimal *quantiser*, which is a different job from packing).

## 2. The design

"Design" is a technical word, and here it is literally a design: the **Witt
design S(5,8,24)**, the combinatorics of the 24 coordinates. The instrument
builds it rather than quoting it — the degree-11 factors of x²³−1 over GF(2) are
found by division, each gives the cyclic [23,12,7] code, and the parity bit
extends it:

| check | value |
| --- | --- |
| codewords | 4 096 |
| minimum weight | 8 |
| weight enumerator | 1 + 759x⁸ + 2 576x¹² + 759x¹⁶ + x²⁴ |
| octads (weight-8 words) | 759 |
| every 5-subset in | exactly 1 octad |
| every 4-subset in | exactly 5 octads |
| every 3-subset in | exactly 21 octads |
| every 2-subset in | exactly 77 octads |
| two factors of x²³−1 | same weight enumerator, overlapping in exactly {0, 1²⁴} |

That last line is the standard fact that the two degree-11 factors give two
coordinate-permuted copies of the same code — here *measured* (their intersection
is 2 words), not assumed.

The lattice is glued from this design: Construction A plus the parity condition —
the exact integer form the repository already states in
`src/lean/RequestProject/GLM/Escalation/LeechResidue.lean` — and
Λ₂₄ ⊃ E8³ with the code as glue. So the 24D environment has a design, it is
S(5,8,24), and its group is M₂₄ ⊂ Co₀.

## 3. Projection versus section — where the intuition fails

Let Λ ⊂ R²⁴ be a lattice, V a 2-plane, π_V the orthogonal projection. Exactly
(verified on rational examples in the instrument):

```
π_V|Λ injective        <=>  Λ ∩ V^⊥ = 0
π_V(Λ) discrete        <=>  V^⊥ is spanned by lattice vectors ("V rational")
cov(π_V Λ)² · det(Λ ∩ V^⊥)² = det(Λ)²
```

With det(Λ₂₄) = 1 the third line reads `cov(π_V Λ) = 1 / det(Λ ∩ V^⊥)`. A
22-dimensional sublattice has a *large* determinant, so the projected 2D lattice
has a *tiny* covolume: it is a very fine lattice — a good **quantiser**, with
many points per unit area, and its packing density is at most π/√12 by
dimension, with equality only if it happens to be A2-shaped. Concretely, in Z³:

| lattice → plane | cov²(image) | injective | what it is |
| --- | ---: | --- | --- |
| Z³ → (e₁,e₂) | 1 | yes | lattice isomorphism: lossless and reversible |
| Z³ → ((1,1,0),(0,0,1)) | 1/2 | **no** | 2-to-1: (1,−1,0) ↦ 0; the address needs a residue label |

So **projection cannot carry packing quality downward**. What does come down is
a *section*, and a section can never beat A2. This is the whole of the "it must
project down" intuition, and it is a category error in the direction the
intuition wants: 24D optimality descends to 2D only as the trivially-optimal A2.

Measured, with the explicit chain A2 ⊂ E8 (and E8³ ⊂ Λ₂₄ declared):

| quantity | value |
| --- | --- |
| A2 section of E8 (roots e₁+e₂, e₂+e₃) | Gram (2,1,2), area² 3, min norm² 2 — **is A2** |
| projection lands in the plane | residual exactly 0 |
| image lattice, det in plane coordinates | 1/3 |
| index [image : section] | **3** |
| kernel | rank 6, **72 roots** — i.e. E6 |
| image shape | min norm² 2/3, 6 shortest vectors, no orthogonal pair — **A2-shaped** (the √3-refinement) |

Read that table as the exact version of "the 24D optimum comes down to 2D": the
*shape* survives (A2 refined by √3 is still A2 up to scale — every triangular
lattice is), the *density per lattice point* does not, and every 2D address now
carries a rank-6 fibre. In Λ₂₄ the fibre is rank 22.

## 4. The 2D maps that pair to a 24D address

There is a rank obstruction first: **no injective linear map R²⁴ → R² exists on a
full-rank lattice**, so a lossless 2D address of a 24D *point* is impossible.
Everything below is a way around that, and each pays a different price.

| map | lossless? | reversible? | what it preserves | price |
| --- | --- | --- | --- | --- |
| **rational plane, zero kernel** | yes | yes | the whole lattice (isomorphism) | needs V^⊥ spanned by 22 lattice vectors; generic planes are dense |
| **quotient + residue label** | yes, with the label | yes, with the label | Λ/(Λ∩V^⊥) | the label is the fibre; drop it and it is 2-to-1 |
| **cut-and-project** | yes, as (2D, 22D) | yes | everything | the 22D internal coordinate must travel; 2D alone is injective but has a dense image |
| **MOG 4×6 coordinate chart** | yes | yes | all 24 coordinates | it is an *index*, not a projection — it is where S(5,8,24) lives |
| **finite class index** | yes | yes | Λ/2Λ, order 2²⁴ | 2²⁴ ↔ 4096² is exact (verified) and carries no geometry |

The fourth row deserves emphasis: the **Miracle Octad Generator** is the 2D
object the question is really asking for, and it is not a projection at all — it
is a 4×6 *layout* of the 24 coordinates on which octads become 2D patterns. It is
lossless because it is a permutation, and it is the only 2D layout that carries
the design.

The fifth row is the repository's own object: `cent_compiler/leech_class.py`
already verified Λ/2Λ ≅ F₂²⁴ (63 257 observed classes, F₂ rank 24, 5 000/5 000
XOR pairs). A 2D address for it exists by bijection and is exact; it is also
useless as geometry, which is the point.

## 5. The exact address when the 2D map is optimal

**Criterion.** A 2D lattice is optimal iff it is similar to A2 (Gauss 1831 among
lattices, Thue/Fejes Tóth among all packings). Four equivalent exact tests, all
checked in the instrument:

```
G = c·[[1, 1/2], [1/2, 1]]          Gram
|b1| = |b2| = |b1 − b2|             three equal shortest vectors
6 shortest vectors, no orthogonal pair among them
regular hexagonal Voronoi cell      centre density 1/√12
```

Measured: A2 0.288 675 135 (= 1/√12), Z² 0.25, a sheared Z² 0.265 165 — the test
rejects the square and the near-miss, and accepts A2 at two different scales and
the A2 roots inside E8.

**Address.** Let V be a rational 2-plane with Λ ∩ V^⊥ = 0 and let S = Λ ∩ V be
the section, similar to A2 with basis (u₁,u₂). Then π_V is injective and

```
π_V(Λ) ⊇ S        with finite index  k = det(S) · det(Λ ∩ V^⊥) / det(Λ)
address(x) = ( (i, j), c )        x ↦ i·u1 + j·u2 + c,   c ∈ π_V(Λ)/S,  |c| = k
```

The hex pair is the 2D coordinate; `c` is the residue that makes it reversible.
In the one fully computed case (E8 → A2 plane) **k = 3**: three cosets, so the
address of a general lattice point is a hex coordinate plus a ternary label.

**Rigidity at the optimum.** At an A2 section the address has a built-in Z² ⋊ S₃
symmetry: the six shortest vectors are equal-length and 60° apart, so the
Voronoi cell is a regular hexagon. That is exactly why the 2D optimum is rigid,
and it is the exploitable content of the 2D end: an A2 packing is determined by
its hex coordinates up to that group.

## 6. What in 24D is exploitable — verdicts

| 24D object | what it gives | verdict for this project |
| --- | --- | --- |
| Witt design S(5,8,24) | balanced 24-point covers, M₂₄ transitivity | a *sampling layout* only. The delivered corpus is not Witt-balanced: 82% of squares in one 30° sector, one pocket holding 46% (measured, `10-LEECH-ADDRESS.md`) |
| Golay C₂₄ / F₂²⁴ class map | exact 24-bit address, XOR algebra | real, exact, already built — and rank 24 means there is no smaller linear invariant to extract |
| deep holes: 23 types ↔ Niemeier lattices | 23 declared *move* types; each hole's vertex figure is that lattice's extended Dynkin diagram | **the only genuinely new attack surface.** It is a move family, not an address — and it needs a pull-back to 2D, which does not exist yet |
| minimal vectors: 196 560, three shapes | contact classification | no 2D analogue (2D contacts are edge-to-edge and corner-to-edge) |
| covering radius √2 | quantiser error bound | irrelevant to exact combinatorial optimisation |
| E8³ ⊂ Λ₂₄ + Golay glue | a 3×8 structured decomposition | matches the 6×4 = 3×8 = 24 pocket chart, but does not select pockets |
| residues mod 8, 144, 256 | — | **blind by theorem**: Λ₂₄ + mZ²⁴ = Λ₂₄ for 8 \| m, so they cannot see deep holes (`LeechResidue.lean`) |

## 7. The measured wall

`10-LEECH-ADDRESS.md` (Run 43) built the only canonical 24-pocket map available —
6 angle sectors × 4 radial shells — over the 1 000 delivered rows:

| quantity | value |
| --- | ---: |
| distinct addresses | 50 of 1 000 rows |
| MI(address; beats grid) | 0.193 0 bits (H = 0.881) |
| permutation null for that MI | mean 0.043 1, max 0.064 4 |
| MI(address; residue r) | 0.919 8 bits |
| MI(address; band k) | 0.562 6 bits |
| MI(gap; beats \| rotation) | **0.000 0** |

The address was re-encoding the column index. Nothing in this run changes that:
a better 2D map does not help, because the missing object is not the lattice. It
is the **map from a 2D square packing to a Λ₂₄ point**, and every such map is a
choice that has to pay for itself with measured gain. The pocket map is the
canonical choice and it pays nothing after conditioning.

## 8. What would reopen this — two falsifiable tests

**T1 — the address, once more, with the class word.** Using the pocket chart
(24 coordinates → Λ₂₄ via Construction A) measure
`MI(Δscore; class word | n, r, rotation, band)` against a permutation null. If it
is zero again, the address route is finished and should be registered as **W-02**
in `14-WRITE-OFFS.md`, keeping the design only as a move source.

**T2 — the design as a move generator (the new one).** Declare the **23 deep-hole
types** as 23 move motifs and spin them with `motif_wheels.py`: gate through
`packlib`, score only through `sqscore`, refusals with reasons, `spin()` pruning
by the area floor and n ≤ 1000. This is the one place where the design of the 24D
environment can produce a *move* rather than an *address*, and the machinery for
it already exists — a wheel is one builder function plus one registry row.

Neither test is run here: T1 needs the packing → Λ₂₄ map to be declared first
(that is the missing object, and declaring it is a research choice, not a
computation), and T2 needs the 23 hole types converted to 2D pulls, which is a
design decision about what a "hole move" means for axis-aligned squares.

## 9. Files

* `scripts/leech24_design.py` — builds the Golay code from x²³−1, verifies
  S(5,8,24), verifies the A2 criterion on four cases, verifies the
  projection/section algebra on exact rational examples, measures the E8 → A2
  projection (index 3, rank-6 E6 kernel, A2-shaped image), and checks the 2²⁴ ↔
  4096² index. 23/23 checks. `python3 scripts/leech24_design.py`
* `workspace/push/leech24_design.json` — ledger, with the declared/measured
  split explicit.
* Related, unchanged: `10-LEECH-ADDRESS.md`, `scripts/leech_address.py`,
  `cent_compiler_v12/cent_compiler/leech_class.py`,
  `src/lean/.../LeechResidue.lean`.
